"""
منطق جدول تبديل تكييفات السيرفر.

ملف "نقي": مفيهوش Qt ولا قاعدة بيانات، كل الدوال بتاخد الوقت (now) كمُدخل،
فسهل اختبارها (شوف test_ac_schedule.py) والحالة دايمًا بتتحسب من الوقت الحالي
+ السجل المحفوظ، مش من أي Timer.
"""
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from math import ceil

# =============================================================
# الإعدادات (عدّل من هنا)
# =============================================================
SCHEDULE_TIMES = (
    time(0, 0),    # 12:00 منتصف الليل
    time(8, 0),    # 08:00 صباحًا
    time(12, 0),   # 12:00 ظهرًا
    time(16, 0),   # 04:00 عصرًا
    time(20, 0),   # 08:00 مساءً
)

INFO_WINDOW_SECONDS = 60 * 60      # قبل الموعد بساعة: تنبيه
WARNING_WINDOW_SECONDS = 30 * 60   # قبل الموعد بنص ساعة: برتقالي
GRACE_MINUTES = 0                  # أي تأخير أكبر من كده = "متأخرة" ويحتاج سبب
OVERDUE_LOOKBACK_HOURS = 24        # التبديل غير المؤكد يفضل ظاهر كده، وبعدها يتسجل "missed"
MISSED_SWEEP_DAYS = 31             # أقصى رجوع لتسجيل المواعيد الفايتة
HISTORY_DAYS = 30

# الأدوار المسموح لها تأكيد التبديل (placeholder: اربطها بنظام الصلاحيات عندك)
AC_CONFIRM_ROLES = frozenset({"SUPER_ADMIN", "ADMIN", "SUB_ADMIN"})
AC_CONFIRM_PERMISSION = "ac_confirm"

# حالات السجل في قاعدة البيانات
STATUS_PENDING = "pending"      # (محجوزة - مش بتتخزن، المعلّق بيتحسب من الوقت)
STATUS_CONFIRMED = "confirmed"  # اتأكد في موعده
STATUS_LATE = "late"            # اتأكد متأخر (ومعاه سبب)
STATUS_MISSED = "missed"        # عدّى وقته ومحدش أكده

# مستويات التنبيه
LEVEL_NORMAL = "normal"
LEVEL_INFO = "info"
LEVEL_WARNING = "warning"
LEVEL_DUE = "due"

ARABIC_MONTHS = [
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
]


# =============================================================
# حساب المواعيد
# =============================================================
def slots_between(start, end):
    """كل المواعيد المجدولة داخل [start, end] مرتبة تصاعديًا."""
    if end < start:
        return []
    result = []
    day = start.date()
    while day <= end.date():
        for slot_time in SCHEDULE_TIMES:
            slot = datetime.combine(day, slot_time)
            if start <= slot <= end:
                result.append(slot)
        day += timedelta(days=1)
    return result


def next_slot(now):
    """أول موعد بعد الآن (الموعد اللي وقته جه بالظبط بيعتبر حان، مش قادم)."""
    for offset in (0, 1):
        day = now.date() + timedelta(days=offset)
        for slot_time in SCHEDULE_TIMES:
            slot = datetime.combine(day, slot_time)
            if slot > now:
                return slot
    raise RuntimeError("لا يوجد موعد قادم")  # لا يحدث عمليًا


def previous_slot(now):
    """آخر موعد حان (<= الآن)."""
    for offset in (0, -1):
        day = now.date() + timedelta(days=offset)
        for slot_time in reversed(SCHEDULE_TIMES):
            slot = datetime.combine(day, slot_time)
            if slot <= now:
                return slot
    raise RuntimeError("لا يوجد موعد سابق")


def outstanding_slots(now, resolved, tracking_start=None, lookback_hours=OVERDUE_LOOKBACK_HOURS):
    """المواعيد اللي حانت ولسه متأكدتش (الأقدم أولًا)، داخل فترة التتبع."""
    window_start = now - timedelta(hours=lookback_hours)
    if tracking_start is not None:
        window_start = max(window_start, tracking_start)
    return [slot for slot in slots_between(window_start, now) if slot not in resolved]


def slots_to_mark_missed(
    now,
    resolved,
    tracking_start,
    lookback_hours=OVERDUE_LOOKBACK_HOURS,
    sweep_days=MISSED_SWEEP_DAYS,
):
    """المواعيد الأقدم من فترة التنبيه وغير مسجلة: تتسجل 'missed' مرة واحدة."""
    if tracking_start is None:
        return []
    cutoff = now - timedelta(hours=lookback_hours)
    start = max(tracking_start, now - timedelta(days=sweep_days))
    return [slot for slot in slots_between(start, cutoff) if slot < cutoff and slot not in resolved]


