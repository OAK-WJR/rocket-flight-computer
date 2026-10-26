#!/usr/bin/env python3
"""R9 step 10: the requalification measurements a clean-sheet geometry invalidates, on one board, bound to its SHA-256.

usage: <KiCad python3> -I requalify_r9.py BOARD.kicad_pcb OUT.json [--seed SEED.json] [--fit FIT.json]
       BOARD needs its project files (.kicad_pro / .kicad_dru) beside it; SEED / FIT are tools/check.sh's rule_h_seed and
       fit_check reports of the same board (checked by SHA; the seeded suite is re-run here when SEED is missing).

Read-only. Every figure is measured by the gate's own code where the gate has it (tools/check_r9.py, pyro_probe.py,
bridge_table.py, m3_design/r9_pyro_check.py and r9_rf_check.py functions), never restated; R8's step-9 measurements
(sources/r8_design/step9/requalify.py) are reused for what they measure geometry-free of R8 (bare pads, TP122, probes,
edges, the order mark, part counts, the RF separation tables, the IMU), with the R8-only constants replaced by the R9
board's own (PYRO_BLOCK from its rule area, U30's body from U30, the tie holes from J122's M-3 evidence, the tab
windows from tools/tab_windows.py). Sections of OUT.json (survey_constraints sections 8.4, 9.4 and 11):

  pyro.margins      rules A-H / A2 and the strict pad rules (pyro_probe), each margin against r9_plan's floor
                    max(R8, 0.2) (r9_pyro_check.gate_margins; the one recorded exception, D-S5-13)
  pyro.bridges      the R4 solder-bridge table (bridge_table): every exposed pair under 1.5 mm with its single-bridge
                    consequence and cold-test signature, tolerated or forbidden; fires-class pairs listed
  pyro.rule_h       the seeded rule-H suite (tools/rule_h_seed.py): pairs x variants, each caught
  pyro.reset        the gate reset-voltage table (check_r9 P-7) and PYRO1_GATE_N's neighbours (r9_pyro_check)
  pyro.divider      the divider-fault analysis' layout preconditions (survey 9.4 item 4): each divider half a separate
                    part, the 4.7 k at the MCU end and the *_MCU lengths (P-8), every sense lane's neighbours with the
                    pin current a hard short there could force through the 4.7 k (Calc), the MCU sides clean
  pyro.armed        foreign nets within 3 mm of armed-live copper (X2 / X2b)
  pyro.bare         coating and leakage distances: exposed gate copper (pyro and actuator switch) and J2's NRST pad to
                    the nearest exposed pad of each class on the same face (R8 requalify.bare)
  pyro.coat         the coat region (PYRO_BLOCK's area + J2) and its keep-offs (check_r9 P-10 / P-1)
  pyro.exits        GATE_N, CONT, ARM1_SENSE and their MCU sides: track length, layers, vias, nearest non-GND and
                    always-live copper; D19; the pyro vias and their GND partners (P-9); M-6
  pyro.block_vias   GND vias inside PYRO_BLOCK and their nearest pyro / arming / RAW_ACT copper
  pyro.tp122        TP122 (the gate test pad): face, place, vias in its pad (A8), the gate via's GND partner
  pyro.wire_room    the terminals' entries and wire room (check_r9 P-11, fit_check's bore-wall figures)
  pyro.fire_bars    the fire loop's board copper by the sheet-resistance estimate (r9_pyro_check.evidence; the
                    dc_solve figures are step10/run_dc_r9.sh's)
  rf.gcpw           every R-5 line sample's gap pair and its Z0 (tools/gcpw_solve.py), per chain
  rf.launch / r7    the launches and chains in each jack's frame against R7's (r9_rf_check)
  rf.return_loss    a lossless ABCD cascade of each chain as drawn (pass2_rf section 3.12's method; Inference)
  rf.contract       check_r9 R-1 ... R-13 evidence (stitching, fence, keep-outs, separations, coexistence, supply)
  rf.separations    R8 requalify.rf on the R9 board: RF parts to the restricted parts, modules to the bucks, radio
                    interface lines to U30's body and the GNSS RF copper, RF line to line, jacks, fast copper
  mech              plate model input (fit), holes and washers, edges, tab windows, the order mark, part counts
  imu               U4: face, rotation, pad 1, lever arm, axis map (check_r9 M-7)
  probes            every test pad (net, face, place) and NRST's probe
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'm3_design'))
import bridge_table as BT  # noqa: E402
import check_r8 as C8  # noqa: E402
import check_r9 as C9  # noqa: E402
import pyro_probe as PP  # noqa: E402
import r9_pyro_check as PC  # noqa: E402
import r9_rf_check as RC  # noqa: E402
import tab_windows as TW  # noqa: E402

_spec = importlib.util.spec_from_file_location('r8_requalify', HERE.parents[1] / 'r8_design/step9/requalify.py')
R8Q = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R8Q)
GS = RC.GS

mm, MM = pcbnew.ToMM, pcbnew.FromMM
C_LIGHT = 299792458.0
PIN_V = 3.3                        # MCU pin taken at the logic rail for the forced-current bound (Calc)
R_MCU = 4700.0                     # R168 / R170 / R172 (check_actuators pins the values)
PACK_MAX = 8.4                     # 2S maximum (REQUIREMENTS F9)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def r3(v):
    return None if v is None else round(v, 3)


# ---------------------------------------------------------------- pyro
def source_volts(net):
    """Open-circuit volts a hard short to `net` can bring (Calc; bridge_table's source classes)."""
    if net == 'GND' or not net or net.startswith('unconnected-'):
        return 0.0
    if net in BT.ARMED or net in BT.BATTERY or net in ('BAT_IN', 'ACT_FET_S', 'RAW_PROTECTED', 'RAW_ACT', 'VLOGIC',
                                                       'BAT_SW_SOURCE', 'BAT_SW_RETURN', 'BAT_ENABLE', 'BAT_DAMP'):
        return PACK_MAX
    if net in ('VBUS', 'CAM_5V', 'CAM_INPUT_LIMITED', 'USB_LIMITED'):
        return 5.0
    return 3.3                                       # logic rails and driven logic nets


def divider(board, ctx):
    """Survey 9.4 item 4: the layout preconditions of F8's divider-fault analysis."""
    fps = {f.GetReference(): f for f in board.GetFootprints()}

    def parts_on(net):
        return sorted({p.GetParentFootprint().GetReference() for f in fps.values() for p in f.Pads()
                       if p.GetNetname() == net})
    out = {}
    for node, mid, mcu in (('PYRO1_CONT', 'PYRO1_CONT_MID', 'PYRO1_CONT_MCU'),
                           ('ARM1_SENSE', 'ARM1_SENSE_MID', 'ARM1_SENSE_MCU'),
                           ('RAW_ACT_SENSE', 'RAW_ACT_SENSE_MID', 'RAW_ACT_SENSE_MCU')):
        mids = [r for r in parts_on(mid) if r.startswith('R')]
        node_r = [r for r in parts_on(node) if r.startswith('R')]
        gnd_half = [r for r in node_r if any(p.GetNetname() == 'GND' for p in fps[r].Pads())]
        mcu_r = [r for r in node_r if any(p.GetNetname() == mcu for p in fps[r].Pads())]
        top_lower = [r for r in mids if r in node_r]                  # mid -> node: the lower top half
        top_upper = [r for r in mids if r not in node_r]               # live -> mid: the upper top half
        vals = {r: fps[r].GetValue() for r in mids + gnd_half + mcu_r}
        out[node] = dict(top_upper=top_upper, top_lower=top_lower, bottom=gnd_half, mcu_series=mcu_r, values=vals,
                         separate_parts=len(top_upper) == 1 and len(top_lower) == 1 and len(gnd_half) == 2
                         and len(mcu_r) == 1)
    issues, sense = PC.gate_sense(board, ctx)
    forced = {}
    for key, (d, a, b_) in sense['neighbours'].items():
        lane, other = key.split(' / ')
        v = source_volts(other)
        if lane.endswith('_MCU'):
            i_ma = None                                # past the 4.7 k: the gate forbids any source above logic
        else:
            i_ma = round(1000 * max(0.0, v - PIN_V) / R_MCU, 3)
        forced[key] = dict(mm=d, lane_item=a, other_item=b_, source_v=v, pin_ma_via_4k7=i_ma)
    p8 = C9.p8(ctx)
    return dict(dividers=out, mcu_end=p8[1], neighbours=forced, mcu_side_issues=issues,
                note='pin_ma_via_4k7 = (V_source - 3.3 V) / 4.7 k: a hard short on the node side of the 4.7 k, MCU pin '
                     'taken at the 3.3 V rail (Calc; F8: about 1 mA for an 8.4 V source)')


def exits(board, byn):
    """R8 requalify.exits on every copper item of the exit nets (R9 has no rigid block copper to leave out)."""
    out = {}
    for net in R8Q.EXIT_NETS + ('RAW_ACT_SENSE_MCU',):
        own = [t for t in board.GetTracks() if t.GetNetname() == net]
        length = sum(mm(t.GetLength()) for t in own if t.GetClass() == 'PCB_TRACK')
        layers = sorted({t.GetLayerName() for t in own if t.GetClass() == 'PCB_TRACK'})
        vias = [(round(mm(t.GetPosition().x), 3), round(mm(t.GetPosition().y), 3)) for t in own if t.GetClass() == 'PCB_VIA']
        mine = [it for it in byn.get(net, []) if isinstance(it[4], (pcbnew.PCB_TRACK, pcbnew.PCB_VIA))]
        best = {'non_gnd': None, 'always_live': None}
        for other, items in byn.items():
            if other in (net, 'GND', ''):
                continue
            for b in items:
                for a in mine:
                    if a[2] != b[2] or not R8Q.near_boxes(a[3], b[3], 2.0):
                        continue
                    g = C8.min_gap(a[3], b[3], 2.0)
                    if g is None:
                        continue
                    row = (g, a[0], f'{b[0]} ({other})', board.GetLayerName(a[2]))
                    if best['non_gnd'] is None or g < best['non_gnd'][0]:
                        best['non_gnd'] = row
                    if other in R8Q.ALWAYS_LIVE and (best['always_live'] is None or g < best['always_live'][0]):
                        best['always_live'] = row
        out[net] = dict(track_mm=round(length, 2), layers=layers, vias=vias,
                        **{f'nearest_{k}': None if v is None else dict(mm=v[0], own=v[1], other=v[2], layer=v[3])
                           for k, v in best.items()})
    return out


def block_vias(board, byn):
    """GND vias inside the PYRO_BLOCK rule area (its outline, not a rectangle) and their nearest pyro copper."""
    area = [pcbnew.SHAPE_POLY_SET(z.Outline()) for z in board.Zones()
            if z.GetIsRuleArea() and z.GetZoneName() == 'PYRO_BLOCK'][0]
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND'
            and area.Contains(t.GetPosition())]
    nets = [n for n in byn if n in R8Q.LIVE + R8Q.GATES + R8Q.SENSE + ('RAW_ACT', 'PYRO1_CONT_MCU', 'ARM1_SENSE_MCU')]
    per, worst_by_class = {}, {}
    for v in vias:
        key = f'{round(mm(v.GetPosition().x), 3)},{round(mm(v.GetPosition().y), 3)}'
        best = None
        for lay in board.GetEnabledLayers().CuStack():
            if not v.IsOnLayer(lay) or not v.FlashLayer(lay):
                continue
            s = C8.item_shape(v, lay)
            for n in nets:
                for it in byn[n]:
                    if it[2] != lay or not R8Q.near_boxes(s, it[3], 2.0):
                        continue
                    g = C8.min_gap(s, it[3], 2.0)
                    if g is None:
                        continue
                    if best is None or g < best[0]:
                        best = (g, f'{it[0]} ({n})', board.GetLayerName(lay))
                    cls = 'armed' if n in R8Q.LIVE else 'other pyro / arming / RAW_ACT'
                    if cls not in worst_by_class or g < worst_by_class[cls][0]:
                        worst_by_class[cls] = (g, key, f'{it[0]} ({n})', board.GetLayerName(lay))
        per[key] = None if best is None else dict(mm=best[0], item=best[1], layer=best[2])
    return dict(count=len(vias), per_via=per,
                nearest={k: dict(mm=v[0], via=v[1], item=v[2], layer=v[3]) for k, v in worst_by_class.items()})


