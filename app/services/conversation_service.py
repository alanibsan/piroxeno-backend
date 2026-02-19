from app.db import supabase


def get_or_create_conversation(client_slug: str, session_id: str):
    # Buscar conversación existente
    response = (
        supabase
        .table("conversations")
        .select("*")
        .eq("client_slug", client_slug)
        .eq("session_id", session_id)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    # Crear nueva conversación
    insert_response = (
        supabase
        .table("conversations")
        .insert({
            "client_slug": client_slug,
            "session_id": session_id
        })
        .execute()
    )

    return insert_response.data[0]
