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
  4. no paste region (G36/G37) or draw (D01) at all: the board's paste is pads only (a region would need its own rule);
  5. each aperture matches its native paste geometry (1 um), including reviewed margins and separate EP windows.
     Explicit dry/manual-process exceptions retain their native paste layers; no coverage percentage is imposed.
The command subset is KiCad mm/absolute 4.6, dark polarity, pad flashes and native aperture macros/attributes.
Legacy image controls are accepted only at their defaults; AS uses AXBY and IP uses POS. Non-default controls,
unit/notation changes, early stops and unknown commands fail closed. This is a project policy: Ucamco permits
readers to ignore several deprecated image controls. Comments and image-neutral metadata remain valid.
Coordinates: Gerber Y = -KiCad Y (KiCad's original coordinates, %TF.SameCoordinates%).
"""
import argparse
import ast
import math
from collections import defaultdict
from decimal import Decimal
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


# Geometric export parity, not a universal stencil-coverage requirement. Native
# paste margins, separate exposed-pad windows and explicit dry/manual lands stay
# authoritative. No stencil thickness or solder volume is inferred.
POLY_ERROR = 100                             # nm: each polygon approximation
GEOMETRY_TOL = TOL                           # 1 um; exceeds both approximation errors and 1 nm file rounding


def neutral_legacy(command):
    """Ucamco2026.05 section8.1: accept defaults only, rather than interpret legacy image transforms."""
    if command in ('ASAXBY', 'IPPOS', 'IR0'):
        return True
    if command.startswith('MI'):
        match = re.fullmatch(r'MI(?:A([01]))?(?:B([01]))?', command)
        return bool(match) and all(v in (None, '0') for v in match.groups())
    kind = command[:2]
    if kind in ('OF', 'SF'):
        number = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)'
        match = re.fullmatch(rf'{kind}(?:A({number}))?(?:B({number}))?', command)
        default = 0 if kind == 'OF' else 1
        return bool(match) and all(v is None or Decimal(v) == default for v in match.groups())
    return False


def commands(text):
    """Tokenize and validate the native subset; never silently discard an image/state command."""
    position, ended, headers = 0, False, []
    while position < len(text):
        if text[position].isspace():
            position += 1
            continue
        extended = text[position] == '%'
        end = text.find('%' if extended else '*', position + 1)
        if end < 0:
            raise ValueError('unterminated paste command')
        token = text[position:end + 1]
        position = end + 1
        if ended:
            raise ValueError('paste data after M02 end command')
        if extended:
            if not token.endswith('*%'):
                raise ValueError('malformed extended paste command')
            command = token[1:-2]
            if command in ('FSLAX46Y46', 'MOMM'):
                headers.append(command)
            elif not (command == 'LPD' or neutral_legacy(command)
                      or re.fullmatch(r'(?:ADD\d+[^,*%]+(?:,[^*%]*)?|AM[^*%]+\*.*)', command, re.S)
                      or re.fullmatch(r'(?:T[FAO][^*%]+|TD(?:\.[^*%]+)?|(?:IN|LN)[^*%]+)', command)):
                raise ValueError(f'unsupported paste command {token[:80]}')
            if command.startswith(('ADD', 'AM')) and set(headers) != {'FSLAX46Y46', 'MOMM'}:
                raise ValueError('paste aperture before native mm/absolute headers')
        else:
            command = token[:-1]
            # G71/G90 confirm the required mm/absolute state; M01 has no effect.
            if not (command.startswith('G04') or command in ('G01', 'G75', 'G36', 'G37', 'G71', 'G90', 'M01', 'M02')
                    or re.fullmatch(r'D(?:[1-9]\d+)', command)
                    or re.fullmatch(r'(?:X-?\d+)?(?:Y-?\d+)?D0[123]', command)):
                raise ValueError(f'unsupported paste command {token[:80]}')
            if not command.startswith('G04') and set(headers) != {'FSLAX46Y46', 'MOMM'}:
                raise ValueError('paste operation before native mm/absolute headers')
            ended = command == 'M02'
        yield token
    if headers.count('FSLAX46Y46') != 1 or headers.count('MOMM') != 1:
        raise ValueError('expected one KiCad mm/absolute format4.6 header')
    if not ended:
        raise ValueError('missing paste M02 end command')


def polygon(points, rotation=0.):
    """Gerber-mm vertices -> native-nm polygon, reflecting Gerber Y."""
    angle = math.radians(rotation)
    c, s = math.cos(angle), math.sin(angle)
    result = pcbnew.SHAPE_POLY_SET()
    result.NewOutline()
    for x, y in points:
        result.Append(round((c * x - s * y) * 1e6), round(-(s * x + c * y) * 1e6))
    return result


def circle(diameter, x=0., y=0., rotation=0.):
    if not math.isfinite(diameter) or diameter <= 0:
        raise ValueError('paste circle diameter must be finite and positive')
    r = diameter / 2
    count = max(16, math.ceil(math.pi / math.acos(max(-1., 1 - POLY_ERROR / (r * 1e6)))))
    return polygon([(x + r * math.cos(2 * math.pi * i / count),
                     y + r * math.sin(2 * math.pi * i / count)) for i in range(count)], rotation)


def expression(text, parameters):
    """The arithmetic subset in KiCad's Gerber macros; never execute source text."""
    def parameter(match):
        index = int(match[1])
        if not 1 <= index <= len(parameters):
            raise ValueError('undefined paste macro parameter')
        return repr(parameters[index - 1])
    text = re.sub(r'\$(\d+)', parameter, text)
    def value(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            return value(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        if isinstance(node, ast.BinOp) and type(node.op) in (ast.Add, ast.Sub, ast.Mult, ast.Div):
            a, b = value(node.left), value(node.right)
            return {ast.Add: lambda: a + b, ast.Sub: lambda: a - b,
                    ast.Mult: lambda: a * b, ast.Div: lambda: a / b}[type(node.op)]()
        raise ValueError('unsupported paste macro expression')
    try:
        result = value(ast.parse(text.replace('x', '*').replace('X', '*'), mode='eval').body)
    except (SyntaxError, IndexError, ZeroDivisionError, OverflowError) as error:
        raise ValueError('invalid paste macro expression') from error
    if not math.isfinite(result):
        raise ValueError('nonfinite paste macro expression')
    return result


def macro_shape(body, parameters):
    """Ucamco primitives 1/4/20, including dark/clear exposure and primitive rotation."""
    result = pcbnew.SHAPE_POLY_SET()
    for command in body.split('*'):
        command = command.strip()
        if not command or re.match(r'^0(?:\s|,)', command):
            continue
        v = [expression(part.strip(), parameters) for part in command.split(',')]
        if len(v) < 2:
            raise ValueError('invalid paste macro primitive')
        code, exposure = v[:2]
        if exposure not in (0, 1):
            raise ValueError('invalid paste macro exposure')
        if code == 1 and len(v) in (5, 6):
            shape = circle(v[2], v[3], v[4], v[5] if len(v) == 6 else 0.)
        elif code == 4 and len(v) >= 12 and float(v[2]).is_integer() and v[2] >= 3:
            pts = list(zip(v[3:-1:2], v[4:-1:2]))
            if len(v) != 4 + 2 * (int(v[2]) + 1) or pts[0] != pts[-1]:
                raise ValueError('invalid paste macro outline')
            shape = polygon(pts[:-1], v[-1])
        elif code == 20 and len(v) == 8 and v[2] > 0:
            _, _, width, ax, ay, bx, by, rotation = v
            length = math.hypot(bx - ax, by - ay)
            if not length:
                raise ValueError('zero-length paste vector primitive')
            dx, dy = -(by - ay) * width / (2 * length), (bx - ax) * width / (2 * length)
            shape = polygon([(ax + dx, ay + dy), (bx + dx, by + dy),
                             (bx - dx, by - dy), (ax - dx, ay - dy)], rotation)
        else:
            raise ValueError(f'unsupported paste macro primitive {code:g}')
        if exposure:
            result.BooleanAdd(shape)
        else:
            result.BooleanSubtract(shape)
    if result.Area() <= 0:
        raise ValueError('empty paste macro aperture')
    return result


def apertures(text):
    """Read the emitted KiCad aperture subset; unsupported image operations fail closed."""
    text = '\n'.join(token for token in commands(text) if token.startswith(('%AM', '%ADD')))
    macros = dict(re.findall(r'%AM([^*%]+)\*(.*?)%', text, re.S))
    result = {}
    for ident, kind, raw in re.findall(r'%ADD(\d+)([^,*%]+)(?:,([^*%]*))?\*%', text):
        number = int(ident)
        try:
            params = [float(v) for v in raw.split('X')] if raw else []
        except ValueError as error:
            raise ValueError(f'invalid paste aperture D{number}') from error
        if not all(math.isfinite(v) for v in params) or number in result:
            raise ValueError(f'nonfinite or duplicate paste aperture D{number}')
        if kind == 'C' and len(params) == 1:
            shape = circle(params[0])
        elif kind in ('R', 'O') and len(params) == 2 and min(params) > 0:
            width, height = params
            if kind == 'R':
                shape = polygon([(-width / 2, -height / 2), (width / 2, -height / 2),
                                 (width / 2, height / 2), (-width / 2, height / 2)])
            else:
                d, dx, dy = min(params), max(0., width - height) / 2, max(0., height - width) / 2
                shape = circle(d, -dx, -dy)
                shape.BooleanAdd(circle(d, dx, dy))
                if dx or dy:
                    shape.BooleanAdd(polygon([(-width / 2 + d / 2, -height / 2),
                                              (width / 2 - d / 2, -height / 2),
                                              (width / 2 - d / 2, height / 2),
                                              (-width / 2 + d / 2, height / 2)]) if dx else
                                     polygon([(-width / 2, -height / 2 + d / 2),
                                              (width / 2, -height / 2 + d / 2),
                                              (width / 2, height / 2 - d / 2),
                                              (-width / 2, height / 2 - d / 2)]))
        elif kind in macros:
            shape = macro_shape(macros[kind], params)
        else:
            raise ValueError(f'unsupported paste aperture D{number}: {kind}')
        result[number] = shape
    return result


def expected_paste(pad, layer):
    """Native plotted pad in the flash's local frame, preserving KiCad10.0.7 margins.
    See pcbnew/plot_board_layers.cpp, PlotStandardLayer/plotPadLayer.
    """
    copy = pcbnew.PAD(pad)
    copy.SetPosition(pcbnew.VECTOR2I(0, 0))
    margin, size, shape = pad.GetSolderPasteMargin(layer), pad.GetSize(layer), pad.GetShape(layer)
    grown = pcbnew.VECTOR2I(size.x + 2 * margin.x, size.y + 2 * margin.y)
    if shape in (pcbnew.PAD_SHAPE_CUSTOM, pcbnew.PAD_SHAPE_TRAPEZOID):
        # Custom artwork is polygonized at the board's plot precision before
        # paste inflation/deflation; retain that reviewed native polygonization.
        error = pad.GetBoard().GetDesignSettings().m_MaxError
        result = pcbnew.SHAPE_POLY_SET()
        copy.TransformShapeToPolygon(result, layer, 0, error, pcbnew.ERROR_INSIDE)
        if margin.x:
            result.InflateWithLinkedHoles(margin.x, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, error)
        return result
    if min(grown.x, grown.y) <= 0:
        raise ValueError('native paste aperture is empty')
    copy.SetSize(layer, grown)
    if shape == pcbnew.PAD_SHAPE_ROUNDRECT and margin.x == margin.y:
        copy.SetRoundRectCornerRadius(layer, max(0, pad.GetRoundRectCornerRadius(layer) + margin.x))
    elif shape == pcbnew.PAD_SHAPE_RECT and margin.x > 0:
        copy.SetShape(layer, pcbnew.PAD_SHAPE_ROUNDRECT)
        copy.SetRoundRectCornerRadius(layer, margin.x)
    elif shape == pcbnew.PAD_SHAPE_CHAMFERED_RECT:
        # R12F5-TRI-06 (R12's U6 corner lands, NXP's chamfered land): plotted at the pad's own outline; a paste margin
        # on a chamfered pad is not a reviewed geometry, so it fails closed
        if margin.x or margin.y:
            raise ValueError('chamfered paste pad with a paste margin (not reviewed)')
    elif shape not in (pcbnew.PAD_SHAPE_CIRCLE, pcbnew.PAD_SHAPE_OVAL,
                        pcbnew.PAD_SHAPE_RECT, pcbnew.PAD_SHAPE_ROUNDRECT):
        raise ValueError('unsupported native paste pad shape')
    result = pcbnew.SHAPE_POLY_SET()
    copy.TransformShapeToPolygon(result, layer, 0, POLY_ERROR, pcbnew.ERROR_INSIDE)
    return result


def geometry_matches(actual, expected):
    for source, target in ((actual, expected), (expected, actual)):
        outer = pcbnew.SHAPE_POLY_SET(target)
        outer.Inflate(GEOMETRY_TOL, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, POLY_ERROR)
        extra = pcbnew.SHAPE_POLY_SET(source)
        extra.BooleanSubtract(outer)
        if extra.Area() > 0:
            return False
    return True


def parse(text):
    """Flashes [(component, x_nm, y_nm_kicad, aperture)] and the other drawing operations of one Gerber layer."""
    flashes, other = [], []
    comp, aperture, x, y = None, None, None, None
    for line in commands(text):
        if line.startswith('%TO.C,'):
            comp = line[len('%TO.C,'):-2]
            continue
        if line in ('%TD*%', '%TD.C*%'):
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
                if x is None or y is None or aperture is None:
                    raise ValueError('paste flash without coordinates/aperture')
                flashes.append((comp, x, -y, aperture))
            elif m.group(3) == '1':
                other.append(('draw', comp, line))
    return flashes, other


def check(board, layers):
    """Issues and evidence of rules 1-5 for the parsed paste layers {'F': text, 'B': text}."""
    issues, evidence = [], {}
    by_ref = {f.GetReference(): f for f in board.GetFootprints()}
    dry = []
    for f in board.GetFootprints():
        placeholder = f.IsDNP() and f.IsExcludedFromBOM()
        if placeholder or DRY_REFS.match(f.GetReference()):
            dry += [(f.GetReference(), p) for p in f.Pads()]
    for side, (tag, paste) in SIDES.items():
        pasted = sum(p.IsOnLayer(paste) for f in board.GetFootprints() for p in f.Pads())
        try:
            flashes, other = parse(layers[side])
            shapes = apertures(layers[side])
        except ValueError as error:
            issues.append(f'{tag}: {error} (rule 5)')
            evidence[tag] = dict(flashes=0, pads_with_paste=pasted, geometry_matched=0,
                                 components=0, parse_error=str(error))
            continue
        checked_geometry = 0
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
            try:
                if ap not in shapes or not geometry_matches(shapes[ap], expected_paste(owners[0], paste)):
                    issues.append(f'{tag}: {comp}.{owners[0].GetNumber()} aperture D{ap} differs from native '
                                  'paste geometry (rule 5)')
                else:
                    checked_geometry += 1
            except ValueError as error:
                issues.append(f'{tag}: {comp}.{owners[0].GetNumber()}: {error} (rule 5)')
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
        evidence[tag] = {'flashes': len(flashes), 'pads_with_paste': pasted, 'geometry_matched': checked_geometry,
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
