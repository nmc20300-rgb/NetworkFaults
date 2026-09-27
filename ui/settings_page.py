import os
import shutil
import sqlite3
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QFileDialog, QFrame, QComboBox, QCheckBox,
    QSpinBox, QScrollArea, QStackedWidget, QSizePolicy
)

from database import get_connection


class StatCard(QFrame):
    def __init__(self, title, value="0", icon="●"):
        super().__init__()
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        top = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setObjectName("cardIcon")
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        top.addWidget(icon_label)
        top.addWidget(title_label, 1)
        layout.addLayout(top)

        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("cardValue")
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


class SettingsPage(QWidget):
    settings_changed = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("settingsPage")
        self.database_path = self.get_database_path()
        self.setup_database()
        self.setup_ui()
        self.load_settings()
        self.refresh_summary()

    def get_database_path(self):
        try:
            con = get_connection()
            row = con.execute("PRAGMA database_list").fetchone()
            con.close()
            if row:
                path = row[2] if len(row) >= 3 else row["file"]
                if path:
                    return os.path.abspath(path)
        except Exception:
            pass

        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "data", "network_faults.db")

    def setup_database(self):
        con = sqlite3.connect(self.database_path)
        con.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        con.commit()
        con.close()

    def get_setting(self, key, default=""):
        con = sqlite3.connect(self.database_path)
        row = con.execute(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        ).fetchone()
        con.close()
        return row[0] if row else default

    def set_setting(self, key, value):
        con = sqlite3.connect(self.database_path)
        con.execute("""
            INSERT INTO app_settings(key, value)
            VALUES(?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, str(value)))
        con.commit()
        con.close()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(16)

        # Header بنفس روح صفحات الأجهزة والأعطال
        header = QFrame()
        header.setObjectName("headerCard")
        h = QHBoxLayout(header)
        h.setContentsMargins(22, 18, 22, 18)

        title_box = QVBoxLayout()
        title = QLabel("⚙  إعدادات النظام")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "إدارة تشغيل النظام، المظهر، التنبيهات، البيانات والنسخ الاحتياطي"
        )
        subtitle.setObjectName("pageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        h.addLayout(title_box, 1)

        self.status_label = QLabel("● النظام يعمل")
        self.status_label.setObjectName("statusBadge")
        self.status_label.setAlignment(Qt.AlignCenter)
        h.addWidget(self.status_label)

        root.addWidget(header)

        # ملخص النظام
        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.devices_card = StatCard("الأجهزة المسجلة", 0, "🖥")
        self.faults_card = StatCard("إجمالي الأعطال", 0, "🔧")
        self.open_faults_card = StatCard("أعطال مفتوحة", 0, "⚠")
        self.parts_card = StatCard("قطع الغيار", 0, "🔩")
        for card in (
            self.devices_card, self.faults_card,
            self.open_faults_card, self.parts_card
        ):
            stats.addWidget(card)
        root.addLayout(stats)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(2, 2, 8, 20)
        content_layout.setSpacing(14)

        # إعدادات التشغيل
        general = self.create_card()
        gl = QVBoxLayout(general)
        gl.setContentsMargins(20, 18, 20, 18)
        gl.setSpacing(12)
        gl.addWidget(self.section_title("🛠", "إعدادات التشغيل"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(10)

        self.program_name = QLineEdit()
        self.program_name.setPlaceholderText("اسم النظام")

        self.refresh_seconds = QSpinBox()
        self.refresh_seconds.setRange(1, 60)
        self.refresh_seconds.setSuffix(" ثانية")

        self.items_per_page = QSpinBox()
        self.items_per_page.setRange(10, 500)
        self.items_per_page.setSingleStep(10)

        self.confirm_delete = QCheckBox("طلب تأكيد قبل الحذف")
        self.auto_refresh = QCheckBox("تحديث البيانات تلقائيًا")

        grid.addWidget(QLabel("اسم النظام"), 0, 0)
        grid.addWidget(self.program_name, 0, 1)
        grid.addWidget(QLabel("سرعة تحديث الرئيسية"), 1, 0)
        grid.addWidget(self.refresh_seconds, 1, 1)
        grid.addWidget(QLabel("عدد السجلات في الصفحة"), 2, 0)
        grid.addWidget(self.items_per_page, 2, 1)
        grid.addWidget(self.confirm_delete, 3, 0, 1, 2)
        grid.addWidget(self.auto_refresh, 4, 0, 1, 2)

        gl.addLayout(grid)

        save_general = QPushButton("💾 حفظ إعدادات التشغيل")
        save_general.setObjectName("primaryButton")
        save_general.clicked.connect(self.save_general)
        gl.addWidget(save_general, alignment=Qt.AlignLeft)
        content_layout.addWidget(general)

        # المظهر
        appearance = self.create_card()
        al = QVBoxLayout(appearance)
        al.setContentsMargins(20, 18, 20, 18)
        al.setSpacing(12)
        al.addWidget(self.section_title("🎨", "المظهر والواجهة"))

        ag = QGridLayout()
        ag.setHorizontalSpacing(18)
        ag.setVerticalSpacing(10)

        self.theme = QComboBox()
        self.theme.addItems(["فاتح", "داكن", "حسب النظام"])

        self.font_size = QComboBox()
        self.font_size.addItems(["صغير", "متوسط", "كبير"])

        self.rtl = QCheckBox("استخدام اتجاه عربي RTL")
        self.rtl.setChecked(True)

        ag.addWidget(QLabel("نمط الواجهة"), 0, 0)
        ag.addWidget(self.theme, 0, 1)
        ag.addWidget(QLabel("حجم الخط"), 1, 0)
        ag.addWidget(self.font_size, 1, 1)
        ag.addWidget(self.rtl, 2, 0, 1, 2)

        al.addLayout(ag)

        save_appearance = QPushButton("🎨 تطبيق المظهر")
        save_appearance.setObjectName("primaryButton")
        save_appearance.clicked.connect(self.save_appearance)
        al.addWidget(save_appearance, alignment=Qt.AlignLeft)
        content_layout.addWidget(appearance)

        # التنبيهات
        alerts = self.create_card()
        tl = QVBoxLayout(alerts)
        tl.setContentsMargins(20, 18, 20, 18)
        tl.setSpacing(8)
        tl.addWidget(self.section_title("🔔", "التنبيهات والمتابعة"))

        self.notify_open_faults = QCheckBox("إظهار تنبيه عند وجود أعطال مفتوحة")
        self.notify_parts = QCheckBox("إظهار تنبيه عند نقص قطع الغيار")
        self.notify_minimum = QCheckBox("إظهار تنبيه عند بلوغ الحد الأدنى للمخزون")

        tl.addWidget(self.notify_open_faults)
        tl.addWidget(self.notify_parts)
        tl.addWidget(self.notify_minimum)

        save_alerts = QPushButton("💾 حفظ إعدادات التنبيهات")
        save_alerts.clicked.connect(self.save_alerts)
        tl.addWidget(save_alerts, alignment=Qt.AlignLeft)
        content_layout.addWidget(alerts)

        # البيانات
        data_card = self.create_card()
        dl = QVBoxLayout(data_card)
        dl.setContentsMargins(20, 18, 20, 18)
        dl.setSpacing(12)
        dl.addWidget(self.section_title("🗄", "إدارة البيانات"))

        self.db_path = QLabel(self.database_path)
        self.db_path.setObjectName("pathLabel")
        self.db_path.setWordWrap(True)
        dl.addWidget(QLabel("قاعدة البيانات الحالية:"))
        dl.addWidget(self.db_path)

        row = QHBoxLayout()
        backup = QPushButton("📦 نسخة احتياطية")
        restore = QPushButton("♻ استعادة نسخة")
        open_folder = QPushButton("📁 مجلد البيانات")
        backup.clicked.connect(self.create_backup)
        restore.clicked.connect(self.restore_backup)
        open_folder.clicked.connect(self.open_database_folder)
        row.addWidget(backup)
        row.addWidget(restore)
        row.addWidget(open_folder)
        row.addStretch()
        dl.addLayout(row)

        self.auto_backup = QCheckBox("إنشاء نسخة احتياطية تلقائية عند تشغيل النظام")
        dl.addWidget(self.auto_backup)
        content_layout.addWidget(data_card)

        # معلومات النظام
        about = self.create_card()
        bl = QVBoxLayout(about)
        bl.setContentsMargins(20, 18, 20, 18)
        bl.setSpacing(8)
        bl.addWidget(self.section_title("ℹ", "حالة النظام"))

        self.system_info = QLabel()
        self.system_info.setObjectName("systemInfo")
        self.system_info.setWordWrap(True)
        bl.addWidget(self.system_info)

        refresh_btn = QPushButton("🔄 تحديث بيانات الصفحة")
        refresh_btn.clicked.connect(self.refresh_summary)
        bl.addWidget(refresh_btn, alignment=Qt.AlignLeft)
        content_layout.addWidget(about)

        content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

        self.setStyleSheet("""
            #settingsPage { background:#f4f7fb; }

            #headerCard, #statCard, #card {
                background:white;
                border:1px solid #e2e8f0;
                border-radius:14px;
            }

            #pageTitle {
                color:#0f2338;
                font-size:26px;
                font-weight:800;
            }

            #pageSubtitle {
                color:#64748b;
                font-size:12px;
                padding-top:3px;
            }

            #statusBadge {
                background:#ecfdf5;
                color:#065f46;
                border:1px solid #a7f3d0;
                border-radius:9px;
                padding:8px 14px;
                font-weight:700;
            }

            #cardIcon {
                font-size:22px;
            }

            #cardTitle {
                color:#64748b;
                font-size:12px;
                font-weight:700;
            }

            #cardValue {
                color:#0f2338;
                font-size:25px;
                font-weight:800;
            }

            #sectionTitle {
                color:#0f2338;
                font-size:18px;
                font-weight:800;
                padding-bottom:4px;
            }

            QLineEdit, QComboBox, QSpinBox {
                min-height:38px;
                border:1px solid #cbd5e1;
                border-radius:8px;
                padding:0 10px;
                background:#fbfdff;
            }

            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border:1.5px solid #0891b2;
                background:white;
            }

            QCheckBox {
                min-height:32px;
                color:#334155;
                font-size:13px;
            }

            QPushButton {
                min-height:40px;
                padding:0 16px;
                border:1px solid #cbd5e1;
                border-radius:8px;
                background:#f1f5f9;
                color:#0f2338;
                font-weight:700;
            }

            QPushButton:hover { background:#e2e8f0; }

            #primaryButton {
                background:#0891b2;
                color:white;
                border:none;
            }

            #primaryButton:hover { background:#0e7490; }
            #primaryButton:pressed { background:#155e75; }

            #pathLabel, #systemInfo {
                background:#f8fafc;
                border:1px solid #e2e8f0;
                border-radius:8px;
                padding:10px;
                color:#475569;
            }

            QScrollBar:vertical {
                width:8px;
                background:transparent;
            }

            QScrollBar::handle:vertical {
                background:#cbd5e1;
                border-radius:4px;
            }
            QScrollBar::handle:vertical:hover {
                background:#0891b2;
            }
        """)

    def create_card(self):
        return QFrame()

    def section_title(self, icon, text):
        label = QLabel(f"{icon}  {text}")
        label.setObjectName("sectionTitle")
        return label

    def load_settings(self):
        self.program_name.setText(
            self.get_setting(
                "program_name",
                "الشبكة - نظام إدارة الأجهزة والأعطال"
            )
        )
        self.items_per_page.setValue(
            self.safe_int(self.get_setting("items_per_page", "50"), 50, 10, 500)
        )
        self.refresh_seconds.setValue(
            self.safe_int(self.get_setting("refresh_seconds", "2"), 2, 1, 60)
        )

        self.confirm_delete.setChecked(
            self.get_setting("confirm_delete", "1") == "1"
        )
        self.auto_refresh.setChecked(
            self.get_setting("auto_refresh", "1") == "1"
        )

        self.select_text(self.theme, self.get_setting("theme", "فاتح"))
        self.select_text(self.font_size, self.get_setting("font_size", "متوسط"))
        self.rtl.setChecked(self.get_setting("rtl", "1") == "1")

        self.notify_open_faults.setChecked(
            self.get_setting("notify_open_faults", "1") == "1"
        )
        self.notify_parts.setChecked(
            self.get_setting("notify_parts", "1") == "1"
        )
        self.notify_minimum.setChecked(
            self.get_setting("notify_minimum", "1") == "1"
        )
        self.auto_backup.setChecked(
            self.get_setting("auto_backup", "0") == "1"
        )

    @staticmethod
    def safe_int(value, default, minimum, maximum):
        try:
            value = int(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, value))

    @staticmethod
    def select_text(combo, text):
        index = combo.findText(text)
        combo.setCurrentIndex(index if index >= 0 else 0)

    def save_general(self):
        self.set_setting("program_name", self.program_name.text().strip())
        self.set_setting("items_per_page", self.items_per_page.value())
        self.set_setting("refresh_seconds", self.refresh_seconds.value())
        self.set_setting("confirm_delete", 1 if self.confirm_delete.isChecked() else 0)
        self.set_setting("auto_refresh", 1 if self.auto_refresh.isChecked() else 0)

        self.settings_changed.emit()
        QMessageBox.information(self, "تم الحفظ", "تم حفظ إعدادات التشغيل وتطبيقها على النظام.")

    def save_appearance(self):
        self.set_setting("theme", self.theme.currentText())
        self.set_setting("font_size", self.font_size.currentText())
        self.set_setting("rtl", 1 if self.rtl.isChecked() else 0)

        self.settings_changed.emit()
        QMessageBox.information(self, "تم التطبيق", "تم تطبيق إعدادات المظهر على النظام.")

    def save_alerts(self):
        self.set_setting("notify_open_faults", 1 if self.notify_open_faults.isChecked() else 0)
        self.set_setting("notify_parts", 1 if self.notify_parts.isChecked() else 0)
        self.set_setting("notify_minimum", 1 if self.notify_minimum.isChecked() else 0)

        self.settings_changed.emit()
        QMessageBox.information(self, "تم الحفظ", "تم حفظ إعدادات التنبيهات.")

    def refresh_summary(self):
        try:
            con = get_connection()
            cur = con.cursor()

            def count(sql, params=()):
                cur.execute(sql, params)
                return cur.fetchone()[0]

            devices = count("SELECT COUNT(*) FROM devices WHERE is_archived = 0")
            faults = count("SELECT COUNT(*) FROM faults")
            open_faults = count(
                "SELECT COUNT(*) FROM faults "
                "WHERE status NOT IN ('تم الإصلاح', 'تم التسليم')"
            )

            try:
                parts = count("SELECT COUNT(*) FROM spare_parts WHERE is_archived = 0")
            except sqlite3.OperationalError:
                parts = 0

            con.close()

            self.devices_card.set_value(devices)
            self.faults_card.set_value(faults)
            self.open_faults_card.set_value(open_faults)
            self.parts_card.set_value(parts)

            self.system_info.setText(
                f"الأجهزة النشطة: {devices}   |   "
                f"إجمالي الأعطال: {faults}   |   "
                f"الأعطال المفتوحة: {open_faults}   |   "
                f"قطع الغيار: {parts}\n\n"
                f"آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as exc:
            self.system_info.setText(f"تعذر قراءة حالة النظام:\n{exc}")

    def create_backup(self):
        if not os.path.exists(self.database_path):
            QMessageBox.critical(self, "خطأ", "قاعدة البيانات غير موجودة.")
            return

        default_name = (
            "network_faults_backup_"
            f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db"
        )

        target, _ = QFileDialog.getSaveFileName(
            self, "إنشاء نسخة احتياطية", default_name, "SQLite Database (*.db)"
        )
        if not target:
            return

        try:
            source = sqlite3.connect(self.database_path)
            source.execute("PRAGMA wal_checkpoint(FULL)")
            backup = sqlite3.connect(target)
            source.backup(backup)
            backup.close()
            source.close()
            QMessageBox.information(self, "تم", "تم إنشاء النسخة الاحتياطية بنجاح.")
        except Exception as exc:
            QMessageBox.critical(self, "خطأ", f"تعذر إنشاء النسخة:\n{exc}")

    def restore_backup(self):
        source, _ = QFileDialog.getOpenFileName(
            self, "اختيار النسخة الاحتياطية", "", "SQLite Database (*.db)"
        )
        if not source:
            return

        answer = QMessageBox.warning(
            self,
            "تأكيد الاستعادة",
            "سيتم استبدال قاعدة البيانات الحالية.\n"
            "سيتم إنشاء نسخة أمان من القاعدة الحالية أولًا.\n\n"
            "هل تريد المتابعة؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if answer != QMessageBox.Yes:
            return

        try:
            safety = (
                f"{self.database_path}.before_restore_"
                f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db"
            )
            if os.path.exists(self.database_path):
                shutil.copy2(self.database_path, safety)

            shutil.copy2(source, self.database_path)

            QMessageBox.information(
                self,
                "تمت الاستعادة",
                "تمت استعادة قاعدة البيانات.\n"
                "أغلق البرنامج وافتحه مرة أخرى حتى تعمل القاعدة الجديدة بالكامل."
            )
        except Exception as exc:
            QMessageBox.critical(self, "خطأ", f"تعذر الاستعادة:\n{exc}")

    def open_database_folder(self):
        folder = os.path.dirname(self.database_path)
        if not os.path.exists(folder):
            QMessageBox.warning(self, "تنبيه", "مجلد البيانات غير موجود.")
            return
        try:
            os.startfile(folder)
        except Exception as exc:
            QMessageBox.critical(self, "خطأ", f"تعذر فتح المجلد:\n{exc}")
