import hashlib
import json
import secrets
from pathlib import Path

from app.config import settings
from app.db import get_supabase
from app.services.auth_service import hash_password
from app.services.client_config import load_client_config


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


def list_clients():
    clients = []
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

        clients.append(
            {
                "client_slug": path.name,
                "enabled": config.get("enabled", True),
                "allowed_origins": config.get("allowed_origins", []),
                "rate_limit_per_minute": config.get(
                    "rate_limit_per_minute",
                    settings.default_rate_limit_per_minute,
                ),
                "has_prompt": prompt_path.exists(),
                "has_embed": (path / "embed.html").exists(),
            }
        )

    return clients


def get_client_detail(client_slug: str):
    config = load_client_config(client_slug)
    prompt = ""
    prompt_path = _prompt_path(client_slug)
    if prompt_path.exists():
        prompt = prompt_path.read_text(encoding="utf-8")

    embed = ""
    embed_path = _embed_path(client_slug)
    if embed_path.exists():
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
    if not prompt_path.exists():
        prompt_path.write_text(
            f"""Eres el asistente del sitio web de {name}.

Tu función es responder dudas, capturar datos importantes y mantener continuidad dentro de la conversación.

Reglas:
- Responde de forma clara, breve y profesional
- No repitas preguntas si el usuario ya dio la información
- Si falta información, pide solo el siguiente dato más importante
- No inventes información
""",
            encoding="utf-8",
        )

    widget_title = title or f"Asistente {name}"
    embed = _embed_code(client_slug, client_key, widget_title, primary_color)
    _embed_path(client_slug).write_text(embed, encoding="utf-8")

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
    config = load_client_config(client_slug)

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
    return config


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
