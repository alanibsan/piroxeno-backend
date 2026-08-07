import hashlib
import hmac
import json
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException, Request

from app.config import settings


CLIENTS_DIR = Path("clients")
LOCAL_ORIGINS = {
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8001",
}


def hash_key(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


def load_client_config(client_slug: str):
    config_path = CLIENTS_DIR / client_slug / "config.json"

    if not config_path.exists():
        raise HTTPException(status_code=403, detail="Client is not configured")

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid client configuration")

    if not config.get("enabled", True):
        raise HTTPException(status_code=403, detail="Client is disabled")

    return config


def origin_from_referer(referer: str | None):
    if not referer:
        return None

    parsed = urlparse(referer)
    if not parsed.scheme or not parsed.netloc:
        return None

    return f"{parsed.scheme}://{parsed.netloc}"


def validate_client_access(client_slug: str, request: Request):
    config = load_client_config(client_slug)
    client_key = request.headers.get("x-client-key")

    if not client_key:
        raise HTTPException(status_code=401, detail="Missing client key")

    expected_hash = config.get("embed_key_hash")
    if not expected_hash:
        raise HTTPException(status_code=500, detail="Client key is not configured")

    if not hmac.compare_digest(hash_key(client_key), expected_hash):
        raise HTTPException(status_code=403, detail="Invalid client key")

    origin = request.headers.get("origin") or origin_from_referer(
        request.headers.get("referer")
    )

    allowed_origins = set(config.get("allowed_origins") or [])
    allowed_origins.update(LOCAL_ORIGINS)

    if settings.require_widget_origin and not origin:
        raise HTTPException(status_code=403, detail="Missing request origin")

    if origin and origin not in allowed_origins:
        raise HTTPException(status_code=403, detail="Origin not allowed")

    return config
