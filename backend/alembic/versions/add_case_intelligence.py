"""Alembic migration: Add case intelligence knowledge graph tables"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_case_intelligence'
down_revision = 'add_conversation_memory'
branch_labels = None
depends_on = None


def upgrade():
    # Create case_entities table
    op.create_table(
        'case_entities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('matter_id', sa.String(36), sa.ForeignKey('matters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_name', sa.String(500), nullable=False),
        sa.Column('entity_value', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), default=0.0),
        sa.Column('source_document', sa.String(200), nullable=True),
        sa.Column('verified_by_user', sa.String(36), nullable=True),
        sa.Column('extracted_at', sa.DateTime(), nullable=False),
    )
    
    # Create indexes for case_entities
    op.create_index('idx_case_entity_matter', 'case_entities', ['matter_id'])
    op.create_index('idx_case_entity_type', 'case_entities', ['matter_id', 'entity_type'])
    op.create_index('idx_case_entity_confidence', 'case_entities', ['matter_id', 'confidence'])
    
    # Create case_relationships table
    op.create_table(
        'case_relationships',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('matter_id', sa.String(36), sa.ForeignKey('matters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_1_id', sa.String(36), sa.ForeignKey('case_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_2_id', sa.String(36), sa.ForeignKey('case_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(100), nullable=False),
        sa.Column('relationship_description', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), default=0.0),
        sa.Column('extracted_at', sa.DateTime(), nullable=False),
    )
    
    # Create indexes for case_relationships
    op.create_index('idx_case_rel_matter', 'case_relationships', ['matter_id'])
    op.create_index('idx_case_rel_entities', 'case_relationships', ['entity_1_id', 'entity_2_id'])
    op.create_index('idx_case_rel_type', 'case_relationships', ['matter_id', 'relationship_type'])


def downgrade():
    op.drop_index('idx_case_rel_type', table_name='case_relationships')
    op.drop_index('idx_case_rel_entities', table_name='case_relationships')
    op.drop_index('idx_case_rel_matter', table_name='case_relationships')
    op.drop_table('case_relationships')
    
    op.drop_index('idx_case_entity_confidence', table_name='case_entities')
    op.drop_index('idx_case_entity_type', table_name='case_entities')
    op.drop_index('idx_case_entity_matter', table_name='case_entities')
    op.drop_table('case_entities')
