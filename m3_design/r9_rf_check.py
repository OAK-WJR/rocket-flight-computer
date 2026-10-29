#!/usr/bin/env python3
"""R9 build step 4 gate: the RF strip copper (r9_plan.md section 4 step 4; R9_DECISIONS D-S4-*).

usage: <KiCad python3> -I m3_design/r9_rf_check.py [board] [--report OUT.json]
       exit 0 = every gate passes

The board is r9_rf.py's output (the step-3 placement plus the strip copper). Gates (tools/check_r9.py's rules are
called, never restated or weakened):
  frames     every strip part sits where its frame template (r9_rf.PARTS) puts it, and the frames agree (r9_rf.Frames)
  r7         R7 congruence of the chains, in each jack's frame, against R7's committed board (git 431025d): every
             chain part's position and rotation equal R7's but the recorded deviations (r9_rf.R7_DEVIATIONS, each a
             decision); the radio chain has none
  launch     each jack's launch, in its frame, against R7's J31 (the launch pass 2 qualified; R7's J30 had one via
             0.5 mm off, D-S1-19): the GND vias inside the launch window (|x| <= 2.0, y 0-4.6) are the eight of
             check_r9.LAUNCH within its 0.05 mm, with R7's size; no other copper in the window but the jack pads and
             the line on the axis; the In1 cut-out equal; the F.Cu GND copper (pads and fill) in the window the same
             as R7's to LAUNCH_XOR_MAX mm2 (both jacks against R7 and against each other)
  contract   check_r9 R-1 ... R-13, LC-1 and K-copper (vias in pads, overlap-only joints, the small-GND-pad thermal
             policy, via rings and holes off paste): every rule holds
  gcpw       every sample check_r9 R-5 takes on the RF lines outside the declared windows (0.05 mm along each track,
             the F.Cu GND gap on each side scanned at 0.01 mm): Z0 from tools/gcpw_solve.py for its gap pair (coated,
             over In1) within 50 +- 2.5 ohm. Each distinct gap pair is solved once
  route      tools/route_check.py, profile r9 (empty allowlist and leftover list): no failing instance and no
             unrecorded leftover on the board (only this step's copper exists)
  drc        kicad-cli DRC with schematic parity, every severity: no violation but the silkscreen classes step 8
             settles, no parity item, and no unconnected item on a net this step completes (r9_rf.STRIP_NETS) nor
             between two GND items inside the strip
  corridors  no F.Cu copper or via of this step inside a lane corridor reserved for step 7's F.Cu lanes
             (r9_rf.CORRIDORS), but the fence row, whose lane openings step 7 makes
"""
import argparse
import collections
import hashlib
import importlib.util
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
import check_r8 as r8  # noqa: E402
import check_r9 as C9  # noqa: E402
import route_check as rc  # noqa: E402
import r9_rf  # noqa: E402

_spec = importlib.util.spec_from_file_location('gcpw_solve', ROOT / 'tools/gcpw_solve.py')
GS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GS)

mm, MM = pcbnew.ToMM, pcbnew.FromMM
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
R7_COMMIT = '431025d'
R7_JACK = {'J30': 12.85, 'J31': 31.54}
CONTRACT_RULES = ('LC-1', 'K-copper') + tuple(f'R-{k}' for k in range(1, 14))
DRC_DEFERRED = {'silk_over_copper', 'silk_overlap', 'silk_edge_clearance'}   # r9_post.py (step 8)
Z_NOM, Z_TOL = 50.0, 2.5
LAUNCH_WIN = 2.0                      # |x| in the jack frame
LAUNCH_XOR_MAX = 0.02                 # mm2 of F.Cu GND copper that may differ from R7's launch (numerical)


def gate_frames(b):
    try:
        f = r9_rf.Frames(b)
        f.check_parts()
        return [], dict(origins=f.origin)
    except AssertionError as e:
        return [f'frames: {e}'], {}


def r7_board():
    tmp = tempfile.TemporaryDirectory()
    p = Path(tmp.name) / 'r7.kicad_pcb'
    p.write_bytes(subprocess.run(['git', '-C', str(ROOT), 'show', f'{R7_COMMIT}:m3_design/assembly_review/m3.kicad_pcb'],
                                 capture_output=True, check=True).stdout)
    return pcbnew.LoadBoard(str(p)), tmp     # both kept alive by the caller (SWIG, step-1 note)


def frame_pos(f, jack_x):
    return (round(mm(f.GetPosition().x) - jack_x, 4), round(mm(f.GetPosition().y), 4),
            round(((f.GetOrientationDegrees() + 180) % 360) - 180, 3), f.IsFlipped())


