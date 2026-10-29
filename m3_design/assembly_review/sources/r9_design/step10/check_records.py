#!/usr/bin/env python3
"""R9 step 10's records check (R9_DECISIONS D-S10-13): the R9 records against their evidence.

usage: python3 check_records.py [--out FILE]          (plain python3, no KiCad; run from anywhere)

  binding       every file in step10_evidence/ (dc/ and gate/ included) names the board's SHA-256 on its first line or
                in a board_sha256 field, and that SHA-256 is the board's on disk (m3_design/assembly_review/m3.kicad_pcb)
  provenance    the scripts and inputs the evidence hashes are the files on disk: requalify_r9.json (its script and
                every input), tab_plan.json and ordering_facts.json (their scripts), gate/r9.json and gate/fit.json
                (their checkers and inputs), r9_binding_note.json (netlist and pin table)
  placeholders  no double-brace (or @@ / __NAME__ drafting) placeholder in any record (RECORDS, the progress log included)
  citations     every backticked evidence path in the cited records resolves to at least one existing file (brace
                lists and * expanded; bases in BASES); a JSON file followed directly by backticked key names holds each
                key (at any depth)
  requal        every row of R9_VALIDATION's requalification tables cites at least one existing evidence file
  figures       every claim of claims(): the record states exactly what its evidence file gives
exit 0 = every check holds. The report lists each check and every failure.
"""
import argparse
import glob
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[5]
R9D = ROOT / 'm3_design/assembly_review/sources/r9_design'
EV = R9D / 'step10_evidence'
BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
BASES = [ROOT, ROOT / 'docs', R9D, EV, EV / 'dc', EV / 'gate', R9D / 'step10', R9D / 'step9_evidence', ROOT / 'm3_design/assembly_review',
         ROOT / 'm3_design/assembly_review/fab', ROOT / 'm3_design/assembly_review/sources', ROOT / 'm3_design',
         ROOT / 'tools', ROOT / 'm3_design/assembly_review/sources/r8_design',
         ROOT / 'm3_design/assembly_review/sources/r7_review']
EXTS = ('.json', '.txt', '.md', '.py', '.sh', '.tsv', '.csv', '.diff', '.png', '.pdf', '.zip', '.xml',
        '.kicad_pcb', '.kicad_dru', '.kicad_sch', '.kicad_pro', '.kicad_mod')


def r9_section(text):
    """STATUS.md: the R9 section only (the older sections cite their own revisions' files)."""
    m = re.search(r'^## Current candidate: M3-ASSY-R9.*?(?=^## )', text, re.S | re.M)
    return m.group(0) if m else ''


def step10_block(text):
    """R9_DECISIONS.md: the step-10 block."""
    i = text.find('## Step 10')
    return text[i:] if i >= 0 else ''


# record -> part of it whose citations are checked (None: placeholders only)
RECORDS = {
    'docs/R9_VALIDATION.md': lambda t: t,
    'docs/M3_R9.md': lambda t: t,
    'docs/ORDERING.md': lambda t: t,
    'docs/REQUIREMENTS.md': lambda t: t,
    'STATUS.md': r9_section,
    'AGENTS.md': None,
    'README.md': None,
    'm3_design/assembly_review/sources/r9_design/R9_DECISIONS.md': step10_block,
    'm3_design/assembly_review/sources/r9_design/r9_step10_handoff.md': lambda t: t,
    'm3_design/assembly_review/sources/r9_design/r9_step10_progress.md': None,
}


def braces(s):
    m = re.search(r'\{([^{}]*)\}', s)
    if not m:
        return [s]
    return [x for alt in m.group(1).split(',') for x in braces(s[:m.start()] + alt + s[m.end():])]


def resolve(token):
    """Existing files a cited path names (empty when none)."""
    found = []
    for variant in braces(token):
        for base in BASES:
            hits = glob.glob(str(base / variant)) if '*' in variant else ([str(base / variant)]
                                                                       if (base / variant).exists() else [])
            if hits:
                found.extend(hits)
                break
    return found


