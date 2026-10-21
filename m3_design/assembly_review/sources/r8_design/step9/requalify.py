#!/usr/bin/env python3
"""R8 step 9: the placement-bound measurements a re-placement invalidates (survey_constraints section 13), on one board.

usage: <KiCad python3> requalify.py BOARD.kicad_pcb OUT.json        (run it on R8 and on R7 for the comparison)

Read-only. The board needs its project files (.kicad_pro / .kicad_dru) and kilib beside it only for nothing here: the
measurements use the saved fills. Sections of OUT.json:
  pyro_rules   per m3.kicad_dru pyro rule (A-H, A2): the closest same-layer approach between copper the rule covers
               (pads, tracks, via rings and zone fills), with both items; DRC proves each >= its minimum, this gives
               the margin and where it is. Pads of the parts the rule exempts are skipped as the rule does. Rule G
               counts a gate-net item only where it intersects the PYRO_BLOCK rule area (the DRU's
               A.intersectsArea('PYRO_BLOCK'), tested on the board's own area outline); G was missing until review
               pass 4 (R8P4-PYRO-01).
  exits        each pyro exit net (GATE_N, CONT, ARM1_SENSE and their 4.7 k MCU sides): copper length, layers, vias and
               the closest other-net copper, outside the rigid CH1 block copper.
  bare         exposed copper (pad mask openings) of the gate nets PYRO1_GATE / PYRO1_GATE_N / ACT_GATE / ACT_DRV and
               J2's NRST pad: nearest exposed pad of each always-live or armed-live net on the same face (the coating
               and leakage distances of ORDERING section 5 / M3_R4 W4).
  block_vias   GND vias inside the PYRO_BLOCK rule area and their nearest pyro / arming / RAW_ACT copper.
  a8           TP122 (gate test pad) and the PYRO1_GATE via inside it: position, side, hole edge inside the pad,
               nearest GND via and nearest foreign copper.
  probes       every test pad (net, side, position); NRST's probe (C24.1) and the nearest 3V3 pad on the same face.
  holes        each M3 hole: nearest pads per face (centre to copper) and the fills within a 3.5 mm washer radius.
  edges        parts whose courtyard or pads come within 1.0 mm of the left or right long edge.
  tabs         the 5 mm windows by ORDERING's rules (r8_place_check.tab_windows) and, for the D35 plan, each tab's
               nearest part, capacitor-class item and connector.
  mark         the JLC order-number text: ink box, nearest via ring, pad opening and other silkscreen.
  parts        placed parts per face, test pads per face, through-hole parts, DNP parts, deepest bottom model.
  rf           courtyard distances from every RF part and both modules to the restricted parts (R7 pass2_rf 3.9),
               radio interface lines to U30's body (DS Table 21 box) and to the GNSS RF copper (3.10), the two RF
               lines' nearest approach and the jacks' spacing (3.11), and fast-net copper near the modules and lines.
  imu          U4's position, rotation, face, pad-1 offset and the lever arm to the roll axis (x 23, top face z 0).
"""
import json
import math
import re
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'm3_design'))
import check_r8 as C8  # noqa: E402
import check_r7 as C7  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
LIVE = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')
GATES = ('PYRO1_GATE', 'PYRO1_GATE_N')
SENSE = ('ARM1_SENSE', 'PYRO1_CONT', 'PYRO1_COLD', 'PYRO1_CONT_MID', 'ARM1_SENSE_MID')
RULES = {   # name: (min mm, predicate on (net A, net B), parts whose own A/B pads are exempt, pads only)
    'A RAW_ACT to pyro control 0.5': (0.5, lambda a, b: a == 'RAW_ACT' and b in GATES + SENSE, (), False),
    'B bus/ign/drain to gate 0.5': (0.5, lambda a, b: a in LIVE and b in GATES, ('Q124',), False),
    'C bus/ign/drain to sense 0.3': (0.3, lambda a, b: a in LIVE and b in SENSE, ('R173', 'R131', 'R132'), False),
    'D GND to bus/ign/drain 0.5': (0.5, lambda a, b: a == 'GND' and b in LIVE, ('Q124', 'C128'), False),
    'E RAW_ACT to bus/ign 1.0': (1.0, lambda a, b: a == 'RAW_ACT' and b in ('PYRO1_BUS', 'PYRO1_IGN'), (), False),
    'F bus/ign/drain to other live 0.5': (0.5, lambda a, b: a in LIVE and b not in LIVE + GATES + SENSE + ('GND', '')
                                          and not (a in ('PYRO1_BUS', 'PYRO1_IGN') and b == 'RAW_ACT'), ('Q124',), False),
    'G gate nets in the block to other live 0.3': (0.3, lambda a, b: a in GATES and b not in GATES + LIVE + ('GND', 'RAW_ACT', ''),
                                                   ('Q124',), False),
    'A2 RAW_ACT to RAW_ACT_SENSE 0.3': (0.3, lambda a, b: a == 'RAW_ACT' and b == 'RAW_ACT_SENSE', (), False),
    'H live pads to sense/gate pads 1.0': (1.0, lambda a, b: (a in LIVE + ('RAW_ACT',) and b in ('ARM1_SENSE', 'PYRO1_CONT',
                                           'RAW_ACT_SENSE') + GATES + ('ACT_GATE', 'ACT_DRV')) or
                                           (a in ('PYRO1_CONT_MID', 'ARM1_SENSE_MID', 'RAW_ACT_SENSE_MID') and
                                            b in GATES + ('ACT_GATE', 'ACT_DRV')), ('Q124', 'Q120', 'Q121', 'Q122'), True),
}
IN_BLOCK_A = ('G gate nets in the block to other live 0.3',)   # rules whose net-A item must intersect PYRO_BLOCK
EXIT_NETS = ('PYRO1_GATE_N', 'PYRO1_CONT', 'ARM1_SENSE', 'PYRO1_CONT_MCU', 'ARM1_SENSE_MCU')
ALWAYS_LIVE = ('RAW_ACT', 'BAT_IN', 'RAW_PROTECTED', 'VLOGIC', '3V3', '3V3A', 'CAM_5V', 'CAM_INPUT_LIMITED',
               'USB_LIMITED', 'VBUS', 'BAT_ENABLE', 'BAT_SW_SOURCE', 'ACT_FET_S') + LIVE
