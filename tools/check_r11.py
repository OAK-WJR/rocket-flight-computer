#!/usr/bin/env python3
"""R11 native-CAD contract (M3-ASSY-R11, D-R11-08): R10's contract rules (tools/check_r10.py) re-expressed for R11's
compact six-layer board (F / In1 GND / In2 power / In3 signal / In4 GND / B, D-R11-03), keyed by net, reference and
pad number, never by an R10 coordinate.

usage: <KiCad python3> -I tools/check_r11.py [board.kicad_pcb] [--report out.json] [--fit FIT.json] [--only S-1,M-1]
       [--stage functional|placement|full] [--bom BOM.csv] [--cpl CPL.csv]
exit 0 = every selected rule holds

tools/check.sh runs it after fit_check --profile r11 (--fit). R11 keeps R10's netlist (D-R11-01), so the R10 rule
functions run here on the R11 board wherever they read nets, references and pad numbers only; R10's coordinate tables
are replaced by R11 data (the gate data file R11_DATA, filled by the later stages) or start empty, like route_check's
r11 allowlists. U1's balls come from the R11 pin table (R11_PIN_TABLE, columns 'port' and 'ball' or 'pin'), not R10's
LQFP pin numbers.

Rules (R10's id where it is R10's rule):
  S-1  RAW_ACT pyro bus, named armed-side parts, no bypass (check_r10.s1; DIRECT_ADC balls of PC0 / PC5 from the pin
       table)
  S-2  pyro feed only through the Q120 / Q121 load switch (check_r10.s2)
  S-3  gate networks defined off (check_r10.s3; PC1's ball for ACT_EN_MCU from the pin table)
  S-3c Q120 / Q121 gate bias joined by the FET layer's copper alone (check_r10.local_gate_bias; full stage only)
  S-4  required fitted parts on board, schematic, BOM and CPL; MPN-decoded values (check_r10.s4); the hand-soldered
       wire pads J1 / J121 (D-R11-05) instead on board and schematic, not DNP, excluded from BOM and CPL
  S-5  J400 arming switch contacts behind their 470 k resistors and D402 (check_r10.s5)
  S-6  external ports apart from pyro / arming copper (check_r10.s6)
  S-7  J122 (JST GH 5-pin): contacts 1-4 SERVO1-4_OUT, 5 GND; only its two fixing tabs besides, on GND or no net
  S-8  on In1..In4 no foreign track, fill or drawing within 1.0 mm of a BARREL_NETS barrel wall or of an inner ring
       it keeps (check_r10.s8 over all four inner layers; GND counts for BARREL_GND_HAZARD only)
  S-9  fire / source copper widths on the current path (check_r10.s9; FIRE_NARROW from R11_DATA, empty by default)
  W-1  D-R11-05 wire pads: J1 = plated pads 1 BAT_IN / 2 GND, J121 = plated pads 1 PYRO1_OUT / 2 PYRO1_IGN, no other
       pad; plated barrels (PTH) only
  W-2  D-R11-05 GH ports: J410 / J420 / J440 1 PORT_4V8, 2 GND, 3 *_TX_WIRE, 4 *_RX_WIRE; J9 1-2 CAM_5V, 3-4 GND,
       5 CAM_RX_WIRE, 6 CAM_TX_WIRE; J400 1 BAT_SW_SOURCE, 2 BAT_SW_RETURN; each a JST GH SMnnB-GHS-TB with its two
       fixing tabs on GND or no net
  LC-1 local clearance overrides respect their floors (check_r10.lc1)
  M-1  outline one rectangle from (0, 0), 46 mm wide, <= 56 mm long (D-R11-02); every Edge.Cuts circle 3.2 mm
  M-3  the D-R11-10 supports pinned in R11_DATA 'supports' (centres within 0.01 mm, no other circle) and one within
       6 mm of each corner
  M-5  fit_check --profile r11 clean and bound to this board
  M-6  bottom parts SMD only, >= 1.5 mm from foreign through-hole pads, >= 3.5 mm from an M3 support (check_r10.m6)
  M-7  U4 side, rotation and lever arm as R11_DATA 'imu' records; no via or fill under U4 / U5 on their side
  M-8  courtyards >= 2.5 mm from the rail-less short edges (y = 0 and the outline's far edge; check_r10.m8 with R11_DATA
       'short_edge_queries', empty by default)
  K-legends  check_r10's legend rules on R11 data (D-R11-64): J9's six GH contacts (TERMINAL_PINS_R11), M3-ASSY-R11 the
             only revision (pinned_texts_r11), GPS / RADIO / AUX inside their span along the pin-row axis
  K-copper   vias in pads, overlap-only joints, thermal policy, via paste (check_r9.k_copper, no GAP-3 exemption on
             R11 unless R11_DATA adds one), no pour debris (check_r10.pour_debris)
  K-inner    In1 and In4 GND only; In2 power and GND only; In3 signal routing (no rule on its nets)
  K-reference critical signal samples: F.Cu over In1 GND, B.Cu over In4 GND, In3 over In4 GND (D-R11-03); own
             antipads and S-8 voids excepted; a sample within REF_EDGE_TOL (0.005 mm, KiCad's arc approximation error)
             of the reference fill counts as over it (D-R11-62); no stale critical_reference name
  K-region   every In3 run of a return-required critical net lies over exactly one In2 plane net and over In2 copper;
             each connected In3 chain sees one In2 plane net (R10's B.Cu-over-In2 rule moved to In3: In3 sits 0.1 mm
             under In2 and 0.535 mm over In4 in the LEVIA-H7 stack, r11_plan section 2, so In2's rail regions are its
             nearer plane; F.Cu and B.Cu see only the solid GND of In1 / In4). Any In2 fill counts as a plane: K-inner
             keeps In2 to power and GND
  K-plane    inner power fills (In2, In3) one piece, else >= 2 links of >= 0.5 mm; necks reported (check_r10)
  K-fill     saved fills are current (check_r10.fill_freshness)
  K-rules    R11's own (D-R11-40): m3.kicad_dru SHA-256 pinned (R11_DRU_SHA256), its rules and the .kicad_pro rules and net
             classes held to JLC's six-layer capability floors (R11_JLC_TABLE, R11_DRU_FLOORS, R11_PRO_FLOORS,
             R11_NETCLASS_FLOORS; later-rule overrides judged on layer and condition), PTH hole to inner copper 0.3 mm
             and JLC board holes, rings and NPTH (check_r10.pth_inner_copper / jlc_board_holes)
  K-lands    the project library is the only footprint source; placed paste / mask settings equal the library
  K-width    BAT_IN / RAW_PROTECTED width floor (check_r10.k_width)
  K-power    rail paths (POWER_PATHS_R11: R10's paths by function on R11's topology, O-C2-6) at the IPC-2152 width of
             R10's design currents on each segment's own layer and R11 copper (CU_MM_R11), narrow pin entries only as
             R11_DATA 'power_narrow' entries with a length cap; their via counts and sizes; Q124's fire return;
             R10's single-via-open taps with U1's LQFP pins mapped to R11 balls (single_open_taps_r11, O-C2-5),
             exceptions only from R11_DATA 'single_open_exceptions' (none by default). Schemas: gate_C2.md
  K-ports    port ESD clamps on the wire side, <= 4.5 mm of track from the pin (J9's UART pins 5 / 6 on R11)
  K-loader   ROM-loader pins: LOADER_R11 (R11's own list, keyed by port pin, on U1's balls from the R11 pin table;
             check_r10.LOADER_H74X's pin set; gate_C2.md section 5): no net without an entry, no entry for another
             net or an NC pin, recorded members, decision and case section present

Dropped from check_r10, each for one reason:
  M-2 (optional plate) not a gate. P-11 DB125 wire room: R11 has no screw terminals (fit_check r11 holds the GH plug and
  wire-pad envelopes). F9-1 / F9-2 the hot-plug model and U9's local loops are bound to R10's extracted copper; R11
  re-runs them on its own copper (r11_plan section 1) and adds the rule then. T-1 panel tabs: R10's tab windows are
  coordinates of a 90 mm board. K-contract: r11_sch_check carries R10's net contract onto the balls (stage A gate).
  K-binding: R10's binding note; R11's is a stage E record. K-actuators: check_actuators pins R10's file text.
  K-retained: R10 coordinate proximity of C29 / TP122 / C460 / C461. K-plane's tab bands (R10 coordinates).
"""
import argparse
import csv
from contextlib import ExitStack
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'quality_audit'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r10 as r10                                          # noqa: E402
from check_r10 import patched                                    # noqa: E402

REVISION = 'M3-ASSY-R11'
R11_DIR = ROOT / 'm3_design/r11'
R11_PIN_TABLE = R11_DIR / 'design/pin_table.tsv'
R11_DATA = R11_DIR / 'design/r11_gate_data.json'
BOARD_WIDTH, BOARD_MAX = 46.0, 56.0                              # D-R11-02
INNER = ('In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu')
GND_PLANES = ('In1.Cu', 'In4.Cu')                                # D-R11-03
POWER_LAYER = 'In2.Cu'
SIGNAL_INNER = 'In3.Cu'
PINNED_TEXTS_R11 = (('B.Silkscreen', REVISION),)
GH_PART = re.compile(r'^SM(\d\d)B-GHS-TB')
WIRE_PADS = {'J1': {'1': 'BAT_IN', '2': 'GND'}, 'J121': {'1': 'PYRO1_OUT', '2': 'PYRO1_IGN'}}
GH_PORTS = {
    'J410': {'1': 'PORT_4V8', '2': 'GND', '3': 'GPS_TX_WIRE', '4': 'GPS_RX_WIRE'},
    'J420': {'1': 'PORT_4V8', '2': 'GND', '3': 'RADIO_TX_WIRE', '4': 'RADIO_RX_WIRE'},
    'J440': {'1': 'PORT_4V8', '2': 'GND', '3': 'AUX_TX_WIRE', '4': 'AUX_RX_WIRE'},
    'J9': {'1': 'CAM_5V', '2': 'CAM_5V', '3': 'GND', '4': 'GND', '5': 'CAM_RX_WIRE', '6': 'CAM_TX_WIRE'},
    'J400': {'1': 'BAT_SW_SOURCE', '2': 'BAT_SW_RETURN'},
    'J122': {str(i): n for i, n in enumerate(r10.SERVO_TERMINAL, 1)},
}
# R10's clamps keyed by terminal pin; J9's UART moves from pins 3 / 4 to 5 / 6 (D-R11-05: RXI pin 5, TXO pin 6)
PORT_CLAMPS_R11 = tuple((ref, {'3': '5', '4': '6'}[pin] if ref == 'J9' else pin, clamp, res)
                        for ref, pin, clamp, res in r10.PORT_CLAMPS)
