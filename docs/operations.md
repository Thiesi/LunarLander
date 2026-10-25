# Playing and installing Lunar Lander

## Play locally

Use Python 3.11 or newer in an ANSI terminal at least 80 columns by 24 rows:

```sh
python lunar_lander.py
```

No packages are required. Local play has no NetBBS account and is unranked.
In the flight director, up/down (or W/S) choose a mission, left/right (or A/D)
switch chapter, and digits jump to a mission on the tab; Enter launches. In flight,
A/D or left/right tilt; W/S or up/down adjust throttle. The setting stays put when you release the key. Digits select
power from 0 (off) to 9 (full); Space cuts thrust and X levels the craft.
P pauses; ? opens the manual. In the flight director, P opens the Pilot Record:
the career, flight totals and personal records on one tab, achievements on the
other (left/right switch tabs, up/down scroll, P or Esc goes back). Q returns to the BBS, which the screens name using
NetBBS's `node_name` (or "NetBBS" when it is absent). During a flight, or while
paused, Q first asks whether to abandon the attempt; Y leaves and N or Esc carries
on, with the simulation stopped meanwhile. Ctrl-C and Ctrl-D leave at once.

Start with training. Burn early, tilt against lateral drift, then straighten out
over the cyan pad. At contact, both feet must be inside the pad, vertical speed
must be at most 3 m/s, horizontal speed at most 2 m/s, and tilt at most 10 degrees.
The displayed craft is an enlarged navigation symbol; numeric altitude and the
pad lights are the precise references. The camera scale changes near the surface.

Missions are grouped in chapters, all open from the start:

- **Maria**: the training basin, Tranquility, Mare Serenitatis, Copernicus,
  Mare Imbrium and Mare Crisium. Broad pads, gentle drift, a steep entry at the end.
- **Highlands**: Ridge Run, Descartes Uplands, Hadley Rille, The Needle and
  Apennine Front. Rough terrain and narrower pads.
- **Frontier**: Far Side, Polar Approach, Tsiolkovsky, Shackleton Rim and Aitken
  Basin. Fast entries, strong drift and lean tanks; difficulty up to five.
- **Daily**: the day's three challenges, one in the manner of each chapter.
  Every setting of a daily (pad width, start, drift, fuel, sink and terrain) is
  drawn from the span of its chapter's own missions, so the Maria daily is as
  gentle as the Maria missions, the Frontier daily as lean as the Frontier ones. The harder
  half of a chapter's span scores its higher difficulty.

Every safe landing on a ranked mission earns a medal from the pilot's best score
there, per point of the mission's difficulty: bronze for any safe landing, silver
from 1,400 and gold from 1,750. Medals count toward a career rank (gold 3 points,
silver 2, bronze 1): Cadet, Pilot (3), Flight Officer (8), LM Pilot (15),
Commander (23), Mission Commander (32) and Lunar Ace (45, every mission gold).
Medals and ranks are read from the existing best scores, so pilots from earlier
releases keep what they earned and no migration is needed. The dailies show
today's medals but do not count toward rank. Callers without a NetBBS
identity earn medals for the session only.

Ranked flights also count toward 50 achievements: milestones (landings, time in
the air, crashes, simulator time), precision and close-call landings, nine
hidden spectacular crashes, completed Programs, and career feats from bests (chapters landed and gold, the top rank,
all three dailies in a day, daily streaks). Achievements that bests already earn
are awarded quietly the first time a pilot launches this release. The debrief
names what a flight earned; silver and gold ones are announced through NetBBS
game events when those are on. The training basin counts as simulator time, not
as ranked flying.

**Programs** (the PROGRAM tab) need a pilot record. A season is the node-local
month: everyone flies the same five to eight missions, generated like the
dailies and climbing from the Maria to the Frontier span, and a new month brings
new ones; a program already under way keeps its season. [N] starts a program
with a preset: Cadet (any number of simulator runs; a crash loses that mission
and the program goes on), Astronaut (one simulator run per mission; a crash
ends the program) or Test Pilot (no simulator; a crash ends it). On the next
mission, [S] flies the simulator and [Enter] the real flight, after a
confirmation. The real flight keeps the simulator's terrain and pad but starts
a little differently (drift within 15%, start within 10 m, up to 3 kg less fuel,
sink within 0.5 m/s), drawn at launch. The attempt is recorded before it
launches, so leaving or losing the connection mid-flight counts as a crash.
Program flights count toward landings, crashes and achievements but never
toward bests, medals or rank. [B] shows the season's board per preset: each
pilot's best program by missions landed, then points (Cadet's also shows
missions lost). A completed program is announced as an `achievement` game
event; the node's first program of a season as a `season` event, but only to a
NetBBS that lists that type.
The dailies change at midnight in the node's published IANA timezone,
including daylight-saving transitions. Everyone gets the same three flights for
a given calendar date, on every node; each has its own leaderboard for the day. An active
flight keeps its original date and leaderboard, even past midnight. Returning to
the briefing or retrying picks up the new day. Only completed safe landings rank. Training,
aborted flights and crashes never replace a record. The formula is in the manual:
difficulty times base landing points, fuel reserve and landing precision. One best
score per pilot per mission; equal scores keep the earlier achieved result.

