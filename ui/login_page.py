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

    LOGO_PATH = Path("assets/nmc_logo3.png")

    def __init__(self):
        super().__init__()

        self.setObjectName("loginPage")
        self.setLayoutDirection(Qt.RightToLeft)

        # =====================================================
        # الصفحة تتمدد بالكامل مع نافذة Login
        # =====================================================

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.setMinimumSize(700, 500)

        # حجم اللوجو الأصلي
        self.logo_pixmap = QPixmap()

        # حفظ الـ font sizes الأصلية
        self.original_title_size = 28
        self.original_welcome_size = 12
        self.original_label_size = 11
        self.original_input_size = 13
        self.original_button_size = 14

        self.build_ui()

    # =========================================================
    # UI
    # =========================================================

    def build_ui(self):

        # =====================================================
        # Main Layout
        # =====================================================

        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(0)

        # =====================================================
        # BRAND PANEL
        # =====================================================

        self.brand_panel = QFrame()
        self.brand_panel.setObjectName("brandPanel")

        self.brand_panel.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.brand_layout = QVBoxLayout(
            self.brand_panel
        )

        self.brand_layout.setContentsMargins(
            50,
            45,
            50,
            45,
        )

        self.brand_layout.setSpacing(0)

        self.brand_layout.addStretch(1)

        # -----------------------------------------------------
        # Logo
        # -----------------------------------------------------

        self.logo = QLabel()

        self.logo.setObjectName("brandLogo")

        self.logo.setAlignment(
            Qt.AlignCenter
        )

        self.logo.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        self.logo.setMinimumHeight(120)

        if self.LOGO_PATH.exists():

            pixmap = QPixmap(
                str(self.LOGO_PATH)
            )

            if not pixmap.isNull():
                self.logo_pixmap = pixmap

        if self.logo_pixmap.isNull():

            self.logo.setText("NMC")

            self.logo.setStyleSheet(
                """
                QLabel#brandLogo {
                    color: white;
                    font-size: 46px;
                    font-weight: 900;
                }
                """
            )

        self.brand_layout.addWidget(
            self.logo,
            alignment=Qt.AlignCenter,
        )

        self.brand_layout.addSpacing(20)

        # -----------------------------------------------------
        # Brand Subtitle
        # -----------------------------------------------------

        self.brand_subtitle = QLabel(
            "نظام إدارة الشبكة والدعم الفني"
        )

        self.brand_subtitle.setObjectName(
            "brandSubtitle"
        )

        self.brand_subtitle.setAlignment(
            Qt.AlignCenter
        )

        self.brand_subtitle.setWordWrap(True)

        self.brand_layout.addWidget(
            self.brand_subtitle
        )

        # -----------------------------------------------------
        # Brand Description
        # -----------------------------------------------------

        self.brand_description = QLabel(
            "إدارة الأجهزة والأعطال والصيانة"
        )

        self.brand_description.setObjectName(
            "brandDescription"
        )

        self.brand_description.setAlignment(
            Qt.AlignCenter
        )

        self.brand_description.setWordWrap(True)

        self.brand_layout.addSpacing(12)

        self.brand_layout.addWidget(
            self.brand_description
        )

        self.brand_layout.addStretch(1)

        # =====================================================
        # LOGIN PANEL
        # =====================================================

        self.login_panel = QFrame()

        self.login_panel.setObjectName(
            "loginPanel"
        )

        self.login_panel.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.login_panel_layout = QVBoxLayout(
            self.login_panel
        )

        self.login_panel_layout.setContentsMargins(
            35,
            35,
            35,
            35,
        )

        self.login_panel_layout.setSpacing(0)

        self.login_panel_layout.addStretch(1)

        # =====================================================
        # LOGIN CARD
        # =====================================================

        self.card = QFrame()

        self.card.setObjectName(
            "loginCard"
        )

        # =====================================================
        # أهم تعديل:
        # الكارت يسمح لنفسه بالتمدد
        # =====================================================

        self.card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Maximum,
        )

        self.card.setMinimumWidth(380)

        self.card.setMaximumWidth(680)

        self.card_layout = QVBoxLayout(
            self.card
        )

        self.card_layout.setContentsMargins(
            48,
            44,
            48,
            44,
        )

        self.card_layout.setSpacing(0)

        # -----------------------------------------------------
        # Shadow
        # -----------------------------------------------------

        shadow = QGraphicsDropShadowEffect()

        shadow.setBlurRadius(45)
        shadow.setOffset(0, 14)

        shadow.setColor(
            QColor(
                15,
                42,
                61,
                45,
            )
        )

        self.card.setGraphicsEffect(
            shadow
        )

        # =====================================================
        # HEADER
        # =====================================================

        self.welcome = QLabel(
            "مرحباً بك"
        )

        self.welcome.setObjectName(
            "loginWelcome"
        )

        self.welcome.setAlignment(
            Qt.AlignLeft |
            Qt.AlignVCenter
        )

        self.card_layout.addWidget(
            self.welcome
        )

        self.login_title = QLabel(
            "تسجيل الدخول"
        )

        self.login_title.setObjectName(
            "loginTitle"
        )

        self.login_title.setAlignment(
            Qt.AlignLeft |
            Qt.AlignVCenter
        )

        self.card_layout.addWidget(
            self.login_title
        )

        self.login_subtitle = QLabel(
            "قم بإدخال بيانات الدخول للوصول إلى النظام"
        )

        self.login_subtitle.setObjectName(
            "loginSubtitle"
        )

        self.login_subtitle.setAlignment(
            Qt.AlignLeft |
            Qt.AlignVCenter
        )

        self.login_subtitle.setWordWrap(True)

        self.card_layout.addSpacing(7)

        self.card_layout.addWidget(
            self.login_subtitle
        )

        self.card_layout.addSpacing(30)

        # =====================================================
        # USERNAME
        # =====================================================

        username_label = QLabel(
            "اسم المستخدم"
        )

        username_label.setObjectName(
            "fieldLabel"
        )

        self.card_layout.addWidget(
            username_label
        )

        self.card_layout.addSpacing(7)

        self.username_wrapper = QFrame()

        self.username_wrapper.setObjectName(
            "inputWrapper"
        )

        username_layout = QHBoxLayout(
            self.username_wrapper
        )

        username_layout.setContentsMargins(
            15,
            0,
            12,
            0,
        )

        username_layout.setSpacing(10)

        username_icon = QLabel("")

        username_icon.setObjectName(
            "fieldIcon"
        )

        username_icon.setAlignment(
            Qt.AlignCenter
        )

        username_layout.addWidget(
            username_icon
        )

        self.username_input = QLineEdit()

        self.username_input.setObjectName(
            "loginInput"
        )

        self.username_input.setPlaceholderText(
            "أدخل اسم المستخدم"
        )

        self.username_input.setMinimumHeight(
            50
        )

        self.username_input.setFrame(False)

        self.username_input.setClearButtonEnabled(
            True
        )

        username_layout.addWidget(
            self.username_input,
            1,
        )

        self.card_layout.addWidget(
            self.username_wrapper
        )

        self.card_layout.addSpacing(16)

        # =====================================================
        # PASSWORD
        # =====================================================

        password_label = QLabel(
            "كلمة المرور"
        )

        password_label.setObjectName(
            "fieldLabel"
        )

        self.card_layout.addWidget(
            password_label
        )

        self.card_layout.addSpacing(7)

        self.password_wrapper = QFrame()

        self.password_wrapper.setObjectName(
            "inputWrapper"
        )

        password_layout = QHBoxLayout(
            self.password_wrapper
        )

        password_layout.setContentsMargins(
            15,
            0,
            10,
            0,
        )

        password_layout.setSpacing(8)

        password_icon = QLabel("")

        password_icon.setObjectName(
            "fieldIcon"
        )

        password_icon.setAlignment(
            Qt.AlignCenter
        )

        password_layout.addWidget(
            password_icon
        )

        self.password_input = QLineEdit()

        self.password_input.setObjectName(
            "loginInput"
        )

        self.password_input.setPlaceholderText(
            "أدخل كلمة المرور"
        )

        self.password_input.setEchoMode(
            QLineEdit.Password
        )

        self.password_input.setMinimumHeight(
            50
        )

        self.password_input.setFrame(False)

        password_layout.addWidget(
            self.password_input,
            1,
        )

        self.password_toggle = QToolButton()

        self.password_toggle.setObjectName(
            "passwordToggle"
        )

        self.password_toggle.setText(
            "إظهار"
        )

        self.password_toggle.setCursor(
            Qt.PointingHandCursor
        )

        self.password_toggle.setCheckable(
            True
        )

        self.password_toggle.setFixedWidth(
            52
        )

        self.password_toggle.toggled.connect(
            self.toggle_password
        )

        password_layout.addWidget(
            self.password_toggle
        )

        self.card_layout.addWidget(
            self.password_wrapper
        )

        self.card_layout.addSpacing(20)

        # =====================================================
        # ERROR
        # =====================================================

        self.error_label = QLabel()

        self.error_label.setObjectName(
            "loginError"
        )

        self.error_label.setAlignment(
            Qt.AlignCenter
        )

        self.error_label.setWordWrap(True)

        self.error_label.hide()

        self.card_layout.addWidget(
            self.error_label
        )

        self.card_layout.addSpacing(8)

        # =====================================================
        # LOGIN BUTTON
        # =====================================================

        self.login_button = QPushButton(
            "تسجيل الدخول"
        )

        self.login_button.setObjectName(
            "loginButton"
        )

        self.login_button.setMinimumHeight(
            54
        )

        self.login_button.setCursor(
            Qt.PointingHandCursor
        )

        self.card_layout.addWidget(
            self.login_button
        )

        # =====================================================
        # FOOTER
        # =====================================================

        self.card_layout.addSpacing(25)

        divider = QFrame()

        divider.setObjectName(
            "footerDivider"
        )

        divider.setFrameShape(
            QFrame.HLine
        )

        self.card_layout.addWidget(
            divider
        )

        # =====================================================
        # Add Card
        # =====================================================

        self.login_panel_layout.addWidget(
            self.card,
            0,
            Qt.AlignHCenter,
        )

        self.login_panel_layout.addStretch(1)

        # =====================================================
        # Main Panels
        # =====================================================

        main_layout.addWidget(
            self.login_panel,
            5,
        )

        main_layout.addWidget(
            self.brand_panel,
            6,
        )

        # =====================================================
        # Events
        # =====================================================

        self.login_button.clicked.connect(
            self.login
        )

        self.password_input.returnPressed.connect(
            self.login
        )

        self.username_input.returnPressed.connect(
            self.login
        )

        # =====================================================
        # Styles
        # =====================================================

        self.setStyleSheet(
            """
            /* =================================================
               PAGE
               ================================================= */

            QWidget#loginPage {
                background: #eef5f8;
                font-family:
                    "IBM Plex Sans Arabic",
                    "Segoe UI",
                    Tahoma,
                    Arial;
                color: #183b4f;
            }

            /* =================================================
               BRAND PANEL
               ================================================= */

            QFrame#brandPanel {
                background: qlineargradient(
                    x1: 0,
                    y1: 0,
                    x2: 1,
                    y2: 1,
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

            QLabel#brandSubtitle {
                background: transparent;
                color: #d8f4f7;
                font-size: 17px;
                font-weight: 700;
            }

            QLabel#brandDescription {
                background: transparent;
                color: #a9dbe2;
                font-size: 12px;
                font-weight: 500;
            }

            /* =================================================
               LOGIN PANEL
               ================================================= */

            QFrame#loginPanel {
                background: qlineargradient(
                    x1: 0,
                    y1: 0,
                    x2: 1,
                    y2: 1,
                    stop: 0 #f9fcfd,
                    stop: 0.55 #f1f7f9,
                    stop: 1 #eaf3f6
                );

                border: none;
            }

            /* =================================================
               LOGIN CARD
               ================================================= */

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

            /* =================================================
               FIELDS
               ================================================= */

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

            /* =================================================
               LOGIN BUTTON
               ================================================= */

            QPushButton#loginButton {
                background: qlineargradient(
                    x1: 0,
                    y1: 0,
                    x2: 1,
                    y2: 0,
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

            /* =================================================
               ERROR
               ================================================= */

            QLabel#loginError {
                color: #b33d48;
                background: #fff4f4;
                border: 1px solid #f1c9cd;
                border-radius: 10px;
                padding: 9px 12px;
                font-size: 11px;
                font-weight: 600;
            }

            /* =================================================
               FOOTER
               ================================================= */

            QFrame#footerDivider {
                background: #e9f0f3;
                border: none;
                max-height: 1px;
            }
            """
        )

        self.username_input.setFocus()

        # أول ضبط للحجم
        self.update_responsive_layout()

    # =========================================================
    # Responsive
    # =========================================================

    def resizeEvent(self, event):

        super().resizeEvent(event)

        self.update_responsive_layout()

    def update_responsive_layout(self):

        width = self.width()
        height = self.height()

        # =====================================================
        # معرفة عرض Login Panel الحقيقي
        # =====================================================

        panel_width = self.login_panel.width()

        if panel_width <= 0:
            panel_width = int(width * 0.45)

        # =====================================================
        # LARGE SCREEN
        # =====================================================

        if width >= 1600:

            card_margin = 58
            brand_margin = 90
            logo_size = 280

            title_size = 30
            welcome_size = 13
            label_size = 12
            input_size = 14
            button_size = 15
            subtitle_size = 18

            max_card_width = 800

        elif width >= 1200:

            card_margin = 50
            brand_margin = 70
            logo_size = 250

            title_size = 28
            welcome_size = 12
            label_size = 11
            input_size = 13
            button_size = 14
            subtitle_size = 17

            max_card_width = 760

        # =====================================================
        # MEDIUM SCREEN
        # =====================================================

        elif width >= 900:

            card_margin = 36
            brand_margin = 45
            logo_size = 200

            title_size = 25
            welcome_size = 11
            label_size = 10
            input_size = 12
            button_size = 13
            subtitle_size = 15

            max_card_width = 560

        # =====================================================
        # SMALL SCREEN
        # =====================================================

        else:

            card_margin = 24
            brand_margin = 25
            logo_size = 150

            title_size = 22
            welcome_size = 10
            label_size = 10
            input_size = 11
            button_size = 12
            subtitle_size = 13

            max_card_width = 500

        # =====================================================
        # أهم جزء:
        # حساب عرض الكارت بناءً على Login Panel
        # =====================================================

        card_width = int(
            panel_width * 0.90
        )

        # أقل عرض
        minimum_card_width = 380

        # في الشاشات الصغيرة جدًا
        if panel_width < 500:

            minimum_card_width = max(
                300,
                panel_width - 40,
            )

        card_width = max(
            minimum_card_width,
            card_width,
        )

        card_width = min(
            max_card_width,
            card_width,
        )

        # منع خروج الكارت خارج الـ Panel
        available_width = max(
            300,
            panel_width - 30,
        )

        card_width = min(
            card_width,
            available_width,
        )

        # =====================================================
        # Card Width
        # =====================================================

        self.card.setMinimumWidth(
            min(
                minimum_card_width,
                card_width,
            )
        )

        self.card.setMaximumWidth(
            card_width
        )

        # =====================================================
        # Card Margins
        # =====================================================

        self.card_layout.setContentsMargins(
            card_margin,
            card_margin,
            card_margin,
            card_margin,
        )

        # =====================================================
        # Panel Margins
        # =====================================================

        panel_margin = max(
            15,
            card_margin // 2,
        )

        self.login_panel_layout.setContentsMargins(
            panel_margin,
            panel_margin,
            panel_margin,
            panel_margin,
        )

        # =====================================================
        # Brand Margins
        # =====================================================

        self.brand_layout.setContentsMargins(
            brand_margin,
            max(
                25,
                brand_margin,
            ),
            brand_margin,
            max(
                25,
                brand_margin,
            ),
        )

        # =====================================================
        # Logo
        # =====================================================

        if not self.logo_pixmap.isNull():

            self.logo.setPixmap(
                self.logo_pixmap.scaled(
                    logo_size,
                    logo_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )

            self.logo.setMinimumHeight(
                min(
                    logo_size + 10,
                    max(
                        120,
                        int(height * 0.35),
                    ),
                )
            )

        # =====================================================
        # Responsive Fonts
        # =====================================================

        self.login_title.setStyleSheet(
            f"""
            QLabel#loginTitle {{
                background: transparent;
                color: #102f42;
                font-size: {title_size}px;
                font-weight: 900;
            }}
            """
        )

        self.welcome.setStyleSheet(
            f"""
            QLabel#loginWelcome {{
                background: transparent;
                color: #2d9caf;
                font-size: {welcome_size}px;
                font-weight: 700;
            }}
            """
        )

        self.brand_subtitle.setStyleSheet(
            f"""
            QLabel#brandSubtitle {{
                background: transparent;
                color: #d8f4f7;
                font-size: {subtitle_size}px;
                font-weight: 700;
            }}
            """
        )

        # =====================================================
        # Input Fonts
        # =====================================================

        input_style = f"""
        QLineEdit#loginInput {{
            background: transparent;
            border: none;
            color: #16394b;
            font-size: {input_size}px;
            font-weight: 500;
            padding: 4px 0;
            selection-background-color: #bdeaf0;
        }}

        QLineEdit#loginInput::placeholder {{
            color: #a5bac4;
        }}
        """

        self.username_input.setStyleSheet(
            input_style
        )

        self.password_input.setStyleSheet(
            input_style
        )

        # =====================================================
        # Button
        # =====================================================

        self.login_button.setStyleSheet(
            f"""
            QPushButton#loginButton {{
                background: qlineargradient(
                    x1: 0,
                    y1: 0,
                    x2: 1,
                    y2: 0,
                    stop: 0 #076f83,
                    stop: 0.5 #10a6b7,
                    stop: 1 #076f83
                );

                color: #ffffff;
                border: none;
                border-radius: 13px;
                font-size: {button_size}px;
                font-weight: 900;
                padding: 0 18px;
            }}

            QPushButton#loginButton:hover {{
                background: #076c7d;
            }}

            QPushButton#loginButton:pressed {{
                background: #055a69;
            }}

            QPushButton#loginButton:disabled {{
                background: #a9cfd5;
                color: rgba(255, 255, 255, 0.75);
            }}
            """
        )

    # =========================================================
    # Password
    # =========================================================

    def toggle_password(self, checked):

        if checked:

            self.password_input.setEchoMode(
                QLineEdit.Normal
            )

            self.password_toggle.setText(
                "إخفاء"
            )

        else:

            self.password_input.setEchoMode(
                QLineEdit.Password
            )

            self.password_toggle.setText(
                "إظهار"
            )

    # =========================================================
    # Login
    # =========================================================

    def login(self):

        username = (
            self.username_input
            .text()
            .strip()
        )

        password = (
            self.password_input
            .text()
        )

        self.error_label.hide()

        # =====================================================
        # Username
        # =====================================================

        if not username:

            self.show_error(
                "من فضلك أدخل اسم المستخدم."
            )

            self.username_input.setFocus()

            return

        # =====================================================
        # Password
        # =====================================================

        if not password:

            self.show_error(
                "من فضلك أدخل كلمة المرور."
            )

            self.password_input.setFocus()

            return

        self.login_button.setEnabled(
            False
        )

        try:

            # =================================================
            # Authentication
            # =================================================

            user = authenticate(
                username,
                password,
            )

            if user is None:

                self.show_error(
                    "اسم المستخدم أو كلمة المرور غير صحيحة."
                )

                self.password_input.clear()

                self.password_input.setFocus()

                return

            # =================================================
            # Permissions
            # =================================================

            permissions = get_user_permissions(
                user["id"],
                user["role_id"],
            )

            user["permissions"] = permissions

            # =================================================
            # Login Success
            # =================================================

            self.login_successful.emit(
                user
            )

        except Exception as error:

            self.show_error(
                f"حدث خطأ أثناء تسجيل الدخول:\n{error}"
            )

        finally:

            self.login_button.setEnabled(
                True
            )

    # =========================================================
    # Error
    # =========================================================

    def show_error(self, message):

        self.error_label.setText(
            message
        )

        self.error_label.show()