"""
ui/switches_seed.py
===================
قائمة السويتشات المعتمدة وإضافتها للمباني.
مطابقة لجدول السويتشات الفعلي (38 سويتش): المبنى + الموديل + الغرض فقط،
وموضع الدور لسويتشات الإدارة لأنه مذكور في الجدول.
أي بيانات أخرى (المنافذ لغير Cisco، المواضع، الملاحظات) تُدخل يدويًا عند الحاجة.
ربط الكاميرات بالسويتشات يتم يدويًا فقط (من نافذة الكاميرا أو نافذة ربط السويتش).
"""

from database import get_connection

SW_CAM = "كاميرات مراقبة"
SW_NET = "شبكة"
SW_BOTH = "شبكة وكاميرات"
SW_MIL = "شبكة عسكرية"
SW_WIFI = "ربط لاسلكي"

TP = "Tp-Link"
C12 = "Cisco 12 Port"
C24 = "Cisco 24 Port"
C48 = "Cisco 48 Port"
NANO = "Ubiquiti NanoStation"

# عدد المنافذ يُؤخذ من اسم موديل Cisco فقط (12/24/48)؛ غير ذلك غير محدد.
_CISCO_PORTS = {C12: 12, C24: 24, C48: 48}

# (الكود، الاسم، المبنى، الموضع، الموديل، الغرض)
_ROWS = [
    ("SW-001", "سويتش الضواغط (كاميرا)", "الضواغط", None, TP, SW_CAM),
    ("SW-002", "سويتش المبردات (شبكة)", "المبردات", None, TP, SW_NET),
    ("SW-003", "سويتش الإعاشة (كاميرا)", "الإعاشة", None, TP, SW_CAM),
    ("SW-004", "سويتش مبنى 1 (Cisco 12P)", "مبنى 1", None, C12, SW_BOTH),
    # الإدارة (4 سويتشات حسب الأدوار)
    ("SW-005", "سويتش الإدارة — الدور الأرضي (Cisco 24P)", "الإدارة", "الدور الأرضي", C24, SW_BOTH),
    ("SW-006", "سويتش الإدارة — الدور الأرضي (Tp-Link عسكرية)", "الإدارة", "الدور الأرضي", TP, SW_MIL),
    ("SW-007", "سويتش الإدارة — الدور الأول (Cisco 48P)", "الإدارة", "الدور الأول", C48, SW_BOTH),
    ("SW-008", "سويتش الإدارة — الدور الثاني (Cisco 24P)", "الإدارة", "الدور الثاني", C24, SW_BOTH),
    ("SW-009", "سويتش مبنى 3 (Cisco 24P)", "مبنى 3", None, C24, SW_BOTH),
    ("SW-010", "سويتش مبنى الشبكة (Cisco 24P)", "الشبكة", None, C24, SW_BOTH),
    ("SW-011", "سويتش مبنى 14 (Tp-Link)", "مبنى 14", None, TP, SW_BOTH),
    ("SW-012", "سويتش مبنى 15 (Tp-Link)", "مبنى 15", None, TP, SW_BOTH),
    ("SW-013", "سويتش فرع الصيانة (Cisco 24P)", "فرع الصيانة", None, C24, SW_BOTH),
    ("SW-014", "سويتش الحملة 1 (Tp-Link)", "الحملة", None, TP, SW_BOTH),
    ("SW-015", "سويتش الحملة 2 (Tp-Link)", "الحملة", None, TP, SW_BOTH),
    ("SW-016", "سويتش السيلنجيه — كاميرات (Tp-Link)", "السيلنجه", None, TP, SW_CAM),
    ("SW-017", "سويتش السيلنجيه — شبكة (Cisco 24P)", "السيلنجه", None, C24, SW_NET),
    ("SW-018", "سويتش القزق الميكانيكي (Tp-Link)", "القزق الميكانيكي", None, TP, SW_CAM),
    ("SW-019", "سويتش الهنجر — كاميرات (Tp-Link)", "الهنجر", None, TP, SW_CAM),
    ("SW-020", "سويتش الهنجر — شبكة (Cisco 24P)", "الهنجر", None, C24, SW_NET),
    ("SW-021", "نقطة ربط الهنجر (Nano Station)", "الهنجر", None, NANO, SW_WIFI),
    ("SW-022", "سويتش مبنى 43 — كاميرات (Tp-Link)", "مبنى 43", None, TP, SW_CAM),
    ("SW-023", "سويتش مبنى 43 — شبكة (Cisco 24P)", "مبنى 43", None, C24, SW_NET),
    ("SW-024", "نقطة ربط مبنى 43 (Nano Station)", "مبنى 43", None, NANO, SW_WIFI),
    ("SW-025", "سويتش مبنى 44/45/46 — كاميرات (Tp-Link)", "مبنى 44", None, TP, SW_CAM),
    ("SW-026", "سويتش مبنى 44/45/46 — شبكة (Cisco 24P)", "مبنى 44", None, C24, SW_NET),
    ("SW-027", "نقطة ربط مبنى 44/45/46 (Nano Station)", "مبنى 44", None, NANO, SW_WIFI),
    ("SW-028", "سويتش إدارة الرافع — كاميرات (Tp-Link)", "الرافع", None, TP, SW_CAM),
    ("SW-029", "سويتش إدارة الرافع — شبكة (Cisco 24P)", "الرافع", None, C24, SW_NET),
    ("SW-030", "نقطة ربط إدارة الرافع (Nano Station)", "الرافع", None, NANO, SW_WIFI),
    ("SW-031", "سويتش بوابة المهبط (Tp-Link)", "بوابة المهبط", None, TP, SW_CAM),
    ("SW-032", "سويتش الطبلية (Cisco 12P)", "الطبلية", None, C12, SW_BOTH),
    ("SW-033", "سويتش المخازن LSC — كاميرات (Tp-Link)", "مبنى LSC", None, TP, SW_CAM),
    ("SW-034", "سويتش المخازن LSC — شبكة (Cisco 24P)", "مبنى LSC", None, C24, SW_NET),
    ("SW-035", "سويتش مبنى الألغام (Cisco 24P)", "الألغام", None, C24, SW_NET),
    ("SW-036", "سويتش مبنى المدمرات (Cisco 24P)", "المدمرات", None, C24, SW_NET),
    ("SW-037", "سويتش شعبة الصيانة (Cisco 24P)", "شعبه الصيانه", None, C24, SW_NET),
    ("SW-038", "سويتش كبير المهندسين ومساعد القائد (Cisco 24P)",
     "كبير المهندسين + مساعد القائد", None, C24, SW_NET),
]

