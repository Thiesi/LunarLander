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
        game.key("left")  # the chapter tabs wrap round to DAILY
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
        row = canvas.cells[21]
        text = "".join(cell[0] for cell in row)
        for value, color in (("70%", 5), ("+30", 12), ("3", 6), ("2", 5), ("10", 12)):
            start = text.index(value, text.index("LAND") if value in ("3", "2", "10") else 0)
            self.assertTrue(all(cell[1] == color for cell in row[start:start + len(value)]), (value, row))

    def test_unsafe_speeds_are_named_not_only_colored(self):
        flight = ll.training()
        flight.vy, flight.vx, flight.fuel = -6, 3, 5
        canvas = ll.Display(ll.Host()).draw(flight)
        values = "".join(cell[0] for cell in canvas.cells[19])
        for word in ("FAST", "WIDE", "LOW"):
            self.assertIn(word, values)

    def test_manual_values_stand_out(self):
        canvas = ll.Display(ll.Host()).draw(ll.training(), "help")
        row = next(row for row in canvas.cells if "10%" in "".join(c[0] for c in row))
        start = "".join(c[0] for c in row).index("10%")
        self.assertEqual([c[1] for c in row[start:start + 3]], [6, 6, 6])

    def test_tilt_rotates_the_whole_symmetric_hull(self):
        left, right = ll.lander_roles(-40, .7), ll.lander_roles(40, .7)
        self.assertEqual({(-x, y): role for (x, y), role in left.items()}, right)
        # Tilted right, the window leans right and the plume trails left.
        self.assertTrue(any(x > 0 and role == "W" for (x, _), role in right.items()))
        self.assertTrue(any(x < 0 and role in ll._FLAME for (x, _), role in right.items()))
        self.assertEqual(set(ll.lander_roles(0, .7)), set(ll.lander_pixels(0, .7)))

    def test_sprites_are_rectangular_and_fully_colored(self):
        for rows in (ll._LANDER_SMALL, ll._LANDER_MEDIUM, ll._LANDER_LARGE):
            self.assertEqual(len({len(row) for row in rows}), 1)
        for size in ll.LANDERS:
            for role in ll.lander_roles(20, 1, .3, size).values():
                self.assertIn(role, ll.LANDER_COLORS)
        medium = ll.lander_roles(-30, .5, size="medium"), ll.lander_roles(30, .5, size="medium")
        self.assertEqual({(-x, y): role for (x, y), role in medium[0].items()}, medium[1])

    def test_menu_missions_share_one_grid(self):
        brackets, pips = set(), set()
        for n, chapter in enumerate(ll.CHAPTERS):
            with self.subTest(chapter=chapter.key):
                shelf = ll.chapter_missions(chapter, ll.missions())
                canvas = ll.Display(ll.Host()).draw(ll.training(), "menu", mission=shelf[-1],
                                                    deck=ll.Deck(chapter=n))
                rows = ["".join(cell[0] for cell in row) for row in canvas.cells]
                listed = [row for row in rows if ll.re.search(r"\[[1-9]\] ", row)]
                self.assertEqual(len(listed), len(shelf))
                self.assertIn(chapter.name, " ".join(rows))
                brackets |= {row.index("]") for row in listed}
                # Difficulty pips start in one column whatever the mission's name.
                pips |= {min(i for i in (row.find("■"), row.find("free")) if i >= 0) for row in listed}
        self.assertEqual((len(brackets), len(pips)), (1, 1))

    def test_stars_never_sit_on_scenery(self):
        display = ll.Display(ll.Host(132, 50))
        canvas = display.draw(ll.training(), "splash", scene_age=6)
        for row in canvas.cells:
            for char, _, bg in row:
                if char in "·+*":
                    self.assertLess(max(ll.rgb(bg)), 70, bg)

    def test_scenery_colors_map_to_every_depth(self):
        for color in ((7, 12, 25), (248, 204, 96), (120, 226, 240), (204, 66, 42), (126, 130, 148)):
            self.assertTrue(16 <= ll.xterm256(color) <= 255)
            self.assertTrue(0 <= ll.ansi16(color) <= 15)
        self.assertEqual(ll.ansi16((204, 66, 42)) % 8, 1)
        self.assertEqual(ll.ansi16((248, 204, 96)) % 8, 3)
        self.assertEqual(ll.ansi16((3, 5, 14)), 0)

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


