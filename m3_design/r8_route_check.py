#!/usr/bin/env python3
"""R8 build step 6 gate, run after each signal family (r8_plan.md section 3 step 6; R8_DECISIONS D51 on).

usage: <KiCad python3> -I m3_design/r8_route_check.py FAMILY [board] [--report OUT.json]    exit 0 = every gate passes

The board is r8_route.py's output after FAMILY: the power copper of step 5 and every family up to FAMILY (in
r8_route.FAMILIES order). "Done" below means the nets of those families. Gates:
  rigid      the 12 check_r8 digests equal R7's (D15)
  drc        kicad-cli DRC with schematic parity, every severity (pyro rules A-H of m3.kicad_dru included): no
             violation and no parity item, except the silkscreen classes r8_post.py settles (step 8) and a dangling
             via on the rigid copper's open end of a net a later family routes
  complete   every pad of every done net is joined (0 unconnected items); GND too from imu on (imu joins the sensors'
             last open GND pads, so a later family's copper must not cut a pour into an island); after the last
             family, links, every net on the board, the shared rails included
  route      tools/route_check.py, profile r8 (A8 the only allowlist entry, no leftovers list): no failure and no
             unrecorded non-critical hygiene instance on a done net or a rail this family draws, except GND pour
             findings (fingers, slivers: step 7's stitching) and the open ends of nets a later family routes
  budget     this family's figures within its BUDGET: signal track length, signal vias, critical layer changes, the
             worst copper / octilinear-MST ratio of its nets more than route_check's 2 mm slack longer than their MST
             (the D10 baseline where it applies); the record (length, vias, layer changes, bends) is
             reported per family and summed against the scorecard targets (r8_plan section 2, soft)
  pyro       check_r8 inner_power_pyro (D18) and gate_servo (D19: PYRO1_GATE_N >= 0.5 mm from servo PWM copper)
  inner      no In1 or In2 track besides the rigid CH1 block's (D20)
  in2        r8_power_check's In2 gate: the islands of D47, no other net's In2 fill under a CH1 pad or under a pyro /
             servo lane on B.Cu (built), except inside U1's field (D47)
  contract   tools/check_r8.py on the board: every finding is one a later step owns (LATER below) and
             check_actuators.py passes
  l10        R5 L10: no bottom courtyard within 1.0 mm of a pyro via (PYRO* / ARM1* nets; TP122, the gate test pad,
             as r8_legalise), except the two MCU-side sense dives of L10_EXCEPT at no worse than their measured gaps
             (R8_DECISIONS D61; R5_VALIDATION's "MCU-side pyro vias" exception)
  reserved   the reservations left in r8_keepclear.tsv (step 7's GND vias; the table is regenerated with the copper
             step 6 builds, D60) drawn on the board pass DRC's copper rules (r8_place_check.reserved), and no row is
             left of a net a done family routes (a stale table)
"""
import argparse
import collections
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
import r8_power_check  # noqa: E402
import r8_place_check  # noqa: E402
import r8_route  # noqa: E402
import route_check as rc  # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
CLI = r8_place_check.CLI
BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
RAILS = ('GND', '3V3', '3V3A', 'CAM_5V')
GND_POUR_LATER = ('pour_finger', 'pour_sliver', 'pad_pour_cut')         # GND stitching: step 7 (r8_ground.py)
# rigid copper whose lane a family continues: (net, family that joins it)
RIGID_OPEN = {'PYRO1_GATE_N': 'pyro', 'PYRO1_CONT': 'pyro', 'ARM1_SENSE': 'pyro', 'GNSS_ANT_DC': 'rf'}
# step-5 copper a family continues (r8_power_check PENDING): (net, segment, family)
PENDING = [('3V3A', ((15.0, 62.2), (24.025, 62.2)), 'imu')]
# check_r8 findings a later step owns: (pattern, owner, family that clears it or None for a later build step)
LATER = [
    (r'^J[29]\.\d: silkscreen must identify', 'r8_post (step 8): the J2 / J9 pin legends', None),
    (r'^terminal pin legend |^J\d+\.\d+: \d+ legends "', 'r8_post (step 8): the terminal pin legends (D92)', None),
    (r'^strip fence: ', 'r8_ground (step 7): the fence row (D16)', None),
    (r'^[FB]\.Cu GND copper at .* in the RF strip is .* from a GND via', 'r8_ground (step 7): strip GND reach', None),
    (r'^In2 track of ARM1_SENSE: 3\.4 mm in 1 segments, first at \(14\.55, 94\.15\)',
     'step-4 open item 1 (D15 against D20): the rigid CH1 ARM1_SENSE In2 link, for the orchestrator', None),
    (r'^C100: |^C93: ', 'camera family: U12 bypass routes', 'camera'),
]
CRITICAL_CLASSES = rc.SIGNAL_CRITICAL
TARGETS = dict(signal_track_mm=2300.0, signal_vias=75, critical_layer_changes=32, bends=400)   # r8_plan section 2