U30_BODY = (5.36, 10.10, 15.46, 19.80)            # MAX-F10S body, DS Table 21 nominal, centred on U30 (pass2_rf 3.7)
RADIO_IF = re.compile(r'^RADIO_(DIO1|RXEN|NRST|BUSY|MISO|MOSI|SCK|NSS|MISO_MCU|MOSI_MCU|SCK_MCU|TXEN)$')
GNSS_RF = ('GNSS_RF_ANT', 'GNSS_RF_IN')
RADIO_RF = ('RADIO_RF_ANT', 'RADIO_RF')
PYRO_BLOCK = (4.0, 84.0, 42.0, 114.4)
HOLE_REACH = 6.0
WASHER = 3.5


def r3(v):
    return None if v is None else round(v, 3)


def items_by_net(board):
    out = {}
    for it in C8.net_items(board, lambda n: True):
        out.setdefault(it[1], []).append(it)
    return out


def box_of(shape):
    return shape.BBox()


def near_boxes(a, b, g):
    A, B = a.BBox(), b.BBox()
    return not (A.GetRight() + MM(g) < B.GetLeft() or B.GetRight() + MM(g) < A.GetLeft() or
                A.GetBottom() + MM(g) < B.GetTop() or B.GetBottom() + MM(g) < A.GetTop())


def owner(it):
    obj = it[4]
    return obj.GetParentFootprint().GetReference() if isinstance(obj, pcbnew.PAD) else None


