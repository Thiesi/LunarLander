import json
import os
from pathlib import Path
import tempfile
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

    def test_narrow_columns_map_both_ways(self):
        # Square column s is narrow columns 2s and 2s + 1.
        for s in range(-5, 6):
            self.assertEqual({ll._column(ll._centre(x, 2), 2) for x in (2 * s, 2 * s + 1)}, {2 * s, 2 * s + 1})
            self.assertEqual({round(ll._centre(x, 2)) for x in (2 * s, 2 * s + 1)}, {s})
            self.assertEqual(ll._column(s, 1), s)

    def test_fine_art_matches_the_square_art(self):
        # The fine landers keep each size's rows and footprint, two columns to one.
        for size in ("small", "medium", "large"):
            with self.subTest(size=size):
                square, fine = ll.LANDERS[size], ll.LANDERS_FINE[size]
                self.assertEqual(square[1:], fine[1:])
                self.assertEqual({y for _, y in square[0]}, {y for _, y in fine[0]})
                self.assertEqual(min(x for x, _ in fine[0]), 2 * min(x for x, _ in square[0]))
                self.assertEqual(max(x for x, _ in fine[0]), 2 * max(x for x, _ in square[0]) + 1)
                self.assertTrue(set(fine[0].values()) <= set(ll.LANDER_COLORS) - set(ll._FLAME))
        for letter, rows in ll._FONT_FINE.items():
            self.assertEqual([len(row) for row in rows], [12] * 7, letter)

    def test_half_mode_sprites_are_unchanged(self):
        # The square art draws as before: fixed points from v0.1.0.
        self.assertEqual(len(ll.medal_sprite("GOLD", 10)), 496)
        self.assertEqual(sorted(ll.insignia(6, 6))[:3], [(-6, -15), (-6, -14), (-6, -12)])
        self.assertEqual(len(ll.wordmark(("LUNAR", "LANDER"))["sprite"]), 465)

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

    def load(self, **fields):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "door.json"
            path.write_text(json.dumps({"door_api": 5, "unicode_style": True, **fields}), encoding="utf-8")
            return ll.Host.load(str(path))

    def test_the_callers_character_set_decides(self):
        # NetBBS converts our output to the caller's set (NetBBS #1557): quadrants
        # only reach a UTF-8 terminal; CP437 has half blocks; ASCII gets ASCII glyphs.
        with mock.patch.dict(os.environ, {"DOOR_LL_PIXELS": ""}):
            for fields, charset, unicode, across in (({}, None, True, 2),
                                                     ({"charset": "utf-8"}, "utf-8", True, 2),
                                                     ({"charset": "cp437"}, "cp437", True, 1),
                                                     ({"charset": "ascii"}, "ascii", False, 1),
                                                     ({"charset": "ebcdic"}, None, True, 2),
                                                     ({"charset": 437}, None, True, 2)):
                with self.subTest(fields=fields):
                    host = self.load(**fields)
                    self.assertEqual((host.charset, host.unicode, ll.Display(host).across),
                                     (charset, unicode, across))

    def test_a_cp437_caller_never_gets_a_quadrant(self):
        quadrants = set(ll.QUADRANTS[1:]) - {"▀", "▌", "▐", "▄", "█"}
        host = ll.Host(132, 50, "256", True, pixels="quad", charset="cp437")
        for mode in ("flying", "splash", "launch", "landing", "crash", "medal", "promotion"):
            with self.subTest(mode=mode):
                flight = ll.training()
                flight.angle = 15
                canvas = ll.Display(host).draw(flight, mode, scene_age=1.2)
                self.assertFalse({cell[0] for row in canvas.cells for cell in row} & quadrants)

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
