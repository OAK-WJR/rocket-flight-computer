#!/usr/bin/env python3
"""Build the R8 board's placement (M3-ASSY-R8, build step 4) from the committed R7 board and the R8 netlist.

usage: <KiCad python3> -I m3_design/r8_pcb.py [--board m3_design/assembly_review/m3.kicad_pcb]
                                              [--place m3_design/r8_place.tsv] [--propose OUT.tsv]

The board file must hold the committed R7 board (SHA-256 checked; m3_design/r8_build.sh restores it from git commit
431025d first). It is rebuilt in place, so the project's m3.kicad_pro and m3.kicad_dru apply while it is filled.
Design basis: r8_plan.md section 3 step 4, R8_DECISIONS (D1-D28 and the step-4 block), the spike results in
m3_design/r8_spikes/*/RESULT.md.

1. Pad nets from the R8 netlist (schematic.net.xml): exactly the 28 pads of R8_DECISIONS D24/D28 change.
2. Copper: every track and via goes except the rigid R7 copper (check_r8's D15 groups: the CH1 block copper up to
   its exit vias, the RF-line copper with GNSS_ANT_DC's via and F.Cu, the strip GND vias off the fence row and the
   strip GND track). Zones: the board-wide GND pours GND_F / GND_B / GND_In1 stay (their settings give the strip's
   coplanar ground, D15 strip_gcpw), and so do the strip rule areas, PYRO_BLOCK and the sensors' rule areas (moved
   with U4 / U5); every other R7 zone goes. In2 and the power pours are r8_power.py's (step 5).
3. TH1-TH3 are deleted (D8); R7's board-level silkscreen goes (r8_post.py redraws it).
4. Every part that is not rigid is placed from r8_place.tsv (the table must name exactly those parts). The rigid parts
   (check_r8 STRIP_PARTS, CH1_PARTS, J1, J122) are never moved.
5. The legaliser (r8_legalise.py) checks the placement: courtyards, the board edge, the bottom-side keep-outs (R5 L10),
   the support washers, the J122 tie path, the routing reservations of r8_keepclear.tsv, the bare test pads' 1.0 mm
   clearance, pyro rules A-H between pads and F10's 5 mm RF separation. The table is frozen: any violation stops the
   build. --propose writes the legaliser's nearest legal positions for the violating parts to OUT.tsv (a design aid;
   the table is edited by hand from it, with the reason).
6. Title block M3-ASSY-R8; native zone fill in the project folder; save (board only); the 12 rigid digests are
   asserted against check_r8.RIGID_BASELINE after the fill.
Deterministic (fixed KIID seed, no random search): a rebuild reproduces the board byte for byte.
"""
import argparse
import csv
import hashlib
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r8  # noqa: E402
import check_r7 as r7  # noqa: E402
import r8_sch_check  # noqa: E402
import r8_legalise  # noqa: E402

SOURCE_SHA = 'c872a3d30509cccf5f78b64cde48ef722ee85c7be23c4848b07ce4082a852de3'   # R7, commit 431025d
PROJECT = ROOT / 'm3_design/assembly_review'
PLACE = ROOT / 'm3_design/r8_place.tsv'
MM, mm = pcbnew.FromMM, pcbnew.ToMM
KIID_SEED = 8801
REV = 'M3-ASSY-R8'
RIGID_PARTS = frozenset(check_r8.STRIP_PARTS) | frozenset(check_r8.CH1_PARTS) | {'J1', 'J122'}
REMOVED = ('TH1', 'TH2', 'TH3')                                   # D8
KEEP_POURS = ('GND_F', 'GND_B', 'GND_In1', 'R6_BAT_IN_crossbar_F')
SENSOR_AREAS = {'IMU_body_B': 'U4', 'IMU_no_internal_tracks': 'U4', 'BARO_body_B': 'U5',
                'BARO_no_inter_row_tracks': 'U5'}
KEEP_AREAS = set(check_r8.STRIP_RULE_AREAS) | {'PYRO_BLOCK'} | set(SENSOR_AREAS)
NETLIST_CHANGES = 28                                              # D24 / D28: 27 U1 pins + R310.1
# R7 board-level silkscreen that belongs to unmoved parts stays (check_actuators 11 needs the ARM / IGN legends; the
# rest are the rigid terminals', J1's, J122's and the jacks' legends, and TP30's); the revision legend is updated. Every
# other R7 silk item described a moved part and goes; r8_post.py (step 8) redraws the board's silkscreen (D29).
KEEP_SILK = {'ARM', 'IGN', '1:BUS1', '2:RAW', '1:E1-', '2:E1+', 'J124 2-FUSE-1: ARM LAST', 'J124: 5A FAST / 2S', 'BAT',
             '1:BAT+', '3:SW', '4:SW', 'J1 BAT LEAD: 15A FUSE', 'SERVO', '1', '2', '3', '4', 'J122 1:S 2:+ 3:GND',
             'GNSS', 'RADIO', 'TP30 SAFEBOOT', 'JLCJLCJLCJLC', 'M3-ASSY-R7'}
