"""R11 family `power` (stage C2): the regulators' cells, the J400 / EN chain, the rails and the In2 power regions
(r11_plan.md section 4; stageC2.md sections 4-5).

Explicit tables only (D-R11-07): each run below was drafted with a scratch maze aid or by hand on the board after `pyro`
and frozen here (the build never searches). Board mm (x east, y forward from the aft edge, KiCad's y).

Cells (placement in D-R11-25 / -26):
  U9 (TPS25947, B.Cu, rotated 180): EN (pin 1) faces J400 / R165, so the EN chain U9.1 -> R81 -> C87 -> R165.2 is one
      B.Cu run with no via, R81 / C87 at U9's end (R10 D-R21-05 intent); OVLO east to R83 / R82, ILIM and dV/dt west to
      R84 / C81; IN leaves the IN bar's aft end straight through C88.1 and runs on B.Cu to J1.1 at 0.7 mm (the 2.9 A
      outer floor 0.68 mm, gate_C2.md) with no via on the path (vias to In2 BAT_IN hang off it as stubs); OUT leaves
      the OUT bar's forward end to two 0.6 / 0.3 mm vias into In2 RAW_PROTECTED and to D9.
  J400 (GH-2, F.Cu): J400.2 by one via to R165.1 / D402.1 on B.Cu (BAT_SW_RETURN; its barrel has an S-8 keep-out on
      In2 / In3); J400.1 on F.Cu to a via and R80.2 (BAT_SW_SOURCE).
  U2 (3V3 buck): L1 rotated (SW pad beside U2), SW from U2.5 under U2's body to L1.1, C5 over U2.5 / U2.6; L1.2 feeds
      U2.1 (FB) on F.Cu and the In2 3V3 region.
  U400 (5V3 buck, rotated 180) / L400 (rotated 180): SW U400.5 -> L400.1 beside it, C402 BST at U400.6, FB column
      R401 / R404 / R400 at U400.1; RAW_PROTECTED from In2 by two vias at its pins 2 / 3.
  U402 (camera switch): PORT_5V3 from L400.2 on F.Cu along the aft strip to C430 / U402.1; CAM_5V U402.6 -> C431.1 and
      by B.Cu to J9.1 / J9.2.
The In2 regions are zones (In2 is power and GND only, K-inner): see ZONES.
"""
import math

import pcbnew

NETS = ('BAT_DVDT', 'BAT_ILIM', 'BAT_OVLO', 'BAT_DAMP', 'CAM_ILIM', 'LOGIC_ILIM', 'LOGIC_SS', 'BAT_ENABLE', 'BAT_SW_SOURCE', 'BAT_SW_RETURN', 'SW_NODE', 'BST', 'PORT_SW', 'PORT_BST', 'PORT_FB', 'PORT_FB_TOP', 'PORT_LDO_FB', 'PORT_LDO_SS', 'BAT_IN', 'RAW_PROTECTED', 'VLOGIC', 'CAM_5V', 'PORT_5V3', 'PORT_4V8', '3V3A', 'VLOGIC_SENSE', 'LOGIC_SOURCE_ST', 'BAT_FAULT_N')

SV, PV, BV = (0.4, 0.2), (0.45, 0.25), (0.6, 0.3)

