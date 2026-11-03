#!/usr/bin/env python3
"""R7 routing hygiene: canonical copper on the whole board (review pass 2 RG-06..RG-10, RG-15, RQ-07, RQ-08).

usage: <KiCad python3> -I m3_design/r7_hygiene.py [--board m3_design/assembly_review/m3.kicad_pcb] [--out PATH]
                                                   [--stop STAGE] [--start STAGE] [--quiet]

The last copper stage of m3_design/r7_build.sh (after r7_rework.py; r7_post.py, which changes no copper, then places
the silkscreen against the final copper and refills). The board's .kicad_pro / .kicad_dru must sit beside it: the pours
are refilled with the board's own rules after every stage. It changes geometry, never connectivity:
  - after every stage each net's pad groups (tools/route_check.pad_groups: pads joined under KiCad's anchor rule)
    with the pour fills joining too must be exactly what they were, and by tracks and vias alone they may only merge
    (a hand redraw may join by track two pads a pour already joined), never split; the run stops on the first stage
    that breaks this; removals in the generic stages keep both exactly;
  - copper is removed only where it is a copy (same-net copper of at least its width lies over or beside it), dead
    (on no path between two terminals: tools/route_check.dead) or inside a same-net pad; a redrawn conductor keeps at
    least the narrowest width of the path it replaces (necks were widened where the clearances allow; each narrowing
    of a locally wider stretch is named in its stage's docstring with the reason);
  - the CH1 pyro power nets (PYRO1_BUS / PYRO1_IGN / PYRO1_OUT) only lose copper that changes no copper outline
    outside pads (duplicates, pieces inside pads, dead stubs, merged collinear runs, one branch trimmed inside
    Q124.5's pad): their geometry and spacing stay R6's, moved +18 mm.
Stages (deterministic, KIID seed 7501):
  hand redraws (HAND_PRE, on the board r7_rework.py leaves): usb_limited, imu_cs, 3v3a, cam_io_3v3, raw_protected,
               vlogic, vbus, 3v3, camera_power, gnd, power_misc, pyro, signals, spi. Each `replace()` deletes the
               counted tracks of one net and layer inside a box (asserted, so a changed upstream board stops the build
               instead of being patched silently), draws asserted 0/45/90 polylines checked against every other net's
               copper (Clearance: m3.kicad_dru incl. the pyro rules, bare test pads 1.0 mm, Tag-Connect 0.508 mm)
               and places vias checked like r7_route.ViaCheck (keep-outs, edges, paste). The reason for each redraw
               is in its docstring.
  zero_length  zero-length tracks go
  dedupe       exact duplicates and collinear segments inside a wider or equal collinear segment go; collinear partial
               overlaps of one width become one segment, of two widths the narrower is cut back to the wider's end
  inside       segments wholly inside a same-net pad (2 µm margin) go
  near_dup     a run of segments (a chain: through plain nodes) lying within (its width + 0.1 mm) of other same-net
               copper at least as wide, along its whole length, goes, when the joints at its ends stay clean (only
               on a layer where its net has a pour, which fills what the run bridged)
  dead         dead copper (stubs, fold-back overshoots, dead branches; also the vias on them) goes: a track with a
               dead end piece is cut back to the live joint
  merge        collinear segments of one width meeting at a plain node become one
  chains       chains with micro segments (< 50 µm), acute turns or tiny jogs are re-solved with their headings kept
               (then merge, dead and inside again: a re-solved chain can leave a piece wholly inside its pad)
  acute_t      a branch meeting a straight trunk of one width at 45° turns square onto the trunk just before it
  gnd_vias     GND return vias beside critical-signal layer changes (AGENTS.md §3; RG-09 / RG-05), where legal
  hand_post    hand redraws (replace(), as above) of the non-critical residue the generic stages leave: crossings,
               a micro hook, necks, tiny jogs, a pour-only stub, and SERVO2_MCU back on R6's line where stage chains
               had necked a GND pour finger out (the reasons, and the jogs left, in its docstring)
The record is sources/r7_review/fix2_F3_handoff.md; tools/route_check.py, run by tools/check.sh, holds the result.
"""
import argparse
import math
from collections import defaultdict
from pathlib import Path
import sys
import time

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import r7_lib as lib  # noqa: E402
import route_check as rc  # noqa: E402

MM, mm = pcbnew.FromMM, pcbnew.ToMM
F, B, IN1, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu
CU4 = (F, IN1, IN2, B)
TOL = rc.TOL                    # nm: end points within 1 µm are one node
PROTECTED = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')
# the 7.7 A servo path (REQUIREMENTS F4): net -> the parts its tools/dc_solve.py run goes between
HIGH_CURRENT = {'BAT_IN': ('J1', 'Q120'), 'RAW_ACT': ('Q121', 'J122'), 'ACT_FET_S': ('Q120', 'Q121')}


# --- model ------------------------------------------------------------------------------------------------------

def xy(v):
    return v.x, v.y


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def tracks(b):
    return [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']


def vias(b):
    return [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']


def groups(b):
    g = defaultdict(list)
    for t in tracks(b):
        g[(t.GetLayer(), t.GetNetname())].append(t)
    return g


def ends(t):
    return xy(t.GetStart()), xy(t.GetEnd())


def length(t):
    return dist(*ends(t))


def V(p):
    return pcbnew.VECTOR2I(int(round(p[0])), int(round(p[1])))


def loc(p):
    return round(mm(p[0]), 4), round(mm(p[1]), 4)


def pad_groups(b, nets=None, skip=()):
    """{net: (pad groups by tracks and vias, pad groups with the pour fills joining too)} (route_check.pad_groups) for
    nets (all when None), without the items in skip. The fills are the board's last fill."""
    sk = frozenset()
    ids = {x.m_Uuid.AsString() for x in skip}
    out = {}
    for net, nc in rc.collect(b, nets).items():
        if ids:                     # the objects in nc are fresh wrappers: match the skipped items by their KIID
            sk = frozenset(id(t['obj']) for t in nc.tracks + nc.vias if t['obj'].m_Uuid.AsString() in ids)
        out[net] = (rc.pad_groups(nc, sk), rc.pad_groups(nc, sk, zones=True))
    return out


def _merged_only(before, after):
    """Whether every group of `after` is a union of whole groups of `before` (tracks may join pads, never split them)."""
    owner = {}
    for k, g in enumerate(after):
        for p in g:
            owner[p] = k
    return set(owner) == {p for g in before for p in g} and all(len({owner[p] for p in g}) == 1 for g in before)


def same_groups(before, after):
    """Nets whose connectivity changed: their pad groups with the pours (the copper's real connectivity) must be
    identical; by tracks and vias alone, groups may only merge (a track that now joins two pads the pour already
    joined), never split."""
    bad = []
    for n in sorted(set(before) | set(after)):
        b0, a0 = before.get(n, (frozenset(), frozenset())), after.get(n, (frozenset(), frozenset()))
        if b0[1] != a0[1] or not _merged_only(b0[0], a0[0]):
            bad.append(n)
    return bad


def keeps_groups(b, net, skip):
    """Whether net's pad groups (by tracks and with the pours) stay exactly the same without the items in skip."""
    return pad_groups(b, {net}) == pad_groups(b, {net}, skip)


def on_body(o, p):
    """Whether p lies on o's centre line (within TOL), away from its ends."""
    a, c = ends(o)
    L = dist(a, c)
    if L == 0:
        return False
    t = ((p[0] - a[0]) * (c[0] - a[0]) + (p[1] - a[1]) * (c[1] - a[1])) / (L * L)
    if not (TOL < t * L < L - TOL):
        return False
    return abs((p[0] - a[0]) * (c[1] - a[1]) - (p[1] - a[1]) * (c[0] - a[0])) / L <= TOL


def new_track(b, net, lay, a, c, w):
    u = pcbnew.PCB_TRACK(b)
    u.SetLayer(lay)
    u.SetWidth(int(w))
    u.SetNet(b.FindNet(net) if isinstance(net, str) else net)
    u.SetStart(V(a))
    u.SetEnd(V(c))
    b.Add(u)
    return u


# --- generic stages -----------------------------------------------------------------------------------------------

def zero_length(b, log):
    gone = [t for t in tracks(b) if length(t) == 0]
    for t in gone:
        b.Delete(t)
    log.append(f'zero_length: {len(gone)} removed')


def collinear_spans(t, u):
    """(Lt, lo, hi) when u's centre line lies on t's within TOL (projections of u's ends on t), else None."""
    a, c = ends(t)
    p, q = ends(u)
    L = dist(a, c)
    Lu = dist(p, q)
    if L == 0 or Lu == 0:
        return None
    ux, uy = (c[0] - a[0]) / L, (c[1] - a[1]) / L
    vx, vy = (q[0] - p[0]) / Lu, (q[1] - p[1]) / Lu
    if abs(ux * vy - uy * vx) > 1e-4:
        return None
    off = max(abs((p[0] - a[0]) * uy - (p[1] - a[1]) * ux), abs((q[0] - a[0]) * uy - (q[1] - a[1]) * ux))
    if off > TOL:
        return None
    t1 = (p[0] - a[0]) * ux + (p[1] - a[1]) * uy
    t2 = (q[0] - a[0]) * ux + (q[1] - a[1]) * uy
    return L, min(t1, t2), max(t1, t2)


def dedupe(b, log):
    """Duplicates, contained collinear segments and collinear partial overlaps (the copper outline is unchanged)."""
    counts = defaultdict(int)
    changed = True
    while changed:
        changed = False
        for key, g in sorted(groups(b).items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
            g = sorted(g, key=lambda t: (-t.GetWidth(), -length(t), ends(t)))
            for i, t in enumerate(g):
                for u in g[i + 1:]:
                    s = collinear_spans(t, u)
                    if s is None:
                        continue
                    L, lo, hi = s
                    ov = min(hi, L) - max(lo, 0)
                    if ov <= TOL:
                        continue
                    wt, wu = t.GetWidth(), u.GetWidth()
                    if lo >= -TOL and hi <= L + TOL and wu <= wt:
                        b.Delete(u)
                        counts['contained' if (hi - lo) < L - TOL or wu < wt else 'duplicate'] += 1
                    elif lo <= TOL and hi >= L - TOL and wt <= wu:
                        b.Delete(t)
                        counts['contained'] += 1
                    elif wt == wu:
                        pts = list(ends(t)) + list(ends(u))
                        a = ends(t)[0]
                        L_ = length(t)
                        d = ((ends(t)[1][0] - a[0]) / L_, (ends(t)[1][1] - a[1]) / L_)
                        pts.sort(key=lambda p: (p[0] - a[0]) * d[0] + (p[1] - a[1]) * d[1])
                        t.SetStart(V(pts[0]))
                        t.SetEnd(V(pts[-1]))
                        b.Delete(u)
                        counts['partial, one width: merged'] += 1
                    else:
                        wide, narrow = (t, u) if wt > wu else (u, t)
                        Lw, lo2, hi2 = collinear_spans(wide, narrow)
                        wa, wc = ends(wide)
                        na, nc_ = ends(narrow)
                        dvec = ((wc[0] - wa[0]) / Lw, (wc[1] - wa[1]) / Lw)

                        def proj(p):
                            return (p[0] - wa[0]) * dvec[0] + (p[1] - wa[1]) * dvec[1]
                        # the narrow end that lies inside the wide span moves to the wide end beyond it
                        inner_start = -TOL <= proj(na) <= Lw + TOL
                        target = wc if (proj(nc_) if inner_start else proj(na)) > Lw else wa
                        if inner_start:
                            narrow.SetStart(V(target))
                        else:
                            narrow.SetEnd(V(target))
                        counts['partial, two widths: narrower cut back'] += 1
                    changed = True
                    break
                if changed:
                    break
            if changed:
                break
    log.append(f'dedupe: {dict(counts)}')


def _shrunk_pad_polys(b, margin=2000):
    out = defaultdict(list)          # (net, layer) -> [(name, poly, pad)]
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or not p.GetNetname():
                continue
            for lay in CU4:
                if p.IsOnLayer(lay):
                    ps = pcbnew.SHAPE_POLY_SET()
                    p.TransformShapeToPolygon(ps, lay, -margin, 500, pcbnew.ERROR_INSIDE)
                    out[(p.GetNetname(), lay)].append((f'{f.GetReference()}.{p.GetNumber()}', ps, p))
    return out


def inside(b, log):
    """Segments whose whole centre line lies inside one same-net pad (2 µm margin): the pad already joins whatever
    ends on them."""
    polys = _shrunk_pad_polys(b)
    gone = []
    for t in tracks(b):
        a, c = ends(t)
        n = max(1, int(dist(a, c) / 10000))          # sample every 10 µm (pads may be non-convex)
        pts = [V((a[0] + (c[0] - a[0]) * k / n, a[1] + (c[1] - a[1]) * k / n)) for k in range(n + 1)]
        for name, ps, p in polys.get((t.GetNetname(), t.GetLayer()), []):
            if all(ps.Contains(q) for q in pts):
                gone.append((t, name))
                break
    kept = []
    for t, name in gone:
        if keeps_groups(b, t.GetNetname(), [t]):
            b.Delete(t)
        else:
            kept.append((t.GetNetname(), name))
    log.append(f'inside: {len(gone) - len(kept)} segments inside their pad removed; kept: {kept}')


def _nodes(group):
    """Track-end clusters of one (layer, net) group: point -> [(track, end index)] (points within TOL merged)."""
    at = defaultdict(list)
    for t in group:
        for e, p in enumerate(ends(t)):
            at[p].append((t, e))
    merged = {}
    grid = defaultdict(list)
    for k in sorted(at):
        g = (round(k[0] / TOL), round(k[1] / TOL))
        hit = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for q in grid[(g[0] + dx, g[1] + dy)]:
                    if dist(q, k) <= TOL:
                        hit = q
        if hit is None:
            merged[k] = list(at[k])
            grid[g].append(k)
        else:
            merged[hit] += at[k]
    return merged


def chain_list(b, lay, net, g, via_pts, pads):
    """The chains of one (layer, net) group: [(tracks, points)] with points[0] and points[-1] non-plain nodes (or a
    closed loop)."""
    nodes = _nodes(g)

    def plain(p):
        m = nodes[p]
        if len(m) != 2 or m[0][0] is m[1][0]:
            return False
        if any(dist(v, p) <= TOL for v in via_pts):
            return False
        if any(pd.IsOnLayer(lay) and pd.GetEffectiveShape(lay).Collide(V(p), 0) for pd in pads):
            return False
        return not any(on_body(o, p) for o in g if o is not m[0][0] and o is not m[1][0])
    where = {}
    for p, m in nodes.items():
        for t, e in m:
            where[(t.m_Uuid.AsString(), e)] = p
    out, seen = [], set()
    isplain = {p: plain(p) for p in nodes}
    starts = [p for p in sorted(nodes) if not isplain[p]] + [p for p in sorted(nodes) if isplain[p]]
    for p0 in starts:
        for t0, e0 in nodes[p0]:
            if t0.m_Uuid.AsString() in seen:
                continue
            chain, pts, cur, e = [], [p0], t0, e0
            while True:
                seen.add(cur.m_Uuid.AsString())
                chain.append(cur)
                q = where[(cur.m_Uuid.AsString(), 1 - e)]
                pts.append(q)
                if not isplain[q]:
                    break
                nxt = [(o, oe) for o, oe in nodes[q] if o is not cur]
                if not nxt or nxt[0][0].m_Uuid.AsString() in seen:
                    break
                cur, e = nxt[0]
            out.append((chain, pts))
    return out, isplain


def _poly(item, lay, err, extra=0):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, lay, int(extra), 500, err)
    return ps


def _bbox(item):
    bb = item.GetBoundingBox()
    return bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()


def _touch(p, q, m=0):
    return not (p[2] + m < q[0] or q[2] + m < p[0] or p[3] + m < q[1] or q[3] + m < p[1])


def _in_pad(pd, lay, p, margin=2000):
    """Whether p lies inside pd's copper on lay by at least margin (nm): a track end on the pad's outline is not a
    joint to rely on."""
    if not pd.GetEffectiveShape(lay).Collide(V(p), 0):
        return False
    ps = pcbnew.SHAPE_POLY_SET()
    pd.TransformShapeToPolygon(ps, lay, -margin, 500, pcbnew.ERROR_INSIDE)
    return ps.Contains(V(p))


def clean_without(b, net, lay, gone, pads):
    """Whether removing the tracks in `gone` leaves clean joints: every other track end at their end points stays at
    two or more track ends, a T (on a track's centre line), a via centre or inside a pad (2 µm or more inside its
    outline); and every via or pad one of them reached keeps another track on that layer (or lies in a same-net pour
    there)."""
    ids = {t.m_Uuid.AsString() for t in gone}
    rest = [o for o in tracks(b) if o.GetNetname() == net and o.GetLayer() == lay and o.m_Uuid.AsString() not in ids]
    vs = [v for v in vias(b) if v.GetNetname() == net and v.IsOnLayer(lay)]
    vpts = [xy(v.GetPosition()) for v in vs]
    zs = [z for z in b.Zones() if z.GetNetname() == net and not z.GetIsRuleArea() and z.IsOnLayer(lay)]

    def poured(p, acc=0):
        return any(z.HitTestFilledArea(lay, V(p), int(acc)) for z in zs)
    for t in gone:
        for e in ends(t):
            for v in vs:
                c, r = xy(v.GetPosition()), v.GetWidth(lay) / 2
                if dist(c, e) <= r and any(dist(q, c) <= r for o in rest for q in ends(o)) and \
                        not any(dist(q, c) <= TOL for o in rest for q in ends(o)):
                    return False                  # the tracks left would end in the via off its centre
                if dist(c, e) <= r and not poured(c, r) and \
                        not any(dist(q, c) <= r for o in rest for q in ends(o)):
                    return False                  # the via would lose its last track on this layer
            for pd in pads:
                if pd.IsOnLayer(lay) and pd.GetEffectiveShape(lay).Collide(V(e), 0) and \
                        not any(_in_pad(pd, lay, q) for o in rest for q in ends(o)) and \
                        not any(z.GetFilledPolysList(lay).Collide(pd.GetEffectiveShape(lay), 1000) for z in zs
                                if z.HasFilledPolysForLayer(lay)):
                    return False                  # the pad would lose its last track on this layer
        for e in ends(t):
            mine = [o for o in rest for q in ends(o) if dist(q, e) <= TOL]
            if not mine or len(mine) >= 2:
                continue
            if any(on_body(o, e) for o in rest) or any(dist(v, e) <= TOL for v in vpts):
                continue
            if any(pd.IsOnLayer(lay) and _in_pad(pd, lay, e) for pd in pads):
                continue
            return False
    return True


def near_dup(b, log, slit=MM(0.1)):
    """Chains lying within (their width + slit) of other same-net copper at least as wide (tracks, vias, pads), along
    their whole length, are copies: they go, narrowest first, when the net's pad groups stay the same and the joints
    at their ends stay clean (one chain per layer and net per pass). Only on a layer where the net has a pour: the test
    cannot tell a copy from a short link between two wide features (a pad and a via 1-2 mm apart: their margins
    cover the run), and only a pour fills the gap such a run bridged (without this, 3V3's new L1.2 -> plane-via link
    went and the buck output fed the In2 plane through one via). Copies on other layers are hand redraws, and
    route_check fails any left on a critical net."""
    removed = []
    failed = set()                   # chains (by their tracks' KIIDs) found not removable: removing copper never
    for _ in range(100):             # makes one removable later
        via_by_net = defaultdict(list)
        for v in vias(b):
            via_by_net[v.GetNetname()].append(v)
        pads_by_net = defaultdict(list)
        for f in b.GetFootprints():
            for pd in f.Pads():
                if pd.GetNetname() and pd.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                    pads_by_net[pd.GetNetname()].append(pd)
        poured = {(z.GetNetname(), l) for z in b.Zones() if not z.GetIsRuleArea() for l in CU4 if z.IsOnLayer(l)}
        cands = []
        for (lay, net), g in groups(b).items():
            if net in PROTECTED or not net or (net, lay) not in poured:
                continue
            ch, _ = chain_list(b, lay, net, g, [xy(v.GetPosition()) for v in via_by_net[net]],
                               pads_by_net[net])
            for chain, pts in ch:
                w = max(t.GetWidth() for t in chain)
                cands.append((w, sum(length(t) for t in chain), loc(pts[0]), lay, net, chain))
        cands.sort(key=lambda c: c[:4])
        done = set()
        for w, L, p0, lay, net, chain in cands:
            ids = {t.m_Uuid.AsString() for t in chain}
            sig = tuple(sorted(ids))
            if (lay, net) in done or sig in failed:
                continue
            failed.add(sig)
            box = None
            for t in chain:
                bb = _bbox(t)
                box = bb if box is None else (min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]),
                                              max(box[3], bb[3]))
            others = [o for o in tracks(b) if o.GetNetname() == net and o.GetLayer() == lay and
                      o.m_Uuid.AsString() not in ids and o.GetWidth() >= w and _touch(box, _bbox(o), w + slit)]
            others += [v for v in via_by_net[net] if v.GetWidth(lay) >= w and _touch(box, _bbox(v), w + slit)]
            others += [p for p in pads_by_net[net] if p.IsOnLayer(lay) and _touch(box, _bbox(p), w + slit)]
            if not others:
                continue
            union = pcbnew.SHAPE_POLY_SET()
            for o in others:
                union.BooleanAdd(_poly(o, lay, pcbnew.ERROR_OUTSIDE, w + slit))
            rest = pcbnew.SHAPE_POLY_SET()
            for t in chain:
                rest.BooleanAdd(_poly(t, lay, pcbnew.ERROR_INSIDE))
            rest.BooleanSubtract(union)
            if rest.Area() >= 50e6:              # nm²: 50 µm²
                continue
            if not clean_without(b, net, lay, chain, pads_by_net[net]) or not keeps_groups(b, net, chain):
                continue
            removed.append((net, b.GetLayerName(lay), p0, round(mm(w), 3), len(chain), round(mm(L), 3)))
            for t in chain:
                b.Delete(t)
            done.add((lay, net))
        if not done:
            break
    log.append(f'near_dup: {len(removed)} copied runs removed (net, layer, start, width, segments, length)')
    for r in removed:
        log.append(f'  {r}')


