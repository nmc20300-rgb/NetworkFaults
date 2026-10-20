"""
واجهة تنبيه تبديل التكييف: البطاقة + نافذة سبب التأخير + السجل التاريخي.

الحالة بتتحسب دايمًا من الوقت الحالي + اللي في قاعدة البيانات (ac_schedule.build_alert_state)،
والـ Timers مجرد وسيلة لتحديث العرض:
  - كل ثانية: تحديث النص من الذاكرة (حساب خفيف جدًا) وبس لو الصفحة ظاهرة.
  - كل 30 ثانية: قراءة قاعدة البيانات (لو الصفحة ظاهرة).
"""
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QRectF,
    QSettings,
    Qt,
    QTimer,
    QUrl,
    QVariantAnimation,
)
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

try:
    from PySide6.QtMultimedia import QSoundEffect
except ImportError:  # الحزمة مش متسطبة: نرجع للـ beep العادي
    QSoundEffect = None

from database import get_connection

from . import ac_repository as repo
from . import ac_schedule as sched
from .ac_history import AcHistoryDialog

LEVEL_COLORS = {
    sched.LEVEL_NORMAL: "#22a06b",   # هادي: قبل التنبيه
    sched.LEVEL_INFO: "#0e9aaa",     # قبل ساعة
    sched.LEVEL_WARNING: "#d97706",  # قبل 30 دقيقة
    sched.LEVEL_DUE: "#dc2626",      # حان / متأخر
    "error": "#94a3b8",
}
ALIGN_RIGHT = Qt.AlignRight | Qt.AlignAbsolute | Qt.AlignVCenter

# ملف الصوت: <فولدر المشروع>\assets\ac_alert.wav (لازم WAV)
SOUND_FILE = Path(__file__).resolve().parent.parent / "assets" / "ac_alert.wav"
REPEAT_MINUTES = 10  # تكرار الصوت كل كام دقيقة طول ما التبديل متأخر
PLAY_COUNT = 3       # كل تنبيه بيتشغّل كام مرة ورا بعض (متواصل)


class AcSound:
    """تشغيل صوت التنبيه (WAV) أو beep النظام لو الملف/الحزمة مش موجودين."""

    def __init__(self, parent):
        self._effect = None
        if QSoundEffect is not None and SOUND_FILE.exists():
            self._effect = QSoundEffect(parent)
            self._effect.setSource(QUrl.fromLocalFile(str(SOUND_FILE)))
            self._effect.setVolume(0.8)
            self._effect.setLoopCount(PLAY_COUNT)  # تكرار متواصل بدون فاصل

    def play(self):
        if self._effect is not None:
            self._effect.play()
        else:
            # بديل لو ملف الصوت مش موجود: beep بنفس عدد المرات
            for index in range(PLAY_COUNT):
                QTimer.singleShot(index * 1000, QApplication.beep)

DIALOG_STYLE = """
    QDialog { background: #f6f8fb; }
    QLabel { color: #334155; font-size: 13px; }
    #dlgTitle { color: #0f2338; font-size: 15px; font-weight: 800; }
    #dlgSummary { color: #64748b; font-size: 12px; font-weight: 600; }
    QPlainTextEdit {
        background: #ffffff; border: 1px solid #dbe3ea; border-radius: 10px;
        padding: 8px; font-size: 13px; color: #0f2338;
    }
    QPlainTextEdit:focus { border: 1px solid #0e9aaa; }
    QComboBox {
        background: #ffffff; border: 1px solid #dbe3ea; border-radius: 8px;
        padding: 5px 10px; min-width: 130px; font-size: 12px;
    }
    QPushButton {
        background: #ffffff; color: #0e7490; border: 1px solid #dbe3ea;
        border-radius: 10px; padding: 8px 18px; font-size: 13px; font-weight: 800;
    }
    QPushButton:hover { background: #eef6f8; }
    #dlgPrimary { background: #0e9aaa; color: #ffffff; border: none; }
    #dlgPrimary:hover { background: #0b8795; }
    #dlgPrimary:disabled { background: #e2e8f0; color: #94a3b8; }
    QTableWidget {
        background: #ffffff; border: 1px solid #e6ebf1; border-radius: 12px;
        color: #334155; font-size: 12px; gridline-color: transparent;
        selection-background-color: #eef6f8; selection-color: #0f2338;
    }
    QTableWidget::item { padding: 4px 6px; border-bottom: 1px solid #f0f3f7; }
    QHeaderView::section {
        background: #ffffff; color: #94a3b8; border: none;
        border-bottom: 1px solid #e6ebf1; padding: 8px 6px;
        font-size: 12px; font-weight: 700;
    }
"""


