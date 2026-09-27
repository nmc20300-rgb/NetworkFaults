import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QDialog,
    QFormLayout,
    QComboBox,
    QDialogButtonBox,
    QHeaderView,
    QFrame,
    QFileDialog,
    QProgressDialog,
    QScrollArea,
)

from database import (
    get_connection,
    write_audit_log,
)


# ============================================================
# STYLE
# ============================================================

STYLE = """
QWidget {
    font-family: "IBM Plex Sans Arabic", "Segoe UI", "Tahoma";
    font-size: 12px;
    color: #334155;
}

#root {
    background: #f4f7fb;
}

#title {
    color: #0f2338;
    font-size: 26px;
    font-weight: 800;
}

#subtitle {
    color: #64748b;
    font-size: 12px;
}

#card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
}

#primary {
    background: #0891b2;
    color: white;
    border: none;
    border-radius: 9px;
    padding: 9px 16px;
    font-weight: 700;
}

#primary:hover {
    background: #0e7490;
}

#primary:pressed {
    background: #155e75;
}

#secondary {
    background: #f1f5f9;
    color: #0f2338;
    border: 1px solid #cbd5e1;
    border-radius: 9px;
    padding: 9px 16px;
    font-weight: 700;
}

#secondary:hover {
    background: #e2e8f0;
}

#danger {
    background: #fef2f2;
    color: #991b1b;
    border: 1px solid #fecaca;
    border-radius: 9px;
    padding: 9px 16px;
    font-weight: 700;
}

#danger:hover {
    background: #fee2e2;
}

#search {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 9px;
    padding: 9px 12px;
}

#search:focus {
    border: 1.5px solid #0891b2;
    background: white;
}

QTableWidget {
    background: white;
    border: none;
    gridline-color: #f1f5f9;
    selection-background-color: #e0f2fe;
    selection-color: #0f2338;
    alternate-background-color: #f8fafc;
}

QHeaderView::section {
    background: #f8fafc;
    color: #0f2338;
    border: none;
    border-bottom: 2px solid #0891b2;
    padding: 10px;
    font-weight: 700;
}

QLineEdit,
QComboBox {
    background: #fbfdff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 10px;
    min-height: 20px;
}

QLineEdit:focus,
QComboBox:focus {
    border: 1.5px solid #0891b2;
    background: white;
}
"""


# ============================================================
# Excel Columns
# ============================================================

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
    """
    أعمدة الأجهزة موجودة بالفعل في SQL Server.
    لا نحتاج إلى ALTER TABLE أثناء التشغيل.
    """
    return


# ============================================================
# Helpers
# ============================================================

def clean(value):
    if value is None:
        return ""

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value).strip()


def norm(value):
    return " ".join(
        clean(value)
        .replace("\n", " ")
        .replace("\r", " ")
        .split()
    )


def device_audit_data(device):
    """
    تحويل بيانات الجهاز إلى Dictionary مناسب لسجل العمليات.
    """

    if not device:
        return {}

    keys = [
        "id",
        "device_number",
        "device_name",
        "user_name",
        "processor",
        "ram",
        "hard_disk",
        "monitor",
        "operating_system",
        "printer",
        "status",
        "building_id",
        "location",
        "user_name_en",
        "lock_number",
        "network_connection",
        "motherboard",
        "graphics_card",
        "hard_disk_serial",
        "ms_office",
        "scanner",
        "ip_address",
        "is_archived",
    ]

    result = {}

    for key in keys:

        try:
            result[key] = clean(
                device[key]
            )

        except Exception:
            pass

    try:

        result["building_name"] = clean(
            device["building_name"]
        )

    except Exception:
        pass

    return result


# ============================================================
# Excel Structure
# ============================================================

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

    "م": [
        "م",
        "م.",
        "الرقم",
        "رقم",
    ],

    "المبنى": [
        "المبنى",
        "المبنى/الفرع",
        "الفرع",
    ],

    "مكان التواجد": [
        "مكان التواجد",
        "مكان التواجد ",
    ],

    "اسم الجهاز": [
        "اسم الجهاز",
        "الجهاز",
    ],

    "اسم المستخدم": [
        "اسم المستخدم",
        "المستخدم",
    ],

    "User name": [
        "User name",
        "User Name",
        "Username",
        "USER NAME",
    ],

    "رقم القفل": [
        "رقم القفل",
        "رقم القفل ",
    ],

    "التوصيل بالشبكة": [
        "التوصيل بالشبكة",
        "التوصيل بالشبكه",
    ],

    "Mother Board": [
        "Mother Board",
        "Motherboard",
        "MOTHER BOARD",
    ],

    "كارت الشاشة الخارجى": [
        "كارت الشاشة الخارجى",
        "كارت الشاشة الخارجي",
        "كارت الشاشة الخارجى ",
    ],

    "الهارد ديسك": [
        "الهارد ديسك",
        "الهارد",
        "Hard Disk",
    ],

    "الرقم التسلسلى للهارد": [
        "الرقم التسلسلى للهارد",
        "الرقم التسلسلي للهارد",
        "Hard Disk Serial",
    ],

    "المعالج المركزى": [
        "المعالج المركزى",
        "المعالج المركزي",
        "Processor",
    ],

    "-": [
        "-",
        " - ",
        "RAM",
        "الرام",
        "RAM ",
    ],

    "طراز الشاشة": [
        "طراز الشاشة",
        "الشاشة",
        "Monitor",
    ],

    "نظام التشغيل": [
        "نظام التشغيل",
        "Operating System",
        "OS",
    ],

    "MS Office": [
        "MS Office",
        "MS OFFICE",
        "Office",
    ],

    "طراز الطابعة": [
        "طراز الطابعة",
        "الطابعة",
        "Printer",
    ],

    "الماسح الضوئى": [
        "الماسح الضوئى",
        "الماسح الضوئي",
        "Scanner",
        "الماسح",
    ],

    "IP": [
        "IP",
        "Ip",
        "ip",
        "IP Address",
    ],

    "الحالة الفنية": [
        "الحالة الفنية",
        "الحالة",
        "Status",
    ],
}