## Native NetBBS installation

On NetBBS v7.41.0 or later, Lunar Lander is bundled: **Content ▸ Doors ▸
<kbd>G</kbd> Gallery** lists it with the other bundled games, and registering it
from there is all the installation it needs. The bundled registration gets the
900-second CPU allowance and keeps records in `<db>.doors/lunar_lander/`, where
the node's backups include them. NetBBS updates the bundled copy with its own
releases, which may trail this repository's.

To run a release newer than the bundled copy, or on an older NetBBS, register it
by hand. NetBBS's door guide covers this in
[Running a newer game release](https://github.com/Thiesi/NetBBS/blob/main/docs/NetBBS-door-guide.md#running-a-newer-game-release).
First read the release's **NetBBS** line in its notes: run it ahead of the bundled
copy only when it says the saved data is unchanged, since NetBBS's backups check
the records database (application ID `0x4C4C0001`; its schema and tables are in
the README's Releases section). If it says the format changed, wait for the
NetBBS release that bundles it: an older NetBBS's backups refuse the new format.

1. Download `lunar_lander.py`, `netbbs.json`, `LICENSE` and `SHA256SUMS` from the
   same tagged release. Verify the checksums before installation. Candidate
   (`-rc`) releases are for testing; ACCEPTANCE.md lists the checks still open.
2. Put the script and license in a persistent directory, for example
   `/var/games/netbbs/lunar-lander`. Use an installed Python 3.11+ interpreter.
3. Import `netbbs.json` through NetBBS's door Compatibility setup. Replace
   `executable_path`, `profile.install_dir` and `DOOR_LL_DATA_DIR` with absolute
   paths on that host. The shipped POSIX paths are examples for a NetBSD or Linux
   service installation; adjust them to your interpreter and game directory.
   Point `DOOR_LL_DATA_DIR` at the node's own records, `<database>.doors/lunar_lander`
   (the example assumes the database `/srv/bbs/netbbs.db`): the hand-installed
   release then flies on the bundled copy's records, node backups include them,
   and returning to the bundled copy later moves nothing. A copy NetBBS did not
   install plays every guest under the shared guest account, so keep its minimum
   play level above your guest level, and raise the bundled entry to SysOp so
   callers see one copy.
4. Give the BBS service account read access to the script and write access to the
   chosen data directory. Keep the entry SysOp-only until Test as SysOp and real
   caller transport checks pass. LL never posts to boards or chat. To have a chat
   bot announce promotions and first gold medals, and to answer `!top` with the
   node's career standings, enable the door's outbound hook and switch game events
   on (NetBBS door API 5). Only ranked pilots' live, saved results are reported.
5. Keep UTF-8 encoding and native stdio. The profile follows caller size (0x0),
   opts into resize signals, and allows eight simultaneous callers with
   `max_sessions: 8` and `multinode_certified: true`. Existing installations must
   update these two profile settings themselves; replacing the script does not
   update a registered door. Callers fly independently and compete on shared
   leaderboards; this is not a shared spacecraft or a head-to-head flight.
6. Allow `cpu_seconds: 900` (the shipped profile; it was 300 before rc.4). LL
   renders continuously, which NetBBS's door guide notes can exhaust the 300
   CPU-second default in a long session. NetBBS enforces the ceiling with SIGKILL;
   LL watches its own use, warns like the session deadline and exits cleanly
   before reaching it. Existing registrations must raise this setting themselves.

NetBBS supplies the path in `NETBBS_DOOR_INFO`; never place that file beside the
game manually in a real installation. LL accepts API versions 2–5 and ignores
unknown additive fields. Missing optional capabilities use conservative defaults.
Unsupported versions or malformed supplied metadata fail with a diagnostic.
Missing node/account identity permits practice but does not create pilot records.
For a custom registration, restrict anonymous guests: a host may give all guests
the same account identity. LL cannot infer guest privileges from the public API.

256 colors are the default local presentation; NetBBS callers get their published
16/256/truecolor palette and Unicode preference. Unicode callers see the scenery
in quadrant blocks (`▖▗▘▝▚▞` and kin), two pixels across each cell. Almost every
current terminal font draws them, as does the NetBBS web terminal; for one that
does not, set `DOOR_LL_PIXELS=half` in the profile environment to draw with half
blocks only, as releases up to v0.1.0 did.

CP437 terminals such as SyncTERM have half blocks but no quadrants. When NetBBS
tells the door the caller's character set (`charset` in the door metadata,
[NetBBS #1557](https://github.com/Thiesi/NetBBS/issues/1557)), CP437 callers get
half blocks and ASCII callers ASCII glyphs automatically. A NetBBS that does not
send it converts quadrants for a CP437 caller to `?`; on such a node, if callers
use CP437 terminals, set `DOOR_LL_PIXELS=half`. ASCII glyph mode still requires
ANSI cursor addressing. Plain non-ANSI terminals are not supported; classic BBS
hosts (DOOR32.SYS and DOOR.SYS) are covered in the README's
[Classic BBS setup](../README.md#classic-bbs-setup).

The opening splash plays for about five seconds: sunrise over the ranges, the
lander's powered descent onto a lit pad, and the wordmark resolving in. It then
holds under "press any key to begin", as the other native NetBBS doors' splashes
do. Keys typed before it starts skip it entirely and are kept for the menu.

The splash and the ignition, successful landing and crash scenes are skippable
with Space (or any other key except Q, which quits). The skip key is consumed;
press the next action separately. The simulation is stopped during a scene, and
records are saved before the landing animation. To omit the opening animation,
set `DOOR_SPLASH=0` (shared with the other native doors) or `DOOR_LL_SPLASH=0`
in the profile environment. `DOOR_LL_SCENES=0` disables the launch and outcome
scenes. These settings are independent.

### Daily calendar and date display

LL reads `timezone` from the native door metadata. A missing timezone uses UTC;
an invalid zone or unavailable system timezone database produces a visible warning
and a bounded stderr diagnostic before falling back to UTC. Install the operating
system's timezone data to use named zones. The briefing shows the reset timezone.

The dailies show their date the way the rest of the node does. Since
v7.41.0, NetBBS publishes the node's date-and-time format (**Settings ▸ Timestamp
format**) to doors as `datetime_format`
([NetBBS #1545](https://github.com/Thiesi/NetBBS/issues/1545)); LL takes its date
part, the longest run of date directives and the separators between them, so
`%d.%m.%Y %H:%M` shows as `%d.%m.%Y`. A format with no usable date, and an older
NetBBS that does not send it, show ISO dates (`%Y-%m-%d`).

To show a different date than the node, or to match an older node, set
`DOOR_LL_DATE_FORMAT` in the profile environment, for example `%d/%m/%Y` or
`%m/%d/%Y`; it always wins. Allowed directives are `%Y`, `%y`, `%m`, `%d`, `%b`,
`%B`, `%a`, `%A`, with spaces, dots, slashes, commas and hyphens (maximum 32
characters). Month/day names follow the process locale. An invalid setting
visibly falls back to ISO dates. Date formatting never changes the challenge seed
or stored record keys.

NetBBS forwards size changes via republished JSON and SIGUSR1. LL also
polls metadata to coalesce notifications.
Resizing below 80x24 pauses the simulation wherever the host publishes the change.
Pause/help/resize do not extend the host's session time; LL warns in the last minute
and exits just before the published deadline. Disconnect forfeits the active flight.

## Records, backups and upgrades

The database is `pilots.db` under `DOOR_LL_DATA_DIR`, or under `data` next to the
script if no override is configured. The bundled registration sets it to
`<db>.doors/lunar_lander/`. For a registration by hand, always set an explicit
writable directory in the profile; an installed package directory may be
read-only. NetBBS forwards profile `DOOR_*` variables, not arbitrary process
environment variables.

Records use the opaque node ID, stable numeric account ID and mission ID. A handle
rename updates the displayed name on the next leaderboard read or saved landing.
Separate nodes cannot read each other's scores even if they share a directory.
Prefer separate directories anyway. Active flights have no resumable save; a result
is committed before the debrief appears. Simultaneous sessions retain the best score.

The records database has application ID `0x4C4C0001`. Schema 2 keeps pilots and
their bests, running counters, achievements and Programs; a schema 1 file
upgrades to it in place on its first open, adding tables only. A newer,
incomplete, unrelated or corrupt database is refused and preserved. LL says records are unavailable, offers unranked
play and writes a bounded stderr diagnostic for NetBBS's door-session history.
A write failure on touchdown clearly says the landing was not saved.

A bundled Lunar Lander's records **are included in NetBBS's backups**:
`python -m netbbs.backup` takes a checked snapshot of `pilots.db`, a restore puts
it back, and damaged or foreign records stop the backup with a message naming the
file. To move a registration by hand onto the bundled door, move its `pilots.db`
to `<db>.doors/lunar_lander/` and remove the hand-made registration.

Records anywhere else, in a hand registration's `DOOR_LL_DATA_DIR` or a profile
that points the bundled door elsewhere, are **not backed up by NetBBS**. Before
upgrades, close admission, let callers return and back up `pilots.db` with
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
| Question marks in the scenery | A CP437 terminal (SyncTERM) on a NetBBS that does not send the caller's `charset`; set `DOOR_LL_PIXELS=half` |
| "Exited unexpectedly (code -9)" | The CPU-seconds ceiling killed the door; raise the profile's `cpu_seconds` to 900 and use this release, which exits cleanly before the ceiling |
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
Use `--mode splash --gif --output .task/splash.gif` to export an animation;
`launch`, `landing` and `crash` are also available. `--angle 40` previews a tilted craft.
Windows developers need `tzdata` installed to run the timezone tests.

See [acceptance evidence](acceptance.md) for completed checks and field limits.