def tp122(board, byn):
    f = board.FindFootprintByReference('TP122')
    p = next(iter(f.Pads()))
    face = 'B' if f.IsFlipped() else 'F'
    cu = pcbnew.B_Cu if face == 'B' else pcbnew.F_Cu
    in_pad = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA'
              and p.GetEffectiveShape(cu).Collide(pcbnew.VECTOR2I(t.GetPosition()), MM(mm(t.GetDrillValue()) / 2))]
    gnd = [(mm(t.GetPosition().x), mm(t.GetPosition().y)) for t in board.GetTracks()
           if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    gate_vias = []
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA' and t.GetNetname() in ('PYRO1_GATE', 'PYRO1_GATE_N'):
            c = (mm(t.GetPosition().x), mm(t.GetPosition().y))
            ng = min(gnd, key=lambda g: math.dist(c, g))
            gate_vias.append(dict(net=t.GetNetname(), at=[round(c[0], 3), round(c[1], 3)],
                                  nearest_gnd_via=[round(ng[0], 3), round(ng[1], 3)],
                                  nearest_gnd_via_mm=round(math.dist(c, ng), 3)))
    return dict(pad=f'TP122.1 ({p.GetNetname()})', face=face,
                at=[round(mm(p.GetPosition().x), 3), round(mm(p.GetPosition().y), 3)],
                vias_in_pad=[f'{t.GetNetname()} ({mm(t.GetPosition().x):.3f}, {mm(t.GetPosition().y):.3f})'
                             for t in in_pad],
                gate_vias=gate_vias)


# ---------------------------------------------------------------- RF
def _abcd_mul(m, n):
    return [[m[0][0] * n[0][0] + m[0][1] * n[1][0], m[0][0] * n[0][1] + m[0][1] * n[1][1]],
            [m[1][0] * n[0][0] + m[1][1] * n[1][0], m[1][0] * n[0][1] + m[1][1] * n[1][1]]]


def _line(z, length_mm, f, eeff):
    bl = 2 * math.pi * f * math.sqrt(eeff) / C_LIGHT * length_mm * 1e-3
    return [[complex(math.cos(bl)), 1j * z * math.sin(bl)], [1j * math.sin(bl) / z, complex(math.cos(bl))]]


def _shunt(y):
    return [[1 + 0j, 0j], [y, 1 + 0j]]


def _series(z):
    return [[1 + 0j, z], [0j, 1 + 0j]]


def _open_stub_y(z, length_mm, f, eeff, c_end):
    """Input admittance of an open stub of `length_mm` ending in c_end (F)."""
    w = 2 * math.pi * f
    yl = 1j * w * c_end
    bl = 2 * math.pi * f * math.sqrt(eeff) / C_LIGHT * length_mm * 1e-3
    t = math.tan(bl)
    return (yl + 1j * t / z) / (1 + 1j * z * yl * t)


CASCADE = dict(z_launch_ref='In2 (gcpw_solve, W 1.2, gap 0.30, In1 cut out)', launch_mm=4.2, launch_tail_mm=0.2,
               z_tail=70.0, esd_pf=0.2, choke_ohm=500.0, series_nh=0.4, stub_end_pf=0.03, load_ohm=50.0,
               basis='pass2_rf section 3.12 (R7 pass 2): launch 49 ohm x 4.2 mm then 0.2 mm at about 70 ohm, the '
                     'line at its solved Z0, the ESD diode 0.2 pF (Infineon ESD103-B1-02 DS rev 1.3 Table 3, maximum '
                     'at 1 MHz), the bias choke >= 500 ohm (u-blox), the DNP shunts as open stubs ending in 0.03 pF, '
                     'the 0 ohm series part as 0.4 nH, the module port 50 ohm (all but the drawn lengths and the '
                     'solved impedances are assumptions, as in pass 2: Inference)')
BANDS = {'GNSS': (1.176e9, 1.20e9, 1.561e9, 1.575e9, 1.602e9, 1.61e9), 'RADIO': (0.902e9, 0.915e9, 0.928e9)}


def return_loss(board, gcpw_ev):
    ctx = C9.Ctx(board)
    fps = ctx.fps
    zl = GS.z0(w=1.2, gap_left=0.30, coated=True, ref='In2')
    out = dict(model=CASCADE, z_launch_ohm=zl['z0_ohm'], eps_eff_launch=zl['eps_eff'])
    pad_z = {}
    for w in (0.54, 0.60):
        r = GS.z0(w=w, gap_left=0.27, coated=True)
        pad_z[w] = (r['z0_ohm'], r['eps_eff'])
    out['pad_section_ohm'] = {str(k): v[0] for k, v in pad_z.items()}
    chains = {}
    pairs = gcpw_ev['gap_pairs']                    # {'gl/gr': samples} over both chains
    zsum = sum(gcpw_ev['z0_ohm'][k if k in gcpw_ev['z0_ohm'] else '/'.join(sorted(k.split('/')))] * n
               for k, n in pairs.items())
    z_mean = zsum / sum(pairs.values())             # the sample-weighted solved Z0 of the drawn line
    for name, ch in C9.CHAINS.items():
        path = C9.rf_path(ctx, name)
        nets = ch['nets']
        line = GS.z0(w=C9.RF_W, gap_left=0.27, coated=True)
        z_line = z_mean
        eeff = line['eps_eff']
        # elements along the path (path coordinate of each pad centre)
        elems = []
        for ref in sorted(C9.chain_parts(ch)):
            f = fps[ref]
            for p in f.Pads():
                if p.GetNetname() not in nets:
                    continue
                c = C9.xy(p.GetPosition())
                s, off = C9.project(path, c)
                kind = ('esd' if ref == ch['esd'] else 'choke' if ref == ch['bias'] else
                        'series' if ref == ch['series'] else 'stub')
                elems.append(dict(ref=f'{ref}.{p.GetNumber()}', kind=kind, s=round(s, 3), offset=round(abs(off), 3)))
        # the line pads' extents along the line, check_r9 R-5 line_pad_lengths on this board (D30.1 / D31.1 0.6,
        # L30.2 0.55, R304 / R316 pads 0.553 mm)
        pad_len = {'esd': 0.6, 'choke': 0.55, 'series': 0.553}
        s0, s1 = path['s0'], path['s1']
        ser = sorted((e for e in elems if e['kind'] == 'series'), key=lambda e: e['s'])
        res = {}
        for f in BANDS[name]:
            m = _line(zl['z0_ohm'], CASCADE['launch_mm'], f, zl['eps_eff'])
            m = _abcd_mul(m, _line(CASCADE['z_tail'], CASCADE['launch_tail_mm'], f, eeff))
            pos = s0 + CASCADE['launch_tail_mm']
            events = []
            for e in elems:
                if e['kind'] == 'stub':
                    events.append((e['s'], 'stub', e))
                elif e['kind'] == 'series':
                    continue
                else:
                    events.append((e['s'] - pad_len[e['kind']] / 2, 'pad_in', e))
                    events.append((e['s'], e['kind'], e))
                    events.append((e['s'] + pad_len[e['kind']] / 2, 'pad_out', e))
            if len(ser) == 2:
                events.append((ser[0]['s'] - pad_len['series'] / 2, 'pad_in', ser[0]))
                events.append((ser[0]['s'] + pad_len['series'] / 2, 'pad_out', ser[0]))
                events.append(((ser[0]['s'] + ser[1]['s']) / 2, 'series', ser[0]))
                events.append((ser[1]['s'] - pad_len['series'] / 2, 'pad_in', ser[1]))
                events.append((ser[1]['s'] + pad_len['series'] / 2, 'pad_out', ser[1]))
                body = (ser[0]['s'] + pad_len['series'] / 2, ser[1]['s'] - pad_len['series'] / 2)
            else:
                body = (0, 0)
            events.sort(key=lambda t: t[0])
            z_cur, in_pad = z_line, False
            for s, kind, e in events:
                s = min(max(s, pos), s1)
                seg = s - pos
                if body[0] - 1e-9 <= pos and s <= body[1] + 1e-9 and seg > 0:
                    seg = 0.0                          # inside the series part's body: lumped
                if seg > 1e-9:
                    m = _abcd_mul(m, _line(pad_z[0.54][0] if in_pad else z_cur, seg, f,
                                           pad_z[0.54][1] if in_pad else eeff))
                pos = s
                w = 2 * math.pi * f
                if kind == 'pad_in':
                    in_pad = True
                elif kind == 'pad_out':
                    in_pad = False
                elif kind == 'esd':
                    m = _abcd_mul(m, _shunt(1j * w * CASCADE['esd_pf'] * 1e-12))
                elif kind == 'choke':
                    m = _abcd_mul(m, _shunt(1 / (1j * CASCADE['choke_ohm'])))
                elif kind == 'series':
                    m = _abcd_mul(m, _series(1j * w * CASCADE['series_nh'] * 1e-9))
                elif kind == 'stub':
                    m = _abcd_mul(m, _shunt(_open_stub_y(z_line, e['offset'], f, eeff, CASCADE['stub_end_pf'] * 1e-12)))
            if s1 - pos > 1e-9:
                m = _abcd_mul(m, _line(z_line, s1 - pos, f, eeff))
            zload = CASCADE['load_ohm']
            zin = (m[0][0] * zload + m[0][1]) / (m[1][0] * zload + m[1][1])
            g = abs((zin - 50) / (zin + 50))
            res[f'{f / 1e9:.3f} GHz'] = dict(s11=round(g, 3), rl_db=round(-20 * math.log10(max(g, 1e-9)), 1),
                                             mismatch_db=round(-10 * math.log10(1 - g * g), 3))
        chains[name] = dict(line_z0_ohm=round(z_line, 2), eps_eff=eeff, path_jack_pad_end_to_module_pad_mm=round(s1 - s0, 3),
                            elements=elems, bands=res)
    out['chains'] = chains
    return out


def rf_separations(board):
    u30 = board.FindFootprintByReference('U30')
    cx, cy = mm(u30.GetPosition().x), mm(u30.GetPosition().y)
    # MAX-F10S body, DS Table 21 nominal 10.1 x 9.7 mm, the 10.1 along the pad rows (check_r9.BODY, local frame)
    R8Q.U30_BODY = (round(cx - 5.05, 3), round(cy - 4.85, 3), round(cx + 5.05, 3), round(cy + 4.85, 3))
    out = R8Q.rf(board)
    out['u30_body_box'] = R8Q.U30_BODY
    return out


# ---------------------------------------------------------------- mechanical
def holes(board, ties):
    """R8 requalify.holes with R9's tie holes left out."""
    out = []
    circles = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and d.GetClass() == 'PCB_SHAPE'
               and d.GetShape() == pcbnew.SHAPE_T_CIRCLE]
    for d in circles:
        c = (round(mm(d.GetCenter().x), 3), round(mm(d.GetCenter().y), 3))
        if any(math.dist(c, t) < 0.05 for t in ties):
            continue
        pt = pcbnew.SHAPE_CIRCLE(d.GetCenter(), MM(0.001))
        row = dict(at=list(c), diameter=round(2 * mm(d.GetRadius()), 3), nearest_pads={})
        for face, cu in (('F', pcbnew.F_Cu), ('B', pcbnew.B_Cu)):
            near = []
            for f in board.GetFootprints():
                for p in f.Pads():
                    if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or not p.IsOnLayer(cu):
                        continue
                    if math.dist(c, (mm(p.GetPosition().x), mm(p.GetPosition().y))) > R8Q.HOLE_REACH + 3:
                        continue
                    g = C8.min_gap(pt, p.GetEffectiveShape(cu), R8Q.HOLE_REACH)
                    if g is not None:
                        near.append((g, f'{f.GetReference()}.{p.GetNumber()}', p.GetNetname(), p.IsOnLayer(
                            pcbnew.F_Mask if face == 'F' else pcbnew.B_Mask)))
            near.sort()
            row['nearest_pads'][face] = [dict(mm=g, pad=n, net=net, exposed=e) for g, n, net, e in near[:3]]
        fills = set()
        for z in board.Zones():
            if z.GetIsRuleArea():
                continue
            for lay in board.GetEnabledLayers().CuStack():
                if z.IsOnLayer(lay) and z.HasFilledPolysForLayer(lay):
                    g = C8.min_gap(pt, z.GetFilledPolysList(lay), R8Q.WASHER + 0.01)
                    if g is not None:
                        fills.add(f'{z.GetNetname()} {board.GetLayerName(lay)} ({g:.2f})')
        row['fills_within_washer_radius'] = sorted(fills)
        out.append(row)
    return out


