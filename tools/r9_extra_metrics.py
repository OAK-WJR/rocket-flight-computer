#!/usr/bin/env python3
"""R9 clean-sheet scorecard rows (X-rows) that the R8 survey (tools/survey_metrics.py) does not measure.

usage: <KiCad python3> -I r9_extra_metrics.py BOARD.kicad_pcb [--tools REPO/tools] [--json OUT.json]

Read-only on BOARD (must carry saved zone fills). Reuses the repo's own definitions so the numbers agree with the
gate: check_r8 (net_items, min_gap, courtyard, RF_PART via check_r7, CH1_PARTS, rf_separation, inner_power_pyro,
battery_pyro), route_check (net classes, collect) and survey_metrics (bends_of). Assumes the R7/R8 schematic
designators (a clean-sheet re-layout of the same schematic keeps them).

Rows (lengths mm, areas mm^2; lower is better unless noted):
  X1   board outline length (y extent), width, area; envelope length incl. parts beyond the outline (the SMA
       overhang); aft overhang
  X2   pyro: armed-live copper = PYRO1_BUS / PYRO1_IGN / PYRO1_OUT (bus, igniter, drain). Own nets = PYRO*, ARM*,
       GND, RAW_ACT (the ARM break's source side). Foreign nets = every other net with copper within 3 mm of
       armed-live copper, (a) on the same copper layer (step9/pyro_neighbours.py's method) and (b) in plan view on
       any layer. Also the nearest foreign copper (same layer), the CH1 block bounding box (union of CH1_PARTS
       courtyards) and its fill, and the foreign nets whose tracks or vias pass through that box ("through traffic")
  X3   RF strip: bounding box of every RF part courtyard (check_r7.RF_PART) clipped to the outline: depth from the
       aft edge, area and share of the outline; non-RF parts whose courtyard enters that box; rf / rfif track length
  X4   placement density: parts per side, parts per cm^2, courtyard sum (both sides) / outline area, distinct
       rotations, parts off a multiple of 90 degrees
  X5   distinct track widths (all, signal, power, GND), distinct via geometries (pad dia / drill)
  X6   bends per mm (signal; all nets), mean segment length
  X7   vias: total, GND, non-GND
  X8   zones: copper zone count (non rule-area), rule areas
  X9   margins of the rule-based safety checks: F10 RF separation (nearest restricted part / fast line, >= 5 mm),
       inner power to pyro (>= 2.5 mm plan), battery-live to ARM side (>= 1.0 mm same layer)
  Z4   vias inside test pads: every via whose hole meets the mask opening of a TP* pad (the bare contacts of M2), on
       every test pad (R9 review pass 1, R9P1-REQUIREMENTS-02: the R8 survey's A8 row looked at TP122 only)
"""
import argparse
import importlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import pcbnew

mm, MM = pcbnew.ToMM, pcbnew.FromMM
LIVE = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')
OWN = re.compile(r'^(PYRO|ARM|GND$|RAW_ACT$)')
BATTERY_LIVE = ('BAT_IN', 'ACT_FET_S')
REACH = 3.0


def r(v, n=2):
    return None if v is None else round(v, n)


def bbox_union(boxes):
    xs0, ys0, xs1, ys1 = zip(*boxes)
    return min(xs0), min(ys0), max(xs1), max(ys1)


