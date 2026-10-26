import unittest

import lunar_lander as ll
from test_records import land


def text(canvas):
    return "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)


class TraceTests(unittest.TestCase):
    def test_a_flight_samples_altitude_and_fuel_twice_a_second(self):
        flight = land(ll.missions()[1])
        self.assertAlmostEqual(len(flight.trace), flight.elapsed / ll.TRACE_EVERY, delta=1.5)
        self.assertGreater(flight.trace[0][0], flight.trace[-1][0])  # it came down
        self.assertEqual(flight.trace[0][1], flight.initial_fuel)
        self.assertEqual(repr(flight).count("trace"), 0)  # not part of a flight's identity

    def test_sparklines_fit_and_follow_the_flight(self):
        flight = land(ll.missions()[1])
        alt, burn = ll.descent_trace(flight, 55)[:2]
        self.assertTrue(alt.startswith("ALT  ") and burn.startswith("BURN "))
        self.assertLessEqual(len(alt) - 5, 55)
        self.assertEqual(alt[5], "█")  # the top of the descent
        self.assertEqual(alt[-1], "▁")  # touchdown
        ascii_alt = ll.descent_trace(flight, 55, blocks=False)[0]
        self.assertTrue(all(ch in " .:-=+*#ALT" for ch in ascii_alt))

    def test_a_hint_only_when_the_fuel_plainly_went_early(self):
        flight = ll.training()
        flight.status, flight.elapsed = "landed", 30
        flight.trace = [(180 - 3 * n, 90 - min(n, 10) * 0.6) for n in range(60)]
        flight.fuel = flight.trace[-1][1]
        self.assertIn("first third", ll.descent_trace(flight, 55)[-1])
        flight.trace = [(180 - 3 * n, 90 - max(0, n - 40) * 0.6) for n in range(60)]
        flight.fuel = flight.trace[-1][1]
        self.assertEqual(len(ll.descent_trace(flight, 55)), 2)

    def test_too_short_to_tell(self):
        flight = ll.training()
        flight.trace = [(10, 90)]
        self.assertEqual(ll.descent_trace(flight, 55), [])

    def test_the_debrief_shows_it_where_there_is_room(self):
        mission = ll.missions()[1]
        flight = land(mission)
        for host, shown in ((ll.Host(80, 40), True), (ll.Host(132, 50), True),
                            (ll.Host(80, 24, "16", False), True), (ll.Host(80, 18), False)):
            with self.subTest(size=(host.width, host.height)):
                screen = text(ll.Display(host).draw(flight, "debrief", mission=mission))
                self.assertEqual("BURN " in screen, shown)
        cp437 = ll.Host(80, 40, "256", True, charset="cp437")
        display = ll.Display(cp437)
        canvas = display.draw(flight, "debrief", mission=mission)
        self.assertIn("ALT  #", text(canvas))
        display.encode(canvas)


if __name__ == "__main__":
    unittest.main()
