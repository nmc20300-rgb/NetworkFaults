"""
طبقة قاعدة البيانات لتبديل التكييفات (SQL Server / pyodbc).
كل الدوال بتاخد connection جاهز (من database.get_connection) وبتعمل commit بنفسها.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta

from . import ac_schedule as sched

TABLE = "dbo.air_conditioner_changes"
SETTINGS_TABLE = "dbo.air_conditioner_settings"
TRACKING_KEY = "ac_tracking_started_at"

RESULT_OK = "ok"
RESULT_ALREADY = "already"  # مستخدم تاني أكده قبلك

_SCHEMA_SQL = """
IF OBJECT_ID(N'dbo.air_conditioner_changes', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.air_conditioner_changes (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        scheduled_time  DATETIME      NOT NULL,
        confirmed_at    DATETIME      NULL,
        confirmed_by    NVARCHAR(150) NULL,
        status          NVARCHAR(20)  NOT NULL,
        delay_minutes   INT           NOT NULL CONSTRAINT DF_ac_changes_delay DEFAULT 0,
        delay_reason    NVARCHAR(500) NULL,
        created_at      DATETIME      NOT NULL CONSTRAINT DF_ac_changes_created DEFAULT GETDATE(),
        CONSTRAINT UQ_ac_changes_scheduled UNIQUE (scheduled_time),
        CONSTRAINT CK_ac_changes_status
            CHECK (status IN (N'pending', N'confirmed', N'late', N'missed'))
    );
END;
IF OBJECT_ID(N'dbo.air_conditioner_settings', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.air_conditioner_settings (
        setting_key   NVARCHAR(60)  NOT NULL PRIMARY KEY,
        setting_value NVARCHAR(200) NULL
    );
END;
"""

_schema_ready = False


@dataclass
class Snapshot:
    tracking_start: datetime
    records: dict            # {scheduled_datetime: {...}}
    last_confirmation: dict  # أو None


def ensure_schema(conn):
    """ينشئ الجدولين لو مش موجودين (مرة واحدة في كل تشغيل)."""
    global _schema_ready
    if _schema_ready:
        return
    cursor = conn.cursor()
    cursor.execute(_SCHEMA_SQL)
    conn.commit()
    _schema_ready = True


def _record_from_row(row):
    return {
        "scheduled": row[0],
        "confirmed_at": row[1],
        "confirmed_by": row[2],
        "status": row[3],
        "delay_minutes": row[4] or 0,
        "delay_reason": row[5],
    }


def get_tracking_start(conn, now):
    """بداية تتبع الجدول (بتتسجل أول مرة بس) عشان مفيش تنبيهات لمواعيد قبل تشغيل الميزة."""
    cursor = conn.cursor()
    select_sql = f"SELECT setting_value FROM {SETTINGS_TABLE} WHERE setting_key = ?"
    cursor.execute(select_sql, (TRACKING_KEY,))
    row = cursor.fetchone()
    if row and row[0]:
        return datetime.fromisoformat(str(row[0]))

    started = now.replace(microsecond=0)
    try:
        cursor.execute(
            f"INSERT INTO {SETTINGS_TABLE} (setting_key, setting_value) VALUES (?, ?)",
            (TRACKING_KEY, started.isoformat(sep=" ")),
        )
        conn.commit()
    except Exception:
        conn.rollback()  # جهاز تاني سبقنا: نقرأ القيمة اللي اتسجلت
        cursor.execute(select_sql, (TRACKING_KEY,))
        row = cursor.fetchone()
        if not row or not row[0]:
            raise
        return datetime.fromisoformat(str(row[0]))
    return started


def fetch_records(conn, start, end):
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT scheduled_time, confirmed_at, confirmed_by, status, delay_minutes, delay_reason
        FROM {TABLE}
        WHERE scheduled_time >= ? AND scheduled_time <= ?
        """,
        (start, end),
    )
    records = {}
    for row in cursor.fetchall():
        record = _record_from_row(row)
        records[record["scheduled"]] = record
    return records


def fetch_last_confirmation(conn):
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT TOP 1 scheduled_time, confirmed_at, confirmed_by, status, delay_minutes, delay_reason
        FROM {TABLE}
        WHERE confirmed_at IS NOT NULL
        ORDER BY confirmed_at DESC
        """
    )
    row = cursor.fetchone()
    return _record_from_row(row) if row else None


def mark_missed(conn, slots):
    """يسجّل المواعيد الفايتة (أقدم من فترة التنبيه) كـ missed مرة واحدة، بدون تكرار."""
    if not slots:
        return
    cursor = conn.cursor()
    try:
        for slot in slots:
            cursor.execute(
                f"""
                INSERT INTO {TABLE} (scheduled_time, confirmed_at, confirmed_by, status, delay_minutes, delay_reason)
                SELECT ?, NULL, NULL, N'missed', 0, NULL
                WHERE NOT EXISTS (SELECT 1 FROM {TABLE} WHERE scheduled_time = ?)
                """,
                (slot, slot),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def load_snapshot(conn, now):
    """كل اللي الكارت محتاجه من قاعدة البيانات في قراءة واحدة."""
    ensure_schema(conn)
    tracking_start = get_tracking_start(conn, now)
    records = fetch_records(conn, now - timedelta(days=sched.MISSED_SWEEP_DAYS), now)

    missed = sched.slots_to_mark_missed(now, set(records), tracking_start)
    if missed:
        mark_missed(conn, missed)
        records = fetch_records(conn, now - timedelta(days=sched.MISSED_SWEEP_DAYS), now)

    return Snapshot(
        tracking_start=tracking_start,
        records=records,
        last_confirmation=fetch_last_confirmation(conn),
    )


def confirm_change(conn, scheduled, confirmed_at, confirmed_by, delay_reason=None):
    """
    يسجّل تأكيد التبديل. الاختفاء من الواجهة مشروط بنجاح التسجيل فعليًا:
    بعد الـ INSERT بنقرا الصف من القاعدة ونتأكد إنه اتسجل باسم المستخدم ده.
    بيرجّع RESULT_OK أو RESULT_ALREADY، وأي فشل تاني بيرفع Exception.
    """
    ensure_schema(conn)
    confirmed_at = confirmed_at.replace(microsecond=0)
    minutes = sched.delay_minutes(scheduled, confirmed_at)
    reason = (delay_reason or "").strip()
    if minutes > sched.GRACE_MINUTES and not reason:
        raise ValueError("سبب التأخير مطلوب")
    status = sched.status_for_delay(minutes)
    reason_value = reason[:500] if minutes > sched.GRACE_MINUTES else None

    cursor = conn.cursor()
    try:
        cursor.execute(
            f"""
            INSERT INTO {TABLE} (scheduled_time, confirmed_at, confirmed_by, status, delay_minutes, delay_reason)
            SELECT ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM {TABLE} WHERE scheduled_time = ?)
            """,
            (scheduled, confirmed_at, confirmed_by, status, minutes, reason_value, scheduled),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    cursor.execute(
        f"SELECT confirmed_by, confirmed_at FROM {TABLE} WHERE scheduled_time = ?",
        (scheduled,),
    )
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError("لم يتم حفظ التأكيد في قاعدة البيانات")

    saved_by, saved_at = row[0], row[1]
    if (
        saved_by == confirmed_by
        and saved_at is not None
        and abs((saved_at - confirmed_at).total_seconds()) < 2
    ):
        return RESULT_OK
    return RESULT_ALREADY