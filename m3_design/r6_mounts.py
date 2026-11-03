#!/usr/bin/env python3
"""Move three R6 parts clear of M3 washers; caller owns rerouting and native DRC."""
import argparse
import json
import math
from pathlib import Path
import uuid

import pcbnew

MM, mm = pcbnew.FromMM, pcbnew.ToMM
MOVES = {
    'C177': ((7.0, 7.0), (7.75, 7.20), 90.0, {'1': 'RAW_PROTECTED', '2': 'GND'}),
    'C178': ((8.0, 4.5), (9.1, 4.5), 0.0, {'1': 'TLM_DVDT', '2': 'GND'}),
    'TP89': ((5.0, 41.5), (5.0, 41.4), 0.0, {'1': 'BAT_ILIM'}),
}
OFFSETS = {'C177': {'1': (0, .775), '2': (0, -.775)},
           'C178': {'1': (-.775, 0), '2': (.775, 0)}, 'TP89': {'1': (0, 0)}}
NAMESPACE = uuid.UUID('590befce-e346-47ee-bdec-9ce10981b67c')


def point(xy):
    return pcbnew.VECTOR2I(*(MM(v) for v in xy))


def xy(p):
    return mm(p.x), mm(p.y)


def leadouts(board, pad, displacement):
    """Detach only old pad leads that lose their anchor; keep vias and trunks."""
    for track in board.GetTracks():
        if (track.GetClass() != 'PCB_TRACK' or track.GetNetname() != pad.GetNetname()
                or not pad.IsOnLayer(track.GetLayer())):
            continue
        shape = pad.GetEffectiveShape(track.GetLayer())
        ends = [end for end in (track.GetStart(), track.GetEnd())
                if shape.Collide(end, track.GetWidth() // 2)]
        target = shape.Clone(); target.Move(point(displacement))
        if ends and not any(target.Collide(end, 0) for end in ends):
            yield track


def anchor_present(board, position):
    """The preserved RAW_PROTECTED power branch must still reach this anchor."""
    p = point(position)
    for track in board.GetTracks():
        if track.GetNetname() == 'RAW_PROTECTED' and track.IsOnLayer(pcbnew.F_Cu):
            if (track.GetClass() == 'PCB_VIA' and track.GetEffectiveShape(pcbnew.F_Cu).Collide(p, 0)) or (
                    track.GetClass() == 'PCB_TRACK' and any(math.dist(xy(end), position) <= .001
                    for end in (track.GetStart(), track.GetEnd()))):
                return True
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.GetNetname() == 'RAW_PROTECTED' and pad.IsOnLayer(pcbnew.F_Cu):
                if pad.GetEffectiveShape(pcbnew.F_Cu).Collide(p, 0):
                    return True
    return False


def repair(board):
    """Change only the supplied board; accept old or final geometry, never other placements.

    SES leadouts are identified by geometry/net, not UUID. Existing foreign
    copper, vias and nonattached tracks are preserved. C177's short input lead
    is rebuilt to its retained power-branch anchor. All other moved pads need
    connectivity rechecking after a refill; incoming routing may need repair.
    """
    footprints, pending = {}, []
    for ref, (old, new, angle, nets) in MOVES.items():
        footprint = board.FindFootprintByReference(ref)
        if footprint is None:
            raise ValueError(f'{ref}: required R6 component is missing')
        position = xy(footprint.GetPosition())
        at_old, at_new = math.dist(position, old) <= .001, math.dist(position, new) <= .001
        if (not (at_old or at_new) or footprint.IsFlipped()
                or abs((footprint.GetOrientationDegrees() - angle + 180) % 360 - 180) > .001):
            raise ValueError(f'{ref}: unexpected position/side/rotation; refusing stale placement repair')
        actual = {pad.GetNumber(): pad.GetNetname() for pad in footprint.Pads()}
        if actual != nets:
            raise ValueError(f'{ref}: unexpected pad nets {actual}')
        for pad in footprint.Pads():
            offset = OFFSETS[ref][pad.GetNumber()]
            expected = (position[0] + offset[0], position[1] + offset[1])
            if math.dist(xy(pad.GetPosition()), expected) > .001:
                raise ValueError(f'{ref}.{pad.GetNumber()}: unexpected pad geometry')
        footprints[ref] = footprint
        if at_old:
            pending.append(ref)
    report = dict(moved=[], detached=[], added=[], connections_to_recheck=[], hidden_references=[],
                  zones_require_refill=False, native_drc_required=True)
    detached = {}
    for ref in pending:
        old, new, _, _ = MOVES[ref]
        displacement = (new[0] - old[0], new[1] - old[1])
        for pad in footprints[ref].Pads():
            for track in leadouts(board, pad, displacement):
                detached[track.m_Uuid.AsString()] = track
    for key, track in sorted(detached.items()):
        report['detached'].append(dict(uuid=key, net=track.GetNetname(),
            layer=board.GetLayerName(track.GetLayer()), width_mm=mm(track.GetWidth()),
            start_mm=xy(track.GetStart()), end_mm=xy(track.GetEnd())))
        board.Remove(track)
    for ref in pending:
        old, new, _, _ = MOVES[ref]
        footprints[ref].SetPosition(point(new))
        report['moved'].append(dict(ref=ref, old_mm=old, new_mm=new))
        for pad in footprints[ref].Pads():
            report['connections_to_recheck'].append(dict(ref=ref, pad=pad.GetNumber(),
                net=pad.GetNetname(), position_mm=xy(pad.GetPosition())))
    if 'C177' in pending and anchor_present(board, (9.025, 7.775)):
        positions = [xy(footprints['C177'].FindPadByNumber('1').GetPosition()), (7.75, 7.775), (9.025, 7.775)]
        for a, b in zip(positions, positions[1:]):
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(point(a)); track.SetEnd(point(b))
            track.SetLayer(pcbnew.F_Cu); track.SetWidth(MM(.3))
            track.SetNet(board.FindNet('RAW_PROTECTED')); track.SetLocked(True)
            key = f'RAW_PROTECTED:{a}:{b}:0.3'
            track.SetUuid(pcbnew.KIID(str(uuid.uuid5(NAMESPACE, key))))
            board.Add(track)
            report['added'].append(dict(net='RAW_PROTECTED', layer='F.Cu', width_mm=.3,
                                       start_mm=a, end_mm=b))
        report['connections_to_recheck'] = [p for p in report['connections_to_recheck']
                                            if (p['ref'], p['pad']) != ('C177', '1')]
    if footprints['C178'].Reference().IsVisible():
        footprints['C178'].Reference().SetVisible(False)
        report['hidden_references'].append('C178')
    if pending:
        board.BuildConnectivity()
        report['zones_require_refill'] = True
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.board.resolve() == args.output.resolve():
        raise SystemExit('Use a distinct output path')
    board = pcbnew.LoadBoard(str(args.board))
    report = repair(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(args.output), board, True)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
