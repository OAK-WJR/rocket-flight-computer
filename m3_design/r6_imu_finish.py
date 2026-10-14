#!/usr/bin/env python3
"""Replay the R6 PE1 polled IMU status connection.

PE1 is an input only: EXTI1 remains assigned to PD1 power monitoring. The caller
must synchronize the schematic/firmware, refill zones, and run native DRC.
"""
import pcbnew
from r6_port_finish import fingerprint, item_for, point

OLD = {
    '49cd1cef-2a3f-4783-aaf0-5b0e191576c8': ('PCB_TRACK', 'IMU_INT1', 'F.Cu', (20.85,29.45), (21.15,29.75), .15, None),
    'a7cc48e7-f9fb-4fcc-8a39-8922232207c4': ('PCB_TRACK', 'IMU_INT1', 'F.Cu', (20.85,27.95), (20.85,29.45), .15, None),
    'caa4bc3c-b304-4485-9c81-f7d10acd2e21': ('PCB_VIA', 'IMU_INT1', 'F.Cu', (21.15,29.75), (21.15,29.75), .5, .3),
}
PATHS = [
    ('F.Cu', [(26.85,43.05),(26.85,44.1),(26.3,44.65)]),
    ('B.Cu', [(26.3,44.65),(26.8,45.15),(26.8,46.35),(26.7,46.45)]),
    ('F.Cu', [(26.7,46.45),(26.85,46.6),(26.85,47.35),(26.65,47.55),(26.65,48.25)]),
    ('B.Cu', [(26.65,48.25),(27.25,48.85),(27.25,49.25),(26.55,49.95),(26.55,51.45),
              (28.75,53.65),(28.75,55.7),(33.05,60),(33.7,60),(34.3,59.4),
              (34.65,59.4),(34.8,59.55),(34.79,59.55)]),
]
VIAS = [(26.3,44.65),(26.7,46.45),(26.65,48.25)]
NC = 'unconnected-(U1-PE10-Pad40)'


def repair(board):
    """Move IMU status to polled PE1; caller refills/checks and preserves PD1 EXTI1."""
    pads = []
    for ref, number, xy, layer in (('U1','40',(20.85,27.95),pcbnew.F_Cu),
                                  ('U1','98',(26.85,43.05),pcbnew.F_Cu),
                                  ('U4','4',(34.79,59.55),pcbnew.B_Cu)):
        fp = board.FindFootprintByReference(ref)
        pad = fp.FindPadByNumber(number) if fp else None
        if not pad or pad.GetPosition()!=point(xy) or not pad.IsOnLayer(layer):
            raise ValueError(f'{ref}.{number}: reviewed IMU pad geometry changed')
        pads.append(pad)
    old_pad, new_pad, sensor = pads
    if sensor.GetNetname()!='IMU_INT1':
        raise ValueError('IMU sensor net changed')
    old_mapping = old_pad.GetNetname()=='IMU_INT1' and new_pad.GetNetname()=='unconnected-(U1-PE1-Pad98)'
    new_mapping = old_pad.GetNetname()==NC and new_pad.GetNetname()=='IMU_INT1'
    if not (old_mapping or new_mapping):
        raise ValueError('Unexpected or partial IMU GPIO mapping')
    for number in ('2', '4', '5', '16', '32'):
        sentinel = board.FindFootprintByReference('U1').FindPadByNumber(number)
        if not sentinel or (sentinel.GetNetname() and not sentinel.GetNetname().startswith('unconnected-')):
            raise ValueError('Actuator sentinel U1.' + number + ' must remain unconnected')
    existing = {t.m_Uuid.AsString():t for t in board.GetTracks()}
    if len(existing)!=len(list(board.GetTracks())):
        raise ValueError('Duplicate copper UUIDs')
    present_old = [key for key in OLD if key in existing]
    if present_old and len(present_old)!=len(OLD):
        raise ValueError('Partial old PE10 escape')
    for key in present_old:
        item = existing[key]
        if fingerprint(board, item) != OLD[key]:
            raise ValueError('Changed old PE10 escape')
        if item.GetClass() == 'PCB_VIA' and (
                item.TopLayer() != pcbnew.F_Cu or item.BottomLayer() != pcbnew.B_Cu or
                item.GetViaType() != pcbnew.VIATYPE_THROUGH):
            raise ValueError('Changed old PE10 via layers/type')
    specs = [{'kind':'via','at':xy,'width':.5,'drill':.3}for xy in VIAS]
    specs += [{'kind':'track','layer':layer,'a':a,'c':c,'width':.15}
              for layer,pts in PATHS for a,c in zip(pts,pts[1:])]
    candidates = [item_for(board,'imu_pe1_finish',i,{'net':'IMU_INT1',**spec})
                  for i,spec in enumerate(specs)]
    present = []
    for item in candidates:
        key=item.m_Uuid.AsString()
        if key in existing:
            if fingerprint(board,existing[key])!=fingerprint(board,item):
                raise ValueError('Changed generated PE1 IMU copper')
            if item.GetClass()=='PCB_VIA' and (existing[key].TopLayer()!=pcbnew.F_Cu or
                                             existing[key].BottomLayer()!=pcbnew.B_Cu or
                                             existing[key].GetViaType()!=pcbnew.VIATYPE_THROUGH):
                raise ValueError('Changed generated PE1 IMU via layers')
            present.append(key)
    report={'applied':False,'added':[],'removed':[],'zones_require_refill':False,
            'native_drc_required':True,'schematic_and_firmware_sync_required':True,'imu_status_mode':'PE1_INPUT_POLLING_ONLY','exti1_owner':'PD1'}
    if present:
        if len(present)!=len(candidates) or not new_mapping or present_old:
            raise ValueError('Partial PE1 route/mapping transition')
        report['skipped']='already applied';return report
    if old_mapping and not present_old:
        raise ValueError('Old PE10 route missing before GPIO transition')
    if new_mapping and present_old:
        raise ValueError('Partial PE1 mapping with old PE10 copper')
    board.BuildConnectivity()
    if new_mapping and sensor.m_Uuid.AsString() in {t.m_Uuid.AsString()
            for t in board.GetConnectivity().GetConnectedItems(new_pad)}:
        report['skipped']='IMU already connected on PE1';return report
    # All guarded states are checked before mutating nets or copper.
    nc=board.FindNet(NC)
    if not nc:
        nc=pcbnew.NETINFO_ITEM(board,NC);board.Add(nc)
    new_pad.SetNet(sensor.GetNet());old_pad.SetNet(nc)
    for key in present_old:
        board.Delete(existing[key]);report['removed'].append(key)
    for item in candidates:
        board.Add(item);report['added'].append(item.m_Uuid.AsString())
    board.BuildConnectivity();report.update(applied=True,zones_require_refill=True)
    return report
