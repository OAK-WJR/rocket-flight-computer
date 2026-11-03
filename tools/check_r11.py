#!/usr/bin/env python3
"""R11 native-CAD contract (M3-ASSY-R11, D-R11-08): R10's contract rules (tools/check_r10.py) re-expressed for R11's
compact six-layer board (F / In1 GND / In2 power / In3 signal / In4 GND / B, D-R11-03), keyed by net, reference and
pad number, never by an R10 coordinate.

usage: <KiCad python3> -I tools/check_r11.py [board.kicad_pcb] [--report out.json] [--fit FIT.json] [--only S-1,M-1]
       [--stage functional|placement|full] [--bom BOM.csv] [--cpl CPL.csv]
exit 0 = every selected rule holds

tools/check.sh runs it after fit_check --profile r11 (--fit). R11 keeps R10's netlist (D-R11-01), so the R10 rule
functions run here on the R11 board wherever they read nets, references and pad numbers only; R10's coordinate tables
are replaced by R11 data (the gate data file R11_DATA, filled by the later stages) or start empty, like route_check's
r11 allowlists. U1's balls come from the R11 pin table (R11_PIN_TABLE, columns 'port' and 'ball' or 'pin'), not R10's
LQFP pin numbers.

Rules (R10's id where it is R10's rule):
  S-1  RAW_ACT pyro bus, named armed-side parts, no bypass (check_r10.s1; DIRECT_ADC balls of PC0 / PC5 from the pin
       table)
  S-2  pyro feed only through the Q120 / Q121 load switch (check_r10.s2)
  S-3  gate networks defined off (check_r10.s3; PC1's ball for ACT_EN_MCU from the pin table)
  S-4  required fitted parts on board, schematic, BOM and CPL; MPN-decoded values (check_r10.s4)
  S-5  J400 arming switch contacts behind their 470 k resistors and D402 (check_r10.s5)
  S-6  external ports apart from pyro / arming copper (check_r10.s6)
  S-7  J122 (JST GH 5-pin): contacts 1-4 SERVO1-4_OUT, 5 GND; only its two fixing tabs besides, on GND or no net
  S-8  on In1..In4 no foreign track, fill or drawing within 1.0 mm of a BARREL_NETS barrel wall or of an inner ring
       it keeps (check_r10.s8 over all four inner layers; GND counts for BARREL_GND_HAZARD only)
  S-9  fire / source copper widths on the current path (check_r10.s9; FIRE_NARROW from R11_DATA, empty by default)
  W-1  D-R11-05 wire pads: J1 = plated pads 1 BAT_IN / 2 GND, J121 = plated pads 1 PYRO1_OUT / 2 PYRO1_IGN, no other
       pad; plated barrels (PTH) only
  W-2  D-R11-05 GH ports: J410 / J420 / J440 1 PORT_4V8, 2 GND, 3 *_TX_WIRE, 4 *_RX_WIRE; J9 1-2 CAM_5V, 3-4 GND,
       5 CAM_RX_WIRE, 6 CAM_TX_WIRE; J400 1 BAT_SW_SOURCE, 2 BAT_SW_RETURN; each a JST GH SMnnB-GHS-TB with its two
       fixing tabs on GND or no net
  LC-1 local clearance overrides respect their floors (check_r10.lc1)
  M-1  outline one rectangle from (0, 0), 46 mm wide, <= 56 mm long (D-R11-02); every Edge.Cuts circle 3.2 mm
  M-3  four or five M3 supports, one within 6 mm of each corner (positions pinned by R11_DATA 'supports' when given)
  M-5  fit_check --profile r11 clean and bound to this board
  M-6  bottom parts SMD only, >= 1.5 mm from foreign through-hole pads, >= 3.5 mm from an M3 support (check_r10.m6)
  M-7  U4 side, rotation and lever arm as R11_DATA 'imu' records; no via or fill under U4 / U5 on their side
  M-8  courtyards >= 2.5 mm from the rail-less short edges (y = 0 and the outline's far edge; check_r10.m8 with R11_DATA
       'short_edge_queries', empty by default)
  K-legends  check_r10's legend rules with the R11 revision text pinned (PINNED_TEXTS_R11)
  K-copper   vias in pads, overlap-only joints, thermal policy, via paste (check_r9.k_copper, no GAP-3 exemption on
             R11 unless R11_DATA adds one), no pour debris (check_r10.pour_debris)
  K-inner    In1 and In4 GND only; In2 power and GND only; In3 signal routing (no rule on its nets)
  K-reference critical signal samples: F.Cu over In1 GND, B.Cu over In4 GND, In3 over In4 GND (D-R11-03); own
             antipads and S-8 voids excepted; no stale critical_reference name
  K-region   every In3 run of a return-required critical net lies over exactly one In2 plane net and over In2 copper;
             each connected In3 chain sees one In2 plane net (R10's B.Cu-over-In2 rule moved to In3: In3 sits 0.1 mm
             under In2 and 0.535 mm over In4 in the LEVIA-H7 stack, r11_plan section 2, so In2's rail regions are its
             nearer plane; F.Cu and B.Cu see only the solid GND of In1 / In4). Any In2 fill counts as a plane: K-inner
             keeps In2 to power and GND
  K-plane    inner power fills (In2, In3) one piece, else >= 2 links of >= 0.5 mm; necks reported (check_r10)
  K-fill     saved fills are current (check_r10.fill_freshness)
  K-rules    .kicad_pro floors, JLC hole table in the DRU, PTH hole to inner copper and JLC board holes (check_r10.k_rules;
             the DRU itself is held to its generator by r11_sch_check, so it is not SHA-pinned here)
  K-lands    the project library is the only footprint source; placed paste / mask settings equal the library
  K-width    BAT_IN / RAW_PROTECTED width floor (check_r10.k_width)
  K-power    rail paths at their IPC-2152 width and via counts (R10's POWER_PATHS without its coordinate bridges or
             per-layer restrictions), Q124's fire return, single-via-open taps (exceptions from R11_DATA, empty)
  K-ports    port ESD clamps on the wire side, <= 4.5 mm of track from the pin (J9's UART pins 5 / 6 on R11)
  K-loader   ROM-loader pins (check_r10.loader_pins with U1's balls from the R11 pin table)

Dropped from check_r10, each for one reason:
  M-2 (optional plate) not a gate. P-11 DB125 wire room: R11 has no screw terminals (fit_check r11 holds the GH plug and
  wire-pad envelopes). F9-1 / F9-2 the hot-plug model and U9's local loops are bound to R10's extracted copper; R11
  re-runs them on its own copper (r11_plan section 1) and adds the rule then. T-1 panel tabs: R10's tab windows are
  coordinates of a 90 mm board. K-contract: r11_sch_check carries R10's net contract onto the balls (stage A gate).
  K-binding: R10's binding note; R11's is a stage E record. K-actuators: check_actuators pins R10's file text.
  K-retained: R10 coordinate proximity of C29 / TP122 / C460 / C461. K-plane's tab bands (R10 coordinates).
"""
import argparse
import csv
from contextlib import ExitStack
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'quality_audit'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r10 as r10                                          # noqa: E402
from check_r10 import patched                                    # noqa: E402

