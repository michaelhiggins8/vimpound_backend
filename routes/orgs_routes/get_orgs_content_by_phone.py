from fastapi import APIRouter, HTTPException
from db import pool

router = APIRouter()


@router.get("/orgs/content/by-phone")
async def get_orgs_content_by_phone(phone_number: str):
    """
    Get organization content by phone number (public endpoint for landing pages).
    Returns the same fields as the authenticated endpoint but uses phone_number to identify the org.
    No authentication required.
    
    Query parameters:
    - phone_number (str): The phone number to look up (e.g., "4155551234")
    
    Returns:
    - default_hours_of_operation
    - agent_name
    - company_name
    - documents_needed
    - cost_to_release_short
    - cost_to_release_long
    - default_address
    - time_zone
    - id (org_id)
    """
    
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Query to get org content by phone number (same as webhook)
                cur.execute(
                    """
                    SELECT 
                        id,
                        default_hours_of_operation,
                        agent_name,
                        company_name,
                        documents_needed,
                        cost_to_release_short,
                        cost_to_release_long,
                        default_address,
                        time_zone
                    FROM orgs
                    WHERE phone_number = %s
                    LIMIT 1
                    """,
                    (phone_number,)
                )
                
                row = cur.fetchone()
                
                # Check if organization was found
                if not row:
                    raise HTTPException(
                        status_code=404,
                        detail="No organization found for this phone number"
                    )
                
                return {
                    "id": str(row[0]),
                    "default_hours_of_operation": row[1],
                    "agent_name": row[2],
                    "company_name": row[3],
                    "documents_needed": row[4],
                    "cost_to_release_short": row[5],
                    "cost_to_release_long": row[6],
                    "default_address": row[7],
                    "time_zone": row[8]
                }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching organization content: {str(e)}"
        )

