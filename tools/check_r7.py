#!/usr/bin/env python3
"""Independent R7 native-CAD contract; complements KiCad DRC/ERC, check_actuators and fit_check.

Run with KiCad Python. Findings are not waived by schematic parity or a connected netlist: foreign filled copper,
weak endpoint overlaps, the flash bypass route and the RF strip are checked on the actual board geometry. No
generator module is imported. R7 (docs/M3_R7.md) moves the radio and GNSS onto the board: the R6 telemetry port
contract (J130/J131, U14-U16, the TLM nets) is replaced by the F10 pin map, the modules' pull and series
resistors, the pyro sentinels, the SMA jack positions and the RF strip's ground rule.
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
import route_check as rc

mm, MM = pcbnew.ToMM, pcbnew.FromMM
# R6 channel-2 removals, then the R6 telemetry port parts R7 removed (F10)
REMOVED = set('J120 J125 Q125 R135 R138 R139 R140 R141 R142 R143 R144 R145 R169 R171 R174 R176 R179 R181 C138 C139 '
              'C140 C141 TP123'.split()) | set('J130 J131 U14 U15 U16 L4 TP130 D130 D131'.split()) \
    | {f'C{n}' for n in range(170, 181)} | {f'R{n}' for n in range(190, 207)}
REMOVED_NETS = ('TLM_', 'GPS_', 'RADIO_M0', 'RADIO_M1', 'RADIO_RXD', 'RADIO_TXD', 'RADIO_AUX', 'RADIO_TX_MCU',
                'RADIO_RX_MCU')
FOOTPRINTS = {'J9': 'M3_GH_BM04B_GHS_TBT', 'J2': 'M3_TC2030_IDC_NL', 'J30': 'M3_SMA_KH_KE8_EDGE',
              'J31': 'M3_SMA_KH_KE8_EDGE', 'U30': 'M3_MAX_F10S_LCC18', 'U31': 'M3_E22_900MM22S'}
CONNECTORS = {
    'J9': ('CAM_5V', 'GND', 'CAM_RX_WIRE', 'CAM_TX_WIRE'),
    'J2': ('3V3', 'SWDIO', 'NRST', 'SWCLK', 'GND', None),
    'J30': ('GND', 'GND', 'GND', 'GND', 'GNSS_RF_ANT'),
    'J31': ('GND', 'GND', 'GND', 'GND', 'RADIO_RF_ANT'),
}
# F10 pin map (docs/M3_R7.md "Pin contract"): U1 pin -> net on the MCU side
RF_MCU_PINS = {'45': 'RADIO_RXEN', '51': 'RADIO_NSS', '52': 'RADIO_SCK_MCU', '53': 'RADIO_MISO_MCU',
               '54': 'RADIO_MOSI_MCU', '55': 'RADIO_BUSY', '56': 'RADIO_NRST', '57': 'RADIO_DIO1',
               '61': 'GNSS_TP_MCU', '63': 'GNSS_RXD_MCU', '64': 'GNSS_TXD_MCU', '65': 'GNSS_RESET_N'}
FREED_NC = ('31', '66', '67', '68', '69')                  # PA7, PC9, PA8, PA9 (ROM USART1), PA10
PYRO_SENTINELS = ('2', '4', '5', '16', '32')               # PE3, PE5, PE6, PC1, PC4: no net (check_actuators.py)
OTHER_NC = ('40', '97')                                    # PE10 (IMU status moved to PE1), PE0
# series resistors (ref, pin 1 net, pin 2 net, value, end it must sit at) and pulls (ref, signal, rail, value)
# (each series resistor sits at the line's driving end: nearer that part than the far end)
SERIES = [('R313', 'RADIO_SCK_MCU', 'RADIO_SCK', '33R', 'U1', 'U31'),
          ('R315', 'RADIO_MOSI_MCU', 'RADIO_MOSI', '33R', 'U1', 'U31'),
          ('R314', 'RADIO_MISO', 'RADIO_MISO_MCU', '33R', 'U31', 'U1'),
          ('R306', 'GNSS_RXD_MCU', 'GNSS_RXD', '220R', 'U1', 'U30'),
          ('R305', 'GNSS_TXD', 'GNSS_TXD_MCU', '220R', 'U30', 'U1'),
          ('R307', 'GNSS_TIMEPULSE', 'GNSS_TP_MCU', '1k', 'U30', 'U1')]
PULLS = [('R310', 'RADIO_NSS', '3V3_RADIO', '100k'), ('R311', 'RADIO_NRST', 'GND', '2k'),
         ('R312', 'RADIO_RXEN', 'GND', '100k')]
MODULE_PINS = {('U31', '3'): 'RADIO_NRST', ('U31', '6'): 'RADIO_RF', ('U31', '9'): 'RADIO_TXEN',
               ('U31', '10'): 'RADIO_RXEN', ('U31', '11'): 'RADIO_BUSY', ('U31', '12'): 'RADIO_MISO',
               ('U31', '13'): 'RADIO_MOSI', ('U31', '14'): 'RADIO_NSS', ('U31', '15'): 'RADIO_SCK',
               ('U31', '19'): 'RADIO_TXEN', ('U31', '20'): 'RADIO_DIO1', ('U31', '1'): '3V3_RADIO',
               ('U30', '2'): 'GNSS_TXD', ('U30', '3'): 'GNSS_RXD', ('U30', '4'): 'GNSS_TIMEPULSE',
               ('U30', '7'): '3V3_GNSS', ('U30', '8'): '3V3_GNSS', ('U30', '9'): 'GNSS_RESET_N',
               ('U30', '11'): 'GNSS_RF_IN', ('U30', '13'): 'GNSS_LNA_EN', ('U30', '14'): 'GNSS_VCC_RF',
               ('U30', '18'): 'GNSS_SAFEBOOT_N', ('TP30', '1'): 'GNSS_SAFEBOOT_N'}
DNP = ('C303', 'C304', 'C305', 'C313', 'C314')
JACKS = {'J30': 12.85, 'J31': 31.54}                       # axes on the aft edge (pass1_layout 3.3)
STRIP_Y = 23.5                                             # RF strip y 0-23.5 (F10)
# Nets that may have copper in the strip, per layer. F.Cu: the modules, their RF chains, supplies and interface leads.
# In1/In2: GND pours only (vias of strip nets pass through). B.Cu: GND, the jack legs and the GNSS feed limiter under
# U30 (pass1_layout 3.3), plus the documented exceptions of the R7 board (docs/M3_R7.md "R7 board"): the radio's TXEN
# loop round the module's west side, DIO1's lead to pin 20 and NSS's hop under SCK.
STRIP_F = re.compile(r'^(GND|GNSS_.*|RADIO_.*|3V3_GNSS|3V3_RADIO|3V3)$')
STRIP_B = re.compile(r'^(GND|GNSS_VCC_RF|GNSS_LNA_EN|GNSS_ANT_(DC|SRC|GATE|PD)|RADIO_TXEN|RADIO_DIO1|RADIO_NSS)$')
STRIP_VIA = re.compile(r'^(GND|GNSS_VCC_RF|GNSS_LNA_EN|GNSS_ANT_DC|RADIO_TXEN|RADIO_DIO1|RADIO_NSS)$')
KEEPOUTS = {'U30_KEEPOUT': ('F.Cu', 'In1.Cu'), 'U31_KEEPOUT': ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')}
# EBYTE E22 manual 4.1 (no wiring under the module): on B.Cu and In2, where the module has no escapes, U31_KEEPOUT
# areas must cover the whole module body (pass 2 RF-05); on F.Cu/In1 the pad-ring interior (the module's own leads
# leave its pads there). m3.kicad_dru's keep-out rule matches every area of that name.
U31_BODY = (24.86, 9.0, 34.86, 19.0)                       # E22-900MM22S body (10 x 10 mm) at (29.86, 14.0)
# RF ground pads connected solidly (no thermal relief; pass 2 RF-02): the ESD diodes, the bias-tee capacitor and the
# pi-network shunt lands; each has its own GND via within RF_GND_VIA mm of the pad edge
# C302.2 (bias-tee decoupler behind L30) is back on the house thermal relief since fix pass 4 (P4-RF-03 / P3-RF-02:
# tombstoning; L30 > 500 ohm makes its spoke inductance immaterial), so thermal_policy checks it; its GND via stays
RF_SOLID_GND = ('D30.2', 'D31.2', 'C303.2', 'C305.2', 'C313.2', 'C314.2')
RF_GND_VIA = 0.6
# RF strip stitching (pass 2 RF-05): the fence along the strip boundary keeps a GND via every <= 2 mm except the two
# lead openings; beside each RF line a GND via every <= 2.5 mm (the gaps the RF review measured and accepted, where the
# chain parts leave no via spot, are named with their ceiling); In1 is GND under every RF track and pad plus 0.3 mm
# except the SMA launch cut-outs
FENCE_Y, FENCE_PITCH = 23.3, 2.0
FENCE_OPENINGS = ((6.0, 12.7), (19.7, 24.1))               # GNSS escapes + 3V3 feed; radio interface lanes
RF_RUNS = {'GNSS': (('GNSS_RF_ANT', 'GNSS_RF_IN'), 'J30', 'U30'), 'RADIO': (('RADIO_RF_ANT', 'RADIO_RF'), 'J31', 'U31')}
STITCH_GAP = 2.5
# accepted gaps (pass2_rf.md 3.6, re-measured on the pass-2 board; the line ends count as stitching points: the jack's
# legs up to its pad end, the module's GND pins from its RF pad): GNSS west 3.90 mm (L30, C302 and C303 fill y 4.4-8.3),
# GNSS east 2.65 mm (R304/C305 pi row between the y 5.65 via and U30.10's via)
STITCH_ACCEPTED = {('GNSS', 'west'): 4.0, ('GNSS', 'east'): 2.7}
IN1_MARGIN = 0.3
# Via holes keep >= 0.1 mm from every SMD pad's solder-mask opening (REQUIREMENTS M2). Only bare contacts are exempt:
# test pads and the J2 Tag-Connect pattern (never soldered).
VIA_PAD_GAP = 0.1
BARE_CONTACTS = re.compile(r'^(TP\d+|J2)$')
SAFETY_NETS = re.compile(r'^(PYRO|ARM|ACT_|RAW_ACT|BAT_IN$|BOOT0|NRST$)')
# RF parts (F10: no RF part pin on a safety net): the modules, jacks, antenna-bias limiter Q30-Q32, ESD diodes, bias
# choke, ferrites, the safe-boot pad and the 3xx passives; RF_NET: the nets that make a part an RF part
RF_PART = re.compile(r'(U3[01]|J3[01]|Q3\d|[RCDLQ]3\d\d|D3[01]|L30|FB3[01]|TP30)')
RF_NET = re.compile(r'^(GNSS_|RADIO_|3V3_GNSS$|3V3_RADIO$)')
STRIP_GND_REACH = 4.0       # mm of copper from any F.Cu / B.Cu GND copper point in the strip to a GND via or hole
LAUNCH_REF_MARGIN = 0.3     # mm: In2 GND must lie under each In1 launch cut-out grown by this much sideways
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
        issues.append('removed part remains: ' + ref)
    nets = {str(name) for name in board.GetNetsByName()}
    for net in sorted(n for n in nets if re.search(r'PYRO2|ARM2', n) or n.startswith(REMOVED_NETS)):
        issues.append('removed net remains: ' + net)
    for ref, expected in FOOTPRINTS.items():
        if ref not in footprints or fp_name(footprints[ref]) != expected:
            issues.append(f'{ref}: requires {expected}')
    def expect(ref, pin, net):
        p = pads.get((ref, str(pin)))
        actual = p.GetNetname() if p else None
        ok = actual == net if net is not None else p is not None and (not actual or actual.startswith('unconnected-'))
        if not ok:
            issues.append(f'{ref}.{pin}: expected {net or "NC"}, found {actual}')
    for ref, nets_ in CONNECTORS.items():
        for pin, net in enumerate(nets_, 1):
            expect(ref, pin, net)
    for pin, net in RF_MCU_PINS.items():
        expect('U1', pin, net)
    for pin in FREED_NC + PYRO_SENTINELS + OTHER_NC:
        expect('U1', pin, None)
    for (ref, pin), net in MODULE_PINS.items():
        expect(ref, pin, net)
    expect('U1', '98', 'IMU_INT1')
    expect('U4', '4', 'IMU_INT1')
    def value(ref):
        return footprints[ref].GetValue().split()[0].lower() if ref in footprints else None
    def center(ref):
        return xy(footprints[ref].GetPosition())
    for ref, one, two, val, end, far in SERIES:
        expect(ref, 1, one); expect(ref, 2, two)
        if value(ref) != val.lower():
            issues.append(f'{ref}: requires {val} series resistance')
        if ref in footprints and math.dist(center(ref), center(end)) >= math.dist(center(ref), center(far)):
            issues.append(f'{ref}: series resistor must sit at its driving end ({end})')
    for ref, signal, rail, val in PULLS:
        p1, p2 = pads.get((ref, '1')), pads.get((ref, '2'))
        if not p1 or not p2 or {p1.GetNetname(), p2.GetNetname()} != {signal, rail}:
            issues.append(f'{ref}: must pull {signal} to {rail}')
        if value(ref) != val.lower():
            issues.append(f'{ref}: pull resistor must be {val}')
    for ref in DNP:
        f = footprints.get(ref)
        want = pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES
        if not f or (f.GetAttributes() & want) != want:
            issues.append(f'{ref}: DNP placeholder needs dnp, exclude-from-BOM and exclude-from-position flags')
    issues.extend(dnp_paste(board))
    for ref in ('U30', 'U31'):
        if ref in footprints and footprints[ref].IsFlipped():
            issues.append(f'{ref}: module must be on the top side (single final reflow)')
    # no radio, GNSS or RF part pin on a pyro, arming, actuator, battery-entry or debug-reset net (F10)
    rf_refs = {r for r in footprints if RF_PART.fullmatch(r)}
    issues.extend(rf_part_coverage(board))
    for ref in sorted(rf_refs):
        for p in footprints[ref].Pads():
            if SAFETY_NETS.match(p.GetNetname() or ''):
                issues.append(f'{ref}.{p.GetNumber()}: RF part on safety net {p.GetNetname()}')
    holes, outline = board_geometry(board)
    evidence['outline_mm'] = outline
    width, length = outline[2] - outline[0], outline[3] - outline[1]
    if abs(width - 46) > 0.01 or length > 120.01:
        issues.append(f'outline {width:g} x {length:g} mm violates 46 mm width / 120 mm maximum (P1)')
    # SMA jacks: front side, rotation 0, local y = 0 on the aft edge, axes as placed, >= 12 mm apart, no paste
    for ref, axis in JACKS.items():
        f = footprints.get(ref)
        if not f:
            continue
        x, y = center(ref)
        if f.IsFlipped() or abs(f.GetOrientationDegrees()) > 0.01 or abs(x - axis) > 0.005 or abs(y - outline[1]) > 0.005:
            issues.append(f'{ref}: jack must be front side, rotation 0, at ({axis}, {outline[1]:g}) on the aft edge; '
                          f'is ({x:.3f}, {y:.3f}) rot {f.GetOrientationDegrees():g}')
        for p in f.Pads():
            if p.IsOnLayer(pcbnew.F_Paste) or p.IsOnLayer(pcbnew.B_Paste):
                issues.append(f'{ref}.{p.GetNumber()}: SMA pads carry no paste (fitted in the through-hole step)')
    if all(r in footprints for r in JACKS) and math.dist(center('J30'), center('J31')) < 12:
        issues.append('J30/J31 must be >= 12 mm apart, centre to centre (F10)')
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
    buzzer = footprints.get('LS120')
    box = model_box(buzzer, folder) if buzzer else None
    if box is None or max(box[2] - box[0], box[3] - box[1]) >= 8.5:
        issues.append('LS120: readable model smaller than 8.5 x 8.5 mm required')
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


def rf_strip(board):
    """The RF strip (y 0-23.5, F10): only GND pours on In1 and In2 (In1 cut out under each SMA centre pad), and on
    each layer only the copper the strip may hold (STRIP_F / STRIP_B / STRIP_VIA); the modules' keep-out areas
    exist on their layers; the In1 launch cut-outs sit under the jack centre pads."""
    issues, counted = [], defaultdict(int)
    def in_strip(box):
        return mm(box.GetTop()) < STRIP_Y - 1e-6
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
        ok = (STRIP_F.match(net) if layer == pcbnew.F_Cu else STRIP_B.match(net) if layer == pcbnew.B_Cu else
              net == 'GND')
        if not ok:
            issues.append(f'{board.GetLayerName(layer)} track of {net} at {xy(t.GetStart())} in the RF strip')
        counted[board.GetLayerName(layer)] += 1
    for z in board.Zones():
        if z.GetIsRuleArea() or not in_strip(z.GetBoundingBox()):
            continue
        if z.GetNetname() != 'GND':
            for layer in z.GetLayerSet().CuStack():
                if z.HasFilledPolysForLayer(layer):
                    polys = z.GetFilledPolysList(layer)
                    if polys.OutlineCount() and mm(polys.BBox().GetTop()) < STRIP_Y:
                        issues.append(f'{z.GetNetname()} pour on {board.GetLayerName(layer)} reaches the RF strip')
    for layer, name in ((pcbnew.In1_Cu, 'In1'), (pcbnew.In2_Cu, 'In2')):
        gnd = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(layer)
               and mm(z.GetBoundingBox().GetTop()) <= 0.5 and mm(z.GetBoundingBox().GetBottom()) >= STRIP_Y]
        if not gnd:
            issues.append(f'{name}: no GND pour covers the RF strip')
    areas = {z.GetZoneName(): z for z in board.Zones() if z.GetIsRuleArea()}
    for name, layers in KEEPOUTS.items():
        same = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetZoneName() == name]
        have = {board.GetLayerName(l) for z in same for l in z.GetLayerSet().CuStack()}
        if not same or have != set(layers):
            issues.append(f'{name}: rule area on {", ".join(layers)} required (m3.kicad_dru keep-out rules use it)')
    issues.extend(u31_body_keepout(board))
    for ref, axis in JACKS.items():
        z = areas.get(f'R7_{ref}_launch_In1')
        if not z:
            issues.append(f'{ref}: In1 cut-out rule area under the centre pad missing')
            continue
        bb = z.GetBoundingBox()
        if abs((mm(bb.GetLeft()) + mm(bb.GetRight())) / 2 - axis) > 0.01 or not z.GetDoNotAllowZoneFills() or \
                {board.GetLayerName(l) for l in z.GetLayerSet().CuStack()} != {'In1.Cu'}:
            issues.append(f'{ref}: In1 cut-out must be centred on the jack axis, In1 only, no fill')
    return issues, dict(counted)


def rf_part_coverage(board):
    """The RF-part filter (RF_PART, used by the safety-net test in check_contract) must hold every part with a pad on a
    radio or GNSS net, except the MCU U1 (P3-REQUIREMENTS-06: Q30-Q32 had slipped through)."""
    issues = []
    for f in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = f.GetReference()
        if ref != 'U1' and not RF_PART.fullmatch(ref) and any(RF_NET.match(p.GetNetname() or '') for p in f.Pads()):
            issues.append(f'{ref}: part on a radio / GNSS net not covered by the RF-part filter')
    return issues


def launch_reference(board):
    """Under each SMA centre pad In1 is cut out (R7_<jack>_launch_In1), so the launch references In2 there: In2 GND fill
    must cover the cut-out grown LAUNCH_REF_MARGIN sideways, from the routed-edge clearance to the cut-out's end (0.1 mm
    sample grid; P3-RF-04)."""
    issues, evidence = [], {}
    gnd = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.In2_Cu)]
    for ref, axis in JACKS.items():
        z = next((a for a in board.Zones() if a.GetIsRuleArea() and a.GetZoneName() == f'R7_{ref}_launch_In1'), None)
        if z is None:
            continue
        bb = z.GetBoundingBox()
        x0, x1 = mm(bb.GetLeft()) - LAUNCH_REF_MARGIN, mm(bb.GetRight()) + LAUNCH_REF_MARGIN
        y0, y1 = 0.6, mm(bb.GetBottom())
        miss, n = [], 0
        for j in range(int(round((y1 - y0) / 0.1)) + 1):
            for i in range(int(round((x1 - x0) / 0.1)) + 1):
                q = pcbnew.VECTOR2I(MM(x0 + 0.1 * i), MM(y0 + 0.1 * j))
                n += 1
                if not any(g.HitTestFilledArea(pcbnew.In2_Cu, q) for g in gnd):
                    miss.append((round(x0 + 0.1 * i, 2), round(y0 + 0.1 * j, 2)))
        evidence[ref] = dict(samples=n, missing=len(miss))
        if miss:
            issues.append(f'{ref}: In2 GND missing under the launch cut-out at {len(miss)} of {n} samples, e.g. {miss[:3]}')
    return issues, evidence


MODULE_GND = {'U31 body': ((24.86, 9.0, 34.86, 19.0), (pcbnew.In1_Cu, pcbnew.In2_Cu)),     # r7_lib.U31_BODY
              'U30 keep-out': ((5.36, 11.25, 15.46, 18.65), (pcbnew.In1_Cu,))}                 # r7_lib.U30_KEEPOUT


def module_ground(board):
    """GND fill must lie under the radio module's whole body on In1 and In2 (EBYTE manual 4.1: nothing but ground under
    the module) and under the GNSS module's keep-out on In1 (u-blox IM 4.4), at every 0.2 mm sample (P3-RF-04)."""
    issues, evidence = [], {}
    for name, ((x0, y0, x1, y1), layers) in MODULE_GND.items():
        for lay in layers:
            gnd = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(lay)]
            miss, n = [], 0
            for j in range(int(round((y1 - y0) / 0.2)) + 1):
                for i in range(int(round((x1 - x0) / 0.2)) + 1):
                    q = pcbnew.VECTOR2I(MM(x0 + 0.2 * i), MM(y0 + 0.2 * j))
                    n += 1
                    if not any(g.HitTestFilledArea(lay, q) for g in gnd):
                        miss.append((round(x0 + 0.2 * i, 2), round(y0 + 0.2 * j, 2)))
            evidence[f'{name} {board.GetLayerName(lay)}'] = dict(samples=n, missing=len(miss))
            if miss:
                issues.append(f'{name}: {board.GetLayerName(lay)} GND missing at {len(miss)} of {n} samples, '
                              f'e.g. {miss[:3]}')
    return issues, evidence


