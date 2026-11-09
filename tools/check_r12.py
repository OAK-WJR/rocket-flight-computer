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
S-10: on every copper layer, fills (protected-net fills too) and barrels included, default-deny (m3_design/r12_fire.py):
      Q124's gate nets >= 1.0585 mm from every net but GND, the gate pair and U1's NC balls; PYRO1_OUT >= 1.040 mm
      from every net but GND (0.25 / 0.5 mm copper / fills) and three pyro-network nets; PYRO1_IGN >= 0.25 / 0.5 mm;
      U1's NC balls count against PYRO1_OUT and PYRO1_IGN (R12F6-TRI-02); only measured item pairs, each with its own
      floor and reason, are excepted (R12F5-TRI-01, verifier lane P2); a netlist guard holds every not-a-path class in
      the commanded-fire state and keeps the cold pull-up diode's anode off 3V3 (R12F6-TRI-01), with part classes
      default-deny (round 6 V-4); the pack-energy nets BAT_IN / ACT_FET_S / RAW_ACT (derived from the netlist) keep
      >= 1.040 mm from every net, copper and fills, but each other, ACT_GATE and their resistors' other ends (V-1 / V-2);
      the FMEA I-5 rails (derived from the netlist, R12F7-TRI-01) keep >= 1.040 mm (pack voltage: RAW_PROTECTED,
      VLOGIC, the converters' switch / bootstrap nodes) or >= 0.300 mm (port voltage: CAM_5V, PORT_4V8, VBUS) from
      3V3 / 3V3A and every I-5 victim (R12F8-TRI-01 / R12F9-TRI-01: every net on or reaching 3V3 / 3V3A, an MCU pin
      or any other IC pin through < 5 kohm, derived from the netlist, default-deny; the port class less the FT-only
      input nets of I5_PORT_FT, their direction read from the pin map (R12F9-TRI-02); every rail less the rated IC
      pins of I5_RATED, checked by i5_rated_guard); the pack-class I-5 DRU rules hold J2 and the test pads at 1.040 mm
      too (R12F9-TRI-03); U403's EN reaches PC12 only through R436 with D436 clamping PC12 (en_guard); every exception
      floor is its measured gap rounded down to 1 um (R12F10-TRI-03); unconnected IC pins are I-5 victims and a loader
      exemption covers only the port rails its reason names (R12F10-TRI-05 / -06); a test pad's local clearance is the
      largest S-10 limit any pair of its net can take (R12F10-TRI-02).
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
K-power: R10 / R11's single-via-open rule (R12F8-TRI-02; R10 D-R21-02 / D-R22-02 / D-R23-01 / -02 / -11, R11 O-C2-5):
         every regulator feedback, OVLO, EN and ILIM tap, sense tap, BOOT0 / VCAP / IMU-ground tap and gate drive of
         SINGLE_OPEN_TAPS_R12 stays joined to its source through same-net copper with any one via of its net removed
         (check_r10.single_via_opens); a single point passes only as an exact SINGLE_OPEN_EXCEPTIONS_R12 entry with its
         measured reason, and an entry no longer met fails as stale.

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
IMPLEMENTED = ('S-1', 'S-2', 'S-3', 'S-4', 'S-5', 'S-6', 'S-7', 'S-8', 'S-9', 'S-10', 'W-1', 'W-2', 'LC-1',
               'M-3', 'M-6', 'M-7', 'M-8', 'K-legends', 'K-copper', 'K-inner', 'K-reference', 'K-region', 'K-plane', 'K-fill',
               'K-neighbours', 'K-power')
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
        c.netlist = ctx.get('netlist')
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


# R12F6-TRI-01: the cold pull-up is 3V3 -> R136 -> D120 (PYRO1_COLD_PU) -> PYRO1_COLD -> R131 -> PYRO1_OUT. R136 is the
# one named tie from the armed-side sense chain to a supply; D120 no longer touches 3V3, so R10's (D120, PYRO1_COLD,
# 3V3) tie is dropped and a D120 anode back on 3V3 fails S-1 / S-2 as an unnamed tie (and S-10's fire-state guard).
SUPPLY_TIES = {k: v for k, v in r10.SUPPLY_TIES.items() if k[0] != 'D120'}
SUPPLY_TIES[('R136', 'PYRO1_COLD_PU', '3V3')] = ('cold pull-up series resistor R136 (R12F6-TRI-01): the continuity '
                                                 'cold-side bias (H-1) from 3V3 through R136, D120 and R131')
ARMED_NET_PARTS = dict(r10.ARMED_NET_PARTS, PYRO1_COLD_PU={'D120', 'R136'})


def s1(c):
    with r10.patched(r10, SUPPLY_TIES=SUPPLY_TIES, ARMED_NET_PARTS=ARMED_NET_PARTS):
        return r11.s1(c)


def s2(c):
    with r10.patched(r10, PFET_ROLES=FET_ROLES, SUPPLY_TIES=SUPPLY_TIES, ARMED_NET_PARTS=ARMED_NET_PARTS):
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
            'bus off PYRO1_OUT is held near 1.6 V by the cold pull-up (R136 5.1k, D120 and R131 5.1k from 3V3, '
            'R12F6-TRI-01), so the pack bound applies only to a bus already on (Calculation / Inference)'),
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