def done_families(family):
    return r8_route.FAMILIES[:r8_route.FAMILIES.index(family) + 1]


def family_nets(names):
    nets = set()
    for f in names:
        nets |= set(r8_route.load_family(f).NETS)
    return nets


def _seg_d(p, a, b):
    return r8_power_check._seg_d(p, a, b)


def open_end(net, p, board, done):
    """A rigid open end (or step-5 PENDING end) of a net a later family routes."""
    fam = RIGID_OPEN.get(net)
    if fam and fam not in done and r8_power_check.on_items(net, p, r8_power_check.rigid_items(board), 0.05):
        return f'{net} rigid open end ({fam} joins it)'
    for n, (a, b), f in PENDING:
        if n == net and f not in done and _seg_d(p, a, b) < 0.05:
            return f'{net} step-5 trunk end ({f} continues it)'
    return None


def drc(board_path, board, done, last):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--severity-all', '--schematic-parity', '--format', 'json', '-o', str(out),
                        str(board_path)], capture_output=True)
        rep = json.loads(out.read_text())
    bad, deferred, allowed = [], collections.Counter(), collections.Counter()
    for v in rep['violations']:
        if v['type'] in r8_place_check.DRC_DEFERRED:
            deferred[v['type']] += 1
            continue
        if v['type'] == 'via_dangling' and len(v['items']) == 1:
            it = v['items'][0]
            net = re.search(r'\[([^\]]*)\]', it['description']).group(1)
            why = open_end(net, (it['pos']['x'], it['pos']['y']), board, done)
            if why:
                allowed[why] += 1
                continue
        bad.append(f"{v['type']}: " + ' | '.join(i['description'] for i in v['items']))
    for p in rep.get('schematic_parity', []):
        bad.append(f"parity {p['type']}: " + ' | '.join(i['description'] for i in p.get('items', [])))
    open_nets = collections.Counter()
    for u in rep['unconnected_items']:
        for n in {m.group(1) for i in u['items'] for m in [re.search(r'\[([^\]]*)\]', i['description'])] if m}:
            open_nets[n] += 1
    return bad, dict(unconnected=len(rep['unconnected_items']), deferred=dict(deferred), allowed=dict(allowed)), \
        open_nets


GND_WHOLE_FROM = 'imu'     # step 5 left only the sensors' GND pads open (their rule areas); imu joins them


def complete(open_nets, nets, last, family):
    want = set(open_nets) if last else set(nets)
    if r8_route.FAMILIES.index(family) >= r8_route.FAMILIES.index(GND_WHOLE_FROM):
        want.add('GND')
    issues = [f'{n}: {open_nets[n]} unconnected item(s)' for n in sorted(want) if open_nets.get(n)]
    return issues, dict(nets=len(nets), open_elsewhere={n: c for n, c in sorted(open_nets.items()) if n not in want})


