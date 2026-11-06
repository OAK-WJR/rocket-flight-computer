#!/usr/bin/env python3
"""R12 native-CAD contract: R10/R11 safety rules on the one-sided, four-layer R12 board.

usage: <KiCad python3> -I -B tools/check_r12.py [board.kicad_pcb] [--report out.json] [--fit FIT.json]
       [--stage placement|copper|full] [--only S-1,M-3] [--bom BOM.csv] [--cpl CPL.csv]
       [--advisory K-reference,K-region,K-plane]
exit 0 = every selected fatal rule holds; no pending ports remain.
--advisory (D-R12-67A, stage C pass 1): the named rules still run and their findings are printed and reported
(report 'advisory'), but they do not fail the run. Only the signal-reference families in ADVISABLE may be named;
the safety (S-), sensor (M-), wiring (W-) and clearance (LC-) rules, and every other rule, are always fatal.

L-1 / M-1: four layers, 1.6 mm, rectangular 46 x <= 100 mm outline (D-R12-03 / -24).
F-1 / M-6: every part on F; bottom assembly is prohibited (D-R12-01).
N-1: native parts and identities match the R12 schematic; revision M3-ASSY-R12.
V-1 / V-2: through vias 0.3 / >= 0.45 mm; no via in a soldered pad (D-R12-03 / -07).
S-1 / S-2: RAW_ACT behind Q120/Q121 only; no unnamed armed-side parts or copper bypass.
S-3: every pyro/load-switch gate defined off; local gate-source bias joined on the FET's layer.
S-4: fitted population, schematic flags, MPN values and optional BOM/CPL identities; J1 excluded,
     every other part JLC-assembled, none owner-fitted (J121 / LS120 THT, C84 SMT; D-R12-04..19 / -29 / -30 / -85).
S-5: protected J400 contacts, 470k resistors, D402 clamp and no switch bypass.
S-6 / S-7: external ports separated from safety copper; servo signals and GND only, sixth pin NC.
S-8: barrel wall AND retained inner ring >= 1 mm from foreign In1/In2 copper, including In2 signals;
     GND counts on ACT_GATE, ACT_DRV and PYRO1_OUT (D-R12-34, inherited R10 hazard policy).
S-9: actual fire-path copper >= 0.5 mm; battery feed >= 1 mm; no inherited narrow-track exceptions.
W-1 / W-2: plated J1 wire pads, J121 DB125 and SH port pin maps including NC contacts (D-R12-29..31).
LC-1: local clearance >= 0.15 mm, SWD >= 0.508 mm and probes >= 1 mm (D-R12-03).
M-3 / M-5: recorded M3 supports and corner support; optional fit report bound to the board.
M-7: recorded top IMU pose; no via/fill under sensor bodies, no track inside any sensor pad ring (D-R12-52).
M-8: courtyard short-edge clearance >= 2.5 mm except exact R12 recorded edge queries.
K-legends: R10's identity, mask, designator and Fab checks with R12 revision and connector pin words;
           no R11 optional-legend exemptions (D-R12-29..31); only J122's harness note may be absent (D-R12-81).
K-copper: via/pad, overlap joints, thermals, paste and pour debris; no VIPPO exemption (D-R12-07).
K-inner: In1 GND only; In2 mixed rail/signal copper, fast interfaces excluded (D-R12-34).
K-reference / K-region: F over In1 GND; In2 over In1 and B GND; B over In2 rail fill, each B chain over one rail.
K-plane: In2 power fills one piece or two >= 0.5 mm outer links; neck checks retained.
K-fill: saved fill geometry agrees with native refill of a copy.
K-rules: DRU text and project floors agree with the R12 generator; no unconditional rule after a scoped one (D-R12-88).
K-neighbours: every ball round PE4 / PC1 is NC, GND, the D-R11-23 3V3 pair or an inert net whose one-bridge gate voltage,
              computed from the board's own resistors, stays <= 0.45 V (D-R11-85, D-R12-86).

Placement remains the stage-B gate. Copper checks safety/routing; full also checks the final legends (stage D).
R12 pin lookup uses its pin table and net names; no U4/U5 pad numbers or R10 layout coordinates are inherited.
"""
import argparse
import csv
import re
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r10 as r10
import check_r11 as r11
REVISION = 'M3-ASSY-R12'
R12_DIR = ROOT / 'm3_design/r12'
R12_MAX_LENGTH = 100.0
WIDTH = 46.0
VIA_DRILL, VIA_DIAMETER = 0.3, 0.45
PENDING = ()
IMPLEMENTED = ('S-1', 'S-2', 'S-3', 'S-4', 'S-5', 'S-6', 'S-7', 'S-8', 'S-9', 'W-1', 'W-2', 'LC-1',
               'M-3', 'M-6', 'M-7', 'M-8', 'K-legends', 'K-copper', 'K-inner', 'K-reference', 'K-region', 'K-plane', 'K-fill',
               'K-neighbours')
STAGES = {'placement': ('L-1', 'M-1', 'F-1', 'N-1', 'K-rules', 'M-5', 'K-neighbours'),
          'copper': ('L-1', 'M-1', 'F-1', 'N-1', 'K-rules', 'M-5', 'V-1', 'V-2')
                    + tuple(r for r in IMPLEMENTED if r != 'K-legends')}
STAGES['full'] = STAGES['copper'] + ('K-legends',) + PENDING
TITLES = {'L-1': 'four copper layers, 1.6 mm', 'M-1': f'outline 46 x <= {R12_MAX_LENGTH:g} mm from (0, 0)',
          'F-1': 'one assembled side (no flipped footprint, no bottom SMD pad)', 'N-1': 'parts equal the R12 schematic',
          'V-1': 'through vias 0.3 / >= 0.45 mm only', 'V-2': 'no via in a soldered SMD pad',
          'K-rules': 'DRU and project floors are the generator\'s', 'M-5': 'fit_check --profile r12 clean, bound'}


def mm(v):
    import pcbnew
    return pcbnew.ToMM(v)


def l1(ctx):
    import pcbnew
    b = ctx['board']
    out = []
    if b.GetCopperLayerCount() != 4:
        out.append(f'{b.GetCopperLayerCount()} copper layers; R12 is a four-layer board (D-R12-03)')
    if abs(mm(b.GetDesignSettings().GetBoardThickness()) - 1.6) > 0.01:
        out.append('board thickness is not 1.6 mm')
    return out


