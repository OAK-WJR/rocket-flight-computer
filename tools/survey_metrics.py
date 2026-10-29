#!/usr/bin/env python3
"""Layout-quality survey of one filled KiCad board: the geometric half of the R8 baseline scorecard.

usage: <KiCad python3> -I tools/survey_metrics.py BOARD.kicad_pcb [--tools DIR] [--json OUT.json] [--step 0.05]

BOARD must carry its saved zone fills (run a refill before surveying a new board). Read-only. Part of the R8 scorecard
(tools/run_survey.sh; metric definitions: m3_design/assembly_review/sources/r8_design/survey_baseline.md), moved into
tools/ unchanged in R8 build step 1 but for the default --tools.
--tools is the directory holding route_check.py, whose net classes (CLASSES / net_class), copper collector
(collect) and per-net route metric (net_route) are reused so the numbers agree with the gate. Default: this
directory. R8's route_check keeps R7's classes, collector and net_route (the D10 keep-out-aware baseline is used only
by its detour gate), so the survey of a board is the same with either revision's tools; detour ratios here are on the
plain octilinear MST.

Sections of the JSON (all lengths mm, areas mm^2):
  inventory     outline area and bbox, footprints per side, pads, nets
  tracks        track length and segment count per layer, per net class, per class x layer
  vias          every via classified: gnd_stitch (GND, only pour fills attached), gnd_track (GND, a GND track or pad
                attached), power_* / signal_* (by net class) split into layer_change (same-net tracks on >= 2 layers),
                track_to_pad (track on one layer, same-net pad on another), track_to_pour, pour_only, other
  routes        every net without a pour and with >= 2 pads: copper length, octilinear MST of its pad centres,
                ratio, layer-changing vias, the vias its pads need (route_check.net_route), length per layer, bends
  detour        distribution of the route ratio (histogram, median, p90, max, length-weighted ratio, excess mm)
  critical      every critical signal net (route_check SIGNAL_CRITICAL: rf, pyro, crystal, usb, spi, rfif):
                route metrics plus its layer changes and how many have no GND via centre within 1.5 mm
  buses         per logical bus (QSPI, SPI1_IMU, RADIO_SPI, RADIO_CTRL, GNSS_IF, SERVO, CAM_UART, SWD, USB; series
                halves summed): total / min / max length, spread, vias, layers, weighted ratio, bends
  bends         heading changes at plain track nodes (two same-net same-layer track ends, no pad, via or T):
                45, 90, acute (> 90), collinear (unmerged), other; per 10 mm of track; per class and per layer
  planes        each (layer, net) pour: area, islands, voids (holes) by size, perimeter; In1 coverage of the board;
                F/B GND pour islands by the number of GND vias / plated GND holes inside them
  reference     length-based reference coverage of the critical nets (centre line every --step mm): R6 mapping
                (F.Cu -> In1 GND, B.Cu -> In2 GND/3V3/3V3A) and the extended mapping (+ In1 -> F.Cu GND,
                In2 -> B.Cu GND), per net and layer, what lies under the unreferenced length, and the number of
                reference-edge crossings (entering / leaving the reference fill along a track); unreferenced
                length within 0.7 mm of the net's own vias / PTH pads (its own antipad at a layer change) is
                reported apart (own_via_antipad) and not counted in 'unreferenced'
  stitching     GND vias + plated GND holes per cm^2, distance from every board point (0.5 mm raster, inside the
                outline) to the nearest one: median, p95, max and where the max is; per y band
  parts         parts per side, courtyard area, utilisation per y band (board height / 5) and on a 4 x 10 grid
  scorecard     the simplicity metrics defined in survey_baseline.md (S-, R-, P- and Q-rows)
"""
import argparse
import importlib
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pcbnew

DEFAULT_TOOLS = str(Path(__file__).resolve().parent)
mm, MM = pcbnew.ToMM, pcbnew.FromMM
CU4 = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
LN = {pcbnew.F_Cu: 'F.Cu', pcbnew.In1_Cu: 'In1.Cu', pcbnew.In2_Cu: 'In2.Cu', pcbnew.B_Cu: 'B.Cu'}
GND_REACH = 1.5
OWN_VIA = 0.7                    # mm: a sample this close to a same-net via / PTH centre is in its own antipad
REF_R6 = {pcbnew.F_Cu: (pcbnew.In1_Cu, ('GND',)), pcbnew.B_Cu: (pcbnew.In2_Cu, ('GND', '3V3', '3V3A'))}
REF_EXT = dict(REF_R6)
REF_EXT.update({pcbnew.In1_Cu: (pcbnew.F_Cu, ('GND',)), pcbnew.In2_Cu: (pcbnew.B_Cu, ('GND',))})
R6_NETS = ('USB_DP', 'USB_DM', 'HSE_IN', 'HSE_OUT', 'QSPI_CLK', 'QSPI_NCS', 'QSPI_IO0', 'QSPI_IO1', 'QSPI_IO2',
           'QSPI_IO3', 'SPI1_SCK', 'SPI1_MOSI', 'SPI1_MISO', 'IMU_CS')
EXT_NETS = ('SWDIO', 'SWCLK', 'NRST', 'RADIO_NSS', 'RADIO_SCK', 'RADIO_SCK_MCU', 'RADIO_MOSI', 'RADIO_MOSI_MCU',
            'RADIO_MISO', 'RADIO_MISO_MCU')