def gate_r7(b, r7, frames):
    issues, ev = [], {}
    fps, fps7 = {f.GetReference(): f for f in b.GetFootprints()}, {f.GetReference(): f for f in r7.GetFootprints()}
    for ref, (frame, *_rest) in sorted(r9_rf.PARTS.items()):
        if frame not in ('J30', 'J31'):
            continue
        now = frame_pos(fps[ref], frames.origin[frame][0])
        was = frame_pos(fps7[ref], R7_JACK[frame])
        same = all(abs(a - c) < 1e-3 for a, c in zip(now[:3], was[:3])) and now[3] == was[3]
        ev[ref] = dict(r9=now, r7=was, deviation=r9_rf.R7_DEVIATIONS.get(ref))
        if same and ref in r9_rf.R7_DEVIATIONS:
            issues.append(f'r7: {ref} is R7\'s; its recorded deviation is stale')
        if not same and ref not in r9_rf.R7_DEVIATIONS:
            issues.append(f'r7: {ref} at {now} in {frame}\'s frame, R7 {was}: not a recorded deviation')
    return issues, ev


def launch_window(b, jack_x):
    """(GND vias [(dx, y, dia, drill)], other copper [str], F.Cu GND copper SHAPE_POLY_SET in the jack frame window)."""
    x0, x1 = jack_x - LAUNCH_WIN, jack_x + LAUNCH_WIN
    L = C9.LAUNCH
    win = C9.rect_poly(x0, L['y0'], x1, L['y1'])
    vias, other = [], []
    for t in b.GetTracks():
        bb = t.GetBoundingBox()
        if mm(bb.GetRight()) < x0 or mm(bb.GetLeft()) > x1 or mm(bb.GetTop()) > L['y1']:
            continue
        if t.GetClass() == 'PCB_VIA':
            x, y = C9.xy(t.GetPosition())
            inside = abs(x - jack_x) <= LAUNCH_WIN and y <= L['y1']
            if t.GetNetname() == 'GND' and inside:
                vias.append((round(x - jack_x, 3), round(y, 3), round(mm(t.GetWidth(pcbnew.F_Cu)), 3),
                             round(mm(t.GetDrillValue()), 3)))
            elif t.GetNetname() != 'GND':
                other.append(f'{t.GetNetname()} via at ({x:.2f}, {y:.2f})')
            continue
        a, c = C9.xy(t.GetStart()), C9.xy(t.GetEnd())
        on_axis = abs(a[0] - jack_x) < 1e-3 and abs(c[0] - jack_x) < 1e-3 and abs(mm(t.GetWidth()) - C9.RF_W) < 1e-3
        if not on_axis:
            other.append(f'{t.GetNetname()} track {a}-{c}')
    gnd = C9.gnd_copper(b, pcbnew.F_Cu)
    gnd.BooleanIntersection(win)
    gnd.Move(pcbnew.VECTOR2I(MM(-jack_x), 0))
    return sorted(vias), other, gnd


def xor_area(a, c):
    u = pcbnew.SHAPE_POLY_SET(a)
    u.BooleanSubtract(c)
    v = pcbnew.SHAPE_POLY_SET(c)
    v.BooleanSubtract(a)
    return C9.area_mm2(u) + C9.area_mm2(v)


def gate_launch(b, r7, frames):
    issues, ev = [], {}
    ref_vias, _, ref_gnd = launch_window(r7, R7_JACK['J31'])
    L = C9.LAUNCH
    want = sorted(L['vias'])
    fills = {}
    for jack in ('J30', 'J31'):
        x = frames.origin[jack][0]
        vias, other, gnd = launch_window(b, x)
        fills[jack] = gnd
        pos = sorted((v[0], v[1]) for v in vias)
        ok_pos = len(pos) == len(want) and all(math.dist(p, w) <= L['via_tol'] + 1e-6 for p, w in zip(pos, want))
        sizes = {v[2:] for v in vias} | {v[2:] for v in ref_vias}
        d_r7 = xor_area(gnd, ref_gnd)
        ev[jack] = dict(vias=vias, other=other, gnd_xor_r7_mm2=round(d_r7, 4))
        if not ok_pos:
            issues.append(f'launch: {jack}: GND vias in the launch window {pos}, required {want} (+-{L["via_tol"]})')
        if len(sizes) != 1:
            issues.append(f'launch: {jack}: launch via sizes {sorted(sizes)} differ from R7\'s')
        if other:
            issues.append(f'launch: {jack}: foreign copper in the launch window: {other}')
        if d_r7 > LAUNCH_XOR_MAX:
            issues.append(f'launch: {jack}: F.Cu GND copper in the launch window differs from R7\'s by {d_r7:.3f} mm2')
        areas = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == f'R9_{jack}_launch_In1']
        if len(areas) != 1 or len(C9.launch_area(C9.Ctx(b), b.FindFootprintByReference(jack))) != 1:
            issues.append(f'launch: {jack}: the In1 cut-out R9_{jack}_launch_In1 is not the qualified rectangle')
    d = xor_area(fills['J30'], fills['J31'])
    ev['J30_vs_J31_mm2'] = round(d, 4)
    if d > LAUNCH_XOR_MAX:
        issues.append(f'launch: J30 and J31 launch copper differ by {d:.3f} mm2')
    return issues, ev