def tabs(board):
    issues, ev = TW.check(board)
    return dict(ok=not issues, issues=issues, **ev,
                rules=dict(length=TW.TAB_LEN, part=TW.TAB_PART, soft=TW.TAB_SOFT, connector=TW.TAB_CONN,
                           hole=TW.TAB_HOLE))


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--seed', type=Path)
    ap.add_argument('--fit', type=Path)
    a = ap.parse_args()
    path = a.board.resolve()
    board_sha = sha(path)
    seed = json.loads(a.seed.read_text()) if a.seed else PC.run_seed(path, None)
    fit = json.loads(a.fit.read_text()) if a.fit else None
    b = pcbnew.LoadBoard(str(path))
    ctx = C9.Ctx(b, path.parent, path)
    byn = R8Q.items_by_net(b)
    rep = dict(board=path.name, board_sha256=board_sha,
               script_sha256=sha(__file__),
               inputs_sha256={k: sha(ROOT / k) for k in ('tools/check_r9.py', 'tools/pyro_probe.py', 'tools/bridge_table.py',
                                                         'm3_design/r9_pyro_check.py', 'm3_design/r9_rf_check.py',
                                                         'tools/gcpw_solve.py', 'm3_design/assembly_review/m3.kicad_dru')})
    if seed and seed.get('board_sha256') != board_sha:
        raise SystemExit('the seeded rule-H report is not of this board')
    if fit and fit.get('board_sha256', board_sha) != board_sha:
        raise SystemExit('the fit report is not of this board')
    r7, tmp = RC.r7_board()                    # kept alive with b (SWIG, step-1 note)
    sections = {}

    def run(key, fn):
        try:
            sections[key] = fn()
        except Exception as e:                 # report and continue: one section must not hide the others
            sections[key] = dict(error=f'{type(e).__name__}: {e}')
        print(key, 'done', flush=True)
    run('pyro.margins', lambda: dict(zip(('issues', 'evidence'), PC.gate_margins(b))))
    run('pyro.bridges', lambda: dict(zip(('issues', 'evidence'), PC.gate_bridges(b)), table=BT.table(b)))
    run('pyro.rule_h', lambda: dict(zip(('issues', 'evidence'), PC.gate_rule_h(seed, board_sha)),
                                    pairs=seed.get('pairs') if seed else None))
    run('pyro.reset', lambda: dict(p7=C9.p7(ctx)[1]['reset_voltage_table'],
                                   gate_n=dict(zip(('issues', 'evidence'), PC.gate_neighbours(b, ctx))),
                                   model=dict(gate_reset_max_v=BT.GATE_RESET_MAX, basis=BT.__doc__.split('Reset model')[1]
                                              .strip())))
    run('pyro.divider', lambda: divider(b, ctx))
    run('pyro.armed', lambda: dict(zip(('issues', 'evidence'), PC.gate_armed(b, ctx))))
    run('pyro.bare', lambda: R8Q.bare(b))
    run('pyro.coat', lambda: dict(p10=C9.p10(ctx)[1], p1=C9.p1(ctx)[1], p6=C9.p6(ctx)[1]))
    run('pyro.exits', lambda: dict(exits=exits(b, byn), p9=C9.p9(ctx)[1], m6=C9.m6(ctx)[1],
                                   d19=C9.k_power_pyro(ctx)[1].get('gate_servo')))
    run('pyro.block_vias', lambda: block_vias(b, byn))
    run('pyro.tp122', lambda: tp122(b, byn))
    run('pyro.wire_room', lambda: dict(p11=C9.p11(ctx)[1], note='fit_check prints the bore-wall figures (J121 / J124 '
                                     '6.4-7.0 mm at 5.0 mm height): gate/check_sh.txt'))
    run('pyro.fire_bars', lambda: PC.evidence(b))
    run('rf.gcpw', lambda: dict(zip(('issues', 'evidence'), RC.gate_gcpw(b))))
    frames = RC.r9_rf.Frames(b)
    run('rf.launch', lambda: dict(zip(('issues', 'evidence'), RC.gate_launch(b, r7, frames))))
    run('rf.r7', lambda: dict(zip(('issues', 'evidence'), RC.gate_r7(b, r7, frames))))
    run('rf.return_loss', lambda: return_loss(b, sections['rf.gcpw']['evidence']))
    run('rf.contract', lambda: {k: v['evidence'] for k, v in C9.check_board(
        b, path.parent, path, only={f'R-{k}' for k in range(1, 14)})['rules'].items()})
    run('rf.separations', lambda: rf_separations(b))
    ties = [tuple(h) for h in C9.m3(ctx)[1]['holes']]
    run('mech.holes', lambda: holes(b, ties))
    run('mech.edges', lambda: R8Q.edges(b))
    run('mech.tabs', lambda: tabs(b))
    run('mech.mark', lambda: R8Q.mark(b))
    run('mech.parts', lambda: R8Q.parts(b))
    run('imu', lambda: dict(R8Q.imu(b), m7=C9.m7(ctx)[1]))
    run('probes', lambda: R8Q.probes(b))
    rep.update(sections)
    errors = [k for k, v in sections.items() if isinstance(v, dict) and 'error' in v]
    issues = {k: v['issues'] for k, v in sections.items() if isinstance(v, dict) and v.get('issues')}
    rep['errors'], rep['issues'] = errors, issues
    a.out.write_text(json.dumps(rep, indent=1, default=str) + '\n')
    print('sections with an error:', errors or 'none')
    print('sections with issues:', list(issues) or 'none')
    del r7, tmp
    return 1 if errors or issues else 0


if __name__ == '__main__':
    raise SystemExit(main())
