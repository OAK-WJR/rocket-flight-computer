#!/usr/bin/env python3
"""R10 silkscreen, assembly references and the final zone fill (M3-ASSY-R10; R10_DECISIONS D-R2-16, D-R3 silkscreen):
the post stage, after r10_route.py's ground family. No copper, zone outline, pad or footprint position edit (asserted by
R8's digest of every copper item, zone and pad before and after; the zone fill is redone last and must reproduce the fill
it found).

usage: <KiCad python3> -I m3_design/r10_post.py [--board m3_design/assembly_review/m3.kicad_pcb] [--report out.json]

R9's post stage (m3_design/r9_post.py, whose placement helpers are imported, not copied) on R10's geometry. First every
footprint whose silkscreen differs from the project library (kilib/rocket.pretty: R3's library pass clipped footprint
outlines 0.15 mm off their pad openings and removed Q120 / Q121's stray EasyEDA arc) gets the library's silkscreen
graphics (sync_silk; nothing else in a footprint may differ, asserted with KiCad's own library comparison). Every
board-level silkscreen item is deleted and every footprint field hidden, then, in this order:
  1. Connector subject legends; wired DB125 contacts use individual terminal-pin legends;
     then the legends about one part, each at the free spot nearest that part's courtyard within LEGEND_REACH (6 mm,
     AGENTS.md; check_r7.legend_subjects gates it): the connector words (check_r10.WORD_LEGENDS_R10, the one list
     K-legends also gates: IGN, BAT, CAM, SWD, SERVO, GPS, RADIO, SWITCH), top face first, RADIO and BAT at their
     reviewed WORD_SPOTS; the port pin tables (PORTS: J9 in the board-side
     convention with its supply, J2, J410 and J420), J122's five-pin table and harness note (O3 / O6), the port tables and the
     notes also with their subject the nearest connector to the legend's centre by SUBJECT_MARGIN (put_subject), J2's
     rows by 0 mm where they can (else beside J2 by label_near, listed in the evidence);
  2. the terminal pin legends (check_r10.TERMINAL_PINS_R10: J121 1:E1- 2:E1+, J1 1:BAT+ 2:GND,
     J400 1:SW 2:SW), each at the free spot nearest its own pin whose text box has that pin as its
     nearest connector pin by OWN_MARGIN (r9_post.put_pin), top face first;
  3. the revision legend M3-ASSY-R10 and JLC's order-number placeholder JLCJLCJLCJLC (ORDERING), both required;
  4. J122's top-side row key (J122_TOP_ROWS beside the rows; the harness note is on the top), where the top has room
     (optional);
  5. pin-1 dots beside pad 1 of DOT_PARTS (pin1_dots: r9_post's mark and search, plus the dot nearer its own pad 1 than
     any other part's pad 1 by DOT_OWN_MARGIN), then every designator by the R4 rule (r5_post.designators, required
     SHOWN_REFS first: >= 1.0 mm
     text, never over a pad, via or hole or off the board, nearer its own part than any other; a crowded one goes on the
     bottom under its part; one with no such spot is hidden and kept on the Fab layer), then R8's courtyard and run-on
     tests (r8_post); one that fails is placed again or hidden;
  6. Fab-layer designators (r5_post.fab_refs, r9_post.fab_clear) and the title-block revision;
  7. the zone fill: every zone is filled before step 1 (the routing families save them unfilled) and again last,
     after the silkscreen; the two fills must agree (R8's digest covers the fill).
Every placement keeps SILK_GAP (R8's 0.15 mm plus 0.005 mm) from pads, vias, holes and other silkscreen plus each pad's
own solder-mask expansion (Silk10), and keeps out of the M3 support hardware circles (fit_check's 3.5 mm bottom standoff and 3.8 mm top
washer radii). The run fails on: any essential legend that does not fit, a terminal legend whose nearest pin is not its
own, a note or port table whose subject is not its nearest connector by SUBJECT_MARGIN,
any silkscreen item (footprint graphics included) nearer than SILK_PAD to a pad's solder-mask opening, a pin-1 mark
(footprint or dot) not nearer its own pad 1 by DOT_OWN_MARGIN, a placed text or dot inside a support circle, or
duplicate ids. A legend beyond LEGEND_REACH is recorded for review (AUD-10), with a 12 mm search fallback.
Runs once, on the ground-stage board (refuses a board that already carries silkscreen text).
Deterministic (fixed KIID seed, no random search): a rebuild reproduces the board byte for byte.
"""
import argparse
import json
import math
from pathlib import Path
import re
import sys

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r7  # noqa: E402
import check_r8  # noqa: E402
import check_r10  # noqa: E402
import fit_check  # noqa: E402  (support geometry: board_geometry, retention_holes, the hardware radii)
import r5_post as silk  # noqa: E402
import r7_post  # noqa: E402
import r8_post  # noqa: E402
import r9_post  # noqa: E402  (put_pin, put_plug_row, fab_clear, outline, connector_pads, owner_margin)

REV = 'M3-ASSY-R10'
silk.EDGE = 0.6                # R5-MFG-02: every silkscreen stroke >= 0.5 mm inside the outline (ink boxes exclude the half stroke)
EDGE_MM = 0.6
KIID_SEED = 10120               # r10_pcb 10103, r10_route families 10110-10118
LEGEND_REACH = r7_post.LEGEND_REACH
REACH_MARGIN = 0.1             # mm: label_near's box gap against legend_subjects' polygon ink (rounding)
SILKS = (pcbnew.F_SilkS, pcbnew.B_SilkS)
# Port pin tables (R3-REQ-04 / R3-BOM-02): pin 1 the supply the port delivers, then GND, then the board-side UART
# directions, TXO = the board transmits on this pin, RXI = the board receives on it (J9 pin 3 CAM_RX_WIRE, pin 4
# CAM_TX_WIRE; CAM_5V from PORT_5V3, 5.456 V nominal, through TPS2553 U402). AUD-8 frees room for the GPS/radio tables;
# AUD-10 treats the 6 mm subject distance as a review finding while preserving text, clearance and ownership rules.
PORTS = {'J2': ('SWD', check_r10.PORT_LEGENDS_R10['J2'])}
SUBJECT_PORTS = ()  # Every wired terminal uses the individually checked TERMINAL_PINS contract.
NO_ROOM_PORTS = {}
WORDS = tuple((ref, word) for word, ref in check_r10.WORD_LEGENDS_R10.items())    # D-R19-06: the one word list
# D-R19-06 (R19-MFG-01 / R19-GATE-06): reviewed word spots (side, x, y, angle) in place of the nearest-gap search, which put
# RADIO on the J410 / J420 seam (nearer J410 by its centre). RADIO sits inside J420's courtyard y-span (24.055 .. 40.065)
# between the GND / RADIO_TX vias, 4.8 mm from the seam. BAT stays at J1's north end, in the J400 / J1 gap, but east of
# the board-edge strip that 1:BAT+ now needs (D-R19-08); with 2:SW on the bottom it is the only text on that line. IGN
# moves one line north so that J121's 1:E1- can sit between it and the J121 body, wholly outside the body's envelope.
WORD_SPOTS = {'RADIO': ('F', 32.18, 29.5, 0), 'BAT': ('F', 4.75, 70.475, 0), 'IGN': ('F', 2.456, 48.95, 0),
              # D-R19-14: AUX at J440's north end, east of its envelope, as GPS sits at J410's (inside the y-span)
              'AUX': ('F', 13.4, 10.2, 0)}