BUSES = {                       # logical signals (series-resistor halves together) judged for bus cleanliness
    'QSPI': [('QSPI_CLK',), ('QSPI_NCS',), ('QSPI_IO0',), ('QSPI_IO1',), ('QSPI_IO2',), ('QSPI_IO3',)],
    'SPI1_IMU': [('SPI1_SCK',), ('SPI1_MOSI',), ('SPI1_MISO',), ('IMU_CS',)],
    'RADIO_SPI': [('RADIO_NSS',), ('RADIO_SCK', 'RADIO_SCK_MCU'), ('RADIO_MOSI', 'RADIO_MOSI_MCU'),
                  ('RADIO_MISO', 'RADIO_MISO_MCU')],
    'RADIO_CTRL': [('RADIO_BUSY',), ('RADIO_NRST',), ('RADIO_DIO1',), ('RADIO_RXEN',), ('RADIO_TXEN',)],
    'GNSS_IF': [('GNSS_TXD', 'GNSS_TXD_MCU'), ('GNSS_RXD', 'GNSS_RXD_MCU'), ('GNSS_RESET_N',),
                ('GNSS_TIMEPULSE', 'GNSS_TP_MCU'), ('GNSS_LNA_EN',)],
    'SERVO': [('SERVO1_MCU', 'SERVO1_OUT'), ('SERVO2_MCU', 'SERVO2_OUT'), ('SERVO3_MCU', 'SERVO3_OUT'),
              ('SERVO4_MCU', 'SERVO4_OUT')],
    'CAM_UART': [('CAM_MCU_TX', 'CAM_TX_BUFFER', 'CAM_TX_WIRE'), ('CAM_MCU_RX', 'CAM_RX_BUFFER', 'CAM_RX_WIRE')],
    'SWD': [('SWDIO',), ('SWCLK',), ('NRST',)],
    'USB': [('USB_DP',), ('USB_DM',)],
}


def octile(dx, dy):
    dx, dy = abs(dx), abs(dy)
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


def pctl(vals, q):
    if not vals:
        return None
    s = sorted(vals)
    k = (len(s) - 1) * q
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def r(v, n=2):
    return None if v is None else round(v, n)


