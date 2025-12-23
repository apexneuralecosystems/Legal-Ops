"""
Payment router - PayPal integration for orders and subscriptions.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dependencies import get_current_user
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
import httpx
import base64
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])


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


class CancelSubscriptionRequest(BaseModel):
    subscription_id: str
    reason: Optional[str] = None


# PayPal API helpers
class PayPalClient:
    """PayPal API client wrapper."""
    
    def __init__(self):
        self.client_id = getattr(settings, 'PAYPAL_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'PAYPAL_CLIENT_SECRET', '')
        self.mode = getattr(settings, 'PAYPAL_MODE', 'sandbox')
        
        if self.mode == 'sandbox':
            self.base_url = "https://api-m.sandbox.paypal.com"
        else:
            self.base_url = "https://api-m.paypal.com"
        
        self._access_token = None
    
    async def get_access_token(self) -> str:
        """Get OAuth access token from PayPal."""
        if not self.client_id or not self.client_secret:
            raise ValueError("PayPal credentials not configured")
        
        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/oauth2/token",
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"grant_type": "client_credentials"}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get PayPal token: {response.text}")
            
            data = response.json()
            self._access_token = data["access_token"]
            return self._access_token
    
    async def create_order(self, amount: float, currency: str, description: str = None) -> Dict:
        """Create a PayPal order."""
        token = await self.get_access_token()
        
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency,
                    "value": str(amount)
                }
            }]
        }
        
        if description:
            order_data["purchase_units"][0]["description"] = description
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v2/checkout/orders",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=order_data
            )
            
            if response.status_code not in [200, 201]:
                raise ValueError(f"Failed to create order: {response.text}")
            
            return response.json()
    
    async def capture_order(self, order_id: str) -> Dict:
        """Capture a PayPal order."""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code not in [200, 201]:
                raise ValueError(f"Failed to capture order: {response.text}")
            
            return response.json()
    
    async def get_order(self, order_id: str) -> Dict:
        """Get order details."""
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2/checkout/orders/{order_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get order: {response.text}")
            
            return response.json()


# Singleton client
_paypal_client: Optional[PayPalClient] = None


def get_paypal_client() -> PayPalClient:
    """Get PayPal client singleton."""
    global _paypal_client
    if _paypal_client is None:
        _paypal_client = PayPalClient()
    return _paypal_client


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
        client = get_paypal_client()
        order = await client.create_order(
            amount=request.amount,
            currency=request.currency,
            description=request.description
        )
        
        # Extract approval URL
        approval_url = None
        for link in order.get("links", []):
            if link.get("rel") == "approve":
                approval_url = link.get("href")
                break
        
        return {
            "status": "success",
            "order_id": order.get("id"),
            "approval_url": approval_url,
            "order_status": order.get("status")
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
        client = get_paypal_client()
        result = await client.capture_order(request.order_id)
        
        return {
            "status": "success",
            "order_id": result.get("id"),
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
        client = get_paypal_client()
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
    # Placeholder - full subscription implementation requires PayPal plan setup
    return {
        "status": "info",
        "message": "Subscription creation requires PayPal plan configuration",
        "plan_id": request.plan_id,
        "subscriber_email": request.subscriber_email
    }


@router.get("/subscriptions/{subscription_id}", response_model=dict)
async def get_subscription(
    subscription_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get subscription details.
    """
    return {
        "status": "info",
        "message": "Subscription lookup requires PayPal integration",
        "subscription_id": subscription_id
    }


@router.post("/subscriptions/cancel", response_model=dict)
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a subscription.
    """
    return {
        "status": "info",
        "message": "Subscription cancellation requires PayPal integration",
        "subscription_id": request.subscription_id
    }
