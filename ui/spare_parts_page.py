from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QDialogButtonBox, QSpinBox, QDoubleSpinBox,
    QMessageBox, QComboBox, QPlainTextEdit, QFrame, QTabWidget,
    QCheckBox, QInputDialog, QProgressBar
)

from database import get_connection, write_audit_log
from ui.reports_page import ReportsPage

APP_STYLE = """
#sparePage {
    background: #f3f6f9;
}

QTabWidget::pane {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    top: -1px;
}

QTabBar::tab {
    background: #f1f5f9;
    color: #475569;
    border: 1px solid #cbd5e1;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 18px;
    margin-left: 4px;
    font-weight: 700;
}

QTabBar::tab:selected {
    background: #0891b2;
    color: white;
    border-color: #0891b2;
}

QTabBar::tab:hover:!selected {
    background: #e2e8f0;
}

#pageTitle {
    color: #0f2338;
    font-size: 25px;
    font-weight: 800;
}

#pageSubtitle {
    color: #64748b;
    font-size: 13px;
}

#card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
}

#cardTitle {
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
}

#cardValue {
    color: #0f2338;
    font-size: 25px;
    font-weight: 800;
}

#statTitle {
    color: #475569;
    font-size: 13px;
    font-weight: 700;
}

#statValue {
    color: #0f2338;
    font-size: 32px;
    font-weight: 800;
}

#statSub {
    color: #94a3b8;
    font-size: 11px;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {
    background: white;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 7px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QPlainTextEdit:focus {
    border: 1.5px solid #0891b2;
}

QPushButton {
    border: none;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 700;
}

#primaryButton {
    background: #0891b2;
    color: white;
}

#primaryButton:hover {
    background: #0e7490;
}

#primaryButton:pressed {
    background: #155e75;
}

#secondaryButton {
    background: #f1f5f9;
    color: #0f2338;
    border: 1px solid #cbd5e1;
}

#secondaryButton:hover {
    background: #e2e8f0;
}

#secondaryButton:disabled {
    color: #94a3b8;
    background: #f8fafc;
}

#dangerButton {
    background: #fef2f2;
    color: #991b1b;
    border: 1px solid #fecaca;
}

#dangerButton:hover {
    background: #fee2e2;
}

#dangerButton:disabled {
    color: #cbd5e1;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
}

#primaryButton:disabled {
    background: #cbd5e1;
    color: white;
}

QTableWidget {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    gridline-color: #f1f5f9;
    selection-background-color: #e0f2fe;
    selection-color: #0f2338;
}

QHeaderView::section {
    background: #f8fafc;
    color: #0f2338;
    padding: 10px;
    border: none;
    border-bottom: 2px solid #0891b2;
    font-weight: 700;
}

QCheckBox {
    color: #475569;
    font-weight: 600;
}

/* --- Dialog header --- */
#dialogRoot {
    background: #f5f8fb;
}

#dialogHeader {
    background: #0f2338;
    color: white;
    border-radius: 12px;
    border-bottom: 3px solid #0891b2;
}

#dialogHeaderIcon {
    color: #26c6da;
    font-size: 26px;
    font-weight: 900;
}

#dialogTitle {
    color: white;
    font-size: 18px;
    font-weight: 800;
}

#dialogHint {
    color: #94a3b8;
    font-size: 11px;
}

#feedbackLabel {
    color: #1f8a53;
    font-weight: 700;
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
    """Create and migrate the category lookup table on SQL Server safely."""
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            IF OBJECT_ID(N'dbo.spare_part_categories', N'U') IS NULL
            BEGIN
                CREATE TABLE dbo.spare_part_categories (
                    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                    name NVARCHAR(150) NOT NULL,
                    is_active BIT NOT NULL CONSTRAINT DF_spare_part_categories_active DEFAULT (1),
                    created_at DATETIME2 NOT NULL CONSTRAINT DF_spare_part_categories_created DEFAULT (SYSDATETIME())
                );
                CREATE UNIQUE INDEX UX_spare_part_categories_name
                    ON dbo.spare_part_categories(name);
            END;
            IF COL_LENGTH('dbo.spare_parts', 'category_id') IS NULL
                ALTER TABLE dbo.spare_parts ADD category_id INT NULL;
        """)
        # Import all existing free-text categories without overwriting existing records.
        cursor.execute("""
            INSERT INTO dbo.spare_part_categories (name)
            SELECT DISTINCT LTRIM(RTRIM(p.category))
            FROM dbo.spare_parts AS p
            WHERE NULLIF(LTRIM(RTRIM(p.category)), '') IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM dbo.spare_part_categories AS c
                  WHERE LTRIM(RTRIM(c.name)) = LTRIM(RTRIM(p.category))
              );
            UPDATE p
            SET category_id = c.id
            FROM dbo.spare_parts AS p
            INNER JOIN dbo.spare_part_categories AS c
              ON LTRIM(RTRIM(c.name)) = LTRIM(RTRIM(p.category))
            WHERE p.category_id IS NULL
              AND NULLIF(LTRIM(RTRIM(p.category)), '') IS NOT NULL;
        """)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def load_categories(include_inactive=False):
    connection = get_connection()
    cursor = connection.cursor()
    query = "SELECT id, name, is_active FROM dbo.spare_part_categories"
    if not include_inactive:
        query += " WHERE is_active = 1"
    query += " ORDER BY name"
    cursor.execute(query)
    rows = cursor.fetchall()
    connection.close()
    return rows


