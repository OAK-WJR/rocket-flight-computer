#!/usr/bin/env python3
"""Generate m3_design/r8_keepclear.tsv: the routing reservations the placement freeze must leave free (R8 step 4, D31).

usage: <KiCad python3> -I make_keepclear.py PLACED_BOARD OUT.tsv [BUILT_BOARD [--routed]]

The reservations are the copper the four spikes proved (m3_design/r8_spikes/*/RESULT.md) on the placement they used,
as segments with their net, layer and width, plus the step-4 lanes listed in MANUAL below (the pyro exits' lanes from
spike (a)'s corridor analysis and the RAW_ACT_SENSE lane of D32). r8_legalise.py checks every pad against them with the
project's clearance rules, so a part that would block a proven route fails the build. Steps 5-7 port this copper into
the r8 generators; where they change it, they regenerate this table (or drop it once the copper itself is built).

  spike (a)  spike_geom.copper(): QSPI, HSE, NRST (to (12.0, 47.85); its tail follows J2's move, step 6), ARM1_SENSE,
             BOOT0, VCAP / VDD escapes, decoupling GND vias
  spike (b)  servo_route.route(): the four lanes, rows, vias, D121 taps and stitching vias (run on PLACED_BOARD; its pad
             assertions hold only if the servo parts are where the spike put them)
  spike (c)  battery.copper(): tracks and vias only (its zones are r8_power.py's, step 5); without the RAW_ACT_SENSE
             divider copper and the corridor reservation lanes (replaced by MANUAL), and with the switch legs, the
             BAT_ENABLE via and R120's gate stub moved with the L10 nudges of D30
  spike (d)  rf_route_r8: GNSS and radio lanes, strip leads, the fence row, stitching, the status-LED lanes
Only F and B (outer) copper is reserved; vias are 'FB'.

BUILT_BOARD (step 5 on): a board with the copper the build steps so far draw (r8_power.py's output). A reservation that
copper already covers (same net and layer, both ends and the middle on one of its tracks, or a via at the same point)
is dropped, and so is every reservation of a net in BUILT_NETS, which step 5 routes completely (its own geometry
replaces the spikes' where they differ: D43, D46). The reservations left are the later steps'.

--routed (step 6 on, D60): BUILT_BOARD carries the signal families of r8_route.py as well. Every reservation of a net
those families complete (their NETS, and the 3V3 / 3V3A rails they finish) is dropped too: the families' own geometry
(R8_DECISIONS D51 on) replaces the spikes' and the step-4 / step-5 lanes, and their gates (r8_route_check.py) check
it. What is left is step 7's: the GND fence and stitching vias not yet built.

Step 7 on (D66): BUILT_BOARD carries r8_ground.py's GND copper too (its pour trims R8_POUR_TRIM_G* mark it); every
reservation it builds is dropped by the covered-copper rule above, which leaves the table empty.
"""
import importlib.util
import math
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SPIKES = ROOT / 'm3_design/r8_spikes'
mm, MM = pcbnew.ToMM, pcbnew.FromMM

