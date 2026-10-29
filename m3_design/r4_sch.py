#!/usr/bin/env python3
"""M3-ASSY-R3 -> R4 schematic edits (docs/M3_R4.md, from docs/R3_VALIDATION.md).

usage: python3 m3_design/r4_sch.py [m3_design/assembly_review]

Plain-text edits on the KiCad 10 sheet files, in the existing house style: every
part is an M3:* symbol whose pins reach global labels through short wires.
New symbols get stable UUIDs (uuid5 of the reference), so m3_design/r4_pcb.py can
link footprints to them and a second run changes nothing. Run this first, then
r4_pcb.py, then tools/check.sh (parity proves the two agree).
"""
import re
import sys
import uuid
from pathlib import Path

D = Path(sys.argv[1] if len(sys.argv) > 1 else 'm3_design/assembly_review')
ROOT = '6007a7db-6a58-5660-8beb-956dea045ff8'
NS = uuid.UUID('5f1c0e3a-8d64-4c1b-9a52-4d334f525234')   # fixed namespace -> stable R4 UUIDs
GRID = 2.54


def uid(*key):
    return str(uuid.uuid5(NS, ':'.join(key)))


def fmt(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.') if abs(v - round(v, 2)) < 1e-9 else repr(v)


def effects(size, justify=None, hide=False):
    j = f'\n\t\t\t\t(justify {justify})' if justify else ''
    h = '\n\t\t\t(hide yes)' if hide else ''
    return f'{h}\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size {size} {size})){j})'


def prop(name, value, x, y, hide=True, justify='left'):
    return f'\t\t(property "{name}" "{value}"\n\t\t\t(at {fmt(x)} {fmt(y)} 0){effects(1.27, justify, hide)})\n'


def sheet_path(text):
    """Instance path of the sheet (root uuid / sheet uuid), read from an existing symbol."""
    m = re.search(r'\(path "(/' + ROOT + r'/[0-9a-f-]+)"', text)
    if not m:
        raise SystemExit('no instance path found in sheet')
    return m.group(1)


def close_paren(text, start):
    """Index just past the parenthesis that closes the one opening at text[start] (skips strings)."""
    depth, i, n, in_str = 0, start, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            if c == '\\':
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise SystemExit('unbalanced parentheses')


def symbol_block(text, ref):
    """(start, end) of the top-level symbol whose Reference is ref, or None."""
    i = text.find(f'(property "Reference" "{ref}"')
    if i < 0:
        return None
    s = text.rfind('\n\t(symbol\n', 0, i) + 2          # at the '('
    return s, close_paren(text, s)


def wire(x1, y1, x2, y2, key):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {fmt(x1)} {fmt(y1)})\n\t\t\t(xy {fmt(x2)} {fmt(y2)}))\n'
            f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default))\n\t\t(uuid {uid(key)}))\n')


def glabel(net, x, y, key, angle=0, justify='right'):
    return (f'\t(global_label "{net}"\n\t\t(shape passive)\n\t\t(at {fmt(x)} {fmt(y)} {angle})'
            f'\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.05 1.05))\n\t\t\t(justify {justify}))\n\t\t(uuid {uid(key)}))\n')


def note(textline, x, y, key):
    return (f'\t(text "{textline}"\n\t\t(at {fmt(x)} {fmt(y)} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.05 1.05))'
            f'\n\t\t\t(justify left))\n\t\t(uuid {uid(key)}))\n')


def two_pin(ref, lib_id, value, footprint, fields, x, y, net1, net2, path):
    """Vertical 2-pin M3:R / M3:C symbol at (x, y): pin 1 at y - 3.81 (top), pin 2 at y + 3.81.
    Each pin gets a 7.62 mm wire to the left ending in a global label (the sheet's style)."""
    body = (f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {fmt(x)} {fmt(y)} 0)\n\t\t(unit 1)\n'
            f'\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(uuid {uid(ref)})\n')
    body += prop('Reference', ref, x + GRID, y - 1.27, hide=False)
    body += prop('Value', value, x + GRID, y + 1.27, hide=False)
    body += prop('Footprint', footprint, x, y)
    body += prop('Datasheet', '', x, y)
    for k, v in fields.items():
        body += prop(k, v, x, y)
    body += (f'\t\t(instances\n\t\t\t(project "m3"\n\t\t\t\t(path "{path}"\n'
             f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)))))\n')
    out = body
    for pin, (py, net) in enumerate(((y - 3.81, net1), (y + 3.81, net2)), 1):
        out += wire(x, py, x - 3 * GRID, py, f'{ref}:w{pin}')
        out += glabel(net, x - 3 * GRID, py, f'{ref}:l{pin}')
    return out


def insert(text, chunk):
    i = text.rfind('\t(sheet_instances')
    return text[:i] + chunk + text[i:]


def set_props(text, ref, updates, optional=()):
    """Set existing properties of a symbol; names in `optional` are skipped when the symbol lacks them."""
    s, e = symbol_block(text, ref)
    blk = text[s:e]
    for k, v in updates.items():
        blk, n = re.subn(r'(\(property "' + re.escape(k) + r'" )"[^"]*"', r'\g<1>"' + v + '"', blk)
        if n != 1 and not (n == 0 and k in optional):
            raise SystemExit(f'{ref}: property {k} found {n} times')
    return text[:s] + blk + text[e:]


def replace_note(text, old_prefix, new_text):
    """Replace the (text "...") note that starts with old_prefix by new_text (no-op when already done)."""
    if f'(text "{new_text}"' in text:
        return text
    pat = r'\(text "' + re.escape(old_prefix) + r'[^"]*"'
    text, n = re.subn(pat, lambda _m: f'(text "{new_text}"', text)
    if n != 1:
        raise SystemExit(f'note {old_prefix!r} found {n} times')
    return text


# ---------------------------------------------------------------------------------------------
# Edits. Each returns the new text; each is a no-op when already applied.

def a1_enable_ride_through(t):
    """A1: 2.2 uF on U9 EN/UVLO (BAT_ENABLE). Opening the switch now discharges it through R81
    (0.62 s), so a contact bounce shorter than ~0.1 s (6.0 V) to ~0.3 s (8.4 V) no longer
    reaches U9's 25-64 us turn-off. Same part as C19/C20/C120 (C23630, JLC Basic)."""
    if symbol_block(t, 'C87'):
        return t
    path = sheet_path(t)
    chunk = two_pin('C87', 'M3:C', '2.2uF', 'rocket:C0603', {'LCSC': 'C23630', 'LCSC Part': 'C23630'},
                    340.36, 121.92, 'BAT_ENABLE', 'GND', path)
    chunk += note('C87: EN/UVLO ride-through. (R80+R165)||R81 = 227k charges it (0.4-1.1 s turn-on); R81 alone '
                  'discharges it (0.66 s), so switch bounce shorter than 0.19/0.33/0.41 s at 6.0/7.4/8.4 V (worst case '
                  '0.11/0.21/0.27 s) cannot trip U9 (25-64 us t_D,OFF). UVLO on 4.89-5.05 V, off 4.45-4.61 V.',
                  20.32, 280.67, 'C87:note')
    return insert(t, chunk)


