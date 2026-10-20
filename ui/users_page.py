from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDialogButtonBox,
    QHeaderView,
)

from PySide6.QtCore import Qt

from database import get_connection
from auth import hash_password


class UserDialog(QDialog):

    def __init__(
        self,
        parent=None,
        user_data=None,
        change_password=False,
    ):

        super().__init__(parent)

        self.user_data = user_data
        self.change_password = change_password

        if user_data is None:
            self.setWindowTitle("إضافة مستخدم")

        elif change_password:
            self.setWindowTitle("تغيير كلمة المرور")

        else:
            self.setWindowTitle("تعديل المستخدم")

        self.resize(450, 330)

        self.setLayoutDirection(Qt.RightToLeft)

        layout = QFormLayout(self)

        layout.setSpacing(12)

        # =================================================
        # Username
        # =================================================

        self.username = QLineEdit()

        self.username.setPlaceholderText("اسم المستخدم")

        if user_data:
            self.username.setText(str(user_data["username"]))

        if change_password:
            self.username.setReadOnly(True)

        layout.addRow("اسم المستخدم:", self.username)

        # =================================================
        # Full Name
        # =================================================

        self.full_name = QLineEdit()

        self.full_name.setPlaceholderText("الاسم الكامل")

        if user_data:
            self.full_name.setText(str(user_data["full_name"] or ""))

        if change_password:
            self.full_name.setVisible(False)

        layout.addRow("الاسم الكامل:", self.full_name)

        # =================================================
        # Display Title (اللقب / الرتبة)
        # =================================================

        self.display_title = QLineEdit()

        self.display_title.setPlaceholderText("اللقب أو الرتبة (مثل: عميد، بشمهندس، رقيب أول...)")

        if user_data:
            self.display_title.setText(str(user_data.get("display_title") or ""))

        if change_password:
            self.display_title.setVisible(False)

        layout.addRow("اللقب / الرتبة:", self.display_title)

        # =================================================
        # Role  (يتم تحميلها من جدول roles)
        # =================================================

        self.role = QComboBox()

        self.load_roles()

        if user_data and not change_password:

            role_id = user_data["role_id"]

            index = self.role.findData(role_id)

            if index >= 0:
                self.role.setCurrentIndex(index)

        if change_password:
            self.role.setVisible(False)

        layout.addRow("الدور:", self.role)

        # =================================================
        # Password
        # =================================================

        self.password = QLineEdit()

        self.password.setEchoMode(QLineEdit.Password)

        self.password.setPlaceholderText("كلمة المرور")

        layout.addRow("كلمة المرور:", self.password)

        # =================================================
        # Password Confirmation
        # =================================================

        self.password_confirm = QLineEdit()

        self.password_confirm.setEchoMode(QLineEdit.Password)

        self.password_confirm.setPlaceholderText("تأكيد كلمة المرور")

        layout.addRow("تأكيد كلمة المرور:", self.password_confirm)

        # =================================================
        # Buttons
        # =================================================

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.validate_and_accept)

        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    # =====================================================
    # Roles
    # =====================================================

    def load_roles(self):
        """
        تحميل الأدوار الفعالة من جدول roles.

        SUPER_ADMIN مستبعد لأنه دور أساسي محمي
        ولا يتم إنشاء مستخدمين به من هذه الشاشة.
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

            for row in cursor.fetchall():
                self.role.addItem(
                    row["role_name"],
                    int(row["id"]),
                )

        except Exception as e:

            QMessageBox.critical(
                self,
                "خطأ",
                f"تعذر تحميل الأدوار:\n{e}"
            )

        finally:

            if connection:
                try:
                    connection.close()
                except Exception:
                    pass

    # =====================================================
    # Validation
    # =====================================================

    def validate_and_accept(self):

        username = self.username.text().strip()

        password = self.password.text()

        confirm = self.password_confirm.text()

        if not self.change_password:

            if not username:
                QMessageBox.warning(
                    self,
                    "تنبيه",
                    "اكتب اسم المستخدم."
                )
                return

            if self.role.currentData() is None:
                QMessageBox.warning(
                    self,
                    "تنبيه",
                    "اختر الدور."
                )
                return

        if not self.user_data or self.change_password:

            if not password:
                QMessageBox.warning(
                    self,
                    "تنبيه",
                    "اكتب كلمة المرور."
                )
                return

            if len(password) < 6:
                QMessageBox.warning(
                    self,
                    "تنبيه",
                    "كلمة المرور يجب أن تكون 6 أحرف أو أكثر."
                )
                return

            if password != confirm:
                QMessageBox.warning(
                    self,
                    "تنبيه",
                    "تأكيد كلمة المرور غير مطابق."
                )
                return

        self.accept()


class UsersPage(QWidget):

    def __init__(
        self,
        current_user=None,
        parent=None,
    ):

        super().__init__(parent)

        self.current_user = current_user or {}

        self.setLayoutDirection(Qt.RightToLeft)

        self.build_ui()

        self.load_users()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 24, 24, 24)

        layout.setSpacing(15)

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        header = QHBoxLayout()

        title_box = QVBoxLayout()

        title = QLabel("إدارة المستخدمين")

        title.setStyleSheet(
            """
            font-size: 25px;
            font-weight: 800;
            color: #0f2338;
            """
        )

        subtitle = QLabel("إضافة وتعديل وتعطيل مستخدمي النظام")

        subtitle.setStyleSheet(
            """
            color: #718096;
            font-size: 12px;
            """
        )

        title_box.addWidget(title)

        title_box.addWidget(subtitle)

        header.addLayout(title_box)

        header.addStretch()

        self.btn_add = QPushButton("＋ إضافة مستخدم")

        self.btn_add.setMinimumHeight(42)

        self.btn_add.setStyleSheet(
            """
            QPushButton {
                background-color: #0891b2;
                color: white;
                border: none;
                border-radius: 9px;
                padding: 9px 18px;
                font-size: 13px;
                font-weight: 700;
            }

            QPushButton:hover {
                background-color: #0e7490;
            }

            QPushButton:pressed {
                background-color: #155e75;
            }
            """
        )

        self.btn_add.clicked.connect(self.add_user)

        header.addWidget(self.btn_add)

        layout.addLayout(header)

        # -------------------------------------------------
        # Action buttons
        # -------------------------------------------------

        actions = QHBoxLayout()

        self.btn_edit = QPushButton("✏ تعديل")

        self.btn_password = QPushButton("🔑 تغيير كلمة المرور")

        self.btn_toggle = QPushButton("⏸ تفعيل / تعطيل")

        self.btn_delete = QPushButton("🗑 حذف")

        for button in (
            self.btn_edit,
            self.btn_password,
            self.btn_toggle,
            self.btn_delete,
        ):

            button.setMinimumHeight(38)

            actions.addWidget(button)

        actions.addStretch()

        self.btn_edit.clicked.connect(self.edit_user)

        self.btn_password.clicked.connect(self.change_password)

        self.btn_toggle.clicked.connect(self.toggle_user)

        self.btn_delete.clicked.connect(self.delete_user)

        layout.addLayout(actions)

        # -------------------------------------------------
        # Table
        # -------------------------------------------------

        self.table = QTableWidget()

        self.table.setColumnCount(7)

        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "اسم المستخدم",
                "اللقب / الرتبة",
                "الاسم الكامل",
                "الدور",
                "الحالة",
                "آخر دخول",
            ]
        )

        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)

        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        header.setSectionResizeMode(3, QHeaderView.Stretch)

        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

        self.setStyleSheet(
            """
            QTableWidget {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                gridline-color: #f1f5f9;
                font-size: 12px;
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

            QPushButton {
                background-color: #f1f5f9;
                color: #0f2338;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                padding: 7px 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #e2e8f0;
            }
            """
        )

    # =====================================================
    # Database
    # =====================================================

    def load_users(self):

        try:

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    u.id,
                    u.username,
                    u.display_title,
                    u.full_name,
                    u.role_id,
                    r.role_code,
                    r.role_name,
                    u.is_active,
                    u.last_login
                FROM dbo.users u
                INNER JOIN dbo.roles r
                    ON r.id = u.role_id
                ORDER BY u.id
                """
            )

            rows = cursor.fetchall()

            connection.close()

            self.table.setRowCount(len(rows))

            for row_index, row in enumerate(rows):

                values = [
                    row["id"],
                    row["username"],
                    row["display_title"] or "",
                    row["full_name"] or "",
                    row["role_name"],
                    "نشط" if row["is_active"] else "غير نشط",
                    row["last_login"] or "",
                ]

                for column, value in enumerate(values):

                    item = QTableWidgetItem(str(value))

                    item.setTextAlignment(Qt.AlignCenter)

                    self.table.setItem(
                        row_index,
                        column,
                        item
                    )

        except Exception as e:

            QMessageBox.critical(
                self,
                "خطأ",
                f"تعذر تحميل المستخدمين:\n{e}"
            )

    # =====================================================
    # Selected User
    # =====================================================

    def get_selected_user_id(self):

        row = self.table.currentRow()

        if row < 0:
            QMessageBox.warning(
                self,
                "تنبيه",
                "اختر مستخدمًا أولاً."
            )
            return None

        item = self.table.item(row, 0)

        if not item:
            return None

        return int(item.text())

    def get_selected_user(self):

        user_id = self.get_selected_user_id()

        if user_id is None:
            return None

        try:

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    u.id,
                    u.username,
                    u.display_title,
                    u.full_name,
                    u.role_id,
                    u.is_active,
                    r.role_code,
                    r.role_name
                FROM dbo.users u
                INNER JOIN dbo.roles r
                    ON r.id = u.role_id
                WHERE u.id = ?
                """,
                (user_id,)
            )

            row = cursor.fetchone()

            connection.close()

            return row

        except Exception as e:

            QMessageBox.critical(
                self,
                "خطأ",
                f"تعذر قراءة المستخدم:\n{e}"
            )

            return None

    # =====================================================
    # Add
    # =====================================================

    def add_user(self):

        dialog = UserDialog(self)

        if dialog.exec() != QDialog.Accepted:
            return

        username = dialog.username.text().strip()

        full_name = dialog.full_name.text().strip()

        display_title = dialog.display_title.text().strip() or None

        password = dialog.password.text()

        role_id = dialog.role.currentData()

        password_hash = hash_password(password)

        try:

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM dbo.users
                WHERE username = ?
                """,
                (username,)
            )

            if cursor.fetchone()[0] > 0:

                connection.close()

                QMessageBox.warning(
                    self,
                    "تنبيه",
                    "اسم المستخدم موجود بالفعل."
                )

                return

            cursor.execute(
                """
                INSERT INTO dbo.users
                (
                    username,
                    password_hash,
                    full_name,
                    display_title,
                    role_id,
                    is_active
                )
                VALUES
                (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    1
                )
                """,
                (
                    username,
                    password_hash,
                    full_name,
                    display_title,
                    role_id,
                )
            )

            connection.commit()

            connection.close()

            self.load_users()

            QMessageBox.information(
                self,
                "تم",
                "تم إنشاء المستخدم بنجاح."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "خطأ",
                f"تعذر إنشاء المستخدم:\n{e}"
            )

    # =====================================================
    # Edit
    # =====================================================

    def edit_user(self):

        user = self.get_selected_user()

        if user is None:
            return

        if user["role_code"] == "SUPER_ADMIN":

            QMessageBox.information(
                self,
                "تنبيه",
                "المستخدم SUPER ADMIN الأساسي محمي من التعديل من هذه الشاشة."
            )

            return

        dialog = UserDialog(
            self,
            user_data=user
        )

        if dialog.exec() != QDialog.Accepted:
            return

        username = dialog.username.text().strip()

        full_name = dialog.full_name.text().strip()

        display_title = dialog.display_title.text().strip() or None

        role_id = dialog.role.currentData()

        try:

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM dbo.users
                WHERE username = ?
                  AND id <> ?
                """,
                (
                    username,
                    user["id"],
                )
            )

            if cursor.fetchone()[0] > 0:

                connection.close()

                QMessageBox.warning(
                    self,
                    "تنبيه",
                    "اسم المستخدم مستخدم بالفعل."
                )

                return

            cursor.execute(
                """
                UPDATE dbo.users
                SET
                    username = ?,
                    full_name = ?,
                    display_title = ?,
                    role_id = ?
                WHERE id = ?
                """,
                (
                    username,
                    full_name,
                    display_title,
                    role_id,
                    user["id"],
                )
            )

            connection.commit()

            connection.close()

            self.load_users()

            QMessageBox.information(
                self,
                "تم",
                "تم تعديل المستخدم بنجاح."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "خطأ",
                f"تعذر تعديل المستخدم:\n{e}"
            )

    # =====================================================
    # Change Password
    # =====================================================

    def change_password(self):

        user = self.get_selected_user()

        if user is None:
            return

        dialog = UserDialog(
            self,
            user_data=user,
            change_password=True
        )

        if dialog.exec() != QDialog.Accepted:
            return

        password_hash = hash_password(dialog.password.text())

        try:

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE dbo.users
                SET password_hash = ?
                WHERE id = ?
                """,
                (
                    password_hash,
                    user["id"],
                )
            )

            connection.commit()

            connection.close()

            QMessageBox.information(
                self,
                "تم",
                "تم تغيير كلمة المرور بنجاح."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "خطأ",
                f"تعذر تغيير كلمة المرور:\n{e}"
            )

    # =====================================================
    # Activate / Deactivate
    # =====================================================

    def toggle_user(self):

        user = self.get_selected_user()

        if user is None:
            return

        if user["role_code"] == "SUPER_ADMIN":

            QMessageBox.warning(
                self,
                "ممنوع",
                "لا يمكن تعطيل SUPER ADMIN الأساسي."
            )

            return

        new_status = not bool(user["is_active"])

        action = "تفعيل" if new_status else "تعطيل"

        answer = QMessageBox.question(
            self,
            "تأكيد",
            f"هل تريد {action} المستخدم:\n"
            f"{user['username']} ؟",
            QMessageBox.Yes | QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE dbo.users
                SET is_active = ?
                WHERE id = ?
                """,
                (
                    1 if new_status else 0,
                    user["id"],
                )
            )

            connection.commit()

            connection.close()

            self.load_users()

        except Exception as e:

            QMessageBox.critical(
                self,
                "خطأ",
                f"تعذر تغيير حالة المستخدم:\n{e}"
            )

    # =====================================================
    # Delete
    # =====================================================

    def delete_user(self):

        user = self.get_selected_user()

        if user is None:
            return

        if user["role_code"] == "SUPER_ADMIN":

            QMessageBox.warning(
                self,
                "ممنوع",
                "لا يمكن حذف SUPER ADMIN الأساسي."
            )

            return

        answer = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف المستخدم:\n"
            f"{user['username']} ؟",
            QMessageBox.Yes | QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM dbo.user_permissions
                WHERE user_id = ?
                """,
                (user["id"],)
            )

            cursor.execute(
                """
                DELETE FROM dbo.users
                WHERE id = ?
                """,
                (user["id"],)
            )

            connection.commit()

            connection.close()

            self.load_users()

            QMessageBox.information(
                self,
                "تم",
                "تم حذف المستخدم."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "خطأ",
                f"تعذر حذف المستخدم:\n{e}"
            )