from fastapi import APIRouter, HTTPException, Depends, Query
from auth import get_current_user
from db import pool

router = APIRouter()


@router.get("/vehicles")
async def get_vehicles_paginated(
    page: int = Query(default=0, ge=0, description="Page number (0-indexed)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get paginated vehicles for the user's organization.
    Returns 10 vehicles per page, ordered by most recent to oldest (created_at DESC).
    Returns all columns from vehicles table except org_id.
    Requires authentication via Bearer token in Authorization header.
    
    The query joins:
    - vehicles.org_id matches orgs.id
    - orgs.id matches profiles.org_id
    - profiles.id matches the authenticated user's ID
    """
    
    user_id = current_user['id']
    page_size = 10
    offset = page * page_size
    
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Query to get paginated vehicles for the user's organization
                cur.execute(
                    """
                    SELECT 
                        v.id,
                        v.created_at,
                        v.status,
                        v.make,
                        v.model,
                        v.year,
                        v.color,
                        v.vin_number,
                        v.plate_number,
                        v.owner_first_name,
                        v.owner_last_name,
                        v.location
                    FROM vehicles v
                    INNER JOIN orgs o ON v.org_id = o.id
                    INNER JOIN profiles p ON o.id = p.org_id
                    WHERE p.id = %s
                    ORDER BY v.created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, page_size, offset)
                )
                
                rows = cur.fetchall()
                
                # Get column names from cursor description
                column_names = [desc[0] for desc in cur.description]
                
                # Convert rows to list of dictionaries
                vehicles = []
                for row in rows:
                    vehicle = dict(zip(column_names, row))
                    vehicles.append(vehicle)
                
                return {
                    "vehicles": vehicles,
                    "page": page,
                    "page_size": page_size,
                    "count": len(vehicles)
                }
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching vehicles: {str(e)}"
        )

