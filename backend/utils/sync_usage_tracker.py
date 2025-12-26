"""
Sync version of usage tracking for backward compatibility.
Used by workflow endpoints that still use sync database sessions.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.usage import UserUsage
from fastapi import HTTPException, status
import uuid
import logging

logger = logging.getLogger(__name__)


class SyncUsageTracker:
    """
    Sync version of UsageTracker for endpoints using sync database.
    """
    
    @staticmethod
    def get_or_create_usage(user_id: str, db: Session) -> UserUsage:
        """Get existing usage record for user, or create new one."""
        usage = db.query(UserUsage).filter(UserUsage.user_id == user_id).first()
        
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
            db.commit()
            db.refresh(usage)
        
        return usage
    
    @staticmethod
    def check_and_increment(
        user_id: str,
        workflow_type: str,
        db: Session
    ) -> dict:
        """
        Check if user can use workflow and increment counter if allowed.
        Returns dict with allowed status and usage info.
        """
        usage = SyncUsageTracker.get_or_create_usage(user_id, db)
        
        # If user has active subscription, allow unlimited access
        if usage.has_paid and usage.subscription_status == "active":
            usage.increment_usage(workflow_type)
            db.commit()
            
            return {
                "allowed": True,
                "remaining": "unlimited",
                "requires_payment": False,
                "message": "Subscription active - unlimited access"
            }
        
        # Check free limit
        if not usage.can_use_workflow(workflow_type):
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
        db.commit()
        
        logger.info(f"User {user_id} used {workflow_type} ({new_count} total, {remaining} remaining)")
        
        return {
            "allowed": True,
            "remaining": remaining,
            "requires_payment": False,
            "message": f"You have {remaining} free {workflow_type} use(s) remaining" if remaining > 0 else f"This was your last free {workflow_type} use"
        }
    
    @staticmethod
    def require_usage_or_payment(
        user_id: str,
        workflow_type: str,
        db: Session
    ) -> dict:
        """
        Check usage and raise 402 error if payment required.
        Use this as a guard at the start of workflow endpoints.
        """
        result = SyncUsageTracker.check_and_increment(user_id, workflow_type, db)
        
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
