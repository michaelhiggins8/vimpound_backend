from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import get_current_user
from db import pool

router = APIRouter()


class DeleteAddressRequest(BaseModel):
    id: str


@router.delete("/addresses")
async def delete_address(
    body: DeleteAddressRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an address entry from the addresses table.
    Requires authentication via Bearer token in Authorization header.
    
    Request body:
    - id (str): The UUID of the address entry to delete
    
    The route verifies that the address belongs to the user's organization
    before deleting it. The deletion will only succeed if:
    - addresses.id matches the id from the request body
    - addresses.org_id matches profiles.org_id where profiles.id matches the authenticated user's ID
    """
    
    user_id = current_user['id']
    
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Delete the address entry, ensuring it belongs to the user's organization
                cur.execute(
                    """
                    DELETE FROM addresses
                    WHERE addresses.id = %s
                    AND addresses.org_id = (
                        SELECT profiles.org_id
                        FROM profiles
                        WHERE profiles.id = %s
                    )
                    """,
                    (body.id, user_id)
                )
                
                # Check if any rows were affected
                rows_deleted = cur.rowcount
                
                if rows_deleted == 0:
                    raise HTTPException(
                        status_code=404,
                        detail="Address not found or does not belong to your organization"
                    )
                
                conn.commit()
                
                return {
                    "message": "Address deleted successfully",
                    "id": body.id
                }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting address: {str(e)}"
        )

