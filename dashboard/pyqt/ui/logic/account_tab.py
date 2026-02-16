from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY


class ChangePasswordDialog(QDialog):
    """Dialog for changing password"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Change Password")
        self.setFixedSize(400, 300)
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
        title = QLabel("Change Password")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")

        # New password
        new_pass_label = QLabel("New Password")
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Enter new password")
        self.new_password_input.setEchoMode(QLineEdit.Password)

        # Confirm password
        confirm_pass_label = QLabel("Confirm Password")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm new password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)

        # Buttons
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Change Password")
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
        layout.addWidget(title)
        layout.addWidget(new_pass_label)
        layout.addWidget(self.new_password_input)
        layout.addWidget(confirm_pass_label)
        layout.addWidget(self.confirm_password_input)
        layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_password(self):
        """Return the new password if valid"""
        new_pass = self.new_password_input.text()
        confirm_pass = self.confirm_password_input.text()

        if new_pass != confirm_pass:
            return None, "Passwords do not match"

        if len(new_pass) < 6:
            return None, "Password must be at least 6 characters"

        return new_pass, None


class AccountTab(QWidget):
    """Account management tab"""

    signOutRequested = pyqtSignal()  # Signal to trigger logout

    def __init__(self, user_session, parent=None):
        super().__init__(parent)
        self.user_session = user_session
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.supabase.auth.set_session(
            access_token=self.user_session.access_token,
            refresh_token=self.user_session.refresh_token
        )
        self.setup_ui()
        self.load_profile()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 90, 30, 30)  # Extra top margin for header

        # Header
        title = QLabel("     Account Settings")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # Horizontal layout for Profile and Security cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        # ========================================
        # LEFT SIDE: Profile Card
        # ========================================
        profile_card = QFrame()
        profile_card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E6E9EC;
                padding: 20px;
            }
        """)

        profile_layout = QVBoxLayout()
        profile_layout.setSpacing(15)

        # Profile Header
        profile_header = QLabel("Profile Information")
        profile_header.setFont(QFont("Arial", 16, QFont.Bold))
        profile_header.setStyleSheet("color: #2c3e50;")

        # Username field
        username_label = QLabel("Display Name")
        username_label.setStyleSheet("color: #6c757d; font-size: 12px; font-weight: 600;")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your display name")
        self.username_input.setStyleSheet("""
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

        # Email field (read-only)
        email_label = QLabel("Email")
        email_label.setStyleSheet("color: #6c757d; font-size: 12px; font-weight: 600;")

        self.email_input = QLineEdit()
        self.email_input.setText(self.user_session.user.email)
        self.email_input.setReadOnly(True)
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: #F8F9FA;
                font-size: 14px;
                color: #6c757d;
            }
        """)

        # User ID (read-only)
        user_id_label = QLabel("User ID")
        user_id_label.setStyleSheet("color: #6c757d; font-size: 12px; font-weight: 600;")

        self.user_id_input = QLineEdit()
        self.user_id_input.setText(self.user_session.user.id)
        self.user_id_input.setReadOnly(True)
        self.user_id_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: #F8F9FA;
                font-size: 11px;
                color: #9ca3af;
                font-family: monospace;
            }
        """)

        # Save button
        save_profile_btn = QPushButton("Save Profile")
        save_profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        save_profile_btn.setCursor(Qt.PointingHandCursor)
        save_profile_btn.clicked.connect(self.save_profile)

        profile_layout.addWidget(profile_header)
        profile_layout.addWidget(username_label)
        profile_layout.addWidget(self.username_input)
        profile_layout.addWidget(email_label)
        profile_layout.addWidget(self.email_input)
        profile_layout.addWidget(user_id_label)
        profile_layout.addWidget(self.user_id_input)
        profile_layout.addStretch()
        profile_layout.addWidget(save_profile_btn)

        profile_card.setLayout(profile_layout)

        # ========================================
        # RIGHT SIDE: Security Card
        # ========================================
        security_card = QFrame()
        security_card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E6E9EC;
                padding: 20px;
            }
        """)

        security_layout = QVBoxLayout()
        security_layout.setSpacing(15)

        security_header = QLabel("Security")
        security_header.setFont(QFont("Arial", 16, QFont.Bold))
        security_header.setStyleSheet("color: #2c3e50;")

        change_password_btn = QPushButton("Change Password")
        change_password_btn.setStyleSheet("""
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
        change_password_btn.setCursor(Qt.PointingHandCursor)
        change_password_btn.clicked.connect(self.change_password)

        security_layout.addWidget(security_header)
        security_layout.addWidget(change_password_btn)
        security_layout.addStretch()

        security_card.setLayout(security_layout)

        # Add both cards to horizontal layout
        cards_layout.addWidget(profile_card, stretch=1)
        cards_layout.addWidget(security_card, stretch=1)

        layout.addLayout(cards_layout)

        # ========================================
        # Sign Out Button (full width at bottom)
        # ========================================
        signout_btn = QPushButton("Sign Out")
        signout_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        signout_btn.setCursor(Qt.PointingHandCursor)
        signout_btn.clicked.connect(self.sign_out)

        layout.addWidget(signout_btn)
        layout.addStretch()

        self.setLayout(layout)

    def load_profile(self):
        """Load user profile from Supabase"""
        try:
            response = self.supabase.table("profiles") \
                .select("full_name") \
                .eq("id", self.user_session.user.id) \
                .execute()

            if response.data and len(response.data) > 0:
                full_name = response.data[0].get("full_name", "")
                self.username_input.setText(full_name)
                print(f"Loaded profile: {full_name}")

        except Exception as e:
            print(f"Error loading profile: {e}")

    def save_profile(self):
        """Save profile changes to Supabase"""
        new_username = self.username_input.text().strip()

        if not new_username:
            QMessageBox.warning(self, "Validation Error", "Display name cannot be empty!")
            return

        try:
            response = self.supabase.table("profiles") \
                .update({"full_name": new_username}) \
                .eq("id", self.user_session.user.id) \
                .execute()

            if response.data:
                QMessageBox.information(
                    self,
                    "Success",
                    "Profile updated successfully!"
                )
                print(f"Profile updated: {new_username}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to update profile:\n{str(e)}"
            )

    def change_password(self):
        """Show dialog to change password"""
        dialog = ChangePasswordDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_password, error = dialog.get_password()

            if error:
                QMessageBox.warning(self, "Validation Error", error)
                return

            try:
                response = self.supabase.auth.update_user({
                    "password": new_password
                })

                if response.user:
                    QMessageBox.information(
                        self,
                        "Success",
                        "Password changed successfully!"
                    )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to change password:\n{str(e)}"
                )

    def sign_out(self):
        """Sign out and emit signal"""
        reply = QMessageBox.question(
            self,
            "Confirm Sign Out",
            "Are you sure you want to sign out?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Sign out from Supabase
                self.supabase.auth.sign_out()
                print("User signed out")

                # Emit signal to close the main window
                self.signOutRequested.emit()

            except Exception as e:
                print(f"Error signing out: {e}")
                # Still emit signal even if API call fails
                self.signOutRequested.emit()