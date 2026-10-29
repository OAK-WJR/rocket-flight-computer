#!/usr/bin/env python3
"""R9 build step 9 gate: the finished board after r9_post.py (r9_plan.md section 4 step 9; R9_DECISIONS D-S9-*).

usage: <KiCad python3> -I m3_design/r9_post_check.py [board] [--report OUT.json] [--numpy-py PYTHON3-WITH-NUMPY]
                                                    [--dc-dir DIR]
       exit 0 = every gate passes

tools/check.sh (the full gate) runs after it in r9_build.sh and holds DRC (every severity, silkscreen included, with
parity), ERC, the silkscreen outline check, fit, the plate model, the seeded rule-H suite, check_r9, route_check r9 and
check_actuators. This gate adds what check.sh does not hold on the finished board (functions of the earlier gates are
called, never restated or weakened):
  legends    every legend r9_post.py must draw is on the board exactly once (the SMA jack, part, pin-table, note,
             terminal-pin, J122 plug, revision and order-number legends), check_r9 K-legends (ids, the J9 / J2 pin
             tables, GNSS / RADIO, legends within 6 mm of their parts, terminal legends nearest their own pins),
             check_actuators 11's ARM / IGN texts, the title-block revision, every visible designator >= 1.0 mm high
             and >= 0.15 mm stroke (REQUIREMENTS M2), every board legend >= 1.0 mm / 0.15 mm
  dc         the final copper's 7.7 A paths at 0.1 mm (r9_power_check.gate_dc: R8_DECISIONS D12's limits, every rise
             <= R8's, D_raw <= 1.0 mOhm, no via barrel over 1.0 A): steps 7 and 8 drew copper after step 6's DC gate,
             and R8's build held D12 on its final copper (R8_DECISIONS D95), so R9's does too (D-S9-04)
  supply     the supply paths on the final copper (r9_power_check.gate_supply: no via barrel over 1.0 A)
  f9         F9's hot-plug premise with the final copper's R_b (r9_power_check.gate_f9, R8's model)
"""
import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r9 as C9  # noqa: E402
import r9_post as POST  # noqa: E402
import r9_power_check as PWC  # noqa: E402

mm = pcbnew.ToMM
BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
TEXT_MIN, STROKE_MIN = 1.0, 0.15                    # mm, REQUIREMENTS M2


def required_legends(b):
    """The board legends r9_post.py draws, as a multiset of texts (pin legends such as 2:GND repeat by design)."""
    want = ['GNSS', 'RADIO', 'TP30 SAFEBOOT', POST.J122_TABLE, POST.REV, POST.ORDER_MARK]
    want += [word for _, word in POST.WORDS]
    for ref, (_, names) in POST.PORTS.items():
        for start in range(0, len(names), 2):
            want.append(ref + ' ' + ' '.join(f'{i + 1}:{names[i]}' for i in range(start, min(start + 2, len(names)))))
    want += [note for _, note in POST.NOTES]
    want += [f'{n}:{name}' for ref, pins in POST.TERMINAL_PINS if b.FindFootprintByReference(ref) for n, name in pins]
    want += [plug for plug, _ in POST.PLUG_ROWS]
    return collections.Counter(want)


