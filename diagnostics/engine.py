"""Deterministic interpretation of raw evidence; missing data never becomes PASS."""
import hashlib
import json
import math
from pathlib import Path

from .registers import REGISTERS, RESET_BITS, CPUID_MASK, EXPECTED_CPUID, EXPECTED_FAMILY

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path):
    def unique(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                raise ValueError('Duplicate JSON key: ' + k)
            d[k] = v
        return d
    return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def number(x, label):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError('Finite number required: ' + label)
    return x


def raw_value(row):
    if row.get('error') is not None:
        if row.get('value') is not None:
            raise ValueError('A failed read cannot also carry a value')
        return None
    v = row.get('value')
    if v is None:
        return None
    if isinstance(v, str) and v.startswith('0x'):
        v = int(v, 16)
    if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v < 2**row['bits']:
        raise ValueError('Invalid register value')
    return v


def validate_snapshot(s, binding):
    if s.get('schema') != 1 or s.get('origin') not in ('SWD_CAPTURE', 'SYNTHETIC_FIXTURE'):
        raise ValueError('Unknown snapshot schema/origin')
    if s.get('board_sha256') != binding['board_sha256']:
        raise ValueError('Snapshot belongs to another PCB revision')
    if not isinstance(s.get('assembly_id'), str) or not s['assembly_id'].strip():
        raise ValueError('Assembly identifier required')
    if not isinstance(s.get('capture_id'), str) or not s['capture_id'].strip() or not s.get('captured_at'):
        raise ValueError('Capture identifier/time required')
    if s.get('state') not in ('STARTED', 'CAPTURED', 'PARTIAL', 'IDENTITY_UNCONFIRMED',
                              'CONNECTION_FAILED', 'CLEANUP_FAILED', 'ABORTED'):
        raise ValueError('Unknown capture state')
    out = {}
    for row in s.get('reads', []):
        key = (row.get('sample'), row.get('name'))
        if key in out or type(key[0]) is not int or key[0] not in (0, 1) or key[1] not in REGISTERS:
            raise ValueError('Duplicate/unknown register or sample')
        address, bits = REGISTERS[key[1]]
        if row.get('address') != f'0x{address:08x}' or type(row.get('bits')) is not int or row['bits'] != bits:
            raise ValueError('Register address/width does not match allowlist')
        if number(row.get('elapsed_ms'), 'elapsed_ms') < 0:
            raise ValueError('Negative elapsed time')
        out[key] = raw_value(row)
    return out


def analyze(snapshot, binding, bench=None):
    values = validate_snapshot(snapshot, binding)
    checks = []
    def add(code, status, text, next_step='', evidence=None):
        checks.append(dict(id=code, status=status, finding=text,
                           next_step=next_step, evidence=evidence))
    def get(name, sample=0):
        return values.get((sample, name))

    if snapshot['state'] != 'CAPTURED':
        add('CAPTURE_COMPLETENESS', 'INCONCLUSIVE',
            'Capture state=' + snapshot['state'] + '; only retained readings are interpreted.',
            'Errors / timeouts / missing data are never evidence of a pass.')

    cpuid, device = get('CPUID'), get('DBGMCU_IDCODE')
    identity = cpuid is not None and device is not None
    if not identity:
        add('DBG_LINK', 'INCONCLUSIVE', 'The debug port returned no complete device identity.',
            'Check J2.5 supply reference, J2.1 ground, NRST, SWCLK/SWDIO and the probe per the test-point map; this does not show the MCU is broken.')
    else:
        identity = cpuid & CPUID_MASK == EXPECTED_CPUID and device & 0xFFF == EXPECTED_FAMILY
        add('DBG_IDENTITY', 'PASS' if identity else 'FAIL',
            f'CPUID=0x{cpuid:08x}, DEV_ID=0x{device & 0xFFF:03x}, REV_ID=0x{device >> 16:04x}.',
            'These fields only confirm the core and compatible family, not the exact part number, package or authenticity.',
            {'variant': (cpuid >> 20) & 15, 'revision': cpuid & 15})

    if identity:
        size = get('FLASH_SIZE_KIB')
        add('FLASH_CAPACITY', 'NOT_TESTED' if size is None else 'PASS' if size == 2048 else 'FAIL',
            f'Flash size register={size} KiB; the current VI part expects 2048 KiB.',
            'This reads the size identifier; it is not a write / erase / read-back test.')
        uid = [get('UID' + str(i)) for i in range(3)]
        if any(x is None for x in uid):
            add('BOARD_UID', 'NOT_TESTED', '96-bit UID read incomplete.')
        else:
            ok = uid != [0]*3 and uid != [0xFFFFFFFF]*3
            add('BOARD_UID', 'PASS' if ok else 'FAIL', 'UID=' + '-'.join(f'{x:08x}' for x in uid),
                'Register the UID against the physical assembly ID; a single zero 32-bit word is not a device error.')

        rsr, rsr1 = get('RCC_RSR'), get('RCC_RSR', 1)
        if rsr is None:
            add('RESET_HISTORY', 'NOT_TESTED', 'RCC_RSR not read.')
        else:
            flags = [name for bit, name in RESET_BITS.items() if rsr & (1 << bit)]
            add('RESET_HISTORY', 'INFO', 'Reset flags: ' + (', '.join(flags) or 'none'),
                'Flags may accumulate or have been cleared by firmware; they cannot uniquely identify the last reset cause. This program never clears them.', flags)
            if rsr1 is not None and rsr != rsr1:
                add('RESET_CHANGED', 'WARNING', 'Reset flags changed between the two reads.',
                    'A reset may have occurred or firmware cleared the flags; investigate with supply waveforms and the boot log.')

        cr, cfgr, cr1, cfgr1 = [get(n, i) for n, i in
                                [('RCC_CR', 0), ('RCC_CFGR', 0), ('RCC_CR', 1), ('RCC_CFGR', 1)]]
        if any(v is None for v in (cr, cfgr, cr1, cfgr1)):
            add('CLOCK_SNAPSHOT', 'NOT_TESTED', 'Double sampling of clock state incomplete.')
        elif (cr, cfgr) != (cr1, cfgr1):
            add('CLOCK_SNAPSHOT', 'INCONCLUSIVE', 'Clock configuration or ready flags changed during sampling.',
                'Capture again after initialisation finishes; a running register snapshot is not atomic.')
        else:
            source = (cfgr >> 3) & 7
            names = ['HSI', 'CSI', 'HSE', 'PLL1']
            ready_bits = [2, 8, 17, 25]
            ok = source < 4 and bool(cr & (1 << ready_bits[source]))
            add('CLOCK_SNAPSHOT', 'INFO' if ok else 'WARNING',
                f'System clock source={names[source] if source < 4 else "reserved"}; selected source ready={ok}.',
                'Only configuration / ready state is checked; frequency accuracy, start-up margin and jitter still need measurement.')
            enabled, ready = bool(cr & (1 << 16)), bool(cr & (1 << 17))
            add('HSE_STATE', 'NOT_TESTED' if not enabled else 'INFO' if ready else 'WARNING',
                f'HSE enabled={enabled}, ready={ready}.',
                'HSE not enabled does not mean the crystal is bad; enabled but not ready must be separated into still initialising, software configuration, or a Y1/C25/C26 problem.')
        cfsr, hfsr = get('CFSR'), get('HFSR')
        if cfsr is None or hfsr is None:
            add('CPU_FAULT_FLAGS', 'NOT_TESTED', 'CPU fault state not fully read.')
        else:
            detail = {'CFSR': f'0x{cfsr:08x}', 'HFSR': f'0x{hfsr:08x}'}
            if cfsr & (1 << 7):
                detail['MMFAR'] = get('MMFAR')
            if cfsr & (1 << 15):
                detail['BFAR'] = get('BFAR')
            add('CPU_FAULT_FLAGS', 'WARNING' if cfsr or hfsr else 'INFO',
                'CPU fault flags recorded; state not cleared.',
                'Flags set do not mean a fault is still present, and zero flags do not prove the firmware correct. Fault addresses are interpreted only when VALID is set.', detail)
        vos = get('PWR_D3CR')
        add('VOLTAGE_SCALING', 'NOT_TESTED' if vos is None else 'INFO',
            'PWR_D3CR not read.' if vos is None else
            f'VOS code={(vos >> 14) & 3}, VOSRDY={bool(vos & (1 << 13))}.',
            'Digital state is not a measured VCAP voltage; interpret with the silicon revision and operating mode.')
    else:
        add('DEVICE_TESTS', 'NOT_TESTED', 'Device identity not confirmed; part-specific registers are not interpreted.')

    if bench is not None:
        analyze_bench(bench, snapshot, binding, add)
    else:
        add('POWER_MEASUREMENTS', 'NOT_TESTED', 'No external instrument voltage evidence.',
            'Fill in an independent bench measurement sheet; never use the ADC reference to prove its own supply is correct.')
    for code, text in [('SPI_SENSOR', 'IMU identity, sample liveness, noise and interrupt'),
                       ('I2C_SENSOR', 'Barometer PROM CRC, conversion and noise'),
                       ('QSPI_DATA', 'External flash quad write/read verification'),
                       ('USB_DATA', 'USB enumeration and data transfer'),
                       ('WATCHDOG', 'Real watchdog timeout reset'),
                       ('TRANSIENTS', 'Power start-up, ripple and load steps')]:
        add(code, 'NOT_TESTED', text + ' not yet performed.')
    add('GNSS', 'NOT_POPULATED' if binding['gnss_dnp'] else 'NOT_TESTED',
        'U6 is not fitted in this assembly configuration; the physical configuration still needs recording.' if binding['gnss_dnp'] else 'GNSS communication / RF not tested.')
    failing = [c['id'] for c in checks if c['status'] == 'FAIL']
    return dict(schema=1, scope='bench register snapshot + optional external DC measurements',
                board_sha256=snapshot['board_sha256'], assembly_id=snapshot['assembly_id'],
                origin=snapshot['origin'], captured_at=snapshot.get('captured_at'),
                capture_state=snapshot.get('state'), capture_error=snapshot.get('error'),
                overall='ISSUES_FOUND' if failing else 'INCOMPLETE',
                first_failed_check=failing[0] if failing else None,
                hardware_qualified=False, fabrication_release=False,
                synthetic=snapshot['origin'] == 'SYNTHETIC_FIXTURE', checks=checks)


def analyze_bench(b, snapshot, binding, add):
    if b.get('schema') != 1 or b.get('board_sha256') != binding['board_sha256']:
        raise ValueError('Bench evidence PCB revision mismatch')
    if b.get('assembly_id') != snapshot['assembly_id'] or b.get('capture_id') != snapshot['capture_id']:
        raise ValueError('Bench evidence must identify this exact assembly/capture session')
    expected_origin = 'SYNTHETIC_FIXTURE' if snapshot['origin'] == 'SYNTHETIC_FIXTURE' else 'MANUAL_BENCH'
    if b.get('origin') != expected_origin:
        raise ValueError('Do not mix synthetic and physical measurements')
    points = {p['net']: p for p in b.get('points', [])}
    if len(points) != len(b.get('points', [])) or set(points) - set(binding['probes']):
        raise ValueError('Duplicate/unknown measurement point')
    m = {}
    for net, p in points.items():
        if p.get('measurement') is None:
            continue
        if p.get('probe') != binding['probes'][net]['probe']:
            raise ValueError('Measurement pad does not match PCB: ' + net)
        q = p['measurement']
        if not q.get('instrument') or not q.get('measured_at') or q.get('unit') != 'V':
            raise ValueError('Instrument/time/unit missing: ' + net)
        v, u, rin = [number(q.get(k), net + '/' + k) for k in ('value', 'uncertainty_v', 'input_ohm')]
        if u < 0 or rin <= 0:
            raise ValueError('Invalid uncertainty/input resistance')
        m[net] = (v-u, v+u, rin)

    for net in ('3V3', '3V3A'):
        if net not in m:
            add('DC_' + net, 'NOT_TESTED', net + ' has no measured value.')
        else:
            lo, hi, _ = m[net]
            status = 'PASS' if lo >= 3.135 and hi <= 3.465 else 'FAIL' if hi < 3.135 or lo > 3.465 else 'INCONCLUSIVE'
            add('DC_' + net, status, f'{net} measured interval=[{lo:.4f},{hi:.4f}] V.',
                '3.3 V ±5% is only a DC screening window, not proof that every chip or transient is acceptable.')
    if all(n in m for n in ('VBUS', 'VLOGIC', '3V3', '3V3A')):
        # Locate the first gross collapse with independent instruments. Thresholds
        # are deliberately gross diagnostic screens, not precision rail specs.
        if m['VBUS'][0] > 4 and m['VLOGIC'][1] < 1:
            profile = binding.get('profile')
            if profile in ('M3-PWR-R1', 'M3-PWR-R2', 'M3-PWR-R3', 'M3-UART-R1',
                           'M3-USB-R1', 'M3-GNSS-R1', 'M3-PDIAG-R1', 'M3-ASSY-R1'):
                path = 'Check U10 input / USB_LIMITED, U11 input selection / output and VLOGIC load shorts; D3 was removed in this revision.'
            elif profile in ('CORE-R3', 'M3-CORE-R3', 'M3-CAM-R1'):
                path = 'Check D3 polarity / soldering / path and downstream VLOGIC shorts; this does not assert D3 is broken.'
            else:
                path = 'Power-path revision not recognised: measure USB input protection, source selection and VLOGIC load stage by stage from that board\'s schematic; no reference designators are guessed.'
            add('POWER_PATH', 'FAIL', 'VBUS present but VLOGIC severely low.',
                path)
        elif m['VLOGIC'][0] > 4 and m['3V3'][1] < 1:
            add('POWER_PATH', 'FAIL', 'Regulator input present but 3V3 not established.',
                'Check U2/L1/C8/C9, enable / supply, assembly and 3V3 load shorts.')
        elif m['3V3'][0] > 3 and m['3V3A'][1] < 1:
            add('POWER_PATH', 'FAIL', '3V3 present but 3V3A not established.',
                'Check the L2 connection and sensor-side load shorts first, then SPI/I2C.')
        else:
            add('POWER_PATH', 'INFO', 'None of the three severe power-drop criteria triggered.', 'This is not a transient / thermal stability pass.')
    for code, source, sense, top, bottom in [
            ('DIV_VLOGIC', 'VLOGIC', 'VLOGIC_SENSE', 100000, 10000),
            ('DIV_3V3', '3V3', 'V3V3_SENSE', 10000, 10000)]:
        if source not in m or sense not in m:
            add(code, 'NOT_TESTED', source + '/' + sense + ' lacks paired measurements.')
            continue
        sl, sh, _ = m[source]
        lo, hi, rin = m[sense]
        def ratio(rt, rb):
            rb = 1/(1/rb + 1/rin)  # voltmeter loads the lower arm
            return rb/(rt+rb)
        expected = [sl*ratio(top*1.01, bottom*.99), sh*ratio(top*.99, bottom*1.01)]
        overlap = hi >= expected[0] and lo <= expected[1]
        add(code, 'INFO' if overlap else 'FAIL',
            f'Measured interval [{lo:.5f},{hi:.5f}] V; the 1% resistor + meter input loading model expects [{expected[0]:.5f},{expected[1]:.5f}] V.',
            'Overlap only means consistency with this model; if they do not overlap, check wiring / meter / fitted resistor values first, then the divider and ADC side.')


def markdown(report):
    lines = ['# M3 diagnostic record', '',
             '**Synthetic test data; must not be used for physical acceptance.**' if report['synthetic'] else '**This record is not a whole-board pass.**', '',
             f"Status: {report['overall']}; assembly ID: {report['assembly_id']}",
             f"Board file SHA-256: `{report['board_sha256']}`", '',
             '| Check | Result | Finding and next step |', '|---|---|---|']
    def clean(s):
        return str(s).replace('|', '\\|').replace('\n', ' ')
    for c in report['checks']:
        lines.append(f"| {clean(c['id'])} | {c['status']} | {clean(c['finding'] + ' ' + c['next_step'])} |")
    if report.get('capture_error'):
        lines += ['', 'Capture error: ' + clean(report['capture_error'])]
    return '\n'.join(lines) + '\n'
