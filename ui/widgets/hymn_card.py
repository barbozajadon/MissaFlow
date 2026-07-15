"""
HymnCard - a draggable card widget representing one slot (entrance hymn,
gloria, communion hymn, etc.) in the Mass Planner's ordered list.

Used as the item widget inside a QListWidget configured for
InternalMove drag-and-drop (see ui/planner_page.py), so the visual card
you see is this widget, while the QListWidget itself handles reordering.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal , Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

SLOT_LABELS = {
    "entrance_hymn": "Entrance Hymn",
    "penitential_rite": "Penitential Rite",
    "gloria": "Gloria",
    "responsorial_psalm": "Responsorial Psalm",
    "creed": "Creed",
    "gospel_acclamation": "Gospel Acclamation",
    "offertory_hymn": "Offertory Hymn",
    "holy": "Holy",
    "proclaimation": "Proclaimation",
    "great_amen": "Great Amen",
    "lamb_of_god": "Lamb of God",
    "communion_hymn": "Communion Hymn",
    "meditation_hymn": "Meditation Hymn",
    "recessional_hymn": "Recessional Hymn",
}


class HymnCard(QWidget):
    """A single draggable card shown in the Mass order list."""

    search_requested = Signal(str)   # emits slot_type
    remove_requested = Signal(str)   # emits slot_type

    def __init__(self, slot_type: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.slot_type = slot_type
        self.hymn_id: Optional[int] = None
        self.hymn_title: Optional[str] = None

        self.setObjectName("HymnCard")
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 8, 12, 8)
        outer.setSpacing(2)

        row = QHBoxLayout()

        self.slot_label = QLabel(SLOT_LABELS.get(self.slot_type, self.slot_type))
        self.slot_label.setObjectName("SlotLabel")
        self.slot_label.setAlignment(Qt.AlignCenter)

        self.hymn_label = QLabel("not selected")
        self.hymn_label.setAlignment(Qt.AlignCenter)
        self.hymn_label.setObjectName("HymnLabel")

        self.select_button = QPushButton("Select")
        self.select_button.setObjectName("SelectButton")
        self.select_button.clicked.connect(
            lambda: self.search_requested.emit(self.slot_type)
        )

        self.remove_button = QPushButton("❌")
        self.remove_button.setStyleSheet("font-family : Segoe UI emoji;")
        self.remove_button.setObjectName("RemoveButton")
        self.remove_button.clicked.connect(
            lambda: self.remove_requested.emit(self.slot_type)
        )

        row.addWidget(self.slot_label, 2)
        row.addWidget(self.hymn_label, 3)
        row.addWidget(self.select_button)
        row.addWidget(self.remove_button)

        outer.addLayout(row)

    def set_hymn(self, hymn_id: Optional[int], title: Optional[str]) -> None:
        self.hymn_id = hymn_id
        self.hymn_title = title
        self.hymn_label.setText(title if title else "— not selected —")