REVISION = 'M3-ASSY-R11'
R11_DIR = ROOT / 'm3_design/r11'
R11_PIN_TABLE = R11_DIR / 'design/pin_table.tsv'
R11_DATA = R11_DIR / 'design/r11_gate_data.json'
BOARD_WIDTH, BOARD_MAX = 46.0, 56.0                              # D-R11-02
INNER = ('In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu')
GND_PLANES = ('In1.Cu', 'In4.Cu')                                # D-R11-03
POWER_LAYER = 'In2.Cu'
SIGNAL_INNER = 'In3.Cu'
PINNED_TEXTS_R11 = (('B.Silkscreen', REVISION),)
GH_PART = re.compile(r'^SM(\d\d)B-GHS-TB')
WIRE_PADS = {'J1': {'1': 'BAT_IN', '2': 'GND'}, 'J121': {'1': 'PYRO1_OUT', '2': 'PYRO1_IGN'}}
GH_PORTS = {
    'J410': {'1': 'PORT_4V8', '2': 'GND', '3': 'GPS_TX_WIRE', '4': 'GPS_RX_WIRE'},
    'J420': {'1': 'PORT_4V8', '2': 'GND', '3': 'RADIO_TX_WIRE', '4': 'RADIO_RX_WIRE'},
    'J440': {'1': 'PORT_4V8', '2': 'GND', '3': 'AUX_TX_WIRE', '4': 'AUX_RX_WIRE'},
    'J9': {'1': 'CAM_5V', '2': 'CAM_5V', '3': 'GND', '4': 'GND', '5': 'CAM_RX_WIRE', '6': 'CAM_TX_WIRE'},
    'J400': {'1': 'BAT_SW_SOURCE', '2': 'BAT_SW_RETURN'},
    'J122': {str(i): n for i, n in enumerate(r10.SERVO_TERMINAL, 1)},
}
# R10's clamps keyed by terminal pin; J9's UART moves from pins 3 / 4 to 5 / 6 (D-R11-05: RXI pin 5, TXO pin 6)
PORT_CLAMPS_R11 = tuple((ref, {'3': '5', '4': '6'}[pin] if ref == 'J9' else pin, clamp, res)
                        for ref, pin, clamp, res in r10.PORT_CLAMPS)
# R10's power paths with their R10 drawing details removed: named bridge coordinates and the J440 feed's F.Cu-only
# restriction were measured on the R10 copper. Floors, design currents, terminals and minimum via counts stay.
POWER_PATHS_R11 = tuple(dict({k: v for k, v in p.items() if k != 'layers'},
                             vias={k: v for k, v in p['vias'].items() if k != 'bridges'}) for p in r10.POWER_PATHS)


