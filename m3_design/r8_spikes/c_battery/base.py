#!/usr/bin/env python3
"""Spike 3(c) scratch base board: R7 (431025d, SHA-256 c872a3d3...) with the R8 netlist applied, every non-rigid track,
via and copper zone removed, TH1-TH3 removed and the step-4 seed placement (partial/b0_place_final.tsv) applied.

usage: <KiCad python3> -I base.py R7_BOARD SEED_TSV OUT_DIR

The rigid copper (check_r8.rigid_groups: CH1 block copper, strip RF copper, strip GND) and the rigid rule areas stay
exactly as in R7. The board-wide GND pours GND_F / GND_B / GND_In1 and R7_GND_In2_strip stay (their settings give
the strip's GCPW ground profile, D15). The IMU / barometer rule areas move with U4 / U5 (as partial/b0_place.py
does). OUT_DIR gets m3.kicad_pcb with the project's m3.kicad_pro and m3.kicad_dru beside it (DRC needs them).
Scratch only: the real build is r8_build.sh (step 4 on).
"""
import csv
import hashlib
import shutil
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'm3_design'))
import check_r8  # noqa: E402
import r8_sch_check  # noqa: E402

MM, mm = pcbnew.FromMM, pcbnew.ToMM
R7_SHA = 'c872a3d30509cccf'
PROJECT = ROOT / 'm3_design/assembly_review'
RIGID_PARTS = set(check_r8.STRIP_PARTS) | set(check_r8.CH1_PARTS) | {'J1', 'J122'}
KEEP_ZONES = ('GND_F', 'GND_B', 'GND_In1', 'R7_GND_In2_strip', 'PYRO_BLOCK', 'U30_KEEPOUT', 'U31_KEEPOUT',
              'R7_J30_launch_In1', 'R7_J31_launch_In1', 'IMU_body_B', 'IMU_no_internal_tracks', 'BARO_body_B',
              'BARO_no_inter_row_tracks')


def main(src, seed, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    assert hashlib.sha256(Path(src).read_bytes()).hexdigest().startswith(R7_SHA), 'not the R7 board'
    dst = out_dir / 'm3.kicad_pcb'
    shutil.copyfile(src, dst)
    for name in ('m3.kicad_pro', 'm3.kicad_dru'):
        shutil.copyfile(PROJECT / name, out_dir / name)
    changed = r8_sch_check.apply_netlist(dst, r8_sch_check.parse(PROJECT / 'schematic.net.xml'))
    assert len(changed) == 28, changed
    b = pcbnew.LoadBoard(str(dst))
    groups_before = {k: check_r8.digest(v) for k, v in check_r8.rigid_groups(b).items()}
    keep = set()
    for t in check_r8.ch1_copper(b):
        keep.add(t.m_Uuid.AsString())
    for t in b.GetTracks():
        n = t.GetNetname()
        if n in check_r8.RF_NETS or (n == 'GNSS_ANT_DC' and (t.GetClass() == 'PCB_VIA' or t.GetLayer() == pcbnew.F_Cu)):
            keep.add(t.m_Uuid.AsString())
        if n == 'GND':
            if t.GetClass() == 'PCB_VIA':
                y = mm(t.GetPosition().y)
                if y < check_r8.r7.STRIP_Y and abs(y - check_r8.r7.FENCE_Y) >= check_r8.FENCE_ROW:
                    keep.add(t.m_Uuid.AsString())
            elif mm(t.GetBoundingBox().GetTop()) < check_r8.r7.STRIP_Y:
                keep.add(t.m_Uuid.AsString())
    dead_zones = [z for z in b.Zones() if z.GetZoneName() not in KEEP_ZONES]
    dead_tracks = [t for t in b.GetTracks() if t.m_Uuid.AsString() not in keep]
    for z in dead_zones:
        b.Delete(z)
    for t in dead_tracks:
        b.Delete(t)
    for ref in ('TH1', 'TH2', 'TH3'):
        f = b.FindFootprintByReference(ref)
        if f:
            b.Delete(f)
    moved = {}
    with open(seed) as fh:
        for row in csv.DictReader(fh, delimiter='\t'):
            f = b.FindFootprintByReference(row['ref'])
            assert f is not None, row
            p = f.GetPosition()
            if row['ref'] in RIGID_PARTS:       # rigid, unmoved: R7's exact position (the seed rounds to 0.01 mm)
                assert abs(mm(p.x) - float(row['x'])) < 0.006 and abs(mm(p.y) - float(row['y'])) < 0.006, row
                continue
            moved[row['ref']] = (mm(p.x), mm(p.y))
            if (row['side'] == 'B') != f.IsFlipped():
                f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
            f.SetOrientationDegrees(float(row['rot']))
            f.SetPosition(pcbnew.VECTOR2I(MM(float(row['x'])), MM(float(row['y']))))
            moved[row['ref']] += (float(row['x']), float(row['y']))
    for z in [b.GetArea(i) for i in range(b.GetAreaCount())]:
        tgt = 'U4' if z.GetZoneName().startswith('IMU') else 'U5' if z.GetZoneName().startswith('BARO') else None
        if tgt and tgt in moved:
            ox, oy, nx, ny = moved[tgt]
            z.Move(pcbnew.VECTOR2I(MM(nx - ox), MM(ny - oy)))
    groups_after = {k: check_r8.digest(v) for k, v in check_r8.rigid_groups(b).items() if k != 'strip_gcpw'}
    drift = [k for k, v in groups_after.items() if v != groups_before[k]]
    pcbnew.SaveBoard(str(dst), b)
    print(f'{dst}: {len(changed)} pads re-netted, {len(moved)} parts placed (rigid parts kept at R7 positions), {len(keep)} rigid tracks/vias kept; '
          f'rigid groups changed (before fill; strip_gcpw needs a fill): {drift or "none"}')


if __name__ == '__main__':
    main(*sys.argv[1:4])
