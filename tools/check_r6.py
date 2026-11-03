#!/usr/bin/env python3
"""Independent R6 native-CAD contract; complements KiCad DRC/ERC and fit_check.

Run with KiCad Python. Findings are not waived by schematic parity or a connected
netlist: foreign filled copper, weak endpoint overlaps and the flash bypass route
are checked on the actual board geometry. No generator module is imported.
"""
import argparse
from collections import defaultdict
import hashlib
import heapq
import json
import math
from pathlib import Path
import re
import sys

import pcbnew
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fit_check import board_geometry, fp_name, input_hashes, model_box

mm, MM = pcbnew.ToMM, pcbnew.FromMM
REMOVED = set('J120 J125 Q125 R135 R138 R139 R140 R141 R142 R143 R144 R145 R169 R171 R174 R176 R179 R181 C138 C139 C140 C141 TP123'.split())
FOOTPRINTS = {'J9': 'M3_GH_BM04B_GHS_TBT', 'J130': 'M3_SH_BM07B_SRSS_TB',
              'J131': 'M3_SH_BM04B_SRSS_TB', 'J2': 'M3_TC2030_IDC_NL'}
CONNECTORS = {
    'J9': ('CAM_5V', 'GND', 'CAM_RX_WIRE', 'CAM_TX_WIRE'),
    'J130': ('RADIO_M0', 'RADIO_M1', 'RADIO_RXD', 'RADIO_TXD', 'RADIO_AUX', 'TLM_5V', 'GND'),
    'J131': ('TLM_5V', 'GND', 'GPS_TXD', 'GPS_RXD'),
    'J2': ('3V3', 'SWDIO', 'NRST', 'SWCLK', 'GND', None),
}
# Header direction is relative to the peripheral: MCU TX goes to peripheral RX.
SIGNALS = [('R196', '65', 'RADIO_M0_MCU', 'RADIO_M0'),
           ('R197', '66', 'RADIO_M1_MCU', 'RADIO_M1'),
           ('R198', '63', 'RADIO_TX_MCU', 'RADIO_RXD'),
           ('R199', '64', 'RADIO_RX_MCU', 'RADIO_TXD'),
           ('R200', '67', 'RADIO_AUX_MCU', 'RADIO_AUX'),
           ('R201', '68', 'GPS_TX_MCU', 'GPS_RXD'),
           ('R202', '69', 'GPS_RX_MCU', 'GPS_TXD')]
# Pad centers from the immutable R5 native board. Rigid translation/rotation is allowed.
CH1_PADS = {('J121', '1'): (36, 72.78), ('J121', '2'): (36, 77.86),
            ('J124', '1'): (10, 77.86), ('J124', '2'): (10, 72.78),
            ('Q124', '5'): (27.4, 72.8), ('R134', '1'): (24.975, 77.8),
            ('R134', '2'): (19.825, 77.8)}


def xy(p):
    return mm(p.x), mm(p.y)


def pads_by_ref(board):
    return {(f.GetReference(), p.GetNumber()): p for f in board.GetFootprints() for p in f.Pads() if p.GetNumber()}


def near_boxes(a, b, gap):
    return not (a.GetRight() + gap < b.GetX() or b.GetRight() + gap < a.GetX()
                or a.GetBottom() + gap < b.GetY() or b.GetBottom() + gap < a.GetY())


def copper_shapes(board):
    """Keep owning SWIG objects alive with their shapes; filled zones, not outlines."""
    result = defaultdict(list)
    layers = list(board.GetEnabledLayers().CuStack())
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            for layer in layers:
                if p.IsOnLayer(layer):
                    shape = p.GetEffectiveShape(layer)
                    result[layer].append((f'{f.GetReference()}.{p.GetNumber()}', p.GetNetname(), shape, p))
    for track in board.GetTracks():
        for layer in layers:
            if track.IsOnLayer(layer):
                result[layer].append((f'{track.GetClass()} {track.m_Uuid.AsString()}', track.GetNetname(),
                                      track.GetEffectiveShape(layer), track))
    for zone in board.Zones():
        if zone.GetIsRuleArea():
            continue
        for layer in layers:
            if zone.HasFilledPolysForLayer(layer):
                result[layer].append(('zone ' + zone.GetZoneName(), zone.GetNetname(),
                                      zone.GetFilledPolysList(layer), zone))
    return result


