#!/usr/bin/env python3
"""R5 autorouting of the non-critical nets with Freerouting (docs/M3_R5.md "How R5 is built").

usage: <KiCad python3> m3_design/r5_route.py export [board] [out.dsn] [--seed=N] [--warm]   DSN for Freerouting
       <KiCad python3> m3_design/r5_route.py import [board] [in.ses]    apply a session file

The board must already carry r5_pcb.py's placement, zones and scripted (hand-specified) critical copper:
power, pyro, crystal, USB and QSPI. The export leaves out the outer-layer GND pours (Freerouting treats a
plane on a signal layer as an obstacle; those pours fill round the routes afterwards), fixes every existing
track and via (type protect) so the router cannot move the scripted copper, and keeps the In2 BAT_IN, RAW_ACT
and CAM_5V islands and the outer power pours as planes, which the router keeps out of (exported with the shape
of their fill, which already clears other nets' pads). In1 is the solid GND reference of every F.Cu trace: it is
exported as a power layer, so the router only drops vias into it and never routes on it. The In2 3V3 and 3V3A
fills are left out too: the router may use In2 there, and the fills then take the rest.
Freerouting v2.4.1 then routes what is left (signals 0.15 mm wide, supplies, GND and pyro nets 0.2 mm, the edge
and hole clearances JLC's 0.5 mm and 0.25 mm with a 20 and 10 um margin, the default clearance written as the
board's 0.15 mm plus 20 um (export), and the optimizer stage off: on this board it re-opened connections, 56
unrouted before it and 75 after):

    java -jar freerouting-2.4.1.jar -de m3_design/r5_autoroute.dsn -do m3_design/r5_autoroute.ses -mp 80 \
        --router.optimizer.enabled=false --router.automatic_neckdown=false --router.neck_width_um=150 \
        --router.copper_to_edge_clearance_um=520 --router.hole_clearance_um=260

r5_finish.py then routes the few connections the router leaves.

The session file is kept in git, so m3_design/r5_build.sh rebuilds the board without Java; the import
adds only the router's new wires and vias (the protected copper is already on the board).
"""
import math
import re
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent
POURED_AFTER = {'3V3', '3V3A'}     # In2 fills that take what the router leaves; their pins are routed
# Net classes for Freerouting, which does not read m3.kicad_dru: the pyro rules it must keep from new copper
# (rules B, D, F: bus/igniter/drain 0.5 mm from gates, GND and every other live net; rule G: gate nets 0.3 mm
# inside the block, applied here everywhere). Exactly the rule values: with a margin, pads that keep the rule
# legally would sit inside the router's clearance and could not be left. DRC checks the result with the real rules.
CLASSES = {'pyro_hv': (500, ['PYRO1_BUS', 'PYRO2_BUS', 'PYRO1_IGN', 'PYRO2_IGN', 'PYRO1_OUT', 'PYRO2_OUT']),
           'pyro_gate': (300, ['PYRO1_GATE', 'PYRO2_GATE', 'PYRO1_GATE_N', 'PYRO2_GATE_N'])}
# Track widths of the router's copper (mm). Signals 0.15 mm (JLC's 4-layer minimum is 0.09 mm; at 0.2 mm the
# middle of the board kept 13-17 connections open after the finisher); the supplies, GND and the pyro nets 0.2 mm
# (their high-current paths are scripted wider in r5_pcb.py; the router only adds branches and pad ties).
SIGNAL_W, POWER_W = 0.15, 0.2
POWER = ('GND', '3V3', '3V3A', 'VLOGIC', 'VBUS', 'USB_LIMITED', 'BAT_IN', 'BAT_DAMP', 'RAW_PROTECTED', 'RAW_ACT',
         'ACT_FET_S', 'CAM_INPUT_LIMITED', 'CAM_5V', 'CAM_IO_3V3', 'SW_NODE', 'BST', 'CAM_SW', 'CAM_BST', 'VCAP1',
         'VCAP2')


def router_width(net):
    """The width the router draws a net's tracks with (mm)."""
    return POWER_W if net in POWER or any(net in nets for _, nets in CLASSES.values()) else SIGNAL_W


CRITICAL = ('USB_DP', 'USB_DM', 'HSE_IN', 'HSE_OUT', 'QSPI_CLK', 'QSPI_NCS', 'QSPI_IO0', 'QSPI_IO1', 'QSPI_IO2',
            'QSPI_IO3', 'SPI1_SCK', 'SPI1_MOSI', 'SPI1_MISO', 'IMU_CS')


