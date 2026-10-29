#!/usr/bin/env python3
"""R8 spike (a), under U1: scratch board builder (KiCad Python). Scratch only; never writes the repository board.

usage: <KiCad python3> -I spike_build.py R7_BOARD OUT_DIR [--no-routes] [--fallback]

  1. load R7 (431025d, sha256 c872a3d3...), apply the R8 netlist (m3_design/assembly_review/schematic.net.xml);
  2. keep only the rigid copper (check_r8 rigid groups: CH1 block copper, strip RF copper, strip GND) and the fence;
  3. place every movable part from the seed (b0_place_final.tsv) with this spike's overrides (spike_geom.PLACE),
     leaving the rigid parts (strip, CH1 block, J1, J122) untouched; remove TH1-TH3 (D8);
  4. zones: R7's GND_F / GND_B / GND_In1 and the rigid / sensor / J2 rule areas (moved with their parts); In2 as the
     Strategy B layer plan (GND strip, 3V3 band, RAW_ACT, BAT_IN; plan_partial section 4) plus spike_geom.IN2_KEEPOUT;
  5. add spike_geom's tracks and vias; fill natively (inside OUT_DIR, beside the project rules); save
     OUT_DIR/m3s.kicad_pcb. KIID seed 8301: two runs give the same bytes (measured).
"""
import argparse
import math
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(HERE))
import check_r8                                                # noqa: E402
import spike_geom as G                                         # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
NETLIST = REPO / 'm3_design/assembly_review/schematic.net.xml'
PROJECT = REPO / 'm3_design/assembly_review'
SEED = HERE / 'b0_place_final.tsv'
RIGID_PARTS = set(check_r8.STRIP_PARTS) | set(check_r8.CH1_PARTS) | {'J1', 'J122'}
KEEP_ZONES = {'GND_F', 'GND_B', 'GND_In1', 'U30_KEEPOUT', 'U31_KEEPOUT', 'PYRO_BLOCK', 'R7_J30_launch_In1',
              'R7_J31_launch_In1', 'IMU_body_B', 'IMU_no_internal_tracks', 'BARO_body_B', 'BARO_no_inter_row_tracks',
              # Kept only so the strip's F.Cu GND fill keeps R7's polygon structure: removing these four far F.Cu power
              # zones together (none within 2 mm of the strip) moves the GND_F fill beside the RF lines by 0.01 mm at 13
              # of 372 GCPW samples and changes the strip_gcpw digest (measured; any one removed alone does not).
              'R6_RAW_ACT_F', 'BAT_IN_F', 'RAW_ACT_F', 'R6_BAT_IN_crossbar_F'}
MOVE_WITH = {'IMU_': 'U4', 'BARO_': 'U5', 'J2_CONTACT_': 'J2'}


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def apply_netlist(b):
    root = ET.parse(NETLIST).getroot()
    pins = {}
    for net in root.findall('./nets/net'):
        for node in net.findall('node'):
            pins[(node.attrib['ref'], node.attrib['pin'])] = net.attrib['name']
    changed = 0
    for f in b.GetFootprints():
        for p in f.Pads():
            key = (f.GetReference(), p.GetNumber())
            if not p.GetNumber() or key not in pins:
                continue
            name = pins[key]
            net = b.FindNet(name)
            if net is None:
                net = pcbnew.NETINFO_ITEM(b, name)
                b.Add(net)
            if p.GetNetname() != name:
                p.SetNet(net)
                changed += 1
    return changed


def rigid_track_ids(b):
    """UUIDs of the rigid copper (check_r8.rigid_groups' track items) plus the R7 fence row (regenerated later)."""
    keep = {t.m_Uuid.AsString() for t in check_r8.ch1_copper(b)}
    for t in b.GetTracks():
        n = t.GetNetname()
        if n in check_r8.RF_NETS or (n == 'GNSS_ANT_DC' and (t.GetClass() == 'PCB_VIA' or t.GetLayer() == pcbnew.F_Cu)):
            keep.add(t.m_Uuid.AsString())
        if n == 'GND':
            if t.GetClass() == 'PCB_VIA' and mm(t.GetPosition().y) < check_r8.r7.STRIP_Y:
                keep.add(t.m_Uuid.AsString())          # strip GND vias and the fence row
            elif t.GetClass() != 'PCB_VIA' and mm(t.GetBoundingBox().GetTop()) < check_r8.r7.STRIP_Y:
                keep.add(t.m_Uuid.AsString())
    return keep


def seed_place():
    out = {}
    for line in SEED.read_text().splitlines()[1:]:
        ref, x, y, rot, side = line.split('\t')
        out[ref] = (float(x), float(y), float(rot), side)
    return out


