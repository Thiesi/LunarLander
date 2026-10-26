import unittest

import lunar_lander as ll
from test_records import land


def screen(canvas):
    return "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)


def settle_on(flight, pad, vy=-.2, angle=0):
    flight.x, flight.y = (pad.left + pad.right) / 2, pad.height + 3.01
    flight.vx, flight.vy, flight.angle, flight.throttle = 0, vy, angle, 0
    for _ in range(10):
        flight.step()
    return flight


class HistoryTests(unittest.TestCase):
    def test_a_chapter_of_five_that_never_touches_rank(self):
        chapter = next(c for c in ll.CHAPTERS if c.key == "history")
        self.assertFalse(chapter.ranked)
        shelf = ll.chapter_missions(chapter, ll.missions())
        self.assertEqual([m.name for m in shelf], ["APOLLO 11", "APOLLO 12", "APOLLO 15", "APOLLO 17", "CHANG'E 3"])
        bests = {m.key: 9999 for m in shelf}
        self.assertEqual(ll.career(bests, ll.missions()).points, 0)
        self.assertEqual(len(ll.tour_missions(ll.missions())), 15)
        self.assertTrue({"history", "eagle"} <= ll.career_feats(bests, ll.missions()))

    def test_every_one_is_landable_in_every_craft(self):
        for mission in ll.HISTORIC:
            for craft in ll.CRAFT:
                with self.subTest(mission=mission.key, craft=craft):
                    self.assertEqual(land(ll.in_craft(mission, craft)).status, "landed")

    def test_change3_lands_on_any_of_its_sites(self):
        mission = ll.HISTORIC[4]
        for centre in (mission.center, *mission.sites):
            flight = mission.launch()
            site = next(p for p in (flight.terrain.pad, *flight.sites) if (p.left + p.right) / 2 == centre)
            with self.subTest(site=centre):
                self.assertEqual(settle_on(flight, site).status, "landed")
        flight = mission.launch()
        flight.x, flight.y, flight.vy = 420, flight.terrain.height(420) + 3.01, -.2
        flight.step()
        self.assertEqual(flight.status, "crashed")  # between the sites is no site

    def test_the_twists_show_in_the_view(self):
        apollo11 = ll.HISTORIC[0].launch()
        apollo11.elapsed = 9
        seen = {any("PROGRAM ALARM 1202" in line for line in screen(ll.Display(ll.Host(80, 24)).draw(
            apollo11, mission=ll.HISTORIC[0])).split("\n")) for _ in range(6)}
        self.assertIn(True, seen)
        apollo11.elapsed = 15
        self.assertNotIn("PROGRAM ALARM", screen(ll.Display(ll.Host(80, 24)).draw(apollo11, mission=ll.HISTORIC[0])))
        apollo12 = ll.HISTORIC[1].launch()
        apollo12.x, apollo12.y = 300, 120
        display = ll.Display(ll.Host(132, 50))
        for _ in range(3):
            text = screen(display.draw(apollo12, mission=ll.HISTORIC[1]))
        self.assertIn("SURVEYOR 3", text)
        change3 = ll.HISTORIC[4].launch()
        change3.x, change3.y = 500, 150
        display = ll.Display(ll.Host(132, 50))
        for _ in range(3):
            text = screen(display.draw(change3, mission=ll.HISTORIC[4]))
        self.assertIn("SITE", text)

    def test_the_debrief_tells_what_the_crew_did(self):
        for mission, words in zip(ll.HISTORIC, ('"30 seconds"; you had', "about 160 m from Surveyor 3",
                                                "tilted about 10 degrees; you, 0", "December 1972",
                                                "100 m hover")):
            flight = settle_on(mission.launch(), mission.launch().terrain.pad)
            with self.subTest(mission=mission.key):
                self.assertIn(words, ll.history_line(mission, flight))
                text = screen(ll.Display(ll.Host(80, 40)).draw(flight, "debrief", mission=mission))
                self.assertIn(words, text)
                self.assertLessEqual(len(ll.history_line(mission, flight)), 60)
        crashed = ll.HISTORIC[0].launch()
        crashed.status = "crashed"
        self.assertEqual(ll.history_line(ll.HISTORIC[0], crashed), "")

    def test_briefings_fit_two_lines(self):
        import textwrap
        for mission in ll.HISTORIC:
            self.assertLessEqual(len(textwrap.wrap(mission.description, 37)), 2, mission.key)


if __name__ == "__main__":
    unittest.main()
