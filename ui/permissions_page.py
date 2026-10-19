from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QCheckBox,
)
from PySide6.QtCore import Qt

from database import get_connection


class PermissionsPage(QWidget):

    PERMISSION_GROUPS = {
        "الرئيسية": [
            ("dashboard.view", "عرض الرئيسية"),
        ],

        "الأجهزة": [
            ("devices.view", "عرض الأجهزة"),
            ("devices.add", "إضافة جهاز"),
            ("devices.edit", "تعديل جهاز"),
            ("devices.delete", "حذف جهاز"),
        ],

        "الأعطال": [
            ("faults.view", "عرض الأعطال"),
            ("faults.add", "إضافة عطل"),
            ("faults.edit", "تعديل عطل"),
            ("faults.delete", "حذف عطل"),
        ],

        "قطع الغيار": [
            ("spare_parts.view", "عرض قطع الغيار"),
            ("spare_parts.add", "إضافة صنف"),
            ("spare_parts.edit", "تعديل صنف"),
            ("spare_parts.delete", "حذف صنف"),
            ("spare_parts.movements", "حركات قطع الغيار"),
        ],

        "التقارير": [
            ("reports.view", "عرض التقارير"),
        ],

        "المستخدمون": [
            ("users.view", "عرض المستخدمين"),
            ("users.add", "إضافة مستخدم"),
            ("users.edit", "تعديل مستخدم"),
            ("users.delete", "حذف مستخدم"),
            ("users.permissions", "إدارة الصلاحيات"),
        ],

        "الأجهزة المصرح بها": [
            ("authorized_devices.view", "عرض الأجهزة المصرح بها"),
            ("authorized_devices.add", "إضافة جهاز مصرح"),
            ("authorized_devices.edit", "تعديل جهاز مصرح"),
            ("authorized_devices.delete", "حذف جهاز مصرح"),
        ],

        "السجل والنظام": [
            ("logs.view", "عرض سجل العمليات"),
            ("system.login", "تسجيل الدخول"),
            ("system.logout", "تسجيل الخروج"),
        ],

        "الأحبار": [
            ("ink.view", "عرض الأحبار"),
            ("ink.add", "إضافة سجل أحبار"),
            ("ink.edit", "تعديل سجل أحبار"),
            ("ink.delete", "حذف سجل أحبار"),
            ("ink.org_structure.manage", "إدارة الهيكل التنظيمي"),
        ],

        "الكاميرات": [
            ("cameras.view", "عرض الكاميرات"),
            ("cameras.add", "إضافة كاميرا"),
            ("cameras.edit", "تعديل كاميرا"),
            ("cameras.archive", "حذف / أرشفة كاميرا"),
        ],

        "أعطال الكاميرات": [
            ("camera_faults.view", "عرض أعطال الكاميرات"),
            ("camera_faults.add", "إضافة بلاغ عطل كاميرا"),
            ("camera_faults.edit", "تعديل بلاغ عطل كاميرا"),
            ("camera_faults.close", "إغلاق بلاغ عطل كاميرا"),
            ("camera_reports.export", "تصدير تقارير الكاميرات"),
        ],
    }

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)

        self.current_user = current_user or {}
        self.checkboxes = {}

        self.setLayoutDirection(Qt.RightToLeft)

        self.build_ui()
        self.load_roles()

    # =========================================================
    # UI
    # =========================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)

        # -----------------------------------------------------
        # Title
        # -----------------------------------------------------

        title = QLabel("إدارة الصلاحيات")

        title.setStyleSheet(
            """
            font-size: 25px;
            font-weight: 800;
            color: #0f2338;
            """
        )

        layout.addWidget(title)

        # -----------------------------------------------------
        # Subtitle
        # -----------------------------------------------------

        subtitle = QLabel(
            "تحكم في الصلاحيات الممنوحة لكل دور — "
            "هذه الشاشة متاحة للـ SUPER ADMIN فقط."
        )

        subtitle.setStyleSheet(
            """
            color: #64748b;
            font-size: 12px;
            """
        )

        layout.addWidget(subtitle)

        # -----------------------------------------------------
        # Role row
        # -----------------------------------------------------

        role_row = QHBoxLayout()

        role_label = QLabel("اختيار الدور:")

        role_label.setStyleSheet(
            """
            font-weight: 700;
            color: #0f2338;
            """
        )

        # الأدوار يتم تحميلها من جدول roles داخل load_roles()
        self.role_combo = QComboBox()

        self.role_combo.setMinimumHeight(40)

        self.role_combo.currentIndexChanged.connect(
            self.load_permissions
        )

        role_row.addWidget(role_label)
        role_row.addWidget(self.role_combo)

        role_row.addStretch()

        # -----------------------------------------------------
        # Buttons
        # -----------------------------------------------------

        self.btn_all = QPushButton("✓ تحديد الكل")

        self.btn_none = QPushButton("✕ إلغاء الكل")

        self.btn_save = QPushButton("💾 حفظ الصلاحيات")

        self.btn_save.setObjectName("primaryButton")

        self.btn_all.clicked.connect(self.select_all)

        self.btn_none.clicked.connect(self.select_none)

        self.btn_save.clicked.connect(self.save_permissions)

        role_row.addWidget(self.btn_all)

        role_row.addWidget(self.btn_none)

        role_row.addWidget(self.btn_save)

        layout.addLayout(role_row)

        # -----------------------------------------------------
        # Permissions table
        # -----------------------------------------------------

        self.table = QTableWidget()

        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels(
            [
                "القسم",
                "الصلاحية",
                "مسموح",
            ]
        )

        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.table.verticalHeader().setVisible(False)

        self.table.setAlternatingRowColors(True)

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)

        header.setSectionResizeMode(1, QHeaderView.Stretch)

        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

        # -----------------------------------------------------
        # Style
        # -----------------------------------------------------

        self.setStyleSheet(
            """
            QTableWidget {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                gridline-color: #f1f5f9;
                font-size: 12px;
                alternate-background-color: #f8fafc;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QTableWidget::item:selected {
                background-color: #e0f2fe;
                color: #0f2338;
            }

            QHeaderView::section {
                background-color: #f8fafc;
                color: #0f2338;
                padding: 9px;
                border: none;
                border-bottom: 2px solid #0891b2;
                font-weight: 700;
            }

            QCheckBox {
                spacing: 6px;
            }

            QPushButton {
                background-color: #f1f5f9;
                color: #0f2338;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #e2e8f0;
            }

            QPushButton#primaryButton {
                background-color: #0891b2;
                color: white;
                border: none;
                font-weight: 700;
            }

            QPushButton#primaryButton:hover {
                background-color: #0e7490;
            }

            QPushButton#primaryButton:pressed {
                background-color: #155e75;
            }
            """
        )

    # =========================================================
    # Roles
    # =========================================================

    def load_roles(self):
        """
        تحميل الأدوار الفعالة من جدول roles.

        SUPER_ADMIN مستبعد لأنه يحصل على كل الصلاحيات
        تلقائيًا (راجع get_user_permissions في auth.py).
        """

        connection = None

        try:

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id, role_name
                FROM dbo.roles
                WHERE is_active = 1
                  AND UPPER(role_code) <> 'SUPER_ADMIN'
                ORDER BY id
                """
            )

            rows = cursor.fetchall()

            # منع تنفيذ load_permissions مع كل عنصر يتم إضافته
            self.role_combo.blockSignals(True)

            self.role_combo.clear()

            for row in rows:
                self.role_combo.addItem(
                    row["role_name"],
                    int(row["id"]),
                )

            self.role_combo.blockSignals(False)

        except Exception as e:

            self.role_combo.blockSignals(False)

            QMessageBox.critical(
                self,
                "خطأ",
                f"تعذر تحميل الأدوار:\n{e}"
            )

            return

        finally:

            if connection:

                try:
                    connection.close()
                except Exception:
                    pass

        if self.role_combo.count() > 0:

            self.role_combo.setCurrentIndex(0)

            self.load_permissions()

    # =========================================================
    # Load permissions
    # =========================================================

    def load_permissions(self):

        role_id = self.role_combo.currentData()

        if role_id is None:
            return

        self.table.setRowCount(0)

        self.checkboxes.clear()

        connection = None

        try:

            connection = get_connection()

            cursor = connection.cursor()

            # -------------------------------------------------
            # Get current role permissions
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT
                    permission_id,
                    allowed
                FROM dbo.role_permissions
                WHERE role_id = ?
                """,
                (role_id,)
            )

            rows = cursor.fetchall()

            allowed_map = {
                int(row["permission_id"]): bool(row["allowed"])
                for row in rows
            }

            # -------------------------------------------------
            # Get all active permissions
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT
                    id,
                    permission_code
                FROM dbo.permissions
                WHERE is_active = 1
                ORDER BY id
                """
            )

            permission_rows = cursor.fetchall()

            permission_map = {
                row["permission_code"]: int(row["id"])
                for row in permission_rows
            }

            # -------------------------------------------------
            # Build table
            # -------------------------------------------------

            row_index = 0

            for group_name, items in self.PERMISSION_GROUPS.items():

                for permission_code, permission_name in items:

                    permission_id = permission_map.get(permission_code)

                    if permission_id is None:
                        continue

                    self.table.insertRow(row_index)

                    # Group
                    self.table.setItem(
                        row_index,
                        0,
                        QTableWidgetItem(group_name)
                    )

                    # Permission name
                    self.table.setItem(
                        row_index,
                        1,
                        QTableWidgetItem(permission_name)
                    )

                    # Checkbox
                    check = QCheckBox()

                    check.setChecked(
                        allowed_map.get(permission_id, False)
                    )

                    check.setCursor(Qt.PointingHandCursor)

                    container = QWidget()

                    box = QHBoxLayout(container)

                    box.setContentsMargins(0, 0, 0, 0)

                    box.setAlignment(Qt.AlignCenter)

                    box.addWidget(check)

                    self.table.setCellWidget(
                        row_index,
                        2,
                        container
                    )

                    self.checkboxes[permission_id] = check

                    row_index += 1

        except Exception as e:

            QMessageBox.critical(
                self,
                "خطأ",
                f"تعذر تحميل الصلاحيات:\n{e}"
            )

        finally:

            if connection:

                try:
                    connection.close()
                except Exception:
                    pass

    # =========================================================
    # Select all
    # =========================================================

    def select_all(self):

        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)

    # =========================================================
    # Select none
    # =========================================================

    def select_none(self):

        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)

    # =========================================================
    # Save permissions
    # =========================================================

    def save_permissions(self):

        role_id = self.role_combo.currentData()

        if role_id is None:
            return

        role_name = self.role_combo.currentText()

        answer = QMessageBox.question(
            self,
            "تأكيد",
            f"هل تريد حفظ صلاحيات الدور {role_name}؟",
            QMessageBox.Yes | QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        connection = None

        try:

            connection = get_connection()

            cursor = connection.cursor()

            # -------------------------------------------------
            # لو سجل الصلاحية موجود  -> UPDATE
            # لو غير موجود          -> INSERT
            # -------------------------------------------------

            for permission_id, checkbox in self.checkboxes.items():

                allowed = 1 if checkbox.isChecked() else 0

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM dbo.role_permissions
                    WHERE role_id = ?
                      AND permission_id = ?
                    """,
                    (
                        role_id,
                        permission_id,
                    )
                )

                result = cursor.fetchone()

                exists = result[0] > 0

                if exists:

                    cursor.execute(
                        """
                        UPDATE dbo.role_permissions
                        SET allowed = ?
                        WHERE role_id = ?
                          AND permission_id = ?
                        """,
                        (
                            allowed,
                            role_id,
                            permission_id,
                        )
                    )

                else:

                    cursor.execute(
                        """
                        INSERT INTO dbo.role_permissions
                        (
                            role_id,
                            permission_id,
                            allowed
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            role_id,
                            permission_id,
                            allowed,
                        )
                    )

            connection.commit()

            QMessageBox.information(
                self,
                "تم الحفظ",
                f"تم حفظ صلاحيات الدور "
                f"{role_name} بنجاح.\n\n"
                "سيتم تطبيق التغييرات عند تسجيل الدخول "
                "مرة أخرى بالحساب."
            )

            # Reload UI from database
            self.load_permissions()

        except Exception as e:

            if connection:

                try:
                    connection.rollback()
                except Exception:
                    pass

            QMessageBox.critical(
                self,
                "خطأ",
                f"تعذر حفظ الصلاحيات:\n{e}"
            )

        finally:

            if connection:

                try:
                    connection.close()
                except Exception:
                    pass