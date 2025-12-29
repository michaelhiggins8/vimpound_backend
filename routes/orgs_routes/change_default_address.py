from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import get_current_user
from db import pool

router = APIRouter()


class ChangeDefaultAddressRequest(BaseModel):
    default_address: str


@router.patch("/orgs/default-address")
async def change_default_address(
    body: ChangeDefaultAddressRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update the default_address column in the orgs table for the user's organization.
    Requires authentication via Bearer token in Authorization header.
    """
    
    user_id = current_user['id']
    
    # Update the default_address in orgs table
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE orgs
                SET default_address = %s
                FROM profiles
                WHERE orgs.id = profiles.org_id AND profiles.id = %s
                """,
                (body.default_address, user_id)
            )
            
            # Check if any rows were updated
            if cur.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No organization found for this user"
                )
            
            conn.commit()
    
    return {"message": "Default address updated successfully", "default_address": body.default_address}
