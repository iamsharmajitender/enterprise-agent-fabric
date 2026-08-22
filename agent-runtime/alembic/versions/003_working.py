"""add working notes column on run pin

Revision ID: 003
Revises: 002
Create Date: 2026-08-22
"""

from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE runtime.runs ADD COLUMN working JSONB")


def downgrade() -> None:
    op.execute("ALTER TABLE runtime.runs DROP COLUMN IF EXISTS working")
