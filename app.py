"""
Church Hymn Planner - application entry point.

Run with:
    python app.py
"""
from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from database.database import init_db
from ui.main_window import MainWindow


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> int:
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting MissaFlow")

    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("MissaFlow")
    
    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
