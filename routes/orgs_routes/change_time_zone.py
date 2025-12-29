from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import get_current_user
from db import pool

router = APIRouter()


class ChangeTimeZoneRequest(BaseModel):
    time_zone: str


@router.patch("/orgs/time-zone")
async def change_time_zone(
    body: ChangeTimeZoneRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update the time_zone column in the orgs table for the user's organization.
    Requires authentication via Bearer token in Authorization header.
    """
    
    user_id = current_user['id']
    
    # Update the time_zone in orgs table
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE orgs
                SET time_zone = %s
                FROM profiles
                WHERE orgs.id = profiles.org_id AND profiles.id = %s
                """,
                (body.time_zone, user_id)
            )
            
            # Check if any rows were updated
            if cur.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No organization found for this user"
                )
            
            conn.commit()
    
    return {"message": "Time zone updated successfully", "time_zone": body.time_zone}