SWITCHES_DATA = [
    {
        "code": code,
        "name": name,
        "building": building,
        "location": location,
        "model": model,
        "ports": _CISCO_PORTS.get(model),
        "role": role,
        "notes": None,
    }
    for code, name, building, location, model, role in _ROWS
]


def ensure_building_id(cursor, building_name):
    """إيجاد أو إنشاء المبنى وإرجاع ID الخاص به."""
    if not building_name:
        return None

    cursor.execute("SELECT id FROM buildings WHERE name = ?", (building_name,))
    row = cursor.fetchone()
    if row:
        return row["id"]

    cursor.execute("SELECT id, name FROM buildings")
    clean_target = "".join(building_name.split())
    for b in cursor.fetchall():
        if "".join(b["name"].split()) == clean_target:
            return b["id"]

    cursor.execute("INSERT INTO buildings (name) VALUES (?)", (building_name,))
    cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT) AS id")
    new_row = cursor.fetchone()
    return new_row["id"] if new_row else None


def seed_network_switches(auto_link=False, *args, **kwargs):
    """
    استيراد السويتشات المعتمدة وربطها بالمباني فقط.
    لا يربط أي كاميرا بأي سويتش؛ الربط يدوي.
    يرجع عدد السويتشات المضافة.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT switch_code FROM network_switches")
        existing_codes = {r["switch_code"] for r in cursor.fetchall()}

        added_switches = 0

        for s in SWITCHES_DATA:
            if s["code"] in existing_codes:
                continue

            b_id = ensure_building_id(cursor, s["building"])
            cursor.execute("""
                INSERT INTO network_switches (
                    switch_code, name, building_id, location_detail,
                    model, ports_count, role, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, N'يعمل', ?)
            """, (
                s["code"], s["name"], b_id, s["location"],
                s["model"], s["ports"], s["role"], s["notes"],
            ))
            added_switches += 1

        conn.commit()
        return added_switches

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()