# K-power on R11 (stageC2.md O-C2-6, gate_C2.md). R10's POWER_PATHS by function, re-drawn on R11's topology: R10's
# coordinates, its 1.0 / 0.5 mm IN via, its drawn floors and the 'through' parts that R11's placement moves off the path
# are gone; the design currents (R10 check_r10 K-power comment, parts_budget.json) stay. Each path's tracks must be at
# least the IPC-2152 width for its current at POWER_RISE on that track's own layer and R11 copper (CU_MM_R11; 0.01 mm
# up), so an inner-layer segment needs its 0.5 oz width; a narrower segment passes only inside a pin entry listed in
# R11_DATA 'power_narrow' (power_narrow_entries). Via specs: R11's power via is 0.6 / 0.3 mm (D-R11-15), held to R10's
# 0.5 / 0.3 mm minimum; 'max' caps the vias on a path.
# R11 copper (stageB.md section 3, JLC06161H-3313 table, Datasheet): outer 0.035 mm, inner 0.0152 mm (0.5 oz).
CU_MM_R11 = {'F.Cu': 0.035, 'B.Cu': 0.035, 'In1.Cu': 0.0152, 'In2.Cu': 0.0152, 'In3.Cu': 0.0152, 'In4.Cu': 0.0152}
POWER_RISE = r10.POWER_RISE                                      # 30 C, R10's U9 OUT basis
_PV = dict(drill=0.3, pad=0.5)                                   # R10's power via minimum; R11 draws 0.6 / 0.3
POWER_PATHS_R11 = (
    # J1 is a plated AWG20 wire pad (1.30 mm hole, 2.50 mm land, D-R11-05) whose barrel reaches U9's B.Cu side; U9, C88
    # (its input decoupling, 'at U9') and the path are on B.Cu, so the path takes no via (max 0: R10's 1.0 / 0.5 mm IN
    # via was the DB125's F.Cu-to-B.Cu change, which R11 does not have).
    dict(name='U9 IN', net='BAT_IN', start={'J1': ('1',)}, end={'U9': ('5',)}, through={'C88': ('1',)}, amps=2.9,
         vias=dict(_PV, count=0, max=0, plane=None)),
    dict(name='U9 OUT', net='RAW_PROTECTED', start={'U9': ('6',)}, end=None, through={}, amps=2.9,
         vias=dict(_PV, count=2, plane='In2.Cu')),
    dict(name='U401 IN', net='PORT_5V3', start={'U401': ('9', '10')}, end=None, through={}, amps=1.9,
         vias=dict(_PV, count=2, plane='In2.Cu')),
    dict(name='U401 EN', net='PORT_5V3', start={'U401': ('7',)}, end=None, through={}, floor=0.2,
         vias=dict(_PV, count=2, plane='In2.Cu')),               # an EN input: no design current, R10's 0.2 mm floor
    dict(name='U401 OUT', net='PORT_4V8', start={'U401': ('1', '2')}, end=None, through={}, amps=1.9,
         vias=dict(_PV, count=2, plane='In2.Cu')),
    # C430 is U402's input capacitor, placed 'at U402' (r11_place.tsv)
    dict(name='U402 IN', net='PORT_5V3', start={'U402': ('1',)}, end=None, through={'C430': ('1',)}, amps=1.249,
         vias=dict(_PV, count=2, plane='In2.Cu')),
    # The three identical GH ports (D-R11-05) each drop from pin 1 to the In2 PORT_4V8 band under them (stageC2.md
    # section 5). R10's J420 'through C421' and J440 two-via / F.Cu-only details were R10 drawing details (D-R19-14).
    dict(name='J410 feed', net='PORT_4V8', start={'J410': ('1',)}, end=None, through={}, amps=1.9,
         vias=dict(_PV, count=1, plane='In2.Cu')),
    dict(name='J420 feed', net='PORT_4V8', start={'J420': ('1',)}, end=None, through={}, amps=1.9,
         vias=dict(_PV, count=1, plane='In2.Cu')),
    dict(name='J440 feed', net='PORT_4V8', start={'J440': ('1',)}, end=None, through={}, amps=1.9,
         vias=dict(_PV, count=1, plane='In2.Cu')),
    # U402, C431 and J9 are all on F.Cu; J9 (GH-6) carries the camera supply on pins 1 and 2 (D-R11-05), both on the
    # path; the whole 1.249 A is held on every segment.
    dict(name='CAM_5V out', net='CAM_5V', start={'U402': ('6',)}, end={'J9': ('1', '2')},
         through={'C431': ('1',), 'J9': ('1', '2')}, amps=1.249, vias=dict(_PV, count=0, plane=None)),
    # C84 (F.Cu) to U11 (B.Cu): two vias, as R10 (D-R19-09: an open barrel no longer drops the hold-up)
    dict(name='C84 hold-up', net='VLOGIC', start={'C84': ('1',)}, end={'U11': ('1', '8')}, through={}, amps=1.294,
         vias=dict(_PV, count=2, plane=None)),
    # U11 and C99 are on B.Cu and U2 on F.Cu (R10: all B.Cu, no via), so the trunk changes side: two vias, D-R19-09's
    # rule for a supply feed (one open barrel would stop U2 and with it the whole logic rail)
    dict(name='VLOGIC trunk', net='VLOGIC', start={'U11': ('1', '8')}, end={'U2': ('2', '3')}, through={'C99': ('1',)},
         amps=1.294, vias=dict(_PV, count=2, plane=None)),
    # The bucks' outputs to their In2 regions. R10's C404 / C8 'through' parts sit elsewhere on R11: C404 in the 1210
    # bank at (31.9, 18.9), C8 east of U2 while L1.2 faces west (stageC2.md O-C2-2 b); they reach In2 by their own vias.
    dict(name='U400 OUT', net='PORT_5V3', start={'L400': ('2',)}, end=None, through={}, amps=1.81,
         vias=dict(_PV, count=2, plane='In2.Cu')),
    dict(name='U2 OUT', net='3V3', start={'L1': ('2',)}, end=None, through={}, amps=2.0,
         vias=dict(_PV, count=2, plane='In2.Cu')),
)
PIN_ENTRY_MAX = 2.0     # mm: a 'power_narrow' length cap may not exceed R8-GATE-04's 2 mm narrow-run limit (K-width)


def load_data(path=None):
    """R11_DATA: what the later stages record (imu, supports, fire_narrow, power_narrow, single_open_exceptions,
    short_edge_queries; route_check r11 reads parallel_vias). Missing file: {} (each rule says what it then needs)."""
    path = R11_DATA if path is None else Path(path)
    if not path.is_file():
        return {}
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f'{path}: gate data must be a JSON object')
    return data


def pin_table(path=None):
    """{port: ball} from the R11 pin table: its 'port' and 'r11_ball' columns (R10's 'pin' column there is the LQFP pin
    number, not a ball); '#' lines are comments."""
    path = R11_PIN_TABLE if path is None else Path(path)
    if not path.is_file():
        raise ValueError(f'R11 pin table {path} not found (stage A writes it)')
    with path.open() as f:
        rows = list(csv.DictReader((line for line in f if not line.startswith('#')), delimiter='\t'))
    if not rows or 'r11_ball' not in rows[0] or 'port' not in rows[0]:
        raise ValueError(f'R11 pin table {path} has no port / r11_ball columns')
    return {r['port']: r['r11_ball'] for r in rows if r.get('port') and r.get('r11_ball') not in (None, '', '-')}


def balls(ctx):
    if getattr(ctx, '_balls', None) is None:
        ctx._balls = ctx.port_pin if getattr(ctx, 'port_pin', None) is not None else pin_table()
    return ctx._balls


def lid(board, name):
    return board.GetLayerID(name)


# ======================================================================================================================
# rules
# ======================================================================================================================
def direct_adc(ctx):
    """R10's DIRECT_ADC (the filtered sense nodes PC0 / PC5 touch only their own U1 pin) on R11's balls."""
    b = balls(ctx)
    return {'PYRO1_CONT': b['PC0'], 'ARM1_SENSE': b['PC5']}


def s1(ctx):
    with patched(r10, DIRECT_ADC=direct_adc(ctx)):
        return r10.s1(ctx)


def s2(ctx):
    """check_r10.s2 with the sense nodes' U1 exemption on R11's balls (U1.F1 PC0, U1.H4 PC5): any other U1 pad on an
    armed / RAW_ACT net, or the sense net on a second ball, is still a tie and fails."""
    with patched(r10, DIRECT_ADC=direct_adc(ctx)):
        return r10.s2(ctx)


LOCAL_BIAS = 'by F.Cu copper alone'                     # check_r10.local_gate_bias's copper finding (S-3c)


def s3(ctx, copper=False):
    """check_r10.s3 with PC1's ball in place of the LQFP pin U1.16. The load switches' copper-only gate bias
    (check_r10.local_gate_bias, a routing rule) is S-3c: the placement stage has no copper, and the full stage runs
    both."""
    issues, ev = r10.s3(ctx)
    issues = [i for i in issues if 'U1.16' not in i and (copper or LOCAL_BIAS not in i and 'copper alone' not in i)]
    ball = balls(ctx)['PC1']
    u1 = ctx.fps.get('U1')
    pad = u1.FindPadByNumber(ball) if u1 else None
    if pad is None or pad.GetNetname() != 'ACT_EN_MCU':
        issues.append(f'S-3: independent load-switch enable U1.{ball} (PC1) must be ACT_EN_MCU '
                      f'(is {pad.GetNetname() if pad else None})')
    ev.get('load_enable', {}).pop('U1.16', None)
    return sorted(set(issues)), ev


def s3c(ctx):
    """R18-SAF-02 on R11: Q120 / Q121's gate and source pads reach a 1 k - 100 k gate-source resistor through copper on
    the FET's own layer (check_r10.local_gate_bias)."""
    issues, ev = [], {}
    for fet in ('Q120', 'Q121'):
        found, ev[fet] = r10.local_gate_bias(ctx, fet, r10.PFET_ROLES)
        issues += [i.replace('S-3:', 'S-3c:') for i in found]
    return issues, ev


# D-R11-05: the battery and pyro wire pads are soldered by hand to the harness, so they are on the board and in the
# schematic but outside the JLC BOM and CPL (exclude_from_bom / exclude_from_pos_files). Every other required part keeps
# check_r10's full population rule.
WIRE_PAD_FLAGS = ('exclude_from_bom', 'exclude_from_pos_files')


def wire_pad_population(ctx):
    """(issues): J1 / J121 present on board and schematic, not DNP, not board-only, value not DNP, and excluded from the
    BOM and position files on both (so no assembly upload lists them); absent from a supplied BOM / CPL."""
    import pcbnew
    from sexpr import read, properties
    issues = []
    flags = {'dnp': pcbnew.FP_DNP, 'board_only': pcbnew.FP_BOARD_ONLY,
             'exclude_from_bom': pcbnew.FP_EXCLUDE_FROM_BOM, 'exclude_from_pos_files': pcbnew.FP_EXCLUDE_FROM_POS_FILES}
    for ref in sorted(WIRE_PADS):
        f = ctx.fps.get(ref)
        if f is None:
            issues.append(f'{ref}: wire-pad part missing from the board')
            continue
        on = {k for k, bit in flags.items() if f.GetAttributes() & bit}
        if on & {'dnp', 'board_only'} or f.GetValue().strip().upper() in ('DNP', 'NC', 'NF', 'NOFIT'):
            issues.append(f'{ref}: wire-pad part not fitted ({sorted(on & {"dnp", "board_only"})}, value {f.GetValue()})')
        missing = [k for k in WIRE_PAD_FLAGS if k not in on]
        if missing:
            issues.append(f'{ref}: wire pads are hand-soldered (D-R11-05) and must be {missing} (a JLC upload would '
                          'list them)')
    sch = Path(ctx.board_path).with_suffix('.kicad_sch') if ctx.board_path else None
    if sch is not None and sch.is_file():
        found = {}
        pending, seen = [sch], set()
        while pending:
            path = pending.pop().resolve()
            if path in seen:
                continue
            seen.add(path)
            tree = read(path.read_text())
            for sheet in tree.children('sheet'):
                pending.append(path.parent / properties(sheet)['Sheetfile'].items[2].atom)
            for node in tree.children('symbol'):
                props = properties(node)
                if 'Reference' in props and props['Reference'].items[2].atom in WIRE_PADS:
                    found[props['Reference'].items[2].atom] = {k: node.children(k)[0].items[1].atom
                                                               for k in ('dnp', 'in_bom', 'on_board') if node.children(k)}
        for ref in sorted(WIRE_PADS):
            got = found.get(ref)
            if got is None:
                issues.append(f'schematic: {ref} wire-pad symbol missing')
            elif got.get('dnp') == 'yes' or got.get('on_board') == 'no':
                issues.append(f'schematic: {ref} wire-pad symbol not fitted ({got})')
            elif got.get('in_bom') != 'no':
                issues.append(f'schematic: {ref} wire pads must be in_bom no (D-R11-05)')
    elif sch is not None:
        issues.append(f'schematic {sch} not found')
    for name, path in (('BOM', ctx.bom), ('CPL', ctx.cpl)):
        if path:
            listed = {ref.strip() for row in csv.DictReader(Path(path).read_text().splitlines())
                      for ref in (row.get('Designator') or '').split(',') if ref.strip()}
            issues += [f'{name}: hand-soldered wire pads {ref} are in the JLC upload' for ref in sorted(WIRE_PADS)
                       if ref in listed]
    return issues


