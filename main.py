import os
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from database import initialize_database, write_audit_log
from ui.arabic_translator import setup_arabic_localization
from ui.dashboard_page import DashboardPage
from ui.devices_page import DevicesPage
from ui.faults_page import FaultsPage
from ui.ink_page import InkPage
from ui.login_page import LoginPage
from ui.logs_page import LogsPage
from ui.org_structure_page import OrgStructurePage
from ui.permissions_page import PermissionsPage
from ui.spare_parts_page import SparePartsPage
from ui.theme import Theme
from ui.users_page import UsersPage


class MainWindow(QMainWindow):
    logout_requested = Signal()

    def __init__(self, user):
        super().__init__()

        self.current_user = user or {}

        self.setWindowTitle("الشبكة - نظام إدارة الأجهزة والأعطال")
        self.resize(1400, 850)
        self.setMinimumSize(1100, 700)
        self.setLayoutDirection(Qt.RightToLeft)

        central = QWidget()
        central.setObjectName("mainCentralWidget")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = self.build_sidebar()
        main_layout.addWidget(self.sidebar)

        self.pages = QStackedWidget()
        self.pages.setObjectName("mainPages")
        main_layout.addWidget(self.pages, 1)

        self.build_pages()
        self.build_navigation()
        self.apply_permissions()
        self.show_page(0)

    # =========================================================
    # Sidebar
    # =========================================================

    def build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(292)
        sidebar.setLayoutDirection(Qt.RightToLeft)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 22, 18, 18)
        sidebar_layout.setSpacing(0)

        # -----------------------------------------------------
        # Brand
        # -----------------------------------------------------

        brand_widget = QWidget()
        brand_widget.setObjectName("sidebarBrand")

        brand_layout = QHBoxLayout(brand_widget)
        brand_layout.setContentsMargins(4, 0, 4, 0)
        brand_layout.setSpacing(11)

        brand_icon = QLabel()
        brand_icon.setObjectName("brandIcon")
        brand_icon.setAlignment(Qt.AlignCenter)
        brand_icon.setFixedSize(58, 58)

        logo_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets",
            "nmc_logo3.png",
        )

        logo_pixmap = QPixmap(logo_path)

        if not logo_pixmap.isNull():
            brand_icon.setPixmap(
                logo_pixmap.scaled(
                    48,
                    48,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
        else:
            brand_icon.setText("NMC")

        brand_text_layout = QVBoxLayout()
        brand_text_layout.setContentsMargins(0, 0, 0, 0)
        brand_text_layout.setSpacing(2)

        sidebar_title = QLabel("الشبكة")
        sidebar_title.setObjectName("sidebarTitle")

        sidebar_subtitle = QLabel("نظام إدارة الأجهزة والدعم الفني")
        sidebar_subtitle.setObjectName("sidebarSubtitle")
        sidebar_subtitle.setWordWrap(True)

        brand_text_layout.addWidget(sidebar_title)
        brand_text_layout.addWidget(sidebar_subtitle)

        brand_layout.addWidget(brand_icon)
        brand_layout.addLayout(brand_text_layout, 1)

        sidebar_layout.addWidget(brand_widget)
        sidebar_layout.addSpacing(25)

        # -----------------------------------------------------
        # User Card
        # -----------------------------------------------------

        user_card_wrapper = QWidget()
        user_card_wrapper.setObjectName("userCardWrapper")

        user_card = QWidget()
        user_card.setObjectName("userCard")

        user_layout = QHBoxLayout(user_card)
        user_layout.setContentsMargins(12, 12, 12, 12)
        user_layout.setSpacing(10)

        user_avatar = QLabel("●")
        user_avatar.setObjectName("userAvatar")
        user_avatar.setAlignment(Qt.AlignCenter)
        user_avatar.setFixedSize(44, 44)

        user_text_layout = QVBoxLayout()
        user_text_layout.setContentsMargins(0, 0, 0, 0)
        user_text_layout.setSpacing(3)

        display_name = (
            self.current_user.get("full_name")
            or self.current_user.get("name")
            or self.current_user.get("username")
            or "مستخدم النظام"
        )

        # =====================================================
        # اسم الدور الظاهر للمستخدم
        # =====================================================

        role_code = str(
            self.current_user.get("role_code", "")
        ).strip().upper()

        if role_code == "SUPER_ADMIN":
            role_name = "عميد أحمد صلاح"
        elif role_code == "ADMIN":
            role_name = "Admin"
        elif role_code == "SUB_ADMIN":
            role_name = "Sub Admin"
        else:
            role_name = "مستخدم"

        user_name = QLabel(str(display_name))
        user_name.setObjectName("userName")
        user_name.setWordWrap(True)

        user_role = QLabel(str(role_name))
        user_role.setObjectName("userRole")

        user_text_layout.addWidget(user_name)
        user_text_layout.addWidget(user_role)

        user_layout.addWidget(user_avatar)
        user_layout.addLayout(user_text_layout, 1)

        wrapper_layout = QVBoxLayout(user_card_wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(user_card)

        sidebar_layout.addWidget(user_card_wrapper)
        sidebar_layout.addSpacing(24)

        # -----------------------------------------------------
        # Navigation
        # -----------------------------------------------------

        section_label = QLabel("التشغيل اليومي")
        section_label.setObjectName("sectionLabel")

        sidebar_layout.addWidget(section_label)
        sidebar_layout.addSpacing(7)

        nav_container = QWidget()
        nav_container.setObjectName("navContainer")

        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(6)

        self.btn_home = self.create_nav_button("", "الرئيسية")
        self.btn_devices = self.create_nav_button("", "الأجهزة")
        self.btn_faults = self.create_nav_button("", "الأعطال")
        self.btn_spare_parts = self.create_nav_button("", "قطع الغيار")
        self.btn_ink = self.create_nav_button("", "الأحبار")

        for button in (
            self.btn_home,
            self.btn_devices,
            self.btn_faults,
            self.btn_spare_parts,
            self.btn_ink,
        ):
            nav_layout.addWidget(button)

        management_label = QLabel("الإدارة والمتابعة")
        management_label.setObjectName("sectionLabel")

        nav_layout.addSpacing(14)
        nav_layout.addWidget(management_label)
        nav_layout.addSpacing(5)

        self.btn_org_structure = self.create_nav_button(
            "",
            "الهيكل التنظيمي"
        )

        self.btn_users = self.create_nav_button(
            "",
            "إدارة المستخدمين"
        )

        self.btn_permissions = self.create_nav_button(
            "",
            "الصلاحيات"
        )

        self.btn_logs = self.create_nav_button(
            "",
            "سجل العمليات"
        )

        for button in (
            self.btn_org_structure,
            self.btn_users,
            self.btn_permissions,
            self.btn_logs,
        ):
            nav_layout.addWidget(button)

        # ترتيب الصفحات الداخلي يطابق ترتيب QStackedWidget

        self.nav_buttons = [
            self.btn_home,
            self.btn_devices,
            self.btn_faults,
            self.btn_spare_parts,
            self.btn_users,
            self.btn_permissions,
            self.btn_logs,
            self.btn_ink,
            self.btn_org_structure,
        ]

        sidebar_layout.addWidget(nav_container)
        sidebar_layout.addStretch(1)

        # -----------------------------------------------------
        # Footer / Logout
        # -----------------------------------------------------

        footer_widget = QWidget()
        footer_widget.setObjectName("sidebarFooterWidget")

        footer_layout = QVBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(10)

        divider = QFrame()
        divider.setObjectName("footerDivider")
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(1)

        self.logout_button = QPushButton("↪  تسجيل الخروج")
        self.logout_button.setObjectName("logoutButton")
        self.logout_button.setCursor(Qt.PointingHandCursor)
        self.logout_button.setMinimumHeight(45)
        self.logout_button.clicked.connect(self.handle_logout)

        footer_layout.addWidget(divider)
        footer_layout.addWidget(self.logout_button)

        sidebar_layout.addWidget(footer_widget)

        # -----------------------------------------------------
        # Sidebar Style
        # -----------------------------------------------------

        sidebar.setStyleSheet("""
            QWidget#sidebar {
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

            QWidget#sidebarBrand,
            QWidget#userCardWrapper,
            QWidget#navContainer,
            QWidget#sidebarFooterWidget {
                background: transparent;
            }

            QLabel#brandIcon {
                background: rgba(255, 255, 255, 0.12);
                color: #ffffff;
                border: 1px solid rgba(216, 244, 247, 0.28);
                border-radius: 29px;
                font-size: 15px;
                font-weight: 900;
            }

            QLabel#sidebarTitle {
                background: transparent;
                color: #ffffff;
                font-size: 22px;
                font-weight: 900;
            }

            QLabel#sidebarSubtitle {
                background: transparent;
                color: #d8f4f7;
                font-size: 12px;
                font-weight: 600;
            }

            QWidget#userCard {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(216, 244, 247, 0.24);
                border-radius: 14px;
            }

            QLabel#userAvatar {
                background: #10a6b7;
                color: #ffffff;
                border: 1px solid #69cbd4;
                border-radius: 22px;
                font-size: 20px;
                font-weight: 900;
            }

            QLabel#userName {
                background: transparent;
                color: #ffffff;
                font-size: 13px;
                font-weight: 800;
            }

            QLabel#userRole {
                background: transparent;
                color: #a9dbe2;
                font-size: 10px;
                font-weight: 600;
            }

            QLabel#sectionLabel {
                background: transparent;
                color: #a9dbe2;
                font-size: 12px;
                font-weight: 800;
                padding: 4px 5px;
            }

            QPushButton#navButton {
                color: #d8f4f7;
                background: transparent;
                border: 1px solid transparent;
                border-radius: 11px;
                padding: 11px 14px;
                font-size: 15px;
                font-weight: 600;
                text-align: left;
            }

            QPushButton#navButton:hover {
                color: #ffffff;
                background: rgba(16, 166, 183, 0.20);
                border: 1px solid rgba(216, 244, 247, 0.18);
            }

            QPushButton#navButton:pressed {
                background: rgba(16, 166, 183, 0.32);
            }

            QPushButton#navButton:checked {
                color: #ffffff;
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 0,
                    stop: 0 rgba(16, 166, 183, 0.38),
                    stop: 1 rgba(16, 166, 183, 0.10)
                );
                border: 1px solid rgba(16, 166, 183, 0.45);
                border-right: 4px solid #10a6b7;
                font-weight: 800;
            }

            QPushButton#navButton:checked:hover {
                background: rgba(16, 166, 183, 0.42);
                border-right: 4px solid #69cbd4;
            }

            QPushButton#navButton:disabled {
                color: rgba(216, 244, 247, 0.48);
                background: rgba(255, 255, 255, 0.035);
                border: 1px solid rgba(216, 244, 247, 0.08);
            }

            QFrame#footerDivider {
                background: rgba(216, 244, 247, 0.20);
                border: none;
                max-height: 1px;
            }

            QPushButton#logoutButton {
                color: #ffd2d2;
                background: rgba(179, 61, 72, 0.16);
                border: 1px solid rgba(241, 201, 205, 0.30);
                border-radius: 11px;
                padding: 11px 14px;
                font-size: 13px;
                font-weight: 800;
                text-align: left;
            }

            QPushButton#logoutButton:hover {
                color: #ffffff;
                background: rgba(179, 61, 72, 0.30);
                border: 1px solid rgba(255, 210, 210, 0.50);
            }

            QPushButton#logoutButton:pressed {
                background: rgba(179, 61, 72, 0.42);
            }
        """)

        shadow = QGraphicsDropShadowEffect(sidebar)
        shadow.setBlurRadius(28)
        shadow.setOffset(-4, 0)
        shadow.setColor(QColor(6, 40, 59, 90))
        sidebar.setGraphicsEffect(shadow)

        return sidebar

    def create_nav_button(self, icon_text, label_text):
        button = QPushButton(f"{icon_text}   {label_text}")
        button.setObjectName("navButton")
        button.setCheckable(True)
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(44)
        return button

    # =========================================================
    # Pages
    # =========================================================

    def build_pages(self):
        self.home_page = DashboardPage(self.current_user)
        self.devices_page = DevicesPage(self.current_user)
        self.faults_page = FaultsPage(self.current_user)
        self.spare_parts_page = SparePartsPage()
        self.users_page = UsersPage(self.current_user)
        self.permissions_page = PermissionsPage(self.current_user)
        self.logs_page = LogsPage(self.current_user)
        self.ink_page = InkPage(self.current_user)
        self.org_structure_page = OrgStructurePage(self.current_user)

        pages = [
            self.home_page,
            self.devices_page,
            self.faults_page,
            self.spare_parts_page,
            self.users_page,
            self.permissions_page,
            self.logs_page,
            self.ink_page,
            self.org_structure_page,
        ]

        for page in pages:
            self.pages.addWidget(page)

    def build_navigation(self):
        for page_index, button in enumerate(self.nav_buttons):
            button.clicked.connect(
                lambda checked=False, index=page_index:
                self.show_page(index)
            )

    # =========================================================
    # Permissions
    # =========================================================

    def has_permission(self, permission_code):
        role = str(
            self.current_user.get("role_code", "")
        ).strip().upper()

        if role == "SUPER_ADMIN":
            return True

        return bool(
            self.current_user.get(
                "permissions",
                {}
            ).get(permission_code, False)
        )

    def apply_permissions(self):

        self.btn_home.setVisible(True)
        self.btn_devices.setVisible(True)
        self.btn_faults.setVisible(True)
        self.btn_spare_parts.setVisible(True)
        self.btn_ink.setVisible(True)
        self.btn_org_structure.setVisible(True)
        self.btn_logs.setVisible(True)

        self.btn_home.setEnabled(
            self.has_permission("dashboard.view")
        )

        self.btn_devices.setEnabled(
            self.has_permission("devices.view")
        )

        self.btn_faults.setEnabled(
            self.has_permission("faults.view")
        )

        self.btn_spare_parts.setEnabled(
            self.has_permission("spare_parts.view")
        )

        self.btn_ink.setEnabled(
            self.has_permission("ink.view")
        )

        self.btn_org_structure.setEnabled(
            self.has_permission("ink.org_structure.manage")
        )

        role = str(
            self.current_user.get("role_code", "")
        ).strip().upper()

        # إدارة المستخدمين والصلاحيات تظهر للـ SUPER_ADMIN فقط.
        is_super_admin = role == "SUPER_ADMIN"

        self.btn_users.setVisible(is_super_admin)
        self.btn_permissions.setVisible(is_super_admin)

        self.btn_users.setEnabled(
            is_super_admin
            and self.has_permission("users.view")
        )

        self.btn_permissions.setEnabled(is_super_admin)

        self.btn_logs.setEnabled(
            role in ("ADMIN", "SUPER_ADMIN")
        )

    # =========================================================
    # Navigation
    # =========================================================

    def show_page(self, index):
        if not 0 <= index < self.pages.count():
            return

        self.pages.setCurrentIndex(index)

        for button in self.nav_buttons:
            button.setChecked(False)

        if index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)

    # =========================================================
    # Logout
    # =========================================================

    def handle_logout(self):
        reply = QMessageBox.question(
            self,
            "تسجيل الخروج",
            "هل أنت متأكد من رغبتك في تسجيل الخروج؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.logout_requested.emit()

    # =========================================================
    # Refresh Pages
    # =========================================================

    def refresh_pages(self):
        pages_to_refresh = (
            (self.home_page, ("refresh",)),
            (self.devices_page, ("load_devices",)),
            (self.faults_page, ("load_faults",)),
            (self.spare_parts_page, ("load_parts", "load_data")),
            (self.users_page, ("load_users",)),
            (self.permissions_page, ("load_roles",)),
            (self.logs_page, ("load_logs",)),
            (self.ink_page, ("load_transactions",)),
            (self.org_structure_page, ("load_units",)),
        )

        for page, method_names in pages_to_refresh:
            for method_name in method_names:
                method = getattr(page, method_name, None)

                if callable(method):
                    try:
                        method()
                    except TypeError:
                        pass
                    break


# =============================================================
# Application
# =============================================================

def main():
    initialize_database()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setLayoutDirection(Qt.RightToLeft)

    setup_arabic_localization(app)

    fonts_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "fonts",
    )

    font_files = [
        "IBMPlexSansArabic-Regular.ttf",
        "IBMPlexSansArabic-Medium.ttf",
        "IBMPlexSansArabic-SemiBold.ttf",
        "IBMPlexSansArabic-Bold.ttf",
    ]

    for font_file in font_files:
        font_path = os.path.join(fonts_dir, font_file)

        if os.path.exists(font_path):
            QFontDatabase.addApplicationFont(font_path)

    app.setFont(QFont("IBM Plex Sans Arabic", 11))
    app.setStyleSheet(Theme.get_global_stylesheet())

    login_page = LoginPage()

    login_window = QMainWindow()
    login_window.setWindowTitle("الشبكة - تسجيل الدخول")
    login_window.resize(1200, 750)
    login_window.setMinimumSize(900, 600)

    login_window.setCentralWidget(login_page)
    login_window.setLayoutDirection(Qt.RightToLeft)

    main_window = {"window": None}

    def handle_logout():
        current_window = main_window.get("window")

        if current_window:
            write_audit_log(
                user=current_window.current_user,
                action="خروج",
                module_name="النظام",
                description="تم تسجيل الخروج",
            )

            current_window.close()
            main_window["window"] = None

        if hasattr(login_page, "password_input"):
            login_page.password_input.clear()

        login_window.show()

    def open_main(user):
        try:
            # نُبقي نافذة الدخول والـ loading ظاهرة أثناء تجهيز النظام.
            window = MainWindow(user)
            main_window["window"] = window
            window.logout_requested.connect(handle_logout)

            # نُظهر النظام أولاً، ثم نخفي نافذة الدخول بدون وميض أو فراغ.
            window.show()
            login_page._set_loading(False)
            login_window.hide()

        except Exception as error:
            login_page._set_loading(False)
            login_page.show_error(
                f"تعذر فتح النظام بعد تسجيل الدخول:\n{error}"
            )

    login_page.login_successful.connect(open_main)

    login_window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())