def outline(board):
    import pcbnew
    xs, ys, other = [], [], []
    for d in board.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        if d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            continue
        if d.GetShape() == pcbnew.SHAPE_T_RECT:
            for p in (d.GetStart(), d.GetEnd()):
                xs.append(mm(p.x))
                ys.append(mm(p.y))
        elif d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            for p in (d.GetStart(), d.GetEnd()):
                xs.append(mm(p.x))
                ys.append(mm(p.y))
        else:
            other.append(d.GetShapeStr())
    return xs, ys, other


def m1(ctx):
    xs, ys, other = outline(ctx['board'])
    out = [f'Edge.Cuts shape {s} (one rectangle expected)' for s in other]
    if not xs:
        return out + ['no Edge.Cuts outline']
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    if abs(x0) > 1e-3 or abs(y0) > 1e-3:
        out.append(f'outline starts at ({x0:g}, {y0:g}), not (0, 0)')
    if abs(x1 - x0 - WIDTH) > 0.01:
        out.append(f'board width {x1 - x0:g} mm, must be {WIDTH:g} mm (P1)')
    if y1 - y0 > R12_MAX_LENGTH + 0.01:
        out.append(f'board length {y1 - y0:g} mm exceeds {R12_MAX_LENGTH:g} mm (the JLC 4-layer price step)')
    return out


def f1(ctx):
    import pcbnew
    out = []
    for f in ctx['board'].GetFootprints():
        if f.IsFlipped():
            out.append(f'{f.GetReference()} is on the bottom side (R12 assembles one side, D-R12-01)')
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l) for l in (pcbnew.B_Cu, pcbnew.B_Paste)):
                out.append(f'{f.GetReference()}.{p.GetNumber() or "(unnumbered)"}: SMD pad on the bottom side')
    return out


def n1(ctx):
    import r12_sch
    board, out = ctx['board'], []
    if board.GetTitleBlock().GetRevision() != REVISION:
        out.append(f'title-block revision {board.GetTitleBlock().GetRevision()!r}, expected {REVISION}')
    parts, _ = r12_sch.read_netlist(ctx['netlist'])
    fps = {f.GetReference(): f for f in board.GetFootprints() if not f.GetReference().startswith(('H', 'TH', 'FID'))}
    for ref in sorted(set(parts) - set(fps)):
        out.append(f'{ref}: in the schematic, not on the board')
    for ref in sorted(set(fps) - set(parts)):
        out.append(f'{ref}: on the board, not in the schematic')
    for ref in sorted(set(parts) & set(fps)):
        f, p = fps[ref], parts[ref]
        if str(f.GetFPID().GetLibItemName()) != p['footprint'].split(':')[1]:
            out.append(f'{ref}: footprint {f.GetFPID().GetLibItemName()}, schematic {p["footprint"]}')
        for key in ('LCSC', 'Manufacturer', 'Manufacturer Part'):
            got = f.GetField(key).GetText() if f.HasField(key) else ''
            if got != p['fields'].get(key, ''):
                out.append(f'{ref}: {key} {got!r}, schematic {p["fields"].get(key, "")!r}')
    return out


def v1(ctx):
    import pcbnew
    out = []
    for t in ctx['board'].GetTracks():
        if t.GetClass() != 'PCB_VIA':
            continue
        xy = f'({mm(t.GetPosition().x):g}, {mm(t.GetPosition().y):g})'
        if t.GetViaType() != pcbnew.VIATYPE_THROUGH:
            out.append(f'via at {xy}: not a through via')
        if abs(mm(t.GetDrillValue()) - VIA_DRILL) > 1e-4:
            out.append(f'via at {xy}: drill {mm(t.GetDrillValue()):g} mm, R12 uses {VIA_DRILL:g} mm only')
        if mm(t.GetWidth(pcbnew.F_Cu)) < VIA_DIAMETER - 1e-4:
            out.append(f'via at {xy}: diameter {mm(t.GetWidth(pcbnew.F_Cu)):g} mm < {VIA_DIAMETER:g} mm')
    return out


def v2(ctx):
    import pcbnew
    out = []
    pads = [(f.GetReference(), p) for f in ctx['board'].GetFootprints() for p in f.Pads()
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.IsOnLayer(pcbnew.F_Cu)]
    for t in ctx['board'].GetTracks():
        if t.GetClass() != 'PCB_VIA':
            continue
        r = t.GetDrillValue() // 2
        for ref, p in pads:
            shape = p.GetEffectivePolygon(pcbnew.F_Cu)
            if shape.Collide(t.GetPosition(), r):
                out.append(f'via at ({mm(t.GetPosition().x):g}, {mm(t.GetPosition().y):g}) in {ref}.{p.GetNumber()}')
    return out


def dru_order(text):
    """D-R12-88 (R12F1-TRI-11): KiCad applies the last matching custom rule, so an unconditional rule written after a
    scoped (condition or layer) rule with the same constraint type replaces it for every item: the scoped rule is dead.
    Refuse that order in the DRU itself, whatever the generator says."""
    import r12_sch
    out, scoped = [], {}
    for m in re.finditer(r'\(rule "([^"]+)"', text):
        body = text[m.start():r12_sch.sch.close_paren(text, m.start())]
        kinds = set(re.findall(r'\(constraint (\w+)', body))
        if r12_sch.dru_conditional(body):
            for k in kinds:
                scoped.setdefault(k, m.group(1))
        else:
            for k in sorted(kinds & set(scoped)):
                out.append(f'unconditional rule "{m.group(1)}" ({k}) follows the scoped rule "{scoped[k]}", which it '
                           'overrides (KiCad applies the last matching rule): put unconditional floors first')
    return out


def k_rules(ctx):
    import r12_sch
    out = []
    dru = ctx['path'].with_suffix('.kicad_dru')
    want = r12_sch.dru((r12_sch.INPUT / 'm3.kicad_dru').read_text())
    if not dru.exists() or dru.read_text() != want:
        out.append('m3.kicad_dru differs from r12_sch.dru() (regenerate with m3_design/r12_sch.py)')
    if dru.exists():
        out += dru_order(dru.read_text())
    pro = ctx['path'].with_suffix('.kicad_pro')
    if pro.exists():
        rules = json.loads(pro.read_text())['board']['design_settings']['rules']
        floor = r12_sch.R12_FLOOR
        for key, value in (('min_clearance', floor['clearance']), ('min_track_width', floor['track_width']),
                           ('min_via_diameter', floor['via_diameter']), ('min_through_hole_diameter', floor['via_hole'])):
            if abs(rules.get(key, -1) - value) > 1e-9:
                out.append(f'project {key} {rules.get(key)!r}, R12 floor {value}')
    else:
        out.append('m3.kicad_pro missing')
    return out


