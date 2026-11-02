#!/usr/bin/env python3
"""R10 copper primitives and explicit routing-family dispatcher; no path search."""
import argparse
import collections
import importlib
import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'm3_design'), str(ROOT / 'tools')]
import r9_route

PROJECT = ROOT / 'm3_design/assembly_review'
LAYERS = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, 'In1': pcbnew.In1_Cu, 'In2': pcbnew.In2_Cu}
FAMILIES = ('core', 'power', 'pyro', 'ports', 'servo', 'usb', 'status', 'signals', 'ground')
WIDTHS = (0.2, 0.25, 0.3, 0.4, 0.5, 0.7, 1.0, 2.0)
CORE_SHIFT = (5.0, -1.5)


def point(xy):
    return pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in xy))


def xy(position):
    return tuple(round(pcbnew.ToMM(v), 4) for v in (position.x, position.y))


class Draw:
    def __init__(self, board, dry=False):
        self.board, self.dry = board, dry
        self.tracks, self.vias = [], {}

    def pad(self, ref, number=None, net=None, at=None):
        if number is None:
            ref, number = ref.split('.')
        footprint = self.board.FindFootprintByReference(ref)
        assert footprint, f'no footprint {ref}'
        pads = [p for p in footprint.Pads() if p.GetNumber() == str(number)]
        assert pads, f'no pad {ref}.{number}'
        p = pads[0]
        pos = xy(p.GetPosition())
        assert net is None or p.GetNetname() == net, (ref, number, p.GetNetname(), net)
        assert at is None or math.dist(pos, at) < 0.001, (ref, number, pos, at)
        return pos

    def net(self, name):
        net = self.board.FindNet(name)
        assert net is not None and net.GetNetCode() > 0, f'unknown net {name}'
        return net

    def track(self, net, layer, width, points):
        assert width in WIDTHS, f'width {width} outside R10 width set'
        points = [tuple(round(v, 4) for v in p) for p in points]
        for a, b in zip(points, points[1:]):
            assert a != b and r9_route.octilinear(a, b), f'{net}: non-octilinear/zero {a} -> {b}'
            self.tracks.append((net, layer, width, a, b))
            if not self.dry:
                t = pcbnew.PCB_TRACK(self.board)
                t.SetStart(point(a)); t.SetEnd(point(b))
                t.SetWidth(pcbnew.FromMM(width)); t.SetLayer(LAYERS[layer]); t.SetNet(self.net(net))
                self.board.Add(t)

    def via(self, net, at, size=(0.5, 0.3), filled=False, capped=False):
        at = tuple(round(v, 4) for v in at)
        assert at not in self.vias, f'duplicate via {at}'
        self.vias[at] = net
        if not self.dry:
            for item in self.board.GetTracks():
                if item.GetClass() == 'PCB_VIA' and xy(item.GetPosition()) == at:
                    raise AssertionError(f'via already present {at}')
            v = pcbnew.PCB_VIA(self.board)
            v.SetPosition(point(at)); v.SetWidth(pcbnew.FromMM(size[0])); v.SetDrill(pcbnew.FromMM(size[1]))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(self.net(net)); self.board.Add(v)
            if filled:
                v.SetFillingMode(pcbnew.FILLING_MODE_FILLED)
            if capped:
                v.SetCappingMode(pcbnew.CAPPING_MODE_CAPPED)

    def zone(self, name, net, layer, pts, prio, clr=0.25, minw=0.25, conn=pcbnew.ZONE_CONNECTION_THERMAL,
             tgap=0.25, spoke=0.3):
        z = pcbnew.ZONE(self.board)
        z.SetLayer(LAYERS[layer])
        z.SetNet(self.net(net))
        z.SetZoneName(name)
        z.SetAssignedPriority(prio)
        z.SetLocalClearance(pcbnew.FromMM(clr))
        z.SetMinThickness(pcbnew.FromMM(minw))
        z.SetPadConnection(conn)
        z.SetThermalReliefGap(pcbnew.FromMM(tgap))
        z.SetThermalReliefSpokeWidth(pcbnew.FromMM(spoke))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o = z.Outline()
        o.NewOutline()
        for x, y in pts:
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        assert not o.IsSelfIntersecting(), name
        if not self.dry:
            self.board.Add(z)
        return z

    def link(self, net, layer, width, start, end, corners=()):
        """Pad-referenced, explicitly chosen polyline. No implicit routing choice."""
        self.track(net, layer, width, [self.pad(start, net=net), *corners, self.pad(end, net=net)])


class Translated:
    """Reuse a deliberate R9 local circuit table as a rigid translation."""
    def __init__(self, draw, shift):
        self.draw, self.shift = draw, shift

    def move(self, p):
        return tuple(round(a + b, 4) for a, b in zip(p, self.shift))

    def track(self, net, layer, width, points):
        self.draw.track(net, layer, width, [self.move(p) for p in points])

    def via(self, net, at, size=(0.5, 0.3)):
        self.draw.via(net, self.move(at), size)

    def pad(self, ref, number, net=None, at=None):
        result = self.draw.pad(ref, number, net, self.move(at) if at else None)
        return tuple(a - b for a, b in zip(result, self.shift))


