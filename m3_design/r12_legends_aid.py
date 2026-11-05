#!/usr/bin/env python3
"""R12 silkscreen drafting aid (D-R12-80): searches the legend, designator, pin-1 dot and Fab-reference placements for
the routed R12 board once, offline, and freezes them into m3_design/r12_legends.tsv. m3_design/r12_post.py only reads
that table (D-R12-26: the build never searches). Not run by m3_design/r12_build.sh.

usage: <KiCad python3> -I -B m3_design/r12_legends_aid.py BOARD [--out m3_design/r12_legends.tsv] [--save COPY]
BOARD is the routed board before the post stage (r12_route.py's output: no silkscreen text).

R11's aid (m3_design/r11_legends_aid: R10's post-stage search and R11's helpers) run on R12's data, in R12's order:
  * every contact legend first (terminals, then each SH contact), then the revision, the required designators
    (check_r10.SHOWN_REFS), the connector words, J2's rows and J122's note, pin-1 dots, the other designators and the
    Fab references (R11 placed the required designators and words before the GH contacts);
  * the contact legends are check_r12.TERMINAL_PINS (J1 / J121 terminals, every contact of the SH ports J400, J410,
    J420, J440, J9 and J122, NC contacts included: D-R12-29 ... -31), in place of check_r11.TERMINAL_PINS_R11;
  * the revision is M3-ASSY-R12 (r12_post.REV) on B.Silkscreen; supports are R12's (r12_post.supports);
  * pin-1 dots for R12's ICs (DOT_PARTS; U1's TFBGA has no pad '1', its A1 mark is in the footprint);
  * a contact legend's box is OWN_MARGIN_R12 (0.05 mm) nearer its own pin than any other (R11's aid used 0.1 mm;
    the gate's margin is 0.01 mm);
  * R12's only optional legend is J122's harness note (check_r12.OPTIONAL_NOTES, D-R12-81): absent, it is left out;
    every other item with no legal spot is an 'open' row, which r12_post refuses. The bottom face carries no parts on R12 (one-sided Economic assembly,
    D-R12-01), so the bottom silkscreen is open for designators and contact legends.
Deterministic: a fixed order and fixed grids, no random search.
"""
import argparse
import copy
from pathlib import Path
import sys

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r10  # noqa: E402
import check_r12  # noqa: E402
import r10_post as P  # noqa: E402
import r11_legends_aid as aid  # noqa: E402
import r11_post  # noqa: E402
import r12_post  # noqa: E402
import r5_post as silk  # noqa: E402
import r7_post  # noqa: E402
import r8_post  # noqa: E402
import r9_post  # noqa: E402

OWN_MARGIN_R12 = 0.05           # mm: pin legend box nearer its own pin than any other (gate 0.01; R11 aid 0.1). The SH
                                # ports' 1.0 mm pitch leaves no spot at 0.1 behind the via fan-out (D-R12-80)
SH_STAGGER = 0.2                # mm: an inward SH legend's ink starts this far past the pad centre line (> SILK_GAP)
DOT_PARTS = ('U2', 'U3', 'U4', 'U5', 'U6', 'U9', 'U400', 'U403')


