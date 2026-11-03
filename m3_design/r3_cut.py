#!/usr/bin/env python3
"""M3-ASSY-R2 -> R3 board edit: remove the GNSS and cut the board to 46 x 193 mm.

usage: <KiCad python3> m3_design/r3_cut.py [m3_design/assembly_review/m3.kicad_pcb]
KiCad python on macOS: /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3

Only deletes copper and parts; nothing is re-routed (docs/M3_R3.md). In order:
  U6, C33, C34; the GPS_TX/GPS_RX nets; the 15-segment 3V3A branch that fed only U6;
  GND stitching vias forward of y = 186.2 except the 12 strip vias clear of the new
  washers; the In2 GND zone under the GNSS; three silk dots; then moves the forward
  edge to y = 193 and the forward M3 holes from y = 234 to y = 189, trims the three
  full-board GND zones to y = 192.5, relabels the silkscreen revision and refills zones.
Run it once after the schematic edit (GNSS symbols gone, PC6/PC7 no-connect). It is
idempotent: on an R3 board it prints 'already R3' and changes nothing.
"""
import math, sys
import pcbnew

PCB = sys.argv[1] if len(sys.argv) > 1 else 'm3_design/assembly_review/m3.kicad_pcb'
mm, MM = pcbnew.ToMM, pcbnew.FromMM
L, HOLE_Y = 193.0, 189.0
HOLES = [(4, 189), (42, 189)]
GNSS_REFS = ('U6', 'C33', 'C34')
GPS_NETS = ('GPS_TX', 'GPS_RX')
# 3V3A segments north of via e5896d17 (36.5, 172.3) that reach only C33/C34/U6
BRANCH = {'e2bebe9e-2897-436e-b9c9-9eb28def40cd', '6c319d76-631b-4a43-a355-fe5f61f3df6c', '4b7e83b5-aaad-48d9-8269-6467dd54722c',
          '267bd46d-296e-46ce-9de3-0cdfe716ee75', '77a8e9ce-eaa0-43c4-a2ef-6e915e9bdca2', '86dc0720-56d7-4002-8a02-38a23edf4f7b',
          '402e80c4-9084-401c-8ddb-456a663291ee', '99337630-f7da-4779-8076-b6ec8fb09c57', '6ad385f1-320d-4c7f-8b0e-23a33b970987',
          '2ab14c4c-4945-4b11-8dfc-20d868fa4e5e', 'be6c45cc-3d53-4c5c-914f-106df8b4120d', '274874a7-6f9b-4427-a3a9-d197a25cb7b4',
          'f37a223a-2a06-47f6-bd21-3368b2555803', '38b9c102-8e6e-4df2-aa41-09624dea6d66', '01386c30-91ed-4467-a4ac-93fb45c34a98'}
SILK_DOTS = {'3e8a1039-a195-4d28-af88-6c018574d3cf', '63049966-dc0b-4e85-873a-995c5d498e0e', '98273fb6-06fd-422d-b337-4e9e14796477'}
GNSS_PLANE = '518402e7-8b43-449f-be00-e6da5ba6b2ca'          # In2 GND, y 188-237.5
FULL_ZONES = {'65e63ba0-78c1-4043-8833-73f266e57c81', '5d6c1dca-a0a2-43f9-ab3b-adbe07f3996e', 'ab940f04-9923-4074-892b-28792eea1d5f'}
EDGE_LEFT, EDGE_RIGHT, EDGE_FWD = '6c3b56e1-eb1a-4f3d-b8c7-d8e69d9eced2', 'e18d4c14-4c46-46e9-8ff9-e3dd710606ac', '7918dcc2-5237-4651-aa7f-c6312000ad29'
SILK_TEXT = {'M3-ASSY-R2 - DATA': 'M3-ASSY-R3 - DATA', '2S INPUT / M3-ASSY-R2': '2S INPUT / M3-ASSY-R3'}
M3_HOLES = {(4, 4), (42, 4), (4, 88), (42, 88), (4, 128), (42, 128), (4, 189), (42, 189)}


def edge_items(b):
    return [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]


def edge_max_y(b):
    ys = []
    for d in edge_items(b):
        if d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            ys += [mm(d.GetStart().y), mm(d.GetEnd().y)]
    return max(ys)


def keep_strip_via(x, y):
    """Forward GND stitching via that may stay: inside the new board and clear of both new washers."""
    return y <= 192.0 and all(math.hypot(x - hx, y - hy) - 0.3 >= 3.5 for hx, hy in HOLES)


