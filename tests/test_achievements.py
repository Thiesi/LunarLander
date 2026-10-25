from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import lunar_lander as ll
from test_career import fly


def touch(mission=None, x=None, vy=-.2, vx=0.0, angle=0.0, fuel=None, height=3.01):
    """A finished flight: the mission's craft let down at `vy` onto `x` (the pad's centre)."""
    mission = mission or ll.missions()[1]
    flight = mission.launch()
    pad = flight.terrain.pad
    flight.throttle, flight.vx, flight.vy, flight.angle = 0, vx, vy, angle
    if fuel is not None:
        flight.fuel = fuel
    flight.x = (pad.left + pad.right) / 2 if x is None else x
    flight.y = flight.terrain.height(flight.x) + height
    while flight.status == "flying":
        flight.step()
    return mission, flight


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "pilots.db"

    def tearDown(self):
        self.temp.cleanup()

    def tables(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            return ({row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")},
                    db.execute("PRAGMA user_version").fetchone()[0])

    def test_a_new_file_is_schema_2(self):
        ll.Records(self.path).close()
        self.assertEqual(self.tables(), (set(ll.SCHEMA), 2))

    def test_schema_1_upgrades_in_place_and_keeps_every_record(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute(ll.SCHEMA["pilots"])
            db.execute(ll.SCHEMA["scores"])
            db.execute(f"PRAGMA application_id={ll.Records.APP_ID}")
            db.execute("PRAGMA user_version=1")
            db.execute("INSERT INTO pilots VALUES ('n', 7, 'Nib')")
            db.execute("INSERT INTO scores VALUES ('n', 7, 'tranquility', 1800, 1)")
        records = ll.Records(self.path)
        host = ll.Host(node="n", user=7)
        self.assertEqual(records.bests(host), {"tranquility": 1800})
        records.close()
        self.assertEqual(self.tables(), (set(ll.SCHEMA), 2))

    def test_anything_else_is_refused_and_preserved(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            for table in ("pilots", "scores", "counters"):
                db.execute(ll.SCHEMA[table])
            db.execute(f"PRAGMA application_id={ll.Records.APP_ID}")
            db.execute("PRAGMA user_version=2")
        with self.assertRaises(ll.DoorError):
            ll.Records(self.path)
        self.assertEqual(self.tables()[1], 2)


class FlightFeatTests(unittest.TestCase):
    def feats(self, **kwargs):
        mission, flight = touch(**kwargs)
        return flight.status, ll.flight_feats(mission, flight)

    def test_precision(self):
        status, got = self.feats(vy=-.1)
        self.assertEqual(status, "landed")
        self.assertTrue({"feather", "no-drift", "dead-centre", "perfect", "fuel-miser"} <= got)
        status, got = self.feats(vy=-.6, vx=.5)
        self.assertFalse(got & {"feather", "no-drift", "perfect"})

    def test_close_calls(self):
        self.assertIn("by-the-book", self.feats(vy=-2.95)[1])
        self.assertIn("shuffle", self.feats(vx=1.95)[1])
        self.assertIn("leaning-in", self.feats(angle=10)[1])
        self.assertIn("fumes", self.feats(fuel=.5)[1])
        pad = ll.missions()[1].launch().terrain.pad
        self.assertIn("edge", self.feats(x=pad.left + 3.3)[1])
        status, got = self.feats(vy=-2.6, vx=1.6, angle=10)
        self.assertEqual(status, "landed")
        self.assertIn("every-limit", got)

    def test_spectacular_crashes(self):
        self.assertTrue({"lithobraking", "full-tank"} <= self.feats(vy=-40)[1])
        self.assertTrue({"lithobraking", "meteorite"} <= self.feats(vy=-70)[1])
        self.assertIn("dead-stick", self.feats(vy=-5, fuel=0)[1])
        status, got = self.feats(vy=-3.2)
        self.assertEqual(status, "crashed")
        self.assertIn("so-close", got)
        self.assertNotIn("so-close", self.feats(vy=-3.6)[1])
        self.assertIn("tipping-point", self.feats(vy=-2, angle=60)[1])
        self.assertIn("wrong-crater", self.feats(x=900, vy=-5)[1])
        mission = ll.missions()[1]
        flight = mission.launch()
        flight.x, flight.vx = 4, -30
        while flight.status == "flying":
            flight.step()
        self.assertEqual(ll.flight_feats(mission, flight), {"off-the-map"})

    def test_training_and_unfinished_flights_earn_nothing(self):
        self.assertEqual(ll.flight_feats(*touch(ll.missions()[0], vy=-.1)), set())
        mission = ll.missions()[1]
        self.assertEqual(ll.flight_feats(mission, mission.launch()), set())


class CountedAndCareerTests(unittest.TestCase):
    def test_flight_log(self):
        mission, flight = touch(vy=-.4)
        added, lowest, highest = ll.flight_log(mission, flight, "landed")
        self.assertEqual(added["landings"], 1)
        self.assertEqual(lowest["softest"], abs(flight.vy))
        self.assertEqual(ll.flight_log(mission, flight, "aborted")[0].keys(), {"aborts", "flight_seconds"})
        training, flight = touch(ll.missions()[0])
        self.assertEqual(ll.flight_log(training, flight, "landed")[0].keys(), {"sim_flights", "sim_seconds"})
        counters = ll.apply_log({"softest": .2}, {"landings": 1}, {"softest": .4}, {"most_fuel": 50})
        self.assertEqual(counters, {"softest": .2, "landings": 1, "most_fuel": 50})

    def test_milestones(self):
        self.assertEqual(ll.counter_feats({"landings": 10, "crashes": 9, "flight_seconds": 3600}),
                         {"land-1", "land-10", "air-1h"})

    def test_career_from_bests(self):
        catalog = ll.missions("2026-10-25")
        maria = [m for m in ll.chapter_missions(ll.CHAPTERS[0], catalog) if m.difficulty]
        landed = {m.key: 1000 * m.difficulty for m in maria}
        self.assertEqual(ll.career_feats(landed, catalog), {"maria-landed"})
        gold = {m.key: 1800 * m.difficulty for m in maria}
        self.assertEqual(ll.career_feats(gold, catalog), {"maria-landed", "maria-gold", "first-gold"})
        everything = {m.key: 1800 * m.difficulty for c in ll.CHAPTERS if c.ranked
                      for m in ll.chapter_missions(c, catalog) if m.difficulty}
        self.assertIn("ace", ll.career_feats(everything, catalog))

    def test_dailies_hat_trick_streaks_and_old_keys(self):
        catalog = ll.missions("2026-10-25")
        day = ll.daily_missions("2026-10-20")
        bests = {m.key: 1000 for m in day}
        self.assertIn("hat-trick", ll.career_feats(bests, catalog))
        # A streak may run through the single daily of releases before v0.4.0.
        streak = {"daily-2026-10-01": 2000, "daily-2026-10-02-maria": 900, "daily-2026-10-03-frontier": 4000}
        self.assertIn("streak-3", ll.career_feats(streak, catalog))
        broken = {key: score for key, score in streak.items() if "-02" not in key}
        self.assertNotIn("streak-3", ll.career_feats(broken, catalog))
        frontier = day[2]
        self.assertIn("daily-gold", ll.career_feats({frontier.key: 1800 * frontier.difficulty}, catalog))


class GameTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.records = ll.Records(Path(self.temp.name) / "pilots.db")
        self.drop = Path(self.temp.name) / "drop"
        self.drop.mkdir()
        self.host = ll.Host(node="n", user=7, handle="Nib", drop=str(self.drop))

    def tearDown(self):
        self.records.close()
        self.temp.cleanup()

    def game(self):
        game = ll.Game(self.host, self.records, clock=ll.DailyClock("UTC", "%Y-%m-%d"))
        game.announcer = ll.Announcer.for_launch(self.host, self.records)
        return game

    def events(self):
        return [json.loads(path.read_text())["event"]["title"] for path in sorted(self.drop.glob("*.json"))
                if "event" in json.loads(path.read_text())]

    def test_a_landing_counts_awards_and_announces_silver_and_gold_only(self):
        game = fly(self.game(), "2", vy=-.1)
        self.assertEqual(game.counters["landings"], 1)
        self.assertTrue({"land-1", "feather", "perfect"} <= set(game.unlocked))
        self.assertEqual(self.records.held(self.host).keys(), game.held.keys())
        titles = self.events()
        self.assertIn("Textbook", titles)
        self.assertIn("Feather", titles)
        self.assertNotIn("First Contact", titles)  # bronze stays quiet
        # Earned once only.
        fly(game, "2", vy=-.1)
        self.assertNotIn("feather", game.unlocked)

    def test_the_debrief_names_them(self):
        game = fly(self.game(), "2", vy=-.1)
        game.mode = "debrief"
        deck = ll.Deck(game.chapter, game.bests, True, game.award, tuple(game.unlocked), game.logbook())
        canvas = ll.Display(ll.Host(node="n", user=7)).draw(game.flight, "debrief", mission=game.mission, deck=deck)
        text = "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)
        self.assertIn("ACHIEVEMENT: First Contact (bronze)", text)
        self.assertIn("more", text)

    def test_old_bests_earn_quietly_at_launch(self):
        catalog = ll.missions()
        maria = [m for m in ll.chapter_missions(ll.CHAPTERS[0], catalog) if m.difficulty]
        for mission in maria:
            flight = touch(mission, vy=-.1)[1]
            self.records.save(self.host, mission, flight)
        game = self.game()
        self.assertTrue({"maria-landed", "first-gold"} <= set(game.held))
        self.assertEqual(self.events(), [])

    def test_crashes_aborts_and_training_count(self):
        game = self.game()
        game.mode = "menu"
        game.key("2")
        game.key("enter")
        game.mode = "flying"
        game.flight.vy = -45
        while game.mode == "flying":
            game.tick(.1, True)
        self.assertEqual(game.counters["crashes"], 1)
        self.assertIn("lithobraking", game.held)
        game.mode = "menu"
        game.key("enter")
        game.mode = "flying"
        game.key("q")
        game.key("y")
        self.assertEqual(game.counters["aborts"], 1)
        game = self.game()
        fly(game, "1")
        self.assertEqual((game.counters["sim_flights"], game.counters.get("landings", 0)), (1, 0))

    def test_practice_callers_keep_a_session(self):
        game = ll.Game(clock=ll.DailyClock("UTC", "%Y-%m-%d"))
        fly(game, "2", vy=-.1)
        self.assertIn("feather", game.held)
        self.assertEqual(game.counters["landings"], 1)


class PilotRecordTests(unittest.TestCase):
    def rows(self, canvas):
        return "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)

    def test_keys_and_tabs(self):
        game = ll.Game(clock=ll.DailyClock("UTC", "%Y-%m-%d"))
        game.key("p")
        self.assertEqual((game.mode, game.record_tab), ("record", 0))
        game.key("down")
        self.assertEqual(game.record_scroll, 0)  # the career tab does not scroll
        game.key("right")
        for _ in range(100):
            game.key("down")
        self.assertEqual(game.record_scroll, len(ll.RECORD_ROWS) - ll.record_rows(game.host.height))
        game.key("left")
        self.assertEqual((game.record_tab, game.record_scroll), (0, 0))
        game.key("escape")
        self.assertEqual(game.mode, "menu")

    def test_both_tabs_at_both_sizes(self):
        game = ll.Game(clock=ll.DailyClock("UTC", "%Y-%m-%d"))
        fly(game, "2", vy=-40)  # a crash: Lithobraking and Full Tank
        for size in ((80, 24), (132, 50)):
            for tab, words in ((0, ("PILOT RECORD", "this session only", "RANK", "MARIA", "FLIGHTS",
                                    "SOFTEST", "hidden to find")),
                               (1, ("MILESTONES", "First Contact", "Land safely once", "Scroll"))):
                with self.subTest(size=size, tab=tab):
                    game.record_tab, game.record_scroll = tab, 0
                    deck = ll.Deck(game.chapter, game.bests, False, None, (), game.logbook())
                    canvas = ll.Display(ll.Host(*size)).draw(game.flight, "record", deck=deck)
                    text = self.rows(canvas)
                    for word in words:
                        self.assertIn(word, text)
        # Hidden ones read "???" until earned; earned ones by name.
        game.record_tab = 1
        game.record_scroll = next(n for n, row in enumerate(ll.RECORD_ROWS)
                                  if getattr(row, "key", None) == "every-limit")
        deck = ll.Deck(game.chapter, game.bests, False, None, (), game.logbook())
        text = self.rows(ll.Display(ll.Host(132, 50)).draw(game.flight, "record", deck=deck))
        self.assertIn("Lithobraking", text)
        self.assertIn("???", text)


if __name__ == "__main__":
    unittest.main()
