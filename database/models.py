"""
SQLAlchemy ORM models for the Church Hymn Planner.

Tables:
    Hymn                - every hymn/song in the master hymnal PPTX
    LiturgicalCalendar   - one row per Mass date (season, psalm, etc.)
    MassPlan             - one row per planned Mass (date, celebrant, notes...)
    MassItem             - individual hymn/mass-part slots within a MassPlan
    Setting              - single-row app configuration (church name, paths, theme...)
    Favorite             - hymns marked as favorites for quick access
    RecentSearch         - search history for the search dialog
"""
from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


class Hymn(Base):
    """
    A single hymn or slide-based item (hymn, psalm response, Gloria, etc.)
    sourced from a PPTX file. Despite the name, this table now holds any
    slide-based content, distinguished by `category` (e.g. 'hymn',
    'psalm_response', 'gloria', 'holy', 'gospel_acclamation') - reusing
    the same search/select/present machinery for all of them.
    """

    __tablename__ = "hymns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hymn_number: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    lyrics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="English")
    tags: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # comma-separated
    source_file: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # Path to the PPTX this entry's slides live in. NULL means "the
    # default master hymnal" (see settings_service master_pptx_path) -
    # this keeps every existing hymn row valid without a migration.
    start_slide: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_slide: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    favorites: Mapped[list["Favorite"]] = relationship(back_populates="hymn", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Hymn #{self.hymn_number} {self.title!r}>"


class LiturgicalCalendar(Base):
    """Liturgical data for a specific Mass date - drives auto-population."""

    __tablename__ = "liturgical_calendar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, unique=True, index=True)
    season: Mapped[str] = mapped_column(String(100), nullable=False)
    feast_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    psalm: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    psalm_response: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    psalm_response_hymn_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("hymns.id", ondelete="SET NULL"), nullable=True
    )
    # Points at the Hymn row (category='psalm_response') holding this
    # date's actual projectable slide, so the Planner can auto-fill the
    # slot with a real slide, not just display text.
    gospel_acclamation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gloria_required: Mapped[bool] = mapped_column(Boolean, default=True)
    creed_required: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    psalm_response_hymn: Mapped[Optional["Hymn"]] = relationship()

    psalm_response_hymn_id: Mapped[Optional[int]] = mapped_column(
    ForeignKey("hymns.id", ondelete="SET NULL"),
    nullable=True
)


class MassPlan(Base):
    """A single planned Mass - the container for all its MassItems."""

    __tablename__ = "mass_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "10:00 AM"
    celebrant: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    liturgical_calendar_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("liturgical_calendar.id", ondelete="SET NULL"), nullable=True
    )
    generated_presentation_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    liturgical_calendar: Mapped[Optional["LiturgicalCalendar"]] = relationship()
    items: Mapped[list["MassItem"]] = relationship(
        back_populates="mass_plan", cascade="all, delete-orphan", order_by="MassItem.sequence_number"
    )

    def __repr__(self) -> str:
        return f"<MassPlan {self.date}>"


# Fixed slot types for a Mass, matching the spec's field list.
DEFAULT_MASS_SLOTS = [
    "entrance_hymn",
    "penitential_rite",
    "psalm_response",
    "offertory_hymn",
    "communion_hymn",
    "recessional_hymn",
]

OPTIONAL_MASS_SLOTS = [
    "gloria",
    "psalm_response",
    "gospel_acclamation",
    "holy",
    "proclaimation",
    "great_amen",
    "lamb_of_god",
    "meditation_hymn",
]

class MassItem(Base):
    """One slot (entrance, gloria, communion, etc.) within a MassPlan."""

    __tablename__ = "mass_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mass_plan_id: Mapped[int] = mapped_column(
        ForeignKey("mass_plans.id", ondelete="CASCADE"), nullable=False
    )
    slot_type: Mapped[str] = mapped_column(String(50), nullable=False)  # see MASS_SLOT_TYPES
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hymn_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("hymns.id", ondelete="SET NULL"), nullable=True
    )
    text_override: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # for fixed parts like "Holy" that aren't hymns

    mass_plan: Mapped["MassPlan"] = relationship(back_populates="items")
    hymn: Mapped[Optional["Hymn"]] = relationship()

    def __repr__(self) -> str:
        return f"<MassItem {self.slot_type} seq={self.sequence_number}>"


class Setting(Base):
    """Single-row (or key/value) application settings."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class Favorite(Base):
    """A hymn marked as a favorite for quick access in the search dialog."""

    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("hymn_id", name="uq_favorite_hymn"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hymn_id: Mapped[int] = mapped_column(ForeignKey("hymns.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    hymn: Mapped["Hymn"] = relationship(back_populates="favorites")


class RecentSearch(Base):
    """Search history, most recent first, for the search dialog's suggestions."""

    __tablename__ = "recent_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    searched_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
