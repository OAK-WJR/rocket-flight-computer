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

Safety (AGENTS.md section 2, F8; single screw switch owner decision 2026-10-28):
  S-1   canonical pyro bus RAW_ACT: J124 and PYRO1_BUS are absent; R134.2 and R132.1 are on RAW_ACT behind Q121.
        Only named parts touch pyro / sense copper; no other part or copper bypasses R134 or the sense-divider tops
        (geometric copper connectivity includes tracks, arcs, vias, fill, drawings and copper text, any net or none).
  S-2   pyro feed: Q120 / Q121 are the back-to-back load switch BAT_IN -> ACT_FET_S -> RAW_ACT with gates on
        ACT_GATE; RAW_ACT is reached from no supply (BAT_IN, RAW_PROTECTED, ACT_FET_S, VLOGIC, ...) except through
        Q121; the downstream pyro / sense network has only its named rail ties and its copper touches no foreign pad
  S-3   gate networks defined off: Q124 (pyro) gate has a pull-down to its source, a gate-source capacitor and a series
        resistor from a U1 pin; Q120 / Q121 (P-FET load switch) gate has a gate-source resistor and capacitor and a
        series resistor from its driver; PC1 independently enables Q122 through R122, with R123 to GND
  S-4   R1-07 required fitted: every safety part (and every R10 contract part) is on the board, not DNP, not excluded
        from BOM or position files, not board-only, on the board and in the schematic; also in --bom / --cpl if given
  S-5   single screw switch: J400 contacts lead only through their 470 k resistors to BAT_IN and U9 EN; no part or
        copper bypasses the contact; obsolete ARM-terminal and fuse legends are rejected by K-legends
  S-6   external ports: no part (the MCU U1 excepted) has pads on both a port net (GPS_ / RADIO_ / CAM_ / PORT_) and a pyro / arming net
        (PYRO1_ / ARM1_ / ACT_ / RAW_ACT*); port copper >= the board default clearance from pyro / arming copper on
        the same layer (no shared copper item)
  S-7   J122 (O3): the middle (+) row 2 / 5 / 8 / 11 has no net and no copper touching it, the GND row 3 / 6 / 9 / 12
        is on GND, the signal row 1 / 4 / 7 / 10 on SERVO1-4_OUT
  S-8   R3-SAF-01: on In1 and In2 no track or zone fill of any net but GND (and the barrel's own net) lies within
        1.0 mm of a plated barrel (via or plated hole wall) of RAW_ACT, PYRO1_IGN, PYRO1_OUT or PYRO1_GATE
  S-9   R3-GATE-07 / AUD-6: current-path copper >= 0.5 mm on fire-only RAW_ACT / PYRO1_IGN / PYRO1_OUT,
        >= 1.0 mm on BAT_IN / ACT_FET_S. FIRE_TERMINALS prunes dead-end branches such as sense taps; pad necks
        (a segment ending in a pad no wider than the track) and named, measured FIRE_NARROW entries are excepted
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
  P-11  J1 / J121 wires enter from -x (owner, r10_plan 2 item 2; J1's wires leave the same west face, R3-MEC-02);
        the entry direction is read from the footprint
        description ("wire entry +y"), else DB128's local -y. Wire room to the bore wall: R8 / R9's 6.25 mm is R8's
        measured value (a non-regression floor, not a derived need). Owner OQ-1, 2026-10-28: R10's accepted floor is
        4.95 mm with 16-22 AWG in DB125 terminals, pending physical fit qualification
  F9-1  owner OQ-2, 2026-10-28: the R10 reverse hot-plug model must pass. Its extracted copper/parts, source curves,
        solver, complete corner set, numerical limits and convergence are checked; stale or failing evidence fails.
        The old part-distance premise is not used. This remains a simulation inference, not a bench result
  F9-2  GAP-2: C82 and D9 have short actual B.Cu OUT connections and local saved-copper GND paths to U9;
        endpoints, layers and loop lengths are reported. Engineering layout bounds, not electrical qualification
  T-1   panel tabs (D-R2-13): R9 barred the aft edge because the SMA jacks overhung it; R10 has no jack, and its east
        edge's aft third carries the three GH ports. Each end third must be held on both sides: a legal 5 mm tab on the
        west edge in the aft and in the forward third, and on the east side in each end third either a legal east-edge
        tab or a legal tab on that end's short edge within its east third (tools/tab_windows.py's clearances)
Kept contract and copper rules:
  K-contract   R10 netlist contract: pin map, connectors, port power / UART isolation, camera UART, parts, removed parts
  K-actuators  m3_design/check_actuators.py --profile r10 in process (check.sh also runs it on its own)
  K-loader     R3-MCU-01: every U1 pin that the H74x ROM bootloader uses (AN2606 Rev 64 Table 119, pp. 277-280) and
               that carries a net is in LOADER_R10 with that net, its recorded members (every other pad on the net, with
               its part value) and an electrical reason; pins the loader drives need a reason for the drive
  K-width      BAT_IN / RAW_PROTECTED tracks >= 0.3 mm, no 0.3 mm run > 2 mm (R8-GATE-04)
  K-legends    pinned revision / safety texts, shown safety refs (R8-GATE-02/03), duplicate ids, pin legends, legend subjects (R10 word legends), R10 terminal pin legends; AUD-10 counts subject distance for review;
               R3-MFG-01: no
               silkscreen item (board or footprint graphic, text, field), as its polygon, overlaps a pad's solder mask
               opening (pad copper + mask expansion) on its side
  K-copper     vias in pads, overlap-only joints, thermal policy, via paste (check_r9.k_copper); GAP-3 admits only
               two exact filled/capped GND vias in U401.11, with unchanged maker paste and a VIPPO order condition
  K-inner      In1 carries no track, In2 power and GND only (check_r9.k_inner_signal, route_check r10 classes)
  K-reference  (nets: the R6 / extended / port nets plus every signal-critical net of route_check's r10 classes,
               excluding only AUD-2's shared named slow-return list) samples have adjacent reference copper (critical_reference's extended set and the R10
               port nets): F.Cu over In1 GND; B.Cu over any In2 rail plane (GND, 3V3, 3V3A and R10's PORT_5V3,
               PORT_4V8, RAW_PROTECTED regions: decoupled DC rails, as R6 counted 3V3; Inference for the new ones);
               In1 / In2 tracks over F.Cu / B.Cu GND. An unreferenced sample passes only inside its own net's via
               antipad (REF_OWN_R of a same-net via, R9 D-S8-17) or as a recorded REF_STRAY (D-R2-10)
  K-region     R4-RTE-02, R5-RTE-01 / -02 / -06: every B.Cu track of a signal-critical net (route_check r10's pyro,
               crystal, usb, spi, uart, portctl classes minus AUD-2's named slow list: the same nets K-reference samples; sampled every 0.02 mm on its
               centre line and on both edges pushed 0.1 mm outward) and every B.Cu SMD pad of such a net (0.05 mm grid
               over the pad grown by 0.1 mm) lies over exactly one In2 plane net and over In2 copper, outside its own
               vias' antipads (REF_OWN_R) and the own through-hole pads' clearance voids (a no-copper region wholly
               inside the disc pad half-size + zone clearance + 0.05 mm); each connected B.Cu chain sees one plane net
  K-fill       R4-GATE-05: a copy of the board loaded from its file and refilled has the saved fill area in every zone
               layer (0.01 mm^2); a stale or hand-edited fill fails
  K-rules      R4-GATE-01: m3.kicad_dru is pinned by SHA-256 (it is generated by m3_design/r10_sch.py); the .kicad_pro
               keeps min clearance and every net class clearance >= 0.15 mm, the min track / via / hole figures at
               their recorded floors, no DRC rule severity "ignore" and no DRC exclusions
  K-retained   bare test pads 1.0 mm / Tag-Connect 0.508 mm from foreign copper, C29 flash bypass, camera bypass,
               TP122 on the bottom
"""
import argparse
from contextlib import contextmanager
import csv
import hashlib
import heapq
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

REQUIRED_FITTED = (set(actuators.PINNED) - {'C121', 'J124'}) | {
    'R131', 'C127', 'C129', 'C122', 'C84', 'U11', 'U12', 'U13',
    'R100', 'R101', 'R102', 'R103', 'C91', 'C92', 'C93', 'C100', 'C29',
    'J400', 'J410', 'J420', 'U400', 'U401', 'U402', 'U410', 'U420',
    'U411', 'U421'} | {f'{prefix}{n}' for prefix, numbers in
        (('R', range(440, 443)), ('R', range(450, 453)), ('C', (440, 443)),
         ('C', (450, 453)), ('D', (400, 401, 410, 411, 420, 421)),
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
       # D-R2-07 camera / buzzer; AUD-4 frees PC13; D-R2-09 status / VLOGIC sense pins.
       '7': 'NC', '8': 'BUZZ_DRV', '31': 'NC', '39': 'CAM_UART_OE', '41': 'CAM_PWR_EN', '42': 'CAM_FAULT_N',
       '16': 'ACT_EN_MCU', '17': 'NC', '28': 'LOGIC_SOURCE_ST', '29': 'BAT_FAULT_N', '30': 'VLOGIC_SENSE'}
PARTS = {'J1': ('C466970', 'M3_DB125_2P_GN'),
         'J121': ('C52993880', 'M3_DB125_2P_BK'),
         'J400': ('C161690', 'M3_GH_BM02B_GHS_TBT'),
         'J410': ('C161692', 'M3_GH_BM04B_GHS_TBT'), 'J420': ('C161692', 'M3_GH_BM04B_GHS_TBT'),
         'C84': ('C46550466', 'M3_MA_8x10'),
         'C92': ('C19666', 'C0603'),  # AUD-1: same qualified land as C23/C28; inferred effective-capacitance bound 2.211uF.
         'C120': ('C29936', 'C_0603_1608Metric'),  # AUD-3: same qualified land as C86/C97/C98; 100ms settling.
         'Q120': ('C431196', 'M3_AONR21357_DFN3x3A_EP1'),
         'Q121': ('C431196', 'M3_AONR21357_DFN3x3A_EP1')}
PARTS.update({f'R{n}': ('C25744', 'R0402') for n in (412, 422, 432)})  # AUD-7.
REMOVED = {'U30', 'U31', 'J30', 'J31', 'C121', 'C150', 'C151', 'U7', 'U8', 'L3', 'J124'}
# AUD-4 / AUD-5 / AUD-8: reject stale parts as well as removing required-population obligations.
AUD_REMOVED = {'J123', 'R160', 'R161', 'C160', 'D122', 'TP84', 'TP85', 'TP86', 'TP87', 'TP89', 'TP92',
               'U412', 'U422', 'R443', 'R453', 'C441', 'C442', 'C451', 'C452'}
REMOVED |= AUD_REMOVED


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
    for ref in ('U412', 'U422', 'R443', 'R453', 'C441', 'C442', 'C451', 'C452'):
        if ref in codes or ref in values or any(p.startswith(ref + '.') for p in pins):
            issues.append(f'AUD-8: obsolete IO LDO part {ref} remains')
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
               5: f'{port}_TX_MCU', 6: f'{port}_UART_OE', 7: '3V3', 8: f'{port}_TX_BUFFER'}, 'C5186957')
        expect(f'R{rbase}', {1: f'{port}_RX_WIRE', 2: f'{port}_RX_BUFFER'}, 'C21190', '1k 1%')
        expect(f'R{rbase + 1}', {1: f'{port}_TX_BUFFER', 2: f'{port}_TX_WIRE'}, 'C21190', '1k 1%')
        expect(f'R{rbase + 2}', {1: f'{port}_UART_OE', 2: 'GND'}, 'C25804', '10k 1%')
        # AUD-8: retain one local 100nF bypass at each TXU supply pin (TI TXU0202 section 12.1).
        for cap in (rbase, rbase + 3):
            expect(f'C{cap}', {1: '3V3', 2: 'GND'}, 'C14663', '100nF 50V X7R 10%')
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
                (f'R{rb + 2}', f'{port}_FAULT_N', '3V3', '10k 1%', 'C25744')):  # AUD-7, 0402 digital pull-up.
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



def signal_critical_nets(board):
    """Every net of `board` that route_check's r10 profile classes signal-critical (pyro, crystal, usb, spi, uart,
    portctl): the ONE definition K-reference and K-region share with route_check (R4-RTE-01)."""
    import route_check as rc
    previous = rc.PROFILE
    rc.set_profile('r10')
    try:
        return {n for n in (str(k) for k in board.GetNetsByName().keys()) if n and rc.net_class(n) in rc.SIGNAL_CRITICAL}
    finally:
        rc.set_profile(previous)


def return_path_nets(board):
    """AUD-2: omit only the shared named slow nets; critical hygiene classification stays intact."""
    import critical_reference as cr
    return {n for n in signal_critical_nets(board) if not cr.r10_slow_return_net(n)}


def own_antipads(board):
    """{net: [(x, y, r)]} mm: the antipads a net's own plated copper opens in the planes (R9 D-S8-17 for vias): its vias
    at REF_OWN_R, and its plated through-hole pads (the terminal barrels) at half the pad size + REF_PAD_ANTIPAD (the
    plane clearance of a barrel; Inference, the measured terminal voids reach 1.3 mm from the barrel centre)."""
    import pcbnew
    out = {}
    for v in board.GetTracks():
        if v.GetClass() == 'PCB_VIA':
            out.setdefault(v.GetNetname(), []).append((pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y),
                                                       REF_OWN_R))
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname():
                size = max(pcbnew.ToMM(p.GetSize().x), pcbnew.ToMM(p.GetSize().y))
                out.setdefault(p.GetNetname(), []).append((pcbnew.ToMM(p.GetPosition().x),
                                                           pcbnew.ToMM(p.GetPosition().y), size / 2 + REF_PAD_ANTIPAD))
    return out


def in_own_antipad(own, net, x, y):
    return any(math.dist((x, y), q[:2]) <= q[2] for q in own.get(net, ()))


REGION_STEP = 0.02             # mm: K-region sample spacing along a track (centre line and both pushed edges)
REGION_MARGIN = 0.1            # mm: the edges are sampled this far outside the copper edge (R5-RTE-02)
REGION_PAD_STEP = 0.05         # mm: K-region sample grid over an SMD pad grown by REGION_MARGIN
REGION_HOLE_REACH = 0.30       # mm: a via's fill hole reaches no further than its pad radius + this (measured hole radius
                               # 0.401 = pad 0.25 + 0.15 on the R10 board; R6-RTE-02)
VOID_RIM_SIDES = 64            # the pad-void disc is this many sided polygon


def fill_hole_table(zones, vias):
    """[(x0, y0, x1, y1, chain, {nets})] mm: every hole (inner outline) of the In2 fills that is a via clearance hole:
    its area contains a via centre and every vertex of its outline lies within (pad radius + REGION_HOLE_REACH) of a via
    centre, so the hole is covered by via discs (one via: its box is no larger than 2 x (pad radius + reach); vias with
    merged antipads: a hole of the union). `nets` are the nets of the vias inside it. A slot, a plane pull-back or any
    other no-copper shape is no via hole (R6-RTE-02 / R6-GATE-01)."""
    import pcbnew
    out = []
    for ps in zones.values():
        for o in range(ps.OutlineCount()):
            for h in range(ps.HoleCount(o)):
                chain = ps.Hole(o, h)
                bb = chain.BBox()
                x0, y0 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
                x1, y1 = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
                near = [v for v in vias if x0 - 1.5 <= v[0] <= x1 + 1.5 and y0 - 1.5 <= v[1] <= y1 + 1.5]
                nets = {n for vx, vy, n, _ in near if x0 <= vx <= x1 and y0 <= vy <= y1
                        and chain.PointInside(pcbnew.VECTOR2I(pcbnew.FromMM(vx), pcbnew.FromMM(vy)))}
                covered = all(any(math.hypot(pcbnew.ToMM(chain.CPoint(k).x) - vx, pcbnew.ToMM(chain.CPoint(k).y) - vy)
                                  <= r + REGION_HOLE_REACH for vx, vy, _, r in near) for k in range(chain.PointCount()))
                if nets and covered and not hole_uncovered_area(chain, near) > HOLE_SLIVER_MM2:
                    out.append((x0, y0, x1, y1, chain, nets))
    return out


HOLE_SLIVER_MM2 = 2e-3         # mm2: what the via discs may leave of a via hole (R7-GATE-02); measured 4.95e-4 at the
                               # merged SPI1 hole (a 0.04 mm triangle between three discs), a slot is mm2 (10 mm: 8)


def hole_uncovered_area(chain, vias):
    """mm2 of the hole polygon `chain` not covered by the union of the discs (via pad radius + REGION_HOLE_REACH) of
    `vias`: a hole whose vertices are near vias but whose body is a slot between them is no via hole (R7-GATE-02)."""
    import pcbnew
    hole = pcbnew.SHAPE_POLY_SET()
    hole.AddOutline(chain)
    for vx, vy, _, r in vias:
        disc = pcbnew.SHAPE_POLY_SET()
        disc.NewOutline()
        for k in range(VOID_RIM_SIDES):
            a = 2 * math.pi * k / VOID_RIM_SIDES
            rr = (r + REGION_HOLE_REACH) / math.cos(math.pi / VOID_RIM_SIDES)       # circumscribed: never smaller
            disc.Append(pcbnew.FromMM(vx + rr * math.cos(a)), pcbnew.FromMM(vy + rr * math.sin(a)))
        hole.BooleanSubtract(disc)
    return hole.Area() / 1e12


def in_via_hole(table, net, x, y):
    import pcbnew
    pt = None
    for x0, y0, x1, y1, chain, nets in table:
        if x0 <= x <= x1 and y0 <= y <= y1 and any(n != net for n in nets):
            pt = pt or pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
            if chain.PointInside(pt):
                return True
    return False


def pad_void_regions(zones, cx, cy, radius):
    """[(free SHAPE_POLY_SET, outline index, escapes)]: the In2 no-copper regions inside the disc (cx, cy, radius) by
    polygon subtraction (no grid, so a 0.02 mm exit slot cannot slip through; R6-GATE-05); `escapes` when the region
    reaches the disc's rim (a vertex on the rim polygon)."""
    import pcbnew
    disc = pcbnew.SHAPE_POLY_SET()
    disc.NewOutline()
    for k in range(VOID_RIM_SIDES):
        a = 2 * math.pi * k / VOID_RIM_SIDES
        disc.Append(pcbnew.FromMM(cx + radius * math.cos(a)), pcbnew.FromMM(cy + radius * math.sin(a)))
    for ps in zones.values():
        disc.BooleanSubtract(ps)
    rim = radius * math.cos(math.pi / VOID_RIM_SIDES) - 0.002
    out = []
    for i in range(disc.OutlineCount()):
        chain = disc.COutline(i)
        escapes = any(math.hypot(pcbnew.ToMM(chain.CPoint(k).x) - cx, pcbnew.ToMM(chain.CPoint(k).y) - cy) >= rim
                      for k in range(chain.PointCount()))
        out.append((disc, i, escapes))
    return out


