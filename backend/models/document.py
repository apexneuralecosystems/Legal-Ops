"""
Document model - Uploaded/collected documents.
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base


class Document(Base):
    """
    Represents a document collected from various sources.
    """
    __tablename__ = "documents"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: f"DOC-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}")
    
    # Foreign key to matter
    matter_id = Column(String, ForeignKey("matters.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Document metadata
    filename = Column(String, nullable=False)
    original_filename = Column(String)
    mime_type = Column(String)
    file_path = Column(String)  # path in storage
    file_size = Column(Integer)  # bytes
    
    # Source information
    source = Column(String, nullable=False)  # gmail, outlook, upload, whatsapp, dms
    source_metadata = Column(Text)  # JSON string with sender, subject, etc.
    received_utc = Column(DateTime)
    
    # Processing status
    ocr_needed = Column(Boolean, default=False)
    ocr_completed = Column(Boolean, default=False)
    ocr_confidence = Column(Integer)  # 0-100
    
    # Language detection
    doc_lang_hint = Column(String, default="unknown")  # ms, en, mixed, unknown
    
    # Deduplication
    file_hash = Column(String, index=True)  # SHA-256
    is_duplicate = Column(Boolean, default=False)
    duplicate_of = Column(String, nullable=True)  # doc_id of original
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    matter = relationship("Matter", back_populates="documents")
    segments = relationship("Segment", back_populates="document", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,  # Added for frontend compatibility
            "doc_id": self.id,
            "matter_id": self.matter_id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "source": self.source,
            "received_utc": self.received_utc.isoformat() if self.received_utc else None,
            "ocr_needed": self.ocr_needed,
            "ocr_completed": self.ocr_completed,
            "ocr_confidence": self.ocr_confidence,
            "doc_lang_hint": self.doc_lang_hint,
            "is_duplicate": self.is_duplicate,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
