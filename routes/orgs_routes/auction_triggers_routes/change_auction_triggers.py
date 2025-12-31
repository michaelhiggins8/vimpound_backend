from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from auth import get_current_user
from db import pool

router = APIRouter()


class ChangeAuctionTriggersRequest(BaseModel):
    auction_triggers: str
    
    @field_validator('auction_triggers')
    @classmethod
    def validate_markdown_bullet_list(cls, v: str) -> str:
        """
        Validate that the auction_triggers string is a markdown-style bullet point list.
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
                    "auction_triggers must be a markdown-style bullet point list. "
                    "Each non-empty line must start with '* ' or '- '."
                )
            has_bullet = True
        
        if not has_bullet:
            raise ValueError(
                "auction_triggers must contain at least one bullet point starting with '* ' or '- '"
            )
        
        return v


@router.patch("/orgs/auction-triggers")
async def change_auction_triggers(
    body: ChangeAuctionTriggersRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update the auction_triggers (TEXT) column in the orgs table for the user's organization.
    The auction_triggers must be a markdown-style bullet point list (each line starting with '* ' or '- ').
    Requires authentication via Bearer token in Authorization header.
    """
    
    user_id = current_user['id']
    
    # Convert empty strings to None (NULL in database)
    auction_triggers_value = body.auction_triggers.strip() if body.auction_triggers and body.auction_triggers.strip() else None
    
    # Update the auction_triggers in orgs table
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE orgs
                SET auction_triggers = %s
                FROM profiles
                WHERE orgs.id = profiles.org_id AND profiles.id = %s
                """,
                (auction_triggers_value, user_id)
            )
            
            # Check if any rows were updated
            if cur.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No organization found for this user"
                )
            
            conn.commit()
    
    return {
        "message": "Auction triggers updated successfully",
        "auction_triggers": auction_triggers_value or ""
    }

