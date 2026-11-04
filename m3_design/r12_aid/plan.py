#!/usr/bin/env python3
"""R12 routing drafting aid, step 3 (D-R12-26): the routing plan (net widths, order, fixed necks, plane fan-outs)
and the driver that runs route.py's search over it and writes m3_design/r12_routes.tsv. Not part of the build.

usage: python3 m3_design/r12_aid/plan.py GEOMETRY.json OUT.tsv --lib astar.so --length 90 [--report R.json]
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import route as R  # noqa: E402

PLANES = {'GND': 'In1', '3V3': 'In2', 'RAW_PROTECTED': 'In2', '3V3A': 'In2', 'PORT_4V8': 'In2'}
PLANES_TSV = Path(__file__).resolve().parents[1] / 'r12_planes.tsv'
# plane-net pads joined on F first, then one of them taken to the island (D-R12-22)
CLUSTERS = {'3V3A': (('U1', 'H1'), ('C21', '1'), ('C22', '1')), 'PORT_4V8': (('L400', '2'), ('C406', '1'), ('R400', '1'))}
# widths (mm): fire path and battery copper per IPC-2152 on 1 oz outer copper (stageC.md section 3), signals 0.1 at
# U1 (the 0.8 mm-pitch channel width), 0.2 elsewhere
WIDTH = {'BAT_IN': 0.8, 'RAW_PROTECTED': 0.8, 'BAT_DAMP': 0.8, 'RAW_ACT': 0.8, 'ACT_FET_S': 0.8, 'PYRO1_IGN': 0.8,
         'PYRO1_OUT': 0.8, 'VLOGIC': 0.5, 'CAM_5V': 0.6, 'CAM_SW': 0.8, 'PORT_SW': 0.8, 'SW_NODE': 0.8,
         'PORT_4V8': 0.5, 'VBUS': 0.5, '3V3A': 0.3, 'VCAP1': 0.2, 'VCAP2': 0.2, 'BST': 0.3, 'PORT_BST': 0.3,
         'CAM_BST': 0.3}
FANOUT_W = 0.3
# route_check extra_vias: a net without a pour may use at most 2 vias (every R12 pad is on F, so it needs none)
VIA_BUDGET = 2
# the fire path stays on F.Cu with no series via (stage A constraint; S-8 needs no pyro barrel there)
F_ONLY = {'BAT_IN', 'PYRO1_OUT', 'PYRO1_IGN', 'RAW_ACT', 'ACT_FET_S'}
POWER_ORDER = ('BAT_IN', 'PYRO1_OUT', 'PYRO1_IGN', 'RAW_ACT', 'ACT_FET_S', 'RAW_PROTECTED', 'SW_NODE', 'PORT_SW',
               'CAM_SW', 'BAT_DAMP', 'VLOGIC', 'CAM_5V', 'PORT_4V8', 'VBUS', '3V3A', 'VCAP1', 'VCAP2')
CRITICAL_PARTNER = ('PYRO1_', 'ARM1_', 'HSE_', 'USB_D', 'QSPI_', 'SPI1_', 'IMU_CS', 'SD_', 'GPS_', 'RADIO_', 'AUX_',
                    'CAM_MCU_', 'CAM_TX', 'CAM_RX', 'CAM_PWR_EN')
SLOW = {'VLOGIC_SENSE', 'CAM_5V_SENSE', 'ACT_EN', 'ACT_EN_MCU', 'ACT_DRV', 'ACT_GATE', 'BAT_ENABLE', 'BAT_SW_SOURCE',
        'BAT_SW_RETURN', 'PYRO1_CONT', 'PYRO1_CONT_MID', 'ARM1_SENSE', 'ARM1_SENSE_MID', 'CAM_PWR_EN'}
# fixed necks into U9's 0.3 mm bars (TPS25947 RPW: pins 5 / 6 are 0.3 mm wide between 0.2 mm gaps; stageC.md
# section 4): (net, layer, width, points, terminal at the wide end with its allowed arrival directions)
NECKS = (('BAT_IN', 'F', 0.3, [(17.0, 15.1), (14.9, 15.1)], ((14.9, 15.1), (1 | 2 | 128))),
         ('RAW_PROTECTED', 'F', 0.3, [(17.0, 15.6), (19.4, 15.6)], None))


WIDTHS = (0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.8, 1.0)      # r12_route.WIDTHS


def limit_w(p, w):
    lim = min(w, 0.8 * p['minor'])
    return max([s for s in WIDTHS if s <= lim + 1e-9] or [0.1])


import re
_CRIT = [r'^(?!(?:PYRO1_CONT|ARM1_SENSE)_MCU$)(PYRO1_|ARM1_|ACT_(GATE|DRV|EN)$|ACT_EN_MCU$|BAT_ENABLE$|BAT_SW_(SOURCE|RETURN)$)',
         r'^HSE_', r'^USB_D[PM]$', r'^(QSPI_|SPI1_|IMU_CS$)|^SD_(SCK|MISO|MOSI|CS|DAT[12])$',
         r'^((GPS|RADIO|AUX)_(TX|RX)_(MCU|WIRE)|CAM_(TX|RX)_(WIRE|BUFFER)|CAM_MCU_(TX|RX))$', r'^CAM_(PWR_EN|FAULT_N|UART_OE)$',
         r'^PORT_', r'^(GPS_|RADIO_|CAM_)\w*(V[0-9]*|SUPPLY|SW|BST|INPUT|POWER|LIMITED)$',
         r'^(3V3|3V3A|3V3_GNSS|3V3_RADIO|VLOGIC|VBUS|USB_LIMITED|BAT_IN|BAT_DAMP|RAW_PROTECTED|RAW_ACT|CAM_5V|'
         r'CAM_INPUT_LIMITED|CAM_IO_3V3|SW_NODE|CAM_SW|BST|CAM_BST|VCAP1|VCAP2|ACT_FET_S|GND)$']


def crit_class(net):
    """route_check's critical classes (R10_CLASSES): hygiene (extra_vias, detour) is gated only on these."""
    return any(re.match(p, net) for p in _CRIT)


