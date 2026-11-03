#!/usr/bin/env python3
"""Apply the reviewed AUX route and its local signal/ground crossovers."""
import json
from pathlib import Path

import pcbnew

PACKET = Path(__file__).parent / 'assembly_review/sources/r6_aux_finish_packet.json'
PADS = [('R202', '1', 'GPS_RX_MCU', (38.77, 45)),
        ('R196', '1', 'RADIO_M0_MCU', (38.77, 31.5)),
        ('R203', '1', 'RADIO_M0_MCU', (34, 32.93)),
        ('D130', '1', 'RADIO_M0_MCU', (35.55, 35.65)),
        ('U1', '25', 'SERVO4_MCU', (29.4, 29.5)),
        ('U1', '65', 'RADIO_M0_MCU', (14.3, 36.5)),
        ('U1', '67', 'RADIO_AUX_MCU', (14.3, 37.5)),
        ('U1', '69', 'GPS_RX_MCU', (14.3, 38.5)),
        ('D131', '1', 'RADIO_AUX_MCU', (35.55, 45.65)),
        ('D131', '4', 'GPS_RX_MCU', (37.45, 43.35)),
        ('R200', '1', 'RADIO_AUX_MCU', (38.77, 37.5)),
        ('D121', '6', 'SERVO4_MCU', (31.05, 65.55)),
        ('R153', '1', 'SERVO4_MCU', (26.1, 81.4)),
        ('R157', '1', 'SERVO4_MCU', (26.1, 83.07))]


def point(xy):
    return pcbnew.VECTOR2I(*(round(v * pcbnew.FromMM(1)) for v in xy))


def _matches(board, item, spec):
    if (item.GetClass() != spec['type'] or item.GetNetname() != spec['net']
            or item.IsLocked() != spec['locked']):
        return False
    if spec['type'] == 'PCB_VIA':
        return (item.GetPosition() == point(spec['position'])
                and item.GetWidth(pcbnew.F_Cu) == pcbnew.FromMM(spec['diameter_mm'])
                and item.GetDrill() == pcbnew.FromMM(spec['drill_mm'])
                and item.TopLayer() == pcbnew.F_Cu and item.BottomLayer() == pcbnew.B_Cu)
    return (item.GetLayer() == board.GetLayerID(spec['layer'])
            and item.GetStart() == point(spec['start']) and item.GetEnd() == point(spec['end'])
            and item.GetWidth() == pcbnew.FromMM(spec['width_mm']))


def repair(board):
    """Reject changed or partial geometry; caller refills and runs native DRC."""
    packet = json.loads(PACKET.read_text())
    added, removed = packet['added_tracks'], packet['removed_tracks_guard']
    if (packet['pad_changes'] or len(removed) != 7 or len(added) != 70
            or any(s['type'] != 'PCB_TRACK'
                   or (s['net'], s['layer']) not in
                   (('RADIO_M0_MCU', 'B.Cu'), ('SERVO4_MCU', 'In2.Cu'),
                    ('GPS_RX_MCU', 'In2.Cu')) for s in removed)
            or any(s['net'] not in ('RADIO_AUX_MCU', 'RADIO_M0_MCU',
                                    'SERVO4_MCU', 'GPS_RX_MCU', 'GND') for s in added)):
        raise ValueError('Unexpected AUX packet scope')
    grounds = [s for s in added if s['net'] == 'GND']
    if (len(grounds) != 1 or grounds[0]['type'] != 'PCB_TRACK'
            or grounds[0]['layer'] != 'In2.Cu' or grounds[0]['width_mm'] != .25
            or {tuple(grounds[0]['start']), tuple(grounds[0]['end'])}
            != {(19.75, 45.25), (20.65, 46.15)}):
        raise ValueError('Changed reviewed ground bridge')
    existing = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    if len(existing) != len(list(board.GetTracks())):
        raise ValueError('Duplicate copper UUIDs')
    for ref, number, net, xy in PADS:
        fp = board.FindFootprintByReference(ref)
        pad = fp.FindPadByNumber(number) if fp else None
        if not pad or pad.GetNetname() != net or pad.GetPosition() != point(xy):
            raise ValueError(f'{ref}.{number}: reviewed AUX crossover pad changed')
    present = [s for s in added if s['uuid'] in existing]
    for spec in present:
        if not _matches(board, existing[spec['uuid']], spec):
            raise ValueError('Changed reviewed AUX crossover copper')
    if present:
        if len(present) != len(added) or any(s['uuid'] in existing for s in removed):
            raise ValueError('Partial AUX migration')
        return {'applied': False, 'skipped': 'already applied'}
    for spec in removed:
        item = existing.get(spec['uuid'])
        if item is None or not _matches(board, item, spec):
            raise ValueError('Changed original AUX crossover route')
    candidates = []
    for spec in added:
        net = board.FindNet(spec['net'])
        if not net or net.GetNetCode() == 0:
            raise ValueError('Missing reviewed AUX crossover net')
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
