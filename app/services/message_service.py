from app.db import supabase


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
