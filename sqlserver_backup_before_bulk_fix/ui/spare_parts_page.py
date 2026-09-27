import sqlite3
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QDialogButtonBox, QSpinBox, QDoubleSpinBox,
    QMessageBox, QComboBox, QPlainTextEdit, QFrame, QTabWidget
)

from database import get_connection
from ui.reports_page import ReportsPage


APP_STYLE = """
#sparePage {
    background: #f3f6f9;
}
QTabWidget::pane {
    background: white;
    border: 1px solid #e1e9ef;
    border-radius: 10px;
    top: -1px;
}
QTabBar::tab {
    background: #e8f2f6;
    color: #294760;
    border: 1px solid #dce7ec;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 18px;
    margin-left: 4px;
    font-weight: 700;
}
QTabBar::tab:selected {
    background: #17324d;
    color: white;
    border-color: #17324d;
}
QTabBar::tab:hover:!selected {
    background: #dcecf0;
}
#pageTitle {
    color: #17324d;
    font-size: 25px;
    font-weight: 800;
}
#pageSubtitle {
    color: #718096;
    font-size: 13px;
}
#card {
    background: white;
    border: 1px solid #e4eaf1;
    border-radius: 14px;
}
#cardTitle {
    color: #718096;
    font-size: 12px;
    font-weight: 700;
}
#cardValue {
    color: #17324d;
    font-size: 25px;
    font-weight: 800;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {
    background: white;
    border: 1px solid #d8e0e8;
    border-radius: 8px;
    padding: 7px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QPlainTextEdit:focus {
    border: 1px solid #4f8cc9;
}
QPushButton {
    border: none;
    border-radius: 8px;
    padding: 9px 15px;
    font-weight: 700;
}
#primaryButton {
    background: #2878b5;
    color: white;
}
#primaryButton:hover {
    background: #21699f;
}
#secondaryButton {
    background: #e8eef5;
    color: #29445c;
}
#dangerButton {
    background: #fbe8e8;
    color: #a33a3a;
}
QTableWidget {
    background: white;
    border: 1px solid #e4eaf1;
    border-radius: 12px;
    gridline-color: #edf1f5;
    selection-background-color: #dcecf8;
    selection-color: #17324d;
}
QHeaderView::section {
    background: #eef3f8;
    color: #40576d;
    padding: 10px;
    border: none;
    font-weight: 800;
}

/* --- Dialog header (same structure as the rest of the app) --- */
#dialogRoot {
    background: #f5f8fb;
}
#dialogHeader {
    background: #17324d;
    color: white;
    border-radius: 12px;
}
#dialogHeaderIcon {
    color: white;
    font-size: 26px;
    font-weight: 900;
}
#dialogTitle {
    color: white;
    font-size: 18px;
    font-weight: 800;
}
#dialogHint {
    color: #dbe7f1;
    font-size: 11px;
}

/* --- Availability segmented toggle --- */
#segmentedBar {
    background: #eef3f8;
    border-radius: 10px;
}
#segmentBtn {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 11px 14px;
    font-weight: 800;
    color: #5b6b7c;
}
#segmentBtnAvailable:checked {
    background: #e8f6ee;
    color: #1f8a53;
}
#segmentBtnMissing:checked {
    background: #fbe8e8;
    color: #a33a3a;
}

/* --- Status badges inside the table --- */
#statusBadgeAvailable {
    background: #e8f6ee;
    color: #1f8a53;
    border-radius: 8px;
    font-weight: 800;
}
#statusBadgeMinimum {
    background: #fff6e0;
    color: #a9790a;
    border-radius: 8px;
    font-weight: 800;
}
#statusBadgeMissing {
    background: #fbe8e8;
    color: #a33a3a;
    border-radius: 8px;
    font-weight: 800;
}
"""

STATUS_AVAILABLE = "متوفرة"
STATUS_MISSING = "ناقصة"