def gate_contract(b, path):
    res = C9.check_board(b, path.parent, path, only=set(CONTRACT_RULES))
    return res['issues'], {k: v['evidence'] for k, v in res['rules'].items()}


def line_samples(b):
    """R-5's samples on the RF lines outside its declared windows: [(chain, net, x, y, gap_left, gap_right)] (mm)."""
    ctx = C9.Ctx(b)
    gnd = C9.gnd_copper(b, pcbnew.F_Cu, ctx.y_f + 3)
    cut = pcbnew.SHAPE_POLY_SET()
    for f in C9.jacks(ctx):
        for z in C9.launch_area(ctx, f):
            cut.BooleanAdd(z.Outline())
    rf_nets = {n for ch in C9.CHAINS.values() for n in ch['nets']}
    paths = {n: C9.rf_path(ctx, n) for n in C9.CHAINS}
    bends = {n: (C9.path_bends(p)[1] if p else []) for n, p in paths.items()}
    steps = int(round(C9.GCPW_REACH / C9.GCPW_SCAN))
    out = []
    for t in sorted((t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in rf_nets),
                    key=lambda t: (C9.xy(t.GetStart()), C9.xy(t.GetEnd()))):
        chain = next(n for n, ch in C9.CHAINS.items() if t.GetNetname() in ch['nets'])
        (ax, ay), (bx, by) = C9.xy(t.GetStart()), C9.xy(t.GetEnd())
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        half = mm(t.GetWidth()) / 2
        for k in range(int(L // C9.GCPW_STEP) + 2):
            s = min(k * C9.GCPW_STEP, L)
            cx, cy = ax + ux * s, ay + uy * s
            gaps = []
            for sx, sy in ((-uy, ux), (uy, -ux)):
                hit = None
                for j in range(1, steps + 1):
                    dd = half + j * C9.GCPW_SCAN
                    if gnd.Contains(pcbnew.VECTOR2I(MM(cx + sx * dd), MM(cy + sy * dd))):
                        hit = j
                        break
                gaps.append(hit)
            pv = pcbnew.VECTOR2I(MM(cx), MM(cy))
            if cut.OutlineCount() and cut.Contains(pv):
                continue
            if all(g is not None and C9.GAP_LO <= g <= C9.GAP_HI for g in gaps):
                out.append((chain, t.GetNetname(), round(cx, 3), round(cy, 3), gaps[0] * C9.GCPW_SCAN,
                            gaps[1] * C9.GCPW_SCAN))
                continue
            near_bend = any(math.dist((cx, cy), v) <= 0.5 for v in bends[chain])
            if near_bend and all(g is not None and C9.GAP_LO <= g and g * C9.GCPW_SCAN <= C9.R5_BEND_GAP + 1e-9
                                 for g in gaps):
                out.append((chain, t.GetNetname(), round(cx, 3), round(cy, 3), gaps[0] * C9.GCPW_SCAN,
                            gaps[1] * C9.GCPW_SCAN))
            # every other sample is a declared window or an R-5 failure (the contract gate reports those)
    return out


def judge_pairs(pairs):
    """(issues, {sorted gap pair: Z0 ohm}, worst) for a Counter of (gap_left, gap_right) mm pairs."""
    issues, z, worst = [], {}, None
    for gl, gr in sorted(pairs):
        key = tuple(sorted((gl, gr)))
        if key not in z:
            r = GS.z0(w=C9.RF_W, gap_left=key[0], gap_right=key[1], coated=True)
            z[key] = round(r['z0_ohm'], 2)
    for (gl, gr), n in sorted(pairs.items()):
        v = z[tuple(sorted((gl, gr)))]
        if worst is None or abs(v - Z_NOM) > abs(worst[0] - Z_NOM):
            worst = (v, gl, gr)
        if abs(v - Z_NOM) > Z_TOL:
            issues.append(f'gcpw: gaps ({gl}, {gr}) mm -> {v} ohm at {n} samples (50 +- {Z_TOL})')
    return issues, z, worst


def gate_gcpw(b):
    samples = line_samples(b)
    pairs = collections.Counter((round(gl, 2), round(gr, 2)) for _, _, _, _, gl, gr in samples)
    issues, z, worst = judge_pairs(pairs)
    zs = list(z.values())
    ev = dict(samples=len(samples), by_chain=dict(collections.Counter(s[0] for s in samples)),
              gap_pairs={f'{a}/{c}': n for (a, c), n in sorted(pairs.items())},
              z0_ohm={f'{a}/{c}': v for (a, c), v in sorted(z.items())},
              z0_range_ohm=[min(zs), max(zs)] if zs else None, worst=worst)
    if not samples:
        issues.append('gcpw: no line sample found')
    return issues, ev


def gate_route(b):
    rc.set_profile('r9')
    inst = rc.scan(b, [])
    bumps, searched = rc.bump_audit(b)
    inst += bumps
    failures, allowed, stale = rc.evaluate(inst)
    _, missing, _ = rc.leftover_check(inst)
    issues = [f"route: {d['cat']} {d['net']} {d['layer']} ({d['x']}, {d['y']})" for d in failures]
    issues += [f"route: unrecorded leftover {d['cat']} {d['net']} {d['layer']} ({d['x']}, {d['y']})" for d in missing]
    issues += [f'route: allowlist entry {e[:4]}' for e in allowed + stale]
    return issues, dict(instances=len(inst), by_category=dict(collections.Counter(d['cat'] for d in inst)),
                        bump_windows=searched)


def drc(path, strip_nets, y_f):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--schematic-parity', '--format', 'json', '-o', str(out),
                        str(path)], capture_output=True)
        rep = json.loads(out.read_text())
    bad, deferred = [], collections.Counter()
    for v in rep['violations']:
        if v['type'] in DRC_DEFERRED:
            deferred[v['type']] += 1
            continue
        bad.append(f"drc: {v['type']}: " + ' | '.join(i['description'] for i in v['items']))
    for p in rep.get('schematic_parity', []):
        bad.append(f"drc: parity {p['type']}: " + ' | '.join(i['description'] for i in p.get('items', [])))
    strip_open = 0
    for u in rep.get('unconnected_items', []):
        nets = {i['description'].split('[')[1].split(']')[0] for i in u['items'] if '[' in i['description']}
        ys = [i['pos']['y'] for i in u['items']]
        if nets & set(strip_nets) or ('GND' in nets and all(y < y_f for y in ys)):
            strip_open += 1
            bad.append('drc: unconnected ' + ' | '.join(i['description'] for i in u['items']))
    return bad, dict(unconnected_total=len(rep['unconnected_items']), unconnected_strip=strip_open,
                     deferred=dict(deferred))


