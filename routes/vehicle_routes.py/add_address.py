from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import get_current_user
from db import pool

router = APIRouter()


class AddAddressRequest(BaseModel):
    address: str


@router.post("/addresses")
async def add_address(
    body: AddAddressRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new address entry in the addresses table.
    Requires authentication via Bearer token in Authorization header.
    
    Request body:
    - address (str): The address string to add
    
    The org_id will be automatically retrieved from the user's profile.
    The new row will have:
    - addresses.address = the input address string
    - addresses.org_id = profiles.org_id where profiles.id matches the authenticated user's ID
    """
    
    user_id = current_user['id']
    
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Insert address with org_id retrieved from profiles in a single query using subquery
                cur.execute(
                    """
                    INSERT INTO addresses (
                        address,
                        org_id
                    )
                    SELECT 
                        %s,
                        p.org_id
                    FROM profiles p
                    WHERE p.id = %s
                    RETURNING 
                        id,
                        address,
                        org_id,
                        created_at
                    """,
                    (
                        body.address,
                        user_id
                    )
                )
                
                # Fetch the inserted row to return
                inserted_row = cur.fetchone()
                
                if not inserted_row:
                    raise HTTPException(
                        status_code=404,
                        detail="No organization found for this user or insertion failed"
                    )
                
                # Get column names from cursor description
                column_names = [desc[0] for desc in cur.description]
                
                # Create dictionary mapping column names to values
                address_data = dict(zip(column_names, inserted_row))
                
                conn.commit()
                
                return {
                    "message": "Address created successfully",
                    "address": address_data
                }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating address: {str(e)}"
        )

