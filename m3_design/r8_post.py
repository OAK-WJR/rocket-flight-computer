#!/usr/bin/env python3
"""R8 silkscreen and assembly references (M3-ASSY-R8, build step 8; R8_DECISIONS D71): the last build stage, after
r8_ground.py. No copper, zone, footprint position or pad edit (asserted).

usage: <KiCad python3> -I m3_design/r8_post.py [--board m3_design/assembly_review/m3.kicad_pcb] [--report out.json]

The whole board-level silkscreen is drawn again from nothing: r8_pcb.py kept R7's legends of the unmoved parts, which
now sit beside re-placed parts and the new vias. Every board-level silkscreen item is deleted, then, in this order (the
R7 finish, m3_design/r7_post.py, with the R8 revision and every legend about a part placed beside that part):
  1. the SMA jack legends GNSS (J30) and RADIO (J31), on the top just forward of each jack, 0.2 mm clear of every via
     and with nothing else within 0.8 mm of them (r7_post's pass-3 DFM-06 rule);
  2. the legends about one part, each at the free spot nearest that part's courtyard and within LEGEND_REACH (6 mm,
     AGENTS.md; tools/check_r7.legend_subjects gates it): TP30 SAFEBOOT; the connector words ARM, IGN, BAT, CAM,
     SWD, SERVO, PULL, top face first (the black terminals J124 / J121 are told apart by them: check_actuators 11);
     the pin tables of J9 and J2 (tools/check_r7.pin_legends) and J122; the arming and fuse notes of J124 and J1;
  3. the terminal pin legends (J124 1:BUS1 2:RAW, J121 1:E1- 2:E1+, J1 1:BAT+ 2:GND 3:SW 4:SW, J123 1:PULL 2:GND)
     beside their pads, each inside its pin's own cell (the half of the window nearer its pin than the part's other
     pins), J1's 2 / 3 / 4 in the forward-edge strip over their pins (fix pass 1, R8P1-REQUIREMENTS-03: each legend's
     nearest connector pin is its own, gated by check_r8.terminal_legends), and J122's row numbers;
  4. the revision legend M3-ASSY-R8 and JLC's order-number placeholder JLCJLCJLCJLC (ORDERING), both required;
  5. pin-1 dots (r5_post.DOT_PARTS), then every designator by the R4 rule (r5_post.designators: >= 1.0 mm text, never
     over a pad, via or hole or off the board, nearer its own part than any other; a crowded one goes on the bottom
     under its part; one with no such spot is hidden and kept on the Fab layer), then the courtyard test on every
     visible designator (r7_post: its ink no nearer another part's courtyard than its own); one that fails is placed
     again with the test, or hidden; the run fails if one is left;
  6. Fab-layer designators for the assembly drawing (r5_post.fab_refs) and the title-block revision.
R8 adds one rule to every placement (RunOnSilk, D71): no text ends within RUN_ON (0.6 mm) of another text on its line
(end to end, or pointing into it at any angle), so a designator never runs into a legend or another designator and
reads as one string (R7 had 'R33TH1', 'C82C29', 'J1211:E1-'). A designator found in a run-on pair at the end is placed
again with both tests, or hidden.
The stage runs once, on r8_ground.py's board (it refuses a board that already carries the J9 / J2 pin tables: a second
pass over its own output does not reproduce it). Any essential legend that does not fit, or a legend about a part
beyond LEGEND_REACH, fails the run. The rigid digests
(check_r8 D15) and a digest of every copper item, zone and pad are asserted unchanged. Deterministic (fixed KIID seed,
no random search, no refill: silkscreen does not touch the fill): a rebuild reproduces the board byte for byte.
"""
import argparse
import hashlib
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
import r7_post  # noqa: E402  (its placement helpers are generic; frozen with the R7 record)

