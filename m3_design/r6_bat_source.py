#!/usr/bin/env python3
"""Guarded battery-switch source route through the reviewed CAM_TX window."""
import pcbnew

from r6_port_finish import fingerprint, item_for, point

CAM_WINDOW = {'4ec6310c-f481-48ac-9ccc-65827d973409': ((43.133, 24.8675), (42.133, 25.8675)),
 'a063e4b5-a523-4741-93e9-82157d442f72': ((43.833, 24.8675), (43.133, 24.8675)),
 'c1086652-0f1e-42c2-aa06-941973f10350': ((44.933, 25.9675), (43.833, 24.8675))}

PATHS = [('B.Cu', [[20.46, 92.4], [25.96, 86.9], [31.46, 86.9]]),
 ('F.Cu', [[31.46, 86.9], [38.86, 79.5], [38.86, 75.6], [42.86, 71.6], [42.86, 62.9]]),
 ('B.Cu', [[42.86, 62.9], [45.26, 60.5], [45.26, 43.6], [44.76, 43.1]]),
 ('F.Cu', [[44.76, 43.1], [45.4, 42.46], [45.4, 34.24], [43.76, 32.6], [42.96, 32.6], [42.56, 33.0]]),
 ('In2.Cu', [[42.56, 33.0], [42.76, 32.8], [42.76, 22.4], [41.36, 21.0]]),
 ('B.Cu',
  [[41.36, 21.0],
   [40.16, 19.8],
   [40.16, 18.7],
   [39.86, 18.4],
   [39.26, 18.4],
   [38.26, 17.4],
   [38.26, 15.6],
   [37.66, 15.0]]),
 ('In2.Cu', [[37.66, 15.0], [37.66, 8.5], [34.46, 5.3]]),
 ('B.Cu', [[34.46, 5.3], [34.46, 3.0], [34.26, 2.8], [29.16, 2.8], [26.06, 5.9]]),
 ('In2.Cu', [[26.06, 5.9], [21.36, 5.9]]),
 ('B.Cu', [[21.36, 5.9], [17.66, 5.9], [17.16, 6.4], [17.125, 6.435], [17.125, 6.45]])]

VIAS = [[31.46, 86.9],
 [42.86, 62.9],
 [44.76, 43.1],
 [42.56, 33.0],
 [41.36, 21.0],
 [37.66, 15.0],
 [34.46, 5.3],
 [26.06, 5.9],
 [21.36, 5.9]]

def repair(board):
    """Close BAT_SW_SOURCE without changing power copper; caller refills and runs DRC."""
    pads = []
    for ref, number, xy in (('J1', '3', (20.46, 92.4)), ('R80', '2', (17.125, 6.45))):
        fp = board.FindFootprintByReference(ref)
        pad = fp.FindPadByNumber(number) if fp else None
        if (not pad or pad.GetNetname() != 'BAT_SW_SOURCE' or
                pad.GetPosition() != point(xy) or not pad.IsOnLayer(pcbnew.B_Cu)):
            raise ValueError(f'{ref}.{number}: battery-switch pad/net/position changed')
        pads.append(pad)
    existing = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    if len(existing) != len(list(board.GetTracks())):
        raise ValueError('Duplicate copper UUIDs')
    window = []
    for key, (a, c) in CAM_WINDOW.items():
        t = existing.get(key)
        if (not t or t.GetClass() != 'PCB_TRACK' or t.GetNetname() != 'CAM_TX_WIRE' or
                t.GetStart() != point(a) or t.GetEnd() != point(c) or
                t.GetWidth() != pcbnew.FromMM(.15) or
                t.GetLayer() not in (pcbnew.In1_Cu, pcbnew.In2_Cu)):
            raise ValueError(f'{key}: reviewed CAM_TX window changed')
        window.append(t)
    window_layers = {t.GetLayer() for t in window}
    if len(window_layers) != 1:
        raise ValueError('Partial CAM_TX window layer change')
    specs = [{'kind': 'via', 'at': xy, 'width': .5, 'drill': .3} for xy in VIAS]
    specs += [{'kind': 'track', 'layer': layer, 'a': a, 'c': c, 'width': .15}
              for layer, points in PATHS for a, c in zip(points, points[1:]) if a != c]
    candidates = [item_for(board, 'battery_source', i, {'net': 'BAT_SW_SOURCE', **spec})
                  for i, spec in enumerate(specs)]
    present = []
    for item in candidates:
        key = item.m_Uuid.AsString()
        if key in existing:
            if fingerprint(board, existing[key]) != fingerprint(board, item):
                raise ValueError('Changed generated battery-switch copper')
            present.append(key)
    report = {'applied': False, 'added': [], 'layer_changes': [],
              'zones_require_refill': False, 'native_drc_required': True}
    if present:
        if len(present) != len(candidates) or window_layers != {pcbnew.In1_Cu}:
            raise ValueError('Partial battery-switch route/window')
        report['skipped'] = 'already applied'
        return report
    board.BuildConnectivity()
    if pads[1].m_Uuid.AsString() in {t.m_Uuid.AsString()
            for t in board.GetConnectivity().GetConnectedItems(pads[0])}:
        report['skipped'] = 'battery-switch source already connected'
        return report
    # Validate every old and generated item before changing copper.
    for item in window:
        if item.GetLayer() != pcbnew.In1_Cu:
            item.SetLayer(pcbnew.In1_Cu)
            report['layer_changes'].append(item.m_Uuid.AsString())
    for item in candidates:
        board.Add(item)
        report['added'].append(item.m_Uuid.AsString())
    board.BuildConnectivity()
    report.update(applied=True, zones_require_refill=True)
    return report