# (net, layer, width, points): a point is (x, y) or (ref, pad)
RUNS = (
    # ---- U9 cell (B.Cu) -------------------------------------------------------------------------------------------
    # EN: U9.1 north to R165.2, R81.1 and C87.1 tapped at U9's end of the run (no via)
    ('BAT_ENABLE', 'B', 0.15, [('U9', '1'), (12.4, 6.0), (11.83, 5.43), ('R165', '2')]),
    ('BAT_ENABLE', 'B', 0.15, [(12.4, 8.6), ('R81', '1')]),
    ('BAT_ENABLE', 'B', 0.15, [(12.4, 7.38), ('C87', '1')]),
    # OVLO east to R83.1 / R82.2; ILIM and dV/dt west
    ('BAT_OVLO', 'B', 0.15, [('U9', '2'), (13.1, 10.375), (13.4, 10.075), ('R83', '1'), ('R82', '2')]),
    ('BAT_ILIM', 'B', 0.15, [('U9', '9'), ('R84', '1')]),
    ('BAT_DVDT', 'B', 0.15, [('U9', '7'), (10.6, 11.65), ('C81', '1')]),
    # IN: the bar's aft end through C88.1, west at 0.7 then 1.0 mm to J1.1; R167 and TP80 taps
    # (C88 at the bar's aft end, the run straight through its pad; U9 IN takes no via, gate_C2.md)
    ('BAT_IN', 'B', 0.3, [('U9', '5'), ('C88', '1')]),
    ('BAT_IN', 'B', 0.7, [('C88', '1'), (11.75, 7.85), (11.05, 7.15), (8.0, 7.15), (7.2, 7.15), (5.3, 7.15), (4.5, 7.95), (4.5, 13.03),
                          (3.23, 14.3), ('J1', '1')]),
    ('BAT_IN', 'B', 0.3, [(4.5, 13.03), ('R167', '1')]),
    ('BAT_IN', 'B', 0.5, [('J1', '1'), (4.7, 16.7)]),                                 # TP80
    # BAT_IN to In2: a stub via off the trunk, D8.1's own via; C80.1 - C96.1 and R80.1 / R82.1 (B.Cu) on (18.7, 9.2)
    ('BAT_IN', 'B', 0.7, [(8.0, 7.15), (8.0, 6.2)]),
    ('BAT_IN', 'B', 0.7, [(7.2, 7.15), (7.2, 6.2)]),
    ('BAT_IN', 'F', 0.5, [(6.0, 10.8), (6.6, 10.2)]),
    ('BAT_IN', 'F', 1.0, [('C80', '1'), ('C96', '1')]),
    ('BAT_IN', 'F', 0.5, [(18.7, 9.2), (17.9, 10.0)]),
    ('BAT_IN', 'B', 0.5, [('R80', '1'), (17.4, 11.0), (16.675, 11.725), ('R82', '1')]),
    ('BAT_IN', 'B', 0.5, [(17.4, 9.2), (18.7, 9.2)]),
    ('BAT_IN', 'B', 0.3, [(18.7, 9.2), (18.7, 8.45)]),
    ('BAT_IN', 'F', 1.0, [('C89', '1'), (17.3, 15.475), ('C95', '1')]),
    # OUT: the bar's forward end to the two In2 vias and D9.1
    ('RAW_PROTECTED', 'B', 0.3, [('U9', '6'), (11.25, 12.1)]),
    ('RAW_PROTECTED', 'B', 0.7, [(11.25, 12.1), (11.25, 12.85)]),
    ('RAW_PROTECTED', 'B', 0.7, [(10.5, 12.85), (11.25, 12.85), (12.0, 12.85)]),
    ('RAW_PROTECTED', 'B', 0.7, [(10.5, 12.85), (9.6, 13.75), (9.6, 14.8)]),
    # C82.1 / R92.1 to their In2 via
    ('RAW_PROTECTED', 'B', 0.5, [('C82', '1'), (17.5, 17.1), (18.3, 17.9)]),
    ('RAW_PROTECTED', 'B', 0.5, [(16.0, 17.1), (16.0, 18.0), (15.375, 18.625), ('R92', '1')]),
    # the input damper: R166 (0.36 ohm) in series with C89 / C95 (22 uF), F.Cu north of R166's GND pad
    ('BAT_DAMP', 'F', 0.5, [('R166', '1'), (8.85, 11.95), (15.425, 11.95), ('C89', '2')]),
    ('BAT_DAMP', 'F', 0.5, [('C89', '2'), ('C95', '2')]),
    # ---- J400 ------------------------------------------------------------------------------------------------------
    ('BAT_SW_RETURN', 'F', 0.2, [('J400', '2'), (9.7, 6.075)]),
    ('BAT_SW_RETURN', 'B', 0.2, [(9.7, 6.075), (9.525, 5.9), ('D402', '1'), ('R165', '1')]),
    ('BAT_SW_SOURCE', 'F', 0.15, [('J400', '1'), (12.155, 5.93), (15.73, 5.93), (16.2, 6.4)]),
    ('BAT_SW_SOURCE', 'B', 0.15, [(16.2, 6.4), (16.2, 7.6), (16.77, 8.17), ('R80', '2')]),
    # ---- U2 (3V3 buck) ---------------------------------------------------------------------------------------------
    ('SW_NODE', 'F', 0.5, [('U2', '5'), (23.6, 35.4), (23.2, 35.8), (20.6, 35.8)]),
    ('SW_NODE', 'F', 0.2, [('U2', '5'), (23.6, 33.48), ('C5', '1')]),
    ('BST', 'F', 0.2, [('U2', '6'), (22.65, 33.37), ('C5', '2')]),
    # ---- U400 (5V3 buck) -------------------------------------------------------------------------------------------
    ('PORT_SW', 'F', 0.7, [('U400', '5'), (36.4, 9.6)]),
    ('PORT_SW', 'F', 0.3, [(36.6, 11.0), (36.6, 12.32), (37.0, 12.72), ('C402', '2')]),
    ('PORT_BST', 'F', 0.2, [('U400', '6'), (38.9, 11.68), ('C402', '1')]),
    ('PORT_FB', 'F', 0.15, [('U400', '1'), (43.17, 10.55), ('R404', '2')]),
    ('PORT_FB', 'F', 0.15, [('R401', '1'), ('R404', '2')]),
    ('PORT_FB_TOP', 'F', 0.15, [('R404', '1'), ('R400', '2')]),
    ('RAW_PROTECTED', 'F', 0.5, [('U400', '3'), (42.3, 8.65)]),
    ('RAW_PROTECTED', 'F', 0.5, [('U400', '2'), (42.3, 9.6)]),
    # ---- U402 (camera switch) --------------------------------------------------------------------------------------
    ('CAM_ILIM', 'F', 0.15, [('U402', '5'), (24.62, 9.4), ('R430', '1')]),
    # PORT_5V3: U402.1 through C430.1, then north and east along the aft strip to L400.2 and its two In2 vias
    ('PORT_5V3', 'F', 0.4, [('U402', '1'), ('C430', '1'), (19.38, 7.95), (20.13, 7.2), (30.45, 7.2), (31.65, 8.4),
                            ('L400', '2'), (31.65, 12.0), (31.65, 12.8)]),
    # CAM_5V: U402.6 -> C431.1 on F.Cu, two vias, B.Cu east to two vias under J9.2 / J9.1
    ('CAM_5V', 'F', 0.4, [('U402', '6'), (26.1, 8.45), ('C431', '1')]),
    ('CAM_5V', 'F', 0.4, [(26.1, 8.45), (26.1, 7.85)]),
    ('CAM_5V', 'F', 0.4, [(26.1, 8.45), (26.5, 8.45), (26.9, 8.05), (26.9, 7.85)]),
    ('CAM_5V', 'B', 0.4, [(26.1, 7.85), (26.9, 7.85), (27.75, 7.0), (34.675, 7.0), (35.925, 7.0)]),
    ('CAM_5V', 'F', 0.4, [(34.675, 7.0), ('J9', '2')]),
    ('CAM_5V', 'F', 0.4, [(35.925, 7.0), ('J9', '1')]),
    # RAW_PROTECTED to U400's input capacitors C400 / C401 (F.Cu) from an In2 via in the aft band
    ('RAW_PROTECTED', 'F', 0.5, [(30.05, 8.2), (30.05, 13.6), (30.05, 14.4)]),
    ('RAW_PROTECTED', 'F', 0.5, [(30.05, 13.6), (34.5, 13.6), (35.2, 14.3)]),
    # ---- U401 (PORT_4V8 LDO) ---------------------------------------------------------------------------------------
    ('PORT_5V3', 'F', 0.25, [('U401', '9'), ('U401', '10')]),
    ('PORT_5V3', 'F', 0.4, [('U401', '10'), (43.05, 21.0), (43.75, 21.0), (44.55, 21.0)]),
    ('PORT_5V3', 'F', 0.2, [('U401', '7'), (43.4, 22.9), (43.75, 23.25)]),
    ('PORT_5V3', 'F', 0.2, [(43.75, 23.25), (44.1, 23.6), (44.55, 23.6)]),
    ('PORT_LDO_SS', 'F', 0.15, [('U401', '8'), ('C408', '1')]),
    ('PORT_LDO_FB', 'F', 0.15, [('U401', '3'), (39.35, 22.4), ('R402', '2')]),
    ('PORT_LDO_FB', 'F', 0.15, [('R402', '2'), ('R403', '1')]),
    ('PORT_4V8', 'F', 0.4, [('U401', '1'), (39.6, 21.4), ('R402', '1')]),
    ('PORT_4V8', 'F', 0.4, [('C406', '1'), (40.0, 20.35), (39.6, 20.75), (39.6, 21.4)]),
    ('PORT_4V8', 'F', 0.4, [(39.6, 21.4), (39.6, 21.9), ('U401', '2')]),              # the second via, U401.2
    ('PORT_4V8', 'F', 0.4, [(39.6, 20.75), (39.2, 20.35), (35.9, 20.35), (31.25, 20.35), (30.4, 21.2), ('C407', '1')]),
    # ---- U2 output, VLOGIC, U11 ------------------------------------------------------------------------------------
    ('3V3', 'F', 0.5, [('L1', '2'), (17.0, 38.1), (22.2, 38.1), (22.65, 37.65), ('U2', '1')]),
    ('3V3', 'F', 0.5, [(19.4, 38.1), (19.4, 38.6)]),
    ('3V3', 'F', 0.5, [(19.4, 38.1), (19.9, 38.6), (20.2, 38.6)]),
    # C84 hold-up: C84.1 north and east on F.Cu (1.05 mm from TP122) to two vias west of U11.1, B.Cu to U11.1 / U11.8
    ('VLOGIC', 'F', 0.4, [('C84', '1'), (9.95, 35.1), (13.65, 35.1), (14.2, 35.65), (14.2, 36.45)]),
    ('VLOGIC', 'B', 0.4, [(14.2, 35.65), ('U11', '1'), ('U11', '8')]),
    ('VLOGIC', 'B', 0.4, [(14.2, 36.45), (14.85, 35.8)]),
    # the trunk: from the vias east on F.Cu under C84's and L1's gap, y 39.35 east, C99.1 (F.Cu), U2.3 / U2.2
    ('VLOGIC', 'F', 0.4, [(14.2, 36.45), (15.2, 36.45), (15.6, 36.85), (15.6, 38.95), (16.0, 39.35), (24.58, 39.35),
                          (24.98, 38.95), ('C99', '1'), (24.55, 37.92), ('U2', '3'), ('U2', '2')]),
    ('VLOGIC', 'F', 0.4, [(17.0, 39.35), ('C6', '1')]),
    ('VLOGIC', 'F', 0.4, [(21.4, 39.35), ('C7', '1')]),
    ('VLOGIC', 'F', 0.3, [('C6', '1'), (17.0, 41.25), (17.6, 41.85)]),
    ('VLOGIC', 'B', 0.3, [(17.6, 41.85), (18.0, 42.25), ('TP83', '1')]),
    # R60.1 (PA6's VLOGIC sense divider top, B.Cu) by two vias south of U2.2 / U2.3
    ('VLOGIC', 'F', 0.3, [('U2', '2'), (23.6, 38.45), (24.3, 38.45)]),
    ('VLOGIC', 'B', 0.3, [(23.6, 38.45), (24.3, 38.45), (24.3, 36.2), (24.9, 35.6)]),
    # U11's RAW_PROTECTED to C97.1 and its In2 via; TP81's In2 via
    ('RAW_PROTECTED', 'B', 0.4, [('U11', '2'), (13.9, 34.95), (13.4, 35.45), (12.6, 35.45)]),
    ('RAW_PROTECTED', 'B', 0.4, [('C97', '1'), (11.7, 35.775)]),
    ('RAW_PROTECTED', 'B', 0.4, [('TP81', '1'), (7.4, 35.5)]),
    # ---- 3V3A from R164.2 to H1 (VDDA) on B.Cu; 3V3 from D120.3 and R164.1 to K1's via on B.Cu (D-R11-27) --------
    ('3V3A', 'B', 0.3, [(20.0, 30.4), (17.225, 30.4)]),
    ('3V3', 'B', 0.2, [('D120', '3'), (9.4, 24.6), (10.6, 24.6), (11.0, 25.0), (11.0, 31.3), (11.4, 31.7), (15.575, 31.7)]),
    ('3V3', 'B', 0.3, [('R164', '1'), (15.575, 31.7), (19.7, 31.7), (20.0, 32.0)]),
    ('3V3A', 'B', 0.3, [(18.95, 30.4), (18.95, 31.1)]),
    # ---- pad taps to the In2 regions (O-C2-3): pad -> its own via (drafted with the scratch via finder) --------------
    ('3V3', 'B', 0.2, [('R12', '2'), (12.45, 38.57), (12.45, 40.67), ('R13', '2')]),
    ('3V3', 'B', 0.2, [('R91', '1'), (15.37, 41.4)]),
    ('3V3', 'B', 0.2, [('R91', '1'), (14.82, 40.9)]),
    ('3V3', 'B', 0.2, [('R11', '2'), (19.8, 18.9), (20.75, 17.95), (20.75, 16.6)]),
    ('3V3', 'B', 0.2, [('U12', '3'), (23.3, 14.85)]),                         # D-R11-49: U12 rotated 180
    ('3V3', 'F', 0.3, [('C461', '1'), (23.25, 15.6)]),
    ('3V3', 'F', 0.2, [('R432', '2'), (24.2, 11.77), (24.2, 11.2)]),
    ('3V3', 'B', 0.2, [('D121', '5'), (24.8, 10.6), (24.2, 11.2)]),
    ('3V3', 'B', 0.2, [('C90', '1'), (24.296, 16.516)]),
    ('3V3', 'B', 0.2, [('C100', '1'), (27.58, 16.5)]),
    ('3V3', 'B', 0.2, [('J430', '4'), (37.405, 13.95), (37.105, 14.25)]),          # D-R11-33: at the pin, so the SD runs pass south
    ('3V3', 'B', 0.2, [(24.8, 28.0), (25.45, 27.35), (25.45, 26.8), ('C16', '1')]),
    ('3V3', 'B', 0.2, [(25.45, 26.8), (25.45, 25.2), ('C14', '1')]),
    ('3V3', 'F', 0.2, [('U3', '8'), (30.85, 26.97)]),
    ('3V3', 'B', 0.2, [(30.85, 26.97), (30.38, 27.44), ('C29', '1')]),
    ('3V3', 'B', 0.2, [('R10', '2'), (31.23, 30.05)]),
    ('3V3', 'B', 0.2, [('C23', '1'), (24.9, 33.05)]),
    ('3V3', 'F', 0.3, [('C8', '1'), (28.1, 36.2)]),
    ('3V3', 'F', 0.3, [('C9', '1'), (25.8, 39.8), (26.4, 39.2)]),
    # D-R11-33: the microSD pull-ups' 3V3 pads, one F.Cu column bus west of the resistors to one via south of R464
    ('3V3', 'F', 0.2, [('R463', '2'), ('R462', '2'), ('R461', '2'), ('R460', '2'), ('R464', '2'), (28.27, 19.25)]),
    ('3V3', 'F', 0.2, [(31.63, 40.4), (31.63, 41.0)]),            # from inside J2.1, south of J2's keep-out strip
    ('3V3', 'B', 0.2, [('C460', '1'), (35.5, 42.82)]),
    ('3V3', 'F', 0.3, [('LS120', '1'), (38.15, 40.05)]),
    ('3V3', 'B', 0.2, [('D123', '1'), (39.83, 41.2)]),
    ('3V3A', 'B', 0.2, [(7.12, 38.9), (7.12, 38.17), (8.37, 38.17), (8.37, 38.9)]),     # U5.1 / U5.2 land pairs
    ('3V3A', 'B', 0.2, [(8.37, 38.17), (8.94, 37.6)]),
    ('3V3A', 'B', 0.2, [('C32', '1'), (11.1, 37.2)]),
    ('3V3A', 'B', 0.2, [('C22', '1'), (15.05, 32.6)]),
    ('3V3A', 'B', 0.2, [('C10', '1'), (19.1, 34.0)]),
    ('3V3A', 'B', 0.2, [('C11', '1'), (19.0, 36.2)]),
    ('PORT_5V3', 'F', 0.4, [('C404', '1'), (31.75, 18.9)]),
    ('PORT_5V3', 'F', 0.4, [('C405', '1'), (36.5, 18.9)]),
    ('PORT_5V3', 'F', 0.4, [('C403', '1'), (41.5, 15.4)]),
    ('PORT_5V3', 'F', 0.2, [('R400', '1'), (43.3, 13.75)]),
    ('PORT_5V3', 'F', 0.2, [(43.0, 13.75), (43.75, 13.75)]),
    ('PORT_4V8', 'F', 0.4, [(35.9, 20.35), ('R405', '1')]),
    ('PORT_4V8', 'F', 0.4, [('J420', '1'), (10.525, 46.1)]),
    ('PORT_4V8', 'F', 0.4, [('J410', '1'), (21.125, 46.1)]),
    ('PORT_4V8', 'F', 0.4, [('J440', '1'), (31.725, 46.1)]),
    ('PORT_4V8', 'B', 0.3, [('C410', '1'), (25.7, 46.82)]),
    ('PORT_4V8', 'B', 0.3, [('C411', '1'), (20.7, 47.4)]),
    ('PORT_4V8', 'B', 0.3, [('C420', '1'), (15.1, 46.82)]),
    ('PORT_4V8', 'B', 0.3, [('C421', '1'), (10.1, 47.4)]),
    ('PORT_4V8', 'B', 0.3, [('C444', '1'), (36.3, 46.82)]),
    ('PORT_4V8', 'B', 0.3, [('C445', '1'), (31.3, 47.4)]),
    # CAM_5V to C91.1 and U13.1 (B.Cu) and R104.1 (F.Cu)
    ('CAM_5V', 'B', 0.4, [(26.9, 7.85), (26.9, 9.8), (26.0, 10.7)]),
    # D-R11-43: U13 rotated 180, CAM_5V enters U13.1 from C91.1 along the north side of U13 (the corridor east of U12.6
    # is the escape plan's)
    ('CAM_5V', 'B', 0.3, [('C91', '1'), (25.625, 12.0), (26.075, 12.45), (27.6, 12.45), (28.4, 13.25), ('U13', '1')]),
    ('CAM_5V', 'F', 0.3, [('C431', '1'), (26.1, 11.6), (26.9, 12.4), ('R104', '1')]),
    # U11 (TPS2121) ILIM to R86, soft-start to C85
    ('LOGIC_ILIM', 'B', 0.15, [('U11', '10'), (15.85, 36.65), (15.85, 39.2), (15.5, 39.55)]),
    ('LOGIC_SS', 'B', 0.15, [('U11', '11'), (15.55, 37.45), (15.25, 37.75)]),
)

