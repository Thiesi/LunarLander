![Lunar Lander: a gold spacecraft descends toward a cyan-lit landing pad beneath an indigo sky and a distant Earth](assets/lunar-lander-social.jpg)

# Lunar Lander

A real-time, single-player lunar landing door game for BBSes. Guide a fragile
lander between lunar ridges and settle it onto a lit pad on a dwindling tank:
fifteen ranked missions in three chapters, three daily challenges, medals for every
safe landing, 52 achievements, a career from Cadet to Lunar Ace, and Programs:
practise in the simulator, then fly each mission for real exactly once. Read the
drift. Watch the fuel. Make both feet count.

Lunar Lander is **one Python file** (`lunar_lander.py`) with no dependencies
beyond the standard library. It needs Python 3.11 or newer and a terminal of at
least 80×24: a flight simulator needs the room, so unlike the other bundled
games it does not go down to 40×12, and below 80×24 it pauses the flight and
asks for a bigger window. Pilot records are one SQLite file the door manages
itself.

![Lunar Lander's 80x24 cockpit, rendered by the game](docs/images/cockpit-80x24.png)

## Where it runs

- **NetBBS:** bundled since NetBBS v7.41.0. NetBBS ships a tagged release of
  this file, so a NetBBS SysOp has nothing to install.
- **Other BBS software** (Synchronet, Mystic, ENiGMA½, …): reads DOOR32.SYS and
  DOOR.SYS, with CP437 or UTF-8 output and stdio or an inherited DOOR32 socket.
  It needs an ANSI terminal; see [Classic BBS setup](#classic-bbs-setup).
  Real-host validation is still pending (#13).
- **Standalone**, for trying it out: `python3 lunar_lander.py`. Local flights
  are practice; no records are kept.

## The game

- **Missions:** a training basin and fifteen ranked missions in three chapters
  (Maria, Highlands, Frontier), plus three daily challenges, new at the node's
  local midnight: one in the manner of each chapter, from a broad sea to a lean
  frontier run. At weekends the Frontier daily is a **hop**: land on one pad,
  lift off, and land on a second one further along.
- **Medals and ranks:** gold, silver and bronze for every safe landing, and a
  career from Cadet to Lunar Ace, with a medal ceremony and promotion fireworks.
- **Programs:** a season's five to eight missions, the same for every pilot on
  the node for a month, climbing from a broad sea to the frontier. Fly each in
  the simulator as the preset allows, then for real exactly once, from a
  slightly different start: **Cadet** (any number of simulator runs; a crash
  loses that mission), **Astronaut** (one run per mission; a crash ends the
  program) or **Test Pilot** (no simulator; a crash ends it). Each preset has
  its own board, and leaving or losing the connection mid-flight counts as a crash.
- **Achievements:** 52 of them, from milestones and precision touchdowns to
  close calls, hops, career feats, Programs and ten hidden ones. The **Pilot
  Record** ([P] in the flight director) shows the career, flight totals and
  personal records on one tab and the achievements, with how many of the node's
  pilots hold each, on the other.
- **Flight:** deterministic lunar physics; a landing needs both feet on the pad,
  a vertical speed of 3 m/s or less, a drift of 2 m/s or less and a tilt of 10°
  or less. Fuel alerts appear over the view at 30 and 10 seconds of hover fuel.
- **Radio:** CAPCOM calls the fuel down as each alert begins, reads out height,
  sink and drift every few seconds below 60 m, and has a word for how it ended
  in the debrief, a first gold on a mission naming its base.
- **Ghosts:** fly beside a faint outline of your own best run on a mission, or
  the node record holder's (**[G]** in the briefing chooses), and compare time
  and fuel in the debrief. **[W]** on a leaderboard replays the leader's landing.
- **Rivals:** when another pilot passes one of your bests while you're away, the
  mission is marked ▼ in the flight director and its briefing says who and by
  how much; **[G]** can then put their run beside you.
- **Descent trace:** the debrief draws altitude over the burn, so you can see
  where the fuel went, and says so when most of it went early.
- **Presentation:** scenery in quadrant blocks, two pixels across each cell, with
  stars, a distant Earth and parallax ranges; a title splash with a rotating
  tagline; and skippable ignition, touchdown and crash scenes. Truecolor, 256-
  and 16-color terminals, with Unicode or ASCII glyphs. There is more scenery at
  132×50.
- **Records:** each pilot's best landing per mission, on per-mission
  leaderboards, for up to eight callers flying at once.

The [132×50 cockpit](docs/images/cockpit-132x50.png), the
[splash](docs/images/splash.gif), the [flight director](docs/images/menu-80x24.png),
the [medal ceremony](docs/images/medal.gif) and the [promotion](docs/images/promotion.gif)
are captured from the game's own renderer.

## Records

Records live in `pilots.db` in the directory named by `DOOR_LL_DATA_DIR`. A
bundled Lunar Lander keeps them in `<db>.doors/lunar_lander/`, next to
Voidrunner's saves and War Dialer's worlds, and NetBBS's backups include them.
If a profile points `DOOR_LL_DATA_DIR` elsewhere, the records there are not
backed up by NetBBS; back them up with SQLite's backup API, as
[OPERATIONS](docs/operations.md#records-backups-and-upgrades) describes.

Records are keyed by the node, the caller's numeric account and the mission, so
a handle rename keeps a pilot's records. Beside each pilot's bests they keep
running counters (landings, crashes, time in the air, simulator time, personal
records) and achievements. Guests fly practice only, and keep counters and
achievements for the session. Flights are not saved mid-air; a landing is
committed before its debrief appears.

## SysOp setup

On NetBBS v7.41.0 or later, **Content ▸ Doors ▸ <kbd>G</kbd> Gallery** lists
Lunar Lander with the other bundled games. Registered from there, it gets a
900-second CPU allowance, which its continuously rendered flight needs for a
long session, instead of the usual 300.

To run a newer release than the bundled copy, register it by hand: download
`lunar_lander.py`, `netbbs.json`, `LICENSE` and `SHA256SUMS` from one tagged
release, verify the checksums and import `netbbs.json` through NetBBS's door
setup, adjusting its paths. Keep `cpu_seconds` at 900. The
[installation guide](docs/operations.md#native-netbbs-installation) covers each
step.

These settings go in the door profile's environment:

| Variable | Effect |
| --- | --- |
| `DOOR_LL_DATA_DIR` | Where `pilots.db` lives. Use an absolute, writable directory. |
| `DOOR_LL_PIXELS=half` | Draw with half blocks instead of quadrant blocks for every caller, for terminal fonts without quadrants (`▖▗▘▝`). On NetBBS 7.43.0 or later, callers choose this themselves (Profile ▸ Quarter blocks). |
| `DOOR_SPLASH=0` or `DOOR_LL_SPLASH=0` | Skip the title splash. `DOOR_SPLASH` is shared with the other native doors. |
| `DOOR_LL_SCENES=0` | Skip the ignition, touchdown and crash scenes. |
| `DOOR_LL_DATE_FORMAT` | How the daily challenges show their date, for example `%d/%m/%Y`. Without it, the date follows the node's own format (NetBBS 7.41.0 or later), or ISO `%Y-%m-%d`. |

## Classic BBS setup

Install Python 3.11+, copy `lunar_lander.py` to a door directory and pass the
caller's drop-file **filename**, quoted if it contains spaces:

```sh
python3 /opt/doors/lunarlander/lunar_lander.py /path/to/node/DOOR32.SYS
```

`DOOR.SYS` works too. Names are matched without case, renamed files are
recognised by their contents, and CRLF or LF endings are accepted. A malformed
drop file stops the launch with a message on stderr, never naming the file.
`NETBBS_DOOR_INFO`, when set, takes precedence.

- **Records:** keyed by the caller's record number, so an alias change keeps a
  pilot's records. Give each BBS its own `DOOR_LL_DATA_DIR`, shared by all its
  nodes: different BBSes' record numbers overlap. A shared guest account is one
  pilot; keep guests out, or accept that they share one record.
- **Display:** 80 columns, with DOOR.SYS's page length or 24 rows; no live
  resize. 16 colours unless `--color 256` or `--color truecolor`. CP437 output,
  in half blocks, unless `--encoding utf-8`; match the host's bridge encoding to
  it. A caller without ANSI (DOOR32 emulation 0, DOOR.SYS `NG` or `7E`) is told
  the game needs an ANSI terminal and returned to the BBS.
- **Time:** the drop file's minutes left; the door warns in the last minute and
  returns before the host's cutoff.
- **DOOR32 socket:** with communication type `2`, the door uses the inherited
  socket handle (Winsock on Windows, a descriptor on POSIX). It filters telnet
  commands, doubles outgoing 0xFF and takes CR NUL or CR LF as one Enter.
  Returning closes only its own handle. Configure the host to pass the caller's
  connected socket to the Python process (DOOR32 line 1 `2`, line 2 the
  handle); copying a drop file alone does not pass it. This is the path for
  Synchronet on Windows.

A Unix launcher at `/opt/doors/lunarlander/launch.sh` can set the environment:

```sh
#!/bin/sh
export DOOR_LL_DATA_DIR=/var/lib/lunarlander
export DOOR_LL_BBS_NAME="Moonbase BBS"
export DOOR_LL_TIMEZONE=Europe/Berlin
exec /usr/bin/python3 /opt/doors/lunarlander/lunar_lander.py "$1"
```

These recipes await the real-host checks in #13:

| Host | Stdio launch configuration |
| --- | --- |
| Synchronet on Linux | In SCFG's Online Programs, select Native Executable, Standard I/O, DOOR32.SYS (or DOOR.SYS), and drop files in the Node Directory. Command line: `/opt/doors/lunarlander/launch.sh "%f"`. |
| Mystic on Linux/macOS | Use the `DD` external-program menu command with `/opt/doors/lunarlander/launch.sh "%PDOOR32.SYS"`. `%P` includes the trailing slash. |
| ENiGMA½ | Use the `abracadabra` menu module with the configuration below. |

```hjson
config: {
    name: Lunar Lander
    dropFileType: DOOR32
    cmd: /usr/bin/python3
    args: [ "/opt/doors/lunarlander/lunar_lander.py", "{dropFilePath}" ]
    io: stdio
    encoding: cp437
    env: { DOOR_LL_DATA_DIR: "/var/lib/lunarlander" }
}
```

Settings for classic hosts, beside those above:

| Setting | Effect |
| --- | --- |
| `DOOR_LL_NODE_ID` | Names this BBS in the records (default `classic`). Keep it once set. |
| `DOOR_LL_BBS_NAME` | The name in "[Q] Return to …" (default "BBS"). |
| `DOOR_LL_TIMEZONE` | The IANA zone whose midnight starts new daily challenges (default UTC). |
| `--encoding auto\|utf-8\|cp437` | Output bytes: CP437 with a drop file unless set. |
| `--color 16\|256\|truecolor` | The caller's colour depth (default 16). |

Game events and `!top` are NetBBS features; a classic host gets neither.

Host references: [Synchronet DOOR.SYS](https://wiki.synchro.net/ref:door.sys),
[Mystic external programs](https://wiki.mysticbbs.com/doku.php?id=menu_commands),
[ENiGMA½ scripts and native binaries](https://enigma-bbs.github.io/doors/scripts-and-binaries/).

## NetBBS game events

Under NetBBS `door_api` 5 with game events switched on for this door
(`outbound.events` in `door_info.json`), Lunar Lander reports what ranked pilots
earn live. NetBBS's bot then announces it in chat and answers `!top` with the
career standings:

| Event | When |
| --- | --- |
| `rank` | A landing promotes the pilot to a new rank |
| `achievement` | A pilot's first gold medal on a mission ("Gold landing: Tranquility"), a silver or gold achievement ("Feather"), or a completed program ("Program complete: Astronaut, 6 of 6, 31,200 points") |
| `season` | The node's first program of a new season ("7 missions, through November"); sent only to a NetBBS that lists `season` among its event types |
| standings | The node's Career Roster by medal points, at launch and after a landing, when the order has changed |

Nothing earned offline or in an earlier session is reported. Without
`outbound.events` (standalone play, a classic BBS, or events switched off), the
door writes nothing.

## Development

```sh
python -m pip install tzdata                    # Windows: named-timezone tests
python -m unittest discover -s tests -v         # the suite
python scripts/netbbs_smoke.py                  # the real NetBBS runtime; needs NetBBS installed
python scripts/capture.py --output .task/flight.png   # a frame as ANSI and PNG (needs Pillow)
```

A change to a screen comes with captures: the tests can prove that a screen
fits, never that it looks right. `scripts/capture.py` takes `--width`,
`--height`, `--color`, `--ascii`, `--pixels` and `--mode` (menu, help, a scene,
or `--gif` for an animation). The game's design is in
[docs/design.md](docs/design.md), and the acceptance evidence and remaining
field checks are in [docs/acceptance.md](docs/acceptance.md).

## Releases

Releases are tagged by hand once CI passes on the release commit.
`scripts/package_release.py`, run in a clean LF checkout, collects
`lunar_lander.py`, `netbbs.json`, `LICENSE`, `OPERATIONS.md` and `ACCEPTANCE.md`
with a `SHA256SUMS` file for the GitHub release. NetBBS vendors these releases.

Every release's notes carry a **NetBBS** line saying whether the saved data
changed, so a SysOp knows whether it can run ahead of the copy NetBBS bundles:
"saved data unchanged; runs on NetBBS 7.41.0 or later", or "changes the save
format; wait for the NetBBS release that bundles it". The format NetBBS's
backups check is the records database, application ID `0x4C4C0001`:

| Schema (`user_version`) | Tables | Releases |
| --- | --- | --- |
| 1 | `pilots`, `scores` | up to v0.4.x |
| 2 | `pilots`, `scores`, `counters`, `achievements`, `programs`, `program_missions` | v0.5.x |
| 3 | schema 2's, plus `ghosts`, `tours` | from the ghosts release |

An older file upgrades to the current schema in place on its first open, keeping
every record; the upgrade only adds tables. NetBBS accepts schema 2 from the
release that resolves [NetBBS #1561](https://github.com/Thiesi/NetBBS/issues/1561),
and schema 3 from the one that resolves
[NetBBS #1577](https://github.com/Thiesi/NetBBS/issues/1577).

The banner is concept art rather than a game screen, and doubles as the
repository's social preview; the [artwork notes](assets/README.md) explain how
it was made and set.

## License

BSD 2-Clause, see [LICENSE](LICENSE).