class OwnPadVoids:
    """The plated through-hole pads' own clearance voids in the In2 planes: a sample is exempt only inside a no-copper
    component that lies wholly in the disc (pad half-size + zone clearance + 0.05 mm) around the pad centre."""

    def __init__(self, board, zones):
        import pcbnew
        self.zones, self.pads, self.cache = zones, {}, {}
        clearance = max((pcbnew.ToMM(z.GetOwnClearance(pcbnew.In2_Cu)) for z in board.Zones()
                         if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In2_Cu)), default=0.0)
        for f in board.GetFootprints():
            for p in f.Pads():
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname():
                    half = max(pcbnew.ToMM(p.GetSize().x), pcbnew.ToMM(p.GetSize().y)) / 2
                    self.pads.setdefault(p.GetNetname(), []).append(
                        (len(self.cache), pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y),
                         half + clearance + 0.05))
                    self.cache[len(self.cache)] = None

    def exempt(self, net, x, y):
        import pcbnew
        pt = pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        for key, cx, cy, radius in self.pads.get(net, ()):
            if math.dist((x, y), (cx, cy)) > radius:
                continue
            if self.cache[key] is None:
                self.cache[key] = pad_void_regions(self.zones, cx, cy, radius)
            regions = self.cache[key]
            hit = [esc for ps, i, esc in regions if ps.Contains(pt, i, 1000, True)]
            if hit and not any(hit):
                return True
        return False


def region_issues(board):
    """K-region (R4-RTE-02, R5-RTE-01 / -02 / -06): every B.Cu track (straight or arc) of a signal-critical net is
    sampled every REGION_STEP on its centre line and on both edges pushed REGION_MARGIN outward, and every B.Cu SMD pad
    of such a net on a REGION_PAD_STEP grid over the pad grown by REGION_MARGIN; each sample lies over exactly one In2
    plane net, outside REF_OWN_R of the net's own vias and outside the net's own through-hole pads' clearance voids (a
    no-copper region wholly inside the pad's disc, OwnPadVoids); a no-copper sample inside a hole of the fill that holds
    another net's via (hole box <= 2 x (via pad radius + REGION_HOLE_REACH)) is a clearance hole, not a boundary. Each connected B.Cu chain (tracks joined end to end or
    through a pad of the net) sees exactly one In2 plane net in total. Returns (issues, evidence)."""
    import critical_reference as cr
    import pcbnew
    nets = return_path_nets(board)
    zones = {}
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In2_Cu) and z.HasFilledPolysForLayer(pcbnew.In2_Cu):
            zones.setdefault(z.GetNetname(), pcbnew.SHAPE_POLY_SET()).BooleanAdd(z.GetFilledPolysList(pcbnew.In2_Cu))
    vias = {}
    for v in board.GetTracks():
        if v.GetClass() == 'PCB_VIA':
            vias.setdefault(v.GetNetname(), []).append((pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y)))
    voids = OwnPadVoids(board, zones)
    # a sample over no copper inside a hole of the In2 fill that holds another net's via is that via's clearance hole,
    # not a plane boundary (geometric: the hole's own outline and size, R6-RTE-02); K-reference holds the run's own
    # reference there (R5 fix pass, D-R5-03)
    via_holes = fill_hole_table(zones, [(pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y), v.GetNetname(),
                                         pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu)) / 2)
                                        for v in board.GetTracks() if v.GetClass() == 'PCB_VIA'])
    items, count = [], 0       # (net, label, endpoint keys, planes seen, gaps)

    def scan(net, pts):
        nonlocal count
        seen, gaps = set(), []
        for x, y in pts:
            if any(math.dist((x, y), q) <= REF_OWN_R for q in vias.get(net, ())):
                continue
            on = [n for n, ps in zones.items() if cr.inside(ps, x, y)]
            if not on and voids.exempt(net, x, y):
                continue
            if not on and in_via_hole(via_holes, net, x, y):
                continue
            count += 1
            seen.update(on)
            if not on:
                gaps.append((round(x, 2), round(y, 2)))
        return seen, gaps

    def key(pt):
        return (round(pcbnew.ToMM(pt.x), 3), round(pcbnew.ToMM(pt.y), 3))
    for t in board.GetTracks():
        if t.GetClass() not in ('PCB_TRACK', 'PCB_ARC') or t.GetLayer() != pcbnew.B_Cu or t.GetNetname() not in nets:
            continue
        net = t.GetNetname()
        seen, gaps = scan(net, [(x, y) for _, _, x, y in cr.track_samples(t, 0.0, REGION_STEP, REGION_MARGIN)])
        a, c = key(t.GetStart()), key(t.GetEnd())
        items.append((net, f'B.Cu run ({a[0]:.2f}, {a[1]:.2f}) - ({c[0]:.2f}, {c[1]:.2f})', {a, c}, seen, gaps))
    pads = []
    for f in board.GetFootprints():
        for p in f.Pads():
            net = p.GetNetname()
            if net not in nets or not p.IsOnLayer(pcbnew.B_Cu) or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            bb = p.GetBoundingBox()
            x0, x1 = pcbnew.ToMM(bb.GetLeft()) - REGION_MARGIN, pcbnew.ToMM(bb.GetRight()) + REGION_MARGIN
            y0, y1 = pcbnew.ToMM(bb.GetTop()) - REGION_MARGIN, pcbnew.ToMM(bb.GetBottom()) + REGION_MARGIN
            shape = p.GetEffectiveShape(pcbnew.B_Cu)
            nx, ny = int((x1 - x0) / REGION_PAD_STEP) + 1, int((y1 - y0) / REGION_PAD_STEP) + 1
            pts = []
            for i in range(nx + 1):
                for j in range(ny + 1):
                    x, y = x0 + i * (x1 - x0) / nx, y0 + j * (y1 - y0) / ny
                    if shape.Collide(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)), pcbnew.FromMM(REGION_MARGIN)):
                        pts.append((x, y))
            seen, gaps = scan(net, pts)
            pads.append(p)
            items.append((net, f'pad {f.GetReference()}.{p.GetNumber()}', {('pad', len(pads) - 1)}, seen, gaps))
    issues = []
    for net, label, _, seen, gaps in items:
        if len(seen) > 1 or gaps:
            issues.append(f'{net} {label} lies over In2 planes {sorted(seen) or "none"}'
                          + (f' and {len(gaps)} samples over no In2 copper, e.g. {gaps[0]}' if gaps else '')
                          + ' (one In2 plane region per signal-critical run)')
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    bynet = {}
    for i, it in enumerate(items):
        bynet.setdefault(it[0], []).append(i)
    for idx in bynet.values():
        for a in idx:
            for c in idx:
                if a >= c:
                    continue
                ea, ec = items[a][2], items[c][2]
                joined = bool(ea & ec)
                for tr, pd in ((a, c), (c, a)):               # a track whose end lies on a pad of the net
                    pad_key = next((k for k in items[pd][2] if k[0] == 'pad'), None)
                    if not joined and pad_key is not None and not any(k[0] == 'pad' for k in items[tr][2]):
                        pad = pads[pad_key[1]]
                        joined = any(pad.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
                                     for x, y in items[tr][2])
                if joined:
                    parent[find(a)] = find(c)
    groups = {}
    for i in range(len(items)):
        groups.setdefault(find(i), []).append(i)
    for g in groups.values():
        planes = set().union(*(items[i][3] for i in g))
        if len(planes) > 1:
            issues.append(f'{items[g[0]][0]} connected B.Cu chain ({", ".join(items[i][1] for i in g[:6])}) lies over '
                          f'In2 planes {sorted(planes)} (one In2 plane region per connected chain)')
    return issues, {'items': len(items), 'samples': count, 'nets': sorted(nets)}


def references(board):
    """K-reference (D-R2-10): critical_reference's samples with B.Cu over any In2 rail plane; an unreferenced sample
    passes inside its own net's via antipad (REF_OWN_R) or as a recorded REF_STRAY."""
    import critical_reference as cr
    import pcbnew
    refs = cr.references(True)
    refs[pcbnew.B_Cu] = (pcbnew.In2_Cu, REF_PLANES_B)
    nets = {n for n in set(cr.R6_NETS + cr.EXTENDED + cr.R10_PORT_NETS) | signal_critical_nets(board)
            if not cr.r10_slow_return_net(n)}  # AUD-2; fast interfaces retain every reference sample.
    samples = cr.samples(board, nets, refs)
    fill = cr.fills(board, refs)
    empty = pcbnew.SHAPE_POLY_SET()
    missing = [s for s in samples if not cr.inside(fill.get(s[1], empty), s[2], s[3])]
    own = own_antipads(board)
    stray = [s for s in missing if not in_own_antipad(own, s[0], s[2], s[3])]
    used, loose = set(), []
    for s in stray:
        name = pcbnew.LayerName(s[1])
        hit = [k for k, e in enumerate(REF_STRAY) if e[:2] == (s[0], name) and math.dist(e[2:4], s[2:4]) <= 0.01]
        if hit:
            used.add(hit[0])
        else:
            loose.append((s[0], name, s[2], s[3]))
    issues = []
    if not samples:
        issues.append('no critical routed-reference samples (unrouted board)')
    if loose:
        issues.append(f'{len(loose)} critical signal samples lack adjacent reference copper outside their own via '
                      f'antipads, e.g. {loose[:3]}')
    issues += [f'stale REF_STRAY entry {e[:4]}' for k, e in enumerate(REF_STRAY) if k not in used and samples
               and len(samples) > 1000]
    return issues, {'samples': len(samples), 'unreferenced': len(missing), 'inside_own_antipad': len(missing) -
                    len(stray), 'recorded_stray': len(used), 'loose': len(loose),
                    'b_cu_planes': list(REF_PLANES_B), 'by_net_layer': cr._group([s for s in stray])}



def contract(text):
    """R10 netlist contract (K-contract): connectors, U1 pin map, port power and UART isolation, camera UART, pinned
    parts, removed R9 parts and nets. Population (S-4) and check_actuators (K-actuators) run as their own rules."""
    issues = []
    codes = {}
    pins, values = actuators.pad_nets(text, codes)
    if values.get('C92') != '4.7uF 16V X5R 10%':
        issues.append('AUD-1: C92 must be qualified 4.7uF 16V X5R 10% (C19666)')
    if values.get('C120') != '1uF 25V X7R 10%':
        issues.append('AUD-3: C120 must be qualified 1uF 25V X7R 10% (C29936)')
    issues += uart_ports(pins, values, codes) + port_power(pins, values, codes) + camera_uart(pins, values, codes)
    fps = {properties(f)['Reference'].items[2].atom: f for f in read(text).children('footprint')}
    refs = [properties(f)['Reference'].items[2].atom for f in read(text).children('footprint')]
    if len(refs) != len(set(refs)):
        issues.append('duplicate footprint reference')
    rf = re.compile(r'(U3[01]|J3[01]|Q3\d|[RCDLQ]3\d\d|D3[01]|L30|FB3[01]|TP30)')
    for ref in sorted((REMOVED & fps.keys()) | {r for r in fps if rf.fullmatch(r)}):
        issues.append(f'{ref}: removed R10 component remains')
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
    for ref in ('J410', 'J420', 'U410', 'U420', 'U411', 'U421'):
        nets = [n for p, n in pins.items() if p.startswith(ref + '.') and n and forbidden.match(n)]
        if nets:
            issues.append(f'{ref}: external port touches safety nets {nets}')
    for net in set(pins.values()) - {None}:
        if net == 'PYRO1_BUS':
            issues.append('PYRO1_BUS: obsolete separate bus; R10 uses RAW_ACT behind Q120/Q121')
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
                 'J400', 'R80', 'R165', 'R122', 'R123', 'J121', 'D120', 'R129', 'R130', 'R131', 'R132', 'R133', 'R173', 'R175', 'R178', 'R180',
                 'R168', 'R170', 'R172', 'R124', 'R177', 'C122', 'C127', 'C128', 'C129'}