def m5(ctx):
    fit = ctx.get('fit')
    if fit is None:
        return []
    out = []
    if fit.get('profile') != 'r12':
        out.append(f'fit report profile {fit.get("profile")!r}, expected r12')
    if fit.get('board_sha256') != ctx['sha']:
        out.append('fit report not bound to this board')
    out += [f'fit: {i}' for i in fit.get('issues', [])]
    return out


# R10/R11 checks retain their algorithms; only R12 contracts and geometry change.
def native(ctx):
    """Lazily share the proven checker's geometry/context without importing another revision's gate data."""
    if '_native' not in ctx:
        import check_r9 as r9
        import fit_check as fc
        class Context(r9.Ctx):
            def fit(self):
                if self.fit_report is None:
                    self.fit_report = fc.check_board(self.board, self.folder, profile='r12')
                return self.fit_report
        p = ctx['path']
        dru = p.with_suffix('.kicad_dru')
        c = Context(ctx['board'], p.parent, p, ctx.get('fit'),
                    dru=dru.read_text() if dru.is_file() else None)
        c.bom, c.cpl, c._reach = ctx.get('bom'), ctx.get('cpl'), None
        c.text = p.read_text() if p.is_file() else None
        c.data = ctx.get('data')
        if c.data is None:
            c.data = json.loads((R12_DIR / 'design/r12_gate_data.json').read_text())
        import r12_sch
        c.port_pin = {r['port']: r['r11_ball'] for r in r12_sch.read_pin_table()}
        c._balls = None
        ctx['_native'] = c
    return ctx['_native']


def ported(fn):
    def run(ctx):
        issues, evidence = fn(native(ctx))
        ctx.setdefault('evidence', {})[fn.__name__] = evidence
        return issues
    return run


# D-R12-10: AO3401A / AO3400A SOT-23, G=1 S=2 D=3. These are expected roles,
# never inferred from the board being checked (a swapped gate must fail).
FET_ROLES = {'G': ('1',), 'S': ('2',), 'D': ('3',)}
INNER = ('In1.Cu', 'In2.Cu')
REF_PLANES = ('GND', '3V3', '3V3A', 'PORT_4V8', 'RAW_PROTECTED')  # PORT_5V3 deleted, D-R12-07
FAST = re.compile(r'^(HSE_|USB_D[PM]$|QSPI_|SPI\d+_|SD_)|_CS$')  # D-R12-34, including new sensor chip selects
SH_PORTS = {
    'J410': dict(zip(map(str, range(1, 7)), ('GND', 'PORT_4V8', 'GPS_TX_WIRE', 'GPS_RX_WIRE', None, None))),
    'J420': dict(zip(map(str, range(1, 5)), ('GND', 'PORT_4V8', 'RADIO_TX_WIRE', 'RADIO_RX_WIRE'))),
    'J440': dict(zip(map(str, range(1, 5)), ('GND', 'PORT_4V8', 'AUX_TX_WIRE', 'AUX_RX_WIRE'))),
    'J9': dict(zip(map(str, range(1, 7)), ('CAM_5V', 'CAM_5V', 'GND', 'GND', 'CAM_RX_WIRE', 'CAM_TX_WIRE'))),
    'J122': dict(zip(map(str, range(1, 7)), (*r10.SERVO_TERMINAL, None))),
    'J400': {'1': 'BAT_SW_SOURCE', '2': 'BAT_SW_RETURN', '3': None, '4': None},
}
WIRE_PADS = {'J1': {'1': 'BAT_IN', '2': 'GND'}}  # D-R12-30; J121 is fitted DB125 (D-R12-29).


def s1(c):
    return r11.s1(c)


def s2(c):
    with r10.patched(r10, PFET_ROLES=FET_ROLES):
        return r11.s2(c)


def s3(c):
    with r10.patched(r10, PFET_ROLES=FET_ROLES, NFET_ROLES=FET_ROLES):
        # Keep the same-layer gate-bias check: it must fail on unrouted copper.
        return r11.s3(c, copper=True)


def s4(c):
    """Required population from the R12 source contract; every part JLC-assembled, J1 (wire pads) off JLC uploads.

    D-R12-04..19 delete/re-source parts; D-R12-29 restores J121 to PCBA; D-R12-85 (owner 2026-11-05: "I want
    everything to be asssembled by jlc") puts C84 and LS120 on the JLC BOM / CPL, so circuit.json's owner_fit must be
    empty: a part listed there fails here, and R10's owner-BOM identity check below still runs for any that appears.
    R10's flag, schematic hierarchy, MPN value and assembly identity checks remain intact.
    """
    import r12_sch
    import export_fab
    parts, _ = r12_sch.model(r12_sch.circuit())
    # R10's SAFETY_FITTED (AGENTS §2.4 gate networks, pyro, switch chain) stays a fixed floor, independent of the source.
    required = frozenset(ref for ref, part in parts.items() if 'exclude_from_bom' not in part['flags']) | r10.SAFETY_FITTED
    manual = r12_sch.circuit()['owner_fit']
    owner_issues = [f'S-4: {ref} is owner-fitted (circuit.json owner_fit); D-R12-85 requires every part JLC-assembled'
                    for ref in sorted(manual)]
    bp, pop = r10.board_population, r10.population
    with r10.patched(r10, REQUIRED_FITTED=required,
                     board_population=lambda b: bp(b, required),
                     population=lambda text, schematic=False: pop(text, required, schematic)), \
            r10.patched(export_fab, MANUAL_FIT=manual), r10.patched(r11, WIRE_PADS=WIRE_PADS):
        issues, ev = r10.s4(c)
        issues += r11.wire_pad_population(c)
    issues += owner_issues
    # R10's owner BOM comparison omits excluded parts from its identity map. Check them explicitly here.
    if c.bom:
        owner = Path(c.bom).with_name(Path(c.bom).name.replace('_bom_jlc', '_bom_owner'))
        rows = list(csv.DictReader(owner.read_text().splitlines())) if owner.is_file() else []
        listed = {ref.strip(): row for row in rows for ref in row.get('Designator', '').split(',')}
        for ref in manual:
            f, row = c.fps.get(ref), listed.get(ref, {})
            if f is not None:
                want = {'LCSC Part #': f.GetFieldText('LCSC'),
                        'Manufacturer Part': f.GetFieldText('Manufacturer Part'),
                        'Footprint': str(f.GetFPID().GetLibItemName())}
                if any(row.get(k) != v for k, v in want.items()):
                    issues.append(f'S-4: owner BOM {ref} differs from its native identity')
    return issues, ev


