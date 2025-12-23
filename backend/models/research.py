"""
ResearchCase model - Legal authorities and citations.
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float
from datetime import datetime
import uuid
from database import Base


class ResearchCase(Base):
    """
    Represents a legal case/authority from research.
    """
    __tablename__ = "research_cases"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: f"CASE-{str(uuid.uuid4())[:12]}")
    
    # Citation information
    citation = Column(String, nullable=False, unique=True, index=True)
    court = Column(String, nullable=False)
    decision_date = Column(DateTime)
    
    # Case details
    case_name = Column(String)
    headnote_en = Column(Text)
    headnote_ms = Column(Text)
    
    # Key quotes (stored as JSON array)
    key_quotes = Column(JSON, default=list)  # [{orig, translation, page}]
    
    # Classification
    weight = Column(String)  # binding, persuasive, distinguishing
    jurisdiction = Column(String)  # Malaysian, English, etc.
    subject_areas = Column(JSON, default=list)  # [contract, tort, etc.]
    
    # Search metadata
    relevance_score = Column(Float)  # for ranking
    embedding_vector = Column(Text, nullable=True)  # for vector search (stored as JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "case_id": self.id,
            "citation": self.citation,
            "court": self.court,
            "decision_date": self.decision_date.isoformat() if self.decision_date else None,
            "case_name": self.case_name,
            "headnote_en": self.headnote_en,
            "headnote_ms": self.headnote_ms,
            "key_quotes": self.key_quotes,
            "weight": self.weight,
            "jurisdiction": self.jurisdiction,
            "subject_areas": self.subject_areas,
            "relevance_score": self.relevance_score
        }
