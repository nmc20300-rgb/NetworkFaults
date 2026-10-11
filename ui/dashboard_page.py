import json
from datetime import date, datetime, timedelta

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QUrl, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QBoxLayout,
    QGraphicsOpacityEffect,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy,
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from database import get_connection

# محاذاة لليمين بشكل مطلق (بدون انعكاس تلقائي في الواجهات RTL)
ALIGN_RIGHT = Qt.AlignRight | Qt.AlignAbsolute | Qt.AlignVCenter


# =============================================================
# أدوات التنسيق (12 ساعة / التاريخ بالعربي)
# =============================================================
ARABIC_WEEKDAYS = [
    "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد",
]
ARABIC_MONTHS = [
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
]


def to_12h(value):
    """يحوّل '17:05' إلى '5:05 م' (نظام 12 ساعة بالعربي)."""
    parsed = datetime.strptime(value, "%H:%M")
    hour = parsed.hour % 12 or 12
    suffix = "ص" if parsed.hour < 12 else "م"
    return f"{hour}:{parsed.minute:02d} {suffix}"


def format_remaining(total_minutes):
    """يحوّل عدد الدقائق إلى نص مقروء: '1 ساعة و 20 دقيقة'."""
    hours, minutes = divmod(max(0, total_minutes), 60)
    if hours and minutes:
        return f"{hours} ساعة و {minutes} دقيقة"
    if hours:
        return f"{hours} ساعة"
    if minutes:
        return f"{minutes} دقيقة"
    return "أقل من دقيقة"


def format_entry_date(value):
    """تاريخ العطل بشكل مقروء: '10 أكتوبر · 9:15 م' (والسنة لو مش السنة الحالية)."""
    if not value:
        return "—"

    parsed = None
    has_time = True
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, datetime.min.time())
        has_time = False
    else:
        text = str(value).strip()
        formats = (
            ("%Y-%m-%d %H:%M:%S.%f", True),
            ("%Y-%m-%d %H:%M:%S", True),
            ("%Y-%m-%d %H:%M", True),
            ("%H:%M:%S %Y-%m-%d", True),
            ("%H:%M %Y-%m-%d", True),
            ("%Y-%m-%d", False),
        )
        for fmt, with_time in formats:
            try:
                parsed = datetime.strptime(text, fmt)
                has_time = with_time
                break
            except ValueError:
                continue
        if parsed is None:
            return text

    result = f"{parsed.day} {ARABIC_MONTHS[parsed.month - 1]}"
    if parsed.year != datetime.now().year:
        result += f" {parsed.year}"
    if has_time:
        result += " · " + to_12h(parsed.strftime("%H:%M"))
    return result


# =============================================================
# ساعة عقارب (Analog)
# =============================================================
class AnalogClock(QWidget):
    def __init__(self, size=54, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        now = datetime.now()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height())
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(side / 200.0, side / 200.0)

        # وجه الساعة
        painter.setPen(QPen(QColor("#0e9aaa"), 8))
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(-92, -92, 184, 184)

        # علامات الساعات (الأربع الرئيسية فقط أغمق)
        for i in range(12):
            major = i % 3 == 0
            painter.setPen(
                QPen(
                    QColor("#334155") if major else QColor("#b6c4d0"),
                    8 if major else 5,
                    Qt.SolidLine,
                    Qt.RoundCap,
                )
            )
            painter.drawLine(0, -76, 0, -62 if major else -68)
            painter.rotate(30)

        def hand(angle, length, width, color):
            painter.save()
            painter.rotate(angle)
            painter.setPen(QPen(QColor(color), width, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(0, 0, 0, -length)
            painter.restore()

        hour_angle = ((now.hour % 12) + now.minute / 60) * 30
        minute_angle = (now.minute + now.second / 60) * 6
        second_angle = now.second * 6

        hand(hour_angle, 44, 10, "#0f2338")
        hand(minute_angle, 64, 7, "#0f2338")
        hand(second_angle, 72, 3, "#0e9aaa")

        # مركز الساعة
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#0e9aaa"))
        painter.drawEllipse(-8, -8, 16, 16)
        painter.end()


# =============================================================
# بطاقة الساعة والتاريخ (مدمجة وثابتة الحجم)
# =============================================================
class ClockCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("clockCard")
        self.setLayoutDirection(Qt.LeftToRight)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 18, 8)
        layout.setSpacing(12)

        self.analog = AnalogClock(54)
        layout.addWidget(self.analog, 0, Qt.AlignVCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)

        time_row = QHBoxLayout()
        time_row.setSpacing(7)
        time_row.addStretch(1)
        self.time_label = QLabel("12:00")
        self.time_label.setObjectName("clockTime")
        self.time_label.setMinimumWidth(78)
        self.time_label.setAlignment(ALIGN_RIGHT)
        self.period_label = QLabel("ص")
        self.period_label.setObjectName("clockPeriod")
        self.period_label.setAlignment(Qt.AlignCenter)
        time_row.addWidget(self.time_label, 0, Qt.AlignVCenter)
        time_row.addWidget(self.period_label, 0, Qt.AlignVCenter)
        text_col.addLayout(time_row)

        self.date_label = QLabel("")
        self.date_label.setObjectName("clockDate")
        self.date_label.setLayoutDirection(Qt.RightToLeft)
        self.date_label.setAlignment(ALIGN_RIGHT)
        self.date_label.setMinimumWidth(170)
        text_col.addWidget(self.date_label)
        layout.addLayout(text_col)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)
        self.tick()

    def tick(self):
        now = datetime.now()
        self.time_label.setText(f"{now.hour % 12 or 12}:{now.minute:02d}")
        self.period_label.setText("ص" if now.hour < 12 else "م")
        self.date_label.setText(
            f"{ARABIC_WEEKDAYS[now.weekday()]}، {now.day} "
            f"{ARABIC_MONTHS[now.month - 1]} {now.year}"
        )
        self.analog.update()


