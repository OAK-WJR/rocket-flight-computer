#!/usr/bin/env python3
"""R12 reverse hot-plug model (stage D, D-R12-09 / -78 / -79, O-R12-08): R10's distributed model (tools/r10_hotplug.py
and its C solver, both unedited) run on R12's own BAT_IN / BAT_DAMP copper and four-layer stack-up.

What differs from R10. Everything else (the 2304 required corners, the limits, the nonlinear solver, the maker C(V)
curves, the convergence, sensitivity, no-clamp, retained-output and C88-topology checks) is R10's code.
  * Stack-up: R12 is four layers (F / In1 GND / In2 3V3 + islands / B, D-R12-22), so R10's own four-layer extractor
    (r10_hotplug.extract with tools/dc_solve.stackup) runs on it: R12's BAT_IN and BAT_DAMP copper is F.Cu track only
    (no pour; the extractor refuses one). Microstrip references as R10: 'near' = In1 or In2, 'gnd' = In1.
  * Parts (R12_DECISIONS D-R12-09, -17): D8 is SMAJ12CA/TR13 (C78399, 400 W) in place of SMBJ12CA (600 W): the same
    12 V standoff, VBR 13.3-14.7 V and 19.9 V clamp class, so R10's soft-knee TVS model and its VBR corners are kept
    (Inference: the model's 0.2 ohm asymptotic slope is stiffer than the SMAJ12CA's (19.9 - 14.7) V / 20.1 A = 0.26 ohm;
    the no-clamp control and the --no-clamp-all run bound the result without any clamp). R167 is the 0402 10k (C25744).
    U9 is TPS259470ARPWR (C3662799): the A variant shares the L variant's EC table and pin-out (TI SLVSFC9C device
    table; only the fault response, auto-retry vs latch-off, differs), so the OUT net role check accepts it.
    C80 / C96 / C89 / C95 / C88 / R166 / R92 are R10's codes. R12's discharge inventory adds C1538 (4.7 nF 0402 X7R, C81)
    and C1549 (18 pF C0G, C25 / C26), each by its datasheet nominal.
  * C79 (D-R12-78): a third damper capacitor, CL31A226KAHNNNE 22 uF (C12891), BAT_IN to BAT_DAMP beside C89 / C95,
    with their maker C(V) curve, tolerance / temperature factors and 'damper' corner. R10's model hard-codes two damper
    capacitors (REFS, the extract keep set, the capacitor incidence rows, the scale vector, the initial BAT_DAMP nodes,
    the legacy linear run's capacitor list, and the C solver's CMAX and curve types). As tools/jlc_orient_r11.py and
    tools/export_fab_r11.py do, this wrapper reads R10's sources, applies PY_REPLACE / C_REPLACE (each asserted to occur
    exactly as counted, so an upstream edit fails here instead of being skipped) and executes the Python as module
    'r10_hotplug_r12'; the patched C source is written into the run's temporary build directory and compiled there.
    model_sha covers both R10 sources, this file and the capacitor curves. MODEL_PARTS gains C79 = C89's identity.
  * Pad joins: R10's extractor joins track ends only through the pads of its named parts (REFS) and capacitors. On R12
    the R167 bleed branch reaches the feed through R80's BAT_IN pad (two tracks end in it), so the extractor here adds
    every part with a BAT_IN or BAT_DAMP pad (R80, R82, TP80, ...) to REFS: their pads are ideal copper joins, as R10's
    named pads are. Branches that end in such a pad are dead ends and R10's pruning removes them.
  * Variants (D-R12-09, evidence for the keep-or-drop decision; not gate runs): --variant r166_shorted runs the 2304
    required cases with R166 replaced by 1 mOhm (the damper capacitors straight to GND); --variant no_damper with C89 /
    C95 / C79 removed (capacitance scaled to 1e-6 of nominal); --no-clamp-all removes D8 (VBR 1000 V) in every case;
    --rdamp-scale K scales R166 in every corner and --damper-scale K scales every damper capacitor (C89 / C95 / C79).
  * The inputs and results are R12's files in m3_design/r12/design/.

usage: <KiCad python3> -I tools/r12_hotplug.py --extract FILLED_BOARD.kicad_pcb [--inputs OUT.json]     (pcbnew)
       <python3 with numpy> -I tools/r12_hotplug.py [--inputs IN.json] [--output OUT.json]            (simulation)
       <python3 with numpy> -I tools/r12_hotplug.py --variant as_built|r166_shorted|no_damper [--no-clamp-all]
                                                   [--rdamp-scale K] [--damper-scale K] --output OUT.json
Simulation needs a C compiler (cc), as R10's.
"""
import json
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SOURCE = HERE / 'r10_hotplug.py'
SOLVER_SOURCE = HERE / 'r10_hotplug_solver.c'
NL = '\n'
# (old, new, count): R10's two damper capacitors become three (C89, C95, C79; D-R12-78).
PY_REPLACE = (
    ("REFS = ('J1', 'D8', 'C80', 'C96', 'C89', 'C95', 'C88',",
     "REFS = ('J1', 'D8', 'C80', 'C96', 'C89', 'C95', 'C79', 'C88',", 1),
    ("keep = {terminals[k] for k in ('J1.1', 'D8.1', 'C80.1', 'C96.1', 'C89.1', 'C89.2'," + NL,
     "keep = {terminals[k] for k in ('J1.1', 'D8.1', 'C80.1', 'C96.1', 'C89.1', 'C89.2', 'C79.1', 'C79.2'," + NL, 1),
    ('E = np.zeros((m, n)); CE = np.zeros((6, n))', 'E = np.zeros((m, n)); CE = np.zeros((7, n))', 1),
    ("('C95.1', 'C95.2'), ('C88.1', None))):", "('C95.1', 'C95.2'), ('C79.1', 'C79.2'), ('C88.1', None))):", 1),
    ("CE[5, index[pins['U9.5']]] = 1", "CE[6, index[pins['U9.5']]] = 1", 1),
    ("[factors[1][corner['damper']] * 22e-6] * 2 +", "[factors[1][corner['damper']] * 22e-6] * 3 +", 1),
    ("for pin in ('C89.2', 'C95.2', 'R166.1'):", "for pin in ('C89.2', 'C95.2', 'C79.2', 'R166.1'):", 2),
    ("('C95.1', 'C95.2', 8.35, 22.), ('C88.1', None, 0., 0.)]",
     "('C95.1', 'C95.2', 8.35, 22.), ('C79.1', 'C79.2', 8.35, 22.), ('C88.1', None, 0., 0.)]", 1),
    ("str(SOLVER), '-o', str(library)]", "str(_r12_solver(tmp)), '-o', str(library)]", 1),
)
C_REPLACE = (
    ('#define CMAX 6', '#define CMAX 7', 1),
    ('const int types[CMAX] = {0, 0, 1, 1, 2, 3};', 'const int types[CMAX] = {0, 0, 1, 1, 1, 2, 3};', 1),
)


