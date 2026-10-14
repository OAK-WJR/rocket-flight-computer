#!/usr/bin/env python3
"""Replay the reviewed GPS transmit connection without changing existing copper."""
import json
from pathlib import Path

import pcbnew

PACKET = Path(__file__).parent / 'assembly_review/sources/r6_gps_finish_packet.json'


def _point(xy):
    return pcbnew.VECTOR2I(*xy)


def _record(board, item):
    via = item.GetClass() == 'PCB_VIA'
    result = {'uuid': item.m_Uuid.AsString(), 'type': item.GetClass(),
              'net': item.GetNetname(), 'locked': item.IsLocked(),
              'width_nm': item.GetWidth(pcbnew.F_Cu) if via else item.GetWidth()}
    if via:
        result.update(position_nm=[item.GetPosition().x, item.GetPosition().y],
                      drill_nm=item.GetDrill(), via_type=item.GetViaType(),
                      top_layer=board.GetLayerName(item.TopLayer()),
                      bottom_layer=board.GetLayerName(item.BottomLayer()))
    else:
        result.update(start_nm=[item.GetStart().x, item.GetStart().y],
                      end_nm=[item.GetEnd().x, item.GetEnd().y],
                      layer=board.GetLayerName(item.GetLayer()))
    return result


def repair(board):
    """Reject partial/changed geometry; caller refills and runs native DRC."""
    packet = json.loads(PACKET.read_text())
    specs = packet['added_tracks']
    if (packet['geometry_units'] != 'nanometres' or len(specs) != 66
            or packet['removed_tracks_guard'] or packet['pad_changes']
            or any(s['net'] != 'GPS_TX_MCU' for s in specs)
            or len({s['uuid'] for s in specs}) != len(specs)):
        raise ValueError('Unexpected GPS packet scope')
    existing = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    if len(existing) != len(list(board.GetTracks())):
        raise ValueError('Duplicate copper UUIDs')
    for spec in packet['pads']:
        fp = board.FindFootprintByReference(spec['ref'])
        pad = fp.FindPadByNumber(spec['number']) if fp else None
        if (not pad or pad.GetNetname() != spec['net']
                or pad.GetPosition() != _point(spec['position_nm'])
                or pad.GetLayerSet().FmtHex() != spec['layers']):
            raise ValueError('Reviewed GPS pad changed: ' + spec['ref'] + '.' + spec['number'])
    for spec in packet['anchors']:
        item = existing.get(spec['uuid'])
        if item is None or _record(board, item) != spec:
            raise ValueError('Reviewed GPS escape anchor changed')
    present = [s for s in specs if s['uuid'] in existing]
    if any(_record(board, existing[s['uuid']]) != s for s in present):
        raise ValueError('Changed reviewed GPS copper')
    if present:
        if len(present) != len(specs):
            raise ValueError('Partial GPS route')
        return {'applied': False, 'skipped': 'already applied'}
    net = board.FindNet('GPS_TX_MCU')
    if not net or net.GetNetCode() == 0:
        raise ValueError('Missing GPS transmit net')
    candidates = []
    for spec in specs:
        if spec['type'] == 'PCB_VIA':
            if (spec['via_type'] != pcbnew.VIATYPE_THROUGH
                    or spec['top_layer'] != 'F.Cu' or spec['bottom_layer'] != 'B.Cu'):
                raise ValueError('Unexpected GPS via type/layers')
            item = pcbnew.PCB_VIA(board)
            item.SetViaType(pcbnew.VIATYPE_THROUGH)
            item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            item.SetPosition(_point(spec['position_nm']))
            item.SetDrill(spec['drill_nm'])
        elif spec['type'] == 'PCB_TRACK':
            item = pcbnew.PCB_TRACK(board)
            item.SetStart(_point(spec['start_nm']))
            item.SetEnd(_point(spec['end_nm']))
            item.SetLayer(board.GetLayerID(spec['layer']))
        else:
            raise ValueError('Unexpected GPS copper type')
        item.SetWidth(spec['width_nm'])
        item.SetNet(net)
        item.SetLocked(spec['locked'])
        item.SetUuid(pcbnew.KIID(spec['uuid']))
        candidates.append(item)
    before = {key: _record(board, item) for key, item in existing.items()}
    for item in candidates:
        board.Add(item)
    board.BuildConnectivity()
    assert all(_record(board, item) == before[key] for key, item in existing.items())
    return {'applied': True, 'added': len(candidates), 'removed': 0,
            'zones_require_refill': True, 'native_drc_required': True}
