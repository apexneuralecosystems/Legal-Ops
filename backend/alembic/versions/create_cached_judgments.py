"""create cached_judgments table

Revision ID: create_cached_judgments
Revises: 9d88ceb4a73c
Create Date: 2026-02-06 10:00:00.000000

Phase 3: Caching & Optimization
Stores full court judgments to avoid refetching from Lexis.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_cached_judgments'
down_revision = '9d88ceb4a73c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create cached_judgments table"""
    op.create_table(
        'cached_judgments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('case_link', sa.String(length=1000), nullable=False),
        sa.Column('citation', sa.String(length=200), nullable=True),
        sa.Column('case_title', sa.String(length=500), nullable=True),
        sa.Column('court', sa.String(length=200), nullable=True),
        sa.Column('judgment_date', sa.String(length=50), nullable=True),
        sa.Column('full_text', sa.Text(), nullable=False),
        sa.Column('headnotes', sa.Text(), nullable=True),
        sa.Column('facts', sa.Text(), nullable=True),
        sa.Column('issues_text', sa.Text(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('judges', sa.Text(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True, default=0),
        sa.Column('sections_count', sa.Integer(), nullable=True, default=0),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.Column('fetch_success', sa.String(length=10), nullable=True, default='true'),
        sa.Column('fetch_error', sa.Text(), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=True, default=0),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('case_link', name='uq_cached_judgment_link')
    )
    
    # Create indexes for fast lookups
    op.create_index('idx_cached_judgment_citation', 'cached_judgments', ['citation'], unique=False)
    op.create_index('idx_cached_judgment_link', 'cached_judgments', ['case_link'], unique=False)
    op.create_index('idx_cached_judgment_court', 'cached_judgments', ['court'], unique=False)
    op.create_index('idx_cached_judgment_fetched', 'cached_judgments', ['fetched_at'], unique=False)


def downgrade() -> None:
    """Drop cached_judgments table"""
    op.drop_index('idx_cached_judgment_fetched', table_name='cached_judgments')
    op.drop_index('idx_cached_judgment_court', table_name='cached_judgments')
    op.drop_index('idx_cached_judgment_link', table_name='cached_judgments')
    op.drop_index('idx_cached_judgment_citation', table_name='cached_judgments')
    op.drop_table('cached_judgments')
