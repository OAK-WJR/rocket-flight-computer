#!/usr/bin/env python3
"""Build the R7 board (M3-ASSY-R7) from the committed R6 board and the R7 netlist.

usage: <KiCad python3> -I m3_design/r7_pcb.py [netlist] [--board m3_design/assembly_review/m3.kicad_pcb]

The board file must hold the committed R6 board (SHA-256 checked; m3_design/r7_build.sh restores it from
git commit 3b215ba first). It is rebuilt in place, so the project's m3.kicad_pro and m3.kicad_dru apply while
it is edited. Design basis: REQUIREMENTS F10/P1/P2, sources/r7_review/pass1_layout.md section 3.3-5.4 and
stepA_handoff.md; decisions and deviations are recorded in sources/r7_review/stepB_progress.md.

1. Every item moves +18.0 mm in y (footprints, tracks, vias, zones, rule areas, drawings); y = 0 stays the
   aft edge. The outline becomes 46 x 118 mm, the two aft supports move to the new corners (4, 4) and
   (42.3, 4), and J123 (pull-pin) moves to (36.0, 34.6).
2. The 37 R6 port parts (J130, J131, U14, U15, U16, L4, TP130, D130, D131, C170-C180, R190-R206) go with
   every track, via and zone of their nets (TLM_*, RADIO_M0/M1/RXD/TXD/AUX(_MCU), RADIO_TX/RX_MCU, GPS_*);
   copper of the shared nets 3V3, GND and RAW_PROTECTED (and PULLPIN_EXT/GND at J123's old place) is removed
   only where KiCad's DRC reports it dangling after the removal (r7_lib.prune_dangling), never elsewhere.
3. The R7 parts come from the netlist (footprints, fields, nets, DNP flags) and are placed in the RF strip.
4. Stackup JLC041611-7628, the RF-strip pours (In2 GND, In1 cut-outs under the SMA centre pads), the module
   keep-out areas named for m3.kicad_dru and the strip-boundary via fence.
No routing beyond the fence is done here (m3_design/r7_route.py).
"""
import argparse
import hashlib
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
import r5_pcb as base  # noqa: E402
import r6_pcb  # noqa: E402
import r7_lib as lib  # noqa: E402

SOURCE_SHA = '184a87e84e67576341244c82517de3e9f55f5c1c22995dfad83631d48c856680'   # R6, commit 3b215ba
PROJECT = ROOT / 'm3_design/assembly_review'
MM, mm = pcbnew.FromMM, pcbnew.ToMM
DY = 18.0
W, L = 46.0, 118.0
REMOVED = set('J130 J131 U14 U15 U16 L4 TP130 D130 D131'.split()) | {f'C{n}' for n in range(170, 181)} \
    | {f'R{n}' for n in range(190, 207)}
REMOVED_NET_PREFIXES = ('TLM_', 'GPS_', 'RADIO_M0', 'RADIO_M1', 'RADIO_RXD', 'RADIO_TXD', 'RADIO_AUX',
                        'RADIO_TX_MCU', 'RADIO_RX_MCU')
SHARED = {'3V3', 'GND', 'RAW_PROTECTED'}
SUPPORT_MOVES = {(4.0, 22.0): (4.0, 4.0), (42.3, 22.0): (42.3, 4.0)}   # after the +18 mm translation
J123_AT = (36.0, 34.6)   # pass1_layout L13: (36.0, 34.5); 0.1 mm forward keeps R6's CAM_5V branch (R104 -> U13)
                         # 0.2 mm clear of its pin 1 instead of rerouting that supply trace


def point(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def translate(b, dy=DY):
    """Rigid +dy translation of everything on the board (footprints carry their own zones and text)."""
    v = point(0, dy)
    for f in b.GetFootprints():
        f.Move(v)
    for t in b.GetTracks():
        t.Move(v)
    for z in b.Zones():
        z.Move(v)
    for d in b.GetDrawings():
        d.Move(v)


def outline(b):
    """46 x 118 mm outline; the aft supports at the new corners; the other holes stay translated."""
    for d in list(b.GetDrawings()):
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() != pcbnew.SHAPE_T_CIRCLE:
            b.Delete(d)
    for a, c in (((0, 0), (W, 0)), ((W, 0), (W, L)), ((W, L), (0, L)), ((0, L), (0, 0))):
        base.edge_line(b, a, c)
    moved = 0
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            c = (round(mm(d.GetCenter().x), 3), round(mm(d.GetCenter().y), 3))
            for old, new in SUPPORT_MOVES.items():
                if abs(c[0] - old[0]) < 0.01 and abs(c[1] - old[1]) < 0.01:
                    r = d.GetRadius()
                    d.SetCenter(point(*new))
                    d.SetEnd(pcbnew.VECTOR2I(MM(new[0]) + r, MM(new[1])))
                    moved += 1
    if moved != 2:
        raise RuntimeError(f'expected to move two aft supports, moved {moved}')


def removed_nets(b, netlist):
    """Board nets that the R7 netlist no longer has: exactly the R6 port nets (asserted)."""
    root = ET.parse(netlist).getroot()
    keep = {n.attrib['name'] for n in root.findall('./nets/net')}
    used = {p.GetNetname() for f in b.GetFootprints() for p in f.Pads() if p.GetNetname()}
    used |= {t.GetNetname() for t in b.GetTracks() if t.GetNetname()}
    gone = {n for n in used - keep if not n.startswith('unconnected-')}
    odd = sorted(n for n in gone if not n.startswith(REMOVED_NET_PREFIXES))
    if odd:
        raise RuntimeError('unexpected nets would lose their copper: ' + ', '.join(odd))
    return gone


def strip_removed_copper(b, gone):
    tracks = [t for t in b.GetTracks() if t.GetNetname() in gone]
    zones = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() in gone]
    for t in tracks:
        b.Delete(t)
    for z in zones:
        b.Delete(z)
    return len(tracks), len(zones)


