#!/usr/bin/env python3
"""R6 silkscreen and assembly reference finishing; no copper or geometry edits.

Call finish(board) after routing. Standalone use requires an explicit output path.
Essential connector legends must fit, otherwise the caller gets an exception.
"""
import argparse
from pathlib import Path

import pcbnew
import r5_post as silk

REV = 'M3-ASSY-R6'
PORTS = {
    'J9': ('CAM', ('5V', 'GND', 'TX', 'RX')),
    'J130': ('RADIO', ('M0', 'M1', 'RX', 'TX', 'AUX', '5V', 'GND')),
    'J131': ('GPS', ('5V', 'GND', 'TX', 'RX')),
    'J2': ('SWD', ('3V3', 'SWDIO', 'NRST', 'SWCLK', 'GND', 'NC')),
}


def finish(b):
    """Place all required legends, optional refdes and all assembly references.

    Pin tables name their connector and use physical pin numbers. RX/TX names on
    the camera/radio/GPS tables are peripheral-side names. Crowded pin tables may
    be on the bottom; short connector names stay in their connector's vicinity.
    Returns placement evidence. Does not fill zones, touch tracks or save files.
    """
    outline = b.GetBoardEdgesBoundingBox()
    if abs(silk.mm(outline.GetX())) > 0.1 or abs(silk.mm(outline.GetY())) > 0.1:
        raise RuntimeError('R6 silkscreen expects the board origin at (0, 0)')
    silk.W, silk.L = silk.mm(outline.GetWidth()), silk.mm(outline.GetHeight())
    for d in list(b.GetDrawings()):
        if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            b.Delete(d)
    for f in b.GetFootprints():
        for field in f.GetFields():
            field.SetVisible(False)
    # Keep polarity visible in assembly drawings; the package hides these glyphs.
    buzzer = silk.fp_of(b, 'LS120')
    for mark in buzzer.GraphicalItems():
        if isinstance(mark, pcbnew.PCB_TEXT) and mark.GetText() in ('+', '-'):
            mark.SetLayer(pcbnew.B_Fab if buzzer.IsFlipped() else pcbnew.F_Fab)
            mark.SetTextSize(pcbnew.VECTOR2I(silk.MM(0.8), silk.MM(0.8)))
            mark.SetTextThickness(silk.MM(0.1))
    silks = {side: silk.Silk(b, side, strict_bodies=True) for side in ('F', 'B')}
    placed, missing = {}, []

    def box(cx, cy, rx, ry):
        return (max(0.4, cx - rx), max(0.4, cy - ry),
                min(silk.W - 0.4, cx + rx), min(silk.L - 0.4, cy + ry))

    whole = (0.4, 0.4, silk.W - 0.4, silk.L - 0.4)

    def put(text, near, region, sides=('F', 'B'), angles=(0, 90), required=True,
            fallback=False):
        result = silk.label(b, silks, text, near, region, angles, sides, size=1.0)
        if result is None and fallback:
            result = silk.label(b, silks, text, near, whole, angles, ('B', 'F'), size=1.0)
        placed[text] = result
        if result is None and required:
            missing.append(text)
        return result

    def centre(ref):
        pos = silk.fp_of(b, ref).GetPosition()
        return silk.mm(pos.x), silk.mm(pos.y)

    # Place essential local labels before extended pin tables and optional refs.
    for ref, name in [('J124', 'ARM'), ('J121', 'IGN'), ('J1', 'BAT'),
                      ('J9', 'CAM'), ('J130', 'RADIO'), ('J131', 'GPS'),
                      ('J2', 'SWD'), ('J122', 'SERVO'), ('J123', 'PULL')]:
        cx, cy = centre(ref)
        put(name, (cx, cy - 5), box(cx, cy, 8, 8))

    # Terminal pin labels remain local to the correct terminal, both sides allowed.
    for ref, mapping in [('J124', (('1', 'BUS1'), ('2', 'RAW'))),
                         ('J121', (('1', 'E1-'), ('2', 'E1+'))),
                         ('J1', (('1', 'BAT+'), ('2', 'GND'), ('3', 'SW'), ('4', 'SW')))]:
        cx, _ = centre(ref)
        for number, name in mapping:
            x, y = silk.pad(b, ref, number)
            # Numbered strings avoid misreading labels where entry-side space is tight.
            text = number + ':' + name
            put(text, (x, y - 3), box(x, y, 3.8, 8), angles=(90, 0))

    # Connector-identified, numbered rows survive congested 1 mm connector pitches.
    # A row has no more than two pins so it can fit a genuine free area after routing.
    for ref, (_, pins) in PORTS.items():
        cx, cy = centre(ref)
        for start in range(0, len(pins), 2):
            row = ref + ' ' + ' '.join(f'{i + 1}:{pins[i]}'
                                       for i in range(start, min(start + 2, len(pins))))
            put(row, (cx - 11, cy + start), box(cx - 10, cy, 13, 12),
                sides=('B', 'F'), angles=(0, 90), fallback=True)
    put('UART 3V3 / RX-TX AT MODULE', (22, 42), whole, sides=('B', 'F'), angles=(0, 90), fallback=True)

    # Servo header columns and row numbers; the numbered map also names the connector.
    cx, cy = centre('J122')
    put('J122 1:S 2:+ 3:GND', (cx, cy - 4), box(cx, cy, 15, 8),
        sides=('B', 'F'), fallback=True)
    for number, row in [('3', '1'), ('6', '2'), ('9', '3'), ('12', '4')]:
        x, y = silk.pad(b, 'J122', number)
        put(row, (x - 2, y), box(x - 2, y, 1.3, 1.3), angles=(0,), required=False)
    cx, cy = centre('J123')
    put('J123 1:PULL 2:GND', (cx, cy + 4), box(cx, cy, 12, 8),
        sides=('B', 'F'), fallback=True)
    put('J124 2-FUSE-1: ARM LAST', (23, silk.L - 2), whole,
        sides=('B', 'F'), angles=(0, 90), fallback=True)
    put('J1 BAT LEAD: 15A FUSE', (23, silk.L - 8), whole,
        sides=('B', 'F'), angles=(0, 90), fallback=True)
    put('J124: 5A FAST / 2S', (23, silk.L - 4), whole,
        sides=('B', 'F'), angles=(0, 90), fallback=True)
    put(REV, (23, silk.L - 6), whole, sides=('B', 'F'), angles=(0, 90), fallback=True)
    put('JLCJLCJLCJLC', (23, 76), whole, sides=('B', 'F'), angles=(0, 90), required=False)
    if missing:
        raise RuntimeError('Essential R6 silkscreen did not fit: ' + ', '.join(missing))

    silk.pin1_dots(b, silks)
    silk.designators(b, silks)
    silk.fab_refs(b)
    b.GetTitleBlock().SetRevision(REV)
    print(f'R6 silkscreen: {sum(v is not None for v in placed.values())} labels; '
          f'{len(silk.HIDDEN)} hidden refs retained on Fab')
    return {'revision': REV, 'labels': placed, 'hidden_references': sorted(silk.HIDDEN)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    board = pcbnew.LoadBoard(str(args.board))
    finish(board)
    pcbnew.SaveBoard(str(args.output), board, True)