def dead(b, log):
    """Dead copper (route_check.dead): whole tracks and vias go; a track with dead end pieces is cut back to its live
    span (ends at the joints where the live copper meets it)."""
    lib.fill(b)                                     # pour contacts are judged on the current copper
    cut, gone, gone_v = [], [], []
    for _ in range(20):
        changed = False
        for net, nc in sorted(rc.collect(b).items()):
            pieces, dvias = rc.dead(nc, pour_islands=False)
            whole = [nc.tracks[i]['obj'] for i, segs in pieces.items()
                     if sum(s1 - s0 for s0, s1 in segs) >= 1 - 1e-9] + [nc.vias[j]['obj'] for j in dvias]
            if (pieces or dvias) and not keeps_groups(b, net, whole):
                log.append(f'  dead: {net} left (removing its dead copper would change its pad groups under KiCad\'s '
                           f'anchor rule)')
                continue
            for i, segs in pieces.items():
                t = nc.tracks[i]
                obj = t['obj']
                L = dist(t['a'], t['b'])
                segs = [s for s in segs if (s[1] - s[0]) * L > TOL]
                if not segs:
                    continue
                # live span: [0, 1] minus the dead pieces, which must sit at the ends
                lo, hi = 0.0, 1.0
                for s0, s1 in sorted(segs):
                    if s0 <= lo + 1e-9:
                        lo = max(lo, s1)
                for s0, s1 in sorted(segs, reverse=True):
                    if s1 >= hi - 1e-9:
                        hi = min(hi, s0)
                if any(lo + 1e-9 < s0 and s1 < hi - 1e-9 for s0, s1 in segs):
                    log.append(f'  dead: {net} piece inside a live span left at {loc(t["a"])}')
                    continue
                if hi - lo <= 1e-9 or (hi - lo) * L <= TOL:
                    gone.append((net, b.GetLayerName(t['lid']), loc(t['a']), loc(t['b'])))
                    b.Delete(obj)
                else:
                    pa = (t['a'][0] + lo * (t['b'][0] - t['a'][0]), t['a'][1] + lo * (t['b'][1] - t['a'][1]))
                    pb = (t['a'][0] + hi * (t['b'][0] - t['a'][0]), t['a'][1] + hi * (t['b'][1] - t['a'][1]))
                    cut.append((net, b.GetLayerName(t['lid']), loc(t['a']), loc(t['b']), '->', loc(pa), loc(pb)))
                    obj.SetStart(V(pa))
                    obj.SetEnd(V(pb))
                changed = True
            for j in dvias:
                gone_v.append((net, loc(nc.vias[j]['pos'])))
                b.Delete(nc.vias[j]['obj'])
                changed = True
            if changed:
                break
        if not changed:
            break
    log.append(f'dead: {len(gone)} tracks and {len(gone_v)} vias removed, {len(cut)} tracks cut back')
    for x in gone + gone_v + cut:
        log.append(f'  {x}')


