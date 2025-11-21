"""Convert deal status and stage to SQLAlchemy Enum

Revision ID: 907fbefc5bd8
Revises: 001
Create Date: 2025-11-21 08:30:14.803811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '907fbefc5bd8'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No database schema changes required
    # Changed from String to SQLAlchemy Enum with native_enum=False
    # This only affects Python-side type handling
    pass


def downgrade() -> None:
    # No database schema changes required
    pass
