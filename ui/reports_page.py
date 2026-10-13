import html
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDateEdit, QFrame
)

from database import get_connection


APP_STYLE = """
QWidget#reportsPage {
    background: #f4f7fb;
}

QLabel#pageTitle {
    color: #0f2338;
    font-size: 25px;
    font-weight: 800;
}

QLabel#pageSubtitle {
    color: #64748b;
    font-size: 12px;
}

QFrame#card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
}

QLabel#cardTitle {
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
}

QLabel#cardValue {
    color: #0f2338;
    font-size: 22px;
    font-weight: 800;
}

QComboBox, QLineEdit, QDateEdit {
    background: #fbfdff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 10px;
    min-height: 18px;
}

QComboBox:focus, QLineEdit:focus, QDateEdit:focus {
    border: 1.5px solid #0891b2;
    background: white;
}

QPushButton {
    border: none;
    border-radius: 8px;
    padding: 9px 16px;
    font-size: 12px;
    font-weight: 700;
}

QPushButton#primaryButton {
    background: #0891b2;
    color: white;
}

QPushButton#primaryButton:hover {
    background: #0e7490;
}

QPushButton#primaryButton:pressed {
    background: #155e75;
}

QPushButton#secondaryButton {
    background: #f1f5f9;
    color: #0f2338;
    border: 1px solid #cbd5e1;
}

QPushButton#secondaryButton:hover {
    background: #e2e8f0;
}

QTableWidget {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    gridline-color: #f1f5f9;
    selection-background-color: #e0f2fe;
    selection-color: #0f2338;
}

QHeaderView::section {
    background: #f8fafc;
    color: #0f2338;
    border: none;
    border-bottom: 2px solid #0891b2;
    padding: 9px;
    font-weight: 700;
}
"""


class ReportsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("reportsPage")
        self.setStyleSheet(APP_STYLE)

        self.setup_ui()
        self.load_report()

    # =========================================================
    # واجهة الصفحة
    # =========================================================

    def setup_ui(self):

        main = QVBoxLayout(self)
        main.setContentsMargins(26, 22, 26, 22)
        main.setSpacing(14)

        title_layout = QHBoxLayout()

        title_box = QVBoxLayout()

        title = QLabel("التقارير")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "تقارير الرصيد والأصناف وحركة المخزون"
        )
        subtitle.setObjectName("pageSubtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        title_layout.addLayout(title_box)
        title_layout.addStretch()

        self.refresh_button = QPushButton(" تحديث")
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.clicked.connect(self.load_report)
        title_layout.addWidget(self.refresh_button)

        self.print_button = QPushButton(" معاينة وطباعة")
        self.print_button.setObjectName("primaryButton")
        self.print_button.clicked.connect(self.print_report)
        title_layout.addWidget(self.print_button)

        main.addLayout(title_layout)

        # =====================================================
        # كروت الإحصائيات
        # =====================================================

        cards = QHBoxLayout()
        cards.setSpacing(12)

        self.total_card = self.create_card(
            "إجمالي الأصناف", "0"
        )

        self.available_card = self.create_card(
            "الأصناف المتوفرة", "0"
        )

        self.minimum_card = self.create_card(
            "عند الحد الأدنى", "0"
        )

        self.missing_card = self.create_card(
            "الأصناف غير المتوفرة", "0"
        )

        self.value_card = self.create_card(
            "قيمة المخزون", "0"
        )

        for card in (
            self.total_card,
            self.available_card,
            self.minimum_card,
            self.missing_card,
            self.value_card
        ):
            cards.addWidget(card)

        main.addLayout(cards)

        # =====================================================
        # الفلاتر
        # =====================================================

        filters = QFrame()
        filters.setObjectName("card")

        filters_layout = QHBoxLayout(filters)
        filters_layout.setContentsMargins(12, 10, 12, 10)
        filters_layout.setSpacing(8)

        report_label = QLabel("نوع التقرير:")

        self.report_box = QComboBox()

        self.report_box.addItems([
            "تقرير رصيد الأصناف",
            "الأصناف غير المتوفرة",
            "الأصناف عند الحد الأدنى",
            "حركة المخزون",
            "قيمة المخزون",
        ])

        self.report_box.currentIndexChanged.connect(
            self.load_report
        )

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "بحث باسم الصنف أو رقم الصنف أو المورد..."
        )

        self.search_box.textChanged.connect(
            self.load_report
        )

        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(
            QDate.currentDate().addMonths(-1)
        )
        self.from_date.setDisplayFormat("yyyy-MM-dd")

        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(
            QDate.currentDate()
        )
        self.to_date.setDisplayFormat("yyyy-MM-dd")

        self.date_label = QLabel("من:")
        self.to_label = QLabel("إلى:")

        filters_layout.addWidget(report_label)
        filters_layout.addWidget(self.report_box, 1)
        filters_layout.addWidget(self.search_box, 2)
        filters_layout.addWidget(self.date_label)
        filters_layout.addWidget(self.from_date)
        filters_layout.addWidget(self.to_label)
        filters_layout.addWidget(self.to_date)

        main.addWidget(filters)

        # =====================================================
        # الجدول
        # =====================================================

        self.table = QTableWidget()

        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SingleSelection
        )

        self.table.verticalHeader().setVisible(False)

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        main.addWidget(self.table, 1)

        # =====================================================
        # الملخص
        # =====================================================

        self.summary = QLabel("")
        self.summary.setObjectName("pageSubtitle")

        main.addWidget(self.summary)

    # =========================================================
    # الكروت
    # =========================================================

    def create_card(self, title, value):

        card = QFrame()
        card.setObjectName("card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")

        value_label = QLabel(value)
        value_label.setObjectName("cardValue")
        value_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return card

    def set_card_value(self, card, value):

        label = card.findChild(
            QLabel,
            "cardValue"
        )

        if label:
            label.setText(str(value))

    # =========================================================
    # تحميل التقرير
    # =========================================================

    def load_report(self):

        self.load_cards()

        report = self.report_box.currentText()

        if report == "حركة المخزون":
            self.load_movements()

        elif report == "الأصناف غير المتوفرة":
            self.load_missing()

        elif report == "الأصناف عند الحد الأدنى":
            self.load_minimum()

        elif report == "قيمة المخزون":
            self.load_value_report()

        else:
            self.load_balance()

    # =========================================================
    # كروت الإحصائيات
    # =========================================================

    def load_cards(self):

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS total,

                COALESCE(SUM(
                    CASE
                        WHEN (
                            availability_status =
                            'ناقصة ومطلوب توفيرها'
                            OR quantity < required_quantity
                        )
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS missing,

                COALESCE(SUM(
                    CASE
                        WHEN (
                            availability_status IS NULL
                            OR availability_status !=
                            'ناقصة ومطلوب توفيرها'
                        )
                        AND quantity >= required_quantity
                        AND quantity <= min_quantity
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS minimum,

                COALESCE(
                    SUM(quantity * unit_price),
                    0
                ) AS stock_value

            FROM spare_parts

            WHERE is_archived = 0
        """)

        row = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*)
            FROM spare_parts
            WHERE is_archived = 0
              AND (
                  availability_status IS NULL
                  OR availability_status !=
                  'ناقصة ومطلوب توفيرها'
              )
              AND quantity >= required_quantity
              AND quantity > min_quantity
        """)

        available = cursor.fetchone()[0]

        connection.close()

        self.set_card_value(
            self.total_card,
            row["total"] or 0
        )

        self.set_card_value(
            self.available_card,
            available or 0
        )

        self.set_card_value(
            self.minimum_card,
            row["minimum"] or 0
        )

        self.set_card_value(
            self.missing_card,
            row["missing"] or 0
        )

        self.set_card_value(
            self.value_card,
            f"{float(row['stock_value'] or 0):,.2f}"
        )

    # =========================================================
    # الاستعلام الأساسي
    # =========================================================

    def base_part_query(self):

        search = self.search_box.text().strip()

        query = """
            SELECT
                id,
                part_number,
                part_name,
                category,
                quantity,
                min_quantity,
                required_quantity,
                unit,
                supplier,
                unit_price,
                storage_location,
                availability_status,
                notes

            FROM spare_parts

            WHERE is_archived = 0
        """

        params = []

        if search:

            query += """
                AND (
                    part_name LIKE ?
                    OR part_number LIKE ?
                    OR supplier LIKE ?
                    OR category LIKE ?
                )
            """

            keyword = f"%{search}%"

            params.extend([
                keyword,
                keyword,
                keyword,
                keyword
            ])

        return query, params

    # =========================================================
    # تقرير الرصيد
    # =========================================================

    def load_balance(self):

        query, params = self.base_part_query()

        query += """
            ORDER BY part_name
        """

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(query, params)

        rows = cursor.fetchall()

        connection.close()

        headers = [
            "رقم الصنف",
            "اسم الصنف",
            "التصنيف",
            "الرصيد",
            "الحد الأدنى",
            "المطلوب",
            "الوحدة",
            "الحالة",
            "المورد",
            "مكان التخزين"
        ]

        self.fill_table(
            headers,
            [
                [
                    row["part_number"] or "-",
                    row["part_name"] or "-",
                    row["category"] or "-",
                    row["quantity"] or 0,
                    row["min_quantity"] or 0,
                    row["required_quantity"] or 0,
                    row["unit"] or "-",
                    self.status_text(row),
                    row["supplier"] or "-",
                    row["storage_location"] or "-",
                ]
                for row in rows
            ]
        )

        self.summary.setText(
            f"تقرير رصيد الأصناف — عدد الأصناف: {len(rows)}"
        )

    # =========================================================
    # تقرير الأصناف الناقصة
    # =========================================================

    def load_missing(self):

        query, params = self.base_part_query()

        query += """
            AND (
                availability_status =
                'ناقصة ومطلوب توفيرها'

                OR quantity < required_quantity
            )

            ORDER BY part_name
        """

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(query, params)

        rows = cursor.fetchall()

        connection.close()

        headers = [
            "رقم الصنف",
            "اسم الصنف",
            "الرصيد",
            "المطلوب",
            "العجز",
            "الوحدة",
            "المورد",
            "مكان التخزين"
        ]

        data = []

        for row in rows:

            quantity = int(
                row["quantity"] or 0
            )

            required = int(
                row["required_quantity"] or 0
            )

            shortage = max(
                required - quantity,
                0
            )

            data.append([
                row["part_number"] or "-",
                row["part_name"] or "-",
                quantity,
                required,
                shortage,
                row["unit"] or "-",
                row["supplier"] or "-",
                row["storage_location"] or "-"
            ])

        self.fill_table(headers, data)

        self.summary.setText(
            "تقرير الأصناف غير المتوفرة / الناقصة "
            f"— عدد الأصناف: {len(rows)}"
        )

    # =========================================================
    # تقرير الحد الأدنى
    # =========================================================

    def load_minimum(self):

        query, params = self.base_part_query()

        query += """
            AND (
                availability_status IS NULL
                OR availability_status !=
                'ناقصة ومطلوب توفيرها'
            )

            AND quantity >= required_quantity

            AND quantity <= min_quantity

            ORDER BY part_name
        """

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(query, params)

        rows = cursor.fetchall()

        connection.close()

        headers = [
            "رقم الصنف",
            "اسم الصنف",
            "الرصيد",
            "الحد الأدنى",
            "المطلوب",
            "الكمية المقترحة",
            "الوحدة",
            "المورد"
        ]

        data = []

        for row in rows:

            quantity = int(
                row["quantity"] or 0
            )

            required = int(
                row["required_quantity"] or 0
            )

            suggested = max(
                required - quantity,
                0
            )

            data.append([
                row["part_number"] or "-",
                row["part_name"] or "-",
                quantity,
                row["min_quantity"] or 0,
                required,
                suggested,
                row["unit"] or "-",
                row["supplier"] or "-"
            ])

        self.fill_table(headers, data)

        self.summary.setText(
            "تقرير الأصناف عند الحد الأدنى "
            f"— عدد الأصناف: {len(rows)}"
        )

    # =========================================================
    # تقرير قيمة المخزون
    # =========================================================

    def load_value_report(self):

        query, params = self.base_part_query()

        query += """
            ORDER BY (quantity * unit_price) DESC
        """

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(query, params)

        rows = cursor.fetchall()

        connection.close()

        headers = [
            "رقم الصنف",
            "اسم الصنف",
            "الرصيد",
            "الوحدة",
            "سعر الوحدة",
            "قيمة المخزون",
            "المورد",
            "مكان التخزين"
        ]

        data = []
        total = 0

        for row in rows:

            quantity = float(
                row["quantity"] or 0
            )

            unit_price = float(
                row["unit_price"] or 0
            )

            value = quantity * unit_price

            total += value

            data.append([
                row["part_number"] or "-",
                row["part_name"] or "-",
                (
                    int(quantity)
                    if quantity.is_integer()
                    else quantity
                ),
                row["unit"] or "-",
                f"{unit_price:,.2f}",
                f"{value:,.2f}",
                row["supplier"] or "-",
                row["storage_location"] or "-"
            ])

        self.fill_table(headers, data)

        self.summary.setText(
            "تقرير قيمة المخزون — "
            f"إجمالي القيمة: {total:,.2f} "
            f"— عدد الأصناف: {len(rows)}"
        )

    # =========================================================
    # حركة المخزون
    # =========================================================

    def load_movements(self):

        search = self.search_box.text().strip()

        from_date = self.from_date.date().toString(
            "yyyy-MM-dd"
        )

        to_date = self.to_date.date().toString(
            "yyyy-MM-dd"
        )

        query = """
            SELECT
                m.created_at,
                p.part_number,
                p.part_name,
                m.movement_type,
                m.quantity,
                p.quantity AS current_quantity,
                m.notes

            FROM spare_part_movements m

            JOIN spare_parts p
                ON p.id = m.spare_part_id

            WHERE CONVERT(date, m.created_at)
                BETWEEN ? AND ?
        """

        params = [
            from_date,
            to_date
        ]

        if search:

            query += """
                AND (
                    p.part_name LIKE ?
                    OR p.part_number LIKE ?
                    OR p.supplier LIKE ?
                    OR m.notes LIKE ?
                )
            """

            keyword = f"%{search}%"

            params.extend([
                keyword,
                keyword,
                keyword,
                keyword
            ])

        query += """
            ORDER BY m.id DESC
        """

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(query, params)

        rows = cursor.fetchall()

        connection.close()

        headers = [
            "التاريخ",
            "رقم الصنف",
            "اسم الصنف",
            "نوع الحركة",
            "الكمية",
            "الرصيد الحالي",
            "البيان"
        ]

        data = []

        for row in rows:

            data.append([
                row["created_at"] or "-",
                row["part_number"] or "-",
                row["part_name"] or "-",
                row["movement_type"] or "-",
                row["quantity"] or 0,
                row["current_quantity"] or 0,
                row["notes"] or "-"
            ])

        self.fill_table(headers, data)

        self.summary.setText(
            f"تقرير حركة المخزون من {from_date} "
            f"إلى {to_date} — عدد الحركات: {len(rows)}"
        )

    # =========================================================
    # حالة الصنف
    # =========================================================

    def status_text(self, row):

        quantity = int(
            row["quantity"] or 0
        )

        minimum = int(
            row["min_quantity"] or 0
        )

        required = int(
            row["required_quantity"] or 0
        )

        explicit = row["availability_status"]

        if (
            explicit == "ناقصة ومطلوب توفيرها"
            or quantity < required
        ):
            return "ناقص"

        if quantity <= minimum:
            return "عند الحد الأدنى"

        return "متوفر"

    # =========================================================
    # تعبئة الجدول
    # =========================================================

    def fill_table(self, headers, data):

        self.table.clear()

        self.table.setColumnCount(
            len(headers)
        )

        self.table.setHorizontalHeaderLabels(
            headers
        )

        self.table.setRowCount(0)

        for values in data:

            row_index = self.table.rowCount()

            self.table.insertRow(
                row_index
            )

            for col, value in enumerate(values):

                item = QTableWidgetItem(
                    str(value)
                )

                item.setTextAlignment(
                    Qt.AlignCenter
                )

                self.table.setItem(
                    row_index,
                    col,
                    item
                )

    # =========================================================
    # الطباعة - معاينة HTML في المتصفح
    # =========================================================

    def print_report(self):

        if self.table.rowCount() == 0:

            QMessageBox.information(
                self,
                "الطباعة",
                "لا توجد بيانات في التقرير الحالي."
            )

            return

        # -----------------------------------------------------
        # عنوان التقرير
        # -----------------------------------------------------

        report_name = self.report_box.currentText()

        report_title = (
            "الشبكة - " + report_name
        )

        # -----------------------------------------------------
        # التاريخ والوقت
        # -----------------------------------------------------

        printed_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )

        # -----------------------------------------------------
        # الفترة الزمنية
        # -----------------------------------------------------

        if report_name == "حركة المخزون":

            period_text = (
                f"الفترة من "
                f"{self.from_date.date().toString('yyyy-MM-dd')} "
                f"إلى "
                f"{self.to_date.date().toString('yyyy-MM-dd')}"
            )

        else:

            period_text = "تاريخ التقرير: " + printed_at

        # -----------------------------------------------------
        # رؤوس الجدول
        # -----------------------------------------------------

        headers = []

        for i in range(
            self.table.columnCount()
        ):

            header_item = (
                self.table.horizontalHeaderItem(i)
            )

            headers.append(
                header_item.text()
                if header_item
                else ""
            )

        headers_html = ""

        for header in headers:

            headers_html += (
                "<th>"
                + html.escape(str(header))
                + "</th>"
            )

        # -----------------------------------------------------
        # بيانات الجدول
        # -----------------------------------------------------

        rows_html = []

        for row in range(
            self.table.rowCount()
        ):

            cells_html = []

            for col in range(
                self.table.columnCount()
            ):

                item = self.table.item(
                    row,
                    col
                )

                value = (
                    item.text()
                    if item
                    else ""
                )

                value = html.escape(
                    str(value)
                )

                value = value.replace(
                    "\n",
                    "<br>"
                )

                cells_html.append(
                    f"<td>{value}</td>"
                )

            rows_html.append(
                "<tr>"
                + "".join(cells_html)
                + "</tr>"
            )

        table_rows = "".join(
            rows_html
        )

        # -----------------------------------------------------
        # الملخص
        # -----------------------------------------------------

        summary_text = html.escape(
            self.summary.text()
        )

        # -----------------------------------------------------
        # HTML التقرير
        # -----------------------------------------------------

        html_content = f"""
<!DOCTYPE html>

<html lang="ar" dir="rtl">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>
    {html.escape(report_title)}
</title>

<style>

@page {{
    size: A4 landscape;
    margin: 12mm;
}}

* {{
    box-sizing: border-box;
}}

html,
body {{
    margin: 0;
    padding: 0;
}}

body {{
    direction: rtl;
    font-family:
        "IBM Plex Sans Arabic",
        Tahoma,
        Arial,
        "Segoe UI",
        sans-serif;

    color: #0f2338;
    background: white;
}}

.report {{
    width: 100%;
}}

.header {{
    text-align: center;

    border-bottom:
        2px solid #0891b2;

    padding-bottom: 12px;

    margin-bottom: 14px;
}}

.header-main {{
    font-size: 24px;
    font-weight: 800;
    margin-bottom: 7px;
}}

.header-title {{
    font-size: 17px;
    font-weight: 700;
    margin-bottom: 6px;
}}

.header-period {{
    font-size: 12px;
    color: #475569;
    margin-bottom: 4px;
}}

.header-date {{
    font-size: 10px;
    color: #64748b;
}}

.summary {{
    background: #f4f7fb;

    border:
        1px solid #dce5ee;

    border-radius: 7px;

    padding: 9px 12px;

    margin-bottom: 13px;

    font-size: 11px;

    font-weight: 600;

    text-align: right;
}}

table {{
    width: 100%;

    border-collapse:
        collapse;

    table-layout:
        fixed;

    font-size: 9.5px;

    direction: rtl;
}}

thead {{
    display: table-header-group;
}}

tfoot {{
    display: table-footer-group;
}}

th {{
    background: #f8fafc;

    color: #0f2338;

    border:
        1px solid #cbd5e1;

    padding: 7px 4px;

    font-weight: 800;

    text-align: center;

    vertical-align: middle;

    word-wrap: break-word;
}}

td {{
    border:
        1px solid #cbd5df;

    padding: 6px 4px;

    text-align: center;

    vertical-align: middle;

    word-wrap: break-word;

    overflow-wrap: anywhere;

    line-height: 1.35;
}}

tbody tr:nth-child(even) {{
    background: #f8fafc;
}}

tr {{
    break-inside: avoid;
    page-break-inside: avoid;
}}

.signature-area {{
    margin-top: 28px;

    display: flex;

    justify-content:
        flex-start;

    page-break-inside:
        avoid;

    break-inside:
        avoid;
}}

.signature {{
    width: 270px;

    text-align: center;

    margin-left: 35px;
}}

.signature-respect {{
    font-size: 12px;

    font-weight: 600;

    margin-bottom: 9px;
}}

.signature-name {{
    font-size: 15px;

    font-weight: 800;

    margin-bottom: 6px;
}}

.signature-role {{
    font-size: 12px;

    font-weight: 700;

    margin-bottom: 42px;
}}

.signature-line {{
    width: 190px;

    margin: 0 auto;

    border-top:
        1px solid #334155;

    padding-top: 6px;

    font-size: 10px;

    color: #64748b;
}}

.print-note {{
    margin-top: 15px;

    text-align: center;

    font-size: 9px;

    color: #94a3b8;
}}

@media print {{

    .print-note {{
        display: none;
    }}

}}

</style>

</head>

<body>

<div class="report">

    <div class="header">

        <div class="header-main">
            الشبكة
        </div>

        <div class="header-title">
            {html.escape(report_title)}
        </div>

        <div class="header-period">
            {html.escape(period_text)}
        </div>

        <div class="header-date">
            تاريخ ووقت الطباعة:
            {html.escape(printed_at)}
        </div>

    </div>


    <div class="summary">
        {summary_text}
    </div>


    <table>

        <thead>

            <tr>
                {headers_html}
            </tr>

        </thead>

        <tbody>

            {table_rows}

        </tbody>

    </table>


    <div class="print-note">
        للطباعة:
        اضغط Ctrl + P
        ثم اختر مقاس الورق A4
        والاتجاه الأفقي Landscape.
    </div>

</div>

</body>

</html>
"""

        # -----------------------------------------------------
        # حفظ التقرير في مجلد مؤقت
        # -----------------------------------------------------

        reports_dir = (
            Path(tempfile.gettempdir())
            / "NetworkFaultsReports"
        )

        reports_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        file_name = (
            "inventory_report_"
            + datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
            + ".html"
        )

        report_path = (
            reports_dir
            / file_name
        )

        report_path.write_text(
            html_content,
            encoding="utf-8"
        )

        # -----------------------------------------------------
        # فتح التقرير في المتصفح
        # -----------------------------------------------------

        try:

            webbrowser.open_new_tab(
                report_path.resolve().as_uri()
            )

        except Exception as error:

            QMessageBox.warning(
                self,
                "خطأ في فتح التقرير",
                "تعذر فتح التقرير في المتصفح.\n\n"
                f"{error}"
            )