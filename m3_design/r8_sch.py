#!/usr/bin/env python3
"""Reproducible R7 -> R8 schematic transform (M3-ASSY-R8; sources/r8_design/R8_DECISIONS.md D2-D4, D7, D8, D14).

usage: python3 m3_design/r8_sch.py [project_dir] [--netlist]
The input is the committed R7 project (431025d); a second run changes nothing. --netlist also regenerates
schematic.net.xml with kicad-cli (local path made relative and the date blanked, as r7_sch.py does).
Verification: <KiCad python3> -I m3_design/r8_sch_check.py (ERC, the netlist diff against R7, RF / safety
separation, check_actuators and check_r8's pin contract on the R8 netlist, schematic parity).

1. MCU sheet: U1 re-pinned from sources/r8_design/pin_table.tsv, the R8 pin contract (every row whose r8_net differs
   from its r7_net; D2, D3). Each U1 pin reaches a global label through a short wire (the R7 sheet style):
   - a pin that keeps a net gets the new label text in place (same wire, position and UUID);
   - a freed pin loses its wire and label and gets a no-connect flag at the pin end;
   - a moved-in pin loses its no-connect flag and gets a 5.08 mm wire and a global label.
   A moved label keeps the shape the net's R7 label had on this sheet. Every pin's state is asserted first: a changed
   row must show its R7 or its R8 net (idempotence), an unchanged row its R7 net; the safety-contract pins (D14) and the
   pyro sentinels stay untouched.
2. Telemetry sheet: R310.1 moves from 3V3_RADIO to 3V3 (D4; R310 sits at the MCU end of the NSS lane on the board).
3. Sheet notes that name moved pins are rewritten (MCU, telemetry, camera UART, USB sense, pull-pin and buzzer); the
   MCU sheet gains the follow-on and loader-pin notes and the servo sheet records D7.
4. Every sheet: rev M3-ASSY-R8.
Not changed: D121's nets (D7 keeps the pass-5 channel map; check_actuators 7c); TH1-TH3 are board-only footprints, not
schematic parts (D8, asserted here). The sheet-15 name keeps its "(R7)" tag: it is the sheet's identity in the netlist
and in the board's footprint sheet paths, so renaming it would only add noise to the netlist diff and the board.
"""
import csv
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r7_sch as r7     # noqa: E402 (R7 helpers, unchanged: parser access, pin geometry, netlist export)

NS = uuid.UUID('5146a5a1-7b63-5ab0-be2a-153453666d51')    # fixed namespace -> stable R8 UUIDs
REV_OLD, REV = 'M3-ASSY-R7', 'M3-ASSY-R8'
PIN_TABLE = Path(__file__).resolve().parent / 'assembly_review/sources/r8_design/pin_table.tsv'
# D14: these pins keep their R7 nets (gate flanked by sentinels, CONT, servos, ARM / RAW senses, PE10, PE0, PE1)
CONTRACT_PINS = ('2', '3', '4', '5', '15', '16', '22', '23', '24', '25', '32', '33', '34', '40', '97', '98')
R310 = ('R310', '1', '3V3_RADIO', '3V3')                  # D4: ref, pin, R7 net, R8 net
WIRE = 5.08


def uid(*key):
    return str(uuid.uuid5(NS, ':'.join(key)))


def glabel(net, x, y, angle, justify, shape, key=None, uuid_=None):
    return (f'\t(global_label "{net}"\n\t\t(shape {shape})\n\t\t(at {r7.fmt(x)} {r7.fmt(y)} {angle})'
            f'\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.05 1.05))\n\t\t\t(justify {justify}))'
            f'\n\t\t(uuid {uuid_ or uid(key)}))\n')


def wire(x1, y1, x2, y2, key):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {r7.fmt(x1)} {r7.fmt(y1)})\n\t\t\t(xy {r7.fmt(x2)} {r7.fmt(y2)}))\n'
            f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default))\n\t\t(uuid {uid(key)}))\n')


def nc(x, y, key):
    return f'\t(no_connect\n\t\t(at {r7.fmt(x)} {r7.fmt(y)})\n\t\t(uuid {uid(key)}))\n'


def note(textline, x, y, key, size):
    return (f'\t(text "{textline}"\n\t\t(at {r7.fmt(x)} {r7.fmt(y)} 0)\n\t\t(effects\n\t\t\t(font'
            f'\n\t\t\t\t(size {size} {size}))\n\t\t\t(justify left))\n\t\t(uuid {uid(key)}))\n')


