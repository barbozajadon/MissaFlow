"""
Main application window: sidebar navigation + stacked pages.
"""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon , QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from services import settings_service
from ui.dashboard_page import DashboardPage
from ui.history_dialog import HistoryDialog
from ui.planner_page import PlannerPage
from ui.search_page import SearchPage
from ui.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)

PAGE_NAMES = ["Dashboard", "Hymn Search", "Mass Planner", "History", "Settings"]


class MainWindow(QMainWindow):
    """Top-level window: sidebar on the left, active page on the right."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MissaFlow")
        self.setWindowIcon(QIcon("assets/icons/app_icon.ico"))

        self.resize(1200, 780)

        self._build_ui()
        self._apply_theme(settings_service.get_setting("theme", "dark"))

    # -- UI construction -----------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)

        app_title = QLabel()
        pixmap = QPixmap("assets/icons/app_logo.png")   # Path to your image
        app_title.setPixmap(pixmap)
        sidebar_layout.addWidget(app_title)
        pixmap = QPixmap("assets/icons/app_logo.png")
        app_title.setPixmap(
        pixmap.scaled(
        180,          # width
        60,           # height
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )
)
        app_title.setAlignment(Qt.AlignCenter)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("NavList")
        for name in PAGE_NAMES:
            item = QListWidgetItem(name)
            item.setTextAlignment(Qt.AlignVCenter)
            self.nav_list.addItem(item)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        sidebar_layout.addWidget(self.nav_list, 1)

        sidebar.setFixedWidth(220)
        root.addWidget(sidebar)

        # Pages
        self.stack = QStackedWidget()

        self.dashboard_page = DashboardPage(
            on_new_mass=self._go_new_mass,
            on_open_previous=self._open_history,
            on_generate=self._go_generate,
        )
        self.search_page = SearchPage()
        self.planner_page = PlannerPage()
        # History and Settings are dialogs, not stacked pages - clicking
        # their sidebar entries opens the dialog directly (see _on_nav_changed).

        self.stack.addWidget(self.dashboard_page)   # index 0
        self.stack.addWidget(self.search_page)      # index 1
        self.stack.addWidget(self.planner_page)      # index 2

        root.addWidget(self.stack, 1)

        self.nav_list.setCurrentRow(0)

    # -- Navigation -----------------------------------------------------

    def _on_nav_changed(self, row: int) -> None:
        page_name = PAGE_NAMES[row]
        if page_name == "History":
            self._open_history()
            self.nav_list.setCurrentRow(0)  # snap back to Dashboard after closing
        elif page_name == "Settings":
            self._open_settings()
            self.nav_list.setCurrentRow(0)
        else:
            self.stack.setCurrentIndex(PAGE_NAMES.index(page_name))
            if page_name == "Dashboard":
                self.dashboard_page.refresh()

    def _open_history(self) -> None:
        dialog = HistoryDialog(self, on_open=self._load_mass_plan)
        dialog.exec()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self, on_theme_changed=self._apply_theme)
        dialog.exec()

    def _load_mass_plan(self, plan_id: int) -> None:
        self.planner_page.load_plan(plan_id)
        self.nav_list.setCurrentRow(PAGE_NAMES.index("Mass Planner"))

    def _go_new_mass(self) -> None:
        self.planner_page.current_plan_id = None
        self.planner_page._populate_slots()
        self.nav_list.setCurrentRow(PAGE_NAMES.index("Mass Planner"))

    def _go_generate(self) -> None:
        self.nav_list.setCurrentRow(PAGE_NAMES.index("Mass Planner"))

    # -- Theming ----------------------------------------------------------

    def _apply_theme(self, theme_name: str) -> None:
        styles_dir = Path(__file__).resolve().parent.parent / "styles"
        qss_path = styles_dir / f"{theme_name}.qss"
        if not qss_path.exists():
            logger.warning("Theme file not found: %s", qss_path)
            return
        self.setStyleSheet(qss_path.read_text())