def _patched(path, table):
    text = path.read_text()
    for old, new, count in table:
        if text.count(old) != count:
            raise SystemExit(f'r12_hotplug: {path.name} no longer has {count} x {old!r}')
        text = text.replace(old, new)
    return text


def _r12_solver(tmp):
    out = Path(tmp) / 'r12_hotplug_solver.c'
    out.write_text(_patched(SOLVER_SOURCE, C_REPLACE))
    return out


def _load():
    mod = types.ModuleType('r10_hotplug_r12')
    mod.__file__ = str(SOURCE)
    mod._r12_solver = _r12_solver
    sys.modules['r10_hotplug_r12'] = mod
    exec(compile(_patched(SOURCE, PY_REPLACE), str(SOURCE), 'exec'), mod.__dict__)
    return mod


base = _load()
ROOT = HERE.parent
DESIGN = ROOT / 'm3_design/r12/design'
MODEL_PARTS = dict(base.MODEL_PARTS, C79=base.MODEL_PARTS['C89'],
                   D8=('SMAJ12CA', 'C78399', 'SMAJ12CA/TR13', ('BAT_IN', 'GND')),
                   R167=('10k 1%', 'C25744', '0402WGF1002TCE', ('BAT_IN', 'GND')))
DISCHARGE_PARTS = dict(base.DISCHARGE_PARTS, **{'0402B472K500NT': (.0047, 'C1538'),
                                                '0402CG180J500NT': (.000018, 'C1549')})
U9_PARTS = ('TPS259470ARPWR',)
_ORIGINAL_COMPONENT_ISSUES = base.component_issues


def model_sha():
    return base.digest([base.file_sha(p) for p in (SOURCE, Path(__file__), SOLVER_SOURCE, base.CAPACITORS)])


def component_issues(inputs):
    """R10's check with R12's U9 part number: R10's function names TPS259470LRPWR; the A variant is accepted on the same
    land, pin-out and OUT net role (D-R12-09). Any other U9 still fails."""
    u9 = inputs.get('parts', {}).get('U9', {})
    if u9.get('fields', {}).get('Manufacturer Part') in U9_PARTS:
        patched = json.loads(json.dumps(inputs))
        patched['parts']['U9']['fields']['Manufacturer Part'] = 'TPS259470LRPWR'
        return _ORIGINAL_COMPONENT_ISSUES(patched)
    return _ORIGINAL_COMPONENT_ISSUES(inputs) + ['U9 is not an R12 part (TPS259470ARPWR)']


_ORIGINAL_EXTRACT = base.extract
_REFS = base.REFS