def is_path(tok):
    if any(c in tok for c in ' <>') or '://' in tok or tok.startswith(('-', '.')):
        return False
    return '/' in tok or tok.endswith(EXTS) or re.search(r'\.\{[a-z,]+\}$', tok) is not None


def json_keys(obj, acc=None):
    acc = set() if acc is None else acc
    if isinstance(obj, dict):
        for k, v in obj.items():
            acc.add(k)
            json_keys(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            json_keys(v, acc)
    return acc


def check_citations(name, text, fails):
    n_paths = n_keys = 0
    toks = list(re.finditer(r'`([^`\n]+)`', text))
    current, prev_end = None, None
    for m in toks:
        tok = m.group(1).strip()
        sep = text[prev_end:m.start()] if prev_end is not None else None
        prev_end = m.end()
        if is_path(tok):
            n_paths += 1
            hits = resolve(tok)
            if not hits:
                fails.append(f'citations: {name}: `{tok}` names no existing file')
                current = None
                continue
            js = [h for h in hits if h.endswith('.json')]
            current = js if js and len(hits) == len(js) else None
            continue
        joined = sep is not None and re.fullmatch(r'[\s,;]*(and\s+)?', sep) is not None
        if current and joined and re.fullmatch(r'[A-Za-z_][\w.\- ]*', tok):
            n_keys += 1
            if not any(tok in json_keys(json.loads(Path(h).read_text())) for h in current):
                fails.append(f'citations: {name}: key `{tok}` not in {", ".join(Path(h).name for h in current)}')
            continue
        current = None
    return n_paths, n_keys


def check_requal(fails):
    text = (ROOT / 'docs/R9_VALIDATION.md').read_text()
    i, j = text.find('## Requalification on the final board'), text.find('## R9 deviations for owner acceptance')
    rows = 0
    for line in text[i:j].splitlines():
        if not line.startswith('| ') or line.startswith('| Item ') or set(line) <= set('|- '):
            continue
        rows += 1
        cell = line.rstrip(' |').split(' | ')[-1]
        cited = [t for t in re.findall(r'`([^`]+)`', cell) if is_path(t) and resolve(t)]
        if not cited:
            fails.append(f'requal: row "{line[2:60]}..." cites no existing evidence file')
    return rows


def board_sha():
    return hashlib.sha256(BOARD.read_bytes()).hexdigest()


def check_binding(sha, fails):
    n = 0
    for p in sorted(EV.rglob('*')):
        if not p.is_file() or p.name.startswith('.'):
            continue
        n += 1
        text = p.read_text(errors='replace')
        ok = False
        if text.lstrip().startswith('{'):              # a JSON report (plate.txt is plate_model's JSON on stdout)
            try:
                d = json.loads(text)
                ok = isinstance(d, dict) and d.get('board_sha256') == sha
            except ValueError:
                pass
        if not ok:
            ok = sha in (text.splitlines() or [''])[0]
        if not ok:
            fails.append(f'binding: {p.relative_to(R9D)} does not name the board SHA-256 {sha[:12]}...')
    return n


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check_provenance(fails):
    n = 0
    ar, r8d = ROOT / 'm3_design/assembly_review', ROOT / 'm3_design/assembly_review/sources/r8_design'

    def want(label, path, digest):
        nonlocal n
        n += 1
        if not Path(path).is_file():
            fails.append(f'provenance: {label}: {path} missing')
        elif sha_file(path) != digest:
            fails.append(f'provenance: {label}: {Path(path).name} changed since the evidence was made')

    q = json.loads((EV / 'requalify_r9.json').read_text())
    want('requalify_r9.json script', R9D / 'step10/requalify_r9.py', q['script_sha256'])
    for rel, digest in q['inputs_sha256'].items():
        want('requalify_r9.json input', ROOT / rel, digest)
    for f, s in (('tab_plan.json', 'tab_plan_r9.py'), ('ordering_facts.json', 'ordering_facts_r9.py')):
        want(f'{f} script', R9D / 'step10' / s, json.loads((EV / f).read_text())['script_sha256'])
    for f, checker in (('gate/r9.json', 'tools/check_r9.py'), ('gate/fit.json', 'tools/fit_check.py')):
        d = json.loads((EV / f).read_text())
        want(f'{f} checker', ROOT / checker, d['checker_sha256'])
        for rel, digest in d['inputs_sha256'].items():
            want(f'{f} input', ar / rel if (ar / rel).exists() else r8d / rel, digest)
    b = json.loads((EV / 'r9_binding_note.json').read_text())
    want('r9_binding_note.json netlist', ar / 'schematic.net.xml', b['netlist_sha256'])
    want('r9_binding_note.json pin table', r8d / 'pin_table.tsv', b['pin_table_sha256'])
    return n


# ---- evidence readers -------------------------------------------------------------------------------------------
def J(rel):
    return json.loads((R9D / rel).read_text() if (R9D / rel).exists() else (ROOT / rel).read_text())


def DC(rel):
    t = (R9D / rel).read_text()
    d = {'r': float(re.search(r'R = ([0-9.]+) mOhm', t).group(1))}
    m = re.search(r'neck ([0-9.]+) mm at level [0-9.]+ on (\S+)', t)
    if m:
        d['neck'], d['layer'] = float(m.group(1)), m.group(2)
    m = re.search(r'rises ([0-9.]+) C', t)
    if m:
        d['rise'] = float(m.group(1))
    d['vias'] = [float(x) for x in re.findall(r'([0-9.]+) A at \(', t)]
    m = re.search(r'vias over 0\.5 A: (\d+); over 1\.0 A: (\d+)', t)
    if m:
        d['over05'], d['over1'] = int(m.group(1)), int(m.group(2))
    return d


def minus(v, f='{:.1f}'):
    s = f.format(abs(v))
    return ('−' if v < 0 else '') + s


def claims():
    """(record, [texts the record must state], evidence) for each claim; texts are built from the evidence."""
    q, r9 = J('step10_evidence/requalify_r9.json'), J('step10_evidence/gate/r9.json')['rules']
    plate, fit = J('step10_evidence/gate/plate.json'), J('step10_evidence/gate/fit.json')
    # the 0.05 mm 7.7 A solves: step 9's until review pass 1's fix pass changed the copper, then step10_evidence/dc/ (D-F1-12)
    raw, bat, fet = (DC(f'step10_evidence/dc/dc005_{n}.txt') for n in ('raw', 'bat', 'fet'))
    R9V, M3, ORD, REQ, ST = 'docs/R9_VALIDATION.md', 'docs/M3_R9.md', 'docs/ORDERING.md', 'docs/REQUIREMENTS.md', 'STATUS.md'
    out = []

    def add(rec, texts, ev):
        out.append((rec, [texts] if isinstance(texts, str) else texts, ev))

    # 7.7 A copper (step 9's 0.05 mm solves on the same board)
    add(R9V, [f'RAW_ACT {raw["r"]:.2f} mΩ, neck {raw["neck"]:.2f} mm on {raw["layer"]}, {raw["rise"]:.1f} °C',
              f'BAT_IN {bat["r"]:.2f} mΩ, {bat["neck"]:.2f} mm {bat["layer"]}, {bat["rise"]:.1f} °C',
              f'ACT_FET_S {fet["r"]:.2f} mΩ, {fet["neck"]:.2f} mm {fet["layer"]}, {fet["rise"]:.1f} °C',
              f'RAW_ACT {raw["vias"][0]:.2f} A, BAT_IN {bat["vias"][0]:.2f} A ({bat["over05"]} vias over 0.5 A',
              f'ACT_FET_S {fet["vias"][0]:.2f} A'], 'step10_evidence/dc/dc005_{raw,bat,fet}.txt')
    for rec in (M3, REQ):
        add(rec, [f'RAW_ACT {raw["r"]:.2f} mΩ, neck {raw["neck"]:.2f} mm on {raw["layer"]}, {raw["rise"]:.1f} °C',
                  f'ACT_FET_S {fet["r"]:.2f} mΩ, {fet["neck"]:.2f} mm'], 'step10_evidence/dc/dc005_{raw,fet}.txt')
    add(ST, f'RAW_ACT {raw["r"]:.2f}, BAT_IN {bat["r"]:.2f}, ACT_FET_S {fet["r"]:.2f} mΩ', 'step10_evidence/dc/dc005_*.txt')
    # step 10's DC solves
    dc = {n: DC(f'step10_evidence/dc/{n}.txt') for n in ('fire_raw', 'fire_bus', 'fire_ign', 'fire_out', 'fire_gnd',
                                                         'gnd_servo', 'bat_u9', 'usb', 'rp_u7', 'rp_u11', 'cam_j9',
                                                         'vl_u2', 'raw_r177', 'raw_j124')}
    fl = (EV / 'dc/fire_loop.txt').read_text()
    copper = float(re.search(r'([0-9.]+) mOhm  board copper', fl).group(1))
    total = float(re.search(r'([0-9.]+) mOhm  board total', fl).group(1))
    amps = float(re.search(r'with the board: .* = ([0-9.]+) A', fl).group(1))
    seg = f'RAW_ACT → J124.2 {dc["fire_raw"]["r"]:.2f} mΩ, bus {dc["fire_bus"]["r"]:.2f}, igniter {dc["fire_ign"]["r"]:.2f}, drain {dc["fire_out"]["r"]:.2f} mΩ'
    for rec in (R9V, M3):
        add(rec, [seg, f'{copper:.1f} mΩ of copper', f'{total:.1f} mΩ', f'{amps:.2f} A'], 'step10_evidence/dc/fire_*.txt, fire_loop.txt')
    add(REQ, [f'{total:.1f} mΩ', f'{amps:.2f} A'], 'step10_evidence/dc/fire_loop.txt')
    add(R9V, [f'servo return {dc["gnd_servo"]["r"]:.2f} mΩ', f'fire-loop return {dc["fire_gnd"]["r"]:.2f} mΩ'],
        'step10_evidence/dc/{gnd_servo,fire_gnd}.txt')
    add(REQ, f'servo GND return {dc["gnd_servo"]["r"]:.2f} mΩ', 'step10_evidence/dc/gnd_servo.txt')
    add(R9V, [f'BAT_IN J1:1 → U9:5 {dc["bat_u9"]["r"]:.2f} mΩ', f'USB_LIMITED U10:6 → U11:7 {dc["usb"]["r"]:.2f} mΩ',
              f'RAW_PROTECTED U9:6 → U7 {dc["rp_u7"]["r"]:.2f} mΩ'], 'step10_evidence/dc/{bat_u9,usb,rp_u7}.txt')
    # pyro (requalify_r9.json, the gate's own functions)
    pm = q['pyro.margins']['evidence']['rules']
    add(R9V, [f'A {pm["A"]["closest"]["mm"]:g} mm (margin {pm["A"]["margin"]:g};'] +
        [f'{k} {pm[k]["closest"]["mm"]:g} ({pm[k]["margin"]:g};' for k in 'BCDGH'] +
        [f'H+ {pm["H+"]["closest"]["mm"]:g} mm (margin {pm["H+"]["margin"]:g} over 1.2)',
         f'GS {pm["GS"]["closest"]["mm"]:g} mm ({pm["GS"]["margin"]:g};',
         f'AG {pm["AG"]["closest"]["mm"]:g} mm ({pm["AG"]["margin"]:g};'], 'step10_evidence/requalify_r9.json pyro.margins')
    add(M3, [f'A {pm["A"]["margin"]:g}, B {pm["B"]["margin"]:g}, C {pm["C"]["margin"]:g}, D {pm["D"]["margin"]:g}, '
             f'H {pm["H"]["margin"]:g} mm, G {pm["G"]["margin"]:g}'], 'requalify_r9.json pyro.margins')
    br = q['pyro.bridges']['evidence']
    add(R9V, f'{br["pairs"]} exposed pairs under 1.5 mm, {br["forbidden"]} forbidden', 'requalify_r9.json pyro.bridges')
    bv = q['pyro.block_vias']
    add(R9V, f'{bv["count"]}; nearest armed copper {bv["nearest"]["armed"]["mm"]:g} mm', 'requalify_r9.json pyro.block_vias')
    fb = q['pyro.fire_bars']['track_mm']
    add(R9V, [f'GATE_N {fb["PYRO1_GATE_N"]:g} mm, CONT {fb["PYRO1_CONT"]:g} mm, ARM1_SENSE {fb["ARM1_SENSE"]:.1f} mm',
              f'(Z2r9 {q["pyro.fire_bars"]["exit_track_mm"]:.1f} mm)'], 'requalify_r9.json pyro.fire_bars')
    tp = q['pyro.tp122']['at']
    add(R9V, f'bottom, ({tp[0]:g}, {tp[1]:g}); no via in its pad', 'requalify_r9.json pyro.tp122')
    rh = q['pyro.rule_h']['evidence']
    words = {3: 'three', 8: 'eight'}
    add(R9V, f'{words[len(rh["pairs"])]} closest pairs ({", ".join(p.replace(" -- ", "–") for p in rh["pairs"])}) × '
             f'{words[len(rh["variants"])]} variants', 'requalify_r9.json pyro.rule_h')
    # RF
    g = q['rf.gcpw']['evidence']
    add(R9V, [f'{g["samples"]} line samples (GNSS {g["by_chain"]["GNSS"]}, radio {g["by_chain"]["RADIO"]})',
              f'Z0 {g["z0_range_ohm"][0]:.2f}–{g["z0_range_ohm"][1]:.2f} Ω'], 'requalify_r9.json rf.gcpw')
    add(R9V, f'XOR {q["rf.launch"]["evidence"]["J30"]["gnd_xor_r7_mm2"]:.1f} mm²', 'requalify_r9.json rf.launch')
    rl = q['rf.return_loss']['chains']
    for chain, label in (('GNSS', 'GNSS |S11| '), ('RADIO', 'radio ')):
        b = rl[chain]['bands'].values()
        s = [x['s11'] for x in b]
        d = [x['rl_db'] for x in b]
        add(R9V, f'{label}{min(s):.3f}–{max(s):.3f}, RL {min(d):.1f}–{max(d):.1f} dB', 'requalify_r9.json rf.return_loss')
    r7 = r9['R-7']['evidence']
    add(R9V, [f'GNSS east {r7["GNSS_east_largest_gap_mm"]:g} / west {r7["GNSS_west_largest_gap_mm"]:g} mm, radio west '
              f'{r7["RADIO_west_largest_gap_mm"]:g} / east {r7["RADIO_east_largest_gap_mm"]:g} mm',
              f'fence of {r7["fence"]["fence_vias"]} vias on y {r7["fence"]["row_y"]:g}'], 'gate/r9.json R-7')
    n10 = r9['R-10']['evidence']['nearest_part']
    add(R9V, f'{n10[0]:g} mm ({n10[1]}–{n10[2]})', 'gate/r9.json R-10')
    n13 = r9['R-13']['evidence']['nearest']
    add(R9V, f'{n13[0]:g} mm ({n13[1]} to {n13[2].split()[0]})', 'gate/r9.json R-13')
    x9c = r9['K-power-pyro']['evidence']['inner_power_pyro']['nearest']
    add(R9V, f'{x9c[0]:g} mm (In2 RAW_ACT to {x9c[2].split()[0]})', 'gate/r9.json K-power-pyro')
    # mechanical
    j = plate['f1']['jacks_only']
    add(R9V, [f'f1 {j["pinned_D5"]:g} Hz pinned, {j["pinned_D10"]:g} / {j["clamped_D5"]:g} / {j["clamped_D10"]:g} Hz',
              f'{plate["f1"]["plugs_on_jacks"]["pinned_D5"]:g} Hz pinned if the plugs hang on the jacks'], 'gate/plate.json')
    add(M3, f'f1 {j["pinned_D5"]:g} Hz', 'gate/plate.json')
    add(ST, f'f1 {j["pinned_D5"]:g} Hz', 'gate/plate.json')
    add(R9V, [f'worst J9 mated {fit["rows"][0][0]:.3f} mm',
              f'supports {fit["nearest_support"][0]:.3f} mm bottom ({fit["nearest_support"][1]}) / '
              f'{fit["nearest_top_support"][0]:.3f} mm top ({fit["nearest_top_support"][1].split()[0]})'], 'gate/fit.json')
    tab = J('step10_evidence/tab_plan.json')['chosen']
    ty = {k: v['kicad_y'] for k, v in tab.items()}
    add(R9V, f'west y {ty["west aft"][0]:g}–{ty["west aft"][1]:g} and {ty["west forward"][0]:g}–{ty["west forward"][1]:g}, '
             f'east {ty["east aft"][0]:g}–{ty["east aft"][1]:g} and {ty["east forward"][0]:g}–{ty["east forward"][1]:g}',
        'tab_plan.json chosen')
    mid = J('step10_evidence/tab_plan.json')['middle_third']['west']['max_pyro_block_mm']
    add(ORD, f'lies within {mid:g} mm of the CH1 pyro column', 'tab_plan.json middle_third')
    imu = q['imu']
    add(R9V, [f'U4 on the bottom at ({imu["at"][0]:.1f}, {imu["at"][1]:.1f}), rotation {imu["rot"]:g}',
              f'lever arm x {minus(imu["lever_arm_x_mm"])} mm'], 'requalify_r9.json imu')
    f9 = r9['F9-1']['evidence']
    prot = [v for k, v in f9.items() if k != 'U9']
    add(R9V, f'input protection {min(prot):.2f}–{max(prot):.2f} mm from J1.1 (≤ 10.6), U9 {f9["U9"]:.2f} mm', 'gate/r9.json F9-1')
    hp = J('step10_evidence/hotplug_feed.json')
    near = hp['by_feed_nH'][f'{hp["feed_estimate_nH"]:g}']
    add(R9V, [f'R_b {hp["rb_mohm"]:.2f} mΩ (dc_solve)', f'feed about {hp["feed_estimate_nH"]:.2f} nH',
              f'within {near["extra_negative_V"]:g} V and × {near["slew_ratio"]:.3f} slew'], 'hotplug_feed.json')
    add(R9V, f'R_b {dc["bat_u9"]["r"]:.2f} mΩ', 'step10_evidence/dc/bat_u9.txt')
    ra, rx = J('step10_evidence/reference_audit.json'), J('step10_evidence/reference_audit_ext.json')
    add(R9V, [f'{ra["unreferenced"]:,} / {ra["samples"]:,} samples unreferenced ({100 * ra["unreferenced_share"]:.2f} %)',
              f'{rx["unreferenced"]:,} / {rx["samples"]:,} ({100 * rx["unreferenced_share"]:.2f} %)'],
        'reference_audit*.json')
    # ordering facts, fab
    mp = q['mech.parts']
    add(ORD, [f'Top: {mp["top"]} parts', f'plus {mp["top_tp"]} test pads', f'bottom: {mp["bottom"]} SMD parts and {mp["bottom_tp"]} test pads'],
        'requalify_r9.json mech.parts')
    vb = J('step10_evidence/ordering_facts.json')['vias_in_bare_contacts']
    if vb:
        add(ORD, [f'the {v["net"]} via at ({v["via"][0]:g}, {v["via"][1]:g}) inside {v["pad"]}' for v in vb],
            'ordering_facts.json vias_in_bare_contacts')
    else:
        add(ORD, 'no via opens into a bare contact', 'ordering_facts.json vias_in_bare_contacts')
    cost = J('m3_design/assembly_review/fab/cost_check.json')
    for rec in (R9V, M3, REQ, ST):
        add(rec, f'${cost["total_usd_per_board"]:.2f} per board', 'fab/cost_check.json')
    add(R9V, f'{len(cost["extended_codes"])} extended codes', 'fab/cost_check.json extended_codes')
    bn = J('step10_evidence/r9_binding_note.json')
    if '0 pins differ' in bn['u1_map']:
        add(R9V, "U1's map equals R8's pin table (0 pins changed", 'r9_binding_note.json u1_map')
    else:
        add(R9V, 'r9_binding_note.json u1_map says 0 pins differ', 'r9_binding_note.json u1_map')
    sw = J('step10_evidence/m2_sweep.json')
    add(R9V, [f'chain detours on nets without a pour {len(sw["chain_detour"])}',
              f'{len(sw["adjacency"])} track / via pairs under 0.2 mm, {len(sw["adjacency_pad"])} pad-to-copper pairs',
              f'routes with ratio ≥ 1.25 or extra vias: {len(sw["routes"])} nets',
              f'short hops {len(sw["short_hop"])}',
              f'| Via steps, poured hops, via folds | via_step, poured_hop, via_fold | {len(sw["via_step"])} / '
              f'{len(sw["poured_hop"])} / {len(sw["via_fold"])} (C6, C7) |'], 'm2_sweep.json')
    rt = J('step10_evidence/gate/route.json')
    add(R9V, [f'### A. `route_check` allowlist: none (`step10_evidence/gate/route.json`: allowed {len(rt["allowed"])}, stale {len(rt["stale"])})',
              f'### B. Non-critical leftovers: none (`gate/route.json`: leftovers {len(rt["leftovers"])}, missing '
              f'{len(rt["leftovers_missing"])}, stale {len(rt["leftovers_stale"])})'], 'gate/route.json')
    d = J('step10_evidence/gate/drc.json')
    add(R9V, f'DRC {len(d["violations"])} at every severity, unconnected {len(d["unconnected_items"])}, parity '
             f'{len(d["schematic_parity"])}', 'gate/drc.json')
    return out


def norm(t):
    return re.sub(r'\s+', ' ', t.replace('**', '').replace('\\|', '|'))


def check_figures(fails):
    n = 0
    texts = {}
    for rec, wants, ev in claims():
        if rec not in texts:
            raw = (ROOT / rec).read_text()
            texts[rec] = norm(r9_section(raw) if rec == 'STATUS.md' else raw)
        for w in wants:
            n += 1
            if norm(w) not in texts[rec]:
                fails.append(f'figures: {rec} does not state "{w}" ({ev})')
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    sha = board_sha()
    lines = [f'# m3_design/assembly_review/m3.kicad_pcb sha256 {sha} (step10/check_records.py; R9_DECISIONS D-S10-13)']
    fails = []
    n = check_binding(sha, fails)
    lines.append(f'binding: {n} evidence files in step10_evidence/')
    try:
        lines.append(f'provenance: {check_provenance(fails)} hashed scripts and inputs equal to the files on disk')
    except (OSError, KeyError, ValueError) as e:
        fails.append(f'provenance: unreadable: {type(e).__name__}: {e}')
    missing = [rec for rec in RECORDS if not (ROOT / rec).is_file()]
    fails += [f'records: {rec} missing' for rec in missing]
    for rec in RECORDS:
        if rec in missing:
            continue
        t = (ROOT / rec).read_text()
        hits = [i + 1 for i, line in enumerate(t.splitlines()) if re.search(r'\{\{|@@|__[A-Z]+__', line)]
        if hits:
            fails.append(f'placeholders: {rec} lines {hits}')
    lines.append(f'placeholders: {len(RECORDS) - len(missing)} records scanned')
    for rec, part in RECORDS.items():
        if part is None or rec in missing:
            continue
        p, k = check_citations(rec, part((ROOT / rec).read_text()), fails)
        lines.append(f'citations: {rec}: {p} paths, {k} JSON keys')
    lines.append(f'requal: {check_requal(fails)} requalification rows')
    try:
        lines.append(f'figures: {check_figures(fails)} stated figures compared with their evidence')
    except (OSError, KeyError, AttributeError, ValueError, IndexError) as e:
        fails.append(f'figures: evidence unreadable: {type(e).__name__}: {e}')
    lines += [f'FAIL {f}' for f in fails]
    lines.append(f'records check: {"OK" if not fails else f"{len(fails)} failures"}')
    text = '\n'.join(lines) + '\n'
    if a.out:
        a.out.write_text(text)
    print(text, end='')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