REQUIRED_FITTED |= SAFETY_FITTED
RAW = 'RAW_ACT'
ARMED = (RAW, 'PYRO1_IGN', 'PYRO1_OUT')
RAILS = frozenset({'GND', '3V3', '3V3A'})        # net-path searches stop here (a divider foot is not a feed)
MAX_PART_NETS = 4                               # parts with more distinct nets (ICs, U1) do not pass a path
ARMED_SIDE = re.compile(r'^(PYRO1_|ARM1_)')
RAW_SIDE = re.compile(r'^RAW_ACT(_SENSE\w*)?$')
LOAD_SWITCH = {'Q120': ('BAT_IN', 'ACT_FET_S'), 'Q121': ('RAW_ACT', 'ACT_FET_S')}   # (drain, source); gate ACT_GATE
PFET_ROLES = {'S': ('1', '2', '3'), 'G': ('4',), 'D': ('5', '6', '7', '8', '9')}     # AUD-3 AONR21357 (AOS PO-00047).
NFET_ROLES = {'S': ('1', '2', '3'), 'G': ('4',), 'D': ('5',)}                       # AON7524 DFN 3x3 (AOS)
PORT_NET = re.compile(r'^(GPS_|RADIO_|CAM_|PORT_)')
SAFE_NET = re.compile(r'^(PYRO1_|ARM1_|ACT_|RAW_ACT)')
MCU_REF = 'U1'
DEFAULT_CLEARANCE = 0.15                       # mm, used only when the board carries no default net class
J122_ROWS = {'signal': ('1', '4', '7', '10'), 'plus': ('2', '5', '8', '11'), 'ground': ('3', '6', '9', '12')}
BOARD_WIDTH, BOARD_MAX = 46.0, 120.0            # P1
F1_MIN = 209.0                                  # Hz, R9's plate floor, kept (r10_mated, pinned, D 5)
WIRE_ENTRY = {'J1': '-x', 'J121': '-x'}           # r10_plan section 2 item 2; J1 the same west face (R3-MEC-02)
WIRE_ROOM = 6.25                                # mm, R8 / R9 P-11
BOT_THT, BOT_M3 = 1.5, 3.5                      # mm, R9 M-6 without its pyro-via term (a pyro spacing rule)
IMU_LEVER_R10 = -6.0                           # mm: U4 centre x - 23 (roll axis), M3_R10 "IMU axis map" (R4-MEC-05)
IMU_PAD1_R10 = (1.21, -0.75)                   # mm: pad 1 board position from the U4 centre at rotation 180 on the bottom
IMU_ROTATION_R10 = 180.0                        # R9 D-S7-06 kept: U4 bottom, rotation 180
IMU_MAPS = {0.0: 'M3_R5 axis map: +X_imu = +x_board, +Y_imu = +y_board; roll = +gyro_Y',
            180.0: 'R9 D-S7-06 axis map: +X_imu = -x_board, +Y_imu = -y_board; roll = -gyro_Y'}
WORD_LEGENDS_R10 = {'IGN': 'J121', 'BAT': 'J1', 'CAM': 'J9', 'SWD': 'J2', 'SERVO': 'J122',
                    'GPS': 'J410', 'RADIO': 'J420'}
TERMINAL_PINS_R10 = (('J121', (('1', 'E1-'), ('2', 'E1+'))),
                     ('J1', (('1', 'BAT+'), ('2', 'GND'))),
                     ('J400', (('1', 'SW'), ('2', 'SW'))))
EPS = 1e-3
# K-reference (R10_DECISIONS D-R2-10): R9's D-S8-17 method on R10's planes.
REF_PLANES_B = ('GND', '3V3', '3V3A', 'PORT_5V3', 'PORT_4V8', 'RAW_PROTECTED')
REF_PAD_ANTIPAD = 0.6          # mm beyond half a plated pad's size: the plane void around a terminal barrel (Inference)
REF_OWN_R = 0.45               # mm: a sample this close to a same-net via centre lies in that via's own antipad
REF_STRAY = [   # (net, layer, x, y, reason): unreferenced samples outside their own via antipads; matched within 0.01 mm
    ('USB_DM', 'F.Cu', 8.0793, 29.5793, "USB_DM's 45-degree run's copper edge grazes CC1's via antipad (7.85, 29.25), "
                                         "r 0.40 mm: 0.401 mm from its centre (R9's REF_STRAY, translated; one edge sample)"),
    ('SPI1_MISO', 'B.Cu', 17.7904, 43.8818, "R9's translated IMU fan-out: the edge of SPI1_MISO's 45-degree stub passes "
                                             "SPI1_MOSI's via (17.55, 44.25) antipad at 0.440 mm (edge samples)"),
    ('SPI1_MISO', 'B.Cu', 17.7975, 43.8889, 'as above'),
    ('SPI1_MISO', 'F.Cu', 17.3046, 43.8869, "as above, F.Cu side: SPI1_MOSI's via (17.55, 44.25) at 0.438 mm, its In1 "
                                             "antipad"),
    ('SPI1_SCK', 'B.Cu', 17.1, 43.4, "R9's translated IMU fan-out: SPI1_SCK's B.Cu edge passes SPI1_MISO's via "
                                     "(17.55, 43.5) antipad at 0.461 mm"),
    ('SPI1_SCK', 'B.Cu', 17.1, 43.42, 'as above'),
]
# K-rules (R4-GATE-01): R10 has no pyro-specific rule, so the board default clearance is the only pyro spacing: the
# rules file is pinned (generated by m3_design/r10_sch.py; a reviewed change re-pins it) and the project's design rules
# may not be loosened. Floors are the values set on the accepted R10 project.
DRU_SHA256 = '5acf6db7017276f7d4ad59d737584adaeaf686fedaba8ad38b5e06063fadf1e3'
PRO_FLOORS = {'min_clearance': 0.15, 'min_track_width': 0.15, 'min_via_diameter': 0.5, 'min_via_annular_width': 0.1,
              'min_through_hole_diameter': 0.3, 'min_hole_clearance': 0.2, 'min_hole_to_hole': 0.25,
              'min_copper_edge_clearance': 0.5, 'min_microvia_diameter': 0.2, 'min_microvia_drill': 0.1}
NETCLASS_CLEARANCE_FLOOR = 0.15


def k_rules(ctx):
    """m3.kicad_dru pinned by SHA-256 and the .kicad_pro design rules not loosened (pyro safety rests on them)."""
    issues, ev = [], {}
    dru = ctx.dru
    if ctx.board_path and Path(ctx.board_path).with_suffix('.kicad_dru').is_file():
        dru = Path(ctx.board_path).with_suffix('.kicad_dru').read_bytes().decode('utf-8')
    if dru is None:
        issues.append('K-rules: m3.kicad_dru not readable next to the board')
    else:
        actual = hashlib.sha256(dru.encode('utf-8')).hexdigest()
        ev['dru_sha256'] = actual
        ev['dru_sha256_expected'] = DRU_SHA256
        if actual != DRU_SHA256:
            issues.append(f'K-rules: m3.kicad_dru SHA-256 {actual} is not the pinned {DRU_SHA256} (a reviewed change '
                          're-pins DRU_SHA256 in tools/check_r10.py)')
    bp = ctx.board_path
    pro = Path(bp).with_suffix('.kicad_pro') if bp else None
    if pro is None or not pro.is_file():
        issues.append('K-rules: the .kicad_pro next to the board is not readable')
        return issues, ev
    project = json.loads(pro.read_text())
    design = project.get('board', {}).get('design_settings', {})
    rules = design.get('rules', {})
    ev['pro_rules'] = {k: rules.get(k) for k in PRO_FLOORS}
    for key, floor in PRO_FLOORS.items():
        value = rules.get(key)
        if not isinstance(value, (int, float)) or value < floor - 1e-9:
            issues.append(f'K-rules: .kicad_pro design rule {key} = {value}, floor {floor} mm')
    classes = project.get('net_settings', {}).get('classes', [])
    ev['netclass_clearance'] = {c.get('name'): c.get('clearance') for c in classes}
    if not any(c.get('name') == 'Default' for c in classes):
        issues.append('K-rules: .kicad_pro has no Default net class')
    for c in classes:
        value = c.get('clearance')
        if not isinstance(value, (int, float)) or value < NETCLASS_CLEARANCE_FLOOR - 1e-9:
            issues.append(f'K-rules: net class {c.get("name")} clearance {value}, floor {NETCLASS_CLEARANCE_FLOOR} mm')
    ignored = sorted(k for k, v in design.get('rule_severities', {}).items() if v == 'ignore')
    ev['ignored_severities'] = ignored
    if ignored:
        issues.append(f'K-rules: DRC rule severities set to ignore: {ignored}')
    if design.get('drc_exclusions'):
        issues.append(f'K-rules: {len(design["drc_exclusions"])} DRC exclusions in the project')
    return issues, ev


# OQ-1 accepted by the owner 2026-10-28; physical fit remains outstanding.
WIRE_ROOM_R10 = 4.95

# S-8 barrels (R3-SAF-01); the former PYRO1_BUS is now RAW_ACT.
BARREL_NETS = ('RAW_ACT', 'PYRO1_IGN', 'PYRO1_OUT', 'PYRO1_GATE')
BARREL_GAP = 1.0                # mm, plated barrel wall to foreign In1 / In2 copper
# S-9 (R3-GATE-07): the fire-loop current path of each net, between its power terminals (pad sets; a pad number set
# per reference). AUD-6 reduces only the fire-only RAW_ACT / IGN / OUT paths to 0.5 mm; BAT_IN and ACT_FET_S
# retain D-R2-02's 1.0 mm floor. The named source bridge below remains individually measured.
FIRE_MIN_W = 1.0                # mm
FIRE_ONLY = frozenset({'RAW_ACT', 'PYRO1_IGN', 'PYRO1_OUT'})  # AUD-6, 4.2 A / 20 ms; other paths unchanged.
FIRE_TERMINALS = {
    'PYRO1_IGN': ({'R134': ('1',)}, {'J121': ('2',)}),
    'PYRO1_OUT': ({'J121': ('1',)}, {'Q124': ('5',)}),
    'RAW_ACT': ({'Q121': ('5', '6', '7', '8', '9')}, {'R134': ('2',)}),
    'ACT_FET_S': ({'Q120': ('1', '2', '3')}, {'Q121': ('1', '2', '3')}),
    'BAT_IN': ({'J1': ('1',)}, {'Q120': ('5', '6', '7', '8', '9')}),
}
# Named narrow fire-path copper (net, layer, width mm, length mm, (x0, y0, x1, y1) ends sorted):
# the ACT_FET_S bridge between the facing sources of Q120 / Q121 (AUD-3 AONR21357 source pins 1-3 at 0.65 mm pitch, 0.35 mm
# wide; a 0.4 mm leg from each pin to a 0.4 mm bar). Adiabatic rise of a 0.4 mm x 35 um outer track carrying the whole
# 4.2 A pulse for 20 ms (Inference, upper bound: the six legs share it): J = 4.2 A / 1.4e-8 m^2 = 3.0e8 A/m^2;
# dT = J^2 rho t / (rho_d c) = 9.0e16 x 1.72e-8 x 0.02 / (8960 x 385) = 9.0 K; at GAP-5's 36 ms fault ceiling,
# 16.2 K (Inference, adiabatic). Matched within 0.01 mm; a narrower, longer or moved segment fails.
FIRE_NARROW = [
    # AUD-3: AONR21357's 0.65mm source pitch; same measured 0.4mm pulse bridge policy.
    ('ACT_FET_S', 'B.Cu', 0.4, 1.95, (12.525, 70.1, 14.475, 70.1), 'AONR21357 source bridge bar'),
    ('ACT_FET_S', 'B.Cu', 0.4, 1.1, (12.525, 70.1, 12.525, 71.2), 'Q120.1 source leg'),
    ('ACT_FET_S', 'B.Cu', 0.4, 1.1, (13.175, 70.1, 13.175, 71.2), 'Q120.2 source leg'),
    ('ACT_FET_S', 'B.Cu', 0.4, 1.1, (13.825, 70.1, 13.825, 71.2), 'Q120.3 source leg'),
    ('ACT_FET_S', 'B.Cu', 0.4, 1.1, (14.475, 69., 14.475, 70.1), 'Q121.1 source leg'),
    ('ACT_FET_S', 'B.Cu', 0.4, 1.1, (13.825, 69., 13.825, 70.1), 'Q121.2 source leg'),
    ('ACT_FET_S', 'B.Cu', 0.4, 1.1, (13.175, 69., 13.175, 70.1), 'Q121.3 source leg'),
]

# K-loader (R3-MCU-01). AN2606 Rev 64 (September 2024) Table 119 "STM32H74xxx/75xxx configuration in system memory boot
# mode", pp. 277-280 (https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-
# mode-stmicroelectronics.pdf; R8 cited the same table as Rev 70 Table 135, pp. 320-323): port -> (interface pin, how
# the loader uses it). 'out' = driven push-pull, 'od' = open-drain I/O (can drive low), 'in' = input ('in-pu' with the
# loader's pull-up). PF0 / PF1 (I2C2), PI0-PI3 (SPI2) and PH13 / PH14 (FDCAN1) are not on the LQFP100 package.
LOADER_H74X = {
    'PA9': ('USART1_TX', 'out'), 'PA10': ('USART1_RX', 'in-pu'), 'PB14': ('USART1_TX (PB14/PB15 map)', 'out'),
    'PB15': ('USART1_RX (PB14/PB15 map)', 'in-pu'), 'PA2': ('USART2_TX', 'out'), 'PA3': ('USART2_RX', 'in-pu'),
    'PB10': ('USART3_TX', 'out'), 'PB11': ('USART3_RX', 'in-pu'), 'PB6': ('I2C1_SCL', 'od'), 'PB9': ('I2C1_SDA', 'od'),
    'PF1': ('I2C2_SCL', 'od'), 'PF0': ('I2C2_SDA', 'od'), 'PA8': ('I2C3_SCL', 'od'), 'PC9': ('I2C3_SDA', 'od'),
    'PA7': ('SPI1_MOSI', 'in'), 'PA6': ('SPI1_MISO', 'out'), 'PA5': ('SPI1_SCK', 'in'), 'PA4': ('SPI1_NSS', 'in'),
    'PI3': ('SPI2_MOSI', 'in'), 'PI2': ('SPI2_MISO', 'out'), 'PI1': ('SPI2_SCK', 'in'), 'PI0': ('SPI2_NSS', 'in'),
    'PC12': ('SPI3_MOSI', 'in'), 'PC11': ('SPI3_MISO', 'out'), 'PC10': ('SPI3_SCK', 'in'), 'PA15': ('SPI3_NSS', 'in'),
    'PE14': ('SPI4_MOSI', 'in'), 'PE13': ('SPI4_MISO', 'out'), 'PE12': ('SPI4_SCK', 'in'), 'PE11': ('SPI4_NSS', 'in'),
    'PA11': ('USB_DM (DFU)', 'od'), 'PA12': ('USB_DP (DFU)', 'od'),
    'PH14': ('FDCAN1_RX', 'in-pu'), 'PH13': ('FDCAN1_TX', 'out')}
