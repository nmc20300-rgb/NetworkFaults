"""
رسوم بيانية خفيفة لداشبورد "الشبكة" - PySide6 فقط (بدون QtCharts أو مكتبات خارجية).

مبادئ الأداء:
- كل رسم هو QWidget يرسم نفسه بـ QPainter (بدون عناصر فرعية كتير).
- أنيميشن واحد قصير (420ms) لكل رسم، ويشتغل فقط لما الرقم يتغير فعلًا.
- لو البيانات ما اتغيرتش (تحديث كل 5 ثواني) مفيش إعادة رسم ولا أنيميشن.
- أول ظهور للصفحة: دخول هادي (الرسم بيتملّي من الصفر)، بعد كده انتقال ناعم من القيمة القديمة للجديدة.
"""
import math
from datetime import date, datetime, timedelta

from PySide6.QtCore import QEasingCurve, QRectF, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

ANIM_MS = 420

TRACK = QColor("#edf1f5")
GRID = QColor("#eef2f6")
TEXT_DARK = QColor("#0f2338")
TEXT_MUTED = QColor("#64748b")
TEXT_FAINT = QColor("#b0bcc8")

TEAL = "#0e9aaa"
TEAL_SOFT = "#bfe3e8"
AMBER = "#d97706"
RED = "#dc2626"

ABS_R = Qt.AlignRight | Qt.AlignAbsolute | Qt.AlignVCenter
ABS_L = Qt.AlignLeft | Qt.AlignAbsolute | Qt.AlignVCenter


# =============================================================
# أساس مشترك: انتقال ناعم من القيم القديمة للجديدة
# =============================================================
class _AnimatedChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LeftToRight)  # الرسم نفسه بنتحكم فيه يدويًا
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._from = []
        self._target = []
        self._t = 1.0
        self._played = False

        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(ANIM_MS)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._on_tick)

    def _on_tick(self, value):
        self._t = float(value)
        self.update()

    def _current(self):
        return [a + (b - a) * self._t for a, b in zip(self._from, self._target)]

    def _set_target(self, values):
        values = [float(v) for v in values]
        if values == self._target:
            return False

        if len(self._target) == len(values):
            previous = self._current()
        else:
            previous = [0.0] * len(values)

        self._anim.stop()
        self._from = previous
        self._target = values

        if self.isVisible():
            self._played = True
            self._t = 0.0
            self._anim.start()
        else:
            self._t = 1.0  # الصفحة لسه ما ظهرتش: هنعمل الدخول في showEvent
        self.update()
        return True

    def showEvent(self, event):
        super().showEvent(event)
        if not self._played and self._target:
            self._played = True
            self._from = [0.0] * len(self._target)
            self._t = 0.0
            self._anim.start()

    def _begin(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        return painter

    @staticmethod
    def _font(painter, pixel_size, bold=False):
        font = painter.font()
        font.setPixelSize(int(pixel_size))
        font.setBold(bold)
        painter.setFont(font)


# =============================================================
# دونات (توزيع حالات الأجهزة) + شرح الألوان على الجنب
# =============================================================
class DonutChart(_AnimatedChart):
    def __init__(self, caption="جهاز", parent=None):
        super().__init__(parent)
        self._caption = caption
        self._center_text = None  # لو متحدد بيظهر بدل إجمالي الأعداد
        self._items = []  # [(label, color)]
        self.setMinimumHeight(180)

    def set_data(self, items):
        """items: [(label, value, color_hex)]"""
        self._items = [(label, color) for label, _, color in items]
        self._set_target([value for _, value, _ in items])
        self.update()

    def set_center(self, text, caption=None):
        """نص مخصص في منتصف الدونات (مثلًا نسبة التشغيل 100%)."""
        self._center_text = text
        if caption is not None:
            self._caption = caption
        self.update()

    def paintEvent(self, event):
        painter = self._begin()
        w, h = self.width(), self.height()
        side = max(60, min(h - 8, w * 0.5))
        thick = max(10.0, side * 0.15)
        rect = QRectF(4 + thick / 2, (h - side) / 2 + thick / 2, side - thick, side - thick)

        values = self._current()
        denom = max(sum(self._target), 1.0)

        # المسار الرمادي
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(TRACK, thick))
        painter.drawEllipse(rect)

        # الشرائح (تبدأ من فوق وتمشي مع عقارب الساعة)
        start = 90 * 16
        for (label, color), value in zip(self._items, values):
            span = -int(round(value / denom * 360 * 16))
            if span == 0:
                continue
            gap = 24 if abs(span) > 48 else 0
            painter.setPen(QPen(QColor(color), thick, Qt.SolidLine, Qt.FlatCap))
            painter.drawArc(rect, start - gap // 2, span + gap)
            start += span

        # الرقم في المنتصف
        total = int(round(sum(values)))
        center = self._center_text if self._center_text is not None else str(total)
        self._font(painter, side * 0.15, True)
        painter.setPen(TEXT_DARK)
        painter.drawText(
            QRectF(rect.x(), rect.y() + rect.height() * 0.22, rect.width(), rect.height() * 0.32),
            Qt.AlignCenter,
            center,
        )
        self._font(painter, 13, False)
        painter.setPen(TEXT_MUTED)
        painter.drawText(
            QRectF(rect.x(), rect.y() + rect.height() * 0.52, rect.width(), rect.height() * 0.2),
            Qt.AlignCenter,
            self._caption,
        )

        # شرح الألوان (يمين) والأرقام (شمال)
        n = max(len(self._items), 1)
        row_h = min(30.0, (h - 8) / n)
        y0 = (h - row_h * n) / 2
        legend_left = side + 24
        legend_right = w - 6
        for i, ((label, color), value) in enumerate(zip(self._items, values)):
            y = y0 + i * row_h
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(color))
            painter.drawEllipse(QRectF(legend_right - 8, y + row_h / 2 - 4, 8, 8))

            self._font(painter, 12, False)
            painter.setPen(TEXT_MUTED)
            painter.drawText(
                QRectF(legend_left + 40, y, max(0.0, legend_right - 16 - (legend_left + 40)), row_h),
                ABS_R,
                label,
            )

            count = int(round(value))
            self._font(painter, 12, True)
            painter.setPen(TEXT_DARK if count else TEXT_FAINT)
            painter.drawText(QRectF(legend_left, y, 38, row_h), ABS_L, str(count))
        painter.end()


