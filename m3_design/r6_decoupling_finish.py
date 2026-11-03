#!/usr/bin/env python3
"""Place C100 beside the camera UART translator and replay its reviewed local repair."""
import json
from pathlib import Path

import pcbnew
from r6_gps_finish import _point, _record

PACKET = Path(__file__).parent / 'assembly_review/sources/r6_decoupling_packet.json'


def footprint_record(board, fp):
    return dict(ref=fp.GetReference(), uuid=fp.m_Uuid.AsString(), value=fp.GetValue(),
                footprint=str(fp.GetFPID().GetLibItemName()), layer=board.GetLayerName(fp.GetLayer()),
                position_nm=[fp.GetPosition().x, fp.GetPosition().y], rotation=fp.GetOrientationDegrees(),
                parts={f.GetName(): f.GetText() for f in fp.GetFields()
                       if f.GetName() in ('LCSC', 'LCSC Part', 'Manufacturer', 'Manufacturer Part')},
                pads=sorted([dict(number=p.GetNumber(), net=p.GetNetname(),
                                  position_nm=[p.GetPosition().x, p.GetPosition().y],
                                  size_nm=[p.GetSize().x, p.GetSize().y],
                                  layers=p.GetLayerSet().FmtHex(), attribute=p.GetAttribute(),
                                  shape=p.GetShape()) for p in fp.Pads()], key=lambda p: p['number']))


def copper_item(board, spec, item=None):
    if spec['type'] == 'PCB_VIA':
        item = item or pcbnew.PCB_VIA(board)
        item.SetViaType(spec['via_type'])
        item.SetLayerPair(board.GetLayerID(spec['top_layer']), board.GetLayerID(spec['bottom_layer']))
        item.SetPosition(_point(spec['position_nm'])); item.SetDrill(spec['drill_nm'])
    elif spec['type'] == 'PCB_TRACK':
        item = item or pcbnew.PCB_TRACK(board)
        item.SetStart(_point(spec['start_nm'])); item.SetEnd(_point(spec['end_nm']))
        item.SetLayer(board.GetLayerID(spec['layer']))
    else:
        raise ValueError('Unexpected decoupling copper type')
    item.SetWidth(spec['width_nm']); item.SetNet(board.FindNet(spec['net']))
    item.SetLocked(spec['locked']); item.SetUuid(pcbnew.KIID(spec['uuid']))
    return item


def repair(board):
    """Reject changed/partial states atomically; caller refills and runs native gates."""
    p = json.loads(PACKET.read_text())
    old, new, adds, removes = p['modified_before'], p['modified_after'], p['added'], p['removed']
    if ({f['ref'] for f in p['footprints_before']} != {'C100', 'R100'}
            or {r['uuid'] for r in old} != {r['uuid'] for r in new}
            or any(r['net'] not in {'3V3', 'GND', 'CAM_RX_WIRE', 'CAM_RX_BUFFER', 'GPS_RX_MCU'}
                   for r in old + new + adds + removes)):
        raise ValueError('Unexpected camera decoupling packet scope')
    existing = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    if len(existing) != len(list(board.GetTracks())):
        raise ValueError('Duplicate copper UUIDs')
    ids = [r['uuid'] for r in adds + old + removes]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate camera packet UUIDs')
    for spec in p['anchors']:
        fp = board.FindFootprintByReference(spec['ref'])
        pad = fp.FindPadByNumber(spec['number']) if fp else None
        if (not pad or pad.GetNetname() != spec['net'] or
                pad.GetPosition() != _point(spec['position_nm']) or
                pad.GetLayerSet().FmtHex() != spec['layers']):
            raise ValueError('Camera decoupling anchor changed')
    def records_match(specs):
        return all(s['uuid'] in existing and _record(board, existing[s['uuid']]) == s for s in specs)
    def footprints_match(specs):
        return all((fp := board.FindFootprintByReference(s['ref'])) is not None and
                   footprint_record(board, fp) == s for s in specs)
    before = (records_match(old + removes) and not any(s['uuid'] in existing for s in adds)
              and footprints_match(p['footprints_before']))
    after = (records_match(new + adds) and not any(s['uuid'] in existing for s in removes)
             and footprints_match(p['footprints_after']))
    if after:
        return dict(applied=False, skipped='already applied')
    if not before:
        raise ValueError('Changed or partial camera decoupling transition')
    for spec in adds + new:
        if not board.FindNet(spec['net']):
            raise ValueError('Missing decoupling net')
    candidates = [copper_item(board, s) for s in adds]
    untouched = {key: _record(board, item) for key, item in existing.items() if key not in ids}
    for spec in removes:
        board.Delete(existing[spec['uuid']])
    for spec in new:
        copper_item(board, spec, existing[spec['uuid']])
    for spec in p['footprints_after']:
        fp = board.FindFootprintByReference(spec['ref'])
        if fp.IsFlipped() != (spec['layer'] == 'B.Cu'):
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetOrientationDegrees(spec['rotation']); fp.SetPosition(_point(spec['position_nm']))
        fp.Reference().SetVisible(False)
    for item in candidates:
        board.Add(item)
    board.BuildConnectivity()
    assert footprints_match(p['footprints_after'])
    assert all(_record(board, existing[key]) == value for key, value in untouched.items())
    return dict(applied=True, added=len(adds), removed=len(removes), modified=len(new),
                moved_footprints=['C100', 'R100'], zones_require_refill=True, native_drc_required=True)
