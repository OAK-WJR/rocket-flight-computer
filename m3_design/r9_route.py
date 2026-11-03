#!/usr/bin/env python3
"""Build the R9 board's signal copper (M3-ASSY-R9, build step 7), one routing family per run.

usage: <KiCad python3> -I m3_design/r9_route.py FAMILY [--board m3_design/assembly_review/m3.kicad_pcb]
       design aid (r9_build.sh never passes it): --no-fill

r9_plan.md section 4 step 7; R9_DECISIONS.md D-S7-*. FAMILY is one of FAMILIES below; r9_build.sh runs them in that
order on the step-6 board, each followed by its gate (r9_route_check.py FAMILY). The board is rebuilt in place, so
the project's m3.kicad_pro and m3.kicad_dru apply while it is filled. Every number is board mm (y forward, U1 at
(18, 44.5) rotation 0; u1_pin below).

Each family is one module, m3_design/r9_route_<family>.py, written as deliberate octilinear polylines and vias from
tables (bus lanes as parallel polylines at a fixed pitch): no autorouter, nothing hand-patched. A module defines
  NETS       the nets it completes (its gate requires every pad of each joined)
  CONTINUES  (optional) the nets an earlier step started and this family finishes (step 6's PARTIAL rails)
  RAILS      the shared rails it taps (3V3, 3V3A, GND ...): its own copper only
  PENDING    (optional) its GND vias that wait for step 8's In1 / outer GND pours (r9_route_check: dangling until then)
  BUDGET     its asserted limits: signal track length, signal vias, critical layer changes, the worst copper /
             octilinear-MST ratio of a net more than route_check's slack longer than its MST (r9_route_check budget)
  PADS       the pads its tables end on, (ref, pad, net, centre): a placement change stops the build
  draw(d)    its copper, through the Draw primitives below
The last family, links, is the constrained short-link stage: each link one layer, no via, copper <= 1.3 x its
octilinear pad-to-pad distance, or the build fails.

The Draw primitives refuse non-octilinear and zero-length segments, two vias at one point, a width outside the board's
five (r9_plan section 2, X5 <= 6), and a pad that is not where (or on the net) the table assumes, so a placement change cannot
silently bend the copper. build(b, family, dry=True) records a family's copper without touching the board
(r9_route_check's template gate). Deterministic (fixed KIID seed per family): a rebuild reproduces the board byte for
byte.
"""
import argparse
import importlib
import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
PROJECT = ROOT / 'm3_design/assembly_review'
MM, mm = pcbnew.FromMM, pcbnew.ToMM
LAYER = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}
FAMILIES = ('rf_if', 'qspi_hse', 'pyro', 'servo', 'imu_baro', 'usb_swd', 'camera', 'status', 'power_ctl', 'links')
KIID_SEED = {name: 9910 + i for i, name in enumerate(FAMILIES)}       # steps 4-6 use 9904-9906
W = 0.2                                     # signal width (R8 D-plan section 4; the board's five widths, X5)
WIDTHS = (0.2, 0.25, 0.3, 0.4, 1.0)         # the board's five track widths (D-S5-08; 0.15 gone, R9P1-ROUTING-01)
VIA_SIG = (0.5, 0.3)                        # signal and GND-partner via (steps 4-6)
VIA_PWR = (0.6, 0.3)                        # rail taps (the board's default via, m3.kicad_pro)
EPS = 1e-6
U1_AT = (18.0, 44.5)                        # r9_place.tsv (D-S3-05), asserted in Draw.check_u1


def r4(v):
    return round(v, 4)


def octilinear(a, b):
    dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
    return dx < EPS or dy < EPS or abs(dx - dy) < EPS


def octile(a, b):
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


