# main.py

import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, AnyHttpUrl
import httpx
from auth import get_current_user
from db import pool
load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
if not VAPI_API_KEY:
    raise RuntimeError("VAPI_API_KEY is not set in .env")

SERVER_URL = os.getenv("SERVER_URL")
if not SERVER_URL:
    raise RuntimeError("SERVER_URL is not set in .env")

router = APIRouter()


class CreateVapiNumberRequest(BaseModel):
    # This is the webhook URL Vapi will call (your /vapi route)
    server_url: AnyHttpUrl | None = None

    # 3-digit US area code for the free number (e.g. "415")
    area_code: str

    # Optional: nice label in the Vapi dashboard
    name: str | None = None


@router.post("/vapi/phone-numbers/free")
async def create_free_vapi_phone_number(
    body: CreateVapiNumberRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a FREE Vapi phone number (one of your 10),
    configured to call your FastAPI server URL.
    Requires authentication via Bearer token in Authorization header.
    """
    
    # Print the user ID
  
    print("--------------------------------")
    print("--------------------------------")
    print(f"User ID: {current_user['id']}")
    print("--------------------------------")
    print("--------------------------------")
    
    # Use provided server_url or default to SERVER_URL from .env
    server_url = str(body.server_url) if body.server_url else SERVER_URL
    
    payload = {
        # Free Vapi-owned number
        "provider": "vapi",
        # Area code so Vapi can allocate a number in that region
        "numberDesiredAreaCode": body.area_code,
        # Server URL so calls hit your backend
        "server": {
            "url": server_url,
            "timeoutSeconds": 20,
        },
    }

    if body.name:
        payload["name"] = body.name

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }

    url = "https://api.vapi.ai/phone-number"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload, headers=headers)

    if resp.status_code not in (200, 201):
        # Bubble the Vapi error back out so you can see what's wrong
        raise HTTPException(
            status_code=resp.status_code,
            detail={"error": resp.text},
        )
    print("resp.json(): ", resp.json())

    phone_number_id = resp.json()["id"]
    phone_number = resp.json()["number"]
    user_id = current_user['id']

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE orgs
                SET phone_number = %s, phone_id = %s
                FROM profiles
                WHERE orgs.id = profiles.org_id AND profiles.id = %s
                """,
                (phone_number, phone_number_id, user_id)
            )
            conn.commit()
    

    # On success, return the phone number object Vapi created
    return resp.json()