# =============================================================
# أعمدة أفقية (حالات الأعطال) - تمتلئ من اليمين
# =============================================================
class HBarChart(_AnimatedChart):
    ROW_H = 31

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []  # [(label, color)]
        self._total = 1.0

    def set_data(self, items, total=None):
        """items: [(label, value, color_hex)]"""
        self._rows = [(label, color) for label, _, color in items]
        values = [value for _, value, _ in items]
        self._total = float(max(total if total is not None else sum(values), 1))
        self.setMinimumHeight(len(items) * self.ROW_H)
        self._set_target(values)
        self.update()

    def paintEvent(self, event):
        painter = self._begin()
        w, h = self.width(), self.height()
        n = max(len(self._rows), 1)
        row_h = min(34.0, h / n)
        y0 = (h - row_h * n) / 2

        name_w, num_w = 120.0, 36.0
        bar_left = num_w + 8
        bar_right = w - name_w - 8
        bar_w = max(10.0, bar_right - bar_left)
        bar_h = 6.0

        for i, ((label, color), value) in enumerate(zip(self._rows, self._current())):
            y = y0 + i * row_h
            cy = y + row_h / 2

            self._font(painter, 12, False)
            painter.setPen(TEXT_MUTED)
            painter.drawText(QRectF(w - name_w, y, name_w, row_h), ABS_R, label)

            painter.setPen(Qt.NoPen)
            painter.setBrush(TRACK)
            painter.drawRoundedRect(QRectF(bar_left, cy - bar_h / 2, bar_w, bar_h), 3, 3)

            fill = bar_w * (value / self._total)
            if value > 0.05:
                fill = max(fill, 5.0)
                painter.setBrush(QColor(color))
                painter.drawRoundedRect(
                    QRectF(bar_right - fill, cy - bar_h / 2, fill, bar_h), 3, 3
                )

            count = int(round(value))
            self._font(painter, 12, True)
            painter.setPen(TEXT_DARK if count else TEXT_FAINT)
            painter.drawText(QRectF(0, y, num_w, row_h), ABS_L, str(count))
        painter.end()


