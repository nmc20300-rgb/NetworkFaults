import pyodbc
import socket
import csv
from datetime import date, datetime, time
from pathlib import Path


# =========================================================
# SQL Server Settings
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

SQL_SERVER = "localhost"
SQL_DATABASE = "NetworkFaults"
SQL_DRIVER = "ODBC Driver 18 for SQL Server"


CONNECTION_STRING = (
    f"DRIVER={{{SQL_DRIVER}}};"
    f"SERVER={SQL_SERVER};"
    f"DATABASE={SQL_DATABASE};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)


# =========================================================
# SQL Server Row
# =========================================================

class SQLServerRow:

    def __init__(self, columns, values):

        self._columns = columns
        self._values = tuple(values)

        self._index = {
            column.lower(): i
            for i, column in enumerate(columns)
        }

    def __getitem__(self, key):

        if isinstance(key, int):
            return self._values[key]

        index = self._index.get(
            str(key).lower()
        )

        if index is None:
            raise KeyError(key)

        return self._values[index]

    def keys(self):
        return self._columns

    def values(self):
        return self._values

    def items(self):

        return [
            (
                column,
                self._values[i]
            )
            for i, column in enumerate(
                self._columns
            )
        ]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)


# =========================================================
# SQL Server Cursor
# =========================================================

class SQLServerCursor:

    def __init__(self, cursor):

        self._cursor = cursor
        self.description = None
        self.lastrowid = None

    def execute(
        self,
        sql,
        params=()
    ):

        if params is None:
            params = ()

        self._cursor.execute(
            sql,
            params
        )

        self.description = (
            self._cursor.description
        )

        return self

    def executemany(
        self,
        sql,
        seq_of_params
    ):

        self._cursor.executemany(
            sql,
            seq_of_params
        )

        self.description = (
            self._cursor.description
        )

        return self

    def fetchone(self):

        row = self._cursor.fetchone()

        if row is None:
            return None

        return self._convert_row(
            row
        )

    def fetchall(self):

        rows = self._cursor.fetchall()

        return [
            self._convert_row(row)
            for row in rows
        ]

    def fetchmany(
        self,
        size=None
    ):

        if size is None:
            rows = self._cursor.fetchmany()

        else:
            rows = self._cursor.fetchmany(
                size
            )

        return [
            self._convert_row(row)
            for row in rows
        ]

    def _convert_row(
        self,
        row
    ):

        if not self.description:
            return row

        columns = [
            column[0]
            for column in self.description
        ]

        return SQLServerRow(
            columns,
            row
        )

    def close(self):

        self._cursor.close()

    @property
    def rowcount(self):

        return self._cursor.rowcount


# =========================================================
# SQL Server Connection
# =========================================================

class SQLServerConnection:

    def __init__(
        self,
        connection
    ):

        self._connection = connection

    def cursor(self):

        return SQLServerCursor(
            self._connection.cursor()
        )

    def execute(
        self,
        sql,
        params=()
    ):

        cursor = self.cursor()

        cursor.execute(
            sql,
            params
        )

        return cursor

    def commit(self):

        self._connection.commit()

    def rollback(self):

        self._connection.rollback()

    def close(self):

        self._connection.close()

    def __enter__(self):

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):

        if exc_type is None:
            self.commit()

        else:
            self.rollback()

        self.close()


# =========================================================
# Database Connection
# =========================================================

def get_connection():

    connection = pyodbc.connect(
        CONNECTION_STRING
    )

    return SQLServerConnection(
        connection
    )


# =========================================================
# AUDIT LOG
# =========================================================