def connector(c, ref, want, rid, tabs=True):
    """NC contacts may carry KiCad's unconnected names, but never a real net (D-R12-31)."""
    f = c.fps.get(ref)
    expected = dict(want)
    if f:
        for p in f.Pads():
            if p.GetNumber() in want and want[p.GetNumber()] is None:
                expected[p.GetNumber()] = p.GetNetname() if not r10.real_net(p.GetNetname()) else ''
    return r11.connector_pads(c, ref, expected, rid, tabs=tabs)


def s5(c):
    # D-R12-31: four-contact body, only 1/2 wired. Preserve S-5's entire resistor/clamp/bypass test.
    issues, ev = r10.s5(c)
    issues = [i for i in issues if i != 'S-5: J400 must have exactly two switch contacts']
    found, ev['contacts'] = connector(c, 'J400', SH_PORTS['J400'], 'S-5')
    return issues + found, ev


def s7(c):
    return connector(c, 'J122', SH_PORTS['J122'], 'S-7')


def s8(c):
    # D-R12-34: In2 is signal-carrying copper, not exempt. Include rings, tracks, pads, fills and drawings.
    return r11.s8(c, layers=INNER)


def fire_terminals(c):
    # D-R12-10: resolve each current-path terminal by its intended net on its reference, not old package pads.
    refs = {'PYRO1_IGN': ('R134', 'J121'), 'PYRO1_OUT': ('J121', 'Q124'),
            'RAW_ACT': ('Q121', 'R134'), 'ACT_FET_S': ('Q120', 'Q121'), 'BAT_IN': ('J1', 'Q120')}
    return {net: tuple({ref: tuple(p.GetNumber() for p in c.fps[ref].Pads() if p.GetNetname() == net)
                               if ref in c.fps else ()} for ref in ends) for net, ends in refs.items()}


def s9(c):
    with r10.patched(r10, FIRE_TERMINALS=fire_terminals(c)):
        return r10.s9(c, narrow=[])  # No R10 coordinate exceptions apply to the new SOT-23 paths.


def w1(c):
    import pcbnew
    issues, ev = [], {}
    for ref, want in {**WIRE_PADS, 'J121': {'1': 'PYRO1_OUT', '2': 'PYRO1_IGN'}}.items():
        found, ev[ref] = connector(c, ref, want, 'W-1', tabs=False)
        issues += found
        f = c.fps.get(ref)
        if f:
            for p in f.Pads():
                if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
                    issues.append(f'W-1: {ref}.{p.GetNumber()} must be plated through-hole')
            if ref == 'J121' and f.GetFieldText('Manufacturer Part') != 'DB125-3.5-2P-BK-S':
                issues.append('W-1: J121 must be the DB125-3.5-2P-BK-S (D-R12-29)')
    return issues, ev


def w2(c):
    issues, ev = [], {}
    for ref, want in SH_PORTS.items():
        found, ev[ref] = connector(c, ref, want, 'W-2')
        issues += found
        f = c.fps.get(ref)
        if f and f.GetFieldText('Manufacturer Part') != f'ZX-SH1.0-{len(want)}PWT':
            issues.append(f'W-2: {ref} must be ZX-SH1.0-{len(want)}PWT (D-R12-31)')
    return issues, ev


def lc1(c):
    # R10 / R11 local-clearance floor 0.15 mm kept (the 0.10 mm netclass, D-R12-03, is not a licence to relax it).
    issues, ev = [], []
    for f in c.board.GetFootprints():
        ref = f.GetReference()
        floor = .508 if ref == 'J2' else 1.0 if ref.startswith('TP') else .15
        for label, item in [(ref, f)] + [(f'{ref}.{p.GetNumber()}', p) for p in f.Pads()]:
            value = item.GetLocalClearance()
            if value is not None:
                ev.append((label, mm(value), floor))
                if mm(value) < floor - 1e-9:
                    issues.append(f'LC-1: {label} local clearance {mm(value):g} below {floor:g} mm')
    return issues, dict(overrides=ev)


def m3(c):
    # D-R12-24 pins R12's supports in its own gate data; corner support and centre tolerances unchanged.
    issues, ev = r11.m3(c)
    import pcbnew
    for d in c.board.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            if abs(mm(d.GetRadius()) - 1.6) > .01:
                issues.append('M-3: support diameter must be 3.2 mm')
    return [i.replace('R11_DATA', 'R12 gate data').replace('D-R11-10', 'D-R12-24') for i in issues], ev


def m6(c):
    # D-R12-01: one assembled face is stricter than R10's bottom-side spacing allowances.
    return f1({'board': c.board}), {}


def m7(c):
    """D-R12-25: sensors on F, geometry from their lands, never from numbered sensor pins."""
    import pcbnew
    import check_r9 as r9
    issues, ev = [], {}
    imu = c.data.get('imu', {})
    f = c.fps.get('U4')
    if not f or not {'rotation', 'lever_mm'} <= imu.keys():
        issues.append('M-7: U4 or its recorded rotation / lever arm missing')
    else:
        if f.IsFlipped() or abs((f.GetOrientationDegrees() - imu['rotation'] + 180) % 360 - 180) > .01:
            issues.append('M-7: U4 differs from its recorded top-side rotation (D-R12-25)')
        if abs(mm(f.GetPosition().x) - WIDTH / 2 - imu['lever_mm']) > imu.get('tol_mm', .05):
            issues.append('M-7: U4 differs from its recorded roll-axis lever arm')
    # Include added accelerometers by function, independent of their reference or pin numbering.
    sensors = {ref for ref, fp in c.fps.items() if ref.startswith('U') and ref != 'U1'
               and any(re.match(r'^(IMU_|HIGH_?G_|ACCEL_|HG_)', p.GetNetname()) for p in fp.Pads())} | {'U4', 'U5'}
    for ref in sorted(sensors):
        f = c.fps.get(ref)
        if f is None:
            issues.append(f'M-7: {ref} missing')
            continue
        body, inner = r9.mems_regions(f)
        bp, ip = r9.rect_poly(*body), r9.rect_poly(*inner)
        ev[ref] = dict(body=body, interior=inner)
        if f.IsFlipped():
            issues.append(f'M-7: {ref} must be on F (D-R12-25)')
        for t in c.board.GetTracks():
            if not t.IsOnLayer(pcbnew.F_Cu):
                continue
            if t.GetClass() == 'PCB_VIA':
                if pcbnew.SHAPE.Collide(bp, t.GetEffectiveShape(pcbnew.F_Cu), 0):
                    issues.append(f'M-7: via under {ref}')
            # D-R12-52: U5 is the MS5607 again, so R10's pad-interior track ban applies to it too.
            elif pcbnew.SHAPE.Collide(ip, t.GetEffectiveShape(pcbnew.F_Cu), 0):
                issues.append(f'M-7: track inside {ref} pad-ring interior')
        for z in c.board.Zones():
            if z.GetIsRuleArea() or not z.IsOnLayer(pcbnew.F_Cu) or not z.HasFilledPolysForLayer(pcbnew.F_Cu):
                continue
            poly = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(pcbnew.F_Cu))
            poly.BooleanIntersection(bp)
            if poly.Area() / 1e12 > r10.EPS:
                issues.append(f'M-7: fill under {ref}')
    return issues, ev


