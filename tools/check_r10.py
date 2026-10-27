#!/usr/bin/env python3
"""R10 native-CAD contract (M3-ASSY-R10): rule-based checks, modelled on tools/check_r9.py, for the leaner R10 board
(r10_plan.md sections 4 and 6-8; docs/R10_VALIDATION.md R1-07, R1-m10).

usage: <KiCad python3> -I tools/check_r10.py [board.kicad_pcb] [--report out.json] [--fit FIT.json]
       [--plate PLATE.json] [--seed SEED.json] [--only S-1,M-1] [--stage functional|placement|full]
       [--bom BOM.csv] [--cpl CPL.csv]
exit 0 = every selected rule holds

Run with KiCad Python on a filled board. tools/check.sh runs it after fit_check --profile r10 (--fit) and
plate_model.py --profile r10 (--plate). Without --fit the fit report is computed here; without --plate M-2 fails as
"not run". --seed is accepted for check_r9's command shape only: R10 has no rule H (owner decision, r10_plan section 2
item 1), so no R10 rule reads it. --stage selects rule groups for build steps (functional, placement); only the full
stage (the default) is the gate. --bom / --cpl, when given, are also checked for the required-fitted safety parts.

Dropped from R9 (r10_plan section 2 item 1 and O1 / O2): every pyro-specific spacing rule (P-0 rules A-H / A2, P-1 /
P-2 PYRO_BLOCK, P-3 purity, P-4 rule H, P-5 bridge table, P-6 bare gate pads, P-7 gate guard, P-10 coat region by the
block, the strict pad rules, K-power-pyro's D18 / D85 / D19 spacing) and every RF rule (R-1..R-13, the U30 / U31 / J30 /
J31 checks, GCPW). Pyro copper uses the board default clearance, which KiCad DRC enforces.

Safety (AGENTS.md section 2, F8; functional, not spacing):
  S-1   ARM break: J124 has exactly one RAW_ACT and one PYRO1_BUS pad; no other part joins the RAW_ACT side to the
        armed side (a net path through any part but J124, rails GND / 3V3 / 3V3A excepted); no test pad on armed
        copper (PYRO1_BUS / IGN / OUT); no copper (track, via, fill, drawing, any net or none) connects RAW_ACT pads
        to armed pads (geometric copper connectivity from the pads, independent of net labels)
  S-2   pyro feed: Q120 / Q121 are the back-to-back load switch BAT_IN -> ACT_FET_S -> RAW_ACT with gates on
        ACT_GATE; RAW_ACT is reached from no supply (BAT_IN, RAW_PROTECTED, ACT_FET_S, VLOGIC, ...) except through
        Q121; the armed side reaches no supply and no RAW_ACT except through J124; neither side's copper touches a
        foreign pad
  S-3   gate networks defined off: Q124 (pyro) gate has a pull-down to its source, a gate-source capacitor and a series
        resistor from a U1 pin; Q120 / Q121 (P-FET load switch) gate has a gate-source resistor and capacitor and a
        series resistor from its driver
  S-4   R1-07 required fitted: every safety part (and every R10 contract part) is on the board, not DNP, not excluded
        from BOM or position files, not board-only, on the board and in the schematic; also in --bom / --cpl if given
  S-5   R1-m10 J124 gap: J124's two pads >= 1.5 mm apart edge to edge on every copper layer, and RAW_ACT vs
        PYRO1_BUS copper >= 1.5 mm inside J124's courtyard (and its pad field + 1.5 mm)
  S-6   external ports: no part (the MCU U1 excepted) has pads on both a port net (GPS_ / RADIO_ / CAM_ / PORT_) and a pyro / arming net
        (PYRO1_ / ARM1_ / ACT_ / RAW_ACT*); port copper >= the board default clearance from pyro / arming copper on
        the same layer (no shared copper item)
  S-7   J122 (O3): the middle (+) row 2 / 5 / 8 / 11 has no net and no copper touching it, the GND row 3 / 6 / 9 / 12
        is on GND, the signal row 1 / 4 / 7 / 10 on SERVO1-4_OUT
Mechanical and placement (kept from check_r9 where they still apply, read from the board):
  LC-1  no pad or footprint carries a local clearance override (check_r9.lc1)
  M-1   outline one rectangle from (0, 0), 46 mm wide, length read from the board <= 120 mm (P1), Edge.Cuts circles
        3.2 mm
  M-2   plate model (profile r10, five supports, mated plugs) pinned D 5 first mode >= 209 Hz, bound to this board
  M-3   J122 tie holes and the 4 mm bottom tie channel (check_r9.m3)
  M-5   fit_check --profile r10 clean and bound to this board
  M-6   bottom parts SMD only, >= 1.5 mm from foreign through-hole pads, >= 3.5 mm from an M3 support centre
  M-7   U4 on the bottom at R9's rotation 180 (roll = -gyro_Y, R9_DECISIONS D-S7-06) with |x - board centre| <= 13 mm;
        no via or fill under U4 / U5 on their side (check_r9.m7); the axis map is read from the board and reported
  P-8   R168 / R170 / R172 at the MCU end (check_r9.p8)
  P-11  J121 / J124 wires enter from -x (owner, r10_plan 2 item 2) with >= 6.25 mm wire room to the bore wall; the
        entry direction is read from the footprint description ("wire entry +y"), else DB128's local -y
  F9-1  input protection near J1.1 (check_r9.f9)
  T-1   a legal 5 mm tab on each long edge in the aft and forward thirds (check_r9.t1)
Kept contract and copper rules:
  K-contract   R10 netlist contract: pin map, connectors, port power / UART isolation, camera UART, parts, removed parts
  K-actuators  m3_design/check_actuators.py --profile r10 in process (check.sh also runs it on its own)
  K-legends    duplicate ids, pin legends, legend subjects (R10 word legends), R10 terminal pin legends
  K-copper     vias in pads, overlap-only joints, thermal policy, via paste (check_r9.k_copper)
  K-inner      In1 carries no track, In2 power and GND only (check_r9.k_inner_signal, route_check r10 classes)
  K-reference  critical signal samples have adjacent reference copper (critical_reference, R10 port nets)
  K-retained   bare test pads 1.0 mm / Tag-Connect 0.508 mm from foreign copper, C29 flash bypass, camera bypass,
               TP122 on the bottom
"""
import argparse
from contextlib import contextmanager
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'quality_audit'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_actuators as actuators                             # noqa: E402
from sexpr import read, properties                              # noqa: E402

REQUIRED_FITTED = (set(actuators.PINNED) - {'C121'}) | {
    'R131', 'C127', 'C129', 'C122', 'C84', 'U11', 'U12', 'U13',
    'R100', 'R101', 'R102', 'R103', 'C91', 'C92', 'C93', 'C100', 'C29',
    'J123', 'J400', 'J410', 'J420', 'U400', 'U401', 'U402', 'U410', 'U420',
    'U411', 'U421', 'U412', 'U422'} | {f'{prefix}{n}' for prefix, numbers in
        (('R', range(440, 444)), ('R', range(450, 454)), ('C', range(440, 444)),
         ('C', range(450, 454)), ('D', (400, 401, 410, 411, 420, 421)),
         ('R', (410, 411, 412, 420, 421, 422, 430, 431, 432)),
         ('R', range(400, 405)), ('C', range(400, 409)), ('L', (400,))) for n in numbers}
CONNECTORS = {
    'J1': ('BAT_IN', 'GND'), 'J400': ('BAT_SW_SOURCE', 'BAT_SW_RETURN'),
    'J410': ('GPS_4V8', 'GND', 'GPS_TX_WIRE', 'GPS_RX_WIRE'),
    'J420': ('RADIO_4V8', 'GND', 'RADIO_TX_WIRE', 'RADIO_RX_WIRE'),
    'J9': ('CAM_5V', 'GND', 'CAM_RX_WIRE', 'CAM_TX_WIRE')}
