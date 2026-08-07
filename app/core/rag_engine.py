import asyncio
from openai import OpenAI
from app.core.semantic_search import search
from app.config import settings
import logging
import time
from pathlib import Path
from app.core.vector_store import load_index

from app.core.request_context import get_request_id, get_client_slug
from app.services.client_registry_service import get_registry_client

logger = logging.getLogger("rag")

client = OpenAI(api_key=settings.openai_api_key)

MAX_CHUNKS = 5
MAX_CONTEXT_CHARS = 6000
MAX_HISTORY_CHARS = 4000

BASE_DIR = Path("clients")


def load_client_prompt(client_slug: str):
    try:
        registry_client = get_registry_client(client_slug)
    except Exception as exc:
        print(f"[PROMPT WARNING] registry lookup failed for {client_slug}: {exc}")
        registry_client = None

    if registry_client and registry_client.get("prompt"):
        return registry_client["prompt"]

    prompt_path = BASE_DIR / client_slug / "prompt.txt"

    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")

    return """
Eres un asistente útil. Responde de forma clara, breve y honesta.
Si no tienes suficiente información, dilo.
"""


def build_context(chunks):

    parts = []
    total_chars = 0

    for i, c in enumerate(chunks, 1):

        text = c["text"]

        if total_chars + len(text) > MAX_CONTEXT_CHARS:
            break

        parts.append(
            f"[Fuente {i}]\n"
            f"Título: {c.get('title', '')}\n"
            f"URL: {c.get('url', '')}\n"
            f"Contenido:\n{text}"
        )

        total_chars += len(text)

    return "\n\n".join(parts)


def build_sources(chunks):

    seen = set()
    sources = []

    for c in chunks:
        url = c.get("url")

        if url and url not in seen:
            seen.add(url)
            sources.append(url)

    return sources


def build_history(messages: list[dict]):
    parts = []
    total_chars = 0

    for message in reversed(messages):
        role = message.get("role")
        content = message.get("content", "")

        if role not in {"user", "assistant"} or not content:
            continue

        entry = f"{role}: {content}"
        if total_chars + len(entry) > MAX_HISTORY_CHARS:
            break

        parts.append(entry)
        total_chars += len(entry)

    return "\n".join(reversed(parts))


async def ask(
    client_id: str,
    question: str,
    history: list[dict] | None = None,
    prompt_override: str | None = None,
):

    start_time = time.time()

    request_id = get_request_id()
    client_slug = get_client_slug() or client_id

    logger.info(
        "rag_started",
        extra={
            "request_id": request_id,
            "client_slug": client_slug,
        },
    )

    index, metadata = load_index(client_id)

    if index is None:

        logger.info(
            "rag_prompt_only_mode",
            extra={
                "request_id": request_id,
                "client_slug": client_slug,
            },
        )

        chunks = []

    else:

        chunks = search(client_id, question)

    if not chunks:

        logger.info(
            "rag_no_chunks_found",
            extra={
                "request_id": request_id,
                "client_slug": client_slug,
            },
        )

        context = ""
        sources = []

    else:

        context = build_context(chunks[:MAX_CHUNKS])
        sources = build_sources(chunks)

    client_prompt = prompt_override or load_client_prompt(client_slug)
    conversation_history = build_history(history or [])

    prompt = f"""Instrucciones del asistente:
{client_prompt}

Reglas de memoria conversacional:
- Usa el historial para mantener continuidad dentro de esta conversación.
- No vuelvas a pedir datos que el usuario ya dio, salvo que sean ambiguos o contradictorios.
- Si el usuario corrige un dato anterior, toma como válido el dato más reciente.

Historial de esta conversación:
{conversation_history or "No hay historial previo."}

Contexto disponible:
{context or "No hay contexto adicional."}

Pregunta del usuario:
{question}"""

    response = await asyncio.wait_for(
        asyncio.to_thread(
            client.responses.create,
            model=settings.openai_model,
            input=prompt,
            temperature=0,
        ),
        timeout=settings.openai_timeout_seconds,
    )

    duration = (time.time() - start_time) * 1000

    logger.info(
        "rag_completed",
        extra={
            "request_id": request_id,
            "client_slug": client_slug,
            "duration_ms": round(duration, 2),
            "documents_used": len(chunks[:MAX_CHUNKS]) if chunks else 0,
        },
    )

    usage = response.usage

    return (
        response.output_text.strip(),
        sources,
        {
            "tokens_prompt": usage.input_tokens if usage else None,
            "tokens_completion": usage.output_tokens if usage else None,
            "total_tokens": usage.total_tokens if usage else None,
            "duration_ms": round(duration, 2),
        }
    )
