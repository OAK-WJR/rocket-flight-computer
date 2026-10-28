#!/usr/bin/env python3
"""Independent R8 native-CAD contract (M3-ASSY-R8); complements KiCad DRC/ERC, check_actuators, route_check and fit_check.

usage: <KiCad python3> -I tools/check_r8.py [board.kicad_pcb] [--report out.json] [--print-hashes]
exit 0 = every check holds

Run with KiCad Python on a filled board. No generator module is imported. R8 keeps R7's contract
(tools/check_r7.py, frozen with the R7 record; its generic geometry checks are imported from it unchanged) with the
changes the R8 decisions make (m3_design/assembly_review/sources/r8_design/R8_DECISIONS.md):
  - U1's whole pin map comes from pin_table.tsv's r8_net column (all 100 pins; D2, D3, D14). The table itself is
    checked: 100 unique pins, the safety-contract pins unchanged (D14) and its loader markers equal to LOADER_DRIVEN.
  - R310 pulls RADIO_NSS to 3V3 (D4); STRIP_B / STRIP_VIA no longer admit RADIO_NSS or RADIO_DIO1 (D4, D14).
  - The tooling holes TH1-TH3 are gone (D8).
  - The strip fence is judged by geometry instead of R7's fixed openings: GND vias on FENCE_Y no more than
    FENCE_PITCH apart, except openings of at most FENCE_OPENING_MAX that a lane actually crosses (D16).
New checks (r8_plan.md section 2):
  rf_separation     F10: every RF part (RF_PART: the strip parts plus R306, R310, R313 and R315, D4 / F10 R8 text)
                    >= 5 mm, courtyard to courtyard, from the switching-regulator parts, the MCU, the flash and the
                    crystal, and >= 5 mm, courtyard to copper in plan view, from fast digital lines (D17)
  inner_power_pyro  no RAW_ACT or BAT_IN copper on In1 / In2 within 2.5 mm, in plan view, of PYRO1_BUS, PYRO1_IGN or
                    PYRO1_OUT copper on any layer (D18)
  gate_servo        PYRO1_GATE_N copper >= 0.5 mm from servo PWM copper on the same layer or on a layer closer than
                    0.5 mm through the stack-up (D19)
  loader_pins       a pin the ROM bootloader drives (AN2606 Table 135) carries only its D5 net, an LED, or nothing
  inner_signal      no track on In1 (S16) and no signal track on In2 (S15): In2 carries power and GND only (D20);
                    the one exception is the rigid CH1 block's internal ARM1_SENSE In2 link, exempt only while it is
                    exactly R7's segment (RIGID_IN2, D70)
  rigid             hash groups of the rigid, unmoved R7 items, against the R7 baseline (D11, D15): the RF strip
                    parts, RF copper, strip GND (fence row excepted), strip rule areas and the GCPW ground profile;
                    the CH1 block parts and copper; PYRO_BLOCK; J1; J122 with its tie holes; the M3 holes; the outline
  check_actuators   m3_design/check_actuators.py is byte-for-byte R7's (D14)
Fix pass 1 (R8_DECISIONS D85, D87, D92):
  battery_pyro      BAT_IN and ACT_FET_S copper (both battery-live whatever the power switch does) >= 1.0 mm, on the
                    same copper layer, from PYRO1_BUS / PYRO1_IGN / PYRO1_OUT copper (bus, igniter and drain):
                    m3.kicad_dru rule E's margin, which names RAW_ACT and the bus and igniter only (D85; R8P1-PYRO-01).
                    The drain since fix pass 2 (R8P2-PYRO-01): battery copper on PYRO1_OUT drives the igniter through
                    the fitted link into RAW_ACT's load with the power switch open, without Q124
  via_paste         no via ring overlaps a solder-paste aperture (0 mm) and no via hole lies within 0.1 mm of one
                    (paste-only pads included). Looser than R7's r7_route.ViaCheck and step7/make_ground.py, which keep
                    the whole ring 0.1 mm clear of the aperture: on the fix-pass-1 board 14 vias had a ring within
                    0.1 mm of an aperture against R7's 5 (D87; R8P1-DFM-01, R8P2-INTEGRITY-02)
  terminal_legends  every terminal pin legend (TERMINAL_PINS) exists once and its nearest connector pin (any pad of a
                    J part, measured from the legend's box) is its own pin (D92; R8P1-REQUIREMENTS-03)
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import pcbnew
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_r7 as r7                                           # noqa: E402 (R7's generic geometry checks, unchanged)
from fit_check import RETENTION_HOLES, board_geometry, fp_name, input_hashes, model_box   # noqa: E402
import route_check as rc                                        # noqa: E402

mm, MM = pcbnew.ToMM, pcbnew.FromMM
ROOT = Path(__file__).resolve().parents[1]
PIN_TABLE = ROOT / 'm3_design/assembly_review/sources/r8_design/pin_table.tsv'
CHECK_ACTUATORS = ROOT / 'm3_design/check_actuators.py'
# D14: check_actuators.py stays untouched in R8 (R7 commit 431025d). A reviewed contract change updates this hash and
# records the decision in R8_DECISIONS.
CHECK_ACTUATORS_SHA = '5de1eb3c3d5d549b0d6ac86bea3fa25142c612025216c636f05eb97e20da3080'

# --- contract constants (R7 values unless marked R8) ------------------------------------------------------------------
REMOVED = r7.REMOVED | {'TH1', 'TH2', 'TH3'}                    # R8 D8: the JLC tooling holes are removed
# D14: the safety-contract pins keep their R7 nets; the pin table must say so (pins 2-5, 15, 16, 22-25, 32-34, 40, 97,
# 98: the gate flanked by sentinels, CONT, the servos, ARM / RAW senses, the IMU status pin)
CONTRACT_PINS = {'2': None, '3': 'PYRO1_GATE_N', '4': None, '5': None, '15': 'PYRO1_CONT_MCU', '16': None,
                 '22': 'SERVO1_MCU', '23': 'SERVO2_MCU', '24': 'SERVO3_MCU', '25': 'SERVO4_MCU', '32': None,
                 '33': 'ARM1_SENSE_MCU', '34': 'RAW_ACT_SENSE_MCU', '40': None, '97': None, '98': 'IMU_INT1'}
PULLS = [('R310', 'RADIO_NSS', '3V3', '100k'), ('R311', 'RADIO_NRST', 'GND', '2k'),     # R8 D4: R310 on 3V3
         ('R312', 'RADIO_RXEN', 'GND', '100k')]
PULL_END = {'R310': ('U1', 'U31')}   # R8 D4: R310 at the MCU end of the NSS lane (nearer U1 than U31, centre to centre)
STRIP_B = re.compile(r'^(GND|GNSS_VCC_RF|GNSS_LNA_EN|GNSS_ANT_(DC|SRC|GATE|PD)|RADIO_TXEN)$')       # R8 D4
STRIP_VIA = re.compile(r'^(GND|GNSS_VCC_RF|GNSS_LNA_EN|GNSS_ANT_DC|RADIO_TXEN)$')                   # R8 D4
FENCE_OPENING_MAX = 2.7          # mm, R8 D16 (r8_plan section 1, from plan C: fence openings with gaps <= 2.7 mm)
FENCE_ROW = 0.06                 # mm: a GND via this close to FENCE_Y is a fence via

# --- D5: pins the ROM bootloader drives (AN2606 Rev 70 Table 135, pp. 320-323: outputs and open-drain I/O) ------------
LOADER_DRIVEN = ('PA2', 'PA6', 'PA8', 'PA9', 'PA11', 'PA12', 'PB6', 'PB9', 'PB10', 'PB14', 'PC9', 'PC11', 'PE13')
LOADER_ALLOWED = {'PA2': 'SERVO3_MCU', 'PB10': 'RADIO_SCK_MCU', 'PB14': 'RADIO_MOSI_MCU', 'PA11': 'USB_DM',
                  'PA12': 'USB_DP', 'PB6': 'QSPI_NCS', 'PB9': 'I2C1_SDA'}
LED = re.compile(r'^LED\d+$')

# --- D17: F10 RF separation ---------------------------------------------------------------------------------------
RF_SEPARATION = 5.0              # mm (F10: RF parts >= 5 mm from switching regulators, MCU, crystal, fast digital lines)
SWITCH_NETS = ('SW_NODE', 'BST', 'CAM_SW', 'CAM_BST', 'CAM_FB')
# the bucks' input / output capacitors, the camera eFuse and its output test pad: the restricted set of the R7 RF
# review (sources/r7_review/pass2_rf.md 3.9), which the parts on SWITCH_NETS complete
BUCK_PARTS = ('C6', 'C7', 'C8', 'C9', 'C72', 'C73', 'C75', 'C76', 'U7', 'TP71')
NOISY_PARTS = ('U1', 'U3', 'Y1')                                # the MCU, the QSPI flash, the crystal
FAST_NETS = re.compile(r'^(SW_NODE|BST|CAM_SW|CAM_BST|QSPI_.*|SPI1_.*|IMU_CS|SWDIO|SWCLK|USB_D[PM]|HSE_IN|HSE_OUT)$')
SEPARATION_REACH = 10.0          # mm: nearest distances are reported up to this

# --- D18 / D19 / D20 ----------------------------------------------------------------------------------------------
INNER_POWER = ('RAW_ACT', 'BAT_IN')
PYRO_LIVE = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')
INNER_POWER_PYRO = 2.5           # mm, plan view (2.5 x rule E; plan C section 6.2)
ARM_TERMINAL = 'J124'            # the ARM plug's own RAW contact is the break's other side (rule E / H, R4-qualified)
GATE_NET = 'PYRO1_GATE_N'
SERVO_PWM = re.compile(r'^SERVO[1-4]_(MCU|OUT)$')
GATE_SERVO = 0.5                 # mm
INNER = (pcbnew.In1_Cu, pcbnew.In2_Cu)
BATTERY_LIVE = ('BAT_IN', 'ACT_FET_S')   # D85: unswitched battery (ACT_FET_S through Q120's body diode)
ARM_SIDE = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')   # bus, igniter and drain (D85; the drain since R8P2-PYRO-01)
BATTERY_PYRO = 1.0               # mm, rule E's RAW_ACT figure
VIA_PASTE_HOLE = 0.1             # mm: via hole to a paste aperture; the ring only off it (0 mm), looser than
                                 # r7_route.ViaCheck / step7/make_ground.py's 0.1 mm ring clearance (D87)
TERMINAL_PINS = (('J124', (('1', 'BUS1'), ('2', 'RAW'))),
                 ('J121', (('1', 'E1-'), ('2', 'E1+'))),
                 ('J1', (('1', 'BAT+'), ('2', 'GND'), ('3', 'SW'), ('4', 'SW'))),
                 ('J123', (('1', 'PULL'), ('2', 'GND'))))
CONNECTOR = re.compile(r'^J\d+$')
# D70: the one In2 signal track D20 admits, the CH1 block's internal ARM1_SENSE link (R7 copy, in the rigid ch1_copper
# group; D9 / D15: the block's copper is never re-baselined). Exempt only while it is exactly this segment: net, ends
# (nm, sorted) and width (nm). Any other In2 signal copper, or this link moved, widened or extended, still fails.
RIGID_IN2 = {('ARM1_SENSE', ((14550000, 94150000), (14550000, 97550000)), 200000)}

# --- D11 / D15: rigid items, hash-asserted against R7 (c872a3d3...) -------------------------------------------------
STRIP_PARTS = ('J30', 'J31', 'U30', 'U31', 'D30', 'D31', 'L30', 'C302', 'C303', 'C304', 'C305', 'R304', 'R316', 'C313',
               'C314', 'Q30', 'Q31', 'Q32', 'R300', 'R301', 'R302', 'R303')
RF_NETS = ('GNSS_RF_ANT', 'GNSS_RF_IN', 'RADIO_RF_ANT', 'RADIO_RF')
STRIP_RULE_AREAS = ('U30_KEEPOUT', 'U31_KEEPOUT', 'R7_J30_launch_In1', 'R7_J31_launch_In1')
CH1_PARTS = ('J124', 'J121', 'Q124', 'R126', 'R127', 'R128', 'R129', 'R130', 'R131', 'R132', 'R133', 'R134', 'R173',
             'R175', 'R178', 'R180', 'C126', 'C127', 'C128', 'C129', 'D120', 'TP122')
CH1_NETS = re.compile(r'^(PYRO1_|ARM1_)(?!.*_MCU$)')
EXIT_VIAS = {'PYRO1_GATE_N': (23.0, 88.33), 'PYRO1_CONT': (28.4, 88.61), 'ARM1_SENSE': (18.18, 91.30)}  # plan_partial 5
GCPW_STEP, GCPW_SCAN, GCPW_REACH = 0.05, 0.01, 1.5   # mm: sample pitch along an RF line, outward step, search reach
# group -> sha256 of its canonical items on the R7 board c872a3d3... (`check_r8.py --print-hashes`, R8 step 1). Never
# re-baselined except by a recorded R8 decision naming the group (r8_plan section 5: only the approved A8 edit; D15).
RIGID_BASELINE = {
    'outline': '9558fcd7d3bc9b97f41d3f52c0f632653706218a07366f6777d7443c8e7a2858',           # 4 Edge.Cuts lines
    'm3_holes': '00605c61132c1574b6095361a30e073c3ee7b96b0d34c0d226bf37b0bd9434cf',          # 5 circles
    'j122_tie': '4ecfed731f5c5bc147c3c26222020a0b9732851139bb6295331c8d35f21041de',          # J122 + 2 tie circles
    'j1': '63a58164251c7035559d18db13e53ceb1544142abb5da8df02506f93b3463a1f',
    'pyro_block_area': '0571313b8489059d0e9a642b58075a3b2a4c25a6f8dda8cad8ea943a3d468d71',
    'ch1_parts': '23bcce687f97f89b59042b89d1994446b6665e61bf4a92113d986e66bbaa68db',         # 22 footprints
    'ch1_copper': '941283195211834998b4c166438eb61ff49d0babb94bdda678f3db47b8f067a1',        # 54 tracks, 6 vias
    'strip_parts': 'c71c1250c4f732ae9e5f210123f47946c788869d1cafa718e3377dc8df163163',       # 22 footprints
    'strip_rf_copper': '7a2598349ad81c5f4c1f3fd341e33a4c1db1ff332f26bf1c3e761cb37275b1fd',   # 8 RF tracks + DC via/F.Cu
    'strip_gnd': 'bfcbe417a3b45e1213558c488c16524bbcdb3df2e3289bece3a547cecbd21e4a',         # 175 vias, 1 track
    'strip_rule_areas': 'd105af8bf59da7466f509ec49b800351f6ecc0fcc478ae50787f1eef4d5754cd',  # 5 rule areas
    'strip_gcpw': '8b46f56919611ca6efe5381da6a01c9a8ea240512d3c3291200191dbdbcc6cc7',        # 8 RF line profiles
}


def xy(p):
    return mm(p.x), mm(p.y)


def footprints(board):
    return {f.GetReference(): f for f in board.GetFootprints()}


# --- pin table -----------------------------------------------------------------------------------------------------
def load_pin_table(path=PIN_TABLE):
    """pin_table.tsv rows as dicts (pin, port, r8_net, an2606_t135_loader_role, ...)."""
    with open(path, newline='') as fh:
        return list(csv.DictReader(fh, delimiter='\t'))


def pin_table_issues(rows):
    issues = []
    pins = [r['pin'] for r in rows]
    if sorted(pins, key=int) != [str(n) for n in range(1, 101)]:
        issues.append(f'pin table: pins must be 1-100 once each (found {len(pins)} rows)')
    by_pin = {r['pin']: r for r in rows}
    for pin, net in CONTRACT_PINS.items():
        got = by_pin.get(pin, {}).get('r8_net')
        if (None if got in (None, 'NC') else got) != net:
            issues.append(f'pin table: contract pin {pin} must stay {net or "NC"} (D14), table has {got}')
    marked = {r['port'] for r in rows if '[LOADER-DRIVEN]' in r.get('an2606_t135_loader_role', '')}
    if marked != set(LOADER_DRIVEN):
        issues.append(f'pin table: loader-driven ports {sorted(marked)} differ from AN2606 Table 135 '
                      f'(LOADER_DRIVEN {sorted(LOADER_DRIVEN)})')
    nets = [r['r8_net'] for r in rows if r['r8_net'] not in ('NC', 'GND', '3V3', '3V3A', 'VCAP1', 'VCAP2')]
    dup = sorted({n for n in nets if nets.count(n) > 1})
    if dup:
        issues.append(f'pin table: signal nets on more than one pin: {dup}')
    return issues


def _nc(net):
    return not net or net.startswith('unconnected-')


def led_net(board, net):
    """True when `net` drives an LED: it joins one MCU pin and series resistors whose other pad's net reaches an LED."""
    pads = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() == net]
    others = [p for p in pads if p.GetParentFootprint().GetReference() != 'U1']
    if not others or any(not re.match(r'^R\d+$', p.GetParentFootprint().GetReference()) for p in others):
        return False
    for p in others:
        far = [q for q in p.GetParentFootprint().Pads() if q.GetNumber() != p.GetNumber()]
        if len(far) != 1 or _nc(far[0].GetNetname()):
            return False
        if not any(LED.match(q.GetParentFootprint().GetReference()) for f in board.GetFootprints() for q in f.Pads()
                   if q.GetNetname() == far[0].GetNetname()):
            return False
    return True


