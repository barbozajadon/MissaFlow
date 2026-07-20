"""
migrate_add_source_columns.py

One-time migration for databases created BEFORE the multi-source-file
presenting feature was added. Adds the two new columns directly via
SQL, without touching any existing rows:

    hymns.source_file                (TEXT, nullable)
    liturgical_calendar.psalm_response_hymn_id   (INTEGER, nullable)

Safe to run more than once - it checks whether each column already
exists before trying to add it.

USAGE
-----
    python migrate_add_source_columns.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "database.db"


def column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    existing_columns = {row[1] for row in cursor.fetchall()}
    return column in existing_columns


def migrate() -> None:
    if not DB_PATH.exists():
        print(f"No database found at {DB_PATH} - nothing to migrate. "
              f"(If this is a brand-new setup, just run the app normally - "
              f"init_db() will create the up-to-date schema from scratch.)")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    if not column_exists(cursor, "hymns", "source_file"):
        cursor.execute("ALTER TABLE hymns ADD COLUMN source_file VARCHAR(500)")
        print("Added hymns.source_file")
    else:
        print("hymns.source_file already exists - skipped")

    if not column_exists(cursor, "liturgical_calendar", "psalm_response_hymn_id"):
        cursor.execute(
            "ALTER TABLE liturgical_calendar ADD COLUMN psalm_response_hymn_id INTEGER "
            "REFERENCES hymns(id)"
        )
        print("Added liturgical_calendar.psalm_response_hymn_id")
    else:
        print("liturgical_calendar.psalm_response_hymn_id already exists - skipped")

    conn.commit()
    conn.close()
    print("\nMigration complete - your existing data was left untouched.")


if __name__ == "__main__":
    migrate()
