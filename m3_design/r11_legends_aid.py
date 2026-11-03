#!/usr/bin/env python3
"""R11 silkscreen drafting aid (D-R11-65): searches the legend, designator, pin-1 dot and Fab-reference placements for
the routed R11 board once, offline, and freezes them into m3_design/r11_legends.tsv. m3_design/r11_post.py only reads
that table (D-R11-07: the build never searches). Not run by m3_design/r11_build.sh.

usage: <KiCad python3> -I -B m3_design/r11_legends_aid.py BOARD [--out m3_design/r11_legends.tsv] [--save COPY]
BOARD is the routed board before the post stage (the build's ground-family output, no silkscreen text).

The search is R10's post stage (m3_design/r10_post.py and the r5 / r7 / r8 / r9 helpers it imports) on R11's data, in
this order (the first placed get the room):
  1. the wire-pad and switch terminal legends (J121 1:E1- / 2:E1+, J1 1:BAT+ / 2:GND, J400 1:SW / 2:SW;
     check_r11.TERMINAL_PINS_R11 via r9_post.put_pin: the text's bounding box OWN_MARGIN_R11 nearer its own pin than any
     other connector pin, both faces, angles 90 / 0, within PIN_REACH of the pin); the revision M3-ASSY-R11 on the bottom;
  2. the designators K-legends requires shown (check_r10.SHOWN_REFS: r8_post.place_designator, else
     place_near_courtyard within SHOWN_CAP of the courtyard);
  3. the connector words (check_r10.WORD_LEGENDS_R10) on the faces K-legends gives each connector, beside it (the tie
     rule), with the centre margin for the blocking words and GPS / RADIO / AUX inside their connector's pin-row span
     (check_r11.word_spans_r11);
  4. the GH ports' pin legends, J2's SWD rows (r10_post.put_subject) and J122's harness note;
  5. pin-1 dots (r10_post.pin1_dots) for DOT_PARTS, optional;
  6. the other designators (r5_post.designators, then r8_post's courtyard and run-on repairs); a designator with no
     legal spot is hidden and kept on the Fab layer;
  7. Fab references (place_fab): one ${REFERENCE} per footprint, inside its own Fab body where it fits, else beside it
     within check_r10.FAB_REF_REACH, crossing no Fab outline or other Fab reference (check_r10.fab_ref_crossings).
A required legend or designator with no legal spot is written as an 'open' row (D-R11-66): m3_design/r11_post.py
accepts exactly those K-legends findings, and tools/check.sh still fails on them.
Every placement keeps r10_post's SILK_GAP from pads, vias, holes, mask openings and other silkscreen, the 0.6 mm edge
margin and the support hardware circles. Deterministic: a fixed order and fixed grids, no random search.
"""
import argparse
import math
from pathlib import Path
import sys

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r10  # noqa: E402
import check_r11  # noqa: E402
import r10_post as P  # noqa: E402
import r11_post  # noqa: E402  (supports, TSV writer, the contract)
import r5_post as silk  # noqa: E402
import r7_post  # noqa: E402
import r8_post  # noqa: E402
import r9_post  # noqa: E402

OWN_MARGIN_R11 = 0.1            # mm: pin legend box nearer its own pin than any other (gate: 0.01 mm; R10 0.3 mm)
DOT_PARTS = ('U9', 'U10', 'U11', 'U12', 'U13', 'U400', 'U401', 'U402', 'U2', 'U3', 'U4', 'U5')
SPAN_WORDS = check_r11.WORD_SPAN_R11
WIRED_FIRST = ('J121', 'J1', 'J400')
SHOWN_CAP = 4.0                 # mm: a required designator's reach from its courtyard when 1.5 mm has no spot