def load_changes(path=PIN_TABLE):
    """{pin: (r7 net, r8 net)} for every U1 pin ('NC' = no net), and the changed subset; the table is checked first."""
    with open(path, newline='') as fh:
        rows = list(csv.DictReader(fh, delimiter='\t'))
    pins = {r['pin']: (r['r7_net'], r['r8_net']) for r in rows}
    assert sorted(pins, key=int) == [str(n) for n in range(1, 101)], 'pin table must list pins 1-100 once each'
    for r in rows:
        assert (r['change'] == 'unchanged') == (r['r7_net'] == r['r8_net']), f"pin {r['pin']}: change column"
    for pin in CONTRACT_PINS:
        assert pins[pin][0] == pins[pin][1], f'U1.{pin} is a safety-contract pin (D14) and must keep its R7 net'
    changed = {p: v for p, v in pins.items() if v[0] != v[1]}
    moved_nets = {v[1] for v in changed.values() if v[1] != 'NC'}
    r7_nets = {v[0] for v in pins.values()}
    assert moved_nets <= r7_nets, f'new nets on U1: {sorted(moved_nets - r7_nets)} (R8 only moves R7 nets)'
    return pins, changed


# ---------------------------------------------------------------------------------------------------------
# MCU sheet


def _index(t):
    """Parsed sheet: no-connect nodes, global labels and two-point wires by end point."""
    read, _, _ = r7._reader()
    root = read(t)
    ncs = {r7._xy(n): n for n in root.children('no_connect')}
    labels = {}
    for n in root.children('global_label'):
        labels.setdefault(r7._xy(n), []).append(n)
    wires = []
    for n in root.children('wire'):
        pts = [tuple(round(float(a.atom), 2) for a in p.items[1:3]) for p in n.children('pts')[0].children('xy')]
        wires.append((n, pts))
    return ncs, labels, wires


def _label_attrs(t, node):
    """(name, shape, x, y, angle, justify, uuid) of a global label node."""
    shape = node.children('shape')[0].items[1].atom
    at = node.children('at')[0].items
    x, y, a = (float(v.atom) for v in at[1:4])
    eff = node.children('effects')[0]
    just = eff.children('justify')
    return (node.items[1].atom, shape, x, y, int(a), just[0].items[1].atom if just else None,
            node.children('uuid')[0].items[1].atom)


def pin_state(t, index, pt):
    """('NC', nc node) or (net, (wire node, label node)) for the pin end pt; asserts the R7 single-wire style."""
    ncs, labels, wires = index
    at_pin = [(n, pts) for n, pts in wires if pt in pts]
    if pt in ncs:
        assert not at_pin, f'pin at {pt}: no-connect flag and a wire'
        return 'NC', ncs[pt]
    assert len(at_pin) == 1 and len(at_pin[0][1]) == 2, f'pin at {pt}: expected one short wire'
    w, pts = at_pin[0]
    end = pts[1] if pts[0] == pt else pts[0]
    assert sum(end in p for _, p in wires) == 1, f'pin at {pt}: branched wire'
    lab = labels.get(end, [])
    assert len(lab) == 1, f'pin at {pt}: expected one global label at {end}, found {len(lab)}'
    return lab[0].items[1].atom, (w, lab[0])


def t_mcu(t, lt, pins, changed):
    """Section 1: U1's pins from the pin table."""
    _, patch, _ = r7._reader()
    pts = r7._mcu_points(t, lt)                              # asserts U1 at its R7 sheet position
    index = _index(t)
    state = {num: pin_state(t, index, pts[num][:2]) for num in pts}
    assert set(state) == set(pins), 'U1 symbol pins differ from the pin table'
    shape = {}                                               # the shape of each net's R7 label on this sheet
    for num, (net, nodes) in state.items():
        if net != 'NC':
            shape[net] = _label_attrs(t, nodes[1])[1]
    for num, (old, new) in pins.items():
        now = state[num][0]
        if num in changed:
            assert now in (old, new), f'U1.{num}: found {now!r}, expected R7 {old!r} or R8 {new!r}'
        else:
            assert now == old, f'U1.{num}: found {now!r}, the pin table keeps {old!r}'
    edits, chunks = [], []
    for num in sorted(changed, key=int):
        old, new = changed[num]
        now, nodes = state[num]
        if now == new:
            continue
        x, y, a = pts[num]
        if old != 'NC' and new != 'NC':                      # label text in place
            name, shp, lx, ly, la, just, u = _label_attrs(t, nodes[1])
            edits.append((nodes[1].start, nodes[1].end,
                          glabel(new, lx, ly, la, just, shape.get(new, shp), uuid_=u).strip()))
        elif new == 'NC':                                    # freed: wire and label out, no-connect flag in
            w, lab = nodes
            edits += [(w.start, w.end, ''), (lab.start, lab.end, '')]
            chunks.append(nc(x, y, f'U1:nc{num}'))
        else:                                                # moved in: no-connect flag out, wire and label in
            edits.append((nodes.start, nodes.end, ''))
            right = a == 180
            bx = round(x + (WIRE if right else -WIRE), 2)
            chunks.append(wire(x, y, bx, y, f'U1:w{num}') +
                          glabel(new, bx, y, 180 if right else 0, 'left' if right else 'right',
                                 shape.get(new, 'passive'), key=f'U1:l{num}'))
    if edits:
        t = patch(t, edits)
    if chunks:
        t = r7.insert(t, ''.join(chunks))
    after = _index(t)
    for num, (old, new) in pins.items():                     # the whole map once more, after the edit
        assert pin_state(t, after, pts[num][:2])[0] == new, f'U1.{num}: not {new} after the edit'
    for num in r7.PYRO_SENTINELS:
        assert pins[num][1] == 'NC', f'pyro sentinel U1.{num} must stay without a net'
    return t