def m8(c):
    # R12's recorded connector edge queries only, never R10's coordinate exemptions (D-R12-24 / -31).
    return r10.m8(c, queries=c.data.get('short_edge_queries', {}))


TERMINAL_PINS = tuple((ref, tuple((pin, word) for pin, word in zip(want, words))) for ref, want, words in (
    ('J1', WIRE_PADS['J1'], ('BAT+', 'GND')),
    ('J121', {'1': '', '2': ''}, ('E1-', 'E1+')),
    ('J400', SH_PORTS['J400'], ('SW', 'SW', 'NC', 'NC')),
    ('J122', SH_PORTS['J122'], ('S1', 'S2', 'S3', 'S4', 'GND', 'NC')),
    ('J410', SH_PORTS['J410'], ('GND', '4V8', 'TXO', 'RXI', 'NC', 'NC')),
    ('J420', SH_PORTS['J420'], ('GND', '4V8', 'TXO', 'RXI')),
    ('J440', SH_PORTS['J440'], ('GND', '4V8', 'TXO', 'RXI')),
    ('J9', SH_PORTS['J9'], ('5V4', '5V4', 'GND', 'GND', 'RXI', 'TXO'))))


def k_legends(c):
    # D-R12-29..31: DB125 / SH contact words. No R11 optional-legend exemptions on R12.
    pinned = (('B.Silkscreen', REVISION),)
    words, base = r10.word_legends, r10.pinned_texts
    def revision(board):
        out = [i for i in base(board, pinned=pinned) if not i.startswith('revision legends ')]
        names = {t.GetText() for t in r10.legend_items(board) if hasattr(t, 'GetText')
                 and re.fullmatch(r'M3-ASSY-R\d+', t.GetText())}
        return out + ([f'revision legends {sorted(names)}: only {REVISION} allowed'] if names != {REVISION} else [])
    with r10.patched(r10, TERMINAL_PINS_R10=TERMINAL_PINS, PINNED_TEXTS=pinned, pinned_texts=revision,
                     word_legends=lambda b, **kw: words(b, spans={}, **kw)):
        issues, ev = r10.k_legends(c)
        found, ev['word_spans'] = r11.word_spans_r11(c.board)
    issues, ev['waived'] = r12_legend_set(c.board, issues + found)
    return issues, ev


# D-R12-81 (owner acceptance pending): J122's harness note is the one optional legend on R12. Drawn, it is checked as on
# R10 (exact words, once, within reach and subject-nearest; a conflicting 'SERVO ...' legend fails); absent, the absence
# alone is waived. Its 18.9 mm ink has no free strip within the 6 mm legend reach of J122 on either face (stage D,
# measured). Every contact legend (all 30 SH contacts, NC included), word, SWD row, revision and SHOWN_REFS designator
# stays required.
OPTIONAL_NOTES = frozenset({r10.SERVO_HARNESS_NOTE})


def r12_legend_set(board, issues):
    texts = r11._silk_texts(board)
    waived = {f'J122: silkscreen must identify {note!r} exactly once' for note in OPTIONAL_NOTES
              if texts.count(note) == 0}
    kept = [i for i in issues if i not in waived]
    return kept, sorted(set(issues) - set(kept))


def k_copper(c):
    import check_r9 as r9
    # D-R12-03 / -07: no VIPPO exception; U401 is deleted.
    issues, ev = r9.k_copper(c)
    found, ev['pour_pieces'] = r10.pour_debris(c.board)
    return issues + found, ev


def k_inner(c):
    import pcbnew
    issues = []
    routed = {t.m_Uuid.AsString() for t in c.board.GetTracks()}
    def bad(layer, net):
        return (layer == pcbnew.In1_Cu and net != 'GND') or (layer == pcbnew.In2_Cu
                and (bool(FAST.search(net)) or net in r10.FIRE_ONLY or not r10.real_net(net)))
    for t in c.board.GetTracks():
        if t.GetClass() != 'PCB_VIA' and bad(t.GetLayer(), t.GetNetname()):
            issues.append(f'K-inner: {t.GetNetname()} track on {c.board.GetLayerName(t.GetLayer())}')
    for key, layer, shape, box, pad, net, label in r10.copper_nodes(c.board):
        if pad is None and key not in routed and bad(layer, net):
            issues.append(f'K-inner: {label} on {c.board.GetLayerName(layer)}')
    return issues, {}  # D-R12-34 permits slower signals on In2; In1 is GND only.


def reference_names():
    """R10's named interfaces minus nets deliberately deleted in R12 (D-R12-04 / -08 / -12).

    Resolve the expected names from the source contract, not the board under test. This retains the stale-name
    check while accommodating sensor changes and their new SPI chip selects without numbered sensor pins.
    """
    import critical_reference as cr
    import r12_sch
    _, pins = r12_sch.model(r12_sch.circuit())
    names = set(filter(None, pins.values()))
    listed = set().union(*map(set, cr.r10_names().values()))
    return (listed & names) | {n for n in names if FAST.search(n)}


def reference_nets(board):
    import critical_reference as cr
    named = reference_names() | r10.signal_critical_nets(board)
    return {n for n in named if not cr.r10_slow_return_net(n)}


