from datetime import datetime
from app.db import get_supabase


def get_client_by_api_key_hash(api_key_hash: str):
    supabase = get_supabase()
    if supabase is None:
        return None

    response = (
        supabase
        .table("clients")
        .select("*")
        .eq("api_key_hash", api_key_hash)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    client = response.data[0]

    # Validación SaaS real
    if not client["is_active"]:
        return None

    now = datetime.utcnow()

    if client["active_from"] and now < datetime.fromisoformat(client["active_from"]):
        return None

    if client["active_until"] and now > datetime.fromisoformat(client["active_until"]):
        return None

    return client
