# Playing and installing Lunar Lander

## Play locally

Use Python 3.11 or newer in an ANSI terminal at least 80 columns by 24 rows:

```sh
python lunar_lander.py
```

No packages are required. Local play has no NetBBS account and is unranked.
Choose a mission with 1–5, then Enter. A/D or left/right tilt; W/S or up/down
adjust throttle. The setting stays put when you release the key. Digits select
power from 0 (off) to 9 (full); Space cuts thrust and X levels the craft.
P pauses; ? opens the manual; Q returns to the BBS.

Start with training. Burn early, tilt against lateral drift, then straighten out
over the cyan pad. At contact, both feet must be inside the pad, vertical speed
must be at most 3 m/s, horizontal speed at most 2 m/s, and tilt at most 10 degrees.
The displayed craft is an enlarged navigation symbol; numeric altitude and the
pad lights are the precise references. The camera scale changes near the surface.

Tranquility, Ridge Run and The Needle increase drift and landing difficulty.
The daily challenge is selected by UTC date when the door starts; the mission and
date remain fixed for that session. Only completed safe landings rank. Training,
aborted flights and crashes never replace a record. The formula is in the manual:
difficulty times base landing points, fuel reserve and landing precision. One best
score per pilot per mission; equal scores keep the earlier achieved result.

## Native NetBBS installation

1. Download `lunar_lander.py`, `netbbs.json`, `LICENSE` and `SHA256SUMS` from the
   same tagged release. Verify the checksums before installation. Candidate
   releases are for testing; their release notes list outstanding acceptance.
2. Put the script and license in a persistent directory, for example
   `/var/games/netbbs/lunar-lander`. Use an installed Python 3.11+ interpreter.
3. Import `netbbs.json` through NetBBS's door Compatibility setup. Replace
   `executable_path`, `profile.install_dir` and `DOOR_LL_DATA_DIR` with absolute
   paths on that host. The shipped POSIX paths are examples for a NetBSD or Linux
   service installation; adjust them to your interpreter and game directory.
4. Give the BBS service account read access to the script and write access to the
   chosen data directory. Keep the entry SysOp-only until Test as SysOp and real
   caller transport checks pass. Do not enable outbound posting; LL does not use it.
5. Keep UTF-8 encoding and native stdio. The profile follows caller size (0x0),
   opts into resize signals, and starts with one caller allowed. LL supports
   transactional simultaneous callers; raise `max_sessions` and set
   `multinode_certified: true` only after your two-caller check.

NetBBS supplies the path in `NETBBS_DOOR_INFO`; never place that file beside the
game manually in a real installation. LL accepts API versions 2–5 and ignores
unknown additive fields. Missing optional capabilities use conservative defaults.
Unsupported versions or malformed supplied metadata fail with a diagnostic.
Missing node/account identity permits practice but does not create pilot records.
For a custom registration, restrict anonymous guests: a host may give all guests
the same account identity. LL cannot infer guest privileges from the public API.

256 colors are the default local presentation; NetBBS callers get their published
16/256/truecolor palette and Unicode preference. ASCII glyph mode still requires
ANSI cursor addressing. Plain non-ANSI terminals and classic DOS/DOOR32 launching
are not supported in this release.

NetBBS forwards size changes via republished JSON and SIGUSR1. LL also
polls metadata to coalesce notifications.
Resizing below 80x24 pauses the simulation wherever the host publishes the change.
Pause/help/resize do not extend the host's session time; LL warns in the last minute
and exits just before the published deadline. Disconnect forfeits the active flight.

## Records, backups and upgrades

The database is `pilots.db` under `DOOR_LL_DATA_DIR`, or under `data` next to the
script if no override is configured. Always set an explicit writable directory in
the profile; an installed package directory may be read-only. NetBBS forwards
profile `DOOR_*` variables, not arbitrary process environment variables.

Records use the opaque node ID, stable numeric account ID and mission ID. A handle
rename updates the displayed name on the next leaderboard read or saved landing.
Separate nodes cannot read each other's scores even if they share a directory.
Prefer separate directories anyway. Active flights have no resumable save; a result
is committed before the debrief appears. Simultaneous sessions retain the best score.

Schema 1 has application ID `0x4C4C0001`. A newer, incomplete, unrelated or corrupt
database is refused and preserved. LL says records are unavailable, offers unranked
play and writes a bounded stderr diagnostic for NetBBS's door-session history.
A write failure on touchdown clearly says the landing was not saved.

These records are **not automatically included in NetBBS's bundled-door backups**.
Before upgrades, close admission, let callers return and back up `pilots.db` with
SQLite's backup API. This also works for a consistent snapshot while readers exist:

```python
import sqlite3
with sqlite3.connect('/absolute/data/pilots.db') as source:
    with sqlite3.connect('/absolute/backups/pilots-before-upgrade.db') as target:
        source.backup(target)
        assert target.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
```

Verify the source exists first; SQLite creates absent paths. Store the backup outside
the installation and preserve the owning NetBBS node database alongside it. To
restore, stop game sessions, preserve the current database and any journal sidecars,
validate the backup, then replace the database with that verified copy. Do not
delete a broken database, clear its schema version, or substitute another node's IDs.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Door cannot start | Check absolute Python/script/install paths and service-account permissions; inspect NetBBS's Last diagnostic |
| Practice only | Confirm node/account metadata and writable `DOOR_LL_DATA_DIR`; read stderr for the precise database failure |
| Garbled blocks/colors | Confirm UTF-8 profile and terminal encoding; select a suitable NetBBS glyph/color preference |
| Flight paused for size | Enlarge to 80x24 |
| Slow link indicator | LL caps physics catch-up to avoid a sudden unseen crash; use a faster terminal connection or smaller window |
| Crash too quickly | Begin braking earlier; use training and the vertical-speed gauge, not just the enlarged ship symbol |

## Development and acceptance

```sh
python -m unittest discover -s tests -v
python scripts/netbbs_smoke.py
```

The second command requires an installed NetBBS and uses disposable nodes/data only.
It launches the real native runtime, checks screen contents through NetBBS's terminal
emulator and retains ANSI captures under `.task/native-acceptance`. CI pins the host
commit and runs Python 3.11 on Linux and Windows. Windows is a development check,
not a production NetBBS deployment target. It does not test a real client.

`scripts/capture.py --output .task/flight.png` exports the game's actual ANSI frame
and a PNG preview (Pillow is a development-only dependency). `--width 132 --height 50`,
`--color 16`, `--ascii` and `--mode menu` select other views.

See [acceptance evidence](acceptance.md) for completed checks and field limits.
