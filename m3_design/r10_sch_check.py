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
    interface_pins = {('J410', '1'): 'PORT_4V8', ('J420', '1'): 'PORT_4V8',
                      ('R440', '2'): 'GPS_RX_MCU', ('R441', '1'): 'GPS_TX_MCU',
                      ('R450', '2'): 'RADIO_RX_MCU', ('R451', '1'): 'RADIO_TX_MCU',
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
            'mcu_reference': 'https://www.st.com/resource/en/reference_manual/rm0433-stm32h742-stm32h743753-and-stm32h750-value-line-advanced-armbased-32bit-mcus-stmicroelectronics.pdf',
            'mcu_cmsis': 'https://raw.githubusercontent.com/STMicroelectronics/cmsis-device-h7/master/Include/stm32h743xx.h',
            'translator': 'https://www.ti.com/lit/ds/symlink/txu0202.pdf',
            'switch': 'https://www.ti.com/lit/ds/symlink/tps2553.pdf',
            'microsd_socket': 'https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf',
            'sd_physical_layer': 'https://www.sdcard.org/downloads/pls/'},
        'port_states': {
            'reset_boot': 'GPS/radio powered directly by PORT_4V8 whenever the battery path is on (off on USB-only power); their UARTs reach FT digital MCU pins through 1 kohm and a ground-only ESD clamp. Keep direct UART RX internal pulls disabled throughout operation; the FT operating pull-off condition is the relevant I/O supply + 0.3 V. Camera EN100k/OE10k pulldowns retain power/isolation default-off.',
            'off_external_uart_active': 'GPS/radio no longer have powered-off isolation. An externally powered module can inject through the kept 1 kohm into an unpowered MCU; no self-powered GPS/radio with the board off. The SD card remains on main3V3, with CS held high by R460 (10 kohm) at reset.',
            'startup': 'GPS/radio UART TX (PC6 / PB13) idles high before alternate-function operation only while the ports are powered (battery path on); on USB-only power the modules are unpowered, so park PC6 / PB13 as inputs (no pull) or drive them low. Camera: EN high, verified rail settling, RX pull-up and TX idle-high, then OE high. SD_CS high before SPI3 AF6 configuration.',
            'shutdown_shedding': 'GPS/radio supply cannot be switched or power-cycled by firmware. Stop UARTs and SD/QSPI writes, disable camera OE then EN, lower MCU clock, extinguish LEDs/buzzer. Faulted cards must not block safety/flight tasks.',
            'port_device_backfeed': ('Always-on GPS/radio power pins directly back-feed PORT_4V8; U401/U400 can then feed RAW_PROTECTED/VLOGIC (Inference). '
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
            'basis': 'GAP-5; DS12110 Rev 11 Table 136: LSI 29.4-33.6 kHz through 125 C; firmware obligations, not implemented',
            'watchdog': {'prescaler_divisor': 4, 'PR_register': 0, 'RLR': 239, 'LSI_cycles': 960, 'nominal_ms': 30.,
                         'minimum_ms': 960 / 33.6, 'maximum_ms': 960 / 29.4},
            'normal_physical_current_max_ms': 20., 'fault_physical_current_max_ms': 36.,
            'prefire_sync_max_ms': .2, 'reset_HiZ_max_ms': .5, 'actual_gate_current_tail_max_ms': 1.5,
            'postfire_safety_pass_and_refeed_max_ms': 5.,
            'refresh_contract': 'No IWDG refresh from prefire through firing until physical firing current has ended (including tail); then require the SAFETY pass and refeed within 5ms. A failed safety task never refreshes.'},
        'firmware_obligations': [
            'Build a new reviewed binding through the assembly_binding design process; never substitute a board hash into the R1 chain.',
            'GPS USART6 PC6 TX/PC7 RX AF7 (DS12110 Rev 11 Table 10 p. 92); radio UART5 PB13 TX/PB12 RX AF14 (Rev 11 Table 10 p. 91); the same cites as pin_table.tsv rows 63-64 and 51-52.',
            'Camera UART7 PE8 TX/PE7 RX AF7 without flow control. UART5/USART6 are separate from the loader USART interfaces (AN2606 Rev64 Table119 pp277-280: no UART5, PB12 or PB13).',
            'Re-mapped loader pins (AN2606 Rev64 Table119 pp279-280; pin_table an2606_t119_loader_role): PA4 / PA5 / PA6 are SPI1 NSS / SCK / MISO and PE11 / PE12 SPI4 NSS / SCK. In the ROM loader PA6 is driven push-pull into the VLOGIC_SENSE divider only (<= 0.36 mA) and PE11 is an input that R431 holds low (camera port off); before a loader jump drive camera EN/OE low, PC1/PE4 low and SD_CS high. PC11 is loader SPI3_MISO output; R460 keeps the card deselected.',
            'Always-on GPS/radio have no FAULT/EN/OE GPIOs; PD8/PD9/PD10/PD14/PD15/PE15 are NC/analog. EXTI12 CAM_FAULT_N (PE12); EXTI4 LOGIC_SOURCE_ST (PA4) and EXTI5 BAT_FAULT_N (PA5), swapped for routing (D-R2-09); EXTI6 USB_FAULT_N (PD6), EXTI8 VBUS_SENSE (PC8). AUD-4 removes PULLPIN; PC13 is NC. One port per EXTI line; lines5/6/8 share EXTI9_5 and line12 uses EXTI15_10, so each handler checks its pending bit. PE1 IMU_INT1 is on EXTI1 (free on R10; R6-MCU-01): configure PE1 as an input with the internal pull-down and take the roll-loop data-ready interrupt on it; LSM6DSV320X INT1 is push-pull and active high by default (Inference: DS14623 not re-read here), so no pull-up is wanted. EXTI1 has its own vector.',
            'PE4 (U1.3, net PYRO1_GATE_N; the _N is historical) is the ACTIVE-HIGH fire command: PE4 high turns Q124 on. Write its output data low before output mode and keep it low except during a permitted fire (R18-MCU-03). R123 2k (R18-MCU-01) and R127 1k hold Q122 / Q124 off against a 30-50 kOhm internal pull-up; never enable a PC1 or PE4 pull-up, and never route RTC_TAMP3 or WKUP5 to PC1. PC1 ACT_EN_MCU and PE4 pyro gate low before GPIO configuration, port shutdown, ROM-loader entry or reset. PC1 is the independent Q120/Q121 enable through R122, not a sentinel. Keep sentinel pins PE3/PE5/PE6/PC4 without nets and in analog mode (their reset state), never driven: every no-net pin, the sentinels included, stays analog (R5-MCU-03). PA15 is the one no-net pin whose reset state is NOT analog (R7-MCU-01): it resets to JTDI with the internal pull-up (STM32H743 debug-pin reset state, DS12110 / RM0433 as the reviewer read it, not re-read here: Inference), so set PA15 to analog mode with no pull explicitly at start-up; "reset state" wording applies only to the other no-net pins.',
            'GAP-5: keep the independent safety task and IWDG divide-by-4 (PR register 0) / RLR 239 (960 LSI cycles): 30ms nominal, 28.571-32.653ms at LSI 33.6-29.4kHz (DS12110 Rev 11 Table 136, through 125 C). Never refresh from prefire through firing until physical firing current has ended (including tail); require the postfire SAFETY pass and refeed within 5ms. Limit NORMAL PHYSICAL igniter current, including the actual gate-discharge tail, to 20ms; a 20ms GPIO-high command alone is insufficient. Worst-fault physical current is bounded by 32.653ms watchdog +0.2ms prefire/synchronization +0.5ms reset HiZ +1.5ms actual gate-current tail =34.853ms, within the 36ms contract. These are firmware and bench obligations, not implemented. Never fire before launch is detected using accelerometer and barometer. On the ground continuity / bus readings are hard refusals; in flight they are logged and annunciated and never veto a fire. The screw switch is the pad arming device; no separate ARM plug or ARM-link state exists.',
            'F6 / FMEA F-1: the first SERVO1-4 output after reset is neutral 1520us, with a command within 50ms. GAP-5 uses the 960-LSI-cycle IWDG period specified above; only the SAFETY task may refresh it, subject to the no-refresh firing interval. A ROM-loader jump is allowed only before IWDG starts: it cannot be stopped afterward; keep both firing controls low.',
            'D-SS-04 / AUD-3: hold BOTH PC1 ACT_EN_MCU and PE4 low for passive cold screening. After a prior load-switch enable, wait at least 1s and verify RAW_ACT discharged / ACT_GATE off before classifying readings. Bench-qualify passive low/healthy/open bands, leakage and unexpected powered-bus readings using parts_qualification.md; any ground fault is a hard refusal BEFORE PC1 enable, especially a failed-short Q124. Only after a valid passive check may PC1 go high, with PE4 still low for at least 100ms before powered-bus checks or any permitted fire. This settling wait is not the no-refresh firing interval; in-flight sense readings never veto fire.',
            'J122 DB1255pos pins1-4SERVO1-4_OUT,pin5GND signal reference; servo positive and motor return direct to pack. Board cannot cut servo power; qualify neutral-on-reset and measured shared return. J400 DB1252pos is power/arming switch; J9/J410/J420 DB1254pos unkeyed, explicit per-pin power/GND/UART legends and end-to-end harness check; clamps28-16AWG with qualified ferrules/splices for thinner module leads.',
            'Maximum normal-flight MCU clock200MHz for the retained-load budget. Firmware not implemented.',
            'F6 battery-break response (always-on port owner decision2026-10-28): C84 plus firmware shedding, no hardware U400 cutoff and no GPS/radio switches. Use PA6 ADC12_INP3 watchdog on ADC1/2. Ports-on ride-through includes the always-on GPS/radio and card allocation; no software power cutoff can be credited. Bench-verify detection latency, selected-card current, camera current decay and retained load. Loaded battery-break continuity is not guaranteed.',
            'On shedding stop SD and QSPI writes immediately without a blocking flush, stop UARTs, lower camera OE then EN, lower MCU clock, extinguish LEDs/buzzer; retain IMU/barometer/flight state and safety. The SD card may stay busy and powered after host clocks stop; budget its<=200mA write allocation until its actual current falls. No in-flight wait for filesystem/card completion.',
            'Camera TPS2553 FAULT deglitch is3-11ms, turn-off up to3ms (TI SLVS841G p7). FAULT is not battery-break detection. GPS/radio rely on shared LDO/buck current and thermal limits; a short can remove both modules, with no independent fault flag or firmware recovery power-cycle.',
            'On VLOGIC undervoltage/shutdown drop camera EN/OE; GPS/radio are always powered. J400 has no state sensor; retain the no-self-powered-port/e-match restriction. Direct GPS/radio UARTs are FT digital inputs only, within 0 to 5 V, RX pulls always disabled. ST DS12110 Rev 11 Table 112 note 3 p. 210 / Table 147 note 6 p. 242 requires pulls off above the relevant I/O supply + 0.3 V in operation; Table 109 note 4 p. 208 gives a separate 4 V absolute-stress condition. No powered-off isolation or positive injected current allowance.',
            'PC14 drives the buzzer gate through R162 1 kOhm: VBAT-domain PC13/PC14/PC15 are characterised at +/-3 mA only (DS12110 Rev 11 Table 149 p. 244); GPIO speed low (2 MHz limit, Rev 11 Table 150 note 2 p. 246), as pin_table.tsv row 8.',
            'Preserve >=150ms switch-bounce immunity separately from battery-lead-break ride-through. Resume flight state from live evidence after reset.',
            'Radio uplink cannot arm or fire; LR900-F band is 890-915 MHz: use manual channels 12-25 (902-915 MHz) or a maker-confirmed FHSS set inside 902-928 MHz; qualify installed maximum-power radio/GPS immunity.',
            'PC14 buzzer GPIO-toggled; PC13, PE10 and PE0 remain NC (AUD-4 removes the pull-pin). Audit2: PC0 PYRO1_CONT and PC5 ARM1_SENSE directly read their retained split dividers and10nF filters, withoutR168/R170 tails; duplicate bus bank/PB0 removed. Sensor functions unchanged.',
            'UART start-up: camera retains U12 isolation and OE pull-down; before camera OE goes high, RX PE7 pull-up and TX PE8 idle-high. GPS/radio connect directly through 1 kohm; PC7/PB12 are digital AF inputs with internal pulls always disabled; PC6/PB13 idle high only while the ports are powered (battery path on). On USB-only power the GPS/radio are unpowered: park PC6/PB13 as inputs (no pull) or drive them low, so the MCU cannot back-feed a module through the 1 kohm. Never connect self-powered GPS/radio with the board off; measure endpoint TX levels.',
            'Per-sense ADC instances: PC0 PYRO1_CONT ADC123_INP10, PA6 VLOGIC_SENSE ADC12_INP3, PC5 ARM1_SENSE ADC12_INP8 (sole RAW_ACT bus reading), PB1 CAM_5V_SENSE ADC12_INP5. PB0 and PC3_C are NC/analog (R18-REQ-08 removes the V3V3_SENSE divider R62/R63: it read 3V3 against VREF+ = 3V3A from the same rail); read VDDA from VREFINT (VREFIN_CAL, DS12110 Rev 8 Tables 28-29 pp. 111-112) and 3V3 from the internal VBAT/4 bridge (VBAT tied to 3V3; Rev 8 Table 94 p. 180, ratio error +/-10%) on ADC3, as pin_table.tsv row 18. Delete duplicate RAW_ACT_SENSE readings and thresholds. Ground continuity and sole bus readings remain hard refusals; in flight neither vetoes fire. PA6 watchdog uses ADC1/2.',
            'microSD J430 locking hinge, no card-detect: SPI3 AF6 PC10 SCK/PC11 MISO/PC12 MOSI, PD0 software CS. CS high before GPIO/AF setup; >= 74 clocks with CS/MOSI high at 100-400 kHz, then CMD0; run at <= 25 MHz. The R460-R464 (10 kohm) pull-ups to 3V3 and the 3V3 bypass are physical. Select and bench-qualify a card with <= 200 mA write and <= 30 mA idle; keep locked during flight, insert/remove only off with board out.',
            'F5: nominal whole-flight storage spans retained QSPI plus secondary removable microSD, with adequate bounded buffering and at least25% measured throughput margin. No requirement that a whole flight fit16MB QSPI alone. A missing/faulted/full/slow card or corrupt filesystem never delays control, safety, watchdog or fire. Use nonblocking bounded transfers and preallocated files; drop secondary SD records only as fault/overload fallback, not the normal capacity plan. Power loss may corrupt the card; no blocking flush during F6 or firing.',
            'Audit2 item16: keep both LEDs dark from arming to landing until the installed opaque U5 cover passes LED-toggle/ambient-light checkout; the CAD cannot certify the cover.',
            'Selected MJG J-Tek LEAD-FREE maker all-fire0.75A times1.5 gives1.125A current criterion; the maker0.5s test does not certify20ms. Retain R1342ohm, normal physical20ms/fault36ms and qualify selected-lot20ms firing/source/harness/charge before flight.',
            'No-net U1 pins (R4-MCU-04): every U1 pin with no net stays in analog mode (the reset state) and is never configured as an output; the K-loader no-net pins (pin_table an2606_t119_loader_role) are never outputs, so a ROM-loader drive or a stray configuration cannot reach copper.',
            'LSE (R5-MCU-02): keep RCC_BDCR.LSEON = 0 and never set up the backup domain for the LSE: PC14 is OSC32_IN and drives BUZZ_DRV through R162, and VBAT is tied to 3V3, so a stray LSEON persists across NRST.',
            'VBUS_SENSE (R5-MCU-05): PC8 = VBUS / 2 (R9 1 kOhm / R110 1 kOhm); at 4.4 V VBUS the node is 2.20 V, below VIH = 0.7 x VDD = 2.31 V, so VBUS detection needs VBUS >= 4.62 V at VDD 3.3 V. A low PC8 is not proof of no USB: never use it as the sole input to a safety decision.',
            'Audit2 direct PC0/PC5 filtered ADCs retain single-resistor protection; duplicate PB0 bank andR168/R170 tails are removed. Other unprotected sense faults (R5-MCU-04): PA6 VLOGIC_SENSE (shorted R60 puts VLOGIC on an FT_a pin; ADC-mode VIN maximum 4.0 V, positive injection allowance 0 mA (DS12110 Rev 11 Table 109 pp. 207-208 notes 3-5). The digital FT ceiling is min(min(relevant supplies)+4.0 V,6.0 V), or 6.0 V with all relevant supplies at 3.3 V; pulls must be disabled above 4.0 V) and PB1 CAM_5V_SENSE (open R105 puts CAM_5V on a TT_a pin through R104 10 kOhm, limit 4.0 V); single-fault pin-damage cases recorded in parts_qualification.md, no firmware mitigation.',
            'Trace (R6-MCU-03): never enable synchronous trace (PE2 TRACECLK, PC1 TRACED0, PE4 TRACED1) in any debug configuration: PC1 enables the load switch and PE4 is the pyro gate (PYRO1_GATE); trace would drive both firing controls. After PC1 and PE4 are configured as low outputs, lock PC1 with GPIOC_LCKR and PE4 with GPIOE_LCKR (the locks hold until the next reset), then read both registers back: bit 16 (LCKK) and the pin lock bit (PC1 bit 1, PE4 bit 4) must read 1, and the firmware refuses to arm otherwise (D-SS-02 / R7-MCU-02). A locked pin\'s output data can still be written, its configuration cannot: in a loader-jump sequence PC1 and PE4 stay locked low outputs, because GPIOC / GPIOE resets (RCC_AHB4RSTR) clear the locks and only R123 / R127 then hold the controls off. R10 locks PC1 and PE4: PE3 / PE5 / PE6 are analog sentinels, PE12 is the CAM_FAULT_N input and PE13 / PE14 are NC. Disconnect the e-match before connecting a trace-capable debugger session: whether the DBGMCU trace pin assignment overrides the GPIO configuration (and the lock) on the H743 is not checked (Inference; R7-SAF-03).',
            'UART break storm: camera retains the TXU0202 input pull-down and can report a continuous break if enabled while unplugged. Direct GPS/radio can float/noise when unplugged. Receive by DMA/IDLE with bounded error handling; mask FE/NE/ORE per-frame storms and disable the affected UART after a bounded error threshold. GPS/radio cannot be isolated or power-cycled in software; camera OE may be lowered.',
            'Trace override bench step (R8-SAF-01 / R9-MCU-01): no e-match connected. Use a debugger-supported STM32H743 synchronous 4-bit ETM setup; RM0433 Rev8 pp3209/543 uses DBGMCU_CR at 0x5C001004 bit20 TRACECLKEN (CMSIS DBGMCU_CR_DBG_TRACECKEN), not TRACE_IOEN or TRACE_MODE. With QSPI idle, set PE2 AF0 TRACECLK; keep PC1 and PE4 locked low GPIO outputs, not trace alternate functions. Read back both GPIOC_LCKR and GPIOE_LCKR: LCKK bit16 plus PC1 bit1 / PE4 bit4 must remain set. Verify the debugger did not reset GPIOC/GPIOE or clear either lock. Observe a running PE2 trace clock before quiet PC1 / PE4 / TP122 counts as evidence; absent clock or lost lock invalidates the test. If either control toggles with valid clock/locks, enforce trace-clock disable and readback before arming and report it (override behavior remains Inference until measured).',
            'W25Q128JV (R6-MCU-04): set the QE bit in status register 2 before QSPI quad mode is used; no blocking flash erase in flight: pre-erase before flight or use erase-suspend, so that the GAP-5 28.571ms minimum IWDG period holds (W25Q128JV Rev I AC characteristics, read in round 7: 4 KB sector erase 45 ms typical / 400 ms maximum, 32 KB block 120 / 1,600 ms, 64 KB block 150 / 2,000 ms, erase-suspend latency tSUS 20 us). The pad ring buffer must be erased in erase-suspend slices or sized for a single pre-erase before arming; erase time is added to the F5 timing-margin statement. This is an open firmware design obligation (R7-MCU-04).',
            'LSM6DSV320X (R6-MCU-05): IMU SPI clock <= 10 MHz (DS14623, as the reviewer read it, not re-read here); ignore gyro data for 40 ms after an IMU power-up (Ton, same source).'
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