def face_boxes(b):
    """{face: {ref: courtyard box}} as check_r10.word_legends sees connectors (mounted there, or plated through)."""
    out = {'F': {}, 'B': {}}
    for f in b.GetFootprints():
        if check_r10.re.fullmatch(r'J\d+', f.GetReference()):
            box = r7_post.subject_box(b, f.GetReference())
            through = any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in f.Pads())
            for face, flipped in (('F', False), ('B', True)):
                if through or f.IsFlipped() == flipped:
                    out[face][f.GetReference()] = box
    return out


def word_ok(word, own, r, boxes):
    """check_r10.word_legends' tests on ink box r (tie, centre margin) plus the R11 span along the pin row."""
    if own not in boxes:
        return False, None
    gaps = {ref: silk._gap(r, box) for ref, box in boxes.items()}
    if any(g <= gaps[own] + check_r10.WORD_TIE + 0.02 for ref, g in gaps.items() if ref != own):
        return False, None
    cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
    centre = {ref: math.hypot(max(box[0] - cx, 0, cx - box[2]), max(box[1] - cy, 0, cy - box[3]))
              for ref, box in boxes.items()}
    margin = min((d for ref, d in centre.items() if ref != own), default=math.inf) - centre[own]
    if word in check_r10.WORD_CENTRE_BLOCKING and margin < check_r10.WORD_CENTRE_MARGIN + 0.05:
        return False, None
    return True, margin


def put_word(b, silks, word, own, span_axis=None, reach=P.LEGEND_REACH - P.REACH_MARGIN, step=0.1):
    fb = face_boxes(b)
    box = r7_post.subject_box(b, own)
    best = None
    for side in ('F', 'B'):
        s = silks[side]
        t = silk._text(b, word, s.layer, 1.0)
        for ang in (0, 90):
            t.SetTextAngleDegrees(ang)
            t.SetPosition(silk.P(0, 0))
            r0 = silk.ink(t)
            w, h = r0[2] - r0[0], r0[3] - r0[1]
            x0, x1 = box[0] - reach - w - r0[0], box[2] + reach - r0[0]
            y0, y1 = box[1] - reach - h - r0[1], box[3] + reach - r0[1]
            for i in range(int((x1 - x0) / step) + 1):
                x = round(x0 + step * i, 4)
                for j in range(int((y1 - y0) / step) + 1):
                    y = round(y0 + step * j, 4)
                    r = (r0[0] + x, r0[1] + y, r0[2] + x, r0[3] + y)
                    g = silk._gap(r, box)
                    key = (round(g, 1), side != 'F', ang)
                    if g > reach or (best is not None and key >= best[0]):
                        continue
                    if span_axis is not None:
                        lo, hi = (box[0], box[2]) if span_axis == 0 else (box[1], box[3])
                        a, z = (r[0], r[2]) if span_axis == 0 else (r[1], r[3])
                        if min(a - lo, hi - z) < check_r10.WORD_SPAN_MARGIN + 0.05:
                            continue
                    if not s.free(r):
                        continue
                    ok, m = word_ok(word, own, r, fb[side])
                    if ok:
                        best = (key, side, x, y, ang, r)
        if best is not None and best[1] == 'F':
            break
    if best is None:
        return None
    _, side, x, y, ang, r = best
    t = silk._text(b, word, silks[side].layer, 1.0)
    t.SetTextAngleDegrees(ang)
    t.SetPosition(silk.P(x, y))
    b.Add(t)
    silks[side].add(r)
    return side, x, y, ang


def pin_axis(b, ref):
    f = b.FindFootprintByReference(ref)
    pads = [p.GetPosition() for p in f.Pads() if p.GetNumber()]
    return 0 if max(p.x for p in pads) - min(p.x for p in pads) >= max(p.y for p in pads) - min(p.y for p in pads) else 1


