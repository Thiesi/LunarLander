import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import lunar_lander as ll


def door32(comm_type=0, handle=0, emulation=1, minutes=45, user=17, alias="Nib"):
    # Comm type, handle, baud, BBS software, record number, real name, alias,
    # security level, minutes left, emulation, node.
    return "\r\n".join(map(str, (comm_type, handle, 38400, "Synchronet 3.20", user, "Ann Example",
                                 alias, 50, minutes, emulation, 2))) + "\r\n"


def doorsys(graphics="GR", rows=25, minutes=30, user=23, alias="Ace"):
    lines = ["COM0:", "38400", "8", "1", "38400", "Y", "Y", "Y", "Y", "Ann Example",
             "Springfield", "555", "555", "secret", "50", "3", "2026-10-25", "1800", str(minutes),
             graphics, str(rows), "Y", "", "", "", str(user)] + [""] * 9 + [alias]
    return "\n".join(lines) + "\n"


class DropFileTests(unittest.TestCase):
    def write(self, name, text):
        directory = tempfile.mkdtemp()
        path = Path(directory) / name
        path.write_bytes(text.encode("cp437"))
        return path

    def test_door32_and_doorsys(self):
        info = ll.drop_file_info(self.write("DOOR32.SYS", door32()))
        self.assertEqual((info["user_id"], info["handle"], info["minutes_left"], info["ansi"], info["height"]),
                         (17, "Nib", 45, True, 24))
        info = ll.drop_file_info(self.write("door.sys", doorsys()))
        self.assertEqual((info["user_id"], info["handle"], info["minutes_left"], info["ansi"], info["height"]),
                         (23, "Ace", 30, True, 25))

    def test_renamed_files_are_recognised_and_bad_ones_refused(self):
        self.assertEqual(ll.drop_file_info(self.write("caller.dat", door32()))["kind"], "DOOR32.SYS")
        self.assertEqual(ll.drop_file_info(self.write("caller.dat", doorsys()))["kind"], "DOOR.SYS")
        for text in ("hello\n", door32(comm_type=7), door32(user=0), doorsys(graphics="XX")):
            with self.subTest(text=text[:12]):
                with self.assertRaises(ValueError):
                    ll.drop_file_info(self.write("DOOR32.SYS" if "COM0" not in text else "DOOR.SYS", text))

    def test_names_lose_terminal_commands(self):
        info = ll.drop_file_info(self.write("DOOR32.SYS", door32(alias="\x1b[2JNib\x07")))
        self.assertEqual(info["handle"], "Nib")

    def test_plain_terminals_are_marked(self):
        self.assertFalse(ll.drop_file_info(self.write("DOOR32.SYS", door32(emulation=0)))["ansi"])
        self.assertFalse(ll.drop_file_info(self.write("DOOR.SYS", doorsys(graphics="NG")))["ansi"])


