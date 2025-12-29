from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import get_current_user
from db import pool

router = APIRouter()


class AddVehicleRequest(BaseModel):
    status: str
    make: str
    model: str
    year: int
    color: str
    vin_number: str
    plate_number: str
    owner_first_name: str
    owner_last_name: str
    location: str


@router.post("/vehicles")
async def add_vehicle(
    body: AddVehicleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new vehicle entry in the vehicles table.
    Requires authentication via Bearer token in Authorization header.
    
    Request body:
    - status (str): Vehicle status
    - make (str): Vehicle make
    - model (str): Vehicle model
    - year (int): Vehicle year
    - color (str): Vehicle color
    - vin_number (str): Vehicle VIN number
    - plate_number (str): Vehicle plate number
    - owner_first_name (str): Owner's first name
    - owner_last_name (str): Owner's last name
    - location (str): Vehicle location
    
    The org_id will be automatically retrieved from the user's profile in a single efficient query.
    """
    
    user_id = current_user['id']
    
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Insert vehicle with org_id retrieved from profiles in a single query using subquery
                cur.execute(
                    """
                    INSERT INTO vehicles (
                        org_id,
                        status,
                        make,
                        model,
                        year,
                        color,
                        vin_number,
                        plate_number,
                        owner_first_name,
                        owner_last_name,
                        location
                    )
                    SELECT 
                        p.org_id,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    FROM profiles p
                    WHERE p.id = %s
                    RETURNING 
                        id,
                        created_at,
                        org_id,
                        status,
                        make,
                        model,
                        year,
                        color,
                        vin_number,
                        plate_number,
                        owner_first_name,
                        owner_last_name,
                        location
                    """,
                    (
                        body.status,
                        body.make,
                        body.model,
                        body.year,
                        body.color,
                        body.vin_number,
                        body.plate_number,
                        body.owner_first_name,
                        body.owner_last_name,
                        body.location,
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
                vehicle = dict(zip(column_names, inserted_row))
                
                conn.commit()
                
                return {
                    "message": "Vehicle created successfully",
                    "vehicle": vehicle
                }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating vehicle: {str(e)}"
        )