LOADER_DRIVES = ('out', 'od')
# R10 allowances: port -> (net, {pad: part value} of every other pad on the net, reason). A loader pin with a net must be
# here with that net and exactly those members (a new part, a changed value or another net fails); a driven pin's
# reason states why the drive is harmless. Members and values recorded
# from the R10 board of the round that set them (not re-measured in round 4).
LOADER_R10 = {
    'PA2': ('SERVO3_MCU', {'R152.1': '1k 0603', 'R156.1': '10k', 'D121.4': 'SRV05-4'},
            "USART2_TX drives the servo-3 signal through R152 1k: R8's allowance (frozen 3.2; a servo never sends 0x7F); "
            'servo power is off the board (O3), so a byte at most twitches an unpowered or harness-powered servo on the '
            'bench (BOOT0 is a bench-only state)'),
    'PA3': ('SERVO4_MCU', {'R153.1': '1k 0603', 'R157.1': '10k', 'D121.6': 'SRV05-4'},
            'USART2_RX: an input (AN2606 p. 278 lists both no pull and pull-up), never driven; the line is held by '
            'R157 10k and driven only by U1 itself in flight'),
    'PA4': ('LOGIC_SOURCE_ST', {'R91.2': '10k 1%', 'U11.9': 'TPS2121RUXR'},  # AUD-5.
            'SPI1_NSS: a slave input, no pull (p. 279), never driven; U11 ST with its R91 10k pull-up (R8 pin table) '
            'is the only driver'),
    'PA5': ('BAT_FAULT_N', {'R89.2': '10k 1%', 'U9.4': 'TPS259470LRPWR'},  # AUD-5.
            'SPI1_SCK: a slave input, no pull (p. 279), never driven; U9 FLT with its R89 10k pull-up (R8 pin table) is '
            'the only driver'),
    'PA6': ('VLOGIC_SENSE', {'R60.2': '100k', 'R61.1': '10k', 'C60.1': '10nF'},
            'SPI1_MISO is driven push-pull by the loader into the VLOGIC divider node (R60 100k from VLOGIC, R61 10k to '
            'GND, C60 10 nF): the pin current is at most 3.3 V / (10k || 100k) = 0.36 mA (VLOGIC at 0 V, pin high), '
            'far below the 20 mA absolute-maximum I/O current (DS12110 Rev 10 Table 22, p. 105); VLOGIC (<= 8.4 V) '
            'reaches the pin only through R60 (<= 84 uA into a low pin); the reading is wrong only while in the loader'),
    'PE11': ('CAM_PWR_EN', {'R431.1': '100k 1%', 'U402.3': 'TPS2553DBVR'},
             'SPI4_NSS: a slave input, no pull (AN2606 p. 280): R431 100k holds U402 EN low, so the camera supply stays '
             'off in the loader'),
    'PE12': ('CAM_FAULT_N', {'R432.1': '10k 1%', 'U402.4': 'TPS2553DBVR'},  # AUD-7.
             'SPI4_SCK: a slave input, no pull (p. 280), never driven; U402 FAULT is open drain (TPS2553 data sheet) '
             'with the R432 10k pull-up'),
    'PA11': ('USB_DM', None, 'DFU is the loader interface itself (R8 allowance); members not pinned (USB contract)'),
    'PA12': ('USB_DP', None, 'DFU is the loader interface itself (R8 allowance); members not pinned (USB contract)'),
    'PB6': ('QSPI_NCS', {'R10.1': '10k', 'U3.1': 'W25Q128JVSIQ'},
            "I2C1_SCL open drain, no pull: R8's allowance (frozen 3.5): the R10 10k pull-up keeps the flash deselected; "
            'the loader as an I2C slave pulls SCL low only to stretch a clock it receives'),
    'PB9': ('I2C1_SDA', {'R13.1': '4.7k', 'U5.7': 'MS561101BA03'},
            "I2C1_SDA open drain, no pull: R8's allowance (frozen 3.6): the barometer's own I2C data line with its 4.7k "
            'pull-up; the loader answers only address 0b1001110x, which the barometer (0x76 / 0x77) does not use'),
}


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


RAW_SIDE_NET = re.compile(r'^(RAW_ACT(_\w+)?|ACT_\w+)$')


def multinet_bridges(nets_of):
    """R5-SAF-01: parts other than U1 with more than MAX_PART_NETS nets are not walked by net_reach, so each is checked
    directly: pads on a RAW side net (RAW_ACT and its sense / MID / MCU nets, ACT_*) and on an armed-side net (PYRO1_*,
    ARM1_* and their sense / MID / MCU nets) at once bypasses the named pyro / sense chain. Returns [(ref, raw nets, armed
    nets)]."""
    out = []
    for ref, nets in sorted(nets_of.items()):
        if ref == MCU_REF or len(nets) <= MAX_PART_NETS:
            continue
        raw, armed = sorted(n for n in nets if RAW_SIDE_NET.match(n)), sorted(n for n in nets if ARMED_SIDE.match(n))
        if raw and armed:
            out.append((ref, raw, armed))
    return out


def multinet_issues(nets_of, rid):
    return [f'{rid}: {ref} (more than {MAX_PART_NETS} nets) has pads on the RAW-side net(s) {raw} and the armed-side '
            f'net(s) {armed}: it bypasses the named pyro / sense chain' for ref, raw, armed in multinet_bridges(nets_of)]


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

    def add_text(t, label):
        """Copper text (R3-GATE-02): its glyph polygons on its copper layer."""
        if t.GetLayer() not in layers or (hasattr(t, 'IsVisible') and not t.IsVisible()):
            return
        poly = pcbnew.SHAPE_POLY_SET()
        t.TransformShapeToPolygon(poly, t.GetLayer(), 0, pcbnew.FromMM(0.001), pcbnew.ERROR_OUTSIDE)
        if poly.OutlineCount():
            add(t.m_Uuid.AsString(), t.GetLayer(), poly, None, '', label)

    def add_zone(z, label):
        if z.GetIsRuleArea():
            return
        for lay in layers:
            if z.IsOnLayer(lay) and z.HasFilledPolysForLayer(lay):
                fill = z.GetFilledPolysList(lay)
                for i in range(fill.OutlineCount()):
                    add(f'{z.m_Uuid.AsString()}/{lay}/{i}', lay, fill.UnitSet(i), None, z.GetNetname(),
                        f'{label or z.GetNetname() or "(no net)"} fill on {board.GetLayerName(lay)}')
    for f in board.GetFootprints():
        ref = f.GetReference()
        for p in f.Pads():
            for lay in layers:                       # an NPTH pad that carries copper layers counts (R4-GATE-04)
                if p.IsOnLayer(lay):
                    add(p.m_Uuid.AsString(), lay, r8.item_shape(p, lay), p, p.GetNetname(), f'{ref}.{p.GetNumber()}')
        for g in f.GraphicalItems():
            if isinstance(g, pcbnew.PCB_SHAPE) and g.GetLayer() in layers:
                add(g.m_Uuid.AsString(), g.GetLayer(), g.GetEffectiveShape(), None, g.GetNetname(), f'{ref} copper drawing')
            elif not isinstance(g, pcbnew.PCB_SHAPE):
                add_text(g, f'{ref} copper text')
        for fld in f.GetFields():
            add_text(fld, f'{ref} copper field {fld.GetName()}')
        for z in f.Zones():
            add_zone(z, f'{ref} footprint zone')
    for t in board.GetTracks():
        kind = 'via' if t.GetClass() == 'PCB_VIA' else 'track'
        at = t.GetPosition() if kind == 'via' else t.GetStart()
        for lay in layers:
            if t.IsOnLayer(lay):
                add(t.m_Uuid.AsString(), lay, r8.item_shape(t, lay), None, t.GetNetname(),
                    f'{kind} {t.GetNetname() or "(no net)"} ({pcbnew.ToMM(at.x):.2f}, {pcbnew.ToMM(at.y):.2f})')
    for z in board.Zones():
        add_zone(z, None)
    for d in board.GetDrawings():
        if isinstance(d, pcbnew.PCB_SHAPE) and d.GetLayer() in layers:
            add(d.m_Uuid.AsString(), d.GetLayer(), d.GetEffectiveShape(), None, d.GetNetname(), 'board copper drawing')
        elif not isinstance(d, pcbnew.PCB_SHAPE):
            add_text(d, 'board copper text')
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
        ctx._reach = {net: copper_reach(nodes, net) for net in ARMED}
    return ctx._reach


# ======================================================================================================================
# S-rules
# ======================================================================================================================
MCU_SIDE = re.compile(r'(_MCU|^PYRO1_GATE_N)$')           # the MCU side of the 4.7 k sense resistors / the gate resistor
GND_TIES = {      # (part, armed-side net): each intended tie to GND, with its reason (R4-SAF-02 / R4-GATE-03)
    ('R128', 'PYRO1_GATE'): 'gate pull-down (S-3)', ('C126', 'PYRO1_GATE'): 'gate-source capacitor (S-3)',
    ('Q124', 'PYRO1_GATE'): 'pyro FET gate pin; its source is GND', ('Q124', 'PYRO1_OUT'): 'pyro FET drain-source: fires the igniter',
    ('R133', 'ARM1_SENSE'): 'ARM_SENSE divider foot (2 k parallel pair)', ('R180', 'ARM1_SENSE'): 'ARM_SENSE divider foot',
    ('C129', 'ARM1_SENSE'): 'ARM_SENSE filter capacitor',
    ('R130', 'PYRO1_CONT'): 'continuity divider foot', ('R178', 'PYRO1_CONT'): 'continuity divider foot',
    ('C127', 'PYRO1_CONT'): 'continuity filter capacitor',
    ('R125', 'RAW_ACT_SENSE'): 'RAW_ACT sense divider foot', ('R182', 'RAW_ACT_SENSE'): 'RAW_ACT sense divider foot',
    ('C122', 'RAW_ACT_SENSE'): 'RAW_ACT sense filter capacitor',
    ('C128', 'PYRO1_OUT'): 'igniter-output bypass capacitor'}
SUPPLY_TIES = {   # the board's intended ties to a supply, rail or the load-switch source node (not GND)
    ('D120', 'PYRO1_COLD', '3V3'): 'cold pull-up diode D120 / R131: the continuity cold-side bias (H-1)',
    ('Q121', 'RAW_ACT', 'ACT_FET_S'): 'load switch Q121 drain RAW_ACT, source on the back-to-back node (S-2)'}


ARMED_PARTS = {       # part: ({armed nets it may touch}, reason) (R6-GATE-07; the whole list on the R10 board, each named)
    'Q121': ({RAW}, 'load-switch drain feeds the pyro bus'),
    'R177': ({RAW}, 'RAW_ACT sense divider high side'),
    'TP120': ({RAW}, 'existing load-switch output test pad'),
    'J121': ({'PYRO1_OUT', 'PYRO1_IGN'}, 'igniter terminal'),
    'R134': ({'PYRO1_IGN', RAW}, 'igniter pulse resistor, bus to igniter'),
    'Q124': ({'PYRO1_OUT'}, 'pyro FET: drain on the igniter return'),
    'R132': ({RAW}, 'bus-sense divider high side'),
    'R131': ({'PYRO1_OUT'}, 'continuity cold pull-up (H-1)'),
    'R173': ({'PYRO1_OUT'}, 'continuity divider high side'),
    'C128': ({'PYRO1_OUT'}, 'igniter-output bypass capacitor')}


ARMED_NET_PARTS = {   # armed-side / RAW_ACT net: every part on it on the R10 board, each named (R7-SAF-01 / R7-GATE-03)
    'PYRO1_IGN': {'J121', 'R134'},
    'PYRO1_OUT': {'C128', 'J121', 'Q124', 'R131', 'R173'}, 'PYRO1_COLD': {'D120', 'R131'},
    'PYRO1_GATE': {'C126', 'Q124', 'R126', 'R128', 'TP122'},
    'PYRO1_CONT': {'C127', 'R129', 'R130', 'R168', 'R178'}, 'PYRO1_CONT_MID': {'R129', 'R173'},
    'ARM1_SENSE': {'C129', 'R133', 'R170', 'R175', 'R180'}, 'ARM1_SENSE_MID': {'R132', 'R175'},
    'RAW_ACT': {'Q121', 'R132', 'R134', 'R177', 'TP120'},
    'RAW_ACT_SENSE': {'C122', 'R124', 'R125', 'R172', 'R182'}, 'RAW_ACT_SENSE_MID': {'R124', 'R177'}}
GATE_PARTS = {'R126': 'gate series resistor', 'R128': 'gate pull-down', 'C126': 'gate-source capacitor',
              'Q124': 'pyro FET', 'TP122': 'gate test pad'}
MCU_NET_PREFIX = re.compile(r'^(PYRO1_|ARM1_|RAW_ACT)')
MCU_RESISTOR_RANGE = (3.3e3, 6.8e3)       # the "4.7 k class" sense resistor toward the MCU


def net_parts(board):
    out = {}
    for ref, nets in part_nets(board).items():
        for n in nets:
            out.setdefault(n, set()).add(ref)
    return out


def armed_net_issues(board):
    """R7-SAF-01: any part on an armed-side / RAW_ACT net other than the named ones (an extra test pad or part there is
    an unreviewed connection to the firing / sense chain)."""
    issues = []
    for n, refs in sorted(net_parts(board).items()):
        if not armed_net(n):
            continue
        if n not in ARMED_NET_PARTS:
            issues.append(f'S-1: armed-side net {n} is not in ARMED_NET_PARTS (parts {sorted(refs)})')
            continue
        extra = sorted(refs - ARMED_NET_PARTS[n])
        if extra:
            issues.append(f'S-1: {extra} on armed-side net {n} is not a named part of it (ARMED_NET_PARTS in '
                          f'tools/check_r10.py: {sorted(ARMED_NET_PARTS[n])})')
    return issues


def mcu_side_issues(board):
    """R7-SAF-02: every armed-prefixed net named like an MCU-side net (`*_MCU`, PYRO1_GATE_N) has exactly the MCU-side
    topology: U1, one 4.7 k-class resistor (R126 for the gate) toward an armed net, and for the gate node resistors to
    GND; otherwise a mis-named armed net would drop out of armed_net() and of every armed-side check."""
    issues, members, nets_of = [], net_parts(board), part_nets(board)
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    for n, refs in sorted(members.items()):
        if not (MCU_NET_PREFIX.match(n) and MCU_SIDE.search(n)):
            continue
        gate = n == 'PYRO1_GATE_N'
        toward, others = [], []
        for ref in sorted(refs - {'U1'}):
            other = nets_of[ref] - {n}
            two = ref.startswith('R') and len(fps[ref].Pads()) == 2 and len(other) == 1
            if two and armed_net(next(iter(other))):
                toward.append(ref)
            elif two and gate and other == {'GND'}:
                continue
            else:
                others.append(ref)
        ok = 'U1' in refs and len(toward) == 1 and not others
        if ok and gate:
            ok = toward == ['R126']
        elif ok:
            v = parse_value(fps[toward[0]].GetValue(), 'R') or 0
            ok = MCU_RESISTOR_RANGE[0] <= v <= MCU_RESISTOR_RANGE[1]
        if not ok:
            issues.append(f'S-1: MCU-side net {n} is not U1 + one {"R126" if gate else "4.7 k-class resistor"} toward '
                          f'an armed net (parts {sorted(refs)}; toward {toward}, others {others}): a mis-named armed net')
    return issues


def armed_net(n):
    """A net on the armed bus or RAW_ACT side (including the high side of the sense dividers and the gate net)."""
    return bool(ARMED_SIDE.match(n) or RAW_SIDE.match(n)) and not MCU_SIDE.search(n)


def supply_net(n):
    import route_check as rc
    previous = rc.PROFILE
    rc.set_profile('r10')
    try:
        return n in SUPPLY_NETS or bool(SUPPLY_NET.match(n)) or rc.net_class(n) == 'power'
    finally:
        rc.set_profile(previous)


def supply_ties(board):
    """[(part, armed-side net, supply net)] of every part (whatever its net count) that has pads on an
    armed-side / RAW_ACT net and on a supply or rail net, other than the named ties above (R4-SAF-02 / R4-GATE-03)."""
    out = []
    for ref, nets in sorted(part_nets(board).items()):
        for a in sorted(n for n in nets if armed_net(n)):
            for sup in sorted(n for n in nets if n != a and supply_net(n) and not armed_net(n)):
                if (ref, a, sup) in SUPPLY_TIES or (sup == 'GND' and (ref, a) in GND_TIES):
                    continue
                out.append((ref, a, sup))
    return out


def tie_issues(ctx, rid, wanted):
    return [f'{rid}: {ref} has pads on the armed / RAW_ACT side net {a} and on the supply {sup}: not a named tie '
            f'(GND_TIES / SUPPLY_TIES in tools/check_r10.py)' for ref, a, sup in supply_ties(ctx.board) if wanted(a)]


