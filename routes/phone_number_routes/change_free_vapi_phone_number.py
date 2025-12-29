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

router = APIRouter()


class ChangeVapiNumberRequest(BaseModel):
    # Optional: The webhook URL Vapi will call (your /vapi route)
    # Required if area_code is provided and existing number has no server_url
    server_url: AnyHttpUrl | None = None

    # Optional: 3-digit US area code for the free number (e.g. "415")
    # If provided, creates a new phone number with this area code and deletes the old one
    area_code: str | None = None

    # Optional: nice label in the Vapi dashboard
    name: str | None = None


@router.patch("/vapi/phone-numbers/free")
async def change_free_vapi_phone_number(
    body: ChangeVapiNumberRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Change/update an existing FREE Vapi phone number configuration.
    - If area_code is provided: Creates a new phone number with that area code and deletes the old one
    - Otherwise: Updates server URL and/or name on the existing number
    Requires authentication via Bearer token in Authorization header.
    """
    
    user_id = current_user['id']
    
    # Step 1: Get phone_id from orgs table using current_user id
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT orgs.phone_id, orgs.phone_number
                FROM orgs
                JOIN profiles ON orgs.id = profiles.org_id
                WHERE profiles.id = %s
                LIMIT 1
                """,
                (user_id,)
            )
            row = cur.fetchone()
            
            if not row or not row[0]:
                raise HTTPException(
                    status_code=404,
                    detail="No phone number found for this user's organization"
                )
            
            old_phone_id = row[0]
            existing_phone_number = row[1]
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # Step 2: Handle area_code change (create new number) vs regular update
    if body.area_code:
        # Get existing phone number details to retrieve server_url if not provided
        server_url_to_use = body.server_url
        
        if not server_url_to_use:
            # Fetch existing phone number to get its server URL
            async with httpx.AsyncClient(timeout=30.0) as client:
                get_resp = await client.get(
                    f"https://api.vapi.ai/phone-number/{old_phone_id}",
                    headers=headers
                )
                
                if get_resp.status_code not in (200, 201):
                    raise HTTPException(
                        status_code=get_resp.status_code,
                        detail={"error": f"Failed to fetch existing phone number: {get_resp.text}"},
                    )
                
                existing_phone_data = get_resp.json()
                # Get server URL from existing phone number
                server_data = existing_phone_data.get("server", {})
                if server_data and server_data.get("url"):
                    server_url_to_use = server_data["url"]
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="server_url is required when changing area code, and existing number has no server_url configured"
                    )
        
        # Create new phone number with the desired area code
        create_payload = {
            "provider": "vapi",
            "numberDesiredAreaCode": body.area_code,
            "server": {
                "url": str(server_url_to_use),
                "timeoutSeconds": 20,
            },
        }
        
        if body.name:
            create_payload["name"] = body.name
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            create_resp = await client.post(
                "https://api.vapi.ai/phone-number",
                json=create_payload,
                headers=headers
            )
        
        if create_resp.status_code not in (200, 201):
            raise HTTPException(
                status_code=create_resp.status_code,
                detail={"error": f"Failed to create new phone number: {create_resp.text}"},
            )
        
        new_phone_data = create_resp.json()
        new_phone_id = new_phone_data["id"]
        new_phone_number = new_phone_data["number"]
        
        # Delete the old phone number
        async with httpx.AsyncClient(timeout=30.0) as client:
            delete_resp = await client.delete(
                f"https://api.vapi.ai/phone-number/{old_phone_id}",
                headers=headers
            )
        
        # Note: Don't fail if delete fails - the new number is created and we'll update DB
        if delete_resp.status_code not in (200, 201, 204):
            print(f"Warning: Failed to delete old phone number {old_phone_id}: {delete_resp.text}")
        
        # Update orgs table with new phone number
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE orgs
                    SET phone_number = %s, phone_id = %s
                    FROM profiles
                    WHERE orgs.id = profiles.org_id AND profiles.id = %s
                    """,
                    (new_phone_number, new_phone_id, user_id)
                )
                conn.commit()
        
        return new_phone_data
    
    else:
        # Regular update: Update server URL and/or name on existing number
        payload = {}
        
        if body.server_url:
            payload["server"] = {
                "url": str(body.server_url),
                "timeoutSeconds": 20,
            }
        
        if body.name:
            payload["name"] = body.name
        
        # If no fields to update, return early
        if not payload:
            raise HTTPException(
                status_code=400,
                detail="At least one field (server_url, name, or area_code) must be provided to update"
            )
        
        # Update the phone number in VAPI
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.patch(
                f"https://api.vapi.ai/phone-number/{old_phone_id}",
                json=payload,
                headers=headers
            )
        
        if resp.status_code not in (200, 201):
            raise HTTPException(
                status_code=resp.status_code,
                detail={"error": resp.text},
            )
        
        print("resp.json(): ", resp.json())
        
        # Get updated phone number from response
        updated_phone_number = resp.json().get("number", existing_phone_number)
        
        # Update the orgs table to reflect any changes
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE orgs
                    SET phone_number = %s, phone_id = %s
                    FROM profiles
                    WHERE orgs.id = profiles.org_id AND profiles.id = %s
                    """,
                    (updated_phone_number, old_phone_id, user_id)
                )
                conn.commit()
        
        return resp.json()
