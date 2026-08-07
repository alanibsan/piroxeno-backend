from fastapi import Header, HTTPException

from app.config import settings
from app.services.auth_service import require_session_user


def require_admin(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing admin authorization")

    token = authorization.removeprefix("Bearer ").strip()
    if settings.admin_api_token and token == settings.admin_api_token:
        return {
            "id": "bootstrap",
            "email": "bootstrap",
            "role": "admin",
            "client_slug": None,
            "is_active": True,
        }

    user = require_session_user(token)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return user
