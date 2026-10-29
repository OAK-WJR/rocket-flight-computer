#!/usr/bin/env python3
"""R8 build step 5 gate: the power copper (r8_plan.md section 3 step 5; R8_DECISIONS D40-D50).

usage: <KiCad python3> -I m3_design/r8_power_check.py [board] [--report OUT.json]      exit 0 = every gate passes

The board is r8_power.py's output: the frozen placement, the rigid R7 copper and the step-5 power copper. Gates:
  rigid      the 12 check_r8 digests equal R7's (D15)
  drc        kicad-cli DRC with schematic parity, every severity (the pyro rules A-H of m3.kicad_dru included): no
             violation and no parity item. Allowed: the silkscreen classes r8_post.py settles (step 8), unconnected
             items of nets that later steps finish, dangling vias on the rigid copper's open ends (step 6) and PENDING
  complete   every net that carries step-5 copper has all its pads joined, except the shared rails of PARTIAL
  pyro       check_r8 inner_power_pyro (D18: no RAW_ACT / BAT_IN inner copper within 2.5 mm, in plan view, of
             PYRO1_BUS / IGN / OUT copper) and gate_servo (D19)
  inner      no In1 or In2 track besides the rigid CH1 block's (step 5 draws In2 as zones only; D20)
  in2        In2 holds only the fills of IN2_ISLANDS, island for island; no other net's In2 fill under a CH1 part's
             pad or barrel (pad + 0.5 mm) or under a pyro / servo lane on B.Cu (built or reserved), except inside U1's
             field (its courtyard + 0.5 mm), where the MCU-end dives run over the 3V3 plane (spike (a); D47)
  route      tools/route_check.py, profile r8: no failure, except on the rigid copper's open ends and PENDING
  reserved   the reservations later steps own (r8_keepclear.tsv, regenerated without the copper step 5 builds, D48),
             drawn as copper over this board, pass DRC's copper rules (r8_place_check.reserved); and the table is
             current: no row of a net step 5 routes completely (make_keepclear BUILT_NETS), none this copper covers
The 7.7 A paths' DC solve and IPC-2152 necks (tools/run_dc.sh, D12 limits) take minutes per grid: r8_build.sh runs them
at 0.1 mm once the copper is final, after step 7 (fix pass 1, R8P1-INTEGRITY-02); D49 records the step-5 figures.
"""
import argparse
import collections
import csv
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r8  # noqa: E402
import importlib.util  # noqa: E402
import r8_legalise  # noqa: E402
import r8_place_check  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
CLI = r8_place_check.CLI
BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
DRC_DEFERRED = r8_place_check.DRC_DEFERRED
# rails that step 5 starts and later steps tap (step 6: the pull-ups, bypasses and modules of its signal families, the
# sensors' 3V3A, the U13 translator supply; step 7: GND stitching)
PARTIAL = {'GND', '3V3', '3V3A', 'CAM_5V'}
# step-5 copper whose far end a later step continues: (net, segment, reason)
PENDING = [('3V3A', ((15.0, 62.2), (24.025, 62.2)),
            "the 3V3A trunk's F.Cu hop over the pyro corridor ends at the via (15.0, 62.2); step 6 (imu_i2c) runs it "
            "on to U4 / U5 / C30-C32 (D48)")]
IN2_ISLANDS = {'GND': 1, '3V3': 1, 'RAW_ACT': 2, 'BAT_IN': 1}     # D47: the plane, the MCU region, spike (c)'s islands
LANE = re.compile(r'^(PYRO1_|ARM1_|SERVO\d_)')
PAD_MARGIN, U1_MARGIN, STEP = 0.5, 0.5, 0.1
INFO = ('width_change_junction', 'pad_end_offcentre', 'segment_inside_pad', 'passes_through_pad', 'extra_bends',
        'short_layer_hop', 'power_via_no_gnd')                     # route_check information, reported


