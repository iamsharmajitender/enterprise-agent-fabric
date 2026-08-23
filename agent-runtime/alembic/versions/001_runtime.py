"""create runtime schema and run pin

Revision ID: 001
Revises:
Create Date: 2026-08-23
"""

from pathlib import Path
from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SQL = Path(__file__).resolve().parents[2] / "db" / "migration" / "V1__runtime.sql"


def upgrade() -> None:
  op.execute(_SQL.read_text())


def downgrade() -> None:
  op.execute("DROP SCHEMA IF EXISTS runtime CASCADE")
