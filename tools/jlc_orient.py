#!/usr/bin/env python3
"""Derive JLCPCB placement corrections by matching our footprints to the LCSC/EasyEDA footprints.

JLC places every part with *its own* (EasyEDA) footprint. For each LCSC code we find the
rotation theta (0/90/180/270) and offset t that map our pad centres onto the EasyEDA pad
centres (pads matched by number), so that
    CPL rotation = our rotation - theta,  CPL position = our position - R(CPL rotation) . t
puts JLC's footprint exactly on our copper.

usage: tools/jlc_orient.py EASYEDA_PADS.json [board.kicad_pcb]  -> writes tools/jlc_corrections.json
       tools/jlc_orient.py EASYEDA_PADS.json [board.kicad_pcb] --verify-cpl fab/m3_cpl_jlc.csv
(the second form rebuilds every placed part's pads from the CPL row and JLC's footprint and compares them with our pads)

Bottom side (R5): KiCad keeps a flipped footprint's pads mirrored in local y (and its orientation turned 180 deg), so
the match uses the un-mirrored pads; theta and t are then properties of the footprint, the same for either side.
JLC's bottom-side rotation is read as seen from below with the board turned over left to right, positive
counter-clockwise (Inference: KiBot's JLCPCB preset, rot_footprint mirror_bottom, checked by its authors against
JLC in November 2023; JLC's help pages do not define it). Then for a bottom part
    CPL rotation = 180 - our rotation - theta,  CPL position = our position - R(180 - CPL rotation) . (tx, -ty)
(tools/export_fab.py). Confirm the bottom side in JLC's placement preview before ordering.
EASYEDA_PADS.json: {"C20917": {"title": ..., "head": [x, y], "pads": ["PAD~RECT~x~y~w~h~layer~net~num~...", ...]}}
(fetched from https://easyeda.com/api/products/<code>/components). Runs under KiCad's python (pcbnew).
"""
import json, math, sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
ARGV = [a for a in sys.argv[1:]]
VERIFY = ARGV[ARGV.index('--verify-cpl') + 1] if '--verify-cpl' in ARGV else None
if VERIFY:
    del ARGV[ARGV.index('--verify-cpl'):ARGV.index('--verify-cpl') + 2]