def sync_attributes(b, netlist):
    """DNP placeholders: dnp, out of the BOM and the position files (the netlist's properties)."""
    root = ET.parse(netlist).getroot()
    dnp = []
    for node in root.findall('./components/comp'):
        props = {p.attrib['name'] for p in node.findall('property')}
        f = b.FindFootprintByReference(node.attrib['ref'])
        attrs = f.GetAttributes()
        if 'dnp' in props:
            attrs |= pcbnew.FP_DNP
            dnp.append(node.attrib['ref'])
        if 'exclude_from_bom' in props:
            attrs |= pcbnew.FP_EXCLUDE_FROM_BOM
        if 'exclude_from_pos_files' in props:
            attrs |= pcbnew.FP_EXCLUDE_FROM_POS_FILES
        f.SetAttributes(attrs)
    return sorted(dnp)


def build(board_path, netlist):
    if hashlib.sha256(board_path.read_bytes()).hexdigest() != SOURCE_SHA:
        raise RuntimeError('the board file is not the committed R6 board (run m3_design/r7_build.sh)')
    pcbnew.KIID.SeedGenerator(7101)
    b = pcbnew.LoadBoard(str(board_path))
    gone = removed_nets(b, netlist)
    translate(b)
    outline(b)
    lib.title(b)
    lib.delete_silkscreen(b)
    j123_pads = lib.detach_footprint(b, 'J123')
    # The port parts go before the netlist import, without their pad leadouts: shared-net copper (3V3, GND,
    # RAW_PROTECTED) that met at, or ran along, one of their leadouts to other parts must stay joined, so only what
    # DRC then calls dangling is removed (lib.prune_dangling trims a leadout back to its last joint).
    for f in [f for f in b.GetFootprints() if f.GetReference() in REMOVED]:
        b.Delete(f)
    added, changed = r6_pcb.synchronize(b, netlist)
    if (set(added), set(changed)) != (set(lib.NEW_REFS), set()):
        raise RuntimeError(f'netlist sync: added {sorted(added)}, replaced {sorted(changed)}')
    # RF ground pads (ESD diodes, bias-tee capacitor, pi-network shunt lands) connect solidly, no thermal relief: the
    # relief's spokes add inductance in series with the ESD return and any shunt fitted later (pass 2 RF-02;
    # tools/check_r7 exempts them from the small-pad relief policy and checks them solid). r6_pcb.synchronize gave
    # the R/C ones thermal relief.
    for ref in lib.RF_SOLID_GND:
        for p in b.FindFootprintByReference(ref).Pads():
            if p.GetNetname() == 'GND':
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    n_tracks, n_zones = strip_removed_copper(b, gone)
    print(f'removed nets ({len(gone)}): {" ".join(sorted(gone))}; {n_tracks} tracks/vias, {n_zones} zones')
    print('DNP placeholders:', ' '.join(sync_attributes(b, netlist)))
    base.place(b, 'J123', *J123_AT, 0, 'F')
    lib.place_rf(b)
    lib.zones(b)
    b.BuildConnectivity()
    pcbnew.SaveBoard(str(board_path), b, True)
    lib.patch_stackup(board_path)
    trimmed, deleted = lib.prune_dangling(board_path, SHARED | {'PULLPIN_EXT'}, j123_pads)
    print(f'dangling shared-net copper: {deleted} items deleted, {trimmed} leadouts trimmed to their last joint')
    print('R7 placement saved:', board_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('netlist', type=Path, nargs='?', default=PROJECT / 'schematic.net.xml')
    parser.add_argument('--board', type=Path, default=PROJECT / 'm3.kicad_pcb')
    args = parser.parse_args()
    build(args.board, args.netlist)
