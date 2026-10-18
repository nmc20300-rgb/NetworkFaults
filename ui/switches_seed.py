"""
ui/switches_seed.py
===================
قائمة وبيانات السويتشات المعتمدة وربطها بالمباني والكاميرات.
مأخوذة بدقة من جدول السويتشات المعتمد بالمنظومة:
  - موديلات السويتشات: Cisco (12P, 24P, 48P), Tp-Link, Ubiquiti NanoStation
  - أغراض الاستخدام: كاميرات مراقبة، شبكة عامة، شبكة عسكرية، ربط لاسلكي
  - ربط تلقائي ذكي بالكاميرات حسب المبنى والدور
"""

from database import get_connection

SWITCHES_DATA = [
    # 1. الضواغط (1 سويتش)
    {
        "code": "SW-001",
        "name": "سويتش الضواغط (كاميرا)",
        "building": "الضواغط",
        "location": "غرفة التشغيل والتحكم",
        "model": "Tp-Link",
        "ports": 8,
        "role": "كاميرات مراقبة",
        "notes": "مخصص لتغذية كاميرات مبنى الضواغط",
    },
    # 2. المبردات (1 سويتش)
    {
        "code": "SW-002",
        "name": "سويتش المبردات (شبكة)",
        "building": "المبردات",
        "location": "مبنى المبردات",
        "model": "Tp-Link",
        "ports": 8,
        "role": "شبكة",
        "notes": "مخصص لنقاط شبكة المبردات",
    },
    # 3. الإعاشة (1 سويتش)
    {
        "code": "SW-003",
        "name": "سويتش الإعاشة (كاميرا)",
        "building": "الإعاشة",
        "location": "مبنى الإعاشة",
        "model": "Tp-Link",
        "ports": 8,
        "role": "كاميرات مراقبة",
        "notes": "مخصص لكاميرات العنابر العلوية والسفلية وخلفي الذخيرة",
    },
    # 4. مبنى 1 (1 سويتش)
    {
        "code": "SW-004",
        "name": "سويتش مبنى 1 (Cisco 12P)",
        "building": "مبنى 1",
        "location": "مبنى 1",
        "model": "Cisco 12 Port",
        "ports": 12,
        "role": "شبكة وكاميرات",
        "notes": "مشترك لخدمة نقاط الشبكة وكاميرات مبنى 1",
    },
    # 5. الإدارة (3 سويتشات مذكورة وتفصيلها 4 وحدات)
    {
        "code": "SW-005",
        "name": "سويتش الإدارة — الدور الأرضي (Cisco 24P)",
        "building": "الإدارة",
        "location": "الدور الأرضي",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة وكاميرات",
        "notes": "خدمة الدور الأرضي شبكة وكاميرات",
    },
    {
        "code": "SW-006",
        "name": "سويتش الإدارة — الدور الأرضي (Tp-Link عسكرية)",
        "building": "الإدارة",
        "location": "الدور الأرضي",
        "model": "Tp-Link",
        "ports": 8,
        "role": "شبكة عسكرية",
        "notes": "مخصص للشبكة العسكرية بالدور الأرضي",
    },
    {
        "code": "SW-007",
        "name": "سويتش الإدارة — الدور الأول (Cisco 48P)",
        "building": "الإدارة",
        "location": "الدور الأول",
        "model": "Cisco 48 Port",
        "ports": 48,
        "role": "شبكة وكاميرات",
        "notes": "خدمة الدور الأول شبكة وكاميرات",
    },
    {
        "code": "SW-008",
        "name": "سويتش الإدارة — الدور الثاني (Cisco 24P)",
        "building": "الإدارة",
        "location": "الدور الثاني",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة وكاميرات",
        "notes": "خدمة الدور الثاني شبكة وكاميرات",
    },
    # 6. مبنى 3 (1 سويتش)
    {
        "code": "SW-009",
        "name": "سويتش مبنى 3 (Cisco 24P)",
        "building": "مبنى 3",
        "location": "مبنى 3",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة وكاميرات",
        "notes": "مشترك لخدمة شبكة وكاميرات مبنى 3",
    },
    # 7. مبنى الشبكة (1 سويتش)
    {
        "code": "SW-010",
        "name": "سويتش مبنى الشبكة (Cisco 24P)",
        "building": "الشبكة",
        "location": "مبنى الشبكة الرئيسي",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة وكاميرات",
        "notes": "مشترك لخدمة شبكة وكاميرات مبنى الشبكة",
    },
    # 8. مبنى 14 و 15 (2 سويتش)
    {
        "code": "SW-011",
        "name": "سويتش مبنى 14 (Tp-Link)",
        "building": "مبنى 14",
        "location": "مبنى 14",
        "model": "Tp-Link",
        "ports": 8,
        "role": "شبكة وكاميرات",
        "notes": "مشترك لخدمة مبنى 14",
    },
    {
        "code": "SW-012",
        "name": "سويتش مبنى 15 (Tp-Link)",
        "building": "مبنى 15",
        "location": "مبنى 15",
        "model": "Tp-Link",
        "ports": 8,
        "role": "شبكة وكاميرات",
        "notes": "مشترك لخدمة مبنى 15",
    },
    # 9. الصيانة (1 سويتش)
    {
        "code": "SW-013",
        "name": "سويتش فرع الصيانة (Cisco 24P)",
        "building": "فرع الصيانة",
        "location": "مبنى الصيانة",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة وكاميرات",
        "notes": "مشترك لخدمة الصيانة",
    },
    # 10. الحملة (2 سويتش)
    {
        "code": "SW-014",
        "name": "سويتش الحملة 1 (Tp-Link)",
        "building": "الحملة",
        "location": "مبنى الحملة — القطاع الأول",
        "model": "Tp-Link",
        "ports": 8,
        "role": "شبكة وكاميرات",
        "notes": "مشترك شبكة وكاميرات بالحملة",
    },
    {
        "code": "SW-015",
        "name": "سويتش الحملة 2 (Tp-Link)",
        "building": "الحملة",
        "location": "مبنى الحملة — القطاع الثاني",
        "model": "Tp-Link",
        "ports": 8,
        "role": "شبكة وكاميرات",
        "notes": "مشترك شبكة وكاميرات بالحملة",
    },
    # 11. السيلنجيه (سويتش مشترك / وحدتان)
    {
        "code": "SW-016",
        "name": "سويتش السيلنجيه — كاميرات (Tp-Link)",
        "building": "السيلنجه",
        "location": "مبنى السيلنجه",
        "model": "Tp-Link",
        "ports": 8,
        "role": "كاميرات مراقبة",
        "notes": "مخصص لكاميرات السيلنجيه",
    },
    {
        "code": "SW-017",
        "name": "سويتش السيلنجيه — شبكة (Cisco 24P)",
        "building": "السيلنجه",
        "location": "مبنى السيلنجه",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة",
        "notes": "مخصص لنقاط الشبكة بالسيلنجيه",
    },
    # 12. القزق الميكانيكي (1 سويتش)
    {
        "code": "SW-018",
        "name": "سويتش القزق الميكانيكي (Tp-Link)",
        "building": "القزق الميكانيكي",
        "location": "القزق الميكانيكي",
        "model": "Tp-Link",
        "ports": 8,
        "role": "كاميرات مراقبة",
        "notes": "مخصص لكاميرات القزق الميكانيكي",
    },
    # 13. الهنجر
    {
        "code": "SW-019",
        "name": "سويتش الهنجر — كاميرات (Tp-Link)",
        "building": "الهنجر",
        "location": "مبنى الهنجر",
        "model": "Tp-Link",
        "ports": 8,
        "role": "كاميرات مراقبة",
        "notes": "مخصص لكاميرات مبنى الهنجر",
    },
    {
        "code": "SW-020",
        "name": "سويتش الهنجر — شبكة (Cisco 24P)",
        "building": "الهنجر",
        "location": "مبنى الهنجر",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة",
        "notes": "مخصص لشبكة مبنى الهنجر",
    },
    {
        "code": "SW-021",
        "name": "نقطة ربط الهنجر (Nano Station)",
        "building": "الهنجر",
        "location": "أعلى مبنى الهنجر",
        "model": "Ubiquiti NanoStation",
        "ports": 2,
        "role": "ربط لاسلكي",
        "notes": "جهاز ربط لاسلكي Nano Station",
    },
    # 14. مبنى 43
    {
        "code": "SW-022",
        "name": "سويتش مبنى 43 — كاميرات (Tp-Link)",
        "building": "مبنى 43",
        "location": "مبنى 43",
        "model": "Tp-Link",
        "ports": 8,
        "role": "كاميرات مراقبة",
        "notes": "مخصص لكاميرات مبنى 43",
    },
    {
        "code": "SW-023",
        "name": "سويتش مبنى 43 — شبكة (Cisco 24P)",
        "building": "مبنى 43",
        "location": "مبنى 43",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة",
        "notes": "مخصص لنقاط شبكة مبنى 43",
    },
    {
        "code": "SW-024",
        "name": "نقطة ربط مبنى 43 (Nano Station)",
        "building": "مبنى 43",
        "location": "أعلى مبنى 43",
        "model": "Ubiquiti NanoStation",
        "ports": 2,
        "role": "ربط لاسلكي",
        "notes": "جهاز ربط لاسلكي Nano Station",
    },
    # 15. مبنى 44 ، 45 ، 46
    {
        "code": "SW-025",
        "name": "سويتش مبنى 44/45/46 — كاميرات (Tp-Link)",
        "building": "مبنى 44",
        "location": "مجمع مباني 44/45/46",
        "model": "Tp-Link",
        "ports": 8,
        "role": "كاميرات مراقبة",
        "notes": "مخصص لكاميرات مجمع مباني 44 و45 و46",
    },
    {
        "code": "SW-026",
        "name": "سويتش مبنى 44/45/46 — شبكة (Cisco 24P)",
        "building": "مبنى 44",
        "location": "مجمع مباني 44/45/46",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة",
        "notes": "مخصص لنقاط شبكة مباني 44 و45 و46",
    },
    {
        "code": "SW-027",
        "name": "نقطة ربط مبنى 44/45/46 (Nano Station)",
        "building": "مبنى 44",
        "location": "أعلى مبنى 44",
        "model": "Ubiquiti NanoStation",
        "ports": 2,
        "role": "ربط لاسلكي",
        "notes": "جهاز ربط لاسلكي Nano Station",
    },
    # 16. إدارة الرافع
    {
        "code": "SW-028",
        "name": "سويتش إدارة الرافع — كاميرات (Tp-Link)",
        "building": "الرافع",
        "location": "مبنى إدارة الرافع",
        "model": "Tp-Link",
        "ports": 8,
        "role": "كاميرات مراقبة",
        "notes": "مخصص لكاميرات إدارة الرافع",
    },
    {
        "code": "SW-029",
        "name": "سويتش إدارة الرافع — شبكة (Cisco 24P)",
        "building": "الرافع",
        "location": "مبنى إدارة الرافع",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة",
        "notes": "مخصص لنقاط شبكة إدارة الرافع",
    },
    {
        "code": "SW-030",
        "name": "نقطة ربط إدارة الرافع (Nano Station)",
        "building": "الرافع",
        "location": "أعلى مبنى الرافع",
        "model": "Ubiquiti NanoStation",
        "ports": 2,
        "role": "ربط لاسلكي",
        "notes": "جهاز ربط لاسلكي Nano Station",
    },
    # 17. بوابة المهبط
    {
        "code": "SW-031",
        "name": "سويتش بوابة المهبط (Tp-Link)",
        "building": "بوابة المهبط",
        "location": "غرفة حراسة بوابة المهبط",
        "model": "Tp-Link",
        "ports": 8,
        "role": "كاميرات مراقبة",
        "notes": "مخصص لتغذية كاميرا بوابة المهبط",
    },
    # 18. الطبلية
    {
        "code": "SW-032",
        "name": "سويتش الطبلية (Cisco 12P)",
        "building": "الطبلية",
        "location": "مبنى الطبلية",
        "model": "Cisco 12 Port",
        "ports": 12,
        "role": "شبكة وكاميرات",
        "notes": "مشترك لخدمة شبكة وكاميرا الطبلية",
    },
    # 19. المخازن LSC
    {
        "code": "SW-033",
        "name": "سويتش المخازن LSC — كاميرات (Tp-Link)",
        "building": "مبنى LSC",
        "location": "مبنى المخازن LSC",
        "model": "Tp-Link",
        "ports": 8,
        "role": "كاميرات مراقبة",
        "notes": "مخصص لكاميرات مخازن LSC",
    },
    {
        "code": "SW-034",
        "name": "سويتش المخازن LSC — شبكة (Cisco 24P)",
        "building": "مبنى LSC",
        "location": "مبنى المخازن LSC",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة",
        "notes": "مخصص لنقاط شبكة مخازن LSC",
    },
    # 20. الألغام
    {
        "code": "SW-035",
        "name": "سويتش مبنى الألغام (Cisco 24P)",
        "building": "الألغام",
        "location": "مبنى الألغام",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة",
        "notes": "مخصص لشبكة الألغام",
    },
    # 21. المدمرات
    {
        "code": "SW-036",
        "name": "سويتش مبنى المدمرات (Cisco 24P)",
        "building": "المدمرات",
        "location": "مبنى المدمرات",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة",
        "notes": "مخصص لشبكة المدمرات",
    },
    # 22. شعبة الصيانة
    {
        "code": "SW-037",
        "name": "سويتش شعبة الصيانة (Cisco 24P)",
        "building": "شعبه الصيانه",
        "location": "مبنى شعبة الصيانة",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة",
        "notes": "مخصص لنقاط شبكة شعبة الصيانة",
    },
    # 23. كبير المهندسين + مساعد القائد
    {
        "code": "SW-038",
        "name": "سويتش كبير المهندسين ومساعد القائد (Cisco 24P)",
        "building": "كبير المهندسين + مساعد القائد",
        "location": "مكتب كبير المهندسين ومساعد القائد",
        "model": "Cisco 24 Port",
        "ports": 24,
        "role": "شبكة",
        "notes": "مخصص لشبكة مكاتب كبير المهندسين ومساعد القائد",
    },
]


