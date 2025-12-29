from fastapi import APIRouter, HTTPException, Depends
from auth import get_current_user
from db import pool

router = APIRouter()


@router.get("/addresses")
async def get_addresses(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all addresses that belong to the user's organization.
    Returns the id (int8) and address (TEXT) columns from every row in the addresses table
    whose org_id matches the user's organization.
    Requires authentication via Bearer token in Authorization header.
    
    The query joins:
    - addresses.org_id matches profiles.org_id
    - profiles.id matches the authenticated user's ID
    """
    
    user_id = current_user['id']
    
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Query to get all addresses for the user's organization
                cur.execute(
                    """
                    SELECT 
                        a.id,
                        a.address
                    FROM addresses a
                    INNER JOIN profiles p ON a.org_id = p.org_id
                    WHERE p.id = %s
                    """,
                    (user_id,)
                )
                
                rows = cur.fetchall()
                
                # Extract id and address from rows (each row is a tuple with id and address)
                addresses = [
                    {"id": row[0], "address": row[1]} 
                    for row in rows
                ]
                
                return {
                    "addresses": addresses
                }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching addresses: {str(e)}"
        )

