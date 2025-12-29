from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import get_current_user
from db import pool

router = APIRouter()


class UpdateExceptionDateRequest(BaseModel):
    id: str
    hours: str


@router.patch("/orgs/exception-dates")
async def update_exception_date(
    body: UpdateExceptionDateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update the hours column of an exception date entry in the exception_dates table.
    Requires authentication via Bearer token in Authorization header.
    
    Request body:
    - id (str): The UUID of the exception date entry to update
    - hours (str): The new hours value (TEXT format)
    
    The route verifies that the exception date belongs to the user's organization
    before updating it.
    """
    
    user_id = current_user['id']
    
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # First, verify the exception date exists and belongs to the user's organization
                cur.execute(
                    """
                    SELECT ed.id
                    FROM exception_dates ed
                    INNER JOIN profiles p ON ed.org_id = p.org_id
                    WHERE ed.id = %s AND p.id = %s
                    LIMIT 1
                    """,
                    (body.id, user_id)
                )
                
                row = cur.fetchone()
                
                if not row:
                    raise HTTPException(
                        status_code=404,
                        detail="Exception date not found or does not belong to your organization"
                    )
                
                # Update the hours column
                cur.execute(
                    """
                    UPDATE exception_dates
                    SET hours = %s
                    WHERE id = %s
                    """,
                    (body.hours, body.id)
                )
                
                conn.commit()
                
                return {
                    "message": "Exception date updated successfully",
                    "id": body.id,
                    "hours": body.hours
                }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating exception date: {str(e)}"
        )
