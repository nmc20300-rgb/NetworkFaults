import sys
import os

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QFrame,
    QGraphicsDropShadowEffect,
    QMessageBox,
)

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase

from database import (
    initialize_database,
    write_audit_log,
)

from ui.theme import Theme

from ui.login_page import LoginPage
from ui.dashboard_page import DashboardPage
from ui.devices_page import DevicesPage
from ui.faults_page import FaultsPage
from ui.spare_parts_page import SparePartsPage
from ui.users_page import UsersPage
from ui.permissions_page import PermissionsPage
from ui.logs_page import LogsPage


class MainWindow(QMainWindow):

    logout_requested = Signal()

    def __init__(self, user):

        super().__init__()

        self.current_user = user

        self.setWindowTitle(
            "الشبكة - نظام إدارة الأجهزة والأعطال"
        )

        self.resize(1400, 850)

        self.setLayoutDirection(
            Qt.RightToLeft
        )

        central = QWidget()

        self.setCentralWidget(
            central
        )

        main_layout = QHBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            0, 0, 0, 0
        )

        main_layout.setSpacing(
            0
        )

        # =================================================
        # Sidebar
        # =================================================

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)

        sidebar_layout = QVBoxLayout(
            sidebar
        )

        sidebar_layout.setContentsMargins(
            0, 0, 0, 0
        )

        sidebar_layout.setSpacing(
            0
        )

        # -------------------------------------------------
        # Logo / Brand Area
        # -------------------------------------------------

        brand_widget = QWidget()
        brand_widget.setObjectName(
            "sidebarBrand"
        )

        brand_layout = QVBoxLayout(
            brand_widget
        )

        brand_layout.setContentsMargins(
            20, 28, 20, 20
        )

        brand_layout.setSpacing(
            4
        )

        brand_layout.setAlignment(
            Qt.AlignCenter
        )

        icon_badge = QLabel("📡")
        icon_badge.setObjectName(
            "brandIcon"
        )

        icon_badge.setAlignment(
            Qt.AlignCenter
        )

        brand_layout.addWidget(
            icon_badge
        )

        title = QLabel("الشبكة")
        title.setObjectName(
            "sidebarTitle"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        brand_layout.addWidget(
            title
        )

        subtitle = QLabel(
            "نظام إدارة الأجهزة والأعطال"
        )

        subtitle.setObjectName(
            "sidebarSubtitle"
        )

        subtitle.setAlignment(
            Qt.AlignCenter
        )

        subtitle.setWordWrap(
            True
        )

        brand_layout.addWidget(
            subtitle
        )

        sidebar_layout.addWidget(
            brand_widget
        )

        # -------------------------------------------------
        # User Card
        # -------------------------------------------------

        user_name = (
            user.get("full_name")
            or user.get("username")
        )

        role_name = user.get(
            "role_name",
            ""
        )

        user_card = QWidget()

        user_card.setObjectName(
            "userCard"
        )

        user_card_layout = QHBoxLayout(
            user_card
        )

        user_card_layout.setContentsMargins(
            16, 12, 16, 12
        )

        user_card_layout.setSpacing(
            12
        )

        avatar = QLabel("👤")

        avatar.setObjectName(
            "userAvatar"
        )

        avatar.setAlignment(
            Qt.AlignCenter
        )

        avatar.setFixedSize(
            QSize(40, 40)
        )

        user_card_layout.addWidget(
            avatar
        )

        user_text_widget = QWidget()

        user_text_layout = QVBoxLayout(
            user_text_widget
        )

        user_text_layout.setContentsMargins(
            0, 0, 0, 0
        )

        user_text_layout.setSpacing(
            2
        )

        user_name_label = QLabel(
            user_name
        )

        user_name_label.setObjectName(
            "userName"
        )

        user_name_label.setAlignment(
            Qt.AlignLeading | Qt.AlignVCenter
        )

        user_role_label = QLabel(
            role_name
        )

        user_role_label.setObjectName(
            "userRole"
        )

        is_role_rtl = any("\u0600" <= c <= "\u06FF" for c in role_name)
        role_align = Qt.AlignLeading if is_role_rtl else Qt.AlignRight
        user_role_label.setAlignment(
            role_align | Qt.AlignVCenter
        )

        user_text_layout.addWidget(
            user_name_label
        )

        user_text_layout.addWidget(
            user_role_label
        )

        user_card_layout.addWidget(
            user_text_widget
        )

        user_card_wrapper = QWidget()

        user_card_wrapper.setObjectName(
            "userCardWrapper"
        )

        user_card_wrapper_layout = QVBoxLayout(
            user_card_wrapper
        )

        user_card_wrapper_layout.setContentsMargins(
            16, 0, 16, 16
        )

        user_card_wrapper_layout.addWidget(
            user_card
        )

        sidebar_layout.addWidget(
            user_card_wrapper
        )

        # -------------------------------------------------
        # Section Label
        # -------------------------------------------------

        nav_section_label = QLabel(
            "القائمة الرئيسية"
        )

        nav_section_label.setObjectName(
            "sectionLabel"
        )

        nav_section_label.setAlignment(
            Qt.AlignLeading | Qt.AlignVCenter
        )

        nav_section_label.setContentsMargins(
            20, 8, 20, 6
        )

        sidebar_layout.addWidget(
            nav_section_label
        )

        # -------------------------------------------------
        # Navigation Buttons
        # -------------------------------------------------

        nav_container = QWidget()

        nav_container.setObjectName(
            "navContainer"
        )

        nav_layout = QVBoxLayout(
            nav_container
        )

        nav_layout.setContentsMargins(
            12, 4, 12, 4
        )

        nav_layout.setSpacing(
            4
        )

        self.btn_home = QPushButton(
            " الرئيسية"
        )

        self.btn_devices = QPushButton(
            "الأجهزة"
        )

        self.btn_faults = QPushButton(
            " الأعطال"
        )

        self.btn_spare_parts = QPushButton(
            "  قطع الغيار"
        )

        self.btn_users = QPushButton(
            " إدارة المستخدمين"
        )

        self.btn_permissions = QPushButton(
            " الصلاحيات"
        )

        self.btn_logs = QPushButton(
            " سجل العمليات"
        )

        buttons = (
            self.btn_home,
            self.btn_devices,
            self.btn_faults,
            self.btn_spare_parts,
            self.btn_users,
            self.btn_permissions,
            self.btn_logs,
        )

        for button in buttons:

            button.setObjectName(
                "navButton"
            )

            button.setCheckable(
                True
            )

            button.setAutoExclusive(
                True
            )

            button.setCursor(
                Qt.PointingHandCursor
            )

            button.setMinimumHeight(
                46
            )

            nav_layout.addWidget(
                button
            )

        sidebar_layout.addWidget(
            nav_container
        )

        sidebar_layout.addStretch()

        # -------------------------------------------------
        # Footer / Logout
        # -------------------------------------------------

        footer_widget = QWidget()

        footer_widget.setObjectName(
            "sidebarFooterWidget"
        )

        footer_layout = QVBoxLayout(
            footer_widget
        )

        footer_layout.setContentsMargins(
            12, 10, 12, 16
        )

        footer_layout.setSpacing(
            10
        )

        footer_divider = QFrame()

        footer_divider.setFrameShape(
            QFrame.HLine
        )

        footer_divider.setObjectName(
            "footerDivider"
        )

        footer_layout.addWidget(
            footer_divider
        )

        self.btn_logout = QPushButton(
            "  🚪   تسجيل الخروج"
        )

        self.btn_logout.setObjectName(
            "logoutButton"
        )

        self.btn_logout.setCursor(
            Qt.PointingHandCursor
        )

        self.btn_logout.setMinimumHeight(
            44
        )

        self.btn_logout.clicked.connect(
            self.handle_logout
        )

        footer_layout.addWidget(
            self.btn_logout
        )

        sidebar_layout.addWidget(
            footer_widget
        )

        # =================================================
        # Sidebar Style
        # =================================================

        sidebar.setStyleSheet(
            """
            QWidget#sidebar {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0   #0f1e2e,
                    stop:0.5 #132639,
                    stop:1   #0b1825
                );
                border-left: 1px solid #1e3a52;
            }

            QWidget#sidebarBrand {
                background: transparent;
            }

            QLabel#brandIcon {
                font-size: 34px;
                padding-bottom: 4px;
            }

            QLabel#sidebarTitle {
                color: #e8f4fd;
                font-size: 22px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QLabel#sidebarSubtitle {
                color: #6a90aa;
                font-size: 10px;
                letter-spacing: 0.5px;
            }

            QWidget#userCardWrapper {
                background: transparent;
            }

            QWidget#userCard {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #182f44,
                    stop:1 #1a3549
                );
                border: 1px solid #244766;
                border-radius: 12px;
            }

            QLabel#userAvatar {
                font-size: 22px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e4d6b,
                    stop:1 #1a3f5a
                );
                border: 1px solid #2d6a8a;
                border-radius: 20px;
                padding: 4px;
            }

            QLabel#userName {
                color: #e4f0f8;
                font-size: 13px;
                font-weight: 700;
            }

            QLabel#userRole {
                color: #4da3c4;
                font-size: 10px;
                font-weight: 500;
            }

            QLabel#sectionLabel {
                color: #365a72;
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 2px;
                padding: 8px 20px 4px 20px;
            }

            QWidget#navContainer {
                background: transparent;
            }

            QPushButton#navButton {
                color: #8aacbf;
                background-color: transparent;
                text-align: left;
                padding: 10px 14px;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton#navButton:hover {
                color: #d4ecf7;
                background-color: rgba(
                    45, 100, 140, 0.35
                );
                border: 1px solid rgba(
                    60, 130, 170, 0.25
                );
            }

            QPushButton#navButton:pressed {
                background-color: rgba(
                    45, 100, 140, 0.55
                );
            }

            QPushButton#navButton:checked {
                color: #e8f7fd;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(
                        38, 198, 218, 0.18
                    ),
                    stop:1 rgba(
                        38, 198, 218, 0.06
                    )
                );
                border: 1px solid rgba(
                    38, 198, 218, 0.30
                );
                border-right: 3px solid #26c6da;
                font-weight: 700;
            }

            QPushButton#navButton:checked:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(
                        38, 198, 218, 0.25
                    ),
                    stop:1 rgba(
                        38, 198, 218, 0.10
                    )
                );
            }

            QWidget#sidebarFooterWidget {
                background: transparent;
            }

            QFrame#footerDivider {
                color: #1e3a52;
                background-color: #1e3a52;
                border: none;
                height: 1px;
                margin-bottom: 6px;
            }

            QPushButton#logoutButton {
                color: #f87171;
                background-color: rgba(
                    239, 68, 68, 0.10
                );
                border: 1px solid rgba(
                    239, 68, 68, 0.25
                );
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 700;
                text-align: left;
            }

            QPushButton#logoutButton:hover {
                color: #fca5a5;
                background-color: rgba(
                    239, 68, 68, 0.22
                );
                border: 1px solid rgba(
                    239, 68, 68, 0.45
                );
            }

            QPushButton#logoutButton:pressed {
                background-color: rgba(
                    239, 68, 68, 0.35
                );
            }
            """
        )

        # Drop shadow

        shadow = QGraphicsDropShadowEffect()

        shadow.setBlurRadius(
            32
        )

        shadow.setOffset(
            -4,
            0
        )

        shadow.setColor(
            QColor(
                0,
                0,
                0,
                120
            )
        )

        sidebar.setGraphicsEffect(
            shadow
        )

        # =================================================
        # Pages
        # =================================================

        self.pages = QStackedWidget()

        self.home_page = DashboardPage()

        self.devices_page = DevicesPage(
            self.current_user
        )

        self.faults_page = FaultsPage(
            self.current_user
        )

        self.spare_parts_page = SparePartsPage()

        self.users_page = UsersPage(
            self.current_user
        )

        self.permissions_page = PermissionsPage(
            self.current_user
        )

        self.logs_page = LogsPage(
            self.current_user
        )

        # =================================================
        # Add Pages
        # =================================================

        self.pages.addWidget(
            self.home_page
        )

        self.pages.addWidget(
            self.devices_page
        )

        self.pages.addWidget(
            self.faults_page
        )

        self.pages.addWidget(
            self.spare_parts_page
        )

        self.pages.addWidget(
            self.users_page
        )

        self.pages.addWidget(
            self.permissions_page
        )

        self.pages.addWidget(
            self.logs_page
        )

        # =================================================
        # Main Layout
        # =================================================

        main_layout.addWidget(
            sidebar
        )

        main_layout.addWidget(
            self.pages
        )

        # =================================================
        # Navigation
        # =================================================

        self.nav_buttons = [
            self.btn_home,
            self.btn_devices,
            self.btn_faults,
            self.btn_spare_parts,
            self.btn_users,
            self.btn_permissions,
            self.btn_logs,
        ]

        for page_index, button in enumerate(
            self.nav_buttons
        ):

            button.clicked.connect(
                lambda checked=False,
                index=page_index:
                self.show_page(index)
            )

        # =================================================
        # Permissions
        # =================================================

        self.apply_permissions()

        self.show_page(
            0
        )

    # =====================================================
    # Permissions
    # =====================================================

    def has_permission(
        self,
        permission_code
    ):

        role = str(
            self.current_user.get(
                "role_code",
                ""
            )
        ).strip().upper()

        # SUPER ADMIN له كل الصلاحيات

        if role == "SUPER_ADMIN":
            return True

        return bool(
            self.current_user
            .get(
                "permissions",
                {}
            )
            .get(
                permission_code,
                False
            )
        )

    # =====================================================
    # Apply Permissions
    # =====================================================

    def apply_permissions(self):

        # -------------------------------------------------
        # الرئيسية
        # -------------------------------------------------

        self.btn_home.setVisible(
            self.has_permission(
                "dashboard.view"
            )
        )

        # -------------------------------------------------
        # الأجهزة
        # -------------------------------------------------

        self.btn_devices.setVisible(
            self.has_permission(
                "devices.view"
            )
        )

        # -------------------------------------------------
        # الأعطال
        # -------------------------------------------------

        self.btn_faults.setVisible(
            self.has_permission(
                "faults.view"
            )
        )

        # -------------------------------------------------
        # قطع الغيار
        # -------------------------------------------------

        self.btn_spare_parts.setVisible(
            self.has_permission(
                "spare_parts.view"
            )
        )

        # -------------------------------------------------
        # إدارة المستخدمين
        # -------------------------------------------------

        self.btn_users.setVisible(
            self.has_permission(
                "users.view"
            )
        )

        # -------------------------------------------------
        # الصلاحيات
        # SUPER ADMIN فقط
        # -------------------------------------------------

        role = str(
            self.current_user.get(
                "role_code",
                ""
            )
        ).strip().upper()

        self.btn_permissions.setVisible(
            role == "SUPER_ADMIN"
        )

        # -------------------------------------------------
        # سجل العمليات
        # ADMIN + SUPER ADMIN فقط
        # -------------------------------------------------

        self.btn_logs.setVisible(
            role in (
                "ADMIN",
                "SUPER_ADMIN"
            )
        )

    # =====================================================
    # Logout
    # =====================================================

    def handle_logout(self):

        reply = QMessageBox.question(
            self,
            "تسجيل الخروج",
            "هل أنت متأكد من رغبتك في تسجيل الخروج؟",
            QMessageBox.Yes |
            QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:

            self.logout_requested.emit()

    # =====================================================
    # Show Page
    # =====================================================

    def show_page(
        self,
        index
    ):

        self.pages.setCurrentIndex(
            index
        )

        if 0 <= index < len(
            self.nav_buttons
        ):

            self.nav_buttons[
                index
            ].setChecked(
                True
            )

    # =====================================================
    # Refresh Pages
    # =====================================================

    def refresh_pages(self):

        pages_to_refresh = (

            (
                self.home_page,
                (
                    "refresh",
                ),
            ),

            (
                self.devices_page,
                (
                    "load_devices",
                ),
            ),

            (
                self.faults_page,
                (
                    "load_faults",
                ),
            ),

            (
                self.spare_parts_page,
                (
                    "load_parts",
                    "load_data",
                ),
            ),

            (
                self.users_page,
                (
                    "load_users",
                ),
            ),

            (
                self.permissions_page,
                (
                    "load_roles",
                ),
            ),

            (
                self.logs_page,
                (
                    "load_logs",
                ),
            ),

        )

        for page, method_names in pages_to_refresh:

            for method_name in method_names:

                method = getattr(
                    page,
                    method_name,
                    None
                )

                if callable(
                    method
                ):

                    try:

                        method()

                    except TypeError:

                        pass

                    break


# =========================================================
# Application
# =========================================================

def main():

    initialize_database()

    app = QApplication(
        sys.argv
    )

    app.setStyle(
        "Fusion"
    )

    app.setLayoutDirection(
        Qt.RightToLeft
    )

    # =====================================================
    # IBM Plex Sans Arabic
    # =====================================================

    fonts_dir = os.path.join(
        os.path.dirname(
            os.path.abspath(
                __file__
            )
        ),
        "fonts",
    )

    font_files = [
        "IBMPlexSansArabic-Regular.ttf",
        "IBMPlexSansArabic-Medium.ttf",
        "IBMPlexSansArabic-SemiBold.ttf",
        "IBMPlexSansArabic-Bold.ttf",
    ]

    for font_file in font_files:

        font_path = os.path.join(
            fonts_dir,
            font_file
        )

        if os.path.exists(
            font_path
        ):

            QFontDatabase.addApplicationFont(
                font_path
            )

    app_font = QFont(
        "IBM Plex Sans Arabic",
        11
    )

    app.setFont(
        app_font
    )

    # =====================================================
    # Global Theme
    # =====================================================

    app.setStyleSheet(
        Theme.get_global_stylesheet()
    )

    # =====================================================
    # Login
    # =====================================================

    login_page = LoginPage()

    login_window = QMainWindow()

    login_window.setWindowTitle(
        "الشبكة - تسجيل الدخول"
    )

    login_window.resize(
        550,
        620
    )

    login_window.setCentralWidget(
        login_page
    )

    login_window.setLayoutDirection(
        Qt.RightToLeft
    )

    # =====================================================
    # الاحتفاظ بالنافذة الرئيسية
    # =====================================================

    main_window = {
        "window": None
    }

    # =====================================================
    # Logout Handler
    # =====================================================

    def handle_logout():

        # -------------------------------------------------
        # Audit Log - Logout
        # -------------------------------------------------

        current_window = main_window.get(
            "window"
        )

        if current_window:

            write_audit_log(
                user=current_window.current_user,
                action="خروج",
                module_name="النظام",
                description="تم تسجيل الخروج",
            )

            current_window.close()

            main_window[
                "window"
            ] = None

        if hasattr(
            login_page,
            "password_input"
        ):

            login_page.password_input.clear()

        login_window.show()

    # =====================================================
    # Open Main Window
    # =====================================================

    def open_main(user):

        login_window.close()

        window = MainWindow(
            user
        )

        main_window[
            "window"
        ] = window

        window.logout_requested.connect(
            handle_logout
        )

        window.show()

    # =====================================================
    # Login Signal
    # =====================================================

    login_page.login_successful.connect(
        open_main
    )

    login_window.show()

    return app.exec()


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )