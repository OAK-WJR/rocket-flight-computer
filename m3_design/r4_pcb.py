#!/usr/bin/env python3
"""M3-ASSY-R3 -> R4 board edits (docs/M3_R4.md, from docs/R3_VALIDATION.md).

usage: <KiCad python3> m3_design/r4_pcb.py [m3_design/assembly_review/m3.kicad_pcb]
KiCad python on macOS: /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3

Run after m3_design/r4_sch.py (the schematic edits); footprints added here are linked to
the symbols it creates through the same uuid5 keys. Each step is idempotent. Positions
are computed from existing pads where possible, and the script asserts what it assumes.
Finishes with a zone refill and save; then run tools/check.sh.
"""
import math
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r4_sch import ROOT, uid  # noqa: E402  (same stable UUIDs as the schematic edit)

PCB = sys.argv[1] if len(sys.argv) > 1 else 'm3_design/assembly_review/m3.kicad_pcb'
LIB = str(Path(PCB).resolve().parent / 'kilib' / 'rocket.pretty')
mm, MM = pcbnew.ToMM, pcbnew.FromMM
SHEET = {'battery_entry': '69ee5338-a377-5d7b-bbd8-28b781c5d2c5', 'pyro': 'a44998d3-a410-5959-9243-41a16cadc930',
         'mcu': 'f468108e-0b0c-5879-abe2-8195c9cd53e8', 'actuator_power': '6133d301-6422-5dca-9dda-573ff465fb31'}


def P(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def fp_of(b, ref):
    f = b.FindFootprintByReference(ref)
    assert f is not None, f'{ref} missing'
    return f


def pad_xy(b, ref, num):
    p = next(p for p in fp_of(b, ref).Pads() if p.GetNumber() == num)
    return mm(p.GetPosition().x), mm(p.GetPosition().y)


def net(b, name):
    n = b.FindNet(name)
    assert n is not None, f'net {name} missing'
    return n


def add_fp(b, lib_name, ref, value, fields, sheet, pos, rot, pad_nets, side='F'):
    """Footprint linked to the r4_sch symbol uid(ref); returns it. No-op if ref exists."""
    old = b.FindFootprintByReference(ref)
    if old is not None:
        return old
    f = pcbnew.FootprintLoad(LIB, lib_name)
    assert f is not None, lib_name
    f.SetFPID(pcbnew.LIB_ID('rocket', lib_name))
    f.SetReference(ref)
    t = f.Reference()
    t.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0)))
    t.SetTextThickness(MM(0.15))
    f.SetValue(value)
    for k, v in fields.items():
        f.SetField(k, v)
    for fld in f.GetFields():
        if fld.GetName() not in ('Reference', 'Value'):
            fld.SetVisible(False)
    f.SetPath(pcbnew.KIID_PATH(f'/{ROOT}/{SHEET[sheet]}/{uid(ref)}'))
    b.Add(f)
    if side == 'B':
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetOrientationDegrees(rot)
    f.SetPosition(P(*pos))
    for p in f.Pads():
        p.SetNet(net(b, pad_nets[p.GetNumber()]))
    return f


def place_ref(b, ref, x, y, angle=0, side=None):
    """Put a footprint's reference text at (x, y), upright at angle; side 'B' puts it on
    B.Silkscreen mirrored (the board already keeps crowded references on the back)."""
    t = fp_of(b, ref).Reference()
    if side == 'B':
        t.SetLayer(pcbnew.B_SilkS)
        t.SetMirrored(True)
    elif side == 'F':
        t.SetLayer(pcbnew.F_SilkS)
        t.SetMirrored(False)
    t.SetPosition(P(x, y))
    t.SetTextAngleDegrees(angle)


def _silk_obstacles(b, layer, skip_ref):
    """Bounding boxes that a reference text on `layer` must not touch: other silkscreen items on
    that layer, pads on the same copper side (mask openings), and every Edge.Cuts shape."""
    cu = pcbnew.F_Cu if layer == pcbnew.F_SilkS else pcbnew.B_Cu
    obs = []
    for f in b.GetFootprints():
        for g in f.GraphicalItems():
            if g.GetLayer() == layer:
                obs.append(g.GetBoundingBox())
        for fld in f.GetFields():
            if f.GetReference() != skip_ref and fld.IsVisible() and fld.GetLayer() == layer:
                obs.append(fld.GetBoundingBox())
        for pd in f.Pads():
            if pd.IsOnLayer(cu):
                obs.append(pd.GetBoundingBox())
    for d in b.GetDrawings():
        if d.GetLayer() in (layer, pcbnew.Edge_Cuts):
            obs.append(d.GetBoundingBox())
    return obs


def auto_ref(b, ref, side, near=None, rmax=6.0):
    """Place ref's reference text at the first free spot (spiral around `near` or the footprint),
    on side 'F' or 'B', keeping 0.2 mm from every obstacle and (pass 4: C89's text had landed wholly
    off the board, where no Edge.Cuts shape is touched) 0.3 mm inside the board outline. Raises if
    nothing fits."""
    f = fp_of(b, ref)
    layer = pcbnew.F_SilkS if side == 'F' else pcbnew.B_SilkS
    obs = _silk_obstacles(b, layer, ref)
    board = b.GetBoardEdgesBoundingBox()
    board.Inflate(-MM(0.3))
    cx, cy = near if near else (mm(f.GetPosition().x), mm(f.GetPosition().y))
    gap = MM(0.2)
    r = 0.0
    while r <= rmax:
        n = max(1, int(6.283 * r / 0.4))
        for k in range(n):
            a = 6.283 * k / n
            x, y = cx + r * __import__('math').cos(a), cy + r * __import__('math').sin(a)
            for ang in (0, 90):
                place_ref(b, ref, x, y, ang, side=side)
                bb = f.Reference().GetBoundingBox()
                if not board.Contains(bb):
                    continue
                bb.Inflate(gap)
                if not any(bb.Intersects(o) for o in obs):
                    return x, y, ang
        r += 0.25
    raise AssertionError(f'no free silkscreen spot for {ref}')


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5


def via_clear(b, xy, netname, dia=0.6, gap=0.25):
    """True when a through via of netname at xy keeps `gap` mm (edge to edge) from every track,
    via and pad of another net on any copper layer, and 0.6 mm from the board edge / holes."""
    x, y = xy
    r = dia / 2
    for t in b.GetTracks():
        if t.GetNetname() == netname:
            continue
        if t.GetClass() == 'PCB_VIA':
            if ((mm(t.GetPosition().x) - x) ** 2 + (mm(t.GetPosition().y) - y) ** 2) ** 0.5 < r + mm(t.GetWidth(pcbnew.F_Cu)) / 2 + gap:
                return False
        else:
            (sx, sy), (ex, ey) = ends(t)
            if _seg_dist(x, y, sx, sy, ex, ey) < r + mm(t.GetWidth()) / 2 + gap:
                return False
    for f in b.GetFootprints():
        for pd in f.Pads():
            if pd.GetNetname() == netname:
                continue
            bb = pd.GetBoundingBox()
            dx = max(mm(bb.GetX()) - x, 0, x - mm(bb.GetRight()))
            dy = max(mm(bb.GetY()) - y, 0, y - mm(bb.GetBottom()))
            if (dx * dx + dy * dy) ** 0.5 < r + gap:
                return False
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts:
            bb = d.GetBoundingBox()
            if d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
                c = d.GetCenter()
                if ((mm(c.x) - x) ** 2 + (mm(c.y) - y) ** 2) ** 0.5 < mm(d.GetRadius()) + r + 0.6:
                    return False
    return 0.6 + r <= x <= 46 - 0.6 - r and 0.6 + r <= y <= 193 - 0.6 - r


def add_zone(b, netname, layer, pts, prio, name, like=None):
    """Copper zone on one layer; electrical settings copied from zone `like` when given."""
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(net(b, netname))
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(MM(x), MM(y))
    if like is not None:
        z.SetMinThickness(like.GetMinThickness())
        z.SetThermalReliefGap(like.GetThermalReliefGap())
        z.SetThermalReliefSpokeWidth(like.GetThermalReliefSpokeWidth())
        z.SetPadConnection(like.GetPadConnection())
        z.SetLocalClearance(like.GetLocalClearance())
        z.SetIslandRemovalMode(like.GetIslandRemovalMode())
    z.SetAssignedPriority(prio)
    z.SetZoneName(name)
    b.Add(z)
    return z


def place_label(b, text, pref, box, angles=(0, 90), size=1.0, layer=pcbnew.F_SilkS, extra=()):
    """New silkscreen text (F by default; B is mirrored) at the free spot inside box (x0, y0, x1, y1)
    closest to pref; `extra` adds obstacle boxes (e.g. vias)."""
    t = pcbnew.PCB_TEXT(b)
    t.SetText(text)
    t.SetLayer(layer)
    t.SetMirrored(layer == pcbnew.B_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(0.15))
    obs = _silk_obstacles(b, layer, None) + list(extra)
    gap = MM(0.2)
    x0, y0, x1, y1 = box
    cands = []
    steps = 0.2
    nx, ny = int((x1 - x0) / steps) + 1, int((y1 - y0) / steps) + 1
    for i in range(nx):
        for j in range(ny):
            x, y = x0 + i * steps, y0 + j * steps
            cands.append(((x - pref[0]) ** 2 + (y - pref[1]) ** 2, x, y))
    cands.sort()
    for _, x, y in cands:
        for ang in angles:
            t.SetPosition(P(x, y))
            t.SetTextAngleDegrees(ang)
            bb = t.GetBoundingBox()
            bb.Inflate(gap)
            if mm(bb.GetX()) < 0.5 or mm(bb.GetRight()) > 45.5 or mm(bb.GetY()) < 0.5 or mm(bb.GetBottom()) > 192.5:
                continue
            if not any(bb.Intersects(o) for o in obs):
                b.Add(t)
                return x, y, ang
    raise AssertionError(f'no room for silkscreen label {text!r} in {box}')


def refresh_from_lib(b, ref):
    """Replace a footprint with a fresh copy from kilib (after r4_lib.py edited the library),
    keeping placement, side, path, attributes, every field with its text placement, and pad nets."""
    old = fp_of(b, ref)
    name = str(old.GetFPID().GetLibItemName())
    new = pcbnew.FootprintLoad(LIB, name)
    assert new is not None, name
    new.SetFPID(old.GetFPID())
    b.Add(new)
    if old.IsFlipped():
        new.Flip(new.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    new.SetOrientation(old.GetOrientation())
    new.SetPosition(old.GetPosition())
    new.SetPath(old.GetPath())
    new.SetAttributes(old.GetAttributes())
    for fo in old.GetFields():
        new.SetField(fo.GetName(), fo.GetText())
        fn = new.GetField(fo.GetName())
        for attr in ('Position', 'TextAngle', 'Layer', 'Visible', 'TextSize', 'TextThickness', 'Mirrored',
                     'HorizJustify', 'VertJustify', 'KeepUpright'):
            getter, setter = getattr(fo, 'Get' + attr if hasattr(fo, 'Get' + attr) else 'Is' + attr, None), getattr(fn, 'Set' + attr, None)
            if getter is not None and setter is not None:
                setter(getter())
    nets = {p.GetNumber(): p.GetNet() for p in old.Pads()}
    for p in new.Pads():
        if p.GetNumber():                  # paste-only apertures (pass 2) have no number and no net
            p.SetNet(nets[p.GetNumber()])
    b.Delete(old)
    return new


def move_fp_with_tracks(b, ref, dx=0.0, dy=0.0):
    """Translate a footprint; every track end lying on one of its pads (same layer) moves with it."""
    f = fp_of(b, ref)
    pads = [(p.GetBoundingBox(), p) for p in f.Pads()]
    moved = []
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_TRACK':
            continue
        for which in ('Start', 'End'):
            pt = getattr(t, 'Get' + which)()
            for bb, pd in pads:
                if pd.IsOnLayer(t.GetLayer()) and t.GetNetname() == pd.GetNetname() and bb.Contains(pt):
                    moved.append((t, which, pt))
                    break
    f.Move(P(dx, dy))
    for t, which, pt in moved:
        getattr(t, 'Set' + which)(pcbnew.VECTOR2I(pt.x + MM(dx), pt.y + MM(dy)))


def track(b, netname, layer, pts, w=0.3):
    n = net(b, netname)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(P(x1, y1))
        t.SetEnd(P(x2, y2))
        t.SetWidth(MM(w))
        t.SetLayer(layer)
        t.SetNet(n)
        b.Add(t)


def via(b, netname, xy, dia=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(P(*xy))
    v.SetWidth(MM(dia))
    v.SetDrill(MM(drill))
    v.SetNet(net(b, netname))
    b.Add(v)
    return v


def close(a, c, tol=0.02):
    return abs(a[0] - c[0]) <= tol and abs(a[1] - c[1]) <= tol


def ends(t):
    return (mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y))


def seg_at(b, netname, a, c, layer=None, tol=0.02):
    """The track segment of netname whose endpoints are a and c (either order)."""
    for t in b.GetTracks():
        if t.GetClass() not in ('PCB_TRACK', 'PCB_ARC') or t.GetNetname() != netname:
            continue
        if layer is not None and t.GetLayer() != layer:
            continue
        s, e = ends(t)
        if (close(s, a, tol) and close(e, c, tol)) or (close(s, c, tol) and close(e, a, tol)):
            return t
    raise AssertionError(f'no {netname} segment {a} - {c}')


def via_at(b, netname, xy, tol=0.02):
    for v in b.GetTracks():
        if v.GetClass() == 'PCB_VIA' and v.GetNetname() == netname and close((mm(v.GetPosition().x), mm(v.GetPosition().y)), xy, tol):
            return v
    raise AssertionError(f'no {netname} via at {xy}')


def remove_segs(b, netname, pairs, layer=None):
    """Find every listed segment first, then delete them (Delete also clears the board caches;
    Remove + Python GC of the proxy corrupted later GetTracks() calls)."""
    items = [seg_at(b, netname, a, c, layer) for a, c in pairs]
    for it in items:
        b.Delete(it)


def set_seg(b, netname, a, c, new_a, new_c, layer=None):
    """Move the endpoints of an existing segment (keeps its width and layer)."""
    t = seg_at(b, netname, a, c, layer)
    s, e = ends(t)
    if close(s, a):
        t.SetStart(P(*new_a)); t.SetEnd(P(*new_c))
    else:
        t.SetStart(P(*new_c)); t.SetEnd(P(*new_a))


def place_pad(b, ref, rot, num, xy):
    """Rotate a footprint to rot, then translate it so pad num sits exactly at xy."""
    f = fp_of(b, ref)
    f.SetOrientationDegrees(rot)
    px, py = pad_xy(b, ref, num)
    f.Move(P(xy[0] - px, xy[1] - py))
    return f


def edge_circle(b, center, tol=0.02):
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            c = d.GetCenter()
            if close((mm(c.x), mm(c.y)), center, tol):
                return d
    raise AssertionError(f'no Edge.Cuts circle at {center}')


# ---------------------------------------------------------------------------------------------

def a1_enable_ride_through(b):
    """C87 (2.2 uF) beside R81, from BAT_ENABLE to GND. Pad 2 (GND) goes to the existing GND
    via at (13.0, 15.3) that already serves R81; pad 1 ties straight into R81's BAT_ENABLE pad."""
    if b.FindFootprintByReference('C87'):
        return
    r81_en = pad_xy(b, 'R81', '1') if fp_pad_net(b, 'R81', '1') == 'BAT_ENABLE' else pad_xy(b, 'R81', '2')
    x, y_en = r81_en[0] - 1.6, r81_en[1]
    c = add_fp(b, 'C0603', 'C87', '2.2uF', {'LCSC': 'C23630', 'LCSC Part': 'C23630'}, 'battery_entry',
               (x, y_en - 0.8), 90, {'1': 'BAT_ENABLE', '2': 'GND'})
    p1, p2 = (pad_xy(b, 'C87', n) for n in ('1', '2'))
    if p1[1] < p2[1]:                       # want pad 1 (BAT_ENABLE) below pad 2, level with R81's EN pad
        c.SetOrientationDegrees(270)
        p1, p2 = (pad_xy(b, 'C87', n) for n in ('1', '2'))
    c.Move(P(0, y_en - p1[1]))
    p1, p2 = (pad_xy(b, 'C87', n) for n in ('1', '2'))
    assert abs(p1[1] - y_en) < 1e-3 and p1[1] > p2[1], (p1, p2, y_en)
    gv = min((v for v in b.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND'),
             key=lambda v: (mm(v.GetPosition().x) - 13.0) ** 2 + (mm(v.GetPosition().y) - 15.3) ** 2)
    gxy = (mm(gv.GetPosition().x), mm(gv.GetPosition().y))
    assert abs(gxy[0] - 13.0) < 0.2 and abs(gxy[1] - 15.3) < 0.2, gxy
    track(b, 'BAT_ENABLE', pcbnew.F_Cu, [p1, r81_en])
    track(b, 'GND', pcbnew.F_Cu, [p2, gxy])
    place_ref(b, 'R81', r81_en[0] + 1.3, y_en - 0.8, 90)     # R81's old spot is now C87
    auto_ref(b, 'C87', 'F')


def fp_pad_net(b, ref, num):
    return next(p for p in fp_of(b, ref).Pads() if p.GetNumber() == num).GetNetname()


def a2_ovlo_release(b):
    f = fp_of(b, 'R83')
    f.SetValue('280k 0.1%')
    for k, v in {'LCSC': 'C705755', 'LCSC Part': 'C705755', 'Manufacturer Part': 'RT0603BRD07280KL'}.items():
        f.SetField(k, v)


def b4_b5_tie_hole_and_tp122(b):
    """B4 + B5. Zip-tie hole 1 moves from (26.5, 68.2) to (26.75, 68.2), the furthest it can go: the
    B.Cu RAW_PROTECTED lane (x 28.9) and the RAW_ACT strip (y 70.3) bound it, and Q124-R128-C126-R126
    are packed to 0.04-0.09 mm courtyard gaps. Pad clearance becomes 0.73 mm (R126) / 0.77 mm (R127),
    up from 0.52-0.56; C129 and the ARM1_SENSE via no longer sit beside it. The tie leaves the hole
    toward J122 (+y), away from R126/R127 (deviation from DESIGN_ASSURANCE 5.4's 2.0 mm, recorded). C129 (ARM1_SENSE filter)
    moves into TP122's old spot beside R133; ARM1_SENSE now leaves R133 through a via under J120's
    body, so the old via at (28.25, 69.95) that notched the RAW_ACT strip to 2.36 mm is gone.
    TP122 (PYRO1_GATE) moves to the bottom side, so no bare gate copper sits beside the armed
    PYRO1_BUS pad (it was 0.8 mm from R134 pad 2)."""
    hole = edge_circle(b, (26.5, 68.2), tol=0.05) if not fp_of(b, 'TP122').IsFlipped() else None
    if hole is None:
        return
    # x <= 26.8 keeps 0.5 mm to the B.Cu RAW_PROTECTED lane (x 28.9); y <= 68.2 keeps 0.5 mm to RAW_ACT
    hole.SetStart(P(26.75, 68.2)); hole.SetEnd(P(26.75 + 1.6, 68.2))
    # TP122 -> bottom, in-pad via (test pads carry no paste, so no wicking)
    remove_segs(b, 'PYRO1_GATE', [((26.6, 64.0), (24.4, 64.0))], pcbnew.F_Cu)
    set_seg(b, 'PYRO1_GATE', (20.0, 64.5), (26.6, 64.5), (20.0, 64.5), (24.4, 64.5), pcbnew.F_Cu)
    tp = fp_of(b, 'TP122')
    tp.Flip(tp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    tp.SetPosition(P(25.55, 64.0))
    track(b, 'PYRO1_GATE', pcbnew.F_Cu, [(24.4, 64.0), (25.55, 64.0)], 0.2)
    via(b, 'PYRO1_GATE', (25.55, 64.0))
    # ARM1_SENSE: old R133 -> C129 -> via (28.25, 69.95) route removed
    remove_segs(b, 'ARM1_SENSE', [((28.72, 64.0), (28.2021, 64.0)), ((28.2021, 64.0), (28.1998, 64.0)),
                                  ((28.1998, 64.0), (28.1998, 65.8502)), ((28.1998, 65.8502), (28.2979, 65.9483)),
                                  ((28.2979, 65.9483), (28.9, 65.9483)), ((28.9, 66.6), (28.9, 65.9483)),
                                  ((28.75, 69.45), (28.75, 66.95)), ((28.25, 69.95), (28.75, 69.45))], pcbnew.F_Cu)
    b.Delete(via_at(b, 'ARM1_SENSE', (28.25, 69.95)))
    set_seg(b, 'ARM1_SENSE', (28.25, 98.15), (28.25, 69.95), (28.25, 98.15), (28.25, 74.9), pcbnew.In2_Cu)
    place_pad(b, 'C129', 270, '1', (26.8, 63.5))
    assert pad_xy(b, 'C129', '2')[1] > 64.8, pad_xy(b, 'C129', '2')     # pad 2 (GND) below pad 1, 1.4 mm pitch
    track(b, 'ARM1_SENSE', pcbnew.F_Cu, [(28.72, 64.0), (27.7, 64.0), (27.2, 63.5), (26.8, 63.5)], 0.2)
    track(b, 'ARM1_SENSE', pcbnew.F_Cu, [(28.72, 64.0), (28.72, 64.55), (30.6, 64.55), (31.55, 65.5)], 0.2)
    via(b, 'ARM1_SENSE', (31.55, 65.5))
    # validation pass 1 (E1-F4, E4-F1/F2): the In2 run used to cross the bottom RAW_ACT strip, splitting
    # the In2 pour and running 0.30 mm from it. It now crosses the strip on B.Cu at x 35.3, between the
    # B.Cu VLOGIC and 3V3 lanes (west of them the 3.2 mm tie hole and the RAW_PROTECTED lane leave no via
    # room; west of the ring In2 is full), with both vias 0.5 mm or more clear of the strip.
    track(b, 'ARM1_SENSE', pcbnew.In2_Cu, [(31.55, 65.5), (35.3, 69.25)], 0.2)
    for xy in ((35.3, 69.25), (35.3, 73.75)):
        assert via_clear(b, xy, 'ARM1_SENSE', gap=0.2), xy
        via(b, 'ARM1_SENSE', xy)
    track(b, 'ARM1_SENSE', pcbnew.B_Cu, [(35.3, 69.25), (35.3, 73.75)], 0.2)
    track(b, 'ARM1_SENSE', pcbnew.In2_Cu, [(35.3, 73.75), (34.55, 74.5), (28.65, 74.5), (28.25, 74.9)], 0.2)
    for r in ('TP122', 'R127', 'C129'):
        auto_ref(b, r, 'B')


def b1_usb_detect(b):
    for ref, val, fields in (('R9', '1k', {'LCSC': 'C11702', 'LCSC Part': 'C11702', 'Manufacturer': '', 'Manufacturer Part': ''}),
                             ('R110', '1k 1%', {'LCSC': 'C21190', 'LCSC Part': 'C21190', 'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)',
                                                'Manufacturer Part': '0603WAF1001T5E'})):
        f = fp_of(b, ref)
        f.SetValue(val)
        for k, v in fields.items():
            f.SetField(k, v)


def b6_vias_out_of_pads(b):
    """B6: GND vias whose holes opened into SMD pads move >= 0.25 mm off the pad (vias are tented
    only). D8 (input TVS) also gets two more GND vias for a lower-inductance return."""
    for old, new in (((33.0, 111.0), (33.65, 111.0)), ((33.0, 114.5), (33.65, 114.5)), ((4.0, 14.0), (3.5, 14.0))):
        try:
            v = via_at(b, 'GND', old)
        except AssertionError:
            continue                                     # already moved
        segs = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'GND'
                and t.GetLayer() == pcbnew.F_Cu and any(close(e, old) for e in ends(t))]
        for t in segs:
            s_, e_ = ends(t)
            if close(s_, old):
                t.SetStart(P(*new))
            else:
                t.SetEnd(P(*new))
        v.SetPosition(P(*new))
    if not any(v.GetClass() == 'PCB_VIA' and close((mm(v.GetPosition().x), mm(v.GetPosition().y)), (3.5, 13.2))
               for v in b.GetTracks()):
        for y in (13.2, 14.8):
            via(b, 'GND', (3.5, y))
            track(b, 'GND', pcbnew.F_Cu, [(3.5, y), (4.6, y)], 0.4)


def b8_3v3a_rc(b):
    """L2 -> R164 (2.2 Ohm 0603) at L2's centre; short 0.5 mm stubs reach the old pad centres,
    which sit inside the 3V3 and 3V3A pours, so the connection does not depend on fill shape."""
    l2 = b.FindFootprintByReference('L2')
    if l2 is None:
        return
    path = l2.GetPath()
    c1, c2 = pad_xy(b, 'L2', '1'), pad_xy(b, 'L2', '2')
    assert fp_pad_net(b, 'L2', '1') == '3V3' and fp_pad_net(b, 'L2', '2') == '3V3A'
    centre = (mm(l2.GetPosition().x), mm(l2.GetPosition().y))
    b.Delete(l2)
    f = pcbnew.FootprintLoad(LIB, 'R_0603_1608Metric')
    f.SetFPID(pcbnew.LIB_ID('rocket', 'R_0603_1608Metric'))
    f.SetReference('R164'); f.SetValue('2.2R 1%')
    f.SetField('LCSC', 'C22939')
    for fld in f.GetFields():
        if fld.GetName() not in ('Reference', 'Value'):
            fld.SetVisible(False)
    t = f.Reference(); t.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0))); t.SetTextThickness(MM(0.15))
    f.SetPath(path)
    b.Add(f)
    f.SetOrientationDegrees(0)
    f.SetPosition(P(*centre))
    for pd in f.Pads():
        pd.SetNet(net(b, {'1': '3V3', '2': '3V3A'}[pd.GetNumber()]))
    p1, p2 = pad_xy(b, 'R164', '1'), pad_xy(b, 'R164', '2')
    assert p1[0] < p2[0], (p1, p2)
    track(b, '3V3', pcbnew.F_Cu, [p1, c1], 0.5)
    track(b, '3V3A', pcbnew.F_Cu, [p2, c2], 0.5)
    auto_ref(b, 'R164', 'F')


def b2_servo_feed(b):
    """B2: the servo feed (RAW_ACT, ~7.7 A with four HV6120 stalled) was F.Cu only, 3.0 mm and
    2.6 mm wide over 14 mm runs. In2 is free under it, so an In2 RAW_ACT pour follows the same ring
    (top strip, right strip, bottom strip) and runs down to J122's RAW pins, stitched to F.Cu with
    vias wherever a via clears every other net on all layers. Two In2 signals (ARM1_SENSE,
    PYRO2_GATE_N) cross the bottom strip and split that pour; each segment gets vias at both ends.
    Validation pass 2 (actuators F2, power P-3): the vias also keep 0.5 mm from every pyro gate, arm-sense,
    continuity and cold-sense net (m3.kicad_dru), which drops the two beside the B.Cu crossings."""
    if any(z.GetZoneName() == 'RAW_ACT_In2' for z in b.Zones()):
        return
    like = next(z for z in b.Zones() if z.GetNetname() == 'RAW_ACT' and z.IsOnLayer(pcbnew.F_Cu))
    ring = [(23.9, 34.6), (45.4, 34.6), (45.4, 72.9), (24.4, 72.9), (24.4, 82.6), (22.3, 82.6), (22.3, 70.3),
            (38.3, 70.3), (38.3, 37.6), (23.9, 37.6)]
    z = add_zone(b, 'RAW_ACT', pcbnew.In2_Cu, ring, 6, 'RAW_ACT_In2', like)
    z.SetLocalClearance(MM(0.5))           # pass 1 (E4-F2): >= 0.5 mm from every other net, pyro control included
    cands = [(x / 10, 36.1) for x in range(245, 445, 6)] + [(41.85, y / 10) for y in range(385, 700, 8)] + \
            [(x / 10, 71.6) for x in range(246, 445, 6)]
    placed = []
    for c in cands:
        if via_clear(b, c, 'RAW_ACT') and clear_of_nets(b, c, PYRO_CONTROL, 0.3, 0.5) and \
                all(((c[0] - q[0]) ** 2 + (c[1] - q[1]) ** 2) ** 0.5 >= 1.1 for q in placed):
            v = via(b, 'RAW_ACT', c)
            # pass 1 (E4-F1): no In1 ring, so the 1.2 mm pitch no longer merges the In1 (GND) antipads into slots
            v.SetRemoveUnconnected(True)
            v.SetKeepStartEnd(True)
            placed.append(c)
    print('  RAW_ACT stitching vias:', len(placed), sorted(placed))
    assert len(placed) >= 20, placed


PYRO_TERMINAL_FIELDS = {'LCSC': 'C430603', 'LCSC Part': 'C430603', 'Manufacturer': 'DORABO',
                        'Manufacturer Part': 'DB128L-5.08-2P-OG-S'}
ARM_TERMINAL_FIELDS = {'LCSC': 'C430601', 'LCSC Part': 'C430601', 'Manufacturer': 'DORABO',
                       'Manufacturer Part': 'DB128L-5.08-2P-BK-S'}           # validation pass 2 (actuators F1)
ARM_TERMINALS = ('J120', 'J124')


def a3_pyro_terminals(b):
    """A3 (copper side): J120/J121 4P green -> J120+J124 / J121+J125 DB128L 2P on the same holes (same
    pad positions and nets), then top-side function labels for every terminal, placed in the free strip
    between each terminal body and the board edge so they stay visible. Pass 2: the ARM pairs (J120, J124)
    are the black part, the igniter pairs orange (r4_sch.ARM_TERMINALS)."""
    if b.FindFootprintByReference('J124'):
        return
    for old, new, vals in (('J120', 'J124', ('ARM CH2: RAW / BUS2', 'ARM CH1: BUS1 / RAW')),
                           ('J121', 'J125', ('IGNITER 1: E1- / E1+', 'IGNITER 2: E2+ / E2-'))):
        f = fp_of(b, old)
        path, rot = f.GetPath(), f.GetOrientationDegrees()
        pos = {p.GetNumber(): (mm(p.GetPosition().x), mm(p.GetPosition().y)) for p in f.Pads()}
        nets = {p.GetNumber(): p.GetNetname() for p in f.Pads()}
        b.Delete(f)
        for ref, pins, pth, val in ((old, ('1', '2'), path, vals[0]),
                                    (new, ('3', '4'), pcbnew.KIID_PATH(f'/{ROOT}/{SHEET["pyro"]}/{uid(new)}'), vals[1])):
            name = 'M3_DB128L_2P_BK' if ref in ARM_TERMINALS else 'M3_DB128L_2P'
            g = pcbnew.FootprintLoad(LIB, name)
            g.SetFPID(pcbnew.LIB_ID('rocket', name))
            g.SetReference(ref)
            g.SetValue(val)
            for k, v in (ARM_TERMINAL_FIELDS if ref in ARM_TERMINALS else PYRO_TERMINAL_FIELDS).items():
                g.SetField(k, v)
            for fld in g.GetFields():
                if fld.GetName() not in ('Reference', 'Value'):
                    fld.SetVisible(False)
            g.SetPath(pth)
            b.Add(g)
            place_pad(b, ref, rot, '1', pos[pins[0]])
            assert close(pad_xy(b, ref, '2'), pos[pins[1]], 1e-3), (ref, pad_xy(b, ref, '2'), pos[pins[1]])
            for num, old_pin in (('1', pins[0]), ('2', pins[1])):
                next(p for p in g.Pads() if p.GetNumber() == num).SetNet(net(b, nets[old_pin]))
        for ref in (old, new):
            auto_ref(b, ref, 'F')
    # top-side function labels (the existing ones are on B.Silkscreen, facing the sled)
    labels = [('J120', '1', 'RAW'), ('J120', '2', 'BUS2'), ('J124', '1', 'BUS1'), ('J124', '2', 'RAW'),
              ('J121', '1', 'E1-'), ('J121', '2', 'E1+'), ('J125', '1', 'E2+'), ('J125', '2', 'E2-'),
              ('J9', '1', '5V'), ('J9', '2', 'GND'), ('J9', '3', 'RX'), ('J9', '4', 'TX')]   # J123 (pull-pin, no hazard) keeps its back-side labels
    for ref, num, text in labels:
        x, y = pad_xy(b, ref, num)
        if x > 30:        # right-hand terminals: strip between the body and the right edge
            place_label(b, text, (43.6, y), (41.9, y - 1.6, 45.3, y + 1.6))
        else:               # left-hand terminals: strip between the left edge and the body
            place_label(b, text, (2.4, y), (0.7, y - 1.6, 4.3, y + 1.6))
    optional = [('ARM', (43.6, 58.0), (41.9, 46.0, 45.3, 70.0), (0, 90)), ('IGN', (2.4, 58.0), (0.7, 46.0, 4.3, 70.0), (0, 90)),
                ('CAM', (2.4, 106.0), (0.7, 94.0, 4.3, 118.0), (0, 90))]
    j1 = [pad_xy(b, 'J1', n)[0] for n in ('1', '2', '3', '4')]
    optional += [(t, (x, 12.0), (x - 2.4, 11.4, x + 2.4, 14.5), (0,))
                 for x, t in ((j1[0], 'BAT+'), (j1[1], 'GND'), ((j1[2] + j1[3]) / 2, 'SW'))]   # one SW for the contact pair
    skipped = []
    for text, pref, box, angs in optional:          # best effort: the per-pin labels above are the requirement
        try:
            place_label(b, text, pref, box, angles=angs)
        except AssertionError:
            skipped.append(text)
    print('  optional labels skipped (no room):', skipped)


def m_courtyards(b):
    """Minor (R3 report 4): reload every footprint r4_lib.py changed (courtyards, paste apertures, and in
    validation pass 1 the silkscreen marks and the terminal wire-entry arrows; in pass 2 the MS5611 and
    AON6403 paste and J3's silkscreen)."""
    for ref in ('D120', 'D122', 'Q122', 'Q123', 'Q120', 'Q121', 'LS120', 'C121', 'D123', 'U9', 'U7',
                'U2', 'D8', 'D9', 'Q124', 'Q125', 'J122', 'J1', 'J9', 'J3', 'U5'):
        refresh_from_lib(b, ref)


def m_courtyard_clearances(b):
    """With true courtyards: the buzzer LS120 off Q123 (their BUZZ_OUT pads touched), D120 off C121, R138 off D120, and R123 turned vertical into the slot between C121's GND pad and Q122 (its GND pad
    overlapped C121's, a tombstone risk for the 0402)."""
    if abs(mm(fp_of(b, 'LS120').GetPosition().x) - 7.0) > 1e-3:
        return
    move_fp_with_tracks(b, 'LS120', dx=-0.55)            # off Q123's BUZZ_OUT pad (moving Q123 hits ARM2_SENSE)
    move_fp_with_tracks(b, 'D120', dy=0.15)              # off C121's base courtyard
    move_fp_with_tracks(b, 'R138', dy=0.3)               # keeps 0.04 mm to D120, 0.02 mm to R139
    move_fp_with_tracks(b, 'TP123', dx=-0.15, dy=0.2)    # off D120 and the PYRO1_COLD trace; 4.4 mm from PYRO2_BUS
    # R123: old pads ACT_EN (32.03, 39.7) / GND (31.17, 39.7) -> vertical, ACT_EN on top at (32.03, 39.38)
    set_seg(b, 'ACT_EN', (32.03, 38.4), (32.03, 39.7), (32.03, 38.4), (32.03, 39.38), pcbnew.F_Cu) if _has_seg(b, 'ACT_EN', (32.03, 38.4), (32.03, 39.7)) else None
    remove_segs(b, 'GND', [((31.17, 39.7), (31.17, 40.2)), ((31.17, 40.2), (31.72, 40.75))], pcbnew.F_Cu)
    place_pad(b, 'R123', 90, '1', (32.03, 39.38))
    if pad_xy(b, 'R123', '2')[1] < 39.38:
        place_pad(b, 'R123', 270, '1', (32.03, 39.38))
    g = pad_xy(b, 'R123', '2')
    assert g[1] > 39.9, g
    # pass 1 (E5-F2): the GND via at (31.72, 40.75) left a 0.08 mm mask dam to the turned R123's pad; it
    # moves down until the dam is >= 0.15 mm (nothing else ends on it)
    v = via_at(b, 'GND', (31.72, 40.75))
    assert not [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and any(close(e, (31.72, 40.75)) for e in ends(t))]
    gv = next(c for c in ((31.75, 41.1), (31.6, 41.2), (31.9, 41.2)) if via_clear(b, c, 'GND', gap=0.2))
    v.SetPosition(P(*gv))
    track(b, 'GND', pcbnew.F_Cu, [g, gv], 0.3)
    auto_ref(b, 'R123', 'F')


def _has_seg(b, netname, a, c):
    try:
        seg_at(b, netname, a, c)
        return True
    except AssertionError:
        return False