def s1(ctx):
    """Owner single screw switch: RAW_ACT is the bus; only R134 and R132 lead into the firing / bus-sense chain."""
    issues, ev = [], {}
    if 'J124' in ctx.fps:
        issues.append('S-1: obsolete J124 ARM terminal must be removed')
    nets_of = part_nets(ctx.board)
    if any(n.GetNetname() == 'PYRO1_BUS' for n in ctx.board.GetNetsByNetcode().values()):
        issues.append('S-1: obsolete PYRO1_BUS must be merged into RAW_ACT')
    for ref, num, net in (('R134', '2', RAW), ('R134', '1', 'PYRO1_IGN'),
                          ('R132', '1', RAW), ('R132', '2', 'ARM1_SENSE_MID')):
        f = ctx.fps.get(ref)
        pad = f.FindPadByNumber(num) if f else None
        if pad is None or pad.GetNetname() != net:
            issues.append(f'S-1: {ref}.{num} must be on {net} (RAW_ACT bus behind Q120/Q121)')
    came = net_reach(nets_of, RAW, skip={'R134', 'R132'})
    for net in sorted(n for n in came if ARMED_SIDE.match(n)):
        issues.append(f'S-1: RAW_ACT reaches {net} outside R134 / R132: {net_path(came, net)}')
    ev['raw_act_reaches_without_r134_r132'] = sorted(came)
    issues += multinet_issues(nets_of, 'S-1')
    joins = {'R134': {RAW, 'PYRO1_IGN'}, 'R132': {RAW, 'ARM1_SENSE_MID'}}
    for ref, nets in sorted(nets_of.items()):                # any part, whatever its net count
        both = sorted(n for n in nets if ARMED_SIDE.match(n))
        if RAW in nets and both and nets != joins.get(ref):
            issues.append(f'S-1: {ref} has pads on RAW_ACT and pyro / sense net(s) {both}; only R134 / R132 may join them')
    issues += tie_issues(ctx, 'S-1', lambda a: a in ARMED)
    for ref, fp in sorted(ctx.fps.items()):                  # any part, whatever its reference
        on = sorted({p.GetNetname() for p in fp.Pads()} & set(ARMED))
        if not on:
            continue
        if ref not in ARMED_PARTS:
            what = 'test pad' if re.fullmatch(r'(TP|PT|TPA|TEST)\w*', ref) or len(fp.Pads()) == 1 else 'part'
            issues.append(f'S-1: {what} {ref} on armed copper {on} is not a named armed-side part (ARMED_PARTS in '
                          f'tools/check_r10.py)')
        elif not set(on) <= ARMED_PARTS[ref][0]:
            issues.append(f'S-1: {ref} is on armed net(s) {on}; its named armed nets are {sorted(ARMED_PARTS[ref][0])}')
    ev['armed_parts'] = sorted(ARMED_PARTS)
    issues += armed_net_issues(ctx.board) + mcu_side_issues(ctx.board)
    reach = connectivity(ctx)
    ev['raw_act_copper_items'] = reach[RAW][1]
    for label, (net, via) in sorted(reach[RAW][0].items()):
        if ARMED_SIDE.match(net):
            issues.append(f'S-1: RAW_ACT copper reaches {label} ({net}) through {via}: firing / sense chain is bypassed')
    return issues, ev


def s2(ctx):
    """The unified RAW_ACT bus is fed only through the back-to-back Q120 / Q121 load switch."""
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
    came = net_reach(nets_of, RAW, skip={'Q121'})
    bad = sorted(n for n in came if not (RAW_SIDE.match(n) or ARMED_SIDE.match(n)) and n not in RAILS)
    issues += [f'S-2: RAW_ACT is joined to {n} other than through Q121: {net_path(came, n)}' for n in bad]
    ev['pyro_side'] = sorted(came)
    issues += multinet_issues(nets_of, 'S-2')
    issues += tie_issues(ctx, 'S-2', lambda a: a not in ARMED)
    ev['named_ties'] = {'gnd': len(GND_TIES), 'supply': [list(k) for k in SUPPLY_TIES]}
    for start, (foreign, count) in connectivity(ctx).items():
        ev[f'{start}_copper_items'] = count
        for label, (net, via) in sorted(foreign.items()):
            issues.append(f'S-2: {start} copper touches {label} ({net}) through {via}')
    return issues, ev


PULL_RANGE = (1e3, 100e3)       # ohm: the gate pull (R4-SAF-01)
SERIES_RANGE = (100.0, 10e3)    # ohm: the gate series resistor (R5-SAF-02)
MCU_PULL_RANGE = (100.0, 100e3)  # ohm: the MCU-side node's pull to GND (R127 type, R5-SAF-02)
GATE_CAP_MIN = 100e-9           # F: the gate-source capacitor
SUPPLY_NET = re.compile(r'^(PORT_|VBUS|VLOGIC|BAT_|RAW_PROTECTED|V3V3|CAM_5V$|[A-Z0-9_]*_(4V8|5V3|5V)$)')
SUPPLY_NETS = RAILS | {'BAT_IN', 'RAW_PROTECTED', 'VLOGIC', 'ACT_FET_S', 'RAW_ACT', 'PYRO1_BUS', 'PYRO1_OUT', 'PYRO1_IGN'}


def parse_value(text, kind):
    """A part Value field ('220nF 25V X7R', '4.7k', '4k7', '2R2', '2R 1%', '2.2uF') as ohms ('R') or farads ('C'); None
    if not readable. The first token is read whole: plain 'number[unit]' or infix notation ('4k7' = 4.7k, '100k5' =
    100.5k); anything else in it ('1e3', '1,5k') is unreadable (R6-GATE-06)."""
    text = (text or '').strip()
    mults = r'meg|[pnu\u00b5\u03bcmrRkKMG]'            # U+00B5 and U+03BC both read as micro (R7-GATE-01)
    unit = r'(?:\u03a9|\u2126|ohms?|F)?' if kind == 'R' else r'F?'
    m = re.match(rf'(\d+)({mults})(\d+)({unit})(?=\s|$)', text)
    if m:
        number, mult, unit_found = float(f'{m.group(1)}.{m.group(3)}'), m.group(2), m.group(4)
    else:
        m = re.match(rf'(\d+(?:\.\d+)?)\s*({mults})?\s*({unit})(?=\s|$)'
                     rf'(?!\s*(?:meg|[pnu\u00b5\u03bcmrRkKMG\u03a9\u2126F]|ohm))', text)
        if not m:
            return None                      # any other unconsumed tail is unreadable ('4.7 kx': a free-text tail
            # after a number may not start like a multiplier or unit)
        number, mult, unit_found = float(m.group(1)), m.group(2) or '', m.group(3) or ''
    has_f = unit_found == 'F'
    if kind == 'C' and not mult and not has_f:
        return None                  # a unitless capacitor value ('220') is not read as farads (R5-SAF-02)
    if kind == 'C' and mult == 'm' and not has_f:
        return None                  # '100m' is not a capacitor value; '100mF' is
    if kind == 'R':
        factor = {'': 1.0, 'r': 1.0, 'R': 1.0, 'k': 1e3, 'K': 1e3, 'm': 1e-3, 'M': 1e6, 'meg': 1e6, 'G': 1e9}.get(mult)
    else:
        factor = {'': 1.0, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, '\u00b5': 1e-6, '\u03bc': 1e-6, 'm': 1e-3}.get(mult)
    return None if factor is None else number * factor


def gate_network(ctx, fet, roles, label):
    """(issues, evidence): the gate of `fet` has a pull-down resistor (1 k - 100 k) and a capacitor (>= 100 nF) to its
    source and a series resistor to another, non-supply net (its driver; R4-SAF-01)."""
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
    values = {ref: ctx.fps[ref].GetValue() for k in ('pull', 'cap') for ref in found[k]}
    found['pull'] = [r for r in found['pull'] if PULL_RANGE[0] <= (parse_value(values[r], 'R') or 0) <= PULL_RANGE[1]]
    found['cap'] = [r for r in found['cap'] if (parse_value(values[r], 'C') or 0) >= GATE_CAP_MIN]
    found['series'] = [(r, o) for r, o in found['series'] if o not in SUPPLY_NETS and not SUPPLY_NET.match(o)
                       and SERIES_RANGE[0] <= (parse_value(ctx.fps[r].GetValue(), 'R') or 0) <= SERIES_RANGE[1]]
    issues = []
    for key, what in (('pull', f'a resistor from the gate ({gate}) to the source ({source}) of 1 k - 100 k'),
                      ('cap', f'a gate-source capacitor >= 100 nF ({gate} to {source})'),
                      ('series', f'a series resistor of 100 ohm - 10 k from a non-supply net into the gate ({gate})')):
        if not found[key]:
            issues.append(f'S-3: {label} {fet}: no {what}')
    return issues, dict(gate=gate, source=source, values=values, **found)


def s3(ctx):
    issues, ev = [], {}
    found, ev['Q124'] = gate_network(ctx, 'Q124', NFET_ROLES, 'pyro FET')
    issues += found
    u1 = {p.GetNetname() for p in ctx.fps['U1'].Pads()} if 'U1' in ctx.fps else set()
    if ev['Q124'] and not any(other in u1 and other not in SUPPLY_NETS for _, other in ev['Q124']['series']):
        issues.append('S-3: pyro FET Q124: no series resistor from a U1 GPIO pad (a non-rail net) into the gate')
    for node in sorted({o for _, o in ev['Q124'].get('series', ()) if o in u1 and o not in SUPPLY_NETS}):
        pulls = [ref for ref, nn in part_nets(ctx.board).items()          # R127 type: the MCU-side node to GND
                 if nn == {node, 'GND'} and len(ctx.fps[ref].Pads()) == 2 and ref.startswith('R')
                 and MCU_PULL_RANGE[0] <= (parse_value(ctx.fps[ref].GetValue(), 'R') or 0) <= MCU_PULL_RANGE[1]]
        ev['Q124'].setdefault('mcu_pull', {})[node] = pulls
        if not pulls:
            issues.append(f'S-3: pyro FET Q124: no resistor of 100 ohm - 100 k from the MCU-side gate node {node} to GND '
                          f'(it must be defined off while the MCU pin floats)')
        series = {r for r, o in ev['Q124']['series'] if o == node}
        for ref, nn in sorted(part_nets(ctx.board).items()):          # R6-SAF-02: only U1, the series R and R to GND
            if node not in nn or ref == 'U1' or ref in series:
                continue
            fp = ctx.fps[ref]
            if not (ref.startswith('R') and len(fp.Pads()) == 2 and nn == {node, 'GND'}):
                issues.append(f'S-3: {ref} is on the MCU-side gate node {node} (nets {sorted(nn)}): only U1, the series '
                              f'resistor and resistors to GND may touch it (a pull-up would hold the gate on)')
    gate_net = ev['Q124'].get('gate')
    for ref, nn in sorted(part_nets(ctx.board).items()):          # R7-GATE-03: only the named gate parts
        if gate_net in nn and ref not in GATE_PARTS:
            issues.append(f'S-3: {ref} is on the pyro gate net {gate_net}: only {sorted(GATE_PARTS)} may touch it '
                          f'(a part there changes the gate network)')
    for fet in ('Q120', 'Q121'):
        found, ev[fet] = gate_network(ctx, fet, PFET_ROLES, 'load switch')
        issues += found
    pins = {f'{ref}.{p.GetNumber()}': p.GetNetname() for ref, f in ctx.fps.items() for p in f.Pads()}
    want = {'U1.16': 'ACT_EN_MCU', 'R122.1': 'ACT_EN_MCU', 'R122.2': 'ACT_EN', 'R123.1': 'ACT_EN',
            'R123.2': 'GND', 'Q122.1': 'ACT_EN', 'Q122.2': 'GND', 'Q122.3': 'ACT_DRV'}
    for pin, net in want.items():
        if pins.get(pin) != net:
            issues.append(f'S-3: independent load-switch enable {pin} must be {net} (is {pins.get(pin)})')
    for net, refs in (('ACT_EN_MCU', {'U1', 'R122'}), ('ACT_EN', {'R122', 'R123', 'Q122'})):
        if net_parts(ctx.board).get(net) != refs:
            issues.append(f'S-3: independent load-switch enable {net} must touch only {sorted(refs)}')
    for ref, value in (('R122', 1e3), ('R123', 100e3)):
        f = ctx.fps.get(ref)
        if f is None or parse_value(f.GetValue(), 'R') != value:
            issues.append(f'S-3: independent load-switch enable {ref} must be {value:g} ohm')
    ev['load_enable'] = {p: pins.get(p) for p in want}
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


def s5(ctx):
    """The external J400 screw switch is the arming contact, isolated by 470 k on each side."""
    issues, ev = [], {}
    pins = {f'{ref}.{p.GetNumber()}': p.GetNetname() for ref, f in ctx.fps.items() for p in f.Pads()}
    members = net_parts(ctx.board)
    for net, want in (('BAT_SW_SOURCE', {'J400', 'R80'}), ('BAT_SW_RETURN', {'J400', 'R165'})):
        if members.get(net) != want:
            issues.append(f'S-5: {net} must touch only {sorted(want)}')
    expected = {'J400.1': 'BAT_SW_SOURCE', 'J400.2': 'BAT_SW_RETURN', 'R80.1': 'BAT_IN',
                'R80.2': 'BAT_SW_SOURCE', 'R165.1': 'BAT_SW_RETURN', 'R165.2': 'BAT_ENABLE', 'U9.1': 'BAT_ENABLE'}
    for pin, net in expected.items():
        if pins.get(pin) != net:
            issues.append(f'S-5: {pin} must be {net} (is {pins.get(pin)})')
    j400 = ctx.fps.get('J400')
    if j400 is not None and sorted(p.GetNumber() for p in j400.Pads() if p.GetNumber()) != ['1', '2']:
        issues.append('S-5: J400 must have exactly two switch contacts')
    for ref in ('R80', 'R165'):
        f = ctx.fps.get(ref)
        if f is None or parse_value(f.GetValue(), 'R') != 470e3:
            issues.append(f'S-5: {ref} must be 470k (external switch wire protection)')
    nets_of = part_nets(ctx.board)
    came = net_reach(nets_of, 'BAT_SW_SOURCE', skip={'J400'}, stop=RAILS | {'BAT_IN', 'BAT_ENABLE'})
    if 'BAT_SW_RETURN' in came:
        issues.append('S-5: a part bypasses the open J400 switch: ' + net_path(came, 'BAT_SW_RETURN'))
    nodes = copper_nodes(ctx.board)
    for start in ('BAT_SW_SOURCE', 'BAT_SW_RETURN'):
        foreign, count = copper_reach(nodes, start)
        ev[f'{start}_copper_items'] = count
        for label, (net, via) in sorted(foreign.items()):
            issues.append(f'S-5: {start} copper touches {label} ({net}) through {via}: switch contact / resistor bypass')
    return issues, ev