# D-R24-17 (the owner, 2026-11-01: "I see 90 degree bends lol. why not 45"): every 90-degree bend where two track ends
# of one layer and net meet with nothing else there (route_check's right_angle at a plain node) becomes one 45-degree
# diagonal. The cut is fixed, not searched: along an axis-aligned leg CHAMFER_CUT (a 0.509 mm diagonal), along a
# diagonal leg CHAMFER_CUT_DIAG per axis (a 0.52 mm axis-aligned chamfer), unless CHAMFER_CUTS names the bend's own cut
# (pairs turning together keep their pitch p: the outer cut is the inner + p(2 - sqrt 2); wide tracks keep the chamfer
# at least their width). A cut never leaves a leg piece shorter than max(width, 0.2 mm) (half each when two bends share
# a leg), never removes copper another item joins, and never yields a chamfer shorter than max(width, 0.2 mm): such a
# bend fails the build instead, so it is redrawn in its own family's table.
CHAMFER_CUT = 0.36
CHAMFER_CUT_DIAG = 0.26
CHAMFER_CUTS = {    # (net, layer, x, y) of the bend: cut, mm along an axis-aligned leg / per axis on a diagonal one
    ('CAM_FAULT_N', 'F', 36.0, 41.0): 0.65,   # outer of CAM_PWR_EN's turn, pitch 0.5 mm: 0.36 + 0.5 x 0.586
    ('SD_SCK', 'B', 19.4, 32.1): 0.77,        # outer of SD_MISO's turn, pitch 0.7 mm: 0.36 + 0.7 x 0.586
    ('BAT_IN', 'F', 17.5, 88.891): 0.72,      # the 1.0 mm feed: a 1.018 mm chamfer and a 1.021 mm leg to its via
    ('3V3A', 'F', 26.5, 49.25): 0.25,         # 0.5 mm leg into the VDDA / VREF+ via: the rest lies in the via
    ('GND', 'B', 14.7, 48.0): 0.3,            # C31.2's 0.51 / 0.5 mm legs to its pad and via
    ('GND', 'B', 22.33, 59.73): 0.33,         # R163.2's 0.53 mm leg
    ('ARM1_SENSE', 'B', 29.75, 45.5): 0.35,   # 0.55 mm leg to the U1.33 via
    ('BUZZ_G', 'B', 20.5, 58.87): 0.15,       # the Q123 gate lead's T at (20.5, 58.7), 0.17 mm up the leg (D-R18-05)
    ('BUZZ_G', 'B', 17.75, 58.7): 0.17,       # Q123.2 (GND) 0.15 mm inside the corner (D-R18-05): 0.17 keeps 0.15 mm
    ('LED_YEL', 'F', 14.4, 43.0): 0.2,        # U1.89 (SPI1_SCK) inside the corner: 0.2 keeps 0.183 mm
    ('GPS_TX_MCU', 'F', 29.3, 16.0): 0.75,    # a >= 1 mm chamfer: no second sub-1 mm piece in the run (staircase)
    ('GPS_RX_MCU', 'F', 28.8, 11.0): 0.75,    # as GPS_TX_MCU
    ('USB_LIMITED', 'In2', 8.5, 29.0): 0.75,  # as GPS_TX_MCU, on the 0.4 mm In2 run
    ('USB_LIMITED', 'In2', 9.6, 50.85): 0.75,
    ('RAW_ACT', 'B', 22.8, 63.875): 0.34,     # R87.1 (USB_LIMITED) inside the corner: 0.34 keeps 0.152 mm
}


