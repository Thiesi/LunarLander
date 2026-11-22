# Release acceptance

Target: `v0.8.1`. It is not a claim that every NetBBS transport or target
operating system has been certified; the checks still to be done in the field
are listed at the end. Earlier releases' evidence follows, newest first.

## v0.8.1: a still window, colored foot marks, hand-drawn tilts

- The window holds still on the pad on the approach as well as close in, and
  every change of scale takes under a second. One scripted 277-frame descent
  at 80x24, bytes per frame after the first: truecolor 1,746 (v0.8.0 2,677,
  v0.7.3 2,244), 256 colors 937 (1,403, 1,499), sixteen colors 463 (697,
  924); at 132x50 truecolor 3,409 (5,721, 4,278). A craft more than 0.35 of
  the window from the pad's middle is still followed.
- The foot marks are white over the pad or another smooth site and red over
  anything else, each set into its cell so no neighbour's color is averaged
  into it. To try in play: it may make the pad's edge too easy to judge.
- The LM at its flight size has hand-drawn frames for 10, 20 and 30 degrees,
  both pixel grids. Turning by rule now joins whatever touched upright, so a
  mast stays under its hatch; the Surveyor's panels sit on a boom and its
  medium legs reach its body, and it is held to one piece at every tilt with
  the rest of the fleet.
- The leaderboard, the tour and program boards, the program presets and the
  Pilot Record use the debrief's lamps: a score on its track, a lamp for each
  mission, flights by how they ended. The viewer's own row keeps its lamps'
  colors.
- The scenes' ground is lit by its slope like the flight's. The postcard's
  flag stands left of the craft, clear of the screen's edge, and its captions
  sit a row lower so the pad stays in the picture.
- ASCII glyphs: a sprite is laid in color and lettered over it.
- A round-trip test reads each display's bytes back through a small ANSI
  terminal and compares the screen with the one meant, frame after frame of
  a flight and across every screen, for truecolor, 256 colors, sixteen on
  NetBBS, sixteen on a classic BBS (bold and eight backgrounds) and ASCII.
  v0.8.0's encoders passed it unchanged.
- 299 tests (unittest). Hosted CI with the real NetBBS 7.40.0 runtime on
  Linux and Windows passed on the release commit. Saved data is unchanged
  from v0.6.0 (schema 3); no new settings.
- The cockpit captures in `docs/images` are of a ranked mission (Tranquility),
  not the training basin with its flight path.

## v0.8.0: the presentation overhaul

- The cockpit is one header row, the view and four rows of instruments: 19
  rows of view at 80x24, where there were 14. Six gauges (altitude, vertical
  speed, drift, tilt, thrust, fuel) as rows of lamps; the touchdown limits are
  on the gauges and in their labels, and a breach is named (FAST, WIDE, STEEP).
  FAST now means sinking too fast: a climb is not flagged. The view adds the
  craft's shadow, the plume's light on the ground, a scale bar and a pointer to
  a pad out of the window; the ground is lit by its slope.
- The flight director and the Pilot Record sit over the chosen mission's
  landing site instead of a dimmed cockpit; the flight keys are no longer on
  that screen (they are on the cockpit and in the manual).
- The debrief shows readings against their limits, the trace in color, and a
  ranked score on a track between the medals and by its parts, which always
  add up to the score. The crash scene leaves a smoking wreck; a lone chevron
  turns gold; a promotion's captions keep a dark ground under the fireworks.
- 256 and 16 colors: the night's colors go by tone, as shade blocks between
  two palette colors, in place of the nearest color (which gave navy and teal
  ranges in 256 colors and one grey for everything in sixteen). The chosen
  row's bar is a palette role, blue in sixteen colors. Cells are compared by
  palette code, so two colors that read as one no longer repaint a cell.
- Cost, one scripted 277-frame descent at 80x24, bytes per frame after the
  first: truecolor 2,677 (was 2,244), 256 colors 1,403 (was 1,499), sixteen
  colors 697 (was 924); at 132x50 truecolor 5,721 (was 4,278). The taller
  view and the change to the close scale cost bytes; comparing by palette
  code saves them in the limited palettes. Close in, the window holds still
  on the pad and the change of scale takes half the frames of the first one,
  which keeps the last 30 m at about 2,700 bytes a frame in truecolor (1,200
  before, when nothing changed scale there). Frame time on the development
  host is unchanged within its noise.
