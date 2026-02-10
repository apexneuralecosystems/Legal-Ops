"""add section_ref to segments

Revision ID: e2b3c4d5e6f7
Revises: d1a2b3c4d5e6
Create Date: 2026-02-10 08:30:00.000000

Adds section_ref column to segments table.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e2b3c4d5e6f7'
down_revision = 'd1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('segments', sa.Column('section_ref', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('segments', 'section_ref')
