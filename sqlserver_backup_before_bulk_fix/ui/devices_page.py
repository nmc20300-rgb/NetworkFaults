from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QFormLayout,
    QComboBox, QDialogButtonBox, QHeaderView, QFrame, QStyle,
    QFileDialog, QProgressDialog, QScrollArea
)

from database import get_connection


STYLE = """
QWidget {
    font-family: "Segoe UI", "Tahoma";
    font-size: 12px;
    color: #334155;
}
#root { background: #f4f7fb; }
#title { color:#17324d; font-size:26px; font-weight:800; }
#subtitle { color:#718096; font-size:12px; }
#card {
    background:white;
    border:1px solid #e3eaf2;
    border-radius:12px;
}
#primary {
    background:#17324d;
    color:white;
    border:none;
    border-radius:9px;
    padding:9px 15px;
    font-weight:700;
}
#primary:hover { background:#244d70; }
#secondary {
    background:#eef3f7;
    color:#29455e;
    border:1px solid #d9e2ec;
    border-radius:9px;
    padding:9px 15px;
    font-weight:700;
}
#danger {
    background:#fff1f2;
    color:#b42318;
    border:1px solid #fecdd3;
    border-radius:9px;
    padding:9px 15px;
    font-weight:700;
}
#search {
    background:#f8fafc;
    border:1px solid #d9e2ec;
    border-radius:9px;
    padding:9px 12px;
}
QTableWidget {
    background:white;
    border:none;
    gridline-color:#edf1f5;
    selection-background-color:#e8f1f8;
    selection-color:#17324d;
    alternate-background-color:#fafcfe;
}
QHeaderView::section {
    background:#f0f4f8;
    color:#4a5d70;
    border:none;
    border-bottom:1px solid #dfe7ef;
    padding:10px;
    font-weight:800;
}
QLineEdit,QComboBox {
    background:#fbfdff;
    border:1px solid #d5dfe9;
    border-radius:8px;
    padding:8px 10px;
    min-height:20px;
}
QLineEdit:focus,QComboBox:focus {
    border:1px solid #5b8bb0;
    background:white;
}
"""


# كل أعمدة Excel المطلوبة.
EXTRA_COLUMNS = {
    "location": "TEXT",
    "user_name_en": "TEXT",
    "lock_number": "TEXT",
    "network_connection": "TEXT",
    "motherboard": "TEXT",
    "graphics_card": "TEXT",
    "hard_disk_serial": "TEXT",
    "ms_office": "TEXT",
    "scanner": "TEXT",
    "ip_address": "TEXT",
}


def ensure_device_columns():
    # الأعمدة الإضافية موجودة بالفعل في SQL Server.
    # لا نحتاج لتنفيذ أي ALTER TABLE عند تشغيل البرنامج.
    return


