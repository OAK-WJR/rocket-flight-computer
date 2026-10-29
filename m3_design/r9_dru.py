#!/usr/bin/env python3
"""R8 -> R9 project design rules, m3.kicad_dru (M3-ASSY-R9, build step 2; r9_plan.md sections 1, 4; R9_DECISIONS.md
D-S1-01, D-S1-20, D-S2-*).

usage: python3 m3_design/r9_dru.py [project_dir] [--check]
The input is R8's m3.kicad_dru (commit 9c8179b, SHA-256 R8_SHA; m3_design/r9_build.sh restores it from git first);
a second run changes nothing, --check writes nothing and exits 1 unless the file is R9's. Four edits, nothing else:

1. P-1b (owner decision 2, R9_OWNER_DECISIONS.md item 2): rule G's condition `A.intersectsArea('PYRO_BLOCK')` becomes
   `(A.intersectsArea('PYRO_BLOCK') || !A.intersectsCourtyard('U1'))` (tools/check_r9.py G_SCOPE): the gate nets keep
   0.3 mm from every other live net everywhere outside U1's courtyard, not only inside PYRO_BLOCK. Stricter: the old
   scope is a subset of the new. The rule's name and every other byte of it stay (check_actuators PYRO_RULES).
2. LC-1 (D-S1-01): R8's pad overrides become rules. KiCad lets a pad's local clearance replace every custom rule for
   the pairs it is in, so R9 carries none (m3_design/r9_lib.clear_overrides) and the DRU carries their clearances:
   - "R9 RAW_ACT pins to foreign copper": every RAW_ACT through-hole pad 0.3 mm from all other copper (R8: 0.3 mm
     overrides on J124.2 and J122's RAW pins, which also switched off rules A, E and A2 there; tools/check_r7
     foreign_clearances already asks 0.3 mm of every RAW_ACT through-hole pad). It sits before the pyro rules, so every
     pyro rule (all >= 0.3 mm) still governs its own pairs, and after the RF rules, which name no RAW_ACT copper.
   - "R9 bare test pads to foreign copper": every test pad (TP*) 1.0 mm from all other copper (R8: a 1.0 mm override on
     each of the 24 test pads; check_r7 foreign_clearances asks the same). It is the last rule: 1.0 mm is at least
     every rule before it (rules E and H are 1.0, none is larger), so for a test pad it only raises a clearance, as
     the override did; tools/check_r9.py P-4 allows a rule after H only at >= 1.0 mm.
3. Comments that describe those rules.
4. Fill margins (build step 5, R9_DECISIONS D-S5-12; r9_plan.md section 2 done row Z1: every pyro rule's margin >=
   max(R8's, 0.2 mm)): a zone fill stops exactly at the clearance that governs it, so a pour beside armed, gate or
   sense copper meets its pyro rule with no margin (R8: rule D 0.001, rule A 0.001 mm). After rule A2, one rule per
   pyro rule A-G and A2, "R9 fill margin <X>", repeats rule X's condition for pairs with a zone and asks X's minimum
   plus FILL_MARGIN[X] (the Z1 floor + 0.05 mm for the filler's arc tolerance). Later in the file than X, it governs
   those pairs; zone pairs only, so no pad, track or via pair changes; before rule H, which names pads only (P-4).
   Stricter only: every zone pair keeps more than its pyro rule asked.
Pyro rules A-F, A2 and H, the RF rules and every other rule stay byte for byte (asserted); the result is pinned by
check_actuators.DRU_SHA and rule G by PYRO_RULE_SHA after review.
"""
import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE / 'assembly_review'
R8_SHA = '1674d58be79ae4282851206ab2578c17dd86f69d7f3da07e5355f3be3dbdf672'
RULE_G = 'Pyro G: gate nets in the pyro block'
OLD_SCOPE = "A.intersectsArea('PYRO_BLOCK')"
G_SCOPE = "(A.intersectsArea('PYRO_BLOCK') || !A.intersectsCourtyard('U1'))"
PYRO_ANCHOR = '# Pyro safety spacing (R6 single CH1;'
G_COMMENT_OLD = ('# Pass 3: D covers all GND copper, E guards the ARM break, F the bus/igniter/drain against every other\n'
                 '# live net, G the gate nets inside the PYRO_BLOCK rule area. No two of rules\n')