VIAS = (
    ('BAT_SW_RETURN', (9.7, 6.075), SV),
    ('BAT_SW_SOURCE', (16.2, 6.4), SV),
    ('BAT_IN', (8.0, 6.2), BV), ('BAT_IN', (7.2, 6.2), BV), ('BAT_IN', (18.7, 8.45), PV), ('BAT_IN', (6.0, 10.8), BV),
    ('BAT_IN', (18.7, 9.2), BV),
    ('BAT_IN', (17.3, 15.475), PV),
    ('RAW_PROTECTED', (10.5, 12.85), BV), ('RAW_PROTECTED', (12.0, 12.85), BV),
    ('RAW_PROTECTED', (18.3, 17.9), PV),
    ('RAW_PROTECTED', (42.3, 8.65), BV), ('RAW_PROTECTED', (42.3, 9.6), BV),
    ('RAW_PROTECTED', (30.05, 8.2), BV), ('RAW_PROTECTED', (11.7, 35.775), BV), ('RAW_PROTECTED', (7.4, 35.5), BV),
    ('PORT_5V3', (31.65, 12.0), BV), ('PORT_5V3', (31.65, 12.8), BV),
    ('PORT_5V3', (43.75, 21.0), BV), ('PORT_5V3', (44.55, 21.0), BV),
    ('PORT_5V3', (43.75, 23.25), BV), ('PORT_5V3', (44.55, 23.6), BV),
    ('PORT_4V8', (39.6, 20.75), BV), ('PORT_4V8', (39.6, 21.9), BV),
    ('CAM_5V', (26.1, 7.85), BV), ('CAM_5V', (26.9, 7.85), BV), ('CAM_5V', (34.675, 7.0), BV),
    ('CAM_5V', (35.925, 7.0), BV),
    ('3V3', (19.4, 38.6), BV), ('3V3', (20.2, 38.6), BV),
    ('VLOGIC', (14.2, 35.65), BV), ('VLOGIC', (14.2, 36.45), BV),
    ('VLOGIC', (23.6, 38.45), PV), ('VLOGIC', (24.3, 38.45), PV),
    ('VLOGIC', (17.6, 41.85), PV),
    ('3V3A', (18.95, 31.1), PV),
    ('3V3', (12.45, 40.67), PV), ('3V3', (15.37, 41.4), PV), ('3V3', (14.82, 40.9), PV), ('3V3', (20.75, 16.6), PV), ('3V3', (23.3, 14.85), PV),
    ('3V3', (23.25, 15.6), PV), ('3V3', (24.2, 11.2), PV), ('3V3', (24.296, 16.516), PV),
    ('3V3', (27.58, 16.5), PV), ('3V3', (37.105, 14.25), PV), ('3V3', (30.85, 26.97), PV), ('3V3', (31.23, 30.05), PV),
    ('3V3', (24.9, 33.05), PV), ('3V3', (28.1, 36.2), PV), ('3V3', (26.4, 39.2), PV), ('3V3', (28.27, 19.25), PV),
    ('3V3', (31.63, 41.0), PV), ('3V3', (35.5, 42.82), PV), ('3V3', (38.15, 40.05), PV), ('3V3', (39.83, 41.2), PV),
    ('3V3A', (8.94, 37.6), PV), ('3V3A', (11.1, 37.2), PV), ('3V3A', (15.05, 32.6), PV), ('3V3A', (19.1, 34.0), PV),
    ('3V3A', (19.0, 36.2), PV),
    ('PORT_5V3', (31.75, 18.9), BV), ('PORT_5V3', (36.5, 18.9), BV), ('PORT_5V3', (41.5, 15.4), BV),
    ('PORT_5V3', (43.0, 13.75), PV), ('PORT_5V3', (43.75, 13.75), PV),
    ('PORT_4V8', (10.525, 46.1), BV), ('PORT_4V8', (21.125, 46.1), BV), ('PORT_4V8', (31.725, 46.1), BV),
    ('PORT_4V8', (25.7, 46.82), PV), ('PORT_4V8', (20.7, 47.4), PV), ('PORT_4V8', (15.1, 46.82), PV),
    ('PORT_4V8', (10.1, 47.4), PV), ('PORT_4V8', (36.3, 46.82), PV), ('PORT_4V8', (31.3, 47.4), PV),
)

