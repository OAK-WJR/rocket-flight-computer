#!/usr/bin/env python3
"""Rebuild R10 placement from the pinned R9 source and native schematic netlist.

No inherited copper is retained. Placement comes exclusively from r10_place.tsv;
the sensor rule areas move with their parts. Subsequent stages draw explicit tables.
"""
import argparse
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'm3_design'), str(ROOT / 'tools')]
import r6_pcb
import r9_lib
import r9_pcb

PROJECT = ROOT / 'm3_design/assembly_review'
SOURCE_COMMIT = '40a1d28'
SOURCE_FILE = 'm3_design/assembly_review/m3.kicad_pcb'
SOURCE_SHA = '4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14'
REV = 'M3-ASSY-R10'
AREAS = {k: v for k, v in r9_pcb.MOVE_AREAS.items() if v in ('U4', 'U5')}


def source_board():
    """Read a committed blob; never restore, checkout or alter another worktree."""
    data = subprocess.run(['git', '-C', str(ROOT), 'show', f'{SOURCE_COMMIT}:{SOURCE_FILE}'],
                          check=True, capture_output=True).stdout
    assert hashlib.sha256(data).hexdigest() == SOURCE_SHA, 'R9 source hash mismatch'
    with tempfile.TemporaryDirectory(prefix='r10-source-') as tmp:
        path = Path(tmp) / 'm3.kicad_pcb'
        path.write_bytes(data)
        return pcbnew.LoadBoard(str(path))


def strip(board):
    for item in list(board.GetTracks()):
        board.Delete(item)
    for item in list(board.GetDrawings()):
        board.Delete(item)
    for zone in list(board.Zones()):
        if not zone.GetIsRuleArea() or zone.GetZoneName() not in AREAS:
            board.Delete(zone)


# D-R18-08 (R18-MFG-02): retained R9 footprints whose library land changed in R10. Only the pads' local mask / paste
# margins follow the library (U4: mask expansion 0 for 0.15 mm webs; paste ratio unchanged at -3 % per axis, 88.4 % of
# the land, inside ST TN1383's 70-90 %); the pad numbers, positions, shapes and sizes must already agree (asserted).
# r10_post.sync_silk then holds the instance to KiCad's own library comparison.
LAND_SYNC = ('U4',)


def sync_lands(board, lib, refs=LAND_SYNC):
    synced = []
    for ref in refs:
        f = board.FindFootprintByReference(ref)
        new = pcbnew.FootprintLoad(str(lib), str(f.GetFPID().GetLibItemName()))
        assert new is not None, ref
        new.SetParent(board)
        if f.IsFlipped():
            new.Flip(new.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        new.SetOrientation(f.GetOrientation())
        new.SetPosition(f.GetPosition())
        lib_pads = {p.GetNumber(): p for p in new.Pads()}
        assert sorted(lib_pads) == sorted(p.GetNumber() for p in f.Pads()), f'{ref}: pad numbers differ from library'
        for p in f.Pads():
            q = lib_pads[p.GetNumber()]
            assert (p.GetPosition(), p.GetSize(), p.GetShape()) == \
                (q.GetPosition(), q.GetSize(), q.GetShape()), f'{ref}.{p.GetNumber()}: land differs'
            p.SetLocalSolderMaskMargin(q.GetLocalSolderMaskMargin())
            p.SetLocalSolderPasteMargin(q.GetLocalSolderPasteMargin())
            p.SetLocalSolderPasteMarginRatio(q.GetLocalSolderPasteMarginRatio())
        synced.append(ref)
    return synced


def build(project, table):
    board = source_board()
    pcbnew.KIID.SeedGenerator(10103)
    strip(board)
    # Reuse the native-netlist importer; its older local-clearance policy is
    # deliberately removed below. R10 uses the project's ordinary clearance.
    r6_pcb.PROJECT = project
    added, changed = r6_pcb.synchronize(board, project / 'schematic.net.xml')
    r9_lib.clear_overrides(board)
    # TP footprints have one contact, so the saved foreign-copper floor is also a safe native-fill override.
    # J2's foreign-only rule cannot be a blanket override: its own contacts and locating holes are closer.
    for footprint in board.GetFootprints():
        ref = footprint.GetReference()
        if ref.startswith('TP'):
            footprint.SetLocalClearance(pcbnew.FromMM(1.0))
    # R10 signal/logic returns need solderable THT thermals on every plane,
    # including In1's otherwise solid GND connection (R11-MFG-01).
    for ref in ('J1', 'J9', 'J122', 'J410', 'J420'):
        for p in board.FindFootprintByReference(ref).Pads():
            if p.GetNetname() == 'GND':
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    print(f'r10_pcb: library land margins: {" ".join(sync_lands(board, project / "kilib" / "rocket.pretty"))}')
    rows, features = r9_pcb.read_place(table, tie_count=0)
    r9_pcb.outline(board, features)
    r9_pcb.place(board, rows)
    import r10_post                     # footprint silkscreen from the project library (R3-MFG-01 / -02, D-R3-D1)
    synced = r10_post.sync_silk(board, project / 'kilib' / 'rocket.pretty')
    print(f'r10_pcb: footprint silkscreen from the library: {" ".join(synced) or "none"}')
    for footprint in board.GetFootprints():
        # The importer updates native fields but keeps legacy fields absent from the new schematic part.
        if footprint.HasField('LCSC Part') and footprint.HasField('LCSC') and \
                footprint.GetField('LCSC Part').GetText() != footprint.GetField('LCSC').GetText():
            footprint.Delete(footprint.GetField('LCSC Part'))
        for field in footprint.GetFields():
            field.SetVisible(False)
        footprint.Value().SetLayer(pcbnew.B_Fab if footprint.IsFlipped() else pcbnew.F_Fab)
    title = board.GetTitleBlock()
    title.SetTitle('Flight computer R10 — CAD candidate')
    title.SetRevision(REV)
    board.BuildConnectivity()
    out = project / 'm3.kicad_pcb'
    assert pcbnew.SaveBoard(str(out), board, True), 'placement save failed'
    print(f'r10_pcb: {len(rows)} parts; {features["outline"]}; '
          f'{len(added)} added, {len(changed)} replaced; no inherited tracks/vias/pours')
    return board


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=PROJECT)
    parser.add_argument('--place', type=Path, default=ROOT / 'm3_design/r10_place.tsv')
    args = parser.parse_args()
    build(args.project.resolve(), args.place)


if __name__ == '__main__':
    main()
