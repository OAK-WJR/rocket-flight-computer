#!/usr/bin/env python3
"""R8 spike 3(b): the servo bus through D121 to J122 (KiCad Python). Primary approach, no relabel (D7).

usage: <KiCad python3> -I servo_route.py BASE_BOARD OUT_BOARD [--no-fill] [--in2-full-tongue]

Geometry (board mm, y forward; U1 at rotation 0, (23, 45); J122 rigid at (23, 75.7) rot 90):
  per channel i = 1..4, lane x X[i] (= U1.(21+i) pad centre), row y Y[i] (= J122.(3i-2) pad centre)
  F.Cu  U1.(21+i) -> straight forward on x X[i] -> 45 deg (CHAMFER) -> east on y Y[i] -> pull-down pad
        R(153+i).1 (node) -> via V[i] at (VIA_X, Y[i])                                  [SERVOi_MCU]
  B.Cu  V[i] -> R(149+i).1 (x RES_X + 1) | 1k | R(149+i).2 (x RES_X - 1) -> J122.(3i-2)   [MCU | OUT]
        the four B.Cu rows cross under the F.Cu lanes: that is the full reversal U1 order -> J122 row order
  B.Cu  V[i] -> east branch to D121 (B.Cu, rot 180): pin 3 (S2) and 4 (S3) straight, pin 1 (S1) and 6 (S4) round the
        north / south row ends with one 45 deg corner; pin 2 (GND) -> GND via north, pin 5 (3V3) -> 3V3 via south
  GND   stitching vias in the three pockets between rows (F.Cu pull-down GND pads and the B.Cu pockets)
  In2   (placeholder for spike (c) / step 5) GND under the B.Cu rows west of the via column (r8_plan section 1: In2
        GND under every servo lane); a 3V3 tongue under D121 only, for D121.5's via, joined to the 3V3 region (y <= 66.8);
        --in2-full-tongue puts the rows over 3V3 too (also passes)
Parts moved: D121, R150-R157 (servo); R124 R177 R125 R182 C122 (RAW_ACT_SENSE divider) east, out of the way.
"""
import sys

import pcbnew

MM, mm = pcbnew.FromMM, pcbnew.ToMM

# --- geometry -------------------------------------------------------------------------------------------------------
CH = (1, 2, 3, 4)
X = {1: 27.5, 2: 28.0, 3: 28.5, 4: 29.0}          # U1.22-25 pad centres (rotation 0, (23, 45))
U1_Y = 52.55                                       # U1 forward-face pad centre line
Y = {1: 79.51, 2: 76.97, 3: 74.43, 4: 71.89}      # J122.1/4/7/10 (signal column x 25.54)
J122_X = 25.54
CHAMFER = 0.5                                      # 45 deg corner, mm on each axis
RES_X = 30.4                                       # R150-R153 centre (rot 180: pad 1 / MCU east, pad 2 / OUT west)
PD_X = 30.4                                        # R154-R157 pull-downs (F.Cu rot 270: pad 1 on the row, pad 2 GND +y)
VIA_X = 32.6
D121_XY = (34.4, 75.70)                            # B.Cu rot 180: 1 NE, 2 N (GND), 3 NW, 4 SW, 5 S (3V3), 6 SE
D121_PIN = {1: '1', 2: '3', 3: '4', 4: '6'}
D121_GND_VIA = (34.4, 78.20)
D121_3V3_VIA = (34.4, 73.20)
POCKET_GND_VIAS = [(31.4, (Y[i] + Y[i + 1]) / 2) for i in (1, 2, 3)]
W_SIG, W_PWR = 0.2, 0.3
VIA_D, VIA_DRILL = 0.6, 0.3
PLACE = {   # ref: (x, y, rot, side)
    'D121': (D121_XY[0], D121_XY[1], 180, 'B'),
    **{f'R{149 + i}': (RES_X, Y[i], 180, 'B') for i in CH},
    **{f'R{153 + i}': (PD_X, Y[i] + 0.43, 270, 'F') for i in CH},
    # RAW_ACT_SENSE divider: out of the servo interface (its own home is step 4's; it must stay east of x ~36.2).
    # R177.1 (RAW_ACT) aft, the MID pads facing, R124.2 (RAW_ACT_SENSE) 1.9 mm from R177.1 (rule H: >= 1.0 mm)
    'R177': (37.4, 73.4, 270, 'B'), 'R124': (37.4, 75.4, 270, 'B'),
    'R125': (39.6, 75.4, 0, 'B'), 'R182': (39.6, 76.6, 0, 'B'), 'C122': (39.8, 78.0, 0, 'B'),
}
# default (r8_plan section 1, "In2 GND under every servo lane"): the B.Cu rows west of the via column over In2 GND, only
# D121 and its dead-end tap branches over a 3V3 tongue (edge between the via column and D121)
IN2_3V3_TONGUE = [(32.95, 66.5), (37.0, 66.5), (37.0, 81.0), (32.95, 81.0)]
IN2_3V3_TONGUE_FULL = [(24.6, 66.5), (37.0, 66.5), (37.0, 81.0), (24.6, 81.0)]     # --in2-full-tongue