# D-R19-08 (R19-MEC-01 / R19-MFG-04 and the coordinator's top-render check): every terminal pin legend lies wholly outside
# the DB125 VRML fit envelopes, which hide anything under them in the top render, and no pin legend shares a line with
# another terminal's word. Reviewed spots (side, x, y, angle), each still nearest its own pin by OWN_MARGIN:
#   1:E1- on J121's north line under IGN; 1:BAT+ on the board-edge strip beside J1.1 (the J400 / J1 gap is nearer J400.2);
#   2:E1+ and 2:SW on the bottom under their pins, so neither reads as part of SWITCH's or BAT's line; 1:SW, J410 4:RXI and
#   1:5V4 moved outward; 1:S1 along J122's south end, clear of the (42, 86) washer; the J410 / J420 / J9 wire-side
#   legends east of the envelope, J410 / J9 in one column and J420's two in a second, so that no two terminals' pin
#   legends run on along one column across a seam.
PIN_SPOTS = {('J121', '1'): ('F', 3.6, 50.455, 0), ('J121', '2'): ('B', 4.0, 57.6, 0),
             ('J1', '1'): ('F', 2.32, 73.0, 90), ('J400', '1'): ('F', 2.4, 63.3, 90), ('J400', '2'): ('B', 4.4, 67.6, 0),
             ('J122', '1'): ('F', 37.05, 82.37, 0), ('J9', '1'): ('F', 41.7, 56.7, 0), ('J9', '4'): ('F', 43.4, 40.55, 90),
             ('J410', '1'): ('F', 43.4, 21.05, 90), ('J410', '4'): ('F', 36.9, 7.05, 0),
             ('J420', '1'): ('F', 44.85, 37.35, 90), ('J420', '4'): ('F', 44.85, 25.45, 90),
             # D-R19-14: J440's pin-1 legend up the west board-edge strip (as 1:SW / 1:BAT+; above the body it would sit
             # under the (4, 4) washer or on C400.2). Its pin-4 legend has no top spot nearer J440.4 than J3's shell pads
             # (west and south) or J430's shell pad 11 (east) by OWN_MARGIN, so it sits on the bottom beside its pin, as
             # 2:SW does (margin 1.74 mm)
             ('J440', '1'): ('F', 2.4, 10.6, 90), ('J440', '4'): ('B', 4.2, 21.5, 0)}
# Owner, 2026-10-28: the external power switch arms the board; the separate ARM terminal and fuse notes are removed.
NOTES = (('J122', 'SERVO + FROM HARNESS'),)
NOTE_PLACE = {'SERVO + FROM HARNESS': (('F', 'B'), None)}          # the plugs mate on the top (R3-REQ-06(b))
SUBJECT_MARGIN = 1.0            # mm: a note / port table centre is this much nearer its connector's courtyard than any other
# J122's top-side key (R3-REQ-06(b)): the plugs mate on the top, where only SERVO was; row labels beside the rows
J122_TOP_ROWS = ()  # Five screw contacts have individual S1-S4/GND legends, no header rows.
TERMINAL_PINS = check_r10.TERMINAL_PINS_R10
ORDER_MARK = r8_post.ORDER_MARK
PIN_REACH = r9_post.PIN_REACH
CONNECTOR = check_r8.CONNECTOR
# pin-1 dots: R10's ICs whose footprints carry no pin-1 mark (R9's list less the removed U7 / U8, plus the port supply
# and port switch / translator-supply parts of O5; U401's M3_TPS7A91_DSK10 and Q120 / Q121's PDFN-8 carry their own mark)
# (R9's four are required; a new part with no free spot within DOT_REACH of its pad 1 is listed in the evidence and
# relies on its Fab-layer pin-1 mark for the assembly drawing)
DOT_PARTS = ('U9', 'U10', 'U11', 'U13', 'U400', 'U402', 'U410', 'U420')
DOT_REQUIRED = ('U9', 'U10', 'U11', 'U13')
DOT_REACH = r9_post.DOT_REACH
FIXED_REFS = {}  # D-AVA-01: references are placed against the new local cells.
# D-R19-12: the round 19 copper (C123 beside Q122, the second power vias) reorders the designator search, which then
# hid R80 / R81 / R123 / C5 and moved their neighbours; these keep their round 18 spots (side, x, y, angle), the search
# still placing every other designator (it checks each fixed spot is free and nearest its own part).
FIXED_REFS.update({'R80': ('F', 13.351, 71.197, 90), 'R81': ('F', 21.558, 66.697, 0), 'R123': ('F', 21.658, 72.357, 0),
                   'C5': ('B', 21.385, 70.291, 0), 'C407': ('F', 30.911, 16.635, 0), 'R89': ('F', 24.999, 71.328, 0),
                   # J121 / J400 read on the board-edge strip beside their bodies: the search would otherwise put them in
                   # the J121 / J400 and J400 / J1 gaps, on SWITCH's and BAT's lines.
                   'J121': ('F', 2.957, 57.041, 90), 'J400': ('F', 2.937, 67.617, 90),
                   # J122 reads in the C84 / J122 gap: the search's spot south of the body (beside 1:S1) is clear of the
                   # nominal body but 0.910 mm under the DB125 fit model the 3D render draws.
                   'J122': ('F', 33.3, 78.6, 90)})
