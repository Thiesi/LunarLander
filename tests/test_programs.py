from datetime import datetime, timezone
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

import lunar_lander as ll
from test_career import touch_down
from test_records import land

SEASON = "2026-11"


def clock():
    return ll.DailyClock("UTC", "%Y-%m-%d", now=lambda: datetime(2026, 11, 3, 12, tzinfo=timezone.utc))


class GenerationTests(unittest.TestCase):
    def test_a_season_is_five_to_eight_climbing_missions(self):
        lengths = set()
        for month in range(1, 13):
            season = f"2027-{month:02d}"
            program = ll.program_missions(season)
            lengths.add(len(program))
            self.assertTrue(5 <= len(program) <= 8)
            self.assertEqual([m.key for m in program], [f"program-{season}-{n}" for n in range(1, len(program) + 1)])
            self.assertLessEqual(program[0].difficulty, 2)
            self.assertGreaterEqual(program[-1].difficulty, 4)
            self.assertEqual([m.difficulty for m in program], sorted(m.difficulty for m in program))
        self.assertGreater(len(lengths), 1)  # the length varies by season

    def test_the_same_program_everywhere(self):
        code = f"import lunar_lander as l; print([repr(m.launch()) for m in l.program_missions('{SEASON}')])"
        self.assertEqual(subprocess.check_output([sys.executable, "-c", code]),
                         subprocess.check_output([sys.executable, "-c", code]))

    def test_the_real_flight_varies_only_its_start_and_stays_landable(self):
        for mission in ll.program_missions("2027-02"):
            for seed in range(4):
                with self.subTest(mission=mission.key, seed=seed):
                    flown, change = ll.varied(mission, random.Random(seed))
                    self.assertEqual(flown.launch().terrain, mission.launch().terrain)
                    self.assertLessEqual(abs(flown.drift - mission.drift), abs(mission.drift) * .15 + .01)
                    self.assertLessEqual(abs(flown.offset - mission.offset), 10.1)
                    self.assertTrue(0 <= mission.fuel - flown.fuel <= 3)
                    self.assertLessEqual(abs(flown.sink - mission.sink), .5)
                    self.assertEqual(json.loads(json.dumps(change)), change)
                    flight = land(flown)
                    self.assertEqual(flight.status, "landed", flight.reason)


class RecordsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "pilots.db"
        self.records = ll.Records(self.path)
        self.host = ll.Host(node="n", user=7, handle="Nib")

    def tearDown(self):
        self.records.close()
        self.temp.cleanup()

    def test_one_real_attempt_and_the_presets_rules(self):
        program, first = self.records.program_start(self.host, SEASON, "astronaut")
        self.assertTrue(first)
        self.assertTrue(self.records.program_real(program, 1, {}))
        self.assertFalse(self.records.program_real(program, 1, {}))  # one shot
        self.assertEqual(self.records.program_end(program, 1, "landed", 1500), "active")
        self.records.program_real(program, 2, {})
        self.assertEqual(self.records.program_end(program, 2, "crashed", 0), "over")
        cadet, first = self.records.program_start(self.host, SEASON, "cadet")
        self.assertFalse(first)
        self.records.program_real(cadet, 1, {})
        self.assertEqual(self.records.program_end(cadet, 1, "crashed", 0), "active")  # Cadet goes on
        last = len(ll.program_missions(SEASON))
        self.records.program_real(cadet, last, {})
        self.assertEqual(self.records.program_end(cadet, last, "landed", 900), "complete")

    def test_a_lost_connection_is_a_lost_mission(self):
        program, _ = self.records.program_start(self.host, SEASON, "test")
        self.records.program_real(program, 1, {"drift": 1})
        self.records.close()
        self.records = ll.Records(self.path)
        self.assertIsNone(self.records.program(self.host))  # Test Pilot: over
        self.assertEqual(self.records.program_steps(program)[1]["result"], "lost")

    def test_a_new_program_closes_the_open_one_and_the_board_keeps_the_best(self):
        first, _ = self.records.program_start(self.host, SEASON, "cadet")
        self.records.program_real(first, 1, {})
        self.records.program_end(first, 1, "landed", 1800)
        second, _ = self.records.program_start(self.host, SEASON, "cadet")
        self.assertEqual(self.records.program(self.host)["id"], second)
        other = ll.Host(node="n", user=9, handle="Ace")
        theirs, _ = self.records.program_start(other, SEASON, "cadet")
        for n in (1, 2):
            self.records.program_real(theirs, n, {})
            self.records.program_end(theirs, n, "landed", 1000)
        board = self.records.program_board(self.host, SEASON, "cadet")
        self.assertEqual(board, [("Ace", 2, 0, 2000, 9), ("Nib", 1, 0, 1800, 7)])
        self.assertEqual(self.records.program_board(self.host, SEASON, "test"), [])


class GameTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.records = ll.Records(Path(self.temp.name) / "pilots.db")
        self.drop = Path(self.temp.name) / "drop"
        self.drop.mkdir()
        self.host = ll.Host(node="n", user=7, handle="Nib", drop=str(self.drop),
                            event_types=("rank", "achievement", "season"))

    def tearDown(self):
        self.records.close()
        self.temp.cleanup()

    def game(self):
        game = ll.Game(self.host, self.records, clock=clock())
        game.announcer = ll.Announcer.for_launch(self.host, self.records)
        game.key("left")  # the PROGRAM tab
        return game

    def events(self):
        return [json.loads(path.read_text()).get("event") for path in sorted(self.drop.glob("*.json"))]

    def real(self, game, vy=-.2):
        game.key("enter")
        self.assertEqual(game.mode, "commit")
        game.key("y")
        game.mode = "flying"
        touch_down(game, vy)
        note = game.record_note  # the debrief's, before [M] returns to the tab
        game.key("m")
        game.key("down")
        return note

    def test_practice_callers_cannot_fly_a_program(self):
        game = ll.Game(clock=clock())
        game.key("left")
        self.assertFalse(game.program_view().ready)
        self.assertFalse(game.key("n"))
        self.assertFalse(game.key("s"))

    def test_simulator_allowances(self):
        game = self.game()
        game.key("n")
        game.key("3")  # Test Pilot: no simulator
        self.assertFalse(game.key("s"))
        game.key("n")
        game.key("2")  # Astronaut: one run
        self.assertTrue(game.key("s"))
        self.assertEqual(game.kind, "sim")
        game.mode = "flying"
        touch_down(game)
        self.assertEqual(game.counters["sim_flights"], 1)
        self.assertFalse(game.key("r"))  # no runs left
        game.key("m")
        self.assertFalse(game.key("s"))

    def test_the_real_flight_scores_the_program_not_the_career(self):
        game = self.game()
        game.key("n")
        game.key("1")
        self.real(game)
        self.assertEqual(game.steps[1]["result"], "landed")
        self.assertGreater(game.program["score"], 0)
        self.assertEqual(game.bests, {})  # never a best, a medal or a promotion
        self.assertEqual(game.counters["landings"], 1)
        self.assertIn("land-1", game.held)
        self.assertEqual(self.events()[0], {"type": "season", "title": "5 missions, through November"})

    def test_completing_a_cadet_program_flawlessly(self):
        game = self.game()
        game.key("n")
        game.key("1")
        for _ in range(len(ll.program_missions(SEASON))):
            self.real(game)
        self.assertEqual(game.program["status"], "complete")
        self.assertTrue({"program-cadet", "flawless"} <= set(game.held))
        titles = [event["title"] for event in self.events() if event["type"] == "achievement"]
        self.assertTrue(any(title.startswith("Program complete: Cadet, 5 of 5") for title in titles))
        self.assertIn("Flawless", titles)
        self.assertNotIn("Graduate", titles)  # the program is announced whole instead

    def test_a_crash_ends_an_astronaut_program(self):
        game = self.game()
        game.key("n")
        game.key("2")
        note = self.real(game, vy=-20)
        self.assertEqual(game.program["status"], "over")
        self.assertIn("PROGRAM OVER", note)
        self.assertFalse(game.key("enter"))

    def test_leaving_mid_flight_loses_the_mission(self):
        game = self.game()
        game.key("n")
        game.key("1")
        game.key("enter")
        game.key("y")
        game.mode = "flying"
        game.key("q")
        game.key("y")
        self.assertTrue(game.leaving)
        self.assertEqual(self.records.program_steps(game.program["id"])[1]["result"], "lost")


class DisplayTests(unittest.TestCase):
    def text(self, game, mode=None, kind=None):
        deck = ll.Deck(game.chapter, game.bests, True, game.award, tuple(game.unlocked), game.logbook(),
                       game.kind if kind is None else kind, game.program_view())
        canvas = ll.Display(ll.Host(80, 24)).draw(game.flight, mode or game.mode, mission=game.mission,
                                                  catalog=game.missions, record_note=game.record_note, deck=deck)
        return "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)

    def test_the_tab_cards_and_header(self):
        with tempfile.TemporaryDirectory() as directory:
            records = ll.Records(Path(directory) / "pilots.db")
            game = ll.Game(ll.Host(node="n", user=7, handle="Nib"), records, clock=clock())
            game.key("left")
            self.assertIn("[N] Start a program", self.text(game))
            game.key("n")
            text = self.text(game)
            for words in ("NEW PROGRAM", "CADET", "ASTRONAUT", "TEST PILOT"):
                self.assertIn(words, text)
            game.key("2")
            text = self.text(game)
            self.assertIn("NEXT", text)
            self.assertIn("SIMULATOR 1 run left", text)
            game.key("enter")
            self.assertIn("This is the real flight", self.text(game))
            game.key("y")
            self.assertIn("LIVE MISSION 1", self.text(game, "flying"))
            game.mode = "flying"
            touch_down(game, -20)
            text = self.text(game, "debrief")
            self.assertIn("PROGRAM OVER", text)
            self.assertNotIn("[R]", text)
            game.key("m")
            text = self.text(game, "menu")
            self.assertIn("LOST", text)
            self.assertIn("PROGRAM OVER", text)
            game.key("b")
            self.assertIn("PROGRAM BOARD / ASTRONAUT", self.text(game))
            records.close()


if __name__ == "__main__":
    unittest.main()
