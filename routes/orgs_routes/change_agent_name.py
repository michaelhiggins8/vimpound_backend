from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import get_current_user
from db import pool

router = APIRouter()


class ChangeAgentNameRequest(BaseModel):
    agent_name: str


@router.patch("/orgs/agent-name")
async def change_agent_name(
    body: ChangeAgentNameRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update the agent_name column in the orgs table for the user's organization.
    Requires authentication via Bearer token in Authorization header.
    """
    
    user_id = current_user['id']
    
    # Update the agent_name in orgs table
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE orgs
                SET agent_name = %s
                FROM profiles
                WHERE orgs.id = profiles.org_id AND profiles.id = %s
                """,
                (body.agent_name, user_id)
            )
            
            # Check if any rows were updated
            if cur.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No organization found for this user"
                )
            
            conn.commit()
    
    return {"message": "Agent name updated successfully", "agent_name": body.agent_name}