def route(board_path, board, nets, rails, done):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'route.json'
        subprocess.run([sys.executable, '-I', str(ROOT / 'tools/route_check.py'), str(board_path), '--profile', 'r8',
                        '--report', str(out)], capture_output=True)
        rep = json.loads(out.read_text())
    bad, allowed, elsewhere = [], collections.Counter(), collections.Counter()
    for f in rep['failures'] + rep['leftovers_missing']:
        mine = f['net'] in nets or f['net'] in rails
        if not mine:
            elsewhere[f['net']] += 1
            continue
        if f['net'] == 'GND' and f['cat'] in GND_POUR_LATER:
            allowed[f"GND {f['cat']} (step 7 stitching)"] += 1
            continue
        why = open_end(f['net'], (f['x'], f['y']), board, done)
        if why:
            allowed[why] += 1
            continue
        bad.append(f"{f['cat']} {f['net']} {f['layer']} ({f['x']}, {f['y']})")
    for e in rep.get('stale', []):               # an allowlist entry of a net no family has routed yet matches nothing
        if e[1] in nets:
            bad.append(f'route_check stale allowlist entry: {e[:4]}')
        else:
            allowed[f'allowlist entry {e[0]} {e[1]} (a later family routes it)'] += 1
    for key in ('nognd_audit', 'leftovers_stale', 'measured_check', 'alt_audit'):
        for e in rep.get(key, []):
            bad.append(f'route_check {key}: {e}')
    info = collections.Counter(i['cat'] for i in rep['instances'] if i['cat'] in rc.INFO and
                               (i['net'] in nets or i['net'] in rails))
    return bad, dict(failures_elsewhere=dict(elsewhere), allowed=dict(allowed), information=dict(info),
                     allowlisted=[(a['cat'], a['net']) for a in rep['allowed'] if a['net'] in nets]), rep


def _bends(tracks):
    """Direction changes at nodes where exactly two segments of one net and layer meet."""
    ends = collections.defaultdict(list)
    for t in tracks:
        a, b = (round(mm(t.GetStart().x), 3), round(mm(t.GetStart().y), 3)), \
               (round(mm(t.GetEnd().x), 3), round(mm(t.GetEnd().y), 3))
        if a == b:
            continue
        ends[(t.GetLayer(), a)].append(math.atan2(b[1] - a[1], b[0] - a[0]))
        ends[(t.GetLayer(), b)].append(math.atan2(a[1] - b[1], a[0] - b[0]))
    n = 0
    for dirs in ends.values():
        if len(dirs) == 2 and abs(abs(dirs[0] - dirs[1]) - math.pi) > 1e-3 and \
                abs(abs(dirs[0] - dirs[1]) - math.pi) < 2 * math.pi - 1e-3:
            n += 1
    return n


