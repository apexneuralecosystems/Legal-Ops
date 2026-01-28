"""add_ocr_tables

Revision ID: c7d1e8f2a3b4
Revises: b93b09bb99e2
Create Date: 2026-01-28 11:30:00.000000

Adds enhanced OCR tables for legal document processing:
- ocr_documents: Document registry with deduplication
- ocr_pages: Page-level OCR storage with raw + cleaned text
- ocr_chunks: RAG-ready semantic chunks with traceability
- ocr_processing_log: Audit trail for OCR operations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = 'c7d1e8f2a3b4'
down_revision: Union[str, None] = 'b93b09bb99e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =====================
    # TABLE: ocr_documents (Document Registry)
    # =====================
    op.create_table(
        'ocr_documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('matter_id', sa.String(), sa.ForeignKey('matters.id', ondelete='SET NULL'), nullable=True),
        
        # File metadata
        sa.Column('filename', sa.String(512), nullable=False),
        sa.Column('file_path', sa.String(1024), nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(100), server_default='application/pdf'),
        
        # OCR status
        sa.Column('total_pages', sa.Integer(), nullable=True),
        sa.Column('ocr_status', sa.String(20), server_default='pending'),  # pending/processing/completed/failed
        sa.Column('ocr_started_at', sa.DateTime(), nullable=True),
        sa.Column('ocr_completed_at', sa.DateTime(), nullable=True),
        sa.Column('ocr_engine', sa.String(50), server_default='google_vision'),
        
        # Document-level metadata (extracted)
        sa.Column('extracted_metadata', sa.JSON(), server_default='{}'),  # case_no, court, parties, dates
        sa.Column('primary_language', sa.String(10), nullable=True),
        
        # Audit
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(36), nullable=True),
    )
    
    op.create_index('idx_ocr_documents_matter', 'ocr_documents', ['matter_id'])
    op.create_index('idx_ocr_documents_status', 'ocr_documents', ['ocr_status'])
    op.create_index('idx_ocr_documents_hash', 'ocr_documents', ['file_hash'], unique=True)

    # =====================
    # TABLE: ocr_pages (Page-Level OCR Storage)
    # =====================
    op.create_table(
        'ocr_pages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('ocr_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        
        # OCR output (preserved)
        sa.Column('raw_text', sa.Text(), nullable=False),  # Original Vision API output
        sa.Column('cleaned_text', sa.Text(), nullable=True),  # Post-processed (no headers/noise)
        
        # Layout data
        sa.Column('bounding_boxes', sa.JSON(), nullable=True),  # Array of {text, x1, y1, x2, y2}
        sa.Column('blocks_json', sa.JSON(), nullable=True),  # Full Vision API blocks structure
        
        # Quality metrics
        sa.Column('ocr_confidence', sa.Float(), nullable=True),  # 0.0 to 1.0
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('char_count', sa.Integer(), nullable=True),
        
        # Flags
        sa.Column('is_header_page', sa.Boolean(), server_default='false'),  # First page with letterhead
        sa.Column('is_blank', sa.Boolean(), server_default='false'),  # No meaningful text
        sa.Column('has_tables', sa.Boolean(), server_default='false'),  # Contains table structure
        sa.Column('has_signatures', sa.Boolean(), server_default='false'),  # Contains signatures
        
        # Detected patterns on this page
        sa.Column('detected_headers', sa.JSON(), server_default='[]'),  # Repeating header patterns
        sa.Column('detected_footers', sa.JSON(), server_default='[]'),  # Repeating footer patterns
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    op.create_index('idx_ocr_pages_document', 'ocr_pages', ['document_id'])
    op.create_index('idx_ocr_pages_confidence', 'ocr_pages', ['ocr_confidence'])
    # Note: Full-text search index would be:
    # CREATE INDEX idx_ocr_pages_cleaned_fts ON ocr_pages USING GIN (to_tsvector('english', cleaned_text));
    # This requires raw SQL execution for PostgreSQL
    op.create_unique_constraint('uq_ocr_pages_doc_page', 'ocr_pages', ['document_id', 'page_number'])

    # =====================
    # TABLE: ocr_chunks (RAG-Ready Semantic Chunks)
    # =====================
    op.create_table(
        'ocr_chunks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('ocr_documents.id', ondelete='CASCADE'), nullable=False),
        
        # Chunk identity
        sa.Column('chunk_sequence', sa.Integer(), nullable=False),  # Order within document
        sa.Column('chunk_id_str', sa.String(100), nullable=True),  # Human-readable: "doc-abc-p2-c3"
        
        # Content
        sa.Column('chunk_text', sa.Text(), nullable=False),  # The actual chunk content
        sa.Column('token_count', sa.Integer(), nullable=False),  # Counted via tiktoken
        
        # Source traceability
        sa.Column('source_page_start', sa.Integer(), nullable=False),  # First page this chunk spans
        sa.Column('source_page_end', sa.Integer(), nullable=False),  # Last page this chunk spans
        sa.Column('source_char_start', sa.Integer(), nullable=True),  # Character offset in cleaned_text
        sa.Column('source_char_end', sa.Integer(), nullable=True),
        
        # Chunk metadata
        sa.Column('language', sa.String(10), server_default='en'),
        sa.Column('chunk_type', sa.String(50), nullable=True),  # heading/paragraph/clause/footer
        sa.Column('section_ref', sa.String(100), nullable=True),  # e.g., "Section 5", "Ground 3"
        
        # Embedding control
        sa.Column('is_embeddable', sa.Boolean(), server_default='true'),  # FALSE for headers/noise
        sa.Column('embedding_model', sa.String(100), nullable=True),  # e.g., "text-embedding-3-small"
        sa.Column('embedded_at', sa.DateTime(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    op.create_index('idx_ocr_chunks_document', 'ocr_chunks', ['document_id'])
    op.create_index('idx_ocr_chunks_pages', 'ocr_chunks', ['source_page_start', 'source_page_end'])
    op.create_index('idx_ocr_chunks_embeddable', 'ocr_chunks', ['is_embeddable'])
    op.create_unique_constraint('uq_ocr_chunks_doc_seq', 'ocr_chunks', ['document_id', 'chunk_sequence'])

    # =====================
    # TABLE: ocr_processing_log (Audit Trail)
    # =====================
    op.create_table(
        'ocr_processing_log',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('ocr_documents.id', ondelete='CASCADE'), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        
        sa.Column('step_name', sa.String(100), nullable=False),  # e.g., "vision_api_call"
        sa.Column('status', sa.String(20), nullable=False),  # started/completed/failed
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        
        sa.Column('input_summary', sa.Text(), nullable=True),  # Brief description of input
        sa.Column('output_summary', sa.Text(), nullable=True),  # Brief description of output
        sa.Column('error_message', sa.Text(), nullable=True),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    op.create_index('idx_ocr_log_document', 'ocr_processing_log', ['document_id'])
    op.create_index('idx_ocr_log_step', 'ocr_processing_log', ['step_name'])


def downgrade() -> None:
    # Drop tables in reverse order (dependencies first)
    op.drop_table('ocr_processing_log')
    op.drop_table('ocr_chunks')
    op.drop_table('ocr_pages')
    op.drop_table('ocr_documents')