def load_data(path=None):
    """R11_DATA: what the later stages record (imu, supports, fire_narrow, power_narrow, single_open_exceptions,
    short_edge_queries). Missing file: {} (each rule says what it then needs)."""
    path = R11_DATA if path is None else Path(path)
    if not path.is_file():
        return {}
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f'{path}: gate data must be a JSON object')
    return data


def pin_table(path=None):
    """{port: ball} from the R11 pin table (columns 'port' and 'ball', else 'pin')."""
    path = R11_PIN_TABLE if path is None else Path(path)
    if not path.is_file():
        raise ValueError(f'R11 pin table {path} not found (stage A writes it)')
    with path.open() as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    col = 'ball' if rows and 'ball' in rows[0] else 'pin'
    return {r['port']: r[col] for r in rows if r.get('port') and r.get(col)}


def balls(ctx):
    if getattr(ctx, '_balls', None) is None:
        ctx._balls = ctx.port_pin if getattr(ctx, 'port_pin', None) is not None else pin_table()
    return ctx._balls


def lid(board, name):
    return board.GetLayerID(name)


# ======================================================================================================================
# rules
# ======================================================================================================================
def s1(ctx):
    b = balls(ctx)
    with patched(r10, DIRECT_ADC={'PYRO1_CONT': b['PC0'], 'ARM1_SENSE': b['PC5']}):
        return r10.s1(ctx)


def s3(ctx):
    """check_r10.s3 with PC1's ball in place of the LQFP pin U1.16."""
    issues, ev = r10.s3(ctx)
    issues = [i for i in issues if 'U1.16' not in i]
    ball = balls(ctx)['PC1']
    u1 = ctx.fps.get('U1')
    pad = u1.FindPadByNumber(ball) if u1 else None
    if pad is None or pad.GetNetname() != 'ACT_EN_MCU':
        issues.append(f'S-3: independent load-switch enable U1.{ball} (PC1) must be ACT_EN_MCU '
                      f'(is {pad.GetNetname() if pad else None})')
    ev.get('load_enable', {}).pop('U1.16', None)
    return sorted(set(issues)), ev


def connector_pads(ctx, ref, want, rid, tabs=True):
    """(issues, evidence): `ref`'s numbered pads are exactly `want` (number -> net); every other pad is a fixing tab
    (non-numeric number) on GND or no net, at most two."""
    f = ctx.fps.get(ref)
    if f is None:
        return [f'{rid}: {ref} missing'], {}
    issues, got, extra = [], {}, []
    for p in f.Pads():
        n = p.GetNumber()
        if n.isdigit():
            if n in got:
                issues.append(f'{rid}: {ref} has two pads numbered {n}')
            got[n] = p.GetNetname()
        else:
            extra.append((n, p.GetNetname()))
    if got != want:
        issues.append(f'{rid}: {ref} contacts {dict(sorted(got.items()))}; required {want}')
    if tabs:
        if len(extra) > 2:
            issues.append(f'{rid}: {ref} has {len(extra)} unnumbered pads; a GH header has two fixing tabs')
        for n, net in extra:
            if net not in ('', 'GND'):
                issues.append(f'{rid}: {ref} fixing tab {n or "(unnumbered)"} is on {net}; GND or no net only')
    elif extra:
        issues.append(f'{rid}: {ref} has unnumbered pads {[n for n, _ in extra]}')
    return issues, dict(contacts=got, tabs=extra)


def s7(ctx):
    return connector_pads(ctx, 'J122', GH_PORTS['J122'], 'S-7')


def w1(ctx):
    import pcbnew
    issues, ev = [], {}
    for ref, want in WIRE_PADS.items():
        found, ev[ref] = connector_pads(ctx, ref, want, 'W-1', tabs=False)
        issues += found
        f = ctx.fps.get(ref)
        for p in (f.Pads() if f else ()):
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
                issues.append(f'W-1: {ref}.{p.GetNumber()} must be a plated wire pad (PTH), D-R11-05')
    return issues, ev


def w2(ctx):
    issues, ev = [], {}
    for ref, want in GH_PORTS.items():
        if ref == 'J122':
            continue
        found, ev[ref] = connector_pads(ctx, ref, want, 'W-2')
        issues += found
    for ref in GH_PORTS:
        f = ctx.fps.get(ref)
        part = f.GetFieldText('Manufacturer Part') if f is not None and f.HasField('Manufacturer Part') else ''
        m = GH_PART.match(part or '')
        if f is not None and (m is None or int(m.group(1)) != len(GH_PORTS[ref])):
            issues.append(f'W-2: {ref} Manufacturer Part {part!r} is not the {len(GH_PORTS[ref])}-circuit side-entry '
                          f'JST GH header SM{len(GH_PORTS[ref]):02d}B-GHS-TB (D-R11-05)')
    return issues, ev