def record(board, nets, baseline=()):
    """Per-net and family figures of the family's own nets (rigid copper excluded from length and vias). The ratio is
    copper / octilinear MST of the pad centres, or route_check's keep-out-aware baseline where it applies (D10)."""
    keepout = {b['net']: b['keepout_mst_mm'] for b in baseline}
    rigid = {t.m_Uuid.AsString() for t in r8_power_check.rigid_items(board)}
    nc = rc.collect(board, set(nets))
    per = {}
    for net in sorted(nets):
        tr = [t for t in board.GetTracks() if t.GetNetname() == net and t.GetClass() == 'PCB_TRACK']
        vias = [t for t in board.GetTracks() if t.GetNetname() == net and t.GetClass() == 'PCB_VIA'
                and t.m_Uuid.AsString() not in rigid]
        length = sum(mm(t.GetLength()) for t in tr if t.m_Uuid.AsString() not in rigid)
        r = rc.net_route(nc[net]) if net in nc else None
        mst = keepout.get(net, r['mst']) if r else None
        ratio = round(r['len'] / mst, 3) if r and mst else None
        excess = round(r['len'] - mst, 2) if r and mst else None
        per[net] = dict(len_mm=round(length, 2), vias=len(vias), bends=_bends(tr), ratio=ratio, excess_mm=excess,
                        mst_mm=round(r['mst'], 2) if r else None, critical=rc.net_class(net) in CRITICAL_CLASSES,
                        signal=rc.net_class(net) not in ('power',))
    fam = dict(signal_track_mm=round(sum(v['len_mm'] for v in per.values() if v['signal']), 1),
               signal_vias=sum(v['vias'] for v in per.values() if v['signal']),
               critical_layer_changes=sum(v['vias'] for v in per.values() if v['critical']),
               bends=sum(v['bends'] for v in per.values() if v['signal']),
               # the detour-relevant ratio: route_check's test needs both > 1.6 x and > 2 mm (DETOUR_SLACK) longer, so a
               # short net's ratio alone means nothing; nets within the slack count as 1.0
               worst_ratio=max((v['ratio'] if (v['excess_mm'] or 0) > rc.DETOUR_SLACK else min(v['ratio'], 1.0)
                                for v in per.values() if v['ratio']), default=None))
    return fam, per


def budget(fam_mod, fig):
    b = fam_mod.BUDGET
    issues = []
    for key, got in (('length_mm', fig['signal_track_mm']), ('vias', fig['signal_vias']),
                     ('critical_layer_changes', fig['critical_layer_changes']), ('ratio', fig['worst_ratio'])):
        if key in b and got is not None and got > b[key] + 1e-9:
            issues.append(f'{key} {got} over the family budget {b[key]}')
    return issues


def contract(board, path, done):
    rep = check_r8.check_board(board, path.parent, str(path))
    bad, later = [], collections.Counter()
    for i in rep['issues']:
        for pat, owner, fam in LATER:
            if re.search(pat, i) and (fam is None or fam not in done):
                later[owner] += 1
                break
        else:
            bad.append(i)
    return bad, dict(later=dict(later))


def actuators(path):
    out = subprocess.run(['python3', str(ROOT / 'm3_design/check_actuators.py'), str(path)],
                         capture_output=True, text=True)
    return ([] if out.returncode == 0 else [f'check_actuators: {(out.stdout + out.stderr).strip()[-400:]}']), \
        dict(ok=out.returncode == 0)


L10_PYRO_VIA = 1.0
# (via net, position): {bottom part: measured courtyard-to-via gap, mm}. D61: spike (a)'s dives (D33) on the MCU side of
# the 4.7 k sense resistors; R170 / R168 are those resistors, R172 / C15 the RAS divider and VDD bypass beside the dive
# (R172 0.685 since fix pass 3 moved it 0.05 mm east, D106; 0.635 before)
L10_EXCEPT = {('ARM1_SENSE_MCU', (29.3, 47.5)): {'R170': 0.635, 'R172': 0.685, 'C15': 0.835},
              ('PYRO1_CONT_MCU', (24.0, 53.7)): {'R168': 0.235}}


def l10(board):
    issues, allowed = [], {}
    for v in board.GetTracks():
        if v.GetClass() != 'PCB_VIA' or not re.match(r'^(PYRO|ARM1)', v.GetNetname()):
            continue
        p, r = v.GetPosition(), pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu)) / 2
        key = (v.GetNetname(), (round(pcbnew.ToMM(p.x), 3), round(pcbnew.ToMM(p.y), 3)))
        for f in board.GetFootprints():
            cy = f.GetCourtyard(pcbnew.B_CrtYd)
            if not f.IsFlipped() or f.GetReference() == 'TP122' or not cy.OutlineCount():
                continue
            o = cy.Outline(0)
            gap = (0.0 if o.PointInside(p) else math.sqrt(o.SquaredDistance(p)) / 1e6) - r
            if gap >= L10_PYRO_VIA:
                continue
            ok = L10_EXCEPT.get(key, {}).get(f.GetReference())
            if ok is not None and gap >= ok - 0.005:
                allowed[f'{key[0]} {key[1]} - {f.GetReference()}'] = round(gap, 3)
            else:
                issues.append(f'{f.GetReference()} bottom courtyard {gap:.3f} mm from the pyro via {key[0]} {key[1]} '
                              f'(L10: {L10_PYRO_VIA} mm)')
    return issues, dict(allowed=allowed)