def critical(net):
    return net.startswith(CRITICAL_PARTNER) and net not in SLOW


class Plan:
    def __init__(self, geo, lib, length):
        self.b = R.Board(geo, length)
        self.b.load_planes(PLANES_TSV)
        self.r = R.Router(self.b, lib)
        self.by_net = {}
        for p in self.b.pads:
            if not p['net'].startswith('~'):
                self.by_net.setdefault(p['net'], []).append(p)
        self.done = {}            # net -> list of connected pad keys
        self.terms = self.r.terms  # net -> extra goal nodes (necks)
        self.fail = []
        self.queue = []
        self.ripped = {}
        self.rip_pairs = set()
        self.rips, self.max_rips = 0, 900

    def bga_setup(self):
        import numpy as np
        b = self.b
        u1 = [p for p in b.pads if p['ref'] == 'U1']
        cx = sum(p['x'] for p in u1) / len(u1)
        cy = sum(p['y'] for p in u1) / len(u1)
        X, Y = np.meshgrid(b.xs, b.ys)
        self.X, self.Y = X, Y
        self.bga = (np.abs(X - cx) <= 4.0 + 1e-6) & (np.abs(Y - cy) <= 4.0 + 1e-6)
        self.ring = {}
        for p in u1:
            r, c = 'ABCDEFGHJK'.index(p['num'][0]), int(p['num'][1:]) - 1
            self.ring[p['num']] = min(r, c, 9 - r, 9 - c)

    def escapes(self):
        """U1's fan-out, fixed before any routing (D-R12-02; stageC.md section 2): a ring-1 signal ball leaves on F.Cu
        straight out to 0.8 mm past the outer ball row; a ring-2 signal ball goes diagonally to the channel between two
        ring-1 balls and straight out the same way; every other used ball (rings 3-5, and every GND / 3V3 / 3V3A /
        VCAP ball) takes a dog-bone via at a free interstitial site next to it. The stub end (or the via) is the net's
        terminal; B.Cu under the field carries only the dog-bone nets."""
        b = self.b
        u1 = {p['num']: p for p in b.pads if p['ref'] == 'U1'}
        cx = sum(p['x'] for p in u1.values()) / len(u1)
        cy = sum(p['y'] for p in u1.values()) / len(u1)
        self.u1c = (cx, cy)
        rows = 'ABCDEFGHJK'
        pos = lambda r, c: (round(cx + (c - 5.5) * 0.8, 4), round(cy + (r - 5.5) * 0.8, 4))   # r, c 1-based, may be .5
        used_sites, used_ch = set(), set()
        self.u1term = {}
        self.dogbone_nets = set()

        def target(net):
            ps = [p for p in self.by_net.get(net, []) if p['ref'] != 'U1']
            if not ps:
                return (cx, cy)
            return (sum(p['x'] for p in ps) / len(ps), sum(p['y'] for p in ps) / len(ps))
        # side: (dr, dc) outward unit in ball index units; N = (-1, 0)
        SIDES = {'N': (-1, 0), 'S': (1, 0), 'W': (0, -1), 'E': (0, 1)}
        DIR = {'E': 0, 'N': 2, 'W': 4, 'S': 6}            # astar dir of the outward heading
        balls = []
        for num, p in u1.items():
            if p['net'].startswith('~'):
                continue
            r, c = rows.index(num[0]) + 1, int(num[1:])
            ring = min(r - 1, c - 1, 10 - r, 10 - c)
            balls.append((ring, num, r, c, p))
        plane = lambda n: n in ('GND', '3V3', 'VCAP1', 'VCAP2')

        def pick_side(r, c, ring, net):
            cands = [s for s, (dr, dc) in SIDES.items()
                     if (dr == -1 and r == 1 + ring) or (dr == 1 and r == 10 - ring) or (dc == -1 and c == 1 + ring)
                     or (dc == 1 and c == 10 - ring)]
            tx, ty = target(net)
            bx, by = pos(r, c)
            return max(cands, key=lambda s: (tx - bx) * SIDES[s][1] + (ty - by) * SIDES[s][0])
        stubs = 0
        # ring 1 signals: straight out
        for ring, num, r, c, p in sorted(balls):
            if ring == 0 and not plane(p['net']):
                s = pick_side(r, c, 0, p['net'])
                dr, dc = SIDES[s]
                a = pos(r, c)
                e = pos(r + dr, c + dc)
                self.fixed(p['net'], 'F', 0.1, [a, e])
                self.u1term[p['net']] = (e, DIR[s])
                self.reserve(p['net'], e, (dc, dr))
                stubs += 1
        # ring 2 signals: diagonal to a free channel, then straight out
        for ring, num, r, c, p in sorted(balls, key=lambda x: (x[0], x[1])):
            if ring == 1 and not plane(p['net']):
                s = pick_side(r, c, 1, p['net'])
                dr, dc = SIDES[s]
                tx, ty = target(p['net'])
                bx, by = pos(r, c)
                if dr:      # north / south: channel at c +- 0.5
                    opts = sorted((c - 0.5, c + 0.5), key=lambda cc: abs(pos(r, cc)[0] - tx))
                    ch = next((cc for cc in opts if (s, cc) not in used_ch), None)
                    site = (r + dr * 0.5, ch) if ch is not None else None
                else:
                    opts = sorted((r - 0.5, r + 0.5), key=lambda rr: abs(pos(rr, c)[1] - ty))
                    ch = next((rr for rr in opts if (s, rr) not in used_ch), None)
                    site = (ch, c + dc * 0.5) if ch is not None else None
                if site is None or site in used_sites:
                    raise SystemExit(f'escape: no channel for {num}')
                used_ch.add((s, ch))
                used_sites.add(site)
                used_sites.add((site[0] + dr, site[1] + dc))       # the straight part crosses the outer site
                end = (site[0] + dr * 1.5, site[1] + dc * 1.5)
                self.fixed(p['net'], 'F', 0.1, [pos(r, c), pos(*site), pos(*end)])
                self.u1term[p['net']] = (pos(*end), DIR[s])
                self.reserve(p['net'], pos(*end), (dc, dr))
                stubs += 1
        # dog-bones: inner signals first (toward their target), then the plane / VCAP balls
        order = [x for x in balls if x[0] >= 2 and not plane(x[4]['net'])] + [x for x in balls if plane(x[4]['net'])]
        for ring, num, r, c, p in order:
            tx, ty = target(p['net'])
            bx, by = pos(r, c)
            cands = [(r + dr, c + dc) for dr in (-0.5, 0.5) for dc in (-0.5, 0.5)]
            lo, hi = (0.5, 10.5) if ring == 0 else (1.5, 9.5)      # an outer ball may take a site just outside
            cands = [s for s in cands if s not in used_sites and lo <= s[0] <= hi and lo <= s[1] <= hi]
            if not cands:
                raise SystemExit(f'escape: no dog-bone site for {num}')
            if plane(p['net']) and p['net'] not in ('VCAP1', 'VCAP2'):
                site = min(cands, key=lambda s: (abs(s[0] - 5.5) + abs(s[1] - 5.5), s))     # inward first
            else:
                site = max(cands, key=lambda s: (pos(*s)[0] - bx) * (tx - bx) + (pos(*s)[1] - by) * (ty - by))
            used_sites.add(site)
            w = 0.3 if plane(p['net']) and p['net'] not in ('VCAP1', 'VCAP2') else (0.2 if plane(p['net']) else 0.1)
            v = pos(*site)
            self.fixed(p['net'], 'F', w, [pos(r, c), v])
            b.add_via(p['net'], v[0], v[1])
            p['fanned'] = True
            if not plane(p['net']) or p['net'] in ('VCAP1', 'VCAP2', '3V3A'):
                self.u1term[p['net']] = (v, None)
                self.dogbone_nets.add(p['net'])
        print('escapes:', stubs, 'stubs,', len(used_sites), 'sites', flush=True)

    def reserve(self, net, e, d, length=1.0):
        """Keep the first `length` mm past a stub end clear of other nets (drafting only: the corridor counts as the
        net's copper in the clearance field, not as a track)."""
        import numpy as np
        b = self.b
        f = (round(e[0] + d[0] * length, 4), round(e[1] + d[1] * length, 4))
        sl, X, Y = b.region(min(e[0], f[0]), min(e[1], f[1]), max(e[0], f[0]), max(e[1], f[1]))
        dd = (b.seg_dist(X, Y, e, f) - 0.05).astype(np.float32)
        b.merge(0, sl, dd, b.nid(net))

    def fixed(self, net, layer, w, pts):
        for a, c in zip(pts, pts[1:]):
            self.b.add_track(net, layer, w, a, c)

    def near(self, pads, r=0.65):
        import numpy as np
        m = np.zeros(self.bga.shape, bool)
        for p in pads:
            m |= np.hypot(self.X - p['x'], self.Y - p['y']) <= r
        return m

    def masks(self, net):
        """Escape discipline under U1 (D-R12-02): balls in rings 3-5 leave by a dog-bone via next to the ball (F.Cu
        inside the field only round the own ball), rings 1-2 leave on F.Cu between the outer balls; B.Cu under the field
        belongs to the dog-bone escapes, and no other net enters the field."""
        import numpy as np
        none = np.zeros(self.bga.shape, bool)
        return [self.bga, none if net in self.dogbone_nets else self.bga]

    def width(self, net, touches_u1):
        if net in WIDTH:
            return WIDTH[net]
        return 0.1 if touches_u1 else 0.2

    def necks(self):
        for p in self.b.pads:
            if p['ref'] == 'U9' and p['num'] in ('5', '6'):
                p['fanned'] = True                      # reached only through its neck
        for net, layer, w, pts, term in NECKS:
            for a, c in zip(pts, pts[1:]):
                self.b.add_track(net, layer, w, a, c)
            if term:
                (x, y), m = term
                self.terms.setdefault(net, []).append((0, int(round(x / R.G)), int(round(y / R.G)), m))

    def connect_tree(self, net, maxexp=3_000_000, subset=None):
        pads = [p for p in self.by_net.get(net, []) if subset is None or (p['ref'], p['num']) in subset]
        if len(pads) < 2 and not self.terms.get(net):
            return
        u1 = [p for p in pads if p['ref'] == 'U1']
        w0 = self.width(net, bool(u1))
        connected = []
        rest = [p for p in pads if p['ref'] != 'U1']          # U1 last: the local cluster on F first (via budget)
        if net in getattr(self, 'u1term', {}):
            (tx, ty), d = self.u1term[net]
            i, j = int(round(tx / R.G)), int(round(ty / R.G))
            if d is None:
                pass                                           # a dog-bone via: own via goal on both layers
            else:
                inward = (d + 4) % 8
                m = (1 << inward) | (((1 << ((inward + 1) % 8)) | (1 << ((inward + 7) % 8))) << 8)
                self.terms.setdefault(net, [])
                if not any(q[:3] == (0, i, j) for q in self.terms[net]):
                    self.terms[net].append((0, i, j, m))
            connected.extend(u1)
            u1 = []
        if self.terms.get(net) or connected:
            pass
        elif rest:
            cx = sum(p['x'] for p in rest) / len(rest)
            cy = sum(p['y'] for p in rest) / len(rest)
            first = min(rest, key=lambda p: (round(-p['minor'], 1), math.hypot(p['x'] - cx, p['y'] - cy)))
            connected.append(first); rest.remove(first)
            for q in first.get('group', []):
                if q in rest:
                    rest.remove(q); connected.append(q)
        else:
            connected.append(u1[0])
        # neck-connected pads count as connected (U9.5 / U9.6 / C82.1)
        for p in list(rest):
            if p['ref'] == 'U9' and p['num'] in ('5', '6'):
                connected.append(p); rest.remove(p)
            if net == 'RAW_PROTECTED' and p['ref'] == 'C82' and p['num'] == '1':
                connected.append(p); rest.remove(p)
        tail = [p for p in u1 if p not in connected]
        connected_goals_u1 = [p for p in connected if p['ref'] == 'U1']
        while rest or tail:
            if not rest:
                rest, tail = tail, []
            def dist(p):
                cs = [(c['x'], c['y']) for c in connected] + [(t[1] * R.G, t[2] * R.G) for t in self.terms.get(net, [])] \
                    + [(v[1], v[2]) for v in self.b.vias if v[0] == net]
                return min(math.hypot(p['x'] - x, p['y'] - y) for x, y in cs)
            p = min(rest, key=dist)
            goals = []
            for c in connected:
                if c['ref'] == 'U1' and net in getattr(self, 'u1term', {}):
                    continue
                if c['ref'] == 'U9' and c['num'] in ('5', '6'):
                    continue                                   # reached only through its neck (NECKS)
                goals += self.r.pad_nodes(c)
            goals += self.r.via_nodes(net)
            goals += self.terms.get(net, [])
            nearest = min(connected, key=lambda c: math.hypot(p['x'] - c['x'], p['y'] - c['y'])) if connected else p
            w = limit_w(p, w0)
            if connected and nearest['ref'] not in ('U9', 'U1'):
                w = min(w, limit_w(nearest, w0))
            starts = [n[:3] for n in self.r.pad_nodes(p)]
            if p.get('group'):        # a linked group (USB pin pairs): its link vias are terminals too
                for (vn, vx, vy) in self.b.vias:
                    if vn == net and any(math.hypot(vx - q['x'], vy - q['y']) < 3.0 for q in p['group']):
                        i, j = int(round(vx / R.G)), int(round(vy / R.G))
                        starts += [(0, i, j), (1, i, j)]
            layers = ('F',) if net in F_ONLY else ('F', 'B')
            ok = False
            for margin in (4.0, 10.0, 30.0):
                win = R.window_of([(0, n[1], n[2]) for n in starts] + [(0, g[1], g[2]) for g in goals
                                  if math.hypot(g[1] * R.G - p['x'], g[2] * R.G - p['y']) < dist(p) + 3], margin)
                used = sum(1 for v in self.b.vias if v[0] == net)
                path = self.r.search(net, w, starts, goals, win, layers=layers, maxexp=maxexp,
                                     maxvia=max(0, (VIA_BUDGET if crit_class(net) else 6) - used), extra_block=self.masks(net))
                if path:
                    self.r.commit(net, w, path)
                    ok = True
                    break
            if not ok:
                maxvia = max(0, (VIA_BUDGET if crit_class(net) else 6) - sum(1 for v in self.b.vias if v[0] == net))
                ok = self.ripup(net, w, starts, goals, layers=layers, maxvia=maxvia, extra_block=self.masks(net))
            if not ok:
                self.fail.append((net, p['ref'] + '.' + p['num'], [f'status {self.r.last_status}']))
                print('  FAIL', net, p['ref'], p['num'], self.r.last_status, flush=True)
            connected.append(p)
            rest.remove(p)
            for q in p.get('group', []):
                if q in rest:
                    rest.remove(q)
                    connected.append(q)

    def ripup(self, net, w, starts, goals, layers, maxvia, extra_block=None, via_block=None, goal_via=False,
              vias=True):
        """A connection that fails among the routed copper: find a path against the fixed copper only, rip the units
        whose copper it crosses (never the fixed fan-out), re-route this connection, and queue the ripped units."""
        if self.rips >= self.max_rips:
            return False
        win = R.window_of([(0, n[1], n[2]) for n in starts] + [(0, g[1], g[2]) for g in goals], 12.0) if goals else \
            R.window_of([(0, n[1], n[2]) for n in starts], 6.0)
        path = self.r.search(net, w, starts, goals, win, layers=layers, maxvia=maxvia, extra_block=extra_block,
                             via_block=via_block, goal_via=goal_via, vias=vias, base=True)
        if not path:
            return False
        bl = R.blockers(self.b, net, w, path) - {self.b.unit}
        bl = {u for u in bl if self.ripped.get(u, 0) < 4 and (u, self.b.unit) not in self.rip_pairs}
        if not bl or len(bl) > 6:
            return False
        for u in bl:
            self.ripped[u] = self.ripped.get(u, 0) + 1
            self.rip_pairs.add((self.b.unit, u))
        self.rips += 1
        self.b.remove_units(bl)
        for u in bl:
            self.unrouted(u)
        print(f'   rip {sorted(bl)} for {net}', flush=True)
        path = self.r.search(net, w, starts, goals, win, layers=layers, maxvia=maxvia, extra_block=extra_block,
                             via_block=via_block, goal_via=goal_via, vias=vias)
        if not path:
            return False
        end_via = goal_via and not any(v[0] == net and abs(v[1] - path[-1][1] * R.G) < 1e-6
                                       and abs(v[2] - path[-1][2] * R.G) < 1e-6 for v in self.b.vias) \
            and not self.on_pad(net, path[-1])
        self.r.commit(net, w, path, end_via=end_via)
        return True

    def unrouted(self, u):
        """Put a ripped unit back on the queue (right after the current one)."""
        if u.startswith('fan:'):
            _, net, key = u.split(':', 2)
            for p in self.by_net.get(net, []):
                if f"{p['ref']}.{p['num']}" == key:
                    p['fanned'] = False
        self.queue.insert(0, u)

    def run_unit(self, u):
        self.b.unit = u
        if u.startswith('fan:'):
            _, net, key = u.split(':', 2)
            p = next(p for p in self.by_net[net] if f"{p['ref']}.{p['num']}" == key)
            self.fanout_pad(net, p)
        elif u.startswith('cluster:'):
            net = u.split(':', 1)[1]
            sub = CLUSTERS[net]
            self.connect_tree(net, subset=sub)
            pads = [p for p in self.by_net[net] if (p['ref'], p['num']) in sub]
            for p in pads[1:]:
                p['fanned'] = True
            lead = next(p for p in pads if p['ref'] != 'U1')
            for p in pads:
                if p['ref'] == 'U1':
                    p['fanned'] = True
            self.b.unit = u
            lead['fanned'] = False
            self.fanout_pad(net, lead)
        else:
            self.connect_tree(u)

    def usb(self):
        """J3's pin pairs (USB-C rows A / B, rotated 90): DP B6 / A6 and DM A7 / B7 are interleaved at 0.5 mm, so each
        pair is linked on B.Cu through two vias just west of the pads (staggered 0.6 mm), and VBUS B4A9 / A4B9 through
        two vias further west; the rest of each net is routed on F (stageC.md section 4)."""
        pads = {p['num']: p for p in self.b.pads if p['ref'] == 'J3'}
        X1, X2, XV = 38.0, 37.4, 36.6
        for net, (pa, xa), (pb, xb) in (('USB_DP', ('B6', X1), ('A6', X1)), ('USB_DM', ('A7', X2), ('B7', X2)),
                                        ('VBUS', ('B4A9', XV), ('A4B9', XV))):
            w = 0.1 if net != 'VBUS' else 0.5
            ya, yb = pads[pa]['y'], pads[pb]['y']
            self.fixed(net, 'F', w, [(round(pads[pa]['x'], 3), ya), (xa, ya)])
            self.fixed(net, 'F', w, [(round(pads[pb]['x'], 3), yb), (xb, yb)])
            self.fixed(net, 'B', w if net != 'VBUS' else 0.5, [(xa, ya), (xb, yb)])
            self.b.add_via(net, xa, ya)
            self.b.add_via(net, xb, yb)
            self.link(pads[pa], pads[pb])

    def on_pad(self, net, node):
        l, i, j = node
        for p in self.by_net.get(net, []):
            if (i, j) in self.b.inside[p['key']].get(R.LAYERS[l], ()):
                return True
        return False

    def link(self, a, b_):
        g = a.get('group') or b_.get('group') or [a]
        for q in (a, b_):
            if q not in g:
                g.append(q)
            q['group'] = g

    def join(self, net, a, b_, w=0.3):
        """A same-net link on F between two pads of one part (LPS28DFW pad 7 to pad 5, D-R12-25)."""
        pa = next(p for p in self.by_net[net] if (p['ref'], p['num']) == a)
        pb = next(p for p in self.by_net[net] if (p['ref'], p['num']) == b_)
        starts = [q[:3] for q in self.r.pad_nodes(pa, layers=('F',))]
        goals = self.r.pad_nodes(pb, layers=('F',))
        win = R.window_of([(0, s[1], s[2]) for s in starts + [g[:3] for g in goals]], 2.0)
        path = self.r.search(net, w, starts, goals, win, layers=('F',), vias=False)
        if not path:
            self.fail.append((net, f'join {a} {b_}'))
            print('  FAIL join', net, a, b_)
            return
        self.r.commit(net, w, path)
        self.link(pa, pb)

    def fanout(self, net, refs=None):
        for p in self.by_net.get(net, []):
            if refs and p['ref'] not in refs:
                continue
            self.fanout_pad(net, p)

    def fanout_pad(self, net, p):
        """A linked group (joined pads) needs one fan-out: try its members in turn."""
        group = p.get('group') or [p]
        if any(q.get('fanned') for q in group):
            p['fanned'] = True
            return
        for q in sorted(group, key=lambda q: (q is not p, -q['minor'])):
            nf = len(self.fail)
            self.fanout_one(net, q)
            if len(self.fail) == nf:
                for q2 in group:
                    q2['fanned'] = True
                return
            if q is not group[-1] and len(group) > 1:
                self.fail = self.fail[:nf]

    def fanout_one(self, net, p):
        if True:
            if p['attr'] == 'pth' or p.get('fanned'):
                return
            n = 2 if (p['minor'] >= 1.0) else 1
            w = limit_w(p, FANOUT_W)
            eb, vb = None, None
            if p['ref'] == 'U1':
                import numpy as np
                if self.ring[p['num']] >= 2:      # dog-bone to an adjacent interstitial site
                    eb = [self.bga & ~self.near([p]), np.zeros(self.bga.shape, bool)]
                    vb = ~self.near([p], 0.6)
                else:                              # out between the outer balls on F, the via outside the field
                    vb = self.bga
            elif True:
                vb = self.bga
            import numpy as np
            vb = (vb if vb is not None else np.zeros(self.bga.shape, bool)) | ~self.b.region_ok(net)
            for _ in range(n):
                starts = [q[:3] for q in self.r.pad_nodes(p, layers=('F',))]
                if not starts:
                    continue
                win = R.window_of([(0, s[1], s[2]) for s in starts], 3.0)
                goals = [g for g in self.r.via_nodes(net) if g[0] == 0] if n == 1 else []
                if n == 1 and net == 'GND':        # a pad may share a neighbour's fan-out (pad to pad, then its via)
                    for q in self.by_net[net]:
                        if q is not p and q.get('fanned') and q['ref'] != 'U1' and \
                                math.hypot(q['x'] - p['x'], q['y'] - p['y']) < 2.5:
                            goals += self.r.pad_nodes(q, layers=('F',))
                path = None
                for margin, lay, mv in ((3.0, ('F',), 0), (6.0, ('F',), 0), (8.0, ('F', 'B'), 1),
                                        (70.0, ('F', 'B'), 1)):
                    win = R.window_of([(0, s[1], s[2]) for s in starts], margin)
                    path = self.r.search(net, w, starts, goals, win, layers=lay, vias=mv > 0, goal_via=True,
                                         extra_block=eb if eb is not None else self.masks(net), via_block=vb,
                                         maxvia=mv)
                    if path:
                        break
                if not path:
                    if self.ripup(net, w, starts, goals, layers=('F',), maxvia=0, extra_block=eb, via_block=vb,
                                  goal_via=True, vias=False):
                        continue
                    self.fail.append((net, p['ref'] + '.' + p['num'] + ' fanout'))
                    print('  FAIL fanout', net, p['ref'], p['num'], flush=True)
                    break
                end = path[-1]
                exist = any(v[0] == net and abs(v[1] - end[1] * R.G) < 1e-6 and abs(v[2] - end[2] * R.G) < 1e-6
                            for v in self.b.vias) or self.on_pad(net, end)
                self.r.commit(net, w, path, end_via=not exist)
            p['fanned'] = True

    def partners(self):
        """A GND via within 1.5 mm of every layer change of a critical signal net (AGENTS section 3)."""
        import numpy as np
        b = self.b
        k = b.nid('GND')
        added = 0
        for (net, x, y) in list(b.vias):
            if not critical(net):
                continue
            if any(n == 'GND' and math.hypot(vx - x, vy - y) <= 1.5 for n, vx, vy in b.vias):
                continue
            ok = b.via_ok(k)
            X, Y = np.meshgrid(b.xs, b.ys)
            d = np.hypot(X - x, Y - y)
            cand = ok & (d <= 1.45) & (b.foreign(1, k) >= 0.95)      # open B.Cu: the GND pour reaches it
            if not cand.any():
                cand = ok & (d <= 1.45)
            if not cand.any():
                self.fail.append((net, f'partner {x:.2f},{y:.2f}'))
                print('  FAIL partner', net, x, y)
                continue
            dd = np.where(cand, d, 99)
            j, i = np.unravel_index(np.argmin(dd), dd.shape)
            b.add_via('GND', round(i * R.G, 4), round(j * R.G, 4))
            added += 1
        return added


