import os
import sys
import traceback
from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QLabel, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMessageBox, QFrame
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt5 import uic

# Import tab classes
from ui.logic.login_window import LoginWindow
from ui.logic.dashboard_tab import DashboardTab
from ui.logic.account_tab import AccountTab
from ui.logic.devices_tab import DevicesTab
from ui.logic.orders import OrdersTab


def get_resource_path(relative_path):
    """Get absolute path to resource - works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class UI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_session = None

        try:
            self.show_login()
        except Exception as e:
            QMessageBox.critical(
                None,
                "Startup Error",
                f"Failed to show login window:\n\n{str(e)}\n\n{traceback.format_exc()}"
            )
            sys.exit(1)

    def show_login(self):
        """Show login dialog and only proceed if successful"""
        try:
            login_dialog = LoginWindow()
            login_dialog.loginSuccessful.connect(self.on_login_success)

            result = login_dialog.exec_()

            if result != LoginWindow.Accepted:
                print("Login cancelled or failed")
                sys.exit(0)

            # Double-check we have a session
            if not self.user_session:
                print("ERROR: No user session after login dialog accepted!")
                QMessageBox.critical(
                    None,
                    "Login Error",
                    "Login appeared successful but no session was created. Please try again."
                )
                sys.exit(1)

        except Exception as e:
            QMessageBox.critical(
                None,
                "Login Error",
                f"Error during login:\n\n{str(e)}\n\n{traceback.format_exc()}"
            )
            sys.exit(1)

    def on_login_success(self, session):
        """Called when user successfully logs in"""
        try:
            print(f"✓ Login successful for user: {session.user.email}")
            self.user_session = session
            self.init_main_ui()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize main window:\n\n{str(e)}\n\n{traceback.format_exc()}"
            )
            sys.exit(1)

    def init_main_ui(self):
        """Initialize the main dashboard UI after successful login"""
        try:
            print("Initializing main UI...")

            # Load UI file with proper path
            ui_file_path = get_resource_path("ui/new_ui.ui")
            print(f"Looking for UI file at: {ui_file_path}")

            if not os.path.exists(ui_file_path):
                raise FileNotFoundError(f"UI file not found at: {ui_file_path}")

            uic.loadUi(ui_file_path, self)
            self.setWindowTitle("AirFlow IQ Analytics")

            # Get tab widget reference
            self.tabWidget = self.findChild(QTabWidget, "tabWidget")

            if not self.tabWidget:
                raise RuntimeError("Could not find tabWidget in UI file")

            # Hide default tab bar
            self.tabWidget.tabBar().hide()

            # Create Orders tab if needed
            self.create_orders_tab()

            # Setup sidebar with hamburger menu
            self.setup_sidebar()

            # Create header bar
            self.create_tab_header()

            # Map tab indices
            self.map_tab_indices()

            # Initialize all tabs (each tab handles its own logic)
            self.init_dashboard_tab()
            self.init_devices_tab()
            self.init_orders_tab()
            self.init_account_tab()

            # Connect tab change
            self.tabWidget.currentChanged.connect(self.update_tab_header)

            print("✓ Main UI initialized successfully")
            self.show()

        except Exception as e:
            print(f"ERROR in init_main_ui: {e}")
            print(traceback.format_exc())
            raise

    def create_orders_tab(self):
        """Create Orders tab programmatically if it doesn't exist"""
        try:
            orders_exists = False
            for i in range(self.tabWidget.count()):
                if self.tabWidget.widget(i).objectName() == "Orders":
                    orders_exists = True
                    break

            if not orders_exists:
                orders_tab_widget = QWidget()
                orders_tab_widget.setObjectName("Orders")
                self.tabWidget.addTab(orders_tab_widget, "Orders")
                print("✓ Orders tab created programmatically")
        except Exception as e:
            print(f"Warning: Could not create orders tab: {e}")

    def setup_sidebar(self):
        """Setup animated sidebar with hamburger menu"""
        try:
            # Create sidebar
            self.sidebar = QFrame(self)
            self.sidebar.setFixedWidth(250)
            self.sidebar.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border-right: 2px solid #E0E0E0;
                }
            """)

            sidebar_layout = QVBoxLayout()
            sidebar_layout.setContentsMargins(0, 0, 0, 0)
            sidebar_layout.setSpacing(0)

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
                print(f"Warning: Logo not found at {logo_path}")
                logo_label.setText("AirFlow IQ")
                logo_label.setStyleSheet("color: #007BFF; font-size: 18px; font-weight: bold;")

            logo_label.setAlignment(Qt.AlignCenter)
            logo_layout.addWidget(logo_label)
            logo_container.setLayout(logo_layout)
            sidebar_layout.addWidget(logo_container)

            # Navigation buttons
            nav_items = [
                ("Dashboard", "Dashboard"),
                ("Devices", "Devices"),
                ("Orders", "Orders"),
                ("Account", "Account")
            ]

            for text, tab_name in nav_items:
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
                btn.clicked.connect(lambda checked, name=tab_name: self.switch_to_tab(name))
                sidebar_layout.addWidget(btn)

            sidebar_layout.addStretch()
            self.sidebar.setLayout(sidebar_layout)

            # Position sidebar off-screen initially
            self.sidebar.setGeometry(-250, 60, 250, self.height() - 60)
            self.sidebar_visible = False

            # Hamburger button
            self.hamburger_btn = QPushButton("☰", self)
            self.hamburger_btn.setFixedSize(50, 50)
            self.hamburger_btn.move(10, 65)
            self.hamburger_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                    font-size: 24px;
                    color: #2c3e50;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #EBF5FF;
                    border: 1px solid #007BFF;
                }
                QPushButton:pressed {
                    background-color: #007BFF;
                    color: white;
                }
            """)
            self.hamburger_btn.clicked.connect(self.toggle_sidebar)
            self.hamburger_btn.setCursor(Qt.PointingHandCursor)
            self.hamburger_btn.raise_()

            # Animations
            self.sidebar_animation = QPropertyAnimation(self.sidebar, b"geometry")
            self.sidebar_animation.setDuration(300)
            self.sidebar_animation.setEasingCurve(QEasingCurve.InOutQuart)

            self.hamburger_animation = QPropertyAnimation(self.hamburger_btn, b"pos")
            self.hamburger_animation.setDuration(300)
            self.hamburger_animation.setEasingCurve(QEasingCurve.InOutQuart)

            print("✓ Sidebar setup complete")
        except Exception as e:
            print(f"ERROR in setup_sidebar: {e}")
            raise

    def toggle_sidebar(self):
        """Toggle sidebar visibility"""
        if self.sidebar_visible:
            # Hide
            self.sidebar_animation.setStartValue(QRect(0, 60, 250, self.height() - 60))
            self.sidebar_animation.setEndValue(QRect(-250, 60, 250, self.height() - 60))
            self.hamburger_animation.setStartValue(QPoint(260, 65))
            self.hamburger_animation.setEndValue(QPoint(10, 65))
            self.sidebar_visible = False
        else:
            # Show
            self.sidebar_animation.setStartValue(QRect(-250, 60, 250, self.height() - 60))
            self.sidebar_animation.setEndValue(QRect(0, 60, 250, self.height() - 60))
            self.hamburger_animation.setStartValue(QPoint(10, 65))
            self.hamburger_animation.setEndValue(QPoint(260, 65))
            self.sidebar_visible = True
            self.sidebar.raise_()
            self.hamburger_btn.raise_()

        self.sidebar_animation.start()
        self.hamburger_animation.start()

    def create_tab_header(self):
        """Create the blue header bar at the top"""
        try:
            self.tab_header = QFrame(self)
            self.tab_header.setFixedHeight(60)
            self.tab_header.setStyleSheet("""
                QFrame {
                    background-color: #007BFF;
                    border: none;
                }
            """)

            header_layout = QHBoxLayout()
            header_layout.setContentsMargins(20, 0, 20, 0)

            self.tab_title_label = QLabel("Dashboard")
            self.tab_title_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 22px;
                    font-weight: bold;
                    background-color: transparent;
                }
            """)
            self.tab_title_label.setAlignment(Qt.AlignCenter)

            header_layout.addWidget(self.tab_title_label)
            self.tab_header.setLayout(header_layout)

            # Position at very top
            self.tab_header.setGeometry(0, 0, self.width(), 60)
            self.tab_header.raise_()

            print("✓ Tab header created")
        except Exception as e:
            print(f"ERROR in create_tab_header: {e}")
            raise

    def map_tab_indices(self):
        """Map tab object names to display names"""
        try:
            self.tab_display_names = {}
            self.tab_object_names = {}

            for i in range(self.tabWidget.count()):
                widget = self.tabWidget.widget(i)
                obj_name = widget.objectName()

                print(f"Tab {i}: objectName = '{obj_name}'")

                name_map = {
                    "Dashboard": "Dashboard",
                    "Devices": "Devices",
                    "Orders": "Orders",
                    "Account": "Account",
                    "Analytics": "Dashboard",  # The UI file uses "Analytics"
                    "tab": "Dashboard",
                    "tab_1": "Dashboard",
                    "tab_2": "Devices",
                    "tab_3": "Orders",
                    "tab_4": "Account"
                }

                if obj_name in name_map:
                    self.tab_display_names[i] = name_map[obj_name]
                    self.tab_object_names[name_map[obj_name]] = i
                else:
                    # If first tab and no name, assume Dashboard
                    if i == 0:
                        self.tab_display_names[i] = "Dashboard"
                        self.tab_object_names["Dashboard"] = i

            print(f"✓ Mapped tabs: {self.tab_object_names}")
        except Exception as e:
            print(f"ERROR in map_tab_indices: {e}")
            raise

    def switch_to_tab(self, tab_name):
        """Switch to tab by name and close sidebar"""
        if tab_name in self.tab_object_names:
            self.tabWidget.setCurrentIndex(self.tab_object_names[tab_name])
            if self.sidebar_visible:
                self.toggle_sidebar()

    def update_tab_header(self, index):
        """Update header title when tab changes"""
        if index in self.tab_display_names:
            self.tab_title_label.setText(self.tab_display_names[index])

    def init_dashboard_tab(self):
        """Initialize Dashboard tab with DashboardTab class"""
        try:
            # Find the Analytics tab (which is the Dashboard in the UI file)
            dashboard_tab_widget = self.findChild(QWidget, "Analytics")
            if dashboard_tab_widget:
                # Clear any existing layout
                if dashboard_tab_widget.layout():
                    QWidget().setLayout(dashboard_tab_widget.layout())

                # Create layout and add DashboardTab
                layout = QVBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                self.dashboard_tab = DashboardTab(self.user_session)
                layout.addWidget(self.dashboard_tab)
                dashboard_tab_widget.setLayout(layout)
                print("✓ Dashboard tab initialized")
        except Exception as e:
            print(f"ERROR initializing dashboard tab: {e}")
            import traceback
            traceback.print_exc()

    def init_devices_tab(self):
        """Initialize Devices tab"""
        try:
            devices_tab_widget = self.findChild(QWidget, "Devices")
            if devices_tab_widget:
                if devices_tab_widget.layout():
                    QWidget().setLayout(devices_tab_widget.layout())

                layout = QVBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                self.devices_tab = DevicesTab(self.user_session)
                layout.addWidget(self.devices_tab)
                devices_tab_widget.setLayout(layout)
                print("✓ Devices tab initialized")
        except Exception as e:
            print(f"ERROR initializing devices tab: {e}")

    def init_orders_tab(self):
        """Initialize Orders tab"""
        try:
            orders_tab_widget = self.findChild(QWidget, "Orders")
            if orders_tab_widget:
                if orders_tab_widget.layout():
                    QWidget().setLayout(orders_tab_widget.layout())

                layout = QVBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                self.orders_tab = OrdersTab(self.user_session)
                layout.addWidget(self.orders_tab)
                orders_tab_widget.setLayout(layout)
                print("✓ Orders tab initialized")
        except Exception as e:
            print(f"ERROR initializing orders tab: {e}")

    def init_account_tab(self):
        """Initialize Account tab"""
        try:
            account_tab_widget = self.findChild(QWidget, "Account")
            if account_tab_widget:
                if account_tab_widget.layout():
                    QWidget().setLayout(account_tab_widget.layout())

                layout = QVBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                self.account_tab = AccountTab(self.user_session)
                self.account_tab.signOutRequested.connect(self.handle_sign_out)
                layout.addWidget(self.account_tab)
                account_tab_widget.setLayout(layout)
                print("✓ Account tab initialized")
        except Exception as e:
            print(f"ERROR initializing account tab: {e}")

    def handle_sign_out(self):
        """Handle sign out"""
        self.close()
        sys.exit(0)

    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)

        # Adjust header width
        if hasattr(self, 'tab_header'):
            self.tab_header.setGeometry(0, 0, self.width(), 60)
            self.tab_header.raise_()

        # Adjust sidebar height
        if hasattr(self, 'sidebar'):
            current_geo = self.sidebar.geometry()
            self.sidebar.setGeometry(current_geo.x(), 60, 250, self.height() - 60)