#!/usr/bin/env python3
"""R9 silkscreen and assembly references (M3-ASSY-R9, build step 9; R9_DECISIONS D-S9-01 ... D-S9-03): the post stage,
after r9_ground.py and its gate. No copper, zone, footprint position or pad edit (asserted by a digest of every copper
item, zone fill and pad, before and after the save).

usage: <KiCad python3> -I m3_design/r9_post.py [--board m3_design/assembly_review/m3.kicad_pcb] [--report out.json]

The whole board-level silkscreen is drawn from nothing (r9_pcb.py kept only R8's ARM / IGN texts, at R8's places):
every board-level silkscreen item is deleted and every footprint field hidden, then, in this order (R8's finish,
m3_design/r8_post.py, on R9's geometry; its placement machinery is imported, not copied):
  1. the SMA jack legends GNSS (J30) and RADIO (J31), on the top just forward of each jack, JACK_VIA_GAP clear of every
     via and with nothing else within JACK_LEGEND_GAP of them (r7_post's pass-3 DFM-06 rule);
  2. J122's plug numbers 1-4 (west to east, the _MIR numbering) as one row of digits on the plug columns, aft or
     forward of the header (put_plug_row), then the legends about one part, each at the free spot nearest that part's
     courtyard and within LEGEND_REACH (6 mm, AGENTS.md; tools/check_r7.legend_subjects gates it): TP30 SAFEBOOT; the
     connector words ARM, IGN, BAT, CAM, SWD, SERVO, PULL, top face first (the black terminals J124 / J121 are told
     apart by them: REQUIREMENTS F8, check_actuators 11); the pin tables of J9 and J2 (tools/check_r7.pin_legends) and
     J122; the arming and fuse notes of J124 and J1;
  3. the terminal pin legends (check_r8.TERMINAL_PINS, drawn by pin: J121 / J124 are renumbered, D-S2-01), each at the
     free spot nearest its own pin whose box (the text's bounding box, check_r8.terminal_legends' measure, D92) has
     that pin as its nearest connector pin by at least OWN_MARGIN, top face first; J1's in the forward-edge strip over
     their pins where the strip has room (R8 fix pass 1). The ownership test, not a hand-cut window, keeps each legend
     on its own pin (D-S9-02);
  4. the revision legend M3-ASSY-R9 and JLC's order-number placeholder JLCJLCJLCJLC (ORDERING), both required;
  5. pin-1 dots beside pad 1 of r5_post.DOT_PARTS (pin1_dots: every one required), then every designator by the R4
     rule (r5_post.designators: >= 1.0 mm text, never over a pad, via or hole or off the board, nearer its own part
     than any other; a crowded one goes on the bottom under its part; one with no such spot is hidden and kept on the
     Fab layer), then R8's courtyard and run-on tests
     on every visible designator (r8_post: ink no nearer another part's courtyard than its own; no text running into
     another within RUN_ON on its line); one that fails is placed again with both tests, or hidden; the run fails if
     one is left;
  6. Fab-layer designators for the assembly drawing (r5_post.fab_refs; fab_clear moves a pair still overlapping apart)
     and the title-block revision.
Any essential legend that does not fit, a terminal legend whose nearest pin is not its own, or a legend about a part
beyond LEGEND_REACH fails the run (check_r7.pin_legends / legend_subjects, check_r8.terminal_legends, duplicate ids).
The stage runs once, on the ground-stage board (it refuses a board that already carries the J9 / J2 pin tables).
Deterministic (fixed KIID seed, no random search, no refill: silkscreen does not touch the fill): a rebuild reproduces
the board byte for byte.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r7  # noqa: E402
import check_r8  # noqa: E402
import r5_post as silk  # noqa: E402
import r7_post  # noqa: E402  (generic placement helpers, frozen with the R7 record)
import r8_post  # noqa: E402  (RunOnSilk, the courtyard / run-on designator pass, the fixed digest; frozen with R8)

REV = 'M3-ASSY-R9'
KIID_SEED = 9909                # r9_pcb 9903, r9_rf 9904, r9_pyro 9905, r9_power 9906, r9_ground 9908, routes 9910-9919
LEGEND_REACH = r7_post.LEGEND_REACH
PORTS = r7_post.PORTS           # J9 CAM 5V GND TX RX (camera-side UART names), J2 SWD 3V3 SWDIO NRST SWCLK GND NC
WORDS = r8_post.WORDS           # J124 ARM, J121 IGN, J1 BAT, J9 CAM, J2 SWD, J122 SERVO, J123 PULL
NOTES = r8_post.NOTES           # J124 2-FUSE-1: ARM LAST, J124: 5A FAST / 2S, J1 BAT LEAD: 15A FUSE
J122_TABLE = 'J122 1:S 2:+ 3:GND'   # each plug's pins (pads 3k+1 / 3k+2 / 3k+3: SERVOn_OUT, RAW_ACT, GND)
TERMINAL_PINS = check_r8.TERMINAL_PINS   # J124 1:BUS1 2:RAW, J121 1:E1- 2:E1+, J1 1:BAT+ .. 4:SW, J123 1:PULL 2:GND
ORDER_MARK = r8_post.ORDER_MARK
OWN_MARGIN = 0.3                # mm: a pin legend's box is this much nearer its own pin than any other connector pin
PIN_REACH = 6.0                 # mm: a pin legend's search window, half size about its pin (both axes)
STRIP_HALF = (2.54, 0.9)        # J1's forward-edge strip window over a pin (R8: J1_STRIP_Y, half sizes)
STRIP_INSET = 1.2               # mm: the strip's centre line from the forward edge (R8: 118 - 116.8)
PLUG_ROWS = (('1', ('1', '2', '3')), ('2', ('4', '5', '6')), ('3', ('7', '8', '9')), ('4', ('10', '11', '12')))
CONNECTOR = check_r8.CONNECTOR


def outline(b):
    """The board outline's extent (mm) from the Edge.Cuts segments' end points (the stroke width left out)."""
    xs, ys = [], []
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() in (pcbnew.SHAPE_T_SEGMENT, pcbnew.SHAPE_T_RECT):
            for p in (d.GetStart(), d.GetEnd()):
                xs.append(silk.mm(p.x))
                ys.append(silk.mm(p.y))
    if not xs or abs(min(xs)) > 1e-6 or abs(min(ys)) > 1e-6:
        raise RuntimeError('R9 silkscreen expects a rectangular outline from (0, 0)')
    return max(xs), max(ys)


def connector_pads(b):
    """(ref, number, (x, y) mm) for every numbered pad of a connector (J*): the set check_r8.terminal_legends ranks."""
    return [(f.GetReference(), p.GetNumber(), (silk.mm(p.GetPosition().x), silk.mm(p.GetPosition().y)))
            for f in b.GetFootprints() if CONNECTOR.match(f.GetReference()) for p in f.Pads() if p.GetNumber()]


def text_box(t):
    """The text's bounding box (mm): check_r8.terminal_legends measures pins to it, not to the ink."""
    r = t.GetBoundingBox()
    return silk.mm(r.GetLeft()), silk.mm(r.GetTop()), silk.mm(r.GetRight()), silk.mm(r.GetBottom())


