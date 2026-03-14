from openai import OpenAI
from app.core.semantic_search import search
from app.config import settings
import logging
import time
from pathlib import Path
from app.core.vector_store import load_index

from app.core.request_context import get_request_id, get_client_slug

logger = logging.getLogger("rag")

client = OpenAI(api_key=settings.openai_api_key)

MAX_CHUNKS = 5
MAX_CONTEXT_CHARS = 6000

BASE_DIR = Path("clients")


def load_client_prompt(client_slug: str):

    prompt_path = BASE_DIR / client_slug / "prompt.txt"

    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")

    # fallback prompt
    return """
Eres un asistente genérico. Este prompt solo se activa si el cliente no tiene un prompt personalizado o está fallando.

INSTRUCCIONES OBLIGATORIAS:
- Ahora mismo esto está en testing.
- Solo responde exactamente con la palabra: TESTING
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


async def ask(client_id: str, question: str):

    start_time = time.time()

    request_id = get_request_id()
    client_slug = get_client_slug()

    logger.info(
        "rag_started",
        extra={
            "request_id": request_id,
            "client_slug": client_slug,
        },
    )

    # 🔎 verificar si existe vector store
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

    # ⚡ SI NO HAY CHUNKS → usar solo el prompt
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

    client_prompt = load_client_prompt(client_slug)

    prompt = f"""
{client_prompt}

Contexto:
{context}

Pregunta:
{question}

Respuesta:
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        temperature=0
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