# S-10 (R12F5-TRI-01, tightened by the round 5 verifier's lane P2): R10's fire-net copper gaps (D-R26-02 / -04, gated in
# R10 by test_r10_check.test_r26_*) and D-R11-23 as one rule on every copper layer: tracks, vias and pads where they are
# flashed, plated barrels (via and pad hole walls) where they are not, and every zone fill, protected-net fills
# included. One solder bridge, or a later CAF / dendrite path, from a gate net to copper that can raise it turns Q124 on,
# and one from PYRO1_OUT to a net that can sink current passes bus current through the match; the bus is live from the
# on-rail check (AGENTS section 2.1), so either fires an enabled match. PYRO1_IGN is held too (R134 overload), and so
# are the pack-energy nets BAT_IN / ACT_FET_S / RAW_ACT (round 6 verifier V-1 / V-2: an unfused pack short, or pack
# voltage on a logic net), derived from the netlist by r12_fire.pack_nets(), and the FMEA I-5 rails above 3V3 against
# 3V3 / 3V3A (R12F7-TRI-01), derived by r12_fire.i5_rails().
# The classes, limits and measured exceptions are m3_design/r12_fire.py's (default-deny: a net counts unless classed
# there with a calculated reason; only U1's NC balls are exempt as NC; every exception is one item pair with its own
# floor). The DRU carries the same definition (r12_sch.dru() from r12_fire.dru_rules()), so DRC holds it and the pours
# pull back on refill; this rule measures the board itself, and K-rules binds the DRU to the generator.
import r12_fire as fire

S10_GATES, S10_OUT, S10_IGN = fire.GATES, fire.OUT, fire.IGN
S10_GATE_MIN, S10_OUT_MIN, S10_GND_MIN, S10_FILL_MIN, S10_IGN_MIN = (fire.GATE_MIN, fire.OUT_MIN, fire.GND_MIN,
                                                                      fire.FILL_MIN, fire.IGN_MIN)


def copper_items(board):
    """Every copper item per layer: (net, layer id, label, shape, is_fill, owner reference or None, pad number)."""
    import pcbnew
    cu = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
    out = []
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            at = f'via ({mm(t.GetPosition().x):g}, {mm(t.GetPosition().y):g})'
            for lid in cu:
                if t.IsOnLayer(lid):
                    flashed = t.FlashLayer(lid)
                    out.append((t.GetNetname(), lid, at if flashed else at + ' barrel',
                                t.GetEffectiveShape(lid) if flashed else t.GetEffectiveHoleShape(), False, None, None))
        else:
            at = (f'track ({mm(t.GetStart().x):g}, {mm(t.GetStart().y):g})-({mm(t.GetEnd().x):g}, '
                  f'{mm(t.GetEnd().y):g})')
            out.append((t.GetNetname(), t.GetLayer(), at, t.GetEffectiveShape(t.GetLayer()), False, None, None))
    for f in board.GetFootprints():
        for p in f.Pads():
            at = f'{f.GetReference()}.{p.GetNumber()}'
            for lid in cu:
                if p.IsOnLayer(lid) and p.FlashLayer(lid):
                    out.append((p.GetNetname(), lid, at, p.GetEffectiveShape(lid), False, f.GetReference(),
                                p.GetNumber()))
                elif p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetDrillSize().x > 0:
                    out.append((p.GetNetname(), lid, at + ' barrel', p.GetEffectiveHoleShape(), False,
                                f.GetReference(), p.GetNumber()))
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        for lid in cu:
            if z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                fill = z.GetFilledPolysList(lid)
                if fill.OutlineCount():
                    out.append((z.GetNetname(), lid, f'fill {z.GetZoneName() or z.GetNetname()}', fill, True, None,
                                None))
    return out


