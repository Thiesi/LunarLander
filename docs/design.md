# Lunar Lander: flight plan

## Product

Land a fragile spacecraft on illuminated pads among lunar ridges. Judge drift,
descent rate, attitude and fuel; commit to a landing or burn precious fuel to
try again. A run should take two to five minutes. Crashes must teach the pilot
what went wrong and invite an immediate retry.

The primary platform is a modern NetBBS ANSI terminal at 80x24 or larger.
132x50 should reveal more landscape detail, not change physics or difficulty.
Art direction: near-black indigo sky, sparse stars, distant Earth, layered slate
mountains, warm gold lander and exhaust, cyan landing lights, amber instruments.
No emoji, font-dependent icons, blinking text or color-only warnings.

## Resolved scope (P0)

- **Distribution:** one `lunar_lander.py`, Python 3.11+, standard library only,
  BSD-2-Clause. Separate tests, docs and profile JSON. No companion process,
  network service, NetBBS imports or new API requirements.
- **Host:** native stdio, UTF-8, `resize_signal: true`, geometry 0x0 (follow
  caller), documented absolute interpreter/install paths. NetBBS handles Telnet,
  SSH and web framing; LL only reads/writes the child terminal stream.
- **API:** explicitly support launch versions 2 through 5 for core play; reject
  unknown versions clearly. Ignore additive fields. Missing optional capabilities
  use conservative defaults. Missing identity permits unranked practice only;
  malformed supplied metadata is an error, never a silent standalone fallback.
- **Controls:** A/D or left/right changes commanded attitude in 10-degree steps;
  W/S or up/down changes latched throttle by 10%; digits select throttle (0 off,
  9 full); space cuts thrust; X levels the craft. No key-up or simultaneous-key
  dependency. P pauses, ? shows help, Q exits. Menus explain controls before flight.
- **Simulation:** fixed 1/60-second steps, SI units, lunar gravity 1.62 m/s²,
  fuel-dependent mass, thrust and fuel consumption. Swept/substepped contact for
  both feet; landing requires a pad, safe vertical/horizontal speeds and attitude.
  Simulation is independent of rendering and terminal size. Slow output never
  causes an unbounded catch-up burst: cap elapsed catch-up and disclose slow play.
- **Presentation:** 10 frames/sec, changed cell runs only after the first frame;
  UTF-8 half-block terrain at two vertical samples per row. 256-color palette
  with truecolor enhancement and 16-color mapping. ASCII glyph preference keeps
  ANSI cursor movement and readable terrain. An ANSI-free real-time version and
  classic DOOR32/DOS support are deferred; explain unsupported terminals clearly.
- **Camera:** overview for approach, closer view near the selected pad, smooth
  bounded tracking and a scale label. Instruments remain fixed. Pause physics on
  undersize terminals, help and explicit pause; deadline still advances. Never
  write the bottom-right cell. Resize invalidates the diff buffer.
- **Content:** training basin plus seven authored challenges, increasing lateral
  drift, terrain and fuel pressure. A seeded daily challenge gives callers the
  same start for a node-local calendar day. No randomness in collision or scoring.
- **Scoring:** completed safe landings only; difficulty, fuel reserve and landing
  precision. Training is unranked. One best score per node/account/challenge;
  exact score formula and tie-break appear in help. No resume of an active flight
  in v1: a lost connection forfeits that attempt, never erases completed records.
- **Storage:** SQLite under explicit `DOOR_LL_DATA_DIR` (allowed by NetBBS's
  `DOOR_*` environment rule), otherwise an installation-local `data` directory.
  Namespace by opaque `node_id` plus numeric `user_id`, never handles. Short
  transactions, versioned schema, concurrent completed-result updates, no locks
  held during play. No automatic integration into NetBBS backups is assumed.
- **Safety/cleanup:** EOF, broken output, SIGTERM, deadline and ordinary quit all
  end promptly; restore cursor, attributes and local input mode. Bounded reads,
  sanitized display names and bounded errors. Save results before celebrations.
- **Optional outbound:** deferred beyond v1. No automatic chat/board posts. The
  existing API 5 achievements/standings hook is sufficient for a future slice.
- **Release:** tagged single-file asset, license, profile and SHA256SUMS, matched
  against tagged source. NetBBS vendoring itself is a downstream integration task;
  do not change its frozen API or edit an existing vendored copy.

No unresolved product decision blocks implementation. The acceptance matrix below
is an evidence gate, not permission to claim unperformed human/host testing.

## Contract research

Reviewed public NetBBS `main` on 2026-10-24:

