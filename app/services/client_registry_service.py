from pathlib import Path
from typing import Any

from app.db import get_supabase


CLIENTS_DIR = Path("clients")


def get_registry_client(client_slug: str):
    supabase = get_supabase()
    if supabase is None:
        return None

    response = (
        supabase.table("client_registry")
        .select("client_slug,config,prompt,embed,updated_at")
        .eq("client_slug", client_slug)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def list_registry_clients():
    supabase = get_supabase()
    if supabase is None:
        return []

    response = (
        supabase.table("client_registry")
        .select("client_slug,config,prompt,embed,updated_at")
        .order("client_slug")
        .execute()
    )
    return response.data or []


def upsert_registry_client(
    *,
    client_slug: str,
    config: dict[str, Any],
    prompt: str,
    embed: str,
):
    supabase = get_supabase()
    if supabase is None:
        return None

    payload = {
        "client_slug": client_slug,
        "config": config,
        "prompt": prompt,
        "embed": embed,
    }
    response = (
        supabase.table("client_registry")
        .upsert(payload, on_conflict="client_slug")
        .execute()
    )
    return response.data[0] if response.data else payload


def local_client_row(client_slug: str):
    client_dir = CLIENTS_DIR / client_slug
    config_path = client_dir / "config.json"
    prompt_path = client_dir / "prompt.txt"
    embed_path = client_dir / "embed.html"

    if not config_path.exists() and not prompt_path.exists():
        return None

    import json

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        config = {}

    return {
        "client_slug": client_slug,
        "config": config,
        "prompt": prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else "",
        "embed": embed_path.read_text(encoding="utf-8") if embed_path.exists() else "",
    }