def m_u9_input(b):
    """C88 (100 nF) at U9 IN, vertical at (21.0, 14.5): BAT_IN pad stubs into the wide BAT_IN feed,
    GND pad sits in the GND pour with its own via. Plus BAT_IN vias from that feed to the In2
    BAT_IN plane, so IN sees a low-impedance source."""
    if b.FindFootprintByReference('C88'):
        return
    add_fp(b, 'C0402', 'C88', '100nF 50V', {'LCSC': 'C307331'}, 'battery_entry', (21.0, 14.5), 90, {'1': 'BAT_IN', '2': 'GND'})
    if pad_xy(b, 'C88', '1')[1] > pad_xy(b, 'C88', '2')[1]:
        fp_of(b, 'C88').SetOrientationDegrees(270)
    p1, p2 = pad_xy(b, 'C88', '1'), pad_xy(b, 'C88', '2')
    assert p1[1] < p2[1], (p1, p2)
    track(b, 'BAT_IN', pcbnew.F_Cu, [p1, (19.75, p1[1])], 0.4)
    gv = next(c for c in ((21.0, p2[1] + 0.75), (21.6, p2[1] + 0.5), (21.75, p2[1])) if via_clear(b, c, 'GND'))
    via(b, 'GND', gv)
    track(b, 'GND', pcbnew.F_Cu, [p2, gv], 0.4)
    n = 0
    for y in (12.6, 13.3):
        if via_clear(b, (19.75, y), 'BAT_IN', gap=0.2):
            via(b, 'BAT_IN', (19.75, y)); n += 1
    print('  U9 IN: BAT_IN vias added', n)
    auto_ref(b, 'C88', 'F')
    auto_ref(b, 'TP89', 'F')                             # its text sat where C88's pad now is


def m_thermal_reliefs(b):
    """Minor: through-hole GND pins were solid into the outer GND pours, which starves hole fill in
    JLC's THT soldering. The F.Cu/B.Cu GND pours now use thermal reliefs for through-hole pads only
    (SMD pads stay solid; In1 already used reliefs). Power pours (BAT_IN, RAW_ACT) stay solid: their
    few THT pins carry servo or battery current and some sit in narrow pour fingers that spokes cannot
    reach (J122's RAW pins fill the 2.1 mm In2 finger). Validation pass 1 (E5-F4): J122's GND pins 3/6/9
    get spokes at 45 deg, aimed between the neighbouring pins. Pads whose spokes would be starved keep a
    local full connection (DRC: fewer than 2 spokes, or a spoke into an isolated island): J122.12 (B.Cu
    3V3 and sense tracks hem it in), J2.1 and J3 shell leg 4. Pass 2 (DFM): legs 1-3 resolve their spokes,
    so only leg 4 stays solid; reliefs make the pin-in-paste reflow and any hand touch-up easier."""
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and b.GetLayerName(z.GetLayer()) in ('F.Cu', 'B.Cu'):
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
    for pd in fp_of(b, 'J122').Pads():
        if pd.GetNumber() in ('3', '6', '9'):
            pd.SetThermalSpokeAngleDegrees(45)
    for ref, nums in (('J122', ('12',)), ('J2', ('1',)), ('J3', ('4',))):
        for pd in fp_of(b, ref).Pads():
            if pd.GetNumber() in nums:
                pd.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)


def m_track_cleanup(b):
    """Minor (AGENTS.md routing rule): drop zero-length and duplicate segments and merge collinear
    fragments of one net/layer/width where nothing else (pad, via, third track) meets the joint.
    Geometry is unchanged; the 0.1 mm router jogs stay (electrically nil, recorded)."""
    tracks = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    dead, seen = [], set()
    for t in tracks:
        s_, e_ = t.GetStart(), t.GetEnd()
        if s_.x == e_.x and s_.y == e_.y:
            dead.append(t); continue
        key = (t.GetNetname(), t.GetLayer(), t.GetWidth()) + tuple(sorted(((s_.x, s_.y), (e_.x, e_.y))))
        if key in seen:
            dead.append(t)
        seen.add(key)
    for t in dead:
        b.Delete(t)
    vias = {(v.GetPosition().x, v.GetPosition().y) for v in b.GetTracks() if v.GetClass() == 'PCB_VIA'}
    padboxes = [(pd.GetBoundingBox(), pd) for f in b.GetFootprints() for pd in f.Pads()]
    merged = 0
    changed = True
    while changed:
        changed = False
        ends_ = {}
        for t in b.GetTracks():
            if t.GetClass() != 'PCB_TRACK':
                continue
            for pt in (t.GetStart(), t.GetEnd()):
                ends_.setdefault((t.GetLayer(), pt.x, pt.y), []).append(t)
        for (layer, x, y), ts in ends_.items():
            if len(ts) != 2 or (x, y) in vias:
                continue
            a, c = ts
            if a.GetNetname() != c.GetNetname() or a.GetWidth() != c.GetWidth():
                continue
            pt = pcbnew.VECTOR2I(x, y)
            if any(pd.IsOnLayer(layer) and bb.Contains(pt) for bb, pd in padboxes):
                continue
            pa = a.GetEnd() if (a.GetStart().x, a.GetStart().y) == (x, y) else a.GetStart()
            pc = c.GetEnd() if (c.GetStart().x, c.GetStart().y) == (x, y) else c.GetStart()
            v1, v2 = (x - pa.x, y - pa.y), (pc.x - x, pc.y - y)
            if v1[0] * v2[1] - v1[1] * v2[0] != 0 or v1[0] * v2[0] + v1[1] * v2[1] <= 0:
                continue                                  # not straight-through collinear
            a.SetStart(pa); a.SetEnd(pc)
            b.Delete(c)
            merged += 1
            changed = True
            break
    # validation pass 1 (E2): a segment lying entirely on a wider-or-equal collinear segment of the same
    # net and layer adds no copper (three such: 3V3 at y 160.5, USB_DM inside D4.1, VBUS below C83)
    segs = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    covered = []
    for a in segs:
        (ax, ay), (bx, by) = ends(a)
        for c in segs:
            if c is a or c.GetNetname() != a.GetNetname() or c.GetLayer() != a.GetLayer() or c.GetWidth() < a.GetWidth():
                continue
            (cx, cy), (dx, dy) = ends(c)
            L = ((dx - cx) ** 2 + (dy - cy) ** 2) ** 0.5
            if L < 1e-6:
                continue
            ux, uy = (dx - cx) / L, (dy - cy) / L
            on = all(abs((px - cx) * uy - (py - cy) * ux) < 1e-3 and -1e-3 <= (px - cx) * ux + (py - cy) * uy <= L + 1e-3
                     for px, py in ((ax, ay), (bx, by)))
            if on and not (a.GetWidth() == c.GetWidth() and id(c) in {id(x) for x in covered}):
                covered.append(a)
                break
    for t in covered:
        b.Delete(t)
    print(f'  track cleanup: {len(dead)} zero-length/duplicate removed, {merged} collinear merges, '
          f'{len(covered)} covered segments removed')


