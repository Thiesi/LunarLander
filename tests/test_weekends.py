from datetime import date, timedelta
from pathlib import Path
import tempfile
import unittest

import lunar_lander as ll
from test_history import settle_on
from test_records import land


def screen(canvas):
    return "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)


def weekends(start="2026-01-03", years=2):
    day = date.fromisoformat(start)
    while day.year < date.fromisoformat(start).year + years:
        if day.weekday() >= 5:
            yield day.isoformat()
        day += timedelta(days=1)


SATURDAY = "2026-10-31"


class WeekendTests(unittest.TestCase):
    def test_weekdays_are_plain_and_weekends_special(self):
        maria, highlands, frontier = ll.daily_missions("2026-10-28")
        self.assertEqual((maria.ascent, highlands.rover, frontier.hop), (0, None, 0))
        maria, highlands, frontier = ll.daily_missions(SATURDAY)
        self.assertTrue(100 <= maria.ascent <= 140 and frontier.hop)
        self.assertTrue(10 <= abs(highlands.rover - highlands.center) <= 14)
        self.assertEqual(highlands.marker, (highlands.rover, "ROVER"))

    def test_the_scripted_pilot_flies_every_weekend_special_of_two_years(self):
        for day in weekends():
            for mission in ll.daily_missions(day)[:2]:
                with self.subTest(day=day, mission=mission.key):
                    flight = land(mission)
                    self.assertEqual(flight.status, "landed", flight.reason)
                    self.assertTrue(flight.met())
                    self.assertGreater(flight.fuel, 5)

    def test_every_craft_flies_them(self):
        for craft in ll.CRAFT:
            for mission in ll.daily_missions(SATURDAY)[:2]:
                with self.subTest(craft=craft, mission=mission.key):
                    flight = land(ll.in_craft(mission, craft))
                    self.assertEqual(flight.status, "landed", flight.reason)
                    self.assertTrue(ll.Ghost(ll.in_craft(mission, craft), ll.ghost_data(flight), "x").faithful())


class RendezvousTests(unittest.TestCase):
    def setUp(self):
        self.mission = ll.daily_missions(SATURDAY)[1]

    def parked(self, x):
        flight = self.mission.launch()
        pad = flight.terrain.pad
        flight.x, flight.y, flight.vx, flight.vy, flight.angle = x, pad.height + 3.01, 0, -.2, 0
        for _ in range(10):
            flight.step()
        return flight

    def test_beside_the_rover_is_a_rendezvous(self):
        flight = self.parked(self.mission.rover + (12 if self.mission.rover < self.mission.center else -12))
        self.assertEqual(flight.status, "landed")
        self.assertGreater(flight.score(3), 0)
        self.assertIn("rendezvous", ll.flight_feats(self.mission, flight))
        self.assertEqual(ll.history_line(self.mission, flight), "Parked 12 m from the rover: a short walk.")

    def test_on_the_rover_is_a_crash(self):
        flight = self.parked(self.mission.rover + 2)
        self.assertEqual(flight.status, "crashed")
        self.assertTrue(flight.reason.startswith("Rover strike"))

    def test_safe_but_far_is_not_scored_or_saved(self):
        pad = self.mission.launch().terrain.pad
        far = pad.left + 4 if self.mission.rover > self.mission.center else pad.right - 4
        flight = self.parked(far)
        self.assertEqual(flight.status, "landed")
        self.assertFalse(flight.met())
        self.assertEqual(flight.score(3), 0)
        self.assertNotIn("rendezvous", ll.flight_feats(self.mission, flight))
        self.assertIn("no rendezvous, no score", ll.history_line(self.mission, flight))
        with tempfile.TemporaryDirectory() as folder:
            records = ll.Records(Path(folder) / "pilots.db")
            try:
                self.assertFalse(records.save(ll.Host(node="n", user=7, handle="Nib"), self.mission, flight))
                self.assertEqual(records.bests(ll.Host(node="n", user=7, handle="Nib")), {})
            finally:
                records.close()

    def test_the_rover_shows_in_the_view(self):
        flight = self.mission.launch()
        flight.x, flight.y = self.mission.rover, flight.terrain.pad.height + 40
        display = ll.Display(ll.Host(132, 50))
        for _ in range(3):
            text = screen(display.draw(flight, mission=self.mission))
        self.assertIn("ROVER", text)
        self.assertIn("park within 20 m", self.mission.description)


class SampleReturnTests(unittest.TestCase):
    def setUp(self):
        self.mission = ll.daily_missions(SATURDAY)[0]

    def test_down_then_up_through_the_line(self):
        flight = self.mission.launch()
        settle_on(flight, flight.terrain.pad, vy=-1.5)
        self.assertEqual((flight.status, flight.resting, len(flight.touchdowns)), ("flying", True, 1))
        flight.command("9")
        for _ in range(60 * 40):
            flight.step()
            if flight.status != "flying":
                break
        self.assertEqual(flight.status, "landed")
        self.assertGreaterEqual(flight.y - 3 - flight.terrain.pad.height, self.mission.ascent)
        self.assertAlmostEqual(flight.touchdown()[0], -1.5, delta=.1)
        # Scored on the touchdown, not on the climb.
        climbing = flight.score(1)
        flight.vy = 30
        self.assertEqual(flight.score(1), climbing)
        self.assertEqual(ll.flight_feats(self.mission, flight), {"sample-return"})

    def test_settling_back_rests_again_and_a_crash_is_a_crash(self):
        flight = self.mission.launch()
        settle_on(flight, flight.terrain.pad)
        flight.y += 1
        flight.resting, flight.vy = False, -1
        for _ in range(60 * 10):
            flight.step()
            if flight.resting:
                break
        self.assertEqual((flight.status, flight.resting, len(flight.touchdowns)), ("flying", True, 2))
        flight.y, flight.resting, flight.vy = flight.y + 10, False, -9
        for _ in range(60 * 3):
            flight.step()
        self.assertEqual(flight.status, "crashed")

    def test_the_line_the_call_and_the_debrief(self):
        flight = self.mission.launch()
        display = ll.Display(ll.Host(132, 50))
        flight.y = flight.terrain.pad.height + 3 + self.mission.ascent + 30
        self.assertIn("ASCENT LINE", screen(display.draw(flight, mission=self.mission)))
        settle_on(flight, flight.terrain.pad, vy=-1)
        text = screen(display.draw(flight, mission=self.mission))
        self.assertIn("Samples aboard", text)
        flight.command("9")
        while flight.status == "flying":
            flight.step()
        text = screen(ll.Display(ll.Host(80, 24)).draw(flight, "debrief", mission=self.mission))
        self.assertIn("ASCENT / SAMPLES ABOARD", text)
        self.assertIn("Vertical -1.0", text)


class AchievementTests(unittest.TestCase):
    def test_two_more_in_the_weekend_group(self):
        self.assertEqual(len(ll.ACHIEVEMENTS), 62)
        self.assertEqual(ll.ACHIEVEMENT["sample-return"].group, "WEEKENDS")
        self.assertEqual(ll.ACHIEVEMENT["rendezvous"].group, "WEEKENDS")


if __name__ == "__main__":
    unittest.main()
