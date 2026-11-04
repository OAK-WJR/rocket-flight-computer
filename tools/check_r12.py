#!/usr/bin/env python3
"""R12 native-CAD contract skeleton (M3-ASSY-R12, r12_plan.md section 4): the rules the low-cost, one-sided, four-layer
board must meet, keyed by net, reference and pad number. Stage A wrote it before any R12 board exists; the R10 / R11
safety rules (check_r10 S-1 ... S-9 and the K-rules) are ported in stages B-D and are listed as PENDING until then, so
the 'full' stage cannot pass on an R12 board before they are.

usage: <KiCad python3> -I tools/check_r12.py [board.kicad_pcb] [--report out.json] [--fit FIT.json]
       [--stage placement|copper|full] [--only L-1,F-1]
exit 0 = every selected rule holds

Rules:
  L-1  four copper layers (D-R12-03), 1.6 mm board
  M-1  outline one rectangle from (0, 0), 46 mm wide, at most R12_MAX_LENGTH (100 mm, the JLC 4-layer price step,
       cost_study.md section 2.1)
  F-1  one assembled side (D-R12-01): no footprint flipped; no SMD pad on a B.* layer; the JLC Economic PCBA tier
  N-1  the board's parts equal the R12 schematic (m3_design/r12/schematic.net.xml): references, footprints, LCSC /
       Manufacturer / Manufacturer Part; title-block revision M3-ASSY-R12
  V-1  every via a 0.3 mm drill / >= 0.45 mm through via (D-R12-03: no small-hole surcharge, no blind or micro via)
  V-2  no via in or touching a soldered SMD pad (no VIPPO on R12: U401 and its GAP-3 vias are deleted, D-R12-07)
  K-rules  m3.kicad_dru is r12_sch.dru()'s text; the project floors are r12_sch.R12_FLOOR
  M-5  fit_check --profile r12 clean and bound to this board (when --fit is given)
  PENDING (stage B-D ports, each fails 'full' until implemented): S-1 ... S-9, W-1, W-2, LC-1, M-3, M-6, M-7, M-8,
       K-legends, K-copper, K-inner, K-reference, K-region, K-plane, K-fill
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
REVISION = 'M3-ASSY-R12'
R12_DIR = ROOT / 'm3_design/r12'
R12_MAX_LENGTH = 100.0
WIDTH = 46.0
VIA_DRILL, VIA_DIAMETER = 0.3, 0.45
PENDING = ('S-1', 'S-2', 'S-3', 'S-4', 'S-5', 'S-6', 'S-7', 'S-8', 'S-9', 'W-1', 'W-2', 'LC-1', 'M-3', 'M-6', 'M-7',
           'M-8', 'K-legends', 'K-copper', 'K-inner', 'K-reference', 'K-region', 'K-plane', 'K-fill')
STAGES = {'placement': ('L-1', 'M-1', 'F-1', 'N-1', 'K-rules', 'M-5'),
          'copper': ('L-1', 'M-1', 'F-1', 'N-1', 'K-rules', 'M-5', 'V-1', 'V-2')}
STAGES['full'] = STAGES['copper'] + PENDING
TITLES = {'L-1': 'four copper layers, 1.6 mm', 'M-1': f'outline 46 x <= {R12_MAX_LENGTH:g} mm from (0, 0)',
          'F-1': 'one assembled side (no flipped footprint, no bottom SMD pad)', 'N-1': 'parts equal the R12 schematic',
          'V-1': 'through vias 0.3 / >= 0.45 mm only', 'V-2': 'no via in a soldered SMD pad',
          'K-rules': 'DRU and project floors are the generator\'s', 'M-5': 'fit_check --profile r12 clean, bound'}


def mm(v):
    import pcbnew
    return pcbnew.ToMM(v)


def l1(ctx):
    import pcbnew
    b = ctx['board']
    out = []
    if b.GetCopperLayerCount() != 4:
        out.append(f'{b.GetCopperLayerCount()} copper layers; R12 is a four-layer board (D-R12-03)')
    if abs(mm(b.GetDesignSettings().GetBoardThickness()) - 1.6) > 0.01:
        out.append('board thickness is not 1.6 mm')
    return out


def outline(board):
    import pcbnew
    xs, ys, other = [], [], []
    for d in board.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        if d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            continue
        if d.GetShape() == pcbnew.SHAPE_T_RECT:
            for p in (d.GetStart(), d.GetEnd()):
                xs.append(mm(p.x))
                ys.append(mm(p.y))
        elif d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            for p in (d.GetStart(), d.GetEnd()):
                xs.append(mm(p.x))
                ys.append(mm(p.y))
        else:
            other.append(d.GetShapeStr())
    return xs, ys, other


def m1(ctx):
    xs, ys, other = outline(ctx['board'])
    out = [f'Edge.Cuts shape {s} (one rectangle expected)' for s in other]
    if not xs:
        return out + ['no Edge.Cuts outline']
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    if abs(x0) > 1e-3 or abs(y0) > 1e-3:
        out.append(f'outline starts at ({x0:g}, {y0:g}), not (0, 0)')
    if abs(x1 - x0 - WIDTH) > 0.01:
        out.append(f'board width {x1 - x0:g} mm, must be {WIDTH:g} mm (P1)')
    if y1 - y0 > R12_MAX_LENGTH + 0.01:
        out.append(f'board length {y1 - y0:g} mm exceeds {R12_MAX_LENGTH:g} mm (the JLC 4-layer price step)')
    return out


def f1(ctx):
    import pcbnew
    out = []
    for f in ctx['board'].GetFootprints():
        if f.IsFlipped():
            out.append(f'{f.GetReference()} is on the bottom side (R12 assembles one side, D-R12-01)')
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l) for l in (pcbnew.B_Cu, pcbnew.B_Paste)):
                out.append(f'{f.GetReference()}.{p.GetNumber() or "(unnumbered)"}: SMD pad on the bottom side')
    return out


def n1(ctx):
    import r12_sch
    board, out = ctx['board'], []
    if board.GetTitleBlock().GetRevision() != REVISION:
        out.append(f'title-block revision {board.GetTitleBlock().GetRevision()!r}, expected {REVISION}')
    parts, _ = r12_sch.read_netlist(ctx['netlist'])
    fps = {f.GetReference(): f for f in board.GetFootprints() if not f.GetReference().startswith(('H', 'TH', 'FID'))}
    for ref in sorted(set(parts) - set(fps)):
        out.append(f'{ref}: in the schematic, not on the board')
    for ref in sorted(set(fps) - set(parts)):
        out.append(f'{ref}: on the board, not in the schematic')
    for ref in sorted(set(parts) & set(fps)):
        f, p = fps[ref], parts[ref]
        if str(f.GetFPID().GetLibItemName()) != p['footprint'].split(':')[1]:
            out.append(f'{ref}: footprint {f.GetFPID().GetLibItemName()}, schematic {p["footprint"]}')
        for key in ('LCSC', 'Manufacturer', 'Manufacturer Part'):
            got = f.GetField(key).GetText() if f.HasField(key) else ''
            if got != p['fields'].get(key, ''):
                out.append(f'{ref}: {key} {got!r}, schematic {p["fields"].get(key, "")!r}')
    return out


def v1(ctx):
    import pcbnew
    out = []
    for t in ctx['board'].GetTracks():
        if t.GetClass() != 'PCB_VIA':
            continue
        xy = f'({mm(t.GetPosition().x):g}, {mm(t.GetPosition().y):g})'
        if t.GetViaType() != pcbnew.VIATYPE_THROUGH:
            out.append(f'via at {xy}: not a through via')
        if abs(mm(t.GetDrillValue()) - VIA_DRILL) > 1e-4:
            out.append(f'via at {xy}: drill {mm(t.GetDrillValue()):g} mm, R12 uses {VIA_DRILL:g} mm only')
        if mm(t.GetWidth(pcbnew.F_Cu)) < VIA_DIAMETER - 1e-4:
            out.append(f'via at {xy}: diameter {mm(t.GetWidth(pcbnew.F_Cu)):g} mm < {VIA_DIAMETER:g} mm')
    return out


def v2(ctx):
    import pcbnew
    out = []
    pads = [(f.GetReference(), p) for f in ctx['board'].GetFootprints() for p in f.Pads()
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.IsOnLayer(pcbnew.F_Cu)]
    for t in ctx['board'].GetTracks():
        if t.GetClass() != 'PCB_VIA':
            continue
        r = t.GetDrillValue() // 2
        for ref, p in pads:
            shape = p.GetEffectivePolygon(pcbnew.F_Cu)
            if shape.Collide(t.GetPosition(), r):
                out.append(f'via at ({mm(t.GetPosition().x):g}, {mm(t.GetPosition().y):g}) in {ref}.{p.GetNumber()}')
    return out


def k_rules(ctx):
    import r12_sch
    out = []
    dru = ctx['path'].with_suffix('.kicad_dru')
    want = r12_sch.dru((r12_sch.INPUT / 'm3.kicad_dru').read_text())
    if not dru.exists() or dru.read_text() != want:
        out.append('m3.kicad_dru differs from r12_sch.dru() (regenerate with m3_design/r12_sch.py)')
    pro = ctx['path'].with_suffix('.kicad_pro')
    if pro.exists():
        rules = json.loads(pro.read_text())['board']['design_settings']['rules']
        floor = r12_sch.R12_FLOOR
        for key, value in (('min_clearance', floor['clearance']), ('min_track_width', floor['track_width']),
                           ('min_via_diameter', floor['via_diameter']), ('min_through_hole_diameter', floor['via_hole'])):
            if abs(rules.get(key, -1) - value) > 1e-9:
                out.append(f'project {key} {rules.get(key)!r}, R12 floor {value}')
    else:
        out.append('m3.kicad_pro missing')
    return out


def m5(ctx):
    fit = ctx.get('fit')
    if fit is None:
        return []
    out = []
    if fit.get('profile') != 'r12':
        out.append(f'fit report profile {fit.get("profile")!r}, expected r12')
    if fit.get('board_sha256') != ctx['sha']:
        out.append('fit report not bound to this board')
    out += [f'fit: {i}' for i in fit.get('issues', [])]
    return out


RULES = {'L-1': l1, 'M-1': m1, 'F-1': f1, 'N-1': n1, 'V-1': v1, 'V-2': v2, 'K-rules': k_rules, 'M-5': m5}


def selected_rules(only=None, stage='full'):
    names = list(STAGES[stage])
    if only:
        unknown = set(only) - set(STAGES['full'])
        if unknown:
            raise ValueError(f'unknown rule ids {sorted(unknown)}')
        names = [n for n in names if n in only]
    return names


def check_board(board, path, fit=None, only=None, stage='full', sha=None, netlist=None):
    ctx = dict(board=board, path=Path(path), fit=fit, sha=sha, netlist=netlist or R12_DIR / 'schematic.net.xml')
    rules, issues = {}, []
    for rid in selected_rules(only, stage):
        if rid in PENDING:
            found = [f'{rid}: not ported to R12 yet (r12_plan.md stages B-D)']
            title = 'pending port'
        else:
            found = RULES[rid](ctx)
            title = TITLES[rid]
        rules[rid] = dict(title=title, ok=not found, issues=found)
        issues += [f'{rid}: {i}' for i in found] if rid not in PENDING else found
    return dict(rules=rules, issues=issues, failing=[r for r, v in rules.items() if not v['ok']], ok=not issues,
                stage=stage)


def file_sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board', nargs='?', type=Path, default=R12_DIR / 'm3.kicad_pcb')
    ap.add_argument('--report', type=Path)
    ap.add_argument('--fit', type=Path)
    ap.add_argument('--only')
    ap.add_argument('--stage', choices=tuple(STAGES), default='full')
    a = ap.parse_args()
    only = {r.strip() for r in a.only.split(',')} if a.only else None
    try:
        selected_rules(only, a.stage)
    except ValueError as error:
        ap.error(str(error))
    import pcbnew
    bp = a.board.resolve()
    sha = file_sha(bp)
    fit = json.loads(a.fit.read_text()) if a.fit else None
    board = pcbnew.LoadBoard(str(bp))
    report = check_board(board, bp, fit=fit, only=only, stage=a.stage, sha=sha)
    if file_sha(bp) != sha:
        report['issues'].append('board changed during check')
        report['ok'] = False
    report.update(board_sha256=sha, checker_sha256=file_sha(__file__))
    for rid, r in report['rules'].items():
        print(f"{rid:10s} {'OK  ' if r['ok'] else 'FAIL'} {r['title']}" + (f" ({len(r['issues'])})" if r['issues'] else ''))
    for i in report['issues']:
        print('FAIL', i)
    print(f'R12 CAD contract ({a.stage}):', 'OK' if report['ok'] else f"FAIL ({len(report['issues'])} findings)")
    if a.report:
        a.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
