import unittest

import lunar_lander as ll


def rows(canvas):
    return ["".join(cell[0] for cell in row) for row in canvas.cells]


class FuelAlertTests(unittest.TestCase):
    def flight(self, fuel, status="flying"):
        flight = ll.training()
        flight.fuel, flight.y, flight.status = fuel, 60, status
        return flight

    def test_levels_follow_hover_time(self):
        self.assertAlmostEqual(ll.hover_seconds(15), 30.4, places=1)
        for fuel, level in ((90, 0), (16, 0), (14, 1), (6, 1), (4, 2), (0, 3)):
            with self.subTest(fuel=fuel):
                self.assertEqual(ll.fuel_alert(self.flight(fuel)), level)
        # Stronger gravity burns faster in a hover, so the alert comes sooner.
        heavy = self.flight(20)
        heavy.gravity = 3.0
        self.assertEqual(ll.fuel_alert(heavy), 1)

    def chip(self, display, flight, frames):
        canvas = None
        for _ in range(frames):
            canvas = display.draw(flight)
        return rows(canvas)[4], canvas

    def test_low_flashes_as_it_appears_then_holds(self):
        display, flight = ll.Display(ll.Host()), self.flight(14)
        seen = [("LOW FUEL" in self.chip(display, flight, 1)[0]) for _ in range(30)]
        self.assertTrue(any(seen) and not all(seen))
        self.assertTrue(all("LOW FUEL" in self.chip(display, flight, 1)[0] for _ in range(12)))
        self.assertIn("HOVER LEFT", self.chip(display, flight, 1)[0])

    def test_critical_flashes_the_chip_and_the_frame(self):
        display, flight = ll.Display(ll.Host()), self.flight(4)
        lit, rules = [], set()
        for _ in range(12):
            row, canvas = self.chip(display, flight, 1)
            lit.append("FUEL CRITICAL" in row)
            rules.add(canvas.cells[2][0][1])
        self.assertTrue(any(lit) and not all(lit))
        self.assertIn(ll.rgb(8), rules)
        self.assertGreater(len(rules), 1)

    def test_empty_holds_and_the_gauge_says_so(self):
        display, flight = ll.Display(ll.Host()), self.flight(0)
        for _ in range(8):
            row, canvas = self.chip(display, flight, 1)
            self.assertIn("FUEL EXHAUSTED", row)
        self.assertIn("EMPTY", "\n".join(rows(canvas)))

    def test_quiet_with_fuel_or_after_the_flight(self):
        for flight in (self.flight(60), self.flight(4, "landed")):
            with self.subTest(status=flight.status):
                row, _ = self.chip(ll.Display(ll.Host()), flight, 3)
                self.assertNotIn("FUEL", row)

    def test_ascii_hosts_get_the_same_alert(self):
        display = ll.Display(ll.Host(unicode=False))
        row, _ = self.chip(display, self.flight(4), 1)
        self.assertIn("FUEL CRITICAL  -  ", row)


if __name__ == "__main__":
    unittest.main()
