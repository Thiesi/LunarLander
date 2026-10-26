import json
from pathlib import Path
import tempfile
import unittest

import lunar_lander as ll
from test_career import touch_down


def screen(canvas):
    return "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)


class PresenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name) / "live"
        self.nib = ll.Presence(self.folder, ll.Host(node="n", user=7, handle="Nib"))
        self.ace = ll.Presence(self.folder, ll.Host(node="n", user=9, handle="Ace"))

    def tearDown(self):
        self.temp.cleanup()

    def test_each_sees_the_other_not_itself(self):
        self.nib.tell({"doing": "descending", "mission": "Hadley Rille"}, 100)
        self.ace.tell({"doing": "idle"}, 100)
        self.assertEqual(self.nib.others(101), [])
        self.assertEqual(self.ace.others(101), [{"handle": "Nib", "doing": "descending", "mission": "Hadley Rille"}])

    def test_a_result_shows_for_a_minute_and_a_dead_door_goes_stale(self):
        self.nib.tell({"doing": "landed", "mission": "Tranquility", "medal": "GOLD"}, 100)
        self.assertEqual(len(self.ace.others(150)), 0)  # no heartbeat for 50 s: stale
        self.nib.tell({"doing": "landed", "mission": "Tranquility", "medal": "GOLD"}, 150)
        self.assertEqual(len(self.ace.others(155)), 1)
        self.nib.tell({"doing": "landed", "mission": "Tranquility", "medal": "GOLD"}, 165)
        self.assertEqual(len(self.ace.others(166)), 0)  # landed over a minute ago

    def test_heartbeats_rewrite_only_every_few_seconds(self):
        self.nib.tell({"doing": "descending", "mission": "X"}, 100)
        written = self.nib.path.read_text()
        self.nib.tell({"doing": "descending", "mission": "X"}, 102)
        self.assertEqual(self.nib.path.read_text(), written)
        self.nib.tell({"doing": "descending", "mission": "X"}, 106)
        self.assertNotEqual(self.nib.path.read_text(), written)

    def test_other_nodes_junk_and_closing(self):
        far = ll.Presence(self.folder, ll.Host(node="elsewhere", user=9, handle="Far"))
        far.tell({"doing": "descending", "mission": "X"}, 100)
        (self.folder / "junk.json").write_text("{not json")
        (self.folder / "odd.json").write_text(json.dumps({"node": "n", "beat": 100, "since": 100, "state": 3}))
        self.assertEqual(self.nib.others(100), [])
        self.nib.tell({"doing": "idle"}, 100)
        self.nib.close()
        self.assertFalse(self.nib.path.exists())
        self.nib.close()  # twice is fine

    def test_the_line_takes_turns(self):
        others = [{"handle": "Nib", "doing": "descending", "mission": "Tsiolkovsky"},
                  {"handle": "Ace", "doing": "landed", "mission": "Polar Approach", "medal": "GOLD"},
                  {"handle": "Cat", "doing": "crashed", "mission": "Aitken Basin"}]
        self.assertEqual(ll.live_line(others, 0), "Nib is descending on Tsiolkovsky...")
        self.assertEqual(ll.live_line(others, 4), "Ace landed on Polar Approach: gold")
        self.assertEqual(ll.live_line(others, 8), "Cat came down hard at Aitken Basin")
        self.assertEqual(ll.live_line([], 0), "")


class GameTests(unittest.TestCase):
    def test_the_state_follows_the_flight(self):
        game = ll.Game(ll.Host(node="n", user=7, handle="Nib"))
        game.scenes = False
        self.assertEqual(game.live_state(), {"doing": "idle"})
        game.key("2")
        game.key("enter")
        game.mode = "flying"
        self.assertEqual(game.live_state(), {"doing": "descending", "mission": "Tranquility"})
        touch_down(game)
        self.assertEqual(game.live_state(), {"doing": "landed", "mission": "Tranquility", "medal": "GOLD"})

    def test_the_flight_director_sets_it_into_its_edge(self):
        game = ll.Game()
        for host in (ll.Host(80, 24), ll.Host(80, 40, "16", False)):
            deck = ll.Deck(live="Ace is descending on Tsiolkovsky...")
            text = screen(ll.Display(host).draw(game.flight, "menu", mission=game.mission, deck=deck))
            self.assertIn("Ace is descending on Tsiolkovsky...", text)


if __name__ == "__main__":
    unittest.main()
