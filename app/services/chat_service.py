import uuid

from app.core.rag_engine import ask, load_client_registry_context
from app.services.conversation_service import (
    get_or_create_conversation,
    reset_conversation,
)
from app.services.message_service import insert_message, list_conversation_messages
from app.services.session_memory import load_messages, reset_session, save_messages
from app.services.lead_service import capture_lead_from_conversation


async def handle_chat(
    client_slug: str,
    question: str,
    session_id: str | None,
    reset: bool = False,
):
    session_id = session_id or str(uuid.uuid4())
    conversation = None

    if reset:
        try:
            reset_conversation(client_slug, session_id)
        except Exception as e:
            print(f"[MEMORY WARNING] could not reset Supabase conversation: {e}")
        reset_session(client_slug, session_id)

    try:
        conversation = get_or_create_conversation(client_slug, session_id)
        if conversation:
            history = list_conversation_messages(conversation["id"])
        else:
            history = load_messages(client_slug, session_id)
    except Exception as e:
        print(f"[MEMORY WARNING] using local JSON fallback: {e}")
        history = load_messages(client_slug, session_id)

    answer, sources, usage_data = await ask(client_slug, question, history)

    history.extend(
        [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]
    )
    save_messages(client_slug, session_id, history)

    if conversation:
        try:
            insert_message(
                conversation_id=conversation["id"],
                client_slug=client_slug,
                role="user",
                content=question,
            )
            insert_message(
                conversation_id=conversation["id"],
                client_slug=client_slug,
                role="assistant",
                content=answer,
                tokens_prompt=usage_data.get("tokens_prompt"),
                tokens_completion=usage_data.get("tokens_completion"),
                total_tokens=usage_data.get("total_tokens"),
                duration_ms=usage_data.get("duration_ms"),
            )
        except Exception as e:
            print(f"[MEMORY WARNING] could not save Supabase messages: {e}")

    try:
        prompt, config = load_client_registry_context(client_slug)
        await capture_lead_from_conversation(
            client_slug=client_slug,
            conversation_id=conversation["id"] if conversation else None,
            session_id=session_id,
            config=config,
            prompt=prompt,
            history=history,
        )
    except Exception as e:
        print(f"[LEAD WARNING] could not capture lead: {e}")

    return {
        "answer": answer,
        "sources": sources,
        "session_id": session_id,
        "usage": usage_data,
    }