MCU = {'63': 'GPS_TX_MCU', '64': 'GPS_RX_MCU', '52': 'RADIO_TX_MCU', '51': 'RADIO_RX_MCU',
       '61': 'GPS_PWR_EN', '57': 'GPS_FAULT_N', '62': 'GPS_UART_OE',
       '55': 'RADIO_PWR_EN', '56': 'RADIO_FAULT_N', '45': 'RADIO_UART_OE',
       # R10_DECISIONS D-R2-07 (camera control, buzzer / pull-pin) and D-R2-09 (status / VLOGIC sense pins)
       '7': 'PULLPIN', '8': 'BUZZ_DRV', '31': 'NC', '39': 'CAM_UART_OE', '41': 'CAM_PWR_EN', '42': 'CAM_FAULT_N',
       '17': 'NC', '28': 'LOGIC_SOURCE_ST', '29': 'BAT_FAULT_N', '30': 'VLOGIC_SENSE'}
PARTS = {'J1': ('C466970', 'M3_DB125_2P_GN'),
         'J121': ('C52993880', 'M3_DB125_2P_BK'), 'J124': ('C52993880', 'M3_DB125_2P_BK'),
         'J400': ('C161690', 'M3_GH_BM02B_GHS_TBT'), 'J123': ('C161690', 'M3_GH_BM02B_GHS_TBT'),
         'J410': ('C161692', 'M3_GH_BM04B_GHS_TBT'), 'J420': ('C161692', 'M3_GH_BM04B_GHS_TBT'),
         'C84': ('C46550466', 'M3_MA_8x10')}
REMOVED = {'U30', 'U31', 'J30', 'J31', 'C121', 'C150', 'C151', 'U7', 'U8', 'L3'}


def population(text, required=REQUIRED_FITTED, schematic=False):
    """Check actual inclusion flags, not value/net presence. Root schematic symbols only."""
    found, issues = {}, []
    for node in read(text).children('symbol' if schematic else 'footprint'):
        props = properties(node)
        if 'Reference' not in props:
            continue
        ref = props['Reference'].items[2].atom
        found[ref] = node
        if ref not in required:
            continue
        attrs = {a.atom for n in node.children('attr') for a in n.items[1:]}
        bad = attrs & {'dnp', 'exclude_from_bom', 'exclude_from_pos_files', 'board_only'}
        for key, forbidden in (('dnp', 'yes'), ('in_bom', 'no'), ('on_board', 'no')):
            if any(n.items[1].atom == forbidden for n in node.children(key)):
                bad.add(f'{key}={forbidden}')
        if bad:
            issues.append(f'{ref}: required fitted part excluded ({", ".join(sorted(bad))})')
    issues += [f'{ref}: required fitted part missing' for ref in sorted(required - found.keys())]
    return issues


def schematic_population(path):
    pending, seen, texts = [Path(path)], set(), []
    while pending:
        path = pending.pop().resolve()
        if path in seen:
            continue
        seen.add(path)
        text = path.read_text()
        texts.append(text)
        for sheet in read(text).children('sheet'):
            props = properties(sheet)
            pending.append(path.parent / props['Sheetfile'].items[2].atom)
    # Collect placed symbols across the reachable hierarchy, never stale sheets or library definitions.
    symbols = [text[n.start:n.end] for text in texts for n in read(text).children('symbol')]
    return population('(kicad_sch ' + '\n'.join(symbols) + ')', schematic=True)


def assembly_population(text, required=REQUIRED_FITTED):
    rows = list(csv.DictReader(io.StringIO(text)))
    refs = {ref.strip() for row in rows for ref in row.get('Designator', '').split(',') if ref.strip()}
    return [f'{ref}: required fitted part missing from assembly list' for ref in sorted(required - refs)]


def uart_ports(pins, values, codes):
    issues = []
    def expect(ref, nets, code=None, value=None):
        for num, net in nets.items():
            actual = pins.get(f'{ref}.{num}')
            if actual != net and not (net is None and actual and actual.startswith('unconnected-')):
                issues.append(f'{ref}.{num}: UART isolation requires {net}, got {actual}')
        if code and codes.get(ref) != code:
            issues.append(f'{ref}: UART isolation requires LCSC {code}')
        if value and values.get(ref) != value:
            issues.append(f'{ref}: UART isolation requires {value}')
    for port, base, rbase, dbase in (('GPS', 410, 440, 410), ('RADIO', 420, 450, 420)):
        expect(f'U{base + 1}', {1: f'{port}_RX_BUFFER', 2: 'GND', 3: '3V3', 4: f'{port}_RX_MCU',
               5: f'{port}_TX_MCU', 6: f'{port}_UART_OE', 7: f'{port}_IO_3V3', 8: f'{port}_TX_BUFFER'}, 'C5186957')
        expect(f'U{base + 2}', {1: f'{port}_4V8', 2: 'GND', 3: None, 4: None, 5: f'{port}_IO_3V3'}, 'C89347')
        expect(f'R{rbase}', {1: f'{port}_RX_WIRE', 2: f'{port}_RX_BUFFER'}, 'C21190', '1k 1%')
        expect(f'R{rbase + 1}', {1: f'{port}_TX_BUFFER', 2: f'{port}_TX_WIRE'}, 'C21190', '1k 1%')
        expect(f'R{rbase + 2}', {1: f'{port}_UART_OE', 2: 'GND'}, 'C25804', '10k 1%')
        expect(f'R{rbase + 3}', {1: f'{port}_IO_3V3', 2: 'GND'}, 'C21190', '1k 1%')
        expect(f'D{dbase}', {1: f'{port}_TX_WIRE', 2: 'GND'}, 'C535146')
        expect(f'D{dbase + 1}', {1: f'{port}_RX_WIRE', 2: 'GND'}, 'C535146')
    return issues


def camera_uart(pins, values, codes):
    expected = {
        'U12': ({1: 'CAM_RX_BUFFER', 2: 'GND', 3: '3V3', 4: 'CAM_MCU_RX', 5: 'CAM_MCU_TX',
                 6: 'CAM_UART_OE', 7: 'CAM_IO_3V3', 8: 'CAM_TX_BUFFER'}, 'C5186957', None),
        'U13': ({1: 'CAM_5V', 2: 'GND', 3: None, 4: None, 5: 'CAM_IO_3V3'}, 'C89347', None),
        'R100': ({1: 'CAM_RX_WIRE', 2: 'CAM_RX_BUFFER'}, 'C21190', '1k 1%'),
        'R101': ({1: 'CAM_TX_BUFFER', 2: 'CAM_TX_WIRE'}, 'C21190', '1k 1%'),
        'R102': ({1: 'CAM_UART_OE', 2: 'GND'}, 'C25804', '10k 1%'),
        'R103': ({1: 'CAM_IO_3V3', 2: 'GND'}, 'C21190', '1k 1%')}
    issues = []
    for ref, (nets, code, value) in expected.items():
        if codes.get(ref) != code or (value and values.get(ref) != value):
            issues.append(f'{ref}: retained camera isolation part/value mismatch')
        for num, net in nets.items():
            actual = pins.get(f'{ref}.{num}')
            if actual != net and not (net is None and actual and actual.startswith('unconnected-')):
                issues.append(f'{ref}.{num}: retained camera isolation requires {net}')
    return issues


