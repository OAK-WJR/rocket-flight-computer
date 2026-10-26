#!/usr/bin/env python3
"""Build the R9 board's placement (M3-ASSY-R9, build step 3) from the committed R8 board and the R9 netlist.

usage: <KiCad python3> -I m3_design/r9_pcb.py [--board m3_design/assembly_review/m3.kicad_pcb]
                                              [--place m3_design/r9_place.tsv] [--propose OUT.tsv] [--draft]

The board file must hold the committed R8 board (SHA-256 checked; m3_design/r9_build.sh restores it from git commit
9c8179b first). It is rebuilt in place, so the project's m3.kicad_pro and m3.kicad_dru apply while it is filled.
Design basis: r9_plan.md sections 1 and 4 step 3, R9_OWNER_DECISIONS.md, R9_DECISIONS.md (D-S2-*, D-S3-*).

1. Footprints: J121 / J124 / J122 become their owner-decided variants in place (r9_lib.apply_variants, D-S2-03) and
   every local clearance override goes (r9_lib.clear_overrides, LC-1). Every pad's net must already equal the R9
   netlist (schematic.net.xml): R9's netlist is R8's pin for pin (D-S2-02), so 0 pads change (asserted).
2. Clean sheet: every track, via and zone goes, but the four sensor rule areas, Y1's In2 keep-out (R5 V1) and the
   PYRO_BLOCK area, which are kept as objects (their settings) and re-shaped below; R8's outline, holes and
   board-level silkscreen go, but the ARM and IGN legends (check_actuators 11), which move onto their terminals until
   r9_post.py (step 8) draws the silkscreen from nothing.
3. Outline and holes from r9_place.tsv's '@' rows: the 46 x L rectangle from (0, 0) (four Edge.Cuts segments), the
   five M3 supports (P2: the corners and the mid-span support of owner decision 5) and J122's two tie holes (M-3),
   each a 3.2 mm Edge.Cuts circle.
4. Every footprint is placed from r9_place.tsv (the table must name every part exactly once). The sensor and Y1 rule
   areas move with U4 / U5 / Y1 (translation only: their parts keep R8's rotation, asserted). PYRO_BLOCK takes the
   outline r9_legalise.block_area derives from the CH1 placement (P-1, check_actuators 15b by construction).
5. The legaliser (r9_legalise.py) checks every part; the table is frozen: any violation stops the build. --propose
   writes the legaliser's nearest legal positions for the violating parts to OUT.tsv (a design aid; the table is
   edited by hand from it, with the reason). --draft saves an illegal board for inspection (r9_build.sh never
   passes it).
6. Title block M3-ASSY-R9; native zone fill in the project folder; save (board only).
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
import r8_sch_check  # noqa: E402
import r9_legalise  # noqa: E402
import r9_lib  # noqa: E402

SOURCE_SHA = 'cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7'   # R8, commit 9c8179b
PROJECT = ROOT / 'm3_design/assembly_review'
PLACE = ROOT / 'm3_design/r9_place.tsv'
MM, mm = pcbnew.FromMM, pcbnew.ToMM
KIID_SEED = 9903
REV = 'M3-ASSY-R9'
HOLE_R = 1.6                                     # Ø3.2 mm: M3 supports and the J122 tie holes (P2)
EDGE_W = 0.05
MOVE_AREAS = {'IMU_body_B': 'U4', 'IMU_no_internal_tracks': 'U4', 'BARO_body_B': 'U5',
              'BARO_no_inter_row_tracks': 'U5', 'Y1_In2_keepout': 'Y1'}
KEEP_TEXT = {'ARM': 'J124', 'IGN': 'J121'}       # check_actuators 11; drawn on their terminals until step 8


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def read_place(path):
    """(rows, features): rows ref -> (x, y, rotation, side); features: dict(outline=(W, L), supports=[(x, y)],
    ties=[(x, y)]) from the '@OUTLINE', '@M3' and '@TIE' rows (tab separated; '#' rows are comments)."""
    rows, feat = {}, dict(outline=None, supports=[], ties=[])
    with open(path) as fh:
        for r in csv.DictReader((line for line in fh if not line.startswith('#')), delimiter='\t'):
            ref = r['ref']
            x, y = float(r['x']), float(r['y'])
            if ref == '@OUTLINE':
                assert feat['outline'] is None, '@OUTLINE twice'
                feat['outline'] = (x, y)
                continue
            if ref == '@M3':
                feat['supports'].append((x, y))
                continue
            if ref == '@TIE':
                feat['ties'].append((x, y))
                continue
            assert not ref.startswith('@'), f'unknown feature row {ref}'
            assert ref not in rows, f'{ref} twice in {path}'
            assert r['side'] in ('F', 'B'), r
            rows[ref] = (x, y, float(r['rot']), r['side'])
    assert feat['outline'] and len(feat['supports']) == 5 and len(feat['ties']) == 2, \
        f'{path}: one @OUTLINE, five @M3 and two @TIE rows required'
    return rows, feat


def check_netlist(b):
    """Every netlist pad already carries its R9 net (D-S2-02: R9's netlist is R8's pin for pin); returns the count."""
    r9 = r8_sch_check.parse(PROJECT / 'schematic.net.xml')
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    assert set(r9['comps']) == set(fps), \
        f'board / netlist parts differ: {sorted(set(r9["comps"]) ^ set(fps))}'
    n, bad = 0, []
    for ref, f in sorted(fps.items()):
        for p in f.Pads():
            key = (ref, p.GetNumber())
            if not p.GetNumber() or key not in r9['pins']:
                continue
            n += 1
            if p.GetNetname() != r9['pins'][key][0]:
                bad.append((key, p.GetNetname(), r9['pins'][key][0]))
    assert not bad, f'pads off the R9 netlist (R9 changes no pin net, D-S2-02): {bad[:8]}'
    return n


def strip(b):
    """The clean sheet: copper, zones (but the kept rule areas), outline, holes and silkscreen go."""
    keep_zones = set(MOVE_AREAS) | {'PYRO_BLOCK'}
    gone = dict(tracks=0, zones=0, drawings=0)
    for t in list(b.GetTracks()):
        b.Delete(t)
        gone['tracks'] += 1
    for z in list(b.Zones()):
        if z.GetIsRuleArea() and z.GetZoneName() in keep_zones:
            continue
        b.Delete(z)
        gone['zones'] += 1
    kept = {}
    for d in list(b.GetDrawings()):
        if d.GetClass() == 'PCB_TEXT' and d.GetText() in KEEP_TEXT and d.GetLayer() == pcbnew.F_SilkS:
            assert d.GetText() not in kept, f'{d.GetText()} twice'
            kept[d.GetText()] = d
            continue
        b.Delete(d)
        gone['drawings'] += 1
    assert set(kept) == set(KEEP_TEXT), f'R8 legends missing: {set(KEEP_TEXT) - set(kept)}'
    names = sorted(z.GetZoneName() for z in b.Zones())
    assert names == sorted(keep_zones), f'kept zones {names}'
    return gone, kept


def outline(b, feat):
    w, length = feat['outline']
    pts = [(0, 0), (w, 0), (w, length), (0, length)]
    for i in range(4):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(V(*pts[i]))
        s.SetEnd(V(*pts[(i + 1) % 4]))
        s.SetWidth(MM(EDGE_W))
        b.Add(s)
    for c in feat['supports'] + feat['ties']:
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_CIRCLE)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetCenter(V(*c))
        s.SetEnd(V(c[0] + HOLE_R, c[1]))
        s.SetWidth(MM(EDGE_W))
        b.Add(s)


def place(b, rows):
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    assert set(rows) == set(fps), (f'placement table must name every part: missing {sorted(set(fps) - set(rows))}, '
                                   f'unknown {sorted(set(rows) - set(fps))}')
    was = {}
    for ref in sorted(rows):
        x, y, rot, side = rows[ref]
        f = fps[ref]
        p = f.GetPosition()
        was[ref] = (mm(p.x), mm(p.y), f.GetOrientationDegrees(), f.IsFlipped())
        if (side == 'B') != f.IsFlipped():
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        f.SetOrientationDegrees(rot)
        f.SetPosition(V(x, y))
    for z in b.Zones():
        ref = MOVE_AREAS.get(z.GetZoneName())
        if ref:
            ox, oy, orot, oflip = was[ref]
            x, y, rot, side = rows[ref]
            assert oflip == (side == 'B'), f'{ref} flipped: its rule areas only move and turn with it'
            z.Move(V(x - ox, y - oy))
            turn = ((rot - orot + 180) % 360) - 180
            if abs(turn) > 1e-6:                   # the areas turn with the part about its centre (U4, D-S7-06)
                z.Rotate(V(x, y), pcbnew.EDA_ANGLE(turn, pcbnew.DEGREES_T))
    return was


def legends(b, kept):
    """ARM / IGN on their terminals' bodies (placeholders for check_actuators 11; step 8 redraws them)."""
    for text, ref in KEEP_TEXT.items():
        f = b.FindFootprintByReference(ref)
        d = kept[text]
        d.SetPosition(f.GetPosition())
        d.SetTextAngleDegrees(0)


