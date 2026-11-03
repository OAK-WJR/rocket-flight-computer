#!/usr/bin/env python3
"""R9 step 3 kill-path record: at which board length the four MCU-end interface resistors have clean spots.

usage: <KiCad python3> -I m3_design/r9_kill_path.py [--lengths 98 100 102] [--cap 6] [--margin 0.25] [--slack 0.2]
                                                    [--json OUT.json]

Evidence for R9_DECISIONS D-S3-03 (r9_plan.md section 4 step 3 "if 98 fails, go to 100", owner decision 1: fallback
100 / 102 mm). Not part of the build. For each length L the frozen table m3_design/r9_place.tsv is re-based: every
part outside the RF strip (and the four resistors) moves L - (table length) mm in y with the forward edge, the forward
supports and J122's tie holes; the RF strip stays. The board is built in memory exactly as r9_pcb.py builds it (R8's
board from git 9c8179b, variants, overrides cleared, clean sheet, outline, placement, PYRO_BLOCK) and the four
resistors R306 (GNSS RXD), R315 (RADIO_MOSI), R310 (RADIO_NSS pull) and R313 (RADIO_SCK) are taken off it. Then:

1. Spots: every 0.2 mm grid position, rotations 0 and 90, top side, where the resistor is legal under the gate's
   legaliser (r9_legalise: R-10's 5.94 mm / 5.0 mm F10 separations, courtyards, pads, ...), meets K-contract's
   SERIES / PULL_END (centre nearer U1's centre than its module's, by at least --margin mm), stays legal --slack mm
   nearer U1 (R-10 slack), and lengthens its lane (U1 pin -> resistor -> module pin) by at most --cap mm.
2. Joint: the four in lane order west to east (R306, R315, R310, R313: the order of their U1 pins and module pins, so
   no two lanes cross), no courtyard clash, least total detour (branch and bound), re-checked with the legaliser.

A length "holds" when a joint arrangement exists. Bottom-side or out-of-order spots are not searched: they need lane
crossings or layer hops on critical nets that a longer board avoids (REQUIREMENTS M2, clean routing).
"""
import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r7 as r7  # noqa: E402
import check_r8 as r8  # noqa: E402
import r9_legalise as LG  # noqa: E402
import r9_lib  # noqa: E402
import r9_pcb  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
R8_COMMIT = '9c8179b'
SEQ = ('R306', 'R315', 'R310', 'R313')          # lane order west to east
LANES = {'R306': (('U1', '63'), ('U30', '3'), 'U30'), 'R315': (('U1', '53'), ('U31', '13'), 'U31'),
         'R310': (('U1', '47'), ('U31', '14'), 'U31'), 'R313': (('U1', '46'), ('U31', '15'), 'U31')}
GRID = 0.2


def rebase(rows, feat, length):
    """The table at another length: everything but the RF strip moves with the forward edge."""
    d = length - feat['outline'][1]
    rows2 = {}
    for ref, (x, y, rot, side) in rows.items():
        move = ref in LANES or not r7.RF_PART.fullmatch(ref)
        rows2[ref] = (x, round(y + d, 4) if move else y, rot, side)
    feat2 = dict(outline=(feat['outline'][0], length),
                 supports=[(x, y + d if y > 30 else y) for x, y in feat['supports']],
                 ties=[(x, y + d) for x, y in feat['ties']])
    return rows2, feat2


def build(tmp, rows, feat):
    """r9_pcb.py's build steps in memory (no fill, no save)."""
    p = Path(tmp) / 'r8.kicad_pcb'
    if not p.exists():
        p.write_bytes(subprocess.run(['git', '-C', str(ROOT), 'show', f'{R8_COMMIT}:m3_design/assembly_review/m3.kicad_pcb'],
                                     capture_output=True, check=True).stdout)
        (Path(tmp) / 'kilib').symlink_to(r9_pcb.PROJECT / 'kilib')     # 3D models for the fit floors
    b = pcbnew.LoadBoard(str(p))
    pcbnew.KIID.SeedGenerator(r9_pcb.KIID_SEED)
    r9_lib.apply_variants(b)
    r9_lib.clear_overrides(b)
    _, kept = r9_pcb.strip(b)
    r9_pcb.outline(b, feat)
    r9_pcb.place(b, rows)
    r9_pcb.legends(b, kept)
    r9_pcb.block(b)
    return b


