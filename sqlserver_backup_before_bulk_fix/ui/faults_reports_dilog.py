from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCalendarWidget, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox
)
from database import get_connection


class FaultReportsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تقارير موقف الأعطال")
        self.resize(1100, 700)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20,20,20,20)
        root.setSpacing(12)

        title = QLabel("📋 تقارير موقف الأعطال")
        title.setStyleSheet("font-size:24px;font-weight:800;color:#17324d;")
        root.addWidget(title)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("نوع التقرير:"))
        self.period = QComboBox()
        self.period.addItems(["موقف يومي", "موقف أسبوعي"])
        self.period.currentIndexChanged.connect(self.refresh)
        bar.addWidget(self.period)

        bar.addWidget(QLabel("التاريخ:"))
        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.clicked.connect(self.refresh)
        self.calendar.setFixedHeight(180)
        bar.addWidget(self.calendar)
        root.addLayout(bar)

        buttons = QHBoxLayout()
        self.print_btn = QPushButton("🖨 طباعة الموقف")
        self.print_btn.clicked.connect(self.print_report)
        self.refresh_btn = QPushButton("↻ تحديث")
        self.refresh_btn.clicked.connect(self.refresh)
        buttons.addWidget(self.print_btn)
        buttons.addWidget(self.refresh_btn)
        buttons.addStretch()
        root.addLayout(buttons)

        self.summary = QLabel("")
        self.summary.setStyleSheet("font-weight:700;color:#40576d;")
        root.addWidget(self.summary)

        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        root.addWidget(self.table, 1)

    def date_range(self):
        d = self.calendar.selectedDate()
        start = d.toString("yyyy-MM-dd")
        if self.period.currentText() == "موقف يومي":
            return start, start

        # أسبوع يبدأ من السبت وينتهي الجمعة بما يناسب الاستخدام المحلي.
        delta = (d.dayOfWeek() % 7)  # الأحد=0 ... السبت=6
        start_date = d.addDays(-delta)
        end_date = start_date.addDays(6)
        return start_date.toString("yyyy-MM-dd"), end_date.toString("yyyy-MM-dd")

    def refresh(self):
        start, end = self.date_range()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT faults.entry_date, faults.fault_number,
                   devices.device_name, faults.user_name,
                   faults.status, faults.priority, faults.technician,
                   faults.repair_date, faults.delivery_date
            FROM faults
            LEFT JOIN devices ON devices.id=faults.device_id
            WHERE date(faults.entry_date) BETWEEN date(?) AND date(?)
            ORDER BY faults.entry_date DESC, faults.id DESC
        """, (start, end))
        rows = cur.fetchall()
        conn.close()

        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "تاريخ الدخول","رقم العطل","الجهاز","المستخدم","الحالة",
            "الأولوية","القائم بالإصلاح","تاريخ الإصلاح","تاريخ التسليم"
        ])
        self.table.setRowCount(0)

        counts = {}
        for item in rows:
            counts[item["status"] or "غير محدد"] = counts.get(item["status"] or "غير محدد", 0) + 1
            r = self.table.rowCount()
            self.table.insertRow(r)
            values = [
                item["entry_date"], item["fault_number"], item["device_name"] or "",
                item["user_name"] or "", item["status"] or "",
                item["priority"] or "", item["technician"] or "",
                item["repair_date"] or "", item["delivery_date"] or ""
            ]
            for c,v in enumerate(values):
                cell = QTableWidgetItem(str(v))
                cell.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r,c,cell)

        status_text = " | ".join(f"{k}: {v}" for k,v in counts.items())
        self.summary.setText(f"الفترة: {start} إلى {end}    |    إجمالي الأعطال: {len(rows)}    |    {status_text}")

    def print_report(self):
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "التقرير", "لا توجد أعطال في الفترة المحددة.")
            return

        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.Accepted:
            return

        start, end = self.date_range()
        title = self.period.currentText()
        html = f"""<html><head><meta charset='utf-8'><style>
        body{{font-family:Arial;direction:rtl}} h1,h3{{text-align:center}}
        table{{width:100%;border-collapse:collapse}} th,td{{border:1px solid #888;padding:5px;text-align:center}}
        th{{background:#eee}}
        </style></head><body>
        <h1>الشبكة - {title}</h1>
        <h3>الفترة: {start} إلى {end}</h3><table><tr>"""
        for c in range(self.table.columnCount()):
            html += f"<th>{self.table.horizontalHeaderItem(c).text()}</th>"
        html += "</tr>"
        for r in range(self.table.rowCount()):
            html += "<tr>"
            for c in range(self.table.columnCount()):
                html += f"<td>{self.table.item(r,c).text() if self.table.item(r,c) else ''}</td>"
            html += "</tr>"
        html += "</table></body></html>"

        doc = QTextDocument()
        doc.setHtml(html)
        doc.print_(printer)