def _seg_d(p, a, b):
    lx, ly = b[0] - a[0], b[1] - a[1]
    n = lx * lx + ly * ly
    t = 0.0 if n == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * lx + (p[1] - a[1]) * ly) / n))
    return math.hypot(p[0] - a[0] - t * lx, p[1] - a[1] - t * ly)


def _xy(v):
    return mm(v.x), mm(v.y)


def rigid_items(board):
    """The rigid R7 tracks and vias (check_r8 D15 selection) whose lanes later steps continue: the CH1 block copper,
    the RF lines and GNSS_ANT_DC's strip copper."""
    items = list(check_r8.ch1_copper(board))
    items += [t for t in board.GetTracks() if t.GetNetname() in check_r8.RF_NETS or
              (t.GetNetname() == 'GNSS_ANT_DC' and (t.GetClass() == 'PCB_VIA' or t.GetLayer() == pcbnew.F_Cu))]
    return items


def on_items(net, p, items, tol=0.02):
    for t in items:
        if t.GetNetname() != net:
            continue
        if t.GetClass() == 'PCB_VIA':
            if math.dist(p, _xy(t.GetPosition())) < tol:
                return True
        elif _seg_d(p, _xy(t.GetStart()), _xy(t.GetEnd())) < tol:
            return True
    return False


def pending(net, p, tol=0.05):
    return next((why for n, (a, b), why in PENDING if n == net and _seg_d(p, a, b) < tol), None)


def drc(board_path, rigid):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--schematic-parity', '--format', 'json', '-o', str(out),
                        str(board_path)], capture_output=True)
        rep = json.loads(out.read_text())
    bad, deferred, allowed = [], collections.Counter(), collections.Counter()
    for v in rep['violations']:
        if v['type'] in DRC_DEFERRED:
            deferred[v['type']] += 1
            continue
        if v['type'] == 'via_dangling' and len(v['items']) == 1:
            it = v['items'][0]
            net = re.search(r'\[([^\]]*)\]', it['description']).group(1)
            p = (it['pos']['x'], it['pos']['y'])
            if on_items(net, p, rigid):
                allowed['rigid via dangling (step 6 connects it)'] += 1
                continue
            if pending(net, p):
                allowed[f'{net} trunk end (PENDING)'] += 1
                continue
        bad.append(f"{v['type']}: " + ' | '.join(i['description'] for i in v['items']))
    for p in rep.get('schematic_parity', []):
        bad.append(f"parity {p['type']}: " + ' | '.join(i['description'] for i in p.get('items', [])))
    open_nets = collections.Counter()
    for u in rep['unconnected_items']:
        for i in u['items']:
            m = re.search(r'\[([^\]]*)\]', i['description'])
            if m:
                open_nets[m.group(1)] += 1
    return bad, dict(unconnected=len(rep['unconnected_items']), deferred=dict(deferred), allowed=dict(allowed)), \
        open_nets


def complete(board, rigid, open_nets):
    ids = {t.m_Uuid.AsString() for t in rigid}
    nets = {t.GetNetname() for t in board.GetTracks() if t.m_Uuid.AsString() not in ids}
    nets |= {z.GetNetname() for z in board.Zones() if not z.GetIsRuleArea()}
    nets.discard('')
    issues = [f'{n}: {open_nets[n]} unconnected item(s), but step 5 routes it completely'
              for n in sorted(nets - PARTIAL) if open_nets.get(n)]
    return issues, dict(nets=len(nets - PARTIAL), partial={n: open_nets.get(n, 0) for n in sorted(PARTIAL)})


def inner(board, rigid):
    ids = {t.m_Uuid.AsString() for t in rigid}
    bad = [t for t in board.GetTracks() if t.GetClass() != 'PCB_VIA' and t.GetLayer() in (pcbnew.In1_Cu, pcbnew.In2_Cu)
           and t.m_Uuid.AsString() not in ids]
    return [f'{t.GetNetname()} track on {t.GetLayerName()} at {_xy(t.GetStart())}' for t in bad], \
        dict(rigid_inner_tracks=sum(1 for t in rigid if t.GetClass() != 'PCB_VIA' and
                                    t.GetLayer() in (pcbnew.In1_Cu, pcbnew.In2_Cu)))


