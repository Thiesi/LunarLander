![Lunar Lander — a gold spacecraft descends toward a cyan-lit landing pad beneath an indigo sky and a distant Earth.](assets/lunar-lander-social.jpg)

# Lunar Lander

A precision flying game for NetBBS. A small spacecraft, a dwindling fuel supply,
and a very unforgiving Moon — drawn in a richly colored ANSI terminal.

Read the drift. Watch the fuel. Make both feet count.

Guide a fragile lander between lunar ridges, manage your descent, and settle
onto an illuminated pad. Every correction costs fuel; every landing earns its
place.

**Status: design and planning.** The game is not playable yet. The banner is
concept art for the project. Implementation and acceptance status will be
recorded in the phase trackers linked from the
[design and delivery plan](docs/design.md).

The flight plan includes:

- Rich ANSI landscapes with stars, a distant Earth, and illuminated landing pads.
- Deterministic lunar physics, fuel management, and precise landing checks.
- A training basin, three authored challenges, and a seeded daily challenge.
- Persistent pilot records and leaderboards for completed safe landings.
- Native NetBBS play at 80×24 and larger, with more scenery at 132×50.

Planned runtime delivery is a single `lunar_lander.py` file for Python 3.11+,
using only the standard library and suitable for vendoring in NetBBS.
NetBBS's existing native door API is the integration contract; Lunar Lander
does not require changes to it.

The [social banner](assets/lunar-lander-social.jpg) is also ready for the
repository's GitHub social preview. See the [artwork notes](assets/README.md)
for the generation prompt and upload instructions.

[BSD 2-Clause licensed](LICENSE).
