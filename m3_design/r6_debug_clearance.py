#!/usr/bin/env python3
"""Apply the independently checked J2 contact-clearance repair in memory."""
import argparse
import json
import math
from pathlib import Path
import uuid

import pcbnew

MM, mm = pcbnew.FromMM, pcbnew.ToMM
NAMESPACE = uuid.UUID('e5a06a6e-13fd-4b91-a430-290402a70755')
OLD = {
    '875bf54e-2563-40bd-8909-7c6c08c60050': ((41.72, 61.4217), (41.72, 57.3217)),
    '79916b63-04cc-41ee-ad05-9989d72fcf75': ((41.72, 57.3217), (38.52, 54.1217)),
}
CONTACTS = {
    '1': ((43.635, 59.92), '3V3'), '2': ((42.365, 59.92), 'SWDIO'),
    '3': ((43.635, 58.65), 'NRST'), '4': ((42.365, 58.65), 'SWCLK'),
    '5': ((43.635, 57.38), 'GND'), '6': ((42.365, 57.38), None),
}


def point(position):
    return pcbnew.VECTOR2I(*(MM(value) for value in position))


def coords(p):
    return p.x, p.y


def owned(item, name):
    item.SetUuid(pcbnew.KIID(str(uuid.uuid5(NAMESPACE, name))))
    return item


def signature(item):
    kind = item.GetClass()
    if kind == 'PCB_TRACK':
        return (kind, item.GetNetname(), item.GetLayer(), item.GetWidth(),
                tuple(sorted((coords(item.GetStart()), coords(item.GetEnd())))))
    if kind == 'PCB_VIA':
        return (kind, item.GetNetname(), coords(item.GetPosition()), item.GetWidth(pcbnew.F_Cu),
                item.GetDrill(), item.GetViaType(), item.GetLayerSet().FmtHex())
    outline = item.Outline()
    return (kind, item.GetZoneName(), item.GetIsRuleArea(), item.GetLayerSet().FmtHex(),
            item.GetDoNotAllowTracks(), item.GetDoNotAllowVias(), item.GetDoNotAllowZoneFills(),
            item.GetDoNotAllowPads(), item.GetDoNotAllowFootprints(),
            tuple((outline.HoleCount(i), tuple(sorted(coords(p) for p in outline.Outline(i).CPoints())))
                  for i in range(outline.OutlineCount())))


def track(board, net, layer, width, a, b):
    item = pcbnew.PCB_TRACK(board)
    item.SetNet(board.FindNet(net)); item.SetLayer(layer); item.SetWidth(MM(width))
    item.SetStart(point(a)); item.SetEnd(point(b)); item.SetLocked(True)
    return item


def plan(board):
    items = []
    paths = [
        ('PYRO1_CONT', pcbnew.F_Cu, .15, [(41.72, 61.4217), (41.1, 60.8017)]),
        ('PYRO1_CONT', pcbnew.In2_Cu, .15,
         [(41.1, 60.8017), (40.5, 60.2017), (40.5, 57.5), (41, 57)]),
        ('PYRO1_CONT', pcbnew.F_Cu, .15, [(41, 57), (38.52, 54.52), (38.52, 54.1217)]),
        ('GND', pcbnew.F_Cu, .2, [(43.85, 57.38), (44.75, 57.38)]),
    ]
    for net, layer, width, points in paths:
        for a, b in zip(points, points[1:]):
            item = track(board, net, layer, width, a, b)
            items.append(owned(item, f'track:{signature(item)}'))
    for net, position in [('PYRO1_CONT', (41.1, 60.8017)), ('PYRO1_CONT', (41, 57)),
                          ('GND', (44.75, 57.38))]:
        via = pcbnew.PCB_VIA(board)
        via.SetViaType(pcbnew.VIATYPE_THROUGH); via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetPosition(point(position)); via.SetWidth(MM(.5)); via.SetDrill(MM(.3))
        via.SetNet(board.FindNet(net)); via.SetLocked(True)
        items.append(owned(via, f'via:{net}:{position}'))
    for number, (center, _) in CONTACTS.items():
        name = f'J2_CONTACT_{number}_POUR_CLEARANCE'
        zone = pcbnew.ZONE(board)
        zone.SetIsRuleArea(True); zone.SetLayer(pcbnew.F_Cu); zone.SetZoneName(name)
        zone.SetDoNotAllowTracks(False); zone.SetDoNotAllowVias(False)
        zone.SetDoNotAllowZoneFills(True); zone.SetDoNotAllowPads(False)
        zone.SetDoNotAllowFootprints(False)
        zone.Outline().NewOutline()
        for i in range(64):
            angle = 2 * math.pi * i / 64
            zone.Outline().Append(point((center[0] + .92 * math.cos(angle),
                                         center[1] + .92 * math.sin(angle))))
        items.append(owned(zone, name))
    return items


