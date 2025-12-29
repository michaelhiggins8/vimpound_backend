import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import autumn
from auth import get_current_user

load_dotenv()

# Get Autumn secret key from environment variables
AUTUMN_SECRET_KEY = os.getenv("AUTUMN_SECRET_KEY")
if not AUTUMN_SECRET_KEY:
    raise RuntimeError("AUTUMN_SECRET_KEY is not set in .env")

# Get frontend URL for return redirect
FRONTEND_URL = os.getenv("FRONTEND_URL")
DEFAULT_RETURN_URL = f"{FRONTEND_URL}/dashboard/billing" if FRONTEND_URL else None

# Initialize Autumn client
autumn_client = autumn.Autumn(token=AUTUMN_SECRET_KEY)

router = APIRouter()


class BillingPortalRequest(BaseModel):
    """Request model for getting a billing portal URL."""
    return_url: str | None = None  # Optional return URL after leaving billing portal


@router.post("/orgs/customer-portal")
async def get_customer_portal(
    body: BillingPortalRequest | None = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a billing portal URL for the authenticated user to manage their subscription and billing.
    Requires authentication via Bearer token in Authorization header.
    
    The user's ID from the authentication token will be used as the customer_id for Autumn.
    If the customer doesn't exist in Autumn, it will be automatically created.
    
    Request body (optional):
    - return_url (str): URL to redirect to after leaving the billing portal. 
                        If not provided, defaults to FRONTEND_URL/dashboard/billing
    
    Returns:
    - url (str): Billing portal URL to redirect the user to
    - customer_id (str): The customer ID used
    """
    
    user_id = current_user['id']
    
    # Determine return_url to use
    return_url = None
    if body and body.return_url:
        return_url = body.return_url
    elif DEFAULT_RETURN_URL:
        return_url = DEFAULT_RETURN_URL
    
    # Ensure return_url has https:// scheme if provided
    if return_url and not return_url.startswith(('http://', 'https://')):
        return_url = f"https://{return_url}"
    
    try:
        # Prepare billing portal parameters
        portal_params = {
            "customer_id": user_id
        }
        
        # Add optional return_url if provided (must have https:// scheme)
        if return_url:
            portal_params["return_url"] = return_url
        
        # Call Autumn billing portal API using SDK
        # Based on Autumn docs: autumn_client.customers.get_billing_portal()
        response = await autumn_client.customers.get_billing_portal(**portal_params)
        
        # Return the billing portal URL and relevant information
        # Response is an object, so access attributes directly
        return {
            "url": getattr(response, 'url', None),
            "customer_id": getattr(response, 'customer_id', user_id)
        }
        
    except Exception as e:
        # Handle any errors from the Autumn API
        error_type = type(e).__name__
        error_message = str(e) if str(e) else repr(e)
        
        # Check for retry errors which indicate network/API connectivity issues
        if "RetryRequestError" in error_type or "_RetryRequestError" in str(type(e)):
            error_detail = "Failed to connect to Autumn API. This may be due to network issues, invalid API credentials, or the Autumn service being unavailable. Please check your AUTUMN_SECRET_KEY and network connection."
        else:
            error_detail = f"Error generating billing portal URL ({error_type}): {error_message}"
        
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )

