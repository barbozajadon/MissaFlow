"""
Business logic for hymns: CRUD, favorites, and recent-search tracking.

UI code should never touch SQLAlchemy sessions directly - it goes through
these service functions instead, keeping business logic separate from UI
(per the project's MVC-like architecture).
"""
from __future__ import annotations

import datetime
import logging
from typing import Optional

from sqlalchemy import select

from database.database import get_session
from database.models import Favorite, Hymn, RecentSearch

logger = logging.getLogger(__name__)


def get_all_hymns() -> list[Hymn]:
    with get_session() as session:
        return list(session.scalars(select(Hymn).order_by(Hymn.title)).all())


def get_hymn_by_id(hymn_id: int) -> Optional[Hymn]:
    with get_session() as session:
        return session.get(Hymn, hymn_id)


def create_hymn(
    hymn_number: Optional[str],
    title: str,
    lyrics: Optional[str] = None,
    category: Optional[str] = None,
    language: str = "English",
    tags: Optional[str] = None,
    start_slide: Optional[int] = None,
    end_slide: Optional[int] = None,
) -> Hymn:
    with get_session() as session:
        hymn = Hymn(
            hymn_number=hymn_number,
            title=title,
            lyrics=lyrics,
            category=category,
            language=language,
            tags=tags,
            start_slide=start_slide,
            end_slide=end_slide,
        )
        session.add(hymn)
        session.commit()
        session.refresh(hymn)
        logger.info("Created hymn #%s %s", hymn_number, title)
        return hymn


def update_hymn(hymn_id: int, **fields) -> Optional[Hymn]:
    with get_session() as session:
        hymn = session.get(Hymn, hymn_id)
        if not hymn:
            return None
        for key, value in fields.items():
            if hasattr(hymn, key):
                setattr(hymn, key, value)
        hymn.updated_at = datetime.datetime.utcnow()
        session.commit()
        session.refresh(hymn)
        return hymn


def delete_hymn(hymn_id: int) -> bool:
    with get_session() as session:
        hymn = session.get(Hymn, hymn_id)
        if not hymn:
            return False
        session.delete(hymn)
        session.commit()
        return True


def search_hymns(
    query: str = "",
    category: Optional[str] = None,
    language: Optional[str] = None,
) -> list[Hymn]:
    """
    Search by hymn number OR title/lyrics keyword, optionally filtered by
    category/language. Designed to be called on every keystroke from the
    search dialog - keep it fast, no heavy joins.
    """
    with get_session() as session:
        stmt = select(Hymn)

        query = (query or "").strip()
        if query:
            like_pattern = f"%{query}%"
            if query.isdigit():
                stmt = stmt.where(
                    (Hymn.hymn_number == query) | (Hymn.title.ilike(like_pattern))
                )
            else:
                stmt = stmt.where(
                    (Hymn.title.ilike(like_pattern)) | (Hymn.lyrics.ilike(like_pattern))
                )

        if category:
            stmt = stmt.where(Hymn.category == category)
        if language:
            stmt = stmt.where(Hymn.language == language)

        stmt = stmt.order_by(Hymn.title).limit(100)
        return list(session.scalars(stmt).all())


def get_categories() -> list[str]:
    with get_session() as session:
        rows = session.scalars(
            select(Hymn.category).distinct().where(Hymn.category.is_not(None))
        ).all()
        return sorted(r for r in rows if r)


# --- Favorites -------------------------------------------------------------

def get_favorites() -> list[Hymn]:
    with get_session() as session:
        favs = session.scalars(select(Favorite).order_by(Favorite.created_at.desc())).all()
        return [f.hymn for f in favs if f.hymn]


def toggle_favorite(hymn_id: int) -> bool:
    """Returns True if now favorited, False if removed."""
    with get_session() as session:
        existing = session.scalar(select(Favorite).where(Favorite.hymn_id == hymn_id))
        if existing:
            session.delete(existing)
            session.commit()
            return False
        session.add(Favorite(hymn_id=hymn_id))
        session.commit()
        return True


# --- Recent searches ---------------------------------------------------

def log_search(query: str) -> None:
    query = (query or "").strip()
    if not query:
        return
    with get_session() as session:
        session.add(RecentSearch(query=query))
        session.commit()


def get_recent_searches(limit: int = 10) -> list[str]:
    with get_session() as session:
        rows = session.scalars(
            select(RecentSearch.query)
            .order_by(RecentSearch.searched_at.desc())
            .limit(limit)
        ).all()
        # de-duplicate while preserving order
        seen: set[str] = set()
        result = []
        for q in rows:
            if q not in seen:
                seen.add(q)
                result.append(q)
        return result
