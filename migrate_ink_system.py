"""
migrate_ink_system.py
=====================
نظام الأحبار - سكريبت إنشاء الجداول وبذر البيانات الأولية
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_connection


# =============================================================
# Helpers
# =============================================================

def table_exists(cursor, table_name):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'dbo'
          AND TABLE_NAME = ?
        """,
        (table_name,)
    )
    return cursor.fetchone()[0] > 0


def permission_exists(cursor, code):
    cursor.execute(
        "SELECT COUNT(*) FROM dbo.permissions WHERE permission_code = ?",
        (code,)
    )
    return cursor.fetchone()[0] > 0


# =============================================================
# Step 1 – Organizational Units
# =============================================================

CREATE_ORG_UNITS = """
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'org_units'
)
BEGIN
    CREATE TABLE dbo.org_units (
        id          INT IDENTITY(1,1) PRIMARY KEY,
        name        NVARCHAR(200)  NOT NULL,
        unit_type   NVARCHAR(20)   NOT NULL
                        CHECK (unit_type IN (N'فرع', N'مبنى', N'قسم', N'مكتب')),
        parent_id   INT            NULL
                        REFERENCES dbo.org_units(id),
        is_active   BIT            NOT NULL DEFAULT 1,
        sort_order  INT            NOT NULL DEFAULT 0,
        created_at  DATETIME2      NOT NULL DEFAULT SYSDATETIME(),
        updated_at  DATETIME2      NOT NULL DEFAULT SYSDATETIME()
    );
END
"""

# =============================================================
# Step 2 – Ink Transactions
# =============================================================

CREATE_INK_TRANSACTIONS = """
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'ink_transactions'
)
BEGIN
    CREATE TABLE dbo.ink_transactions (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        serial_number   INT NOT NULL,
        trans_date      DATE NOT NULL,
        org_unit_id     INT  NOT NULL
                            REFERENCES dbo.org_units(id),
        office_id       INT  NULL
                            REFERENCES dbo.org_units(id),
        quantity        INT  NOT NULL CHECK (quantity > 0),
        delivery_date   DATE NULL,
        status          NVARCHAR(30) NOT NULL
                            CHECK (status IN (
                                N'ملئ',
                                N'إصلاح',
                                N'ملئ و إصلاح',
                                N'تدبير من القديم',
                                N'تكهين'
                            )),
        disposal_reason NVARCHAR(500) NULL,
        created_by      INT NULL
                            REFERENCES dbo.users(id),
        created_at      DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        updated_at      DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
END
"""

CREATE_SERIAL_SEQUENCE = """
IF NOT EXISTS (
    SELECT 1 FROM sys.sequences
    WHERE name = 'ink_serial_seq' AND schema_id = SCHEMA_ID('dbo')
)
BEGIN
    CREATE SEQUENCE dbo.ink_serial_seq
        AS INT
        START WITH 1
        INCREMENT BY 1;
END
"""


# =============================================================
# Step 3 – Permissions
# =============================================================

INK_PERMISSIONS = [
    ("ink.view",                 "عرض الأحبار"),
    ("ink.add",                  "إضافة سجل أحبار"),
    ("ink.edit",                 "تعديل سجل أحبار"),
    ("ink.delete",               "حذف سجل أحبار"),
    ("ink.org_structure.manage", "إدارة الهيكل التنظيمي"),
]


def insert_permission(cursor, code, description):
    if not permission_exists(cursor, code):
        cursor.execute(
            """
            INSERT INTO dbo.permissions (permission_code, permission_name, description, is_active)
            VALUES (?, ?, ?, 1)
            """,
            (code, description, description)
        )
        print(f"  added permission: {code}")
    else:
        print(f"  exists: {code}")


