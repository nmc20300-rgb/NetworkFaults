from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy,
    QStyle,
)

from database import get_connection

# =============================================================
# بطاقة إحصائية
# =============================================================


class StatCard(QFrame):
    def __init__(self, title, value="0", icon_type=QStyle.SP_ComputerIcon):
        super().__init__()

        self.setObjectName("statCard")
        self.setMinimumHeight(135)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(18, 16, 18, 16)

        layout.setSpacing(8)

        # -----------------------------------------------------
        # Header
        # -----------------------------------------------------

        top = QHBoxLayout()
        top.setSpacing(10)

        icon = QLabel()
        icon.setObjectName("cardIcon")

        pixmap = self.style().standardIcon(icon_type).pixmap(30, 30)

        icon.setPixmap(pixmap)
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(44, 44)

        top.addWidget(icon)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")

        title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        top.addWidget(title_label, 1)

        layout.addLayout(top)

        # -----------------------------------------------------
        # Value
        # -----------------------------------------------------

        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("cardValue")

        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(self.value_label)

        # -----------------------------------------------------
        # Bottom line
        # -----------------------------------------------------

        line = QFrame()
        line.setObjectName("cardLine")
        line.setFixedHeight(3)

        layout.addWidget(line)

    def set_value(self, value):

        self.value_label.setText(str(value))


# =============================================================
# لوحة صغيرة
# =============================================================


class MiniPanel(QFrame):
    def __init__(self, title, icon_type=QStyle.SP_FileDialogInfoView):
        super().__init__()

        self.setObjectName("dashboardPanel")

        self.layout = QVBoxLayout(self)

        self.layout.setContentsMargins(18, 16, 18, 18)

        self.layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(8)

        icon = QLabel()
        icon.setObjectName("panelIcon")

        icon.setPixmap(self.style().standardIcon(icon_type).pixmap(20, 20))

        header.addWidget(icon)

        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")

        header.addWidget(title_label, 1)

        self.layout.addLayout(header)


# =============================================================
# Dashboard
# =============================================================