def rf_gnd_reach(board, limit=STRIP_GND_REACH):
    """Every F.Cu and B.Cu GND copper point in the RF strip lies within `limit` mm, through copper on its own layer, of
    a GND via or plated GND hole (P3-RF-01: a 15 mm unstitched GND finger reached 18.3 mm; u-blox IM 4.4: stubs at the
    ground planes must be avoided or ended with a via). Searched over the strip and 5 mm forward of it."""
    issues, evidence = [], {}
    for lid in (pcbnew.F_Cu, pcbnew.B_Cu):
        pts = rc.gnd_reach(board, lid, (0.0, -1.0, 46.0, STRIP_Y + 5.0), (0.0, -1.0, 46.0, STRIP_Y), limit=limit + 30)
        far = [(d, x, y) for d, x, y in pts if d is None or d > limit]
        worst = max((d for d, _, _ in pts if d is not None), default=0.0)
        evidence[board.GetLayerName(lid)] = round(worst, 2)
        shown = []
        for d, x, y in sorted(far, key=lambda t: -(t[0] or 1e9)):
            if all(math.dist((x, y), q[1:]) > 1.5 for q in shown):
                shown.append((None if d is None else round(d, 2), round(x, 2), round(y, 2)))
        for d, x, y in shown:
            issues.append(f'{board.GetLayerName(lid)} GND copper at ({x}, {y}) in the RF strip is '
                          f'{"unreachable" if d is None else f"{d} mm"} of copper from a GND via (maximum {limit} mm)')
    return issues, evidence