def pyro_rules(board, byn):
    out = {}
    block = [pcbnew.SHAPE_POLY_SET(z.Outline()) for z in board.Zones()
             if z.GetIsRuleArea() and z.GetZoneName() == 'PYRO_BLOCK']
    if not block:
        raise ValueError('no PYRO_BLOCK rule area on the board (rule G needs it)')

    def in_block(it):          # the DRU's A.intersectsArea('PYRO_BLOCK'): the area outline collides with the item's shape
        return any(pcbnew.SHAPE.Collide(area, it[3], 0) for area in block)

    for name, (mn, pred, exempt, pads_only) in RULES.items():
        best, close = None, 0
        nets = list(byn)
        for na in nets:
            for nb in nets:
                if na == nb or not pred(na, nb):
                    continue
                for a in byn[na]:
                    if pads_only and not isinstance(a[4], pcbnew.PAD):
                        continue
                    if name in IN_BLOCK_A and not in_block(a):
                        continue
                    for b in byn[nb]:
                        if a[2] != b[2] or (pads_only and not isinstance(b[4], pcbnew.PAD)):
                            continue
                        oa, ob = owner(a), owner(b)
                        if oa and oa == ob and oa in exempt:
                            continue
                        if not near_boxes(a[3], b[3], mn + 1.0):
                            continue
                        g = C8.min_gap(a[3], b[3], mn + 1.0)
                        if g is None:
                            continue
                        close += g < mn + 0.1
                        if best is None or g < best[0]:
                            best = (g, a[0], na, b[0], nb, board.GetLayerName(a[2]))
        out[name] = dict(minimum=mn, closest=None if best is None else dict(
            mm=best[0], margin=round(best[0] - mn, 3), a=f'{best[1]} ({best[2]})', b=f'{best[3]} ({best[4]})',
            layer=best[5]), within_0p1_of_minimum=close)
    return out


def exits(board, byn):
    """Per exit net: its copper outside the rigid CH1 copper (check_r8.ch1_copper), and the nearest other-net copper
    to that copper: any net but GND, and the always-live nets (GND pours sit at the netclass clearance everywhere)."""
    rigid_ids = {str(it.m_Uuid.AsString()) for it in C8.ch1_copper(board) if hasattr(it, 'm_Uuid')}
    out = {}
    for net in EXIT_NETS:
        own = [t for t in board.GetTracks() if t.GetNetname() == net and str(t.m_Uuid.AsString()) not in rigid_ids]
        length = sum(mm(t.GetLength()) for t in own if t.GetClass() == 'PCB_TRACK')
        layers = sorted({t.GetLayerName() for t in own if t.GetClass() == 'PCB_TRACK'})
        vias = [(round(mm(t.GetPosition().x), 3), round(mm(t.GetPosition().y), 3)) for t in own if t.GetClass() == 'PCB_VIA']
        own_ids = {str(t.m_Uuid.AsString()) for t in own}
        mine = [it for it in byn.get(net, []) if isinstance(it[4], (pcbnew.PCB_TRACK, pcbnew.PCB_VIA))
                and str(it[4].m_Uuid.AsString()) in own_ids]
        best = {'non_gnd': None, 'always_live': None}
        for other, items in byn.items():
            if other in (net, 'GND', ''):
                continue
            for b in items:
                for a in mine:
                    if a[2] != b[2] or not near_boxes(a[3], b[3], 2.0):
                        continue
                    g = C8.min_gap(a[3], b[3], 2.0)
                    if g is None:
                        continue
                    row = (g, a[0], f'{b[0]} ({other})', board.GetLayerName(a[2]))
                    if best['non_gnd'] is None or g < best['non_gnd'][0]:
                        best['non_gnd'] = row
                    if other in ALWAYS_LIVE and (best['always_live'] is None or g < best['always_live'][0]):
                        best['always_live'] = row
        out[net] = dict(new_copper_mm=round(length, 2), layers=layers, vias=vias,
                        **{f'nearest_{k}': None if v is None else dict(mm=v[0], own=v[1], other=v[2], layer=v[3])
                           for k, v in best.items()})
    return out


def exposed_pads(board):
    out = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            for face, cu, mask in (('F', pcbnew.F_Cu, pcbnew.F_Mask), ('B', pcbnew.B_Cu, pcbnew.B_Mask)):
                if p.IsOnLayer(cu) and p.IsOnLayer(mask):
                    out.append((f'{f.GetReference()}.{p.GetNumber()}', p.GetNetname(), face, p.GetEffectiveShape(cu)))
    return out


