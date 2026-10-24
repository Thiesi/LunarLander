"""Opt-in acceptance through an installed NetBBS runtime, with disposable state.

Uses real host profiles, processes, streams and terminal emulation. This is not
a Telnet/SSH/browser client test or a human playtest. No production node is used.
"""
import argparse
import asyncio
import codecs
import json
import os
from pathlib import Path
import sys
import tempfile

import netbbs
from netbbs.auth.users import create_user
from netbbs.doors.profiles import DoorProfile
from netbbs.doors.registry import create_door
from netbbs.doors.runtime import run_door
from netbbs.net.session import Session, SessionClosedError
from netbbs.rendering.terminal_emulator import TerminalEmulator
from netbbs.storage.database import Database
from netbbs.storage.execution import DatabaseLane

ROOT = Path(__file__).resolve().parents[1]


class Caller(Session):
    node_display_name = "Lunar Lander acceptance"
    transport_name = "local"

    def __init__(self, width, height):
        self.terminal_width, self.terminal_height = width, height
        self.queue = asyncio.Queue()
        self.decoder = codecs.getincrementaldecoder("utf-8")()
        self.screen = TerminalEmulator(width, height)
        self.output = bytearray()

    async def read_byte(self):
        value = await self.queue.get()
        if value is None:
            raise SessionClosedError("acceptance caller disconnected")
        return value

    async def write_raw(self, data):
        self.output.extend(data)
        del self.output[:-2_000_000]
        self.screen.feed(self.decoder.decode(data))

    async def write(self, text):
        await self.write_raw(text.encode("utf-8"))

    async def read_line(self, **kwargs):
        raise NotImplementedError

    async def read_key(self, **kwargs):
        raise NotImplementedError

    async def read_editor_key(self, **kwargs):
        raise NotImplementedError

    async def close(self):
        self.queue.put_nowait(None)

    def send(self, text):
        for byte in text.encode():
            self.queue.put_nowait(byte)

    def resize(self, width, height):
        self.terminal_width, self.terminal_height = width, height
        self.screen.resize(width, height)

    async def drawing(self, task, seconds=8):
        """Until the door has drawn its first frame."""
        async with asyncio.timeout(seconds):
            while b"[" not in self.output:
                if task.done():
                    raise AssertionError(f"Door ended before drawing: {task.result()}")
                await asyncio.sleep(.02)

    async def until(self, text, task, seconds=8):
        async with asyncio.timeout(seconds):
            while text not in "\n".join(self.screen.text_rows()):
                if task.done():
                    raise AssertionError(f"Door ended before {text!r}: {task.result()}")
                await asyncio.sleep(.02)


async def check(root, captures, width, height, scenario):
    with tempfile.TemporaryDirectory(prefix="node-", dir=root) as directory:
        directory = Path(directory)
        db = Database(directory / "netbbs.db")
        lane = DatabaseLane(db.path)
        tasks = []
        try:
            player = create_user(db, "MoonPilot", password="acceptance-only", user_level=255)
            value = json.loads((ROOT / "profiles/netbbs.json").read_text())
            value["profile"].update(install_dir=str(ROOT),
                                    environment={"DOOR_LL_DATA_DIR": str(directory / "records")})
            profile = DoorProfile.from_json(json.dumps(value["profile"]))
            door = create_door(db, "Lunar Lander acceptance", sys.executable,
                               args=tuple(value["args"]), creator=player, profile=profile)
            caller = Caller(width, height)
            limit = 3 if scenario == "deadline" else 30
            task = asyncio.create_task(run_door(caller, lane, door, player, wall_time_limit_seconds=limit))
            tasks.append(task)
            # The splash's title is pixel art; its caption is the first text on screen.
            await caller.drawing(task)
            if scenario not in ("deadline", "disconnect"):
                await caller.until("PRECISION FLYING", task)
            if scenario == "deadline":
                result = await asyncio.wait_for(task, 6)
                assert result.reason == "exited", result
            elif scenario == "disconnect":
                await caller.close()
                result = await asyncio.wait_for(task, 8)
                assert result.reason == "caller_disconnected", result
            else:
                # A real caller can skip the intro and ignition without leaking
                # those keys into the menu or flight controls.
                caller.send(" ")
                await caller.until("FLIGHT DIRECTOR", task)
                caller.send("\r")
                await asyncio.sleep(.15)
                caller.send(" ")
                await asyncio.sleep(.3)
                caller.send("p")
                await caller.until("FLIGHT PAUSED", task)
                caller.send("?")
                await caller.until("FLIGHT MANUAL", task)
                caller.send("?")
                await caller.until("FLIGHT PAUSED", task)
                caller.send("p")
                await asyncio.sleep(.2)
                captures.mkdir(parents=True, exist_ok=True)
                (captures / f"native-{width}x{height}.ans").write_text(caller.screen.restore_ansi(), encoding="utf-8")
                if scenario == "crash":
                    await caller.until("LANDER DOWN", task, seconds=20)
                    caller.send("r")
                    await asyncio.sleep(.3)
                    assert "LANDER DOWN" not in "\n".join(caller.screen.text_rows())
                elif scenario == "resize":
                    caller.resize(70, 20)
                    await caller.until("Resize to 80x24", task)
                    caller.resize(132, 50)
                    await caller.until("ALTITUDE", task)
                    assert len(caller.screen.text_rows()) == 50
                elif scenario == "concurrent":
                    others = []
                    for n in range(1, profile.max_sessions):
                        other_player = create_user(db, f"MoonPilot{n}", password="acceptance-only", user_level=255)
                        second = Caller(width, height)
                        other = asyncio.create_task(run_door(second, lane, door, other_player, wall_time_limit_seconds=20))
                        tasks.append(other)
                        others.append((second, other))
                    # The splash holds until a key, as the other native doors' do.
                    await asyncio.gather(*(session.until("PRECISION FLYING", child) for session, child in others))
                    for session, _ in others:
                        session.send(" ")
                    await asyncio.gather(*(session.until("FLIGHT DIRECTOR", child) for session, child in others))
                    for session, _ in others:
                        session.send("q")
                    results = await asyncio.wait_for(asyncio.gather(*(child for _, child in others)), 8)
                    assert all(r.reason == "exited" for r in results), results
                    print(f"PASS {profile.max_sessions} distinct simultaneous callers", flush=True)
                caller.send("q")
                result = await asyncio.wait_for(task, 8)
                assert result.reason == "exited" and result.exit_code == 0, result
                assert b"\x1b[?25h" in caller.output
            assert not result.diagnostic, result.diagnostic
            assert not caller.door_active
            print(f"PASS {scenario} {width}x{height}: {result.reason}, exit={result.exit_code}", flush=True)
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            lane.close()
            db.close()


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".task" / "native-acceptance")
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    # Keep NetBBS's temporary launch files inside the disposable test area too.
    previous_temp = tempfile.tempdir
    tempfile.tempdir = str(args.output)
    try:
        print(f"NetBBS {netbbs.__version__}; Python {sys.version.split()[0]}; platform {sys.platform}", flush=True)
        for width, height, scenario in ((80, 24, "play"), (132, 50, "play"),
                                       (80, 24, "crash"), (80, 24, "deadline"),
                                       (80, 24, "disconnect"), (132, 50, "concurrent")):
            await check(args.output, args.output, width, height, scenario)
        if os.name == "posix":
            await check(args.output, args.output, 80, 24, "resize")
        else:
            print("NOT RUN: native resize forwarding is POSIX-only in NetBBS.", flush=True)
    finally:
        tempfile.tempdir = previous_temp


if __name__ == "__main__":
    asyncio.run(main())
