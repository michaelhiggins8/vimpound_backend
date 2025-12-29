from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import get_current_user
from db import pool

router = APIRouter()


class DeleteVehicleRequest(BaseModel):
    id: str


@router.delete("/vehicles")
async def delete_vehicle(
    body: DeleteVehicleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a vehicle entry from the vehicles table.
    Requires authentication via Bearer token in Authorization header.
    
    Request body:
    - id (str): The UUID of the vehicle entry to delete
    
    The route verifies that the vehicle belongs to the user's organization
    before deleting it.
    """
    
    user_id = current_user['id']
    
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # First, verify the vehicle exists and belongs to the user's organization
                cur.execute(
                    """
                    SELECT v.id
                    FROM vehicles v
                    INNER JOIN orgs o ON v.org_id = o.id
                    INNER JOIN profiles p ON o.id = p.org_id
                    WHERE v.id = %s AND p.id = %s
                    LIMIT 1
                    """,
                    (body.id, user_id)
                )
                
                row = cur.fetchone()
                
                if not row:
                    raise HTTPException(
                        status_code=404,
                        detail="Vehicle not found or does not belong to your organization"
                    )
                
                # Delete the vehicle entry
                cur.execute(
                    """
                    DELETE FROM vehicles
                    WHERE id = %s
                    """,
                    (body.id,)
                )
                
                conn.commit()
                
                return {
                    "message": "Vehicle deleted successfully",
                    "id": body.id
                }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting vehicle: {str(e)}"
        )







