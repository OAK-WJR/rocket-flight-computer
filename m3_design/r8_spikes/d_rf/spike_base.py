#!/usr/bin/env python3
"""Spike (d) scratch base board: R7 (431025d) with the R8 netlist, the seed placement and only the rigid copper.

usage: <KiCad python3> -I spike_base.py R7.kicad_pcb schematic.net.xml seed.tsv out.kicad_pcb [--place extra.tsv]

What it does (deterministic, scratch only; the real build is r8_build.sh, step 4 onwards):
  1. Records the rigid copper of R7 with check_r8's own definitions (D15): the CH1 block copper, the strip RF copper
     and the strip GND vias and track (the fence row at FENCE_Y is not rigid, D16). Every other track and via goes.
  2. Gives every pad its R8 net from schematic.net.xml (as r8_sch_check.apply_netlist does).
  3. Removes TH1-TH3 (D8).
  4. Places every other part from the seed table (partial/b0_place_final.tsv), then the rows of --place (later rows
     win). Rigid parts (check_r8 STRIP_PARTS, CH1_PARTS, J1, J122) must already sit where the seed says (to its 0.01 mm
     rounding); they are asserted, never moved. The IMU_* / BARO_* rule areas move with U4 / U5.
  5. Zones: keeps the strip rule areas, PYRO_BLOCK, the IMU / BARO areas and R7's whole-board GND pours on F.Cu, B.Cu
     and In1 (their settings reproduce the strip's coplanar ground, D15 strip_gcpw). In2 becomes the plan's layout
     for this region (plan_partial section 4): GND under the strip (y 0.3-23.6) and 3V3 from y 23.9 to 66.8; the rest
     of In2 is GND here (the battery-band planes are spike (c)'s). R7's pour trims and J2 contact areas go (J2 moves).
  6. Drops R7's board-level pin-1 dots (silk circles at R7 positions; r8_post redraws silk with the parts).
  7. Fills the zones natively and saves.
"""
import argparse
import csv
import math
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import check_r8  # noqa: E402
import check_r7 as r7  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
RIGID_PARTS = set(check_r8.STRIP_PARTS) | set(check_r8.CH1_PARTS) | {'J1', 'J122'}
KEEP_AREAS = set(check_r8.STRIP_RULE_AREAS) | {'PYRO_BLOCK', 'IMU_body_B', 'IMU_no_internal_tracks', 'BARO_body_B',
                                               'BARO_no_inter_row_tracks'}
# R6_BAT_IN_crossbar_F (battery band, y 103.6-115.5, far from the strip) stays as a stand-in for the R8 board's own
# F.Cu power pours: measured on R7, a native refill with no non-GND F.Cu pour at all moves the GND_F fill boundary by a
# few µm along the RF lines (fill-path noise), which flips single 0.01 mm samples of check_r8's strip_gcpw profile;
# with any one of R7's four F.Cu power pours present the profile reproduces R7 exactly (RESULT.md, finding F-1)
KEEP_POURS = {'GND_F', 'GND_B', 'GND_In1', 'R6_BAT_IN_crossbar_F'}
IN2 = [  # (name, net, outline, priority) -- plan_partial section 4 for this region
    ('D_GND_In2_strip', 'GND', [(0.3, 0.3), (45.7, 0.3), (45.7, 23.6), (0.3, 23.6)], 7),
    ('D_3V3_In2', '3V3', [(0.3, 23.9), (45.7, 23.9), (45.7, 66.8), (0.3, 66.8)], 2),
    ('D_GND_In2_fwd', 'GND', [(0.3, 67.2), (45.7, 67.2), (45.7, 117.7), (0.3, 117.7)], 1),
]


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def read_place(path):
    rows = {}
    with open(path) as fh:
        for r in csv.DictReader(fh, delimiter='\t'):
            if r['ref'].startswith('#'):
                continue
            rows[r['ref']] = (float(r['x']), float(r['y']), float(r['rot']), r['side'].strip())
    return rows


def netlist_pins(path):
    root = ET.parse(path).getroot()
    pins = {}
    for net in root.findall('./nets/net'):
        for node in net.findall('node'):
            pins[(node.attrib['ref'], node.attrib['pin'])] = net.attrib['name']
    return pins


def rigid_tracks(board):
    """KIIDs of the rigid tracks and vias (check_r8 D15 definitions, R7 board)."""
    keep = list(check_r8.ch1_copper(board))
    keep += [t for t in board.GetTracks() if t.GetNetname() in check_r8.RF_NETS]
    keep += [t for t in board.GetTracks() if t.GetNetname() == 'GNSS_ANT_DC' and
             (t.GetClass() == 'PCB_VIA' or t.GetLayer() == pcbnew.F_Cu)]
    keep += [t for t in board.GetTracks() if t.GetNetname() == 'GND' and (
        (t.GetClass() == 'PCB_VIA' and mm(t.GetPosition().y) < r7.STRIP_Y and
         abs(mm(t.GetPosition().y) - r7.FENCE_Y) >= check_r8.FENCE_ROW) or
        (t.GetClass() != 'PCB_VIA' and mm(t.GetBoundingBox().GetTop()) < r7.STRIP_Y))]
    return {t.m_Uuid.AsString() for t in keep}


