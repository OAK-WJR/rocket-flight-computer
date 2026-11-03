#!/usr/bin/env python3
"""R8 placement legaliser (build step 4): the placement rules every part must meet before any copper is drawn.

Imported by r8_pcb.py (strict: the frozen table must be legal) and r8_place_check.py; KiCad Python. Board mm, y = 0
at the aft edge, +y forward. A part violates the placement when any of these fails (R8_DECISIONS D29-D31):

  courtyard  courtyards on the same side keep >= COURTYARD_GAP apart; every courtyard lies inside the outline (J3
             overhangs by design); no hole inside a courtyard (KiCad npth/pth_inside_courtyard)
  copper     every pad keeps its clearance from every foreign pad and rigid track or via on a shared copper layer:
             the netclass 0.15 mm, the pads' own local clearances (bare test pads 1.0 mm, the RAW_ACT pins 0.3 mm),
             J2's 0.508 mm (m3.kicad_dru), pyro rules A-G and A2 and, between pads, rule H (1.0 mm live to sense and
             gate pads), each the larger where several apply; pads >= 0.5 mm from the board edge and the Edge.Cuts
             holes, >= 0.25 mm from every other hole
  bottom     R5 L10: bottom courtyards >= 1.5 mm from foreign through-hole pads, >= 3.5 mm from an M3 centre, >= 1.0 mm
             from a pyro via, >= 2.0 mm from TP122's pad, and >= 2.0 mm from the J122 tie path's centre line (4 mm
             under-board channel between the tie holes)
  top        top courtyards (bare pads: the pad) >= 3.8 mm from an M3 centre (7 mm washer + 0.3 mm, fit_check)
  keepclear  no pad or hole closer than its clearance rule to the reserved routing copper of r8_keepclear.tsv (the
             copper the spikes proved, and the step-4 lanes), so steps 5-7 can draw it as proved
  rf         F10 / D17: RF parts' courtyards >= 5.0 mm from the restricted parts' courtyards and from fast-net pads;
             no pad of a net the strip does not allow (check_r7 STRIP_F, check_r8 STRIP_B) at y < 23.5
"""
import csv
import math
import re
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import check_r7 as r7  # noqa: E402
import check_r8  # noqa: E402

MM, mm = pcbnew.FromMM, pcbnew.ToMM
KEEPCLEAR = ROOT / 'm3_design/r8_keepclear.tsv'
W, L = 46.0, 118.0
COURTYARD_GAP = 0.02            # mm between courtyard outlines (their 0.05 mm lines must not touch)
NETCLASS = 0.15                 # mm, m3.kicad_pro Default
EDGE = 0.5                      # mm, m3.kicad_pro min_copper_edge_clearance
SMA_EDGE = 0.2                  # mm, m3.kicad_dru "R7 SMA pads to the aft edge"
HOLE = 0.25                     # mm, m3.kicad_dru "General copper to hole clearance"
J2_FOREIGN = 0.508              # mm, m3.kicad_dru Tag-Connect rule
BOT_THT, BOT_M3, BOT_PYRO_VIA, BOT_TP122, TIE_HALF = 1.5, 3.5, 1.0, 2.0, 2.0
TOP_M3 = 3.8
RF_SEP = 5.0
TIE = ((21.5, 68.6), (27.0, 82.6))                      # fit_check.RETENTION_HOLES
EDGE_PARTS = {'J3', 'J9'}                                  # courtyards may cross the outline: J3 overhangs 0.45 mm (HRO), J9's
                                                          # courtyard reaches x 46.05 at R7's x (mated margin 0.03 mm), as in R7
