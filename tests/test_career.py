import json
from pathlib import Path
import tempfile
import unittest

import lunar_lander as ll


def touch_down(game, vy=-.2, fuel=None):
    """Settle the current flight onto the middle of its pad at `vy`."""
    flight = game.flight
    flight.throttle, flight.vx, flight.vy, flight.angle = 0, 0, vy, 0
    if fuel is not None:
        flight.fuel = fuel
    flight.x = (flight.terrain.pad.left + flight.terrain.pad.right) / 2
    flight.y = flight.terrain.pad.height + 3.01
    game.tick(.1, True)
    return game


def fly(game, key, vy=-.2, fuel=None):
    """Choose a mission from the menu, launch it and touch down."""
    game.mode = "menu"
    game.key(key)
    game.key("enter")
    game.mode = "flying"
    return touch_down(game, vy, fuel)


class MedalTests(unittest.TestCase):
    def test_thresholds_scale_with_difficulty(self):
        needle = next(m for m in ll.missions() if m.key == "needle")
        for score, expected in ((1750 * 3, "GOLD"), (1750 * 3 - 1, "SILVER"), (1400 * 3, "SILVER"),
                                (1400 * 3 - 1, "BRONZE"), (1000 * 3, "BRONZE"), (0, None)):
            self.assertEqual(ll.medal(needle, score), expected, score)
        self.assertIsNone(ll.medal(ll.missions()[0], 5000))

    def test_ranks_count_only_ranked_chapters(self):
        catalog = ll.missions("2026-10-24")
        ranked = [m for c in ll.CHAPTERS if c.ranked for m in ll.chapter_missions(c, catalog) if m.difficulty]
        self.assertEqual(len(ranked), 15)
        everything = ll.career({m.key: 2000 * m.difficulty for m in ranked}, catalog)
        self.assertEqual((everything.points, everything.rank, everything.next_rank), (45, "LUNAR ACE", None))
        one_short = {m.key: 2000 * m.difficulty for m in ranked[1:]}
        self.assertEqual(ll.career(one_short, catalog).rank, "MISSION COMMANDER")
        daily = next(m for m in catalog if m.key.startswith("daily-"))
        self.assertEqual(ll.career({daily.key: 9999}, catalog).points, 0)

    def test_every_mission_has_one_chapter(self):
        keys = [key for chapter in ll.CHAPTERS for key in chapter.missions]
        self.assertEqual(len(keys), len(set(keys)))
        catalog = {m.key for m in ll.missions("2026-10-24")}
        dailies = {"daily-2026-10-24-maria", "daily-2026-10-24-highlands", "daily-2026-10-24-frontier"}
        self.assertEqual(catalog, {k for k in keys if not k.startswith("daily-")} | dailies)

    def test_original_keys_and_places_are_kept(self):
        self.assertEqual([m.key for m in ll.missions("2026-10-24")[:9]],
                         ["training", "tranquility", "ridgetop", "needle", "daily-2026-10-24-maria",
                          "copernicus", "hadley", "farside", "polar"])


class MenuTests(unittest.TestCase):
    def test_cursor_and_chapter_navigation(self):
        game = ll.Game()
        self.assertEqual(game.mission.key, "training")
        for key, expected in (("down", "tranquility"), ("s", "serenitatis"), ("up", "tranquility"),
                              ("w", "training"), ("up", "crisium"), ("right", "ridgetop"), ("d", "farside"),
                              ("3", "tsiolkovsky"), ("a", "ridgetop"), ("left", "crisium"),
                              ("left", game.missions[4].key), ("right", "crisium")):
            self.assertTrue(game.key(key), key)
            self.assertEqual(game.mission.key, expected, key)
        self.assertFalse(game.key("9"))  # no ninth mission on this tab
        game.key("2")
        game.key("enter")
        self.assertEqual((game.mode, game.flight.terrain.pad.name), ("flying", "TRANQUILITY"))

    def test_menu_shows_rank_and_medals(self):
        bests = {"tranquility": 1800, "serenitatis": 1450}
        canvas = ll.Display(ll.Host()).draw(ll.training(), "menu", deck=ll.Deck(0, bests, True))
        text = " ".join("".join(c[0] for c in row) for row in canvas.cells)
        self.assertIn("RANK PILOT", text)
        self.assertIn("2/15 landed", text)
        self.assertNotIn("session only", text)


