from pathlib import Path
import tempfile
import unittest

import lunar_lander as ll
from test_records import land


def screen(canvas):
    return "\n".join("".join(cell[0] for cell in row) for row in canvas.cells)


class ColdGasTests(unittest.TestCase):
    def setUp(self):
        self.mission = ll.in_craft(ll.missions()[1], "hopper")

    def test_the_thrusters_heat_cut_out_and_cool(self):
        flight = self.mission.launch()
        self.assertEqual(flight.cooling, ll.CRAFT["hopper"][6])
        full = flight.fuel
        flight.y, flight.vy = 300, -10
        flight.command("9")
        for _ in range(60 * 3):
            flight.step()
        self.assertLess(flight.fuel, full)
        for _ in range(60 * 60):
            flight.step()
            if flight.overheated:
                break
        self.assertTrue(flight.overheated)
        self.assertEqual(ll.fuel_alert(flight), 3)
        climbing = flight.vy
        flight.step()
        self.assertLess(flight.vy, climbing)  # cut out: falling, throttle or not
        for _ in range(60 * 60):
            flight.step()
            if not flight.overheated:
                break
        self.assertFalse(flight.overheated)
        self.assertGreaterEqual(flight.fuel + 1e-9, ll.OVERHEAT_RESUME * flight.initial_fuel)
        flight.command("0")
        before = flight.fuel
        for _ in range(60):
            flight.step()
        self.assertGreater(flight.fuel, before)  # idling cools

    def test_the_gas_weighs_nothing(self):
        flight = self.mission.launch()
        flight.command("9")
        flight.step()
        a = (flight.vy - self.mission.sink) / ll.DT + flight.gravity
        self.assertAlmostEqual(a, ll.CRAFT["hopper"][2] / ll.CRAFT["hopper"][1], places=1)

    def test_heat_on_the_panel_the_chip_and_the_radio(self):
        flight = self.mission.launch()
        flight.fuel = .1 * flight.initial_fuel
        display = ll.Display(ll.Host(80, 24))
        text = screen(display.draw(flight, mission=self.mission))
        self.assertIn("HEAT", text)
        self.assertIn("THRUSTERS HOT", text)
        self.assertIn("Thrusters hot", text)
        self.assertNotIn("FUEL", text)
        flight.status = "landed"
        text = screen(ll.Display(ll.Host(80, 24)).draw(flight, "debrief", mission=self.mission))
        self.assertIn("Thrusters at 90% heat", text)

    def test_a_steady_pilot_lands_everything_in_it(self):
        for mission in (*ll.missions("2026-10-31")[1:], *ll.HISTORIC):
            with self.subTest(mission=mission.key):
                flight = land(ll.in_craft(mission, "hopper"))
                self.assertEqual(flight.status, "landed", flight.reason)


class UnlockTests(unittest.TestCase):
    def test_squeaker_opens_the_hopper(self):
        with tempfile.TemporaryDirectory() as folder:
            records = ll.Records(Path(folder) / "pilots.db")
            try:
                game = ll.Game(ll.Host(node="n", user=7, handle="Nib"), records)
                self.assertNotIn("hopper", game.fleet())
                game.held["every-limit"] = 1
                self.assertEqual(game.fleet(), ["lm", "hopper"])
            finally:
                records.close()
        self.assertTrue(ll.ACHIEVEMENT["craft-hopper"].hidden)


class ArtTests(unittest.TestCase):
    def test_each_craft_has_its_own_art_on_the_lms_frame(self):
        for size in ("small", "medium"):
            for across in (1, 2):
                lm = set(ll.lander_roles(0, 0, 0, size, across))
                feet = max(y for _, y in lm)
                for craft in ("surveyor", "altair", "hopper"):
                    with self.subTest(size=size, across=across, craft=craft):
                        art = set(ll.lander_roles(0, 0, 0, size, across, craft))
                        self.assertNotEqual(art, lm)
                        self.assertEqual(max(y for _, y in art), feet)
                        xs = [x for x, _ in art]
                        self.assertEqual(min(xs) + max(xs), across - 1)  # centred as the LM is

    def test_the_view_draws_the_mission_craft(self):
        mission = ll.missions()[1]
        drawn = {}
        for craft in ll.CRAFT:
            variant = ll.in_craft(mission, craft)
            flight = variant.launch()
            canvas = ll.Display(ll.Host(80, 24)).draw(flight, mission=variant)
            drawn[craft] = screen(canvas)
        self.assertEqual(len(set(drawn.values())), len(ll.CRAFT))


if __name__ == "__main__":
    unittest.main()
