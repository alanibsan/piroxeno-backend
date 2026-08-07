from fastapi import Header, HTTPException

from app.config import settings


def require_admin(authorization: str | None = Header(default=None)):
    if not settings.admin_api_token:
        raise HTTPException(status_code=503, detail="Admin API is not configured")

    expected = f"Bearer {settings.admin_api_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid admin token")
