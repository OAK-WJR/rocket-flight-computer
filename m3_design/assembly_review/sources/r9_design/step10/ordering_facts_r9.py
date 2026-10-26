#!/usr/bin/env python3
"""R9 step 10: the board facts docs/ORDERING.md quotes (assembly counts, edges, probe and coat points, staking, the
stall-test windows, the sled), measured on one board and bound to its SHA-256 (R9_DECISIONS D-S10-06).

usage: <KiCad python3> -I ordering_facts_r9.py BOARD.kicad_pcb OUT.json [--dc RAW.txt BAT.txt FET.txt]

Read-only. Distances are copper / courtyard geometry (tools/check_r8.py min_gap on KiCad's effective shapes), in mm, in
KiCad board coordinates (y = 0 the aft edge, Gerber Y = -y). --dc takes tools/run_dc.sh's three 0.05 mm outputs of the
same board (checked by SHA) and places each 7.7 A neck's cut box against the FETs and J122.
"""
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import check_r8 as C8  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
JACK_FP = 'M3_SMA_KH_KE8_EDGE'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def xy(v):
    return [round(mm(v.x), 3), round(mm(v.y), 3)]


def cy(f):
    return C8.courtyard(f)


def box(shape):
    b = shape.BBox()
    return [round(mm(b.GetLeft()), 2), round(mm(b.GetTop()), 2), round(mm(b.GetRight()), 2), round(mm(b.GetBottom()), 2)]


def boxes_touch(a, b):
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def face(f):
    return 'B' if f.IsFlipped() else 'F'