def barrel_rings(board, nets=r10.BARREL_NETS, layers=INNER):
    """[(label, net, layer, SHAPE)] of the inner ring each plated barrel of `nets` keeps on In1..In4."""
    import pcbnew
    out = []
    items = [(f'via ({pcbnew.ToMM(t.GetPosition().x):.3f}, {pcbnew.ToMM(t.GetPosition().y):.3f})', t)
             for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() in nets]
    items += [(f'{f.GetReference()}.{p.GetNumber()}', p) for f in board.GetFootprints() for p in f.Pads()
              if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname() in nets]
    for label, item in items:
        for name in layers:
            lay = board.GetLayerID(name)
            if item.IsOnLayer(lay) and item.FlashLayer(lay):
                out.append((f'{label} inner ring', item.GetNetname(), lay, item.GetEffectiveShape(lay)))
    return out


def s8(ctx, gap=r10.BARREL_GAP, gnd_hazard=r10.BARREL_GND_HAZARD, layers=INNER):
    """check_r10.s8 over every inner layer of the six-layer stack (D-R11-08)."""
    import pcbnew
    import check_r8 as r8
    inner = {ctx.board.GetLayerID(n) for n in layers}
    inner &= set(ctx.board.GetEnabledLayers().CuStack())
    barrels = [(label, net, shape, None) for label, net, shape in r10.barrel_shapes(ctx.board)]
    barrels += [(label, net, shape, lay) for label, net, lay, shape in barrel_rings(ctx.board, layers=layers)
                if lay in inner]
    others = [(label, net, lay, shape) for _, lay, shape, _, pad, net, label in r10.copper_nodes(ctx.board)
              if lay in inner]
    worst = {}
    for blabel, bnet, bshape, blay in barrels:
        for label, net, lay, shape in others:
            if net == bnet or (net == 'GND' and bnet not in gnd_hazard) or (blay is not None and lay != blay) \
                    or not pcbnew.SHAPE.Collide(bshape, shape, pcbnew.FromMM(gap) - 1):
                continue
            g = r8.min_gap(bshape, shape, gap + 1)
            g = 0.0 if g is None else g
            key = (blabel, net, ctx.board.GetLayerName(lay))
            if key not in worst or g < worst[key]:
                worst[key] = g
    issues = [f'S-8: {net} copper on {lay} is {g:.3f} mm from the {blabel} '
              f'{"" if blabel.endswith("inner ring") else "barrel "}of {next(b[1] for b in barrels if b[0] == blabel)}'
              f' (minimum {gap} mm)' for (blabel, net, lay), g in sorted(worst.items())]
    return issues, dict(inner_layers=sorted(ctx.board.GetLayerName(x) for x in inner),
                        barrels=sum(1 for b in barrels if b[3] is None),
                        inner_rings=sum(1 for b in barrels if b[3] is not None), gap_mm=gap,
                        near={f'{k[0]} / {k[1]} / {k[2]}': round(v, 3) for k, v in sorted(worst.items())})


def s9(ctx):
    narrow = [(e[0], e[1], e[2], e[3], tuple(e[4]), e[5]) for e in ctx.data.get('fire_narrow', [])]
    return r10.s9(ctx, narrow=narrow)


def m1(ctx):
    with patched(r10, BOARD_WIDTH=BOARD_WIDTH, BOARD_MAX=BOARD_MAX):
        issues, ev = r10.m1(ctx)
    return [i.replace('the P1 ', 'the D-R11-02 ') for i in issues], ev


def m3(ctx):
    import pcbnew
    mm = pcbnew.ToMM
    holes = [(mm(d.GetCenter().x), mm(d.GetCenter().y)) for d in ctx.board.GetDrawings()
             if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE]
    pinned = ctx.data.get('supports')
    if pinned:
        return r10.m3(ctx, supports=tuple(tuple(p) for p in pinned))
    import fit_check as fc
    _, _, issues = fc.corner_supports(holes, ctx.outline, [])
    return [f'M-3: {i}' for i in issues], dict(centres_mm=sorted((round(x, 4), round(y, 4)) for x, y in holes),
                                               pinned=False)


def m5(ctx, board_sha=None):
    rep = ctx.fit()
    issues = [f'M-5: fit_check: {i}' for i in rep.get('issues', [])]
    if rep.get('profile') != 'r11':
        issues.append(f'M-5: fit report profile {rep.get("profile")!r}; R11 needs fit_check --profile r11')
    if ctx.fit_given and board_sha and rep.get('board_sha256') != board_sha:
        issues.append('M-5: the fit report is not bound to this board (board_sha256)')
    return issues, dict(width_mm=rep.get('width_mm'), length_mm=rep.get('length_mm'), supports=rep.get('supports'),
                        gh_ports=rep.get('gh_ports'))