- Below 30 m the camera closes in to a third scale, 200 m across (entered at
  30 m, left at 42 m; the 400 m scale is entered at 100 m and left at 120 m),
  and two marks on the ground show where the feet really are. The ranges'
  feet sink with the view there, so there is still sky over them.
- A craft is redrawn for each tilt (solid parts mapped whole, legs drawn as
  lines, windows, hatch and thrusters always kept) in place of a rotation by
  majority vote, which broke legs and smeared windows at nine pixels. Tests
  hold every craft in one piece with its windows at every tilt step, both
  pixel grids and both flight sizes. The frames are made by rule and kept,
  not drawn by hand.
- Training aids: the training basin and a Cadet program's simulator show the
  flight path ahead and the speed it would come down at; a pilot with no
  flight on record is told which key lights the engine. Scored flights show
  neither.
- The manual gives the tilt of the craft in hand (15 degrees for the Surveyor,
  5 for the Altair) where it said 10 for all.
- Instrument landings: the radar altimeter in large figures, a cross-pointer
  with the landing limits as a window on it, and the pad's bearing.
- A classic BBS's sixteen colors are sent as bold for a bright foreground and
  the eight plain backgrounds, never 90-97 or 100-107. SyncTERM's CTerm
  reference lists 1 and 22 and says the bright codes have no effect unless a
  mode is on (read from its published documentation, not tried on a host).
- 293 tests (unittest). Hosted CI with the real NetBBS 7.40.0 runtime on
  Linux and Windows passed on the release commit. Saved data is unchanged
  from v0.6.0 (schema 3); no new settings.
- Reviewed from renderer captures (`docs/images`), which mix a shade block's
  two colors as a fine dot pattern does. Not seen in a live terminal: see the
  field checks below.

## v0.7.3: a slimmer flight director

