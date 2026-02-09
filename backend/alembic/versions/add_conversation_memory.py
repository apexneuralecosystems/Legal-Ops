"""Add chat_messages and case_learnings tables

Revision ID: add_conversation_memory
Revises: 
Create Date: 2026-01-30 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_conversation_memory'
down_revision = '3926d51d6f0f'  # Points to the latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('matter_id', sa.String(36), sa.ForeignKey('matters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('conversation_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('method', sa.String(50), nullable=True),
        sa.Column('context_used', sa.Text, nullable=True),
        sa.Column('confidence', sa.String(20), nullable=True),
        sa.Column('helpful', sa.Boolean, nullable=True),
        sa.Column('user_correction', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for performance
    op.create_index('idx_chat_matter_id', 'chat_messages', ['matter_id'])
    op.create_index('idx_chat_conversation_id', 'chat_messages', ['conversation_id'])
    op.create_index('idx_chat_created_at', 'chat_messages', ['created_at'])
    op.create_index('idx_chat_matter_conversation', 'chat_messages', ['matter_id', 'conversation_id', 'created_at'])
    
    # Create case_learnings table
    op.create_table(
        'case_learnings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('matter_id', sa.String(36), sa.ForeignKey('matters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('learning_type', sa.String(50), nullable=False),
        sa.Column('original_text', sa.Text, nullable=True),
        sa.Column('corrected_text', sa.Text, nullable=False),
        sa.Column('importance', sa.Integer, nullable=False, server_default='3'),
        sa.Column('source_message_id', sa.String(36), sa.ForeignKey('chat_messages.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('applied_count', sa.Integer, nullable=False, server_default='0'),
    )
    
    # Create indexes
    op.create_index('idx_learnings_matter_id', 'case_learnings', ['matter_id'])
    op.create_index('idx_learnings_importance', 'case_learnings', ['importance'])


def downgrade():
    op.drop_index('idx_learnings_importance', 'case_learnings')
    op.drop_index('idx_learnings_matter_id', 'case_learnings')
    op.drop_table('case_learnings')
    
    op.drop_index('idx_chat_matter_conversation', 'chat_messages')
    op.drop_index('idx_chat_created_at', 'chat_messages')
    op.drop_index('idx_chat_conversation_id', 'chat_messages')
    op.drop_index('idx_chat_matter_id', 'chat_messages')
    op.drop_table('chat_messages')