def m7(ctx):
    import check_r9 as r9
    imu = ctx.data.get('imu')
    if not isinstance(imu, dict) or not {'rotation', 'lever_mm'} <= imu.keys():
        return ['M-7: R11_DATA has no imu record (rotation, lever_mm[, tol_mm]); stage B records U4\'s pose and axis '
                'map with its decision'], {}
    rev = ctx.board.GetTitleBlock().GetRevision()
    with patched(r9, IMU_ROTATION={**r9.IMU_ROTATION, rev: float(imu['rotation'])}, IMU_LEVER=math.inf):
        issues, ev = r9.m7(ctx)
    u4 = ctx.fps.get('U4')
    if u4 is not None:
        lever = r10.pcbnew_mm(u4.GetPosition().x) - 23.0
        ev['imu_lever_arm_signed_mm'] = round(lever, 3)
        tol = float(imu.get('tol_mm', 0.05))
        if abs(lever - float(imu['lever_mm'])) > tol:
            issues.append(f'M-7: U4 centre x offset from the roll axis (x 23) is {lever:.3f} mm, recorded '
                          f'{imu["lever_mm"]} +/- {tol} mm (R11_DATA imu)')
    return issues, ev


def m8(ctx):
    return r10.m8(ctx, queries={k: tuple(v) for k, v in ctx.data.get('short_edge_queries', {}).items()})


def k_legends(ctx):
    with patched(r10, PINNED_TEXTS=PINNED_TEXTS_R11):
        return r10.k_legends(ctx)


def k_copper(ctx):
    import check_r9 as r9
    issues, ev = r9.k_copper(ctx)
    debris, debris_ev = r10.pour_debris(ctx.board)
    return issues + [f'K-copper: {i}' for i in debris], dict(ev, pour_pieces=debris_ev)


def k_inner(ctx):
    """In1 / In4 GND only; In2 power and GND only (route_check's r10 classes, which r11 reads); In3 free."""
    import pcbnew
    import route_check as rc
    b = ctx.board
    gnd_only = {lid(b, n) for n in GND_PLANES}
    power = lid(b, POWER_LAYER)

    def bad(layer, net):
        return (layer in gnd_only and net != 'GND') or (layer == power and rc.net_class(net) != 'power')
    issues, length = [], {}
    routed = set()
    for t in b.GetTracks():
        routed.add(t.m_Uuid.AsString())
        if t.GetClass() == 'PCB_VIA' or not bad(t.GetLayer(), t.GetNetname()):
            continue
        name = b.GetLayerName(t.GetLayer())
        length[name] = length.get(name, 0.) + pcbnew.ToMM(t.GetLength())
        issues.append(f'{name} track of {t.GetNetname()}: In1 / In4 carry GND only; In2 power and GND only')
    for key, layer, shape, box, pad, net, label in r10.copper_nodes(b):
        if pad is None and key not in routed and bad(layer, net):
            issues.append(f'{b.GetLayerName(layer)} {label} of {net or "(no net)"}: In1 / In4 carry GND only; '
                          'In2 power and GND only')
    return [f'K-inner: {i}' for i in issues], dict(length_mm=length)


def reference_map(board):
    """{signal layer id: (reference layer id, plane nets)} of the R11 stack (D-R11-03); In3's In2 side is K-region's."""
    return {lid(board, 'F.Cu'): (lid(board, 'In1.Cu'), ('GND',)),
            lid(board, 'B.Cu'): (lid(board, 'In4.Cu'), ('GND',)),
            lid(board, SIGNAL_INNER): (lid(board, 'In4.Cu'), ('GND',))}


def k_reference(ctx):
    import critical_reference as cr
    import pcbnew
    b = ctx.board
    refs = reference_map(b)
    nets = {n for n in set(cr.R6_NETS + cr.EXTENDED_R10 + cr.R10_PORT_NETS + cr.R10_SD_NETS) | r10.signal_critical_nets(b)
            if not cr.r10_slow_return_net(n)}
    samples = cr.samples(b, nets, refs)
    fill = cr.fills(b, refs)
    empty = pcbnew.SHAPE_POLY_SET()
    missing = [s for s in samples if not cr.inside(fill.get(s[1], empty), s[2], s[3])]
    own, voids = r10.own_antipads(b), r10.own_barrel_voids(b)
    loose = [(s[0], b.GetLayerName(s[1]), s[2], s[3]) for s in missing
             if not r10.in_own_antipad(own, s[0], s[2], s[3]) and not r10.in_own_antipad(voids, s[0], s[2], s[3])]
    issues = []
    if loose:
        issues.append(f'{len(loose)} critical signal samples lack adjacent reference copper outside their own via '
                      f'antipads (F over In1 GND, B over In4 GND, In3 over In4 GND), e.g. {loose[:3]}')
    stale = cr.r10_stale_names({str(n) for n in b.GetNetsByName().keys()})
    issues += [f'stale critical_reference.{lst} entry {name!r}: no such net on the board' for lst, name in stale]
    return [f'K-reference: {i}' for i in issues], dict(samples=len(samples), unreferenced=len(missing),
                                                       loose=len(loose))


