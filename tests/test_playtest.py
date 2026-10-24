from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

import lunar_lander as ll


class DailyTests(unittest.TestCase):
    def clock(self, zone, instant, fmt="%Y-%m-%d"):
        result = ll.DailyClock(zone, fmt, now=lambda: instant)
        self.assertEqual(result.warning, "", "Install tzdata for Windows development tests")
        return result

    def test_node_midnight_is_not_utc_midnight(self):
        instant = datetime(2026, 10, 24, 22, 30, tzinfo=timezone.utc)
        self.assertEqual(self.clock("Europe/Berlin", instant).day(), "2026-10-25")
        self.assertEqual(self.clock("America/Los_Angeles", instant).day(), "2026-10-24")

    def test_dst_fall_back_does_not_repeat_or_skip_a_challenge(self):
        for hour in (0, 1, 2, 22):
            instant = datetime(2026, 10, 25, hour, 30, tzinfo=timezone.utc)
            self.assertEqual(self.clock("Europe/Berlin", instant).day(), "2026-10-25")
        self.assertEqual(self.clock("Europe/Berlin", datetime(2026, 10, 25, 23, 30, tzinfo=timezone.utc)).day(), "2026-10-26")

    def test_rollover_updates_menu_but_keeps_active_flight(self):
        now = [datetime(2026, 10, 24, 21, 59, tzinfo=timezone.utc)]
        clock = ll.DailyClock("Europe/Berlin", "%d.%m.%Y", now=lambda: now[0])
        self.assertFalse(clock.warning)
        game = ll.Game(clock=clock)
        game.key("5")
        self.assertEqual(game.mission.name, "DAILY 24.10.2026")
        game.key("enter")
        now[0] = datetime(2026, 10, 24, 22, 1, tzinfo=timezone.utc)
        game.tick(.1, True)
        self.assertEqual(game.mission.key, "daily-2026-10-24")
        game.mode = "debrief"
        game.key("r")
        self.assertEqual(game.mission.key, "daily-2026-10-25")
        self.assertEqual(game.mission.name, "DAILY 25.10.2026")
        game.mode = "menu"
        now[0] = datetime(2026, 10, 26, 23, 1, tzinfo=timezone.utc)
        game.tick(.1, True)
        self.assertEqual(game.mission.key, "daily-2026-10-27")

    def test_day_changes_the_actual_flight_not_just_the_label(self):
        a, b = ll.missions("2026-10-24")[4].launch(), ll.missions("2026-10-25")[4].launch()
        self.assertNotEqual(a.terrain, b.terrain)
        self.assertNotEqual(a.x, b.x)
        formatted = ll.missions("2026-10-24", "%d/%m/%Y")[4].launch()
        self.assertEqual(a.terrain.points, formatted.terrain.points)
        self.assertEqual((a.x, a.y, a.fuel, a.vx, a.vy),
                         (formatted.x, formatted.y, formatted.fuel, formatted.vx, formatted.vy))

    def test_missing_zone_data_and_invalid_format_are_visible(self):
        clock = ll.DailyClock("missing/zone", "%n%Q")
        self.assertIn("UTC", clock.warning)
        self.assertIn("ISO", clock.warning)
        self.assertEqual(clock.date_format, "%Y-%m-%d")


class PresentationTests(unittest.TestCase):
    def test_exact_hotkey_color_order(self):
        canvas = ll.Canvas(80, 24)
        canvas.annotated(0, 0, "[R] Retry", bg=1)
        self.assertEqual(canvas.cells[0][:4], [("[", 9, 1), ("R", 5, 1), ("]", 9, 1), (" ", 7, 1)])
        self.assertTrue(all(color == 7 for _, color, _ in canvas.cells[0][4:9]))

    def test_thrust_tilt_and_threshold_colors(self):
        flight = ll.training()
        flight.angle, flight.throttle = 30, .7
        canvas = ll.Display(ll.Host()).draw(flight)
        row = canvas.cells[20]
        text = "".join(cell[0] for cell in row)
        for value, color in (("70%", 5), ("+30", 12), ("3", 6), ("2", 5), ("10", 12)):
            start = text.index(value, 46 if value in ("3", "2", "10") else 0)
            self.assertTrue(all(cell[1] == color for cell in row[start:start + len(value)]), (value, row))

    def test_manual_values_stand_out(self):
        canvas = ll.Display(ll.Host()).draw(ll.training(), "help")
        row = next(row for row in canvas.cells if "10%" in "".join(c[0] for c in row))
        start = "".join(c[0] for c in row).index("10%")
        self.assertEqual([c[1] for c in row[start:start + 3]], [6, 6, 6])

    def test_tilt_rotates_the_whole_symmetric_hull(self):
        left, right = ll.lander_pixels(-40, .7), ll.lander_pixels(40, .7)
        self.assertEqual({(-x, y): c for (x, y), c in left.items()}, right)
        self.assertTrue(any(x > 0 and color == 6 for (x, _), color in right.items()))
        self.assertTrue(any(x < 0 and color == 8 for (x, _), color in right.items()))

    def test_all_scenes_change_and_fit_in_supported_modes(self):
        for width, height in ((80, 24), (132, 50)):
            for unicode in (True, False):
                for scene in ll.SCENE_SECONDS:
                    with self.subTest(size=(width, height), scene=scene, unicode=unicode):
                        display = ll.Display(ll.Host(width, height, unicode=unicode))
                        first = display.draw(ll.training(), scene, scene_age=.1)
                        later = display.draw(ll.training(), scene, scene_age=1)
                        self.assertNotEqual(first.cells, later.cells)
                        self.assertEqual(len(later.cells), height)
                        self.assertTrue(all(len(row) == width - 1 for row in later.cells))
                        if not unicode:
                            self.assertTrue(display.encode(later).isascii())


class SceneLifecycleTests(unittest.TestCase):
    def test_scene_skip_key_does_not_become_flight_control(self):
        game = ll.Game(scenes=True, splash=True)
        game.tick(1, True)
        self.assertEqual(game.flight.elapsed, 0)
        game.key("enter")
        self.assertEqual(game.mode, "menu")
        game.key("enter")
        self.assertEqual(game.mode, "launch")
        game.key("9")
        self.assertEqual(game.mode, "flying")
        self.assertEqual(game.flight.throttle, 0)

    def test_scene_finishes_without_advancing_physics_and_respects_small_size(self):
        game = ll.Game(scenes=True, splash=True)
        game.tick(10, False)
        self.assertEqual((game.mode, game.scene_age), ("splash", 0))
        game.tick(4, True)
        self.assertEqual(game.mode, "menu")
        game.key("enter")
        game.tick(2, True)
        self.assertEqual((game.mode, game.flight.elapsed), ("flying", 0))

    def test_save_commits_before_landing_animation(self):
        with tempfile.TemporaryDirectory() as directory:
            records = ll.Records(Path(directory) / "pilots.db")
            try:
                host = ll.Host(node="test", user=1)
                game = ll.Game(host, records, scenes=True)
                game.key("2")
                game.key("enter")
                game.key(" ")
                game.flight.x = game.mission.center
                game.flight.y = game.flight.terrain.pad.height + 3
                game.flight.vx, game.flight.vy = 0, -1
                game.tick(.1, True)
                self.assertEqual(game.mode, "landing")
                self.assertEqual(len(records.top(host, game.mission)), 1)
                game.key("r")
                self.assertEqual(game.mode, "debrief")
                self.assertEqual(len(records.top(host, game.mission)), 1)
            finally:
                records.close()


if __name__ == "__main__":
    unittest.main()
