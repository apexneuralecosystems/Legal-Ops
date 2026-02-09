"""Alembic migration: Add cross-case learning tables"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_cross_case_learning'
down_revision = 'add_case_insights'
branch_labels = None
depends_on = None


def upgrade():
    # Create case_patterns table
    op.create_table(
        'case_patterns',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('pattern_type', sa.String(100), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('frequency', sa.Integer(), default=1),
        sa.Column('success_rate', sa.Float(), default=0.0),
        sa.Column('total_cases_analyzed', sa.Integer(), default=0),
        sa.Column('applicable_to', sa.JSON(), nullable=True),
        sa.Column('key_factors', sa.JSON(), nullable=True),
        sa.Column('required_evidence', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), default=0.0),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Create indexes for case_patterns
    op.create_index('idx_pattern_type', 'case_patterns', ['pattern_type'])
    op.create_index('idx_pattern_success_rate', 'case_patterns', ['success_rate'])
    
    # Create case_outcomes table
    op.create_table(
        'case_outcomes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('matter_id', sa.String(36), sa.ForeignKey('matters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('outcome_type', sa.String(50), nullable=False),
        sa.Column('outcome_date', sa.DateTime(), nullable=True),
        sa.Column('claim_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('settlement_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('costs_awarded', sa.Numeric(15, 2), nullable=True),
        sa.Column('filing_date', sa.DateTime(), nullable=True),
        sa.Column('duration_months', sa.Integer(), nullable=True),
        sa.Column('key_factors', sa.JSON(), nullable=True),
        sa.Column('decisive_evidence', sa.JSON(), nullable=True),
        sa.Column('winning_arguments', sa.JSON(), nullable=True),
        sa.Column('failed_arguments', sa.JSON(), nullable=True),
        sa.Column('motions_filed', sa.JSON(), nullable=True),
        sa.Column('appeals_filed', sa.Boolean(), default=False),
        sa.Column('appeal_outcome', sa.String(50), nullable=True),
        sa.Column('lessons_learned', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(36), nullable=True),
    )
    
    # Create indexes for case_outcomes
    op.create_index('idx_outcome_matter', 'case_outcomes', ['matter_id'])
    op.create_index('idx_outcome_type', 'case_outcomes', ['outcome_type'])
    op.create_index('idx_outcome_date', 'case_outcomes', ['outcome_date'])
    
    # Create case_similarities table
    op.create_table(
        'case_similarities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('matter_id_1', sa.String(36), sa.ForeignKey('matters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('matter_id_2', sa.String(36), sa.ForeignKey('matters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('overall_similarity', sa.Float(), default=0.0),
        sa.Column('type_similarity', sa.Float(), default=0.0),
        sa.Column('jurisdiction_similarity', sa.Float(), default=0.0),
        sa.Column('claim_amount_similarity', sa.Float(), default=0.0),
        sa.Column('issue_similarity', sa.Float(), default=0.0),
        sa.Column('party_similarity', sa.Float(), default=0.0),
        sa.Column('common_factors', sa.JSON(), nullable=True),
        sa.Column('key_differences', sa.JSON(), nullable=True),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
    )
    
    # Create indexes for case_similarities
    op.create_index('idx_similarity_matter1', 'case_similarities', ['matter_id_1', 'overall_similarity'])
    op.create_index('idx_similarity_matter2', 'case_similarities', ['matter_id_2', 'overall_similarity'])


def downgrade():
    op.drop_index('idx_similarity_matter2', table_name='case_similarities')
    op.drop_index('idx_similarity_matter1', table_name='case_similarities')
    op.drop_table('case_similarities')
    
    op.drop_index('idx_outcome_date', table_name='case_outcomes')
    op.drop_index('idx_outcome_type', table_name='case_outcomes')
    op.drop_index('idx_outcome_matter', table_name='case_outcomes')
    op.drop_table('case_outcomes')
    
    op.drop_index('idx_pattern_success_rate', table_name='case_patterns')
    op.drop_index('idx_pattern_type', table_name='case_patterns')
    op.drop_table('case_patterns')
