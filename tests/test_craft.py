from pathlib import Path
import tempfile
import unittest

import lunar_lander as ll
from test_career import touch_down
from test_records import land


def screen(canvas):
    return "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)


class FlightTests(unittest.TestCase):
    def test_each_craft_flies_differently(self):
        mission = ll.missions()[1]
        flights = {craft: ll.in_craft(mission, craft).launch() for craft in ll.CRAFT}
        self.assertEqual((flights["lm"].dry_mass, flights["lm"].thrust), (ll.DRY_MASS, ll.MAX_THRUST))
        self.assertLess(flights["surveyor"].fuel, flights["lm"].fuel)
        self.assertGreater(flights["altair"].fuel, flights["lm"].fuel)
        for craft, step in (("lm", 10), ("surveyor", 15), ("altair", 5)):
            flights[craft].command("d")
            self.assertEqual(flights[craft].angle, step)

    def test_the_altairs_engine_lags_the_throttle(self):
        flight = ll.in_craft(ll.missions()[1], "altair").launch()
        flight.command("9")
        flight.step()
        self.assertLess(flight.engine, .2)
        for _ in range(120):
            flight.step()
        self.assertGreater(flight.engine, .95)
        instant = ll.missions()[1].launch()
        instant.command("9")
        instant.step()
        self.assertEqual(instant.engine, 1.0)

    def test_a_steady_pilot_lands_every_mission_in_every_craft(self):
        for craft in ll.CRAFT:
            for mission in (*ll.missions("2026-10-31")[1:], ll.daily_missions("2026-11-01")[2]):
                with self.subTest(craft=craft, mission=mission.key):
                    flight = land(ll.in_craft(mission, craft))
                    self.assertEqual(flight.status, "landed", flight.reason)
                    if not flight.cooling:  # the Hopper's margin is heat, not a tank
                        self.assertGreater(flight.fuel, 5)

    def test_hover_time_is_the_crafts(self):
        lm, altair = ll.missions()[1].launch(), ll.in_craft(ll.missions()[1], "altair").launch()
        altair.fuel = lm.fuel = 20
        self.assertLess(ll.hover_seconds(altair.fuel, altair.gravity, altair.dry_mass, altair.thrust),
                        ll.hover_seconds(lm.fuel, lm.gravity, lm.dry_mass, lm.thrust))

    def test_keys_names_and_ghosts(self):
        mission = ll.in_craft(ll.missions()[1], "surveyor")
        self.assertEqual(mission.key, "tranquility@surveyor")
        self.assertEqual(ll.variant_key("tranquility", "surveyor", True), ll.on_instruments(mission).key)
        self.assertEqual(ll.mission_title(ll.on_instruments(mission)), "Tranquility in the Surveyor on instruments")
        self.assertEqual(ll.base_name(mission), "Tranquility Base")
        self.assertEqual(ll.in_craft(mission, "altair"), mission)  # one craft per flight
        flight = land(mission)
        self.assertTrue(ll.Ghost(mission, ll.ghost_data(flight), "x").faithful())


class GameTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.records = ll.Records(Path(self.temp.name) / "pilots.db")
        self.host = ll.Host(node="n", user=7, handle="Nib")

    def tearDown(self):
        self.records.close()
        self.temp.cleanup()

    def game(self, level_points=0):
        game = ll.Game(self.host, self.records)
        game.scenes = False
        # Enough golds for a rank: the first missions of the catalogue.
        golds = [m for m in ll.tour_missions(game.missions)][:level_points // 3]
        game.bests.update({m.key: 1750 * m.difficulty for m in golds})
        game.key("2")
        return game

    def test_the_fleet_opens_with_rank(self):
        self.assertEqual(self.game().fleet(), ["lm"])
        self.assertFalse(self.game().key("v"))
        self.assertEqual(self.game(24).fleet(), ["lm", "surveyor"])
        self.assertEqual(self.game(45).fleet(), ["lm", "surveyor", "altair"])

    def test_flying_the_surveyor_keeps_its_own_best_and_earns_its_gold(self):
        game = self.game(24)
        game.key("v")
        deck = ll.Deck(game.chapter, game.bests, True, None, (), game.logbook(), craft=game.craft,
                       fleet=tuple(game.fleet()))
        text = screen(ll.Display(ll.Host(80, 24)).draw(game.flight, "menu", mission=game.mission,
                                                       catalog=game.missions, deck=deck))
        self.assertIn("[V] SURVEYOR", text)
        self.assertIn("[I] IFR", text)
        before = game.bests["tranquility"]
        game.key("enter")
        self.assertEqual(game.mission.key, "tranquility@surveyor")
        self.assertIn("FLIGHT TRANQUILITY SURVEYOR",
                      screen(ll.Display(ll.Host(80, 24)).draw(game.flight, mission=game.mission)))
        game.mode = "flying"
        touch_down(game, fuel=60)
        self.assertEqual(game.bests["tranquility"], before)
        self.assertIn("tranquility@surveyor", game.bests)
        self.assertIn("craft-surveyor", game.held)

    def test_a_grand_tour_is_flown_in_the_lm(self):
        game = self.game(24)
        game.key("v")
        game.key("t")
        game.key("enter")
        self.assertEqual((game.mission.key, game.craft), ("tranquility", "lm"))


if __name__ == "__main__":
    unittest.main()