def draft(b):
    """r11_legends_aid.draft in R12's order (D-R12-80); the steps and helpers are R11's."""
    silk.W, silk.L = r9_post.outline(b)
    for d in list(b.GetDrawings()):
        if d.GetLayer() in P.SILKS:
            b.Delete(d)
    for f in b.GetFootprints():
        for field in f.GetFields():
            field.SetVisible(False)
        t = f.Reference()
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.0), pcbnew.FromMM(1.0)))
        t.SetTextThickness(pcbnew.FromMM(0.15))
    silks = {side: P.Silk10(b, side) for side in ('F', 'B')}
    pads = r9_post.connector_pads(b)
    boxes = P.connector_boxes(b)
    log, missing = {}, []

    def clip(x0, y0, x1, y1):
        return (max(P.EDGE_MM, x0), max(P.EDGE_MM, y0), min(silk.W - P.EDGE_MM, x1), min(silk.L - P.EDGE_MM, y1))

    def pin(ref, number, name):
        x, y = silk.pad(b, ref, number)
        regions = [(clip(x - r9_post.PIN_REACH, y - r9_post.PIN_REACH, x + r9_post.PIN_REACH,
                         y + r9_post.PIN_REACH), ('F', 'B'), (90, 0))]
        result = r9_post.put_pin(b, silks, f'{number}:{name}', pads, {(ref, number)}, (x, y), regions)
        log[f'{ref} {number}:{name}'] = result
        if result is None:
            missing.append(('pin', f'{ref} {number}:{name}'))

    def sh_row(ref, mapping):
        """An SH port's contact legends (D-R12-80): at 1.0 mm pitch two neighbours' 1.0 mm legends cannot sit side by
        side on one face (ink 1.0 mm + SILK_GAP > pitch), so each contact's legend goes on the bottom (no parts there,
        D-R12-01) along its own column, alternately inward and outward of the pad row, then anywhere put_pin finds.
        Both alternations are tried from the same state; the one with fewer contacts left without a spot is kept
        (the first on a tie)."""
        def attempt(parity):
            fails, results = [], {}
            for k, (number, name) in enumerate(mapping):
                x, y = silk.pad(b, ref, number)
                reach = r9_post.PIN_REACH
                win = clip(x - reach, y - reach, x + reach, y + reach)
                t = silk._text(b, f'{number}:{name}', silks['B'].layer, 1.0)
                t.SetTextAngleDegrees(90)
                t.SetPosition(silk.P(0, 0))
                r0 = silk.ink(t)
                # anchor ranges whose ink lies wholly on one side: outward ink ends at the pad centre line, inward ink
                # starts SH_STAGGER past it, so alternate neighbours clear each other by the silkscreen gap
                if y < silk.L / 2:      # aft row: outward is -y
                    outward = (win[0], win[1], win[2], y - r0[3])
                    inward = (win[0], y + SH_STAGGER - r0[1], win[2], win[3])
                else:                   # forward row: outward is +y
                    outward = (win[0], y - r0[1], win[2], win[3])
                    inward = (win[0], win[1], win[2], y - SH_STAGGER - r0[3])
                first, second = (inward, outward) if k % 2 == parity else (outward, inward)
                regions = [(first, ('B',), (90,)), (second, ('B',), (90,)), (win, ('F', 'B'), (90, 0))]
                got = r9_post.put_pin(b, silks, f'{number}:{name}', pads, {(ref, number)}, (x, y), regions)
                results[f'{ref} {number}:{name}'] = got
                if got is None:
                    fails.append(('pin', f'{ref} {number}:{name}'))
            return fails, results

        def snapshot():
            return ({k: (copy.deepcopy(v.grid), list(v.texts)) for k, v in silks.items()},
                    {d.m_Uuid.AsString() for d in b.GetDrawings()})

        def restore(snap):
            state, ids = snap
            for k, (grid, texts) in state.items():
                silks[k].grid, silks[k].texts = copy.deepcopy(grid), list(texts)
            for d in list(b.GetDrawings()):
                if d.m_Uuid.AsString() not in ids:
                    b.Remove(d)

        snap = snapshot()
        tried = []
        for parity in (0, 1):
            fails, _ = attempt(parity)
            tried.append((len(fails), parity))
            log[f'{ref} alternation {parity} misses'] = [text for _, text in fails]
            restore(snap)
        parity = min(tried)[1]
        fails, results = attempt(parity)
        log.update(results)
        log[f'{ref} alternation'] = parity
        missing.extend(fails)

    # 1. every contact legend first (D-R12-80): the wire-pad / terminal / switch legends, then every SH contact, so
    #    the 1.0 mm-pitch rows get the room before the designators and words (R11 placed them after)
    for ref in aid.WIRED_FIRST:
        for number, name in dict(check_r12.TERMINAL_PINS)[ref]:
            pin(ref, number, name)
    for ref, mapping in check_r12.TERMINAL_PINS:
        if ref not in aid.WIRED_FIRST:
            sh_row(ref, mapping)
    # 1b. J122's harness note next (D-R12-80: a long legend; R11 placed it last)
    for ref, note in P.NOTES:
        result = P.put_subject(b, silks, note, ref, boxes, sides=('F', 'B'))
        if result is None:
            result = P.put_subject(b, silks, note, ref, boxes, sides=('F', 'B'), margin=0.0)
        log[note] = result
        if result is None:
            missing.append(('note', note))
    # 2. the revision, on the bottom (pinned)
    whole = (P.EDGE_MM, P.EDGE_MM, silk.W - P.EDGE_MM, silk.L - P.EDGE_MM)
    result = silk.label(b, silks, r12_post.REV, (silk.W / 2, silk.L / 2), whole, (0, 90), ('B',), size=1.0)
    log[r12_post.REV] = result
    if result is None:
        raise RuntimeError(f'no room for {r12_post.REV} on the bottom')
    # 2b. the designators K-legends requires shown (check_r10.SHOWN_REFS), before the other legends take the room
    shown = []
    with check_r10.patched(r8_post, RunOnSilk=P.Silk10):
        for ref in check_r10.SHOWN_REFS:
            got = r8_post.place_designator(b, ref)
            if got is None:                      # a larger reach for the required ones (the gate measures ownership)
                got = aid.place_near_courtyard(b, ref, aid.SHOWN_CAP, step=0.05)   # D-R11-82: Q120's 1.22 mm band
            log[f'designator {ref}'] = got
            if got is None:
                missing.append(('ref', ref))
                continue
            t = b.FindFootprintByReference(ref).Reference()
            silks['B' if t.GetLayer() == pcbnew.B_SilkS else 'F'].add(silk.ink(t))
            shown.append(ref)
    # 3. connector words
    for word, ref in check_r10.WORD_LEGENDS_R10.items():
        axis = aid.pin_axis(b, ref) if word in aid.SPAN_WORDS else None
        result = aid.put_word(b, silks, word, ref, span_axis=axis)
        if result is None:
            result = aid.put_word(b, silks, word, ref, span_axis=axis, reach=12.0)
        log[word] = result
        if result is None:
            missing.append(('word', word))
    # 4. J2's SWD rows, J122's harness note
    for text in sorted(P.port_rows('J2'), key=lambda t: (-len(t), t)):
        result = P.put_subject(b, silks, text, 'J2', boxes, sides=('F', 'B'))
        if result is None:
            result = P.put_subject(b, silks, text, 'J2', boxes, sides=('F', 'B'), margin=0.0)
        log[text] = result
        if result is None:
            missing.append(('port', text))
    if missing:
        print('NO LEGAL SPOT (recorded as open rows):', missing)
    # 4. pin-1 dots
    dots, no_dot = P.pin1_dots(b, silks, [r for r in DOT_PARTS if b.FindFootprintByReference(r) is not None])
    log['dots'] = dots
    log['no_dot'] = no_dot
    # 5. designators
    silk.designators(b, silks, priority=check_r10.SHOWN_REFS, fixed=set(shown))
    with check_r10.patched(r8_post, RunOnSilk=P.Silk10):
        for _ in range(4):
            bad = {ref: ('courtyard',) for ref in r7_post.courtyard_offenders(b)}
            bad.update({ref: ('run-on',) for ref in r8_post.run_on_offenders(b) if ref not in bad})
            if not bad:
                break
            for ref in sorted(bad, key=lambda r: (r not in check_r10.SHOWN_REFS, r)):
                r8_post.place_designator(b, ref)
    # 6. Fab references
    log['fab'] = aid.place_fab(b)
    return log, missing


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', type=Path)
    ap.add_argument('--out', type=Path, default=ROOT / 'm3_design/r12_legends.tsv')
    ap.add_argument('--save', type=Path, help='save the drafted board copy here (inspection only)')
    args = ap.parse_args()
    with check_r10.patched(P, supports=r12_post.supports), \
            check_r10.patched(r9_post, OWN_MARGIN=OWN_MARGIN_R12), \
            check_r10.patched(r11_post, REV=r12_post.REV):
        b = pcbnew.LoadBoard(str(args.board.resolve()))
        log, missing = draft(b)
    for k, v in log.items():
        if k != 'fab':
            print(k, v)
    hidden = sorted(f.GetReference() for f in b.GetFootprints() if not f.Reference().IsVisible())
    print('hidden designators', len(hidden), ' '.join(hidden))
    optional = [(kind, text) for kind, text in missing if kind == 'note' and text in check_r12.OPTIONAL_NOTES]
    missing = [m for m in missing if m not in optional]
    if optional:
        print('optional on R12 (D-R12-81), not drawn, no open row:', optional)
    if missing:
        print('OPEN (no legal spot; r12_post refuses the table):', missing)
    rows = r12_post.table_rows(b) + [('open', text, kind, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0) for kind, text in missing]
    r12_post.write_table(args.out, rows)
    print(f'wrote {len(rows)} rows to {args.out}')
    if args.save:
        pcbnew.SaveBoard(str(args.save), b, True)
    return 1 if missing else 0


if __name__ == '__main__':
    raise SystemExit(main())
