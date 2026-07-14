"""
Hymn Search page - the sidebar's full-page hymn browser (as opposed to
search_dialog.py, which is the modal picker used from the Mass Planner).
Also where volunteers manage favorites and browse by category/language.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
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


class SearchPage(QWidget):
    """Full hymn search/browse page for the sidebar."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._results: list[Hymn] = []
        self._build_ui()
        self._load_categories()
        self._run_search()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        title = QLabel("Hymn Search")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        search_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by hymn number, title, or keyword...")
        self.search_box.textChanged.connect(self._run_search)

        self.category_combo = QComboBox()
        self.category_combo.addItem("All categories", None)
        self.category_combo.currentIndexChanged.connect(self._run_search)

        search_row.addWidget(self.search_box, 3)
        search_row.addWidget(self.category_combo, 1)
        root.addLayout(search_row)

        content_row = QHBoxLayout()
        self.results_list = QListWidget()
        self.results_list.currentItemChanged.connect(self._show_preview)
        content_row.addWidget(self.results_list, 2)

        preview_col = QVBoxLayout()
        self.preview_title = QLabel("Select a hymn to preview")
        self.preview_title.setObjectName("PreviewTitle")
        self.preview_meta = QLabel("")
        self.favorite_button = QPushButton("☆ Add to favorites")
        self.favorite_button.clicked.connect(self._toggle_favorite)
        self.preview_lyrics = QTextEdit()
        self.preview_lyrics.setReadOnly(True)

        preview_col.addWidget(self.preview_title)
        preview_col.addWidget(self.preview_meta)
        preview_col.addWidget(self.favorite_button)
        preview_col.addWidget(self.preview_lyrics, 1)
        content_row.addLayout(preview_col, 3)

        root.addLayout(content_row, 1)

    def _load_categories(self) -> None:
        self.category_combo.blockSignals(True)
        current = self.category_combo.currentData()
        self.category_combo.clear()
        self.category_combo.addItem("All categories", None)
        for cat in hymn_service.get_categories():
            self.category_combo.addItem(cat, cat)
        if current:
            idx = self.category_combo.findData(current)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
        self.category_combo.blockSignals(False)

    def _run_search(self) -> None:
        query = self.search_box.text()
        category = self.category_combo.currentData()
        self._results = hymn_service.search_hymns(query=query, category=category)

        self.results_list.clear()
        for hymn in self._results:
            item = QListWidgetItem(f"#{hymn.hymn_number or '—'}   {hymn.title}")
            item.setData(Qt.UserRole, hymn.id)
            self.results_list.addItem(item)

        if self._results:
            self.results_list.setCurrentRow(0)
        else:
            self.preview_title.setText("No results")
            self.preview_meta.setText("")
            self.preview_lyrics.clear()

    def _current_hymn(self) -> Optional[Hymn]:
        item = self.results_list.currentItem()
        if not item:
            return None
        hymn_id = item.data(Qt.UserRole)
        return next((h for h in self._results if h.id == hymn_id), None)

    def _show_preview(self, *_args) -> None:
        hymn = self._current_hymn()
        if not hymn:
            return
        self.preview_title.setText(f"#{hymn.hymn_number or '—'}  {hymn.title}")
        meta_parts = [p for p in [hymn.category, hymn.language] if p]
        slide_info = ""
        if hymn.start_slide and hymn.end_slide:
            slide_info = f"  ·  Slides {hymn.start_slide}-{hymn.end_slide}"
        self.preview_meta.setText("  ·  ".join(meta_parts) + slide_info)
        self.preview_lyrics.setPlainText(hymn.lyrics or "(no lyrics stored)")

        favorites_ids = {h.id for h in hymn_service.get_favorites()}
        self.favorite_button.setText(
            "★ In favorites" if hymn.id in favorites_ids else "☆ Add to favorites"
        )

    def _toggle_favorite(self) -> None:
        hymn = self._current_hymn()
        if not hymn:
            return
        is_favorite = hymn_service.toggle_favorite(hymn.id)
        self.favorite_button.setText("★ In favorites" if is_favorite else "☆ Add to favorites")