def shape_gap(a, b, reach):
    """Edge-to-edge distance (mm) between two copper shapes, bisected with KiCad's collision to 0.1 um, or None when
    they are reach mm or more apart."""
    import pcbnew
    if not b.Collide(a, pcbnew.FromMM(reach)):
        return None
    if b.Collide(a, 0):
        return 0.0
    lo, hi = 0, pcbnew.FromMM(reach)
    while hi - lo > 100:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if b.Collide(a, mid) else (mid, hi)
    return hi / 1e6


def fire_gaps(board, items=None):
    """S-10's measured pairs: [dict(gap, limit, cls, net_a, a, net_b, b, layer)] for every pair of copper items on one
    layer, one of them on a protected net (r12_fire.PROTECTED), nearer than GATE_MIN plus 10 um. limit is None when the
    pair is not a path (cls says why); a is the item of the first protected net of the pair (r12_fire priority)."""
    import pcbnew
    items = copper_items(board) if items is None else items
    boxes = [it[3].BBox() for it in items]
    reach = pcbnew.FromMM(fire.REACH)
    rank = {n: i for i, n in enumerate(fire.PROTECTED)}
    seen, out = set(), []
    for i, a in enumerate(items):
        if a[0] not in rank:
            continue
        box = boxes[i]
        grown = pcbnew.BOX2I(box.GetPosition() - pcbnew.VECTOR2I(reach, reach),
                             pcbnew.VECTOR2I(box.GetWidth() + 2 * reach, box.GetHeight() + 2 * reach))
        for j, b in enumerate(items):
            if b[1] != a[1] or b[0] == a[0] or not grown.Intersects(boxes[j]):
                continue
            key = (min(i, j), max(i, j))
            if key in seen:
                continue
            seen.add(key)
            limit, cls, pn = fire.pair_limit(a[0], a[5], b[0], b[5], a[4] or b[4])
            if cls == 'unprotected':
                continue                          # an I-5 rail against a net other than 3V3 / 3V3A (R12F7-TRI-01)
            gap = shape_gap(a[3], b[3], fire.REACH)
            if gap is None:
                continue
            p, q = (a, b) if pn == a[0] else (b, a)
            out.append(dict(gap=round(gap, 4), limit=limit, cls=cls, net_a=p[0], a=p[2], net_b=q[0], b=q[2],
                            layer=board.GetLayerName(a[1])))
    return sorted(out, key=lambda r: (r['gap'], r['net_a'], r['a'], r['net_b'], r['b']))


