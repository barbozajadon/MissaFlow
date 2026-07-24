"""
Business logic for the liturgical calendar - looking up season/psalm/etc.
for a given Mass date, used to auto-populate the Mass Planner page.
"""
from __future__ import annotations

import datetime
import logging
from typing import Optional

from sqlalchemy import select

from database.database import get_session
from database.models import LiturgicalCalendar

logger = logging.getLogger(__name__)


def get_by_date(mass_date: datetime.date) -> Optional[LiturgicalCalendar]:
    with get_session() as session:
        return session.scalar(
            select(LiturgicalCalendar).where(LiturgicalCalendar.date == mass_date)
        )


def upsert_entry(
    mass_date: datetime.date,
    season: Optional[str] = None,
    feast_name: Optional[str] = None,
    psalm: Optional[str] = None,
    psalm_response: Optional[str] = None,
    psalm_response_hymn_id: Optional[int] = None,
    gospel_acclamation: Optional[str] = None,
    gloria_required: Optional[bool] = None,
    creed_required: Optional[bool] = None,
    notes: Optional[str] = None,
) -> LiturgicalCalendar:
    """
    Create or update the liturgical calendar entry for a date.

    Any argument left as None leaves that field UNCHANGED on an existing
    entry (so e.g. an importer that only knows psalm_response doesn't
    wipe out a season/psalm that was already set some other way). For a
    brand-new entry, None fields fall back to sensible defaults.
    """
    with get_session() as session:
        entry = session.scalar(
            select(LiturgicalCalendar).where(LiturgicalCalendar.date == mass_date)
        )
        is_new = entry is None
        if entry is None:
            entry = LiturgicalCalendar(date=mass_date, season=season or "Ordinary Time")
            session.add(entry)
        entry.psalm_response_hymn_id = psalm_response_hymn_id
        if season is not None:
            entry.season = season
        if feast_name is not None:
            entry.feast_name = feast_name
        if psalm is not None:
            entry.psalm = psalm
        if psalm_response is not None:
            entry.psalm_response = psalm_response
        if psalm_response_hymn_id is not None:
            entry.psalm_response_hymn_id = psalm_response_hymn_id
        if gospel_acclamation is not None:
            entry.gospel_acclamation = gospel_acclamation
        if gloria_required is not None:
            entry.gloria_required = gloria_required
        if creed_required is not None:
            entry.creed_required = creed_required
        elif is_new:
            entry.creed_required = True
        if notes is not None:
            entry.notes = notes

        session.commit()
        session.refresh(entry)
        return entry
    


def get_current_season(today: Optional[datetime.date] = None) -> str:
    """
    Best-effort fallback season lookup for the Dashboard when no calendar
    entry exists for today. Real parish liturgical dates should be seeded
    into LiturgicalCalendar via sample_data.py or manual entry - this is
    only a rough placeholder so the Dashboard never shows a blank field.
    """
    today = today or datetime.date.today()
    with get_session() as session:
        entry = session.scalar(
            select(LiturgicalCalendar).where(LiturgicalCalendar.date == today)
        )
        if entry:
            return entry.season
    return "Ordinary Time"


def get_upcoming_dates(limit: int = 10) -> list[LiturgicalCalendar]:
    today = datetime.date.today()
    with get_session() as session:
        stmt = (
            select(LiturgicalCalendar)
            .where(LiturgicalCalendar.date >= today)
            .order_by(LiturgicalCalendar.date)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())
