#!/usr/bin/env python3
"""M3-ASSY-R5: route what the autorouter left (docs/M3_R5.md "How R5 is built").

usage: <KiCad python3> m3_design/r5_finish.py [m3_design/assembly_review/m3.kicad_pcb] [--shake] [--force]
                                             [--snapshot=board_before_LATE.kicad_pcb] [--record=r5_finish.json]
       <KiCad python3> m3_design/r5_finish.py [board] --replay=m3_design/r5_finish.json

--record writes the result (the import board's copper removed, the copper added) as a session file; --replay applies
one to the board as r5_route.py import left it, without the search. r5_build.sh replays the file in git: the search
is not repeatable, because KiCad's DRC reports one and the same open connection now as a pair of items, now as two
pour pieces, and the rounds take their work from that list (one of several runs leaves nothing open).

After r5_route.py import (the scripted copper locked, the router's unlocked). First the router's tracks narrower
than their net's router width (r5_route.router_width) are removed (Freerouting v2.4.1 necks down whatever its
neck-down settings say).
Then rounds of KiCad's DRC (kicad-cli, JSON): unlocked copper DRC calls dangling (left by the router or by the
removals) is deleted, and each connection still open is drawn by the scripted grid router (r5_maze.maze_multi:
F.Cu, B.Cu and In2 with checked vias, the board's clearances and the pyro spacing rules, 0/45/90 degree
segments, 0.02 mm over each clearance rule like the autorouter), shortest first, at the router's widths (0.25 mm
for 3V3 and 3V3A). A GND pad left open gets a via into the In1 plane instead,
and a 3V3 or 3V3A pad a via into its In2 plane where one lands inside it.
In2 keeps the keep-outs under the critical B.Cu traces that the autorouter had (r5_route.reference_keepouts).
A connection with no free path may then cross the router's own (unlocked) copper at a cost per cell: what it
crosses is removed, the connections that opens are drawn again (each may cross other router copper once more),
and the attempt is kept only if fewer connections are open afterwards (KiCad's connectivity count); otherwise it
is undone. Everything drawn here is
locked, so no later round moves it. Repeats until nothing is open or nothing changes.
Then the forced moves, repeated while they leave fewer connections open (each is undone unless it does): GND pads
still on outer-pour islands get a track across the movable copper to a GND via within 6 mm (--shake), then a via of
their own or a track to the nearest grounded copper in a box cleared of movable copper (late_islands); each open
connection in turn is drawn across the movable copper (--shake). Movable copper is the router's, this script's own
and the scripted links of the non-critical nets (critical(): the nets AGENTS.md has hand-routed stay as scripted).
Then the hand finish (LATE): connections the routers leave on this session, each with the area whose movable copper
may be cleared and the waypoints a person would route it through, kept only if fewer connections stay open. --force
draws whatever is still open across the router's copper (the board for a warm second session). What is still open
is listed (and fails tools/check.sh).
"""
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r5_maze  # noqa: E402
import r5_route  # noqa: E402
import r5_routes  # noqa: E402

PCB = next((x for x in sys.argv[1:] if not x.startswith('--')), 'm3_design/assembly_review/m3.kicad_pcb')
mm, MM = pcbnew.ToMM, pcbnew.FromMM
F, B, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu
CLI = shutil.which('kicad-cli') or '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
ROUNDS = 16
r5_maze.MARGIN = 0.02     # the last connections keep 0.02 mm over each rule, as the autorouter does (DRC checks)


def width(net):
    """The width the finisher draws a net with (mm): the router's, and 0.25 mm for the 3V3 rails."""
    return 0.25 if net in ('3V3', '3V3A') else r5_route.router_width(net)


def drc(path):
    """KiCad's DRC: ([(net, (uuid, xy), (uuid, xy))] open connections, [descriptions] of other open items
    (zone islands), {uuids} of dangling tracks and vias)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--format', 'json', '-o', str(out), path], capture_output=True)
        d = json.loads(out.read_text())
    pairs, other = [], []
    for u in d['unconnected_items']:
        its = u['items']
        desc = [it['description'] for it in its]
        if len(its) == 2 and not any(x.startswith('Zone') for x in desc):
            net = desc[0].split('[', 1)[1].split(']', 1)[0]
            pairs.append((net, *((it['uuid'], (it['pos']['x'], it['pos']['y'])) for it in its)))
        else:
            other.append(' / '.join(x[:50] for x in desc))
    dangling = {it['uuid'] for v in d['violations'] if v['type'] in ('track_dangling', 'via_dangling')
                for it in v['items']}
    pairs.sort(key=_pair_key)
    return pairs, sorted(other), dangling


def _pair_key(pr):
    """Shortest first, then by net and position: a full order, so the rounds take the connections in the same order
    every run whatever order kicad-cli lists them in (its connectivity is built on several threads)."""
    net, (_, pa), (_, pc) = pr
    return (round(math.hypot(pa[0] - pc[0], pa[1] - pc[1]), 6), net, min(pa, pc), max(pa, pc))


def _index(b):
    idx = {t.m_Uuid.AsString(): t for t in b.GetTracks()}
    for f in b.GetFootprints():
        for p in f.Pads():
            idx[p.m_Uuid.AsString()] = p
    return idx


def _point(idx, item):
    """Connection point and the layers it may be reached on: a pad's centre, a via's centre, or the end of a
    track nearest the point KiCad reports (a ratsnest end)."""
    o = idx[item[0]]
    x, y = item[1]
    if isinstance(o, pcbnew.PAD):
        return (round(mm(o.GetPosition().x), 4), round(mm(o.GetPosition().y), 4)), \
            {lay for lay in (F, B, IN2) if o.IsOnLayer(lay)}
    if o.GetClass() == 'PCB_VIA':
        return (round(mm(o.GetPosition().x), 4), round(mm(o.GetPosition().y), 4)), {F, B, IN2}
    q = min((o.GetStart(), o.GetEnd()), key=lambda q: math.hypot(mm(q.x) - x, mm(q.y) - y))
    return (round(mm(q.x), 4), round(mm(q.y), 4)), {o.GetLayer()}


def _ss(p, q, r, s):
    """Distance between segments pq and rs."""
    def cross(o, a, c):
        return (a[0] - o[0]) * (c[1] - o[1]) - (a[1] - o[1]) * (c[0] - o[0])
    d1, d2, d3, d4 = cross(r, s, p), cross(r, s, q), cross(p, q, r), cross(p, q, s)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(r5_maze._seg_dist(*p, *r, *s), r5_maze._seg_dist(*q, *r, *s),
               r5_maze._seg_dist(*r, *p, *q), r5_maze._seg_dist(*s, *p, *q))


def conflicts(b, net, runs, vias, w, rip):
    """The ripable items (uuids in `rip`) the new copper comes too close to: the router's clearance (the rule plus
    0.05 mm) between the new tracks and vias and each item, on its layer (a via: every layer)."""
    segs = [(lay, p, q) for lay, pts in runs for p, q in zip(pts, pts[1:])]
    out = []
    for t in b.GetTracks():
        if t.GetNetname() == net or t.m_Uuid.AsString() not in rip:
            continue
        k = r5_maze.rule_clearance(net, t.GetNetname())
        if t.GetClass() == 'PCB_VIA':
            c = (mm(t.GetPosition().x), mm(t.GetPosition().y))
            r = mm(t.GetWidth(F)) / 2
            hit = any(r5_maze._seg_dist(*c, *p, *q) < r + w / 2 + k for _, p, q in segs) or \
                any(math.hypot(c[0] - v[0], c[1] - v[1]) < max(r + 0.3 + k, 0.75) for v in vias)
        else:
            a, c, hw = (mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y)), mm(t.GetWidth()) / 2
            hit = any(lay == t.GetLayer() and _ss(p, q, a, c) < hw + w / 2 + k for lay, p, q in segs) or \
                any(r5_maze._seg_dist(*v, *a, *c) < hw + 0.3 + k for v in vias)
        if hit:
            out.append(t)
    return out


SCRIPTED = set()   # geometric keys of the critical scripted copper (locked at import), which no pass may move


def critical(net):
    """The nets AGENTS.md has hand-routed: power (and GND), pyro, crystal, USB, SPI/QSPI. The scripted copper of other
    nets (the slow and long links drawn before the autorouter) may be moved by the late passes, like the router's."""
    return (net in r5_route.POWER or net in r5_route.CRITICAL or net.startswith(('PYRO', 'ARM', 'RAW_ACT_SENSE')) or
            net in ('HSE_IN', 'HSE_OUT', 'USB_DP', 'USB_DM', 'CC1', 'CC2'))