def bare(board):
    pads = exposed_pads(board)
    targets = [p for p in pads if p[1] in GATES + ('ACT_GATE', 'ACT_DRV')]
    targets += [p for p in pads if p[0].startswith('J2.') and p[1] == 'NRST']
    out = {}
    for name, net, face, shape in targets:
        row = {}
        for cls, pred in (('armed live (bus/ign/drain)', lambda n: n in LIVE), ('RAW_ACT', lambda n: n == 'RAW_ACT'),
                          ('3V3', lambda n: n in ('3V3', '3V3A')),
                          ('other always-live', lambda n: n in ALWAYS_LIVE and n not in LIVE + ('RAW_ACT', '3V3', '3V3A')),
                          ('GND', lambda n: n == 'GND'), ('any other net', lambda n: n not in (net, '') and n is not None)):
            best = None
            for n2, net2, face2, s2 in pads:
                if face2 != face or net2 == net or not pred(net2) or n2.split('.')[0] == name.split('.')[0] and cls != 'any other net':
                    continue
                if not near_boxes(shape, s2, 5.0):
                    continue
                g = C8.min_gap(shape, s2, 5.0)
                if g is not None and (best is None or g < best[0]):
                    best = (g, f'{n2} ({net2})')
            row[cls] = None if best is None else dict(mm=best[0], pad=best[1])
        out[f'{name} ({net}, {face})'] = row
    return out


def block_vias(board, byn):
    x0, y0, x1, y1 = PYRO_BLOCK
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND'
            and x0 <= mm(t.GetPosition().x) <= x1 and y0 <= mm(t.GetPosition().y) <= y1]
    nets = [n for n in byn if n in LIVE + GATES + SENSE + ('RAW_ACT', 'PYRO1_CONT_MCU', 'ARM1_SENSE_MCU')]
    worst = None
    for v in vias:
        for lay in board.GetEnabledLayers().CuStack():
            if not v.IsOnLayer(lay):
                continue
            s = C8.item_shape(v, lay)
            for n in nets:
                for it in byn[n]:
                    if it[2] != lay or not near_boxes(s, it[3], 2.0):
                        continue
                    g = C8.min_gap(s, it[3], 2.0)
                    if g is not None and (worst is None or g < worst[0]):
                        worst = (g, (round(mm(v.GetPosition().x), 3), round(mm(v.GetPosition().y), 3)), it[0], n,
                                 board.GetLayerName(lay))
    per = {}
    for v in vias:
        key = (round(mm(v.GetPosition().x), 3), round(mm(v.GetPosition().y), 3))
        best = None
        for lay in board.GetEnabledLayers().CuStack():
            if not v.IsOnLayer(lay):
                continue
            s = C8.item_shape(v, lay)
            for n in nets:
                for it in byn[n]:
                    if it[2] != lay or not near_boxes(s, it[3], 2.0):
                        continue
                    g = C8.min_gap(s, it[3], 2.0)
                    if g is not None and (best is None or g < best[0]):
                        best = (g, f'{it[0]} ({n})')
        per[f'{key[0]},{key[1]}'] = None if best is None else dict(mm=best[0], item=best[1])
    return dict(count=len(vias), per_via=per,
                nearest=None if worst is None else dict(mm=worst[0], via=worst[1], item=worst[2], net=worst[3],
                                                        layer=worst[4]))