def s4(ctx):
    """check_r10.s4 with the required set less the wire pads (J1 / J121), which wire_pad_population holds instead."""
    required = frozenset(r10.REQUIRED_FITTED) - set(WIRE_PADS)
    fns = (r10.board_population, r10.population)
    old = [f.__defaults__ for f in fns]
    r10.board_population.__defaults__ = (required,)
    r10.population.__defaults__ = (required, False)
    try:
        with patched(r10, REQUIRED_FITTED=required):
            issues, ev = r10.s4(ctx)
    finally:
        for f, d in zip(fns, old):
            f.__defaults__ = d
    issues += [f'S-4: {i}' for i in wire_pad_population(ctx)]
    ev['wire_pads'] = sorted(WIRE_PADS)
    return issues, ev


def connector_pads(ctx, ref, want, rid, tabs=True):
    """(issues, evidence): `ref`'s numbered pads are exactly `want` (number -> net); every other pad is a fixing tab
    (non-numeric number) on GND or no net, at most two."""
    f = ctx.fps.get(ref)
    if f is None:
        return [f'{rid}: {ref} missing'], {}
    issues, got, extra = [], {}, []
    for p in f.Pads():
        n = p.GetNumber()
        if n.isdigit():
            if n in got:
                issues.append(f'{rid}: {ref} has two pads numbered {n}')
            got[n] = p.GetNetname()
        else:
            extra.append((n, p.GetNetname()))
    if got != want:
        issues.append(f'{rid}: {ref} contacts {dict(sorted(got.items()))}; required {want}')
    if tabs:
        if len(extra) > 2:
            issues.append(f'{rid}: {ref} has {len(extra)} unnumbered pads; a GH header has two fixing tabs')
        for n, net in extra:
            if net not in ('', 'GND'):
                issues.append(f'{rid}: {ref} fixing tab {n or "(unnumbered)"} is on {net}; GND or no net only')
    elif extra:
        issues.append(f'{rid}: {ref} has unnumbered pads {[n for n, _ in extra]}')
    return issues, dict(contacts=got, tabs=extra)


def s7(ctx):
    return connector_pads(ctx, 'J122', GH_PORTS['J122'], 'S-7')


def w1(ctx):
    import pcbnew
    issues, ev = [], {}
    for ref, want in WIRE_PADS.items():
        found, ev[ref] = connector_pads(ctx, ref, want, 'W-1', tabs=False)
        issues += found
        f = ctx.fps.get(ref)
        for p in (f.Pads() if f else ()):
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
                issues.append(f'W-1: {ref}.{p.GetNumber()} must be a plated wire pad (PTH), D-R11-05')
    return issues, ev


def w2(ctx):
    issues, ev = [], {}
    for ref, want in GH_PORTS.items():
        if ref == 'J122':
            continue
        found, ev[ref] = connector_pads(ctx, ref, want, 'W-2')
        issues += found
    for ref in GH_PORTS:
        f = ctx.fps.get(ref)
        part = f.GetFieldText('Manufacturer Part') if f is not None and f.HasField('Manufacturer Part') else ''
        m = GH_PART.match(part or '')
        if f is not None and (m is None or int(m.group(1)) != len(GH_PORTS[ref])):
            issues.append(f'W-2: {ref} Manufacturer Part {part!r} is not the {len(GH_PORTS[ref])}-circuit side-entry '
                          f'JST GH header SM{len(GH_PORTS[ref]):02d}B-GHS-TB (D-R11-05)')
    return issues, ev


def barrel_rings(board, nets=r10.BARREL_NETS, layers=INNER):
    """[(label, net, layer, SHAPE)] of the inner ring each plated barrel of `nets` keeps on In1..In4."""
    import pcbnew
    out = []
    items = [(f'via ({pcbnew.ToMM(t.GetPosition().x):.3f}, {pcbnew.ToMM(t.GetPosition().y):.3f})', t)
             for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() in nets]
    items += [(f'{f.GetReference()}.{p.GetNumber()}', p) for f in board.GetFootprints() for p in f.Pads()
              if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname() in nets]
    for label, item in items:
        for name in layers:
            lay = board.GetLayerID(name)
            if item.IsOnLayer(lay) and item.FlashLayer(lay):
                out.append((f'{label} inner ring', item.GetNetname(), lay, item.GetEffectiveShape(lay)))
    return out


def s8(ctx, gap=r10.BARREL_GAP, gnd_hazard=r10.BARREL_GND_HAZARD, layers=INNER):
    """check_r10.s8 over every inner layer of the six-layer stack (D-R11-08)."""
    import pcbnew
    import check_r8 as r8
    inner = {ctx.board.GetLayerID(n) for n in layers}
    inner &= set(ctx.board.GetEnabledLayers().CuStack())
    barrels = [(label, net, shape, None) for label, net, shape in r10.barrel_shapes(ctx.board)]
    barrels += [(label, net, shape, lay) for label, net, lay, shape in barrel_rings(ctx.board, layers=layers)
                if lay in inner]
    others = [(label, net, lay, shape) for _, lay, shape, _, pad, net, label in r10.copper_nodes(ctx.board)
              if lay in inner]
    worst = {}
    for blabel, bnet, bshape, blay in barrels:
        for label, net, lay, shape in others:
            if net == bnet or (net == 'GND' and bnet not in gnd_hazard) or (blay is not None and lay != blay) \
                    or not pcbnew.SHAPE.Collide(bshape, shape, pcbnew.FromMM(gap) - 1):
                continue
            g = r8.min_gap(bshape, shape, gap + 1)
            g = 0.0 if g is None else g
            key = (blabel, net, ctx.board.GetLayerName(lay))
            if key not in worst or g < worst[key]:
                worst[key] = g
    issues = [f'S-8: {net} copper on {lay} is {g:.3f} mm from the {blabel} '
              f'{"" if blabel.endswith("inner ring") else "barrel "}of {next(b[1] for b in barrels if b[0] == blabel)}'
              f' (minimum {gap} mm)' for (blabel, net, lay), g in sorted(worst.items())]
    return issues, dict(inner_layers=sorted(ctx.board.GetLayerName(x) for x in inner),
                        barrels=sum(1 for b in barrels if b[3] is None),
                        inner_rings=sum(1 for b in barrels if b[3] is not None), gap_mm=gap,
                        near={f'{k[0]} / {k[1]} / {k[2]}': round(v, 3) for k, v in sorted(worst.items())})


def s9(ctx):
    narrow = [(e[0], e[1], e[2], e[3], tuple(e[4]), e[5]) for e in ctx.data.get('fire_narrow', [])]
    return r10.s9(ctx, narrow=narrow)


def m1(ctx):
    with patched(r10, BOARD_WIDTH=BOARD_WIDTH, BOARD_MAX=BOARD_MAX):
        issues, ev = r10.m1(ctx)
    return [i.replace('the P1 ', 'the D-R11-02 ') for i in issues], ev


SUPPORT_TOL = r10.SUPPORT_TOL


def m3(ctx, tol=SUPPORT_TOL):
    """D-R11-10: the supports R11_DATA 'supports' pins (four corner M3 holes), each one Edge.Cuts circle centred within
    `tol`, no other circle, and fit_check's corner rule (one support within 6 mm of each corner). Without a pin the rule
    fails: an unpinned support could move unreviewed."""
    import pcbnew
    import fit_check as fc
    mm = pcbnew.ToMM
    holes = [(mm(d.GetCenter().x), mm(d.GetCenter().y)) for d in ctx.board.GetDrawings()
             if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE]
    _, _, corner = fc.corner_supports(holes, ctx.outline, [])
    issues = [f'M-3: {i}' for i in corner]
    pinned = [tuple(map(float, p)) for p in ctx.data.get('supports', [])]
    if not pinned:
        issues.append('M-3: R11_DATA pins no supports (D-R11-10 records them)')
    for want in pinned:
        near = [h for h in holes if math.dist(h, want) <= tol]
        if len(near) != 1:
            issues.append(f'M-3: the D-R11-10 support ({want[0]:g}, {want[1]:g}) needs one Edge.Cuts circle centred '
                          f'within {tol} mm (found {len(near)})')
    issues += [f'M-3: Edge.Cuts circle at ({h[0]:.3f}, {h[1]:.3f}) is not a pinned support' for h in holes
               if pinned and not any(math.dist(h, w) <= tol for w in pinned)]
    return issues, dict(centres_mm=sorted((round(x, 4), round(y, 4)) for x, y in holes),
                        pinned_mm=[list(p) for p in pinned], tolerance_mm=tol)


def m5(ctx, board_sha=None):
    rep = ctx.fit()
    issues = [f'M-5: fit_check: {i}' for i in rep.get('issues', [])]
    if rep.get('profile') != 'r11':
        issues.append(f'M-5: fit report profile {rep.get("profile")!r}; R11 needs fit_check --profile r11')
    if ctx.fit_given and board_sha and rep.get('board_sha256') != board_sha:
        issues.append('M-5: the fit report is not bound to this board (board_sha256)')
    return issues, dict(width_mm=rep.get('width_mm'), length_mm=rep.get('length_mm'), supports=rep.get('supports'),
                        gh_ports=rep.get('gh_ports'))


def m7(ctx):
    import check_r9 as r9
    imu = ctx.data.get('imu')
    if not isinstance(imu, dict) or not {'rotation', 'lever_mm'} <= imu.keys():
        return ['M-7: R11_DATA has no imu record (rotation, lever_mm[, tol_mm]); stage B records U4\'s pose and axis '
                'map with its decision'], {}
    rev = ctx.board.GetTitleBlock().GetRevision()
    with patched(r9, IMU_ROTATION={**r9.IMU_ROTATION, rev: float(imu['rotation'])}, IMU_LEVER=math.inf):
        issues, ev = r9.m7(ctx)
    u4 = ctx.fps.get('U4')
    if u4 is not None:
        lever = r10.pcbnew_mm(u4.GetPosition().x) - 23.0
        ev['imu_lever_arm_signed_mm'] = round(lever, 3)
        tol = float(imu.get('tol_mm', 0.05))
        if abs(lever - float(imu['lever_mm'])) > tol:
            issues.append(f'M-7: U4 centre x offset from the roll axis (x 23) is {lever:.3f} mm, recorded '
                          f'{imu["lever_mm"]} +/- {tol} mm (R11_DATA imu)')
    return issues, ev


