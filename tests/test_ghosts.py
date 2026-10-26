from pathlib import Path
import tempfile
import unittest

import lunar_lander as ll
from test_career import touch_down
from test_records import land


def screen(canvas):
    return "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)


class ReplayTests(unittest.TestCase):
    def test_every_mission_flies_again_exactly(self):
        for mission in (*ll.missions("2026-10-31")[1:], ll.daily_missions("2026-11-01")[2]):
            with self.subTest(mission=mission.key):
                flight = land(mission)
                data = ll.ghost_data(flight)
                self.assertLess(len(data), 4096)
                ghost = ll.Ghost(mission, data, "x")
                self.assertTrue(ghost.faithful())
                self.assertEqual((ghost.flight.status, ghost.flight.fuel), (flight.status, flight.fuel))

    def test_it_keeps_pace_step_for_step(self):
        mission = ll.missions()[1]
        flight = land(mission)
        ghost = ll.Ghost(mission, ll.ghost_data(flight), "x")
        ghost.advance(100)
        self.assertEqual(ghost.flight.steps, 100)
        replayed = mission.launch()
        for _ in range(100):
            for step, throttle, angle in flight.log:
                if step == replayed.steps:
                    replayed.throttle, replayed.angle = throttle, angle
            replayed.step()
        self.assertEqual((ghost.flight.x, ghost.flight.y), (replayed.x, replayed.y))

    def test_the_log_records_only_changes(self):
        flight = ll.missions()[1].launch()
        for key in ("9", "5", "d"):
            flight.command(key)
            for _ in range(5):
                flight.step()
        self.assertEqual([entry[0] for entry in flight.log], [0, 5, 10])

    def test_unknown_formats_are_refused(self):
        import json, zlib
        with self.assertRaises(ValueError):
            ll.Ghost(ll.missions()[1], zlib.compress(json.dumps({"v": 9}).encode()), "x")


class RecordsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.records = ll.Records(Path(self.temp.name) / "pilots.db")
        self.host = ll.Host(node="n", user=7, handle="Nib")

    def tearDown(self):
        self.records.close()
        self.temp.cleanup()

    def test_a_new_best_keeps_its_ghost_and_a_worse_run_does_not(self):
        mission = ll.missions()[1]
        best = land(mission)
        self.assertTrue(self.records.save(self.host, mission, best))
        stored = self.records.ghost(self.host, mission)
        self.assertEqual(stored, ll.ghost_data(best))
        worse = mission.launch()
        touch = ll.Game(self.host, self.records)
        touch.flight = worse
        worse.status, worse.fuel = "landed", 1
        self.assertFalse(self.records.save(self.host, mission, worse))
        self.assertEqual(self.records.ghost(self.host, mission), stored)

    def test_old_daily_ghosts_are_cleared(self):
        old = ll.daily_missions("2026-01-01")[0]
        self.records.save(self.host, old, land(old))
        self.records.db.execute("UPDATE ghosts SET recorded=1")
        today = ll.daily_missions("2026-10-26")[0]
        self.records.save(self.host, today, land(today))
        self.assertIsNone(self.records.ghost(self.host, old))
        self.assertIsNotNone(self.records.ghost(self.host, today))


class GameTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.records = ll.Records(Path(self.temp.name) / "pilots.db")
        self.host = ll.Host(node="n", user=7, handle="Nib")
        self.game = ll.Game(self.host, self.records)
        self.game.scenes = False
        self.game.key("2")  # Tranquility
        self.mission = self.game.mission

    def tearDown(self):
        self.records.close()
        self.temp.cleanup()

    def store(self, host, flight=None):
        self.records.save(host, self.mission, flight or land(self.mission))

    def test_the_choice_cycles_and_names_what_there_is(self):
        self.assertEqual(self.game.ghost_choice(), "yours, once you land")
        self.game.key("g")
        self.assertEqual(self.game.ghost_choice(), "node best, none yet")
        self.store(ll.Host(node="n", user=9, handle="Ace"))
        self.assertEqual(self.game.ghost_choice(), "Ace's best")
        self.game.key("g")
        self.assertEqual(self.game.ghost_choice(), "off")
        self.game.key("g")
        self.assertEqual(self.game.ghost_mode, "mine")

    def test_flying_beside_your_best(self):
        self.store(self.host)
        self.game.key("enter")
        self.assertIsNotNone(self.game.ghost)
        self.game.mode = "flying"
        for _ in range(30):
            self.game.tick(.1, True)
        self.assertEqual(self.game.ghost.flight.steps, self.game.flight.steps)
        deck = ll.Deck(ghost=self.game.ghost)
        text = screen(ll.Display(ll.Host(80, 24)).draw(self.game.flight, mission=self.mission, deck=deck))
        self.assertIn("GHOST your best", text)

    def test_the_debrief_compares_with_the_ghost(self):
        self.store(self.host)
        self.game.key("enter")
        self.game.mode = "flying"
        touch_down(self.game, fuel=30)
        self.assertEqual(self.game.ghost.flight.status, "landed")  # flown to its end
        deck = ll.Deck(ghost=self.game.ghost)
        text = screen(ll.Display(ll.Host(80, 40)).draw(self.game.flight, "debrief", mission=self.mission,
                                                       deck=deck))
        self.assertIn("Against the ghost:", text)
        self.assertIn("faster", text)

    def test_simulator_and_program_flights_fly_alone(self):
        self.store(self.host)
        self.game.launch("sim")
        self.assertIsNone(self.game.ghost)

    def test_watching_the_leader(self):
        self.store(ll.Host(node="n", user=9, handle="Ace"))
        self.game.key("b")
        self.assertIn("[W] Watch the leader", screen(ll.Display(ll.Host(80, 24)).draw(
            self.game.flight, "scores", mission=self.mission, standings=self.game.standings)))
        self.assertTrue(self.game.key("w"))
        self.assertEqual(self.game.mode, "replay")
        for _ in range(400):
            self.game.tick(.25, True)
            if self.game.mode != "replay":
                break
        self.assertEqual(self.game.mode, "scores")
        self.game.key("w")
        self.game.tick(.25, True)
        deck = ll.Deck(kind="replay", ghost=self.game.replay)
        text = screen(ll.Display(ll.Host(80, 24)).draw(self.game.replay.flight, "replay", mission=self.mission,
                                                       deck=deck))
        self.assertIn("REPLAY", text)
        self.assertIn("WATCHING Ace's best", text)
        self.game.key(" ")
        self.assertEqual(self.game.mode, "scores")

    def test_nothing_to_watch_on_an_empty_board(self):
        self.game.key("b")
        self.assertFalse(self.game.key("w"))


if __name__ == "__main__":
    unittest.main()
