import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

import lunar_lander as ll


class MetadataTests(unittest.TestCase):
    def load(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "door.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return ll.Host.load(str(path))

    def test_optional_fields_and_additions(self):
        host = self.load({"door_api": 5, "future": 123})
        self.assertEqual((host.width, host.height, host.color), (80, 24, "16"))
        self.assertFalse(host.ranked)

    def test_identity_and_width_safe_handle(self):
        host = self.load({"door_api": 5, "node_id": "node", "user_id": 42,
                          "handle": "\x1b\n界" * 50, "terminal_width": 132, "terminal_height": 50})
        self.assertTrue(host.ranked)
        self.assertEqual(host.handle, "界" * 20)
        self.assertEqual(host.width, 132)

    def test_invalid_metadata_is_not_demo(self):
        for data in ({"door_api": 6}, {}, [], {"door_api": True},
                     {"door_api": 5, "terminal_width": -1}, {"door_api": 5, "session_limit_seconds": math.inf}):
            with self.subTest(data=data), self.assertRaises(ll.DoorError):
                self.load(data)


class InputTests(unittest.TestCase):
    def test_fragmented_arrows_and_unknown_sequence(self):
        keys = ll.Keys()
        self.assertEqual(keys.feed(b"\x1b", 0), [])
        self.assertEqual(keys.feed(b"[", .02), [])
        self.assertEqual(keys.feed(b"A\x1b[1;5D9 \x1b[99~q", .04), ["up", "left", "9", " ", "q"])

    def test_escape_and_alt_do_not_thrust(self):
        keys = ll.Keys()
        self.assertEqual(keys.feed(b"\x1b", 0), [])
        self.assertEqual(keys.feed(b"", .3), ["escape"])
        self.assertEqual(keys.feed(b"\x1bw", .5), [])

    def test_latched_controls(self):
        flight = ll.training()
        flight.command("9")
        flight.command("left")
        flight.step()
        self.assertEqual((flight.throttle, flight.angle), (1, -10))
        flight.command(" ")
        flight.command("x")
        self.assertEqual((flight.throttle, flight.angle), (0, 0))


class FlightTests(unittest.TestCase):
    def test_ballistic_motion_and_replay(self):
        a, b = ll.training(), ll.training()
        for _ in range(60):
            a.step()
            b.step()
        self.assertEqual(a, b)
        self.assertAlmostEqual(a.y, 180 - 6 - .5 * ll.GRAVITY, places=8)
        self.assertAlmostEqual(a.vy, -6 - ll.GRAVITY, places=8)

    def test_empty_tank_and_partial_burn(self):
        flight = ll.training()
        flight.fuel = .001
        flight.throttle = 1
        flight.step()
        self.assertEqual(flight.fuel, 0)
        vy = flight.vy
        flight.step()
        self.assertAlmostEqual(flight.vy, vy - ll.GRAVITY * ll.DT)

    def test_touchdown_causes(self):
        for changes, result, reason in (({}, "landed", "Contact"),
                ({"vx": 4}, "crashed", "drift"), ({"vy": -8}, "crashed", "Hard"),
                ({"angle": 30}, "crashed", "Attitude"), ({"x": 249}, "crashed", "Terrain")):
            with self.subTest(changes=changes):
                flight = ll.training()
                flight.y, flight.vy = 27, -1
                for key, value in changes.items():
                    setattr(flight, key, value)
                flight.step()
                self.assertEqual(flight.status, result)
                self.assertIn(reason, flight.reason)

    def test_fast_impact_cannot_tunnel(self):
        flight = ll.training()
        flight.y, flight.vy = 40, -1500
        flight.step()
        self.assertEqual(flight.status, "crashed")
        self.assertGreater(flight.y, 27)

    def test_scripted_training_landing(self):
        flight = ll.training()
        for _ in range(60 * 180):
            altitude = flight.y - flight.terrain.pad.height - 3
            desired_vy = -min(9, max(.8, altitude * .12))
            acceleration = ll.GRAVITY + (desired_vy - flight.vy) * 1.5
            flight.throttle = max(0, min(1, acceleration * (ll.DRY_MASS + flight.fuel) / ll.MAX_THRUST))
            flight.step()
            if flight.status != "flying":
                break
        self.assertEqual(flight.status, "landed", flight.reason)
        self.assertGreater(flight.fuel, 0)
        self.assertGreater(flight.score(), 1000)


class ProcessTests(unittest.TestCase):
    def run_door(self, data, keys):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "door.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            env = {**os.environ, "NETBBS_DOOR_INFO": str(path)}
            return subprocess.run([sys.executable, "lunar_lander.py"], input=keys,
                                  capture_output=True, env=env, timeout=5)

    def test_quit_and_eof_restore_cursor(self):
        for keys in (b"q", b""):
            result = self.run_door({"door_api": 5}, keys)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(b"\x1b[?25h", result.stdout)

    def test_expired_deadline_exits(self):
        result = self.run_door({"door_api": 5, "session_limit_seconds": 0}, b"")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_live_deadline_with_open_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "door.json"
            path.write_text(json.dumps({"door_api": 5, "session_limit_seconds": .6}))
            with tempfile.TemporaryFile() as capture, subprocess.Popen([sys.executable, "lunar_lander.py"], stdin=subprocess.PIPE,
                    stdout=capture, stderr=subprocess.PIPE,
                    env={**os.environ, "NETBBS_DOOR_INFO": str(path)}) as process:
                started = time.monotonic()
                self.assertEqual(process.wait(timeout=3), 0)
                self.assertLess(time.monotonic() - started, 2)
                _, error = process.communicate()
                capture.seek(0)
                output = capture.read()
                self.assertIn(b"\x1b[?25h", output)
                self.assertEqual(error, b"")

    def test_bad_host_metadata_reports_to_sysop(self):
        result = self.run_door({"door_api": 99}, b"")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"supported door_api", result.stderr)


if __name__ == "__main__":
    unittest.main()
