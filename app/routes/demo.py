from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.db import supabase
import os
import requests

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

            resend_key = os.getenv("RESEND_API_KEY")

            requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "Demo Request <alan@leads.piroxeno.com>",
                    "to": "ibarrasantoyo.a@gmail.com",
                    "subject": "🚀 New Demo Request",
                    "html": f"""
                    <h2>New Demo Request</h2>
                    <p><strong>Name:</strong> {data.first_name} {data.last_name}</p>
                    <p><strong>Email:</strong> {data.email}</p>
                    <p><strong>Phone:</strong> {data.phone}</p>
                    <p><strong>Company:</strong> {data.company}</p>
                    <p><strong>Job Title:</strong> {data.job_title}</p>
                    """
                }
            )

        return {"success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))