def reference_keepouts(b, margin=0.5, piece=3.5, gap=1.0):
    """In2 is the reference plane of every B.Cu trace (0.21 mm away; In1 GND serves F.Cu). Under each scripted
    B.Cu segment of a critical net (USB, HSE, QSPI, SPI1) the router may put no In2 copper, so the 3V3 fill stays
    whole beneath it (export and r5_finish.py only), except for a `gap` mm gate every `piece` mm where another
    track may cross under it at right angles (a slot of about 0.6 mm in its reference; without the gates the long
    USB, QSPI and SPI1 runs fenced In2 into pieces and 5-11 connections stayed open). Vias are kept out too:
    Freerouting reads no track-only keep-out (KiCad writes it as wire_keepout, which Freerouting skips), and within
    0.5 mm of the trace a via is excluded by its clearance anyway."""
    mm, MM = pcbnew.ToMM, pcbnew.FromMM
    n = 0
    for t in list(b.GetTracks()):
        if t.GetClass() == 'PCB_VIA' or t.GetLayer() != pcbnew.B_Cu or t.GetNetname() not in CRITICAL:
            continue
        ax, ay, cx, cy = mm(t.GetStart().x), mm(t.GetStart().y), mm(t.GetEnd().x), mm(t.GetEnd().y)
        ln = ((cx - ax) ** 2 + (cy - ay) ** 2) ** 0.5
        if ln < 1e-6:
            continue
        r = mm(t.GetWidth()) / 2 + margin
        ux, uy = (cx - ax) / ln, (cy - ay) / ln
        px, py = -uy * r, ux * r
        total = ln + 2 * r                            # the fence from -r to ln + r along the segment
        k = max(1, round((total + gap) / (piece + gap)))
        size = (total - (k - 1) * gap) / k
        for i in range(k):
            s0 = -r + i * (size + gap)
            s1 = s0 + size
            pts = [(ax + ux * s0 + px, ay + uy * s0 + py), (ax + ux * s1 + px, ay + uy * s1 + py),
                   (ax + ux * s1 - px, ay + uy * s1 - py), (ax + ux * s0 - px, ay + uy * s0 - py)]
            _rule_area(b, pts)
            n += 1
    return n