def dnp_paste(board):
    """An unfitted placeholder (dnp and out of the BOM) gets no solder paste: JLC would print solder on empty lands
    (pass 2 RF-01/DFM-02)."""
    issues = []
    for f in board.GetFootprints():
        a = f.GetAttributes()
        if not (a & pcbnew.FP_DNP and a & pcbnew.FP_EXCLUDE_FROM_BOM):
            continue
        for p in f.Pads():
            if p.IsOnLayer(pcbnew.F_Paste) or p.IsOnLayer(pcbnew.B_Paste):
                issues.append(f'{f.GetReference()}.{p.GetNumber()}: unfitted placeholder land carries solder paste')
    return issues


def vias_in_smd_pads(board, exempt=None):
    """REQUIREMENTS M2: no via hole opens into a soldered SMD pad, and every via hole keeps >= VIA_PAD_GAP from a pad's
    solder-mask opening (bare contacts exempt). DRC hole clearance does not see same-net pads.
    Optional caller predicate exempt(pad, via) defaults to no additional exceptions (R10 GAP-3 only)."""
    issues, checked = [], 0
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
    for f in board.GetFootprints():
        if BARE_CONTACTS.match(f.GetReference()):
            continue
        for p in f.Pads():
            if p.GetAttribute() not in (pcbnew.PAD_ATTRIB_SMD, pcbnew.PAD_ATTRIB_CONN):
                continue
            for cu, mask in ((pcbnew.F_Cu, pcbnew.F_Mask), (pcbnew.B_Cu, pcbnew.B_Mask)):
                if not (p.IsOnLayer(cu) and p.IsOnLayer(mask)):
                    continue
                shape = p.GetEffectiveShape(cu)
                gap = MM(VIA_PAD_GAP) + max(0, p.GetSolderMaskExpansion(mask))
                checked += 1
                for v in vias:
                    hole = pcbnew.SHAPE_CIRCLE(v.GetPosition(), v.GetDrillValue() // 2)
                    if near_boxes(shape.BBox(), hole.BBox(), gap) and shape.Collide(hole, gap - 1):
                        if exempt is not None and exempt(p, v):
                            continue
                        issues.append(f'via hole at {xy(v.GetPosition())} ({v.GetNetname()}) is within '
                                      f'{VIA_PAD_GAP} mm of {f.GetReference()}.{p.GetNumber()}\'s mask opening')
    return issues, checked


def rf_grounds(board, rules_text):
    """RF ground pads solid (no thermal relief), each with a GND via beside it (pass 2 RF-02)."""
    issues, found = [], {}
    pads = pads_by_ref(board)
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    for name in RF_SOLID_GND:
        ref, num = name.split('.')
        p = pads.get((ref, num))
        if not p:
            issues.append(f'{name}: RF ground pad missing')
            continue
        if p.GetNetname() != 'GND':
            issues.append(f'{name}: RF ground pad must be on GND, is {p.GetNetname()}')
        connection = p.GetLocalZoneConnection()
        if connection == pcbnew.ZONE_CONNECTION_INHERITED:
            connection = p.GetParentFootprint().GetLocalZoneConnection()
        if connection != pcbnew.ZONE_CONNECTION_FULL:
            issues.append(f'{name}: RF ground pad needs a solid zone connection (no thermal relief)')
        layer = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        shape = p.GetEffectiveShape(layer)
        best = None
        for v in vias:
            ring = pcbnew.SHAPE_CIRCLE(v.GetPosition(), v.GetWidth(layer) // 2)
            for k in range(1, 61):                      # edge-to-edge distance to 0.01 mm
                if shape.Collide(ring, MM(0.01 * k)):
                    best = k * 0.01 if best is None else min(best, k * 0.01)
                    break
        found[name] = best
        if best is None or best > RF_GND_VIA:
            issues.append(f'{name}: no GND via within {RF_GND_VIA} mm of the pad (nearest {best})')
    return issues, found


def rf_stitching(board):
    """Fence along y = FENCE_Y (GND vias <= FENCE_PITCH apart except the named openings); GND vias beside each RF line
    (largest gap per side <= STITCH_GAP or its accepted ceiling); In1 GND under every RF track and pad plus IN1_MARGIN,
    except the SMA launch cut-outs (pass 2 RF-05)."""
    issues, evidence = [], {}
    gnd = [xy(t.GetPosition()) for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    fence = sorted(x for x, y in gnd if abs(y - FENCE_Y) < 0.06)
    pts = [0.0] + fence + [46.0]
    gaps = [(a, b) for a, b in zip(pts, pts[1:]) if b - a > FENCE_PITCH + 1e-6]
    evidence['fence_vias'] = len(fence)
    evidence['fence_openings'] = [(round(a, 2), round(b, 2)) for a, b in gaps]
    for a, b in gaps:
        if not any(lo <= a and b <= hi for lo, hi in FENCE_OPENINGS):
            issues.append(f'strip fence: GND vias {b - a:.2f} mm apart between x {a:.2f} and {b:.2f} '
                          f'(maximum {FENCE_PITCH} mm outside the named openings)')
    pads = pads_by_ref(board)
    for run, (nets, jack, module) in RF_RUNS.items():
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
        y0 = mm(jack_pad.GetBoundingBox().GetBottom())            # the jack's legs ground the line up to here
        y1 = mm(mod_pad.GetBoundingBox().GetTop())                # the module's GND pins flank its RF pad from here
        main = [(a, b) for a, b in segs if abs(a[0] - b[0]) < 1e-6]   # the line runs along y; the pi row crosses x
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
            limit = STITCH_ACCEPTED.get((run, side), STITCH_GAP)
            evidence[f'{run}_{side}_largest_gap_mm'] = round(gap, 2)
            if gap > limit + 1e-6:
                issues.append(f'{run} {side}: GND stitching gap {gap:.2f} mm beside the RF line (maximum {limit} mm)')
    # In1 under the RF copper
    in1 = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.In1_Cu)]
    launch = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetZoneName().startswith('R7_J3')
              and z.GetZoneName().endswith('_launch_In1')]
    fill = pcbnew.SHAPE_POLY_SET()
    for z in in1:
        fill.BooleanAdd(z.GetFilledPolysList(pcbnew.In1_Cu))
    cut = pcbnew.SHAPE_POLY_SET()
    for z in launch:
        cut.BooleanAdd(z.Outline())
    rf_nets = {n for nets, _, _ in RF_RUNS.values() for n in nets}
    items = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in rf_nets]
    # the SMA centre pads are the launches, deliberately without In1 under them (their cut-out areas are checked in
    # rf_strip); every other RF pad and track needs the plane
    items += [p for f in board.GetFootprints() if f.GetReference() not in JACKS for p in f.Pads()
              if p.GetNetname() in rf_nets]
    inside = pcbnew.SHAPE_POLY_SET()
    inside.NewOutline()
    for x, y in ((0, 0), (46, 0), (46, 200), (0, 200)):
        inside.Append(MM(x), MM(y))
    missing = 0.0
    for it in items:
        poly = pcbnew.SHAPE_POLY_SET()
        it.TransformShapeToPolygon(poly, pcbnew.F_Cu, MM(IN1_MARGIN), MM(0.005), pcbnew.ERROR_OUTSIDE)
        poly.BooleanIntersection(inside)
        poly.BooleanSubtract(fill)
        poly.BooleanSubtract(cut)
        area = poly.Area() / 1e12
        if area > 0.001:
            missing += area
            name = it.GetParentFootprint().GetReference() + '.' + it.GetNumber() if isinstance(it, pcbnew.PAD) \
                else f'{it.GetNetname()} track at {xy(it.GetStart())}'
            issues.append(f'In1: GND missing under {name} (+{IN1_MARGIN} mm): {area:.3f} mm2')
    evidence['in1_missing_mm2'] = round(missing, 4)
    return issues, evidence