def _key(t):
    if t.GetClass() == 'PCB_VIA':
        q = t.GetPosition()
        return ('v', t.GetNetname(), q.x, q.y)
    a, c = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
    return ('t', t.GetNetname(), t.GetLayer(), min(a, c), max(a, c), t.GetWidth())


def _movable(b):
    """uuids of the copper a forced crossing (shake) may remove: the router's, this script's own and the scripted copper
    of the non-critical nets (critical())."""
    return {t.m_Uuid.AsString() for t in b.GetTracks() if not t.IsLocked() or _key(t) not in SCRIPTED}


def _lock_new(b, before):
    for t in b.GetTracks():
        if t.m_Uuid.AsString() not in before:
            t.SetLocked(True)


def draw(b, net, runs, vias, w):
    """Add the route, locked; returns the new items' uuids."""
    before = {t.m_Uuid.AsString() for t in b.GetTracks()}
    for layer, pts in runs:
        r5_routes.route(b, net, layer, pts, w)
    for v in vias:
        r5_routes.via(b, net, v)
    _lock_new(b, before)
    return [t.m_Uuid.AsString() for t in b.GetTracks() if t.m_Uuid.AsString() not in before]


class Txn:
    """Removals and additions of one rip-up attempt, so it can be undone."""
    def __init__(self, b):
        self.b, self.added, self.removed = b, [], []

    def delete(self, t):
        if t.GetClass() == 'PCB_VIA':
            q = t.GetPosition()
            self.removed.append(('via', t.GetNetname(), (q.x, q.y), t.GetWidth(F), t.GetDrill(), t.IsLocked()))
        else:
            a, c = t.GetStart(), t.GetEnd()
            self.removed.append(('track', t.GetNetname(), t.GetLayer(), (a.x, a.y), (c.x, c.y), t.GetWidth(),
                                 t.IsLocked()))
        self.b.Delete(t)

    def draw(self, net, runs, vias, w):
        self.added += draw(self.b, net, runs, vias, w)

    def undo(self):
        idx = {t.m_Uuid.AsString(): t for t in self.b.GetTracks()}
        for u in self.added:
            if u in idx:
                self.b.Delete(idx[u])
        for r in self.removed:
            if r[0] == 'via':
                _, net, q, d, drill, locked = r
                o = pcbnew.PCB_VIA(self.b)
                o.SetPosition(pcbnew.VECTOR2I(*q))
                o.SetWidth(d)
                o.SetDrill(drill)
            else:
                _, net, lay, a, c, w, locked = r
                o = pcbnew.PCB_TRACK(self.b)
                o.SetLayer(lay)
                o.SetStart(pcbnew.VECTOR2I(*a))
                o.SetEnd(pcbnew.VECTOR2I(*c))
                o.SetWidth(w)
            o.SetNet(self.b.FindNet(net))
            o.SetLocked(locked)
            self.b.Add(o)


def n_open(b, fill=False):
    """Open connections by KiCad's connectivity, as DRC counts them: with the zone fills as saved, or (fill) refilled
    first. The forced moves refill: a track they draw may cut a GND pad's pour patch off, which the saved fill hides
    until the final refill (an NRST hand finish once traded its open connection for a stranded capacitor pad)."""
    if fill:
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    return b.GetConnectivity().GetUnconnectedCount(False)


def _island(b, item, a, radius=12.0, step=0.05):
    """Points inside the copper of item's island (KiCad's connected items: tracks along their centre lines, via and
    pad centres on their layers) within `radius` of a, as (x, y, layer) targets for the grid router."""
    b.BuildConnectivity()
    pts = []
    for o in b.GetConnectivity().GetConnectedItems(item):
        cl = o.GetClass()
        if cl == 'PCB_TRACK':
            if o.GetLayer() not in (F, B, IN2) or mm(o.GetWidth()) < 0.18:
                continue
            ax, ay, cx, cy = mm(o.GetStart().x), mm(o.GetStart().y), mm(o.GetEnd().x), mm(o.GetEnd().y)
            n = max(1, int(math.hypot(cx - ax, cy - ay) / step))
            pts += [(ax + (cx - ax) * k / n, ay + (cy - ay) * k / n, o.GetLayer()) for k in range(n + 1)]
        elif cl == 'PCB_VIA':
            pts += [(mm(o.GetPosition().x), mm(o.GetPosition().y), lay) for lay in (F, B, IN2)]
        elif cl == 'PAD':
            pts += [(mm(o.GetPosition().x), mm(o.GetPosition().y), lay) for lay in (F, B, IN2) if o.IsOnLayer(lay)]
    return sorted(q for q in pts if math.hypot(q[0] - a[0], q[1] - a[1]) <= radius)   # (KiCad's item order may vary)


