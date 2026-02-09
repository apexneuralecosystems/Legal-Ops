"""Alembic migration: Add case insights tables"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_case_insights'
down_revision = 'add_case_intelligence'
branch_labels = None
depends_on = None


def upgrade():
    # Create case_insights table
    op.create_table(
        'case_insights',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('matter_id', sa.String(36), sa.ForeignKey('matters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('insight_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('insight_data', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), default=0.0),
        sa.Column('actionable', sa.Boolean(), default=False),
        sa.Column('action_deadline', sa.DateTime(), nullable=True),
        sa.Column('resolved', sa.Boolean(), default=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(36), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
    )
    
    # Create indexes for case_insights
    op.create_index('idx_insight_matter', 'case_insights', ['matter_id'])
    op.create_index('idx_insight_type', 'case_insights', ['matter_id', 'insight_type'])
    op.create_index('idx_insight_severity', 'case_insights', ['matter_id', 'severity'])
    op.create_index('idx_insight_actionable', 'case_insights', ['matter_id', 'actionable', 'resolved'])
    
    # Create case_metrics table
    op.create_table(
        'case_metrics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('matter_id', sa.String(36), sa.ForeignKey('matters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('metric_date', sa.DateTime(), nullable=False),
        sa.Column('answer_helpful_rate', sa.Float(), default=0.0),
        sa.Column('correction_rate', sa.Float(), default=0.0),
        sa.Column('entities_extracted', sa.Integer(), default=0),
        sa.Column('entities_verified', sa.Integer(), default=0),
        sa.Column('relationships_mapped', sa.Integer(), default=0),
        sa.Column('questions_answered', sa.Integer(), default=0),
        sa.Column('avg_confidence', sa.Float(), default=0.0),
        sa.Column('unique_insights', sa.Integer(), default=0),
        sa.Column('documents_uploaded', sa.Integer(), default=0),
        sa.Column('evidence_gaps_identified', sa.Integer(), default=0),
        sa.Column('critical_risks_identified', sa.Integer(), default=0),
    )
    
    # Create indexes for case_metrics
    op.create_index('idx_metric_matter_date', 'case_metrics', ['matter_id', 'metric_date'])


def downgrade():
    op.drop_index('idx_metric_matter_date', table_name='case_metrics')
    op.drop_table('case_metrics')
    
    op.drop_index('idx_insight_actionable', table_name='case_insights')
    op.drop_index('idx_insight_severity', table_name='case_insights')
    op.drop_index('idx_insight_type', table_name='case_insights')
    op.drop_index('idx_insight_matter', table_name='case_insights')
    op.drop_table('case_insights')
