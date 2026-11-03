#!/usr/bin/env python3
"""R9 footprint variants and the board-side footprint rules (M3-ASSY-R9, build step 2; r9_plan.md sections 1, 4;
R9_OWNER_DECISIONS.md items 2 and 5; R9_DECISIONS.md D-S2-*).

usage: python3 m3_design/r9_lib.py [project_dir] [--check]
Writes kilib/rocket.pretty/<variant>.kicad_mod for each VARIANTS entry, generated from its base footprint (both in
the same library); --check writes nothing and exits 1 if a variant file is missing or differs. A second run changes
nothing. The board functions (apply_variants, clear_overrides, compare_to_library) need KiCad's Python; the library
part runs under plain python3.

A variant is its base footprint mirrored about the footprint's local y axis: every pad, graphic and text position
has x -> -x. So it is the same part on the same land (the same pad positions, pad sizes, drills and layers; the
footprint courtyard, fabrication outline and 3D model are the base's, because those are symmetric about that axis,
which build() asserts) with the pad numbering reversed along x. The pin-1 marks move with pin 1: the square THT pad
(the library's pin-1 convention: J1's DB128V, the DB128L and the 3 x 4 header all mark pin 1 so) and the header's
pin-1 silkscreen corner and dot. Nets stay with pad numbers, so the netlist is unchanged.
- M3_DB128L_2P_BK_SW (J121, J124): DORABO DB128L-5.08-2P-BK-S, LCSC C430601, pads 1 and 2 change places. Turned to
  rotation 90 (wire entry -x), J124's RAW pin (2) lies forward and its BUS pin (1) aft, J121's IGN pin (2) forward and
  its OUT pin (1) aft (plan_spine.md section 2.1).
- HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR (J122): hanxia HX PZ2.54-3x4P ZZ, LCSC C32713291, the four plug columns
  numbered from +x: plug 1 (pads 1/2/3 = SIG/RAW/GND) at local x +3.81. Turned to rotation 180, plug 1 (SERVO1) is
  the west plug and the SIG row is aft, so U1.22-25 reach plugs 1-4 in order (plan_spine.md section 2.3). The rows
  do not move (RAW stays the middle row: a reversed servo plug stays harmless, DESIGN_ASSURANCE). The header's 3D model
  is the base's: its body box is symmetric (+-5.08 x +-3.79 mm); its only asymmetric parts are a printed glyph on the
  top face and the mesh triangulation (Inference from the model's vertex data; the part is unkeyed square pins).

PAD_ALIAS gives, for each variant pad number, the base (maker / EasyEDA) number at the same position: JLC places
parts with the maker's numbering, so tools/jlc_orient.py matches pads through it (a match by raw number would turn
the terminal body 180 degrees and face its wire entry into the board).

Board side (the step-3 builder and m3_design/r9_sch_check.py):
- apply_variants(board): each base instance of VARIANT_REFS becomes the variant in place: its pads and footprint
  graphics are mirrored the same way in its own frame and its FPID and description set; reference, value, fields,
  path, UUIDs, pad nets and pad-level settings stay (J122's solid GND pads, for one). compare_to_library() then checks
  the instance against the library variant; KiCad DRC's lib_footprint_mismatch checks it too.
- clear_overrides(board): LC-1 (R9_DECISIONS D-S1-01): no pad or footprint keeps a local clearance; the clearances
  R8 carried that way are rules of m3.kicad_dru in R9 (m3_design/r9_dru.py).
"""
import re
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE / 'assembly_review'
LIB_NICK = 'rocket'
NS = uuid.UUID('8c0f6a1e-2b4d-5e79-9a35-0d6c1f7e4b92')      # fixed namespace -> stable variant UUIDs

VARIANTS = {   # variant -> (base, description)
    'M3_DB128L_2P_BK_SW': (
        'M3_DB128L_2P_BK',
        'DORABO DB128L-5.08-2P-BK-S (LCSC C430601, black; ARM terminals): 5.08 pitch; 1.6 finished hole; hole 5.00 '
        'from body face; body 10.16 wide (end-stackable, two make the 4P envelope) x 10.1 deep x 14.1 high; wire entry '
        'on local -y (arrows). R9 variant of M3_DB128L_2P_BK with pads 1 and 2 swapped (the base mirrored about its '
        'local y axis: same part, same land; pin 1, the square pad, at local +2.54)'),
    'HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR': (
        'HDR-TH_12P-P2.54-V-M-R3-C4-S2.54',
        'hanxia HX PZ2.54-3x4P ZZ (LCSC C32713291), R9 variant of HDR-TH_12P-P2.54-V-M-R3-C4-S2.54 with the plug '
        'columns numbered from +x (the base mirrored about its local y axis: same part, same land, rows unchanged; '
        'pin 1, the square pad, at local +3.81 / +2.54)'),
}
VARIANT_REFS = {'J121': 'M3_DB128L_2P_BK_SW', 'J124': 'M3_DB128L_2P_BK_SW',
                'J122': 'HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR'}
