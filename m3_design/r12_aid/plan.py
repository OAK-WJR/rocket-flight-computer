#!/usr/bin/env python3
"""R12 routing drafting aid, step 3 (D-R12-26): the routing plan (net widths, order, fixed necks, plane fan-outs)
and the driver that runs route.py's search over it and writes m3_design/r12_routes.tsv. Not part of the build.

usage: python3 m3_design/r12_aid/plan.py GEOMETRY.json OUT.tsv --lib astar.so --length 90 [--report R.json]
"""
import argparse
import ctypes
import pickle
import json
import math
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import route as R  # noqa: E402

PLANES = {'GND': 'In1', '3V3': 'In2', 'RAW_PROTECTED': 'In2', '3V3A': 'In2', 'PORT_4V8': 'In2'}
PLANES_TSV = Path(__file__).resolve().parents[1] / 'r12_planes.tsv'
# D-R12-41: hand-drawn copper, fixed before any search (same columns as r12_routes.tsv); a net listed here is complete
# and is not searched
HAND_TSV = Path(__file__).resolve().parent / 'hand_fixed.tsv'
# D-R12-47: seed copper (U1 stub-tip vias), fixed before the search like HAND_TSV, but its nets are still searched
HAND_SEED_TSV = Path(os.environ.get('R12_HAND_SEED', Path(__file__).resolve().parent / 'hand_seed.tsv'))
# plane-net pads joined on F first, then one of them taken to the island (D-R12-22)
CLUSTERS = {'3V3A': (('U1', 'H1'), ('C21', '1'), ('C22', '1')), 'PORT_4V8': (('L400', '2'), ('C406', '1'), ('R400', '1'))}
# widths (mm): fire path and battery copper per IPC-2152 on 1 oz outer copper (stageC.md section 3), signals 0.1 at
# U1 (the 0.8 mm-pitch channel width), 0.2 elsewhere
WIDTH = {'BAT_IN': 0.8, 'RAW_PROTECTED': 0.8, 'BAT_DAMP': 0.8, 'RAW_ACT': 0.8, 'ACT_FET_S': 0.8, 'PYRO1_IGN': 0.8,
         'PYRO1_OUT': 0.8, 'VLOGIC': 0.5, 'CAM_5V': 0.6, 'CAM_SW': 0.8, 'PORT_SW': 0.8, 'SW_NODE': 0.8,
         'PORT_4V8': 0.5, 'VBUS': 0.5, '3V3A': 0.3, 'VCAP1': 0.2, 'VCAP2': 0.2, 'BST': 0.3, 'PORT_BST': 0.3,
         'CAM_BST': 0.3}
FANOUT_W = 0.3
# D-R12-34: a long slow net (pads more than IN2_SPAN mm apart) prefers In2 (cost IN2_PREF per step against F / B's 1.0),
# so the long aft-to-U1 runs leave F / B to the fast interfaces
IN2_SPAN = float(os.environ.get('R12_IN2_SPAN', 6.0))
IN2_PREF = float(os.environ.get('R12_IN2_PREF', 0.7))
IN2_CORE = float(os.environ.get('R12_IN2_CORE', 5.0))   # half-size of U1's In2 3V3 core (D-R12-34)
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


# D-R12-34: In2 is a mixed layer (3V3 pour + low / medium-speed signals). The fast interfaces stay on F / B; so do the
# power nets (their own widths), the plane nets and the fire path. A fast net's B.Cu track keeps In2 under it free.
FAST = re.compile(r'^(HSE_|USB_D[PM]$|QSPI_|SPI1_|IMU_CS$|SD_)')


def fast(net):
    return bool(FAST.match(net))


# The fast SPI / QSPI / microSD / IMU nets may use In2 too (it lies over In1's unbroken GND; D-R12-34), at In2's full
# cost and never preferred; the crystal and USB data stay on F / B.
IN2_DENY = re.compile(r'^(HSE_|USB_D[PM]$)')


def in2_ok(net):
    return not IN2_DENY.match(net) and net not in WIDTH and net not in PLANES and net not in F_ONLY


