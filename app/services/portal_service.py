from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.db import get_supabase
from app.services.admin_service import get_client_usage, list_clients


def _parse_date(value: str | None, end_of_day: bool = False):
    if not value:
        return None

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    if end_of_day and len(value) <= 10:
        parsed = parsed + timedelta(days=1)
    return parsed.isoformat()


def _allowed_client_slug(user: dict, requested_client_slug: str | None):
    if user.get("role") == "admin":
        return requested_client_slug or None

    client_slug = user.get("client_slug")
    if not client_slug:
        raise HTTPException(status_code=403, detail="User is not assigned to a client")
    if requested_client_slug and requested_client_slug != client_slug:
        raise HTTPException(status_code=403, detail="Client access denied")
    return client_slug


def list_portal_clients(user: dict):
    clients = list_clients()
    if user.get("role") == "admin":
        return clients

    client_slug = user.get("client_slug")
    return [client for client in clients if client["client_slug"] == client_slug]


def get_portal_summary(
    user: dict,
    client_slug: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    supabase = get_supabase()
    scoped_client = _allowed_client_slug(user, client_slug)
    if supabase is None:
        if scoped_client:
            return {"scope": scoped_client, **get_client_usage(scoped_client)}
        return {"scope": "global", "conversation_count": 0, "message_count": 0, "total_tokens": 0}

    start = _parse_date(start_date)
    end = _parse_date(end_date, end_of_day=True)

    conversations_query = supabase.table("conversations").select("*")
    messages_query = supabase.table("messages").select("*")

    if scoped_client:
        conversations_query = conversations_query.eq("client_slug", scoped_client)
        messages_query = messages_query.eq("client_slug", scoped_client)
    if start:
        conversations_query = conversations_query.gte("created_at", start)
        messages_query = messages_query.gte("created_at", start)
    if end:
        conversations_query = conversations_query.lt("created_at", end)
        messages_query = messages_query.lt("created_at", end)

    conversations = conversations_query.execute().data or []
    messages = messages_query.execute().data or []

    total_tokens = sum(message.get("total_tokens") or 0 for message in messages)
    assistant_messages = [message for message in messages if message.get("role") == "assistant"]
    user_messages = [message for message in messages if message.get("role") == "user"]
    latencies = [
        float(message["duration_ms"])
        for message in assistant_messages
        if message.get("duration_ms") is not None
    ]
    avg_latency_ms = round(sum(latencies) / len(latencies), 2) if latencies else 0

    by_client = {}
    for message in messages:
        slug = message.get("client_slug") or "unknown"
        stats = by_client.setdefault(slug, {"client_slug": slug, "messages": 0, "tokens": 0})
        stats["messages"] += 1
        stats["tokens"] += message.get("total_tokens") or 0

    return {
        "scope": scoped_client or "global",
        "conversation_count": len(conversations),
        "message_count": len(messages),
        "assistant_messages": len(assistant_messages),
        "user_messages": len(user_messages),
        "total_tokens": total_tokens,
        "avg_latency_ms": avg_latency_ms,
        "by_client": sorted(by_client.values(), key=lambda item: item["messages"], reverse=True),
    }


def list_portal_conversations(
    user: dict,
    client_slug: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 50,
):
    supabase = get_supabase()
    scoped_client = _allowed_client_slug(user, client_slug)
    if supabase is None:
        return []

    start = _parse_date(start_date)
    end = _parse_date(end_date, end_of_day=True)

    query = supabase.table("conversations").select("*").order("created_at", desc=True).limit(limit)
    if scoped_client:
        query = query.eq("client_slug", scoped_client)
    if start:
        query = query.gte("created_at", start)
    if end:
        query = query.lt("created_at", end)

    conversations = query.execute().data or []
    if not conversations:
        return []

    conversation_ids = [conversation["id"] for conversation in conversations]
    messages = (
        supabase.table("messages")
        .select("conversation_id,role,total_tokens,duration_ms,created_at,content")
        .in_("conversation_id", conversation_ids)
        .order("created_at", desc=False)
        .execute()
        .data
        or []
    )

    by_conversation = {}
    for message in messages:
        stats = by_conversation.setdefault(
            message["conversation_id"],
            {"message_count": 0, "total_tokens": 0, "last_message": "", "last_message_at": None},
        )
        stats["message_count"] += 1
        stats["total_tokens"] += message.get("total_tokens") or 0
        stats["last_message"] = message.get("content") or ""
        stats["last_message_at"] = message.get("created_at")

    return [
        {
            **conversation,
            **by_conversation.get(
                conversation["id"],
                {"message_count": 0, "total_tokens": 0, "last_message": "", "last_message_at": None},
            ),
        }
        for conversation in conversations
    ]


def get_portal_conversation_messages(user: dict, conversation_id: str):
    supabase = get_supabase()
    if supabase is None:
        return []

    conversation_response = (
        supabase.table("conversations")
        .select("*")
        .eq("id", conversation_id)
        .limit(1)
        .execute()
    )
    if not conversation_response.data:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversation_response.data[0]
    _allowed_client_slug(user, conversation["client_slug"])

    messages = (
        supabase.table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
        .data
        or []
    )
    return {"conversation": conversation, "messages": messages}


def get_portal_docs(user: dict, lang: str):
    is_es = lang == "es"
    shared = [
        {
            "title": "Primeros pasos" if is_es else "Getting started",
            "body": (
                "Usa el panel para revisar conversaciones, consumo y rendimiento de tu asistente. "
                "Los filtros de fecha te ayudan a auditar periodos concretos."
                if is_es
                else "Use the portal to review conversations, usage and assistant performance. Date filters help audit specific periods."
            ),
        },
        {
            "title": "Conversaciones" if is_es else "Conversations",
            "body": (
                "Cada conversación agrupa los mensajes de una misma sesión. Puedes abrirla para revisar el contexto completo."
                if is_es
                else "Each conversation groups messages from one session. Open it to review the full context."
            ),
        },
    ]
    admin = [
        {
            "title": "Clientes y usuarios" if is_es else "Clients and users",
            "body": (
                "Los admins pueden crear clientes, asignar usuarios a clientes existentes o crear cliente y usuario en un mismo flujo."
                if is_es
                else "Admins can create clients, assign users to existing clients, or create a client and user in one flow."
            ),
        },
        {
            "title": "Sincronizacion" if is_es else "Sync",
            "body": (
                "El registry de Supabase es la fuente principal. Publicar locales sube configuraciones al registry; sincronizar baja el registry al entorno actual."
                if is_es
                else "The Supabase registry is the primary source. Publishing locals pushes configs to the registry; syncing pulls the registry into the current environment."
            ),
        },
    ]
    return shared + (admin if user.get("role") == "admin" else [])
