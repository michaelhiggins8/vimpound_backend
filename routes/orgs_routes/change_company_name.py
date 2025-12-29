from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import get_current_user
from db import pool

router = APIRouter()


class ChangeCompanyNameRequest(BaseModel):
    company_name: str


@router.patch("/orgs/company-name")
async def change_company_name(
    body: ChangeCompanyNameRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update the company_name column in the orgs table for the user's organization.
    Requires authentication via Bearer token in Authorization header.
    """
    
    user_id = current_user['id']
    
    # Update the company_name in orgs table
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE orgs
                SET company_name = %s
                FROM profiles
                WHERE orgs.id = profiles.org_id AND profiles.id = %s
                """,
                (body.company_name, user_id)
            )
            
            # Check if any rows were updated
            if cur.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No organization found for this user"
                )
            
            conn.commit()
    
    return {"message": "Company name updated successfully", "company_name": body.company_name}