def gate_legends(b, path):
    issues, ev = [], {}
    texts = [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and
             d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
    have = collections.Counter(d.GetText().strip() for d in texts)
    want = required_legends(b)
    for text, n in sorted(want.items()):
        if have[text] != n:
            issues.append(f'legends: {text!r} drawn {have[text]} time(s), expected {n}')
    for text in sorted(set(have) - set(want)):
        issues.append(f'legends: unexpected board silkscreen text {text!r} (AGENTS.md: designators and the listed '
                      f'legends only)')
    for d in texts:
        if mm(d.GetTextHeight()) < TEXT_MIN - 1e-6 or mm(d.GetTextThickness()) < STROKE_MIN - 1e-6:
            issues.append(f'legends: {d.GetText()!r} {mm(d.GetTextHeight())} mm / {mm(d.GetTextThickness())} mm')
    shown = [f for f in b.GetFootprints() if f.Reference().IsVisible()]
    for f in shown:
        t = f.Reference()
        if t.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            issues.append(f'legends: {f.GetReference()} designator visible on {t.GetLayerName()}')
        if mm(t.GetTextHeight()) < TEXT_MIN - 1e-6 or mm(t.GetTextThickness()) < STROKE_MIN - 1e-6:
            issues.append(f'legends: {f.GetReference()} designator {mm(t.GetTextHeight())} mm / '
                          f'{mm(t.GetTextThickness())} mm')
    for f in b.GetFootprints():
        if f.Value().IsVisible() and f.Value().GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            issues.append(f'legends: {f.GetReference()} value on the silkscreen (part numbers stay on Fab)')
    if b.GetTitleBlock().GetRevision() != POST.REV:
        issues.append(f'legends: title-block revision {b.GetTitleBlock().GetRevision()!r}, expected {POST.REV}')
    ctx = C9.Ctx(b, path.parent, path)
    found, kev = C9.k_legends(ctx)
    issues += [f'legends: K-legends: {i}' for i in found]
    text = path.read_text()
    for word in ('ARM', 'IGN'):                   # check_actuators 11 (also in check.sh; named here for the record)
        if not re.search(rf'\(gr_text "{word}"', text):
            issues.append(f'legends: no {word} text (check_actuators 11, REQUIREMENTS F8)')
    hidden = sorted(f.GetReference() for f in b.GetFootprints() if not f.Reference().IsVisible())
    ev.update(board_texts=len(texts), designators_shown=len(shown), designators_hidden=len(hidden),
              hidden=hidden, terminal_legends=kev.get('terminal_legends'))
    return issues, ev


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', nargs='?', type=Path, default=BOARD)
    ap.add_argument('--report', type=Path)
    ap.add_argument('--numpy-py', default='python3', help='a python3 with numpy (the hot-plug model, f9)')
    ap.add_argument('--dc-dir', type=Path, help='keep the DC solves here')
    args = ap.parse_args()
    path = args.board.resolve()
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    board = pcbnew.LoadBoard(str(path))
    report, fails = {}, {}

    def gate(name, result):
        issues, ev = result
        report[name] = dict(ok=not issues, issues=issues, evidence=ev)
        fails[name] = len(issues)
    gate('legends', gate_legends(board, path))
    gate('dc', PWC.gate_dc(path, args.dc_dir))
    gate('supply', PWC.gate_supply(path, args.dc_dir))
    gate('f9', PWC.gate_f9(report['supply']['evidence'].get('paths', {}).get('bat_u9', {}).get('mohm'), args.numpy_py))
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name
    report.update(board=str(shown), board_sha256=sha,
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  builder_sha256=hashlib.sha256((ROOT / 'm3_design/r9_post.py').read_bytes()).hexdigest())
    for name, n in fails.items():
        print(f'{name:10s} {"OK" if not n else f"FAIL ({n})"}')
        for i in report[name]['issues'][:25]:
            print('    ', i)
    lg = report['legends']['evidence']
    print(f"legends: {lg.get('board_texts')} board texts; {lg.get('designators_shown')} designators shown, "
          f"{lg.get('designators_hidden')} hidden (kept on Fab)")
    dc = report['dc']['evidence'].get('rows') or {}
    print('dc', {k: (v or {}).get('mohm') for k, v in dc.items()}, 'mOhm;',
          {k: (v or {}).get('rise_c') for k, v in dc.items()}, 'C;',
          'via max', max([(v or {}).get('via_max_a') or 0 for v in dc.values()] or [0]), 'A')
    sp = report['supply']['evidence'].get('paths', {})
    print('supply', {k: v.get('mohm') for k, v in sp.items()}, 'mOhm')
    f9 = report['f9']['evidence']
    print('f9', f9.get('rb_mohm'), 'mOhm,', f9.get('feed_estimate_nH'), 'nH')
    ok = not any(fails.values())
    print('R9 post gate:', 'OK' if ok else 'FAIL')
    if args.report:
        args.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
