#!/usr/bin/env python3
"""R10 host-only conditional diagnostics. No arguments: synthetic JSONL protocol.

Explicit ``manual``, ``template`` and ``points`` commands require the saved PCB.
Uses only the standard library; no device, network or output-control access.
See R10_OFFLINE.md for manual evidence semantics and limits.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys

BOARD_SHA = '6d23d1e5ca477a9754b55a8830fee6e4554b6cb74903593de075c0ede7b60153'
PROFILE_SHA = 'fe04ece06d2706b79b647daa119879c4f2b9eca883a7ee8b795b18ffe9b6c669'
PROFILE = 'M3-ASSY-R10'
MODULES = ('GPS', 'RADIO', 'AUX', 'CAMERA')
DIRECT = ('J410', 'J420', 'J440')
METHOD = 'prior_unpowered_continuity_record_no_subsequent_rewire'
MAX_JSON = 2_000_000
# Reference allocations from public protocol, NOT device failure thresholds.
BANDS = {'3V3': (3.135, 3.465), '3V3A': (3.135, 3.465),
         'CAM_IO_3V3': (3.135, 3.465), 'PORT_5V3': (5.367, 5.546),
         'PORT_4V8': (4.71, 4.87)}
PREFERRED = {'BAT_IN': 'TP80.1', 'RAW_PROTECTED': 'TP81.1',
             'VBUS': 'C83.1', 'USB_LIMITED': 'TP82.1', 'VLOGIC': 'TP83.1',
             '3V3': 'C9.1', '3V3A': 'R164.2', 'PORT_5V3': 'C403.1',
             'PORT_4V8': 'J410.1', 'CAM_5V': 'J9.1',
             'CAM_IO_3V3': 'C92.1', 'CAM_PWR_EN': 'R431.1'}
LABELS = {
    'battery_input': '电池输入或输入线／接点',
    'battery_protected_branch': 'BAT_IN→RAW_PROTECTED 保护、使能、供电或负载',
    'usb_input': 'USB 电源、线缆或 VBUS 输入接点',
    'usb_limited_branch': 'VBUS→USB_LIMITED 限流、供电或负载',
    'logic_selection_branch': '所选电源→VLOGIC 选择、供电或负载',
    'logic_conversion_branch': 'VLOGIC→3V3 转换、供电或负载',
    'peripheral_conversion_branch': 'RAW_PROTECTED→PORT_5V3 转换、供电或共用负载',
    'direct_port_supply_branch': 'PORT_5V3→PORT_4V8 共用供电或外接负载／线束',
    'sensor_supply_branch': '3V3→R164→3V3A 滤波、连接或传感器电源负载',
    'camera_power_branch': 'PORT_5V3→CAM_5V 开关、控制、供电或负载',
    'camera_interface_supply_branch': 'CAM_5V→CAM_IO_3V3 供电、稳压或接口负载',
}
LIMITS_ZH = (
    '仅为所记录稳态的条件性分支定位；缺测不等于 0 V。',
    '静态电压不能区分开路、限流、短路、使能状态或单颗芯片损坏；信号回灌仍可掩盖故障。',
    '没有整板 PASS、实体资格或 R10 固件验证；启动、瞬态、热、通信和传感器功能均未验证。',
    '坐标是 PCB 顶视投影，底层不镜像；原生焊盘身份不证明实际可探测空间。',
    'J410/J420/J440 的模块 TX 高电平限制为 3.6 V，尚未核实；J9 电源不同且 TX/RX 顺序相反，不可互换。',
    '所列位置仅用于核对离线记录或断电检查；本程序不提供加电、换线、引脚写入或输出测试步骤。',
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def finite_tree(x):
    if isinstance(x, float):
        require(math.isfinite(x), 'Nonfinite numeric evidence')
    elif isinstance(x, dict):
        for v in x.values():
            finite_tree(v)
    elif isinstance(x, list):
        for v in x:
            finite_tree(v)


def loads(text):
    require(len(text) <= MAX_JSON, 'JSON exceeds 2 MB')
    def pairs(items):
        d = {}
        for k, v in items:
            require(k not in d, 'Duplicate JSON key: ' + k)
            d[k] = v
        return d
    result = json.loads(text, object_pairs_hook=pairs)
    finite_tree(result)
    return result


def regular_bytes(path, maximum=16_000_000):
    """Only regular host files; reject symlinks, pipes and device nodes."""
    p = Path(path)
    s = p.lstat()
    require(stat.S_ISREG(s.st_mode), 'Expected a regular host file: ' + str(p))
    require(s.st_size <= maximum, 'Host file exceeds size bound')
    require(all(hasattr(os, flag) for flag in ('O_NONBLOCK', 'O_NOFOLLOW')),
            'Host does not support bounded no-follow regular-file reads')
    # The path may change after lstat. Open without following a replacement
    # symlink or blocking on a replacement FIFO, and validate the open file.
    try:
        fd = os.open(p, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    except OSError as exc:
        raise ValueError('Cannot open regular host file: ' + str(p)) from exc
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        require(stat.S_ISREG(opened.st_mode), 'Expected an open regular host file')
        require(opened.st_size <= maximum, 'Host file exceeds size bound')
        data = stream.read(maximum + 1)
    require(len(data) <= maximum, 'Host file grew beyond size bound')
    return data


def document(path):
    return loads(regular_bytes(path, MAX_JSON).decode('utf-8'))


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def fields(obj, required, optional=()):
    require(isinstance(obj, dict), 'Expected object')
    require(set(required) <= obj.keys() and obj.keys() <= set(required) | set(optional),
            'Missing or unexpected fields: ' + ','.join(sorted(set(required) ^ obj.keys())))


def number(x):
    require(type(x) in (int, float), 'Expected finite number')
    try:
        finite = math.isfinite(x)
    except OverflowError:
        finite = False
    require(finite, 'Expected finite number')
    return x


def identifier(x):
    require(isinstance(x, str) and 0 < len(x.strip()) <= 200, 'Nonempty identifier required')


def timestamp(x):
    require(isinstance(x, str), 'Timezone timestamp required')
    d = datetime.fromisoformat(x.replace('Z', '+00:00'))
    require(d.tzinfo is not None, 'Timezone timestamp required')
    return d


class Profile:
    """Pinned native catalog. Synthetic transport never authenticates a physical PCB."""
    def __init__(self, path=None, *, board=None, synthetic=False):
        self.data = document(path or Path(__file__).with_name('r10_profile.json'))
        require(hashlib.sha256(canonical(self.data)).hexdigest() == PROFILE_SHA,
                'Wrong native catalog/profile identity')
        self.synthetic = synthetic
        require(board is not None or synthetic, 'Normal host use requires actual --board bytes')
        if board is not None:
            require(hashlib.sha256(regular_bytes(board)).hexdigest() == BOARD_SHA,
                    'Wrong board bytes: expected ' + BOARD_SHA)
        self.board_checked = board is not None
        self.points = self.data['points']

    def point(self, key):
        return copy.deepcopy(self.points[key])

    def identity(self, value, ground=False):
        require(isinstance(value, dict), 'Missing native point identity')
        p = self.points.get(value.get('point_id'))
        require(p is not None, 'Wrong native pad/net/side/XY/frame')
        value = copy.deepcopy(value)
        xy = value.get('xy_mm')
        require(isinstance(xy, list) and len(xy) == 2, 'Wrong native coordinates')
        require(all(number(a) == b for a, b in zip(xy, p['xy_mm'])), 'Wrong native coordinates')
        # JSON 38 and 38.0 identify the same native coordinate; True is not 1.
        value['xy_mm'] = p['xy_mm']
        require(canonical(value) == canonical(p), 'Wrong native pad/net/side/XY/frame')
        if ground:
            require(p['point_id'] in self.data['ground_point_ids'] and p['net'] == 'GND',
                    'Not an offered native GND reference')
        return p['net']

    def ground(self, point):
        key = point['reference'] + '.2'
        if key not in self.data['ground_point_ids']:
            key = 'TP74.1' if point['net'] in ('3V3A', 'CAM_IO_3V3', 'CAM_PWR_EN') else 'TP88.1'
        return self.point(key)


def validate_map(mapping):
    fields(mapping, MODULES)
    require(mapping['CAMERA'] == 'J9' and sorted(mapping[m] for m in MODULES[:3]) == sorted(DIRECT),
            'GPS/RADIO/AUX must be a permutation; CAMERA must use J9')


def validate_interval(m):
    require(m['unit'] == 'V', 'Wrong measurement unit')
    v = m['interval']
    require(isinstance(v, list) and len(v) == 2, 'Closed interval required')
    lo, hi = map(number, v)
    u = number(m['uncertainty_abs_v'])
    require(lo <= hi and u > 0, 'Invalid interval/uncertainty')
    # Declared +/- uncertainty must fit inside the reported enclosure. Wider
    # enclosures are retained; repeated measurements NEVER reduce uncertainty.
    width, required_width = hi - lo, 2 * u
    number(width); number(required_width)
    require(width >= required_width or math.isclose(width, required_width, rel_tol=1e-12, abs_tol=0),
            'Interval understates declared uncertainty')


def validate_measurement(m, profile, origin, epoch, *, port=None, manual_meta=()):
    base = ['status', 'origin', 'epoch'] + list(manual_meta)
    if port is None:
        base += ['type', 'point', 'ground']
    else:
        base += ['location_kind', 'positive', 'negative', 'installed_port']
    require(isinstance(m, dict), 'Measurement must be an object')
    require(m.get('status') in ('AVAILABLE', 'NOT_AVAILABLE'), 'Unknown measurement status')
    if m['status'] == 'AVAILABLE':
        base += ['unit', 'interval', 'uncertainty_abs_v']
    fields(m, base)
    require(m['origin'] == origin and m['epoch'] == epoch, 'Mixed origin or stale epoch')
    if port is None:
        require(m['type'] == 'measurement', 'Not a measurement')
        profile.identity(m['point']); profile.identity(m['ground'], ground=True)
    else:
        kind = 'FIXTURE_MODULE_TERMINALS' if origin == 'SYNTHETIC_FIXTURE' else 'MANUAL_MODULE_TERMINALS'
        require((m['location_kind'], m['positive'], m['negative'], m['installed_port']) ==
                (kind, 'VPLUS', 'GND', port), 'Wrong module terminals or installed port')
    if m['status'] == 'AVAILABLE':
        validate_interval(m)


def validate_wiring(w, profile, origin, extras=()):
    require(isinstance(w, dict) and w.get('status') in ('AVAILABLE', 'NOT_AVAILABLE'), 'Bad wiring record')
    keys = ['status', 'origin']
    if w['status'] == 'AVAILABLE':
        keys += ['method', 'module_TX_to', 'module_RX_to'] + list(extras)
    fields(w, keys)
    require(w['origin'] == origin, 'Mixed wiring origin')
    if w['status'] == 'AVAILABLE':
        require(w['method'] == METHOD, 'UART evidence requires prior unpowered unchanged harness record')
        profile.identity(w['module_TX_to']); profile.identity(w['module_RX_to'])


class Engine:
    """Evidence ledger and causal graph; no fixture identifiers or response banks."""
    def __init__(self, profile, port_map, context, origin):
        self.profile, self.ports, self.context, self.origin = profile, port_map, context, origin
        self.rows = {}  # metadata-free conservative enclosures of AVAILABLE tokens
        self.observation_records = {}  # original observations, including unavailable ones
        self.consistency = {}  # overlap for contradiction detection ONLY, never precision
        self.attempted = set()
        self.conflicts = set()
        self.wiring = {}
        self.count = 0
        self.pending = None
        self.exhausted = False

    def add(self, m, module=None):
        if module is None:
            self.attempted.add(m['point']['point_id'])
            token = 'net:' + m['point']['net']
        else:
            token = 'module:' + module + ':supply'
        self.observation_records.setdefault(token, []).append(copy.deepcopy(m))
        if m['status'] != 'AVAILABLE':
            return
        low, high = m['interval']
        if token in self.consistency:
            prior_low, prior_high = self.consistency[token]
            low, high = max(low, prior_low), min(high, prior_high)
        self.consistency[token] = [low, high]
        if low > high:
            self.conflicts.add(token)
        old = self.rows.get(token)
        interval = list(m['interval'])
        uncertainty = m['uncertainty_abs_v']
        if old is not None:
            # The union is conservative and cannot hide disjoint contributors:
            # the separate consistency bound above detects those in any order.
            interval = [min(old['interval'][0], interval[0]), max(old['interval'][1], interval[1])]
            uncertainty = max(old['max_declared_uncertainty_abs_v'], uncertainty)
        self.rows[token] = {'kind': 'CONSERVATIVE_ENVELOPE', 'unit': 'V',
                            'interval': interval, 'max_declared_uncertainty_abs_v': uncertainty}

    def interval(self, node):
        token = node if node.startswith('module:') else 'net:' + node
        if token in self.conflicts or token not in self.rows:
            return None
        return self.rows[token]['interval']

    def positive(self, node):
        v = self.interval(node)
        return v is not None and v[0] > 0

    def within(self, node, bounds=None):
        v = self.interval(node)
        bounds = bounds or BANDS.get(node)
        return v is not None and bounds is not None and bounds[0] <= v[0] <= v[1] <= bounds[1]

    def collapsed(self, node, parent=None):
        v = self.interval(node)
        if v is None or not v[0] <= 0 <= v[1]:
            return False
        # Zero-compatible alone is not enough: interval must exclude a known
        # reference band or a separated, observed upstream voltage.
        bound = BANDS.get(node)
        if bound:
            return v[1] < bound[0]
        if parent and self.interval(parent):
            return v[1] < self.interval(parent)[0]
        if node in ('BAT_IN', 'VBUS') and self.origin == 'MANUAL_OFFLINE':
            return v[1] < self.context['source_reference_v'][0]
        if self.origin == 'SYNTHETIC_FIXTURE':
            # Public fixture construction windows only, never physical limits.
            if node.startswith('module:') or node == 'CAM_5V':
                floor = 5.367 if node in ('CAM_5V', 'module:CAMERA:supply') else 4.71
            else:
                floor = 7.1 if self.source() == 'PACK' else 4.9
            return v[1] < floor
        return False

    def low_hint(self, node):
        v = self.interval(node)
        if v is None:
            return True
        return v[0] <= 0 <= v[1] or (node in BANDS and v[1] < BANDS[node][0])

    def source(self):
        return self.context.get('selected_source', self.context['attached_source'])

    def pack(self):
        return self.context['attached_source'] in ('PACK', 'BOTH')

    def camera(self):
        v = self.interval('CAM_PWR_EN')
        # TPS2553 Rev G §6.3/6.5: guaranteed EN input levels; not an output command.
        if v is None:
            return 'UNKNOWN'
        if 1.1 <= v[0] <= v[1] <= 6.5:
            return 'ON'
        if 0 <= v[0] <= v[1] <= 0.66:
            return 'OFF'
        return 'UNKNOWN'

    def graph(self):
        """Directed possible supply/feed/loading classes, conditioned on source."""
        edges = []
        source = self.source()
        if source == 'PACK' or self.pack():
            edges.append(('battery_protected_branch', 'BAT_IN', 'RAW_PROTECTED'))
        if self.context['attached_source'] in ('USB', 'BOTH'):
            edges.append(('usb_limited_branch', 'VBUS', 'USB_LIMITED'))
        if source in ('PACK', 'USB'):
            edges.append(('logic_selection_branch', 'RAW_PROTECTED' if source == 'PACK' else 'USB_LIMITED', 'VLOGIC'))
        edges += [('logic_conversion_branch', 'VLOGIC', '3V3'),
                  ('sensor_supply_branch', '3V3', '3V3A')]
        if self.pack():
            edges += [('peripheral_conversion_branch', 'RAW_PROTECTED', 'PORT_5V3'),
                      ('direct_port_supply_branch', 'PORT_5V3', 'PORT_4V8')]
            if self.camera() == 'ON':
                edges.append(('camera_power_branch', 'PORT_5V3', 'CAM_5V'))
            if self.positive('CAM_5V'):
                edges.append(('camera_interface_supply_branch', 'CAM_5V', 'CAM_IO_3V3'))
            for module in MODULES:
                edges.append(('module_power:' + module, 'CAM_5V' if module == 'CAMERA' else 'PORT_4V8',
                              'module:' + module + ':supply'))
        return edges

    def upstream_supported(self, parent, child):
        if parent in BANDS:
            return self.within(parent)
        # Minimum regulator input is a design operating condition (M3_R10),
        # not a failure threshold. Source windows are operator-declared context.
        if child == '3V3':
            v = self.interval(parent)
            return v is not None and v[0] >= 3.8
        if parent == 'CAM_5V':
            return self.within(parent, BANDS['PORT_5V3'])
        if self.origin == 'SYNTHETIC_FIXTURE':
            return self.positive(parent)
        return self.within(parent, self.context['source_reference_v'])

    def assumptions_supported(self):
        if self.origin == 'SYNTHETIC_FIXTURE':
            return True
        return (self.context['steady'] is True and self.context['backfeed_excluded'] is True
                and self.context['ground_reference_verified'] is True
                and self.context['external_self_power'] is False
                and self.context['selected_source'] in ('PACK', 'USB')
                and self.context['attached_source'] in ('PACK', 'USB')
                and (not self.pack() or self.context['battery_path_expected'] is True))

    def causes(self):
        found = {}
        # Conflicting voltage records invalidate voltage inference, not the
        # separately validated prior-unpowered harness continuity evidence.
        if not self.conflicts and self.assumptions_supported():
            for cause, parent, child in self.graph():
                if self.upstream_supported(parent, child) and self.collapsed(child, parent):
                    tokens = ['net:' + parent, child if child.startswith('module:') else 'net:' + child]
                    if cause == 'camera_power_branch':
                        tokens.append('net:CAM_PWR_EN')
                    found[cause] = tokens
            for node, cause, source in [('BAT_IN', 'battery_input', 'PACK'), ('VBUS', 'usb_input', 'USB')]:
                if self.context['attached_source'] in (source, 'BOTH') and self.collapsed(node):
                    found[cause] = ['net:' + node]
        # UART diagnoses depend on historical unpowered continuity, never DC UART levels.
        for module, w in self.wiring.items():
            if w['status'] == 'AVAILABLE':
                port = self.ports[module]
                tx, rx = ('3', '4') if port == 'J9' else ('4', '3')
                if w['module_TX_to']['point_id'] != port + '.' + tx or w['module_RX_to']['point_id'] != port + '.' + rx:
                    found['uart_harness:' + module] = ['wiring:' + module]
        return found

    def choose_point(self, net):
        preferred = PREFERRED[net]
        # Native port placement follows installation, not the printed device label.
        if net == 'PORT_4V8':
            suspects = [m for m in MODULES[:3] if self.low_hint('module:' + m + ':supply')]
            preferred = self.ports[suspects[0] if suspects else 'GPS'] + '.1'
        choices = [preferred] + sorted(k for k, p in self.profile.points.items()
                                       if p['net'] == net and k != preferred)
        return next((self.profile.point(k) for k in choices if k not in self.attempted), None)

    def next_probe(self, *, respect_budget=True):
        """Prioritize the observed low node's missing upstream boundary, then
        branch coverage. Unavailable points may use a different native pad.
        No repeated net sampling after AVAILABLE; budget includes unavailability.
        """
        if (respect_budget and self.count >= 6) or self.conflicts or self.exhausted:
            return None
        needs = {}
        def want(net, priority):
            if self.interval(net) is None and net not in {'GND'}:
                needs[net] = max(priority, needs.get(net, 0))
        for _, parent, child in self.graph():
            if self.interval(child) is not None and self.low_hint(child):
                want(parent, 100)
        want('3V3', 95)
        if self.positive('3V3'):
            want('3V3A', 70)
        if self.low_hint('3V3'):
            want('VLOGIC', 98)
        if self.pack():
            direct_low = any(self.low_hint('module:' + m + ':supply') for m in MODULES[:3])
            want('PORT_4V8', 90 if direct_low else 40)
            cam_low = self.low_hint('module:CAMERA:supply')
            want('CAM_5V', 88 if cam_low else 45)
            if cam_low or self.low_hint('CAM_5V'):
                want('CAM_PWR_EN', 92 if self.interval('CAM_5V') is not None else 60)
            if self.positive('CAM_5V') or self.camera() == 'ON':
                want('CAM_IO_3V3', 75)
            # When EN was unknown the camera power edge could not yet be used.
            if self.camera() == 'ON' and self.low_hint('CAM_5V'):
                want('PORT_5V3', 100)
        for net, _ in sorted(needs.items(), key=lambda pair: (-pair[1], pair[0])):
            p = self.choose_point(net)
            if p:
                return {'type': 'probe', 'point': p, 'ground': self.profile.ground(p)}
        return None

    def screening_complete(self):
        if self.conflicts or not self.assumptions_supported() or not self.within('3V3') or not self.within('3V3A'):
            return False
        if any(self.interval('module:' + m + ':supply') is None for m in MODULES):
            return False
        def off(node, reference_floor):
            v = self.interval(node)
            return v is not None and v[0] <= 0 <= v[1] < reference_floor
        if not self.pack():
            for net, band in [('PORT_5V3', 'PORT_5V3'), ('PORT_4V8', 'PORT_4V8'),
                              ('CAM_5V', 'PORT_5V3'), ('CAM_IO_3V3', 'CAM_IO_3V3')]:
                if self.interval(net) is not None and not off(net, BANDS[band][0]):
                    return False
            return all(off('module:' + m + ':supply', BANDS['PORT_5V3' if m == 'CAMERA' else 'PORT_4V8'][0]) for m in MODULES)
        if any(self.interval(n) is not None and not self.within(n) for n in ('PORT_5V3', 'PORT_4V8')):
            return False
        # These conservative reference screens cannot establish a module's
        # operating limits or cable acceptance; outside them stays unresolved.
        if not self.within('PORT_4V8') or not all(self.within('module:' + m + ':supply', BANDS['PORT_4V8']) for m in MODULES[:3]):
            return False
        if self.camera() == 'OFF':
            return (off('CAM_5V', BANDS['PORT_5V3'][0]) and off('module:CAMERA:supply', BANDS['PORT_5V3'][0])
                    and (self.interval('CAM_IO_3V3') is None or off('CAM_IO_3V3', BANDS['CAM_IO_3V3'][0])))
        if self.interval('CAM_PWR_EN') is not None and self.camera() == 'UNKNOWN':
            return False
        return (self.within('CAM_5V', BANDS['PORT_5V3']) and
                self.within('module:CAMERA:supply', BANDS['PORT_5V3']) and self.within('CAM_IO_3V3'))

    def target_points(self, cause):
        if cause.startswith(('module_power:', 'uart_harness:')):
            port = self.ports[cause.split(':')[1]]
            pads = ('1', '2') if cause.startswith('module_power:') else ('3', '4')
            return [self.profile.point(port + '.' + pad) for pad in pads]
        if cause == 'sensor_supply_branch':
            return [self.profile.point('R164.1'), self.profile.point('R164.2')]
        for c, parent, child in self.graph():
            if c == cause:
                return [self.profile.point(PREFERRED[n]) for n in (parent, child)]
        return [self.profile.point('TP80.1' if cause == 'battery_input' else 'C83.1')]

    def result(self):
        causes = self.causes()
        if causes:
            cause = next(iter(causes))
            action = ('INSPECT_UNPOWERED_MODULE_HARNESS' if cause.startswith('module_power:') else
                      'VERIFY_UNPOWERED_UART_ORDER' if cause.startswith('uart_harness:') else 'INSPECT_UNPOWERED_BRANCH')
            step = {'action': action, 'target_cause': cause, 'target_points': self.target_points(cause)}
            status = 'LOCALIZED'
        else:
            complete = self.screening_complete()
            status = 'NO_DEMONSTRATED_FAULT_WITHIN_OBSERVATIONS' if complete else 'INSUFFICIENT_EVIDENCE'
            step = {'action': 'REVIEW_UNVERIFIED_FIRMWARE' if complete else 'REQUEST_MISSING_MEASUREMENTS',
                    'target_cause': None}
        return {'type': 'result', 'status': status, 'candidate_causes': list(causes),
                'evidence': [{'cause': c, 'observations': t} for c, t in causes.items()],
                'next_step': step, 'physical_qualified': False, 'firmware_verified': False}


class Session:
    """One independent synthetic initial -> probe -> measurement -> result session."""
    def __init__(self, initial, profile=None):
        self.profile = profile or Profile(synthetic=True)
        finite_tree(initial)
        fields(initial, ('type', 'protocol', 'profile', 'board_sha256', 'origin', 'installed_port_map',
                         'power_context', 'observations', 'probe_budget', 'physical_qualified', 'firmware_verified'))
        require(initial['type'] == 'initial' and initial['protocol'] == 'r10-offline-diagnostic/v1', 'Wrong protocol')
        require(initial['profile'] == PROFILE and initial['board_sha256'] == BOARD_SHA, 'Wrong revision')
        require(initial['origin'] == 'SYNTHETIC_FIXTURE', 'JSONL mode is synthetic-only; use manual --board')
        require(initial['physical_qualified'] is False and initial['firmware_verified'] is False, 'Unsupported qualification')
        require(type(initial['probe_budget']) is int and initial['probe_budget'] == 6, 'Protocol budget must be six')
        validate_map(initial['installed_port_map'])
        c = initial['power_context']
        fields(c, ('attached_source', 'steady_observation_epoch', 'external_self_power', 'recovery_loads_connected', 'camera_control'))
        require(c['attached_source'] in ('PACK', 'USB') and c['steady_observation_epoch'] == 'steady_1', 'Wrong source/epoch')
        require(c['external_self_power'] is False and c['recovery_loads_connected'] is False and
                c['camera_control'] == 'hypothetical_static_state_not_a_firmware_claim', 'Unsupported source context')
        self.engine = Engine(self.profile, copy.deepcopy(initial['installed_port_map']), copy.deepcopy(c), 'SYNTHETIC_FIXTURE')
        obs = initial['observations']
        fields(obs, ('logic_supply', 'module_supplies', 'harness_continuity', 'serial'))
        require(obs['serial'] == {'status': 'NOT_AVAILABLE', 'reason': 'NO_BOUND_R10_FIRMWARE'}, 'No R10 serial evidence supported')
        validate_measurement(obs['logic_supply'], self.profile, 'SYNTHETIC_FIXTURE', 'steady_1')
        require(obs['logic_supply']['point']['net'] == '3V3', 'Initial logic supply must be 3V3')
        self.engine.add(obs['logic_supply'])
        fields(obs['module_supplies'], MODULES); fields(obs['harness_continuity'], MODULES)
        for m in MODULES:
            v = obs['module_supplies'][m]
            validate_measurement(v, self.profile, 'SYNTHETIC_FIXTURE', 'steady_1', port=self.engine.ports[m])
            self.engine.add(v, m)
            w = obs['harness_continuity'][m]
            validate_wiring(w, self.profile, 'SYNTHETIC_FIXTURE')
            self.engine.wiring[m] = copy.deepcopy(w)
        self.done = False

    def advance(self, measurement=None):
        require(not self.done, 'Session already terminated')
        e = self.engine
        if measurement is not None:
            require(e.pending is not None, 'Unsolicited measurement')
            validate_measurement(measurement, self.profile, e.origin, 'steady_1')
            require(measurement['point'] == e.pending['point'] and measurement['ground'] == e.pending['ground'],
                    'Response does not echo requested point/ground')
            e.add(measurement)
            e.pending = None
        else:
            require(e.pending is None, 'A probe response is still pending')
        probe = e.next_probe()
        if probe is not None:
            e.pending = probe
            e.count += 1
            return copy.deepcopy(probe)
        self.done = True
        return e.result()


MANUAL_META = ('assembly_id', 'session_id', 'configuration_id', 'measured_at', 'instrument', 'uncertainty_basis')
WIRING_META = ('assembly_id', 'session_id', 'board_sha256', 'harness_id', 'observed_at', 'power_state', 'unchanged_since')


def analyze_manual(record, *, board, profile_path=None):
    p = Profile(profile_path, board=board)
    finite_tree(record)
    fields(record, ('schema', 'profile', 'board_sha256', 'origin', 'assembly_id', 'session_id', 'epoch',
                    'observed_window', 'installed_port_map', 'power_context', 'measurements',
                    'module_supplies', 'harness_continuity'))
    require(record['schema'] == 'r10-manual-offline/v1' and record['origin'] == 'MANUAL_OFFLINE', 'Wrong manual schema/origin')
    require(record['profile'] == PROFILE and record['board_sha256'] == BOARD_SHA, 'Wrong manual revision')
    for key in ('assembly_id', 'session_id', 'epoch'):
        identifier(record[key])
    validate_map(record['installed_port_map'])
    fields(record['observed_window'], ('start', 'end'))
    start, end = (timestamp(record['observed_window'][k]) for k in ('start', 'end'))
    require(start <= end <= datetime.now(timezone.utc), 'Invalid or future observation window')
    c = record['power_context']
    fields(c, ('attached_source', 'selected_source', 'steady', 'configuration_id', 'external_self_power',
               'recovery_loads_connected', 'source_note', 'source_reference_v', 'battery_path_expected',
               'ground_reference_verified', 'backfeed_excluded'))
    require(c['attached_source'] in ('PACK', 'USB', 'BOTH', 'NONE', 'UNKNOWN'), 'Unknown source context')
    require(c['selected_source'] in ('PACK', 'USB', 'UNKNOWN'), 'Unknown selected source')
    require(c['selected_source'] == 'UNKNOWN' or c['attached_source'] in (c['selected_source'], 'BOTH'), 'Contradictory source selection')
    for key in ('steady', 'external_self_power', 'recovery_loads_connected', 'battery_path_expected', 'ground_reference_verified', 'backfeed_excluded'):
        require(type(c[key]) is bool, 'Context flags must be explicit booleans')
    require(c['steady'] and not c['recovery_loads_connected'], 'Only steady observations without recovery loads supported')
    identifier(c['configuration_id']); identifier(c['source_note'])
    v = c['source_reference_v']
    require(isinstance(v, list) and len(v) == 2 and 0 < number(v[0]) < number(v[1]), 'Declared source reference interval required')
    e = Engine(p, copy.deepcopy(record['installed_port_map']), copy.deepcopy(c), 'MANUAL_OFFLINE')
    def check(m, module=None):
        validate_measurement(m, p, e.origin, record['epoch'], port=e.ports[module] if module else None, manual_meta=MANUAL_META)
        for key in ('assembly_id', 'session_id'):
            require(m[key] == record[key], 'Mixed assembly/session')
        require(m['configuration_id'] == c['configuration_id'], 'Changed source configuration')
        require(start <= timestamp(m['measured_at']) <= end, 'Stale measurement outside coherent observation window')
        identifier(m['instrument']); identifier(m['uncertainty_basis'])
        e.add(m, module)
    require(isinstance(record['measurements'], list), 'Measurements must be a list')
    for m in record['measurements']:
        check(m)
    require(isinstance(record['module_supplies'], dict) and record['module_supplies'].keys() <= set(MODULES), 'Unknown module')
    for module, m in record['module_supplies'].items():
        check(m, module)
    require(isinstance(record['harness_continuity'], dict) and record['harness_continuity'].keys() <= set(MODULES), 'Unknown wiring module')
    for module, w in record['harness_continuity'].items():
        validate_wiring(w, p, e.origin, WIRING_META)
        if w['status'] == 'AVAILABLE':
            require(w['assembly_id'] == record['assembly_id'] and w['session_id'] == record['session_id'] and
                    w['board_sha256'] == BOARD_SHA, 'Stale wiring binding')
            require(timestamp(w['observed_at']) < start and w['power_state'] == 'UNPOWERED' and
                    w['unchanged_since'] is True, 'Wiring requires prior unpowered unchanged harness evidence')
            identifier(w['harness_id'])
        e.wiring[module] = copy.deepcopy(w)
    result = e.result()
    unresolved = []
    if not e.assumptions_supported():
        unresolved.append('电源选择、接地或回灌前提未确认，不能定位电源分支。')
    if e.conflicts:
        unresolved.append('同一网络的读数区间不相交，需要核对记录和配置，不能合并推断。')
    if e.pack() and e.camera() == 'UNKNOWN':
        unresolved.append('相机使能状态缺测或电压区间不足以确认逻辑状态，不能判定相机供电开关异常。')
    for net in BANDS:
        if e.interval(net) is not None and not e.within(net) and not e.collapsed(net):
            unresolved.append(net + ' 的记录区间不在参考带内，但不能单独证明该分支损坏。')
    return {'schema': 'r10-manual-report/v1', 'origin': e.origin, 'board_sha256': BOARD_SHA,
            'profile': PROFILE, 'board_bytes_verified': True, 'assembly_id': record['assembly_id'],
            'session_id': record['session_id'], 'epoch': record['epoch'], 'observed_window': record['observed_window'],
            'result': result, 'observed': e.rows, 'observation_records': e.observation_records,
            'conflicting_tokens': sorted(e.conflicts),
            'wiring_observed': e.wiring,
            'unverified_voltage_tokens': ['net:' + n for n in PREFERRED if e.interval(n) is None] +
                ['module:' + m + ':supply' for m in MODULES if e.interval('module:' + m + ':supply') is None],
            'assumptions_supported': e.assumptions_supported(), 'next_probe': e.next_probe(),
            'unresolved_reasons_zh': unresolved,
            'limitations_zh': list(LIMITS_ZH)}


def template(board, profile_path=None):
    Profile(profile_path, board=board)
    now = datetime.now(timezone.utc).isoformat()
    return {'schema': 'r10-manual-offline/v1', 'profile': PROFILE, 'board_sha256': BOARD_SHA,
            'origin': 'MANUAL_OFFLINE', 'assembly_id': 'REPLACE_ASSEMBLY', 'session_id': 'REPLACE_SESSION',
            'epoch': 'REPLACE_STEADY_EPOCH', 'observed_window': {'start': now, 'end': now},
            'installed_port_map': dict(zip(MODULES, (*DIRECT, 'J9'))),
            'power_context': {'attached_source': 'UNKNOWN', 'selected_source': 'UNKNOWN', 'steady': True,
                'configuration_id': 'REPLACE_CONFIGURATION', 'external_self_power': False,
                'recovery_loads_connected': False, 'source_note': 'REPLACE_SOURCE_REFERENCE_BASIS',
                'source_reference_v': [0, 0], 'battery_path_expected': False,
                'ground_reference_verified': False, 'backfeed_excluded': False},
            'measurements': [], 'module_supplies': {}, 'harness_continuity': {}}


def location(p):
    return '%s [reference=%s pad=%s] %s %s XY=(%s, %s) mm；%s' % (p['point_id'], p['reference'], p['pad'],
            p['net'], p['side'], *p['xy_mm'], p['frame'])


def render_zh(report):
    r = report['result']
    lines = ['R10 离线诊断：' + r['status'],
             '来源 MANUAL_OFFLINE；板文件 SHA256 ' + BOARD_SHA,
             '记录会话 %s / epoch %s；只解释该记录时段。' % (report['session_id'], report['epoch']), '已观察：']
    for token, m in report['observed'].items():
        enclosure = '[%s, %s]' % tuple(format(v, '.9g') for v in m['interval'])
        lines.append('  %s 保守包络 %s V（汇总，不是一条仪器读数）' % (token, enclosure))
        for original in report['observation_records'][token]:
            if original['status'] != 'AVAILABLE':
                continue
            bounds = '[%s, %s]' % tuple(format(v, '.9g') for v in original['interval'])
            place = original.get('point', {}).get('point_id', original.get('installed_port', ''))
            lines.append('    %s：%s V；不确定度 %s V；%s；%s；依据 %s' %
                (place, bounds, format(original['uncertainty_abs_v'], '.9g'), original['instrument'],
                 original['measured_at'], original['uncertainty_basis']))
    if not report['observed']:
        lines.append('  没有可用电压记录。')
    for module, w in report['wiring_observed'].items():
        if w['status'] == 'AVAILABLE':
            lines.append('  先前断电连续性 %s：模块 TX→%s，RX→%s；记录后未改线。' %
                         (module, w['module_TX_to']['point_id'], w['module_RX_to']['point_id']))
    if not report['assumptions_supported']:
        lines.append('  电源选择／接地／回灌前提未确认，电源分支结论保持未定。')
    if report['conflicting_tokens']:
        lines.append('  同网记录互相矛盾，拒绝电压观测合并推断：' + ', '.join(report['conflicting_tokens']))
    for reason in report['unresolved_reasons_zh']:
        lines.append('尚未确定：' + reason)
    def label(c):
        if c.startswith('module_power:'):
            return c.split(':')[1] + ' 模块端供电／回流线、接点或局部负载'
        if c.startswith('uart_harness:'):
            return c.split(':')[1] + ' 先前记录的 UART 线序与安装端口方向不符'
        return LABELS[c]
    lines.append('可能分支：' + ('、'.join(label(c) for c in r['candidate_causes']) or '未定位'))
    for ev in r['evidence']:
        lines.append('  %s ← %s' % (ev['cause'], ', '.join(ev['observations'])))
    actions = {'INSPECT_UNPOWERED_BRANCH': '断电检查该分支',
               'INSPECT_UNPOWERED_MODULE_HARNESS': '断电检查模块供电与回流线束',
               'VERIFY_UNPOWERED_UART_ORDER': '核实断电 UART 线序记录',
               'REQUEST_MISSING_MEASUREMENTS': '补充缺失的离线测量记录',
               'REVIEW_UNVERIFIED_FIRMWARE': '固件尚未验证，单独审查其证据'}
    lines.append('下一项：%s（%s）' % (actions[r['next_step']['action']], r['next_step']['action']))
    p = Profile(synthetic=True)
    for pt in r['next_step'].get('target_points', []):
        lines.append('  检查位置 ' + location(pt))
        lines.append('  地参考 ' + location(p.ground(pt)))
    if report['next_probe']:
        lines.append('待补离线电压记录：' + location(report['next_probe']['point']))
        lines.append('  地参考 ' + location(report['next_probe']['ground']))
    if report['unverified_voltage_tokens']:
        lines.append('本记录未覆盖的电压（不代表故障）：' + ', '.join(report['unverified_voltage_tokens']))
    lines.extend(report['limitations_zh'])
    return '\n'.join(lines)


def protocol(stdin, stdout, profile=None):
    """One session per process; stdout contains schema-only JSON, errors use stderr."""
    line = stdin.readline(MAX_JSON + 1)
    require(bool(line), 'Missing JSONL initial')
    session = Session(loads(line), profile)
    message = session.advance()
    while True:
        stdout.write(json.dumps(message, ensure_ascii=False, allow_nan=False) + '\n')
        stdout.flush()
        if message['type'] == 'result':
            return session.engine.count
        line = stdin.readline(MAX_JSON + 1)
        require(bool(line), 'EOF with pending probe; no result invented')
        message = session.advance(loads(line))


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        if not args:
            protocol(sys.stdin, sys.stdout)
            return 0
        parser = argparse.ArgumentParser(description=__doc__)
        subs = parser.add_subparsers(dest='command', required=True)
        for name in ('manual', 'template', 'points'):
            sub = subs.add_parser(name)
            sub.add_argument('--board', required=True, type=Path)
            sub.add_argument('--profile', type=Path)
            if name in ('manual', 'points'):
                sub.add_argument('--json', action='store_true')
            if name == 'manual':
                sub.add_argument('record', type=Path)
        a = parser.parse_args(args)
        if a.command == 'points':
            profile = Profile(a.profile, board=a.board)
            rows = [{'point': point, 'ground': profile.ground(point)}
                    for _, point in sorted(profile.points.items()) if point['net'] != 'GND']
            if a.json:
                print(json.dumps(rows, ensure_ascii=False, indent=2))
            else:
                print('R10 原生位置；底层使用顶视投影，不镜像；实际探测空间未验证。')
                for row in rows:
                    print(location(row['point']))
                    print('  地参考 ' + location(row['ground']))
        elif a.command == 'template':
            print(json.dumps(template(a.board, a.profile), ensure_ascii=False, indent=2))
        else:
            report = analyze_manual(document(a.record), board=a.board, profile_path=a.profile)
            print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) if a.json else render_zh(report))
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as exc:
        print('R10 拒绝输入：' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