def s10(c, exceptions=None, not_a_path=None):
    """S-10: Q124's gate nets, PYRO1_OUT and PYRO1_IGN keep their limits on every layer, fills included; only the
    measured item-pair exceptions of r12_fire, each above its floor, are allowed below a limit (R12F5-TRI-01)."""
    table = fire.exception_index(exceptions)
    issues, kept, nc, owner, used, least = [], [], [], [], set(), {}
    fire_gaps_cache = fire_gaps(c.board)
    for r in fire_gaps_cache:
        where = f'{r["net_a"]} {r["a"]} to {r["net_b"]} {r["b"]} on {r["layer"]}: {r["gap"]:.4f} mm'
        if r['limit'] is None:
            if r['cls'] == 'U1 NC ball' and r['gap'] < fire.GATE_MIN:
                nc.append(where)
            continue
        if r['net_a'] == fire.OUT and r['net_b'] == 'GND' and r['gap'] < fire.OUT_MIN:
            owner.append(where)                    # fire-capable, under R10's 1.040 mm: R10 row 1's owner list
        if r['net_a'] == fire.IGN and r['gap'] < fire.OUT_MIN:
            owner.append(where)                    # R134 overload (destructive, not a match fire)
        if r['gap'] >= r['limit'] - 5e-5:
            continue
        hit = table.get((r['a'], r['b'], r['layer']))
        if hit is None:
            issues.append(f'S-10: {where}, below {r["limit"]:g} mm ({r["cls"]})')
            continue
        used.add((r['a'], r['b'], r['layer']))
        k3 = (r['a'], r['b'], r['layer'])
        least[k3] = min(least.get(k3, r['gap']), r['gap'])
        floor, key = hit
        if r['gap'] < floor - 5e-5:
            issues.append(f'S-10: {where}, below the {floor:.3f} mm floor of its exception ({key}: {fire.WHY[key]})')
        else:
            kept.append(dict(pair=where, floor=floor, exception=key))
    probes = {}
    for f in c.board.GetFootprints():                # R12F9-TRI-03: KiCad applies a pad's own clearance in place of the
        if f.GetReference().startswith('TP'):        # DRU's rules, so a test pad's override carries its net's S-10 floor
            for p in f.Pads():
                lc, need = p.GetLocalClearance(), fire.probe_clearance(p.GetNetname())
                have = mm(lc) if lc is not None else None
                probes[f'{f.GetReference()}.{p.GetNumber()}'] = (p.GetNetname(), have, need)
                if have is None or have < need - 1e-9:
                    issues.append(f'S-10: test pad {f.GetReference()}.{p.GetNumber()} ({p.GetNetname()}) local clearance '
                                  f'{have} mm, below its S-10 floor {need:g} mm: KiCad would apply it instead of the DRU '
                                  'rule (R12F9-TRI-03)')
    for k3, gap in sorted(least.items()):              # R12F10-TRI-03: a floor is its pair's measured gap rounded down
        floor, key = table[k3]                         # to 1 um, so a looser one accepts movement the record denies
        if gap - floor > 0.001 + 5e-5:
            issues.append(f'S-10: exception {k3[0]} to {k3[1]} on {k3[2]} ({key}): floor {floor:.3f} mm is more than 1 um '
                          f'below its measured gap {gap:.4f} mm (set it to the gap rounded down to 1 um, R12F10-TRI-03)')
    for (a, b, layer), (floor, key) in sorted(table.items()):
        if (a, b, layer) not in used:
            issues.append(f'S-10: exception {a} to {b} on {layer} ({key}, floor {floor:.3f} mm) is not on the board '
                          'below its limit: a stale entry (update m3_design/r12_fire.py)')
    netlist = getattr(c, 'netlist', None) or R12_DIR / 'schematic.net.xml'
    classes = fire.netlist_classes(netlist)
    issues += [f'S-10: {m}' for m in fire.guard(classes, not_a_path)]
    fired, fire_ev = fire.fire_state_guard(netlist, not_a_path, classes)     # R12F6-TRI-01: the commanded-fire state
    issues += [f'S-10: {m}' for m in fired]
    packed, pack_ev = fire.pack_guard(netlist, classes, not_a_path)          # round 6 V-1 / V-2: the pack-energy nets
    issues += [f'S-10: {m}' for m in packed]
    flt, flt_ev = fire.flt_guard(netlist, classes)                         # PACK_FLT: R95 and D95 between U9 FLT and PC13
    issues += [f'S-10: {m}' for m in flt]
    en, en_ev = fire.en_guard(netlist, classes)                            # R12F8-TRI-01: R436 and D436 at U403's EN
    issues += [f'S-10: {m}' for m in en]
    i5, i5_ev = fire.i5_guard(netlist)                                     # R12F7-TRI-01: the FMEA I-5 rails
    issues += [f'S-10: {m}' for m in i5]
    i5_ev['least'], i5_ev['rated_least'] = {}, {}
    for r in fire_gaps_cache:
        if r['cls'] in ('i5-pack', 'i5-port', 'i5-rated'):
            k = f'{r["net_a"]} / {r["net_b"]}'
            at = i5_ev['rated_least' if r['cls'] == 'i5-rated' else 'least']
            if k not in at:
                at[k] = f'{r["gap"]:.4f} mm, {r["a"]} to {r["b"]} on {r["layer"]}'
    return issues, dict(exceptions=kept, u1_nc_balls=nc, owner_pairs=owner, netlist_classes=classes, probe_pads=probes,
                        fire_state=dict(series_ohm=fire_ev, min_ohm=fire.FIRE_SERIES_MIN),
                        pack=dict(pack_ev, min_ohm=fire.PACK_SERIES_MIN, limit=fire.PACK_MIN),
                        pack_flt=dict(flt_ev, min_ohm=fire.PACK_SERIES_MIN),
                        cam_en=dict(en_ev, min_ohm=fire.PACK_SERIES_MIN), i5=i5_ev,
                        not_a_path={f'{p} / {f}': why for (p, f), why in fire.NOT_A_PATH.items()},
                        limits=dict(gate=fire.GATE_MIN, out=fire.OUT_MIN, out_gnd=fire.GND_MIN, fill=fire.FILL_MIN,
                                    ign=fire.IGN_MIN, pack=fire.PACK_MIN, i5_pack=fire.PACK_MIN,
                                    i5_port=fire.I5_PORT_MIN))


# D-R12-67A: stage C pass 1 may report these signal-reference rules without failing (r12_build.sh, R12_ROUTE_HYGIENE).
# Nothing else may be made advisory; the S- / M- / W- / LC- families never relax (AGENTS section 2).
ADVISABLE = ('K-reference', 'K-region', 'K-plane')
ALWAYS_FATAL = ('S-', 'M-', 'W-', 'LC-')

