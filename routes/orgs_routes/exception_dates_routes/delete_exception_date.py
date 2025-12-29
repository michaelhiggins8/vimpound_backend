from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import get_current_user
from db import pool

router = APIRouter()


class DeleteExceptionDateRequest(BaseModel):
    id: str


@router.delete("/orgs/exception-dates")
async def delete_exception_date(
    body: DeleteExceptionDateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an exception date entry from the exception_dates table.
    Requires authentication via Bearer token in Authorization header.
    
    Request body:
    - id (str): The UUID of the exception date entry to delete
    
    The route verifies that the exception date belongs to the user's organization
    before deleting it.
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
                
                # Delete the exception date entry
                cur.execute(
                    """
                    DELETE FROM exception_dates
                    WHERE id = %s
                    """,
                    (body.id,)
                )
                
                conn.commit()
                
                return {
                    "message": "Exception date deleted successfully",
                    "id": body.id
                }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting exception date: {str(e)}"
        )