# D-AVA-01: reserve an unambiguous SWD band before all other legends.
SWD_LEGENDS = {'J2 4:SWCLK': ['B', 5.0, 37.2, 0], 'J2 2:SWDIO': ['F', 5.0, 37.0, 0], 'J2 3:NRST': ['B', 10.0, 42.5, 90], 'J2 5:GND': ['B', 10.9, 35.800000000000004, 0], 'J2 1:3V3': ['F', 11.3, 35.6, 0], 'J2 6:NC': ['B', 11.4, 43.400000000000006, 90]}
DOT_OWN_MARGIN = 0.5            # mm: a pin-1 mark's centre is this much nearer its pad 1 than any other part's pad 1
MARK_R = 0.35                   # mm: a footprint silkscreen circle this small is a mark, not an outline
SILK_PAD = 0.15                 # mm: JLC pad-to-silkscreen minimum, every silkscreen item to every solder-mask opening
SILK_GAP = 0.155                # mm: the placement gap (box to box) for R8's 0.15 mm, 0.005 mm for the ink-box error


# ----------------------------------------------------------------------------------------------------------------------
# footprint silkscreen from the library
def sync_silk(b, lib):
    """Footprints whose library copy differs give the board instance the library's silkscreen graphics (the board
    footprints come from R9's board, r10_pcb.py). Nothing else may differ: KiCad's own comparison
    (FootprintNeedsUpdate, the DRC library-parity test) must pass afterwards. Returns the changed references."""
    changed = []

    def load(name):
        fp = pcbnew.FootprintLoad(str(lib), name)
        assert fp is not None, f'{name} missing from {lib}'
        fp.SetParent(b)
        return fp

    def pads(fp):
        return sorted((p.GetNumber(), p.GetPosition().x, p.GetPosition().y) for p in fp.Pads())
    for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        name = str(f.GetFPID().GetLibItemName())
        if not f.FootprintNeedsUpdate(load(name), pcbnew.BOARD_ITEM.DRC, None):
            continue
        placed = load(name)
        if f.IsFlipped():
            placed.Flip(placed.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        placed.SetOrientation(f.GetOrientation())
        placed.SetPosition(f.GetPosition())
        assert pads(placed) == pads(f), f'{f.GetReference()}: library copy does not land on the board pads'
        for g in [g for g in f.GraphicalItems() if g.GetClass() == 'PCB_SHAPE' and g.GetLayer() in SILKS]:
            f.Delete(g)
        for g in placed.GraphicalItems():
            if g.GetClass() == 'PCB_SHAPE' and g.GetLayer() in SILKS:
                d = g.Duplicate()
                d.thisown = False
                f.Add(d)
        if f.FootprintNeedsUpdate(load(name), pcbnew.BOARD_ITEM.DRC, None):
            raise RuntimeError(f'{f.GetReference()}: differs from library {name} beyond its silkscreen')
        changed.append(f.GetReference())
    return changed


# ----------------------------------------------------------------------------------------------------------------------
# placement rules
def supports(b):
    """The five M3 support centres; R10 has no servo-plug tie holes."""
    holes, _ = fit_check.board_geometry(b)
    ties = fit_check.retention_holes(b, holes, profile='r10')
    return [h for h in holes if all(math.dist(h, t) >= 0.02 for t in ties)]


def hardware(b, side):
    """(x, y, r) keep-outs of the support hardware on one face: the 3.5 mm bottom standoff and the 3.8 mm top washer
    radii (fit_check.STANDOFF_RADIUS / TOP_HARDWARE_RADIUS; R3-MFG-05)."""
    r = fit_check.STANDOFF_RADIUS if side == 'B' else fit_check.TOP_HARDWARE_RADIUS
    return [(x, y, r) for x, y in supports(b)]


def in_circle(r, c):
    """Box r (x0, y0, x1, y1) reaches into circle c (x, y, radius)."""
    dx = max(r[0] - c[0], 0.0, c[0] - r[2])
    dy = max(r[1] - c[1], 0.0, c[1] - r[3])
    return dx * dx + dy * dy < c[2] * c[2]


class Silk10(r8_post.RunOnSilk):
    """r8_post.RunOnSilk with R10's keep-outs: its 0.15 mm gaps are SILK_GAP (the ink boxes come from a polygon drawn
    0.005 mm inside the stroke: DRC's silk_overlap at min_silk_clearance 0.15 measured 0.149999 mm between two texts
    placed exactly 0.15 apart), each pad's solder-mask expansion is added to its gap (LS120's 0.05 mm and U4's 0.025 mm
    openings, R3-MFG-02: JLC measures silkscreen to the opening) and the support hardware circles (R3-MFG-05)."""

    def add(self, r, gap=None):
        if gap is None:
            self.texts.append(r)
        if gap is None or gap == silk.GAP:
            gap = SILK_GAP
        silk.Silk.add(self, r, gap)

    def __init__(self, b, side, strict_bodies=True):
        super().__init__(b, side, strict_bodies)
        mask = pcbnew.F_Mask if side == 'F' else pcbnew.B_Mask
        for f in b.GetFootprints():
            for p in f.Pads():
                e = silk.mm(p.GetSolderMaskExpansion(mask)) if p.IsOnLayer(mask) else 0.0
                if e > 0:
                    self.add(silk.bx(p), silk.GAP + e)
        self.hardware = hardware(b, side)

    def free(self, r):
        return super().free(r) and not any(in_circle(r, c) for c in self.hardware)


def connector_boxes(b):
    return {f.GetReference(): r7_post.subject_box(b, f.GetReference()) for f in b.GetFootprints()
            if CONNECTOR.match(f.GetReference())}


def subject_margin(r, ref, boxes):
    """(margin, own gap): how much nearer the centre of box r is to ref's courtyard box than to any other connector's."""
    c = ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2) * 2
    own = silk._gap(c, boxes[ref])
    return min(silk._gap(c, v) for k, v in boxes.items() if k != ref) - own, own


