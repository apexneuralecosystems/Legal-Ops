from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class OCRDocument(Base):
    __tablename__ = "ocr_documents"

    id = Column(String(36), primary_key=True)
    matter_id = Column(String, ForeignKey("matters.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String(512), nullable=False)
    file_path = Column(String(1024), nullable=True)
    file_hash = Column(String(64), nullable=False, unique=True, index=True)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True, default="application/pdf")
    total_pages = Column(Integer, nullable=True)
    ocr_status = Column(String(20), nullable=False, default="pending")
    ocr_started_at = Column(DateTime, nullable=True)
    ocr_completed_at = Column(DateTime, nullable=True)
    ocr_engine = Column(String(50), nullable=True, default="google_vision")
    extracted_metadata = Column(JSON, default=dict)
    primary_language = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(36), nullable=True)

    pages = relationship("OCRPage", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("OCRChunk", back_populates="document", cascade="all, delete-orphan")
    processing_logs = relationship("OCRProcessingLog", back_populates="document", cascade="all, delete-orphan")


class OCRPage(Base):
    __tablename__ = "ocr_pages"

    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("ocr_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=False)
    cleaned_text = Column(Text, nullable=True)
    bounding_boxes = Column(JSON, nullable=True)
    blocks_json = Column(JSON, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    word_count = Column(Integer, nullable=True)
    char_count = Column(Integer, nullable=True)
    is_header_page = Column(Boolean, default=False)
    is_blank = Column(Boolean, default=False)
    has_tables = Column(Boolean, default=False)
    has_signatures = Column(Boolean, default=False)
    detected_headers = Column(JSON, default=list)
    detected_footers = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("OCRDocument", back_populates="pages")


class OCRChunk(Base):
    __tablename__ = "ocr_chunks"

    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("ocr_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_sequence = Column(Integer, nullable=False)
    chunk_id_str = Column(String(100), nullable=True)
    chunk_text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    source_page_start = Column(Integer, nullable=False)
    source_page_end = Column(Integer, nullable=False)
    source_char_start = Column(Integer, nullable=True)
    source_char_end = Column(Integer, nullable=True)
    language = Column(String(10), nullable=True, default="en")
    chunk_type = Column(String(50), nullable=True)
    section_ref = Column(String(100), nullable=True)
    is_embeddable = Column(Boolean, default=True, index=True)
    embedding_model = Column(String(100), nullable=True)
    embedded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("OCRDocument", back_populates="chunks")


class OCRProcessingLog(Base):
    __tablename__ = "ocr_processing_log"

    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("ocr_documents.id", ondelete="CASCADE"), nullable=True, index=True)
    page_number = Column(Integer, nullable=True)
    step_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)
    duration_ms = Column(Integer, nullable=True)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("OCRDocument", back_populates="processing_logs")

