import unittest

import lunar_lander as ll
from test_career import touch_down


def screen(canvas):
    return "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)


class PostcardTests(unittest.TestCase):
    def landed(self, vy=-.2, fuel=None):
        game = ll.Game(ll.Host(80, 24, handle="Nib"))
        game.scenes = False
        game.key("2")
        game.key("enter")
        game.mode = "flying"
        touch_down(game, vy, fuel)
        return game

    def draw(self, game, mode, host=None):
        deck = ll.Deck(game.chapter, game.bests, False, game.award, (), game.logbook())
        display = ll.Display(host or ll.Host(80, 24, handle="Nib"))
        canvas = display.draw(game.flight, mode, mission=game.mission, record_note=game.record_note, deck=deck)
        display.encode(canvas)
        return screen(canvas)

    def test_a_gold_offers_one_and_it_shows_where_who_and_how_well(self):
        game = self.landed()
        self.assertEqual(game.award.medal, "GOLD")
        self.assertIn("[C] Postcard", self.draw(game, "debrief"))
        self.assertTrue(game.key("c"))
        self.assertEqual(game.mode, "postcard")
        for host in (ll.Host(80, 24, handle="Nib"), ll.Host(132, 50, handle="Nib"),
                     ll.Host(80, 24, "16", False, handle="Nib"),
                     ll.Host(80, 24, "256", True, charset="cp437", handle="Nib")):
            text = self.draw(game, "postcard", host)
            for words in ("G  R  E  E  T  I  N  G  S", "TRANQUILITY BASE", "Nib  /", f"{game.award.score:,} pts  /  GOLD"):
                self.assertIn(words, text)
        game.tick(5, True)
        self.assertEqual(game.mode, "postcard")  # it waits for the pilot
        self.assertTrue(game.key(" "))
        self.assertEqual(game.mode, "debrief")

    def test_no_postcard_without_gold(self):
        game = self.landed(vy=-2.9, fuel=5)
        self.assertNotEqual(game.award.medal, "GOLD")
        self.assertNotIn("[C] Postcard", self.draw(game, "debrief"))
        self.assertFalse(game.key("c"))

    def test_the_flag_stands_on_its_pole(self):
        flag = ll.flag_sprite(2)
        self.assertEqual(min(dy for _, dy in flag), -9)
        self.assertEqual(max(dy for _, dy in flag), 0)
        self.assertEqual(max(dx for dx, _ in flag), 14)


if __name__ == "__main__":
    unittest.main()
