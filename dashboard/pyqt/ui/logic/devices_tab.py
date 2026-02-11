from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY


class DeviceCard(QFrame):
    """Individual device card widget"""

    # these are the signals that can be sent by the cards
    unclaimRequested = pyqtSignal(object)  # Emits device data
    editRequested = pyqtSignal(object)

    def __init__(self, device_data, parent=None):
        super().__init__(parent)
        self.device_data = device_data  # store device info (name ,id, location)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            DeviceCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E6E9EC;
                padding: 15px;
            }
            DeviceCard:hover {
                border: 1px solid #007BFF;
                background-color: #F8F9FA;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Device name
        name_label = QLabel(self.device_data.get('name', 'Unnamed Device'))
        name_label.setFont(QFont("Arial", 14, QFont.Bold))
        name_label.setStyleSheet("color: #2c3e50;")

        # Location
        location = self.device_data.get('hvac_location', 'No location set')
        location_label = QLabel(f"Location: {location}")
        location_label.setStyleSheet("color: #6c757d; font-size: 12px;")

        # Device ID
        device_id = self.device_data.get('id', 'Unknown')
        id_label = QLabel(f"ID: {device_id}")
        id_label.setStyleSheet("color: #9ca3af; font-size: 10px; font-family: monospace;")
        id_label.setWordWrap(True)

        # Created date
        created_at = self.device_data.get('created_at', '')
        if created_at:
            # formatting the created at date nicely
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                date_str = dt.strftime('%b %d, %Y')
                date_label = QLabel(f"Added: {date_str}")
                date_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
            except:
                date_label = QLabel("")
        else:
            date_label = QLabel("")

        # buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        edit_btn = QPushButton("Edit")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        edit_btn.setCursor(Qt.PointingHandCursor)

        # when clicked, emit signal with the device's data
        edit_btn.clicked.connect(lambda: self.editRequested.emit(self.device_data))

        unclaim_btn = QPushButton("Unclaim")
        unclaim_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #dc3545;
                border: 2px solid #dc3545;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc3545;
                color: white;
            }
        """)
        unclaim_btn.setCursor(Qt.PointingHandCursor)
        # when unclaim btn clicked, emit signal with device data
        unclaim_btn.clicked.connect(lambda: self.unclaimRequested.emit(self.device_data))

        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(unclaim_btn)
        btn_layout.addStretch()

        # Add all to layout
        layout.addWidget(name_label)
        layout.addWidget(location_label)
        layout.addWidget(date_label)
        layout.addWidget(id_label)
        layout.addLayout(btn_layout)

        self.setLayout(layout)


class FindDeviceDialog(QDialog):
    """Dialog for finding and claiming a device"""

    def __init__(self, device_data=None, parent=None):
        super().__init__(parent)
        self.device_data = device_data
        self.is_edit = device_data is not None
        self.setup_ui()

    def setup_ui(self):
        title = "Find Device"
        self.setWindowTitle(title)
        self.setFixedSize(450, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: #F4F7FA;
            }
            QLabel {
                color: #333333;
                font-weight: bold;
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: #FFFFFF;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #007BFF;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")

        # MAC address input
        mac_label = QLabel("MAC Address")
        self.mac_input = QLineEdit()
        self.mac_input.setPlaceholderText("e.g., 1A:BC:D2:3B:3E:4F")

        self.status_label = QLabel("")  # hidden initially
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 10px; border-radius: 6px;")
        self.status_label.hide()

        # Buttons
        btn_layout = QHBoxLayout()

        self.search_btn = QPushButton("Search")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #6c757d;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
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
        btn_layout.addWidget(self.search_btn)

        # Add all to layout
        layout.addWidget(title_label)
        layout.addWidget(mac_label)
        layout.addWidget(self.mac_input)
        layout.addWidget(self.status_label)

        layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_mac_address(self):
        """Return the MAC address of the device"""
        return self.mac_input.text().strip()


class AddEditDeviceDialog(QDialog):
    """Dialog for adding or editing a device"""

    def __init__(self, device_data=None, parent=None):
        super().__init__(parent)
        self.device_data = device_data
        self.is_edit = device_data is not None
        self.setup_ui()

    def setup_ui(self):
        title = "Edit Device" if self.is_edit else "Add New Device"
        self.setWindowTitle(title)
        self.setFixedSize(450, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #F4F7FA;
            }
            QLabel {
                color: #333333;
                font-weight: bold;
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: #FFFFFF;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #007BFF;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")

        # Device name
        name_label = QLabel("Device Name")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Living Room Unit")
        if self.is_edit:
            self.name_input.setText(self.device_data.get('name', ''))

        # Location
        location_label = QLabel("HVAC Location")
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("e.g., Upstairs Hallway")
        if self.is_edit:
            self.location_input.setText(self.device_data.get('hvac_location', ''))

        # Buttons
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Save" if self.is_edit else "Add Device")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #6c757d;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
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
        btn_layout.addWidget(save_btn)

        # Add all to layout
        layout.addWidget(title_label)
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(location_label)
        layout.addWidget(self.location_input)
        layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_data(self):
        """Return the device data from the form"""
        return {
            'name': self.name_input.text().strip(),
            'hvac_location': self.location_input.text().strip()
        }


class DevicesTab(QWidget):
    """Main devices management tab"""
    devicesChanged = pyqtSignal()
    def __init__(self, user_session, parent=None):
        super().__init__(parent)
        self.user_session = user_session
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.supabase.auth.set_session(
            access_token=self.user_session.access_token,
            refresh_token=self.user_session.refresh_token
        )
        self.devices = []
        self.setup_ui()
        self.load_devices()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 90, 30, 30)  # Extra top margin for header

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("    My Devices")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")

        self.device_count = QLabel("0 devices")
        self.device_count.setStyleSheet("""
            background-color: #EBF5FF;
            color: #007BFF;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: bold;
        """)

        add_btn = QPushButton("+ Add Device")
        add_btn.setFixedSize(140, 45)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)

        find_btn = QPushButton("⌕ Find Device")
        find_btn.setFixedSize(140, 45)
        find_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)

        find_btn.setCursor(Qt.PointingHandCursor)
        find_btn.clicked.connect(self.find_device)

        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self.add_device)

        header_layout.addWidget(title)
        header_layout.addWidget(self.device_count)
        header_layout.addStretch()
        header_layout.addWidget(find_btn)
        header_layout.addWidget(add_btn)

        # Scroll area for device cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self.devices_container = QWidget()
        self.devices_layout = QVBoxLayout()
        self.devices_layout.setSpacing(15)
        self.devices_container.setLayout(self.devices_layout)

        scroll.setWidget(self.devices_container)

        # Add to main layout
        layout.addLayout(header_layout)
        layout.addWidget(scroll)

        self.setLayout(layout)

    def load_devices(self):
        """Load devices from Supabase"""
        try:
            response = self.supabase.table("devices") \
                .select("*") \
                .eq("owner_id", self.user_session.user.id) \
                .order("created_at", desc=True) \
                .execute()

            self.devices = response.data if response.data else []
            self.refresh_device_list()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load devices: {str(e)}")

    def refresh_device_list(self):
        """Refresh the device cards display"""
        # Clear existing cards
        while self.devices_layout.count():
            child = self.devices_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Update count
        count = len(self.devices)
        self.device_count.setText(f"{count} device{'s' if count != 1 else ''}")

        # Add device cards
        if count == 0:
            empty_label = QLabel("No devices yet. Click 'Add Device' to get started!")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #6c757d; font-size: 16px; padding: 60px;")
            self.devices_layout.addWidget(empty_label)
        else:
            for device in self.devices:
                card = DeviceCard(device)
                card.unclaimRequested.connect(self.unclaim_device)
                card.editRequested.connect(self.edit_device)
                self.devices_layout.addWidget(card)

        self.devices_layout.addStretch()

    def add_device(self):
        """Show dialog to add a new device"""
        dialog = AddEditDeviceDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()

            if not data['name']:
                QMessageBox.warning(self, "Validation Error", "Device name is required!")
                return

            try:
                # in the event that users add their own device, we write to supabase
                data['owner_id'] = self.user_session.user.id

                response = self.supabase.table("devices").insert(data).execute()

                if response.data:
                    QMessageBox.information(self, "Success", "Device added successfully!")
                    self.load_devices()

                    self.devicesChanged.emit() #emit signal to let dashboard know to update

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add device: {str(e)}")

    def find_device(self):
        """Show dialog to find and claim a device by MAC address"""
        dialog = FindDeviceDialog(parent=self)

        if dialog.exec_() == QDialog.Accepted:
            mac_address = dialog.get_mac_address()

            if not mac_address:
                QMessageBox.warning(self, "Validation Error", "Please enter a MAC address!")
                return

            try:
                # Step 1: Search for the device by MAC address
                response = self.supabase.table("devices") \
                    .select("*") \
                    .eq("device_mac", mac_address) \
                    .execute()

                # Step 2: Check if device was found
                if not response.data or len(response.data) == 0:
                    QMessageBox.warning(
                        self,
                        "Device Not Found",
                        f"No device found with MAC address: {mac_address}\n\n"
                        f"Possible reasons:\n"
                        f"• Device doesn't exist in the system\n"
                        f"• MAC address is incorrect\n"
                        f"• Device is claimed by another user (RLS blocking access)\n\n"
                        f"If you're sure the device exists, check your database permissions."
                    )
                    return

                device = response.data[0]

                # Step 3: Check if device is claimed using BOTH methods for compatibility
                # Some databases might use 'claimed' column, others just 'owner_id'
                is_claimed = device.get('claimed', False) or device.get('owner_id') is not None

                if is_claimed:
                    current_owner = device.get('owner_id')

                    # Check if it's already the current user's device
                    if current_owner == self.user_session.user.id:
                        QMessageBox.information(
                            self,
                            "Already Your Device",
                            f"This device is already in your account!\n\n"
                            f"Device: {device.get('name', 'Unnamed')}\n"
                            f"Location: {device.get('hvac_location', 'Not set')}\n"
                            f"MAC: {mac_address}"
                        )
                        return
                    else:
                        # Claimed by someone else
                        QMessageBox.warning(
                            self,
                            "Device Already Claimed",
                            f"This device is already assigned to another user.\n\n"
                            f"Device: {device.get('name', 'Unnamed')}\n"
                            f"MAC: {mac_address}\n\n"
                            f"Please contact support if you believe this is an error."
                        )
                        return

                # Step 4: Device is available! Ask user if they want to claim it
                reply = QMessageBox.question(
                    self,
                    "Claim Device?",
                    f"✅ Device found and available!\n\n"
                    f"Device Name: {device.get('name', 'Unnamed Device')}\n"
                    f"Location: {device.get('hvac_location', 'Not set')}\n"
                    f"MAC Address: {mac_address}\n\n"
                    f"Would you like to claim this device and add it to your account?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )

                if reply == QMessageBox.Yes:
                    # Step 5: Claim the device by setting owner_id and claimed flag
                    update_data = {
                        "owner_id": self.user_session.user.id,
                        "claimed": True
                    }

                    update_response = self.supabase.table("devices") \
                        .update(update_data) \
                        .eq("id", device['id']) \
                        .execute()

                    if update_response.data:
                        QMessageBox.information(
                            self,
                            "Success!",
                            f"🎉 Device '{device.get('name', 'Unnamed')}' has been successfully added to your account!"
                        )
                        self.load_devices()  # Refresh the device list
                        self.devicesChanged.emit()
                    else:
                        QMessageBox.warning(
                            self,
                            "Update Failed",
                            "Device was found but could not be claimed. Please try again."
                        )

            except Exception as e:
                error_msg = str(e)
                print(f"Error in find_device: {error_msg}")

                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to find/claim device:\n\n{error_msg}\n\n"
                    f"If the device exists but you can't see it, this may be due to "
                    f"database permissions (RLS policy). Please contact your administrator."
                )

    def edit_device(self, device_data):
        """Show dialog to edit a device"""
        dialog = AddEditDeviceDialog(device_data, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()

            if not data['name']:
                QMessageBox.warning(self, "Validation Error", "Device name is required!")
                return

            try:
                response = self.supabase.table("devices") \
                    .update(data) \
                    .eq("id", device_data['id']) \
                    .execute()

                if response.data:
                    QMessageBox.information(self, "Success", "Device updated successfully!")
                    self.load_devices()
                    self.devicesChanged.emit()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update device: {str(e)}")

    def unclaim_device(self, device_data):
        """Unclaim a device after confirmation"""
        reply = QMessageBox.question(
            self,
            "Confirm Unclaim",
            f"Are you sure you want to unclaim '{device_data.get('name')}'?\n\n"
            "This will release the device so others can claim it.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                response = self.supabase.table("devices") \
                    .update({
                    "owner_id": None,
                    "claimed": False  # ✅ Added this!
                    }) \
                    .eq("id", device_data['id']) \
                    .execute()

                QMessageBox.information(self, "Success", "Device unclaimed successfully!")
                self.load_devices()
                self.devicesChanged.emit()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to unclaim device: {str(e)}")