def barrel_shapes(board, nets=BARREL_NETS):
    """[(label, net, SHAPE)] of every plated barrel wall (via drill, plated pad hole) of `nets`."""
    import pcbnew
    out = []
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA' and t.GetNetname() in nets:
            p = t.GetPosition()
            out.append((f'via ({pcbnew.ToMM(p.x):.3f}, {pcbnew.ToMM(p.y):.3f})', t.GetNetname(),
                        pcbnew.SHAPE_CIRCLE(p, t.GetDrillValue() // 2)))
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname() in nets:
                out.append((f'{f.GetReference()}.{p.GetNumber()} hole', p.GetNetname(), p.GetEffectiveHoleShape()))
    return out


def s8(ctx, gap=BARREL_GAP):
    """R3-SAF-01: no In1 / In2 track or zone fill of a net other than GND (or the barrel's own net) within `gap` of a
    pyro barrel wall."""
    import pcbnew
    import check_r8 as r8
    inner = (pcbnew.In1_Cu, pcbnew.In2_Cu)
    barrels = barrel_shapes(ctx.board)
    issues, worst = [], {}
    others = [it for it in ctx.net_items(lambda n: n != 'GND', inner)     # PCB_ARC and PCB_VIA are PCB_TRACKs; + pads (R6-SAF-02)
              if isinstance(it[4], (pcbnew.PCB_TRACK, pcbnew.ZONE, pcbnew.PAD))]
    for blabel, bnet, bshape in barrels:
        for label, net, lay, shape, obj in others:
            if net == bnet or not pcbnew.SHAPE.Collide(bshape, shape, pcbnew.FromMM(gap) - 1):
                continue
            g = r8.min_gap(bshape, shape, gap + 1)
            g = 0.0 if g is None else g
            key = (blabel, net, ctx.board.GetLayerName(lay))
            if key not in worst or g < worst[key]:
                worst[key] = g
    for (blabel, net, lay), g in sorted(worst.items()):
        issues.append(f'S-8: {net} copper on {lay} is {g:.3f} mm from the {blabel} barrel of '
                      f'{next(b[1] for b in barrels if b[0] == blabel)} (minimum {gap} mm)')
    return issues, dict(barrels=len(barrels), gap_mm=gap, near={f'{k[0]} / {k[1]} / {k[2]}': round(v, 3)
                                                                for k, v in sorted(worst.items())})


def fire_path(board, net, terminals):
    """(segments on the net's current path between the two terminal pad sets, connected?): the net's track graph
    (track ends, vias, pads as nodes) with dead-end branches pruned back until only copper between the terminals
    remains (a sense tap ending in a resistor pad is pruned; a branch inside one pad is no branch)."""
    import pcbnew
    pads, vias, segs = [], [], []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == net and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                pads.append((f'{f.GetReference()}.{p.GetNumber()}', f.GetReference(), p.GetNumber(), p))
    for t in board.GetTracks():
        if t.GetNetname() != net:
            continue
        (vias if t.GetClass() == 'PCB_VIA' else segs).append(t)
    term = [{lab for lab, ref, num, _ in pads if num in spec.get(ref, ())} for spec in terminals]

    def node(pt, lay):
        for lab, _, _, p in pads:
            if p.IsOnLayer(lay) and p.HitTest(pt):
                return 'P' + lab
        for v in vias:
            if (v.GetPosition() - pt).EuclideanNorm() <= v.GetWidth(lay) // 2:
                return 'V' + v.m_Uuid.AsString()
        return ('N', lay, round(pt.x / 1000), round(pt.y / 1000))
    edges = {}
    for t in segs:
        # a track end on another track's body (a T) splits that track there
        s, e = t.GetStart(), t.GetEnd()
        length = (e - s).EuclideanNorm()
        cuts = [0.0, 1.0]
        for o in segs:
            if o is t or o.GetLayer() != t.GetLayer() or length == 0:
                continue
            for q in (o.GetStart(), o.GetEnd()):
                k = ((q.x - s.x) * (e.x - s.x) + (q.y - s.y) * (e.y - s.y)) / length ** 2
                if 0 < k < 1:
                    px, py = s.x + k * (e.x - s.x), s.y + k * (e.y - s.y)
                    if math.hypot(q.x - px, q.y - py) <= 1000:
                        cuts.append(k)
        cuts = sorted(set(cuts))
        for i in range(len(cuts) - 1):
            pa = pcbnew.VECTOR2I(int(round(s.x + cuts[i] * (e.x - s.x))), int(round(s.y + cuts[i] * (e.y - s.y))))
            pb = pcbnew.VECTOR2I(int(round(s.x + cuts[i + 1] * (e.x - s.x))), int(round(s.y + cuts[i + 1] * (e.y - s.y))))
            a, b = node(pa, t.GetLayer()), node(pb, t.GetLayer())
            if a != b:
                edges[f'{t.m_Uuid.AsString()}/{i}'] = (a, b, t)
    keep = {'P' + lab for group in term for lab in group}
    while True:
        deg = {}
        for a, b, _ in edges.values():
            deg[a] = deg.get(a, 0) + 1
            deg[b] = deg.get(b, 0) + 1
        leaves = {n for n, d in deg.items() if d == 1 and n not in keep}
        if not leaves:
            break
        edges = {k: e for k, e in edges.items() if e[0] not in leaves and e[1] not in leaves}
    # connected between the terminals?
    adj = {}
    for a, b, _ in edges.values():
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    seen, stack = set(), ['P' + lab for lab in term[0]]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack += adj.get(n, ())
    joined = any('P' + lab in seen for lab in term[1])
    unique = {e[2].m_Uuid.AsString(): e[2] for e in edges.values()}
    return list(unique.values()), joined, [sorted(t) for t in term]


def s9(ctx, floor=FIRE_MIN_W, narrow=FIRE_NARROW):
    """R3-GATE-07: the fire-loop current path >= `floor` wide, pad necks and the measured `narrow` list excepted."""
    import pcbnew
    mm = pcbnew.ToMM
    issues, ev, used = [], {}, set()
    for net, terminals in FIRE_TERMINALS.items():
        minimum = min(floor, 0.5) if net in FIRE_ONLY else floor  # AUD-6: fire-only copper, not BAT_IN / ACT_FET_S.
        segs, joined, term = fire_path(ctx.board, net, terminals)
        widths = sorted({round(mm(t.GetWidth()), 3) for t in segs})
        ev[net] = dict(terminals=term, path_segments=len(segs), widths_mm=widths, joined=joined, minimum_mm=minimum)
        if not joined:
            issues.append(f'S-9: {net}: no copper path between its power terminals {term}')
            continue
        for t in segs:
            w = mm(t.GetWidth())
            if w >= minimum - EPS:
                continue
            s, e = t.GetStart(), t.GetEnd()
            ends = tuple(round(v, 2) for v in sorted([(mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))])[0] +
                         sorted([(mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))])[1])
            length = mm(t.GetLength())
            neck = False
            for pt in (s, e):
                for f in ctx.board.GetFootprints():
                    for p in f.Pads():
                        if p.GetNetname() == net and p.IsOnLayer(t.GetLayer()) and p.HitTest(pt) and \
                                mm(min(p.GetSize().x, p.GetSize().y)) <= w + EPS:
                            neck = True
            hit = [k for k, x in enumerate(narrow) if x[0] == net and x[1] == ctx.board.GetLayerName(t.GetLayer())
                   and abs(x[2] - w) <= 0.005 and abs(x[3] - length) <= 0.01
                   and all(abs(a - b) <= 0.01 for a, b in zip(x[4], ends))]
            if hit:
                used.add(hit[0])
                continue
            if neck:
                continue
            issues.append(f'S-9: {net} fire-path track {w:.3f} mm wide, {length:.3f} mm long on '
                          f'{ctx.board.GetLayerName(t.GetLayer())} ({ends[0]}, {ends[1]})-({ends[2]}, {ends[3]}); '
                          f'minimum {minimum} mm ({"AUD-6" if net in FIRE_ONLY else "D-R2-02"})')
    issues += [f'S-9: stale FIRE_NARROW entry {x[:5]} ({x[5]})' for k, x in enumerate(narrow) if k not in used]
    ev['narrow_used'] = [narrow[k][5] for k in sorted(used)]
    return issues, ev


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


def pcbnew_mm(v):
    import pcbnew
    return pcbnew.ToMM(v)


def m7(ctx):
    """check_r9.m7 (U4 bottom, rotation, lever arm, no via or fill under U4 / U5) at R10's recorded rotation, with the
    axis map read from the board."""
    import check_r9 as r9
    with patched(r9, IMU_ROTATION={**r9.IMU_ROTATION, ctx.board.GetTitleBlock().GetRevision(): IMU_ROTATION_R10}):
        issues, ev = r9.m7(ctx)
    u4 = ctx.fps.get('U4')
    if u4 is not None:
        c = u4.GetPosition()
        lever = pcbnew_mm(c.x) - 23.0
        pad1 = u4.FindPadByNumber('1')
        offset = (pcbnew_mm(pad1.GetPosition().x - c.x), pcbnew_mm(pad1.GetPosition().y - c.y)) if pad1 else None
        ev['imu_lever_arm_signed_mm'] = round(lever, 3)
        ev['imu_pad1_offset_mm'] = None if offset is None else [round(v, 3) for v in offset]
        if abs(lever - IMU_LEVER_R10) > 0.05:
            issues.append(f'M-7: U4 centre x offset from the roll axis (x 23) is {lever:.3f} mm, recorded '
                          f'{IMU_LEVER_R10} mm (M3_R10 "IMU axis map")')
        if offset is None or any(abs(a - b) > 0.05 for a, b in zip(offset, IMU_PAD1_R10)):
            issues.append(f'M-7: U4 pad 1 is at {offset} mm from the centre, recorded {IMU_PAD1_R10} (a mirrored or '
                          'rotated footprint would change the axis map)')
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
            ev[ref].update(wire_room_mm=round(room, 3), r8_floor_mm=WIRE_ROOM, r10_accepted_floor_mm=WIRE_ROOM_R10,
                           owner_decision='OQ-1 accepted 2026-10-28; physical 16-22 AWG fit not verified')
            if room < WIRE_ROOM_R10 - EPS:
                issues.append(f'P-11: {ref} has {room:.2f} mm of wire room to the bore wall (owner-accepted R10 '
                              f'floor {WIRE_ROOM_R10}; R8 {WIRE_ROOM})')
        else:
            issues += [f'P-11: {i}' for i in r9.axial_ok(ctx, f, d, face, box)]
    return issues, ev


def f9(ctx):
    """OQ-2: board-derived, reproducible reverse hot-plug evidence; never substitute a distance for a model pass."""
    import r10_hotplug as hp
    inputs = json.loads(hp.INPUTS.read_text())
    result = json.loads(hp.RESULTS.read_text())
    live = hp.extract(ctx.board, ctx.board_path)
    issues = []
    if hp.digest(live) != hp.digest(inputs):
        changed = [ref for ref in sorted(set(live['parts']) | set(inputs.get('parts', {})))
                   if hp.digest(live['parts'].get(ref)) != hp.digest(inputs.get('parts', {}).get(ref))]
        issues.append('F9-1: stale board-derived model inputs' + (': ' + ', '.join(changed) if changed else ''))
    issues += ['F9-1: ' + i for i in hp.validate(inputs, result, live['electrical_sha256'])]
    return issues, dict(board_sha256=live['board_sha256'], electrical_sha256=live['electrical_sha256'],
                        model_sha256=result.get('model_sha256'), qualification=result.get('qualification'),
                        limits=result.get('limits'), convergence=result.get('convergence'),
                        inference=result.get('inference'), owner_decision='OQ-2, 2026-10-28')


def local_ground_return(board, start, end, limit=14.0, step=.05, details=False):
    """GAP-2: shortest local saved-copper path, including real GND plane detours, on a 0.05mm grid.
    Layer changes occur only at GND vias/PTH copper, charged a full board thickness conservatively.
    This geometric model is not an inductance or electrical qualification."""
    import pcbnew
    import route_check as rc
    if start.GetNetname() != 'GND' or end.GetNetname() != 'GND':
        return None
    pts = [p.GetPosition() for p in (start, end)]
    grow = pcbnew.FromMM(2.)
    window = (min(p.x for p in pts) - grow, min(p.y for p in pts) - grow,
              max(p.x for p in pts) + grow, max(p.y for p in pts) + grow)
    raster = rc.Raster(window, pcbnew.FromMM(step))
    layers = [pcbnew.B_Cu, pcbnew.In1_Cu]  # GAP-2 reviewed local return: component side and uninterrupted In1 GND.
    copper, stitches, ends = [], [], []
    queue, best, came = [], {}, {}
    for i, layer in enumerate(layers):
        cop, stitch = rc.net_copper(board, 'GND', layer)
        copper.append(raster.fill(cop)); stitches.append(raster.fill(stitch))
        ends.append(raster.fill([rc._poly(end, layer)]) if end.IsOnLayer(layer) else bytearray(raster.nx * raster.ny))
        if start.IsOnLayer(layer):
            source = raster.fill([rc._poly(start, layer)])
            for k, on in enumerate(source):
                if on and copper[i][k]:
                    best[i, k] = 0.; came[i, k] = None; queue.append((0., i, k))
    heapq.heapify(queue)
    vertical = pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness())
    moves = [(dx, dy, step * math.hypot(dx, dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
    while queue:
        distance, layer, k = heapq.heappop(queue)
        if distance != best.get((layer, k)):
            continue
        if ends[layer][k]:
            if not details:
                return distance
            states, state = [], (layer, k)
            while state is not None:
                states.append(state); state = came[state]
            states.reverse()
            path = []
            for i, (lay, cell) in enumerate(states):
                if 0 < i < len(states) - 1:
                    before, after = states[i - 1], states[i + 1]
                    if before[0] == lay == after[0] and cell - before[1] == after[1] - cell:
                        continue
                x, y = raster.centre(cell)
                path.append([board.GetLayerName(layers[lay]), round(pcbnew.ToMM(x), 3), round(pcbnew.ToMM(y), 3)])
            return dict(distance_mm=distance, path_mm=path, layers=sorted({p[0] for p in path}),
                        endpoints=[f'{p.GetParentFootprint().GetReference()}.{p.GetNumber()}' for p in (start, end)])
        x, y = k % raster.nx, k // raster.nx
        adjacent = []
        for dx, dy, cost in moves:
            a, b = x + dx, y + dy
            if 0 <= a < raster.nx and 0 <= b < raster.ny:
                q = b * raster.nx + a
                if copper[layer][q] and (not dx or not dy or
                    (copper[layer][y * raster.nx + a] and copper[layer][b * raster.nx + x])):
                    adjacent.append((layer, q, cost))
        if stitches[layer][k]:
            adjacent += [(other, k, vertical) for other in range(len(layers)) if other != layer
                         and stitches[other][k] and copper[other][k]]
        for other, q, cost in adjacent:
            total = distance + cost
            if total <= limit and total < best.get((other, q), float('inf')):
                best[other, q] = total; came[other, q] = (layer, k); heapq.heappush(queue, (total, other, q))
    return None


def output_path(board, start, end):
    """GAP-2: shortest endpoint-linked B.Cu OUT track path; no vias, fills or remote-plane shortcut."""
    import pcbnew
    graph, positions = {}, {}
    for t in board.GetTracks():
        if t.GetClass() != 'PCB_TRACK' or t.GetLayer() != pcbnew.B_Cu or t.GetNetname() != start.GetNetname():
            continue
        a, b = [(p.x, p.y) for p in (t.GetStart(), t.GetEnd())]
        graph.setdefault(a, []).append((b, pcbnew.ToMM(t.GetLength())))
        graph.setdefault(b, []).append((a, pcbnew.ToMM(t.GetLength())))
        positions[a], positions[b] = t.GetStart(), t.GetEnd()
    starts = [p for p in positions if start.IsOnLayer(pcbnew.B_Cu) and start.HitTest(positions[p])]
    ends = {p for p in positions if end.IsOnLayer(pcbnew.B_Cu) and end.HitTest(positions[p])}
    queue, best, came = [(0., p) for p in starts], {p: 0. for p in starts}, {p: None for p in starts}
    heapq.heapify(queue)
    while queue:
        distance, p = heapq.heappop(queue)
        if distance != best.get(p):
            continue
        if p in ends:
            path, q = [], p
            while q is not None:
                path.append([pcbnew.ToMM(q[0]), pcbnew.ToMM(q[1])]); q = came[q]
            return dict(distance_mm=distance, path_mm=list(reversed(path)))
        for q, cost in graph[p]:
            total = distance + cost
            if total < best.get(q, float('inf')):
                best[q], came[q] = total, p; heapq.heappush(queue, (total, q))
    return None


def output_loop(ctx, bounds=None):
    """GAP-2: C82 and D9 protect U9 OUT through short actual OUT and local GND copper paths.
    Engineering regression bounds, not datasheet numeric limits or a bench qualification."""
    import check_r7 as r7
    import pcbnew
    pads = r7.pads_by_ref(ctx.board)
    out, ground = pads.get(('U9', '6')), pads.get(('U9', '8'))
    # GAP-2 reviewed cell: OUT / saved GND / total measured 3.391 / 9.178 / 12.569 mm (C82),
    # 6.873 / 9.818 / 16.692 mm (D9). These regression bounds preserve short local paths; TI gives no numeric limit.
    bounds = bounds or {'C82': (4., 10., 13.5), 'D9': (7., 10.5, 17.)}
    issues, ev = [], dict(bounds_mm=bounds, out_detour_ratio_max=1.25, ground_grid_mm=.05,
                          basis='GAP-2 engineering local-copper bounds; physical qualification pending',
                          area_method='projected OUT/GND paths joined through component pad centres; 0.05mm GND raster, not inductance')
    if out is None or ground is None or out.GetNetname() != 'RAW_PROTECTED' or ground.GetNetname() != 'GND':
        return ['GAP-2: U9 OUT.6 / GND.8 missing or miswired'], ev
    for ref in ('C82', 'D9'):
        power, ret = pads.get((ref, '1')), pads.get((ref, '2'))
        if power is None or ret is None or power.GetNetname() != 'RAW_PROTECTED' or ret.GetNetname() != 'GND':
            issues.append(f'GAP-2: {ref} must connect U9 OUT (pad1) to GND (pad2)'); continue
        f = ctx.fps[ref]
        if ref == 'C82' and (parse_value(f.GetValue(), 'C') or 0) < 1e-6:
            issues.append('GAP-2: C82 must provide at least 1uF on U9 OUT')
        if ref == 'D9' and f.GetValue() != 'B340A-13-F':
            issues.append('GAP-2: D9 must be the qualified B340A-13-F Schottky')
        if not all(p.IsOnLayer(pcbnew.B_Cu) for p in (out, power, ret, ground)):
            issues.append(f'GAP-2: {ref} requires the reviewed local B.Cu output protection cell')
        out_limit, return_limit, loop_limit = bounds[ref]
        out_path = output_path(ctx.board, out, power)
        outgoing = out_path['distance_mm'] if out_path else None
        ground_path = local_ground_return(ctx.board, ret, ground, return_limit, details=True)
        returning = ground_path['distance_mm'] if ground_path else None
        loop = None if outgoing is None or returning is None else outgoing + returning
        xy = lambda p: (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
        a, b = xy(out), xy(power)
        dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
        shortest = max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)
        detour = outgoing / shortest if outgoing is not None and shortest else None
        polygon = ([xy(out)] + out_path['path_mm'] + [xy(power), xy(ret)]
                   + [p[1:] for p in ground_path['path_mm']] + [xy(ground)]) if loop is not None else []
        area = abs(sum(a[0] * b[1] - a[1] * b[0] for a, b in zip(polygon, polygon[1:] + polygon[:1]))) / 2
        ev[ref] = dict(out_route_mm=outgoing, out_endpoints=['U9.6', ref + '.1'], out_layer='B.Cu',
                       out_path=out_path, out_octilinear_mm=shortest, out_detour_ratio=detour,
                       local_ground_route_mm=returning, ground_path=ground_path, loop_mm=loop,
                       projected_loop_area_mm2=area if polygon else None)
        if outgoing is None or outgoing > out_limit or detour is None or detour > ev['out_detour_ratio_max'] \
                or returning is None or loop > loop_limit:
            issues.append(f'GAP-2: {ref} needs short actual OUT / GND loop (OUT {outgoing}, return {returning}, loop {loop})')
    return issues, ev


def t1(ctx):
    """T-1 for R10 (D-R2-13): the west edge holds each end third; on the east side each end third is held by an
    east-edge tab or by a tab on that end's short edge within its east third. Clearances as tools/tab_windows.py."""
    import pcbnew
    import tab_windows as tw
    from fit_check import board_geometry
    b = ctx.board
    _, (x0, y0, x1, y1) = board_geometry(b)
    obs = tw.obstacles(b)
    holes = [((pcbnew.ToMM(d.GetCenter().x), pcbnew.ToMM(d.GetCenter().y)), pcbnew.ToMM(d.GetRadius()))
             for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE]

    def spans(edge):
        horiz = edge in ('aft', 'forward')
        e = {'west': x0, 'east': x1, 'aft': y0, 'forward': y1}[edge]
        lo, hi = (x0, x1) if horiz else (y0, y1)
        ok, a = [], lo + 0.5
        while a + tw.TAB_LEN <= hi - 0.5 + 1e-9:
            z = a + tw.TAB_LEN

            def gap(bb):
                along = max(bb[0] - z, a - bb[2], 0) if horiz else max(bb[1] - z, a - bb[3], 0)
                across = max(bb[1] - e, e - bb[3], 0) if horiz else max(bb[0] - e, e - bb[2], 0)
                return math.hypot(along, across)
            good = all(gap(bb) >= need - 1e-6 for _, bb, need in obs) and \
                all(gap((c[0] - r, c[1] - r, c[0] + r, c[1] + r)) >= tw.TAB_HOLE - 1e-6 for c, r in holes)
            if good:
                ok.append(round(a, 2))
            a = round(a + tw.STEP, 2)
        out = []
        for s in ok:
            if out and s - out[-1][1] <= tw.STEP + 0.01:
                out[-1][1] = s
            else:
                out.append([s, s])
        return [(p, round(q + tw.TAB_LEN, 2)) for p, q in out]
    wins = {e: spans(e) for e in ('west', 'east', 'aft', 'forward')}
    third_y, third_x = (y1 - y0) * tw.END_SHARE, (x1 - x0) * tw.END_SHARE
    aft = lambda ss: any(s[0] <= y0 + third_y - tw.TAB_LEN + 1e-6 for s in ss)           # noqa: E731
    fwd = lambda ss: any(s[1] >= y1 - third_y + tw.TAB_LEN - 1e-6 for s in ss)           # noqa: E731
    east_third = lambda ss: any(s[1] >= x1 - third_x + tw.TAB_LEN - 1e-6 for s in ss)    # noqa: E731
    issues = []
    if not aft(wins['west']):
        issues.append('T-1: no legal 5 mm tab on the west edge within the aft third')
    if not fwd(wins['west']):
        issues.append('T-1: no legal 5 mm tab on the west edge within the forward third')
    if not (aft(wins['east']) or east_third(wins['aft'])):
        issues.append('T-1: the east side of the aft third has no legal tab (east edge or aft edge east third)')
    if not (fwd(wins['east']) or east_third(wins['forward'])):
        issues.append('T-1: the east side of the forward third has no legal tab (east edge or forward edge east third)')
    return issues, dict(windows=wins, rule='R10_DECISIONS D-R2-13')


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


R10_PIN_TABLE = ROOT / 'm3_design/assembly_review/sources/r10_design/pin_table.tsv'


def loader_pins(board, port_pin=None, allowances=None):
    """K-loader (R3-MCU-01): (issues, evidence). Every U1 pin on a LOADER_H74X port that carries a net needs a
    LOADER_R10 allowance naming that net and the net's exact other members (pad -> part value); a loader-driven pin
    needs a reason for the drive; stale allowances fail."""
    allowances = LOADER_R10 if allowances is None else allowances
    if port_pin is None:
        with R10_PIN_TABLE.open() as table:
            port_pin = {row['port']: row['pin'] for row in csv.DictReader(table, delimiter='\t')}
    u1 = board.FindFootprintByReference(MCU_REF)
    if u1 is None:
        return ['U1 missing'], {}
    members = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            if real_net(p.GetNetname()) and f.GetReference() != MCU_REF:
                members.setdefault(p.GetNetname(), {})[f'{f.GetReference()}.{p.GetNumber()}'] = f.GetValue()
    issues, ev, used = [], {}, set()
    for port, (role, use) in sorted(LOADER_H74X.items()):
        pin = port_pin.get(port)
        if pin is None:
            ev[port] = 'not on this package'
            continue
        pad = u1.FindPadByNumber(pin)
        net = pad.GetNetname() if pad else None
        where = f'U1.{pin} {port} ({role}, loader {use}; AN2606 Rev 64 Table 119)'
        if pad is None:
            issues.append(f'{where}: pad missing')
            continue
        if not real_net(net):
            ev[port] = 'NC'
            continue
        entry = allowances.get(port)
        if entry is None:
            issues.append(f'{where} carries {net} with no LOADER_R10 allowance' +
                          (' (the loader drives this pin)' if use in LOADER_DRIVES else ''))
            continue
        used.add(port)
        want, pinned, reason = entry
        ev[port] = dict(net=net, role=role, use=use, reason=reason)
        if net != want:
            issues.append(f'{where} carries {net}; its allowance is for {want}')
            continue
        if not reason or not reason.strip():
            issues.append(f'{where}: allowance without an electrical reason')
        if pinned is not None:
            actual = members.get(net, {})
            if actual != pinned:
                extra = sorted(f'{k} {v}' for k, v in actual.items() if pinned.get(k) != v)
                gone = sorted(f'{k} {v}' for k, v in pinned.items() if actual.get(k) != v)
                issues.append(f'{where}: {net} members differ from the allowance (now {extra}, recorded {gone}); '
                              're-qualify the loader state')
    issues += [f'stale LOADER_R10 allowance {port} ({allowances[port][0]}): the pin carries no net or is not a loader '
               'pin' for port in sorted(set(allowances) - used)]
    return issues, ev


def k_loader(ctx):
    issues, ev = loader_pins(ctx.board)
    return [f'K-loader: {i}' for i in issues], ev


def silk_mask_overlaps(board, eps=0.001):
    """R3-MFG-01: every silkscreen item (board graphics and texts, footprint graphics, texts and visible fields), as its
    polygon, against every pad's solder mask opening on that side (the pad's copper polygon grown by its mask
    expansion; a pad with no mask layer on that side has none). DRC's silk-to-mask test misses degenerate shapes (a
    near-zero-length arc drawn as a nearly full circle); the polygons do not. Returns [(silk label, pad label, overlap
    depth mm)] with the depth the smaller side of the overlap's bounding box."""
    import pcbnew
    sides = ((pcbnew.F_SilkS, pcbnew.F_Mask, pcbnew.F_Cu), (pcbnew.B_SilkS, pcbnew.B_Mask, pcbnew.B_Cu))
    silk = {s: [] for s, _, _ in sides}

    def add(item, label):
        lay = item.GetLayer()
        if lay not in silk:
            return
        if hasattr(item, 'IsVisible') and not item.IsVisible():
            return
        poly = pcbnew.SHAPE_POLY_SET()
        item.TransformShapeToPolygon(poly, lay, 0, pcbnew.FromMM(0.001), pcbnew.ERROR_OUTSIDE)
        if poly.OutlineCount():
            silk[lay].append((label, poly, poly.BBox()))
    for d in board.GetDrawings():
        add(d, f'board {type(d).__name__} {getattr(d, "GetShapeStr", lambda: "")()}'.strip())
    for f in board.GetFootprints():
        ref = f.GetReference()
        for g in f.GraphicalItems():
            kind = g.GetShapeStr() if hasattr(g, 'GetShapeStr') else type(g).__name__
            at = g.GetStart() if hasattr(g, 'GetStart') else g.GetPosition()
            add(g, f'{ref} {kind} ({pcbnew.ToMM(at.x):.4f}, {pcbnew.ToMM(at.y):.4f})')
        for fld in f.GetFields():
            add(fld, f'{ref} field {fld.GetName()}')
    out = []
    for slay, mlay, clay in sides:
        if not silk[slay]:
            continue
        for f in board.GetFootprints():
            for p in f.Pads():
                if not p.IsOnLayer(mlay):
                    continue
                opening = pcbnew.SHAPE_POLY_SET()
                cu = clay if p.IsOnLayer(clay) else mlay
                grow = p.GetSolderMaskExpansion(mlay)
                p.TransformShapeToPolygon(opening, cu, max(0, grow), pcbnew.FromMM(0.001), pcbnew.ERROR_OUTSIDE)
                if grow < 0:                                   # a negative local margin shrinks the opening
                    opening.Inflate(grow, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, pcbnew.FromMM(0.001))
                if not opening.OutlineCount():
                    continue
                ob = opening.BBox()
                for label, poly, pb in silk[slay]:
                    if not pb.Intersects(ob):
                        continue
                    both = pcbnew.SHAPE_POLY_SET(poly)
                    both.BooleanIntersection(opening)
                    if not both.OutlineCount():
                        continue
                    bb = both.BBox()
                    depth = pcbnew.ToMM(min(bb.GetWidth(), bb.GetHeight()))
                    if depth > eps:
                        out.append((label, f'{f.GetReference()}.{p.GetNumber()} ({board.GetLayerName(mlay)})',
                                    round(depth, 3)))
    return sorted(set(out))



PORT_LEGENDS_R10 = {'J9': ('5V4', 'GND', 'RXI', 'TXO'), 'J2': ('3V3', 'SWDIO', 'NRST', 'SWCLK', 'GND', 'NC')}


def port_legends(board, required=PORT_LEGENDS_R10):
    """R10's port pin tables (m3_design/r10_post.PORTS; R3-REQ-04, D-R3-D4): pin 1 the supply, GND, then the board-side
    TXO / RXI. check_r7.pin_legends holds R7's camera-side J9 table."""
    import pcbnew
    seen = {}
    for item in board.GetDrawings():
        if isinstance(item, pcbnew.PCB_TEXT) and item.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            m = re.match(r'^(J\d+)\s+(.+)', item.GetText())
            if m and m[1] in required:
                for pin, name in re.findall(r'(\d+):([A-Z0-9]+)', m[2]):
                    seen.setdefault((m[1], int(pin)), set()).add(name)
    return [f'{ref}.{i}: silkscreen must identify {name} (R10 port table)' for ref, names in required.items()
            for i, name in enumerate(names, 1) if seen.get((ref, i)) != {name}]


# K-text (R8-GATE-02): the revision and safety legends are pinned to their exact words (a changed text fails).
PINNED_TEXTS = (('B.Silkscreen', 'M3-ASSY-R10'),)
# R8-GATE-03: these references must stay shown on silkscreen (all shown on the R10 board now). The full hidden list is
# reported in the evidence, not pinned.
SHOWN_REFS = ('J1', 'J121', 'J122', 'J400', 'J9', 'J410', 'J420', 'J3', 'Q120', 'Q121', 'Q124', 'R134')


def pinned_texts(board, pinned=PINNED_TEXTS):
    import pcbnew
    have = {}
    items = list(board.GetDrawings())
    for fp in board.GetFootprints():
        items += list(fp.GraphicalItems()) + list(fp.GetFields())
    for item in items:
        if isinstance(item, pcbnew.PCB_TEXT) and (not hasattr(item, 'IsVisible') or item.IsVisible()):
            have[(board.GetLayerName(item.GetLayer()), item.GetText())] = have.get(
                (board.GetLayerName(item.GetLayer()), item.GetText()), 0) + 1
    out = [f'silkscreen text {t!r} missing on {lay} (pinned revision / safety legend)' for lay, t in pinned
           if have.get((lay, t), 0) != 1]
    out += [f'obsolete ARM terminal or fuse legend {t!r} (single screw switch)' for (lay, t) in have
            if lay.endswith('Silkscreen') and (re.search(r'\bJ124\b|\bFUSE\b|\b5A\s+FAST\b', t, re.I)
                                               or re.fullmatch(r'ARM(?:1| CH1)?', t.strip(), re.I))]
    revs = sorted({t for (_, t) in have if re.match(r'^M3-ASSY-R\d+$', t)})
    return out + [f'revision legends {revs}: only M3-ASSY-R10 allowed' for _ in [0] if revs != ['M3-ASSY-R10']]


def hidden_refs(board, shown=SHOWN_REFS):
    """(issues, evidence): references not drawn on a silkscreen layer; a pinned safety / connector part may not be."""
    import pcbnew
    hidden = sorted(f.GetReference() for f in board.GetFootprints()
                    if not (f.Reference().IsVisible() and f.Reference().GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)))
    issues = [f'{r}: reference designator hidden (a safety / connector part must show it)'
              for r in shown if r in hidden]
    return issues, dict(hidden=hidden, hidden_count=len(hidden))


# K-width (R8-GATE-04): BAT_IN / RAW_PROTECTED track widths (recorded minimum 0.3 mm: U9 pad entries, D-R3-03).
HC_MIN_W = {'BAT_IN': 0.3, 'RAW_PROTECTED': 0.3}
HC_NARROW_MAX_LEN = 2.0          # mm: a chain of minimum-width segments longer than this fails


def k_width(board, floor=HC_MIN_W, max_len=HC_NARROW_MAX_LEN):
    import pcbnew
    mm = pcbnew.ToMM
    issues, ev = [], {}
    for net, wmin in floor.items():
        tr = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == net]
        ev[net] = dict(tracks=len(tr), min_width_mm=round(min((mm(t.GetWidth()) for t in tr), default=0), 3))
        narrow = []
        for t in tr:
            w = mm(t.GetWidth())
            if w < wmin - EPS:
                issues.append(f'{net} track {w:.3f} mm wide at ({mm(t.GetStart().x):.2f}, {mm(t.GetStart().y):.2f}) '
                              f'on {board.GetLayerName(t.GetLayer())}; minimum {wmin} mm')
            elif w <= wmin + EPS:
                narrow.append(t)
        parent = list(range(len(narrow)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i, a in enumerate(narrow):
            for j in range(i):
                b = narrow[j]
                ends = lambda t: {(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)}   # noqa: E731
                if a.GetLayer() == b.GetLayer() and ends(a) & ends(b):
                    parent[find(i)] = find(j)
        chains = {}
        for i, t in enumerate(narrow):
            chains.setdefault(find(i), []).append(t)
        longest = 0.0
        for ts in chains.values():
            length = sum(mm(t.GetLength()) for t in ts)
            longest = max(longest, length)
            if length > max_len + EPS:
                t = ts[0]
                issues.append(f'{net}: {wmin} mm-wide run {length:.2f} mm long on {board.GetLayerName(t.GetLayer())} '
                              f'near ({mm(t.GetStart().x):.2f}, {mm(t.GetStart().y):.2f}); limit {max_len} mm')
        ev[net]['longest_narrow_run_mm'] = round(longest, 2)
    return issues, ev


def k_legends(ctx):
    import check_r7 as r7
    import check_r8 as r8
    review = []
    with patched(r7, WORD_LEGENDS=WORD_LEGENDS_R10), patched(r8, TERMINAL_PINS=TERMINAL_PINS_R10):
        issues = list(r7.duplicate_ids(ctx.board)) + port_legends(ctx.board) + \
            list(r7.legend_subjects(ctx.board, distance_review=review))  # AUD-10: distance only, names still block.
        found, ev = r8.terminal_legends(ctx.board)
    overlaps = silk_mask_overlaps(ctx.board)
    found += [f'K-legends: silkscreen {s} overlaps the solder mask opening of {p} by {d:.3f} mm (R3-MFG-01)'
              for s, p, d in overlaps]
    texts = [f'K-legends: {i}' for i in pinned_texts(ctx.board)]
    hid, hev = hidden_refs(ctx.board)
    texts += [f'K-legends: {i}' for i in hid]
    return issues + found + texts, dict(terminal_legends=ev, silk_mask_overlaps=len(overlaps),
                                       aud10_review=review, aud10_review_count=len(review), **hev)


def k_reference(ctx):
    issues, ev = references(ctx.board)
    return [f'K-reference: {i}' for i in issues], ev


# GAP-3: a local VIPPO manufacturing condition, not a general via-in-pad exemption or a fabrication claim.
VIPPO_CENTRES = ((27.3, 13.6), (27.9, 13.6))
VIPPO_EP = (27.0, 12.6, 28.2, 14.6)
VIPPO_PASTE = ((27.035, 12.6, 28.165, 13.49), (27.035, 13.71, 28.165, 14.6))


def thermal_vias(board):
    """GAP-3: two 0.5/0.3 GND vias wholly in U401.11, with explicit filled/capped fabrication intent.
    The saved intent does not establish resin filling, copper capping or planarity: ordering and inspection do."""
    import pcbnew
    import check_r8 as r8
    issues, qualified = [], set()
    fp = board.FindFootprintByReference('U401')
    pad = fp.FindPadByNumber('11') if fp else None
    if pad is None or pad.GetNetname() != 'GND' or not pad.IsOnLayer(pcbnew.B_Cu):
        return ['GAP-3: U401.11 must be the bottom GND exposed pad'], {}, qualified
    xy = lambda p: (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))
    box = lambda ps: tuple(pcbnew.ToMM(v) for v in (ps.BBox().GetLeft(), ps.BBox().GetTop(),
                                                   ps.BBox().GetRight(), ps.BBox().GetBottom()))
    paste_polys = [poly for name, cu, poly in r8.paste_polys(board) if name == 'U401.paste' and cu == pcbnew.B_Cu]
    paste = [box(poly) for poly in paste_polys]
    paste_ok = len(paste) == 2 and all(any(max(abs(a - b) for a, b in zip(box(poly), expected)) <= EPS
                 and abs(poly.Area() / 1e12 - (expected[2] - expected[0]) * (expected[3] - expected[1])) <= EPS ** 2
                 for poly in paste_polys) for expected in VIPPO_PASTE)
    if not paste_ok:
        issues.append('GAP-3: U401 maker exposed-pad paste windows changed')
    shape = pad.GetEffectiveShape(pcbnew.B_Cu)
    ep_box = tuple(pcbnew.ToMM(v) for v in (shape.BBox().GetLeft(), shape.BBox().GetTop(),
                                            shape.BBox().GetRight(), shape.BBox().GetBottom()))
    ep_ok = (pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and pad.GetShape() == pcbnew.PAD_SHAPE_RECT
             and not pad.IsOnLayer(pcbnew.F_Cu) and max(abs(a - b) for a, b in zip(ep_box, VIPPO_EP)) <= EPS)
    if not ep_ok:
        issues.append('GAP-3: U401.11 exposed-pad shape or reviewed local pose changed')
    vias = [v for v in board.GetTracks() if v.GetClass() == 'PCB_VIA'
            and shape.Collide(pcbnew.SHAPE_CIRCLE(v.GetPosition(), v.GetDrillValue() // 2), pcbnew.FromMM(0.1))]
    if len(vias) != 2:
        issues.append(f'GAP-3: U401.11 requires exactly two thermal vias (has {len(vias)})')
    for centre in VIPPO_CENTRES:
        matches = [v for v in vias if math.dist(xy(v.GetPosition()), centre) <= EPS]
        ok = len(matches) == 1
        if ok:
            v = matches[0]
            ring, drill = pcbnew.ToMM(v.GetWidth(pcbnew.B_Cu)), pcbnew.ToMM(v.GetDrillValue())
            ok = (v.GetNetname() == 'GND' and abs(ring - 0.5) <= EPS and abs(drill - 0.3) <= EPS
                  and v.GetViaType() == pcbnew.VIATYPE_THROUGH
                  and v.TopLayer() == pcbnew.F_Cu and v.BottomLayer() == pcbnew.B_Cu
                  and v.GetFillingMode() == pcbnew.FILLING_MODE_FILLED
                  and v.GetCappingMode() == pcbnew.CAPPING_MODE_CAPPED)
            # The full ring, not only its centre, must fit the intended exposed pad.
            r = pcbnew.FromMM(0.25)
            c = v.GetPosition()
            ok = ok and all(shape.Collide(pcbnew.VECTOR2I(c.x + dx, c.y + dy), 0)
                            for dx, dy in ((-r, 0), (r, 0), (0, -r), (0, r)))
            if ok and paste_ok and ep_ok:
                qualified.add(v.m_Uuid.AsString())
        if not ok:
            issues.append(f'GAP-3: thermal via at {centre} must be 0.5/0.3 GND through-via, filled and capped, inside U401.11')
    return issues, dict(centres_mm=VIPPO_CENTRES, qualified=len(qualified), exposed_pad_mm=ep_box, paste_windows_mm=paste,
                        manufacturing_condition='resin-filled, copper-capped, planar VIPPO; physical fabrication unverified'), qualified


def k_copper(ctx):
    """GAP-3's exact U401 thermal vias only; every other inherited copper and paste check is unchanged."""
    import check_r7 as r7
    import check_r8 as r8
    import check_r9 as r9
    import pcbnew
    thermal, evidence, allowed = thermal_vias(ctx.board)
    smd, paste = r7.vias_in_smd_pads, r8.via_paste

    def pad_exempt(p, v):
        return (v.m_Uuid.AsString() in allowed and p.GetParentFootprint().GetReference() == 'U401'
                and p.GetNumber() == '11' and p.GetNetname() == 'GND')

    def paste_exempt(name, cu, poly, v):
        return v.m_Uuid.AsString() in allowed and name == 'U401.paste' and cu == pcbnew.B_Cu

    with patched(r7, vias_in_smd_pads=lambda b: smd(b, exempt=pad_exempt)), \
            patched(r8, via_paste=lambda b: paste(b, exempt=paste_exempt)):
        issues, ev = r9.k_copper(ctx)
    return issues + thermal, dict(ev, gap3=evidence)


FILL_TOLERANCE = 0.01          # mm^2 per zone and layer


def fill_freshness(path):
    """K-fill (R4-GATE-05): the saved zone fills are the board's current fills. A second copy of the board is loaded
    from `path`, refilled with ZONE_FILLER, and each zone's filled area per layer compared. Returns (issues, evidence)."""
    import pcbnew

    def areas(b):
        out = {}
        for z in b.Zones():
            if z.GetIsRuleArea():
                continue
            for lay in z.GetLayerSet().Seq():
                out[(z.m_Uuid.AsString(), b.GetLayerName(lay), z.GetNetname())] = (
                    z.GetFilledPolysList(lay).Area() / 1e12 if z.HasFilledPolysForLayer(lay) else 0.0)
        return out
    board = pcbnew.LoadBoard(str(path))
    before = areas(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    after = areas(board)
    stale = [(k, before[k], after.get(k)) for k in before if after.get(k) is None or abs(before[k] - after[k]) > FILL_TOLERANCE]
    return ([f'zone {k[2] or "(no net)"} on {k[1]}: saved fill {b:.3f} mm^2, refill {a if a is None else round(a, 3)} mm^2 '
             '(refill the zones and save the board)' for k, b, a in stale],
            {'zones': len(before), 'stale': len(stale), 'tolerance_mm2': FILL_TOLERANCE})


def k_fill(ctx):
    if not ctx.board_path or not Path(ctx.board_path).is_file():
        return ['K-fill: no board file path to refill a copy from'], {}
    issues, ev = fill_freshness(ctx.board_path)
    return [f'K-fill: {i}' for i in issues], ev


def k_region(ctx):
    issues, ev = region_issues(ctx.board)
    return [f'K-region: {i}' for i in issues], ev


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
    ('S-1', 'single screw switch: RAW_ACT pyro bus, no J124', lambda c, s: s1(c)),
    ('S-2', 'pyro feed only through the load switch', lambda c, s: s2(c)),
    ('S-3', 'gate networks defined off', lambda c, s: s3(c)),
    ('S-4', 'required-fitted safety parts (R1-07)', lambda c, s: s4(c)),
    ('S-5', 'J400 screw arming switch and protected EN contacts', lambda c, s: s5(c)),
    ('S-6', 'external ports apart from pyro / arming copper', lambda c, s: s6(c)),
    ('S-7', 'J122 servo + row off board, GND row on GND (O3)', lambda c, s: s7(c)),
    ('S-8', 'In1 / In2 copper >= 1.0 mm from pyro barrels (R3-SAF-01)', lambda c, s: s8(c)),
    ('S-9', 'fire-only copper >= 0.5 mm; BAT_IN / ACT_FET_S >= 1.0 mm (AUD-6)', lambda c, s: s9(c)),
    ('K-contract', 'R10 netlist contract', lambda c, s: k_contract(c)),
    ('K-loader', 'ROM-loader pins (AN2606 Table 119, R3-MCU-01)', lambda c, s: k_loader(c)),
    ('K-actuators', 'check_actuators --profile r10', lambda c, s: k_actuators(c)),
    ('LC-1', 'local clearance overrides', lambda c, s: __import__('check_r9').lc1(c.board)),
    ('M-1', 'outline 46 mm wide, length <= 120 mm', lambda c, s: m1(c)),
    ('M-3', 'J122 tie holes', _r9('m3')),
    ('M-5', 'fit (profile r10)', lambda c, s: m5(c, s)),
    ('M-6', 'bottom keep-outs', lambda c, s: m6(c)),
    ('M-7', 'IMU and MEMS', lambda c, s: m7(c)),
    ('P-11', 'terminal entry and owner-accepted 4.95 mm wire room', lambda c, s: p11(c)),
    ('F9-1', 'R10 reverse hot-plug model pass (OQ-2)', lambda c, s: f9(c)),
    ('F9-2', 'GAP-2 U9 output capacitor and Schottky local copper loops', lambda c, s: output_loop(c)),
    ('T-1', 'panel-tab windows (R10)', lambda c, s: t1(c)),
    ('K-legends', 'legends and ids', lambda c, s: k_legends(c)),
    ('M-2', 'vibration (plate model, r10_mated)', lambda c, s: m2(c, s)),
    ('P-8', 'sense resistors at the MCU end', _r9('p8')),
    ('K-copper', 'copper hygiene, exact GAP-3 U401 VIPPO condition', lambda c, s: k_copper(c)),
    ('K-inner', 'In1 / In2 signal tracks', _r9('k_inner_signal')),
    ('K-reference', 'critical signal reference copper', lambda c, s: k_reference(c)),
    ('K-region', 'critical B.Cu runs over one In2 plane region (R4-RTE-02)', lambda c, s: k_region(c)),
    ('K-fill', 'saved zone fills are current (refill a copy, R4-GATE-05)', lambda c, s: k_fill(c)),
    ('K-rules', 'm3.kicad_dru pinned, board design rules floor (R4-GATE-01)', lambda c, s: k_rules(c)),
    ('K-width', 'BAT_IN / RAW_PROTECTED width floor (R8-GATE-04)', lambda c, s: k_width(c.board)),
    ('K-retained', 'bare contacts, flash and camera bypass, TP122', lambda c, s: retained_routing(c)),
]
STAGES = {'functional': {'S-1', 'S-2', 'S-3', 'S-4', 'S-5', 'S-6', 'S-7', 'K-contract', 'K-loader', 'K-actuators'}}
STAGES['placement'] = STAGES['functional'] | {'LC-1', 'M-1', 'M-3', 'M-5', 'M-6', 'M-7', 'P-11', 'F9-1', 'T-1',
                                              'K-legends', 'K-width'}
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
    tables = {'r8_pin_table': ROOT / 'm3_design/assembly_review/sources/r8_design/pin_table.tsv',
              'r10_pin_table': R10_PIN_TABLE,
              'masses': ROOT / 'm3_design/assembly_review/sources/r10_design/masses.json'}
    report.update(board_sha256=sha, inputs_sha256=before, checker_sha256=file_sha(__file__),
                  contract_tables_sha256={k: {'path': str(v.relative_to(ROOT)), 'sha256': file_sha(v)}
                                          for k, v in tables.items()})
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
