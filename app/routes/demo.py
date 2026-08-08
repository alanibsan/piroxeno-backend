from typing import Optional
from html import escape

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.config import settings
from app.db import get_supabase
from app.services.email_service import send_html_email

router = APIRouter()


class DemoRequest(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None


@router.post("/request-demo")
async def request_demo(data: DemoRequest):

    try:
        supabase = get_supabase()
        if supabase is None:
            raise HTTPException(status_code=503, detail="Supabase is not configured")

        # Insert lead into Supabase
        supabase.table("demo_requests").insert({
            "email": data.email,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "phone": data.phone,
            "job_title": data.job_title,
            "company": data.company,
            "source": data.source
        }).execute()

        # Only send email if full form was submitted
        if data.first_name:
            send_html_email(
                to_email=settings.demo_notification_email,
                subject="New Demo Request",
                html=f"""
                <h2>New Demo Request</h2>
                <p><strong>Name:</strong> {escape(data.first_name or "")} {escape(data.last_name or "")}</p>
                <p><strong>Email:</strong> {escape(data.email)}</p>
                <p><strong>Phone:</strong> {escape(data.phone or "")}</p>
                <p><strong>Company:</strong> {escape(data.company or "")}</p>
                <p><strong>Job Title:</strong> {escape(data.job_title or "")}</p>
                """,
            )

        return {"success": True}

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
