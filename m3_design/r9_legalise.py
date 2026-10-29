#!/usr/bin/env python3
"""R9 placement legaliser (build step 3): the placement rules every part must meet before any copper is drawn.

Imported by r9_pcb.py (strict: the frozen table must be legal) and r9_place_check.py; KiCad Python. Board mm, y = 0
at the aft edge, +y forward, x = 0 the west long edge. R8's legaliser (m3_design/r8_legalise.py) generalised to the R9
contract: nothing is a fixed coordinate (the outline, the supports and J122's tie holes are read from the board), the
clearances follow R9's m3.kicad_dru (no local overrides, LC-1), and the R9 gate's placement-bound rules are applied
here so a legal table cannot fail them later (tools/check_r9.py constants are imported, never restated). A part
violates the placement when any of these fails (R9_DECISIONS D-S3-*):

  outline    every courtyard inside the outline (J3, J9 and the SMA jacks may cross it, as in R8); pads >= 0.5 mm
             from the edge and the Edge.Cuts holes (SMA pads 0.2 mm, the DRU); no hole inside a courtyard
  courtyard  courtyards on the same side keep >= COURTYARD_GAP apart
  copper     every pad keeps its clearance from every foreign pad on a shared copper layer: the R9 DRU (netclass
             0.15, RF 50 ohm lines 0.25 and SMA centre pads 0.30 to GND, RAW_ACT through-hole pads 0.3, pyro rules
             A-H and A2 with rule G's P-1b scope (gate pads outside U1's courtyard), Tag-Connect 0.508, bare test pads
             1.0), the strict pad rules of tools/pyro_probe.py (H+ 1.2, GS 1.2, AG 1.2), check_r9 P-6 (bare gate pads
             1.0 mm from bare always-live pads) and P-5 (no exposed pad pair in a forbidden solder-bridge class,
             tools/bridge_table.py), each the larger where several apply; drills >= 0.25 mm from foreign copper
  bottom     R5 L10 / check_r9 M-6: bottom parts SMD only, courtyards >= 1.5 mm from foreign through-hole pads,
             >= 2.0 mm from TP122's pad and from the J122 tie line (a 4 mm channel, M-3); every bottom model box,
             bottom pad and through-hole pin >= FIT_SUPPORT_BOTTOM (check_r9 M-5: R8's 4.452 mm) from an M3 centre
  top        top model boxes and exposed top pads >= FIT_SUPPORT_TOP (M-5: R8's 5.008 mm) from an M3 centre
  fit        fit_check's bore margin of the part (and its mated envelope) >= 0, >= check_r9.FIT_FLOORS for its
             category, bottom parts >= check_r9.FIT_BOTTOM (M-5)
  rf         check_r9 R-1: every RF part but the MCU-end interface resistors lies inside y <= y_f, no other part has a
             pad below y_f; R-10: RF parts' courtyards >= 5.94 mm from the restricted parts' courtyards and >= 5.0 mm
             from fast-net pads
  purity     check_r9 P-3 for pads: inside the CH1 courtyards' hull + 1.0 mm, foreign F.Cu pads only on GND, RAW_ACT
             or 3V3, no foreign pad barrel on In1 / In2, foreign B.Cu pads >= 1.0 mm from CH1 B.Cu pads and exposed
             ones >= 1.5 mm from the terminals' bottom pads
  coat       check_r9 P-10 on the derived PYRO_BLOCK (block_area) and J2: the coat region >= 5.0 mm from U4 and clear
             of U5, U30, U31, LS120, the jacks, J3, J9, J122, J123 and every test pad but TP122
  entry      check_r9 M-4: no top courtyard between J1's wire-entry face and the forward edge
"""
import math
import re
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'm3_design'))
import check_r7 as r7  # noqa: E402
import check_r8  # noqa: E402
import check_r9 as C9  # noqa: E402
import fit_check as fc  # noqa: E402
import bridge_table as BT  # noqa: E402
import pyro_probe as PP  # noqa: E402