def put_subject(b, silks, text, ref, boxes, sides=('B', 'F'), angles=(90, 0), reach=LEGEND_REACH - REACH_MARGIN,
                step=0.1, margin=SUBJECT_MARGIN, prefer=None):
    """A legend about connector ref at the free spot nearest its courtyard box (ink gap, in 0.1 mm bands, then the
    distance between the two centres), within reach, on the first face in sides that has one, whose centre is nearer
    ref's courtyard than any other connector's by SUBJECT_MARGIN (R3-REQ-06: R8's notes were centred one terminal away
    from their subject). prefer '-x' ranks first the spots whose centre lies on the subject's -x side (the wire-entry
    side of J1, where the harness is handled), then those centred along the terminal column (|dy|, 0.1 mm bands).
    Returns (side, x, y, angle, gap, margin) or None."""
    box = boxes[ref]
    bc = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
    for side in sides:
        s = silks[side]
        t = silk._text(b, text, s.layer, 1.0)
        best = None
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
                    if g > reach:
                        continue
                    cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
                    key = ((int(cx > bc[0]), round(abs(cy - bc[1]), 1)) if prefer == '-x' else (0, 0)) + \
                        (round(g, 1), round(math.hypot(cx - bc[0], cy - bc[1]), 3))
                    if best is not None and key >= best[0]:
                        continue
                    m, _ = subject_margin(r, ref, boxes)
                    if m < margin or not s.free(r):
                        continue
                    best = (key, x, y, ang, r, m, g)
        if best is not None:
            _, x, y, ang, r, m, g = best
            t.SetTextAngleDegrees(ang)
            t.SetPosition(silk.P(x, y))
            b.Add(t)
            s.add(r)
            return side, round(x, 2), round(y, 2), ang, round(g, 2), round(m, 2)
    print(f'  no room for legend {text!r} within {reach} mm of {ref} with its subject nearest')
    return None


def find_pin(b, s, text, pads, own, near, region, angles=(0,), step=0.1):
    """r9_post.put_pin's search on one face and region without placing: the free spot nearest `near` whose text box
    keeps `own`'s pins nearest by r9_post.OWN_MARGIN; returns (gap, x, y, angle, ink box, margin) or None."""
    t = silk._text(b, text, s.layer, 1.0)
    best = None
    for ang in angles:
        t.SetTextAngleDegrees(ang)
        t.SetPosition(silk.P(0, 0))
        r0, b0 = silk.ink(t), r9_post.text_box(t)
        x0, y0, x1, y1 = region
        for i in range(int(round((x1 - x0) / step)) + 1):
            x = x0 + step * i
            for j in range(int(round((y1 - y0) / step)) + 1):
                y = y0 + step * j
                r = (r0[0] + x, r0[1] + y, r0[2] + x, r0[3] + y)
                g = silk._gap(r, (near[0], near[1], near[0], near[1]))
                if best is not None and g >= best[0]:
                    continue
                if not s.free(r):
                    continue
                m = r9_post.owner_margin((b0[0] + x, b0[1] + y, b0[2] + x, b0[3] + y), pads, own)
                if m < r9_post.OWN_MARGIN:
                    continue
                best = (g, x, y, ang, r, m)
    return best


def j122_top_key(b, silks, pads, boxes, clip):
    """J122's row labels on the top beside each row (the same end of the header for all three where the top has room,
    else each at the nearer free end), each with its own row's pins nearest (OWN_MARGIN); the harness note goes on the
    top first (NOTE_PLACE). Optional: returns the evidence; a label with no room is reported, not fatal."""
    s = silks['F']
    rows = {}
    for name, pins in J122_TOP_ROWS:
        xy = [silk.pad(b, 'J122', n) for n in pins]
        xs, y = [p[0] for p in xy], xy[0][1]
        own = {('J122', n) for n in pins}
        rows[name] = {end: find_pin(b, s, name, pads, own, near, clip(*win))
                      for end, near, win in (('west', (min(xs) - 1.5, y), (min(xs) - 6.0, y - 1.0, min(xs), y + 1.0)),
                                             ('east', (max(xs) + 1.5, y), (max(xs), y - 1.0, max(xs) + 6.0, y + 1.0)))}
    choice = None
    for end in ('west', 'east'):
        if all(rows[n][end] for n, _ in J122_TOP_ROWS):
            choice = {n: rows[n][end] for n, _ in J122_TOP_ROWS}
            break
    if choice is None:
        choice = {n: rows[n]['west'] or rows[n]['east'] for n, _ in J122_TOP_ROWS}
    out = {}
    for name, _ in J122_TOP_ROWS:
        got = choice[name]
        if got is None or not s.free(got[4]):          # (two labels never share a spot: rows are 2.54 mm apart)
            out[f'J122 top {name}'] = None
            print(f'  no room on the top for J122 row label {name!r}')
            continue
        g, x, y, ang, r, m = got
        t = silk._text(b, name, s.layer, 1.0)
        t.SetTextAngleDegrees(ang)
        t.SetPosition(silk.P(x, y))
        b.Add(t)
        s.add(r)
        out[f'J122 top {name}'] = ['F', round(x, 2), round(y, 2), ang, round(g, 2), round(m, 2)]
    return out


def pin1_parts(b, flipped):
    """(ref, pad-1 centre) of the parts on one face whose pad 1 means something: connectors, diodes and every part
    with three or more numbered pads (a two-pad resistor or capacitor has no pin 1 to read)."""
    out = []
    for f in b.GetFootprints():
        if f.IsFlipped() != flipped:
            continue
        ref = f.GetReference()
        numbers = {p.GetNumber() for p in f.Pads() if p.GetNumber()}
        if len(numbers) >= 3 or ref.startswith(('J', 'D')):
            p1 = [p for p in f.Pads() if p.GetNumber() == '1']
            if p1:
                out.append((ref, silk.mm(p1[0].GetPosition().x), silk.mm(p1[0].GetPosition().y)))
    return out


def own_margin(x, y, ref, parts):
    """How much nearer (x, y) is to ref's pad-1 centre than to any other part's pad 1 on the face."""
    own = min(math.hypot(x - px, y - py) for r, px, py in parts if r == ref)
    other = min((math.hypot(x - px, y - py) for r, px, py in parts if r != ref), default=1e9)
    return other - own