class PlaytestFindingTests(unittest.TestCase):
    def rows(self, canvas):
        return ["".join(cell[0] for cell in row) for row in canvas.cells]

    def test_ranking_notes_are_never_cut_by_the_card_rule(self):
        for note in ("RANKED FLIGHT / best landing per pilot",
                     "PRACTICE ONLY / no persistent NetBBS caller identity",
                     "PRACTICE ONLY / pilot records unavailable"):
            with self.subTest(note=note):
                canvas = ll.Display(ll.Host()).draw(ll.training(), "menu", mission=ll.missions()[1],
                                                    record_note=note)
                text = " ".join(self.rows(canvas))
                for line in ll.textwrap.wrap(note, 36):
                    self.assertIn(line, text)

    def test_q_returns_at_once_except_mid_flight(self):
        for mode in ("menu", "debrief", "scores", "splash"):
            with self.subTest(mode=mode):
                game = ll.Game(scenes=True)
                game.mode = mode
                self.assertTrue(game.key("q"))
                self.assertTrue(game.leaving)

    def test_q_mid_flight_asks_and_freezes_the_flight(self):
        for mode in ("flying", "paused", "help"):
            with self.subTest(mode=mode):
                game = ll.Game()
                game.key("enter")
                game.tick(.1, True)
                if mode == "paused":
                    game.key("p")
                elif mode == "help":
                    game.key("?")
                game.key("q")
                self.assertEqual((game.mode, game.leaving), ("confirm", False))
                elapsed = game.flight.elapsed
                game.tick(1, True)
                game.key("w")
                self.assertEqual((game.flight.elapsed, game.flight.throttle), (elapsed, 0))
                game.key("n")
                self.assertEqual(game.mode, "paused" if mode == "paused" else "flying")
                game.key("q")
                game.key("y")
                self.assertTrue(game.leaving)

    def test_control_c_and_d_still_exit_immediately(self):
        self.assertEqual(ll.Keys().feed(b"q", 0), ["abort", "abort", "q"])

    def test_return_names_the_bbs(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "door.json"
            for name, expected in (("Moonbase [7]", "Moonbase 7"), (None, "NetBBS"), ("   ", "NetBBS")):
                data = {"door_api": 5} if name is None else {"door_api": 5, "node_name": name}
                path.write_text(ll.json.dumps(data), encoding="utf-8")
                self.assertEqual(ll.Host.load(str(path)).bbs, expected)
        host = ll.Host(bbs="Moonbase 7")
        for mode in ("menu", "flying", "debrief", "help", "paused", "confirm"):
            with self.subTest(mode=mode):
                text = " ".join(self.rows(ll.Display(host).draw(ll.training(), mode)))
                self.assertIn("Return to Moonbase 7", text)

    def test_cursor_keys_are_advertised(self):
        for unicode, tilt, thrust in ((True, "←→", "↑↓"), (False, "<>", "^v")):
            for mode in ("flying", "menu", "help"):
                with self.subTest(unicode=unicode, mode=mode):
                    text = " ".join(self.rows(ll.Display(ll.Host(unicode=unicode)).draw(ll.training(), mode)))
                    self.assertIn(f"A/D {tilt}", text)
                    self.assertIn(f"W/S {thrust}", text)


class CpuBudgetTests(unittest.TestCase):
    def test_estimates_from_the_recent_rate_and_stops_before_the_ceiling(self):
        used = [0.0]
        budget = ll.CpuBudget(limit=60, usage=lambda: used[0])
        self.assertGreater(budget.remaining(0), 1000)
        used[0] = 5.0
        # 5 CPU-seconds over 10 s: half a CPU, 52 seconds of budget left.
        self.assertAlmostEqual(budget.remaining(10), 104)
        used[0] = 57.5
        self.assertEqual(budget.remaining(20), 0)

    def test_no_ceiling_means_no_estimate(self):
        self.assertIsNone(ll.CpuBudget(limit=None, usage=lambda: 1.0).remaining(0))

    def test_shipped_profile_has_headroom(self):
        profile = ll.json.loads((Path(__file__).resolve().parents[1] / "profiles/netbbs.json").read_text())
        self.assertGreaterEqual(profile["profile"]["cpu_seconds"], 900)


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
        # Played out, the splash holds under its prompt until a key, which it spends.
        game.tick(30, True)
        self.assertEqual(game.mode, "splash")
        canvas = ll.Display(ll.Host()).draw(game.flight, "splash", scene_age=game.scene_age)
        self.assertIn(ll.SPLASH_PROMPT, "".join(cell[0] for cell in canvas.cells[-1]))
        self.assertTrue(game.key("w"))
        self.assertEqual((game.mode, game.flight.throttle), ("menu", 0))
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
                # A first, soft landing: gold, which promotes a cadet. Each skip key
                # is spent on its own scene, never on the debrief behind them.
                self.assertEqual((game.award.medal, game.award.promoted), ("GOLD", "PILOT"))
                shown = []
                for _ in range(3):
                    game.key("r")
                    shown.append(game.mode)
                self.assertEqual(shown, ["medal", "promotion", "debrief"])
                self.assertEqual(len(records.top(host, game.mission)), 1)
            finally:
                records.close()


if __name__ == "__main__":
    unittest.main()
