import os
import unittest
from unittest import mock

import lunar_lander as ll

RED, BLUE, WHITE, BLACK = (200, 0, 0), (0, 0, 200), (255, 255, 255), (0, 0, 0)


class QuadrantTests(unittest.TestCase):
    def test_two_colors_are_exact(self):
        self.assertEqual(ll.quadrant(RED, RED, RED, RED), (" ", 7, RED))
        self.assertEqual(ll.quadrant(RED, RED, BLUE, BLUE), ("▀", RED, BLUE))
        self.assertEqual(ll.quadrant(RED, BLUE, RED, BLUE), ("▌", RED, BLUE))
        self.assertEqual(ll.quadrant(BLUE, RED, RED, BLUE), ("▞", RED, BLUE))
        self.assertEqual(ll.quadrant(RED, RED, RED, BLUE), ("▛", RED, BLUE))

    def test_more_colors_keep_the_odd_one_out_apart(self):
        # Three near-whites and a black: the black keeps its own color.
        char, fg, bg = ll.quadrant(WHITE, (250, 250, 250), (245, 245, 245), BLACK)
        self.assertEqual((char, fg, bg), ("▛", (250, 250, 250), BLACK))
        # Red, blue and two blacks: one bright color stands alone, the other darkens the blacks.
        self.assertIn(ll.quadrant(RED, BLUE, BLACK, BLACK), {("▘", RED, (0, 0, 67)), ("▝", BLUE, (67, 0, 0))})

    def test_widen_doubles_columns_about_the_same_centre(self):
        self.assertEqual(ll.widen({(0, 0): 1, (-1, 2): 2}, 2), {(0, 0): 1, (1, 0): 1, (-2, 2): 2, (-1, 2): 2})
        self.assertEqual(ll.lander_roles(0, .7, size="small", across=2),
                         ll.widen(ll.lander_roles(0, .7, size="small"), 2))

    def test_narrow_pixels_keep_a_tilted_hull_symmetric(self):
        for size in ("small", "medium"):  # the large craft is drawn three-quarter, not symmetric
            with self.subTest(size=size):
                left, right = (ll.lander_roles(angle, .5, size=size, across=2) for angle in (-30, 30))
                # Source column 0 covers narrow columns 0 and 1, so column t mirrors to 1 - t.
                self.assertEqual({(1 - x, y): role for (x, y), role in left.items()}, right)

    def test_half_mode_scenery_is_unchanged(self):
        # The stage in cells is the same composition either way: quad pixels average to the half pixels.
        for cols in (79, 80, 131):
            half, quad = ll.stage(cols, 30), ll.stage(cols, 30, 2)
            self.assertEqual(half.pad[0] * 2, quad.pad[0])
            self.assertEqual(half.pad[1] * 2 + 1, quad.pad[1])
            drift = sum(abs(sum(half.pixels[y][x]) - (sum(quad.pixels[y][2 * x]) + sum(quad.pixels[y][2 * x + 1])) / 2)
                        for y in range(60) for x in range(cols)) / (60 * cols * 3)
            self.assertLess(drift, 3)


class DisplayPixelTests(unittest.TestCase):
    def test_setting_and_default(self):
        with mock.patch.dict(os.environ, {"DOOR_LL_PIXELS": ""}):
            self.assertEqual(ll.Display(ll.Host()).across, 2)
            self.assertEqual(ll.Display(ll.Host(unicode=False)).across, 1)
        with mock.patch.dict(os.environ, {"DOOR_LL_PIXELS": "half"}):
            self.assertEqual(ll.Display(ll.Host()).across, 1)

    def test_every_view_draws_in_quadrants_or_ascii(self):
        quadrants = set(ll.QUADRANTS[1:])
        for unicode in (True, False):
            for mode in ("flying", "splash", "launch", "landing", "crash", "medal", "promotion"):
                with self.subTest(unicode=unicode, mode=mode):
                    display = ll.Display(ll.Host(132, 50, "256", unicode, pixels="quad"))
                    flight = ll.training()
                    flight.angle = 15
                    canvas = display.draw(flight, mode, scene_age=1.2)
                    glyphs = {cell[0] for row in canvas.cells for cell in row}
                    if unicode:
                        self.assertTrue(glyphs & quadrants - {"▀"}, "narrow pixels in use")
                    else:
                        self.assertFalse(glyphs & quadrants)
                        self.assertTrue(display.encode(canvas).isascii())


if __name__ == "__main__":
    unittest.main()