- Playtest feedback: the full flight director drops its "In flight" and
  "Touchdown" lines, which the instruments below show at every size (the
  compact card never had them). The card is 18 rows, not 20, so it fits from
  31 rows, not 33; the Pilot Record shares it and shows 13 lines at a time
  (#92).
- 248 tests (unittest). Hosted CI with the real NetBBS 7.40.0 runtime on
  Linux and Windows passed on the release commit. Saved data is unchanged
  from v0.6.0 (schema 3); no new settings.
- Field check: on a 31- or 32-row terminal the full card clears the
  instruments.

## v0.7.2: time to read

- Playtest feedback: the launch scene runs 4.5 s, not 3 (#88); a medal, a
  promotion and a crash hold, once played out, until a key, ignoring keys in
  their first 1.2 s so a burn held through touchdown cannot skip them unseen
  (#88, #89); the crash scene's hint reads "Continue".
- New achievements on the debrief take turns every 4 s, named in their medal's
  color with what each was for under it, in place of "+N more"; the Pilot
  Record shows an earned one's date and what it was for side by side where
  there is room, taking turns at 80 columns (#90).
- 248 tests (unittest). The NetBBS smoke test now continues past the held
  crash scene. Hosted CI with the real NetBBS 7.40.0 runtime on Linux and
  Windows passed on the release commit. Saved data is unchanged from v0.6.0
  (schema 3); no new settings.
- Field check: at 80x24, the achievement column's turns read calmly, and 4 s
  is long enough to read a description.

## v0.7.1: a sample return's records

- Three bugs found by NetBBS's review of v0.7.0 (Thiesi/NetBBS PR #1585),
  all in the sample return, which ends in the air at the ascent line:
  the pilot's softest-touchdown record came from the speed at the line, and
  the closest-landing record from a mid-air position (now the touchdown's
  speed, and no closest record for a sample return); a successful return
  could earn crash achievements such as Dead Stick; and a crash after lifting
  off was judged by the earlier soft touchdown, not the impact.
- `DOOR_LL_TODAY=YYYY-MM-DD` pins the game's date for testing and previews
  (asked for by NetBBS for its screen gallery); invalid values are ignored.
- 245 tests (unittest); each new bug test fails on v0.7.0. Hosted CI with the
  real NetBBS 7.40.0 runtime on Linux and Windows passed on the release
  commit. Saved data is unchanged from v0.6.0 (schema 3).

## v0.7.0: weekend specials and the Hopper

- At weekends the Maria daily is a sample return and the Highlands daily a
  rover rendezvous (#83); a hidden fourth craft, the Hopper, with cold-gas
  thrusters that heat and cut out, and the Surveyor, Altair and Hopper drawn
  as themselves (#84). 63 achievements.
- 241 tests (unittest): the scripted pilot flies every weekend special of 2026
  and 2027 and both in every craft with faithful ghosts; rover strike, near
  and far parking (a far one is not saved); sample-return resting, settling
  back and the climb; the Hopper's heating, cut-out and cooling, and its
  pilot on every ranked and historic mission. Hosted CI with the real NetBBS
  7.40.0 runtime on Linux and Windows passed on each change and on the
  release commit. Saved data is unchanged from v0.6.0 (schema 3).
- Not yet flown by a human: the two new weekend specials and the Hopper.

## v0.6.0: the roadmap release

- CAPCOM callouts, the descent trace, weekend hops, ghosts and replays,
  rivals, the Grand Tour, instrument landings, postcards, the Surveyor and
  the Altair, live descents and the HISTORY chapter (#71-#81, tracker #70).
- **Records schema 3.** Adds the tables `ghosts` and `tours`; schema 1 and 2
  files upgrade in place on first open, keeping every record (one-way). Tests
  cover a new file, both upgrades and refusal of anything newer. NetBBS's
  backups accept schema 3 from Thiesi/NetBBS#1577 on, so this release must not
  run on a node before the NetBBS release that bundles it.
- Live descents keep small files in a `live/` folder beside `pilots.db`; they
  are transient and need no backup. `DOOR_LL_LIVE=0` turns them off.
- 223 tests (unittest): ghosts replay exactly for every mission and craft, the
  scripted pilot lands every weekend hop of 2026 and 2027 and every mission in
  every craft, historic facts as cited in #81. Hosted CI with the real NetBBS
  7.40.0 runtime on Linux and Windows passed on each change and on the
  release commit.
- Not yet flown by a human: hop gold, the Surveyor's and Altair's handling,
  and whether the live line is welcome or noise. Listed below.

## v0.5.2: cosmetic fixes

- The DAILIES tab and splash; [X] Level in the flight director's key line,
  which fits 70 columns; a countdown to the node's midnight in the Dailies
  briefing (tested in UTC and Europe/Berlin, including the 25-hour night);
  the PROGRAM tab lists only the keys that work. All from the maintainer's
  playtest.
- 147 tests (unittest); hosted CI with the real NetBBS 7.40.0 runtime on Linux
  and Windows passed on each change and on the release commit. Saved data is
  unchanged from v0.5.0 (schema 2).

## v0.5.1: half blocks for fonts without quarter blocks

- NetBBS 7.43.0 sends `quadrants` in the door metadata (Thiesi/NetBBS#1560);
  when it is false the door draws that caller in half blocks (#43). Absent or
  non-boolean values change nothing, and a CP437 caller still gets half blocks.
- 146 tests (unittest), Windows / Python 3.14.7; hosted CI with the real
  NetBBS 7.40.0 runtime on Linux and Windows passed on the change and on the
  release commit. Saved data is unchanged from v0.5.0 (schema 2).
- Not yet seen on a live NetBBS 7.43.0 node with PuTTY and Profile ▸ Quarter
  blocks on Auto. Listed below.

## v0.5.0: achievements, the Pilot Record and Programs

- **Records schema 2.** A schema 1 file upgrades in place on its first open,
  adding four tables and keeping every record; tests cover a new file, the
  upgrade and refusal of anything else. NetBBS 7.41.0's backups accept only
  schema 1, so this release must not run on a node before the NetBBS release
  that resolves Thiesi/NetBBS#1561; the final schema is posted there.
- 145 tests (unittest), Windows / Python 3.14.7 with development-only tzdata.
  Added: every flight achievement driven by real touchdowns and impacts,
  counters and career feats (streaks across old and new daily keys), awarding
  once, quiet retroactive awards, silver and gold announcements only, the
  Pilot Record's keys and tabs at 80x24 and 132x50; Programs' generation (five
  to eight climbing missions, the same everywhere), the real flight's variation
  (start only, landable), one real attempt per mission, each preset's rules, a
  lost connection counting as a crash, the board, simulator allowances, scoring
  the program and never the career, completion with its achievements and
  announcement, and the tab, cards, header and debrief.
- Outside the suite, the scripted pilot landed every mission of 36 seasons of
  Programs; the dailies are byte-for-byte unchanged by the shared generator.
- The launch scene lasts 3 seconds, long enough to read (playtest feedback).
- Hosted CI with the real NetBBS 7.40.0 runtime on Linux and Windows passed on
  each change and on the release commit. Locally the real-process tests and the
  smoke test's 3-second deadline timed out under unrelated machine load, here and
  on `main` alike; they pass on their own.
- Not yet assessed by a human pilot: the achievements' thresholds, Programs'
  difficulty curve and presets, and the Pilot Record at 80x24. Listed below.

## v0.4.0: three dailies and a compact flight director

- 114 tests pass under unittest, Windows / Python 3.14.7 with development-only
  tzdata. Added: three dailies a day with their keys and names; every daily
  setting within its chapter's span over a year of dates; a fair approach
  (inside the field, clear of the ridges, drifting toward the pad); variety and
  both start sides; reproducibility across processes; the scripted pilot landing
  sixty days of dailies with over 20 kg of fuel left; the compact flight
  director's size and contents at 24, 32, 33 and 50 rows, with the instruments
  visible below it at 80x24.
- Outside the suite, the scripted pilot landed every daily of two years (2,190
  flights) with at least 49, 40 and 30 kg of fuel left on the Maria, Highlands
  and Frontier dailies.
- Hosted CI with the real NetBBS 7.40.0 runtime on Linux and Windows passed on
  both changes and on the release commit.
- Not yet assessed by a human pilot: how the three dailies feel, and whether
  the Frontier daily is hard enough. Listed below.

## v0.3.0: classic BBS hosts, the node's date, cleaner cards

- 108 tests (unittest and pytest collect the same suite), Windows / Python
  3.14.7 with development-only tzdata. Added: DOOR32.SYS and DOOR.SYS parsing
  (both formats, renamed and malformed files, sanitised names, plain terminals),
  classic hosts' identity, limits, settings and error messages, every screen
  reaching CP437 without loss, the DOOR32 socket link over a socketpair (telnet
  filtering, CR NUL and CR LF, IAC doubling, carrier loss), two real-process
  classic launches (DOOR32.SYS over stdio in CP437, and a plain terminal told it
  needs ANSI), the date part of nine node date formats and its precedence, cards
  clearing the gauges they cover at 80x24, and the leaderboard marking the
  viewer's own row.
- Hosted CI, with the real NetBBS 7.40.0 runtime on Linux and Windows, passed on
  each change as rebased onto the one before it, and on the release commit.
  Locally, the timing-sensitive process tests and the NetBBS smoke test's
  3-second deadline scenario timed out on `main` and on the changes alike while
  the development machine was saturated by unrelated processes; the rest passed.
- Classic BBS support has not met a real Synchronet, Mystic or ENiGMA½ install;
  that check is listed below.

## v0.2.1: CP437 callers and documentation

- A SyncTERM (CP437) playtest on NetBBS showed v0.2.0's quadrant blocks as
  question marks: NetBBS maps every other glyph the game draws to CP437, but has
  no substitute for a quadrant. The door now reads the caller's character set
  (`charset`, proposed in NetBBS #1557) and draws half blocks for CP437 and
  ASCII glyphs for ASCII; without the field it behaves as v0.2.0. Twelve screens
  run through NetBBS's own CP437 mapping (from its `main`) produced 7,010
  question marks from quadrant output and none on the CP437 path.
- 89 unittest cases pass in both pixel modes; added: the `charset` field's
  parsing and that no view gives a CP437 caller a quadrant.
- Hosted CI passed on the change and on the release commit. Locally, the
  3-second deadline test timed out on `main` and on the change alike while the
  development machine was saturated by unrelated processes.
- The README now follows the other native games' layout, and the operations
  guide describes the door bundled in NetBBS v7.41.0 (Gallery registration,
  records backed up with the node) and the `datetime_format` it does not read
  yet (#34).

## v0.2.0: quadrant blocks, fine sprite art, taglines and fuel alerts

- 87 unittest cases, Windows / Python 3.14.7 with development-only tzdata, pass
  with the default quadrant blocks and again with `DOOR_LL_PIXELS=half`. Added:
  the quadrant colour split, narrow-column mapping, the fine landers' footprint
  and tilted symmetry, the stage's composition matching between modes, quadrant
  or ASCII output in every view, the tagline pick and fit, and the fuel alert
  levels, flashing, frame alarm, gauge and ASCII form.
- Half-block mode is unchanged from v0.1.0: the stage and every sprite were
  compared against v0.1.0's output and matched exactly.
- NetBBS 7.40.0 from the pinned commit, Windows / Python 3.14.7: all six
  scenarios passed on each change and on the merged result.
- Cost of quadrant blocks, 300-frame descent at 256 colours: the 132x50 cockpit
  rose from about 10 to 14 ms of CPU and from 2.7 to 3.5 KiB per frame; scenes
  from 9.4 to 12.5 ms. Card screens keep their slow redraw rates, so idle CPU
  is as in v0.1.0. Timings vary with machine load.
- The maintainer playtested the tagline and fuel-alert changes before release.

## v0.1.0: completed locally

- 70 unittest cases, Windows / Python 3.14.7 with development-only tzdata: flight model,
  discrete-control successful landings in all missions, daily reproducibility,
  real process quit/EOF/deadline, incremental keys, palettes, screen bounds,
  help/pause/retry, database concurrency/isolation/recovery refusal; node-local
  midnight and DST, active-flight date pinning, formatting-independent seeds,
  scene lifecycle/skip/save ordering, rotating hull and colored controls/values;
  splash hold and spent skip key, menu grid alignment, named unsafe-speed
  warnings, stars kept off scenery and 256/16-color readings of scenery colors;
  rc.4: the menu's ranking notes in full, Q's return and in-flight confirmation,
  the advertised cursor keys, the CPU-budget estimate and clean exit, medal
  thresholds, the rank ladder and the daily challenge's exclusion, chapter
  navigation, the award sequence after a landing, and NetBBS game-event requests.
- rc.4 idle CPU: the 132x50 menu measured 2.5% of a CPU, down from about 20% in
  rc.3, whose idle callers ran out the 300 CPU-second ceiling in about 25 minutes.
- rc.4 playtest fixes: NetBBS 7.40.0 from the pinned commit, Windows / Python
  3.14.7: all six scenarios passed. With the career feature added, the five
  untimed scenarios passed locally; the 3-second deadline scenario timed out
  under unrelated 100% CPU load (as did the fixes alone at that time) and passed
  in hosted CI on both platforms.
- rc.3 visual overhaul: NetBBS 7.40.0 from an archive of pinned commit
  `8e593794ab5dad308d8a3552198b7da35b852c6d`, Windows / Python 3.14.7: all six
  scenarios below passed again, including eight simultaneous callers.
- NetBBS 7.40.0, isolated tag checkout `fd8744c4d86805081f0d8470c6dc31323c9c207d`,
  Windows / Python 3.12.10 development check: real `run_door` launches at 80x24 and 132x50, flight/help/pause,
  crash/retry, clean deadline exit, caller disconnect cleanup, eight simultaneous
  callers and return to host mode. All six scenarios passed. The imported module
  path and version were checked against that isolated checkout. This rerun replaces
  the earlier inconsistent provenance claim: `d04170aa` belongs to the 7.31.0 line,
  not 7.40.0. NetBBS supports Windows for development/testing, not production.
  The Windows development runtime does not forward native resize because SIGUSR1
  is POSIX-only; that scenario was explicitly not run on Windows.
- Inspected rendered 80x24 and 132x50 cockpit captures, briefing and help. Layout
  tests cover 16/256/truecolor and ASCII/Unicode. Animated arrival, ignition,
  landing and crash captures are generated from the actual terminal renderer.
  After the visual overhaul, a default 80x24 256-color flight frame is about
  11,000 bytes initially (17,000 in truecolor, 6,100 in 16 colors) and about
  170 bytes per frame in early flight (rc.1 drew 8,251 and 112). The 80x24
  truecolor splash sends about 119,000 bytes over its five seconds. Camera
  transitions and large screens require more bandwidth. These are not worst-case
  network measurements.

## Hosted checks

The acceptance workflow runs the full game suite and actual NetBBS runtime on
Linux and Windows with Python 3.11 (Windows is development evidence), pinned to public host commit
`8e593794ab5dad308d8a3552198b7da35b852c6d`. Linux additionally exercises live native
resize down to 70x20 and back to 132x50. Inspect the workflow run associated with
the release commit; a pending or skipped job is not passing evidence.

## Playtests and remaining field checks

ReLink reported a successful general playtest and enjoyable gameplay, with
deployment feedback in #14, addressed in rc.2. The rc.3 playtest's findings were
fixed in rc.4, and the rc.4 review's one cosmetic finding (the menu's ranking
note wrapping mid-phrase) is fixed in v0.1.0. These reports do not identify
every transport, mission or recovery scenario; the following were not performed
before release and remain open:

- The presentation overhaul: shade blocks in real 256- and 16-color terminals
  and fonts (do `░▒▓` read as tones or as noise, and do they join without
  seams?); a terminal theme that recolors the sixteen colors; the header's
  shortened key hints with a long BBS name; the gauge strip's `■` lamps in a
  CP437 font; and a human pass over the taller view (does the craft's shadow
  help or distract?), the close zoom and its foot marks (is the change of
  scale at 30 m a help in the last seconds, or a jolt?), the tilted craft at
  each step, and the training path (does it teach, or fly the basin for you?).
- v0.8.0 classic hosts: bold-for-bright and eight backgrounds on a real
  SyncTERM, NetRunner or DOS terminal (#13).
- v0.2.0 quadrant blocks in a range of real terminal fonts: whether quadrant
  pieces join without seams. NetBBS's web terminal draws them itself.
- v0.7.0: a human pass over the sample return, the rover rendezvous and the
  Hopper's heat (does the cut-out feel fair?).
- v0.6.0: a human pass over weekend hops (is gold within reach?), the
  Surveyor's and Altair's handling, instrument landings, and whether the live
  line on a busy node reads as company or noise; a NetBBS backup and restore
  of schema 3 records once NetBBS ships #1577.
- v0.5.1: PuTTY with its default font on NetBBS 7.43.0 (Quarter blocks on
  Auto) sees half-block scenery with no boxes; with Quarter blocks On, the
  quadrant picture.
- v0.5.0: a human pass over achievements (are any too easy or out of reach?),
  a full program in each preset, and the Pilot Record at 80x24; a NetBBS
  backup and restore of schema 2 records once NetBBS supports it (#1561).
- v0.4.0 dailies: a human assessment of the three generated dailies' feel and
  difficulty, across a few days.
- v0.2.1 CP437 callers: half blocks once NetBBS sends `charset` (NetBBS #1557).
  Until then, CP437 callers need `DOOR_LL_PIXELS=half` on their node.

- Human flight/control/balance assessment of the four added authored missions and animations.
- rc.4 career: human assessment of the eight new missions and of the medal
  thresholds. A scripted fuel-thrifty pilot reaches gold on every mission, by
  11-26 points on the hardest. Game events are covered by unit tests of the
  request files; a NetBBS bot announcing them has not been observed.
- rc.3 presentation in real Telnet/SSH/web clients: the splash, shaded scenery and
  lander were reviewed from renderer captures, not live terminals; ASCII glyph
  mode's large scene lander is legible but busy.
- Actual Telnet and SSH terminals, including ordinary key repeat and realistic latency.
- Classic BBS hosts: a real Synchronet (Linux stdio and Windows DOOR32 socket),
  Mystic and ENiGMA½ launch, including real-time flight over telnet. Drop-file
  parsing, CP437 output and the socket link are covered by unit and stdio
  process tests only.
- Actual browser terminal, control keys and live resize.
- NetBSD service deployment, permissions/resource limits, two callers and restore drill.
- Caller disconnect and relaunch with durable records on that installation.

Automated successful flight is evidence of feasibility, not evidence of enjoyable
difficulty. NetBBS's terminal emulator is useful for screen assertions, but it does
not substitute for a human looking at a real client. Report what these checks
find as issues against the release.
