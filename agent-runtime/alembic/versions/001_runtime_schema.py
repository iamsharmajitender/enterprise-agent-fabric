"""create runtime schema

Revision ID: 001
Revises:
Create Date: 2026-08-20
"""

from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  op.execute("CREATE SCHEMA IF NOT EXISTS runtime")


def downgrade() -> None:
  op.execute("DROP SCHEMA IF EXISTS runtime CASCADE")
