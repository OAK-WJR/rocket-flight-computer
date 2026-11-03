#!/usr/bin/env python3
"""Restore the wide R6 RAW_ACT front pour; caller owns refill, DRC and save."""
import argparse
from pathlib import Path
import uuid

import pcbnew

MM, mm = pcbnew.FromMM, pcbnew.ToMM
NAMESPACE = uuid.UUID('8ea0cf02-9fc2-43d2-b77a-ec061df8da30')
OLD_CHAIN = [(7.9, 62.6902), (4.4, 62.6902), (4.1, 62.9902),
             (4.1, 69.9902), (4.7, 70.5902), (11.9, 70.5902),
             (12.5, 71.1902), (12.5, 71.225)]
PATHS = [(pcbnew.F_Cu, [(7.9, 62.6902), (7.9, 62.4)]),
         (pcbnew.In2_Cu, [(7.9, 62.4), (7.9, 66.6), (12.5, 71.2)]),
         (pcbnew.F_Cu, [(12.5, 71.2), (12.5, 71.225)])]
VIAS = [(7.9, 62.4), (12.5, 71.2)]


def point(xy):
    return pcbnew.VECTOR2I(*(MM(v) for v in xy))


def xy(p):
    return round(mm(p.x), 4), round(mm(p.y), 4)


def repair(board):
    """Replace only the identified 3V3 barrier, with deterministic locked copper.

    The front trace split the RAW_ACT pour into isolated pieces and forced the
    servo feed through a long 0.2 mm back trace. The short In2 bypass leaves the
    front pour continuous. Native DRC and both actuator DC paths must be checked
    after refill; this function never changes component positions or zones.
    """
    signatures = {frozenset((a, b)) for a, b in zip(OLD_CHAIN, OLD_CHAIN[1:])}
    tracks = {}
    for index, (layer, pts) in enumerate(PATHS):
        for segment, (a, b) in enumerate(zip(pts, pts[1:])):
            tracks[str(uuid.uuid5(NAMESPACE, f'track:{index}:{segment}'))] = (layer, a, b)
    vias = {str(uuid.uuid5(NAMESPACE, f'via:{index}')): p for index, p in enumerate(VIAS)}
    own = set(tracks) | set(vias)
    old, present = [], set()
    for item in board.GetTracks():
        identity = item.m_Uuid.AsString()
        if identity in own:
            present.add(identity)
        elif (item.GetClass() == 'PCB_TRACK' and item.GetNetname() == '3V3'
              and item.GetLayer() == pcbnew.F_Cu
              and frozenset((xy(item.GetStart()), xy(item.GetEnd()))) in signatures):
            old.append(item)
    if len(old) != len(signatures) and not (not old and present == own):
        raise RuntimeError('3V3 barrier geometry changed; rederive the RAW_ACT bridge')
    removed = [item.m_Uuid.AsString() for item in old]
    for item in list(board.GetTracks()):
        if item.m_Uuid.AsString() in own or item.m_Uuid.AsString() in removed:
            board.Delete(item)
    for identity, (layer, a, b) in tracks.items():
        item = pcbnew.PCB_TRACK(board)
        item.SetUuid(pcbnew.KIID(identity))
        item.SetLayer(layer)
        item.SetStart(point(a))
        item.SetEnd(point(b))
        item.SetWidth(MM(.25))
        item.SetNet(board.FindNet('3V3'))
        item.SetLocked(True)
        board.Add(item)
    for identity, pos in vias.items():
        item = pcbnew.PCB_VIA(board)
        item.SetUuid(pcbnew.KIID(identity))
        item.SetPosition(point(pos))
        item.SetWidth(MM(.6))
        item.SetDrill(MM(.3))
        item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        item.SetNet(board.FindNet('3V3'))
        item.SetLocked(True)
        board.Add(item)
    board.BuildConnectivity()
    return dict(removed_tracks=removed, added_tracks=len(tracks), added_vias=VIAS,
                zones_require_refill=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.board.resolve() == args.output.resolve():
        raise SystemExit('Use a distinct output path')
    board = pcbnew.LoadBoard(str(args.board))
    print(repair(board))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(args.output), board, True)