def m8(ctx):
    return r10.m8(ctx, queries={k: tuple(v) for k, v in ctx.data.get('short_edge_queries', {}).items()})


# D-R11-64: K-legends on R11. R10's rules run unchanged except where they encode R10 geometry or R10 text:
#  * TERMINAL_PINS_R11: J9 is a JST GH 6-pin on R11 (D-R11-05: 1-2 CAM_5V, 3-4 GND, 5 CAM_RX_WIRE, 6 CAM_TX_WIRE), so
#    R10's four-pin J9 legends would name the wrong contacts; every other terminal keeps R10's words and pins.
#  * the revision: check_r10.pinned_texts binds R10's PINNED_TEXTS as its default argument and names M3-ASSY-R10 as
#    the only revision, so patching the module constant alone never checked R11's text (R11 must carry exactly
#    M3-ASSY-R11 on B.Silkscreen and no other revision legend).
#  * WORD_SPAN: R10's GPS / RADIO / AUX words must lie inside their terminal's courtyard span along the pin row; R10's
#    rows run along y, R11's GH rows along x (D-R11-12), so the span is taken on each connector's own pin-row axis.
TERMINAL_PINS_R11 = tuple((ref, (('1', '5V4'), ('2', '5V4'), ('3', 'GND'), ('4', 'GND'), ('5', 'RXI'), ('6', 'TXO'))
                           if ref == 'J9' else pins) for ref, pins in r10.TERMINAL_PINS_R10)
WORD_SPAN_R11 = dict(r10.WORD_SPAN_R10)                          # GPS J410, RADIO J420, AUX J440


def pinned_texts_r11(board, _base=r10.pinned_texts):
    """check_r10.pinned_texts with R11's pinned text and R11 as the only revision legend."""
    import pcbnew
    out = [i for i in _base(board, pinned=PINNED_TEXTS_R11) if not i.startswith('revision legends ')]
    revs = set()
    for item in r10.legend_items(board):
        if isinstance(item, pcbnew.PCB_TEXT) and (not hasattr(item, 'IsVisible') or item.IsVisible()) \
                and re.match(r'^M3-ASSY-R\d+$', item.GetText()):
            revs.add(item.GetText())
    return out + [f'revision legends {sorted(revs)}: only {REVISION} allowed' for _ in [0] if sorted(revs) != [REVISION]]


def word_spans_r11(board, spans=WORD_SPAN_R11, margin=None):
    """(issues, evidence): each span word's ink lies inside its own connector's courtyard span along that connector's
    pin-row axis (the axis along which its numbered pads spread) by WORD_SPAN_MARGIN (D-R19-06's rule, R11 axis)."""
    import pcbnew
    margin = r10.WORD_SPAN_MARGIN if margin is None else margin
    mm = pcbnew.ToMM
    issues, ev = [], {}
    for item in r10.legend_items(board):
        if (not isinstance(item, (pcbnew.PCB_TEXT, pcbnew.PCB_TEXTBOX))
                or item.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS)
                or (hasattr(item, 'IsVisible') and not item.IsVisible())):
            continue
        word = item.GetText().strip()
        f = board.FindFootprintByReference(spans.get(word, ''))
        if f is None:
            continue
        pads = [p.GetPosition() for p in f.Pads() if p.GetNumber()]
        axis = 0 if max(p.x for p in pads) - min(p.x for p in pads) >= max(p.y for p in pads) - min(p.y for p in pads) \
            else 1
        c = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd).BBox()
        lo, hi = (mm(c.GetLeft()), mm(c.GetRight())) if axis == 0 else (mm(c.GetTop()), mm(c.GetBottom()))
        poly = pcbnew.SHAPE_POLY_SET()
        item.TransformShapeToPolygon(poly, item.GetLayer(), 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
        q = poly.BBox()
        a, z = (mm(q.GetLeft()), mm(q.GetRight())) if axis == 0 else (mm(q.GetTop()), mm(q.GetBottom()))
        inside = min(a - lo, hi - z)
        ev[word] = dict(connector=f.GetReference(), axis='xy'[axis], inside_mm=round(inside, 3))
        if inside < margin - r10.EPS:
            issues.append(f'{f.GetReference()}: word legend {word!r} lies {inside:.3f} mm inside its courtyard span '
                          f'along the pin row ({"xy"[axis]} {lo:.3f} .. {hi:.3f}); it must be inside by {margin} mm '
                          '(D-R19-06, R11 axis: D-R11-64)')
    return issues, ev


def k_legends(ctx):
    words = r10.word_legends
    with patched(r10, PINNED_TEXTS=PINNED_TEXTS_R11, TERMINAL_PINS_R10=TERMINAL_PINS_R11,
                 pinned_texts=pinned_texts_r11,
                 word_legends=lambda board, **kw: words(board, spans={}, **kw)):
        issues, ev = r10.k_legends(ctx)
        spans, span_ev = word_spans_r11(ctx.board)
    return issues + spans, dict(ev, word_spans=span_ev)


def k_copper(ctx):
    import check_r9 as r9
    issues, ev = r9.k_copper(ctx)
    debris, debris_ev = r10.pour_debris(ctx.board)
    return issues + [f'K-copper: {i}' for i in debris], dict(ev, pour_pieces=debris_ev)


def k_inner(ctx):
    """In1 / In4 GND only; In2 power and GND only (route_check's r10 classes, which r11 reads); In3 free."""
    import pcbnew
    import route_check as rc
    b = ctx.board
    gnd_only = {lid(b, n) for n in GND_PLANES}
    power = lid(b, POWER_LAYER)

    def bad(layer, net):
        return (layer in gnd_only and net != 'GND') or (layer == power and rc.net_class(net) != 'power')
    issues, length = [], {}
    routed = set()
    for t in b.GetTracks():
        routed.add(t.m_Uuid.AsString())
        if t.GetClass() == 'PCB_VIA' or not bad(t.GetLayer(), t.GetNetname()):
            continue
        name = b.GetLayerName(t.GetLayer())
        length[name] = length.get(name, 0.) + pcbnew.ToMM(t.GetLength())
        issues.append(f'{name} track of {t.GetNetname()}: In1 / In4 carry GND only; In2 power and GND only')
    for key, layer, shape, box, pad, net, label in r10.copper_nodes(b):
        if pad is None and key not in routed and bad(layer, net):
            issues.append(f'{b.GetLayerName(layer)} {label} of {net or "(no net)"}: In1 / In4 carry GND only; '
                          'In2 power and GND only')
    return [f'K-inner: {i}' for i in issues], dict(length_mm=length)


def reference_map(board):
    """{signal layer id: (reference layer id, plane nets)} of the R11 stack (D-R11-03); In3's In2 side is K-region's."""
    return {lid(board, 'F.Cu'): (lid(board, 'In1.Cu'), ('GND',)),
            lid(board, 'B.Cu'): (lid(board, 'In4.Cu'), ('GND',)),
            lid(board, SIGNAL_INNER): (lid(board, 'In4.Cu'), ('GND',))}


# D-R11-62 (gate lane): a copper edge drawn exactly at the 0.25 mm hole clearance from another net's via lies exactly on
# the GND plane's antipad boundary, which KiCad also draws at that hole clearance; the fill approximates the antipad
# circle by a polygon whose chords lie outside the circle by up to the board's arc error (m_MaxError, 0.005 mm on R11),
# so an exact point-in-polygon test reads such an edge sample as off the plane by up to 0.005 mm. A sample within
# REF_EDGE_TOL of the fill is over it. Measured on board 4e552ef4...: 248 samples, all 0.250-0.252 mm from a foreign via
# hole wall and at most 0.0005 mm inside the void. A sample further inside a void than the tolerance still fails.
REF_EDGE_TOL = 0.005             # mm: KiCad's default arc approximation error (the R11 board's m_MaxError)


def ref_inside(polys, x, y, tol=REF_EDGE_TOL):
    """True when (x, y) mm lies on the fill or within `tol` mm of it. SHAPE_POLY_SET.Collide measures to the outlines
    and to the holes (Contains' accuracy argument does not widen a hole's edge, measured on KiCad 10)."""
    import pcbnew
    return polys.Collide(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)), pcbnew.FromMM(tol))


def k_reference(ctx, tol=REF_EDGE_TOL):
    import critical_reference as cr
    import pcbnew
    b = ctx.board
    refs = reference_map(b)
    nets = {n for n in set(cr.R6_NETS + cr.EXTENDED_R10 + cr.R10_PORT_NETS + cr.R10_SD_NETS) | r10.signal_critical_nets(b)
            if not cr.r10_slow_return_net(n)}
    samples = cr.samples(b, nets, refs)
    fill = cr.fills(b, refs)
    empty = pcbnew.SHAPE_POLY_SET()
    strict = [s for s in samples if not cr.inside(fill.get(s[1], empty), s[2], s[3])]
    missing = [s for s in strict if not ref_inside(fill.get(s[1], empty), s[2], s[3], tol)]
    own, voids = r10.own_antipads(b), r10.own_barrel_voids(b)
    loose = [(s[0], b.GetLayerName(s[1]), s[2], s[3]) for s in missing
             if not r10.in_own_antipad(own, s[0], s[2], s[3]) and not r10.in_own_antipad(voids, s[0], s[2], s[3])]
    issues = []
    if loose:
        issues.append(f'{len(loose)} critical signal samples lack adjacent reference copper outside their own via '
                      f'antipads (F over In1 GND, B over In4 GND, In3 over In4 GND), e.g. {loose[:3]}')
    stale = cr.r10_stale_names({str(n) for n in b.GetNetsByName().keys()})
    issues += [f'stale critical_reference.{lst} entry {name!r}: no such net on the board' for lst, name in stale]
    return [f'K-reference: {i}' for i in issues], dict(samples=len(samples), unreferenced=len(missing),
                                                       loose=len(loose), edge_tolerance_mm=tol,
                                                       on_boundary=len(strict) - len(missing),
                                                       board_max_error_mm=pcbnew.ToMM(b.GetDesignSettings().m_MaxError))


def region_issues(board, track_layer=SIGNAL_INNER, plane_layer=POWER_LAYER):
    """check_r10.region_issues with the signal layer In3 and the plane layer In2 (R10: B.Cu over In2): every run and
    SMD pad of a return-required critical net on `track_layer` lies over exactly one `plane_layer` plane net and over
    its copper (own via antipads, own pad voids, S-8 voids and other nets' via clearance holes excepted); each connected
    chain sees one plane net."""
    import pcbnew
    tl, pl = board.GetLayerID(track_layer), board.GetLayerID(plane_layer)
    import types
    proxy = types.ModuleType('pcbnew')                 # pcbnew with B_Cu / In2_Cu re-pointed, for that one call
    proxy.__dict__.update({k: v for k, v in pcbnew.__dict__.items() if not k.startswith('__')})
    proxy.B_Cu, proxy.In2_Cu = tl, pl
    saved = sys.modules['pcbnew']
    sys.modules['pcbnew'] = proxy
    try:
        issues, ev = r10.region_issues(board)
    finally:
        sys.modules['pcbnew'] = saved
    issues = [i.replace('B.Cu', track_layer).replace('In2', plane_layer.split('.')[0]) for i in issues]
    return issues, dict(ev, track_layer=track_layer, plane_layer=plane_layer)


def k_region(ctx):
    issues, ev = region_issues(ctx.board)
    return [f'K-region: {i}' for i in issues], ev


PLANE_LAYERS_R11 = ('In2.Cu', 'In3.Cu')


