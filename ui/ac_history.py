"""
سجل تبديل التكييف: نافذة احترافية.

  - ملخص علوي: نسبة الالتزام + في موعدها + متأخرة + غير مؤكدة
  - فلاتر سريعة (الكل / في موعدها / متأخرة / غير مؤكدة) + بحث + فترة (7 أيام / 30 يومًا)
  - جدول بحالة ملوّنة على شكل شارة (pill) وسبب التأخير كاملًا في الـ Tooltip
  - تصدير CSV يفتح مباشرة في Excel بالعربي
"""
import csv
from datetime import datetime, timedelta

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database import get_connection

from . import ac_repository as repo
from . import ac_schedule as sched

ALIGN_RIGHT = Qt.AlignRight | Qt.AlignAbsolute | Qt.AlignVCenter

# لون النص / لون الخلفية لكل حالة (هادي: أخضر / كهرماني / أحمر للمشاكل فقط)
PILL_COLORS = {
    sched.HISTORY_ON_TIME: ("#15803d", "#e7f6ee"),
    sched.HISTORY_LATE: ("#b45309", "#fdf1dc"),
    sched.HISTORY_UNCONFIRMED: ("#b91c1c", "#fdeaea"),
}
MUTED = "#c0cad4"

STYLE = """
    QDialog { background: #f6f8fb; }
    QLabel { color: #334155; font-size: 13px; }
    #histTitle { color: #0f2338; font-size: 19px; font-weight: 800; }
    #histSub { color: #64748b; font-size: 12px; font-weight: 500; }

    #kpiCard {
        background: #ffffff; border: 1px solid #e6ebf1; border-radius: 14px;
    }
    #kpiTitle { color: #64748b; font-size: 12px; font-weight: 600; }
    #kpiValue { color: #0f2338; font-size: 26px; font-weight: 800; }
    #kpiValue[tone="good"] { color: #15803d; }
    #kpiValue[tone="warn"] { color: #b45309; }
    #kpiValue[tone="bad"] { color: #b91c1c; }
    #kpiSub { color: #94a3b8; font-size: 11px; font-weight: 500; }

    QPushButton {
        background: #ffffff; color: #0e7490; border: 1px solid #dbe3ea;
        border-radius: 10px; padding: 8px 16px; font-size: 12px; font-weight: 800;
    }
    QPushButton:hover { background: #eef6f8; }
    QPushButton:disabled { background: #f1f5f9; color: #94a3b8; }
    QPushButton#segBtn {
        background: #ffffff; color: #475569; border: 1px solid #dbe3ea;
        border-radius: 9px; padding: 6px 14px; font-size: 12px; font-weight: 700;
    }
    QPushButton#segBtn:hover { background: #f1f6f8; }
    QPushButton#segBtn:checked {
        background: #0e9aaa; color: #ffffff; border: 1px solid #0e9aaa;
    }

    QLineEdit {
        background: #ffffff; border: 1px solid #dbe3ea; border-radius: 9px;
        padding: 6px 12px; font-size: 12px; color: #0f2338;
    }
    QLineEdit:focus { border: 1px solid #0e9aaa; }

    QTableWidget {
        background: #ffffff; border: 1px solid #e6ebf1; border-radius: 12px;
        color: #334155; font-size: 12px; gridline-color: transparent;
        selection-background-color: #eef6f8; selection-color: #0f2338;
    }
    QTableWidget::item { padding: 4px 8px; border-bottom: 1px solid #f0f3f7; }
    QHeaderView::section {
        background: #fbfcfd; color: #94a3b8; border: none;
        border-bottom: 1px solid #e6ebf1; padding: 10px 8px;
        font-size: 12px; font-weight: 700;
    }
    QScrollBar:vertical { width: 8px; background: transparent; margin: 2px; }
    QScrollBar::handle:vertical {
        background: #cfd8e1; border-radius: 4px; min-height: 30px;
    }
    QScrollBar::handle:vertical:hover { background: #b6c4d0; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

    #emptyLabel { color: #94a3b8; font-size: 13px; font-weight: 600; }
    #histFooter { color: #94a3b8; font-size: 11px; font-weight: 500; }
"""