def owner_margin(box, pads, own):
    """How much nearer the box is to the nearest of the `own` pins than to any other connector pin (mm); negative when
    another pin is as near or nearer (check_r8.terminal_legends' ranking: pad centre to box)."""
    def gap(c):
        return math.hypot(max(box[0] - c[0], c[0] - box[2], 0.0), max(box[1] - c[1], c[1] - box[3], 0.0))
    mine = min(gap(c) for ref, num, c in pads if (ref, num) in own)
    other = min(gap(c) for ref, num, c in pads if (ref, num) not in own)
    return other - mine


def put_pin(b, silks, text, pads, own, near, regions):
    """A pin legend at the free spot nearest `near` (ink box gap) in the first region (box, sides, angles) that has one
    whose text box keeps `own`'s pin(s) nearest by OWN_MARGIN; returns (side, x, y, angle, gap, margin) or None."""
    for region, sides, angles in regions:
        for side in sides:
            s = silks[side]
            t = silk._text(b, text, s.layer, 1.0)
            best = None
            for ang in angles:
                t.SetTextAngleDegrees(ang)
                t.SetPosition(silk.P(0, 0))
                r0, b0 = silk.ink(t), text_box(t)
                x0, y0, x1, y1 = region
                for i in range(int(round((x1 - x0) / 0.1)) + 1):
                    x = x0 + 0.1 * i
                    for j in range(int(round((y1 - y0) / 0.1)) + 1):
                        y = y0 + 0.1 * j
                        r = (r0[0] + x, r0[1] + y, r0[2] + x, r0[3] + y)
                        g = silk._gap(r, (near[0], near[1], near[0], near[1]))
                        if best is not None and g >= best[0]:
                            continue
                        if not s.free(r):
                            continue
                        m = owner_margin((b0[0] + x, b0[1] + y, b0[2] + x, b0[3] + y), pads, own)
                        if m < OWN_MARGIN:
                            continue
                        best = (g, x, y, ang, r, m)
            if best is not None:
                g, x, y, ang, r, m = best
                t.SetTextAngleDegrees(ang)
                t.SetPosition(silk.P(x, y))
                b.Add(t)
                s.add(r)
                return side, round(x, 2), round(y, 2), ang, round(g, 2), round(m, 2)
    return None


