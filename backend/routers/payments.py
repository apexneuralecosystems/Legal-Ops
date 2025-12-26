"""
Payment router - PayPal integration using Apex SaaS Framework.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dependencies import get_current_user
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
import logging

# Import from local apex module
from apex.payments import PayPalClient, init_payments, get_paypal_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])

# Initialize PayPal client on module load
_client: Optional[PayPalClient] = None


def get_client() -> PayPalClient:
    """Get or initialize PayPal client."""
    global _client
    if _client is None:
        _client = PayPalClient(
            client_id=getattr(settings, 'PAYPAL_CLIENT_ID', ''),
            client_secret=getattr(settings, 'PAYPAL_CLIENT_SECRET', ''),
            mode=getattr(settings, 'PAYPAL_MODE', 'sandbox')
        )
        logger.info(f"PayPal client initialized (mode={_client.mode})")
    return _client


# Pydantic schemas
class CreateOrderRequest(BaseModel):
    amount: float
    currency: str = "USD"
    description: Optional[str] = None


class CaptureOrderRequest(BaseModel):
    order_id: str


class CreateSubscriptionRequest(BaseModel):
    plan_id: str
    subscriber_email: str
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CancelSubscriptionRequest(BaseModel):
    subscription_id: str
    reason: Optional[str] = None


# Endpoints
@router.post("/orders/create", response_model=dict)
async def create_order(
    request: CreateOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a PayPal order for payment.
    
    Returns order ID and approval URL.
    """
    try:
        client = get_client()
        result = await client.create_order(
            amount=request.amount,
            currency=request.currency,
            description=request.description
        )
        
        return {
            "status": "success",
            "order_id": result.get("order_id"),
            "approval_url": result.get("approval_url"),
            "order_status": result.get("status")
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"PayPal order creation failed: {e}")
        raise HTTPException(status_code=500, detail="Payment service unavailable")


@router.post("/orders/capture", response_model=dict)
async def capture_order(
    request: CaptureOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Capture a PayPal order after customer approval.
    """
    try:
        client = get_client()
        result = await client.capture_order(request.order_id)
        
        return {
            "status": "success",
            "order_id": result.get("order_id"),
            "order_status": result.get("status"),
            "payer": result.get("payer", {})
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"PayPal capture failed: {e}")
        raise HTTPException(status_code=500, detail="Payment capture failed")


@router.get("/orders/{order_id}", response_model=dict)
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get PayPal order details.
    """
    try:
        client = get_client()
        order = await client.get_order(order_id)
        
        return {
            "status": "success",
            "order": order
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Get order failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve order")


@router.post("/subscriptions/create", response_model=dict)
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a PayPal subscription.
    
    Note: Requires pre-configured subscription plans in PayPal.
    """
    try:
        client = get_client()
        result = await client.create_subscription(
            plan_id=request.plan_id,
            subscriber_email=request.subscriber_email,
            return_url=request.return_url,
            cancel_url=request.cancel_url
        )
        
        return {
            "status": "success",
            "subscription_id": result.get("subscription_id"),
            "approval_url": result.get("approval_url"),
            "subscription_status": result.get("status")
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Create subscription failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")


@router.get("/subscriptions/{subscription_id}", response_model=dict)
async def get_subscription(
    subscription_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get subscription details from PayPal.
    """
    try:
        client = get_client()
        # Get subscription from PayPal
        token = await client._get_access_token()
        
        import httpx
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{client.base_url}/v1/billing/subscriptions/{subscription_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Subscription not found: {subscription_id}")
            
            data = response.json()
            return {
                "status": "success",
                "subscription_id": data.get("id"),
                "subscription_status": data.get("status"),
                "plan_id": data.get("plan_id"),
                "start_time": data.get("start_time"),
                "billing_info": data.get("billing_info", {})
            }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Get subscription failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription")


@router.post("/subscriptions/cancel", response_model=dict)
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a subscription.
    """
    try:
        client = get_client()
        result = await client.cancel_subscription(
            subscription_id=request.subscription_id,
            reason=request.reason
        )
        
        return {
            "status": "success",
            "message": "Subscription cancelled",
            "subscription_id": request.subscription_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Cancel subscription failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")