def merge(b, log):
    """Collinear segments of one width meeting at a plain node become one."""
    count = 0
    changed = True
    while changed:
        changed = False
        via_pts = defaultdict(list)
        for v in vias(b):
            via_pts[v.GetNetname()].append(xy(v.GetPosition()))
        pads = defaultdict(list)
        for f in b.GetFootprints():
            for p in f.Pads():
                pads[p.GetNetname()].append(p)
        for (lay, net), g in sorted(groups(b).items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
            nodes = _nodes(g)
            for p, m in sorted(nodes.items()):
                if len(m) != 2:
                    continue
                (t, et), (u, eu) = m
                if t is u or t.GetWidth() != u.GetWidth():
                    continue
                if any(dist(p, v) <= TOL for v in via_pts[net]):
                    continue
                if any(pd.IsOnLayer(lay) and pd.GetEffectiveShape(lay).Collide(V(p), 0) for pd in pads[net]):
                    continue
                if any(o is not t and o is not u and on_body(o, p) for o in g):
                    continue
                ft = ends(t)[1 - et]
                fu = ends(u)[1 - eu]
                h1 = math.atan2(p[1] - ft[1], p[0] - ft[0])
                h2 = math.atan2(fu[1] - p[1], fu[0] - p[0])
                if abs(math.remainder(h1 - h2, 2 * math.pi)) > math.radians(0.01):
                    continue
                if et == 1:
                    t.SetEnd(V(fu))
                else:
                    t.SetStart(V(fu))
                b.Delete(u)
                count += 1
                changed = True
                break
            if changed:
                break
    log.append(f'merge: {count} collinear joints merged')


# --- clearance model (m3.kicad_dru and the board rules; kicad-cli DRC on the saved board is the final word) -----

PYRO_POWER = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')
PYRO_SENSE = ('ARM1_SENSE', 'PYRO1_CONT', 'PYRO1_COLD', 'PYRO1_CONT_MID', 'ARM1_SENSE_MID')
PYRO_GATES = ('PYRO1_GATE', 'PYRO1_GATE_N')
RF_NETS = ('GNSS_RF_ANT', 'GNSS_RF_IN', 'RADIO_RF_ANT', 'RADIO_RF')


PYRO_BLOCK = (4.0, 84.0, 42.0, 114.4)          # the PYRO_BLOCK rule area (mm), where rule G holds


def rule_clearance(a, c, gate_in_block=True):
    """Minimum copper clearance (mm) between nets a and c for tracks and vias (m3.kicad_dru; rule G only when the
    gate-net item touches the PYRO_BLOCK area), plus 0.01."""
    def one(x, y):
        v = 0.15
        if x in RF_NETS and y == 'GND':
            v = 0.25
        if x == 'RAW_ACT' and y in PYRO_GATES + PYRO_SENSE:
            v = 0.5
        if x in PYRO_POWER and y in PYRO_GATES:
            v = max(v, 0.5)
        if x in PYRO_POWER and y in PYRO_SENSE:
            v = max(v, 0.3)
        if x == 'GND' and y in PYRO_POWER:
            v = max(v, 0.5)
        if x == 'RAW_ACT' and y in PYRO_POWER[:2]:
            v = max(v, 1.0)
        if x in PYRO_POWER and y and y not in PYRO_POWER + PYRO_SENSE + PYRO_GATES + ('GND', 'RAW_ACT'):
            v = max(v, 0.5)
        if x in PYRO_GATES and y and y not in PYRO_GATES + PYRO_POWER + ('GND', 'RAW_ACT') and gate_in_block:
            v = max(v, 0.3)
        if x == 'RAW_ACT' and y == 'RAW_ACT_SENSE':
            v = max(v, 0.3)
        return v
    return max(one(a, c), one(c, a)) + 0.01


class Clearance:
    """Other-net copper of the board (tracks, vias, pads; pours refill around new copper) for clearance tests."""

    def __init__(self, b):
        self.items = []
        self.gone = set()                          # KIIDs of tracks deleted since (never touched again)
        for t in b.GetTracks():
            lays = [l for l in CU4 if t.IsOnLayer(l)] if t.GetClass() == 'PCB_VIA' else [t.GetLayer()]
            self.items.append((t, t.GetNetname(), lays, _bbox(t), 0.0, t.m_Uuid.AsString()))
        for f in b.GetFootprints():
            ref = f.GetReference()
            for p in f.Pads():
                lays = [l for l in CU4 if p.IsOnLayer(l)]
                extra = 0.0
                if ref.startswith('TP') and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                    extra = 1.0                    # check_r7: bare test pads keep 1.0 mm from foreign copper
                elif ref == 'J2':
                    extra = 0.508                  # Tag-Connect contact rule
                elif p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname() == 'RAW_ACT':
                    extra = 0.3
                self.items.append((p, p.GetNetname(), lays, _bbox(p), extra, None))
        self.holes = []
        for t in b.GetTracks():
            if t.GetClass() == 'PCB_VIA':
                self.holes.append((xy(t.GetPosition()), t.GetDrillValue() / 2))
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                    self.holes.append((xy(p.GetPosition()), max(p.GetDrillSize().x, p.GetDrillSize().y) / 2))

    def add_segment(self, net, lay, a, c, w):
        """New copper (not yet on the board's item list) that later tests must respect."""
        sh = pcbnew.SHAPE_SEGMENT(V(a), V(c), int(w))
        r = w / 2
        bb = (min(a[0], c[0]) - r, min(a[1], c[1]) - r, max(a[0], c[0]) + r, max(a[1], c[1]) + r)
        self.items.append((sh, net, [lay], bb, 0.0, None))

    def ok(self, net, lay, a, c, w):
        """Whether a track of net from a to c (nm) with width w (nm) on lay keeps every clearance."""
        return self.why(net, lay, a, c, w) is None

    def why(self, net, lay, a, c, w):
        """The first other-net item a track of net from a to c (width w, nm) on lay comes too close to, or None."""
        seg = pcbnew.SHAPE_SEGMENT(V(a), V(c), int(w))
        r = w / 2 + MM(1.1)
        box = (min(a[0], c[0]) - r, min(a[1], c[1]) - r, max(a[0], c[0]) + r, max(a[1], c[1]) + r)
        blk = (MM(PYRO_BLOCK[0]), MM(PYRO_BLOCK[1]), MM(PYRO_BLOCK[2]), MM(PYRO_BLOCK[3]))
        for obj, n, lays, bb, extra, uid in self.items:
            if n == net or lay not in lays or not _touch(box, bb) or (uid is not None and uid in self.gone):
                continue
            gate_bb = box if net in PYRO_GATES else bb   # the gate-net item of the pair (if any)
            in_block = _touch(gate_bb, blk)
            if isinstance(obj, pcbnew.SHAPE_SEGMENT):
                sh = obj
            elif obj.GetClass() == 'PCB_VIA':
                sh = pcbnew.SHAPE_CIRCLE(obj.GetPosition(), obj.GetWidth(lay) // 2)
            else:
                sh = obj.GetEffectiveShape(lay)
            if seg.Collide(sh, MM(max(rule_clearance(net, n, in_block), extra))):
                if isinstance(obj, pcbnew.SHAPE_SEGMENT):
                    return (n, 'new segment')
                if obj.GetClass() == 'PAD':
                    return (n, obj.GetParentFootprint().GetReference() + '.' + obj.GetNumber())
                return (n, obj.GetClass(), loc(xy(obj.GetPosition())) if obj.GetClass() == 'PCB_VIA' else
                        (loc(xy(obj.GetStart())), loc(xy(obj.GetEnd()))))
        return None


# --- chains: re-solve bend points with fixed headings --------------------------------------------------------------

DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
MICRO = 50000                    # nm


def direction(a, c):
    """(index into DIRS, step count) of an exact 0/45/90 segment a->c, or None (off-angle beyond 2 nm)."""
    dx, dy = c[0] - a[0], c[1] - a[1]
    if dx == 0 and dy == 0:
        return None
    for k, (ux, uy) in enumerate(DIRS):
        if ux == 0:
            if abs(dx) <= 2 and dy * uy > 0:
                return k, abs(dy)
        elif uy == 0:
            if abs(dy) <= 2 and dx * ux > 0:
                return k, abs(dx)
        elif dx * ux > 0 and dy * uy > 0 and abs(abs(dx) - abs(dy)) <= 2:
            return k, (abs(dx) + abs(dy)) // 2
    return None


def turn(k1, k2):
    d = (k2 - k1) % 8
    return min(d, 8 - d) * 45


def chain_points(p0, steps):
    pts = [p0]
    for k, n in steps:
        ux, uy = DIRS[k]
        pts.append((pts[-1][0] + ux * n, pts[-1][1] + uy * n))
    return pts


def badness(steps):
    """(micro segments, acute turns, tiny jogs) of a chain's steps."""
    lens = [n * (math.sqrt(2) if k % 2 else 1) for k, n in steps]
    micro = sum(1 for x in lens if x < MICRO)
    acute = sum(1 for (k1, _), (k2, _) in zip(steps, steps[1:]) if turn(k1, k2) > 90)
    jogs = 0
    for i in range(len(steps) - 2):
        (a, _), (bk, _), (c, _) = steps[i:i + 3]
        if a == c and a != bk and (lens[i + 1] < 500000 or lens[i + 1] * math.sin(math.radians(turn(a, bk))) < 250000):
            jogs += 1
    return micro, acute, jogs


def solve_steps(dirs, x0, D):
    """Step counts for the directions dirs (indices) closest (least squares in length) to x0 with sum = D exactly,
    or None."""
    m = len(dirs)
    if m == 0:
        return [] if D == (0, 0) else None
    U = [(DIRS[k][0] / math.hypot(*DIRS[k]), DIRS[k][1] / math.hypot(*DIRS[k])) for k in dirs]
    sc = [math.hypot(*DIRS[k]) for k in dirs]
    y0 = [x * s for x, s in zip(x0, sc)]
    a11 = sum(u[0] * u[0] for u in U); a12 = sum(u[0] * u[1] for u in U); a22 = sum(u[1] * u[1] for u in U)
    det = a11 * a22 - a12 * a12
    r = (D[0] - sum(u[0] * y for u, y in zip(U, y0)), D[1] - sum(u[1] * y for u, y in zip(U, y0)))
    if abs(det) < 1e-9:
        ux, uy = U[0]
        if abs(r[0] * uy - r[1] * ux) > 0.5:
            return None
        lam = (r[0] * ux + r[1] * uy) / m
        y = [yy + lam * (u[0] * ux + u[1] * uy) for yy, u in zip(y0, U)]
    else:
        l1 = (a22 * r[0] - a12 * r[1]) / det
        l2 = (-a12 * r[0] + a11 * r[1]) / det
        y = [yy + u[0] * l1 + u[1] * l2 for yy, u in zip(y0, U)]
    x = [int(round(yy / s)) for yy, s in zip(y, sc)]
    res = (D[0] - sum(DIRS[k][0] * n for k, n in zip(dirs, x)), D[1] - sum(DIRS[k][1] * n for k, n in zip(dirs, x)))
    if res != (0, 0):
        best = None
        for i in range(m):
            for j in range(m):
                if i == j:
                    continue
                (ax, ay), (bx, by) = DIRS[dirs[i]], DIRS[dirs[j]]
                dt = ax * by - ay * bx
                if abs(dt) != 1:
                    continue
                p_ = (res[0] * by - res[1] * bx) * dt
                q_ = (ax * res[1] - ay * res[0]) * dt
                score = -(x[i] + x[j])
                if best is None or score < best[0]:
                    best = (score, i, j, p_, q_)
        if best is None:
            return None
        _, i, j, p_, q_ = best
        x[i] += p_
        x[j] += q_
    return x


def _resolve(steps, pts, nodes, pads, lay):
    """New chain points for steps between pts[0] and pts[-1] with fewer micro segments, acute turns or jogs, or
    None."""
    before = badness(steps)
    p0, pn = pts[0], pts[-1]

    def lens(st):
        return [n * (math.sqrt(2) if k % 2 else 1) for k, n in st]

    def compact(st):
        out = []
        for k, n in st:
            if out and out[-1][0] == k:
                out[-1] = (k, out[-1][1] + n)
            else:
                out.append((k, n))
        return out
    L = lens(steps)
    base = compact([s for s, l in zip(steps, L) if l >= MICRO])
    cands = [base]
    st = list(base)
    for _ in range(4):
        Ls = lens(st)
        drop = None
        for i in range(len(st) - 2):
            (a, _), (bk, _), (c, _) = st[i:i + 3]
            if a == c and a != bk and (Ls[i + 1] < 500000 or Ls[i + 1] * math.sin(math.radians(turn(a, bk))) < 250000):
                drop = i + 1
                break
        if drop is None:
            for i in range(len(st) - 1):
                if turn(st[i][0], st[i + 1][0]) > 90:
                    drop = i if Ls[i] < Ls[i + 1] else i + 1
                    break
        if drop is None:
            break
        st = compact(st[:drop] + st[drop + 1:])
        cands.append(st)
    soft = []
    for which, p in ((0, p0), (1, pn)):
        if len(nodes[p]) == 1:
            pd = [q for q in pads if q.IsOnLayer(lay) and q.GetEffectiveShape(lay).Collide(V(p), 0)]
            if pd:
                soft.append((which, pd[0]))
    for st in cands:
        if not st:
            continue
        dirs = [k for k, _ in st]
        x0 = [n for _, n in st]
        x = solve_steps(dirs, x0, (pn[0] - p0[0], pn[1] - p0[1]))
        newpts = None
        if x is not None and all(n * (math.sqrt(2) if k % 2 else 1) >= MICRO for k, n in zip(dirs, x)):
            newpts = chain_points(p0, list(zip(dirs, x)))
        elif len(set(dirs)) == 1 and soft:
            k = dirs[0]
            ux, uy = DIRS[k]
            for which, pd in soft:
                fixed_p, moving = (pn, p0) if which == 0 else (p0, pn)
                if ux == 0 or uy == 0:
                    q = (fixed_p[0], moving[1]) if ux == 0 else (moving[0], fixed_p[1])
                else:
                    tt = ((moving[0] - fixed_p[0]) * ux + (moving[1] - fixed_p[1]) * uy) // 2
                    q = (fixed_p[0] + ux * tt, fixed_p[1] + uy * tt)
                ps = pcbnew.SHAPE_POLY_SET()
                pd.TransformShapeToPolygon(ps, lay, -2000, 500, pcbnew.ERROR_INSIDE)
                if not ps.Contains(V(q)) or dist(q, fixed_p) < MICRO:
                    continue
                newpts = [q, pn] if which == 0 else [p0, q]
                break
        if newpts is None:
            continue
        segs = [direction(a, c) for a, c in zip(newpts, newpts[1:]) if a != c]
        if any(s_ is None for s_ in segs):
            continue
        after = badness(segs)
        if after[0] == 0 and after[1] == 0 and after[2] <= before[2] and after != before:
            return newpts
    return None


def chains(b, log):
    """Chains with micro segments, acute turns or tiny jogs, re-solved with their headings kept: micro segments (and,
    where that is not enough, jog middles and the shorter leg of an acute turn) are dropped and the remaining bends
    move so the chain still lands exactly on its two end joints. A chain end alone in a pad may slide inside that pad
    when the chain is left with one heading. Each new chain keeps the board clearances."""
    fixed, skipped = [], []
    tried = set()
    for _ in range(400):
        clr = Clearance(b)
        via_pts = defaultdict(list)
        for v in vias(b):
            via_pts[v.GetNetname()].append(xy(v.GetPosition()))
        pads = defaultdict(list)
        for f in b.GetFootprints():
            for pd in f.Pads():
                if pd.GetNetname():
                    pads[pd.GetNetname()].append(pd)
        progress = False
        for (lay, net), g in sorted(groups(b).items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
            if net in PROTECTED:
                continue
            ch, isplain = chain_list(b, lay, net, g, via_pts[net], pads[net])
            nodes = _nodes(g)
            for chain, pts in ch:
                if len({t.GetWidth() for t in chain}) != 1:
                    continue
                steps = []
                for a, c in zip(pts, pts[1:]):
                    d = direction(a, c)
                    if d is None:
                        steps = None
                        break
                    steps.append(d)
                if not steps:
                    continue
                before = badness(steps)
                if before == (0, 0, 0):
                    continue
                key = (net, lay, pts[0], pts[-1], tuple(steps))
                if key in tried:
                    continue
                tried.add(key)
                newpts = _resolve(steps, pts, nodes, pads[net], lay)
                where = (net, b.GetLayerName(lay), loc(pts[0]))
                if newpts is None:
                    skipped.append(where + (before,))
                    continue
                w = chain[0].GetWidth()
                if not all(clr.ok(net, lay, a, c, w) for a, c in zip(newpts, newpts[1:])):
                    skipped.append(where + ('clearance',))
                    continue
                segs = [(a, c) for a, c in zip(newpts, newpts[1:]) if a != c]
                clr.gone |= {t.m_Uuid.AsString() for t in chain}
                for t, (a, c) in zip(chain, segs):
                    t.SetStart(V(a))
                    t.SetEnd(V(c))
                for t in chain[len(segs):]:
                    b.Delete(t)
                for a, c in segs[len(chain):]:
                    new_track(b, chain[0].GetNet(), lay, a, c, w)
                for a, c in segs:                    # later groups in this pass test against the new copper
                    clr.add_segment(net, lay, a, c, w)
                fixed.append(where + (before, badness([direction(a, c) for a, c in segs])))
                progress = True
                break                                # this group's chains changed: next group
        if not progress:
            break
    log.append(f'chains: {len(fixed)} chains re-solved; not solvable here: {len(skipped)}')
    for f_ in fixed:
        log.append(f'  fixed {f_}')
    for s_ in skipped:
        log.append(f'  left {s_}')


# --- acute T joints -----------------------------------------------------------------------------------------------

def acute_t(b, log, stubs=(0.25, 0.2, 0.3, 0.15)):
    """A branch meeting a straight trunk at 45° at a free node (the acute notch beside it) turns square onto the trunk
    just before it: the branch is cut back by k along its own line and a stub of length h = k/sqrt(2), perpendicular
    to the trunk, joins it to the trunk h further along (the first h in `stubs` whose stub keeps the clearances). The
    new stub lies in the wedge between the branch and the trunk."""
    fixed, left = [], []
    tried = set()
    for _ in range(200):
        clr = Clearance(b)
        via_pts = defaultdict(list)
        for v in vias(b):
            via_pts[v.GetNetname()].append(xy(v.GetPosition()))
        pads = defaultdict(list)
        for f in b.GetFootprints():
            for pd in f.Pads():
                if pd.GetNetname():
                    pads[pd.GetNetname()].append(pd)
        progress = False
        for (lay, net), g in sorted(groups(b).items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
            if net in PROTECTED:
                continue
            for p, m in sorted(_nodes(g).items()):
                if (lay, net, p) in tried:
                    continue
                if any(dist(p, v) <= TOL for v in via_pts[net]) or \
                        any(pd.IsOnLayer(lay) and pd.GetEffectiveShape(lay).Collide(V(p), 0) for pd in pads[net]):
                    continue
                br = []                                   # (unit direction from p, track, end index or None)
                for t, e in m:
                    q = ends(t)[1 - e]
                    L = dist(p, q)
                    if L > 0:
                        br.append(((q[0] - p[0]) / L, (q[1] - p[1]) / L, t, e))
                for o in g:
                    if all(o is not t for t, _ in m) and on_body(o, p):
                        for q in ends(o):
                            L = dist(p, q)
                            br.append(((q[0] - p[0]) / L, (q[1] - p[1]) / L, o, None))
                if len(br) != 3:
                    continue
                trunk = None
                for i in range(3):
                    for j in range(i + 1, 3):
                        if br[i][0] * br[j][0] + br[i][1] * br[j][1] < -0.9999:
                            trunk = (i, j)
                if trunk is None or br[trunk[0]][2].GetWidth() != br[trunk[1]][2].GetWidth():
                    continue                              # (a trunk that changes width here would become a neck)
                k_ = 3 - sum(trunk)
                ux, uy, bt, be = br[k_]
                if be is None:
                    continue
                c1 = ux * br[trunk[0]][0] + uy * br[trunk[0]][1]
                if abs(abs(c1) - math.sqrt(0.5)) > 1e-4:
                    continue
                d = br[trunk[0]] if c1 > 0 else br[trunk[1]]         # the trunk direction on the acute side
                dx, dy, dt, de = d
                tried.add((lay, net, p))
                wb = bt.GetWidth()
                far = ends(bt)[1 - be]
                Lb = dist(p, far)
                # how far the trunk runs straight from p along d (its track on that side)
                Lt = dist(p, ends(dt)[1 - de]) if de is not None else \
                    max(((q[0] - p[0]) * dx + (q[1] - p[1]) * dy) for q in ends(dt))
                done = False
                for h_mm in stubs:
                    h = MM(max(h_mm, mm(wb)))
                    k = h * math.sqrt(2)
                    if Lb - k < MICRO or Lt - h < MICRO:
                        continue
                    qpt = (round(p[0] + k * ux), round(p[1] + k * uy))
                    ppt = (round(p[0] + h * dx), round(p[1] + h * dy))
                    if not clr.ok(net, lay, qpt, ppt, wb):
                        continue
                    if be == 0:
                        bt.SetStart(V(qpt))
                    else:
                        bt.SetEnd(V(qpt))
                    new_track(b, net, lay, qpt, ppt, wb)
                    clr.add_segment(net, lay, qpt, ppt, wb)
                    fixed.append((net, b.GetLayerName(lay), loc(p), round(mm(h), 3)))
                    done = progress = True
                    break
                if not done:
                    left.append((net, b.GetLayerName(lay), loc(p)))
                else:
                    break
            if progress:
                break
        if not progress:
            break
    log.append(f'acute_t: {len(fixed)} acute T joints squared (net, layer, joint, stub mm); left {left}')
    for f_ in fixed:
        log.append(f'  {f_}')


# --- hand redraws ---------------------------------------------------------------------------------------------------

LAYERS = {'F': F, 'In1': IN1, 'In2': IN2, 'B': B}


def _in_box(p, box):
    return box[0] - 1e-6 <= mm(p[0]) <= box[2] + 1e-6 and box[1] - 1e-6 <= mm(p[1]) <= box[3] + 1e-6


def replace(b, log, label, net, layer, box, count, draw=(), vias_gone=(), vias_new=(), clr=None):
    """Hand redraw: delete the `count` tracks of net on layer ('F', 'In1', 'In2', 'B') lying wholly inside box
    (x0, y0, x1, y1 mm; asserted, so a changed upstream board stops the build) and the vias of net at vias_gone, then
    draw `draw` = [(width mm, [(x, y), ...]), ...] and 0.6/0.3 mm vias at vias_new. Every new segment must be 0/45/90
    and keep the board clearances (Clearance)."""
    lay = LAYERS[layer]
    gone = [t for t in tracks(b) if t.GetNetname() == net and t.GetLayer() == lay and
            all(_in_box(q, box) for q in ends(t))]
    assert len(gone) == count, (label, net, layer, box, len(gone), count)
    for t in gone:
        b.Delete(t)
    for p in vias_gone:
        hit = [v for v in vias(b) if v.GetNetname() == net and dist(xy(v.GetPosition()), (MM(p[0]), MM(p[1]))) <= TOL]
        assert len(hit) == 1, (label, net, p, len(hit))
        b.Delete(hit[0])
    clr = clr or Clearance(b)
    anchors = [xy(v.GetPosition()) for v in vias(b) if v.GetNetname() == net]
    anchors += [(MM(x), MM(y)) for x, y in vias_new]

    def snap(p):                     # onto a via centre the coordinates name to within 2 um (R6's are nm-rounded)
        hit = [a for a in anchors if dist(a, p) <= 2000]
        return hit[0] if hit else p
    n = 0
    for w, pts in draw:
        q = [snap((MM(x), MM(y))) for x, y in pts]
        for a, c in zip(q, q[1:]):
            assert direction(a, c) is not None, (label, 'not 0/45/90', loc(a), loc(c))
            bad = clr.why(net, lay, a, c, MM(w))
            assert bad is None, (label, 'clearance', loc(a), loc(c), w, bad)
            new_track(b, net, lay, a, c, MM(w))
            n += 1
    for p in vias_new:
        q = (MM(p[0]), MM(p[1]))
        for l in CU4:
            bad = clr.why(net, l, q, q, MM(0.6))
            assert bad is None, (label, 'via clearance', p, b.GetLayerName(l), bad)
        assert all(dist(q, h) >= MM(0.15 + 0.25 + 0.01) + r for h, r in clr.holes), (label, 'via hole clearance', p)
        import r7_route as rt                   # noqa: E402 (keep-outs, edges, supports, paste: the GND-via rules)
        assert rt.ViaCheck(b, net).ok(p, 0.6), (label, 'via keep-out / edge / paste', p)
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(V((MM(p[0]), MM(p[1]))))
        v.SetWidth(MM(0.6))
        v.SetDrill(MM(0.3))
        v.SetNet(b.FindNet(net))
        b.Add(v)
    log.append(f'{label}: {net} {layer}: {count} tracks and {len(vias_gone)} vias removed, {n} segments and '
               f'{len(vias_new)} vias drawn')


def usb_limited(b, log):
    """RG-06 / RQ-08: USB_LIMITED B.Cu from the U10 run to U11.7 was drawn three times (0.4 mm plus two 0.3 mm copies
    0.025-0.2 mm aside, with split loops at x 28.9-31.6). One 0.4 mm trunk on the 0.4 mm copy's path, split at the R87
    branch via (29.1, 40.55); C98.1's 0.25 mm branch meets the trunk square at (30.4, 27.85). TP82's 0.2 mm branch
    becomes one diagonal meeting the trunk square (it ended in a 4 um hook)."""
    replace(b, log, 'usb_limited trunk', 'USB_LIMITED', 'B', (28.4, 25.2, 33.6, 57.2), 43, draw=[
        (0.4, [(28.7, 57.05), (28.7, 46.55), (29.1, 46.15), (29.1, 40.55)]),
        (0.4, [(29.1, 40.55), (29.1, 40.05), (29.9, 39.25), (29.9, 36.25), (31.6, 34.55), (31.6, 31.35),
               (30.8, 30.55), (30.8, 28.15), (30.5, 27.85), (29.875, 27.85)]),
        (0.25, [(33.1, 26.45), (33.1, 26.15), (32.4, 25.45), (31.9, 25.45), (30.4, 26.95), (30.4, 27.85)])])
    replace(b, log, 'usb_limited TP82', 'USB_LIMITED', 'B', (22.9, 60.4, 24.2, 61.7), 3, draw=[
        (0.2, [(23.0, 60.5), (24.125, 61.625)])])


def v3v3a(b, log):
    """RG-06 / RQ-08: 3V3A B.Cu was a tangle of R5 copies: two parallel buses (y 48.1 and 49.5) into U1's 3V3A pins
    with 0.02-0.05 mm offset copies, a 0.25 mm route 0.04-0.06 mm beside the 0.3 mm ones that joined them only by
    overlap, tiny jogs on the way to U4/U5 and doubled diagonals at C30/C31. Redrawn as one tree: R164 and C10 feed one
    0.3 mm bus through C22.1 to the U1 vias; C11 branches square off it (x 36.9) and runs as R6 did; the 0.25 mm U4/U5
    feed leaves that branch square on R6's diagonal (x + y = 88.5: 0.7 mm clear of NRST's In2 diagonal, so the B.Cu
    GND pocket over NRST that F1's via keeps stays) and runs straight at x 36.4 (0.16 mm from the 3V3 via (36.94, 52.65) and R63.2,
    0.2 mm from the GND via (37.03, 58.9): the gap the old 0.1 mm jog dodged), steps 0.36 mm west past TP91 (bare
    test pads keep 1.0 mm) and passes east of NRST's via on R6's diagonal to the In2 via; U5's pads join at their
    centres; at U4 one 0.3 mm run with its via (moved onto the run, 0.3 mm clear of the IMU_body_B via keep-out) feeds
    C31/C30, U4.8 joining it square. The In2 and F.Cu
    3V3A copper is unchanged."""
    replace(b, log, '3v3a', '3V3A', 'B', (28, 43, 42, 80), 63, vias_gone=[(37.91, 76.75)], vias_new=[(37.4, 76.52)],
            draw=[(0.3, [(32.3, 44.475), (33.2, 45.375), (33.2, 47.8), (33.5, 48.1)]),
                  (0.3, [(40.1, 47.4), (39.4, 48.1), (36.9, 48.1)]),
                  (0.3, [(36.9, 48.1), (33.5, 48.1), (32.3, 49.3), (31.6, 50.0), (31.1, 50.0), (29.4, 50.0)]),
                  (0.3, [(32.3, 49.3), (32.6, 49.6), (32.6, 50.2)]),
                  (0.3, [(36.9, 48.1), (36.9, 48.7), (38.35, 50.15)]),
                  (0.3, [(38.35, 50.15), (40.1, 51.9), (40.1, 54.6)]),
                  (0.25, [(38.35, 50.15), (36.4, 52.1), (36.4, 60.86), (36.04, 61.22), (36.04, 63.716),
                          (37.8632, 65.5392), (37.8632, 68.0393), (35.9632, 69.9393)]),
                  (0.2, [(35.9632, 69.9393), (35.67, 70.2325), (35.67, 71.175), (34.42, 71.175)]),
                  (0.3, [(32.72, 71.9), (33.445, 71.175), (34.42, 71.175)]),
                  (0.3, [(35.5, 76.54), (36.24, 75.8), (36.68, 75.8), (37.4, 76.52)]),
                  (0.3, [(37.4, 76.52), (37.82, 76.94), (38.38, 77.5), (38.68, 77.5), (38.68, 78.8)]),
                  (0.2, [(35.5, 76.54), (35.5, 77.34)]),
                  (0.2, [(37.21, 77.55), (37.82, 76.94)])])


def cam_io_3v3(b, log):
    """RG-06 / RQ-08: CAM_IO_3V3 B.Cu from U13.5 to U12.7 was drawn twice (0.025 and 0.125 mm apart, 6 mm and 4.4 mm
    side by side, crossing without a node), with 25-50 um pieces round U13.5 and R103's branch meeting C92's at 45°.
    One 0.25 mm route (the first copy's path) whose bend sits in C93.1; R103's branch runs square onto C92's; TP90's
    0.2 mm branch leaves U13.5 at its centre."""
    replace(b, log, 'cam_io_3v3', 'CAM_IO_3V3', 'B', (37, 27, 45, 50), 29, draw=[
        (0.25, [(42.8, 32.45), (43.25, 32.45), (44.55, 33.75), (44.55, 38.45), (43.05, 39.95), (43.05, 46.15),
                (42.05, 47.15), (42.05, 47.6)]),
        (0.25, [(42.05, 47.6), (42.05, 49.45)]),
        (0.25, [(42.7, 27.7), (41.9, 28.5), (41.9, 29.875)]),
        (0.25, [(41.9, 29.875), (41.9, 31.55), (42.8, 32.45)]),
        (0.25, [(37.8, 27.775), (37.8, 27.975), (39.7, 29.875), (41.9, 29.875)]),
        (0.2, [(42.8, 32.45), (40.75, 34.5), (40.5, 34.5)])])


def raw_protected(b, log):
    """RG-06 / RG-08 / RQ-07 / RQ-08: RAW_PROTECTED was drawn three deep at the D9 vias (0.6, 0.4 and 0.25 mm runs
    along x 15.65-15.7, the 0.25 mm R92 branch lying on the 0.6 mm trunk for 6.6 mm), with 20-50 um pieces at
    (15.7, 32.4), a doubled U11 feed beside C97 and a zig-zag with 25 um hooks at TP70 / C71 / U7. Redrawn:
    - D9: one 0.6 mm trunk via (15.7, 32.4) -> via (13.6, 37.85); the 0.4 mm east feed leaves its corner square to
      the trunk's diagonal; R92 joins the via (13.6, 37.85) by its own 0.25 mm run;
    - U11 feed: D9 -> via (14.0, 33.3) -> (14.0, 27.5) was a 0.2 mm neck (6.5 mm) feeding a 0.6 mm run; it is one
      0.5 mm run now (0.6 mm on F.Cu to the via): at x 14.0 0.5 mm is the most that keeps TP83's 1.0 mm and BAT_IN's
      0.15 mm, so the 0.6 mm part becomes 0.5 mm too. The path's narrowest copper goes from 0.2 to 0.5 mm. C97.1
      joins the run's diagonal square; 0.3 mm into U11.2 (0.65 mm from its pad);
    - camera feed: the 0.4 mm F.Cu run continues at 0.4 mm to the via (37.85, 54.7) instead of necking to 0.2 mm,
      and the B.Cu 0.2 mm run leaves that via without the 15-100 um pieces;
    - TP70: TP81 -> TP70 centre, one 0.4 mm diagonal TP70 -> C71.1, one 0.4 mm run TP70 -> U7.4 (the 0.2 mm neck
      widened), C71.1 -> its In2 via at 0.2 mm."""
    replace(b, log, 'raw_protected D9', 'RAW_PROTECTED', 'B', (13.5, 31.5, 23.2, 40.5), 11, draw=[
        (0.6, [(15.7, 32.4), (15.7, 35.75), (13.6, 37.85)]),
        (0.4, [(15.7, 35.75), (17.65, 37.7), (23.05, 37.7)]),
        (0.25, [(14.4, 40.325), (15.7, 39.025), (15.7, 37.0), (15.075, 36.375)])])
    replace(b, log, 'raw_protected U11 neck F', 'RAW_PROTECTED', 'F', (13.9, 31.1, 14.1, 33.4), 1, draw=[
        (0.6, [(14.0, 31.2), (14.0, 33.3)])])
    replace(b, log, 'raw_protected U11 neck B', 'RAW_PROTECTED', 'B', (13.9, 26.9, 14.6, 33.4), 2)
    replace(b, log, 'raw_protected U11', 'RAW_PROTECTED', 'B', (14.4, 25.9, 28.6, 28.0), 9, draw=[
        (0.5, [(14.0, 33.3), (14.0, 27.5), (15.3, 26.2), (25.7, 26.2), (26.225, 26.725)]),
        (0.5, [(26.225, 26.725), (27.35, 27.85)]),
        (0.3, [(27.35, 27.85), (28.525, 27.85)]),
        (0.25, [(25.7, 27.25), (26.225, 26.725)])])
    replace(b, log, 'raw_protected camera F', 'RAW_PROTECTED', 'F', (36.1, 47.8, 38.1, 54.75), 4, draw=[
        (0.4, [(36.15, 47.9), (38.05, 49.8), (38.05, 54.5), (37.85, 54.7)])])
    replace(b, log, 'raw_protected camera B', 'RAW_PROTECTED', 'B', (37.8, 54.6, 40.3, 59.2), 5, draw=[
        (0.2, [(37.85, 54.7), (37.85, 56.75), (40.2, 59.1)])])
    replace(b, log, 'raw_protected TP70', 'RAW_PROTECTED', 'B', (34.8, 80.9, 39.6, 86.7), 21, draw=[
        (0.2, [(39.5, 81.0), (39.5, 82.2), (38.5, 83.2)]),
        (0.4, [(38.5, 83.2), (38.175, 83.2), (35.7, 85.675)]),
        (0.2, [(35.7, 85.675), (35.7, 85.82), (34.85, 86.67)]),
        (0.4, [(38.5, 83.2), (38.5, 84.175), (38.9, 84.575), (38.9, 85.7)]),
        (0.3, [(38.45, 85.7), (38.9, 85.7)])])


def vlogic(b, log):
    """RG-06 / RQ-07: VLOGIC at U11 had two vias 0.85 mm apart joining U11.1's B.Cu to F.Cu, a 0.2 mm B.Cu run
    0.014 mm beside the 0.5 mm trunk, a via sitting 0.2 mm off the trunk's centre line, 5-64 um pieces and a 1.7 mm
    F.Cu stub doubled by a fold-back (to the R60 sense line). Redrawn: one via on the trunk's centre line joins it to
    C99.1, and the R60 sense line starts at C99.1 (0.25 mm all the way, it necked 0.25 -> 0.2 -> 0.25 mm). The 0.2 mm
    neck of the C84 -> U2 trunk (B.Cu (11.0, 38.65) -> via (13.6, 36.35) -> F.Cu -> via (16.5, 33.15)) is widened as
    far as the clearances allow."""
    replace(b, log, 'vlogic U11 F', 'VLOGIC', 'F', (26.8, 26.9, 32.3, 35.6), 13, draw=[
        (0.2, [(26.905, 29.25), (27.905, 29.25), (28.505, 29.85)]),
        (0.25, [(28.505, 29.85), (31.355, 27.0), (32.27, 27.915), (32.27, 29.2), (31.67, 29.8), (31.67, 35.5)])])
    replace(b, log, 'vlogic U11 B', 'VLOGIC', 'B', (23.4, 28.4, 28.6, 29.5), 9,
            vias_gone=[(27.57, 28.9), (26.905, 29.45)], vias_new=[(26.905, 29.25)], draw=[
                (0.5, [(28.525, 28.55), (27.825, 28.55), (27.125, 29.25), (26.905, 29.25)]),
                (0.5, [(26.905, 29.25), (23.425, 29.25)])])
    replace(b, log, 'vlogic neck B', 'VLOGIC', 'B', (10.9, 36.3, 13.7, 38.7), 2, draw=[
        (0.5, [(11.0, 38.65), (13.3, 36.35), (13.6, 36.35)])])
    replace(b, log, 'vlogic neck F', 'VLOGIC', 'F', (13.5, 33.1, 16.6, 36.4), 3, draw=[
        (0.5, [(13.6, 36.35), (14.1, 36.35), (16.5, 33.95), (16.5, 33.15)])])


def imu_cs(b, log):
    """RG-08 / RQ-07: IMU_CS (a §3 critical SPI chip select) had two complete routes from U1.93 to the via (37.2,
    80.07): the direct 18.4 mm F.Cu diagonal, which crossed the via's vertical without a node, overshot it by 0.15 mm
    and hooked back (acute), and a 25 mm detour F.Cu -> via (25.1, 66.77) -> In2 -> via (30.8, 66.77) -> F.Cu with 28 /
    30 um pieces at U1. The detour goes (and with it two critical layer changes RG-09 counted); the diagonal ends on
    the via's vertical."""
    replace(b, log, 'imu_cs F', 'IMU_CS', 'F', (24, 60, 39, 81), 11, draw=[
        (0.2, [(24.35, 61.05), (24.35, 66.75), (37.2, 79.6), (37.2, 80.07)])])
    replace(b, log, 'imu_cs In2', 'IMU_CS', 'In2', (25.0, 66.7, 30.9, 66.8), 1,
            vias_gone=[(25.1, 66.77), (30.8, 66.77)])


def vbus(b, log):
    """RG-06 / RG-08 / RQ-07 / RQ-08: VBUS from the USB connector J3 to D4, R9, C28, C83 and U10 had 20-30 um pieces
    round the via (11.0, 76.35) on In2 and B.Cu, a 0.85 mm In2 overshoot folded back over by a 0.2 mm branch (acute),
    staircases at both J3 VBUS pins and a 3-6 um step into the via (9.88, 77.8). Redrawn with the same vias: each J3
    VBUS pin leaves its pad in one bend-free run (A4B9 on R6's diagonal, B4A9 one horizontal); In2 is one 0.4 mm spine
    x 11.0 from the J3 feed to the via (10.8, 79.95), the J3 B4A9 via joining it square; R9's In2 feed as R6 drew it
    without the pieces; U10.3 one 0.2 mm run (its dogleg between two GND tracks lengthened to 0.5 mm: no tiny jog); the
    F.Cu link via (10.8, 79.95) -> via (11.325, 82.05) one diagonal at R6's 0.2 mm (widened to 0.4 mm it pushed the
    RAW_ACT F.Cu pour back 0.09 mm² and raised the 7.7 A Q121 -> J122 resistance from 3.9567 to 3.9570 mOhm)."""
    replace(b, log, 'vbus F', 'VBUS', 'F', (5, 69, 15, 83), 13, draw=[
        (0.4, [(6.88, 72.9), (7.58, 72.9), (9.28, 71.2), (9.28, 70.7)]),
        (0.4, [(6.98, 77.8), (9.88, 77.8)]),
        (0.2, [(10.8, 79.95), (10.8, 81.525), (11.325, 82.05)]),
        (0.3, [(11.325, 82.05), (13.225, 82.05)])])
    replace(b, log, 'vbus B', 'VBUS', 'B', (5, 69, 15, 83), 18, draw=[
        (0.4, [(9.28, 70.7), (8.2, 71.78), (8.2, 75.0), (6.9, 76.3)]),
        (0.4, [(11.0, 76.35), (11.0, 75.15)]),
        (0.2, [(9.88, 77.8), (12.2, 77.8), (13.05, 78.65), (13.05, 79.15), (13.55, 79.65)]),
        (0.3, [(11.325, 82.05), (13.2, 82.05), (13.7, 81.55)]),
        (0.25, [(14.0, 73.23), (14.0, 73.03), (14.5, 72.53)])])
    replace(b, log, 'vbus In2', 'VBUS', 'In2', (5, 69, 15, 83), 16, draw=[
        (0.4, [(9.28, 70.7), (11.0, 72.42), (11.0, 76.35)]),
        (0.4, [(11.0, 76.35), (11.0, 77.8)]),
        (0.4, [(11.0, 77.8), (11.0, 79.75), (10.8, 79.95)]),
        (0.4, [(9.88, 77.8), (11.0, 77.8)]),
        (0.4, [(11.0, 76.35), (11.4, 76.35), (14.0, 73.75), (14.0, 73.23)])])


def v3v3(b, log):
    """RG-06 / RG-08 / RG-10 / RQ-07: 3V3 residue.
    - U1.100's via (27.85, 62.75): three F.Cu runs left it, two of them side by side 0.1 mm apart (x 27.8 / 27.9) with
      about ten 14-50 um pieces round the via, and the B.Cu x 30.17 run passed 0.07 mm from the via (30.1, 71.17)
      without a node. One F.Cu trunk to that via, the via (30.4, 70.25) joining the trunk square; the via moves 0.07 mm
      onto the B.Cu run (x 30.17 is held by CAM_UART_OE's via (29.6, 63.4)), R12.2 joins the run square at y 73.17,
      and the F.Cu run to the via (30.17, 65.1), which left the U1 via at 45° beside the trunk, goes (the vias still
      join both runs through the B.Cu run); C18.1 reaches the U1 via in one straight run.
    - RG-10: (41.35, 58.55) -> (42.95, 57.15), 3.8° off 45°: the corner moves to (41.55, 58.55) (the straight part
      first, as the pass-2 skeptic measured: 0.24 mm to R100.1, 0.35 mm to the GND via).
    - L1.2: the via (24.9, 35.0) hung off L1's diagonal at 45° on a second 0.6 mm diagonal beside the first; its In2
      feed now ends at the via (24.2, 35.3) on the first diagonal, and the via itself moves onto that diagonal at
      (24.8, 34.3) (a node on it; 0.2 mm from L1.2's pad, ViaCheck's own-pad and paste rules): the buck output keeps
      three vias into the In2 3V3 plane (without it, L1.2 -> U1.75 measured 13.99 -> 14.97 mOhm, tools/dc_solve.py);
      C9.1's 0.6 mm feed ends in L1.2's pad instead of on a second vertical 0.3 mm from the first.
    - D120.3 / R11: the R11 feed crossed the D120 vertical without a node and ran 0.27 mm beside the D120 link; both
      now leave the vertical square at nodes (the R11 feed still passes the GND via (34.3, 82.36) on R6's line); the
      0.25 mm diagonal from (38.635, 77.92) ends on the via centre (it stopped 36 um off it).
    - (7.9, 80.69): a diagonal that necked 0.2 -> 0.25 mm and hooked back 45° into its via is one diagonal and a
      straight into the via at the run's width, 0.2 mm (the 0.25 mm part was the last 3.7 mm of a 0.2 mm feed)."""
    replace(b, log, '3v3 U1.100 F', '3V3', 'F', (27.7, 62.7, 30.5, 71.3), 13, draw=[
        (0.25, [(27.85, 62.75), (27.85, 68.85), (30.17, 71.17)]),
        (0.25, [(30.4, 70.25), (29.825, 70.825)])])
    replace(b, log, '3v3 C18 B', '3V3', 'B', (27.8, 60.9, 27.9, 62.85), 3, draw=[
        (0.3, [(27.85, 61.0), (27.85, 62.75)])])
    replace(b, log, '3v3 x30 B', '3V3', 'B', (29.9, 59.5, 33.25, 75.4), 6,
            vias_gone=[(30.1, 71.17)], vias_new=[(30.17, 71.17)], draw=[
                (0.2, [(33.1583, 59.63), (30.17, 62.6183), (30.17, 65.1)]),
                (0.25, [(30.17, 65.1), (30.17, 71.17)]),
                (0.25, [(30.17, 71.17), (30.17, 73.7), (31.77, 75.3)]),
                (0.25, [(30.17, 73.17), (32.7, 73.17)])])
    replace(b, log, '3v3 RG-10', '3V3', 'B', (40.2, 57.1, 43.0, 58.6), 2, draw=[
        (0.25, [(40.25, 58.55), (41.55, 58.55), (42.95, 57.15)])])
    replace(b, log, '3v3 L1 B', '3V3', 'B', (24.0, 32.9, 26.5, 36.7), 8, vias_new=[(24.8, 34.3)], draw=[
        (0.6, [(26.1, 33.0), (24.8, 34.3)]),
        (0.6, [(24.8, 34.3), (24.2, 34.9), (24.2, 35.3)]),
        (0.6, [(24.1, 36.6), (26.0, 34.7)]),
        (0.6, [(26.1, 33.0), (26.4, 33.3), (26.4, 36.6)])])
    replace(b, log, '3v3 L1 In2', '3V3', 'In2', (20.9, 31.0, 24.95, 35.05), 2, vias_gone=[(24.9, 35.0)], draw=[
        (0.25, [(20.95, 31.1), (24.2, 34.35), (24.2, 35.3)])])
    replace(b, log, '3v3 D120', '3V3', 'F', (31.9, 77.9, 38.7, 82.5), 12, draw=[
        (0.25, [(33.1, 80.95), (33.1, 82.35)]),
        (0.25, [(32.0, 82.0), (33.1, 82.0)]),
        (0.2, [(33.1, 81.73), (34.5, 81.73), (35.2, 82.43), (36.0, 82.43)]),
        (0.25, [(38.635, 77.92), (38.635, 79.795), (36.0, 82.43)])])
    replace(b, log, '3v3 (7.9, 80.69)', '3V3', 'F', (7.8, 76.5, 12.1, 80.7), 3, draw=[
        (0.2, [(12.049, 76.5412), (8.1902, 80.4), (7.9, 80.4)])])


def camera_power(b, log):
    """RG-06 / RG-08 / RQ-07: CAM_5V and CAM_INPUT_LIMITED residue.
    - CAM_5V R104.1 run: 0.4 mm from R104.1 then 0.2 mm on, joined by 6-50 um hooks (acute, overlap-only); one 0.2 mm
      run (the path was 0.2 mm beyond the hooks; this also moves it 0.1 mm further from J123.1, REGRESSION-05).
    - CAM_5V at C75 / L3: two 0.8 mm stubs to two stitching vias lay side by side 0.02 mm apart, a 0.3 mm feed ran
      0.02 mm beside them into C75.1, and L3's run met C75.1 0.05 mm off its centre with a 50 um piece. L3.2 -> C75.1
      leaves L3 south then meets C75.1 diagonally (so it no longer runs beside the via stub), C75.1 -> on, one 0.8 mm
      stub to both vias (both move onto it, 0.15 mm or more from C75.1's pad), the 0.3 mm feed meets the stub's first
      via square.
    - CAM_INPUT_LIMITED: TP71's 0.2 mm branch overshot the 0.3 mm run's end and hooked back; one 0.3 mm run from TP71.
      U7.5 -> C73.1: a 0.2 mm jog between 0.3 and 0.8 mm runs; one straight 0.8 mm run into C73.1 (0.3 mm out of
      U7.5's pad), the run south leaving it square."""
    replace(b, log, 'cam_5v R104', 'CAM_5V', 'B', (32.9, 30.7, 36.1, 33.55), 8, draw=[
        (0.2, [(33.03, 30.8), (33.43, 30.8), (34.23, 31.6), (34.23, 32.2), (35.48, 33.45), (36.0, 33.45)])])
    replace(b, log, 'cam_5v C75', 'CAM_5V', 'B', (33.7, 102.4, 41.9, 109.0), 11,
            vias_gone=[(39.3, 104.8), (39.5, 103.6)], vias_new=[(39.35, 104.55), (39.35, 103.6)], draw=[
                (0.8, [(41.8, 102.45), (41.8, 104.0), (40.3, 105.5)]),
                (0.8, [(40.3, 105.5), (40.3, 108.9)]),
                (0.8, [(40.3, 105.5), (39.35, 104.55), (39.35, 103.6)]),
                (0.3, [(33.8, 103.925), (38.3, 103.925), (38.925, 104.55), (39.35, 104.55)])])
    replace(b, log, 'cam_input_limited TP71', 'CAM_INPUT_LIMITED', 'B', (32.4, 93.4, 36.95, 95.6), 3, draw=[
        (0.3, [(32.5, 95.5), (34.5, 93.5), (36.9, 93.5)])])
    replace(b, log, 'cam_input_limited U7', 'CAM_INPUT_LIMITED', 'B', (38.9, 87.35, 40.95, 87.65), 4, draw=[
        (0.3, [(38.95, 87.6), (39.65, 87.6)]),
        (0.8, [(39.65, 87.6), (40.9, 87.6)])])
    replace(b, log, 'cam_input_limited U7 south', 'CAM_INPUT_LIMITED', 'B', (40.25, 87.35, 40.35, 90.85), 1, draw=[
        (0.8, [(40.3, 87.6), (40.3, 90.8)])])


def gnd(b, log):
    """RG-06 / RG-08 / RQ-07 / RQ-08: GND track residue (the pours are untouched).
    - (24.47, 107.9) F.Cu: a run ended 0.17 mm off a via's centre on its way to the next via; it now passes through
      both via centres.
    - C10.2: a 0.2 mm copy beside the 0.25 mm pad-to-via link, and a 0.2 mm stub from it into the pour, go.
    - U5 (baro) GND pads: four vias, two crossing links and a 25 um piece; both GND pins join one via square to each
      other (the other three vias stay as stitching vias).
    - R64.2 / C31.2 / C30.2: a 0.11 mm jog (S, 0.16 mm SW, S) and a 45 um piece; straight runs.
    - U12.2 -> (44.65, 54.95): a staircase (0.3 mm step); one diagonal.
    - U10.2: an acute T (a 45° branch onto a 0.25 / 0.2 mm trunk); U10.2 joins the trunk square.
    - R155.2: two branches left the pad 45° apart, and the run to the via (24.55, 89.275) ended in a 0.3 mm jog and a
      25 um step 28 um off the via; one diagonal and one straight run onto the via centre.
    - C94.2: a 0.72 mm dead stub goes.
    - D122.1 -> C160.2 F.Cu: an 8 um piece and a 0.31 mm jog; one straight run and a straight drop into C160.2."""
    replace(b, log, 'gnd (24.47, 107.9)', 'GND', 'F', (23.9, 107.8, 25.4, 109.65), 4, draw=[
        (0.2, [(23.97, 109.6), (23.97, 108.63), (24.55, 108.05)]),
        (0.2, [(24.55, 108.05), (24.7, 107.9), (25.37, 107.9)])])
    replace(b, log, 'gnd C10.2', 'GND', 'B', (38.35, 45.35, 40.15, 46.2), 4, draw=[
        (0.25, [(40.1, 45.4), (39.15, 45.4), (38.95, 45.6)])])
    replace(b, log, 'gnd U5', 'GND', 'B', (36.85, 69.0, 38.25, 71.95), 8, draw=[
        (0.25, [(36.93, 71.175), (37.73, 70.375)]),
        (0.25, [(38.18, 71.175), (38.18, 70.825), (37.73, 70.375)])])
    replace(b, log, 'gnd R64', 'GND', 'B', (38.15, 74.8, 39.65, 78.85), 8, draw=[
        (0.2, [(39.52, 77.5), (39.52, 78.8)]),
        (0.2, [(39.63, 76.2), (39.63, 77.5)]),
        (0.2, [(39.63, 76.2), (39.63, 75.7033), (38.7517, 74.825), (38.18, 74.825)])])
    replace(b, log, 'gnd U12.2', 'GND', 'B', (42.0, 51.7, 44.7, 54.96), 10, draw=[
        (0.25, [(42.05, 52.55), (42.05, 51.95), (42.25, 51.75), (42.85, 51.75), (44.65, 53.55), (44.65, 54.95)]),
        (0.25, [(42.05, 52.55), (42.05, 53.18), (42.42, 53.55), (42.42, 53.9)])])
    replace(b, log, 'gnd U10.2', 'GND', 'B', (13.6, 78.7, 14.7, 81.95), 6, draw=[
        (0.25, [(13.7, 78.8), (14.2, 78.8), (14.6, 79.2), (14.6, 80.6)]),
        (0.2, [(14.6, 80.6), (14.6, 81.9287)]),
        (0.25, [(13.7, 80.6), (14.6, 80.6)])])
    replace(b, log, 'gnd R155', 'GND', 'B', (17.5, 86.9, 24.6, 89.35), 8, draw=[
        (0.25, [(19.03, 89.0), (19.305, 89.275), (24.55, 89.275)]),
        (0.2, [(19.03, 89.0), (19.03, 88.4583), (17.5717, 87.0)])])
    replace(b, log, 'gnd C94 stub', 'GND', 'B', (35.05, 27.6, 35.15, 28.45), 1)
    replace(b, log, 'gnd D122', 'GND', 'F', (33.4, 28.55, 34.95, 28.95), 4, draw=[
        (0.2, [(33.45, 28.6), (34.9, 28.6), (34.9, 28.92)])])


def power_misc(b, log):
    """RG-06 / RG-08 / RQ-07 / RQ-08: the last power-net residue.
    - BAT_IN at TP80 / R167 / C96: TP80's 0.5 mm feed ran 0.33 mm beside R167's (overlapping copper) and through
      R167.1 and C96.1 to its own In2 via, and C96's link to its via ran 0.1 mm beside R167's diagonal. TP80 joins
      R167's run (TP80 is a test pad: no current), whose via now also serves C96.1; C96.1 keeps its second via by a run
      that leaves its pad east. The via that fed only TP80 goes (dead once its track goes). C80.1's link into the
      same via ended 5 um off its centre: it now ends on it.
    - RAW_ACT at (5.3, 82.17): a 30 um stub goes; the 0.2 mm F.Cu branch from the via (12.6, 81.27) had a 0.3 mm jog
      (0.4 mm N between two diagonals) round VBUS's via (10.8, 79.95): the N run goes on to the W run (one corner).
    - VCAP2: U1.73 -> its capacitor stepped 0.1 mm down and up (0.14 mm diagonals) round USB_DP's via (12.5, 57.9) and
      necked 0.25 -> 0.3 mm; one straight run at the path's narrowest width, 0.25 mm (0.3 mm at y 58.5 would leave
      0.15 mm to that via; VCAP2 is U1's core-regulator capacitor pin, not a supply path)."""
    replace(b, log, 'bat_in TP80', 'BAT_IN', 'B', (3.7, 53.3, 9.75, 54.85), 6, vias_gone=[(9.7, 54.8)], draw=[
        (0.5, [(3.8, 54.475), (6.0, 54.475)]),
        (0.5, [(6.0, 54.475), (8.2, 54.475), (9.3, 53.375)]),
        (0.5, [(8.3, 54.525), (9.2, 54.525), (9.7, 54.025)])])
    replace(b, log, 'bat_in C80', 'BAT_IN', 'B', (9.25, 52.05, 10.7, 53.42), 3, draw=[
        (0.5, [(10.62, 52.1), (10.62, 52.6), (9.845, 53.375), (9.3, 53.375)])])
    replace(b, log, 'raw_act stub', 'RAW_ACT', 'F', (5.25, 82.16, 5.35, 82.21), 1)
    replace(b, log, 'raw_act jog', 'RAW_ACT', 'F', (9.75, 79.3, 12.65, 81.3), 4, draw=[
        (0.2, [(12.6, 81.27), (11.4, 80.07), (11.4, 79.37), (9.8, 79.37)])])
    replace(b, log, 'vcap2', 'VCAP2', 'F', (10.5, 58.4, 16.05, 62.45), 9, draw=[
        (0.25, [(14.3, 58.5), (11.1, 58.5), (10.6, 59.0), (10.6, 59.6), (13.4, 62.4), (16.0, 62.4)])])


def pyro(b, log):
    """RG-07 / RG-08 / RQ-07 on the pyro sense and gate nets (the CH1 bus, igniter and drain copper only loses a piece
    inside Q124.5's pad; spacing is checked against m3.kicad_dru's pyro rules by the Clearance model and then DRC).
    - RG-07 PYRO1_GATE: a 0.3 mm trunk through C126.1 and R128.1 plus 0.2 mm doglegs beside it (side-by-side copper, a
      crossing without a node, a 0.22 mm jog, an acid-trap sliver at R126.2). One 0.2 mm route, the pass-2 skeptic's
      v5: R126.2's centre, one 45° step, then straight at y 91.85 through C126.1, R128.1 and Q124.4 (the only line
      inside all three pads), with a node in each pad; TP122's link as before. Gate current is the 10 k gate drive's
      (well under 1 mA), so 0.2 mm is ample (inference from the schematic values, not measured).
    - PYRO1_COLD: after the dead branch goes (stage dead), R131.2 -> D120.1 is a 0.2 mm diagonal, two 18-30 um pieces
      and a 0.15 mm diagonal; one 0.2 mm route with one corner.
    - PYRO1_CONT In2: a 0.2 -> 0.15 mm neck at a bend; 0.2 mm through to its via.
    - PYRO1_OUT: R6's 0.2 mm drain branch crossed the 0.6 mm drain run inside Q124.5's pad (with 11-12 um pieces);
      it now ends inside the pad short of the run, at (28.85, 91.73), where its whole width lies inside the pad's
      finger (copper removed inside the pad only; it stopped 5 um inside the finger's edge before)."""
    replace(b, log, 'pyro1_gate', 'PYRO1_GATE', 'F', (20.4, 91.7, 26.05, 92.45), 8, draw=[
        (0.2, [(20.45, 92.4), (21.6, 92.4)]),
        (0.2, [(21.6, 92.4), (22.1, 92.4), (22.65, 91.85), (23.4, 91.85)]),
        (0.2, [(23.4, 91.85), (24.7, 91.85)]),
        (0.2, [(24.7, 91.85), (26.0, 91.85)])])
    replace(b, log, 'pyro1_cold', 'PYRO1_COLD', 'F', (28.7, 83.9, 31.1, 86.15), 5, draw=[
        (0.2, [(29.72, 86.1), (29.335, 85.715), (31.05, 84.0)])])
    replace(b, log, 'pyro1_cont In2', 'PYRO1_CONT', 'In2', (25.2, 84.7, 34.75, 88.45), 3, draw=[
        (0.2, [(25.22, 88.4217), (32.42, 88.4217), (32.42, 87.0217), (34.72, 84.7217)])])
    replace(b, log, 'pyro1_out', 'PYRO1_OUT', 'F', (28.6, 89.9, 30.6, 91.95), 3, draw=[
        (0.2, [(30.58, 90.0), (28.85, 91.73)])])


def signals(b, log):
    """RG-08 / RG-15 / RQ-07 on slow signal nets (§3 rule categories: acute angles, fold-backs, staircases).
    - SERVO4_MCU In2: a 45° branch 0.2 mm off the via, with a zero-length piece; both runs leave the via itself.
    - BAT_ENABLE: a 0.15 mm link between U9.1's two overlapping pads (acute against the 0.2 mm run) goes.
    - CAM_FB: three branches into the via (41.1, 96.15) as two 0.18 mm-apart diagonals and two 0.05 mm-apart
      horizontals with 25-35 um pieces (fold-backs). R71.2 joins R72's run square, that run and C77's meet at one
      square node, one run into the via.
    - CAM_UART_OE: a 0.85 mm / 0.7 mm two-step staircase on B.Cu (held by PYRO1_GATE_N's via (31.9, 59.23) and the
      3V3 diagonal it runs 0.17 mm beside): its via moves 0.7 mm to the end of the diagonal and the 0.7 mm step moves
      to the F.Cu link; at the via (38.06, 60.09) the F.Cu run overshot it with 14-24 um
      pieces (acute) and the B.Cu link to TP91 stepped 63 um: straight runs through the via centre.
    - NRST In2: two routes 0.135 mm apart for 5 mm (an R6 copy) merging at 45°; the east feed now ends at the via
      (30.82, 46.19) and one route runs on.
    - RAW_ACT_SENSE In2: a 5 mm overshoot drawn twice (0.2 and 0.15 mm) folded back 135° into the via branch; the
      0.2 mm run turns square into its via.
    - VBUS_SENSE: B.Cu had a 3 um slot between two runs, fold-backs at the via and a staircase; one run from the
      via (15.2, 64.2) past a 3V3 via and between R90's pads (one 0.4 mm dogleg) through R9.2 to the via (13.39, 71.48), R110.1 joining it
      square. In2: a staircase (two 0.47 / 0.58 mm steps round GND vias): the second step and the 1.5 mm run after it
      become one diagonal (one step left).
    - PULLPIN (R6's D122.3 tree): a five-segment staircase and 28-40 um pieces at R160 / R161; the run from D122.3
      to R160.2 is one straight run at x 32.7, the only line between VLOGIC's x 32.27 run and CAM_5V_SENSE's via
      (33.25, 29.85) (it stepped 0.26 mm between them, a tiny jog), ending 0.2 mm off both pads' centres (a piece to
      a centre would lie wholly inside the pad, which stage inside removes); R160.2 -> R161.2 straight, R161.2 ->
      C160.1 one bend.
    - SWCLK: two staircases: F.Cu near the pyro block (0.14 mm and 0.3 mm steps; it keeps 0.3 mm from PYRO1_GATE_N)
      becomes two clean doglegs; In1 near U1 (E 0.55, NE 0.5, N, NE 0.78, N) leaves its via on one diagonal and keeps
      R6's x 21.5 run (In1 is SPI1_SCK's F.Cu reference: a run further east cut it under U1.89)."""
    replace(b, log, 'servo4_mcu In2', 'SERVO4_MCU', 'In2', (24.7, 95.9, 27.5, 99.2), 5, draw=[
        (0.15, [(27.4033, 99.1366), (24.7866, 99.1366)]),
        (0.15, [(27.4033, 99.1366), (26.602, 98.3353), (26.602, 95.9991)])])
    replace(b, log, 'bat_enable', 'BAT_ENABLE', 'F', (10.3, 41.3, 10.55, 41.55), 1)
    replace(b, log, 'cam_fb', 'CAM_FB', 'F', (40.9, 92.75, 44.6, 98.65), 11, draw=[
        (0.25, [(43.675, 92.8), (43.675, 94.5), (42.025, 96.15)]),
        (0.25, [(44.525, 93.9), (43.675, 93.9)]),
        (0.25, [(44.475, 98.6), (42.025, 96.15)]),
        (0.25, [(42.025, 96.15), (41.1, 96.15)])])
    replace(b, log, 'cam_uart_oe F', 'CAM_UART_OE', 'F', (33.85, 58.7, 43.8, 60.85), 6, draw=[
        (0.15, [(33.9, 60.8), (34.6135, 60.0865), (38.0625, 60.0865)]),
        (0.15, [(38.0625, 60.0865), (39.3625, 58.7865), (43.7865, 58.7865)])])
    replace(b, log, 'cam_uart_oe TP91', 'CAM_UART_OE', 'B', (37.95, 60.0, 38.1, 62.55), 3, draw=[
        (0.15, [(38.0625, 60.0865), (38.0625, 62.5)])])
    replace(b, log, 'cam_uart_oe B', 'CAM_UART_OE', 'B', (29.55, 57.35, 31.95, 63.45), 4,
            vias_gone=[(29.6, 63.4)], vias_new=[(29.6, 62.7)], draw=[
                (0.15, [(31.9, 57.4), (31.3, 58.0), (31.3, 61.0), (29.6, 62.7)])])
    replace(b, log, 'cam_uart_oe F link', 'CAM_UART_OE', 'F', (29.55, 63.35, 31.35, 63.45), 1, draw=[
        (0.15, [(29.6, 62.7), (29.6, 63.4), (31.3, 63.4)])])
    replace(b, log, 'nrst In2', 'NRST', 'In2', (30.3, 45.6, 34.1, 53.15), 15, draw=[
        (0.15, [(34.035, 45.65), (31.3687, 45.65), (30.824, 46.1947)]),
        (0.15, [(30.824, 46.1947), (30.4, 46.6187), (30.4, 50.1), (31.3, 51.0), (31.3, 51.7), (30.8, 52.2),
                (30.8, 53.1)])])
    replace(b, log, 'raw_act_sense In2', 'RAW_ACT_SENSE', 'In2', (13.6, 57.6, 14.7, 78.1), 4, draw=[
        (0.2, [(14.63, 57.7), (14.63, 72.5), (13.63, 72.5)])])
    replace(b, log, 'vbus_sense B', 'VBUS_SENSE', 'B', (13.35, 64.15, 16.65, 71.9), 13, draw=[
        (0.15, [(15.2, 64.2), (16.6, 65.6), (16.6, 68.0), (16.2, 68.4), (16.2, 70.5), (15.217, 71.483), (14.5, 71.483)]),
        (0.15, [(14.5, 71.483), (13.39, 71.483)]),
        (0.15, [(16.1, 71.875), (15.4625, 71.2375)])])
    replace(b, log, 'vbus_sense In2', 'VBUS_SENSE', 'In2', (13.1, 52.95, 15.7, 71.5), 6, draw=[
        (0.15, [(13.39, 71.483), (13.1452, 71.2382), (13.1452, 59.747), (13.6118, 59.2804), (13.6118, 55.0382),
                (15.65, 53.0)])])
    replace(b, log, 'pullpin', 'PULLPIN', 'F', (32.45, 26.75, 34.95, 30.65), 13, draw=[
        (0.15, [(32.7, 30.6), (32.7, 27.03)]),
        (0.15, [(32.9, 27.03), (34.17, 27.03)]),
        (0.15, [(34.17, 26.8), (34.17, 27.35), (34.9, 28.08)])])
    replace(b, log, 'swclk F', 'SWCLK', 'F', (22.8, 84.0, 25.2, 89.9), 10, draw=[
        (0.15, [(22.85, 89.85), (22.85, 89.45), (23.85, 88.45), (23.85, 86.65), (25.15, 85.35), (25.15, 84.05)])])
    replace(b, log, 'swclk In1', 'SWCLK', 'In1', (20.55, 56.3, 22.1, 62.65), 5, draw=[
        (0.15, [(20.6, 62.6), (21.5, 61.7), (21.5, 59.2), (22.05, 58.65), (22.05, 56.35)])])


def spi(b, log):
    """RG-08 / RQ-08 on the SPI / QSPI nets (§3 critical):
    - QSPI_NCS B.Cu: two diagonals 0.21 mm apart joined by a 0.3 mm step and a 0.3 mm stub at its via: one diagonal
      via to via.
    - SPI1_MISO: a 0.2 mm jog (W 0.49, SW 0.28, W 0.55) at U4.1; R6's diagonal, one straight run past the GND via
      (33.9, 78.5) and one short diagonal into U4.1's centre.
    - SPI1_MOSI: a 0.25 mm bump round C121.1 between two diagonals 0.18 mm apart: one diagonal on the bump's line (the
      IMU_CS diagonal it runs beside is the only copper on that side: 0.19 mm, as at the bump); its via moves 0.26 mm
      up its own run (to (34.55, 80.7)), so B.Cu enters it in one diagonal.
    - SPI1_SCK: a staircase (0.3 / 0.57 mm steps) and a loop past SPI1_MOSI's old via with 10-28 um pieces: the main
      diagonal runs on to one square turn and one diagonal up into U4.13 (between the moved via, the GND via
      (34.3, 82.36) and R11)."""
    replace(b, log, 'qspi_ncs', 'QSPI_NCS', 'B', (19.8, 40.4, 26.8, 47.4), 4, draw=[
        (0.2, [(19.85, 47.35), (26.75, 40.45)])])
    replace(b, log, 'spi1_miso', 'SPI1_MISO', 'B', (28.5, 74.2, 34.8, 79.3), 4, draw=[
        (0.2, [(28.55, 74.25), (33.55, 79.25), (34.6, 79.25), (34.79, 79.06)])])
    replace(b, log, 'spi1_mosi F', 'SPI1_MOSI', 'F', (23, 60, 35, 81.5), 9, draw=[
        (0.2, [(23.35, 61.05), (23.35, 66.3), (34.55, 77.5), (34.55, 80.7)])])
    replace(b, log, 'spi1_mosi B', 'SPI1_MOSI', 'B', (34.5, 79.2, 35.6, 81.0), 3, vias_gone=[(34.6, 80.96)],
            vias_new=[(34.55, 80.7)], draw=[
                (0.2, [(35.5, 79.26), (35.5, 79.75), (34.55, 80.7)])])
    replace(b, log, 'spi1_sck', 'SPI1_SCK', 'B', (22, 65, 37, 82), 12, draw=[
        (0.2, [(22.25, 65.65), (27.85, 71.25), (27.85, 74.85), (34.65, 81.65), (36.0, 80.3), (36.0, 79.26)])])


HAND_PRE = [('usb_limited', usb_limited), ('imu_cs', imu_cs), ('3v3a', v3v3a), ('cam_io_3v3', cam_io_3v3),
            ('raw_protected', raw_protected), ('vlogic', vlogic), ('vbus', vbus), ('3v3', v3v3),
            ('camera_power', camera_power), ('gnd', gnd), ('power_misc', power_misc), ('pyro', pyro),
            ('signals', signals), ('spi', spi)]


# --- GND return vias at critical layer changes ----------------------------------------------------------------------

class GndFit:
    """The project's legality test for a new GND via (gnd_vias; route_check's allowlist audit runs the same test): the
    r7_route.ViaCheck rules (board rules against every other net's copper on every layer, RF and SMA gaps, hole
    clearance, edges and supports, no via in or by a GND solder pad, keep-outs, paste), bare test pads 1.02 mm
    (check_r7), Tag-Connect contacts 0.528 mm, Pyro D 0.52 mm (GND to the pyro bus, igniter and drain copper, fills
    included), and none within 0.5 mm of a BAT_IN / RAW_ACT / ACT_FET_S pour inside that net's servo-current corridor
    (gnd_vias' docstring has the measurement). window = (x0, y0, x1, y1) mm limits the copper it loads to that box
    (a spot search near one point; the test is the same for any spot more than 2 mm inside the box)."""

    def __init__(self, b, window=None):
        import r7_route as rt                   # noqa: E402 (heavy import, only here)
        self.chk = rt.ViaCheck(b)
        self.window = window

        def near_(bb):
            if window is None:
                return True
            return not (mm(bb.GetLeft()) > window[2] or mm(bb.GetRight()) < window[0] or
                        mm(bb.GetTop()) > window[3] or mm(bb.GetBottom()) < window[1])
        if window is not None:
            self.chk.objs = [o for o in self.chk.objs if near_(o.GetBoundingBox())]
        self.bare = [(p, lay) for f in b.GetFootprints() if f.GetReference().startswith('TP') for p in f.Pads()
                     for lay in (F, B) if p.IsOnLayer(lay) and near_(p.GetBoundingBox())]
        self.j2 = [(p, lay) for f in b.GetFootprints() if f.GetReference() == 'J2' for p in f.Pads() for lay in CU4
                   if p.IsOnLayer(lay) and near_(p.GetBoundingBox())]
        self.pyro = []
        for t in b.GetTracks():
            if t.GetNetname() in PYRO_POWER and near_(t.GetBoundingBox()):
                for lay in CU4:
                    if t.IsOnLayer(lay):
                        self.pyro.append(t.GetEffectiveShape(lay))
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetNetname() in PYRO_POWER and near_(p.GetBoundingBox()):
                    for lay in CU4:
                        if p.IsOnLayer(lay):
                            self.pyro.append(p.GetEffectiveShape(lay))
        for z in b.Zones():
            if z.GetNetname() in PYRO_POWER and not z.GetIsRuleArea():
                for lay in CU4:
                    if z.IsOnLayer(lay) and z.HasFilledPolysForLayer(lay):
                        self.pyro.append(z.GetFilledPolysList(lay))
        self.heavy = []      # the 7.7 A servo-path pours between their DC terminals: a GND via's antipad there costs copper
        for z in b.Zones():
            if z.GetNetname() in HIGH_CURRENT and not z.GetIsRuleArea():
                box = None
                for ref in HIGH_CURRENT[z.GetNetname()]:
                    bb = b.FindFootprintByReference(ref).GetBoundingBox(False, False)
                    r = (mm(bb.GetLeft()) - 2, mm(bb.GetTop()) - 2, mm(bb.GetRight()) + 2, mm(bb.GetBottom()) + 2)
                    box = r if box is None else (min(box[0], r[0]), min(box[1], r[1]), max(box[2], r[2]),
                                                 max(box[3], r[3]))
                for lay in CU4:
                    if z.IsOnLayer(lay) and z.HasFilledPolysForLayer(lay):
                        self.heavy.append((z.GetFilledPolysList(lay), box))

    def ok(self, q, d):
        if not self.chk.ok(q, d):
            return False
        ring = pcbnew.SHAPE_CIRCLE(V((MM(q[0]), MM(q[1]))), MM(d / 2))
        if any(p.GetNetname() != 'GND' and p.GetEffectiveShape(lay).Collide(ring, MM(1.02)) for p, lay in self.bare):
            return False
        if any(p.GetNetname() != 'GND' and p.GetEffectiveShape(lay).Collide(ring, MM(0.528)) for p, lay in self.j2):
            return False
        for sh in self.pyro:
            if isinstance(sh, pcbnew.SHAPE_POLY_SET):
                if sh.Collide(V((MM(q[0]), MM(q[1]))), MM(d / 2 + 0.52)):
                    return False
            elif sh.Collide(ring, MM(0.52)):
                return False
        if any(bx[0] <= q[0] <= bx[2] and bx[1] <= q[1] <= bx[3] and sh.Collide(V((MM(q[0]), MM(q[1]))), MM(d / 2 + 0.5))
               for sh, bx in self.heavy):
            return False
        return True

    def add(self, q, d):
        self.chk.add(q, d)


GND_VIA_SIZES = (0.6, 0.5)      # mm: the board's GND return via (0.6/0.3) and its small stitching size (0.5/0.3)


def gnd_spots(b, q, reach=rc.GND_REACH, step=0.025, sizes=GND_VIA_SIZES, first=False):
    """Every spot (step grid round q, centre within `reach` of q) where a GND via of one of `sizes` passes GndFit:
    [((x, y), d, distance)], nearest first; first=True stops at the nearest one found (the grid is walked by
    distance)."""
    fit = GndFit(b, (q[0] - reach - 2.5, q[1] - reach - 2.5, q[0] + reach + 2.5, q[1] + reach + 2.5))
    n = int(math.ceil(reach / step))
    cand = sorted(((round(math.hypot(step * i, step * j), 6), (round(q[0] + step * i, 4), round(q[1] + step * j, 4)))
                   for j in range(-n, n + 1) for i in range(-n, n + 1)), key=lambda t: (t[0], t[1]))
    out = []
    for dist_, c in cand:
        if dist_ > reach + 1e-9:
            break
        for d in sizes:
            if fit.ok(c, d):
                out.append((c, d, dist_))
                if first:
                    return out
                break
    return out


def gnd_vias(b, log, near=1.0, reach=rc.GND_REACH, step=0.05, fine=None):
    """GND return vias beside critical-signal layer changes (AGENTS.md §3; RG-09 for R6 copper, RG-05 for R7's): while
    a via carries a critical signal net's tracks on two layers with no GND via within `reach` (route_check), the legal
    spot within `near` (then within `reach`) of the most such layer changes gets a 0.6/0.3 mm GND via (0.5/0.3 mm, as
    the board's other small stitching vias, where 0.6 mm does not fit). Legal: GndFit (the r7_route.ViaCheck rules
    (board rules against every other net's copper on every layer, RF and SMA gaps, hole clearance, edges and supports,
    no via in or by a GND solder pad, keep-outs, paste), bare test pads 1.0 mm (check_r7), Tag-Connect contacts
    0.508 mm and Pyro D (GND 0.5 mm from the pyro bus, igniter and drain copper); and none within 0.5 mm of a BAT_IN /
    RAW_ACT / ACT_FET_S pour inside that net's servo-current corridor (the box round the parts its DC solve runs
    between, plus 2 mm): there its antipad cuts the 7.7 A path (measured: two vias at (13.8, 93.95) / (13.8, 97.35)
    raised BAT_IN's J1 -> Q120 resistance from 3.91 to 3.95 mOhm; the vias by the USB connector, in the same BAT_IN
    pour 10 mm outside the corridor, changed nothing).
    fine (mm): then, for each layer change still without one, the nearest legal spot on a `fine` grid (gnd_spots, the
    search route_check's allowlist audit runs) gets one.
    Each layer change left without one is logged with its nearest GND via (the record lists them)."""
    fit = GndFit(b)
    refused = set()                             # a spot that failed stays failed: added vias only take room

    def fits(q, d):
        if (q, d) in refused:
            return False
        if not fit.ok(q, d):
            refused.add((q, d))
            return False
        return True

    def gnd():
        return [(mm(t.GetPosition().x), mm(t.GetPosition().y)) for t in vias(b) if t.GetNetname() == 'GND']
    trans = [(n, (mm(p[0]), mm(p[1]))) for n, p, g in rc.critical_transitions(b)]
    added = []
    for lim, d in ((near, 0.6), (near, 0.5), (reach, 0.6), (reach, 0.5)):
        while True:
            have = gnd()
            open_ = [q for _, q in trans if min((math.dist(q, g_) for g_ in have), default=99) > reach]
            if not open_:
                break
            cands = set()
            n = int(lim / step)
            for q in open_:
                for j in range(-n, n + 1):
                    for i in range(-n, n + 1):
                        c = (round(q[0] + step * i, 2), round(q[1] + step * j, 2))
                        if math.dist(c, q) <= lim:
                            cands.add(c)
            scored = []
            for c in cands:
                served = [q for q in open_ if math.dist(c, q) <= lim]
                if served:
                    scored.append(((-len(served), round(sum(math.dist(c, q) for q in served), 4), c), c))
            scored.sort()
            pick = next((c for _, c in scored if fits(c, d)), None)
            if pick is None:
                break
            fit.add(pick, d)
            added.append((pick, d))
    if fine:
        for _, q in trans:
            if min((math.dist(q, g_) for g_ in gnd()), default=99) <= reach:
                continue
            hit = gnd_spots(b, q, reach, fine, first=True)
            if hit:
                (c, d, _), = hit
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(V((MM(c[0]), MM(c[1]))))
                v.SetWidth(MM(d))
                v.SetDrill(MM(0.3))
                v.SetNet(b.FindNet('GND'))
                b.Add(v)
                added.append((c, d))
    have = gnd()
    log.append(f'gnd_vias: {len(added)} GND vias added: {added}')
    for n_, q in trans:
        d = min((math.dist(q, g_) for g_ in have), default=None)
        if d is None or d > reach:
            log.append(f'  left: {n_} {q}: nearest GND via {d:.2f} mm (no legal spot within {reach} mm)')


# --- hand redraws of the residue the generic stages leave (on their output) ------------------------------------------

def hand_post(b, log):
    """Non-critical nets the generic stages could not clean (route_check counts these, gating them only on critical
    nets; the owner's clean-routing criterion covers the whole board):
    - crossings without a node, both inside a pad: CAM_5V_SENSE at R104.2 (the via branch crossed the R105.1 run)
      now leaves that run square at (32.2, 29.85); ACT_GATE at Q121.4 (the 0.25 mm diagonal crossed the 0.2 mm C120
      run 20 um short of the pad centre) now ends on the centre (its corner moves 20 um);
    - LOGIC_SOURCE_ST: a 25 / 35 um In2 hook wholly inside its via goes (the via joins F.Cu and B.Cu);
    - necks: USB_OVLO (0.2 -> 0.15 mm, collinear), LOGIC_SS (0.2 mm fan-out, 0.15 mm body, 0.2 mm into C85) and
      LOGIC_ILIM (0.2 -> 0.15 mm) are one width each, 0.2 mm (LOGIC_SS's run between C8's pads moves 0.05 mm to
      the gap's centre line, y 33.6, and its turn at U11 0.05 mm up, clear of the GND via (28.13, 31.3));
    - tiny jogs: SWCLK west of U1 (four 0.1-0.2 mm steps between the 3V3, USB_FAULT_N and CAM_FAULT_N vias) is one
      straight run at x 16.6, the line all three vias allow; CAM_UART_OE U12.6 -> R102.1 one straight run at x 41.5
      (between CAM_MCU_TX and C93.1) and one diagonal; IMU_INT1 hopped B -> F -> B through two vias 1.8 mm apart
      round R6's RADIO_M0_MCU vias (removed in R7): it stays on B.Cu (two vias fewer), straight down beside SERVO2_MCU
      (x 26.3, so the B.Cu GND pour east of it stays one piece: a run at x 27.25 cut off a GND island between the
      two), then east of SERVO2_MCU's via as before; SERVO4_MCU In2 one diagonal
      between the 3V3 and CAM_FAULT_N vias; CAM_FAULT_N one run at x 37.8875, the line that keeps 0.15 mm from
      R77.2 and the 0.5 mm pyro rule from J121.2 (it stepped 94 um between the two), its via moving 9 um along its
      In2 diagonal onto it; CAM_TX_WIRE's 0.21 mm step east of R101.1 moves into its via's copper; USB_ILIM leaves
      R85.1 0.2 mm off its centre in one diagonal clear of Q123.3; ACT_EN leaves Q122.1 48 um east of
      its centre, in line with its via (moving the via instead pushes its In2 run into BAT_IN's In2 neck at
      (10.45, 107.62): J1 -> Q120 measured 3.9070 -> 3.9159 mOhm).
    - SERVO2_MCU B.Cu: stage chains removed the 0.1 mm jog at its via (24.4, 69.3) by moving the 12 mm run beside
      J122's RAW_ACT pins 0.1 mm west, which necked the B.Cu GND pour between those pins below its minimum width:
      a 16 mm² GND finger dropped out. The run is back on R6's line (x 24.5, with R6's bends below), its 0.1 mm step
      now inside the via's copper.
    - ACT_FET_S: R6's 0.4 mm L (5.1, 95.0) -> (6.45, 94.7) lay in the pour joined to nothing but the pour (RG-06
      listed its end as an overlap-only joint; it adds 7.7 A copper, so it stays): it now runs from R120.1 to
      Q120.1's centre (copper only added).
    Jogs left (geometry, not routing choice; route_check counts them, non-critical): CAM_EN at U7.2 (between U7.1's
    and C71.1's corners), SERVO2_MCU In2 (threaded between the SERVO1_OUT, PYRO1_GATE_N, PYRO1_CONT and GND vias),
    CAM_5V_SENSE at U1.35 (U1.36's corner, then RAW_ACT_SENSE_MCU's via), LOGIC_ILIM at U11.10 (LOGIC_SOURCE_ST's
    via beside the pin)."""
    replace(b, log, 'cam_5v_sense R104', 'CAM_5V_SENSE', 'B', (32.1, 29.8, 33.3, 30.8), 2, draw=[
        (0.15, [(32.2, 29.85), (33.25, 29.85)])])
    replace(b, log, 'act_gate Q121.4', 'ACT_GATE', 'B', (5.85, 98.8, 7.1, 102.42), 3, draw=[
        (0.25, [(7.08, 98.86), (7.08, 101.22), (5.9, 102.4)]),
        (0.2, [(5.9, 101.7), (5.9, 102.4)])])
    replace(b, log, 'logic_source_st In2', 'LOGIC_SOURCE_ST', 'In2', (29.9, 30.45, 30.0, 30.6), 2)
    replace(b, log, 'usb_ovlo', 'USB_OVLO', 'B', (29.4, 26.2, 29.85, 27.1), 3, draw=[
        (0.2, [(29.45, 27.05), (29.45, 26.5898), (29.8083, 26.2315)])])
    replace(b, log, 'logic_ss', 'LOGIC_SS', 'B', (27.5, 29.3, 29.7, 36.5), 11, draw=[
        (0.2, [(28.95, 29.35), (28.95, 29.85), (28.45, 30.35), (28.45, 30.7), (27.9, 30.7), (27.55, 31.05),
               (27.55, 33.4), (27.75, 33.6), (29.4, 33.6), (29.65, 33.85), (29.65, 35.75), (28.95, 36.45)])])
    replace(b, log, 'logic_ilim', 'LOGIC_ILIM', 'B', (29.2, 30.8, 30.7, 32.3), 1, draw=[
        (0.2, [(29.25, 30.85), (30.65, 32.25)])])
    replace(b, log, 'swclk U1 west', 'SWCLK', 'F', (15.1, 65.3, 16.7, 68.6), 9, draw=[
        (0.15, [(15.15, 65.85), (15.65, 65.35), (16.2, 65.35), (16.6, 65.75), (16.6, 67.7), (15.75, 68.55)])])
    replace(b, log, 'cam_uart_oe U12.6', 'CAM_UART_OE', 'B', (41.35, 45.65, 42.2, 49.55), 4, draw=[
        (0.15, [(41.5, 49.45), (41.5, 46.375), (42.175, 45.7)])])
    replace(b, log, 'imu_int1 F', 'IMU_INT1', 'F', (26.6, 64.4, 26.9, 66.3), 4,
            vias_gone=[(26.7, 64.45), (26.65, 66.25)])
    replace(b, log, 'imu_int1 B', 'IMU_INT1', 'B', (26.25, 62.6, 27.3, 67.3), 5, draw=[
        (0.15, [(26.3, 62.65), (26.3, 66.3), (27.25, 67.25)])])
    replace(b, log, 'servo4_mcu In2 U1', 'SERVO4_MCU', 'In2', (15.45, 63.5, 17.85, 67.2), 6, draw=[
        (0.15, [(17.825, 63.5384), (17.825, 64.8296), (15.4784, 67.1762)])])
    replace(b, log, 'cam_fault_n F', 'CAM_FAULT_N', 'F', (37.75, 84.5, 38.65, 97.0), 4,
            vias_gone=[(37.8938, 96.944)], vias_new=[(37.8875, 96.9503)], draw=[
                (0.15, [(38.6, 84.575), (37.8875, 85.2875), (37.8875, 96.9503)])])
    replace(b, log, 'cam_fault_n In2', 'CAM_FAULT_N', 'In2', (31.0, 96.9, 37.9, 103.8), 1, draw=[
        (0.15, [(31.0599, 103.7779), (37.8875, 96.9503)])])
    replace(b, log, 'cam_tx_wire', 'CAM_TX_WIRE', 'B', (44.9, 43.9, 45.2, 51.4), 3, draw=[
        (0.15, [(44.933, 43.9675), (45.1408, 44.1753), (45.1408, 51.3592)])])
    replace(b, log, 'usb_ilim R85', 'USB_ILIM', 'B', (7.8, 81.55, 10.25, 83.05), 4, draw=[
        (0.15, [(7.825, 82.8), (9.025, 81.6), (10.2411, 81.6)])])
    replace(b, log, 'act_en Q122', 'ACT_EN', 'B', (11.05, 107.55, 11.2, 108.65), 3, draw=[
        (0.15, [(11.1483, 108.6), (11.1483, 107.611)])])
    replace(b, log, 'servo2_mcu J122', 'SERVO2_MCU', 'B', (20.45, 69.25, 24.45, 88.65), 4, draw=[
        (0.15, [(24.4, 69.3), (24.5, 69.4), (24.5, 81.1), (24.0, 81.6), (24.0, 85.1), (20.5, 88.6)])])
    replace(b, log, 'act_fet_s R120-Q120', 'ACT_FET_S', 'B', (5.05, 94.65, 6.5, 95.05), 2, draw=[
        (0.4, [(5.17, 96.0), (5.17, 95.0), (6.45, 95.0), (6.45, 94.44), (5.91, 93.9)])])


GENERIC = [('zero_length', zero_length), ('dedupe', dedupe), ('inside', inside), ('near_dup', near_dup),
           ('dead', dead), ('dedupe2', dedupe), ('merge', merge), ('chains', chains), ('merge2', merge),
           ('dead2', dead), ('inside2', inside), ('acute_t', acute_t), ('merge3', merge)]
STAGES = HAND_PRE + GENERIC + [('gnd_vias', gnd_vias), ('hand_post', hand_post)]


def run(b, stop=None, verbose=True, start=None):
    """The stages in order; after each one the pours are refilled (the board's own rules: the .kicad_pro / .kicad_dru
    beside it must be present) and the pad groups compared with the previous stage's (same_groups)."""
    pcbnew.KIID.SeedGenerator(7501)
    lib.fill(b)
    base = pad_groups(b)
    log = []
    names = [n for n, _ in STAGES]
    for name, fn in STAGES[names.index(start) if start else 0:]:
        t0 = time.time()
        fn(b, log)
        lib.fill(b)
        now = pad_groups(b)
        bad = same_groups(base, now)
        if bad:
            raise RuntimeError(f'stage {name} changed the pad groups of {bad}')
        base = now
        if verbose:
            print(f'[{name}] ({time.time() - t0:.0f} s)', *log, sep='\n  ', flush=True)
        log.clear()
        if stop == name:
            break


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--board', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--out', type=Path, help='save here instead of over --board')
    ap.add_argument('--stop', help='stop after this stage (debugging)')
    ap.add_argument('--start', help='start at this stage (development only: the build runs every stage)')
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()
    if not args.board.with_suffix('.kicad_dru').exists():
        raise SystemExit(f'{args.board.with_suffix(".kicad_dru")} missing: the fills need the board\'s own rules')
    b = pcbnew.LoadBoard(str(args.board))
    run(b, args.stop, not args.quiet, args.start)
    lib.fill(b)
    out = args.out or args.board
    pcbnew.SaveBoard(str(out), b, True)
    print('saved', out)


if __name__ == '__main__':
    main()