class CategoryManagementDialog(QDialog):
    """إدارة تصنيفات قطع الغيار (إضافة / إعادة تسمية / تفعيل وتعطيل)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إدارة تصنيفات قطع الغيار")
        self.setObjectName("dialogRoot")
        self.setStyleSheet(APP_STYLE)
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(660, 580)
        self.setMinimumSize(560, 480)
        self._rows = []

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 18)
        root.setSpacing(12)

        # ---------- الهيدر ----------
        header = QFrame()
        header.setObjectName("dialogHeader")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 13, 16, 13)
        icon = QLabel("🏷")
        icon.setObjectName("dialogHeaderIcon")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(42, 42)
        hl.addWidget(icon)
        text = QVBoxLayout()
        title = QLabel("إدارة التصنيفات")
        title.setObjectName("dialogTitle")
        hint = QLabel("التصنيف المعطّل يختفي من الفلتر ومن قائمة الإضافة، والقطع القديمة تفضل زي ما هي")
        hint.setObjectName("dialogHint")
        text.addWidget(title)
        text.addWidget(hint)
        hl.addLayout(text)
        hl.addStretch()
        root.addWidget(header)

        # ---------- إضافة تصنيف ----------
        add_row = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اكتب اسم تصنيف جديد ثم اضغط Enter...")
        self.add_btn = QPushButton("＋ إضافة")
        self.add_btn.setObjectName("primaryButton")
        add_row.addWidget(self.name_input, 1)
        add_row.addWidget(self.add_btn)
        root.addLayout(add_row)

        # ---------- بحث + إظهار المعطّلة ----------
        filter_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 ابحث في التصنيفات...")
        self.search_input.setClearButtonEnabled(True)
        self.show_inactive = QCheckBox("إظهار المعطّلة")
        self.show_inactive.setChecked(True)
        filter_row.addWidget(self.search_input, 1)
        filter_row.addWidget(self.show_inactive)
        root.addLayout(filter_row)

        # ---------- الجدول ----------
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "اسم التصنيف", "عدد القطع", "الحالة"])
        self.table.setColumnHidden(0, True)
        self.table.verticalHeader().setVisible(False)
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table, 1)

        # ---------- سطر الحالة / الرسائل ----------
        info_row = QHBoxLayout()
        self.count_label = QLabel("")
        self.count_label.setObjectName("pageSubtitle")
        self.feedback = QLabel("")
        self.feedback.setObjectName("feedbackLabel")
        info_row.addWidget(self.count_label)
        info_row.addStretch()
        info_row.addWidget(self.feedback)
        root.addLayout(info_row)

        # ---------- الأزرار ----------
        buttons = QHBoxLayout()
        self.rename_btn = QPushButton("✎ إعادة تسمية")
        self.rename_btn.setObjectName("secondaryButton")
        self.toggle_btn = QPushButton("تفعيل / تعطيل")
        self.toggle_btn.setObjectName("secondaryButton")
        self.close_btn = QPushButton("إغلاق")
        self.close_btn.setObjectName("primaryButton")
        buttons.addWidget(self.rename_btn)
        buttons.addWidget(self.toggle_btn)
        buttons.addStretch()
        buttons.addWidget(self.close_btn)
        root.addLayout(buttons)

        # ---------- الربط ----------
        self.add_btn.clicked.connect(self.add_category)
        self.name_input.returnPressed.connect(self.add_category)
        self.rename_btn.clicked.connect(self.rename_category)
        self.toggle_btn.clicked.connect(self.toggle_category)
        self.close_btn.clicked.connect(self.accept)
        self.table.itemSelectionChanged.connect(self.update_buttons)
        self.table.doubleClicked.connect(lambda *_: self.rename_category())
        self.search_input.textChanged.connect(lambda *_: self.render())
        self.show_inactive.toggled.connect(lambda *_: self.render())

        self.refresh()
        self.name_input.setFocus()

    # ---------- مساعدات ----------
    def show_feedback(self, message):
        self.feedback.setText(f"✔ {message}")
        QTimer.singleShot(3000, lambda: self.feedback.setText(""))

    def current_id(self):
        if not self.table.selectedItems():
            return None
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def get_category(self, category_id):
        for category in self._rows:
            if int(category["id"]) == category_id:
                return category
        return None

    def update_buttons(self):
        category_id = self.current_id()
        category = self.get_category(category_id) if category_id is not None else None
        self.rename_btn.setEnabled(category is not None)
        self.toggle_btn.setEnabled(category is not None)
        if category is None:
            self.toggle_btn.setText("تفعيل / تعطيل")
        elif bool(category["is_active"]):
            self.toggle_btn.setText("⛔ تعطيل التصنيف")
        else:
            self.toggle_btn.setText("✅ تفعيل التصنيف")

    # ---------- تحميل وعرض ----------
    def refresh(self, select_id=None):
        if select_id is None:
            select_id = self.current_id()
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT c.id, c.name, c.is_active, COUNT(p.id) AS parts_count
                FROM dbo.spare_part_categories AS c
                LEFT JOIN dbo.spare_parts AS p
                  ON p.category_id = c.id AND p.is_archived = 0
                GROUP BY c.id, c.name, c.is_active
                ORDER BY c.name
            """)
            self._rows = cursor.fetchall()
        finally:
            connection.close()
        self.render(select_id)

    def render(self, select_id=None):
        if select_id is None:
            select_id = self.current_id()
        term = self.search_input.text().strip().lower()
        show_inactive = self.show_inactive.isChecked()

        self.table.blockSignals(True)
        self.table.setRowCount(0)
        selected_row = -1
        for category in self._rows:
            active = bool(category["is_active"])
            name = str(category["name"])
            if not active and not show_inactive:
                continue
            if term and term not in name.lower():
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = (
                category["id"], name, category["parts_count"],
                "نشط" if active else "معطّل",
            )
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                if not active:
                    item.setForeground(QColor("#94a3b8"))
                if col == 3:
                    item.setForeground(QColor("#1f8a53" if active else "#a33a3a"))
                    item.setBackground(QColor("#e8f6ee" if active else "#fbe8e8"))
                self.table.setItem(row, col, item)
            if select_id is not None and int(category["id"]) == int(select_id):
                selected_row = row
        self.table.blockSignals(False)

        if selected_row >= 0:
            self.table.selectRow(selected_row)
        self.update_buttons()
        self.count_label.setText(
            f"المعروض: {self.table.rowCount()} من أصل {len(self._rows)} تصنيف"
        )

    # ---------- العمليات ----------
    def add_category(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT id FROM dbo.spare_part_categories WHERE name = ?", (name,))
            if cursor.fetchone():
                QMessageBox.warning(self, "تصنيف موجود", "هذا التصنيف موجود بالفعل.")
                return
            cursor.execute(
                "INSERT INTO dbo.spare_part_categories (name, is_active) OUTPUT INSERTED.id VALUES (?, 1)",
                (name,),
            )
            new_id = int(cursor.fetchone()["id"])
            connection.commit()
        except Exception as exc:
            connection.rollback()
            QMessageBox.critical(self, "خطأ", f"تعذر إضافة التصنيف:\n{exc}")
            return
        finally:
            connection.close()
        self.name_input.clear()
        self.search_input.clear()
        self.refresh(select_id=new_id)
        self.show_feedback(f"تمت إضافة التصنيف: {name}")
        self.name_input.setFocus()

    def rename_category(self):
        category_id = self.current_id()
        if category_id is None:
            return
        old_name = str(self.get_category(category_id)["name"])
        new_name, ok = QInputDialog.getText(
            self, "إعادة تسمية التصنيف", "الاسم الجديد:", text=old_name
        )
        new_name = new_name.strip()
        if not ok or not new_name or new_name == old_name:
            return
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT id FROM dbo.spare_part_categories WHERE name = ? AND id <> ?",
                (new_name, category_id),
            )
            if cursor.fetchone():
                QMessageBox.warning(self, "تصنيف موجود", "يوجد تصنيف آخر بهذا الاسم.")
                return
            cursor.execute(
                "UPDATE dbo.spare_part_categories SET name = ? WHERE id = ?",
                (new_name, category_id),
            )
            cursor.execute(
                "UPDATE dbo.spare_parts SET category = ? WHERE category_id = ?",
                (new_name, category_id),
            )
            connection.commit()
        except Exception as exc:
            connection.rollback()
            QMessageBox.critical(self, "خطأ", f"تعذر إعادة تسمية التصنيف:\n{exc}")
            return
        finally:
            connection.close()
        self.refresh(select_id=category_id)
        self.show_feedback("تمت إعادة التسمية")

    def toggle_category(self):
        category_id = self.current_id()
        if category_id is None:
            return
        category = self.get_category(category_id)
        is_active = bool(category["is_active"])
        parts_count = int(category["parts_count"] or 0)

        if is_active and parts_count > 0:
            answer = QMessageBox.question(
                self,
                "تأكيد التعطيل",
                f"التصنيف \"{category['name']}\" مستخدم في {parts_count} قطعة.\n\n"
                "التعطيل هيخفيه من الفلتر ومن قائمة الإضافة فقط، "
                "والقطع الحالية هتفضل محتفظة بالتصنيف.\n\nتكمل؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE dbo.spare_part_categories SET is_active = ? WHERE id = ?",
                (0 if is_active else 1, category_id),
            )
            connection.commit()
        except Exception as exc:
            connection.rollback()
            QMessageBox.critical(self, "خطأ", f"تعذر تغيير حالة التصنيف:\n{exc}")
            return
        finally:
            connection.close()
        self.refresh(select_id=category_id)
        self.show_feedback("تم تعطيل التصنيف" if is_active else "تم تفعيل التصنيف")


