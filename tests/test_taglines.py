import unittest

import lunar_lander as ll


def rows(canvas):
    return ["".join(cell[0] for cell in row) for row in canvas.cells]


class TaglineTests(unittest.TestCase):
    def test_taglines_fit_and_one_is_picked_per_session(self):
        self.assertGreaterEqual(len(set(ll.TAGLINES)), 10)
        self.assertTrue(all(t.isascii() and t == t.upper() for t in ll.TAGLINES))
        # Every tagline fits beside the wordmark on an 80-column splash.
        self.assertLessEqual(max(map(len, ll.TAGLINES)), 74)
        self.assertIn(ll.Display(ll.Host()).tagline, ll.TAGLINES)

    def test_the_splash_shows_the_sessions_tagline(self):
        for tagline in ll.TAGLINES:
            with self.subTest(tagline=tagline):
                display = ll.Display(ll.Host())
                display.tagline = tagline
                self.assertIn(tagline, "\n".join(rows(display.draw(ll.training(), "splash", scene_age=5.0))))


if __name__ == "__main__":
    unittest.main()