def m_pin1_marks(b):
    """Minor: U7-U11 and U13 had no pin-1 mark (U7-U11 look the same rotated 180 deg)."""
    import math
    obs = _silk_obstacles(b, pcbnew.F_SilkS, None)
    for ref in ('U7', 'U8', 'U9', 'U10', 'U11', 'U13'):
        f = fp_of(b, ref)
        c = f.GetPosition()
        p1 = next(p for p in f.Pads() if p.GetNumber() == '1')
        q = p1.GetPosition()
        base = math.atan2(q.y - c.y, q.x - c.x)
        half = max(p1.GetBoundingBox().GetWidth(), p1.GetBoundingBox().GetHeight()) / 2
        body = None             # pass 1 (E5-F7): the dot must be visible after assembly, so not under the package
        for g in f.GraphicalItems():
            if g.GetLayer() == pcbnew.F_Fab and g.GetClass() == 'PCB_SHAPE':
                if body is None:
                    body = g.GetBoundingBox()
                else:
                    body.Merge(g.GetBoundingBox())
        for k in range(16 * 9):
            reach = half + MM(0.35 + 0.1 * (k // 16))
            ang = base + ((k % 16) // 2) * (1 if k % 2 else -1) * math.pi / 8
            x, y = q.x + reach * math.cos(ang), q.y + reach * math.sin(ang)
            dot = pcbnew.PCB_SHAPE(b)
            dot.SetShape(pcbnew.SHAPE_T_CIRCLE)
            dot.SetLayer(pcbnew.F_SilkS)
            dot.SetStart(pcbnew.VECTOR2I(int(x), int(y)))
            dot.SetEnd(pcbnew.VECTOR2I(int(x + MM(0.1)), int(y)))
            dot.SetWidth(MM(0.2))
            dot.SetFilled(True)
            bb = dot.GetBoundingBox(); bb.Inflate(MM(0.15))
            if not any(bb.Intersects(o) for o in obs) and not (body is not None and dot.GetBoundingBox().Intersects(body)):
                b.Add(dot)
                obs.append(dot.GetBoundingBox())
                break
        else:
            print('  no room for a pin-1 dot at', ref)


def keepout(b, name, pts, layer=pcbnew.F_Cu, tracks=False, vias=True, fill=True):
    """Rule area on one layer: by default no zone fill and no vias (tracks allowed for pad stubs)."""
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    z.SetLayer(layer)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowZoneFills(fill)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(MM(x), MM(y))
    b.Add(z)
    return z


def m_imu(b):
    """U4 -> ST LSM6DSV320X (same land and pin numbers; see r4_sch.m_imu_lsm6dsv320x), with the
    sensor layout ST TN0018/TN1383 and TE ask for: no vias and no copper fill under either MEMS body on
    the component side (requirement P3). Pins 10/11 open.
    IMU: the GND via at the package centre goes; pins 6/7 reach C31's GND pad and pins 2/3 stub out to
    the pour. The BOOT0 via had its ring 0.15 mm inside the IMU corner (0.21 mm from pad 4): it moves
    to (36.65, 169.90), 0.08 mm outside, after IMU_INT1's via steps from (36.2, 169.5) to (35.9, 169.25)
    (below the body the B.Cu IMU_CS lane and the 3V3A via at pin 5 leave no room). SPI1_SCK and BOOT0
    still cross under the IMU on B.Cu, which TN1383 3.4 allows. C30/C31 turn 180 deg so each 3V3A pad
    reaches its supply pin (5 VDDIO, 8 VDD) on F.Cu, not only through the In2 plane.
    MS5611: the keep-out covers the whole 5.0 x 3.0 body (TE: no tracks between the pads). Pad 5's GND
    via ring reached 0.10 mm under the body: the via moves out to (41.75, 159.2). Pad 4's (same, and
    B.Cu QSPI_IO2 blocks moving it) goes; pad 4 joins pad 3 just outside the body. C32 moves from the
    far side of the sensor to just below its VDD pins (was ~6 nH through a via, an In2 finger and a via)."""
    if fp_of(b, 'U4').GetValue() == 'LSM6DSV320X':
        return
    refresh_from_lib(b, 'U4')                                   # land 0.575 x 0.28, NSMD +0.04, paste 88 % (r4_lib)
    f = fp_of(b, 'U4')
    f.SetValue('LSM6DSV320X')
    f.SetField('LCSC', 'C26633007')
    if f.HasField('LCSC Part'):
        f.SetField('LCSC Part', 'C26633007')
    for num, name in (('9', 'unconnected-(U4-INT2-Pad9)'), ('10', 'unconnected-(U4-OCS_aux-Pad10)'),
                      ('11', 'unconnected-(U4-SDO_aux-Pad11)')):
        n = pcbnew.NETINFO_ITEM(b, name)
        b.Add(n)
        next(p_ for p_ in f.Pads() if p_.GetNumber() == num).SetNet(n)
    remove_segs(b, 'GND', [((39.76, 168.25), (39.76, 167.75)), ((39.76, 167.75), (40.7, 167.4)),
                           ((38.5, 169.51), (38.5, 168.5))], pcbnew.F_Cu)
    for v in [via_at(b, 'GND', (40.7, 167.4)), via_at(b, 'GND', (38.5, 168.5))]:
        b.Delete(v)
    # C30/C31 turn about their centres; the R3 stubs that now meet the other pad change net or go
    for ref in ('C30', 'C31'):
        rt = fp_of(b, ref).Reference()
        keep = (rt.GetPosition(), rt.GetTextAngleDegrees())
        fp_of(b, ref).SetOrientationDegrees(180)
        rt.SetPosition(keep[0]); rt.SetTextAngleDegrees(keep[1])
    assert close(pad_xy(b, 'C30', '1'), (37.02, 171.4)) and close(pad_xy(b, 'C31', '1'), (40.02, 171.2))
    for a, c in (((36.18, 171.4), (36.18, 172.3)), ((36.18, 172.3), (36.5, 172.3)), ((39.18, 171.2), (39.2, 172.0))):
        seg_at(b, '3V3A', a, c, pcbnew.F_Cu).SetNet(net(b, 'GND'))
    for xy in ((36.5, 172.3), (39.2, 172.0)):
        via_at(b, '3V3A', xy).SetNet(net(b, 'GND'))
    remove_segs(b, 'GND', [((37.02, 171.4), (37.3, 172.2)), ((40.02, 171.2), (40.9, 171.2))], pcbnew.F_Cu)
    track(b, 'GND', pcbnew.F_Cu, [(38.5, 169.46), (38.5, 170.15), (39.0, 170.15)], 0.25)
    track(b, 'GND', pcbnew.F_Cu, [(39.0, 169.46), (39.0, 170.15), (39.0, 171.05)], 0.25)       # pins 6/7 -> C31.2
    track(b, 'GND', pcbnew.F_Cu, [(37.29, 168.25), (36.55, 168.25), (36.55, 168.75), (37.29, 168.75)], 0.25)
    track(b, '3V3A', pcbnew.F_Cu, [(37.02, 171.4), (38.0, 171.4)], 0.25)        # C30.1 -> pin 5's via and trace
    track(b, '3V3A', pcbnew.F_Cu, [(40.1, 169.25), (40.1, 171.05)], 0.25)       # pin 8 -> C31.1
    # BOOT0 via out from under the IMU corner (IMU_INT1's via moves first)
    via_at(b, 'IMU_INT1', (36.2, 169.5)).SetPosition(P(35.9, 169.25))
    set_seg(b, 'IMU_INT1', (36.2, 169.5), (37.24, 169.25), (35.9, 169.25), (37.24, 169.25), pcbnew.F_Cu)
    set_seg(b, 'IMU_INT1', (35.8, 169.8), (36.2, 169.5), (35.35, 169.8), (35.9, 169.25), pcbnew.B_Cu)
    set_seg(b, 'IMU_INT1', (30.5, 169.8), (35.8, 169.8), (30.5, 169.8), (35.35, 169.8), pcbnew.B_Cu)
    via_at(b, 'BOOT0', (37.1, 169.9)).SetPosition(P(36.65, 169.9))
    remove_segs(b, 'BOOT0', [((37.1, 169.9), (36.7, 169.9)), ((36.7, 169.9), (35.75, 170.85)),
                             ((35.75, 170.85), (35.7, 170.85)), ((35.7, 170.85), (35.05, 171.5))], pcbnew.F_Cu)
    track(b, 'BOOT0', pcbnew.F_Cu, [(36.65, 169.9), (35.05, 171.5)], 0.25)
    set_seg(b, 'BOOT0', (38.0, 169.9), (37.1, 169.9), (38.0, 169.9), (36.65, 169.9), pcbnew.B_Cu)
    keepout(b, 'IMU_body_F', [(37.0, 167.25), (40.0, 167.25), (40.0, 169.75), (37.0, 169.75)])
    # MS5611
    u5 = fp_of(b, 'U5')
    cx, cy = mm(u5.GetPosition().x), mm(u5.GetPosition().y)
    keepout(b, 'BARO_reserved_F', [(cx - 2.5, cy - 1.5), (cx + 2.5, cy - 1.5), (cx + 2.5, cy + 1.5), (cx - 2.5, cy + 1.5)])
    via_at(b, 'GND', (41.7, 159.8)).SetPosition(P(41.75, 159.2))
    set_seg(b, 'GND', (40.88, 159.75), (41.7, 159.8), (40.88, 159.2), (41.75, 159.2), pcbnew.F_Cu)
    remove_segs(b, 'GND', [((40.88, 162.35), (41.7, 162.4))], pcbnew.F_Cu)
    b.Delete(via_at(b, 'GND', (41.7, 162.4)))
    track(b, 'GND', pcbnew.F_Cu, [(39.63, 162.85), (40.88, 162.85)], 0.25)
    remove_segs(b, '3V3A', [((37.58, 157.9), (37.6, 157.0))], pcbnew.F_Cu)
    b.Delete(via_at(b, '3V3A', (37.6, 157.0)))
    remove_segs(b, 'GND', [((38.42, 157.9), (39.3, 157.9))], pcbnew.F_Cu)
    c32 = fp_of(b, 'C32')
    c32.SetOrientationDegrees(0)
    c32.SetPosition(P(38.35, 164.35))
    p1, p2 = pad_xy(b, 'C32', '1'), pad_xy(b, 'C32', '2')
    assert p1[0] < p2[0] and abs(p1[1] - 164.35) < 1e-3, (p1, p2)
    track(b, '3V3A', pcbnew.F_Cu, [p1, (p1[0], 163.7)], 0.25)        # onto the pin 2 / plane-via diagonal
    track(b, 'GND', pcbnew.F_Cu, [p2, (39.37, 163.75)], 0.25)        # into pad 3's GND via (39.6, 163.6)
    for ref in ('C32', 'U5'):                                    # U5's reference sat where C32 now is
        try:
            auto_ref(b, ref, 'F')
        except AssertionError:
            auto_ref(b, ref, 'B')                                # crowded: the board keeps such references on the back


# --- validation pass 1 (docs/M3_R4.md section 1b) ----------------------------------------------

def v_pyro2_gate_crossing(b):
    """E1-F4, E4-F1/F2/F3, E6-5: PYRO2_GATE_N crossed the bottom RAW_ACT strip on In2, splitting the new
    In2 pour and running 0.30 mm from it (a latent inner-layer short would gate channel 2 on with the
    MCU in reset), and its In2 diagonal passed 0.29 mm from J124.2's (RAW_ACT) ring. Its F.Cu via sat
    0.25 mm from R135's PYRO2_BUS pad. Now: the via moves to (26.7, 53.25), 0.95 mm from R135 (the In2
    RAW_ACT_SENSE diagonal and the PYRO1_COLD trace bound it); the In2 diagonal shifts 0.35 mm off
    J124.2 (0.64 mm); the strip crossing drops to B.Cu, vias 0.55 mm clear of the strip. Runs before
    b2_servo_feed so its stitching vias keep clear of the new B.Cu run."""
    if not _has_seg(b, 'PYRO2_GATE_N', (37.45, 122.65), (37.45, 69.45)):
        return
    remove_segs(b, 'PYRO2_GATE_N', [((37.45, 122.65), (37.45, 69.45)), ((37.45, 69.45), (26.25, 58.25)),
                                    ((26.25, 58.25), (26.25, 53.95))], pcbnew.In2_Cu)
    remove_segs(b, 'PYRO2_GATE_N', [((25.95, 52.35), (25.95, 53.55)), ((26.25, 53.95), (24.65, 52.35))], pcbnew.F_Cu)
    b.Delete(via_at(b, 'PYRO2_GATE_N', (26.25, 53.95)))
    for xy in ((26.7, 53.25), (36.95, 69.45), (36.95, 73.75)):
        assert via_clear(b, xy, 'PYRO2_GATE_N'), xy
        via(b, 'PYRO2_GATE_N', xy)
    track(b, 'PYRO2_GATE_N', pcbnew.F_Cu, [(25.95, 52.35), (25.95, 52.5), (26.7, 53.25)], 0.2)      # from R138.1
    track(b, 'PYRO2_GATE_N', pcbnew.F_Cu, [(24.65, 52.35), (25.55, 53.25), (26.7, 53.25)], 0.2)     # from R139.1
    track(b, 'PYRO2_GATE_N', pcbnew.In2_Cu, [(26.7, 53.25), (26.7, 59.2), (36.95, 69.45)], 0.2)
    track(b, 'PYRO2_GATE_N', pcbnew.B_Cu, [(36.95, 69.45), (36.95, 73.75)], 0.2)
    track(b, 'PYRO2_GATE_N', pcbnew.In2_Cu, [(36.95, 73.75), (37.45, 74.25), (37.45, 122.65)], 0.2)


def _set_fields(f, value, fields):
    """Footprint value + fields; a field the footprint lacks is only added when it is a core one (the
    schematic symbol gets the same treatment, so both sides keep the same field set)."""
    f.SetValue(value)
    for k, v in fields.items():
        if f.HasField(k) or k in ('LCSC', 'Manufacturer', 'Manufacturer Part'):
            f.SetField(k, v)


def v_input_protection(b):
    """Same change as r4_sch.v_input_protection: D8 SMBJ12CA, C88 50 V (set in m_u9_input), R125 1k,
    R80 470k, R81 300k, and R165 470k between J1.4 (now its own net, BAT_SW_RETURN) and the EN network.
    R165 (0402) sits in the only free spot, just below J1.4: J1.4 drops straight to it on F.Cu, and its
    EN side joins the existing B.Cu run to U9 through a via under J1's back edge."""
    if b.FindFootprintByReference('R165'):
        return
    uni = {'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)'}
    _set_fields(fp_of(b, 'D8'), 'SMBJ12CA', {'LCSC': 'C83849', 'LCSC Part': 'C83849', 'Manufacturer': 'Littelfuse',
                                             'Manufacturer Part': 'SMBJ12CA'})
    _set_fields(fp_of(b, 'R125'), '1k', {'LCSC': 'C11702', 'LCSC Part': 'C11702'})
    _set_fields(fp_of(b, 'R80'), '470k 1%', {'LCSC': 'C23178', 'LCSC Part': 'C23178', 'Manufacturer Part': '0603WAF4703T5E', **uni})
    _set_fields(fp_of(b, 'R81'), '300k 1%', {'LCSC': 'C23024', 'LCSC Part': 'C23024', 'Manufacturer Part': '0603WAF3003T5E', **uni})
    n = pcbnew.NETINFO_ITEM(b, 'BAT_SW_RETURN')
    b.Add(n)
    next(p for p in fp_of(b, 'J1').Pads() if p.GetNumber() == '4').SetNet(n)
    add_fp(b, 'R0402', 'R165', '470k 1%', {'LCSC': 'C25790', 'LCSC Part': 'C25790', 'Manufacturer Part': '0402WGF4703TCE', **uni},
           'battery_entry', (30.19, 11.85), 180, {'1': 'BAT_SW_RETURN', '2': 'BAT_ENABLE'})
    p1, p2 = pad_xy(b, 'R165', '1'), pad_xy(b, 'R165', '2')
    assert abs(p1[0] - 30.62) < 0.02 and p2[0] < p1[0], (p1, p2)
    j14 = pad_xy(b, 'J1', '4')
    track(b, 'BAT_SW_RETURN', pcbnew.F_Cu, [j14, p1], 0.25)
    vxy = (round(p2[0] - 0.85, 3), round(p2[1] - 0.85, 3))
    assert via_clear(b, vxy, 'BAT_ENABLE', gap=0.2), vxy
    via(b, 'BAT_ENABLE', vxy)
    track(b, 'BAT_ENABLE', pcbnew.F_Cu, [p2, vxy], 0.25)
    set_seg(b, 'BAT_ENABLE', (19.0, 15.3), (29.4, 5.9), (19.0, 15.3), vxy, pcbnew.B_Cu)
    auto_ref(b, 'R165', 'F')
    sw = [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == 'SW' and mm(d.GetPosition().y) < 16]
    for d in sw:                                             # a3's optional J1 label sat where R165 now is
        b.Delete(d)
    x = (pad_xy(b, 'J1', '3')[0] + pad_xy(b, 'J1', '4')[0]) / 2
    try:
        place_label(b, 'SW', (x, 12.0), (x - 2.6, 11.2, x + 2.6, 14.5), angles=(0,))
    except AssertionError:
        try:
            place_label(b, 'SW', (x, 13.1), (x - 3.0, 11.0, x + 2.0, 15.0), angles=(0, 90))
        except AssertionError:
            print('  J1 SW label: no room after R165 (optional; the pin labels are on the bottom side)')


def v_tp123_bottom(b):
    """E4-F3: TP123 (bare PYRO2_GATE pad) sat 0.55 mm from D120 pin 3 (3V3): a probe slip would turn
    channel 2's FET on (VGS(th) 0.4-1.2 V) and fire it if armed. Like TP122 (R4 B5) it moves to the
    bottom side on the same spot, with an in-pad via (test pads carry no paste)."""
    tp = fp_of(b, 'TP123')
    if tp.IsFlipped():
        return
    xy = (round(mm(tp.GetPosition().x), 3), round(mm(tp.GetPosition().y), 3))
    tp.Flip(tp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    tp.SetPosition(P(*xy))
    assert via_clear(b, xy, 'PYRO2_GATE', gap=0.2), xy
    via(b, 'PYRO2_GATE', xy)
    for t in b.GetTracks():                                  # tracks that ended on the old pad end on the via centre
        if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'PYRO2_GATE' and t.GetLayer() == pcbnew.F_Cu:
            s_, e_ = ends(t)
            if close(s_, xy, 0.35):
                t.SetStart(P(*xy))
            if close(e_, xy, 0.35):
                t.SetEnd(P(*xy))
    for t in [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'PYRO2_GATE'
              and t.GetStart().x == t.GetEnd().x and t.GetStart().y == t.GetEnd().y]:
        b.Delete(t)
    auto_ref(b, 'TP123', 'B')


def _move_via(b, netname, old, new):
    v = via_at(b, netname, old)
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == netname:
            s_, e_ = ends(t)
            if close(s_, old):
                t.SetStart(P(*new))
            elif close(e_, old):
                t.SetEnd(P(*new))
    v.SetPosition(P(*new))


def v_mask_dams(b):
    """E5-F2: via holes against small-pad mask openings below or at JLC's 0.1 mm mask dam. R11.2's
    3V3 via (0.037 mm) moves to straight above the pad, still in the In2 3V3 area; D9.2's GND via
    (0.10 mm) moves 0.3 mm out. (R123's is fixed in m_courtyard_clearances.)"""
    try:
        via_at(b, '3V3', (40.9, 165.6))
    except AssertionError:
        return
    remove_segs(b, '3V3', [((40.42, 165.6), (40.9, 165.6))], pcbnew.F_Cu)
    b.Delete(via_at(b, '3V3', (40.9, 165.6)))
    r11 = pad_xy(b, 'R11', '2')
    new = (r11[0], 164.85)
    assert via_clear(b, new, '3V3', gap=0.2), new
    via(b, '3V3', new)
    track(b, '3V3', pcbnew.F_Cu, [r11, new], 0.25)
    assert via_clear(b, (14.2, 25.0), 'GND', gap=0.2)
    _move_via(b, 'GND', (14.5, 25.0), (14.2, 25.0))


def v_camera_via(b):
    """E1-F6: the camera feed (RAW_PROTECTED, up to 1.24 A) changed layer through one 0.3 mm via at
    TP70. A second via 1.2 mm west on the same F.Cu/B.Cu runs halves the current per barrel."""
    if not _has_seg(b, 'RAW_PROTECTED', (26.0, 89.5), (18.0, 89.5)):
        return
    assert via_clear(b, (16.8, 89.5), 'RAW_PROTECTED', gap=0.2)
    set_seg(b, 'RAW_PROTECTED', (26.0, 89.5), (18.0, 89.5), (26.0, 89.5), (16.8, 89.5), pcbnew.B_Cu)
    via(b, 'RAW_PROTECTED', (16.8, 89.5))


def v_j123_jst(b):
    """E5-F5/E6 (P2/P3): J123 PZ254 2.54 mm header -> JST PH B2B-PH-K-S (C131337), same x, same centre.
    Pin 1 (PULLPIN_EXT) on top at (42.0, 74.85), pin 2 (GND) at (42.0, 76.85); the deep (front) side of
    the body faces inboard. PULLPIN_EXT now leaves pin 1 westward, clear of pin 2."""
    old = fp_of(b, 'J123')
    if str(old.GetFPID().GetLibItemName()) == 'M3_JST_PH_B2B_2P':
        return
    path = old.GetPath()
    keep = {f.GetName(): f.GetText() for f in old.GetFields()
            if f.GetName() not in ('Reference', 'Value', 'Footprint', 'Datasheet', 'Description')}
    b.Delete(old)
    g = pcbnew.FootprintLoad(LIB, 'M3_JST_PH_B2B_2P')
    assert g is not None
    g.SetFPID(pcbnew.LIB_ID('rocket', 'M3_JST_PH_B2B_2P'))
    g.SetReference('J123')
    t = g.Reference(); t.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0))); t.SetTextThickness(MM(0.15))
    keep.update({'LCSC': 'C131337', 'Manufacturer': 'JST', 'Manufacturer Part': 'B2B-PH-K-S(LF)(SN)'})
    if 'LCSC Part' in keep:
        keep['LCSC Part'] = 'C131337'
    g.SetValue('PULL-PIN PH 1x2')
    for k, v in keep.items():
        g.SetField(k, v)
    for fld in g.GetFields():
        if fld.GetName() not in ('Reference', 'Value'):
            fld.SetVisible(False)
    g.SetPath(path)
    b.Add(g)
    place_pad(b, 'J123', 270, '1', (42.0, 74.85))
    assert close(pad_xy(b, 'J123', '2'), (42.0, 76.85), 1e-3), pad_xy(b, 'J123', '2')
    for p in g.Pads():
        p.SetNet(net(b, {'1': 'PULLPIN_EXT', '2': 'GND'}[p.GetNumber()]))
    remove_segs(b, 'PULLPIN_EXT', [((42.0, 74.6), (42.0, 75.702)), ((42.0, 75.702), (41.862, 75.702)),
                                   ((41.862, 75.702), (40.522, 77.042))], pcbnew.F_Cu)
    track(b, 'PULLPIN_EXT', pcbnew.F_Cu, [(42.0, 74.85), (40.522, 74.85), (40.522, 77.042)], 0.2)
    auto_ref(b, 'J123', 'F')


def v_silk(b):
    """E4-F4, E5-F7: the bottom ARM-plug legend still used the old 4-pin numbers; J122 gets S/+/- on
    top (R3 A3 asked for it). (The three R3 board-level dots flagged as 0.05 mm are filled r 0.3 dots.)"""
    for d in b.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == 'ARM PLUG: 4-F1-3 / 1-F2-2':
            d.SetText('ARM PLUG: J124 2-F1-1 / J120 1-F2-2')
    for d in b.GetDrawings():                                 # J123's back-side labels follow its new pin pitch
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == pcbnew.B_SilkS and abs(mm(d.GetPosition().x) - 39.0) < 0.2:
            for txt, old_y, new_y in (('PULL', 74.6, 74.85), ('GND', 77.14, 76.85)):
                if d.GetText() == txt and abs(mm(d.GetPosition().y) - old_y) < 0.05:
                    d.SetPosition(P(mm(d.GetPosition().x), new_y))
    if not any(isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == 'S' and d.GetLayer() == pcbnew.F_SilkS for d in b.GetDrawings()):
        rb = fp_of(b, 'J122').Reference().GetBoundingBox()
        if mm(rb.GetBottom()) > 71.0 and mm(rb.GetY()) < 72.8:  # J122's designator sits where the legend goes:
            auto_ref(b, 'J122', 'B')                            # it moves to the back, like other crowded ones
        missing = []
        for x, text, boxes in ((25.54, 'S', [(24.54, 71.2, 26.54, 72.6)]), (23.0, '+', [(22.0, 71.2, 24.0, 72.6)]),
                               (20.46, '-', [(19.46, 71.2, 21.46, 72.6), (20.0, 70.6, 21.9, 72.7), (19.46, 83.2, 21.9, 84.6)])):
            for box in boxes:
                try:
                    place_label(b, text, (x, 72.0), box, angles=(0,))
                    break
                except AssertionError:
                    continue
            else:
                missing.append(text)
        print('  J122 legend not placed (no room):', missing or 'none')
        try:                                                  # J123 (pull-pin): best effort, in the edge strip
            place_label(b, 'PULL', (44.9, 75.85), (43.7, 72.4, 45.6, 80.0), angles=(90,))
        except AssertionError:
            print('  J123 label: no room (optional)')


HIDDEN_REFS = ['R135', 'R134', 'J120', 'J121', 'J124', 'J125', 'R133', 'Q124', 'Q125', 'TP89', 'R144', 'R145',
               'C88', 'C140', 'C141', 'C128']


def v_refs(b):
    """E5-F7: 16 reference designators sat under part bodies (mostly the orange terminals and J1) and
    vanish after assembly. Each is re-placed at the nearest spot clear of every front-side part body,
    pad and silkscreen item; one with no free spot within 6 mm keeps its place (listed)."""
    bodies = []
    for f in b.GetFootprints():
        if f.IsFlipped():
            continue
        bb = None
        for g in f.GraphicalItems():
            if g.GetLayer() == pcbnew.F_Fab and g.GetClass() == 'PCB_SHAPE':
                if bb is None:
                    bb = g.GetBoundingBox()
                else:
                    bb.Merge(g.GetBoundingBox())
        if bb is not None:
            bodies.append(bb)
    kept = []
    for ref in HIDDEN_REFS:
        f = fp_of(b, ref)
        t = f.Reference()
        old = (t.GetPosition(), t.GetTextAngleDegrees(), t.GetLayer(), t.IsMirrored())
        obs = _silk_obstacles(b, pcbnew.F_SilkS, ref) + bodies
        cx, cy = mm(f.GetPosition().x), mm(f.GetPosition().y)
        found = False
        r = 0.0
        while r <= 6.0 and not found:
            n = max(1, int(6.283 * r / 0.4))
            for k in range(n):
                a = 6.283 * k / n
                x, y = cx + r * __import__('math').cos(a), cy + r * __import__('math').sin(a)
                for ang in (0, 90):
                    place_ref(b, ref, x, y, ang, side='F')
                    bb = t.GetBoundingBox()
                    bb.Inflate(MM(0.2))
                    if 0.5 < mm(bb.GetX()) and mm(bb.GetRight()) < 45.5 and not any(bb.Intersects(o) for o in obs):
                        found = True
                        break
                if found:
                    break
            r += 0.25
        if not found:
            t.SetPosition(old[0]); t.SetTextAngleDegrees(old[1]); t.SetLayer(old[2]); t.SetMirrored(old[3])
            kept.append(ref)
    print('  references kept under a body (no free spot within 6 mm):', kept or 'none')


# --- validation pass 2 (docs/M3_R4.md section 1c) ----------------------------------------------

PYRO_CONTROL = ('PYRO1_GATE', 'PYRO2_GATE', 'PYRO1_GATE_N', 'PYRO2_GATE_N', 'ARM1_SENSE', 'ARM2_SENSE',
                'PYRO1_CONT', 'PYRO2_CONT', 'PYRO1_COLD', 'PYRO2_COLD')


def clear_of_nets(b, xy, nets, r, gap):
    """True when a round item of radius r at xy keeps gap mm (edge to edge) from every track, via and
    pad of the listed nets, on any layer."""
    x, y = xy
    for t in b.GetTracks():
        if t.GetNetname() not in nets:
            continue
        if t.GetClass() == 'PCB_VIA':
            if math.hypot(mm(t.GetPosition().x) - x, mm(t.GetPosition().y) - y) < r + mm(t.GetWidth(pcbnew.F_Cu)) / 2 + gap:
                return False
        else:
            (sx, sy), (ex, ey) = ends(t)
            if _seg_dist(x, y, sx, sy, ex, ey) < r + mm(t.GetWidth()) / 2 + gap:
                return False
    for f in b.GetFootprints():
        for pd in f.Pads():
            if pd.GetNetname() in nets:
                bb = pd.GetBoundingBox()
                dx = max(mm(bb.GetX()) - x, 0, x - mm(bb.GetRight()))
                dy = max(mm(bb.GetY()) - y, 0, y - mm(bb.GetBottom()))
                if math.hypot(dx, dy) < r + gap:
                    return False
    return True


def w_pyro_spacing(b):
    """Actuators F2/F6, power P-3, system 3: the pyro spacing rules are now in m3.kicad_dru, so
    tools/check.sh enforces them: RAW_ACT >= 0.5 mm from every pyro gate, arm-sense, continuity and
    cold-sense net; bus, igniter and drain copper >= 0.5 mm from the gate nets and >= 0.3 mm from the
    sense nets. Pass 1's "0.5 mm on every layer" had been measured against zone fills only.
    - R144 turns 180 deg: ARM2_SENSE ran under its PYRO2_BUS pad (0.15 mm); now the sense pad faces the
      sense via and the BUS2 stub drops straight from the strap onto pad 1.
    - ARM1_SENSE's two strap-crossing vias step 0.2 mm off the BUS1 strap (0.19/0.21 -> 0.39/0.41 mm).
    - PYRO1_COLD's via steps 0.15 mm off the BUS2 strap (0.21 -> 0.36 mm), and ARM2_SENSE's via steps off
      R135's PYRO2_BUS pad (0.26 -> 0.33 mm; it was hidden behind the R144 violation).
    - PYRO1_COLD leaves R131 straight down instead of diagonally past R131's PYRO1_OUT pad (0.21 -> 0.33 mm).
    - PYRO1_CONT's In2 run moves 0.15 mm west, off J122's RAW_ACT rings (0.35 -> 0.50 mm; 0.24 mm to the
      GND rings on its other side).
    Runs before b2_servo_feed, whose stitching vias now keep the same 0.5 mm."""
    r144 = fp_of(b, 'R144')
    if abs(r144.GetOrientationDegrees()) > 1:
        return
    remove_segs(b, 'ARM2_SENSE', [((29.58, 57.35), (29.58, 57.8717)), ((29.58, 57.8717), (28.319, 57.8717)),
                                  ((28.319, 57.8717), (27.9646, 57.5173))], pcbnew.F_Cu)
    rt = r144.Reference()
    keep = (rt.GetPosition(), rt.GetTextAngleDegrees())
    r144.SetOrientationDegrees(180)
    rt.SetPosition(keep[0]); rt.SetTextAngleDegrees(keep[1])
    assert close(pad_xy(b, 'R144', '1'), (29.58, 57.35)) and close(pad_xy(b, 'R144', '2'), (28.72, 57.35))
    set_seg(b, 'PYRO2_BUS', (28.72, 57.35), (28.72, 55.46), (29.58, 57.35), (29.58, 55.46), pcbnew.F_Cu)
    # the sense via steps 0.06 mm onto an exact 45 deg B.Cu line, 0.33 mm from R135's PYRO2_BUS pad (was 0.26)
    sv = (28.025, 57.575)
    via_at(b, 'ARM2_SENSE', (27.9646, 57.5173)).SetPosition(P(*sv))
    set_seg(b, 'ARM2_SENSE', (16.35, 69.25), (27.9646, 57.5173), (16.35, 69.25), sv, pcbnew.B_Cu)
    remove_segs(b, 'ARM2_SENSE', [((27.9502, 57.5029), (27.9646, 57.5173))], pcbnew.In2_Cu)
    set_seg(b, 'ARM2_SENSE', (27.9502, 52.0062), (27.9502, 57.5029), (27.9502, 52.0062), (27.9502, 57.5), pcbnew.In2_Cu)
    track(b, 'ARM2_SENSE', pcbnew.In2_Cu, [(27.9502, 57.5), sv], 0.2)
    track(b, 'ARM2_SENSE', pcbnew.F_Cu, [(28.72, 57.35), (28.25, 57.35), sv], 0.2)
    # ARM1_SENSE: In2 hop under the BUS1 strap, vias 0.39/0.41 mm off it
    remove_segs(b, 'ARM1_SENSE', [((31.45, 59.05), (30.45, 59.05)), ((30.45, 59.05), (29.85, 58.45)),
                                  ((31.45, 62.05), (30.45, 62.05)), ((30.45, 62.05), (28.75, 63.75))], pcbnew.F_Cu)
    via_at(b, 'ARM1_SENSE', (31.45, 59.05)).SetPosition(P(31.45, 58.85))
    via_at(b, 'ARM1_SENSE', (31.45, 62.05)).SetPosition(P(31.45, 62.25))
    set_seg(b, 'ARM1_SENSE', (31.45, 62.05), (31.45, 59.05), (31.45, 62.25), (31.45, 58.85), pcbnew.In2_Cu)
    track(b, 'ARM1_SENSE', pcbnew.F_Cu, [(29.58, 58.65), (31.25, 58.65), (31.45, 58.85)], 0.2)
    track(b, 'ARM1_SENSE', pcbnew.F_Cu, [(31.45, 62.25), (30.25, 62.25), (28.75, 63.75)], 0.2)
    # PYRO1_COLD: strap-crossing via up 0.15 mm, then straight down out of R131
    # pass 3 (actuators F1): the via also keeps 0.3 mm from PYRO2_GATE_N's via (block rule G): (27.40, 53.85)
    via_at(b, 'PYRO1_COLD', (27.35, 53.95)).SetPosition(P(27.40, 53.85))
    set_seg(b, 'PYRO1_COLD', (27.35, 53.95), (27.35, 50.35), (27.40, 53.85), (27.40, 50.3), pcbnew.F_Cu)
    set_seg(b, 'PYRO1_COLD', (27.35, 50.35), (27.65, 50.05), (27.40, 50.3), (27.65, 50.05), pcbnew.F_Cu)
    # its B.Cu run shifts 0.05 mm east (0.2 mm from the RAW_PROTECTED lane) to clear the ARM2_SENSE via
    set_seg(b, 'PYRO1_COLD', (28.55, 55.15), (27.35, 53.95), (28.6, 55.05), (27.40, 53.85), pcbnew.B_Cu)
    set_seg(b, 'PYRO1_COLD', (28.55, 57.85), (28.55, 55.15), (28.6, 57.8), (28.6, 55.05), pcbnew.B_Cu)
    set_seg(b, 'PYRO1_COLD', (19.65, 66.75), (28.55, 57.85), (19.65, 66.75), (28.6, 57.8), pcbnew.B_Cu)
    remove_segs(b, 'PYRO1_COLD', [((18.13, 69.7), (17.85, 70.05)), ((17.85, 70.05), (17.85, 70.15)),
                                  ((17.85, 70.15), (17.55, 70.45)), ((17.55, 70.45), (17.25, 70.45)),
                                  ((17.25, 70.45), (17.15, 70.55))], pcbnew.F_Cu)
    track(b, 'PYRO1_COLD', pcbnew.F_Cu, [(18.13, 69.7), (18.13, 70.4), (17.3, 70.4), (17.15, 70.55)], 0.2)
    # PYRO1_CONT on In2: x 21.75 -> 21.6 between J122's GND and RAW columns
    set_seg(b, 'PYRO1_CONT', (21.75, 68.95), (20.78, 67.9783), (21.6, 68.7983), (20.78, 67.9783), pcbnew.In2_Cu)
    set_seg(b, 'PYRO1_CONT', (21.75, 91.15), (21.75, 68.95), (21.6, 91.3), (21.6, 68.7983), pcbnew.In2_Cu)
    set_seg(b, 'PYRO1_CONT', (21.35, 91.55), (21.75, 91.15), (21.35, 91.55), (21.6, 91.3), pcbnew.In2_Cu)
    w_gate_block(b)
    w_r124_turn(b)


def w_gate_block(b):
    """Pass 3 (actuators F1): inside the pyro block the gate nets now keep 0.3 mm from every other live net (rule G
    in m3.kicad_dru, scoped to the PYRO_BLOCK rule area added here); a cold-node or 3V3 bridge to a gate fires a
    channel once armed. The block is the pyro parts' area (y 42-72.4). Moved: PYRO2_GATE_N's via to (26.6, 53.42)
    with its In2 run on x 26.6 (0.31 mm from PYRO1_COLD's via, 0.32 mm from the In2 RAW_ACT_SENSE run, 0.74 mm from
    the BUS2 strap); PYRO1_GATE_N's via 0.28 mm down its own 45 deg line (0.40 mm from the In2 PYRO2_CONT run, was
    0.20). Outside the block the gate lines keep the default 0.15 mm: at y 74 a 3V3 via sits 0.17 mm from the In2
    PYRO1_GATE_N run, boxed in by ARM2_SENSE and LOGIC_SOURCE_ST, and at the MCU the 0.5 mm pin pitch sets the
    spacing (docs/M3_R4.md section 2)."""
    remove_segs(b, 'PYRO2_GATE_N', [((25.95, 52.5), (26.7, 53.25)), ((25.55, 53.25), (26.7, 53.25)),
                                    ((24.65, 52.35), (25.55, 53.25)), ((25.95, 52.35), (25.95, 52.5))], pcbnew.F_Cu)
    via_at(b, 'PYRO2_GATE_N', (26.7, 53.25)).SetPosition(P(26.6, 53.42))
    track(b, 'PYRO2_GATE_N', pcbnew.F_Cu, [(25.95, 52.35), (25.95, 52.77), (26.6, 53.42)], 0.2)      # from R138.1
    track(b, 'PYRO2_GATE_N', pcbnew.F_Cu, [(24.65, 52.35), (25.72, 53.42), (26.6, 53.42)], 0.2)      # from R139.1
    set_seg(b, 'PYRO2_GATE_N', (26.7, 53.25), (26.7, 59.2), (26.6, 53.42), (26.6, 59.1), pcbnew.In2_Cu)
    set_seg(b, 'PYRO2_GATE_N', (26.7, 59.2), (36.95, 69.45), (26.6, 59.1), (36.95, 69.45), pcbnew.In2_Cu)
    via_at(b, 'PYRO1_GATE_N', (18.65, 72.65)).SetPosition(P(18.45, 72.85))
    set_seg(b, 'PYRO1_GATE_N', (23.05, 68.25), (18.65, 72.65), (23.05, 68.25), (18.45, 72.85), pcbnew.B_Cu)
    set_seg(b, 'PYRO1_GATE_N', (8.35, 82.95), (18.65, 72.65), (8.35, 82.95), (18.45, 72.85), pcbnew.In2_Cu)
    for netname, xy in (('PYRO2_GATE_N', (26.6, 53.42)), ('PYRO1_GATE_N', (18.45, 72.85))):
        assert via_clear(b, xy, netname), (netname, xy)
    z = pcbnew.ZONE(b)                                   # named area only: rule G's condition, no keep-out
    z.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    for layer in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        ls.AddLayer(layer)
    z.SetLayerSet(ls)
    for fn in ('SetDoNotAllowTracks', 'SetDoNotAllowVias', 'SetDoNotAllowZoneFills', 'SetDoNotAllowPads', 'SetDoNotAllowFootprints'):
        getattr(z, fn)(False)
    z.SetZoneName('PYRO_BLOCK')
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((12.0, 42.0), (42.0, 42.0), (42.0, 72.4), (12.0, 72.4)):
        ol.Append(MM(x), MM(y))
    b.Add(z)


def w_r124_turn(b):
    """Pass 3 (sensors note 5): the RAW_ACT feed ran 0.15 mm past R124's bare RAW_ACT_SENSE pad on its way to pad 1;
    a bridge there puts 8.4 V on PB0 (FT_a, VDD + 4 V absolute). R124 turns 180 deg: its RAW_ACT pad now faces the
    feed, and its sense pad sits straight above R125's, 0.48 mm from RAW_ACT (rule "Pyro A2", 0.3 mm)."""
    remove_segs(b, 'RAW_ACT', [((34.317, 44.48), (33.097, 44.48)), ((33.097, 44.48), (32.77, 44.807)),
                               ((32.77, 44.807), (32.77, 45.0))], pcbnew.F_Cu)
    remove_segs(b, 'RAW_ACT_SENSE', [((33.63, 45.0), (33.63, 45.522)), ((33.63, 45.522), (33.027, 45.522)),
                                     ((33.027, 45.522), (32.77, 45.778))], pcbnew.F_Cu)
    r = fp_of(b, 'R124')
    rt = r.Reference()
    keep = (rt.GetPosition(), rt.GetTextAngleDegrees())
    r.SetOrientationDegrees(180)
    rt.SetPosition(keep[0]); rt.SetTextAngleDegrees(keep[1])
    assert close(pad_xy(b, 'R124', '1'), (33.63, 45.0)) and close(pad_xy(b, 'R124', '2'), (32.77, 45.0))
    set_seg(b, 'RAW_ACT', (34.317, 47.542), (34.317, 44.48), (34.317, 47.542), (34.317, 45.0), pcbnew.F_Cu)
    track(b, 'RAW_ACT', pcbnew.F_Cu, [(34.317, 45.0), (33.63, 45.0)], 0.2)
    track(b, 'RAW_ACT_SENSE', pcbnew.F_Cu, [(32.77, 45.0), (32.77, 45.778)], 0.2)


def w_input_damper(b):
    """Power P-1 (pass 2) and F-1/F-2/F-3 (pass 3), same change as r4_sch.w_input_damper: C80 + C96 (2 x 10 uF) at
    the input and the RC damper C89 + C95 (2 x 22 uF 1206) + R166 (0.33 ohm 2512) across BAT_IN, stacked in the free
    strip on the left edge below D8 (the aft M3 hole's washer circle, r 3.5 mm, ends at y 7.5; the BAT_IN vias that
    feed Q120 start at y 38). Each BAT_IN pad drops into the In2 BAT_IN plane through its own via; R166's and C96's
    GND pads share vias to In1. BAT_DAMP joins both capacitors straight down into R166's upper pad on F.Cu."""
    if b.FindFootprintByReference('C89'):
        return
    _set_fields(fp_of(b, 'C80'), '10uF 50V X5R 10%', {'LCSC': 'C13585', 'LCSC Part': 'C13585',
                                                       'Manufacturer': 'Samsung Electro-Mechanics', 'Manufacturer Part': 'CL31A106KBHNNNE'})
    n = pcbnew.NETINFO_ITEM(b, 'BAT_DAMP')
    b.Add(n)
    cd = {'LCSC': 'C12891', 'LCSC Part': 'C12891', 'Manufacturer': 'Samsung Electro-Mechanics', 'Manufacturer Part': 'CL31A226KAHNNNE'}
    for ref, x in (('C89', 1.85), ('C95', 4.25)):
        add_fp(b, 'C_1206_3216Metric', ref, '22uF 25V X5R 10%', cd, 'battery_entry', (x, 18.9), 270, {'1': 'BAT_IN', '2': 'BAT_DAMP'})
    add_fp(b, 'R2512', 'R166', '0.33R 1% 2512', {'LCSC': 'C25468', 'LCSC Part': 'C25468', 'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)',
           'Manufacturer Part': '25121WF330LT4E'}, 'battery_entry', (3.0, 25.45), 270, {'1': 'BAT_DAMP', '2': 'GND'})
    add_fp(b, 'C_1206_3216Metric', 'C96', '10uF 50V X5R 10%', {'LCSC': 'C13585', 'LCSC Part': 'C13585', 'Manufacturer': 'Samsung Electro-Mechanics',
           'Manufacturer Part': 'CL31A106KBHNNNE'}, 'battery_entry', (3.0, 32.2), 90, {'1': 'BAT_IN', '2': 'GND'})
    want = {('C89', '1'): (1.85, 17.425), ('C89', '2'): (1.85, 20.375), ('C95', '1'): (4.25, 17.425), ('C95', '2'): (4.25, 20.375),
            ('R166', '1'): (3.0, 22.875), ('R166', '2'): (3.0, 28.025), ('C96', '1'): (3.0, 33.675), ('C96', '2'): (3.0, 30.725)}
    for (ref, num), xy in want.items():
        assert close(pad_xy(b, ref, num), xy), (ref, num, pad_xy(b, ref, num))
    # a B.Cu BAT_FAULT_N run crosses the strip diagonally (x 3.2 at y 29.7): the GND vias sit beside the pads
    vias = [('BAT_IN', (1.85, 16.2)), ('BAT_IN', (4.25, 16.2)), ('GND', (5.45, 28.025)), ('GND', (4.6, 30.725)), ('BAT_IN', (3.0, 34.95))]
    for netname, xy in vias:
        assert via_clear(b, xy, netname, gap=0.2), (netname, xy)
        via(b, netname, xy)
    for x in (1.85, 4.25):
        track(b, 'BAT_IN', pcbnew.F_Cu, [(x, 17.425), (x, 16.2)], 0.6)
        track(b, 'BAT_DAMP', pcbnew.F_Cu, [(x, 20.375), (x, 22.875)], 0.8)
    track(b, 'GND', pcbnew.F_Cu, [(3.0, 28.025), (3.0, 30.725)], 0.8)
    track(b, 'GND', pcbnew.F_Cu, [(3.0, 28.025), (5.45, 28.025)], 0.8)
    track(b, 'GND', pcbnew.F_Cu, [(3.0, 30.725), (4.6, 30.725)], 0.8)
    track(b, 'BAT_IN', pcbnew.F_Cu, [(3.0, 33.675), (3.0, 34.95)], 0.6)
    for ref in ('C89', 'C95', 'R166', 'C96', 'TP84', 'R89'):    # TP84's and R89's designators sat where the damper is
        try:
            auto_ref(b, ref, 'F')
        except AssertionError:
            auto_ref(b, ref, 'B')                             # crowded: the board keeps such references on the back


def w_part_values(b):
    """Same part changes as r4_sch.w_usb_ov, w_100n_basic, w_10k_basic, w_pyro_drain_caps and w_u8 (no copper
    change)."""
    for ref in ('R75', 'R76', 'R78', 'R88', 'R89', 'R90', 'R91', 'R92', 'R102'):
        _set_fields(fp_of(b, ref), '10k 1%', {'LCSC': 'C25804', 'LCSC Part': 'C25804', 'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)',
                                               'Manufacturer Part': '0603WAF1002T5E'})
    _set_fields(fp_of(b, 'R87'), '47k 1%', {'LCSC': 'C25819', 'LCSC Part': 'C25819', 'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)',
                                            'Manufacturer Part': '0603WAF4702T5E'})
    for ref in ('C71', 'C74', 'C83', 'C90', 'C93'):
        _set_fields(fp_of(b, ref), '100nF 50V X7R 10%', {'LCSC': 'C14663', 'LCSC Part': 'C14663', 'Manufacturer': 'YAGEO',
                                                          'Manufacturer Part': 'CC0603KRX7R9BB104'})
    for ref in ('C128', 'C140'):
        _set_fields(fp_of(b, ref), '100nF 50V X7R 10%', {'LCSC': 'C161115', 'LCSC Part': 'C161115', 'Manufacturer': 'Murata',
                                                          'Manufacturer Part': 'GCJ188R71H104KA12D'})
    _set_fields(fp_of(b, 'U8'), 'AP63301WU-7', {'LCSC': 'C2158003', 'LCSC Part': 'C2158003', 'Manufacturer': 'Diodes Incorporated',
                                                'Manufacturer Part': 'AP63301WU-7'})        # pass 3: the old MPN reached the BOM


def w_ms5611_scl(b):
    """Sensors note: I2C1_SCL reached U5 pad 8 through the package end, 0.1-0.3 mm inside the body outline.
    It now enters pad 8's outer end (y 159.0-159.55, outside the body) from the west, clear of the body."""
    if not _has_seg(b, 'I2C1_SCL', (36.3, 161.1), (36.3, 160.2)):
        return
    remove_segs(b, 'I2C1_SCL', [((36.3, 161.1), (36.3, 160.2)), ((36.3, 160.2), (36.6, 159.75)),
                                ((36.6, 159.75), (36.82, 159.75))], pcbnew.F_Cu)
    track(b, 'I2C1_SCL', pcbnew.F_Cu, [(36.3, 161.1), (36.3, 159.5), (36.5, 159.3), (37.12, 159.3)], 0.25)


def w_route_hygiene(b):
    """Sensors note, AGENTS.md routing rule: the PULLPIN 0.1 mm staircase off U1 pin 8 becomes one 45 deg run
    (0.17 mm from the GND via, 0.22 mm from pin 9); VLOGIC_SENSE's 0.1 mm jogs at R61 become straight and
    45 deg runs."""
    if not _has_seg(b, 'PULLPIN', (25.65, 157.55), (25.65, 157.45)):
        return
    remove_segs(b, 'PULLPIN', [((25.5, 158.45), (25.55, 157.55)), ((25.55, 157.55), (25.65, 157.55)),
                               ((25.65, 157.55), (25.65, 157.45)), ((25.65, 157.45), (25.75, 157.45)),
                               ((25.75, 157.45), (25.75, 157.35)), ((25.75, 157.35), (25.85, 157.35)),
                               ((25.85, 157.35), (25.85, 157.25)), ((25.85, 157.25), (25.95, 157.15))], pcbnew.F_Cu)
    track(b, 'PULLPIN', pcbnew.F_Cu, [(25.5, 158.45), (25.5, 157.6), (25.95, 157.15)], 0.2)
    remove_segs(b, 'VLOGIC_SENSE', [((19.6, 149.5), (19.7, 149.6)), ((19.7, 149.6), (19.7, 149.7)),
                                    ((20.2, 150.1), (20.2, 150.3)), ((20.2, 150.3), (20.3, 150.4)),
                                    ((20.3, 150.4), (20.3, 150.5)), ((20.3, 150.5), (20.4, 150.6)),
                                    ((20.4, 150.6), (20.8, 150.6)), ((20.8, 150.6), (22.1, 151.1))], pcbnew.F_Cu)
    track(b, 'VLOGIC_SENSE', pcbnew.F_Cu, [(19.6, 149.5), (19.85, 149.75)], 0.25)
    track(b, 'VLOGIC_SENSE', pcbnew.F_Cu, [(20.0, 150.2), (20.0, 150.6), (21.6, 150.6), (22.1, 151.1)], 0.25)


def x_r166_land(b):
    """Power F-7 (pass 4), same change as r4_sch.x_input_bleed: R166 moves from the Bourns CRM2512 land to
    UNI-ROYAL's (rocket:M3_R2512_UR, 8.2 mm overall). Same centre, so the BAT_DAMP and GND track ends
    (2.575 mm from the centre) stay inside the new pads (2.5-4.1 mm); C89/C95 move 0.2 mm aft, with their
    track ends, so the longer courtyard clears theirs."""
    f = fp_of(b, 'R166')
    if str(f.GetFPID().GetLibItemName()) == 'M3_R2512_UR':
        return
    f.SetFPID(pcbnew.LIB_ID('rocket', 'M3_R2512_UR'))
    refresh_from_lib(b, 'R166')
    for ref in ('C89', 'C95'):
        move_fp_with_tracks(b, ref, dy=-0.2)
    for (ref, num), xy in {('R166', '1'): (3.0, 22.15), ('R166', '2'): (3.0, 28.75),
                           ('C89', '2'): (1.85, 20.175), ('C95', '2'): (4.25, 20.175)}.items():
        assert close(pad_xy(b, ref, num), xy), (ref, num, pad_xy(b, ref, num))
    # designators on the back, under each part (the board's rule for crowded references): on the front C89/C95
    # found room only 3-5 mm away, above C89, and R166's sat under its own body
    for ref, x, y in (('C89', 1.85, 18.7), ('C95', 4.25, 18.7), ('R166', 3.0, 25.45)):
        place_ref(b, ref, x, y, 90, side='B')


def x_input_bleed(b):
    """Power F-1 (pass 4), same change as r4_sch.x_input_bleed: R167 10k from BAT_IN to GND, beside TP80's BAT_IN
    run (x 8.4) between J1's courtyard and D8's (D8's designator holds the other side). Pad 1 joins the run, pad 2
    sits in the F.Cu GND pour (SMD pads connect solid)."""
    if b.FindFootprintByReference('R167'):
        return
    fields = {'LCSC': 'C25804', 'LCSC Part': 'C25804', 'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0603WAF1002T5E'}
    add_fp(b, 'R_0603_1608Metric', 'R167', '10k 1%', fields, 'battery_entry', (10.15, 10.6), 0, {'1': 'BAT_IN', '2': 'GND'})
    assert close(pad_xy(b, 'R167', '1'), (9.325, 10.6)) and close(pad_xy(b, 'R167', '2'), (10.975, 10.6))
    assert _has_seg(b, 'BAT_IN', (8.4, 9.2), (8.4, 12.9))
    remove_segs(b, 'BAT_IN', [((8.4, 9.2), (8.4, 12.9))], pcbnew.F_Cu)
    track(b, 'BAT_IN', pcbnew.F_Cu, [(8.4, 9.2), (8.4, 10.6), (8.4, 12.9)], 0.3)
    track(b, 'BAT_IN', pcbnew.F_Cu, [(8.4, 10.6), (9.325, 10.6)], 0.3)
    place_ref(b, 'R167', 10.15, 10.6, 0, side='B')           # on the front the only room was half under J1's body


TOOLING = {'TH1': (9.7, 1.8), 'TH2': (36.0, 1.8), 'TH3': (36.3, 191.2)}


def x_tooling_holes(b):
    """DFM (pass 4): JLC's Economic PCBA requires 1.152 mm NPTH tooling holes in opposite corners and adds its own
    when the board has none. Three, each >= 1.9 mm from any track, pad or via and clear of every courtyard: both
    aft corners beside the aft M3 holes' washers and J1, and the forward right corner. Board-only footprints
    (not in the schematic, BOM or CPL)."""
    for ref, xy in TOOLING.items():
        if b.FindFootprintByReference(ref):
            continue
        f = pcbnew.FootprintLoad(LIB, 'M3_ToolingHole_JLC')
        assert f is not None
        f.SetFPID(pcbnew.LIB_ID('rocket', 'M3_ToolingHole_JLC'))
        f.SetReference(ref)
        f.SetValue('JLC tooling hole')
        b.Add(f)
        f.SetPosition(P(*xy))


def y_gate_clear_of_j9(b):
    """Actuators F2 (pass 5): PYRO1_GATE_N's In2 run (x 8.35, y 83-115) passed 0.24-0.25 mm from J9's four
    through-hole rings (CAM_5V, GND, camera UART). A bridge, or a conductive filament along the glass, from CAM_5V
    to the gate drive would fire channel 1 when the camera is switched on, which is after arming; the plug-out cold
    test cannot see it. The run moves to x 7.95: 0.65 mm from the rings (0.52 mm at the jog past pin 1), 2.2 mm
    from the M3 hole at (4, 88) and outside its washer. In2 is empty there."""
    if not _has_seg(b, 'PYRO1_GATE_N', (8.35, 82.95), (8.35, 115.05)):
        return
    remove_segs(b, 'PYRO1_GATE_N', [((18.45, 72.85), (8.35, 82.95)), ((8.35, 82.95), (8.35, 115.05)),
                                    ((8.35, 115.05), (9.25, 115.95)), ((9.25, 115.95), (9.25, 131.45))], pcbnew.In2_Cu)
    track(b, 'PYRO1_GATE_N', pcbnew.In2_Cu, [(18.45, 72.85), (7.95, 83.35), (7.95, 115.05), (9.25, 116.35), (9.25, 131.45)], 0.2)


def y_bat_sense_side(b):
    """Power (pass 5): R82.1 (the OVLO divider's top), R167 (the input bleed) and TP80 reached BAT_IN only through
    D8.1's pad, behind the 0.7 mm trace that section 2 of M3_R4 records as D8's fusible link. If D8 failed short and
    that trace opened, OVLO would go with it (R83 then holds the pin at 0 V, so a wrong 3S pack turns the board and
    the servos on), and so would the bleed and TP80, all silently. Each now drops into the In2 BAT_IN plane through its
    own via; only D8 stays behind the link."""
    if not _has_seg(b, 'BAT_IN', (8.4, 10.6), (8.4, 12.9)):
        return
    remove_segs(b, 'BAT_IN', [((8.4, 10.6), (8.4, 12.9)), ((11.8, 19.6), (10.9, 15.1))], pcbnew.F_Cu)
    assert via_clear(b, (8.4, 11.8), 'BAT_IN', gap=0.25)
    via(b, 'BAT_IN', (8.4, 11.8))
    track(b, 'BAT_IN', pcbnew.F_Cu, [(8.4, 10.6), (8.4, 11.8)], 0.3)
    if via_clear(b, (11.0, 18.8), 'BAT_IN', gap=0.25):
        via(b, 'BAT_IN', (11.0, 18.8))
        track(b, 'BAT_IN', pcbnew.F_Cu, [(11.8, 19.6), (11.0, 18.8)], 0.3)
    else:
        assert via_clear(b, (11.0, 18.4), 'BAT_IN', gap=0.25)
        via(b, 'BAT_IN', (11.0, 18.4))
        track(b, 'BAT_IN', pcbnew.F_Cu, [(11.8, 19.6), (11.0, 18.8), (11.0, 18.4)], 0.3)


def y_u5_fields(b):
    """Same fields as r4_sch.y_u5_mpn (U5's maker and part number). Pass 5's do-not-populate flags on U5 and LS120 were
    reverted in pass 6: the order moves to Standard PCBA (240 +/- 5 C reflow)."""
    f = fp_of(b, 'U5')
    _set_fields(f, f.GetValue(), {'Manufacturer': 'TE Connectivity', 'Manufacturer Part': 'MS561101BA03-50'})
    for fld in f.GetFields():
        if fld.GetName() in ('Manufacturer', 'Manufacturer Part'):
            fld.SetVisible(False)                                  # new fields come in visible on the silkscreen


def y_drop_tp124(b):
    """Same change as r4_sch.y_drop_tp124: TP124 (bare GND pad between the igniter straps) removed. It joined GND
    through the F.Cu pour only, so no track or via is left behind."""
    f = b.FindFootprintByReference('TP124')
    if f is not None:
        b.Delete(f)


# --- validation pass 9 (docs/M3_R4.md section 1j) ----------------------------------------------

def move_to_net(b, pad_ref, nets, new):
    """Every track and via of `nets` joined to pad_ref ('U1.15') through track ends and vias (no other pad is crossed)
    goes to net `new`, with the pad; returns how many items changed net."""
    ref, num = pad_ref.split('.')
    pad = next(p for p in fp_of(b, ref).Pads() if p.GetNumber() == num)
    box = pad.GetBoundingBox()
    left = [t for t in b.GetTracks() if t.GetNetname() in nets]
    pts, hit = [], []
    grew = True
    while grew:
        grew = False
        for t in list(left):
            if t.GetClass() == 'PCB_VIA':
                xy = (mm(t.GetPosition().x), mm(t.GetPosition().y))
                ok = any(close(xy, p[:2]) for p in pts)
            else:
                ok = any((pad.IsOnLayer(t.GetLayer()) and box.Contains(P(*e))) or
                         any(close(e, p[:2]) and p[2] in (None, t.GetLayer()) for p in pts) for e in ends(t))
            if ok:
                left.remove(t)
                hit.append(t)
                grew = True
                if t.GetClass() == 'PCB_VIA':
                    pts.append((*xy, None))
                else:
                    pts.extend((*e, t.GetLayer()) for e in ends(t))
    n = net(b, new)
    moved = sum(t.GetNetname() != new for t in hit)
    for t in hit:
        t.SetNet(n)
    pad.SetNet(n)
    return moved


SENSE_SERIES = {  # ref: (divider-side net, MCU pin, centre, rotation, pad 1 (divider side), MCU-side items to re-net)
    'R168': ('PYRO1_CONT', 'U1.15', (21.35, 130.90), 270, (21.35, 130.47), 11),
    'R169': ('PYRO2_CONT', 'U1.16', (17.35, 125.40), 270, (17.35, 124.97), 10),
    'R170': ('ARM1_SENSE', 'U1.33', (25.85, 150.50), 270, (25.85, 150.07), 8),
    'R171': ('ARM2_SENSE', 'U1.32', (13.40, 162.95), 0, (12.97, 162.95), 1),
    'R172': ('RAW_ACT_SENSE', 'U1.34', (10.35, 131.50), 270, (10.35, 131.07), 18),
}


def z_sense_series(b):
    """Actuators F1 (pass 9), same change as r4_sch.z_sense_series: a 4.7k 0402 (C25900) between each pyro sense divider
    and its ADC pin. ARM1 (R170) and ARM2 (R171) sit beside the MCU on their top-side escapes; PYRO1 (R168) and PYRO2
    (R169) sit mid-board on their B.Cu runs (y 125-131), the nearest free top-side room (Y1, C60, C13 and C21 fill the
    space at PC0/PC1; R168 sits between SERVO4_MCU's diagonal and SW_NODE). The copper from each resistor to its pin
    becomes the *_MCU net; the divider side keeps its name, so the pyro spacing rules still cover all of it. ARM2's In2
    run now surfaces at (12.25, 162.95), and one GND stitching via beside pin 32, with its dangling stub, makes room
    for R171. R172 (pass 10) sits on PB0's straight F.Cu run at x 10.35 (y 127.6-136), with no new via."""
    if b.FindFootprintByReference('R168'):
        return
    F, B, I2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu
    for _, (tap, *_r) in SENSE_SERIES.items():
        b.Add(pcbnew.NETINFO_ITEM(b, tap + '_MCU'))
    # PYRO1: the B.Cu run (x 21.35) surfaces through R168 between vias at y 129.6 and 132.2
    set_seg(b, 'PYRO1_CONT', (21.35, 144.25), (21.35, 124.15), (21.35, 144.25), (21.35, 132.2), B)
    track(b, 'PYRO1_CONT', B, [(21.35, 124.15), (21.35, 129.6)], 0.2)
    via(b, 'PYRO1_CONT', (21.35, 129.6))
    via(b, 'PYRO1_CONT_MCU', (21.35, 132.2))
    track(b, 'PYRO1_CONT', F, [(21.35, 129.6), (21.35, 130.47)], 0.2)
    track(b, 'PYRO1_CONT_MCU', F, [(21.35, 131.33), (21.35, 132.2)], 0.2)
    # PYRO2: likewise from the via at (17.35, 124.15); B.Cu restarts at (17.55, 127.3), clear of the GND via (18.0, 126.5)
    remove_segs(b, 'PYRO2_CONT', [((17.35, 124.15), (17.35, 126.75)), ((17.35, 126.75), (17.55, 126.95))], B)
    set_seg(b, 'PYRO2_CONT', (17.55, 126.95), (17.55, 143.15), (17.55, 127.3), (17.55, 143.15), B)
    via(b, 'PYRO2_CONT_MCU', (17.55, 127.3))
    track(b, 'PYRO2_CONT', F, [(17.35, 124.15), (17.35, 124.97)], 0.2)
    track(b, 'PYRO2_CONT_MCU', F, [(17.35, 125.83), (17.35, 127.1), (17.55, 127.3)], 0.2)
    # ARM1: R170 on the F.Cu escape below its B.Cu -> F.Cu via (25.85, 149.25); the diagonal keeps its line
    remove_segs(b, 'ARM1_SENSE', [((25.85, 150.75), (25.85, 149.25))], F)
    set_seg(b, 'ARM1_SENSE', (31.05, 155.95), (25.85, 150.75), (31.05, 155.95), (26.03, 150.93), F)
    track(b, 'ARM1_SENSE', F, [(25.85, 149.25), (25.85, 150.07)], 0.2)
    track(b, 'ARM1_SENSE_MCU', F, [(25.85, 150.93), (26.03, 150.93)], 0.2)
    # ARM2: R171 beside pin 32
    b.Delete(via_at(b, 'GND', (13.3, 162.8)))
    remove_segs(b, 'GND', [((12.43, 162.8), (13.3, 162.8))], F)
    remove_segs(b, 'ARM2_SENSE', [((11.85, 162.55), (12.35, 162.55)), ((12.35, 162.55), (12.75, 162.15)),
                                  ((12.75, 162.15), (13.55, 162.15)), ((13.55, 162.15), (13.95, 162.55)),
                                  ((13.95, 162.55), (13.95, 163.05)), ((13.95, 163.05), (14.05, 163.15))], I2)
    remove_segs(b, 'ARM2_SENSE', [((14.25, 162.95), (14.05, 163.15))], F)
    b.Delete(via_at(b, 'ARM2_SENSE', (14.05, 163.15)))
    set_seg(b, 'ARM2_SENSE', (11.85, 162.55), (8.65, 159.35), (12.25, 162.95), (8.65, 159.35), I2)   # one straight run
    via(b, 'ARM2_SENSE', (12.25, 162.95))
    track(b, 'ARM2_SENSE', F, [(12.25, 162.95), (12.97, 162.95)], 0.2)
    track(b, 'ARM2_SENSE_MCU', F, [(13.83, 162.95), (14.25, 162.95)], 0.2)
    # RAW_ACT_SENSE (pass 10): R172 on PB0's F.Cu run at x 10.35
    set_seg(b, 'RAW_ACT_SENSE', (10.35, 135.95), (10.35, 127.55), (10.35, 131.07), (10.35, 127.55), F)
    track(b, 'RAW_ACT_SENSE_MCU', F, [(10.35, 131.93), (10.35, 135.95)], 0.2)
    for ref, (tap, pin, pos, rot, p1, n_mcu) in SENSE_SERIES.items():
        add_fp(b, 'R0402', ref, '4.7k', {'LCSC': 'C25900'}, 'mcu', pos, rot, {'1': tap, '2': tap + '_MCU'})
        assert close(pad_xy(b, ref, '1'), p1), (ref, pad_xy(b, ref, '1'))
        moved = move_to_net(b, pin, (tap, tap + '_MCU'), tap + '_MCU')
        assert moved == n_mcu, (ref, moved)
    # the two-line board legend (x 23, y 128 / 131): its second line would sit on R168's pads, and the band below holds
    # the buck parts' designators; the block moves 3.25 mm right and 1.25 mm up, lines 2.2 mm apart
    key = lambda r: (r.GetX(), r.GetY(), r.GetWidth(), r.GetHeight())  # noqa: E731
    lines = [next(d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetText().endswith(' - DATA')),
             next(d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == 'USB / SWD - PROTOTYPE')]
    for d, y in zip(lines, (126.75, 128.95)):
        d.SetPosition(P(26.25, y))
    skip = {key(d.GetBoundingBox()) for d in lines} | {key(fp_of(b, r).Reference().GetBoundingBox()) for r in SENSE_SERIES}
    obs = [o for o in _silk_obstacles(b, pcbnew.F_SilkS, None) if key(o) not in skip]
    for d in lines:
        bb = d.GetBoundingBox()
        bb.Inflate(MM(0.2))
        assert not any(bb.Intersects(o) for o in obs), d.GetText()
    pads = [p.GetBoundingBox() for r in SENSE_SERIES for p in fp_of(b, r).Pads()]
    for f in b.GetFootprints():          # a designator the new parts cover (C25's sat above it) goes under its own part
        if f.GetReference() not in SENSE_SERIES and f.Reference().IsVisible() and \
                any(f.Reference().GetBoundingBox().Intersects(p) for p in pads):
            auto_ref(b, f.GetReference(), 'B')
    for ref in SENSE_SERIES:
        try:
            auto_ref(b, ref, 'F')
        except AssertionError:
            auto_ref(b, ref, 'B')                                # crowded: the board keeps such references on the back


BOOT0_KEEP = [((30.55, 163.0), (31.4, 163.0)), ((31.4, 163.0), (32.9, 164.5)), ((32.9, 164.5), (33.35, 164.5))]


def z_j2_no_boot0(b):
    """Sensors F-A (pass 9), same change as r4_sch.z_j2_no_boot0: BOOT0 ends at R5 (U1.94 -> R5.1). The run on to J2.6
    (F.Cu under J2's base beside J2.4/J2.5, a B.Cu crossing under the IMU and four vias) goes, and J2.6 is unconnected.
    Pass 10: the 0.02 mm stub at R5.1 goes too (the run ends inside the pad), and J2's description loses BOOT0."""
    j2 = fp_of(b, 'J2')
    p6 = next(p for p in j2.Pads() if p.GetNumber() == '6')
    if p6.GetNetname() != 'BOOT0':
        return
    for a, c in BOOT0_KEEP:
        seg_at(b, 'BOOT0', a, c, pcbnew.F_Cu)                    # asserts the U1.94 -> R5.1 run is as expected

    def kept(t):
        if t.GetClass() == 'PCB_VIA':
            return False
        s, e = ends(t)
        return any((close(s, a) and close(e, c)) or (close(s, c) and close(e, a)) for a, c in BOOT0_KEEP)
    gone = [t for t in b.GetTracks() if t.GetNetname() == 'BOOT0' and not kept(t)]
    assert len(gone) == 20 and sum(t.GetClass() == 'PCB_VIA' for t in gone) == 4, len(gone)
    for t in gone:
        b.Delete(t)
    n = pcbnew.NETINFO_ITEM(b, 'unconnected-(J2-Pin_6-Pad6)')
    b.Add(n)
    p6.SetNet(n)
    j2.SetValue('SWD 1x6')
    j2.SetLibDescription('SWD 1x6; Pin 1 GND / 2 SWCLK / 3 SWDIO / 4 NRST / 5 3V3 / 6 not connected (R4: BOOT0 stays on R5)')


SILK_TIDY = [('C21', 19.45, 156.56, 0), ('C93', 13.8, 155.0, 90), ('C18', 28.34, 155.6, 90)]


def z_silk_tidy(b):
    """Pass 10 (silkscreen): after pass 9 sent C25's, Y1's and C14's designators to the bottom, "C18" and "C93" sat nearer
    the unlabelled C25 and C14 than their own parts, and "C13" and "C21" were already 3.7 and 6.3 mm from theirs (R3
    placement). C13's goes under its part on the bottom (the board's rule for crowded references, as for C25, C14 and
    Y1); "C21" moves into the band between C21 and U1's pins (0.24 mm from both), so "C26" no longer reads as C21's;
    "C93" and "C18" move beside their own parts, into the spots "C21" and "C13" left."""
    if fp_of(b, 'C13').Reference().GetLayer() == pcbnew.B_SilkS:
        return
    auto_ref(b, 'C13', 'B')
    for ref, x, y, ang in SILK_TIDY:
        place_ref(b, ref, x, y, ang, side='F')
        bb = fp_of(b, ref).Reference().GetBoundingBox()
        bb.Inflate(MM(0.2))
        assert not any(bb.Intersects(o) for o in _silk_obstacles(b, pcbnew.F_SilkS, ref)), ref


# --- validation pass 11 (docs/M3_R4.md section 1l) ---------------------------------------------

SPLIT_NEW = {  # new half: (sheet, centre, rotation, pad 1 net, pad 2 net)
    'R173': ('pyro', (15.85, 69.05), 0, 'PYRO1_OUT', 'PYRO1_CONT_MID'),
    'R174': ('pyro', (15.85, 46.95), 0, 'PYRO2_OUT', 'PYRO2_CONT_MID'),
    'R175': ('pyro', (29.30, 58.48), 0, 'ARM1_SENSE_MID', 'ARM1_SENSE'),
    'R176': ('pyro', (29.30, 57.54), 180, 'ARM2_SENSE_MID', 'ARM2_SENSE'),
    'R177': ('actuator_power', (34.60, 46.30), 90, 'RAW_ACT', 'RAW_ACT_SENSE_MID'),
}
SPLIT_RENET = {('R129', '1'): 'PYRO1_CONT_MID', ('R141', '1'): 'PYRO2_CONT_MID', ('R132', '2'): 'ARM1_SENSE_MID',
               ('R144', '2'): 'ARM2_SENSE_MID', ('R124', '1'): 'RAW_ACT_SENSE_MID'}


def z_split_tops(b):
    """Pass 11, same change as r4_sch.z_split_pyro/z_split_raw: every sense divider's 10k top becomes two 5.1k 0402s
    (C25905) in series, so no single shorted resistor can lift an ADC node above 1.4 V (3.3 V at the 19.9 V clamp).
    PYRO1/PYRO2: the drain no longer runs down through the old top resistor's pad; it leaves the drain bar at x 15.42,
    through the new half (R173/R174, clear of the igniter terminals' courtyards), on to the cold pull-up (R131/R143).
    ARM2's via steps from (16.35, 69.25) to (16.35, 70.75) to let PYRO1's drain pass. ARM1/ARM2: the four halves stack in
    the gap between the bus bars, which narrow from 2.0 to 1.0 mm on their inner edge (the fire current needs about
    0.5 mm; their outer edges, and so rule E's ARM-break spacing, do not move): rows R144 (bus 2 / mid), R176 (sense 2 /
    mid), R175 (mid / sense 1), R132 (mid / bus 1). RAW_ACT_SENSE: R177 on R124's RAW_ACT feed.
    Pass 12 (reviewer F1/nits): a bus pad faced its own channel's sense pad 0.40 mm away in the stack, so one solder bridge
    bypassed both halves; with 1.0 mm bars those two gaps are 0.94 mm (the rows that face across channels stay 0.40 mm).
    R173/R174 sit 0.35-0.40 mm further from the orange terminals' free end faces, clear of a 0.6 mm dovetail tongue on either
    end; PYRO1's drain branch runs at y 69.85 to keep rule C's 0.3 mm from R173's midpoint pad."""
    if b.FindFootprintByReference('R173'):
        return
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    for n in ('PYRO1_CONT_MID', 'PYRO2_CONT_MID', 'ARM1_SENSE_MID', 'ARM2_SENSE_MID', 'RAW_ACT_SENSE_MID'):
        b.Add(pcbnew.NETINFO_ITEM(b, n))
    for ref in ('R129', 'R141', 'R132', 'R144', 'R124'):
        f = fp_of(b, ref)
        _set_fields(f, '5.1k', {'LCSC': 'C25905', 'LCSC Part': 'C25905'})   # the board copies also carry 'LCSC Part'
    for (ref, num), n in SPLIT_RENET.items():
        next(p_ for p_ in fp_of(b, ref).Pads() if p_.GetNumber() == num).SetNet(net(b, n))
    # PYRO1: drain from the bar at x 15.42 through R173 to R131; ARM2's via steps down to let it pass
    remove_segs(b, 'PYRO1_OUT', [((17.27, 68.5), (17.27, 66.4)), ((17.27, 69.7), (17.27, 68.5))], F)
    track(b, 'PYRO1_OUT', F, [(15.42, 66.4), (15.42, 69.85), (17.27, 69.85)], 0.3)
    track(b, 'PYRO1_CONT_MID', F, [(16.28, 69.05), (16.6, 69.05), (17.05, 68.6)], 0.2)
    via_at(b, 'ARM2_SENSE', (16.35, 69.25)).SetPosition(P(16.35, 70.75))
    track(b, 'ARM2_SENSE', B, [(16.35, 69.25), (16.35, 70.75)], 0.2)
    set_seg(b, 'ARM2_SENSE', (16.35, 73.35), (16.35, 69.25), (16.35, 73.35), (16.35, 70.75), F)
    # PYRO2: the same through R174 to R143
    remove_segs(b, 'PYRO2_OUT', [((17.27, 46.1), (17.27, 47.4)), ((17.27, 47.4), (17.27, 49.6))], F)
    track(b, 'PYRO2_OUT', F, [(17.27, 46.1), (15.42, 46.1), (15.42, 49.6)], 0.3)
    track(b, 'PYRO2_CONT_MID', F, [(16.28, 46.95), (16.6, 46.95), (17.05, 47.4)], 0.2)
    # ARM1/ARM2: narrower bars, old stubs and sense tracks out, the four-row stack in
    for netname, y_old, y_new in (('PYRO2_BUS', 55.46, 54.96), ('PYRO1_BUS', 60.54, 61.04)):
        bar = seg_at(b, netname, (26.762, y_old), (36.0, y_old), F)
        bar.SetStart(P(26.762, y_new)); bar.SetEnd(P(36.0, y_new)); bar.SetWidth(MM(1.0))
    remove_segs(b, 'PYRO2_BUS', [((29.58, 57.35), (29.58, 55.46))], F)
    remove_segs(b, 'PYRO1_BUS', [((28.72, 58.65), (28.72, 60.54))], F)
    remove_segs(b, 'ARM2_SENSE', [((28.72, 57.35), (28.25, 57.35)), ((28.25, 57.35), (28.025, 57.575))], F)
    remove_segs(b, 'ARM1_SENSE', [((29.58, 58.65), (31.25, 58.65)), ((31.25, 58.65), (31.45, 58.85))], F)
    for ref, xy, rot in (('R144', (29.30, 56.06), 0), ('R132', (29.30, 59.96), 180)):
        f = fp_of(b, ref)
        f.SetOrientationDegrees(rot)
        f.SetPosition(P(*xy))
    assert close(pad_xy(b, 'R144', '1'), (28.87, 56.06)) and close(pad_xy(b, 'R132', '1'), (29.73, 59.96))
    track(b, 'PYRO2_BUS', F, [(28.87, 56.06), (28.87, 55.2)], 0.4)
    track(b, 'PYRO1_BUS', F, [(29.73, 59.96), (29.73, 60.8)], 0.4)
    track(b, 'ARM2_SENSE_MID', F, [(29.73, 56.06), (29.73, 57.54)], 0.2)
    track(b, 'ARM1_SENSE_MID', F, [(28.87, 58.48), (28.87, 59.96)], 0.2)
    track(b, 'ARM2_SENSE', F, [(28.87, 57.54), (28.06, 57.54), (28.025, 57.575)], 0.2)
    track(b, 'ARM1_SENSE', F, [(29.73, 58.48), (31.08, 58.48), (31.45, 58.85)], 0.2)
    # RAW_ACT_SENSE: R177 on R124's RAW_ACT feed (moved to x 34.6, clear of R125's GND pad)
    remove_segs(b, 'RAW_ACT', [((34.317, 45.0), (33.63, 45.0)), ((34.317, 47.542), (34.317, 45.0)),
                               ((37.15, 50.375), (34.317, 47.542))], F)
    track(b, 'RAW_ACT', F, [(37.15, 50.375), (34.6, 47.825), (34.6, 46.73)], 0.2)
    track(b, 'RAW_ACT_SENSE_MID', F, [(34.6, 45.87), (34.6, 45.0), (33.63, 45.0)], 0.2)
    for ref, (sheet, pos, rot, n1, n2) in SPLIT_NEW.items():
        add_fp(b, 'R0402', ref, '5.1k', {'LCSC': 'C25905'}, sheet, pos, rot, {'1': n1, '2': n2})
    for ref, p1 in (('R173', (15.42, 69.05)), ('R174', (15.42, 46.95)), ('R175', (28.87, 58.48)), ('R176', (29.73, 57.54)),
                    ('R177', (34.6, 46.73))):
        assert close(pad_xy(b, ref, '1'), p1), (ref, pad_xy(b, ref, '1'))
    pads = [p_.GetBoundingBox() for r in list(SPLIT_NEW) + ['R132', 'R144'] for p_ in fp_of(b, r).Pads()]
    for f in b.GetFootprints():          # a designator the new or moved parts cover goes under its own part
        if f.GetReference() not in SPLIT_NEW and f.GetReference() not in ('R132', 'R144') and f.Reference().IsVisible() and \
                any(f.Reference().GetBoundingBox().Intersects(p_) for p_ in pads):
            auto_ref(b, f.GetReference(), 'B')
    for ref in list(SPLIT_NEW) + ['R132', 'R144']:
        if ref == 'R177':
            auto_ref(b, ref, 'F')
        else:                            # the pyro block's top side is full (terminal bodies, R134/R135): under the part
            auto_ref(b, ref, 'B')


SPLIT_BOTTOM_NEW = {  # pass 12, parallel half of each 1k bottom: (sheet, centre, rotation, node net); pad 1 node, pad 2 GND
    'R178': ('pyro', (19.60, 69.65), 0, 'PYRO1_CONT'),
    'R179': ('pyro', (15.90, 124.15), 180, 'PYRO2_CONT'),
    'R180': ('pyro', (29.15, 62.85), 0, 'ARM1_SENSE'),
    'R181': ('pyro', (29.15, 53.00), 0, 'ARM2_SENSE'),
    'R182': ('actuator_power', (33.20, 47.30), 0, 'RAW_ACT_SENSE'),
}


def z_split_bottoms(b):
    """Pass 12 (reviewer F2), same change as r4_sch.z_split_pyro/z_split_raw: each 1k bottom (R130, R142, R133, R145, R125)
    becomes two 2k in parallel (C4109), so one open part leaves the node at <= 1.38 V instead of letting it rise to the
    drain, bus or RAW_ACT. The partners sit beside the first 2k (R178, R180, R181, R182; pass 13 moves R178 under R129), except PYRO2's (R179), which has
    no room in the pyro block and sits on the same node mid-board beside R169. PYRO1: R178's GND pad takes the place of
    the stitching via (20.3, 69.55), which moves to (20.5, 69.08) between the two GND pads (clear of PYRO1_COLD's and
    PYRO1_GATE_N's B.Cu runs and the In2 PYRO1_CONT run; hole >= 0.15 mm from both pad openings). ARM1: the node now
    reaches R133 along y 62.25 and x 28.72, past R180."""
    if b.FindFootprintByReference('R178'):
        return
    F = pcbnew.F_Cu
    for ref in ('R130', 'R142', 'R133', 'R145', 'R125'):
        _set_fields(fp_of(b, ref), '2k', {'LCSC': 'C4109', 'LCSC Part': 'C4109'})
    remove_segs(b, 'GND', [((20.03, 68.5), (20.3, 68.77)), ((20.3, 68.77), (20.3, 69.55))], F)
    b.Delete(via_at(b, 'GND', (20.3, 69.55)))
    track(b, 'PYRO1_CONT', F, [(19.17, 68.5), (19.17, 69.65)], 0.2)
    track(b, 'GND', F, [(20.03, 68.5), (20.03, 69.65)], 0.25)
    assert via_clear(b, (20.5, 69.08), 'GND', gap=0.15)                    # the island's stitch to In1, between the pads
    via(b, 'GND', (20.5, 69.08))
    track(b, 'GND', F, [(20.03, 69.08), (20.5, 69.08)], 0.25)
    track(b, 'PYRO2_CONT', F, [(16.33, 124.15), (17.35, 124.15)], 0.2)
    remove_segs(b, 'ARM1_SENSE', [((31.45, 62.25), (30.25, 62.25)), ((30.25, 62.25), (28.75, 63.75)),
                                  ((28.72, 64.0), (28.75, 63.75))], F)
    track(b, 'ARM1_SENSE', F, [(31.45, 62.25), (28.72, 62.25), (28.72, 64.0)], 0.2)
    track(b, 'ARM2_SENSE', F, [(28.72, 52.0), (28.72, 53.0)], 0.2)
    track(b, 'RAW_ACT_SENSE', F, [(32.77, 46.3), (32.77, 47.3)], 0.2)
    for ref, (sheet, pos, rot, node) in SPLIT_BOTTOM_NEW.items():
        add_fp(b, 'R0402', ref, '2k', {'LCSC': 'C4109'}, sheet, pos, rot, {'1': node, '2': 'GND'})
    for ref, p1 in (('R178', (19.17, 69.65)), ('R179', (16.33, 124.15)), ('R180', (28.72, 62.85)), ('R181', (28.72, 53.0)),
                    ('R182', (32.77, 47.3))):
        assert close(pad_xy(b, ref, '1'), p1), (ref, pad_xy(b, ref, '1'))


# --- final CAD iteration: the pass-13 findings (docs/M3_R4.md section 1o) ---------------------------------------

STACK_V = {  # the four ARM halves as two single-channel columns of vertical 0402s: (centre, rotation)
    'R144': ((28.83, 56.10), 270), 'R176': ((28.83, 57.85), 270),     # channel 2: bus 2 / mid, mid / sense 2
    'R175': ((29.83, 58.15), 90), 'R132': ((29.83, 59.90), 90),       # channel 1: sense 1 / mid, mid / bus 1
}


def z_bridge_gaps(b):
    """Pass-13 review (AH1): one solder bridge between pads of different parts closer than 1.0 mm still bypassed a
    divider top (bus, drain or RAW_ACT straight onto a sense node). Every exposed bus, igniter, drain and RAW_ACT pad
    now keeps 1.0 mm from every sense and gate pad, and every divider-midpoint pad 1.0 mm from every gate pad; DRC rule H
    enforces both. ARM stack: two single-channel columns between the bus bars (channel 2 at x 28.83, channel 1 at
    x 29.83; pass 13 proved this layout on a copy), each column's bus pad at its own bar, so the stack's bus pads are
    >= 1.55 mm from its sense pads (pass 12's rows faced at 0.94 mm) and R134/R135's >= 1.18 mm. The columns face each other 0.46 mm apart (0.40 before): a
    bridge there goes through one 5.1 k half, about 1.7 V at 8.4 V; they cannot sit 1 mm apart, as R134/R135's bus pads
    and J120/J124's courtyards leave a 2.9 mm wide gap. C129 moves 0.5 mm down, off R134's bus pad
    (0.65 mm). PYRO1: the cold pull-up R131 moves beside R173 with its drain pad on the drain branch (it sat 0.72 mm
    from R129's CONT pad), so ARM2's via steps down to (16.35, 71.45); R178 moves under R129 (0.81 mm from C150's
    RAW_ACT pad) and C127 0.1 mm up (0.98 mm). PYRO2: R143 moves beside R174 (0.82 mm from R141's CONT pad), 1.5 mm
    clear of C120's ACT_GATE pad, and its COLD run loses the 0.05 mm tilt it had since R3. Pass 12's GND stub now meets a segment end, not a segment middle."""
    if fp_of(b, 'R144').GetOrientationDegrees() in (270.0, -90.0):
        return
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    # ARM stack: old rows, stubs and sense tracks out, the two columns in
    remove_segs(b, 'PYRO2_BUS', [((28.87, 56.06), (28.87, 55.2))], F)
    remove_segs(b, 'PYRO1_BUS', [((29.73, 59.96), (29.73, 60.8))], F)
    remove_segs(b, 'ARM2_SENSE_MID', [((29.73, 56.06), (29.73, 57.54))], F)
    remove_segs(b, 'ARM1_SENSE_MID', [((28.87, 58.48), (28.87, 59.96))], F)
    remove_segs(b, 'ARM2_SENSE', [((28.87, 57.54), (28.06, 57.54)), ((28.06, 57.54), (28.025, 57.575))], F)
    remove_segs(b, 'ARM1_SENSE', [((29.73, 58.48), (31.08, 58.48)), ((31.08, 58.48), (31.45, 58.85))], F)
    for ref, (xy, rot) in STACK_V.items():
        f = fp_of(b, ref)
        f.SetOrientationDegrees(rot)
        f.SetPosition(P(*xy))
    for ref, p1, p2 in (('R144', (28.83, 55.67), (28.83, 56.53)), ('R176', (28.83, 57.42), (28.83, 58.28)),
                        ('R175', (29.83, 58.58), (29.83, 57.72)), ('R132', (29.83, 60.33), (29.83, 59.47))):
        assert close(pad_xy(b, ref, '1'), p1) and close(pad_xy(b, ref, '2'), p2), (ref, pad_xy(b, ref, '1'), pad_xy(b, ref, '2'))
    track(b, 'PYRO2_BUS', F, [(28.83, 55.67), (28.83, 55.2)], 0.4)
    track(b, 'ARM2_SENSE_MID', F, [(28.83, 56.53), (28.83, 57.42)], 0.2)
    track(b, 'ARM2_SENSE', F, [(28.83, 58.28), (28.305, 58.28), (28.025, 58.0), (28.025, 57.575)], 0.2)
    track(b, 'PYRO1_BUS', F, [(29.83, 60.33), (29.83, 60.8)], 0.4)
    track(b, 'ARM1_SENSE_MID', F, [(29.83, 59.47), (29.83, 58.58)], 0.2)
    track(b, 'ARM1_SENSE', F, [(29.83, 57.72), (30.32, 57.72), (31.45, 58.85)], 0.2)
    # C129 0.5 mm down; its node track runs straight in from R133
    remove_segs(b, 'ARM1_SENSE', [((28.72, 64.0), (27.7, 64.0)), ((27.7, 64.0), (27.2, 63.5)), ((27.2, 63.5), (26.8, 63.5))], F)
    fp_of(b, 'C129').SetPosition(P(26.8, 64.7))
    assert close(pad_xy(b, 'C129', '1'), (26.8, 64.0)), pad_xy(b, 'C129', '1')
    track(b, 'ARM1_SENSE', F, [(28.72, 64.0), (26.8, 64.0)], 0.2)
    # PYRO1: R131 beside R173 on the drain branch; its COLD run passes ARM2's lowered via to the COLD via
    remove_segs(b, 'PYRO1_OUT', [((15.42, 69.85), (17.27, 69.85))], F)
    set_seg(b, 'PYRO1_OUT', (15.42, 66.4), (15.42, 69.85), (15.42, 66.4), (15.42, 70.3), F)
    remove_segs(b, 'PYRO1_COLD', [((18.13, 69.7), (18.13, 70.4)), ((18.13, 70.4), (17.3, 70.4)),
                                  ((17.3, 70.4), (17.15, 70.55)), ((17.15, 70.55), (17.15, 72.65))], F)
    fp_of(b, 'R131').SetPosition(P(15.85, 70.3))
    assert close(pad_xy(b, 'R131', '1'), (15.42, 70.3)), pad_xy(b, 'R131', '1')
    track(b, 'PYRO1_COLD', F, [(16.28, 70.3), (16.75, 70.3), (17.15, 70.7), (17.15, 72.65)], 0.2)
    via_at(b, 'ARM2_SENSE', (16.35, 70.75)).SetPosition(P(16.35, 71.45))
    set_seg(b, 'ARM2_SENSE', (16.35, 73.35), (16.35, 70.75), (16.35, 73.35), (16.35, 71.45), F)
    set_seg(b, 'ARM2_SENSE', (16.35, 69.25), (16.35, 70.75), (16.35, 69.25), (16.35, 71.45), B)
    # R178 under R129 (CONT straight down from R129.2); its GND runs to R130's, the via stub meeting a segment end
    remove_segs(b, 'PYRO1_CONT', [((19.17, 68.5), (19.17, 69.65))], F)
    remove_segs(b, 'GND', [((20.03, 68.5), (20.03, 69.65))], F)
    fp_of(b, 'R178').SetPosition(P(18.56, 69.65))
    assert close(pad_xy(b, 'R178', '1'), (18.13, 69.65)), pad_xy(b, 'R178', '1')
    track(b, 'PYRO1_CONT', F, [(18.13, 68.5), (18.13, 69.65)], 0.2)
    track(b, 'GND', F, [(20.03, 68.5), (20.03, 69.08), (20.03, 69.65), (18.99, 69.65)], 0.25)
    # C127 0.1 mm up
    fp_of(b, 'C127').SetPosition(P(22.1, 69.2))
    set_seg(b, 'PYRO1_CONT', (21.4, 69.3), (21.4, 68.598), (21.4, 69.2), (21.4, 68.598), F)
    # PYRO2: R143 beside R174, on a stub from the drain branch; its drain pad keeps 1.5 mm from C120's ACT_GATE pad
    # (pass 14: a bridge there pulls the actuator switch's gate down through the drain divider, so RAW_ACT comes on
    # with the power switch open)
    remove_segs(b, 'PYRO2_OUT', [((17.27, 46.1), (15.42, 46.1))], F)
    set_seg(b, 'PYRO2_OUT', (15.42, 46.1), (15.42, 49.6), (15.42, 45.85), (15.42, 49.6), F)
    remove_segs(b, 'PYRO2_COLD', [((18.13, 46.1), (24.45, 46.05))], F)
    fp_of(b, 'R143').SetPosition(P(16.75, 45.85))
    assert close(pad_xy(b, 'R143', '1'), (16.32, 45.85)), pad_xy(b, 'R143', '1')
    track(b, 'PYRO2_OUT', F, [(15.42, 45.85), (16.32, 45.85)], 0.3)
    track(b, 'PYRO2_COLD', F, [(17.18, 45.85), (17.7, 45.85), (17.9, 46.05), (24.45, 46.05)], 0.2)
    moved = [p_.GetBoundingBox() for r in list(STACK_V) + ['C129', 'R131', 'R178', 'C127', 'R143'] for p_ in fp_of(b, r).Pads()]
    for f in b.GetFootprints():          # a designator the moved parts now cover goes under its own part
        if f.Reference().IsVisible() and any(f.Reference().GetBoundingBox().Intersects(p_) for p_ in moved):
            auto_ref(b, f.GetReference(), 'B')


def _box_gap(a, c):
    """Edge-to-edge distance in mm between two BOX2I (0 when they touch or overlap)."""
    dx = max(mm(c.GetX()) - mm(a.GetRight()), mm(a.GetX()) - mm(c.GetRight()), 0.0)
    dy = max(mm(c.GetY()) - mm(a.GetBottom()), mm(a.GetY()) - mm(c.GetBottom()), 0.0)
    return (dx * dx + dy * dy) ** 0.5


def place_ref_clear(b, ref, sides=('F', 'B'), rmax=6.0, margin=0.15, cap=1.5):
    """Pass 12 (reviewer F4): like auto_ref, but the text also keeps clear of every via, of other parts' courtyards on the
    top side, and sits nearer its own part's pads than any other part's (by `margin`); returns the side used or None.
    Pass 14 (F4): nearness is measured from the text's box to pad edges, not centre to centre, the text may sit at most
    `cap` mm from its own pads, and the pads that count are those on the part's own side and on the label's side."""
    f = fp_of(b, ref)
    own = [p_.GetBoundingBox() for p_ in f.Pads()]
    part_cu = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
    vias = [v.GetBoundingBox() for v in b.GetTracks() if v.GetClass() == 'PCB_VIA']
    board = b.GetBoardEdgesBoundingBox()
    board.Inflate(-MM(0.3))
    cx, cy = mm(f.GetPosition().x), mm(f.GetPosition().y)
    for side in sides:
        layer = pcbnew.F_SilkS if side == 'F' else pcbnew.B_SilkS
        label_cu = pcbnew.F_Cu if side == 'F' else pcbnew.B_Cu
        others = [p_.GetBoundingBox() for g in b.GetFootprints() if g.GetReference() != ref for p_ in g.Pads()
                  if (p_.IsOnLayer(part_cu) or p_.IsOnLayer(label_cu))
                  and abs(mm(p_.GetPosition().x) - cx) < rmax + 8 and abs(mm(p_.GetPosition().y) - cy) < rmax + 8]
        obs = _silk_obstacles(b, layer, ref) + vias
        if side == 'F':
            obs += [g.GetCourtyard(pcbnew.F_CrtYd).BBox() for g in b.GetFootprints()
                    if g.GetReference() != ref and not g.IsFlipped() and g.GetCourtyard(pcbnew.F_CrtYd).OutlineCount()]
        r = 0.0
        while r <= rmax:
            n = max(1, int(6.283 * r / 0.3))
            for k in range(n):
                a = 6.283 * k / n
                x, y = cx + r * math.cos(a), cy + r * math.sin(a)
                for ang in (0, 90):
                    place_ref(b, ref, x, y, ang, side=side)
                    bb = f.Reference().GetBoundingBox()
                    if not board.Contains(bb):
                        continue
                    d_own = min(_box_gap(bb, o) for o in own)
                    if d_own > cap:
                        continue
                    near_o = [_box_gap(bb, o) for o in others if abs(mm(o.Centre().x) - x) < 6 and abs(mm(o.Centre().y) - y) < 6]
                    if near_o and d_own + margin > min(near_o):
                        continue                 # nearer (or as near) another part: ambiguous
                    bb.Inflate(MM(0.2))
                    if not any(bb.Intersects(o) for o in obs):
                        return side
            r += 0.2
    return None


PYRO_LABELS = ['R177', 'R182', 'R125', 'R124', 'C120', 'R173', 'R174', 'R129', 'R131', 'R141', 'R142', 'R143', 'R130', 'R178',
               'R133', 'R180', 'R145', 'R181', 'R179', 'R169', 'R168',
               # pass 13 (AH2): the ARM columns and the neighbours the pass-12 rule had not covered
               'R144', 'R176', 'R175', 'R132', 'R127', 'C127', 'C129', 'C138', 'C150', 'TP122', 'TP123']
UNLABELLED = []                                 # filled by z_pyro_labels, listed in docs/M3_R4.md section 2


def z_pyro_labels(b):
    """Pass 12 (reviewer F4), extended in pass 13 (AH2): the designators around the dividers. A label nearer another part
    than its own misleads more than no label, so any designator with no unambiguous spot (clear of vias and pads, nearer
    its own part) is hidden and listed (F.Fab still carries it). A bottom-side part's label stays on the bottom side."""
    UNLABELLED[:] = []
    for ref in PYRO_LABELS:
        f = fp_of(b, ref)
        f.Reference().SetVisible(True)
        if place_ref_clear(b, ref, sides=('B',) if f.IsFlipped() else ('F', 'B')) is None:
            f.Reference().SetVisible(False)
            UNLABELLED.append(ref)
    print('  designators hidden (no unambiguous spot):', UNLABELLED)


def _fab_ref(f):
    fab = pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab
    for g in f.GraphicalItems():
        if isinstance(g, pcbnew.PCB_TEXT) and g.GetText() == '${REFERENCE}' and g.GetLayer() == fab:
            return g
    return None


def z_fab_refs(b):
    """Pass 14 (F1): the assembly drawing (tools/export_fab.py) is plotted from the fab layers, so every footprint carries
    a ${REFERENCE} text there. Where the library footprint has none (connectors, test pads, ICs and some capacitors) one is
    added at the centre of the courtyard; where fab designators overlap they shrink to 0.4 mm, then 0.3 mm, so the
    designators hidden on the silkscreen can be read on the drawing."""
    added = []
    for f in b.GetFootprints():
        if _fab_ref(f) is not None:
            continue
        cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
        c = cy.BBox().Centre() if cy.OutlineCount() else f.GetPosition()
        tx = pcbnew.PCB_TEXT(f)
        tx.SetText('${REFERENCE}')
        tx.SetLayer(pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab)
        tx.SetMirrored(f.IsFlipped())
        tx.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
        tx.SetTextThickness(MM(0.12))
        tx.SetPosition(pcbnew.VECTOR2I(c.x, c.y))
        f.Add(tx)
        added.append(f.GetReference())

    def overlaps():
        bx = [(f.GetReference(), f.IsFlipped(), _fab_ref(f).GetBoundingBox()) for f in b.GetFootprints()]
        hit = set()
        for i, (r1, s1, b1) in enumerate(bx):
            for r2, s2, b2 in bx[i + 1:]:
                if s1 == s2 and b1.Intersects(b2):
                    hit.update((r1, r2))
        return hit
    for size in (0.4, 0.3):
        hit = overlaps()
        for f in b.GetFootprints():
            tx = _fab_ref(f)
            if f.GetReference() in hit and mm(tx.GetTextHeight()) > size:
                tx.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
                tx.SetTextThickness(MM(size * 0.15))
    left = sorted(overlaps())
    print(f'  fab designators added: {len(added)}; still overlapping at 0.3 mm: {left}')


def w_order_mark(b):
    """DFM (ORDERING): JLC's "specify a location" order-number option needs a JLCJLCJLCJLC placeholder on
    the silkscreen; without it the choice is JLC's placement or a paid removal. Bottom side, clear of
    every pad opening and label, and (pass 3) off every via: a drilled hole under the text loses ink.
    """
    if any(isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == 'JLCJLCJLCJLC' for d in b.GetDrawings()):
        return
    vias = [v.GetBoundingBox() for v in b.GetTracks() if v.GetClass() == 'PCB_VIA']
    x, y, ang = place_label(b, 'JLCJLCJLCJLC', (23.0, 120.0), (6.0, 96.0, 40.0, 150.0), angles=(0, 90), layer=pcbnew.B_SilkS,
                            extra=vias)
    print(f'  order-number placeholder on B.Silkscreen at ({x:.1f}, {y:.1f}), {ang} deg')


def rev_r4(b):
    """Silkscreen revision and the board title block (R3 left it empty, so the Gerber job file said
    'rev?')."""
    for d in b.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and 'M3-ASSY-R3' in d.GetText():
            d.SetText(d.GetText().replace('M3-ASSY-R3', 'M3-ASSY-R4'))
    tb = b.GetTitleBlock()
    tb.SetTitle('M3 flight computer')
    tb.SetRevision('M3-ASSY-R4')


STACKUP = '''\t\t(stackup
\t\t\t(layer "F.SilkS"
\t\t\t\t(type "Top Silk Screen")
\t\t\t)
\t\t\t(layer "F.Paste"
\t\t\t\t(type "Top Solder Paste")
\t\t\t)
\t\t\t(layer "F.Mask"
\t\t\t\t(type "Top Solder Mask")
\t\t\t\t(thickness 0.01)
\t\t\t)
\t\t\t(layer "F.Cu"
\t\t\t\t(type "copper")
\t\t\t\t(thickness 0.035)
\t\t\t)
\t\t\t(layer "dielectric 1"
\t\t\t\t(type "prepreg")
\t\t\t\t(thickness 0.2104)
\t\t\t\t(material "FR4")
\t\t\t\t(epsilon_r 4.4)
\t\t\t\t(loss_tangent 0.02)
\t\t\t)
\t\t\t(layer "In1.Cu"
\t\t\t\t(type "copper")
\t\t\t\t(thickness 0.035)
\t\t\t)
\t\t\t(layer "dielectric 2"
\t\t\t\t(type "core")
\t\t\t\t(thickness 1.0392)
\t\t\t\t(material "FR4")
\t\t\t\t(epsilon_r 4.6)
\t\t\t\t(loss_tangent 0.02)
\t\t\t)
\t\t\t(layer "In2.Cu"
\t\t\t\t(type "copper")
\t\t\t\t(thickness 0.035)
\t\t\t)
\t\t\t(layer "dielectric 3"
\t\t\t\t(type "prepreg")
\t\t\t\t(thickness 0.2104)
\t\t\t\t(material "FR4")
\t\t\t\t(epsilon_r 4.4)
\t\t\t\t(loss_tangent 0.02)
\t\t\t)
\t\t\t(layer "B.Cu"
\t\t\t\t(type "copper")
\t\t\t\t(thickness 0.035)
\t\t\t)
\t\t\t(layer "B.Mask"
\t\t\t\t(type "Bottom Solder Mask")
\t\t\t\t(thickness 0.01)
\t\t\t)
\t\t\t(layer "B.Paste"
\t\t\t\t(type "Bottom Solder Paste")
\t\t\t)
\t\t\t(layer "B.SilkS"
\t\t\t\t(type "Bottom Silk Screen")
\t\t\t)
\t\t\t(copper_finish "ENIG")
\t\t\t(dielectric_constraints no)
\t\t)
'''


def stackup_enig(path):
    """REQUIREMENTS M1 (JLC 4-layer 1.6 mm, 1 oz outer and inner, ENIG): the board had no physical
    stackup, so the Gerber job file said Finish 'None'. The pcbnew Python API does not expose the
    stackup, so the block is written into (setup) as text; copper and dielectric sum to 1.60 mm."""
    t = Path(path).read_text()
    if '(stackup' in t:
        return
    k = t.index('\t(setup\n') + len('\t(setup\n')
    Path(path).write_text(t[:k] + STACKUP + t[k:])
    print('  stackup with ENIG finish written')


STEPS = [a1_enable_ride_through, a2_ovlo_release, b4_b5_tie_hole_and_tp122, b1_usb_detect,
         b6_vias_out_of_pads, b8_3v3a_rc, a3_pyro_terminals,
         m_courtyards, m_courtyard_clearances, m_u9_input, m_thermal_reliefs, m_track_cleanup,
         v_pyro2_gate_crossing, v_input_protection, w_pyro_spacing, b2_servo_feed, m_pin1_marks, m_imu,
         v_tp123_bottom, v_mask_dams, v_camera_via, w_input_damper, w_part_values, w_ms5611_scl, w_route_hygiene,
         x_r166_land, x_input_bleed, x_tooling_holes, y_gate_clear_of_j9, y_drop_tp124, y_bat_sense_side, y_u5_fields,
         z_sense_series, z_j2_no_boot0, z_silk_tidy, v_j123_jst, v_silk, v_refs, z_split_tops, z_split_bottoms,
         z_bridge_gaps, z_pyro_labels, z_fab_refs, w_order_mark, rev_r4]


def main():
    b = pcbnew.LoadBoard(PCB)
    for s in STEPS:
        s(b)
        print('step', s.__name__)
    b.BuildConnectivity()          # the filler's island removal reads connectivity; stale data dropped a J3 GND island
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
    stackup_enig(PCB)
    print('saved', PCB)


if __name__ == '__main__':
    main()
