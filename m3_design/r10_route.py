#!/usr/bin/env python3
"""R10 copper primitives and explicit routing-family dispatcher; no path search."""
import argparse
import importlib
import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'm3_design'), str(ROOT / 'tools')]
import r9_route

PROJECT = ROOT / 'm3_design/assembly_review'
LAYERS = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, 'In1': pcbnew.In1_Cu, 'In2': pcbnew.In2_Cu}
FAMILIES = ('core', 'power', 'pyro', 'ports', 'servo', 'usb', 'status', 'signals', 'ground')
WIDTHS = (0.2, 0.25, 0.3, 0.4, 1.0, 2.0)
CORE_SHIFT = (5.0, -1.5)


def point(xy):
    return pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in xy))


def xy(position):
    return tuple(round(pcbnew.ToMM(v), 4) for v in (position.x, position.y))


class Draw:
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
        assert width in WIDTHS, f'width {width} outside R10 width set'
        points = [tuple(round(v, 4) for v in p) for p in points]
        for a, b in zip(points, points[1:]):
            assert a != b and r9_route.octilinear(a, b), f'{net}: non-octilinear/zero {a} -> {b}'
            self.tracks.append((net, layer, width, a, b))
            if not self.dry:
                t = pcbnew.PCB_TRACK(self.board)
                t.SetStart(point(a)); t.SetEnd(point(b))
                t.SetWidth(pcbnew.FromMM(width)); t.SetLayer(LAYERS[layer]); t.SetNet(self.net(net))
                self.board.Add(t)

    def via(self, net, at, size=(0.5, 0.3)):
        at = tuple(round(v, 4) for v in at)
        assert at not in self.vias, f'duplicate via {at}'
        self.vias[at] = net
        if not self.dry:
            for item in self.board.GetTracks():
                if item.GetClass() == 'PCB_VIA' and xy(item.GetPosition()) == at:
                    raise AssertionError(f'via already present {at}')
            v = pcbnew.PCB_VIA(self.board)
            v.SetPosition(point(at)); v.SetWidth(pcbnew.FromMM(size[0])); v.SetDrill(pcbnew.FromMM(size[1]))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(self.net(net)); self.board.Add(v)

    def zone(self, name, net, layer, pts, prio, clr=0.25, minw=0.25, conn=pcbnew.ZONE_CONNECTION_THERMAL,
             tgap=0.25, spoke=0.3):
        z = pcbnew.ZONE(self.board)
        z.SetLayer(LAYERS[layer])
        z.SetNet(self.net(net))
        z.SetZoneName(name)
        z.SetAssignedPriority(prio)
        z.SetLocalClearance(pcbnew.FromMM(clr))
        z.SetMinThickness(pcbnew.FromMM(minw))
        z.SetPadConnection(conn)
        z.SetThermalReliefGap(pcbnew.FromMM(tgap))
        z.SetThermalReliefSpokeWidth(pcbnew.FromMM(spoke))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o = z.Outline()
        o.NewOutline()
        for x, y in pts:
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        assert not o.IsSelfIntersecting(), name
        if not self.dry:
            self.board.Add(z)
        return z

    def link(self, net, layer, width, start, end, corners=()):
        """Pad-referenced, explicitly chosen polyline. No implicit routing choice."""
        self.track(net, layer, width, [self.pad(start, net=net), *corners, self.pad(end, net=net)])


class Translated:
    """Reuse a deliberate R9 local circuit table as a rigid translation."""
    def __init__(self, draw, shift):
        self.draw, self.shift = draw, shift

    def move(self, p):
        return tuple(round(a + b, 4) for a, b in zip(p, self.shift))

    def track(self, net, layer, width, points):
        self.draw.track(net, layer, width, [self.move(p) for p in points])

    def via(self, net, at, size=(0.5, 0.3)):
        self.draw.via(net, self.move(at), size)

    def pad(self, ref, number, net=None, at=None):
        result = self.draw.pad(ref, number, net, self.move(at) if at else None)
        return tuple(a - b for a, b in zip(result, self.shift))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family', choices=FAMILIES)
    parser.add_argument('--board', type=Path, default=PROJECT / 'm3.kicad_pcb')
    args = parser.parse_args()
    board = pcbnew.LoadBoard(str(args.board))
    pcbnew.KIID.SeedGenerator(10110 + FAMILIES.index(args.family))
    for zone in board.Zones():
        if not zone.GetIsRuleArea():
            zone.UnFill()
    draw = Draw(board)
    importlib.import_module(f'r10_route_{args.family}').draw(draw)
    board.BuildConnectivity()
    assert pcbnew.SaveBoard(str(args.board), board, True), 'route save failed'
    print(f'r10_route {args.family}: {len(draw.tracks)} segments, {len(draw.vias)} vias')


if __name__ == '__main__':
    main()
