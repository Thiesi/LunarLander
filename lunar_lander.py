#!/usr/bin/env python3
"""Lunar Lander for NetBBS. Copyright (c) 2026 Thiesi. BSD-2-Clause.

Runtime dependency: Python 3.11+ standard library. NetBBS owns transport framing;
this program owns only the native child stdin/stdout stream.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import select
import signal
import sys
import time
import unicodedata

VERSION = "0.1.0-dev"
DT = 1 / 60
GRAVITY = 1.62
DRY_MASS = 900.0
MAX_THRUST = 3600.0
FUEL_FLOW = 1.2


class DoorError(Exception):
    """Bounded, actionable configuration failure."""


def plain(text: str, columns: int = 40) -> str:
    """Sanitize a label before ANSI composition, clipping by display cells."""
    result = []
    used = 0
    for char in str(text):
        if unicodedata.category(char).startswith("C") or unicodedata.combining(char):
            continue
        width = 2 if unicodedata.east_asian_width(char) in "WF" else 1
        if used + width > columns:
            break
        result.append(char)
        used += width
    return "".join(result)


@dataclass(frozen=True)
class Host:
    width: int = 80
    height: int = 24
    color: str = "256"
    unicode: bool = True
    handle: str = "Pilot"
    node: str = ""
    user: int | None = None
    limit: float | None = None
    path: str | None = None

    @property
    def ranked(self) -> bool:
        return bool(self.node) and self.user is not None and self.user > 0

    @classmethod
    def load(cls, path: str | None = None) -> Host:
        if path is None:
            size = os.get_terminal_size() if sys.stdin.isatty() else os.terminal_size((80, 24))
            return cls(width=size.columns, height=size.lines)
        try:
            with open(path, "rb") as stream:
                raw = stream.read(65537)
            if len(raw) > 65536:
                raise ValueError("metadata exceeds 64 KiB")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("metadata must be an object")
            api = data.get("door_api")
            if type(api) is not int or api not in (2, 3, 4, 5):
                raise ValueError("supported door_api versions are 2, 3, 4 and 5")
            geometry = []
            for name, default, maximum in (("terminal_width", 80, 500), ("terminal_height", 24, 200)):
                value = data.get(name, default)
                if type(value) is not int or not 1 <= value <= maximum:
                    raise ValueError(f"invalid {name}")
                geometry.append(value)
            limit = data.get("session_limit_seconds")
            if limit is not None and (type(limit) not in (int, float) or not math.isfinite(limit) or limit < 0):
                raise ValueError("invalid session_limit_seconds")
            user = data.get("user_id")
            if user is not None and type(user) is not int:
                raise ValueError("invalid user_id")
            node = data.get("node_id", "")
            if not isinstance(node, str) or len(node) > 256:
                raise ValueError("invalid node_id")
            return cls(*geometry, color=data.get("color_depth") if data.get("color_depth") in
                       ("16", "256", "truecolor") else "16",
                       unicode=data.get("unicode_style") is True,
                       handle=plain(data.get("handle", "Pilot")), node=node, user=user,
                       limit=limit, path=path)
        except (OSError, ValueError, TypeError) as exc:
            raise DoorError(f"Cannot read NetBBS launch metadata: {exc}") from exc


class Keys:
    """Incremental ANSI/SS3 decoder. Escape tails never become flight commands."""

    def __init__(self):
        self.buffer = bytearray()
        self.since = 0.0

    def feed(self, data: bytes, now: float) -> list[str]:
        if not self.buffer:
            self.since = now
        self.buffer.extend(data[:256])
        result = []
        while self.buffer:
            first = self.buffer[0]
            if first != 27:
                del self.buffer[0]
                if first in (3, 4):
                    result.append("q")
                elif first in (10, 13):
                    result.append("enter")
                elif 32 <= first < 127:
                    result.append(chr(first).lower())
                continue
            if len(self.buffer) == 1:
                break
            if self.buffer[1] not in (ord("["), ord("O")):
                del self.buffer[:2]  # Ignore Alt chords, including their command letter.
                continue
            end = next((i for i in range(2, len(self.buffer)) if 64 <= self.buffer[i] <= 126), None)
            if end is None:
                break
            tail = self.buffer[end]
            del self.buffer[:end + 1]
            key = {65: "up", 66: "down", 67: "right", 68: "left"}.get(tail)
            if key:
                result.append(key)
        if self.buffer and now - self.since >= 0.25:
            if self.buffer == b"\x1b":
                result.append("escape")
            self.buffer.clear()
        return result


class Terminal:
    """Nonblocking input and reversible local-terminal setup; no reader thread."""

    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.console = os.name == "nt" and sys.stdin.isatty()
        self.saved = None
        self.windows_mode = None

    def __enter__(self):
        if os.name != "nt" and os.isatty(self.fd):
            import termios
            import tty
            self.saved = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        elif os.name == "nt":
            import ctypes
            import msvcrt
            self.windows_mode = msvcrt.setmode(self.fd, os.O_BINARY)
            self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            self.kernel.PeekNamedPipe.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong,
                                                 ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong), ctypes.c_void_p]
            self.kernel.PeekNamedPipe.restype = ctypes.c_int
            self.handle = msvcrt.get_osfhandle(self.fd)
        self.write("\x1b[0m\x1b[?25l\x1b[2J\x1b[H")
        return self

    def read(self, timeout: float = 0.02) -> bytes | None:
        """None means no key yet; empty bytes means caller disconnected."""
        if os.name != "nt":
            if not select.select([self.fd], [], [], timeout)[0]:
                return None
            return os.read(self.fd, 256)
        if self.console:
            import msvcrt
            until = time.monotonic() + timeout
            while not msvcrt.kbhit():
                if time.monotonic() >= until:
                    return None
                time.sleep(0.005)
            key = msvcrt.getwch()
            if key in ("\x00", "\xe0"):
                key = {"H": "\x1b[A", "P": "\x1b[B", "M": "\x1b[C", "K": "\x1b[D"}.get(msvcrt.getwch(), "")
            return key.encode("utf-8") or None
        import ctypes
        available = ctypes.c_ulong()
        if not self.kernel.PeekNamedPipe(self.handle, None, 0, None, ctypes.byref(available), None):
            error = ctypes.get_last_error()
            if error in (109, 232, 233):
                return b""
            # Redirected regular-file input is useful for smoke scripts.
            if error == 1:
                return os.read(self.fd, 256)
            raise OSError(error, "Cannot poll door stdin")
        if available.value:
            return os.read(self.fd, min(256, available.value))
        time.sleep(timeout)
        return None

    def write(self, text: str):
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.buffer.flush()

    def __exit__(self, *_):
        try:
            self.write("\x1b[0m\x1b[?25h\x1b[2J\x1b[H")
        except OSError:
            pass
        finally:
            if self.saved is not None:
                import termios
                termios.tcsetattr(self.fd, termios.TCSADRAIN, self.saved)
            if self.windows_mode is not None:
                import msvcrt
                msvcrt.setmode(self.fd, self.windows_mode)


@dataclass(frozen=True)
class Pad:
    left: float
    right: float
    height: float
    name: str = "TRANQUILITY"


@dataclass(frozen=True)
class Terrain:
    points: tuple[tuple[float, float], ...]
    pad: Pad

    def height(self, x: float) -> float:
        i = max(0, min(len(self.points) - 2, bisect_right(self.points, (x, math.inf)) - 1))
        a, b = self.points[i:i + 2]
        fraction = max(0.0, min(1.0, (x - a[0]) / (b[0] - a[0])))
        return a[1] + (b[1] - a[1]) * fraction


@dataclass
class Flight:
    terrain: Terrain
    x: float = 300.0
    y: float = 180.0
    vx: float = 0.0
    vy: float = -6.0
    fuel: float = 90.0
    initial_fuel: float = 90.0
    angle: float = 0.0
    throttle: float = 0.0
    elapsed: float = 0.0
    status: str = "flying"
    reason: str = ""

    def command(self, key: str):
        if key in ("a", "left"):
            self.angle = max(-60.0, self.angle - 10)
        elif key in ("d", "right"):
            self.angle = min(60.0, self.angle + 10)
        elif key in ("w", "up"):
            self.throttle = min(1.0, round(self.throttle + 0.1, 2))
        elif key in ("s", "down"):
            self.throttle = max(0.0, round(self.throttle - 0.1, 2))
        elif key in "0123456789" and len(key) == 1:
            self.throttle = int(key) / 9
        elif key == " ":
            self.throttle = 0.0
        elif key == "x":
            self.angle = 0.0

    def feet(self) -> tuple[tuple[float, float], ...]:
        a = math.radians(self.angle)
        return tuple((self.x + side * 3 * math.cos(a) + 3 * math.sin(a),
                      self.y + side * 3 * math.sin(a) - 3 * math.cos(a)) for side in (-1, 1))

    def contact(self) -> bool:
        feet = self.feet()
        # Include the body and the span between the feet, not just the center.
        samples = (*feet, ((feet[0][0] + feet[1][0]) / 2, (feet[0][1] + feet[1][1]) / 2), (self.x, self.y))
        if all(y > self.terrain.height(x) for x, y in samples):
            return False
        pad = self.terrain.pad
        if not all(pad.left <= x <= pad.right for x, _ in feet):
            reason = "Terrain strike: put both landing feet inside the lit pad."
        elif abs(self.angle) > 10:
            reason = "Attitude: land within 10 degrees of upright."
        elif abs(self.vx) > 2:
            reason = "Sideways drift: reduce horizontal speed to 2 m/s or less."
        elif abs(self.vy) > 3:
            reason = "Hard impact: reduce vertical speed to 3 m/s or less."
        else:
            self.status = "landed"
            self.reason = "Contact light. Engine stop. Welcome to the Moon."
            return True
        self.status, self.reason = "crashed", reason
        return True

    def step(self, dt: float = DT):
        if not 0 < dt <= 0.1:
            raise ValueError("flight steps must be in (0, 0.1] seconds")
        if self.status != "flying" or self.contact():
            return
        # Limit travel to a quarter metre per collision check, including fast falls.
        steps = max(1, math.ceil((math.hypot(self.vx, self.vy) + 10) * dt / 0.25))
        h = dt / steps
        for _ in range(steps):
            burn = min(self.fuel, FUEL_FLOW * self.throttle * h)
            power = burn / (FUEL_FLOW * h)
            acceleration = MAX_THRUST * power / (DRY_MASS + self.fuel - burn / 2)
            a = math.radians(self.angle)
            ax, ay = acceleration * math.sin(a), acceleration * math.cos(a) - GRAVITY
            self.x += self.vx * h + ax * h * h / 2
            self.y += self.vy * h + ay * h * h / 2
            self.vx += ax * h
            self.vy += ay * h
            self.fuel -= burn
            self.elapsed += h
            if self.x < 3 or self.x > 997 or self.y > 800:
                self.status, self.reason = "crashed", "Flight corridor exceeded. Stay within 0-1000 m and below 800 m."
                return
            if self.contact():
                return

    def score(self, difficulty: int = 1) -> int:
        if self.status != "landed":
            return 0
        precision = max(0, 1 - abs(self.vy) / 3) + max(0, 1 - abs(self.vx) / 2)
        return round(difficulty * (1000 + 500 * self.fuel / self.initial_fuel + 250 * precision))


def training() -> Flight:
    pad = Pad(250, 350, 25)
    return Flight(Terrain(((0, 80), (100, 45), (180, 70), (250, 25), (350, 25),
                           (450, 75), (600, 120), (750, 60), (900, 100), (1000, 80)), pad))


def run(host: Host, started: float) -> int:
    """Foundation screen. The next slice supplies the flight cockpit."""
    stopped = False
    previous = {}

    def stop(*_):
        nonlocal stopped
        stopped = True

    def resize(*_):
        pass  # Metadata polling below coalesces host signals.

    for name, handler in (("SIGTERM", stop), ("SIGINT", stop), ("SIGUSR1", resize)):
        if hasattr(signal, name):
            sig = getattr(signal, name)
            previous[sig] = signal.signal(sig, handler)
    keys = Keys()
    deadline = None if host.limit is None else started + max(0, host.limit - 0.25)
    last_size = None
    next_check = 0.0
    try:
        with Terminal() as terminal:
            while not stopped:
                now = time.monotonic()
                if deadline is not None and now >= deadline:
                    break
                if now >= next_check:
                    host = Host.load(host.path)
                    next_check = now + 0.5
                size = (host.width, host.height)
                if size != last_size:
                    message = "LUNAR LANDER | Flight systems ready. Q: return to NetBBS"
                    if host.width < 80 or host.height < 24:
                        message = "Resize to 80x24. Q: exit"
                    terminal.write("\x1b[2J\x1b[H" + plain(message, max(0, host.width - 1)))
                    last_size = size
                data = terminal.read()
                if data == b"":
                    break
                if "q" in keys.feed(data or b"", now):
                    break
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    return 0


def main() -> int:
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    parser.parse_args()
    try:
        return run(Host.load(os.environ.get("NETBBS_DOOR_INFO")), started)
    except (BrokenPipeError, ConnectionResetError):
        # Prevent interpreter shutdown from retrying a buffered broken stdout.
        sys.stdout = open(os.devnull, "w")
        return 0
    except (DoorError, OSError) as exc:
        print("Lunar Lander: " + plain(str(exc), 200), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
