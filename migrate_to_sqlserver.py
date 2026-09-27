import sqlite3
import pyodbc
from pathlib import Path


# =========================
# SQLite
# =========================
BASE_DIR = Path(__file__).resolve().parent
SQLITE_DB = BASE_DIR / "data" / "network_faults.db"


# =========================
# SQL Server
# =========================
SQL_SERVER_CONNECTION = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=NetworkFaults;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)


TABLES = [
    "buildings",
    "devices",
    "faults",
    "fault_updates",
    "spare_parts",
    "spare_part_movements",
    "app_settings",
]


def sqlite_connection():
    con = sqlite3.connect(SQLITE_DB)
    con.row_factory = sqlite3.Row
    return con


def sqlserver_connection():
    return pyodbc.connect(SQL_SERVER_CONNECTION)


def get_columns(sqlite_cur, table):
    rows = sqlite_cur.execute(f"PRAGMA table_info([{table}])").fetchall()
    return [row["name"] for row in rows]


def migrate_table(sqlite_cur, sql_cur, table):
    columns = get_columns(sqlite_cur, table)

    rows = sqlite_cur.execute(
        f"SELECT * FROM [{table}]"
    ).fetchall()

    print(f"\n[{table}] SQLite rows: {len(rows)}")

    if not rows:
        print(f"[{table}] Nothing to migrate.")
        return 0

    column_list = ", ".join(f"[{c}]" for c in columns)
    placeholders = ", ".join("?" for _ in columns)

    sql = f"""
        INSERT INTO [{table}] ({column_list})
        VALUES ({placeholders})
    """

    count = 0

    for row in rows:
        values = [row[c] for c in columns]

        # SQLite INTEGER 0/1 -> SQL Server BIT
        if table == "devices" and "is_archived" in columns:
            index = columns.index("is_archived")
            if values[index] is not None:
                values[index] = 1 if int(values[index]) else 0

        if table == "spare_parts" and "is_archived" in columns:
            index = columns.index("is_archived")
            if values[index] is not None:
                values[index] = 1 if int(values[index]) else 0

        sql_cur.execute(sql, values)
        count += 1

    print(f"[{table}] Migrated: {count}")
    return count


def verify_counts(sqlite_cur, sql_cur):
    print("\n" + "=" * 60)
    print("VERIFYING COUNTS")
    print("=" * 60)

    all_ok = True

    for table in TABLES:
        sqlite_count = sqlite_cur.execute(
            f"SELECT COUNT(*) FROM [{table}]"
        ).fetchone()[0]

        sqlserver_count = sql_cur.execute(
            f"SELECT COUNT(*) FROM [{table}]"
        ).fetchone()[0]

        status = "OK" if sqlite_count == sqlserver_count else "MISMATCH"

        print(
            f"{table:25} "
            f"SQLite={sqlite_count:<5} "
            f"SQL Server={sqlserver_count:<5} "
            f"{status}"
        )

        if sqlite_count != sqlserver_count:
            all_ok = False

    return all_ok


def main():
    print("=" * 60)
    print("NetworkFaults - SQLite -> SQL Server Migration")
    print("=" * 60)

    print(f"\nSQLite DB:")
    print(SQLITE_DB)

    if not SQLITE_DB.exists():
        print("\nERROR: SQLite database not found.")
        return

    sqlite_con = None
    sqlserver_con = None

    try:
        sqlite_con = sqlite_connection()
        sqlite_cur = sqlite_con.cursor()

        sqlserver_con = sqlserver_connection()
        sql_cur = sqlserver_con.cursor()

        print("\nSQL Server connection: OK")

        # Check that target tables exist
        print("\nChecking SQL Server tables...")

        for table in TABLES:
            sql_cur.execute(
                """
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo'
                AND TABLE_NAME = ?
                """,
                table,
            )

            exists = sql_cur.fetchone()[0]

            if not exists:
                raise RuntimeError(
                    f"SQL Server table not found: {table}"
                )

        print("All target tables exist.")

        # Check target is empty
        print("\nChecking target database...")

        total_target = 0

        for table in TABLES:
            sql_cur.execute(f"SELECT COUNT(*) FROM [{table}]")
            count = sql_cur.fetchone()[0]
            total_target += count

            if count:
                print(
                    f"WARNING: {table} already contains {count} rows."
                )

        if total_target:
            print(
                "\nMigration stopped because SQL Server already "
                "contains data."
            )
            print(
                "This script will NOT overwrite existing records."
            )
            return

        # Disable foreign key problem by inserting in dependency order
        print("\nStarting migration...")

        # Parent tables first
        migration_order = [
            "app_settings",
            "buildings",
            "devices",
            "spare_parts",
            "faults",
            "fault_updates",
            "spare_part_movements",
        ]

        for table in migration_order:
            migrate_table(sqlite_cur, sql_cur, table)

        sqlserver_con.commit()

        print("\nMigration committed successfully.")

        # Verify
        if verify_counts(sqlite_cur, sql_cur):
            print("\n" + "=" * 60)
            print("MIGRATION SUCCESSFUL")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("MIGRATION COMPLETED WITH COUNT MISMATCH")
            print("=" * 60)

    except Exception as e:
        if sqlserver_con:
            sqlserver_con.rollback()

        print("\n" + "=" * 60)
        print("MIGRATION FAILED")
        print("=" * 60)
        print(type(e).__name__, ":", e)

    finally:
        if sqlite_con:
            sqlite_con.close()

        if sqlserver_con:
            sqlserver_con.close()


if __name__ == "__main__":
    main()