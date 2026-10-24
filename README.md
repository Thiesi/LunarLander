![Lunar Lander — a gold spacecraft descends toward a cyan-lit landing pad beneath an indigo sky and a distant Earth.](assets/lunar-lander-social.jpg)

# Lunar Lander

A precision flying game for NetBBS. A small spacecraft, a dwindling fuel supply,
and a very unforgiving Moon — drawn in a richly colored ANSI terminal.

Read the drift. Watch the fuel. Make both feet count.

Guide a fragile lander between lunar ridges, manage your descent, and settle
onto an illuminated pad. Every correction costs fuel; every landing earns its
place.

**Status: playable release candidate.** Run `python lunar_lander.py` locally or
follow the [NetBBS installation and playing guide](docs/operations.md).
The banner is concept art; the cockpit below is rendered by the game itself.
See [acceptance evidence and remaining field checks](docs/acceptance.md) and the
[phase trackers](docs/design.md).

The game includes:

- Rich ANSI landscapes with stars, a distant Earth, and illuminated landing pads.
- Deterministic lunar physics, fuel management, and precise landing checks.
- A training basin, seven authored challenges, and a daily challenge that changes
  at the NetBBS node's local midnight.
- Animated arrival, ignition, touchdown and crash scenes, with a rotating lander.
- Persistent pilot records and leaderboards for completed safe landings.
- Up to eight concurrent callers with independent flights and shared leaderboards.
- Native NetBBS play at 80×24 and larger, with more scenery at 132×50.

Runtime delivery is a single `lunar_lander.py` file for Python 3.11+,
using only the standard library and suitable for vendoring in NetBBS.
NetBBS's existing native door API is the integration contract; Lunar Lander
does not require changes to it.

![Actual 80x24 Lunar Lander cockpit](docs/images/cockpit-80x24.png)

The [132x50 cockpit](docs/images/cockpit-132x50.png) shows the larger view.
The [arrival animation](docs/images/splash.gif) is captured from the terminal renderer.
The game has no third-party runtime dependencies. Run the test suite with
`python -m unittest discover -s tests -v`. Windows development tests also need
`pip install tzdata` for the named-timezone cases; production POSIX hosts use
their system timezone database.

The [social banner](assets/lunar-lander-social.jpg) is also ready for the
repository's GitHub social preview. See the [artwork notes](assets/README.md)
for the generation prompt and upload instructions.

[BSD 2-Clause licensed](LICENSE).
