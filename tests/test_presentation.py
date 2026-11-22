from pathlib import Path
import tempfile
import unittest

import lunar_lander as ll
from test_career import fly


def text(canvas, rows=None):
    return "\n".join("".join(cell[0] for cell in canvas.cells[row]) for row in (rows or range(canvas.height)))


SKY, INDIGO, ROCK, GOLD, LAMP = (3, 5, 14), (40, 46, 80), (118, 124, 142), (248, 204, 96), (130, 250, 255)


def bucket(color):
    return tuple(c >> 3 for c in color)


class PaletteTests(unittest.TestCase):
    """What a 256- or sixteen-color terminal is sent for the night's colors."""

    def test_the_nights_two_families(self):
        for color, family in ((SKY, "grey"), (INDIGO, "blue"), ((24, 24, 54), "blue"), (ROCK, "grey"),
                              ((74, 82, 112), "grey"), (GOLD, None), (LAMP, None), ((30, 86, 178), None),
                              ((204, 66, 42), None)):
            with self.subTest(color=color):
                self.assertEqual(ll.night(color), family)

    def test_256_colors_tint_an_indigo_and_keep_a_grey_flat(self):
        glyph, fg, bg = ll.blend(bucket(INDIGO), "256")
        self.assertIn(glyph, ll.SHADES)
        # A blue and a grey of about one lightness: a tint, with next to no grain.
        self.assertIn(fg, ll._BLUES256)
        self.assertTrue(bg == 16 or 232 <= bg <= 255, bg)
        swatches = {swatch[0]: swatch for swatch in ll._swatches("256")}
        self.assertLess(abs(swatches[fg][4] - swatches[bg][4]), 12)
        for color in (ROCK, SKY, (204, 210, 220)):
            glyph, _, bg = ll.blend(bucket(color), "256")
            self.assertEqual(glyph, " ")
            self.assertTrue(bg == 16 or bg == 231 or 232 <= bg <= 255, (color, bg))
        # A dark indigo is never a teal or a loud navy, edge or fill.
        self.assertTrue(232 <= ll.xterm256((46, 52, 88)) <= 255)

    def test_sixteen_colors_shade_between_their_greys_and_blues(self):
        self.assertEqual(ll.blend(bucket(SKY), "16"), (" ", 0, 0))
        self.assertEqual(ll.blend(bucket(INDIGO), "16"), ("░", 4, 0))  # a quarter blue: never a field of it
        tones = [ll.blend(bucket((v, v + 4, v + 16)), "16") for v in range(30, 230, 10)]
        self.assertGreaterEqual(len(set(tones)), 8, "a ramp of rock tones, not four greys")
        for glyph, fg, bg in tones:
            self.assertIn(glyph, " █" + ll.SHADES)
            self.assertLessEqual({fg, bg}, {0, 7, 8, 15})
        # Brighter rock never comes out darker.
        levels = [next(level for level, cell in ll._ramp16("grey") if cell == tone) for tone in tones]
        self.assertEqual(levels, sorted(levels))

    def test_a_color_with_a_hue_takes_its_one_nearest(self):
        for depth in ("256", "16"):
            for color in (GOLD, LAMP, (204, 66, 42)):
                with self.subTest(depth=depth, color=color):
                    glyph, fg, bg = ll.blend(bucket(color), depth)
                    self.assertIn(glyph, " █")
        self.assertEqual(ll.ansi16(GOLD) % 8, 3)
        self.assertEqual(ll.ansi16(LAMP) % 8, 6)
        # The chosen row's bar is a palette role: blue in sixteen colors, navy in 256.
        self.assertEqual((ll.code_of(ll.HIGHLIGHT, "16"), ll.code_of(ll.HIGHLIGHT, "256")), (4, 17))

    def test_only_flat_scenery_is_shaded(self):
        flight = ll.training()
        for mode in ("flying", "menu", "debrief", "help", "splash"):
            for depth in ("256", "16"):
                with self.subTest(mode=mode, depth=depth):
                    display = ll.Display(ll.Host(80, 24, depth))
                    canvas = display.draw(flight, mode, scene_age=5.5)
                    shaded = 0
                    for cells, marks, sent in zip(canvas.cells, canvas.soft, display.wire(canvas)):
                        for cell, mark, (glyph, ink, paper) in zip(cells, marks, sent):
                            if glyph in ll.SHADES:
                                shaded += 1
                                self.assertTrue(mark, "a shade block only where blit laid scenery")
                            if depth == "16" and glyph not in ll.PIXEL_GLYPHS:
                                self.assertNotEqual(ink, paper, (cell, "writing never vanishes into its ground"))
                    if mode in ("flying", "menu", "splash"):
                        self.assertGreater(shaded, 20)
        # ASCII glyphs get no shade blocks, and truecolor is sent as drawn.
        display = ll.Display(ll.Host(80, 24, "256", False))
        canvas = display.draw(flight)
        self.assertFalse({cell[0] for row in display.wire(canvas) for cell in row} & set(ll.SHADES))
        self.assertTrue(display.encode(canvas).isascii())
        display = ll.Display(ll.Host(80, 24, "truecolor"))
        canvas = display.draw(flight)
        self.assertIs(display.wire(canvas), canvas.cells)

    def test_cp437_has_every_glyph_the_limited_palettes_send(self):
        host = ll.Host(80, 24, "16", True, charset="cp437", encoding="cp437")
        display = ll.Display(host)
        for mode in ("flying", "menu", "debrief", "splash", "crash"):
            with self.subTest(mode=mode):
                flight = ll.training()
                flight.fuel, flight.vy, flight.vx, flight.angle = 4, -6, 3, 20
                sent = "".join(cell[0] for row in display.wire(display.draw(flight, mode, scene_age=3)) for cell in row)
                sent.translate(ll.CP437_GLYPHS).encode("cp437")  # raises on a glyph CP437 lacks


