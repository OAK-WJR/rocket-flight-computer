#!/usr/bin/env python3
"""R10 CAD contract. --stage functional/placement are explicitly incomplete build gates.

The full stage also requires routed-reference, fit, plate and assembly-list evidence.
No R9 pyro-spacing or RF-strip rule is inherited. Physical/firmware qualification is separate.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'quality_audit'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_actuators as actuators
from sexpr import read, properties

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
MCU = {'63': 'GPS_TX_MCU', '64': 'GPS_RX_MCU', '82': 'RADIO_TX_MCU', '81': 'RADIO_RX_MCU',
       '61': 'GPS_PWR_EN', '57': 'GPS_FAULT_N', '39': 'GPS_UART_OE',
       '56': 'RADIO_PWR_EN', '45': 'RADIO_FAULT_N', '55': 'RADIO_UART_OE'}
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
            ('CAM', 'U402', 430, 'PORT_5V3', 'CAM_5V', '22.6k 1%', 'C185349', ('42', '41')),
            ('GPS', 'U410', 410, 'PORT_4V8', 'GPS_4V8', '100k 1%', 'C14675', ('61', '57')),
            ('RADIO', 'U420', 420, 'PORT_4V8', 'RADIO_4V8', '66.5k 1%', 'C137691', ('56', '45'))):
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


def functional(text):
    issues = actuators.check(text, profile='r10') + population(text)
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
    expected_mcu.update({pin: 'NC' for pin in ('46', '47', '53', '54', '62')})
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


def arm_gap(board):
    """Actual RAW/BUS copper at J124, including its own pads and adjoining tracks/vias/fill.

    Clip to the terminal pad-field bounding box + 1.5 mm. Never exempt same-part pairs.
    """
    import pcbnew
    import check_r8 as geometry
    import pyro_probe
    f = board.FindFootprintByReference('J124')
    if f is None:
        return ['J124 missing'], {}
    pads = [p for p in f.Pads() if p.GetNumber() in ('1', '2')]
    if len(pads) != 2 or {p.GetNetname() for p in pads} != {'RAW_ACT', 'PYRO1_BUS'}:
        return ['J124 requires one RAW_ACT and one PYRO1_BUS pad'], {}
    boxes = [p.GetBoundingBox() for p in pads]
    grow = pcbnew.FromMM(1.5)
    bounds = (min(b.GetLeft() for b in boxes) - grow, min(b.GetTop() for b in boxes) - grow,
              max(b.GetRight() for b in boxes) + grow, max(b.GetBottom() for b in boxes) + grow)
    window = pcbnew.SHAPE_POLY_SET(); window.NewOutline()
    for x, y in ((bounds[0], bounds[1]), (bounds[2], bounds[1]), (bounds[2], bounds[3]), (bounds[0], bounds[3])):
        window.Append(x, y)
    items = []
    for item in geometry.net_items(board, lambda n: n in ('RAW_ACT', 'PYRO1_BUS')):
        poly = pyro_probe._poly(item)
        poly.BooleanIntersection(window)
        if poly.OutlineCount():
            items.append((*item[:3], poly))
    closest = None
    for a in items:
        for b in items:
            if a[1] != 'RAW_ACT' or b[1] != 'PYRO1_BUS' or a[2] != b[2]:
                continue
            gap = geometry.min_gap(a[3], b[3], 10)
            if gap is not None and (closest is None or gap < closest[0]):
                closest = gap, a[0], b[0], board.GetLayerName(a[2])
    issues = [] if closest is not None and closest[0] >= 1.5 else ['J124 RAW_ACT–PYRO1_BUS copper gap must be >=1.5 mm']
    return issues, {'closest': closest, 'window_mm': [pcbnew.ToMM(v) for v in bounds]}


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


def retained_routing(ctx):
    """Unchanged camera/flash bypass and exposed-contact/assembly copper contracts."""
    import check_r7 as r7
    import check_r8 as r8
    import math
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
    issues += r7.duplicate_ids(ctx.board)
    issues += r7.legend_subjects(ctx.board)
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
    # Ground-side test point and contact policy is not a pyro spacing rule.
    gate_pad = ctx.fps.get('TP122')
    if gate_pad is None or not gate_pad.IsFlipped():
        issues.append('TP122 must remain on B.Cu')
    return issues, evidence


def check_board(path, stage='full', fit=None, plate=None, bom=None, cpl=None):
    import pcbnew
    import check_r9 as r9
    import fit_check
    import route_check
    path = Path(path)
    text = path.read_text()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    board = pcbnew.LoadBoard(str(path))
    rules = {}
    def add(name, result):
        issues, evidence = result
        rules[name] = dict(ok=not issues, issues=issues, evidence=evidence)
    add('functional', (functional(text), {}))
    add('schematic-population', (schematic_population(path.with_suffix('.kicad_sch')), {}))
    add('arm-gap', arm_gap(board))
    route_check.set_profile('r10')
    if stage != 'functional':
        # Only revision-independent retained geometry. No RF, strict pyro pad or battery-live spacing.
        ctx = r9.Ctx(board, path.parent, path, None, None, None, 0, path.with_suffix('.kicad_dru').read_text())
        for name, fn in (('local-clearance', lambda c: r9.lc1(c.board)), ('sense-end', r9.p8),
                         ('ties', r9.m3), ('mems', r9.m7), ('input-protection', r9.f9), ('tabs', r9.t1)):
            add(name, fn(ctx))
        fit = fit or fit_check.check_board(board, path.parent, profile='r10')
        fit_issues = list(fit['issues'])
        if fit.get('profile') != 'r10' or fit.get('board_sha256', digest) != digest:
            fit_issues.append('fit evidence profile/board binding mismatch')
        add('fit', (fit_issues, fit))
    if stage == 'full':
        add('references', references(board))
        add('copper', r9.k_copper(ctx))
        add('retained-routing', retained_routing(ctx))
        add('inner-layers', r9.k_inner_signal(ctx))
        errors = []
        if not plate or plate.get('profile') != 'r10' or plate.get('board_sha256') != digest:
            errors.append('R10 plate report missing or bound to another board/profile')
        elif plate.get('f1', {}).get('r10_mated', {}).get('pinned_D5', 0) < 209:
            errors.append('R10 plate pinned D5 first mode must be >=209 Hz')
        add('plate', (errors, plate or {}))
        for name, filename in (('bom', bom), ('cpl', cpl)):
            add(name, (assembly_population(Path(filename).read_text()) if filename else [f'{name} assembly list not supplied'], {}))
    issues = [f'{name}: {i}' for name, row in rules.items() for i in row['issues']]
    return dict(profile='r10', stage=stage, complete=stage == 'full', board_sha256=digest,
                ok=not issues, issues=issues, rules=rules)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board', nargs='?', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--stage', choices=('functional', 'placement', 'full'), default='full')
    for name in ('fit', 'plate', 'report', 'bom', 'cpl'):
        ap.add_argument('--' + name, type=Path)
    args = ap.parse_args()
    try:
        report = check_board(args.board, args.stage,
                             json.loads(args.fit.read_text()) if args.fit else None,
                             json.loads(args.plate.read_text()) if args.plate else None, args.bom, args.cpl)
    except Exception as error:
        report = dict(profile='r10', stage=args.stage, complete=False, ok=False,
                      issues=[f'could not run: {type(error).__name__}: {error}'])
    for issue in report['issues']:
        print('FAIL', issue)
    print(f"R10 {args.stage} contract: {'OK' if report['ok'] else 'FAIL'}; complete={report['complete']}")
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
