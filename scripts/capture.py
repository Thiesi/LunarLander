"""Development-only PNG/ANSI capture; PNG export requires Pillow (not the game)."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lunar_lander as ll


def render_canvas(canvas):
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new("RGB", ((canvas.width + 1) * 10, canvas.height * 20), ll.rgb(0))
    draw = ImageDraw.Draw(image)
    font = None
    for path in ("C:/Windows/Fonts/consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"):
        if Path(path).is_file():
            font = ImageFont.truetype(path, 16)
            break
    if font is None:
        font = ImageFont.load_default()
    for y, row in enumerate(canvas.cells):
        for x, (char, fg, bg) in enumerate(row):
            draw.rectangle((x * 10, y * 20, x * 10 + 9, y * 20 + 19), fill=ll.rgb(bg))
            if char in ll.QUADRANTS[1:]:
                mask = ll.QUADRANTS.index(char)
                for bit, (qx, qy) in enumerate(((0, 0), (5, 0), (0, 10), (5, 10))):
                    if mask >> bit & 1:
                        draw.rectangle((x * 10 + qx, y * 20 + qy, x * 10 + qx + 4, y * 20 + qy + 9), fill=ll.rgb(fg))
            elif char.strip():
                draw.text((x * 10, y * 20), char, font=font, fill=ll.rgb(fg))
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=80)
    parser.add_argument("--height", type=int, default=24)
    parser.add_argument("--mode", choices=("menu", "flying", "help", "paused", "debrief", *ll.SCENE_SECONDS), default="flying")
    parser.add_argument("--scene-time", type=float, default=1)
    parser.add_argument("--angle", type=float, default=0)
    parser.add_argument("--gif", action="store_true", help="Export a complete scene at 10 fps")
    parser.add_argument("--color", choices=("16", "256", "truecolor"), default="truecolor")
    parser.add_argument("--ascii", action="store_true")
    parser.add_argument("--pixels", choices=("half", "quad"), default="quad")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    display = ll.Display(ll.Host(args.width, args.height, args.color, not args.ascii, pixels=args.pixels))
    flight = ll.training()
    flight.throttle = .7
    flight.angle = args.angle
    if args.mode == "crash":
        flight.reason = "Hard impact: reduce vertical speed to 3 m/s or less."
    canvas = display.draw(flight, args.mode, scene_age=args.scene_time)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".ans").write_bytes(display.encode(canvas).encode("utf-8"))
    if args.gif:
        frames = [render_canvas(display.draw(flight, args.mode, scene_age=n / 10))
                  # The splash's last second and a half is its hold under the prompt.
                  for n in range(int(ll.SCENE_SECONDS.get(args.mode, 3) * 10) + (15 if args.mode == "splash" else 0))]
        frames[0].save(args.output, save_all=True, append_images=frames[1:], duration=100, loop=0)
    else:
        render_canvas(canvas).save(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
