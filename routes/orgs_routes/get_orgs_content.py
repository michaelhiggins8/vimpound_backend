from fastapi import APIRouter, HTTPException, Depends
from auth import get_current_user
from db import pool

router = APIRouter()


@router.get("/orgs/content")
async def get_orgs_content(
    current_user: dict = Depends(get_current_user)
):
    """
    Get the organization content from the orgs table for the user's organization.
    Returns default_hours_of_operation, agent_name, company_name, documents_needed,
    cost_to_release_short, cost_to_release_long, default_address, and time_zone columns from the orgs table
    where orgs.id matches profiles.org_id and profiles.id matches the authenticated user's ID.
    Requires authentication via Bearer token in Authorization header.
    """
    
    user_id = current_user['id']
    
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Query to get org content for the user's organization
                cur.execute(
                    """
                    SELECT 
                        o.default_hours_of_operation,
                        o.agent_name,
                        o.company_name,
                        o.documents_needed,
                        o.cost_to_release_short,
                        o.cost_to_release_long,
                        o.default_address,
                        o.time_zone
                    FROM orgs o
                    INNER JOIN profiles p ON o.id = p.org_id
                    WHERE p.id = %s
                    """,
                    (user_id,)
                )
                
                row = cur.fetchone()
                
                # Check if organization was found
                if not row:
                    raise HTTPException(
                        status_code=404,
                        detail="No organization found for this user"
                    )
                
                return {
                    "default_hours_of_operation": row[0],
                    "agent_name": row[1],
                    "company_name": row[2],
                    "documents_needed": row[3],
                    "cost_to_release_short": row[4],
                    "cost_to_release_long": row[5],
                    "default_address": row[6],
                    "time_zone": row[7]
                }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching organization content: {str(e)}"
        )
