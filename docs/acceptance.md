# Release candidate acceptance

Target: `v0.1.0-rc.3`. This is a playable candidate for field testing, not a claim
that every NetBBS transport or target operating system has been certified.

## Completed locally

- 47 unittest cases, Windows / Python 3.14.7 with development-only tzdata: flight model,
  discrete-control successful landings in all missions, daily reproducibility,
  real process quit/EOF/deadline, incremental keys, palettes, screen bounds,
  help/pause/retry, database concurrency/isolation/recovery refusal; node-local
  midnight and DST, active-flight date pinning, formatting-independent seeds,
  scene lifecycle/skip/save ordering, rotating hull and colored controls/values;
  splash hold and spent skip key, menu grid alignment, named unsafe-speed
  warnings, stars kept off scenery and 256/16-color readings of scenery colors.
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

## ReLink playtest and remaining field gates

ReLink reported a successful general playtest and enjoyable gameplay, with
deployment feedback in #14. That feedback is addressed in this candidate.
This report does not identify every transport, mission or recovery scenario;
the expanded mission set and presentation still need human flight assessment.

- Human flight/control/balance assessment of the four added authored missions and animations.
- rc.3 presentation in real Telnet/SSH/web clients: the splash, shaded scenery and
  lander were reviewed from renderer captures, not live terminals; ASCII glyph
  mode's large scene lander is legible but busy.
- Actual Telnet and SSH terminals, including ordinary key repeat and realistic latency.
- Actual browser terminal, control keys and live resize.
- NetBSD service deployment, permissions/resource limits, two callers and restore drill.
- Caller disconnect and relaunch with durable records on that installation.

Automated successful flight is evidence of feasibility, not evidence of enjoyable
difficulty. NetBBS's terminal emulator is useful for screen assertions, but it does
not substitute for a human looking at a real client. Keep these gates open until
the corresponding evidence exists; a candidate can be distributed meanwhile.