def a8(board, byn):
    f = next(f for f in board.GetFootprints() if f.GetReference() == 'TP122')
    p = next(iter(f.Pads()))
    face = 'B' if f.IsFlipped() else 'F'
    cu = pcbnew.B_Cu if face == 'B' else pcbnew.F_Cu
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and p.GetEffectiveShape(cu).Collide(
        pcbnew.VECTOR2I(t.GetPosition()), 0)]
    pr = mm(p.GetSize(cu).x) / 2
    out = dict(pad=f'TP122.1 ({p.GetNetname()})', face=face, at=[round(mm(p.GetPosition().x), 3), round(mm(p.GetPosition().y), 3)],
               pad_diameter=round(2 * pr, 3), vias=[])
    gnd = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    for v in vias:
        c = (mm(v.GetPosition().x), mm(v.GetPosition().y))
        d0 = math.dist(c, (mm(p.GetPosition().x), mm(p.GetPosition().y)))
        hole_edge = pr - d0 - mm(v.GetDrillValue()) / 2
        ng = min(gnd, key=lambda g: math.dist(c, (mm(g.GetPosition().x), mm(g.GetPosition().y))))
        out['vias'].append(dict(net=v.GetNetname(), at=[round(c[0], 3), round(c[1], 3)], drill=mm(v.GetDrillValue()),
                                hole_edge_inside_pad_edge_mm=round(hole_edge, 3),
                                nearest_gnd_via_mm=round(math.dist(c, (mm(ng.GetPosition().x), mm(ng.GetPosition().y))), 3),
                                nearest_gnd_via=[round(mm(ng.GetPosition().x), 3), round(mm(ng.GetPosition().y), 3)]))
    best = None
    s = p.GetEffectiveShape(cu)
    for n, items in byn.items():
        if n == p.GetNetname():
            continue
        for it in items:
            if it[2] != cu or not near_boxes(s, it[3], 3.0):
                continue
            g = C8.min_gap(s, it[3], 3.0)
            if g is not None and (best is None or g < best[0]):
                best = (g, it[0], n)
    out['nearest_foreign_copper'] = None if best is None else dict(mm=best[0], item=f'{best[1]} ({best[2]})')
    return out


def probes(board):
    tps = []
    for f in sorted(board.GetFootprints(), key=lambda f: (len(f.GetReference()), f.GetReference())):
        if f.GetReference().startswith('TP'):
            p = next(iter(f.Pads()))
            tps.append(dict(ref=f.GetReference(), net=p.GetNetname(), face='B' if f.IsFlipped() else 'F',
                            at=[round(mm(f.GetPosition().x), 2), round(mm(f.GetPosition().y), 2)]))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    c24 = fps['C24']
    face = 'B' if c24.IsFlipped() else 'F'
    nrst = next(p for p in c24.Pads() if p.GetNetname() == 'NRST')
    q = (mm(nrst.GetPosition().x), mm(nrst.GetPosition().y))
    cand = []
    for f in board.GetFootprints():
        if ('B' if f.IsFlipped() else 'F') != face:
            continue
        for p in f.Pads():
            if p.GetNetname() == '3V3' and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                cand.append((math.dist(q, (mm(p.GetPosition().x), mm(p.GetPosition().y))), f'{f.GetReference()}.{p.GetNumber()}',
                             [round(mm(p.GetPosition().x), 2), round(mm(p.GetPosition().y), 2)]))
    cand.sort()
    gnd_tps = [t for t in tps if t['net'] == 'GND']
    return dict(test_pads=tps, gnd_test_pads=gnd_tps,
                nrst_probe=dict(pad=f'C24.{nrst.GetNumber()}', face=face, at=[round(q[0], 2), round(q[1], 2)],
                                nearest_3v3_pads=[dict(mm=round(d, 2), pad=n, at=a) for d, n, a in cand[:3]]))


def holes(board):
    out = []
    circles = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and d.GetClass() == 'PCB_SHAPE'
               and d.GetShape() == pcbnew.SHAPE_T_CIRCLE]
    ties = {(21.5, 68.6), (27.0, 82.6)}
    for d in circles:
        c = (round(mm(d.GetCenter().x), 3), round(mm(d.GetCenter().y), 3))
        if any(math.dist(c, t) < 0.05 for t in ties):
            continue
        pt = pcbnew.SHAPE_CIRCLE(d.GetCenter(), MM(0.001))
        row = dict(at=list(c), nearest_pads={})
        for face, cu in (('F', pcbnew.F_Cu), ('B', pcbnew.B_Cu)):
            near = []
            for f in board.GetFootprints():
                for p in f.Pads():
                    if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or not p.IsOnLayer(cu):
                        continue
                    if math.dist(c, (mm(p.GetPosition().x), mm(p.GetPosition().y))) > HOLE_REACH + 3:
                        continue
                    g = C8.min_gap(pt, p.GetEffectiveShape(cu), HOLE_REACH)
                    if g is not None:
                        near.append((g, f'{f.GetReference()}.{p.GetNumber()}', p.GetNetname(), p.IsOnLayer(
                            pcbnew.F_Mask if face == 'F' else pcbnew.B_Mask)))
            near.sort()
            row['nearest_pads'][face] = [dict(mm=g, pad=n, net=net, exposed=e) for g, n, net, e in near[:3]]
        fills = set()
        for z in board.Zones():
            if z.GetIsRuleArea():
                continue
            for lay in board.GetEnabledLayers().CuStack():
                if z.IsOnLayer(lay) and z.HasFilledPolysForLayer(lay):
                    g = C8.min_gap(pt, z.GetFilledPolysList(lay), WASHER + 0.01)
                    if g is not None:
                        fills.add(f'{z.GetNetname()} {board.GetLayerName(lay)} ({g:.2f})')
        row['fills_within_washer_radius'] = sorted(fills)
        out.append(row)
    return out


