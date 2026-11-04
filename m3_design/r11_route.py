#!/usr/bin/env python3
"""R11 copper primitives and the routing-family dispatcher (stage C, r11_plan.md section 4; D-R11-07): explicit tables
only, no path search. One family per run, in build order; a family whose module (m3_design/r11_route_<family>.py) does
not exist yet is skipped, so later stages add their families without touching this file.

usage: <KiCad python3> -I -B m3_design/r11_route.py FAMILY [--board m3_design/r11/m3.kicad_pcb]

Six copper layers (JLC06161H-3313, D-R11-03): F (parts, signals) / In1 GND / In2 power regions / In3 inner signals /
In4 GND / B (parts, signals). Every via is a through via (F to B): JLC's standard multilayer process; blind and buried
vias are not used. Widths (D-R11-15): signals 0.1 mm (the BGA channel width), 0.15 / 0.2 mm where there is room;
power from R10's set (0.2 ... 2.0 mm), sized per IPC-2152 by the family that draws them.
"""
import argparse
import importlib
import importlib.util
import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'm3_design'), str(ROOT / 'tools')]

PROJECT = ROOT / 'm3_design/r11'
LAYERS = {'F': pcbnew.F_Cu, 'In1': pcbnew.In1_Cu, 'In2': pcbnew.In2_Cu, 'In3': pcbnew.In3_Cu, 'In4': pcbnew.In4_Cu,
          'B': pcbnew.B_Cu}
LAYER_NAME = {v: k for k, v in LAYERS.items()}
# Build order (r11_plan.md section 4): the core fan-out first, the poured ground last.
FAMILIES = ('core', 'usb', 'pyro', 'power', 'ports', 'servo', 'sd', 'signals', 'status', 'ground')
# D-R11-15: signal 0.1 (JLC multilayer 0.09 mm floor plus 0.01, m3.kicad_dru), wider signal / power steps after R10's
WIDTHS = (0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5, 2.0)
SIGNAL_VIA = (0.4, 0.2)          # stageB.md section 10: dog-bone / signal via, 0.10 mm annular ring
POWER_VIA = (0.45, 0.25)         # power and GND stitching
BIG_VIA = (0.6, 0.3)             # high-current power
FLOOR_VIA = (0.3, 0.15)          # D-R11-85: the DRU floor via (m3.kicad_dru, D-R11-15), one GND partner in the ball field
VIA_SIZES = (SIGNAL_VIA, POWER_VIA, BIG_VIA, FLOOR_VIA)
EPS = 1e-6
KIID_BASE = 11110


def point(p):
    return pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in p))


def xy(position):
    return tuple(round(pcbnew.ToMM(v), 4) for v in (position.x, position.y))


def octilinear(a, b):
    dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
    return dx < EPS or dy < EPS or abs(dx - dy) < EPS


def module_path(family):
    return ROOT / 'm3_design' / f'r11_route_{family}.py'


def implemented(family):
    return module_path(family).is_file()


def family_module(family):
    return importlib.import_module(f'r11_route_{family}')


def family_nets(family):
    """The nets a family completes (its module's NETS); () for a family not written yet."""
    return tuple(getattr(family_module(family), 'NETS', ())) if implemented(family) else ()


