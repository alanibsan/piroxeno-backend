from fastapi import APIRouter, Depends, Query

from app.core.admin_auth import require_user
from app.services.portal_service import (
    get_portal_conversation_messages,
    get_portal_docs,
    get_portal_summary,
    list_portal_clients,
    list_portal_conversations,
)


router = APIRouter(prefix="/portal", tags=["portal"])


@router.get("/clients")
def portal_clients(user: dict = Depends(require_user)):
    return {"clients": list_portal_clients(user)}


@router.get("/summary")
def portal_summary(
    client_slug: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    user: dict = Depends(require_user),
):
    return get_portal_summary(user, client_slug, start_date, end_date)


@router.get("/conversations")
def portal_conversations(
    client_slug: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    user: dict = Depends(require_user),
):
    return {
        "conversations": list_portal_conversations(
            user,
            client_slug=client_slug,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    }


@router.get("/conversations/{conversation_id}/messages")
def portal_conversation_messages(conversation_id: str, user: dict = Depends(require_user)):
    return get_portal_conversation_messages(user, conversation_id)


@router.get("/docs")
def portal_docs(lang: str = "es", user: dict = Depends(require_user)):
    return {"docs": get_portal_docs(user, lang)}