REV = 'M3-ASSY-R8'
KIID_SEED = 8816                # r8_ground.py uses 8815
LEGEND_REACH = r7_post.LEGEND_REACH
PORTS = r7_post.PORTS           # J9 CAM 5V GND TX RX (camera-side UART names), J2 SWD 3V3 SWDIO NRST SWCLK GND NC
WORDS = (('J124', 'ARM'), ('J121', 'IGN'), ('J1', 'BAT'), ('J9', 'CAM'), ('J2', 'SWD'), ('J122', 'SERVO'),
         ('J123', 'PULL'))
TERMINAL_PINS = check_r8.TERMINAL_PINS       # J124 1:BUS1 2:RAW, J121 1:E1- 2:E1+, J1 1:BAT+ 2:GND 3:SW 4:SW, J123 1:PULL 2:GND
# window (near point offset, half sizes, sides, angles) per terminal; J1's middle and outer pins: the forward-edge strip
# (y 116.8, between J1's body and the edge), over the pin (fix pass 1)
# (the cell margin: J123's 2.0 mm pitch takes 0.9 mm, half a vertical legend's ink width, so the whole legend stays on
# its pin's side of the midline)
PIN_WINDOW = {'J124': ((0, -3), (3.8, 8), ('F', 'B'), (90, 0), 0.25), 'J121': ((0, -3), (3.8, 8), ('F', 'B'), (90, 0), 0.25),
              'J1': ((0, -3), (3.8, 8), ('F', 'B'), (90, 0), 0.25), 'J123': ((0, 3), (2.5, 8), ('B', 'F'), (90, 0), 0.9)}
J1_STRIP_Y = 116.8
PIN_STRIP = {('J1', '2'), ('J1', '3'), ('J1', '4')}
NOTES = (('J124', 'J124 2-FUSE-1: ARM LAST'), ('J124', 'J124: 5A FAST / 2S'), ('J1', 'J1 BAT LEAD: 15A FUSE'))
ORDER_MARK = 'JLCJLCJLCJLC'
RUN_ON = 0.6                    # mm: end-to-end gap between two texts on one line (about a word space at 1.0 mm text)
AXIS = 1.15                     # a box this much longer one way than the other has a reading direction
DOT = 0.5                       # mm: an ink box smaller than this both ways is a mark, not text


def axis(r):
    """The reading direction of an ink box: 'h', 'v', or None for a box near square (one character, a dot)."""
    w, h = r[2] - r[0], r[3] - r[1]
    return 'h' if w > AXIS * h else 'v' if h > AXIS * w else None


def _ends_into(a, c, gap):
    """Text box a has a reading direction and c lies on its line (overlapping a's band across it by at least half the
    thinner of the two) closer than gap off one of a's ends, or overlapping it along the line."""
    d = axis(a)
    if d is None:
        return False
    i, j = (1, 0) if d == 'h' else (0, 1)            # i: across a's line, j: along it
    across = min(a[i + 2], c[i + 2]) - max(a[i], c[i])
    along = max(c[j] - a[j + 2], a[j] - c[j + 2])
    return across >= 0.5 * min(a[i + 2] - a[i], c[i + 2] - c[i]) and along < gap


def run_on(a, c, gap=RUN_ON):
    """Ink boxes a and c read as one string: one of them runs, along its reading direction, into the other within gap
    (two texts end to end on one line, or a text pointing straight into another, whatever the other's direction).
    Dots (pin-1 marks, under DOT mm both ways) are not text."""
    if max(a[2] - a[0], a[3] - a[1]) < DOT or max(c[2] - c[0], c[3] - c[1]) < DOT:
        return False
    return _ends_into(a, c, gap) or _ends_into(c, a, gap)


