"""
main.py - VocaDesk entry point.
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from app.gui import MainWindow
from app.utils import get_logger

logger = get_logger("main")


def main():
    # High-DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("VocaDesk")
    app.setApplicationDisplayName("VocaDesk")
    app.setOrganizationName("VocaDesk")

    # Base font
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    window = MainWindow()
    window.show()

    logger.info("VocaDesk started.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
