#!/usr/bin/env python3
"""R7 silkscreen and assembly reference finishing (after r7_route.py); no copper or geometry edits.

usage: <KiCad python3> -I m3_design/r7_post.py [--board m3_design/assembly_review/m3.kicad_pcb]

The R6 finish (r6_post.py) with the R7 legends: the board revision M3-ASSY-R7, the SMA jack legends GNSS (J30)
and RADIO (J31), TP30 SAFEBOOT (the GNSS safe-boot pad), and no telemetry port tables (J130/J131 are gone).
Designators are placed by r5_post.designators (>= 1.0 mm text, never over pads or off the board, on the
part's own side or under it on the other); one with no spot is hidden, kept on the Fab layer, and listed in
docs/M3_R7.md. Fix pass 5: every visible designator then passes the courtyard test (its ink no nearer another part's
courtyard than its own, ink polygon to courtyard polygon, as the pass-4/5 reviews measured) or is placed again with it,
or hidden (AGENTS.md silkscreen rule); the run fails if one is left. Essential legends must fit, otherwise the run fails.
Fix pass 7: the legends about one part (connector pin tables, the J124 / J1 fuse notes) go beside that part
(label_near, within LEGEND_REACH; tools/check_r7 legend_subjects gates it), and R6's 'UART 3V3 / RX-TX AT MODULE'
(about the R6 port R7 removed) is gone. The board is filled and saved once.
"""
import argparse
import math
from pathlib import Path
import sys

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
import r5_post as silk  # noqa: E402
import r7_lib as lib  # noqa: E402

REV = lib.REV
PORTS = {
    'J9': ('CAM', ('5V', 'GND', 'TX', 'RX')),
    'J2': ('SWD', ('3V3', 'SWDIO', 'NRST', 'SWCLK', 'GND', 'NC')),
}


# Designators that r5_post.designators (nearest by pads) leaves nearer another part's courtyard than their own: placed
# again with the courtyard test (pass 2 DFM-10: FB31's sat beside C310)
COURTYARD_REFS = ('FB31',)
JACK_VIA_GAP = 0.2          # mm: SMA jack legends to any via (pass 3 DFM-06)
JACK_LEGEND_GAP = 0.8        # mm: other silkscreen to the jack legends
SILK_W = {'LS120': 0.15}      # REQUIREMENTS M2: silkscreen lines >= 0.15 mm (kilib M3_MLT5020_3pad has 0.15 since pass 2)


def _courtyard(f):
    c = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    r = c.BBox()
    return silk.mm(r.GetX()), silk.mm(r.GetY()), silk.mm(r.GetRight()), silk.mm(r.GetBottom())


