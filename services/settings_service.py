"""
Simple key/value settings store, backed by the Setting table.

Not listed explicitly in the original services/ spec, but the Settings
page needs somewhere to persist church name, default paths, theme, etc.,
so it lives alongside the other services rather than mixed into the UI.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from database.database import get_session
from database.models import Setting

DEFAULTS = {
    "church_name": "Church Name",
    "presentation_folder": "generated_presentations",
    "master_pptx_path": "assets/master_hymnal.pptx",
    "theme": "dark",
    "backup_location": "backups",
    "default_language": "English",
}


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    with get_session() as session:
        row = session.scalar(select(Setting).where(Setting.key == key))
        if row is not None:
            return row.value
        return default if default is not None else DEFAULTS.get(key)


def set_setting(key: str, value: str) -> None:
    with get_session() as session:
        row = session.scalar(select(Setting).where(Setting.key == key))
        if row is None:
            row = Setting(key=key, value=value)
            session.add(row)
        else:
            row.value = value
        session.commit()


def get_all_settings() -> dict[str, str]:
    result = dict(DEFAULTS)
    with get_session() as session:
        rows = session.scalars(select(Setting)).all()
        for row in rows:
            result[row.key] = row.value
    return result
