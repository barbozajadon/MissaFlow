"""
CRUD and duplication logic for MassPlan / MassItem.

Used by planner_page.py (create/edit/save a Mass) and history_dialog.py
(list, open, duplicate, delete past Mass plans).
"""
from __future__ import annotations

import datetime
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.database import get_session
from database.models import MassItem, MassPlan

logger = logging.getLogger(__name__)


def get_all_mass_plans() -> list[MassPlan]:
    with get_session() as session:
        stmt = (
            select(MassPlan)
            .options(selectinload(MassPlan.items).selectinload(MassItem.hymn))
            .order_by(MassPlan.date.desc())
        )
        return list(session.scalars(stmt).all())


def get_mass_plan(plan_id: int) -> Optional[MassPlan]:
    with get_session() as session:
        stmt = (
            select(MassPlan)
            .options(selectinload(MassPlan.items).selectinload(MassItem.hymn))
            .where(MassPlan.id == plan_id)
        )
        return session.scalar(stmt)


def get_next_scheduled_mass() -> Optional[MassPlan]:
    today = datetime.date.today()
    with get_session() as session:
        stmt = (
            select(MassPlan)
            .where(MassPlan.date >= today)
            .order_by(MassPlan.date)
            .limit(1)
        )
        return session.scalar(stmt)


def create_mass_plan(
    mass_date: datetime.date,
    time: Optional[str] = None,
    celebrant: Optional[str] = None,
    notes: Optional[str] = None,
    liturgical_calendar_id: Optional[int] = None,
) -> MassPlan:
    with get_session() as session:
        plan = MassPlan(
            date=mass_date,
            time=time,
            celebrant=celebrant,
            notes=notes,
            liturgical_calendar_id=liturgical_calendar_id,
        )
        session.add(plan)
        session.commit()
        session.refresh(plan)
        return plan


def save_mass_items(plan_id: int, items: list[dict]) -> None:
    """
    Replace all MassItems for a plan with the given ordered list of dicts:
        {"slot_type": str, "sequence_number": int, "hymn_id": int | None,
         "text_override": str | None}
    Called whenever the user reorders/saves the drag-and-drop list.
    """
    with get_session() as session:
        session.query(MassItem).filter(MassItem.mass_plan_id == plan_id).delete()
        for item in items:
            session.add(MassItem(mass_plan_id=plan_id, **item))
        session.commit()


def duplicate_mass_plan(plan_id: int, new_date: datetime.date) -> Optional[MassPlan]:
    """Duplicate a previous plan's items onto a new date (e.g. 'duplicate previous Sunday')."""
    with get_session() as session:
        source = session.get(MassPlan, plan_id)
        if not source:
            return None

        new_plan = MassPlan(
            date=new_date,
            time=source.time,
            celebrant=source.celebrant,
            notes=source.notes,
        )
        session.add(new_plan)
        session.flush()  # get new_plan.id before creating items

        for item in source.items:
            session.add(MassItem(
                mass_plan_id=new_plan.id,
                slot_type=item.slot_type,
                sequence_number=item.sequence_number,
                hymn_id=item.hymn_id,
                text_override=item.text_override,
            ))

        session.commit()
        session.refresh(new_plan)
        return new_plan


def delete_mass_plan(plan_id: int) -> bool:
    with get_session() as session:
        plan = session.get(MassPlan, plan_id)
        if not plan:
            return False
        session.delete(plan)
        session.commit()
        return True


def set_generated_presentation_path(plan_id: int, path: str) -> None:
    with get_session() as session:
        plan = session.get(MassPlan, plan_id)
        if plan:
            plan.generated_presentation_path = path
            session.commit()