def v(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def track(b, net, layer, a, c, w=W_SIG):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(v(*a))
    t.SetEnd(v(*c))
    t.SetWidth(MM(w))
    t.SetLayer(layer)
    t.SetNet(b.FindNet(net))
    b.Add(t)
    return t


def path(b, net, layer, pts, w=W_SIG):
    return [track(b, net, layer, pts[k], pts[k + 1], w) for k in range(len(pts) - 1)]


def via(b, net, xy):
    t = pcbnew.PCB_VIA(b)
    t.SetPosition(v(*xy))
    t.SetWidth(MM(VIA_D))
    t.SetDrill(MM(VIA_DRILL))
    t.SetViaType(pcbnew.VIATYPE_THROUGH)
    t.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    t.SetNet(b.FindNet(net))
    b.Add(t)
    return t


def place(b):
    for ref, (x, y, rot, side) in PLACE.items():
        f = b.FindFootprintByReference(ref)
        if (side == 'B') != f.IsFlipped():
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        f.SetOrientationDegrees(rot)
        f.SetPosition(v(x, y))


def pad_xy(b, ref, num):
    p = next(p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num)
    return round(mm(p.GetPosition().x), 4), round(mm(p.GetPosition().y), 4), p.GetNetname()


def check_pads(b):
    """The geometry above assumes these pad centres and nets; refuse to draw if the board differs."""
    for i in CH:
        want = [(('U1', str(21 + i)), (X[i], U1_Y, f'SERVO{i}_MCU')),
                (('J122', str(3 * i - 2)), (J122_X, Y[i], f'SERVO{i}_OUT')),
                ((f'R{149 + i}', '1'), (RES_X + 1, Y[i], f'SERVO{i}_MCU')),
                ((f'R{149 + i}', '2'), (RES_X - 1, Y[i], f'SERVO{i}_OUT')),
                ((f'R{153 + i}', '1'), (PD_X, Y[i], f'SERVO{i}_MCU'))]
        for (ref, num), (x, y, net) in want:
            got = pad_xy(b, ref, num)
            assert abs(got[0] - x) < 1e-3 and abs(got[1] - y) < 1e-3 and got[2] == net, (ref, num, got, (x, y, net))
    for num, net in (('2', 'GND'), ('5', '3V3')):
        assert pad_xy(b, 'D121', num)[2] == net


def route(b, tongue=IN2_3V3_TONGUE):
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    dx0, dy0 = D121_XY
    for i in CH:
        net, out = f'SERVO{i}_MCU', f'SERVO{i}_OUT'
        x, y = X[i], Y[i]
        path(b, net, F, [(x, U1_Y), (x, y - CHAMFER), (x + CHAMFER, y), (PD_X, y), (VIA_X, y)])
        via(b, net, (VIA_X, y))
        track(b, net, B, (VIA_X, y), (RES_X + 1, y))
        track(b, out, B, (RES_X - 1, y), (J122_X, y))
        px, py, _ = pad_xy(b, 'D121', D121_PIN[i])
        if i in (2, 3):                                  # NW / SW pads: straight in on the row (0.12 mm off centre)
            track(b, net, B, (VIA_X, y), (px, y))
        else:                                            # NE / SE pads: round the row end, one 45 deg corner
            s = -1 if i == 1 else 1                      # S1 turns aft (-y) into pin 1, S4 forward into pin 6
            path(b, net, B, [(VIA_X, y), (px - CHAMFER, y), (px, y + s * CHAMFER), (px, py)])
    for num, net, xy in (('2', 'GND', D121_GND_VIA), ('5', '3V3', D121_3V3_VIA)):
        px, py, _ = pad_xy(b, 'D121', num)
        track(b, net, B, (px, py), xy, W_PWR)
        via(b, net, xy)
    for xy in POCKET_GND_VIAS:
        via(b, 'GND', xy)
    z = pcbnew.ZONE(b)
    z.SetLayer(pcbnew.In2_Cu)
    z.SetNet(b.FindNet('3V3'))
    z.SetZoneName('SPIKE_3V3_In2_servo_tongue')
    o = z.Outline()
    o.NewOutline()
    for px, py in tongue:
        o.Append(MM(px), MM(py))
    z.SetAssignedPriority(4)                         # above the 3V3 region it overlaps (distinct priorities)
    z.SetLocalClearance(MM(0.25))
    z.SetMinThickness(MM(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    b.Add(z)


def main(src, dst, fill=True, full=False):
    pcbnew.KIID.SeedGenerator(8322)               # deterministic UUIDs (byte-identical rebuilds)
    b = pcbnew.LoadBoard(src)
    place(b)
    check_pads(b)
    route(b, IN2_3V3_TONGUE_FULL if full else IN2_3V3_TONGUE)
    if fill:
        b.BuildConnectivity()
        assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'native zone fill failed'
    b.Save(dst)
    print('saved', dst)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], '--no-fill' not in sys.argv, '--in2-full-tongue' in sys.argv)