# step-4 lanes (net, layer, width, polyline) and vias (net, x, y, diameter). Basis: spike (a) RESULT "GATE_N and CONT
# corridor": ARM is the westmost lane (x 18.18), GATE_N at about x 18.6-18.75 with its via near pin 3 at (18.75, 54.3),
# CONT next to it, reaching R168 from the north at about y 57.5; spike (c) section 5 for the exits' turns (y 88.33 /
# 87.6). D32: the RAW_ACT_SENSE lane from the divider at J122's aft end to R172 at pin 34, on B.Cu east of ARM.
MANUAL_TRACKS = [
    ('PYRO1_GATE_N', 'B', 0.2, [(23.0, 88.33), (19.3, 88.33), (18.75, 87.78), (18.75, 54.3)]),
    ('PYRO1_GATE_N', 'F', 0.2, [(18.0, 52.55), (18.0, 53.55), (18.75, 54.3)]),
    ('PYRO1_CONT', 'B', 0.2, [(28.4, 88.61), (27.39, 87.6), (19.85, 87.6), (19.25, 87.0), (19.25, 58.1),
                              (19.85, 57.5), (22.57, 57.5), (23.17, 56.9), (23.17, 54.6)]),
    # D32: RAW_ACT tap J122.11 -> R177.1; the SENSE spine R124.2 / R125.1 / R182.1 / C122.1 on x 25.92, then B.Cu
    # under the servo lanes (y 58.1) and down x 30.6, east of ARM1_SENSE, to R172.1 under U1's east pad row
    ('RAW_ACT', 'B', 0.2, [(23.0, 71.89), (25.86, 69.03), (25.92, 69.03)]),
    # D45: its turn to y 58.1 is a 45-degree chamfer from (25.92, 60.0), which leaves step 5's 3V3A trunk (C10 / C11
    # to C21 / C22 under the VDDA pins) and R62's 3V3 via room south-west of it
    ('RAW_ACT_SENSE', 'B', 0.2, [(25.92, 66.27), (25.92, 60.0), (27.82, 58.1), (30.0, 58.1), (30.6, 57.5),
                                 (30.6, 48.53)]),
    # D33: east-face escapes outward to vias (the inward side is spike (a)'s): pin 34 back west to R172.2, pin 35 and
    # the camera status pins 41 / 42 to B.Cu (D3's corridor between NRST and DIO1; spike (d) F-4)
    ('RAW_ACT_SENSE_MCU', 'F', 0.2, [(30.55, 47.0), (31.9, 47.0)]),
    ('RAW_ACT_SENSE_MCU', 'B', 0.2, [(31.9, 47.0), (31.23, 47.67), (30.6, 47.67)]),
    ('CAM_5V_SENSE', 'F', 0.2, [(30.55, 46.5), (32.25, 46.5), (32.55, 46.2)]),
    # D33: CAM_5V reaches the sense divider's top resistor R104 through a gap in the camera test-pad column
    ('CAM_5V', 'B', 0.3, [(39.4, 47.7), (35.73, 47.7)]),
    ('CAM_FAULT_N', 'F', 0.2, [(30.55, 43.5), (32.45, 43.5)]),
    ('CAM_PWR_EN', 'F', 0.2, [(30.55, 43.0), (31.85, 43.0)]),
    ('CAM_FAULT_N', 'B', 0.2, [(32.45, 43.5), (32.45, 36.2)]),
    # D37: CAM_PWR_EN comes round U7's west end to R74 south of U7 (EN is on U7's far row, FLT on the near one)
    ('CAM_PWR_EN', 'B', 0.2, [(31.85, 43.0), (31.85, 36.8), (28.0, 36.8), (28.0, 27.5), (30.775, 27.5)]),
    # D33: VLOGIC reaches the top-side VLOGIC divider at pin 17 through one via north of the RAS lane; pin 17's sense
    # lane runs north on F.Cu, pin 18 dives east of it to the bottom-side V3V3 divider, pin 15 dives to R168
    ('VLOGIC', 'F', 0.2, [(26.95, 60.5), (26.95, 55.3), (26.53, 55.3)]),
    ('VLOGIC_SENSE', 'F', 0.2, [(25.0, 52.55), (25.0, 55.3)]),
    ('V3V3_SENSE', 'F', 0.2, [(25.5, 52.55), (25.5, 54.0), (25.75, 54.25)]),
    ('V3V3_SENSE', 'B', 0.2, [(25.75, 54.25), (25.85, 54.35), (25.85, 55.73)]),
    ('PYRO1_CONT_MCU', 'F', 0.2, [(24.0, 52.55), (24.0, 53.7)]),
    ('PYRO1_CONT_MCU', 'B', 0.2, [(24.0, 53.7), (24.0, 54.33)]),
]
MANUAL_VIAS = [('PYRO1_GATE_N', 18.75, 54.3, 0.5), ('RAW_ACT_SENSE_MCU', 31.9, 47.0, 0.5), ('CAM_5V_SENSE', 32.55, 46.2, 0.5),
               ('CAM_FAULT_N', 32.45, 43.5, 0.5), ('CAM_PWR_EN', 31.85, 43.0, 0.5), ('VLOGIC', 26.95, 60.5, 0.5),
               ('V3V3_SENSE', 25.75, 54.25, 0.5), ('PYRO1_CONT_MCU', 24.0, 53.7, 0.5)]