BARE = re.compile(r'^(TP\d+|J2)$')                        # exposed pads, no body: top washer measured to the pad
PYRO_BLOCK = (4.0, 84.0, 42.0, 114.4)
LIVE = {'PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT'}
GATES = {'PYRO1_GATE', 'PYRO1_GATE_N'}
SENSE = {'ARM1_SENSE', 'PYRO1_CONT', 'PYRO1_COLD', 'PYRO1_CONT_MID', 'ARM1_SENSE_MID'}
H_LIVE = LIVE | {'RAW_ACT'}
H_SENSE_GATE = {'ARM1_SENSE', 'PYRO1_CONT', 'RAW_ACT_SENSE', 'PYRO1_GATE', 'PYRO1_GATE_N', 'ACT_GATE', 'ACT_DRV'}
H_MID = {'PYRO1_CONT_MID', 'ARM1_SENSE_MID', 'RAW_ACT_SENSE_MID'}
H_GATE = {'PYRO1_GATE', 'PYRO1_GATE_N', 'ACT_GATE', 'ACT_DRV'}
H_OWN = {'Q124', 'Q120', 'Q121', 'Q122'}
RF_NETS50 = {'GNSS_RF_ANT', 'GNSS_RF_IN', 'RADIO_RF_ANT', 'RADIO_RF'}


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def _sym(a, b, sa, sb):
    return (a in sa and b in sb) or (b in sa and a in sb)


def rule_clearance(na, nb, ra, rb, pads, at_block):
    """Required copper clearance (mm) between items of nets na / nb owned by footprints ra / rb (None: board copper),
    from m3.kicad_dru; pads = both items are pads; at_block = a gate item lies in the PYRO_BLOCK area (rule G)."""
    if na == nb and na:
        return 0.0
    same = ra is not None and ra == rb
    req = NETCLASS
    if _sym(na, nb, RF_NETS50, {'GND'}):
        req = max(req, 0.25)
    for a, b, x, y in ((na, nb, ra, rb), (nb, na, rb, ra)):
        if a == 'RAW_ACT' and b in GATES | SENSE:                                        # A
            req = max(req, 0.5)
        if a in LIVE and b in GATES and not (same and x == 'Q124'):                       # B
            req = max(req, 0.5)
        if a in LIVE and b in SENSE and not (same and x in ('R173', 'R131', 'R132')):     # C
            req = max(req, 0.3)
        if a == 'GND' and b in LIVE and not (same and x in ('Q124', 'C128')):             # D
            req = max(req, 0.5)
        if a == 'RAW_ACT' and b in ('PYRO1_BUS', 'PYRO1_IGN'):                            # E
            req = max(req, 1.0)
        if a in LIVE and b and b != 'GND' and b not in SENSE | GATES | LIVE and \
                not (a in ('PYRO1_BUS', 'PYRO1_IGN') and b == 'RAW_ACT') and not (same and x == 'Q124'):  # F
            req = max(req, 0.5)
        if a in GATES and at_block and b and b not in {'GND', 'RAW_ACT'} | LIVE | GATES and \
                not (same and x == 'Q124'):                                                # G
            req = max(req, 0.3)
        if a == 'RAW_ACT' and b == 'RAW_ACT_SENSE':                                        # A2
            req = max(req, 0.3)
        if pads and not (same and x in H_OWN) and \
                ((a in H_LIVE and b in H_SENSE_GATE) or (a in H_MID and b in H_GATE)):    # H
            req = max(req, 1.0)
    return req


def read_keepclear(path=KEEPCLEAR):
    """[(family, net, layers, shape, box)] from r8_keepclear.tsv: track segments (w = width) and vias (a point, w =
    diameter; on every copper layer)."""
    out = []
    if not Path(path).is_file():
        return out
    lay = {'F': (pcbnew.F_Cu,), 'B': (pcbnew.B_Cu,), 'FB': (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)}
    with open(path) as fh:
        for r in csv.DictReader((line for line in fh if not line.startswith('#')), delimiter='\t'):
            x0, y0, x1, y1, w = (float(r[k]) for k in ('x0', 'y0', 'x1', 'y1', 'w'))
            if (x0, y0) == (x1, y1):
                shape = pcbnew.SHAPE_CIRCLE(V(x0, y0), MM(w / 2))
            else:
                shape = pcbnew.SHAPE_SEGMENT(V(x0, y0), V(x1, y1), MM(w))
            box = (min(x0, x1) - w / 2, min(y0, y1) - w / 2, max(x0, x1) + w / 2, max(y0, y1) + w / 2)
            out.append((r['family'], r['net'], lay[r['layer']], shape, box))
    return out


GRID = 2.0


def _cells(b, grow=0.0):
    for i in range(int(math.floor((b[0] - grow) / GRID)), int(math.floor((b[2] + grow) / GRID)) + 1):
        for j in range(int(math.floor((b[1] - grow) / GRID)), int(math.floor((b[3] + grow) / GRID)) + 1):
            yield i, j


