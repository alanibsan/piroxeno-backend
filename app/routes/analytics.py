from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.services.website_analytics_service import track_website_event


router = APIRouter(prefix="/analytics", tags=["analytics"])


class WebsiteEventRequest(BaseModel):
    site: str = "piroxeno"
    event_name: str = "page_view"
    path: str | None = Field(default=None, max_length=500)
    url: str | None = Field(default=None, max_length=1000)
    referrer: str | None = Field(default=None, max_length=1000)
    title: str | None = Field(default=None, max_length=300)
    language: str | None = Field(default=None, max_length=40)
    timezone: str | None = Field(default=None, max_length=80)
    screen_width: int | None = None
    screen_height: int | None = None
    visitor_id: str | None = Field(default=None, max_length=120)
    session_id: str | None = Field(default=None, max_length=120)
    metadata: dict[str, Any] = {}


@router.post("/event")
def analytics_event(request: Request, body: WebsiteEventRequest):
    return track_website_event(request, body.model_dump())