# ---------------------------------------------------------------------------------------------------------
# telemetry sheet


def t_r310(t, lt):
    """Section 2: R310 pin 1 to 3V3 (the label text in place)."""
    ref, num, old, new = R310
    _, patch, _ = r7._reader()
    assert t.count(f'(property "Reference" "{ref}"') == 1, f'{ref} symbol not found once'
    s, e = r7.symbol_block(t, ref)
    m = re.match(r'\t\(symbol\n\t\t\(lib_id "M3:R"\)\n\t\t\(at ([\d.]+) ([\d.]+) 0\)', t[s - 1:e])
    assert m, f'{ref}: expected an M3:R symbol at rotation 0'
    X, Y = float(m.group(1)), float(m.group(2))
    px, py, _ = r7._lib_pins(lt, 'R')[num]
    pt = (round(X + px, 2), round(Y - py, 2))
    now, nodes = pin_state(t, _index(t), pt)
    assert now in (old, new), f'{ref}.{num}: found {now!r}, expected {old!r} or {new!r}'
    if now == old:
        name, shp, lx, ly, la, just, u = _label_attrs(t, nodes[1])
        t = patch(t, [(nodes[1].start, nodes[1].end, glabel(new, lx, ly, la, just, shp, uuid_=u).strip())])
    assert pin_state(t, _index(t), pt)[0] == new
    return t


# ---------------------------------------------------------------------------------------------------------
# notes