# S-8 keep-outs (R10 BARREL_NETS; GND exempt for these nets, so In2 / In3 only): no inner track or fill within 1.0 mm
# of the barrel's 0.4 mm ring (radius 0.2 + 1.0, held at 1.3 as the pyro family's ACT_GATE barrels)
S8_BARRELS = (('BAT_SW_RETURN', (9.7, 6.075)),)


# In2 power regions (stageC2.md section 5, D-R11-27): a 3V3 base fill over the whole board at priority 0 and the other
# rails' polygons at priority 1, so 3V3 takes every In2 area no other rail claims (island removal: always). Clearance
# 0.2 mm, minimum width 0.2 mm, solid connection (only vias and plated barrels reach In2).
ZONES = (
    ('3V3', 0, ((0.3, 0.3), (45.7, 0.3), (45.7, 49.7), (0.3, 49.7))),
    ('BAT_IN', 1, ((0.3, 0.3), (19.0, 0.3), (19.0, 16.35), (14.85, 16.35), (14.85, 12.3), (0.3, 12.3))),
    ('RAW_PROTECTED', 1, ((0.3, 12.5), (14.65, 12.5), (14.65, 16.55), (19.2, 16.55), (19.2, 0.3), (45.7, 0.3),
                          (45.7, 9.95), (20.6, 9.95), (20.6, 18.6), (14.1, 18.6), (14.1, 19.8), (9.8, 19.8),
                          (9.8, 34.6), (12.35, 34.6), (12.35, 36.45), (0.3, 36.45))),
    ('PORT_5V3', 1, ((29.4, 10.3), (45.7, 10.3), (45.7, 24.6), (43.45, 24.6), (43.45, 20.45), (38.95, 20.45),
                     (38.95, 12.45), (36.85, 12.45), (36.85, 20.55), (29.4, 20.55))),
    ('PORT_4V8', 1, ((39.1, 20.65), (43.25, 20.65), (43.25, 24.8), (45.7, 24.8), (45.7, 49.7), (0.3, 49.7),
                     (0.3, 43.95), (40.7, 43.95), (40.7, 24.8), (39.1, 24.8))),
    # 3V3A: west column (x 14.3-19.15, west of NRST's In3 run x 19.6, which lies under 3V3), the arm west to C32 / U5,
    # and a block over U4 that covers SCK's whole In3 run (x 24.6, y 18.25-23.6) and C30 / C31's via, so SCK's chain
    # sees one In2 net, 3V3A (K-region, O-C1-3; D-R11-27)
    ('3V3A', 1, ((6.9, 36.65), (14.3, 36.65), (14.3, 20.0), (20.8, 20.0), (20.8, 17.0), (27.6, 17.0), (27.6, 22.8),
                 (26.0, 22.8), (26.0, 23.9), (24.0, 23.9), (24.0, 22.8), (19.15, 22.8), (19.15, 37.85), (6.9, 37.85))),
)