KEEP_SILK_AT = {('2:GND', 26.54, 102.6)}                              # J1.2's legend (J123's '2:GND' goes)


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def read_place(path):
    """ref -> (x, y, rotation, side) from a placement table (tab separated; '#' rows are comments)."""
    rows = {}
    with open(path) as fh:
        for r in csv.DictReader((line for line in fh if not line.startswith('#')), delimiter='\t'):
            assert r['ref'] not in rows, f'{r["ref"]} twice in {path}'
            assert r['side'] in ('F', 'B'), r
            rows[r['ref']] = (float(r['x']), float(r['y']), float(r['rot']), r['side'])
    return rows


def apply_netlist(b):
    """Every netlist pad takes its R8 net; returns the changed pads, which must be exactly D28's set."""
    r8 = r8_sch_check.parse(PROJECT / 'schematic.net.xml')
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    missing = sorted(set(r8['comps']) - set(fps))
    assert not missing, f'netlist parts missing from the board: {missing}'
    changed = {}
    for ref in sorted(fps):
        if ref not in r8['comps']:
            continue
        for p in fps[ref].Pads():
            key = (ref, p.GetNumber())
            if not p.GetNumber() or key not in r8['pins']:
                continue
            name = r8['pins'][key][0]
            net = b.FindNet(name)
            if net is None:
                net = pcbnew.NETINFO_ITEM(b, name)
                b.Add(net)
            if p.GetNetname() != name:
                changed[key] = (r8_sch_check.nc(p.GetNetname()), r8_sch_check.nc(name))
                p.SetNet(net)
    want = r8_sch_check.expected_changes()
    assert changed == want and len(changed) == NETLIST_CHANGES, \
        f'netlist changes differ from D28: extra {sorted(set(changed) - set(want))}, missing {sorted(set(want) - set(changed))}'
    return changed


def rigid_copper(b):
    """UUIDs of the rigid R7 tracks and vias (check_r8.rigid_groups' selection; the fence row is not rigid, D16)."""
    keep = {t.m_Uuid.AsString() for t in check_r8.ch1_copper(b)}
    for t in b.GetTracks():
        n, via = t.GetNetname(), t.GetClass() == 'PCB_VIA'
        if n in check_r8.RF_NETS or (n == 'GNSS_ANT_DC' and (via or t.GetLayer() == pcbnew.F_Cu)):
            keep.add(t.m_Uuid.AsString())
        elif n == 'GND' and via:
            y = mm(t.GetPosition().y)
            if y < r7.STRIP_Y and abs(y - r7.FENCE_Y) >= check_r8.FENCE_ROW:
                keep.add(t.m_Uuid.AsString())
        elif n == 'GND' and mm(t.GetBoundingBox().GetTop()) < r7.STRIP_Y:
            keep.add(t.m_Uuid.AsString())
    return keep


def strip(b):
    """Non-rigid copper, R7's other zones, the tooling holes and R7's board-level silkscreen go."""
    keep = rigid_copper(b)
    dead = [t for t in b.GetTracks() if t.m_Uuid.AsString() not in keep]
    for t in dead:
        b.Delete(t)
    for z in list(b.Zones()):
        name = z.GetZoneName()
        if not (name in KEEP_AREAS if z.GetIsRuleArea() else name in KEEP_POURS):
            b.Delete(z)
    for ref in REMOVED:
        f = b.FindFootprintByReference(ref)
        assert f is not None, ref
        b.Delete(f)
    for d in list(b.GetDrawings()):
        if d.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            continue
        text = d.GetText() if d.GetClass() == 'PCB_TEXT' else None
        at = (text, round(mm(d.GetPosition().x), 2), round(mm(d.GetPosition().y), 2))
        if text in KEEP_SILK or at in KEEP_SILK_AT:
            if text == 'M3-ASSY-R7':
                d.SetText(REV)
            continue
        b.Delete(d)
    return len(keep), len(dead)