# =============================================================
# بطاقة إحصائية (بدون أيقونات؛ لون واحد يدل على الحالة فقط)
# =============================================================
class StatCard(QFrame):
    def __init__(self, title, value="0", dot_color="#0e9aaa"):
        super().__init__()
        self.setObjectName("statCard")
        self.setFixedHeight(98)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(8)
        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background: {dot_color}; border-radius: 4px;")
        top.addWidget(dot, 0, Qt.AlignVCenter)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        top.addWidget(title_label, 1)
        layout.addLayout(top)

        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("cardValue")
        self.value_label.setAlignment(ALIGN_RIGHT)
        layout.addWidget(self.value_label)

    def set_value(self, value, tone=""):
        self.value_label.setText(str(value))
        self.value_label.setProperty("tone", tone)
        self.value_label.style().unpolish(self.value_label)
        self.value_label.style().polish(self.value_label)


# =============================================================
# لوحة صغيرة
# =============================================================
class MiniPanel(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("dashboardPanel")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 18, 20, 20)
        self.layout.setSpacing(14)

        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        self.layout.addWidget(title_label)


# =============================================================
# لوحة مواقيت الصلاة - الإسكندرية / مصر
# =============================================================
class PrayerTimesPanel(QFrame):
    COLLAPSED_WIDTH = 68
    EXPANDED_WIDTH = 252
    PRAYERS = [
        ("Fajr", "الفجر"),
        ("Sunrise", "الشروق"),
        ("Dhuhr", "الظهر"),
        ("Asr", "العصر"),
        ("Maghrib", "المغرب"),
        ("Isha", "العشاء"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("prayerPanel")
        self.setLayoutDirection(Qt.RightToLeft)
        # الارتفاع على قد المحتوى (بدون فراغ طويل تحت)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
        self.setFixedWidth(self.COLLAPSED_WIDTH)

        self.times = None  # تُحفظ بنظام 24 ساعة للحساب، وتُعرض بنظام 12 ساعة
        self.loaded_date = None
        self.pending_reply = None
        self._last_load_attempt = None  # لمنع تكرار الطلبات كل ثانية لو النت فاصل
        self._last_next_key = None
        self._countdown_tone = ""
        self.network = QNetworkAccessManager(self)
        self.network.finished.connect(self._handle_reply)

        panel_layout = QVBoxLayout(self)
        panel_layout.setContentsMargins(9, 12, 9, 14)
        panel_layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(7)
        self.title_label = QLabel("مواقيت الصلاة")
        self.title_label.setObjectName("prayerPanelTitle")
        self.title_label.setAlignment(ALIGN_RIGHT)
        header.addWidget(self.title_label, 1)

        self.toggle_button = QPushButton("مواقيت\nالصلاة")
        self.toggle_button.setObjectName("prayerToggle")
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.setFixedSize(48, 54)
        self.toggle_button.clicked.connect(self.toggle)
        header.addWidget(self.toggle_button)
        panel_layout.addLayout(header)

        self.content = QWidget()
        self.content.setObjectName("prayerContent")
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(4, 2, 4, 2)
        content_layout.setSpacing(8)

        self.city_label = QLabel("الإسكندرية · مصر")
        self.city_label.setObjectName("prayerCity")
        self.city_label.setAlignment(ALIGN_RIGHT)
        content_layout.addWidget(self.city_label)

        # رسالة التحميل / الخطأ
        self.next_status = QLabel("جارٍ تحميل مواقيت اليوم…")
        self.next_status.setObjectName("prayerStatus")
        self.next_status.setAlignment(Qt.AlignCenter)
        self.next_status.setWordWrap(True)
        content_layout.addWidget(self.next_status)

        # الصلاة القادمة: كل معلومة في سطر مستقل (يمنع تلخبط الأرقام مع العربي)
        self.next_box = QFrame()
        self.next_box.setObjectName("prayerNext")
        next_layout = QVBoxLayout(self.next_box)
        next_layout.setContentsMargins(12, 9, 12, 9)
        next_layout.setSpacing(3)

        caption = QLabel("الصلاة القادمة")
        caption.setObjectName("prayerNextCaption")
        caption.setAlignment(ALIGN_RIGHT)
        next_layout.addWidget(caption)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        self.next_name = QLabel("")
        self.next_name.setObjectName("prayerNextName")
        self.next_time = QLabel("")
        self.next_time.setObjectName("prayerNextTime")
        self.next_time.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        name_row.addWidget(self.next_name, 1)
        name_row.addWidget(self.next_time)
        next_layout.addLayout(name_row)

        # عدّاد تنازلي حي: "متبقي" على اليمين والعدّاد على اليسار
        countdown_row = QHBoxLayout()
        countdown_row.setSpacing(8)
        remaining_caption = QLabel("متبقي")
        remaining_caption.setObjectName("prayerNextRemaining")
        remaining_caption.setAlignment(ALIGN_RIGHT)
        self.next_countdown = QLabel("00:00:00")
        self.next_countdown.setObjectName("prayerCountdown")
        self.next_countdown.setLayoutDirection(Qt.LeftToRight)
        self.next_countdown.setAlignment(Qt.AlignLeft | Qt.AlignAbsolute | Qt.AlignVCenter)
        countdown_row.addWidget(remaining_caption, 1)
        countdown_row.addWidget(self.next_countdown)
        next_layout.addLayout(countdown_row)

        self.next_box.hide()
        content_layout.addWidget(self.next_box)

        self.row_widgets = {}
        self.time_labels = {}
        for key, arabic_name in self.PRAYERS:
            row = QWidget()
            row.setObjectName("prayerRow")
            row.setLayoutDirection(Qt.RightToLeft)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(11, 7, 11, 7)
            row_layout.setSpacing(8)

            name_label = QLabel(arabic_name)
            name_label.setObjectName("prayerName")
            name_label.setAlignment(ALIGN_RIGHT)
            time_label = QLabel("--:--")
            time_label.setObjectName("prayerTime")
            time_label.setMinimumWidth(66)
            time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            row_layout.addWidget(name_label, 1)
            row_layout.addWidget(time_label)
            content_layout.addWidget(row)
            self.row_widgets[key] = row
            self.time_labels[key] = time_label

        self.method_label = QLabel("الحساب: الهيئة المصرية العامة للمساحة")
        self.method_label.setObjectName("prayerMethod")
        self.method_label.setWordWrap(True)
        self.method_label.setAlignment(ALIGN_RIGHT)
        content_layout.addWidget(self.method_label)
        panel_layout.addWidget(self.content)
        self.title_label.hide()
        self.content.hide()

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_countdown)
        self.clock_timer.start(1000)

    def toggle(self):
        expanded = not self.content.isVisible()
        self.content.setVisible(expanded)
        self.title_label.setVisible(expanded)
        self.toggle_button.setText("−" if expanded else "مواقيت\nالصلاة")
        self.toggle_button.setFixedSize(38 if expanded else 48, 38 if expanded else 54)
        self.setFixedWidth(self.EXPANDED_WIDTH if expanded else self.COLLAPSED_WIDTH)

    def load_times(self):
        if self.pending_reply is not None:
            return

        self._last_load_attempt = datetime.now()
        request_date = datetime.now().strftime("%d-%m-%Y")
        url = (
            "https://api.aladhan.com/v1/timings/"
            f"{request_date}?latitude=31.2001&longitude=29.9187"
            "&method=5&timezonestring=Africa%2FCairo"
        )
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"User-Agent", b"NetworkFaults-PrayerTimes/1.0")
        if hasattr(request, "setTransferTimeout"):
            request.setTransferTimeout(12_000)
        self.pending_reply = self.network.get(request)
        self.pending_reply.setProperty("requestedDate", request_date)

    def _show_status(self, text):
        self.next_box.hide()
        self.next_status.setText(text)
        self.next_status.show()

    def _handle_reply(self, reply):
        if reply != self.pending_reply:
            reply.deleteLater()
            return

        request_date = reply.property("requestedDate") or datetime.now().strftime("%d-%m-%Y")
        self.pending_reply = None
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                raise RuntimeError("تعذر الاتصال بخدمة المواقيت")

            payload = json.loads(bytes(reply.readAll()).decode("utf-8"))
            if payload.get("code") != 200:
                raise RuntimeError("خدمة المواقيت لم تُرجع بيانات صحيحة")

            data = payload["data"]
            meta = data.get("meta", {})
            method = meta.get("method", {})
            if method.get("id") != 5:
                raise RuntimeError("استجابة الخدمة لم تستخدم طريقة الحساب المصرية")
            if meta.get("timezone") != "Africa/Cairo":
                raise RuntimeError("استجابة الخدمة لم تُرجع توقيت مصر المحلي")
            if (
                abs(float(meta.get("latitude", 0)) - 31.2001) > 0.1
                or abs(float(meta.get("longitude", 0)) - 29.9187) > 0.1
            ):
                raise RuntimeError("استجابة الخدمة لا تخص إحداثيات الإسكندرية")

            timing_keys = [key for key, _ in self.PRAYERS]
            timings = data["timings"]
            parsed_times = {key: str(timings[key]).split()[0][:5] for key in timing_keys}
            for value in parsed_times.values():
                datetime.strptime(value, "%H:%M")

            self.times = parsed_times
            self.loaded_date = request_date
            for key, value in parsed_times.items():
                self.time_labels[key].setText(to_12h(value))
            self._update_countdown()
        except Exception:
            self.times = None
            for time_label in self.time_labels.values():
                time_label.setText("--:--")
            self._show_status("تعذر تحميل المواقيت. تحقق من الاتصال بالإنترنت.")
        finally:
            reply.deleteLater()

    def _update_countdown(self):
        today = datetime.now().strftime("%d-%m-%Y")
        if today != self.loaded_date and (
            self._last_load_attempt is None
            or (datetime.now() - self._last_load_attempt).total_seconds() >= 60
        ):
            self.load_times()

        if not self.times:
            return

        now = datetime.now()
        upcoming = []
        for key, arabic_name in self.PRAYERS:
            if key == "Sunrise":
                continue
            prayer_time = datetime.strptime(self.times[key], "%H:%M").time()
            prayer_datetime = datetime.combine(now.date(), prayer_time)
            if prayer_datetime > now:
                upcoming.append((prayer_datetime, key, arabic_name, False))

        if upcoming:
            next_time, next_key, next_name, tomorrow = min(upcoming)
        else:
            fajr_time = datetime.strptime(self.times["Fajr"], "%H:%M").time()
            next_time = datetime.combine(now.date() + timedelta(days=1), fajr_time)
            next_key, next_name, tomorrow = "Fajr", "الفجر", True

        remaining_seconds = max(0, int((next_time - now).total_seconds()))
        hours, rest = divmod(remaining_seconds, 3600)
        minutes, seconds = divmod(rest, 60)

        self.next_status.hide()
        self.next_box.show()
        self.next_name.setText(next_name + (" (غدًا)" if tomorrow else ""))
        self.next_time.setText(to_12h(next_time.strftime("%H:%M")))
        self.next_countdown.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        # أقل من 10 دقايق: العدّاد يتحول للون كهرماني
        tone = "soon" if remaining_seconds < 600 else ""
        if tone != self._countdown_tone:
            self._countdown_tone = tone
            self.next_countdown.setProperty("tone", tone)
            self.next_countdown.style().unpolish(self.next_countdown)
            self.next_countdown.style().polish(self.next_countdown)

        # تمييز صف الصلاة القادمة (فقط عند تغيّرها)
        if next_key != self._last_next_key:
            self._last_next_key = next_key
            for key, row in self.row_widgets.items():
                row.setObjectName("prayerRowNext" if key == next_key else "prayerRow")
                row.style().unpolish(row)
                row.style().polish(row)
                row.update()


