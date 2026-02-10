"""add processing_status column to matters table

Revision ID: d1a2b3c4d5e6
Revises: create_cached_judgments
Create Date: 2026-02-10 07:00:00.000000

Adds processing_status column to matters table for real-time
progress tracking during matter intake processing.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1a2b3c4d5e6'
down_revision: Union[str, None] = 'create_cached_judgments'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('matters', sa.Column('processing_status', sa.String(), nullable=True, server_default='Initializing...'))


def downgrade() -> None:
    op.drop_column('matters', 'processing_status')