def a2_ovlo_release(t):
    """A2: R83 300k -> 280k (same part as R81). OVLO trip 9.63-9.96 V, release 8.76-9.09 V,
    so a full 8.4 V pack can no longer sit inside the hysteresis band after a trip."""
    return set_props(t, 'R83', {'Value': '280k 0.1%', 'LCSC': 'C705755', 'LCSC Part': 'C705755',
                                'Manufacturer Part': 'RT0603BRD07280KL'})


def b1_usb_detect(t):
    """B1: PD15 VBUS detect divider 6.2k/10k -> 1k/1k (both existing JLC Basic lines). With the
    D+ pull-up enabled and the cable out, D4's I/O->VBUS diode back-feeds VBUS; 2 kOhm holds it
    at <= 2.0 V, so PD15 <= 1.01 V (VIL max 1.19 V at VDD min); at VBUS 4.40 V PD15 = 2.18 V
    (VIH min 1.83 V). Was 1.35-1.6 V, inside the undefined band, in both cases."""
    t = set_props(t, 'R9', {'Value': '1k', 'LCSC': 'C11702', 'LCSC Part': 'C11702',
                            'Manufacturer': '', 'Manufacturer Part': ''})
    t = set_props(t, 'R110', {'Value': '1k 1%', 'LCSC': 'C21190', 'LCSC Part': 'C21190',
                              'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0603WAF1001T5E'})
    return replace_note(t, 'R9=6.2k 1%, R110=10k 0.1%', 'R9 = R110 = 1k (R4): PD15 <= 1.01 V when D4 back-feeds VBUS '
                        'with the D+ pull-up on, 2.18 V at VBUS 4.40 V. TP92 measures their junction. No internal pull-up/down.')


def b8_3v3a_rc(t):
    """B8: L2 (4.7 uH) -> R164 2.2 Ohm. The LC had f0 13-15 kHz with Q 4.4-6.2 (amplifying 3V3
    transients ~1.8x onto the IMU, baro and VREF+); the RC (2.2 Ohm, ~27 uF) is critically damped,
    corner ~2.7 kHz, -52 dB at the 1.1 MHz buck frequency, ~11 mV DC drop at ~5 mA. The u-blox
    series-resistance limit that forced an LC left with the GNSS. Same symbol uuid, same pins."""
    if symbol_block(t, 'R164'):
        return t
    s, e = symbol_block(t, 'L2')
    blk = t[s:e].replace('(lib_id "M3:L")', '(lib_id "M3:R")').replace('(reference "L2")', '(reference "R164")')
    t = t[:s] + blk + t[e:]
    t = set_props(t, 'L2', {'Reference': 'R164'}) if symbol_block(t, 'L2') else t
    return set_props(t, 'R164', {'Value': '2.2R 1%', 'Footprint': 'rocket:R_0603_1608Metric', 'LCSC': 'C22939'})


PYRO_TERMINAL_FIELDS = {'LCSC': 'C430603', 'LCSC Part': 'C430603', 'Manufacturer': 'DORABO',
                        'Manufacturer Part': 'DB128L-5.08-2P-OG-S'}
# validation pass 2 (actuators F1): the ARM terminals are the black DB128L, the igniter terminals stay orange,
# so swapping an ARM link and an igniter harness is visible (wired swapped, the igniter sits across RAW_ACT)
ARM_TERMINAL_FIELDS = {'LCSC': 'C430601', 'LCSC Part': 'C430601', 'Manufacturer': 'DORABO',
                       'Manufacturer Part': 'DB128L-5.08-2P-BK-S'}
ARM_TERMINALS = ('J120', 'J124')


def conn2_block(ref, uuid_, x, y, value, path):
    """M3:Conn_1x2 symbol at (x, y): pins at (x - 7.62, y -/+ 1.27), texts to the right."""
    arm = ref in ARM_TERMINALS
    body = (f'\t(symbol\n\t\t(lib_id "M3:Conn_1x2")\n\t\t(at {fmt(x)} {fmt(y)} 0)\n\t\t(unit 1)\n'
            f'\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(uuid {uuid_})\n')
    body += prop('Reference', ref, x + 3.81, y - 1.27, hide=False)
    body += prop('Value', value, x + 3.81, y + 1.27, hide=False)
    body += prop('Footprint', 'rocket:M3_DB128L_2P_BK' if arm else 'rocket:M3_DB128L_2P', x, y)
    body += prop('Datasheet', '', x, y)
    for k, v in (ARM_TERMINAL_FIELDS if arm else PYRO_TERMINAL_FIELDS).items():
        body += prop(k, v, x, y)
    body += (f'\t\t(instances\n\t\t\t(project "m3"\n\t\t\t\t(path "{path}"\n'
             f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)))))\n')
    return body


def a3_pyro_terminals(t):
    """A3: the ARM (J120) and igniter (J121) terminals become DB128L-5.08-2P pairs (J120 + J124,
    J121 + J125) on the same holes, so pyro terminals no longer look like the green battery (J1) and
    camera (J9) terminals; the 4P part is green-only at JLC. Pass 2: ARM pairs black, igniter pairs
    orange (ARM_TERMINALS). Each new symbol's pins land on the old 1x4 pin positions, so every
    existing wire and label is reused unchanged."""
    if symbol_block(t, 'J124'):
        return t
    if '(symbol "M3:Conn_1x2"' not in t:
        src = (D / 'pullpin_buzzer.kicad_sch').read_text()
        i = src.find('\t\t(symbol "M3:Conn_1x2"')
        blk = src[i:close_paren(src, i + 2)] + '\n'
        k = t.find('\t(lib_symbols\n')
        assert k > 0, 'no lib_symbols block'
        ins = k + len('\t(lib_symbols\n')                      # first child of lib_symbols
        t = t[:ins] + blk + t[ins:]
    path = sheet_path(t)
    for old, new, vals in (('J120', 'J124', ('ARM CH2: RAW / BUS2', 'ARM CH1: BUS1 / RAW')),
                           ('J121', 'J125', ('IGNITER 1: E1- / E1+', 'IGNITER 2: E2+ / E2-'))):
        s, e = symbol_block(t, old)
        blk = t[s:e]
        assert '(lib_id "M3:Conn_1x4")' in blk, old
        u = re.search(r'\(uuid ([0-9a-f-]+)\)', blk).group(1)
        x, y = map(float, re.search(r'\(at ([\d.]+) ([\d.]+) 0\)', blk).groups())
        a = conn2_block(old, u, x, y - 2.54, vals[0], path)          # pins on old pins 1, 2
        c = conn2_block(new, uid(new), x, y + 2.54, vals[1], path)   # pins on old pins 3, 4
        t = t[:s] + a[1:] + c.rstrip('\n') + t[e:]
    t = re.sub(r'\(text "Two independent channels \(FMEA H-5\)\. ARM plug = [^"]*"',
               '(text "Two independent channels (FMEA H-5). ARM links: J124.2 (RAW) -> F1 5A FAST -> J124.1 (BUS1); '
               'J120.1 (RAW) -> F2 5A FAST -> J120.2 (BUS2). R4: DB128L 2P pairs, ARM terminals black, igniter terminals orange."', t)
    t = re.sub(r'\(text "Igniter 1 across J121\.1-2, igniter 2 across J121\.3-4\.[^"]*"',
               '(text "Igniter 1 across J121.1-2, igniter 2 across J125.1-2. Each pin order is reversal-symmetric '
               'within its channel."', t)
    return t