def edges(board):
    out = []
    for f in board.GetFootprints():
        if f.GetReference() in ('J30', 'J31'):
            continue
        bb = C8.courtyard(f).BBox()
        boxes = [('courtyard', bb)] + [(f'pad {p.GetNumber()}', p.GetBoundingBox()) for p in f.Pads()]
        for edge, x in (('left', 0.0), ('right', 46.0)):
            d = min((mm(b.GetLeft()) - x) if edge == 'left' else (x - mm(b.GetRight())) for _, b in boxes)
            if d < 1.0:
                pad_d = min(((mm(b.GetLeft()) - x) if edge == 'left' else (x - mm(b.GetRight())))
                            for k, b in boxes if k.startswith('pad')) if len(boxes) > 1 else None
                out.append(dict(ref=f.GetReference(), edge=edge, courtyard_or_pad_mm=round(d, 2),
                                pad_mm=r3(pad_d), face='B' if f.IsFlipped() else 'F',
                                y=round(mm(f.GetPosition().y), 1)))
    return sorted(out, key=lambda r: (r['edge'], r['courtyard_or_pad_mm']))


def tabs(board):
    import r8_place_check as PC
    import r8_legalise as RL
    wins = PC.tab_windows(board)
    boxes = []
    for f in board.GetFootprints():
        ref = f.GetReference()
        if ref in ('J30', 'J31'):
            continue
        cls = 'soft' if PC.TAB_SOFT_REFS.match(ref) else 'connector' if ref.startswith('J') else 'part'
        boxes.append((ref, RL._box(C8.courtyard(f)), cls))
        for p in f.Pads():
            b = p.GetBoundingBox()
            boxes.append((ref, (mm(b.GetLeft()), mm(b.GetTop()), mm(b.GetRight()), mm(b.GetBottom())), cls))
    plan = {}
    for edge, spans in PC.TAB_PLAN.items():
        x = 0.0 if edge == 'left' else RL.W
        for y0, y1 in spans:
            near = {}
            for ref, b, cls in boxes:
                dx = max(b[0] - x, x - b[2], 0)
                dy = max(b[1] - y1, y0 - b[3], 0)
                d = math.hypot(dx, dy)
                for k in ('any', cls):
                    if k not in near or d < near[k][0]:
                        near[k] = (round(d, 2), ref)
            plan[f'{edge} y {y0}-{y1}'] = {k: dict(mm=v[0], ref=v[1]) for k, v in near.items()}
    return dict(windows=wins, plan=plan, rules=dict(length=PC.TAB_LEN, part=PC.TAB_PART, soft=PC.TAB_SOFT,
                                                     connector=PC.TAB_CONN, hole=PC.TAB_HOLE))


