"""create_lexis_credentials_table

Revision ID: 9d88ceb4a73c
Revises: add_cross_case_learning
Create Date: 2026-02-03 19:11:28.403355

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d88ceb4a73c'
down_revision: Union[str, None] = 'add_cross_case_learning'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create lexis_credentials table with VARCHAR user_id to match users.id type
    op.create_table('lexis_credentials',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('auth_method', sa.String(), nullable=True),
        sa.Column('cookies_encrypted', sa.Text(), nullable=True),
        sa.Column('cookies_expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    op.drop_table('lexis_credentials')