- [Developer handbook: native doors, metadata, lifetime and resize](https://github.com/Thiesi/NetBBS/blob/main/docs/NetBBS-Developer-Handbook.md#developing-a-native-door).
  The metadata discriminator is currently `door_api: 5`; `unicode_style` is a
  boolean, not a font name. Session limits are elapsed wall time, not CPU time.
- [Door guide: installation and operational limits](https://github.com/Thiesi/NetBBS/blob/main/docs/NetBBS-door-guide.md#native-doors).
  Install directories persist; launch/drop-file directories do not.
- [Profile parser](https://github.com/Thiesi/NetBBS/blob/main/src/netbbs/doors/profiles.py),
  reviewed blob `294497fd258705f0e60bb38b5d9d580eeba87adc`:
  `DOOR_*` environment names are allowed; arbitrary `LL_*` names are not.
- [Runtime](https://github.com/Thiesi/NetBBS/blob/main/src/netbbs/doors/runtime.py)
  publishes JSON and signals stdio resize with SIGUSR1 on POSIX. Polling metadata
  periodically handles coalesced notifications.
- [Retro Trivia](https://github.com/Thiesi/NetBBS/blob/main/src/netbbs/doors/bundled/retro_trivia.py)
  demonstrates timed POSIX/Windows input. LL implements its own bounded input
  decoder and stream lifecycle rather than importing the bundled game.

The existing API is sufficient. No NetBBS gap issue is required.

## Phases and slices

Each P-number is a GitHub milestone with one tracker; P0 is the scoping issue.
[P0 #2](https://github.com/Thiesi/LunarLander/issues/2),
[P1 #3](https://github.com/Thiesi/LunarLander/issues/3),
[P2 #4](https://github.com/Thiesi/LunarLander/issues/4),
[P3 #5](https://github.com/Thiesi/LunarLander/issues/5),
[P4 #6](https://github.com/Thiesi/LunarLander/issues/6).
Each slice gets a reviewable PR, or adjacent tightly coupled slices share one PR
with explicit acceptance evidence. Dependencies below are blockers.

### P0 — Contract and design

**S00 — Resolve the product and host contract.** Build this design and the GitHub
milestones/trackers so implementation has an agreed, executable scope.
Outcome: no unresolved launch/control/storage/presentation decisions.
Acceptance: source-linked API research, all slices have build/why/outcome/criteria/
blockers, release/manual boundaries explicit. Blockers: none.

### P1 — Native flight foundation

**S01 — Host adapter and terminal lifecycle.** Build metadata validation, incremental
key decoding, timed input, resize/deadline handling and a usable flight-ready screen.
Why: a beautiful game is useless if callers cannot enter or leave reliably.
Outcome: native stdio door launches and returns cleanly.
Acceptance: real subprocess pipe input/EOF/quit/deadline tests; split arrow sequences;
optional-field defaults; unknown API rejected; malformed metadata diagnosed; 80x24
and 132x50 geometry; documented profile accepted by NetBBS parser.
Blockers: S00.

**S02 — Deterministic flight model.** Build terrain/pads, thrust/fuel, attitude,
collision, safe landing classification and scoring primitives.
Why: control must feel learnable and crashes must be fair.
Outcome: reproducible flights independent of rendering.
Acceptance: known ballistic motion; fuel exhaustion; both-foot pad containment;
fast impact cannot tunnel; tilt/drift/vertical-speed failures named; replay produces
identical results; a scripted successful landing is possible. Blockers: S00.

### P2 — Beautiful playable vertical slice

**S03 — Landscape and cockpit renderer.** Build half-block scenery, stars/Earth,
lander/exhaust, lit pads, camera, numeric gauges, palettes and diff output.
Why: terminal graphics are a primary product feature.
Outcome: legible and attractive flight at both target sizes.
Acceptance: inspect rendered captures at 80x24 and 132x50; 16/256/truecolor and
ASCII glyph modes; no out-of-bounds cursor moves or bottom-right output; unchanged
frames emit nothing; normal flight avoids full-screen clears. Blockers: S01, S02.

**S04 — Complete training flight.** Connect simulation/input/rendering to launch,
pause/help, landing/crash debrief and retry. Show failure causes and safe thresholds.
Why: demonstrate the whole fun loop before adding content or persistent systems.
Outcome: caller can learn, fly, crash/land and retry without relaunching the door.
Acceptance: scripted end-to-end launch/control/crash/retry/quit; helpful debrief;
help/pause/undersize freezes physics but not host deadline; resize forces full
repaint; no stale key starts a new flight unexpectedly. Blockers: S03.

### P3 — Challenge and replay value

**S05 — Missions and daily challenge.** Build three authored missions and one
UTC-daily deterministic variant with briefing, risk/reward and visible targets.
Why: mastery needs increasingly demanding, recognizable flights.
Outcome: distinct challenges with reachable landings and finite fuel margins.
Acceptance: every authored mission has a successful scripted flight; same daily
date yields identical terrain/start across processes; different dates vary;
all pad widths/speeds remain usable at 80x24. Blockers: S04.

**S06 — Durable pilot records.** Build transactional best scores, mission-scoped
leaderboards, personal best feedback and clear unranked practice behavior.
Why: BBS callers should have a reason to return and compete fairly.
Outcome: completed flights survive restart, concurrent callers and handle changes.
Acceptance: node/account isolation; simultaneous writes preserve best result;
practice/aborts/crashes do not rank; corrupt/newer databases fail clearly without
replacement; read-only storage does not trap callers; explicit backup instructions.
Blockers: S05.

### P4 — Acceptance and vendoring release

**S07 — Native host and presentation acceptance.** Build repeatable NetBBS runtime
integration scenarios and capture tooling; fix real usability/integration failures.
Why: fixtures alone cannot establish compatibility with the actual host.
Outcome: reproducible evidence distinguishing unit, subprocess, native runtime,
transport and human play tests.
Acceptance: full LL suite; real NetBBS run_door launches at 80x24 and 132x50;
quit/deadline/disconnect/resize and two callers; inspect terminal renders; record
platform/version, unperformed Telnet/SSH/web client and human balance testing.
Blockers: S06.

**S08 — Release and SysOp handoff.** Build install/controls/troubleshooting docs,
vendoring artifacts and checksum verification; publish a tagged candidate or stable
release according to evidence. Why: SysOps need a deployable, maintainable game.
Outcome: verified downloadable source/profile/license with safe state operations.
Acceptance: clean-checkout suite, artifact/tag byte identity, LF endings, downloaded
checksum verification, fresh install invocation; release notes name outstanding
field/balance gates. Stable v1 requires actual terminal/browser human acceptance;
without it publish an explicitly marked prerelease. Blockers: S07.

## Delivery discipline

### P5 — ReLink playtest polish

[Milestone 6](https://github.com/Thiesi/LunarLander/milestone/6) and
[tracker #15](https://github.com/Thiesi/LunarLander/issues/15) define R01–R03,
their acceptance criteria and blockers. R01 corrects deployment guidance and
enables eight independent concurrent callers. R02 adds skippable arrival,
ignition, landing and crash scenes, consistent hotkey/value colors, and the
user-selected rotating half-block hull. R03 adds four authored missions and
node-local daily rollover with an explicit date-format setting.

The original S05 UTC policy above describes rc.1; R03 supersedes it. In-flight
attempts retain their calendar key through midnight, while briefing/retry picks
up the new day. Existing mission IDs and record schema remain unchanged.
NetBBS publishes the node timezone but not its date-format preference; use
`DOOR_LL_DATE_FORMAT` rather than require an API change. The nonblocking gap is
tracked in [NetBBS #1545](https://github.com/Thiesi/NetBBS/issues/1545).

The visual overhaul brings the presentation in line with the other native doors
(Voidrunner, Retro Trivia): shaded RGB scenery with 256- and 16-color readings,
peaked parallax ranges, a lit Earth, a gold-foil lander in three sizes with a
flickering plume and ground dust, framed cards over a dimmed cockpit, and a
splash that holds under its prompt until a key.

The career release adds chapters (Maria, Highlands, Frontier, Daily) with fifteen
ranked missions, medals derived from best scores (bronze any safe landing, silver
1,400 and gold 1,750 per difficulty point), a rank ladder from medal points, medal
and promotion scenes, and NetBBS game events for promotions, first golds and
career standings. Chapters are data, and a mission carries its own gravity, so a
later season or another world is new entries rather than new machinery.

Animations run at the existing 10 fps, obey host deadlines and consume their skip
key. They never advance flight physics. Save a landing before celebrating it;
unranked play and storage errors remain explicit. The eight-caller shipped
profile is checked through NetBBS itself as well as transactional record tests.

### Review and delivery

Fetch and start from current remote main. Commit/push and open a PR; wait for Claude's
completed written review. Triage findings by caller/SysOp impact, fix meaningful
ones, and request `@claude review` again after fixes. Merge only after that cycle and
relevant checks pass. Explain dismissed theoretical findings. Delete merged local
and remote branches and task-owned worktrees. Never equate a failed/skipped reviewer
run with approval. Keep subsequent work independent while a review is pending.

## Acceptance matrix

Automated: deterministic physics; boundary/collision scenarios; protocol fixtures;
real stdin/stdout subprocesses; storage concurrency; ANSI terminal bounds; NetBBS's
actual runtime and profile parser. Capture 80x24/132x50 and palette variants.

Field: real terminal client over Telnet and SSH, actual browser transport, resizing
during flight, ordinary key repeat/network latency, disconnect and relaunch, two
callers, and human assessment of difficulty/readability. Record these separately;
a virtual terminal or ScriptSession does not certify a browser or a human playtest.
