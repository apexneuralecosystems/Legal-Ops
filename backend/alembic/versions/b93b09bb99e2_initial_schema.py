"""initial_schema

Revision ID: b93b09bb99e2
Revises: 
Create Date: 2025-12-26 12:17:23.682609

Creates all tables for the Legal-Ops application:
- users (Apex auth)
- subscriptions (Apex payments)
- payment_orders (Apex payments)
- matters (core legal matter)
- documents (uploaded documents)
- segments (text segments with translations)
- pleadings (generated pleadings)
- research_cases (legal research)
- audit_logs (audit trail)
- user_usage (freemium tracking)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b93b09bb99e2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =====================
    # Users table (Apex auth)
    # =====================
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), server_default=''),
        sa.Column('username', sa.String(100), unique=True, nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # =====================
    # Subscriptions table (Apex payments)
    # =====================
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('plan_id', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('payment_provider', sa.String(50), server_default='paypal'),
        sa.Column('external_subscription_id', sa.String(255), nullable=True),
        sa.Column('amount', sa.String(20), nullable=True),
        sa.Column('currency', sa.String(10), server_default='USD'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
    )
    
    # =====================
    # Payment Orders table (Apex payments)
    # =====================
    op.create_table(
        'payment_orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('external_order_id', sa.String(255), nullable=True),
        sa.Column('amount', sa.String(20), nullable=False),
        sa.Column('currency', sa.String(10), server_default='USD'),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('payment_provider', sa.String(50), server_default='paypal'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    
    # =====================
    # User Usage table (freemium tracking)
    # =====================
    op.create_table(
        'user_usage',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, unique=True),
        sa.Column('intake_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('drafting_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('evidence_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('research_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('has_paid', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('subscription_id', sa.String(255), nullable=True),
        sa.Column('payment_date', sa.DateTime(), nullable=True),
        sa.Column('subscription_status', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_user_usage_user_id', 'user_usage', ['user_id'], unique=True)
    
    # =====================
    # Matters table (core legal matter)
    # =====================
    op.create_table(
        'matters',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('matter_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), server_default='intake'),
        sa.Column('court', sa.String(), nullable=True),
        sa.Column('jurisdiction', sa.String(), nullable=True),
        sa.Column('primary_language', sa.String(), server_default='ms'),
        sa.Column('parties', sa.JSON(), server_default='[]'),
        sa.Column('key_dates', sa.JSON(), server_default='[]'),
        sa.Column('issues', sa.JSON(), server_default='[]'),
        sa.Column('requested_remedies', sa.JSON(), server_default='[]'),
        sa.Column('volume_estimate', sa.Integer(), nullable=True),
        sa.Column('estimated_pages', sa.Integer(), nullable=True),
        sa.Column('jurisdictional_complexity', sa.Integer(), nullable=True),
        sa.Column('language_complexity', sa.Integer(), nullable=True),
        sa.Column('volume_risk', sa.Integer(), nullable=True),
        sa.Column('time_pressure', sa.Integer(), nullable=True),
        sa.Column('composite_score', sa.Float(), nullable=True),
        sa.Column('risk_rationale', sa.JSON(), server_default='[]'),
        sa.Column('human_review_required', sa.Boolean(), server_default='false'),
        sa.Column('reviewer_id', sa.String(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(), nullable=True),
    )
    op.create_index('ix_matters_title', 'matters', ['title'])
    
    # =====================
    # Documents table
    # =====================
    op.create_table(
        'documents',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('matter_id', sa.String(), sa.ForeignKey('matters.id', ondelete='CASCADE'), nullable=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=True),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('source_metadata', sa.Text(), nullable=True),
        sa.Column('received_utc', sa.DateTime(), nullable=True),
        sa.Column('ocr_needed', sa.Boolean(), server_default='false'),
        sa.Column('ocr_completed', sa.Boolean(), server_default='false'),
        sa.Column('ocr_confidence', sa.Integer(), nullable=True),
        sa.Column('doc_lang_hint', sa.String(), server_default='unknown'),
        sa.Column('file_hash', sa.String(), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), server_default='false'),
        sa.Column('duplicate_of', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_documents_matter_id', 'documents', ['matter_id'])
    op.create_index('ix_documents_file_hash', 'documents', ['file_hash'])
    
    # =====================
    # Segments table (text segments)
    # =====================
    op.create_table(
        'segments',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('document_id', sa.String(), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('lang', sa.String(), nullable=False),
        sa.Column('lang_confidence', sa.Float(), nullable=True),
        sa.Column('ocr_confidence', sa.Float(), nullable=True),
        sa.Column('translation_en', sa.Text(), nullable=True),
        sa.Column('translation_ms', sa.Text(), nullable=True),
        sa.Column('translation_literal', sa.Text(), nullable=True),
        sa.Column('translation_idiomatic', sa.Text(), nullable=True),
        sa.Column('alignment_score', sa.Float(), nullable=True),
        sa.Column('human_check_required', sa.Integer(), server_default='0'),
        sa.Column('flagged_for_review', sa.Integer(), server_default='0'),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_segments_document_id', 'segments', ['document_id'])
    
    # =====================
    # Pleadings table (generated pleadings)
    # =====================
    op.create_table(
        'pleadings',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('matter_id', sa.String(), sa.ForeignKey('matters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pleading_type', sa.String(), nullable=False),
        sa.Column('template_id', sa.String(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('pleading_ms_text', sa.Text(), nullable=True),
        sa.Column('pleading_ms_confidence', sa.Float(), nullable=True),
        sa.Column('pleading_en_text', sa.Text(), nullable=True),
        sa.Column('pleading_en_confidence', sa.Float(), nullable=True),
        sa.Column('paragraph_map', sa.JSON(), server_default='[]'),
        sa.Column('issues_used', sa.JSON(), server_default='[]'),
        sa.Column('prayers_used', sa.JSON(), server_default='[]'),
        sa.Column('consistency_report', sa.JSON(), nullable=True),
        sa.Column('has_high_severity_issues', sa.Boolean(), server_default='false'),
        sa.Column('block_for_human', sa.Boolean(), server_default='false'),
        sa.Column('status', sa.String(), server_default='draft'),
        sa.Column('reviewed_by', sa.String(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(), nullable=True),
    )
    op.create_index('ix_pleadings_matter_id', 'pleadings', ['matter_id'])
    
    # =====================
    # Research Cases table (legal research)
    # =====================
    op.create_table(
        'research_cases',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('citation', sa.String(), nullable=False, unique=True),
        sa.Column('court', sa.String(), nullable=False),
        sa.Column('decision_date', sa.DateTime(), nullable=True),
        sa.Column('case_name', sa.String(), nullable=True),
        sa.Column('headnote_en', sa.Text(), nullable=True),
        sa.Column('headnote_ms', sa.Text(), nullable=True),
        sa.Column('key_quotes', sa.JSON(), server_default='[]'),
        sa.Column('weight', sa.String(), nullable=True),
        sa.Column('jurisdiction', sa.String(), nullable=True),
        sa.Column('subject_areas', sa.JSON(), server_default='[]'),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('embedding_vector', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_accessed', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('access_count', sa.Integer(), server_default='0'),
    )
    op.create_index('ix_research_cases_citation', 'research_cases', ['citation'], unique=True)
    
    # =====================
    # Audit Logs table
    # =====================
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('matter_id', sa.String(), sa.ForeignKey('matters.id', ondelete='CASCADE'), nullable=True),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('action_description', sa.Text(), nullable=True),
        sa.Column('version_tag', sa.String(), nullable=True),
        sa.Column('entity_type', sa.String(), nullable=True),
        sa.Column('entity_id', sa.String(), nullable=True),
        sa.Column('changes', sa.JSON(), nullable=True),
        sa.Column('human_reviewed', sa.Boolean(), server_default='false'),
        sa.Column('reviewer_id', sa.String(), nullable=True),
        sa.Column('review_timestamp', sa.DateTime(), nullable=True),
        sa.Column('timestamp_utc', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
    )
    op.create_index('ix_audit_logs_matter_id', 'audit_logs', ['matter_id'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp_utc'])


def downgrade() -> None:
    # Drop tables in reverse order (dependencies first)
    op.drop_table('audit_logs')
    op.drop_table('research_cases')
    op.drop_table('pleadings')
    op.drop_table('segments')
    op.drop_table('documents')
    op.drop_table('matters')
    op.drop_table('user_usage')
    op.drop_table('payment_orders')
    op.drop_table('subscriptions')
    op.drop_table('users')