def m_note_tim8(t):
    """Minor: PA5 = TIM8_CH1N (AF3) was verified in docs/M3_R3.md section 6; the note still said inference."""
    return t.replace('software toggle or TIM8_CH1N (AF3, inference).', 'software toggle or TIM8_CH1N (AF3, verified, M3_R3 6).')


def m_note_cold_pullup(t):
    """Minor: the cold pull-up resistors are R131/R143 = 10k, not 47k."""
    return t.replace('(text "D120 + 47k: cold pull-up', '(text "D120 + R131/R143 (10k): cold pull-up')


def m_u9_input_cap(t):
    """Minor: TI asks for a 0.1-1 uF bypass at the TPS25947 IN pin; C80 sat ~11 mm away.
    C88 100 nF (C1525, JLC Basic, already on the BOM) goes right at U9 IN."""
    if symbol_block(t, 'C88'):
        return t
    chunk = two_pin('C88', 'M3:C', '100nF 50V', 'rocket:C0402', {'LCSC': 'C307331'}, 391.16, 121.92, 'BAT_IN', 'GND', sheet_path(t))
    chunk += note('C88: U9 IN bypass at the pin (TI TPS25947 layout guidance); 50 V for the 19.9 V TVS clamp. '
                  'C80/D8 stay at the terminal.', 20.32, 287.02, 'C88:note')
    return insert(t, chunk)


R0603_UNIROYAL = {'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)'}


def v_input_protection(t):
    """Validation pass 1 (docs/M3_R4.md section 1b).
    D8 SMBJ9.0CA -> SMBJ12CA (Littelfuse, C83849): the 9.0 V part breaks down at 10.0-11.5 V, so a
    wrong 3S pack (12.6 V) drove amps through it until it failed (REQUIREMENTS F9). VBR >= 13.3 V now;
    the 19.9 V clamp stays inside U9 IN (28 V), C80 (50 V), Q120 (30 V) and C88, which goes to 50 V.
    R80 1M -> 470k plus R165 470k on the EN side of the external contact: a chafed SW lead or a
    battery lead screwed into J1.3/J1.4 put the pack straight on U9 EN/UVLO (6.5 V abs max); now EN
    sees <= 3.3 V (2S) / 4.9 V (3S). R81 280k -> 300k with R80+R165 = 940k lowers UVLO to 4.45-4.61 V
    off (was 4.92-5.10), so a four-servo stall on a near-empty pack no longer drops the logic."""
    t = set_props(t, 'D8', {'Value': 'SMBJ12CA', 'LCSC': 'C83849', 'Manufacturer': 'Littelfuse',
                            'Manufacturer Part': 'SMBJ12CA', 'LCSC Part': 'C83849'}, optional=('LCSC Part',))
    t = set_props(t, 'R80', {'Value': '470k 1%', 'LCSC': 'C23178', 'LCSC Part': 'C23178',
                             'Manufacturer Part': '0603WAF4703T5E', **R0603_UNIROYAL})
    t = set_props(t, 'R81', {'Value': '300k 1%', 'LCSC': 'C23024', 'LCSC Part': 'C23024',
                             'Manufacturer Part': '0603WAF3003T5E', **R0603_UNIROYAL})
    # J1 pin 4 (SW RETURN) gets its own net; R165 joins it to BAT_ENABLE
    t = t.replace('(global_label "BAT_ENABLE"\n\t\t(shape passive)\n\t\t(at 101.6 72.39 180)',
                  '(global_label "BAT_SW_RETURN"\n\t\t(shape passive)\n\t\t(at 101.6 72.39 180)')
    assert '(global_label "BAT_SW_RETURN"' in t
    if not symbol_block(t, 'R165'):
        t = insert(t, two_pin('R165', 'M3:R', '470k 1%', 'rocket:R0402',
                              {'LCSC': 'C25790', 'LCSC Part': 'C25790', 'Manufacturer Part': '0402WGF4703TCE', **R0603_UNIROYAL},
                              370.84, 121.92, 'BAT_SW_RETURN', 'BAT_ENABLE', sheet_path(t)))
    t = replace_note(t, 'R80 precedes the contact', 'R80 (BAT_IN side) and R165 (EN side) bracket the contact: a chafed SW '
                     'lead or a battery lead in J1.3/J1.4 puts <= 3.3 V (2S) / 4.9 V (3S) on EN (6.5 V abs max). '
                     'Power-enable contact, not a main-current break.')
    return replace_note(t, 'Reverse battery: R80/R82', 'Reverse battery: R80+R165 (940k) and R82 hold EN/OV injection '
                        'below 10 uA; C80 and D8 are nonpolar. D8 SMBJ12CA: VBR >= 13.3 V, so a wrong 3S pack (12.6 V) '
                        'cannot drive it; its 19.9 V clamp is within U9, C80, C88 and Q120 ratings.')


def v_raw_act_sense(t):
    """Validation pass 1 (E3-F4 with the new TVS): R125 4.7k -> 1k (existing Basic line). PB0 is FT_a;
    with its ADC switch on, ST (AN4899 5.2.2, as quoted) limits it to VDDA + 0.3 V = 3.6 V. RAW_ACT / 3.13
    reached 6.4 V at the SMBJ12CA clamp; RAW_ACT / 11 is 0.76 V at 8.4 V and 1.81 V at 19.9 V."""
    t = set_props(t, 'R125', {'Value': '1k', 'LCSC': 'C11702', 'LCSC Part': 'C11702'}, optional=('LCSC Part',))
    return replace_note(t, 'R124/R125 10k/4.7k', 'R124/R125 10k/1k -> PB0 (RAW_ACT / 11: 0.76 V at 8.4 V, 1.81 V at the '
                        '19.9 V TVS clamp; FT_a analog limit VDDA + 0.3 V): RAW_ACT sense AND bleed (tau ~6 s with C121). '
                        'Mandatory external 15 A ATO fuse in battery lead.')