def spare_part_audit_data(part):
    """Create a stable, JSON-friendly snapshot of a spare-part row."""
    if not part:
        return {}
    keys = (
        "id", "part_number", "part_name", "category", "category_id", "quantity",
        "min_quantity", "required_quantity", "unit", "supplier",
        "unit_price", "storage_location", "notes", "availability_status",
        "is_archived", "created_at", "updated_at",
    )
    snapshot = {}
    for key in keys:
        try:
            value = part[key]
        except (KeyError, IndexError, TypeError):
            continue
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        snapshot[key] = value
    return snapshot


class StatCard(QFrame):
    """كارت إحصائية: أيقونة ملوّنة + رقم كبير + نسبة + شريط تقدم. قابل للضغط للفلترة."""

    clicked = Signal()

    def __init__(self, title, accent="#0891b2", tint="#e0f2fe"):
        super().__init__()
        self.accent = accent
        self.tint = tint
        self._active = False
        self.setObjectName("statCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(118)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(10)
        self.dot = QLabel()
        self.dot.setFixedSize(10, 10)
        self.dot.setStyleSheet(f"background: {accent}; border-radius: 5px;")
        top.addWidget(self.dot)
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        top.addWidget(title_label)
        top.addStretch()
        layout.addLayout(top)

        self.value_label = QLabel("0")
        self.value_label.setObjectName("statValue")
        layout.addWidget(self.value_label)

        self.sub_label = QLabel("")
        self.sub_label.setObjectName("statSub")
        layout.addWidget(self.sub_label)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)
        self.bar.setStyleSheet(
            "QProgressBar { background: #eef2f6; border: none; border-radius: 3px; }"
            f"QProgressBar::chunk {{ background: {accent}; border-radius: 3px; }}"
        )
        layout.addWidget(self.bar)

        self._apply_style()

    def _apply_style(self):
        if self._active:
            bg, border = self.tint, self.accent
        else:
            bg, border = "white", "#e2e8f0"
        hover_bg = self.tint if self._active else "#f8fafc"
        self.setStyleSheet(f"""
            #statCard {{
                background: {bg};
                border: 1px solid {border};
                border-right: 4px solid {self.accent};
                border-radius: 14px;
            }}
            #statCard:hover {{
                background: {hover_bg};
                border: 1px solid {self.accent};
                border-right: 4px solid {self.accent};
            }}
        """)

    def set_active(self, active):
        if active != self._active:
            self._active = active
            self._apply_style()

    def set_data(self, value, total, subtitle=None):
        self.value_label.setText(str(value))
        percent = round(value * 100 / total) if total else 0
        self.bar.setValue(percent)
        self.sub_label.setText(subtitle if subtitle else f"{percent}% من الأصناف")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


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
        icon = QLabel("")
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
        self.available_btn.setCheckable(True)
        self.available_btn.setChecked(True)
        self.missing_btn = QPushButton("🔴  ناقصة ومطلوب توفيرها")
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

        self.category = QComboBox()
        self.category.addItem("بدون تصنيف", None)
        for category_row in load_categories(include_inactive=True):
            category_id = int(category_row["id"])
            category_name = str(category_row["name"])
            is_active = bool(category_row["is_active"])
            current_category_id = None
            if part:
                try:
                    current_category_id = part["category_id"]
                except (KeyError, IndexError, TypeError):
                    current_category_id = None
            is_current_category = bool(
                part and (
                    (current_category_id is not None and int(current_category_id) == category_id)
                    or str(part["category"] or "").strip() == category_name
                )
            )
            if is_active or is_current_category:
                self.category.addItem(category_name, category_id)

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

        category_id = None
        try:
            category_id = p["category_id"]
        except (KeyError, IndexError, TypeError):
            pass
        category_index = self.category.findData(category_id) if category_id is not None else -1
        if category_index < 0 and p["category"]:
            category_index = self.category.findText(str(p["category"]))
        self.category.setCurrentIndex(category_index if category_index >= 0 else 0)

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
            "category_id": self.category.currentData(),
            "category": self.category.currentText() if self.category.currentData() is not None else "",
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
    PAGE_SIZE = 50

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user or {}
        self._page = 0
        self._total = 0
        self.setObjectName("sparePage")
        self.setStyleSheet(APP_STYLE)
        ensure_spare_parts_tables()
        self.setup_ui()
        self.refresh_category_filter()
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
        self.history_button = QPushButton("سجل الحركات")
        self.history_button.setObjectName("secondaryButton")
        self.delete_button = QPushButton("حذف")
        self.delete_button.setObjectName("dangerButton")
        self.categories_button = QPushButton("إدارة التصنيفات")
        self.categories_button.setObjectName("secondaryButton")

        header.addWidget(self.categories_button)
        header.addWidget(self.add_button)
        header.addWidget(self.edit_button)
        header.addWidget(self.movement_button)
        header.addWidget(self.history_button)
        header.addWidget(self.delete_button)
        main.addLayout(header)

        cards = QHBoxLayout()
        cards.setSpacing(14)
        self.missing_card = StatCard("قطع ناقصة", "#dc2626", "#fef2f2")
        self.minimum_card = StatCard("وصلت للحد الأدنى", "#d97706", "#fffbeb")
        self.available_card = StatCard("متوفرة", "#16a34a", "#f0fdf4")
        self.total_card = StatCard("إجمالي الأصناف", "#0891b2", "#f0f9ff")
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
        self.category_filter = QComboBox()
        self.category_filter.addItem("كل التصنيفات", None)

        search_row.addWidget(self.search_box, 1)
        search_row.addWidget(self.category_filter)
        search_row.addWidget(self.filter_box)
        main.addLayout(search_row)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "رقم القطعة",
            "اسم القطعة",
            "التصنيف",
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

        pagination_row = QHBoxLayout()
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #64748b; font-size: 11px;")
        pagination_row.addWidget(self.stats_label)
        pagination_row.addStretch()

        self.previous_button = QPushButton("◀  السابق")
        self.previous_button.setObjectName("secondaryButton")
        self.previous_button.setMinimumHeight(32)
        self.previous_button.clicked.connect(self._previous_page)

        self.page_label = QLabel("صفحة 1 / 1")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setStyleSheet("font-weight: 700; min-width: 90px;")

        self.next_button = QPushButton("التالي  ▶")
        self.next_button.setObjectName("secondaryButton")
        self.next_button.setMinimumHeight(32)
        self.next_button.clicked.connect(self._next_page)

        pagination_row.addWidget(self.previous_button)
        pagination_row.addWidget(self.page_label)
        pagination_row.addWidget(self.next_button)
        main.addLayout(pagination_row)

        self.search_box.textChanged.connect(self._reset_page_and_load_parts)
        self.filter_box.currentIndexChanged.connect(self._reset_page_and_load_parts)
        self.category_filter.currentIndexChanged.connect(self._reset_page_and_load_parts)
        self.categories_button.clicked.connect(self.manage_categories)
        self.missing_card.clicked.connect(lambda: self.toggle_status_filter("القطع الناقصة"))
        self.minimum_card.clicked.connect(lambda: self.toggle_status_filter("عند الحد الأدنى"))
        self.available_card.clicked.connect(lambda: self.toggle_status_filter("المتوفرة"))
        self.total_card.clicked.connect(lambda: self.filter_box.setCurrentIndex(0))
        self.add_button.clicked.connect(self.add_part)
        self.edit_button.clicked.connect(self.edit_part)
        self.movement_button.clicked.connect(self.add_movement)
        self.history_button.clicked.connect(self.show_movement_history)
        self.delete_button.clicked.connect(self.delete_part)
        self.table.doubleClicked.connect(self.edit_part)
        self.table.itemSelectionChanged.connect(self.update_action_buttons)
        self.update_action_buttons()

        self.tabs.addTab(parts_tab, "إدارة قطع الغيار")
        self.report_page = ReportsPage()
        self.tabs.addTab(self.report_page, "التقارير")

    def refresh_category_filter(self):
        current_id = self.category_filter.currentData() if hasattr(self, "category_filter") else None
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("كل التصنيفات", None)
        # التصنيفات المعطّلة لا تظهر في الفلتر
        for category in load_categories(include_inactive=False):
            self.category_filter.addItem(str(category["name"]), int(category["id"]))
        index = self.category_filter.findData(current_id)
        self.category_filter.setCurrentIndex(index if index >= 0 else 0)
        self.category_filter.blockSignals(False)

    def manage_categories(self):
        dialog = CategoryManagementDialog(self)
        dialog.exec()
        self.refresh_category_filter()
        self._reset_page_and_load_parts()

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

    def update_action_buttons(self):
        """أزرار التعديل والحركة والحذف تتفعل فقط عند اختيار قطعة."""
        has_selection = bool(self.table.selectedItems())
        for button in (self.edit_button, self.movement_button, self.delete_button):
            button.setEnabled(has_selection)

    def toggle_status_filter(self, filter_text):
        """الضغط على كارت يفلتر بحالته، والضغط مرة تانية يرجّع كل القطع."""
        if self.filter_box.currentText() == filter_text:
            self.filter_box.setCurrentIndex(0)
        else:
            self.filter_box.setCurrentText(filter_text)

    def _reset_page_and_load_parts(self, *_args):
        self._page = 0
        self.load_parts()

    def _previous_page(self, _checked=False):
        if self._page > 0:
            self._page -= 1
            self.load_parts()

    def _next_page(self, _checked=False):
        total_pages = max(
            1,
            (self._total + self.PAGE_SIZE - 1) // self.PAGE_SIZE,
        )
        if self._page < total_pages - 1:
            self._page += 1
            self.load_parts()

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

        category_id = self.category_filter.currentData()
        if category_id is not None:
            query += " AND category_id = ?"
            params.append(int(category_id))

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

        query += " ORDER BY part_name"
        cursor.execute(query, params)
        all_parts = cursor.fetchall()
        connection.close()

        # الإحصائيات تُحسب على كل النتائج (بعد البحث والتصنيف) بغض النظر عن فلتر الحالة،
        # عشان الكروت تفضل ثابتة وتتحسب النسب صح.
        missing_count = 0
        minimum_count = 0
        available_count = 0
        status_by_id = {}

        for part in all_parts:
            status = self.compute_status(part)
            status_by_id[part["id"]] = status
            if status == "ناقص":
                missing_count += 1
            elif status == "عند الحد الأدنى":
                minimum_count += 1
            else:
                available_count += 1

        wanted_status = {
            "القطع الناقصة": "ناقص",
            "عند الحد الأدنى": "عند الحد الأدنى",
            "المتوفرة": "متوفر",
        }.get(filter_value)
        parts = [
            part for part in all_parts
            if wanted_status is None or status_by_id[part["id"]] == wanted_status
        ]

        self._total = len(parts)
        total_pages = max(
            1,
            (self._total + self.PAGE_SIZE - 1) // self.PAGE_SIZE,
        )
        self._page = min(self._page, total_pages - 1)

        start = self._page * self.PAGE_SIZE
        visible_parts = parts[start:start + self.PAGE_SIZE]

        self.table.setRowCount(0)
        for part in visible_parts:
            row = self.table.rowCount()
            self.table.insertRow(row)

            quantity = int(part["quantity"] or 0)
            minimum = int(part["min_quantity"] or 0)
            required = int(part["required_quantity"] or 0)
            status = status_by_id[part["id"]]

            if status == "ناقص":
                status_color = QColor("#a33a3a")
                status_bg = QColor("#fbe8e8")
            elif status == "عند الحد الأدنى":
                status_color = QColor("#a9790a")
                status_bg = QColor("#fff6e0")
            else:
                status_color = QColor("#1f8a53")
                status_bg = QColor("#e8f6ee")

            values = [
                part["id"],
                part["part_number"] or "",
                part["part_name"] or "",
                part["category"] or "",
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
                if column == 7:
                    item.setForeground(status_color)
                    item.setBackground(status_bg)
                self.table.setItem(row, column, item)

        overall_total = missing_count + minimum_count + available_count
        self.total_card.set_data(overall_total, overall_total, "كل الأصناف المطابقة للبحث")
        self.missing_card.set_data(missing_count, overall_total)
        self.minimum_card.set_data(minimum_count, overall_total)
        self.available_card.set_data(available_count, overall_total)

        self.total_card.set_active(filter_value == "كل القطع")
        self.missing_card.set_active(filter_value == "القطع الناقصة")
        self.minimum_card.set_active(filter_value == "عند الحد الأدنى")
        self.available_card.set_active(filter_value == "المتوفرة")

        self.page_label.setText(f"صفحة {self._page + 1} / {total_pages}")
        self.previous_button.setEnabled(self._page > 0)
        self.next_button.setEnabled(self._page < total_pages - 1)
        self.stats_label.setText(
            f"إجمالي القطع: {self._total}  |  "
            f"المعروض في الصفحة: {len(visible_parts)}"
            if self._total else "لا توجد قطع مطابقة للبحث أو الفلتر الحالي"
        )
        self.update_action_buttons()

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
                part_number, part_name, category, category_id, quantity,
                min_quantity, required_quantity, unit, supplier,
                unit_price, storage_location, notes, availability_status
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["part_number"],
            data["part_name"],
            data["category"],
            data["category_id"],
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
        inserted = cursor.fetchone()
        part_id = inserted["id"] if inserted else None
        connection.commit()
        connection.close()

        audit_new_values = dict(data)
        audit_new_values["id"] = part_id

        write_audit_log(
            user=self.current_user,
            action="إضافة",
            module_name="قطع الغيار",
            record_id=part_id,
            description=f"تمت إضافة قطعة الغيار: {data['part_name']}",
            new_values=audit_new_values,
        )

        self.load_parts()

    def edit_part(self):
        part = self.selected_part()
        if not part:
            return

        old_values = spare_part_audit_data(part)

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
                category_id = ?,
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
            data["category_id"],
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

        audit_new_values = dict(data)
        audit_new_values["id"] = part["id"]
        audit_new_values["is_archived"] = old_values.get("is_archived", 0)

        write_audit_log(
            user=self.current_user,
            action="تعديل",
            module_name="قطع الغيار",
            record_id=part["id"],
            description=f"تم تعديل بيانات قطعة الغيار: {data['part_name']}",
            old_values=old_values,
            new_values=audit_new_values,
        )

        self.load_parts()

    def add_movement(self):
        part = self.selected_part()
        if not part:
            return

        dialog = MovementDialog(self, part)
        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.get_data()
        old_quantity = int(part["quantity"] or 0)
        delta = data["quantity"]
        if data["movement_type"] == "صرف":
            delta = -delta

        new_quantity = old_quantity + delta
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

        write_audit_log(
            user=self.current_user,
            action="إضافة",
            module_name="قطع الغيار",
            record_id=part["id"],
            description=(
                f"تم تسجيل حركة {data['movement_type']} "
                f"للقطعة {part['part_name']} بكمية {data['quantity']}"
            ),
            old_values={
                "part_id": part["id"],
                "part_name": part["part_name"],
                "quantity": old_quantity,
                "availability_status": part["availability_status"],
            },
            new_values={
                "part_id": part["id"],
                "part_name": part["part_name"],
                "quantity": new_quantity,
                "availability_status": new_status,
                "movement_type": data["movement_type"],
                "movement_quantity": data["quantity"],
                "notes": data["notes"],
            },
        )

        self.load_parts()

    def show_movement_history(self):
        dialog = MovementHistoryDialog(self)
        dialog.exec()

    def delete_part(self):
        part = self.selected_part()
        if not part:
            return

        old_values = spare_part_audit_data(part)

        answer = QMessageBox.warning(
            self,
            "تأكيد الحذف",
            f"هل تريد حذف القطعة نهائيًا؟\n\n{part['part_name']}\n\n"
            "سيتم حذف سجل حركاتها أيضًا، ولا يمكن التراجع عن هذه العملية.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM spare_part_movements WHERE spare_part_id = ?",
                (part["id"],),
            )
            cursor.execute("DELETE FROM spare_parts WHERE id = ?", (part["id"],))
            connection.commit()
        except Exception as exc:
            connection.rollback()
            QMessageBox.critical(self, "خطأ", f"تعذر حذف القطعة:\n{exc}")
            return
        finally:
            connection.close()

        write_audit_log(
            user=self.current_user,
            action="حذف",
            module_name="قطع الغيار",
            record_id=part["id"],
            description=f"تم حذف قطعة الغيار: {part['part_name']}",
            old_values=old_values,
        )

        self.load_parts()