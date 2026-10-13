"""
org_cache.py
============
Singleton لبيانات الهيكل التنظيمي — يُحمَّل مرة واحدة ويُرسل إشارة
لكل الشاشات المشتركة عند أي تعديل (إضافة / تعديل / حذف / تفعيل).

الاستخدام:
----------
    from ui.org_cache import OrgStructureCache

    cache = OrgStructureCache.instance()

    # الاتصال بالإشارة (في __init__ أي شاشة):
    cache.data_changed.connect(self.refresh_org_data)

    # جلب البيانات:
    units = cache.get_units()
    actives = cache.get_active_units()
    by_type = cache.get_units_by_type("فرع")

    # إبطال الكاش وإشعار الجميع:
    cache.invalidate()
"""

from __future__ import annotations

import threading
from typing import ClassVar

from PySide6.QtCore import QObject, Signal

from database import get_connection


class OrgStructureCache(QObject):
    """
    Singleton يحتفظ ببيانات dbo.org_units في الذاكرة.

    - data_changed  تُطلَق فور استدعاء invalidate().
    - _units        قائمة القواميس الخام (أو None لو الكاش فارغ).
    - Thread-safe   عبر threading.Lock.
    """

    data_changed = Signal()

    _instance: ClassVar["OrgStructureCache | None"] = None
    _class_lock: ClassVar[threading.Lock] = threading.Lock()

    def __new__(cls) -> "OrgStructureCache":
        with cls._class_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        super().__init__()
        self._units: "list[dict] | None" = None
        self._data_lock = threading.Lock()
        self._initialized = True

    @classmethod
    def instance(cls) -> "OrgStructureCache":
        """أعِد الـ Singleton (أو أنشئه لأول مرة)."""
        return cls()

    def _load(self) -> "list[dict]":
        """جلب كل الوحدات من قاعدة البيانات."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    o.id,
                    o.name,
                    o.unit_type,
                    o.parent_id,
                    o.is_active,
                    p.name AS parent_name
                FROM dbo.org_units o
                LEFT JOIN dbo.org_units p ON p.id = o.parent_id
                ORDER BY o.sort_order, o.unit_type, o.name
            """)
            return [dict(row.items()) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_units(self) -> "list[dict]":
        """
        أعِد كل وحدات الهيكل التنظيمي.

        يُحمَّل من قاعدة البيانات أول مرة فقط، ثم يُعاد من الذاكرة.
        في حالة فشل الاتصال يعيد قائمة فارغة بدون استثناء.
        """
        with self._data_lock:
            if self._units is None:
                try:
                    self._units = self._load()
                except Exception:
                    return []
            return list(self._units)

    def get_active_units(self) -> "list[dict]":
        """أعِد الوحدات النشطة فقط (is_active = 1)."""
        return [u for u in self.get_units() if u.get("is_active")]

    def get_units_by_type(self, unit_type: str) -> "list[dict]":
        """أعِد الوحدات النشطة من نوع محدد."""
        return [
            u for u in self.get_active_units()
            if u.get("unit_type") == unit_type
        ]

    def get_unit_by_id(self, unit_id: int) -> "dict | None":
        """ابحث عن وحدة بـ ID محدد."""
        for unit in self.get_units():
            if unit.get("id") == unit_id:
                return unit
        return None

    def get_active_by_types(self, *types: str) -> "list[dict]":
        """أعِد الوحدات النشطة من أنواع متعددة."""
        type_set = set(types)
        return [
            u for u in self.get_active_units()
            if u.get("unit_type") in type_set
        ]

    def invalidate(self) -> None:
        """
        أبطل الكاش وأعلم كل المشتركين بالتغيير.

        استدعِ هذه الدالة بعد كل عملية إضافة/تعديل/حذف/تفعيل
        في شاشة الهيكل التنظيمي.
        """
        with self._data_lock:
            self._units = None
        self.data_changed.emit()

    def preload(self) -> None:
        """
        حمّل البيانات مسبقاً (اختياري للأداء).
        استدعِ بعد تسجيل الدخول مباشرةً.
        """
        self.get_units()