def loader_pins(board, rows):
    """D5: a pin the ROM bootloader drives carries its allowed net, an LED net, or nothing."""
    issues, evidence = [], {}
    u1 = board.FindFootprintByReference('U1')
    if u1 is None:
        return ['U1 missing'], evidence
    port_pin = {r['port']: r['pin'] for r in rows}
    for port in LOADER_DRIVEN:
        pin = port_pin.get(port)
        pad = u1.FindPadByNumber(pin) if pin else None
        net = pad.GetNetname() if pad else None
        if pad is None:
            issues.append(f'U1 {port}: pin missing')
            continue
        if _nc(net):
            evidence[port] = 'NC'
        elif net == LOADER_ALLOWED.get(port):
            evidence[port] = net + ' (D5)'
        elif led_net(board, net):
            evidence[port] = net + ' (LED)'
        else:
            evidence[port] = net
            issues.append(f'U1.{pin} {port} is driven by the ROM bootloader (AN2606 Table 135) and may carry only '
                          f'{LOADER_ALLOWED.get(port, "an LED")} or nothing (D5); it carries {net}')
    return issues, evidence


# --- contract --------------------------------------------------------------------------------------------------------
def u1_pin_map(board, rows):
    """U1's pad nets against the pin table's r8_net column (NC: no net), and the pyro sentinels NC (also in the table:
    defence in depth)."""
    issues = []
    u1 = board.FindFootprintByReference('U1')
    want = {r['pin']: (None if r['r8_net'] == 'NC' else r['r8_net']) for r in rows}
    for pin in r7.PYRO_SENTINELS:
        if want.get(pin) is not None:
            issues.append(f'U1.{pin}: pyro sentinel must stay NC (check_actuators), the pin table gives {want[pin]}')
    for pin, net in sorted(want.items(), key=lambda kv: int(kv[0])):
        p = u1.FindPadByNumber(pin) if u1 else None
        actual = p.GetNetname() if p else None
        ok = p is not None and (actual == net if net is not None else _nc(actual))
        if not ok:
            issues.append(f'U1.{pin}: expected {net or "NC"}, found {actual}')
    return issues