def ensure_role_permission(cursor, role_id, permission_id, allowed=1):
    cursor.execute(
        """
        SELECT COUNT(*) FROM dbo.role_permissions
        WHERE role_id = ? AND permission_id = ?
        """,
        (role_id, permission_id)
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
            INSERT INTO dbo.role_permissions (role_id, permission_id, allowed)
            VALUES (?, ?, ?)
            """,
            (role_id, permission_id, allowed)
        )


# =============================================================
# Step 4 – Seed Org Data
# =============================================================

ORG_SEED = [
    # الإدارة
    {"key": "الإدارة",              "name": "الإدارة",              "type": "قسم",  "parent": None},
    {"key": "القائد",               "name": "القائد",               "type": "مكتب", "parent": "الإدارة"},
    {"key": "السكرتارية",           "name": "السكرتارية",           "type": "مكتب", "parent": "الإدارة"},
    {"key": "رئيس الأركان",         "name": "رئيس الأركان",         "type": "مكتب", "parent": "الإدارة"},

    # فرع التنظيم
    {"key": "فرع التنظيم",          "name": "فرع التنظيم",          "type": "فرع",  "parent": None},
    {"key": "رئيس فرع التنظيم",     "name": "رئيس فرع التنظيم",     "type": "مكتب", "parent": "فرع التنظيم"},
    {"key": "الإدارة العسكرية",     "name": "الإدارة العسكرية",     "type": "مكتب", "parent": "فرع التنظيم"},
    {"key": "مكتب الخدمة",          "name": "مكتب الخدمة",          "type": "مكتب", "parent": "فرع التنظيم"},
    {"key": "الماليات",             "name": "الماليات",             "type": "مكتب", "parent": "فرع التنظيم"},
    {"key": "الأفراد",              "name": "الأفراد",              "type": "مكتب", "parent": "فرع التنظيم"},
    {"key": "التنظيم",              "name": "التنظيم",              "type": "مكتب", "parent": "فرع التنظيم"},
    {"key": "أرشيف القائد",         "name": "أرشيف القائد",         "type": "مكتب", "parent": "فرع التنظيم"},
    {"key": "المجندين",             "name": "المجندين",             "type": "مكتب", "parent": "فرع التنظيم"},
    {"key": "سرية س5",              "name": "سرية س5",              "type": "مكتب", "parent": "فرع التنظيم"},
    {"key": "الإشارات تنظيم",       "name": "الإشارات",             "type": "مكتب", "parent": "فرع التنظيم"},
    {"key": "نائب أحكام",           "name": "نائب أحكام",           "type": "مكتب", "parent": "فرع التنظيم"},
    {"key": "الحسابات الخصوصية",    "name": "الحسابات الخصوصية",    "type": "مكتب", "parent": "فرع التنظيم"},
    {"key": "ميس الضباط",           "name": "ميس الضباط",           "type": "مكتب", "parent": "فرع التنظيم"},
    {"key": "الشبكة العسكرية",      "name": "الشبكة العسكرية",      "type": "مكتب", "parent": "فرع التنظيم"},

    # الشبكة
    {"key": "الشبكة",               "name": "الشبكة",               "type": "قسم",  "parent": None},
    {"key": "قائد الشبكة",          "name": "قائد الشبكة",          "type": "مكتب", "parent": "الشبكة"},
    {"key": "ضباط وصف ضباط الشبكة","name": "ضباط وصف ضباط الشبكة","type": "مكتب", "parent": "الشبكة"},
    {"key": "مهندسو الشبكة",        "name": "مهندسو الشبكة",        "type": "مكتب", "parent": "الشبكة"},

    # فرع التخطيط
    {"key": "فرع التخطيط",          "name": "فرع التخطيط",          "type": "فرع",  "parent": None},
    {"key": "رئيس فرع التخطيط",     "name": "رئيس فرع التخطيط",     "type": "مكتب", "parent": "فرع التخطيط"},
    {"key": "نائب رئيس فرع التخطيط","name": "نائب رئيس فرع التخطيط","type": "مكتب", "parent": "فرع التخطيط"},
    {"key": "رئيس قسم الإنتاج",     "name": "رئيس قسم الإنتاج",     "type": "مكتب", "parent": "فرع التخطيط"},
    {"key": "أرشيف التخطيط",        "name": "أرشيف التخطيط",        "type": "مكتب", "parent": "فرع التخطيط"},
    {"key": "سرية التخطيط",         "name": "سرية التخطيط",         "type": "مكتب", "parent": "فرع التخطيط"},
    {"key": "العمليات",             "name": "العمليات",             "type": "مكتب", "parent": "فرع التخطيط"},

    # الإشراف
    {"key": "الإشراف",              "name": "الإشراف",              "type": "قسم",  "parent": None},
    {"key": "قائد الإشراف",         "name": "قائد الإشراف",         "type": "مكتب", "parent": "الإشراف"},
    {"key": "نائب قائد الإشراف",    "name": "نائب قائد الإشراف",    "type": "مكتب", "parent": "الإشراف"},
    {"key": "ضباط الإشراف",         "name": "ضباط الإشراف",         "type": "مكتب", "parent": "الإشراف"},

    # التوجيه
    {"key": "التوجيه",              "name": "التوجيه",              "type": "قسم",  "parent": None},
    {"key": "سرية التوجيه",         "name": "سرية التوجيه",         "type": "مكتب", "parent": "التوجيه"},
    {"key": "قائد مناوب التوجيه",   "name": "قائد مناوب",           "type": "مكتب", "parent": "التوجيه"},
    {"key": "الحراسة",              "name": "الحراسة",              "type": "مكتب", "parent": "التوجيه"},

    # مبنى 1
    {"key": "مبنى 1",               "name": "مبنى 1",               "type": "مبنى", "parent": None},
    {"key": "قائد مبنى 1",          "name": "قائد مبنى 1",          "type": "مكتب", "parent": "مبنى 1"},
    {"key": "سرية مبنى 1",          "name": "سرية مبنى 1",          "type": "مكتب", "parent": "مبنى 1"},
    {"key": "ضباط مبنى 1",          "name": "ضباط مبنى 1",          "type": "مكتب", "parent": "مبنى 1"},
    {"key": "مكتب قائد مبنى 1",     "name": "مكتب قائد مبنى 1",     "type": "مكتب", "parent": "مبنى 1"},

    # مبنى 2
    {"key": "مبنى 2",               "name": "مبنى 2",               "type": "مبنى", "parent": None},
    {"key": "قائد مبنى 2",          "name": "قائد مبنى 2",          "type": "مكتب", "parent": "مبنى 2"},
    {"key": "ضباط مبنى 2",          "name": "ضباط مبنى 2",          "type": "مكتب", "parent": "مبنى 2"},
    {"key": "سرية مبنى 2",          "name": "سرية مبنى 2",          "type": "مكتب", "parent": "مبنى 2"},

    # القزق الميكانيكي
    {"key": "القزق الميكانيكي",     "name": "القزق الميكانيكي",     "type": "مبنى", "parent": None},
    {"key": "قائد القزق",           "name": "قائد القزق الميكانيكي","type": "مكتب", "parent": "القزق الميكانيكي"},
    {"key": "سرية القزق",           "name": "سرية القزق الميكانيكي","type": "مكتب", "parent": "القزق الميكانيكي"},

    # المبنى الفرنسي
    {"key": "المبنى الفرنسي",       "name": "المبنى الفرنسي",       "type": "مبنى", "parent": None},
    {"key": "مكتب المبنى الفرنسي",  "name": "المبنى الفرنسي",       "type": "مكتب", "parent": "المبنى الفرنسي"},

    # مبنى 3
    {"key": "مبنى 3",               "name": "مبنى 3",               "type": "مبنى", "parent": None},
    {"key": "قائد مبنى 3",          "name": "قائد مبنى 3",          "type": "مكتب", "parent": "مبنى 3"},
    {"key": "نائب قائد مبنى 3",     "name": "نائب قائد مبنى 3",     "type": "مكتب", "parent": "مبنى 3"},
    {"key": "ضباط مبنى 3",          "name": "ضباط مبنى 3",          "type": "مكتب", "parent": "مبنى 3"},
    {"key": "تخطيط مبنى 3",         "name": "تخطيط مبنى 3",         "type": "مكتب", "parent": "مبنى 3"},
    {"key": "سرية مبنى 3",          "name": "سرية مبنى 3",          "type": "مكتب", "parent": "مبنى 3"},
    {"key": "قائد مبنى 15",         "name": "قائد مبنى 15",         "type": "مكتب", "parent": "مبنى 3"},
    {"key": "سرية مبنى 15",         "name": "سرية مبنى 15",         "type": "مكتب", "parent": "مبنى 3"},
    {"key": "قسم المدفعية",         "name": "قسم المدفعية",         "type": "مكتب", "parent": "مبنى 3"},
    {"key": "قسم الخراطة",          "name": "قسم الخراطة",          "type": "مكتب", "parent": "مبنى 3"},
    {"key": "مدنيين قوات مسلحة",    "name": "مدنيين قوات مسلحة",    "type": "مكتب", "parent": "مبنى 3"},
    {"key": "المسبك",               "name": "المسبك",               "type": "مكتب", "parent": "مبنى 3"},
    {"key": "قسم الديزل",           "name": "قسم الديزل",           "type": "مكتب", "parent": "مبنى 3"},
    {"key": "قسم الميكانيكا 3",     "name": "قسم الميكانيكا",       "type": "مكتب", "parent": "مبنى 3"},
    {"key": "MTU مبنى 3",           "name": "MTU",                  "type": "مكتب", "parent": "مبنى 3"},
    {"key": "المعمل",               "name": "المعمل",               "type": "مكتب", "parent": "مبنى 3"},
    {"key": "مخزن العدة",           "name": "مخزن العدة",           "type": "مكتب", "parent": "مبنى 3"},
    {"key": "ورشة MTU",             "name": "ورشة MTU",             "type": "مكتب", "parent": "مبنى 3"},
    {"key": "ورشة المدفعية",        "name": "ورشة المدفعية",        "type": "مكتب", "parent": "مبنى 3"},

    # مبنى 4/7
    {"key": "مبنى 4/7",             "name": "مبنى 4/7",             "type": "مبنى", "parent": None},
    {"key": "قائد مبنى 4/7",        "name": "قائد مبنى 4/7",        "type": "مكتب", "parent": "مبنى 4/7"},
    {"key": "نائب قائد مبنى 4/7",   "name": "نائب قائد مبنى 4/7",   "type": "مكتب", "parent": "مبنى 4/7"},
    {"key": "ضباط مبنى 4/7",        "name": "ضباط مبنى 4/7",        "type": "مكتب", "parent": "مبنى 4/7"},
    {"key": "تخطيط مبنى 4/7",       "name": "تخطيط مبنى 4/7",       "type": "مكتب", "parent": "مبنى 4/7"},
    {"key": "سرية مبنى 4/7",        "name": "سرية مبنى 4/7",        "type": "مكتب", "parent": "مبنى 4/7"},
    {"key": "قسم اللف",             "name": "قسم اللف",             "type": "مكتب", "parent": "مبنى 4/7"},
    {"key": "قسم المواتير",         "name": "قسم المواتير",         "type": "مكتب", "parent": "مبنى 4/7"},
    {"key": "قسم التركيبات",        "name": "قسم التركيبات",        "type": "مكتب", "parent": "مبنى 4/7"},
    {"key": "أرشيف المدنيين",       "name": "أرشيف المدنيين",       "type": "مكتب", "parent": "مبنى 4/7"},
    {"key": "قسم البطاريات",        "name": "قسم البطاريات",        "type": "مكتب", "parent": "مبنى 4/7"},
    {"key": "الثلاجات",             "name": "الثلاجات",             "type": "مكتب", "parent": "مبنى 4/7"},
    {"key": "محطة الاختبار",        "name": "محطة الاختبار",        "type": "مكتب", "parent": "مبنى 4/7"},
    {"key": "محطة التركيبات",       "name": "محطة التركيبات",       "type": "مكتب", "parent": "مبنى 4/7"},
    {"key": "مخزن مستديم 4/7",      "name": "مخزن مستديم",          "type": "مكتب", "parent": "مبنى 4/7"},
    {"key": "مخزن مستهلك",          "name": "مخزن مستهلك",          "type": "مكتب", "parent": "مبنى 4/7"},

    # مبنى 5
    {"key": "مبنى 5",               "name": "مبنى 5",               "type": "مبنى", "parent": None},
    {"key": "قائد مبنى 5",          "name": "قائد مبنى 5",          "type": "مكتب", "parent": "مبنى 5"},
    {"key": "نائب قائد مبنى 5",     "name": "نائب قائد مبنى 5",     "type": "مكتب", "parent": "مبنى 5"},
    {"key": "ضباط مبنى 5",          "name": "ضباط مبنى 5",          "type": "مكتب", "parent": "مبنى 5"},
    {"key": "سرية مبنى 5",          "name": "سرية مبنى 5",          "type": "مكتب", "parent": "مبنى 5"},
    {"key": "مخزن مبنى 5",          "name": "مخزن مبنى 5",          "type": "مكتب", "parent": "مبنى 5"},
    {"key": "مكتب الضباط 5",        "name": "مكتب الضباط",          "type": "مكتب", "parent": "مبنى 5"},

    # فرع الصيانة
    {"key": "فرع الصيانة",          "name": "فرع الصيانة",          "type": "فرع",  "parent": None},
    {"key": "رئيس فرع الصيانة",     "name": "رئيس فرع الصيانة",     "type": "مكتب", "parent": "فرع الصيانة"},
    {"key": "نائب رئيس الصيانة",    "name": "نائب رئيس فرع الصيانة","type": "مكتب", "parent": "فرع الصيانة"},
    {"key": "سرية فرع الصيانة",     "name": "سرية فرع الصيانة",     "type": "مكتب", "parent": "فرع الصيانة"},
    {"key": "الأوناش صيانة",        "name": "الأوناش",              "type": "مكتب", "parent": "فرع الصيانة"},
    {"key": "ورشة الصيانة",         "name": "ورشة الصيانة",         "type": "مكتب", "parent": "فرع الصيانة"},
    {"key": "رئيس قسم الأوناش",     "name": "رئيس قسم الأوناش",     "type": "مكتب", "parent": "فرع الصيانة"},
    {"key": "رئيس قسم الميكانيكا",  "name": "رئيس قسم الميكانيكا",  "type": "مكتب", "parent": "فرع الصيانة"},
    {"key": "محطة الغازات",         "name": "محطة الغازات",         "type": "مكتب", "parent": "فرع الصيانة"},

    # هنجر السلنجيه
    {"key": "هنجر السلنجيه",        "name": "هنجر السلنجيه",        "type": "مبنى", "parent": None},
    {"key": "قائد السلنجيه",        "name": "قائد السلنجيه",        "type": "مكتب", "parent": "هنجر السلنجيه"},
    {"key": "سرية السلنجيه",        "name": "سرية السلنجيه",        "type": "مكتب", "parent": "هنجر السلنجيه"},
    {"key": "قائد مبنى 14",         "name": "قائد مبنى 14",         "type": "مكتب", "parent": "هنجر السلنجيه"},
    {"key": "سرية مبنى 14",         "name": "سرية مبنى 14",         "type": "مكتب", "parent": "هنجر السلنجيه"},
    {"key": "مكتب السريه سلنجيه",   "name": "مكتب السريه",          "type": "مكتب", "parent": "هنجر السلنجيه"},
    {"key": "مكتب الضباط سلنجيه",   "name": "مكتب الضباط",          "type": "مكتب", "parent": "هنجر السلنجيه"},
    {"key": "مكتب اللوجيستي",       "name": "مكتب اللوجيستي",       "type": "مكتب", "parent": "هنجر السلنجيه"},
    {"key": "هنجر السلنجيه مكتب",   "name": "هنجر السلنجيه",        "type": "مكتب", "parent": "هنجر السلنجيه"},

    # الحملة
    {"key": "الحملة",               "name": "الحملة",               "type": "قسم",  "parent": None},
    {"key": "قائد الحملة",          "name": "قائد الحملة",          "type": "مكتب", "parent": "الحملة"},
    {"key": "الحملة مكتب",          "name": "الحملة",               "type": "مكتب", "parent": "الحملة"},

    # التدريب
    {"key": "التدريب",              "name": "التدريب",              "type": "قسم",  "parent": None},
    {"key": "رئيس فرع التدريب",     "name": "رئيس فرع التدريب",     "type": "مكتب", "parent": "التدريب"},
    {"key": "أرشيف التدريب",        "name": "أرشيف التدريب",        "type": "مكتب", "parent": "التدريب"},

    # ورشة النجارة
    {"key": "ورشة النجارة",         "name": "ورشة النجارة",         "type": "مبنى", "parent": None},
    {"key": "قائد مبنى النجارة",    "name": "قائد مبنى النجارة",    "type": "مكتب", "parent": "ورشة النجارة"},
    {"key": "سرية مبنى النجارة",    "name": "سرية مبنى النجارة",    "type": "مكتب", "parent": "ورشة النجارة"},

    # شئون العاملين
    {"key": "شئون العاملين",        "name": "شئون العاملين",        "type": "قسم",  "parent": None},
    {"key": "رئيس شئون العاملين",   "name": "رئيس شئون العاملين",   "type": "مكتب", "parent": "شئون العاملين"},
    {"key": "شئون العاملين مكتب",   "name": "شئون العاملين",        "type": "مكتب", "parent": "شئون العاملين"},

    # فرع الميزانية
    {"key": "فرع الميزانية",        "name": "فرع الميزانية",        "type": "فرع",  "parent": None},
    {"key": "رئيس الفرع ميزانية",   "name": "رئيس الفرع",           "type": "مكتب", "parent": "فرع الميزانية"},
    {"key": "نائب رئيس الميزانية",  "name": "نائب رئيس الفرع",      "type": "مكتب", "parent": "فرع الميزانية"},
    {"key": "MMC",                   "name": "MMC",                  "type": "مكتب", "parent": "فرع الميزانية"},
    {"key": "أرشيف الميزانية",      "name": "أرشيف الميزانية",      "type": "مكتب", "parent": "فرع الميزانية"},
    {"key": "قائد مبنى 4 مخازن",    "name": "قائد مبنى 4 مخازن",    "type": "مكتب", "parent": "فرع الميزانية"},
    {"key": "غرفة المراقبة",        "name": "غرفة المراقبة",        "type": "مكتب", "parent": "فرع الميزانية"},

    # فرع الشئون الإدارية
    {"key": "فرع الشئون الإدارية",  "name": "فرع الشئون الإدارية",  "type": "فرع",  "parent": None},
    {"key": "رئيس الفرع إداري",     "name": "رئيس الفرع",           "type": "مكتب", "parent": "فرع الشئون الإدارية"},
    {"key": "الحريق",               "name": "الحريق",               "type": "مكتب", "parent": "فرع الشئون الإدارية"},
    {"key": "سرية الشؤون الإدارية", "name": "سرية الشؤون الإدارية", "type": "مكتب", "parent": "فرع الشئون الإدارية"},
    {"key": "الفرن",                "name": "الفرن",                "type": "مكتب", "parent": "فرع الشئون الإدارية"},
    {"key": "العيادة",              "name": "العيادة",              "type": "مكتب", "parent": "فرع الشئون الإدارية"},
    {"key": "المهمات",              "name": "المهمات",              "type": "مكتب", "parent": "فرع الشئون الإدارية"},

    # فرع الأمن
    {"key": "فرع الأمن",            "name": "فرع الأمن",            "type": "فرع",  "parent": None},
    {"key": "قائد الأمن",           "name": "قائد الأمن",           "type": "مكتب", "parent": "فرع الأمن"},
    {"key": "ضابط أمن الرافع",      "name": "ضابط أمن الرافع",      "type": "مكتب", "parent": "فرع الأمن"},
    {"key": "حكمدار الأمن",         "name": "حكمدار الأمن",         "type": "مكتب", "parent": "فرع الأمن"},
    {"key": "أمن الشركات",          "name": "أمن الشركات",          "type": "مكتب", "parent": "فرع الأمن"},
    {"key": "مكتب الاستعلامات",     "name": "مكتب الاستعلامات",     "type": "مكتب", "parent": "فرع الأمن"},
    {"key": "سرية الأمن والأختام",  "name": "سرية الأمن والأختام",  "type": "مكتب", "parent": "فرع الأمن"},
    {"key": "أرشيف الأمن",          "name": "أرشيف الأمن",          "type": "مكتب", "parent": "فرع الأمن"},
    {"key": "مركز المراقبة",        "name": "مركز المراقبة",        "type": "مكتب", "parent": "فرع الأمن"},
    {"key": "السنترال",             "name": "السنترال",             "type": "مكتب", "parent": "فرع الأمن"},

    # رافع السفن
    {"key": "رافع السفن",           "name": "رافع السفن",           "type": "قسم",  "parent": None},
    {"key": "قائد الرافع",          "name": "قائد الرافع",          "type": "مكتب", "parent": "رافع السفن"},
    {"key": "قائد مناوب الرافع",    "name": "قائد مناوب الرافع",    "type": "مكتب", "parent": "رافع السفن"},
    {"key": "سرية الرافع",          "name": "سرية الرافع",          "type": "مكتب", "parent": "رافع السفن"},
    {"key": "كنترول الرافع",        "name": "كنترول الرافع",        "type": "مكتب", "parent": "رافع السفن"},
    {"key": "مدنيين الرافع",        "name": "مدنيين الرافع",        "type": "مكتب", "parent": "رافع السفن"},
    {"key": "غرفة أمن الرافع",      "name": "غرفة أمن الرافع",      "type": "مكتب", "parent": "رافع السفن"},
    {"key": "الأوناش رافع",         "name": "الأوناش",              "type": "مكتب", "parent": "رافع السفن"},
    {"key": "التجاري",              "name": "التجاري",              "type": "مكتب", "parent": "رافع السفن"},
    {"key": "الفروشات",             "name": "الفروشات",             "type": "مكتب", "parent": "رافع السفن"},
    {"key": "جهاز المكتبات",        "name": "جهاز المكتبات",        "type": "مكتب", "parent": "رافع السفن"},
    {"key": "قائد التجاري",         "name": "قائد التجاري",         "type": "مكتب", "parent": "رافع السفن"},
    {"key": "مكتب الكنترول",        "name": "مكتب الكنترول",        "type": "مكتب", "parent": "رافع السفن"},
    {"key": "مكتب الميكانيكا رافع", "name": "مكتب الميكانيكا",      "type": "مكتب", "parent": "رافع السفن"},
    {"key": "مهندس أول الرافع",     "name": "مهندس أول الرافع",     "type": "مكتب", "parent": "رافع السفن"},

    # النوكس
    {"key": "النوكس",               "name": "النوكس",               "type": "قسم",  "parent": None},
    {"key": "قائد النوكس",          "name": "قائد النوكس",          "type": "مكتب", "parent": "النوكس"},
    {"key": "سرية النوكس",          "name": "سرية النوكس",          "type": "مكتب", "parent": "النوكس"},
    {"key": "مبنى 46 نوكس",         "name": "مبنى 46",              "type": "مكتب", "parent": "النوكس"},
    {"key": "قائد مبنى 46 نوكس",    "name": "قائد مبنى 46",         "type": "مكتب", "parent": "النوكس"},

    # الهنجر
    {"key": "الهنجر",               "name": "الهنجر",               "type": "مبنى", "parent": None},
    {"key": "قائد الهنجر",          "name": "قائد الهنجر",          "type": "مكتب", "parent": "الهنجر"},
    {"key": "سرية الهنجر",          "name": "سرية الهنجر",          "type": "مكتب", "parent": "الهنجر"},

    # مبنى 6 المطور
    {"key": "مبنى 6 المطور",        "name": "مبنى 6 المطور",        "type": "مبنى", "parent": None},
    {"key": "قائد مبنى 6",          "name": "قائد مبنى 6",          "type": "مكتب", "parent": "مبنى 6 المطور"},
    {"key": "سرية مبنى 6",          "name": "سرية مبنى 6",          "type": "مكتب", "parent": "مبنى 6 المطور"},

    # فرع الجودة
    {"key": "فرع الجودة",           "name": "فرع الجودة",           "type": "فرع",  "parent": None},
    {"key": "رئيس فرع الجودة",      "name": "رئيس فرع الجودة",      "type": "مكتب", "parent": "فرع الجودة"},
    {"key": "مدرسة اللحام",         "name": "مدرسة اللحام",         "type": "مكتب", "parent": "فرع الجودة"},
    {"key": "سرية الجودة",          "name": "سرية الجودة",          "type": "مكتب", "parent": "فرع الجودة"},
    {"key": "قائد الجودة",          "name": "قائد الجودة",          "type": "مكتب", "parent": "فرع الجودة"},
    {"key": "فرع الجودة مكتب",      "name": "فرع الجودة",           "type": "مكتب", "parent": "فرع الجودة"},

    # مبنى الشبكة
    {"key": "مبنى الشبكة",          "name": "مبنى الشبكة",          "type": "مبنى", "parent": None},
    {"key": "IT مبنى الشبكة",       "name": "IT",                   "type": "مكتب", "parent": "مبنى الشبكة"},
    {"key": "الورشة مبنى الشبكة",   "name": "الورشة",               "type": "مكتب", "parent": "مبنى الشبكة"},
    {"key": "مكتب قائد الشبكة",     "name": "مكتب قائد الشبكة",     "type": "مكتب", "parent": "مبنى الشبكة"},
    {"key": "منظومة الأرشيف",       "name": "منظومة الأرشيف",       "type": "مكتب", "parent": "مبنى الشبكة"},

    # مبنى اللنشات
    {"key": "مبنى اللنشات",         "name": "مبنى اللنشات",         "type": "مبنى", "parent": None},
    {"key": "قائد المبنى لنشات",    "name": "قائد المبنى",          "type": "مكتب", "parent": "مبنى اللنشات"},
    {"key": "السرية لنشات",         "name": "السرية",               "type": "مكتب", "parent": "مبنى اللنشات"},
    {"key": "التخطيط والمتابعة",    "name": "التخطيط والمتابعة",    "type": "مكتب", "parent": "مبنى اللنشات"},
    {"key": "مكتب متابعة التخطيط",  "name": "مكتب متابعة التخطيط",  "type": "مكتب", "parent": "مبنى اللنشات"},
    {"key": "المكتب الفني",         "name": "المكتب الفني",         "type": "مكتب", "parent": "مبنى اللنشات"},
    {"key": "مخازن اليارد",         "name": "مخازن اليارد",         "type": "مكتب", "parent": "مبنى اللنشات"},
    {"key": "مخزن لنشات",           "name": "مخزن",                 "type": "مكتب", "parent": "مبنى اللنشات"},

    # مبنى ISB
    {"key": "مبنى ISB",             "name": "مبنى ISB",             "type": "مبنى", "parent": None},
    {"key": "IT ISB",               "name": "IT",                   "type": "مكتب", "parent": "مبنى ISB"},
    {"key": "تخطيط النوكس ISB",     "name": "تخطيط النوكس",         "type": "مكتب", "parent": "مبنى ISB"},
    {"key": "دعم فني ISB",          "name": "دعم فني",              "type": "مكتب", "parent": "مبنى ISB"},
    {"key": "قائد المبنى ISB",      "name": "قائد المبنى",          "type": "مكتب", "parent": "مبنى ISB"},
    {"key": "مساعد مركز التخطيط",   "name": "مساعد مركز التخطيط",   "type": "مكتب", "parent": "مبنى ISB"},
    {"key": "مكتب الأمن ISB",       "name": "مكتب الأمن",           "type": "مكتب", "parent": "مبنى ISB"},
    {"key": "نائب قائد ISB",        "name": "نائب قائد المبنى",     "type": "مكتب", "parent": "مبنى ISB"},

    # مبنى LSC
    {"key": "مبنى LSC",             "name": "مبنى LSC",             "type": "مبنى", "parent": None},
    {"key": "مكتب القائد LSC",      "name": "مكتب القائد",          "type": "مكتب", "parent": "مبنى LSC"},

    # مبنى الرافع القديم
    {"key": "مبنى الرافع القديم",   "name": "مبنى الرافع (القديم)", "type": "مبنى", "parent": None},
    {"key": "المخزن رافع قديم",     "name": "المخزن",               "type": "مكتب", "parent": "مبنى الرافع القديم"},
    {"key": "مخزن الغلايات",        "name": "مخزن الغلايات",        "type": "مكتب", "parent": "مبنى الرافع القديم"},

    # مبنى 43
    {"key": "مبنى 43",              "name": "مبنى 43",              "type": "مبنى", "parent": None},
    {"key": "قائد مبنى 43",         "name": "قائد مبنى 43",         "type": "مكتب", "parent": "مبنى 43"},
    {"key": "السرية الأرشيف 43",    "name": "السرية / الأرشيف 43",  "type": "مكتب", "parent": "مبنى 43"},
    {"key": "الأرشيف 43",           "name": "الأرشيف",              "type": "مكتب", "parent": "مبنى 43"},
    {"key": "الجودة 43",            "name": "الجودة",               "type": "مكتب", "parent": "مبنى 43"},
    {"key": "فرع الجودة 43",        "name": "فرع الجودة",           "type": "مكتب", "parent": "مبنى 43"},
    {"key": "قائد الجودة 43",       "name": "قائد الجودة",          "type": "مكتب", "parent": "مبنى 43"},
    {"key": "جهاز التقطيع CNC",     "name": "جهاز التقطيع CNC",     "type": "مكتب", "parent": "مبنى 43"},
    {"key": "معمل معايرة كهربائية", "name": "معمل معايرة الأجهزة الكهربائية", "type": "مكتب", "parent": "مبنى 43"},
    {"key": "معمل معايير ميكانيكية","name": "معمل معايير أجهزة ميكانيكية",    "type": "مكتب", "parent": "مبنى 43"},

    # مبنى 44
    {"key": "مبنى 44",              "name": "مبنى 44",              "type": "مبنى", "parent": None},
    {"key": "سرية مبنى 44",         "name": "سرية مبنى 44",         "type": "مكتب", "parent": "مبنى 44"},
    {"key": "قائد النجارة 44",      "name": "قائد مبنى النجارة 44", "type": "مكتب", "parent": "مبنى 44"},

    # مبنى 46
    {"key": "مبنى 46",              "name": "مبنى 46",              "type": "مبنى", "parent": None},
    {"key": "قائد مبنى 46 مستقل",   "name": "قائد مبنى 46",         "type": "مكتب", "parent": "مبنى 46"},

    # قزق أبوقير
    {"key": "قزق أبوقير",           "name": "قزق أبوقير",           "type": "قسم",  "parent": None},
    {"key": "المخازن أبوقير",       "name": "المخازن",              "type": "مكتب", "parent": "قزق أبوقير"},
    {"key": "مكتب التدريب أبوقير",  "name": "مكتب التدريب",         "type": "مكتب", "parent": "قزق أبوقير"},
    {"key": "مكتب السرية أبوقير",   "name": "مكتب السرية",          "type": "مكتب", "parent": "قزق أبوقير"},
    {"key": "مكتب القائد أبوقير",   "name": "مكتب القائد",          "type": "مكتب", "parent": "قزق أبوقير"},

    # مكتب المتابعة (parent غير محدد)
    {"key": "مكتب المتابعة",        "name": "مكتب المتابعة",        "type": "مكتب", "parent": None},
]


def seed_org_units(cursor):
    cursor.execute("SELECT COUNT(*) FROM dbo.org_units")
    if cursor.fetchone()[0] > 0:
        print("  - org_units already seeded, skipping.")
        return

    key_to_id = {}

    for i, entry in enumerate(ORG_SEED):
        key     = entry["key"]
        name    = entry["name"]
        typ     = entry["type"]
        par_key = entry["parent"]
        parent_id = key_to_id.get(par_key) if par_key else None

        cursor.execute(
            """
            INSERT INTO dbo.org_units (name, unit_type, parent_id, is_active, sort_order)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, 1, ?)
            """,
            (name, typ, parent_id, i)
        )
        new_id = cursor.fetchone()[0]
        key_to_id[key] = new_id

    print(f"  {len(ORG_SEED)} org units seeded.")


# =============================================================
# Main
# =============================================================

def run_migration():

    print("=" * 60)
    print("INK SYSTEM MIGRATION")
    print("=" * 60)

    connection = get_connection()
    cursor     = connection.cursor()

    try:
        print("\n[1] Creating org_units table ...")
        cursor.execute(CREATE_ORG_UNITS)
        connection.commit()
        print("    done")

        print("\n[2] Creating ink_transactions table ...")
        cursor.execute(CREATE_INK_TRANSACTIONS)
        cursor.execute(CREATE_SERIAL_SEQUENCE)
        connection.commit()
        print("    done")

        print("\n[3] Adding ink permissions ...")
        for code, desc in INK_PERMISSIONS:
            insert_permission(cursor, code, desc)
        connection.commit()

        print("\n[4] Granting ink permissions to roles ...")
        cursor.execute(
            "SELECT id, role_code FROM dbo.roles WHERE role_code IN ('SUPER_ADMIN','ADMIN','SUB_ADMIN')"
        )
        roles = {r["role_code"]: r["id"] for r in cursor.fetchall()}

        for code, _ in INK_PERMISSIONS:
            cursor.execute(
                "SELECT id FROM dbo.permissions WHERE permission_code = ?",
                (code,)
            )
            perm_row = cursor.fetchone()
            if not perm_row:
                continue
            perm_id = perm_row["id"]

            if "SUPER_ADMIN" in roles:
                ensure_role_permission(cursor, roles["SUPER_ADMIN"], perm_id, 1)
            if "ADMIN" in roles:
                ensure_role_permission(cursor, roles["ADMIN"], perm_id, 1)
            if "SUB_ADMIN" in roles:
                allowed = 1 if code in ("ink.view", "ink.add") else 0
                ensure_role_permission(cursor, roles["SUB_ADMIN"], perm_id, allowed)

        connection.commit()
        print("    done")

        print("\n[5] Seeding organizational units ...")
        seed_org_units(cursor)
        connection.commit()
        print("    done")

        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)

    except Exception as e:
        try:
            connection.rollback()
        except Exception:
            pass
        print(f"\nMIGRATION FAILED: {e}")
        raise

    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass


if __name__ == "__main__":
    run_migration()
