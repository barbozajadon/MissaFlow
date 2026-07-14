"""
Database engine and session management for the Church Hymn Planner.

Uses SQLite by default (database.db in the project root) via SQLAlchemy.
Call `init_db()` once at application startup to create tables if they
don't already exist.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base

logger = logging.getLogger(__name__)

# database.db lives at the project root, alongside app.py
DB_PATH = Path(__file__).resolve().parent.parent / "database.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False is required because PySide6 may touch the
# session from callback/slot contexts other than the thread that created it.
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create all tables if they don't exist yet."""
    logger.info("Initializing database at %s", DB_PATH)
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context-managed session for use in services:

        with get_session() as session:
            session.add(obj)
            session.commit()

    Rolls back automatically on exception.
    """
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