def _rule_area(b, pts):
    """A no-tracks, no-vias rule area on In2 (fills allowed)."""
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    z.SetLayer(pcbnew.In2_Cu)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowZoneFills(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    b.Add(z)


def _as_fill(b, z):
    """Replace a power pour by zones shaped like its fill, which already clears other nets' pads (U9's pins sit
    inside BAT_IN_F's outline, and the router could not reach them). Holes in a fill are dropped (it then covers
    those items on that layer only; they stay reachable on the others)."""
    MM = pcbnew.FromMM
    for lay in z.GetLayerSet().CuStack():
        fill = z.GetFilledPolysList(lay)
        for k in range(fill.OutlineCount()):
            ol = fill.Outline(k)
            if ol.PointCount() < 3:
                continue
            nz = pcbnew.ZONE(b)
            nz.SetLayer(lay)
            nz.SetNet(z.GetNet())
            nz.SetAssignedPriority(z.GetAssignedPriority())
            s = nz.Outline()
            s.NewOutline()
            for i in range(ol.PointCount()):
                s.Append(ol.CPoint(i).x, ol.CPoint(i).y)
            b.Add(nz)
    b.Delete(z)


def _keepout(b, z):
    """A keep-out (tracks and vias) shaped like a power pour's fill, holes kept (KiCad writes them as windows):
    Freerouting treats another net's plane as free space and routes through it, and the refilled pour then
    splits. The pour's nets are complete before routing (scripted), so the keep-out costs them nothing."""
    for lay in z.GetLayerSet().CuStack():
        fill = z.GetFilledPolysList(lay)
        for k in range(fill.OutlineCount()):
            ol = fill.Outline(k)
            if ol.PointCount() < 3:
                continue
            nz = pcbnew.ZONE(b)
            nz.SetIsRuleArea(True)
            nz.SetLayer(lay)
            nz.SetDoNotAllowTracks(True)
            nz.SetDoNotAllowVias(True)
            nz.SetDoNotAllowZoneFills(False)
            nz.SetDoNotAllowPads(False)
            nz.SetDoNotAllowFootprints(False)
            s = nz.Outline()
            s.NewOutline()
            for i in range(ol.PointCount()):
                s.Append(ol.CPoint(i).x, ol.CPoint(i).y)
            for h in range(fill.HoleCount(k)):
                hl = fill.Hole(k, h)
                s.NewHole()
                for i in range(hl.PointCount()):
                    s.Append(hl.CPoint(i).x, hl.CPoint(i).y, -1, h)
            b.Add(nz)


def _hole_keepouts(b, margin=0.55):
    """Freerouting keeps only its normal clearance from a hole inside the board; KiCad wants the 0.5 mm edge
    clearance from it. A keep-out disc (tracks and vias, every copper layer) margin beyond each Edge.Cuts circle."""
    n = 0
    for d in list(b.GetDrawings()):
        if d.GetLayer() != pcbnew.Edge_Cuts or d.GetShape() != pcbnew.SHAPE_T_CIRCLE:
            continue
        c, r = d.GetCenter(), d.GetRadius() + pcbnew.FromMM(margin)
        r /= math.cos(math.pi / 24)                     # the 24-gon encloses the circle
        z = pcbnew.ZONE(b)
        z.SetIsRuleArea(True)
        z.SetLayerSet(_cu4())
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowZoneFills(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        ol = z.Outline()
        ol.NewOutline()
        for k in range(24):
            a = 2 * math.pi * k / 24
            ol.Append(int(c.x + r * math.cos(a)), int(c.y + r * math.sin(a)))
        b.Add(z)
        n += 1
    return n


def _cu4():
    ls = pcbnew.LSET()
    for lay in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        ls.AddLayer(lay)
    return ls


def export(board, out, no_in2=False, seed=None, warm=False):
    b = pcbnew.LoadBoard(board)
    for z in list(b.Zones()):
        if z.GetIsRuleArea():
            if not (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias() or z.GetDoNotAllowZoneFills()):
                b.Delete(z)                  # PYRO_BLOCK names an area for DRC rule G; exported, it is a keep-out
            continue
        if z.GetNetname() in POURED_AFTER or (z.GetNetname() == 'GND' and not z.IsOnLayer(pcbnew.In1_Cu)):
            b.Delete(z)
        elif z.GetNetname() != 'GND':
            _keepout(b, z)                   # other nets stay out of the pour
            _as_fill(b, z)                   # and its own pads count as joined by it
    if not no_in2:
        print(f'  {reference_keepouts(b)} In2 keep-outs under critical B.Cu segments')
    print(f'  {_hole_keepouts(b)} hole keep-outs (0.5 mm edge clearance)')
    assert pcbnew.ExportSpecctraDSN(b, out), 'DSN export failed'
    t = Path(out).read_text()
    if not warm:                                      # warm start: the router's own (unlocked) wires stay movable
        t = t.replace('(type route)', '(type protect)')
    # signals at SIGNAL_W: the structure rule and the default class, the only width rules before _classes adds
    # the power and pyro classes at POWER_W
    t, k = re.subn(r'(\(rule\s*\(width )[\d.]+(\))', rf'\g<1>{SIGNAL_W * 1000:.0f}\g<2>', t)
    assert k == 2, ('unexpected DSN width rules', k)
    t = _classes(t)
    # the default clearance (the board's 0.15 mm, in the structure rule and the default class) plus a 20 um margin
    # for the router's approximations of round shapes; DRC checks the result at the real 0.15 mm (trial runs at
    # 0.20 mm left 5-11 connections open in the middle of the board)
    m = re.search(r'\(rule\s*\(width [\d.]+\)\s*\(clearance ([\d.]+)\)', t)
    assert m, 'no default rule in the DSN'
    assert t.count(f'(clearance {m.group(1)})') == 2, ('unexpected DSN default rules', m.group(1))
    t = t.replace(f'(clearance {m.group(1)})', '(clearance 170)')
    assert '(layer In1.Cu\n      (type signal)' in t, 'no In1 layer in the DSN'
    t = t.replace('(layer In1.Cu\n      (type signal)', '(layer In1.Cu\n      (type power)')   # GND plane: no routes
    if no_in2:                                        # In2 carries planes and the 3V3 fills: no new signals there
        t = t.replace('(layer In2.Cu\n      (type signal)', '(layer In2.Cu\n      (type power)')
    if seed is not None:
        t = _shuffle(t, seed)
    t = re.sub(r'^\(pcb "[^"]*"', f'(pcb "{Path(out).name}"', t, count=1)   # KiCad writes the absolute path
    Path(out).write_text(t)
    print('exported', out)


def _shuffle(t, seed):
    """The same board in another order: Freerouting routes in the order of the DSN's components and nets, so a
    shuffled copy (component blocks in the placement section, net blocks in the network section; the classes stay
    last) is another, equally valid attempt. The session in git names its seed (r5_build.sh)."""
    import random
    rnd = random.Random(seed)
    for head, item in (('  (placement\n', '    (component'), ('  (network\n', '    (net')):
        i = t.index(head) + len(head)
        j = t.index('\n  )\n', i)
        parts = re.split(r'(?m)^(?=' + re.escape(item) + ')', t[i:j])
        last = [q for q in parts[1:] if not q.startswith(item + ' ') or q.startswith('    (class')]
        items = [q for q in parts[1:] if q not in last]
        rnd.shuffle(items)
        t = t[:i] + parts[0] + ''.join(items) + ''.join(last) + t[j:]
    return t


def _classes(t):
    """Move the pyro and power nets out of kicad_default into their own classes (clearances above, POWER_W)."""
    m = re.search(r'\(class kicad_default(.*?)\(circuit', t, re.S)
    assert m, 'no default class in the DSN'
    names = m.group(1)
    classes = dict(CLASSES, power=(170, POWER))     # the power class at the default clearance (see export)
    for cls, (clr, nets) in classes.items():
        for n in nets:
            names, k = re.subn(r'(?<=\s)' + re.escape(n) + r'(?=\s)', '', names)
            assert k == 1, (n, k)
    t = t[:m.start(1)] + names + t[m.end(1):]
    extra = ''
    for cls, (clr, nets) in classes.items():
        extra += (f'    (class {cls} {" ".join(nets)}\n      (circuit\n        (use_via "Via[0-3]_600:300_um")\n'
                  f'      )\n      (rule\n        (width {POWER_W * 1000:.0f})\n        (clearance {clr})\n'
                  f'      )\n    )\n')
    i = t.index('  (wiring')
    j = t.rindex('  )', 0, i)                         # end of the network section
    return t[:j] + extra + t[j:]


def _seg_dist(px, py, ax, ay, cx, cy):
    dx, dy = cx - ax, cy - ay
    n = dx * dx + dy * dy
    u = 0.0 if n == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / n))
    return ((px - ax - u * dx) ** 2 + (py - ay - u * dy) ** 2) ** 0.5


