
INT, EXT = "داخلية", "خارجية"
FIXED, PTZ = "ثابتة", "متحركة (PTZ)"
OK = "تعمل"

# الموديل الافتراضي لكل الكاميرات المستوردة
DEFAULT_MODEL = "Hikvision"

# أسماء المواقع في الشجرة المختلفة عن اسمها في جدول المباني (buildings).
# المفتاح: اسم الموقع في الشجرة — القيمة: اسم المبنى في النظام.
BUILDING_ALIASES = {
    "إدارة الرافع": "الرافع",
    "مبنى 2 مواسير": "مبنى 2",
    "مبنى LSC مخازن": "مبنى LSC",
    "مبنى الفرنسيين": "المبنى الفرنسي",
    "مبنى 4 و7": "مبنى 4&7",
    "مبنى الحملة": "الحملة",
    "عنبر الحملة": "الحملة",
    "مبنى السيلنجية": "السيلنجه",
    "مبنى الصيانة": "فرع الصيانة",
}


def _e(placement, kind, detail="", count=1, status=OK):
    return (placement, kind, detail, count, status)


CAMERA_TREE = [
    ("المخازن", 2, [
        _e(EXT, FIXED, "الواجهة السفلية"),
        _e(EXT, FIXED, "الواجهة العلوية"),
    ]),
    ("مبنى 5", 3, [
        _e(EXT, FIXED, "أمامي"),
        _e(EXT, FIXED, "خلفي"),
        _e(EXT, FIXED, "جانبي"),
    ]),
    ("الإشراف", 2, [
        _e(EXT, FIXED, "أمامي"),
        _e(EXT, FIXED, "خلفي"),
    ]),
    ("مبنى 4 و7", 3, [
        _e(INT, FIXED, "داخلي"),
        _e(EXT, FIXED, "جانبي ناحية السلاح"),
        _e(EXT, FIXED, "جانبي ناحية الفرنسيين"),
    ]),
    ("مبنى 1", 2, [
        _e(INT, FIXED),
        _e(EXT, PTZ),
    ]),
    ("الضواغط", 1, [
        _e(EXT, PTZ),
    ]),
    ("اليارد", 1, [
        _e(EXT, FIXED, "أمامي"),
    ]),
    ("مدرسة اللحام", 1, [
        _e(EXT, FIXED, "جانبي"),
    ]),
    ("الإدارة", 7, [
        _e(INT, FIXED, "الدور الأرضي", 1),
        _e(INT, FIXED, "الدور الأول", 3),
        _e(INT, FIXED, "الدور الثاني", 1),
        _e(EXT, FIXED, "واجهة المبنى", 2),
    ]),
    ("الإعاشة", 5, [
        _e(INT, FIXED, "العنبر العلوي", 2),
        _e(INT, FIXED, "العنبر السفلي", 2),
        _e(EXT, FIXED, "خلفي ناحية الذخيرة", 1),
    ]),
    ("مبنى 2 مواسير", 3, [
        _e(INT, FIXED),
        _e(EXT, FIXED, "أمامي"),
        _e(EXT, PTZ, "فوق السلاح"),
    ]),
    ("الشبكة", 5, [
        _e(INT, FIXED, "السلم"),
        _e(INT, FIXED, "السيرفر"),
        _e(INT, FIXED, "الطرقة"),
        _e(EXT, FIXED, "آخر المبنى"),
        _e(EXT, PTZ, "أول المبنى"),
    ]),
    ("مبنى الحرب الإلكترونية", 2, [
        _e(INT, FIXED, "قاعة المأمون"),
        _e(EXT, FIXED, "خلفي"),
    ]),
    ("مبنى الفرنسيين", 1, [
        _e(EXT, FIXED),
    ]),
    ("مبنى 3", 2, [
        _e(INT, FIXED, "", 2),
    ]),
    ("مبنى 15", 2, [
        _e(INT, FIXED, "أمامي"),
        _e(INT, FIXED, "خلفي"),
    ]),
    ("مبنى 14", 2, [
        _e(INT, FIXED, "أمامي"),
        _e(INT, FIXED, "خلفي"),
    ]),
    ("مبنى الحملة", 3, [
        _e(EXT, FIXED, "الجراج", 1),
        _e(EXT, FIXED, "خلف المبنى", 2),
    ]),
    ("مبنى الصيانة", 2, [
        _e(EXT, FIXED, "", 2),
    ]),
    ("عنبر الحملة", 1, [
        _e(INT, FIXED),
    ]),
    ("مبنى السيلنجية", 6, [
        _e(INT, FIXED, "", 4),
        _e(EXT, FIXED, "", 2),
    ]),
    ("القزق الميكانيكي", 2, [
        _e(EXT, FIXED, "", 2),
    ]),
    ("مبنى الهنجر", 7, [
        _e(INT, FIXED, "", 5),
        _e(EXT, FIXED, "", 2),
    ]),
    ("مبنى 43", 5, [
        _e(INT, FIXED, "", 2),
        _e(EXT, FIXED, "", 3),
    ]),
    ("مبنى 44", 1, [
        _e(INT, FIXED),
    ]),
    ("مبنى 45", 1, [
        _e(INT, FIXED),
    ]),
    ("مبنى ISB", 1, [
        _e(EXT, FIXED, "خلف المبنى"),
    ]),
    ("مبنى النجارة", 2, [
        _e(INT, FIXED),
        _e(EXT, PTZ),
    ]),
    ("مبنى LSC مخازن", 3, [
        _e(EXT, FIXED, "", 2),
        _e(EXT, PTZ),
    ]),
    # في الشجرة: "خلف المبنى: 1" يلي بعد سطر الـPTZ، فنربطه بالكاميرا المتحركة
    ("إدارة الرافع", 5, [
        _e(EXT, FIXED, "", 4),
        _e(EXT, PTZ, "خلف المبنى"),
    ]),
    ("بوابة المهبط", 1, [
        _e(EXT, FIXED, "البوابة"),
    ]),
    ("سور الرصيف الغربي", 2, [
        _e(INT, FIXED, "أول السور"),
        _e(EXT, PTZ, "على البرج"),
    ]),
    ("الحارات", 2, [
        _e(EXT, FIXED, "", 2),
    ]),
    ("الطبلية", 1, [
        _e(EXT, FIXED),
    ]),
    ("الاحتياطي المتاح", 7, [
        _e(None, PTZ, "كاميرات متحركة احتياطي", 2, "احتياطي"),
        _e(None, None, "كاميرات خارج القطاع للصيانة", 5, "تحت الصيانة"),
    ]),
]