def chamfer_right_angles(board, cuts=CHAMFER_CUTS):
    """Chamfer every plain 90-degree bend on the board (D-R24-17); returns [(net, layer, x, y, cut)] in board order."""
    nm = pcbnew.FromMM
    tracks = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK']
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
    pads = [p for f in board.GetFootprints() for p in f.Pads()]
    by = collections.defaultdict(list)
    for t in tracks:
        by[(t.GetLayer(), t.GetNetCode())].append(t)
    ends = collections.defaultdict(list)
    for (lid, code), group in by.items():
        for t in group:
            for e, q in ((0, t.GetStart()), (1, t.GetEnd())):
                ends[(lid, code, q.x, q.y)].append((t, e))

    def on_body(t, q):
        a, b = t.GetStart(), t.GetEnd()
        return q not in (a, b) and pcbnew.SEG(a, b).Distance(q) <= 1

    def occupied(lid, code, q, skip):
        """Another item of the net joins copper at q on lid: a track end or body, a via, a pad."""
        if any(id(t) not in skip and (q in (t.GetStart(), t.GetEnd()) or on_body(t, q)) for t in by[(lid, code)]):
            return True
        if any(v.GetNetCode() == code and (v.GetPosition() - q).EuclideanNorm() <= v.GetWidth(lid) // 2 for v in vias):
            return True
        return any(p.GetNetCode() == code and p.IsOnLayer(lid) and p.HitTest(q) for p in pads)

    bends = {}
    for (lid, code, x, y), es in sorted(ends.items()):
        if len(es) != 2 or es[0][0] is es[1][0]:
            continue
        q = pcbnew.VECTOR2I(x, y)
        (t1, e1), (t2, e2) = es
        if occupied(lid, code, q, {id(t1), id(t2)}):
            continue
        far1 = t1.GetEnd() if e1 == 0 else t1.GetStart()
        far2 = t2.GetEnd() if e2 == 0 else t2.GetStart()
        u, v = far1 - q, far2 - q
        cos = (u.x * v.x + u.y * v.y) / (math.hypot(u.x, u.y) * math.hypot(v.x, v.y))
        if abs(cos) > math.sin(math.radians(0.5)) or t1.GetWidth() != t2.GetWidth():
            continue                                          # not 90 degrees (or a neck, route_check's own case)
        bends[(lid, code, x, y)] = (t1, e1, far1, t2, e2, far2)
    moves = {}
    out = []
    problems = []
    for key, (t1, e1, far1, t2, e2, far2) in bends.items():
        lid, code, x, y = key
        net = board.GetNetInfo().GetNetItem(code).GetNetname()
        name = board.GetLayerName(lid)[0] if board.GetLayerName(lid) in ('F.Cu', 'B.Cu') else board.GetLayerName(lid)[:3]
        here = (round(pcbnew.ToMM(x), 4), round(pcbnew.ToMM(y), 4))
        cut = cuts.get((net, name, *here))
        w = pcbnew.ToMM(t1.GetWidth())
        floor = max(w, 0.2)
        pts = []
        for t, far in ((t1, far1), (t2, far2)):
            dx, dy = far.x - x, far.y - y
            diag = dx != 0 and dy != 0
            c = cut if cut is not None else (CHAMFER_CUT_DIAG if diag else CHAMFER_CUT)
            length = pcbnew.ToMM(int(math.hypot(dx, dy)))
            along = c * math.sqrt(2) if diag else c
            shared = (lid, code, far.x, far.y) in bends
            limit = (length - floor) / 2 if shared else length - floor
            if c != (CHAMFER_CUT_DIAG if diag else CHAMFER_CUT):
                limit = (length - floor) / 2 if shared else length - min(floor, length / 2)   # a named cut: its own
            if along > limit + 1e-6:
                problems.append(f'{net} {name} {here}: a {c} mm cut leaves less than {floor} mm of a {length:.3f} mm leg')
            sx, sy = (1 if dx > 0 else -1 if dx < 0 else 0), (1 if dy > 0 else -1 if dy < 0 else 0)
            p = pcbnew.VECTOR2I(x + sx * nm(c), y + sy * nm(c))
            seg = pcbnew.SEG(pcbnew.VECTOR2I(x, y), p)
            joins = [r for o in by[(lid, code)] if o is not t1 and o is not t2 for r in (o.GetStart(), o.GetEnd())]
            joins += [v.GetPosition() for v in vias if v.GetNetCode() == code]
            if not all(seg.Distance(r) > 1 for r in joins):
                problems.append(f'{net} {name} {here}: the cut removes copper another item joins')
            pts.append(p)
        chamfer = pcbnew.ToMM(int((pts[0] - pts[1]).EuclideanNorm()))
        if chamfer < floor - 1e-6:
            problems.append(f'{net} {name} {here}: {chamfer:.3f} mm chamfer is shorter than {floor} mm')
        moves[(id(t1), e1)], moves[(id(t2), e2)] = (t1, pts[0]), (t2, pts[1])
        out.append((net, name, *here, cut if cut is not None else CHAMFER_CUT, pts, t1))
    assert not problems, 'right-angle bends the fixed chamfer cannot take:\n  ' + '\n  '.join(problems)
    for (_, e), (t, p) in moves.items():
        (t.SetStart if e == 0 else t.SetEnd)(p)
    for net, name, x, y, c, pts, t1 in out:
        n = pcbnew.PCB_TRACK(board)
        n.SetStart(pts[0]); n.SetEnd(pts[1])
        n.SetWidth(t1.GetWidth()); n.SetLayer(t1.GetLayer()); n.SetNet(t1.GetNet())
        board.Add(n)
    return [o[:5] for o in out]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family', choices=FAMILIES)
    parser.add_argument('--board', type=Path, default=PROJECT / 'm3.kicad_pcb')
    args = parser.parse_args()
    board = pcbnew.LoadBoard(str(args.board))
    pcbnew.KIID.SeedGenerator(10110 + FAMILIES.index(args.family))
    for zone in board.Zones():
        if not zone.GetIsRuleArea():
            zone.UnFill()
    draw = Draw(board)
    importlib.import_module(f'r10_route_{args.family}').draw(draw)
    board.BuildConnectivity()
    assert pcbnew.SaveBoard(str(args.board), board, True), 'route save failed'
    print(f'r10_route {args.family}: {len(draw.tracks)} segments, {len(draw.vias)} vias')


if __name__ == '__main__':
    main()