# ---- K-power (R12F8-TRI-02): R10 / R11's single-via-open rule, ported --------------------------------------------------
# R10's SINGLE_OPEN_TAPS (check_r10, D-R21-02 / D-R22-02 / D-R23-01 / -02 / -11) mapped by function onto R12's parts: U2
# (the 3V3 buck, R10's R21-PWR-01 case: R14.1 on one via, open, R15 pulls FB to GND and U2 drives 3V3 toward VLOGIC), U9
# (OVLO, EN, ILIM and GND), U400 (port buck), U403 (camera buck, EN since R12F8-TRI-01), PA6's VLOGIC sense, BOOT0, VCAP,
# the load-switch gate drive, the IMU's power ground and the USB-C CC Rd returns. (net, tap pad, source pads, why); U1
# pads are R12 balls (BOOT0 D5, VCAP1 F8, VCAP2 E7, PA6 J3). R10 parts R12 deletes (U10, U11, U401, U402) have no entry.
SINGLE_OPEN_TAPS_R12 = (
    ('3V3', 'R14.1', ('L1.2',), "U2's feedback divider top (R10 R21-PWR-01): open, R15 pulls FB to GND and U2 drives 3V3 "
                                'toward VLOGIC'),
    ('FB_3V3', 'U2.3', ('R14.2', 'R15.1'), "U2's FB pin"),
    ('GND', 'R15.2', ('U2.2',), "U2's feedback divider bottom"),
    ('GND', 'U2.2', ('J1.2',), "U2's GND pin"),
    ('BAT_IN', 'R82.1', ('U9.5',), "U9's OVLO divider top"),
    ('BAT_OVLO', 'U9.2', ('R82.2', 'R83.1'), "U9's OVLO pin"),
    ('BAT_OVLO_B', 'R93.1', ('R83.2',), "U9's OVLO divider lower node"),
    ('GND', 'R93.2', ('U9.8',), "U9's OVLO divider bottom (open: OVLO rises to BAT_IN x 1, U9 off)"),
    ('BAT_ENABLE', 'R81.1', ('U9.1',), "U9's EN pull-down (R10 R20-SAF-01)"),
    ('BAT_ENABLE', 'C87.1', ('U9.1',), "U9's EN filter"),
    ('GND', 'R81.2', ('U9.8',), "U9's EN pull-down bottom (open: EN rises toward BAT_IN through R80 + R165 with J400 "
                                'closed, above its 6.5 V absolute maximum)'),
    ('GND', 'C87.2', ('U9.8',), "U9's EN filter bottom"),
    ('BAT_ILIM', 'R84.1', ('U9.9',), "U9's ILIM"),
    ('BAT_ILIM', 'R94.1', ('U9.9',), "U9's ILIM (second leg)"),
    ('GND', 'R84.2', ('U9.8',), "U9's ILIM bottom"),
    ('GND', 'R94.2', ('U9.8',), "U9's ILIM bottom (second leg)"),
    ('GND', 'U9.8', ('J1.2',), "U9's only GND pin"),
    ('PORT_4V8', 'R400.1', ('L400.2',), "U400's feedback divider top"),
    ('PORT_FB_TOP', 'R400.2', ('R404.1',), "U400's feedback divider middle"),
    ('PORT_FB', 'U400.4', ('R404.2', 'R401.1'), "U400's FB pin"),
    ('GND', 'R401.2', ('U400.1',), "U400's feedback divider bottom"),
    ('GND', 'U400.1', ('J1.2',), "U400's GND pin"),
    ('CAM_5V', 'R433.1', ('L401.2',), "U403's feedback divider top"),
    ('CAM_FB_TOP', 'R433.2', ('R434.1',), "U403's feedback divider middle"),
    ('CAM_FB', 'U403.4', ('R434.2', 'R435.1'), "U403's FB pin"),
    ('GND', 'R435.2', ('U403.1',), "U403's feedback divider bottom"),
    ('GND', 'U403.1', ('J1.2',), "U403's GND pin"),
    ('CAM_EN', 'R431.1', ('U403.5',), "U403's EN pull-down (camera off in reset)"),
    ('VLOGIC', 'R60.1', ('D5.1', 'D6.1'), "R60, PA6's VLOGIC sense divider top (R10 R22-POWER-02)"),
    ('GND', 'R61.2', ('J1.2',), "R61, PA6's VLOGIC sense divider bottom"),
    ('BOOT0', 'U1.D5', ('R5.1',), "BOOT0's pull-down R5 (R10 R23-MCU-02)"),
    ('GND', 'R5.2', ('J1.2',), "BOOT0's pull-down R5, GND end"),
    ('VCAP1', 'U1.F8', ('C19.1',), "VCAP1's 2.2 uF capacitor C19 (R10 R23-MCU-02)"),
    ('VCAP2', 'U1.E7', ('C20.1',), "VCAP2's 2.2 uF capacitor C20"),
    ('GND', 'C19.2', ('J1.2',), "C19 (VCAP1) GND end"),
    ('GND', 'C20.2', ('J1.2',), "C20 (VCAP2) GND end"),
    ('ACT_GATE', 'Q120.1', ('R121.1',), "Q120's gate drive from R121 (R10 R23-SAFETY-05)"),
    ('ACT_GATE', 'Q121.1', ('R121.1',), "Q121's gate drive from R121"),
    ('GND', 'U4.6', ('J1.2',), "U4's (IMU) power ground pin 6 (R10 R23-GATE-07)"),
    ('GND', 'U4.7', ('J1.2',), "U4's (IMU) ground pin 7"),
    ('GND', 'R7.2', ('J1.2',), 'R7 (USB-C CC1 Rd) GND'),
    ('GND', 'R8.2', ('J1.2',), 'R8 (USB-C CC2 Rd) GND'),
    # R12F8-TRI-03 (R10 row 22's class): the supply feeds from U9's OUT and to the sensor / ADC supply
    ('RAW_PROTECTED', 'C400.1', ('U9.6',), "U400's (port buck) input capacitor, the RAW B trunk's north end"),
    ('RAW_PROTECTED', 'U400.3', ('U9.6',), "U400's VIN"),
    ('RAW_PROTECTED', 'D5.2', ('U9.6',), "D5's anode: VLOGIC's only battery path"),
    ('RAW_PROTECTED', 'D9.1', ('U9.6',), 'D9 (SS34 RAW reverse clamp), assumed by the 2304-case hot-plug result'),
    ('RAW_PROTECTED', 'C97.1', ('U9.6',), "U9 OUT's 1 uF"),
    ('RAW_PROTECTED', 'R92.1', ('U9.6',), 'R92, the RAW bleed'),
    ('RAW_PROTECTED', 'U403.3', ('U9.6',), "U403's (camera buck) VIN"),
    ('3V3A', 'U1.H1', ('R164.2',), "U1's VDDA (ball H1) from R164"),
    ('3V3A', 'C22.1', ('R164.2',), "VDDA's 1 uF C22"),
    ('3V3A', 'U5.1', ('R164.2',), "U5's (barometer) VDD"),
    # R12F9-TRI-07: R164's 3V3 end (R10 row 22's sensor and ADC supply feed; one via there unpowered all of 3V3A) and
    # the high-g sensor U6's grounds (R10 R23-GATE-07's IMU-ground tap, carried to the second inertial part)
    ('3V3', 'R164.1', ('L1.2',), "R164's 3V3 end, the only feed of 3V3A (VDDA, U4, U5)"),
    ('GND', 'U6.7', ('J1.2',), "U6's (high-g) ground pin 7"),
    ('GND', 'U6.14', ('J1.2',), "U6's ground pin 14"),
    ('GND', 'U6.17', ('J1.2',), "U6's exposed pad"),
    # R12F9-TRI-08: PD10 PORT_SENSE, R12's power-state monitor (R10's PA4 taps, D-R22-02): it gates PC1 (firmware rule 1)
    # and the port UARTs
    ('PORT_SENSE', 'U1.H9', ('R111.2', 'R112.1'), "PD10's PORT_4V8 divider tap (open: PD10 floats, Inference)"),
    ('PORT_4V8', 'R111.1', ('L400.2',), "R111, PD10's divider top (open: PD10 reads low, PC1 refused, ports off)"),
    ('GND', 'R112.2', ('J1.2',), "R112, PD10's divider bottom (open: PD10 reads PORT_4V8 through R111)"),
    # R12F10-TRI-07: R10 row 22's taps ported by function to the rest of the barometer and the ADC supply: U5's only GND
    # pin (U5.3; U5.4 is CSB, tied to it), the I2C1 pull-ups' 3V3 ends, U1's VSSA (ball G1) and U4's 3V3A decoupling
    ('GND', 'U5.3', ('J1.2',), "U5's (barometer) only GND pin (open: no barometric gain, so no primary fire)"),
    ('GND', 'U5.4', ('J1.2',), "U5's CSB, tied to GND (I2C address select)"),
    ('3V3', 'R12.2', ('L1.2',), "R12, I2C1_SCL's pull-up 3V3 end (the barometer bus)"),
    ('3V3', 'R13.2', ('L1.2',), "R13, I2C1_SDA's pull-up 3V3 end (the barometer bus)"),
    ('GND', 'U1.G1', ('J1.2',), "U1's VSSA (ball G1), the ADC's ground (PA6 VLOGIC sense, PC2_C camera sense)"),
    ('3V3A', 'C30.1', ('R164.2',), "C30, U4's (IMU) 100 nF on 3V3A"),
)
# (tap pad, via label as check_r10.copper_nodes prints it, measured reason): the single points kept on purpose. An entry
# no longer met (its pads present) fails as stale.
_DOGBONE = ("a dog-bone via inside U1's TFBGA-100 escape (ball pitch 0.8 mm; every neighbouring channel holds another "
            "ball's escape), so no second barrel fits: R11 row 4's class, carried (owner row)")