PLUG_SLIDE = 0.5               # mm: a plug number may sit this far off its column's centre line (nearest first)


def put_plug_row(b, silks, pads, reach=3.0, step=0.1):
    """J122's plug numbers 1-4 (PLUG_ROWS: the _MIR numbering puts plug 1 west) as one row of digits on one line, each
    on its plug's column (within PLUG_SLIDE of its centre line), aft of the signal row or forward of the GND row, on the
    first face (top, then bottom) and at the first offset where all four are free and each box has its own plug's pins
    nearest by OWN_MARGIN. Returns {plug: (side, x, y, angle, gap, margin)} or None."""
    cols = {plug: [silk.pad(b, 'J122', n) for n in numbers] for plug, numbers in PLUG_ROWS}
    ys = [y for xy in cols.values() for _, y in xy]
    slides = [0.0] + [s_ * k * step for k in range(1, int(round(PLUG_SLIDE / step)) + 1) for s_ in (-1, 1)]
    for side in ('F', 'B'):
        s = silks[side]
        for k in range(int(round(reach / step)) + 1):
            for y in (min(ys) - 1.2 - k * step, max(ys) + 1.2 + k * step):
                spots = {}
                for plug, numbers in PLUG_ROWS:
                    cx = sum(p[0] for p in cols[plug]) / len(cols[plug])
                    for dx in slides:
                        t = silk._text(b, plug, s.layer, 1.0)
                        t.SetPosition(silk.P(cx + dx, y))
                        r, bb = silk.ink(t), text_box(t)
                        m = owner_margin(bb, pads, {('J122', n) for n in numbers})
                        if s.free(r) and m >= OWN_MARGIN and all(silk._gap(r, o[0]) >= silk.GAP
                                                                 for o in spots.values()):
                            spots[plug] = (r, t, cx + dx, m)
                            break
                    else:
                        break
                if len(spots) == len(PLUG_ROWS):
                    out = {}
                    for plug, (r, t, x, m) in spots.items():
                        b.Add(t)
                        s.add(r)
                        g = min(silk._gap(r, (px, py, px, py)) for px, py in cols[plug])
                        out[plug] = (side, round(x, 2), round(y, 2), 0, round(g, 2), round(m, 2))
                    # the row reads as one: no later text between its digits or within RUN_ON of its ends
                    rs = [o[0] for o in spots.values()]
                    s.add((min(r[0] for r in rs), min(r[1] for r in rs), max(r[2] for r in rs), max(r[3] for r in rs)),
                          r8_post.RUN_ON)
                    return out
    return None


DOT_REACH = 1.0                 # mm: a pin-1 dot's box keeps at most this from its pad's box