COORD = re.compile(r'\((at|start|end|center|mid|xy) (-?[\d.]+) (-?[\d.]+)((?: -?[\d.]+)?)\)')
SYMMETRIC_LAYERS = ('F.CrtYd', 'B.CrtYd', 'F.Fab', 'B.Fab')    # must be symmetric about local x = 0 (same body)


def neg(s):
    """-x in KiCad's number format ('0' stays '0')."""
    if float(s) == 0:
        return s
    return s[1:] if s.startswith('-') else '-' + s


def mirrored(text, base, variant, descr):
    """The variant's .kicad_mod text from the base's."""
    assert text.startswith(f'(footprint "{base}"\n'), f'{base}: unexpected file head'
    assert '(justify' not in text, f'{base}: a justified text would need its justification mirrored too'

    def coord(m):
        key, x, y, angle = m.groups()
        assert not angle.strip() or float(angle) == 0, f'{base}: rotated item {m.group(0)} (its angle would mirror too)'
        return f'({key} {neg(x)} {y}{angle})'
    out = COORD.sub(coord, text)
    out = out.replace(f'(footprint "{base}"\n', f'(footprint "{variant}"\n', 1)
    value = f'(property "Value" "{base}"'
    assert out.count(value) == 1, f'{base}: Value property'
    out = out.replace(value, f'(property "Value" "{variant}"')
    d = re.search(r'\n\t\(descr "[^"]*"\)', out)
    new = f'\n\t(descr "{descr}")'
    out = out[:d.start()] + new + out[d.end():] if d else out.replace('\n\t(layer "F.Cu")', new + '\n\t(layer "F.Cu")', 1)
    out = re.sub(r'\(uuid "([0-9a-f-]+)"\)', lambda m: f'(uuid "{uuid.uuid5(NS, variant + ":" + m.group(1))}")', out)
    return out


# --- parsing (plain python: pads and graphics of a .kicad_mod) ---------------------------------------------------
def _blocks(text, head):
    out, i = [], 0
    while True:
        i = text.find(head, i)
        if i < 0:
            return out
        i += head.index('(')
        depth = 0
        for j in range(i, len(text)):
            depth += {'(': 1, ')': -1}.get(text[j], 0)
            if depth == 0:
                out.append(text[i:j + 1])
                i = j + 1
                break


def pads(text):
    """{number: (shape, x, y, size, drill, layers)} of a footprint file."""
    out = {}
    for blk in _blocks(text, '\n\t(pad '):
        m = re.match(r'\s*\(pad "([^"]*)" (\S+) (\S+)', blk)
        at = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)\)', blk)
        size = re.search(r'\(size ([\d.]+) ([\d.]+)\)', blk).groups()
        drill = re.search(r'\(drill ([\d.]+)\)', blk)
        layers = re.search(r'\(layers ([^)]*)\)', blk).group(1)
        assert m.group(1) not in out, f'pad {m.group(1)} twice'
        out[m.group(1)] = (m.group(3), round(float(at.group(1)), 4), round(float(at.group(2)), 4), size,
                           drill.group(1) if drill else None, layers)
    return out


def graphics(text, layers=None):
    """Multiset (sorted list) of (kind, layer, points) of the footprint's fp_* graphics, optionally on given layers."""
    out = []
    for kind in ('fp_line', 'fp_rect', 'fp_circle', 'fp_arc', 'fp_poly'):
        for blk in _blocks(text, f'\n\t({kind}'):
            lay = re.search(r'\(layer "([^"]+)"\)', blk).group(1)
            if layers and lay not in layers:
                continue
            pts = tuple((round(float(x), 4), round(float(y), 4)) for _, x, y, _a in COORD.findall(blk))
            out.append((kind, lay, _norm(kind, pts)))
    return sorted(out)


def _norm(kind, pts):
    """A segment is undirected, a rectangle is its corner box."""
    if kind == 'fp_line':
        return tuple(sorted(pts))
    if kind == 'fp_rect':
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return (min(xs), min(ys)), (max(xs), max(ys))
    return pts


def mirror_graphics(g):
    return sorted((kind, lay, _norm(kind, tuple((-x if x else 0.0, y) for x, y in pts))) for kind, lay, pts in g)


def models(text):
    return re.findall(r'\(model "([^"]+)"', text)


