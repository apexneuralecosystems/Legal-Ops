"""
Cached Judgment Model - Store full court judgments to avoid refetching

This table caches complete judgment text from Lexis Advance to:
1. Speed up repeated argument building (0 seconds vs 30-50 seconds)
2. Reduce load on Lexis servers
3. Enable offline argument generation (with cached cases)
4. Improve user experience with instant judgment access
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, Index
from datetime import datetime, timezone
from database import Base


class CachedJudgment(Base):
    """Stores complete court judgment text for fast retrieval"""
    
    __tablename__ = "cached_judgments"
    
    # Primary identification
    id = Column(String(36), primary_key=True)
    case_link = Column(String(1000), unique=True, nullable=False, index=True)
    
    # Case metadata
    citation = Column(String(200), nullable=True, index=True)
    case_title = Column(String(500), nullable=True)
    court = Column(String(200), nullable=True)
    judgment_date = Column(String(50), nullable=True)  # As string from case data
    
    # Full judgment content
    full_text = Column(Text, nullable=False)  # Complete 50-200 page judgment
    
    # Structured sections (if extracted)
    headnotes = Column(Text, nullable=True)
    facts = Column(Text, nullable=True)
    issues_text = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    judges = Column(Text, nullable=True)  # JSON array as string
    
    # Document metrics
    word_count = Column(Integer, default=0)
    sections_count = Column(Integer, default=0)  # Number of identified sections
    
    # Cache metadata
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fetch_success = Column(String(10), default="true")  # "true" or "false" as string
    fetch_error = Column(Text, nullable=True)  # Error message if fetch failed
    
    # Performance tracking
    access_count = Column(Integer, default=0)  # How many times accessed from cache
    last_accessed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_cached_judgment_citation', 'citation'),
        Index('idx_cached_judgment_link', 'case_link'),
        Index('idx_cached_judgment_court', 'court'),
        Index('idx_cached_judgment_fetched', 'fetched_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        import json
        
        judges_list = []
        if self.judges:
            try:
                judges_list = json.loads(self.judges)
            except:
                judges_list = [self.judges]
        
        return {
            "id": self.id,
            "case_link": self.case_link,
            "citation": self.citation,
            "case_title": self.case_title,
            "court": self.court,
            "judgment_date": self.judgment_date,
            "full_text": self.full_text,
            "headnotes": self.headnotes,
            "facts": self.facts,
            "issues_text": self.issues_text,
            "reasoning": self.reasoning,
            "judges": judges_list,
            "word_count": self.word_count,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "fetch_success": self.fetch_success == "true",
            "access_count": self.access_count,
            "from_cache": True
        }