class RunOnSilk(silk.Silk):
    """r5_post.Silk that also keeps every new text off the ends of the texts already placed (run_on). Texts are the
    boxes added without an explicit gap (r5_post.label / designators, r7_post.label_near) and the board texts present
    when it is built; pads, vias, holes, bodies and footprint graphics are added with their gap, as in Silk."""

    def __init__(self, b, side, strict_bodies=True):
        self.texts = []
        super().__init__(b, side, strict_bodies)
        for d in b.GetDrawings():
            if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == self.layer:
                self.texts.append(silk.ink(d))

    def add(self, r, gap=None):
        if gap is None:
            self.texts.append(r)
            gap = silk.GAP
        super().add(r, gap)

    def free(self, r):
        return super().free(r) and not any(run_on(r, c) for c in self.texts)


def texts_on(b, layer, skip=None):
    """Ink boxes of the visible designators and board texts on one silkscreen layer, but the designator of the part
    named skip (SWIG hands out a new proxy per call: parts are compared by reference, never with `is`)."""
    out = [silk.ink(d) for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == layer]
    out += [silk.ink(f.Reference()) for f in b.GetFootprints() if f.GetReference() != skip and
            f.Reference().IsVisible() and f.Reference().GetLayer() == layer]
    return out


def run_on_offenders(b):
    """Visible designators whose ink runs on into another text on their layer."""
    bad = []
    for f in b.GetFootprints():
        t = f.Reference()
        if t.IsVisible() and any(run_on(silk.ink(t), c) for c in texts_on(b, t.GetLayer(), skip=f.GetReference())):
            bad.append(f.GetReference())
    return sorted(bad)


def courtyard_fails(b, f):
    """r7_post.courtyard_offenders for one part: its visible designator's ink lies nearer another part's courtyard
    (on the face the text is on, centres within 8 mm) than its own part's courtyard (ink polygon to courtyard
    polygon)."""
    t = f.Reference()
    yard = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    if not t.IsVisible() or not yard.OutlineCount():
        return False
    ink_ = pcbnew.SHAPE_POLY_SET()
    t.TransformShapeToPolygon(ink_, t.GetLayer(), 0, silk.MM(0.002), pcbnew.ERROR_INSIDE)
    back = t.GetLayer() == pcbnew.B_SilkS
    c = ink_.BBox().Centre()
    own = r7_post._poly_gap(ink_, yard)
    for g in b.GetFootprints():
        if g.GetReference() == f.GetReference() or g.IsFlipped() != back:
            continue
        ps = g.GetCourtyard(pcbnew.B_CrtYd if back else pcbnew.F_CrtYd)
        if not ps.OutlineCount():
            continue
        bb = ps.BBox().Centre()
        if abs(bb.x - c.x) < silk.MM(8) and abs(bb.y - c.y) < silk.MM(8) and r7_post._poly_gap(ink_, ps) < own:
            return True
    return False


def place_designator(b, ref, cap=1.5, margin=0.15):
    """r7_post.courtyard_designator with RunOnSilk: the free spot nearest ref's part whose ink is within `cap` of its
    own courtyard and nearer it (by `margin`) than any other part's courtyard and runs into no text; a top part's on
    the top first, then under the part on the bottom; a bottom part's on the bottom; with none the designator is
    hidden (kept on the Fab layer)."""
    f = b.FindFootprintByReference(ref)
    t = f.Reference()
    own = r7_post._courtyard(f)
    others = [r7_post._courtyard(g) for g in b.GetFootprints() if g.GetReference() != ref and
              abs(silk.mm(g.GetPosition().x) - silk.mm(f.GetPosition().x)) < 10 and
              abs(silk.mm(g.GetPosition().y) - silk.mm(f.GetPosition().y)) < 10]
    others = [o for o in others if o[2] > o[0]]
    cx, cy = silk.mm(f.GetPosition().x), silk.mm(f.GetPosition().y)
    for side in (('B',) if f.IsFlipped() else ('F', 'B')):        # a bottom part's designator stays on the bottom
        t.SetVisible(False)
        s = RunOnSilk(b, side)
        for g in b.GetFootprints():
            r_ = g.Reference()
            if g.GetReference() != ref and r_.IsVisible() and r_.GetLayer() == s.layer:
                s.add(silk.ink(r_))
        t.SetLayer(s.layer)
        t.SetMirrored(side == 'B')
        rr_ = 0.0
        while rr_ <= 3.0:
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
                    if side == 'B' and not f.IsFlipped() and not (own[0] <= x <= own[2] and own[1] <= y <= own[3]):
                        continue                          # a top part's on the bottom only under the part itself
                    if any(silk._gap(r, o) < d_own + margin for o in others):
                        continue
                    t.SetVisible(True)
                    if not courtyard_fails(b, f):
                        return side, (x, y)
                    t.SetVisible(False)
            rr_ += 0.1
    t.SetVisible(False)
    if ref not in silk.HIDDEN:
        silk.HIDDEN.append(ref)
    return None