def v_pullpin_jst(t):
    """Validation pass 1 (E5-F5, E6): J123 PZ254 2.54 mm header -> JST PH B2B-PH-K-S (C131337). The
    PZ254 plug stood 16.75 mm with its wires leaving the top 19 mm off the bore axis; the wire bend
    left the bore envelope, and a 3 mm aft shift put the housing inside the coupler. PH: ~6 mm, latching."""
    t = set_props(t, 'J123', {'Value': 'PULL-PIN PH 1x2', 'Footprint': 'rocket:M3_JST_PH_B2B_2P', 'LCSC': 'C131337',
                              'LCSC Part': 'C131337', 'Manufacturer': 'JST', 'Manufacturer Part': 'B2B-PH-K-S(LF)(SN)'},
                  optional=('LCSC Part', 'Manufacturer Part'))
    if 'J123 = JST PH' not in t:
        t = insert(t, note('J123 = JST PH B2B-PH-K-S (R4): ~6 mm high, latching; pin 1 = PULLPIN_EXT, pin 2 = GND. '
                           'The 2.54 mm PZ254 plug and its wire bend did not fit the bore 19 mm off axis.',
                           20.32, 275.48, 'J123:note'))
    return t


IMU_PIN_NAMES = {'AP_SDO': 'SDO', 'RESV_2': 'SDx', 'RESV_3': 'SCx', 'RESV_7': 'GND', 'INT2/FSYNC/CLKIN': 'INT2',
                 'RESV_10': 'OCS_aux', 'RESV_11': 'SDO_aux', 'AP_CS': 'CS', 'AP_SCLK': 'SCL/SPC', 'AP_SDI': 'SDA/SDI'}


def drop_block_at(t, kind, xy):
    """Remove the top-level (kind ...) block anchored at xy (a wire with an end there, or a label at
    it). xy may be numbers or the exact coordinate strings as written in the file (some are float
    artefacts such as 234.95000000000002, so text must be matched verbatim)."""
    x, y = (fmt(v) if isinstance(v, float) else v for v in xy)
    if kind == 'wire':
        key = f'(xy {x} {y})'
        i = t.find(key)
        s_ = t.rfind('\n\t(wire\n', 0, i) + 2
    else:
        key = f'(at {x} {y} '
        i = t.find(key)
        s_ = t.rfind('\n\t(' + kind + ' ', 0, i) + 2
    assert i > 0 and s_ > 1, (kind, xy)
    e = close_paren(t, s_)
    blk = t[s_:e]
    return t[:s_ - 1] + t[e:], blk


def m_imu_lsm6dsv320x(t):
    """IMU swap (first-principles pass): flight 2 (L1000W, light build) reaches ~37 g, beyond the
    ICM-45686's +/-32 g, while gain scheduling integrates acceleration. The ST LSM6DSV320X sits on the
    same LGA-14 land and pin numbers and adds a +/-32..320 g channel; its datasheet sets no supply-ramp
    limit (the ICM-45686 needs 0.01-1 ms; this board ramps in ~3.2 ms) and it is stocked at JLC (the
    ICM-45686 is not). Pins 10/11 (OCS_aux, SDO_aux) must be VDDIO or open, not GND: now no-connect."""
    if '(property "Value" "LSM6DSV320X"' in t:
        return t
    k = t.find('\t\t(symbol "M3:IMU_SPI"\n')
    e = close_paren(t, k + 2)
    blk = t[k:e]
    for old, new in IMU_PIN_NAMES.items():
        blk, n = re.subn(r'\(name "' + re.escape(old) + '"', f'(name "{new}"', blk)
        assert n == 1, old
    blk = re.sub(r'\(pin passive line(\n\t*\(at [^)]*\)\n\t*\(length [^)]*\)\n\t*\(name "GND")',
                 r'(pin power_in line\1', blk)
    t = t[:k] + blk + t[e:]
    t = set_props(t, 'U4', {'Value': 'LSM6DSV320X', 'LCSC': 'C26633007'})
    for y in (76.2, 78.74):                                   # pins 10, 11 at x 229.87
        t, w = drop_block_at(t, 'wire', (229.87, y))
        ends_ = re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', w)
        far = next(p_ for p_ in ends_ if abs(float(p_[0]) - 229.87) > 1e-6 or abs(float(p_[1]) - y) > 1e-6)
        t, lab = drop_block_at(t, 'global_label', far)
        assert '"GND"' in lab, lab
        nc = f'\t(no_connect\n\t\t(at {fmt(229.87)} {fmt(y)})\n\t\t(uuid {uid("U4", "nc", str(y))}))\n'
        t = insert(t, nc)
    t = insert(t, note('U4 = ST LSM6DSV320X (R4): +/-16 g low-g + +/-32..320 g high-g accel, +/-4000 dps gyro, SPI <= 10 MHz. '
                       'Pins 10/11 open per DS14623 table 2.', 20.32, 260.35, 'U4:note'))
    t = replace_note(t, 'U4: single-interface 4-wire SPI.', 'U4: 4-wire SPI. INT2 open; OCS_aux/SDO_aux (pins 10/11) open, '
                     'held by their internal pull-ups (DS14623 table 25).')
    return replace_note(t, 'Firmware must disable the default pulls on tied auxiliary pads',
                        'Firmware: keep OIS_PU_DIS = 0 (pins 10/11 rely on the internal pull-ups); WHO_AM_I 0x73.')


# --- validation pass 2 (docs/M3_R4.md section 1c) ----------------------------------------------

