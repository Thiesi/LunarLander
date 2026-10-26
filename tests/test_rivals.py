from pathlib import Path
import tempfile
import unittest

import lunar_lander as ll
from test_records import land


def screen(canvas):
    return "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)


class RivalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "pilots.db"
        self.records = ll.Records(self.path)
        self.nib = ll.Host(node="n", user=7, handle="Nib")
        self.ace = ll.Host(node="n", user=9, handle="Ace")
        self.mission = ll.missions()[1]  # Tranquility

    def tearDown(self):
        self.records.close()
        self.temp.cleanup()

    def score(self, host, points, mission=None):
        """Store a landing worth `points`, as a real flight's ghost would be."""
        mission = mission or self.mission
        flight = land(mission)
        self.records.save(host, mission, flight)
        self.records.db.execute("UPDATE scores SET score=? WHERE node=? AND user=? AND mission=?",
                                (points, host.node, host.user, mission.key))

    def visit(self, host):
        game = ll.Game(host, self.records)
        game.key("2")
        return game

    def test_passed_since_your_last_visit(self):
        self.score(self.nib, 1700)
        self.assertEqual(self.visit(self.nib).rivals, {})  # first visit: nothing to compare
        self.score(self.ace, 1740)
        game = self.visit(self.nib)
        self.assertEqual(game.live_rivals(), {"tranquility": ("Ace", 40)})
        self.assertEqual(self.visit(self.nib).rivals, {})  # seen: not again

    def test_passing_them_back_clears_it(self):
        self.score(self.nib, 1700)
        self.visit(self.nib)
        self.score(self.ace, 1740)
        game = self.visit(self.nib)
        game.bests["tranquility"] = 1750
        self.assertEqual(game.live_rivals(), {})

    def test_the_list_marks_it_and_the_briefing_names_them(self):
        self.score(self.nib, 1700)
        self.visit(self.nib)
        self.score(self.ace, 1740)
        game = self.visit(self.nib)
        deck = ll.Deck(game.chapter, game.bests, True, None, (), game.logbook(), "", game.program_view(), None,
                       game.ghost_choice(), game.live_rivals())
        for host in (ll.Host(80, 24), ll.Host(80, 24, "16", False), ll.Host(80, 24, "256", True, charset="cp437")):
            display = ll.Display(host)
            canvas = display.draw(game.flight, "menu", mission=game.mission, catalog=game.missions,
                                  record_note=game.record_note, deck=deck)
            text = screen(canvas)
            self.assertIn("PASSED BY ACE: +40 PTS", text)
            self.assertIn("▼" if host.unicode else "v", text)
            display.encode(canvas)

    def test_their_ghost_joins_the_choices(self):
        self.score(self.nib, 1700)
        self.visit(self.nib)
        self.score(self.ace, 1740)
        game = self.visit(self.nib)
        self.assertEqual(game.ghost_choice(), "your best")
        game.key("g")
        self.assertEqual(game.ghost_mode, "rival")
        self.assertEqual(game.ghost_choice(), "Ace's best")
        game.key("1")  # the training basin: no rival there, so the cycle skips it
        game.key("2")
        game.key("down")  # Serenitatis: no rival, "rival" flies the node best
        self.assertEqual(game.ghost_mode, "rival")
        self.assertEqual(game.ghost_choice(), "node best, none yet")

    def test_other_nodes_and_lower_scores_are_not_rivals(self):
        self.score(self.nib, 1700)
        self.visit(self.nib)
        self.score(ll.Host(node="elsewhere", user=9, handle="Far"), 1900)
        self.score(self.ace, 1600)
        self.assertEqual(self.visit(self.nib).rivals, {})


if __name__ == "__main__":
    unittest.main()