class CockpitTests(unittest.TestCase):
    def test_one_header_row_the_view_and_four_rows_of_instruments(self):
        for size in ((80, 24), (132, 50)):
            with self.subTest(size=size):
                canvas = ll.Display(ll.Host(*size)).draw(ll.training())
                self.assertIn("FLIGHT TRAINING BASIN", text(canvas, range(ll.HEAD_ROWS)))
                self.assertIn("T+", text(canvas, range(ll.HEAD_ROWS)))
                view = range(ll.HEAD_ROWS, canvas.height - ll.PANEL_ROWS)
                self.assertEqual(len(view), size[1] - 5)
                # The view is scenery from edge to edge; the header and instruments are not.
                self.assertTrue(all(sum(canvas.soft[row]) > canvas.width * .5 for row in view))
                self.assertFalse(any(sum(canvas.soft[row]) for row in range(canvas.height) if row not in view))
                labels = text(canvas, [canvas.height - ll.PANEL_ROWS])
                for label in ("ALTITUDE", "VERTICAL ≤3", "DRIFT ≤2", "TILT ≤10°", "THRUST", "FUEL"):
                    self.assertIn(label, labels)
        ascii_labels = text(ll.Display(ll.Host(unicode=False)).draw(ll.training()), [24 - ll.PANEL_ROWS])
        for label in ("VERTICAL <=3", "DRIFT <=2", "TILT <=10"):
            self.assertIn(label, ascii_labels)

    def bars(self, flight, **host):
        canvas = ll.Display(ll.Host(**host)).draw(flight)
        return canvas, canvas.cells[canvas.height - ll.PANEL_ROWS + 2]

    def test_a_needle_shows_which_way_and_a_word_says_too_much(self):
        flight = ll.training()
        positions = {}
        for vx in (-3, 0, 3):
            flight.vx = vx
            canvas, bars = self.bars(flight)
            row = "".join(cell[0] for cell in bars)
            start = (canvas.width - 1) // 6 * 2  # the drift gauge is the third of six
            positions[vx] = row.index("█", start)
        self.assertLess(positions[-3], positions[0])
        self.assertLess(positions[0], positions[3])
        readings = text(canvas, [canvas.height - ll.PANEL_ROWS + 1])
        self.assertIn("WIDE", readings)
        # A climb breaks no limit, however fast.
        flight.vx, flight.vy = 0, 6
        self.assertNotIn("FAST", text(self.bars(flight)[0], [24 - ll.PANEL_ROWS + 1]))
        flight.vy = -6
        self.assertIn("FAST", text(self.bars(flight)[0], [24 - ll.PANEL_ROWS + 1]))

    def test_a_gauge_is_an_odd_number_of_lamps_so_a_needle_has_a_centre(self):
        for width in (80, 81, 100, 132, 133):
            with self.subTest(width=width):
                flight = ll.training()
                flight.vx = flight.angle = 0
                canvas, bars = self.bars(flight, width=width, height=30)
                each = (canvas.width - 1) // 6
                for gauge in range(6):
                    lamps = [cell for cell in bars[1 + gauge * each:1 + (gauge + 1) * each] if cell[0] in "■█┃"]
                    self.assertEqual(len(lamps), each - 2 if each % 2 else each - 3)
                    self.assertEqual(len(lamps) % 2, 1)
                # Level and still, the drift and tilt needles sit on the middle lamp.
                for gauge in (2, 3):
                    lamps = [cell[0] for cell in bars[1 + gauge * each:1 + (gauge + 1) * each] if cell[0] in "■█"]
                    self.assertEqual(lamps.index("█"), len(lamps) // 2)

    def test_the_view_says_what_a_hundred_metres_is(self):
        display, flight = ll.Display(ll.Host()), ll.training()
        row = text(display.draw(flight), [ll.HEAD_ROWS])
        self.assertIn("100 m", row)
        wide = row.count("─")
        # Low over the pad the camera closes in, and the same hundred metres is a longer bar.
        flight.y = flight.terrain.pad.height + 3 + 20
        for _ in range(40):
            row = text(display.draw(flight), [ll.HEAD_ROWS])
        self.assertGreater(row.count("─"), wide * 2)

    def test_a_pad_out_of_the_window_is_pointed_to(self):
        display, flight = ll.Display(ll.Host()), ll.training()
        flight.x, flight.y = 900, flight.terrain.height(900) + 3 + 30  # low, and 600 m east of the pad
        for _ in range(40):
            canvas = display.draw(flight)
        view = text(canvas, range(ll.HEAD_ROWS, canvas.height - ll.PANEL_ROWS))
        self.assertIn("◄ PAD 600 m", view)
        flight.x = 300
        for _ in range(40):
            canvas = display.draw(flight)
        self.assertNotIn("◄", text(canvas))
        self.assertIn("PAD", text(canvas, range(ll.HEAD_ROWS, canvas.height - ll.PANEL_ROWS)))

    def test_the_header_names_the_bbs_as_long_as_it_can(self):
        # The longest form the row has room for; a name too long for any of them is left to the dialog.
        for bbs, expected in (("NetBBS", "[P] Pause  [?] Manual  [Q] Return to NetBBS"),
                              ("Moonbase 7", "[P] [?]  [Q] Return to Moonbase 7"),
                              ("The Lunar Receiving Lab", "[P] Pause  [?] Help  [Q] Leave")):
            with self.subTest(bbs=bbs):
                header = text(ll.Display(ll.Host(bbs=bbs)).draw(ll.training()), [0])
                self.assertIn(expected, header)
                self.assertIn("FLIGHT TRAINING BASIN", header)
        self.assertIn("[P] Pause  [?] Flight manual  [Q] Return to NetBBS",
                      text(ll.Display(ll.Host(132, 50)).draw(ll.training()), [0]))

    def test_the_craft_casts_a_shadow_as_it_comes_down(self):
        plate = (224, 230, 240)
        for altitude, cast in ((12, True), (200, False)):
            with self.subTest(altitude=altitude):
                display, flight = ll.Display(ll.Host(80, 24)), ll.training()
                flight.y = flight.terrain.pad.height + 3 + altitude
                for _ in range(40):
                    canvas = display.draw(flight)
                colors = {color for row in canvas.cells for cell in row for color in cell[1:]}
                self.assertIn(plate, colors)  # the pad's plate, in the light at its ends
                # Under the craft it is darker by how near the craft is.
                shadow = ll.scale(plate, 1 - .5 * (1 - altitude / 90))
                self.assertEqual(shadow in colors, cast)


class DebriefTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.records = ll.Records(Path(self.temp.name) / "pilots.db")
        self.addCleanup(self.records.close)
        self.game = ll.Game(ll.Host(node="n", user=7, handle="Nib"), self.records)
        self.game.scenes = False

    def debrief(self, **host):
        game = self.game
        deck = ll.Deck(game.chapter, game.bests, True, game.award, tuple(game.unlocked), game.logbook())
        return ll.Display(ll.Host(**host)).draw(game.flight, "debrief", mission=game.mission,
                                                record_note=game.record_note, catalog=game.missions, deck=deck)

    def test_a_score_is_shown_between_the_medals_and_by_its_parts(self):
        fly(self.game, "2", vy=-1.5, fuel=40)
        game = self.game
        score = game.flight.score(game.mission.difficulty)
        display = ll.Display(ll.Host())
        parts = display.score_parts(game.mission, game.flight, score)
        numbers = [int(part) for part, _ in parts if part.strip().lstrip("+").isdigit()]
        self.assertEqual(numbers[0], 1000 * game.mission.difficulty)
        self.assertEqual(sum(numbers), score)
        track = "".join(part for part, _ in display.score_track(game.mission, score))
        self.assertIn(f"{score} of {2000 * game.mission.difficulty}", track)
        self.assertEqual(track.count("┃"), 2)  # the silver and gold lines
        screen = text(self.debrief(width=80, height=30))
        for words in ("SCORE ", " landing  +", " fuel  +", " soft  +", " steady", f"{game.award.medal} MEDAL"):
            self.assertIn(words, screen)

    def test_a_reading_past_its_limit_is_red_and_fills_past_the_tick(self):
        display = ll.Display(ll.Host())
        safe = display.reading("Vertical", "-1.50 m/s", .5)
        over = display.reading("Vertical", "-9.00 m/s", 3.0)
        self.assertEqual((safe[1][1], over[1][1]), (6, 8))
        lamps = lambda parts: [color for glyph, color in parts[2:] if glyph == "■" and color != ll.TRACK]
        self.assertEqual(len(lamps(safe)), 4)
        self.assertEqual(len(lamps(over)), 11)  # twelve less the tick
        self.assertTrue(all(color == ll.rgb(8) for color in lamps(over)))
        self.assertEqual(sum(1 for glyph, _ in over if glyph == "┃"), 1)

    def test_the_trace_is_drawn_in_color(self):
        fly(self.game, "2")
        flight = self.game.flight
        flight.trace = [(180 - 3 * n, 85 - n * 0.5) for n in range(60)]
        lines = ll.Display(ll.Host()).trace_lines(flight)
        self.assertEqual([line[0][0] for line in lines[:2]], ["ALT  ", "BURN "])
        self.assertTrue(all(isinstance(color, tuple) for line in lines[:2] for _, color in line[1:]))

    def test_every_debrief_fits_its_screen(self):
        fly(self.game, "2", vy=-1.5, fuel=40)
        self.game.flight.trace = [(180 - 3 * n, 85 - n * 0.5) for n in range(60)]
        for size in ((80, 24), (80, 30), (132, 50)):
            with self.subTest(size=size):
                canvas = self.debrief(width=size[0], height=size[1])
                screen = text(canvas)
                for words in ("CONTACT LIGHT", "[M] Mission briefing", "Return to NetBBS", "Vertical -1.5"):
                    self.assertIn(words, screen)
                # The card's bottom edge is on the screen.
                self.assertIn("╰", screen)


class SceneTests(unittest.TestCase):
    def test_a_crash_leaves_a_wreck_that_smokes(self):
        self.assertGreater(len(ll.wreck_sprite()), 40)
        self.assertNotEqual(ll.smoke(2.0, 16), ll.smoke(2.5, 16))
        self.assertTrue(all(y <= 0 for _, y in ll.smoke(3.0, 16)))
        display = ll.Display(ll.Host())
        flight = ll.training()
        flight.status, flight.reason = "crashed", "Hard impact: reduce vertical speed to 3 m/s or less."
        held = [display.draw(flight, "crash", scene_age=age).cells for age in (4.0, 4.5)]
        self.assertNotEqual(*held)  # the hold is not a still: the smoke drifts

    def test_a_lone_chevron_turns_gold(self):
        colors = {color for color, _ in ll.insignia(1, 6, 1.0).values()}
        self.assertNotIn((255, 255, 255), colors)
        self.assertIn((255, 255, 255), {color for color, _ in ll.insignia(1, 6, .4).values()})

    def test_a_caption_is_never_lost_in_a_burst(self):
        award = ll.Award(ll.missions()[1], 1800, "GOLD", "GOLD", True,
                         ll.Career(3, "PILOT", 1, "FLIGHT OFFICER", 8, 1, 1, 15), "PILOT")
        for age in (1.0, 1.4, 1.8, 2.2, 2.6, 3.0, 3.4):
            canvas = ll.Display(ll.Host()).draw(ll.training(), "promotion", scene_age=age, deck=ll.Deck(award=award))
            for row in (1, 3):
                for char, fg, bg in canvas.cells[row]:
                    if char.isalpha():
                        self.assertLess(max(ll.rgb(bg)), 80, (age, row, char))


class TiltTests(unittest.TestCase):
    """A craft is redrawn for each tilt: nothing breaks off, nothing that names it is lost."""

    def pieces(self, pixels):
        left, count = set(pixels), 0
        while left:
            count += 1
            stack = [left.pop()]
            while stack:
                x, y = stack.pop()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if (x + dx, y + dy) in left:
                            left.remove((x + dx, y + dy))
                            stack.append((x + dx, y + dy))
        return count

    def test_a_tilted_craft_stays_in_one_piece_with_its_windows(self):
        for craft in ("lm", "altair", "hopper"):
            for size in ("small", "medium"):
                for across in (1, 2):
                    upright = ll.lander_roles(0, 0, size=size, across=across, craft=craft)
                    self.assertEqual(self.pieces(upright), 1)
                    step = ll.CRAFT[craft][4]
                    for n in range(1, int(60 / step) + 1):
                        for angle in (step * n, -step * n):
                            with self.subTest(craft=craft, size=size, across=across, angle=angle):
                                roles = ll.lander_roles(angle, 0, size=size, across=across, craft=craft)
                                self.assertEqual(self.pieces(roles), 1, "a leg or a pad came off")
                                for role in set(upright.values()) & ll._KEPT:
                                    self.assertIn(role, roles.values())
                                # About as many pixels as upright: nothing smeared out or lost.
                                self.assertLess(abs(len(roles) - len(upright)), len(upright) * .25)

    def test_a_leg_is_a_line_at_every_tilt(self):
        for across in (1, 2):
            for angle in range(10, 61, 10):
                with self.subTest(across=across, angle=angle):
                    roles = ll.lander_roles(angle, 0, across=across)
                    legs = {point for point, role in roles.items() if role in ll._THIN}
                    hull = set(roles) - legs
                    # Each leg pixel touches another, or the hull it hangs from.
                    for x, y in legs:
                        self.assertTrue(any((x + dx, y + dy) in legs | hull for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                                            if (dx, dy) != (0, 0)))
                    self.assertLessEqual(self.pieces(legs), 2)

    def test_each_tilt_is_drawn_once(self):
        self.assertIs(ll._hull("lm", "small", 2, 20), ll._hull("lm", "small", 2, 20))
        first = ll.lander_roles(20, 0, across=2)
        first.clear()  # the copy handed out, not the drawing
        self.assertTrue(ll.lander_roles(20, 0, across=2))
        # The plume turns with the hull and trails away from the lean.
        burning = ll.lander_roles(30, 1)
        self.assertTrue(set(ll.lander_roles(30, 0).items()) <= set(burning.items()))
        self.assertLess(min(x for (x, _), role in burning.items() if role in ll._FLAME), 0)


class CloseInTests(unittest.TestCase):
    def test_three_scales_each_left_later_than_entered(self):
        display, flight = ll.Display(ll.Host()), ll.training()
        ground = flight.terrain.pad.height + 3
        flight.steps = 1  # under way: the first frame of a flight takes its scale outright
        seen = []
        for altitude in (200, 101, 99, 110, 121, 60, 31, 29, 38, 43, 110, 125):
            flight.y = ground + altitude
            display.draw(flight)
            seen.append(display._zoom)
        self.assertEqual(seen, [1000, 1000, 400, 400, 1000, 400, 400, 200, 200, 400, 400, 1000])
        # A new flight low over the pad starts close in.
        fresh = ll.training()
        fresh.y = ground + 20
        display.draw(fresh)
        self.assertEqual(display._zoom, 200)

    def test_the_feet_are_marked_where_they_really_are(self):
        white = (255, 255, 255)
        for altitude, marked in ((12, True), (39, True), (60, False)):
            with self.subTest(altitude=altitude):
                display, flight = ll.Display(ll.Host()), ll.training()
                flight.y = flight.terrain.pad.height + 3 + altitude
                for _ in range(40):
                    canvas = display.draw(flight, mission=ll.missions()[1])
                marks = sum(1 for row in canvas.cells for cell in row if white in cell[1:])
                self.assertEqual(marks > 0, marked)
                if marked:
                    self.assertLessEqual(marks, 2)  # two feet, a cell or two between them

    def test_close_in_there_is_still_sky(self):
        mission = ll.missions()[1]
        display, flight = ll.Display(ll.Host()), mission.launch()
        flight.x = (flight.terrain.pad.left + flight.terrain.pad.right) / 2
        flight.y = flight.terrain.pad.height + 3 + 10
        for _ in range(40):
            canvas = display.draw(flight, mission=mission)
        top = canvas.cells[ll.HEAD_ROWS + 1]
        self.assertGreater(sum(1 for cell in top if max(ll.rgb(cell[2])) < 40), canvas.width // 2)


class TrainingAidTests(unittest.TestCase):
    def test_the_forecast_agrees_with_the_flight(self):
        for throttle, angle in ((0, 0), (.3, 10), (.5, -20)):
            with self.subTest(throttle=throttle, angle=angle):
                flight = ll.training()
                flight.throttle, flight.angle = throttle, angle
                points, lands = ll.forecast(flight)
                self.assertTrue(lands)
                x, y, vx, vy = points[-1]
                while flight.status == "flying":
                    flight.step()
                self.assertLess(abs(x - flight.x), 6)
                self.assertLess(abs(vy - flight.vy), 1.5)
                self.assertLess(abs(vx - flight.vx), 1.5)
        climbing = ll.training()
        climbing.throttle = 1
        self.assertFalse(ll.forecast(climbing)[1])

    def test_only_training_and_a_cadet_simulator_show_the_path(self):
        display = ll.Display(ll.Host())
        training, ranked = ll.missions()[0], ll.missions()[1]
        for deck, mission, shown in ((ll.Deck(), training, True), (ll.Deck(), ranked, False),
                                     (ll.Deck(kind="sim", program=ll.ProgramView(preset="cadet")), ranked, True),
                                     (ll.Deck(kind="sim", program=ll.ProgramView(preset="astronaut")), ranked, False),
                                     (ll.Deck(kind="real", program=ll.ProgramView(preset="cadet")), ranked, False),
                                     (ll.Deck(kind="replay"), training, False)):
            with self.subTest(kind=deck.kind, mission=mission.key):
                display.deck = deck
                self.assertEqual(display.assisted(mission), shown)
        aided = text(ll.Display(ll.Host()).draw(training.launch(), mission=training))
        unaided = text(ll.Display(ll.Host()).draw(ranked.launch(), mission=ranked))
        for mark in ("×", "PATH training aid"):
            self.assertIn(mark, aided)
            self.assertNotIn(mark, unaided)
        self.assertIn(" m/s ", aided.split("×", 1)[1][:10])  # how fast it would come down
        ascii_aided = text(ll.Display(ll.Host(unicode=False)).draw(training.launch(), mission=training))
        self.assertTrue(ascii_aided.isascii())

    def cue(self, flight, deck):
        return "Engine off" in text(ll.Display(ll.Host()).draw(flight, deck=deck))

    def test_a_first_flight_is_told_how_to_light_the_engine(self):
        new = ll.Deck(logbook=ll.Logbook(counters={"last_seen": 1.0}))
        flown = ll.Deck(logbook=ll.Logbook(counters={"crashes": 1}))
        self.assertTrue(self.cue(ll.training(), new))
        self.assertFalse(self.cue(ll.training(), flown))
        self.assertFalse(self.cue(ll.training(), ll.Deck()))  # nothing known of the pilot
        burning = ll.training()
        burning.throttle = .1
        self.assertFalse(self.cue(burning, new))
        late = ll.training()
        late.elapsed = 13
        self.assertFalse(self.cue(late, new))
        screen = text(ll.Display(ll.Host()).draw(ll.training(), deck=new))
        self.assertIn("[W] or [↑] throttles up, [9] is full thrust", screen)

    def test_the_manual_gives_the_tilt_of_the_craft(self):
        for craft, degrees in (("lm", 10), ("surveyor", 15), ("altair", 5), ("hopper", 10)):
            with self.subTest(craft=craft):
                screen = text(ll.Display(ll.Host()).draw(ll.training(), "help", deck=ll.Deck(craft=craft)))
                self.assertIn(f"Tilt +/-{degrees} degrees", screen)
        # In flight it is the craft being flown, whatever is chosen for the next.
        mission = ll.in_craft(ll.missions()[1], "surveyor")
        screen = text(ll.Display(ll.Host()).draw(mission.launch(), "help", mission=mission))
        self.assertIn("Tilt +/-15 degrees", screen)


class ClassicColorTests(unittest.TestCase):
    """The sixteen colors of a classic BBS: bold for a bright foreground, eight backgrounds."""

    def host(self, **fields):
        return ll.Host(80, 24, "16", True, charset="cp437", encoding="cp437", source="classic", **fields)

    def test_only_what_every_ansi_terminal_knows(self):
        for mode in ("flying", "menu", "debrief", "help", "splash", "medal", "crash"):
            with self.subTest(mode=mode):
                display = ll.Display(self.host())
                flight = ll.training()
                flight.fuel = 4  # the amber and red chips, too
                canvas = display.draw(flight, mode, scene_age=2)
                self.assertTrue(all(paper < 8 for row in display.wire(canvas) for _, _, paper in row))
                frame = display.encode(canvas)
                used = {int(n) for sequence in ll.re.findall(r"\x1b\[([0-9;]*)m", frame) for n in sequence.split(";")}
                self.assertLessEqual(used, {0, 1, *range(30, 38), *range(40, 48)})
                self.assertIn(1, used)
                self.assertEqual(display.encode(canvas), "")

    def test_bold_is_set_for_a_bright_ink_and_reset_for_a_plain_one(self):
        display = ll.Display(self.host())
        canvas = ll.Canvas(80, 24)
        canvas.text(0, 0, "A", 7, 0)   # white: bright
        canvas.text(1, 0, "B", 9, 0)   # subdued: plain cyan
        canvas.text(2, 0, "C", 5, 0)   # gold: bright yellow
        frame = display.encode(canvas)
        self.assertRegex(frame[:frame.index("A")], r"\x1b\[0;1;37;40m$")
        self.assertIn("A\x1b[0;36;40mB\x1b[1;33mC", frame)

    def test_a_bright_ground_is_turned_inside_out_or_dimmed(self):
        self.assertEqual(ll.eight_grounds((" ", 0, 15)), ("█", 15, 0))
        self.assertEqual(ll.eight_grounds(("▀", 4, 15)), ("▄", 15, 4))
        self.assertEqual(ll.eight_grounds(("░", 7, 15)), ("▓", 15, 7))
        self.assertEqual(ll.eight_grounds(("x", 0, 11)), ("x", 0, 3))  # dark writing on amber: on brown
        self.assertEqual(ll.eight_grounds(("▀", 12, 15)), ("▀", 12, 7))
        self.assertEqual(ll.eight_grounds(("▀", 9, 3)), ("▀", 9, 3))

    def test_netbbs_callers_keep_the_bright_codes(self):
        display = ll.Display(ll.Host(80, 24, "16", True, source="netbbs"))
        frame = display.encode(display.draw(ll.training()))
        self.assertRegex(frame, r"\x1b\[(?:[0-9;]*;)?9[0-7]")
        self.assertFalse(display.classic)


class InstrumentPanelTests(unittest.TestCase):
    def test_the_altimeter_is_in_large_figures(self):
        mission = ll.on_instruments(ll.missions()[1])
        for host in (ll.Host(80, 24), ll.Host(132, 50), ll.Host(80, 24, "16", False)):
            with self.subTest(size=(host.width, host.height), unicode=host.unicode):
                flight = mission.launch()
                canvas = ll.Display(host).draw(flight, mission=mission)
                screen = text(canvas)
                for words in ("INSTRUMENT APPROACH", "RADAR ALT (m)", "DRIFT / SINK", "PAD BEARING", "SINK", "wide"):
                    self.assertIn(words, screen)
                figures = sum(1 for row in canvas.cells for cell in row if cell[2] == ll.rgb(6))
                self.assertGreater(figures, 60)
                # The figures stay inside their box.
                box = next(row for row in canvas.cells if "RADAR ALT" in "".join(cell[0] for cell in row))
                edge = "".join(cell[0] for cell in box).index("DRIFT / SINK") - 4
                self.assertFalse(any(cell[2] == ll.rgb(6) for row in canvas.cells for cell in row[edge:edge + 2]))

    def test_the_pointer_is_in_its_window_when_the_landing_would_hold(self):
        mission = ll.on_instruments(ll.missions()[1])
        for vx, vy, color in ((0, -2, 6), (1.5, -3, 6), (3, -2, 8), (0, -5, 8)):
            with self.subTest(vx=vx, vy=vy):
                flight = mission.launch()
                flight.vx, flight.vy = vx, vy
                canvas = ll.Display(ll.Host()).draw(flight, mission=mission)
                dots = [cell for row in canvas.cells for cell in row if cell[0] == "●"]
                self.assertEqual([cell[1] for cell in dots], [color])


if __name__ == "__main__":
    unittest.main()
