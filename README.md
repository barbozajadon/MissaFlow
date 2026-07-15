# Church Hymn Planner

A desktop app for a parish music ministry to plan the hymns and Mass parts
for each Mass, and generate the final projection PowerPoint automatically
from an existing master hymnal deck.

## Setup

```bash
cd church_hymn_planner
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

1. Put your existing hymn PowerPoint at `assets/master_hymnal.pptx`
   (or point Settings → Master PowerPoint at wherever it lives).
2. Populate the database:
   ```bash
   python sample_data.py
   ```
   This adds a handful of **placeholder** sample hymns and three sample
   liturgical calendar dates just so the app isn't empty on first run.
   Replace them with your real hymn data (see "Loading your real hymns" below).
3. Run the app:
   ```bash
   python app.py
   ```

## Loading your real hymns

Each `Hymn` row needs `start_slide`/`end_slide` pointing at that hymn's
slide range **inside your actual `master_hymnal.pptx`**, since that's what
`services/ppt_service.py` copies from when generating a Mass presentation.

The sample data in `sample_data.py` is just a placeholder shape to show
you the fields - for your real hymnal, write a small one-off script (or
extend `sample_data.py`) that reads your PPTX with `python-pptx` and
inserts one `Hymn` row per hymn with its real `hymn_number`, `title`,
`lyrics`, and slide range. The exact parsing logic depends on how your
deck is laid out (e.g. an index of hyperlinked slides vs. numbered
headers on every slide) - happy to write that extraction script once
you confirm the layout.

## Project structure

```
church_hymn_planner/
├── app.py                     Entry point - initializes the DB and launches the UI
├── sample_data.py              One-off script to seed sample hymns/calendar dates
├── database/
│   ├── models.py                SQLAlchemy models: Hymn, MassPlan, MassItem,
│   │                             LiturgicalCalendar, Setting, Favorite, RecentSearch
│   └── database.py              Engine/session setup, init_db()
├── services/
│   ├── hymn_service.py          Hymn CRUD, search, favorites, recent searches
│   ├── calendar_service.py      Liturgical calendar lookup/auto-population
│   ├── search_service.py        Search dialog orchestration (wraps hymn_service)
│   ├── mass_plan_service.py     MassPlan/MassItem CRUD, duplication
│   ├── present_service.py       Runs the slideshow in-app via PowerPoint COM (primary path)
│   ├── ppt_service.py           (legacy) copies slide ranges into a new .pptx file - not
│   │                             called from the UI anymore, kept for optional file export
│   └── settings_service.py      Key/value app settings persistence
├── ui/
│   ├── main_window.py            Sidebar + page navigation
│   ├── dashboard_page.py         Landing page: today's status, quick actions
│   ├── search_page.py            Full hymn browser (sidebar page)
│   ├── search_dialog.py          Modal hymn picker (used from the Planner)
│   ├── planner_page.py           Mass Planner: fields, auto-fill, drag-and-drop order
│   ├── history_dialog.py         Browse/open/duplicate/delete past Mass plans
│   ├── settings_dialog.py        Church name, paths, theme, language
│   └── widgets/
│       └── hymn_card.py           Draggable card widget for one Mass slot
├── styles/
│   ├── dark.qss                  Dark theme (default)
│   └── light.qss                 Light theme
├── assets/
│   ├── icons/                     (add your own icon files here)
│   └── master_hymnal.pptx         Your existing hymn deck (you provide this)
├── generated_presentations/       Output folder for generated Mass .pptx files
└── database.db                    SQLite database (created automatically on first run)
```

## How presenting works

The app no longer exports a new .pptx file. Instead, **Present on Screen**
drives PowerPoint directly via COM automation (Windows + PowerPoint
required, `pywin32` package):

1. In the Mass Planner, assign a hymn to each slot (Entrance, Communion,
   Recessional, etc.) via the Search dialog, and reorder the cards by
   dragging them.
2. Click **Present on Screen**. The app opens `master_hymnal.pptx`
   directly in PowerPoint, builds a temporary Custom Show containing
   only your selected slides in your chosen order, and starts the
   slideshow - full fidelity, since it's the real file running in real
   PowerPoint, not a copy.
3. Click **Stop Presenting** to end the slideshow and close the file.
4. Fixed spoken/sung parts (Gloria, Holy, Psalm Response, etc.) currently
   populate from the Liturgical Calendar as text fields on the Planner
   page. If you also want those projected as slides, add them to
   `master_hymnal.pptx` as their own "hymn" entries with a slide range,
   the same way a regular hymn works.

`services/ppt_service.py` (the old file-export approach) is still in the
project but no longer called from the UI - kept in case you want a
downloadable/emailable copy of a Mass's slides in the future.

## What's implemented vs. stretch goals

**Implemented:** hymn CRUD/search, favorites, recent searches, liturgical
calendar auto-population with manual override, Mass Planner with
drag-and-drop ordering, PPTX generation from slide ranges, History
(open/duplicate/delete/search), Settings, dark/light theme.

**Not yet implemented** (flagged here rather than left silently missing):
undo/redo, auto-save, PDF export of the Mass sheet, print dialog, and
in-app slide preview before generation. These are straightforward to add
as new service/UI methods on top of the existing structure whenever
you're ready for them - just say the word.

## Notes on PPTX fidelity

`python-pptx` has no built-in "duplicate slide" operation, so
`ppt_service.py` copies each shape's XML and picture bytes individually.
This preserves text, formatting, and images reliably. Slide transitions
and animations live outside python-pptx's object model, so if your deck
uses custom transitions, spot-check the first generated file - see the
docstring at the top of `services/ppt_service.py` for details.