def region_issues(board, track_layer=SIGNAL_INNER, plane_layer=POWER_LAYER):
    """check_r10.region_issues with the signal layer In3 and the plane layer In2 (R10: B.Cu over In2): every run and
    SMD pad of a return-required critical net on `track_layer` lies over exactly one `plane_layer` plane net and over
    its copper (own via antipads, own pad voids, S-8 voids and other nets' via clearance holes excepted); each connected
    chain sees one plane net."""
    import pcbnew
    tl, pl = board.GetLayerID(track_layer), board.GetLayerID(plane_layer)
    import types
    proxy = types.ModuleType('pcbnew')                 # pcbnew with B_Cu / In2_Cu re-pointed, for that one call
    proxy.__dict__.update({k: v for k, v in pcbnew.__dict__.items() if not k.startswith('__')})
    proxy.B_Cu, proxy.In2_Cu = tl, pl
    saved = sys.modules['pcbnew']
    sys.modules['pcbnew'] = proxy
    try:
        issues, ev = r10.region_issues(board)
    finally:
        sys.modules['pcbnew'] = saved
    issues = [i.replace('B.Cu', track_layer).replace('In2', plane_layer.split('.')[0]) for i in issues]
    return issues, dict(ev, track_layer=track_layer, plane_layer=plane_layer)


def k_region(ctx):
    issues, ev = region_issues(ctx.board)
    return [f'K-region: {i}' for i in issues], ev


PLANE_LAYERS_R11 = ('In2.Cu', 'In3.Cu')


def k_plane(ctx):
    issues, ev = [], {}
    for (net, layer), pieces in sorted(r10.plane_pieces(ctx.board, layers=PLANE_LAYERS_R11).items()):
        areas = [round(p.Area() / 1e12, 2) for p in pieces]
        ev[f'{net} {layer}'] = areas
        if len(pieces) < 2:
            continue
        main = max(range(len(pieces)), key=lambda i: areas[i])
        count = r10.plane_links(ctx.board, net, pieces)
        for i, area in enumerate(areas):
            if i != main and count[i] < r10.PLANE_LINKS:
                bb = pieces[i].BBox()
                issues.append(f'K-plane: {net} on {layer} fills as {len(pieces)} pieces; the {area} mm^2 piece at '
                              f'({r10.pcbnew_mm(bb.GetCenter().x):.2f}, {r10.pcbnew_mm(bb.GetCenter().y):.2f}) has '
                              f'{count[i]} link(s) of >= {r10.PLANE_LINK_W} mm outer copper (minimum {r10.PLANE_LINKS})')
    necks, neck_ev = r10.plane_necks(ctx.board, layers=PLANE_LAYERS_R11)
    return issues + necks, dict(pieces_mm2=ev, necks=neck_ev)


def k_rules(ctx):
    dru = None
    if ctx.board_path and Path(ctx.board_path).with_suffix('.kicad_dru').is_file():
        dru = Path(ctx.board_path).with_suffix('.kicad_dru').read_bytes().decode('utf-8')
    pin = hashlib.sha256(dru.encode('utf-8')).hexdigest() if dru is not None else r10.DRU_SHA256
    with patched(r10, DRU_SHA256=ctx.data.get('dru_sha256', pin)):
        issues, ev = r10.k_rules(ctx)
    ev['dru_pin'] = 'R11_DATA dru_sha256' if 'dru_sha256' in ctx.data else 'r11_sch_check (generator replay)'
    return issues, ev


def k_lands(ctx):
    folder = Path(ctx.board_path).parent if ctx.board_path else ctx.folder
    if folder is None:
        return ['K-lands: the project folder is unknown (no board path)'], {}
    from sexpr import read
    issues, used = [], set()
    libs = folder / 'fp-lib-table'
    found = [(lib.children('name')[0].items[1].atom, lib.children('uri')[0].items[1].atom)
             for lib in read(libs.read_text()).children('lib')] if libs.is_file() else None
    if found != r10.FP_LIB_TABLE:
        issues.append(f'K-lands: fp-lib-table lists {found}; R11 uses only {r10.FP_LIB_TABLE}')
    for f in ctx.board.GetFootprints():
        lib, name = f.GetFPID().GetLibNickname().wx_str(), f.GetFPID().GetLibItemName().wx_str()
        if lib != r10.FP_LIB_TABLE[0][0]:
            issues.append(f'K-lands: {f.GetReference()} uses {lib}:{name}, not the project library')
        used.add(name)
    pins = ctx.data.get('footprint_sha256', {})
    for name, want in sorted(pins.items()):
        path = folder / 'kilib/rocket.pretty' / f'{name}.kicad_mod'
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if name not in used:
            issues.append(f'K-lands: stale footprint_sha256 entry {name}')
        elif actual != want:
            issues.append(f'K-lands: {name} library file SHA-256 {actual} is not the pinned {want}')
    overrides, compared = r10.land_overrides(ctx.board, folder / 'kilib/rocket.pretty')
    issues += [f'K-lands: {i} (a stencil / mask change goes in the reviewed library land)' for i in overrides]
    if 'paste_totals' in ctx.data:
        pastes, _ = r10.paste_totals(ctx.board, ctx.data['paste_totals'])
        issues += [f'K-lands: {i}' for i in pastes]
    return issues, dict(footprints_used=len(used), pads_compared_for_paste_mask=compared, pinned=len(pins))