SINGLE_OPEN_EXCEPTIONS_R12 = [
    ('U1.D5', 'via BOOT0 (23.00, 52.40)',
     "BOOT0's ball D5 escape: " + _DOGBONE + ". Open, BOOT0 floats with no pull: a reset may start the ROM loader "
     "instead of the firmware (no flight control, no fire: fail-safe; the Blue Jay covers recovery; Inference: DS12110 "
     "gives BOOT0 no internal pull)"),
    ('U1.D5', 'via BOOT0 (17.80, 48.20)',
     "BOOT0's B-to-F via by R5: a second barrel has no legal spot (NRST's In2 run at x 16.85-16.95 west, ACT_EN_MCU's B "
     "lane at x 16.4, PYRO1_GATE_N's F run at x 18.7 east, which holds every net but GND 1.0585 mm off; measured on the "
     "R12F8 lane P board). Open, BOOT0 floats as at its dog-bone (fail-safe, Inference); R5.2's own GND end has two vias"),
    ('U1.F8', 'via VCAP1 (25.40, 54.00)',
     "VCAP1's ball F8 escape: " + _DOGBONE + ". Open, the core LDO keeps C20's 2.2 uF on VCAP2 instead of DS12110 "
     "Rev 8's two 2.2 uF (Table 124 p. 216); its stability then is an Inference (R10's U1.48 entry); C19's own end now "
     "has two barrels"),
    ('U1.E7', 'via VCAP2 (24.60, 54.00)',
     "VCAP2's ball E7 escape: " + _DOGBONE + ". Open, the core LDO keeps C19's 2.2 uF on VCAP1 only (as VCAP1's entry, "
     "Inference); C20's own end now has two barrels"),
    # R12F8-TRI-03: the 3V3A feeds with no legal second barrel (owner row, R10 row 22 carried)
    ('U1.H1', 'via 3V3A (19.65, 36.80)',
     "3V3A's F-to-In2 via at R164.2 (U4's cell): a second barrel has no legal spot (R164.2's own land and mask north, "
     "C129.1 (ARM1_SENSE) west, I2C1_SCL's F / B runs and a GND via east, the SPI1 B lanes south; measured on the R12F8 "
     "lane P board). Open, VDDA (U1.H1) loses 3V3A: the ADCs (PA6 VLOGIC sense, PC2_C camera sense) read garbage and "
     "the MCU's analog domain is unpowered (DS12110 requires VDDA; behaviour not characterised: Inference)"),
    ('C22.1', 'via 3V3A (19.65, 36.80)', "as U1.H1: the same via feeds VDDA's decoupling"),
    ('U5.1', 'via 3V3A (25.80, 29.80)',
     "U5's (barometer) 3V3A B-to-F via: a second barrel has no legal spot (U5's body (M-7: no via under a sensor body) "
     "west, CAM_5V_SENSE's In2 run at x 26.6 and a GND via east, C32's lands north; measured on the R12F8 lane P board). "
     "Open, the barometer is unpowered: no barometric gain, so the fire rule (LIFTOFF AND a barometric gain) never "
     "fires the primary (fail-safe; the Blue Jay covers recovery)"),
    # R12F10-TRI-07: R12's 3V3 end and C30's 3V3A feed
    ('R12.2', 'via 3V3 (20.25, 31.50)',
     "R12.2's (I2C1_SCL pull-up) 3V3 via: a second barrel has no legal spot (I2C1_SDA's F run at x 19.15 west, 0.105 mm "
     "from the land; R13.1 (I2C1_SDA) and SDA's jog north; R12.1 (I2C1_SCL) south; I2C1_SCL's F run at x 20.7 east, with "
     "the GND via (20.25, 32.2) beside the land, SPI1_SCK's via (20.1, 33.6)'s only GND partner within 1.5 mm (1.41 mm), "
     "and a 3V3 via there would sit on SPI1_SCK's via; measured on the R12F10 lane P board). Open, SCL loses its 4.7 "
     "kohm pull-up: I2C1 runs on the MCU's internal pull-up or fails (Inference), so the barometer may give no reading: "
     "no barometric gain, so the fire rule never fires the primary (fail-safe; the Blue Jay covers recovery), as U5.1's "
     "single 3V3A via"),
    # C30's 3V3A feed
    ('C30.1', 'via 3V3A (25.70, 42.75)',
     "C30.1's B-to-F 3V3A via (U4's 100 nF): a second barrel has no legal spot (the 3V3A B run under C30 at x 25.7 and "
     "HG_CS's B loop (25.15, 42.95)-(25.7, 43.5)-(25.7, 44.25) south, IMU_INT1's F run at x 26.45 east, C30.2's GND land "
     "and its F link to the GND via (24.9, 41.6) north and west, SPI1_MISO's F jog (24.55, 42.35)-(25.15, 42.95) "
     "south-west; measured on the R12F10 lane P board). Open, only C30's 100 nF is lost: U4 keeps its own 3V3A feed "
     "through (24.95, 39.95) and C10 beside it (Inference: the IMU's noise without C30 is not characterised); not a power loss"),
    # R12F9-TRI-08: PD10's ball H9 escape
    ('U1.H9', 'via PORT_SENSE (26.20, 56.40)',
     "PD10's ball H9 escape: " + _DOGBONE + ". Open, PD10 is cut from the R111 / R112 divider and floats (no internal "
     "pull): its level is undefined (Inference), so R12 firmware rule 1's PC1 and port-UART gate loses its power-state "
     "input, with VBUS_SENSE (rule 1's cross-check) and the cold screen left; the divider's far via, R111.1's PORT_4V8 "
     "via and R112.2's GND via each have a second barrel"),
]


