"""
Subscription and usage status router.
Provides endpoints for checking usage, activating subscriptions, etc.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from dependencies import get_current_user
from utils.usage_tracker import UsageTracker
from typing import Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscription", tags=["Subscription"])


class SubscriptionActivateRequest(BaseModel):
    """Request to activate subscription after payment."""
    subscription_id: str


class SubscriptionResponse(BaseModel):
    """Response with subscription status."""
    status: str
    message: str
    subscription_id: str = None


@router.get("/usage/status", response_model=dict)
async def get_usage_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current usage status for the authenticated user.
    
    Returns usage counts, limits, and subscription status.
    """
    user_id = current_user["user_id"]
    
    usage = await UsageTracker.get_or_create_usage(user_id, db)
    
    return usage.to_dict()


@router.post("/activate", response_model=SubscriptionResponse)
async def activate_subscription(
    request: SubscriptionActivateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate subscription after successful PayPal payment.
    
    Call this endpoint after the user completes payment on PayPal.
    """
    user_id = current_user["user_id"]
    
    try:
        usage = await UsageTracker.activate_subscription(
            user_id=user_id,
            subscription_id=request.subscription_id,
            db=db
        )
        
        return SubscriptionResponse(
            status="success",
            message="Subscription activated! You now have unlimited access to all workflows.",
            subscription_id=request.subscription_id
        )
    except Exception as e:
        logger.error(f"Failed to activate subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate subscription"
        )


@router.post("/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel the user's subscription.
    
    The user will lose unlimited access but usage history is preserved.
    """
    user_id = current_user["user_id"]
    
    try:
        usage = await UsageTracker.cancel_subscription(
            user_id=user_id,
            db=db
        )
        
        return SubscriptionResponse(
            status="success",
            message="Subscription canceled. You will retain access until the end of your billing period.",
            subscription_id=usage.subscription_id
        )
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )


@router.get("/check/{workflow_type}")
async def check_workflow_access(
    workflow_type: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if user can access a specific workflow.
    
    Does NOT increment usage - just checks availability.
    Use this before showing workflow UI to user.
    
    Args:
        workflow_type: One of 'intake', 'drafting', 'evidence', 'research'
    """
    if workflow_type not in ["intake", "drafting", "evidence", "research"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid workflow type: {workflow_type}"
        )
    
    user_id = current_user["user_id"]
    usage = await UsageTracker.get_or_create_usage(user_id, db)
    
    can_access = usage.can_use_workflow(workflow_type)
    remaining = usage.get_remaining_free_uses(workflow_type)
    
    return {
        "workflow_type": workflow_type,
        "can_access": can_access,
        "remaining_free_uses": "unlimited" if usage.has_paid and usage.subscription_status == "active" else remaining,
        "has_subscription": usage.has_paid and usage.subscription_status == "active",
        "requires_payment": not can_access
    }