def port_power(pins, values, codes):
    """Independent O5 topology and hardware default-off/FAULT/ILIM contract."""
    issues = []
    expected = {
        'U400': {1: 'PORT_FB', 2: 'RAW_PROTECTED', 3: 'RAW_PROTECTED', 4: 'GND', 5: 'PORT_SW', 6: 'PORT_BST'},
        'U401': {1: 'PORT_4V8', 2: 'PORT_4V8', 3: 'PORT_LDO_FB', 4: 'GND', 5: None, 6: 'GND',
                 7: 'PORT_5V3', 8: 'PORT_LDO_SS', 9: 'PORT_5V3', 10: 'PORT_5V3', 11: 'GND'}}
    pinned = {'U400': 'C2071044', 'U401': 'C2878140'}
    for port, switch, rb, supply, out, limit, code, mcu in (
            ('CAM', 'U402', 430, 'PORT_5V3', 'CAM_5V', '22.6k 1%', 'C185349', ('41', '42')),
            ('GPS', 'U410', 410, 'PORT_4V8', 'GPS_4V8', '100k 1%', 'C14675', ('61', '57')),
            ('RADIO', 'U420', 420, 'PORT_4V8', 'RADIO_4V8', '66.5k 1%', 'C137691', ('55', '56'))):
        expected[switch] = {1: supply, 2: 'GND', 3: f'{port}_PWR_EN', 4: f'{port}_FAULT_N',
                            5: f'{port}_ILIM', 6: out}
        pinned[switch] = 'C55266'
        for ref, net, return_net, value, lcsc in (
                (f'R{rb}', f'{port}_ILIM', 'GND', limit, code),
                (f'R{rb + 1}', f'{port}_PWR_EN', 'GND', '100k 1%', 'C14675'),
                (f'R{rb + 2}', f'{port}_FAULT_N', '3V3', '10k 0.1%', 'C95204')):
            expected[ref] = {1: net, 2: return_net}; pinned[ref] = lcsc
            if values.get(ref) != value:
                issues.append(f'{ref}: power-port bias/current limit must be {value}')
        for net, members in (
                (f'{port}_PWR_EN', {f'{switch}.3', f'R{rb + 1}.1', f'U1.{mcu[0]}'}),
                (f'{port}_FAULT_N', {f'{switch}.4', f'R{rb + 2}.1', f'U1.{mcu[1]}'}),
                (f'{port}_ILIM', {f'{switch}.5', f'R{rb}.1'})):
            actual = {pin for pin, name in pins.items() if name == net}
            if actual != members:
                issues.append(f'{net}: members must be {sorted(members)}, got {sorted(actual)}')
    for ref, nets, value, code in (
            ('R400', {1: 'PORT_5V3', 2: 'PORT_FB_TOP'}, '56.2k 0.1%', 'C705784'),
            ('R404', {1: 'PORT_FB_TOP', 2: 'PORT_FB'}, '2k 1%', 'C22975'),
            ('R401', {1: 'PORT_FB', 2: 'GND'}, '10k 0.1%', 'C95204'),
            ('R402', {1: 'PORT_4V8', 2: 'PORT_LDO_FB'}, '49.9k 0.1%', 'C705780'),
            ('R403', {1: 'PORT_LDO_FB', 2: 'GND'}, '10k 0.1%', 'C95204'),
            ('L400', {1: 'PORT_SW', 2: 'PORT_5V3'}, '6.8uH', 'C1329837')):
        expected[ref] = nets; pinned[ref] = code
        if values.get(ref) != value:
            issues.append(f'{ref}: qualified supply setting requires {value}')
    for ref, nets in expected.items():
        for num, net in nets.items():
            actual = pins.get(f'{ref}.{num}')
            if actual != net and not (net is None and actual and actual.startswith('unconnected-')):
                issues.append(f'{ref}.{num}: O5 power topology requires {net}, got {actual}')
        if codes.get(ref) != pinned[ref]:
            issues.append(f'{ref}: O5 power topology requires LCSC {pinned[ref]}')
    return issues



def references(board):
    import critical_reference as cr
    refs = cr.references(True)
    nets = cr.R6_NETS + cr.EXTENDED + cr.R10_PORT_NETS
    samples = cr.samples(board, nets, refs)
    fill = cr.fills(board, refs)
    missing = [s for s in samples if not cr.inside(fill[s[1]], s[2], s[3])]
    issues = []
    if not samples:
        issues.append('no critical routed-reference samples (unrouted board)')
    if missing:
        issues.append(f'{len(missing)} critical signal samples lack adjacent reference copper')
    return issues, {'samples': len(samples), 'unreferenced': len(missing), 'by_net_layer': cr._group(missing)}



def contract(text):
    """R10 netlist contract (K-contract): connectors, U1 pin map, port power and UART isolation, camera UART, pinned
    parts, removed R9 parts and nets. Population (S-4) and check_actuators (K-actuators) run as their own rules."""
    issues = []
    codes = {}
    pins, values = actuators.pad_nets(text, codes)
    issues += uart_ports(pins, values, codes) + port_power(pins, values, codes) + camera_uart(pins, values, codes)
    fps = {properties(f)['Reference'].items[2].atom: f for f in read(text).children('footprint')}
    refs = [properties(f)['Reference'].items[2].atom for f in read(text).children('footprint')]
    if len(refs) != len(set(refs)):
        issues.append('duplicate footprint reference')
    rf = re.compile(r'(U3[01]|J3[01]|Q3\d|[RCDLQ]3\d\d|D3[01]|L30|FB3[01]|TP30)')
    for ref in sorted((REMOVED & fps.keys()) | {r for r in fps if rf.fullmatch(r)}):
        issues.append(f'{ref}: removed R9 RF/servo/camera component remains')
    for ref, nets in CONNECTORS.items():
        if tuple(pins.get(f'{ref}.{i}') for i in range(1, len(nets) + 1)) != nets:
            issues.append(f'{ref}: connector pin mapping must be {nets}')
        electrical = {k for k in pins if k.startswith(ref + '.') and k.split('.')[-1].isdigit()}
        if electrical != {f'{ref}.{i}' for i in range(1, len(nets) + 1)}:
            issues.append(f'{ref}: wrong electrical pin count')
    with (ROOT / 'm3_design/assembly_review/sources/r8_design/pin_table.tsv').open() as table:
        expected_mcu = {row['pin']: row['r8_net'] for row in csv.DictReader(table, delimiter='\t')}
    expected_mcu.update(MCU)
    expected_mcu.update({pin: 'NC' for pin in ('46', '47', '53', '54')})
    for pin, net in expected_mcu.items():
        actual = pins.get('U1.' + pin)
        if actual != net and not (net == 'NC' and (actual is None or actual.startswith('unconnected-'))):
            issues.append(f'U1.{pin}: must be {net}, got {actual}')
    for ref, (code, land) in PARTS.items():
        if codes.get(ref) != code or ref not in fps or fps[ref].items[1].atom != 'rocket:' + land:
            issues.append(f'{ref}: must use {code} on rocket:{land}')
    forbidden = re.compile(r'^(PYRO|ARM|ACT_|SERVO|RAW_ACT|BAT_IN)')
    for ref in ('J410', 'J420', 'U410', 'U420', 'U411', 'U421', 'U412', 'U422'):
        nets = [n for p, n in pins.items() if p.startswith(ref + '.') and n and forbidden.match(n)]
        if nets:
            issues.append(f'{ref}: external port touches safety nets {nets}')
    for net in set(pins.values()) - {None}:
        if re.match(r'^(GNSS_|3V3_GNSS|3V3_RADIO|RADIO_(RF|SCK|MOSI|MISO|NSS|BUSY|DIO|NRST|TXEN|RXEN))', net):
            issues.append(f'{net}: obsolete on-board RF net remains')
    return issues


def functional(text):
    """The whole netlist-level contract in one call (kept for the generators' quick check)."""
    return actuators.check(text, profile='r10') + population(text) + contract(text)


# ======================================================================================================================
# R10 constants
# ======================================================================================================================
# R1-07: the safety parts that must be assembled (the task list, plus the RAW_ACT sense divider, the load-switch
# driver and the cold pull-up, all of which the F8 functions rely on). REQUIRED_FITTED (above) adds every R10 contract
# part and check_actuators' pinned parts.
SAFETY_FITTED = {'R134', 'R126', 'R127', 'R128', 'C126', 'Q124', 'Q120', 'Q121', 'R120', 'C120', 'R121', 'Q122',
                 'J124', 'J121', 'D120', 'R129', 'R130', 'R131', 'R132', 'R133', 'R173', 'R175', 'R178', 'R180',
                 'R168', 'R170', 'R172', 'R124', 'R177', 'C122', 'C127', 'C128', 'C129'}
