"""
In-app presentation control via PowerPoint COM automation (Windows only,
requires PowerPoint to be installed and pywin32: `pip install pywin32`).

Instead of copying slides into a new .pptx file, this opens the master
hymnal directly in PowerPoint and runs a slideshow restricted to the
exact ordered list of slide numbers from the current Mass plan - so it
always reflects the live master file, in the exact order you arranged
on the Planner page, including any real transitions/animations.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

CUSTOM_SHOW_NAME = "MissaFlowShow"

# PowerPoint COM constants (from the PpSlideShowRangeType enum) -
# not exposed as Python constants by win32com, so defined here directly.
PP_SHOW_NAMED_SLIDE_SHOW = 3

_app = None
_presentation = None


def _get_com_app():
    """Lazily import and start (or reuse) the PowerPoint COM application."""
    global _app
    try:
        import win32com.client
    except ImportError as exc:
        raise RuntimeError(
            "pywin32 is required for in-app presentation. Install it with: "
            "pip install pywin32"
        ) from exc

    if _app is None:
        _app = win32com.client.Dispatch("PowerPoint.Application")
        _app.Visible = True
    return _app


def build_slide_indices_from_mass_items(mass_items: list) -> list[int]:
    """
    Expand each MassItem's linked hymn start_slide/end_slide into an
    explicit, ordered list of individual slide numbers (1-indexed) -
    this is what PowerPoint's NamedSlideShows.Add() needs.
    """
    indices: list[int] = []
    for item in mass_items:
        hymn = getattr(item, "hymn", None)
        if hymn and hymn.start_slide and hymn.end_slide:
            indices.extend(range(hymn.start_slide, hymn.end_slide + 1))
    return indices


def present(master_pptx_path: str, slide_indices: list[int]) -> None:
    """
    Open the master presentation and run a slideshow restricted to
    slide_indices, in that exact order. Blocks nothing - PowerPoint runs
    the slideshow in its own window; call stop_presentation() to end it.
    """
    global _presentation

    if not slide_indices:
        raise ValueError("No slides to present - assign hymns to at least one slot first.")

    # PowerPoint's COM Presentations.Open() does NOT reliably resolve
    # relative paths the way Python does - it uses PowerPoint's own
    # working directory, not the script's, so a relative path here
    # (e.g. "assets/hymnal.pptx") can fail with a cryptic
    # "file not found" COM error even though the file exists. Always
    # resolve to an absolute path first.
    abs_path = os.path.abspath(master_pptx_path)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(
            f"Master PowerPoint not found at: {abs_path}\n"
            f"Check the 'Master PowerPoint' path in Settings."
        )

    app = _get_com_app()
    presentation = app.Presentations.Open(abs_path, WithWindow=True)
    _presentation = presentation

    # IMPORTANT: NamedSlideShows.Add() takes each slide's permanent SlideID,
    # NOT its position/index in the deck. These are different things - a
    # slide's position can change if slides are reordered, but its SlideID
    # never does. Passing positions directly (as if they were IDs) causes
    # PowerPoint to silently show the wrong slides. Convert first.
    slide_ids = []
    for position in slide_indices:
        try:
            slide_ids.append(presentation.Slides(position).SlideID)
        except Exception as exc:
            raise ValueError(
                f"Slide position {position} does not exist in this presentation "
                f"(it only has {presentation.Slides.Count} slides) - the imported "
                f"start_slide/end_slide values may be stale. Re-run import_hymns.py."
            ) from exc

    # Remove any previous custom show with the same name before re-adding,
    # so re-running Present after changing the order doesn't stack up
    # stale named shows inside the same PowerPoint file.
    named_shows = presentation.SlideShowSettings.NamedSlideShows
    for i in range(named_shows.Count, 0, -1):
        if named_shows.Item(i).Name == CUSTOM_SHOW_NAME:
            named_shows.Item(i).Delete()

    named_shows.Add(CUSTOM_SHOW_NAME, slide_ids)

    settings = presentation.SlideShowSettings
    settings.RangeType = PP_SHOW_NAMED_SLIDE_SHOW
    settings.SlideShowName = CUSTOM_SHOW_NAME

    logger.info("Starting presentation with %s slides: %s", len(slide_indices), slide_indices)
    settings.Run()


def stop_presentation() -> None:
    """Exit the running slideshow and close the presentation, if one is open."""
    global _presentation
    if _presentation is None:
        return
    try:
        if _presentation.SlideShowWindow is not None:
            _presentation.SlideShowWindow.View.Exit()
    except Exception:
        logger.exception("Error exiting slideshow view")
    try:
        _presentation.Close()
    except Exception:
        logger.exception("Error closing presentation")
    _presentation = None


def is_presenting() -> bool:
    return _presentation is not None