def k_reference(c):
    import pcbnew
    import critical_reference as cr
    # D-R12-34: In2 sees both In1 GND and the nearer B GND pour (0.2104 mm versus the 1.065 mm core).
    # B signals reference only In2 rail pours, never its signal copper.

    refs = {pcbnew.F_Cu: (pcbnew.In1_Cu, ('GND',)), pcbnew.In2_Cu: (pcbnew.In1_Cu, ('GND',)),
            pcbnew.B_Cu: (pcbnew.In2_Cu, REF_PLANES)}
    nets = reference_nets(c.board)
    samples, fill = cr.samples(c.board, nets, refs), cr.fills(c.board, refs)
    own, voids = r10.own_antipads(c.board), r10.own_barrel_voids(c.board)
    empty = pcbnew.SHAPE_POLY_SET()
    loose = [s for s in samples if not cr.inside(fill.get(s[1], empty), s[2], s[3])
             and not r10.in_own_antipad(own, s[0], s[2], s[3])
             and not r10.in_own_antipad(voids, s[0], s[2], s[3])]
    lower_refs = {pcbnew.In2_Cu: (pcbnew.B_Cu, ('GND',))}
    lower_samples = cr.samples(c.board, nets, lower_refs)
    lower_fill = cr.fills(c.board, lower_refs)
    loose += [s for s in lower_samples if not cr.inside(lower_fill.get(s[1], empty), s[2], s[3])
              and not r10.in_own_antipad(own, s[0], s[2], s[3])
              and not r10.in_own_antipad(voids, s[0], s[2], s[3])]
    samples += lower_samples
    issues = ['K-reference: no critical routed-reference samples (unrouted board)'] if not samples else []
    missing = reference_names() - {str(n) for n in c.board.GetNetsByName().keys()}
    issues += [f'K-reference: named interface net {n} absent from the board' for n in sorted(missing)]
    if loose:
        issues.append(f'K-reference: {len(loose)} critical samples lack reference copper, e.g. {loose[:3]}')
    return issues, dict(samples=len(samples), loose=len(loose))


def k_region(c):
    # D-R12-34 does not waive B.Cu's single reference region. Signal fills cannot masquerade as planes.
    with r10.patched(r10, return_path_nets=reference_nets):
        issues, ev = r10.k_region(c)
    import pcbnew
    for z in c.board.Zones():
        if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In2_Cu) and z.GetNetname() not in REF_PLANES:
            issues.append(f'K-region: non-plane In2 fill {z.GetNetname()} is not a reference region')
    return issues, ev


def k_plane(c):
    # R10's links / neck checks, without R10's panel tab coordinates, on R12's sole mixed power layer. D-R12-34 / -36:
    # 3V3 necks must be >= 1.0 mm (IPC-2152, 1 A on 0.5 oz inner), not R10's 0.5 mm.
    necks = r10.plane_necks
    with r10.patched(r11, PLANE_LAYERS_R11=('In2.Cu',)), \
            r10.patched(r10, plane_necks=lambda board, **kw: necks(board, **{**kw, 'width': PLANE_NECK_W})):
        return r11.k_plane(c)


PLANE_NECK_W = 1.0    # mm, D-R12-34

# D-R12-86 (R12F1-TRI-01): K-neighbours, ported from R11 (D-R11-85). Every ball round PE4 (PYRO1_GATE_N, C3) and PC1
# (ACT_EN_MCU, F2) is NC, GND, D-R11-23's 3V3 pair, or an inert net. R12 changes the inert argument from R11's text
# to a computation on the board's own parts: for each inert net the worst-corner gate voltage that one solder bridge
# to the guarded ball can put on the guarded FET (with the guard pin high-Z: reset, boot or MCU unpowered) is computed
# from the source bound, the divider resistors and the guard's series / pull-down resistors, each read from the board
# (value, and 1 % or 5 % from the UNI-ROYAL MPN, plus 100 ppm/K over 67 K), and must stay at or below GATE_LIMIT_V.
# R11's LOGIC_SOURCE_ST entry is dropped (U11 is deleted, D-R12-04); its ball G3 carries PORT_SENSE, which is driven
# HIGH whenever the battery path is on, so the old open-drain argument does not carry over.
# D-R12-93: PORT_SENSE moves to PD10 (H9) and G3 is NC, so its D-R12-86 inert entry is dropped (a stale entry fails).
# AO3400A VGS(th) 0.65 / 1.05 / 1.45 V at ID 250 uA, TJ 25 C (AOS AO3400A Rev 3.1 p. 2, Datasheet). The limit keeps a
# 0.20 V allowance below the 0.65 V minimum for the threshold's fall to the bay's +70 C and for the < 250 uA drain current
# that already starts Q120 / Q121 through ACT_GATE's 50 kohm pull-up (Inference: AOS gives no VGS(th)-temperature curve).
GATE_LIMIT_V = 0.45
NEIGHBOUR_EXCEPTIONS = dict(r11.NEIGHBOUR_EXCEPTIONS)       # D-R11-23 owner deviation: C3 diagonal to 3V3 B2 / D2
# guard net -> (series resistor from the guard to the gate, gate net, pull-down from the gate to GND, FET)
GUARD_LOAD = {'ACT_EN_MCU': ('R122', 'ACT_EN', 'R123', 'Q122')}
PACK_MAX_V = 8.4                                           # 2S full charge (REQUIREMENTS F9; r12_budget u9)
NRST_RPU_MIN = 30e3                                        # DS12110 Rev 8 Table 65 p. 146: RPU 30 / 40 / 50 kohm
# (guard, net) -> source bound, divider chain (top: series from the source net to the sense net; bottom: in parallel
# from the sense net to GND) and the argument. 'rail' bounds come from r12_windows.json's drift maximum.
NEIGHBOUR_INERT = {
    ('ACT_EN_MCU', 'PYRO1_CONT'): dict(
        source='PYRO1_OUT', vmax=('fixed', PACK_MAX_V), top=('R173', 'R129'), bottom=('R130', 'R178'),
        why='D-R11-85 (fixed ball, R10\'s LQFP neighbour of PC1 too): passive 10.2k / 1k divider of PYRO1_OUT. With the '
            'bus off PYRO1_OUT is held near 1.6 V by the cold pull-up (R131 10k from 3V3 through D120), so the pack '
            'bound applies only to a bus already on (Calculation / Inference)'),
    ('ACT_EN_MCU', 'CAM_5V_SENSE'): dict(
        source='CAM_5V', vmax=('rail', 'CAM_5V ('), top=('R104', 'R107'), bottom=('R105', 'R106'),
        why='D-R11-85 / -86: passive 10.2k / 1k divider of CAM_5V (Calculation / Inference)'),
    ('ACT_EN_MCU', 'NRST'): dict(
        source='3V3', vmax=('rail', '3V3 ('), pullup_min=NRST_RPU_MIN, also=('J2',),
        why='D-R11-85 (fixed ball): open-drain reset, only the internal >= 30 kohm pull-up to VDD (DS12110 Table 65); '
            'a bridge held low by PC1 holds the MCU in reset (outputs off); J2.3 is the SWD probe\'s reset, attached '
            'on the bench only'),
}