# =============================================================
# نافذة سبب التأخير
# =============================================================
class DelayReasonDialog(QDialog):
    def __init__(self, slot_text, delay_minutes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("سبب تأخير التبديل")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setStyleSheet(DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        title = QLabel("تم تأخير تبديل التكييف")
        title.setObjectName("dlgTitle")
        layout.addWidget(title)

        info = QLabel(
            f"الموعد المجدول {slot_text} — التأخير الحالي "
            f"{sched.format_duration_ar(delay_minutes)}."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addWidget(QLabel("اختر سبب التأخير (مطلوب لحفظ التأكيد):"))
        self.reason_choice = QComboBox()
        self.reason_choice.addItem("اختر سببًا…", "")
        self.reason_choice.addItem(
            "لم أكن متاحًا قرب الجهاز وقت التبديل",
            "لم أكن متاحًا قرب الجهاز وقت التبديل",
        )
        self.reason_choice.addItem("سبب آخر", "__other__")
        self.reason_choice.currentIndexChanged.connect(self._on_reason_choice_changed)
        layout.addWidget(self.reason_choice)

        self.edit = QPlainTextEdit()
        self.edit.setFixedHeight(90)
        self.edit.setPlaceholderText("اكتب سبب التأخير هنا…")
        self.edit.textChanged.connect(self._validate)
        self.edit.hide()
        layout.addWidget(self.edit)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.save_button = QPushButton("حفظ التأكيد")
        self.save_button.setObjectName("dlgPrimary")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.accept)
        cancel = QPushButton("إلغاء")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(self.save_button)
        buttons.addWidget(cancel)
        buttons.addStretch(1)
        layout.addLayout(buttons)

    def _on_reason_choice_changed(self, _index):
        is_other = self.reason_choice.currentData() == "__other__"
        self.edit.setVisible(is_other)
        if not is_other:
            self.edit.clear()
        self._validate()

    def _validate(self):
        choice = self.reason_choice.currentData()
        if choice == "__other__":
            self.save_button.setEnabled(bool(self.edit.toPlainText().strip()))
        else:
            self.save_button.setEnabled(bool(choice))

    def reason(self):
        choice = self.reason_choice.currentData()
        if choice == "__other__":
            return self.edit.toPlainText().strip()[:500]
        return str(choice or "")[:500]


# =============================================================
# بطاقة التنبيه (ارتفاع ثابت عشان الداشبورد ما تتحركش)
# =============================================================
class AcAlertCard(QFrame):
    DB_REFRESH_MS = 30_000
    TICK_MS = 1_000

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.setObjectName("acCard")
        self.setFixedHeight(92)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setLayoutDirection(Qt.RightToLeft)

        self.current_user = current_user or {}
        self._can_confirm = sched.can_confirm_ac_change(self.current_user)
        self._snapshot = None
        self._db_error = None
        self._state = None
        self._level = None
        self._accent = QColor(LEVEL_COLORS[sched.LEVEL_NORMAL])
        self._busy = False

        # صوت التنبيه (حالة الكتم بتتحفظ بين التشغيلات)
        self._settings = QSettings("NetworkFaults", "AcAlert")
        self._sound = AcSound(self)
        self._sound_on = self._settings.value("ac_sound_on", True, type=bool)
        self._sound_key = None
        self._sound_at = None

        self._fade = QVariantAnimation(self)
        self._fade.setDuration(350)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)
        self._fade.valueChanged.connect(self._on_fade)

        self._build_ui()

        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._on_tick)
        self._tick_timer.start(self.TICK_MS)
        self._db_timer = QTimer(self)
        self._db_timer.timeout.connect(self._on_db_timer)
        self._db_timer.start(self.DB_REFRESH_MS)

        self.reload_from_db()
        self._render()

    # ---------------------------------------------------------
    def _build_ui(self):
        self.setStyleSheet("""
            #acTitle { color: #64748b; font-size: 12px; font-weight: 700; }
            #acMessage { color: #0f2338; font-size: 15px; font-weight: 800; }
            #acDetail { color: #64748b; font-size: 12px; font-weight: 500; }
            #acCaption { color: #64748b; font-size: 11px; font-weight: 600; }
            #acCountdown { font-size: 22px; font-weight: 800; color: #0f2338; }
            #acCountdown[level="normal"] { color: #15803d; }
            #acCountdown[level="info"] { color: #0e7490; }
            #acCountdown[level="warning"] { color: #b45309; }
            #acCountdown[level="due"] { color: #b91c1c; }
            #acConfirm {
                background: #dc2626; color: #ffffff; border: none;
                border-radius: 10px; padding: 9px 16px;
                font-size: 13px; font-weight: 800;
            }
            #acConfirm:hover { background: #b91c1c; }
            #acConfirm:disabled { background: #e2e8f0; color: #94a3b8; }
            #acHistory {
                background: #f1f6f8; color: #0e7490; border: 1px solid #e0eaee;
                border-radius: 10px; padding: 9px 14px;
                font-size: 12px; font-weight: 800;
            }
            #acHistory:hover { background: #e3f0f3; }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 10, 16, 10)  # يمين أكبر: مكان شريط اللون
        layout.setSpacing(18)

        info = QVBoxLayout()
        info.setSpacing(2)
        self.title_label = QLabel("تنبيه تبديل التكييف")
        self.title_label.setObjectName("acTitle")
        self.title_label.setAlignment(ALIGN_RIGHT)
        self.message_label = QLabel("")
        self.message_label.setObjectName("acMessage")
        self.message_label.setAlignment(ALIGN_RIGHT)
        self.message_label.setWordWrap(True)
        self.detail_label = QLabel("")
        self.detail_label.setObjectName("acDetail")
        self.detail_label.setAlignment(ALIGN_RIGHT)
        self.detail_label.setWordWrap(True)
        info.addWidget(self.title_label)
        info.addWidget(self.message_label)
        info.addWidget(self.detail_label)
        layout.addLayout(info, 1)

        counter = QVBoxLayout()
        counter.setSpacing(0)
        self.caption_label = QLabel("")
        self.caption_label.setObjectName("acCaption")
        self.caption_label.setAlignment(Qt.AlignCenter)
        self.countdown_label = QLabel("")
        self.countdown_label.setObjectName("acCountdown")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setMinimumWidth(170)
        counter.addStretch(1)
        counter.addWidget(self.caption_label)
        counter.addWidget(self.countdown_label)
        counter.addStretch(1)
        layout.addLayout(counter)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self.confirm_button = QPushButton("تأكيد تبديل التكييف")
        self.confirm_button.setObjectName("acConfirm")
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.clicked.connect(self._on_confirm)
        self.confirm_button.hide()
        self.history_button = QPushButton("السجل")
        self.history_button.setObjectName("acHistory")
        self.history_button.setCursor(Qt.PointingHandCursor)
        self.history_button.clicked.connect(self._open_history)
        self.sound_button = QPushButton()
        self.sound_button.setObjectName("acHistory")
        self.sound_button.setCheckable(True)
        self.sound_button.setCursor(Qt.PointingHandCursor)
        self.sound_button.setChecked(self._sound_on)
        self.sound_button.setText("الصوت: يعمل" if self._sound_on else "الصوت: متوقف")
        self.sound_button.toggled.connect(self._toggle_sound)
        buttons.addWidget(self.confirm_button)
        buttons.addWidget(self.history_button)
        buttons.addWidget(self.sound_button)
        layout.addLayout(buttons)

    # ---------------------------------------------------------
    # الرسم: خلفية بيضاء + لمسة لون خفيفة + شريط لون على اليمين
    # ---------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, 14, 14)

        painter.fillPath(path, QColor("#ffffff"))
        tint = QColor(self._accent)
        tint.setAlpha(16)
        painter.fillPath(path, tint)

        painter.save()
        painter.setClipPath(path)
        painter.fillRect(QRectF(rect.right() - 6, rect.top(), 6, rect.height()), self._accent)
        painter.restore()

        painter.setPen(QPen(QColor("#e6ebf1"), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        painter.end()

    def _on_fade(self, value):
        self._accent = QColor(value)
        self.update()

    def _set_level(self, level):
        """تغيير المستوى: Fade خفيف للون (350ms) مرة واحدة فقط عند تغيّر الحالة."""
        if level == self._level:
            return
        first = self._level is None
        self._level = level
        target = QColor(LEVEL_COLORS[level])

        self._fade.stop()
        if first or not self.isVisible():
            self._accent = target
            self.update()
        else:
            self._fade.setStartValue(QColor(self._accent))
            self._fade.setEndValue(target)
            self._fade.start()

        self.countdown_label.setProperty("level", level)
        self.countdown_label.style().unpolish(self.countdown_label)
        self.countdown_label.style().polish(self.countdown_label)

    @staticmethod
    def _set_text(label, text):
        if label.text() != text:
            label.setText(text)

    # ---------------------------------------------------------
    # قاعدة البيانات
    # ---------------------------------------------------------
    def reload_from_db(self):
        try:
            conn = get_connection()
            try:
                self._snapshot = repo.load_snapshot(conn, datetime.now())
            finally:
                conn.close()
            self._db_error = None
        except Exception as exc:
            self._snapshot = None
            self._db_error = str(exc)

    def _last_confirmation_text(self):
        last = self._snapshot.last_confirmation if self._snapshot else None
        if not last or not last.get("confirmed_at"):
            return ""
        when = sched.format_datetime_ar(last["confirmed_at"], datetime.now())
        who = last.get("confirmed_by") or ""
        return f"آخر تأكيد: {when}" + (f" · {who}" if who else "")

    # ---------------------------------------------------------
    # العرض (من الحالة المحسوبة)
    # ---------------------------------------------------------
    def _render(self):
        now = datetime.now()

        if self._snapshot is None:
            self._state = None
            self._set_level("error")
            self._set_text(self.message_label, "تعذر قراءة حالة تبديل التكييف من قاعدة البيانات")
            self._set_text(self.detail_label, "سيُعاد المحاولة تلقائيًا كل 30 ثانية")
            self._set_text(self.caption_label, "")
            self._set_text(self.countdown_label, "—")
            self.confirm_button.hide()
            return

        state = sched.build_alert_state(
            now, set(self._snapshot.records), self._snapshot.tracking_start
        )
        self._state = state
        self._maybe_play_sound(state, now)
        self._set_level(state.level)
        self._set_text(self.message_label, state.message)
        self._set_text(self.detail_label, state.detail or self._last_confirmation_text())
        self._set_text(self.caption_label, state.countdown_caption)
        self._set_text(self.countdown_label, state.countdown_value)

        if state.is_due:
            self.confirm_button.show()
            self.confirm_button.setEnabled(self._can_confirm and not self._busy)
            self.confirm_button.setToolTip(
                "" if self._can_confirm else "تأكيد التبديل متاح للمستخدمين المصرّح لهم فقط"
            )
        else:
            self.confirm_button.hide()

    def _on_tick(self):
        if self.isVisible():
            self._render()
        elif self._snapshot is not None:
            # الصفحة مخفية: مفيش رسم، بس الصوت لسه شغّال
            now = datetime.now()
            state = sched.build_alert_state(
                now, set(self._snapshot.records), self._snapshot.tracking_start
            )
            self._maybe_play_sound(state, now)

    def _on_db_timer(self):
        # بنقرا القاعدة حتى لو الصفحة مخفية، عشان الصوت ما يرنش على تبديل اتأكد من مستخدم تاني
        self.reload_from_db()
        if self.isVisible():
            self._render()

    # ---------------------------------------------------------
    # الصوت
    # ---------------------------------------------------------
    def _maybe_play_sound(self, state, now):
        """صوت واحد: مرة عند حلول الموعد، وبعدها كل REPEAT_MINUTES طول ما التبديل متأخر."""
        if not self._sound_on or not self._can_confirm:
            return
        if state.level != sched.LEVEL_DUE:
            return

        key = state.primary_slot
        if key != self._sound_key:
            self._sound_key = key
            self._sound_at = now
            self._sound.play()
        elif (now - self._sound_at) >= timedelta(minutes=REPEAT_MINUTES):
            self._sound_at = now
            self._sound.play()

    def _toggle_sound(self, on):
        self._sound_on = on
        self.sound_button.setText("الصوت: يعمل" if on else "الصوت: متوقف")
        self._settings.setValue("ac_sound_on", on)

    def showEvent(self, event):
        super().showEvent(event)
        self.reload_from_db()
        self._render()

    # ---------------------------------------------------------
    # التأكيد
    # ---------------------------------------------------------
    def _on_confirm(self):
        state = self._state
        if self._busy or state is None or not state.is_due or not self._can_confirm:
            return

        slot = state.primary_slot
        now = datetime.now()
        delay = sched.delay_minutes(slot, now)
        reason = None
        if delay > sched.GRACE_MINUTES:
            dialog = DelayReasonDialog(sched.slot_label(slot, now), delay, self)
            if dialog.exec() != QDialog.Accepted:
                return
            reason = dialog.reason()

        self._busy = True
        self.confirm_button.setEnabled(False)
        try:
            conn = get_connection()
            try:
                result = repo.confirm_change(
                    conn, slot, datetime.now(), sched.actor_name(self.current_user), reason
                )
            finally:
                conn.close()
        except Exception as exc:
            self._busy = False
            self.reload_from_db()
            self._render()
            QMessageBox.warning(
                self,
                "تعذر حفظ التأكيد",
                f"لم يتم تسجيل التأكيد، والتنبيه سيظل ظاهرًا.\n\n{exc}",
            )
            return

        self._busy = False
        if result == repo.RESULT_ALREADY:
            QMessageBox.information(
                self, "تم التأكيد مسبقًا", "هذا التبديل تم تأكيده بالفعل من مستخدم آخر."
            )
        # الاختفاء بيحصل فقط لأن القاعدة بقت فيها سجل للموعد ده
        self.reload_from_db()
        self._render()

    def _open_history(self):
        AcHistoryDialog(self).exec()