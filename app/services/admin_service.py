import hashlib
import json
import secrets
from pathlib import Path
from typing import Any

from app.config import settings
from app.db import get_supabase
from app.services.auth_service import hash_password
from app.services.client_config import load_client_config
from app.services.client_registry_service import (
    get_registry_client,
    list_registry_clients,
    local_client_row,
    upsert_registry_client,
)


CLIENTS_DIR = Path("clients")


def _client_dir(client_slug: str):
    return CLIENTS_DIR / client_slug


def _config_path(client_slug: str):
    return _client_dir(client_slug) / "config.json"


def _prompt_path(client_slug: str):
    return _client_dir(client_slug) / "prompt.txt"


def _embed_path(client_slug: str):
    return _client_dir(client_slug) / "embed.html"


def _hash_key(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


def _embed_code(client_slug: str, client_key: str, title: str, color: str):
    api_url = settings.public_api_url.rstrip("/")
    return f"""<!-- Piroxeno AI Chatbot - {client_slug} -->
<script
  src="{api_url}/static/widget.js"
  data-api-url="{api_url}"
  data-client-slug="{client_slug}"
  data-client-key="{client_key}"
  data-title="{title}"
  data-primary-color="{color}"
  async>
</script>
"""


def _read_json_file(path: Path, fallback: dict[str, Any]):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def _registry_row_from_files(client_slug: str):
    return local_client_row(client_slug)


def _upsert_client_registry(client_slug: str):
    payload = _registry_row_from_files(client_slug)
    if payload is None:
        return None

    try:
        return upsert_registry_client(
            client_slug=payload["client_slug"],
            config=payload["config"],
            prompt=payload["prompt"],
            embed=payload["embed"],
        )
    except Exception as exc:
        print(f"[CLIENT REGISTRY WARNING] client={client_slug} error={exc}")
        return None


def _upsert_client_registry_payload(
    *,
    client_slug: str,
    config: dict[str, Any],
    prompt: str,
    embed: str,
):
    try:
        return upsert_registry_client(
            client_slug=client_slug,
            config=config,
            prompt=prompt,
            embed=embed,
        )
    except Exception as exc:
        print(f"[CLIENT REGISTRY WARNING] client={client_slug} error={exc}")
        return None


def _list_registry_clients():
    try:
        return list_registry_clients()
    except Exception as exc:
        print(f"[CLIENT REGISTRY WARNING] list error={exc}")
        return []


def list_clients():
    clients_by_slug = {}
    for path in sorted(CLIENTS_DIR.iterdir()):
        if not path.is_dir():
            continue

        config_path = path / "config.json"
        prompt_path = path / "prompt.txt"

        if not config_path.exists() and not prompt_path.exists():
            continue

        config = {}
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                config = {"enabled": False, "config_error": "invalid_json"}

        clients_by_slug[path.name] = {
            "client_slug": path.name,
            "enabled": config.get("enabled", True),
            "allowed_origins": config.get("allowed_origins", []),
            "rate_limit_per_minute": config.get(
                "rate_limit_per_minute",
                settings.default_rate_limit_per_minute,
            ),
            "has_prompt": prompt_path.exists(),
            "has_embed": (path / "embed.html").exists(),
            "source": "local",
        }

    for row in _list_registry_clients():
        config = row.get("config") or {}
        slug = row["client_slug"]
        clients_by_slug[slug] = {
            **clients_by_slug.get(slug, {}),
            "client_slug": slug,
            "enabled": config.get("enabled", True),
            "allowed_origins": config.get("allowed_origins", []),
            "rate_limit_per_minute": config.get(
                "rate_limit_per_minute",
                settings.default_rate_limit_per_minute,
            ),
            "has_prompt": bool(row.get("prompt")) or clients_by_slug.get(slug, {}).get("has_prompt", False),
            "has_embed": bool(row.get("embed")) or clients_by_slug.get(slug, {}).get("has_embed", False),
            "source": "registry" if slug not in clients_by_slug else "local+registry",
            "registry_updated_at": row.get("updated_at"),
        }

    return [clients_by_slug[key] for key in sorted(clients_by_slug)]


def get_client_detail(client_slug: str):
    registry_client = None
    try:
        registry_client = get_registry_client(client_slug)
    except Exception as exc:
        print(f"[CLIENT REGISTRY WARNING] detail lookup failed for {client_slug}: {exc}")

    config = registry_client.get("config") if registry_client else load_client_config(client_slug)
    prompt = registry_client.get("prompt") if registry_client else ""
    prompt_path = _prompt_path(client_slug)
    if not prompt and prompt_path.exists():
        prompt = prompt_path.read_text(encoding="utf-8")

    embed = registry_client.get("embed") if registry_client else ""
    embed_path = _embed_path(client_slug)
    if not embed and embed_path.exists():
        embed = embed_path.read_text(encoding="utf-8")

    return {
        "client_slug": client_slug,
        "config": config,
        "prompt": prompt,
        "embed": embed,
    }


def create_client(
    client_slug: str,
    name: str,
    title: str | None,
    allowed_origins: list[str],
    primary_color: str,
    rate_limit_per_minute: int,
):
    client_dir = _client_dir(client_slug)
    client_dir.mkdir(parents=True, exist_ok=True)

    client_key = secrets.token_urlsafe(32)
    config = {
        "enabled": True,
        "embed_key_hash": _hash_key(client_key),
        "allowed_origins": allowed_origins,
        "rate_limit_per_minute": rate_limit_per_minute,
    }
    _config_path(client_slug).write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    prompt_path = _prompt_path(client_slug)
    default_prompt = f"""Eres el asistente del sitio web de {name}.

Tu función es responder dudas, capturar datos importantes y mantener continuidad dentro de la conversación.

Reglas:
- Responde de forma clara, breve y profesional
- No repitas preguntas si el usuario ya dio la información
- Si falta información, pide solo el siguiente dato más importante
- No inventes información
"""
    if not prompt_path.exists():
        prompt_path.write_text(
            default_prompt,
            encoding="utf-8",
        )

    widget_title = title or f"Asistente {name}"
    embed = _embed_code(client_slug, client_key, widget_title, primary_color)
    _embed_path(client_slug).write_text(embed, encoding="utf-8")
    prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else default_prompt
    _upsert_client_registry_payload(
        client_slug=client_slug,
        config=config,
        prompt=prompt,
        embed=embed,
    )

    return {
        "client_slug": client_slug,
        "client_key": client_key,
        "embed": embed,
    }


def update_client_config(
    client_slug: str,
    allowed_origins: list[str] | None = None,
    enabled: bool | None = None,
    rate_limit_per_minute: int | None = None,
):
    detail = get_client_detail(client_slug)
    config = detail["config"]

    if allowed_origins is not None:
        config["allowed_origins"] = allowed_origins
    if enabled is not None:
        config["enabled"] = enabled
    if rate_limit_per_minute is not None:
        config["rate_limit_per_minute"] = rate_limit_per_minute

    _config_path(client_slug).write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _upsert_client_registry_payload(
        client_slug=client_slug,
        config=config,
        prompt=detail.get("prompt") or "",
        embed=detail.get("embed") or "",
    )
    return config


def list_client_registry():
    return _list_registry_clients()


def publish_local_clients_to_registry():
    published = []
    for path in sorted(CLIENTS_DIR.iterdir()):
        if not path.is_dir():
            continue
        result = _upsert_client_registry(path.name)
        if result is not None:
            published.append(path.name)

    return {
        "published_count": len(published),
        "clients": published,
    }


def sync_clients_from_registry():
    rows = _list_registry_clients()
    synced = []

    for row in rows:
        client_slug = row["client_slug"]
        client_dir = _client_dir(client_slug)
        client_dir.mkdir(parents=True, exist_ok=True)

        config = row.get("config") or {}
        _config_path(client_slug).write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        _prompt_path(client_slug).write_text(row.get("prompt") or "", encoding="utf-8")
        _embed_path(client_slug).write_text(row.get("embed") or "", encoding="utf-8")
        synced.append(client_slug)

    return {
        "synced_count": len(synced),
        "clients": synced,
    }


def get_client_usage(client_slug: str):
    supabase = get_supabase()
    if supabase is None:
        return {
            "client_slug": client_slug,
            "conversation_count": 0,
            "message_count": 0,
            "total_tokens": 0,
        }

    conversations = (
        supabase.table("conversations")
        .select("id", count="exact")
        .eq("client_slug", client_slug)
        .execute()
    )
    messages = (
        supabase.table("messages")
        .select("role,total_tokens")
        .eq("client_slug", client_slug)
        .execute()
    )

    total_tokens = 0
    message_count = 0
    assistant_messages = 0
    user_messages = 0

    for message in messages.data or []:
        message_count += 1
        total_tokens += message.get("total_tokens") or 0
        if message.get("role") == "assistant":
            assistant_messages += 1
        elif message.get("role") == "user":
            user_messages += 1

    return {
        "client_slug": client_slug,
        "conversation_count": conversations.count or 0,
        "message_count": message_count,
        "assistant_messages": assistant_messages,
        "user_messages": user_messages,
        "total_tokens": total_tokens,
    }


def list_users():
    supabase = get_supabase()
    if supabase is None:
        return []

    response = (
        supabase.table("app_users")
        .select("id,email,role,client_slug,is_active,created_at")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def upsert_user(
    email: str,
    role: str,
    client_slug: str | None,
    is_active: bool = True,
    password: str | None = None,
):
    supabase = get_supabase()
    if supabase is None:
        raise RuntimeError("Supabase is not configured")

    payload = {
        "email": email.lower().strip(),
        "role": role,
        "client_slug": client_slug,
        "is_active": is_active,
    }
    if password:
        payload["password_hash"] = hash_password(password)

    response = (
        supabase.table("app_users")
        .upsert(payload, on_conflict="email")
        .execute()
    )
    return response.data[0] if response.data else payload
