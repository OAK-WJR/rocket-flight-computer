#!/usr/bin/env python3
"""Check the exported solder-paste Gerbers against the board's pads (the fab package's paste check, ORDERING section 4).

usage: <KiCad python3> -I tools/paste_check.py [board.kicad_pcb] [fab/m3_gerber.zip] [--json out.json]
exit 0 = every rule holds

Reads F_Paste / B_Paste from the Gerber zip (or a folder of .gbr files) that tools/export_fab.py wrote. KiCad flashes
each pad's paste opening at the pad's position with the pad's component in a %TO.C attribute, so every flash is matched
to a pad of that component on that side, by position (within 1 um). Rules:
  1. every flash belongs to exactly one pad of its own component that carries paste on that side (no stray paste, and
     none on a pad that carries no paste, such as the SMA jacks J30/J31, the unfitted lands, bare test pads or J2);
  2. every pad that carries paste on a side gets exactly one flash there (no pad left dry, none printed twice);
  3. no flash centre lies inside a pad that must stay dry: the SMA jacks' pads (fitted in the through-hole step) and
     every pad of an unfitted placeholder (DNP and out of the BOM; tools/export_fab.py), whoever the flash names;
  4. no paste region (G36/G37) or draw (D01) at all: the board's paste is pads only (a region would need its own rule).
Coordinates: Gerber Y = -KiCad Y (KiCad's original coordinates, %TF.SameCoordinates%).
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys
import zipfile

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
DRY_REFS = re.compile(r'^J3[01]$')            # SMA edge jacks: hand-soldered in the through-hole step, no paste
TOL = 1000                                    # nm: flash to pad position
SIDES = {'F': ('F_Paste', pcbnew.F_Paste), 'B': ('B_Paste', pcbnew.B_Paste)}


def gerbers(source):
    """{'F': text, 'B': text} of the paste layers in a zip or a folder."""
    out = {}
    source = Path(source)
    if source.is_dir():
        files = {p.name: p.read_text() for p in source.glob('*.gbr')}
    else:
        with zipfile.ZipFile(source) as z:
            files = {n: z.read(n).decode() for n in z.namelist() if n.endswith('.gbr')}
    for side, (tag, _) in SIDES.items():
        names = [n for n in files if n.endswith(f'-{tag}.gbr')]
        if len(names) != 1:
            raise ValueError(f'expected one {tag} Gerber, found {names}')
        out[side] = files[names[0]]
    return out


def parse(text):
    """Flashes [(component, x_nm, y_nm_kicad, aperture)] and the other drawing operations of one Gerber layer."""
    fmt = re.search(r'%FSLAX(\d)(\d)Y(\d)(\d)\*%', text)
    if not fmt or fmt.group(2) != '6' or fmt.group(4) != '6' or '%MOMM*%' not in text:
        raise ValueError('expected KiCad mm Gerbers in format 4.6')
    flashes, other = [], []
    comp, aperture, x, y = None, None, None, None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith('%TO.C,'):
            comp = line[len('%TO.C,'):].rstrip('*%')
            continue
        if line.startswith('%TD'):
            comp = None
            continue
        if line.startswith(('G36', 'G37')):
            other.append(('region', comp, line))
            continue
        m = re.fullmatch(r'D(\d+)\*', line)
        if m and int(m.group(1)) >= 10:
            aperture = int(m.group(1))
            continue
        m = re.fullmatch(r'(?:X(-?\d+))?(?:Y(-?\d+))?D0([123])\*', line)
        if m:
            x = int(m.group(1)) if m.group(1) is not None else x
            y = int(m.group(2)) if m.group(2) is not None else y
            if m.group(3) == '3':
                flashes.append((comp, x, -y, aperture))
            elif m.group(3) == '1':
                other.append(('draw', comp, line))
    return flashes, other


def check(board, layers):
    """Issues and evidence of rules 1-4 for the parsed paste layers {'F': text, 'B': text}."""
    issues, evidence = [], {}
    by_ref = {f.GetReference(): f for f in board.GetFootprints()}
    dry = []
    for f in board.GetFootprints():
        placeholder = f.IsDNP() and f.IsExcludedFromBOM()
        if placeholder or DRY_REFS.match(f.GetReference()):
            dry += [(f.GetReference(), p) for p in f.Pads()]
    for side, (tag, paste) in SIDES.items():
        flashes, other = parse(layers[side])
        for kind, comp, line in other:
            issues.append(f'{tag}: {kind} ({comp}: {line}): the paste layers are pads only (rule 4)')
        hits = defaultdict(int)
        for comp, x, y, ap in flashes:
            at = pcbnew.VECTOR2I(x, y)
            f = by_ref.get(comp)
            if f is None:
                issues.append(f'{tag}: flash D{ap} at ({x / 1e6:.4f}, {y / 1e6:.4f}) names {comp}, not on the board')
                continue
            owners = [p for p in f.Pads() if p.IsOnLayer(paste) and
                      abs(p.GetPosition().x - x) <= TOL and abs(p.GetPosition().y - y) <= TOL]
            if len(owners) != 1:
                issues.append(f'{tag}: flash D{ap} at ({x / 1e6:.4f}, {y / 1e6:.4f}) of {comp} matches '
                              f'{len(owners)} pads carrying paste (rule 1)')
                continue
            hits[(comp, owners[0].GetNumber(), owners[0].GetPosition().x, owners[0].GetPosition().y)] += 1
            for ref, p in dry:
                if p.HitTest(at):
                    issues.append(f'{tag}: flash of {comp} at ({x / 1e6:.4f}, {y / 1e6:.4f}) lies in {ref}.'
                                  f'{p.GetNumber()}, which must stay dry (rule 3)')
        pasted = 0
        for f in board.GetFootprints():
            for p in f.Pads():
                if not p.IsOnLayer(paste):
                    continue
                pasted += 1
                n = hits.get((f.GetReference(), p.GetNumber(), p.GetPosition().x, p.GetPosition().y), 0)
                if n != 1:
                    issues.append(f'{tag}: {f.GetReference()}.{p.GetNumber()} carries paste but has {n} flashes '
                                  '(rule 2)')
        evidence[tag] = {'flashes': len(flashes), 'pads_with_paste': pasted,
                         'components': len({c for c, *_ in flashes})}
    for ref, p in dry:
        if p.IsOnLayer(pcbnew.F_Paste) or p.IsOnLayer(pcbnew.B_Paste):
            issues.append(f'{ref}.{p.GetNumber()} must stay dry but carries paste on the board (rule 3)')
    evidence['dry_pads'] = sorted({f'{ref}.{p.GetNumber()}' for ref, p in dry})
    return issues, evidence


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', nargs='?', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('gerbers', nargs='?', type=Path, default=ROOT / 'm3_design/assembly_review/fab/m3_gerber.zip')
    ap.add_argument('--json', type=Path)
    args = ap.parse_args()
    issues, evidence = check(pcbnew.LoadBoard(str(args.board.resolve())), gerbers(args.gerbers))
    for issue in issues:
        print('FAIL', issue)
    print(f"paste check: {'OK' if not issues else f'FAIL ({len(issues)})'}; "
          + '; '.join(f"{k} {v['flashes']} flashes on {v['pads_with_paste']} pasted pads"
                      for k, v in evidence.items() if k != 'dry_pads')
          + f"; {len(evidence['dry_pads'])} dry pads with no flash in them")
    if args.json:
        args.json.write_text(json.dumps(dict(ok=not issues, issues=issues, evidence=evidence), indent=1) + '\n')
    return 0 if not issues else 1


if __name__ == '__main__':
    sys.exit(main())