def place_near_courtyard(b, ref, cap, step=0.1, margin=0.15):
    """A required designator's spot by grid around its courtyard box (r8_post.place_designator searches 3 mm about the
    part centre, which is under a large connector's body): the free spot (Silk10, run-on) nearest the courtyard
    within cap, nearer its own courtyard than any other by margin (r8_post.courtyard_fails, the gate's measure), the
    top face first, the bottom only under the part (AGENTS.md section 3). Returns (side, (x, y)) or None."""
    f = b.FindFootprintByReference(ref)
    t = f.Reference()
    own = r7_post._courtyard(f)
    others = [r7_post._courtyard(g) for g in b.GetFootprints() if g.GetReference() != ref]
    others = [o for o in others if o[2] > o[0]]
    for side in (('B',) if f.IsFlipped() else ('F', 'B')):
        t.SetVisible(False)
        s = P.Silk10(b, side)
        for g in b.GetFootprints():
            r_ = g.Reference()
            if g.GetReference() != ref and r_.IsVisible() and r_.GetLayer() == s.layer:
                s.add(silk.ink(r_))
        t.SetLayer(s.layer)
        t.SetMirrored(side == 'B')
        best = None
        for ang in (0, 90):
            t.SetTextAngleDegrees(ang)
            t.SetPosition(silk.P(0, 0))
            r0 = silk.ink(t)
            x0, x1 = own[0] - cap - r0[2], own[2] + cap - r0[0]
            y0, y1 = own[1] - cap - r0[3], own[3] + cap - r0[1]
            for i in range(int((x1 - x0) / step) + 1):
                x = round(x0 + step * i, 4)
                for j in range(int((y1 - y0) / step) + 1):
                    y = round(y0 + step * j, 4)
                    r = (r0[0] + x, r0[1] + y, r0[2] + x, r0[3] + y)
                    d = silk._gap(r, own)
                    if d > cap or (best is not None and (round(d, 1), ang) >= best[0]):
                        continue
                    if side == 'B' and not f.IsFlipped() and not (own[0] <= x <= own[2] and own[1] <= y <= own[3]):
                        continue
                    if not s.free(r) or any(silk._gap(r, o) < d + margin for o in others):
                        continue
                    t.SetPosition(silk.P(x, y))
                    t.SetVisible(True)
                    ok = not r8_post.courtyard_fails(b, f)
                    t.SetVisible(False)
                    if ok:
                        best = ((round(d, 1), ang), x, y, ang)
        if best is not None:
            _, x, y, ang = best
            t.SetTextAngleDegrees(ang)
            t.SetPosition(silk.P(x, y))
            t.SetVisible(True)
            return side, (x, y)
    t.SetVisible(False)
    return None


# ----------------------------------------------------------------------------------------------------------------------
# Fab references
FAB_SIZES = ((0.8, 0.8), (0.6, 0.6), (0.5, 0.5), (0.4, 0.4), (0.35, 0.3), (0.3, 0.3), (0.3, 0.22), (0.3, 0.16))


def fab_shapes(f):
    fab = pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab
    shapes = [g for g in f.GraphicalItems() if isinstance(g, pcbnew.PCB_SHAPE) and g.GetLayer() == fab]
    outline = pcbnew.SHAPE_POLY_SET()
    for g in shapes:
        g.TransformShapeToPolygon(outline, fab, 0, pcbnew.FromMM(0.002), pcbnew.ERROR_INSIDE)
    outline.Simplify()
    body = [g for g in shapes if g.GetShape() != pcbnew.SHAPE_T_CIRCLE]
    if body:
        own = body[0].GetBoundingBox()
        for g in body[1:]:
            own.Merge(g.GetBoundingBox())
    else:
        own = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd).BBox()
    return fab, outline, own


def ink_poly(t, lay):
    poly = pcbnew.SHAPE_POLY_SET()
    t.TransformShapeToPolygon(poly, lay, 0, pcbnew.FromMM(0.002), pcbnew.ERROR_INSIDE)
    return poly


