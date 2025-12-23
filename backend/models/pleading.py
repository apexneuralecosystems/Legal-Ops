"""
Pleading model - Generated legal pleadings.
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base


class Pleading(Base):
    """
    Represents a generated legal pleading (Malay + English versions).
    """
    __tablename__ = "pleadings"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: f"PLD-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}")
    
    # Foreign key to matter
    matter_id = Column(String, ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Pleading metadata
    pleading_type = Column(String, nullable=False)  # statement_of_claim, defense, reply, etc.
    template_id = Column(String)
    version = Column(Integer, default=1)
    
    # Malay version (primary for West Malaysia)
    pleading_ms_text = Column(Text)
    pleading_ms_confidence = Column(Float)
    
    # English version (companion or primary for East Malaysia)
    pleading_en_text = Column(Text)
    pleading_en_confidence = Column(Float)
    
    # Paragraph mapping (JSON array)
    paragraph_map = Column(JSON, default=list)  # [{para_id, source_refs, confidence}]
    
    # Issues and prayers used
    issues_used = Column(JSON, default=list)
    prayers_used = Column(JSON, default=list)
    
    # QA results
    consistency_report = Column(JSON, nullable=True)
    has_high_severity_issues = Column(Boolean, default=False)
    block_for_human = Column(Boolean, default=False)
    
    # Review status
    status = Column(String, default="draft")  # draft, under_review, approved, filed
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
    
    # Relationships
    matter = relationship("Matter", back_populates="pleadings")
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "pleading_id": self.id,
            "matter_id": self.matter_id,
            "pleading_type": self.pleading_type,
            "template_id": self.template_id,
            "version": self.version,
            "pleading_ms_text": self.pleading_ms_text,
            "pleading_ms_confidence": self.pleading_ms_confidence,
            "pleading_en_text": self.pleading_en_text,
            "pleading_en_confidence": self.pleading_en_confidence,
            "paragraph_map": self.paragraph_map,
            "issues_used": self.issues_used,
            "prayers_used": self.prayers_used,
            "consistency_report": self.consistency_report,
            "has_high_severity_issues": self.has_high_severity_issues,
            "block_for_human": self.block_for_human,
            "status": self.status,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