MM, mm = pcbnew.FromMM, pcbnew.ToMM
COURTYARD_GAP = 0.02            # mm between courtyard outlines (their 0.05 mm lines must not touch)
NETCLASS = 0.15                 # mm, m3.kicad_pro Default
EDGE = 0.5                      # mm, m3.kicad_pro min_copper_edge_clearance
SMA_EDGE = 0.2                  # mm, m3.kicad_dru "R7 SMA pads to the aft edge"
HOLE = 0.25                     # mm, m3.kicad_dru "General copper to hole clearance"
J2_FOREIGN = 0.508              # mm, m3.kicad_dru Tag-Connect rule
TP_FOREIGN = 1.0                # mm, m3.kicad_dru "R9 bare test pads to foreign copper"
RAW_PTH = 0.3                   # mm, m3.kicad_dru "R9 RAW_ACT pins to foreign copper"
RF_GND, SMA_GND = 0.25, 0.30    # mm, m3.kicad_dru "R7 RF50 coplanar gap", "R7 SMA launch gap"
BOT_THT, BOT_TP122, TIE_HALF = C9.BOT_THT, C9.TP122_BOTTOM, C9.TIE_CHANNEL
SUPPORT_BOTTOM, SUPPORT_TOP = C9.FIT_SUPPORT_BOTTOM, C9.FIT_SUPPORT_TOP
RF_SEP_PART, RF_SEP_LINE = C9.RF_SEP_PART, C9.RF_SEP_LINE
EDGE_PARTS = {'J3', 'J9', 'J30', 'J31'}   # J3 overhangs 0.45 mm (HRO), J9's courtyard may reach the east edge, the
                                          # SMA jacks overhang the aft edge (as in R8)
BARE_TP = re.compile(r'^TP\d+$')
LIVE = set(PP.LIVE)
GATES = set(PP.GATES)
SENSE = set(PP.SENSE)
H_LIVE, H_SENSE_GATE, H_MID, H_GATE, H_OWN = set(PP.H_LIVE), set(PP.H_SENSE_GATE), set(PP.H_MID), set(PP.H_GATE), \
    set(PP.H_OWN)
GS_SENSE, ACT_GATES = set(PP.GS_SENSE), set(PP.ACT_GATES)
ALWAYS_LIVE = set(C9.ALWAYS_LIVE)
RF_NETS50 = {'GNSS_RF_ANT', 'GNSS_RF_IN', 'RADIO_RF_ANT', 'RADIO_RF'}
# PYRO_BLOCK derivation (block_area): CH1 courtyards grown by P-1's 1.0 mm + BLOCK_MARGIN, exit-net CH1 pads grown by
# P-1's 3.0 mm reach + BLOCK_MARGIN, block-net copper already drawn and exit-net copper within check_actuators 15b's
# reach of a CH1 pad (step 5, D-S5-11), closed by BLOCK_CLOSE (a gap narrower than 2 x BLOCK_CLOSE between two parts'
# boxes is filled, so copper running between them stays inside), rectilinear, no hole, on a 0.1 mm grid
BLOCK_MARGIN, BLOCK_CLOSE, BLOCK_GRID = 0.1, 1.5, 0.1
EXIT_STEP = 0.05                # mm, exit-net track sampling for block_area (finer than check_actuators 15b's 0.1)


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def _sym(a, b, sa, sb):
    return (a in sa and b in sb) or (b in sa and a in sb)


