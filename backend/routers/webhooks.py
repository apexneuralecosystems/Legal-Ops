"""
PayPal Webhook Router - Handle payment events from PayPal.

Webhooks allow PayPal to notify your server when:
- Payment is completed
- Subscription is activated/canceled
- Refunds are processed
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from utils.usage_tracker import UsageTracker
from apex.email import get_email_client
import logging
import hmac
import hashlib
import httpx

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


async def verify_paypal_webhook(
    request: Request,
    transmission_id: str,
    timestamp: str,
    webhook_id: str,
    cert_url: str,
    auth_algo: str,
    transmission_sig: str,
    webhook_body: bytes
) -> bool:
    """
    Verify PayPal webhook signature.
    
    In production, implement full verification using PayPal's API.
    For now, we do basic validation.
    """
    # Basic validation - check required headers exist
    if not all([transmission_id, timestamp, transmission_sig]):
        return False
    
    # In production, verify with PayPal API:
    # POST https://api-m.paypal.com/v1/notifications/verify-webhook-signature
    # For now, accept if headers are present
    return True


@router.post("/paypal")
async def paypal_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle PayPal webhook events.
    
    Events handled:
    - PAYMENT.CAPTURE.COMPLETED: Payment successful
    - BILLING.SUBSCRIPTION.ACTIVATED: Subscription started
    - BILLING.SUBSCRIPTION.CANCELLED: Subscription canceled
    - BILLING.SUBSCRIPTION.EXPIRED: Subscription expired
    """
    try:
        # Get webhook headers
        transmission_id = request.headers.get("paypal-transmission-id")
        timestamp = request.headers.get("paypal-transmission-time")
        webhook_id = request.headers.get("paypal-webhook-id")
        cert_url = request.headers.get("paypal-cert-url")
        auth_algo = request.headers.get("paypal-auth-algo")
        transmission_sig = request.headers.get("paypal-transmission-sig")
        
        # Get body
        body = await request.body()
        
        # Verify webhook (in production, use full verification)
        if not await verify_paypal_webhook(
            request, transmission_id, timestamp, webhook_id,
            cert_url, auth_algo, transmission_sig, body
        ):
            logger.warning("PayPal webhook verification failed")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse event
        event = await request.json()
        event_type = event.get("event_type")
        resource = event.get("resource", {})
        
        logger.info(f"PayPal webhook received: {event_type}")
        
        # Handle different event types
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            # One-time payment completed
            order_id = resource.get("id")
            amount = resource.get("amount", {}).get("value")
            payer_email = resource.get("payer", {}).get("email_address")
            
            logger.info(f"Payment completed: {order_id} for {amount}")
            
            # Note: For one-time payments, subscription is activated via /subscription/activate endpoint
            # This webhook confirms the payment was successful
            
            return {"status": "received", "event": event_type}
        
        elif event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
            # Subscription activated
            subscription_id = resource.get("id")
            subscriber_email = resource.get("subscriber", {}).get("email_address")
            
            logger.info(f"Subscription activated: {subscription_id} for {subscriber_email}")
            
            # Find user by email and activate subscription
            from apex.models import User
            from sqlalchemy import select
            
            async with db.begin():
                result = await db.execute(
                    select(User).where(User.email == subscriber_email)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    await UsageTracker.activate_subscription(
                        user_id=user.id,
                        subscription_id=subscription_id,
                        db=db
                    )
                    
                    # Send confirmation email
                    email_client = get_email_client()
                    if email_client:
                        await email_client.send_subscription_confirmation(
                            to_email=subscriber_email,
                            subscription_id=subscription_id
                        )
                    
                    logger.info(f"Subscription activated for user {user.id}")
                else:
                    logger.warning(f"User not found for subscription: {subscriber_email}")
            
            return {"status": "activated", "subscription_id": subscription_id}
        
        elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
            # Subscription canceled
            subscription_id = resource.get("id")
            subscriber_email = resource.get("subscriber", {}).get("email_address")
            
            logger.info(f"Subscription cancelled: {subscription_id}")
            
            # Find user and cancel subscription
            from apex.models import User
            from sqlalchemy import select
            
            async with db.begin():
                result = await db.execute(
                    select(User).where(User.email == subscriber_email)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    await UsageTracker.cancel_subscription(
                        user_id=user.id,
                        db=db
                    )
                    logger.info(f"Subscription cancelled for user {user.id}")
            
            return {"status": "cancelled", "subscription_id": subscription_id}
        
        elif event_type == "BILLING.SUBSCRIPTION.EXPIRED":
            # Subscription expired
            subscription_id = resource.get("id")
            logger.info(f"Subscription expired: {subscription_id}")
            
            # Handle expiration (similar to cancellation)
            return {"status": "expired", "subscription_id": subscription_id}
        
        else:
            # Unknown event type - log and acknowledge
            logger.info(f"Unhandled PayPal event: {event_type}")
            return {"status": "received", "event": event_type}
            
    except Exception as e:
        logger.error(f"PayPal webhook error: {e}")
        # Always return 200 to prevent PayPal from retrying
        return {"status": "error", "message": str(e)}
