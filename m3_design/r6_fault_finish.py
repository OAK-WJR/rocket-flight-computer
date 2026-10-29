#!/usr/bin/env python3
"""Replay the reviewed PA7 fault connection and its local 3V3 bridge."""
import json
from pathlib import Path

import pcbnew

from r6_port_finish import point
from r6_selected_finish import copper_record

PACKET = Path(__file__).parent / 'assembly_review/sources/r6_fault_pa7_packet.json'


def record(item):
    result = copper_record(item)
    result['locked'] = item.IsLocked()
    if item.GetClass() == 'PCB_VIA':
        result['layers'] = [item.TopLayer(), item.BottomLayer()]
    return result


def repair(board):
    """Guard the complete old/new states; caller refills and runs DRC/parity."""
    data = json.loads(PACKET.read_text())
    existing = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    if len(existing) != len(list(board.GetTracks())):
        raise ValueError('Duplicate copper UUIDs')
    present = [s for s in data['added'] if s['uuid'] in existing]
    for spec in present:
        if record(existing[spec['uuid']]) != spec:
            raise ValueError('Changed reviewed fault copper')
    if present and len(present) != len(data['added']):
        raise ValueError('Partial fault route')
    pads = []
    for change in data['pad_changes']:
        fp = board.FindFootprintByReference(change['reference'])
        pad = fp.FindPadByNumber(change['pad']) if fp else None
        expected = change['after'] if present else change['before']
        if not pad or pad.GetPosition() != point(change['position']) or pad.GetNetname() != expected:
            raise ValueError('Changed fault GPIO assignment or position')
        pads.append((pad, change))
    if present:
        if any(s['uuid'] in existing for s in data['removed']):
            raise ValueError('Original fault escape remains after migration')
        return {'applied': False, 'skipped': 'already applied'}
    for spec in data['removed']:
        item = existing.get(spec['uuid'])
        if item is None or record(item) != spec:
            raise ValueError('Changed original PE0 escape')
    for spec in data['added']:
        if board.FindNet(spec['net']) is None:
            raise ValueError('Required route net is absent')
    for item, change in pads:
        net = board.FindNet(change['after'])
        if net is None:
            net = pcbnew.NETINFO_ITEM(board, change['after'])
            board.Add(net)
        item.SetNet(net)
    for spec in data['removed']:
        board.Delete(existing[spec['uuid']])
    for spec in data['added']:
        if spec['kind'] == 'via':
            item = pcbnew.PCB_VIA(board)
            item.SetPosition(point(spec['at']))
            item.SetWidth(pcbnew.FromMM(spec['diameter']))
            item.SetDrill(pcbnew.FromMM(spec['drill']))
            item.SetLayerPair(*spec['layers'])
        else:
            item = pcbnew.PCB_TRACK(board)
            item.SetStart(point(spec['start']))
            item.SetEnd(point(spec['end']))
            item.SetWidth(pcbnew.FromMM(spec['width']))
            item.SetLayer(spec['layer'])
        item.SetNet(board.FindNet(spec['net']))
        item.SetLocked(spec['locked'])
        item.SetUuid(pcbnew.KIID(spec['uuid']))
        board.Add(item)
    return {'applied': True, 'added': len(data['added']), 'removed': len(data['removed']),
            'zones_require_refill': True, 'native_drc_required': True}