def u31_body_keepout(board):
    """U31_KEEPOUT areas cover U31's whole body on B.Cu and In2 (RF-05)."""
    issues = []
    areas = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'U31_KEEPOUT']
    x0, y0, x1, y1 = U31_BODY
    for layer in (pcbnew.B_Cu, pcbnew.In2_Cu):
        body = pcbnew.SHAPE_POLY_SET()
        body.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            body.Append(MM(x), MM(y))
        for z in areas:
            if z.IsOnLayer(layer):
                body.BooleanSubtract(z.Outline())
        if body.Area() / 1e12 > 0.001:
            issues.append(f'U31_KEEPOUT does not cover the module body on {board.GetLayerName(layer)} '
                          f'({body.Area() / 1e12:.2f} mm2 uncovered)')
    return issues


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
            if name in RF_SOLID_GND:                      # solid by RF rule (rf_grounds checks it)
                continue
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
                'J2': ('3V3', 'SWDIO', 'NRST', 'SWCLK', 'GND', 'NC')}
    seen = defaultdict(lambda: defaultdict(set))
    texts = []
    for item in board.GetDrawings():
        if not isinstance(item, pcbnew.PCB_TEXT) or item.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            continue
        texts.append(item)
        match = re.match(r'^(J\d+)\s+(.+)', item.GetText())
        if match and match[1] in required:
            for pin, name in re.findall(r'(\d+):([A-Z0-9]+)', match[2]):
                seen[match[1]][int(pin)].add(name)
    issues = [f'{ref}.{pin}: silkscreen must identify {name} (UART names at module)'
              for ref, names in required.items() for pin, name in enumerate(names, 1)
              if seen[ref][pin] != {name}]
    # SMA jack legends (F10 / step B brief): GNSS at J30, RADIO at J31, each nearer its own jack than the other
    for ref, other, word in (('J30', 'J31', 'GNSS'), ('J31', 'J30', 'RADIO')):
        f, g = board.FindFootprintByReference(ref), board.FindFootprintByReference(other)
        if not f or not g:
            continue
        ok = [t for t in texts if t.GetText().strip() == word and
              math.dist(xy(t.GetPosition()), xy(f.GetPosition())) < 10 and
              math.dist(xy(t.GetPosition()), xy(f.GetPosition())) < math.dist(xy(t.GetPosition()), xy(g.GetPosition()))]
        if not ok:
            issues.append(f'{ref}: silkscreen legend "{word}" required beside the jack')
    return issues