# spike (a)'s C21 / C22 GND via (27.2, 56.1) sits on spike (b)'s SERVO1_MCU lane (x 27.5, F.Cu): two GND vias outside
# the lanes replace it (D31)
A_REPLACED = {('GND', 27.2, 56.1)}
A_REPLACED_TRACKS = {('GND', ((26.5, 56.02), (26.5, 56.1), (27.2, 56.1)))}
A_ADDED_TRACKS = [('GND', 'B', 0.2, [(26.5, 56.02), (26.5, 56.65), (26.3, 56.85)]), ('GND', 'B', 0.2, [(29.1, 55.18), (29.85, 55.18)])]
A_ADDED_VIAS = [('GND', 26.3, 56.85, 0.5), ('GND', 29.85, 55.18, 0.5)]
SPIKE_C_DROP_NETS = {'RAW_ACT_SENSE', 'RAW_ACT_SENSE_MID', 'PYRO1_GATE_N', 'PYRO1_CONT', 'ARM1_SENSE',
                     'BAT_SW_SOURCE', 'BAT_SW_RETURN'}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(Path(path).parent))
    spec.loader.exec_module(mod)
    return mod


def segs(rows, family, net, layer, w, pts):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if (x0, y0) != (x1, y1):
            rows.append((family, net, layer, w, x0, y0, x1, y1))


def board_items(b, before, family, rows, drop=lambda t: False):
    """Tracks and vias added to b since the UUID set `before`."""
    for t in b.GetTracks():
        if t.m_Uuid.AsString() in before or drop(t):
            continue
        net = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            p = t.GetPosition()
            rows.append((family, net, 'FB', round(mm(t.GetWidth(pcbnew.F_Cu)), 4), round(mm(p.x), 4), round(mm(p.y), 4),
                         round(mm(p.x), 4), round(mm(p.y), 4)))
        else:
            lay = {pcbnew.F_Cu: 'F', pcbnew.B_Cu: 'B'}.get(t.GetLayer())
            if lay:
                rows.append((family, net, lay, round(mm(t.GetWidth()), 4), round(mm(t.GetStart().x), 4),
                             round(mm(t.GetStart().y), 4), round(mm(t.GetEnd().x), 4), round(mm(t.GetEnd().y), 4)))


# nets r8_power.py (step 5) routes completely: every reservation of theirs is dropped once it has run
BUILT_NETS = {'RAW_ACT', 'BAT_IN', 'ACT_GATE', 'ACT_DRV', 'ACT_EN', 'BAT_DAMP', 'BAT_SW_SOURCE', 'BAT_SW_RETURN',
              'RAW_PROTECTED', 'VLOGIC', 'VCAP1', 'VCAP2'}


def built_copper(path):
    """(tracks by (net, layer), vias by net) of the board at path."""
    b = pcbnew.LoadBoard(str(path))
    tracks, vias = {}, {}
    for t in b.GetTracks():
        net = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            p = t.GetPosition()
            vias.setdefault(net, set()).add((round(mm(p.x), 2), round(mm(p.y), 2)))
            continue
        lay = {pcbnew.F_Cu: 'F', pcbnew.B_Cu: 'B'}.get(t.GetLayer())
        if lay:
            tracks.setdefault((net, lay), []).append(((mm(t.GetStart().x), mm(t.GetStart().y)),
                                                      (mm(t.GetEnd().x), mm(t.GetEnd().y))))
    return tracks, vias