def fixed_digest(b):
    """Every copper item, zone (outline and fill) and pad: the stage may change silkscreen and Fab text only."""
    h = hashlib.sha256()
    for t in sorted(b.GetTracks(), key=lambda t: t.m_Uuid.AsString()):
        via = t.GetClass() == 'PCB_VIA'
        h.update(repr((t.GetClass(), t.GetNetname(), t.GetLayer(), t.GetStart().x, t.GetStart().y, t.GetEnd().x,
                       t.GetEnd().y, t.GetWidth(pcbnew.F_Cu) if via else t.GetWidth(),
                       t.GetDrillValue() if via else 0)).encode())
    for z in sorted(b.Zones(), key=lambda z: z.m_Uuid.AsString()):
        h.update(repr((z.GetZoneName(), z.GetNetname(), z.GetIsRuleArea(), z.Outline().Format())).encode())
        for lay in z.GetLayerSet().Seq():
            if z.HasFilledPolysForLayer(lay):
                h.update(z.GetFilledPolysList(lay).Format().encode())
    for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        h.update(repr((f.GetReference(), f.GetPosition().x, f.GetPosition().y, f.GetOrientationDegrees(),
                       f.IsFlipped())).encode())
        for p in f.Pads():
            h.update(repr((p.GetNumber(), p.GetNetname(), p.GetPosition().x, p.GetPosition().y)).encode())
    return h.hexdigest()


CELL_MARGIN = 0.25             # mm: a pin legend's centre keeps this inside its pin's half (label() places centres)


def own_cell(region, pins, number, margin=CELL_MARGIN):
    """The centre region (x0, y0, x1, y1) of a pin legend, cut `margin` short of the midline to each of the part's
    other pins in the same row or column: a centred legend no wider than the pitch is then nearer its own pin than
    any of them."""
    x0, y0, x1, y1 = region
    px, py = pins[number]
    for other, (qx, qy) in pins.items():
        if other == number:
            continue
        if abs(qy - py) < 1e-6:
            mid = (px + qx) / 2
            x1, x0 = (min(x1, mid - margin), x0) if qx > px else (x1, max(x0, mid + margin))
        elif abs(qx - px) < 1e-6:
            mid = (py + qy) / 2
            y1, y0 = (min(y1, mid - margin), y0) if qy > py else (y1, max(y0, mid + margin))
    return (x0, y0, x1, y1)