def w_input_damper(t):
    """Power P-1 (pass 2) and F-1/F-2/F-3 (pass 3): a reverse-polarity hot-plug through the battery harness
    rang U9 IN past the TPS25947's -15 V and 10 V/us input limits (SLVSFC9C 6.3, SRIN(F)). Pass 3 re-modelled
    it with Samsung's measured DC-bias curves (C80 keeps 47 % of its 10 uF at 8.4 V) and a stiff warm pack
    (0.03 ohm, 0.1-1 uH): pass 2's damper (22 uF 0805 + 1 ohm) still reached -15.8 V and 14 V/us.
    Now: C80 + C96 2 x 10 uF 50 V X5R (C13585, Basic) at the input, and a non-polar RC damper across BAT_IN,
    C89 + C95 2 x 22 uF 25 V X5R 1206 (C12891, Basic) in series with R166 0.33 ohm 2512 (C25468). Same model,
    every corner: >= -12.7 V, <= 7.0 V/us (pass 4, independent model and more corners: -13.0 V, 7.3 V/us from an
    empty input; x_input_bleed covers a charged one). R166 takes up to ~1.9 mJ / 400 W per battery connection (2512: about
    1.1-1.4x Vishay's drift-based single-pulse curve at the stiffest corner, n < 1000; drift does not matter in
    a damper). No polarized capacitor may sit ahead of U9."""
    t = set_props(t, 'C80', {'Value': '10uF 50V X5R 10%', 'LCSC': 'C13585', 'LCSC Part': 'C13585',
                             'Manufacturer': 'Samsung Electro-Mechanics', 'Manufacturer Part': 'CL31A106KBHNNNE'})
    if symbol_block(t, 'C89'):
        return t
    path = sheet_path(t)
    cd = {'LCSC': 'C12891', 'LCSC Part': 'C12891', 'Manufacturer': 'Samsung Electro-Mechanics', 'Manufacturer Part': 'CL31A226KAHNNNE'}
    for ref, x in (('C89', 309.88), ('C95', 325.12)):
        t = insert(t, two_pin(ref, 'M3:C', '22uF 25V X5R 10%', 'rocket:C_1206_3216Metric', cd, x, 175.26, 'BAT_IN', 'BAT_DAMP', path))
    t = insert(t, two_pin('R166', 'M3:R', '0.33R 1% 2512', 'rocket:R2512',
                          {'LCSC': 'C25468', 'LCSC Part': 'C25468', **R0603_UNIROYAL, 'Manufacturer Part': '25121WF330LT4E'},
                          340.36, 175.26, 'BAT_DAMP', 'GND', path))
    t = insert(t, two_pin('C96', 'M3:C', '10uF 50V X5R 10%', 'rocket:C_1206_3216Metric',
                          {'LCSC': 'C13585', 'LCSC Part': 'C13585', 'Manufacturer': 'Samsung Electro-Mechanics', 'Manufacturer Part': 'CL31A106KBHNNNE'},
                          355.6, 175.26, 'BAT_IN', 'GND', path))
    return insert(t, note('C80 + C96 (2 x 10 uF) at the input; C89 + C95 (2 x 22 uF 25 V X5R) + R166 (0.33 ohm 2512): non-polar RC damper '
                          'across BAT_IN. A reverse hot-plug through a 0.1-1 uH, >= 0.03 ohm harness keeps U9 IN >= -12.7 V and <= 7.0 V/us '
                          '(TPS25947: -15 V, 10 V/us). No polarized capacitor may sit ahead of U9.', 20.32, 224.79, 'C89:note'))


def w_usb_ov(t):
    """Power P-9: the TPS2121 OV1 divider R87/R88 tripped at 5.47-5.96 V, so a 5.5 V USB-C source could drop
    USB power. R87 44.2k 0.1 % -> 47k 1 % (C25819, Basic): trip 5.71-6.33 V with R88 10k 0.1 %."""
    return set_props(t, 'R87', {'Value': '47k 1%', 'LCSC': 'C25819', 'LCSC Part': 'C25819',
                                'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)', 'Manufacturer Part': '0603WAF4702T5E'})


C14663 = {'LCSC': 'C14663', 'LCSC Part': 'C14663', 'Manufacturer': 'YAGEO', 'Manufacturer Part': 'CC0603KRX7R9BB104'}


def w_100n_basic(refs):
    """DFM M3: the 100 nF 50 V 0603 line C1591 (Samsung, Extended) carries a 1433-piece JLC minimum purchase
    (about $9 per order). Yageo CC0603KRX7R9BB104 (C14663) is the same value, rating, dielectric and size
    and is a Basic part. C128/C140 take the soft-termination part instead (w_pyro_drain_caps)."""
    def edit(t):
        for ref in refs:
            t = set_props(t, ref, {'Value': '100nF 50V X7R 10%', **C14663}, optional=('LCSC Part',))
        return t
    edit.__name__ = 'w_100n_basic'
    return edit


R10K_BASIC = {'Value': '10k 1%', 'LCSC': 'C25804', 'LCSC Part': 'C25804', **R0603_UNIROYAL, 'Manufacturer Part': '0603WAF1002T5E'}


def w_10k_basic(refs):
    """Cost (M3): nine 10k 0.1 % thin-film parts (C95204, Extended, $0.033) were pull-ups, pull-downs, a bleed and
    the lower leg of the USB OV divider; none needs 0.1 %. Basic 10k 1 % 0603 (C25804): -$0.28 per board and one
    extended code (and its JLC loading fee) fewer. The USB OV trip becomes 5.66-6.37 V with R87 and R88 at 1 %."""
    def edit(t):
        for ref in refs:
            t = set_props(t, ref, R10K_BASIC)
        return t
    edit.__name__ = 'w_10k_basic'
    return edit


def w_pyro_drain_caps(t):
    """Actuators F4: C128/C140 (100 nF, PYRO*_OUT to GND) bypass the firing FET if they short, and an MLCC flex
    crack usually fails short. Murata GCJ188R71H104KA12D (C161115), the same value, rating and land with soft
    (resin) terminations, so board flex cracks the termination open instead. Kept: they cap the turn-off
    kick of the igniter lead inductance (about 27 V, below the 30 V AON7524 rating)."""
    for ref in ('C128', 'C140'):
        t = set_props(t, ref, {'Value': '100nF 50V X7R 10%', 'LCSC': 'C161115', 'LCSC Part': 'C161115', 'Manufacturer': 'Murata',
                               'Manufacturer Part': 'GCJ188R71H104KA12D'}, optional=('LCSC Part',))
    return t


def add_props(t, ref, props):
    """Add properties a symbol lacks (hidden, at the symbol position), keeping the field set equal to the PCB's."""
    s, e = symbol_block(t, ref)
    blk = t[s:e]
    x, y = re.search(r'\(at ([\d.]+) ([\d.]+) \d+\)', blk).groups()
    k = blk.rindex('\t\t(property ')
    k = blk.index('\n\t\t(', k + 1) + 1
    add = ''.join(prop(n, v, float(x), float(y)) for n, v in props.items() if f'(property "{n}"' not in blk)
    return t[:s] + blk[:k] + add + blk[k:] + t[e:]


def w_u8(t):
    """DFM M1 / system 5: U8 AP63300WU-7 (C2158012) had 5 in stock at JLC, exactly 5 boards, with a 17-piece
    minimum purchase. AP63301WU-7 (C2158003, 5107 in stock) is the same die and pinout in forced PWM; Table 1
    of the shared AP63300/AP63301 datasheet gives the same external parts. The camera load (0.2-1 A) keeps
    it out of the light-load range where the two differ."""
    t = set_props(t, 'U8', {'Value': 'AP63301WU-7', 'LCSC': 'C2158003'})
    # pass 3 (system m6): the board carried the old Manufacturer Part (AP63300WU-7) into the BOM; both sides now agree
    t = add_props(t, 'U8', {'Manufacturer': 'Diodes Incorporated', 'Manufacturer Part': 'AP63301WU-7'})
    return set_props(t, 'U8', {'Manufacturer': 'Diodes Incorporated', 'Manufacturer Part': 'AP63301WU-7'})