def _open_pairs(b, nets):
    """The connections of these nets that DRC would list as open, from KiCad's connectivity (no kicad-cli run): each
    net's copper grouped into connected clusters, joined by a minimum spanning tree of the clusters' nearest anchors
    (pad and via centres, track ends). Same form as drc()'s pairs."""
    b.BuildConnectivity()
    cc = b.GetConnectivity()
    out = []
    for net in sorted(nets):
        items = [o for o in b.GetTracks() if o.GetNetname() == net] + \
            [q for f in b.GetFootprints() for q in f.Pads() if q.GetNetname() == net]
        seen, clusters = set(), []
        for o in items:
            if o.m_Uuid.AsString() in seen:
                continue
            grp = []
            for q in [o] + list(cc.GetConnectedItems(o)):
                u = q.m_Uuid.AsString()
                if u in seen or q.GetNetname() != net or q.GetClass() not in ('PCB_TRACK', 'PCB_VIA', 'PAD'):
                    continue
                seen.add(u)
                grp.append(q)
            if grp:                                  # (KiCad's own order of connected items may vary)
                grp.sort(key=lambda q: (q.GetClass(), q.GetPosition().x, q.GetPosition().y,
                                        q.GetEnd().x if q.GetClass() == 'PCB_TRACK' else 0,
                                        q.GetEnd().y if q.GetClass() == 'PCB_TRACK' else 0))
                clusters.append(grp)
        if len(clusters) < 2:
            continue

        def anchors(grp):
            pts = []
            for q in grp:
                if q.GetClass() == 'PCB_TRACK':
                    pts += [(q.m_Uuid.AsString(), (mm(e.x), mm(e.y))) for e in (q.GetStart(), q.GetEnd())]
                else:
                    pts.append((q.m_Uuid.AsString(), (mm(q.GetPosition().x), mm(q.GetPosition().y))))
            return pts
        an = [anchors(g) for g in clusters]
        joined = {0}
        while len(joined) < len(clusters):
            best = None
            for i in joined:
                for j in range(len(clusters)):
                    if j in joined:
                        continue
                    for ua, pa in an[i]:
                        for ub, pb in an[j]:
                            d = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
                            if best is None or d < best[0]:
                                best = (d, j, (ua, pa), (ub, pb))
            joined.add(best[1])
            out.append((net, best[2], best[3]))
    return out


def _route(b, net, a, la, c, lc, w, rip=None, target=None):
    """A route from a to c; with `target` (the item at c), first to any point of target's island. GND stays off
    In2 (the 3V3 fill there is the bottom layer's reference)."""
    lays = (F, B) if net == 'GND' else (F, B, IN2)
    la = None if la is None else (set(la) & set(lays)) or None
    lc = None if lc is None else (set(lc) & set(lays)) or None
    if target is not None:
        tg = _island(b, target, a)
        if tg:
            xs, ys = [a[0]] + [q[0] for q in tg], [a[1]] + [q[1] for q in tg]
            for m in (3, 6):
                box = (min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m)
                try:
                    return r5_maze.maze_multi(b, net, lays, a, c, w=w, a_layers=la, box=box, via_cost=10.0,
                                              rip=rip, rip_cost=8.0, targets=tg)
                except RuntimeError:
                    continue
    for margin in (4, 8, 14, 20):
        try:
            return r5_maze.maze_multi(b, net, lays, a, c, w=w, a_layers=la, c_layers=lc, margin=margin,
                                      via_cost=10.0, rip=rip, rip_cost=8.0)
        except RuntimeError:
            continue
    return None


def _gnd_tie(b, idx, ia, ic):
    """A stranded GND pad, or a stranded GND track end: a via into the In1 plane beside it (locked)."""
    ends = []
    for u, xy in (ia, ic):
        o = idx[u]
        if isinstance(o, pcbnew.PAD) and o.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
            ends.append(((round(mm(o.GetPosition().x), 4), round(mm(o.GetPosition().y), 4)), F if o.IsOnLayer(F) else B,
                         True))
        elif o.GetClass() == 'PCB_TRACK' and o.GetLayer() in (F, B):
            q = min((o.GetStart(), o.GetEnd()), key=lambda q: math.hypot(mm(q.x) - xy[0], mm(q.y) - xy[1]))
            ends.append(((round(mm(q.x), 4), round(mm(q.y), 4)), o.GetLayer(), False))
    for p, lay, is_pad in ends:
        before = {t.m_Uuid.AsString() for t in b.GetTracks()}
        try:
            r5_routes.tie(b, 'GND', p, (r5_routes.escape(b, p, extra=0.7) if is_pad else None) or p, lay, w=0.25,
                          tries=8)
        except RuntimeError:
            continue
        _lock_new(b, before)
        return True
    return False


def prune(b):
    """Delete the router's (unlocked) copper left hanging, whole chains at once: tracks with a free end by KiCad's
    connectivity, repeated until none, then whatever else DRC calls dangling (vias). Returns the count."""
    n = 0
    for _ in range(20):
        while True:
            b.BuildConnectivity()
            c = b.GetConnectivity()
            dead = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and not t.IsLocked() and
                    c.TestTrackEndpointDangling(t, False)]
            if not dead:
                break
            for t in dead:
                b.Delete(t)
            n += len(dead)
        pcbnew.SaveBoard(PCB, b)
        _, _, dangling = drc(PCB)
        idx = _index(b)
        dead = [idx[u] for u in dangling if u in idx and not idx[u].IsLocked()]
        if not dead:
            break
        for t in dead:
            b.Delete(t)
        n += len(dead)
    return n


def _plane_tie(b, idx, ia, ic, net):
    """A 3V3 or 3V3A pad left open: a via beside it into that net's In2 plane (filled after routing), kept only if
    it lands inside the plane's outline."""
    pad = next((idx[u] for u, _ in (ia, ic) if isinstance(idx[u], pcbnew.PAD)), None)
    zone = next((z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == net and z.IsOnLayer(IN2)), None)
    if pad is None or zone is None:
        return False
    p = (round(mm(pad.GetPosition().x), 4), round(mm(pad.GetPosition().y), 4))
    lay = F if pad.IsOnLayer(F) else B
    before = {t.m_Uuid.AsString() for t in b.GetTracks()}
    try:
        v = r5_routes.tie(b, net, p, r5_routes.escape(b, p, extra=0.7) or p, lay, w=0.25, tries=8)
    except RuntimeError:
        return False
    if zone.Outline().Contains(pcbnew.VECTOR2I(MM(v[0]), MM(v[1]))):
        _lock_new(b, before)
        return True
    for t in [t for t in b.GetTracks() if t.m_Uuid.AsString() not in before]:
        b.Delete(t)
    return False