def zone(board, net, priority, pts):
    z = pcbnew.ZONE(board)
    z.SetLayer(pcbnew.In2_Cu)
    z.SetNet(board.FindNet(net))
    z.SetAssignedPriority(priority)
    # D-R11-46: the 3V3 base fill keeps 0.12 mm clearance and 0.1 mm minimum width, so it stays continuous between two
    # foreign vias 0.8 mm apart under the ball field (0.8 - 2 x (0.2 + 0.12) = 0.16 mm) and every In3 line there keeps
    # one In2 region (check_r11 K-region); the power regions keep 0.2 / 0.2
    base = net == '3V3' and priority == 0
    z.SetLocalClearance(pcbnew.FromMM(0.12 if base else 0.2))
    z.SetMinThickness(pcbnew.FromMM(0.1 if base else 0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName(f'In2_{net}')
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    board.Add(z)


def keepout(board, centre, radius, layers, name):
    z = pcbnew.ZONE(board)
    ls = pcbnew.LSET()
    for lay in layers:
        ls.AddLayer(lay)
    z.SetLayerSet(ls)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    n = 16
    r = radius / math.cos(math.pi / n)
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        ol.Append(pcbnew.FromMM(centre[0] + r * math.cos(a)), pcbnew.FromMM(centre[1] + r * math.sin(a)))
    board.Add(z)


# Stage C2c (O-C2-4, D-R11-36): VLOGIC_SENSE (PA6) leaves U1.J3 down the F.Cu lane x 21.6, one via south of the field,
# B.Cu diagonally to R60.2 and the divider's R61.1 / C60.1. LOGIC_SOURCE_ST: only U11.9 to R91.2 (its pull-up) here; the
# MCU side and BAT_FAULT_N are the escape plan's (r11_escape.py, stageC1b.md, D-R11-44).
SIGNAL_RUNS = (
    ('VLOGIC_SENSE', 'F', [('U1', 'J3'), (21.6, 31.2), (21.6, 32.6)]),
    ('VLOGIC_SENSE', 'B', [(21.6, 32.6), (22.5, 32.6), (23.75, 33.85), (23.75, 34.75), (24.15, 35.15), (25.58, 35.15),
                           ('R60', '2')]),
    ('VLOGIC_SENSE', 'B', [('R60', '2'), (26.03, 35.84), ('R61', '1'), (25.17, 37.8)]),          # ends inside C60.1
    ('LOGIC_SOURCE_ST', 'B', [('U11', '9'), (17.2, 37.1), (17.2, 39.8), (16.35, 40.65)]),     # ends inside R91.2
)
SIGNAL_VIAS = (('VLOGIC_SENSE', (21.6, 32.6)),)


def draw(d):
    import r11_escape
    r11_escape.draw(d, 'power')
    for net, layer, pts in SIGNAL_RUNS:
        d.track(net, layer, 0.1, [d.pad(p[0], p[1], net=net) if isinstance(p[0], str) else p for p in pts])
    for net, at in SIGNAL_VIAS:
        d.via(net, at, SV)
    for net, layer, width, pts in RUNS:
        d.track(net, layer, width, [d.pad(p[0], p[1], net=net) if isinstance(p[0], str) else p for p in pts])
    for net, at, size in VIAS:
        d.via(net, at, size)
    if not d.dry:
        for k, (net, at) in enumerate(S8_BARRELS):
            keepout(d.board, at, 1.3, (pcbnew.In2_Cu, pcbnew.In3_Cu), f'S8_{net}_{k}')
        # D-R11-49: R89.1's 3V3 via sits in the In2 3V3A block; without a fill keep-out the 3V3 base fills a 0.18 mm^2
        # sliver inside 3V3A's clearance ring around it (a second 3V3 piece, K-plane, Measured)
        keepout(d.board, (18.57, 20.55), 0.5, (pcbnew.In2_Cu,), 'R89_3V3_VIA')
        for net, prio, pts in ZONES:
            zone(d.board, net, prio, pts)
