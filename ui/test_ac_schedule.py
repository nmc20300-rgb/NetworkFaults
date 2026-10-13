"""
تشغيل الاختبارات (من نفس فولدر الملفات):
    python -m unittest test_ac_schedule -v
"""
import unittest
from datetime import datetime, timedelta

import ac_schedule as ac


def dt(day, hour, minute=0, second=0):
    return datetime(2026, 10, day, hour, minute, second)


class SlotTests(unittest.TestCase):
    def test_next_slot_basic(self):
        self.assertEqual(ac.next_slot(dt(12, 7, 59)), dt(12, 8))
        self.assertEqual(ac.next_slot(dt(12, 8, 0, 1)), dt(12, 12))
        self.assertEqual(ac.next_slot(dt(12, 20, 0, 1)), dt(13, 0))

    def test_next_slot_when_exactly_due_is_the_following_one(self):
        self.assertEqual(ac.next_slot(dt(12, 8)), dt(12, 12))

    def test_midnight_slot(self):
        self.assertEqual(ac.next_slot(dt(12, 23, 59)), dt(13, 0))
        self.assertEqual(ac.previous_slot(dt(13, 0, 5)), dt(13, 0))

    def test_previous_slot(self):
        self.assertEqual(ac.previous_slot(dt(12, 9)), dt(12, 8))
        self.assertEqual(ac.previous_slot(dt(12, 0, 0)), dt(12, 0))

    def test_slots_between_counts_five_per_day(self):
        slots = ac.slots_between(dt(12, 0), dt(12, 23, 59))
        self.assertEqual(len(slots), 5)
        self.assertEqual(slots, sorted(slots))


class LevelTests(unittest.TestCase):
    def test_levels(self):
        self.assertEqual(ac.classify_level(3601), ac.LEVEL_NORMAL)
        self.assertEqual(ac.classify_level(3600), ac.LEVEL_INFO)
        self.assertEqual(ac.classify_level(1801), ac.LEVEL_INFO)
        self.assertEqual(ac.classify_level(1800), ac.LEVEL_WARNING)
        self.assertEqual(ac.classify_level(1), ac.LEVEL_WARNING)
        self.assertEqual(ac.classify_level(0), ac.LEVEL_DUE)
        self.assertEqual(ac.classify_level(-500), ac.LEVEL_DUE)


class StateTests(unittest.TestCase):
    start = dt(12, 0, 1)

    def test_calm_state(self):
        state = ac.build_alert_state(dt(12, 9, 0), {dt(12, 8)}, self.start)
        self.assertEqual(state.level, ac.LEVEL_NORMAL)
        self.assertFalse(state.is_due)
        self.assertEqual(state.countdown_value, "03:00:00")

    def test_one_hour_message(self):
        state = ac.build_alert_state(dt(12, 11, 0), {dt(12, 8)}, self.start)
        self.assertEqual(state.level, ac.LEVEL_INFO)
        self.assertEqual(state.message, "متبقي ساعة على تبديل التكييف")

    def test_warning_countdown(self):
        state = ac.build_alert_state(dt(12, 11, 44, 40), {dt(12, 8)}, self.start)
        self.assertEqual(state.level, ac.LEVEL_WARNING)
        self.assertEqual(state.countdown_value, "00:15:20")

    def test_info_countdown(self):
        state = ac.build_alert_state(dt(12, 11, 14, 40), {dt(12, 8)}, self.start)
        self.assertEqual(state.level, ac.LEVEL_INFO)
        self.assertEqual(state.countdown_value, "00:45:20")

    def test_due_now(self):
        state = ac.build_alert_state(dt(12, 12, 0, 20), {dt(12, 8)}, self.start)
        self.assertTrue(state.is_due)
        self.assertEqual(state.level, ac.LEVEL_DUE)
        self.assertEqual(state.countdown_value, "موعد التبديل الآن")

    def test_overdue_minutes(self):
        state = ac.build_alert_state(dt(12, 12, 25, 10), {dt(12, 8)}, self.start)
        self.assertEqual(state.countdown_caption, "متأخر منذ")
        self.assertEqual(state.countdown_value, "25 دقيقة")

    def test_overdue_stays_when_next_slot_approaches(self):
        # 8:00 لم يؤكد، والوقت 15:30 (قبل 16:00 بنص ساعة)
        state = ac.build_alert_state(dt(12, 15, 30), {dt(12, 0), dt(12, 12)}, self.start)
        self.assertTrue(state.is_due)
        self.assertEqual(state.primary_slot, dt(12, 8))
        self.assertIn("التبديل القادم", state.detail)

    def test_multiple_outstanding_oldest_first(self):
        state = ac.build_alert_state(dt(12, 17, 0), {dt(12, 0)}, self.start)
        self.assertEqual(state.outstanding, (dt(12, 8), dt(12, 12), dt(12, 16)))
        self.assertEqual(state.primary_slot, dt(12, 8))
        self.assertIn("2", state.detail)

    def test_confirmed_slot_not_shown_after_restart(self):
        resolved = {dt(12, 8), dt(12, 12)}
        state = ac.build_alert_state(dt(12, 12, 40), resolved, self.start)
        self.assertFalse(state.is_due)
        self.assertEqual(state.outstanding, ())

    def test_tracking_start_ignores_older_slots(self):
        state = ac.build_alert_state(dt(12, 9), set(), tracking_start=dt(12, 8, 30))
        self.assertEqual(state.outstanding, ())

    def test_lookback_limit(self):
        state = ac.build_alert_state(dt(14, 9), set(), tracking_start=dt(10, 0))
        self.assertTrue(all(s >= dt(13, 9) for s in state.outstanding))


