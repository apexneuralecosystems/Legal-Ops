"""
Matter model - Core case/matter entity.
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base


class Matter(Base):
    """
    Represents a legal matter/case with all metadata.
    """
    __tablename__ = "matters"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: f"MAT-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}")
    
    # Basic information
    title = Column(String, nullable=False, index=True)
    matter_type = Column(String, nullable=False)  # contract, tort, criminal, etc.
    status = Column(String, default="intake")  # intake, drafting, research, ready, filed
    
    # Court information
    court = Column(String)
    jurisdiction = Column(String)  # Peninsular Malaysia, East Malaysia
    primary_language = Column(String, default="ms")  # ms or en
    
    # Parties (stored as JSON array)
    parties = Column(JSON, default=list)  # [{role, name, address, source}]
    
    # Key dates (stored as JSON array)
    key_dates = Column(JSON, default=list)  # [{type, date, source}]
    
    # Issues and remedies
    issues = Column(JSON, default=list)  # [{id, text_en, text_ms, confidence}]
    requested_remedies = Column(JSON, default=list)  # [{text, confidence}]
    
    # Volume estimates
    volume_estimate = Column(Integer)  # word count
    estimated_pages = Column(Integer)
    
    # Risk scoring
    jurisdictional_complexity = Column(Integer)  # 1-5
    language_complexity = Column(Integer)  # 1-5
    volume_risk = Column(Integer)  # 1-5
    time_pressure = Column(Integer)  # 1-5
    composite_score = Column(Float)  # average
    risk_rationale = Column(JSON, default=list)
    
    # Human review flags
    human_review_required = Column(Boolean, default=False)
    reviewer_id = Column(String, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
    
    # Relationships
    documents = relationship("Document", back_populates="matter", cascade="all, delete-orphan")
    pleadings = relationship("Pleading", back_populates="matter", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="matter", cascade="all, delete-orphan")
    
    @property
    def matter_id(self):
        """Alias for id to match Pydantic schema."""
        return self.id
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "matter_id": self.id,
            "title": self.title,
            "matter_type": self.matter_type,
            "status": self.status,
            "court": self.court,
            "jurisdiction": self.jurisdiction,
            "primary_language": self.primary_language,
            "parties": self.parties,
            "key_dates": self.key_dates,
            "issues": self.issues,
            "requested_remedies": self.requested_remedies,
            "volume_estimate": self.volume_estimate,
            "estimated_pages": self.estimated_pages,
            "risk_scores": {
                "jurisdictional_complexity": self.jurisdictional_complexity,
                "language_complexity": self.language_complexity,
                "volume_risk": self.volume_risk,
                "time_pressure": self.time_pressure,
                "composite_score": self.composite_score,
                "rationale": self.risk_rationale
            },
            "human_review_required": self.human_review_required,
            "reviewer_id": self.reviewer_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