def k_power(c):
    taps, ev = r10.single_via_opens(c.board, taps=SINGLE_OPEN_TAPS_R12, exceptions=SINGLE_OPEN_EXCEPTIONS_R12)
    return [f'K-power: {i}' for i in taps], dict(single_via_open_taps=ev, exceptions=len(SINGLE_OPEN_EXCEPTIONS_R12))


PORTED = {
    'S-1': s1, 'S-2': s2, 'S-3': s3, 'S-4': s4, 'S-5': s5, 'S-6': r10.s6, 'S-7': s7, 'S-8': s8, 'S-9': s9,
    'S-10': s10, 'W-1': w1, 'W-2': w2, 'LC-1': lc1, 'M-3': m3, 'M-6': m6, 'M-7': m7, 'M-8': m8,
    'K-legends': k_legends, 'K-copper': k_copper, 'K-inner': k_inner, 'K-reference': k_reference,
    'K-region': k_region, 'K-plane': k_plane, 'K-fill': r10.k_fill, 'K-neighbours': k_neighbours, 'K-power': k_power,
}


RULES = {'L-1': l1, 'M-1': m1, 'F-1': f1, 'N-1': n1, 'V-1': v1, 'V-2': v2, 'K-rules': k_rules, 'M-5': m5}

RULES.update({rid: ported(fn) for rid, fn in PORTED.items()})
TITLES.update({
    'S-1': 'RAW_ACT armed-side parts and no bypass', 'S-2': 'pyro feed through Q120/Q121 only',
    'S-3': 'gates defined off, local bias on the FET layer', 'S-4': 'fitted population and assembly identities',
    'S-5': 'protected switch contacts, clamp and no bypass', 'S-6': 'ports separated from safety copper',
    'S-7': 'servo signals, GND and NC only', 'S-8': 'foreign In1/In2 copper >= 1 mm from barrels and rings',
    'S-9': 'fire and battery current-path widths',
    'S-10': 'fire-net copper gaps on every layer, fills included, default-deny with item-pair exceptions (R10 D-R26-02 / -04)', 'W-1': 'battery wire pads and DB125 pyro terminal',
    'W-2': 'SH connector identities and pin maps', 'LC-1': 'local clearance floors',
    'M-3': 'recorded M3 supports', 'M-6': 'no bottom assembly', 'M-7': 'sensor pose and copper exclusions',
    'M-8': 'courtyard short-edge clearances', 'K-legends': 'R12 legends, designators and Fab references',
    'K-copper': 'via/pad, joints, thermal, paste and pour hygiene', 'K-inner': 'In1 GND, In2 mixed copper',
    'K-reference': 'critical reference coverage', 'K-region': 'one In2 rail region per B signal chain',
    'K-plane': 'In2 fill connectivity and necks', 'K-fill': 'saved fills agree with native refill',
    'K-neighbours': 'PE4 / PC1 ball neighbours cannot raise their gate if bridged (D-R11-85, D-R12-86)',
    'K-power': 'regulator, sense and gate taps survive any one via opening (R12F8-TRI-02; R10 D-R21-02)',
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
