#!/usr/bin/env python3
"""Check the R10 schematic against the R9 source and explicit circuit contract.

Usage: python3 -B m3_design/r10_sch_check.py --project DIR [--json FILE]
Checks every pin and fitted component, retained functional safety, UART isolation,
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


def expected():
    parts, pins = gen.baseline()
    data = gen.circuit()
    for ref in data['removed_refs']:
        parts.pop(ref)
        pins = {key: value for key, value in pins.items() if key[0] != ref}
    for ref, spec in {**data['parts'], **data['replacements']}.items():
        parts[ref] = spec
        pins = {key: value for key, value in pins.items() if key[0] != ref}
        pins.update({(ref, pin): net for pin, net in spec['nets'].items()})
    for pin in ('2', '5', '8', '11'):
        pins['J122', pin] = None
    for row in csv.DictReader((gen.SOURCE / 'pin_table.tsv').open(), delimiter='\t'):
        pins['U1', row['pin']] = None if row['r10_net'] == 'NC' else row['r10_net']
    return parts, pins


def contract(actual_parts, actual_pins):
    want_parts, want_pins = expected()
    issues = []
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
        'ARM bypass': lambda p, n: n.update({('J124', '1'): 'RAW_ACT'}),
        'servo middle row powered': lambda p, n: n.update({('J122', '2'): 'RAW_ACT'}),
        'radio USB injection bypass': lambda p, n: n.update({('U1', '51'): 'RADIO_RX_WIRE'}),
        'GPS OE pulldown missing': lambda p, n: p.pop('R442'),
        'radio enable bias missing': lambda p, n: p.pop('R421'),
        'pyro load switch removed': lambda p, n: p.pop('Q120'),
        'pyro gate capacitor excluded': lambda p, n: ET.SubElement(p['C126'], 'property', name='exclude_from_bom'),
        'shorted igniter limiter DNP': lambda p, n: ET.SubElement(p['R134'], 'property', name='dnp'),
        'GPS FAULT pullup externally powered': lambda p, n: n.update({('R412', '2'): 'GPS_4V8'}),
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
    rows = list(csv.DictReader((gen.SOURCE / 'pin_table.tsv').open(), delimiter='\t'))
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
            'translator': 'https://www.ti.com/lit/ds/symlink/txu0202.pdf',
            'switch': 'https://www.ti.com/lit/ds/symlink/tps2553.pdf'},
        'port_states': {
            'reset_boot': '100k EN and 10k OE pulldowns hold each external port disabled; fault pullups only to main 3V3.',
            'off_external_uart_active': 'TXU0202 partial-power-down isolation; ground-only ESD clamps; test both UART lines and independently powered radio USB.',
            'startup': 'EN high, wait for verified rail settling, configure UART idle-high, then OE high; no GPIO alternate function before safe port state.',
            'shutdown_shedding': 'OE low before EN low; stop UART activity. Do not infer immediate loss of supply from delayed FAULT.',
            'usb_radio_vcc_backfeed': 'Separately qualify TPS2553 reverse current and up-to-7ms reverse-trip transition; UART isolation alone does not qualify the power pin.',
            'port_device_backfeed': ('An ENABLED TPS2553 blocks reverse current only above 95-190 mV / 135 mOhm, about 0.7 A, after 3-7 ms '
                                     '(SLVS841F section 7.5 p7): a self- or USB-powered GPS, radio or camera can back-feed PORT_4V8 / PORT_5V3, '
                                     'then RAW_PROTECTED (U401 / U400 body paths, Inference), VLOGIC and ACT_EN (R122/R123) with the power '
                                     'switch open; ORDERING R10 bench step (R3-SAF-02).')},
        'firmware_obligations': [
            'Build a new reviewed binding through the assembly_binding design process; never substitute a board hash into the R1 chain.',
            'GPS USART6 PC6 TX/PC7 RX AF7 (DS12110 Rev10 Table12 p91); radio UART5 PB13 TX/PB12 RX AF14 (Table11 p90).',
            'Camera UART7 PE8 TX/PE7 RX AF7 without flow control. UART5/USART6 are separate from the loader USART interfaces (AN2606 Rev64 Table119 pp277-280: no UART5, PB12 or PB13).',
            'Re-mapped loader pins (AN2606 Rev64 Table119 pp279-280; pin_table an2606_t119_loader_role): PA4 / PA5 / PA6 are SPI1 NSS / SCK / MISO and PE11 / PE12 SPI4 NSS / SCK. In the ROM loader PA6 is driven push-pull into the VLOGIC_SENSE divider only (<= 0.36 mA) and PE11 is an input that R431 holds low (camera port off); before a loader jump drive every port EN and OE low as well as PE4.',
            'EXTI10 GPS_FAULT_N (PD10), EXTI9 RADIO_FAULT_N (PD9), EXTI12 CAM_FAULT_N (PE12); EXTI4 LOGIC_SOURCE_ST (PA4) and EXTI5 BAT_FAULT_N (PA5), swapped for routing (D-R2-09); EXTI6 USB_FAULT_N (PD6), EXTI8 VBUS_SENSE (PC8), EXTI13 PULLPIN (PC13). One port per EXTI line; lines 5/6/8/9 share EXTI9_5 and 10/12/13 share EXTI15_10, so each handler checks its pending bit. PE1 IMU interrupt polled.',
            'PE4 pyro gate low before GPIO configuration, port shutdown, ROM-loader entry or reset. Keep sentinel pins PE3/PE5/PE6/PC1/PC4 without nets and driven low in operation.',
            'Keep hardware watchdog and independent safety task; end every fire pulse within20ms. Ground ARM/continuity refusal; in-flight readings never veto a fire.',
            'F6 / FMEA F-1: the first SERVO1-4 output after any reset is neutral 1520 us; IWDG <= 32 ms, fed only by the 100 Hz safety task.',
            'Servo positive and motor return direct to pack. Board cannot cut servo power; qualify neutral-on-reset with the chosen servo and harness.',
            'Maximum normal-flight MCU clock200MHz for the retained-load budget. Firmware not implemented.',
            'F6 battery-break response uses the PA6 (ADC12_INP3, moved from PC2_C, D-R2-09) VLOGIC_SENSE ADC watchdog, not delayed port FAULT. Threshold, maximum detection/shedding latency and retained-load envelope require measured qualification.',
            'On shedding disable all three UART OEs and port switches, pause flash writes, lower MCU clock, extinguish LEDs/buzzer; retain IMU/barometer/flight state and safety timing.',
            'Drop every port enable and UART OE when the power switch opens or VLOGIC sags: port back-feed through an enabled TPS2553 is not blocked below about 0.7 A (R3-SAF-02).',
            'PC14 drives the buzzer gate through R162 1 kOhm: VBAT-domain PC13/PC14/PC15 are characterised at +/-3 mA only (DS12110 Rev10 Table62 p141); GPIO speed low (2 MHz limit, Table63 note 2).',
            'Preserve >=150ms switch-bounce immunity separately from battery-lead-break ride-through. Resume flight state from live evidence after reset.',
            'Radio uplink cannot arm or fire; LR900-F band is 890-915 MHz: use manual channels 12-25 (902-915 MHz) or a maker-confirmed FHSS set inside 902-928 MHz; qualify installed maximum-power radio/GPS immunity.',
            'PC14 buzzer GPIO-toggled and PC13 pull-pin input (swapped for routing, D-R2-07); PE10 and PE0 remain NC. Retained safety ADC dividers and sensor functions unchanged.',
            'Port UART start-up (R4-MCU-01): while U1 is in reset the TXU0202 A side floats and the OE pull-downs hold the translators off. Before any translator OE goes high, enable the internal pull-ups on the three MCU receive pins GPS_RX_MCU (PC7), RADIO_RX_MCU (PB12) and CAM_MCU_RX (PE7), and drive the three TX pins (PC6, PB13, PE8) idle-high; only then raise OE.',
            'Per-sense ADC instance and channel (R4-MCU-02; Inference until each is checked against DS12110 Rev10 Table 9): PC0 PYRO1_CONT_MCU ADC123_INP10, PA6 VLOGIC_SENSE ADC12_INP3, PC5 ARM1_SENSE_MCU ADC12_INP8, PB0 RAW_ACT_SENSE_MCU ADC12_INP9, PB1 CAM_5V_SENSE ADC12_INP5, PC3_C V3V3_SENSE ADC3_INP1 (ADC3 only). The F6 analog watchdog on PA6 must therefore run on ADC1 or ADC2, not ADC3; V3V3_SENSE is read on ADC3.',
            'No-net U1 pins (R4-MCU-04): every U1 pin with no net stays in analog mode (the reset state) and is never configured as an output; the K-loader no-net pins (pin_table an2606_t119_loader_role) are never outputs, so a ROM-loader drive or a stray configuration cannot reach copper.'
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
                       'lever_arm_z_mm': -2.06, 'lever_arm_z_basis': 'Inference: centre of the U4 3D model box, not measured', 'bench_sign_check': 'required'}
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