class Plan:
    def __init__(self, geo, lib, length):
        self.b = R.Board(geo, length)
        self.b.load_planes(PLANES_TSV)
        self.r = R.Router(self.b, lib)
        self.r.fast = fast
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
        # D-R12-34: In2 keeps a 3V3 pour core under U1 and 1 mm round the ball field (its supply-ball dog-bones)
        self.core = (np.abs(X - cx) <= IN2_CORE + 1e-6) & (np.abs(Y - cy) <= IN2_CORE + 1e-6)
        # the pour guard's U1 box (D-R12-36): the ball field plus 1 mm, whatever In2 routing may enter
        self.core_guard = (np.abs(X - cx) <= 5.0 + 1e-6) & (np.abs(Y - cy) <= 5.0 + 1e-6)
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
        lanes = self.b_lanes(used_sites, pos, target, DIR) if os.environ.get('R12_BLANES', '1') == '1' else 0
        print('escapes:', stubs, 'stubs,', len(used_sites), 'sites,', lanes, 'B lanes', flush=True)

    def b_lanes(self, used_sites, pos, target, DIR):
        """D-R12-43: deterministic B.Cu escapes for U1's signal dog-bones. Under the ball field B.Cu is a grid of lanes
        along the ball rows and columns, 0.4 mm from the interstitial via sites on either side (one 0.1 mm track per
        lane: 0.125 mm to the via rings). Each signal dog-bone via goes diagonally (0.566 mm) to one of its four lane
        crossings and straight along that lane to 0.8 mm past the outer ball row; crossings are exclusive, so no two
        escapes touch. The lane end on B is the net's terminal (u1term, layer B) and B under the field is closed to
        every search. A net with no free lane keeps the old free B escape."""
        nets = sorted(self.dogbone_nets, key=lambda n: n)
        site = {}
        for n in nets:
            (vx, vy), d = self.u1term[n]
            if d is not None:
                continue
            cx, cy = self.u1c
            site[n] = (round((vy - cy) / 0.8 + 5.5, 3), round((vx - cx) / 0.8 + 5.5, 3))
        occ = set()
        self.u1term_layer = getattr(self, 'u1term_layer', {})
        done = 0
        # inner sites first (fewer free lanes), then by name (deterministic)
        ring = lambda s: min(s[0] - 1, s[1] - 1, 10 - s[0], 10 - s[1])
        for n in sorted(site, key=lambda n: (-ring(site[n]), n)):
            r0, c0 = site[n]
            tx, ty = target(n)
            vx, vy = pos(r0, c0)
            best = None
            for cr in (r0 - 0.5, r0 + 0.5):
                for cc in (c0 - 0.5, c0 + 0.5):
                    for dr, dc, s in ((-1, 0, 'N'), (1, 0, 'S'), (0, -1, 'W'), (0, 1, 'E')):
                        path = [(cr, cc)]
                        r, c = cr, cc
                        while 1 <= r <= 10 and 1 <= c <= 10:
                            r, c = r + dr, c + dc
                            path.append((r, c))
                        if any(q in occ for q in path):
                            continue
                        ex, ey = pos(r, c)
                        L = abs(r - cr) + abs(c - cc)
                        gain = (ex - vx) * (tx - vx) + (ey - vy) * (ty - vy)
                        key = (-gain / max(1e-6, math.hypot(tx - vx, ty - vy)) + 0.3 * L, s, cr, cc)
                        if best is None or key < best[0]:
                            best = (key, path, (cr, cc), (r, c), s)
            if best is None:
                continue
            _, path, corner, end, s = best
            occ.update(path)
            pts = [pos(r0, c0), pos(*corner), pos(*end)]
            self.fixed(n, 'B', 0.1, pts)
            self.u1term[n] = (pos(*end), DIR[s])
            self.u1term_layer[n] = 1
            self.reserve_b = getattr(self, 'reserve_b', set()) | {n}
            done += 1
        self.lane_nets = set(self.u1term_layer)
        return done

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
        return [self.bga, none if net in self.dogbone_nets and net not in getattr(self, 'lane_nets', ()) else self.bga,
                self.core]

    def width(self, net, touches_u1):
        if net in getattr(self, 'lane_nets', ()):
            return 0.1                                  # D-R12-43: a B lane is 0.1 mm; no neck at its end
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

    def connect_tree(self, net, maxexp=None, subset=None):
        maxexp = maxexp or int(os.environ.get("R12_MAXEXP", 3_000_000))
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
                tl = getattr(self, 'u1term_layer', {}).get(net, 0)     # D-R12-43: a B.Cu lane end is on layer 1
                if not any(q[:3] == (tl, i, j) for q in self.terms[net]):
                    self.terms[net].append((tl, i, j, m))
                if tl == 0:
                    self.__dict__.setdefault('tipvia', {})[net] = (i, j)
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
            # D-R12-38: a U1 escape stub may also be reached from B / In2 through a via at its tip (a dog-bone at the
            # stub end), where the via is legal; the path then gets its F node at the tip (a via) in tip_fix()
            tip = getattr(self, 'tipvia', {}).get(net)
            if tip and os.environ.get('R12_TIPVIA', '1') == '1' and net not in F_ONLY:
                ti, tj = tip
                vok = (self.b.via_ok_base(self.b.nid(net)) if self.r.__dict__.get('pf') else self.b.via_ok(self.b.nid(net)))
                if vok[tj, ti] and not self.bga[tj, ti]:
                    goals = goals + [(1, ti, tj, 255), (2, ti, tj, 255)]
            nearest = min(connected, key=lambda c: math.hypot(p['x'] - c['x'], p['y'] - c['y'])) if connected else p
            w = limit_w(p, w0)
            if connected and nearest['ref'] not in ('U9', 'U1'):
                w = min(w, limit_w(nearest, w0))
            starts = [n[:3] for n in self.r.pad_nodes(p)]
            if p.get('cl_lead'):      # D-R12-37: a cluster lead already fanned out may also join from its fan-out vias
                for (vn, vx, vy), vu in zip(self.b.vias, self.b.vunit):
                    if vn == net and vu == self.b.unit:
                        i, j = int(round(vx / R.G)), int(round(vy / R.G))
                        starts += [(0, i, j), (1, i, j)]
            starts += [q for q in getattr(self, 'usb_starts', {}).get(net, []) if p.get('group')]
            if p.get('group'):        # a linked group (USB pin pairs): its link vias are terminals too
                for (vn, vx, vy) in self.b.vias:
                    if vn == net and any(math.hypot(vx - q['x'], vy - q['y']) < 3.0 for q in p['group']):
                        i, j = int(round(vx / R.G)), int(round(vy / R.G))
                        starts += [(0, i, j), (1, i, j)]
            sset = {q[1:3] for q in starts}          # D-R12-40: never a goal at a start (a linked group's vias)
            goals = [g for g in goals if g[1:3] not in sset]
            layers = ('F',) if net in F_ONLY else ('F', 'B', 'In2') if in2_ok(net) and net not in \
                getattr(self, 'no_in2', ()) else ('F', 'B')        # no_in2: D-R12-45 pour repair
            span = max((math.hypot(a['x'] - c['x'], a['y'] - c['y']) for a in pads for c in pads), default=0)
            ic = IN2_PREF if 'In2' in layers and span > IN2_SPAN and not fast(net) else None
            ok = False
            # D-R12-39: in negotiated mode a path always exists inside the first window (other units' copper only
            # costs), so a unit that keeps conflicting gets a wider first window (R12_PF_WIN mm per conflicting
            # iteration, up to 16 mm) and can detour round the congestion instead of sharing it
            k_ = getattr(self, 'pf_hits', {}).get(self.b.unit, 0) if self.r.__dict__.get('pf') else 0
            m0 = min(4.0 + float(os.environ.get('R12_PF_WIN', 0.0)) * k_, 16.0)
            for margin in sorted({m0, max(m0, 10.0), 30.0}):
                win = R.window_of([(0, n[1], n[2]) for n in starts] + [(0, g[1], g[2]) for g in goals
                                  if math.hypot(g[1] * R.G - p['x'], g[2] * R.G - p['y']) < dist(p) + 3], margin)
                used = sum(1 for v in self.b.vias if v[0] == net)
                path = self.r.search(net, w, starts, goals, win, layers=layers, maxexp=maxexp, in2_cost=ic,
                                     maxvia=max(0, (VIA_BUDGET if crit_class(net) else 6) - used), extra_block=self.masks(net),
                                     via_block=self.partner_block(net))
                if path:
                    if tip and path[-1][0] != 0 and (path[-1][1], path[-1][2]) == tip:
                        path = path + [(0, tip[0], tip[1])]
                    self.r.commit(net, w, path)
                    ok = True
                    break
            if not ok:
                maxvia = max(0, (VIA_BUDGET if crit_class(net) else 6) - sum(1 for v in self.b.vias if v[0] == net))
                ok = self.ripup(net, w, starts, goals, layers=layers, maxvia=maxvia, extra_block=self.masks(net),
                                in2_cost=ic)
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
              vias=True, in2_cost=None):
        """A connection that fails among the routed copper: find a path against the fixed copper only, rip the units
        whose copper it crosses (never the fixed fan-out), re-route this connection, and queue the ripped units."""
        if self.rips >= self.max_rips:
            return False
        win = R.window_of([(0, n[1], n[2]) for n in starts] + [(0, g[1], g[2]) for g in goals], 12.0) if goals else \
            R.window_of([(0, n[1], n[2]) for n in starts], 6.0)
        path = self.r.search(net, w, starts, goals, win, layers=layers, maxvia=maxvia, extra_block=extra_block,
                             via_block=via_block, goal_via=goal_via, vias=vias, base=True, in2_cost=in2_cost)
        if not path:
            return False
        bl = R.blockers(self.b, net, w, path, end_via=goal_via) - {self.b.unit}
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
                             via_block=via_block, goal_via=goal_via, vias=vias, in2_cost=in2_cost)
        if not path:
            return False
        tip = getattr(self, 'tipvia', {}).get(net)
        if tip and not goal_via and path[-1][0] != 0 and (path[-1][1], path[-1][2]) == tip:
            path = path + [(0, tip[0], tip[1])]       # D-R12-38: the dog-bone via at the stub tip
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
            pads = [p for p in self.by_net[net] if (p['ref'], p['num']) in sub]
            lead = next(p for p in pads if p['ref'] != 'U1')
            # D-R12-37: the lead's plane fan-out first, then the cluster joins it on F (fanning out last left the
            # lead pad boxed in by the cluster's own tracks)
            lead['fanned'] = False
            self.fanout_pad(net, lead)
            self.b.unit = u
            lead['cl_lead'] = True
            try:
                self.connect_tree(net, subset=sub)
            finally:
                lead['cl_lead'] = False
            for p in pads:
                p['fanned'] = True
        else:
            self.connect_tree(u)

    def usb(self):
        """J3's pin pairs (USB-C rows A / B, rotated 90): DP B6 / A6 and DM A7 / B7 are interleaved at 0.5 mm. DP is
        linked on B.Cu through two vias just west of its pads (its F stubs cross DM's row); DM is linked on F.Cu round
        those vias (D-R12-40: on B its link was a needless hop, route_check extra_vias), VBUS B4A9 / A4B9 through two
        vias further west; the rest of each net is routed by the search (stageC.md section 3). The link's on-grid
        nodes are the search's starts (usb_starts): J3's pads sit on a 0.25 mm offset the 0.1 mm grid cannot reach."""
        pads = {p['num']: p for p in self.b.pads if p['ref'] == 'J3'}
        X1, XV = 38.0, 36.6
        self.usb_starts = {}
        for net, (pa, xa), (pb, xb) in (('USB_DP', ('B6', X1), ('A6', X1)), ('VBUS', ('B4A9', XV), ('A4B9', XV))):
            w = 0.1 if net != 'VBUS' else 0.5
            ya, yb = pads[pa]['y'], pads[pb]['y']
            self.fixed(net, 'F', w, [(round(pads[pa]['x'], 3), ya), (xa, ya)])
            self.fixed(net, 'F', w, [(round(pads[pb]['x'], 3), yb), (xb, yb)])
            self.fixed(net, 'B', w, [(xa, ya), (xb, yb)])
            self.b.add_via(net, xa, ya)
            self.b.add_via(net, xb, yb)
            self.link(pads[pa], pads[pb])
        pa, pb = pads['A7'], pads['B7']
        xp, ya, yb = round(pa['x'], 3), pa['y'], pb['y']           # ya < yb, 1.0 mm apart, DP's vias between
        pts = [(xp, ya), (37.75, ya), (37.4, round(ya + 0.35, 3)), (37.4, round(yb - 0.35, 3)), (37.75, yb), (xp, yb)]
        self.fixed('USB_DM', 'F', 0.1, pts)
        self.link(pa, pb)
        i = int(round(37.4 / R.G))
        j0, j1 = int(math.ceil((ya + 0.35) / R.G - 1e-6)), int(math.floor((yb - 0.35) / R.G + 1e-6))
        self.usb_starts['USB_DM'] = [(0, i, j) for j in range(j0, j1 + 1)]
        # the link's straight middle does not wall in its own starts (route.own_block)
        self.r.__dict__.setdefault('links', set()).update(('USB_DM', a_, c_) for a_, c_ in zip(pts, pts[1:]))

    def hand(self, path, complete=True):
        """D-R12-41: hand-drawn copper (explicit rows, reviewed by hand) is fixed copper; its nets are complete
        (complete=False, D-R12-47: seed copper, the nets are still searched)."""
        import csv
        nets = set()
        if not Path(path).exists():
            return nets
        for r in csv.DictReader((l for l in open(path) if not l.startswith('#')), delimiter='\t'):
            if r['kind'] == 'track':
                self.b.add_track(r['net'], r['layer'], float(r['width']), (float(r['x0']), float(r['y0'])),
                                 (float(r['x1']), float(r['y1'])))
            else:
                self.b.add_via(r['net'], float(r['x0']), float(r['y0']))
            nets.add(r['net'])
        if not complete:
            return set()
        for n in nets:
            for p in self.by_net.get(n, []):
                p['fanned'] = True
        return nets

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
        n0 = len(self.b.tracks)
        self.r.commit(net, w, path)
        self.r.__dict__.setdefault('links', set()).update((t[0], t[3], t[4]) for t in self.b.tracks[n0:])
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
                tiers = ((3.0, ('F',), 0), (6.0, ('F',), 0), (8.0, ('F', 'B'), 1), (70.0, ('F', 'B'), 1))
                if net == '3V3A':        # D-R12-34: the H1 cluster reaches the 3V3A island over In2 (it is 15 mm away)
                    tiers += ((30.0, ('F', 'B', 'In2'), 2),)
                for margin, lay, mv in tiers:
                    win = R.window_of([(0, s[1], s[2]) for s in starts], margin)
                    vb_, gm = vb, None
                    if 'In2' in lay:      # D-R12-37: the run's own vias may sit in the 3V3 pour; only the end via in the island
                        vb_ = (vb & ~self.b.region_ok('~any')) | self.bga
                        gm = self.b.region_ok(net) & ~self.bga
                    path = self.r.search(net, w, starts, goals, win, layers=lay, vias=mv > 0, goal_via=True,
                                         extra_block=eb if eb is not None else self.masks(net), via_block=vb_,
                                         maxvia=mv, goal_mask=gm)
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

    # ---------------- negotiated congestion (PathFinder, D-R12-35) and the 3V3 pour guard (D-R12-36)
    def pf_remove(self, u, hard=False):
        """Rip one unit's copper (negotiated mode; hard: rebuild the fields) and reset the fan-out flags it owned."""
        b = self.b
        if hard:
            n0 = len(b.tracks) + len(b.vias)
            b.remove_units({u})
            had = len(b.tracks) + len(b.vias) < n0
        else:
            had = b.soft_remove({u}) > 0
        if u.startswith('fan:'):
            _, net, key = u.split(':', 2)
            p = next(p for p in self.by_net[net] if f"{p['ref']}.{p['num']}" == key)
            group = p.get('group') or [p]
            owned = set(b.tunit) | set(b.vunit)
            others = any(f"fan:{net}:{q['ref']}.{q['num']}" in owned for q in group if q is not p)
            if had or not others:
                for q in group:
                    if not (q['ref'] == 'U9' and q['num'] in ('5', '6')):
                        q['fanned'] = False
        elif u.startswith('cluster:'):
            n_ = u.split(':')[1]
            for p in self.by_net[n_]:
                if (p['ref'], p['num']) in CLUSTERS[n_]:
                    p['fanned'] = False

    def pour3v3(self, neck=1.0):
        """D-R12-36: a raster model of the In2 3V3 fill (0.1 mm grid): the fill keeps 0.2 mm from foreign copper, the
        islands, the board edge and the S-8 keep-outs; opened by neck / 2 (a neck of `neck` mm), every 3V3 via must sit in
        the piece that holds most of them. Returns (isolated vias, {via: eroded component node mask})."""
        import numpy as np
        b = self.b
        k = b.nid('3V3')
        D = b.foreign_base(2, k) - 0.2
        for sd in b.island.values():
            D = np.minimum(D, sd - 0.2)
        for p in b.pads:
            if p['ref'] == 'J121':
                D = np.minimum(D, np.hypot(self.X - p['x'], self.Y - p['y']) - 1.75)
        D = D.astype(np.float32)
        for (n, layer, w, a, c), u in zip(b.tracks, b.tunit):
            if layer != 'In2' or n == '3V3' or u == 'fixed':
                continue
            sl, X, Y = b.region(min(a[0], c[0]), min(a[1], c[1]), max(a[0], c[0]), max(a[1], c[1]))
            D[sl] = np.minimum(D[sl], b.seg_dist(X, Y, a, c) - w / 2 - 0.2)
        for (n, x, y), u in zip(b.vias, b.vunit):
            if n == '3V3' or u == 'fixed':
                continue
            sl, X, Y = b.region(x, y, x, y)
            D[sl] = np.minimum(D[sl], np.hypot(X - x, Y - y) - R.VIA_D / 2 - 0.2)
        # U1's core (the supply-ball dog-bones at 0.8 mm pitch) cannot hold a 1 mm neck between its antipads: there the
        # plain fill (0.25 mm minimum width) counts, and the core joins the rest through 1 mm necks
        er = np.ascontiguousarray(((D >= neck / 2 - 1e-4) | (self.core_guard & (D >= 0.125))).astype(np.uint8))
        lab = np.zeros(er.shape, np.int32)
        self.r.lib.label4.restype = ctypes.c_int
        self.r.lib.label4(ctypes.c_int(b.NX), ctypes.c_int(b.NY), er.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
                          lab.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)))
        vs = [(x, y) for (n, x, y) in b.vias if n == '3V3']
        comps = []
        for x, y in vs:
            sl, X, Y = b.region(x, y, x, y)
            m = np.hypot(X - x, Y - y) <= neck / 2 + 0.05
            comps.append(set(np.unique(lab[sl][m & (lab[sl] > 0)]).tolist()))
        from collections import Counter
        cnt = Counter(c for cs in comps for c in cs)
        main = cnt.most_common(1)[0][0] if cnt else 0
        iso = [(v, cs) for v, cs in zip(vs, comps) if main not in cs]
        return iso, lab, D

    def plane_penalty(self, iso, lab):
        """Units whose In2 tracks or vias bound an isolated 3V3 via's piece of fill: their nodes get history cost on In2
        (the isolated via's own spot too), and they count as conflicting this iteration."""
        import numpy as np
        b = self.b
        pf = self.r.pf
        bad = set()
        for (x, y), cs in iso:
            sl, X, Y = b.region(x, y, x, y)
            reg = np.zeros(lab.shape, bool)
            for c in cs:
                reg |= lab == c
            if not cs:
                reg[sl] |= np.hypot(X - x, Y - y) <= 0.6
            jj, ii = np.nonzero(reg)
            if len(ii) > 40000:          # a large piece: only its part near the via
                keep = np.hypot(ii * R.G - x, jj * R.G - y) < 4.0
                ii, jj = ii[keep], jj[keep]
            P = np.stack([ii * R.G, jj * R.G], 1)
            j0, j1 = jj.min() if len(jj) else 0, jj.max() if len(jj) else 0
            for (n, layer, w, a, c), u in zip(b.tracks, b.tunit):
                if layer != 'In2' or n == '3V3' or u == 'fixed':
                    continue
                d = b.seg_dist(P[:, 0], P[:, 1], a, c)
                if len(d) and d.min() < w / 2 + 0.2 + 0.5 + 0.25:
                    bad.add(u)
                    sl2, X2, Y2 = b.region(min(a[0], c[0]), min(a[1], c[1]), max(a[0], c[0]), max(a[1], c[1]))
                    pf['hist'][2][sl2] += pf['plane_inc'] * (b.seg_dist(X2, Y2, a, c) < w / 2 + 0.3)
            for (n, vx, vy), u in zip(b.vias, b.vunit):
                if n == '3V3' or u == 'fixed':
                    continue
                if len(P) and np.hypot(P[:, 0] - vx, P[:, 1] - vy).min() < R.VIA_D / 2 + 0.2 + 0.5 + 0.25:
                    bad.add(u)
                    sl2, X2, Y2 = b.region(vx, vy, vx, vy)
                    pf['hvia'][sl2] += pf['plane_inc'] * (np.hypot(X2 - vx, Y2 - vy) < 0.4)
            pf['hvia'][sl] += pf['plane_inc'] * (np.hypot(X - x, Y - y) < 0.4)
            for u, uu in zip(b.vunit, b.vias):
                if uu[0] == '3V3' and abs(uu[1] - x) < 1e-6 and abs(uu[2] - y) < 1e-6 and u != 'fixed':
                    bad.add(u)
        return bad

    def negotiate(self, units, iters, t0):
        import numpy as np
        b, pf = self.b, None
        self.r.pf_setup(pres=float(os.environ.get('R12_PF_PRES', 0.5)),
                        hist_inc=float(os.environ.get('R12_PF_HIST', 0.4)),
                        pres_mult=float(os.environ.get('R12_PF_MULT', 1.6)))
        pf = self.r.pf
        pf['plane_inc'] = float(os.environ.get('R12_PF_PLANE', 1.0))
        self.max_rips = 0
        best = None
        full = int(os.environ.get('R12_PF_FULL', iters))    # iterations that re-route every unit; later ones only
        todo = list(units)                                   # the units in conflict, failed or cutting the pour
        focus_after = int(os.environ.get('R12_PF_FOCUS', 0))    # D-R12-39: stagnation iterations before focus mode
        since_best, focused = 0, False
        for it in range(iters):
            self.fail = []
            for u in (units if it < full else [u for u in units if u in todo]):
                self.pf_remove(u)
                self.b.unit = u
                self.queue = []
                self.run_unit(u)
            cf = R.conflicts(b, fast)
            iso, lab, _ = self.pour3v3()
            bad = {x for c in cf for x in c[:2]}
            pbad = self.plane_penalty(iso, lab) if iso else set()
            for (u1, u2, layer, x, y) in cf:
                sl, X, Y = b.region(x, y, x, y)
                disc = np.hypot(X - x, Y - y) < 0.35
                if layer == 'via':
                    pf['hvia'][sl] += pf['hist_inc'] * disc
                    for li in range(R.NL):
                        pf['hist'][li][sl] += pf['hist_inc'] * disc
                elif layer == 'ref':
                    pf['hist'][1][sl] += pf['hist_inc'] * disc
                    pf['hist'][2][sl] += pf['hist_inc'] * disc
                else:
                    pf['hist'][R.LAYERS.index(layer)][sl] += pf['hist_inc'] * disc
            score = len(cf) + len(self.fail) * 3 + len(iso)
            self.__dict__.setdefault('pf_hits', {})
            for u in set(bad) | set(pbad):
                self.pf_hits[u] = self.pf_hits.get(u, 0) + 1
            todo = set(bad) | set(pbad)
            for f in self.fail:
                net_, what = f[0], f[1]
                if what.endswith(' fanout'):
                    todo.add(f'fan:{net_}:{what.split()[0]}')
                todo.add(net_)
                todo.add(f'cluster:{net_}')
            print(f'pf {it}: conflicts {len(cf)} (units {len(bad)}), fails {len(self.fail)}, isolated 3V3 vias '
                  f'{len(iso)} (units {len(pbad)}), pres {pf["pres"]:.2f}, {round(time.time() - t0)} s', flush=True)
            if self.fail:
                print('   fails:', [f[:2] for f in self.fail][:12], flush=True)
            if len(cf) + len(iso) <= 6 and cf + [i[0] for i in iso]:
                print('   left:', [(c[0], c[1], c[2], round(c[3], 2), round(c[4], 2)) for c in cf][:6],
                      [i[0] for i in iso][:6], flush=True)
            if best is None or score < best[0]:
                best = (score, it, self.state())
                since_best = 0
            else:
                since_best += 1
                if os.environ.get('R12_PF_DUMP'):
                    pickle.dump(best[2], open(os.environ['R12_PF_DUMP'], 'wb'))
            if not cf and not self.fail and not iso:
                break
            pf['pres'] = min(pf['pres'] * pf['pres_mult'], float(os.environ.get('R12_PF_PMAX', 40.0)))
            # D-R12-39 focus mode: once the negotiation stagnates, every unit not in conflict is frozen (a hard obstacle)
            # and only the conflicting units negotiate among themselves; a unit that then finds no path at all thaws the
            # frozen units with copper within 2 mm of its failing pad
            if focus_after and it >= full and (focused or since_best >= focus_after):
                if not focused:
                    if best[1] != it:
                        self.load_state(best[2])
                        cf = R.conflicts(b, fast)
                        todo = {x for c in cf for x in c[:2]}
                    focused = True
                    print(f'   focus: freezing {len(set(units) - set(todo))} units, {len(todo)} negotiate', flush=True)
                thaw = set()
                for f in self.fail:
                    pad = next((q for q in self.by_net.get(f[0], []) if f"{q['ref']}.{q['num']}" == f[1].split()[0]),
                               None)
                    if pad is None:
                        continue
                    for (n, layer, w, a_, c_), u in zip(b.tracks, b.tunit):
                        if u in getattr(b, 'frozen', set()) and R.Board.seg_dist(
                                np.array(pad['x']), np.array(pad['y']), a_, c_) < 2.0 + w / 2:
                            thaw.add(u)
                    for (n, x, y), u in zip(b.vias, b.vunit):
                        if u in getattr(b, 'frozen', set()) and math.hypot(x - pad['x'], y - pad['y']) < 2.2:
                            thaw.add(u)
                if thaw:
                    print(f'   focus: thawing {sorted(thaw)[:10]}', flush=True)
                todo = set(todo) | thaw
                self.b.freeze(set(u for u in set(b.tunit) | set(b.vunit) if u != 'fixed') - set(todo))
        if focused:
            self.b.freeze(set())
        if best[1] != it:
            print(f'pf: restoring the best iteration {best[1]} (score {best[0]})', flush=True)
            self.load_state(best[2])
        return best

    def state(self):
        b = self.b
        return dict(tracks=list(b.tracks), tunit=list(b.tunit), vias=list(b.vias), vunit=list(b.vunit),
                    fanned={p['key']: bool(p.get('fanned')) for p in b.pads}, fail=list(self.fail))

    def load_state(self, st):
        b = self.b
        b.tracks, b.tunit, b.vias, b.vunit = list(st['tracks']), list(st['tunit']), list(st['vias']), list(st['vunit'])
        for p in b.pads:
            p['fanned'] = st['fanned'].get(p['key'], False)
        self.fail = list(st['fail'])

    def clean(self, rep, turn):
        """Clean-up pass (stage C, D-R12-33): every unit with a route_check hygiene finding in an earlier draft is
        ripped and re-routed alone with a higher turn cost and no rip-up of others; if it no longer completes, its
        old copper is put back unchanged."""
        b = self.b
        cats = {'staircase', 'tiny_jog', 'fold_back', 'acute_angle', 'track_loop', 'detour', 'collinear_overlap',
                'extra_bends', 'local_bump', 'short_segment', 'chain_detour', 'extra_vias', 'pour_net_hop', 'jog'}
        units = []
        for f in rep.get('failures', []):
            if f.get('cat') not in cats:
                continue
            net = f['net']
            if net in PLANES:
                x, y = f.get('x'), f.get('y')
                if x is None:
                    continue
                best = None
                for u in set(b.tunit) | set(b.vunit):
                    if not u.startswith(f'fan:{net}:') and u != f'cluster:{net}':
                        continue
                    pts = [t[3] for t, uu in zip(b.tracks, b.tunit) if uu == u] + \
                          [t[4] for t, uu in zip(b.tracks, b.tunit) if uu == u]
                    if pts:
                        d = min(math.hypot(px - x, py - y) for px, py in pts)
                        if d < 0.5 and (best is None or d < best[0]):
                            best = (d, u)
                if best:
                    u = best[1]
                else:
                    continue
            else:
                u = net
            if u not in units and u in set(b.tunit):
                units.append(u)
        old_turn, old_max = R.TURN, self.max_rips
        self.max_rips = self.rips
        kept = 0
        for u in units:
            saved_t = [(t, uu) for t, uu in zip(b.tracks, b.tunit) if uu == u]
            saved_v = [(v, uu) for v, uu in zip(b.vias, b.vunit) if uu == u]
            nfail = len(self.fail)
            b.remove_units({u})
            if u.startswith('fan:') or u.startswith('cluster:'):
                self.unrouted(u)
                self.queue.pop(0)
                if u.startswith('cluster:'):
                    n_ = u.split(':')[1]
                    for p in self.by_net[n_]:
                        if (p['ref'], p['num']) in CLUSTERS[n_]:
                            p['fanned'] = False
            R.TURN = turn
            try:
                self.run_unit(u)
            finally:
                R.TURN = old_turn
            if len(self.fail) > nfail or self.queue:
                self.queue = []
                del self.fail[nfail:]
                b.remove_units({u})
                b.unit = u
                for (net, layer, w, a_, c_), _ in saved_t:
                    b.add_track(net, layer, w, a_, c_)
                for (net, x, y), _ in saved_v:
                    b.add_via(net, x, y)
                if u.startswith('fan:'):
                    _, n_, key = u.split(':', 2)
                    for p in self.by_net.get(n_, []):
                        if f"{p['ref']}.{p['num']}" == key:
                            p['fanned'] = True
                print('  clean: kept old copper of', u, flush=True)
            else:
                kept += 1
        self.max_rips = old_max
        print('clean:', kept, 'of', len(units), 'units re-routed', flush=True)

    def partner_block(self, net):
        """D-R12-42: outside the negotiation, a critical net may place a via only where a GND partner via could still
        go (a legal GND via site within 1.0 mm in x and y, so within 1.41 mm: AGENTS section 3's 1.5 mm rule)."""
        import numpy as np
        if self.r.__dict__.get('pf') or not critical(net) or os.environ.get('R12_PARTNER_BLOCK', '1') != '1':
            return None
        ok = self.b.via_ok(self.b.nid('GND')).astype(np.int32)
        r = int(round(1.0 / R.G))
        c = np.pad(ok, r).cumsum(0).cumsum(1)
        c = np.pad(c, ((1, 0), (1, 0)))
        H, W = ok.shape
        n = 2 * r + 1
        box = c[n:n + H, n:n + W] - c[0:H, n:n + W] - c[n:n + H, 0:W] + c[0:H, 0:W]
        return box == 0

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