class Draw:
    """Copper writer. Every segment is checked octilinear and non-zero, every width and via size against the R11 sets;
    a via is never placed twice at one point."""

    def __init__(self, board, dry=False):
        self.board, self.dry = board, dry
        self.tracks, self.vias = [], {}

    def pad(self, ref, number=None, net=None, at=None):
        if number is None:
            ref, number = ref.split('.')
        footprint = self.board.FindFootprintByReference(ref)
        assert footprint, f'no footprint {ref}'
        pads = [p for p in footprint.Pads() if p.GetNumber() == str(number)]
        assert pads, f'no pad {ref}.{number}'
        p = pads[0]
        pos = xy(p.GetPosition())
        assert net is None or p.GetNetname() == net, (ref, number, p.GetNetname(), net)
        assert at is None or math.dist(pos, at) < 0.001, (ref, number, pos, at)
        return pos

    def net(self, name):
        net = self.board.FindNet(name)
        assert net is not None and net.GetNetCode() > 0, f'unknown net {name}'
        return net

    def track(self, net, layer, width, points):
        assert width in WIDTHS, f'{net}: width {width} outside the R11 width set'
        assert layer in LAYERS, layer
        points = [tuple(round(v, 4) for v in p) for p in points]
        for a, b in zip(points, points[1:]):
            assert a != b and octilinear(a, b), f'{net}: non-octilinear or zero segment {a} -> {b}'
            self.tracks.append((net, layer, width, a, b))
            if not self.dry:
                t = pcbnew.PCB_TRACK(self.board)
                t.SetStart(point(a)); t.SetEnd(point(b))
                t.SetWidth(pcbnew.FromMM(width)); t.SetLayer(LAYERS[layer]); t.SetNet(self.net(net))
                self.board.Add(t)

    def via(self, net, at, size=SIGNAL_VIA):
        assert tuple(size) in VIA_SIZES, f'{net}: via {size} outside the R11 via set'
        at = tuple(round(v, 4) for v in at)
        assert at not in self.vias, f'duplicate via {at}'
        self.vias[at] = net
        if not self.dry:
            for item in self.board.GetTracks():
                if item.GetClass() == 'PCB_VIA' and xy(item.GetPosition()) == at:
                    raise AssertionError(f'via already present {at}')
            v = pcbnew.PCB_VIA(self.board)
            v.SetPosition(point(at)); v.SetWidth(pcbnew.FromMM(size[0])); v.SetDrill(pcbnew.FromMM(size[1]))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(self.net(net))
            self.board.Add(v)

    def vippo(self, net, at):
        """GAP-3 (AGENTS section 3, D-R11-80): one of U401.11's two 0.5 / 0.3 GND thermal vias, resin-filled and
        copper-capped (planar VIPPO). The only via size outside VIA_SIZES; check_r11 K-copper holds the exact pose."""
        assert net == 'GND', 'GAP-3 thermal vias are GND only'
        at = tuple(round(v, 4) for v in at)
        assert at not in self.vias, f'duplicate via {at}'
        self.vias[at] = net
        if not self.dry:
            v = pcbnew.PCB_VIA(self.board)
            v.SetPosition(point(at)); v.SetWidth(pcbnew.FromMM(0.5)); v.SetDrill(pcbnew.FromMM(0.3))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(self.net(net))
            v.SetFillingMode(pcbnew.FILLING_MODE_FILLED); v.SetCappingMode(pcbnew.CAPPING_MODE_CAPPED)
            self.board.Add(v)

    def link(self, net, layer, width, start, end, corners=()):
        """Pad-referenced polyline: start pad, the explicit corners, end pad."""
        self.track(net, layer, width, [self.pad(start, net=net), *corners, self.pad(end, net=net)])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('family', choices=FAMILIES)
    parser.add_argument('--board', type=Path, default=PROJECT / 'm3.kicad_pcb')
    args = parser.parse_args()
    if not implemented(args.family):
        print(f'r11_route {args.family}: no module {module_path(args.family).name} yet; skipped')
        return 0
    board = pcbnew.LoadBoard(str(args.board))
    pcbnew.KIID.SeedGenerator(KIID_BASE + FAMILIES.index(args.family))
    for zone in board.Zones():
        if not zone.GetIsRuleArea():
            zone.UnFill()
    draw = Draw(board)
    family_module(args.family).draw(draw)
    board.BuildConnectivity()
    assert pcbnew.SaveBoard(str(args.board), board, True), 'route save failed'
    print(f'r11_route {args.family}: {len(draw.tracks)} segments, {len(draw.vias)} vias')
    return 0


if __name__ == '__main__':
    sys.exit(main())
