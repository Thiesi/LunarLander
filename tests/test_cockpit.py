import re
import unittest

import lunar_lander as ll


class DisplayTests(unittest.TestCase):
    def test_geometry_palettes_and_idle_diff(self):
        for width, height in ((80, 24), (132, 50)):
            for depth in ("16", "256", "truecolor"):
                for unicode in (False, True):
                    with self.subTest(size=(width, height), depth=depth, unicode=unicode):
                        display = ll.Display(ll.Host(width, height, depth, unicode))
                        canvas = display.draw(ll.training())
                        frame = display.encode(canvas)
                        self.assertEqual(display.encode(canvas), "")
                        for row, column in re.findall(r"\x1b\[(\d+);(\d+)H", frame):
                            self.assertTrue(1 <= int(row) <= height)
                            self.assertTrue(1 <= int(column) < width)
                        self.assertEqual(len(canvas.cells), height)
                        self.assertTrue(all(len(row) == width - 1 for row in canvas.cells))
                        if not unicode:
                            self.assertTrue(frame.isascii())
                        if depth == "16":
                            self.assertNotRegex(frame, r"\x1b\[(?:38|48);")

    def test_flight_diff_is_smaller_than_full_frame(self):
        display = ll.Display(ll.Host())
        flight = ll.training()
        first = display.encode(display.draw(flight))
        for _ in range(6):
            flight.step()
        second = display.encode(display.draw(flight))
        self.assertNotIn("\x1b[2J", second)
        self.assertLess(len(second), len(first) // 2)

    def test_small_terminal_and_wide_name(self):
        for width, height in ((10, 4), (79, 23), (80, 24)):
            host = ll.Host(width, height, handle="界" * 20)
            canvas = ll.Display(host).draw(ll.training(), "menu")
            for row in canvas.cells:
                columns = sum(2 if char and ll.unicodedata.east_asian_width(char) in "WF" else len(char)
                              for char, _, _ in row)
                self.assertEqual(columns, width - 1)


class GameTests(unittest.TestCase):
    def test_launch_help_pause_and_resize_freeze_physics(self):
        game = ll.Game()
        game.key("enter")
        game.tick(.1, True)
        elapsed = game.flight.elapsed
        game.key("p")
        game.tick(1, True)
        self.assertEqual(game.flight.elapsed, elapsed)
        game.key("?")
        game.tick(1, True)
        game.key("escape")
        self.assertEqual(game.mode, "paused")
        game.key("p")
        game.tick(1, False)
        self.assertEqual(game.flight.elapsed, elapsed)
        game.tick(.1, True)
        self.assertGreater(game.flight.elapsed, elapsed)

    def test_crash_debrief_retry(self):
        game = ll.Game()
        game.key("enter")
        for _ in range(1000):
            game.tick(.1, True)
            if game.mode == "debrief":
                break
        self.assertEqual(game.flight.status, "crashed")
        self.assertIn("Hard impact", game.flight.reason)
        game.key("r")
        self.assertEqual((game.mode, game.flight.elapsed), ("flying", 0))

    def test_slow_output_has_bounded_catchup(self):
        game = ll.Game()
        game.key("enter")
        game.tick(10, True)
        self.assertTrue(game.slow)
        self.assertLessEqual(game.flight.elapsed, .25)


if __name__ == "__main__":
    unittest.main()
