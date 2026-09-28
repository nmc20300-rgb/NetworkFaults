"""
ui/org_structure_page.py
========================
شاشة إدارة الهيكل التنظيمي
متاحة فقط لـ SUPER_ADMIN و ADMIN
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QDialog, QFormLayout, QLineEdit,
    QComboBox, QMessageBox, QFrame, QAbstractItemView,
    QWizard, QWizardPage, QCompleter, QFileDialog,
)
from PySide6.QtCore import Qt, QSize, QStringListModel, QTimer
from PySide6.QtGui import QColor, QFont
from pathlib import Path
from database import get_connection, write_audit_log


def org_unit_audit_data(unit, all_units=None):
    """Build a readable, JSON-friendly snapshot of an organization unit."""
    if not unit:
        return {}

    parent_id = unit.get("parent_id")
    parent_name = unit.get("parent_name")
    if parent_id is None:
        parent_name = "— (عنصر رئيسي)"
    elif not parent_name:
        parent = next(
            (candidate for candidate in (all_units or [])
             if candidate.get("id") == parent_id),
            None,
        )
        parent_name = parent.get("name") if parent else "غير معروف"

    return {
        "id": unit.get("id"),
        "name": unit.get("name"),
        "unit_type": unit.get("unit_type"),
        "parent_id": parent_id,
        "parent_name": parent_name,
        "is_active": bool(unit.get("is_active", True)),
    }


# ─────────────────────────────────────────────────────────────
# Dialog: Add / Edit Org Unit
# ─────────────────────────────────────────────────────────────

class _OrgUnitDetailsPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard

    def validatePage(self):
        if not self.wizard.name_input.text().strip():
            QMessageBox.warning(
                self,
                "تحقق من البيانات",
                "اكتب اسم الوحدة قبل الانتقال للخطوة التالية.",
            )
            self.wizard.name_input.setFocus()
            return False
        return True


class OrgUnitDialog(QWizard):

    UNIT_TYPES = ["فرع", "مبنى", "قسم", "مكتب"]
    STEP_NAMES = ["نوع الوحدة", "البيانات", "مراجعة"]

    def __init__(self, parent=None, unit=None, all_units=None):
        super().__init__(parent)
        self.unit = unit
        self.all_units = all_units or []
        is_edit = unit is not None

        self.setWindowTitle(
            "تعديل عنصر في الهيكل" if is_edit else "إضافة عنصر للهيكل التنظيمي"
        )
        self.setMinimumSize(620, 560)
        self.resize(720, 610)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.NoBackButtonOnStartPage, True)
        self.setButtonText(QWizard.BackButton, "السابق")
        self.setButtonText(QWizard.NextButton, "التالي")
        self.setButtonText(QWizard.CancelButton, "إلغاء")
        self.setButtonText(QWizard.FinishButton, "حفظ العنصر")

        self._build_pages(is_edit)
        self._populate_parent_combo()

        if is_edit:
            self._load_unit()

        self.currentIdChanged.connect(self._update_review)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self.name_input.textChanged.connect(self._update_review)
        self.parent_combo.currentTextChanged.connect(self._update_review)
        self._update_review()

        self.setStyleSheet("""
            QWizard { background: #f4f7fb; }
            QWizardPage { background: transparent; }
            QLabel#dialogTitle { color: #0f2338; font-size: 19px; font-weight: 800; }
            QLabel#dialogHint { color: #64748b; font-size: 12px; }
            QFrame#wizardCard {
                background: white; border: 1px solid #e2e8f0; border-radius: 12px;
            }
            QFrame#stepBar { background: transparent; }
            QLabel#stepItem {
                background: #eef2f7; color: #64748b; border-radius: 9px;
                padding: 9px 12px; font-weight: 700;
            }
            QLabel#stepItem[stepState="active"] {
                background: #e0f2fe; color: #0369a1; border: 1px solid #7dd3fc;
            }
            QLabel#stepItem[stepState="done"] {
                background: #ecfdf5; color: #047857;
            }
            QLineEdit, QComboBox {
                background: #fbfdff; border: 1px solid #cbd5e1;
                border-radius: 8px; padding: 8px 10px; min-height: 24px;
            }
            QLineEdit:focus, QComboBox:focus { border: 1.5px solid #0891b2; }
            QWizard QPushButton {
                background: #f1f5f9; color: #0f2338; border: 1px solid #cbd5e1;
                border-radius: 8px; padding: 8px 18px; font-weight: 700; min-width: 88px;
            }
            QWizard QPushButton:hover { background: #e2e8f0; }
        """)

    def _build_stepper(self, active_step):
        bar = QFrame()
        bar.setObjectName("stepBar")
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 4, 0, 10)
        row.setSpacing(8)
        for index, title in enumerate(self.STEP_NAMES):
            state = "done" if index < active_step else "active" if index == active_step else ""
            label = QLabel(f"{index + 1}  {title}")
            label.setObjectName("stepItem")
            label.setProperty("stepState", state)
            label.setAlignment(Qt.AlignCenter)
            row.addWidget(label, 1)
        return bar

    def _make_page_heading(self, title, hint):
        box = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("dialogTitle")
        hint_label = QLabel(hint)
        hint_label.setObjectName("dialogHint")
        box.addWidget(title_label)
        box.addWidget(hint_label)
        return box

    def _build_pages(self, is_edit):
        # Step 1 — choose the organizational unit type.
        type_page = QWizardPage()
        type_page.setTitle("نوع الوحدة")
        type_page.setSubTitle("ابدأ بتحديد نوع العنصر الذي تريد إضافته.")
        type_layout = QVBoxLayout(type_page)
        type_layout.setContentsMargins(8, 8, 8, 8)
        type_layout.addWidget(self._build_stepper(0))
        type_layout.addLayout(self._make_page_heading(
            "ما نوع الوحدة؟",
            "اختيار النوع يحدد مكان الوحدة في الهيكل والجهة التي يمكن أن تتبع لها.",
        ))

        type_card = QFrame()
        type_card.setObjectName("wizardCard")
        card_layout = QVBoxLayout(type_card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(12)
        card_layout.addWidget(QLabel("نوع العنصر التنظيمي *"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.UNIT_TYPES)
        self.type_combo.setMinimumHeight(42)
        card_layout.addWidget(self.type_combo)
        self.type_hint = QLabel()
        self.type_hint.setObjectName("dialogHint")
        self.type_hint.setWordWrap(True)
        card_layout.addWidget(self.type_hint)
        card_layout.addStretch()
        type_layout.addWidget(type_card, 1)
        self.type_page_id = self.addPage(type_page)

        # Step 2 — enter the unit name and parent.
        self.details_page = _OrgUnitDetailsPage(self)
        self.details_page.setTitle("بيانات الوحدة")
        self.details_page.setSubTitle("أدخل الاسم وحدد موقع الوحدة ضمن الهيكل.")
        details_layout = QVBoxLayout(self.details_page)
        details_layout.setContentsMargins(8, 8, 8, 8)
        details_layout.addWidget(self._build_stepper(1))
        details_layout.addLayout(self._make_page_heading(
            "أكمل البيانات الأساسية",
            "يمكنك الرجوع للخطوة السابقة لتغيير نوع الوحدة.",
        ))

        details_card = QFrame()
        details_card.setObjectName("wizardCard")
        form = QFormLayout(details_card)
        form.setContentsMargins(20, 20, 20, 20)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(16)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: فرع وسط البلد")
        self.name_input.setMinimumHeight(42)
        self.parent_combo = QComboBox()
        self.parent_combo.setMinimumHeight(42)
        form.addRow("اسم الوحدة *", self.name_input)
        form.addRow("تابعة إلى", self.parent_combo)
        details_layout.addWidget(details_card)
        details_layout.addStretch()
        self.details_page_id = self.addPage(self.details_page)

        # Step 3 — review before saving.
        review_page = QWizardPage()
        review_page.setTitle("مراجعة وحفظ")
        review_page.setSubTitle("تأكد من البيانات قبل إضافتها إلى الهيكل.")
        review_layout = QVBoxLayout(review_page)
        review_layout.setContentsMargins(8, 8, 8, 8)
        review_layout.addWidget(self._build_stepper(2))
        review_layout.addLayout(self._make_page_heading(
            "راجع ملخص الوحدة",
            "إذا احتجت إلى تعديل أي معلومة، ارجع إلى الخطوة المناسبة.",
        ))

        review_card = QFrame()
        review_card.setObjectName("wizardCard")
        review_form = QFormLayout(review_card)
        review_form.setContentsMargins(20, 20, 20, 20)
        review_form.setHorizontalSpacing(16)
        review_form.setVerticalSpacing(16)
        self.review_name = QLabel("—")
        self.review_type = QLabel("—")
        self.review_parent = QLabel("—")
        for label in (self.review_name, self.review_type, self.review_parent):
            label.setStyleSheet("font-weight: 700; color: #0f2338;")
            label.setWordWrap(True)
        review_form.addRow("اسم الوحدة", self.review_name)
        review_form.addRow("النوع", self.review_type)
        review_form.addRow("تابعة إلى", self.review_parent)
        review_layout.addWidget(review_card)
        review_layout.addStretch()
        self.review_page_id = self.addPage(review_page)

    def _parent_label_for_id(self, parent_id):
        if parent_id is None:
            return "بدون وحدة أعلى (عنصر رئيسي)"
        for unit in self.all_units:
            if unit["id"] == parent_id:
                return f"{unit['name']} — {unit['unit_type']}"
        return "بدون وحدة أعلى"

    def _update_review(self, *_args):
        if not hasattr(self, "type_combo"):
            return
        unit_type = self.type_combo.currentText()
        hints = {
            "فرع": "الفرع وحدة رئيسية، ولا يحتاج إلى اختيار عنصر أعلى.",
            "مبنى": "المبنى وحدة رئيسية، ولا يحتاج إلى اختيار عنصر أعلى.",
            "قسم": "يمكن ربط القسم بفرع أو مبنى أو قسم أعلى.",
            "مكتب": "يمكن ربط المكتب بفرع أو مبنى أو قسم.",
        }
        self.type_hint.setText(hints.get(unit_type, ""))
        self.review_name.setText(self.name_input.text().strip() or "—")
        self.review_type.setText(unit_type or "—")
        self.review_parent.setText(
            self._parent_label_for_id(self.parent_combo.currentData())
        )

    def _populate_parent_combo(self):
        if not hasattr(self, "parent_combo"):
            return
        previous_parent = self.parent_combo.currentData()
        self.parent_combo.clear()
        self.parent_combo.addItem("— بدون وحدة أعلى —", None)
        current_type = self.type_combo.currentText()

        if current_type in ("فرع", "مبنى"):
            self.parent_combo.setEnabled(False)
            return

        self.parent_combo.setEnabled(True)
        exclude_ids = set()
        if self.unit:
            exclude_ids.add(self.unit["id"])
            children = {}
            for unit in self.all_units:
                children.setdefault(unit.get("parent_id"), []).append(unit["id"])
            stack = list(children.get(self.unit["id"], []))
            while stack:
                child_id = stack.pop()
                if child_id in exclude_ids:
                    continue
                exclude_ids.add(child_id)
                stack.extend(children.get(child_id, []))

        for unit in self.all_units:
            if unit["id"] in exclude_ids:
                continue
            if unit["unit_type"] in ("فرع", "مبنى", "قسم"):
                self.parent_combo.addItem(
                    f"[{unit['unit_type']}]  {unit['name']}",
                    unit["id"],
                )

        idx = self.parent_combo.findData(previous_parent)
        if idx >= 0:
            self.parent_combo.setCurrentIndex(idx)

    def _on_type_changed(self, _unit_type):
        self._populate_parent_combo()
        self._update_review()

    def _load_unit(self):
        unit = self.unit
        self.name_input.setText(unit.get("name") or "")
        idx = self.type_combo.findText(unit.get("unit_type") or "")
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self._populate_parent_combo()
        parent_idx = self.parent_combo.findData(unit.get("parent_id"))
        if parent_idx >= 0:
            self.parent_combo.setCurrentIndex(parent_idx)
        self._update_review()

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "unit_type": self.type_combo.currentText(),
            "parent_id": self.parent_combo.currentData(),
        }


# ─────────────────────────────────────────────────────────────
# OrgStructurePage
# ─────────────────────────────────────────────────────────────

class OrgStructurePage(QWidget):

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user or {}
        self._quick_label_to_id = {}
        self._quick_label_by_id = {}
        self._tree_items_by_id = {}
        self.setLayoutDirection(Qt.RightToLeft)
        self.setObjectName("orgPage")
        self._build_ui()
        self.load_units()

    # ─────────────── UI ─────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(14)

        # Page heading and primary action.
        title_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        title = QLabel("إدارة الهيكل التنظيمي")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "استكشف الفروع والمباني والأقسام والمكاتب في عرض هرمي واضح"
        )
        subtitle.setObjectName("pageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        title_row.addLayout(title_box)
        title_row.addStretch()

        self.btn_export = QPushButton("تصدير إلى Excel")
        self.btn_export.setObjectName("toolButton")
        self.btn_export.setMinimumHeight(42)
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.clicked.connect(self._export_excel)
        title_row.addWidget(self.btn_export)

        self.btn_add = QPushButton("＋  إضافة وحدة")
        self.btn_add.setObjectName("primaryButton")
        self.btn_add.setMinimumHeight(42)
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.clicked.connect(self._add_unit)
        title_row.addWidget(self.btn_add)
        layout.addLayout(title_row)

        # Compact overview cards.
        metrics = QHBoxLayout()
        metrics.setSpacing(10)
        self.metric_total = self._metric_card("إجمالي الوحدات", "0")
        self.metric_active = self._metric_card("وحدات نشطة", "0")
        self.metric_inactive = self._metric_card("وحدات معطلة", "0")
        metrics.addWidget(self.metric_total[0], 1)
        metrics.addWidget(self.metric_active[0], 1)
        metrics.addWidget(self.metric_inactive[0], 1)
        layout.addLayout(metrics)

        # Search and filters in one calm toolbar.
        filter_card = QFrame()
        filter_card.setObjectName("filterCard")
        filter_row = QHBoxLayout(filter_card)
        filter_row.setContentsMargins(14, 12, 14, 12)
        filter_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchBox")
        self.search_input.setPlaceholderText("ابحث باسم الفرع أو الوحدة...")
        self.search_input.setMinimumHeight(38)
        self.search_input.textChanged.connect(self.load_units)

        self.filter_type = QComboBox()
        self.filter_type.addItem("كل الأنواع", "")
        for unit_type in ("فرع", "مبنى", "قسم", "مكتب"):
            self.filter_type.addItem(unit_type, unit_type)
        self.filter_type.setMinimumHeight(38)
        self.filter_type.currentIndexChanged.connect(self.load_units)

        self.filter_status = QComboBox()
        self.filter_status.addItem("كل الحالات", "")
        self.filter_status.addItem("نشط فقط", "1")
        self.filter_status.addItem("غير نشط فقط", "0")
        self.filter_status.setCurrentIndex(1)
        self.filter_status.setMinimumHeight(38)
        self.filter_status.currentIndexChanged.connect(self.load_units)

        clear_button = QPushButton("مسح الفلاتر")
        clear_button.setObjectName("clearButton")
        clear_button.setMinimumHeight(38)
        clear_button.clicked.connect(self._clear_filters)

        filter_row.addWidget(QLabel("بحث"))
        filter_row.addWidget(self.search_input, 1)
        filter_row.addWidget(QLabel("النوع"))
        filter_row.addWidget(self.filter_type)
        filter_row.addWidget(QLabel("الحالة"))
        filter_row.addWidget(self.filter_status)
        filter_row.addWidget(clear_button)
        layout.addWidget(filter_card)

        # Hierarchical browser: collapsed levels keep long lists manageable.
        tree_card = QFrame()
        tree_card.setObjectName("treeCard")
        tree_layout = QVBoxLayout(tree_card)
        tree_layout.setContentsMargins(10, 10, 10, 10)
        tree_layout.setSpacing(8)

        tree_header = QHBoxLayout()
        tree_title = QLabel("الوحدات والعلاقات التنظيمية")
        tree_title.setObjectName("sectionTitle")
        tree_header.addWidget(tree_title)
        tree_header.addStretch()

        self.quick_search = QLineEdit()
        self.quick_search.setObjectName("quickSearch")
        self.quick_search.setPlaceholderText("بحث سريع داخل الشجرة…")
        self.quick_search.setClearButtonEnabled(True)
        self.quick_search.setMinimumWidth(230)
        self.quick_search.setToolTip("اكتب اسم الوحدة أو مسارها، ثم اختر النتيجة للانتقال إليها")
        self.quick_search_model = QStringListModel([], self)
        self.quick_search_completer = QCompleter(self.quick_search_model, self)
        self.quick_search_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.quick_search_completer.setFilterMode(Qt.MatchContains)
        self.quick_search_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.quick_search.setCompleter(self.quick_search_completer)
        self.quick_search_completer.activated[str].connect(self._on_quick_completion)
        self.quick_search.returnPressed.connect(self._quick_find_unit)
        tree_header.addWidget(self.quick_search)

        self.quick_find_button = QPushButton("انتقال")
        self.quick_find_button.setObjectName("toolButton")
        self.quick_find_button.clicked.connect(self._quick_find_unit)
        tree_header.addWidget(self.quick_find_button)

        root_legend = QLabel("◆ رئيسي — التوابع أسفلها")
        root_legend.setObjectName("rootLegend")
        tree_header.addWidget(root_legend)
        self.btn_collapse = QPushButton("طي الكل")
        self.btn_collapse.setObjectName("toolButton")
        self.btn_collapse.clicked.connect(self._collapse_all)
        self.btn_expand = QPushButton("توسيع الكل")
        self.btn_expand.setObjectName("toolButton")
        self.btn_expand.clicked.connect(self._expand_all)
        tree_header.addWidget(self.btn_collapse)
        tree_header.addWidget(self.btn_expand)
        tree_layout.addLayout(tree_header)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels([
            "الوحدة التنظيمية", "النوع", "الحالة", "عدد العناصر التابعة", "الإجراءات",
        ])
        self.tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(22)
        self.tree.setAnimated(True)
        self.tree.setUniformRowHeights(False)
        self.tree.setAllColumnsShowFocus(True)
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        tree_layout.addWidget(self.tree, 1)

        self.stats_lbl = QLabel("")
        self.stats_lbl.setObjectName("statsLabel")
        tree_layout.addWidget(self.stats_lbl)
        layout.addWidget(tree_card, 1)

        self.setStyleSheet("""
            #orgPage { background: #f4f7fb; }
            #pageTitle { color: #0f2338; font-size: 23px; font-weight: 800; }
            #pageSubtitle { color: #64748b; font-size: 12px; }
            #filterCard, #treeCard, #metricCard {
                background: white; border: 1px solid #e2e8f0; border-radius: 12px;
            }
            #metricTitle { color: #64748b; font-size: 11px; font-weight: 700; }
            #metricValue { color: #0f2338; font-size: 23px; font-weight: 800; }
            #sectionTitle { color: #0f2338; font-size: 14px; font-weight: 800; }
            #rootLegend { background: #fff7ed; color: #9a3412; border-radius: 8px; padding: 5px 9px; font-size: 11px; font-weight: 700; }
            QWidget#rootActionCell { background: #fff7ed; border-radius: 6px; }
            #statsLabel { color: #64748b; font-size: 11px; padding: 3px 6px; }
            QTreeWidget {
                background: white; border: none; gridline-color: #f1f5f9;
                selection-background-color: #e0f2fe; selection-color: #0f2338;
                alternate-background-color: #f8fafc; outline: none;
            }
            QTreeWidget::item { padding: 3px 7px; border-bottom: 1px solid #f1f5f9; }
            QTreeWidget::item:hover { background: #f0f9ff; }
            QHeaderView::section {
                background: #f8fafc; color: #0f2338; padding: 10px 8px;
                border: none; border-bottom: 2px solid #0891b2; font-weight: 700;
            }
            QLineEdit, QComboBox {
                background: #fbfdff; border: 1px solid #cbd5e1;
                border-radius: 8px; padding: 7px 10px; min-width: 115px;
            }
            QLineEdit#quickSearch { min-width: 230px; background: white; }
            QLineEdit:focus, QComboBox:focus { border: 1.5px solid #0891b2; }
            QPushButton#primaryButton {
                background: #0891b2; color: white; border: none;
                border-radius: 9px; padding: 9px 17px; font-weight: 700;
            }
            QPushButton#primaryButton:hover { background: #0e7490; }
            QPushButton#toolButton, QPushButton#clearButton {
                background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1;
                border-radius: 8px; padding: 6px 11px; font-weight: 700;
            }
            QPushButton#toolButton:hover, QPushButton#clearButton:hover { background: #e2e8f0; }
            QPushButton#editBtn, QPushButton#deleteBtn {
                border-radius: 7px; padding: 3px 9px; font-size: 11px; font-weight: 700;
                min-height: 30px;
            }
            QPushButton#editBtn { background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; }
            QPushButton#editBtn:hover { background: #dbeafe; }
            QPushButton#deleteBtn { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
            QPushButton#deleteBtn:hover { background: #fee2e2; }
        """)

    def _metric_card(self, title, value):
        card = QFrame()
        card.setObjectName("metricCard")
        box = QVBoxLayout(card)
        box.setContentsMargins(15, 11, 15, 11)
        box.setSpacing(3)
        title_label = QLabel(title)
        title_label.setObjectName("metricTitle")
        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        box.addWidget(title_label)
        box.addWidget(value_label)
        return card, value_label

    def _clear_filters(self):
        self.search_input.blockSignals(True)
        self.filter_type.blockSignals(True)
        self.filter_status.blockSignals(True)
        self.search_input.clear()
        self.filter_type.setCurrentIndex(0)
        self.filter_status.setCurrentIndex(1)
        self.search_input.blockSignals(False)
        self.filter_type.blockSignals(False)
        self.filter_status.blockSignals(False)
        self.load_units()

    def _expand_all(self):
        self.tree.expandAll()

    def _collapse_all(self):
        self.tree.collapseAll()

    # ─────────────── Load ────────────────────────────────────

    def _show_toast(self, message, duration_ms=3200):
        if not hasattr(self, "_toast_label"):
            self._toast_label = QLabel(self)
            self._toast_label.setObjectName("successToast")
            self._toast_label.setAlignment(Qt.AlignCenter)
            self._toast_label.setWordWrap(True)
            self._toast_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self._toast_label.setContentsMargins(16, 9, 16, 9)
            self._toast_label.setMinimumHeight(42)
            self._toast_label.setStyleSheet(
                "QLabel#successToast { background: #166534; color: white; "
                "border: 1px solid #14532d; border-radius: 11px; "
                "font-size: 12px; font-weight: 700; padding: 9px 16px; }"
            )
            self._toast_timer = QTimer(self)
            self._toast_timer.setSingleShot(True)
            self._toast_timer.timeout.connect(self._toast_label.hide)

        max_width = max(200, min(520, self.width() - 32))
        self._toast_label.setMinimumWidth(min(240, max_width))
        self._toast_label.setMaximumWidth(max_width)
        self._toast_label.setText(message)
        self._toast_label.adjustSize()
        x = max(16, (self.width() - self._toast_label.width()) // 2)
        y = max(16, self.height() - self._toast_label.height() - 24)
        self._toast_label.move(x, y)
        self._toast_label.show()
        self._toast_label.raise_()
        self._toast_timer.start(duration_ms)

    def _unit_path(self, unit, units_by_id):
        names = []
        current = unit
        visited = set()
        while current:
            unit_id = current.get("id")
            if unit_id in visited:
                break
            visited.add(unit_id)
            names.append(current.get("name") or "(بدون اسم)")
            current = units_by_id.get(current.get("parent_id"))
        return " / ".join(reversed(names))

    def _refresh_quick_search_model(self, units_by_id):
        self._quick_label_to_id = {}
        self._quick_label_by_id = {}
        labels = []
        for unit in self._all_units:
            path = self._unit_path(unit, units_by_id)
            label = f"{path}  [{unit.get('unit_type') or 'وحدة'}]"
            if label.casefold() in self._quick_label_to_id:
                label = f"{label}  · {unit['id']}"
            self._quick_label_to_id[label.casefold()] = unit["id"]
            self._quick_label_by_id[unit["id"]] = label
            labels.append(label)
        self.quick_search_model.setStringList(labels)

    def _on_quick_completion(self, label):
        unit_id = self._quick_label_to_id.get(str(label).casefold())
        if unit_id is not None:
            self._navigate_to_unit(unit_id)

    def _quick_find_unit(self):
        query = self.quick_search.text().strip().casefold()
        if not query:
            return

        unit_id = self._quick_label_to_id.get(query)
        if unit_id is not None:
            self._navigate_to_unit(unit_id)
            return

        exact = [u for u in self._all_units if (u.get("name") or "").casefold() == query]
        candidates = exact or [
            u for u in self._all_units
            if (u.get("name") or "").casefold().startswith(query)
        ]
        if not candidates:
            candidates = [
                u for u in self._all_units
                if query in (u.get("name") or "").casefold()
            ]

        if not candidates:
            QMessageBox.information(
                self,
                "لا توجد نتيجة",
                "لم يتم العثور على وحدة بهذا الاسم.",
            )
            return

        if len(candidates) > 1:
            self.quick_search.setFocus()
            self.quick_search.setToolTip(
                "وجدت أكثر من وحدة مطابقة؛ اختر المسار الصحيح من قائمة الاقتراحات."
            )
            self.quick_search_completer.complete()
            return

        self._navigate_to_unit(candidates[0]["id"])

    def _navigate_to_unit(self, unit_id):
        # Preserve current filters unless they hide the requested unit.
        if unit_id not in self._tree_items_by_id:
            self.search_input.blockSignals(True)
            self.filter_type.blockSignals(True)
            self.filter_status.blockSignals(True)
            self.search_input.clear()
            self.filter_type.setCurrentIndex(0)
            self.filter_status.setCurrentIndex(0)
            self.search_input.blockSignals(False)
            self.filter_type.blockSignals(False)
            self.filter_status.blockSignals(False)
            self.load_units()

        item = self._tree_items_by_id.get(unit_id)
        if item is None:
            QMessageBox.information(
                self,
                "تعذر الوصول",
                "لم أتمكن من إظهار الوحدة في الشجرة.",
            )
            return

        parent = item.parent()
        while parent is not None:
            parent.setExpanded(True)
            parent = parent.parent()
        if item.childCount():
            item.setExpanded(True)

        self.tree.setCurrentItem(item, 0)
        self.tree.scrollToItem(item, QAbstractItemView.PositionAtCenter)
        self.tree.setFocus()
        self.quick_search.setText(
            self._quick_label_by_id.get(unit_id, "")
        )

    def load_units(self, *_args):
        search = self.search_input.text().strip().lower() if hasattr(self, "search_input") else ""
        type_filter = self.filter_type.currentData() if hasattr(self, "filter_type") else ""
        status_filter = self.filter_status.currentData() if hasattr(self, "filter_status") else "1"

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    o.id, o.name, o.unit_type, o.parent_id, o.is_active,
                    p.name AS parent_name
                FROM dbo.org_units o
                LEFT JOIN dbo.org_units p ON p.id = o.parent_id
                ORDER BY o.sort_order, o.unit_type, o.name
            """)
            fetched_units = cursor.fetchall()
            self._all_units = [dict(unit.items()) for unit in fetched_units]
        except Exception as error:
            QMessageBox.critical(self, "خطأ", f"تعذر تحميل البيانات:\n{error}")
            return
        finally:
            if conn is not None:
                conn.close()

        def matches(unit):
            if type_filter and unit["unit_type"] != type_filter:
                return False
            is_active = bool(unit["is_active"])
            if status_filter != "" and str(int(is_active)) != status_filter:
                return False
            if search and search not in (unit["name"] or "").lower():
                return False
            return True

        matched_ids = {unit["id"] for unit in self._all_units if matches(unit)}
        visible_ids = set(matched_ids)
        units_by_id = {unit["id"]: unit for unit in self._all_units}
        self._refresh_quick_search_model(units_by_id)

        # Keep matching units' ancestors visible for context in the hierarchy.
        for unit_id in list(matched_ids):
            current = units_by_id.get(unit_id)
            visited = set()
            while current and current.get("parent_id") in units_by_id:
                parent_id = current.get("parent_id")
                if parent_id in visited:
                    break
                visited.add(parent_id)
                visible_ids.add(parent_id)
                current = units_by_id[parent_id]

        self.tree.clear()
        tree_items = {}
        children_by_parent = {}
        for unit in self._all_units:
            children_by_parent.setdefault(unit.get("parent_id"), []).append(unit["id"])

        descendant_counts = {}

        def count_descendants(unit_id, trail=None):
            trail = set() if trail is None else trail
            if unit_id in trail:
                return 0
            if unit_id in descendant_counts:
                return descendant_counts[unit_id]
            next_trail = trail | {unit_id}
            count = 0
            for child_id in children_by_parent.get(unit_id, []):
                if child_id in next_trail:
                    continue
                count += 1 + count_descendants(child_id, next_trail)
            descendant_counts[unit_id] = count
            return count

        type_colors = {
            "فرع": ("#eff6ff", "#1e40af"),
            "مبنى": ("#f0fdf4", "#166534"),
            "قسم": ("#fefce8", "#854d0e"),
            "مكتب": ("#fdf4ff", "#7e22ce"),
        }

        for unit in self._all_units:
            unit_id = unit["id"]
            if unit_id not in visible_ids:
                continue
            is_root_unit = unit.get("parent_id") not in units_by_id
            display_name = unit.get("name") or "(بدون اسم)"
            if is_root_unit:
                display_name = f"◆ {display_name}  — وحدة رئيسية"
            item = QTreeWidgetItem([
                display_name,
                unit.get("unit_type") or "",
                "نشط ✓" if bool(unit.get("is_active")) else "معطل",
                str(count_descendants(unit_id)),
                "",
            ])
            if is_root_unit:
                root_font = QFont(item.font(0))
                root_font.setPointSize(11)
                root_font.setBold(True)
                item.setFont(0, root_font)
            item.setData(0, Qt.UserRole, unit_id)
            item.setSizeHint(0, QSize(0, 56))
            bg, fg = type_colors.get(unit.get("unit_type"), ("#f8fafc", "#334155"))
            item.setBackground(1, QColor(bg))
            item.setForeground(1, QColor(fg))
            item.setTextAlignment(1, Qt.AlignCenter)
            item.setTextAlignment(2, Qt.AlignCenter)
            item.setTextAlignment(3, Qt.AlignCenter)
            item.setForeground(3, QColor("#0369a1"))
            item.setToolTip(3, "عدد جميع العناصر التابعة، بكل المستويات والحالات")
            if not bool(unit.get("is_active")):
                item.setForeground(2, QColor("#991b1b"))
            else:
                item.setForeground(2, QColor("#166534"))
            tree_items[unit_id] = item

        # Attach all nodes first, so action widgets are installed on visible tree items.
        for unit in self._all_units:
            unit_id = unit["id"]
            item = tree_items.get(unit_id)
            if item is None:
                continue
            parent_item = tree_items.get(unit.get("parent_id"))
            if parent_item is not None:
                parent_item.addChild(item)
            else:
                self.tree.addTopLevelItem(item)

        for unit in self._all_units:
            unit_id = unit["id"]
            item = tree_items.get(unit_id)
            if item is None:
                continue
            unit_dict = dict(unit)
            actions = QWidget()
            action_layout = QHBoxLayout(actions)
            actions.setMinimumHeight(48)
            action_layout.setContentsMargins(5, 4, 5, 4)
            action_layout.setSpacing(5)
            action_layout.setAlignment(Qt.AlignVCenter)

            edit_button = QPushButton("تعديل")
            edit_button.setObjectName("editBtn")
            edit_button.setCursor(Qt.PointingHandCursor)
            edit_button.setMinimumHeight(32)
            edit_button.clicked.connect(
                lambda checked=False, ud=unit_dict: self._edit_unit(ud)
            )
            action_layout.addWidget(edit_button)

            delete_button = QPushButton("حذف")
            delete_button.setObjectName("deleteBtn")
            delete_button.setCursor(Qt.PointingHandCursor)
            delete_button.setMinimumHeight(32)
            delete_button.clicked.connect(
                lambda checked=False, ud=unit_dict: self._delete_unit(ud)
            )
            action_layout.addWidget(delete_button)
            if item.parent() is None:
                actions.setObjectName("rootActionCell")
            self.tree.setItemWidget(item, 4, actions)

        self._tree_items_by_id = tree_items

        # Highlight the full row of every top-level unit, not just its name cell.
        for index in range(self.tree.topLevelItemCount()):
            root_item = self.tree.topLevelItem(index)
            for column in range(4):
                root_item.setBackground(column, QColor("#fff7ed"))
            root_item.setForeground(0, QColor("#9a3412"))
            root_font = root_item.font(0)
            root_font.setBold(True)
            root_item.setFont(0, root_font)
            root_item.setToolTip(0, "وحدة رئيسية في الهيكل التنظيمي")

        # Make filtered results easy to find; otherwise show roots and one level.
        if search or type_filter or status_filter == "0":
            self.tree.expandAll()
        else:
            self.tree.collapseAll()
            for index in range(self.tree.topLevelItemCount()):
                self.tree.topLevelItem(index).setExpanded(True)

        total = len(self._all_units)
        active_count = sum(bool(unit.get("is_active")) for unit in self._all_units)
        self.metric_total[1].setText(str(total))
        self.metric_active[1].setText(str(active_count))
        self.metric_inactive[1].setText(str(total - active_count))
        self.stats_lbl.setText(
            f"إجمالي الوحدات: {total}  |  مطابقة للفلاتر: {len(matched_ids)}  |  "
            f"ظاهرة في المسار: {len(visible_ids)}"
        )

    def _hierarchy_rows_for_export(self):
        units_by_id = {unit["id"]: unit for unit in self._all_units}
        children_by_parent = {}
        for unit in self._all_units:
            children_by_parent.setdefault(unit.get("parent_id"), []).append(unit)

        descendant_cache = {}

        def descendant_count(unit_id, trail=None):
            trail = set() if trail is None else trail
            if unit_id in trail:
                return 0
            if unit_id in descendant_cache:
                return descendant_cache[unit_id]
            next_trail = trail | {unit_id}
            count = 0
            for child in children_by_parent.get(unit_id, []):
                child_id = child["id"]
                if child_id not in next_trail:
                    count += 1 + descendant_count(child_id, next_trail)
            descendant_cache[unit_id] = count
            return count

        result = []
        visited = set()

        def append_branch(unit, level, ancestors):
            unit_id = unit["id"]
            if unit_id in visited:
                return
            visited.add(unit_id)
            name = unit.get("name") or "(بدون اسم)"
            path_parts = ancestors + [name]
            parent = units_by_id.get(unit.get("parent_id"))
            result.append({
                "id": unit_id,
                "level": level,
                "name": name,
                "unit_type": unit.get("unit_type") or "",
                "status": "نشط" if bool(unit.get("is_active")) else "معطل",
                "parent_name": parent.get("name") if parent else "—",
                "descendants": descendant_count(unit_id),
                "path": " / ".join(path_parts),
            })
            for child in children_by_parent.get(unit_id, []):
                append_branch(child, level + 1, path_parts)

        root_units = [
            unit for unit in self._all_units
            if unit.get("parent_id") not in units_by_id
        ]
        for unit in root_units:
            append_branch(unit, 0, [])

        # Include any disconnected/cyclic records rather than silently omitting them.
        for unit in self._all_units:
            if unit["id"] not in visited:
                append_branch(unit, 0, [])

        return result

    def _export_excel(self):
        if not self._all_units:
            QMessageBox.information(self, "لا توجد بيانات", "لا توجد وحدات لتصديرها.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "تصدير الهيكل التنظيمي إلى Excel",
            "الهيكل_التنظيمي.xlsx",
            "Excel Workbook (*.xlsx)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".xlsx"):
            file_path += ".xlsx"

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

            rows = self._hierarchy_rows_for_export()
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "الهيكل التنظيمي"
            sheet.sheet_view.rightToLeft = True
            sheet.sheet_view.showGridLines = False
            sheet.sheet_view.zoomScale = 90

            # Report title and total, matching the visual hierarchy in the reference.
            sheet.merge_cells("A1:D1")
            title = sheet["A1"]
            title.value = "الهيكل التنظيمي"
            title.font = Font(name="Arial", size=16, bold=True, color="FFFFFF")
            title.fill = PatternFill("solid", fgColor="10263D")
            title.alignment = Alignment(horizontal="center", vertical="center")

            sheet.merge_cells("A2:D2")
            total = sheet["A2"]
            total.value = f"إجمالي الوحدات: {len(rows)}"
            total.font = Font(name="Arial", size=11, bold=True, color="64748B")
            total.alignment = Alignment(horizontal="center", vertical="center")

            headers = ["المستوى", "الوحدة التنظيمية", "النوع", "المسار الكامل"]
            header_row = 3
            for column, value in enumerate(headers, 1):
                cell = sheet.cell(header_row, column, value)
                cell.font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="1095B0")
                cell.alignment = Alignment(horizontal="center", vertical="center")

            thin_gray = Side(style="thin", color="D9DEE5")
            root_fill = PatternFill("solid", fgColor="FFF7E8")
            for row_index, data in enumerate(rows, header_row + 1):
                is_root = data["level"] == 0
                unit_name = data["name"]
                if is_root:
                    unit_name = f"{unit_name} — وحدة رئيسية"
                values = [data["level"], unit_name, data["unit_type"], data["path"]]
                for column, value in enumerate(values, 1):
                    cell = sheet.cell(row_index, column, value)
                    cell.font = Font(
                        name="Arial",
                        size=10,
                        bold=is_root,
                        color="9A4D18" if is_root else "334155",
                    )
                    cell.alignment = Alignment(
                        horizontal="right" if column in (2, 4) else "center",
                        vertical="center",
                        wrap_text=(column == 4),
                        indent=min(data["level"] * 2, 15) if column == 2 else 0,
                    )
                    cell.border = Border(bottom=thin_gray)
                    if is_root:
                        cell.fill = root_fill
                sheet.row_dimensions[row_index].height = 24
                sheet.row_dimensions[row_index].outlineLevel = min(data["level"], 7)

            for column, width in enumerate((12, 36, 18, 64), 1):
                sheet.column_dimensions[chr(64 + column)].width = width
            sheet.row_dimensions[1].height = 32
            sheet.row_dimensions[2].height = 24
            sheet.row_dimensions[header_row].height = 28
            sheet.freeze_panes = "A4"
            sheet.auto_filter.ref = f"A{header_row}:D{header_row + len(rows)}"
            sheet.sheet_properties.outlinePr.summaryBelow = True
            sheet.sheet_properties.pageSetUpPr.fitToPage = True
            sheet.page_setup.orientation = "landscape"
            sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
            sheet.page_setup.fitToWidth = 1
            sheet.page_setup.fitToHeight = 0
            sheet.print_title_rows = "1:3"

            workbook.save(file_path)
            workbook.close()
            write_audit_log(
                user=self.current_user,
                action="تصدير",
                module_name="الهيكل التنظيمي",
                description=f"تصدير الهيكل التنظيمي إلى Excel: {Path(file_path).name}",
                new_values={
                    "file_name": Path(file_path).name,
                    "record_count": len(rows),
                },
            )
            self._show_toast("تم تصدير الشجرة بالكامل إلى Excel بنجاح")
        except ImportError:
            QMessageBox.critical(
                self,
                "مكتبة غير متاحة",
                "لتصدير Excel، ثبّت مكتبة openpyxl:\n\npython -m pip install openpyxl",
            )
        except Exception as error:
            QMessageBox.critical(self, "خطأ في التصدير", f"تعذر إنشاء ملف Excel:\n{error}")

    # ─────────────── Actions ─────────────────────────────────

    def _get_all_units_list(self):
        return [dict(u.items()) for u in self._all_units]

    def _add_unit(self):
        dlg = OrgUnitDialog(self, all_units=self._get_all_units_list())
        if dlg.exec() != QDialog.Accepted:
            return
        data = dlg.get_data()
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO dbo.org_units (name, unit_type, parent_id, is_active, sort_order)
                VALUES (?, ?, ?, 1, 0)
                """,
                (data["name"], data["unit_type"], data["parent_id"])
            )
            cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
            inserted = cursor.fetchone()
            unit_id = inserted[0] if inserted else None
            conn.commit()
            conn.close()

            new_values = org_unit_audit_data(
                {**data, "id": unit_id, "is_active": True},
                self._all_units,
            )
            write_audit_log(
                user=self.current_user,
                action="إضافة",
                module_name="الهيكل التنظيمي",
                record_id=unit_id,
                description=f"إضافة عنصر: {data['name']} ({data['unit_type']})",
                new_values=new_values,
            )

            self.load_units()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"تعذر الإضافة:\n{e}")

    def _edit_unit(self, unit_dict):
        dlg = OrgUnitDialog(
            self,
            unit=unit_dict,
            all_units=self._get_all_units_list()
        )
        if dlg.exec() != QDialog.Accepted:
            return
        data = dlg.get_data()
        old_values = org_unit_audit_data(unit_dict, self._all_units)
        new_values = org_unit_audit_data(
            {
                **data,
                "id": unit_dict["id"],
                "is_active": unit_dict.get("is_active", True),
            },
            self._all_units,
        )
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE dbo.org_units
                SET name = ?, unit_type = ?, parent_id = ?, updated_at = SYSDATETIME()
                WHERE id = ?
                """,
                (data["name"], data["unit_type"], data["parent_id"], unit_dict["id"])
            )
            conn.commit()
            conn.close()

            write_audit_log(
                user=self.current_user,
                action="تعديل",
                module_name="الهيكل التنظيمي",
                record_id=unit_dict["id"],
                description=f"تعديل عنصر ID={unit_dict['id']}: {data['name']}",
                old_values=old_values,
                new_values=new_values,
            )

            self.load_units()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"تعذر التعديل:\n{e}")

    def _delete_unit(self, unit_dict):
        unit_id = unit_dict["id"]
        name    = unit_dict["name"]

        # هل له سجلات أحبار؟
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) FROM dbo.ink_transactions
                WHERE org_unit_id = ? OR office_id = ?
                """,
                (unit_id, unit_id)
            )
            used = cursor.fetchone()[0]

            # هل له أبناء؟
            cursor.execute(
                "SELECT COUNT(*) FROM dbo.org_units WHERE parent_id = ?",
                (unit_id,)
            )
            has_children = cursor.fetchone()[0]
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"تعذر الفحص:\n{e}")
            return

        if has_children > 0:
            QMessageBox.warning(
                self,
                "تعذر الحذف",
                f"العنصر «{name}» لديه {has_children} عنصر تابع.\n"
                "يجب حذف العناصر التابعة أولاً أو نقلها."
            )
            return

        if used > 0:
            QMessageBox.warning(
                self,
                "تعذر الحذف",
                f"العنصر «{name}» مرتبط بـ {used} سجل(ات) أحبار.\n"
                "لا يمكن حذفه فعليًا حفاظًا على سجل العمليات.",
            )
            return

        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل تريد حذف العنصر «{name}» نهائياً؟\n\nلا يمكن التراجع عن هذا الإجراء.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM dbo.org_units WHERE id = ?",
                (unit_id,)
            )
            conn.commit()
            conn.close()

            write_audit_log(
                user=self.current_user,
                action="حذف",
                module_name="الهيكل التنظيمي",
                record_id=unit_id,
                description=f"حذف عنصر: {name}",
                old_values=org_unit_audit_data(unit_dict, self._all_units),
                new_values={"deleted": True},
            )

            self.load_units()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"تعذر الحذف:\n{e}")