def k_plane(ctx):
    issues, ev = [], {}
    for (net, layer), pieces in sorted(r10.plane_pieces(ctx.board, layers=PLANE_LAYERS_R11).items()):
        areas = [round(p.Area() / 1e12, 2) for p in pieces]
        ev[f'{net} {layer}'] = areas
        if len(pieces) < 2:
            continue
        main = max(range(len(pieces)), key=lambda i: areas[i])
        count = r10.plane_links(ctx.board, net, pieces)
        for i, area in enumerate(areas):
            if i != main and count[i] < r10.PLANE_LINKS:
                bb = pieces[i].BBox()
                issues.append(f'K-plane: {net} on {layer} fills as {len(pieces)} pieces; the {area} mm^2 piece at '
                              f'({r10.pcbnew_mm(bb.GetCenter().x):.2f}, {r10.pcbnew_mm(bb.GetCenter().y):.2f}) has '
                              f'{count[i]} link(s) of >= {r10.PLANE_LINK_W} mm outer copper (minimum {r10.PLANE_LINKS})')
    necks, neck_ev = r10.plane_necks(ctx.board, layers=PLANE_LAYERS_R11)
    return issues + necks, dict(pieces_mm2=ev, necks=neck_ev)


# K-rules for R11 (D-R11-40, gate_C2.md section 4). R10's k_rules held R11's board to R10's floors (R23-GATE-03:
# 0.15 mm clearance and track, 0.5 / 0.3 mm via, 0.25 mm hole to hole); R11 is a six-layer JLC board with a TFBGA-100
# and its own floors (D-R11-15). Every figure below is from JLCPCB's capability page,
# https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-11-03; the page gives multilayer figures, which cover the
# six-layer board; it has no separate six-layer column). A floor here is never below JLC's figure.
#   "Traces" section:
#     Min. track width and spacing (1 oz), multilayer: 0.09 / 0.09 mm ("3 mil is acceptable in BGA fan-outs": not used)
#     BGA pad to trace clearance >= 0.1 mm (min. 0.09 mm for multilayer boards)
#     Inner layer via hole to copper clearance 0.2 mm; Via hole to track 0.2 mm
#     Inner layer PTH pad hole to copper clearance 0.3 mm (R21-GATE-02); PTH to track min 0.28 mm (0.35 recommended)
#     PTH annular ring, multilayer 1 oz: recommended 0.20 mm, absolute minimum 0.15 mm; NPTH pad annular ring >= 0.45 mm
#     NPTH to track 0.2 mm
#   "Drilling" section:
#     Drill diameter, multilayer: 0.15 - 6.3 mm; Min. via hole size / diameter, multilayer: 0.15 mm / 0.25 mm
#     (via diameter 0.1 mm over the hole: a 0.05 mm via ring); Via hole-to-hole spacing 0.2 mm; Pad hole-to-hole
#     spacing 0.45 mm; Min. non-plated holes 0.50 mm
#   "Outline" section: copper clearance from routed board edges >= 0.2 mm
# The DRU is pinned by SHA-256 here (a reviewed DRU change re-pins R11_DRU_SHA256 in this file; R11_DATA cannot re-pin
# it). Its rules are read as KiCad reads them (check_r10.dru_rules) and held to R11_DRU_FLOORS and R11_JLC_TABLE.
R11_DRU_SHA256 = 'b483f287ef14c506438357c894d7ddbf4e93d58e3c789dee913a7a7effbdf0ca'   # m3_design/r11/m3.kicad_dru
JLC_URL = 'https://jlcpcb.com/capabilities/pcb-capabilities'
# Board design-rule floors (.kicad_pro 'rules'): D-R11-15's figures where they are stricter than JLC's, else JLC's.
R11_PRO_FLOORS = {
    'min_clearance': 0.1,                  # D-R11-15 0.1 mm; JLC Traces 0.09 mm
    'min_track_width': 0.1,                # D-R11-15 0.1 mm; JLC Traces 0.09 mm
    'min_via_diameter': 0.25,              # JLC Drilling: via 0.15 / 0.25 mm
    'min_via_annular_width': 0.05,         # JLC Drilling: via diameter 0.1 mm over the hole
    'min_through_hole_diameter': 0.15,     # JLC Drilling: multilayer drill 0.15 mm
    'min_hole_clearance': 0.2,             # JLC Traces: via hole to track / inner via hole to copper 0.2 mm
    'min_hole_to_hole': 0.2,               # JLC Drilling: via hole-to-hole 0.2 mm
    'min_copper_edge_clearance': 0.5,      # R10's 0.5 mm kept; JLC Outline 0.2 mm
    'min_microvia_diameter': 0.2,          # JLC Drilling: min drill 0.1 mm on 2+ layers, plus the 0.1 mm via ring rule;
    'min_microvia_drill': 0.1,             # R11 draws none (D-R11-15), and jlc_board_holes holds every via to 0.15 mm
    # REQUIREMENTS M2 silkscreen floors and the project's spoke count, as R10 (R18-GATE-06)
    'min_text_height': 1.0, 'min_text_thickness': 0.15, 'min_silk_clearance': 0.15, 'min_resolved_spokes': 2}
# Net-class floors (.kicad_pro net_settings classes): the same figures per class.
R11_NETCLASS_FLOORS = {'clearance': 0.1, 'track_width': 0.1, 'via_diameter': 0.25, 'via_drill': 0.15}
R11_NETCLASS_VIA_RING = 0.05
# DRU constraint floors (every (min ...) in m3.kicad_dru, whatever its rule or condition)
R11_DRU_FLOORS = {
    'clearance': 0.1, 'track_width': 0.1,                         # D-R11-15; JLC Traces 0.09 mm
    'edge_clearance': 0.5,                                        # R10's 0.5 mm; JLC Outline 0.2 mm
    'annular_width': 0.05,                                        # JLC Drilling: via ring; PTH pads by R11_JLC_TABLE
    'via_diameter': 0.25, 'hole_size': 0.15,                      # JLC Drilling: 0.15 / 0.25 mm, drill 0.15 mm
    'hole_clearance': 0.20,                                       # JLC Traces: via hole to track 0.2 mm
    'hole_to_hole': 0.20,                                         # JLC Drilling: via hole-to-hole 0.2 mm
    'text_height': 1.0, 'text_thickness': 0.15, 'silk_clearance': 0.15,     # REQUIREMENTS M2
    'thermal_relief_gap': 0.1, 'thermal_spoke_width': 0.1,        # copper gap / width: D-R11-15; JLC Traces 0.09 mm
    'physical_clearance': 0.1, 'diff_pair_gap': 0.1,              # D-R11-15; JLC Traces 0.09 mm
    'physical_hole_clearance': 0.20,                              # JLC Traces 0.2 mm
    'courtyard_clearance': 0.0}
# JLC rows held by named DRU rules: (what, JLC's row, DRU rule, layer, condition, constraint, JLC minimum mm), as R10's
# JLC_HOLE_TABLE (whose four rows are kept: PTH to inner copper 0.3 mm stays, R21-GATE-02) plus R11's floor rules.
R11_JLC_TABLE = r10.JLC_HOLE_TABLE + (
    ('copper clearance', 'Traces: Min. track width and spacing (1 oz) multilayer 0.09 / 0.09 mm',
     'R11 board floor: copper clearance', None, None, 'clearance', 0.09),
    ('track width', 'Traces: Min. track width and spacing (1 oz) multilayer 0.09 / 0.09 mm',
     'R11 board floor: track width', None, None, 'track_width', 0.09),
    ('via drill', 'Drilling: Min. via hole size / diameter, multilayer 0.15 mm / 0.25 mm', 'R11 board floor: via drill',
     None, "A.Type == 'Via'", 'hole_size', 0.15),
    ('via diameter', 'Drilling: Min. via hole size / diameter, multilayer 0.15 mm / 0.25 mm',
     'R11 board floor: via diameter', None, "A.Type == 'Via'", 'via_diameter', 0.25),
    ('via hole to hole', 'Drilling: Via hole-to-hole spacing 0.2 mm', 'R11 board floor: via hole to hole', None,
     "A.Type == 'Via' && B.Type == 'Via'", 'hole_to_hole', 0.20),
    ('PTH annular ring', 'Traces: PTH annular ring, multilayer 1 oz, absolute minimum 0.15 mm',
     'R11 board floor: PTH pad annular ring', None, "A.Type == 'Pad' && A.Pad_Type == 'Through-hole'",
     'annular_width', 0.15),
)
_COND_FACT = re.compile(r"^\s*([AB])\.(Type|Pad_Type)\s*==\s*'([^']*)'\s*$")


def _top_split(cond, op):
    """`cond` split on `op` ('&&' or '||') outside parentheses and quotes."""
    parts, depth, i, start, quote = [], 0, 0, 0, False
    while i < len(cond):
        c = cond[i]
        if c == "'":
            quote = not quote
        elif not quote and c == '(':
            depth += 1
        elif not quote and c == ')':
            depth -= 1
        elif not quote and depth == 0 and cond.startswith(op, i):
            parts.append(cond[start:i])
            i += len(op)
            start = i
            continue
        i += 1
    parts.append(cond[start:])
    return parts


def condition_facts(cond):
    """{(item, field): value} that `cond` requires: its top-level '&&' terms of the form A/B.Type / Pad_Type == 'lit'
    (a Pad_Type also requires Type 'Pad'). A term of any other form, and a condition with a top-level '||', adds no
    fact, so the facts are never narrower than the condition (a sound basis for 'cannot match')."""
    if not cond or len(_top_split(cond, '||')) > 1:
        return {}
    facts = {}
    for term in _top_split(cond, '&&'):
        m = _COND_FACT.match(term)
        if not m:
            continue
        item, field, value = m.groups()
        for key, v in (((item, field), value),) + ((((item, 'Type'), 'Pad'),) if field == 'Pad_Type' else ()):
            if facts.get(key, v) != v:
                return None                                      # self-contradictory: the condition matches nothing
            facts[key] = v
    return facts


def conditions_meet(pinned, later):
    """True when some item pair can satisfy both conditions, so a later rule can override the pinned one (D-R11-40).
    KiCad tests a two-item rule's condition both ways round (A, B) and (B, A), so both orders are tried; a condition
    that matches nothing meets nothing."""
    p, q = condition_facts(pinned), condition_facts(later)
    if p is None or q is None:
        return False
    for swap in (False, True):
        qq = {(('B' if k[0] == 'A' else 'A') if swap else k[0], k[1]): v for k, v in q.items()}
        if all(p.get(k, v) == v for k, v in qq.items()):
            return True
    return False


def jlc_table_r11(text, table=R11_JLC_TABLE, floor=r10.JLC_HOLE_FLOOR, floors=None):
    """check_r10.jlc_hole_table on R11's table and floors, with the later-rule test limited to rules that can meet the
    pinned rule on both layer (check_r10.dru_layers_meet) and condition (conditions_meet). The rest of R10's checks
    (one rule per row, its layer and condition pinned, its minimum at least JLC's, no hole rule below JLC's least hole
    figure, every minimum readable and at least its floor, severity error only) run unchanged."""
    floors = R11_DRU_FLOORS if floors is None else floors
    issues, ev = r10.jlc_hole_table(text, table=table, floor=floor, floors=floors)
    issues = [i for i in issues if ' follows "' not in i]                # R10's condition-blind test, replaced below
    named = [r for r in r10.dru_rules(text) if r['name']]
    for what, row, name, layer, cond, constraint, need in table:
        hits = [i for i, r in enumerate(named) if r['name'] == name]
        if len(hits) != 1:
            continue
        for later in named[hits[0] + 1:]:
            v = later['mins'].get(constraint)
            if (v is not None and v < need - 1e-9 and r10.dru_layers_meet(layer, later['layer'])
                    and conditions_meet(cond, later['condition'])):
                issues.append(f'JLC table: DRU rule "{later["name"]}" ({constraint} min {v:.4g} mm on layer '
                              f'{later["layer"]}, condition {later["condition"]!r}) follows "{name}" and can override '
                              f'JLC\'s {need} mm ({what})')
    return issues, ev


