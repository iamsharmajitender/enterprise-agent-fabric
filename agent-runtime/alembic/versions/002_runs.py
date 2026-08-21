"""create run pin table

Revision ID: 002
Revises: 001
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE runtime.runs (
          correlation_id TEXT PRIMARY KEY,
          idempotency_key TEXT NOT NULL UNIQUE,
          session_id TEXT NOT NULL,
          route_id TEXT NOT NULL,
          route_version TEXT NOT NULL,
          activation_target TEXT,
          agent_client_id TEXT,
          hydrated_tools JSONB NOT NULL DEFAULT '[]'::jsonb,
          status TEXT NOT NULL,
          result JSONB,
          checkpoint JSONB,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX runs_session_status ON runtime.runs (session_id, status)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS runtime.runs")
