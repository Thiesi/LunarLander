"""What the terminal ends up showing: the bytes a display sends, read back by a
small ANSI terminal, must give the screen the display meant, frame after frame."""
import re
import unittest

import lunar_lander as ll


class Screen:
    """A terminal of the plainest kind: cursor addressing, erase, and the SGR
    colors of one depth. Bold is the bright foreground, as on a classic BBS
    terminal; anything it does not know raises, so a stray sequence is a failure."""

    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.cells = [[(" ", 7, 0)] * width for _ in range(height)]
        self.x = self.y = 0
        self.fg, self.bg, self.bold = 7, 0, False

    def feed(self, data: str):
        position = 0
        for match in re.finditer(r"\x1b\[([0-9;]*)([A-Za-z])", data):
            self.write(data[position:match.start()])
            position = match.end()
            numbers = [int(n) if n else 0 for n in match.group(1).split(";")]
            if match.group(2) == "H":
                self.y, self.x = numbers[0] - 1, (numbers[1] if len(numbers) > 1 else 1) - 1
            elif match.group(2) == "J":
                assert numbers == [2], numbers
                self.cells = [[(" ", self.fg, self.bg)] * self.width for _ in range(self.height)]
            elif match.group(2) == "m":
                self.sgr(numbers)
            else:
                raise AssertionError(f"unknown sequence {match.group()!r}")
        self.write(data[position:])

    def write(self, text: str):
        assert "\x1b" not in text, repr(text)
        for char in text:
            assert 0 <= self.x < self.width and 0 <= self.y < self.height, (self.x, self.y)
            ink = self.fg + 8 if self.bold and isinstance(self.fg, int) and self.fg < 8 else self.fg
            self.cells[self.y][self.x] = (char, ink, self.bg)
            self.x += 1

    def sgr(self, numbers: list):
        numbers = list(numbers)
        while numbers:
            n = numbers.pop(0)
            if n == 0:
                self.fg, self.bg, self.bold = 7, 0, False
            elif n == 1:
                self.bold = True
            elif 30 <= n <= 37:
                self.fg = n - 30
            elif 40 <= n <= 47:
                self.bg = n - 40
            elif 90 <= n <= 97:
                self.fg = n - 90 + 8
            elif 100 <= n <= 107:
                self.bg = n - 100 + 8
            elif n in (38, 48):
                kind = numbers.pop(0)
                color = numbers.pop(0) if kind == 5 else (numbers.pop(0), numbers.pop(0), numbers.pop(0))
                assert kind in (5, 2), kind
                if n == 38:
                    self.fg = color
                else:
                    self.bg = color
            else:
                raise AssertionError(f"unknown SGR {n}")


HOSTS = {
    "truecolor": ll.Host(80, 24, "truecolor"),
    "256": ll.Host(80, 24, "256"),
    "16 on NetBBS": ll.Host(80, 24, "16", source="netbbs"),
    "16 classic": ll.Host(80, 24, "16", True, charset="cp437", encoding="cp437", source="classic"),
    "16 classic ASCII": ll.Host(80, 24, "16", False, source="classic"),
    "256 ASCII": ll.Host(80, 24, "256", False),
}


class RoundTripTests(unittest.TestCase):
    def meant(self, display, canvas):
        """The screen the display means: its wire cells, colors as the terminal names them."""
        rows = []
        for row in display.wire(canvas):
            rows.append([(char, ll.rgb(fg) if display.host.color == "truecolor" else fg,
                          ll.rgb(bg) if display.host.color == "truecolor" else bg) for char, fg, bg in row])
        return rows

    def check(self, name, screen, display, canvas, step):
        for y, (shown, meant) in enumerate(zip(screen.cells, self.meant(display, canvas))):
            for x, ((char, fg, bg), (want, want_fg, want_bg)) in enumerate(zip(shown, meant)):
                if (char, bg) != (want, want_bg) or (want != " " and fg != want_fg):
                    self.fail(f"{name}, frame {step}, cell ({x}, {y}): shows {(char, fg, bg)}, meant "
                              f"{(want, want_fg, want_bg)}")

    def test_a_flight_reads_back_as_drawn_frame_after_frame(self):
        for name, host in HOSTS.items():
            with self.subTest(host=name):
                display, screen = ll.Display(host), Screen(host.width - 1, host.height)
                flight = ll.missions()[1].launch()
                flight.throttle, flight.angle = .6, 10
                for step in range(45):
                    for _ in range(12):
                        flight.step()
                    if step == 20:
                        flight.fuel, flight.throttle, flight.angle = 4, .9, -20  # the alarms and their chips
                    canvas = display.draw(flight, mission=ll.missions()[1])
                    screen.feed(display.encode(canvas))
                    self.check(name, screen, display, canvas, step)

    def test_every_screen_reads_back_as_drawn(self):
        crashed = ll.training()
        crashed.status, crashed.reason = "crashed", "Hard impact: reduce vertical speed to 3 m/s or less."
        for name, host in HOSTS.items():
            display, screen = ll.Display(host), Screen(host.width - 1, host.height)
            # One display through every screen in turn: each is a change from the last.
            for step, (mode, age) in enumerate((("splash", 5.5), ("menu", 0), ("help", 0), ("flying", 0),
                                                ("paused", 0), ("debrief", 0), ("crash", .6), ("crash", 3),
                                                ("medal", 2), ("promotion", 2.4), ("record", 0), ("scores", 0))):
                with self.subTest(host=name, mode=mode):
                    flight = crashed if mode in ("debrief", "crash") else ll.training()
                    canvas = display.draw(flight, mode, scene_age=age, standings=[("Ace", 1780, 3)])
                    screen.feed(display.encode(canvas))
                    self.check(name, screen, display, canvas, step)

    def test_an_idle_frame_sends_nothing_and_a_resize_repaints(self):
        for name, host in HOSTS.items():
            with self.subTest(host=name):
                display = ll.Display(host)
                canvas = display.draw(ll.training(), "menu")
                first = display.encode(canvas)
                self.assertEqual(display.encode(canvas), "")
                display.previous = None  # as after a resize
                screen = Screen(host.width - 1, host.height)
                screen.feed(display.encode(canvas))
                self.check(name, screen, display, canvas, 0)
                self.assertTrue(first.startswith("\x1b[0m\x1b[2J"))


if __name__ == "__main__":
    unittest.main()
