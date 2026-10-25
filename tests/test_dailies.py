from datetime import date, timedelta
import subprocess
import sys
import unittest

import lunar_lander as ll
from test_records import land


def days(count, start=date(2026, 1, 1)):
    return [(start + timedelta(n)).isoformat() for n in range(count)]


class DailyTests(unittest.TestCase):
    def test_three_a_day_one_per_chapter(self):
        dailies = ll.daily_missions("2026-10-25", "%d.%m.%Y")
        self.assertEqual([m.key for m in dailies], ["daily-2026-10-25-maria", "daily-2026-10-25-highlands",
                                                    "daily-2026-10-25-frontier"])
        self.assertEqual([m.name for m in dailies], ["MARIA 25.10.2026", "HIGHLANDS 25.10.2026",
                                                     "FRONTIER 25.10.2026"])
        tab = next(c for c in ll.CHAPTERS if c.key == "daily")
        self.assertEqual(ll.chapter_missions(tab, ll.missions("2026-10-25")), ll.daily_missions("2026-10-25"))
        # Dailies never count toward rank, all three of them.
        self.assertEqual(ll.career({m.key: 9999 for m in dailies}, ll.missions("2026-10-25")).points, 0)

    def test_every_setting_stays_within_its_chapters_span(self):
        for day in days(365):
            for mission, (_, _, _, *spans) in zip(ll.daily_missions(day), ll.DAILY_TIERS):
                difficulties, widths, altitudes, offsets, drifts, fuels, sinks, floors, ceilings = spans
                with self.subTest(day=day, mission=mission.key):
                    inside = lambda value, span: min(span) <= value <= max(span)
                    self.assertIn(mission.difficulty, difficulties)
                    for value, span in ((mission.width, widths), (abs(mission.drift), drifts),
                                        (mission.fuel, fuels), (mission.sink, sinks),
                                        (mission.relief[0], floors), (mission.relief[1], ceilings)):
                        self.assertTrue(inside(value, span), (value, span))
                    self.assertLessEqual(abs(mission.offset), max(offsets))
                    self.assertTrue(inside(mission.altitude, (min(altitudes), max(max(altitudes), mission.relief[1] + 120))))
                    # Fair approach: inside the field, clear of the ridges, drifting toward the pad.
                    self.assertTrue(100 <= mission.center - mission.width / 2 < mission.center + mission.width / 2 <= 900)
                    self.assertTrue(60 <= mission.center + mission.offset <= 940)
                    self.assertGreaterEqual(mission.altitude, mission.relief[1] + 120)
                    self.assertLess(mission.drift * mission.offset, 0)

    def test_they_vary_from_day_to_day(self):
        for tier in range(3):
            shapes = {(m.center, m.width, m.offset, m.drift, m.fuel, m.difficulty)
                      for m in (ll.daily_missions(day)[tier] for day in days(60))}
            self.assertGreater(len(shapes), 55)
            sides = {m.offset > 0 for m in (ll.daily_missions(day)[tier] for day in days(60))}
            self.assertEqual(sides, {True, False})

    def test_a_steady_pilot_lands_them_all(self):
        for day in days(60, date(2027, 3, 1)):
            for mission in ll.daily_missions(day):
                with self.subTest(day=day, mission=mission.key):
                    flight = land(mission)
                    self.assertEqual(flight.status, "landed", flight.reason)
                    self.assertGreater(flight.fuel, 20)

    def test_the_same_day_everywhere(self):
        code = "import lunar_lander as l; print([repr(m.launch()) for m in l.daily_missions('2026-10-24')])"
        first = subprocess.check_output([sys.executable, "-c", code])
        self.assertEqual(first, subprocess.check_output([sys.executable, "-c", code]))
        # The date's display never changes the flight.
        a, b = ll.daily_missions("2026-10-24", "%d/%m/%Y")[2].launch(), ll.daily_missions("2026-10-24")[2].launch()
        self.assertEqual((a.terrain.points, a.x, a.y, a.vx, a.vy, a.fuel), (b.terrain.points, b.x, b.y, b.vx, b.vy, b.fuel))


if __name__ == "__main__":
    unittest.main()
