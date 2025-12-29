from fastapi import APIRouter, HTTPException, Depends
from auth import get_current_user
from db import pool

router = APIRouter()


@router.get("/phone-number")
async def get_vapi_phone_number_from_database(
    current_user: dict = Depends(get_current_user)
):
    """
    Get the phone_number (TEXT) column from the orgs table for the user's organization.
    Returns the phone_number value where orgs.id matches profiles.org_id 
    and profiles.id matches the authenticated user's ID.
    Requires authentication via Bearer token in Authorization header.
    """
    
    user_id = current_user['id']
    
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Query to get phone_number for the user's organization
                cur.execute(
                    """
                    SELECT 
                        o.phone_number
                    FROM orgs o
                    INNER JOIN profiles p ON o.id = p.org_id
                    WHERE p.id = %s
                    """,
                    (user_id,)
                )
                
                row = cur.fetchone()
                
                # Check if organization was found
                if not row:
                    raise HTTPException(
                        status_code=404,
                        detail="No organization found for this user"
                    )
                
                phone_number = row[0]
                
                return {
                    "phone_number": phone_number
                }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching phone number: {str(e)}"
        )