def _relock(b, vias, segs, tol=2000):
    """Lock again what was the scripted copper (within 2 um: the session rounds coordinates to 0.1 um, and the
    router merges or splits collinear segments). A track counts when both ends and its middle lie on scripted
    copper of the same net, layer and width; a via when it sits on a scripted via of its net."""
    n = 0
    for t in b.GetTracks():
        if t.IsLocked():
            continue
        if t.GetClass() == 'PCB_VIA':
            q = t.GetPosition()
            ok = any(abs(q.x - x) <= tol and abs(q.y - y) <= tol for x, y in vias.get(t.GetNetname(), ()))
        else:
            ss = [s for (net, lay, w), v in segs.items() if net == t.GetNetname() and lay == t.GetLayer() and
                  abs(w - t.GetWidth()) <= 10 for s in v]
            a, c = t.GetStart(), t.GetEnd()
            ok = bool(ss) and all(any(_seg_dist(x, y, *s) <= tol for s in ss)
                                  for x, y in ((a.x, a.y), (c.x, c.y), ((a.x + c.x) / 2, (a.y + c.y) / 2)))
        if ok:
            t.SetLocked(True)
            n += 1
    return n


def import_ses(board, ses):
    """Apply a session. KiCad's import replaces every unlocked track and via by the session's (the protected
    scripted copper comes back from the session); the scripted copper is then locked, so r5_finish.py can tell it
    from the router's (unlocked), which a rip-up may move."""
    b = pcbnew.LoadBoard(board)
    before = len(b.GetTracks())
    vias, segs = {}, {}
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            vias.setdefault(t.GetNetname(), []).append((t.GetPosition().x, t.GetPosition().y))
        else:
            segs.setdefault((t.GetNetname(), t.GetLayer(), t.GetWidth()), []).append(
                (t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y))
    assert pcbnew.ImportSpecctraSES(b, ses), 'SES import failed'
    locked = _relock(b, vias, segs)
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(board, b)
    print(f'imported {ses}: {before} -> {len(b.GetTracks())} tracks and vias ({locked} scripted, locked)')


if __name__ == '__main__':
    cmd = sys.argv[1]
    pos = [x for x in sys.argv[2:] if not x.startswith('--')]
    board = pos[0] if pos else str(ROOT / 'assembly_review' / 'm3.kicad_pcb')
    if cmd == 'export':
        seed = next((int(x.split('=', 1)[1]) for x in sys.argv if x.startswith('--seed=')), None)
        export(board, pos[1] if len(pos) > 1 else str(ROOT / 'r5_autoroute.dsn'), '--no-in2' in sys.argv, seed,
               '--warm' in sys.argv)
    elif cmd == 'import':
        pcbnew.KIID.SeedGenerator(5102)   # repeatable UUIDs (r5_pcb.main)
        import_ses(board, pos[1] if len(pos) > 1 else str(ROOT / 'r5_autoroute.ses'))
    else:
        raise SystemExit(__doc__)