def courtyard_designator(b, ref, cap=1.5, margin=0.15):
    """Move ref's designator to the free spot nearest its part whose ink is within `cap` of its own courtyard and
    nearer it (by `margin`) than any other part's courtyard; top face first, then under the part on the bottom; with no
    such spot it is hidden (AGENTS silkscreen rule), kept on the Fab layer."""
    f = b.FindFootprintByReference(ref)
    t = f.Reference()
    own = _courtyard(f)
    others = [_courtyard(g) for g in b.GetFootprints() if g is not f and abs(silk.mm(g.GetPosition().x) - silk.mm(
        f.GetPosition().x)) < 10 and abs(silk.mm(g.GetPosition().y) - silk.mm(f.GetPosition().y)) < 10]
    others = [o for o in others if o[2] > o[0]]
    cx, cy = silk.mm(f.GetPosition().x), silk.mm(f.GetPosition().y)
    for side in ('F', 'B'):
        s = silk.Silk(b, side, strict_bodies=True)
        for g in b.GetFootprints():                       # every other placed designator and legend
            r_ = g.Reference()
            if g is not f and r_.IsVisible() and r_.GetLayer() == s.layer:
                s.add(silk.ink(r_))
        t.SetLayer(s.layer)
        t.SetMirrored(side == 'B')
        best = None
        rr_ = 0.0
        while rr_ <= 3.0 and best is None:
            n = max(1, int(2 * math.pi * rr_ / 0.1))
            for k in range(n):
                x, y = cx + rr_ * math.cos(2 * math.pi * k / n), cy + rr_ * math.sin(2 * math.pi * k / n)
                for ang in (90, 0):
                    t.SetTextAngleDegrees(ang)
                    t.SetPosition(silk.P(x, y))
                    r = silk.ink(t)
                    d_own = silk._gap(r, own)
                    if d_own > cap or not s.free(r):
                        continue
                    if side == 'B' and not (own[0] <= x <= own[2] and own[1] <= y <= own[3]):
                        continue                          # on the bottom only under the part itself
                    if any(silk._gap(r, o) < d_own + margin for o in others):
                        continue
                    best = (x, y, ang)
                    break
                if best:
                    break
            rr_ += 0.1
        if best:
            t.SetTextAngleDegrees(best[2])
            t.SetPosition(silk.P(best[0], best[1]))
            t.SetVisible(True)
            return side, best
    t.SetVisible(False)                                   # AGENTS: no unambiguous spot on either side -> hidden,
    if ref not in silk.HIDDEN:                            # kept on the Fab layer and listed in the R7 record
        silk.HIDDEN.append(ref)
    return None


def _poly_gap(a, c):
    """Edge distance (mm) between two polygon sets, 0 when they overlap."""
    x = pcbnew.SHAPE_POLY_SET(a)
    x.BooleanIntersection(c)
    if x.OutlineCount():
        return 0.0
    best = None
    for p_, q_ in ((a, c), (c, a)):
        for o in range(p_.OutlineCount()):
            ol = p_.Outline(o)
            for i in range(ol.PointCount()):
                pt = ol.CPoint(i)
                for k in range(q_.OutlineCount()):
                    d = q_.Outline(k).SquaredDistance(pt)
                    best = d if best is None else min(best, d)
    return silk.mm(math.sqrt(best))


def courtyard_offenders(b):
    """Visible designators whose ink lies nearer another part's courtyard (on the side the text is on) than their own
    part's courtyard (any side: a designator under its part on the other face measures to it in plan): the pass-4/5
    review test, ink polygon to courtyard polygon. {ref: (own gap, nearest other gap, other ref)}."""
    yards = {}
    for f in b.GetFootprints():
        ps = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
        if ps.OutlineCount():
            yards[f.GetReference()] = (f.IsFlipped(), ps, ps.BBox())
    out = {}
    for f in b.GetFootprints():
        t = f.Reference()
        ref = f.GetReference()
        if not t.IsVisible() or ref not in yards:
            continue
        ink_ = pcbnew.SHAPE_POLY_SET()
        t.TransformShapeToPolygon(ink_, t.GetLayer(), 0, silk.MM(0.002), pcbnew.ERROR_INSIDE)
        back = t.GetLayer() == pcbnew.B_SilkS
        c = ink_.BBox().Centre()
        own = _poly_gap(ink_, yards[ref][1])
        near_ = [(_poly_gap(ink_, ps), r) for r, (flip, ps, bb) in yards.items()
                 if r != ref and flip == back and abs(bb.Centre().x - c.x) < silk.MM(8) and abs(bb.Centre().y - c.y) < silk.MM(8)]
        if near_:
            g, r = min(near_)
            if g < own:
                out[ref] = (round(own, 3), round(g, 3), r)
    return out


LEGEND_REACH = 6.0          # mm: a subject's legend goes within this of its subject's courtyard (fix pass 7: tools/check_r7
                            # legend_subjects gates it), on either face, either angle, nearest first