G_COMMENT_NEW = ('# Pass 3: D covers all GND copper, E guards the ARM break, F the bus/igniter/drain against every other\n'
                 '# live net, G the gate nets inside the PYRO_BLOCK rule area; R9 (P-1b) also everywhere outside U1\'s\n'
                 '# courtyard, so only the MCU pin\'s own escape is left to the board minimum. No two of rules\n')
RAW_RULE = (
    '# R9 (LC-1): no pad carries a local clearance (KiCad lets one replace every custom rule, pyro rules included, for the\n'
    '# pairs it is in). R8\'s 0.3 mm overrides on J124.2 and J122\'s RAW pins become this rule for every RAW_ACT\n'
    '# through-hole pad (hand-soldered; a bridge shorts the servo and pyro feed). It comes before the pyro rules, so each\n'
    '# of them (all >= 0.3 mm) still governs its own pairs; the RF rules above name no RAW_ACT copper.\n'
    '(rule "R9 RAW_ACT pins to foreign copper"\n'
    '  (condition "A.Type == \'Pad\' && A.Pad_Type == \'Through-hole\' && A.NetName == \'RAW_ACT\'")\n'
    '  (constraint clearance (min 0.3mm)))\n\n')
FILL_BASE = ('Pyro A: RAW_ACT to pyro control', 'Pyro B: bus, igniter and drain to gate',
             'Pyro C: bus, igniter and drain to sense', 'Pyro D: GND to bus, igniter and drain',
             'Pyro E: RAW_ACT to bus and igniter (ARM break)', 'Pyro F: bus, igniter and drain to other live nets',
             RULE_G, 'Pyro A2: RAW_ACT to RAW_ACT_SENSE')
# the Z1 floor (max(R8's margin, 0.2): R8 A .001 B .17 C .077 D .001 E .30 F .20 G .000; A2 none) + 0.05 mm
FILL_MARGIN = {'A': 0.25, 'B': 0.25, 'C': 0.25, 'D': 0.25, 'E': 0.35, 'F': 0.25, 'G': 0.25, 'A2': 0.25}
FILL_ANCHOR = '# Pass 13 (final CAD iteration): rule H comes last'
FILL_COMMENT = (
    '# R9 (build step 5): zone fills keep every pyro rule above plus a margin (r9_plan section 2, Z1: every margin >=\n'
    '# max(R8, 0.2 mm); + 0.05 mm for the filler\'s arc tolerance; E keeps R8\'s 0.30). A fill stops exactly at the\n'
    '# clearance that governs it, so without these a GND, RAW_ACT or power pour would meet its pyro rule with no margin\n'
    '# (R8: D 0.001, A 0.001 mm). Each repeats its rule\'s condition for pairs with a zone and comes after it, so it\n'
    '# governs those pairs only; no pad, track or via pair changes, and rule H (pads only) still comes last.\n')


def fill_rule(name, block):
    """The fill-margin rule for pyro rule `name` (its text `block`)."""
    key = name.split(':')[0].split()[1]
    cond = re.search(r'\(condition "(.*)"\)', block).group(1)
    mn = float(re.search(r'\(constraint clearance \(min ([\d.]+)mm\)\)', block).group(1))
    return (f'(rule "R9 fill margin {key}: {name.split(": ", 1)[1]}"\n'
            f'  (condition "(A.Type == \'Zone\' || B.Type == \'Zone\') && ({cond})")\n'
            f'  (constraint clearance (min {mn + FILL_MARGIN[key]:.2f}mm)))\n')


def fill_names():
    return [f'R9 fill margin {n.split(":")[0].split()[1]}: {n.split(": ", 1)[1]}' for n in FILL_BASE]


def fill_block(dru):
    """The comment and the fill-margin rules for the pyro rules of `dru` (R9's rule G included)."""
    return FILL_COMMENT + ''.join(fill_rule(n, rule_block(dru, n)) for n in FILL_BASE) + '\n'


def without_fill(r9):
    """r9 with the fill-margin block removed (the step-2 gate's fill-equivalence test isolates the LC-1 change)."""
    blk = fill_block(r9)
    assert r9.count(blk) == 1, 'the fill-margin block is not where transform puts it'
    return r9.replace(blk, '')


TP_RULE = (
    '\n# R9 (LC-1): R8\'s 1.0 mm overrides on the bare test pads become this rule. Bare copper is probed by hand, so every\n'
    '# test pad keeps 1.0 mm from all other copper (tools/check_r7 foreign_clearances measures the same). It is last: no\n'
    '# rule above asks more than 1.0 mm, so for a test pad it only raises a clearance, never lowers a pyro rule.\n'
    '(rule "R9 bare test pads to foreign copper"\n'
    '  (condition "A.Type == \'Pad\' && A.memberOfFootprint(\'TP*\')")\n'
    '  (constraint clearance (min 1.0mm)))\n')


