import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.config import settings
from app.db import get_supabase


PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 260000


def _b64encode(value: bytes):
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _b64decode(value: str):
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _session_secret():
    secret = settings.admin_session_secret or settings.admin_api_token
    if not secret:
        raise HTTPException(status_code=503, detail="Admin auth is not configured")
    return secret.encode()


def hash_password(password: str):
    salt = secrets.token_urlsafe(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str | None):
    if not password_hash:
        return False

    try:
        scheme, iterations, salt, expected = password_hash.split("$", 3)
    except ValueError:
        return False

    if scheme != PASSWORD_SCHEME:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        int(iterations),
    ).hex()
    return hmac.compare_digest(digest, expected)


def create_session_token(user: dict):
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=settings.admin_session_hours)
    payload = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
        "client_slug": user.get("client_slug"),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    payload_part = _b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    )
    signature = hmac.new(
        _session_secret(),
        payload_part.encode(),
        hashlib.sha256,
    ).digest()
    return f"{payload_part}.{_b64encode(signature)}"


def decode_session_token(token: str):
    try:
        payload_part, signature_part = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid session token") from exc

    expected = hmac.new(
        _session_secret(),
        payload_part.encode(),
        hashlib.sha256,
    ).digest()
    provided = _b64decode(signature_part)
    if not hmac.compare_digest(expected, provided):
        raise HTTPException(status_code=401, detail="Invalid session token")

    payload = json.loads(_b64decode(payload_part))
    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        raise HTTPException(status_code=401, detail="Session expired")
    return payload


def get_user_by_email(email: str):
    supabase = get_supabase()
    if supabase is None:
        raise HTTPException(status_code=503, detail="Supabase is not configured")

    response = (
        supabase.table("app_users")
        .select("id,email,role,client_slug,is_active,password_hash")
        .eq("email", email.lower().strip())
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def get_user_by_id(user_id: str):
    supabase = get_supabase()
    if supabase is None:
        raise HTTPException(status_code=503, detail="Supabase is not configured")

    response = (
        supabase.table("app_users")
        .select("id,email,role,client_slug,is_active")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def login(email: str, password: str):
    user = get_user_by_email(email)
    if (
        not user
        or not user.get("is_active")
        or not verify_password(password, user.get("password_hash"))
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    supabase = get_supabase()
    if supabase is not None:
        supabase.table("app_users").update(
            {"last_login_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", user["id"]).execute()

    token = create_session_token(user)
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "client_slug": user.get("client_slug"),
            "is_active": user.get("is_active"),
        },
        "expires_in": settings.admin_session_hours * 3600,
    }


def require_session_user(token: str):
    payload = decode_session_token(token)
    user = get_user_by_id(payload["sub"])
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=401, detail="Inactive user")
    return user