def subject_box(b, ref):
    """The subject footprint's courtyard box (mm), either face; its pads' box when it has no courtyard."""
    f = b.FindFootprintByReference(ref)
    c = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    if c.OutlineCount():
        r = c.BBox()
    else:
        r = f.GetBoundingBox(False)
    return silk.mm(r.GetX()), silk.mm(r.GetY()), silk.mm(r.GetRight()), silk.mm(r.GetBottom())


def label_near(b, silks, text, ref, reach=LEGEND_REACH, sides=('F', 'B'), angles=(0, 90), size=1.0, step=0.1):
    """A board legend about part `ref` at the free spot (r5_post.Silk) whose ink is nearest the part's courtyard box,
    over both angles together, on the first face in `sides` that has one within `reach` (r5_post.label tries one angle
    at a time over its whole region, which put fix pass 6's J124 fuse legend 73 mm from J124; the bottom face first
    leaves the top-side designators their room); returns (side, x, y, angle, gap) or None."""
    box = subject_box(b, ref)
    best = None
    for side in sides:
        if best is not None:
            break
        s = silks[side]
        t = silk._text(b, text, s.layer, size)
        for ang in angles:
            t.SetTextAngleDegrees(ang)
            t.SetPosition(silk.P(0, 0))
            r0 = silk.ink(t)
            w, h = r0[2] - r0[0], r0[3] - r0[1]
            x0, x1 = box[0] - reach - w - r0[0], box[2] + reach - r0[0]
            y0, y1 = box[1] - reach - h - r0[1], box[3] + reach - r0[1]
            for i in range(int((x1 - x0) / step) + 1):
                x = x0 + step * i
                for j in range(int((y1 - y0) / step) + 1):
                    y = y0 + step * j
                    r = (r0[0] + x, r0[1] + y, r0[2] + x, r0[3] + y)
                    g = silk._gap(r, box)
                    if g > reach or (best is not None and g >= best[0]):
                        continue
                    if s.free(r):
                        best = (g, side, x, y, ang, r)
    if best is None:
        print(f'  no room for legend {text!r} within {reach} mm of {ref}')
        return None
    g, side, x, y, ang, r = best
    s = silks[side]
    t = silk._text(b, text, s.layer, size)
    t.SetTextAngleDegrees(ang)
    t.SetPosition(silk.P(x, y))
    b.Add(t)
    s.add(r)
    return side, round(x, 2), round(y, 2), ang, round(g, 2)