def ensure_building_id(cursor, building_name):
    """إيجاد أو إنشاء المبنى وإرجاع ID الخاص به."""
    if not building_name:
        return None

    # البحث بالاسم المباشر
    cursor.execute("SELECT id FROM buildings WHERE name = ?", (building_name,))
    row = cursor.fetchone()
    if row:
        return row["id"]

    # تنظيف المسافات والبحث التقديري
    cursor.execute("SELECT id, name FROM buildings")
    all_b = cursor.fetchall()
    clean_target = "".join(building_name.split())
    for b in all_b:
        if "".join(b["name"].split()) == clean_target:
            return b["id"]

    # إنشاء المبنى إذا لم يكن موجودًا
    cursor.execute("INSERT INTO buildings (name) VALUES (?)", (building_name,))
    cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT) AS id")
    new_row = cursor.fetchone()
    return new_row["id"] if new_row else None


def seed_network_switches(auto_link=True):
    """
    استيراد السويتشات المعتمدة وربطها بالمباني والكاميرات.
    يرجع (عدد السويتشات المضافة, عدد الكاميرات المربوطة).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # جلب الأكواد الموجودة مسبقًا لتجنب التكرار
        cursor.execute("SELECT switch_code FROM network_switches")
        existing_codes = {r["switch_code"] for r in cursor.fetchall()}

        added_switches = 0
        switches_map = {}  # switch_code -> switch_id

        for s in SWITCHES_DATA:
            b_id = ensure_building_id(cursor, s["building"])

            if s["code"] not in existing_codes:
                cursor.execute("""
                    INSERT INTO network_switches (
                        switch_code, name, building_id, location_detail,
                        model, ports_count, role, status, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, N'يعمل', ?)
                """, (
                    s["code"], s["name"], b_id, s["location"],
                    s["model"], s["ports"], s["role"], s["notes"],
                ))
                cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT) AS id")
                sw_id = cursor.fetchone()["id"]
                added_switches += 1
            else:
                cursor.execute("SELECT id FROM network_switches WHERE switch_code = ?", (s["code"],))
                sw_id = cursor.fetchone()["id"]

            switches_map[s["code"]] = {
                "id": sw_id,
                "building_id": b_id,
                "role": s["role"],
                "name": s["name"],
                "location": s["location"],
            }

        conn.commit()

        linked_cameras = 0
        if auto_link:
            linked_cameras = link_cameras_to_switches(cursor, switches_map)
            conn.commit()

        return added_switches, linked_cameras

    finally:
        conn.close()


def link_cameras_to_switches(cursor, switches_map=None):
    """
    ربط ذكي للكاميرات بالسويتشات المناسبة:
    1. يطابق مبنى الكاميرا مع مبنى السويتش المخصص للكاميرات.
    2. في مبنى الإدارة، يطابق الدور (الأرضي، الأول، الثاني).
    3. يرقم المنافذ (Port 1, Port 2, ...) تلقائيًا.
    """
    if switches_map is None:
        cursor.execute("SELECT id, switch_code, name, building_id, location_detail, role FROM network_switches WHERE is_archived = 0")
        switches_map = {
            r["switch_code"]: {
                "id": r["id"],
                "building_id": r["building_id"],
                "role": r["role"],
                "name": r["name"],
                "location": r["location_detail"],
            }
            for r in cursor.fetchall()
        }

    # جلب الكاميرات المسجلة
    cursor.execute("""
        SELECT c.id, c.camera_code, c.name, c.building_id, c.location_detail, c.switch_id
        FROM cameras c
        WHERE c.is_archived = 0
    """)
    cameras = cursor.fetchall()

    port_counters = {}
    linked_count = 0

    for cam in cameras:
        # إذا كانت الكاميرا مربوطة بالفعل بسويتش نتخطاها
        if cam["switch_id"]:
            continue

        b_id = cam["building_id"]
        if not b_id:
            continue

        loc_text = str(cam["location_detail"] or "") + " " + str(cam["name"] or "")

        # البحث عن السويتش الأنسب في نفس المبنى
        matched_switch_id = None

        # حالة خاصة: مبنى الإدارة (توزيع حسب الدور)
        if "الدور الأرضي" in loc_text:
            matched_switch_id = switches_map.get("SW-005", {}).get("id")
        elif "الدور الأول" in loc_text:
            matched_switch_id = switches_map.get("SW-007", {}).get("id")
        elif "الدور الثاني" in loc_text:
            matched_switch_id = switches_map.get("SW-008", {}).get("id")

        if not matched_switch_id:
            # البحث عن سويتش كاميرات مخصص في نفس المبنى أولاً
            candidate_switches = [
                s for s in switches_map.values()
                if s["building_id"] == b_id and "كاميرا" in s["role"]
            ]

            # إن لم يوجد، أي سويتش في نفس المبنى
            if not candidate_switches:
                candidate_switches = [
                    s for s in switches_map.values()
                    if s["building_id"] == b_id
                ]

            if candidate_switches:
                matched_switch_id = candidate_switches[0]["id"]

        if matched_switch_id:
            cursor.execute("""
                UPDATE cameras
                SET switch_id = ?, switch_port = NULL, updated_at = GETDATE()
                WHERE id = ?
            """, (matched_switch_id, cam["id"]))
            linked_count += 1

    return linked_count