def _on(p, a, b, tol=0.02):
    lx, ly = b[0] - a[0], b[1] - a[1]
    n = lx * lx + ly * ly
    t = 0.0 if n == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * lx + (p[1] - a[1]) * ly) / n))
    return math.hypot(p[0] - a[0] - t * lx, p[1] - a[1] - t * ly) < tol


def is_built(row, tracks, vias):
    _, net, layer, _, x0, y0, x1, y1 = row
    if layer == 'FB':
        return (round(x0, 2), round(y0, 2)) in vias.get(net, ())
    segs = tracks.get((net, layer), [])
    return all(any(_on(p, *s) for s in segs) for p in ((x0, y0), (x1, y1), ((x0 + x1) / 2, (y0 + y1) / 2)))


def routed_nets():
    """The nets r8_route.py's signal families complete (step 6), with the rails they finish."""
    sys.path.insert(0, str(ROOT / 'm3_design'))
    import r8_route
    nets = {'3V3', '3V3A'}
    for fam in r8_route.FAMILIES:
        nets |= set(r8_route.load_family(fam).NETS)
    return nets


def main(board_path, out, built=None, routed=False):
    rows = []
    # spike (a)
    a = load(SPIKES / 'a_underU1/spike_geom.py', 'spike_a_geom')
    tracks, vias = a.copper()
    for net, layer, pts, w in tracks:
        if (net, tuple(tuple(p) for p in pts)) in A_REPLACED_TRACKS:
            continue
        if net == 'NRST':                      # the tail to R7's J2 position goes (J2 moved west, D3 / spike (d) P7)
            pts = [p for p in pts if not (p[0] < 12.0 - 1e-6)]
            if layer == 'F' and pts and all(abs(p[1] - 42.6) < 1e-6 for p in pts):
                continue
        segs(rows, 'a', net, layer, w, pts)
    for net, x, y, d, _ in vias:
        if (net, x, y) == ('NRST', 7.6, 42.6) or (net, x, y) in A_REPLACED:
            continue
        rows.append(('a', net, 'FB', d, x, y, x, y))
    # spike (d)
    d = load(SPIKES / 'd_rf/rf_route_r8.py', 'spike_d_route')
    for net, pts, layer, w in d.gnss_lanes() + d.radio_lanes() + d.strip_lanes() + d.status_lanes():
        segs(rows, 'd', net, layer[0], w, [(d.r(x), d.r(y)) for x, y in pts])
    for net, x, y, size in d.LIMITER_VIAS + d.VIAS:
        rows.append(('d', net, 'FB', size[0], x, y, x, y))
    for x in d.FENCE_X:
        rows.append(('d', 'GND', 'FB', d.VIA_FENCE[0], x, d.FENCE_Y, x, d.FENCE_Y))
    for x, y in d.STITCH:
        rows.append(('d', 'GND', 'FB', d.VIA_FENCE[0], x, y, x, y))
    # spike (b): run its route on the placed board (asserts the servo pads are where it put them)
    b = pcbnew.LoadBoard(str(board_path))
    sb = load(SPIKES / 'b_servo/servo_route.py', 'spike_b_route')
    before = {t.m_Uuid.AsString() for t in b.GetTracks()}
    sb.check_pads(b)
    sb.route(b, sb.IN2_3V3_TONGUE)
    board_items(b, before, 'b', rows)
    # spike (c): tracks and vias only, on the placed board
    sc = load(SPIKES / 'c_battery/battery.py', 'spike_c_band')
    before = {t.m_Uuid.AsString() for t in b.GetTracks()}
    band = sc.Band(b)
    band.zone = lambda *args, **kw: None
    sc.copper(band)
    moved = {(16.6, 106.0), (16.6, 107.075)}        # R165's BAT_ENABLE stub and via (R165 moved aft, D30)
    gone = {(41.6, 100.0)}                          # the input caps' GND via sits on the moved BAT_IN feed (D36)

    def drop(t):
        if t.GetNetname() in SPIKE_C_DROP_NETS:
            return True
        if t.GetClass() == 'PCB_VIA' and (round(mm(t.GetPosition().x), 3), round(mm(t.GetPosition().y), 3)) in gone:
            return True
        if t.GetNetname() == 'BAT_IN' and t.GetClass() != 'PCB_VIA' and \
                abs(mm(t.GetStart().x) - 40.75) < 1e-3 and abs(mm(t.GetEnd().x) - 40.75) < 1e-3:
            return True                                 # the eFuse feed lane follows U9 (D36)
        if t.GetNetname() == 'BAT_ENABLE':
            ends = [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]
            return any((round(mm(p.x), 3), round(mm(p.y), 3)) in moved for p in ends)
        return False
    board_items(b, before, 'c', rows, drop)
    for net, layer, w, pts in A_ADDED_TRACKS:
        segs(rows, 'a', net, layer, w, pts)
    for net, x, y, dia in A_ADDED_VIAS:
        rows.append(('a', net, 'FB', dia, x, y, x, y))
    for net, layer, w, pts in MANUAL_TRACKS + C_MOVED_TRACKS:
        segs(rows, 's4', net, layer, w, pts)
    for net, x, y, dia in MANUAL_VIAS + C_MOVED_VIAS:
        rows.append(('s4', net, 'FB', dia, x, y, x, y))
    for net, layer, w, pts in STEP5_TRACKS:
        segs(rows, 's5', net, layer, w, pts)
    for net, x, y, dia in STEP5_VIAS:
        rows.append(('s5', net, 'FB', dia, x, y, x, y))
    dropped = 0
    grounded = built is not None and any(z.GetIsRuleArea() and z.GetZoneName().startswith('R8_POUR_TRIM_G')
                                         for z in pcbnew.LoadBoard(str(built)).Zones())
    if built:
        tracks, vias = built_copper(built)
        gone = BUILT_NETS | (routed_nets() if routed else set())
        kept = [r for r in rows if r[1] not in gone and not is_built(r, tracks, vias)]
        dropped, rows = len(rows) - len(kept), kept
    with open(out, 'w') as fh:
        fh.write('# R8 routing reservations (m3_design/assembly_review/sources/r8_design/step4/make_keepclear.py; '
                 'R8_DECISIONS D31). family: spike a/b/c/d, s4 (step 4) or s5 (step 5, D50)'
                 + ('; without the copper steps 5-7 build (r8_power.py, r8_route.py, r8_ground.py: D48, D60, D66)'
                    if routed and grounded else
                    '; without the copper steps 5-6 build (r8_power.py, r8_route.py: D48, D60)' if routed else
                    '; without the copper step 5 builds (r8_power.py, D48)' if built else '') + '\n')
        fh.write('family\tnet\tlayer\tw\tx0\ty0\tx1\ty1\n')
        for r in rows:
            fh.write('\t'.join(str(round(v, 4)) if isinstance(v, float) else str(v) for v in r) + '\n')
    print(f'{len(rows)} reservations written to {out}' +
          (f' ({dropped} built by step {"7" if grounded else "6" if routed else "5"} dropped)' if built else ''))