def box_poly(bb, grow=0):
    box = pcbnew.SHAPE_POLY_SET()
    box.NewOutline()
    for x, y in ((bb.GetLeft() - grow, bb.GetTop() - grow), (bb.GetRight() + grow, bb.GetTop() - grow),
                 (bb.GetRight() + grow, bb.GetBottom() + grow), (bb.GetLeft() - grow, bb.GetBottom() + grow)):
        box.Append(int(x), int(y))
    return box


def hits(a, c):
    x = pcbnew.SHAPE_POLY_SET(a)
    x.BooleanIntersection(c)
    return x.OutlineCount() and x.Area() > 0


def place_fab(b, step=0.05, margin=0.03):
    """Every footprint's one ${REFERENCE} on its own Fab layer (added where the library has none, removed where it has
    more than one), largest size first, inside its own body box first, else beside it; returns {ref: (h, w, x, y)}."""
    G = pcbnew.FromMM(margin)                      # placement margin over the gate's zero-area tests
    info = {}
    for f in b.GetFootprints():
        fab, outline, own = fab_shapes(f)
        refs = [g for g in f.GraphicalItems() if isinstance(g, pcbnew.PCB_TEXT) and g.GetText() == '${REFERENCE}']
        for g in refs[1:]:
            f.Remove(g)
        if refs:
            t = refs[0]
        else:
            t = pcbnew.PCB_TEXT(f)
            t.SetText('${REFERENCE}')
            f.Add(t)
        t.SetLayer(fab)
        t.SetMirrored(f.IsFlipped())
        t.SetVisible(True)
        t.SetKeepUpright(False)
        info[f.GetReference()] = (f, t, fab, outline, own)
    placed = {}                                    # ref -> (fab layer, ink box poly, bbox)
    order = sorted(info, key=lambda r: (info[r][4].GetWidth() * info[r][4].GetHeight(), r))
    result = {}
    for ref in order:
        f, t, fab, outline, own = info[ref]
        ocx, ocy = own.Centre().x, own.Centre().y
        reach = pcbnew.FromMM(check_r10.FAB_REF_REACH - 0.1)
        others = [(r, o[2], o[3]) for r, o in info.items() if r != ref and o[2] == fab and o[3].OutlineCount()]
        found = None
        for inside in (True, False):
            for h, w in FAB_SIZES:
                t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(w), pcbnew.FromMM(h)))
                t.SetTextThickness(pcbnew.FromMM(round(max(0.15 * h, 0.05), 4)))
                for ang in (0, 90):
                    t.SetTextAngleDegrees(ang)
                    t.SetPosition(pcbnew.VECTOR2I(int(ocx), int(ocy)))
                    bb0 = ink_poly(t, fab).BBox()
                    hw, hh = bb0.GetWidth() / 2, bb0.GetHeight() / 2
                    dx0, dy0 = bb0.Centre().x - ocx, bb0.Centre().y - ocy
                    if inside:
                        if 2 * hw > own.GetWidth() or 2 * hh > own.GetHeight():
                            continue
                        span = pcbnew.ToMM(max(own.GetWidth(), own.GetHeight())) / 2
                    else:
                        span = pcbnew.ToMM(max(own.GetWidth(), own.GetHeight())) / 2 + check_r10.FAB_REF_REACH + 2
                    n = int(span / step) + 1
                    cands = sorted(((i * i + j * j, i, j) for i in range(-n, n + 1) for j in range(-n, n + 1)))
                    for _, i, j in cands:
                        cx = ocx + pcbnew.FromMM(i * step)
                        cy = ocy + pcbnew.FromMM(j * step)
                        # text centre at (cx, cy) - ink offset
                        dist = math.hypot(max(own.GetLeft() - cx, 0, cx - own.GetRight()),
                                          max(own.GetTop() - cy, 0, cy - own.GetBottom()))
                        if dist > reach:
                            continue
                        if inside and not (own.GetLeft() + hw <= cx <= own.GetRight() - hw
                                           and own.GetTop() + hh <= cy <= own.GetBottom() - hh):
                            continue
                        t.SetPosition(pcbnew.VECTOR2I(int(cx - dx0), int(cy - dy0)))
                        poly = ink_poly(t, fab)
                        bb = poly.BBox()
                        if outline.OutlineCount():
                            grown = pcbnew.SHAPE_POLY_SET(poly)
                            grown.Inflate(G, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, pcbnew.FromMM(0.005))
                            if hits(grown, outline):
                                continue
                        gb = box_poly(bb, G)
                        bad = False
                        for r2, olay, oout in others:
                            obb = oout.BBox()
                            if not obb.Intersects(gb.BBox()):
                                continue
                            if hits(gb, oout) or obb.Contains(bb.Centre()):
                                bad = True
                                break
                        if bad:
                            continue
                        if any(lay == fab and pb.Intersects(gb.BBox()) and hits(gb, pp)
                               for lay, pp, pb in placed.values()):
                            continue
                        found = (h, w, ang, t.GetPosition())
                        break
                    if found:
                        break
                if found:
                    break
            if found:
                break
        if found is None:
            raise RuntimeError(f'no Fab reference spot for {ref}')
        h, w, ang, pos = found
        poly = ink_poly(t, fab)
        bp = box_poly(poly.BBox())
        placed[ref] = (fab, bp, bp.BBox())
        result[ref] = (h, w, ang, round(pcbnew.ToMM(pos.x), 4), round(pcbnew.ToMM(pos.y), 4))
    return result


