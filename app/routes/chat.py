from pydantic import BaseModel
from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException

from app.core.auth import authenticate_client
from app.core.request_context import set_client_slug
from app.services.chat_service import handle_chat

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: Request,
    body: ChatRequest,
    background_tasks: BackgroundTasks,
    client: dict = Depends(authenticate_client),
):
    try:
        # 🔐 Identify client
        client_slug = client["slug"]
        set_client_slug(client_slug)

        # 🌐 Optional domain validation
        origin = request.headers.get("origin")
        allowed_domains = client.get("allowed_domains")

        if allowed_domains and origin:
            if origin not in allowed_domains:
                raise HTTPException(status_code=403, detail="Domain not allowed")

        # 🤖 Main chat handler
        result = await handle_chat(
            client_slug=client_slug,
            question=body.question,
            session_id=body.session_id,
            background_tasks=background_tasks,
        )

        return ChatResponse(**result)

    except HTTPException:
        # Re-throw FastAPI errors as-is
        raise

    except Exception as e:
        # Prevent silent 500 crashes
        print(f"[CHAT ERROR] client={client.get('slug')} error={str(e)}")
        raise HTTPException(status_code=500, detail="Chat processing error")