REQUIRED_FITTED |= SAFETY_FITTED
ARM_REF = 'J124'
RAW, BUS = 'RAW_ACT', 'PYRO1_BUS'
ARMED = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')
RAILS = frozenset({'GND', '3V3', '3V3A'})        # net-path searches stop here (a divider foot is not a feed)
MAX_PART_NETS = 4                               # parts with more distinct nets (ICs, U1) do not pass a path
ARMED_SIDE = re.compile(r'^(PYRO1_|ARM1_)')
RAW_SIDE = re.compile(r'^RAW_ACT(_SENSE\w*)?$')
LOAD_SWITCH = {'Q120': ('BAT_IN', 'ACT_FET_S'), 'Q121': ('RAW_ACT', 'ACT_FET_S')}   # (drain, source); gate ACT_GATE
PFET_ROLES = {'S': ('1', '2', '3'), 'G': ('4',), 'D': ('5', '6', '7', '8', '9')}     # AON6403 PDFN 5x6 (AOS)
NFET_ROLES = {'S': ('1', '2', '3'), 'G': ('4',), 'D': ('5',)}                       # AON7524 DFN 3x3 (AOS)
ARM_GAP = 1.5                                   # mm, r10_plan section 2 item 2 and R1-m10
PORT_NET = re.compile(r'^(GPS_|RADIO_|CAM_|PORT_)')
SAFE_NET = re.compile(r'^(PYRO1_|ARM1_|ACT_|RAW_ACT)')
MCU_REF = 'U1'
DEFAULT_CLEARANCE = 0.15                       # mm, used only when the board carries no default net class
J122_ROWS = {'signal': ('1', '4', '7', '10'), 'plus': ('2', '5', '8', '11'), 'ground': ('3', '6', '9', '12')}
BOARD_WIDTH, BOARD_MAX = 46.0, 120.0            # P1
F1_MIN = 209.0                                  # Hz, R9's plate floor, kept (r10_mated, pinned, D 5)
WIRE_ENTRY = {'J121': '-x', 'J124': '-x'}       # r10_plan section 2 item 2
WIRE_ROOM = 6.25                                # mm, R8 / R9 P-11
BOT_THT, BOT_M3 = 1.5, 3.5                      # mm, R9 M-6 without its pyro-via term (a pyro spacing rule)
IMU_ROTATION_R10 = 180.0                        # R9 D-S7-06 kept: U4 bottom, rotation 180
IMU_MAPS = {0.0: 'M3_R5 axis map: +X_imu = +x_board, +Y_imu = +y_board; roll = +gyro_Y',
            180.0: 'R9 D-S7-06 axis map: +X_imu = -x_board, +Y_imu = -y_board; roll = -gyro_Y'}
WORD_LEGENDS_R10 = {'ARM': 'J124', 'IGN': 'J121', 'BAT': 'J1', 'CAM': 'J9', 'SWD': 'J2', 'SERVO': 'J122',
                    'PULL': 'J123', 'GPS': 'J410', 'RADIO': 'J420'}
TERMINAL_PINS_R10 = (('J124', (('1', 'BUS1'), ('2', 'RAW'))),
                     ('J121', (('1', 'E1-'), ('2', 'E1+'))),
                     ('J1', (('1', 'BAT+'), ('2', 'GND'))),
                     ('J400', (('1', 'SW'), ('2', 'SW'))),
                     ('J123', (('1', 'PULL'), ('2', 'GND'))))
EPS = 1e-3


def real_net(n):
    return bool(n) and not n.startswith('unconnected-')


@contextmanager
def patched(module, **values):
    old = {k: getattr(module, k) for k in values}
    try:
        for k, v in values.items():
            setattr(module, k, v)
        yield
    finally:
        for k, v in old.items():
            setattr(module, k, v)


def part_nets(board):
    """{ref: set of real nets on its pads}, from the board's own pad nets."""
    return {f.GetReference(): {p.GetNetname() for p in f.Pads() if real_net(p.GetNetname())}
            for f in board.GetFootprints()}


def net_reach(nets_of, start, skip=(), stop=RAILS):
    """Nets reachable from `start` through parts (any part with <= MAX_PART_NETS nets, `skip` excepted), not through
    the rails. Returns {net: (previous net, part)} (start maps to None)."""
    members = {}
    for ref, nets in nets_of.items():
        for n in nets:
            members.setdefault(n, set()).add(ref)
    came, queue = {start: None}, [start]
    while queue:
        n = queue.pop()
        if n in stop and n != start:
            continue
        for ref in sorted(members.get(n, ())):
            if ref in skip or len(nets_of[ref]) > MAX_PART_NETS:
                continue
            for m in sorted(nets_of[ref]):
                if m not in came:
                    came[m] = (n, ref)
                    queue.append(m)
    return came


def net_path(came, net):
    out = [net]
    while came.get(net):
        net, ref = came[net]
        out[:0] = [net, f'[{ref}]']
    return ' '.join(out)


# ======================================================================================================================
# copper connectivity (geometry only: net labels on tracks, vias, fills and drawings are ignored)
# ======================================================================================================================
def copper_nodes(board):
    """[(key, layer, shape, bbox, pad-or-None, net, label)] of every copper pad, track, arc, via, fill island and
    copper drawing. One key per physical item (a pad or via spans its layers)."""
    import pcbnew
    import check_r8 as r8
    layers = list(board.GetEnabledLayers().CuStack())
    out = []

    def add(key, lay, shape, pad, net, label):
        b = shape.BBox()
        out.append((key, lay, shape, (b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom()), pad, net, label))
    for f in board.GetFootprints():
        ref = f.GetReference()
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            for lay in layers:
                if p.IsOnLayer(lay):
                    add(p.m_Uuid.AsString(), lay, r8.item_shape(p, lay), p, p.GetNetname(), f'{ref}.{p.GetNumber()}')
        for g in f.GraphicalItems():
            if isinstance(g, pcbnew.PCB_SHAPE) and g.GetLayer() in layers:
                add(g.m_Uuid.AsString(), g.GetLayer(), g.GetEffectiveShape(), None, g.GetNetname(), f'{ref} copper drawing')
    for t in board.GetTracks():
        kind = 'via' if t.GetClass() == 'PCB_VIA' else 'track'
        at = t.GetPosition() if kind == 'via' else t.GetStart()
        for lay in layers:
            if t.IsOnLayer(lay):
                add(t.m_Uuid.AsString(), lay, r8.item_shape(t, lay), None, t.GetNetname(),
                    f'{kind} {t.GetNetname() or "(no net)"} ({pcbnew.ToMM(at.x):.2f}, {pcbnew.ToMM(at.y):.2f})')
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        for lay in layers:
            if z.IsOnLayer(lay) and z.HasFilledPolysForLayer(lay):
                fill = z.GetFilledPolysList(lay)
                for i in range(fill.OutlineCount()):
                    add(f'{z.m_Uuid.AsString()}/{lay}/{i}', lay, fill.UnitSet(i), None, z.GetNetname(),
                        f'{z.GetNetname() or "(no net)"} fill on {board.GetLayerName(lay)}')
    for d in board.GetDrawings():
        if isinstance(d, pcbnew.PCB_SHAPE) and d.GetLayer() in layers:
            add(d.m_Uuid.AsString(), d.GetLayer(), d.GetEffectiveShape(), None, d.GetNetname(), 'board copper drawing')
    return out


def copper_reach(nodes, net):
    """Grow from every pad of `net` through touching copper on a shared layer. Pads of other nets are recorded and not
    passed through; tracks, vias, fills and drawings are passed whatever their net. Returns ({foreign pad label: (its
    net, the item that touched it)}, reached item count)."""
    import pcbnew
    by_layer, by_key = {}, {}
    for i, n in enumerate(nodes):
        by_layer.setdefault(n[1], []).append(i)
        by_key.setdefault(n[0], []).append(i)
    seen = {n[0] for n in nodes if n[4] is not None and n[5] == net}
    queue = [i for k in seen for i in by_key[k]]
    foreign = {}
    while queue:
        i = queue.pop()
        _, lay, shape, box, _, _, label = nodes[i]
        for j in by_layer[lay]:
            key, _, other, b, pad, other_net, other_label = nodes[j]
            if key in seen or b[0] > box[2] or b[2] < box[0] or b[1] > box[3] or b[3] < box[1]:
                continue
            if not pcbnew.SHAPE.Collide(shape, other, 1):
                continue
            if pad is not None and other_net != net and other_net:
                foreign.setdefault(other_label, (other_net, label))
                continue
            seen.add(key)
            queue.extend(by_key[key])
    return foreign, len(seen)


def connectivity(ctx):
    if getattr(ctx, '_reach', None) is None:
        nodes = copper_nodes(ctx.board)
        ctx._reach = {net: copper_reach(nodes, net) for net in (RAW, BUS)}
    return ctx._reach


