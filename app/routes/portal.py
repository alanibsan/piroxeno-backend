from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query

from app.core.admin_auth import require_user
from app.services.portal_service import (
    get_portal_conversation_messages,
    get_portal_docs,
    list_portal_leads,
    get_portal_summary,
    list_portal_clients,
    list_portal_conversations,
    resolve_portal_user,
    run_demo_chat,
)


router = APIRouter(prefix="/portal", tags=["portal"])


class DemoChatRequest(BaseModel):
    prompt: str = Field(min_length=10)
    question: str = Field(min_length=1)
    session_id: str | None = Field(default=None, pattern=r"^[a-zA-Z0-9_-]+$")
    reset: bool = False


@router.get("/clients")
def portal_clients(
    impersonate_user_id: str | None = None,
    user: dict = Depends(require_user),
):
    portal_user = resolve_portal_user(user, impersonate_user_id)
    return {"clients": list_portal_clients(portal_user), "user": portal_user}


@router.get("/summary")
def portal_summary(
    client_slug: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    impersonate_user_id: str | None = None,
    user: dict = Depends(require_user),
):
    portal_user = resolve_portal_user(user, impersonate_user_id)
    return get_portal_summary(portal_user, client_slug, start_date, end_date)


@router.get("/conversations")
def portal_conversations(
    client_slug: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    impersonate_user_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    user: dict = Depends(require_user),
):
    portal_user = resolve_portal_user(user, impersonate_user_id)
    return {
        "conversations": list_portal_conversations(
            portal_user,
            client_slug=client_slug,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    }


@router.get("/conversations/{conversation_id}/messages")
def portal_conversation_messages(
    conversation_id: str,
    impersonate_user_id: str | None = None,
    user: dict = Depends(require_user),
):
    portal_user = resolve_portal_user(user, impersonate_user_id)
    return get_portal_conversation_messages(portal_user, conversation_id)


@router.get("/leads")
def portal_leads(
    client_slug: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 200,
    impersonate_user_id: str | None = None,
    user: dict = Depends(require_user),
):
    portal_user = resolve_portal_user(user, impersonate_user_id)
    return {
        "leads": list_portal_leads(
            portal_user,
            client_slug=client_slug,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    }


@router.get("/docs")
def portal_docs(
    lang: str = "es",
    impersonate_user_id: str | None = None,
    user: dict = Depends(require_user),
):
    portal_user = resolve_portal_user(user, impersonate_user_id)
    return {"docs": get_portal_docs(portal_user, lang)}


@router.post("/demo-chat")
async def portal_demo_chat(body: DemoChatRequest, user: dict = Depends(require_user)):
    return await run_demo_chat(
        user=user,
        prompt=body.prompt,
        question=body.question,
        session_id=body.session_id,
        reset=body.reset,
    )