def alias(base_text, variant_text):
    """{variant pad number: base pad number at the same position}."""
    bp, vp = pads(base_text), pads(variant_text)
    at = {(x, y): n for n, (_s, x, y, *_r) in bp.items()}
    out = {n: at[(x, y)] for n, (_s, x, y, *_r) in vp.items()}
    assert sorted(out.values(), key=str) == sorted(bp, key=str), 'variant pads must sit on the base pad positions'
    return out


def build(lib, variant):
    """(variant text, alias, findings) from the base file in lib; findings name any departure from 'same land'."""
    base, descr = VARIANTS[variant]
    btext = (lib / f'{base}.kicad_mod').read_text()
    vtext = mirrored(btext, base, variant, descr)
    issues = []
    bp, vp = pads(btext), pads(vtext)
    if set(bp) != set(vp):
        issues.append(f'{variant}: pad numbers differ from {base}')
    for n in bp:                                              # every pad keeps its shape, size, drill and layers ...
        if (bp[n][0], *bp[n][3:]) != (vp[n][0], *vp[n][3:]) or (bp[n][1], bp[n][2]) != (-vp[n][1] or 0.0, vp[n][2]):
            issues.append(f'{variant}: pad {n} is not the mirror of {base} pad {n}')
    land = lambda p: sorted((x, y, sz, dr, ly) for _s, x, y, sz, dr, ly in p.values())      # noqa: E731
    if land(bp) != land(vp):                                  # ... and the land (positions, sizes, drills) is the same
        issues.append(f'{variant}: pad positions / sizes / drills differ from {base} (not the same land)')
    sym = graphics(btext, SYMMETRIC_LAYERS)
    if mirror_graphics(sym) != sym:
        issues.append(f'{base}: courtyard or fabrication outline not symmetric about local x = 0 (a different body)')
    if graphics(vtext, SYMMETRIC_LAYERS) != sym:
        issues.append(f'{variant}: courtyard or fabrication outline differs from {base}')
    if models(vtext) != models(btext) or len(models(btext)) != 1:
        issues.append(f'{variant}: 3D model differs from {base}')
    for blk in _blocks(btext, '\n\t(property ') + _blocks(btext, '\n\t(fp_text '):
        if float(re.search(r'\(at (-?[\d.]+) ', blk).group(1)) != 0:
            issues.append(f'{base}: a text off local x = 0 (the variant would move it)')
    return vtext, alias(btext, vtext), issues


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    project = Path(args[0]) if args else PROJECT
    lib = project / 'kilib' / f'{LIB_NICK}.pretty'
    bad = []
    for variant in VARIANTS:
        text, al, issues = build(lib, variant)
        bad += issues
        path = lib / f'{variant}.kicad_mod'
        now = path.read_text() if path.is_file() else None
        if '--check' in sys.argv:
            if now != text:
                bad.append(f'{path.name} {"missing" if now is None else "differs from its generated text"}')
        elif now != text and not issues:
            path.write_text(text)
            print('wrote', path.name)
        print(f'{variant}: base {VARIANTS[variant][0]}, pad alias (variant -> base) '
              + ' '.join(f'{k}:{v}' for k, v in sorted(al.items(), key=lambda kv: int(kv[0]))))
    for i in bad:
        print('FAIL', i)
    return 1 if bad else 0


# --- board side (KiCad Python) -------------------------------------------------------------------------------------
def library_footprint(name, project=PROJECT):
    import pcbnew
    f = pcbnew.FootprintLoad(str(project / 'kilib' / f'{LIB_NICK}.pretty'), name)
    assert f is not None, f'{name} not in {LIB_NICK}.pretty'
    return f


def _local(f, p):
    """Footprint-frame coordinates (mm) of a board point (KiCad: board = O + R(theta) local, y down)."""
    import math
    import pcbnew
    th = math.radians(f.GetOrientationDegrees())
    c, s = math.cos(th), math.sin(th)
    dx, dy = pcbnew.ToMM(p.x - f.GetPosition().x), pcbnew.ToMM(p.y - f.GetPosition().y)
    return round(dx * c - dy * s, 4) + 0.0, round(dx * s + dy * c, 4) + 0.0