class AwardTests(unittest.TestCase):
    def test_first_soft_landing_is_gold_and_promotes(self):
        game = fly(ll.Game(scenes=True), "2")
        award = game.award
        self.assertEqual((award.medal, award.improved, award.promoted), ("GOLD", True, "PILOT"))
        self.assertEqual(game.queue, ["medal", "promotion"])

    def test_worse_landing_keeps_the_better_medal(self):
        game = fly(ll.Game(scenes=True), "2")
        fly(game, "2", vy=-2.9, fuel=5)
        award = game.award
        self.assertEqual((award.medal, award.best, award.improved, award.promoted), ("BRONZE", "GOLD", False, None))
        self.assertEqual(game.queue, ["medal"])

    def test_training_and_crashes_earn_nothing(self):
        self.assertIsNone(fly(ll.Game(scenes=True), "1").award)
        crash = fly(ll.Game(scenes=True), "2", vy=-9)
        self.assertEqual((crash.flight.status, crash.award, crash.queue), ("crashed", None, []))

    def test_without_scenes_the_debrief_carries_the_award(self):
        game = fly(ll.Game(scenes=False), "2")
        self.assertEqual((game.mode, game.queue), ("debrief", []))
        canvas = ll.Display(ll.Host()).draw(game.flight, "debrief", mission=game.mission,
                                            deck=ll.Deck(0, game.bests, False, game.award))
        text = " ".join("".join(c[0] for c in row) for row in canvas.cells)
        self.assertIn("GOLD MEDAL", text)
        self.assertIn("PROMOTED TO PILOT", text)


class AnnouncerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        (self.root / "outbound").mkdir()
        self.info = self.root / "door.json"

    def tearDown(self):
        self.directory.cleanup()

    def host(self, events=True, user=7, types=None):
        data = {"door_api": 5, "node_id": "node", "handle": "Pilot"}
        if user is not None:
            data["user_id"] = user
        if events:
            data["outbound"] = {"directory": "outbound",
                                "events": {"types": types or ["rank", "achievement"], "title_max": 60}}
        self.info.write_text(json.dumps(data), encoding="utf-8")
        return ll.Host.load(str(self.info))

    def requests(self):
        return [json.loads(path.read_text(encoding="utf-8"))
                for path in sorted((self.root / "outbound").glob("*.json"))]

    def test_metadata(self):
        host = self.host()
        self.assertEqual((Path(host.drop), host.event_types, host.title_max),
                         (self.root / "outbound", ("rank", "achievement"), 60))
        self.assertIsNone(self.host(events=False).drop)

    def test_live_gold_and_promotion_are_announced_after_the_save(self):
        host = self.host()
        records = ll.Records(self.root / "pilots.db")
        try:
            game = ll.Game(host, records, scenes=True)
            game.announcer = ll.Announcer.for_launch(host, records)
            fly(game, "2")
            sent = self.requests()
            self.assertIn({"event": {"type": "rank", "user_id": 7, "title": "Pilot"}}, sent)
            self.assertIn({"event": {"type": "achievement", "user_id": 7, "title": "Gold landing: Tranquility"}}, sent)
            self.assertEqual([r for r in sent if "standings" in r][-1],
                             {"standings": {"title": "Career Roster",
                                            "rows": [{"user_id": 7, "value": "3 medal pts", "label": "Pilot"}]}})
            self.assertEqual(list((self.root / "outbound").glob("*.part")), [])
            # The same gold again is not news, and the standings did not move.
            fly(game, "2")
            self.assertEqual(len(self.requests()), len(sent))
        finally:
            records.close()

    def test_types_the_sysop_left_out_are_not_sent(self):
        host = self.host(types=["achievement"])
        records = ll.Records(self.root / "pilots.db")
        try:
            ll.Announcer.for_launch(host, records).event("rank", "Pilot")
            self.assertEqual(self.requests(), [])
        finally:
            records.close()

    def test_guests_and_practice_announce_nothing(self):
        self.assertIsNone(ll.Announcer.for_launch(self.host(user=None), None))
        self.assertIsNone(ll.Announcer.for_launch(self.host(), None))
        self.assertIsNone(ll.Announcer.for_launch(self.host(events=False), None))


if __name__ == "__main__":
    unittest.main()