def finish(b):
    """Place all required legends, optional refdes and all assembly references; return placement evidence."""
    outline = b.GetBoardEdgesBoundingBox()
    if abs(silk.mm(outline.GetX())) > 0.1 or abs(silk.mm(outline.GetY())) > 0.1:
        raise RuntimeError('R7 silkscreen expects the board origin at (0, 0)')
    silk.W, silk.L = silk.mm(outline.GetWidth()), silk.mm(outline.GetHeight())
    for d in list(b.GetDrawings()):
        if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            b.Delete(d)
    for f in b.GetFootprints():
        for field in f.GetFields():
            field.SetVisible(False)
    for ref, w in SILK_W.items():                  # silkscreen strokes at the library width (lib_footprint_mismatch)
        for g in silk.fp_of(b, ref).GraphicalItems():
            if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) and g.GetClass() == 'PCB_SHAPE':
                g.SetWidth(silk.MM(w))
    buzzer = silk.fp_of(b, 'LS120')               # keep polarity visible in assembly drawings
    for mark in buzzer.GraphicalItems():
        if isinstance(mark, pcbnew.PCB_TEXT) and mark.GetText() in ('+', '-'):
            mark.SetLayer(pcbnew.B_Fab if buzzer.IsFlipped() else pcbnew.F_Fab)
            mark.SetTextSize(pcbnew.VECTOR2I(silk.MM(0.8), silk.MM(0.8)))
            mark.SetTextThickness(silk.MM(0.1))
    silks = {side: silk.Silk(b, side, strict_bodies=True) for side in ('F', 'B')}
    placed, missing = {}, []

    def box(cx, cy, rx, ry):
        return (max(0.4, cx - rx), max(0.4, cy - ry), min(silk.W - 0.4, cx + rx), min(silk.L - 0.4, cy + ry))

    whole = (0.4, 0.4, silk.W - 0.4, silk.L - 0.4)

    def put(text, near, region, sides=('F', 'B'), angles=(0, 90), required=True, fallback=False):
        result = silk.label(b, silks, text, near, region, angles, sides, size=1.0)
        if result is None and fallback:
            result = silk.label(b, silks, text, near, whole, angles, ('B', 'F'), size=1.0)
        placed[text] = result
        if result is None and required:
            missing.append(text)
        return result

    def centre(ref):
        pos = silk.fp_of(b, ref).GetPosition()
        return silk.mm(pos.x), silk.mm(pos.y)

    def put_near(text, ref, sides=('B', 'F')):
        """A legend about part ref next to it (label_near); the old whole-board search only if no spot is within
        LEGEND_REACH (check_r7 legend_subjects then fails the gate)."""
        result = label_near(b, silks, text, ref, sides=sides)
        if result is None:
            return put(text, centre(ref), whole, sides=('B', 'F'), angles=(0, 90), fallback=True)
        placed[text] = result[:4]
        return result

    # SMA jack legends first (the strip is crowded): on the board just forward of each jack, nearer its own jack, both
    # on the top face where a spot exists (pass 2 DFM-10/REQUIREMENTS-09), else the nearest spot on either face. Pass 3
    # DFM-06: they keep 0.35 mm (not 0.15) from every via, so the words do not sit on the strip's tented stitching vias,
    # and nothing else is placed within 0.8 mm of them afterwards, so a designator (J31's) cannot run on end to end
    # with RADIO and read as one string.
    jack = {side: silk.Silk(b, side, strict_bodies=True) for side in ('F', 'B')}
    for side in jack:
        for v in b.GetTracks():
            if v.GetClass() == 'PCB_VIA':
                jack[side].add(silk.bx(v), JACK_VIA_GAP)

    def put_jack(name, near, region, sides, angles, required):
        result = silk.label(b, jack, name, near, region, angles, sides, size=1.0)
        placed[name] = result
        if result is None:
            if required:
                missing.append(name)
            return None
        t = [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == name][-1]
        silks[result[0]].add(silk.ink(t), JACK_LEGEND_GAP)
        return result
    for ref, name in (('J30', 'GNSS'), ('J31', 'RADIO')):
        cx, cy = centre(ref)
        if not put_jack(name, (cx, cy + 3.0), box(cx, cy + 4.5, 6.0, 5.0), ('F',), (0, 90), False):
            put_jack(name, (cx, cy + 3.0), box(cx, cy + 4.0, 5.5, 4.5), ('F', 'B'), (0,), True)
    # TP30 SAFEBOOT up the left edge from TP30, in the window the strip lattice leaves (r7_route.TP30_LEGEND)
    put('TP30 SAFEBOOT', (1.45, 16.7), (0.4, 10.4, 5.2, 23.0), sides=('F',), angles=(90,))
    # essential local labels, then extended pin tables and optional refs (as R6)
    for ref, name in [('J124', 'ARM'), ('J121', 'IGN'), ('J1', 'BAT'), ('J9', 'CAM'), ('J2', 'SWD'),
                      ('J122', 'SERVO'), ('J123', 'PULL')]:
        cx, cy = centre(ref)
        put(name, (cx, cy - 5), box(cx, cy, 8, 8))
    for ref, mapping in [('J124', (('1', 'BUS1'), ('2', 'RAW'))),
                         ('J121', (('1', 'E1-'), ('2', 'E1+'))),
                         ('J1', (('1', 'BAT+'), ('2', 'GND'), ('3', 'SW'), ('4', 'SW')))]:
        for number, name in mapping:
            x, y = silk.pad(b, ref, number)
            put(number + ':' + name, (x, y - 3), box(x, y, 3.8, 8), angles=(90, 0))
    # fix pass 7: the connector pin tables beside their connector (label_near; the region search left J2's third row
    # 19 mm and J122's row 25 mm away). R6's 'UART 3V3 / RX-TX AT MODULE' legend is gone with the R6 port it named.
    for ref, (_, pins) in PORTS.items():
        for start in range(0, len(pins), 2):
            row = ref + ' ' + ' '.join(f'{i + 1}:{pins[i]}' for i in range(start, min(start + 2, len(pins))))
            put_near(row, ref)
    put_near('J122 1:S 2:+ 3:GND', 'J122')
    for number, row in [('3', '1'), ('6', '2'), ('9', '3'), ('12', '4')]:
        x, y = silk.pad(b, 'J122', number)
        put(row, (x - 2, y), box(x - 2, y, 1.3, 1.3), angles=(0,), required=False)
    # J123 (moved by R7 into a crowded corner): one label per pin, as the terminals have (a single 'J123 1:PULL 2:GND'
    # row found no spot nearer than 12 mm)
    for number, name in (('1', 'PULL'), ('2', 'GND')):
        x, y = silk.pad(b, 'J123', number)
        put(number + ':' + name, (x, y + 3), box(x, y, 2.5, 8), sides=('B', 'F'), angles=(90, 0), fallback=True)
    # the ARM-link and battery-lead fuse legends beside J124 / J1 (fix pass 7: 'J124: 5A FAST / 2S' had landed at the
    # RF strip, 73 mm from J124)
    put_near('J124 2-FUSE-1: ARM LAST', 'J124')
    put_near('J124: 5A FAST / 2S', 'J124')
    put_near('J1 BAT LEAD: 15A FUSE', 'J1')
    put(REV, (23, silk.L - 6), whole, sides=('B', 'F'), angles=(0, 90), fallback=True)
    put('JLCJLCJLCJLC', (23, 94), whole, sides=('B', 'F'), angles=(0, 90), required=False)
    if missing:
        raise RuntimeError('Essential R7 silkscreen did not fit: ' + ', '.join(missing))
    silk.pin1_dots(b, silks)
    silk.designators(b, silks)
    for ref in COURTYARD_REFS:
        courtyard_designator(b, ref)
    # AGENTS.md silkscreen rule on every visible designator (P4-DOCS-04 / P5-DOCS-01, deviation D17): one nearer another
    # part's courtyard than its own is placed again with the courtyard test, or hidden when no spot passes it
    moved = {}
    for _ in range(3):
        bad = courtyard_offenders(b)
        if not bad:
            break
        for ref in sorted(bad):
            moved[ref] = (bad[ref], courtyard_designator(b, ref))
    left = courtyard_offenders(b)
    if left:
        raise RuntimeError(f'designators still nearer another part\'s courtyard than their own: {left}')
    for ref, (why, got) in sorted(moved.items()):
        print(f'  courtyard test: {ref} (own {why[0]} mm, {why[2]} {why[1]} mm) -> '
              f'{"hidden" if got is None else f"{got[0]}.SilkS at ({got[1][0]:.2f}, {got[1][1]:.2f})"}')
    silk.fab_refs(b)
    b.GetTitleBlock().SetRevision(REV)
    print(f'R7 silkscreen: {sum(v is not None for v in placed.values())} labels; '
          f'{len(silk.HIDDEN)} hidden refs retained on Fab: {" ".join(sorted(silk.HIDDEN))}')
    return {'revision': REV, 'labels': placed, 'hidden_references': sorted(silk.HIDDEN)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--board', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    args = ap.parse_args()
    pcbnew.KIID.SeedGenerator(7301)
    b = pcbnew.LoadBoard(str(args.board))
    finish(b)
    lib.fill(b)
    pcbnew.SaveBoard(str(args.board), b, True)
    print('saved', args.board)


if __name__ == '__main__':
    main()