# =============================================================
# Dashboard
# =============================================================
class DashboardPage(QWidget):
    DONE_STATUSES = {"تم الإصلاح", "تم التسليم"}
    WARN_STATUSES = {"جديد", "قيد الفحص", "قيد الإصلاح", "بانتظار قطعة غيار"}
    HIGH_PRIORITIES = {"عاجل", "عاجلة", "عالي", "عالية", "حرج", "حرجة", "مرتفع", "مرتفعة"}

    def __init__(self, current_user=None):
        super().__init__()
        self.setObjectName("dashboardPage")
        self.current_user = current_user or {}

        self.setup_ui()
        self.prayer_panel.load_times()
        self.refresh()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5000)

        # حدّث التحية كل دقيقة لكل المستخدمين.
        self.greeting_timer = QTimer(self)
        self.greeting_timer.timeout.connect(self.update_greeting)
        self.greeting_timer.start(60000)

    def is_super_admin(self):
        role_code = str(self.current_user.get("role_code", "") or "").strip().upper()
        return role_code == "SUPER_ADMIN"

    # =========================================================
    # التحية المخصصة للمستخدم الحالي
    # =========================================================
    def update_greeting(self):
        username = str(self.current_user.get("username", "") or "").strip()
        full_name = str(self.current_user.get("full_name", "") or "").strip()
        display_name = str(self.current_user.get("display_name", "") or "").strip()
        name = str(self.current_user.get("name", "") or "").strip()
        role_code = str(self.current_user.get("role_code", "") or "").strip().upper()

        user_profiles = {
            "قائد شبكه الربط المحلية": {"title": "عميد", "name": "أحمد صلاح"},
            "قائد شبكة الربط المحلية": {"title": "عميد", "name": "أحمد صلاح"},
            "superadmin": {"title": "عميد", "name": "أحمد صلاح"},
            "ali": {"title": "بشمهندس", "name": "علي"},
            "m_adel": {"title": "بشمهندس", "name": "محمد عادل"},
            "m_samir": {"title": "بشمهندس", "name": "محمد سمير"},
            "a_galal": {"title": "بشمهندس", "name": "احمد جلال"},
            "m_rashad": {"title": "مهندس", "name": "مصطفي رشاد"},
            "علي سعودي": {"title": "بشمهندس", "name": "علي سعودي"},
            "علي السعودى": {"title": "بشمهندس", "name": "علي سعودي"},
            "م علي سعودي": {"title": "بشمهندس", "name": "علي سعودي"},
            "بشمهندس علي سعودي": {"title": "بشمهندس", "name": "علي سعودي"},
            "ali saudi": {"title": "بشمهندس", "name": "علي سعودي"},
            "ali_saudi": {"title": "بشمهندس", "name": "علي سعودي"},
            "ali.saud": {"title": "بشمهندس", "name": "علي سعودي"},
        }

        candidates = [
            full_name.casefold(),
            display_name.casefold(),
            name.casefold(),
            username.casefold(),
        ]
        profile = next(
            (user_profiles[key] for key in candidates if key in user_profiles),
            None,
        )
        if profile is None and role_code == "SUPER_ADMIN":
            profile = user_profiles["superadmin"]

        if profile:
            person_name = profile["name"]
            title = profile["title"]
        else:
            person_name = full_name or display_name or name or username or "زميلنا"
            role_titles = {
                "SUPER_ADMIN": "قائد الشبكة",
            }
            title = role_titles.get(role_code, "")

        hour = datetime.now().hour
        greeting = "صباح الخير" if 5 <= hour < 12 else "مساء الخير"
        if title == "عميد" and person_name == "أحمد صلاح":
            addressed_name = "سيادة العميد أحمد صلاح"
        else:
            addressed_name = f"{title} {person_name}".strip()

        self.greeting_label.setText(f"{greeting}، {addressed_name}")
        if role_code == "SUPER_ADMIN":
            hint = "إليك ملخص حالة الشبكة والأجهزة والأعطال."
        elif role_code in ("ADMIN", "SUB_ADMIN"):
            hint = "تابع الأعطال والأجهزة ومهام فريقك من لوحة التحكم."
        else:
            hint = "نتمنى لك يوم عمل موفقًا؛ إليك آخر مستجدات النظام."

        self.greeting_hint.setText(hint)

    # =========================================================
    # بناء الواجهة
    # =========================================================
    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 18)
        root.setSpacing(18)

        # ---------- Header: التحية + الساعة + تحديث ----------
        header = QHBoxLayout()
        header.setSpacing(14)

        self.greeting_box = QWidget()
        greeting_layout = QVBoxLayout(self.greeting_box)
        greeting_layout.setContentsMargins(0, 0, 0, 0)
        greeting_layout.setSpacing(4)

        self.greeting_label = QLabel("")
        self.greeting_label.setObjectName("greetingLabel")
        self.greeting_label.setWordWrap(True)
        greeting_layout.addWidget(self.greeting_label)

        self.greeting_hint = QLabel("")
        self.greeting_hint.setObjectName("greetingHint")
        self.greeting_hint.setWordWrap(True)
        greeting_layout.addWidget(self.greeting_hint)
        header.addWidget(self.greeting_box, 1, Qt.AlignVCenter)

        # ساعة + تاريخ (منفصلة تمامًا عن مواقيت الصلاة)
        self.clock_card = ClockCard()
        header.addWidget(self.clock_card, 0, Qt.AlignVCenter)

        root.addLayout(header)

        # Fade-in entrance animation (يعمل مرة واحدة عند فتح الصفحة).
        self.greeting_opacity = QGraphicsOpacityEffect(self.greeting_box)
        self.greeting_box.setGraphicsEffect(self.greeting_opacity)
        self.greeting_opacity.setOpacity(0.0)
        self.greeting_animation = QPropertyAnimation(
            self.greeting_opacity, b"opacity", self
        )
        self.greeting_animation.setDuration(650)
        self.greeting_animation.setStartValue(0.0)
        self.greeting_animation.setEndValue(1.0)
        self.greeting_animation.setEasingCurve(QEasingCurve.OutCubic)
        QTimer.singleShot(80, self.greeting_animation.start)

        # ---------- العمود الرئيسي + صندوق المواقيت الجانبي القابل للطي ----------
        body_layout = QHBoxLayout()
        body_layout.setDirection(QBoxLayout.LeftToRight)
        body_layout.setSpacing(16)
        main_column = QVBoxLayout()
        main_column.setSpacing(18)
        body_layout.addLayout(main_column, 1)
        self.prayer_panel = PrayerTimesPanel(self)
        body_layout.addWidget(self.prayer_panel, 0, Qt.AlignTop)
        root.addLayout(body_layout, 1)

        # ---------- Cards ----------
        self.cards = {}
        cards_layout = QGridLayout()
        cards_layout.setSpacing(14)
        teal, slate, amber = "#0e9aaa", "#94a3b8", "#d97706"
        definitions = [
            ("devices", "إجمالي الأجهزة", teal),
            ("faults", "إجمالي الأعطال", slate),
            ("open", "أعطال مفتوحة", amber),
            ("buildings", "المباني / الفروع", slate),
            ("spare_parts", "قطع غيار ناقصة", amber),
        ]
        for col, (key, title_text, dot_color) in enumerate(definitions):
            card = StatCard(title_text, "0", dot_color)
            self.cards[key] = card
            cards_layout.addWidget(card, 0, col)
            cards_layout.setColumnStretch(col, 1)
        main_column.addLayout(cards_layout)

        # ---------- Middle panels ----------
        middle = QGridLayout()
        middle.setSpacing(14)

        status_panel = MiniPanel("حالة الأجهزة")
        self.device_status_layout = QVBoxLayout()
        self.device_status_layout.setSpacing(10)
        status_panel.layout.addLayout(self.device_status_layout)
        status_panel.layout.addStretch(1)
        middle.addWidget(status_panel, 0, 0)

        fault_panel = MiniPanel("حالة الأعطال")
        self.fault_status_layout = QVBoxLayout()
        self.fault_status_layout.setSpacing(10)
        fault_panel.layout.addLayout(self.fault_status_layout)
        fault_panel.layout.addStretch(1)
        middle.addWidget(fault_panel, 0, 1)

        health_panel = MiniPanel("مؤشر التشغيل")
        health_panel.layout.addStretch(1)
        self.health_value = QLabel("0%")
        self.health_value.setObjectName("healthValue")
        self.health_value.setAlignment(Qt.AlignCenter)
        health_panel.layout.addWidget(self.health_value)

        self.health_bar = QProgressBar()
        self.health_bar.setRange(0, 100)
        self.health_bar.setTextVisible(False)
        self.health_bar.setFixedHeight(8)
        self.health_bar.setObjectName("healthBar")
        health_panel.layout.addWidget(self.health_bar)

        self.health_hint = QLabel("")
        self.health_hint.setObjectName("healthHint")
        self.health_hint.setAlignment(Qt.AlignCenter)
        self.health_hint.setWordWrap(True)
        health_panel.layout.addWidget(self.health_hint)
        health_panel.layout.addStretch(1)
        middle.addWidget(health_panel, 0, 2)

        for col in range(3):
            middle.setColumnStretch(col, 1)
        main_column.addLayout(middle)

        # ---------- Recent Faults ----------
        recent_panel = MiniPanel("آخر الأعطال المسجلة")
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(6)
        self.recent_table.setHorizontalHeaderLabels(
            ["رقم العطل", "التاريخ", "الجهاز", "المستخدم", "الحالة", "الأولوية"]
        )
        self.recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recent_table.setSelectionMode(QTableWidget.SingleSelection)
        self.recent_table.setShowGrid(False)
        self.recent_table.setFocusPolicy(Qt.NoFocus)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.verticalHeader().setDefaultSectionSize(40)
        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recent_table.horizontalHeader().setHighlightSections(False)
        self.recent_table.setMinimumHeight(240)
        recent_panel.layout.addWidget(self.recent_table)
        main_column.addWidget(recent_panel, 1)

        # ---------- Footer (الأسماء + آخر تحديث بخط صغير هادي) ----------
        footer = QHBoxLayout()
        credits = QLabel(
            "قائد شبكة الربط عميد أحمد صلاح   ·   المطورون  Ahmed Abozead · Hamdy Haggag"
        )
        credits.setObjectName("dashboardFooter")
        footer.addWidget(credits)
        footer.addStretch(1)
        self.footer = QLabel("آخر تحديث --")
        self.footer.setObjectName("dashboardFooter")
        footer.addWidget(self.footer)
        root.addLayout(footer)

        # ---------- Style ----------
        self.setStyleSheet("""
            #dashboardPage { background: #f6f8fb; }

            /* الهيدر */
            #greetingLabel { color: #0f2338; font-size: 22px; font-weight: 800; }
            #greetingHint { color: #64748b; font-size: 13px; font-weight: 500; }

            /* الساعة */
            #clockCard {
                background: #ffffff;
                border: 1px solid #e6ebf1;
                border-radius: 16px;
            }
            #clockTime { color: #0f2338; font-size: 26px; font-weight: 800; }
            #clockPeriod {
                background: #e6f5f7;
                color: #0e7490;
                border-radius: 6px;
                padding: 1px 7px;
                font-size: 12px;
                font-weight: 800;
            }
            #clockDate { color: #64748b; font-size: 12px; font-weight: 600; }

            /* الكروت واللوحات */
            #statCard, #dashboardPanel {
                background: #ffffff;
                border: 1px solid #e6ebf1;
                border-radius: 14px;
            }
            #cardTitle { color: #64748b; font-size: 13px; font-weight: 600; }
            #cardValue { color: #0f2338; font-size: 30px; font-weight: 800; }
            #cardValue[tone="warn"] { color: #b45309; }
            #panelTitle { color: #0f2338; font-size: 14px; font-weight: 800; }
            #healthValue { color: #0f2338; font-size: 40px; font-weight: 800; }
            #healthBar { border: none; background: #edf1f5; border-radius: 4px; }
            #healthBar::chunk { background: #0e9aaa; border-radius: 4px; }
            #healthHint { color: #64748b; font-size: 12px; padding-top: 4px; }

            /* الجدول */
            QTableWidget {
                background: transparent;
                border: none;
                color: #334155;
                font-size: 12px;
                selection-background-color: #eef6f8;
                selection-color: #0f2338;
            }
            QTableWidget::item { padding: 4px 6px; border-bottom: 1px solid #f0f3f7; }
            QHeaderView::section {
                background: transparent;
                color: #94a3b8;
                border: none;
                border-bottom: 1px solid #e6ebf1;
                padding: 8px 6px;
                font-size: 12px;
                font-weight: 700;
            }

            #dashboardFooter { color: #7b8a99; font-size: 11px; }

            /* مواقيت الصلاة */
            #prayerPanel {
                background: #ffffff;
                border: 1px solid #e6ebf1;
                border-radius: 14px;
            }
            #prayerPanelTitle { color: #0f2338; font-size: 14px; font-weight: 800; }
            #prayerToggle {
                background: #f1f6f8;
                color: #0e7490;
                border: 1px solid #e0eaee;
                border-radius: 10px;
                padding: 5px;
                font-size: 12px;
                font-weight: 800;
            }
            #prayerToggle:hover { background: #e3f0f3; }
            #prayerCity { color: #94a3b8; font-size: 11px; font-weight: 600; }
            #prayerStatus {
                background: #f7fafc;
                color: #64748b;
                border-radius: 10px;
                padding: 10px 8px;
                font-size: 12px;
                font-weight: 600;
            }
            #prayerNext {
                background: #eef8f6;
                border: 1px solid #d3ebe4;
                border-radius: 12px;
            }
            #prayerNextCaption { color: #5f8f86; font-size: 11px; font-weight: 700; }
            #prayerNextName { color: #0f5f52; font-size: 16px; font-weight: 800; }
            #prayerNextTime { color: #0f5f52; font-size: 16px; font-weight: 800; }
            #prayerNextRemaining { color: #5f8f86; font-size: 11px; font-weight: 600; }
            #prayerCountdown { color: #0f5f52; font-size: 20px; font-weight: 800; }
            #prayerCountdown[tone="soon"] { color: #b45309; }
            QWidget#prayerRow { background: transparent; border-radius: 9px; }
            QWidget#prayerRowNext { background: #f0f8f6; border-radius: 9px; }
            #prayerName { color: #475569; font-size: 12px; font-weight: 600; }
            #prayerTime { color: #0f2338; font-size: 12px; font-weight: 800; }
            #prayerMethod { color: #b0bcc8; font-size: 9px; padding-top: 4px; }
        """)

        self.update_greeting()

    # =============================================================
    # Clear Layout
    # =============================================================
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget:
                widget.deleteLater()
            elif child_layout:
                self._clear_layout(child_layout)

    # =============================================================
    # Status Row (الصفر يظهر بلون باهت عشان ما يشدش العين)
    # =============================================================
    def _add_status_row(self, layout, label, count, total):
        row = QHBoxLayout()
        row.setSpacing(10)
        name = QLabel(label)
        name.setMinimumWidth(110)
        name.setStyleSheet("color:#475569; font-size:12px; font-weight:600;")

        bar = QProgressBar()
        bar.setRange(0, max(total, 1))
        bar.setValue(count)
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        bar.setStyleSheet("""
            QProgressBar { border: none; background: #edf1f5; border-radius: 3px; }
            QProgressBar::chunk { background: #0e9aaa; border-radius: 3px; }
        """)

        number = QLabel(str(count))
        number.setAlignment(Qt.AlignCenter)
        number.setMinimumWidth(34)
        number_color = "#0f2338" if count else "#b0bcc8"
        number.setStyleSheet(f"color:{number_color}; font-size:12px; font-weight:800;")
        row.addWidget(name)
        row.addWidget(bar, 1)
        row.addWidget(number)
        layout.addLayout(row)

    # =============================================================
    # Refresh
    # =============================================================
    def refresh(self):
        self.update_greeting()
        connection = get_connection()
        cursor = connection.cursor()

        def count(query, params=()):
            cursor.execute(query, params)
            result = cursor.fetchone()
            return (result[0] or 0) if result else 0

        try:
            cursor.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN is_archived = 0 THEN 1 ELSE 0 END) AS active,
                    SUM(CASE WHEN is_archived = 1 THEN 1 ELSE 0 END) AS archived,
                    SUM(CASE WHEN is_archived IS NULL THEN 1 ELSE 0 END) AS null_archived
                FROM devices
            """)
            debug = cursor.fetchone()
            total_devices = debug["total"] or 0

            total_faults = count("SELECT COUNT(*) FROM faults")
            open_faults = count("""
                SELECT COUNT(*) FROM faults
                WHERE LTRIM(RTRIM(ISNULL(status, N'')))
                    NOT IN (N'تم الإصلاح', N'تم التسليم')
            """)
            total_buildings = count("""
                SELECT COUNT(DISTINCT building_id)
                FROM devices
                WHERE is_archived = 0 AND building_id IS NOT NULL
            """)
            missing_spare_parts = count("""
                SELECT COUNT(*) FROM spare_parts
                WHERE is_archived = 0 AND quantity < required_quantity
            """)

            # اللون الكهرماني يظهر فقط لما فيه شيء يحتاج انتباه
            self.cards["devices"].set_value(total_devices)
            self.cards["faults"].set_value(total_faults)
            self.cards["open"].set_value(open_faults, "warn" if open_faults else "")
            self.cards["buildings"].set_value(total_buildings)
            self.cards["spare_parts"].set_value(
                missing_spare_parts, "warn" if missing_spare_parts else ""
            )

            device_statuses = ["صالح", "يحتاج فحص", "عطل", "خارج الخدمة"]
            self._clear_layout(self.device_status_layout)
            for status in device_statuses:
                value = count("SELECT COUNT(*) FROM devices WHERE status = ?", (status,))
                self._add_status_row(self.device_status_layout, status, value, total_devices)

            fault_statuses = [
                "جديد", "قيد الفحص", "قيد الإصلاح", "بانتظار قطعة غيار",
                "تم الإصلاح", "تم التسليم",
            ]
            self._clear_layout(self.fault_status_layout)
            for status in fault_statuses:
                value = count("SELECT COUNT(*) FROM faults WHERE status = ?", (status,))
                self._add_status_row(self.fault_status_layout, status, value, total_faults)

            healthy = count("""
                SELECT COUNT(*) FROM devices
                WHERE is_archived = 0 AND LTRIM(RTRIM(status)) = N'صالح'
            """)
            active_devices = count("SELECT COUNT(*) FROM devices WHERE is_archived = 0")
            health = round((healthy / active_devices) * 100) if active_devices else 0
            self.health_value.setText(f"{health}%")
            self.health_bar.setValue(health)

            if health >= 90:
                hint = "ممتاز — أغلب الأجهزة تعمل بصورة طبيعية."
            elif health >= 70:
                hint = "جيد — توجد بعض الأجهزة التي تحتاج متابعة."
            elif active_devices:
                hint = "يحتاج متابعة — نسبة الأجهزة غير السليمة مرتفعة."
            else:
                hint = "لا توجد أجهزة نشطة حتى الآن."
            self.health_hint.setText(hint)

            cursor.execute("""
                SELECT TOP 10
                    faults.fault_number,
                    faults.entry_date,
                    devices.device_name,
                    faults.user_name,
                    faults.status,
                    faults.priority
                FROM faults
                LEFT JOIN devices ON faults.device_id = devices.id
                ORDER BY faults.id DESC
            """)
            recent = cursor.fetchall()
            self.recent_table.setRowCount(0)
            for fault in recent:
                row = self.recent_table.rowCount()
                self.recent_table.insertRow(row)
                status = str(fault["status"] or "").strip()
                priority = str(fault["priority"] or "").strip()
                values = [
                    fault["fault_number"] or "—",
                    format_entry_date(fault["entry_date"]),
                    fault["device_name"] or "—",
                    fault["user_name"] or "—",
                    status or "—",
                    priority or "—",
                ]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)

                    # الحالة والأولوية بلون هادي يدل على المعنى فقط
                    if col == 4:
                        if status in self.DONE_STATUSES:
                            item.setForeground(QColor("#15803d"))
                        elif status in self.WARN_STATUSES:
                            item.setForeground(QColor("#b45309"))
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                    elif col == 5:
                        if priority in self.HIGH_PRIORITIES:
                            item.setForeground(QColor("#b91c1c"))
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)
                        else:
                            item.setForeground(QColor("#94a3b8"))
                    elif value == "—":
                        item.setForeground(QColor("#c0cad4"))

                    self.recent_table.setItem(row, col, item)

            self.footer.setText(
                "آخر تحديث " + to_12h(datetime.now().strftime("%H:%M"))
            )
        finally:
            connection.close()

    # =============================================================
    # Show Event
    # =============================================================
    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()