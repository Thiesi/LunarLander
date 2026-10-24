# Release candidate acceptance

Target: `v0.1.0-rc.1`. This is a playable candidate for field testing, not a claim
that every NetBBS transport or target operating system has been certified.

## Completed locally

- 29 standard-library unittest cases, Windows / Python 3.14.7: flight model,
  discrete-control successful landings in all missions, daily reproducibility,
  real process quit/EOF/deadline, incremental keys, palettes, screen bounds,
  help/pause/retry, database concurrency/isolation/recovery refusal.
- NetBBS 7.40.0, isolated tag checkout `fd8744c4d86805081f0d8470c6dc31323c9c207d`,
  Windows / Python 3.12.10 development check: real `run_door` launches at 80x24 and 132x50, flight/help/pause,
  crash/retry, clean deadline exit, caller disconnect cleanup, two simultaneous
  callers and return to host mode. All six scenarios passed. The imported module
  path and version were checked against that isolated checkout. This rerun replaces
  the earlier inconsistent provenance claim: `d04170aa` belongs to the 7.31.0 line,
  not 7.40.0. NetBBS supports Windows for development/testing, not production.
  The Windows development runtime does not forward native resize because SIGUSR1
  is POSIX-only; that scenario was explicitly not run on Windows.
- Inspected rendered 80x24 and 132x50 cockpit captures, briefing and help. Layout
  tests cover 16/256/truecolor and ASCII/Unicode. A sample default 80x24 frame was
  8,251 bytes initially and 112 bytes after 0.1 seconds of early flight; camera
  transitions and large screens require more bandwidth. These are not worst-case
  network measurements.

## Hosted checks

The acceptance workflow runs the full game suite and actual NetBBS runtime on
Linux and Windows with Python 3.11 (Windows is development evidence), pinned to public host commit
`8e593794ab5dad308d8a3552198b7da35b852c6d`. Linux additionally exercises live native
resize down to 70x20 and back to 132x50. Inspect the workflow run associated with
the release commit; a pending or skipped job is not passing evidence.

## Field gates before stable v1

- Human flight/control/balance assessment on training and all three authored missions.
- Actual Telnet and SSH terminals, including ordinary key repeat and realistic latency.
- Actual browser terminal, control keys and live resize.
- NetBSD service deployment, permissions/resource limits, two callers and restore drill.
- Caller disconnect and relaunch with durable records on that installation.

Automated successful flight is evidence of feasibility, not evidence of enjoyable
difficulty. NetBBS's terminal emulator is useful for screen assertions, but it does
not substitute for a human looking at a real client. Keep these gates open until
the corresponding evidence exists; a candidate can be distributed meanwhile.
