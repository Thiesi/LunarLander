import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import lunar_lander as ll


class DatePartTests(unittest.TestCase):
    def test_the_date_in_common_node_formats(self):
        for node, expected in (("%d.%m.%Y %H:%M", "%d.%m.%Y"),       # NetBBS's default
                               ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"),
                               ("%m/%d/%Y %I:%M %p", "%m/%d/%Y"),
                               ("%a %d %b %Y, %H:%M", "%a %d %b %Y"),
                               ("%H:%M %d/%m/%y", "%d/%m/%y"),
                               ("%A, %B %d, %Y", "%A, %B %d, %Y"),
                               ("%Y-%m-%d", "%Y-%m-%d"),
                               ("%d.%m. %H:%M %Y", "%d.%m"),           # trimmed to end on a date
                               ("%d.%m.%Y %H:%M %Z", "%d.%m.%Y")):
            with self.subTest(node=node):
                self.assertEqual(ll.date_part(node), expected)

    def test_nothing_usable_falls_back(self):
        for node in ("%H:%M", "%H:%M:%S %p", "", "100%%", "%d%% %H", None, 42, "day %d at %H"):
            with self.subTest(node=node):
                result = ll.date_part(node)
                self.assertTrue(result is None or ll.date_format_ok(result), result)
        self.assertIsNone(ll.date_part("%H:%M"))
        self.assertEqual(ll.date_part("day %d at %H"), "%d")


class PrecedenceTests(unittest.TestCase):
    def host(self, **fields):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "door.json"
            path.write_text(json.dumps({"door_api": 5, **fields}), encoding="utf-8")
            return ll.Host.load(str(path))

    def test_the_sysops_setting_then_the_node_then_iso(self):
        node = self.host(datetime_format="%d.%m.%Y %H:%M")
        self.assertEqual(node.datetime_format, "%d.%m.%Y %H:%M")
        with mock.patch.dict(os.environ, {"DOOR_LL_DATE_FORMAT": "%m/%d/%Y"}):
            self.assertEqual(ll.daily_format(node), "%m/%d/%Y")
        with mock.patch.dict(os.environ, {"DOOR_LL_DATE_FORMAT": ""}):
            self.assertEqual(ll.daily_format(node), "%d.%m.%Y")
            self.assertEqual(ll.daily_format(self.host()), "%Y-%m-%d")
            self.assertEqual(ll.daily_format(self.host(datetime_format="%H:%M")), "%Y-%m-%d")
            for bad in (12, ["%d"], "%d" * 40):
                self.assertIsNone(self.host(datetime_format=bad).datetime_format)

    def test_the_daily_title_follows_the_node(self):
        clock = ll.DailyClock("UTC", ll.date_part("%d.%m.%Y %H:%M"))
        self.assertEqual(clock.warning, "")
        daily = next(m for m in ll.missions("2026-10-25", clock.date_format) if m.key.startswith("daily-"))
        self.assertEqual(daily.name, "DAILY 25.10.2026")
        # The seed and record key keep the ISO date whatever the display.
        self.assertEqual(daily.key, "daily-2026-10-25")


if __name__ == "__main__":
    unittest.main()