def stale(rows, nets):
    """Reservation rows of nets the done families route: the table was not regenerated (make_keepclear --routed)."""
    return [f'stale reservations of {n} (a done family routes it): regenerate r8_keepclear.tsv '
            '(make_keepclear.py ... BUILT_BOARD --routed)' for n in sorted({r['net'] for r in rows if r['net'] in nets})]


def reserved(path, nets):
    issues, ev = r8_place_check.reserved(path)
    return issues + stale(r8_power_check.keepclear_rows(), nets), ev


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('family', choices=r8_route.FAMILIES)
    ap.add_argument('board', nargs='?', type=Path, default=BOARD)
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    path = args.board.resolve()
    board = pcbnew.LoadBoard(str(path))
    done = done_families(args.family)
    last = args.family == r8_route.FAMILIES[-1]
    fam_mod = r8_route.load_family(args.family)
    nets = family_nets(done)
    rails = set(fam_mod.RAILS)
    report, fails = {}, {}

    def gate(name, issues, evidence):
        report[name] = dict(ok=not issues, issues=issues, evidence=evidence)
        fails[name] = len(issues)
    issues, ev = check_r8.rigid(board)
    gate('rigid', issues, {k: v['sha256'][:16] for k, v in ev.items()})
    issues, ev, open_nets = drc(path, board, done, last)
    gate('drc', issues, ev)
    issues, ev = complete(open_nets, nets, last, args.family)
    gate('complete', issues, ev)
    issues, ev, rrep = route(path, board, nets, rails, done)
    gate('route', issues, ev)
    fig, per = record(board, set(fam_mod.NETS), rrep['detour_baseline'])
    gate('budget', budget(fam_mod, fig), dict(family=fig, budget=fam_mod.BUDGET, nets=per))
    issues, ev = check_r8.inner_power_pyro(board)
    found, ev2 = check_r8.gate_servo(board, check_r8.close_layer_pairs(str(path)))
    gate('pyro', issues + found, dict(inner_power_pyro=ev, gate_servo=ev2))
    issues, ev = r8_power_check.inner(board, r8_power_check.rigid_items(board))
    gate('inner', issues, ev)
    issues, ev = r8_power_check.in2(board, [])
    gate('in2', issues, ev)
    issues, ev = contract(board, path, done)
    found, ev2 = actuators(path)
    gate('contract', issues + found, dict(check_r8=ev, check_actuators=ev2))
    issues, ev = l10(board)
    gate('l10', issues, ev)
    issues, ev = reserved(path, nets)
    gate('reserved', issues, ev)
    totals = collections.Counter()
    for f in done:
        m = r8_route.load_family(f)
        tf, _ = record(board, set(m.NETS), rrep['detour_baseline'])
        for k in TARGETS:
            totals[k] += tf[k]
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name   # no local absolute paths (AGENTS.md)
    report.update(family=args.family, done=list(done), board=str(shown),
                  board_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  totals_so_far=dict(totals), targets=TARGETS)
    for name, n in fails.items():
        print(f'{name:10s} {"OK" if not n else f"FAIL ({n})"}')
        for i in report[name]['issues'][:25]:
            print('    ', i)
    print('family', args.family, fig)
    print('totals so far', dict(totals), 'targets', TARGETS)
    ok = not any(fails.values())
    print(f'R8 route gate ({args.family}):', 'OK' if ok else 'FAIL')
    if args.report:
        args.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