def pin1_dots(b, silks, refs, step=0.05):
    """r9_post.pin1_dots (a filled 0.4 mm dot outside the package body on the part's own face, at the free spot nearest
    pad 1 within DOT_REACH whose nearest pad of the part is pad 1) with one more condition (R3-DOC-10: U410's dot sat
    nearer U401's pad 1): the dot's centre is nearer its own pad 1 than any other part's pad 1 on the face by
    DOT_OWN_MARGIN. Returns {ref: (x, y, gap, margin)} and the parts with no such spot."""
    out, none = {}, []
    for ref in refs:
        f = silk.fp_of(b, ref)
        s = silks['B' if f.IsFlipped() else 'F']
        fab = pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab
        parts = pin1_parts(b, f.IsFlipped())
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
                m = own_margin(x, y, ref, parts)
                if m < DOT_OWN_MARGIN:
                    continue
                found = (x, y, gaps['1'], r, m)
                break
            if found:
                break
        if found is None:
            if ref in DOT_REQUIRED:
                raise RuntimeError(f'no room for a pin-1 dot at {ref} within {DOT_REACH} mm of its pad 1')
            none.append(ref)
            continue
        x, y, gap, r, m = found
        dot = pcbnew.PCB_SHAPE(b)
        dot.SetShape(pcbnew.SHAPE_T_CIRCLE)
        dot.SetLayer(s.layer)
        dot.SetStart(silk.P(x, y))
        dot.SetEnd(silk.P(x + 0.1, y))
        dot.SetWidth(silk.MM(0.2))
        dot.SetFilled(True)
        b.Add(dot)
        s.add(r)
        out[ref] = (round(x, 3), round(y, 3), round(gap, 3), round(m, 3))
    return out, none


# ----------------------------------------------------------------------------------------------------------------------
# contracts
def port_legends(b):
    """Every PORTS pin named exactly once over the legends starting with its connector's designator (R10's pin tables;
    check_r7.pin_legends holds R7's camera-side J9 table)."""
    seen = {}
    for d in b.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() in SILKS:
            m = re.match(r'^(J\d+)\s+(.+)', d.GetText())
            if m and m[1] in PORTS:
                for pin, name in re.findall(r'(\d+):([A-Z0-9]+)', m[2]):
                    seen.setdefault((m[1], int(pin)), set()).add(name)
    return [f'{ref}.{i}: silkscreen must identify {name}' for ref, (_, names) in PORTS.items()
            for i, name in enumerate(names, 1) if seen.get((ref, i)) != {name}]


def subjects(b, boxes):
    """Notes and port tables whose subject is not the nearest connector to their centre by SUBJECT_MARGIN."""
    texts = {note: ref for ref, note in NOTES}
    texts.update({t: ref for ref in SUBJECT_PORTS for t in port_rows(ref)})
    issues, ev = [], {}
    for d in b.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() in SILKS and d.GetText() in texts:
            m, own = subject_margin(silk.ink(d), texts[d.GetText()], boxes)
            ev[d.GetText()] = round(m, 2)
            if m < SUBJECT_MARGIN - 1e-6:
                issues.append(f'{d.GetText()!r}: nearer another connector than {texts[d.GetText()]} '
                              f'(margin {m:.2f} mm < {SUBJECT_MARGIN})')
    return issues, ev


def port_rows(ref):
    names = PORTS[ref][1]
    count = 1  # D-AVA-01: short SWD rows fit beside J2 instead of straddling USB/core.
    return [ref + ' ' + ' '.join(f'{i + 1}:{names[i]}' for i in range(k, min(k + count, len(names))))
            for k in range(0, len(names), count)]


def _polys(item, layer):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, layer, 0, silk.MM(0.002), pcbnew.ERROR_INSIDE)
    return ps


def _poly_gap(a, c):
    """Edge distance (mm) between two polygon sets, 0 when they overlap (vertex to outline both ways)."""
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
    return 1e9 if best is None else silk.mm(math.sqrt(best))


def silk_to_openings(b, limit=SILK_PAD):
    """Every silkscreen item (footprint graphics, visible designators, board items) against every solder-mask opening
    on its face, the pad's mask expansion included (JLC 'pad to silkscreen' 0.15 mm, R3-MFG-02; KiCad's silk_over_copper
    tests overlap only). Returns the items nearer than limit: (gap, owner, item, pad)."""
    masks = {pcbnew.F_SilkS: pcbnew.F_Mask, pcbnew.B_SilkS: pcbnew.B_Mask}
    openings = {lay: [] for lay in masks}
    for f in b.GetFootprints():
        for p in f.Pads():
            for lay, mask in masks.items():
                if p.IsOnLayer(mask):
                    ps = pcbnew.SHAPE_POLY_SET()
                    p.TransformShapeToPolygon(ps, mask, max(0, p.GetSolderMaskExpansion(mask)), silk.MM(0.002),
                                              pcbnew.ERROR_OUTSIDE)
                    openings[lay].append((f'{f.GetReference()}.{p.GetNumber()}', ps, ps.BBox()))
    items = [(f.GetReference(), g) for f in b.GetFootprints() for g in f.GraphicalItems() if g.GetLayer() in masks
             and (g.GetClass() == 'PCB_SHAPE' or (isinstance(g, pcbnew.PCB_TEXT) and g.IsVisible()))]
    items += [(f.GetReference(), f.Reference()) for f in b.GetFootprints()
              if f.Reference().IsVisible() and f.Reference().GetLayer() in masks]
    items += [('board', d) for d in b.GetDrawings() if d.GetLayer() in masks]
    reach = silk.MM(limit + 0.01)
    bad = []
    for who, g in items:
        ps = _polys(g, g.GetLayer())
        if not ps.OutlineCount():
            continue
        bb = ps.BBox()
        for pad, pp, pb in openings[g.GetLayer()]:
            if pb.GetLeft() - reach > bb.GetRight() or bb.GetLeft() - reach > pb.GetRight() or \
                    pb.GetTop() - reach > bb.GetBottom() or bb.GetTop() - reach > pb.GetBottom():
                continue
            gap = _poly_gap(ps, pp)
            if gap < limit - 1e-4:
                what = g.GetText() if isinstance(g, pcbnew.PCB_TEXT) else g.ShowShape()
                bad.append((round(gap, 3), who, what, pad))
    return bad


def pin1_marks(b):
    """Every pin-1 mark (the footprints' small silkscreen circles and the board-level dots) against the pad-1 centres
    on its face: [(owner, x, y, margin, nearest other)] where the owner's pad 1 is not nearer by DOT_OWN_MARGIN. A
    board-level dot's owner is the part whose pad 1 is nearest."""
    bad, ev = [], []
    marks = [(f.GetReference(), g) for f in b.GetFootprints() for g in f.GraphicalItems()
             if g.GetLayer() in SILKS and g.GetClass() == 'PCB_SHAPE' and g.GetShape() == pcbnew.SHAPE_T_CIRCLE
             and silk.mm(g.GetRadius()) <= MARK_R]
    marks += [(None, d) for d in b.GetDrawings()
              if d.GetLayer() in SILKS and d.GetClass() == 'PCB_SHAPE' and d.GetShape() == pcbnew.SHAPE_T_CIRCLE]
    for owner, g in marks:
        parts = pin1_parts(b, g.GetLayer() == pcbnew.B_SilkS)
        x, y = silk.mm(g.GetCenter().x), silk.mm(g.GetCenter().y)
        if owner is None:
            owner = min(parts, key=lambda q: math.hypot(x - q[1], y - q[2]))[0]
        if not any(r == owner for r, _, _ in parts):
            continue                                   # (a mark of a part with no pin 1 to read)
        m = own_margin(x, y, owner, parts)
        ev.append((owner, round(x, 3), round(y, 3), round(m, 2)))
        if m < DOT_OWN_MARGIN - 1e-6:
            bad.append((owner, round(x, 3), round(y, 3), round(m, 2)))
    return bad, ev


