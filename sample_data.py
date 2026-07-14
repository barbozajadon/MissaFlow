"""
Populates the database with sample hymns and liturgical calendar entries
so the app has something to show on first run.

Run with:
    python sample_data.py

Safe to re-run - it only inserts hymns/dates that don't already exist.
"""
from __future__ import annotations

import datetime

from database.database import get_session, init_db
from database.models import Hymn, LiturgicalCalendar

SAMPLE_HYMNS = [
    # (number, title, category, language, start_slide, end_slide)
    ("142", "Amazing Grace", "General", "English", 3, 5),
    ("201", "Here I Am, Lord", "Entrance", "English", 6, 8),
    ("315", "Gift of Finest Wheat", "Communion", "English", 9, 12),
    ("87", "Go Make a Difference", "Recessional", "English", 13, 15),
    ("54", "Be Not Afraid", "General", "English", 16, 18),
    ("233", "On Eagle's Wings", "General", "English", 19, 22),
    ("6", "Table of Plenty", "Communion", "English", 23, 25),
    ("178", "Sing a New Song", "Entrance", "English", 26, 27),
]

SAMPLE_CALENDAR = [
    # (date offset in days from today, season, feast, psalm, psalm_response, gospel_acclamation)
    (0, "Ordinary Time", None, "Psalm 34", "Taste and see the goodness of the Lord.", "Alleluia, alleluia."),
    (7, "Ordinary Time", None, "Psalm 63", "My soul is thirsting for you, O Lord my God.", "Alleluia, alleluia."),
    (14, "Ordinary Time", None, "Psalm 145", "The Lord is close to all who call him.", "Alleluia, alleluia."),
]


def load_sample_hymns() -> None:
    with get_session() as session:
        existing_numbers = {h.hymn_number for h in session.query(Hymn).all()}
        added = 0
        for number, title, category, language, start, end in SAMPLE_HYMNS:
            if number in existing_numbers:
                continue
            session.add(Hymn(
                hymn_number=number,
                title=title,
                lyrics=f"(Sample lyrics placeholder for {title} - replace by extracting "
                       f"from your actual master_hymnal.pptx)",
                category=category,
                language=language,
                start_slide=start,
                end_slide=end,
            ))
            added += 1
        session.commit()
        print(f"Added {added} sample hymns.")


def load_sample_calendar() -> None:
    today = datetime.date.today()
    with get_session() as session:
        existing_dates = {c.date for c in session.query(LiturgicalCalendar).all()}
        added = 0
        for offset, season, feast, psalm, response, acclamation in SAMPLE_CALENDAR:
            mass_date = today + datetime.timedelta(days=offset)
            if mass_date in existing_dates:
                continue
            session.add(LiturgicalCalendar(
                date=mass_date,
                season=season,
                feast_name=feast,
                psalm=psalm,
                psalm_response=response,
                gospel_acclamation=acclamation,
                gloria_required=True,
                creed_required=True,
            ))
            added += 1
        session.commit()
        print(f"Added {added} sample liturgical calendar entries.")


if __name__ == "__main__":
    init_db()
    load_sample_hymns()
    load_sample_calendar()
    print("Sample data load complete.")
