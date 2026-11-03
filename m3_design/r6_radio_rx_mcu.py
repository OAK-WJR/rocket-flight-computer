#!/usr/bin/env python3
"""Reviewed radio receive route and its short local 3V3 neck keeper."""
import pcbnew

from r6_port_finish import fingerprint, item_for, point

ANCHORS = {
    'eb2874e7-be5c-59e0-b595-cdf2cd22f5be': ('RADIO_RX_MCU', (34, 35.2), .5),
    '36c58be0-8106-4247-a25d-2a8e32970b10': ('RADIO_RX_MCU', (17.5, 34.9), .6),
    '263da12e-c07b-46d3-a3dd-7722a6365b21': ('RADIO_TX_MCU', (19.2675, 34.2245), .6),
}
PATHS = [
    ('F.Cu', [(34, 35.2), (33.9, 35.2), (33.1, 34.4), (33.1, 33.9)]),
    ('In1.Cu', [(33.1, 33.9), (31.1, 33.9), (30.9, 34.1), (27.9, 34.1), (27.6, 33.8)]),
    ('F.Cu', [(27.6, 33.8), (27.2, 34.2), (24.2, 34.2), (21.4, 31.4)]),
    ('In2.Cu', [(21.4, 31.4), (19.6, 33.2), (18.6, 33.2)]),
    ('F.Cu', [(18.6, 33.2), (17.5, 34.3), (17.5, 34.9)]),
]
VIAS = [(33.1, 33.9), (27.6, 33.8), (21.4, 31.4), (18.6, 33.2)]
KEEPER = [(18.7, 33.9), (19, 33.6), (19.6, 33.6)]


def repair(board):
    """Add only the reviewed route; caller must refill and run native DRC."""
    pads = []
    for ref, number, xy in (('U1', '64', (14.3, 36)), ('D130', '6', (35.55, 33.35))):
        fp = board.FindFootprintByReference(ref)
        pad = fp.FindPadByNumber(number) if fp else None
        if (not pad or pad.GetNetname() != 'RADIO_RX_MCU' or
                pad.GetPosition() != point(xy) or not pad.IsOnLayer(pcbnew.F_Cu)):
            raise ValueError(f'{ref}.{number}: radio receive pad/net/position changed')
        pads.append(pad)
    existing = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    if len(existing) != len(list(board.GetTracks())):
        raise ValueError('Duplicate copper UUIDs')
    for key, (net, xy, diameter) in ANCHORS.items():
        t = existing.get(key)
        expected = ('PCB_VIA', net, 'F.Cu', xy, xy, diameter, .3)
        if (not t or fingerprint(board, t) != expected or
                t.TopLayer() != pcbnew.F_Cu or t.BottomLayer() != pcbnew.B_Cu):
            raise ValueError(f'{key}: reviewed radio/power-neck anchor changed')
    specs = [{'kind': 'via', 'net': 'RADIO_RX_MCU', 'at': xy, 'width': .5, 'drill': .3}
             for xy in VIAS]
    specs += [{'kind': 'track', 'net': 'RADIO_RX_MCU', 'layer': layer,
               'a': a, 'c': c, 'width': .15}
              for layer, points in PATHS for a, c in zip(points, points[1:])]
    # This 1.024 mm keeper follows the existing In2 supply neck. The new RX via
    # leaves adequate copper clearance but prevents a 0.3 mm-minimum pour neck.
    specs += [{'kind': 'track', 'net': '3V3', 'layer': 'In2.Cu',
               'a': a, 'c': c, 'width': .25} for a, c in zip(KEEPER, KEEPER[1:])]
    candidates = [item_for(board, 'radio_rx_mcu_finish', i, spec)
                  for i, spec in enumerate(specs)]
    present = []
    for item in candidates:
        key = item.m_Uuid.AsString()
        if key in existing:
            if fingerprint(board, existing[key]) != fingerprint(board, item):
                raise ValueError('Changed generated radio receive copper')
            if item.GetClass() == 'PCB_VIA' and (
                    existing[key].TopLayer() != pcbnew.F_Cu or
                    existing[key].BottomLayer() != pcbnew.B_Cu):
                raise ValueError('Changed generated radio receive via layers')
            present.append(key)
    report = {'applied': False, 'added': [], 'zones_require_refill': False,
              'native_drc_required': True}
    if present:
        if len(present) != len(candidates):
            raise ValueError('Partial radio receive route/3V3 keeper')
        report['skipped'] = 'already applied'
        return report
    board.BuildConnectivity()
    if pads[1].m_Uuid.AsString() in {t.m_Uuid.AsString()
            for t in board.GetConnectivity().GetConnectedItems(pads[0])}:
        report['skipped'] = 'radio receive already connected'
        return report
    for item in candidates:
        board.Add(item)
        report['added'].append(item.m_Uuid.AsString())
    board.BuildConnectivity()
    report.update(applied=True, zones_require_refill=True)
    return report
