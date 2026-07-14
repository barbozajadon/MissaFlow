"""
Search orchestration for the Hymn Search dialog/page.

Wraps hymn_service's raw search with recent-search logging and a
convenience method for the dialog's "default" view (favorites + recents)
before the user has typed anything.
"""
from __future__ import annotations

import logging
from typing import Optional

from database.models import Hymn
from services import hymn_service

logger = logging.getLogger(__name__)


def search(
    query: str = "",
    category: Optional[str] = None,
    language: Optional[str] = None,
    log_history: bool = True,
) -> list[Hymn]:
    """Search hymns and optionally log the query to recent searches."""
    results = hymn_service.search_hymns(query=query, category=category, language=language)
    if log_history and query.strip():
        hymn_service.log_search(query.strip())
    return results


def default_view() -> dict[str, list]:
    """
    What to show in the search dialog before the user types anything:
    favorites first, then recent search terms for quick re-run.
    """
    return {
        "favorites": hymn_service.get_favorites(),
        "recent_searches": hymn_service.get_recent_searches(),
    }