def w_servo_note(t):
    """Actuators note N-b: "stall <= 3 A per pin" read as a servo limit; 3 A is the header contact's rating
    (maker, no datasheet; MARGIN_PRESCRIPTION), while F4 sizes the copper for 1.92 A per servo, 7.7 A for four."""
    return replace_note(t, 'J122 column-major:', 'J122 column-major: 1/4/7/10 = SIGNAL 1-4, 2/5/8/11 = RAW_ACT (+), 3/6/9/12 = GND. '
                        'HV servos only: stall <= 1.92 A each, <= 7.7 A for all four (REQUIREMENTS F4); the header contact '
                        'is rated 3 A (maker, no datasheet).')


def w_cam_sense_note(t):
    """Sensors pass 3: the CAM_5V_SENSE note still used the old 15.4 V TVS clamp; D8 SMBJ12CA clamps at 19.9 V."""
    return t.replace('even 15.4 V (TVS clamp, failed regulator) reads 1.40 V.', 'even 19.9 V (TVS clamp, failed regulator) reads 1.81 V.')


def x_input_bleed(t):
    """Power F-1 (pass 4): with the switch open only U9's shutdown current and R82 + R83 (2.28 Mohm) drained BAT_IN,
    so after an unplug the input kept most of 8.4 V for minutes. A reversed pack plugged in meanwhile starts the
    harness ring from up to +8.4 V instead of 0 V: U9 IN reached -17 V and 15 V/us through a stiff harness, past
    the TPS25947's -15 V and 10 V/us. From <= 2.0 V left on the input every corner stays inside. R167 10k 1 %
    (C25804, a Basic line already on the BOM) from BAT_IN to GND brings 8.5 V down to 2.0 V in <= 0.73 s, faster
    than a pack can be pulled and plugged back reversed. It draws 0.84 mA from a connected pack (1.3 mA, 16 mW at
    12.6 V). R166 (pass 4, power F-7) moves to UNI-ROYAL's own 2512 land (rocket:M3_R2512_UR)."""
    t = set_props(t, 'R166', {'Footprint': 'rocket:M3_R2512_UR'})
    if symbol_block(t, 'R167'):
        return t
    fields = {k: v for k, v in R10K_BASIC.items() if k != 'Value'}
    t = insert(t, two_pin('R167', 'M3:R', '10k 1%', 'rocket:R_0603_1608Metric', fields, 309.88, 195.58, 'BAT_IN', 'GND',
                          sheet_path(t)))
    return replace_note(t, 'C80 + C96 (2 x 10 uF) at the input;', BLEED_NOTE)


R_FILTERS = ('(property "ki_fp_filters" "R0402 R0805 R_0603_1608Metric R2512"',
             '(property "ki_fp_filters" "R0402 R0805 R_0603_1608Metric R2512 M3_R2512_UR"')


def x_r_filter(t):
    """R166's new land (pass 4) is outside the M3:R symbol's footprint filters (ERC footprint_filter, DRC parity).
    The same text edit goes into kilib/m3.kicad_sym and every sheet's embedded copy, so they stay identical."""
    return t.replace(*R_FILTERS)


BLEED_NOTE = ('C80 + C96 (2 x 10 uF) at the input; C89 + C95 (2 x 22 uF 25 V X5R) + R166 (0.33 ohm 2512): non-polar RC damper '
              'across BAT_IN; R167 (10k) bleeds the input below 2 V within 0.73 s of an unplug (about 1.3 s with the switch closed: wait 2 s). A reverse hot-plug through a '
              '0.1-2 uH, >= 0.03 ohm harness, from <= 2 V left on the input, keeps U9 IN >= -14.6 V and <= 9.2 V/us '
              '(TPS25947: -15 V, 10 V/us). No polarized capacitor may sit ahead of U9.')


def y_drop_tp124(t):
    """Actuators F3 (pass 5): TP124, a bare GND test pad at (17.9, 58.0), sat 1.15-1.22 mm from R134.1 and R135.1,
    the bare igniter-side pads of the 2 ohm series resistors. A probe slip while armed shorts an igniter net to GND:
    up to 4.2 A through a 2 W resistor, below the 5 A link fuse, so nothing clears it. GND stays reachable at TP88
    and J2 pin 1. The symbol goes with its wire and GND label."""
    if not symbol_block(t, 'TP124'):
        return t
    s, e = symbol_block(t, 'TP124')
    t = t[:s - 1] + t[e:]
    t, _ = drop_block_at(t, 'wire', ('449.58', '241.3'))
    t, _ = drop_block_at(t, 'global_label', ('449.58', '246.38'))
    return t


def y_u5_mpn(t):
    """Pass 5: U5 carried only its LCSC code; the BOM now gives the maker and part number too (JLC/LCSC model name
    for C15639). (Pass 5 also made U5 and LS120 owner-fitted because JLC Economic reflows at 255 +/- 5 C, above their
    250 C limits; pass 6 reverted that: TE's AN808 forbids hand soldering the MS5611, and the order moves to Standard
    PCBA, 240 +/- 5 C, which keeps every part inside its maker's reflow limit. docs/M3_R4.md Z4, AA1.)"""
    return add_props(t, 'U5', {'Manufacturer': 'TE Connectivity', 'Manufacturer Part': 'MS561101BA03-50'})


# --- validation pass 9 (docs/M3_R4.md section 1j) ----------------------------------------------

SENSE_SERIES = (('R168', 'PYRO1_CONT', '80.01'), ('R169', 'PYRO2_CONT', '82.55'),
                ('R170', 'ARM1_SENSE', '107.95'), ('R171', 'ARM2_SENSE', '105.41'), ('R172', 'RAW_ACT_SENSE', '110.49'))
SENSE_NOTE = ('R168-R172 (R4): 4.7k between each sense divider and its ADC pin: PYRO1/2_CONT -> PC0/PC1, ARM1/2_SENSE -> PC5/PC4, '
              'RAW_ACT_SENSE -> PB0.\\nThe dividers (2 x 5.1k in series over 2 x 2k in parallel, passes 11-12) keep each node <= 1.4 V '
              '(3.3 V at the 19.9 V clamp) with any one part shorted or open;\\nthese 4.7k limit the current only if two faults coincide '
              '(about 1 mA, Inference). ADC source 5.6 kohm (Table 184: 10-bit limit 5.65 kohm): long sample time.')