class MissedTests(unittest.TestCase):
    def test_old_unconfirmed_become_missed_once(self):
        now = dt(14, 9)
        missed = ac.slots_to_mark_missed(now, set(), tracking_start=dt(12, 0, 1))
        self.assertIn(dt(12, 8), missed)
        self.assertNotIn(dt(14, 8), missed)  # لسه داخل فترة التنبيه
        again = ac.slots_to_mark_missed(now, set(missed), tracking_start=dt(12, 0, 1))
        self.assertEqual(again, [])


class DelayTests(unittest.TestCase):
    def test_delay(self):
        self.assertEqual(ac.delay_minutes(dt(12, 8), dt(12, 8, 0, 59)), 0)
        self.assertEqual(ac.delay_minutes(dt(12, 8), dt(12, 8, 25)), 25)
        self.assertEqual(ac.delay_minutes(dt(12, 8), dt(12, 7, 59)), 0)

    def test_status_for_delay(self):
        self.assertEqual(ac.status_for_delay(0), ac.STATUS_CONFIRMED)
        self.assertEqual(ac.status_for_delay(1), ac.STATUS_LATE)


class FormatTests(unittest.TestCase):
    def test_duration(self):
        self.assertEqual(ac.format_duration_ar(60), "ساعة")
        self.assertEqual(ac.format_duration_ar(120), "ساعتان")
        self.assertEqual(ac.format_duration_ar(90), "ساعة و 30 دقيقة")
        self.assertEqual(ac.format_duration_ar(25), "25 دقيقة")
        self.assertEqual(ac.format_duration_ar(3), "3 دقائق")
        self.assertEqual(ac.format_duration_ar(0), "أقل من دقيقة")

    def test_slot_label(self):
        now = dt(12, 23, 0)
        self.assertEqual(ac.slot_label(dt(12, 20), now), "8:00 م")
        self.assertEqual(ac.slot_label(dt(13, 0), now), "غدًا 12:00 ص")
        self.assertEqual(ac.slot_label(dt(11, 20), now), "أمس 8:00 م")


class HistoryTests(unittest.TestCase):
    def test_rows_and_compliance(self):
        now = dt(12, 17)
        records = {
            dt(12, 0): {"status": ac.STATUS_CONFIRMED, "confirmed_at": dt(12, 0, 0, 20),
                        "confirmed_by": "a", "delay_minutes": 0},
            dt(12, 8): {"status": ac.STATUS_LATE, "confirmed_at": dt(12, 8, 30),
                        "confirmed_by": "b", "delay_minutes": 30, "delay_reason": "x"},
        }
        rows = ac.history_rows(now, records, tracking_start=dt(11, 23))
        self.assertEqual(rows[0]["scheduled"], dt(12, 16))      # الأحدث أولًا
        keys = {r["scheduled"]: r["status_key"] for r in rows}
        self.assertEqual(keys[dt(12, 0)], ac.HISTORY_ON_TIME)
        self.assertEqual(keys[dt(12, 8)], ac.HISTORY_LATE)
        self.assertEqual(keys[dt(12, 12)], ac.HISTORY_UNCONFIRMED)
        summary = ac.compliance_summary(rows)
        self.assertEqual(summary["on_time"], 1)
        self.assertEqual(summary["late"], 1)
        self.assertEqual(summary["unconfirmed"], 2)


class PermissionTests(unittest.TestCase):
    def test_roles(self):
        self.assertTrue(ac.can_confirm_ac_change({"role_code": "super_admin"}))
        self.assertFalse(ac.can_confirm_ac_change({"role_code": "VIEWER"}))
        self.assertFalse(ac.can_confirm_ac_change(None))
        self.assertTrue(ac.can_confirm_ac_change({"role_code": "X", "permissions": ["ac_confirm"]}))

    def test_actor_name(self):
        self.assertEqual(ac.actor_name({"username": "m_adel"}), "m_adel")
        self.assertEqual(ac.actor_name({"full_name": "محمد", "username": "m"}), "محمد")


if __name__ == "__main__":
    unittest.main()