def extract(board, board_path):
    """R10's extract with every part that has a BAT_IN / BAT_DAMP pad joining copper (see the module docstring)."""
    extra = sorted({f.GetReference() for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() in base.NETS}
                   - set(_REFS))
    base.REFS = tuple(_REFS) + tuple(extra)
    try:
        return _ORIGINAL_EXTRACT(board, board_path)
    finally:
        base.REFS = _REFS


def install():
    base.extract = extract
    base.DESIGN = DESIGN
    base.INPUTS = DESIGN / 'hotplug_inputs_r12.json'
    base.RESULTS = DESIGN / 'hotplug_results_r12.json'
    base.MODEL_PARTS = MODEL_PARTS
    base.DISCHARGE_PARTS = DISCHARGE_PARTS
    base.model_sha = model_sha
    base.component_issues = component_issues


def variant(name, no_clamp, inputs_path, output_path, rdamp_scale=1.0, damper_scale=1.0):
    """The 2304 required corners with the named damper change; failures by R10's assess (D-R12-09 evidence)."""
    inputs = json.loads(Path(inputs_path).read_text())
    corners = [dict(c, rdamp_ohm=round(c['rdamp_ohm'] * rdamp_scale, 10)) for c in base.cases()]
    if damper_scale != 1.0:
        scaled = base.curves

        def curves():
            ns, xs, cs, qs, factors = scaled()
            factors = [dict(f) for f in factors]
            factors[1] = dict(factors[1], low=factors[1]['low'] * damper_scale, high=factors[1]['high'] * damper_scale)
            return ns, xs, cs, qs, factors
        base.curves = curves
    if name == 'r166_shorted':
        corners = [dict(c, rdamp_ohm=.001) for c in corners]
    elif name == 'no_damper':
        original = base.curves

        def curves():
            ns, xs, cs, qs, factors = original()
            factors = [dict(f) for f in factors]
            factors[1] = dict(factors[1], low=factors[1]['low'] * 1e-6, high=factors[1]['high'] * 1e-6,
                              basis='C89 / C95 removed (variant): capacitance x 1e-6')
            return ns, xs, cs, qs, factors
        base.curves = curves
    elif name != 'as_built':
        raise SystemExit(f'unknown variant {name}')
    if no_clamp:
        corners = [dict(c, vbr_V=1000.) for c in corners]
    rows = base.run_nonlinear(inputs, corners)
    failures = base.assess(rows)
    failed = {f['case'] for f in failures}
    worst = {k: (min if k == 'minimum_V' else max)(rows, key=lambda r: r[k]) for k in base.LIMITS}
    by_lh = {}
    for i, r in enumerate(rows):
        b = by_lh.setdefault(f"{r['corner']['lh_uH']:g}", dict(cases=0, failing=0, minimum_V=1e9, falling_V_per_us=0.))
        b['cases'] += 1
        b['failing'] += i in failed
        b['minimum_V'] = min(b['minimum_V'], r['minimum_V'])
        b['falling_V_per_us'] = max(b['falling_V_per_us'], r['falling_V_per_us'])
    out = dict(variant=name, no_clamp_all=no_clamp, rdamp_scale=rdamp_scale, damper_scale=damper_scale,
               inputs_sha256=base.digest(inputs), model_sha256=model_sha(),
               limits=base.LIMITS, cases=len(rows), failing_cases=len(failed),
               failing_by_metric={k: sum(1 for f in failures if f['metric'] == k) for k in base.LIMITS},
               worst={k: dict(value=v[k], corner=v['corner']) for k, v in worst.items()},
               damper_peak_W=max(r['damper_peak_W'] for r in rows),
               damper_energy_J=max(r['damper_energy_J'] for r in rows), by_harness_uH=by_lh,
               label='Simulation / Inference (R10 model, corners and limits; a variant run, not gate evidence)')
    Path(output_path).write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    print(json.dumps({k: out[k] for k in ('variant', 'no_clamp_all', 'rdamp_scale', 'damper_scale', 'cases',
                                          'failing_cases', 'failing_by_metric')}))
    print(json.dumps({k: round(v['value'], 4) for k, v in out['worst'].items()}))
    return 0


if __name__ == '__main__':
    install()
    if any(a in sys.argv for a in ('--variant', '--no-clamp-all', '--rdamp-scale', '--damper-scale')):
        import argparse
        ap = argparse.ArgumentParser()
        ap.add_argument('--variant', default='as_built')
        ap.add_argument('--no-clamp-all', action='store_true')
        ap.add_argument('--inputs', default=str(base.INPUTS))
        ap.add_argument('--rdamp-scale', type=float, default=1.0)
        ap.add_argument('--damper-scale', type=float, default=1.0)
        ap.add_argument('--output', required=True)
        a = ap.parse_args()
        raise SystemExit(variant(a.variant, a.no_clamp_all, a.inputs, a.output, a.rdamp_scale, a.damper_scale))
    sys.argv[0] = __file__
    raise SystemExit(base.main())