def cut(b):
    dele, count = [], {}

    def add(item, kind):
        dele.append(item); count[kind] = count.get(kind, 0) + 1
    for f in b.GetFootprints():
        if f.GetReference() in GNSS_REFS:
            add(f, 'footprint')
    for t in b.GetTracks():
        net, is_via = t.GetNetname(), t.Type() == pcbnew.PCB_VIA_T
        if net in GPS_NETS:
            add(t, 'gps_via' if is_via else 'gps_track')
        elif t.m_Uuid.AsString() in BRANCH:
            add(t, '3v3a_branch')
        elif net == 'GND' and is_via:
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            if y > 186.2 and not keep_strip_via(x, y):
                add(t, 'gnd_via')
        elif net == 'GND' and min(mm(t.GetStart().y), mm(t.GetEnd().y)) > 192.5:
            add(t, 'gnd_track')
    for d in b.GetDrawings():
        if d.m_Uuid.AsString() in SILK_DOTS:
            add(d, 'silk_dot')
    for z in b.Zones():
        if z.m_Uuid.AsString() == GNSS_PLANE:
            add(z, 'zone')
    for item in dele:
        b.Delete(item)
    print('deleted', count)

    for d in edge_items(b):
        u = d.m_Uuid.AsString()
        if u == EDGE_LEFT:
            d.SetStart(pcbnew.VECTOR2I(MM(0), MM(L)))
        elif u == EDGE_RIGHT:
            d.SetEnd(pcbnew.VECTOR2I(MM(46), MM(L)))
        elif u == EDGE_FWD:
            d.SetStart(pcbnew.VECTOR2I(MM(46), MM(L))); d.SetEnd(pcbnew.VECTOR2I(MM(0), MM(L)))
        elif d.GetShape() == pcbnew.SHAPE_T_CIRCLE and abs(mm(d.GetCenter().y) - 234) < 1e-6:
            d.Move(pcbnew.VECTOR2I(0, MM(HOLE_Y - 234)))
    for z in b.Zones():
        if z.m_Uuid.AsString() in FULL_ZONES:
            ol = z.Outline()
            for j in range(ol.Outline(0).PointCount()):
                p = ol.CVertex(j)
                if abs(mm(p.y) - 237.5) < 1e-6:
                    ol.SetVertex(j, pcbnew.VECTOR2I(p.x, MM(L - 0.5)))
    for d in b.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() in SILK_TEXT:
            d.SetText(SILK_TEXT[d.GetText()])
    # Same net names "Update PCB from Schematic" gives the no-connect pins (schematic parity)
    u1 = next(f for f in b.GetFootprints() if f.GetReference() == 'U1')
    for num, name in (('63', 'unconnected-(U1-PC6-Pad63)'), ('64', 'unconnected-(U1-PC7-Pad64)')):
        net = pcbnew.NETINFO_ITEM(b, name); b.Add(net)
        for pad in u1.Pads():
            if pad.GetNumber() == num:
                pad.SetNet(net)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())


def self_check(b):
    refs = {f.GetReference() for f in b.GetFootprints()}
    assert not refs & set(GNSS_REFS), 'GNSS footprint left'
    assert all(mm(f.GetPosition().y) < 186.2 for f in b.GetFootprints()), 'footprint forward of the logic block'
    assert not [t for t in b.GetTracks() if t.GetNetname() in GPS_NETS], 'GPS copper left'
    segs = [d for d in edge_items(b) if d.GetShape() == pcbnew.SHAPE_T_SEGMENT]
    pts = {(round(mm(p.x), 3), round(mm(p.y), 3)) for d in segs for p in (d.GetStart(), d.GetEnd())}
    assert pts == {(0, 0), (46, 0), (46, L), (0, L)}, f'outline {sorted(pts)}'
    circles = {(round(mm(d.GetCenter().x), 3), round(mm(d.GetCenter().y), 3)): round(mm(d.GetRadius()), 3)
               for d in edge_items(b) if d.GetShape() == pcbnew.SHAPE_T_CIRCLE}
    m3 = {c for c in circles if c not in ((24, 85.6), (26.5, 68.2))}
    assert m3 == M3_HOLES and all(circles[c] == 1.6 for c in m3), f'holes {sorted(circles)}'
    texts = {d.GetText() for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT)}
    assert set(SILK_TEXT.values()) <= texts, 'silkscreen revision not updated'
    print('self-check OK')


def main():
    b = pcbnew.LoadBoard(PCB)
    if 'U6' not in {f.GetReference() for f in b.GetFootprints()} and abs(edge_max_y(b) - L) < 1e-6:
        print('already R3'); self_check(b); return
    cut(b)
    self_check(b)
    pcbnew.SaveBoard(PCB, b)
    print('saved', PCB)


if __name__ == '__main__':
    main()