def pin1_dots(b, silks, step=0.05):
    """R4's pin-1 dot (r5_post.pin1_dots' mark: a filled 0.4 mm dot, outside the package body, on the part's own face)
    beside pad 1 of each r5_post.DOT_PARTS part whose footprint carries no pin-1 mark, at the free spot nearest pad 1
    (box gap, then angle from the part's centre through pad 1) within DOT_REACH whose nearest pad of the part is pad 1:
    r5_post's search tries eight directions at fixed reaches and found none for U11 / U13 on this board (D-S9-02).
    Returns {ref: (x, y, gap)}; a part with no such spot fails the run."""
    out = {}
    for ref in silk.DOT_PARTS:
        f = silk.fp_of(b, ref)
        s = silks['B' if f.IsFlipped() else 'F']
        fab = pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab
        body = None
        for g in f.GraphicalItems():
            if g.GetLayer() == fab and g.GetClass() == 'PCB_SHAPE':
                r = silk.bx(g)
                body = r if body is None else (min(body[0], r[0]), min(body[1], r[1]), max(body[2], r[2]),
                                               max(body[3], r[3]))
        pads = [(p.GetNumber(), silk.bx(p)) for p in f.Pads() if p.GetNumber()]
        p1 = next(r for n, r in pads if n == '1')
        cx, cy = silk.mm(f.GetPosition().x), silk.mm(f.GetPosition().y)
        base = math.atan2((p1[1] + p1[3]) / 2 - cy, (p1[0] + p1[2]) / 2 - cx)
        found = None
        for k in range(1, int(round(DOT_REACH / step)) + 1):
            g = k * step
            for a in range(64):
                ang = base + (a + 1) // 2 * (1 if a % 2 else -1) * math.pi / 32
                # the dot's centre on the ray from pad 1's centre, its box gap g beyond pad 1's box along the ray
                dx, dy = math.cos(ang), math.sin(ang)
                hx, hy = (p1[2] - p1[0]) / 2, (p1[3] - p1[1]) / 2
                d = min(hx / abs(dx) if abs(dx) > 1e-9 else 1e9, hy / abs(dy) if abs(dy) > 1e-9 else 1e9)
                x = (p1[0] + p1[2]) / 2 + (d + 0.2 + g) * dx
                y = (p1[1] + p1[3]) / 2 + (d + 0.2 + g) * dy
                r = (x - 0.2, y - 0.2, x + 0.2, y + 0.2)
                if body and r[0] < body[2] and body[0] < r[2] and r[1] < body[3] and body[1] < r[3]:
                    continue
                gaps = {n: silk._gap(r, q) for n, q in pads}
                if min(gaps, key=gaps.get) != '1' or gaps['1'] > DOT_REACH or not s.free(r):
                    continue
                found = (x, y, gaps['1'], r)
                break
            if found:
                break
        if found is None:
            raise RuntimeError(f'no room for a pin-1 dot at {ref} within {DOT_REACH} mm of its pad 1')
        x, y, gap, r = found
        dot = pcbnew.PCB_SHAPE(b)
        dot.SetShape(pcbnew.SHAPE_T_CIRCLE)
        dot.SetLayer(s.layer)
        dot.SetStart(silk.P(x, y))
        dot.SetEnd(silk.P(x + 0.1, y))
        dot.SetWidth(silk.MM(0.2))
        dot.SetFilled(True)
        b.Add(dot)
        s.add(r)
        out[ref] = (round(x, 3), round(y, 3), round(gap, 3))
    return out


def fab_clear(b, step=0.1):
    """r5_post.fab_refs shrinks overlapping Fab-layer designators to 0.3 mm; a pair still overlapping then has the
    designator of the part with the smaller courtyard moved, inside its own courtyard box, to the spot nearest the
    box centre where it overlaps no other Fab designator on its face (the assembly drawings stay legible). Returns
    {ref: (x, y)} of the moved ones; a pair left overlapping fails the run."""
    def fab(f):
        return silk._fab_ref(f)

    def box(f):
        c = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
        r = c.BBox() if c.OutlineCount() else f.GetBoundingBox(False)
        return silk.mm(r.GetX()), silk.mm(r.GetY()), silk.mm(r.GetRight()), silk.mm(r.GetBottom())

    def hits(f):
        a = fab(f).GetBoundingBox()
        return [g for g in b.GetFootprints() if g.GetReference() != f.GetReference() and g.IsFlipped() == f.IsFlipped()
                and fab(g).GetBoundingBox().Intersects(a)]
    moved = {}
    for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        for g in hits(f):
            a, c = box(f), box(g)
            small = f if (a[2] - a[0]) * (a[3] - a[1]) <= (c[2] - c[0]) * (c[3] - c[1]) else g
            x0, y0, x1, y1 = box(small)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            t = fab(small)
            spots = sorted(((x0 + step * i, y0 + step * j) for i in range(int((x1 - x0) / step) + 1)
                            for j in range(int((y1 - y0) / step) + 1)),
                           key=lambda q: ((q[0] - cx) ** 2 + (q[1] - cy) ** 2, q))
            for x, y in spots:
                t.SetPosition(silk.P(x, y))
                if not hits(small):
                    moved[small.GetReference()] = (round(x, 2), round(y, 2))
                    break
            else:
                raise RuntimeError(f'Fab designators {f.GetReference()} / {g.GetReference()} overlap')
    return moved