def finish(pl):
    # D-R12-35 finish: the units still in conflict (or failed) are ripped and re-routed against all the other
    # copper as hard obstacles, with the rip-up search (a few units, so it no longer stalls)
    bad = []
    for c in R.conflicts(pl.b, fast):
        for u in c[:2]:
            if u not in bad and u != 'fixed':
                bad.append(u)
    for f in pl.fail:
        u = f'fan:{f[0]}:{f[1].split()[0]}' if f[1].endswith(' fanout') else f[0]
        if f[0] in CLUSTERS and any(tuple(f[1].split()[0].split('.')) == q for q in CLUSTERS[f[0]]):
            u = f'cluster:{f[0]}'
        if u not in bad:
            bad.append(u)
    print('finish: re-routing', len(bad), 'units hard:', bad[:20], flush=True)
    pl.fail = []
    for u in bad:
        pl.pf_remove(u, hard=True)
    pl.queue = list(bad)
    pl.ripped, pl.rip_pairs, pl.rips, pl.max_rips = {}, set(), 0, 300
    return int(os.environ.get('R12_FINISH_PASSES', 4))


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
    ap.add_argument('--clean', default='', help='route_check --report JSON of an earlier draft: re-route the units it '
                    'flags (hygiene findings) once more with a higher turn cost, keeping the old copper if that fails')
    ap.add_argument('--clean-turn', type=float, default=8.0)
    ap.add_argument('--pf', type=int, default=0, help='negotiated congestion (PathFinder, D-R12-35): at most this '
                    'many iterations, every unit re-routed in each, instead of the rip-up passes')
    ap.add_argument('--save-state', default='', help='pickle the routed units after the search (before --clean)')
    ap.add_argument('--load-state', default='', help='skip the search: load a --save-state pickle')
    ap.add_argument('--save-final', default='', help='pickle the routed units after clean and partners')
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
    # D-R12-34: the servo pull-down block's GND pads in pairs (1.0 mm apart, one fan-out per pair)
    pl.join('GND', ('R154', '2'), ('R155', '2'))
    pl.join('GND', ('R156', '2'), ('R157', '2'))
    pl.join('CAM_5V', ('J9', '1'), ('J9', '2'), w=0.5)
    # D-R12-37: R401's GND pad is boxed in by the port buck's feedback divider (R404 / R400 / U400): it shares C94.2's
    # GND fan-out through a short F.Cu link
    pl.join('GND', ('R401', '2'), ('C94', '2'), w=0.2)
    pl.usb()
    hand = pl.hand(HAND_TSV)
    pl.hand(HAND_SEED_TSV, complete=False)
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
    # D-R12-34: the long slow nets go first after the dog-bone escapes, so they take In2 before F / B fill up
    longslow = [n for n in order + rest if n not in pl.dogbone_nets and in2_ok(n) and not fast(n)
                and mst(n) > IN2_SPAN]
    order = [n for n in order if n in pl.dogbone_nets] + longslow + [n for n in order if n not in pl.dogbone_nets
                                                                     and n not in longslow]
    rest = [n for n in rest if n not in longslow]
    short = [n for n in short if n not in longslow]
    pl.queue = [u for u in order + short + fans + power + [n for n in rest if n not in short] if u not in hand
                and not (u.startswith(('cluster:', 'fan:')) and u.split(':')[1] in hand)]   # D-R12-47
    done = 0
    if a.load_state:
        pl.load_state(pickle.load(open(a.load_state, 'rb')))
        pl.queue = []
        a.passes = 0
        if os.environ.get('R12_FINISH'):
            pl.b.harden()
            a.passes = finish(pl)
    elif a.pf:
        units = list(pl.queue)
        pl.queue = []
        pl.negotiate(units, a.pf, t0)
        a.passes = 0
        pl.r.pf = None
        pl.b.harden()
        if a.save_state:
            pickle.dump(pl.state(), open(a.save_state, 'wb'))
        a.passes = finish(pl)
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
    iso, _, _ = pl.pour3v3()
    print('after search: conflicts', len(R.conflicts(pl.b, fast)), 'fails', len(pl.fail), 'isolated 3V3 vias', len(iso),
          [v for v, _ in iso][:8], flush=True)
    if a.save_state:
        pickle.dump(pl.state(), open(a.save_state + ('.fin' if (a.pf or a.load_state) else ''), 'wb'))
    if a.load_state:
        pl.b.harden()
    if a.clean:
        pl.clean(json.load(open(a.clean)), a.clean_turn)
    pl.b.unit = 'partner'
    n = pl.partners()
    print('partners', n, 'fails', len(pl.fail))
    write_tsv(pl.b, a.out)
    if a.save_final:
        pickle.dump(pl.state(), open(a.save_final, 'wb'))
    if a.report:
        json.dump(dict(fail=pl.fail, tracks=len(pl.b.tracks), vias=len(pl.b.vias)), open(a.report, 'w'), indent=1)


if __name__ == '__main__':
    main()
