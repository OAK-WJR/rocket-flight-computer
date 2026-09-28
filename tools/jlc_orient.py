#!/usr/bin/env python3
"""Derive JLCPCB placement corrections by matching our footprints to the LCSC/EasyEDA footprints.

JLC places every part with *its own* (EasyEDA) footprint. For each LCSC code we find the
rotation theta (0/90/180/270) and offset t that map our pad centres onto the EasyEDA pad
centres (pads matched by number), so that
    CPL rotation = our rotation - theta,  CPL position = our position - R(CPL rotation) . t
puts JLC's footprint exactly on our copper.

usage: tools/jlc_orient.py EASYEDA_PADS.json [board.kicad_pcb]  -> writes tools/jlc_corrections.json
EASYEDA_PADS.json: {"C20917": {"title": ..., "head": [x, y], "pads": ["PAD~RECT~x~y~w~h~layer~net~num~...", ...]}}
(fetched from https://easyeda.com/api/products/<code>/components). Runs under KiCad's python (pcbnew).
"""
import json, math, sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
EZ = json.load(open(sys.argv[1]))
BOARD = sys.argv[2] if len(sys.argv) > 2 else str(ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
MIL10 = 0.254
TOL = 0.35    # mm, max pad-centre residual (land sizes differ between libraries, centres move a little)
MARGIN = 0.4  # mm, the next-best rotation must be worse by at least this much (orientation is unambiguous)
# pads compared by number; a footprint that merges pads (AON7524 drain fingers + paddle = pad 5) compares its distinct pins only
ONLY = {'M3_AON7524_DFN3x3A': ['1', '2', '3', '4']}
# both origins are the package centre (EasyEDA pins at +-1.5 mm; ours: drain fingers centred at -1.5, source lands
# pulled in to +1.4 per AOS PO-00047), so the one-row fit's 0.1 mm is land shape, not an origin shift
OFFSET = {'M3_AON7524_DFN3x3A': (0.0, 0.0)}


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
        if not p.GetNumber(): continue
        r = p.GetFPRelativePosition(); ours.setdefault(p.GetNumber(), []).append((mm(r.x), mm(r.y)))
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
    ok = full and ((worst <= TOL and second - worst >= MARGIN) or (len(common) == 2 and worst <= 0.6 and second - worst >= 2.0))
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
json.dump(dict(source='easyeda.com/api/products/<LCSC>/components, matched by pad number', tolerance_mm=TOL,
               parts=dict(sorted(result.items()))), open(out, 'w'), indent=1)
for k, v in sorted(result.items(), key=lambda kv: (kv[1]['status'], kv[0])):
    print(k.split('|')[0].ljust(11), v['status'].ljust(5), f"theta {v['theta']:>3}", f"off {v['offset'][0]:+.3f},{v['offset'][1]:+.3f}",
          f"res {v['residual_mm']:.3f}/{v.get('next_best_mm', 0):.2f}", f"pads {v['pads_ours']}/{v['pads_easyeda']}/{v['pads_matched']}", v['footprint'], '|', v['easyeda'])
print('CHECK:', problems or 'none')
