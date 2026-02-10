"""Case Insights Models - Automated Case Analysis"""

from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, Index, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class CaseInsight(Base):
    """Stores automated case analysis insights"""
    __tablename__ = "case_insights"
    
    id = Column(String(36), primary_key=True)
    matter_id = Column(String(36), ForeignKey('matters.id', ondelete='CASCADE'), nullable=False)
    
    # Insight classification
    insight_type = Column(String(50), nullable=False)  
    # 'swot_analysis', 'risk_assessment', 'evidence_gap', 'timeline_analysis', 'strategic_recommendation'
    
    # Insight details
    title = Column(String(500), nullable=False)  # Brief title
    description = Column(Text, nullable=False)  # Full explanation
    severity = Column(String(20), nullable=True)  # 'critical', 'high', 'medium', 'low' for risks
    category = Column(String(50), nullable=True)  # 'strength', 'weakness', 'opportunity', 'threat' for SWOT
    
    # Additional structured data
    insight_data = Column(JSON, nullable=True)  # Extra context, references, metrics
    
    # Metadata
    confidence = Column(Float, default=0.0)  # 0.0-1.0 confidence in insight
    actionable = Column(Boolean, default=False)  # Is this actionable?
    action_deadline = Column(DateTime, nullable=True)  # When action must be taken
    resolved = Column(Boolean, default=False)  # Has this been addressed?
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(36), nullable=True)  # User ID
    
    # Timestamps
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    matter = relationship("Matter")

    __table_args__ = (
        Index('idx_insight_matter', 'matter_id'),
        Index('idx_insight_type', 'matter_id', 'insight_type'),
        Index('idx_insight_severity', 'matter_id', 'severity'),
        Index('idx_insight_actionable', 'matter_id', 'actionable', 'resolved'),
    )


class CaseMetric(Base):
    """Tracks case intelligence metrics over time"""
    __tablename__ = "case_metrics"
    
    id = Column(String(36), primary_key=True)
    matter_id = Column(String(36), ForeignKey('matters.id', ondelete='CASCADE'), nullable=False)
    metric_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Accuracy metrics
    answer_helpful_rate = Column(Float, default=0.0)  # % thumbs up
    correction_rate = Column(Float, default=0.0)  # % requiring corrections
    
    # Knowledge metrics
    entities_extracted = Column(Integer, default=0)
    entities_verified = Column(Integer, default=0)
    relationships_mapped = Column(Integer, default=0)
    
    # Usage metrics
    questions_answered = Column(Integer, default=0)
    avg_confidence = Column(Float, default=0.0)
    unique_insights = Column(Integer, default=0)
    
    # Case progress metrics
    documents_uploaded = Column(Integer, default=0)
    evidence_gaps_identified = Column(Integer, default=0)
    critical_risks_identified = Column(Integer, default=0)
    
    # Relationships
    matter = relationship("Matter")

    __table_args__ = (
        Index('idx_metric_matter_date', 'matter_id', 'metric_date'),
    )