def box_of(poly):
    bb = poly.BBox()
    return mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board')
    ap.add_argument('--tools', default=str(Path(__file__).resolve().parent))
    ap.add_argument('--json')
    a = ap.parse_args()
    sys.path.insert(0, str(Path(a.tools).resolve()))
    C8 = importlib.import_module('check_r8')
    C7 = importlib.import_module('check_r7')
    rc = importlib.import_module('route_check')
    sm = importlib.import_module('survey_metrics')
    b = pcbnew.LoadBoard(a.board)
    out = {}
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    # ---- X1 outline and envelope
    ps = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(ps, False)
    ox0, oy0, ox1, oy1 = box_of(ps)
    area = ps.Area() / 1e12
    yards = {ref: C8.courtyard(f) for ref, f in fps.items()}
    yb = {ref: box_of(p) for ref, p in yards.items() if p.OutlineCount()}
    ex = bbox_union(list(yb.values()) + [(ox0, oy0, ox1, oy1)])
    out['X1'] = dict(length=r(oy1 - oy0), width=r(ox1 - ox0), area=r(area, 1), envelope_length=r(ex[3] - ex[1]),
                     aft_overhang=r(oy0 - ex[1]), fwd_overhang=r(ex[3] - oy1),
                     side_overhang=r(max(ox0 - ex[0], ex[2] - ox1)))

    # ---- X2 pyro neighbourhood
    items = C8.net_items(b, lambda n: True)
    live = [it for it in items if it[1] in LIVE]
    same, plan = {}, {}
    for it in items:
        n = it[1]
        if not n or n in LIVE:
            continue
        ib = it[3].BBox()
        for lv in live:
            lb = lv[3].BBox()
            g0 = MM(REACH)
            if lb.GetRight() + g0 < ib.GetLeft() or ib.GetRight() + g0 < lb.GetLeft() or \
                    lb.GetBottom() + g0 < ib.GetTop() or ib.GetBottom() + g0 < lb.GetTop():
                continue
            if lv[2] == it[2]:
                if n in same and same[n][0] == 0:
                    continue
                g = C8.min_gap(lv[3], it[3], REACH)
                if g is not None and (n not in same or g < same[n][0]):
                    same[n] = (g, b.GetLayerName(it[2]), lv[0], it[0])
            if n not in plan or plan[n] > 0:
                g = C8.min_gap(lv[3], it[3], REACH)
                if g is not None and (n not in plan or g < plan[n]):
                    plan[n] = g
    foreign_same = {n: v for n, v in same.items() if not OWN.match(n)}
    foreign_plan = {n: v for n, v in plan.items() if not OWN.match(n)}
    nf = min(((v[0], n, v[1]) for n, v in foreign_same.items()), default=None)
    nb = min(((v[0], n, v[1]) for n, v in foreign_same.items() if n in BATTERY_LIVE), default=None)
    ch1 = [ref for ref in C8.CH1_PARTS if ref in yb]
    blk = bbox_union([yb[ref] for ref in ch1])
    blk_area = (blk[2] - blk[0]) * (blk[3] - blk[1])
    yard_sum = sum(yards[ref].Area() / 1e12 for ref in ch1)
    ch1_nets = {p.GetNetname() for ref in ch1 for p in fps[ref].Pads() if p.GetNetname()}
    through = Counter()
    for t in b.GetTracks():
        n = t.GetNetname()
        if not n or n in ch1_nets or n == 'GND':
            continue
        tb = t.GetBoundingBox()
        if overlap((mm(tb.GetLeft()), mm(tb.GetTop()), mm(tb.GetRight()), mm(tb.GetBottom())), blk):
            through[n] += 1
    out['X2'] = dict(
        foreign_nets_3mm_same_layer=len([n for n in foreign_same if not n.startswith('unconnected-')]),
        foreign_nets_3mm_plan=len([n for n in foreign_plan if not n.startswith('unconnected-')]),
        unconnected_pads_3mm=len([n for n in foreign_plan if n.startswith('unconnected-')]),
        foreign_same_layer={n: dict(mm=v[0], layer=v[1], live=v[2], other=v[3])
                            for n, v in sorted(foreign_same.items(), key=lambda kv: kv[1][0])},
        foreign_plan={n: v for n, v in sorted(foreign_plan.items(), key=lambda kv: kv[1])},
        own_nets_3mm_same_layer=sorted(n for n in same if OWN.match(n)),
        nearest_foreign_same_layer=nf, nearest_battery_live_same_layer=nb,
        ch1_parts=len(ch1), ch1_bbox=[r(v) for v in blk], ch1_bbox_area=r(blk_area, 1),
        ch1_courtyard_fill=r(yard_sum / blk_area, 3),
        through_nets=len(through), through_items=sum(through.values()), through=dict(sorted(through.items())))

    # ---- X3 RF strip: check_r8.STRIP_PARTS (jacks, modules, RF-line parts, limiter) and RF_NETS copper define the
    # strip; every RF_PART (adds module decoupling, interface resistors, test pad) defines the wider RF zone
    rf = [ref for ref in yb if C7.RF_PART.fullmatch(ref)]
    core = [yb[ref] for ref in C8.STRIP_PARTS if ref in yb]
    core += [box_of(it[3]) for it in C8.net_items(b, lambda n: n in C8.RF_NETS)]
    sb = bbox_union(core)
    sbc = (max(sb[0], ox0), max(sb[1], oy0), min(sb[2], ox1), min(sb[3], oy1))
    s_area = (sbc[2] - sbc[0]) * (sbc[3] - sbc[1])
    intr = sorted(ref for ref, bx in yb.items() if ref not in rf and overlap(bx, sbc))
    zb = bbox_union([yb[ref] for ref in rf])
    zbc = (max(zb[0], ox0), max(zb[1], oy0), min(zb[2], ox1), min(zb[3], oy1))
    tracks_cls = Counter()
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_TRACK':
            tracks_cls[rc.net_class(t.GetNetname()) or 'other'] += mm(t.GetLength())
    out['X3'] = dict(rf_parts=len(rf), strip_bbox=[r(v) for v in sbc], depth_from_aft=r(sbc[3] - oy0),
                     area=r(s_area, 1), share=r(s_area / area, 3),
                     rf_zone_bbox=[r(v) for v in zbc], rf_zone_depth=r(zbc[3] - oy0),
                     rf_zone_area=r((zbc[2] - zbc[0]) * (zbc[3] - zbc[1]), 1), non_rf_parts_in_strip=len(intr),
                     non_rf_in_strip=intr, rf_track_mm=r(tracks_cls['rf'], 1), rfif_track_mm=r(tracks_cls['rfif'], 1))

    # ---- X4 density
    top = [f for f in fps.values() if not f.IsFlipped()]
    bot = [f for f in fps.values() if f.IsFlipped()]
    ysum = sum(p.Area() / 1e12 for p in yards.values() if p.OutlineCount())
    rots = Counter(round(f.GetOrientationDegrees() % 360, 3) for f in fps.values())
    out['X4'] = dict(parts=len(fps), top=len(top), bottom=len(bot), parts_per_cm2=r(len(fps) / (area / 100), 2),
                     courtyard_sum=r(ysum, 1), courtyard_per_outline=r(ysum / area, 3),
                     courtyard_per_outline_outside_rf=r(sum(yards[x].Area() / 1e12 for x in yb if x not in rf) /
                                                        (area - s_area), 3),
                     distinct_rotations=len(rots), off_90=sum(v for k, v in rots.items() if k % 90),
                     rotations={str(k): v for k, v in sorted(rots.items())})

    # ---- X5 widths, X7 vias
    w_all, w_cls = Counter(), {'signal': Counter(), 'power': Counter(), 'gnd': Counter()}
    vgeo, nvia, ngnd = Counter(), 0, 0
    for t in b.GetTracks():
        n = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            nvia += 1
            ngnd += n == 'GND'
            vgeo[(round(mm(t.GetWidth(pcbnew.F_Cu)), 3), round(mm(t.GetDrillValue()), 3))] += 1
            continue
        w = round(mm(t.GetWidth()), 3)
        L = mm(t.GetLength())
        w_all[w] += L
        c = 'gnd' if n == 'GND' else ('power' if rc.net_class(n) == 'power' else 'signal')
        w_cls[c][w] += L
    out['X5'] = dict(track_widths=len(w_all), signal_widths=len(w_cls['signal']), power_widths=len(w_cls['power']),
                     gnd_widths=len(w_cls['gnd']), via_geometries=len(vgeo),
                     widths_mm={c: {str(k): r(v, 1) for k, v in sorted(d.items())} for c, d in w_cls.items()},
                     via_geometry_counts={f'{k[0]}/{k[1]}': v for k, v in sorted(vgeo.items())})
    out['X7'] = dict(vias=nvia, gnd_vias=ngnd, non_gnd_vias=nvia - ngnd)

    # ---- X6 bends
    sv = sm.Survey(b, rc, 0.05)
    bends_sig = bends_all = 0
    L_sig = L_all = 0.0
    nseg = 0
    for net, nc in sv.nc.items():
        k = sum(1 for lay, ch, p in sv.bends_of(nc) if sv.bend_kind(ch) in ('b45', 'b90', 'acute', 'other'))
        L = sum(math.dist(t['a'], t['b']) / 1e6 for t in nc.tracks)
        nseg += len(nc.tracks)
        bends_all += k
        L_all += L
        if sv.signal(net):
            bends_sig += k
            L_sig += L
    out['X6'] = dict(signal_bends=bends_sig, signal_bends_per_mm=r(bends_sig / L_sig, 4) if L_sig else None,
                     all_bends=bends_all, all_bends_per_mm=r(bends_all / L_all, 4) if L_all else None,
                     mean_segment_mm=r(L_all / nseg, 3) if nseg else None)

    # ---- Z4 vias inside test pads (every TP*)
    z4 = []
    vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        if not re.match(r'^TP\d+$', f.GetReference()):
            continue
        for p in f.Pads():
            for lid in (pcbnew.F_Cu, pcbnew.B_Cu):
                if not p.IsOnLayer(lid):
                    continue
                opening = pcbnew.SHAPE_POLY_SET()
                p.TransformShapeToPolygon(opening, lid, max(0, p.GetSolderMaskExpansion(lid)), MM(0.001),
                                          pcbnew.ERROR_OUTSIDE)
                for v in vias:
                    hole = pcbnew.SHAPE_CIRCLE(v.GetPosition(), v.GetDrillValue() // 2)
                    if opening.Collide(hole, 0):
                        z4.append(dict(pad=f'{f.GetReference()}.{p.GetNumber()}', net=v.GetNetname(),
                                       at=[r(mm(v.GetPosition().x), 3), r(mm(v.GetPosition().y), 3)]))
    out['Z4'] = dict(vias=z4)

    # ---- X8 zones
    zs = list(b.Zones())
    out['X8'] = dict(copper_zones=sum(1 for z in zs if not z.GetIsRuleArea()),
                     rule_areas=sum(1 for z in zs if z.GetIsRuleArea()),
                     rule_area_names=sorted(z.GetZoneName() for z in zs if z.GetIsRuleArea()))

    # ---- X9 rule-based safety margins (designator-based checks of check_r8, reusable on any board of this netlist)
    _, ev = C8.rf_separation(b)
    _, ip = C8.inner_power_pyro(b)
    _, bp = C8.battery_pyro(b)
    out['X9'] = dict(rf_sep_nearest_part=ev['nearest_part'], rf_sep_nearest_line=ev['nearest_line'],
                     inner_power_pyro_nearest=ip['nearest'], battery_pyro_nearest=bp['nearest'])

    rows = dict(
        X1_board_length_mm=out['X1']['length'], X1b_board_width_mm=out['X1']['width'],
        X1c_outline_area_mm2=out['X1']['area'], X1d_envelope_length_mm=out['X1']['envelope_length'],
        X2_pyro_foreign_nets_3mm_same_layer=out['X2']['foreign_nets_3mm_same_layer'],
        X2b_pyro_foreign_nets_3mm_plan=out['X2']['foreign_nets_3mm_plan'],
        X2c_pyro_nearest_foreign_mm=nf[0] if nf else None,
        X2d_pyro_nearest_battery_live_mm=nb[0] if nb else None,
        X2e_ch1_bbox_area_mm2=out['X2']['ch1_bbox_area'], X2f_ch1_courtyard_fill=out['X2']['ch1_courtyard_fill'],
        X2g_ch1_through_nets=out['X2']['through_nets'],
        X3_rf_strip_depth_mm=out['X3']['depth_from_aft'], X3b_rf_strip_area_mm2=out['X3']['area'],
        X3c_rf_strip_share=out['X3']['share'], X3d_non_rf_parts_in_strip=out['X3']['non_rf_parts_in_strip'],
        X3g_rf_zone_depth_mm=out['X3']['rf_zone_depth'], X3h_rf_zone_area_mm2=out['X3']['rf_zone_area'],
        X3e_rf_track_mm=out['X3']['rf_track_mm'], X3f_rfif_track_mm=out['X3']['rfif_track_mm'],
        X4_parts=out['X4']['parts'], X4b_parts_per_cm2=out['X4']['parts_per_cm2'],
        X4c_courtyard_per_outline=out['X4']['courtyard_per_outline'],
        X4d_courtyard_per_outline_outside_rf=out['X4']['courtyard_per_outline_outside_rf'],
        X4e_distinct_rotations=out['X4']['distinct_rotations'], X4f_parts_off_90=out['X4']['off_90'],
        X5_track_widths=out['X5']['track_widths'], X5b_signal_track_widths=out['X5']['signal_widths'],
        X5c_power_track_widths=out['X5']['power_widths'], X5d_gnd_track_widths=out['X5']['gnd_widths'],
        X5e_via_geometries=out['X5']['via_geometries'],
        X6_signal_bends_per_mm=out['X6']['signal_bends_per_mm'], X6b_all_bends_per_mm=out['X6']['all_bends_per_mm'],
        X6c_mean_segment_mm=out['X6']['mean_segment_mm'],
        X7_vias_total=nvia, X7b_gnd_vias=ngnd, X7c_non_gnd_vias=nvia - ngnd,
        X8_copper_zones=out['X8']['copper_zones'], X8b_rule_areas=out['X8']['rule_areas'],
        X9_rf_sep_nearest_part_mm=ev['nearest_part'][0] if ev['nearest_part'] else None,
        X9b_rf_sep_nearest_fast_line_mm=ev['nearest_line'][0] if ev['nearest_line'] else None,
        X9c_inner_power_pyro_mm=ip['nearest'][0] if ip['nearest'] else None,
        X9d_battery_pyro_mm=bp['nearest'][0] if bp['nearest'] else None,
        Z4_vias_in_test_pads=len(z4),
        Z2r9_exit_net_track_mm=r(sum(mm(t.GetLength()) for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and
                                     t.GetNetname() in ('PYRO1_GATE_N', 'PYRO1_CONT', 'ARM1_SENSE')), 1))
    out['scorecard'] = rows
    out['meta'] = dict(board=str(Path(a.board).resolve()), tools=str(Path(a.tools).resolve()))
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1, default=str) + '\n')
    for k, v in rows.items():
        print(f'{k:42s} {v}')


if __name__ == '__main__':
    main()
