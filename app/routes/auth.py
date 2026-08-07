from pydantic import BaseModel
from fastapi import APIRouter, Header, HTTPException

from app.services.auth_service import login, require_session_user


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def auth_login(body: LoginRequest):
    return login(body.email, body.password)


@router.get("/me")
def auth_me(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing session token")

    return {"user": require_session_user(authorization.removeprefix("Bearer ").strip())}