EZ = json.load(open(ARGV[0]))
BOARD = ARGV[1] if len(ARGV) > 1 else str(ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
MIL10 = 0.254
TOL = 0.35    # mm, max pad-centre residual (land sizes differ between libraries, centres move a little)
MARGIN = 0.4  # mm, the next-best rotation must be worse by at least this much (orientation is unambiguous)
# pads compared by number; a footprint that merges pads (AON7524 drain fingers + paddle = pad 5) compares its distinct pins only
ONLY = {'M3_AON7524_DFN3x3A': ['1', '2', '3', '4']}
# both origins are the package centre (EasyEDA pins at +-1.5 mm; ours: drain fingers centred at -1.5, source lands
# pulled in to +1.4 per AOS PO-00047), so the one-row fit's 0.1 mm is land shape, not an origin shift
OFFSET = {'M3_AON7524_DFN3x3A': (0.0, 0.0)}
# Body correction for parts whose pin row is symmetric but whose body is not, so pad matching cannot see a
# 180 deg turn. DORABO DB128V (C2915641): EasyEDA's footprint puts the wire entry on its +y side (body
# -5.00/+5.20 mm, 3D model turned 180 deg; the DORABO drawing agrees: pin row 5.00 mm from the BACK face).
# Our footprints put the entry on local -y, toward the board edge. +180 makes JLC fit J1/J9 entry-out;
# JLC's pin 1 then lands on our pin 4, which a screw terminal does not care about.
BODY = {'C2915641': 180}
# JST mechanical solder tabs have no KiCad electrical number; supplier libraries
# number them. Match these tabs as well as signals to verify the connector body.
MECHANICAL = {'M3_SH_BM04B_SRSS_TB': ('0', '0'),
              'M3_SH_BM07B_SRSS_TB': ('9', '8'),
              'M3_GH_BM04B_GHS_TBT': ('5', '6')}
# MLT-5020 maker drawing (sources/mlt5020.pdf p4): 1.5 x0.8 mm
# terminations, general +/-0.3 mm tolerance. Our 2.3 x1.7 mm lands at
# x=+/-1.85 cover toe/heel and tolerance; EasyEDA's narrower lands are at
# +/-2.30. Body origins and pin polarity agree; retain the 0.45 mm land
# centre difference explicitly rather than moving the component body.
PAD_TOLERANCE = {'M3_MLT5020_3pad': 0.451}


def placement_pad_number(pad, footprint):
    number = pad.GetNumber()
    if not number and footprint in MECHANICAL:
        number = MECHANICAL[footprint][pad.GetFPRelativePosition().x > 0]
    return number


def rot(v, deg):
    """Rotate a vector the way KiCad rotates footprint content (y axis down, positive = CCW on screen)."""
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return (v[0] * c + v[1] * s, -v[0] * s + v[1] * c)


def ez_pads(rec):
    hx, hy = rec['head']
    out = {}
    for p in rec['pads']:
        f = p.split('~')
        x, y, num = float(f[2]), float(f[3]), f[8]
        out.setdefault(num, []).append(((x - hx) * MIL10, (y - hy) * MIL10))
    return out


b = pcbnew.LoadBoard(BOARD)
mm = pcbnew.ToMM
# calibrate the rotation sign on a real rotated footprint
for f in b.GetFootprints():
    if f.GetOrientationDegrees() % 180 and len(f.Pads()) > 1:
        p = f.Pads()[0]; rel = p.GetFPRelativePosition(); ab = p.GetPosition(); o = f.GetPosition()
        want = (mm(ab.x - o.x), mm(ab.y - o.y)); got = rot((mm(rel.x), mm(rel.y)), f.GetOrientationDegrees())
        assert abs(want[0] - got[0]) < 1e-3 and abs(want[1] - got[1]) < 1e-3, (f.GetReference(), want, got)
        break

if VERIFY:
    import csv
    from collections import Counter
    worst_all, bad, n_top, n_bot, skipped = 0.0, [], 0, 0, []
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    excluded = pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_DNP
    expected = {ref for ref, f in fps.items() if ref and not ref.startswith('#')
                and f.GetAttributes() & (pcbnew.FP_SMD | pcbnew.FP_THROUGH_HOLE)
                and not f.GetAttributes() & excluded}
    with open(VERIFY, newline='') as source:
        reader = csv.DictReader(source)
        if len(reader.fieldnames or []) != 5 or set(reader.fieldnames or []) != {'Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'}:
            sys.exit('CPL check: invalid column headers')
        rows = list(reader)
    counts = Counter(row['Designator'] for row in rows)
    missing = sorted(expected - counts.keys())
    extra = sorted(counts.keys() - expected)
    duplicates = sorted(ref for ref, count in counts.items() if count != 1)
    if missing or extra or duplicates:
        sys.exit(f'CPL check: missing {missing}; unexpected {extra}; duplicate {duplicates}')
    corrections = json.loads((ROOT / 'tools/jlc_corrections.json').read_text())['parts']
    for row in rows:
        f = fps[row['Designator']]
        lcsc = f.GetField('LCSC').GetText() if f.HasField('LCSC') else ''
        ref = f.GetReference()
        try:
            if not row['Mid X'].endswith('mm') or not row['Mid Y'].endswith('mm'):
                raise ValueError('coordinates must be in mm')
            cx, cy = float(row['Mid X'][:-2]), -float(row['Mid Y'][:-2])
            r_ = float(row['Rotation'])
            if not all(math.isfinite(v) for v in (cx, cy, r_)):
                raise ValueError('non-finite placement')
            if row['Layer'] != ('Bottom' if f.IsFlipped() else 'Top'):
                raise ValueError('wrong assembly side')
            key = f"{lcsc}|{f.GetFPID().GetLibItemName().wx_str()}"
            correction = corrections.get(key)
            if not correction or correction['status'] != 'OK':
                raise ValueError('no reviewed orientation correction')
            theta = correction['theta']
            tx, ty = correction['offset']
            angle = f.GetOrientationDegrees()
            if f.IsFlipped():
                angle = 180 - angle - theta
                dx, dy = rot((tx, -ty), 180 - angle)
            else:
                angle -= theta
                dx, dy = rot((tx, ty), angle)
            position = f.GetPosition()
            if math.hypot(cx - (mm(position.x) - dx), cy - (mm(position.y) - dy)) > 0.00015:
                raise ValueError('position differs from board and reviewed correction')
            if abs((r_ - angle + 180) % 360 - 180) > 0.01:
                raise ValueError('rotation differs from board and reviewed correction')
        except (ValueError, TypeError, KeyError) as error:
            bad.append((ref, str(error)))
            continue
        if lcsc not in EZ or 'pads' not in EZ[lcsc] or lcsc in BODY:
            skipped.append(ref)        # inventory, side and corrected placement checked above; no independent pad match
            continue
        ez = ez_pads(EZ[lcsc])
        bottom = row['Layer'] == 'Bottom'
        worst = 0.0
        only = ONLY.get(f.GetFPID().GetLibItemName().wx_str())   # as the generator: the pads it matched on
        fpname = f.GetFPID().GetLibItemName().wx_str()
        visible = {placement_pad_number(p, fpname) for p in f.Pads() if placement_pad_number(p, fpname)
                   and (p.IsOnLayer(pcbnew.F_Mask) or p.IsOnLayer(pcbnew.B_Mask))}
        wanted = set(only) if only else visible
        if not wanted or not wanted <= visible or not wanted <= ez.keys() or (not only and wanted != ez.keys()):
            bad.append((ref, 'incomplete independent pad coverage'))
            continue
        npads = len({placement_pad_number(p, fpname) for p in f.Pads() if placement_pad_number(p, fpname) in ez})
        for p in f.Pads():
            n = placement_pad_number(p, fpname)
            if not n or n not in ez or not (p.IsOnLayer(pcbnew.F_Mask) or p.IsOnLayer(pcbnew.B_Mask)):
                continue
            if only and n not in only:
                continue
            ab = (mm(p.GetPosition().x), mm(p.GetPosition().y))
            preds = []
            for e in ez[n]:
                # JLC's footprint at the CPL row: top, turned r; bottom, seen from below (board turned left to
                # right), turned r there, i.e. mirrored in x and turned -r on the top view
                q = rot((-e[0], e[1]), -r_) if bottom else rot(e, r_)
                preds.append((cx + q[0], cy + q[1]))
            worst = max(worst, min(math.hypot(ab[0] - q[0], ab[1] - q[1]) for q in preds))
        n_bot += bottom
        n_top += not bottom
        worst_all = max(worst_all, worst)
        tolerance = PAD_TOLERANCE.get(fpname, 0.6 if npads == 2 else TOL)
        if worst > tolerance + 1e-4:  # supplier coordinate rounding: <=0.1 um
            bad.append((row['Designator'], round(worst, 3)))
    print(f'CPL check: {n_top} top and {n_bot} bottom rows rebuilt from JLC footprints; worst pad residual '
          f'{worst_all:.3f} mm; errors: {bad or "none"}; '
          f'placement-only checks: {len(skipped)} ({" ".join(skipped)}); expected rows: {len(expected)}')
    sys.exit(1 if bad else 0)

result, problems = {}, []
done = {}
for f in b.GetFootprints():
    lcsc = f.GetField('LCSC').GetText() if f.HasField('LCSC') else ''
    if not lcsc or lcsc not in EZ or 'pads' not in EZ[lcsc]: continue
    fpname = f.GetFPID().GetLibItemName().wx_str()
    key = (lcsc, fpname)
    if key in done: continue
    ours = {}
    for p in f.Pads():
        # paste-only apertures (no number) and copper-only tabs under the mask (no opening) carry no lead
        number = placement_pad_number(p, fpname)
        if not number or not (p.IsOnLayer(pcbnew.F_Mask) or p.IsOnLayer(pcbnew.B_Mask)): continue
        r = p.GetFPRelativePosition()
        # a flipped footprint keeps its pads mirrored in local y: un-mirror to the library footprint
        ours.setdefault(number, []).append((mm(r.x), -mm(r.y) if f.IsFlipped() else mm(r.y)))
    ez = ez_pads(EZ[lcsc])
    common = sorted(set(ours) & set(ez))
    if fpname in ONLY: common = [n for n in common if n in ONLY[fpname]]
    best = None; tried = []
    for th in (0, 90, 180, 270):
        # translation from the centroid of matched pads
        A = [q for n in common for q in [rot(v, th) for v in ours[n]]]
        B = [q for n in common for q in ez[n]]
        if not A or not B: continue
        # bounding-box centre of the matched pad centres: unlike the mean it is not pulled by the pad count per side
        ta = ((min(x for x, _ in A) + max(x for x, _ in A)) / 2, (min(y for _, y in A) + max(y for _, y in A)) / 2)
        tb = ((min(x for x, _ in B) + max(x for x, _ in B)) / 2, (min(y for _, y in B) + max(y for _, y in B)) / 2)
        t = (tb[0] - ta[0], tb[1] - ta[1])
        worst = 0.0
        for n in common:
            for v in ours[n]:
                w = rot(v, th); w = (w[0] + t[0], w[1] + t[1])
                worst = max(worst, min(math.hypot(w[0] - e[0], w[1] - e[1]) for e in ez[n]))
        tried.append(worst)
        if best is None or worst < best[0]: best = (worst, th, t)
    worst, th, t = best
    if fpname in OFFSET: t = OFFSET[fpname]
    second = sorted(tried)[1] if len(tried) > 1 else 99
    rec = dict(footprint=fpname, easyeda=EZ[lcsc].get('title'), easyeda_proxy=EZ[lcsc].get('proxy'), theta=th, offset=[round(t[0], 4), round(t[1], 4)],
               residual_mm=round(worst, 3), next_best_mm=round(second, 3), pads_ours=len(ours), pads_easyeda=len(ez), pads_matched=len(common))
    full = len(common) == len(ours) == len(ez) or (fpname in ONLY and len(common) == len(ONLY[fpname]))
    # two-pad parts: the lands may differ a lot (e.g. a vendor land pulled inward), the axis cannot
    tolerance = PAD_TOLERANCE.get(fpname, TOL)
    ok = full and ((worst <= tolerance + 1e-4 and second - worst >= MARGIN) or (len(common) == 2 and worst <= 0.6 and second - worst >= 2.0))
    if fpname in PAD_TOLERANCE:
        rec['land_center_tolerance_mm'] = tolerance
        rec['land_pattern_source'] = 'sources/mlt5020.pdf p4; maker-derived enlarged lands, unchanged body centre'
    if lcsc in BODY:
        assert abs(t[0]) < 1e-6 and abs(t[1]) < 1e-6, (lcsc, t)    # centred symmetric row: offset unaffected
        rec['theta'] = (th + BODY[lcsc]) % 360
        rec['body_correction_deg'] = BODY[lcsc]
    rec['status'] = 'OK' if ok else 'CHECK'
    if not ok: problems.append(f'{lcsc}|{fpname}')
    result[f'{lcsc}|{fpname}'] = rec; done[key] = 1
for f in b.GetFootprints():
    lcsc = f.GetField('LCSC').GetText() if f.HasField('LCSC') else ''
    fpname = f.GetFPID().GetLibItemName().wx_str()
    if lcsc and f'{lcsc}|{fpname}' not in result and lcsc in EZ and 'pads' not in EZ[lcsc]:
        donor = next((k for k, v in result.items() if v['footprint'] == fpname and v['status'] == 'OK'), None)
        if donor:
            result[f'{lcsc}|{fpname}'] = dict(result[donor], via=f'same footprint as {donor.split("|")[0]} (EasyEDA has no entry for {lcsc})')
out = ROOT / 'tools/jlc_corrections.json'
json.dump(dict(source='JLCEDA/EasyEDA Official Library; public product-to-component mapping; matched by pad number and reviewed mechanical tab identities',
               source_urls=['https://lceda.cn/', 'https://easyeda.com/'], tolerance_mm=TOL,
               parts=dict(sorted(result.items()))), open(out, 'w'), indent=1)
for k, v in sorted(result.items(), key=lambda kv: (kv[1]['status'], kv[0])):
    print(k.split('|')[0].ljust(11), v['status'].ljust(5), f"theta {v['theta']:>3}", f"off {v['offset'][0]:+.3f},{v['offset'][1]:+.3f}",
          f"res {v['residual_mm']:.3f}/{v.get('next_best_mm', 0):.2f}", f"pads {v['pads_ours']}/{v['pads_easyeda']}/{v['pads_matched']}", v['footprint'], '|', v['easyeda'])
print('CHECK:', problems or 'none')
sys.exit(1 if problems else 0)