# spike (c) copper that follows the L10 nudges of D30 (switch legs to J1.3 / J1.4, BAT_ENABLE's via)
C_MOVED_TRACKS = [
    ('BAT_SW_SOURCE', 'B', 0.25, [(20.46, 106.92), (20.46, 110.4)]),                  # R80.2 -> J1.3
    ('BAT_SW_RETURN', 'B', 0.25, [(16.6, 106.92), (16.6, 109.18), (15.38, 110.4)]),   # R165.1 -> J1.4
    ('BAT_ENABLE', 'B', 0.25, [(16.6, 105.28), (16.6, 104.5)]),                        # R165.2 -> via
    ('BAT_ENABLE', 'F', 0.25, [(16.6, 104.5), (16.6, 99.25)]),                         # up to spike (c)'s lane
]
C_MOVED_VIAS = [('BAT_ENABLE', 16.6, 104.5, 0.6)]
# D36: U9 aft of J121's L10 zone at (41.5, 85.5): the BAT_IN feed lane on x 41.25 into pad 5's north end; BAT_ENABLE
# and RAW_PROTECTED continue the spike's top-side lanes east of J121 and drop to U9 (EN's spine x 40.42, OUT's south end)
C_MOVED_TRACKS += [
    ('BAT_IN', 'B', 0.5, [(41.25, 102.4), (41.25, 87.4)]),
    ('BAT_IN', 'B', 0.3, [(41.25, 87.4), (41.25, 86.6)]),
    ('BAT_ENABLE', 'F', 0.25, [(38.5, 99.25), (42.9, 99.25), (42.9, 93.5), (40.42, 93.5)]),
    ('BAT_ENABLE', 'B', 0.25, [(40.42, 93.5), (40.42, 86.38), (40.6, 86.2)]),
    ('RAW_PROTECTED', 'F', 0.25, [(38.5, 99.75), (45.3, 99.75), (45.3, 83.7), (41.75, 83.7)]),
    # D37: RAW_PROTECTED's trunk to the logic mux U11 and the camera eFuse U7 runs down the east side on F.Cu (east
    # of J1 / J121 / C84, between J9's signal and mounting pads), drops to B.Cu south of L3 and runs along y 25.6 to
    # U7's IN pins: OUT leaves U7 east to the buck, so IN is fed from the south-east without crossing it
    ('RAW_PROTECTED', 'F', 0.4, [(45.3, 83.7), (45.3, 51.5), (43.6, 49.8), (42.15, 49.8), (42.15, 26.2)]),
    ('RAW_PROTECTED', 'B', 0.4, [(42.15, 26.2), (42.15, 25.6), (34.65, 25.6), (34.05, 26.2), (34.05, 29.5)]),
]
C_MOVED_VIAS += [('GND', 42.0, 100.6, 0.6), ('BAT_ENABLE', 40.42, 93.5, 0.6), ('RAW_PROTECTED', 41.75, 83.7, 0.6), ('RAW_PROTECTED', 42.15, 26.2, 0.6)]