def block(b):
    """PYRO_BLOCK takes the derived outline (r9_legalise.block_area)."""
    zs = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'PYRO_BLOCK']
    assert len(zs) == 1
    z = zs[0]
    pts = r9_legalise.block_area(b)
    o = z.Outline()
    o.RemoveAllContours()
    o.NewOutline()
    for x, y in pts:
        o.Append(MM(x), MM(y))
    z.SetNeedRefill(True)
    return pts


def title(b):
    block_ = b.GetTitleBlock()
    block_.SetTitle('M3 flight computer — R9, CAD candidate')
    block_.SetRevision(REV)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--board', type=Path, default=PROJECT / 'm3.kicad_pcb')
    ap.add_argument('--place', type=Path, default=PLACE)
    ap.add_argument('--propose', type=Path, help='write legal positions for violating parts here; board not saved')
    ap.add_argument('--radius', type=float, default=4.0, help='--propose search radius (mm)')
    ap.add_argument('--draft', action='store_true', help='design aid: save the board even when the legaliser fails '
                    '(r9_build.sh never passes it)')
    ap.add_argument('--out', type=Path, help='design aid: save here instead of --board')
    args = ap.parse_args()
    board = args.board.resolve()
    sha = hashlib.sha256(board.read_bytes()).hexdigest()
    assert sha == SOURCE_SHA, f'{board} is not the R8 board ({sha[:16]}); m3_design/r9_build.sh restores it first'
    for ext in ('.kicad_pro', '.kicad_dru'):
        assert board.with_suffix(ext).is_file(), f'{board.with_suffix(ext).name} must sit beside the board'
    b = pcbnew.LoadBoard(str(board))
    pcbnew.KIID.SeedGenerator(KIID_SEED)
    variants = r9_lib.apply_variants(b)
    cleared = r9_lib.clear_overrides(b)
    pads = check_netlist(b)
    gone, kept = strip(b)
    rows, feat = read_place(args.place)
    outline(b, feat)
    place(b, rows)
    legends(b, kept)
    area = block(b)
    title(b)
    report = r9_legalise.check(b, rows)
    if args.propose:
        proposal = r9_legalise.propose(b, rows, report, radius=args.radius)
        r9_legalise.write_proposal(args.propose, rows, proposal)
        print(f'{len(report)} parts in violation; proposal written to {args.propose}')
        return 0 if not report else 1
    for ref, why in sorted(report.items()):
        print(f'LEGALISER {ref}: {"; ".join(why)}')
    if report and not args.draft:
        raise SystemExit(f'placement table is not legal: {len(report)} parts (run with --propose OUT.tsv)')
    b.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'native zone fill failed'
    out = (args.out or board).resolve()
    assert pcbnew.SaveBoard(str(out), b, True), 'save failed'
    print(f'r9_pcb: variants {variants or "already"}, {len(cleared)} local clearances cleared, {pads} pads on the R9 '
          f'netlist (0 changed), removed {gone}, outline {feat["outline"][0]:g} x {feat["outline"][1]:g} mm, '
          f'{len(feat["supports"])} supports, 2 tie holes, {len(rows)} parts placed, PYRO_BLOCK {len(area)} vertices, '
          f'legaliser {"clean" if not report else f"DRAFT, {len(report)} parts illegal"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