# ======================================================================================================================
# S-rules
# ======================================================================================================================
def s1(ctx):
    """ARM break (AGENTS.md 2.1): J124 is the only thing between RAW_ACT and the armed bus."""
    issues, ev = [], {}
    f = ctx.fps.get(ARM_REF)
    if f is None:
        return ['S-1: J124 (ARM terminal) missing'], ev
    pads = sorted((p.GetNumber(), p.GetNetname()) for p in f.Pads() if p.GetNumber())
    ev['j124_pads'] = pads
    if sorted(n for _, n in pads) != sorted((BUS, RAW)):
        issues.append(f'S-1: J124 must have exactly one {RAW} and one {BUS} pad (has {pads})')
    nets_of = part_nets(ctx.board)
    came = net_reach(nets_of, RAW, skip={ARM_REF})
    for net in ARMED:
        if net in came:
            issues.append(f'S-1: {RAW} reaches the armed net {net} without J124: {net_path(came, net)}')
    ev['raw_act_reaches'] = sorted(came)
    for ref, fp in ctx.fps.items():
        if re.fullmatch(r'TP\d+', ref):
            on = sorted({p.GetNetname() for p in fp.Pads()} & set(ARMED))
            if on:
                issues.append(f'S-1: test pad {ref} on armed copper {on} (a clip from it bypasses the ARM plug)')
    reach = connectivity(ctx)
    for start, other in ((RAW, ARMED), (BUS, (RAW,))):
        foreign, count = reach[start]
        ev[f'{start}_copper_items'] = count
        for label, (net, via) in sorted(foreign.items()):
            if net in other:
                issues.append(f'S-1: {start} copper reaches {label} ({net}) through {via}: the ARM break is bridged')
    return issues, ev


def s2(ctx):
    """Pyro feed (AGENTS.md 2.2): RAW_ACT only from BAT_IN through the Q120 / Q121 load switch; the armed side only
    from RAW_ACT through J124."""
    issues, ev = [], {}
    for ref, (drain, source) in LOAD_SWITCH.items():
        f = ctx.fps.get(ref)
        if f is None:
            issues.append(f'S-2: load switch {ref} missing')
            continue
        roles = {}
        for p in f.Pads():
            for role, nums in PFET_ROLES.items():
                if p.GetNumber() in nums:
                    roles.setdefault(role, set()).add(p.GetNetname())
        ev[ref] = {k: sorted(v) for k, v in roles.items()}
        want = {'D': {drain}, 'S': {source}, 'G': {'ACT_GATE'}}
        if roles != want:
            issues.append(f'S-2: {ref} must be drain {drain}, source {source}, gate ACT_GATE (is {ev[ref]})')
    nets_of = part_nets(ctx.board)
    came = net_reach(nets_of, RAW, skip={ARM_REF, 'Q121'})
    bad = sorted(n for n in came if not RAW_SIDE.match(n) and n not in RAILS)
    issues += [f'S-2: {RAW} is joined to {n} other than through Q121: {net_path(came, n)}' for n in bad]
    ev['raw_side'] = sorted(came)
    came = net_reach(nets_of, BUS, skip={ARM_REF})
    bad = sorted(n for n in came if not ARMED_SIDE.match(n) and n not in RAILS)
    issues += [f'S-2: the armed bus is joined to {n} other than through J124: {net_path(came, n)}' for n in bad]
    ev['armed_side'] = sorted(came)
    reach = connectivity(ctx)
    for start in (RAW, BUS):
        for label, (net, via) in sorted(reach[start][0].items()):
            if not (start == RAW and net in ARMED) and not (start == BUS and net == RAW):   # S-1's findings
                issues.append(f'S-2: {start} copper touches {label} ({net}) through {via}')
    return issues, ev


def gate_network(ctx, fet, roles, label):
    """(issues, evidence): the gate of `fet` has a pull-down resistor and a capacitor to its source and a series
    resistor to another net (its driver)."""
    f = ctx.fps.get(fet)
    if f is None:
        return [f'S-3: {fet} missing'], {}
    nets = {}
    for p in f.Pads():
        for role, nums in roles.items():
            if p.GetNumber() in nums:
                nets.setdefault(role, set()).add(p.GetNetname())
    if len(nets.get('G', ())) != 1 or len(nets.get('S', ())) != 1:
        return [f'S-3: {fet} gate / source pads not on one net each ({nets})'], {}
    gate, source = next(iter(nets['G'])), next(iter(nets['S']))
    found = {'pull': [], 'cap': [], 'series': []}
    for ref, nn in part_nets(ctx.board).items():
        if gate not in nn or len(nn) != 2 or len(ctx.fps[ref].Pads()) != 2:
            continue
        other = next(iter(nn - {gate}))
        kind = ref.rstrip('0123456789')
        if other == source and kind == 'R':
            found['pull'].append(ref)
        elif other == source and kind == 'C':
            found['cap'].append(ref)
        elif kind == 'R':
            found['series'].append((ref, other))
    issues = []
    for key, what in (('pull', f'a resistor from the gate ({gate}) to the source ({source})'),
                      ('cap', f'a gate-source capacitor ({gate} to {source})'),
                      ('series', f'a series resistor into the gate ({gate})')):
        if not found[key]:
            issues.append(f'S-3: {label} {fet}: no {what}')
    return issues, dict(gate=gate, source=source, **found)


def s3(ctx):
    issues, ev = [], {}
    found, ev['Q124'] = gate_network(ctx, 'Q124', NFET_ROLES, 'pyro FET')
    issues += found
    u1 = {p.GetNetname() for p in ctx.fps['U1'].Pads()} if 'U1' in ctx.fps else set()
    if ev['Q124'] and not any(other in u1 for _, other in ev['Q124']['series']):
        issues.append('S-3: pyro FET Q124: no series resistor from a U1 pin into the gate')
    for fet in ('Q120', 'Q121'):
        found, ev[fet] = gate_network(ctx, fet, PFET_ROLES, 'load switch')
        issues += found
    return sorted(set(issues)), ev


def board_population(board, required=REQUIRED_FITTED):
    """R1-07 on the loaded board: present, not DNP / excluded from BOM or position files / board-only."""
    import pcbnew
    issues, fps = [], {f.GetReference(): f for f in board.GetFootprints()}
    flags = {'dnp': pcbnew.FP_DNP, 'exclude_from_bom': pcbnew.FP_EXCLUDE_FROM_BOM,
             'exclude_from_pos_files': pcbnew.FP_EXCLUDE_FROM_POS_FILES, 'board_only': pcbnew.FP_BOARD_ONLY}
    for ref in sorted(required):
        f = fps.get(ref)
        if f is None:
            issues.append(f'{ref}: required fitted part missing from the board')
            continue
        bad = [name for name, bit in flags.items() if f.GetAttributes() & bit]
        if f.GetValue().strip().upper() in ('DNP', 'NC', 'NF', 'NOFIT'):
            bad.append(f'value {f.GetValue()}')
        if bad:
            issues.append(f'{ref}: required fitted part excluded ({", ".join(bad)})')
    return issues


def s4(ctx):
    issues, ev = [], dict(required=len(REQUIRED_FITTED), safety=sorted(SAFETY_FITTED))
    issues += board_population(ctx.board)
    if ctx.text is not None:
        issues += population(ctx.text)
    sch = Path(ctx.board_path).with_suffix('.kicad_sch') if ctx.board_path else None
    if sch is None or not sch.is_file():
        issues.append(f'schematic {sch} not found: the required-fitted check needs the schematic too')
    else:
        issues += [f'schematic: {i}' for i in schematic_population(sch)]
        ev['schematic'] = sch.name
    for name, path in (('BOM', ctx.bom), ('CPL', ctx.cpl)):
        if path:
            issues += [f'{name}: {i}' for i in assembly_population(Path(path).read_text())]
            ev[name] = str(path)
        else:
            ev[name] = 'not supplied (board and schematic flags checked)'
    return [f'S-4: {i}' for i in sorted(set(issues))], ev