def finish(b):
    """Place every legend, the designators and the Fab references; return the placement evidence."""
    silk.W, silk.L = outline(b)
    for d in list(b.GetDrawings()):
        if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            b.Delete(d)
    for f in b.GetFootprints():
        for field in f.GetFields():
            field.SetVisible(False)
    for ref, w in r7_post.SILK_W.items():           # silkscreen strokes at the library width (lib_footprint_mismatch)
        for g in silk.fp_of(b, ref).GraphicalItems():
            if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) and g.GetClass() == 'PCB_SHAPE':
                g.SetWidth(silk.MM(w))
    silks = {side: r8_post.RunOnSilk(b, side) for side in ('F', 'B')}
    pads = connector_pads(b)
    placed, missing = {}, []

    def clip(x0, y0, x1, y1):
        return (max(0.4, x0), max(0.4, y0), min(silk.W - 0.4, x1), min(silk.L - 0.4, y1))

    def put_near(text, ref, sides=('B', 'F')):
        """A legend about part ref beside it (r7_post.label_near, within LEGEND_REACH of its courtyard), or the run
        fails: no whole-board fallback."""
        result = r7_post.label_near(b, silks, text, ref, sides=sides)
        placed[text] = None if result is None else list(result)
        if result is None:
            missing.append(f'{text} (within {LEGEND_REACH} mm of {ref})')
        return result

    # 1. the SMA jack legends (r7_post: vias kept JACK_VIA_GAP clear, nothing else within JACK_LEGEND_GAP afterwards)
    jack = {side: r8_post.RunOnSilk(b, side) for side in ('F', 'B')}
    for side in jack:
        for v in b.GetTracks():
            if v.GetClass() == 'PCB_VIA':
                jack[side].add(silk.bx(v), r7_post.JACK_VIA_GAP)
    for ref, name in (('J30', 'GNSS'), ('J31', 'RADIO')):
        pos = silk.fp_of(b, ref).GetPosition()
        cx, cy = silk.mm(pos.x), silk.mm(pos.y)
        result = silk.label(b, jack, name, (cx, cy + 3.0), clip(cx - 6.0, cy - 0.5, cx + 6.0, cy + 9.5), (0, 90),
                            ('F',))
        if result is None:
            result = silk.label(b, jack, name, (cx, cy + 3.0), clip(cx - 5.5, cy - 0.5, cx + 5.5, cy + 8.5), (0,),
                                ('F', 'B'))
        placed[name] = None if result is None else list(result)
        if result is None:
            missing.append(name)
            continue
        t = [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == name][-1]
        silks[result[0]].add(silk.ink(t), r7_post.JACK_LEGEND_GAP)
        silks[result[0]].texts.append(silk.ink(t))
    # 2. J122's plug numbers 1-4 in one row across the plugs (their own pins nearest), then the legends about one part,
    # beside it; the connector words on the top first (the terminals' own face)
    row = put_plug_row(b, silks, pads)
    for plug, _ in PLUG_ROWS:
        placed[f'J122 plug {plug}'] = None if row is None else list(row[plug])
    if row is None:
        missing.append('J122 plug numbers 1-4 (one row)')
    put_near('TP30 SAFEBOOT', 'TP30', sides=('F', 'B'))
    for ref, word in WORDS:
        put_near(word, ref, sides=('F', 'B'))
    for ref, (_, names) in PORTS.items():
        for start in range(0, len(names), 2):
            row = ref + ' ' + ' '.join(f'{i + 1}:{names[i]}' for i in range(start, min(start + 2, len(names))))
            put_near(row, ref)
    put_near(J122_TABLE, 'J122')
    for ref, note in NOTES:
        put_near(note, ref)
    # 3. terminal pin legends by pin (J1's in the forward-edge strip first), then J122's plug numbers
    for ref, mapping in TERMINAL_PINS:
        for number, name in mapping:
            x, y = silk.pad(b, ref, number)
            regions = []
            if ref == 'J1':
                sy = silk.L - STRIP_INSET
                regions.append((clip(x - STRIP_HALF[0], sy - STRIP_HALF[1], x + STRIP_HALF[0], sy + STRIP_HALF[1]),
                                ('F',), (0,)))
            regions.append((clip(x - PIN_REACH, y - PIN_REACH, x + PIN_REACH, y + PIN_REACH), ('F', 'B'), (90, 0)))
            result = put_pin(b, silks, f'{number}:{name}', pads, {(ref, number)}, (x, y), regions)
            key = f'{ref} {number}:{name}'
            placed[key] = None if result is None else list(result)
            if result is None:
                missing.append(key)
    # 4. revision legend and JLC's order-number placeholder
    whole = (0.4, 0.4, silk.W - 0.4, silk.L - 0.4)
    for text, near in ((REV, (silk.W / 2, silk.L - 6.0)), (ORDER_MARK, (silk.W / 2, silk.L - 24.0))):
        result = silk.label(b, silks, text, near, whole, (0, 90), ('B', 'F'), size=1.0)
        placed[text] = None if result is None else list(result)
        if result is None:
            missing.append(text)
    if missing:
        raise RuntimeError('Essential R9 silkscreen did not fit: ' + ', '.join(missing))
    # 5. pin-1 dots, designators, the courtyard and run-on tests (r8_post)
    dots = pin1_dots(b, silks)
    silk.designators(b, silks)
    moved = {}
    for _ in range(4):
        bad = {ref: ('courtyard',) + why for ref, why in r7_post.courtyard_offenders(b).items()}
        bad.update({ref: ('run-on',) for ref in r8_post.run_on_offenders(b) if ref not in bad})
        if not bad:
            break
        for ref in sorted(bad):
            moved[ref] = (bad[ref], r8_post.place_designator(b, ref))
    left = r7_post.courtyard_offenders(b)
    if left:
        raise RuntimeError(f"designators still nearer another part's courtyard than their own: {left}")
    left = r8_post.run_on_offenders(b)
    if left:
        raise RuntimeError(f'designators still running into another text: {left}')
    small = [f.GetReference() for f in b.GetFootprints() if f.Reference().IsVisible() and
             silk.mm(f.Reference().GetTextHeight()) < 1.0 - 1e-6]
    if small:
        raise RuntimeError(f'designators below 1.0 mm text (REQUIREMENTS M2): {small}')
    # 6. Fab references, title block
    silk.fab_refs(b)
    fab_moved = fab_clear(b)
    b.GetTitleBlock().SetRevision(REV)
    issues = (check_r7.duplicate_ids(b) + check_r7.pin_legends(b) + check_r7.legend_subjects(b) +
              check_r8.terminal_legends(b)[0])
    if issues:
        raise RuntimeError('legend contract: ' + '; '.join(issues))
    hidden = sorted(silk.HIDDEN, key=lambda r: (r.rstrip('0123456789'), int(r[len(r.rstrip('0123456789')):] or 0)))
    visible = sum(1 for f in b.GetFootprints() if f.Reference().IsVisible())
    bottom_of_top = sorted(f.GetReference() for f in b.GetFootprints() if f.Reference().IsVisible() and
                           not f.IsFlipped() and f.Reference().GetLayer() == pcbnew.B_SilkS)
    for ref, (why, got) in sorted(moved.items()):
        print(f'  {why[0]}: {ref} -> '
              f'{"hidden" if got is None else f"{got[0]}.SilkS at ({got[1][0]:.2f}, {got[1][1]:.2f})"}')
    print(f'R9 silkscreen: {len(placed)} legends; {visible} designators shown ({len(bottom_of_top)} top parts\' on the '
          f'bottom under their part); {len(hidden)} hidden, kept on Fab: {" ".join(hidden)}')
    return {'revision': REV, 'outline_mm': [silk.W, silk.L], 'legends': placed, 'pin1_dots': dots,
            'fab_moved': fab_moved,
            'designators_shown': visible,
            'top_designators_under_part_on_bottom': bottom_of_top, 'hidden_references': hidden,
            'replaced_designators': {r: {'why': list(w), 'after': None if g is None else [g[0], list(g[1])]}
                                     for r, (w, g) in sorted(moved.items())}}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--board', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--report', type=Path, help='write the placement evidence (JSON)')
    args = ap.parse_args()
    board = args.board.resolve()
    pcbnew.KIID.SeedGenerator(KIID_SEED)
    b = pcbnew.LoadBoard(str(board))
    if not check_r7.pin_legends(b):
        raise SystemExit('r9_post runs once, on the ground-stage board: this board already carries its pin tables')
    before = r8_post.fixed_digest(b)
    evidence = finish(b)
    assert r8_post.fixed_digest(b) == before, 'r9_post changed copper, a zone, a pad or a footprint position'
    assert pcbnew.SaveBoard(str(board), b, True), 'save failed'
    b = pcbnew.LoadBoard(str(board))
    assert r8_post.fixed_digest(b) == before, 'the saved board differs in copper, zones, pads or footprint positions'
    print(f'r9_post: saved {board.name}; copper, zones, pads and footprint positions unchanged')
    if args.report:
        args.report.write_text(json.dumps(evidence, indent=1) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
