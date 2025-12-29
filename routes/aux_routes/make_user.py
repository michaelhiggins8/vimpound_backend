from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import get_current_user
from db import pool

router = APIRouter()


class MakeUserRequest(BaseModel):
    user_id: str


@router.post("/make-user")
async def make_user(
    body: MakeUserRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new organization entry in the orgs table and a profile entry in the profiles table.
    This is called during the signup flow to establish the user's personhood in the system.
    Requires authentication via Bearer token in Authorization header.
    
    Request body:
    - user_id (str): The UUID of the user (will be used as profiles.id)
    
    Creates:
    1. An entry in the orgs table (id and created_at are auto-generated)
    2. An entry in the profiles table with the org_id from step 1 and user_id as profiles.id
    """
    
    user_id = body.user_id
    
    # Verify that the user_id in the body matches the authenticated user
    if user_id != current_user['id']:
        raise HTTPException(
            status_code=403,
            detail="User ID in request body does not match authenticated user"
        )
    
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Check if profile already exists
                cur.execute(
                    """
                    SELECT id, org_id, created_at
                    FROM profiles
                    WHERE id = %s
                    """,
                    (user_id,)
                )
                
                existing_profile = cur.fetchone()
                
                if existing_profile:
                    # Profile already exists, return existing data
                    return {
                        "message": "User profile already exists",
                        "org_id": str(existing_profile[1]),
                        "profile_id": str(existing_profile[0]),
                        "profile_created_at": str(existing_profile[2])
                    }
                
                # Step 1: Insert into orgs table (id and created_at will be auto-generated)
                cur.execute(
                    """
                    INSERT INTO orgs DEFAULT VALUES
                    RETURNING id, created_at
                    """
                )
                
                org_row = cur.fetchone()
                if not org_row:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to create organization"
                    )
                
                org_id = org_row[0]
                
                # Step 2: Insert into profiles table with org_id and user_id
                cur.execute(
                    """
                    INSERT INTO profiles (id, org_id)
                    VALUES (%s, %s)
                    RETURNING id, created_at, org_id
                    """,
                    (user_id, org_id)
                )
                
                profile_row = cur.fetchone()
                if not profile_row:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to create profile"
                    )
                
                conn.commit()
                
                return {
                    "message": "User created successfully",
                    "org_id": str(org_id),
                    "profile_id": str(profile_row[0]),
                    "org_created_at": str(org_row[1]),
                    "profile_created_at": str(profile_row[1])
                }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating user: {str(e)}"
        )
