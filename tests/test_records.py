from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

import lunar_lander as ll


def land(mission):
    """A 10 Hz pilot using the same angle/throttle increments as human controls."""
    flight = mission.launch()
    for frame in range(1800):
        altitude = flight.y - flight.terrain.pad.height - 3
        desired_vy = -min(8, max(.8, altitude * .10))
        desired_vx = max(-8, min(8, (mission.center - flight.x) * .08))
        ax = (desired_vx - flight.vx) * .8
        ay = ll.GRAVITY + (desired_vy - flight.vy) * 1.2
        angle = max(-60, min(60, round(math.degrees(math.atan2(ax, max(.1, ay))) / 10) * 10))
        flight.angle = angle
        throttle = math.hypot(ax, ay) * (ll.DRY_MASS + flight.fuel) / ll.MAX_THRUST
        flight.command(str(max(0, min(9, round(throttle * 9)))))
        for _ in range(6):
            flight.step()
        if flight.status != "flying":
            return flight
    return flight


class MissionTests(unittest.TestCase):
    def test_authored_and_daily_missions_are_landable(self):
        for mission in ll.missions("2026-10-24"):
            with self.subTest(mission=mission.key):
                flight = land(mission)
                self.assertEqual(flight.status, "landed", str(flight))
                self.assertGreater(flight.fuel, 5)
                self.assertGreaterEqual(mission.width, 45)

    def test_daily_reproducible_across_processes(self):
        code = "import lunar_lander as l; print(repr(l.missions('2026-10-24')[-1].launch()))"
        first = subprocess.check_output([sys.executable, "-c", code])
        second = subprocess.check_output([sys.executable, "-c", code])
        self.assertEqual(first, second)
        self.assertNotEqual(ll.missions("2026-10-24")[-1], ll.missions("2026-10-25")[-1])


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "pilots.db"
        self.records = ll.Records(self.path)
        self.host = ll.Host(node="node-a", user=7, handle="Pilot")
        self.mission = ll.missions()[1]
        self.flight = land(self.mission)

    def tearDown(self):
        self.records.close()
        self.temp.cleanup()

    def test_best_survives_restart_and_rename(self):
        self.assertTrue(self.records.save(self.host, self.mission, self.flight))
        score = self.flight.score()
        self.flight.fuel = 0
        self.assertFalse(self.records.save(self.host, self.mission, self.flight))
        self.records.close()
        self.records = ll.Records(self.path)
        renamed = ll.Host(node="node-a", user=7, handle="New name")
        self.assertEqual(self.records.top(renamed, self.mission), [("New name", score)])

    def test_identity_mission_and_practice_isolation(self):
        self.records.save(self.host, self.mission, self.flight)
        self.assertEqual(self.records.top(ll.Host(node="node-b", user=7), self.mission), [])
        self.assertEqual(self.records.top(self.host, ll.missions()[2]), [])
        self.assertFalse(self.records.save(ll.Host(), self.mission, self.flight))
        self.assertFalse(self.records.save(self.host, ll.missions()[0], self.flight))
        self.flight.status = "crashed"
        self.assertFalse(self.records.save(self.host, self.mission, self.flight))

    def test_concurrent_pilots_and_same_pilot_best(self):
        def save(user, fuel):
            records = ll.Records(self.path)
            try:
                flight = land(self.mission)
                flight.fuel = fuel
                records.save(ll.Host(node="node-a", user=user, handle=f"Pilot {user}"), self.mission, flight)
            finally:
                records.close()
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda args: save(*args), [(7, 10), (8, 20), (7, 70), (7, 30)]))
        rows = self.records.top(self.host, self.mission)
        self.assertEqual(len(rows), 2)
        expected = land(self.mission)
        expected.fuel = 70
        self.assertEqual(rows[0][1], expected.score())

    def test_newer_schema_refused_without_replacement(self):
        self.records.db.execute("PRAGMA user_version=99")
        self.records.close()
        before = self.path.read_bytes()
        with self.assertRaises(ll.DoorError):
            ll.Records(self.path)
        self.assertEqual(self.path.read_bytes(), before)

    def test_corrupt_database_preserved(self):
        self.records.close()
        self.path.write_bytes(b"not a SQLite database")
        with self.assertRaises(ll.DoorError):
            ll.Records(self.path)
        self.assertEqual(self.path.read_bytes(), b"not a SQLite database")

    def test_readonly_result_failure_still_reaches_debrief(self):
        game = ll.Game(self.host, self.records)
        game.key("2")
        game.key("enter")
        game.flight.x = game.mission.center
        game.flight.y = game.flight.terrain.pad.height + 3
        game.flight.vx, game.flight.vy = 0, -1
        self.records.db.execute("PRAGMA query_only=ON")
        game.tick(.1, True)
        self.assertEqual(game.mode, "debrief")
        self.assertIn("not saved", game.record_note)


if __name__ == "__main__":
    unittest.main()
