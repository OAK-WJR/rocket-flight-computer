#!/usr/bin/env python3
"""R10 silkscreen, assembly references and the final zone fill (M3-ASSY-R10; R10_DECISIONS D-R2-16): the post stage,
after r10_route.py's ground family. No copper, zone outline, pad or footprint position edit (asserted by R8's digest of
every copper item, zone and pad before and after; the zone fill is redone last and must reproduce the fill it found).

usage: <KiCad python3> -I m3_design/r10_post.py [--board m3_design/assembly_review/m3.kicad_pcb] [--report out.json]

R9's post stage (m3_design/r9_post.py, whose placement helpers are imported, not copied) on R10's geometry. Every board-
level silkscreen item is deleted and every footprint field hidden, then, in this order:
  1. J122's plug numbers 1-4 (west to east, the _MIR numbering) in one row across the plugs (r9_post.put_plug_row);
     then the legends about one part, each at the free spot nearest that part's courtyard within LEGEND_REACH (6 mm,
     AGENTS.md; check_r7.legend_subjects gates it): the connector words (check_r10.WORD_LEGENDS_R10: ARM, IGN, BAT, CAM,
     SWD, SERVO, PULL, GPS, RADIO; and SWITCH for J400), top face first (the black terminals J124 / J121 are told apart
     by ARM / IGN: REQUIREMENTS F8, check_actuators); the pin tables of J9 and J2 (check_r7.pin_legends); J122's row
     table and its harness note (O3 / O6: the middle (+) row has no connection, servo power comes from the harness);
     the ARM-plug and fuse notes of J124 and J1 (R8's wording);
  2. the terminal pin legends (check_r10.TERMINAL_PINS_R10: J124 1:BUS1 2:RAW, J121 1:E1- 2:E1+, J1 1:BAT+ 2:GND,
     J400 1:SW 2:SW, J123 1:PULL 2:GND), each at the free spot nearest its own pin whose text box has that pin as its
     nearest connector pin by OWN_MARGIN (r9_post.put_pin), top face first;
  3. the revision legend M3-ASSY-R10 and JLC's order-number placeholder JLCJLCJLCJLC (ORDERING), both required;
  4. pin-1 dots beside pad 1 of DOT_PARTS (r9_post.pin1_dots' mark and search), then every designator by the R4 rule
     (r5_post.designators: >= 1.0 mm text, never over a pad, via or hole or off the board, nearer its own part than any
     other; a crowded one goes on the bottom under its part; one with no such spot is hidden and kept on the Fab
     layer), then R8's courtyard and run-on tests (r8_post); one that fails is placed again or hidden;
  5. Fab-layer designators (r5_post.fab_refs, r9_post.fab_clear) and the title-block revision;
  6. the zone fill: every zone is filled before step 1 (the routing families save them unfilled) and again last,
     after the silkscreen; the two fills must agree (R8's digest covers the fill).
Any essential legend that does not fit, a terminal legend whose nearest pin is not its own, or a legend beyond
LEGEND_REACH fails the run (check_r7.pin_legends / legend_subjects with R10's words, check_r8.terminal_legends with R10's
pins, duplicate ids). Runs once, on the ground-stage board (refuses a board that already carries the J9 / J2 pin
tables). Deterministic (fixed KIID seed, no random search): a rebuild reproduces the board byte for byte.
"""
import argparse
import json
from pathlib import Path
import sys

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r7  # noqa: E402
import check_r8  # noqa: E402
import check_r10  # noqa: E402
import r5_post as silk  # noqa: E402
import r7_post  # noqa: E402
import r8_post  # noqa: E402
import r9_post  # noqa: E402  (put_pin, put_plug_row, pin1_dots, fab_clear, outline, connector_pads)

REV = 'M3-ASSY-R10'
KIID_SEED = 10120               # r10_pcb 10103, r10_route families 10110-10118
LEGEND_REACH = r7_post.LEGEND_REACH
REACH_MARGIN = 0.1             # mm: label_near's box gap against legend_subjects' polygon ink (rounding)
PORTS = r7_post.PORTS           # J9 CAM 5V GND TX RX (camera-side UART names), J2 SWD 3V3 SWDIO NRST SWCLK GND NC
WORDS = tuple((ref, word) for word, ref in check_r10.WORD_LEGENDS_R10.items()) + (('J400', 'SWITCH'),)
NOTES = r8_post.NOTES + (('J122', 'J122 1:S 2:NC 3:GND'), ('J122', 'SERVO + FROM HARNESS'))
TERMINAL_PINS = check_r10.TERMINAL_PINS_R10
ORDER_MARK = r8_post.ORDER_MARK
PIN_REACH = r9_post.PIN_REACH
# pin-1 dots: R10's ICs whose footprints carry no pin-1 mark (R9's list less the removed U7 / U8, plus the port supply
# and port switch / translator-supply parts of O5)
# (R9's four are required; a new part with no free spot within DOT_REACH of its pad 1 is listed in the evidence and
# relies on its Fab-layer pin-1 mark for the assembly drawing)
DOT_PARTS = ('U9', 'U10', 'U11', 'U13', 'U400', 'U401', 'U402', 'U410', 'U412', 'U420', 'U422')
DOT_REQUIRED = ('U9', 'U10', 'U11', 'U13')


