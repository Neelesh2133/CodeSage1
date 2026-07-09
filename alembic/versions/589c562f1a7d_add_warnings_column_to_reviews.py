"""add warnings column to reviews

Revision ID: 589c562f1a7d
Revises: bcb386d16b0b
Create Date: 2026-07-07 13:57:05.294324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '589c562f1a7d'
down_revision: Union[str, Sequence[str], None] = 'bcb386d16b0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('reviews', sa.Column('warnings', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('reviews', 'warnings')