def footprint_shape(f):
    """Pads and graphics of a footprint in its own frame, comparable between a board instance and the library."""
    import pcbnew
    assert not f.IsFlipped(), f'{f.GetReference()}: only top-side footprints are compared here'
    pad_rows = {}
    for p in f.Pads():
        sz = p.GetSize(pcbnew.F_Cu)
        dr = p.GetDrillSize()
        pad_rows[p.GetNumber()] = (p.GetShape(pcbnew.F_Cu), _local(f, p.GetPosition()),
                                   (pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)), (pcbnew.ToMM(dr.x), pcbnew.ToMM(dr.y)),
                                   p.GetLayerSet().FmtHex(), p.GetAttribute(),
                                   round((p.GetOrientationDegrees() - f.GetOrientationDegrees()) % 180, 3))
    shapes = []
    for g in f.GraphicalItems():
        if g.GetClass() != 'PCB_SHAPE':
            continue
        pts = [g.GetStart(), g.GetEnd()]
        if g.GetShape() == pcbnew.SHAPE_T_ARC:
            pts.append(g.GetArcMid())
        local = [_local(f, q) for q in pts]
        if g.GetShape() in (pcbnew.SHAPE_T_SEGMENT, pcbnew.SHAPE_T_RECT):
            local = sorted(local)
            if g.GetShape() == pcbnew.SHAPE_T_RECT:          # a rectangle by its corner box, whatever the rotation
                xs, ys = [q[0] for q in local], [q[1] for q in local]
                local = [(min(xs), min(ys)), (max(xs), max(ys))]
        shapes.append((g.GetShape(), g.GetLayerName(), tuple(local), round(pcbnew.ToMM(g.GetWidth()), 4)))
    return pad_rows, sorted(shapes)


def compare_to_library(f, project=PROJECT):
    """Differences between a board instance and its library footprint (pads and graphics, footprint frame)."""
    name = str(f.GetFPID().GetLibItemName())
    lib = library_footprint(name, project)
    a, b = footprint_shape(f), footprint_shape(lib)
    issues = []
    if a[0] != b[0]:
        diff = sorted(n for n in set(a[0]) | set(b[0]) if a[0].get(n) != b[0].get(n))
        issues.append(f'{f.GetReference()}: pads {diff} differ from library {name}')
    if a[1] != b[1]:
        issues.append(f'{f.GetReference()}: graphics differ from library {name}')
    if f.GetLibDescription() != lib.GetLibDescription():
        issues.append(f'{f.GetReference()}: description differs from library {name}')
    return issues


def apply_variants(board, refs=VARIANT_REFS, project=PROJECT):
    """Turn each base instance of refs into its variant in place; returns the refs changed (idempotent)."""
    import pcbnew
    changed = []
    for ref, variant in sorted(refs.items()):
        f = board.FindFootprintByReference(ref)
        assert f is not None, f'{ref} missing'
        name = str(f.GetFPID().GetLibItemName())
        if name == variant:
            continue
        base = VARIANTS[variant][0]
        assert name == base, f'{ref}: footprint {name}, expected {base} or {variant}'
        assert not f.IsFlipped(), f'{ref}: a bottom-side instance is not expected'
        th = round(f.GetOrientationDegrees()) % 360
        assert th in (0, 90, 180, 270) and abs(f.GetOrientationDegrees() - round(f.GetOrientationDegrees())) < 1e-9, \
            f'{ref}: orientation {f.GetOrientationDegrees()} (only multiples of 90 degrees)'
        direction = pcbnew.FLIP_DIRECTION_LEFT_RIGHT if th in (0, 180) else pcbnew.FLIP_DIRECTION_TOP_BOTTOM
        origin = f.GetPosition()
        for p in f.Pads():
            assert round(p.GetFPRelativeOrientation().AsDegrees()) % 180 == 0, f'{ref}.{p.GetNumber()}: turned pad'
            rel = p.GetFPRelativePosition()
            p.SetFPRelativePosition(pcbnew.VECTOR2I(-rel.x, rel.y))
        for g in f.GraphicalItems():
            if g.GetClass() == 'PCB_SHAPE':
                g.Mirror(origin, direction)
            else:
                x, _y = _local(f, g.GetPosition())
                assert abs(x) < 1e-6, f'{ref}: footprint text off local x = 0 ({g.GetClass()})'
        f.SetFPID(pcbnew.LIB_ID(LIB_NICK, variant))
        f.SetLibDescription(VARIANTS[variant][1])
        f.BuildCourtyardCaches()
        issues = compare_to_library(f, project)
        assert not issues, issues
        changed.append(ref)
    return changed


def clear_overrides(board):
    """LC-1: every pad and footprint local clearance removed; returns what was cleared."""
    import pcbnew
    cleared = []
    for f in board.GetFootprints():
        if f.GetLocalClearance() is not None:
            cleared.append((f.GetReference(), '', pcbnew.ToMM(f.GetLocalClearance())))
            f.SetLocalClearance(None)
        for p in f.Pads():
            if p.GetLocalClearance() is not None:
                cleared.append((f.GetReference(), p.GetNumber(), pcbnew.ToMM(p.GetLocalClearance())))
                p.SetLocalClearance(None)
    return sorted(cleared)


if __name__ == '__main__':
    raise SystemExit(main())