def find_header_indexes(headers):
    """
    مطابقة عناوين Excel مع الأعمدة الفعلية.

    يتم الاعتماد أولاً على اسم العمود،
    ثم يتم استخدام ترتيب الأعمدة كـ fallback.
    """

    indexes = {}

    normalized = [
        norm(header)
        for header in headers
    ]

    for wanted in EXCEL_COLUMNS:

        aliases = HEADER_ALIASES.get(
            wanted,
            [wanted],
        )

        aliases = {
            norm(alias)
            for alias in aliases
        }

        for index, header in enumerate(
            normalized
        ):

            if header in aliases:

                indexes[wanted] = index

                break

    # Fallback حسب ترتيب الملف
    for index, wanted in enumerate(
        EXCEL_COLUMNS
    ):

        if (
            wanted not in indexes
            and index < len(headers)
        ):

            indexes[wanted] = index

    return indexes


# ============================================================
# Device Dialog
# ============================================================

class DeviceDialog(QDialog):

    def __init__(
        self,
        parent=None,
        device=None,
    ):
        super().__init__(parent)

        self.device = device

        self.setWindowTitle(
            "تعديل جهاز"
            if device
            else "إضافة جهاز"
        )

        self.resize(
            720,
            760,
        )

        self.setStyleSheet(
            STYLE
        )

        root = QVBoxLayout(self)

        root.setContentsMargins(
            20,
            20,
            20,
            18,
        )

        title = QLabel(
            "بيانات الجهاز كاملة"
        )

        title.setStyleSheet(
            "background:#0f2338;"
            "color:white;"
            "font-size:19px;"
            "font-weight:800;"
            "padding:14px;"
            "border-radius:10px;"
            "border-bottom:3px solid #0891b2;"
        )

        root.addWidget(title)

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setFrameShape(
            QFrame.NoFrame
        )

        body = QWidget()

        form = QFormLayout(body)

        form.setVerticalSpacing(
            8
        )

        form.setHorizontalSpacing(
            18
        )

        self.fields = {}

        field_list = [
            (
                "device_number",
                "م / رقم الجهاز",
            ),
            (
                "device_name",
                "اسم الجهاز",
            ),
            (
                "building",
                "المبنى",
            ),
            (
                "location",
                "مكان التواجد",
            ),
            (
                "user_name",
                "اسم المستخدم",
            ),
            (
                "user_name_en",
                "User name",
            ),
            (
                "lock_number",
                "رقم القفل",
            ),
            (
                "network_connection",
                "التوصيل بالشبكة",
            ),
            (
                "motherboard",
                "Mother Board",
            ),
            (
                "graphics_card",
                "كارت الشاشة الخارجى",
            ),
            (
                "hard_disk",
                "الهارد ديسك",
            ),
            (
                "hard_disk_serial",
                "الرقم التسلسلى للهارد",
            ),
            (
                "processor",
                "المعالج المركزى",
            ),
            (
                "ram",
                "RAM",
            ),
            (
                "monitor",
                "طراز الشاشة",
            ),
            (
                "operating_system",
                "نظام التشغيل",
            ),
            (
                "ms_office",
                "MS Office",
            ),
            (
                "printer",
                "طراز الطابعة",
            ),
            (
                "scanner",
                "الماسح الضوئى",
            ),
            (
                "ip_address",
                "IP",
            ),
        ]

        for key, label in field_list:

            widget = QLineEdit()

            self.fields[key] = widget

            form.addRow(
                label + ":",
                widget,
            )

        self.status = QComboBox()

        self.status.addItems(
            [
                "صالح",
                "يحتاج فحص",
                "عطل",
                "خارج الخدمة",
            ]
        )

        form.addRow(
            "الحالة الفنية:",
            self.status,
        )

        scroll.setWidget(
            body
        )

        root.addWidget(
            scroll,
            1,
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(
            self.validate
        )

        buttons.rejected.connect(
            self.reject
        )

        root.addWidget(
            buttons
        )

        if device:
            self.load_device()

    def load_device(self):

        for key, widget in self.fields.items():

            if key == "building":

                value = ""

                try:
                    value = clean(
                        self.device[
                            "building_name"
                        ]
                    )
                except Exception:
                    pass

            else:

                try:
                    value = clean(
                        self.device[key]
                    )

                except Exception:

                    value = ""

            widget.setText(
                value
            )

        try:

            status = (
                clean(
                    self.device[
                        "status"
                    ]
                )
                or "صالح"
            )

        except Exception:

            status = "صالح"

        index = self.status.findText(
            status
        )

        if index >= 0:

            self.status.setCurrentIndex(
                index
            )

    def validate(self):

        if not self.fields[
            "device_name"
        ].text().strip():

            QMessageBox.warning(
                self,
                "تنبيه",
                "اسم الجهاز مطلوب.",
            )

            return

        self.accept()

    def data(self):

        result = {
            key: widget.text().strip()
            for key, widget in self.fields.items()
        }

        result["status"] = (
            self.status.currentText()
        )

        return result


# ============================================================
# Devices Page
# ============================================================

class DevicesPage(QWidget):

    def __init__(
        self,
        current_user=None,
    ):
        super().__init__()

        self.current_user = (
            current_user or {}
        )

        ensure_device_columns()

        self.setup_ui()

        self.apply_permissions()

        self.load_devices()

    # ========================================================
    # Permission System
    # ========================================================

    def has_permission(self, code):

        role = str(
            self.current_user.get(
                "role_code",
                "",
            )
        ).strip().upper()

        if role == "SUPER_ADMIN":
            return True

        permissions = (
            self.current_user.get(
                "permissions",
                {},
            )
        )

        if not isinstance(
            permissions,
            dict,
        ):
            return False

        return bool(
            permissions.get(
                code,
                False,
            )
        )

    def apply_permissions(self):

        can_add = self.has_permission(
            "devices.add"
        )

        can_edit = self.has_permission(
            "devices.edit"
        )

        can_delete = self.has_permission(
            "devices.delete"
        )

        self.import_button.setVisible(
            can_add
        )

        self.add_button.setVisible(
            can_add
        )

        self.edit_button.setVisible(
            can_edit
        )

        self.archive_button.setVisible(
            can_delete
        )

        self.clear_all_button.setVisible(
            can_delete
        )

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):

        self.setObjectName(
            "root"
        )

        self.setStyleSheet(
            STYLE
        )

        root = QVBoxLayout(self)

        root.setContentsMargins(
            25,
            22,
            25,
            22,
        )

        root.setSpacing(
            13
        )

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        head = QHBoxLayout()

        titles = QVBoxLayout()

        title = QLabel(
            "إدارة الأجهزة"
        )

        title.setObjectName(
            "title"
        )

        titles.addWidget(
            title
        )

        subtitle = QLabel(
            "استيراد وعرض وتعديل جميع بيانات الأجهزة كما هي في ملف Excel"
        )

        subtitle.setObjectName(
            "subtitle"
        )

        titles.addWidget(
            subtitle
        )

        head.addLayout(
            titles
        )

        head.addStretch()

        # ----------------------------------------------------
        # Buttons
        # ----------------------------------------------------

        self.import_button = QPushButton(
            "📥  استيراد Excel"
        )

        self.import_button.setObjectName(
            "primary"
        )

        self.import_button.clicked.connect(
            self.import_excel
        )

        self.add_button = QPushButton(
            "＋  إضافة جهاز"
        )

        self.add_button.setObjectName(
            "primary"
        )

        self.add_button.clicked.connect(
            self.add_device
        )

        self.edit_button = QPushButton(
            "✎  تعديل"
        )

        self.edit_button.setObjectName(
            "secondary"
        )

        self.edit_button.clicked.connect(
            self.edit_device
        )

        self.archive_button = QPushButton(
            "🗄  أرشفة"
        )

        self.archive_button.setObjectName(
            "danger"
        )

        self.archive_button.clicked.connect(
            self.archive_device
        )

        self.clear_all_button = QPushButton(
            "🗑  مسح الكل"
        )

        self.clear_all_button.setObjectName(
            "danger"
        )

        self.clear_all_button.clicked.connect(
            self.clear_all_devices
        )

        head.addWidget(
            self.import_button
        )

        head.addWidget(
            self.add_button
        )

        head.addWidget(
            self.edit_button
        )

        head.addWidget(
            self.archive_button
        )

        head.addWidget(
            self.clear_all_button
        )

        root.addLayout(
            head
        )

        # ----------------------------------------------------
        # Search / Filters
        # ----------------------------------------------------

        search_card = QFrame()

        search_card.setObjectName(
            "card"
        )

        search_layout = QHBoxLayout(
            search_card
        )

        search_layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )

        search_layout.addWidget(
            QLabel("🔎")
        )

        self.search = QLineEdit()

        self.search.setObjectName(
            "search"
        )

        self.search.setPlaceholderText(
            "بحث برقم الجهاز أو المبنى أو المكان أو المستخدم أو IP أو Serial..."
        )

        self.search.textChanged.connect(
            self.load_devices
        )

        search_layout.addWidget(
            self.search,
            1,
        )

        self.building_filter = QComboBox()

        self.building_filter.setMinimumWidth(
            170
        )

        self.building_filter.addItem(
            "كل المباني",
            "",
        )

        self.building_filter.currentIndexChanged.connect(
            self.load_devices
        )

        search_layout.addWidget(
            self.building_filter
        )

        self.status_filter = QComboBox()

        self.status_filter.setMinimumWidth(
            150
        )

        self.status_filter.addItem(
            "كل الحالات",
            "",
        )

        self.status_filter.currentIndexChanged.connect(
            self.load_devices
        )

        search_layout.addWidget(
            self.status_filter
        )

        root.addWidget(
            search_card
        )

        # ----------------------------------------------------
        # Table
        # ----------------------------------------------------

        table_card = QFrame()

        table_card.setObjectName(
            "card"
        )

        table_layout = QVBoxLayout(
            table_card
        )

        table_layout.setContentsMargins(
            7,
            7,
            7,
            7,
        )

        self.table = QTableWidget()

        self.table.setColumnCount(
            22
        )

        self.table.setHorizontalHeaderLabels(
            [
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
            ]
        )

        self.table.setColumnHidden(
            0,
            True,
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SingleSelection
        )

        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.verticalHeader().setVisible(
            False
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        header.setStretchLastSection(
            True
        )

        self.table.doubleClicked.connect(
            self.edit_device
        )

        table_layout.addWidget(
            self.table
        )

        root.addWidget(
            table_card,
            1,
        )

    # ========================================================
    # Load Devices
    # ========================================================

    def load_devices(self):

        search = self.search.text().strip()

        selected_building = (
            self.building_filter.currentData()
            if hasattr(
                self,
                "building_filter",
            )
            else ""
        )

        selected_status = (
            self.status_filter.currentData()
            if hasattr(
                self,
                "status_filter",
            )
            else ""
        )

        con = get_connection()
        cur = con.cursor()

        try:

            # ------------------------------------------------
            # Buildings
            # ------------------------------------------------

            cur.execute(
                """
                SELECT id, name
                FROM buildings
                ORDER BY name
                """
            )

            buildings = cur.fetchall()

            current_building = (
                selected_building
            )

            self.building_filter.blockSignals(
                True
            )

            self.building_filter.clear()

            self.building_filter.addItem(
                "كل المباني",
                "",
            )

            for building in buildings:

                self.building_filter.addItem(
                    building["name"],
                    str(building["id"]),
                )

            index = (
                self.building_filter.findData(
                    current_building
                )
            )

            self.building_filter.setCurrentIndex(
                index if index >= 0 else 0
            )

            self.building_filter.blockSignals(
                False
            )

            # ------------------------------------------------
            # Statuses
            # ------------------------------------------------

            cur.execute(
                """
                SELECT DISTINCT status
                FROM devices
                WHERE is_archived = 0
                  AND status IS NOT NULL
                  AND TRIM(status) <> ''
                ORDER BY status
                """
            )

            statuses = cur.fetchall()

            current_status = (
                selected_status
            )

            self.status_filter.blockSignals(
                True
            )

            self.status_filter.clear()

            self.status_filter.addItem(
                "كل الحالات",
                "",
            )

            for status in statuses:

                self.status_filter.addItem(
                    str(status["status"]),
                    str(status["status"]),
                )

            index = (
                self.status_filter.findData(
                    current_status
                )
            )

            self.status_filter.setCurrentIndex(
                index if index >= 0 else 0
            )

            self.status_filter.blockSignals(
                False
            )

            # ------------------------------------------------
            # Devices Query
            # ------------------------------------------------

            query = """
                SELECT
                    devices.*,
                    buildings.name AS building_name
                FROM devices
                LEFT JOIN buildings
                    ON devices.building_id = buildings.id
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

                params.extend(
                    [key] * 7
                )

            if selected_building:

                query += """
                    AND devices.building_id = ?
                """

                params.append(
                    int(selected_building)
                )

            if selected_status:

                query += """
                    AND devices.status = ?
                """

                params.append(
                    selected_status
                )

            query += """
                ORDER BY devices.id ASC
            """

            cur.execute(
                query,
                params,
            )

            rows = cur.fetchall()

        finally:

            con.close()

        # ----------------------------------------------------
        # Fill Table
        # ----------------------------------------------------

        self.table.setRowCount(
            0
        )

        for device in rows:

            row = self.table.rowCount()

            self.table.insertRow(
                row
            )

            values = [
                device["id"],
                device["device_number"],
                device["building_name"] or "",
                device["location"],
                device["device_name"],
                device["user_name"],
                device["user_name_en"],
                device["lock_number"],
                device["network_connection"],
                device["motherboard"],
                device["graphics_card"],
                device["hard_disk"],
                device["hard_disk_serial"],
                device["processor"],
                device["ram"],
                device["monitor"],
                device["operating_system"],
                device["ms_office"],
                device["printer"],
                device["scanner"],
                device["ip_address"],
                device["status"],
            ]

            for column, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    clean(value)
                )

                item.setTextAlignment(
                    Qt.AlignCenter
                )

                self.table.setItem(
                    row,
                    column,
                    item,
                )

    # ========================================================
    # Selected Device
    # ========================================================

    def get_selected_device(self):

        selected = (
            self.table.selectedItems()
        )

        if not selected:

            QMessageBox.information(
                self,
                "تنبيه",
                "من فضلك اختر جهازاً أولاً.",
            )

            return None

        row = selected[0].row()

        device_id = (
            self.table.item(
                row,
                0,
            ).text()
        )

        con = get_connection()
        cur = con.cursor()

        try:

            cur.execute(
                """
                SELECT
                    devices.*,
                    buildings.name AS building_name
                FROM devices
                LEFT JOIN buildings
                    ON devices.building_id = buildings.id
                WHERE devices.id = ?
                """,
                (
                    device_id,
                ),
            )

            device = cur.fetchone()

        finally:

            con.close()

        return device

    # ========================================================
    # Building
    # ========================================================

    def get_building_id(
        self,
        building_name,
        con,
    ):

        name = clean(
            building_name
        )

        if not name:
            return None

        cur = con.cursor()

        cur.execute(
            """
            SELECT TOP 1 id
            FROM buildings
            WHERE name = ?
            """,
            (
                name,
            ),
        )

        row = cur.fetchone()

        if row:
            return row["id"]

        cur.execute(
            """
            INSERT INTO buildings (
                name,
                location,
                notes
            )
            VALUES (?, ?, ?)
            """,
            (
                name,
                "",
                "تم إنشاؤه تلقائياً من استيراد Excel",
            ),
        )

        cur.execute(
            """
            SELECT CAST(
                SCOPE_IDENTITY()
                AS INT
            ) AS id
            """
        )

        row = cur.fetchone()

        return row["id"] if row else None

    # ========================================================
    # Add Device
    # ========================================================

    def add_device(self):

        if not self.has_permission(
            "devices.add"
        ):

            QMessageBox.warning(
                self,
                "غير مسموح",
                "ليس لديك صلاحية إضافة الأجهزة.",
            )

            return

        dialog = DeviceDialog(
            self
        )

        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.data()

        con = get_connection()
        cur = con.cursor()

        try:

            building_id = (
                self.get_building_id(
                    data["building"],
                    con,
                )
            )

            cur.execute(
                """
                INSERT INTO devices (
                    device_number,
                    device_name,
                    user_name,
                    department,
                    device_type,
                    serial_number,
                    processor,
                    ram,
                    hard_disk,
                    monitor,
                    operating_system,
                    printer,
                    production_year,
                    status,
                    building_id,
                    location,
                    user_name_en,
                    lock_number,
                    network_connection,
                    motherboard,
                    graphics_card,
                    hard_disk_serial,
                    ms_office,
                    scanner,
                    ip_address
                )
                VALUES (
                    ?,?,?,?,?,?,?,?,?,?,
                    ?,?,?,?,?,?,?,?,?,?,
                    ?,?,?,?,?
                )
                """,
                (
                    data["device_number"],
                    data["device_name"],
                    data["user_name"],
                    "",
                    "",
                    "",
                    data["processor"],
                    data["ram"],
                    data["hard_disk"],
                    data["monitor"],
                    data["operating_system"],
                    data["printer"],
                    "",
                    data["status"],
                    building_id,
                    data["location"],
                    data["user_name_en"],
                    data["lock_number"],
                    data["network_connection"],
                    data["motherboard"],
                    data["graphics_card"],
                    data["hard_disk_serial"],
                    data["ms_office"],
                    data["scanner"],
                    data["ip_address"],
                ),
            )

            # الحصول على ID للجهاز الجديد
            new_device_id = None

            try:

                cur.execute(
                    """
                    SELECT CAST(
                        SCOPE_IDENTITY()
                        AS INT
                    ) AS id
                    """
                )

                identity_row = cur.fetchone()

                if identity_row:
                    new_device_id = identity_row["id"]

            except Exception:
                pass

            con.commit()

        except Exception as error:

            con.rollback()

            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء إضافة الجهاز:\n\n{error}",
            )

            return

        finally:

            con.close()

        # ----------------------------------------------------
        # Audit Log
        # ----------------------------------------------------

        audit_new_values = dict(
            data
        )

        audit_new_values[
            "building_id"
        ] = building_id

        write_audit_log(
            user=self.current_user,
            action="إضافة",
            module_name="الأجهزة",
            record_id=new_device_id,
            description=(
                f"تمت إضافة الجهاز: "
                f"{data['device_name']}"
            ),
            new_values=audit_new_values,
        )

        self.load_devices()

        QMessageBox.information(
            self,
            "تم",
            "تمت إضافة الجهاز بنجاح.",
        )

    # ========================================================
    # Edit Device
    # ========================================================

    def edit_device(self):

        if not self.has_permission(
            "devices.edit"
        ):

            QMessageBox.warning(
                self,
                "غير مسموح",
                "ليس لديك صلاحية تعديل الأجهزة.",
            )

            return

        device = self.get_selected_device()

        if not device:
            return

        old_values = device_audit_data(
            device
        )

        dialog = DeviceDialog(
            self,
            device,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.data()

        con = get_connection()
        cur = con.cursor()

        try:

            building_id = (
                self.get_building_id(
                    data["building"],
                    con,
                )
            )

            cur.execute(
                """
                UPDATE devices
                SET
                    device_number=?,
                    device_name=?,
                    user_name=?,
                    processor=?,
                    ram=?,
                    hard_disk=?,
                    monitor=?,
                    operating_system=?,
                    printer=?,
                    status=?,
                    building_id=?,
                    location=?,
                    user_name_en=?,
                    lock_number=?,
                    network_connection=?,
                    motherboard=?,
                    graphics_card=?,
                    hard_disk_serial=?,
                    ms_office=?,
                    scanner=?,
                    ip_address=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (
                    data["device_number"],
                    data["device_name"],
                    data["user_name"],
                    data["processor"],
                    data["ram"],
                    data["hard_disk"],
                    data["monitor"],
                    data["operating_system"],
                    data["printer"],
                    data["status"],
                    building_id,
                    data["location"],
                    data["user_name_en"],
                    data["lock_number"],
                    data["network_connection"],
                    data["motherboard"],
                    data["graphics_card"],
                    data["hard_disk_serial"],
                    data["ms_office"],
                    data["scanner"],
                    data["ip_address"],
                    device["id"],
                ),
            )

            con.commit()

        except Exception as error:

            con.rollback()

            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء تعديل الجهاز:\n\n{error}",
            )

            return

        finally:

            con.close()

        # ----------------------------------------------------
        # Audit Log
        # ----------------------------------------------------

        audit_new_values = dict(
            data
        )

        audit_new_values[
            "building_id"
        ] = building_id

        write_audit_log(
            user=self.current_user,
            action="تعديل",
            module_name="الأجهزة",
            record_id=device["id"],
            description=(
                f"تم تعديل بيانات الجهاز: "
                f"{data['device_name']}"
            ),
            old_values=old_values,
            new_values=audit_new_values,
        )

        self.load_devices()

        QMessageBox.information(
            self,
            "تم",
            "تم تعديل الجهاز بنجاح.",
        )

    # ========================================================
    # Delete All Devices
    # ========================================================

    def clear_all_devices(self):

        if not self.has_permission(
            "devices.delete"
        ):

            QMessageBox.warning(
                self,
                "غير مسموح",
                "ليس لديك صلاحية حذف الأجهزة.",
            )

            return

        answer = QMessageBox.question(
            self,
            "تأكيد مسح جميع الأجهزة",
            "⚠ هل أنت متأكد من مسح جميع الأجهزة نهائيًا؟\n\n"
            "سيتم حذف الأجهزة النشطة والمؤرشفة من قاعدة البيانات، "
            "ولا يمكن التراجع عن العملية.",
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        con = get_connection()
        cur = con.cursor()

        try:

            # حماية سجل الأعطال
            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM faults
                WHERE device_id IS NOT NULL
                """
            )

            fault_count = int(
                cur.fetchone()["total"] or 0
            )

            if fault_count > 0:

                con.close()

                QMessageBox.warning(
                    self,
                    "لا يمكن المسح",
                    "يوجد أعطال مرتبطة بأجهزة مسجلة.\n\n"
                    "لم يتم حذف أي جهاز حفاظًا على سجل الأعطال.\n"
                    "احذف/عالج سجلات الأعطال المرتبطة أولًا "
                    "ثم استخدم مسح الكل.",
                )

                return

            # معرفة العدد قبل الحذف
            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM devices
                """
            )

            total_before = int(
                cur.fetchone()["total"] or 0
            )

            cur.execute(
                "DELETE FROM devices"
            )

            deleted = cur.rowcount

            con.commit()

        except Exception as error:

            con.rollback()

            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء مسح الأجهزة:\n{error}",
            )

            return

        finally:

            con.close()

        # ----------------------------------------------------
        # Audit Log
        # ----------------------------------------------------

        write_audit_log(
            user=self.current_user,
            action="حذف",
            module_name="الأجهزة",
            description=(
                "تم مسح جميع الأجهزة نهائيًا "
                f"وعدد السجلات المحذوفة: {deleted}"
            ),
            old_values={
                "عدد الأجهزة قبل المسح": total_before,
                "عدد الأجهزة المحذوفة": deleted,
            },
        )

        QMessageBox.information(
            self,
            "تم",
            f"تم مسح جميع الأجهزة بنجاح.\n\n"
            f"عدد الأجهزة المحذوفة: {deleted}",
        )

        self.load_devices()

    # ========================================================
    # Archive Device
    # ========================================================

    def archive_device(self):

        if not self.has_permission(
            "devices.delete"
        ):

            QMessageBox.warning(
                self,
                "غير مسموح",
                "ليس لديك صلاحية حذف/أرشفة الأجهزة.",
            )

            return

        device = self.get_selected_device()

        if not device:
            return

        answer = QMessageBox.question(
            self,
            "تأكيد الأرشفة",
            f"هل تريد أرشفة الجهاز:\n\n"
            f"{device['device_name']}؟",
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        old_values = device_audit_data(
            device
        )

        con = get_connection()
        cur = con.cursor()

        try:

            cur.execute(
                """
                UPDATE devices
                SET
                    is_archived=1,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (
                    device["id"],
                ),
            )

            con.commit()

        except Exception as error:

            con.rollback()

            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء أرشفة الجهاز:\n\n{error}",
            )

            return

        finally:

            con.close()

        # ----------------------------------------------------
        # Audit Log
        # ----------------------------------------------------

        write_audit_log(
            user=self.current_user,
            action="أرشفة",
            module_name="الأجهزة",
            record_id=device["id"],
            description=(
                f"تمت أرشفة الجهاز: "
                f"{device['device_name']}"
            ),
            old_values=old_values,
            new_values={
                "is_archived": 1,
            },
        )

        self.load_devices()

        QMessageBox.information(
            self,
            "تم",
            "تمت أرشفة الجهاز بنجاح.",
        )

    # ========================================================
    # Import Excel
    # ========================================================

    def import_excel(self):

        if not self.has_permission(
            "devices.add"
        ):

            QMessageBox.warning(
                self,
                "غير مسموح",
                "ليس لديك صلاحية استيراد وإضافة الأجهزة.",
            )

            return

        try:

            from openpyxl import (
                load_workbook
            )

        except ImportError:

            QMessageBox.critical(
                self,
                "مكتبة ناقصة",
                "ثبت openpyxl أولاً:\n\n"
                "python -m pip install openpyxl",
            )

            return

        file_path, _ = (
            QFileDialog.getOpenFileName(
                self,
                "اختيار ملف Excel",
                "",
                "Excel (*.xlsx *.xlsm)",
            )
        )

        if not file_path:
            return

        file_name = os.path.basename(
            file_path
        )

        wb = None
        con = None
        progress = None

        try:

            wb = load_workbook(
                file_path,
                read_only=True,
                data_only=True,
            )

            ws = wb.active

            iterator = ws.iter_rows(
                values_only=True
            )

            header = next(
                iterator,
                None,
            )

            if not header:

                wb.close()
                wb = None

                QMessageBox.warning(
                    self,
                    "تنبيه",
                    "ملف Excel فارغ.",
                )

                return

            indexes = find_header_indexes(
                header
            )

            # ------------------------------------------------
            # Required Columns
            # ------------------------------------------------

            if (
                "اسم الجهاز" not in indexes
                or "المبنى" not in indexes
            ):

                wb.close()
                wb = None

                QMessageBox.warning(
                    self,
                    "خطأ في الملف",
                    "لم أستطع التعرف على أعمدة "
                    "المبنى واسم الجهاز.",
                )

                return

            def cell(
                row,
                name,
            ):

                index = indexes.get(
                    name
                )

                if (
                    index is None
                    or index >= len(row)
                ):

                    return ""

                return clean(
                    row[index]
                )

            imported_rows = []

            # ------------------------------------------------
            # Read Excel
            # ------------------------------------------------

            for row in iterator:

                if (
                    not row
                    or not any(
                        clean(value)
                        for value in row
                    )
                ):
                    continue

                device_name = cell(
                    row,
                    "اسم الجهاز",
                )

                if not device_name:
                    continue

                imported_rows.append(
                    {
                        "device_number": cell(
                            row,
                            "م",
                        ),
                        "building": cell(
                            row,
                            "المبنى",
                        ),
                        "location": cell(
                            row,
                            "مكان التواجد",
                        ),
                        "device_name": device_name,
                        "user_name": cell(
                            row,
                            "اسم المستخدم",
                        ),
                        "user_name_en": cell(
                            row,
                            "User name",
                        ),
                        "lock_number": cell(
                            row,
                            "رقم القفل",
                        ),
                        "network_connection": cell(
                            row,
                            "التوصيل بالشبكة",
                        ),
                        "motherboard": cell(
                            row,
                            "Mother Board",
                        ),
                        "graphics_card": cell(
                            row,
                            "كارت الشاشة الخارجى",
                        ),
                        "hard_disk": cell(
                            row,
                            "الهارد ديسك",
                        ),
                        "hard_disk_serial": cell(
                            row,
                            "الرقم التسلسلى للهارد",
                        ),
                        "processor": cell(
                            row,
                            "المعالج المركزى",
                        ),
                        "ram": cell(
                            row,
                            "-",
                        ),
                        "monitor": cell(
                            row,
                            "طراز الشاشة",
                        ),
                        "operating_system": cell(
                            row,
                            "نظام التشغيل",
                        ),
                        "ms_office": cell(
                            row,
                            "MS Office",
                        ),
                        "printer": cell(
                            row,
                            "طراز الطابعة",
                        ),
                        "scanner": cell(
                            row,
                            "الماسح الضوئى",
                        ),
                        "ip_address": cell(
                            row,
                            "IP",
                        ),
                        "status": (
                            cell(
                                row,
                                "الحالة الفنية",
                            )
                            or "صالح"
                        ),
                    }
                )

            wb.close()
            wb = None

            if not imported_rows:

                QMessageBox.warning(
                    self,
                    "تنبيه",
                    "لم يتم العثور على صفوف أجهزة.",
                )

                return

            # ------------------------------------------------
            # Preview
            # ------------------------------------------------

            preview = "\n".join(
                f"{index + 1}. "
                f"{data['device_number']} | "
                f"{data['device_name']} | "
                f"{data['building']} | "
                f"{data['status']}"
                for index, data
                in enumerate(
                    imported_rows[:12]
                )
            )

            more = ""

            if len(imported_rows) > 12:

                more = (
                    f"\n... و "
                    f"{len(imported_rows) - 12}"
                    f" جهاز آخر"
                )

            answer = QMessageBox.question(
                self,
                "تأكيد الاستيراد",
                f"تم العثور على "
                f"{len(imported_rows)} جهاز.\n\n"
                f"{preview}"
                f"{more}\n\n"
                "سيتم نقل كل الأعمدة الـ21 كما هي "
                "إلى النظام.\n"
                "المباني غير الموجودة سيتم إنشاؤها تلقائياً.\n"
                "إذا كان رقم الجهاز موجوداً سيتم تحديث نفس الجهاز.\n\n"
                "هل تريد بدء الاستيراد؟",
                QMessageBox.Yes
                | QMessageBox.No,
                QMessageBox.No,
            )

            if answer != QMessageBox.Yes:
                return

            # ------------------------------------------------
            # Progress
            # ------------------------------------------------

            progress = QProgressDialog(
                "جاري استيراد جميع بيانات الأجهزة...",
                "إلغاء",
                0,
                len(imported_rows),
                self,
            )

            progress.setWindowTitle(
                "استيراد Excel"
            )

            progress.setWindowModality(
                Qt.WindowModal
            )

            progress.setMinimumDuration(
                0
            )

            progress.show()

            con = get_connection()
            cur = con.cursor()

            new_count = 0
            update_count = 0
            cancel = False

            # ------------------------------------------------
            # Import Loop
            # ------------------------------------------------

            for number, data in enumerate(
                imported_rows,
                1,
            ):

                progress.setValue(
                    number
                )

                if progress.wasCanceled():

                    cancel = True

                    break

                building_id = (
                    self.get_building_id(
                        data["building"],
                        con,
                    )
                )

                existing = None

                # --------------------------------------------
                # Match by Device Number
                # --------------------------------------------

                if data["device_number"]:

                    cur.execute(
                        """
                        SELECT TOP 1 id
                        FROM devices
                        WHERE device_number=?
                          AND is_archived=0
                        """,
                        (
                            data[
                                "device_number"
                            ],
                        ),
                    )

                    existing = cur.fetchone()

                # --------------------------------------------
                # Match by Device Name
                # --------------------------------------------

                if not existing:

                    cur.execute(
                        """
                        SELECT TOP 1 id
                        FROM devices
                        WHERE device_name=?
                          AND is_archived=0
                        """,
                        (
                            data[
                                "device_name"
                            ],
                        ),
                    )

                    existing = cur.fetchone()

                values = (
                    data["device_number"],
                    data["device_name"],
                    data["user_name"],
                    "",
                    "",
                    "",
                    data["processor"],
                    data["ram"],
                    data["hard_disk"],
                    data["monitor"],
                    data["operating_system"],
                    data["printer"],
                    "",
                    data["status"],
                    building_id,
                    data["location"],
                    data["user_name_en"],
                    data["lock_number"],
                    data["network_connection"],
                    data["motherboard"],
                    data["graphics_card"],
                    data["hard_disk_serial"],
                    data["ms_office"],
                    data["scanner"],
                    data["ip_address"],
                )

                # --------------------------------------------
                # Update Existing
                # --------------------------------------------

                if existing:

                    cur.execute(
                        """
                        UPDATE devices
                        SET
                            device_number=?,
                            device_name=?,
                            user_name=?,
                            department=?,
                            device_type=?,
                            serial_number=?,
                            processor=?,
                            ram=?,
                            hard_disk=?,
                            monitor=?,
                            operating_system=?,
                            printer=?,
                            production_year=?,
                            status=?,
                            building_id=?,
                            location=?,
                            user_name_en=?,
                            lock_number=?,
                            network_connection=?,
                            motherboard=?,
                            graphics_card=?,
                            hard_disk_serial=?,
                            ms_office=?,
                            scanner=?,
                            ip_address=?,
                            updated_at=CURRENT_TIMESTAMP
                        WHERE id=?
                        """,
                        values
                        + (
                            existing["id"],
                        ),
                    )

                    update_count += 1

                # --------------------------------------------
                # Insert New
                # --------------------------------------------

                else:

                    cur.execute(
                        """
                        INSERT INTO devices (
                            device_number,
                            device_name,
                            user_name,
                            department,
                            device_type,
                            serial_number,
                            processor,
                            ram,
                            hard_disk,
                            monitor,
                            operating_system,
                            printer,
                            production_year,
                            status,
                            building_id,
                            location,
                            user_name_en,
                            lock_number,
                            network_connection,
                            motherboard,
                            graphics_card,
                            hard_disk_serial,
                            ms_office,
                            scanner,
                            ip_address
                        )
                        VALUES (
                            ?,?,?,?,?,?,?,?,?,?,
                            ?,?,?,?,?,?,?,?,?,?,
                            ?,?,?,?,?
                        )
                        """,
                        values,
                    )

                    new_count += 1

            # ------------------------------------------------
            # Save
            # ------------------------------------------------

            con.commit()

            con.close()
            con = None

            progress.close()
            progress = None

            self.load_devices()

            # ------------------------------------------------
            # Audit Log - Import
            # ------------------------------------------------

            write_audit_log(
                user=self.current_user,
                action="استيراد",
                module_name="الأجهزة",
                description=(
                    "تم استيراد ملف Excel للأجهزة"
                    f"\nالملف: {file_name}"
                    f"\nإجمالي الصفوف: "
                    f"{len(imported_rows)}"
                    f"\nأجهزة جديدة: "
                    f"{new_count}"
                    f"\nأجهزة محدثة: "
                    f"{update_count}"
                    f"\nتم الإلغاء: "
                    f"{'نعم' if cancel else 'لا'}"
                ),
                new_values={
                    "file": file_name,
                    "total_rows": len(
                        imported_rows
                    ),
                    "new_devices": new_count,
                    "updated_devices": update_count,
                    "cancelled": cancel,
                },
            )

            # ------------------------------------------------
            # Result
            # ------------------------------------------------

            if cancel:

                QMessageBox.information(
                    self,
                    "تم إيقاف الاستيراد",
                    "تم حفظ ما تم استيراده حتى لحظة الإلغاء.\n\n"
                    f"أجهزة جديدة: {new_count}\n"
                    f"أجهزة محدثة: {update_count}",
                )

            else:

                QMessageBox.information(
                    self,
                    "تم الاستيراد بالكامل",
                    "تم استيراد الملف بالكامل بدون حذف أعمدة.\n\n"
                    f"عدد الأجهزة الجديدة: {new_count}\n"
                    f"عدد الأجهزة المحدثة: {update_count}\n\n"
                    "تم حفظ كل بيانات Excel الـ21 "
                    "في قاعدة البيانات.",
                )

        except Exception as error:

            if wb is not None:

                try:
                    wb.close()
                except Exception:
                    pass

            if con is not None:

                try:
                    con.rollback()
                except Exception:
                    pass

                try:
                    con.close()
                except Exception:
                    pass

            if progress is not None:

                try:
                    progress.close()
                except Exception:
                    pass

            QMessageBox.critical(
                self,
                "خطأ في الاستيراد",
                "حدث خطأ أثناء الاستيراد:\n\n"
                + str(error),
            )