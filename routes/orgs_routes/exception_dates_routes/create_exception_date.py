from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import get_current_user
from db import pool

router = APIRouter()


class CreateExceptionDateRequest(BaseModel):
    date: str
    hours: str


@router.post("/orgs/exception-dates")
async def create_exception_date(
    body: CreateExceptionDateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new exception date entry in the exception_dates table.
    Requires authentication via Bearer token in Authorization header.
    
    Request body:
    - date (str): The date for the exception (TEXT format)
    - hours (str): The hours for the exception (TEXT format)
    
    The org_id will be automatically retrieved from the user's profile.
    """
    
    user_id = current_user['id']
    
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # First, get the org_id from the profiles table
                cur.execute(
                    """
                    SELECT org_id
                    FROM profiles
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (user_id,)
                )
                
                row = cur.fetchone()
                
                if not row or not row[0]:
                    raise HTTPException(
                        status_code=404,
                        detail="No organization found for this user"
                    )
                
                org_id = row[0]
                
                # Insert the new exception date entry
                cur.execute(
                    """
                    INSERT INTO exception_dates (date, hours, org_id)
                    VALUES (%s, %s, %s)
                    RETURNING date, hours, org_id
                    """,
                    (body.date, body.hours, org_id)
                )
                
                # Fetch the inserted row to return
                inserted_row = cur.fetchone()
                conn.commit()
                
                return {
                    "message": "Exception date created successfully",
                    "date": inserted_row[0],
                    "hours": inserted_row[1],
                    "org_id": str(inserted_row[2])
                }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating exception date: {str(e)}"
        )
