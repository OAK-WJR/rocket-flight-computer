#!/usr/bin/env python3
"""Score an R12 placement: ratsnest (MST) length per net class, ratsnest crossings, routed length / MST, vias,
regulator-to-load and decoupling distances, U1 ball-facing errors.

usage: <KiCad python3> -I -B score.py BOARD [--place TSV] [--swaps TSV] [--json OUT] [--quiet]

BOARD is read only. --place moves footprints in memory (r12_place.tsv format: ref x y rot side basis; '@' rows
ignored). --swaps re-assigns U1 ball nets in memory (TSV: net old_ball new_ball). With --place, routed lengths are
not reported (the copper belongs to the old placement).
"""
import argparse, json, math, re, sys
import pcbnew

mm = pcbnew.ToMM
MMf = pcbnew.FromMM
PLANE = {'GND', '3V3'}                     # In1 / In2 planes: reached by vias, no ratsnest
POWER = {'BAT_IN', 'RAW_PROTECTED', 'RAW_ACT', 'VLOGIC', 'PORT_4V8', 'CAM_5V', 'VBUS', '3V3A', 'SW_NODE',
         'PORT_SW', 'CAM_SW', 'BAT_DAMP', 'VCAP1', 'VCAP2'}
FIRE = {'PYRO1_OUT', 'PYRO1_IGN', 'ACT_FET_S', 'ACT_GATE', 'PYRO1_GATE', 'PYRO1_GATE_N', 'ACT_EN', 'ACT_EN_MCU',
        'ACT_DRV', 'PYRO1_CONT', 'PYRO1_CONT_MID', 'PYRO1_COLD', 'ARM1_SENSE', 'ARM1_SENSE_MID'}
FAST = re.compile(r'^(HSE_|USB_D|QSPI_|SPI1_|IMU_CS|HG_CS|SD_(CS|SCK|MOSI|MISO))')


def klass(n):
    if n in PLANE: return 'plane'
    if n in POWER: return 'power'
    if n in FIRE: return 'pyro'
    if FAST.match(n): return 'fast'
    return 'slow'


def octd(a, b):
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


def mst(pts):
    """Prim on octilinear distance; returns edges (i, j, d)."""
    n = len(pts)
    if n < 2: return []
    inT = [False] * n; best = [1e18] * n; par = [-1] * n; best[0] = 0; E = []
    for _ in range(n):
        u = min((i for i in range(n) if not inT[i]), key=lambda i: best[i])
        inT[u] = True
        if par[u] >= 0: E.append((par[u], u, best[u]))
        for v in range(n):
            if not inT[v]:
                d = octd(pts[u], pts[v])
                if d < best[v]: best[v] = d; par[v] = u
    return E


def seg_x(p1, p2, p3, p4):
    def o(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)
    if min(map(lambda q: math.dist(*q), ((p1, p3), (p1, p4), (p2, p3), (p2, p4)))) < 1e-6: return False
    return o(p1, p2, p3) * o(p1, p2, p4) < 0 and o(p3, p4, p1) * o(p3, p4, p2) < 0


def load(board, place=None, swaps=None):
    b = pcbnew.LoadBoard(board)
    moved = set()
    if place:
        for line in open(place):
            if line.startswith(('ref', '#', '@')) or not line.strip(): continue
            ref, x, y, rot, side = line.split('\t')[:5]
            fp = b.FindFootprintByReference(ref)
            if fp is None: print('missing', ref, file=sys.stderr); continue
            fp.SetOrientationDegrees(float(rot)); fp.SetPosition(pcbnew.VECTOR2I(MMf(float(x)), MMf(float(y))))
            moved.add(ref)
    if swaps:
        u1 = b.FindFootprintByReference('U1'); ni = b.GetNetInfo()
        plan = []
        for line in open(swaps):
            if line.startswith(('net', '#')) or not line.strip(): continue
            net, old, new = line.split('\t')[:3]
            plan.append((net.strip(), old.strip(), new.strip()))
        for net, old, new in plan:
            po = u1.FindPadByNumber(old)
            assert po.GetNetname() == net, (net, old, po.GetNetname())
            po.SetNetCode(0)
        for net, old, new in plan:
            pn = u1.FindPadByNumber(new)
            assert pn.GetNetCode() == 0 or pn.GetNetname().startswith('unconnected'), (new, pn.GetNetname())
            pn.SetNet(b.FindNet(net))
    return b, moved


def pads_by_net(b):
    nets = {}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            n = p.GetNetname()
            if not n or n.startswith('unconnected'): continue
            c = p.GetPosition()
            nets.setdefault(n, []).append((fp.GetReference(), p.GetName(), (mm(c.x), mm(c.y))))
    # merge pads of the same ref+name (split lands) to one point
    for n, L in nets.items():
        seen = {}
        for r, pn, xy in L: seen.setdefault((r, pn), xy)
        nets[n] = [(r, pn, xy) for (r, pn), xy in seen.items()]
    return nets