def rule_clearance(na, nb, ra, rb, g_scope_a=True, g_scope_b=True, pads=True, pad_a=None, pad_b=None):
    """Required copper clearance (mm) between items of nets na / nb owned by footprints ra / rb (None: board copper)
    under R9's m3.kicad_dru, as the maximum of every rule that matches (KiCad applies the last matching rule; every
    later rule in the file is >= the earlier ones it overlaps, so the maximum is the same or stricter). g_scope_*:
    the item lies inside rule G's R9 scope (PYRO_BLOCK, or outside U1's courtyard). pad_*: the PAD objects (for the
    through-hole and test-pad rules)."""
    if na == nb and na:
        return 0.0
    same = ra is not None and ra == rb
    req = NETCLASS
    if _sym(na, nb, RF_NETS50, {'GND'}):
        req = max(req, RF_GND)
    for pa, rr, n in ((pad_a, ra, na), (pad_b, rb, nb)):
        if pa is None:
            continue
        if rr in ('J30', 'J31') and n != 'GND' and (nb if n == na else na) == 'GND':
            req = max(req, SMA_GND)
        if n == 'RAW_ACT' and pa.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            req = max(req, RAW_PTH)
        if rr == 'J2' and not same:
            req = max(req, J2_FOREIGN)
        if rr and BARE_TP.match(rr) and not same:
            req = max(req, TP_FOREIGN)
    for a, b, x, sa in ((na, nb, ra, g_scope_a), (nb, na, rb, g_scope_b)):
        if a == 'RAW_ACT' and b in GATES | SENSE:                                         # A
            req = max(req, 0.5)
        if a in LIVE and b in GATES and not (same and x == 'Q124'):                        # B
            req = max(req, 0.5)
        if a in LIVE and b in SENSE and not (same and x in ('R173', 'R131', 'R132')):      # C
            req = max(req, 0.3)
        if a == 'GND' and b in LIVE and not (same and x in ('Q124', 'C128')):              # D
            req = max(req, 0.5)
        if a == 'RAW_ACT' and b in ('PYRO1_BUS', 'PYRO1_IGN'):                             # E
            req = max(req, 1.0)
        if a in LIVE and b and b != 'GND' and b not in SENSE | GATES | LIVE and \
                not (a in ('PYRO1_BUS', 'PYRO1_IGN') and b == 'RAW_ACT') and not (same and x == 'Q124'):   # F
            req = max(req, 0.5)
        if a in GATES and sa and b and b not in {'GND', 'RAW_ACT'} | LIVE | GATES and not (same and x == 'Q124'):  # G
            req = max(req, 0.3)
        if a == 'RAW_ACT' and b == 'RAW_ACT_SENSE':                                         # A2
            req = max(req, 0.3)
        if pads and not (same and x in H_OWN) and \
                ((a in H_LIVE and b in H_SENSE_GATE) or (a in H_MID and b in H_GATE)):     # H
            req = max(req, 1.0)
    return req


def strict_pad(na, nb, ra, rb, exposed_same_face):
    """The R9 strict pad rules for a pad pair on a shared copper layer (mm): pyro_probe H+, GS, AG; check_r9 P-6 and
    P-5's forbidden solder-bridge classes for two exposed pads on the same face of different parts."""
    req = 0.0
    same = ra is not None and ra == rb
    for a, b, x in ((na, nb, ra), (nb, na, rb)):
        if not (same and x in H_OWN) and ((a in H_LIVE and b in H_SENSE_GATE) or (a in H_MID and b in H_GATE)):
            req = max(req, PP.STRICT)                                                        # H+
        if not same and a in GATES and b in GS_SENSE:
            req = max(req, PP.STRICT)                                                        # GS
        if not same and a in ACT_GATES and b == 'GND':
            req = max(req, PP.STRICT)                                                        # AG
    if exposed_same_face and not same and na != nb:
        if (na in GATES | ACT_GATES and nb in ALWAYS_LIVE) or (nb in GATES | ACT_GATES and na in ALWAYS_LIVE):
            req = max(req, C9.BARE_GATE)                                                     # P-6
        cls = BT.classify(na, nb)
        if cls is not None and not cls[1]:
            req = max(req, cls[2])                                                           # P-5
    return req


GRID = 2.0


def _box(s):
    bb = s.BBox()
    return mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())


def _near(a, b, d):
    return not (a[2] + d < b[0] or b[2] + d < a[0] or a[3] + d < b[1] or b[3] + d < a[1])


def _gap(a, b, limit):
    """True when shapes a and b are closer than limit mm (edge to edge)."""
    return pcbnew.SHAPE.Collide(a, b, max(MM(limit) - 1, 0))


def _rect(x0, y0, x1, y1):
    s = pcbnew.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        s.Append(MM(x), MM(y))
    return s


def _point_box(p, b):
    return math.hypot(max(b[0] - p[0], 0, p[0] - b[2]), max(b[1] - p[1], 0, p[1] - b[3]))


