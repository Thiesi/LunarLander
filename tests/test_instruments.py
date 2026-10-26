from pathlib import Path
import tempfile
import unittest

import lunar_lander as ll
from test_career import touch_down


def screen(canvas):
    return "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)


class InstrumentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.records = ll.Records(Path(self.temp.name) / "pilots.db")
        self.host = ll.Host(node="n", user=7, handle="Nib")
        self.game = ll.Game(self.host, self.records)
        self.game.scenes = False
        self.game.key("2")  # Tranquility

    def tearDown(self):
        self.records.close()
        self.temp.cleanup()

    def fly(self, **kwargs):
        self.game.key("enter")
        self.game.mode = "flying"
        touch_down(self.game, **kwargs)

    def test_the_switch_flies_the_same_flight_under_its_own_key(self):
        visual = self.game.mission.launch()
        self.assertTrue(self.game.key("i"))
        self.game.key("enter")
        self.assertEqual(self.game.mission.key, "tranquility@ifr")
        flight = self.game.flight  # the same ground and the same start
        self.assertEqual(flight.terrain.points, visual.terrain.points)
        self.assertEqual((flight.x, flight.y, flight.vx, flight.vy, flight.fuel),
                         (visual.x, visual.y, visual.vx, visual.vy, visual.fuel))
        self.assertIsNone(self.game.ghost)

    def test_its_own_best_never_touches_the_visual_one_or_the_rank(self):
        self.game.key("i")
        self.fly()
        self.assertIn("tranquility@ifr", self.game.bests)
        self.assertNotIn("tranquility", self.game.bests)
        self.assertEqual(self.game.career().points, 0)
        self.assertTrue({"ifr", "ifr-gold"} <= set(self.game.held))
        self.game.key("m")  # back to the visual mission in the briefing
        self.assertEqual(self.game.mission.key, "tranquility")
        self.game.key("i")
        self.fly()
        self.assertIn("tranquility", self.game.bests)

    def test_retry_stays_on_instruments(self):
        self.game.key("i")
        self.fly(vy=-20)
        self.game.key("r")
        self.assertEqual(self.game.mission.key, "tranquility@ifr")

    def test_the_view_is_dark_and_the_panel_reads_the_flight(self):
        self.game.key("i")
        self.game.key("enter")
        for host in (ll.Host(80, 24), ll.Host(132, 50), ll.Host(80, 24, "16", False),
                     ll.Host(80, 24, "256", True, charset="cp437")):
            display = ll.Display(host)
            canvas = display.draw(self.game.flight, "flying", mission=self.game.mission)
            text = screen(canvas)
            for words in ("INSTRUMENT APPROACH", "RADAR ALT", "DRIFT / SINK", "FLIGHT TRANQUILITY IFR"):
                self.assertIn(words, text)
            top, bottom = 3, host.height - 7
            view = {cell[0] for row in canvas.cells[top:bottom] for cell in row}
            self.assertFalse(view & set(ll.QUADRANTS[1:]) - {"▀", "▄"} if host.unicode else set())
            display.encode(canvas)

    def test_the_briefing_shows_the_switch_and_the_ifr_best(self):
        self.game.key("i")
        self.fly()
        self.game.key("m")
        deck = ll.Deck(self.game.chapter, self.game.bests, True, None, (), self.game.logbook(), ifr=True)
        text = screen(ll.Display(ll.Host(80, 24)).draw(self.game.flight, "menu", mission=self.game.mission,
                                                       catalog=self.game.missions, deck=deck))
        self.assertIn("[I] IFR", text)
        self.assertIn(f"BEST {self.game.bests['tranquility@ifr']} pts", text)

    def test_a_grand_tour_flies_with_the_window_open(self):
        self.game.key("i")
        self.game.key("t")
        self.game.key("enter")
        self.assertEqual(self.game.mission.key, "tranquility")
        self.game.mode = "flying"
        touch_down(self.game)
        self.assertEqual(self.game.tour["landed"], 1)

    def test_prose_names_it(self):
        mission = ll.on_instruments(ll.missions()[1])
        self.assertEqual(ll.mission_title(mission), "Tranquility on instruments")
        self.assertEqual(ll.on_instruments(mission), mission)
        flight = mission.launch()
        flight.status = "landed"
        award = ll.Award(mission, 9999, "GOLD", "GOLD", True, None, None)
        self.assertIn("Tranquility Base", ll.debrief_call(flight, mission, award))


if __name__ == "__main__":
    unittest.main()
