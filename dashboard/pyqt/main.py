"""
AirFlow IQ Analytics - Main Entry Point
This is the main file that starts the application
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# Import the main window
# Adjust this path based on where your main_window.py is located
try:
    from ui.logic.main_window import UI
except ImportError:
    # Try alternate import path
    from main_window import UI


def get_resource_path(relative_path):
    """Get absolute path to resource - works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main():
    """Main application entry point"""
    # Create the Qt Application
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("AirFlow IQ Analytics")
    app.setOrganizationName("AirFlow IQ")
    app.setApplicationVersion("1.0.0")

    # Set application icon (if exists)
    icon_path = get_resource_path("assets/icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Create and show the main window
    window = UI()

    # Start the event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()