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

    def test_a_card_never_leaves_gauges_half_hidden(self):
        # At 80x24 the manual and debrief reach the instruments: the panel is
        # cleared edge to edge rather than showing fragments beside the card.
        for mode in ("help", "debrief"):
            with self.subTest(mode=mode):
                instruments = text(self.draw(mode), range(17, 24))
                for label in ("ALTITUDE", "THRUST", "FUEL", "Flight manual"):
                    self.assertNotIn(label, instruments)

    def test_a_card_that_misses_the_instruments_leaves_them(self):
        # The flight director is compact below 33 rows, so the cockpit shows whole beneath it.
        for mode, size in (("paused", (80, 24)), ("scores", (80, 24)), ("menu", (80, 24)), ("menu", (80, 30)),
                           ("help", (132, 50)), ("menu", (132, 50))):
            with self.subTest(mode=mode, size=size):
                canvas = self.draw(mode, *size)
                self.assertIn("ALTITUDE", text(canvas, range(canvas.height - 7, canvas.height)))
                self.assertIn("L U N A R", text(canvas, range(0, 2)))

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
    def test_compact_below_33_rows_full_above(self):
        for height, rows in ((24, 15), (32, 15), (33, 20), (50, 20)):
            with self.subTest(height=height):
                display = ll.Display(ll.Host(80, height))
                x, y, width, card = display.menu_box(ll.Canvas(80, height))
                self.assertEqual(card, rows)
                # The card ends above the instruments; its shadow reaches their rule at most.
                self.assertLessEqual(y + card, height - 7)
                text = "\n".join("".join(cell[0] for cell in row) for row in
                                 display.draw(ll.training(), "menu", mission=ll.missions()[1]).cells[y:y + card])
                for words in ("FLIGHT DIRECTOR", "[ENTER] Launch", "Return to NetBBS", "PAD", "GOLD"):
                    self.assertIn(words, text)


if __name__ == "__main__":
    unittest.main()
