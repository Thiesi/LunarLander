from datetime import date, timedelta
from pathlib import Path
import tempfile
import unittest

import lunar_lander as ll
from test_records import land

SATURDAY = "2026-10-31"


def hop():
    return ll.daily_missions(SATURDAY)[2]


def settle(flight, vy=-.5, vx=0.0):
    """Put the craft just above the middle of its lit pad, sinking at `vy`."""
    pad = flight.terrain.pad
    flight.x, flight.y = (pad.left + pad.right) / 2, pad.height + 3.01
    flight.vx, flight.vy, flight.angle, flight.throttle = vx, vy, 0, 0
    for _ in range(10):
        flight.step()


def screen(canvas):
    return "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)


class GenerationTests(unittest.TestCase):
    def test_the_frontier_daily_hops_at_weekends_only(self):
        for n in range(14):
            day = (date(2026, 10, 26) + timedelta(n)).isoformat()
            weekend = date.fromisoformat(day).weekday() >= 5
            maria, highlands, frontier = ll.daily_missions(day)
            with self.subTest(day=day):
                self.assertEqual(bool(frontier.hop), weekend)
                self.assertFalse(maria.hop or highlands.hop)
                self.assertEqual(frontier.description == ll.HOP_BRIEFING, weekend)

    def test_both_pads_inside_the_field_and_well_apart(self):
        for n in range(0, 730):
            day = (date(2026, 1, 1) + timedelta(n)).isoformat()
            mission = ll.daily_missions(day)[2]
            if not mission.hop:
                continue
            with self.subTest(day=day):
                flight = mission.launch()
                first, (second,) = flight.terrain.pad, flight.pads
                self.assertTrue(100 <= second.left and second.right <= 900)
                for pad in (first, second):
                    self.assertEqual(flight.terrain.height((pad.left + pad.right) / 2), pad.height)
                self.assertGreaterEqual(abs(mission.hop), min(ll.HOP_DISTANCE))
                self.assertTrue(all(h <= ll.HOP_CEILING for _, h in flight.terrain.points))

    def test_weekday_dailies_and_authored_missions_are_unchanged(self):
        # Hop machinery adds no draws: a mission without a hop builds the same ground.
        for mission in (*ll.missions("2026-10-26")[:4], *ll.daily_missions("2026-10-26")):
            flight = mission.launch()
            self.assertEqual(flight.pads, ())


class PhysicsTests(unittest.TestCase):
    def test_a_good_touchdown_on_the_first_pad_lights_the_second(self):
        flight = hop().launch()
        second = flight.pads[0]
        settle(flight)
        self.assertEqual(flight.status, "flying")
        self.assertTrue(flight.resting)
        self.assertEqual(flight.terrain.pad, second)
        self.assertEqual(flight.pads, ())
        self.assertEqual(len(flight.touchdowns), 1)

    def test_a_hard_touchdown_on_the_first_pad_is_a_crash(self):
        flight = hop().launch()
        settle(flight, vy=-5)
        self.assertEqual(flight.status, "crashed")

    def test_standing_burns_fuel_until_it_lifts_and_stays_upright_until_clear(self):
        flight = hop().launch()
        settle(flight)
        flight.command("2")  # not enough to lift
        fuel = flight.fuel
        for _ in range(60):
            flight.step()
        self.assertTrue(flight.resting)
        self.assertLess(flight.fuel, fuel)
        flight.command("d")
        self.assertEqual(flight.angle, 0)  # no tilting on the pad
        flight.command("9")
        for _ in range(20):
            flight.step()
        self.assertFalse(flight.resting)
        self.assertGreater(flight.vy, 0)
        flight.angle = 40  # even set directly, upright until 2 m clear
        flight.step()
        self.assertEqual(flight.angle, 0)
        for _ in range(240):
            flight.step()
        flight.command("d")
        self.assertEqual(flight.angle, 10)
        self.assertEqual(flight.status, "flying")

    def test_settling_back_onto_the_pad_it_left_stands_it_there_again(self):
        flight = hop().launch()
        settle(flight)
        flight.command("9")
        for _ in range(15):
            flight.step()
        self.assertFalse(flight.resting)
        flight.command("0")
        for _ in range(120):
            flight.step()
        self.assertEqual(flight.status, "flying")
        self.assertTrue(flight.resting)
        self.assertEqual(len(flight.touchdowns), 1)

    def test_the_score_takes_the_worse_touchdown(self):
        mission = hop()
        smooth = mission.launch()
        settle(smooth, vy=-.2)
        rough = mission.launch()
        settle(rough, vy=-2.9)
        for flight in (smooth, rough):
            flight.x = (flight.terrain.pad.left + flight.terrain.pad.right) / 2
            flight.resting = False
            settle(flight, vy=-.2)
            self.assertEqual(flight.status, "landed")
        self.assertGreater(smooth.score(4), rough.score(4))

    def test_a_steady_pilot_lands_both_pads(self):
        for n in range(0, 140, 7):
            day = (date(2026, 10, 31) + timedelta(n)).isoformat()
            flight = land(ll.daily_missions(day)[2])
            with self.subTest(day=day):
                self.assertEqual(flight.status, "landed", flight.reason)
                self.assertEqual(len(flight.touchdowns), 1)


class GameTests(unittest.TestCase):
    def test_landing_a_hop_earns_grasshopper(self):
        mission = hop()
        flight = land(mission)
        self.assertIn("hop", ll.flight_feats(mission, flight))
        self.assertEqual("hop-gold" in ll.flight_feats(mission, flight),
                         ll.medal(mission, flight.score(mission.difficulty)) == "GOLD")
        self.assertNotIn("hop", ll.flight_feats(ll.missions()[1], land(ll.missions()[1])))
        self.assertEqual(ll.ACHIEVEMENT["hop"].name, "Grasshopper")

    def test_the_view_marks_the_next_pad_and_the_radio_calls_the_first(self):
        mission = hop()
        flight = mission.launch()
        display = ll.Display(ll.Host(132, 50))
        flight.x, flight.y = (flight.terrain.pad.left + flight.pads[0].left) / 2, 120  # between, wide view
        self.assertIn("PAD 2", screen(display.draw(flight, mission=mission)))
        settle(flight)
        text = screen(display.draw(flight, mission=mission))
        self.assertIn("Lift off for the next pad", text)
        self.assertNotIn("PAD 2", text)


if __name__ == "__main__":
    unittest.main()
