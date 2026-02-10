"""Case Intelligence Models - Knowledge Graph Entities and Relationships"""

from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class CaseEntity(Base):
    """Stores extracted case entities (parties, claims, defenses, dates, issues)"""
    __tablename__ = "case_entities"
    
    id = Column(String(36), primary_key=True)
    matter_id = Column(String(36), ForeignKey('matters.id', ondelete='CASCADE'), nullable=False)
    
    # Entity classification
    entity_type = Column(String(50), nullable=False)  # 'party', 'claim', 'defense', 'date', 'issue', 'document'
    entity_name = Column(String(500), nullable=False)  # Display name
    
    # Detailed information stored as JSON
    entity_value = Column(JSON, nullable=True)  # Full structured data
    
    # Metadata
    confidence = Column(Float, default=0.0)  # 0.0-1.0 extraction confidence
    source_document = Column(String(200), nullable=True)  # Which document this came from
    verified_by_user = Column(String(36), nullable=True)  # User ID who verified
    extracted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    matter = relationship("Matter", back_populates="entities")
    outgoing_relationships = relationship("CaseRelationship", 
                                         foreign_keys="CaseRelationship.entity_1_id",
                                         back_populates="entity_1",
                                         cascade="all, delete-orphan")
    incoming_relationships = relationship("CaseRelationship", 
                                         foreign_keys="CaseRelationship.entity_2_id",
                                         back_populates="entity_2",
                                         cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_case_entity_matter', 'matter_id'),
        Index('idx_case_entity_type', 'matter_id', 'entity_type'),
        Index('idx_case_entity_confidence', 'matter_id', 'confidence'),
    )


class CaseRelationship(Base):
    """Stores relationships between case entities"""
    __tablename__ = "case_relationships"
    
    id = Column(String(36), primary_key=True)
    matter_id = Column(String(36), ForeignKey('matters.id', ondelete='CASCADE'), nullable=False)
    
    # Relationship endpoints
    entity_1_id = Column(String(36), ForeignKey('case_entities.id', ondelete='CASCADE'), nullable=False)
    entity_2_id = Column(String(36), ForeignKey('case_entities.id', ondelete='CASCADE'), nullable=False)
    
    # Relationship details
    relationship_type = Column(String(100), nullable=False)  # 'claims_against', 'defended_by', 'relies_on', etc.
    relationship_description = Column(Text, nullable=True)  # Human-readable description
    
    # Metadata
    confidence = Column(Float, default=0.0)
    extracted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    matter = relationship("Matter")
    entity_1 = relationship("CaseEntity", foreign_keys=[entity_1_id], back_populates="outgoing_relationships")
    entity_2 = relationship("CaseEntity", foreign_keys=[entity_2_id], back_populates="incoming_relationships")

    __table_args__ = (
        Index('idx_case_rel_matter', 'matter_id'),
        Index('idx_case_rel_entities', 'entity_1_id', 'entity_2_id'),
        Index('idx_case_rel_type', 'matter_id', 'relationship_type'),
    )