def write_tsv(b, out):
    lines = ['# M3-ASSY-R12 copper table (stage C, D-R12-26): written by the drafting aid m3_design/r12_aid/plan.py and '
             'frozen here;', '# m3_design/r12_route.py replays it (no search in the build). Coordinates in mm, board '
             'frame (x east, y forward from the aft edge).', 'kind\tnet\tlayer\twidth\tx0\ty0\tx1\ty1']
    for (net, layer, w, a, c) in b.tracks:
        lines.append(f'track\t{net}\t{layer}\t{w:g}\t{a[0]:g}\t{a[1]:g}\t{c[0]:g}\t{c[1]:g}')
    for (net, x, y) in b.vias:
        lines.append(f'via\t{net}\t-\t{R.VIA_D:g}\t{x:g}\t{y:g}\t\t')
    Path(out).write_text('\n'.join(lines) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('geo')
    ap.add_argument('out')
    ap.add_argument('--lib', required=True)
    ap.add_argument('--length', type=float, required=True)
    ap.add_argument('--report')
    ap.add_argument('--stop', default='')
    ap.add_argument('--debug', default='')
    ap.add_argument('--passes', type=int, default=3)
    a = ap.parse_args()
    geo = json.load(open(a.geo))
    pl = Plan(geo, a.lib, a.length)
    pl.r.debug, pl.r.debug_out = a.debug, a.out + '.npz'
    t0 = time.time()
    pl.necks()
    pl.join('GND', ('U5', '7'), ('U5', '5'))
    for a_, b_ in ((('U4', '2'), ('U4', '3')), (('U4', '6'), ('U4', '7')), (('J9', '3'), ('J9', '4')),
                   (('J122', '5'), None)):
        if b_:
            pl.join('GND', a_, b_)
    pl.join('VLOGIC', ('U2', '4'), ('U2', '5'), w=0.4)
    pl.join('CAM_5V', ('J9', '1'), ('J9', '2'), w=0.5)
    pl.usb()
    pl.bga_setup()
    pl.escapes()
    pl.b.snapshot()
    rings = {}
    for p in pl.b.pads:
        if p['ref'] == 'U1' and p['net'] not in PLANES and not p['net'].startswith('~'):
            rings[p['net']] = pl.ring[p['num']]
    order = sorted((n for n in rings if n not in WIDTH or n in ('VCAP1', 'VCAP2')),
                   key=lambda n: (n not in pl.dogbone_nets, -rings[n], n))
    fans = [f"fan:{net}:{p['ref']}.{p['num']}" for net in PLANES for p in pl.by_net[net]
            if p['attr'] != 'pth' and not p.get('fanned')]
    power = [n for n in POWER_ORDER if n not in order and n not in PLANES]

    def mst(net):
        ps = [(p['x'], p['y']) for p in pl.by_net[net]]
        if len(ps) < 2:
            return 0.0
        inn, tot = [ps[0]], 0.0
        rest_ = ps[1:]
        while rest_:
            d, q = min((min(math.hypot(a[0] - b[0], a[1] - b[1]) for b in inn), a) for a in rest_)
            tot += d
            inn.append(q)
            rest_.remove(q)
        return tot
    fans = [f'cluster:{n}' for n in CLUSTERS] + [f for f in fans if not any(
        f.startswith(f'fan:{n}:') and tuple(f.split(':')[2].split('.')) in CLUSTERS[n] for n in CLUSTERS)]
    rest = sorted((n for n in pl.by_net if n not in PLANES and n not in POWER_ORDER and n not in rings), key=mst)
    short = [n for n in rest if mst(n) < 4.0]
    pl.queue = order + short + fans + power + [n for n in rest if n not in short]
    done = 0
    for npass in range(a.passes):
        while pl.queue:
            u = pl.queue.pop(0)
            pl.run_unit(u)
            done += 1
            if done % 100 == 0:
                print('units', done, 'queue', len(pl.queue), 'rips', pl.rips, round(time.time() - t0, 1), flush=True)
        units = []
        for f in pl.fail:
            net, what = f[0], f[1]
            if what.endswith(' fanout'):
                u = f'fan:{net}:{what.split()[0]}'
            elif net in CLUSTERS and any(tuple(what.split('.')) == q for q in CLUSTERS[net]):
                u = f'cluster:{net}'
            elif what.startswith(('join', 'partner')):
                continue
            else:
                u = net
            if u not in units:
                units.append(u)
        print(f'pass {npass}: {len(pl.fail)} failures, {len(units)} units to retry', flush=True)
        if not units or npass == a.passes - 1:
            break
        pl.fail = []
        pl.b.remove_units(set(units))
        for u in units:
            if u.startswith('cluster:'):
                n_ = u.split(':')[1]
                for p in pl.by_net[n_]:
                    if (p['ref'], p['num']) in CLUSTERS[n_]:
                        p['fanned'] = False
            pl.unrouted(u)
        pl.ripped, pl.rip_pairs, pl.rips = {}, set(), 0
    pl.b.unit = 'partner'
    n = pl.partners()
    print('partners', n, 'fails', len(pl.fail))
    write_tsv(pl.b, a.out)
    if a.report:
        json.dump(dict(fail=pl.fail, tracks=len(pl.b.tracks), vias=len(pl.b.vias)), open(a.report, 'w'), indent=1)


if __name__ == '__main__':
    main()