# =============================================================
# أعمدة رأسية (الأعطال آخر 7 أيام) - الأقدم يمين واليوم شمال
# =============================================================
class TrendChart(_AnimatedChart):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._labels = []
        self.setMinimumHeight(180)

    def set_data(self, items):
        """items: [(label, value)] مرتبة من الأقدم لليوم"""
        self._labels = [label for label, _ in items]
        self._set_target([value for _, value in items])
        self.update()

    def paintEvent(self, event):
        painter = self._begin()
        w, h = self.width(), self.height()
        n = len(self._labels)
        if not n:
            painter.end()
            return

        pad = 8.0
        top, bottom = 20.0, 24.0
        plot_h = max(10.0, h - top - bottom)
        base_y = top + plot_h

        peak = max(max(self._target), 1.0)
        scale_max = max(4.0, math.ceil(peak / 2.0) * 2.0)

        # خطوط شبكة هادية
        painter.setPen(QPen(GRID, 1))
        for frac in (0.0, 0.5, 1.0):
            y = base_y - plot_h * frac
            painter.drawLine(int(pad), int(y), int(w - pad), int(y))

        slot = (w - 2 * pad) / n
        bar_w = min(40.0, slot * 0.5)
        for i, (label, value) in enumerate(zip(self._labels, self._current())):
            is_today = i == n - 1
            # الترتيب معكوس: i=0 هو الأقدم ويظهر في أقصى اليمين، واليوم في الشمال
            cx = w - pad - slot * (i + 0.5)
            bar_h = plot_h * (value / scale_max)

            painter.setPen(Qt.NoPen)
            if bar_h >= 2:
                painter.setBrush(QColor(TEAL if is_today else TEAL_SOFT))
                painter.drawRoundedRect(QRectF(cx - bar_w / 2, base_y - bar_h, bar_w, bar_h), 5, 5)
            else:
                painter.setBrush(TRACK)
                painter.drawRoundedRect(QRectF(cx - bar_w / 2, base_y - 3, bar_w, 3), 1.5, 1.5)

            count = int(round(value))
            if count > 0:
                self._font(painter, 11, True)
                painter.setPen(TEXT_DARK if is_today else TEXT_MUTED)
                painter.drawText(
                    QRectF(cx - slot / 2, base_y - bar_h - 18, slot, 16), Qt.AlignCenter, str(count)
                )

            self._font(painter, 11, is_today)
            painter.setPen(TEXT_DARK if is_today else TEXT_MUTED)
            painter.drawText(QRectF(cx - slot / 2, base_y + 4, slot, 18), Qt.AlignCenter, label)
        painter.end()


# =============================================================
# مؤشر التشغيل: حلقة نسبة مئوية (اللون حسب الحالة)
# =============================================================
class GaugeChart(_AnimatedChart):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)

    def set_value(self, percent):
        self._set_target([max(0.0, min(100.0, float(percent)))])

    @staticmethod
    def _color_for(percent):
        if percent >= 90:
            return TEAL
        if percent >= 70:
            return AMBER
        return RED

    def paintEvent(self, event):
        painter = self._begin()
        w, h = self.width(), self.height()
        side = max(60.0, min(w, h) - 8)
        thick = max(9.0, side * 0.11)
        rect = QRectF((w - side) / 2 + thick / 2, (h - side) / 2 + thick / 2, side - thick, side - thick)

        current = self._current()
        value = current[0] if current else 0.0
        target = self._target[0] if self._target else 0.0

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(TRACK, thick))
        painter.drawEllipse(rect)

        if value > 0.2:
            painter.setPen(QPen(QColor(self._color_for(target)), thick, Qt.SolidLine, Qt.RoundCap))
            painter.drawArc(rect, 90 * 16, -int(round(value / 100.0 * 360 * 16)))

        self._font(painter, side * 0.24, True)
        painter.setPen(TEXT_DARK)
        painter.drawText(rect, Qt.AlignCenter, f"{int(round(value))}%")
        painter.end()


# =============================================================
# مساعد: عدد الأعطال في كل يوم (آخر N يوم) من قيم entry_date
# =============================================================
_DATE_FORMATS = (
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%H:%M:%S %Y-%m-%d",
    "%H:%M %Y-%m-%d",
    "%Y-%m-%d",
)


def _to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def faults_per_day(raw_dates, days=7):
    """يرجّع [(date, count)] مرتبة من الأقدم لليوم الحالي."""
    today = date.today()
    counts = {today - timedelta(days=i): 0 for i in range(days)}
    for raw in raw_dates:
        day = _to_date(raw)
        if day in counts:
            counts[day] += 1
    return [(day, counts[day]) for day in sorted(counts)]