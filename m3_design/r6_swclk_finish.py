#!/usr/bin/env python3
"""Apply the reviewed SWCLK route, preserving its MCU ground-plane crossover."""
import json
from pathlib import Path

import pcbnew

from r6_port_finish import point

PACKET = Path(__file__).parent / 'assembly_review/sources/r6_swclk_finish_packet.json'


def _matches(board, item, spec):
    if item.GetClass() != spec['type'] or item.GetNetname() != spec['net']:
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
    """Fail closed on changed or partial copper. Caller refills and runs native DRC."""
    packet = json.loads(PACKET.read_text())
    existing = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    if len(existing) != len(list(board.GetTracks())):
        raise ValueError('Duplicate copper UUIDs')
    added = packet['added_tracks']
    removed = packet['removed_tracks_guard']
    present = [s for s in added if s['uuid'] in existing]
    for spec in present:
        if not _matches(board, existing[spec['uuid']], spec):
            raise ValueError('Changed reviewed SWCLK copper')
    for ref, number, xy in [('U1', '76', (15.85, 43.05)), ('J2', '4', (42.365, 58.65))]:
        fp = board.FindFootprintByReference(ref)
        pad = fp.FindPadByNumber(number) if fp else None
        if not pad or pad.GetNetname() != 'SWCLK':
            raise ValueError(f'{ref}.{number}: SWCLK assignment changed')
        if pad.GetPosition() != point(xy):
            raise ValueError(f'{ref}.{number}: SWCLK pad moved')
    thermal = packet['pad_changes'][0]
    pad = board.FindFootprintByReference('R128').FindPadByNumber('2')
    if pad.GetNetname() != thermal['net'] or pad.GetPosition() != point(thermal['position']):
        raise ValueError('R128.2 reviewed thermal anchor changed')
    angle = pad.GetThermalSpokeAngle().AsDegrees()
    if present:
        if len(present) != len(added) or any(s['uuid'] in existing for s in removed):
            raise ValueError('Partial SWCLK migration')
        if angle != thermal['thermal_angle_after_deg']:
            raise ValueError('Changed R128.2 thermal angle')
        return {'applied': False, 'skipped': 'already applied'}
    if angle != thermal['thermal_angle_before_deg']:
        raise ValueError('Unexpected R128.2 thermal angle')
    for spec in removed:
        item = existing.get(spec['uuid'])
        if item is None or not _matches(board, item, spec):
            raise ValueError('Changed original SWCLK escape')
    for spec in removed:
        board.Delete(existing[spec['uuid']])
    for spec in added:
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
        item.SetNet(board.FindNet(spec['net']))
        item.SetLocked(spec['locked'])
        item.SetUuid(pcbnew.KIID(spec['uuid']))
        board.Add(item)
    pad.SetThermalSpokeAngle(pcbnew.EDA_ANGLE(thermal['thermal_angle_after_deg'], pcbnew.DEGREES_T))
    return {'applied': True, 'added': len(added), 'removed': len(removed),
            'zones_require_refill': True, 'native_drc_required': True}
