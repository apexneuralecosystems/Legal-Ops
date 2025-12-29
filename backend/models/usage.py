"""
UserUsage model for tracking workflow usage in freemium model.
Tracks how many times each user has used each workflow type.
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import uuid
from config import settings


class UserUsage(Base):
    """
    Track user workflow usage for freemium payment gate.
    
    Each user gets 1 free use of each workflow type:
    - Intake workflow
    - Drafting workflow  
    - Evidence workflow
    - Research workflow
    
    After free uses are exhausted, user must subscribe for unlimited access.
    """
    __tablename__ = "user_usage"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to user
    user_id = Column(String(36), nullable=False, index=True, unique=True)
    
    # Usage counters for each workflow type
    intake_count = Column(Integer, default=0, nullable=False)
    drafting_count = Column(Integer, default=0, nullable=False)
    evidence_count = Column(Integer, default=0, nullable=False)
    research_count = Column(Integer, default=0, nullable=False)
    
    # Payment/subscription status
    has_paid = Column(Boolean, default=False, nullable=False)
    subscription_id = Column(String(255), nullable=True)  # PayPal subscription ID
    payment_date = Column(DateTime, nullable=True)
    subscription_status = Column(String(50), nullable=True)  # active, canceled, expired
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Free usage limits (class constants)
    FREE_LIMITS = {
        "intake": 10,
        "drafting": 10,
        "evidence": 10,
        "research": 10
    }
    
    def get_usage_count(self, workflow_type: str) -> int:
        """Get current usage count for a workflow type."""
        return getattr(self, f"{workflow_type}_count", 0)
    
    def increment_usage(self, workflow_type: str) -> int:
        """Increment usage count for a workflow type. Returns new count."""
        current = self.get_usage_count(workflow_type)
        new_count = current + 1
        setattr(self, f"{workflow_type}_count", new_count)
        return new_count
    
    def can_use_workflow(self, workflow_type: str) -> bool:
        """Check if user can use a workflow (has free uses left or has paid)."""
        if settings.SKIP_PAYMENT_CHECK:
            return True

        if self.has_paid and self.subscription_status == "active":
            return True
        
        current = self.get_usage_count(workflow_type)
        limit = self.FREE_LIMITS.get(workflow_type, 1)
        return current < limit
    
    def get_remaining_free_uses(self, workflow_type: str) -> int:
        """Get remaining free uses for a workflow type."""
        if self.has_paid and self.subscription_status == "active":
            return -1  # Unlimited
        
        current = self.get_usage_count(workflow_type)
        limit = self.FREE_LIMITS.get(workflow_type, 1)
        return max(0, limit - current)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "has_paid": self.has_paid,
            "subscription_status": self.subscription_status,
            "usage": {
                "intake": {
                    "used": self.intake_count,
                    "limit": "unlimited" if self.has_paid else self.FREE_LIMITS["intake"],
                    "remaining": "unlimited" if self.has_paid else self.get_remaining_free_uses("intake")
                },
                "drafting": {
                    "used": self.drafting_count,
                    "limit": "unlimited" if self.has_paid else self.FREE_LIMITS["drafting"],
                    "remaining": "unlimited" if self.has_paid else self.get_remaining_free_uses("drafting")
                },
                "evidence": {
                    "used": self.evidence_count,
                    "limit": "unlimited" if self.has_paid else self.FREE_LIMITS["evidence"],
                    "remaining": "unlimited" if self.has_paid else self.get_remaining_free_uses("evidence")
                },
                "research": {
                    "used": self.research_count,
                    "limit": "unlimited" if self.has_paid else self.FREE_LIMITS["research"],
                    "remaining": "unlimited" if self.has_paid else self.get_remaining_free_uses("research")
                }
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
