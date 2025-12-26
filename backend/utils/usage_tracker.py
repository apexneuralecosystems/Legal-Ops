"""
Usage tracking for freemium payment gate.
Provides utilities for checking and enforcing workflow usage limits.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.usage import UserUsage
from fastapi import HTTPException, status
import uuid
import logging

logger = logging.getLogger(__name__)


class UsageTracker:
    """
    Track and enforce usage limits for freemium model.
    
    Each user gets 1 free use of each workflow type.
    After that, they must subscribe for unlimited access.
    """
    
    @staticmethod
    async def get_or_create_usage(user_id: str, db: AsyncSession) -> UserUsage:
        """
        Get existing usage record for user, or create new one.
        
        Args:
            user_id: UUID of the user
            db: Database session
            
        Returns:
            UserUsage record for the user
        """
        result = await db.execute(
            select(UserUsage).where(UserUsage.user_id == user_id)
        )
        usage = result.scalar_one_or_none()
        
        if not usage:
            logger.info(f"Creating new usage record for user {user_id}")
            usage = UserUsage(
                id=str(uuid.uuid4()),
                user_id=user_id,
                intake_count=0,
                drafting_count=0,
                evidence_count=0,
                research_count=0,
                has_paid=False
            )
            db.add(usage)
            await db.commit()
            await db.refresh(usage)
        
        return usage
    
    @staticmethod
    async def check_and_increment(
        user_id: str,
        workflow_type: str,
        db: AsyncSession
    ) -> dict:
        """
        Check if user can use workflow and increment counter if allowed.
        
        Args:
            user_id: UUID of the user
            workflow_type: Type of workflow (intake, drafting, evidence, research)
            db: Database session
            
        Returns:
            Dict with:
                - allowed: bool, whether user can proceed
                - remaining: int or "unlimited", remaining free uses
                - requires_payment: bool, whether payment is required
                - message: str, user-facing message
                
        Raises:
            HTTPException with 402 if payment required
        """
        usage = await UsageTracker.get_or_create_usage(user_id, db)
        
        # If user has active subscription, allow unlimited access
        if usage.has_paid and usage.subscription_status == "active":
            # Still increment for analytics
            usage.increment_usage(workflow_type)
            await db.commit()
            
            return {
                "allowed": True,
                "remaining": "unlimited",
                "requires_payment": False,
                "message": "Subscription active - unlimited access"
            }
        
        # Check free limit
        if not usage.can_use_workflow(workflow_type):
            remaining = usage.get_remaining_free_uses(workflow_type)
            logger.info(f"User {user_id} hit free {workflow_type} limit")
            
            return {
                "allowed": False,
                "remaining": 0,
                "requires_payment": True,
                "message": f"Free {workflow_type} limit reached. Please subscribe to continue.",
                "redirect_url": "/pricing"
            }
        
        # Increment usage and allow
        new_count = usage.increment_usage(workflow_type)
        remaining = usage.get_remaining_free_uses(workflow_type)
        await db.commit()
        
        logger.info(f"User {user_id} used {workflow_type} ({new_count} total, {remaining} remaining)")
        
        return {
            "allowed": True,
            "remaining": remaining,
            "requires_payment": False,
            "message": f"You have {remaining} free {workflow_type} use(s) remaining" if remaining > 0 else f"This was your last free {workflow_type} use"
        }
    
    @staticmethod
    async def require_usage_or_payment(
        user_id: str,
        workflow_type: str,
        db: AsyncSession
    ) -> dict:
        """
        Check usage and raise 402 error if payment required.
        Use this as a guard at the start of workflow endpoints.
        
        Args:
            user_id: UUID of the user
            workflow_type: Type of workflow
            db: Database session
            
        Returns:
            Usage info dict if allowed
            
        Raises:
            HTTPException 402 if payment required
        """
        result = await UsageTracker.check_and_increment(user_id, workflow_type, db)
        
        if not result["allowed"]:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "message": result["message"],
                    "requires_payment": True,
                    "redirect_url": result.get("redirect_url", "/pricing"),
                    "workflow_type": workflow_type
                }
            )
        
        return result
    
    @staticmethod
    async def activate_subscription(
        user_id: str,
        subscription_id: str,
        db: AsyncSession
    ) -> UserUsage:
        """
        Activate user subscription after successful payment.
        
        Args:
            user_id: UUID of the user
            subscription_id: PayPal subscription/order ID
            db: Database session
            
        Returns:
            Updated UserUsage record
        """
        from datetime import datetime
        
        usage = await UsageTracker.get_or_create_usage(user_id, db)
        
        usage.has_paid = True
        usage.subscription_id = subscription_id
        usage.payment_date = datetime.utcnow()
        usage.subscription_status = "active"
        
        await db.commit()
        await db.refresh(usage)
        
        logger.info(f"Activated subscription for user {user_id}: {subscription_id}")
        
        return usage
    
    @staticmethod
    async def cancel_subscription(
        user_id: str,
        db: AsyncSession
    ) -> UserUsage:
        """
        Cancel user subscription.
        
        Args:
            user_id: UUID of the user
            db: Database session
            
        Returns:
            Updated UserUsage record
        """
        usage = await UsageTracker.get_or_create_usage(user_id, db)
        
        usage.subscription_status = "canceled"
        # Note: has_paid stays True to keep history
        
        await db.commit()
        await db.refresh(usage)
        
        logger.info(f"Canceled subscription for user {user_id}")
        
        return usage
