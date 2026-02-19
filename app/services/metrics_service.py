from datetime import datetime
from app.db import supabase


def get_client_metrics(client_slug: str):
    # Total mensajes (solo assistant para métricas reales)
    total_response = (
        supabase
        .table("messages")
        .select("id", count="exact")
        .eq("client_slug", client_slug)
        .eq("role", "assistant")
        .execute()
    )

    total_messages = total_response.count or 0

    # Tokens y latencia promedio
    tokens_response = (
        supabase
        .table("messages")
        .select("total_tokens, duration_ms")
        .eq("client_slug", client_slug)
        .eq("role", "assistant")
        .execute()
    )

    total_tokens = 0
    total_latency = 0
    latency_count = 0

    for row in tokens_response.data:
        if row["total_tokens"]:
            total_tokens += row["total_tokens"]

        if row["duration_ms"]:
            total_latency += row["duration_ms"]
            latency_count += 1

    avg_latency = (
        round(total_latency / latency_count, 2)
        if latency_count > 0
        else 0
    )

    # Mensajes este mes
    start_of_month = datetime.utcnow().replace(day=1)

    monthly_response = (
        supabase
        .table("messages")
        .select("id", count="exact")
        .eq("client_slug", client_slug)
        .eq("role", "assistant")
        .gte("created_at", start_of_month.isoformat())
        .execute()
    )

    messages_this_month = monthly_response.count or 0

    return {
        "total_messages": total_messages,
        "total_tokens": total_tokens,
        "avg_latency_ms": avg_latency,
        "messages_this_month": messages_this_month,
    }
