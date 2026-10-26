from pathlib import Path
import tempfile
import unittest

import lunar_lander as ll
from test_career import touch_down


def screen(canvas):
    return "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)


class TourTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "pilots.db"
        self.records = ll.Records(self.path)
        self.host = ll.Host(node="n", user=7, handle="Nib")
        self.game = self.new_game()

    def tearDown(self):
        self.records.close()
        self.temp.cleanup()

    def new_game(self, host=None):
        game = ll.Game(host or self.host, self.records)
        game.scenes = False
        return game

    def fly(self, game, vy=-.2, fuel=None):
        game.mode = "flying"
        touch_down(game, vy, fuel)

    def text(self, game, mode=None, height=24):
        deck = ll.Deck(game.chapter, game.bests, game.records is not None and game.host.ranked, game.award, tuple(game.unlocked), game.logbook(),
                       tour=game.tour_view())
        return screen(ll.Display(ll.Host(80, height)).draw(game.flight, mode or game.mode, mission=game.mission,
                                                           catalog=game.missions, record_note=game.record_note,
                                                           deck=deck))

    def test_fifteen_missions_in_chapter_order(self):
        tour = ll.tour_missions(ll.missions())
        self.assertEqual(len(tour), 15)
        self.assertEqual((tour[0].key, tour[-1].key), ("tranquility", "aitken"))
        self.assertFalse(any(m.key.startswith(("daily", "training")) for m in tour))

    def test_starting_flies_the_first_and_a_landing_moves_on(self):
        game = self.game
        self.assertIn("[T] Grand Tour", self.text(game, "menu"))
        game.key("t")
        self.assertIn("[ENTER] Start a tour", self.text(game))
        game.key("enter")
        self.assertEqual((game.mode, game.mission.key), ("flying", "tranquility"))
        self.fly(game)
        self.assertEqual(game.tour["landed"], 1)
        self.assertIn("[ENTER] Tour 2/15: MARE SERENITATIS", self.text(game, "debrief"))
        self.assertGreater(game.bests["tranquility"], 0)  # a tour flight is a ranked flight
        game.key("enter")
        self.assertEqual(game.mission.key, "serenitatis")

    def test_a_crash_is_a_retry_of_the_same_mission(self):
        game = self.game
        game.key("t")
        game.key("enter")
        self.fly(game, vy=-20)
        self.assertEqual((game.tour["landed"], game.tour["retries"]), (0, 1))
        self.assertNotIn("[ENTER] Tour", self.text(game, "debrief"))
        game.key("r")
        self.assertEqual(game.mission.key, "tranquility")
        self.fly(game)
        self.assertEqual(game.tour["landed"], 1)

    def test_other_flights_do_not_count(self):
        game = self.game
        game.key("t")
        game.key("enter")
        game.mode = "menu"
        game.key("down")  # Serenitatis, out of turn
        game.key("enter")
        self.fly(game)
        self.assertEqual(game.tour["landed"], 0)

    def test_a_complete_tour_earns_its_achievements_and_its_board(self):
        game = self.game
        game.key("t")
        game.key("enter")
        for _ in range(15):
            self.fly(game, fuel=90)  # every one gold
            if game.tour["status"] == "complete":
                break
            game.key("enter")
        self.assertEqual(game.tour["status"], "complete")
        self.assertTrue({"grand-tour", "grand-slam"} <= set(game.held))
        self.assertIn("GRAND TOUR COMPLETE", game.record_note)
        game.mode = "menu"
        game.key("t")
        game.key("b")
        text = self.text(game)
        self.assertIn("GRAND TOUR BOARD", text)
        self.assertIn("Nib", text)

    def test_leaving_ends_the_tour_unfinished(self):
        game = self.game
        game.key("t")
        game.key("enter")
        self.fly(game)
        tour = game.tour["id"]
        later = self.new_game()
        self.assertEqual(self.records.tour(self.host, tour)["status"], "unfinished")
        self.assertIsNone(later.tour)
        self.assertIsNone(self.records.tour(self.host))

    def test_practice_callers_have_no_tour(self):
        game = ll.Game()
        self.assertFalse(game.key("t"))
        self.assertNotIn("[T] Grand Tour", self.text(game, "menu"))

    def test_the_card_fits_80x24(self):
        game = self.game
        game.key("t")
        game.key("enter")
        self.fly(game)
        game.key("m")
        game.key("t")
        text = self.text(game)
        self.assertIn("Under way: 1 of 15 landed", text)
        self.assertIn("[ENTER] Continue: MARE SERENITATIS", text)


if __name__ == "__main__":
    unittest.main()
