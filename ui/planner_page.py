"""
Mass Planner page.

Lets the user pick a Mass date (auto-populating liturgical fields),
assign a celebrant, select hymns for every slot via the search dialog,
reorder the resulting cards by drag-and-drop, and generate the final
PowerPoint presentation.
"""
from __future__ import annotations

import datetime
import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database.models import MASS_SLOT_TYPES
from services import calendar_service, hymn_service, mass_plan_service, ppt_service, settings_service
from ui.search_dialog import SearchDialog
from ui.widgets.hymn_card import SLOT_LABELS, HymnCard

logger = logging.getLogger(__name__)


class PlannerPage(QWidget):
    """The Mass Planner page, embedded in MainWindow's central stack."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_plan_id: Optional[int] = None
        self._build_ui()
        self._populate_slots()
        self._on_date_changed()

    # -- UI construction -----------------------------------------------

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)

        # Left column: Mass details form
        left = QVBoxLayout()
        form = QFormLayout()

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(datetime.date.today())
        self.date_edit.dateChanged.connect(self._on_date_changed)

        self.time_edit = QLineEdit()
        self.time_edit.setPlaceholderText("e.g. 10:00 AM")

        self.celebrant_edit = QLineEdit()
        self.celebrant_edit.setPlaceholderText("Celebrant name")

        self.season_label = QLabel("—")
        self.psalm_label = QLabel("—")
        self.gospel_accl_label = QLabel("—")

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notes for this Mass...")
        self.notes_edit.setMaximumHeight(100)

        form.addRow("Date:", self.date_edit)
        form.addRow("Time:", self.time_edit)
        form.addRow("Celebrant:", self.celebrant_edit)
        form.addRow("Liturgical Season:", self.season_label)
        form.addRow("Psalm:", self.psalm_label)
        form.addRow("Gospel Acclamation:", self.gospel_accl_label)
        form.addRow("Notes:", self.notes_edit)

        left.addLayout(form)

        button_row = QHBoxLayout()
        self.save_button = QPushButton("Save Mass Plan")
        self.save_button.clicked.connect(self._save_plan)
        self.generate_button = QPushButton("Generate Presentation")
        self.generate_button.setObjectName("PrimaryButton")
        self.generate_button.clicked.connect(self._generate_presentation)
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.generate_button)
        left.addLayout(button_row)
        left.addStretch()

        root.addLayout(left, 2)

        # Right column: draggable order list
        right = QVBoxLayout()
        right.addWidget(QLabel("Mass Order (drag to reorder)"))

        self.order_list = QListWidget()
        self.order_list.setDragDropMode(QListWidget.InternalMove)
        self.order_list.setSelectionMode(QListWidget.NoSelection)
        right.addWidget(self.order_list, 1)

        root.addLayout(right, 3)

    def _populate_slots(self) -> None:
        """Create one draggable card per fixed Mass slot type."""
        self.order_list.clear()
        self._cards: dict[str, HymnCard] = {}
        for slot_type in MASS_SLOT_TYPES:
            self._add_card(slot_type)

    def _add_card(self, slot_type: str) -> None:
        card = HymnCard(slot_type)
        card.search_requested.connect(self._open_search_for_slot)
        card.remove_requested.connect(self._clear_slot)

        item = QListWidgetItem(self.order_list)
        item.setSizeHint(card.sizeHint())
        self.order_list.addItem(item)
        self.order_list.setItemWidget(item, card)
        self._cards[slot_type] = card

    # -- Behavior -----------------------------------------------------

    def _on_date_changed(self) -> None:
        mass_date = self.date_edit.date().toPython()
        entry = calendar_service.get_by_date(mass_date)
        if entry:
            self.season_label.setText(entry.season)
            self.psalm_label.setText(entry.psalm or "—")
            self.gospel_accl_label.setText(entry.gospel_acclamation or "—")
        else:
            self.season_label.setText("(no calendar entry - add one in Settings/sample data)")
            self.psalm_label.setText("—")
            self.gospel_accl_label.setText("—")

    def _open_search_for_slot(self, slot_type: str) -> None:
        dialog = SearchDialog(self, title=f"Select hymn for: {SLOT_LABELS.get(slot_type, slot_type)}")
        if dialog.exec() == SearchDialog.Accepted:
            hymn = dialog.get_selected_hymn()
            if hymn:
                self._cards[slot_type].set_hymn(hymn.id, f"#{hymn.hymn_number or '—'}  {hymn.title}")

    def _clear_slot(self, slot_type: str) -> None:
        self._cards[slot_type].set_hymn(None, None)

    def _collect_items(self) -> list[dict]:
        """Read the current order_list (post drag-and-drop) into MassItem dicts."""
        items = []
        for seq in range(self.order_list.count()):
            list_item = self.order_list.item(seq)
            card: HymnCard = self.order_list.itemWidget(list_item)
            items.append({
                "slot_type": card.slot_type,
                "sequence_number": seq,
                "hymn_id": card.hymn_id,
                "text_override": None,
            })
        return items

    def _save_plan(self) -> Optional[int]:
        mass_date = self.date_edit.date().toPython()
        entry = calendar_service.get_by_date(mass_date)

        if self.current_plan_id is None:
            plan = mass_plan_service.create_mass_plan(
                mass_date=mass_date,
                time=self.time_edit.text().strip() or None,
                celebrant=self.celebrant_edit.text().strip() or None,
                notes=self.notes_edit.toPlainText().strip() or None,
                liturgical_calendar_id=entry.id if entry else None,
            )
            self.current_plan_id = plan.id
        else:
            plan = mass_plan_service.get_mass_plan(self.current_plan_id)

        mass_plan_service.save_mass_items(self.current_plan_id, self._collect_items())
        QMessageBox.information(self, "Saved", "Mass plan saved.")
        return self.current_plan_id

    def load_plan(self, plan_id: int) -> None:
        """Load an existing MassPlan (from History) into the form."""
        plan = mass_plan_service.get_mass_plan(plan_id)
        if not plan:
            return
        self.current_plan_id = plan.id
        self.date_edit.setDate(plan.date)
        self.time_edit.setText(plan.time or "")
        self.celebrant_edit.setText(plan.celebrant or "")
        self.notes_edit.setPlainText(plan.notes or "")

        self._populate_slots()
        for item in plan.items:
            if item.slot_type in self._cards and item.hymn:
                hymn = item.hymn
                self._cards[item.slot_type].set_hymn(
                    hymn.id, f"#{hymn.hymn_number or '—'}  {hymn.title}"
                )

    def _generate_presentation(self) -> None:
        plan_id = self._save_plan()
        if not plan_id:
            return

        plan = mass_plan_service.get_mass_plan(plan_id)
        slide_ranges = ppt_service.build_slide_ranges_from_mass_items(plan.items)

        if not slide_ranges:
            QMessageBox.warning(
                self, "Nothing to generate",
                "No selected hymns have slide ranges. Assign hymns to at least one slot first."
            )
            return

        master_path = settings_service.get_setting("master_pptx_path")
        output_dir = settings_service.get_setting("presentation_folder")

        try:
            output_path = ppt_service.generate_presentation(
                master_pptx_path=master_path,
                slide_ranges=slide_ranges,
                mass_date=plan.date,
                output_dir=output_dir,
            )
        except Exception as exc:
            logger.exception("Presentation generation failed")
            QMessageBox.critical(self, "Generation failed", str(exc))
            return

        mass_plan_service.set_generated_presentation_path(plan_id, output_path)
        QMessageBox.information(self, "Presentation generated", f"Saved to:\n{output_path}")
