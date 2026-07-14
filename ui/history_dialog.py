"""
History dialog - browse, open, duplicate, or delete past Mass plans.
"""
from __future__ import annotations

import datetime
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from services import mass_plan_service


class HistoryDialog(QDialog):
    """Modal dialog listing all saved Mass plans with quick actions."""

    def __init__(self, parent=None, on_open: Optional[Callable[[int], None]] = None):
        super().__init__(parent)
        self.setWindowTitle("Mass History")
        self.resize(600, 500)
        self._on_open = on_open
        self._plans = []
        self._build_ui()
        self._load_plans()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by date (YYYY-MM-DD)...")
        self.search_box.textChanged.connect(self._filter_plans)
        root.addWidget(self.search_box)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._open_selected)
        root.addWidget(self.list_widget, 1)

        button_row = QHBoxLayout()
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self._open_selected)
        duplicate_btn = QPushButton("Duplicate")
        duplicate_btn.clicked.connect(self._duplicate_selected)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_selected)

        button_row.addWidget(open_btn)
        button_row.addWidget(duplicate_btn)
        button_row.addWidget(delete_btn)
        root.addLayout(button_row)

    def _load_plans(self) -> None:
        self._plans = mass_plan_service.get_all_mass_plans()
        self._render_list(self._plans)

    def _render_list(self, plans) -> None:
        self.list_widget.clear()
        for plan in plans:
            label = f"{plan.date.strftime('%Y-%m-%d')}"
            if plan.celebrant:
                label += f"  ·  {plan.celebrant}"
            if plan.time:
                label += f"  ·  {plan.time}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, plan.id)
            self.list_widget.addItem(item)

    def _filter_plans(self, text: str) -> None:
        text = text.strip()
        if not text:
            self._render_list(self._plans)
            return
        filtered = [p for p in self._plans if text in p.date.strftime("%Y-%m-%d")]
        self._render_list(filtered)

    def _current_plan_id(self) -> Optional[int]:
        item = self.list_widget.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _open_selected(self, *_args) -> None:
        plan_id = self._current_plan_id()
        if plan_id is None:
            return
        if self._on_open:
            self._on_open(plan_id)
        self.accept()

    def _duplicate_selected(self) -> None:
        plan_id = self._current_plan_id()
        if plan_id is None:
            return

        date_str, ok = QInputDialog.getText(
            self, "Duplicate Mass Plan", "New Mass date (YYYY-MM-DD):",
            text=datetime.date.today().isoformat(),
        )
        if not ok or not date_str.strip():
            return

        try:
            new_date = datetime.date.fromisoformat(date_str.strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid date", "Please enter a date as YYYY-MM-DD.")
            return

        mass_plan_service.duplicate_mass_plan(plan_id, new_date)
        self._load_plans()

    def _delete_selected(self) -> None:
        plan_id = self._current_plan_id()
        if plan_id is None:
            return
        confirm = QMessageBox.question(
            self, "Delete Mass Plan", "Delete this Mass plan permanently?"
        )
        if confirm == QMessageBox.Yes:
            mass_plan_service.delete_mass_plan(plan_id)
            self._load_plans()