def u1_pin(n):
    """U1 pad centre (LQFP-100, rotation 0 at (18, 44.5)): pins 1-25 on the forward face west to east, 26-50 the east
    face forward to aft, 51-75 the aft face east to west, 76-100 the west face aft to forward."""
    x0, y0 = U1_AT
    if n <= 25:
        return (r4(x0 - 6.0 + 0.5 * (n - 1)), r4(y0 + 7.55))
    if n <= 50:
        return (r4(x0 + 7.55), r4(y0 + 6.0 - 0.5 * (n - 26)))
    if n <= 75:
        return (r4(x0 + 6.0 - 0.5 * (n - 51)), r4(y0 - 7.55))
    return (r4(x0 - 7.55), r4(y0 - 6.0 + 0.5 * (n - 76)))


class Draw:
    """Copper primitives for one family on a board; every item is recorded (dry=True records without adding)."""

    def __init__(self, board, family, dry=False):
        self.b = board
        self.family = family
        self.dry = dry
        self.vias = {}
        self.via_size = {}
        self.moved = []                     # (net, old position) of the vias move_via relocated
        self.tracks = []
        self.check_u1()

    def check_u1(self):
        f = self.b.FindFootprintByReference('U1')
        at = (r4(mm(f.GetPosition().x)), r4(mm(f.GetPosition().y)))
        assert math.dist(at, U1_AT) < 1e-3 and abs(f.GetOrientationDegrees()) < 1e-6 and not f.IsFlipped(), \
            f'U1 is at {at}, the tables assume {U1_AT} rotation 0 on the top'
        for n in (1, 25, 26, 50, 51, 75, 76, 100):
            self.pad('U1', str(n), at=u1_pin(n))

    def net(self, name):
        n = self.b.FindNet(name)
        assert n is not None and n.GetNetCode() > 0, f'no net {name}'
        return n

    def pad(self, ref, num, net=None, at=None):
        """A pad's centre (mm, 4 dp); asserts its net and, if given, its position (the table's assumption)."""
        f = self.b.FindFootprintByReference(ref)
        assert f is not None, ref
        pads = [p for p in f.Pads() if p.GetNumber() == str(num)]
        assert pads, f'{ref}.{num}'
        p = pads[0]
        xy = (r4(mm(p.GetPosition().x)), r4(mm(p.GetPosition().y)))
        if net is not None:
            assert p.GetNetname() == net, f'{ref}.{num} is on {p.GetNetname()}, the table assumes {net}'
        if at is not None:
            assert math.dist(xy, at) < 1e-3, f'{ref}.{num} is at {xy}, the table assumes {at}'
        return xy

    def track(self, net, layer, width, pts):
        n = self.net(net)
        assert any(abs(width - w) < EPS for w in WIDTHS), f'{net}: width {width} is not one of the board\'s {WIDTHS}'
        pts = [(r4(x), r4(y)) for x, y in pts]
        for a, c in zip(pts, pts[1:]):
            assert a != c, f'{net}: zero-length segment at {a}'
            assert octilinear(a, c), f'{net}: segment {a}-{c} is not 0 / 45 / 90 degrees'
            if not self.dry:
                t = pcbnew.PCB_TRACK(self.b)
                t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
                t.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
                t.SetWidth(MM(width))
                t.SetLayer(LAYER[layer])
                t.SetNet(n)
                self.b.Add(t)
            self.tracks.append((net, layer, width, a, c))

    def via(self, net, at, size=VIA_SIG):
        at = (r4(at[0]), r4(at[1]))
        assert at not in self.vias, f'two vias at {at}'
        n = self.net(net)
        if not self.dry:
            v = pcbnew.PCB_VIA(self.b)
            v.SetPosition(pcbnew.VECTOR2I(MM(at[0]), MM(at[1])))
            v.SetWidth(MM(size[0]))
            v.SetDrill(MM(size[1]))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNet(n)
            self.b.Add(v)
        self.vias[at] = net
        self.via_size[at] = size

    def move_via(self, net, old, new, size=VIA_SIG):
        """Relocate a via an earlier step's table placed (asserted there, on net and at size) to new: the table move
        by which a family opens a gap (rf_if's fence openings, D-S7-03)."""
        old = (r4(old[0]), r4(old[1]))
        if not self.dry:                    # (a dry run records only; r9_route_check's template finds old empty)
            hits = [t for t in self.b.GetTracks() if t.GetClass() == 'PCB_VIA' and
                    math.dist((mm(t.GetPosition().x), mm(t.GetPosition().y)), old) < 1e-3]
            assert len(hits) == 1, f'move_via: {len(hits)} vias at {old}'
            v = hits[0]
            assert v.GetNetname() == net and abs(mm(v.GetWidth(pcbnew.F_Cu)) - size[0]) < EPS and \
                abs(mm(v.GetDrillValue()) - size[1]) < EPS, f'move_via: the via at {old} is not a {size} {net} via'
            self.b.Remove(v)
        self.moved.append((net, old))
        self.via(net, new, size)