def k_power(ctx):
    narrow = [(e[0], e[1], e[2], e[3], tuple(e[4]), e[5]) for e in ctx.data.get('power_narrow', [])]
    exceptions = [tuple(e) for e in ctx.data.get('single_open_exceptions', [])]
    issues, ev = r10.power_paths(ctx.board, paths=POWER_PATHS_R11, narrow=narrow)
    found, ev['fire_return'] = r10.fire_return(ctx.board)
    taps, ev['single_via_open_taps'] = r10.single_via_opens(ctx.board, exceptions=exceptions)
    return [f'K-power: {i}' for i in issues + found + taps], ev


def k_ports(ctx):
    issues, ev = r10.port_clamps(ctx.board, clamps=PORT_CLAMPS_R11)
    returns, gnd = r10.clamp_returns(ctx.board, clamps=PORT_CLAMPS_R11)
    return ([f'K-ports: {i}' for i in issues + returns],
            dict(clamp_path_mm=ev, bound_mm=r10.CLAMP_PATH_MAX, clamp_gnd_mm=gnd))


def k_loader(ctx):
    issues, ev = r10.loader_pins(ctx.board, port_pin=balls(ctx))
    return [f'K-loader: {i}' for i in issues], ev


RULES = [
    ('S-1', 'RAW_ACT pyro bus, named armed-side parts', lambda c, s: s1(c)),
    ('S-2', 'pyro feed only through the load switch', lambda c, s: r10.s2(c)),
    ('S-3', 'gate networks defined off', lambda c, s: s3(c)),
    ('S-4', 'required-fitted parts, MPN-decoded values', lambda c, s: r10.s4(c)),
    ('S-5', 'J400 arming switch and protected EN contacts', lambda c, s: r10.s5(c)),
    ('S-6', 'external ports apart from pyro / arming copper', lambda c, s: r10.s6(c)),
    ('S-7', 'J122 GH: SERVO1-4 and GND, two fixing tabs', lambda c, s: s7(c)),
    ('S-8', 'In1..In4 copper >= 1.0 mm from pyro, load-switch gate and enable barrels', lambda c, s: s8(c)),
    ('S-9', 'fire / source copper widths', lambda c, s: s9(c)),
    ('W-1', 'J1 / J121 plated wire pads (D-R11-05)', lambda c, s: w1(c)),
    ('W-2', 'GH port pin-outs and parts (D-R11-05)', lambda c, s: w2(c)),
    ('LC-1', 'local overrides respect the applicable floors', lambda c, s: r10.lc1(c.board)),
    ('M-1', 'outline 46 mm wide, <= 56 mm long', lambda c, s: m1(c)),
    ('M-3', 'four or five M3 supports, one at each corner', lambda c, s: m3(c)),
    ('M-5', 'fit (profile r11)', lambda c, s: m5(c, s)),
    ('M-6', 'bottom keep-outs', lambda c, s: r10.m6(c)),
    ('M-7', 'IMU pose (R11_DATA) and MEMS keep-outs', lambda c, s: m7(c)),
    ('M-8', 'courtyards >= 2.5 mm from the short edges', lambda c, s: m8(c)),
    ('K-legends', 'legends, ids, silkscreen allowlist, designators and Fab references', lambda c, s: k_legends(c)),
    ('K-copper', 'copper hygiene, no pour debris', lambda c, s: k_copper(c)),
    ('K-inner', 'In1 / In4 GND only, In2 power and GND only', lambda c, s: k_inner(c)),
    ('K-reference', 'critical signal reference copper on the six-layer stack', lambda c, s: k_reference(c)),
    ('K-region', 'critical In3 runs over one In2 plane region', lambda c, s: k_region(c)),
    ('K-plane', 'inner power fills one piece, else >= 2 links', lambda c, s: k_plane(c)),
    ('K-fill', 'saved zone fills are current', lambda c, s: r10.k_fill(c)),
    ('K-rules', 'project rule floors, JLC hole table, PTH to inner copper, board holes', lambda c, s: k_rules(c)),
    ('K-lands', 'project library only, placed paste / mask as the library', lambda c, s: k_lands(c)),
    ('K-width', 'BAT_IN / RAW_PROTECTED width floor', lambda c, s: r10.k_width(c.board)),
    ('K-power', 'rail paths, fire return, single-via-open taps', lambda c, s: k_power(c)),
    ('K-ports', 'port ESD clamps on the wire side', lambda c, s: k_ports(c)),
    ('K-loader', 'ROM-loader pins on U1\'s balls', lambda c, s: k_loader(c)),
]
STAGES = {'functional': {'S-1', 'S-2', 'S-3', 'S-4', 'S-5', 'S-6', 'S-7', 'W-1', 'W-2', 'K-loader'}}
STAGES['placement'] = STAGES['functional'] | {'LC-1', 'M-1', 'M-3', 'M-5', 'M-6', 'M-7', 'M-8', 'K-lands'}
STAGES['full'] = {rid for rid, _, _ in RULES}


