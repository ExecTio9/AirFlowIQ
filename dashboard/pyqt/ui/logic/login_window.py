from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import os
import sys


def get_resource_path(relative_path):
    """Get absolute path to resource - works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ForgotPasswordDialog(QDialog):
    """Dialog for password reset"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Reset Password")
        self.setFixedSize(500, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #F4F7FA;
            }
            QLabel {
                color: #333333;
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
            QTextEdit {
                padding: 12px;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: #FFF9E6;
                font-size: 12px;
                color: #6c757d;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        title = QLabel("Reset Your Password")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50;")

        # Description
        description = QLabel(
            "Enter your email address and we'll send you\n"
            "a link to reset your password."
        )
        description.setFont(QFont("Arial", 11))
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #6c757d;")

        # Email field
        email_label = QLabel("Email Address")
        email_label.setFont(QFont("Arial", 11, QFont.Bold))

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("you@example.com")
        self.email_input.returnPressed.connect(self.send_reset_email)

        # Info box
        info_box = QTextEdit()
        info_box.setReadOnly(True)
        info_box.setMaximumHeight(80)
        info_box.setHtml("""
            <p style='margin: 5px;'>
            <b>Note:</b> Make sure to check your spam folder if you don't see the email.
            The reset link will expire in 1 hour.
            </p>
        """)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")

        # Buttons
        btn_layout = QHBoxLayout()

        self.send_btn = QPushButton("Send Reset Link")
        self.send_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.clicked.connect(self.send_reset_email)

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
        btn_layout.addWidget(self.send_btn)

        # Add all to layout
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(10)
        layout.addWidget(email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(info_box)
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def set_loading(self, is_loading):
        """Disable form during API call"""
        self.send_btn.setEnabled(not is_loading)
        self.email_input.setEnabled(not is_loading)

        if is_loading:
            self.send_btn.setText("Sending...")
            self.status_label.setText("Please wait...")
            self.status_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        else:
            self.send_btn.setText("Send Reset Link")

    def send_reset_email(self):
        """Send password reset email via Supabase"""
        email = self.email_input.text().strip()

        if not email:
            self.status_label.setText("Please enter your email address")
            self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
            return

        # Basic email validation
        if "@" not in email or "." not in email:
            self.status_label.setText("Please enter a valid email address")
            self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
            return

        self.set_loading(True)

        try:
            # Supabase will send a password reset email
            self.supabase.auth.reset_password_email(
                email,
                options={
                    'redirect_to': 'https://ire-odes.github.io/password-reset-test/'
                }
            )

            # Show success message
            QMessageBox.information(
                self,
                "Reset Link Sent",
                f"If an account exists for {email}, you will receive a password reset link shortly.\n\n"
                "Please check your email (and spam folder) for instructions."
            )

            self.status_label.setText("Email sent! Check your inbox.")
            self.status_label.setStyleSheet("color: #22c55e; font-size: 12px;")

            # Close dialog after short delay
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(2000, self.accept)

        except Exception as e:
            error_msg = str(e)
            print(f"Password reset error: {error_msg}")

            # Generic error message for security (don't reveal if email exists)
            self.status_label.setText(
                "If an account exists for this email, a reset link will be sent."
            )
            self.status_label.setStyleSheet("color: #22c55e; font-size: 12px;")

            self.set_loading(False)


class LoginWindow(QDialog):
    loginSuccessful = pyqtSignal(object)  # Emits session data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.user_session = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("AirFlow IQ Analytics - Login")
        self.setFixedSize(550, 800)  # Increased height for logo
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
            QLabel {
                color: #333333;
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
            QPushButton {
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#loginBtn {
                background-color: #007BFF;
                color: #FFFFFF;
                border: none;
            }
            QPushButton#loginBtn:hover {
                background-color: #0056b3;
            }
            QPushButton#signupBtn {
                background-color: #FFFFFF;
                color: #007BFF;
                border: 2px solid #007BFF;
            }
            QPushButton#signupBtn:hover {
                background-color: #EBF5FF;
            }
            QPushButton#forgotBtn {
                background-color: transparent;
                color: #007BFF;
                border: none;
                padding: 5px;
                font-size: 13px;
                text-decoration: underline;
            }
            QPushButton#forgotBtn:hover {
                color: #0056b3;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Logo
        logo_label = QLabel()
        logo_path = get_resource_path("assets/logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(400, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText("AirFlow IQ")
            logo_label.setFont(QFont("Arial", 22, QFont.Bold))
            logo_label.setStyleSheet("color: #007BFF;")
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # Catchphrase
        catchphrase = QLabel("Clean Air. Smarter Energy.")
        catchphrase.setFont(QFont("Arial", 13))
        catchphrase.setAlignment(Qt.AlignCenter)
        catchphrase.setStyleSheet("color: #6c757d; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(catchphrase)

        # Header
        title = QLabel("Welcome to AirFlow IQ")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")

        subtitle = QLabel("Sign in to access your dashboard")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #6c757d; margin-bottom: 20px;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #E0E0E0;")
        layout.addWidget(line)

        # Email field
        email_label = QLabel("Email")
        email_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("you@example.com")
        self.email_input.returnPressed.connect(self.handle_login)

        layout.addWidget(email_label)
        layout.addWidget(self.email_input)

        # Password field
        password_label = QLabel("Password")
        password_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.handle_login)

        layout.addWidget(password_label)
        layout.addWidget(self.password_input)

        # Forgot password link
        forgot_layout = QHBoxLayout()
        forgot_layout.addStretch()
        self.forgot_btn = QPushButton("Forgot Password?")
        self.forgot_btn.setObjectName("forgotBtn")
        self.forgot_btn.setCursor(Qt.PointingHandCursor)
        self.forgot_btn.clicked.connect(self.show_forgot_password)
        forgot_layout.addWidget(self.forgot_btn)
        layout.addLayout(forgot_layout)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
        layout.addWidget(self.status_label)

        # Login button
        self.login_btn = QPushButton("Log In")
        self.login_btn.setObjectName("loginBtn")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)

        # Sign up button
        self.signup_btn = QPushButton("Create Account")
        self.signup_btn.setObjectName("signupBtn")
        self.signup_btn.setCursor(Qt.PointingHandCursor)
        self.signup_btn.clicked.connect(self.handle_signup)
        layout.addWidget(self.signup_btn)

        layout.addStretch()
        self.setLayout(layout)

    def show_forgot_password(self):
        """Show forgot password dialog"""
        dialog = ForgotPasswordDialog(self)
        dialog.exec_()

    def set_loading(self, is_loading):
        """Disable buttons during API calls"""
        self.login_btn.setEnabled(not is_loading)
        self.signup_btn.setEnabled(not is_loading)
        self.email_input.setEnabled(not is_loading)
        self.password_input.setEnabled(not is_loading)
        self.forgot_btn.setEnabled(not is_loading)

        if is_loading:
            self.login_btn.setText("Loading...")
            self.status_label.setText("Please wait...")
            self.status_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        else:
            self.login_btn.setText("Log In")

    def handle_login(self):
        """Handle user login"""
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            self.status_label.setText("Please enter email and password")
            self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
            return

        self.set_loading(True)

        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            # Check for session instead of user
            if response.session:
                self.user_session = response.session

                # DEBUG: Print user information
                print("=" * 60)
                print("LOGIN SUCCESSFUL!")
                print("=" * 60)
                print(f"User ID (profiles.id): {response.session.user.id}")
                print(f"User Email: {response.session.user.email}")
                print(f"Access Token: {response.session.access_token[:20]}...")
                print("=" * 60)

                self.status_label.setText("Login successful!")
                self.status_label.setStyleSheet("color: #22c55e; font-size: 12px;")

                # Emit session, not the full response
                self.loginSuccessful.emit(response.session)

                # Close dialog after short delay
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(500, self.accept)
            else:
                self.status_label.setText("Login failed. No session returned.")
                self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
                self.set_loading(False)

        except Exception as e:
            error_msg = str(e)
            print(f"Login error: {error_msg}")
            if "Invalid login credentials" in error_msg:
                self.status_label.setText("Invalid email or password")
            elif "Email not confirmed" in error_msg:
                self.status_label.setText("Please confirm your email first")
            else:
                self.status_label.setText(f"Error: {error_msg}")

            self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
            self.set_loading(False)


    def handle_signup(self):
        """Open browser-based signup page"""
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl

        QDesktopServices.openUrl(
            QUrl("https://ire-odes.github.io/password-reset-test/signup.html")
        )

        QMessageBox.information(
            self,
            "Create Account",
            "A browser window has been opened to create your account.\n\n"
            "After confirming your email, return here to log in."
    )