def rule_block(dru, name):
    i = dru.find(f'(rule "{name}"')
    if i < 0:
        return None
    depth = 0
    for j in range(i, len(dru)):
        depth += {'(': 1, ')': -1}.get(dru[j], 0)
        if depth == 0:
            return dru[i:j + 1]
    return None


def rules(dru):
    return [(m.group(1), rule_block(dru, m.group(1))) for m in re.finditer(r'\(rule "([^"]+)"', dru)]


def transform(r8):
    """R9's m3.kicad_dru text from R8's."""
    assert hashlib.sha256(r8.encode()).hexdigest() == R8_SHA, 'input is not R8\'s m3.kicad_dru (restore it from 9c8179b)'
    g = rule_block(r8, RULE_G)
    assert g and g.count(OLD_SCOPE) == 1 and G_SCOPE not in g, 'rule G: unexpected R8 text'
    out = r8.replace(g, g.replace(OLD_SCOPE, G_SCOPE))
    assert out.count(G_COMMENT_OLD) == 1 and out.count(PYRO_ANCHOR) == 1
    out = out.replace(G_COMMENT_OLD, G_COMMENT_NEW).replace(PYRO_ANCHOR, RAW_RULE + PYRO_ANCHOR)
    assert out.count(FILL_ANCHOR) == 1
    out = out.replace(FILL_ANCHOR, fill_block(out) + FILL_ANCHOR)
    assert out.endswith(')\n')
    out += TP_RULE
    return out


def verify(r8, r9):
    """What separates r9 from transform(r8)'s intent: every R8 rule but G byte-identical and in R8's order, G the
    scope edit only, the two new rules where they belong."""
    issues = []
    a, b = rules(r8), rules(r9)
    names8, names9 = [n for n, _ in a], [n for n, _ in b]
    want = [n for n in names8]
    want.insert(want.index('Pyro A: RAW_ACT to pyro control'), 'R9 RAW_ACT pins to foreign copper')
    i = want.index('Pyro A2: RAW_ACT to RAW_ACT_SENSE') + 1
    want[i:i] = fill_names()
    want.append('R9 bare test pads to foreign copper')
    if names9 != want:
        issues.append(f'rule order {names9} != {want}')
    old = dict(a)
    for n, t in b:
        if n in fill_names():
            base = FILL_BASE[fill_names().index(n)]
            if t + '\n' != fill_rule(base, dict(b).get(base, '')):
                issues.append(f'rule "{n}" is not rule {base.split(":")[0]}\'s condition on zones with its fill margin')
            continue
        if n == RULE_G:
            if t != old[n].replace(OLD_SCOPE, G_SCOPE):
                issues.append('rule G differs from R8 beyond the P-1b scope')
        elif n in old and t != old[n]:
            issues.append(f'rule "{n}" differs from R8')
    if transform(r8) != r9:
        issues.append('m3.kicad_dru is not r9_dru.transform(R8)')
    return issues


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    project = Path(args[0]) if args else PROJECT
    path = project / 'm3.kicad_dru'
    now = path.read_text()
    if hashlib.sha256(now.encode()).hexdigest() == R8_SHA:
        r8 = now
    else:
        import subprocess
        r8 = subprocess.run(['git', '-C', str(HERE), 'show', '9c8179b:m3_design/assembly_review/m3.kicad_dru'],
                            check=True, capture_output=True, text=True).stdout
    r9 = transform(r8)
    issues = verify(r8, r9)
    if '--check' in sys.argv:
        if now != r9:
            issues.append(f'{path} is not R9\'s design rules: run m3_design/r9_dru.py')
    elif now != r9:
        path.write_text(r9)
        print('wrote', path.name)
    for i in issues:
        print('FAIL', i)
    print(f"r9_dru: {'OK' if not issues else 'FAIL'}; sha16 {hashlib.sha256(r9.encode()).hexdigest()[:16]}, rule G "
          f"sha16 {hashlib.sha256(rule_block(r9, RULE_G).encode()).hexdigest()[:16]}")
    return 1 if issues else 0


if __name__ == '__main__':
    raise SystemExit(main())