def resistor(board, ref):
    """(ohms, tolerance, pad nets) of a fitted resistor; tolerance from the UNI-ROYAL WG MPN letter (F 1 %, J 5 %),
    otherwise 5 %, each plus 100 ppm/K over 67 K (r12_budget's drift case)."""
    f = board.FindFootprintByReference(ref)
    if f is None:
        return None
    ohms = r10.parse_value(f.GetValue(), 'R')
    mpn = {field.GetName(): field.GetText().strip() for field in f.GetFields()}.get('Manufacturer Part', '')
    m = re.match(r'^\d{4}WG([FJ])', mpn or '')
    tol = {'F': 0.01, 'J': 0.05}[m.group(1)] if m else 0.05
    return ohms, tol + 100e-6 * 67, {p.GetNumber(): p.GetNetname() for p in f.Pads()}


def bridged_gate(board, guard, net, entry, rails):
    """(worst gate V, issues): one bridge from `net` to the guard pin, guard high-Z, every resistor at its worst end."""
    import itertools
    issues = []
    series, gate_net, pulldown, _fet = GUARD_LOAD[guard]
    load = {r: resistor(board, r) for r in (series, pulldown)}
    if None in load.values() or any(v[0] is None for v in load.values()):
        return None, [f'{guard}: load resistors {series} / {pulldown} missing or unreadable']
    if sorted(load[series][2].values()) != sorted((guard, gate_net)) or \
            sorted(load[pulldown][2].values()) != sorted((gate_net, 'GND')):
        return None, [f'{guard}: {series} must join {guard} to {gate_net} and {pulldown} {gate_net} to GND']
    kind, bound = entry['vmax']
    if kind == 'rail':
        name = next((k for k in rails if k.startswith(bound)), None)
        if name is None:
            return None, [f'{net}: rail {bound!r} not in r12_windows.json']
        vmax = rails[name]['drift']['max_V']
    else:
        vmax = bound
    if 'pullup_min' in entry:
        sources = [(entry['pullup_min'], 0.0)]           # an exact minimum: no tolerance on top of it
        tops, bots = [[(entry['pullup_min'], 0.0)]], []
    else:
        parts = {r: resistor(board, r) for r in entry['top'] + entry['bottom']}
        if any(v is None or v[0] is None for v in parts.values()):
            return None, [f'{net}: divider part missing or unreadable ({sorted(k for k, v in parts.items() if not v)})']
        # top: a series chain from the source net to the sense net; bottom: each from the sense net to GND
        at = entry['source']
        for r in entry['top']:
            nets = list(parts[r][2].values())
            if at not in nets or len(nets) != 2:
                return None, [f'{net}: {r} does not continue the divider chain from {at}']
            at = nets[1] if nets[0] == at else nets[0]
        if at != net:
            issues.append(f'{net}: divider top {"+".join(entry["top"])} ends on {at}, not {net}')
        for r in entry['bottom']:
            if sorted(parts[r][2].values()) != sorted((net, 'GND')):
                issues.append(f'{net}: {r} is not from {net} to GND')
        tops = [[parts[r][:2] for r in entry['top']]]
        bots = [parts[r][:2] for r in entry['bottom']]
    # anything else on the sense net (a driver) would void the argument: only U1, the divider and capacitors to GND
    allowed = set(entry.get('top', ())[-1:]) | set(entry.get('bottom', ())) | set(entry.get('also', ())) | {'U1'}
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == net and f.GetReference() not in allowed:
                other = {q.GetNetname() for q in f.Pads()} - {net}
                if not (f.GetReference().startswith('C') and other == {'GND'}):
                    issues.append(f'{net}: {f.GetReference()}.{p.GetNumber()} on the sense net is not a recorded '
                                  'divider part or a capacitor to GND')
    terms = tops[0] + bots + [load[series][:2], load[pulldown][:2]]
    worst = 0.0
    for signs in itertools.product((-1, 1), repeat=len(terms)):
        val = [r * (1 + s * t) for (r, t), s in zip(terms, signs)]
        n_top = len(tops[0])
        top = sum(val[:n_top])
        bots_v = val[n_top:n_top + len(bots)]
        rs, rp = val[-2], val[-1]
        if bots_v:
            bot = 1 / sum(1 / b for b in bots_v)
            vth, rth = vmax * bot / (top + bot), top * bot / (top + bot)
        else:
            vth, rth = vmax, top
        worst = max(worst, vth * rp / (rth + rs + rp))
    return worst, issues


def k_neighbours(c):
    """(issues, evidence): the D-R11-85 ball rule with R12's inert table and a board-value gate computation."""
    issues, ev = r11.gate_neighbours(c.board, exceptions=NEIGHBOUR_EXCEPTIONS,
                                     inert={k: v['why'] for k, v in NEIGHBOUR_INERT.items()})
    rails = json.loads((R12_DIR / 'design/r12_windows.json').read_text())['rails']
    gates = {}
    for (guard, net), entry in sorted(NEIGHBOUR_INERT.items()):
        if guard not in GUARD_LOAD:
            issues.append(f'{guard}: no gate load model for inert neighbour {net}')
            continue
        if not any(p.GetNetname() == net for f in c.board.GetFootprints() for p in f.Pads()):
            continue                                     # stale entries are reported by gate_neighbours
        v, found = bridged_gate(c.board, guard, net, entry, rails)
        issues += found
        if v is None:
            continue
        gates[f'{guard}/{net}'] = round(v, 4)
        if v > GATE_LIMIT_V:
            issues.append(f'{guard} bridged to {net}: Q122 gate up to {v:.3f} V with the guard high-Z, above the '
                          f'{GATE_LIMIT_V} V limit (AO3400A VGS(th) min 0.65 V less 0.20 V allowance; D-R12-86)')
    ev = dict(balls=ev, bridged_gate_V=gates, limit_V=GATE_LIMIT_V)
    return issues, ev


# D-R12-67A: stage C pass 1 may report these signal-reference rules without failing (r12_build.sh, R12_ROUTE_HYGIENE).
# Nothing else may be made advisory; the S- / M- / W- / LC- families never relax (AGENTS section 2).
ADVISABLE = ('K-reference', 'K-region', 'K-plane')
ALWAYS_FATAL = ('S-', 'M-', 'W-', 'LC-')

