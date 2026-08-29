import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def database_url() -> str:
    """Postgres URL from DATABASE_URL, or the local fabric default."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://fabric:fabric@localhost:5432/ar",
    )


def engine() -> Engine:
    """SQLAlchemy engine for the runtime database."""
    return create_engine(database_url())
