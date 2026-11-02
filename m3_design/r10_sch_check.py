#!/usr/bin/env python3
"""Check the R10 schematic against the R9 source and explicit circuit contract.

Usage: python3 -B m3_design/r10_sch_check.py --project DIR [--json FILE]
Checks every pin and fitted component, retained functional safety, camera isolation,
strict ERC, a fresh netlist export and deterministic sheet regeneration. Seeded
contract mutations run in memory and never modify the checked project.
This is a schematic gate; it makes no routing, thermal or bench qualification claim.
"""
import argparse
import copy
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r10_sch as gen


def read_netlist(path):
    root = ET.parse(path).getroot()
    parts = {c.get('ref'): c for c in root.findall('./components/comp')}
    pins = {(p.get('ref'), p.get('pin')): None if n.get('name').startswith('unconnected-') else n.get('name')
            for n in root.findall('./nets/net') for p in n.findall('node')}
    return parts, pins


def assembly_groups(parts):
    """Match export_fab's BOM grouping before routing/export: one footprint and MPN per LCSC code.
    Owner-fitted DNP and JLC parts are separate BOMs; excluded placeholders do not enter either group."""
    groups, issues = {}, []
    for ref, part in parts.items():
        flags = {p.get('name') for p in part.findall('property')}
        if not ref or ref.startswith('#') or 'exclude_from_bom' in flags:
            continue
        fields = {f.get('name'): f.text or '' for f in part.findall('./fields/field')}
        code = fields.get('LCSC', '')
        if code:
            key = ('owner' if 'dnp' in flags else 'JLC', code)
            groups.setdefault(key, []).append((ref, (part.findtext('footprint') or '').split(':')[-1],
                                               fields.get('Manufacturer Part', '')))
    for (bom, code), members in sorted(groups.items()):
        fps, mpns = {m[1] for m in members}, {m[2] for m in members}
        if len(fps) > 1 or len(mpns) > 1:
            issues.append(f'BOM contract: LCSC {code} on several footprints {sorted(fps)} or part numbers '
                          f'{sorted(mpns)} ({",".join(sorted(m[0] for m in members))}; {bom} BOM)')
    return issues


def expected():
    parts, pins = gen.baseline()
    data = gen.circuit()
    for ref in data['removed_refs']:
        parts.pop(ref, None)  # AUD-8 also lists obsolete R10-only parts absent from the archived R9 baseline.
        pins = {key: value for key, value in pins.items() if key[0] != ref}
    for ref, spec in {**data['parts'], **data['replacements']}.items():
        parts[ref] = spec
        pins = {key: value for key, value in pins.items() if key[0] != ref}
        pins.update({(ref, pin): net for pin, net in spec['nets'].items()})
    for ref, value in data['value_overrides'].items():
        parts[ref].find('value').text = value
    with (gen.SOURCE / 'pin_table.tsv').open() as table:
        for row in csv.DictReader(table, delimiter='\t'):
            pins['U1', row['pin']] = None if row['r10_net'] == 'NC' else row['r10_net']
    return parts, pins


def contract(actual_parts, actual_pins):
    want_parts, want_pins = expected()
    issues = assembly_groups(actual_parts)
    removed = {'J123', 'R160', 'R161', 'C160', 'D122', 'TP84', 'TP85', 'TP86', 'TP87', 'TP89', 'TP92',
               'U412', 'U422', 'R443', 'R453', 'C441', 'C442', 'C451', 'C452',
               'U410', 'U420', 'U411', 'U421', 'R410', 'R411', 'R412', 'R420', 'R421', 'R422',
               'R442', 'R452', 'C440', 'C443', 'C450', 'C453', 'R177', 'R124', 'R125', 'R182', 'R172', 'C122', 'R168', 'R170'}
    if removed & actual_parts.keys():
        issues.append(f'AUD-4 / AUD-5 / AUD-8: obsolete parts remain: {sorted(removed & actual_parts.keys())}')
    if 'J124' in actual_parts:
        issues.append('single screw switch: obsolete J124 ARM terminal remains')
    if 'PYRO1_BUS' in actual_pins.values():
        issues.append('single screw switch: PYRO1_BUS must be merged into RAW_ACT')
    if any(str(net).startswith('RAW_ACT_SENSE') for net in actual_pins.values()):
        issues.append('AVA: ARM1_SENSE is the sole RAW_ACT bus divider; duplicate RAW_ACT_SENSE remains')
    safety_pins = {('R134', '2'): 'RAW_ACT', ('R132', '1'): 'RAW_ACT', ('U1', '16'): 'ACT_EN_MCU',
                   ('R122', '1'): 'ACT_EN_MCU', ('R122', '2'): 'ACT_EN', ('R123', '1'): 'ACT_EN',
                   ('R123', '2'): 'GND', ('Q122', '1'): 'ACT_EN', ('Q122', '2'): 'GND'}
    for key, net in safety_pins.items():
        if actual_pins.get(key) != net:
            issues.append(f'single screw switch: {key[0]}.{key[1]} must be {net}')
    # D-R19-14: three electrically identical always-on ports (J410 GPS, J420 radio, J440 AUX spare by default).
    interface_pins = {('J410', '1'): 'PORT_4V8', ('J420', '1'): 'PORT_4V8', ('J440', '1'): 'PORT_4V8',
                      ('R440', '2'): 'GPS_RX_MCU', ('R441', '1'): 'GPS_TX_MCU',
                      ('R450', '2'): 'RADIO_RX_MCU', ('R451', '1'): 'RADIO_TX_MCU',
                      ('R470', '2'): 'AUX_RX_MCU', ('R471', '1'): 'AUX_TX_MCU',
                      ('U1', '55'): 'GPS_TX_MCU', ('U1', '56'): 'GPS_RX_MCU',
                      ('U1', '63'): 'AUX_TX_MCU', ('U1', '64'): 'AUX_RX_MCU',
                      ('U1', '33'): 'ARM1_SENSE', ('U1', '34'): None,
                      ('U1', '78'): 'SD_SCK', ('U1', '79'): 'SD_MISO',
                      ('U1', '80'): 'SD_MOSI', ('U1', '81'): 'SD_CS'}
    for key, net in interface_pins.items():
        if actual_pins.get(key) != net:
            issues.append(f'AVA port / SD contract: {key[0]}.{key[1]} must be {net}')
    if set(actual_parts) != set(want_parts):
        issues.append(f'component set: missing {sorted(set(want_parts)-set(actual_parts))}; extra {sorted(set(actual_parts)-set(want_parts))}')
    for key in sorted(set(want_pins) | set(actual_pins)):
        if key not in actual_pins or key not in want_pins or actual_pins.get(key) != want_pins.get(key):
            issues.append(f'{key[0]}.{key[1]}: {actual_pins.get(key)!r}, expected {want_pins.get(key)!r}')
    for ref in sorted(set(want_parts) & set(actual_parts)):
        a, want = actual_parts[ref], want_parts[ref]
        spec = gen.specification(want, {}) if isinstance(want, ET.Element) else want
        for key in ('value', 'footprint'):
            if a.findtext(key) != spec[key]:
                issues.append(f'{ref}: {key} differs')
        if 'M3:' + a.find('libsource').get('part') != spec['lib']:
            issues.append(f'{ref}: symbol differs')
        fields = {f.get('name'): f.text or '' for f in a.findall('./fields/field')}
        for key in ('LCSC', 'Manufacturer', 'Manufacturer Part'):
            if fields.get(key, '') != spec['fields'].get(key, ''):
                issues.append(f'{ref}: {key} differs')
        # All fitted R10 circuit parts and all retained safety parts must actually
        # reach assembly output. Compare the baseline DNP status for any survivor.
        props = {p.get('name') for p in a.findall('property')}
        expected_props = {p.get('name') for p in want.findall('property')} if isinstance(want, ET.Element) else set()
        for flag in ('dnp', 'exclude_from_bom', 'exclude_from_pos_files', 'exclude_from_board'):
            if (flag in props) != (flag in expected_props):
                issues.append(f'{ref}: changed assembly flag {flag}')
    return issues


