#!/usr/bin/env python3
"""R8 spike 3(b) scratch base board (KiCad Python): R7 board -> R8 nets -> rigid copper only -> seed placement.

usage: <KiCad python3> -I make_base.py R7_BOARD R8_NETLIST SEED_TSV OUT_BOARD

1. every netlist pad takes its R8 net (schematic.net.xml, as r8_sch_check.apply_netlist);
2. TH1-TH3 removed (D8);
3. every track and via that is not rigid R7 copper is deleted. Rigid = check_r8's groups (D15): the CH1 copper
   (check_r8.ch1_copper), the RF-line copper with GNSS_ANT_DC's via and F.Cu, and every strip GND via / track
   (y < STRIP_Y; the fence row is kept too, it is far from the RF lines);
4. the movable parts go to the Strategy B seed placement (partial/b0_place_final.tsv; U1 at rotation 0, (23, 45)),
   the IMU / baro rule areas follow U4 / U5 (as partial/b0_place.py);
5. zones: R7's GND_F, GND_B and GND_In1 pours, its four F.Cu power pours (R7_FCU_POURS, see there) and the rigid
   rule areas stay; every other R7 zone goes (its parts
   moved); In2 gets a placeholder plane model (GND everywhere, the strip GND, 3V3 over y 23.9-66.8 as plan_partial
   section 3, RAW_ACT only under J122's middle column). Spike (c) owns the real In2 map.
Nothing is filled here (servo_route.py fills once, after its copper).
"""
import csv
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

TOOLS = Path(__file__).resolve().parents[3] / 'tools'
sys.path.insert(0, str(TOOLS))
import check_r7 as r7                      # noqa: E402
import check_r8                            # noqa: E402

MM, mm = pcbnew.FromMM, pcbnew.ToMM
KEEP_ZONES = ('GND_F', 'GND_B', 'GND_In1', 'U30_KEEPOUT', 'U31_KEEPOUT', 'R7_J30_launch_In1', 'R7_J31_launch_In1',
              'PYRO_BLOCK')
# R7's four F.Cu power pours stay (far from the strip and from the servo interface): deleting all four together moves 13
# of the GCPW profile's 0.01 mm samples by one step (zone-fill numerical noise; any one alone moves none), which
# changes the strip_gcpw digest without touching the strip. SPIKE_DROP_FCU_POURS=1 drops them to show that effect.
R7_FCU_POURS = ('R6_RAW_ACT_F', 'BAT_IN_F', 'RAW_ACT_F', 'R6_BAT_IN_crossbar_F')
MOVE_WITH = {'IMU': 'U4', 'BARO': 'U5'}      # R7 rule areas tied to a part (b0_place.py)
DELETE = ('TH1', 'TH2', 'TH3')
RIGID_PARTS = set(check_r8.STRIP_PARTS) | set(check_r8.CH1_PARTS) | {'J122', 'J1'}   # never re-placed (D15): the
# seed TSV rounds to 0.01 mm (L30 12.3875 -> 12.39), which alone would break the strip_parts / strip_gcpw digests


def v(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def netlist_pins(path):
    pins = {}
    for net in ET.parse(path).getroot().findall('./nets/net'):
        for node in net.findall('node'):
            pins[(node.attrib['ref'], node.attrib['pin'])] = net.attrib['name']
    return pins


def apply_nets(b, pins):
    changed = 0
    for f in b.GetFootprints():
        for p in f.Pads():
            key = (f.GetReference(), p.GetNumber())
            if not p.GetNumber() or key not in pins:
                continue
            net = b.FindNet(pins[key])
            if net is None:
                net = pcbnew.NETINFO_ITEM(b, pins[key])
                b.Add(net)
            if p.GetNetname() != pins[key]:
                p.SetNet(net)
                changed += 1
    return changed


def rigid_copper(b):
    """UUIDs of the rigid tracks / vias (check_r8.rigid_groups' selection; strip GND incl. the fence row)."""
    keep = {t.m_Uuid.AsString() for t in check_r8.ch1_copper(b)}
    for t in b.GetTracks():
        n = t.GetNetname()
        via = t.GetClass() == 'PCB_VIA'
        if n in check_r8.RF_NETS or (n == 'GNSS_ANT_DC' and (via or t.GetLayer() == pcbnew.F_Cu)):
            keep.add(t.m_Uuid.AsString())
        elif n == 'GND' and ((via and mm(t.GetPosition().y) < r7.STRIP_Y) or
                             (not via and mm(t.GetBoundingBox().GetTop()) < r7.STRIP_Y)):
            keep.add(t.m_Uuid.AsString())
    return keep


def place(b, rows):
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    old = {}
    for r in rows:
        if r['ref'] in RIGID_PARTS:
            continue
        f = fps[r['ref']]
        old[r['ref']] = (mm(f.GetPosition().x), mm(f.GetPosition().y))
        if (r['side'] == 'B') != f.IsFlipped():
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        f.SetOrientationDegrees(float(r['rot']))
        f.SetPosition(v(float(r['x']), float(r['y'])))
    return old


def zone(b, net, layer, pts, name, prio, conn, clearance=0.25, minw=0.2):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet(net))
    z.SetZoneName(name)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(MM(x), MM(y))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(MM(clearance))
    z.SetMinThickness(MM(minw))
    z.SetPadConnection(conn)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    b.Add(z)
    return z


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def in2_model(b):
    In2 = pcbnew.In2_Cu
    T, F = pcbnew.ZONE_CONNECTION_THERMAL, pcbnew.ZONE_CONNECTION_FULL
    zone(b, 'GND', In2, rect(0.3, 0.3, 45.7, 117.7), 'SPIKE_GND_In2', 0, T)
    zone(b, 'GND', In2, rect(0.3, 0.3, 45.7, 23.6), 'SPIKE_GND_In2_strip', 7, F)
    zone(b, '3V3', In2, rect(0.3, 23.9, 45.7, 66.8), 'SPIKE_3V3_In2', 2, T)
    zone(b, 'RAW_ACT', In2, rect(21.4, 70.3, 24.3, 81.1), 'SPIKE_RAW_ACT_In2_J122', 3, F, 0.3, 0.3)


def main(src, netlist, seed, dst):
    pcbnew.KIID.SeedGenerator(8321)               # deterministic UUIDs (byte-identical rebuilds)
    b = pcbnew.LoadBoard(src)
    print('nets changed', apply_nets(b, netlist_pins(netlist)))
    for ref in DELETE:
        b.Delete(b.FindFootprintByReference(ref))
    keep = rigid_copper(b)
    kill = [t for t in b.GetTracks() if t.m_Uuid.AsString() not in keep]
    for t in kill:
        b.Delete(t)
    print('tracks/vias kept', len(keep), 'removed', len(kill))
    rows = list(csv.DictReader(open(seed), delimiter='\t'))
    old = place(b, rows)
    pos = {r['ref']: (float(r['x']), float(r['y'])) for r in rows}
    for z in list(b.Zones()):
        name = z.GetZoneName()
        tgt = next((t for k, t in MOVE_WITH.items() if name.startswith(k)), None)
        if tgt and z.GetIsRuleArea():
            (ox, oy), (nx, ny) = old[tgt], pos[tgt]
            z.Move(v(nx - ox, ny - oy))
        elif name not in KEEP_ZONES and (name not in R7_FCU_POURS or os.environ.get('SPIKE_DROP_FCU_POURS')):
            b.Delete(z)
    in2_model(b)
    b.Save(dst)
    print('saved', dst, 'placed', len(rows))


if __name__ == '__main__':
    main(*sys.argv[1:5])