def place(board, rows):
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    moved = {}
    for ref, (x, y, rot, side) in sorted(rows.items()):
        f = fps[ref]
        p = f.GetPosition()
        if ref in RIGID_PARTS:
            same = (abs(mm(p.x) - x) < 0.0051 and abs(mm(p.y) - y) < 0.0051 and   # the seed rounds to 0.01 mm
                    (side == 'B') == f.IsFlipped()
                    and abs(((f.GetOrientationDegrees() - rot + 180) % 360) - 180) < 1e-6)
            assert same, f'rigid part {ref} differs from the placement table'
            continue
        moved[ref] = (mm(p.x), mm(p.y))
        if (side == 'B') != f.IsFlipped():
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        f.SetOrientationDegrees(rot)
        f.SetPosition(V(x, y))
    return moved, fps


def zone(board, net, layer, pts, name, priority):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(board.FindNet(net))
    z.SetZoneName(name)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(MM(x), MM(y))
    z.SetAssignedPriority(priority)
    z.SetMinThickness(MM(0.2))
    z.SetLocalClearance(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if net == 'GND' else pcbnew.ZONE_CONNECTION_THERMAL)
    board.Add(z)
    return z


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('r7')
    ap.add_argument('netlist')
    ap.add_argument('seed')
    ap.add_argument('out')
    ap.add_argument('--place', action='append', default=[])
    args = ap.parse_args()
    # the zone filler takes its clearances from the project rules loaded with the board: without m3.kicad_dru beside
    # it the RF lines' 0.25 mm coplanar gap falls back to 0.15 mm and strip_gcpw changes (measured)
    assert Path(args.r7).with_suffix('.kicad_dru').is_file(), 'm3.kicad_dru must sit beside the R7 board'
    board = pcbnew.LoadBoard(args.r7)
    pcbnew.KIID.SeedGenerator(8401)                 # deterministic UUIDs (as r7_pcb.py): byte-identical rebuilds
    keep = rigid_tracks(board)
    for t in list(board.GetTracks()):
        if t.m_Uuid.AsString() not in keep:
            board.Delete(t)
    pins = netlist_pins(args.netlist)
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    for ref in ('TH1', 'TH2', 'TH3'):
        if ref in fps:
            board.Delete(fps.pop(ref))
    for ref, f in fps.items():
        for p in f.Pads():
            name = pins.get((ref, p.GetNumber()))
            if not p.GetNumber() or name is None:
                continue
            net = board.FindNet(name)
            if net is None:
                net = pcbnew.NETINFO_ITEM(board, name)
                board.Add(net)
            p.SetNet(net)
    rows = read_place(args.seed)
    for extra in args.place:
        rows.update(read_place(extra))
    moved, fps = place(board, rows)
    for z in list(board.Zones()):
        name = z.GetZoneName()
        if z.GetIsRuleArea():
            if name not in KEEP_AREAS:
                board.Delete(z)
                continue
            tgt = 'U4' if name.startswith('IMU') else 'U5' if name.startswith('BARO') else None
            if tgt and tgt in moved:
                ox, oy = moved[tgt]
                nx, ny = rows[tgt][:2]
                z.Move(V(nx - ox, ny - oy))
        elif name not in KEEP_POURS:
            board.Delete(z)
    # R7's board-level pin-1 dots (silk circles) belong to R7 positions; r8_post redraws them with their parts
    for d in list(board.GetDrawings()):
        if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) and isinstance(d, pcbnew.PCB_SHAPE) and \
                d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            board.Delete(d)
    for name, net, pts, pri in IN2:
        zone(board, net, pcbnew.In2_Cu, pts, name, pri)
    board.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(board).Fill(board.Zones()), 'native zone fill failed'
    # Save the board only (aSkipSettings): saving through the API rewrites the project file with KiCad's defaults
    # (netclass clearance 0.2 mm, no minimum clearance) when the output sits in another folder, and the next load then
    # fills and checks with the wrong rules (measured). The project files are copied from the input instead.
    out = Path(args.out)
    assert pcbnew.SaveBoard(str(out), board, True), 'save failed'
    for ext in ('.kicad_pro', '.kicad_dru'):
        if Path(args.r7).with_suffix(ext).resolve() != out.with_suffix(ext).resolve():
            shutil.copyfile(Path(args.r7).with_suffix(ext), out.with_suffix(ext))
    print('saved', args.out, 'rigid tracks kept', len(keep))


if __name__ == '__main__':
    main()
