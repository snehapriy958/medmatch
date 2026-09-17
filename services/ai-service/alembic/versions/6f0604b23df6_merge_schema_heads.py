"""merge schema heads

Revision ID: 6f0604b23df6
Revises: 0008, 3f3884863f27
Create Date: 2026-09-18 04:27:10.811069

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f0604b23df6'
down_revision: Union[str, Sequence[str], None] = ('0008', '3f3884863f27')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