def search(b, cap, margin, slack):
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    m = LG.Model(b, list(fps))

    def xy(v):
        return mm(v.x), mm(v.y)

    def put(ref, x, y, rot):
        f = fps[ref]
        if f.IsFlipped():
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        f.SetOrientationDegrees(rot)
        f.SetPosition(LG.V(x, y))

    park = {r: (200.0 + 5 * i, -100.0) for i, r in enumerate(SEQ)}
    for r, (x, y) in park.items():
        put(r, x, y, 0)
    u1 = xy(fps['U1'].GetPosition())
    boxes = [m.part(r)['box'] for r in ('U1', 'U3', 'Y1')]
    spots = {}
    for ref in SEQ:
        (a, ap), (z, zp), far = LANES[ref]
        pa, pz = xy(fps[a].FindPadByNumber(ap).GetPosition()), xy(fps[z].FindPadByNumber(zp).GetPosition())
        fc = xy(fps[far].GetPosition())
        direct = math.dist(pa, pz)
        out = []
        for rot in (0, 90):
            for iy in range(int((u1[1] + 12 - 19) / GRID)):
                y = round(19 + GRID * iy, 3)
                for ix in range(int(45 / GRID)):
                    x = round(0.5 + GRID * ix, 3)
                    c = (x, y)
                    if math.dist(c, fc) - math.dist(c, u1) < max(margin, 1e-9):
                        continue                                        # SERIES / PULL_END (+ margin)
                    if any(LG._point_box(c, bx) < 5.94 + 0.4 for bx in boxes):
                        continue                                        # cheap R-10 pre-filter (the legaliser decides)
                    det = math.dist(pa, c) + math.dist(c, pz) - direct
                    if det > cap:
                        continue
                    if slack:
                        put(ref, x, y + slack, rot)
                        if m.violations(ref, first=True):
                            continue
                    put(ref, x, y, rot)
                    if not m.violations(ref, first=True):
                        bb = r8.courtyard(fps[ref]).BBox()
                        out.append((round(det, 2), x, y, rot, round(math.dist(c, fc) - math.dist(c, u1), 2),
                                    (mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))))
        put(ref, *park[ref], 0)
        out.sort()
        spots[ref] = out
    best = [None]

    def clash(p, q):
        return not (p[2] <= q[0] - 0.03 or q[2] <= p[0] - 0.03 or p[3] <= q[1] - 0.03 or q[3] <= p[1] - 0.03)

    def dfs(k, chosen, tot):
        if best[0] and tot >= best[0][0]:
            return
        if k == len(SEQ):
            for r, c in zip(SEQ, chosen):
                put(r, c[1], c[2], c[3])
            ok = all(not m.violations(r, first=True) for r in SEQ)
            for r in SEQ:
                put(r, *park[r], 0)
            if ok:
                best[0] = (round(tot, 2), {r: dict(detour=c[0], x=c[1], y=c[2], rot=c[3], series_margin=c[4])
                                           for r, c in zip(SEQ, chosen)})
            return
        for c in spots[SEQ[k]]:
            if best[0] and tot + c[0] >= best[0][0]:
                break
            if chosen and c[1] <= chosen[-1][1] + 0.3:
                continue
            if any(clash(c[5], o[5]) for o in chosen):
                continue
            dfs(k + 1, chosen + [c], tot + c[0])
    dfs(0, [], 0.0)
    return dict(u1=u1, spots={r: len(v) for r, v in spots.items()},
                least_single={r: (v[0][:5] if v else None) for r, v in spots.items()},
                holds=best[0] is not None, total_detour=best[0] and best[0][0], joint=best[0] and best[0][1])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--lengths', type=float, nargs='+', default=[98.0, 100.0, 102.0])
    ap.add_argument('--cap', type=float, default=6.0)
    ap.add_argument('--margin', type=float, default=0.25)
    ap.add_argument('--slack', type=float, default=0.2)
    ap.add_argument('--json', type=Path)
    a = ap.parse_args()
    rows, feat = r9_pcb.read_place(r9_pcb.PLACE)
    out, boards = [], []
    with tempfile.TemporaryDirectory() as tmp:
        for length in a.lengths:
            r, f = rebase(rows, feat, length)
            b = build(tmp, r, f)
            boards.append(b)                     # kept alive until the end (SWIG)
            res = dict(board_mm=length, cap=a.cap, margin=a.margin, slack=a.slack, **search(b, a.cap, a.margin, a.slack))
            out.append(res)
            print(f'{length:g} mm: U1 at y {res["u1"][1]:g}; spots {res["spots"]}; '
                  + (f'holds, total detour {res["total_detour"]} mm: '
                     + ', '.join(f'{k} ({v["x"]:g}, {v["y"]:g}) rot {v["rot"]}' for k, v in res['joint'].items())
                     if res['holds'] else 'no clean arrangement'), flush=True)
    if a.json:
        a.json.write_text(json.dumps(out, indent=1) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