NOTES = {   # sheet -> [(R7 text, R8 text)]: each R7 note that names a moved pin, rewritten in place (same UUID)
    'mcu.kicad_sch': [
        ('Added PD3 / pin84: camera enable. PD4 / pin85: fault input; no actuation changes.',
         'R8: camera enable CAM_PWR_EN on PE12 / pin42, fault input CAM_FAULT_N on PE11 / pin41 (GPIO only, SPI4 '
         'never enabled); no actuation changes.'),
        ('R2: PE3 (pin 2) and PE6 (pin 5) are pyro-gate sentinels - no net, firmware drives them low. LED_RED moved '
         'to PE8.',
         'R2: PE3 (pin 2) and PE6 (pin 5) are pyro-gate sentinels - no net, firmware drives them low. R8: LED_RED on '
         'PD5 (pin 86), LED_YEL on PD7 (pin 88).'),
        ('IMU INT1: PE1 polled input only. EXTI1 remains PD1 power status. PE10 NC; pyro sentinels unchanged.',
         'IMU INT1: PE1 polled input only. R8 EXTI: 4 BAT_FAULT_N PA4, 5 LOGIC_SOURCE_ST PA5, 6 USB_FAULT_N PD6, '
         '8 VBUS_SENSE PC8, 11 CAM_FAULT_N PE11, 14 PULLPIN PC14, 15 RADIO_DIO1 PE15. PE10 NC; pyro sentinels '
         'unchanged.'),
        ('R7 (sheet 15): radio SPI2 PB12 NSS, PB13 SCK, PB14 MISO, PB15 MOSI; PD8 BUSY, PD9 NRST, PD10 DIO1, PE15 '
         'RXEN. GNSS USART6 PC6/PC7, PC8 RESET_N (open drain), PD14 TIMEPULSE. PA7, PC9, PA8, PA9, PA10 NC.',
         'R8 (sheet 15): radio SPI2 PB10 SCK, PB11 NSS (software; R310 100k to 3V3), PB14 MOSI / PB15 MISO (AF5 '
         'with SPI_CFG2.IOSWP = 1); PD8 BUSY (polled), PD9 RXEN, PE9 NRST, PE15 DIO1. GNSS USART6 PC6/PC7, PD14 '
         'RESET_N (open drain), PD15 TIMEPULSE (TIM4_CH4).'),
    ],
    'telemetry.kicad_sch': [
        ('GNSS on USART6: PC6 TX -> R306 220R -> RXD; TXD -> R305 220R -> PC7 RX. PC8 drives RESET_N open-drain (no '
         'pull, no capacitor). TIMEPULSE -> R307 1k -> PD14, never pulled down (SAFEBOOT_N shares it).',
         'GNSS on USART6: PC6 TX -> R306 220R -> RXD; TXD -> R305 220R -> PC7 RX. PD14 drives RESET_N open-drain (no '
         'pull, no capacitor). TIMEPULSE -> R307 1k -> PD15 (TIM4_CH4 capture), never pulled down (SAFEBOOT_N shares '
         'it). R8 pins.'),
        ('Radio on SPI2: PB12 NSS (R310 100k to 3V3_RADIO), PB13 SCK / PB15 MOSI / PB14 MISO through R313 / R315 / '
         'R314 33R. PD8 BUSY, PD9 NRST (R311 2.0k to GND), PD10 DIO1 (EXTI10), PE15 RXEN (R312 100k to GND), TXEN = '
         'DIO2.',
         'Radio on SPI2 (R8): PB11 NSS, software (R310 100k to 3V3, at the MCU end), PB10 SCK / PB14 MOSI / PB15 MISO '
         'through R313 / R315 / R314 33R; PB14/PB15 swap by SPI_CFG2.IOSWP = 1, set while SPE = 0 before AF5. PD8 '
         'BUSY (polled), PE9 NRST (R311 2.0k to GND), PE15 DIO1 (EXTI15), PD9 RXEN (R312 100k to GND), TXEN = DIO2.'),
        ('MCU in reset or ROM bootloader: R311 holds the radio in reset (it cannot transmit), NSS high, RXEN low, TXEN '
         'low (DIO2 pulled down in reset); the GNSS keeps tracking. PA7, PC9, PA8, PA9, PA10 NC; pyro sentinels '
         'unchanged.',
         'MCU in reset or ROM bootloader: R311 holds the radio in reset (it cannot transmit), NSS high (the loader '
         'never selects USART3 on PB10/PB11; PB10 and PB14 drive only the held radio\'s inputs), RXEN low, TXEN low '
         '(DIO2 pulled down in reset); the GNSS keeps tracking. PA6, PA8, PA9, PA10, PC9, PC11, PE13 NC; pyro '
         'sentinels unchanged.'),
    ],
    'camera_uart.kicad_sch': [
        ('PB10/pin46 USART3_TX and PB11/pin47 USART3_RX use AF7. PC13/pin7 controls OE as GPIO.',
         'R8: PE8/pin38 UART7_TX and PE7/pin37 UART7_RX use AF7, no flow control (never AF7 on PE9 or PE10); off the '
         'ROM loader\'s USART3. PA7/pin31 controls OE as GPIO.'),
    ],
    'usb_sense.kicad_sch': [
        ('PD15 / U1 pin62 is a regular FT_h GPIO input. PA9 remains NC. D+/D- are unchanged.',
         'PC8 / U1 pin65 (R8) is a regular FT_h GPIO input (EXTI8). PA9 remains NC. D+/D- are unchanged.'),
        ('R9 = R110 = 1k (R4): PD15 <= 1.01 V when D4 back-feeds VBUS with the D+ pull-up on, 2.18 V at VBUS 4.40 V. '
         'TP92 measures their junction. No internal pull-up/down.',
         'R9 = R110 = 1k (R4): PC8 <= 1.01 V when D4 back-feeds VBUS with the D+ pull-up on, 2.18 V at VBUS 4.40 V. '
         'TP92 measures their junction. No internal pull-up/down.'),
        ('Use software attach/detach from PD15. Do NOT enable native PA9 VBUS sensing (VBDEN).',
         'Use software attach/detach from PC8. Do NOT enable native PA9 VBUS sensing (VBDEN).'),
    ],
    'pullpin_buzzer.kicad_sch': [
        ('BUZZ_DRV = PA5 (pin 29). MLT-5020: 4 kHz, 50% duty; software toggle or TIM8_CH1N (AF3). Never leave the coil '
         'driven with DC.',
         'BUZZ_DRV = PC13 (pin 7, R8). MLT-5020: 4 kHz, 50% duty; software toggle only (PC13 has no timer AF; '
         'backup-domain pin, <= 2 MHz, no RTC output on it). Never leave the coil driven with DC.'),
    ],
}
NEW_NOTES = {   # sheet -> [(key, text, x, y, font size)]: R8 notes added in free sheet space, in the size of the notes
               # beside them (MCU: the 1.05 mm R7/R8 radio note; servos: the sheet's 1.27 mm notes)
    'mcu.kicad_sch': [
        ('mcu:followon', 'R8 follow-on moves (D3): BUZZ_DRV PC13, BAT_FAULT_N PA4, LOGIC_SOURCE_ST PA5, CAM_UART_OE '
         'PA7, camera UART7 PE7 RX / PE8 TX, CAM_FAULT_N PE11, CAM_PWR_EN PE12, VBUS_SENSE PC8, LEDs PD5 / PD7. '
         'Freed, NC: PB12, PB13, PD10, PD0, PD1, PD3, PD4.', 20.32, 264.16, 1.05),
        ('mcu:loader', 'Pins the ROM bootloader drives (AN2606 Table 135; D5) carry only SERVO3 PA2, RADIO_SCK PB10, '
         'RADIO_MOSI PB14, USB PA11/PA12, QSPI_NCS PB6 and I2C1_SDA PB9; PA6, PA8, PA9, PA10, PC9, PC11, PE13 stay '
         'NC.', 20.32, 269.24, 1.05),
    ],
    'servos.kicad_sch': [
        ('servos:d121', 'R8 (D7): D121 keeps the pass-5 channel map (pins 1/3/4/6 = SERVO1-4_MCU, 2 GND, 5 3V3); on '
         'the board it sits on the bottom side, on the U1-ordered servo lanes ahead of their reversal into J122\'s row '
         'order.', 20.32, 275.48, 1.27),
    ],
}


