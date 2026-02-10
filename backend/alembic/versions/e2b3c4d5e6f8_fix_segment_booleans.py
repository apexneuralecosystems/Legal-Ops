"""fix segment booleans

Revision ID: e2b3c4d5e6f8
Revises: e2b3c4d5e6f7
Create Date: 2026-02-10 10:00:00.000000

Converts integer columns in segments table to boolean to match SQLAlchemy model.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e2b3c4d5e6f8'
down_revision = 'e2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert human_check_required from INTEGER to BOOLEAN
    op.execute('ALTER TABLE segments ALTER COLUMN human_check_required DROP DEFAULT')
    op.execute('ALTER TABLE segments ALTER COLUMN human_check_required TYPE BOOLEAN USING human_check_required::boolean')
    op.execute('ALTER TABLE segments ALTER COLUMN human_check_required SET DEFAULT false')
    
    # Convert flagged_for_review from INTEGER to BOOLEAN
    op.execute('ALTER TABLE segments ALTER COLUMN flagged_for_review DROP DEFAULT')
    op.execute('ALTER TABLE segments ALTER COLUMN flagged_for_review TYPE BOOLEAN USING flagged_for_review::boolean')
    op.execute('ALTER TABLE segments ALTER COLUMN flagged_for_review SET DEFAULT false')


def downgrade() -> None:
    # Revert to INTEGER
    op.execute('ALTER TABLE segments ALTER COLUMN human_check_required DROP DEFAULT')
    op.execute('ALTER TABLE segments ALTER COLUMN human_check_required TYPE INTEGER USING human_check_required::integer')
    op.execute('ALTER TABLE segments ALTER COLUMN human_check_required SET DEFAULT 0')
    
    op.execute('ALTER TABLE segments ALTER COLUMN flagged_for_review DROP DEFAULT')
    op.execute('ALTER TABLE segments ALTER COLUMN flagged_for_review TYPE INTEGER USING flagged_for_review::integer')
    op.execute('ALTER TABLE segments ALTER COLUMN flagged_for_review SET DEFAULT 0')
