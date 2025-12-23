"""
AuditLog model - Version history and audit trail.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base


class AuditLog(Base):
    """
    Represents an audit log entry for tracking changes and agent actions.
    """
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to matter (optional)
    matter_id = Column(String, ForeignKey("matters.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Action information
    agent_id = Column(String, nullable=False)  # which agent performed the action
    action_type = Column(String, nullable=False)  # document_collection, ocr, translation, etc.
    action_description = Column(Text)
    
    # Version tracking
    version_tag = Column(String)
    entity_type = Column(String)  # matter, document, pleading, etc.
    entity_id = Column(String)
    
    # Changes (stored as JSON)
    changes = Column(JSON, nullable=True)  # before/after values
    
    # Human review
    human_reviewed = Column(Boolean, default=False)
    reviewer_id = Column(String, nullable=True)
    review_timestamp = Column(DateTime, nullable=True)
    
    # Metadata
    timestamp_utc = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String)
    ip_address = Column(String, nullable=True)
    
    # Relationships
    matter = relationship("Matter", back_populates="audit_logs")
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "log_id": self.id,
            "matter_id": self.matter_id,
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "action_description": self.action_description,
            "version_tag": self.version_tag,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "changes": self.changes,
            "human_reviewed": bool(self.human_reviewed),
            "reviewer_id": self.reviewer_id,
            "timestamp_utc": self.timestamp_utc.isoformat() if self.timestamp_utc else None
        }