def seeds(parts, pins):
    results = {}
    mutations = {
        'C92 split assembly footprint': lambda p, n: setattr(p['C92'].find('footprint'), 'text', 'rocket:C_0603_1608Metric'),
        'C120 split assembly footprint': lambda p, n: setattr(p['C120'].find('footprint'), 'text', 'rocket:C0603'),
        'AUD-4 pull-pin restored': lambda p, n: p.update({'J123': gen.baseline()[0]['J123']}),
        'AUD-4 pull-pin MCU net restored': lambda p, n: n.update({('U1', '7'): 'PULLPIN'}),
        'AUD-5 removed test pad restored': lambda p, n: p.update({'TP92': gen.baseline()[0]['TP84']}),
        'AVA obsolete GPS translator restored': lambda p, n: p.update({'U411': copy.deepcopy(p['U12'])}),
        'AVA obsolete radio switch restored': lambda p, n: p.update({'U420': copy.deepcopy(p['U402'])}),
        'AVA duplicate bus divider restored': lambda p, n: p.update({'R124': gen.baseline()[0]['R124']}),
        'audit2 CONT pin resistor restored': lambda p, n: p.update({'R168': gen.baseline()[0]['R168']}),
        'audit2 bus ADC tail restored': lambda p, n: n.update({('U1', '33'): 'ARM1_SENSE_MCU'}),
        'AVA duplicate bus ADC restored': lambda p, n: n.update({('U1', '34'): 'RAW_ACT_SENSE_MCU'}),
        'obsolete ARM terminal restored': lambda p, n: p.update({'J124': gen.baseline()[0]['J124']}),
        'obsolete separate pyro bus': lambda p, n: n.update({('R134', '2'): 'PYRO1_BUS'}),
        'pyro feed directly from pack': lambda p, n: n.update({('R134', '2'): 'BAT_IN'}),
        'bus sense directly from pack': lambda p, n: n.update({('R132', '1'): 'BAT_IN'}),
        'load switch follows logic rail': lambda p, n: n.update({('R122', '1'): 'RAW_PROTECTED'}),
        'load switch enable pull-down missing': lambda p, n: p.pop('R123'),
        'independent load switch MCU pin missing': lambda p, n: n.update({('U1', '16'): None}),
        'servo signal terminal powered': lambda p, n: n.update({('J122', '2'): 'RAW_ACT'}),
        'radio USB injection bypass': lambda p, n: n.update({('U1', '51'): 'RADIO_RX_WIRE'}),
        'GPS always-on feed split': lambda p, n: n.update({('J410', '1'): 'GPS_4V8'}),
        'radio TX series bypass': lambda p, n: n.update({('U1', '52'): 'RADIO_TX_WIRE'}),
        'AUX always-on feed split': lambda p, n: n.update({('J440', '1'): 'AUX_4V8'}),
        'AUX TX series bypass': lambda p, n: n.update({('U1', '63'): 'AUX_TX_WIRE'}),
        'AUX port ESD clamp removed': lambda p, n: p.pop('D441'),
        # D-R24-11: J400.2's contact clamp is required, and its second pad is GND only
        'J400 contact clamp removed': lambda p, n: p.pop('D402'),
        'J400 contact clamp return off GND': lambda p, n: n.update({('D402', '2'): 'BAT_ENABLE'}),
        'retained camera isolation removed': lambda p, n: p.pop('U12'),
        'retained camera switch removed': lambda p, n: p.pop('U402'),
        'pyro load switch removed': lambda p, n: p.pop('Q120'),
        'pyro gate capacitor excluded': lambda p, n: ET.SubElement(p['C126'], 'property', name='exclude_from_bom'),
        'shorted igniter limiter DNP': lambda p, n: ET.SubElement(p['R134'], 'property', name='dnp'),
        'microSD socket removed': lambda p, n: p.pop('J430'),
        'microSD CS reset pullup removed': lambda p, n: p.pop('R460'),
        'microSD MOSI MISO swapped': lambda p, n: n.update({('J430', '3'): 'SD_MISO', ('J430', '7'): 'SD_MOSI'}),
        'microSD shield floating': lambda p, n: n.update({('J430', '9'): None}),
        'microSD supplied by port LDO': lambda p, n: n.update({('J430', '4'): 'PORT_4V8'}),
        'microSD unused DAT2 floating': lambda p, n: p.pop('R464'),
        'QSPI primary logger removed': lambda p, n: p.pop('U3'),
    }
    for label, mutate in mutations.items():
        p, n = copy.deepcopy(parts), dict(pins)
        mutate(p, n)
        results[label] = bool(contract(p, n))
    return results