def ensure_spare_parts_tables():
    # جداول قطع الغيار موجودة بالفعل في SQL Server
    # وتم ترحيل البيانات إليها من SQLite.
    return

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS spare_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT,
            part_name TEXT NOT NULL,
            category TEXT,
            quantity INTEGER DEFAULT 0,
            min_quantity INTEGER DEFAULT 0,
            required_quantity INTEGER DEFAULT 0,
            unit TEXT DEFAULT 'قطعة',
            supplier TEXT,
            unit_price REAL DEFAULT 0,
            storage_location TEXT,
            notes TEXT,
            availability_status TEXT DEFAULT 'متوفرة',
            is_archived INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS spare_part_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spare_part_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (spare_part_id)
                REFERENCES spare_parts(id)
                ON DELETE CASCADE
        )
    """)

    # ترقية الجداول القديمة اللي اتعملت قبل إضافة عمود availability_status
    try:
        cursor.execute(
            "ALTER TABLE spare_parts ADD COLUMN availability_status TEXT DEFAULT 'متوفرة'"
        )
    except sqlite3.OperationalError:
        pass

    # تصحيح القطع القديمة اللي الكمية عندها صفر والمطلوب أكتر من صفر
    cursor.execute("""
        UPDATE spare_parts
        SET availability_status = ?
        WHERE (availability_status IS NULL OR availability_status = '')
          AND quantity < required_quantity
    """, (STATUS_MISSING,))

    cursor.execute("""
        UPDATE spare_parts
        SET availability_status = ?
        WHERE availability_status IS NULL OR availability_status = ''
    """, (STATUS_AVAILABLE,))

    connection.commit()
    connection.close()


class StatCard(QFrame):
    def __init__(self, title, value="0", symbol=""):
        super().__init__()
        self.setObjectName("card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)

        top = QHBoxLayout()
        icon = QLabel(symbol)
        icon.setStyleSheet("font-size: 23px;")
        top.addWidget(icon)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        top.addWidget(title_label)
        top.addStretch()

        layout.addLayout(top)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("cardValue")
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


class SparePartDialog(QDialog):
    def __init__(self, parent=None, part=None):
        super().__init__(parent)
        self.part = part

        self.setWindowTitle("إضافة قطعة غيار" if not part else "تعديل قطعة غيار")
        self.setObjectName("dialogRoot")
        self.resize(600, 760)
        self.setMinimumSize(560, 700)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 18)
        root.setSpacing(12)

        # ---------- هيدر الديالوج (نفس هيكل هيدر باقي النظام) ----------
        header = QFrame()
        header.setObjectName("dialogHeader")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 13, 16, 13)

        icon = QLabel("🔧")
        icon.setObjectName("dialogHeaderIcon")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(42, 42)
        hl.addWidget(icon)

        text = QVBoxLayout()
        title = QLabel("إضافة قطعة غيار جديدة" if not part else "تعديل بيانات قطعة الغيار")
        title.setObjectName("dialogTitle")
        hint = QLabel("حدد حالة القطعة أولًا: موجودة بالمخزن ولا ناقصة ومطلوب توفيرها")
        hint.setObjectName("dialogHint")
        text.addWidget(title)
        text.addWidget(hint)
        hl.addLayout(text)
        hl.addStretch()
        root.addWidget(header)

        # ---------- شريط اختيار الحالة (متوفرة / ناقصة) ----------
        segmented = QFrame()
        segmented.setObjectName("segmentedBar")
        seg_layout = QHBoxLayout(segmented)
        seg_layout.setContentsMargins(6, 6, 6, 6)
        seg_layout.setSpacing(6)

        self.available_btn = QPushButton("🟢  متوفرة بالمخزن")
        self.available_btn.setObjectName("segmentBtn")
        self.available_btn.setProperty("class", "segmentBtnAvailable")
        self.available_btn.setCheckable(True)
        self.available_btn.setChecked(True)

        self.missing_btn = QPushButton("🔴  ناقصة ومطلوب توفيرها")
        self.missing_btn.setObjectName("segmentBtn")
        self.missing_btn.setProperty("class", "segmentBtnMissing")
        self.missing_btn.setCheckable(True)

        # نستخدم object name مختلف لكل زرار عشان الـ QSS بتاع :checked يتفعل صح
        self.available_btn.setObjectName("segmentBtnAvailable")
        self.missing_btn.setObjectName("segmentBtnMissing")

        seg_layout.addWidget(self.available_btn, 1)
        seg_layout.addWidget(self.missing_btn, 1)
        root.addWidget(segmented)

        self.available_btn.clicked.connect(lambda: self.set_availability(True))
        self.missing_btn.clicked.connect(lambda: self.set_availability(False))

        # ---------- الفورم ----------
        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(9)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.part_number = QLineEdit()
        self.part_name = QLineEdit()
        self.category = QLineEdit()

        self.quantity = QSpinBox()
        self.quantity.setRange(0, 1000000)

        self.min_quantity = QSpinBox()
        self.min_quantity.setRange(0, 1000000)

        self.required_quantity = QSpinBox()
        self.required_quantity.setRange(0, 1000000)
        self.required_quantity.setValue(1)

        self.unit = QComboBox()
        self.unit.addItems(["قطعة", "كرتونة", "عبوة", "متر", "كيلو", "أخرى"])

        self.supplier = QLineEdit()

        self.unit_price = QDoubleSpinBox()
        self.unit_price.setRange(0, 100000000)
        self.unit_price.setDecimals(2)

        self.storage_location = QLineEdit()
        self.notes = QPlainTextEdit()
        self.notes.setFixedHeight(80)

        self.part_number_label = QLabel("رقم القطعة:")
        self.part_name_label = QLabel("اسم القطعة *:")
        self.category_label = QLabel("التصنيف:")
        self.quantity_label = QLabel("الكمية المتوفرة حاليًا:")
        self.min_quantity_label = QLabel("حد التنبيه (الحد الأدنى):")
        self.required_quantity_label = QLabel("الكمية المطلوب توفيرها *:")
        self.unit_label = QLabel("الوحدة:")
        self.supplier_label = QLabel("المورد:")
        self.unit_price_label = QLabel("سعر الوحدة:")
        self.storage_location_label = QLabel("مكان التخزين:")
        self.notes_label = QLabel("ملاحظات:")

        form.addRow(self.part_number_label, self.part_number)
        form.addRow(self.part_name_label, self.part_name)
        form.addRow(self.category_label, self.category)
        form.addRow(self.quantity_label, self.quantity)
        form.addRow(self.min_quantity_label, self.min_quantity)
        form.addRow(self.required_quantity_label, self.required_quantity)
        form.addRow(self.unit_label, self.unit)
        form.addRow(self.supplier_label, self.supplier)
        form.addRow(self.unit_price_label, self.unit_price)
        form.addRow(self.storage_location_label, self.storage_location)
        form.addRow(self.notes_label, self.notes)

        root.addLayout(form, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        # الحالة الابتدائية: متوفرة
        self.set_availability(True)

        if part:
            self.load_part()

    def set_availability(self, is_available: bool):
        """يبدّل شكل الفورم حسب اختيار (متوفرة / ناقصة)."""
        self.available_btn.setChecked(is_available)
        self.missing_btn.setChecked(not is_available)

        # الكمية الحالية وحد التنبيه مهمين لما القطعة متوفرة بالمخزن
        self.quantity_label.setVisible(is_available)
        self.quantity.setVisible(is_available)
        self.min_quantity_label.setVisible(is_available)
        self.min_quantity.setVisible(is_available)

        # الكمية المطلوب توفيرها مهمة لما القطعة ناقصة
        self.required_quantity_label.setVisible(not is_available)
        self.required_quantity.setVisible(not is_available)

        if not is_available:
            # القطعة ناقصة: مفيش رصيد حالي منها
            self.quantity.setValue(0)
            if self.required_quantity.value() <= 0:
                self.required_quantity.setValue(1)
        else:
            self.required_quantity.setValue(0)

    def load_part(self):
        p = self.part
        self.part_number.setText(p["part_number"] or "")
        self.part_name.setText(p["part_name"] or "")
        self.category.setText(p["category"] or "")
        self.quantity.setValue(int(p["quantity"] or 0))
        self.min_quantity.setValue(int(p["min_quantity"] or 0))
        self.required_quantity.setValue(int(p["required_quantity"] or 0))

        index = self.unit.findText(p["unit"] or "قطعة")
        if index >= 0:
            self.unit.setCurrentIndex(index)

        self.supplier.setText(p["supplier"] or "")
        self.unit_price.setValue(float(p["unit_price"] or 0))
        self.storage_location.setText(p["storage_location"] or "")
        self.notes.setPlainText(p["notes"] or "")

        saved_status = None
        try:
            saved_status = p["availability_status"]
        except (KeyError, IndexError):
            saved_status = None

        if saved_status:
            is_available = saved_status == STATUS_AVAILABLE
        else:
            # توافق مع بيانات قديمة متسجلة قبل إضافة العمود
            is_available = int(p["quantity"] or 0) >= int(p["required_quantity"] or 0)

        self.set_availability(is_available)

        # نرجّع القيم الحقيقية بعد ما set_availability صفّرت حقل مقفول
        self.quantity.setValue(int(p["quantity"] or 0))
        self.required_quantity.setValue(int(p["required_quantity"] or 0))

    def validate_and_accept(self):
        if not self.part_name.text().strip():
            QMessageBox.warning(self, "تنبيه", "اسم القطعة مطلوب.")
            self.part_name.setFocus()
            return

        if self.missing_btn.isChecked() and self.required_quantity.value() <= 0:
            QMessageBox.warning(
                self, "تنبيه",
                "من فضلك حدد الكمية المطلوب توفيرها للقطعة الناقصة."
            )
            self.required_quantity.setFocus()
            return

        self.accept()

    def get_data(self):
        is_available = self.available_btn.isChecked()
        return {
            "part_number": self.part_number.text().strip(),
            "part_name": self.part_name.text().strip(),
            "category": self.category.text().strip(),
            "quantity": self.quantity.value(),
            "min_quantity": self.min_quantity.value(),
            "required_quantity": self.required_quantity.value(),
            "unit": self.unit.currentText(),
            "supplier": self.supplier.text().strip(),
            "unit_price": self.unit_price.value(),
            "storage_location": self.storage_location.text().strip(),
            "notes": self.notes.toPlainText().strip(),
            "availability_status": STATUS_AVAILABLE if is_available else STATUS_MISSING,
        }


class MovementDialog(QDialog):
    def __init__(self, parent, part):
        super().__init__(parent)
        self.part = part

        self.setWindowTitle("حركة مخزون")
        self.resize(430, 300)

        layout = QVBoxLayout(self)

        title = QLabel(f"حركة مخزون — {part['part_name']}")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        form = QFormLayout()

        self.movement_type = QComboBox()
        self.movement_type.addItems(["إضافة", "صرف", "إرجاع"])

        self.quantity = QSpinBox()
        self.quantity.setRange(1, 1000000)

        self.notes = QPlainTextEdit()
        self.notes.setFixedHeight(80)

        form.addRow("نوع الحركة:", self.movement_type)
        form.addRow("الكمية:", self.quantity)
        form.addRow("ملاحظات:", self.notes)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def validate_and_accept(self):
        if self.movement_type.currentText() == "صرف":
            if self.quantity.value() > int(self.part["quantity"] or 0):
                QMessageBox.warning(
                    self,
                    "تنبيه",
                    "الكمية المطلوب صرفها أكبر من الكمية المتاحة."
                )
                return
        self.accept()

    def get_data(self):
        return {
            "movement_type": self.movement_type.currentText(),
            "quantity": self.quantity.value(),
            "notes": self.notes.toPlainText().strip(),
        }


class MovementHistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("سجل حركات قطع الغيار")
        self.resize(980, 620)
        self.setStyleSheet(APP_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("سجل حركات المخزون")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel("متابعة كل عمليات الإضافة والصرف والإرجاع مع الرصيد الحالي")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        filters = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("ابحث باسم القطعة أو رقمها أو الملاحظات...")

        self.type_box = QComboBox()
        self.type_box.addItems(["كل الحركات", "إضافة", "صرف", "إرجاع"])

        filters.addWidget(self.search_box, 1)
        filters.addWidget(self.type_box)
        layout.addLayout(filters)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "التاريخ", "رقم القطعة", "اسم القطعة", "نوع الحركة",
            "الكمية", "الرصيد الحالي", "الملاحظات"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table, 1)

        self.summary = QLabel("")
        self.summary.setObjectName("pageSubtitle")
        layout.addWidget(self.summary)

        close_button = QPushButton("إغلاق")
        close_button.setObjectName("secondaryButton")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, 0, Qt.AlignLeft)

        self.search_box.textChanged.connect(self.load_history)
        self.type_box.currentIndexChanged.connect(self.load_history)
        self.load_history()

    def load_history(self):
        search = self.search_box.text().strip()
        movement_type = self.type_box.currentText()

        connection = get_connection()
        cursor = connection.cursor()

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
            JOIN spare_parts p ON p.id = m.spare_part_id
            WHERE 1 = 1
        """
        params = []

        if search:
            query += """
                AND (p.part_name LIKE ? OR p.part_number LIKE ? OR m.notes LIKE ?)
            """
            keyword = f"%{search}%"
            params.extend([keyword, keyword, keyword])

        if movement_type != "كل الحركات":
            query += " AND m.movement_type = ?"
            params.append(movement_type)

        query += " ORDER BY m.id DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        cursor.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN movement_type = 'إضافة' THEN quantity ELSE 0 END), 0) AS added,
                COALESCE(SUM(CASE WHEN movement_type = 'صرف' THEN quantity ELSE 0 END), 0) AS issued,
                COALESCE(SUM(CASE WHEN movement_type = 'إرجاع' THEN quantity ELSE 0 END), 0) AS returned
            FROM spare_part_movements
        """)
        totals = cursor.fetchone()
        connection.close()

        self.table.setRowCount(0)
        for item in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                item["created_at"] or "",
                item["part_number"] or "",
                item["part_name"] or "",
                item["movement_type"] or "",
                item["quantity"] or 0,
                item["current_quantity"] or 0,
                item["notes"] or "",
            ]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                cell.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, cell)

        self.summary.setText(
            f"إجمالي الإضافات: {totals['added']}   |   "
            f"إجمالي الصرف: {totals['issued']}   |   "
            f"إجمالي الإرجاع: {totals['returned']}   |   "
            f"عدد الحركات المعروضة: {len(rows)}"
        )


class SparePartsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("sparePage")
        self.setStyleSheet(APP_STYLE)

        ensure_spare_parts_tables()

        self.setup_ui()
        self.load_parts()

    def setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(False)
        outer.addWidget(self.tabs)

        parts_tab = QWidget()
        main = QVBoxLayout(parts_tab)
        main.setContentsMargins(25, 25, 25, 25)
        main.setSpacing(14)

        header = QHBoxLayout()

        title_box = QVBoxLayout()

        title = QLabel("إدارة قطع الغيار")
        title.setObjectName("pageTitle")
        title_box.addWidget(title)

        subtitle = QLabel(
            "متابعة المخزون والناقص والحد الأدنى وحركات الصرف والإضافة"
        )
        subtitle.setObjectName("pageSubtitle")
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch()

        self.add_button = QPushButton("＋ إضافة قطعة")
        self.add_button.setObjectName("primaryButton")

        self.edit_button = QPushButton("✎ تعديل")
        self.edit_button.setObjectName("secondaryButton")

        self.movement_button = QPushButton("↕ حركة مخزون")
        self.movement_button.setObjectName("secondaryButton")

        self.history_button = QPushButton("📋 سجل الحركات")
        self.history_button.setObjectName("secondaryButton")

        self.archive_button = QPushButton("🗄 أرشفة")
        self.archive_button.setObjectName("dangerButton")

        header.addWidget(self.add_button)
        header.addWidget(self.edit_button)
        header.addWidget(self.movement_button)
        header.addWidget(self.history_button)
        header.addWidget(self.archive_button)

        main.addLayout(header)

        cards = QHBoxLayout()
        self.missing_card = StatCard("قطع ناقصة", "0", "🔴")
        self.minimum_card = StatCard("وصلت للحد الأدنى", "0", "🟡")
        self.available_card = StatCard("متوفرة", "0", "🟢")
        self.total_card = StatCard("إجمالي الأصناف", "0", "📦")

        cards.addWidget(self.missing_card)
        cards.addWidget(self.minimum_card)
        cards.addWidget(self.available_card)
        cards.addWidget(self.total_card)

        main.addLayout(cards)

        search_row = QHBoxLayout()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "ابحث باسم القطعة أو رقم القطعة أو المورد..."
        )

        self.filter_box = QComboBox()
        self.filter_box.addItems([
            "كل القطع",
            "القطع الناقصة",
            "عند الحد الأدنى",
            "المتوفرة"
        ])

        search_row.addWidget(self.search_box, 1)
        search_row.addWidget(self.filter_box)

        main.addLayout(search_row)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "رقم القطعة",
            "اسم القطعة",
            "المتاح",
            "الحد الأدنى",
            "المطلوب",
            "الحالة",
            "المورد",
            "مكان التخزين",
        ])

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        main.addWidget(self.table, 1)

        self.search_box.textChanged.connect(self.load_parts)
        self.filter_box.currentIndexChanged.connect(self.load_parts)
        self.add_button.clicked.connect(self.add_part)
        self.edit_button.clicked.connect(self.edit_part)
        self.movement_button.clicked.connect(self.add_movement)
        self.history_button.clicked.connect(self.show_movement_history)
        self.archive_button.clicked.connect(self.archive_part)
        self.table.doubleClicked.connect(self.edit_part)

        self.tabs.addTab(parts_tab, "📦 إدارة قطع الغيار")
        self.report_page = ReportsPage()
        self.tabs.addTab(self.report_page, "📊 التقارير")

    def compute_status(self, part):
        """يحدد حالة القطعة: ناقصة / عند الحد الأدنى / متوفرة."""
        quantity = int(part["quantity"] or 0)
        minimum = int(part["min_quantity"] or 0)
        required = int(part["required_quantity"] or 0)

        try:
            explicit_status = part["availability_status"]
        except (KeyError, IndexError):
            explicit_status = None

        if explicit_status == STATUS_MISSING or quantity < required:
            return "ناقص"
        if quantity <= minimum:
            return "عند الحد الأدنى"
        return "متوفر"

    def load_parts(self):
        search = self.search_box.text().strip()
        filter_value = self.filter_box.currentText()

        connection = get_connection()
        cursor = connection.cursor()

        query = """
            SELECT *
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
                )
            """
            keyword = f"%{search}%"
            params.extend([keyword, keyword, keyword])

        if filter_value == "القطع الناقصة":
            query += " AND (availability_status = ? OR quantity < required_quantity)"
            params.append(STATUS_MISSING)
        elif filter_value == "عند الحد الأدنى":
            query += """
                AND (availability_status IS NULL OR availability_status != ?)
                AND quantity >= required_quantity
                AND quantity <= min_quantity
            """
            params.append(STATUS_MISSING)
        elif filter_value == "المتوفرة":
            query += """
                AND (availability_status IS NULL OR availability_status != ?)
                AND quantity >= required_quantity
                AND quantity > min_quantity
            """
            params.append(STATUS_MISSING)

        query += " ORDER BY part_name"

        cursor.execute(query, params)
        parts = cursor.fetchall()
        connection.close()

        missing_count = 0
        minimum_count = 0
        available_count = 0

        self.table.setRowCount(0)

        for part in parts:
            row = self.table.rowCount()
            self.table.insertRow(row)

            quantity = int(part["quantity"] or 0)
            minimum = int(part["min_quantity"] or 0)
            required = int(part["required_quantity"] or 0)
            status = self.compute_status(part)

            if status == "ناقص":
                missing_count += 1
                status_color = QColor("#a33a3a")
                status_bg = QColor("#fbe8e8")
            elif status == "عند الحد الأدنى":
                minimum_count += 1
                status_color = QColor("#a9790a")
                status_bg = QColor("#fff6e0")
            else:
                available_count += 1
                status_color = QColor("#1f8a53")
                status_bg = QColor("#e8f6ee")

            values = [
                part["id"],
                part["part_number"] or "",
                part["part_name"] or "",
                quantity,
                minimum,
                required,
                status,
                part["supplier"] or "",
                part["storage_location"] or "",
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                if column == 6:
                    item.setForeground(status_color)
                    item.setBackground(status_bg)
                self.table.setItem(row, column, item)

        self.total_card.set_value(missing_count + minimum_count + available_count)
        self.missing_card.set_value(missing_count)
        self.minimum_card.set_value(minimum_count)
        self.available_card.set_value(available_count)

    def selected_part(self):
        selected = self.table.selectedItems()

        if not selected:
            QMessageBox.information(
                self,
                "تنبيه",
                "من فضلك اختر قطعة أولًا."
            )
            return None

        row = selected[0].row()
        part_id = self.table.item(row, 0).text()

        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM spare_parts WHERE id = ?",
            (part_id,)
        )
        part = cursor.fetchone()
        connection.close()

        return part

    def add_part(self):
        dialog = SparePartDialog(self)

        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.get_data()

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO spare_parts (
                part_number, part_name, category, quantity,
                min_quantity, required_quantity, unit, supplier,
                unit_price, storage_location, notes, availability_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["part_number"],
            data["part_name"],
            data["category"],
            data["quantity"],
            data["min_quantity"],
            data["required_quantity"],
            data["unit"],
            data["supplier"],
            data["unit_price"],
            data["storage_location"],
            data["notes"],
            data["availability_status"],
        ))

        connection.commit()
        connection.close()

        self.load_parts()

    def edit_part(self):
        part = self.selected_part()
        if not part:
            return

        dialog = SparePartDialog(self, part)

        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.get_data()

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE spare_parts
            SET
                part_number = ?,
                part_name = ?,
                category = ?,
                quantity = ?,
                min_quantity = ?,
                required_quantity = ?,
                unit = ?,
                supplier = ?,
                unit_price = ?,
                storage_location = ?,
                notes = ?,
                availability_status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data["part_number"],
            data["part_name"],
            data["category"],
            data["quantity"],
            data["min_quantity"],
            data["required_quantity"],
            data["unit"],
            data["supplier"],
            data["unit_price"],
            data["storage_location"],
            data["notes"],
            data["availability_status"],
            part["id"],
        ))

        connection.commit()
        connection.close()

        self.load_parts()

    def add_movement(self):
        part = self.selected_part()
        if not part:
            return

        dialog = MovementDialog(self, part)

        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.get_data()

        delta = data["quantity"]
        if data["movement_type"] == "صرف":
            delta = -delta

        new_quantity = int(part["quantity"] or 0) + delta

        if new_quantity < 0:
            QMessageBox.warning(
                self,
                "تنبيه",
                "لا يمكن أن تصبح الكمية أقل من صفر."
            )
            return

        required = int(part["required_quantity"] or 0)
        new_status = STATUS_MISSING if new_quantity < required else STATUS_AVAILABLE

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE spare_parts
            SET quantity = ?, availability_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_quantity, new_status, part["id"]))

        cursor.execute("""
            INSERT INTO spare_part_movements (
                spare_part_id, movement_type, quantity, notes
            )
            VALUES (?, ?, ?, ?)
        """, (
            part["id"],
            data["movement_type"],
            data["quantity"],
            data["notes"],
        ))

        connection.commit()
        connection.close()

        self.load_parts()

    def show_movement_history(self):
        dialog = MovementHistoryDialog(self)
        dialog.exec()

    def archive_part(self):
        part = self.selected_part()
        if not part:
            return

        answer = QMessageBox.question(
            self,
            "تأكيد الأرشفة",
            f"هل تريد أرشفة القطعة:\n\n{part['part_name']}؟",
            QMessageBox.Yes | QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE spare_parts
            SET is_archived = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (part["id"],))

        connection.commit()
        connection.close()

        self.load_parts()
