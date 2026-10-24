# Release candidate acceptance

Target: `v0.1.0-rc.1`. This is a playable candidate for field testing, not a claim
that every NetBBS transport or target operating system has been certified.

## Completed locally

- 29 standard-library unittest cases, Windows / Python 3.14.7: flight model,
  discrete-control successful landings in all missions, daily reproducibility,
  real process quit/EOF/deadline, incremental keys, palettes, screen bounds,
  help/pause/retry, database concurrency/isolation/recovery refusal.
- NetBBS 7.40.0, checkout `d04170aa998b459b9f5ca6b9bca9ea63a17f7ab9`, Windows /
  Python 3.12.10: real `run_door` launches at 80x24 and 132x50, flight/help/pause,
  crash/retry, clean deadline exit, caller disconnect cleanup, two simultaneous
  callers and return to host mode. All six scenarios passed. Windows native resize
  forwarding is not implemented by this host, so it was explicitly not run.
- Inspected rendered 80x24 and 132x50 cockpit captures, briefing and help. Layout
  tests cover 16/256/truecolor and ASCII/Unicode. A sample default 80x24 frame was
  8,251 bytes initially and 112 bytes after 0.1 seconds of early flight; camera
  transitions and large screens require more bandwidth. These are not worst-case
  network measurements.

## Hosted checks

The acceptance workflow runs the full game suite and actual NetBBS runtime on
Linux and Windows with Python 3.11, pinned to public host commit
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