def keepclear_rows(path=None):
    with open(path or r8_legalise.KEEPCLEAR) as fh:
        return list(csv.DictReader((line for line in fh if not line.startswith('#')), delimiter='\t'))


def in2(board, reservations):
    issues, ev = [], {}
    fills = [(z.GetNetname(), z.GetFilledPolysList(pcbnew.In2_Cu)) for z in board.Zones()
             if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In2_Cu) and z.HasFilledPolysForLayer(pcbnew.In2_Cu)]
    islands = collections.Counter()
    for net, poly in fills:
        islands[net] += poly.OutlineCount()
    ev['islands'] = dict(islands)
    if dict(islands) != IN2_ISLANDS:
        issues.append(f'In2 islands {dict(islands)}, planned {IN2_ISLANDS}')

    def under(x, y):
        v = pcbnew.VECTOR2I(MM(x), MM(y))
        return [n for n, poly in fills if poly.Contains(v)]

    u1 = r8_legalise._box(check_r8.courtyard(board.FindFootprintByReference('U1')))
    u1 = (u1[0] - U1_MARGIN, u1[1] - U1_MARGIN, u1[2] + U1_MARGIN, u1[3] + U1_MARGIN)
    ev['u1_field'] = tuple(round(c, 2) for c in u1)
    found = collections.defaultdict(list)
    pads = 0
    for f in board.GetFootprints():
        if f.GetReference() not in check_r8.CH1_PARTS:
            continue
        for p in f.Pads():
            pads += 1
            bb = p.GetBoundingBox()
            x0, y0, x1, y1 = (mm(bb.GetLeft()) - PAD_MARGIN, mm(bb.GetTop()) - PAD_MARGIN,
                              mm(bb.GetRight()) + PAD_MARGIN, mm(bb.GetBottom()) + PAD_MARGIN)
            for i in range(int((x1 - x0) / STEP) + 1):
                for j in range(int((y1 - y0) / STEP) + 1):
                    x, y = x0 + i * STEP, y0 + j * STEP
                    for n in under(x, y):
                        if n not in ('GND', p.GetNetname()):
                            found[f'In2 {n} under {f.GetReference()}.{p.GetNumber()} ({p.GetNetname()})'].append(
                                (round(x, 2), round(y, 2)))
    lanes = [('built', t.GetNetname(), _xy(t.GetStart()), _xy(t.GetEnd())) for t in board.GetTracks()
             if t.GetClass() != 'PCB_VIA' and t.GetLayer() == pcbnew.B_Cu and LANE.match(t.GetNetname())]
    lanes += [('reserved', r['net'], (float(r['x0']), float(r['y0'])), (float(r['x1']), float(r['y1'])))
              for r in reservations if r['layer'] == 'B' and LANE.match(r['net'])]
    exempt = 0
    for kind, net, a, b in lanes:
        n = max(1, int(math.dist(a, b) / STEP))
        for k in range(n + 1):
            x, y = a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n
            if u1[0] <= x <= u1[2] and u1[1] <= y <= u1[3]:
                exempt += 1
                continue
            for z in under(x, y):
                if z != 'GND':
                    found[f'In2 {z} under the {kind} {net} lane'].append((round(x, 2), round(y, 2)))
    for k, pts in sorted(found.items()):
        issues.append(f'{k}: {len(pts)} points, first {pts[0]}')
    ev.update(ch1_pads=pads, lane_segments=len(lanes), u1_field_samples=exempt)
    return issues, ev