def in_hardware(b):
    """Board-level silkscreen and visible designators reaching into a support hardware circle on their face."""
    keep = {pcbnew.F_SilkS: hardware(b, 'F'), pcbnew.B_SilkS: hardware(b, 'B')}
    items = [(d.GetText() if isinstance(d, pcbnew.PCB_TEXT) else 'dot', d) for d in b.GetDrawings()
             if d.GetLayer() in SILKS]
    items += [(f.GetReference(), f.Reference()) for f in b.GetFootprints()
              if f.Reference().IsVisible() and f.Reference().GetLayer() in SILKS]
    return [name for name, d in items
            if any(in_circle(silk.ink(d) if isinstance(d, pcbnew.PCB_TEXT) else silk.bx(d), c)
                   for c in keep[d.GetLayer()])]


def fab_reference_details(b):
    """R12-MFG-01: clear five Fab outlines/dots; small assembly text requires detail zoom."""
    for ref, dx, dy in (('R10', 0, 0.1), ('C29', -0.05, 0), ('C92', 0, 0), ('R8', 0, 0), ('C5', 0, 0)):
        f = silk.fp_of(b, ref)
        text = silk._fab_ref(f)
        text.SetTextSize(silk.P(0.4, 0.4))
        text.SetTextThickness(silk.MM(0.06))
        text.SetPosition(f.GetPosition() + silk.P(dx, dy))


# R13-MFG-01: measured per-reference Fab ink clearances. Keep all other labels unchanged.
# D-R20-07 (R20-MFG-03): C123, C445, D440, D441, R119 and R173 measured clear of their own Fab outlines and marks
# (C445 as C411; D440 / D441 beside their bodies as D410 / D411; R119's 1.0 mm text read "R1119").
# This table is derived offline; the production stage performs no placement search here.
FAB_REFERENCE_CLEARANCES_R13 = {
    'C10': (0.0, 0.1, 1.0),
    'C100': (-0.05, 0.0, 0.4),
    'C123': (0.0, -0.1, 0.4),
    'C13': (-0.05, 0.0, 0.4),
    'C14': (0.0, -0.05, 0.4),
    'C15': (0.1, 0.0, 0.4),
    'C16': (0.0, -0.05, 0.4),
    'C17': (-0.05, 0.0, 0.4),
    'C18': (0.0, -0.05, 0.4),
    'C21': (0.0, 0.1, 0.4),
    'C24': (0.1, -0.1, 0.4),
    'C25': (0.0, -0.05, 0.4),
    'C26': (0.0, 0.1, 0.4),
    'C30': (-0.05, 0.0, 0.4),
    'C31': (-0.05, 0.0, 0.4),
    'C32': (0.1, 0.0, 0.4),
    'C407': (0.0, 0.0, 0.6),
    'C408': (0.0, -0.05, 0.4),
    'C411': (0.0, 0.0, 0.7),
    'C445': (0.0, 0.0, 0.7),
    'C461': (0.0, 0.0, 0.7),
    'C88': (0.1, 0.0, 0.4),
    'C99': (0.0, 0.1, 0.4),
    'D400': (0.15, 1.1, 0.8),
    'D401': (0.0, 1.1, 0.8),
    'D410': (0.05, -1.0, 0.8),
    'D411': (0.0, -1.0, 0.8),
    'D420': (0.0, 1.1, 0.8),
    'D421': (0.15, 1.1, 0.8),
    'D440': (0.0, -1.0, 0.8),
    'D441': (0.0, -1.0, 0.8),
    'LED1': (-1.45, 0.0, 0.6),
    'LED2': (-1.45, 0.0, 0.6),
    'LS120': (0.0, 1.2, 0.8),
    'Q120': (0.0, 0.0, 0.7),
    'Q121': (0.0, 0.0, 0.7),
    'R104': (0.0, 0.15, 0.4),
    'R105': (0.0, -0.05, 0.4),
    'R11': (0.1, 0.0, 0.4),
    'R119': (0.0, 0.1, 0.4),
    'R12': (0.1, 0.0, 0.4),
    'R120': (-0.05, 0.0, 0.4),
    'R121': (-0.05, 0.0, 0.4),
    'R122': (0.1, 0.0, 0.4),
    'R123': (0.1, 0.0, 0.4),
    'R127': (0.0, -0.05, 0.4),
    'R128': (0.1, 0.0, 0.4),
    'R129': (0.1, 0.0, 0.4),
    'R13': (-0.05, 0.0, 0.4),
    'R130': (0.0, 0.1, 0.4),
    'R131': (0.0, 0.1, 0.4),
    'R132': (0.1, 0.0, 0.4),
    'R133': (0.0, 0.1, 0.4),
    'R154': (-0.05, 0.0, 0.4),
    'R155': (-0.05, 0.0, 0.4),
    'R156': (0.1, 0.0, 0.4),
    'R157': (0.1, 0.0, 0.4),
    'R163': (-0.05, 0.0, 0.4),
    'R173': (-0.1, 0.0, 0.4),
    'R175': (0.1, 0.0, 0.4),
    'R178': (0.0, 0.1, 0.4),
    'R180': (0.0, 0.1, 0.4),
    'R432': (0.0, 0.15, 0.4),
    'R60': (0.0, 0.1, 0.4),
    'R61': (0.0, -0.05, 0.4),
    'R64': (-0.05, 0.0, 0.4),
    'TP120': (0.0, -1.15, 0.6),
    'TP122': (0.0, -1.15, 0.6),
    'TP74': (0.0, -1.15, 0.6),
    'TP80': (0.0, -1.15, 0.6),
    'TP81': (0.0, -1.15, 0.6),
    'TP82': (0.0, -1.15, 0.6),
    'TP83': (0.0, -1.15, 0.6),
    'TP88': (0.0, -1.15, 0.6),
    'U10': (0.0, 0.0, 0.5),
    'U11': (0.0, 0.0, 0.7),
    'U12': (0.0, 0.0, 0.7),
    'U13': (0.0, 0.0, 0.5),
    'U400': (0.0, 0.0, 0.4),
}