# --- the derived PYRO_BLOCK area (P-1) ------------------------------------------------------------------------------
def block_area(board):
    """The PYRO_BLOCK outline derived from the board (check_r9 P-1 and check_actuators 15b by construction): the union
    of every CH1 courtyard's box grown by 1.0 + BLOCK_MARGIN, every CH1 pad of an exit net grown by 3.0 + BLOCK_MARGIN,
    every track / via of the block's internal nets grown by BLOCK_MARGIN, and the part of every exit-net track / via
    within check_actuators 15b's reach of a CH1 pad of its net (EXIT_REACH plus the pad's half diagonal from the pad
    centre, sampled every EXIT_STEP like 15b) grown by its half width + BLOCK_MARGIN (later steps' copper); closed by
    BLOCK_CLOSE, holes filled, snapped outward to BLOCK_GRID. Returns [(x, y), ...] (one rectilinear outline).
    Step 5 (R9_DECISIONS D-S5-11): an exit-net track counts only within that reach, as P-1 and 15b require, not by its
    whole bounding box, so a long exit lane does not pull the area (and rule G's scope) out to U1's pins."""
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    boxes = []
    for ref in C9.CH1_PARTS:
        b = _box(check_r8.courtyard(fps[ref]))
        g = C9.COURTYARD_GROW + BLOCK_MARGIN
        boxes.append((b[0] - g, b[1] - g, b[2] + g, b[3] + g))
        for p in fps[ref].Pads():
            if p.GetNetname() in C9.EXIT_NETS:
                pb = p.GetBoundingBox()
                g = C9.EXIT_REACH + BLOCK_MARGIN
                boxes.append((mm(pb.GetLeft()) - g, mm(pb.GetTop()) - g, mm(pb.GetRight()) + g, mm(pb.GetBottom()) + g))
    reach = {}                                           # exit net -> [(pad centre, 15b's reach)]
    for ref in C9.CH1_PARTS:
        for p in fps[ref].Pads():
            if p.GetNetname() in C9.EXIT_NETS:
                sz = p.GetSize(pcbnew.F_Cu)
                reach.setdefault(p.GetNetname(), []).append(
                    ((mm(p.GetPosition().x), mm(p.GetPosition().y)), C9.EXIT_REACH + math.hypot(mm(sz.x), mm(sz.y)) / 2))
    for t in board.GetTracks():
        n = t.GetNetname()
        tb = t.GetBoundingBox()
        b = (mm(tb.GetLeft()), mm(tb.GetTop()), mm(tb.GetRight()), mm(tb.GetBottom()))
        if n in C9.BLOCK_NETS:
            boxes.append((b[0] - BLOCK_MARGIN, b[1] - BLOCK_MARGIN, b[2] + BLOCK_MARGIN, b[3] + BLOCK_MARGIN))
        elif n in C9.EXIT_NETS:
            if t.GetClass() == 'PCB_VIA':
                pts, w = [(mm(t.GetPosition().x), mm(t.GetPosition().y))], mm(t.GetWidth(pcbnew.F_Cu)) / 2
            else:
                a, c = (mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y))
                k = max(1, math.ceil(math.dist(a, c) / EXIT_STEP))
                pts = [(a[0] + (c[0] - a[0]) * i / k, a[1] + (c[1] - a[1]) * i / k) for i in range(k + 1)]
                w = mm(t.GetWidth()) / 2
            g = w + BLOCK_MARGIN
            for q in pts:
                if any(math.dist(q, c0) <= r0 + w + EXIT_STEP for c0, r0 in reach.get(n, ())):
                    boxes.append((q[0] - g, q[1] - g, q[0] + g, q[1] + g))
    u = pcbnew.SHAPE_POLY_SET()
    for b in boxes:
        u.BooleanAdd(_rect(*b))
    u.Inflate(MM(BLOCK_CLOSE), pcbnew.CORNER_STRATEGY_ALLOW_ACUTE_CORNERS, MM(0.001))
    u.Inflate(-MM(BLOCK_CLOSE), pcbnew.CORNER_STRATEGY_ALLOW_ACUTE_CORNERS, MM(0.001))
    if u.OutlineCount() != 1:
        # disjoint groups: join them with their common bounding box (the conservative side: a larger area)
        bb = _box(u)
        u = _rect(*bb)
    ch = u.Outline(0)
    pts = [(mm(ch.CPoint(k).x), mm(ch.CPoint(k).y)) for k in range(ch.PointCount())]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    out = []
    for x, y in pts:                                  # snap outward (away from the centroid) to the grid
        sx = math.floor(x / BLOCK_GRID + 1e-6) if x < cx else math.ceil(x / BLOCK_GRID - 1e-6)
        sy = math.floor(y / BLOCK_GRID + 1e-6) if y < cy else math.ceil(y / BLOCK_GRID - 1e-6)
        q = (round(sx * BLOCK_GRID, 3), round(sy * BLOCK_GRID, 3))
        if not out or q != out[-1]:
            out.append(q)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    # drop collinear points
    clean = []
    n = len(out)
    for i in range(n):
        a, b, c = out[i - 1], out[i], out[(i + 1) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
            clean.append(b)
    return clean


def _box_of_pad(p):
    b = p.GetBoundingBox()
    return mm(b.GetLeft()), mm(b.GetTop()), mm(b.GetRight()), mm(b.GetBottom())


def poly_of(points):
    s = pcbnew.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in points:
        s.Append(MM(x), MM(y))
    return s


class Model:
    """Geometry of the board for the placement rules; parts are re-read from their footprints on demand."""

    def __init__(self, board, movable, y_f=C9.Y_F):
        self.b = board
        self.fps = {f.GetReference(): f for f in board.GetFootprints()}
        self.movable = set(movable)
        self.y_f = y_f
        self.prj = Path(board.GetFileName()).resolve().parent if board.GetFileName() else ROOT / 'm3_design/assembly_review'
        self.cu = list(board.GetEnabledLayers().CuStack())
        holes, outline = fc.board_geometry(board)
        self.outline = outline
        self.W, self.L = outline[2] - outline[0], outline[3] - outline[1]
        self.edge_holes = [(c, 1.6) for c in holes]
        self.ties = fc.retention_holes(board, holes)
        self.supports = [c for c in holes if all(math.dist(c, t) > 0.02 for t in self.ties)]
        self.restricted = {r for r, f in self.fps.items() if any(p.GetNetname() in check_r8.SWITCH_NETS
                                                                  for p in f.Pads())}
        self.restricted |= {r for r in check_r8.BUCK_PARTS + check_r8.NOISY_PARTS if r in self.fps}
        self.rf = {r for r in self.fps if r7.RF_PART.fullmatch(r)}
        self.cache = {}
        self._derived = None

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
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            exp = {'F': p.IsOnLayer(pcbnew.F_Cu) and p.IsOnLayer(pcbnew.F_Mask),
                   'B': p.IsOnLayer(pcbnew.B_Cu) and p.IsOnLayer(pcbnew.B_Mask)}
            for lay in self.cu:
                if p.IsOnLayer(lay):
                    s = check_r8.item_shape(p, lay)
                    face = 'F' if lay == pcbnew.F_Cu else 'B' if lay == pcbnew.B_Cu else None
                    pads.append((p.GetNetname(), lay, s, _box(s), p, bool(face and exp[face])))
        holes = []
        for p in f.Pads():
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                pp = p.GetPosition()
                holes.append((mm(pp.x), mm(pp.y), mm(p.GetDrillSize().x) / 2, mm(max(p.GetSize().x, p.GetSize().y)) / 2,
                              p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH))
        info = dict(side=side, cy=cy, box=_box(cy), pads=pads, holes=holes,
                    fast=[x for x in pads if check_r8.FAST_NETS.match(x[0] or '')],
                    gscope=self._gate_scope(ref, pads))
        self.cache[ref] = (key, info)
        return info

    def _gate_scope(self, ref, pads):
        """Per pad index: inside rule G's R9 scope (outside U1's courtyard, or inside PYRO_BLOCK)."""
        if ref != 'U1':
            return [True] * len(pads)
        return [False] * len(pads)          # U1's own pads lie inside its courtyard (the MCU pin's escape)

    def derived(self):
        """(block outline polygon, CH1 hull + 1 mm, CH1 B.Cu pads, terminal B.Cu pads) for the current placement."""
        key = tuple((self.fps[r].GetPosition().x, self.fps[r].GetPosition().y, self.fps[r].GetOrientationDegrees())
                    for r in C9.CH1_PARTS)
        if self._derived and self._derived[0] == key:
            return self._derived[1]
        pts = []
        for r in C9.CH1_PARTS:
            pts += C9.poly_points(check_r8.courtyard(self.fps[r]))
        h = C9.inflate(C9.poly_of_points(C9.hull(pts)), C9.HULL_GROW)
        block = poly_of(block_area(self.b))
        ch1_b = [(f'{r}.{p.GetNumber()}', p.GetNetname(), p.GetEffectiveShape(pcbnew.B_Cu))
                 for r in C9.CH1_PARTS for p in self.fps[r].Pads()
                 if p.IsOnLayer(pcbnew.B_Cu) and C9.CH1_NET.match(p.GetNetname() or '')]
        term_b = [(f'{r}.{p.GetNumber()}', p.GetEffectiveShape(pcbnew.B_Cu)) for r in ('J121', 'J124')
                  for p in self.fps[r].Pads() if p.IsOnLayer(pcbnew.B_Cu)]
        val = dict(hull=h, hull_box=_box(h), block=block, block_box=_box(block), ch1_b=ch1_b, term_b=term_b)
        self._derived = (key, val)
        return val

    def fit_rows(self, ref):
        """[(category, margin, floor)] of the part's bore fit (fit_check's margin, model box and mated envelope)."""
        f = self.fps[ref]
        if fc.board_feature(f) or f.GetAttributes() & pcbnew.FP_DNP:
            return []
        box = fc.model_box(f, self.prj)
        if box is None:
            return [(ref, None, 0.0)]
        out = []
        side = 'B' if f.IsFlipped() else 'F'
        floor = C9.FIT_FLOORS.get(ref, (0.0, None))[0]
        if side == 'B':
            floor = max(floor, C9.FIT_BOTTOM)
        out.append((ref, fc.margin(box, 24.9, 23.0, 0.3), floor))
        spec = fc.MATED.get(fc.fp_name(f))
        if spec:
            mb = fc.footprint_box(f, spec['box'])
            out.append((ref + ' mated', fc.margin(mb, 24.9, 23.0, 0.3), C9.FIT_FLOORS.get(ref + ' mated', (0.0, None))[0]))
        return out

    def support_rows(self, ref):
        """[(what, distance to the nearest support, required)] for the M-5 support floors (fit_check's measures)."""
        f = self.fps[ref]
        out = []
        feature = fc.board_feature(f) or f.GetAttributes() & pcbnew.FP_DNP
        box = None if feature else fc.model_box(f, self.prj)
        bottom, top_boxes, top_pads = [], [], []
        if f.IsFlipped():
            if box is not None:
                bottom.append((ref, box))
            bottom += [(f'{ref}.{p.GetNumber()}', fc.pad_box(p)) for p in f.Pads() if p.IsOnLayer(pcbnew.B_Cu)
                       and (not feature or (p.IsOnLayer(pcbnew.B_Mask) and not p.IsTented(pcbnew.B_Cu)))]
        else:
            if box is not None:
                top_boxes.append((ref, box))
            bottom += [(f'{ref}.{p.GetNumber()} pin', fc.pad_box(p)) for p in f.Pads()
                       if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
        if feature and not f.IsFlipped():
            bottom += [(f'{ref}.{p.GetNumber()} exposed bottom pad', fc.pad_box(p)) for p in f.Pads()
                       if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH and p.IsOnLayer(pcbnew.B_Cu)
                       and p.IsOnLayer(pcbnew.B_Mask) and not p.IsTented(pcbnew.B_Cu)]
        top_pads = [(f'{ref}.{p.GetNumber()}', p) for p in f.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH
                    and p.IsOnLayer(pcbnew.F_Cu) and p.IsOnLayer(pcbnew.F_Mask) and not p.IsTented(pcbnew.F_Cu)]
        for hole in self.supports:
            for what, b in bottom:
                out.append((what, fc.point_box_distance(hole, b), SUPPORT_BOTTOM, hole))
            for what, b in top_boxes:
                out.append((what + ' top body', fc.point_box_distance(hole, b), SUPPORT_TOP, hole))
            for what, p in top_pads:
                c = (p.GetPosition().x, p.GetPosition().y)
                if math.hypot(mm(c[0]) - hole[0], mm(c[1]) - hole[1]) > SUPPORT_TOP + 6:
                    continue
                out.append((what + ' exposed top pad', fc.copper_distance(p, V(*hole)), SUPPORT_TOP, hole))
        return out

    # --- rules ----------------------------------------------------------------------------------------------------
    def violations(self, ref, first=False):
        out = []

        def bad(msg):
            out.append(msg)
            return first
        me = self.part(ref)
        side, cy, box = me['side'], me['cy'], me['box']
        x0, y0, x1, y1 = self.outline
        if ref not in EDGE_PARTS and (box[0] < x0 or box[1] < y0 or box[2] > x1 or box[3] > y1):
            if bad('courtyard outside the outline'):
                return out
        # R-1: the RF strip by content
        if ref in self.rf and ref not in C9.MCU_END and box[3] > self.y_f + 1e-6:
            if bad(f'R-1: RF part courtyard reaches y {box[3]:.2f} (strip boundary y_f {self.y_f})'):
                return out
        if ref not in self.rf:
            for net, lay, s, pb, p, ex in me['pads']:
                if pb[1] < self.y_f - 1e-6 and bad(f'R-1: pad {p.GetNumber()} ({net}) in the RF strip (y < {self.y_f})'):
                    return out
        # outline and Edge.Cuts holes for pads
        for net, lay, s, pb, p, ex in me['pads']:
            edge = SMA_EDGE if ref in ('J30', 'J31') else EDGE
            if ref not in EDGE_PARTS and (pb[0] < x0 + edge or pb[1] < y0 + edge or pb[2] > x1 - edge or
                                          pb[3] > y1 - edge):
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
        # bottom parts are SMD only (M-6)
        if side == 'B' and me['holes'] and bad('bottom part with drilled pads (bottom parts SMD only, M-6)'):
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
            for i, (net, lay, s, pb, p, ex) in enumerate(me['pads']):
                for j, (onet, olay, os_, ob, op, oex) in enumerate(o['pads']):
                    if olay != lay or (net and net == onet) or not _near(pb, ob, 1.6):
                        continue
                    req = rule_clearance(net, onet, ref, other, me['gscope'][i], o['gscope'][j], True, p, op)
                    face = 'F' if lay == pcbnew.F_Cu else 'B' if lay == pcbnew.B_Cu else None
                    req = max(req, strict_pad(net, onet, ref, other, bool(face and ex and oex)))
                    if _gap(s, os_, req) and bad(f'pad {p.GetNumber()} ({net}) closer than {req} mm to '
                                                 f'{other}.{op.GetNumber()} ({onet}) on {self.b.GetLayerName(lay)}'):
                        return out
            # drills of this part vs copper of the other (hole clearance)
            for hx, hy, hr, ring, pth in me['holes']:
                for onet, olay, os_, ob, op, oex in o['pads']:
                    if _near((hx - hr, hy - hr, hx + hr, hy + hr), ob, HOLE) and \
                            _gap(pcbnew.SHAPE_CIRCLE(V(hx, hy), MM(hr)), os_, HOLE) and \
                            bad(f'hole within {HOLE} mm of {other}.{op.GetNumber()}'):
                        return out
        # side rules: bottom keep-outs (M-6, M-3) and the support floors (M-5)
        if side == 'B' and ref != 'TP122' and 'TP122' in self.fps:
            tp = [x[2] for x in self.part('TP122')['pads'] if x[1] == pcbnew.B_Cu]
            if tp and _gap(cy, tp[0], BOT_TP122) and bad(f'bottom courtyard within {BOT_TP122} mm of TP122'):
                return out
        if side == 'B' and len(self.ties) == 2:
            seg = pcbnew.SHAPE_SEGMENT(V(*self.ties[0]), V(*self.ties[1]), 0)
            if _gap(cy, seg, TIE_HALF) and bad(f'bottom courtyard within {TIE_HALF} mm of the J122 tie path (M-3)'):
                return out
        for what, d, need, hole in self.support_rows(ref):
            if d < need - 1e-4 and bad(f'{what} {d:.3f} mm from support {hole} (M-5 floor {need} mm)'):
                return out
        # bore fit (M-5)
        for cat, mgn, floor in self.fit_rows(ref):
            if mgn is None:
                if bad(f'{cat}: no readable 3D model (fit_check)'):
                    return out
            elif mgn < floor - 1e-6 and bad(f'fit: {cat} bore margin {mgn:.3f} mm below {floor} mm (M-5)'):
                return out
        # F10 separation (R-10)
        for other in self.fps:
            if other == ref:
                continue
            if (ref in self.rf and other in self.restricted) or (ref in self.restricted and other in self.rf):
                o = self.part(other)
                if _near(box, o['box'], RF_SEP_PART) and _gap(cy, o['cy'], RF_SEP_PART) and \
                        bad(f'R-10: {RF_SEP_PART} mm RF separation to {other}'):
                    return out
            if ref in self.rf or other in self.rf:
                a, o = (me, self.part(other)) if ref in self.rf else (self.part(other), me)
                rfref = ref if ref in self.rf else other
                for net, lay, s, pb, p, ex in o['fast']:
                    if _near(a['box'], pb, RF_SEP_LINE) and _gap(a['cy'], s, RF_SEP_LINE) and \
                            bad(f'R-10: RF part {rfref} within {RF_SEP_LINE} mm of fast-net pad {net}'):
                        return out
        # P-3 block purity for pads, P-10 coat region (both derived from the CH1 placement)
        d = self.derived()
        if ref not in C9.CH1_PARTS and _near(box, d['hull_box'], 1.6):
            for net, lay, s, pb, p, ex in me['pads']:
                if not net or net.startswith('unconnected-') or C9.CH1_NET.match(net) or net == 'GND':
                    continue
                if not _near(pb, d['hull_box'], 1.6):
                    continue
                inside = pcbnew.SHAPE.Collide(d['hull'], s, 0)
                if lay == pcbnew.F_Cu and inside and net not in C9.PURITY_F:
                    if bad(f'P-3: pad {p.GetNumber()} ({net}) on F.Cu inside the CH1 hull + {C9.HULL_GROW} mm'):
                        return out
                elif lay in (pcbnew.In1_Cu, pcbnew.In2_Cu) and inside:
                    if bad(f'P-3: pad {p.GetNumber()} ({net}) on {self.b.GetLayerName(lay)} inside the CH1 hull'):
                        return out
                elif lay == pcbnew.B_Cu:
                    if inside:
                        for lab, n2, s2 in d['ch1_b']:
                            if _gap(s, s2, C9.PURITY_B_GAP) and \
                                    bad(f'P-3: pad {p.GetNumber()} ({net}) on B.Cu within {C9.PURITY_B_GAP} mm of CH1 {lab}'):
                                return out
                    if ex:
                        for lab, s2 in d['term_b']:
                            if _gap(s, s2, C9.PURITY_BARE_GAP) and \
                                    bad(f'P-3: exposed pad {p.GetNumber()} ({net}) within {C9.PURITY_BARE_GAP} mm of {lab}'):
                                return out
        coat = pcbnew.SHAPE_POLY_SET(d['block'])
        if 'J2' in self.fps:
            coat.BooleanAdd(check_r8.courtyard(self.fps['J2']))
        cbox = _box(coat)
        if ref == 'U4' and _near(box, cbox, C9.COAT_U4) and _gap(cy, coat, C9.COAT_U4):
            if bad(f'P-10: U4 within {C9.COAT_U4} mm of the coat region (PYRO_BLOCK, J2)'):
                return out
        if ref in C9.COAT_KEEPOFF and _near(box, cbox, 0) and pcbnew.SHAPE.Collide(coat, cy, 0):
            if bad('P-10: inside the coat region (PYRO_BLOCK, J2): a coating keep-off'):
                return out
        if BARE_TP.match(ref) and ref != 'TP122':
            for net, lay, s, pb, p, ex in me['pads']:
                if lay in (pcbnew.F_Cu, pcbnew.B_Cu) and _near(pb, cbox, 0) and pcbnew.SHAPE.Collide(coat, s, 0):
                    if bad('P-10: test pad inside the coat region (only TP122 may be)'):
                        return out
        if ref in C9.CH1_PARTS or ref == 'J2':             # the region moved: every keep-off part must still clear it
            for other in sorted(C9.COAT_KEEPOFF + ('U4',)):
                if other not in self.fps:
                    continue
                ocy = self.part(other)['cy']
                lim = C9.COAT_U4 if other == 'U4' else 0
                hit = _gap(ocy, coat, lim) if lim else pcbnew.SHAPE.Collide(coat, ocy, 0)
                if hit and bad(f'P-10: the coat region reaches {other}'):
                    return out
        # M-4: nothing stands in front of J1's wire entry
        if 'J1' in self.fps and ref != 'J1' and side == 'F':
            j = self.part('J1')
            jb = j['box']
            corridor = _rect(jb[0], jb[3], jb[2], y1)
            if jb[3] < y1 - 0.01 and _near(box, (jb[0], jb[3], jb[2], y1), 0) and \
                    pcbnew.SHAPE.Collide(corridor, cy, -MM(0.01)) and bad('M-4: stands in front of J1\'s wire entry'):
                return out
        return out


def check(board, refs, y_f=C9.Y_F):
    """{ref: [violations]} over refs; empty when the placement is legal."""
    m = Model(board, refs, y_f)
    out = {}
    for ref in sorted(refs):
        v = m.violations(ref)
        if v:
            out[ref] = v
    return out


def propose(board, rows, report, radius=4.0, step=0.05, y_f=C9.Y_F, turn=True):
    """Nearest legal position (spiral on a step grid, own rotation then +90 if turn) for each violating part,
    smallest courtyard first; returns {ref: (x, y, rot, side) or None or 'legal'} (a design aid only)."""
    m = Model(board, rows, y_f)
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
        for rot in ((rot0, rot0 + 90) if turn else (rot0,)):
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