def check(project):
    gen.source_check()
    parts, pins = read_netlist(project / 'schematic.net.xml')
    issues = contract(parts, pins)
    seeded = seeds(parts, pins)
    issues += [f'seed survived: {name}' for name, caught in seeded.items() if not caught]
    if (project / 'm3.kicad_dru').read_text() != gen.dru((gen.BASE / 'm3.kicad_dru').read_text()):
        issues.append('DRU differs from authorized default-clearance transform')
    cli = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
    with tempfile.TemporaryDirectory(prefix='r10-sch-check-') as directory:
        work = Path(directory)
        erc = work / 'erc.json'
        subprocess.run([cli, 'sch', 'erc', '--severity-all', '--format', 'json', '-o', str(erc),
                        str(project / 'm3.kicad_sch')], check=True, capture_output=True, text=True)
        erc_data = json.loads(erc.read_text())
        violations = [v for sheet in erc_data['sheets'] for v in sheet['violations']]
        issues += [f'ERC {v["type"]}: {v.get("description", "")}' for v in violations]
        replay = work / 'replay'
        gen.build(replay)
        # Freshly regenerate both the stored netlist and sheets from fixed input.
        for file in sorted(replay.glob('*.kicad_sch')) + [replay / 'schematic.net.xml', replay / 'm3.kicad_dru']:
            if file.read_bytes() != (project / file.name).read_bytes():
                issues.append(f'nonreproducible generated artifact: {file.name}')
        # Export the supplied sheets themselves too, detecting a changed sheet
        # paired with a stale but otherwise valid netlist.
        fresh = work / 'fresh'
        fresh.mkdir()
        for file in project.glob('*.kicad_sch'):
            shutil.copy2(file, fresh / file.name)
        gen.sch.export_netlist(fresh)
        p2, n2 = read_netlist(fresh / 'schematic.net.xml')
        issues += ['fresh schematic export: ' + issue for issue in contract(p2, n2)]
    return {'ok': not issues, 'issues': issues, 'components': len(parts), 'pins': len(pins),
            'erc_violations': len(violations), 'seeded_faults': seeded,
            'netlist_sha256': hashlib.sha256((project / 'schematic.net.xml').read_bytes()).hexdigest(),
            'scope': 'schematic, parts, exact pin nets and default-clearance DRU; no PCB/physical qualification'}