def t_notes(name, t):
    """Section 3: R7 notes rewritten in place, R8 notes added once."""
    for old, new in NOTES.get(name, ()):
        assert '"' not in new and '\\' not in new
        o, n = f'(text "{old}"', f'(text "{new}"'
        if t.count(n) == 1 and o not in t:
            continue
        assert t.count(o) == 1 and n not in t, f'{name}: note not found once: {old[:60]}...'
        t = t.replace(o, n)
    for key, text, x, y, size in NEW_NOTES.get(name, ()):
        assert '"' not in text and '\\' not in text
        block = note(text, x, y, key, size)
        if block in t:
            assert t.count(block) == 1
            continue
        assert f'(uuid {uid(key)})' not in t, f'{name}: note {key} present in another form: restore the R7 sheets'
        t = r7.insert(t, block)
    return t


# ---------------------------------------------------------------------------------------------------------


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    project = Path(args[0]) if args else Path(__file__).resolve().parent / 'assembly_review'
    lt = (project / 'kilib' / 'm3.kicad_sym').read_text()
    pins, changed = load_changes()
    edits = {'mcu.kicad_sch': lambda t: t_mcu(t, lt, pins, changed),
             'telemetry.kicad_sch': lambda t: t_r310(t, lt)}
    sheets = sorted(project.glob('*.kicad_sch'))
    assert len(sheets) == 15, f'expected the 15 R7 sheets, found {len(sheets)}'
    for f in sheets:
        original = f.read_text()
        assert not re.search(r'\(property "Reference" "TH\d+"', original), f'{f.name}: TH parts are board-only (D8)'
        text = edits.get(f.name, lambda t: t)(original)
        text = t_notes(f.name, text)
        text = text.replace(f'(rev "{REV_OLD}")', f'(rev "{REV}")')
        assert text.count(f'(rev "{REV}")') == 1, f'{f.name}: one title block with rev {REV}'
        text = re.sub(r'\n(?:\s*\n)+', '\n', text)          # removed blocks otherwise leave blank lines
        if text != original:
            f.write_text(text)
            print('edited', f.name)
    if '--netlist' in sys.argv:
        r7.export_netlist(project)
    moved_in = sum(1 for o, n in changed.values() if o == 'NC')
    freed = sum(1 for o, n in changed.values() if n == 'NC')
    print(f'R8 schematic: {len(changed)} U1 pins changed ({len(changed) - moved_in - freed} reassigned, {moved_in} '
          f'moved in, {freed} freed), {R310[0]}.{R310[1]} {R310[2]} -> {R310[3]}, rev {REV}')


if __name__ == '__main__':
    main()
