from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.db import supabase

router = APIRouter()


class DemoRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: EmailStr
    job_title: str
    company: str


@router.post("/request-demo")
async def request_demo(data: DemoRequest):

    response = (
        supabase
        .table("demo_requests")
        .insert(data.dict())
        .execute()
    )

    if response.error:
        raise HTTPException(status_code=500, detail="Could not save request")

    return {"success": True}