def foreign_clearances(board, copper):
    issues, measured = [], []
    for f in board.GetFootprints():
        for pad in f.Pads():
            bare = bool(re.fullmatch(r'TP\d+', f.GetReference()))
            raw = pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and pad.GetNetname() == 'RAW_ACT'
            debug = (f.GetReference() == 'J2' and pad.GetNumber() in ('1', '2', '3', '4', '5', '6')
                     and pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH)
            if not (bare or raw or debug):
                continue
            clearance = 1.0 if bare else (0.508 if debug else 0.3)
            if debug and (not pad.IsOnLayer(pcbnew.F_Mask) or pad.IsOnLayer(pcbnew.F_Paste)):
                issues.append(f'J2.{pad.GetNumber()}: contact needs exposed front copper and no solder paste')
            # Test-pad access is on exposed outer copper; RAW_ACT PTH spans every copper layer.
            layers = [layer for layer in copper if pad.IsOnLayer(layer) and
                      (raw or (debug and layer == pcbnew.F_Cu) or
                       (layer == pcbnew.F_Cu and pad.IsOnLayer(pcbnew.F_Mask)) or
                       (layer == pcbnew.B_Cu and pad.IsOnLayer(pcbnew.B_Mask)))]
            for layer in layers:
                shape = pad.GetEffectiveShape(layer)
                for name, net, other, owner in copper[layer]:
                    if owner == pad or (net and net == pad.GetNetname()):
                        continue
                    # The maker's adjacent contacts have a deliberate smaller gap.
                    if debug and isinstance(owner, pcbnew.PAD) and owner.GetParentFootprint() == f:
                        continue
                    if not near_boxes(shape.BBox(), other.BBox(), MM(clearance)):
                        continue
                    if shape.Collide(other, MM(clearance) - 1000):
                        issues.append(f'{f.GetReference()}.{pad.GetNumber()} needs {clearance:g} mm foreign-copper '
                                      f'clearance on {board.GetLayerName(layer)}: {name} ({net or "no net"})')
            measured.append(f'{f.GetReference()}.{pad.GetNumber()}: {clearance:g} mm')
    return issues, measured


def vias_on_through_pads(board):
    issues = []
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() not in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                continue
            shape = p.GetEffectiveShape(pcbnew.F_Cu)
            for via in vias:
                other = via.GetEffectiveShape(pcbnew.F_Cu)
                if near_boxes(shape.BBox(), other.BBox(), 0) and shape.Collide(other, 0):
                    issues.append(f'via at {xy(via.GetPosition())} overlaps through-hole pad {f.GetReference()}.{p.GetNumber()}')
    return issues


def distance_to_segment(point, start, end):
    x, y = point; ax, ay = start; bx, by = end
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(x - ax, y - ay)
    t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - ax - t * dx, y - ay - t * dy)


