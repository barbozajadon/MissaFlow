"""
Settings dialog - app-wide configuration (church name, default folders,
theme, backup location, default language).
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services import settings_service


class SettingsDialog(QDialog):
    """Modal dialog for editing application-wide settings."""

    def __init__(self, parent: Optional[QWidget] = None, on_theme_changed: Optional[Callable[[str], None]] = None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(480, 320)
        self._on_theme_changed = on_theme_changed
        self._build_ui()
        self._load_settings()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        form = QFormLayout()

        self.church_name_edit = QLineEdit()

        self.presentation_folder_edit, presentation_row = self._path_row()
        self.master_pptx_edit, master_pptx_row = self._path_row(is_file=True)
        self.backup_location_edit, backup_row = self._path_row()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])

        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Spanish", "Tagalog", "French", "Other"])

        form.addRow("Church name:", self.church_name_edit)
        form.addRow("Default presentation folder:", presentation_row)
        form.addRow("Master PowerPoint:", master_pptx_row)
        form.addRow("Backup location:", backup_row)
        form.addRow("Theme:", self.theme_combo)
        form.addRow("Default language:", self.language_combo)

        root.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _path_row(self, is_file: bool = False) -> tuple[QLineEdit, QWidget]:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        edit = QLineEdit()
        browse_btn = QPushButton("Browse...")

        def browse():
            if is_file:
                path, _ = QFileDialog.getOpenFileName(self, "Select file", filter="PowerPoint (*.pptx)")
            else:
                path = QFileDialog.getExistingDirectory(self, "Select folder")
            if path:
                edit.setText(path)

        browse_btn.clicked.connect(browse)
        layout.addWidget(edit)
        layout.addWidget(browse_btn)
        return edit, container

    def _load_settings(self) -> None:
        settings = settings_service.get_all_settings()
        self.church_name_edit.setText(settings.get("church_name", ""))
        self.presentation_folder_edit.setText(settings.get("presentation_folder", ""))
        self.master_pptx_edit.setText(settings.get("master_pptx_path", ""))
        self.backup_location_edit.setText(settings.get("backup_location", ""))
        self.theme_combo.setCurrentText(settings.get("theme", "dark"))
        self.language_combo.setCurrentText(settings.get("default_language", "English"))

    def _save(self) -> None:
        settings_service.set_setting("church_name", self.church_name_edit.text().strip())
        settings_service.set_setting("presentation_folder", self.presentation_folder_edit.text().strip())
        settings_service.set_setting("master_pptx_path", self.master_pptx_edit.text().strip())
        settings_service.set_setting("backup_location", self.backup_location_edit.text().strip())
        settings_service.set_setting("theme", self.theme_combo.currentText())
        settings_service.set_setting("default_language", self.language_combo.currentText())

        if self._on_theme_changed:
            self._on_theme_changed(self.theme_combo.currentText())

        self.accept()
