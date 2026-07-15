"""
Dashboard page - the app's landing page.

Shows today's date, the current liturgical season, the next scheduled
Mass, and the last generated presentation, with quick-action buttons.
"""
from __future__ import annotations

import datetime
from typing import Callable, Optional

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services import calendar_service, mass_plan_service


class DashboardPage(QWidget):
    """Landing page with an at-a-glance summary and quick actions."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        on_new_mass: Optional[Callable[[], None]] = None,
        on_open_previous: Optional[Callable[[], None]] = None,
        on_generate: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self._on_new_mass = on_new_mass
        self._on_open_previous = on_open_previous
        self._on_generate = on_generate
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        title = QLabel("Dashboard")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        self.date_label = QLabel()
        self.season_label = QLabel()
        self.next_mass_label = QLabel()
        self.last_generated_label = QLabel()

        for label in (self.date_label, self.season_label, self.next_mass_label, self.last_generated_label):
            label.setObjectName("DashboardStat")
            root.addWidget(label)

        button_row = QHBoxLayout()
        new_mass_btn = QPushButton("New Mass")
        new_mass_btn.clicked.connect(lambda: self._on_new_mass and self._on_new_mass())
        open_prev_btn = QPushButton("Open Previous")
        open_prev_btn.clicked.connect(lambda: self._on_open_previous and self._on_open_previous())
        generate_btn = QPushButton("Present on Screen")
        generate_btn.setObjectName("PrimaryButton")
        generate_btn.clicked.connect(lambda: self._on_generate and self._on_generate())

        button_row.addWidget(new_mass_btn)
        button_row.addWidget(open_prev_btn)
        button_row.addWidget(generate_btn)
        root.addLayout(button_row)
        root.addStretch()

    def refresh(self) -> None:
        today = datetime.date.today()
        self.date_label.setText(f"Today: {today.strftime('%A, %B %d, %Y')}")
        self.season_label.setText(f"Liturgical season: {calendar_service.get_current_season(today)}")

        next_mass = mass_plan_service.get_next_scheduled_mass()
        if next_mass:
            self.next_mass_label.setText(
                f"Next scheduled Mass: {next_mass.date.strftime('%A, %B %d, %Y')}"
                + (f" at {next_mass.time}" if next_mass.time else "")
            )
        else:
            self.next_mass_label.setText("Next scheduled Mass: none planned yet")

        # Presentations now run in-app via PowerPoint COM (see present_service.py)
        # rather than being exported to a file, so there's no file path to show
        # here anymore - this label is left as a placeholder for a future
        # "last presented on" timestamp if that's ever tracked.
        self.last_generated_label.setText("")
