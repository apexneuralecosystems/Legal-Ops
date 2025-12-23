"""
Segment model - Text segments with language tags and translations.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base


class Segment(Base):
    """
    Represents a text segment extracted from a document with language detection.
    """
    __tablename__ = "segments"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: f"SEG-{str(uuid.uuid4())[:12]}")
    
    # Foreign keys
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Segment location
    page_number = Column(Integer)
    sequence_number = Column(Integer)  # order within page
    
    # Original text
    text = Column(Text, nullable=False)
    
    # Language detection
    lang = Column(String, nullable=False)  # ms, en, mixed
    lang_confidence = Column(Float)  # 0.0-1.0
    
    # OCR confidence (if applicable)
    ocr_confidence = Column(Float)  # 0.0-1.0
    
    # Translation (if available)
    translation_en = Column(Text, nullable=True)
    translation_ms = Column(Text, nullable=True)
    translation_literal = Column(Text, nullable=True)
    translation_idiomatic = Column(Text, nullable=True)
    alignment_score = Column(Float, nullable=True)  # 0.0-1.0
    
    # Flags
    human_check_required = Column(Integer, default=False)
    flagged_for_review = Column(Integer, default=False)
    review_notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="segments")
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "segment_id": self.id,
            "doc_id": self.document_id,
            "page": self.page_number,
            "sequence": self.sequence_number,
            "text": self.text,
            "lang": self.lang,
            "lang_confidence": self.lang_confidence,
            "ocr_confidence": self.ocr_confidence,
            "translation_en": self.translation_en,
            "translation_ms": self.translation_ms,
            "translation_literal": self.translation_literal,
            "translation_idiomatic": self.translation_idiomatic,
            "alignment_score": self.alignment_score,
            "human_check_required": bool(self.human_check_required),
            "flagged_for_review": bool(self.flagged_for_review)
        }
