#!/usr/bin/env python3
"""Draw the M3-ASSY-R12 copper (r12_plan.md section 4, stage C; stageC.md) on the placed board: every track and via
of m3_design/r12_routes.tsv (an explicit table; the build never searches, D-R12-26), then the planes and pours.

usage: <KiCad python3> -I -B m3_design/r12_route.py [--board m3_design/r12/m3.kicad_pcb] [--routes m3_design/r12_routes.tsv]

Copper (D-R12-22, -34): F.Cu parts and signals; In1.Cu one unbroken GND plane; In2.Cu a mixed layer: the 3V3 pour with
the RAW_PROTECTED, 3V3A and PORT_4V8 islands of m3_design/r12_planes.tsv, filling round In2's low / medium-speed signal
tracks (minimum pour width 0.25 mm); B.Cu signals under a GND pour
(minimum width 0.5 mm, so no sliver or finger can form, route_check pour rules). Every via is a 0.3 / 0.45 mm through
via (D-R12-03). Pyro barrels keep foreign inner copper away (S-8, stageC.md section 5): rule areas on In1 / In2 round
J121's barrels, which also keep out every track and via on those layers (D-R12-34). Each segment is checked octilinear and non-zero, each via against the one R12 size; a via is never
placed twice. The zones are filled with KiCad's filler and the board saved; a rebuild is byte-identical.
"""
import argparse
import csv
import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'm3_design/r12/m3.kicad_pcb'
ROUTES = ROOT / 'm3_design/r12_routes.tsv'
PLANES = ROOT / 'm3_design/r12_planes.tsv'
LAYERS = {'F': pcbnew.F_Cu, 'In1': pcbnew.In1_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}
VIA = (0.45, 0.3)
WIDTHS = (0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.8, 1.0)
KIID_SEED = 12212
MM = pcbnew.FromMM
# S-8 (R10 check_r10, R11 D-R11-23 lineage): a pyro barrel keeps >= 1 mm to foreign inner copper; J121.2 (PYRO1_IGN)
# on both planes, J121.1 (PYRO1_OUT) on In2 only (GND is not foreign at PYRO1_OUT, D-R19-01). Radius from the barrel
# centre: hole 0.65 + 1.0 + 0.1 mm fill tolerance.
S8_KEEPOUT = (('J121', '2', ('In1', 'In2')), ('J121', '1', ('In2',)))
S8_R = 1.75


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def read_routes(path):
    tracks, vias = [], []
    with open(path) as fh:
        for r in csv.DictReader((l for l in fh if not l.startswith('#')), delimiter='\t'):
            if r['kind'] == 'track':
                tracks.append((r['net'], r['layer'], float(r['width']), (float(r['x0']), float(r['y0'])),
                               (float(r['x1']), float(r['y1']))))
            elif r['kind'] == 'via':
                vias.append((r['net'], float(r['x0']), float(r['y0'])))
            else:
                raise ValueError(f'unknown row kind {r["kind"]}')
    return tracks, vias


def read_planes(path, length):
    """m3_design/r12_planes.tsv: (net, layer, priority, [(x, y)]); 'L' in a vertex is the board length."""
    out = []
    for line in Path(path).read_text().splitlines():
        if line.startswith('#') or line.startswith('net\t') or not line.strip():
            continue
        net, layer, prio, pts = line.split('\t')
        out.append((net, layer, int(prio), [tuple(length if v == 'L' else float(v) for v in q.split(','))
                                              for q in pts.split()]))
    return out


def octilinear(a, b):
    dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
    return (dx > 1e-6 or dy > 1e-6) and (dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-6)


def zone(board, net, layer, pts, name, min_w, clearance, priority=0):
    z = pcbnew.ZONE(board)
    z.SetLayer(LAYERS[layer])
    z.SetNet(board.FindNet(net))
    z.SetZoneName(name)
    z.SetMinThickness(MM(min_w))
    z.SetLocalClearance(MM(clearance))
    z.SetAssignedPriority(priority)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.25))
    z.SetThermalReliefSpokeWidth(MM(0.3))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(MM(x), MM(y))
    board.Add(z)
    return z


def keepout(board, name, layers, cx, cy, r):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(LAYERS[l])
    z.SetLayerSet(ls)
    z.SetZoneName(name)
    z.SetDoNotAllowTracks(True)       # D-R12-34: In2 carries signal tracks; none may enter S-8's reach
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for k in range(16):
        a = 2 * math.pi * k / 16
        o.Append(MM(round(cx + r * math.cos(a), 4)), MM(round(cy + r * math.sin(a), 4)))
    board.Add(z)


def build(board_path, routes):
    board = pcbnew.LoadBoard(str(board_path))
    pcbnew.KIID.SeedGenerator(KIID_SEED)
    tracks, vias = read_routes(routes)
    seen = set()
    for net, layer, w, a, b in tracks:
        assert octilinear(a, b), f'{net}: segment {a} {b} not octilinear or zero'
        assert any(abs(w - s) < 1e-9 for s in WIDTHS), f'{net}: width {w}'
        n = board.FindNet(net)
        assert n is not None and n.GetNetCode() > 0, f'unknown net {net}'
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(*a))
        t.SetEnd(V(*b))
        t.SetWidth(MM(w))
        t.SetLayer(LAYERS[layer])
        t.SetNet(n)
        board.Add(t)
    for net, x, y in vias:
        key = (round(x, 4), round(y, 4))
        assert key not in seen, f'via twice at {key}'
        seen.add(key)
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(V(x, y))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetWidth(MM(VIA[0]))
        v.SetDrill(MM(VIA[1]))
        v.SetNet(board.FindNet(net))
        board.Add(v)
    bb = board.GetBoardEdgesBoundingBox()
    w, length = round(pcbnew.ToMM(bb.GetWidth()) - 0.05, 3), round(pcbnew.ToMM(bb.GetHeight()) - 0.05, 3)
    rect = [(0, 0), (w, 0), (w, length), (0, length)]
    for net, layer, prio, pts in read_planes(PLANES, length):
        zone(board, net, layer, pts, f'{net}_{layer}', 0.25, 0.2, prio)
    zone(board, 'GND', 'B', rect, 'GND_pour_B', 0.5, 0.2)
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    for ref, num, layers in S8_KEEPOUT:
        p = next(p for p in fps[ref].Pads() if p.GetNumber() == num)
        c = p.GetPosition()
        keepout(board, f'S8_{ref}_{num}', layers, pcbnew.ToMM(c.x), pcbnew.ToMM(c.y), S8_R)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    assert pcbnew.SaveBoard(str(board_path), board, True), 'save failed'
    print(f'r12_route: {len(tracks)} tracks, {len(vias)} vias, {len(board.Zones())} zones and rule areas, '
          f'{len(S8_KEEPOUT)} S-8 keep-outs')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--board', type=Path, default=BOARD)
    ap.add_argument('--routes', type=Path, default=ROUTES)
    a = ap.parse_args()
    build(a.board, a.routes)


if __name__ == '__main__':
    main()