class DashboardPage(QWidget):
    def __init__(self, current_user=None):
        super().__init__()

        self.setObjectName("dashboardPage")

        # -----------------------------------------------------
        # المستخدم الحالي
        # -----------------------------------------------------

        self.current_user = current_user or {}

        # -----------------------------------------------------
        # بناء الواجهة
        # -----------------------------------------------------

        self.setup_ui()

        self.refresh()

        # -----------------------------------------------------
        # تحديث البيانات كل 5 ثواني
        # -----------------------------------------------------

        self.refresh_timer = QTimer(self)

        self.refresh_timer.timeout.connect(self.refresh)

        self.refresh_timer.start(5000)

        # -----------------------------------------------------
        # تحديث التحية كل دقيقة
        # SUPER_ADMIN فقط
        # -----------------------------------------------------

        self.greeting_timer = QTimer(self)

        self.greeting_timer.timeout.connect(self.update_greeting)

        role_code = str(self.current_user.get("role_code", "") or "").strip().upper()

        if role_code == "SUPER_ADMIN":
            self.greeting_timer.start(60000)
        else:
            self.greeting_timer.stop()

    # =========================================================
    # التحقق من SUPER_ADMIN
    # =========================================================

    def is_super_admin(self):

        role_code = str(self.current_user.get("role_code", "") or "").strip().upper()

        return role_code == "SUPER_ADMIN"

    # =========================================================
    # التحية
    # =========================================================

    def update_greeting(self):

        # -----------------------------------------------------
        # لا توجد تحية لغير SUPER_ADMIN
        # -----------------------------------------------------

        if not self.is_super_admin():
            self.greeting_card.hide()

            return

        username = str(self.current_user.get("username", "") or "").strip()

        full_name = str(self.current_user.get("full_name", "") or "").strip()

        display_name_from_user = str(
            self.current_user.get("display_name", "") or ""
        ).strip()

        name_from_user = str(self.current_user.get("name", "") or "").strip()

        role_code = str(self.current_user.get("role_code", "") or "").strip().upper()

        # -----------------------------------------------------
        # المستخدمون المعروفون
        # -----------------------------------------------------

        user_profiles = {
            "قائد شبكه الربط المحلية": {
                "title": "عميد",
                "name": "أحمد صلاح",
            },
            "قائد شبكة الربط المحلية": {
                "title": "عميد",
                "name": "أحمد صلاح",
            },
            "superadmin": {
                "title": "عميد",
                "name": "أحمد صلاح",
            },
            "ali": {
                "title": "مهندس",
                "name": "علي",
            },
            "m_adel": {
                "title": "مهندس",
                "name": "محمد عادل",
            },
            "m_samir": {
                "title": "بشمهندس",
                "name": "محمد سمير",
            },
            "a_galal": {
                "title": "بشمهندس",
                "name": "جلال",
            },
            "m_rashad": {
                "title": "مهندس",
                "name": "رشاد",
            },
        }

        # -----------------------------------------------------
        # Profile
        # -----------------------------------------------------

        profile = user_profiles.get(username)

        if profile:
            title = profile["title"]

            display_name = profile["name"]

        else:
            display_name = (
                display_name_from_user
                or full_name
                or name_from_user
                or username
                or "مستخدم النظام"
            )

            if role_code == "SUPER_ADMIN":
                title = "عميد"

            else:
                title = ""

        # -----------------------------------------------------
        # الدور الظاهر
        # -----------------------------------------------------

        visible_role = "قائد شبكة الربط المحلية"

        # -----------------------------------------------------
        # الوقت
        # -----------------------------------------------------

        hour = datetime.now().hour

        if 5 <= hour < 12:
            greeting = "صباح الخير"

            icon = "☀️"

            message = "نتمنى لك صباحًا موفقًا ومليئًا بالإنجاز."

        elif 12 <= hour < 17:
            greeting = "مساء الخير"

            icon = "🌤️"

            message = "نتمنى لك يومًا سعيدًا ومثمرًا."

        elif 17 <= hour < 24:
            greeting = "مساء الخير"

            icon = "🌙"

            message = "نتمنى لك مساءً هادئًا ومميزًا."

        else:
            greeting = "مساء الخير"

            icon = "🌙"

            message = "نتمنى لك ليلة هادئة."

        # -----------------------------------------------------
        # النص
        # -----------------------------------------------------

        if title:
            main_text = f"{greeting}، {title} {display_name} {icon}"

        else:
            main_text = f"{greeting}، {display_name} {icon}"

        self.greeting_label.setText(main_text)

        self.greeting_hint.setText(message)

        self.greeting_role.setText(visible_role)

        self.greeting_card.show()

    # =========================================================
    # بناء الواجهة
    # =========================================================

    def setup_ui(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(26, 22, 26, 22)

        root.setSpacing(16)

        # =====================================================
        # Header
        # =====================================================

        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("الرئيسية")
        title.setObjectName("dashboardTitle")

        title_box.addWidget(title)

        credits = QLabel(
            "قائد شبكة الربط: عميد أحمد صلاح  |  المطور: Ahmed Abozead, Hamdy Haggag"
        )

        credits.setObjectName("dashboardCredits")

        title_box.addWidget(credits)

        header.addLayout(title_box)
        header.addStretch()

        self.refresh_btn = QPushButton("  تحديث البيانات")

        self.refresh_btn.setObjectName("dashboardRefresh")

        self.refresh_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))

        self.refresh_btn.setIconSize(QPixmap(18, 18).size())

        self.refresh_btn.clicked.connect(self.refresh)

        header.addWidget(self.refresh_btn)

        root.addLayout(header)

        # =====================================================
        # Greeting Card
        # =====================================================

        self.greeting_card = QFrame()

        self.greeting_card.setObjectName("greetingCard")

        greeting_layout = QVBoxLayout(self.greeting_card)

        greeting_layout.setContentsMargins(24, 17, 24, 17)

        greeting_layout.setSpacing(5)

        greeting_top = QHBoxLayout()
        greeting_top.setSpacing(12)

        self.greeting_label = QLabel("")
        self.greeting_label.setObjectName("greetingLabel")

        self.greeting_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        greeting_top.addWidget(self.greeting_label, 1)

        self.greeting_role = QLabel("قائد شبكة الربط المحلية")

        self.greeting_role.setObjectName("greetingRole")

        self.greeting_role.setAlignment(Qt.AlignCenter)

        self.greeting_role.setMinimumWidth(145)

        greeting_top.addWidget(self.greeting_role)

        greeting_layout.addLayout(greeting_top)

        self.greeting_hint = QLabel("")
        self.greeting_hint.setObjectName("greetingHint")

        self.greeting_hint.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        greeting_layout.addWidget(self.greeting_hint)

        root.addWidget(self.greeting_card)

        # -----------------------------------------------------
        # إظهار Greeting للـ SUPER_ADMIN فقط
        # -----------------------------------------------------

        self.greeting_card.setVisible(self.is_super_admin())

        # =====================================================
        # Cards
        # =====================================================

        self.cards = {}

        cards_layout = QGridLayout()
        cards_layout.setSpacing(14)

        definitions = [
            ("devices", "إجمالي الأجهزة", QStyle.SP_ComputerIcon),
            ("faults", "إجمالي الأعطال", QStyle.SP_MessageBoxWarning),
            ("open", "أعطال مفتوحة", QStyle.SP_MessageBoxCritical),
            ("buildings", "المباني / الفروع", QStyle.SP_DirHomeIcon),
            ("spare_parts", "قطع غيار ناقصة", QStyle.SP_FileDialogDetailedView),
        ]

        for col, (key, title_text, icon_type) in enumerate(definitions):
            card = StatCard(title_text, "0", icon_type)

            self.cards[key] = card

            cards_layout.addWidget(card, 0, col)

        root.addLayout(cards_layout)

        # =====================================================
        # Middle
        # =====================================================

        middle = QGridLayout()
        middle.setSpacing(14)

        # -----------------------------------------------------
        # Device Status
        # -----------------------------------------------------

        status_panel = MiniPanel("حالة الأجهزة", QStyle.SP_ComputerIcon)

        self.device_status_layout = QVBoxLayout()

        self.device_status_layout.setSpacing(8)

        status_panel.layout.addLayout(self.device_status_layout)

        middle.addWidget(status_panel, 0, 0)

        # -----------------------------------------------------
        # Fault Status
        # -----------------------------------------------------

        fault_panel = MiniPanel("حالة الأعطال", QStyle.SP_MessageBoxWarning)

        self.fault_status_layout = QVBoxLayout()

        self.fault_status_layout.setSpacing(7)

        fault_panel.layout.addLayout(self.fault_status_layout)

        middle.addWidget(fault_panel, 0, 1)

        # -----------------------------------------------------
        # Health
        # -----------------------------------------------------

        health_panel = MiniPanel("مؤشر التشغيل", QStyle.SP_DialogApplyButton)

        self.health_value = QLabel("0%")

        self.health_value.setObjectName("healthValue")

        self.health_value.setAlignment(Qt.AlignCenter)

        health_panel.layout.addWidget(self.health_value)

        self.health_bar = QProgressBar()

        self.health_bar.setRange(0, 100)

        self.health_bar.setTextVisible(False)

        self.health_bar.setFixedHeight(13)

        self.health_bar.setObjectName("healthBar")

        health_panel.layout.addWidget(self.health_bar)

        self.health_hint = QLabel("")

        self.health_hint.setObjectName("healthHint")

        self.health_hint.setAlignment(Qt.AlignCenter)

        self.health_hint.setWordWrap(True)

        health_panel.layout.addWidget(self.health_hint)

        middle.addWidget(health_panel, 0, 2)

        for col in range(3):
            middle.setColumnStretch(col, 1)

        root.addLayout(middle)

        # =====================================================
        # Recent Faults
        # =====================================================

        recent_panel = MiniPanel(
            "آخر الأعطال المسجلة", QStyle.SP_FileDialogDetailedView
        )

        self.recent_table = QTableWidget()

        self.recent_table.setColumnCount(6)

        self.recent_table.setHorizontalHeaderLabels(
            ["رقم العطل", "التاريخ", "الجهاز", "المستخدم", "الحالة", "الأولوية"]
        )

        self.recent_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.recent_table.setSelectionBehavior(QTableWidget.SelectRows)

        self.recent_table.setSelectionMode(QTableWidget.SingleSelection)

        self.recent_table.verticalHeader().setVisible(False)

        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.recent_table.setMinimumHeight(205)

        self.recent_table.setAlternatingRowColors(True)

        recent_panel.layout.addWidget(self.recent_table)

        root.addWidget(recent_panel)

        # =====================================================
        # Footer
        # =====================================================

        self.footer = QLabel("آخر تحديث: --")

        self.footer.setObjectName("dashboardFooter")

        self.footer.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        root.addWidget(self.footer)

        # =====================================================
        # Style
        # =====================================================

        self.setStyleSheet("""
            #dashboardPage {
                background: #f4f7fb;
            }

            #dashboardTitle {
                font-size: 27px;
                font-weight: 800;
                color: #0f2338;
            }

            #dashboardCredits {
                font-size: 12px;
                font-weight: 700;
                color: #0891b2;
                padding-top: 3px;
            }

            #dashboardRefresh {
                background: #0891b2;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 18px;
                font-weight: 700;
            }

            #dashboardRefresh:hover {
                background: #0e7490;
            }

            #dashboardRefresh:pressed {
                background: #155e75;
            }

            #dashboardRefresh:focus {
                border: 1.5px solid #38bdf8;
            }

            /* Greeting */

            #greetingCard {
                background: white;
                border: 1px solid #dce7ed;
                border-right: 5px solid #58b7c2;
                border-radius: 15px;
            }

            #greetingCard:hover {
                border: 1px solid #9bcbd0;
                border-right: 5px solid #58b7c2;
            }

            #greetingLabel {
                color: #17324d;
                font-size: 21px;
                font-weight: 800;
            }

            #greetingHint {
                color: #718096;
                font-size: 12px;
                font-weight: 600;
            }

            #greetingRole {
                background: #e6f7f8;
                color: #087f8c;
                border: 1px solid #b9e3e6;
                border-radius: 9px;
                padding: 7px 13px;
                font-size: 11px;
                font-weight: 800;
            }

            /* Cards */

            #statCard,
            #dashboardPanel {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 15px;
            }

            #statCard:hover,
            #dashboardPanel:hover {
                border: 1px solid #38bdf8;
            }

            #cardIcon {
                background: #e0f2fe;
                border-radius: 11px;
            }

            #cardTitle {
                color: #64748b;
                font-size: 13px;
                font-weight: 600;
            }

            #cardValue {
                color: #0f2338;
                font-size: 29px;
                font-weight: 800;
            }

            #cardLine {
                background: #0891b2;
                border-radius: 2px;
            }

            /* Panels */

            #panelIcon {
                background: #e0f2fe;
                border-radius: 7px;
                padding: 4px;
            }

            #panelTitle {
                color: #0f2338;
                font-size: 15px;
                font-weight: 800;
            }

            /* Health */

            #healthValue {
                color: #0f2338;
                font-size: 36px;
                font-weight: 900;
                padding: 4px;
            }

            #healthBar {
                border: none;
                background: #e2e8f0;
                border-radius: 7px;
            }

            #healthBar::chunk {
                background: #0891b2;
                border-radius: 7px;
            }

            #healthHint {
                color: #64748b;
                font-size: 12px;
                padding: 5px;
            }

            /* Footer */

            #dashboardFooter {
                color: #94a3b8;
                font-size: 11px;
                padding-top: 2px;
            }

            /* Table */

            QTableWidget {
                background: white;
                border: none;
                gridline-color: #f1f5f9;
                color: #334155;
                font-size: 12px;
                selection-background-color: #e0f2fe;
                selection-color: #0f2338;
                alternate-background-color: #f8fafc;
            }

            QTableWidget::item {
                padding: 6px;
                border: none;
            }

            QHeaderView::section {
                background: #f8fafc;
                color: #0f2338;
                border: none;
                border-bottom: 2px solid #0891b2;
                padding: 10px 8px;
                font-weight: 700;
            }
            """)

        # =====================================================
        # التحية بعد بناء العناصر
        # =====================================================

        if self.is_super_admin():
            self.update_greeting()
        else:
            self.greeting_card.hide()

    # =============================================================
    # Clear Layout
    # =============================================================

    def _clear_layout(self, layout):

        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()
            child_layout = item.layout()

            if widget:
                widget.deleteLater()

            elif child_layout:
                self._clear_layout(child_layout)

    # =============================================================
    # Status Row
    # =============================================================

    def _add_status_row(self, layout, label, count, total):

        row = QHBoxLayout()
        row.setSpacing(9)

        name = QLabel(label)

        name.setMinimumWidth(118)

        name.setStyleSheet("""
            color:#53677a;
            font-size:12px;
            font-weight:600;
            """)

        bar = QProgressBar()

        bar.setRange(0, max(total, 1))

        bar.setValue(count)

        bar.setTextVisible(False)

        bar.setFixedHeight(9)

        bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background: #edf1f5;
                border-radius: 4px;
            }

            QProgressBar::chunk {
                background: #4b7ea5;
                border-radius: 4px;
            }
            """)

        number = QLabel(str(count))

        number.setAlignment(Qt.AlignCenter)

        number.setMinimumWidth(32)

        number.setStyleSheet("""
            color:#0f2338;
            font-size:12px;
            font-weight:800;
            """)

        row.addWidget(name)

        row.addWidget(bar, 1)

        row.addWidget(number)

        layout.addLayout(row)

    # =============================================================
    # Refresh
    # =============================================================

    def refresh(self):

        # ---------------------------------------------------------
        # التحية لـ SUPER_ADMIN فقط
        # ---------------------------------------------------------

        if self.is_super_admin():
            self.update_greeting()

        else:
            self.greeting_card.hide()

        connection = get_connection()
        cursor = connection.cursor()

        def count(query, params=()):

            cursor.execute(query, params)

            result = cursor.fetchone()

            if result:
                return result[0] or 0

            return 0

        try:
            # =====================================================
            # Devices
            # =====================================================

            cursor.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(
                        CASE
                            WHEN is_archived = 0
                            THEN 1
                            ELSE 0
                        END
                    ) AS active,
                    SUM(
                        CASE
                            WHEN is_archived = 1
                            THEN 1
                            ELSE 0
                        END
                    ) AS archived,
                    SUM(
                        CASE
                            WHEN is_archived IS NULL
                            THEN 1
                            ELSE 0
                        END
                    ) AS null_archived
                FROM devices
                """)

            debug = cursor.fetchone()

            total_devices = debug["total"] or 0

            # =====================================================
            # Faults
            # =====================================================

            total_faults = count("""
                SELECT COUNT(*)
                FROM faults
                """)

            open_faults = count("""
                SELECT COUNT(*)
                FROM faults
                WHERE LTRIM(
                    RTRIM(
                        ISNULL(
                            status,
                            N''
                        )
                    )
                ) NOT IN (
                    N'تم الإصلاح',
                    N'تم التسليم'
                )
                """)

            # =====================================================
            # Buildings
            # =====================================================

            total_buildings = count("""
                SELECT COUNT(
                    DISTINCT building_id
                )
                FROM devices
                WHERE is_archived = 0
                  AND building_id IS NOT NULL
                """)

            # =====================================================
            # Spare Parts
            # =====================================================

            missing_spare_parts = count("""
                SELECT COUNT(*)
                FROM spare_parts
                WHERE is_archived = 0
                  AND quantity < required_quantity
                """)

            # =====================================================
            # Cards
            # =====================================================

            self.cards["devices"].set_value(total_devices)

            self.cards["faults"].set_value(total_faults)

            self.cards["open"].set_value(open_faults)

            self.cards["buildings"].set_value(total_buildings)

            self.cards["spare_parts"].set_value(missing_spare_parts)

            # =====================================================
            # Device Status
            # =====================================================

            device_statuses = ["صالح", "يحتاج فحص", "عطل", "خارج الخدمة"]

            self._clear_layout(self.device_status_layout)

            for status in device_statuses:
                value = count(
                    """
                    SELECT COUNT(*)
                    FROM devices
                    WHERE status = ?
                    """,
                    (status,),
                )

                self._add_status_row(
                    self.device_status_layout, status, value, total_devices
                )

            # =====================================================
            # Fault Status
            # =====================================================

            fault_statuses = [
                "جديد",
                "قيد الفحص",
                "قيد الإصلاح",
                "بانتظار قطعة غيار",
                "تم الإصلاح",
                "تم التسليم",
            ]

            self._clear_layout(self.fault_status_layout)

            for status in fault_statuses:
                value = count(
                    """
                    SELECT COUNT(*)
                    FROM faults
                    WHERE status = ?
                    """,
                    (status,),
                )

                self._add_status_row(
                    self.fault_status_layout, status, value, total_faults
                )

            # =====================================================
            # Health
            # =====================================================

            healthy = count("""
                SELECT COUNT(*)
                FROM devices
                WHERE is_archived = 0
                  AND LTRIM(
                      RTRIM(
                          status
                      )
                  ) = N'صالح'
                """)

            active_devices = count("""
                SELECT COUNT(*)
                FROM devices
                WHERE is_archived = 0
                """)

            health = round((healthy / active_devices) * 100) if active_devices else 0

            self.health_value.setText(f"{health}%")

            self.health_bar.setValue(health)

            if health >= 90:
                hint = "ممتاز — أغلب الأجهزة تعمل بصورة طبيعية."

            elif health >= 70:
                hint = "جيد — توجد بعض الأجهزة التي تحتاج متابعة."

            elif active_devices:
                hint = "يحتاج متابعة — نسبة الأجهزة غير السليمة مرتفعة."

            else:
                hint = "لا توجد أجهزة نشطة حتى الآن."

            self.health_hint.setText(hint)

            # =====================================================
            # Recent Faults
            # =====================================================

            cursor.execute("""
                SELECT TOP 10
                    faults.fault_number,
                    faults.entry_date,
                    devices.device_name,
                    faults.user_name,
                    faults.status,
                    faults.priority
                FROM faults
                LEFT JOIN devices
                    ON faults.device_id = devices.id
                ORDER BY faults.id DESC
                """)

            recent = cursor.fetchall()

            self.recent_table.setRowCount(0)

            for fault in recent:
                row = self.recent_table.rowCount()

                self.recent_table.insertRow(row)

                values = [
                    fault["fault_number"],
                    fault["entry_date"],
                    fault["device_name"] or "",
                    fault["user_name"] or "",
                    fault["status"] or "",
                    fault["priority"] or "",
                ]

                for col, value in enumerate(values):
                    item = QTableWidgetItem(str(value or ""))

                    item.setTextAlignment(Qt.AlignCenter)

                    self.recent_table.setItem(row, col, item)

            # =====================================================
            # Last Update
            # =====================================================

            self.footer.setText(
                "آخر تحديث: " + datetime.now().strftime("%Y-%m-%d %H:%M")
            )

        finally:
            connection.close()

    # =============================================================
    # Show Event
    # =============================================================

    def showEvent(self, event):

        super().showEvent(event)

        self.refresh()