# =============================================================
# مكونات صغيرة
# =============================================================
class _Bar(QWidget):
    """شريط نسبة رفيع. بيتملي من اليمين (الواجهة RTL)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(6)
        self._percent = 0
        self._color = QColor("#0e9aaa")

    def set_value(self, percent, color):
        self._percent = max(0, min(100, percent or 0))
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        track = QPainterPath()
        track.addRoundedRect(rect, 3, 3)
        painter.fillPath(track, QColor("#e6ebf1"))
        width = rect.width() * self._percent / 100
        if width > 0:
            fill = QPainterPath()
            fill.addRoundedRect(QRectF(rect.right() - width, rect.top(), width, rect.height()), 3, 3)
            painter.fillPath(fill, self._color)
        painter.end()


class _KpiCard(QFrame):
    def __init__(self, title, dot_color, with_bar=False):
        super().__init__()
        self.setObjectName("kpiCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(104 if with_bar else 96)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(8)
        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background: {dot_color}; border-radius: 4px;")
        top.addWidget(dot, 0, Qt.AlignVCenter)
        title_label = QLabel(title)
        title_label.setObjectName("kpiTitle")
        top.addWidget(title_label, 1)
        layout.addLayout(top)

        self.value_label = QLabel("—")
        self.value_label.setObjectName("kpiValue")
        self.value_label.setAlignment(ALIGN_RIGHT)
        layout.addWidget(self.value_label)

        self.bar = None
        if with_bar:
            self.bar = _Bar()
            layout.addWidget(self.bar)

        self.sub_label = QLabel("")
        self.sub_label.setObjectName("kpiSub")
        self.sub_label.setAlignment(ALIGN_RIGHT)
        layout.addWidget(self.sub_label)

    def set_data(self, value, sub="", tone="", percent=None, bar_color="#0e9aaa"):
        self.value_label.setText(str(value))
        self.sub_label.setText(sub)
        self.value_label.setProperty("tone", tone)
        self.value_label.style().unpolish(self.value_label)
        self.value_label.style().polish(self.value_label)
        if self.bar is not None:
            self.bar.set_value(percent, bar_color)


class _StatusPillDelegate(QStyledItemDelegate):
    """يرسم الحالة كشارة ملوّنة (من غير أيقونات أو إيموجي)."""

    def paint(self, painter, option, index):
        key = index.data(Qt.UserRole)
        fg, bg = PILL_COLORS.get(key, ("#475569", "#eef2f6"))
        text = str(index.data(Qt.DisplayRole) or "")

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#eef6f8"))

        font = QFont(option.font)
        font.setBold(True)
        painter.setFont(font)
        width = QFontMetrics(font).horizontalAdvance(text) + 26
        rect = QRectF(0, 0, min(width, option.rect.width() - 8), 24)
        rect.moveCenter(QRectF(option.rect).center())

        path = QPainterPath()
        path.addRoundedRect(rect, 12, 12)
        painter.fillPath(path, QColor(bg))
        painter.setPen(QColor(fg))
        painter.drawText(rect, Qt.AlignCenter, text)
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setWidth(size.width() + 34)
        return size


# =============================================================
# نافذة السجل
# =============================================================
class AcHistoryDialog(QDialog):
    COLUMNS = [
        "الموعد المجدول", "الحالة", "وقت التنفيذ الفعلي",
        "المستخدم", "التأخير", "سبب التأخير",
    ]
    CSV_COLUMNS = [
        "الموعد المجدول", "الحالة", "وقت التنفيذ الفعلي",
        "المستخدم", "التأخير (دقيقة)", "سبب التأخير",
    ]
    PERIODS = ((7, "7 أيام"), (30, "30 يومًا"))
    FILTERS = (
        (None, "الكل"),
        (sched.HISTORY_ON_TIME, "في موعدها"),
        (sched.HISTORY_LATE, "متأخرة"),
        (sched.HISTORY_UNCONFIRMED, "غير مؤكدة"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("سجل تبديل التكييف")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(880, 580)
        self.resize(1040, 700)
        self.setStyleSheet(STYLE)

        self._rows = []
        self._visible = []
        self._days = sched.HISTORY_DAYS
        self._filter_key = None
        self._filter_buttons = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        # ---------- الهيدر ----------
        header = QHBoxLayout()
        header.setSpacing(10)
        titles = QVBoxLayout()
        titles.setSpacing(2)
        title = QLabel("سجل تبديل التكييف")
        title.setObjectName("histTitle")
        title.setAlignment(ALIGN_RIGHT)
        self.subtitle = QLabel("")
        self.subtitle.setObjectName("histSub")
        self.subtitle.setAlignment(ALIGN_RIGHT)
        titles.addWidget(title)
        titles.addWidget(self.subtitle)
        header.addLayout(titles, 1)

        self.refresh_button = QPushButton("تحديث")
        self.refresh_button.setCursor(Qt.PointingHandCursor)
        self.refresh_button.clicked.connect(self._load)
        header.addWidget(self.refresh_button)

        period_group = QButtonGroup(self)
        period_group.setExclusive(True)
        for days, label in self.PERIODS:
            button = QPushButton(label)
            button.setObjectName("segBtn")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setChecked(days == self._days)
            button.clicked.connect(lambda _=False, d=days: self._set_period(d))
            period_group.addButton(button)
            header.addWidget(button)
        self._period_group = period_group
        root.addLayout(header)

        # ---------- بطاقات الملخص ----------
        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.card_rate = _KpiCard("نسبة الالتزام", "#0e9aaa", with_bar=True)
        self.card_on_time = _KpiCard("في موعدها", "#22a06b")
        self.card_late = _KpiCard("متأخرة", "#d97706")
        self.card_missed = _KpiCard("غير مؤكدة", "#dc2626")
        for card in (self.card_rate, self.card_on_time, self.card_late, self.card_missed):
            cards.addWidget(card, 1)
        root.addLayout(cards)

        # ---------- شريط الفلاتر والبحث ----------
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        filter_group = QButtonGroup(self)
        filter_group.setExclusive(True)
        for key, label in self.FILTERS:
            button = QPushButton(label)
            button.setObjectName("segBtn")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setChecked(key is None)
            button.clicked.connect(lambda _=False, k=key: self._set_filter(k))
            filter_group.addButton(button)
            toolbar.addWidget(button)
            self._filter_buttons[key] = button
        self._filter_group = filter_group
        toolbar.addStretch(1)

        self.search = QLineEdit()
        self.search.setPlaceholderText("بحث بالمستخدم أو سبب التأخير…")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(280)
        self.search.textChanged.connect(self._apply_filter)
        toolbar.addWidget(self.search)
        root.addLayout(toolbar)

        # ---------- الجدول + رسالة الفراغ ----------
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.setItemDelegateForColumn(1, _StatusPillDelegate(self.table))
        header_view = self.table.horizontalHeader()
        header_view.setHighlightSections(False)
        header_view.setSectionResizeMode(QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(len(self.COLUMNS) - 1, QHeaderView.Stretch)
        header_view.setFixedHeight(40)
        root.addWidget(self.table, 1)

        self.empty_label = QLabel("")
        self.empty_label.setObjectName("emptyLabel")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.empty_label.hide()
        root.addWidget(self.empty_label, 1)

        # ---------- الفوتر ----------
        footer = QHBoxLayout()
        footer.setSpacing(10)
        self.updated_label = QLabel("")
        self.updated_label.setObjectName("histFooter")
        footer.addWidget(self.updated_label)
        footer.addStretch(1)
        self.export_button = QPushButton("تصدير CSV")
        self.export_button.setCursor(Qt.PointingHandCursor)
        self.export_button.clicked.connect(self._export)
        close = QPushButton("إغلاق")
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.accept)
        footer.addWidget(self.export_button)
        footer.addWidget(close)
        root.addLayout(footer)

        # النافذة تظهر الأول وبعدين نقرا القاعدة (من غير ما تبان متأخرة)
        self._show_empty("جارٍ تحميل السجل…")
        QTimer.singleShot(0, self._load)

    # ---------------------------------------------------------
    # التحميل
    # ---------------------------------------------------------
    def _load(self):
        self.refresh_button.setEnabled(False)
        now = datetime.now()
        error = None
        tracking_start = None
        records = {}
        try:
            conn = get_connection()
            try:
                repo.ensure_schema(conn)
                tracking_start = repo.get_tracking_start(conn, now)
                records = repo.fetch_records(conn, now - timedelta(days=self._days), now)
            finally:
                conn.close()
        except Exception as exc:
            error = str(exc)
        self.refresh_button.setEnabled(True)

        if error is not None:
            self._rows = []
            self._visible = []
            self._update_summary()
            self.updated_label.setText("")
            self._show_empty(f"تعذر قراءة السجل من قاعدة البيانات:\n{error}")
            return

        self._rows = sched.history_rows(now, records, tracking_start, days=self._days)
        self.updated_label.setText("آخر تحديث " + sched.format_time_ar(now))
        self._update_summary()
        self._apply_filter()

    def _set_period(self, days):
        if days == self._days:
            return
        self._days = days
        self._load()

    def _set_filter(self, key):
        self._filter_key = key
        self._apply_filter()

    # ---------------------------------------------------------
    # الملخص
    # ---------------------------------------------------------
    def _update_summary(self):
        stats = sched.compliance_summary(self._rows)
        total = stats["total"]
        period_label = dict(self.PERIODS).get(self._days, f"{self._days} يومًا")
        self.subtitle.setText(
            f"آخر {period_label} · {total} تبديل مطلوب تأكيده (8 ص / 12 ظ / 4 ع)"
            if total
            else f"آخر {period_label} · لا توجد مواعيد مسجلة بعد؛ سيبدأ السجل من أول موعد قادم."
        )

        percent = stats["on_time_percent"]
        if percent is None:
            self.card_rate.set_data("—", "لا توجد بيانات", "", 0)
        else:
            if percent >= 90:
                tone, color = "good", "#22a06b"
            elif percent >= 70:
                tone, color = "warn", "#d97706"
            else:
                tone, color = "bad", "#dc2626"
            self.card_rate.set_data(
                f"{percent}%", f"{stats['on_time']} من {total} تبديل", tone, percent, color
            )

        self.card_on_time.set_data(stats["on_time"], "تم التأكيد في الموعد")

        late_delays = [
            r["delay_minutes"] for r in self._rows
            if r["status_key"] == sched.HISTORY_LATE and r["delay_minutes"]
        ]
        late_sub = (
            f"متوسط التأخير {sched.format_duration_ar(round(sum(late_delays) / len(late_delays)))}"
            if late_delays else "تم التأكيد بعد الموعد"
        )
        self.card_late.set_data(stats["late"], late_sub, "warn" if stats["late"] else "")

        self.card_missed.set_data(
            stats["unconfirmed"], "لم يتم تأكيدها", "bad" if stats["unconfirmed"] else ""
        )

        counts = {
            None: total,
            sched.HISTORY_ON_TIME: stats["on_time"],
            sched.HISTORY_LATE: stats["late"],
            sched.HISTORY_UNCONFIRMED: stats["unconfirmed"],
        }
        for key, label in self.FILTERS:
            self._filter_buttons[key].setText(f"{label} ({counts[key]})")

    # ---------------------------------------------------------
    # الجدول
    # ---------------------------------------------------------
    def _show_empty(self, text):
        self.table.hide()
        self.empty_label.setText(text)
        self.empty_label.show()

    def _apply_filter(self):
        wanted = self._filter_key
        query = self.search.text().strip().casefold()
        rows = []
        for row in self._rows:
            if wanted is not None and row["status_key"] != wanted:
                continue
            if query:
                haystack = f"{row['confirmed_by']} {row['delay_reason']}".casefold()
                if query not in haystack:
                    continue
            rows.append(row)
        self._visible = rows
        self._populate()

    def _populate(self):
        rows = self._visible
        if not rows:
            if not self._rows:
                self._show_empty("لا توجد مواعيد في هذه الفترة.")
            else:
                self._show_empty("لا توجد نتائج مطابقة للفلتر أو البحث.")
            return

        self.empty_label.hide()
        self.table.show()

        now = datetime.now()
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            delay = (
                sched.format_duration_ar(row["delay_minutes"]) if row["delay_minutes"] else "—"
            )
            values = [
                sched.format_datetime_ar(row["scheduled"], now),
                row["status_label"],
                sched.format_datetime_ar(row["confirmed_at"], now),
                row["confirmed_by"] or "—",
                delay,
                row["delay_reason"] or "—",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 5:
                    item.setTextAlignment(ALIGN_RIGHT)
                    if row["delay_reason"]:
                        item.setToolTip(row["delay_reason"])
                else:
                    item.setTextAlignment(Qt.AlignCenter)

                if col == 0:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    item.setForeground(QColor("#0f2338"))
                elif col == 1:
                    item.setData(Qt.UserRole, row["status_key"])
                elif value == "—":
                    item.setForeground(QColor(MUTED))
                self.table.setItem(index, col, item)
        self.table.setUpdatesEnabled(True)

    # ---------------------------------------------------------
    # التصدير
    # ---------------------------------------------------------
    def _export(self):
        if not self._visible:
            QMessageBox.information(self, "تصدير السجل", "لا توجد بيانات لتصديرها.")
            return

        default_name = f"ac_history_{datetime.now():%Y-%m-%d}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "تصدير سجل التكييف", default_name, "CSV (*.csv)"
        )
        if not path:
            return

        def stamp(value):
            return value.strftime("%Y-%m-%d %H:%M") if value else ""

        try:
            # utf-8-sig: عشان Excel يقرا العربي صح
            with open(path, "w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                writer.writerow(self.CSV_COLUMNS)
                for row in self._visible:
                    writer.writerow(
                        [
                            stamp(row["scheduled"]),
                            row["status_label"],
                            stamp(row["confirmed_at"]),
                            row["confirmed_by"],
                            row["delay_minutes"] or 0,
                            row["delay_reason"],
                        ]
                    )
        except OSError as exc:
            QMessageBox.warning(self, "تعذر التصدير", f"لم يتم حفظ الملف.\n\n{exc}")
            return

        self.updated_label.setText(f"تم تصدير {len(self._visible)} صف")