class ClassicHostTests(unittest.TestCase):
    def host(self, text, name="DOOR32.SYS", **kwargs):
        path = Path(tempfile.mkdtemp()) / name
        path.write_bytes(text.encode("cp437"))
        return ll.Host.classic(str(path), **kwargs)

    def test_a_classic_caller(self):
        with mock.patch.dict(os.environ, {"DOOR_LL_NODE_ID": "", "DOOR_LL_BBS_NAME": "", "DOOR_LL_TIMEZONE": ""}):
            for key in ("DOOR_LL_NODE_ID", "DOOR_LL_BBS_NAME", "DOOR_LL_TIMEZONE"):
                del os.environ[key]
            host = self.host(door32())
        self.assertEqual((host.source, host.width, host.height, host.color, host.encoding, host.charset),
                         ("classic", 80, 24, "16", "cp437", "cp437"))
        self.assertEqual((host.handle, host.user, host.node, host.bbs, host.timezone, host.limit, host.socket),
                         ("Nib", 17, "classic", "BBS", "UTC", 2700.0, None))
        self.assertTrue(host.ranked)
        self.assertEqual(ll.Display(host).across, 1)  # CP437 has half blocks, not quadrants

    def test_profile_settings_and_overrides(self):
        with mock.patch.dict(os.environ, {"DOOR_LL_NODE_ID": "moonbase", "DOOR_LL_BBS_NAME": "[Moon]base 7",
                                          "DOOR_LL_TIMEZONE": "Europe/Berlin"}):
            host = self.host(door32(comm_type=2, handle=1234), encoding="utf-8", color="256")
        self.assertEqual((host.node, host.bbs, host.timezone, host.socket, host.encoding, host.color),
                         ("moonbase", "Moonbase 7", "Europe/Berlin", 1234, "utf-8", "256"))
        self.assertEqual(ll.Display(host).across, 2)

    def test_a_bad_drop_file_names_no_path(self):
        with self.assertRaises(ll.DoorError) as caught:
            self.host("nonsense\n", name="secret-place.dat")
        self.assertNotIn("secret-place", str(caught.exception))

    def test_every_screen_reaches_cp437_without_loss(self):
        host = self.host(door32())
        for mode in ("splash", "menu", "flying", "help", "paused", "debrief", "scores", "confirm",
                     "launch", "landing", "crash", "medal", "promotion"):
            with self.subTest(mode=mode):
                display = ll.Display(host)
                flight = ll.training()
                flight.angle = 15
                text = display.encode(display.draw(flight, mode, scene_age=1.2))
                data = ll.encode_output(text, "cp437")
                self.assertEqual(data.count(b"?"), text.count("?"))


class SocketLinkTests(unittest.TestCase):
    def setUp(self):
        self.caller, ours = socket.socketpair()
        self.link = ll.SocketLink(ours.detach())

    def tearDown(self):
        self.caller.close()
        if not self.link.lost:
            self.link.close()

    def test_telnet_commands_are_filtered_and_enter_is_one_key(self):
        self.caller.sendall(b"x\xff\xfb\x01\xff\xffy\r\x00z\xff\xfa\x18\x00abc\xff\xf0w\r\nq")
        data = b""
        while len(data) < 7:
            data += self.link.read(1) or b""
        self.assertEqual(data, b"x\xffy\rzw\rq")
        self.assertEqual(ll.Keys().feed(b"\r\n\r\x00", 0), ["enter", "enter"])

    def test_output_doubles_iac_and_carrier_loss_is_eof(self):
        self.link.write(b"a\xffb")
        self.assertEqual(self.caller.recv(16), b"a\xff\xffb")
        self.caller.close()
        self.assertEqual(self.link.read(1), b"")
        with self.assertRaises(ConnectionResetError):
            self.link.write(b"late")


class ClassicProcessTests(unittest.TestCase):
    def test_a_door32_stdio_launch_speaks_cp437(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "DOOR32.SYS"
            path.write_bytes(door32().encode("cp437"))
            env = {**os.environ, "DOOR_LL_DATA_DIR": directory, "DOOR_SPLASH": "0"}
            env.pop("NETBBS_DOOR_INFO", None)
            result = subprocess.run([sys.executable, "lunar_lander.py", str(path)], input=b"q",
                                    capture_output=True, env=env, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"FLIGHT DIRECTOR", result.stdout)
        self.assertIn(b"\xda", result.stdout)          # CP437's corner, not UTF-8's
        self.assertNotIn("─".encode("utf-8"), result.stdout)

    def test_a_plain_terminal_is_told_it_needs_ansi(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "DOOR.SYS"
            path.write_bytes(doorsys(graphics="NG").encode("cp437"))
            env = {**os.environ, "DOOR_LL_DATA_DIR": directory}
            env.pop("NETBBS_DOOR_INFO", None)
            result = subprocess.run([sys.executable, "lunar_lander.py", str(path)], input=b"",
                                    capture_output=True, env=env, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"needs an ANSI terminal", result.stdout)
        self.assertNotIn(b"\x1b[", result.stdout)


if __name__ == "__main__":
    unittest.main()
