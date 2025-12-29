from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from auth import get_current_user
from db import pool

router = APIRouter()


class ChangeCostToReleaseLongRequest(BaseModel):
    cost_to_release_long: str
    
    @field_validator('cost_to_release_long')
    @classmethod
    def validate_markdown_bullet_list(cls, v: str) -> str:
        """
        Validate that the cost_to_release_long string is a markdown-style bullet point list.
        Each non-empty line should start with '* ' or '- '.
        Allows empty strings (which will be stored as NULL in the database).
        """
        # Allow empty strings - they will be converted to NULL in the database
        if not v or not v.strip():
            return v
        
        lines = v.split('\n')
        has_bullet = False
        
        for line in lines:
            stripped = line.strip()
            # Skip empty lines
            if not stripped:
                continue
            
            # Check if line starts with markdown bullet point (* or -)
            if not (stripped.startswith('* ') or stripped.startswith('- ')):
                raise ValueError(
                    "cost_to_release_long must be a markdown-style bullet point list. "
                    "Each non-empty line must start with '* ' or '- '."
                )
            has_bullet = True
        
        if not has_bullet:
            raise ValueError(
                "cost_to_release_long must contain at least one bullet point starting with '* ' or '- '"
            )
        
        return v


@router.patch("/orgs/cost-to-release-long")
async def change_cost_to_release_long(
    body: ChangeCostToReleaseLongRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update the cost_to_release_long (TEXT) column in the orgs table for the user's organization.
    The cost_to_release_long must be a markdown-style bullet point list (each line starting with '* ' or '- ').
    Requires authentication via Bearer token in Authorization header.
    """
    
    user_id = current_user['id']
    
    # Convert empty strings to None (NULL in database)
    cost_to_release_long_value = body.cost_to_release_long.strip() if body.cost_to_release_long and body.cost_to_release_long.strip() else None
    
    # Update the cost_to_release_long in orgs table
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE orgs
                SET cost_to_release_long = %s
                FROM profiles
                WHERE orgs.id = profiles.org_id AND profiles.id = %s
                """,
                (cost_to_release_long_value, user_id)
            )
            
            # Check if any rows were updated
            if cur.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No organization found for this user"
                )
            
            conn.commit()
    
    return {
        "message": "Cost to release long updated successfully",
        "cost_to_release_long": cost_to_release_long_value or ""
    }