def arm_gap(board, limit=ARM_GAP):
    """R1-m10: J124's own pads and the RAW_ACT / PYRO1_BUS copper at J124, measured, never exempting same-part pairs.

    Pad edge to pad edge on every copper layer both pads are on; then every RAW_ACT item against every PYRO1_BUS item
    on the same layer, clipped to J124's courtyard united with the pad field's bounding box grown by `limit`."""
    import pcbnew
    import check_r8 as geometry
    import pyro_probe
    f = board.FindFootprintByReference(ARM_REF)
    if f is None:
        return ['J124 missing'], {}
    pads = [p for p in f.Pads() if p.GetNumber() in ('1', '2')]
    if len(pads) != 2 or {p.GetNetname() for p in pads} != {RAW, BUS}:
        return ['J124 requires one RAW_ACT and one PYRO1_BUS pad'], {}
    issues, ev = [], {'pad_to_pad': {}}
    for lay in board.GetEnabledLayers().CuStack():
        if all(p.IsOnLayer(lay) for p in pads):
            g = geometry.min_gap(geometry.item_shape(pads[0], lay), geometry.item_shape(pads[1], lay), limit + 5)
            ev['pad_to_pad'][board.GetLayerName(lay)] = g
            if g is None or g < limit - EPS:
                issues.append(f'J124 pad to pad {g:.3f} mm on {board.GetLayerName(lay)}; minimum {limit} mm')
    boxes = [p.GetBoundingBox() for p in pads]
    grow = pcbnew.FromMM(limit)
    bounds = (min(b.GetLeft() for b in boxes) - grow, min(b.GetTop() for b in boxes) - grow,
              max(b.GetRight() for b in boxes) + grow, max(b.GetBottom() for b in boxes) + grow)
    window = pcbnew.SHAPE_POLY_SET()
    window.NewOutline()
    for x, y in ((bounds[0], bounds[1]), (bounds[2], bounds[1]), (bounds[2], bounds[3]), (bounds[0], bounds[3])):
        window.Append(x, y)
    court = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    if court.OutlineCount():
        window.BooleanAdd(pcbnew.SHAPE_POLY_SET(court))
    items = []
    for item in geometry.net_items(board, lambda n: n in (RAW, BUS)):
        poly = pyro_probe._poly(item)
        poly.BooleanIntersection(window)
        if poly.OutlineCount():
            items.append((*item[:3], poly))
    closest = None
    for a in items:
        for b in items:
            if a[1] != RAW or b[1] != BUS or a[2] != b[2]:
                continue
            gap = geometry.min_gap(a[3], b[3], 10)
            if gap is not None and (closest is None or gap < closest[0]):
                closest = gap, a[0], b[0], board.GetLayerName(a[2])
    if closest is None or closest[0] < limit - EPS:
        where = f'{closest[0]:.3f} mm, {closest[1]} to {closest[2]} on {closest[3]}' if closest else 'not measured'
        issues.append(f'J124 RAW_ACT–PYRO1_BUS copper gap must be >={limit} mm ({where})')
    bb = window.BBox()
    ev.update(closest=closest, window_mm=[pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(),
                                                                       bb.GetBottom())])
    return issues, ev


def s5(ctx):
    issues, ev = arm_gap(ctx.board)
    return [f'S-5: {i}' for i in issues], ev


def default_clearance(board):
    import pcbnew
    try:
        return pcbnew.ToMM(board.GetDesignSettings().m_NetSettings.GetDefaultNetclass().GetClearance())
    except Exception:                                      # an older API or no net class: the documented default
        return DEFAULT_CLEARANCE


def s6(ctx):
    """External ports (O1 / O2 / F10): no port net shares a part, a copper item or the board default clearance with
    pyro / arming copper."""
    import pcbnew
    import check_r8 as r8
    issues, ev = [], {}
    for ref, nets in sorted(part_nets(ctx.board).items()):
        if ref == MCU_REF:
            continue                                       # the MCU is the intended common node (firmware, F10)
        ports, safe =sorted(n for n in nets if PORT_NET.match(n)), sorted(n for n in nets if SAFE_NET.match(n))
        if ports and safe:
            issues.append(f'S-6: {ref} joins port nets {ports} to pyro / arming nets {safe}')
    clr = default_clearance(ctx.board)
    ev['clearance_mm'] = clr
    safe = ctx.net_items(lambda n: bool(SAFE_NET.match(n or '')))
    worst = None
    for label, net, lay, shape, _ in ctx.net_items(lambda n: bool(PORT_NET.match(n or ''))):
        for l2, n2, lay2, s2, _ in safe:
            if lay2 != lay or not pcbnew.SHAPE.Collide(shape, s2, pcbnew.FromMM(clr) - 1):
                continue
            g = r8.min_gap(shape, s2, clr + 1)
            g = 0.0 if g is None else g
            where = f'{net} {label} to {n2} {l2} on {ctx.board.GetLayerName(lay)}'
            if worst is None or g < worst[0]:
                worst = (g, where)
            issues.append(f'S-6: {where}: {g:.3f} mm' + (' (shared copper)' if g == 0 else f' < {clr} mm'))
    ev['closest_violation'] = worst
    return sorted(set(issues)), ev


def s7(ctx):
    """J122 under O3 / O6: servo power off the board."""
    import pcbnew
    issues, ev = [], {}
    f = ctx.fps.get('J122')
    if f is None:
        return ['S-7: J122 missing'], ev
    pads = {p.GetNumber(): p for p in f.Pads() if p.GetNumber()}
    ev['pads'] = {k: p.GetNetname() for k, p in sorted(pads.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0)}
    for i, num in enumerate(J122_ROWS['signal'], 1):
        if num not in pads or pads[num].GetNetname() != f'SERVO{i}_OUT':
            issues.append(f'S-7: J122.{num} must be SERVO{i}_OUT (is {ev["pads"].get(num)})')
    for num in J122_ROWS['ground']:
        if num not in pads or pads[num].GetNetname() != 'GND':
            issues.append(f'S-7: J122.{num} (ground row) must be on GND (is {ev["pads"].get(num)})')
    plus = [pads[n] for n in J122_ROWS['plus'] if n in pads]
    if len(plus) != 4:
        issues.append('S-7: J122 middle row 2 / 5 / 8 / 11 incomplete')
    for p in plus:
        if real_net(p.GetNetname()):
            issues.append(f'S-7: J122.{p.GetNumber()} (servo + row) carries {p.GetNetname()}; O3: no board net')
    import check_r8 as r8
    for p in plus:
        for lay in ctx.board.GetEnabledLayers().CuStack():
            if not p.IsOnLayer(lay):
                continue
            shape = r8.item_shape(p, lay)
            for label, net, l2, s2, obj in ctx.items:
                if l2 != lay or obj == p:
                    continue
                if pcbnew.SHAPE.Collide(shape, s2, 1):
                    issues.append(f'S-7: {label} ({net}) touches J122.{p.GetNumber()} (servo + row) on '
                                  f'{ctx.board.GetLayerName(lay)}')
    return sorted(set(issues)), ev


# ======================================================================================================================
# mechanical and placement
# ======================================================================================================================
def m1(ctx):
    import pcbnew
    issues = []
    x0, y0, x1, y1 = ctx.outline
    width, length = x1 - x0, y1 - y0
    ev = dict(outline_mm=ctx.outline, width_mm=round(width, 3), length_mm=round(length, 3))
    if abs(width - BOARD_WIDTH) > 0.01:
        issues.append(f'M-1: board width {width:g} mm; P1 requires {BOARD_WIDTH:g} mm')
    if length > BOARD_MAX + 0.01:
        issues.append(f'M-1: board length {length:g} mm exceeds the P1 {BOARD_MAX:g} mm maximum')
    edges = [d for d in ctx.board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts
             and d.GetShape() != pcbnew.SHAPE_T_CIRCLE]
    mm = pcbnew.ToMM
    rect = (len(edges) == 1 and edges[0].GetShape() == pcbnew.SHAPE_T_RECT) or \
        (len(edges) == 4 and all(d.GetShape() == pcbnew.SHAPE_T_SEGMENT for d in edges) and
         all(abs(mm(d.GetStart().x) - mm(d.GetEnd().x)) < 1e-4 or abs(mm(d.GetStart().y) - mm(d.GetEnd().y)) < 1e-4
             for d in edges))
    if not rect or abs(x0) > 0.005 or abs(y0) > 0.005:
        issues.append(f'M-1: outline must be one rectangle from (0, 0) (found {len(edges)} edges from ({x0:g}, {y0:g}))')
    for d in ctx.board.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE and \
                abs(mm(d.GetRadius()) - 1.6) > 0.01:
            issues.append(f'M-1: Edge.Cuts circle at ({mm(d.GetCenter().x):g}, {mm(d.GetCenter().y):g}) is not a 3.2 mm hole')
    return issues, ev