def building_name_for(location):
    """اسم المبنى في جدول buildings المقابل لاسم الموقع في الشجرة."""
    return BUILDING_ALIASES.get(location, location)


def validate_tree():
    """يتأكد أن مجموع مدخلات كل موقع = الإجمالي المكتوب. يرجع قائمة الأخطاء."""
    errors = []

    for name, total, entries in CAMERA_TREE:
        actual = sum(e[3] for e in entries)

        if actual != total:
            errors.append(f"{name}: المكتوب {total} والمحسوب {actual}")

    return errors


def expand_tree():
    """يفرد الشجرة إلى كاميرا لكل صف، بأسماء مميزة وثابتة."""
    rows = []

    for location, _total, entries in CAMERA_TREE:
        for placement, kind, detail, count, status in entries:
            label = " ".join(p for p in (placement, kind) if p)

            for index in range(1, count + 1):
                parts = [location]

                if label:
                    parts.append(label)

                if detail:
                    parts.append(detail)

                name = " — ".join(parts)

                if count > 1:
                    name += f" ({index})"

                rows.append({
                    "location": location,
                    "placement": placement,
                    "camera_type": kind,
                    "detail": detail,
                    "status": status,
                    "model": DEFAULT_MODEL,
                    "name": name,
                })

    return rows


if __name__ == "__main__":
    problems = validate_tree()
    print("أخطاء:", problems or "لا يوجد")
    rows = expand_tree()
    print("إجمالي الكاميرات:", len(rows))
    print("أسماء مكررة:", len(rows) - len({r["name"] for r in rows}))