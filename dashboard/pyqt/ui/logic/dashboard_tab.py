import sys
import os
import pandas as pd

# Add parent directory to path to access modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QDialog, QCheckBox, QScrollArea, QFrame, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from data.supabase_loader import SupabaseDataLoader
from plot.mpl_canvas import MplCanvas

REFRESH_COUNTDOWN = 30000


class MultiDeviceDialog(QDialog):
    """
    Dialog for selecting multiple devices to display on the same graph.
    Shows checkboxes for each device the user owns.
    """

    def __init__(self, devices, selected_device_ids, parent=None):
        super().__init__(parent)
        self.devices = devices
        self.selected_device_ids = selected_device_ids.copy()  # Copy to avoid modifying original
        self.checkboxes = {}  # Map device_id -> checkbox
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Add Devices to Graph")
        self.setMinimumSize(400, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #F4F7FA;
            }
            QLabel {
                color: #333333;
            }
            QCheckBox {
                font-size: 13px;
                color: #2c3e50;
                padding: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Select Devices to Display")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "Check the devices you want to see on the graph.\nEach device will be shown as a different colored line.")
        desc.setStyleSheet("color: #6c757d; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Scroll area for checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
        """)

        checkbox_container = QWidget()
        checkbox_layout = QVBoxLayout()
        checkbox_layout.setSpacing(10)
        checkbox_layout.setContentsMargins(15, 15, 15, 15)

        # Create checkbox for each device
        if len(self.devices) == 0:
            no_devices_label = QLabel("No devices available")
            no_devices_label.setStyleSheet("color: #6c757d; padding: 20px;")
            no_devices_label.setAlignment(Qt.AlignCenter)
            checkbox_layout.addWidget(no_devices_label)
        else:
            for device in self.devices:
                device_id = device.get('id')
                device_name = device.get('name', f'Device {device_id}')
                hvac_location = device.get('hvac_location', '')

                # Create display name
                display_name = f"{device_name}"
                if hvac_location:
                    display_name += f" ({hvac_location})"

                checkbox = QCheckBox(display_name)
                checkbox.setStyleSheet("""
                    QCheckBox {
                        padding: 10px;
                        background-color: #F8F9FA;
                        border-radius: 6px;
                    }
                    QCheckBox:hover {
                        background-color: #EBF5FF;
                    }
                """)

                # Check if this device is already selected
                if device_id in self.selected_device_ids:
                    checkbox.setChecked(True)

                self.checkboxes[device_id] = checkbox
                checkbox_layout.addWidget(checkbox)

        checkbox_layout.addStretch()
        checkbox_container.setLayout(checkbox_layout)
        scroll.setWidget(checkbox_container)
        layout.addWidget(scroll)

        # Buttons
        btn_layout = QHBoxLayout()

        # Select All / Deselect All buttons
        select_all_btn = QPushButton("Select All")
        select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #6c757d;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F8F9FA;
            }
        """)
        select_all_btn.setCursor(Qt.PointingHandCursor)
        select_all_btn.clicked.connect(self.select_all)

        deselect_all_btn = QPushButton("Clear All")
        deselect_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #6c757d;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F8F9FA;
            }
        """)
        deselect_all_btn.setCursor(Qt.PointingHandCursor)
        deselect_all_btn.clicked.connect(self.deselect_all)

        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        btn_layout.addStretch()

        # Apply / Cancel buttons
        apply_btn = QPushButton("Apply")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #6c757d;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F8F9FA;
            }
        """)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(apply_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def select_all(self):
        """Check all checkboxes"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)

    def deselect_all(self):
        """Uncheck all checkboxes"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)

    def get_selected_device_ids(self):
        """Return list of selected device IDs"""
        selected = []
        for device_id, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                selected.append(device_id)
        return selected


class DashboardTab(QWidget):
    """Dashboard tab with graphs and sensor data - supports multiple devices on one graph"""

    def __init__(self, user_session, parent=None):
        super().__init__(parent)
        self.user_session = user_session
        self.data_df = pd.DataFrame()
        self.current_plot_col = "temp"
        self.current_device_id = None
        self.current_time_range_hours = 24
        self.devices = []
        self.selected_device_ids = []  # List of device IDs to show on graph
        self.device_data_cache = {}  # Cache data for each device {device_id: dataframe}
        self.active_loaders = []  # Keep references to active loaders to prevent garbage collection
        self.setup_ui()
        self.fetch_devices()
        self.setup_auto_refresh()

    def setup_auto_refresh(self):
        """Setup auto-refresh timer"""
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.refresh_all_data)
        # Refresh every 30 seconds (30000 milliseconds)
        self.auto_refresh_timer.start(REFRESH_COUNTDOWN)
        print("✅ Auto-refresh enabled (every 30 seconds)")

    def update_refresh_interval(self, seconds):
        """Update the auto-refresh interval"""
        milliseconds = seconds * 1000
        self.auto_refresh_timer.setInterval(milliseconds)
        print(f"✅ Auto-refresh interval updated to {seconds} seconds")

    def setup_ui(self):
        """Setup the dashboard UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 80, 20, 20)
        main_layout.setSpacing(20)

        # ============================================================
        # CONTROL SECTION (Device selector, Time range, User info)
        # ============================================================
        controls_layout = QHBoxLayout()

        # Device selector
        device_label = QLabel("Device:")
        device_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #6c757d;")

        self.deviceComboBox = QComboBox()
        self.deviceComboBox.setMinimumWidth(200)
        self.deviceComboBox.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1px solid #007BFF;
            }
        """)
        self.deviceComboBox.currentIndexChanged.connect(self.on_device_changed)

        controls_layout.addWidget(device_label)
        controls_layout.addWidget(self.deviceComboBox)

        # Time range selector
        time_label = QLabel("Time Range:")
        time_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #6c757d; margin-left: 20px;")

        self.timeRangeComboBox = QComboBox()
        self.timeRangeComboBox.setMinimumWidth(150)
        self.timeRangeComboBox.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1px solid #007BFF;
            }
        """)

        # Add time range options
        self.timeRangeComboBox.addItem("Last Hour", 1)
        self.timeRangeComboBox.addItem("Last 6 Hours", 6)
        self.timeRangeComboBox.addItem("Last 24 Hours", 24)
        self.timeRangeComboBox.addItem("Last 7 Days", 24 * 7)
        self.timeRangeComboBox.addItem("Last 30 Days", 24 * 30)
        self.timeRangeComboBox.addItem("All Time", None)
        self.timeRangeComboBox.setCurrentIndex(2)
        self.timeRangeComboBox.currentIndexChanged.connect(self.on_time_range_changed)

        controls_layout.addWidget(time_label)
        controls_layout.addWidget(self.timeRangeComboBox)
        controls_layout.addStretch()

        # Auto-refresh period control
        refresh_period_label = QLabel("Auto-refresh:")
        refresh_period_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #6c757d; margin-left: 20px;")

        self.refreshPeriodSpinBox = QSpinBox()
        self.refreshPeriodSpinBox.setMinimum(5)  # Minimum 5 seconds
        self.refreshPeriodSpinBox.setMaximum(300)  # Maximum 5 minutes
        self.refreshPeriodSpinBox.setValue(30)  # Default 30 seconds
        self.refreshPeriodSpinBox.setSuffix(" sec")
        self.refreshPeriodSpinBox.setMinimumWidth(100)
        self.refreshPeriodSpinBox.setStyleSheet("""
            QSpinBox {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QSpinBox:hover {
                border: 1px solid #007BFF;
            }
        """)
        self.refreshPeriodSpinBox.valueChanged.connect(self.update_refresh_interval)

        controls_layout.addWidget(refresh_period_label)
        controls_layout.addWidget(self.refreshPeriodSpinBox)

        # User info
        user_email = self.user_session.user.email if self.user_session else "Unknown"
        user_label = QLabel(f"Logged in as: {user_email}")
        user_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        controls_layout.addWidget(user_label)

        # Add to Graph button (NEW!)
        add_to_graph_btn = QPushButton(" + Add to Graph")
        add_to_graph_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_to_graph_btn.setCursor(Qt.PointingHandCursor)
        add_to_graph_btn.clicked.connect(self.show_multi_device_dialog)
        controls_layout.addWidget(add_to_graph_btn)

        # Refresh button
        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_all_data)
        controls_layout.addWidget(refresh_btn)

        main_layout.addLayout(controls_layout)

        # ============================================================
        # GRAPH SECTION WITH WARNING OVERLAY
        # ============================================================
        # Create a container for the graph to hold both canvas and warning
        graph_container = QWidget()
        graph_container_layout = QVBoxLayout()
        graph_container_layout.setContentsMargins(0, 0, 0, 0)
        graph_container_layout.setSpacing(0)

        self.canvas = MplCanvas()
        graph_container_layout.addWidget(self.canvas)
        graph_container.setLayout(graph_container_layout)

        # Create warning banner as overlay (positioned absolutely)
        self.filter_warning = QFrame(graph_container)
        self.filter_warning.setObjectName("warning")
        self.filter_warning.setStyleSheet("""
            QFrame#warning { 
                background-color: #fff3cd;
                border: 3px solid #ffc107;
                border-radius: 8px;
                padding: 10px 15px;
            }
        """)
        self.filter_warning.setVisible(False)  # Hidden by default
        self.filter_warning.raise_()  # Ensure it's on top

        warning_layout = QHBoxLayout()
        warning_layout.setContentsMargins(0, 0, 0, 0)
        warning_layout.setSpacing(8)

        # Warning icon
        warning_icon = QLabel("⚠️")
        warning_icon.setStyleSheet("font-size: 18px; background: transparent; border: none;")

        # Warning text
        self.filter_warning_text = QLabel("Filter may be dirty or clogged")
        self.filter_warning_text.setStyleSheet("""
            color: #856404;
            font-size: 12px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        self.filter_warning_text.setWordWrap(False)

        warning_layout.addWidget(warning_icon)
        warning_layout.addWidget(self.filter_warning_text)

        self.filter_warning.setLayout(warning_layout)

        # Position warning in top right (will be updated in resizeEvent)
        self.filter_warning.adjustSize()

        main_layout.addWidget(graph_container, stretch=2)

        # ============================================================
        # BUTTONS FOR GRAPH TYPE SELECTION
        # ============================================================
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        buttons = [
            ("Temperature", "temp"),
            ("Pressure", "pressure"),
            ("Humidity", "humidity"),
            ("Wind Speed", "windspeed")
        ]

        for text, keyword in buttons:
            btn = QPushButton(text)
            btn.setFixedHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    border: 2px solid #E0E0E0;
                    border-radius: 8px;
                    color: #2c3e50;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #EBF5FF;
                    border: 2px solid #007BFF;
                    color: #007BFF;
                }
                QPushButton:pressed {
                    background-color: #007BFF;
                    color: white;
                }
            """)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=keyword: self.plot_data(k))
            button_layout.addWidget(btn)

        main_layout.addLayout(button_layout)

        # ============================================================
        # STATISTICS CARDS
        # ============================================================
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(0)

        # Create stat cards
        self.temp_card = self.create_stat_card("Avg Temperature", "N/A", "#004794")
        self.pressure_card = self.create_stat_card("Avg Pressure", "N/A", "#004794")
        self.humidity_card = self.create_stat_card("Avg Humidity", "N/A", "#004794")
        self.windspeed_card = self.create_stat_card("Wind Speed", "N/A", "#004794")

        stats_layout.addWidget(self.temp_card)
        stats_layout.addWidget(self.pressure_card)
        stats_layout.addWidget(self.humidity_card)
        stats_layout.addWidget(self.windspeed_card)

        main_layout.addLayout(stats_layout)

        self.setLayout(main_layout)

    def resizeEvent(self, event):
        """Handle resize to reposition warning banner"""
        super().resizeEvent(event)
        if hasattr(self, 'filter_warning') and hasattr(self, 'canvas'):
            # Position warning in top right corner of canvas
            self.filter_warning.adjustSize()
            warning_width = self.filter_warning.width()
            warning_height = self.filter_warning.height()

            # Get canvas position and size
            canvas_width = self.canvas.width()

            # Position with some margin from edges
            x = canvas_width - warning_width - 15
            y = 15

            self.filter_warning.move(x, y)

    def create_stat_card(self, title, value, color):
        """Create a statistics card"""
        card = QWidget()
        card.setObjectName("stat_card")
        card.setFixedSize(400, 120)
        # "QWidget#stat_card" makes the following style sheet only affect the stat card. no cascading styles unto child widgets
        card.setStyleSheet(f"""
            QWidget#stat_card{{
                background-color: white;
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 5px;
                }}

        """)

        layout = QVBoxLayout()
        layout.setSpacing(5)

        title_label = QLabel("  " + title)
        title_label.setStyleSheet("color: #6c757d; font-size: 18px; font-weight: 600;")

        value_label = QLabel("   " + value)
        value_label.setObjectName(f"{title.replace(' ', '_')}_value")
        value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        card.setLayout(layout)
        return card

    def show_multi_device_dialog(self):
        """Show dialog to select multiple devices for the graph"""
        if len(self.devices) == 0:
            QMessageBox.information(
                self,
                "No Devices",
                "You don't have any devices yet. Please add a device first."
            )
            return

        dialog = MultiDeviceDialog(self.devices, self.selected_device_ids, self)
        if dialog.exec_() == QDialog.Accepted:
            self.selected_device_ids = dialog.get_selected_device_ids()
            print(f"📊 Selected devices: {self.selected_device_ids}")

            # Fetch data for all selected devices
            if len(self.selected_device_ids) > 0:
                self.fetch_multi_device_data()
            else:
                # If no devices selected, clear the graph
                self.canvas.ax.clear()
                self.canvas.ax.set_title("No devices selected", fontsize=14)
                self.canvas.draw()

    def refresh_all_data(self):
        """Refresh both graph data and averages"""
        print("🔄 Refreshing all data...")
        if len(self.selected_device_ids) > 0:
            self.fetch_multi_device_data()
        else:
            self.fetch_data()
        self.fetch_averages()

    def fetch_devices(self):
        """Fetch list of devices from Supabase"""
        print("📡 Fetching devices...")
        self.device_loader = SupabaseDataLoader(
            SupabaseDataLoader.FETCH_MODE_DEVICES,
            user_session=self.user_session
        )
        self.device_loader.devicesFetched.connect(self.update_devices)
        self.device_loader.errorOccurred.connect(self.handle_error)
        self.device_loader.start()

    def update_devices(self, devices):
        """Populate combo box with devices"""
        print(f"✅ Received {len(devices)} devices")
        self.devices = devices

        # Check if currently selected device still exists
        device_still_exists = False
        if self.current_device_id:
            device_still_exists = any(d.get("id") == self.current_device_id for d in devices)

        self.deviceComboBox.blockSignals(True)
        self.deviceComboBox.clear()

        if len(devices) == 0:
            self.deviceComboBox.addItem("No devices found", None)
            self.deviceComboBox.setEnabled(False)
            # Clear current device
            self.current_device_id = None
        else:
            # Add "All My Devices" option
            #self.deviceComboBox.addItem("All My Devices", None)

            for device in devices:
                device_id = device.get("id")
                device_name = device.get("name", f"Device {device_id}")
                hvac_location = device.get("hvac_location", "")
                display_name = f"{device_name} ({hvac_location})" if hvac_location else device_name
                self.deviceComboBox.addItem(display_name, device_id)

            self.deviceComboBox.setEnabled(True)

            # If current device no longer exists, reset to "All My Devices"
            if self.current_device_id and not device_still_exists:
                print(f"⚠️ Device {self.current_device_id} no longer available, switching to 'All My Devices'")
                self.current_device_id = None
                self.deviceComboBox.setCurrentIndex(0)  # Select "All My Devices"

        self.deviceComboBox.blockSignals(False)

        if len(devices) > 0:
            self.fetch_data()
            self.fetch_averages()

    def on_device_changed(self, index):
        """Handle device selection change"""
        self.current_device_id = self.deviceComboBox.currentData()
        print(f"🔍 Device changed to: {self.current_device_id or 'All'}")

        # Clear multi-device selection when changing main device
        self.selected_device_ids = []

        self.fetch_data()
        self.fetch_averages()

    def on_time_range_changed(self, index):
        """Handle time range selection change"""
        self.current_time_range_hours = self.timeRangeComboBox.currentData()
        print(f"⏰ Time range changed to: {self.current_time_range_hours} hours")

        if len(self.selected_device_ids) > 0:
            self.fetch_multi_device_data()
        else:
            self.fetch_data()
        self.fetch_averages()

    def fetch_data(self):
        """Fetch graph data from Supabase for single device view"""
        print(f"📊 Fetching data for device: {self.current_device_id or 'All'}...")
        self.loader = SupabaseDataLoader(
            SupabaseDataLoader.FETCH_MODE_GRAPH,
            device_id=self.current_device_id,
            user_session=self.user_session,
            time_range_hours=self.current_time_range_hours
        )
        self.loader.dataFetched.connect(self.update_data)
        self.loader.errorOccurred.connect(self.handle_error)
        self.loader.start()

    def fetch_multi_device_data(self):
        """Fetch data for all selected devices and plot them together"""
        print(f"📊 Fetching data for {len(self.selected_device_ids)} devices...")
        self.device_data_cache = {}
        self.pending_fetches = len(self.selected_device_ids)
        self.active_loaders = []  # Clear and store new loaders

        # Fetch data for each selected device
        for device_id in self.selected_device_ids:
            loader = SupabaseDataLoader(
                SupabaseDataLoader.FETCH_MODE_GRAPH,
                device_id=device_id,
                user_session=self.user_session,
                time_range_hours=self.current_time_range_hours
            )

            # Store the device_id as an attribute on the loader
            loader.device_id_for_callback = device_id

            # Connect signals - use a proper method instead of lambda
            loader.dataFetched.connect(self.on_device_data_fetched)
            loader.errorOccurred.connect(self.handle_error)

            # Keep reference to prevent garbage collection
            self.active_loaders.append(loader)

            # Start the loader
            loader.start()

    def on_device_data_fetched(self, df):
        """Handle data fetched event from a specific device loader"""
        # Get the device_id from the sender (the loader that emitted the signal)
        sender = self.sender()
        if hasattr(sender, 'device_id_for_callback'):
            device_id = sender.device_id_for_callback
            self.update_multi_device_data(device_id, df)

    def update_multi_device_data(self, device_id, df):
        """Store fetched data for a device and plot when all are loaded"""
        self.device_data_cache[device_id] = df
        self.pending_fetches -= 1

        print(f"✅ Received data for device {device_id}: {len(df)} rows")

        # Once all devices are loaded, plot them
        if self.pending_fetches == 0:
            self.plot_multi_device()
            # Clean up loader references to free memory
            self.active_loaders = []

    def update_data(self, df):
        """Update graph with new data (single device)"""
        print(f"✅ Data received: {len(df)} rows")
        self.data_df = df
        self.plot_current()

    def plot_data(self, keyword):
        """Set which data to plot"""
        print(f"📈 Plotting: {keyword}")
        self.current_plot_col = keyword

        # Plot based on mode
        if len(self.selected_device_ids) > 0:
            self.plot_multi_device()
        else:
            self.plot_current()

    def plot_current(self):
        """Plot the current data selection (single device)"""
        if self.data_df.empty:
            print("⚠ DataFrame is empty")
            return

        if not self.current_plot_col:
            return

        # Find matching column
        col = next(
            (c for c in self.data_df.columns if self.current_plot_col in c.lower()),
            None
        )
        if not col:
            print(f"⚠ Column matching '{self.current_plot_col}' not found")
            print(f"Available columns: {self.data_df.columns.tolist()}")
            return

        if "recorded_at" not in self.data_df.columns:
            print("⚠ 'recorded_at' column not found")
            return

        # Prepare data
        df = self.data_df[["recorded_at", col]].copy()

        if not pd.api.types.is_datetime64_any_dtype(df["recorded_at"]):
            df["recorded_at"] = pd.to_datetime(df["recorded_at"], utc=True, errors='coerce')

        if df["recorded_at"].dt.tz is not None:
            df["recorded_at"] = df["recorded_at"].dt.tz_localize(None)

        df = df.dropna()

        if df.empty:
            print("⚠ No valid data after cleaning")
            return

        df = df.sort_values("recorded_at")

        x = df["recorded_at"]
        y = pd.to_numeric(df[col], errors="coerce")

        # Plot
        self.canvas.ax.clear()
        self.canvas.ax.plot(x, y, marker='o', linestyle='-', linewidth=2, markersize=5, color='#007BFF')
        self.canvas.ax.set_title(col.replace("_", " ").title(), fontsize=14, fontweight='bold')
        self.canvas.ax.set_xlabel("Date & Time", fontsize=11)
        self.canvas.ax.set_ylabel(col.replace("_", " ").title(), fontsize=11)
        self.canvas.ax.grid(True, alpha=0.3)

        import matplotlib.dates as mdates
        self.canvas.ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
        self.canvas.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.canvas.ax.tick_params(axis="x", labelrotation=0)
        self.canvas.fig.subplots_adjust(bottom=0.2)

        self.canvas.draw()
        print(f"✅ Plot updated: {len(df)} data points")

    def plot_multi_device(self):
        """Plot multiple devices on the same graph with different colors"""
        if not self.current_plot_col:
            return

        # Color palette for different devices
        colors = ['#007BFF', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6f42c1', '#e83e8c', '#fd7e14']

        self.canvas.ax.clear()

        # Get device name mapping
        device_names = {d['id']: d.get('name', 'Unknown') for d in self.devices}

        plotted_any = False

        # Plot each device
        for idx, device_id in enumerate(self.selected_device_ids):
            if device_id not in self.device_data_cache:
                continue

            df = self.device_data_cache[device_id]

            if df.empty:
                continue

            # Find matching column
            col = next(
                (c for c in df.columns if self.current_plot_col in c.lower()),
                None
            )

            if not col or "recorded_at" not in df.columns:
                continue

            # Prepare data
            plot_df = df[["recorded_at", col]].copy()

            if not pd.api.types.is_datetime64_any_dtype(plot_df["recorded_at"]):
                plot_df["recorded_at"] = pd.to_datetime(plot_df["recorded_at"], utc=True, errors='coerce')

            if plot_df["recorded_at"].dt.tz is not None:
                plot_df["recorded_at"] = plot_df["recorded_at"].dt.tz_localize(None)

            plot_df = plot_df.dropna().sort_values("recorded_at")

            if plot_df.empty:
                continue

            x = plot_df["recorded_at"]
            y = pd.to_numeric(plot_df[col], errors="coerce")

            # Use different color for each device
            color = colors[idx % len(colors)]
            device_name = device_names.get(device_id, device_id[:8])

            # Plot with label for legend
            self.canvas.ax.plot(
                x, y,
                marker='o',
                linestyle='-',
                linewidth=2,
                markersize=4,
                color=color,
                label=device_name,
                alpha=0.8
            )

            plotted_any = True

        if not plotted_any:
            self.canvas.ax.set_title("No data available", fontsize=14)
            self.canvas.draw()
            return

        # Set title and labels
        col_name = self.current_plot_col.replace("_", " ").title()
        self.canvas.ax.set_title(f"{col_name} - Multiple Devices", fontsize=14, fontweight='bold')
        self.canvas.ax.set_xlabel("Date & Time", fontsize=11)
        self.canvas.ax.set_ylabel(col_name, fontsize=11)
        self.canvas.ax.grid(True, alpha=0.3)

        # Add legend (only if multiple devices)
        if len(self.selected_device_ids) > 1:
            self.canvas.ax.legend(loc='best', fontsize=9, framealpha=0.9)

        import matplotlib.dates as mdates
        self.canvas.ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
        self.canvas.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.canvas.ax.tick_params(axis="x", labelrotation=0)
        self.canvas.fig.subplots_adjust(bottom=0.2)

        self.canvas.draw()
        print(f"✅ Multi-device plot updated: {len(self.selected_device_ids)} devices")

    def fetch_averages(self):
        """Fetch average statistics"""
        print("📈 Fetching averages...")
        self.avg_loader = SupabaseDataLoader(
            SupabaseDataLoader.FETCH_MODE_AVERAGES,
            device_id=self.current_device_id,
            user_session=self.user_session,
            time_range_hours=self.current_time_range_hours
        )
        self.avg_loader.averagesFetched.connect(self.update_averages)
        self.avg_loader.errorOccurred.connect(self.handle_error)
        self.avg_loader.start()

    def update_averages(self, avg):
        """Update statistics cards with averages"""
        # Update each card
        temp_label = self.temp_card.findChild(QLabel, "Avg_Temperature_value")
        if temp_label and avg.get('temp') is not None:
            temp_label.setText(f"{avg.get('temp'):.2f}°C")

        pressure_label = self.pressure_card.findChild(QLabel, "Avg_Pressure_value")
        if pressure_label and avg.get('pressure') is not None:
            pressure_label.setText(f"{avg.get('pressure'):.2f} Pa")

        humidity_label = self.humidity_card.findChild(QLabel, "Avg_Humidity_value")
        if humidity_label and avg.get('humidity') is not None:
            humidity_label.setText(f"{avg.get('humidity'):.2f}%")

        windspeed_label = self.windspeed_card.findChild(QLabel, "Wind_Speed_value")
        if windspeed_label and avg.get('windspeed') is not None:
            windspeed_label.setText(f"{avg.get('windspeed'):.2f} m/s")

        # Check for filter warning after updating cards
        self.check_filter_warning(avg)

        print("✅ Averages updated")

    def check_filter_warning(self, avg):
        """Check if windspeed indicates potential filter issue"""
        WINDSPEED_THRESHOLD = 2  # m/s - below this indicates potential issue
        MIN_TIME_RANGE_HOURS = 5  # Need at least 5 hours of data for reliable check

        windspeed = avg.get('windspeed')

        if windspeed is None:
            self.filter_warning.setVisible(False)
            return

        # Only warn if windspeed is low AND we have sufficient time range
        should_warn = (
                windspeed < WINDSPEED_THRESHOLD and
                (self.current_time_range_hours is None or
                 self.current_time_range_hours >= MIN_TIME_RANGE_HOURS)
        )

        if should_warn:
            self.filter_warning.setVisible(True)
            self.filter_warning_text.setText(
                f"Low airflow: {windspeed:.2f} m/s (normal is around {WINDSPEED_THRESHOLD} m/s)"
            )
            # Reposition after showing
            self.filter_warning.adjustSize()
            self.resizeEvent(None)
            print(f"🚨 Filter warning triggered: {windspeed:.2f} m/s")
        else:
            self.filter_warning.setVisible(False)

    def handle_error(self, error_msg):
        """Handle errors from data loading - just log them, don't show message boxes"""
        print(f"❌ Error: {error_msg}")
        # Don't show message boxes for data fetch errors - they can be annoying during auto-refresh
        # Users can check console for errors if needed