def finish(b):
    """Place every legend, the designators and the Fab references; return the placement evidence."""
    outline = b.GetBoardEdgesBoundingBox()
    if abs(silk.mm(outline.GetX())) > 0.1 or abs(silk.mm(outline.GetY())) > 0.1:
        raise RuntimeError('R8 silkscreen expects the board origin at (0, 0)')
    silk.W, silk.L = silk.mm(outline.GetWidth()), silk.mm(outline.GetHeight())
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
    silks = {side: RunOnSilk(b, side) for side in ('F', 'B')}
    placed, missing = {}, []

    def box(cx, cy, rx, ry):
        return (max(0.4, cx - rx), max(0.4, cy - ry), min(silk.W - 0.4, cx + rx), min(silk.L - 0.4, cy + ry))

    whole = (0.4, 0.4, silk.W - 0.4, silk.L - 0.4)

    def put(text, near, region, sides=('F', 'B'), angles=(0, 90), about=None):
        """A legend at the free spot in region nearest `near`; `about` names its part in the report (pin legends
        such as 2:GND repeat across connectors)."""
        result = silk.label(b, silks, text, near, region, angles, sides, size=1.0)
        key = f'{about} {text}' if about else text
        placed[key] = result
        if result is None:
            missing.append(key)
        return result

    def put_near(text, ref, sides=('B', 'F')):
        """A legend about part ref beside it (r7_post.label_near, within LEGEND_REACH of its courtyard), or the run
        fails: R8 has no whole-board fallback."""
        result = r7_post.label_near(b, silks, text, ref, sides=sides)
        placed[text] = None if result is None else result[:4]
        if result is None:
            missing.append(f'{text} (within {LEGEND_REACH} mm of {ref})')
        return result

    # 1. the SMA jack legends (r7_post: vias kept JACK_VIA_GAP clear, nothing else within JACK_LEGEND_GAP afterwards)
    jack = {side: RunOnSilk(b, side) for side in ('F', 'B')}
    for side in jack:
        for v in b.GetTracks():
            if v.GetClass() == 'PCB_VIA':
                jack[side].add(silk.bx(v), r7_post.JACK_VIA_GAP)
    for ref, name in (('J30', 'GNSS'), ('J31', 'RADIO')):
        pos = silk.fp_of(b, ref).GetPosition()
        cx, cy = silk.mm(pos.x), silk.mm(pos.y)
        result = silk.label(b, jack, name, (cx, cy + 3.0), box(cx, cy + 4.5, 6.0, 5.0), (0, 90), ('F',))
        if result is None:
            result = silk.label(b, jack, name, (cx, cy + 3.0), box(cx, cy + 4.0, 5.5, 4.5), (0,), ('F', 'B'))
        placed[name] = result
        if result is None:
            missing.append(name)
            continue
        t = [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == name][-1]
        silks[result[0]].add(silk.ink(t), r7_post.JACK_LEGEND_GAP)
    # 2. legends about one part, beside it; the connector words on the top first (the terminals' own face)
    put_near('TP30 SAFEBOOT', 'TP30', sides=('F', 'B'))
    for ref, word in WORDS:
        put_near(word, ref, sides=('F', 'B'))
    for ref, (_, pins) in PORTS.items():
        for start in range(0, len(pins), 2):
            row = ref + ' ' + ' '.join(f'{i + 1}:{pins[i]}' for i in range(start, min(start + 2, len(pins))))
            put_near(row, ref)
    put_near('J122 1:S 2:+ 3:GND', 'J122')
    for ref, note in NOTES:
        put_near(note, ref)
    # 3. terminal pin legends beside their pads, each in its pin's own cell (R7's windows cut at the midline to the
    # part's neighbouring pins), J1's 2 / 3 / 4 in the forward-edge strip; J122's row numbers
    for ref, mapping in TERMINAL_PINS:
        pins = {number: silk.pad(b, ref, number) for number, _ in mapping}
        (ox, oy), (rx, ry), sides, angles, margin = PIN_WINDOW[ref]
        for number, name in mapping:
            x, y = pins[number]
            if (ref, number) in PIN_STRIP:
                near, region, sides_, angles_ = (x, J1_STRIP_Y), box(x, J1_STRIP_Y, 2.54, 0.9), ('F',), (0,)
            else:
                near, region, sides_, angles_ = (x + ox, y + oy), box(x, y, rx, ry), sides, angles
            put(number + ':' + name, near, own_cell(region, pins, number, margin), sides=sides_, angles=angles_,
                about=ref)
    for number, row in (('3', '1'), ('6', '2'), ('9', '3'), ('12', '4')):
        x, y = silk.pad(b, 'J122', number)
        put(row, (x - 2, y), box(x - 2, y, 1.3, 1.3), angles=(0,), about='J122 row')
    # 4. revision legend and JLC's order-number placeholder
    put(REV, (23, silk.L - 6), whole, sides=('B', 'F'))
    put(ORDER_MARK, (23, 94), whole, sides=('B', 'F'))
    if missing:
        raise RuntimeError('Essential R8 silkscreen did not fit: ' + ', '.join(missing))
    # 5. pin-1 dots, designators, the courtyard test
    silk.pin1_dots(b, silks)
    silk.designators(b, silks)
    moved = {}
    for _ in range(4):
        bad = {ref: ('courtyard',) + why for ref, why in r7_post.courtyard_offenders(b).items()}
        bad.update({ref: ('run-on',) for ref in run_on_offenders(b) if ref not in bad})
        if not bad:
            break
        for ref in sorted(bad):
            moved[ref] = (bad[ref], place_designator(b, ref))
    left = r7_post.courtyard_offenders(b)
    if left:
        raise RuntimeError(f"designators still nearer another part's courtyard than their own: {left}")
    left = run_on_offenders(b)
    if left:
        raise RuntimeError(f'designators still running into another text: {left}')
    for ref, (why, got) in sorted(moved.items()):
        print(f'  {why[0]}: {ref} {why[1:] or ""} -> '
              f'{"hidden" if got is None else f"{got[0]}.SilkS at ({got[1][0]:.2f}, {got[1][1]:.2f})"}')
    small = [f.GetReference() for f in b.GetFootprints() if f.Reference().IsVisible() and
             silk.mm(f.Reference().GetTextHeight()) < 1.0 - 1e-6]
    if small:
        raise RuntimeError(f'designators below 1.0 mm text (REQUIREMENTS M2): {small}')
    # 6. Fab references, title block
    silk.fab_refs(b)
    b.GetTitleBlock().SetRevision(REV)
    issues = check_r7.pin_legends(b) + check_r7.legend_subjects(b) + check_r8.terminal_legends(b)[0]
    if issues:
        raise RuntimeError('legend contract: ' + '; '.join(issues))
    hidden = sorted(silk.HIDDEN, key=lambda r: (r.rstrip('0123456789'), int(r[len(r.rstrip('0123456789')):] or 0)))
    visible = sum(1 for f in b.GetFootprints() if f.Reference().IsVisible())
    bottom_of_top = sorted(f.GetReference() for f in b.GetFootprints() if f.Reference().IsVisible() and
                           not f.IsFlipped() and f.Reference().GetLayer() == pcbnew.B_SilkS)
    print(f'R8 silkscreen: {sum(v is not None for v in placed.values())} legends; {visible} designators shown '
          f'({len(bottom_of_top)} top parts\' on the bottom under their part); {len(hidden)} hidden, kept on Fab: '
          f'{" ".join(hidden)}')
    return {'revision': REV, 'legends': {k: list(v) if v else None for k, v in placed.items()},
            'designators_shown': visible, 'top_designators_under_part_on_bottom': bottom_of_top,
            'hidden_references': hidden,
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
        raise SystemExit('r8_post runs once, on the ground-stage board: this board already carries its pin tables')
    issues, _ = check_r8.rigid(b)
    assert not issues, issues
    before = fixed_digest(b)
    evidence = finish(b)
    assert fixed_digest(b) == before, 'r8_post changed copper, a zone, a pad or a footprint position'
    assert pcbnew.SaveBoard(str(board), b, True), 'save failed'
    b = pcbnew.LoadBoard(str(board))
    issues, digests = check_r8.rigid(b)
    assert not issues, issues
    assert fixed_digest(b) == before, 'the saved board differs in copper, zones, pads or footprint positions'
    print(f'r8_post: saved {board.name}; rigid digests {len(digests)}/12 equal R7; copper, zones and pads unchanged')
    if args.report:
        args.report.write_text(json.dumps(evidence, indent=1) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