def mark(board):
    texts = [d for d in board.GetDrawings() if d.GetClass() in ('PCB_TEXT', 'PCB_TEXTBOX')
             and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
    m = next((t for t in texts if t.GetText().startswith('JLCJLC')), None)
    if m is None:
        return None
    lay = m.GetLayer()
    face_cu, face_mask = (pcbnew.B_Cu, pcbnew.B_Mask) if lay == pcbnew.B_SilkS else (pcbnew.F_Cu, pcbnew.F_Mask)
    ink = m.GetEffectiveShape()
    bb = m.GetBoundingBox()
    best_via = best_pad = best_silk = None
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            g = C8.min_gap(ink, pcbnew.SHAPE_CIRCLE(t.GetPosition(), t.GetWidth(face_cu) // 2), 3.0)
            if g is not None and (best_via is None or g < best_via[0]):
                best_via = (g, t.GetNetname(), (round(mm(t.GetPosition().x), 3), round(mm(t.GetPosition().y), 3)))
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.IsOnLayer(face_mask):
                g = C8.min_gap(ink, p.GetEffectiveShape(face_cu), 3.0)
                if g is not None and (best_pad is None or g < best_pad[0]):
                    best_pad = (g, f'{f.GetReference()}.{p.GetNumber()}')
        for fld in (f.Reference(), f.Value()):
            if fld.IsVisible() and fld.GetLayer() == lay:
                g = C8.min_gap(ink, fld.GetEffectiveShape(), 3.0)
                if g is not None and (best_silk is None or g < best_silk[0]):
                    best_silk = (g, f'{f.GetReference()} designator')
        for gr in f.GraphicalItems():
            if gr.GetLayer() == lay:
                g = C8.min_gap(ink, gr.GetEffectiveShape(), 3.0)
                if g is not None and (best_silk is None or g < best_silk[0]):
                    best_silk = (g, f'{f.GetReference()} graphic')
    for t in texts:
        if t is m or t.GetLayer() != lay or t.GetText() == m.GetText():
            continue
        g = C8.min_gap(ink, t.GetEffectiveShape(), 3.0)
        if g is not None and (best_silk is None or g < best_silk[0]):
            best_silk = (g, f'text "{t.GetText()[:20]}"')
    return dict(text=m.GetText(), layer=m.GetLayerName(), at=[round(mm(m.GetPosition().x), 2), round(mm(m.GetPosition().y), 2)],
                ink_box=[round(mm(bb.GetLeft()), 2), round(mm(bb.GetTop()), 2), round(mm(bb.GetRight()), 2),
                         round(mm(bb.GetBottom()), 2)],
                nearest_via_ring=None if best_via is None else dict(mm=best_via[0], net=best_via[1], at=best_via[2]),
                nearest_pad_opening=None if best_pad is None else dict(mm=best_pad[0], pad=best_pad[1]),
                nearest_other_silk=None if best_silk is None else dict(mm=best_silk[0], item=best_silk[1]))


def parts(board):
    out = dict(top=0, bottom=0, top_tp=0, bottom_tp=0, tht=[], dnp=[], board_only=[])
    for f in board.GetFootprints():
        a = f.GetAttributes()
        ref = f.GetReference()
        if a & pcbnew.FP_BOARD_ONLY:
            out['board_only'].append(ref)
            continue
        if a & pcbnew.FP_DNP:
            out['dnp'].append(ref)
            continue
        face = 'bottom' if f.IsFlipped() else 'top'
        if ref.startswith('TP') or ref == 'J2':
            if ref.startswith('TP'):
                out[face + '_tp'] += 1
            continue
        out[face] += 1
        if a & pcbnew.FP_THROUGH_HOLE:
            out['tht'].append(ref)
    for k in ('tht', 'dnp', 'board_only'):
        out[k].sort()
    return out


def rf(board):
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    yards = {r: C8.courtyard(f) for r, f in fps.items()}
    rf_parts = sorted(r for r in fps if C7.RF_PART.fullmatch(r))
    restricted = sorted({r for r, f in fps.items() if any(p.GetNetname() in C8.SWITCH_NETS for p in f.Pads())}
                        | {r for r in C8.BUCK_PARTS + C8.NOISY_PARTS if r in fps})
    per = {}
    for r in rf_parts:
        best = None
        for o in restricted:
            g = C8.min_gap(yards[r], yards[o], 40.0)
            if g is not None and (best is None or g < best[0]):
                best = (g, o)
        per[r] = None if best is None else dict(mm=best[0], part=best[1])
    modules = {}
    for m in ('U30', 'U31'):
        modules[m] = {o: C8.min_gap(yards[m], yards[o], 120.0) for o in ('U2', 'L1', 'U3', 'U1', 'Y1', 'U8', 'L3', 'C6',
                                                                          'U7') if o in fps}
    # radio interface lines near U30
    body = pcbnew.SHAPE_POLY_SET()
    body.NewOutline()
    x0, y0, x1, y1 = U30_BODY
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        body.Append(MM(x), MM(y))
    gnss_rf = [it for it in C8.net_items(board, lambda n: n in GNSS_RF) if not isinstance(it[4], pcbnew.ZONE)]
    radio_rf = [it for it in C8.net_items(board, lambda n: n in RADIO_RF) if not isinstance(it[4], pcbnew.ZONE)]
    lines = {}
    for it in C8.net_items(board, lambda n: bool(RADIO_IF.match(n or ''))):
        if isinstance(it[4], (pcbnew.ZONE, pcbnew.PAD)):
            continue
        net = it[1]
        g = C8.min_gap(body, it[3], 40.0)
        h = min((C8.min_gap(it[3], q[3], 40.0) for q in gnss_rf if True), key=lambda v: 99 if v is None else v)
        cur = lines.setdefault(net, dict(body=None, gnss_rf=None))
        if g is not None and (cur['body'] is None or g < cur['body'][0]):
            cur['body'] = (g, it[0], board.GetLayerName(it[2]))
        if h is not None and (cur['gnss_rf'] is None or h < cur['gnss_rf']):
            cur['gnss_rf'] = h
    lines = {n: dict(body_mm=v['body'][0] if v['body'] else None, at=v['body'][1] if v['body'] else None,
                     layer=v['body'][2] if v['body'] else None, gnss_rf_mm=v['gnss_rf']) for n, v in sorted(lines.items())}
    rf_rf = None
    for a in gnss_rf:
        for b in radio_rf:
            g = C8.min_gap(a[3], b[3], 40.0)
            if g is not None and (rf_rf is None or g < rf_rf):
                rf_rf = g
    jacks = math.dist(*[(mm(fps[j].GetPosition().x), mm(fps[j].GetPosition().y)) for j in ('J30', 'J31')])
    fast = C8.net_items(board, lambda n: bool(C8.FAST_NETS.match(n or '')))
    near_fast = {}
    for label, targets in (('U30', [yards['U30']]), ('U31', [yards['U31']]), ('RF copper', [q[3] for q in gnss_rf + radio_rf])):
        best = None
        for it in fast:
            for t in targets:
                g = C8.min_gap(t, it[3], 30.0)
                if g is not None and (best is None or g < best[0]):
                    best = (g, it[1], it[0])
        near_fast[label] = None if best is None else dict(mm=best[0], net=best[1], item=best[2])
    return dict(restricted=restricted, per_rf_part=per, modules=modules, radio_lines_near_u30=lines,
                rf_lines_nearest_mm=rf_rf, jack_spacing_mm=round(jacks, 3),
                module_courtyards_mm=C8.min_gap(yards['U30'], yards['U31'], 40.0), fast_copper=near_fast)


def imu(board):
    f = next(f for f in board.GetFootprints() if f.GetReference() == 'U4')
    p1 = next(p for p in f.Pads() if p.GetNumber() == '1')
    c = (mm(f.GetPosition().x), mm(f.GetPosition().y))
    return dict(at=[round(c[0], 3), round(c[1], 3)], rot=f.GetOrientationDegrees(), face='B' if f.IsFlipped() else 'F',
                pad1_offset=[round(mm(p1.GetPosition().x) - c[0], 3), round(mm(p1.GetPosition().y) - c[1], 3)],
                lever_arm_x_mm=round(c[0] - 23.0, 3))


def main(path, out):
    b = pcbnew.LoadBoard(path)
    byn = items_by_net(b)
    rep = dict(board=path)
    for name, fn in (('pyro_rules', lambda: pyro_rules(b, byn)), ('exits', lambda: exits(b, byn)), ('bare', lambda: bare(b)),
                     ('block_vias', lambda: block_vias(b, byn)), ('a8', lambda: a8(b, byn)), ('probes', lambda: probes(b)),
                     ('holes', lambda: holes(b)), ('edges', lambda: edges(b)), ('tabs', lambda: tabs(b)),
                     ('mark', lambda: mark(b)), ('parts', lambda: parts(b)), ('rf', lambda: rf(b)), ('imu', lambda: imu(b))):
        try:
            rep[name] = fn()
        except Exception as e:                       # report and continue: one section must not hide the others
            rep[name] = dict(error=f'{type(e).__name__}: {e}')
        print(name, 'done', flush=True)
    json.dump(rep, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