def binding_note(project, board=None):
    """Evidence record for a future firmware binding, never a hash-only approval."""
    with (gen.SOURCE / 'pin_table.tsv').open() as table:
        rows = list(csv.DictReader(table, delimiter='\t'))
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    note = {
        'profile': 'M3-ASSY-R10',
        'status': 'record only; R1 binding invalid; no R10 firmware or flight approval',
        'board_sha256': None,
        'netlist_sha256': sha(project / 'schematic.net.xml'),
        'pin_table_sha256': sha(gen.SOURCE / 'pin_table.tsv'),
        'circuit_sha256': sha(gen.SOURCE / 'circuit.json'),
        'u1_pins': {r['pin']: {'port': r['port'], 'net': r['r10_net'], 'mode': r['mode_af']} for r in rows},
        'u1_board_map_checked': False,
        'imu': {'status': 'pending final PCB orientation and lever-arm measurement'},
        'sources': {
            'mcu': 'https://www.st.com/resource/en/datasheet/stm32h743vi.pdf',
            'mcu_revision': ('every DS12110 citation in this note is Rev 8 (April 2021), revision V electrical chapter (section 7; '
                             'the LCSC copy is byte-identical); Rev 11 and RM0433 were not re-read in round 19 (R19-MCU-02)'),
            'imu': 'https://www.st.com/resource/en/datasheet/ism6hg256x.pdf',
            'imu_alternate': 'https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf',
            'source_selector': 'https://www.ti.com/lit/ds/symlink/tps2121.pdf',
            'mcu_reference': 'https://www.st.com/resource/en/reference_manual/rm0433-stm32h742-stm32h743753-and-stm32h750-value-line-advanced-armbased-32bit-mcus-stmicroelectronics.pdf',
            'mcu_cmsis': 'https://raw.githubusercontent.com/STMicroelectronics/cmsis-device-h7/master/Include/stm32h743xx.h',
            'translator': 'https://www.ti.com/lit/ds/symlink/txu0202.pdf',
            'switch': 'https://www.ti.com/lit/ds/symlink/tps2553.pdf',
            'microsd_socket': 'https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf',
            'sd_physical_layer': 'https://www.sdcard.org/downloads/pls/'},
        'port_states': {
            'reset_boot': 'GPS/radio/AUX ports (J410/J420/J440, electrically identical, D-R19-14) powered directly by PORT_4V8 whenever the battery path is on (off on USB-only power); their UARTs reach FT digital MCU pins through 1 kohm and a ground-only ESD clamp. Keep direct UART RX internal pulls disabled throughout operation; the FT operating pull-off condition is the relevant I/O supply + 0.3 V. Camera EN100k/OE10k pulldowns retain power/isolation default-off.',
            'off_external_uart_active': 'GPS/radio/AUX ports have no powered-off isolation. An externally powered module can inject through the kept 1 kohm into an unpowered MCU; no self-powered GPS/radio with the board off. The SD card remains on main3V3, with CS held high by R460 (10 kohm) at reset.',
            'startup': 'Port UART TX (J410 PD8 USART3, J420 PB13 UART5, J440 PC6 USART6): select the TX alternate function (idle high) only while PA4 LOGIC_SOURCE_ST reads low after a settling delay (U11 ST low = IN2 = RAW_PROTECTED, the battery path that powers PORT_4V8; ST high = IN1 = USB or no valid input; TI SLVSEA3F Table 9-3 p. 18, p. 21); while PA4 reads high the modules may be unpowered (USB-only), so PD8 / PB13 / PC6 stay in analog mode, no pull (R19-MCU-01). Camera: EN high, verified rail settling, RX pull-up and TX idle-high, then OE high. SD_CS high before SPI3 AF6 configuration.',
            'shutdown_shedding': 'GPS/radio/AUX port supply cannot be switched or power-cycled by firmware. When PA4 rises or the PA6 VLOGIC watchdog trips, park PD8 / PB13 / PC6 in analog mode, no pull (R19-MCU-01). Stop UARTs and SD/QSPI writes, disable camera OE then EN, lower MCU clock, extinguish LEDs/buzzer. Faulted cards must not block safety/flight tasks.',
            'port_device_backfeed': ('Always-on GPS/radio/AUX port power pins directly back-feed PORT_4V8; U401/U400 can then feed RAW_PROTECTED/VLOGIC (Inference). '
                                     'The retained camera TPS2553 blocks reverse current when disabled, but an enabled part trips only beyond95-190mV after3-7ms '
                                     '(TI SLVS841G section6.5p7); UART isolation does not qualify its power pin. '
                                     'J400 has no state sensor, so back-feed can hide switch opening. Connect the e-match only with no USB/self-powered port source attached; '
                                     'bench USB with pack disconnected or e-match disconnected. No firmware mitigation replaces this restriction.')},
        'arming_policy': {
            'decision': 'owner single screw switch, 2026-10-28; J124 and its ARM-link fuse removed',
            'hardware': 'J400 is the pad power/arming device, connected to U9 EN with no switch-state sensor. Q120/Q121 feed RAW_ACT directly to R134 and R132. PC1 independently enables Q122 through R122; PE4 separately drives Q124. Both MCU controls default off in reset.',
            'pad': 'Turn the screw switch on last and off first, only with the vehicle on the pad / rail. GPS, telemetry and IMU pad checks occur on the rail.',
            'bench': 'Use USB with the pack disconnected, or disconnect the e-match. Connect the e-match only with no USB or self-powered port back-feed source attached.',
            'limits': 'No physical ARM break while powered; a back-feed source can keep logic powered with J400 open. Continuity and ARM1_SENSE measure the firing return and RAW_ACT bus, not a separate ARM-link state.'},
        'fire_timing': {
            'basis': 'GAP-5; DS12110 Rev 8 Table 146 p. 238: LSI 29.4-33.6 kHz at TJ -40 to 125 C; firmware obligations, not implemented',
            'watchdog': {'prescaler_divisor': 4, 'PR_register': 0, 'RLR': 239, 'LSI_cycles': 960, 'nominal_ms': 30.,
                         'minimum_ms': 960 / 33.6, 'maximum_ms': 960 / 29.4},
            'normal_physical_current_max_ms': 20., 'fault_physical_current_max_ms': 36.,
            'prefire_sync_max_ms': .2, 'reset_HiZ_max_ms': .5, 'actual_gate_current_tail_max_ms': 1.5,
            'postfire_safety_pass_and_refeed_max_ms': 5.,
            'refresh_contract': 'No IWDG refresh from prefire through firing until physical firing current has ended (including tail); then require the SAFETY pass and refeed within 5ms. A failed safety task never refreshes.'},
        'firmware_obligations': [
            'Build a new reviewed binding through the assembly_binding design process; never substitute a board hash into the R1 chain.',
            'Port UARTs (D-R19-14): J410 USART3 PD8 TX/PD9 RX AF7 (DS12110 Rev 8 Table 13 p. 94), J420 UART5 PB13 TX/PB12 RX AF14 (Rev 8 Table 11 p. 91), J440 USART6 PC6 TX/PC7 RX AF7 (Rev 8 Table 12 p. 92); the same cites as pin_table.tsv rows 55-56, 51-52 and 63-64.',
            'Configurable port map (D-R19-14, owner 2026-10-30): J410, J420 and J440 are electrically identical (pin 1 PORT_4V8, 2 GND, 3 board TXO, 4 board RXI; 1 kohm series, ground-only ESD clamp, 100 nF + 22 uF local supply), so the GPS and the radio may each be wired to any of the three. Firmware maps each device to a port UART (baud, protocol and receive handling follow the device, not the port); default GPS J410 (USART3), radio J420 (UART5), J440 AUX spare (USART6). The camera port J9 is not part of the set (5.4 V supply, reversed TX/RX order, isolated UART). The three ports share PORT_4V8: the spare port (AUX by default) may draw up to 100 mA at 4.8 V beyond the GPS 150 mA and radio 300 mA allocations (U401 thermal floor, parts_budget.json). A port with no mapped device keeps its USART disabled and both pins in analog mode, no pull, so an open RX never floats as a digital input (R20-MCU-03).',
            'Camera UART7 PE8 TX/PE7 RX AF7 without flow control. UART5/USART6 and USART3 on PD8/PD9 are separate from the loader USART interfaces (AN2606 Rev64 Table119 pp277-280: no UART5, PB12 or PB13; the loader USART3 is PB10/PB11 only).',
            'Re-mapped loader pins (AN2606 Rev64 Table119 pp279-280; pin_table an2606_t119_loader_role): PA4 / PA5 / PA6 are SPI1 NSS / SCK / MISO and PE11 / PE12 SPI4 NSS / SCK. In the ROM loader PA6 is driven push-pull into the VLOGIC_SENSE divider only (<= 0.36 mA) and PE11 is an input that R431 holds low (camera port off); before a loader jump drive camera EN/OE low, PC1/PE4 low and SD_CS high. PC11 is loader SPI3_MISO output; R460 keeps the card deselected.',
            'Always-on GPS/radio/AUX ports have no FAULT/EN/OE GPIOs; PD10/PD14/PD15/PE15 are NC/analog. EXTI12 CAM_FAULT_N (PE12); EXTI4 LOGIC_SOURCE_ST (PA4) and EXTI5 BAT_FAULT_N (PA5), swapped for routing (D-R2-09); EXTI6 USB_FAULT_N (PD6), EXTI8 VBUS_SENSE (PC8). AUD-4 removes PULLPIN; PC13 is NC. One port per EXTI line; lines5/6/8 share EXTI9_5 and line12 uses EXTI15_10, so each handler checks its pending bit. PE1 IMU_INT1 is on EXTI1 (free on R10; R6-MCU-01): configure PE1 as an input with the internal pull-down and take the roll-loop data-ready interrupt on it; U4 INT1 is push-pull and active high by default (IF_CFG PP_OD = 0, H_LACTIVE = 0 on the fitted ISM6HG256X and the alternate LSM6DSV320X: DS15034 / DS14623 Rev 1 p. 60), so no pull-up is wanted. EXTI1 has its own vector.',
            'PE4 (U1.3, net PYRO1_GATE_N; the _N is historical) is the ACTIVE-HIGH fire command: PE4 high turns Q124 on. Write its output data low before output mode and keep it low except during a permitted fire (R18-MCU-03). R123 2k (R18-MCU-01) and R127 1k hold Q122 / Q124 off against a 30-50 kOhm internal pull-up; never enable a PC1 or PE4 pull-up, and never route RTC_TAMP3 or WKUP5 to PC1. PC1 ACT_EN_MCU and PE4 pyro gate low before GPIO configuration, port shutdown, ROM-loader entry or reset. PC1 is the independent Q120/Q121 enable through R122, not a sentinel. Keep sentinel pins PE3/PE5/PE6/PC4 without nets and in analog mode (their reset state), never driven: every no-net pin, the sentinels included, stays analog (R5-MCU-03). PA15 is the one no-net pin whose reset state is NOT analog (R7-MCU-01): it resets to JTDI with the internal pull-up (STM32H743 debug-pin reset state, DS12110 / RM0433 as the reviewer read it, not re-read here: Inference), so set PA15 to analog mode with no pull explicitly at start-up; "reset state" wording applies only to the other no-net pins.',
            'GAP-5: keep the independent safety task and IWDG divide-by-4 (PR register 0) / RLR 239 (960 LSI cycles): 30ms nominal, 28.571-32.653ms at LSI 33.6-29.4kHz (DS12110 Rev 8 Table 146 p. 238, TJ -40 to 125 C). Never refresh from prefire through firing until physical firing current has ended (including tail); require the postfire SAFETY pass and refeed within 5ms. Limit NORMAL PHYSICAL igniter current, including the actual gate-discharge tail, to 20ms; a 20ms GPIO-high command alone is insufficient. Worst-fault physical current is bounded by 32.653ms watchdog +0.2ms prefire/synchronization +0.5ms reset HiZ +1.5ms actual gate-current tail =34.853ms, within the 36ms contract. These are firmware and bench obligations, not implemented. Never fire before launch is detected using accelerometer and barometer. On the ground continuity / bus readings are hard refusals; in flight they are logged and annunciated and never veto a fire. The screw switch is the pad arming device; no separate ARM plug or ARM-link state exists.',
            'F6 / FMEA F-1: the first SERVO1-4 output after reset is neutral 1520us, with a command within 50ms. GAP-5 uses the 960-LSI-cycle IWDG period specified above; only the SAFETY task may refresh it, subject to the no-refresh firing interval. A ROM-loader jump is allowed only before IWDG starts: it cannot be stopped afterward; keep both firing controls low.',
            'D-SS-04 / AUD-3: hold BOTH PC1 ACT_EN_MCU and PE4 low for passive cold screening. After a prior load-switch enable, wait at least 1s and verify RAW_ACT discharged / ACT_GATE off before classifying readings. Bench-qualify passive low/healthy/open bands, leakage and unexpected powered-bus readings using parts_qualification.md; any ground fault is a hard refusal BEFORE PC1 enable, especially a failed-short Q124. Only after a valid passive check may PC1 go high, with PE4 still low for at least 100ms before powered-bus checks or any permitted fire. This settling wait is not the no-refresh firing interval; in-flight sense readings never veto fire.',
            'J122 DB1255pos pins1-4SERVO1-4_OUT,pin5GND signal reference; servo positive and motor return direct to pack. Board cannot cut servo power; qualify neutral-on-reset and measured shared return. J400 DB1252pos is power/arming switch; J9/J410/J420/J440 DB1254pos unkeyed, explicit per-pin power/GND/UART legends and end-to-end harness check; clamps28-16AWG with qualified ferrules/splices for thinner module leads.',
            'Maximum normal-flight MCU clock200MHz for the retained-load budget. Firmware not implemented.',
            'F6 battery-break response (always-on port owner decision2026-10-28): C84 plus firmware shedding, no hardware U400 cutoff and no GPS/radio switches. Use PA6 ADC12_INP3 watchdog on ADC1/2. Ports-on ride-through includes the always-on GPS/radio, the 100 mA AUX allowance and the card allocation; no software power cutoff can be credited. Bench-verify detection latency, selected-card current, camera current decay and retained load. Loaded battery-break continuity is not guaranteed.',
            'On shedding stop SD and QSPI writes immediately without a blocking flush, stop UARTs, lower camera OE then EN, lower MCU clock, extinguish LEDs/buzzer; retain IMU/barometer/flight state and safety. The SD card may stay busy and powered after host clocks stop; budget its<=200mA write allocation until its actual current falls. No in-flight wait for filesystem/card completion.',
            'Camera TPS2553 FAULT deglitch is3-11ms, turn-off up to3ms (TI SLVS841G p7). FAULT is not battery-break detection. GPS/radio/AUX ports rely on shared LDO/buck current and thermal limits; a short can remove all three port loads, with no independent fault flag or firmware recovery power-cycle.',
            'On VLOGIC undervoltage/shutdown drop camera EN/OE and park PD8 / PB13 / PC6 in analog mode, no pull; the GPS/radio/AUX ports stay powered whenever the battery path is on (firmware cannot switch them; off on USB-only power). J400 has no state sensor; retain the no-self-powered-port/e-match restriction. Direct port UARTs are FT digital inputs only, RX pulls always disabled; a device on J410 / J420 / J440 must drive its TX high at no more than 3.6 V, because PORT_4V8 rises about 44 ms or more before 3V3 (U11 C85 slew, TI SLVSEA3F Table 9-1 p. 13, Calculation) and an FT pin allows only 4.0 V while VDD = 0 (DS12110 Rev 8 Table 119 p. 212; R20-MCU-02). ST DS12110 Rev 8 Table 122 note 3 p. 215 / Table 157 note 7 p. 247 requires pulls off above Min(VDD, VDDA, VDD33USB) + 0.3 V in operation; Table 119 note 4 p. 213 gives a separate 4 V absolute-stress condition. No powered-off isolation or positive injected current allowance.',
            'PC14 drives the buzzer gate through R162 1 kOhm: VBAT-domain PC13/PC14/PC15 are characterised at +/-3 mA only (DS12110 Rev 8 Table 159 p. 249); GPIO speed low (2 MHz limit, Rev 8 Table 160 note 2 p. 251), as pin_table.tsv row 8.',
            'Switch-chatter immunity is hardware only (C87 220 nF, R19-REQ-02 / D-R19-10 / D-R20-11 / D-R24-19): J400 drop-outs shorter than 10.3/20.1/26.0 ms worst case (19/33/41 ms nominal) at 6.0/7.4/8.4 V, and about 8.2 ms at the fire budget four-stall BAT_IN of 5.73 V, cannot trip U9 (Calculation, R20-SAF-04 / R24-TRI-02: 297 kOhm x 0.72 x 220 nF from EN 1.401 V at 6.0 V (1 % divider, 0.1 uA EN leakage out of the node and D402\'s 50 nA at J400.2) falling to 1.116 V with the same leakages on R81, D402\'s through R165; TPS25947 SLVSFC9C p. 9 EN thresholds and leakage, Infineon ESD103 Rev 1.3 leakage). The REQUIREMENTS F6 bench acceptance of a longest measured drop-out < 10 ms holds only with the loaded pack at or above 5.96 V (6.3 ms at 5.5 V); re-size C87 (BOM only, same land) if the bench drop-out exceeds these; keep it separate from battery-lead-break ride-through. A longer drop-out reboots the board after a 30-130 ms EN turn-on delay. Resume flight state from live evidence after reset.',
            'Radio uplink cannot arm or fire; LR900-F band is 890-915 MHz: use manual channels 12-25 (902-915 MHz) or a maker-confirmed FHSS set inside 902-928 MHz; qualify installed maximum-power radio/GPS immunity.',
            'PC14 buzzer GPIO-toggled; PC13, PE10 and PE0 remain NC (AUD-4 removes the pull-pin). Audit2: PC0 PYRO1_CONT and PC5 ARM1_SENSE directly read their retained split dividers and10nF filters, withoutR168/R170 tails; duplicate bus bank/PB0 removed. Sensor functions unchanged.',
            'UART start-up: camera retains U12 isolation and OE pull-down; before camera OE goes high, RX PE7 pull-up and TX PE8 idle-high. The three port UARTs connect directly through 1 kohm; PD9/PB12/PC7 are digital AF inputs with internal pulls always disabled; PD8/PB13/PC6 take their TX alternate function (idle high) only while PA4 LOGIC_SOURCE_ST reads low after a settling delay (U11 ST low = IN2 = RAW_PROTECTED, the battery path that powers PORT_4V8; ST high = IN1 = USB or no valid input; TI SLVSEA3F Table 9-3 p. 18, p. 21), and return to analog mode, no pull when PA4 rises or the PA6 watchdog trips: on USB-only power the port modules are unpowered, so the MCU cannot back-feed a module through the 1 kohm (R19-MCU-01). Never connect a self-powered port module with the board off; measure endpoint TX levels.',
            'Per-sense ADC instances: PC0 PYRO1_CONT ADC123_INP10, PA6 VLOGIC_SENSE ADC12_INP3, PC5 ARM1_SENSE ADC12_INP8 (sole RAW_ACT bus reading), PB1 CAM_5V_SENSE ADC12_INP5. PB0 and PC3_C are NC/analog (R18-REQ-08 removes the V3V3_SENSE divider R62/R63: it read 3V3 against VREF+ = 3V3A from the same rail); read VDDA from VREFINT (VREFIN_CAL, DS12110 Rev 8 Tables 127-128 pp. 218-219) and 3V3 from the internal VBAT/4 bridge (VBAT tied to 3V3; Rev 8 Table 192 p. 293, ratio error +/-10%) on ADC3, as pin_table.tsv row 18. Delete duplicate RAW_ACT_SENSE readings and thresholds. Ground continuity and sole bus readings remain hard refusals; in flight neither vetoes fire. PA6 watchdog uses ADC1/2.',
            'microSD J430 locking hinge, no card-detect: SPI3 AF6 PC10 SCK/PC11 MISO/PC12 MOSI, PD0 software CS. CS high before GPIO/AF setup; >= 74 clocks with CS/MOSI high at 100-400 kHz, then CMD0; run at <= 25 MHz. The R460-R464 (10 kohm) pull-ups to 3V3 and the 3V3 bypass are physical. Select and bench-qualify a card with <= 200 mA write and <= 30 mA idle; keep locked during flight, insert/remove only off with board out.',
            'F5: nominal whole-flight storage spans retained QSPI plus secondary removable microSD, with adequate bounded buffering and at least25% measured throughput margin. No requirement that a whole flight fit16MB QSPI alone. A missing/faulted/full/slow card or corrupt filesystem never delays control, safety, watchdog or fire. Use nonblocking bounded transfers and preallocated files; drop secondary SD records only as fault/overload fallback, not the normal capacity plan. Power loss may corrupt the card; no blocking flush during F6 or firing.',
            'Audit2 item16: keep both LEDs dark from arming to landing until the installed opaque U5 cover passes LED-toggle/ambient-light checkout; the CAD cannot certify the cover.',
            'Selected MJG J-Tek LEAD-FREE maker all-fire0.75A times1.5 gives1.125A current criterion; the maker0.5s test does not certify20ms. Retain R1342ohm, normal physical20ms/fault36ms and qualify selected-lot20ms firing/source/harness/charge before flight.',
            'No-net U1 pins (R4-MCU-04): every U1 pin with no net stays in analog mode (the reset state) and is never configured as an output; the K-loader no-net pins (pin_table an2606_t119_loader_role) are never outputs, so a ROM-loader drive or a stray configuration cannot reach copper.',
            'LSE (R5-MCU-02): keep RCC_BDCR.LSEON = 0 and never set up the backup domain for the LSE: PC14 is OSC32_IN and drives BUZZ_DRV through R162, and VBAT is tied to 3V3, so a stray LSEON persists across NRST.',
            'VBUS_SENSE (R5-MCU-05): PC8 = VBUS / 2 (R9 1 kOhm / R110 1 kOhm); at 4.4 V VBUS the node is 2.20 V, below VIH = 0.7 x VDD = 2.31 V, so VBUS detection needs VBUS >= 4.62 V at VDD 3.3 V. A low PC8 is not proof of no USB: never use it as the sole input to a safety decision.',
            'Audit2 direct PC0/PC5 filtered ADCs retain single-resistor protection; duplicate PB0 bank andR168/R170 tails are removed. Other unprotected sense faults (R5-MCU-04): PA6 VLOGIC_SENSE (shorted R60 puts VLOGIC on an FT_a pin; positive injection allowance 0 mA (DS12110 Rev 8 Table 120 note 3 p. 213). Rev 8 Table 119 pp. 212-213 (notes 3-4) gives the FT ceiling Min(VDD, VDDA, VDD33USB, VBAT) + 4.0 V with pulls disabled above 4 V and 4.0 V on TT pins; the 4.0 V ADC-mode maximum and the 6.0 V FT cap were read from Rev 11 Table 109 in round 14 and are kept as design limits (Inference: not in Rev 8, Rev 11 not re-read)) and PB1 CAM_5V_SENSE (open R105 puts CAM_5V on a TT_u pin through R104 10 kOhm, limit 4.0 V); single-fault pin-damage cases recorded in parts_qualification.md, no firmware mitigation.',
            'Trace (R6-MCU-03): never enable synchronous trace (PE2 TRACECLK, PC1 TRACED0, PE4 TRACED1) in any debug configuration: PC1 enables the load switch and PE4 is the pyro gate (PYRO1_GATE); trace would drive both firing controls. After PC1 and PE4 are configured as low outputs, lock PC1 with GPIOC_LCKR and PE4 with GPIOE_LCKR (the locks hold until the next reset), then read both registers back: bit 16 (LCKK) and the pin lock bit (PC1 bit 1, PE4 bit 4) must read 1, and the firmware refuses to arm otherwise (D-SS-02 / R7-MCU-02). A locked pin\'s output data can still be written, its configuration cannot: in a loader-jump sequence PC1 and PE4 stay locked low outputs, because GPIOC / GPIOE resets (RCC_AHB4RSTR) clear the locks and only R123 / R127 then hold the controls off. R10 locks PC1 and PE4: PE3 / PE5 / PE6 are analog sentinels, PE12 is the CAM_FAULT_N input and PE13 / PE14 are NC. Disconnect the e-match before connecting a trace-capable debugger session: whether the DBGMCU trace pin assignment overrides the GPIO configuration (and the lock) on the H743 is not checked (Inference; R7-SAF-03).',
            'UART break storm: camera retains the TXU0202 input pull-down and can report a continuous break if enabled while unplugged. Direct port UARTs (GPS/radio/AUX) can float/noise when unplugged. Receive by DMA/IDLE with bounded error handling; mask FE/NE/ORE per-frame storms and disable the affected UART after a bounded error threshold. Port modules cannot be isolated or power-cycled in software; camera OE may be lowered.',
            'Trace override bench step (R8-SAF-01 / R9-MCU-01): no e-match connected. Use a debugger-supported STM32H743 synchronous 4-bit ETM setup; RM0433 Rev8 pp3209/543 uses DBGMCU_CR at 0x5C001004 bit20 TRACECLKEN (CMSIS DBGMCU_CR_DBG_TRACECKEN), not TRACE_IOEN or TRACE_MODE. With QSPI idle, set PE2 AF0 TRACECLK; keep PC1 and PE4 locked low GPIO outputs, not trace alternate functions. Read back both GPIOC_LCKR and GPIOE_LCKR: LCKK bit16 plus PC1 bit1 / PE4 bit4 must remain set. Verify the debugger did not reset GPIOC/GPIOE or clear either lock. Observe a running PE2 trace clock before quiet PC1 / PE4 / TP122 counts as evidence; absent clock or lost lock invalidates the test. If either control toggles with valid clock/locks, enforce trace-clock disable and readback before arming and report it (override behavior remains Inference until measured).',
            'W25Q128JV (R6-MCU-04): set the QE bit in status register 2 before QSPI quad mode is used; no blocking flash erase in flight: pre-erase before flight or use erase-suspend, so that the GAP-5 28.571ms minimum IWDG period holds (W25Q128JV Rev I AC characteristics, read in round 7: 4 KB sector erase 45 ms typical / 400 ms maximum, 32 KB block 120 / 1,600 ms, 64 KB block 150 / 2,000 ms, erase-suspend latency tSUS 20 us). The pad ring buffer must be erased in erase-suspend slices or sized for a single pre-erase before arming; erase time is added to the F5 timing-margin statement. This is an open firmware design obligation (R7-MCU-04).',
            'IMU (R6-MCU-05, D-R19-11): U4 is fitted as the ISM6HG256X (JLC C51931514); the LSM6DSV320X is the second-fallback alternate (needs part fields, BOM and CPL regenerated: ORDERING 8.1) on the same land with the same pins and axis directions (DS15034 Rev 1 Figure 5 p. 9 and Table 2 pp. 10-11; DS14623 Rev 1 p. 9). WHO_AM_I reads 0x73 on both (p. 66), so it cannot identify the part. Their high-g full-scale codes differ (FS_XL_HG, Table 150 p. 93 of both: ISM6HG256X 100 = +/-256 g and 011 reserved; LSM6DSV320X 011 = +/-256 g and 100 = +/-320 g): use only 001 (+/-64 g) or 010 (+/-128 g), which mean the same on both and meet F2. IMU SPI clock <= 10 MHz (DS15034 p. 17); ignore gyro data for 40 ms after an IMU power-up (Ton, DS15034 p. 15).',
            'VREFBUF (R19-MCU-04): VREF+ (U1.20) is tied to VDDA (U1.21) on 3V3A (DS12110 Rev 8 Figure 95 p. 286). Keep VREFBUF_CSR at its reset value (ENVR = 0, HIZ = 1 per the ST SVD) and never write it: never enable the buffer (no HAL_SYSCFG_EnableVREFBUF) and never clear HIZ, since ENVR = 0 with HIZ = 0 pulls VREF+ to VSSA and would load 3V3A (VDDA, U4, U5) through R164 (RM0433 mode table as quoted on the ST community forum; Inference, R20-MCU-01). Scale ADC readings from VREFINT: an enabled buffer would drive its 1.5-2.5 V output (Table 189 p. 291, 4 mA static load) against 3V3A. Table 9 note 7 p. 88 requires the buffer kept disabled where VREF+ is tied to VDDA inside the package; applying it to this board-level tie is an Inference (RM0433 not re-read).',
            # D-R23-03: the root's round 23 firmware rules 1-13, in the wording M3_R10 'Firmware' uses
            "R23 firmware rule 1, launch (R23-SAFETY-07): the fire path needs LIFTOFF from the accelerometer AND a barometric altitude gain (LAUNCH_CORROBORATED), as AGENTS §2.1 requires. There is no inertial-only fire path on R10. With the barometer invalid, the primary channel does not fire and the independent Blue Jay covers recovery. FMEA F-6's accelerometer-only latch is not enough on R10.",
            'R23 firmware rule 2, cold screen after every power-up or reset (R23-SAFETY-09): wait at least 1 s, and verify that RAW_ACT has discharged and ACT_GATE is off, before classifying. This covers both U9 variants.',
            "R23 firmware rule 3, QSPI_IO2 / PE4 bridge (R23-SAFETY-08 (1); verified Minor by round23_safety_severity_check.md). Physics: Q124's gate capacitor is C126, 220 nF, not C128 (100 nF, on the drain); the gate time constant is 47–53 µs; a steady IO2-against-PE4 fight puts 1.19–1.98 V on the gate and fires the match after about 0.55 ms; page-program logging at a QSPI clock of 25 MHz or more stays at most 6 mA RMS, at least 50× below the 0.30 A no-fire; firing needs a sustained IO2-high pattern. Ground refusal: before PC1 goes high, run a QSPI quad read-verify of a known pattern, and refuse on any mismatch: the bridge corrupts quad reads. QSPI use while PC1 is high: PE2 stays in its QSPI alternate function, never a GPIO driven high; no memory-mapped or parked quad reads; no long all-ones writes at a low clock; the flash output drive is not at 100 %. Cold screen: during part of the passive cold screen, run sustained QSPI traffic and toggle PC14 and the servo PWM; refuse if CONT or BUS moves out of band. First article, before coating: inspect U1 pins 1–5 for bridges, and meter U3.3 (QSPI_IO2) to R127.1 (the PE4 gate network): it must read open.",
            "R23 firmware rule 4, bus voltage (R23-SAFETY-05): on the ground, after PC1 goes high and a 100 ms settle, the powered BUS must read at least 0.96 × the pack voltage derived from VLOGIC_SENSE, else refuse (this catches Q120 left off and the bus fed through its body diode). Qualify the band on first articles. Verified Minor: four stalls give 1.128 / 1.063 A (0.7 / 1.0 V drop), 0.93–1.01× the 1.125 A floor but at least 1.39× the maker's 0.75 A all-fire and at least 1.04× its 1.00 A recommended minimum. A first-order thermal model fires the match in 4–5 ms, inside the 20 ms pulse (Inference). At first article, probe ACT_GATE at R120.2 / C120.2 and record the dummy-load drop. Since D-R24-02 each gate drive has a second barrel (Q120 (16.2, 73.3) + (15.4, 72.85), Q121 (11.14, 71.7) + (11.74, 72.3)): leaving Q120 off this way takes two opens (D-R24-19).",
            'R23 firmware rule 5, PC1 source rule (R23-SAFETY-02 (4)): PC1 may go high only while PA4 reads low (U11 on the battery path, so U9 and J400 are on) and VBUS_SENSE does not contradict it. R91.1 and U1.28 each have a second via since D-R24-08 (no single point; the D-R22-02 entries are gone), and the rule stays an extra barrier, not a guarantee.',
            'R23 firmware rule 6, LANDED (R23-SAFETY-04, R23-REQUIREMENTS-06): use FMEA 7.4\'.9\'s criteria with a T_min floor. Then PE4 and PC1 go low and stay latched until power-off; PC1 never re-enables in the same power session. The IWDG keeps being serviced until power-off. The GPS and radio keep beaconing position: the ports are always on, so FMEA F-8\'s "GNSS off" does not apply to R10; park the GNSS UART instead if power must be shed. The locator tone sounds; logging stops or drops to 1 Hz.',
            "R23 firmware rule 7, PA5 (R23-POWER-04): PA5 low also means U9 is blocking reverse current (SLVSFC9C Table 7-3 p38). Treat it as a U9 fault only when it stays low longer than a qualified time with RAW_PROTECTED collapsed. Rate-limit EXTI5, and never reset or refuse readiness on one pulse. PA4 during U11's own reverse blocking is unstated (Inference): deglitch PA4 before re-enabling the port UARTs.",
            "R23 firmware rule 8, PA6 trip and hold-up (R23-POWER-01): the PA6 trip window is VLOGIC about 4.8–5.2 V (PA6 0.44–0.47 V): above U9's 4.80 V BAT_IN turn-off corner (D402's 50 nA included, D-R24-19; the PA6 lower edge 0.44 V x 11 = 4.84 V stays above it) and below the 5.37 V four-stall-plus-fire corner, to be qualified with the divider and ADC tolerances. Hold-up after the trip is 0.157–0.182 ms with all ports on and 0.44–0.48 ms with the camera off / shed (Calculation, from 5.3 V at 300.8 µF).",
            'R23 firmware rule 9, pad readiness. Pack (R23-REQUIREMENTS-07): firmware reads PA6, and PC5 after the cold screen. It telemeters the pack voltage and refuses the pad READY state below 7.4 V plus the measured PA6 divider error. Temperature (R23-MECHANICS-03): announce, and refuse arming-dependent checks, above an MS5611 TEMP of about 80 °C.',
            'R23 firmware rule 10, bring-up configuration (R23-MCU-01): program and read back these option bytes: BOOT_ADD0 = 0x0800, IWDG1_SW software start, BOR_LEV (state the level, DS12110 Table 126 p217), SWAP_BANK = 0, IO_HSLV = 0, and the RDP level. Also: LDO supply (never bypass), with VOS matched to 200 MHz (Table 122); HSEBYP = 0, a bounded HSE-ready wait, and CSSHSEON with HSI fallback and safety-timer rescaling (FMEA F-2); PLL limits per Table 147; USB VBUS sensing off with a B-session override (PA9 NC). The RM0433 items are an Inference until RM0433 is read.',
            'R23 firmware rule 11, bring-up facts (R23-DOCS_BINDING-03): U5 MS5611 on I2C1 PB8 / PB9 at 0x77 (PS high, CSB low), with R12 / R13 4.7 kΩ pull-ups. IMU_CS (PB7, R11) and QSPI_NCS (PB6, R10) idle high: write the ODR high before switching to output / AF. Scales: PA6 = VLOGIC / 11, PB1 = CAM_5V / 11, PC0 / PC5 = node / 11.2. The PA6 trip from rule 8, and a PA4 settling time to qualify on the bench.',
            'R23 firmware rule 12, clocks (R23-ROUTING-01): avoid SPI3, QSPI and timer clocks with an integer harmonic within ±1.023 MHz of 1575.42 MHz (25 and 75 MHz, for example). This is an Inference until the installed GNSS check has run.',
            "R23 firmware rule 13, IMU (R23-MCU-03): FS_XL_HG code 010 is 3.904 mg/LSB on all three parts and clips at ±80 g on the LSM6DSV80X, so 001 / 010 serve all three. Never use ST's ism6hg256x driver's 256 g enum (0x3 is reserved in DS15034 Table 150).",
        ],
        'physical_tests': 'not performed; see R10 validation and power qualification',
    }
    if board:
        import pcbnew
        pcb = pcbnew.LoadBoard(str(board))
        assert pcb.GetTitleBlock().GetRevision() == 'M3-ASSY-R10', 'not an R10 board'
        u1 = pcb.FindFootprintByReference('U1')
        actual = {p.GetNumber(): p.GetNetname() for p in u1.Pads()}
        assert set(actual) == {str(i) for i in range(1, 101)}, 'U1 must have100pins'
        for row in rows:
            net = actual[row['pin']]
            net = 'NC' if not net or net.startswith('unconnected-') else net
            assert net == row['r10_net'], f"U1.{row['pin']}: board pin differs"
        u4 = pcb.FindFootprintByReference('U4')
        pos = u4.GetPosition()
        rotation = u4.GetOrientationDegrees() % 360
        bottom = u4.IsFlipped()
        note['board_sha256'] = sha(board)
        note['u1_board_map_checked'] = True
        note['imu'] = {'x_mm': pcbnew.ToMM(pos.x), 'y_mm': pcbnew.ToMM(pos.y),
                       'rotation_deg': rotation, 'side': 'bottom' if bottom else 'top',
                       'lever_arm_x_mm': pcbnew.ToMM(pos.x) - 23.0,
                       'lever_arm_z_mm': -2.06, 'lever_arm_z_basis': 'Inference: centre of the U4 3D model box, not measured',
                       'lever_arm_frame': ('board frame: x east (+x toward the x = 46 edge), y forward, z up from the top face; lever_arm_x_mm and '
                                           'lever_arm_z_mm are the sensor position relative to the roll axis in that frame; in the IMU frame '
                                           '(+X_imu = -x, +Y_imu = -y, +Z_imu = -z) the lever arm is (+6.0, ., +2.06) mm'),
                       'bench_sign_check': 'required'}
        if bottom and abs(rotation - 180) < .001:
            note['imu'].update(axis_basis='same signed frame as R9: bottom180',
                               roll_about_forward_axis='-gyro_Y', forward_thrust='-a_Y')
        elif bottom and min(rotation, 360 - rotation) < .001:
            note['imu'].update(axis_basis='same signed frame as R8: bottom0',
                               roll_about_forward_axis='+gyro_Y', forward_thrust='+a_Y')
        else:
            note['imu']['axis_basis'] = 'new orientation: signed map must be derived and reviewed before firmware'
    return note


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--json', type=Path)
    parser.add_argument('--board', type=Path)
    parser.add_argument('--binding-note', type=Path)
    args = parser.parse_args()
    report = check(args.project.resolve())
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + '\n')
    if args.binding_note:
        assert report['ok'], 'binding note requires a passing schematic contract'
        args.binding_note.write_text(json.dumps(binding_note(args.project.resolve(), args.board), indent=2) + '\n')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['ok'] else 1)


if __name__ == '__main__':
    main()