def k_rules(ctx, dru_sha=None):
    """R11's own K-rules (D-R11-40): m3.kicad_dru pinned by SHA-256 (R11_DRU_SHA256), its rules held to JLC's six-layer
    capability (R11_JLC_TABLE, R11_DRU_FLOORS), the .kicad_pro rules and net classes held to R11_PRO_FLOORS /
    R11_NETCLASS_FLOORS, no ignored severity or DRC exclusion, and the board itself against JLC's PTH-to-inner-copper
    (0.3 mm), hole, ring and NPTH rows (check_r10.pth_inner_copper, check_r10.jlc_board_holes, unchanged)."""
    pin = R11_DRU_SHA256 if dru_sha is None else dru_sha
    issues, ev = [], dict(jlc_source=JLC_URL)
    dru = getattr(ctx, 'dru', None)
    if ctx.board_path and Path(ctx.board_path).with_suffix('.kicad_dru').is_file():
        dru = Path(ctx.board_path).with_suffix('.kicad_dru').read_bytes().decode('utf-8')
    if dru is None:
        issues.append('K-rules: m3.kicad_dru not readable next to the board')
    else:
        actual = hashlib.sha256(dru.encode('utf-8')).hexdigest()
        ev.update(dru_sha256=actual, dru_sha256_expected=pin)
        if actual != pin:
            issues.append(f'K-rules: m3.kicad_dru SHA-256 {actual} is not the pinned {pin} (a reviewed change re-pins '
                          'R11_DRU_SHA256 in tools/check_r11.py)')
        table, ev['jlc_table'] = jlc_table_r11(dru)
        issues += [f'K-rules: {i}' for i in table]
    if ctx.board is not None:
        walls, ev['pth_inner_copper_mm'] = r10.pth_inner_copper(ctx.board)     # JLC 0.3 mm (R21-GATE-02)
        issues += [f'K-rules: {i}' for i in walls]
        holes, ev['jlc_board_holes'] = r10.jlc_board_holes(ctx.board)          # rings, hole sizes, NPTH (D-R22-01)
        issues += [f'K-rules: {i}' for i in holes]
    pro = Path(ctx.board_path).with_suffix('.kicad_pro') if ctx.board_path else None
    if pro is None or not pro.is_file():
        issues.append('K-rules: the .kicad_pro next to the board is not readable')
        return issues, ev
    project = json.loads(pro.read_text())
    issues += project_rule_issues(project, ev)
    return issues, ev


def project_rule_issues(project, ev=None):
    """The .kicad_pro design rules and net classes against R11_PRO_FLOORS / R11_NETCLASS_FLOORS; no ignored
    severity, no DRC exclusion."""
    ev = {} if ev is None else ev
    issues = []
    design = project.get('board', {}).get('design_settings', {})
    rules = design.get('rules', {})
    ev['pro_rules'] = {k: rules.get(k) for k in R11_PRO_FLOORS}
    for key, floor in R11_PRO_FLOORS.items():
        value = rules.get(key)
        if not isinstance(value, (int, float)) or value < floor - 1e-9:
            issues.append(f'K-rules: .kicad_pro design rule {key} = {value}, floor {floor} mm')
    classes = project.get('net_settings', {}).get('classes', [])
    ev['netclasses'] = {c.get('name'): {k: c.get(k) for k in R11_NETCLASS_FLOORS} for c in classes}
    if not any(c.get('name') == 'Default' for c in classes):
        issues.append('K-rules: .kicad_pro has no Default net class')
    for c in classes:
        for key, floor in R11_NETCLASS_FLOORS.items():
            value = c.get(key)
            if not isinstance(value, (int, float)) or value < floor - 1e-9:
                issues.append(f'K-rules: net class {c.get("name")} {key} {value}, floor {floor} mm')
        d, h = c.get('via_diameter'), c.get('via_drill')
        if isinstance(d, (int, float)) and isinstance(h, (int, float)) and (d - h) / 2 < R11_NETCLASS_VIA_RING - 1e-9:
            issues.append(f'K-rules: net class {c.get("name")} via {d} / {h} mm has a {(d - h) / 2:.3f} mm ring, under '
                          f'JLC\'s {R11_NETCLASS_VIA_RING} mm')
    ignored = sorted(k for k, v in design.get('rule_severities', {}).items() if v == 'ignore')
    ev['ignored_severities'] = ignored
    if ignored:
        issues.append(f'K-rules: DRC rule severities set to ignore: {ignored}')
    if design.get('drc_exclusions'):
        issues.append(f'K-rules: {len(design["drc_exclusions"])} DRC exclusions in the project')
    return issues


def k_lands(ctx):
    folder = Path(ctx.board_path).parent if ctx.board_path else ctx.folder
    if folder is None:
        return ['K-lands: the project folder is unknown (no board path)'], {}
    from sexpr import read
    issues, used = [], set()
    libs = folder / 'fp-lib-table'
    found = [(lib.children('name')[0].items[1].atom, lib.children('uri')[0].items[1].atom)
             for lib in read(libs.read_text()).children('lib')] if libs.is_file() else None
    if found != r10.FP_LIB_TABLE:
        issues.append(f'K-lands: fp-lib-table lists {found}; R11 uses only {r10.FP_LIB_TABLE}')
    for f in ctx.board.GetFootprints():
        lib, name = f.GetFPID().GetLibNickname().wx_str(), f.GetFPID().GetLibItemName().wx_str()
        if lib != r10.FP_LIB_TABLE[0][0]:
            issues.append(f'K-lands: {f.GetReference()} uses {lib}:{name}, not the project library')
        used.add(name)
    pins = ctx.data.get('footprint_sha256', {})
    for name, want in sorted(pins.items()):
        path = folder / 'kilib/rocket.pretty' / f'{name}.kicad_mod'
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if name not in used:
            issues.append(f'K-lands: stale footprint_sha256 entry {name}')
        elif actual != want:
            issues.append(f'K-lands: {name} library file SHA-256 {actual} is not the pinned {want}')
    overrides, compared = r10.land_overrides(ctx.board, folder / 'kilib/rocket.pretty')
    issues += [f'K-lands: {i} (a stencil / mask change goes in the reviewed library land)' for i in overrides]
    if 'paste_totals' in ctx.data:
        pastes, _ = r10.paste_totals(ctx.board, ctx.data['paste_totals'])
        issues += [f'K-lands: {i}' for i in pastes]
    return issues, dict(footprints_used=len(used), pads_compared_for_paste_mask=compared, pinned=len(pins))


def lqfp_balls(path=None):
    """{LQFP pin number: TFBGA ball} from the R11 pin table's 'pin' and 'r11_ball' columns (R10's tables name U1 by
    LQFP pin; R11's U1 pads are balls)."""
    path = R11_PIN_TABLE if path is None else Path(path)
    if not path.is_file():
        raise ValueError(f'R11 pin table {path} not found (stage A writes it)')
    with path.open() as f:
        rows = list(csv.DictReader((line for line in f if not line.startswith('#')), delimiter='\t'))
    if not rows or 'r11_ball' not in rows[0] or 'pin' not in rows[0]:
        raise ValueError(f'R11 pin table {path} has no pin / r11_ball columns')
    return {r['pin']: r['r11_ball'] for r in rows if r.get('pin') and r.get('r11_ball') not in (None, '', '-')}


def single_open_taps_r11(pin_ball=None):
    """O-C2-5: R10's SINGLE_OPEN_TAPS by function on R11. Every other reference keeps its R10 refdes and pad number
    (D-R11-01: same netlist; U1 is the only package whose pad names change), so a tap or source 'U1.<LQFP pin>' becomes
    'U1.<ball>' through the pin table (PA4 28 -> G3, VCAP1 48 -> F8, VCAP2 73 -> E7, BOOT0 94 -> D5). A U1 pin with no
    ball fails here (ValueError), never silently drops its tap."""
    pin_ball = lqfp_balls() if pin_ball is None else pin_ball

    def ball(label):
        ref, _, num = label.partition('.')
        if ref != 'U1':
            return label
        if num not in pin_ball:
            raise ValueError(f'single-via-open tap {label}: LQFP pin {num} has no R11 ball in the pin table')
        return f'U1.{pin_ball[num]}'
    return tuple((net, ball(tap), tuple(ball(s) for s in sources), why) for net, tap, sources, why in r10.SINGLE_OPEN_TAPS)


NARROW_KEYS = {'net', 'pad', 'layer', 'width_mm', 'max_len_mm', 'reason'}


def power_narrow_entries(data):
    """(entries, issues) from R11_DATA 'power_narrow' (O-C2-6): a list of objects
    {"net": "BAT_IN", "pad": "U9.5", "layer": "B.Cu", "width_mm": 0.3, "max_len_mm": 1.0, "reason": "measured reason"}:
    a run of a power path's tracks narrower than the path's IPC-2152 floor, on `layer`, touching pad `pad` (a pin entry),
    every segment at least width_mm wide and the run at most max_len_mm long (<= PIN_ENTRY_MAX). A missing key is an
    empty list; a malformed entry is an issue (fail closed)."""
    raw = data.get('power_narrow', [])
    if not isinstance(raw, list):
        return [], ["R11_DATA 'power_narrow' must be a list"]
    out, issues = [], []
    for k, e in enumerate(raw):
        where = f"R11_DATA 'power_narrow'[{k}]"
        if not isinstance(e, dict) or set(e) != NARROW_KEYS:
            issues.append(f'{where}: an object with exactly the keys {", ".join(sorted(NARROW_KEYS))}')
            continue
        num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)   # noqa: E731
        bad = [f for f, ok in (('net', isinstance(e['net'], str) and e['net']),
                               ('pad', isinstance(e['pad'], str) and re.fullmatch(r'[A-Z]+\d+\.\w+', e['pad'])),
                               ('layer', e['layer'] in CU_MM_R11),
                               ('width_mm', num(e['width_mm']) and e['width_mm'] > 0),
                               ('max_len_mm', num(e['max_len_mm']) and 0 < e['max_len_mm'] <= PIN_ENTRY_MAX),
                               ('reason', isinstance(e['reason'], str) and e['reason'].strip())) if not ok]
        if bad:
            issues.append(f'{where}: invalid {", ".join(bad)} (max_len_mm at most {PIN_ENTRY_MAX} mm, R8-GATE-04)')
            continue
        out.append(e)
    return out, issues


def ipc_floor(layer, amps):
    """IPC-2152 width (mm, rounded up to 0.01 mm) for `amps` at POWER_RISE on `layer` with R11's copper."""
    import ipc2152
    return math.ceil(ipc2152.ipc_width(POWER_RISE, layer, amps, th_mm=CU_MM_R11[layer]) * 100 - 1e-6) / 100