def _rect(x0, y0, x1, y1):
    s = pcbnew.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        s.Append(MM(x), MM(y))
    return s


def _box(s):
    bb = s.BBox()
    return mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())


def _near(a, b, d):
    return not (a[2] + d < b[0] or b[2] + d < a[0] or a[3] + d < b[1] or b[3] + d < a[1])


def _gap(a, b, limit):
    """True when shapes a and b are closer than limit mm (edge to edge)."""
    return pcbnew.SHAPE.Collide(a, b, max(MM(limit) - 1, 0))


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    t = max(0.0, min(1.0, ((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)))
    return math.dist(p, (ax + t * (bx - ax), ay + t * (by - ay)))


class Model:
    """Geometry of the board for the placement rules; parts are re-read from their footprints on demand."""

    def __init__(self, board, movable, keepclear=None, copper=None):
        """copper: the board items the rules treat as the fixed copper (default: every track and via, the placed
        board's rigid R7 copper; a test on a later-step board passes r8_power_check.rigid_items for the same set)."""
        self.b = board
        self.fps = {f.GetReference(): f for f in board.GetFootprints()}
        self.movable = set(movable)
        self.keepclear = read_keepclear() if keepclear is None else keepclear
        self.kc_grid = {}
        for k, item in enumerate(self.keepclear):
            for c in _cells(item[4]):
                self.kc_grid.setdefault(c, []).append(k)
        self.cu = list(board.GetEnabledLayers().CuStack())
        holes = self.edge_holes_of(board)
        self.edge_holes = holes
        self.m3 = [c for c, r in holes if abs(r - 1.6) < 0.01 and all(math.dist(c, t) > 0.02 for t in TIE)]
        self.rigid_items = []                       # (net, layer, shape, box) of the rigid tracks and vias
        self.pyro_vias = []
        for t in (board.GetTracks() if copper is None else copper):
            for lay in self.cu:
                if t.IsOnLayer(lay):
                    s = check_r8.item_shape(t, lay)
                    self.rigid_items.append((t.GetNetname(), lay, s, _box(s), mm(t.GetPosition().x),
                                             mm(t.GetPosition().y)))
            if t.GetClass() == 'PCB_VIA' and re.match(r'^(PYRO|ARM1)', t.GetNetname()):
                self.pyro_vias.append((mm(t.GetPosition().x), mm(t.GetPosition().y), mm(t.GetWidth(pcbnew.F_Cu)) / 2))
        self.restricted = {r for r, f in self.fps.items() if any(p.GetNetname() in check_r8.SWITCH_NETS
                                                                  for p in f.Pads())}
        self.restricted |= {r for r in check_r8.BUCK_PARTS + check_r8.NOISY_PARTS if r in self.fps}
        self.rf = {r for r in self.fps if r7.RF_PART.fullmatch(r)}
        self.cache = {}

    @staticmethod
    def edge_holes_of(board):
        """[((x, y), r)] of the Edge.Cuts circles (M3 supports and the J122 tie holes)."""
        holes = []
        for d in board.GetDrawings():
            if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
                c = d.GetCenter()
                holes.append(((mm(c.x), mm(c.y)), mm(d.GetRadius())))
        return holes

    # --- per-part geometry ---------------------------------------------------------------------------------------
    def part(self, ref):
        f = self.fps[ref]
        key = (f.GetPosition().x, f.GetPosition().y, f.GetOrientationDegrees(), f.IsFlipped())
        hit = self.cache.get(ref)
        if hit and hit[0] == key:
            return hit[1]
        side = 'B' if f.IsFlipped() else 'F'
        cy = check_r8.courtyard(f)
        pads = []
        for p in f.Pads():
            for lay in self.cu:
                if p.IsOnLayer(lay) and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                    s = check_r8.item_shape(p, lay)
                    lc = p.GetLocalClearance()
                    pads.append((p.GetNetname(), lay, s, _box(s), mm(lc) if lc is not None else 0.0, p))
        holes = []
        for p in f.Pads():
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                pp = p.GetPosition()
                holes.append((mm(pp.x), mm(pp.y), mm(p.GetDrillSize().x) / 2, mm(max(p.GetSize().x, p.GetSize().y)) / 2,
                              p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH))
        info = dict(side=side, cy=cy, box=_box(cy), pads=pads, holes=holes,
                    fast=[x for x in pads if check_r8.FAST_NETS.match(x[0] or '')])
        self.cache[ref] = (key, info)
        return info

    # --- rules ----------------------------------------------------------------------------------------------------
    def violations(self, ref, first=False):
        out = []

        def bad(msg):
            out.append(msg)
            return first
        me = self.part(ref)
        side, cy, box = me['side'], me['cy'], me['box']
        if ref not in EDGE_PARTS and (box[0] < 0 or box[1] < 0 or box[2] > W or box[3] > L):
            if bad('courtyard outside the outline'):
                return out
        # F10 strip content (check_r7 STRIP_F, check_r8 STRIP_B): no other net's pad in y < STRIP_Y on that layer
        for net, lay, s, pb, lc, p in me['pads']:
            if pb[1] < r7.STRIP_Y and lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                allowed = r7.STRIP_F if lay == pcbnew.F_Cu else check_r8.STRIP_B
                if not allowed.match(net or '') and bad(f'pad {p.GetNumber()} ({net}) in the RF strip (y < {r7.STRIP_Y})'):
                    return out
        # outline and Edge.Cuts holes for pads
        for net, lay, s, pb, lc, p in me['pads']:
            edge = SMA_EDGE if ref in ('J30', 'J31') else EDGE
            if ref not in EDGE_PARTS and (pb[0] < edge or pb[1] < edge or pb[2] > W - edge or pb[3] > L - edge):
                if bad(f'pad {p.GetNumber()} within {edge} mm of the board edge'):
                    return out
            for (c, r) in self.edge_holes:
                if math.dist(((pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2), c) < r + EDGE + 3:
                    if _gap(s, pcbnew.SHAPE_CIRCLE(V(*c), MM(r)), EDGE) and bad(f'pad {p.GetNumber()} near hole {c}'):
                        return out
        for (c, r) in self.edge_holes:
            if _near(box, (c[0] - r, c[1] - r, c[0] + r, c[1] + r), 0) and \
                    _gap(cy, pcbnew.SHAPE_CIRCLE(V(*c), MM(r)), 0.0001) and bad(f'courtyard over hole {c}'):
                return out
        # other parts
        for other in self.fps:
            if other == ref:
                continue
            o = self.part(other)
            if not _near(box, o['box'], 6.0):
                continue
            if o['side'] == side and _near(box, o['box'], COURTYARD_GAP) and _gap(cy, o['cy'], COURTYARD_GAP):
                if bad(f'courtyard overlaps {other}'):
                    return out
            for hx, hy, hr, ring, pth in o['holes']:
                if _near(box, (hx - hr, hy - hr, hx + hr, hy + hr), 0) and \
                        cy.Collide(pcbnew.SHAPE_CIRCLE(V(hx, hy), MM(hr)), 0) and bad(f'hole of {other} in courtyard'):
                    return out
                if side == 'B' and pth and _near(box, (hx - ring, hy - ring, hx + ring, hy + ring), BOT_THT) and \
                        _gap(cy, pcbnew.SHAPE_CIRCLE(V(hx, hy), MM(ring)), BOT_THT) and \
                        bad(f'bottom courtyard within {BOT_THT} mm of a through-hole pad of {other}'):
                    return out
            for net, lay, s, pb, lc, p in me['pads']:
                for onet, olay, os_, ob, olc, op in o['pads']:
                    if olay != lay or (net and net == onet) or not _near(pb, ob, 1.2):
                        continue
                    req = max(rule_clearance(net, onet, ref, other, True,
                                             self._block(pb, net) or self._block(ob, onet)), lc, olc)
                    if 'J2' in (ref, other) and ref != other:
                        req = max(req, J2_FOREIGN)
                    if _gap(s, os_, req) and bad(f'pad {p.GetNumber()} ({net}) closer than {req} mm to '
                                                 f'{other}.{op.GetNumber()} ({onet})'):
                        return out
            # holes of this part vs copper of the other (hole clearance)
            for hx, hy, hr, ring, pth in me['holes']:
                for onet, olay, os_, ob, olc, op in o['pads']:
                    if _near((hx - hr, hy - hr, hx + hr, hy + hr), ob, HOLE) and \
                            _gap(pcbnew.SHAPE_CIRCLE(V(hx, hy), MM(hr)), os_, HOLE) and \
                            bad(f'hole within {HOLE} mm of {other}.{op.GetNumber()}'):
                        return out
        # rigid copper
        for net, lay, s, pb, lc, p in me['pads']:
            for onet, olay, os_, ob, ox, oy in self.rigid_items:
                if olay != lay or (net and net == onet) or not _near(pb, ob, 1.2):
                    continue
                req = max(rule_clearance(net, onet, ref, None, False,
                                         self._block(pb, net) or self._block(ob, onet)), lc)
                if ref == 'J2':
                    req = max(req, J2_FOREIGN)
                if _gap(s, os_, req) and bad(f'pad {p.GetNumber()} ({net}) closer than {req} mm to rigid {onet} '
                                             f'copper at ({ox:.2f}, {oy:.2f})'):
                    return out
        for hx, hy, hr, ring, pth in me['holes']:
            for onet, olay, os_, ob, ox, oy in self.rigid_items:
                if _near((hx - hr, hy - hr, hx + hr, hy + hr), ob, HOLE) and \
                        _gap(pcbnew.SHAPE_CIRCLE(V(hx, hy), MM(hr)), os_, HOLE) and \
                        bad(f'hole within {HOLE} mm of rigid {onet} copper'):
                    return out
        # routing reservations (r8_keepclear.tsv)
        for net, lay, s, pb, lc, p in me['pads']:
            seen = set()
            for c in _cells(pb, 1.2):
                for k in self.kc_grid.get(c, ()):
                    if k in seen:
                        continue
                    seen.add(k)
                    fam, rnet, layers, rs, rb = self.keepclear[k]
                    if lay not in layers or (net and net == rnet) or not _near(pb, rb, 1.2):
                        continue
                    req = max(rule_clearance(net, rnet, ref, None, False,
                                             self._block(pb, net) or self._block(rb, rnet)), lc)
                    if ref == 'J2':
                        req = max(req, J2_FOREIGN)
                    if _gap(s, rs, req) and bad(f'pad {p.GetNumber()} ({net}) blocks the reserved spike-{fam} '
                                                f'{rnet} copper ({rb[0]:.2f}, {rb[1]:.2f})'):
                        return out
        for hx, hy, hr, ring, pth in me['holes']:
            hb = (hx - hr, hy - hr, hx + hr, hy + hr)
            for c in _cells(hb, HOLE):
                for k in self.kc_grid.get(c, ()):
                    fam, rnet, layers, rs, rb = self.keepclear[k]
                    if _near(hb, rb, HOLE) and _gap(pcbnew.SHAPE_CIRCLE(V(hx, hy), MM(hr)), rs, HOLE) and \
                            bad(f'hole within {HOLE} mm of the reserved spike-{fam} {rnet} copper'):
                        return out
        # side rules
        if side == 'B':
            for c in self.m3:
                if _gap(cy, pcbnew.SHAPE_CIRCLE(V(*c), 1), BOT_M3) and bad(f'bottom courtyard within {BOT_M3} mm of M3 {c}'):
                    return out
            if ref != 'TP122':
                for x, y, r in self.pyro_vias:
                    if _near(box, (x - r, y - r, x + r, y + r), BOT_PYRO_VIA) and \
                            _gap(cy, pcbnew.SHAPE_CIRCLE(V(x, y), MM(r)), BOT_PYRO_VIA) and \
                            bad(f'bottom courtyard within {BOT_PYRO_VIA} mm of the pyro via ({x}, {y})'):
                        return out
                tp = self.part('TP122')['pads'][0][2]
                if _gap(cy, tp, BOT_TP122) and bad(f'bottom courtyard within {BOT_TP122} mm of TP122'):
                    return out
            # J122 tie path: the courtyard's nearest point to the hole-to-hole centre line
            pts = [box[:2], (box[2], box[1]), box[2:], (box[0], box[3])]
            if min(_seg_dist(p, *TIE) for p in pts) < TIE_HALF + 10:
                seg = pcbnew.SHAPE_SEGMENT(V(*TIE[0]), V(*TIE[1]), 0)
                if _gap(cy, seg, TIE_HALF) and bad(f'bottom courtyard within {TIE_HALF} mm of the J122 tie path'):
                    return out
        else:
            for c in self.m3:
                if BARE.match(ref):
                    for net, lay, s, pb, lc, p in me['pads']:
                        if lay == pcbnew.F_Cu and _gap(s, pcbnew.SHAPE_CIRCLE(V(*c), 1), TOP_M3) and \
                                bad(f'exposed pad within {TOP_M3} mm of M3 {c}'):
                            return out
                elif _gap(cy, pcbnew.SHAPE_CIRCLE(V(*c), 1), TOP_M3) and bad(f'top courtyard within {TOP_M3} mm of M3 {c}'):
                    return out
        # F10 separation (D17)
        for other in self.fps:
            if other == ref:
                continue
            if (ref in self.rf and other in self.restricted) or (ref in self.restricted and other in self.rf):
                o = self.part(other)
                if _near(box, o['box'], RF_SEP) and _gap(cy, o['cy'], RF_SEP) and \
                        bad(f'F10: {RF_SEP} mm RF separation to {other}'):
                    return out
            if ref in self.rf or other in self.rf:
                a, o = (me, self.part(other)) if ref in self.rf else (self.part(other), me)
                rfref = ref if ref in self.rf else other
                for net, lay, s, pb, lc, p in o['fast']:
                    if _near(a['box'], pb, RF_SEP) and _gap(a['cy'], s, RF_SEP) and \
                            bad(f'F10: RF part {rfref} within {RF_SEP} mm of fast-net pad {net}'):
                        return out
        return out

    @staticmethod
    def _block(b, net):
        return net in GATES and _near(b, PYRO_BLOCK, 0)


def check(board, rows, keepclear=None, copper=None):
    """{ref: [violations]} over the movable parts (rows' refs); empty when the placement is legal."""
    m = Model(board, rows, keepclear, copper)
    out = {}
    for ref in sorted(rows):
        v = m.violations(ref)
        if v:
            out[ref] = v
    return out


def propose(board, rows, report, keepclear=None, radius=4.0, step=0.05):
    """Nearest legal position (spiral on a step grid, own rotation then +90) for each violating part, smallest
    courtyard first; returns {ref: (x, y, rot, side) or None}."""
    m = Model(board, rows, keepclear)
    order = sorted(report, key=lambda r: (m.part(r)['box'][2] - m.part(r)['box'][0]) *
                   (m.part(r)['box'][3] - m.part(r)['box'][1]))
    out = {}
    for ref in order:
        if not m.violations(ref, first=True):
            out[ref] = 'legal'
            continue
        f = m.fps[ref]
        x0, y0, rot0, side = rows[ref]
        best = None
        for rot in (rot0, rot0 + 90):
            f.SetOrientationDegrees(rot)
            for k in range(int(radius / step) + 1):
                r = k * step
                n = max(1, int(round(2 * math.pi * r / step)))
                for i in range(n):
                    x = round((x0 + r * math.cos(2 * math.pi * i / n)) / step) * step
                    y = round((y0 + r * math.sin(2 * math.pi * i / n)) / step) * step
                    f.SetPosition(V(x, y))
                    if not m.violations(ref, first=True):
                        best = (round(x, 3), round(y, 3), ((rot + 180) % 360) - 180, side)
                        break
                if best:
                    break
            if best:
                break
        if best is None:
            f.SetOrientationDegrees(rot0)
            f.SetPosition(V(x0, y0))
        out[ref] = best
    return out


def write_proposal(path, rows, proposal):
    with open(path, 'w') as fh:
        fh.write('ref\tx\ty\trot\tside\twas\n')
        for ref in sorted(proposal):
            p = proposal[ref]
            was = rows[ref]
            if p == 'legal':
                fh.write(f'# {ref}\tlegal after the moves above\n')
            elif p is None:
                fh.write(f'# {ref}\tNO LEGAL SPOT within the search radius\t\t\t\t{was}\n')
            else:
                fh.write(f'{ref}\t{p[0]:g}\t{p[1]:g}\t{p[2]:g}\t{p[3]}\t{was[0]:g},{was[1]:g},{was[2]:g}\n')
