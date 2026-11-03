#!/usr/bin/env python3
"""Build the R8 board's signal copper (M3-ASSY-R8, build step 6), one signal family per run.

usage: <KiCad python3> -I m3_design/r8_route.py FAMILY [--board m3_design/assembly_review/m3.kicad_pcb] [--no-fill]

FAMILY is one of FAMILIES below; r8_build.sh runs them in that order, each followed by its gate
(r8_route_check.py FAMILY). The board is rebuilt in place, so the project's m3.kicad_pro and m3.kicad_dru apply
while it is filled. Design basis: r8_plan.md section 3 step 6, R8_DECISIONS (D1-D50 and the step-6 block D51 on),
the spikes (m3_design/r8_spikes/*/RESULT.md) and the routing reservations of r8_keepclear.tsv. Every number is board
mm (y forward, U1 at (23, 45) rotation 0).

Each family is one module, m3_design/r8_route_<family>.py, written as deliberate, explicit octilinear polylines and
vias from tables (bus lanes as parallel polylines at a fixed pitch): no autorouter, nothing hand-patched. A module
defines
  NETS     the nets it completes (its gate requires every pad of each joined)
  CONTINUES  (optional) those of NETS that an earlier step started (step 5's 3V3A trunk); the others must carry no
           copper before the family runs
  RAILS    the shared nets it taps (3V3, GND), whole after the last family (GND from imu on, r8_route_check)
  BUDGET   its asserted limits: signal track length, signal vias, critical layer changes, the worst copper /
           octilinear-MST ratio of a net (checked by r8_route_check.py)
  draw(d)  its copper, through the Draw primitives below
The last family, links, draws the remaining short links under the plan's r5_maze constraint (each link on one layer,
copper <= 1.3 x its octilinear distance, no via) or the build fails; R8_DECISIONS D59 says why it does not call
r5_maze itself.

The Draw primitives refuse non-octilinear segments, zero-length segments, two vias at one point and a pad that is
not where (or on the net) the table assumes, so a placement change cannot silently bend the copper.
Deterministic (fixed KIID seed per family): a rebuild reproduces the board byte for byte.
"""
import argparse
import importlib
import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r8  # noqa: E402
import r8_power_check  # noqa: E402

PROJECT = ROOT / 'm3_design/assembly_review'
MM, mm = pcbnew.FromMM, pcbnew.ToMM
F, B = pcbnew.F_Cu, pcbnew.B_Cu
LAYER = {'F': F, 'B': B}
FAMILIES = ('qspi_hse', 'rf', 'servo', 'pyro', 'usb_swd', 'imu', 'camera', 'status', 'links')
KIID_SEED = {name: 8806 + i for i, name in enumerate(FAMILIES)}
W = 0.2                      # signal width (plan_partial section 4; the spikes)
VIA_SIG = (0.5, 0.3)         # signal and GND-partner via (spikes a / d)
VIA_PWR = (0.6, 0.3)         # the board's default via (m3.kicad_pro), power taps
EPS = 1e-6


def P(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def r4(v):
    return round(v, 4)


def octilinear(a, b):
    dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
    return dx < EPS or dy < EPS or abs(dx - dy) < EPS


def octile(a, b):
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


def u1_pin(n):
    """U1 pad centre at rotation 0, (23, 45) (R8_DECISIONS D1; spike (a) u1_pin)."""
    if n <= 25:
        return (r4(17.0 + 0.5 * (n - 1)), 52.55)
    if n <= 50:
        return (30.55, r4(51.0 - 0.5 * (n - 26)))
    if n <= 75:
        return (r4(29.0 - 0.5 * (n - 51)), 37.45)
    return (15.45, r4(39.0 + 0.5 * (n - 76)))


class Draw:
    """Copper primitives for one family on a board; every item is recorded for the gate's report."""

    def __init__(self, board, family):
        self.b = board
        self.family = family
        self.vias = {}
        self.tracks = []

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
        pts = [(r4(x), r4(y)) for x, y in pts]
        for a, c in zip(pts, pts[1:]):
            assert a != c, f'{net}: zero-length segment at {a}'
            assert octilinear(a, c), f'{net}: segment {a}-{c} is not 0 / 45 / 90 degrees'
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(P(*a))
            t.SetEnd(P(*c))
            t.SetWidth(MM(width))
            t.SetLayer(LAYER[layer])
            t.SetNet(n)
            self.b.Add(t)
            self.tracks.append((net, layer, width, a, c))

    def via(self, net, x, y, size=VIA_SIG):
        key = (r4(x), r4(y))
        assert key not in self.vias, f'two vias at {key}'
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(P(*key))
        v.SetWidth(MM(size[0]))
        v.SetDrill(MM(size[1]))
        v.SetLayerPair(F, B)
        v.SetNet(self.net(net))
        self.b.Add(v)
        self.vias[key] = net


def load_family(name):
    assert name in FAMILIES, f'unknown family {name}; one of {FAMILIES}'
    return importlib.import_module(f'r8_route_{name}')


def check_input(b, fam):
    """The family runs once: none of its nets carries copper yet (besides the rigid R7 copper), and the rigid digests
    hold."""
    issues, _ = check_r8.rigid(b)
    assert not issues, issues
    rigid = {t.m_Uuid.AsString() for t in r8_power_check.rigid_items(b)}
    fresh = set(fam.NETS) - set(getattr(fam, 'CONTINUES', ()))
    drawn = sorted({t.GetNetname() for t in b.GetTracks() if t.m_Uuid.AsString() not in rigid} & fresh)
    assert not drawn, f'{fam.__name__}: its nets already carry copper {drawn} (run each family once, in order)'


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
            z.UnFill()                     # stale fills would re-net new vias (spike (c) pitfall)
    d = Draw(b, args.family)
    fam.draw(d)
    if not args.no_fill:
        b.BuildConnectivity()
        assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'native zone fill failed'
    b.BuildConnectivity()
    moved = []
    for v in b.GetTracks():
        if v.GetClass() == 'PCB_VIA':
            key = (r4(mm(v.GetPosition().x)), r4(mm(v.GetPosition().y)))
            if key in d.vias and d.vias[key] != v.GetNetname():
                moved.append((key, d.vias[key], v.GetNetname()))
    assert not moved, f'connectivity re-netted vias (a via sits on foreign copper): {moved}'
    assert pcbnew.SaveBoard(str(board), b, True), 'save failed'
    b = pcbnew.LoadBoard(str(board))
    issues, digests = check_r8.rigid(b)
    assert not issues, issues
    length = sum(math.dist(a, c) for _, _, _, a, c in d.tracks)
    print(f'r8_route {args.family}: {len(d.tracks)} segments ({length:.1f} mm), {len(d.vias)} vias, '
          f'rigid digests {len(digests)}/12 equal R7')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
