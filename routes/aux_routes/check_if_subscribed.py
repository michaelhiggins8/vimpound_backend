import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
import autumn
from auth import get_current_user

load_dotenv()

# Get Autumn secret key from environment variables
AUTUMN_SECRET_KEY = os.getenv("AUTUMN_SECRET_KEY")
if not AUTUMN_SECRET_KEY:
    raise RuntimeError("AUTUMN_SECRET_KEY is not set in .env")

# Get feature ID from environment variables
AUTUMN_FEATURE_ID = os.getenv("AUTUMN_FEATURE_ID")
if not AUTUMN_FEATURE_ID:
    raise RuntimeError("AUTUMN_FEATURE_ID is not set in .env")

# Initialize Autumn client
autumn_client = autumn.Autumn(token=AUTUMN_SECRET_KEY)

router = APIRouter()


@router.get("/check-subscription")
async def check_if_subscribed(
    current_user: dict = Depends(get_current_user)
):
    """
    Check if the authenticated user is subscribed to the preset feature.
    Requires authentication via Bearer token in Authorization header.
    
    The user's ID from the authentication token will be used as the customer_id for Autumn.
    If the customer doesn't exist in Autumn, it will be automatically created.
    
    Returns:
    - allowed (bool): Whether the customer has access to the feature
    - code (str): Code describing the result of the check
    - customer_id (str): ID of the customer
    - feature_id (str): ID of the feature
    - balance (number | null): The remaining available balance
    - usage (number | null): The total cumulative usage consumed
    - included_usage (number | null): The total amount of usage included
    - next_reset_at (number | null): Unix timestamp when usage counter will reset
    - overage_allowed (bool | null): Whether customer can continue using beyond included usage
    """
    
    user_id = current_user['id']
    
    try:
        # Call Autumn check API to verify subscription status
        # According to Autumn docs: POST /check with customer_id and feature_id
        response = await autumn_client.check(
            customer_id=user_id,
            feature_id=AUTUMN_FEATURE_ID
        )
        
        # Extract relevant information from the response
        # Response is an object, so access attributes directly
        return {
            "allowed": getattr(response, 'allowed', False),
            "code": getattr(response, 'code', None),
            "customer_id": getattr(response, 'customer_id', None),
            "feature_id": getattr(response, 'feature_id', None),
            "balance": getattr(response, 'balance', None),
            "usage": getattr(response, 'usage', None),
            "included_usage": getattr(response, 'included_usage', None),
            "next_reset_at": getattr(response, 'next_reset_at', None),
            "overage_allowed": getattr(response, 'overage_allowed', None),
            "interval": getattr(response, 'interval', None),
            "interval_count": getattr(response, 'interval_count', None),
            "unlimited": getattr(response, 'unlimited', None),
            "required_balance": getattr(response, 'required_balance', None),
        }
        
    except Exception as e:
        # Handle any errors from the Autumn API
        error_type = type(e).__name__
        error_message = str(e) if str(e) else repr(e)
        
        # Check for retry errors which indicate network/API connectivity issues
        if "RetryRequestError" in error_type or "_RetryRequestError" in str(type(e)):
            error_detail = "Failed to connect to Autumn API. This may be due to network issues, invalid API credentials, or the Autumn service being unavailable. Please check your AUTUMN_SECRET_KEY and network connection."
        else:
            error_detail = f"Error checking subscription status ({error_type}): {error_message}"
        
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )
