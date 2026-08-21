import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def database_url() -> str:
  return os.environ.get(
      "DATABASE_URL",
      "postgresql+psycopg://fabric:fabric@localhost:5432/ar",
  )


def engine() -> Engine:
  return create_engine(database_url())
