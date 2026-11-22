import unittest

import lunar_lander as ll


def text(canvas, rows=None):
    return "\n".join("".join(cell[0] for cell in canvas.cells[row]) for row in (rows or range(canvas.height)))


class CardTests(unittest.TestCase):
    def draw(self, mode, width=80, height=24, **kwargs):
        flight = ll.training()
        if mode == "debrief":
            flight.status, flight.reason = "crashed", "Hard impact: reduce vertical speed to 3 m/s or less."
        return ll.Display(ll.Host(width, height, **kwargs)).draw(flight, mode, standings=[("Ace", 1780, 3)])

    LABELS = ("ALTITUDE", "VERTICAL", "DRIFT", "TILT", "THRUST", "FUEL", "[SPACE] Cut")

    def test_a_card_never_leaves_gauges_half_hidden(self):
        # At 80x24 the manual reaches the instruments: the panel is cleared
        # edge to edge rather than showing fragments beside the card.
        instruments = text(self.draw("help"), range(24 - ll.PANEL_ROWS, 24))
        for label in self.LABELS:
            self.assertNotIn(label, instruments)
        # Whatever the card and the screen, the instruments show whole or not at all.
        for mode in ("help", "debrief", "paused", "scores", "confirm", "presets", "tour"):
            for size in ((80, 24), (80, 30), (132, 50)):
                with self.subTest(mode=mode, size=size):
                    canvas = self.draw(mode, *size)
                    instruments = text(canvas, range(canvas.height - ll.PANEL_ROWS, canvas.height))
                    self.assertIn(sum(label in instruments for label in self.LABELS), (0, len(self.LABELS)))

    def test_a_card_that_misses_the_instruments_leaves_them(self):
        for mode, size in (("paused", (80, 24)), ("scores", (80, 24)), ("debrief", (80, 24)), ("help", (132, 50))):
            with self.subTest(mode=mode, size=size):
                canvas = self.draw(mode, *size)
                instruments = text(canvas, range(canvas.height - ll.PANEL_ROWS, canvas.height))
                for label in self.LABELS:
                    self.assertIn(label, instruments)
                self.assertIn("FLIGHT TRAINING BASIN", text(canvas, range(0, ll.HEAD_ROWS)))

    def test_the_flight_director_sits_over_the_landing_site(self):
        # No instruments behind the flight director: the mission's site, whole, under the card.
        for size in ((80, 24), (80, 30), (132, 50)):
            with self.subTest(size=size):
                display = ll.Display(ll.Host(*size))
                canvas = display.draw(ll.training(), "menu")
                x, y, width, card = display.menu_box(canvas)
                self.assertIn("LUNAR LANDER" if size[0] < 100 else "L U N A R", text(canvas, range(0, ll.HEAD_ROWS)))
                below = text(canvas, range(y + card, canvas.height))
                for words in ("PAD", "START"):
                    self.assertIn(words, below)
                for label in self.LABELS:
                    self.assertNotIn(label, below)
                # The site is drawn, not dimmed away: lit ground reaches the last row.
                self.assertGreater(max(ll.rgb(canvas.cells[-1][canvas.width // 2][2])), 40)

    def test_the_viewers_own_row_stands_out(self):
        standings = [("Ace", 1780, 3), ("Thiesi", 1650, 7), ("Nib", 1400, 9)]
        for user, marked in ((7, "Thiesi"), (12, None)):
            with self.subTest(user=user):
                host = ll.Host(node="n", user=user, handle="Thiesi")
                canvas = ll.Display(host).draw(ll.training(), "scores", standings=standings)
                rows = ["".join(cell[0] for cell in row) for row in canvas.cells
                        if any(cell[2] == ll.HIGHLIGHT for cell in row)]
                self.assertEqual([marked in row for row in rows], [True] if marked else [])
        # A practice caller (no node) is never marked, even with a matching id.
        canvas = ll.Display(ll.Host(user=7)).draw(ll.training(), "scores", standings=standings)
        self.assertFalse(any(cell[2] == ll.HIGHLIGHT for row in canvas.cells for cell in row))


class CompactMenuTests(unittest.TestCase):
    def test_compact_below_31_rows_full_above(self):
        for height, rows in ((24, 15), (30, 15), (31, 18), (50, 18)):
            with self.subTest(height=height):
                display = ll.Display(ll.Host(80, height))
                x, y, width, card = display.menu_box(ll.Canvas(80, height))
                self.assertEqual(card, rows)
                # The card leaves the landing site in view below it.
                self.assertLessEqual(y + card, height - 6)
                text = "\n".join("".join(cell[0] for cell in row) for row in
                                 display.draw(ll.training(), "menu", mission=ll.missions()[1]).cells[y:y + card])
                for words in ("FLIGHT DIRECTOR", "[ENTER] Launch", "Return to NetBBS", "PAD", "GOLD"):
                    self.assertIn(words, text)


if __name__ == "__main__":
    unittest.main()
