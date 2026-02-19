from openai import OpenAI
from app.core.semantic_search import search
from app.config import settings
import logging
import time

from app.core.request_context import get_request_id, get_client_slug

logger = logging.getLogger("rag")

client = OpenAI(api_key=settings.openai_api_key)

MAX_CHUNKS = 5


def build_context(chunks):
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(
            f"[Fuente {i}]\n"
            f"Título: {c.get('title', '')}\n"
            f"URL: {c.get('url', '')}\n"
            f"Contenido:\n{c['text']}"
        )
    return "\n\n".join(parts)


def build_sources(chunks):
    seen = set()
    sources = []
    for c in chunks:
        if c["url"] not in seen:
            seen.add(c["url"])
            sources.append(c["url"])
    return sources


def ask(client_id: str, question: str):
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

    chunks = search(client_id, question)

    if not chunks:
        logger.info(
            "rag_no_chunks_found",
            extra={
                "request_id": request_id,
                "client_slug": client_slug,
            },
        )
        return "No dispongo de esa información.", []

    context = build_context(chunks[:MAX_CHUNKS])
    sources = build_sources(chunks)

    prompt = f"""
Eres un asistente de atención al cliente de una clínica oftalmológica.

INSTRUCCIONES OBLIGATORIAS:
- Usa ÚNICAMENTE la información del contexto.
- No completes con conocimiento externo.
- No hagas suposiciones.
- Si la respuesta no está explícitamente en el contexto, responde exactamente:
  "No dispongo de esa información."
- Responde en español neutro.
- Máximo 120 palabras.

Contexto:
{context}

Pregunta:
{question}

Respuesta:
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    duration = (time.time() - start_time) * 1000

    logger.info(
        "rag_completed",
        extra={
            "request_id": request_id,
            "client_slug": client_slug,
            "duration_ms": round(duration, 2),
            "documents_used": len(chunks[:MAX_CHUNKS]),
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

