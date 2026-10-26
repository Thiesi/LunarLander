from pathlib import Path
import tempfile
import unittest

import lunar_lander as ll
from test_career import touch_down


def rows(canvas):
    return ["".join(cell[0] for cell in row) for row in canvas.cells]


class FlightCallTests(unittest.TestCase):
    def flight(self, fuel=90, y=200):
        flight = ll.training()
        flight.fuel, flight.y = fuel, y
        return flight

    def radio(self, display, flight):
        return rows(display.draw(flight))[5]  # under the fuel chip

    def test_quiet_while_high_with_fuel_to_spare(self):
        display, flight = ll.Display(ll.Host()), self.flight()
        self.assertNotIn("\"", self.radio(display, flight))

    def test_each_fuel_alert_is_called_once_as_it_begins(self):
        display, flight = ll.Display(ll.Host()), self.flight(14)
        self.assertIn('"30 seconds."', self.radio(display, flight))
        flight.elapsed += 3.1
        self.assertNotIn("seconds", self.radio(display, flight))
        flight.fuel = 4
        self.assertIn('"10 seconds."', self.radio(display, flight))
        flight.fuel = 0
        self.assertIn("Fuel's out", self.radio(display, flight))

    def test_low_over_the_ground_it_reads_out_height_sink_and_drift(self):
        display, flight = ll.Display(ll.Host()), self.flight()
        ground = flight.terrain.height(flight.x)
        flight.y, flight.vy, flight.vx = ground + 3 + 40, -2.4, 1.2
        self.assertIn('"40 metres, down 2.4, drifting right."', self.radio(display, flight))
        flight.elapsed += 2.6
        flight.y = ground + 3 + 30
        self.assertNotIn("\"", self.radio(display, flight))  # not again for a few seconds
        flight.elapsed += 1.5
        flight.vx = -.9
        self.assertIn('"30 metres, down 2.4, drifting left."', self.radio(display, flight))

    def test_a_new_flight_starts_with_a_quiet_radio(self):
        display = ll.Display(ll.Host())
        self.radio(display, self.flight(14))
        self.assertIn("30 seconds", self.radio(display, self.flight(14)))  # called again for the new flight

    def test_every_call_fits_ascii_and_cp437(self):
        for host in (ll.Host(80, 24, "16", False), ll.Host(80, 24, "256", True, charset="cp437")):
            display, flight = ll.Display(host), self.flight(4)
            canvas = display.draw(flight)
            self.assertIn('"10 seconds."', rows(canvas)[5])
            display.encode(canvas)  # every glyph has a byte


class DebriefCallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.records = ll.Records(Path(self.temp.name) / "pilots.db")
        self.game = ll.Game(ll.Host(node="n", user=7, handle="Nib"), self.records)
        self.game.scenes = False

    def tearDown(self):
        self.records.close()
        self.temp.cleanup()

    def debrief(self):
        game = self.game
        deck = ll.Deck(game.chapter, game.bests, True, game.award, tuple(game.unlocked), game.logbook())
        canvas = ll.Display(ll.Host(80, 24)).draw(game.flight, "debrief", mission=game.mission,
                                                  catalog=game.missions, record_note=game.record_note, deck=deck)
        return "\n".join(rows(canvas))

    def land(self, **kwargs):
        self.game.mode = "menu"
        self.game.key("2")  # Tranquility
        self.game.key("enter")
        self.game.mode = "flying"
        touch_down(self.game, **kwargs)
        return self.debrief()

    def test_a_first_gold_names_its_base(self):
        self.assertIn("Houston, Tranquility Base here. The Eagle has landed.", self.land())
        self.assertNotIn("Eagle", self.land())  # the second gold is routine

    def test_a_landing_on_fumes_earns_relief(self):
        self.game.bests["tranquility"] = 99999  # no new medal to celebrate
        self.assertIn("about to turn blue", self.land(fuel=3))

    def test_a_crash_and_an_empty_tank(self):
        text = self.land(vy=-20)
        self.assertTrue(any(call in text for call in ll.CRASH_CALLS))
        self.assertIn("Fuel exhausted", self.land(vy=-20, fuel=0))

    def test_every_call_fits_the_card(self):
        mission = ll.missions()[1]
        for flight_time in range(10):
            for status, fuel in (("landed", 50), ("landed", 1), ("crashed", 50), ("crashed", 0)):
                flight = ll.training()
                flight.status, flight.fuel, flight.elapsed = status, fuel, flight_time / 10
                self.assertLessEqual(len(ll.debrief_call(flight, mission)) + 2, 60)
        for long in ll.missions():
            award = ll.Award(long, 9999, "GOLD", "GOLD", True, None, None)
            flight = ll.training()
            flight.status = "landed"
            self.assertLessEqual(len(ll.debrief_call(flight, long, award)) + 2, 60, long.name)


if __name__ == "__main__":
    unittest.main()