def pulls(board):
    """Each pull resistor joins its signal to its rail with its value (R8 D4: R310 to 3V3)."""
    issues = []
    fps = footprints(board)
    for ref, signal, rail, val in PULLS:
        f = fps.get(ref)
        p1, p2 = (f.FindPadByNumber('1'), f.FindPadByNumber('2')) if f else (None, None)
        if not p1 or not p2 or {p1.GetNetname(), p2.GetNetname()} != {signal, rail}:
            issues.append(f'{ref}: must pull {signal} to {rail}')
        if not f or (f.GetValue().split() or [''])[0].lower() != val.lower():
            issues.append(f'{ref}: pull resistor must be {val}')
        if f and ref in PULL_END and all(r in fps for r in PULL_END[ref]):
            near, far = (xy(fps[r].GetPosition()) for r in PULL_END[ref])
            here = xy(f.GetPosition())
            if math.dist(here, near) >= math.dist(here, far):
                issues.append(f'{ref}: must sit at the {PULL_END[ref][0]} end of its lane (D4)')
    return issues


def check_contract(board, folder, rows):
    """R7's check_contract with the R8 pin map, pulls and removals (the rest is R7's, constant for constant)."""
    issues, notes, evidence = [], [], {}
    fps = footprints(board)
    pads = r7.pads_by_ref(board)
    for ref in sorted(REMOVED & fps.keys()):
        issues.append('removed part remains: ' + ref)
    nets = {str(name) for name in board.GetNetsByName()}
    for net in sorted(n for n in nets if re.search(r'PYRO2|ARM2', n) or n.startswith(r7.REMOVED_NETS)):
        issues.append('removed net remains: ' + net)
    for ref, expected in r7.FOOTPRINTS.items():
        if ref not in fps or fp_name(fps[ref]) != expected:
            issues.append(f'{ref}: requires {expected}')

    def expect(ref, pin, net):
        p = pads.get((ref, str(pin)))
        actual = p.GetNetname() if p else None
        ok = actual == net if net is not None else p is not None and _nc(actual)
        if not ok:
            issues.append(f'{ref}.{pin}: expected {net or "NC"}, found {actual}')
    for ref, nets_ in r7.CONNECTORS.items():
        for pin, net in enumerate(nets_, 1):
            expect(ref, pin, net)
    issues.extend(u1_pin_map(board, rows))                      # D14: the whole U1 map
    for (ref, pin), net in r7.MODULE_PINS.items():
        expect(ref, pin, net)
    expect('U4', '4', 'IMU_INT1')

    def value(ref):
        return fps[ref].GetValue().split()[0].lower() if ref in fps else None

    def center(ref):
        return xy(fps[ref].GetPosition())
    for ref, one, two, val, end, far in r7.SERIES:
        expect(ref, 1, one); expect(ref, 2, two)
        if value(ref) != val.lower():
            issues.append(f'{ref}: requires {val} series resistance')
        if ref in fps and end in fps and far in fps and \
                math.dist(center(ref), center(end)) >= math.dist(center(ref), center(far)):
            issues.append(f'{ref}: series resistor must sit at its driving end ({end})')
    issues.extend(pulls(board))
    for ref in r7.DNP:
        f = fps.get(ref)
        want = pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES
        if not f or (f.GetAttributes() & want) != want:
            issues.append(f'{ref}: DNP placeholder needs dnp, exclude-from-BOM and exclude-from-position flags')
    issues.extend(r7.dnp_paste(board))
    for ref in ('U30', 'U31'):
        if ref in fps and fps[ref].IsFlipped():
            issues.append(f'{ref}: module must be on the top side (single final reflow)')
    rf_refs = {r for r in fps if r7.RF_PART.fullmatch(r)}
    issues.extend(r7.rf_part_coverage(board))
    for ref in sorted(rf_refs):
        for p in fps[ref].Pads():
            if r7.SAFETY_NETS.match(p.GetNetname() or ''):
                issues.append(f'{ref}.{p.GetNumber()}: RF part on safety net {p.GetNetname()}')
    holes, outline = board_geometry(board)
    evidence['outline_mm'] = outline
    width, length = outline[2] - outline[0], outline[3] - outline[1]
    if abs(width - 46) > 0.01 or length > 120.01:
        issues.append(f'outline {width:g} x {length:g} mm violates 46 mm width / 120 mm maximum (P1)')
    for ref, axis in r7.JACKS.items():
        f = fps.get(ref)
        if not f:
            continue
        x, y = center(ref)
        if f.IsFlipped() or abs(f.GetOrientationDegrees()) > 0.01 or abs(x - axis) > 0.005 or abs(y - outline[1]) > 0.005:
            issues.append(f'{ref}: jack must be front side, rotation 0, at ({axis}, {outline[1]:g}) on the aft edge; '
                          f'is ({x:.3f}, {y:.3f}) rot {f.GetOrientationDegrees():g}')
        for p in f.Pads():
            if p.IsOnLayer(pcbnew.F_Paste) or p.IsOnLayer(pcbnew.B_Paste):
                issues.append(f'{ref}.{p.GetNumber()}: SMA pads carry no paste (fitted in the through-hole step)')
    if all(r in fps for r in r7.JACKS) and math.dist(center('J30'), center('J31')) < 12:
        issues.append('J30/J31 must be >= 12 mm apart, centre to centre (F10)')
    ch1 = [(key, pos) for key, pos in r7.CH1_PADS.items() if key in pads]
    for i, (key, position) in enumerate(ch1):
        for other, other_position in ch1[i + 1:]:
            old = math.dist(position, other_position)
            new = math.dist(xy(pads[key].GetPosition()), xy(pads[other].GetPosition()))
            if abs(new - old) > 0.02:
                issues.append(f'CH1 spacing changed: {key[0]}.{key[1]} to {other[0]}.{other[1]} '
                              f'{new:.3f} mm, R5 {old:.3f} mm')
    if all(ref in fps for ref in ('J1', 'J121', 'J124')):
        if max(math.dist(center('J1'), center(ref)) for ref in ('J121', 'J124')) > 25:
            issues.append('J1 must be grouped within 25 mm of both CH1 terminal centers')
    buzzer = fps.get('LS120')
    box = model_box(buzzer, folder) if buzzer else None
    if box is None or max(box[2] - box[0], box[3] - box[1]) >= 8.5:
        issues.append('LS120: readable model smaller than 8.5 x 8.5 mm required')
    flash, bypass = pads.get(('U3', '8')), pads.get(('C29', '1'))
    if flash and bypass:
        distance = math.dist(xy(flash.GetPosition()), xy(bypass.GetPosition()))
        route = r7.direct_route(board, flash, bypass)
        evidence.update(c29_vcc_pad_distance_mm=distance, c29_direct_route_mm=route)
        if distance > 2:
            issues.append(f'C29 VCC pad is {distance:.3f} mm from U3.8; maximum 2 mm')
        if route is None or route > 3:
            issues.append(f'C29 requires a direct same-layer route <=3 mm to U3.8; found {route}')
    else:
        issues.append('C29.1 or U3.8 is absent')
    found, evidence['camera_bypass'] = r7.camera_bypass(board)
    issues.extend(found)
    return issues, notes, evidence