LEGEND_REACH = 6.0               # mm: m3_design/r7_post.LEGEND_REACH (fix pass 7)
WORD_LEGENDS = {'ARM': 'J124', 'IGN': 'J121', 'BAT': 'J1', 'CAM': 'J9', 'SWD': 'J2', 'SERVO': 'J122', 'PULL': 'J123',
                'GNSS': 'J30', 'RADIO': 'J31'}


def _box_gap(a, c):
    dx = max(c[0] - a[2], a[0] - c[2], 0.0)
    dy = max(c[1] - a[3], a[1] - c[3], 0.0)
    return math.hypot(dx, dy)


def legend_subjects(board, distance_review=None):
    """Fix pass 7 (AGENTS.md silkscreen rule, P6-DOCS-04(d)): every board legend about a part (its text starts with
    that part's designator, J124: ..., or is one of the connector words ARM / IGN / BAT / CAM / SWD / SERVO / PULL /
    GNSS / RADIO) has its ink within LEGEND_REACH of that part's courtyard box, and names a part on the board.
    Optional distance_review collects distance findings only (R10 AUD-10); missing subjects always fail."""
    issues = []
    for t in board.GetDrawings():
        if not isinstance(t, pcbnew.PCB_TEXT) or t.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            continue
        text = t.GetText().strip()
        m = re.match(r'^([A-Z]+\d+)(?=[\s:])', text)
        ref = m[1] if m else WORD_LEGENDS.get(text)
        if ref is None:
            continue
        f = board.FindFootprintByReference(ref)
        if f is None:
            issues.append(f'silkscreen legend {text!r} names {ref}, which is not on the board')
            continue
        c = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
        r = c.BBox() if c.OutlineCount() else f.GetBoundingBox(False)
        box = (pcbnew.ToMM(r.GetX()), pcbnew.ToMM(r.GetY()), pcbnew.ToMM(r.GetRight()), pcbnew.ToMM(r.GetBottom()))
        ps = pcbnew.SHAPE_POLY_SET()
        t.TransformShapeToPolygon(ps, t.GetLayer(), 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
        q = ps.BBox()
        ink = (pcbnew.ToMM(q.GetX()), pcbnew.ToMM(q.GetY()), pcbnew.ToMM(q.GetRight()), pcbnew.ToMM(q.GetBottom()))
        g = _box_gap(ink, box)
        if g > LEGEND_REACH:
            target = issues if distance_review is None else distance_review
            target.append(f'silkscreen legend {text!r} is {g:.1f} mm from {ref} (maximum {LEGEND_REACH} mm)')
    return issues


def check_board(board, folder):
    issues, notes, evidence = check_contract(board, folder)
    issues.extend(duplicate_ids(board))
    issues.extend(pin_legends(board))
    issues.extend(legend_subjects(board))
    found, evidence['rf_strip_items'] = rf_strip(board); issues.extend(found)
    copper = copper_shapes(board)
    found, evidence['guarded_pads'] = foreign_clearances(board, copper); issues.extend(found)
    issues.extend(vias_on_through_pads(board))
    found, evidence['smd_pads_checked_for_via_holes'] = vias_in_smd_pads(board); issues.extend(found)
    found, evidence['rf_stitching'] = rf_stitching(board); issues.extend(found)
    found, evidence['track_endpoints_checked'] = overlap_only_joints(board, copper); issues.extend(found)
    rule_file = folder / (Path(board.GetFileName()).stem + '.kicad_dru')
    found, evidence['small_ground_pads'] = thermal_policy(board, rule_file.read_text() if rule_file.is_file() else '')
    issues.extend(found)
    found, evidence['rf_ground_via_mm'] = rf_grounds(board, ''); issues.extend(found)
    found, evidence['launch_in2_reference'] = launch_reference(board); issues.extend(found)
    found, evidence['module_ground'] = module_ground(board); issues.extend(found)
    found, evidence['strip_gnd_reach_mm'] = rf_gnd_reach(board); issues.extend(found)
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
    print('R7 CAD contract:', 'OK' if report['ok'] else f"FAIL ({len(report['issues'])} findings)")
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