def write_audit_log(
    user=None,
    action="",
    module_name="",
    record_id=None,
    description="",
    old_values=None,
    new_values=None,
    computer_name=None,
    ip_address=None,
):
    """
    تسجيل عملية داخل جدول audit_logs.

    user:
        Dictionary المستخدم الحالي.

    action:
        العملية مثل:
        إضافة / تعديل / حذف / دخول / خروج

    module_name:
        القسم مثل:
        الأجهزة / الأعطال / قطع الغيار / المستخدمين

    record_id:
        رقم السجل المتأثر.

    description:
        وصف مختصر للعملية.

    old_values:
        القيم القديمة - اختياري.

    new_values:
        القيم الجديدة - اختياري.
    """

    connection = None
    cursor = None

    try:

        # ---------------------------------------------
        # User
        # ---------------------------------------------

        user = user or {}

        user_id = user.get(
            "id"
        )

        username = (
            user.get("username")
            or user.get("full_name")
            or "SYSTEM"
        )

        # ---------------------------------------------
        # Computer
        # ---------------------------------------------

        if not computer_name:

            try:
                computer_name = socket.gethostname()

            except Exception:
                computer_name = None

        # ---------------------------------------------
        # IP
        # ---------------------------------------------

        if not ip_address:

            try:

                ip_address = socket.gethostbyname(
                    socket.gethostname()
                )

            except Exception:

                ip_address = None

        # ---------------------------------------------
        # Convert values to text
        # ---------------------------------------------

        if old_values is not None:

            if not isinstance(
                old_values,
                str
            ):

                old_values = str(
                    old_values
                )

        if new_values is not None:

            if not isinstance(
                new_values,
                str
            ):

                new_values = str(
                    new_values
                )

        # ---------------------------------------------
        # Connection
        # ---------------------------------------------

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO dbo.audit_logs
            (
                user_id,
                username,
                action,
                module_name,
                record_id,
                description,
                old_values,
                new_values,
                computer_name,
                ip_address,
                created_at
            )
            VALUES
            (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                SYSDATETIME()
            )
            """,
            (
                user_id,
                username,
                action,
                module_name,
                record_id,
                description,
                old_values,
                new_values,
                computer_name,
                ip_address,
            )
        )

        connection.commit()

        return True

    except Exception as e:

        # مهم:
        # فشل تسجيل الـ Log لا يوقف البرنامج
        print(
            "AUDIT LOG ERROR:",
            type(e).__name__,
            ":",
            e
        )

        return False

    finally:

        try:

            if cursor:
                cursor.close()

        except Exception:
            pass

        try:

            if connection:
                connection.close()

        except Exception:
            pass


# =========================================================
# Prayer Times (local SQL Server table)
# =========================================================

PRAYER_TIMES_TABLE = "dbo.PrayerTimes"


def ensure_prayer_times_table(connection=None):
    """Create the local prayer-times table if it does not already exist."""
    owns_connection = connection is None
    if owns_connection:
        connection = get_connection()

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("""
            IF OBJECT_ID(N'dbo.PrayerTimes', N'U') IS NULL
            BEGIN
                CREATE TABLE dbo.PrayerTimes (
                    PrayerDate DATE NOT NULL PRIMARY KEY,
                    Fajr TIME(0) NOT NULL,
                    Sunrise TIME(0) NOT NULL,
                    Dhuhr TIME(0) NOT NULL,
                    Asr TIME(0) NOT NULL,
                    Maghrib TIME(0) NOT NULL,
                    Isha TIME(0) NOT NULL,
                    DataSource NVARCHAR(250) NOT NULL,
                    TimeZone NVARCHAR(50) NOT NULL
                );
            END
        """)
        if owns_connection:
            connection.commit()
    except Exception:
        if owns_connection:
            connection.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if owns_connection and connection:
            connection.close()


def import_prayer_times_csv(csv_path, replace_existing=False):
    """Import the supplied prayer-times CSV into dbo.PrayerTimes.

    By default, refuses to import if records already exist, preventing an
    accidental duplicate import. Set replace_existing=True only when you
    explicitly intend to clear and replace the table contents.
    """
    required_columns = {
        "date", "fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha",
        "source", "timezone",
    }

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        actual_columns = set(reader.fieldnames or [])
        missing = required_columns - actual_columns
        if missing:
            raise ValueError(
                "CSV is missing required columns: " + ", ".join(sorted(missing))
            )

        rows = []
        for line_number, row in enumerate(reader, start=2):
            try:
                prayer_date = date.fromisoformat(row["date"].strip())
                parsed_times = [
                    time.fromisoformat(row[key].strip()).replace(second=0, microsecond=0)
                    for key in ("fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha")
                ]
                timezone_name = row["timezone"].strip()
                data_source = row["source"].strip()
                if not timezone_name or not data_source:
                    raise ValueError("source/timezone cannot be empty")
                rows.append((prayer_date, *parsed_times, data_source, timezone_name))
            except Exception as exc:
                raise ValueError(f"Invalid CSV data at line {line_number}: {exc}") from exc

    if not rows:
        raise ValueError("CSV contains no prayer-time rows")

    connection = get_connection()
    cursor = None
    try:
        ensure_prayer_times_table(connection)
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM dbo.PrayerTimes")
        existing = cursor.fetchone()["total"]

        if existing and not replace_existing:
            raise RuntimeError(
                f"dbo.PrayerTimes already contains {existing} rows. "
                "Import cancelled to avoid duplicates. Use replace_existing=True "
                "only if you intend to replace all existing prayer-time records."
            )

        if replace_existing:
            cursor.execute("DELETE FROM dbo.PrayerTimes")

        cursor.executemany(
            """
            INSERT INTO dbo.PrayerTimes
                (PrayerDate, Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha,
                 DataSource, TimeZone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.commit()
        return len(rows)
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        connection.close()


def get_prayer_times(prayer_date=None):
    """Return one day's prayer times as HH:MM strings, or None if not found."""
    if prayer_date is None:
        prayer_date = datetime.now().date()
    elif isinstance(prayer_date, datetime):
        prayer_date = prayer_date.date()
    elif isinstance(prayer_date, str):
        prayer_date = date.fromisoformat(prayer_date)
    elif not isinstance(prayer_date, date):
        raise TypeError("prayer_date must be a date, datetime, ISO date string, or None")

    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha, DataSource, TimeZone
            FROM dbo.PrayerTimes
            WHERE PrayerDate = ?
            """,
            (prayer_date,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        def as_hhmm(value):
            return value.strftime("%H:%M") if hasattr(value, "strftime") else str(value)[:5]

        return {
            "Fajr": as_hhmm(row["Fajr"]),
            "Sunrise": as_hhmm(row["Sunrise"]),
            "Dhuhr": as_hhmm(row["Dhuhr"]),
            "Asr": as_hhmm(row["Asr"]),
            "Maghrib": as_hhmm(row["Maghrib"]),
            "Isha": as_hhmm(row["Isha"]),
            "source": row["DataSource"],
            "timezone": row["TimeZone"],
        }
    finally:
        if cursor:
            cursor.close()
        connection.close()


# =========================================================
# Initialize Database
# =========================================================

def initialize_database():

    connection = get_connection()

    # جدول مواقيت الصلاة محلي، ينشأ تلقائيًا ولا يحتاج اتصالًا بالإنترنت.
    ensure_prayer_times_table(connection)
    connection.commit()

    cursor = connection.cursor()

    required_tables = [
        "app_settings",
        "buildings",
        "devices",
        "faults",
        "fault_updates",
        "spare_parts",
        "spare_part_movements",
        "audit_logs",
        # نظام الأحبار (اختياري - لا يوقف التشغيل لو لم تُنشأ بعد)
    ]

    # الجداول الاختيارية للأحبار - لا توقف التشغيل لو لم تُنشأ
    _optional_tables = [
        "org_units",
        "ink_transactions",
    ]

    missing_tables = []

    for table in required_tables:

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'dbo'
              AND TABLE_NAME = ?
            """,
            (table,)
        )

        row = cursor.fetchone()

        if row[0] == 0:
            missing_tables.append(table)

    try:
        cursor.execute("""
            IF NOT EXISTS (
                SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'faults' AND COLUMN_NAME = 'fault_target'
            )
            BEGIN
                ALTER TABLE faults ADD fault_target NVARCHAR(50) NULL DEFAULT 'device';
            END
        """)
        connection.commit()
    except Exception as err:
        print("MIGRATION WARNING (fault_target):", err)

    cursor.close()

    connection.close()

    if missing_tables:

        raise RuntimeError(
            "Missing SQL Server tables: "
            + ", ".join(
                missing_tables
            )
        )


# =========================================================
# Direct Test
# =========================================================

if __name__ == "__main__":

    try:

        initialize_database()

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM devices
            """
        )

        devices_count = (
            cursor.fetchone()["total"]
        )

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM faults
            """
        )

        faults_count = (
            cursor.fetchone()["total"]
        )

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM buildings
            """
        )

        buildings_count = (
            cursor.fetchone()["total"]
        )

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM audit_logs
            """
        )

        logs_count = (
            cursor.fetchone()["total"]
        )

        cursor.close()

        connection.close()

        print(
            "========================================"
        )

        print(
            "SQL SERVER DATABASE: OK"
        )

        print(
            "========================================"
        )

        print(
            f"Buildings : {buildings_count}"
        )

        print(
            f"Devices   : {devices_count}"
        )

        print(
            f"Faults    : {faults_count}"
        )

        print(
            f"Audit Logs: {logs_count}"
        )

        print(
            "========================================"
        )

    except Exception as e:

        print(
            "========================================"
        )

        print(
            "DATABASE ERROR"
        )

        print(
            "========================================"
        )

        print(
            type(e).__name__,
            ":",
            e
        )