# --- RF strip --------------------------------------------------------------------------------------------------------
def rf_strip(board):
    """R7's rf_strip with the R8 B.Cu and via net lists (D4): RADIO_NSS and RADIO_DIO1 no longer enter the strip
    below F.Cu."""
    issues, counted = [], defaultdict(int)

    def in_strip(box):
        return mm(box.GetTop()) < r7.STRIP_Y - 1e-6
    for t in board.GetTracks():
        if not in_strip(t.GetBoundingBox()):
            continue
        net = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            if not STRIP_VIA.match(net):
                issues.append(f'via of {net} at {xy(t.GetPosition())} in the RF strip')
            counted['vias'] += 1
            continue
        layer = t.GetLayer()
        ok = (r7.STRIP_F.match(net) if layer == pcbnew.F_Cu else STRIP_B.match(net) if layer == pcbnew.B_Cu else
              net == 'GND')
        if not ok:
            issues.append(f'{board.GetLayerName(layer)} track of {net} at {xy(t.GetStart())} in the RF strip')
        counted[board.GetLayerName(layer)] += 1
    for z in board.Zones():
        if z.GetIsRuleArea() or not in_strip(z.GetBoundingBox()) or z.GetNetname() == 'GND':
            continue
        for layer in z.GetLayerSet().CuStack():
            if z.HasFilledPolysForLayer(layer):
                polys = z.GetFilledPolysList(layer)
                if polys.OutlineCount() and mm(polys.BBox().GetTop()) < r7.STRIP_Y:
                    issues.append(f'{z.GetNetname()} pour on {board.GetLayerName(layer)} reaches the RF strip')
    for layer, name in ((pcbnew.In1_Cu, 'In1'), (pcbnew.In2_Cu, 'In2')):
        gnd = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(layer)
               and mm(z.GetBoundingBox().GetTop()) <= 0.5 and mm(z.GetBoundingBox().GetBottom()) >= r7.STRIP_Y]
        if not gnd:
            issues.append(f'{name}: no GND pour covers the RF strip')
    areas = {z.GetZoneName(): z for z in board.Zones() if z.GetIsRuleArea()}
    for name, layers in r7.KEEPOUTS.items():
        same = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetZoneName() == name]
        have = {board.GetLayerName(lay) for z in same for lay in z.GetLayerSet().CuStack()}
        if not same or have != set(layers):
            issues.append(f'{name}: rule area on {", ".join(layers)} required (m3.kicad_dru keep-out rules use it)')
    issues.extend(r7.u31_body_keepout(board))
    for ref, axis in r7.JACKS.items():
        z = areas.get(f'R7_{ref}_launch_In1')
        if not z:
            issues.append(f'{ref}: In1 cut-out rule area under the centre pad missing')
            continue
        bb = z.GetBoundingBox()
        if abs((mm(bb.GetLeft()) + mm(bb.GetRight())) / 2 - axis) > 0.01 or not z.GetDoNotAllowZoneFills() or \
                {board.GetLayerName(lay) for lay in z.GetLayerSet().CuStack()} != {'In1.Cu'}:
            issues.append(f'{ref}: In1 cut-out must be centred on the jack axis, In1 only, no fill')
    return issues, dict(counted)


def fence(board):
    """D16: the GND via fence on FENCE_Y. Consecutive fence vias (and the board's side edges) are at most FENCE_PITCH
    apart, except openings, each at most FENCE_OPENING_MAX wide and crossed by at least one non-GND track (a lane):
    a gap no lane needs is not an opening."""
    issues, evidence = [], {}
    _, outline = board_geometry(board)
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    xs = sorted(mm(v.GetPosition().x) for v in vias if abs(mm(v.GetPosition().y) - r7.FENCE_Y) < FENCE_ROW)
    pts = [outline[0]] + xs + [outline[2]]
    y = MM(r7.FENCE_Y)
    lanes = []
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA' or t.GetNetname() == 'GND':
            continue
        a, b = t.GetStart(), t.GetEnd()
        if (a.y - y) * (b.y - y) < 0 or (a.y == y) != (b.y == y):
            if a.y == b.y:
                continue
            x = a.x + (b.x - a.x) * (y - a.y) / (b.y - a.y)
            lanes.append((mm(x), t.GetNetname(), board.GetLayerName(t.GetLayer())))
    openings = []
    for a, b in zip(pts, pts[1:]):
        if b - a <= r7.FENCE_PITCH + 1e-6:
            continue
        crossing = sorted({(n, lay) for x, n, lay in lanes if a < x < b})
        openings.append(dict(x0=round(a, 3), x1=round(b, 3), width=round(b - a, 3), lanes=[n for n, _ in crossing]))
        if not crossing:
            issues.append(f'strip fence: GND vias {b - a:.2f} mm apart between x {a:.2f} and {b:.2f} with no lane '
                          f'through the gap (maximum {r7.FENCE_PITCH} mm)')
        elif b - a > FENCE_OPENING_MAX + 1e-6:
            issues.append(f'strip fence: opening x {a:.2f}-{b:.2f} is {b - a:.2f} mm wide (maximum {FENCE_OPENING_MAX} '
                          f'mm, D16; lanes {", ".join(n for n, _ in crossing)})')
    evidence.update(fence_vias=len(xs), openings=openings)
    return issues, evidence


def rf_line_stitching(board):
    """R7's rf_stitching without its fence part (fence() replaces it, D16): GND vias beside each RF line (largest gap
    per side <= STITCH_GAP or its accepted ceiling) and In1 GND under every RF track and pad plus IN1_MARGIN, except
    the SMA launch cut-outs (pass 2 RF-05)."""
    issues, evidence = [], {}
    gnd = [xy(t.GetPosition()) for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    pads = r7.pads_by_ref(board)
    for run, (nets, jack, module) in r7.RF_RUNS.items():
        tracks = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in nets]
        if not tracks:
            issues.append(f'{run}: RF line copper missing')
            continue
        segs = [(xy(t.GetStart()), xy(t.GetEnd())) for t in tracks]
        jack_pad = next((p for (r, n), p in pads.items() if r == jack and p.GetNetname() == nets[0]), None)
        mod_pad = next((p for (r, n), p in pads.items() if r == module and p.GetNetname() == nets[1]), None)
        if not jack_pad or not mod_pad:
            issues.append(f'{run}: RF pads missing')
            continue
        y0 = mm(jack_pad.GetBoundingBox().GetBottom())
        y1 = mm(mod_pad.GetBoundingBox().GetTop())
        main = [(a, b) for a, b in segs if abs(a[0] - b[0]) < 1e-6]
        for side, sign in (('west', -1), ('east', 1)):
            ys = []
            for vx, vy in gnd:
                if not (y0 <= vy <= y1):
                    continue
                for (a, b) in main:
                    lo, hi = sorted((a[1], b[1]))
                    off = (vx - a[0]) * sign
                    if lo - 0.5 <= vy <= hi + 0.5 and 0.4 < off <= 2.0:
                        ys.append(vy)
                        break
            ys = sorted(set([y0, y1] + ys))
            gap = max(b - a for a, b in zip(ys, ys[1:]))
            limit = r7.STITCH_ACCEPTED.get((run, side), r7.STITCH_GAP)
            evidence[f'{run}_{side}_largest_gap_mm'] = round(gap, 2)
            if gap > limit + 1e-6:
                issues.append(f'{run} {side}: GND stitching gap {gap:.2f} mm beside the RF line (maximum {limit} mm)')
    in1 = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.In1_Cu)]
    launch = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetZoneName().startswith('R7_J3')
              and z.GetZoneName().endswith('_launch_In1')]
    fill = pcbnew.SHAPE_POLY_SET()
    for z in in1:
        fill.BooleanAdd(z.GetFilledPolysList(pcbnew.In1_Cu))
    cut = pcbnew.SHAPE_POLY_SET()
    for z in launch:
        cut.BooleanAdd(z.Outline())
    rf_nets = {n for nets, _, _ in r7.RF_RUNS.values() for n in nets}
    items = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in rf_nets]
    items += [p for f in board.GetFootprints() if f.GetReference() not in r7.JACKS for p in f.Pads()
              if p.GetNetname() in rf_nets]
    inside = pcbnew.SHAPE_POLY_SET()
    inside.NewOutline()
    for x, y in ((0, 0), (46, 0), (46, 200), (0, 200)):
        inside.Append(MM(x), MM(y))
    missing = 0.0
    for it in items:
        poly = pcbnew.SHAPE_POLY_SET()
        it.TransformShapeToPolygon(poly, pcbnew.F_Cu, MM(r7.IN1_MARGIN), MM(0.005), pcbnew.ERROR_OUTSIDE)
        poly.BooleanIntersection(inside)
        poly.BooleanSubtract(fill)
        poly.BooleanSubtract(cut)
        area = poly.Area() / 1e12
        if area > 0.001:
            missing += area
            name = it.GetParentFootprint().GetReference() + '.' + it.GetNumber() if isinstance(it, pcbnew.PAD) \
                else f'{it.GetNetname()} track at {xy(it.GetStart())}'
            issues.append(f'In1: GND missing under {name} (+{r7.IN1_MARGIN} mm): {area:.3f} mm2')
    evidence['in1_missing_mm2'] = round(missing, 4)
    return issues, evidence


