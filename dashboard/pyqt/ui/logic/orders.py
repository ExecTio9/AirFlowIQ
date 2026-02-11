from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QMessageBox, QDialog,
    QSpinBox, QTextEdit, QComboBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QDoubleValidator
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime
import json


class ProductCard(QFrame):
    """Individual product card widget"""
    addToCartRequested = pyqtSignal(object)  # Emits product data

    def __init__(self, product_data, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            ProductCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 2px solid #E6E9EC;
                padding: 20px;
            }
            ProductCard:hover {
                border: 2px solid #007BFF;
                background-color: #F8FBFF;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Product name
        name = self.product_data.get('name', 'N/A')
        name_label = QLabel(name)
        name_label.setFont(QFont("Arial", 16, QFont.Bold))
        name_label.setStyleSheet("color: #2c3e50;")
        name_label.setWordWrap(True)

        # SKU
        sku = self.product_data.get('sku', '')
        if sku:
            sku_label = QLabel(f"SKU: {sku}")
            sku_label.setStyleSheet("color: #9ca3af; font-size: 11px; font-family: monospace;")
            layout.addWidget(sku_label)

        # Description
        description = self.product_data.get('description', '')
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #6c757d; font-size: 13px;")
            desc_label.setWordWrap(True)
            desc_label.setMaximumHeight(60)
            layout.addWidget(desc_label)

        # Price
        price_cents = self.product_data.get('price_cents', 0)
        price = price_cents / 100.0
        currency = self.product_data.get('currency', 'USD')

        price_label = QLabel(f"${price:.2f} {currency}")
        price_label.setFont(QFont("Arial", 24, QFont.Bold))
        price_label.setStyleSheet("color: #007BFF;")

        # Product type badge
        product_type = self.product_data.get('product_type', 'product')
        type_badge = QLabel(product_type.upper())
        type_badge.setStyleSheet("""
            background-color: #EBF5FF;
            color: #007BFF;
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        """)
        type_badge.setAlignment(Qt.AlignCenter)

        # Active status
        is_active = self.product_data.get('active', False)
        if is_active:
            status_badge = QLabel("Available")
            status_badge.setStyleSheet("""
                background-color: #d1fae5;
                color: #065f46;
                padding: 6px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            """)
        else:
            status_badge = QLabel("Unavailable")
            status_badge.setStyleSheet("""
                background-color: #fee2e2;
                color: #991b1b;
                padding: 6px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            """)

        # Quantity selector
        qty_layout = QHBoxLayout()
        qty_label = QLabel("Quantity:")
        qty_label.setStyleSheet("color: #6c757d; font-size: 13px; font-weight: 600;")

        self.qty_spinner = QSpinBox()
        self.qty_spinner.setMinimum(1)
        self.qty_spinner.setMaximum(100)
        self.qty_spinner.setValue(1)
        self.qty_spinner.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                background-color: #FFFFFF;
                font-size: 14px;
            }
        """)

        qty_layout.addWidget(qty_label)
        qty_layout.addWidget(self.qty_spinner)
        qty_layout.addStretch()

        # Add to cart button
        add_btn = QPushButton("Add to Cart")
        add_btn.setStyleSheet("""
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
                background-color: #cccccc;
                color: #666666;
            }
        """)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setEnabled(is_active)
        add_btn.clicked.connect(self.add_to_cart)

        # Add all to layout
        layout.addWidget(name_label)
        layout.addWidget(price_label)
        layout.addWidget(type_badge)
        layout.addWidget(status_badge)
        layout.addLayout(qty_layout)
        layout.addStretch()
        layout.addWidget(add_btn)

        self.setLayout(layout)

    def add_to_cart(self):
        """Emit signal with product and quantity"""
        cart_item = {
            'product': self.product_data,
            'quantity': self.qty_spinner.value()
        }
        self.addToCartRequested.emit(cart_item)


class CheckoutDialog(QDialog):
    """Dialog for entering shipping information and completing order"""

    def __init__(self, cart_items, parent=None):
        super().__init__(parent)
        self.cart_items = cart_items
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Checkout - Shipping Information")
        self.setMinimumSize(600, 700)
        self.setStyleSheet("""
            QDialog {
                background-color: #F4F7FA;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit, QTextEdit {
                padding: 12px;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: #FFFFFF;
                font-size: 14px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #007BFF;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Shipping Information")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        form_widget = QWidget()
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        # Full Name
        name_label = QLabel("Full Name *")
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("John Doe")
        form_layout.addWidget(name_label)
        form_layout.addWidget(self.name_input)

        # Address Line 1
        address1_label = QLabel("Address Line 1 *")
        address1_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.address1_input = QLineEdit()
        self.address1_input.setPlaceholderText("123 Main Street")
        form_layout.addWidget(address1_label)
        form_layout.addWidget(self.address1_input)

        # Address Line 2
        address2_label = QLabel("Address Line 2 (Optional)")
        address2_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.address2_input = QLineEdit()
        self.address2_input.setPlaceholderText("Apt 4B")
        form_layout.addWidget(address2_label)
        form_layout.addWidget(self.address2_input)

        # City
        city_label = QLabel("City *")
        city_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("New York")
        form_layout.addWidget(city_label)
        form_layout.addWidget(self.city_input)

        # State and Postal Code (side by side)
        state_postal_layout = QHBoxLayout()

        state_layout = QVBoxLayout()
        state_label = QLabel("State *")
        state_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.state_input = QLineEdit()
        self.state_input.setPlaceholderText("NY")
        self.state_input.setMaxLength(2)
        state_layout.addWidget(state_label)
        state_layout.addWidget(self.state_input)

        postal_layout = QVBoxLayout()
        postal_label = QLabel("Postal Code *")
        postal_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.postal_input = QLineEdit()
        self.postal_input.setPlaceholderText("10001")
        postal_layout.addWidget(postal_label)
        postal_layout.addWidget(self.postal_input)

        state_postal_layout.addLayout(state_layout)
        state_postal_layout.addLayout(postal_layout)
        form_layout.addLayout(state_postal_layout)

        # Country
        country_label = QLabel("Country *")
        country_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.country_input = QComboBox()
        self.country_input.addItems(["USA", "Canada", "Mexico", "Other"])
        self.country_input.setStyleSheet("""
            QComboBox {
                padding: 12px;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: #FFFFFF;
                font-size: 14px;
            }
        """)
        form_layout.addWidget(country_label)
        form_layout.addWidget(self.country_input)

        # Phone
        phone_label = QLabel("Phone Number *")
        phone_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("(555) 123-4567")
        form_layout.addWidget(phone_label)
        form_layout.addWidget(self.phone_input)

        # Notes (optional)
        notes_label = QLabel("Order Notes (Optional)")
        notes_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Any special instructions...")
        self.notes_input.setMaximumHeight(80)
        form_layout.addWidget(notes_label)
        form_layout.addWidget(self.notes_input)

        form_widget.setLayout(form_layout)
        scroll.setWidget(form_widget)
        layout.addWidget(scroll)

        # Order summary
        summary_label = QLabel("Order Summary")
        summary_label.setFont(QFont("Arial", 14, QFont.Bold))
        summary_label.setStyleSheet("color: #2c3e50; margin-top: 10px;")
        layout.addWidget(summary_label)

        # Calculate totals
        subtotal = sum(item['product']['price_cents'] * item['quantity'] for item in self.cart_items)
        tax = int(subtotal * 0.08)  # 8% tax
        shipping = 999  # $9.99 shipping
        total = subtotal + tax + shipping

        summary_text = f"""
        Subtotal: ${subtotal / 100:.2f}
        Tax (8%): ${tax / 100:.2f}
        Shipping: ${shipping / 100:.2f}
        â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        Total: ${total / 100:.2f}
        """

        summary_display = QLabel(summary_text)
        summary_display.setStyleSheet("""
            background-color: #FFFFFF;
            padding: 15px;
            border-radius: 8px;
            color: #2c3e50;
            font-size: 13px;
            font-family: monospace;
        """)
        layout.addWidget(summary_display)

        # Buttons
        btn_layout = QHBoxLayout()

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

        place_order_btn = QPushButton("Place Order")
        place_order_btn.setStyleSheet("""
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
        place_order_btn.setCursor(Qt.PointingHandCursor)
        place_order_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(place_order_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_shipping_info(self):
        """Validate and return shipping information"""
        name = self.name_input.text().strip()
        address1 = self.address1_input.text().strip()
        address2 = self.address2_input.text().strip()
        city = self.city_input.text().strip()
        state = self.state_input.text().strip().upper()
        postal = self.postal_input.text().strip()
        country = self.country_input.currentText()
        phone = self.phone_input.text().strip()
        notes = self.notes_input.toPlainText().strip()

        # Validation
        if not name:
            return None, "Full name is required"
        if not address1:
            return None, "Address is required"
        if not city:
            return None, "City is required"
        if not state or len(state) != 2:
            return None, "State must be a 2-letter code (e.g., NY)"
        if not postal:
            return None, "Postal code is required"
        if not phone:
            return None, "Phone number is required"

        return {
            'ship_to_name': name,
            'ship_to_line1': address1,
            'ship_to_line2': address2 or None,
            'ship_to_city': city,
            'ship_to_state': state,
            'ship_to_postal': postal,
            'ship_to_country': country,
            'ship_to_phone': phone,
            'notes': notes or None
        }, None


class OrderCard(QFrame):
    """Individual order history card"""

    def __init__(self, order_data, parent=None):
        super().__init__(parent)
        self.order_data = order_data
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            OrderCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E6E9EC;
                padding: 20px;
            }
            OrderCard:hover {
                border: 1px solid #007BFF;
                background-color: #F8FBFF;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Header with Order ID and Status
        header_layout = QHBoxLayout()

        order_id = self.order_data.get('id', 'N/A')
        order_label = QLabel(f"Order #{order_id[:13]}...")
        order_label.setFont(QFont("Arial", 13, QFont.Bold))
        order_label.setStyleSheet("color: #2c3e50;")

        # Status badge
        status = self.order_data.get('status', 'pending')
        status_colors = {
            'pending': '#f59e0b',
            'confirmed': '#3b82f6',
            'processing': '#8b5cf6',
            'shipped': '#06b6d4',
            'delivered': '#22c55e',
            'cancelled': '#ef4444'
        }
        status_color = status_colors.get(status.lower(), '#6b7280')

        status_badge = QLabel(status.upper())
        status_badge.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        """)
        status_badge.setAlignment(Qt.AlignCenter)
        status_badge.setFixedWidth(120)

        header_layout.addWidget(order_label)
        header_layout.addStretch()
        header_layout.addWidget(status_badge)

        # Order details
        total_cents = self.order_data.get('total_cents', 0)
        currency = self.order_data.get('currency', 'USD')
        total_label = QLabel(f"Total: ${total_cents / 100:.2f} {currency}")
        total_label.setFont(QFont("Arial", 16, QFont.Bold))
        total_label.setStyleSheet("color: #007BFF;")

        # Shipping address
        ship_to_name = self.order_data.get('ship_to_name', 'N/A')
        ship_to_city = self.order_data.get('ship_to_city', 'N/A')
        ship_to_state = self.order_data.get('ship_to_state', 'N/A')

        address_label = QLabel(f"Ship to: {ship_to_name}, {ship_to_city}, {ship_to_state}")
        address_label.setStyleSheet("color: #6c757d; font-size: 12px;")

        # Date
        created_at = self.order_data.get('created_at', '')
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                date_label = QLabel(f"Ordered: {dt.strftime('%b %d, %Y at %I:%M %p')}")
                date_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
            except:
                date_label = QLabel("")
        else:
            date_label = QLabel("")

        # Add to layout
        layout.addLayout(header_layout)
        layout.addWidget(total_label)
        layout.addWidget(address_label)
        layout.addWidget(date_label)

        self.setLayout(layout)


class OrdersTab(QWidget):
    """Main orders tab with product browsing and order management"""

    def __init__(self, user_session, parent=None):
        super().__init__(parent)
        self.user_session = user_session
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.supabase.auth.set_session(
            access_token=self.user_session.access_token,
            refresh_token=self.user_session.refresh_token
        )
        self.products = []
        self.orders = []
        self.cart = []
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 90, 30, 30)  # Extra top margin for header

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("    Orders & Products")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")

        # Cart button
        self.cart_btn = QPushButton("Cart (0)")
        self.cart_btn.setFixedSize(140, 45)
        self.cart_btn.setStyleSheet("""
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
        self.cart_btn.setCursor(Qt.PointingHandCursor)
        self.cart_btn.clicked.connect(self.show_cart)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.cart_btn)

        main_layout.addLayout(header_layout)

        # Tab widget
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E6E9EC;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #F8F9FA;
                color: #6c757d;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #007BFF;
            }
            QTabBar::tab:hover {
                background-color: #EBF5FF;
            }
        """)

        # Products Tab
        products_tab = QWidget()
        products_layout = QVBoxLayout()
        products_layout.setSpacing(15)
        products_layout.setContentsMargins(20, 20, 20, 20)

        products_header = QLabel("Available Products")
        products_header.setFont(QFont("Arial", 18, QFont.Bold))
        products_header.setStyleSheet("color: #2c3e50;")
        products_layout.addWidget(products_header)

        # Products scroll area
        products_scroll = QScrollArea()
        products_scroll.setWidgetResizable(True)
        products_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.products_container = QWidget()
        self.products_layout = QHBoxLayout()
        self.products_layout.setSpacing(15)
        self.products_container.setLayout(self.products_layout)

        products_scroll.setWidget(self.products_container)
        products_layout.addWidget(products_scroll)

        products_tab.setLayout(products_layout)

        # Order History Tab
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        history_layout.setSpacing(15)
        history_layout.setContentsMargins(20, 20, 20, 20)

        history_header = QLabel("Order History")
        history_header.setFont(QFont("Arial", 18, QFont.Bold))
        history_header.setStyleSheet("color: #2c3e50;")
        history_layout.addWidget(history_header)

        # Orders scroll area
        orders_scroll = QScrollArea()
        orders_scroll.setWidgetResizable(True)
        orders_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.orders_container = QWidget()
        self.orders_layout = QVBoxLayout()
        self.orders_layout.setSpacing(15)
        self.orders_container.setLayout(self.orders_layout)

        orders_scroll.setWidget(self.orders_container)
        history_layout.addWidget(orders_scroll)

        history_tab.setLayout(history_layout)

        # Add tabs
        tab_widget.addTab(products_tab, "Shop")
        tab_widget.addTab(history_tab, "My Orders")

        main_layout.addWidget(tab_widget)

        self.setLayout(main_layout)

    def load_data(self):
        """Load products and orders"""
        self.load_products()
        self.load_orders()

    def load_products(self):
        """Load products from Supabase"""
        try:
            response = self.supabase.table("products") \
                .select("*") \
                .eq("active", True) \
                .order("name") \
                .execute()

            self.products = response.data if response.data else []
            self.refresh_products_list()

        except Exception as e:
            print(f"Error loading products: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load products: {str(e)}")

    def load_orders(self):
        """Load user's order history"""
        try:
            response = self.supabase.table("orders") \
                .select("*") \
                .eq("customer_id", self.user_session.user.id) \
                .order("created_at", desc=True) \
                .execute()

            self.orders = response.data if response.data else []
            self.refresh_orders_list()

        except Exception as e:
            print(f"Error loading orders: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load orders: {str(e)}")

    def refresh_products_list(self):
        """Refresh products display"""
        # Clear existing cards
        while self.products_layout.count():
            child = self.products_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if len(self.products) == 0:
            empty_label = QLabel("No products available")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #6c757d; font-size: 16px; padding: 60px;")
            self.products_layout.addWidget(empty_label)
        else:
            for product in self.products:
                card = ProductCard(product)
                card.setMinimumWidth(280)
                card.setMaximumWidth(350)
                card.addToCartRequested.connect(self.add_to_cart)
                self.products_layout.addWidget(card)

        self.products_layout.addStretch()

    def refresh_orders_list(self):
        """Refresh orders display"""
        # Clear existing cards
        while self.orders_layout.count():
            child = self.orders_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if len(self.orders) == 0:
            empty_label = QLabel("No orders yet. Start shopping!")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #6c757d; font-size: 16px; padding: 60px;")
            self.orders_layout.addWidget(empty_label)
        else:
            for order in self.orders:
                card = OrderCard(order)
                self.orders_layout.addWidget(card)

        self.orders_layout.addStretch()

    def add_to_cart(self, cart_item):
        """Add item to cart"""
        # Check if product already in cart
        for item in self.cart:
            if item['product']['id'] == cart_item['product']['id']:
                item['quantity'] += cart_item['quantity']
                QMessageBox.information(
                    self,
                    "Added to Cart",
                    f"Updated quantity for {cart_item['product']['name']}"
                )
                self.update_cart_button()
                return

        # Add new item
        self.cart.append(cart_item)
        QMessageBox.information(
            self,
            "Added to Cart",
            f"Added {cart_item['quantity']}x {cart_item['product']['name']} to cart"
        )
        self.update_cart_button()

    def update_cart_button(self):
        """Update cart button with item count"""
        total_items = sum(item['quantity'] for item in self.cart)
        self.cart_btn.setText(f"ðŸ›’ Cart ({total_items})")

    def show_cart(self):
        """Show cart and checkout"""
        if len(self.cart) == 0:
            QMessageBox.information(self, "Empty Cart", "Your cart is empty. Add some products first!")
            return

        # Show checkout dialog
        dialog = CheckoutDialog(self.cart, self)
        if dialog.exec_() == QDialog.Accepted:
            shipping_info, error = dialog.get_shipping_info()

            if error:
                QMessageBox.warning(self, "Validation Error", error)
                return

            # Place the order
            self.place_order(shipping_info)

    def place_order(self, shipping_info):
        """Create order in Supabase"""
        try:
            # Calculate totals
            subtotal = sum(item['product']['price_cents'] * item['quantity'] for item in self.cart)
            tax = int(subtotal * 0.08)  # 8% tax
            shipping = 999  # $9.99 shipping
            total = subtotal + tax + shipping

            # Get currency from first product
            currency = self.cart[0]['product'].get('currency', 'USD')

            # Create order
            order_data = {
                'customer_id': self.user_session.user.id,
                'status': 'pending',
                'currency': currency,
                'subtotal_cents': subtotal,
                'tax_cents': tax,
                'shipping_cents': shipping,
                'total_cents': total,
                'created_by': self.user_session.user.id,
                **shipping_info
            }

            order_response = self.supabase.table("orders").insert(order_data).execute()

            if not order_response.data:
                raise Exception("Failed to create order")

            order_id = order_response.data[0]['id']

            # Create order items
            order_items = []
            for item in self.cart:
                line_total = item['product']['price_cents'] * item['quantity']
                order_item = {
                    'order_id': order_id,
                    'product_id': item['product']['id'],
                    'qty': item['quantity'],
                    'unit_price_cents': item['product']['price_cents'],
                    'line_total_cents': line_total,
                    'meta': {}
                }
                order_items.append(order_item)

            # Insert all order items
            self.supabase.table("order_items").insert(order_items).execute()

            # Clear cart
            self.cart = []
            self.update_cart_button()

            # Reload orders
            self.load_orders()

            # Success message
            QMessageBox.information(
                self,
                "Order Placed",
                f"Your order has been placed successfully!\n\nOrder ID: {order_id[:13]}...\nTotal: ${total / 100:.2f}"
            )

        except Exception as e:
            print(f"Error placing order: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to place order:\n{str(e)}"
            )