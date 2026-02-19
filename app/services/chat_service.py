import time
import uuid
from fastapi import BackgroundTasks

from app.services.conversation_service import get_or_create_conversation
from app.services.message_service import insert_message
from app.core.rag_engine import ask


def handle_chat(
    client_slug: str,
    question: str,
    session_id: str | None,
    background_tasks: BackgroundTasks,
):
    # 1️⃣ Generar session_id si no viene
    session_id = session_id or str(uuid.uuid4())

    # 2️⃣ Obtener o crear conversación
    conversation = get_or_create_conversation(client_slug, session_id)
    conversation_id = conversation["id"]

    # 3️⃣ Guardar mensaje del usuario
    insert_message(
        conversation_id=conversation_id,
        client_slug=client_slug,
        role="user",
        content=question,
    )

    # 4️⃣ Ejecutar RAG
    start_time = time.time()
    answer, sources, usage_data = ask(client_slug, question)


    # ⚠️ ya capturando tokens

    background_tasks.add_task(
        insert_message,
        conversation_id,
        client_slug,
        "assistant",
        answer,
        usage_data["tokens_prompt"],
        usage_data["tokens_completion"],
        usage_data["total_tokens"],
        usage_data["duration_ms"],
    )


    return {
        "answer": answer,
        "sources": sources,
        "session_id": session_id,
    }
