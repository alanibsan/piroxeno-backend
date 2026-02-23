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

    try:
        result = supabase.table("demo_requests").insert({
            "first_name": data.first_name,
            "last_name": data.last_name,
            "phone": data.phone,
            "email": data.email,
            "job_title": data.job_title,
            "company": data.company,
        }).execute()

        return {"success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))