def selected_rules(only=None, stage='full'):
    if only is None:
        if stage not in STAGES:
            raise ValueError(f'unknown rule stage: {stage!r}')
        return STAGES[stage]
    selected = set(only)
    if not selected or not any(selected):
        raise ValueError('explicit rule selection is empty')
    unknown = selected - STAGES['full']
    if unknown:
        raise ValueError(f'unknown rule ids: {", ".join(repr(r) for r in sorted(unknown))}')
    return selected


def make_ctx(board, folder=None, board_path=None, fit=None, text=None, bom=None, cpl=None, data=None, port_pin=None):
    import check_r9 as r9
    import fit_check as fc

    class R11Ctx(r9.Ctx):
        def fit(self):
            if self.fit_report is None:
                self.fit_report = fc.check_board(self.board, self.folder or Path('.'), profile='r11')
            return self.fit_report
    ctx = R11Ctx(board, folder, board_path, fit, None, None, 0.0, None)
    if text is None and board_path and Path(board_path).is_file():
        text = Path(board_path).read_text()
    ctx.text, ctx.bom, ctx.cpl, ctx.fit_given, ctx._reach = text, bom, cpl, fit is not None, None
    ctx.data = load_data() if data is None else data
    ctx.port_pin, ctx._balls = port_pin, None
    return ctx


def check_board(board, folder=None, board_path=None, fit=None, only=None, stage='full', board_sha=None, text=None,
                bom=None, cpl=None, data=None, port_pin=None):
    """Run the rules of `stage` (or `only`); each rule that cannot run fails. route_check runs as profile r11."""
    selected = selected_rules(only, stage)
    import route_check as rc
    ctx = make_ctx(board, folder, board_path, fit, text, bom, cpl, data, port_pin)
    previous = rc.PROFILE
    out, flat = {}, []
    with ExitStack() as stack:
        rc.set_profile('r11')
        stack.callback(rc.set_profile, previous)
        for rid, title, fn in RULES:
            if rid not in selected:
                continue
            try:
                issues, ev = fn(ctx, board_sha)
            except Exception as e:                       # a rule that cannot run fails, it never passes
                issues, ev = [f'{rid}: could not run: {type(e).__name__}: {e}'], {}
            out[rid] = dict(title=title, ok=not issues, issues=issues, evidence=ev)
            flat += [i if i.startswith(rid) else f'{rid}: {i}' for i in issues]
    return dict(profile='r11', stage=stage, complete=stage == 'full' and only is None, ok=not flat, rules=out,
                issues=flat, failing=[k for k, v in out.items() if not v['ok']])


def file_sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board', nargs='?', type=Path, default=R11_DIR / 'm3.kicad_pcb')
    ap.add_argument('--report', type=Path)
    ap.add_argument('--fit', type=Path, help='tools/fit_check.py --profile r11 --report of this board')
    ap.add_argument('--only', help='comma-separated rule ids')
    ap.add_argument('--stage', choices=tuple(STAGES), default='full')
    ap.add_argument('--bom', type=Path)
    ap.add_argument('--cpl', type=Path)
    a = ap.parse_args()
    only = {rid.strip() for rid in a.only.split(',')} if a.only is not None else None
    try:
        selected_rules(only, a.stage)
    except ValueError as error:
        ap.error(str(error))
    import pcbnew
    import fit_check as fc
    bp = a.board.resolve()

    def inputs():
        r = fc.input_hashes(bp)
        for p in (bp.with_suffix('.kicad_dru'), bp.with_suffix('.kicad_pro'), bp.with_suffix('.kicad_sch'),
                  R11_PIN_TABLE, R11_DATA):
            r[p.name] = file_sha(p)
        return r
    before = inputs()
    sha = before[bp.name]
    fit = json.loads(a.fit.read_text()) if a.fit else None
    if fit is not None and fit.get('board_sha256') != sha:
        print('FAIL the fit report is not bound to this board (board_sha256)')
        return 1
    board = pcbnew.LoadBoard(str(bp))
    if board.GetTitleBlock().GetRevision() != REVISION:
        print(f'FAIL title-block revision {board.GetTitleBlock().GetRevision()!r}; check_r11 checks {REVISION}')
        return 1
    report = check_board(board, bp.parent, bp, fit=fit, only=only, stage=a.stage, board_sha=sha, bom=a.bom, cpl=a.cpl)
    if before != inputs():
        report['issues'].append('board, rules, schematic, pin table or gate data changed during check')
        report['ok'] = False
    report.update(board_sha256=sha, inputs_sha256=before, checker_sha256=file_sha(__file__))
    for rid, r in report['rules'].items():
        print(f"{rid:12s} {'OK  ' if r['ok'] else 'FAIL'} {r['title']}" + (f" ({len(r['issues'])})" if r['issues'] else ''))
    for i in report['issues']:
        print('FAIL', i)
    scope = a.stage if only is None else 'selected rules'
    print(f'R11 CAD contract ({scope}):', 'OK' if report['ok'] else f"FAIL ({len(report['issues'])} findings in "
          f"{len(report['failing'])} rules: {', '.join(report['failing'])})")
    if a.report:
        a.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