def m2(ctx, board_sha=None):
    p = ctx.plate
    if p is None:
        return ['M-2: plate model (tools/plate_model.py --profile r10 on this board\'s fit report, --plate) not run'], {}
    f1 = p.get('f1', {}).get('r10_mated', {}).get('pinned_D5')
    issues = []
    if p.get('profile') != 'r10':
        issues.append(f'M-2: plate report profile {p.get("profile")!r}; R10 needs --profile r10')
    if board_sha and p.get('board_sha256') != board_sha:
        issues.append('M-2: the plate model report is not bound to this board (board_sha256 of its fit report)')
    if f1 is None or f1 < F1_MIN:
        issues.append(f'M-2: first plate mode {f1} Hz (r10_mated, pinned, D 5); minimum {F1_MIN} Hz')
    return issues, dict(f1_hz=f1, supports=p.get('supports'))


def m5(ctx, board_sha=None):
    rep = ctx.fit()
    issues = [f'M-5: fit_check: {i}' for i in rep.get('issues', [])]
    if rep.get('profile') != 'r10':
        issues.append(f'M-5: fit report profile {rep.get("profile")!r}; R10 needs fit_check --profile r10')
    if ctx.fit_given and board_sha and rep.get('board_sha256') != board_sha:
        issues.append('M-5: the fit report is not bound to this board (board_sha256)')
    ns, nt = rep.get('nearest_support'), rep.get('nearest_top_support')
    return issues, dict(width_mm=rep.get('width_mm'), length_mm=rep.get('length_mm'), supports=rep.get('supports'),
                        nearest_support=ns, nearest_top_support=nt)


def m6(ctx):
    import pcbnew
    import check_r8 as r8
    MM = pcbnew.FromMM
    issues = []
    supports = ctx.fit().get('supports', [])
    tht = [(f.GetReference(), p.GetPosition(), max(p.GetSize().x, p.GetSize().y) // 2)
           for f in ctx.board.GetFootprints() for p in f.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    for f in ctx.board.GetFootprints():
        if not f.IsFlipped():
            continue
        ref = f.GetReference()
        if any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in f.Pads()):
            issues.append(f'M-6: bottom part {ref} has through-hole pads (bottom parts SMD only)')
        cy = r8.courtyard(f)
        for other, c, r in tht:
            if other == ref:
                continue
            d = r8.min_gap(cy, pcbnew.SHAPE_CIRCLE(c, r), BOT_THT + 1)
            if d is not None and d < BOT_THT - EPS:
                issues.append(f'M-6: bottom part {ref} is {d:.2f} mm from {other}\'s through-hole pad (minimum {BOT_THT})')
                break
        for c in supports:
            d = r8.min_gap(cy, pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])), 1), BOT_M3 + 1)
            if d is not None and d < BOT_M3 - EPS:
                issues.append(f'M-6: bottom part {ref} is {d:.2f} mm from the M3 centre {tuple(c)} (minimum {BOT_M3})')
    return sorted(set(issues)), dict(supports=supports)


def m7(ctx):
    """check_r9.m7 (U4 bottom, rotation, lever arm, no via or fill under U4 / U5) at R10's recorded rotation, with the
    axis map read from the board."""
    import check_r9 as r9
    with patched(r9, IMU_ROTATION={**r9.IMU_ROTATION, ctx.board.GetTitleBlock().GetRevision(): IMU_ROTATION_R10}):
        issues, ev = r9.m7(ctx)
    u4 = ctx.fps.get('U4')
    if u4 is not None:
        rot = round(u4.GetOrientationDegrees() % 360.0, 3)
        ev['board_axis_map'] = dict(side='bottom' if u4.IsFlipped() else 'top', rotation=rot,
                                    map=IMU_MAPS.get(rot, 'no recorded map'))
    return issues, ev


def entry_dir(f):
    """Board direction of a terminal's wire entry: the footprint description's "wire entry +y" (the R10 DB125
    lands), else DB128's local -y (check_r9.entry_dir)."""
    m = re.search(r'wire entry ([+-])([xy])', f.GetLibDescription() or '')
    sign, axis = (m[1], m[2]) if m else ('-', 'y')
    lx, ly = (1.0 if sign == '+' else -1.0, 0.0) if axis == 'x' else (0.0, 1.0 if sign == '+' else -1.0)
    th = math.radians(f.GetOrientationDegrees())
    c, s = math.cos(th), math.sin(th)
    dx, dy = lx * c + ly * s, -lx * s + ly * c
    if abs(dx) > abs(dy):
        return '+x' if dx > 0 else '-x'
    return '+y' if dy > 0 else '-y'


def p11(ctx):
    import check_r9 as r9
    issues, ev = [], {}
    for ref, want in WIRE_ENTRY.items():
        f = ctx.fps.get(ref)
        if f is None:
            issues.append(f'P-11: {ref} missing')
            continue
        d = entry_dir(f)
        ev[ref] = dict(entry=d)
        if d != want:
            issues.append(f'P-11: {ref} wires enter from {d}; R10 sets {want} (r10_plan section 2 item 2)')
        face, box = r9.entry_face(ctx, f, d)
        if d in ('-x', '+x'):
            room = r9.wire_room(face)
            ev[ref]['wire_room_mm'] = round(room, 3)
            if room < WIRE_ROOM - EPS:
                issues.append(f'P-11: {ref} has {room:.2f} mm of wire room to the bore wall (minimum {WIRE_ROOM}, R8)')
        else:
            issues += [f'P-11: {i}' for i in r9.axial_ok(ctx, f, d, face, box)]
    return issues, ev


# ======================================================================================================================
# K-rules
# ======================================================================================================================
def k_contract(ctx):
    if ctx.text is None:
        return ['K-contract: no board file text (pass the saved board path)'], {}
    return contract(ctx.text), {}


def k_actuators(ctx):
    path = ROOT / 'm3_design/check_actuators.py'
    sha = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    if ctx.text is None:
        return ['K-actuators: no board file text (pass the saved board path)'], dict(sha256=sha)
    return [f'check_actuators: {i}' for i in actuators.check(ctx.text, ctx.dru, profile='r10')], dict(sha256=sha)


def k_legends(ctx):
    import check_r7 as r7
    import check_r8 as r8
    with patched(r7, WORD_LEGENDS=WORD_LEGENDS_R10), patched(r8, TERMINAL_PINS=TERMINAL_PINS_R10):
        issues = list(r7.duplicate_ids(ctx.board)) + list(r7.pin_legends(ctx.board)) + \
            list(r7.legend_subjects(ctx.board))
        found, ev = r8.terminal_legends(ctx.board)
    return issues + found, dict(terminal_legends=ev)


def k_reference(ctx):
    issues, ev = references(ctx.board)
    return [f'K-reference: {i}' for i in issues], ev


def retained_routing(ctx):
    """Unchanged camera / flash bypass and exposed-contact copper contracts (not pyro spacing: probe contact)."""
    import check_r7 as r7
    import pcbnew
    issues, camera = r7.camera_bypass(ctx.board)
    copper = r7.copper_shapes(ctx.board)
    for footprint in ctx.board.GetFootprints():
        ref = footprint.GetReference()
        if not (ref.startswith('TP') or ref == 'J2'):
            continue
        gap = 0.508 if ref == 'J2' else 1.0
        for pad in footprint.Pads():
            if not pad.GetNumber() or pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            for layer, mask in ((pcbnew.F_Cu, pcbnew.F_Mask), (pcbnew.B_Cu, pcbnew.B_Mask)):
                if not pad.IsOnLayer(layer) or not pad.IsOnLayer(mask):
                    continue
                shape = pad.GetEffectiveShape(layer)
                for label, net, other, owner in copper[layer]:
                    if owner == pad or net == pad.GetNetname():
                        continue
                    if ref == 'J2' and isinstance(owner, pcbnew.PAD) and owner.GetParentFootprint() == footprint:
                        continue
                    if pcbnew.SHAPE.Collide(shape, other, pcbnew.FromMM(gap) - 1000):
                        issues.append(f'{ref}.{pad.GetNumber()}: bare contact clearance {gap} mm to {label}')
    pads = r7.pads_by_ref(ctx.board)
    flash, bypass = pads.get(('U3', '8')), pads.get(('C29', '1'))
    evidence = {'camera_bypass': camera}
    if flash is None or bypass is None:
        issues.append('flash local bypass U3.8/C29.1 missing')
    else:
        gap = math.dist(tuple(flash.GetPosition()), tuple(bypass.GetPosition())) / 1e6
        route = r7.direct_route(ctx.board, flash, bypass)
        evidence['flash'] = dict(pad_distance_mm=gap, direct_route_mm=route)
        if gap > 2 or route is None or route > 3:
            issues.append('C29 flash bypass requires <=2 mm pad distance and <=3 mm direct route')
    gate_pad = ctx.fps.get('TP122')
    if gate_pad is None or not gate_pad.IsFlipped():
        issues.append('TP122 must remain on B.Cu')
    return [f'K-retained: {i}' for i in issues], evidence


