from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from auth import get_current_user
from db import pool

router = APIRouter()


class ChangeDocumentsNeededRequest(BaseModel):
    documents_needed: str
    
    @field_validator('documents_needed')
    @classmethod
    def validate_markdown_bullet_list(cls, v: str) -> str:
        """
        Validate that the documents_needed string is a markdown-style bullet point list.
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
                    "documents_needed must be a markdown-style bullet point list. "
                    "Each non-empty line must start with '* ' or '- '."
                )
            has_bullet = True
        
        if not has_bullet:
            raise ValueError(
                "documents_needed must contain at least one bullet point starting with '* ' or '- '"
            )
        
        return v


@router.patch("/orgs/documents-needed")
async def change_documents_needed(
    body: ChangeDocumentsNeededRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update the documents_needed (TEXT) column in the orgs table for the user's organization.
    The documents_needed must be a markdown-style bullet point list (each line starting with '* ' or '- ').
    Requires authentication via Bearer token in Authorization header.
    """
    
    user_id = current_user['id']
    
    # Convert empty strings to None (NULL in database)
    documents_needed_value = body.documents_needed.strip() if body.documents_needed and body.documents_needed.strip() else None
    
    # Update the documents_needed in orgs table
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE orgs
                SET documents_needed = %s
                FROM profiles
                WHERE orgs.id = profiles.org_id AND profiles.id = %s
                """,
                (documents_needed_value, user_id)
            )
            
            # Check if any rows were updated
            if cur.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No organization found for this user"
                )
            
            conn.commit()
    
    return {
        "message": "Documents needed updated successfully",
        "documents_needed": documents_needed_value or ""
    }
