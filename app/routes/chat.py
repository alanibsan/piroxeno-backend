from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.core.rate_limit import check_rate_limit
from app.core.request_context import set_client_slug
from app.services.chat_service import handle_chat
from app.services.client_config import validate_client_access

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = Field(default=None, pattern=r"^[a-zA-Z0-9_-]+$")
    client_slug: str | None = Field(default=None, pattern=r"^[a-zA-Z0-9_-]+$")
    reset: bool = False


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    session_id: str
    usage: dict | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: Request,
    body: ChatRequest,
):
    try:
        client_slug = body.client_slug or settings.default_client_slug
        client_config = validate_client_access(client_slug, request)
        ip = request.client.host if request.client else "unknown"
        check_rate_limit(
            key=f"{client_slug}:{ip}",
            limit=client_config.get(
                "rate_limit_per_minute",
                settings.default_rate_limit_per_minute,
            ),
        )
        set_client_slug(client_slug)

        result = await handle_chat(
            client_slug=client_slug,
            question=body.question,
            session_id=body.session_id,
            reset=body.reset,
        )

        return ChatResponse(**result)

    except HTTPException:
        # Re-throw FastAPI errors as-is
        raise

    except Exception as e:
        print(f"[CHAT ERROR] client={body.client_slug or settings.default_client_slug} error={str(e)}")
        raise HTTPException(status_code=500, detail="Chat processing error")