# ----------------------------------------------------------------------------------------------------------------------
def draft(b):
    silk.W, silk.L = r9_post.outline(b)
    for d in list(b.GetDrawings()):
        if d.GetLayer() in P.SILKS:
            b.Delete(d)
    for f in b.GetFootprints():
        for field in f.GetFields():
            field.SetVisible(False)
        t = f.Reference()
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.0), pcbnew.FromMM(1.0)))
        t.SetTextThickness(pcbnew.FromMM(0.15))
    silks = {side: P.Silk10(b, side) for side in ('F', 'B')}
    pads = r9_post.connector_pads(b)
    boxes = P.connector_boxes(b)
    log, missing = {}, []

    def clip(x0, y0, x1, y1):
        return (max(P.EDGE_MM, x0), max(P.EDGE_MM, y0), min(silk.W - P.EDGE_MM, x1), min(silk.L - P.EDGE_MM, y1))

    def pin(ref, number, name):
        x, y = silk.pad(b, ref, number)
        regions = [(clip(x - r9_post.PIN_REACH, y - r9_post.PIN_REACH, x + r9_post.PIN_REACH,
                         y + r9_post.PIN_REACH), ('F', 'B'), (90, 0))]
        result = r9_post.put_pin(b, silks, f'{number}:{name}', pads, {(ref, number)}, (x, y), regions)
        log[f'{ref} {number}:{name}'] = result
        if result is None:
            missing.append(('pin', f'{ref} {number}:{name}'))

    terminals = dict(check_r11.TERMINAL_PINS_R11)
    # 1. the wire-pad and switch terminal legends first (J121 E1- / E1+, J1, J400: pyro, battery, arming)
    for ref in WIRED_FIRST:
        for number, name in terminals[ref]:
            pin(ref, number, name)
    # 2. the revision, on the bottom (pinned)
    whole = (P.EDGE_MM, P.EDGE_MM, silk.W - P.EDGE_MM, silk.L - P.EDGE_MM)
    result = silk.label(b, silks, r11_post.REV, (silk.W / 2, silk.L / 2), whole, (0, 90), ('B',), size=1.0)
    log[r11_post.REV] = result
    if result is None:
        raise RuntimeError(f'no room for {r11_post.REV} on the bottom')
    # 2b. the designators K-legends requires shown (check_r10.SHOWN_REFS), before the other legends take the room
    shown = []
    with check_r10.patched(r8_post, RunOnSilk=P.Silk10):
        for ref in check_r10.SHOWN_REFS:
            got = r8_post.place_designator(b, ref)
            if got is None:                      # a larger reach for the required ones (the gate measures ownership)
                got = place_near_courtyard(b, ref, SHOWN_CAP)
            log[f'designator {ref}'] = got
            if got is None:
                missing.append(('ref', ref))
                continue
            t = b.FindFootprintByReference(ref).Reference()
            silks['B' if t.GetLayer() == pcbnew.B_SilkS else 'F'].add(silk.ink(t))
            shown.append(ref)
    # 3. connector words
    for word, ref in check_r10.WORD_LEGENDS_R10.items():
        axis = pin_axis(b, ref) if word in SPAN_WORDS else None
        result = put_word(b, silks, word, ref, span_axis=axis)
        if result is None:
            result = put_word(b, silks, word, ref, span_axis=axis, reach=12.0)
        log[word] = result
        if result is None:
            missing.append(('word', word))
    # 4. the GH ports' pin legends, J2's SWD rows, J122's harness note
    for ref, mapping in check_r11.TERMINAL_PINS_R11:
        if ref not in WIRED_FIRST:
            for number, name in mapping:
                pin(ref, number, name)
    for text in sorted(P.port_rows('J2'), key=lambda t: (-len(t), t)):
        result = P.put_subject(b, silks, text, 'J2', boxes, sides=('F', 'B'))
        if result is None:
            result = P.put_subject(b, silks, text, 'J2', boxes, sides=('F', 'B'), margin=0.0)
        log[text] = result
        if result is None:
            missing.append(('port', text))
    for ref, note in P.NOTES:
        result = P.put_subject(b, silks, note, ref, boxes, sides=('F', 'B'))
        if result is None:
            result = P.put_subject(b, silks, note, ref, boxes, sides=('F', 'B'), margin=0.0)
        log[note] = result
        if result is None:
            missing.append(('note', note))
    if missing:
        print('NO LEGAL SPOT (recorded as open rows):', missing)
    # 4. pin-1 dots
    dots, no_dot = P.pin1_dots(b, silks, [r for r in DOT_PARTS if b.FindFootprintByReference(r) is not None])
    log['dots'] = dots
    log['no_dot'] = no_dot
    # 5. designators
    silk.designators(b, silks, priority=check_r10.SHOWN_REFS, fixed=set(shown))
    with check_r10.patched(r8_post, RunOnSilk=P.Silk10):
        for _ in range(4):
            bad = {ref: ('courtyard',) for ref in r7_post.courtyard_offenders(b)}
            bad.update({ref: ('run-on',) for ref in r8_post.run_on_offenders(b) if ref not in bad})
            if not bad:
                break
            for ref in sorted(bad, key=lambda r: (r not in check_r10.SHOWN_REFS, r)):
                r8_post.place_designator(b, ref)
    # 6. Fab references
    log['fab'] = place_fab(b)
    return log, missing


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', type=Path)
    ap.add_argument('--out', type=Path, default=ROOT / 'm3_design/r11_legends.tsv')
    ap.add_argument('--save', type=Path, help='save the drafted board copy here (inspection only)')
    args = ap.parse_args()
    with check_r10.patched(P, supports=r11_post.supports), check_r10.patched(r9_post, OWN_MARGIN=OWN_MARGIN_R11):
        b = pcbnew.LoadBoard(str(args.board.resolve()))
        log, missing = draft(b)
    for k, v in log.items():
        if k != 'fab':
            print(k, v)
    hidden = sorted(f.GetReference() for f in b.GetFootprints() if not f.Reference().IsVisible())
    print('hidden designators', len(hidden), ' '.join(hidden))
    rows = r11_post.table_rows(b) + [('open', text, kind, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0) for kind, text in missing]
    r11_post.write_table(args.out, rows)
    print(f'wrote {len(rows)} rows to {args.out}')
    if args.save:
        pcbnew.SaveBoard(str(args.save), b, True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