def load_family(name):
    assert name in FAMILIES, f'unknown family {name}; one of {FAMILIES}'
    return importlib.import_module(f'r9_route_{name}')


def build(b, family, dry=False):
    """Draw (or, dry, record) one family's copper; asserts its pads and the nets it draws."""
    fam = load_family(family)
    d = Draw(b, family, dry)
    for ref, num, net, at in getattr(fam, 'PADS', ()):
        d.pad(ref, num, net, at)
    fam.draw(d)
    drawn = {net for net, *_ in d.tracks} | set(d.vias.values())
    allowed = set(fam.NETS) | set(getattr(fam, 'CONTINUES', ())) | set(fam.RAILS) | {'GND'}
    assert drawn <= allowed, f'{family}: draws nets it does not own {sorted(drawn - allowed)}'
    missing = set(fam.NETS) - drawn
    assert not missing, f'{family}: nets not drawn {sorted(missing)}'
    return d


def check_input(b, fam):
    """The family runs once: none of its NETS carries copper yet."""
    fresh = set(fam.NETS)
    drawn = sorted({t.GetNetname() for t in b.GetTracks()} & fresh)
    assert not drawn, f'{fam.__name__}: its nets already carry copper {drawn} (run each family once, in order)'


def check_vias(b, d):
    """Every via keeps the net it was drawn with after connectivity (a via landing on foreign copper is re-netted)."""
    bad = []
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            at = (r4(mm(t.GetPosition().x)), r4(mm(t.GetPosition().y)))
            if at in d.vias and t.GetNetname() != d.vias[at]:
                bad.append(f'{at}: drawn {d.vias[at]}, now {t.GetNetname()}')
    assert not bad, 'connectivity re-netted vias (a via sits on foreign copper):\n  ' + '\n  '.join(bad)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('family', choices=FAMILIES)
    ap.add_argument('--board', type=Path, default=PROJECT / 'm3.kicad_pcb')
    ap.add_argument('--no-fill', action='store_true', help='design aid: save unfilled')
    args = ap.parse_args()
    board = args.board.resolve()
    for ext in ('.kicad_pro', '.kicad_dru'):
        assert board.with_suffix(ext).is_file(), f'{board.with_suffix(ext).name} must sit beside the board'
    fam = load_family(args.family)
    b = pcbnew.LoadBoard(str(board))
    check_input(b, fam)
    pcbnew.KIID.SeedGenerator(KIID_SEED[args.family])
    for z in b.Zones():
        if not z.GetIsRuleArea():
            z.UnFill()                     # stale fills would re-net new vias (R8 spike (c) pitfall)
    d = build(b, args.family)
    if not args.no_fill:
        b.BuildConnectivity()
        assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'native zone fill failed'
    b.BuildConnectivity()
    check_vias(b, d)
    assert pcbnew.SaveBoard(str(board), b, True), 'save failed'
    length = sum(math.dist(a, c) for _, _, _, a, c in d.tracks)
    print(f'r9_route {args.family}: {len(d.tracks)} segments ({length:.1f} mm), {len(d.vias)} vias '
          f'({sum(1 for n in d.vias.values() if n == "GND")} GND)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
