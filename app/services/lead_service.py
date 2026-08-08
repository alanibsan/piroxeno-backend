import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Any

from openai import OpenAI

from app.config import settings
from app.db import get_supabase


client = OpenAI(api_key=settings.openai_api_key)

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")


def _lead_columns(config: dict[str, Any]) -> list[dict[str, str]]:
    columns = config.get("lead_columns") or []
    normalized = []
    for column in columns:
        if isinstance(column, str):
            key = re.sub(r"[^a-z0-9]+", "_", column.lower()).strip("_")
            if key:
                normalized.append({"key": key, "label": column})
        elif isinstance(column, dict):
            key = str(column.get("key") or "").strip()
            label = str(column.get("label") or key).strip()
            if key and label:
                normalized.append({"key": key, "label": label})
    return normalized


def _extract_contact(text: str):
    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)
    email = email_match.group(0).lower() if email_match else None
    phone = re.sub(r"\s+", " ", phone_match.group(0)).strip() if phone_match else None
    return email, phone


def _fallback_interest(text: str):
    compact = " ".join(text.split())
    if not compact:
        return None
    return compact[:180]


async def _extract_with_model(
    *,
    prompt: str,
    transcript: str,
    columns: list[dict[str, str]],
):
    if not columns:
        return {}, None

    column_lines = "\n".join(f"- {column['key']}: {column['label']}" for column in columns)
    extraction_prompt = f"""Extrae datos de lead desde una conversacion de chatbot.

Prompt del cliente:
{prompt}

Columnas configuradas:
{column_lines}

Conversacion reciente:
{transcript}

Devuelve solo JSON valido con esta forma:
{{"interest":"resumen breve del servicio o necesidad", "fields": {{"key":"valor"}}}}
Incluye solo campos que puedas inferir con claridad. No inventes datos."""

    response = await asyncio.wait_for(
        asyncio.to_thread(
            client.responses.create,
            model=settings.openai_model,
            input=extraction_prompt,
            temperature=0,
        ),
        timeout=8,
    )
    text = response.output_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    parsed = json.loads(text)
    fields = parsed.get("fields") if isinstance(parsed.get("fields"), dict) else {}
    allowed_keys = {column["key"] for column in columns}
    fields = {key: value for key, value in fields.items() if key in allowed_keys and value not in (None, "")}
    interest = parsed.get("interest") if isinstance(parsed.get("interest"), str) else None
    return fields, interest


async def capture_lead_from_conversation(
    *,
    client_slug: str,
    conversation_id: str | None,
    session_id: str,
    config: dict[str, Any],
    prompt: str,
    history: list[dict],
):
    supabase = get_supabase()
    if supabase is None:
        return None

    transcript = "\n".join(
        f"{message.get('role')}: {message.get('content')}"
        for message in history[-10:]
        if message.get("role") in {"user", "assistant"} and message.get("content")
    )
    email, phone = _extract_contact(transcript)
    if not email and not phone:
        return None

    columns = _lead_columns(config)
    fields: dict[str, Any] = {}
    interest = None
    try:
        fields, interest = await _extract_with_model(
            prompt=prompt,
            transcript=transcript,
            columns=columns,
        )
    except Exception as exc:
        print(f"[LEAD WARNING] extraction fallback client={client_slug} error={exc}")

    payload = {
        "client_slug": client_slug,
        "conversation_id": conversation_id,
        "session_id": session_id,
        "email": email,
        "phone": phone,
        "interest": interest or fields.get("interest") or _fallback_interest(transcript),
        "fields": fields,
        "source": "chatbot",
    }

    existing_query = supabase.table("leads").select("id").eq("client_slug", client_slug)
    if email:
        existing_query = existing_query.eq("email", email)
    elif phone:
        existing_query = existing_query.eq("phone", phone)
    existing = existing_query.limit(1).execute().data or []

    if existing:
        response = (
            supabase.table("leads")
            .update({**payload, "last_seen_at": datetime.now(timezone.utc).isoformat()})
            .eq("id", existing[0]["id"])
            .execute()
        )
    else:
        response = supabase.table("leads").insert(payload).execute()

    return response.data[0] if response.data else payload


def lead_capture_instructions(config: dict[str, Any]):
    columns = _lead_columns(config)
    if not columns:
        return ""
    labels = ", ".join(column["label"] for column in columns)
    return (
        "\n\nObjetivo de captura de leads:\n"
        "- Si el usuario muestra interés, intenta obtener email o telefono de forma natural.\n"
        f"- Cuando sea relevante, consigue estos datos para el lead: {labels}.\n"
        "- No preguntes todo de golpe; pide solo el siguiente dato útil."
    )