def gate_corridors(b, frames):
    issues = []
    boxes = r9_rf.corridor_boxes(frames)
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_VIA' and t.GetLayer() != pcbnew.F_Cu:
            continue                                  # the lanes are F.Cu: only F.Cu copper and vias block them
        if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND' and abs(mm(t.GetPosition().y) - r9_rf.FENCE_Y) < 1e-3:
            continue                                  # the fence row: step 7 opens its lane gaps (R-7 openings)
        shape = t.GetEffectiveShape(pcbnew.F_Cu)
        for x0, y0, x1, y1, lanes in boxes:
            if pcbnew.SHAPE.Collide(C9.rect_poly(x0, y0, x1, y1), shape, 0):
                kind = 'via' if t.GetClass() == 'PCB_VIA' else 'track'
                issues.append(f'corridors: {t.GetNetname()} {kind} at {C9.xy(t.GetPosition())} inside the corridor '
                              f'for {lanes}')
    return issues, dict(corridors=len(boxes))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', nargs='?', type=Path, default=BOARD)
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    path = args.board.resolve()
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    r7, _keep = r7_board()
    board = pcbnew.LoadBoard(str(path))
    report, fails = {}, {}

    def gate(name, result):
        issues, evidence = result
        report[name] = dict(ok=not issues, issues=issues, evidence=evidence)
        fails[name] = len(issues)
    gate('frames', gate_frames(board))
    frames = r9_rf.Frames(board)
    gate('r7', gate_r7(board, r7, frames))
    gate('launch', gate_launch(board, r7, frames))
    gate('contract', gate_contract(board, path))
    gate('gcpw', gate_gcpw(board))
    gate('route', gate_route(board))
    gate('drc', drc(path, r9_rf.strip_nets(board), C9.Y_F))
    gate('corridors', gate_corridors(board, frames))
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name
    report.update(board=str(shown), board_sha256=sha,
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  builder_sha256=hashlib.sha256((ROOT / 'm3_design/r9_rf.py').read_bytes()).hexdigest())
    for name, n in fails.items():
        print(f'{name:10s} {"OK" if not n else f"FAIL ({n})"}')
        for i in report[name]['issues'][:25]:
            print('    ', i)
    g = report['gcpw']['evidence']
    print('gcpw', g.get('samples'), 'line samples, Z0', g.get('z0_range_ohm'), 'ohm; launch XOR',
          {k: v.get('gnd_xor_r7_mm2') for k, v in report['launch']['evidence'].items() if isinstance(v, dict)})
    ok = not any(fails.values())
    print('R9 RF strip gate:', 'OK' if ok else 'FAIL')
    if args.report:
        args.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