def fab_reference_clearances(b):
    """Clear the reviewed Fab borders/polarity marks; small labels require vector zoom."""
    for ref, (dx, dy, size) in FAB_REFERENCE_CLEARANCES_R13.items():
        f = silk.fp_of(b, ref)
        text = silk._fab_ref(f)
        text.SetTextSize(silk.P(size, size))
        text.SetTextThickness(silk.MM(round(size * 0.15, 6)))
        text.SetPosition(f.GetPosition() + silk.P(dx, dy))


# ----------------------------------------------------------------------------------------------------------------------
def finish(b, lib):
    """Place every legend, the designators and the Fab references; return the placement evidence."""
    silk.W, silk.L = r9_post.outline(b)
    for d in list(b.GetDrawings()):
        if d.GetLayer() in SILKS:
            b.Delete(d)
    for f in b.GetFootprints():
        for field in f.GetFields():
            field.SetVisible(False)
    for ref, w in r7_post.SILK_W.items():           # silkscreen strokes at the library width (lib_footprint_mismatch)
        f = b.FindFootprintByReference(ref)
        for g in (f.GraphicalItems() if f else ()):
            if g.GetLayer() in SILKS and g.GetClass() == 'PCB_SHAPE':
                g.SetWidth(silk.MM(w))
    synced = sync_silk(b, lib)
    silks = {side: Silk10(b, side) for side in ('F', 'B')}
    pads = r9_post.connector_pads(b)
    boxes = connector_boxes(b)
    placed, missing = {}, []

    def clip(x0, y0, x1, y1):
        return (max(EDGE_MM, x0), max(EDGE_MM, y0), min(silk.W - EDGE_MM, x1), min(silk.L - EDGE_MM, y1))

    def put_near(text, ref, sides=('B', 'F')):
        result = r7_post.label_near(b, silks, text, ref, reach=LEGEND_REACH - REACH_MARGIN, sides=sides)
        if result is None:
            result = r7_post.label_near(b, silks, text, ref, reach=12.0, sides=sides)
        placed[text] = None if result is None else list(result)
        if result is None:
            missing.append(f'{text} (within {LEGEND_REACH} mm of {ref})')
        return result

    def put_spot(text, ref, side, x, y, angle):
        """D-R19-06: a word legend at its reviewed spot; it must be free and within LEGEND_REACH of its connector."""
        t = silk._text(b, text, silks[side].layer, 1.0)
        t.SetTextAngleDegrees(angle)
        t.SetPosition(silk.P(x, y))
        box = silk.ink(t)
        gap = silk._gap(box, r7_post.subject_box(b, ref))
        if not silks[side].free(box) or gap > LEGEND_REACH - REACH_MARGIN:
            raise RuntimeError(f'{text}: reviewed word spot is obstructed or no longer beside {ref}')
        b.Add(t)
        silks[side].add(box)
        placed[text] = [side, x, y, angle, round(gap, 2)]
        return placed[text]

    def put_about(text, ref, sides=('B', 'F'), prefer=None):
        result = put_subject(b, silks, text, ref, boxes, sides=sides, prefer=prefer)
        if result is None:
            result = put_subject(b, silks, text, ref, boxes, sides=sides, prefer=prefer, reach=12.0)
        placed[text] = None if result is None else list(result)
        if result is None:
            missing.append(f'{text} (within {LEGEND_REACH} mm of {ref}, nearest it by {SUBJECT_MARGIN} mm)')
        return result

    # 1. Connector names and the sole SWD table; every wired connector has individual pin legends.
    # Reserve the SWD pin table before short subject words; longest rows constrain placement most.
    fallback = []
    for ref in PORTS:
        for text in sorted(port_rows(ref), key=lambda text: (-len(text), text)):
            if ref in SUBJECT_PORTS:
                put_about(text, ref)
                continue
            side, x, y, angle = SWD_LEGENDS[text]
            t = silk._text(b, text, silks[side].layer, 1.0)
            t.SetTextAngleDegrees(angle)
            t.SetPosition(silk.P(x, y))
            box = silk.ink(t)
            margin, gap = subject_margin(box, ref, boxes)
            if not silks[side].free(box) or margin < 0 or gap > LEGEND_REACH:
                raise RuntimeError(f'{text}: reserved SWD legend is obstructed or no longer beside J2')
            b.Add(t)
            silks[side].add(box)
            placed[text] = [side, x, y, angle, round(gap, 3), round(margin, 3)]
    for ref, word in WORDS:
        if word in WORD_SPOTS:
            put_spot(word, ref, *WORD_SPOTS[word])
        else:
            put_near(word, ref, sides=('F', 'B'))
    for ref, note in NOTES:
        sides, prefer = NOTE_PLACE.get(note, NOTE_PLACE.get(ref, (('B', 'F'), None)))
        put_about(note, ref, sides=sides, prefer=prefer)
    # 2. terminal pin legends by pin
    for ref, mapping in TERMINAL_PINS:
        for number, name in mapping:
            x, y = silk.pad(b, ref, number)
            regions = [(clip(x - PIN_REACH, y - PIN_REACH, x + PIN_REACH, y + PIN_REACH), ('F', 'B'), (90, 0))]
            if (ref, number) in PIN_SPOTS:          # D-R19-08: the one reviewed spot, the same OWN_MARGIN test
                side, sx, sy, angle = PIN_SPOTS[(ref, number)]
                regions = [((sx, sy, sx, sy), (side,), (angle,))]
            result = r9_post.put_pin(b, silks, f'{number}:{name}', pads, {(ref, number)}, (x, y), regions)
            key = f'{ref} {number}:{name}'
            placed[key] = None if result is None else list(result)
            if result is None:
                missing.append(key)
    # 3. revision legend and JLC's order-number placeholder
    whole = (EDGE_MM, EDGE_MM, silk.W - EDGE_MM, silk.L - EDGE_MM)
    for text, near in ((REV, (silk.W / 2, silk.L - 6.0)), (ORDER_MARK, (silk.W / 2, silk.L / 2))):
        result = silk.label(b, silks, text, near, whole, (0, 90), ('B', 'F'), size=1.0)
        placed[text] = None if result is None else list(result)
        if result is None:
            missing.append(text)
    if missing:
        raise RuntimeError('Essential R10 silkscreen did not fit: ' + ', '.join(missing))
    # 4. J122's top-side key (optional)
    top_key = j122_top_key(b, silks, pads, boxes, clip)
    placed.update(top_key)
    # 5. pin-1 dots, designators, the courtyard and run-on tests
    dots, no_dot = pin1_dots(b, silks, [r for r in DOT_PARTS if b.FindFootprintByReference(r) is not None])
    for ref, (side, x, y, angle) in FIXED_REFS.items():
        f = b.FindFootprintByReference(ref)
        t = f.Reference()
        t.SetLayer(silks[side].layer)
        t.SetMirrored(side == 'B')
        t.SetTextSize(pcbnew.VECTOR2I(silk.MM(1.0), silk.MM(1.0)))
        t.SetTextThickness(silk.MM(0.15))
        t.SetTextAngleDegrees(angle)
        t.SetPosition(silk.P(x, y))
        t.SetVisible(True)
        if not silks[side].free(silk.ink(t)) or r8_post.courtyard_fails(b, f):
            raise RuntimeError(f'{ref}: fixed designator spot no longer clear or nearest its own courtyard')
        silks[side].add(silk.ink(t))
    silk.designators(b, silks, priority=check_r10.SHOWN_REFS, fixed=FIXED_REFS)
    moved = {}
    with check_r10.patched(r8_post, RunOnSilk=Silk10):     # place_designator's own obstacle map keeps R10's keep-outs
        for _ in range(4):
            bad = {ref: ('courtyard',) + why for ref, why in r7_post.courtyard_offenders(b).items()}
            bad.update({ref: ('run-on',) for ref in r8_post.run_on_offenders(b) if ref not in bad})
            if not bad:
                break
            for ref in sorted(bad, key=lambda r: (r not in check_r10.SHOWN_REFS, r)):
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
    # Keep the assembly reference clear of the five terminal drills.
    silk._fab_ref(silk.fp_of(b, 'J122')).SetPosition(silk.P(36.5, 71.5))
    fab_reference_details(b)
    fab_moved = r9_post.fab_clear(b)
    fab_reference_clearances(b)
    b.GetTitleBlock().SetRevision(REV)
    distance_review = []
    with check_r10.patched(check_r7, WORD_LEGENDS=check_r10.WORD_LEGENDS_R10), \
            check_r10.patched(check_r8, TERMINAL_PINS=TERMINAL_PINS):
        issues = (check_r7.duplicate_ids(b) + port_legends(b) + check_r7.legend_subjects(b, distance_review=distance_review) + check_r10.hidden_refs(b)[0] +
                  check_r8.terminal_legends(b)[0] + check_r10.word_legends(b)[0])
    found, margins = subjects(b, boxes)
    issues += found
    near_pads = silk_to_openings(b)
    issues += [f'silkscreen {what!r} of {who} {gap} mm from {pad} opening (< {SILK_PAD})' for gap, who, what, pad in near_pads]
    marks_bad, marks = pin1_marks(b)
    issues += [f'pin-1 mark of {o} at ({x}, {y}) only {m} mm nearer its pad 1 (< {DOT_OWN_MARGIN})' for o, x, y, m in marks_bad]
    issues += [f'{name!r} inside a support hardware circle' for name in in_hardware(b)]
    if issues:
        raise RuntimeError('legend contract: ' + '; '.join(issues))
    hidden = sorted(silk.HIDDEN, key=lambda r: (r.rstrip('0123456789'), int(r[len(r.rstrip('0123456789')):] or 0)))
    visible = sum(1 for f in b.GetFootprints() if f.Reference().IsVisible())
    bottom_of_top = sorted(f.GetReference() for f in b.GetFootprints() if f.Reference().IsVisible() and
                           not f.IsFlipped() and f.Reference().GetLayer() == pcbnew.B_SilkS)
    for ref, (why, got) in sorted(moved.items()):
        print(f'  {why[0]}: {ref} -> '
              f'{"hidden" if got is None else f"{got[0]}.SilkS at ({got[1][0]:.2f}, {got[1][1]:.2f})"}')
    print(f'footprint silkscreen from the library: {" ".join(synced) or "none"}')
    print(f'R10 silkscreen: {len(placed)} legends; {visible} designators shown ({len(bottom_of_top)} top parts\' on the '
          f'bottom under their part); {len(hidden)} hidden, kept on Fab: {" ".join(hidden)}')
    print(f'pin-1 dots: {" ".join(sorted(dots))}; no room (Fab mark only): {" ".join(no_dot) or "none"}')
    print(f'port rows beside their part but not nearer it than every other connector: {", ".join(fallback) or "none"}')
    print(f'J122 top key: {", ".join(k for k, v in top_key.items() if v) or "none"}; '
          f'no room: {", ".join(k for k, v in top_key.items() if not v) or "none"}')
    return {'revision': REV, 'outline_mm': [silk.W, silk.L], 'footprint_silk_from_library': synced, 'legends': placed,
            'subject_margins_mm': margins, 'port_rows_not_nearest': fallback, 'legend_distance_review': distance_review,
            'port_tables_no_room': {ref: list(names) for ref, names in NO_ROOM_PORTS.items()}, 'pin1_dots': dots, 'no_pin1_dot': no_dot, 'pin1_marks': marks,
            'fab_moved': fab_moved, 'designators_shown': visible, 'fixed_designators': FIXED_REFS,
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
    if any(isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() in SILKS for d in b.GetDrawings()):
        raise SystemExit('r10_post runs once, on the ground-stage board: this board already carries silkscreen text')
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())          # the zone fill (the routing families leave zones unfilled)
    before = r8_post.fixed_digest(b)
    evidence = finish(b, board.parent / 'kilib' / 'rocket.pretty')
    assert r8_post.fixed_digest(b) == before, 'r10_post changed copper, a zone, a pad or a footprint position'
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())          # the final fill, after the silkscreen: it must reproduce the first
    assert r8_post.fixed_digest(b) == before, 'the final zone fill differs from the first'
    assert pcbnew.SaveBoard(str(board), b, True), 'save failed'
    b = pcbnew.LoadBoard(str(board))
    assert r8_post.fixed_digest(b) == before, 'the saved board differs in copper, zones, pads or footprint positions'
    print(f'r10_post: saved {board.name}; copper, zones, pads and footprint positions unchanged; zones refilled')
    if args.report:
        args.report.write_text(json.dumps(evidence, indent=1) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
