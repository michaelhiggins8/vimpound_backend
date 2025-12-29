from fastapi import APIRouter, HTTPException, Depends
from auth import get_current_user
from db import pool

router = APIRouter()


@router.get("/orgs/exception-dates")
async def get_exception_dates(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all exception dates for the user's organization.
    Returns id (INTEGER), date (TEXT) and hours (TEXT) columns from exception_dates table
    where exception_dates.org_id matches the profiles.org_id of the authenticated user.
    Requires authentication via Bearer token in Authorization header.
    """
    
    user_id = current_user['id']
    
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Query to get exception dates for the user's organization
                cur.execute(
                    """
                    SELECT 
                        ed.id,
                        ed.date,
                        ed.hours
                    FROM exception_dates ed
                    INNER JOIN profiles p ON ed.org_id = p.org_id
                    WHERE p.id = %s
                    ORDER BY ed.date
                    """,
                    (user_id,)
                )
                
                rows = cur.fetchall()
                
                # Convert rows to list of dictionaries for easy frontend consumption
                exception_dates = []
                for row in rows:
                    exception_dates.append({
                        "id": row[0],
                        "date": row[1],
                        "hours": row[2]
                    })
                
                return {
                    "exception_dates": exception_dates,
                    "count": len(exception_dates)
                }
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching exception dates: {str(e)}"
        )
