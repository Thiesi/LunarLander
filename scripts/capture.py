"""Development-only PNG/ANSI capture; PNG export requires Pillow (not the game).

A capture shows what the caller's terminal is sent: with `--color 256` or
`--color 16` the picture is drawn from the palette codes on the wire, shade
blocks and all, so a limited palette can be judged as well as truecolor."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lunar_lander as ll

CELL = (10, 20)
# Glyphs drawn as exact rectangles (left, top, right, bottom of the cell), so
# scenery has no seams whatever the font: half blocks and the sparkline's eighths.
BLOCKS = {"▀": (0, 0, 1, .5), "▄": (0, .5, 1, 1), "█": (0, 0, 1, 1), "▌": (0, 0, .5, 1), "▐": (.5, 0, 1, 1),
          **{glyph: (0, 1 - (n + 1) / 8, 1, 1) for n, glyph in enumerate("▁▂▃▄▅▆▇")}}
SHADE = dict(zip(ll.SHADES, (.25, .5, .75)))


def palette(depth: str):
    """How a wire cell's colors read as RGB: the colors themselves in
    truecolor, the palette's entries in 256 or sixteen colors."""
    if depth == "truecolor":
        return ll.rgb
    table = {swatch[0]: swatch[1] for swatch in ll._swatches(depth)}
    table.update(enumerate(ll._VGA))  # a 256-color terminal's first sixteen
    return table.__getitem__


def render_canvas(canvas, display=None):
    """The canvas as an image. With a display, as that display sends it."""
    from PIL import Image, ImageDraw, ImageFont
    depth = display.host.color if display is not None else "truecolor"
    cells = display.wire(canvas) if display is not None else canvas.cells
    tone = palette(depth)
    width, height = CELL
    image = Image.new("RGB", ((canvas.width + 1) * width, canvas.height * height), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = None
    for path in ("C:/Windows/Fonts/consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"):
        if Path(path).is_file():
            font = ImageFont.truetype(path, 16)
            break
    if font is None:
        font = ImageFont.load_default()
    for y, row in enumerate(cells):
        for x, (char, fg, bg) in enumerate(row):
            left, top = x * width, y * height
            paper = tone(bg)
            draw.rectangle((left, top, left + width - 1, top + height - 1), fill=paper)
            if not char.strip():
                continue
            ink = tone(fg)
            if char in ll.QUADRANTS[1:] and char not in BLOCKS:
                mask = ll.QUADRANTS.index(char)
                for bit, (qx, qy) in enumerate(((0, 0), (5, 0), (0, 10), (5, 10))):
                    if mask >> bit & 1:
                        draw.rectangle((left + qx, top + qy, left + qx + 4, top + qy + 9), fill=ink)
            elif char in BLOCKS:
                a, b, c, d = BLOCKS[char]
                draw.rectangle((left + a * width, top + b * height, left + c * width - 1, top + d * height - 1),
                               fill=ink)
            elif char in SHADE:
                # A fine dot pattern, as the eye mixes it: the two colors by area, in linear light.
                share = SHADE[char]
                mixed = [ll._linear(i) * share + ll._linear(p) * (1 - share) for i, p in zip(ink, paper)]
                draw.rectangle((left, top, left + width - 1, top + height - 1), fill=tuple(
                    round(255 * (v * 12.92 if v <= .0031308 else 1.055 * v ** (1 / 2.4) - .055)) for v in mixed))
            else:
                draw.text((left, top), char, font=font, fill=ink)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=80)
    parser.add_argument("--height", type=int, default=24)
    parser.add_argument("--mode", choices=("menu", "record", "flying", "help", "paused", "debrief", "scores",
                                           "confirm", *ll.SCENE_SECONDS), default="flying")
    parser.add_argument("--scene-time", type=float, default=1)
    parser.add_argument("--angle", type=float, default=0)
    parser.add_argument("--altitude", type=float, help="Metres above the pad, instead of the start")
    parser.add_argument("--gif", action="store_true", help="Export a complete scene at 10 fps")
    parser.add_argument("--color", choices=("16", "256", "truecolor"), default="truecolor")
    parser.add_argument("--ascii", action="store_true")
    parser.add_argument("--pixels", choices=("half", "quad"), default="quad")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    display = ll.Display(ll.Host(args.width, args.height, args.color, not args.ascii, pixels=args.pixels))
    display.tagline = ll.TAGLINES[0]  # captures stay reproducible
    flight = ll.training()
    flight.throttle = .7
    flight.angle = args.angle
    if args.altitude is not None:
        flight.y, flight.vy = flight.terrain.pad.height + 3 + args.altitude, -2.4
    if args.mode in ("crash", "debrief"):
        flight.status = "crashed"
        flight.reason = "Hard impact: reduce vertical speed to 3 m/s or less."
    canvas = display.draw(flight, args.mode, scene_age=args.scene_time)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".ans").write_bytes(display.encode(canvas).encode("utf-8"))
    if args.gif:
        frames = [render_canvas(display.draw(flight, args.mode, scene_age=n / 10), display)
                  # The splash's last second and a half is its hold under the prompt.
                  for n in range(int(ll.SCENE_SECONDS.get(args.mode, 3) * 10) + (15 if args.mode == "splash" else 0))]
        frames[0].save(args.output, save_all=True, append_images=frames[1:], duration=100, loop=0)
    else:
        render_canvas(canvas, display).save(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
