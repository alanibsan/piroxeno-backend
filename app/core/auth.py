from fastapi import Header, HTTPException
from app.services.client_service import get_client_by_api_key_hash
from app.core.security import hash_api_key


def authenticate_client(x_api_key: str = Header(None)):

    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    hashed = hash_api_key(x_api_key)

    client = get_client_by_api_key_hash(hashed)

    if not client:
        raise HTTPException(status_code=403, detail="Invalid or inactive API key")

    return client