def repair(board):
    """Guard geometry, replace two sense tracks, add contact pour guards and GND escape.

    Only this helper's deterministic IDs and the two verified old sense segments
    are touched. Pads, footprint keepout, and all other routing stay unchanged.
    A repeated invocation preserves identical items; altered own geometry fails.
    Refill and native DRC are required after applying it to routed CAD.
    """
    fp = board.FindFootprintByReference('J2')
    if (fp is None or fp.IsFlipped() or coords(fp.GetPosition()) != coords(point((43, 58.65)))
            or abs(fp.GetOrientationDegrees() - 90) > .001
            or str(fp.GetFPID().GetLibItemName()) != 'M3_TC2030_IDC_NL'):
        raise ValueError('J2 placement or footprint changed; review the clearance repair')
    for number, (position, net) in CONTACTS.items():
        pad = fp.FindPadByNumber(number)
        if (pad is None or coords(pad.GetPosition()) != coords(point(position))
                or coords(pad.GetSize()) != coords(point((.7874, .7874)))
                or pad.GetShape() != pcbnew.PAD_SHAPE_CIRCLE
                or pad.GetAttribute() != pcbnew.PAD_ATTRIB_CONN
                or not pad.IsOnLayer(pcbnew.F_Cu) or not pad.IsOnLayer(pcbnew.F_Mask)
                or pad.IsOnLayer(pcbnew.F_Paste)
                or (pad.GetNetname() != net if net is not None
                    else not pad.GetNetname().startswith('unconnected-'))):
            raise ValueError(f'J2.{number}: contact geometry or net changed')
    keepouts = list(fp.Zones())
    expected = {coords(point(p)) for p in ((42.365, 57.38), (42.365, 59.92),
                                          (43.635, 59.92), (43.635, 57.38))}
    if (len(keepouts) != 1 or keepouts[0].Outline().OutlineCount() != 1
            or keepouts[0].Outline().HoleCount(0) != 0
            or {coords(p) for p in keepouts[0].Outline().Outline(0).CPoints()} != expected
            or list(keepouts[0].GetLayerSet().Seq()) != [pcbnew.F_Cu]
            or keepouts[0].GetDoNotAllowPads() or not keepouts[0].GetDoNotAllowFootprints()
            or not all((keepouts[0].GetIsRuleArea(), keepouts[0].GetDoNotAllowTracks(),
                        keepouts[0].GetDoNotAllowVias(), keepouts[0].GetDoNotAllowZoneFills()))):
        raise ValueError('J2 central footprint keepout changed')
    planned = plan(board)
    existing = {item.m_Uuid.AsString(): item for item in list(board.GetTracks()) + list(board.Zones())}
    for item in planned:
        prior = existing.get(item.m_Uuid.AsString())
        if prior is not None and signature(prior) != signature(item):
            raise ValueError('Previously applied J2 repair geometry changed: ' + item.m_Uuid.AsString())
        if item.GetClass() == 'ZONE' and any(z.GetZoneName() == item.GetZoneName()
                and z.m_Uuid.AsString() != item.m_Uuid.AsString() for z in board.Zones()):
            raise ValueError('Unrecognized existing J2 contact guard: ' + item.GetZoneName())
    remove = []
    for key, (a, b) in OLD.items():
        prior = existing.get(key)
        wanted = signature(track(board, 'PYRO1_CONT', pcbnew.F_Cu, .15, a, b))
        if prior is not None and signature(prior) != wanted:
            raise ValueError('Original PYRO1_CONT segment changed: ' + key)
        remove.extend(item for item in board.GetTracks()
                      if item.GetClass() == 'PCB_TRACK' and signature(item) == wanted)
    if not remove and not any(item.m_Uuid.AsString() in existing for item in planned):
        raise ValueError('Neither original PYRO1_CONT segments nor this J2 repair are present')
    for item in remove:
        board.Remove(item)
    added = []
    for item in planned:
        if item.m_Uuid.AsString() not in existing:
            board.Add(item)
            added.append(dict(uuid=item.m_Uuid.AsString(), kind=item.GetClass()))
    board.BuildConnectivity()
    return dict(removed=[item.m_Uuid.AsString() for item in remove], added=added,
                zones_require_refill=bool(remove or added), native_drc_required=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.board.resolve() == args.output.resolve():
        raise SystemExit('Use a distinct output path')
    board = pcbnew.LoadBoard(str(args.board))
    report = repair(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(args.output), board, True)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
