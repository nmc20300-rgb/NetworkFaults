from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
)
from PySide6.QtGui import QColor

from auth import authenticate, get_user_permissions


class LoginPage(QWidget):

    login_successful = Signal(object)

    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self.build_ui()

    def build_ui(self):

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignCenter)

        # =================================================
        # Card
        # =================================================

        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(440)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(44, 40, 44, 40)
        card_layout.setSpacing(0)

        # Drop shadow on card
        card_shadow = QGraphicsDropShadowEffect()
        card_shadow.setBlurRadius(50)
        card_shadow.setOffset(0, 12)
        card_shadow.setColor(QColor(100, 160, 190, 80))
        card.setGraphicsEffect(card_shadow)

        # -------------------------------------------------
        # Brand Section
        # -------------------------------------------------

        brand_widget = QWidget()
        brand_widget.setObjectName("brandWidget")
        brand_layout = QVBoxLayout(brand_widget)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(6)
        brand_layout.setAlignment(Qt.AlignCenter)

        logo = QLabel("📡")
        logo.setObjectName("loginLogo")
        logo.setAlignment(Qt.AlignCenter)
        brand_layout.addWidget(logo)

        title = QLabel("الشبكة")
        title.setObjectName("loginTitle")
        title.setAlignment(Qt.AlignCenter)
        brand_layout.addWidget(title)

        subtitle = QLabel("نظام إدارة الأجهزة والأعطال")
        subtitle.setObjectName("loginSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        brand_layout.addWidget(subtitle)

        card_layout.addWidget(brand_widget)
        card_layout.addSpacing(32)

        # -------------------------------------------------
        # Divider
        # -------------------------------------------------

        divider = QFrame()
        divider.setObjectName("cardDivider")
        divider.setFrameShape(QFrame.HLine)
        card_layout.addWidget(divider)
        card_layout.addSpacing(26)

        # -------------------------------------------------
        # Username Field
        # -------------------------------------------------

        username_label = QLabel("اسم المستخدم")
        username_label.setObjectName("fieldLabel")
        card_layout.addWidget(username_label)
        card_layout.addSpacing(6)

        username_wrapper = QWidget()
        username_wrapper.setObjectName("inputWrapper")
        username_wrapper_layout = QHBoxLayout(username_wrapper)
        username_wrapper_layout.setContentsMargins(14, 0, 14, 0)
        username_wrapper_layout.setSpacing(10)

        username_icon = QLabel("👤")
        username_icon.setObjectName("fieldIcon")
        username_wrapper_layout.addWidget(username_icon)

        self.username_input = QLineEdit()
        self.username_input.setObjectName("loginInput")
        self.username_input.setPlaceholderText("أدخل اسم المستخدم")
        self.username_input.setMinimumHeight(48)
        self.username_input.setFrame(False)
        username_wrapper_layout.addWidget(self.username_input)

        card_layout.addWidget(username_wrapper)
        card_layout.addSpacing(14)

        # -------------------------------------------------
        # Password Field
        # -------------------------------------------------

        password_label = QLabel("كلمة المرور")
        password_label.setObjectName("fieldLabel")
        card_layout.addWidget(password_label)
        card_layout.addSpacing(6)

        password_wrapper = QWidget()
        password_wrapper.setObjectName("inputWrapper")
        password_wrapper_layout = QHBoxLayout(password_wrapper)
        password_wrapper_layout.setContentsMargins(14, 0, 14, 0)
        password_wrapper_layout.setSpacing(10)

        password_icon = QLabel("🔒")
        password_icon.setObjectName("fieldIcon")
        password_wrapper_layout.addWidget(password_icon)

        self.password_input = QLineEdit()
        self.password_input.setObjectName("loginInput")
        self.password_input.setPlaceholderText("أدخل كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(48)
        self.password_input.setFrame(False)
        password_wrapper_layout.addWidget(self.password_input)

        card_layout.addWidget(password_wrapper)
        card_layout.addSpacing(20)

        # -------------------------------------------------
        # Error Banner
        # -------------------------------------------------

        self.error_label = QLabel()
        self.error_label.setObjectName("loginError")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)

        # -------------------------------------------------
        # Login Button
        # -------------------------------------------------

        self.login_button = QPushButton("تسجيل الدخول")
        self.login_button.setObjectName("loginButton")
        self.login_button.setMinimumHeight(52)
        self.login_button.setCursor(Qt.PointingHandCursor)
        card_layout.addWidget(self.login_button)
        card_layout.addSpacing(24)

        # -------------------------------------------------
        # Footer
        # -------------------------------------------------

        footer_divider = QFrame()
        footer_divider.setObjectName("footerDivider")
        footer_divider.setFrameShape(QFrame.HLine)
        card_layout.addWidget(footer_divider)
        card_layout.addSpacing(16)

        footer = QLabel("Network Management System  ·  v1.0")
        footer.setObjectName("loginFooter")
        footer.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(footer)

        main_layout.addWidget(card)

        # =================================================
        # Events
        # =================================================

        self.login_button.clicked.connect(self.login)
        self.password_input.returnPressed.connect(self.login)
        self.username_input.returnPressed.connect(self.login)

        # =================================================
        # Stylesheet
        # =================================================

        self.setStyleSheet("""
            /* ── Page background ──────────────────────── */
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:0.6, y2:1,
                    stop:0   #e8f4fb,
                    stop:0.5 #dceef8,
                    stop:1   #cfe5f4
                );
                font-family: "IBM Plex Sans Arabic", "Segoe UI", Tahoma, Arial;
                font-size: 13px;
                color: #2c4a5e;
            }

            /* ── Card ─────────────────────────────────── */
            QFrame#loginCard {
                background: #ffffff;
                border: 1px solid rgba(26, 143, 168, 0.15);
                border-radius: 20px;
            }

            /* ── Brand widget ─────────────────────────── */
            QWidget#brandWidget {
                background: transparent;
            }

            QLabel#loginLogo {
                font-size: 50px;
                padding-bottom: 2px;
                background: transparent;
            }

            QLabel#loginTitle {
                color: #0f2a3d;
                font-size: 28px;
                font-weight: 800;
                letter-spacing: 1px;
                background: transparent;
            }

            QLabel#loginSubtitle {
                color: #7097ae;
                font-size: 11px;
                letter-spacing: 0.5px;
                background: transparent;
            }

            /* ── Dividers ─────────────────────────────── */
            QFrame#cardDivider {
                background-color: #e2eef5;
                border: none;
                max-height: 1px;
            }

            QFrame#footerDivider {
                background-color: #edf4f9;
                border: none;
                max-height: 1px;
            }

            /* ── Field labels ─────────────────────────── */
            QLabel#fieldLabel {
                color: #4a7a95;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1.5px;
                background: transparent;
            }

            /* ── Input wrappers ───────────────────────── */
            QWidget#inputWrapper {
                background-color: #f4f9fc;
                border: 1.5px solid #cde0ec;
                border-radius: 12px;
                min-height: 50px;
            }

            QWidget#inputWrapper:focus-within {
                border: 1.5px solid #26c6da;
                background-color: #ffffff;
            }

            QLabel#fieldIcon {
                font-size: 16px;
                background: transparent;
            }

            /* ── Inputs ───────────────────────────────── */
            QLineEdit#loginInput {
                background: transparent;
                border: none;
                color: #0f2a3d;
                font-size: 13px;
                font-weight: 500;
                padding: 4px 0;
                selection-background-color: #b2e0ea;
            }

            QLineEdit#loginInput::placeholder {
                color: #9bbcce;
            }

            /* ── Login button ─────────────────────────── */
            QPushButton#loginButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0891b2,
                    stop:0.5 #26c6da,
                    stop:1 #0891b2
                );
                color: #ffffff;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QPushButton#loginButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0e7490,
                    stop:0.5 #0891b2,
                    stop:1 #0e7490
                );
            }

            QPushButton#loginButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #155e75,
                    stop:0.5 #0e7490,
                    stop:1 #155e75
                );
            }

            QPushButton#loginButton:disabled {
                background: #b2dde6;
                color: rgba(255,255,255,0.6);
            }

            /* ── Error banner ─────────────────────────── */
            QLabel#loginError {
                color: #b33a3a;
                background-color: #fff2f2;
                border: 1px solid #f5c0c0;
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 12px;
                font-weight: 600;
                margin-bottom: 10px;
            }

            /* ── Footer ───────────────────────────────── */
            QLabel#loginFooter {
                color: #9bbcce;
                font-size: 10px;
                letter-spacing: 0.5px;
                background: transparent;
            }
        """)

        self.username_input.setFocus()

    def login(self):

        username = self.username_input.text().strip()
        password = self.password_input.text()

        self.error_label.hide()

        if not username:
            self.show_error("من فضلك أدخل اسم المستخدم.")
            self.username_input.setFocus()
            return

        if not password:
            self.show_error("من فضلك أدخل كلمة المرور.")
            self.password_input.setFocus()
            return

        self.login_button.setEnabled(False)

        try:
            user = authenticate(username, password)

            if user is None:
                self.show_error(
                    "اسم المستخدم أو كلمة المرور غير صحيحة."
                )
                self.password_input.clear()
                self.password_input.setFocus()
                return

            permissions = get_user_permissions(
                user["id"],
                user["role_id"],
            )

            user["permissions"] = permissions
            self.login_successful.emit(user)

        except Exception as error:
            self.show_error(
                f"حدث خطأ أثناء تسجيل الدخول:\n{error}"
            )

        finally:
            self.login_button.setEnabled(True)

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()