def _gnd_islands(b):
    """GND SMD pads (one list per island) on outer-layer GND fill islands that hold no GND via and no through-hole GND
    pin: their pads reach GND only through the island, which DRC lists as an unconnected zone piece."""
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    anchors = [v.GetPosition() for v in b.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND']
    anchors += [q.GetPosition() for f in b.GetFootprints() for q in f.Pads()
                if q.GetNetname() == 'GND' and q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    out = []
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != 'GND' or z.IsOnLayer(pcbnew.In1_Cu):
            continue
        for lay in (F, B):
            if not z.IsOnLayer(lay):
                continue
            fill = z.GetFilledPolysList(lay)
            for k in range(fill.OutlineCount()):
                ol = fill.Outline(k)
                if any(ol.PointInside(q) for q in anchors):
                    continue
                pads = [q for f in b.GetFootprints() for q in f.Pads() if q.GetNetname() == 'GND' and
                        q.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and q.IsOnLayer(lay) and ol.PointInside(q.GetPosition())]
                if pads and not any(_reaches_plane(b, q) for q in pads):
                    out.append(sorted(pads, key=lambda q: (q.GetPosition().x, q.GetPosition().y)))
    return sorted(out, key=lambda ps: (ps[0].GetPosition().x, ps[0].GetPosition().y))


def _reaches_plane(b, pad):
    """The pad's own copper (tracks, vias, pads; not the pours) reaches a GND via or through-hole GND pin."""
    for o in b.GetConnectivity().GetConnectedItems(pad):
        if o.GetClass() == 'PCB_VIA' or (o.GetClass() == 'PAD' and o.GetAttribute() == pcbnew.PAD_ATTRIB_PTH):
            return True
    return False


def _join_island(b, pads):
    """One of an island's GND pads to the In1 plane: a via beside it, else a track (F.Cu, B.Cu) to the nearest GND
    vias within 6 mm, else the same across the router's copper if that leaves fewer connections open."""
    for q in pads:
        p = (round(mm(q.GetPosition().x), 4), round(mm(q.GetPosition().y), 4))
        lay = F if q.IsOnLayer(F) else B
        before = {t.m_Uuid.AsString() for t in b.GetTracks()}
        try:
            r5_routes.tie(b, 'GND', p, r5_routes.escape(b, p, extra=0.7) or p, lay, w=0.25, tries=8)
            _lock_new(b, before)
            return 'via'
        except RuntimeError:
            pass
    vias = [(mm(v.GetPosition().x), mm(v.GetPosition().y)) for v in b.GetTracks()
            if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND']
    for rip in (None, 'rip'):
        for q in pads:
            p = (round(mm(q.GetPosition().x), 4), round(mm(q.GetPosition().y), 4))
            tg = [(x, y, lay) for x, y in vias if math.hypot(x - p[0], y - p[1]) < 6.0 for lay in (F, B)]
            if not tg:
                continue
            la = {lay for lay in (F, B) if q.IsOnLayer(lay)}
            xs, ys = [p[0]] + [g[0] for g in tg], [p[1]] + [g[1] for g in tg]
            box = (min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2)
            rset = {t.m_Uuid.AsString() for t in b.GetTracks() if not t.IsLocked()} if rip else None
            try:
                found = r5_maze.maze_multi(b, 'GND', (F, B), p, tg[0][:2], w=0.25, a_layers=la, box=box,
                                           via_cost=10.0, rip=rset, rip_cost=8.0, targets=tg)
            except RuntimeError:
                continue
            if not rip:
                draw(b, 'GND', *found, 0.25)
                return 'track'
            base = n_open(b)
            txn = Txn(b)
            for t in conflicts(b, 'GND', *found, 0.25, rset):
                txn.delete(t)
            txn.draw('GND', *found, 0.25)
            pcbnew.ZONE_FILLER(b).Fill(b.Zones())
            if n_open(b) < base:
                return 'crossing'
            txn.undo()
    return None


def rounds(b, st, limit=ROUNDS):
    """Rounds of DRC and routing (see the module docstring) until nothing is open or nothing changes."""
    last = None
    for rnd in range(1, limit + 1):
        pcbnew.SaveBoard(PCB, b)
        pairs, other, dangling = drc(PCB)
        idx = _index(b)
        if any(u in idx and not idx[u].IsLocked() for u in dangling):
            st['cleaned'] += prune(b)                          # left hanging by a crossing: remove, then look again
            continue
        state = sorted(repr(pr) for pr in pairs)
        if not pairs or state == last:
            break
        last = state
        pairs.sort(key=_pair_key)
        done, failed = 0, []
        for net, ia, ic in pairs:                    # free paths first
            if net == 'GND' and _gnd_tie(b, idx, ia, ic):
                done += 1
                continue
            if net in ('3V3', '3V3A') and _plane_tie(b, idx, ia, ic, net):
                done += 1
                continue
            a, la = _point(idx, ia)
            c, lc = _point(idx, ic)
            w = width(net)
            found = _route(b, net, a, la, c, lc, w, target=idx[ic[0]]) or \
                _route(b, net, c, lc, a, la, w, target=idx[ia[0]])
            if found:
                draw(b, net, *found, w)
                done += 1
            else:
                failed.append((net, a, la, c, lc, w, ia[0], ic[0]))
        for net, a, la, c, lc, w, ua, uc in failed:  # then across the router's copper, kept only if it helps
            base = n_open(b)
            rip = {t.m_Uuid.AsString() for t in b.GetTracks() if not t.IsLocked()}
            found = _route(b, net, a, la, c, lc, w, rip, target=_index(b).get(uc))   # (it may have been ripped)
            if not found:
                continue
            txn = Txn(b)
            gone = conflicts(b, net, *found, w, rip)
            nets = {t.GetNetname() for t in gone}
            for t in gone:
                txn.delete(t)
            txn.draw(net, *found, w)
            while True:                              # the crossed connections' remains (router tracks left hanging)
                b.BuildConnectivity()
                cc = b.GetConnectivity()
                dead = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and not t.IsLocked() and
                        t.GetNetname() in nets and cc.TestTrackEndpointDangling(t, False)]
                if not dead:
                    break
                for t in dead:
                    txn.delete(t)
            again = _open_pairs(b, nets)
            for net2, ia, ic in again:               # draw the connections the crossing opened
                idx2 = _index(b)                     # (afresh: the previous one may have deleted items)
                if net2 not in nets or ia[0] not in idx2 or ic[0] not in idx2:
                    continue
                a2, la2 = _point(idx2, ia)
                c2, lc2 = _point(idx2, ic)
                w2 = width(net2)
                f2 = _route(b, net2, a2, la2, c2, lc2, w2)
                if not f2:                           # one level deeper: it may cross other router copper too
                    rip2 = {t.m_Uuid.AsString() for t in b.GetTracks() if not t.IsLocked()}
                    f2 = _route(b, net2, a2, la2, c2, lc2, w2, rip2)
                    if f2:
                        for t in conflicts(b, net2, *f2, w2, rip2):
                            txn.delete(t)
                if f2:
                    txn.draw(net2, *f2, w2)
            now = n_open(b)
            if now < base:
                st['ripped'] += len(gone)
                done += 1
                print(f'    {net}: crossed {len(gone)} router items of {", ".join(sorted(nets))}; open {base} -> {now}')
            else:
                txn.undo()
        st['total'] += done
        print(f'  round {rnd}: {len(pairs)} open, {done} drawn' + (f'; {len(other)} zone islands' if other else ''))
        if not done:
            break


def islands(b):
    """Join every outer-pour GND island it can (_join_island)."""
    joined, tried = {}, set()
    while True:                                      # GND pads stranded on outer-pour islands
        islands = [ps for ps in _gnd_islands(b) if ps[0].m_Uuid.AsString() not in tried]
        if not islands:
            break
        for pads in islands:
            tried.add(pads[0].m_Uuid.AsString())
            how = _join_island(b, pads)
            if how:
                joined[how] = joined.get(how, 0) + 1
                break                                # the fill changes: look again
    print(f'  GND islands joined: {joined or "none"}; tried without success: {len(tried) - sum(joined.values())}')


def _snapshot(b):
    out = []
    for t in b.GetTracks():
        u = t.m_Uuid.AsString()
        if t.GetClass() == 'PCB_VIA':
            q = t.GetPosition()
            out.append((u, 'via', t.GetNetname(), (q.x, q.y), t.GetWidth(F), t.GetDrill(), t.IsLocked()))
        else:
            a, c = t.GetStart(), t.GetEnd()
            out.append((u, 'track', t.GetNetname(), t.GetLayer(), (a.x, a.y), (c.x, c.y), t.GetWidth(), t.IsLocked()))
    return out


def _restore(b, snap):
    """The tracks and vias as they were at the snapshot, touching only what changed: items added since are removed and
    items removed since are drawn again (deleting and redrawing the whole board each time made KiCad crash)."""
    keep = {r[0] for r in snap}
    present = set()
    for t in list(b.GetTracks()):
        u = t.m_Uuid.AsString()
        if u in keep:
            present.add(u)
        else:
            b.Delete(t)
    for r in snap:
        if r[0] in present:
            continue
        if r[1] == 'via':
            _, _, net, q, d, drill, locked = r
            o = pcbnew.PCB_VIA(b)
            o.SetPosition(pcbnew.VECTOR2I(*q))
            o.SetWidth(d)
            o.SetDrill(drill)
        else:
            _, _, net, lay, a, c, w, locked = r
            o = pcbnew.PCB_TRACK(b)
            o.SetLayer(lay)
            o.SetStart(pcbnew.VECTOR2I(*a))
            o.SetEnd(pcbnew.VECTOR2I(*c))
            o.SetWidth(w)
        o.SetNet(b.FindNet(net))
        o.SetLocked(locked)
        b.Add(o)


def shake(b, st, tries=5):
    """The connections still open, one at a time: drawn across the movable copper (_movable: the router's, this script's
    own, the non-critical scripted links) whatever that opens, then the rounds again for what it opened; kept only if
    fewer connections are open in the end, else the board is put back as it was (a larger move than the rounds' own
    crossings, which must pay off at once)."""
    n = 0
    while n < tries:
        pcbnew.SaveBoard(PCB, b)
        pairs, _, _ = drc(PCB)
        if not pairs:
            return
        pairs.sort(key=_pair_key)
        base = n_open(b, fill=True)
        kept = False
        for k in range(len(pairs)):
            if n >= tries:
                break
            n += 1
            if k:                                    # the board was put back: its items are new, look again
                pcbnew.SaveBoard(PCB, b)
                pairs, _, _ = drc(PCB)
                pairs.sort(key=_pair_key)
                if k >= len(pairs):
                    break
            net, ia, ic = pairs[k]
            idx = _index(b)
            a, la = _point(idx, ia)
            c, lc = _point(idx, ic)
            w = width(net)
            rip = _movable(b)
            found = _route(b, net, a, la, c, lc, w, rip, target=idx[ic[0]])
            if not found:
                continue
            snap = _snapshot(b)
            gone = conflicts(b, net, *found, w, rip)
            for t in gone:
                b.Delete(t)
            draw(b, net, *found, w)
            prune(b)
            rounds(b, st, 3)
            now = n_open(b, fill=True)
            if now < base:
                print(f'    shake: {net} forced across {len(gone)} router items; open {base} -> {now}')
                kept = True
                break
            _restore(b, snap)
        if not kept:
            return


def shake_islands(b, st, tries=3):
    """The GND islands _join_island could not join: a track from one of the island's pads to the nearest GND vias within
    6 mm (F.Cu, B.Cu) across the movable copper (_movable) whatever that opens, then the rounds again; kept only if
    fewer connections are open in the end, else the board is put back."""
    n = 0
    tried = set()
    while n < tries:
        isl = [ps for ps in _gnd_islands(b) if ps[0].m_Uuid.AsString() not in tried]
        if not isl:
            return
        pads = isl[0]
        tried.add(pads[0].m_Uuid.AsString())
        n += 1
        base = n_open(b, fill=True)
        rset = _movable(b)
        vias = [(mm(v.GetPosition().x), mm(v.GetPosition().y)) for v in b.GetTracks()
                if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND']
        found = None
        for q in pads:
            p = (round(mm(q.GetPosition().x), 4), round(mm(q.GetPosition().y), 4))
            tg = [(x, y, lay) for x, y in vias if math.hypot(x - p[0], y - p[1]) < 6.0 for lay in (F, B)]
            if not tg:
                continue
            xs, ys = [p[0]] + [g[0] for g in tg], [p[1]] + [g[1] for g in tg]
            try:
                found = r5_maze.maze_multi(b, 'GND', (F, B), p, tg[0][:2], w=0.25,
                                           a_layers={lay for lay in (F, B) if q.IsOnLayer(lay)},
                                           box=(min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2), via_cost=10.0,
                                           rip=rset, rip_cost=8.0, targets=tg)
                break
            except RuntimeError:
                continue
        if found is None:
            continue
        snap = _snapshot(b)
        gone = conflicts(b, 'GND', *found, 0.25, rset)
        for t in gone:
            b.Delete(t)
        draw(b, 'GND', *found, 0.25)
        prune(b)
        rounds(b, st, 3)
        now = n_open(b, fill=True)
        if now < base:
            print(f'    shake: GND island joined across {len(gone)} router items; open {base} -> {now}')
            tried.clear()
            continue
        _restore(b, snap)


def force_all(b, st):
    """--force (before a warm-started second Freerouting session, r5_build.sh): every connection still open is drawn
    across the router's copper whatever that opens, locked, and the rounds run again; what the crossings leave open
    is the second session's work."""
    for _ in range(2):
        pcbnew.SaveBoard(PCB, b)
        pairs, _, _ = drc(PCB)
        if not pairs:
            return
        idx = _index(b)
        drawn = 0
        for net, ia, ic in sorted(pairs, key=lambda pr: math.hypot(pr[1][1][0] - pr[2][1][0],
                                                                    pr[1][1][1] - pr[2][1][1])):
            if ia[0] not in idx or ic[0] not in idx:
                continue
            a, la = _point(idx, ia)
            c, lc = _point(idx, ic)
            w = width(net)
            rip = {t.m_Uuid.AsString() for t in b.GetTracks() if not t.IsLocked()}
            found = _route(b, net, a, la, c, lc, w, rip, target=idx[ic[0]])
            if not found:
                continue
            for t in conflicts(b, net, *found, w, rip):
                b.Delete(t)
            draw(b, net, *found, w)
            drawn += 1
            print(f'    force: {net}')
            idx = _index(b)
        prune(b)
        rounds(b, st, 3)
        if not drawn:
            return


# Hand finish: connections the routers leave open on this session, each drawn the way a person would finish it.
# (net, end a, end c): drawn across the movable copper, what it cuts drawn again (_force); or
# (net, end a, end c, areas whose movable copper (_movable) may be cleared, waypoints): an
# end is (ref, pad) or (x, y); an area is (x0, y0, x1, y1) on every routing layer, or (x0, y0, x1, y1, layer) on one
# (the vias in it cleared either way); the route passes the waypoints
# (x, y, layer) in order. Kept only if fewer connections are open afterwards (the rounds redraw what the clearing
# opened).
LATE = [
    # VLOGIC_SENSE (U1.17) and V3V3_SENSE (U1.18) leave neighbouring pins; forced across, either cut the other. A via
    # 0.25 mm off the pad row's line clears V3V3_SENSE's F.Cu lane; NRST's In2 copper round it is redrawn by the rounds
    ('VLOGIC_SENSE', ('U1', '17'), (32.50, 24.80), [(30.6, 33.0, 31.2, 34.5, IN2)], [(30.75, 33.75, IN2)]),
]


def _spec(b, s):
    if isinstance(s[0], str):
        q = next(p for p in b.FindFootprintByReference(s[0]).Pads() if p.GetNumber() == s[1])
        return (round(mm(q.GetPosition().x), 4), round(mm(q.GetPosition().y), 4)), \
            {lay for lay in (F, B, IN2) if q.IsOnLayer(lay)}, q
    return (s[0], s[1]), None, None


def _force(b, st, net, sa, sc):
    """A LATE entry of three (net, end a, end c): the net's open connection nearest end a drawn across the movable
    copper as shake() draws it, then each connection that cuts drawn again at once, before the rounds (in the rounds'
    order one could take the next one's way); kept only if fewer connections stay open."""
    pa = _spec(b, sa)[0]
    pairs = _open_pairs(b, {net})
    if not pairs:
        print(f'    late: {net} {sa}->{sc}: nothing open')
        return
    net, ia, ic = min(pairs, key=lambda pr: min(math.hypot(q[1][0] - pa[0], q[1][1] - pa[1]) for q in pr[1:]))
    idx = _index(b)
    a, la = _point(idx, ia)
    c, lc = _point(idx, ic)
    base = n_open(b, fill=True)
    snap = _snapshot(b)
    w = width(net)
    rip = _movable(b)
    found = _route(b, net, a, la, c, lc, w, rip, target=idx[ic[0]])
    if not found:
        print(f'    late: {net} {sa}->{sc} not kept (no path)')
        return
    gone = conflicts(b, net, *found, w, rip)
    cut = {t.GetNetname() for t in gone}
    for t in gone:
        b.Delete(t)
    draw(b, net, *found, w)
    for n2, ia, ic in _open_pairs(b, cut):
        idx = _index(b)
        if ia[0] not in idx or ic[0] not in idx:
            continue
        a2, la2 = _point(idx, ia)
        c2, lc2 = _point(idx, ic)
        f2 = _route(b, n2, a2, la2, c2, lc2, width(n2), target=idx[ic[0]])
        if f2:
            draw(b, n2, *f2, width(n2))
    prune(b)
    rounds(b, st, 4)
    now = n_open(b, fill=True)
    if now < base:
        print(f'    late: {net} {sa}->{sc} forced across {len(gone)} items of {", ".join(sorted(cut))}; open {base} -> {now}')
    else:
        _restore(b, snap)
        print(f'    late: {net} {sa}->{sc} not kept (open {base} -> {now})')


def late(b, st):
    for entry in LATE:
        if len(entry) == 3:
            _force(b, st, *entry)
            continue
        net, sa, sc, areas, waypoints = entry
        a, la, oa = _spec(b, sa)
        c, lc, oc = _spec(b, sc)
        base = n_open(b, fill=True)
        snap = _snapshot(b)
        gone = 0
        for t in list(b.GetTracks()):
            if (t.IsLocked() and _key(t) in SCRIPTED) or t.GetNetname() == net:
                continue
            bb = t.GetBoundingBox()
            x0, y0, x1, y1 = mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())
            if any(x1 >= ar[0] and x0 <= ar[2] and y1 >= ar[1] and y0 <= ar[3] and
                   (len(ar) < 5 or t.GetClass() == 'PCB_VIA' or t.GetLayer() == ar[4]) for ar in areas):
                b.Delete(t)
                gone += 1
        w = width(net)
        lays = (F, B) if net == 'GND' else (F, B, IN2)       # (GND stays off In2, as in _route)
        pts = [(a, la)] + [((x, y), {lay}) for x, y, lay in waypoints] + [(c, lc)]
        ok = True
        for (p0, l0), (p1, l1) in zip(pts, pts[1:]):
            found = None
            l0 = None if l0 is None else (set(l0) & set(lays)) or None
            l1 = None if l1 is None else (set(l1) & set(lays)) or None
            for m in (3, 6, 10):
                try:
                    found = r5_maze.maze_multi(b, net, lays, p0, p1, w=w, a_layers=l0, c_layers=l1, margin=m,
                                               via_cost=10.0)
                    break
                except RuntimeError:
                    continue
            if found is None:
                ok = False
                break
            draw(b, net, *found, w)
        if ok:
            prune(b)
            rounds(b, st, 4)
        now = n_open(b, fill=True)
        if ok and now < base:
            print(f'    late: {net} {sa}->{sc} drawn, {gone} router items cleared; open {base} -> {now}')
        else:
            _restore(b, snap)
            print(f'    late: {net} {sa}->{sc} not kept ({"no path" if not ok else f"open {base} -> {now}"})')


def late_islands(b, st, tries=4):
    """GND pads still stranded on outer-pour islands: for each, first a via of its own beside it, then a GND track (F.Cu,
    B.Cu) to the nearest GND vias, through-hole GND pins and GND pads that reach the plane within 5 mm, in turn, the
    movable copper (_movable) in a box round the pad (and the target) cleared first and the rounds run for what the
    clearing opened; kept only if fewer connections are open afterwards, else the board is put back."""
    done = set()
    while True:
        isl = [ps for ps in _gnd_islands(b) if ps[0].m_Uuid.AsString() not in done]
        if not isl:
            return
        pads = isl[0]
        done.add(pads[0].m_Uuid.AsString())
        tg = [(mm(v.GetPosition().x), mm(v.GetPosition().y)) for v in b.GetTracks()
              if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND']
        tg += [(mm(q.GetPosition().x), mm(q.GetPosition().y)) for f in b.GetFootprints() for q in f.Pads()
               if q.GetNetname() == 'GND' and q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
        b.BuildConnectivity()
        tg += [(mm(q.GetPosition().x), mm(q.GetPosition().y)) for f in b.GetFootprints() for q in f.Pads()
               if q.GetNetname() == 'GND' and q.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and q not in pads and
               _reaches_plane(b, q)]                 # GND pads that reach the plane through their own copper
        kept = False
        for q in pads:
            p = (round(mm(q.GetPosition().x), 4), round(mm(q.GetPosition().y), 4))
            own = F if q.IsOnLayer(F) else B
            near = sorted((g for g in tg if math.hypot(g[0] - p[0], g[1] - p[1]) < 5.0),
                          key=lambda g: math.hypot(g[0] - p[0], g[1] - p[1]))[:tries]
            for m in (1.5, 2.5):                     # first a via of its own beside the pad, in a cleared box
                base = n_open(b, fill=True)
                snap = _snapshot(b)
                gone = 0
                for t in list(b.GetTracks()):
                    if (t.IsLocked() and _key(t) in SCRIPTED) or t.GetNetname() == 'GND':
                        continue
                    bb = t.GetBoundingBox()
                    if mm(bb.GetRight()) >= p[0] - m and mm(bb.GetX()) <= p[0] + m and \
                            mm(bb.GetBottom()) >= p[1] - m and mm(bb.GetY()) <= p[1] + m:
                        b.Delete(t)
                        gone += 1
                before = {o.m_Uuid.AsString() for o in b.GetTracks()}
                try:
                    r5_routes.tie(b, 'GND', p, r5_routes.escape(b, p, extra=0.7) or p, own, w=0.25, tries=8)
                    ok = True
                except RuntimeError:
                    ok = False
                if ok:
                    _lock_new(b, before)
                    prune(b)
                    rounds(b, st, 3)
                now = n_open(b, fill=True)
                if ok and now < base:
                    print(f'    island: {q.GetParentFootprint().GetReference()}.{q.GetNumber()} via of its own, '
                          f'{gone} items cleared; open {base} -> {now}')
                    kept = True
                    break
                _restore(b, snap)
            if kept:
                break
            for g in near:
                base = n_open(b, fill=True)
                snap = _snapshot(b)
                box = (min(p[0], g[0]) - 1.0, min(p[1], g[1]) - 1.0, max(p[0], g[0]) + 1.0, max(p[1], g[1]) + 1.0)
                gone = 0
                for t in list(b.GetTracks()):
                    if (t.IsLocked() and _key(t) in SCRIPTED) or t.GetNetname() == 'GND':
                        continue
                    bb = t.GetBoundingBox()
                    if mm(bb.GetRight()) >= box[0] and mm(bb.GetX()) <= box[2] and mm(bb.GetBottom()) >= box[1] and \
                            mm(bb.GetY()) <= box[3]:
                        b.Delete(t)
                        gone += 1
                found = None
                for m in (1.5, 3.0):
                    try:
                        found = r5_maze.maze_multi(b, 'GND', (F, B), p, g, w=0.25, a_layers={own}, margin=m,
                                                   via_cost=10.0)
                        break
                    except RuntimeError:
                        continue
                if found:
                    draw(b, 'GND', *found, 0.25)
                    prune(b)
                    rounds(b, st, 3)
                now = n_open(b, fill=True)
                if found and now < base:
                    print(f'    island: {q.GetParentFootprint().GetReference()}.{q.GetNumber()} to GND at '
                          f'({g[0]:.2f}, {g[1]:.2f}), {gone} items cleared; open {base} -> {now}')
                    kept = True
                    break
                _restore(b, snap)
            if kept:
                break
        if kept:
            done.clear()


def _drop_unused(b):
    """Fan-out vias and stubs that ended up unused (their pin reached its net another way), locked or not: removed while
    DRC calls them dangling, one at a time, each put back if KiCad's connectivity (zones refilled) then counts more open
    connections (DRC's view of a track ending in a pour is not the same on every run). Returns (open pairs, other open
    items, count removed)."""
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
    left, other, dangling = drc(PCB)
    base = n_open(b)
    unused = 0
    for _ in range(10):
        idx = _index(b)
        dead = [idx[u] for u in sorted(dangling) if u in idx]
        removed = 0
        for o in dead:
            snap = _snapshot(b)
            b.Delete(o)
            if n_open(b, fill=True) > base:
                _restore(b, snap)
            else:
                removed += 1
        if not removed:
            break
        unused += removed
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        pcbnew.SaveBoard(PCB, b)
        left, other, dangling = drc(PCB)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
    return left, other, unused


def _jkey(t):
    """A track's or via's geometry as a JSON-friendly key (layer by name)."""
    if t.GetClass() == 'PCB_VIA':
        q = t.GetPosition()
        return ('v', t.GetNetname(), q.x, q.y)
    a, c = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
    a, c = min(a, c), max(a, c)
    return ('t', t.GetNetname(), pcbnew.LayerName(t.GetLayer()), a[0], a[1], c[0], c[1], t.GetWidth())


def _record(b, start, path):
    """The finisher's result as a session file, as Freerouting's is kept: the import board's copper it removed and the
    copper it added. r5_build.sh replays it (--replay), so the board rebuilds the same: the search itself is not
    repeatable, because KiCad's DRC reports one and the same open connection now as a pair of items, now as two pour
    pieces, and the rounds take their work from that list."""
    end = {_jkey(o): o for o in b.GetTracks()}
    added = []
    for k, o in end.items():
        if k in start:
            continue
        added.append({'item': list(k), 'drill': o.GetDrill() if o.GetClass() == 'PCB_VIA' else 0,
                      'size': o.GetWidth(F) if o.GetClass() == 'PCB_VIA' else 0, 'locked': o.IsLocked()})
    out = {'removed': sorted(list(k) for k in start if k not in end), 'added': sorted(added, key=lambda d: d['item'])}
    Path(path).write_text(json.dumps(out, indent=0) + '\n')
    print(f'  recorded {len(out["removed"])} removals and {len(added)} additions in {Path(path).name}')


def _replay(b, path):
    """Apply a session recorded by --record to the board as r5_route.py import left it."""
    d = json.loads(Path(path).read_text())
    gone = {tuple(k) for k in d['removed']}
    hit = 0
    for o in list(b.GetTracks()):
        if _jkey(o) in gone:
            b.Delete(o)
            hit += 1
    if hit != len(gone):
        raise RuntimeError(f'replay: {len(gone) - hit} of the recorded removals are not on this board (not the board '
                           'the session was recorded on)')
    for it in d['added']:
        k = it['item']
        if k[0] == 'v':
            o = pcbnew.PCB_VIA(b)
            o.SetPosition(pcbnew.VECTOR2I(k[2], k[3]))
            o.SetWidth(it['size'])
            o.SetDrill(it['drill'])
        else:
            o = pcbnew.PCB_TRACK(b)
            o.SetLayer(b.GetLayerID(k[2]))
            o.SetStart(pcbnew.VECTOR2I(k[3], k[4]))
            o.SetEnd(pcbnew.VECTOR2I(k[5], k[6]))
            o.SetWidth(k[7])
        o.SetNet(b.FindNet(k[1]))
        o.SetLocked(it['locked'])
        b.Add(o)
    print(f'  replayed {path.split("/")[-1]}: {hit} removals, {len(d["added"])} additions')


def main():
    pcbnew.KIID.SeedGenerator(5103)   # repeatable UUIDs, so kicad-cli lists the open connections in the same
    b = pcbnew.LoadBoard(PCB)          # order every run (r5_pcb.main)
    replay = next((x.split('=', 1)[1] for x in sys.argv if x.startswith('--replay=')), None)
    if replay:
        _replay(b, replay)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        pcbnew.SaveBoard(PCB, b)
        left, other, _ = drc(PCB)
        print(f'finished (replayed): still open: {len(left)} connections, {len(other)} other')
        for o in left + other:
            print('   ', o)
        return
    start = {_jkey(t) for t in b.GetTracks()}
    SCRIPTED.update(_key(t) for t in b.GetTracks() if t.IsLocked() and critical(t.GetNetname()))
    narrow = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and not t.IsLocked() and
              mm(t.GetWidth()) < r5_route.router_width(t.GetNetname()) - 1e-6]
    for t in narrow:
        b.Delete(t)
    cleaned = prune(b)
    print(f'  {len(narrow)} router tracks under their router width removed, then {cleaned} items they left hanging')
    n_keep = r5_route.reference_keepouts(b)
    keep = [z for z in b.Zones() if z.GetIsRuleArea() and not z.GetZoneName()]
    st = {'total': 0, 'ripped': 0, 'cleaned': cleaned}
    rounds(b, st)
    islands(b)
    for _ in range(3):                               # the forced moves, while they gain anything
        base = n_open(b, fill=True)
        if '--shake' in sys.argv:
            shake_islands(b, st)
        late_islands(b, st)
        if '--shake' in sys.argv:
            shake(b, st)
            islands(b)
        if n_open(b, fill=True) >= base:
            break
    early = _drop_unused(b)[2] if LATE else 0         # the hand finish works on the board as it will end up
    snap = next((x.split('=', 1)[1] for x in sys.argv if x.startswith('--snapshot=')), None)
    if snap:                                         # the board before the hand finish (to work out LATE entries)
        pcbnew.SaveBoard(snap, b)
        pcbnew.SaveBoard(PCB, b)
    if LATE:
        late(b, st)
        islands(b)
    if '--force' in sys.argv:
        force_all(b, st)
    for z in keep:
        b.Delete(z)
    b.BuildConnectivity()
    left, other, unused = _drop_unused(b)
    unused += early
    if unused:
        print(f'  {unused} unused fan-out items removed')
    record = next((x.split('=', 1)[1] for x in sys.argv if x.startswith('--record=')), None)
    if record:
        _record(b, start, record)
    print(f'finished: {st["total"]} connections drawn, {st["ripped"]} router items crossed and removed, {st["cleaned"]} dangling '
          f'removed ({n_keep} In2 keep-outs used); still open: {len(left)} connections, {len(other)} other')
    idx = _index(b)
    for net, ia, ic in left:
        names = []
        for u, xy in (ia, ic):
            o = idx.get(u)
            names.append(f'{o.GetParentFootprint().GetReference()}.{o.GetNumber()}' if isinstance(o, pcbnew.PAD)
                         else f'{"via" if o and o.GetClass() == "PCB_VIA" else "track"}@({xy[0]:.2f},{xy[1]:.2f})')
        print('   ', net, ' - '.join(names))
    for o in other:
        print('   ', o)


if __name__ == '__main__':
    main()
