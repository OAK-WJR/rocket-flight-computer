#!/usr/bin/env python3
"""Apply the reviewed radio M1 route and bounded radio TX reroute."""
import json
from pathlib import Path

import pcbnew

from r6_port_finish import point
from r6_swclk_finish import _matches

PACKET = Path(__file__).parent / 'assembly_review/sources/r6_m1_finish_packet.json'
PADS = [('U1', '66', 'RADIO_M1_MCU', (14.3, 37)),
        ('R197', '1', 'RADIO_M1_MCU', (38.77, 33)),
        ('U1', '63', 'RADIO_TX_MCU', (14.3, 35.5)),
        ('R198', '1', 'RADIO_TX_MCU', (38.77, 34.5))]


def repair(board):
    """Reject changed or partial geometry; caller refills and runs native DRC."""
    packet = json.loads(PACKET.read_text())
    added, removed = packet['added_tracks'], packet['removed_tracks_guard']
    if (packet['pad_changes'] or len(removed) != 2
            or any(s['net'] != 'RADIO_TX_MCU' or s['type'] != 'PCB_TRACK'
                   or s['layer'] != 'F.Cu' for s in removed)
            or any(s['net'] not in ('RADIO_M1_MCU', 'RADIO_TX_MCU') for s in added)):
        raise ValueError('Unexpected M1 packet scope')
    existing = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    if len(existing) != len(list(board.GetTracks())):
        raise ValueError('Duplicate copper UUIDs')
    for ref, number, net, xy in PADS:
        fp = board.FindFootprintByReference(ref)
        pad = fp.FindPadByNumber(number) if fp else None
        if not pad or pad.GetNetname() != net or pad.GetPosition() != point(xy):
            raise ValueError(f'{ref}.{number}: reviewed radio pad changed')
    present = [s for s in added if s['uuid'] in existing]
    for spec in present:
        if not _matches(board, existing[spec['uuid']], spec):
            raise ValueError('Changed reviewed M1/TX copper')
    if present:
        if len(present) != len(added) or any(s['uuid'] in existing for s in removed):
            raise ValueError('Partial M1/TX migration')
        return {'applied': False, 'skipped': 'already applied'}
    for spec in removed:
        item = existing.get(spec['uuid'])
        if item is None or not _matches(board, item, spec):
            raise ValueError('Changed original radio TX route')
    candidates = []
    for spec in added:
        net = board.FindNet(spec['net'])
        if not net or net.GetNetCode() == 0:
            raise ValueError('Missing reviewed radio net')
        if spec['type'] == 'PCB_VIA':
            item = pcbnew.PCB_VIA(board)
            item.SetPosition(point(spec['position']))
            item.SetWidth(pcbnew.FromMM(spec['diameter_mm']))
            item.SetDrill(pcbnew.FromMM(spec['drill_mm']))
            item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        else:
            item = pcbnew.PCB_TRACK(board)
            item.SetStart(point(spec['start']))
            item.SetEnd(point(spec['end']))
            item.SetWidth(pcbnew.FromMM(spec['width_mm']))
            item.SetLayer(board.GetLayerID(spec['layer']))
        item.SetNet(net)
        item.SetLocked(spec['locked'])
        item.SetUuid(pcbnew.KIID(spec['uuid']))
        candidates.append(item)
    for spec in removed:
        board.Delete(existing[spec['uuid']])
    for item in candidates:
        board.Add(item)
    board.BuildConnectivity()
    return {'applied': True, 'added': len(added), 'removed': len(removed),
            'zones_require_refill': True, 'native_drc_required': True}