def finish(b):
    """Place every legend, the designators and the Fab references; return the placement evidence."""
    silk.W, silk.L = r9_post.outline(b)
    for d in list(b.GetDrawings()):
        if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            b.Delete(d)
    for f in b.GetFootprints():
        for field in f.GetFields():
            field.SetVisible(False)
    for ref, w in r7_post.SILK_W.items():           # silkscreen strokes at the library width (lib_footprint_mismatch)
        f = b.FindFootprintByReference(ref)
        for g in (f.GraphicalItems() if f else ()):
            if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) and g.GetClass() == 'PCB_SHAPE':
                g.SetWidth(silk.MM(w))
    silks = {side: r8_post.RunOnSilk(b, side) for side in ('F', 'B')}
    pads = r9_post.connector_pads(b)
    placed, missing = {}, []

    def clip(x0, y0, x1, y1):
        return (max(0.4, x0), max(0.4, y0), min(silk.W - 0.4, x1), min(silk.L - 0.4, y1))

    def put_near(text, ref, sides=('B', 'F')):
        result = r7_post.label_near(b, silks, text, ref, reach=LEGEND_REACH - REACH_MARGIN, sides=sides)
        placed[text] = None if result is None else list(result)
        if result is None:
            missing.append(f'{text} (within {LEGEND_REACH} mm of {ref})')
        return result

    # 1. J122's plug numbers, then the legends about one part
    with check_r10.patched(r9_post, PLUG_ROWS=r9_post.PLUG_ROWS):
        row = r9_post.put_plug_row(b, silks, pads)
    for plug, _ in r9_post.PLUG_ROWS:
        placed[f'J122 plug {plug}'] = None if row is None else list(row[plug])
    if row is None:
        missing.append('J122 plug numbers 1-4 (one row)')
    for ref, word in WORDS:
        put_near(word, ref, sides=('F', 'B'))
    for ref, (_, names) in PORTS.items():
        for start in range(0, len(names), 2):
            text = ref + ' ' + ' '.join(f'{i + 1}:{names[i]}' for i in range(start, min(start + 2, len(names))))
            put_near(text, ref)
    for ref, note in NOTES:
        put_near(note, ref)
    # 2. terminal pin legends by pin
    for ref, mapping in TERMINAL_PINS:
        for number, name in mapping:
            x, y = silk.pad(b, ref, number)
            regions = [(clip(x - PIN_REACH, y - PIN_REACH, x + PIN_REACH, y + PIN_REACH), ('F', 'B'), (90, 0))]
            result = r9_post.put_pin(b, silks, f'{number}:{name}', pads, {(ref, number)}, (x, y), regions)
            key = f'{ref} {number}:{name}'
            placed[key] = None if result is None else list(result)
            if result is None:
                missing.append(key)
    # 3. revision legend and JLC's order-number placeholder
    whole = (0.4, 0.4, silk.W - 0.4, silk.L - 0.4)
    for text, near in ((REV, (silk.W / 2, silk.L - 6.0)), (ORDER_MARK, (silk.W / 2, silk.L / 2))):
        result = silk.label(b, silks, text, near, whole, (0, 90), ('B', 'F'), size=1.0)
        placed[text] = None if result is None else list(result)
        if result is None:
            missing.append(text)
    if missing:
        raise RuntimeError('Essential R10 silkscreen did not fit: ' + ', '.join(missing))
    # 4. pin-1 dots, designators, the courtyard and run-on tests
    dots, no_dot = {}, []
    for ref in DOT_PARTS:
        if b.FindFootprintByReference(ref) is None:
            continue
        with check_r10.patched(silk, DOT_PARTS=(ref,)):
            try:
                dots.update(r9_post.pin1_dots(b, silks))
            except RuntimeError:
                if ref in DOT_REQUIRED:
                    raise
                no_dot.append(ref)
    silk.designators(b, silks)
    moved = {}
    for _ in range(4):
        bad = {ref: ('courtyard',) + why for ref, why in r7_post.courtyard_offenders(b).items()}
        bad.update({ref: ('run-on',) for ref in r8_post.run_on_offenders(b) if ref not in bad})
        if not bad:
            break
        for ref in sorted(bad):
            moved[ref] = (bad[ref], r8_post.place_designator(b, ref))
    left = r7_post.courtyard_offenders(b)
    if left:
        raise RuntimeError(f"designators still nearer another part's courtyard than their own: {left}")
    left = r8_post.run_on_offenders(b)
    if left:
        raise RuntimeError(f'designators still running into another text: {left}')
    small = [f.GetReference() for f in b.GetFootprints() if f.Reference().IsVisible() and
             silk.mm(f.Reference().GetTextHeight()) < 1.0 - 1e-6]
    if small:
        raise RuntimeError(f'designators below 1.0 mm text (REQUIREMENTS M2): {small}')
    # 5. Fab references, title block
    silk.fab_refs(b)
    fab_moved = r9_post.fab_clear(b)
    b.GetTitleBlock().SetRevision(REV)
    with check_r10.patched(check_r7, WORD_LEGENDS=check_r10.WORD_LEGENDS_R10), \
            check_r10.patched(check_r8, TERMINAL_PINS=TERMINAL_PINS):
        issues = (check_r7.duplicate_ids(b) + check_r7.pin_legends(b) + check_r7.legend_subjects(b) +
                  check_r8.terminal_legends(b)[0])
    if issues:
        raise RuntimeError('legend contract: ' + '; '.join(issues))
    hidden = sorted(silk.HIDDEN, key=lambda r: (r.rstrip('0123456789'), int(r[len(r.rstrip('0123456789')):] or 0)))
    visible = sum(1 for f in b.GetFootprints() if f.Reference().IsVisible())
    bottom_of_top = sorted(f.GetReference() for f in b.GetFootprints() if f.Reference().IsVisible() and
                           not f.IsFlipped() and f.Reference().GetLayer() == pcbnew.B_SilkS)
    for ref, (why, got) in sorted(moved.items()):
        print(f'  {why[0]}: {ref} -> '
              f'{"hidden" if got is None else f"{got[0]}.SilkS at ({got[1][0]:.2f}, {got[1][1]:.2f})"}')
    print(f'R10 silkscreen: {len(placed)} legends; {visible} designators shown ({len(bottom_of_top)} top parts\' on the '
          f'bottom under their part); {len(hidden)} hidden, kept on Fab: {" ".join(hidden)}')
    print(f'pin-1 dots: {" ".join(sorted(dots))}; no room (Fab mark only): {" ".join(no_dot) or "none"}')
    return {'revision': REV, 'outline_mm': [silk.W, silk.L], 'legends': placed, 'pin1_dots': dots, 'no_pin1_dot': no_dot,
            'fab_moved': fab_moved, 'designators_shown': visible,
            'top_designators_under_part_on_bottom': bottom_of_top, 'hidden_references': hidden,
            'replaced_designators': {r: {'why': list(w), 'after': None if g is None else [g[0], list(g[1])]}
                                     for r, (w, g) in sorted(moved.items())}}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--board', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--report', type=Path, help='write the placement evidence (JSON)')
    args = ap.parse_args()
    board = args.board.resolve()
    pcbnew.KIID.SeedGenerator(KIID_SEED)
    b = pcbnew.LoadBoard(str(board))
    if not check_r7.pin_legends(b):
        raise SystemExit('r10_post runs once, on the ground-stage board: this board already carries its pin tables')
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())          # the zone fill (the routing families leave zones unfilled)
    before = r8_post.fixed_digest(b)
    evidence = finish(b)
    assert r8_post.fixed_digest(b) == before, 'r10_post changed copper, a zone, a pad or a footprint position'
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())          # the final fill, after the silkscreen: it must reproduce the first
    assert r8_post.fixed_digest(b) == before, 'the final zone fill differs from the first'
    assert pcbnew.SaveBoard(str(board), b, True), 'save failed'
    b = pcbnew.LoadBoard(str(board))
    assert r8_post.fixed_digest(b) == before, 'the saved board differs in copper, zones, pads or footprint positions'
    print(f'r10_post: saved {board.name}; copper, zones, pads and footprint positions unchanged; zones refilled')
    if args.report:
        args.report.write_text(json.dumps(evidence, indent=1) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