def route(board_path, board, rigid):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'route.json'
        subprocess.run([sys.executable, '-I', str(ROOT / 'tools/route_check.py'), str(board_path), '--profile', 'r8',
                        '--report', str(out)], capture_output=True)
        rep = json.loads(out.read_text())
    bad, allowed = [], collections.Counter()
    for f in rep['failures']:
        p = (f['x'], f['y'])
        if on_items(f['net'], p, rigid, 0.05):
            allowed[f"{f['cat']} on the rigid copper (step 6 continues it)"] += 1
        elif pending(f['net'], p):
            allowed[f"{f['cat']} {f['net']} (PENDING)"] += 1
        else:
            bad.append(f"{f['cat']} {f['net']} {f['layer']} ({f['x']}, {f['y']})")
    info = collections.Counter(i['cat'] for i in rep['instances'] if i['cat'] in INFO)
    return bad, dict(failures=len(rep['failures']), allowed=dict(allowed), information=dict(info))


def _keepclear_tool():
    path = ROOT / 'm3_design/assembly_review/sources/r8_design/step4/make_keepclear.py'
    spec = importlib.util.spec_from_file_location('make_keepclear', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def stale(board_path, reservations):
    """Reservation rows step 5 has built or owns: the table was not regenerated after r8_power.py changed."""
    kc = _keepclear_tool()
    tracks, vias = kc.built_copper(board_path)
    out = []
    for r in reservations:
        row = (r['family'], r['net'], r['layer'], float(r['w']), float(r['x0']), float(r['y0']), float(r['x1']),
               float(r['y1']))
        if r['net'] in kc.BUILT_NETS or kc.is_built(row, tracks, vias):
            out.append(f"stale reservation {r['family']} {r['net']} {r['layer']} ({r['x0']}, {r['y0']})-({r['x1']}, "
                       f"{r['y1']}): step 5 builds it; regenerate r8_keepclear.tsv (make_keepclear.py ... BUILT_BOARD)")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', nargs='?', type=Path, default=BOARD)
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    path = args.board.resolve()
    board = pcbnew.LoadBoard(str(path))
    report, fails = {}, {}

    def gate(name, issues, evidence):
        report[name] = dict(ok=not issues, issues=issues, evidence=evidence)
        fails[name] = len(issues)
    issues, ev = check_r8.rigid(board)
    gate('rigid', issues, {k: v['sha256'][:16] for k, v in ev.items()})
    rigid = rigid_items(board)
    issues, ev, open_nets = drc(path, rigid)
    gate('drc', issues, ev)
    issues, ev = complete(board, rigid, open_nets)
    gate('complete', issues, ev)
    issues, ev = check_r8.inner_power_pyro(board)
    found, ev2 = check_r8.gate_servo(board, check_r8.close_layer_pairs(str(path)))
    gate('pyro', issues + found, dict(inner_power_pyro=ev, gate_servo=ev2))
    issues, ev = inner(board, rigid)
    gate('inner', issues, ev)
    issues, ev = in2(board, keepclear_rows())
    gate('in2', issues, ev)
    issues, ev = route(path, board, rigid)
    gate('route', issues, ev)
    issues, ev = r8_place_check.reserved(path)
    issues += stale(path, keepclear_rows())
    gate('reserved', issues, ev)
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name   # no local absolute paths (AGENTS.md)
    report.update(board=str(shown), board_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  pending=[dict(net=n, segment=s, reason=r) for n, s, r in PENDING])
    for name, n in fails.items():
        print(f'{name:10s} {"OK" if not n else f"FAIL ({n})"}')
        for i in report[name]['issues'][:20]:
            print('    ', i)
    print('in2', report['in2']['evidence']['islands'], 'pyro nearest',
          report['pyro']['evidence']['inner_power_pyro'].get('nearest'))
    print('route', report['route']['evidence'])
    ok = not any(fails.values())
    print('R8 power gate:', 'OK' if ok else 'FAIL')
    if args.report:
        args.report.write_text(json.dumps(report, indent=2, default=str) + '\n')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
