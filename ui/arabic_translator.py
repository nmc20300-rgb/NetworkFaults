"""
ui/arabic_translator.py
========================
مترجم ومُعرّب النظام الشامل
يعرّب كافة أزرار وخيارات النوافذ المنبثقة ومربعات الحوار (QMessageBox, QDialogButtonBox, QFileDialog, etc.)
عبر كامل شاشات النظام دون استثناء.
"""

import os
from PySide6.QtCore import QTranslator, QLibraryInfo, Qt
from PySide6.QtWidgets import QApplication

# ─────────────────────────────────────────────────────────────
# قاموس تعريب خيارات النوافذ المنبثقة والأزرار القياسية
# ─────────────────────────────────────────────────────────────

ARABIC_DIALOG_MAP = {
    # الأزرار الأساسية الشائعة
    "OK": "موافق",
    "&OK": "موافق",
    "Ok": "موافق",
    "&Ok": "موافق",
    "Cancel": "إلغاء",
    "&Cancel": "إلغاء",
    "Yes": "نعم",
    "&Yes": "نعم",
    "No": "لا",
    "&No": "لا",
    "Save": "حفظ",
    "&Save": "حفظ",
    "Open": "فتح",
    "&Open": "فتح",
    "Close": "إغلاق",
    "&Close": "إغلاق",
    "Apply": "تطبيق",
    "&Apply": "تطبيق",
    "Reset": "إعادة تعيين",
    "&Reset": "إعادة تعيين",
    "Discard": "تجاهل",
    "&Discard": "تجاهل",
    "Don't Save": "عدم الحفظ",
    "&Don't Save": "عدم الحفظ",
    "Do not save": "عدم الحفظ",
    "&Do not save": "عدم الحفظ",
    "Save All": "حفظ الكل",
    "&Save All": "حفظ الكل",
    "Restore Defaults": "استعادة الافتراضي",
    "&Restore Defaults": "استعادة الافتراضي",
    "Abort": "إلغاء الأمر",
    "&Abort": "إلغاء الأمر",
    "Retry": "إعادة المحاولة",
    "&Retry": "إعادة المحاولة",
    "Ignore": "تجاهل",
    "&Ignore": "تجاهل",
    "Help": "مساعدة",
    "&Help": "مساعدة",
    "Yes to All": "نعم للكل",
    "&Yes to All": "نعم للكل",
    "No to All": "لا للكل",
    "&No to All": "لا للكل",
    "Show Details...": "عرض التفاصيل...",
    "&Show Details...": "عرض التفاصيل...",
    "Hide Details...": "إخفاء التفاصيل...",
    "&Hide Details...": "إخفاء التفاصيل...",

    # تصحيح تعريبات Qt الافتراضية الرسمية (التي تستخدم كلمات تراثية غير شائعة في البرمجيات)
    "حَسَنًا": "موافق",
    "حسناً": "موافق",
    "حسنا": "موافق",
    "ألغِ": "إلغاء",
    "إلغِ": "إلغاء",
    "احفظ": "حفظ",
    "اغلق": "إغلاق",
    "افتح": "فتح",
    "ارفض": "تجاهل",
    "&نعم": "نعم",
    "&لا": "لا",

    # عناوين الحوارات القياسية
    "Information": "معلومات",
    "Warning": "تنبيه",
    "Critical": "خطأ",
    "Question": "تأكيد",
    "Error": "خطأ",
    "About": "حول النظام",

    # مربعات حوار الملفات (QFileDialog)
    "Look in:": "البحث في:",
    "&Look in:": "البحث في:",
    "File name:": "اسم الملف:",
    "File &name:": "اسم الملف:",
    "Files of type:": "نوع الملفات:",
    "Files of &type:": "نوع الملفات:",
    "Directory:": "المجلد:",
    "&Directory:": "المجلد:",
    "Folder": "مجلد",
    "&Folder:": "المجلد:",
    "Choose": "اختيار",
    "Select Folder": "تحديد مجلد",
    "Create New Folder": "إنشاء مجلد جديد",
    "New Folder": "مجلد جديد",
    "All Files (*)": "كافة الملفات (*)",
    "All Files (*.*)": "كافة الملفات (*.*)",
    "Find Directory": "تحديد المجلد",
    "Open Directory": "فتح المجلد",
    "Save As": "حفظ باسم",
    "Open File": "فتح ملف",
    "Save File": "حفظ ملف",
    "Recent Places": "الأماكن الأخيرة",

    # مربعات حوار الإدخال (QInputDialog)
    "Select": "تحديد",
    "&Select": "تحديد",
}


class SystemArabicTranslator(QTranslator):
    """مترجم ديناميكي يترجم كل نصوص الأزرار وخيارات النوافذ المنبثقة إلى العربية."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def translate(self, context, sourceText, disambiguation="", n=-1):
        # 1. مطابقة مباشرة
        if sourceText in ARABIC_DIALOG_MAP:
            return ARABIC_DIALOG_MAP[sourceText]

        # 2. مطابقة بعد إزالة رمز الاختصار &
        cleaned = sourceText.replace("&", "").strip()
        if cleaned in ARABIC_DIALOG_MAP:
            return ARABIC_DIALOG_MAP[cleaned]

        return super().translate(context, sourceText, disambiguation, n)


# الاحتفاظ بمراجع المترجمين لمنع تنظيفهم بواسطة Garbage Collector
_INSTALLED_TRANSLATORS = []


def setup_arabic_localization(app: QApplication):
    """
    تطبيق التعريب الشامل على مستوى التطبيق:
    - تحميل ملفات ترجمة Qt الأساسية العربية (للقوائم، التقويمات، إلخ).
    - تثبيت المترجم المخصص لتعريب جميع الأزرار والخيارات (موافق، إلغاء، نعم، لا، حفظ، إلخ).
    - تعيين اتجاه التطبيق بالكامل من اليمين إلى اليسار (Right-To-Left).
    """
    global _INSTALLED_TRANSLATORS

    # 1. تعيين اتجاه التطبيق بالكامل
    app.setLayoutDirection(Qt.RightToLeft)

    # 2. تحميل الترجمة العربية الرسمية لـ Qt إن وُجدت (للقوائم والتقويمات)
    trans_dir = QLibraryInfo.path(QLibraryInfo.TranslationsPath)
    if os.path.exists(trans_dir):
        base_trans = QTranslator(app)
        if base_trans.load("qtbase_ar.qm", trans_dir):
            app.installTranslator(base_trans)
            _INSTALLED_TRANSLATORS.append(base_trans)

        qt_trans = QTranslator(app)
        if qt_trans.load("qt_ar.qm", trans_dir):
            app.installTranslator(qt_trans)
            _INSTALLED_TRANSLATORS.append(qt_trans)

    # 3. تثبيت المترجم المخصص (يتم تثبيته آخراً ليكون له أعلى أولوية)
    custom_trans = SystemArabicTranslator(app)
    app.installTranslator(custom_trans)
    _INSTALLED_TRANSLATORS.append(custom_trans)