# --- geometry helpers for the new checks -----------------------------------------------------------------------------
def min_gap(a, b, reach):
    """Edge-to-edge distance in mm between two KiCad shapes (SHAPE / SHAPE_POLY_SET), to 0.001 mm; None when it is at
    least `reach` mm."""
    hit = pcbnew.SHAPE.Collide                     # the base-class overload takes any pair of shapes
    if not hit(a, b, MM(reach)):
        return None
    if hit(a, b, 0):
        return 0.0
    lo, hi = 0, MM(reach)
    while hi - lo > 500:
        m = (lo + hi) // 2
        if hit(a, b, m):
            hi = m
        else:
            lo = m
    return round(mm(hi), 3)


def courtyard(f):
    c = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    if c.OutlineCount():
        return pcbnew.SHAPE_POLY_SET(c)
    bb = f.GetBoundingBox(False)
    s = pcbnew.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in ((bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()), (bb.GetRight(), bb.GetBottom()),
                 (bb.GetLeft(), bb.GetBottom())):
        s.Append(x, y)
    return s


def item_shape(item, layer):
    """The copper of a pad, track or via on `layer` (vias and through-hole pads: their flashed ring, else the plated
    barrel)."""
    if isinstance(item, pcbnew.PCB_VIA):
        r = item.GetWidth(layer) // 2 if item.FlashLayer(layer) else item.GetDrillValue() // 2
        return pcbnew.SHAPE_CIRCLE(item.GetPosition(), r)
    if isinstance(item, pcbnew.PAD) and item.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and not item.FlashLayer(layer):
        return pcbnew.SHAPE_CIRCLE(item.GetPosition(), item.GetDrillSize().x // 2)
    return item.GetEffectiveShape(layer)


def net_items(board, nets, layers=None):
    """[(label, net, layer, shape)] of every pad, track, via and zone fill of `nets` (a predicate on the net name) on
    `layers` (default every copper layer)."""
    layers = list(board.GetEnabledLayers().CuStack()) if layers is None else list(layers)
    out = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH and nets(p.GetNetname()):
                for lay in layers:
                    if p.IsOnLayer(lay):
                        out.append((f'{f.GetReference()}.{p.GetNumber()}', p.GetNetname(), lay, item_shape(p, lay), p))
    for t in board.GetTracks():
        if not nets(t.GetNetname()):
            continue
        for lay in layers:
            if t.IsOnLayer(lay):
                kind = 'via' if t.GetClass() == 'PCB_VIA' else 'track'
                out.append((f'{kind} {xy(t.GetPosition() if kind == "via" else t.GetStart())}', t.GetNetname(), lay,
                            item_shape(t, lay), t))
    for z in board.Zones():
        if z.GetIsRuleArea() or not nets(z.GetNetname()):
            continue
        for lay in layers:
            if z.IsOnLayer(lay) and z.HasFilledPolysForLayer(lay):
                fill = z.GetFilledPolysList(lay)
                if fill.OutlineCount():
                    out.append((f'zone {z.GetZoneName() or z.GetNetname()}', z.GetNetname(), lay,
                                pcbnew.SHAPE_POLY_SET(fill), z))
    return out


# --- D17: F10 RF separation ------------------------------------------------------------------------------------------
def rf_separation(board, limit=RF_SEPARATION):
    """Every RF part's courtyard >= limit from each restricted part's courtyard (the parts on SWITCH_NETS, BUCK_PARTS,
    NOISY_PARTS) and, in plan view, from every fast digital line's copper (FAST_NETS)."""
    issues, evidence = [], {}
    fps = footprints(board)
    rf = sorted(r for r in fps if r7.RF_PART.fullmatch(r))
    restricted = {r for r, f in fps.items() if any(p.GetNetname() in SWITCH_NETS for p in f.Pads())}
    restricted |= {r for r in BUCK_PARTS + NOISY_PARTS if r in fps}
    yards = {r: courtyard(fps[r]) for r in set(rf) | restricted}
    fast = net_items(board, lambda n: bool(FAST_NETS.match(n or '')))
    for ref in rf:
        a = yards[ref]
        bb = a.BBox()
        near_part = None
        for other in sorted(restricted):
            g = min_gap(a, yards[other], SEPARATION_REACH)
            if g is not None and (near_part is None or g < near_part[0]):
                near_part = (g, other)
        near_line = None
        for label, net, lay, shape, _ in fast:
            sb = shape.BBox()
            if sb.GetLeft() > bb.GetRight() + MM(SEPARATION_REACH) or sb.GetRight() < bb.GetLeft() - MM(SEPARATION_REACH) \
                    or sb.GetTop() > bb.GetBottom() + MM(SEPARATION_REACH) or sb.GetBottom() < bb.GetTop() - MM(SEPARATION_REACH):
                continue
            g = min_gap(a, shape, SEPARATION_REACH)
            if g is not None and (near_line is None or g < near_line[0]):
                near_line = (g, net, f'{label} {board.GetLayerName(lay)}')
        evidence[ref] = dict(part=near_part, line=near_line)
        if near_part and near_part[0] < limit - 1e-3:
            issues.append(f'F10 separation: RF part {ref} is {near_part[0]:.2f} mm from {near_part[1]} '
                          f'(courtyards; minimum {limit} mm)')
        if near_line and near_line[0] < limit - 1e-3:
            issues.append(f'F10 separation: RF part {ref} is {near_line[0]:.2f} mm from fast line {near_line[1]} '
                          f'({near_line[2]}; minimum {limit} mm)')
    parts = [(v['part'][0], r, v['part'][1]) for r, v in evidence.items() if v['part']]
    lines = [(v['line'][0], r, v['line'][1]) for r, v in evidence.items() if v['line']]
    return issues, dict(per_part=evidence, nearest_part=min(parts) if parts else None,
                        nearest_line=min(lines) if lines else None, restricted=sorted(restricted))


# --- D18: inner power near pyro live copper ------------------------------------------------------------------------
def inner_power_pyro(board, limit=INNER_POWER_PYRO):
    """No RAW_ACT / BAT_IN copper on In1 or In2 (fills, tracks, via rings or barrels, through-hole pads) within limit,
    in plan view, of PYRO1_BUS / PYRO1_IGN / PYRO1_OUT copper on any layer. The ARM terminal's own RAW contact
    (ARM_TERMINAL) is the break's other side by design and is exempt."""
    issues, worst = [], {}
    power = [it for it in net_items(board, lambda n: n in INNER_POWER, INNER)
             if not (isinstance(it[4], pcbnew.PAD) and it[4].GetParentFootprint().GetReference() == ARM_TERMINAL)]
    live = net_items(board, lambda n: n in PYRO_LIVE)
    for label, net, lay, shape, _ in power:
        best = None
        for l2, n2, lay2, s2, _ in live:
            g = min_gap(shape, s2, limit + 2.5)
            if g is not None and (best is None or g < best[0]):
                best = (g, f'{l2} ({n2}, {board.GetLayerName(lay2)})')
        key = f'{net} {label} {board.GetLayerName(lay)}'
        if best is not None:
            worst[key] = best
        if best and best[0] < limit - 1e-3:
            issues.append(f'inner power near pyro: {key} is {best[0]:.2f} mm (plan view) from {best[1]}; minimum '
                          f'{limit} mm (D18)')
    near = min(((v[0], k, v[1]) for k, v in worst.items()), default=None)
    return issues, dict(nearest=near, items=len(power), within_5mm=len(worst))


# --- D85: battery-live copper beside the ARM bus and the igniter ----------------------------------------------------
def battery_pyro(board, limit=BATTERY_PYRO):
    """BAT_IN / ACT_FET_S copper >= limit from PYRO1_BUS / PYRO1_IGN / PYRO1_OUT copper on the same layer (D85)."""
    issues, worst = [], None
    live = net_items(board, lambda n: n in ARM_SIDE)
    for label, net, lay, shape, _ in net_items(board, lambda n: n in BATTERY_LIVE):
        for l2, n2, lay2, s2, _ in live:
            if lay2 != lay:
                continue
            g = min_gap(shape, s2, limit + 1.0)
            if g is None:
                continue
            if worst is None or g < worst[0]:
                worst = (g, f'{net} {label} to {n2} {l2} ({board.GetLayerName(lay)})')
            if g < limit - 1e-3:
                issues.append(f'battery-live copper near the ARM side: {net} {label} is {g:.3f} mm from {n2} {l2} on '
                              f'{board.GetLayerName(lay)}; minimum {limit} mm (D85, rule E\'s margin)')
    return issues, dict(nearest=worst)


# --- D87: vias against the solder-paste apertures -------------------------------------------------------------------
def paste_polys(board):
    """[(name, copper layer, SHAPE_POLY_SET)] of every pad's paste aperture (the pad shape grown by its paste margin;
    paste-only pads included)."""
    out = []
    for f in board.GetFootprints():
        for p in f.Pads():
            for paste, cu in ((pcbnew.F_Paste, pcbnew.F_Cu), (pcbnew.B_Paste, pcbnew.B_Cu)):
                if not p.IsOnLayer(paste):
                    continue
                poly = pcbnew.SHAPE_POLY_SET()
                p.TransformShapeToPolygon(poly, paste, 0, MM(0.001), pcbnew.ERROR_INSIDE)
                margin = p.GetSolderPasteMargin(paste).x
                if margin:
                    poly.Inflate(margin, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MM(0.001))
                out.append((f'{f.GetReference()}.{p.GetNumber() or "paste"}', cu, poly))
    return out


def via_paste(board, hole_gap=VIA_PASTE_HOLE, exempt=None):
    """No via ring overlaps a paste aperture on its side (0 mm) and no via hole lies within hole_gap of one (D87); the
    ring clause is looser than r7_route.ViaCheck's 0.1 mm (R8P2-INTEGRITY-02).
    Optional exempt(name, copper_layer, polygon, via) defaults to no exceptions (R10 GAP-3 only)."""
    issues, nearest, checked = [], None, 0
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
    for name, cu, poly in paste_polys(board):
        box = poly.BBox()
        for v in vias:
            c = v.GetPosition()
            if (abs(c.x - box.Centre().x) > box.GetWidth() // 2 + MM(1.0)
                    or abs(c.y - box.Centre().y) > box.GetHeight() // 2 + MM(1.0)) or not v.IsOnLayer(cu):
                continue
            if exempt is not None and exempt(name, cu, poly, v):
                continue
            checked += 1
            ring = pcbnew.SHAPE_CIRCLE(c, v.GetWidth(cu) // 2)
            hole = pcbnew.SHAPE_CIRCLE(c, v.GetDrillValue() // 2)
            where = f'via {xy(c)} ({v.GetNetname()}) and {name}\'s paste ({board.GetLayerName(cu)[0]})'
            if pcbnew.SHAPE.Collide(ring, poly, 0):
                issues.append(f'{where}: the via ring overlaps the paste aperture (D87)')
            elif pcbnew.SHAPE.Collide(hole, poly, MM(hole_gap) - 1):
                issues.append(f'{where}: the via hole is within {hole_gap} mm of the paste aperture (D87)')
            g = min_gap(ring, poly, 0.5)
            if g is not None and (nearest is None or g < nearest[0]):
                nearest = (g, where)
    return issues, dict(pairs_checked=checked, nearest_ring_mm=nearest)


# --- D92: terminal pin legends over their own pins --------------------------------------------------------------------
def terminal_legends(board):
    """Each terminal pin legend 'n:NAME' of TERMINAL_PINS exists once, and its nearest connector pin (a pad of any J
    part, measured from the pad centre to the legend's box) is its own pin, strictly (D92)."""
    expected = {(ref, num): f'{num}:{name}' for ref, pins in TERMINAL_PINS for num, name in pins}
    words = set(expected.values())
    pads = [(f.GetReference(), p.GetNumber(), p.GetPosition()) for f in board.GetFootprints()
            if CONNECTOR.match(f.GetReference()) for p in f.Pads() if p.GetNumber()]
    found, issues, evidence = defaultdict(list), [], {}
    for d in board.GetDrawings():
        if not isinstance(d, pcbnew.PCB_TEXT) or d.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            continue
        text = d.GetText().strip()
        if text not in words:
            continue
        bb = d.GetBoundingBox()

        def gap(c):
            dx = max(bb.GetLeft() - c.x, c.x - bb.GetRight(), 0)
            dy = max(bb.GetTop() - c.y, c.y - bb.GetBottom(), 0)
            return math.hypot(dx, dy)
        ranked = sorted((gap(c), ref, num) for ref, num, c in pads)
        (d0, ref, num), d1 = ranked[0], ranked[1][0]
        owner = (ref, num) if expected.get((ref, num)) == text and d1 - d0 > MM(0.01) else None
        evidence[f'{text} {xy(d.GetPosition())}'] = (f'{ranked[0][1]}.{ranked[0][2]}', round(mm(d0), 2),
                                                     f'{ranked[1][1]}.{ranked[1][2]}', round(mm(d1), 2))
        if owner is None:
            issues.append(f'terminal pin legend "{text}" at {xy(d.GetPosition())}: its nearest connector pin is '
                          f'{ranked[0][1]}.{ranked[0][2]} ({mm(d0):.2f} mm; next {ranked[1][1]}.{ranked[1][2]} '
                          f'{mm(d1):.2f} mm), not a pin it names (D92)')
        else:
            found[owner].append(text)
    for key, text in expected.items():
        if board.FindFootprintByReference(key[0]) is not None and len(found[key]) != 1:
            issues.append(f'{key[0]}.{key[1]}: {len(found[key])} legends "{text}" nearest it, expected one (D92)')
    return issues, evidence


# --- D19: gate drive beside servo PWM ------------------------------------------------------------------------------
def close_layer_pairs(board_path, limit=GATE_SERVO):
    """Copper layer pairs (same layer included) closer than `limit` mm through the board's own stack-up (mid-plane to
    mid-plane, tools/dc_solve.stackup)."""
    import dc_solve
    stack = dc_solve.stackup(board_path)
    ids = dict(zip(dc_solve.CU_NAMES, dc_solve.LAYERS))
    pairs = set()
    for a, (_, za) in stack.items():
        for b, (_, zb) in stack.items():
            if abs(za - zb) < limit:
                pairs.add((ids[a], ids[b]))
    return pairs


def gate_servo(board, pairs, limit=GATE_SERVO):
    """PYRO1_GATE_N copper >= limit from servo PWM copper (SERVO1-4 _MCU / _OUT) on every layer pair in `pairs`."""
    issues = []
    gate = net_items(board, lambda n: n == GATE_NET)
    servo = net_items(board, lambda n: bool(SERVO_PWM.match(n or '')))
    best, worst = None, {}
    for l1, _, lay1, s1, _ in gate:
        for l2, n2, lay2, s2, _ in servo:
            if (lay1, lay2) not in pairs:
                continue
            g = min_gap(s1, s2, limit + 1.5)
            if g is None:
                continue
            where = f'{GATE_NET} {l1} {pcbnew.LayerName(lay1)} to {n2} {l2} {pcbnew.LayerName(lay2)}'
            if best is None or g < best[0]:
                best = (g, where)
            key = (l1, n2)
            if g < limit - 1e-3 and (key not in worst or g < worst[key][0]):
                worst[key] = (g, where)
    for g, where in sorted(worst.values()):
        issues.append(f'gate beside servo PWM: {where} is {g:.3f} mm; minimum {limit} mm (D19)')
    return issues, dict(nearest=best, under_limit=len(worst),
                        layer_pairs=sorted((pcbnew.LayerName(a), pcbnew.LayerName(b)) for a, b in pairs))


# --- D20: S15 / S16 ----------------------------------------------------------------------------------------------------
def inner_signal(board):
    """No track on In1 (the GND reference plane, S16) and no signal track on In2 (S15: In2 carries only the route_check
    power class, GND included), but the rigid RIGID_IN2 link (D70), whose length is reported as In2_rigid_exempt."""
    issues, length, per = [], defaultdict(float), defaultdict(lambda: [0.0, 0, None])
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            continue
        lay, net = t.GetLayer(), t.GetNetname()
        if lay == pcbnew.In1_Cu:
            key = ('In1', net)
        elif lay == pcbnew.In2_Cu and rc.net_class(net) != 'power':
            ends = tuple(sorted((tuple(_p(t.GetStart())), tuple(_p(t.GetEnd())))))
            if (net, ends, t.GetWidth()) in RIGID_IN2:
                length['In2_rigid_exempt'] += mm(t.GetLength())
                continue
            key = ('In2_signal', net)
        else:
            continue
        n = mm(t.GetLength())
        length[key[0]] += n
        row = per[key]
        row[0] += n; row[1] += 1; row[2] = row[2] or xy(t.GetStart())
    for (where, net), (n, k, at) in sorted(per.items()):
        rule = 'In1 carries no track (S16, D20)' if where == 'In1' else 'In2 carries power and GND only (S15, D20)'
        issues.append(f'{where.split("_")[0]} track of {net}: {n:.1f} mm in {k} segments, first at {at}; {rule}')
    return issues, {k: round(v, 1) for k, v in length.items()}


# --- D11 / D15: rigid hash groups ------------------------------------------------------------------------------------
def _net(name):
    return '' if _nc(name) else name


def _p(v):
    return [int(v.x), int(v.y)]


def _layers(board, lset):
    return sorted(board.GetLayerName(lay) for lay in lset.Seq() if board.IsLayerEnabled(lay))


def canon_track(board, t):
    if t.GetClass() == 'PCB_VIA':
        return ['via', _net(t.GetNetname()), _p(t.GetPosition()), int(t.GetWidth(pcbnew.F_Cu)), int(t.GetDrillValue()),
                int(t.GetViaType()), board.GetLayerName(t.TopLayer()), board.GetLayerName(t.BottomLayer()),
                bool(t.GetRemoveUnconnected())]
    ends = sorted([_p(t.GetStart()), _p(t.GetEnd())])
    out = ['track', _net(t.GetNetname()), board.GetLayerName(t.GetLayer()), ends, int(t.GetWidth())]
    if t.GetClass() == 'PCB_ARC':
        out.append(_p(t.GetMid()))
    return out


def canon_pad(board, p):
    opt = lambda v: None if v is None else int(v)     # noqa: E731
    return [p.GetNumber(), _net(p.GetNetname()), int(p.GetAttribute()), int(p.GetShape()), _p(p.GetSize()),
            _p(p.GetPosition()), round(p.GetOrientationDegrees() * 1000), _p(p.GetOffset()), _p(p.GetDrillSize()),
            int(p.GetDrillShape()), _layers(board, p.GetLayerSet()), opt(p.GetLocalClearance()),
            opt(p.GetLocalSolderMaskMargin()), opt(p.GetLocalSolderPasteMargin()), int(p.GetLocalZoneConnection()),
            round(p.GetRoundRectRadiusRatio() * 1e6), round(p.GetChamferRectRatio() * 1e6), int(p.GetChamferPositions()),
            bool(p.GetRemoveUnconnected())]


def canon_fp(board, f):
    """Placement and copper of a footprint: library id, position, rotation, side, attributes and every pad (net,
    shape, size, position, drill, layers, local rules). Silkscreen, fab and value text are not geometry."""
    return ['fp', f.GetReference(), f.GetFPIDAsString(), _p(f.GetPosition()), round(f.GetOrientationDegrees() * 1000),
            bool(f.IsFlipped()), int(f.GetAttributes()), sorted(canon_pad(board, p) for p in f.Pads())]


def canon_area(board, z):
    poly = z.Outline()
    contours = []
    for i in range(poly.OutlineCount()):
        for ch in [poly.Outline(i)] + [poly.Hole(i, h) for h in range(poly.HoleCount(i))]:
            pts = [_p(ch.CPoint(k)) for k in range(ch.PointCount())]
            k = pts.index(min(pts))
            contours.append(pts[k:] + pts[:k])
    return ['area', z.GetZoneName(), _net(z.GetNetname()), _layers(board, z.GetLayerSet()), sorted(contours),
            [bool(z.GetDoNotAllowTracks()), bool(z.GetDoNotAllowVias()), bool(z.GetDoNotAllowPads()),
             bool(z.GetDoNotAllowZoneFills()), bool(z.GetDoNotAllowFootprints())]]


def canon_edge(d):
    s = d.GetShape()
    if s == pcbnew.SHAPE_T_CIRCLE:
        return ['circle', _p(d.GetCenter()), int(d.GetRadius())]
    out = [d.GetShapeStr(), sorted([_p(d.GetStart()), _p(d.GetEnd())])]
    if s == pcbnew.SHAPE_T_ARC:
        out.append(_p(d.GetArcMid()))
    return out


def edge_items(board):
    return [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]


def is_hole(d, centers=None):
    if d.GetShape() != pcbnew.SHAPE_T_CIRCLE or abs(mm(d.GetRadius()) - 1.6) > 0.01:
        return False
    if centers is None:
        return True
    return any(math.dist(xy(d.GetCenter()), c) < 0.01 for c in centers)


def _graph_reach(board, pads, tracks, stop=lambda t: False):
    """Tracks and vias reached from `pads` through same-net copper (track ends meeting, a track end on another track's
    centre line, inside a via or a pad on a shared layer); a via for which stop(via) holds is included but not passed;
    no pad other than the given ones is passed."""
    def touches(t, item):
        ends = [t.GetStart(), t.GetEnd()] if t.GetClass() != 'PCB_VIA' else [t.GetPosition()]
        if isinstance(item, pcbnew.PAD):
            return any(item.HitTest(e) for e in ends) and \
                (t.GetClass() == 'PCB_VIA' or item.IsOnLayer(t.GetLayer()))
        if item.GetClass() == 'PCB_VIA':
            r = item.GetWidth(pcbnew.F_Cu) / 2
            return any(math.hypot(e.x - item.GetPosition().x, e.y - item.GetPosition().y) <= r for e in ends)
        if t.GetClass() == 'PCB_VIA':
            return touches(item, t)
        if item.GetLayer() != t.GetLayer():
            return False
        oth = [item.GetStart(), item.GetEnd()]
        for e in ends:
            if any(abs(e.x - o.x) <= 1000 and abs(e.y - o.y) <= 1000 for o in oth):
                return True
            if r7.distance_to_segment(xy(e), xy(oth[0]), xy(oth[1])) <= 0.001:
                return True
        return any(r7.distance_to_segment(xy(o), xy(ends[0]), xy(ends[1])) <= 0.001 for o in oth)
    seen, todo = [], [t for t in tracks if any(touches(t, p) for p in pads)]
    while todo:
        t = todo.pop()
        if any(t is s or t.m_Uuid.AsString() == s.m_Uuid.AsString() for s in seen):
            continue
        seen.append(t)
        if t.GetClass() == 'PCB_VIA' and stop(t):
            continue
        for u in tracks:
            if not any(u.m_Uuid.AsString() == s.m_Uuid.AsString() for s in seen) and touches(u, t):
                todo.append(u)
        for p in pads:                                          # through a given pad to its other tracks
            if touches(t, p):
                todo.extend(u for u in tracks if touches(u, p))
    return seen


def ch1_copper(board):
    """The CH1 block's copper (D9, D11): every track and via of the block-internal pyro nets; for the exit nets, the
    copper from the block pads up to and including the exit via (the lane beyond it is not block copper); GND
    tracks from the block pads up to the first via. RAW_ACT and 3V3 feeds are not block copper."""
    block = [f for f in board.GetFootprints() if f.GetReference() in CH1_PARTS]
    bpads = [p for f in block for p in f.Pads()]
    nets = {p.GetNetname() for p in bpads if CH1_NETS.match(p.GetNetname() or '')}
    allpads = defaultdict(set)
    for f in board.GetFootprints():
        for p in f.Pads():
            allpads[p.GetNetname()].add(f.GetReference())
    items = []
    by_net = defaultdict(list)
    for t in board.GetTracks():
        by_net[t.GetNetname()].append(t)
    for net in sorted(nets):
        internal = allpads[net] <= set(CH1_PARTS) and net not in EXIT_VIAS
        if internal:
            items += by_net[net]
            continue
        exit_xy = EXIT_VIAS.get(net)
        stop = (lambda v, e=exit_xy: e is not None and math.dist(xy(v.GetPosition()), e) < 0.01)
        items += _graph_reach(board, [p for p in bpads if p.GetNetname() == net], by_net[net], stop)
    items += _graph_reach(board, [p for p in bpads if p.GetNetname() == 'GND'], by_net['GND'], lambda v: True)
    return items


def gcpw_profile(board):
    """The F.Cu GND gap beside every RF line (D15: the coplanar ground the pass-2 field solve used): along each RF
    track every GCPW_STEP, the distance from the track edge to the first F.Cu GND copper on each side, stepped by
    GCPW_SCAN out to GCPW_REACH ({track: [(left, right) in GCPW_SCAN units, or -1 beyond reach]})."""
    gnd = pcbnew.SHAPE_POLY_SET()
    window = MM(r7.STRIP_Y + 3)
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.F_Cu) and \
                z.HasFilledPolysForLayer(pcbnew.F_Cu):
            gnd.BooleanAdd(z.GetFilledPolysList(pcbnew.F_Cu))
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == 'GND' and p.IsOnLayer(pcbnew.F_Cu) and p.GetPosition().y < window:
                p.TransformShapeToPolygon(gnd, pcbnew.F_Cu, 0, MM(0.001), pcbnew.ERROR_INSIDE)
    for t in board.GetTracks():
        if t.GetNetname() == 'GND' and t.IsOnLayer(pcbnew.F_Cu) and t.GetBoundingBox().GetTop() < window:
            t.TransformShapeToPolygon(gnd, pcbnew.F_Cu, 0, MM(0.001), pcbnew.ERROR_INSIDE)
    gnd.Simplify()
    out = {}
    steps = int(round(GCPW_REACH / GCPW_SCAN))
    for t in sorted((t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in RF_NETS),
                    key=lambda t: sorted([_p(t.GetStart()), _p(t.GetEnd())])):
        (ax, ay), (bx, by) = sorted([_p(t.GetStart()), _p(t.GetEnd())])
        length = math.hypot(bx - ax, by - ay)
        if length == 0:
            continue
        ux, uy = (bx - ax) / length, (by - ay) / length
        half = t.GetWidth() / 2
        prof = []
        for k in range(int(length // MM(GCPW_STEP)) + 1):
            cx, cy = ax + ux * k * MM(GCPW_STEP), ay + uy * k * MM(GCPW_STEP)
            row = []
            for sx, sy in ((-uy, ux), (uy, -ux)):
                hit = -1
                for s in range(1, steps + 1):
                    d = half + s * MM(GCPW_SCAN)
                    if gnd.Contains(pcbnew.VECTOR2I(int(round(cx + sx * d)), int(round(cy + sy * d)))):
                        hit = s
                        break
                row.append(hit)
            prof.append(tuple(row))
        out[f'{t.GetNetname()} {[ax, ay]}-{[bx, by]} w{t.GetWidth()}'] = prof
    return out


def rigid_groups(board):
    """{group: canonical items} of the rigid R7 items (D11, D15)."""
    fps = footprints(board)
    g = {}
    g['outline'] = sorted(canon_edge(d) for d in edge_items(board) if d.GetShape() != pcbnew.SHAPE_T_CIRCLE)
    g['m3_holes'] = sorted(canon_edge(d) for d in edge_items(board) if is_hole(d) and not is_hole(d, RETENTION_HOLES))
    g['j122_tie'] = [canon_fp(board, fps['J122'])] if 'J122' in fps else []
    g['j122_tie'] += sorted(canon_edge(d) for d in edge_items(board) if is_hole(d, RETENTION_HOLES))
    g['j1'] = [canon_fp(board, fps['J1'])] if 'J1' in fps else []
    g['pyro_block_area'] = sorted(canon_area(board, z) for z in board.Zones()
                                  if z.GetIsRuleArea() and z.GetZoneName() == 'PYRO_BLOCK')
    g['ch1_parts'] = sorted(canon_fp(board, fps[r]) for r in CH1_PARTS if r in fps)
    g['ch1_copper'] = sorted(canon_track(board, t) for t in ch1_copper(board))
    g['strip_parts'] = sorted(canon_fp(board, fps[r]) for r in STRIP_PARTS if r in fps)
    strip_rf = [t for t in board.GetTracks() if t.GetNetname() in RF_NETS]
    strip_rf += [t for t in board.GetTracks() if t.GetNetname() == 'GNSS_ANT_DC' and
                 (t.GetClass() == 'PCB_VIA' or t.GetLayer() == pcbnew.F_Cu)]
    g['strip_rf_copper'] = sorted(canon_track(board, t) for t in strip_rf)
    gnd = [t for t in board.GetTracks() if t.GetNetname() == 'GND' and (
        (t.GetClass() == 'PCB_VIA' and mm(t.GetPosition().y) < r7.STRIP_Y and
         abs(mm(t.GetPosition().y) - r7.FENCE_Y) >= FENCE_ROW) or
        (t.GetClass() != 'PCB_VIA' and mm(t.GetBoundingBox().GetTop()) < r7.STRIP_Y))]
    g['strip_gnd'] = sorted(canon_track(board, t) for t in gnd)
    g['strip_rule_areas'] = sorted(canon_area(board, z) for z in board.Zones()
                                   if z.GetIsRuleArea() and z.GetZoneName() in STRIP_RULE_AREAS)
    g['strip_gcpw'] = sorted([k, v] for k, v in gcpw_profile(board).items())
    return g


def digest(items):
    return hashlib.sha256(json.dumps(items, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def rigid(board, baseline=None):
    """Each rigid group's digest against the R7 baseline."""
    baseline = RIGID_BASELINE if baseline is None else baseline
    issues, evidence = [], {}
    for name, items in rigid_groups(board).items():
        d = digest(items)
        evidence[name] = dict(items=len(items), sha256=d)
        if name not in baseline:
            issues.append(f'rigid group {name}: no R7 baseline digest')
        elif baseline[name] != d:
            issues.append(f'rigid group {name} differs from R7 ({len(items)} items, sha256 {d[:16]}, R7 '
                          f'{baseline[name][:16]}): rigid, unmoved R7 copy changed (D11, D15)')
    for name in sorted(set(baseline) - set(evidence)):
        issues.append(f'rigid group {name}: not computed')
    return issues, evidence


def actuators_unchanged(path=CHECK_ACTUATORS):
    d = hashlib.sha256(Path(path).read_bytes()).hexdigest() if Path(path).is_file() else None
    if d != CHECK_ACTUATORS_SHA:
        return [f'm3_design/check_actuators.py differs from R7 (sha256 {d}); D14 keeps it untouched'], d
    return [], d


# --- the gate --------------------------------------------------------------------------------------------------------
def check_board(board, folder, board_path=None, rows=None):
    rows = load_pin_table() if rows is None else rows
    issues = pin_table_issues(rows)
    found, notes, evidence = check_contract(board, folder, rows)
    issues.extend(found)
    issues.extend(r7.duplicate_ids(board))
    issues.extend(r7.pin_legends(board))
    issues.extend(r7.legend_subjects(board))
    found, evidence['rf_strip_items'] = rf_strip(board); issues.extend(found)
    found, evidence['fence'] = fence(board); issues.extend(found)
    copper = r7.copper_shapes(board)
    found, evidence['guarded_pads'] = r7.foreign_clearances(board, copper); issues.extend(found)
    issues.extend(r7.vias_on_through_pads(board))
    found, evidence['smd_pads_checked_for_via_holes'] = r7.vias_in_smd_pads(board); issues.extend(found)
    found, evidence['rf_stitching'] = rf_line_stitching(board); issues.extend(found)
    found, evidence['track_endpoints_checked'] = r7.overlap_only_joints(board, copper); issues.extend(found)
    rule_file = folder / (Path(board.GetFileName()).stem + '.kicad_dru')
    found, evidence['small_ground_pads'] = r7.thermal_policy(board, rule_file.read_text() if rule_file.is_file() else '')
    issues.extend(found)
    found, evidence['rf_ground_via_mm'] = r7.rf_grounds(board, ''); issues.extend(found)
    found, evidence['launch_in2_reference'] = r7.launch_reference(board); issues.extend(found)
    found, evidence['module_ground'] = r7.module_ground(board); issues.extend(found)
    found, evidence['strip_gnd_reach_mm'] = r7.rf_gnd_reach(board); issues.extend(found)
    found, evidence['loader_pins'] = loader_pins(board, rows); issues.extend(found)
    found, evidence['rf_separation'] = rf_separation(board); issues.extend(found)
    found, evidence['inner_power_pyro'] = inner_power_pyro(board); issues.extend(found)
    found, evidence['battery_pyro'] = battery_pyro(board); issues.extend(found)
    found, evidence['via_paste'] = via_paste(board); issues.extend(found)
    found, evidence['terminal_legends'] = terminal_legends(board); issues.extend(found)
    pairs = close_layer_pairs(board_path or board.GetFileName())
    found, evidence['gate_servo'] = gate_servo(board, pairs); issues.extend(found)
    found, evidence['inner_signal_mm'] = inner_signal(board); issues.extend(found)
    found, evidence['rigid'] = rigid(board); issues.extend(found)
    found, evidence['check_actuators_sha256'] = actuators_unchanged(); issues.extend(found)
    return dict(ok=not issues, issues=issues, notes=notes, evidence=evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('board', nargs='?', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--print-hashes', action='store_true', help='print every rigid group digest and exit')
    args = parser.parse_args()
    board_path = args.board.resolve()
    if args.print_hashes:
        for name, items in rigid_groups(pcbnew.LoadBoard(str(board_path))).items():
            print(f"    '{name}': '{digest(items)}',   # {len(items)} items")
        return 0

    def inputs():
        result = input_hashes(board_path)
        for path in (board_path.with_suffix('.kicad_dru'), board_path.with_suffix('.kicad_pro'), PIN_TABLE):
            result[path.name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        return result
    before = inputs()
    report = check_board(pcbnew.LoadBoard(str(board_path)), board_path.parent, board_path)
    if before != inputs():
        report['issues'].append('board, model, rules or pin table changed during check'); report['ok'] = False
    report.update(board_sha256=before[board_path.name], inputs_sha256=before,
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  r7_checker_sha256=hashlib.sha256(Path(r7.__file__).read_bytes()).hexdigest())
    for note in report['notes']:
        print('NOTE', note)
    for issue in report['issues']:
        print('FAIL', issue)
    print('R8 CAD contract:', 'OK' if report['ok'] else f"FAIL ({len(report['issues'])} findings)")
    if args.report:
        args.report.write_text(json.dumps(report, indent=2, default=str) + '\n')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
