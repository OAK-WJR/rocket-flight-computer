#!/usr/bin/env python3
"""R11 GND via site search (gate lane, D-R11-61): the legal spots for a GND through via near a point on the six-layer
R11 board, against the rules of m3_design/r11/m3.kicad_dru and the R11 gate. route_check --profile r11 runs it for
every allowlisted critical_via_no_gnd entry (nognd_audit): an entry whose search finds a spot fails as out of date.
R7-R10 keep m3_design/r7_hygiene.gnd_spots (four layers, R7's rules).

A spot (centre on a `step` grid round q, within `reach` of q) is legal for a through via of diameter d / drill h when,
on every copper layer (F, In1, In2, In3, In4, B; a via keeps its ring on every layer, the conservative case):
  * its ring keeps the copper clearance from every other net's track, via and flashed pad (0.1 mm, R11 floor;
    1.0 mm from a bare TP* SMD pad, 0.508 mm from a Tag-Connect J2 contact, or the pad's own local clearance);
  * its hole keeps 0.25 mm from that copper (DRU "General copper to hole clearance");
  * its hole keeps 0.2 mm from every other hole, of any net (via hole to hole 0.2 mm; KiCad's min_hole_to_hole);
  * its ring keeps 0.55 mm (inner layers) / 0.28 mm (outer layers) from another net's plated pad hole (DRU "JLC inner-
    layer PTH pad hole to copper" / "JLC outer-layer PTH hole to track") and 0.25 mm from a non-plated hole;
  * its ring keeps 0.5 mm from the board edge, and lies outside every rule area that forbids vias on any layer;
  * its hole touches no SMD pad (no via in a soldered pad, AGENTS section 3 GAP-3);
  * on an inner layer its ring keeps check_r10.BARREL_GAP (1.0 mm) from a barrel of a net in BARREL_GND_HAZARD
    (S-8: GND counts as foreign copper for ACT_GATE, ACT_DRV and PYRO1_OUT).
Other nets' zone fills do not block (a pour refills round a new via). Geometry only, on KiCad's own shapes; the
result is a site DRC would accept, not a proof that the site is electrically useful."""
import math

import pcbnew

NM = 1e6
CLEAR = 0.1                      # mm, R11 copper clearance floor (m3.kicad_dru "R11 board floor: copper clearance")
HOLE_CLEAR = 0.25                # mm, "General copper to hole clearance"
HOLE_TO_HOLE = 0.2               # mm, "R11 board floor: via hole to hole" / min_hole_to_hole
PTH_INNER, PTH_OUTER = 0.55, 0.28   # mm, JLC inner-layer PTH pad hole to copper / outer-layer PTH hole to track
EDGE = 0.5                       # mm, min_copper_edge_clearance
TP_CLEAR, TAG_CLEAR = 1.0, 0.508    # mm, bare test pads (check_r7) and Tag-Connect contacts (m3.kicad_dru)
BARREL_GAP = 1.0                 # mm, check_r10.BARREL_GAP (S-8)
BARREL_GND_HAZARD = ('ACT_GATE', 'ACT_DRV', 'PYRO1_OUT')    # check_r10.BARREL_GND_HAZARD
SIZES = ((0.45, 0.25), (0.4, 0.2))  # mm (diameter, drill): the R11 board's GND via sizes (Power / Default class)
FLOOR_SIZES = ((0.3, 0.15), (0.25, 0.15))   # mm: smaller vias the DRU still allows (via 0.25 / 0.15 mm floor, D-R11-15)


def _mm(v):
    return v / NM


def _nm(v):
    return int(round(v * NM))


def _pt(x, y):
    v = pcbnew.VECTOR2I(_nm(x), _nm(y))
    return pcbnew.SEG(v, v)


