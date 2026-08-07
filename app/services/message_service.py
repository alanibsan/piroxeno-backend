from app.db import get_supabase


MAX_HISTORY_MESSAGES = 20


def insert_message(
    conversation_id: str,
    client_slug: str,
    role: str,
    content: str,
    tokens_prompt: int | None = None,
    tokens_completion: int | None = None,
    total_tokens: int | None = None,
    duration_ms: float | None = None,
):
    supabase = get_supabase()
    if supabase is None:
        return

    supabase.table("messages").insert({
        "conversation_id": conversation_id,
        "client_slug": client_slug,
        "role": role,
        "content": content,
        "tokens_prompt": tokens_prompt,
        "tokens_completion": tokens_completion,
        "total_tokens": total_tokens,
        "duration_ms": duration_ms,
    }).execute()


def list_conversation_messages(conversation_id: str, limit: int = MAX_HISTORY_MESSAGES):
    supabase = get_supabase()
    if supabase is None:
        return []

    response = (
        supabase
        .table("messages")
        .select("role, content, created_at")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return list(reversed(response.data or []))