def overlap_only_joints(board, copper):
    """Flag open track centerlines connected only by the width of another item.

    Endpoints inside a pad, via or filled same-net zone are real junctions.
    Interior segment crossings are valid; only unsupported endpoints are checked.
    """
    issues, checked = [], 0
    tracks = defaultdict(list)
    for item in board.GetTracks():
        if item.GetClass() == 'PCB_TRACK':
            tracks[item.GetLayer(), item.GetNetname()].append(item)
    for (layer, net), group in tracks.items():
        for item in group:
            for end in (item.GetStart(), item.GetEnd()):
                checked += 1
                same = [(name, shape, owner) for name, other_net, shape, owner in copper[layer]
                        if other_net == net and owner != item and
                        near_boxes(item.GetBoundingBox(), shape.BBox(), 0)]
                if any(shape.Collide(end, 0) for name, shape, owner in same
                       if owner.GetClass() != 'PCB_TRACK'):
                    continue
                close = [other for other in group if other != item and
                         distance_to_segment(xy(end), xy(other.GetStart()), xy(other.GetEnd())) <= 0.001]
                if close:
                    continue
                touch = [name for name, shape, owner in same
                         if shape.Collide(end, max(0, item.GetWidth() // 2 - 1000))]
                if touch:
                    issues.append(f'{net} endpoint {xy(end)} on {board.GetLayerName(layer)} has overlap-only joint to {touch[0]}')
    return sorted(set(issues)), checked


def direct_route(board, start_pad, end_pad, through_vias=False):
    """Shortest endpoint-linked same-net track route, no zone or remote plane shortcut."""
    if start_pad.GetNetname() != end_pad.GetNetname():
        return None
    graph = defaultdict(list)
    positions = {}
    for track in board.GetTracks():
        if track.GetClass() != 'PCB_TRACK' or track.GetNetname() != start_pad.GetNetname():
            continue
        a, b = (track.GetLayer(), *xy(track.GetStart())), (track.GetLayer(), *xy(track.GetEnd()))
        distance = math.dist(a[1:], b[1:])
        graph[a].append((b, distance)); graph[b].append((a, distance))
        positions[a], positions[b] = track.GetStart(), track.GetEnd()
    if through_vias:
        # Charge one full board thickness per layer transition. This is conservative
        # for inner layers and prevents a remote plane from posing as a local bypass.
        height = mm(board.GetDesignSettings().GetBoardThickness())
        for via in board.GetTracks():
            if via.GetClass() != 'PCB_VIA' or via.GetNetname() != start_pad.GetNetname():
                continue
            keys = [(layer, *xy(via.GetPosition())) for layer in board.GetEnabledLayers().CuStack()
                    if via.IsOnLayer(layer)]
            for key in keys:
                positions[key] = via.GetPosition()
                for other in keys:
                    if key != other:
                        graph[key].append((other, height))
    starts = [key for key, p in positions.items() if start_pad.IsOnLayer(key[0]) and start_pad.HitTest(p)]
    ends = {key for key, p in positions.items() if end_pad.IsOnLayer(key[0]) and end_pad.HitTest(p)}
    queue, seen = [(0.0, key) for key in starts], set()
    heapq.heapify(queue)
    while queue:
        cost, key = heapq.heappop(queue)
        if key in ends:
            return cost
        if key in seen:
            continue
        seen.add(key)
        for nxt, extra in graph[key]:
            if nxt not in seen:
                heapq.heappush(queue, (cost + extra, nxt))
    return None


def camera_bypass(board):
    """Verify both camera translator supply bypasses, including C100's local return."""
    issues, evidence = [], {}
    pads = pads_by_ref(board)
    for ref, supply, net in (('C100', '3', '3V3'), ('C93', '7', 'CAM_IO_3V3')):
        cap = board.FindFootprintByReference(ref)
        power, ground = pads.get((ref, '1')), pads.get((ref, '2'))
        pin = pads.get(('U12', supply))
        if not cap or not power or not ground or not pin:
            issues.append(f'{ref}: camera UART translator bypass or U12 supply pin is missing')
            continue
        if cap.GetValue().lower().split()[:1] != ['100nf']:
            issues.append(f'{ref}: camera UART translator bypass must be 100nF')
        if power.GetNetname() != net or ground.GetNetname() != 'GND' or pin.GetNetname() != net:
            issues.append(f'{ref}: camera UART translator bypass must connect {net} to GND')
        distance = math.dist(xy(power.GetPosition()), xy(pin.GetPosition()))
        route = direct_route(board, pin, power, through_vias=True)
        evidence[ref] = dict(supply_pin='U12.' + supply, pad_distance_mm=distance,
                             direct_copper_route_mm=route)
        limit = 3 if cap.GetLayer() == pin.GetParentFootprint().GetLayer() else 5
        if distance > 3 or route is None or route > limit:
            issues.append(f'{ref}: requires local bypass within 3 mm of U12.{supply} '
                          f'and direct copper <= {limit} mm; distance {distance:.3f}, route {route}')
        if ref == 'C100':
            return_pin = pads.get(('U12', '2'))
            route = direct_route(board, ground, return_pin, through_vias=True) if return_pin else None
            evidence[ref]['direct_ground_return_mm'] = route
            if route is None or route > limit:
                issues.append(f'C100: requires direct local GND return <= {limit} mm to U12.2; found {route}')
    return issues, evidence


def check_contract(board, folder):
    issues, notes, evidence = [], [], {}
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    pads = pads_by_ref(board)
    for ref in sorted(REMOVED & footprints.keys()):
        issues.append('removed channel-2 part remains: ' + ref)
    nets = {str(name) for name in board.GetNetsByName()}
    for net in sorted(n for n in nets if re.search(r'PYRO2|ARM2', n)):
        issues.append('removed channel-2 net remains: ' + net)
    for ref, expected in FOOTPRINTS.items():
        if ref not in footprints or fp_name(footprints[ref]) != expected:
            issues.append(f'{ref}: requires {expected}')
    def expect(ref, pin, net):
        p = pads.get((ref, str(pin)))
        actual = p.GetNetname() if p else None
        ok = actual == net if net is not None else p is not None and (not actual or actual.startswith('unconnected-'))
        if not ok:
            issues.append(f'{ref}.{pin}: expected {net or "NC"}, found {actual}')
    for ref, nets in CONNECTORS.items():
        for pin, net in enumerate(nets, 1):
            expect(ref, pin, net)
    for pin in ('4', '16', '32', '40', '97'):
        expect('U1', pin, None)
    expect('U1', '98', 'IMU_INT1')
    expect('U4', '4', 'IMU_INT1')
    for ref, mcu_pin, mcu_net, port_net in SIGNALS:
        expect('U1', mcu_pin, mcu_net); expect(ref, '1', mcu_net); expect(ref, '2', port_net)
        if ref not in footprints or footprints[ref].GetValue().lower().split()[:1] not in (['1k'], ['1k0'], ['1000']):
            issues.append(f'{ref}: requires 1 kohm series resistance')
    for ref, pin, net in [('U1', '51', 'TLM_PWR_EN'), ('U1', '31', 'TLM_FAULT_N'),
                          ('R192', '1', 'TLM_PWR_EN'), ('R192', '2', 'TLM_EN'),
                          ('R193', '1', 'TLM_EN'), ('R193', '2', 'GND'),
                          ('U14', '2', 'TLM_EN'), ('U16', '2', 'TLM_EN'),
                          ('U15', '4', 'TLM_FAULT_N'), ('U15', '6', 'TLM_5V')]:
        expect(ref, pin, net)
    for ref, value in [('U14', 'AP63301'), ('U15', 'TPS2553')]:
        if ref not in footprints or value not in footprints[ref].GetValue():
            issues.append(f'{ref}: requires {value}')
    for ref in ['D130', 'D131']:
        if ref not in footprints or 'SRV05' not in footprints[ref].GetValue():
            issues.append(f'{ref}: requires SRV05 port ESD protection')
    for ref, nets in [('D130', ('RADIO_M0_MCU', 'GND', 'RADIO_M1_MCU', 'RADIO_TX_MCU', '3V3', 'RADIO_RX_MCU')),
                      ('D131', ('RADIO_AUX_MCU', 'GND', 'GPS_TX_MCU', 'GPS_RX_MCU', '3V3', 'GND'))]:
        for pin, net in enumerate(nets, 1):
            expect(ref, pin, net)
    for ref, value in [('R192', '1k'), ('R193', '10k')]:
        if ref not in footprints or footprints[ref].GetValue().lower().split()[:1] != [value]:
            issues.append(f'{ref}: reset-off enable network requires {value}')
    buzzer = footprints.get('LS120')
    box = model_box(buzzer, folder) if buzzer else None
    if box is None or max(box[2] - box[0], box[3] - box[1]) >= 8.5:
        issues.append('LS120: readable model smaller than 8.5 x 8.5 mm required')
    holes, outline = board_geometry(board)
    evidence['outline_mm'] = outline
    width, length = outline[2] - outline[0], outline[3] - outline[1]
    if abs(width - 46) > 0.01 or length > 110.01:
        issues.append(f'outline {width:g} x {length:g} mm violates 46 mm width / 110 mm maximum')
    if not 80 <= length <= 90:
        notes.append(f'{length:g} mm length is outside the 80–90 mm target')
    port_positions = [xy(footprints[ref].GetPosition()) for ref in ('J9', 'J130', 'J131') if ref in footprints]
    if len(port_positions) == 3:
        x0, y0, x1, y1 = outline
        edge = [all(abs(p[axis] - value) <= 6 for p in port_positions)
                for axis, value in ((0, x0), (0, x1), (1, y0), (1, y1))]
        if not any(edge) or max(math.dist(a, b) for a in port_positions for b in port_positions) > 35:
            issues.append('camera/radio/GPS must form one block within 6 mm of one board edge')
    ch1 = [(key, pos) for key, pos in CH1_PADS.items() if key in pads]
    for i, (key, position) in enumerate(ch1):
        for other, other_position in ch1[i + 1:]:
            old = math.dist(position, other_position)
            new = math.dist(xy(pads[key].GetPosition()), xy(pads[other].GetPosition()))
            if abs(new - old) > 0.02:
                issues.append(f'CH1 spacing changed: {key[0]}.{key[1]} to {other[0]}.{other[1]} '
                              f'{new:.3f} mm, R5 {old:.3f} mm')
    if all(ref in footprints for ref in ('J1', 'J121', 'J124')):
        if max(math.dist(xy(footprints['J1'].GetPosition()), xy(footprints[ref].GetPosition()))
               for ref in ('J121', 'J124')) > 25:
            issues.append('J1 must be grouped within 25 mm of both CH1 terminal centers')
    flash, bypass = pads.get(('U3', '8')), pads.get(('C29', '1'))
    if flash and bypass:
        distance = math.dist(xy(flash.GetPosition()), xy(bypass.GetPosition()))
        route = direct_route(board, flash, bypass)
        evidence.update(c29_vcc_pad_distance_mm=distance, c29_direct_route_mm=route)
        if distance > 2:
            issues.append(f'C29 VCC pad is {distance:.3f} mm from U3.8; maximum 2 mm')
        if route is None or route > 3:
            issues.append(f'C29 requires a direct same-layer route <=3 mm to U3.8; found {route}')
    else:
        issues.append('C29.1 or U3.8 is absent')
    found, evidence['camera_bypass'] = camera_bypass(board)
    issues.extend(found)
    return issues, notes, evidence


def thermal_policy(board, rules_text):
    """Small two-pad SMD passives need thermal connection plus enforced rule minima."""
    issues, small = [], []
    gap = re.search(r'\(constraint thermal_relief_gap\s+\(min ([\d.]+)mm\)', rules_text)
    spoke = re.search(r'\(constraint thermal_spoke_width\s+\(min ([\d.]+)mm\)', rules_text)
    if not gap or float(gap[1]) < 0.25 or not spoke or float(spoke[1]) < 0.3:
        issues.append('small GND thermal rules require minimum 0.25 mm gap and 0.3 mm spokes')
    for f in board.GetFootprints():
        pads = list(f.Pads())
        if len(pads) != 2 or any(p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD for p in pads):
            continue
        if any(max(mm(p.GetSize().x), mm(p.GetSize().y)) > 1.0 for p in pads):
            continue
        for p in pads:
            if p.GetNetname() != 'GND':
                continue
            name = f'{f.GetReference()}.{p.GetNumber()}'
            small.append(name)
            connection = p.GetLocalZoneConnection()
            if connection == pcbnew.ZONE_CONNECTION_INHERITED:
                connection = f.GetLocalZoneConnection()
            if connection != pcbnew.ZONE_CONNECTION_THERMAL:
                issues.append(f'{name}: small GND pad lacks explicit thermal relief')
    return issues, small


def duplicate_ids(board):
    items = list(board.GetFootprints()) + list(board.GetDrawings()) + list(board.Zones())
    for fp in board.GetFootprints():
        items += list(fp.Pads()) + list(fp.GraphicalItems()) + list(fp.GetFields()) + list(fp.Zones())
    items += list(board.GetTracks())
    seen, issues = {}, []
    for item in items:
        key = item.m_Uuid.AsString()
        if key in seen:
            issues.append(f'duplicate CAD UUID {key}: {seen[key]} and {item.GetClass()}')
        seen[key] = item.GetClass()
    return issues


def pin_legends(board):
    # UART names are peripheral-side; inherited CAM_RX_WIRE is camera TX.
    required = {'J9': ('5V', 'GND', 'TX', 'RX'),
                'J130': ('M0', 'M1', 'RX', 'TX', 'AUX', '5V', 'GND'),
                'J131': ('5V', 'GND', 'TX', 'RX'),
                'J2': ('3V3', 'SWDIO', 'NRST', 'SWCLK', 'GND', 'NC')}
    seen = defaultdict(lambda: defaultdict(set))
    for item in board.GetDrawings():
        if not isinstance(item, pcbnew.PCB_TEXT) or item.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            continue
        match = re.match(r'^(J\d+)\s+(.+)', item.GetText())
        if match and match[1] in required:
            for pin, name in re.findall(r'(\d+):([A-Z0-9]+)', match[2]):
                seen[match[1]][int(pin)].add(name)
    return [f'{ref}.{pin}: silkscreen must identify {name} (UART names at module)'
            for ref, names in required.items() for pin, name in enumerate(names, 1)
            if seen[ref][pin] != {name}]


def check_board(board, folder):
    issues, notes, evidence = check_contract(board, folder)
    issues.extend(duplicate_ids(board))
    issues.extend(pin_legends(board))
    copper = copper_shapes(board)
    found, evidence['guarded_pads'] = foreign_clearances(board, copper); issues.extend(found)
    issues.extend(vias_on_through_pads(board))
    found, evidence['track_endpoints_checked'] = overlap_only_joints(board, copper); issues.extend(found)
    rule_file = folder / (Path(board.GetFileName()).stem + '.kicad_dru')
    found, evidence['small_ground_pads'] = thermal_policy(board, rule_file.read_text() if rule_file.is_file() else '')
    issues.extend(found)
    return dict(ok=not issues, issues=issues, notes=notes, evidence=evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', nargs='?', type=Path, default=Path('m3_design/assembly_review/m3.kicad_pcb'))
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    board_path = args.board.resolve()
    def inputs():
        result = input_hashes(board_path)
        for path in (board_path.with_suffix('.kicad_dru'), board_path.with_suffix('.kicad_pro')):
            result[path.name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        return result
    before = inputs()
    report = check_board(pcbnew.LoadBoard(str(board_path)), board_path.parent)
    if before != inputs():
        report['issues'].append('board, model or rules changed during check'); report['ok'] = False
    report.update(board_sha256=before[board_path.name], inputs_sha256=before,
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  fit_checker_sha256=hashlib.sha256(Path(__file__).with_name('fit_check.py').read_bytes()).hexdigest())
    for note in report['notes']: print('NOTE', note)
    for issue in report['issues']: print('FAIL', issue)
    print('R6 CAD contract:', 'OK' if report['ok'] else f"FAIL ({len(report['issues'])} findings)")
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
