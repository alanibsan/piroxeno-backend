from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.db import supabase
import os
import requests

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
    
    