# =============================================================
# التأخير والحالة
# =============================================================
def delay_minutes(scheduled, confirmed_at):
    """التأخير بالدقائق الكاملة (الصفر لو التأكيد في الموعد أو قبله)."""
    return max(0, int((confirmed_at - scheduled).total_seconds() // 60))


def status_for_delay(minutes):
    return STATUS_LATE if minutes > GRACE_MINUTES else STATUS_CONFIRMED


def classify_level(seconds_until):
    """لون/مستوى التنبيه حسب الوقت المتبقي للموعد."""
    if seconds_until > INFO_WINDOW_SECONDS:
        return LEVEL_NORMAL
    if seconds_until > WARNING_WINDOW_SECONDS:
        return LEVEL_INFO
    if seconds_until > 0:
        return LEVEL_WARNING
    return LEVEL_DUE


# =============================================================
# التنسيق بالعربي
# =============================================================
def format_time_ar(dt):
    hour = dt.hour % 12 or 12
    suffix = "ص" if dt.hour < 12 else "م"
    return f"{hour}:{dt.minute:02d} {suffix}"


def slot_label(slot, now):
    """'8:00 ص' / 'أمس 8:00 م' / 'غدًا 12:00 ص'."""
    text = format_time_ar(slot)
    diff = (slot.date() - now.date()).days
    if diff == 0:
        return text
    if diff == -1:
        return f"أمس {text}"
    if diff == 1:
        return f"غدًا {text}"
    return f"{slot.day}/{slot.month} {text}"


def format_datetime_ar(value, now=None):
    """'10 أكتوبر · 9:15 م' (والسنة لو مش السنة الحالية)."""
    if value is None:
        return "—"
    now = now or datetime.now()
    result = f"{value.day} {ARABIC_MONTHS[value.month - 1]}"
    if value.year != now.year:
        result += f" {value.year}"
    return f"{result} · {format_time_ar(value)}"


def _plural(n, one, two, few, many):
    if n == 1:
        return one
    if n == 2:
        return two
    if 3 <= n <= 10:
        return f"{n} {few}"
    return f"{n} {many}"


def format_duration_ar(total_minutes):
    """90 -> 'ساعة و 30 دقيقة' ، 25 -> '25 دقيقة' ، 120 -> 'ساعتان'."""
    total = max(0, int(total_minutes))
    hours, minutes = divmod(total, 60)
    parts = []
    if hours:
        parts.append(_plural(hours, "ساعة", "ساعتان", "ساعات", "ساعة"))
    if minutes:
        parts.append(_plural(minutes, "دقيقة", "دقيقتان", "دقائق", "دقيقة"))
    return " و ".join(parts) if parts else "أقل من دقيقة"


def format_hms(seconds):
    total = int(ceil(max(0.0, seconds)))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# =============================================================
# حالة التنبيه (كل اللي الواجهة محتاجاه جاهز كنصوص)
# =============================================================
@dataclass(frozen=True)
class AlertState:
    level: str
    primary_slot: datetime      # الموعد المعروض في البطاقة (متأخر الأقدم، أو القادم)
    is_due: bool                # الموعد الأساسي حان أو فات => يظهر زر التأكيد
    message: str
    countdown_caption: str      # 'متبقي' / 'متأخر منذ' / ''
    countdown_value: str        # '00:45:20' / '25 دقيقة' / 'موعد التبديل الآن'
    detail: str                 # سطر ثانوي (تبديلات متأخرة أخرى / القادم)
    outstanding: tuple          # كل المواعيد المتأخرة غير المؤكدة (الأقدم أولًا)
    next_slot: datetime


def build_alert_state(now, resolved, tracking_start=None, lookback_hours=OVERDUE_LOOKBACK_HOURS):
    """
    resolved: مجموعة المواعيد اللي ليها سجل في قاعدة البيانات (مؤكدة أو missed).
    الدالة نقية: نفس المُدخلات = نفس النتيجة، فالحالة صحيحة حتى بعد إعادة تشغيل البرنامج.
    """
    upcoming = next_slot(now)
    until_next = (upcoming - now).total_seconds()
    outstanding = tuple(outstanding_slots(now, resolved, tracking_start, lookback_hours))

    if outstanding:
        primary = outstanding[0]
        late_seconds = (now - primary).total_seconds()
        if late_seconds < 60:
            message = "حان موعد تبديل التكييف"
            caption, value = "", "موعد التبديل الآن"
        else:
            message = f"تبديل التكييف المجدول {slot_label(primary, now)} لم يتم تأكيده"
            caption = "متأخر منذ"
            value = format_duration_ar(int(late_seconds // 60))

        details = []
        if len(outstanding) > 1:
            details.append(f"تبديلات متأخرة أخرى غير مؤكدة: {len(outstanding) - 1}")
        if until_next <= INFO_WINDOW_SECONDS:
            details.append(
                f"التبديل القادم {slot_label(upcoming, now)} — متبقي "
                f"{format_duration_ar(ceil(until_next / 60))}"
            )
        return AlertState(
            level=LEVEL_DUE,
            primary_slot=primary,
            is_due=True,
            message=message,
            countdown_caption=caption,
            countdown_value=value,
            detail=" · ".join(details),
            outstanding=outstanding,
            next_slot=upcoming,
        )

    level = classify_level(until_next)
    if level == LEVEL_NORMAL:
        message = f"التبديل القادم: {slot_label(upcoming, now)}"
    else:
        message = f"متبقي {format_duration_ar(ceil(until_next / 60))} على تبديل التكييف"
    return AlertState(
        level=level,
        primary_slot=upcoming,
        is_due=False,
        message=message,
        countdown_caption="متبقي",
        countdown_value=format_hms(until_next),
        detail="",
        outstanding=(),
        next_slot=upcoming,
    )


# =============================================================
# الصلاحيات واسم المستخدم (من المستخدم الحالي في الداشبورد، بدون تغيير منطق الصلاحيات)
# =============================================================
def can_confirm_ac_change(user):
    user = user or {}
    permissions = user.get("permissions")
    if permissions and AC_CONFIRM_PERMISSION in permissions:
        return True
    role_code = str(user.get("role_code", "") or "").strip().upper()
    return role_code in AC_CONFIRM_ROLES


def actor_name(user):
    user = user or {}
    for key in ("full_name", "display_name", "name", "username"):
        value = str(user.get(key, "") or "").strip()
        if value:
            return value
    return "غير معروف"


# =============================================================
# السجل التاريخي
# =============================================================
HISTORY_ON_TIME = "on_time"
HISTORY_LATE = "late"
HISTORY_UNCONFIRMED = "unconfirmed"
HISTORY_LABELS_AR = {
    HISTORY_ON_TIME: "في موعدها",
    HISTORY_LATE: "متأخرة",
    HISTORY_UNCONFIRMED: "غير مؤكدة",
}


def history_rows(now, records, tracking_start=None, days=HISTORY_DAYS):
    """
    records: {scheduled_datetime: {confirmed_at, confirmed_by, status, delay_minutes, delay_reason}}
    بترجّع صف لكل موعد (الأحدث أولًا): اللي ملوش سجل = غير مؤكدة.
    """
    start = now - timedelta(days=days)
    if tracking_start is not None:
        start = max(start, tracking_start)

    rows = []
    for slot in reversed(slots_between(start, now)):
        record = records.get(slot)
        if record is None:
            key = HISTORY_UNCONFIRMED
        elif record.get("status") == STATUS_CONFIRMED:
            key = HISTORY_ON_TIME
        elif record.get("status") == STATUS_LATE:
            key = HISTORY_LATE
        else:
            key = HISTORY_UNCONFIRMED

        record = record or {}
        rows.append(
            {
                "scheduled": slot,
                "confirmed_at": record.get("confirmed_at"),
                "confirmed_by": record.get("confirmed_by") or "",
                "status_key": key,
                "status_label": HISTORY_LABELS_AR[key],
                "delay_minutes": record.get("delay_minutes") or 0,
                "delay_reason": record.get("delay_reason") or "",
            }
        )
    return rows


def compliance_summary(rows):
    total = len(rows)
    on_time = sum(1 for r in rows if r["status_key"] == HISTORY_ON_TIME)
    late = sum(1 for r in rows if r["status_key"] == HISTORY_LATE)
    unconfirmed = sum(1 for r in rows if r["status_key"] == HISTORY_UNCONFIRMED)
    percent = round(on_time / total * 100) if total else None
    return {
        "total": total,
        "on_time": on_time,
        "late": late,
        "unconfirmed": unconfirmed,
        "on_time_percent": percent,
    }