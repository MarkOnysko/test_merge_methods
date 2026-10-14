"""SQLAlchemy engine, session factory and the declarative base."""
from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app import config

_is_sqlite = config.DATABASE_URL.startswith("sqlite")

# check_same_thread=False: FastAPI may run a dependency and its route in
# different worker threads, but each request gets its own session.
engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_conn, _record):
        # SQLite ignores foreign keys unless you ask for them on every connection.
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """All models inherit from this; Alembic reads Base.metadata."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request, closed afterwards."""
    with SessionLocal() as session:
        yield session