def place(b, rows):
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    movable = set(fps) - RIGID_PARTS
    assert set(rows) == movable, (f'placement table must name exactly the non-rigid parts: missing '
                                  f'{sorted(movable - set(rows))}, unknown or rigid {sorted(set(rows) - movable)}')
    moved = {}
    for ref in sorted(rows):
        x, y, rot, side = rows[ref]
        f = fps[ref]
        p = f.GetPosition()
        moved[ref] = (mm(p.x), mm(p.y), f.GetOrientationDegrees())
        if (side == 'B') != f.IsFlipped():
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        f.SetOrientationDegrees(rot)
        f.SetPosition(V(x, y))
    for z in b.Zones():
        ref = SENSOR_AREAS.get(z.GetZoneName())
        if ref:
            ox, oy, orot = moved[ref]
            x, y, rot, _ = rows[ref]
            assert abs(((rot - orot + 180) % 360) - 180) < 1e-6, f'{ref} turned: its rule areas only translate'
            z.Move(V(x - ox, y - oy))
    return moved


# Fix pass 1 (R8P1-DFM-03, D89): R5 made J3's GND legs solid (r5_pcb.py FULL_PADS) because in R5's layout their spokes
# were starved (between the board edge, a locating hole and the USB fan-out). R8 moved J3 and the GND fill now reaches
# its spokes, so REQUIREMENTS M2's rule applies: they inherit the THT thermal relief. J123.2 (the pull-pin's GND) gets
# its relief in r8_ground.py instead (fix pass 2, D101): on the step-6 board, before step 7's GND vias and fill, DRC
# reports starved_thermal on B.Cu there, but on the final copper the relief resolves 2 spokes on B.Cu (the project's
# min_resolved_spokes) and >= 4 on F.Cu and In1. J122's GND pins stay solid: the 7.7 A servo return (and with a relief
# J122.3 would resolve only 1 spoke on F.Cu); they are also in the rigid j122_tie digest.
THERMAL_PADS = (('J3', '1'), ('J3', '4'))


def zone_connections(b):
    for ref, num in THERMAL_PADS:
        pads = [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num]
        assert len(pads) == 1 and pads[0].GetNetname() == 'GND', (ref, num)
        assert pads[0].GetLocalZoneConnection() == pcbnew.ZONE_CONNECTION_FULL, (ref, num, 'expected R7 FULL')
        pads[0].SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_INHERITED)


def title(b):
    block = b.GetTitleBlock()
    block.SetTitle('M3 flight computer — R8, CAD candidate')
    block.SetRevision(REV)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--board', type=Path, default=PROJECT / 'm3.kicad_pcb')
    ap.add_argument('--place', type=Path, default=PLACE)
    ap.add_argument('--keepclear', type=Path, default=r8_legalise.KEEPCLEAR)
    ap.add_argument('--propose', type=Path, help='write legal positions for violating parts here; board not saved')
    ap.add_argument('--draft', action='store_true', help='design aid: save the board even when the legaliser fails '
                    '(r8_build.sh never passes it)')
    args = ap.parse_args()
    board = args.board.resolve()
    sha = hashlib.sha256(board.read_bytes()).hexdigest()
    assert sha == SOURCE_SHA, f'{board} is not the R7 board ({sha[:16]}); m3_design/r8_build.sh restores it first'
    for ext in ('.kicad_pro', '.kicad_dru'):
        assert board.with_suffix(ext).is_file(), f'{board.with_suffix(ext).name} must sit beside the board'
    b = pcbnew.LoadBoard(str(board))
    pcbnew.KIID.SeedGenerator(KIID_SEED)
    changed = apply_netlist(b)
    kept, dead = strip(b)
    rows = read_place(args.place)
    place(b, rows)
    zone_connections(b)
    title(b)
    keepclear = r8_legalise.read_keepclear(args.keepclear)
    report = r8_legalise.check(b, rows, keepclear)
    if args.propose:
        proposal = r8_legalise.propose(b, rows, report, keepclear)
        r8_legalise.write_proposal(args.propose, rows, proposal)
        print(f'{len(report)} parts in violation; proposal written to {args.propose}')
        return 0 if not report else 1
    for ref, why in sorted(report.items()):
        print(f'LEGALISER {ref}: {"; ".join(why)}')
    if report and not args.draft:
        raise SystemExit(f'placement table is not legal: {len(report)} parts (run with --propose OUT.tsv)')
    b.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'native zone fill failed'
    assert pcbnew.SaveBoard(str(board), b, True), 'save failed'
    b = pcbnew.LoadBoard(str(board))
    issues, digests = check_r8.rigid(b)
    assert not issues, issues
    print(f'r8_pcb: {len(changed)} pads re-netted, {kept} rigid tracks/vias kept, {dead} removed, '
          f'{len(rows)} parts placed, legaliser {"clean" if not report else f"DRAFT, {len(report)} parts illegal"}, '
          f'rigid digests {len(digests)}/12 equal R7')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
