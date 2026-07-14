"""
Hymn Search dialog.

Opened from the Mass Planner (to pick a hymn for a slot) or from the
sidebar's Hymn Search page. Updates results as the user types, with a
category filter, favorites toggle, and hymn preview panel.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database.models import Hymn
from services import hymn_service


class SearchDialog(QDialog):
    """Modal dialog for finding and selecting a hymn."""

    def __init__(self, parent: Optional[QWidget] = None, title: str = "Search Hymns"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(720, 480)
        self.selected_hymn: Optional[Hymn] = None
        self._results: list[Hymn] = []

        self._build_ui()
        self._load_categories()
        self._run_search()

    # -- UI construction -----------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        # Search bar row
        search_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by hymn number, title, or keyword...")
        self.search_box.textChanged.connect(self._run_search)

        self.category_combo = QComboBox()
        self.category_combo.addItem("All categories", None)
        self.category_combo.currentIndexChanged.connect(self._run_search)

        self.favorites_button = QPushButton("★ Favorites")
        self.favorites_button.setCheckable(True)
        self.favorites_button.toggled.connect(self._run_search)

        search_row.addWidget(self.search_box, 4)
        search_row.addWidget(self.category_combo, 2)
        search_row.addWidget(self.favorites_button, 1)
        root.addLayout(search_row)

        # Results + preview split
        content_row = QHBoxLayout()

        self.results_list = QListWidget()
        self.results_list.currentItemChanged.connect(self._show_preview)
        self.results_list.itemDoubleClicked.connect(self._accept_selection)
        content_row.addWidget(self.results_list, 2)

        preview_col = QVBoxLayout()
        self.preview_title = QLabel("Select a hymn to preview")
        self.preview_title.setObjectName("PreviewTitle")
        self.preview_meta = QLabel("")
        self.preview_meta.setObjectName("PreviewMeta")
        self.preview_lyrics = QTextEdit()
        self.preview_lyrics.setReadOnly(True)

        preview_col.addWidget(self.preview_title)
        preview_col.addWidget(self.preview_meta)
        preview_col.addWidget(self.preview_lyrics, 1)
        content_row.addLayout(preview_col, 3)

        root.addLayout(content_row, 1)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept_selection)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _load_categories(self) -> None:
        for cat in hymn_service.get_categories():
            self.category_combo.addItem(cat, cat)

    # -- Behavior ---------------------------------------------------------

    def _run_search(self) -> None:
        query = self.search_box.text()
        category = self.category_combo.currentData()

        if self.favorites_button.isChecked():
            results = hymn_service.get_favorites()
            if query.strip():
                q = query.lower()
                results = [
                    h for h in results
                    if q in (h.title or "").lower() or q == (h.hymn_number or "")
                ]
        else:
            results = hymn_service.search_hymns(query=query, category=category)

        self._results = results
        self.results_list.clear()
        for hymn in results:
            label = f"#{hymn.hymn_number or '—'}   {hymn.title}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, hymn.id)
            self.results_list.addItem(item)

        if results:
            self.results_list.setCurrentRow(0)

    def _show_preview(self, current: Optional[QListWidgetItem], _previous=None) -> None:
        if current is None:
            return
        hymn_id = current.data(Qt.UserRole)
        hymn = next((h for h in self._results if h.id == hymn_id), None)
        if not hymn:
            return
        self.preview_title.setText(f"#{hymn.hymn_number or '—'}  {hymn.title}")
        meta_parts = [p for p in [hymn.category, hymn.language] if p]
        slide_info = ""
        if hymn.start_slide and hymn.end_slide:
            slide_info = f"  ·  Slides {hymn.start_slide}-{hymn.end_slide}"
        self.preview_meta.setText("  ·  ".join(meta_parts) + slide_info)
        self.preview_lyrics.setPlainText(hymn.lyrics or "(no lyrics stored)")

    def _accept_selection(self, *_args) -> None:
        current = self.results_list.currentItem()
        if current is None:
            return
        hymn_id = current.data(Qt.UserRole)
        self.selected_hymn = next((h for h in self._results if h.id == hymn_id), None)
        if self.selected_hymn:
            hymn_service.log_search(self.search_box.text())
            self.accept()

    def get_selected_hymn(self) -> Optional[Hymn]:
        return self.selected_hymn
