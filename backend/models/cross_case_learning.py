"""Cross-Case Learning Models - Learn from Historical Cases"""

from sqlalchemy import Column, String, Text, Float, DateTime, Integer, ForeignKey, Index, JSON, Numeric, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class CasePattern(Base):
    """Stores learned patterns from multiple cases"""
    __tablename__ = "case_patterns"
    
    id = Column(String(36), primary_key=True)
    
    # Pattern classification
    pattern_type = Column(String(100), nullable=False)
    # 'successful_defense', 'winning_argument', 'settlement_trigger', 
    # 'evidence_factor', 'procedural_success', 'failed_strategy'
    
    # Pattern details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    # Statistical data
    frequency = Column(Integer, default=1)  # How many cases this appeared in
    success_rate = Column(Float, default=0.0)  # 0.0 to 1.0
    total_cases_analyzed = Column(Integer, default=0)
    
    # Applicability
    applicable_to = Column(JSON, nullable=True)  # Case types, jurisdictions, etc.
    # Example: {"case_types": ["breach_of_contract"], "jurisdictions": ["Kuala Lumpur"]}
    
    # Evidence and factors
    key_factors = Column(JSON, nullable=True)  # What made this pattern work/fail
    required_evidence = Column(JSON, nullable=True)  # Evidence needed for this pattern
    
    # Metadata
    confidence = Column(Float, default=0.0)  # Statistical confidence
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('idx_pattern_type', 'pattern_type'),
        Index('idx_pattern_success_rate', 'success_rate'),
    )


class CaseOutcome(Base):
    """Stores outcomes of closed cases for learning"""
    __tablename__ = "case_outcomes"
    
    id = Column(String(36), primary_key=True)
    matter_id = Column(String(36), ForeignKey('matters.id', ondelete='CASCADE'), nullable=False)
    
    # Outcome details
    outcome_type = Column(String(50), nullable=False)
    # 'judgment_plaintiff', 'judgment_defendant', 'settlement', 'dismissed', 'withdrawn'
    
    outcome_date = Column(DateTime, nullable=True)
    
    # Financial outcome
    claim_amount = Column(Numeric(15, 2), nullable=True)  # Original claim
    settlement_amount = Column(Numeric(15, 2), nullable=True)  # Final amount
    costs_awarded = Column(Numeric(15, 2), nullable=True)
    
    # Timeline
    filing_date = Column(DateTime, nullable=True)
    duration_months = Column(Integer, nullable=True)  # Time to resolution
    
    # Key factors that influenced outcome
    key_factors = Column(JSON, nullable=True)
    # Example: ["strong_documentary_evidence", "expert_testimony", "summary_judgment"]
    
    decisive_evidence = Column(JSON, nullable=True)  # What evidence was most important
    winning_arguments = Column(JSON, nullable=True)  # Arguments that succeeded
    failed_arguments = Column(JSON, nullable=True)  # Arguments that failed
    
    # Procedural details
    motions_filed = Column(JSON, nullable=True)  # List of motions and their outcomes
    appeals_filed = Column(Boolean, default=False)
    appeal_outcome = Column(String(50), nullable=True)
    
    # Lessons learned
    lessons_learned = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(String(36), nullable=True)
    
    # Relationships
    matter = relationship("Matter")

    __table_args__ = (
        Index('idx_outcome_matter', 'matter_id'),
        Index('idx_outcome_type', 'outcome_type'),
        Index('idx_outcome_date', 'outcome_date'),
    )


class CaseSimilarity(Base):
    """Stores case similarity scores for efficient matching"""
    __tablename__ = "case_similarities"
    
    id = Column(String(36), primary_key=True)
    matter_id_1 = Column(String(36), ForeignKey('matters.id', ondelete='CASCADE'), nullable=False)
    matter_id_2 = Column(String(36), ForeignKey('matters.id', ondelete='CASCADE'), nullable=False)
    
    # Similarity scores
    overall_similarity = Column(Float, default=0.0)  # 0.0 to 1.0
    type_similarity = Column(Float, default=0.0)  # Same case type
    jurisdiction_similarity = Column(Float, default=0.0)  # Same jurisdiction
    claim_amount_similarity = Column(Float, default=0.0)  # Similar amounts
    issue_similarity = Column(Float, default=0.0)  # Similar legal issues
    party_similarity = Column(Float, default=0.0)  # Similar party types
    
    # Detailed comparison
    common_factors = Column(JSON, nullable=True)  # What makes them similar
    key_differences = Column(JSON, nullable=True)  # How they differ
    
    # Metadata
    computed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('idx_similarity_matter1', 'matter_id_1', 'overall_similarity'),
        Index('idx_similarity_matter2', 'matter_id_2', 'overall_similarity'),
    )
