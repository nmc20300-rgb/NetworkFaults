from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QSizePolicy,
    QToolButton,
)

from auth import authenticate, get_user_permissions


class LoginPage(QWidget):
    login_successful = Signal(object)

    # ضع ملف اللوجو هنا
    # مثال: assets/nmc_logo.png
    LOGO_PATH = Path("assets/nmc_logo3.png")

    def __init__(self):
        super().__init__()

        self.setObjectName("loginPage")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(900, 600)

        self.build_ui()

    def build_ui(self):
        # =========================================================
        # Main full-screen layout
        # =========================================================
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # =========================================================
        # LEFT / BRAND PANEL
        # =========================================================
        brand_panel = QFrame()
        brand_panel.setObjectName("brandPanel")
        brand_panel.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        brand_layout = QVBoxLayout(brand_panel)
        brand_layout.setContentsMargins(80, 65, 80, 65)
        brand_layout.setSpacing(0)

        brand_layout.addStretch(1)

        # Logo
        logo = QLabel()
        logo.setObjectName("brandLogo")
        logo.setAlignment(Qt.AlignCenter)
        logo.setMinimumSize(210, 210)

        if self.LOGO_PATH.exists():
            pixmap = QPixmap(str(self.LOGO_PATH))
            if not pixmap.isNull():
                logo.setPixmap(
                    pixmap.scaled(
                        250,
                        250,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
        else:
            logo.setText("NMC")
            logo.setStyleSheet("""
                QLabel#brandLogo {
                    color: white;
                    font-size: 46px;
                    font-weight: 900;
                }
            """)

        brand_layout.addWidget(logo, alignment=Qt.AlignCenter)
        brand_layout.addSpacing(20)

        brand_subtitle = QLabel(
            "نظام إدارة الشبكة والدعم الفني"
        )
        brand_subtitle.setObjectName("brandSubtitle")
        brand_subtitle.setAlignment(Qt.AlignCenter)
        brand_subtitle.setWordWrap(True)
        brand_layout.addWidget(brand_subtitle)

        brand_description = QLabel(
            "إدارة الأجهزة والأعطال والصيانة"
        )
        brand_description.setObjectName("brandDescription")
        brand_description.setAlignment(Qt.AlignCenter)
        brand_description.setWordWrap(True)
        brand_layout.addSpacing(12)
        brand_layout.addWidget(brand_description)

        brand_layout.addStretch(1)



        # =========================================================
        # RIGHT / LOGIN PANEL
        # =========================================================
        login_panel = QFrame()
        login_panel.setObjectName("loginPanel")
        login_panel.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Expanding,
        )

        login_panel_layout = QVBoxLayout(login_panel)
        login_panel_layout.setContentsMargins(70, 50, 70, 50)
        login_panel_layout.setSpacing(0)

        login_panel_layout.addStretch(1)

        # Login card
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(510)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 44, 48, 44)
        card_layout.setSpacing(0)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(45)
        shadow.setOffset(0, 14)
        shadow.setColor(QColor(15, 42, 61, 45))
        card.setGraphicsEffect(shadow)

        # ---------------------------------------------------------
        # Header
        # ---------------------------------------------------------

        welcome = QLabel("مرحباً بك")
        welcome.setObjectName("loginWelcome")
        welcome.setLayoutDirection(Qt.LeftToRight)
        welcome.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        card_layout.addWidget(welcome)

        login_title = QLabel("تسجيل الدخول")
        login_title.setObjectName("loginTitle")
        login_title.setLayoutDirection(Qt.LeftToRight)
        login_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        card_layout.addWidget(login_title)

        login_subtitle = QLabel(
            "قم بإدخال بيانات الدخول للوصول إلى النظام"
            )
        login_subtitle.setObjectName("loginSubtitle")
        login_subtitle.setLayoutDirection(Qt.LeftToRight)
        login_subtitle.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        login_subtitle.setWordWrap(True)

        card_layout.addSpacing(7)
        card_layout.addWidget(login_subtitle)

        card_layout.addSpacing(30)
        # ---------------------------------------------------------
        # Username
        # ---------------------------------------------------------
        username_label = QLabel("اسم المستخدم")
        username_label.setObjectName("fieldLabel")
        card_layout.addWidget(username_label)
        card_layout.addSpacing(7)

        username_wrapper = QFrame()
        username_wrapper.setObjectName("inputWrapper")
        username_layout = QHBoxLayout(username_wrapper)
        username_layout.setContentsMargins(15, 0, 12, 0)
        username_layout.setSpacing(10)

        username_icon = QLabel("")
        username_icon.setObjectName("fieldIcon")
        username_icon.setAlignment(Qt.AlignCenter)
        username_layout.addWidget(username_icon)

        self.username_input = QLineEdit()
        self.username_input.setObjectName("loginInput")
        self.username_input.setPlaceholderText("أدخل اسم المستخدم")
        self.username_input.setMinimumHeight(50)
        self.username_input.setFrame(False)
        self.username_input.setClearButtonEnabled(True)
        username_layout.addWidget(self.username_input, 1)

        card_layout.addWidget(username_wrapper)
        card_layout.addSpacing(16)

        # ---------------------------------------------------------
        # Password
        # ---------------------------------------------------------
        password_label = QLabel("كلمة المرور")
        password_label.setObjectName("fieldLabel")
        card_layout.addWidget(password_label)
        card_layout.addSpacing(7)

        password_wrapper = QFrame()
        password_wrapper.setObjectName("inputWrapper")
        password_layout = QHBoxLayout(password_wrapper)
        password_layout.setContentsMargins(15, 0, 10, 0)
        password_layout.setSpacing(8)

        password_icon = QLabel("")
        password_icon.setObjectName("fieldIcon")
        password_icon.setAlignment(Qt.AlignCenter)
        password_layout.addWidget(password_icon)

        self.password_input = QLineEdit()
        self.password_input.setObjectName("loginInput")
        self.password_input.setPlaceholderText("أدخل كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(50)
        self.password_input.setFrame(False)
        password_layout.addWidget(self.password_input, 1)

        self.password_toggle = QToolButton()
        self.password_toggle.setObjectName("passwordToggle")
        self.password_toggle.setText("إظهار")
        self.password_toggle.setCursor(Qt.PointingHandCursor)
        self.password_toggle.setCheckable(True)
        self.password_toggle.setFixedWidth(52)
        self.password_toggle.toggled.connect(self.toggle_password)
        password_layout.addWidget(self.password_toggle)

        card_layout.addWidget(password_wrapper)
        card_layout.addSpacing(20)

        # ---------------------------------------------------------
        # Error
        # ---------------------------------------------------------
        self.error_label = QLabel()
        self.error_label.setObjectName("loginError")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)
        card_layout.addSpacing(8)

        # ---------------------------------------------------------
        # Login button
        # ---------------------------------------------------------
        self.login_button = QPushButton("تسجيل الدخول")
        self.login_button.setObjectName("loginButton")
        self.login_button.setMinimumHeight(54)
        self.login_button.setCursor(Qt.PointingHandCursor)
        card_layout.addWidget(self.login_button)

        # ---------------------------------------------------------
        # Footer
        # ---------------------------------------------------------
        card_layout.addSpacing(25)

        divider = QFrame()
        divider.setObjectName("footerDivider")
        divider.setFrameShape(QFrame.HLine)
        card_layout.addWidget(divider)

        card_layout.addSpacing(15)



        login_panel_layout.addWidget(
            card,
            alignment=Qt.AlignCenter,
        )

        login_panel_layout.addStretch(1)

        # RTL-safe explicit order:
        # Login panel first visually on the right, branding on the left.
        main_layout.addWidget(login_panel, 5)
        main_layout.addWidget(brand_panel, 6)

        # =========================================================
        # Events
        # =========================================================
        self.login_button.clicked.connect(self.login)
        self.password_input.returnPressed.connect(self.login)
        self.username_input.returnPressed.connect(self.login)

        # =========================================================
        # Styles
        # =========================================================
        self.setStyleSheet("""
            /* =====================================================
               PAGE
               ===================================================== */
            QWidget#loginPage {
                background: #eef5f8;
                font-family: "IBM Plex Sans Arabic", "Segoe UI", Tahoma, Arial;
                color: #183b4f;
            }

            /* =====================================================
               BRAND PANEL
               ===================================================== */
            QFrame#brandPanel {
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 1,
                    stop: 0 #06283b,
                    stop: 0.42 #084d65,
                    stop: 0.72 #086c7d,
                    stop: 1 #087f91
                );
                border: none;
            }

            QLabel#brandLogo {
                background: transparent;
                color: white;
                font-size: 46px;
                font-weight: 900;
            }

            QLabel#brandTitle {
                background: transparent;
                color: #ffffff;
                font-size: 27px;
                font-weight: 800;
                letter-spacing: 0.5px;
            }

            QLabel#brandSubtitle {
                background: transparent;
                color: #d8f4f7;
                font-size: 17px;
                font-weight: 700;
                margin-top: 5px;
            }

            QLabel#brandDescription {
                background: transparent;
                color: #a9dbe2;
                font-size: 12px;
                line-height: 1.5;
            }

            QLabel#brandFooter {
                background: transparent;
                color: rgba(255, 255, 255, 0.55);
                font-size: 10px;
                letter-spacing: 0.5px;
            }

            /* =====================================================
               LOGIN PANEL
               ===================================================== */
            QFrame#loginPanel {
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 1,
                    stop: 0 #f9fcfd,
                    stop: 0.55 #f1f7f9,
                    stop: 1 #eaf3f6
                );
                border: none;
            }

            /* =====================================================
               LOGIN CARD
               ===================================================== */
            QFrame#loginCard {
                background: rgba(255, 255, 255, 0.98);
                border: 1px solid #dcebf0;
                border-radius: 24px;
            }

            QLabel#loginWelcome {
                background: transparent;
                color: #2d9caf;
                font-size: 12px;
                font-weight: 700;
            }

            QLabel#loginTitle {
                background: transparent;
                color: #102f42;
                font-size: 28px;
                font-weight: 900;
            }

            QLabel#loginSubtitle {
                background: transparent;
                color: #7c98a6;
                font-size: 11px;
                font-weight: 500;
            }

            /* =====================================================
               FIELDS
               ===================================================== */
            QLabel#fieldLabel {
                background: transparent;
                color: #3f6172;
                font-size: 11px;
                font-weight: 800;
            }

            QFrame#inputWrapper {
                background: #f6fafc;
                border: 1px solid #d8e7ed;
                border-radius: 13px;
                min-height: 52px;
            }

            QFrame#inputWrapper:focus-within {
                background: #ffffff;
                border: 1.5px solid #16a6ba;
            }

            QLabel#fieldIcon {
                background: transparent;
                color: #69aabb;
                font-size: 14px;
                font-weight: 800;
                min-width: 18px;
            }

            QLineEdit#loginInput {
                background: transparent;
                border: none;
                color: #16394b;
                font-size: 13px;
                font-weight: 500;
                padding: 4px 0;
                selection-background-color: #bdeaf0;
            }

            QLineEdit#loginInput::placeholder {
                color: #a5bac4;
            }

            QToolButton#passwordToggle {
                background: transparent;
                border: none;
                color: #5793a2;
                font-size: 10px;
                font-weight: 700;
                padding: 5px;
            }

            QToolButton#passwordToggle:hover {
                color: #087d91;
            }

            /* =====================================================
               BUTTON
               ===================================================== */
            QPushButton#loginButton {
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 0,
                    stop: 0 #076f83,
                    stop: 0.5 #10a6b7,
                    stop: 1 #076f83
                );
                color: #ffffff;
                border: none;
                border-radius: 13px;
                font-size: 14px;
                font-weight: 900;
                padding: 0 18px;
            }

            QPushButton#loginButton:hover {
                background: #076c7d;
            }

            QPushButton#loginButton:pressed {
                background: #055a69;
            }

            QPushButton#loginButton:disabled {
                background: #a9cfd5;
                color: rgba(255, 255, 255, 0.75);
            }

            /* =====================================================
               ERROR
               ===================================================== */
            QLabel#loginError {
                color: #b33d48;
                background: #fff4f4;
                border: 1px solid #f1c9cd;
                border-radius: 10px;
                padding: 9px 12px;
                font-size: 11px;
                font-weight: 600;
            }

            /* =====================================================
               FOOTER
               ===================================================== */
            QFrame#footerDivider {
                background: #e9f0f3;
                border: none;
                max-height: 1px;
            }

            QLabel#loginFooter {
                background: transparent;
                color: #75919e;
                font-size: 10px;
                font-weight: 600;
            }

            QLabel#loginVersion {
                background: transparent;
                color: #b0c1c8;
                font-size: 9px;
            }

            QLabel#securityHint {
                background: transparent;
                color: #9aadb5;
                font-size: 9px;
                font-weight: 600;
            }
        """)

        self.username_input.setFocus()

    def toggle_password(self, checked):
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.password_toggle.setText("إخفاء")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.password_toggle.setText("إظهار")

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
