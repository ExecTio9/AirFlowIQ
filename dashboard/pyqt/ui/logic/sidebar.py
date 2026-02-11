import os
import sys
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal


def get_resource_path(relative_path):
    """Get absolute path to resource - works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class Sidebar(QFrame):
    """Animated sidebar navigation component"""

    tabRequested = pyqtSignal(str)  # Emits tab name when clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup sidebar UI"""
        self.setFixedWidth(250)
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-right: 2px solid #E0E0E0;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo section at top
        logo_container = QFrame()
        logo_container.setFixedHeight(100)
        logo_container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-bottom: 2px solid #E0E0E0;
            }
        """)
        logo_layout = QVBoxLayout()
        logo_layout.setContentsMargins(20, 20, 20, 20)
        logo_layout.setAlignment(Qt.AlignCenter)

        logo_label = QLabel()
        logo_path = get_resource_path("assets/logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(180, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText("AirFlow IQ")
            logo_label.setStyleSheet("""
                QLabel {
                    color: #007BFF;
                    font-size: 18px;
                    font-weight: bold;
                }
            """)

        logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_label)
        logo_container.setLayout(logo_layout)
        layout.addWidget(logo_container)

        # Navigation buttons
        nav_items = [
            ("Dashboard", "Dashboard"),
            ("Devices", "Devices"),
            ("Orders", "Orders"),
            ("Account", "Account")
        ]

        for text, tab_name in nav_items:
            btn = self.create_nav_button(text, tab_name)
            layout.addWidget(btn)

        layout.addStretch()
        self.setLayout(layout)

    def create_nav_button(self, text, tab_name):
        """Create a navigation button"""
        btn = QPushButton(text)
        btn.setFixedHeight(50)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                text-align: left;
                padding-left: 20px;
                font-size: 14px;
                color: #2c3e50;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #EBF5FF;
                color: #007BFF;
            }
            QPushButton:pressed {
                background-color: #007BFF;
                color: white;
            }
        """)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self.tabRequested.emit(tab_name))
        return btn