def _narrow_runs(segs):
    """Connected runs (tracks joined end to end on one layer) of `segs`: [[track, ...]]."""
    parent = list(range(len(segs)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, a in enumerate(segs):
        for j in range(i):
            b = segs[j]
            if a.GetLayer() == b.GetLayer() and any((p - q).EuclideanNorm() <= 1000 for p in (a.GetStart(), a.GetEnd())
                                                    for q in (b.GetStart(), b.GetEnd())):
                parent[root(i)] = root(j)
    runs = {}
    for i, t in enumerate(segs):
        runs.setdefault(root(i), []).append(t)
    return list(runs.values())


def power_paths_r11(board, paths=POWER_PATHS_R11, narrow=()):
    """O-C2-6: every path joined from its start to its end (None: a via of the net), through its listed pads; each of
    its tracks at least the floor of its own layer (the IPC-2152 width of the path's design current on R11 copper, or
    the path's fixed floor where it has no current); a run of narrower tracks only as one 'power_narrow' pin entry
    (net, layer and pad match, every width >= width_mm, run length <= max_len_mm); its vias (r10.via_issues, plus a 'max'
    count). An entry that excuses nothing is stale."""
    import pcbnew
    mm = pcbnew.ToMM
    issues, ev, used = [], {}, set()
    for spec in paths:
        name, net = spec['name'], spec['net']
        segs, joined, vias, on = r10.path_graph(board, net, spec['start'], spec['end'])
        layers = sorted({board.GetLayerName(t.GetLayer()) for t in segs})
        floors = {lay: (ipc_floor(lay, spec['amps']) if 'amps' in spec else spec['floor']) for lay in layers}
        ev[name] = dict(net=net, path_segments=len(segs), widths_mm=sorted({round(mm(t.GetWidth()), 3) for t in segs}),
                        joined=joined, floors_mm=floors, amps=spec.get('amps'), pads=on,
                        vias=[[round(mm(v.GetPosition().x), 3), round(mm(v.GetPosition().y), 3),
                               round(mm(v.GetWidth(pcbnew.F_Cu)), 3), round(mm(v.GetDrillValue()), 3)] for v in vias])
        if not joined:
            issues.append(f'{name}: no {net} copper path from {spec["start"]} to {spec["end"] or "a via of the net"}')
            continue
        issues += [f'{name}: the {net} path does not pass {ref}.{num}' for ref, nums in spec['through'].items()
                   for num in nums if f'{ref}.{num}' not in on]
        thin = [t for t in segs if mm(t.GetWidth()) < floors[board.GetLayerName(t.GetLayer())] - r10.EPS]
        for run in _narrow_runs(thin):
            lay = board.GetLayerName(run[0].GetLayer())
            length = sum(mm(t.GetLength()) for t in run)
            width = min(mm(t.GetWidth()) for t in run)
            touched = set()
            for f in board.GetFootprints():
                for pad in f.Pads():
                    if pad.GetNetname() == net and pad.IsOnLayer(run[0].GetLayer()) and any(
                            pad.HitTest(q) for t in run for q in (t.GetStart(), t.GetEnd())):
                        touched.add(f'{f.GetReference()}.{pad.GetNumber()}')
            hit = [k for k, e in enumerate(narrow) if e['net'] == net and e['layer'] == lay and e['pad'] in touched
                   and width >= e['width_mm'] - 0.005 and length <= e['max_len_mm'] + 0.005]
            if hit:
                used.update(hit)
                continue
            a = run[0].GetStart()
            cap = [e for e in narrow if e['net'] == net and e['layer'] == lay and e['pad'] in touched]
            why = (f'; the power_narrow entry for {cap[0]["pad"]} allows {cap[0]["width_mm"]} mm over at most '
                   f'{cap[0]["max_len_mm"]} mm' if cap else '; no power_narrow pin entry for it')
            issues.append(f'{name}: {net} run of {len(run)} track(s) {width:.3f} mm wide, {length:.3f} mm long on {lay} '
                          f'from ({mm(a.x):.3f}, {mm(a.y):.3f}) touching {sorted(touched) or "no pad"}; floor '
                          f'{floors[lay]} mm ({spec.get("amps", "no")} A, IPC-2152 at {POWER_RISE:g} C on R11 copper)'
                          f'{why}')
        vspec = spec['vias']
        if 'max' in vspec and len(vias) > vspec['max']:
            issues.append(f'{name}: {len(vias)} via(s) on the path; at most {vspec["max"]}')
        issues += r10.via_issues(board, name, vias, {k: v for k, v in vspec.items() if k != 'max'}, net)
    issues += [f'stale power_narrow entry {e["net"]} {e["pad"]} {e["layer"]} {e["width_mm"]} mm / {e["max_len_mm"]} mm '
               f'({e["reason"][:60]})' for k, e in enumerate(narrow) if k not in used]
    ev['narrow_used'] = [narrow[k]['reason'] for k in sorted(used)]
    return issues, ev


def k_power(ctx):
    narrow, bad = power_narrow_entries(ctx.data)
    exceptions = [tuple(e) for e in ctx.data.get('single_open_exceptions', [])]
    issues, ev = power_paths_r11(ctx.board, narrow=narrow)
    found, ev['fire_return'] = r10.fire_return(ctx.board)
    taps, ev['single_via_open_taps'] = r10.single_via_opens(ctx.board, taps=single_open_taps_r11(),
                                                            exceptions=exceptions)
    return [f'K-power: {i}' for i in bad + issues + found + taps], ev


def k_ports(ctx):
    issues, ev = r10.port_clamps(ctx.board, clamps=PORT_CLAMPS_R11)
    returns, gnd = r10.clamp_returns(ctx.board, clamps=PORT_CLAMPS_R11)
    return ([f'K-ports: {i}' for i in issues + returns],
            dict(clamp_path_mm=ev, bound_mm=r10.CLAMP_PATH_MAX, clamp_gnd_mm=gnd))


# K-loader on R11 (R3-MCU-01 / R17-MCU-02; gate_C2.md section 5). The loader-pin set is check_r10.LOADER_H74X unchanged
# (AN2606 Rev 64 Table 119 pp. 277-280 = Rev 70 Table 135 pp. 320-323); U1's balls come from pin_table.tsv. R10's
# LOADER_R10 is keyed to R10's pin map and stays frozen; LOADER_R11 is R11's own list, keyed by port pin. Each entry:
# the net the pin may carry, the net's other members (pad -> part value; None = not pinned, the USB contract), the
# decision that put the net there, the section holding its case ('R10' = check_r10.LOADER_R10's case, reused only
# while R10's entry has the same net and members), the AN2606 citation and the electrical reason.
LOADER_AN2606 = 'AN2606 Rev 64 Table 119 pp. 277-280 (Rev 70 Table 135 pp. 320-323)'
LOADER_DECISIONS = R11_DIR / 'design/R11_DECISIONS.md'
LOADER_CASES = R11_DIR / 'design/stageC1b.md'
R10_CASE = 'R10'


def _loader_r10(port):
    """An R10 allowance whose pin carries the same net on R11 (D-R11-01 keeps R10's netlist)."""
    net, members, reason = r10.LOADER_R10[port]
    return dict(net=net, members=members, decision='D-R11-01', case=R10_CASE, an2606=LOADER_AN2606, reason=reason)


LOADER_R11 = {
    **{port: _loader_r10(port) for port in ('PA4', 'PA5', 'PA6', 'PC10', 'PC11', 'PC12', 'PA11', 'PA12', 'PB6')},
    'PB9': dict(net='CAM_MCU_TX', members={'U12.5': 'TXU0202DCUR'}, decision='D-R11-49', case='8.4',
                an2606=LOADER_AN2606,
                reason='I2C1_SDA open drain, no pull: the loader leaves PB9 released into U12\'s CMOS input; U12 is '
                       'disabled (OE low by R102 10k while PC15 is an input) and the camera unpowered (U402 EN low by '
                       'R431 100k while PC14 is an input), so nothing reaches J9; the I2C1 slave needs SCL edges on '
                       'PB6 (QSPI_NCS, held high by R10 10k) and no board device is an I2C master (Inference)'),
    'PA15': dict(net='SERVO2_MCU', members={'R151.1': '1k 0603', 'R155.1': '10k', 'D121.3': 'SRV05-4'},
                 decision='D-R11-49', case='8.4', an2606=LOADER_AN2606,
                 reason='SPI3_NSS: a loader input, no pull, never driven; R155 10k holds it low, so the servo sees a '
                        'constant low; the reset JTDI pull-up (>= 30k, Inference) against R155 gives <= 0.83 V '
                        '(Calculation); an SPI3 frame needs SCK edges on PC10 (SD_SCK), which nothing drives'),
    'PB10': dict(net='I2C1_SCL', members={'R12.1': '4.7k', 'U5.8': 'MS561101BA03'}, decision='D-R11-41', case='7',
                 an2606=LOADER_AN2606,
                 reason='USART3_TX, driven push-pull: idle high, the level R12 4.7k holds; it transmits only after a '
                        '0x7F sync on PB11, which cannot form; U5 SCL is an input (no clock stretching), so a low pin '
                        'draws at most 3.3 V / 4.7k = 0.7 mA (Calculation), far below 20 mA; SDA stays high, no START'),
    'PB11': dict(net='I2C1_SDA', members={'R13.1': '4.7k', 'U5.7': 'MS561101BA03'}, decision='D-R11-41', case='7',
                 an2606=LOADER_AN2606,
                 reason='USART3_RX, a loader input with pull-up, never driven: R13 and the pull-up hold a UART mark; '
                        'U5 drives SDA only after a master START and its address, and in system-memory boot nothing '
                        'masters the bus, so no start bit and no 0x7F sync form (Inference)'),
}


def loader_entry_issues(allowances):
    """Schema and provenance of LOADER_R11-form entries: a LOADER_H74X port, every field, a decision heading in
    R11_DECISIONS.md, a case section heading in stageC1b.md (or R10's own entry, same net and members), R10's AN2606
    citation."""
    issues = []
    decisions = LOADER_DECISIONS.read_text() if LOADER_DECISIONS.is_file() else ''
    cases = LOADER_CASES.read_text() if LOADER_CASES.is_file() else ''
    for port, e in sorted(allowances.items()):
        tag = f'LOADER_R11 {port}'
        if port not in r10.LOADER_H74X:
            issues.append(f'{tag}: not a loader pin (AN2606 Rev 70 Table 135 as check_r10.LOADER_H74X encodes it)')
        missing = [k for k in ('net', 'decision', 'case', 'an2606', 'reason') if not str(e.get(k) or '').strip()]
        if missing or 'members' not in e:
            issues.append(f'{tag}: missing {missing + ([] if "members" in e else ["members"])}')
            continue
        if e['an2606'] != LOADER_AN2606:
            issues.append(f'{tag}: AN2606 citation {e["an2606"]!r} is not R10\'s ({LOADER_AN2606})')
        if not re.search(rf'^## {re.escape(e["decision"])} ', decisions, re.M):
            issues.append(f'{tag}: decision {e["decision"]} has no heading in {LOADER_DECISIONS.name}')
        if e['case'] == R10_CASE:
            old = r10.LOADER_R10.get(port)
            if old is None or (old[0], old[1]) != (e['net'], e['members']):
                issues.append(f'{tag}: names R10\'s case, but R10\'s LOADER_R10 has no entry for {port} with net '
                              f'{e["net"]} and these members; write an R11 case')
        elif not re.search(rf'^#+ {re.escape(e["case"])}\.? ', cases, re.M):
            issues.append(f'{tag}: case section {e["case"]} not found in {LOADER_CASES.name}')
    return issues


def loader_pins_r11(board, port_pin, allowances=None):
    """K-loader on R11: (issues, evidence). Every U1 ball on a LOADER_H74X port that carries a net needs a LOADER_R11
    entry naming that net and the net's exact other members; an entry whose pin carries another net fails; an entry
    for an NC pin, or a pin not on the package, is stale."""
    allowances = LOADER_R11 if allowances is None else allowances
    issues = loader_entry_issues(allowances)
    u1 = board.FindFootprintByReference(r10.MCU_REF)
    if u1 is None:
        return issues + ['U1 missing'], {}
    members = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            if r10.real_net(p.GetNetname()) and f.GetReference() != r10.MCU_REF:
                members.setdefault(p.GetNetname(), {})[f'{f.GetReference()}.{p.GetNumber()}'] = f.GetValue()
    ev, used = {}, set()
    for port, (role, use) in sorted(r10.LOADER_H74X.items()):
        ball = port_pin.get(port)
        if ball is None:
            ev[port] = 'not on this package'
            continue
        pad = u1.FindPadByNumber(ball)
        where = f'U1.{ball} {port} ({role}, loader {use}; {LOADER_AN2606})'
        if pad is None:
            issues.append(f'{where}: pad missing')
            continue
        net = pad.GetNetname()
        if not r10.real_net(net):
            ev[port] = 'NC'
            continue
        e = allowances.get(port)
        if e is None:
            issues.append(f'{where} carries {net} with no LOADER_R11 entry' +
                          (' (the loader drives this pin)' if use in r10.LOADER_DRIVES else ''))
            continue
        used.add(port)
        ev[port] = dict(ball=ball, net=net, role=role, use=use, decision=e.get('decision'), case=e.get('case'))
        if net != e.get('net'):
            issues.append(f'{where} carries {net}; its LOADER_R11 entry is for {e.get("net")}')
            continue
        pinned = e.get('members')
        if pinned is not None:
            actual = members.get(net, {})
            if actual != pinned:
                extra = sorted(f'{k} {v}' for k, v in actual.items() if pinned.get(k) != v)
                gone = sorted(f'{k} {v}' for k, v in pinned.items() if actual.get(k) != v)
                issues.append(f'{where}: {net} members differ from the entry (now {extra}, recorded {gone}); '
                              're-qualify the loader state')
    issues += [f'stale LOADER_R11 entry {port} ({allowances[port].get("net")}): the pin carries no net or is not on '
               'this package' for port in sorted(set(allowances) - used)]
    return issues, ev


def k_loader(ctx):
    issues, ev = loader_pins_r11(ctx.board, balls(ctx))
    return [f'K-loader: {i}' for i in issues], ev


RULES = [
    ('S-1', 'RAW_ACT pyro bus, named armed-side parts', lambda c, s: s1(c)),
    ('S-2', 'pyro feed only through the load switch', lambda c, s: s2(c)),
    ('S-3', 'gate networks defined off', lambda c, s: s3(c)),
    ('S-3c', 'load-switch gate bias on the FET layer\'s copper alone (R18-SAF-02)', lambda c, s: s3c(c)),
    ('S-4', 'required-fitted parts, MPN-decoded values; wire pads off the JLC upload', lambda c, s: s4(c)),
    ('S-5', 'J400 arming switch and protected EN contacts', lambda c, s: r10.s5(c)),
    ('S-6', 'external ports apart from pyro / arming copper', lambda c, s: r10.s6(c)),
    ('S-7', 'J122 GH: SERVO1-4 and GND, two fixing tabs', lambda c, s: s7(c)),
    ('S-8', 'In1..In4 copper >= 1.0 mm from pyro, load-switch gate and enable barrels', lambda c, s: s8(c)),
    ('S-9', 'fire / source copper widths', lambda c, s: s9(c)),
    ('W-1', 'J1 / J121 plated wire pads (D-R11-05)', lambda c, s: w1(c)),
    ('W-2', 'GH port pin-outs and parts (D-R11-05)', lambda c, s: w2(c)),
    ('LC-1', 'local overrides respect the applicable floors', lambda c, s: r10.lc1(c.board)),
    ('M-1', 'outline 46 mm wide, <= 56 mm long', lambda c, s: m1(c)),
    ('M-3', 'the pinned D-R11-10 supports, one at each corner', lambda c, s: m3(c)),
    ('M-5', 'fit (profile r11)', lambda c, s: m5(c, s)),
    ('M-6', 'bottom keep-outs', lambda c, s: r10.m6(c)),
    ('M-7', 'IMU pose (R11_DATA) and MEMS keep-outs', lambda c, s: m7(c)),
    ('M-8', 'courtyards >= 2.5 mm from the short edges, recorded queries (D-R11-12)', lambda c, s: m8(c)),
    ('K-legends', 'legends, ids, silkscreen allowlist, designators and Fab references', lambda c, s: k_legends(c)),
    ('K-copper', 'copper hygiene, no pour debris', lambda c, s: k_copper(c)),
    ('K-inner', 'In1 / In4 GND only, In2 power and GND only', lambda c, s: k_inner(c)),
    ('K-reference', 'critical signal reference copper on the six-layer stack', lambda c, s: k_reference(c)),
    ('K-region', 'critical In3 runs over one In2 plane region', lambda c, s: k_region(c)),
    ('K-plane', 'inner power fills one piece, else >= 2 links', lambda c, s: k_plane(c)),
    ('K-fill', 'saved zone fills are current', lambda c, s: r10.k_fill(c)),
    ('K-rules', 'project rule floors, JLC hole table, PTH to inner copper, board holes', lambda c, s: k_rules(c)),
    ('K-lands', 'project library only, placed paste / mask as the library', lambda c, s: k_lands(c)),
    ('K-width', 'BAT_IN / RAW_PROTECTED width floor', lambda c, s: r10.k_width(c.board)),
    ('K-power', 'rail paths, fire return, single-via-open taps', lambda c, s: k_power(c)),
    ('K-ports', 'port ESD clamps on the wire side', lambda c, s: k_ports(c)),
    ('K-loader', 'ROM-loader pins on U1\'s balls', lambda c, s: k_loader(c)),
]
STAGES = {'functional': {'S-1', 'S-2', 'S-3', 'S-4', 'S-5', 'S-6', 'S-7', 'W-1', 'W-2', 'K-loader'}}
STAGES['placement'] = STAGES['functional'] | {'LC-1', 'M-1', 'M-3', 'M-5', 'M-6', 'M-7', 'M-8', 'K-lands'}
STAGES['full'] = {rid for rid, _, _ in RULES}


def selected_rules(only=None, stage='full'):
    if only is None:
        if stage not in STAGES:
            raise ValueError(f'unknown rule stage: {stage!r}')
        return STAGES[stage]
    selected = set(only)
    if not selected or not any(selected):
        raise ValueError('explicit rule selection is empty')
    unknown = selected - STAGES['full']
    if unknown:
        raise ValueError(f'unknown rule ids: {", ".join(repr(r) for r in sorted(unknown))}')
    return selected


def make_ctx(board, folder=None, board_path=None, fit=None, text=None, bom=None, cpl=None, data=None, port_pin=None):
    import check_r9 as r9
    import fit_check as fc

    class R11Ctx(r9.Ctx):
        def fit(self):
            if self.fit_report is None:
                self.fit_report = fc.check_board(self.board, self.folder or Path('.'), profile='r11')
            return self.fit_report
    ctx = R11Ctx(board, folder, board_path, fit, None, None, 0.0, None)
    if text is None and board_path and Path(board_path).is_file():
        text = Path(board_path).read_text()
    ctx.text, ctx.bom, ctx.cpl, ctx.fit_given, ctx._reach = text, bom, cpl, fit is not None, None
    ctx.data = load_data() if data is None else data
    ctx.port_pin, ctx._balls = port_pin, None
    return ctx


def check_board(board, folder=None, board_path=None, fit=None, only=None, stage='full', board_sha=None, text=None,
                bom=None, cpl=None, data=None, port_pin=None):
    """Run the rules of `stage` (or `only`); each rule that cannot run fails. route_check runs as profile r11."""
    selected = selected_rules(only, stage)
    import route_check as rc
    ctx = make_ctx(board, folder, board_path, fit, text, bom, cpl, data, port_pin)
    previous = rc.PROFILE
    out, flat = {}, []
    with ExitStack() as stack:
        rc.set_profile('r11')
        stack.callback(rc.set_profile, previous)
        for rid, title, fn in RULES:
            if rid not in selected:
                continue
            try:
                issues, ev = fn(ctx, board_sha)
            except Exception as e:                       # a rule that cannot run fails, it never passes
                issues, ev = [f'{rid}: could not run: {type(e).__name__}: {e}'], {}
            out[rid] = dict(title=title, ok=not issues, issues=issues, evidence=ev)
            flat += [i if i.startswith(rid) else f'{rid}: {i}' for i in issues]
    return dict(profile='r11', stage=stage, complete=stage == 'full' and only is None, ok=not flat, rules=out,
                issues=flat, failing=[k for k, v in out.items() if not v['ok']])


def file_sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board', nargs='?', type=Path, default=R11_DIR / 'm3.kicad_pcb')
    ap.add_argument('--report', type=Path)
    ap.add_argument('--fit', type=Path, help='tools/fit_check.py --profile r11 --report of this board')
    ap.add_argument('--only', help='comma-separated rule ids')
    ap.add_argument('--stage', choices=tuple(STAGES), default='full')
    ap.add_argument('--bom', type=Path)
    ap.add_argument('--cpl', type=Path)
    a = ap.parse_args()
    only = {rid.strip() for rid in a.only.split(',')} if a.only is not None else None
    try:
        selected_rules(only, a.stage)
    except ValueError as error:
        ap.error(str(error))
    import pcbnew
    import fit_check as fc
    bp = a.board.resolve()

    def inputs():
        r = fc.input_hashes(bp)
        for p in (bp.with_suffix('.kicad_dru'), bp.with_suffix('.kicad_pro'), bp.with_suffix('.kicad_sch'),
                  R11_PIN_TABLE, R11_DATA):
            r[p.name] = file_sha(p)
        return r
    before = inputs()
    sha = before[bp.name]
    fit = json.loads(a.fit.read_text()) if a.fit else None
    if fit is not None and fit.get('board_sha256') != sha:
        print('FAIL the fit report is not bound to this board (board_sha256)')
        return 1
    board = pcbnew.LoadBoard(str(bp))
    if board.GetTitleBlock().GetRevision() != REVISION:
        print(f'FAIL title-block revision {board.GetTitleBlock().GetRevision()!r}; check_r11 checks {REVISION}')
        return 1
    report = check_board(board, bp.parent, bp, fit=fit, only=only, stage=a.stage, board_sha=sha, bom=a.bom, cpl=a.cpl)
    if before != inputs():
        report['issues'].append('board, rules, schematic, pin table or gate data changed during check')
        report['ok'] = False
    report.update(board_sha256=sha, inputs_sha256=before, checker_sha256=file_sha(__file__))
    for rid, r in report['rules'].items():
        print(f"{rid:12s} {'OK  ' if r['ok'] else 'FAIL'} {r['title']}" + (f" ({len(r['issues'])})" if r['issues'] else ''))
    for i in report['issues']:
        print('FAIL', i)
    scope = a.stage if only is None else 'selected rules'
    print(f'R11 CAD contract ({scope}):', 'OK' if report['ok'] else f"FAIL ({len(report['issues'])} findings in "
          f"{len(report['failing'])} rules: {', '.join(report['failing'])})")
    if a.report:
        a.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