def z_sense_series(t):
    """Actuators F1 (pass 9): each pyro sense divider's 10k top resistor (R129/R141 from the drain, R132/R144 from the
    bus) was the only part between armed copper and an MCU analog pin. Shorted, it put the drain or the bus straight on
    PC0/PC1/PC5/PC4 with nothing to limit the current: on the drain side the igniter sits in that path (tens to hundreds
    of mA if the pin conducts into VDDA, Inference), on the bus side the MCU is overstressed while armed. A 4.7k at each
    pin limits whatever flows to about 1.0 mA (3.5 mA at the 19.9 V TVS clamp) if the pin conducts near VDDA; the pin
    is still driven past its ratings (DS12110: positive injection +0 mA on FT and TT pins, TT_a 4.0 V absolute maximum),
    so this limits the damage rather than preventing it (Inference: ST does not say how a pin behaves there). The
    igniter carries at most the divider's 1k leg plus that, about 9.4 mA. R172 (pass 10) does the same for PB0: a shorted
    R124 put stiff RAW_ACT on it, before arming or, if the board powers up armed (FMEA H-6(b)), while armed.
    4.7k rather than 10k keeps the ADC source (4.7k + 10k || 1k = 5.6 kohm nominal) at DS12110 Table 184's 10-bit RAIN
    limit (5.65 kohm at TJ = 125 C; 10k would leave only the 8-bit limit). C25900 is a Basic line already on the BOM
    (R12/R13). The labels at the MCU pins become the *_MCU nets; the divider side keeps its name."""
    if symbol_block(t, 'R168'):
        return t
    path = sheet_path(t)
    for i, (ref, node, y) in enumerate(SENSE_SERIES):
        old = f'(global_label "{node}"\n\t\t(shape passive)\n\t\t(at 127 {y} 0)'
        assert t.count(old) == 1, (ref, node)
        t = t.replace(old, f'(global_label "{node}_MCU"\n\t\t(shape passive)\n\t\t(at 127 {y} 0)')
        t = insert(t, two_pin(ref, 'M3:R', '4.7k', 'rocket:R0402', {'LCSC': 'C25900'}, 180.34, 86.36 + 15.24 * i,
                              node, node + '_MCU', path))
    return insert(t, note(SENSE_NOTE, 20.32, 251.46, 'R168:note'))


def z_j2_no_boot0(t):
    """Sensors F-A (pass 9): BOOT0's route to J2.6 ran under J2's plastic base, 0.175 mm from J2.5 (3V3) and 0.19 mm from
    J2.4 (NRST), on a board that is not washed. Leakage there either boots the ROM loader or holds NRST low, and neither
    recovers by itself (no neutral command, no deployment); lowering R5 trades one for the other. J2.6 is now unconnected
    and R5 holds BOOT0 low at the MCU. DFU goes through SWD or a firmware jump to the system bootloader."""
    if '(global_label "BOOT0"\n\t\t(shape passive)\n\t\t(at 320.04 71.12 0)' not in t:
        return t
    t, w = drop_block_at(t, 'wire', ('325.12', '71.12'))
    assert '(xy 320.04 71.12)' in w, w
    t, lab = drop_block_at(t, 'global_label', ('320.04', '71.12'))
    assert '"BOOT0"' in lab, lab
    t = insert(t, f'\t(no_connect\n\t\t(at 325.12 71.12)\n\t\t(uuid {uid("J2", "nc", "6")}))\n')
    t = set_props(t, 'J2', {'Value': 'SWD 1x6'})
    return replace_note(t, 'J2: 1 GND | 2 SWCLK | 3 SWDIO | 4 NRST | 5 3V3 | 6 BOOT0',
                        'J2: 1 GND | 2 SWCLK | 3 SWDIO | 4 NRST | 5 3V3 | 6 n/c (R4: BOOT0 stays on R5 at the MCU; '
                        'DFU through SWD or a firmware jump to the system bootloader)')


# --- validation pass 11 (docs/M3_R4.md section 1l) ---------------------------------------------

R5K1 = {'LCSC': 'C25905'}              # 5.1k 1 % 0402, the Basic line R7/R8 already use
# existing top resistor -> (label to rename: (x, y), old net, new net), new half (ref, x, y, pin 1 net, pin 2 net)
SPLIT_PYRO = {'R129': ((332.74, 41.91), 'PYRO1_OUT', 'PYRO1_CONT_MID', ('R173', 66.04, 205.74, 'PYRO1_OUT', 'PYRO1_CONT_MID')),
              'R141': ((215.9, 168.91), 'PYRO2_OUT', 'PYRO2_CONT_MID', ('R174', 101.6, 205.74, 'PYRO2_OUT', 'PYRO2_CONT_MID')),
              'R132': ((157.48, 123.19), 'ARM1_SENSE', 'ARM1_SENSE_MID', ('R175', 137.16, 205.74, 'ARM1_SENSE_MID', 'ARM1_SENSE')),
              'R144': ((40.64, 250.19), 'ARM2_SENSE', 'ARM2_SENSE_MID', ('R176', 172.72, 205.74, 'ARM2_SENSE_MID', 'ARM2_SENSE'))}
SPLIT_NOTE = ('Pass 11: each divider top is 2 x 5.1k in series (R173 + R129, R174 + R141 from the drains; R132 + R175, R144 + R176 '
              'from the buses); pass 12: each bottom is 2 x 2k in parallel (R130 + R178, R142 + R179, R133 + R180, R145 + R181).'
              '\\nRatio 1/11.2. One shorted or open 0402 leaves its ADC node <= 1.4 V (<= 3.3 V at the 19.9 V clamp) and the '
              'igniter <= 1.4 mA; R168-R171 (4.7k at the MCU pins) stay as the second layer.')
R2K = {'LCSC': 'C4109'}                 # 2k 1 % 0402 (UNI-ROYAL 0402WGF2001TCE, Basic)
SPLIT_BOTTOM = {'R130': ('R178', 208.28, 205.74, 'PYRO1_CONT'), 'R142': ('R179', 243.84, 205.74, 'PYRO2_CONT'),
                'R133': ('R180', 279.4, 205.74, 'ARM1_SENSE'), 'R145': ('R181', 314.96, 205.74, 'ARM2_SENSE')}


def _rename_label(t, xy, old, new):
    x, y = xy
    pat = re.compile(r'\(global_label "' + re.escape(old) + r'"(\s*\(shape \w+\)\s*\(at ' + fmt(x) + ' ' + fmt(y) + ' )')
    t, n = pat.subn(lambda m: '(global_label "' + new + '"' + m.group(1), t)
    assert n == 1, (old, xy, n)
    return t