def kind(f):
    ref = f.GetReference()
    if ref.startswith('TP'):
        return 'test pad'
    if str(f.GetFPID().GetLibItemName()) == JACK_FP:
        return 'jack'
    if any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in f.Pads()):
        return 'tht'
    return 'smd'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--dc', nargs=3, type=Path)
    a = ap.parse_args()
    path = a.board.resolve()
    b = pcbnew.LoadBoard(str(path))
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    W = 46.0
    out = dict(board=path.name, board_sha256=sha(path), script_sha256=sha(__file__))

    # assembly counts (DNP: the five unfitted lands carry the DNP attribute)
    counts = {}
    for f in fps.values():
        dnp = bool(f.IsDNP())
        k = 'dnp' if dnp else kind(f)
        counts.setdefault(face(f), {}).setdefault(k, []).append(f.GetReference())
    out['assembly'] = {fc: {k: dict(n=len(v), refs=sorted(v)) for k, v in d.items()} for fc, d in counts.items()}

    # edge distances (rail removal): every pad and courtyard within 1.6 mm of the long edges, per footprint
    edges = {}
    for f in fps.values():
        c = box(cy(f))
        for name, d_c in (('west', c[0]), ('east', W - c[2])):
            pads = []
            for p in f.Pads():
                pb = p.GetBoundingBox()
                d = mm(pb.GetLeft()) if name == 'west' else W - mm(pb.GetRight())
                kindp = 'npth' if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else 'pad'
                pads.append((round(d, 3), kindp, p.GetNumber()))
            near = min(pads) if pads else None
            if (near and near[0] < 1.6) or d_c < 1.0:
                edges.setdefault(name, []).append(dict(ref=f.GetReference(), face=face(f), courtyard_mm=round(d_c, 3),
                                                       nearest_pad=dict(mm=near[0], kind=near[1], pad=near[2]),
                                                       nearest_contact=min(((d, n) for d, k, n in pads if k == 'pad'),
                                                                           default=None),
                                                       y=round(mm(f.GetPosition().y), 2)))
    for k in edges:
        edges[k].sort(key=lambda r: r['nearest_pad']['mm'])
    out['edges'] = edges

    # J3: its slots and the nearest bottom part to each THT leg (the hand-finish iron caution)
    j3 = fps['J3']
    legs = []
    for p in j3.Pads():
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
            continue
        best = None
        for f in fps.values():
            if not f.IsFlipped():
                continue
            g = C8.min_gap(p.GetEffectiveShape(pcbnew.B_Cu), cy(f), 5.0)
            if g is not None and (best is None or g < best[0]):
                best = (round(g, 3), f.GetReference())
        legs.append(dict(pad=p.GetNumber(), net=p.GetNetname(), at=xy(p.GetPosition()), nearest_bottom_part=best))
    out['j3_legs'] = legs

    # J2 (TC2030): pad map and every pad's gap to NRST's pad
    j2 = fps['J2']
    j2p = {p.GetNumber(): p for p in j2.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH}
    nrst = [p for p in j2p.values() if p.GetNetname() == 'NRST'][0]
    out['j2'] = dict(at=xy(j2.GetPosition()), face=face(j2),
                     pads={n: dict(net=p.GetNetname(), at=xy(p.GetPosition())) for n, p in sorted(j2p.items())},
                     nrst_pad=nrst.GetNumber(),
                     nrst_gaps={n: round(C8.min_gap(nrst.GetEffectiveShape(pcbnew.F_Cu),
                                                    p.GetEffectiveShape(pcbnew.F_Cu), 5.0) or -1, 3)
                                for n, p in sorted(j2p.items()) if p is not nrst})

    # PYRO_BLOCK contents by face (courtyard touching the area's outline polygon)
    blk = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'PYRO_BLOCK'][0]
    poly = pcbnew.SHAPE_POLY_SET(blk.Outline())
    inside = {'F': [], 'B': []}
    for r, f in fps.items():
        c = cy(f)
        if poly.Collide(c) or poly.Contains(f.GetPosition()):
            inside[face(f)].append(r)
    out['pyro_block'] = dict(bbox=box(blk.Outline()), parts={k: sorted(v) for k, v in inside.items()})

    # parts by name: positions, faces, rotations
    want = ['C24', 'C15', 'C83', 'C84', 'C88', 'C121', 'C150', 'D30', 'D31', 'J1', 'J9', 'J121', 'J122', 'J123', 'J124',
            'L1', 'Q120', 'Q121', 'Q124', 'R134', 'R166', 'R311', 'R312', 'TP80', 'TP122', 'U4', 'U5', 'U9', 'U30',
            'U31', 'LS120', 'J30', 'J31', 'J2', 'J3']
    out['parts'] = {r: dict(face=face(fps[r]), at=xy(fps[r].GetPosition()), rot=round(fps[r].GetOrientationDegrees(), 1),
                            courtyard=box(cy(fps[r])), value=fps[r].GetValue()) for r in want}
    out['pins'] = {f'{r}.{p.GetNumber()}': dict(net=p.GetNetname(), at=xy(p.GetPosition()))
                   for r in ('J1', 'J121', 'J124', 'C24', 'U9', 'C88', 'R311', 'R312') for p in fps[r].Pads()}

    # staking: bottom parts under C84 / C121, MEMS within 3 mm of U4 / U5
    out['under'] = {r: sorted(o for o, f in fps.items() if f.IsFlipped() and boxes_touch(box(cy(fps[r])), box(cy(f))))
                    for r in ('C84', 'C121', 'J1', 'J121', 'J124', 'J122', 'J123')}
    for r in ('U4', 'U5'):
        c = box(cy(fps[r]))
        grown = [c[0] - 3, c[1] - 3, c[2] + 3, c[3] + 3]
        out['under'][f'{r}_3mm'] = sorted(o for o, f in fps.items() if o != r and boxes_touch(grown, box(cy(f))))

    # U9: its IN pins and their distance to J1.1; the capacitor on U9's IN pin
    u9 = fps['U9']
    j11 = fps['J1'].FindPadByNumber('1')
    ins = [p for p in u9.Pads() if p.GetNetname() == 'BAT_IN']
    caps = []
    for f in fps.values():
        if not f.GetReference().startswith('C'):
            continue
        for p in f.Pads():
            if p.GetNetname() == 'BAT_IN':
                d = min(math.dist(xy(p.GetPosition()), xy(q.GetPosition())) for q in ins)
                caps.append((round(d, 3), f.GetReference(), face(f)))
    caps.sort()
    out['u9'] = dict(at=xy(u9.GetPosition()), face=face(u9), in_pins=[q.GetNumber() for q in ins],
                     j1_1_to_in_mm=round(min(math.dist(xy(j11.GetPosition()), xy(q.GetPosition())) for q in ins), 3),
                     bat_in_caps_by_distance=caps[:4])

    # bottom power pours (sled: non-conductive under the bottom face) and their boxes
    pours = {}
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(pcbnew.B_Cu) or not z.HasFilledPolysForLayer(pcbnew.B_Cu):
            continue
        if z.GetNetname() in ('GND',):
            continue
        polys = z.GetFilledPolysList(pcbnew.B_Cu)
        pours.setdefault(z.GetNetname(), []).append(
            [box(pcbnew.SHAPE_POLY_SET(polys.Outline(i))) for i in range(polys.OutlineCount())])
    out['bottom_pours'] = pours

    # J30 / J31 centre pads to D30 / D31
    rf = {}
    for j, d in (('J30', 'D30'), ('J31', 'D31')):
        centre = [p for p in fps[j].Pads() if p.GetNetname() not in ('GND', '')]
        best = None
        for p in centre:
            for q in fps[d].Pads():
                g = C8.min_gap(p.GetEffectiveShape(pcbnew.F_Cu), q.GetEffectiveShape(pcbnew.F_Cu), 5.0)
                if g is not None and (best is None or g < best[0]):
                    best = (round(g, 3), f'{j}.{p.GetNumber()}', f'{d}.{q.GetNumber()}')
        rf[j] = best
    out['jack_to_esd'] = rf

    # vias whose hole reaches into a bare contact (test pads, J2): ORDERING's via-covering exception list
    vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    bare = []
    for r, f in fps.items():
        if not (r.startswith('TP') or r == 'J2'):
            continue
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            lay = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
            for v in vias:
                hole = pcbnew.SHAPE_CIRCLE(v.GetPosition(), v.GetDrillValue() // 2)
                if p.GetEffectiveShape(lay).Collide(hole, 0):
                    bare.append(dict(pad=f'{r}.{p.GetNumber()}', via=xy(v.GetPosition()), net=v.GetNetname()))
    out['vias_in_bare_contacts'] = bare
    sizes = {}
    for v in vias:
        k = f'{mm(v.GetWidth(pcbnew.F_Cu)):.2f}/{mm(v.GetDrillValue()):.2f}'
        sizes[k] = sizes.get(k, 0) + 1
    out['via_sizes_pad_drill'] = dict(sorted(sizes.items()))

    # In2 regions (filled area per net) and DNP lands
    in2 = {}
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(pcbnew.In2_Cu) or not z.HasFilledPolysForLayer(pcbnew.In2_Cu):
            continue
        polys = z.GetFilledPolysList(pcbnew.In2_Cu)
        in2.setdefault(z.GetNetname(), []).append(dict(zone=z.GetZoneName(), pieces=polys.OutlineCount(),
                                                       area_mm2=round(polys.Area() / 1e12, 1)))
    out['in2_regions'] = in2
    out['dnp'] = {r: dict(face=face(f), at=xy(f.GetPosition())) for r, f in sorted(fps.items()) if f.IsDNP()}

    # through-hole pads: effective zone connection on each layer with a fill of their net, and the nearest bottom part
    names = {0: 'none', 1: 'thermal', 2: 'solid', 3: 'tht_thermal'}
    tht = {}
    for r, f in fps.items():
        pth = [p for p in f.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
        if not pth:
            continue
        rows = {}
        for p in pth:
            net = p.GetNetname()
            conn = {}
            for z in b.Zones():
                if z.GetIsRuleArea() or z.GetNetname() != net or not net:
                    continue
                for lay in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
                    if not z.IsOnLayer(lay) or not z.HasFilledPolysForLayer(lay):
                        continue
                    if not z.GetFilledPolysList(lay).Collide(p.GetEffectiveShape(lay), 0):
                        continue
                    mode = int(p.GetLocalZoneConnection())
                    if mode < 0:
                        mode = int(f.GetLocalZoneConnection())
                    if mode < 0:
                        mode = int(z.GetPadConnection())
                    conn[b.GetLayerName(lay)] = names.get(mode, str(mode))
            near = None
            for g in fps.values():
                if not g.IsFlipped() or g.GetReference() == r:
                    continue
                d = C8.min_gap(p.GetEffectiveShape(pcbnew.B_Cu), cy(g), 5.0)
                if d is not None and (near is None or d < near[0]):
                    near = (round(d, 3), g.GetReference())
            rows[p.GetNumber()] = dict(net=net, zone_connection=conn, nearest_bottom_part=near)
        tht[r] = rows
    out['tht_pads'] = tht

    # the 7.7 A necks' cut boxes against the FETs and J122
    if a.dc:
        necks = {}
        for name, f in zip(('RAW_ACT', 'BAT_IN', 'ACT_FET_S'), a.dc):
            text = f.read_text()
            if out['board_sha256'] not in text.splitlines()[0]:
                raise SystemExit(f'{f} is not of this board')
            m = re.search(r'cuts: neck ([0-9.]+) mm at level [0-9.]+ on (\S+) .*cut box \(([^)]*)\)', text)
            x0, x1, y0, y1 = (float(v) for v in m.group(3).split(','))
            nb = [x0, y0, x1, y1]
            near = {}
            for r in ('Q120', 'Q121', 'J122', 'J1', 'C121'):
                c = box(cy(fps[r]))
                dx = max(c[0] - nb[2], nb[0] - c[2], 0)
                dy = max(c[1] - nb[3], nb[1] - c[3], 0)
                near[r] = round(math.hypot(dx, dy), 2)
            rise = re.search(r'rises ([0-9.]+) C', text).group(1)
            necks[name] = dict(neck_mm=float(m.group(1)), layer=m.group(2), cut_box=nb, rise_c=float(rise),
                               box_to_courtyard_mm=near)
        out['necks'] = necks
    a.out.write_text(json.dumps(out, indent=1) + '\n')
    print('ordering facts written for', out['board_sha256'][:12])


if __name__ == '__main__':
    main()