class Survey:
    def __init__(self, board, rc, step):
        self.b, self.rc, self.step = board, rc, step
        self.nc = rc.collect(board)
        self.cls_cache = {}
        self.out = {}

    def cls(self, net):
        if net not in self.cls_cache:
            if net == 'GND':
                c = 'gnd'
            else:
                c = self.rc.net_class(net) or 'other'
            self.cls_cache[net] = c
        return self.cls_cache[net]

    def signal(self, net):
        return self.cls(net) not in ('power', 'gnd')

    # ------------------------------------------------------------------ inventory
    def inventory(self):
        b = self.b
        ps = pcbnew.SHAPE_POLY_SET()
        b.GetBoardPolygonOutlines(ps, False)
        self.outline = ps
        bb = ps.BBox()
        self.bbox = (mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))
        self.area = ps.Area() / 1e12
        fps = list(b.GetFootprints())
        pads = [p for f in fps for p in f.Pads()]
        nets_with_pads = Counter(p.GetNetname() for p in pads if p.GetNetname())
        self.out['inventory'] = dict(
            board=b.GetFileName(), outline_bbox=[r(v) for v in self.bbox],
            outline_w=r(self.bbox[2] - self.bbox[0]), outline_h=r(self.bbox[3] - self.bbox[1]),
            outline_area=r(self.area, 1), copper_layers=b.GetCopperLayerCount(),
            footprints=len(fps), top=sum(1 for f in fps if f.GetLayer() == pcbnew.F_Cu),
            bottom=sum(1 for f in fps if f.GetLayer() == pcbnew.B_Cu),
            pads=len(pads), pth_pads=sum(1 for p in pads if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH),
            nets=b.GetNetCount() - 1, nets_with_2plus_pads=sum(1 for n, k in nets_with_pads.items() if k >= 2),
            poured_nets=sorted(n for n, c in self.nc.items() if c.zones),
            segments=sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK'),
            arcs=sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_ARC'),
            vias=sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA'))

    # ------------------------------------------------------------------ tracks
    def tracks(self):
        per_layer, per_cls, per_cls_layer, seg_layer = Counter(), Counter(), defaultdict(Counter), Counter()
        width_cls = defaultdict(Counter)
        for t in self.b.GetTracks():
            if t.GetClass() != 'PCB_TRACK':
                continue
            L = mm(t.GetLength())
            lay, c = LN[t.GetLayer()], self.cls(t.GetNetname())
            per_layer[lay] += L
            seg_layer[lay] += 1
            per_cls[c] += L
            per_cls_layer[c][lay] += L
            width_cls[c][round(mm(t.GetWidth()), 3)] += L
        sig = sum(v for c, v in per_cls.items() if c not in ('power', 'gnd'))
        self.out['tracks'] = dict(
            total=r(sum(per_layer.values()), 1), signal=r(sig, 1), power=r(per_cls['power'], 1), gnd=r(per_cls['gnd'], 1),
            per_layer={k: r(v, 1) for k, v in sorted(per_layer.items())},
            segments_per_layer=dict(sorted(seg_layer.items())),
            per_class={k: r(v, 1) for k, v in sorted(per_cls.items())},
            per_class_layer={c: {k: r(v, 1) for k, v in sorted(d.items())} for c, d in sorted(per_cls_layer.items())},
            width_by_class={c: {str(w): r(v, 1) for w, v in sorted(d.items())} for c, d in sorted(width_cls.items())})

    # ------------------------------------------------------------------ vias
    def via_layers(self, net, v):
        """(track layers, pad layers, pour layers) of same-net copper attached at via v (dict from collect)."""
        nc = self.nc[net]
        p, rad = v['pos'], v['r']
        tl = {t['lid'] for t in nc.tracks if math.dist(t['a'], p) <= rad or math.dist(t['b'], p) <= rad}
        pl = set()
        for pd in nc.pads:
            for lid in pd['layers']:
                if self.rc._in_pad(pd, lid, p):
                    pl.add(lid)
        zl = {lid for z, lays in nc.zones for lid in lays if z.HitTestFilledArea(lid, pcbnew.VECTOR2I(int(p[0]), int(p[1])))}
        return tl, pl, zl

    def vias(self):
        kinds, by_net = Counter(), defaultdict(Counter)
        self.gnd_vias, self.layer_changes = [], defaultdict(list)
        drills = Counter()
        for net, nc in self.nc.items():
            for v in nc.vias:
                tl, pl, zl = self.via_layers(net, v)
                drills[(round(mm(v['obj'].GetDrillValue()), 3), round(mm(2 * v['r']), 3))] += 1
                c = self.cls(net)
                if c == 'gnd':
                    self.gnd_vias.append(v['pos'])
                    k = 'gnd_track' if (tl or pl) else 'gnd_stitch'
                else:
                    grp = 'power' if c == 'power' else 'signal'
                    if len(tl) >= 2:
                        k = grp + '_layer_change'
                        self.layer_changes[net].append(v['pos'])
                    elif tl and (pl - tl):
                        k = grp + '_track_to_pad'
                    elif tl and (zl - tl):
                        k = grp + '_track_to_pour'
                    elif zl and not tl:
                        k = grp + '_pour_only'
                    else:
                        k = grp + '_other'
                kinds[k] += 1
                by_net[net][k] += 1
        n_sig = sum(v for k, v in kinds.items() if k.startswith('signal'))
        n_pow = sum(v for k, v in kinds.items() if k.startswith('power'))
        self.out['vias'] = dict(
            total=sum(kinds.values()), gnd=kinds['gnd_stitch'] + kinds['gnd_track'], gnd_stitch=kinds['gnd_stitch'],
            gnd_track=kinds['gnd_track'], power=n_pow, signal=n_sig,
            signal_layer_change=kinds['signal_layer_change'], power_layer_change=kinds['power_layer_change'],
            kinds=dict(sorted(kinds.items())),
            drill_diameter={f'{d}/{D}': n for (d, D), n in sorted(drills.items())},
            top_signal_via_nets=sorted(((n, sum(v for k, v in c.items() if k.startswith('signal')))
                                        for n, c in by_net.items()), key=lambda x: -x[1])[:15],
            top_power_via_nets=sorted(((n, sum(v for k, v in c.items() if k.startswith('power')))
                                       for n, c in by_net.items()), key=lambda x: -x[1])[:10])

    # ------------------------------------------------------------------ bends
    def bends_of(self, nc):
        """Heading changes at plain nodes of one net, per layer: list of (layer, change deg, (x, y) mm)."""
        out = []
        by_layer = defaultdict(list)
        for t in nc.tracks:
            if t['a'] != t['b']:
                by_layer[t['lid']].append(t)
        for lid, ts in by_layer.items():
            ends = defaultdict(list)
            for i, t in enumerate(ts):
                for e, o in ((t['a'], t['b']), (t['b'], t['a'])):
                    ends[(round(e[0] / 1000), round(e[1] / 1000))].append((i, e, o))
            for key, lst in ends.items():
                if len(lst) != 2:
                    continue
                p = lst[0][1]
                if any(math.dist(v['pos'], p) <= v['r'] and lid in v['layers'] for v in nc.vias):
                    continue
                if any(self.rc._in_pad(pd, lid, p) for pd in nc.pads):
                    continue
                if any(j not in (lst[0][0], lst[1][0]) and self.rc.pt_seg(p, t['a'], t['b'])[0] <= 1000
                       for j, t in enumerate(ts)):
                    continue          # a T: another track's body passes here
                (i1, e1, o1), (i2, e2, o2) = lst
                u = (o1[0] - p[0], o1[1] - p[1])
                w = (o2[0] - p[0], o2[1] - p[1])
                nu, nw = math.hypot(*u), math.hypot(*w)
                if nu == 0 or nw == 0:
                    continue
                cosang = max(-1.0, min(1.0, (u[0] * w[0] + u[1] * w[1]) / (nu * nw)))
                change = 180.0 - math.degrees(math.acos(cosang))
                out.append((LN[lid], change, (mm(p[0]), mm(p[1]))))
        return out

    @staticmethod
    def bend_kind(ch):
        if ch < 0.5:
            return 'collinear'
        if abs(ch - 45) <= 0.5:
            return 'b45'
        if abs(ch - 90) <= 0.5:
            return 'b90'
        if ch > 90.5:
            return 'acute'
        return 'other'

    # ------------------------------------------------------------------ routes, detours, bends, critical
    def routes(self):
        rows = []
        bend_cls, bend_layer, len_cls_layer = defaultdict(Counter), defaultdict(Counter), defaultdict(Counter)
        for net, nc in sorted(self.nc.items()):
            bl = self.bends_of(nc)
            c = self.cls(net)
            for lay, ch, _ in bl:
                k = self.bend_kind(ch)
                bend_cls[c][k] += 1
                bend_layer[lay][k] += 1
            for t in nc.tracks:
                len_cls_layer[c][LN[t['lid']]] += mm(math.dist(t['a'], t['b']))
            if nc.zones:
                continue
            rt = self.rc.net_route(nc)
            if rt['pads'] < 2:
                continue
            per_layer = Counter()
            for t in nc.tracks:
                per_layer[LN[t['lid']]] += mm(math.dist(t['a'], t['b']))
            kinds = Counter(self.bend_kind(ch) for _, ch, _ in bl)
            rows.append(dict(net=net, cls=c, pads=rt['pads'], len=r(rt['len']), mst=r(rt['mst']),
                             ratio=r(rt['len'] / rt['mst'], 3) if rt['mst'] else None, vias=rt['vias'], need=rt['need'],
                             layers={k: r(v) for k, v in sorted(per_layer.items())},
                             bends=sum(kinds[k] for k in ('b45', 'b90', 'acute', 'other')),
                             b45=kinds['b45'], b90=kinds['b90']))
        self.route_rows = rows
        self.out['routes'] = rows
        # detour distribution (nets with copper and a non-zero MST)
        rr = [x for x in rows if x['ratio'] is not None and x['len'] > 0]
        ratios = [x['ratio'] for x in rr]
        bins = [(1.0, 1.1), (1.1, 1.25), (1.25, 1.6), (1.6, 2.0), (2.0, 3.0), (3.0, 1e9)]
        hist = {f'{lo}-{hi if hi < 1e8 else "inf"}': sum(1 for v in ratios if (lo <= v < hi) or (lo == 1.0 and v < 1.0))
                for lo, hi in bins}
        tot_len, tot_mst = sum(x['len'] for x in rr), sum(x['mst'] for x in rr)
        two = [x for x in rr if x['pads'] == 2]
        sig = [x for x in rr if x['cls'] not in ('power', 'gnd')]
        self.out['detour'] = dict(
            nets=len(rr), histogram=hist, median=r(pctl(ratios, 0.5), 3), p90=r(pctl(ratios, 0.9), 3),
            max=r(max(ratios), 3) if ratios else None,
            weighted=r(tot_len / tot_mst, 3) if tot_mst else None, excess_mm=r(tot_len - tot_mst, 1),
            len_total=r(tot_len, 1), mst_total=r(tot_mst, 1),
            two_pad_nets=len(two), two_pad_weighted=r(sum(x['len'] for x in two) / sum(x['mst'] for x in two), 3) if two else None,
            signal_weighted=r(sum(x['len'] for x in sig) / sum(x['mst'] for x in sig), 3) if sig else None,
            over_1_6=sum(1 for v in ratios if v > 1.6), over_2=sum(1 for v in ratios if v > 2.0),
            gated_detours=sum(1 for x in rr if x['ratio'] > 1.6 and x['len'] - x['mst'] > 2.0),
            worst=sorted(({k: x[k] for k in ('net', 'cls', 'pads', 'len', 'mst', 'ratio', 'vias')} for x in rr),
                         key=lambda x: -x['ratio'])[:15],
            top_excess=sorted(({k: x[k] for k in ('net', 'cls', 'pads', 'len', 'mst', 'ratio', 'vias')}
                               for x in rr), key=lambda x: -(x['len'] - x['mst']))[:20],
            excess_by_class={c: r(sum(x['len'] - x['mst'] for x in rr if x['cls'] == c), 1)
                             for c in sorted({x['cls'] for x in rr})})
        # bends
        tl = defaultdict(float)
        for c, d in len_cls_layer.items():
            for lay, v in d.items():
                tl[(c, lay)] += v
        tot_bends = Counter()
        for d in bend_cls.values():
            tot_bends.update(d)
        sig_bends = Counter()
        for c, d in bend_cls.items():
            if c not in ('power', 'gnd'):
                sig_bends.update(d)
        sig_len = sum(v for (c, lay), v in tl.items() if c not in ('power', 'gnd'))
        all_len = sum(tl.values())

        def per10(cnt, L):
            n = cnt['b45'] + cnt['b90'] + cnt['acute'] + cnt['other']
            return r(10 * n / L, 3) if L else None
        self.out['bends'] = dict(
            all=dict(tot_bends), signal=dict(sig_bends),
            per_10mm_all=per10(tot_bends, all_len), per_10mm_signal=per10(sig_bends, sig_len),
            b90_share_signal=r(sig_bends['b90'] / max(1, sig_bends['b45'] + sig_bends['b90']), 3),
            per_class={c: dict(d, per_10mm=per10(d, sum(v for (cc, _), v in tl.items() if cc == c)))
                       for c, d in sorted(bend_cls.items())},
            per_layer={lay: dict(d, per_10mm=per10(d, sum(v for (_, ll), v in tl.items() if ll == lay)))
                       for lay, d in sorted(bend_layer.items())},
            two_pad_signal_bends_per_route=r(statistics.mean([x['bends'] for x in rr if x['pads'] == 2 and
                                                               x['cls'] not in ('power', 'gnd')]), 2))
        # critical signal nets
        trans = self.rc.critical_transitions(self.b)
        nog = defaultdict(int)
        alltr = defaultdict(int)
        for net, p, g in trans:
            alltr[net] += 1
            if g is None or g > GND_REACH:
                nog[net] += 1
        crit = [dict(x, layer_changes=alltr.get(x['net'], 0), no_gnd_via=nog.get(x['net'], 0))
                for x in rows if x['cls'] in self.rc.SIGNAL_CRITICAL]
        by_cls = defaultdict(lambda: Counter())
        for x in crit:
            d = by_cls[x['cls']]
            d['nets'] += 1
            d['len'] += x['len']
            d['mst'] += x['mst']
            d['layer_changes'] += x['layer_changes']
            d['no_gnd_via'] += x['no_gnd_via']
        self.out['critical'] = dict(
            nets=len(crit), layer_changes=sum(x['layer_changes'] for x in crit),
            no_gnd_via=sum(x['no_gnd_via'] for x in crit),
            nets_with_layer_change=sum(1 for x in crit if x['layer_changes']),
            len=r(sum(x['len'] for x in crit), 1),
            weighted_ratio=r(sum(x['len'] for x in crit) / max(1e-9, sum(x['mst'] for x in crit)), 3),
            by_class={c: dict(nets=d['nets'], len=r(d['len'], 1), ratio=r(d['len'] / d['mst'], 3) if d['mst'] else None,
                              layer_changes=d['layer_changes'], no_gnd_via=d['no_gnd_via']) for c, d in sorted(by_cls.items())},
            table=sorted(crit, key=lambda x: (x['cls'], x['net'])))
        # buses
        rowmap = {x['net']: x for x in rows}
        bus = {}
        for name, sigs in BUSES.items():
            lens, have = {}, []
            for sig in sigs:
                parts = [rowmap[n] for n in sig if n in rowmap]
                if parts:
                    lens[sig[0]] = sum(x['len'] for x in parts)
                    have += parts
            if not have:
                continue
            bus[name] = dict(signals=sorted(lens), len_total=r(sum(lens.values()), 1),
                             len_min=r(min(lens.values())), len_max=r(max(lens.values())),
                             spread=r(max(lens.values()) / max(1e-9, min(lens.values())), 2),
                             vias=sum(x['vias'] for x in have),
                             layers=sorted({k for x in have for k in x['layers']}),
                             weighted_ratio=r(sum(x['len'] for x in have) / max(1e-9, sum(x['mst'] for x in have)), 3),
                             bends=sum(x['bends'] for x in have))
        self.out['buses'] = bus

    # ------------------------------------------------------------------ planes
    def merged_fill(self, net, lid):
        ps = pcbnew.SHAPE_POLY_SET()
        for z, lays in self.nc[net].zones if net in self.nc else []:
            if lid in lays and z.HasFilledPolysForLayer(lid):
                f = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(lid))
                f.Unfracture()             # fills are stored fractured (keyholes); union them with their holes
                ps.BooleanAdd(f)
        return ps

    def planes(self):
        rows = []
        self.fills = {}
        for net, nc in sorted(self.nc.items()):
            for lid in CU4:
                if not any(lid in lays for _, lays in nc.zones):
                    continue
                ps = self.merged_fill(net, lid)
                self.fills[(net, lid)] = ps
                holes = [abs(ps.Hole(i, j).Area()) / 1e12 for i in range(ps.OutlineCount()) for j in range(ps.HoleCount(i))]
                isl = [ps.Outline(i).Area() / 1e12 for i in range(ps.OutlineCount())]
                per = sum(ps.Outline(i).Length() for i in range(ps.OutlineCount())) / 1e6 + \
                    sum(ps.Hole(i, j).Length() for i in range(ps.OutlineCount()) for j in range(ps.HoleCount(i))) / 1e6
                rows.append(dict(layer=LN[lid], net=net, area=r(ps.Area() / 1e12, 1),
                                 coverage=r(ps.Area() / 1e12 / self.area, 4), islands=ps.OutlineCount(),
                                 smallest_island=r(min(isl), 2) if isl else None,
                                 voids=len(holes), voids_lt1=sum(1 for h in holes if h < 1.0),
                                 voids_1to5=sum(1 for h in holes if 1.0 <= h < 5.0),
                                 voids_ge5=sum(1 for h in holes if h >= 5.0), void_area=r(sum(holes), 1),
                                 largest_void=r(max(holes), 2) if holes else 0, perimeter=r(per, 1)))
        self.out['planes'] = dict(pours=rows)
        # layer summaries
        lay_sum = {}
        for lid in CU4:
            L = [x for x in rows if x['layer'] == LN[lid]]
            lay_sum[LN[lid]] = dict(nets=len(L), regions=sum(x['islands'] for x in L),
                                    copper_area=r(sum(x['area'] for x in L), 1),
                                    coverage=r(sum(x['area'] for x in L) / self.area, 4),
                                    gnd_coverage=r(sum(x['area'] for x in L if x['net'] == 'GND') / self.area, 4),
                                    perimeter=r(sum(x['perimeter'] for x in L), 1),
                                    non_gnd_nets=sorted(x['net'] for x in L if x['net'] != 'GND'))
        self.out['planes']['layers'] = lay_sum
        # In1 voids worth naming (>= 5 mm^2, not a mounting hole) and In1 track copper
        in1 = self.fills.get(('GND', pcbnew.In1_Cu))
        big = []
        if in1 is not None:
            for i in range(in1.OutlineCount()):
                for j in range(in1.HoleCount(i)):
                    h = in1.Hole(i, j)
                    a = abs(h.Area()) / 1e12
                    if a >= 5.0:
                        bb = h.BBox()
                        big.append(dict(area=r(a, 2), bbox=[r(mm(bb.GetLeft())), r(mm(bb.GetTop())),
                                                            r(mm(bb.GetRight())), r(mm(bb.GetBottom()))]))
        self.out['planes']['in1_large_voids'] = sorted(big, key=lambda x: -x['area'])
        # In1 slots: voids at least 2.5 mm long and narrower than 1.6 mm on average (area / length): chains of merged
        # antipads (via columns) or pad rows, which cut the F.Cu reference across their length
        slots = []
        if in1 is not None:
            for i in range(in1.OutlineCount()):
                for j in range(in1.HoleCount(i)):
                    h = in1.Hole(i, j)
                    bb = h.BBox()
                    w_, h_ = mm(bb.GetWidth()), mm(bb.GetHeight())
                    L = max(w_, h_)
                    a = abs(h.Area()) / 1e12
                    if L >= 2.5 and a / L < 1.6:
                        slots.append(dict(length=r(L), mean_width=r(a / L), area=r(a, 2),
                                          bbox=[r(mm(bb.GetLeft())), r(mm(bb.GetTop())), r(mm(bb.GetRight())), r(mm(bb.GetBottom()))]))
        self.out['planes']['in1_slots'] = sorted(slots, key=lambda x: -x['length'])
        # outer GND islands and their stitching
        gnd_pts = [(p, 'via') for p in self.gnd_vias]
        for f in self.b.GetFootprints():
            for p in f.Pads():
                if p.GetNetname() == 'GND' and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                    gnd_pts.append(((p.GetPosition().x, p.GetPosition().y), 'pth'))
        self.gnd_pts = [q for q, _ in gnd_pts]
        outer = {}
        for lid in (pcbnew.F_Cu, pcbnew.B_Cu):
            ps = self.fills.get(('GND', lid))
            if ps is None:
                continue
            counts = []
            for i in range(ps.OutlineCount()):
                one = pcbnew.SHAPE_POLY_SET()
                one.AddOutline(ps.Outline(i))
                for j in range(ps.HoleCount(i)):
                    one.AddHole(ps.Hole(i, j))
                bb = one.BBox()
                n = 0
                for q in self.gnd_pts:
                    if bb.GetLeft() <= q[0] <= bb.GetRight() and bb.GetTop() <= q[1] <= bb.GetBottom() and \
                            one.Collide(pcbnew.VECTOR2I(int(q[0]), int(q[1])), MM(0.15)):
                        n += 1
                counts.append((n, one.Area() / 1e12))
            outer[LN[lid]] = dict(islands=len(counts), with_0=sum(1 for n, _ in counts if n == 0),
                                  with_1=sum(1 for n, _ in counts if n == 1), with_2plus=sum(1 for n, _ in counts if n >= 2),
                                  area_with_le1=r(sum(a for n, a in counts if n <= 1), 1))
        self.out['planes']['outer_gnd_islands'] = outer

    # ------------------------------------------------------------------ reference coverage (length based)
    def reference(self):
        out = {}
        # every pour fill per layer, for naming what lies under an unreferenced sample
        layer_fills = defaultdict(list)
        for (net, lid), ps in self.fills.items():
            layer_fills[lid].append((net, ps))
        layer_tracks = defaultdict(list)
        for t in self.b.GetTracks():
            if t.GetClass() == 'PCB_TRACK':
                a_, b_ = t.GetStart(), t.GetEnd()
                layer_tracks[t.GetLayer()].append((a_.x, a_.y, b_.x, b_.y, t.GetWidth() / 2, t.GetNetname()))
        for name, refs, nets in (('r6', REF_R6, R6_NETS), ('extended', REF_EXT, R6_NETS + EXT_NETS)):
            ref_ps = {}
            for lay, (rlay, rnets) in refs.items():
                ps = pcbnew.SHAPE_POLY_SET()
                for n in rnets:
                    if (n, rlay) in self.fills:
                        ps.BooleanAdd(self.fills[(n, rlay)])
                ref_ps[lay] = ps
            per = defaultdict(lambda: [0.0, 0.0, 0])       # (net, layer) -> [length, unreferenced, crossings]
            under = Counter()
            own = 0.0                                      # unreferenced length within OWN_VIA of a same-net via / PTH
            holes = defaultdict(list)
            for t in self.b.GetTracks():
                if t.GetClass() == 'PCB_VIA' and t.GetNetname() in nets:
                    holes[t.GetNetname()].append((t.GetPosition().x, t.GetPosition().y))
            for f in self.b.GetFootprints():
                for pd in f.Pads():
                    if pd.GetNetname() in nets and pd.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                        holes[pd.GetNetname()].append((pd.GetPosition().x, pd.GetPosition().y))
            for t in self.b.GetTracks():
                if t.GetClass() != 'PCB_TRACK' or t.GetNetname() not in nets or t.GetLayer() not in refs:
                    continue
                a, c = t.GetStart(), t.GetEnd()
                L = mm(t.GetLength())
                if L == 0:
                    continue
                n = max(1, int(math.ceil(L / self.step)))
                prev = None
                key = (t.GetNetname(), LN[t.GetLayer()])
                per[key][0] += L
                rlay = refs[t.GetLayer()][0]
                for k in range(n):
                    f = (k + 0.5) / n
                    p = pcbnew.VECTOR2I(int(a.x + (c.x - a.x) * f), int(a.y + (c.y - a.y) * f))
                    ok = ref_ps[t.GetLayer()].Contains(p, -1, 0, True)
                    if not ok and any(math.hypot(p.x - q[0], p.y - q[1]) <= MM(OWN_VIA) for q in holes[t.GetNetname()]):
                        own += L / n                       # the net's own antipad at its layer change: unavoidable
                    elif not ok:
                        per[key][1] += L / n
                        what = 'void'
                        for fn, fp in layer_fills[rlay]:
                            if fp.Contains(p, -1, 0, True):
                                what = fn
                                break
                        if what == 'void':         # no pour: is another net's track stacked there, or a pour gap?
                            for (ax, ay, bx, by, hw, tn) in layer_tracks[rlay]:
                                if min(ax, bx) - hw <= p.x <= max(ax, bx) + hw and min(ay, by) - hw <= p.y <= max(ay, by) + hw \
                                        and self.rc.pt_seg((p.x, p.y), (ax, ay), (bx, by))[0] <= hw + MM(0.2):
                                    what = 'track(+0.2 mm)'
                                    break
                            else:
                                what = 'gap/void'
                        under[f'{LN[rlay]}:{what}'] += L / n
                    if prev is not None and ok != prev:
                        per[key][2] += 1
                    prev = ok
            tot = sum(v[0] for v in per.values())
            un = sum(v[1] for v in per.values())
            by_net = defaultdict(lambda: [0.0, 0.0, 0])
            for (net, lay), v in per.items():
                for i in range(3):
                    by_net[net][i] += v[i]
            out[name] = dict(length=r(tot, 1), unreferenced=r(un, 1), own_via_antipad=r(own, 1),
                             referenced_share=r(1 - (un + own) / tot, 4) if tot else None,
                             crossings=sum(v[2] for v in per.values()),
                             under_unreferenced={k: r(v, 1) for k, v in sorted(under.items(), key=lambda x: -x[1])},
                             by_net={n: dict(len=r(v[0], 1), unref=r(v[1], 1), crossings=v[2]) for n, v in sorted(by_net.items())},
                             by_net_layer={f'{n} {l}': dict(len=r(v[0], 1), unref=r(v[1], 1), crossings=v[2])
                                           for (n, l), v in sorted(per.items()) if v[1] > 0.05})
        self.out['reference'] = out

    # ------------------------------------------------------------------ stitching
    def stitching(self, raster=0.5):
        pts = [(mm(q[0]), mm(q[1])) for q in self.gnd_pts]
        cell = 3.0
        buckets = defaultdict(list)
        for p in pts:
            buckets[(int(p[0] // cell), int(p[1] // cell))].append(p)
        x0, y0, x1, y1 = self.bbox
        dists, pour_d = [], []
        outer_gnd = [self.fills.get(('GND', pcbnew.F_Cu)), self.fills.get(('GND', pcbnew.B_Cu))]
        worst = (0, None)
        bands = defaultdict(list)
        h = (y1 - y0) / 5
        y = y0 + raster / 2
        while y < y1:
            x = x0 + raster / 2
            while x < x1:
                if self.outline.Contains(pcbnew.VECTOR2I(MM(x), MM(y))):
                    ci, cj = int(x // cell), int(y // cell)
                    best, ring = float('inf'), 0
                    while True:
                        for di in range(-ring, ring + 1):
                            for dj in range(-ring, ring + 1):
                                if max(abs(di), abs(dj)) != ring:
                                    continue
                                for p in buckets.get((ci + di, cj + dj), ()):
                                    best = min(best, math.hypot(p[0] - x, p[1] - y))
                        if best <= ring * cell or ring > 40:
                            break
                        ring += 1
                    dists.append(best)
                    pv = pcbnew.VECTOR2I(MM(x), MM(y))
                    if any(ps is not None and ps.Contains(pv) for ps in outer_gnd):
                        pour_d.append(best)
                    bands[min(4, int((y - y0) // h))].append(best)
                    if best > worst[0]:
                        worst = (best, (round(x, 2), round(y, 2)))
                x += raster
            y += raster
        self.out['stitching'] = dict(
            gnd_vias=len(self.gnd_vias), gnd_pth=len(self.gnd_pts) - len(self.gnd_vias),
            per_cm2=r(len(self.gnd_pts) / (self.area / 100), 2),
            dist_median=r(pctl(dists, 0.5)), dist_p95=r(pctl(dists, 0.95)), dist_max=r(worst[0]), dist_max_at=worst[1],
            share_over_3mm=r(sum(1 for d in dists if d > 3.0) / len(dists), 4),
            outer_pour_points=len(pour_d), outer_pour_p95=r(pctl(pour_d, 0.95)), outer_pour_max=r(max(pour_d) if pour_d else None),
            bands={f'y{r(y0 + k * h, 1)}-{r(y0 + (k + 1) * h, 1)}': dict(p95=r(pctl(v, 0.95)), max=r(max(v)),
                                                                     vias=sum(1 for p in pts if y0 + k * h <= p[1] < y0 + (k + 1) * h))
                   for k, v in sorted(bands.items())})

    # ------------------------------------------------------------------ parts
    def parts(self):
        x0, y0, x1, y1 = self.bbox
        H, W = y1 - y0, x1 - x0
        nb, gx, gy = 5, 4, 10
        side = {}
        for lid, crt, nm in ((pcbnew.F_Cu, pcbnew.F_CrtYd, 'top'), (pcbnew.B_Cu, pcbnew.B_CrtYd, 'bottom')):
            fps = [f for f in self.b.GetFootprints() if f.GetLayer() == lid]
            band_n, band_a = Counter(), Counter()
            grid_n, grid_a = Counter(), Counter()
            tot_a = 0.0
            def rect(xa, ya, xb, yb):
                ps = pcbnew.SHAPE_POLY_SET()
                ps.NewOutline()
                for x, y in ((xa, ya), (xb, ya), (xb, yb), (xa, yb)):
                    ps.Append(MM(x), MM(y))
                return ps

            def clipped(c, box):          # courtyard area inside a rectangle (courtyards clipped, not by centre)
                k = pcbnew.SHAPE_POLY_SET(c)
                k.BooleanIntersection(box)
                return k.Area() / 1e12
            bands_r = [rect(x0, y0 + k * H / nb, x1, y0 + (k + 1) * H / nb) for k in range(nb)]
            cells_r = {(i, j): rect(x0 + i * W / gx, y0 + j * H / gy, x0 + (i + 1) * W / gx, y0 + (j + 1) * H / gy)
                       for i in range(gx) for j in range(gy)}
            for f in fps:
                c = f.GetCourtyard(crt)
                a = c.Area() / 1e12 if c.OutlineCount() else 0.0
                p = f.GetPosition()
                x, y = mm(p.x), mm(p.y)
                k = min(nb - 1, max(0, int((y - y0) / (H / nb))))
                band_n[k] += 1
                g = (min(gx - 1, max(0, int((x - x0) / (W / gx)))), min(gy - 1, max(0, int((y - y0) / (H / gy)))))
                grid_n[g] += 1
                tot_a += a
                if a:
                    bb = c.BBox()
                    for kk, box in enumerate(bands_r):
                        band_a[kk] += clipped(c, box) if bb.GetTop() < MM(y0 + (kk + 1) * H / nb) and \
                            bb.GetBottom() > MM(y0 + kk * H / nb) else 0.0
                    for gg, box in cells_r.items():
                        cb = box.BBox()
                        if bb.GetRight() > cb.GetLeft() and bb.GetLeft() < cb.GetRight() and \
                                bb.GetBottom() > cb.GetTop() and bb.GetTop() < cb.GetBottom():
                            grid_a[gg] += clipped(c, box)
            cell_a = (W / gx) * (H / gy)
            band_area = W * H / nb
            util = [grid_a[(i, j)] / cell_a for j in range(gy) for i in range(gx)]
            side[nm] = dict(parts=len(fps), courtyard_area=r(tot_a, 1), utilisation=r(tot_a / self.area, 3),  # courtyards may overlap pads of others: a sum, not a union
                            per_cm2=r(len(fps) / (self.area / 100), 2),
                            bands={f'y{r(y0 + k * H / nb, 1)}-{r(y0 + (k + 1) * H / nb, 1)}':
                                   dict(parts=band_n[k], util=r(band_a[k] / band_area, 3)) for k in range(nb)},
                            grid_util_max=r(max(util), 3), grid_util_sd=r(statistics.pstdev(util), 3),
                            grid_util=[[r(grid_a[(i, j)] / cell_a, 2) for i in range(gx)] for j in range(gy)],
                            grid_parts=[[grid_n[(i, j)] for i in range(gx)] for j in range(gy)])
        self.out['parts'] = side

    # ------------------------------------------------------------------ scorecard (geometric rows)
    def scorecard(self):
        o = self.out
        rows = dict(
            S1_signal_track_mm=o['tracks']['signal'],
            S2_total_track_mm=o['tracks']['total'],
            S3_signal_vias=o['vias']['signal'],
            S4_signal_layer_change_vias=o['vias']['signal_layer_change'],
            S5_power_vias_non_gnd=o['vias']['power'],
            S6_detour_weighted=o['detour']['weighted'],
            S7_detour_excess_mm=o['detour']['excess_mm'],
            S8_nets_ratio_over_1_6=o['detour']['over_1_6'],
            S9_nets_ratio_over_2=o['detour']['over_2'],
            S10_bends_per_10mm_signal=o['bends']['per_10mm_signal'],
            S11_bends_per_two_pad_signal_route=o['bends']['two_pad_signal_bends_per_route'],
            S12_critical_layer_changes=o['critical']['layer_changes'],
            S13_critical_layer_changes_no_gnd_via=o['critical']['no_gnd_via'],
            S14_critical_weighted_ratio=o['critical']['weighted_ratio'],
            S15_in2_signal_track_mm=r(sum(v.get('In2.Cu', 0) for c, v in o['tracks']['per_class_layer'].items()
                                          if c not in ('power', 'gnd')), 1),
            S16_in1_track_mm=r(o['tracks']['per_layer'].get('In1.Cu', 0), 1),
            S17_route_mst_total_mm=o['detour']['mst_total'],
            S18_track_segments=o['inventory']['segments'],
            P1_in1_gnd_coverage=o['planes']['layers']['In1.Cu']['gnd_coverage'],
            P2_in1_gnd_islands=next((x['islands'] for x in o['planes']['pours'] if x['layer'] == 'In1.Cu' and x['net'] == 'GND'), None),
            P3_in1_large_voids=len(o['planes']['in1_large_voids']),
            P3b_in1_slots=len(o['planes']['in1_slots']),
            P4_in2_regions=o['planes']['layers']['In2.Cu']['regions'],
            P5_in2_nets=o['planes']['layers']['In2.Cu']['nets'],
            P6_in2_perimeter_mm=o['planes']['layers']['In2.Cu']['perimeter'],
            P7_outer_gnd_islands_le1_via=sum(v['with_0'] + v['with_1'] for v in o['planes']['outer_gnd_islands'].values()),
            P8_gnd_stitch_per_cm2=o['stitching']['per_cm2'],
            P9_gnd_dist_p95_mm=o['stitching']['dist_p95'],
            P10_gnd_dist_max_mm=o['stitching']['dist_max'],
            P11_outer_gnd_pour_dist_p95_mm=o['stitching']['outer_pour_p95'],
            R1_ref_r6_unreferenced_mm=o['reference']['r6']['unreferenced'],
            R2_ref_r6_referenced_share=o['reference']['r6']['referenced_share'],
            R3_ref_ext_unreferenced_mm=o['reference']['extended']['unreferenced'],
            R4_ref_ext_crossings=o['reference']['extended']['crossings'],
            Q1_top_utilisation=o['parts']['top']['utilisation'],
            Q2_bottom_utilisation=o['parts']['bottom']['utilisation'],
            Q3_grid_util_max=max(o['parts']['top']['grid_util_max'], o['parts']['bottom']['grid_util_max']))
        o['scorecard'] = rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board')
    ap.add_argument('--tools', default=DEFAULT_TOOLS)
    ap.add_argument('--json')
    ap.add_argument('--step', type=float, default=0.05, help='reference sampling step along track centre lines (mm)')
    a = ap.parse_args()
    sys.path.insert(0, str(Path(a.tools).resolve()))
    rc = importlib.import_module('route_check')
    b = pcbnew.LoadBoard(a.board)
    unfilled = [z.GetZoneName() or z.GetNetname() for z in b.Zones() if not z.GetIsRuleArea() and not z.IsFilled()]
    if unfilled:
        print(f'[survey] WARNING: unfilled zones {unfilled}: plane, reference and stitching rows are wrong; refill and save '
              f'the board first', file=sys.stderr)
    s = Survey(b, rc, a.step)
    for stage in ('inventory', 'tracks', 'vias', 'routes', 'planes', 'reference', 'stitching', 'parts', 'scorecard'):
        getattr(s, stage)()
        print(f'[survey] {stage} done', file=sys.stderr, flush=True)
    s.out['meta'] = dict(board=str(Path(a.board).resolve()), tools=str(Path(a.tools).resolve()), step=a.step)
    txt = json.dumps(s.out, indent=1)
    if a.json:
        Path(a.json).write_text(txt + '\n')
    for k, v in s.out['scorecard'].items():
        print(f'{k:42s} {v}')


if __name__ == '__main__':
    main()
