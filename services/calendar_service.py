"""
Business logic for the liturgical calendar - looking up season/psalm/etc.
for a given Mass date, used to auto-populate the Mass Planner page.
"""
from __future__ import annotations
import requests 
import xml.etree.ElementTree as ET
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
            select(LiturgicalCalendar).where(
                LiturgicalCalendar.date == mass_date
            )
        )
    
def upsert_entry(
    mass_date: datetime.date,
    season: str,
    feast_name: Optional[str] = None,
    psalm: Optional[str] = None,
    psalm_response: Optional[str] = None,
    gospel_acclamation: Optional[str] = None,
    gloria_required: bool = True,
    creed_required: bool = True,
    notes: Optional[str] = None,
) -> LiturgicalCalendar:
    """Create or update the liturgical calendar entry for a date."""
    with get_session() as session:
        entry = session.scalar(
            select(LiturgicalCalendar).where(LiturgicalCalendar.date == mass_date)
        )
        if entry is None:
            entry = LiturgicalCalendar(date=mass_date)
            session.add(entry)

        entry.season = season
        entry.feast_name = feast_name
        entry.psalm = psalm
        entry.psalm_response = psalm_response
        entry.gospel_acclamation = gospel_acclamation
        entry.gloria_required = gloria_required
        entry.creed_required = creed_required
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