def place(b, table):
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    old = {}
    for ref, (x, y, rot, side) in sorted(table.items()):
        if ref in RIGID_PARTS or ref not in fps:
            continue
        f = fps[ref]
        old[ref] = (mm(f.GetPosition().x), mm(f.GetPosition().y), f.GetOrientationDegrees())
        if (side == 'B') != f.IsFlipped():
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        f.SetOrientationDegrees(rot)
        f.SetPosition(V(x, y))
    for z in list(b.Zones()):
        name = z.GetZoneName()
        for prefix, ref in MOVE_WITH.items():
            if name.startswith(prefix) and ref in old:
                ox, oy, orot = old[ref]
                nx, ny, nrot = table[ref][0], table[ref][1], table[ref][2]
                if abs((nrot - orot) % 360) > 1e-6:
                    z.Rotate(V(ox, oy), pcbnew.EDA_ANGLE(nrot - orot, pcbnew.DEGREES_T))
                z.Move(V(nx - ox, ny - oy))
    for ref in ('TH1', 'TH2', 'TH3'):
        if ref in fps:
            b.Remove(fps[ref])


def add_zone(b, net, layer, pts, name, clearance=0.25, minw=0.2, priority=0, rule=False):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    if rule:
        z.SetIsRuleArea(True)
        z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
    else:
        z.SetNet(b.FindNet(net))
        z.SetLocalClearance(MM(clearance))
        z.SetMinThickness(MM(minw))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetAssignedPriority(priority)
    z.SetZoneName(name)
    chain = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in pts:
        chain.Append(MM(x), MM(y))
    chain.SetClosed(True)
    poly = pcbnew.SHAPE_POLY_SET()
    poly.AddOutline(chain)
    z.SetOutline(poly)
    b.Add(z)
    return z


LAYERS = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, 'In1': pcbnew.In1_Cu, 'In2': pcbnew.In2_Cu}


def add_copper(b, tracks, vias):
    for net, layer, pts, width in tracks:
        n = b.FindNet(net)
        assert n is not None, net
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(V(x0, y0))
            t.SetEnd(V(x1, y1))
            t.SetWidth(MM(width))
            t.SetLayer(LAYERS[layer])
            t.SetNet(n)
            b.Add(t)
    for net, x, y, dia, drill in vias:
        n = b.FindNet(net)
        assert n is not None, net
        v = pcbnew.PCB_VIA(b)
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetPosition(V(x, y))
        v.SetWidth(MM(dia))
        v.SetDrill(MM(drill))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(n)
        b.Add(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('r7', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--no-routes', action='store_true')
    ap.add_argument('--fallback', action='store_true', help='flash on top (kill-rule fallback)')
    a = ap.parse_args()
    # The fill needs the project's rules (m3.kicad_pro / m3.kicad_dru beside the board): without them a native refill
    # changes the strip's coplanar GND gaps and the strip_gcpw hash (measured: 8b46... -> 281d...).
    a.out.mkdir(parents=True, exist_ok=True)
    dst = a.out / 'm3s.kicad_pcb'
    shutil.copy(a.r7, dst)
    shutil.copy(PROJECT / 'm3.kicad_pro', a.out / 'm3s.kicad_pro')
    shutil.copy(PROJECT / 'm3.kicad_dru', a.out / 'm3s.kicad_dru')
    b = pcbnew.LoadBoard(str(dst))
    pcbnew.KIID.SeedGenerator(8301)   # new items' UUIDs repeat from build to build (as r5-r7 builds)
    print('netlist pads changed', apply_netlist(b))
    keep = rigid_track_ids(b)
    kill = [t for t in b.GetTracks() if t.m_Uuid.AsString() not in keep]
    for t in kill:
        b.Remove(t)
    print('tracks/vias removed', len(kill), 'kept', len(keep))
    table = seed_place()
    table.update(G.FALLBACK_PLACE if a.fallback else G.PLACE)
    place(b, table)
    for z in list(b.Zones()):
        if z.GetZoneName() not in KEEP_ZONES and not z.GetZoneName().startswith('J2_CONTACT_'):
            b.Remove(z)
    In2 = pcbnew.In2_Cu
    add_zone(b, 'GND', In2, [(0.3, 0.3), (45.7, 0.3), (45.7, 23.6), (0.3, 23.6)], 'B8_GND_In2_strip')
    add_zone(b, '3V3', In2, [(0.3, 23.9), (45.7, 23.9), (45.7, 66.8), (0.3, 66.8)], 'B8_3V3_In2')
    add_zone(b, 'RAW_ACT', In2, [(5.5, 67.2), (36.5, 67.2), (36.5, 102.2), (5.5, 102.2)], 'B8_RAW_ACT_In2',
             clearance=0.3, minw=0.3)
    add_zone(b, 'BAT_IN', In2, [(5.5, 102.6), (45.7, 102.6), (45.7, 117.7), (5.5, 117.7)], 'B8_BAT_IN_In2',
             clearance=0.3, minw=0.3)
    for name, layer, pts in (G.FALLBACK_KEEPOUTS if a.fallback else G.KEEPOUTS):
        add_zone(b, None, LAYERS[layer], pts, name, rule=True)
    if not a.no_routes:
        tracks, vias = (G.fallback_copper() if a.fallback else G.copper())
        add_copper(b, tracks, vias)
        print('spike copper', len(tracks), 'polylines', len(vias), 'vias')
    b.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'zone fill failed'
    pcbnew.SaveBoard(str(dst), b)
    print('saved', dst)


if __name__ == '__main__':
    main()