# D50 (step 5): the U9 / U11 status lanes to the MCU, the one way the step-5 power copper leaves them.
# - BAT_FAULT_N: U9.4, R89.2 and TP85 on B.Cu, under the 3V3 spine's y 82.0 line to a via south of it, then F.Cu down
#   x 33.6 between the servo-row vias (x 32.6) and the spine, over USB_LIMITED's B.Cu run, into pin 28 from the east.
# - LOGIC_SOURCE_ST: U11.9 south, then east on B.Cu (y 57.27) to TP87 and R91.2; one via (38.6, 57.27), then F.Cu
#   south of C84, past C90's 3V3 via, and west under BAT_FAULT_N's turn into pin 29.
STEP5_TRACKS = [
    ('BAT_FAULT_N', 'B', 0.2, [(40.6, 84.8), (37.675, 84.8), (37.675, 83.6), (36.0, 83.6), (35.4, 83.0), (33.6, 81.2)]),
    ('BAT_FAULT_N', 'F', 0.2, [(33.6, 81.2), (33.6, 51.0), (32.6, 50.0), (30.55, 50.0)]),
    ('LOGIC_SOURCE_ST', 'B', 0.2, [(36.75, 57.85), (36.75, 57.27), (43.595, 57.27), (44.3, 57.975)]),
    ('LOGIC_SOURCE_ST', 'B', 0.2, [(42.0, 57.27), (42.0, 58.5)]),
    ('LOGIC_SOURCE_ST', 'F', 0.2, [(38.6, 57.27), (38.6, 55.4), (35.4, 52.2), (35.4, 50.4), (34.5, 49.5),
                                   (30.55, 49.5)]),
]
STEP5_VIAS = [('BAT_FAULT_N', 33.6, 81.2, 0.5), ('LOGIC_SOURCE_ST', 38.6, 57.27, 0.5)]

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--routed']
    main(Path(args[0]), Path(args[1]), Path(args[2]) if len(args) > 2 else None, '--routed' in sys.argv[1:])
