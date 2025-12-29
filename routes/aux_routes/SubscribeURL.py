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

# Optional: Default product ID from environment (can be overridden in request)
DEFAULT_PRODUCT_ID = os.getenv("AUTUMN_PRODUCT_ID")

FRONTEND_URL = os.getenv("FRONTEND_URL")
FRONTEND_URL = FRONTEND_URL + "/dashboard/phone_number"

# Initialize Autumn client
autumn_client = autumn.Autumn(token=AUTUMN_SECRET_KEY)

router = APIRouter()


class SubscribeURLRequest(BaseModel):
    """Request model for getting a subscription checkout URL."""
    product_id: str | None = None  # Optional product_id, will use env default if not provided
    success_url: str | None = None  # Optional success redirect URL


@router.post("/subscribe-url")
async def get_subscribe_url(
    body: SubscribeURLRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a Stripe checkout URL for the authenticated user to subscribe to a product.
    Requires authentication via Bearer token in Authorization header.
    
    The user's ID from the authentication token will be used as the customer_id for Autumn.
    If the customer doesn't exist in Autumn, it will be automatically created.
    
    Request body (optional):
    - product_id (str): Product ID to subscribe to. If not provided, uses AUTUMN_PRODUCT_ID from .env
    - success_url (str): URL to redirect to after successful purchase
    
    Returns:
    - url (str): Stripe checkout URL to redirect the user to
    - customer_id (str): The customer ID used
    - product (object): Product information
    """
    
    user_id = current_user['id']
    
    # Determine product_id to use
    product_id = body.product_id or DEFAULT_PRODUCT_ID
    
    if not product_id:
        raise HTTPException(
            status_code=400,
            detail="product_id is required. Either provide it in the request body or set AUTUMN_PRODUCT_ID in .env"
        )
    
    try:
        # Prepare checkout parameters
        checkout_params = {
            "customer_id": user_id,
            "product_id": product_id,
            "success_url":FRONTEND_URL
        }
        
        # Add optional success_url if provided
        if body.success_url:
            checkout_params["success_url"] = body.success_url
        
        # Call Autumn checkout API
        response = await autumn_client.checkout(**checkout_params)
        print(FRONTEND_URL)
        # Return the checkout URL and relevant information
        # CheckoutResponse is an object, not a dict, so access attributes directly
        return {
            "url": getattr(response, 'url', None),
            "customer_id": getattr(response, 'customer_id', None),
            "product": getattr(response, 'product', None)
        }
        
    except Exception as e:
        # Handle any errors from the Autumn API
        error_type = type(e).__name__
        error_message = str(e) if str(e) else repr(e)
        
        # Check for retry errors which indicate network/API connectivity issues
        if "RetryRequestError" in error_type or "_RetryRequestError" in str(type(e)):
            error_detail = "Failed to connect to Autumn API. This may be due to network issues, invalid API credentials, or the Autumn service being unavailable. Please check your AUTUMN_SECRET_KEY and network connection."
        else:
            error_detail = f"Error generating checkout URL ({error_type}): {error_message}"
        
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )
