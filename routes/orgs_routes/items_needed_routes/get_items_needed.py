from fastapi import APIRouter, HTTPException, Depends
from auth import get_current_user
from db import pool

router = APIRouter()


@router.get("/orgs/documents-needed")
async def get_documents_needed(
    current_user: dict = Depends(get_current_user)
):
    """
    Get the documents_needed (TEXT) column from the orgs table for the user's organization.
    Returns the documents_needed value where orgs.id matches profiles.org_id 
    and profiles.id matches the authenticated user's ID.
    Requires authentication via Bearer token in Authorization header.
    """
    
    user_id = current_user['id']
    
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Query to get documents_needed for the user's organization
                cur.execute(
                    """
                    SELECT 
                        o.documents_needed
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
                
                documents_needed = row[0]
                
                return {
                    "documents_needed": documents_needed
                }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching documents needed: {str(e)}"
        )