def z_split_pyro(t):
    """Pass 11 (follows pass 10's AE1): R168-R171 limit the current, but a single shorted divider top resistor still drove
    its ADC pin past DS12110's ratings (positive injection +0 mA, TT_a 4.0 V maximum). Each 10k top resistor becomes two
    5.1k in series (C25905, a Basic line already on the BOM), so no single short can lift the divider node above
    8.4 V x 1k / 6.1k = 1.38 V (3.26 V at the 19.9 V TVS clamp): inside every pin rating, with the igniter at most 1.4 mA.
    The ratio becomes 1/11.2 (0.75 V at 8.4 V, 1.78 V at the clamp) and the ADC source stays 5.6 kohm. The drain-side
    halves (R173, R174) are new; on the bus side the new halves (R175, R176) sit on the sense side.
    Pass 12 (reviewer F2): an open 1k bottom leg still let the node rise to the source through 10.2k. Each bottom becomes two
    2k in parallel (C4109, UNI-ROYAL 0402WGF2001TCE, Basic; one new BOM code), so one open leaves the node <= 1.38 V too."""
    if symbol_block(t, 'R173'):
        return t
    path = sheet_path(t)
    for ref, (xy, old, new, (nref, x, y, n1, n2)) in SPLIT_PYRO.items():
        t = set_props(t, ref, {'Value': '5.1k', **R5K1})
        t = _rename_label(t, xy, old, new)
        t = insert(t, two_pin(nref, 'M3:R', '5.1k', 'rocket:R0402', R5K1, x, y, n1, n2, path))
    for ref, (nref, x, y, node) in SPLIT_BOTTOM.items():     # pass 12: open-tolerant bottoms, 2 x 2k in parallel
        t = set_props(t, ref, {'Value': '2k', **R2K, 'LCSC Part': 'C4109'}, optional=('LCSC Part',))
        t = insert(t, two_pin(nref, 'M3:R', '2k', 'rocket:R0402', R2K, x, y, node, 'GND', path))
    t = replace_note(t, 'CONT = 10k/1k from drain', 'CONT = (2 x 5.1k)/(2 x 2k parallel) from each drain (open detector only, '
                     'CIRCUIT_REVIEW 2.9). ARMn_SENSE = the same from each fused bus.')
    return insert(t, note(SPLIT_NOTE, 40.64, 220.98, 'R173:note'))


def z_split_raw(t):
    """Pass 11, same as z_split_pyro for RAW_ACT_SENSE: R124 10k -> R177 + R124, 2 x 5.1k, so a shorted half leaves PB0's
    node <= 1.38 V (3.26 V at the clamp); with R172 (pass 10) PB0 has two layers too."""
    if symbol_block(t, 'R177'):
        return t
    t = set_props(t, 'R124', {'Value': '5.1k', **R5K1}, optional=('LCSC Part',))
    t = _rename_label(t, (215.9, 105.41), 'RAW_ACT', 'RAW_ACT_SENSE_MID')
    t = insert(t, two_pin('R177', 'M3:R', '5.1k', 'rocket:R0402', R5K1, 254.0, 83.82, 'RAW_ACT', 'RAW_ACT_SENSE_MID', sheet_path(t)))
    t = set_props(t, 'R125', {'Value': '2k', **R2K, 'LCSC Part': 'C4109'}, optional=('LCSC Part',))   # pass 12: 2 x 2k
    t = insert(t, two_pin('R182', 'M3:R', '2k', 'rocket:R0402', R2K, 279.4, 83.82, 'RAW_ACT_SENSE', 'GND', sheet_path(t)))
    return replace_note(t, 'R124/R125 10k/1k -> PB0', 'R177 + R124 (2 x 5.1k) over R125 + R182 (2 x 2k parallel) -> R172 4.7k -> PB0 '
                        '(RAW_ACT / 11.2: 0.75 V at 8.4 V, 1.78 V at the 19.9 V TVS clamp; one shorted or open part leaves PB0 <= 3.3 V): '
                        'RAW_ACT sense AND bleed (tau ~5 s with C121). Mandatory external 15 A ATO fuse in battery lead.')


def rev_r4(t):
    """Every sheet's title block: M3-ASSY-R3 -> M3-ASSY-R4."""
    return t.replace('(rev "M3-ASSY-R3")', '(rev "M3-ASSY-R4")')


EDITS = {
    'battery_entry.kicad_sch': [a1_enable_ride_through, a2_ovlo_release, m_u9_input_cap, v_input_protection, w_input_damper,
                                w_10k_basic(('R89', 'R92')), x_input_bleed],
    'usb_sense.kicad_sch': [b1_usb_detect],
    'm3.kicad_sch': [b8_3v3a_rc],
    'pyro.kicad_sch': [a3_pyro_terminals, m_note_cold_pullup, w_pyro_drain_caps, y_drop_tp124, z_split_pyro],
    'actuator_power.kicad_sch': [v_raw_act_sense, z_split_raw],
    'pullpin_buzzer.kicad_sch': [m_note_tim8, v_pullpin_jst],
    'sensors.kicad_sch': [m_imu_lsm6dsv320x, y_u5_mpn],
    'logic_power_path.kicad_sch': [w_usb_ov, w_100n_basic(('C83',)), w_10k_basic(('R88', 'R90', 'R91'))],
    'camera_power.kicad_sch': [w_100n_basic(('C71', 'C74')), w_u8, w_10k_basic(('R75', 'R76', 'R78'))],
    'camera_uart.kicad_sch': [w_100n_basic(('C90', 'C93')), w_10k_basic(('R102',))],
    'servos.kicad_sch': [w_servo_note],
    'diagnostics.kicad_sch': [w_cam_sense_note],
    'mcu.kicad_sch': [z_sense_series, z_j2_no_boot0],
}


def main():
    lib = D / 'kilib' / 'm3.kicad_sym'
    lt = lib.read_text()
    if R_FILTERS[1] not in lt:
        assert lt.count(R_FILTERS[0]) == 1
        lib.write_text(x_r_filter(lt))
        print('edited kilib/m3.kicad_sym [x_r_filter]')
    for f in sorted(D.glob('*.kicad_sch')):
        EDITS.setdefault(f.name, [])
        if rev_r4 not in EDITS[f.name]:
            EDITS[f.name].append(rev_r4)
        if R_FILTERS[0] in f.read_text() and x_r_filter not in EDITS[f.name]:
            EDITS[f.name].append(x_r_filter)
    for name, fns in EDITS.items():
        f = D / name
        t0 = f.read_text()
        t = t0
        for fn in fns:
            t = fn(t)
        if t != t0:
            f.write_text(t)
            print('edited', name, [fn.__name__ for fn in fns])
        else:
            print('unchanged', name)


if __name__ == '__main__':
    main()