def clean(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def norm(value):
    return " ".join(clean(value).replace("\n", " ").replace("\r", " ").split())


# ترتيب الأعمدة الحقيقي في ملف المستخدم.
# هذا مهم حتى لو كان عنوان أحد الأعمدة مكتوباً "-" أو كان به مسافات.
EXCEL_COLUMNS = [
    "م",
    "المبنى",
    "مكان التواجد",
    "اسم الجهاز",
    "اسم المستخدم",
    "User name",
    "رقم القفل",
    "التوصيل بالشبكة",
    "Mother Board",
    "كارت الشاشة الخارجى",
    "الهارد ديسك",
    "الرقم التسلسلى للهارد",
    "المعالج المركزى",
    "-",
    "طراز الشاشة",
    "نظام التشغيل",
    "MS Office",
    "طراز الطابعة",
    "الماسح الضوئى",
    "IP",
    "الحالة الفنية",
]


HEADER_ALIASES = {
    "م": ["م", "م.", "الرقم", "رقم"],
    "المبنى": ["المبنى", "المبنى/الفرع", "الفرع"],
    "مكان التواجد": ["مكان التواجد", "مكان التواجد "],
    "اسم الجهاز": ["اسم الجهاز", "الجهاز"],
    "اسم المستخدم": ["اسم المستخدم", "المستخدم"],
    "User name": ["User name", "User Name", "Username", "USER NAME"],
    "رقم القفل": ["رقم القفل", "رقم القفل "],
    "التوصيل بالشبكة": ["التوصيل بالشبكة", "التوصيل بالشبكه"],
    "Mother Board": ["Mother Board", "Motherboard", "MOTHER BOARD"],
    "كارت الشاشة الخارجى": [
        "كارت الشاشة الخارجى",
        "كارت الشاشة الخارجي",
        "كارت الشاشة الخارجى ",
    ],
    "الهارد ديسك": ["الهارد ديسك", "الهارد", "Hard Disk"],
    "الرقم التسلسلى للهارد": [
        "الرقم التسلسلى للهارد",
        "الرقم التسلسلي للهارد",
        "Hard Disk Serial",
    ],
    "المعالج المركزى": ["المعالج المركزى", "المعالج المركزي", "Processor"],
    "-": ["-", " - ", "RAM", "الرام", "RAM "],
    "طراز الشاشة": ["طراز الشاشة", "الشاشة", "Monitor"],
    "نظام التشغيل": ["نظام التشغيل", "Operating System", "OS"],
    "MS Office": ["MS Office", "MS OFFICE", "Office"],
    "طراز الطابعة": ["طراز الطابعة", "الطابعة", "Printer"],
    "الماسح الضوئى": [
        "الماسح الضوئى",
        "الماسح الضوئي",
        "Scanner",
        "الماسح",
    ],
    "IP": ["IP", "Ip", "ip", "IP Address"],
    "الحالة الفنية": ["الحالة الفنية", "الحالة", "Status"],
}


def find_header_indexes(headers):
    """
    يطابق كل عنوان Excel مع رقمه الحقيقي.
    لا نعتمد على أسماء الأعمدة فقط؛ يوجد fallback على ترتيب الأعمدة
    الذي أرسله المستخدم، حتى لا تضيع أي خانة.
    """
    indexes = {}
    normalized = [norm(h) for h in headers]

    for wanted in EXCEL_COLUMNS:
        aliases = HEADER_ALIASES.get(wanted, [wanted])
        aliases = {norm(x) for x in aliases}

        for i, header in enumerate(normalized):
            if header in aliases:
                indexes[wanted] = i
                break

    # fallback: إذا لم يتعرف على العنوان، استخدم موضعه في الملف
    for i, wanted in enumerate(EXCEL_COLUMNS):
        if wanted not in indexes and i < len(headers):
            indexes[wanted] = i

    return indexes


class DeviceDialog(QDialog):
    def __init__(self, parent=None, device=None):
        super().__init__(parent)
        self.device = device
        self.setWindowTitle("تعديل جهاز" if device else "إضافة جهاز")
        self.resize(720, 760)
        self.setStyleSheet(STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 18)

        title = QLabel("بيانات الجهاز كاملة")
        title.setStyleSheet(
            "background:#17324d;color:white;font-size:19px;font-weight:800;"
            "padding:14px;border-radius:10px;"
        )
        root.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        body = QWidget()
        form = QFormLayout(body)
        form.setVerticalSpacing(8)
        form.setHorizontalSpacing(18)

        self.fields = {}
        field_list = [
            ("device_number", "م / رقم الجهاز"),
            ("device_name", "اسم الجهاز"),
            ("building", "المبنى"),
            ("location", "مكان التواجد"),
            ("user_name", "اسم المستخدم"),
            ("user_name_en", "User name"),
            ("lock_number", "رقم القفل"),
            ("network_connection", "التوصيل بالشبكة"),
            ("motherboard", "Mother Board"),
            ("graphics_card", "كارت الشاشة الخارجى"),
            ("hard_disk", "الهارد ديسك"),
            ("hard_disk_serial", "الرقم التسلسلى للهارد"),
            ("processor", "المعالج المركزى"),
            ("ram", "RAM"),
            ("monitor", "طراز الشاشة"),
            ("operating_system", "نظام التشغيل"),
            ("ms_office", "MS Office"),
            ("printer", "طراز الطابعة"),
            ("scanner", "الماسح الضوئى"),
            ("ip_address", "IP"),
        ]

        for key, label in field_list:
            w = QLineEdit()
            self.fields[key] = w
            form.addRow(label + ":", w)

        self.status = QComboBox()
        self.status.addItems(["صالح", "يحتاج فحص", "عطل", "خارج الخدمة"])
        form.addRow("الحالة الفنية:", self.status)

        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        if device:
            self.load_device()

    def load_device(self):
        for key, widget in self.fields.items():
            if key == "building":
                value = ""
                try:
                    value = clean(self.device["building_name"])
                except Exception:
                    pass
            else:
                try:
                    value = clean(self.device[key])
                except Exception:
                    value = ""
            widget.setText(value)

        status = clean(self.device["status"]) or "صالح"
        i = self.status.findText(status)
        if i >= 0:
            self.status.setCurrentIndex(i)

    def validate(self):
        if not self.fields["device_name"].text().strip():
            QMessageBox.warning(self, "تنبيه", "اسم الجهاز مطلوب.")
            return
        self.accept()

    def data(self):
        result = {
            key: widget.text().strip()
            for key, widget in self.fields.items()
        }
        result["status"] = self.status.currentText()
        return result


class DevicesPage(QWidget):
    def __init__(self):
        super().__init__()
        ensure_device_columns()
        self.setup_ui()
        self.load_devices()

    def setup_ui(self):
        self.setObjectName("root")
        self.setStyleSheet(STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(25, 22, 25, 22)
        root.setSpacing(13)

        head = QHBoxLayout()
        titles = QVBoxLayout()

        title = QLabel("إدارة الأجهزة")
        title.setObjectName("title")
        titles.addWidget(title)

        sub = QLabel(
            "استيراد وعرض وتعديل جميع بيانات الأجهزة كما هي في ملف Excel"
        )
        sub.setObjectName("subtitle")
        titles.addWidget(sub)

        head.addLayout(titles)
        head.addStretch()

        self.import_button = QPushButton("📥  استيراد Excel")
        self.import_button.setObjectName("primary")
        self.import_button.clicked.connect(self.import_excel)

        self.add_button = QPushButton("＋  إضافة جهاز")
        self.add_button.setObjectName("primary")
        self.add_button.clicked.connect(self.add_device)

        self.edit_button = QPushButton("✎  تعديل")
        self.edit_button.setObjectName("secondary")
        self.edit_button.clicked.connect(self.edit_device)

        self.archive_button = QPushButton("🗄  أرشفة")
        self.archive_button.setObjectName("danger")
        self.archive_button.clicked.connect(self.archive_device)

        self.clear_all_button = QPushButton("🗑  مسح الكل")
        self.clear_all_button.setObjectName("danger")
        self.clear_all_button.clicked.connect(self.clear_all_devices)

        head.addWidget(self.import_button)
        head.addWidget(self.add_button)
        head.addWidget(self.edit_button)
        head.addWidget(self.archive_button)
        head.addWidget(self.clear_all_button)
        root.addLayout(head)

        search_card = QFrame()
        search_card.setObjectName("card")
        sl = QHBoxLayout(search_card)
        sl.setContentsMargins(12, 10, 12, 10)

        sl.addWidget(QLabel("🔎"))
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText(
            "بحث برقم الجهاز أو المبنى أو المكان أو المستخدم أو IP أو Serial..."
        )
        self.search.textChanged.connect(self.load_devices)
        sl.addWidget(self.search, 1)

        # فلتر 1: المبنى / الفرع
        self.building_filter = QComboBox()
        self.building_filter.setMinimumWidth(170)
        self.building_filter.addItem("كل المباني", "")
        self.building_filter.currentIndexChanged.connect(self.load_devices)
        sl.addWidget(self.building_filter)

        # فلتر 2: الحالة الفنية
        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(150)
        self.status_filter.addItem("كل الحالات", "")
        self.status_filter.currentIndexChanged.connect(self.load_devices)
        sl.addWidget(self.status_filter)

        root.addWidget(search_card)

        table_card = QFrame()
        table_card.setObjectName("card")
        tl = QVBoxLayout(table_card)
        tl.setContentsMargins(7, 7, 7, 7)

        self.table = QTableWidget()
        self.table.setColumnCount(22)

        # ID مخفي + نفس أعمدة Excel الـ21 بدون حذف أي عمود.
        self.table.setHorizontalHeaderLabels([
            "ID",
            "م",
            "المبنى",
            "مكان التواجد",
            "اسم الجهاز",
            "اسم المستخدم",
            "User name",
            "رقم القفل",
            "التوصيل بالشبكة",
            "Mother Board",
            "كارت الشاشة الخارجى",
            "الهارد ديسك",
            "الرقم التسلسلى للهارد",
            "المعالج المركزى",
            "RAM",
            "طراز الشاشة",
            "نظام التشغيل",
            "MS Office",
            "طراز الطابعة",
            "الماسح الضوئى",
            "IP",
            "الحالة الفنية",
        ])

        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

        self.table.doubleClicked.connect(self.edit_device)

        tl.addWidget(self.table)
        root.addWidget(table_card, 1)

    def load_devices(self):
        search = self.search.text().strip()
        selected_building = self.building_filter.currentData() if hasattr(self, "building_filter") else ""
        selected_status = self.status_filter.currentData() if hasattr(self, "status_filter") else ""

        con = get_connection()
        cur = con.cursor()

        cur.execute("""
            SELECT id, name
            FROM buildings
            ORDER BY name
        """)
        buildings = cur.fetchall()

        current_building = selected_building
        self.building_filter.blockSignals(True)
        self.building_filter.clear()
        self.building_filter.addItem("كل المباني", "")
        for b in buildings:
            self.building_filter.addItem(b["name"], str(b["id"]))
        idx = self.building_filter.findData(current_building)
        self.building_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.building_filter.blockSignals(False)

        cur.execute("""
            SELECT DISTINCT status
            FROM devices
            WHERE is_archived = 0
              AND status IS NOT NULL
              AND TRIM(status) <> ''
           ORDER BY status
        """)
        statuses = cur.fetchall()

        current_status = selected_status
        self.status_filter.blockSignals(True)
        self.status_filter.clear()
        self.status_filter.addItem("كل الحالات", "")
        for s in statuses:
            self.status_filter.addItem(str(s["status"]), str(s["status"]))
        idx = self.status_filter.findData(current_status)
        self.status_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.status_filter.blockSignals(False)

        query = """
            SELECT devices.*, buildings.name AS building_name
            FROM devices
            LEFT JOIN buildings ON devices.building_id = buildings.id
            WHERE devices.is_archived = 0
        """
        params = []

        if search:
            query += """
                AND (
                    devices.device_number LIKE ?
                    OR devices.device_name LIKE ?
                    OR devices.user_name LIKE ?
                    OR devices.serial_number LIKE ?
                    OR devices.ip_address LIKE ?
                    OR devices.location LIKE ?
                    OR buildings.name LIKE ?
                )
            """
            key = f"%{search}%"
            params.extend([key] * 7)

        if selected_building:
            query += " AND devices.building_id = ?"
            params.append(int(selected_building))

        if selected_status:
            query += " AND devices.status = ?"
            params.append(selected_status)

        query += " ORDER BY devices.id ASC"
        cur.execute(query, params)
        rows = cur.fetchall()
        con.close()

        self.table.setRowCount(0)

        for d in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            values = [
                d["id"],
                d["device_number"],
                d["building_name"] or "",
                d["location"],
                d["device_name"],
                d["user_name"],
                d["user_name_en"],
                d["lock_number"],
                d["network_connection"],
                d["motherboard"],
                d["graphics_card"],
                d["hard_disk"],
                d["hard_disk_serial"],
                d["processor"],
                d["ram"],
                d["monitor"],
                d["operating_system"],
                d["ms_office"],
                d["printer"],
                d["scanner"],
                d["ip_address"],
                d["status"],
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(clean(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

    def get_selected_device(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(
                self, "تنبيه", "من فضلك اختر جهازاً أولاً."
            )
            return None

        row = selected[0].row()
        device_id = self.table.item(row, 0).text()

        con = get_connection()
        cur = con.cursor()
        cur.execute("""
            SELECT devices.*, buildings.name AS building_name
            FROM devices
            LEFT JOIN buildings ON devices.building_id = buildings.id
            WHERE devices.id = ?
        """, (device_id,))
        device = cur.fetchone()
        con.close()
        return device

    def get_building_id(self, building_name, con):
        name = clean(building_name)
        if not name:
            return None

        cur = con.cursor()
        cur.execute(
            "SELECT id FROM buildings WHERE name = ? LIMIT 1",
            (name,)
        )
        row = cur.fetchone()

        if row:
            return row["id"]

        cur.execute(
            "INSERT INTO buildings (name, location, notes) VALUES (?, ?, ?)",
            (name, "", "تم إنشاؤه تلقائياً من استيراد Excel")
        )
        return cur.lastrowid

    def add_device(self):
        dialog = DeviceDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        d = dialog.data()
        con = get_connection()
        cur = con.cursor()

        building_id = self.get_building_id(d["building"], con)

        cur.execute("""
            INSERT INTO devices (
                device_number, device_name, user_name, department,
                device_type, serial_number, processor, ram, hard_disk,
                monitor, operating_system, printer, production_year,
                status, building_id, location, user_name_en, lock_number,
                network_connection, motherboard, graphics_card,
                hard_disk_serial, ms_office, scanner, ip_address
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            d["device_number"], d["device_name"], d["user_name"], "",
            "", "", d["processor"], d["ram"], d["hard_disk"],
            d["monitor"], d["operating_system"], d["printer"], "",
            d["status"], building_id, d["location"], d["user_name_en"],
            d["lock_number"], d["network_connection"], d["motherboard"],
            d["graphics_card"], d["hard_disk_serial"], d["ms_office"],
            d["scanner"], d["ip_address"]
        ))

        con.commit()
        con.close()
        self.load_devices()

    def edit_device(self):
        device = self.get_selected_device()
        if not device:
            return

        dialog = DeviceDialog(self, device)
        if dialog.exec() != QDialog.Accepted:
            return

        d = dialog.data()
        con = get_connection()
        cur = con.cursor()
        building_id = self.get_building_id(d["building"], con)

        cur.execute("""
            UPDATE devices SET
                device_number=?, device_name=?, user_name=?,
                processor=?, ram=?, hard_disk=?, monitor=?,
                operating_system=?, printer=?, status=?,
                building_id=?, location=?, user_name_en=?,
                lock_number=?, network_connection=?, motherboard=?,
                graphics_card=?, hard_disk_serial=?, ms_office=?,
                scanner=?, ip_address=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            d["device_number"], d["device_name"], d["user_name"],
            d["processor"], d["ram"], d["hard_disk"], d["monitor"],
            d["operating_system"], d["printer"], d["status"],
            building_id, d["location"], d["user_name_en"],
            d["lock_number"], d["network_connection"], d["motherboard"],
            d["graphics_card"], d["hard_disk_serial"], d["ms_office"],
            d["scanner"], d["ip_address"], device["id"]
        ))

        con.commit()
        con.close()
        self.load_devices()

    def clear_all_devices(self):
        answer = QMessageBox.question(
            self,
            "تأكيد مسح جميع الأجهزة",
            "⚠ هل أنت متأكد من مسح جميع الأجهزة نهائيًا؟\n\n"
            "سيتم حذف الأجهزة النشطة والمؤرشفة من قاعدة البيانات، ولا يمكن التراجع عن العملية.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        con = get_connection()
        cur = con.cursor()

        try:
            # لا نحذف الأجهزة إذا كانت هناك أعطال مرتبطة بها حتى لا نفقد سجل الأعطال.
            cur.execute("SELECT COUNT(*) AS total FROM faults WHERE device_id IS NOT NULL")
            fault_count = int(cur.fetchone()["total"] or 0)

            if fault_count > 0:
                con.close()
                QMessageBox.warning(
                    self,
                    "لا يمكن المسح",
                    "يوجد أعطال مرتبطة بأجهزة مسجلة.\n\n"
                    "لم يتم حذف أي جهاز حفاظًا على سجل الأعطال.\n"
                    "احذف/عالج سجلات الأعطال المرتبطة أولًا ثم استخدم مسح الكل."
                )
                return

            cur.execute("DELETE FROM devices")
            deleted = cur.rowcount
            con.commit()
            con.close()

            self.load_devices()
            QMessageBox.information(
                self,
                "تم",
                f"تم مسح جميع الأجهزة بنجاح.\n\nعدد الأجهزة المحذوفة: {deleted}"
            )

        except Exception as exc:
            con.rollback()
            con.close()
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء مسح الأجهزة:\n{exc}"
            )


    def archive_device(self):
        device = self.get_selected_device()
        if not device:
            return

        answer = QMessageBox.question(
            self,
            "تأكيد الأرشفة",
            f"هل تريد أرشفة الجهاز:\n\n{device['device_name']}؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if answer != QMessageBox.Yes:
            return

        con = get_connection()
        cur = con.cursor()
        cur.execute("""
            UPDATE devices
            SET is_archived=1, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (device["id"],))
        con.commit()
        con.close()
        self.load_devices()

    def import_excel(self):
        try:
            from openpyxl import load_workbook
        except ImportError:
            QMessageBox.critical(
                self,
                "مكتبة ناقصة",
                "ثبت openpyxl أولاً:\n\n"
                "python -m pip install openpyxl"
            )
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "اختيار ملف Excel",
            "",
            "Excel (*.xlsx *.xlsm)"
        )
        if not file_path:
            return

        try:
            wb = load_workbook(
                file_path,
                read_only=True,
                data_only=True
            )
            ws = wb.active

            iterator = ws.iter_rows(values_only=True)
            header = next(iterator, None)

            if not header:
                wb.close()
                QMessageBox.warning(self, "تنبيه", "ملف Excel فارغ.")
                return

            indexes = find_header_indexes(header)

            # يجب أن يكون على الأقل المبنى واسم الجهاز معروفين.
            if "اسم الجهاز" not in indexes or "المبنى" not in indexes:
                wb.close()
                QMessageBox.warning(
                    self,
                    "خطأ في الملف",
                    "لم أستطع التعرف على أعمدة المبنى واسم الجهاز."
                )
                return

            def cell(row, name):
                i = indexes.get(name)
                if i is None or i >= len(row):
                    return ""
                return clean(row[i])

            imported_rows = []

            for row in iterator:
                if not row or not any(clean(x) for x in row):
                    continue

                # الصف الأول قد يكون عنواناً أو صفاً فارغاً.
                device_name = cell(row, "اسم الجهاز")
                if not device_name:
                    continue

                imported_rows.append({
                    "device_number": cell(row, "م"),
                    "building": cell(row, "المبنى"),
                    "location": cell(row, "مكان التواجد"),
                    "device_name": device_name,
                    "user_name": cell(row, "اسم المستخدم"),
                    "user_name_en": cell(row, "User name"),
                    "lock_number": cell(row, "رقم القفل"),
                    "network_connection": cell(row, "التوصيل بالشبكة"),
                    "motherboard": cell(row, "Mother Board"),
                    "graphics_card": cell(row, "كارت الشاشة الخارجى"),
                    "hard_disk": cell(row, "الهارد ديسك"),
                    "hard_disk_serial": cell(row, "الرقم التسلسلى للهارد"),
                    "processor": cell(row, "المعالج المركزى"),
                    "ram": cell(row, "-"),
                    "monitor": cell(row, "طراز الشاشة"),
                    "operating_system": cell(row, "نظام التشغيل"),
                    "ms_office": cell(row, "MS Office"),
                    "printer": cell(row, "طراز الطابعة"),
                    "scanner": cell(row, "الماسح الضوئى"),
                    "ip_address": cell(row, "IP"),
                    "status": cell(row, "الحالة الفنية") or "صالح",
                })

            wb.close()

            if not imported_rows:
                QMessageBox.warning(
                    self,
                    "تنبيه",
                    "لم يتم العثور على صفوف أجهزة."
                )
                return

            # معاينة واضحة قبل التنفيذ.
            preview = "\n".join(
                f"{i+1}. {r['device_number']} | "
                f"{r['device_name']} | {r['building']} | "
                f"{r['status']}"
                for i, r in enumerate(imported_rows[:12])
            )

            more = ""
            if len(imported_rows) > 12:
                more = f"\n... و {len(imported_rows)-12} جهاز آخر"

            answer = QMessageBox.question(
                self,
                "تأكيد الاستيراد",
                f"تم العثور على {len(imported_rows)} جهاز.\n\n"
                f"{preview}{more}\n\n"
                "سيتم نقل كل الأعمدة الـ21 كما هي إلى النظام.\n"
                "المباني غير الموجودة سيتم إنشاؤها تلقائياً.\n"
                "إذا كان رقم الجهاز موجوداً سيتم تحديث نفس الجهاز.\n\n"
                "هل تريد بدء الاستيراد؟",
                QMessageBox.Yes | QMessageBox.No
            )

            if answer != QMessageBox.Yes:
                return

            progress = QProgressDialog(
                "جاري استيراد جميع بيانات الأجهزة...",
                "إلغاء",
                0,
                len(imported_rows),
                self
            )
            progress.setWindowTitle("استيراد Excel")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.show()

            con = get_connection()
            cur = con.cursor()

            new_count = 0
            update_count = 0
            cancel = False

            for number, d in enumerate(imported_rows, 1):
                progress.setValue(number)
                if progress.wasCanceled():
                    cancel = True
                    break

                building_id = self.get_building_id(
                    d["building"], con
                )

                existing = None

                # المطابقة الأساسية: م / رقم الجهاز.
                if d["device_number"]:
                    cur.execute("""
                        SELECT id FROM devices
                        WHERE device_number=? AND is_archived=0
                        LIMIT 1
                    """, (d["device_number"],))
                    existing = cur.fetchone()

                # إذا لم يوجد رقم، نطابق باسم الجهاز.
                if not existing:
                    cur.execute("""
                        SELECT id FROM devices
                        WHERE device_name=? AND is_archived=0
                        LIMIT 1
                    """, (d["device_name"],))
                    existing = cur.fetchone()

                values = (
                    d["device_number"],
                    d["device_name"],
                    d["user_name"],
                    "",                         # department
                    "",                         # device_type
                    "",                         # serial_number
                    d["processor"],
                    d["ram"],
                    d["hard_disk"],
                    d["monitor"],
                    d["operating_system"],
                    d["printer"],
                    "",                         # production_year
                    d["status"],
                    building_id,
                    d["location"],
                    d["user_name_en"],
                    d["lock_number"],
                    d["network_connection"],
                    d["motherboard"],
                    d["graphics_card"],
                    d["hard_disk_serial"],
                    d["ms_office"],
                    d["scanner"],
                    d["ip_address"],
                )

                if existing:
                    cur.execute("""
                        UPDATE devices SET
                            device_number=?, device_name=?, user_name=?,
                            department=?, device_type=?, serial_number=?,
                            processor=?, ram=?, hard_disk=?, monitor=?,
                            operating_system=?, printer=?, production_year=?,
                            status=?, building_id=?, location=?,
                            user_name_en=?, lock_number=?,
                            network_connection=?, motherboard=?,
                            graphics_card=?, hard_disk_serial=?,
                            ms_office=?, scanner=?, ip_address=?,
                            updated_at=CURRENT_TIMESTAMP
                        WHERE id=?
                    """, values + (existing["id"],))
                    update_count += 1
                else:
                    cur.execute("""
                        INSERT INTO devices (
                            device_number, device_name, user_name,
                            department, device_type, serial_number,
                            processor, ram, hard_disk, monitor,
                            operating_system, printer, production_year,
                            status, building_id, location, user_name_en,
                            lock_number, network_connection, motherboard,
                            graphics_card, hard_disk_serial, ms_office,
                            scanner, ip_address
                        )
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, values)
                    new_count += 1

            con.commit()
            con.close()
            progress.close()

            self.load_devices()

            if cancel:
                QMessageBox.information(
                    self,
                    "تم إيقاف الاستيراد",
                    f"تم حفظ ما تم استيراده حتى لحظة الإلغاء.\n\n"
                    f"أجهزة جديدة: {new_count}\n"
                    f"أجهزة محدثة: {update_count}"
                )
            else:
                QMessageBox.information(
                    self,
                    "تم الاستيراد بالكامل",
                    f"تم استيراد الملف بالكامل بدون حذف أعمدة.\n\n"
                    f"عدد الأجهزة الجديدة: {new_count}\n"
                    f"عدد الأجهزة المحدثة: {update_count}\n\n"
                    "تم حفظ كل بيانات Excel الـ21 في قاعدة البيانات."
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "خطأ في الاستيراد",
                "حدث خطأ أثناء الاستيراد:\n\n" + str(error)
            )
