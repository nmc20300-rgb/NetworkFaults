from ast import literal_eval
import json

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QLineEdit,
    QMessageBox,
    QDialog,
    QFormLayout,
    QDateEdit,
    QAbstractItemView,
    QScrollArea,
)

from database import get_connection


class LogsPage(QWidget):

    def __init__(self, current_user=None):

        super().__init__()

        self.current_user = current_user or {}

        self.setObjectName("logsPage")

        self.setup_ui()
        self.load_logs()

    # =========================================================
    # Permission
    # =========================================================

    def can_view(self):

        role = str(
            self.current_user.get(
                "role_code",
                ""
            )
        ).strip().upper()

        return role in (
            "ADMIN",
            "SUPER_ADMIN",
        )

    # =========================================================
    # UI
    # =========================================================

    def setup_ui(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(
            25,
            22,
            25,
            22
        )

        root.setSpacing(14)

        # =====================================================
        # Header
        # =====================================================

        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title_box.setSpacing(3)

        title = QLabel(
            "سجل العمليات"
        )

        title.setObjectName(
            "logsTitle"
        )

        subtitle = QLabel(
            "متابعة ومراجعة جميع العمليات التي تمت داخل النظام"
        )

        subtitle.setObjectName(
            "logsSubtitle"
        )

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch()

        self.refresh_button = QPushButton(
            "⟳  تحديث"
        )

        self.refresh_button.setObjectName(
            "logsRefreshButton"
        )

        self.refresh_button.clicked.connect(
            self.load_logs
        )

        header.addWidget(
            self.refresh_button
        )

        root.addLayout(header)

        # =====================================================
        # Filters
        # =====================================================

        filter_frame = QFrame()

        filter_frame.setObjectName(
            "logsFilterFrame"
        )

        filter_layout = QHBoxLayout(
            filter_frame
        )

        filter_layout.setContentsMargins(
            14,
            12,
            14,
            12
        )

        filter_layout.setSpacing(8)

        # -----------------------------------------------------
        # User
        # -----------------------------------------------------

        user_label = QLabel(
            "المستخدم:"
        )

        self.user_filter = QLineEdit()

        self.user_filter.setPlaceholderText(
            "اسم المستخدم..."
        )

        self.user_filter.setMinimumWidth(
            145
        )

        filter_layout.addWidget(
            user_label
        )

        filter_layout.addWidget(
            self.user_filter
        )

        # -----------------------------------------------------
        # Module
        # -----------------------------------------------------

        module_label = QLabel(
            "القسم:"
        )

        self.module_filter = QComboBox()

        self.module_filter.setMinimumWidth(
            120
        )

        self.module_filter.addItem(
            "كل الأقسام",
            ""
        )

        self.module_filter.addItems([
            "الأجهزة",
            "الأعطال",
            "قطع الغيار",
            "المستخدمين",
            "الصلاحيات",
            "التقارير",
            "النظام",
        ])

        filter_layout.addWidget(
            module_label
        )

        filter_layout.addWidget(
            self.module_filter
        )

        # -----------------------------------------------------
        # Action
        # -----------------------------------------------------

        action_label = QLabel(
            "العملية:"
        )

        self.action_filter = QComboBox()

        self.action_filter.setMinimumWidth(
            125
        )

        self.action_filter.addItem(
            "كل العمليات",
            ""
        )

        self.action_filter.addItems([
            "إضافة",
            "تعديل",
            "حذف",
            "أرشفة",
            "استيراد",
            "تصدير",
            "دخول",
            "خروج",
            "عرض",
            "استعادة",
            "تفعيل",
            "تعطيل",
            "تغيير كلمة المرور",
            "تغيير الصلاحيات",
        ])

        filter_layout.addWidget(
            action_label
        )

        filter_layout.addWidget(
            self.action_filter
        )

        # -----------------------------------------------------
        # From Date
        # -----------------------------------------------------

        from_label = QLabel(
            "من:"
        )

        self.from_date = QDateEdit()

        self.from_date.setCalendarPopup(
            True
        )

        self.from_date.setDisplayFormat(
            "dd/MM/yyyy"
        )

        self.from_date.setDate(
            QDate.currentDate().addDays(-30)
        )

        self.from_date.setMinimumWidth(
            110
        )

        filter_layout.addWidget(
            from_label
        )

        filter_layout.addWidget(
            self.from_date
        )

        # -----------------------------------------------------
        # To Date
        # -----------------------------------------------------

        to_label = QLabel(
            "إلى:"
        )

        self.to_date = QDateEdit()

        self.to_date.setCalendarPopup(
            True
        )

        self.to_date.setDisplayFormat(
            "dd/MM/yyyy"
        )

        self.to_date.setDate(
            QDate.currentDate()
        )

        self.to_date.setMinimumWidth(
            110
        )

        filter_layout.addWidget(
            to_label
        )

        filter_layout.addWidget(
            self.to_date
        )

        # -----------------------------------------------------
        # Search
        # -----------------------------------------------------

        self.search_button = QPushButton(
            "🔎 بحث"
        )

        self.search_button.setObjectName(
            "logsSearchButton"
        )

        self.search_button.clicked.connect(
            self.load_logs
        )

        filter_layout.addWidget(
            self.search_button
        )

        # -----------------------------------------------------
        # Reset
        # -----------------------------------------------------

        self.reset_button = QPushButton(
            "↻ إعادة تعيين"
        )

        self.reset_button.setObjectName(
            "logsResetButton"
        )

        self.reset_button.clicked.connect(
            self.reset_filters
        )

        filter_layout.addWidget(
            self.reset_button
        )

        root.addWidget(
            filter_frame
        )

        # =====================================================
        # Table
        # =====================================================

        table_frame = QFrame()

        table_frame.setObjectName(
            "logsTableFrame"
        )

        table_layout = QVBoxLayout(
            table_frame
        )

        table_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.table = QTableWidget()

        self.table.setColumnCount(9)

        self.table.setHorizontalHeaderLabels([
            "المستخدم",
            "العملية",
            "القسم",
            "رقم السجل",
            "الوصف",
            "الكمبيوتر",
            "IP",
            "التاريخ",
            "التفاصيل",
        ])

        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setWordWrap(False)

        header_view = (
            self.table.horizontalHeader()
        )

        header_view.setSectionResizeMode(
            QHeaderView.Interactive
        )

        header_view.setStretchLastSection(
            True
        )

        widths = [
            125,
            95,
            110,
            80,
            300,
            145,
            120,
            155,
            130,
        ]

        for index, width in enumerate(
            widths
        ):
            self.table.setColumnWidth(
                index,
                width
            )

        table_layout.addWidget(
            self.table
        )

        root.addWidget(
            table_frame,
            1
        )

        # =====================================================
        # Footer
        # =====================================================

        footer = QHBoxLayout()

        self.count_label = QLabel(
            "عدد السجلات: 0"
        )

        self.count_label.setObjectName(
            "logsCount"
        )

        footer.addWidget(
            self.count_label
        )

        footer.addStretch()

        self.range_label = QLabel(
            "مرتبة من الأحدث إلى الأقدم"
        )

        self.range_label.setObjectName(
            "logsRange"
        )

        footer.addWidget(
            self.range_label
        )

        root.addLayout(
            footer
        )

        # =====================================================
        # Style
        # =====================================================

        self.setStyleSheet(
            """
            #logsPage {
                background: #f4f7fb;
            }

            #logsTitle {
                color: #0f2338;
                font-size: 27px;
                font-weight: 800;
            }

            #logsSubtitle {
                color: #64748b;
                font-size: 12px;
            }

            #logsRefreshButton,
            #logsSearchButton {
                background: #0891b2;
                color: white;
                border: none;
                border-radius: 9px;
                padding: 9px 15px;
                font-weight: 700;
            }

            #logsRefreshButton:hover,
            #logsSearchButton:hover {
                background: #0e7490;
            }

            #logsResetButton {
                background: #f1f5f9;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 9px;
                padding: 9px 13px;
                font-weight: 700;
            }

            #logsResetButton:hover {
                background: #e2e8f0;
            }

            #logsFilterFrame,
            #logsTableFrame {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 13px;
            }

            QLineEdit,
            QComboBox,
            QDateEdit {
                background: white;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 7px 9px;
                min-height: 20px;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QDateEdit:focus {
                border: 1px solid #0891b2;
            }

            QTableWidget {
                background: white;
                border: none;
                gridline-color: #edf2f7;
                color: #334155;
                font-size: 12px;
                selection-background-color: #e0f2fe;
                selection-color: #0f2338;
                alternate-background-color: #f8fafc;
            }

            QTableWidget::item {
                padding: 7px;
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

            #logsCount {
                color: #64748b;
                font-size: 11px;
                font-weight: 700;
            }

            #logsRange {
                color: #94a3b8;
                font-size: 11px;
            }

            #logDetailsButton {
                background: #ecfeff;
                color: #0e7490;
                border: 1px solid #a5f3fc;
                border-radius: 7px;
                padding: 5px 10px;
                font-weight: 700;
            }

            #logDetailsButton:hover {
                background: #cffafe;
            }

            #detailsDialog {
                background: #f4f7fb;
            }

            #detailsTitle {
                color: #0f2338;
                font-size: 22px;
                font-weight: 800;
            }

            #detailsCard {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }

            #detailsSectionTitle {
                color: #0f2338;
                font-size: 15px;
                font-weight: 800;
            }

            #oldValuesFrame {
                background: #fff7ed;
                border: 1px solid #fed7aa;
                border-radius: 12px;
            }

            #newValuesFrame {
                background: #f0fdf4;
                border: 1px solid #bbf7d0;
                border-radius: 12px;
            }

            #oldValuesTitle {
                color: #c2410c;
                font-size: 15px;
                font-weight: 800;
            }

            #newValuesTitle {
                color: #15803d;
                font-size: 15px;
                font-weight: 800;
            }

            #valuesTable {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #e5e7eb;
                color: #334155;
                font-size: 12px;
            }

            #valuesTable::item {
                padding: 7px;
            }

            #valuesTable QHeaderView::section {
                background: #f8fafc;
                color: #334155;
                border: none;
                border-bottom: 1px solid #cbd5e1;
                padding: 8px;
                font-weight: 700;
            }

            #detailsCloseButton {
                background: #0891b2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px 25px;
                font-weight: 700;
            }

            #detailsCloseButton:hover {
                background: #0e7490;
            }
            """
        )

    # =========================================================
    # Query
    # =========================================================

    def get_filtered_logs(self):

        connection = None
        cursor = None

        try:

            connection = get_connection()
            cursor = connection.cursor()

            query = """
                SELECT
                    id,
                    username,
                    action,
                    module_name,
                    record_id,
                    description,
                    computer_name,
                    ip_address,
                    created_at,
                    old_values,
                    new_values
                FROM audit_logs
                WHERE 1 = 1
            """

            params = []

            # User

            username = (
                self.user_filter.text().strip()
            )

            if username:

                query += """
                    AND username LIKE ?
                """

                params.append(
                    "%" + username + "%"
                )

            # Module

            module = (
                self.module_filter.currentData()
            )

            if module:

                query += """
                    AND module_name = ?
                """

                params.append(module)

            # Action

            action = (
                self.action_filter.currentData()
            )

            if action:

                query += """
                    AND action = ?
                """

                params.append(action)

            # From date

            from_date = (
                self.from_date.date()
            )

            if from_date.isValid():

                query += """
                    AND created_at >= ?
                """

                params.append(
                    from_date.toString(
                        "yyyy-MM-dd"
                    )
                )

            # To date

            to_date = (
                self.to_date.date()
            )

            if to_date.isValid():

                next_day = (
                    to_date.addDays(1)
                )

                query += """
                    AND created_at < ?
                """

                params.append(
                    next_day.toString(
                        "yyyy-MM-dd"
                    )
                )

            query += """
                ORDER BY id DESC
            """

            cursor.execute(
                query,
                tuple(params)
            )

            return cursor.fetchall()

        finally:

            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass

            try:
                if connection:
                    connection.close()
            except Exception:
                pass

    # =========================================================
    # Load Logs
    # =========================================================

    def load_logs(self):

        if not self.can_view():

            self.table.setRowCount(0)

            self.count_label.setText(
                "غير مصرح بعرض سجل العمليات"
            )

            return

        try:

            rows = self.get_filtered_logs()

            self.table.setRowCount(0)

            for row_data in rows:

                row = self.table.rowCount()

                self.table.insertRow(row)

                self.set_table_item(
                    row,
                    0,
                    row_data["username"]
                )

                action_item = self.set_table_item(
                    row,
                    1,
                    row_data["action"]
                )

                self.apply_action_style(
                    action_item,
                    row_data["action"]
                )

                self.set_table_item(
                    row,
                    2,
                    row_data["module_name"]
                )

                self.set_table_item(
                    row,
                    3,
                    row_data["record_id"]
                )

                self.set_table_item(
                    row,
                    4,
                    row_data["description"]
                )

                self.set_table_item(
                    row,
                    5,
                    row_data["computer_name"]
                )

                self.set_table_item(
                    row,
                    6,
                    row_data["ip_address"]
                )

                self.set_table_item(
                    row,
                    7,
                    self.format_datetime(
                        row_data["created_at"]
                    )
                )

                details_button = QPushButton(
                    "عرض التفاصيل"
                )

                details_button.setObjectName(
                    "logDetailsButton"
                )

                details_button.setCursor(
                    Qt.PointingHandCursor
                )

                log_id = row_data["id"]

                details_button.clicked.connect(
                    lambda checked=False,
                    current_id=log_id:
                    self.show_details(
                        current_id
                    )
                )

                self.table.setCellWidget(
                    row,
                    8,
                    details_button
                )

            self.count_label.setText(
                f"عدد السجلات: {len(rows)}"
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "خطأ",
                "حدث خطأ أثناء تحميل سجل العمليات:\n\n"
                + str(error)
            )

    # =========================================================
    # Table Item
    # =========================================================

    def set_table_item(
        self,
        row,
        column,
        value
    ):

        item = QTableWidgetItem(
            ""
            if value is None
            else str(value)
        )

        item.setTextAlignment(
            Qt.AlignCenter
        )

        self.table.setItem(
            row,
            column,
            item
        )

        return item

    # =========================================================
    # Date
    # =========================================================

    def format_datetime(self, value):

        if value is None:
            return ""

        try:

            return value.strftime(
                "%d/%m/%Y %H:%M:%S"
            )

        except Exception:

            return str(value)

    # =========================================================
    # Action Style
    # =========================================================

    def apply_action_style(
        self,
        item,
        action
    ):

        action = str(
            action or ""
        ).strip()

        if action in (
            "حذف",
            "تعطيل",
        ):

            item.setForeground(
                Qt.darkRed
            )

        elif action in (
            "إضافة",
            "استيراد",
            "تفعيل",
        ):

            item.setForeground(
                Qt.darkGreen
            )

        elif action in (
            "تعديل",
            "أرشفة",
        ):

            item.setForeground(
                Qt.darkBlue
            )

        elif action in (
            "دخول",
            "خروج",
        ):

            item.setForeground(
                Qt.darkCyan
            )

    # =========================================================
    # Reset Filters
    # =========================================================

    def reset_filters(self):

        self.user_filter.clear()

        self.module_filter.setCurrentIndex(0)

        self.action_filter.setCurrentIndex(0)

        self.from_date.setDate(
            QDate.currentDate().addDays(-30)
        )

        self.to_date.setDate(
            QDate.currentDate()
        )

        self.load_logs()

    # =========================================================
    # Get Log
    # =========================================================

    def get_log_by_id(
        self,
        log_id
    ):

        connection = None
        cursor = None

        try:

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    username,
                    action,
                    module_name,
                    record_id,
                    description,
                    computer_name,
                    ip_address,
                    created_at,
                    old_values,
                    new_values
                FROM audit_logs
                WHERE id = ?
                """,
                (log_id,)
            )

            return cursor.fetchone()

        finally:

            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass

            try:
                if connection:
                    connection.close()
            except Exception:
                pass

    # =========================================================
    # Parse Audit Values
    # =========================================================

    def parse_audit_values(
        self,
        value
    ):

        if value is None:
            return {}

        if isinstance(value, dict):
            return value

        text = str(value).strip()

        if not text:
            return {}

        # -----------------------------------------------------
        # Try JSON
        # -----------------------------------------------------

        try:

            parsed = json.loads(text)

            if isinstance(
                parsed,
                dict
            ):
                return parsed

        except Exception:
            pass

        # -----------------------------------------------------
        # Try Python dict representation
        # -----------------------------------------------------

        try:

            parsed = literal_eval(text)

            if isinstance(
                parsed,
                dict
            ):
                return parsed

        except Exception:
            pass

        # -----------------------------------------------------
        # If it's just text
        # -----------------------------------------------------

        return {
            "البيانات": text
        }

    # =========================================================
    # Format Key Names
    # =========================================================

    def friendly_key(
        self,
        key
    ):

        names = {

            "id": "رقم السجل",

            "device_number": "رقم الجهاز",
            "device_name": "اسم الجهاز",
            "device_type": "نوع الجهاز",
            "serial_number": "الرقم التسلسلي",
            "building": "المبنى",
            "building_id": "رقم المبنى",
            "building_name": "اسم المبنى",

            "user_name": "اسم المستخدم",
            "username": "اسم المستخدم",

            "received_by": "اسم المستلم",
            "recipient_name": "اسم المستلم",

            "specifications": "المواصفات",
            "device_specifications": "مواصفات الجهاز",

            "fault_description": "وصف العطل",
            "repair_action": "إجراءات الإصلاح",
            "repair_description": "إجراءات الإصلاح",

            "technician": "القائم بالإصلاح",
            "repairer": "القائم بالإصلاح",

            "status": "الحالة",
            "is_archived": "مؤرشف",

            "ip_address": "عنوان IP",
            "computer_name": "اسم الكمبيوتر",

            "part_name": "اسم الصنف",
            "part_number": "رقم الصنف",
            "quantity": "الكمية",
            "unit": "الوحدة",

            "old_password": "كلمة المرور القديمة",
            "new_password": "كلمة المرور الجديدة",

            "role_code": "الدور",
            "role_name": "اسم الدور",

            "is_active": "الحالة",

            "created_at": "تاريخ الإنشاء",
            "updated_at": "آخر تعديل",
        }

        return names.get(
            str(key),
            str(key)
        )

    # =========================================================
    # Format Value
    # =========================================================

    def friendly_value(
        self,
        value
    ):

        if value is None:
            return ""

        if isinstance(
            value,
            bool
        ):

            return (
                "نعم"
                if value
                else "لا"
            )

        return str(value)

    # =========================================================
    # Create Professional Values Table
    # =========================================================

    def create_values_table(
        self,
        values
    ):

        table = QTableWidget()

        table.setObjectName(
            "valuesTable"
        )

        table.setColumnCount(2)

        table.setHorizontalHeaderLabels([
            "الحقل",
            "القيمة",
        ])

        table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        table.verticalHeader().setVisible(
            False
        )

        table.setAlternatingRowColors(
            True
        )

        table.setWordWrap(True)

        table.setColumnWidth(
            0,
            170
        )

        table.horizontalHeader().setStretchLastSection(
            True
        )

        if not values:

            table.setRowCount(1)

            empty_key = QTableWidgetItem(
                "—"
            )

            empty_value = QTableWidgetItem(
                "لا توجد بيانات"
            )

            empty_key.setTextAlignment(
                Qt.AlignCenter
            )

            empty_value.setTextAlignment(
                Qt.AlignCenter
            )

            table.setItem(
                0,
                0,
                empty_key
            )

            table.setItem(
                0,
                1,
                empty_value
            )

            return table

        table.setRowCount(
            len(values)
        )

        for row_index, (
            key,
            value
        ) in enumerate(
            values.items()
        ):

            key_item = QTableWidgetItem(
                self.friendly_key(
                    key
                )
            )

            value_item = QTableWidgetItem(
                self.friendly_value(
                    value
                )
            )

            key_item.setTextAlignment(
                Qt.AlignRight
                | Qt.AlignVCenter
            )

            value_item.setTextAlignment(
                Qt.AlignRight
                | Qt.AlignVCenter
            )

            key_item.setToolTip(
                str(key)
            )

            table.setItem(
                row_index,
                0,
                key_item
            )

            table.setItem(
                row_index,
                1,
                value_item
            )

        table.resizeRowsToContents()

        return table

    # =========================================================
    # Details Dialog
    # =========================================================

    def show_details(
        self,
        log_id
    ):

        if not self.can_view():
            return

        row = self.get_log_by_id(
            log_id
        )

        if not row:

            QMessageBox.warning(
                self,
                "تنبيه",
                "لم يتم العثور على سجل العملية."
            )

            return

        old_values = (
            self.parse_audit_values(
                row["old_values"]
            )
        )

        new_values = (
            self.parse_audit_values(
                row["new_values"]
            )
        )

        dialog = QDialog(self)

        dialog.setObjectName(
            "detailsDialog"
        )

        dialog.setWindowTitle(
            "تفاصيل سجل العملية"
        )

        dialog.resize(
            1000,
            760
        )

        root = QVBoxLayout(dialog)

        root.setContentsMargins(
            22,
            20,
            22,
            20
        )

        root.setSpacing(14)

        # =====================================================
        # Title
        # =====================================================

        title = QLabel(
            "تفاصيل سجل العملية"
        )

        title.setObjectName(
            "detailsTitle"
        )

        root.addWidget(title)

        # =====================================================
        # Basic Information
        # =====================================================

        info_card = QFrame()

        info_card.setObjectName(
            "detailsCard"
        )

        form = QFormLayout(
            info_card
        )

        form.setContentsMargins(
            18,
            15,
            18,
            15
        )

        form.setVerticalSpacing(9)

        self.add_detail_row(
            form,
            "المستخدم",
            row["username"]
        )

        self.add_detail_row(
            form,
            "العملية",
            row["action"]
        )

        self.add_detail_row(
            form,
            "القسم",
            row["module_name"]
        )

        self.add_detail_row(
            form,
            "رقم السجل",
            row["record_id"]
        )

        self.add_detail_row(
            form,
            "الوصف",
            row["description"]
        )

        self.add_detail_row(
            form,
            "اسم الكمبيوتر",
            row["computer_name"]
        )

        self.add_detail_row(
            form,
            "عنوان IP",
            row["ip_address"]
        )

        self.add_detail_row(
            form,
            "التاريخ والوقت",
            self.format_datetime(
                row["created_at"]
            )
        )

        root.addWidget(
            info_card
        )

        # =====================================================
        # Old / New Tables
        # =====================================================

        values_layout = QHBoxLayout()

        values_layout.setSpacing(14)

        # -----------------------------------------------------
        # Old Values
        # -----------------------------------------------------

        old_frame = QFrame()

        old_frame.setObjectName(
            "oldValuesFrame"
        )

        old_layout = QVBoxLayout(
            old_frame
        )

        old_layout.setContentsMargins(
            12,
            12,
            12,
            12
        )

        old_title = QLabel(
            "القيم القديمة"
        )

        old_title.setObjectName(
            "oldValuesTitle"
        )

        old_layout.addWidget(
            old_title
        )

        old_table = self.create_values_table(
            old_values
        )

        old_layout.addWidget(
            old_table,
            1
        )

        values_layout.addWidget(
            old_frame,
            1
        )

        # -----------------------------------------------------
        # New Values
        # -----------------------------------------------------

        new_frame = QFrame()

        new_frame.setObjectName(
            "newValuesFrame"
        )

        new_layout = QVBoxLayout(
            new_frame
        )

        new_layout.setContentsMargins(
            12,
            12,
            12,
            12
        )

        new_title = QLabel(
            "القيم الجديدة"
        )

        new_title.setObjectName(
            "newValuesTitle"
        )

        new_layout.addWidget(
            new_title
        )

        new_table = self.create_values_table(
            new_values
        )

        new_layout.addWidget(
            new_table,
            1
        )

        values_layout.addWidget(
            new_frame,
            1
        )

        root.addLayout(
            values_layout,
            1
        )

        # =====================================================
        # Close
        # =====================================================

        buttons = QHBoxLayout()

        buttons.addStretch()

        close_button = QPushButton(
            "إغلاق"
        )

        close_button.setObjectName(
            "detailsCloseButton"
        )

        close_button.setCursor(
            Qt.PointingHandCursor
        )

        close_button.clicked.connect(
            dialog.accept
        )

        buttons.addWidget(
            close_button
        )

        buttons.addStretch()

        root.addLayout(
            buttons
        )

        dialog.exec()

    # =========================================================
    # Detail Row
    # =========================================================

    def add_detail_row(
        self,
        layout,
        label,
        value
    ):

        label_widget = QLabel(
            label + ":"
        )

        label_widget.setStyleSheet(
            """
            QLabel {
                color: #64748b;
                font-weight: 700;
            }
            """
        )

        value_widget = QLabel(
            ""
            if value is None
            else str(value)
        )

        value_widget.setWordWrap(True)

        value_widget.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        value_widget.setStyleSheet(
            """
            QLabel {
                color: #0f2338;
                font-weight: 600;
            }
            """
        )

        layout.addRow(
            label_widget,
            value_widget
        )