def score(b, routed=True):
    nets = pads_by_net(b)
    res = {'nets': {}, 'class': {}, 'edges': []}
    track = {}; vias = {}
    if routed:
        for t in b.GetTracks():
            n = t.GetNetname()
            if t.GetClass() == 'PCB_VIA': vias[n] = vias.get(n, 0) + 1; continue
            track[n] = track.get(n, 0) + mm(t.GetLength())
    for n, L in nets.items():
        if n in PLANE: continue
        pts = [xy for _, _, xy in L]
        E = mst(pts); m = sum(d for *_, d in E)
        res['nets'][n] = {'class': klass(n), 'pads': len(pts), 'mst': round(m, 2)}
        if routed:
            res['nets'][n].update(track=round(track.get(n, 0), 2), vias=vias.get(n, 0),
                                  ratio=round(track.get(n, 0) / m, 2) if m > 0.5 else None)
        for i, j, d in E: res['edges'].append((n, pts[i], pts[j]))
    for n, d in res['nets'].items():
        c = res['class'].setdefault(d['class'], {'nets': 0, 'mst': 0, 'track': 0, 'vias': 0})
        c['nets'] += 1; c['mst'] += d['mst']
        if routed: c['track'] += d['track']; c['vias'] += d['vias']
    for c in res['class'].values():
        for k in ('mst', 'track'): c[k] = round(c[k], 1)
    # crossings between ratsnest edges of different nets (non-plane)
    E = res['edges']; X = 0; xc = {}
    for i in range(len(E)):
        for j in range(i + 1, len(E)):
            if E[i][0] == E[j][0]: continue
            if seg_x(E[i][1], E[i][2], E[j][1], E[j][2]):
                X += 1; xc[E[i][0]] = xc.get(E[i][0], 0) + 1; xc[E[j][0]] = xc.get(E[j][0], 0) + 1
    Xs = 0
    for i in range(len(E)):
        for j in range(i + 1, len(E)):
            if E[i][0] == E[j][0] or klass(E[i][0]) == 'power' or klass(E[j][0]) == 'power': continue
            if seg_x(E[i][1], E[i][2], E[j][1], E[j][2]): Xs += 1
    res['crossings_signal'] = Xs
    res['crossings'] = X; res['cross_by_net'] = dict(sorted(xc.items(), key=lambda kv: -kv[1])[:25])
    del res['edges']
    res['total_mst'] = round(sum(d['mst'] for d in res['nets'].values()), 1)
    if routed:
        res['total_track_signal'] = round(sum(d['track'] for d in res['nets'].values()), 1)
        res['total_vias'] = sum(vias.values()); res['vias_gnd'] = vias.get('GND', 0); res['vias_3v3'] = vias.get('3V3', 0)
    # regulator -> load distances (pad to pad, straight line)
    def pad(ref, name):
        fp = b.FindFootprintByReference(ref); p = fp.FindPadByNumber(name); c = p.GetPosition(); return (mm(c.x), mm(c.y))
    reg = {
        'U400.SW->J410.2 (PORT_4V8 regulator to GPS)': ('L400', '2', 'J410', '2'),
        'U400.SW->J420.2': ('L400', '2', 'J420', '2'),
        'U400.SW->J440.2': ('L400', '2', 'J440', '2'),
        'L401.2->J9.1 (CAM_5V)': ('L401', '2', 'J9', '1'),
        'L1.2->U1 centre (3V3)': ('L1', '2', 'U1', 'F5'),
        'U9.6->Q121.3 path start (RAW to bus switch)': ('U9', '6', 'Q120', '3'),
        'J1.1->U9.5 (BAT_IN entry)': ('J1', '1', 'U9', '5'),
        'D6.1->U2.5 (VLOGIC from USB OR-ing)': ('D6', '1', 'U2', '5'),
        'C84.1->U2.5 (hold-up cap to 3V3 buck)': ('C84', '1', 'U2', '5'),
        'J3.A6->U1.B10 (USB_DP)': ('J3', 'A6', 'U1', 'B10'),
        'J2.2->U1.A10 (SWDIO)': ('J2', '2', 'U1', 'A10'),
        'J121.1->Q124.3 (fire return)': ('J121', '1', 'Q124', '3'),
        'R134.1->J121.2 (fire feed)': ('R134', '1', 'J121', '2'),
        'R152.1->U1 SERVO3 ball': ('R152', '1', 'U1', None),
        'R153.1->U1 SERVO4 ball': ('R153', '1', 'U1', None),
        'R89.2->U1 BAT_FAULT_N ball': ('R89', '2', 'U1', None),
        'C24.1->J2.3 (NRST)': ('C24', '1', 'J2', '3'),
        'LED1.2->U1 LED_RED ball via R32': ('R32', '1', 'U1', None),
        'R33.1->U1 LED_YEL ball': ('R33', '1', 'U1', None),
        'R162.1->U1 BUZZ_DRV ball': ('R162', '1', 'U1', None),
        'U3.6->U1 QSPI_CLK ball': ('U3', '6', 'U1', None),
        'J430.5->U1 SD_SCK ball': ('J430', '5', 'U1', None),
        'U5.8->U1 I2C SCL ball': ('U5', '8', 'U1', None),
        'R105.1->U1 CAM_5V_SENSE ball': ('R105', '1', 'U1', None),
        'C60.1->U1 VLOGIC_SENSE ball': ('C60', '1', 'U1', None),
        'R112.1->U1 PORT_SENSE ball': ('R112', '1', 'U1', None),
        'U403.5->U1 CAM_PWR_EN ball': ('U403', '5', 'U1', None),
    }
    res['distances'] = {}
    for k, (r1, p1, r2, p2) in reg.items():
        a = pad(r1, p1)
        if p2 is None:
            net = b.FindFootprintByReference(r1).FindPadByNumber(p1).GetNetname()
            balls = [p for p in b.FindFootprintByReference('U1').Pads() if p.GetNetname() == net]
            if not balls: res['distances'][k] = None; continue
            c = balls[0].GetPosition(); bb = (mm(c.x), mm(c.y)); k = k + f' ({balls[0].GetName()})'
        else: bb = pad(r2, p2)
        res['distances'][k] = round(math.dist(a, bb), 2)
    # decoupling: every U1 supply ball -> nearest cap pad of the same net, and cap -> nearest ball
    u1 = b.FindFootprintByReference('U1')
    caps = {}
    for fp in b.GetFootprints():
        if not fp.GetReference().startswith('C'): continue
        for p in fp.Pads():
            caps.setdefault(p.GetNetname(), []).append((fp.GetReference(), (mm(p.GetPosition().x), mm(p.GetPosition().y))))
    dec = {}
    for p in u1.Pads():
        n = p.GetNetname()
        if n in ('3V3', '3V3A', 'VCAP1', 'VCAP2'):
            c = (mm(p.GetPosition().x), mm(p.GetPosition().y))
            best = min(caps.get(n, []), key=lambda rc: math.dist(rc[1], c))
            dec[f'{p.GetName()} {n}'] = (best[0], round(math.dist(best[1], c), 2))
    res['decoupling'] = dec
    # U1 ball facing: for every signal ball, the side its nearest partner pad lies on vs the ball's escape side
    cx, cy = mm(u1.GetPosition().x), mm(u1.GetPosition().y)
    face = {}; bad = 0
    for p in u1.Pads():
        n = p.GetNetname()
        if not n or n.startswith('unconnected') or n in PLANE or n in ('3V3A', 'VCAP1', 'VCAP2', 'BOOT0'): continue
        bx, by = mm(p.GetPosition().x) - cx, mm(p.GetPosition().y) - cy
        others = [xy for r, _, xy in nets[n] if r != 'U1']
        if not others: continue
        t = min(others, key=lambda q: math.dist(q, (bx + cx, by + cy)))
        tx, ty = t[0] - cx, t[1] - cy
        # ball's natural escape side = the side of the ball field it is nearest
        side_b = max(((-bx, 'W'), (bx, 'E'), (-by, 'aft'), (by, 'fwd')))[1]
        ang = math.degrees(math.atan2(ty, tx))
        side_t = 'E' if -45 <= ang < 45 else 'fwd' if 45 <= ang < 135 else 'aft' if -135 <= ang < -45 else 'W'
        opp = {'W': 'E', 'E': 'W', 'aft': 'fwd', 'fwd': 'aft'}
        verdict = 'faces' if side_b == side_t else ('OPPOSITE' if opp[side_b] == side_t else 'side')
        if verdict == 'OPPOSITE': bad += 1
        face[f'{p.GetName()} {n}'] = f'ball side {side_b}, part {side_t} ({math.hypot(tx - bx, ty - by):.1f} mm): {verdict}'
    res['facing'] = face; res['facing_opposite'] = bad
    res['facing_side'] = sum(1 for v in face.values() if v.endswith('side'))
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('board'); ap.add_argument('--place'); ap.add_argument('--swaps')
    ap.add_argument('--json'); ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()
    b, moved = load(a.board, a.place, a.swaps)
    r = score(b, routed=not a.place)
    if a.json: json.dump(r, open(a.json, 'w'), indent=1)
    if a.quiet: return
    print('total ratsnest (octilinear MST, non-plane nets):', r['total_mst'], 'mm; crossings:', r['crossings'], 'signal-only crossings:', r['crossings_signal'])
    for k, v in sorted(r['class'].items()): print(' ', k, v)
    if 'total_vias' in r: print('vias', r['total_vias'], 'GND', r['vias_gnd'], '3V3', r['vias_3v3'], 'signal track', r['total_track_signal'])
    print('facing: opposite', r['facing_opposite'], 'side', r['facing_side'])
    for k, v in r['distances'].items(): print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