PORTED = {
    'S-1': s1, 'S-2': s2, 'S-3': s3, 'S-4': s4, 'S-5': s5, 'S-6': r10.s6, 'S-7': s7, 'S-8': s8, 'S-9': s9,
    'W-1': w1, 'W-2': w2, 'LC-1': lc1, 'M-3': m3, 'M-6': m6, 'M-7': m7, 'M-8': m8,
    'K-legends': k_legends, 'K-copper': k_copper, 'K-inner': k_inner, 'K-reference': k_reference,
    'K-region': k_region, 'K-plane': k_plane, 'K-fill': r10.k_fill, 'K-neighbours': k_neighbours,
}


RULES = {'L-1': l1, 'M-1': m1, 'F-1': f1, 'N-1': n1, 'V-1': v1, 'V-2': v2, 'K-rules': k_rules, 'M-5': m5}

RULES.update({rid: ported(fn) for rid, fn in PORTED.items()})
TITLES.update({
    'S-1': 'RAW_ACT armed-side parts and no bypass', 'S-2': 'pyro feed through Q120/Q121 only',
    'S-3': 'gates defined off, local bias on the FET layer', 'S-4': 'fitted population and assembly identities',
    'S-5': 'protected switch contacts, clamp and no bypass', 'S-6': 'ports separated from safety copper',
    'S-7': 'servo signals, GND and NC only', 'S-8': 'foreign In1/In2 copper >= 1 mm from barrels and rings',
    'S-9': 'fire and battery current-path widths', 'W-1': 'battery wire pads and DB125 pyro terminal',
    'W-2': 'SH connector identities and pin maps', 'LC-1': 'local clearance floors',
    'M-3': 'recorded M3 supports', 'M-6': 'no bottom assembly', 'M-7': 'sensor pose and copper exclusions',
    'M-8': 'courtyard short-edge clearances', 'K-legends': 'R12 legends, designators and Fab references',
    'K-copper': 'via/pad, joints, thermal, paste and pour hygiene', 'K-inner': 'In1 GND, In2 mixed copper',
    'K-reference': 'critical reference coverage', 'K-region': 'one In2 rail region per B signal chain',
    'K-plane': 'In2 fill connectivity and necks', 'K-fill': 'saved fills agree with native refill',
    'K-neighbours': 'PE4 / PC1 ball neighbours cannot raise their gate if bridged (D-R11-85, D-R12-86)',
})


def selected_rules(only=None, stage='full'):
    names = list(STAGES[stage])
    if only:
        unknown = set(only) - set(STAGES['full'])
        if unknown:
            raise ValueError(f'unknown rule ids {sorted(unknown)}')
        names = [n for n in names if n in only]
    return names


def advisory_rules(names):
    """Validate an --advisory list (D-R12-67A): only ADVISABLE rules, never an ALWAYS_FATAL family."""
    names = set(names or ())
    fatal = sorted(n for n in names if n.startswith(ALWAYS_FATAL))
    if fatal:
        raise ValueError(f'rules {fatal} are always fatal (S- / M- / W- / LC-, D-R12-67A)')
    other = sorted(names - set(ADVISABLE))
    if other:
        raise ValueError(f'rules {other} cannot be advisory; only {list(ADVISABLE)} (D-R12-67A)')
    return frozenset(names)


def check_board(board, path, fit=None, only=None, stage='full', sha=None, netlist=None, data=None, bom=None, cpl=None,
                advisory=()):
    advisory = advisory_rules(advisory)
    ctx = dict(board=board, path=Path(path), fit=fit, sha=sha, netlist=netlist or R12_DIR / 'schematic.net.xml',
               data=data, bom=bom, cpl=cpl)
    rules, issues, notes = {}, [], []
    for rid in selected_rules(only, stage):
        if rid in PENDING:
            found = [f'{rid}: not ported to R12 yet (r12_plan.md stages B-D)']
            title = 'pending port'
        else:
            try:
                found = RULES[rid](ctx)
            except Exception as error:
                found = [f'check could not run: {type(error).__name__}: {error}']
            title = TITLES[rid]
        found = [i.removeprefix(rid + ': ') for i in found]
        rules[rid] = dict(title=title, ok=not found, issues=found, fatal=rid not in advisory)
        tagged = [f'{rid}: {i}' for i in found] if rid not in PENDING else found
        if rid in advisory:
            notes += tagged
        else:
            issues += tagged
    return dict(rules=rules, issues=issues, advisory=notes, advisory_rules=sorted(advisory),
                failing=[r for r, v in rules.items() if not v['ok'] and v['fatal']],
                reported=[r for r, v in rules.items() if not v['ok'] and not v['fatal']], ok=not issues,
                stage=stage, evidence=ctx.get('evidence', {}))


def file_sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board', nargs='?', type=Path, default=R12_DIR / 'm3.kicad_pcb')
    ap.add_argument('--report', type=Path)
    ap.add_argument('--fit', type=Path)
    ap.add_argument('--only')
    ap.add_argument('--bom', type=Path)
    ap.add_argument('--cpl', type=Path)
    ap.add_argument('--stage', choices=tuple(STAGES), default='full')
    ap.add_argument('--advisory', default='', help=f'comma list from {",".join(ADVISABLE)}: reported, not fatal')
    a = ap.parse_args()
    only = {r.strip() for r in a.only.split(',')} if a.only else None
    advisory = {r.strip() for r in a.advisory.split(',') if r.strip()}
    try:
        selected_rules(only, a.stage)
        advisory_rules(advisory)
    except ValueError as error:
        ap.error(str(error))
    import pcbnew
    bp = a.board.resolve()
    sha = file_sha(bp)
    fit = json.loads(a.fit.read_text()) if a.fit else None
    board = pcbnew.LoadBoard(str(bp))
    report = check_board(board, bp, fit=fit, only=only, stage=a.stage, sha=sha, bom=a.bom, cpl=a.cpl,
                         advisory=advisory)
    if file_sha(bp) != sha:
        report['issues'].append('board changed during check')
        report['ok'] = False
    report.update(board_sha256=sha, checker_sha256=file_sha(__file__))
    for rid, r in report['rules'].items():
        state = 'OK  ' if r['ok'] else 'FAIL' if r['fatal'] else 'NOTE'
        print(f"{rid:10s} {state} {r['title']}" + (f" ({len(r['issues'])})" if r['issues'] else ''))
    for i in report['issues']:
        print('FAIL', i)
    for i in report['advisory']:
        print('NOTE', i)
    reported = f"; {len(report['advisory'])} advisory findings reported, not fatal ({', '.join(report['reported'])})" \
        if report['advisory'] else ''
    print(f'R12 CAD contract ({a.stage}):', ('OK' if report['ok'] else f"FAIL ({len(report['issues'])} findings)")
          + reported)
    if a.report:
        a.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