# ======================================================================================================================
def _r9(name):
    def run(c, s):
        import check_r9 as r9
        return getattr(r9, name)(c)
    return run


RULES = [
    ('S-1', 'ARM break (J124 the only RAW_ACT to armed link)', lambda c, s: s1(c)),
    ('S-2', 'pyro feed only through the load switch and J124', lambda c, s: s2(c)),
    ('S-3', 'gate networks defined off', lambda c, s: s3(c)),
    ('S-4', 'required-fitted safety parts (R1-07)', lambda c, s: s4(c)),
    ('S-5', 'J124 RAW_ACT to PYRO1_BUS gap >= 1.5 mm (R1-m10)', lambda c, s: s5(c)),
    ('S-6', 'external ports apart from pyro / arming copper', lambda c, s: s6(c)),
    ('S-7', 'J122 servo + row off board, GND row on GND (O3)', lambda c, s: s7(c)),
    ('K-contract', 'R10 netlist contract', lambda c, s: k_contract(c)),
    ('K-actuators', 'check_actuators --profile r10', lambda c, s: k_actuators(c)),
    ('LC-1', 'local clearance overrides', lambda c, s: __import__('check_r9').lc1(c.board)),
    ('M-1', 'outline 46 mm wide, length <= 120 mm', lambda c, s: m1(c)),
    ('M-3', 'J122 tie holes', _r9('m3')),
    ('M-5', 'fit (profile r10)', lambda c, s: m5(c, s)),
    ('M-6', 'bottom keep-outs', lambda c, s: m6(c)),
    ('M-7', 'IMU and MEMS', lambda c, s: m7(c)),
    ('P-11', 'terminal entry', lambda c, s: p11(c)),
    ('F9-1', 'input protection at J1', _r9('f9')),
    ('T-1', 'panel-tab windows', _r9('t1')),
    ('K-legends', 'legends and ids', lambda c, s: k_legends(c)),
    ('M-2', 'vibration (plate model, r10_mated)', lambda c, s: m2(c, s)),
    ('P-8', 'sense resistors at the MCU end', _r9('p8')),
    ('K-copper', 'copper hygiene (vias in pads, joints, thermals, paste)', _r9('k_copper')),
    ('K-inner', 'In1 / In2 signal tracks', _r9('k_inner_signal')),
    ('K-reference', 'critical signal reference copper', lambda c, s: k_reference(c)),
    ('K-retained', 'bare contacts, flash and camera bypass, TP122', lambda c, s: retained_routing(c)),
]
STAGES = {'functional': {'S-1', 'S-2', 'S-3', 'S-4', 'S-5', 'S-6', 'S-7', 'K-contract', 'K-actuators'}}
STAGES['placement'] = STAGES['functional'] | {'LC-1', 'M-1', 'M-3', 'M-5', 'M-6', 'M-7', 'P-11', 'F9-1', 'T-1',
                                              'K-legends'}
STAGES['full'] = {rid for rid, _, _ in RULES}


def make_ctx(board, folder=None, board_path=None, fit=None, plate=None, seed=None, dru=None, text=None, bom=None,
             cpl=None):
    import check_r9 as r9
    import fit_check as fc

    class R10Ctx(r9.Ctx):
        def fit(self):
            if self.fit_report is None:
                self.fit_report = fc.check_board(self.board, self.folder or Path('.'), profile='r10')
            return self.fit_report
    ctx = R10Ctx(board, folder, board_path, fit, plate, seed, 0.0, dru)
    if text is None and board_path and Path(board_path).is_file():
        text = Path(board_path).read_text()
    ctx.text, ctx.bom, ctx.cpl, ctx.fit_given, ctx._reach = text, bom, cpl, fit is not None, None
    return ctx


def check_board(board, folder=None, board_path=None, fit=None, plate=None, seed=None, only=None, stage='full',
                board_sha=None, dru=None, text=None, bom=None, cpl=None):
    """Run the rules of `stage` (or `only`) on a loaded board; each rule that cannot run fails."""
    import route_check as rc
    ctx = make_ctx(board, folder, board_path, fit, plate, seed, dru, text, bom, cpl)
    previous = rc.PROFILE
    rc.set_profile('r10')
    out, flat = {}, []
    try:
        for rid, title, fn in RULES:
            if (only and rid not in only) or (not only and rid not in STAGES[stage]):
                continue
            try:
                issues, ev = fn(ctx, board_sha)
            except Exception as e:                       # a rule that cannot run fails, it never passes
                issues, ev = [f'{rid}: could not run: {type(e).__name__}: {e}'], {}
            out[rid] = dict(title=title, ok=not issues, issues=issues, evidence=ev)
            flat += [i if i.startswith(rid) else f'{rid}: {i}' for i in issues]
    finally:
        rc.set_profile(previous)
    return dict(profile='r10', stage=stage, complete=stage == 'full' and not only, ok=not flat, rules=out,
                issues=flat, failing=[k for k, v in out.items() if not v['ok']])


def file_sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def main():
    import pcbnew
    import fit_check as fc
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board', nargs='?', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--report', type=Path)
    ap.add_argument('--fit', type=Path, help='tools/fit_check.py --profile r10 --report of this board')
    ap.add_argument('--plate', type=Path, help='tools/plate_model.py --profile r10 --json of this board\'s fit report')
    ap.add_argument('--seed', type=Path, help='accepted for check_r9\'s command shape; R10 has no rule H to seed')
    ap.add_argument('--only', help='comma-separated rule ids')
    ap.add_argument('--stage', choices=tuple(STAGES), default='full')
    ap.add_argument('--bom', type=Path, help='JLC BOM CSV to check for the required-fitted parts')
    ap.add_argument('--cpl', type=Path, help='JLC CPL CSV to check for the required-fitted parts')
    a = ap.parse_args()
    bp = a.board.resolve()
    load = lambda p: json.loads(p.read_text()) if p else None      # noqa: E731

    def inputs():
        r = fc.input_hashes(bp)
        for p in (bp.with_suffix('.kicad_dru'), bp.with_suffix('.kicad_pro'), bp.with_suffix('.kicad_sch')):
            r[p.name] = file_sha(p)
        return r
    before = inputs()
    sha = before[bp.name]
    fit = load(a.fit)
    if fit is not None and fit.get('board_sha256') != sha:
        print('FAIL the fit report is not bound to this board (board_sha256)')
        return 1
    report = check_board(pcbnew.LoadBoard(str(bp)), bp.parent, bp, fit=fit, plate=load(a.plate), seed=None,
                         only=set(a.only.split(',')) if a.only else None, stage=a.stage, board_sha=sha,
                         bom=a.bom, cpl=a.cpl)
    if a.seed:
        report['seed_note'] = f'{a.seed} not read: R10 has no pyro rule H (r10_plan section 2 item 1)'
    if before != inputs():
        report['issues'].append('board, model, rules or schematic changed during check')
        report['ok'] = False
    report.update(board_sha256=sha, inputs_sha256=before, checker_sha256=file_sha(__file__))
    for rid, r in report['rules'].items():
        print(f"{rid:12s} {'OK  ' if r['ok'] else 'FAIL'} {r['title']}" + (f" ({len(r['issues'])})" if r['issues'] else ''))
    length = report['rules'].get('M-1', {}).get('evidence', {}).get('length_mm')
    if length is not None:
        print(f'board outline: {report["rules"]["M-1"]["evidence"]["width_mm"]:g} x {length:g} mm (P1: 46 mm wide, '
              f'<= {BOARD_MAX:g} mm long)')
    for i in report['issues']:
        print('FAIL', i)
    scope = a.stage if not a.only else 'selected rules'
    print(f'R10 CAD contract ({scope}):', 'OK' if report['ok'] else f"FAIL ({len(report['issues'])} findings in "
          f"{len(report['failing'])} rules: {', '.join(report['failing'])})")
    if a.report:
        a.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
