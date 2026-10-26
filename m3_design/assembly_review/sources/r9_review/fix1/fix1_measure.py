#!/usr/bin/env python3
"""R9 review pass 1, fix pass 1: the measurements the fix pass's records quote that no gate report carries.

usage: <KiCad python3> -I fix1_measure.py BOARD.kicad_pcb OUT.json        (read-only on BOARD; it must carry its fills)

Sections of OUT.json (board_sha256 names the board; every distance mm, edge to edge unless noted):
  module_gnd_pins  the RF modules' GND pins (U31.2 / .7 / .16, U30.1 / .10 / .12): through-copper distance on F.Cu from
                   the pad to the nearest GND via or plated GND hole (route_check's raster, 0.05 mm; R7 pass 3 3.6's
                   metric, R9P1-RF-01)
  via_openings     every via ring against every SMD pad's solder-mask opening and paste aperture on the via's outer
                   layers: the own-net pairs closer than JLC's 0.10 mm mask web, the worst three, the nearest foreign
                   pair; via holes against openings (REQUIREMENTS M2's 0.1 mm) (R9P1-DFM-04)
  gate_pads_to_gnd the bare pyro-gate and actuator-gate pads against the GND zone fills of their layer (R9P1-PYRO-02,
                   R9P1-DFM-02)
  single_vias      every via of a power-class net (route_check) whose removal leaves a pad of its net unconnected
                   (the via moved off the board in memory, KiCad connectivity rebuilt, the moved via itself not
                   counted, nothing saved): the single-via links (R9P1-POWER-03)
  hardware         non-GND copper (tracks, vias, fills) within the top washer (F.Cu, r 3.5) and the bottom standoff
                   (B.Cu, r 3.2) of each M3 hole, from the hole centre; the nearest pad on each face (R9P1-MECHANICAL-04)
  thin_gnd         outer GND fill pieces narrower than 0.75 / 1.0 mm (route_check.thin_pieces: length >= 2 mm, area
                   >= 0.15 mm2) per layer (R8 C15's method, R9P1-PLANES-03)
  tp_vias          vias whose hole meets a test pad's opening (scorecard Z4, R9P1-REQUIREMENTS-02)
  gnd_reach        through-copper reach on the ground aid's raster (r9_ground_aid.reach_maps, 0.1 mm, forward of the
                   strip; the strip is R-7's): every outer GND copper point's p95 / max per layer, every GND SMD pad of a
                   C / U / D / Q / R / L / Y / J part (the ten farthest), the clusters beyond 8 mm (R9P1-PLANES-01..03)
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import pcbnew

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'm3_design'))
import check_r8 as C8                                           # noqa: E402
import route_check as rc                                        # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
F, B = pcbnew.F_Cu, pcbnew.B_Cu
OUTER = ((F, pcbnew.F_Mask, pcbnew.F_Paste), (B, pcbnew.B_Mask, pcbnew.B_Paste))
MODULE_GND = ('U31.2', 'U31.7', 'U31.16', 'U30.1', 'U30.10', 'U30.12')
GATE_PADS = ('R126.1', 'R126.2', 'R127.1', 'R128.1', 'C126.1', 'Q124.4', 'C120.2', 'R121.1', 'Q121.4', 'Q122.3',
             'R121.2', 'R120.2', 'Q120.4', 'TP121.1', 'TP122.1')
HOLES = ((4, 4), (42, 4), (4, 98), (42, 98), (42, 59.5))


def r3(v):
    return None if v is None else round(v, 3)


def xy(p):
    return (round(mm(p.x), 4), round(mm(p.y), 4))


def pads(b):
    return {f'{f.GetReference()}.{p.GetNumber()}': p for f in b.GetFootprints() for p in f.Pads() if p.GetNumber()}


def poly(item, lid, grow=0):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, lid, grow, MM(0.001), pcbnew.ERROR_OUTSIDE)
    return ps


def module_gnd_pins(b):
    out = {}
    P = pads(b)
    r = None
    for name in MODULE_GND:
        p = P[name]
        c = (mm(p.GetPosition().x), mm(p.GetPosition().y))
        win = (c[0] - 6, c[1] - 6, c[0] + 6, c[1] + 6)
        cop, stitch = rc.net_copper(b, 'GND', F)
        r = rc.Raster(tuple(v / rc.NM for v in win), rc.RASTER / rc.NM)
        copper = r.fill(cop)
        d = rc.reach(r, copper, r.fill(stitch), 12.0)
        cells = r.fill([poly(p, F)])
        vals = [d[k] for k in range(r.nx * r.ny) if cells[k] and copper[k] and d[k] >= 0]
        out[name] = r3(min(vals)) if vals else None
    return out


def via_openings(b):
    vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    own_mask, own_paste, foreign, holes = [], [], None, None
    allp = [(k, p) for k, p in pads(b).items() if p.GetAttribute() in (pcbnew.PAD_ATTRIB_SMD, pcbnew.PAD_ATTRIB_CONN)]
    for v in vias:
        c = v.GetPosition()
        for cu, mk, pa in OUTER:
            ring = pcbnew.SHAPE_CIRCLE(c, v.GetWidth(cu) // 2)
            hole = pcbnew.SHAPE_CIRCLE(c, v.GetDrillValue() // 2)
            for k, p in allp:
                if not p.IsOnLayer(cu):
                    continue
                if abs(p.GetPosition().x - c.x) > MM(4) or abs(p.GetPosition().y - c.y) > MM(4):
                    continue
                if p.IsOnLayer(mk):
                    op = poly(p, cu, max(0, p.GetSolderMaskExpansion(mk)))
                    g = C8.min_gap(op, ring, 0.3)
                    gh = C8.min_gap(op, hole, 0.3)
                    if gh is not None and (holes is None or gh < holes[0]):
                        holes = (gh, k, xy(c))
                    if g is not None:
                        row = dict(mm=r3(g), via=xy(c), net=v.GetNetname(), pad=k, pad_net=p.GetNetname())
                        if p.GetNetname() == v.GetNetname():
                            if g < 0.1 - 1e-9:
                                own_mask.append(row)
                        elif foreign is None or g < foreign['mm']:
                            foreign = row
    for name, cu, pp in C8.paste_polys(b):            # paste apertures as check_r8.via_paste builds them
        box = pp.BBox()
        for v in vias:
            c = v.GetPosition()
            if (abs(c.x - box.Centre().x) > box.GetWidth() // 2 + MM(1.0) or
                    abs(c.y - box.Centre().y) > box.GetHeight() // 2 + MM(1.0)) or not v.IsOnLayer(cu):
                continue
            g = C8.min_gap(pcbnew.SHAPE_CIRCLE(c, v.GetWidth(cu) // 2), pp, 0.3)
            if g is not None and g < 0.1 - 1e-9:
                own_paste.append(dict(mm=r3(g), via=xy(c), net=v.GetNetname(), paste=name))
    own_mask.sort(key=lambda d: (d['mm'], d['via'], d['pad']))
    own_paste.sort(key=lambda d: (d['mm'], d['via'], d['paste']))
    return dict(own_mask_pairs_under_0p1=len(own_mask), own_mask_vias=len({tuple(d['via']) for d in own_mask}),
                own_mask_worst=own_mask[:6], own_paste_pairs_under_0p1=len(own_paste),
                own_paste_vias=len({tuple(d['via']) for d in own_paste}), own_paste_worst=own_paste[:4],
                foreign_ring_to_opening=foreign,
                hole_to_opening_min=None if holes is None else dict(mm=r3(holes[0]), pad=holes[1], via=holes[2]))


def gate_pads_to_gnd(b):
    P = pads(b)
    out = {}
    fills = {}
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != 'GND':
            continue
        for lid in (F, B):
            if z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                fills.setdefault(lid, pcbnew.SHAPE_POLY_SET()).BooleanAdd(
                    pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(lid)))
    for name in GATE_PADS:
        p = P.get(name)
        if p is None:
            continue
        lid = F if p.IsOnLayer(F) else B
        g = C8.min_gap(fills[lid], p.GetEffectiveShape(lid), 3.0) if lid in fills else None
        out[name] = dict(net=p.GetNetname(), layer=b.GetLayerName(lid), gnd_fill_mm=r3(g))
    return out


def single_vias(b):
    vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() and t.GetNetname() != 'GND'
            and rc.net_class(t.GetNetname()) == 'power']
    b.BuildConnectivity()
    base = b.GetConnectivity().GetUnconnectedCount(True)
    out = []
    for v in vias:
        pos = v.GetPosition()
        v.SetPosition(pcbnew.VECTOR2I(pos.x + MM(300), pos.y + MM(300)))
        b.BuildConnectivity()
        n = b.GetConnectivity().GetUnconnectedCount(True)
        v.SetPosition(pos)
        if n > base + 1:                            # the moved via itself is one unconnected item
            out.append(dict(net=v.GetNetname(), at=xy(pos), size=[r3(mm(v.GetWidth(F))), r3(mm(v.GetDrillValue()))],
                            unconnected=n - base - 1))
    b.BuildConnectivity()
    return dict(power_vias=len(vias), single=sorted(out, key=lambda d: (d['net'], d['at'])))


def hardware(b):
    out = {}
    P = pads(b)
    for hx, hy in HOLES:
        c = pcbnew.VECTOR2I(MM(hx), MM(hy))
        row = dict(F=[], B=[], nearest_pad={})
        for lid, rad, name in ((F, 3.5, 'F'), (B, 3.2, 'B')):
            disc = pcbnew.SHAPE_CIRCLE(c, MM(rad))
            seen = {}
            for t in b.GetTracks():
                n = t.GetNetname()
                if n == 'GND' or not t.IsOnLayer(lid):
                    continue
                s = t.GetEffectiveShape(lid)
                if pcbnew.SHAPE.Collide(disc, s, 0):
                    g = C8.min_gap(pcbnew.SHAPE_CIRCLE(c, 1), s, 10.0)
                    d = None if g is None else g + 0.000001
                    if d is not None and (n not in seen or d < seen[n]):
                        seen[n] = d
            for z in b.Zones():
                n = z.GetNetname()
                if z.GetIsRuleArea() or n == 'GND' or not (z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid)):
                    continue
                f = z.GetFilledPolysList(lid)
                if f.Collide(c, MM(rad)):
                    seen[n + ' (fill)'] = mm(int(f.SquaredDistance(c) ** 0.5))
            row[name] = [dict(net=n, from_centre_mm=r3(d)) for n, d in sorted(seen.items(), key=lambda kv: kv[1])]
            best = None
            for k, p in P.items():
                if not p.IsOnLayer(lid) or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    continue
                g = C8.min_gap(pcbnew.SHAPE_CIRCLE(c, 1), p.GetEffectiveShape(lid), 12.0)
                if g is not None and (best is None or g < best[0]):
                    best = (g, k)
            row['nearest_pad'][name] = None if best is None else dict(pad=best[1], from_centre_mm=r3(best[0]))
        out[f'{hx},{hy}'] = row
    return out


def thin_gnd(b):
    out = {}
    for lid, name in ((F, 'F'), (B, 'B')):
        fill = pcbnew.SHAPE_POLY_SET()
        for z in b.Zones():
            if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                fill.BooleanAdd(pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(lid)))
        for w in (0.75, 1.0):
            pieces = [pc for pc in rc.thin_pieces(fill, MM(w / 2)) if pc[2] >= 2.0 and pc[3] >= 0.15]
            out[f'{name} {w}'] = len(pieces)
    return out


def tp_vias(b):
    vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    out = []
    for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        if not re.match(r'^TP\d+$', f.GetReference()):
            continue
        for p in f.Pads():
            for lid, mk in ((F, pcbnew.F_Mask), (B, pcbnew.B_Mask)):
                if not p.IsOnLayer(lid):
                    continue
                op = poly(p, lid, max(0, p.GetSolderMaskExpansion(mk)))
                for v in vias:
                    if op.Collide(pcbnew.SHAPE_CIRCLE(v.GetPosition(), v.GetDrillValue() // 2), 0):
                        out.append(dict(pad=f'{f.GetReference()}.{p.GetNumber()}', via=xy(v.GetPosition())))
    return out


def gnd_reach(b):
    import r9_ground_aid as A
    maps = A.reach_maps(b)
    out = dict(raster_mm=A.COPPER_RASTER, copper={}, pads=None, worst_pads=[], clusters_over_8mm=[])
    for lid, name in ((F, 'F'), (B, 'B')):
        r, copper, d = maps[lid]
        vals = sorted(d[k] for k in range(r.nx * r.ny) if copper[k] and d[k] >= 0)
        out['copper'][name] = dict(points=len(vals), p95=r3(vals[int(0.95 * (len(vals) - 1))]), max=r3(vals[-1]))
        for dk, k, cells in A.over_clusters(r, copper, d):
            out['clusters_over_8mm'].append(dict(layer=name, at=[r3(mm(v)) for v in r.centre(k)], mm=r3(dk),
                                                 cells=len(cells)))
    rows = []
    for f in b.GetFootprints():
        ref = f.GetReference()
        if not re.match(r'^(C|U|D|Q|R|L|Y|J)\d+$', ref):
            continue
        for p in f.Pads():
            if p.GetNetname() != 'GND' or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or mm(p.GetPosition().y) < A.STRIP_Y:
                continue
            lid = F if p.IsOnLayer(F) else B
            rows.append((A.pad_reach(maps, p, lid), f'{ref}.{p.GetNumber()}'))
    rows.sort(key=lambda t: (-(t[0] if t[0] is not None else 99.0), t[1]))
    out['pads'] = len(rows)
    out['worst_pads'] = [dict(pad=n, mm=r3(v)) for v, n in rows[:10]]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', type=Path)
    ap.add_argument('out', type=Path)
    a = ap.parse_args()
    path = a.board.resolve()
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    b = pcbnew.LoadBoard(str(path))
    rep = dict(board_sha256=sha, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    for name, fn in (('module_gnd_pins', module_gnd_pins), ('via_openings', via_openings),
                     ('gate_pads_to_gnd', gate_pads_to_gnd), ('hardware', hardware), ('thin_gnd', thin_gnd),
                     ('tp_vias', tp_vias), ('gnd_reach', gnd_reach), ('single_vias', single_vias)):
        rep[name] = fn(b)
        print(name, json.dumps(rep[name])[:600])
    a.out.write_text(json.dumps(rep, indent=1) + '\n')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == sha, 'board changed during the measurement'
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
