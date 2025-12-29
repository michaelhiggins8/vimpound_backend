from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from auth import get_current_user
from db import pool

router = APIRouter()

# Days of the week in the expected order
EXPECTED_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class ChangeDefaultHoursRequest(BaseModel):
    default_hours_of_operation: str
    
    @field_validator('default_hours_of_operation')
    @classmethod
    def validate_hours_format(cls, v: str) -> str:
        """
        Validate that the input matches the exact format:
        * Monday: 4:00 AM - 7PM
        * Tuesday: 4:00 AM - 7PM
        ...
        """
        if not v:
            raise ValueError("default_hours_of_operation cannot be empty")
        
        lines = v.strip().split('\n')
        
        # Check that we have exactly 7 lines (one for each day)
        if len(lines) != 7:
            raise ValueError("Must have exactly 7 lines (one for each day of the week)")
        
        # Validate each line
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check line starts with "* "
            if not line.startswith("* "):
                raise ValueError(f"Line {i+1} must start with '* '")
            
            # Extract day and hours
            day_part = line[2:].split(":", 1)
            if len(day_part) != 2:
                raise ValueError(f"Line {i+1} must have format '* Day: hours'")
            
            day = day_part[0].strip()
            hours = day_part[1].strip()
            
            # Check day matches expected day
            if day != EXPECTED_DAYS[i]:
                raise ValueError(f"Line {i+1} must be for {EXPECTED_DAYS[i]}, got {day}")
            
            # Check hours is not empty
            if not hours:
                raise ValueError(f"Line {i+1} must have hours after the colon")
        
        return v


@router.patch("/orgs/default-hours")
async def change_default_hours(
    body: ChangeDefaultHoursRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update the default_hours_of_operation column in the orgs table for the user's organization.
    Requires authentication via Bearer token in Authorization header.
    Input must be in format:
    * Monday: 4:00 AM - 7PM
    * Tuesday: 4:00 AM - 7PM
    * Wednesday: 4:00 AM - 1:00 PM, 5:00 PM - 8:00 PM 
    * Thursday: 4:00 AM - 7PM
    * Friday: 4:00 AM - 7PM
    * Saturday: 4:00 AM - 7PM 
    * Sunday: 4:00 AM - 7PM 
    """
    
    user_id = current_user['id']
    
    # Update the default_hours_of_operation in orgs table
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE orgs
                SET default_hours_of_operation = %s
                FROM profiles
                WHERE orgs.id = profiles.org_id AND profiles.id = %s
                """,
                (body.default_hours_of_operation, user_id)
            )
            
            # Check if any rows were updated
            if cur.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No organization found for this user"
                )
            
            conn.commit()
    
    return {"message": "Default hours of operation updated successfully", "default_hours_of_operation": body.default_hours_of_operation}