class Sites:
    """The board's obstacles round one window, read once."""

    def __init__(self, board, box):
        self.b = board
        x0, y0, x1, y1 = box
        self.box = box
        self.cu = [lid for lid in board.GetEnabledLayers().CuStack()]
        self.outer = {pcbnew.F_Cu, pcbnew.B_Cu}

        def near(bb):
            return not (_mm(bb.GetRight()) < x0 or _mm(bb.GetLeft()) > x1 or _mm(bb.GetBottom()) < y0
                        or _mm(bb.GetTop()) > y1)
        self.copper = []         # (layer, shape, clearance mm, bbox mm)
        self.holes = []          # (x, y, r, kind 'via' / 'pth' / 'npth', net)
        self.smd = []            # (shape, layer) of SMD pads (any net)
        self.barrels = []        # (x, y, ring radius) of hazard-net vias / PTH pads
        for t in board.GetTracks():
            if not near(t.GetBoundingBox()):
                continue
            net = t.GetNetname()
            if t.GetClass() == 'PCB_VIA':
                x, y = _mm(t.GetPosition().x), _mm(t.GetPosition().y)
                self.holes.append((x, y, _mm(t.GetDrillValue()) / 2, 'via', net))
                if net in BARREL_GND_HAZARD:
                    self.barrels.append((x, y, _mm(t.GetWidth(pcbnew.F_Cu)) / 2))
                if net == 'GND':
                    continue
                for lid in self.cu:
                    self.copper.append((lid, pcbnew.SHAPE_CIRCLE(t.GetPosition(), t.GetWidth(lid) // 2), CLEAR,
                                        self._bb(t.GetBoundingBox())))
            elif net != 'GND':
                self.copper.append((t.GetLayer(), pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), t.GetWidth()),
                                    CLEAR, self._bb(t.GetBoundingBox())))
        for f in board.GetFootprints():
            ref = f.GetReference()
            for p in f.Pads():
                if not near(p.GetBoundingBox()):
                    continue
                net, attr = p.GetNetname(), p.GetAttribute()
                if attr in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) and p.GetDrillSize().x > 0:
                    x, y = _mm(p.GetPosition().x), _mm(p.GetPosition().y)
                    r = _mm(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2
                    self.holes.append((x, y, r, 'pth' if attr == pcbnew.PAD_ATTRIB_PTH else 'npth', net))
                    if net in BARREL_GND_HAZARD:
                        self.barrels.append((x, y, _mm(max(p.GetSize().x, p.GetSize().y)) / 2))
                for lid in self.cu:
                    if not p.IsOnLayer(lid) or not p.FlashLayer(lid):
                        continue
                    if attr == pcbnew.PAD_ATTRIB_SMD:
                        self.smd.append((p.GetEffectiveShape(lid), lid))
                    if net == 'GND':
                        continue
                    c = CLEAR
                    if ref.startswith('TP') and attr == pcbnew.PAD_ATTRIB_SMD:
                        c = max(c, TP_CLEAR)
                    if ref == 'J2':
                        c = max(c, TAG_CLEAR)
                    local = p.GetLocalClearance()
                    if local:
                        c = max(c, _mm(local))
                    self.copper.append((lid, p.GetEffectiveShape(lid), c, self._bb(p.GetBoundingBox())))
        self.rule_areas = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
        self.edge = pcbnew.SHAPE_POLY_SET()
        board.GetBoardPolygonOutlines(self.edge, True)

    @staticmethod
    def _bb(bb):
        return (_mm(bb.GetLeft()), _mm(bb.GetTop()), _mm(bb.GetRight()), _mm(bb.GetBottom()))

    def why(self, c, d, h):
        """None when a GND via of diameter d / drill h (mm) fits at c = (x, y) mm, else the first reason it does not."""
        x, y = c
        r, rh = d / 2, h / 2
        here = _pt(x, y)
        v = pcbnew.VECTOR2I(_nm(x), _nm(y))
        if not self.edge.Contains(v) or self.edge.Outline(0).SquaredDistance(v, True) < _nm(EDGE + r) ** 2:
            return 'board edge'
        for z in self.rule_areas:
            if z.Outline().Collide(v, _nm(r)):
                return f'rule area {z.GetZoneName()}'
        reach = max(r + TP_CLEAR, rh + HOLE_CLEAR) + 0.01
        for lid, sh, cl, bb in self.copper:
            if x + reach < bb[0] or x - reach > bb[2] or y + reach < bb[1] or y - reach > bb[3]:
                continue
            need = max(r + cl, rh + HOLE_CLEAR)
            if sh.Collide(here, _nm(need)):
                return f'copper on {self.b.GetLayerName(lid)}'
        for hx, hy, hr, kind, net in self.holes:
            dist = math.hypot(hx - x, hy - y)
            if dist - hr - rh < HOLE_TO_HOLE:
                return f'hole to hole ({hx:.3f}, {hy:.3f})'
            if kind == 'pth' and net != 'GND':
                if dist - hr - r < PTH_INNER:     # every R11 via crosses the inner layers
                    return f'PTH hole ({hx:.3f}, {hy:.3f}) to inner copper'
            elif kind == 'npth' and dist - hr - r < HOLE_CLEAR:
                return f'NPTH hole ({hx:.3f}, {hy:.3f})'
        for sh, lid in self.smd:
            if sh.Collide(here, _nm(rh)):
                return 'hole in an SMD pad'
        for bx, by, br in self.barrels:
            if math.hypot(bx - x, by - y) - br - r < BARREL_GAP:
                return f'S-8 barrel ({bx:.3f}, {by:.3f})'
        return None

    def ok(self, c, d, h):
        return self.why(c, d, h) is None


def gnd_spots(board, q, reach=1.5, step=0.025, sizes=SIZES, first=False):
    """Every spot (step grid round q, centre within `reach` of q, mm) where a GND via of one of `sizes` (diameter,
    drill) is legal (Sites.why): [((x, y), (d, h), distance)], nearest first; first=True stops at the nearest one."""
    sites = Sites(board, (q[0] - reach - 2.0, q[1] - reach - 2.0, q[0] + reach + 2.0, q[1] + reach + 2.0))
    n = int(math.ceil(reach / step))
    cand = sorted((round(math.hypot(step * i, step * j), 6), (round(q[0] + step * i, 4), round(q[1] + step * j, 4)))
                  for j in range(-n, n + 1) for i in range(-n, n + 1))
    out = []
    for dist_, c in cand:
        if dist_ > reach + 1e-9:
            break
        for d, h in sizes:
            if sites.ok(c, d, h):
                out.append((c, (d, h), dist_))
                if first:
                    return out
                break
    return out
