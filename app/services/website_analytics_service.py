import hashlib
from typing import Any
from urllib.parse import urlparse

from fastapi import Request

from app.config import settings
from app.db import get_supabase


MAX_TEXT_LENGTH = 1000


def _clean_text(value: Any, max_length: int = MAX_TEXT_LENGTH):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:max_length]


def _client_ip(request: Request):
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return (
        request.headers.get("cf-connecting-ip")
        or request.headers.get("x-real-ip")
        or (request.client.host if request.client else None)
    )


def _hash_ip(ip: str | None):
    if not ip:
        return None
    salt = settings.analytics_ip_salt or settings.admin_session_secret or "piroxeno-analytics"
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()


def _location_from_headers(request: Request):
    return {
        "country": _clean_text(
            request.headers.get("cf-ipcountry")
            or request.headers.get("x-vercel-ip-country"),
            80,
        ),
        "region": _clean_text(
            request.headers.get("x-vercel-ip-country-region")
            or request.headers.get("x-vercel-ip-region")
            or request.headers.get("cf-region"),
            120,
        ),
        "city": _clean_text(
            request.headers.get("x-vercel-ip-city")
            or request.headers.get("cf-ipcity"),
            120,
        ),
    }


def _origin_allowed(request: Request):
    origin = request.headers.get("origin")
    if not origin:
        return True

    allowed = {
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    }
    app_origin = settings.public_app_url.rstrip("/")
    if app_origin:
        parsed = urlparse(app_origin)
        if parsed.scheme and parsed.netloc:
            allowed.add(f"{parsed.scheme}://{parsed.netloc}")

    return origin.rstrip("/") in allowed


def track_website_event(request: Request, body: dict[str, Any]):
    if not _origin_allowed(request):
        return {"stored": False}

    supabase = get_supabase()
    if supabase is None:
        return {"stored": False}

    location = _location_from_headers(request)
    payload = {
        "site": _clean_text(body.get("site"), 120) or "piroxeno",
        "event_name": _clean_text(body.get("event_name"), 80) or "page_view",
        "path": _clean_text(body.get("path"), 500),
        "url": _clean_text(body.get("url"), 1000),
        "referrer": _clean_text(body.get("referrer"), 1000),
        "title": _clean_text(body.get("title"), 300),
        "language": _clean_text(body.get("language"), 40),
        "timezone": _clean_text(body.get("timezone"), 80),
        "screen_width": body.get("screen_width") if isinstance(body.get("screen_width"), int) else None,
        "screen_height": body.get("screen_height") if isinstance(body.get("screen_height"), int) else None,
        "visitor_id": _clean_text(body.get("visitor_id"), 120),
        "session_id": _clean_text(body.get("session_id"), 120),
        "ip_hash": _hash_ip(_client_ip(request)),
        "country": location["country"],
        "region": location["region"],
        "city": location["city"],
        "user_agent": _clean_text(request.headers.get("user-agent"), 1000),
        "metadata": body.get("metadata") if isinstance(body.get("metadata"), dict) else {},
    }

    supabase.table("website_events").insert(payload).execute()
    return {"stored": True}
