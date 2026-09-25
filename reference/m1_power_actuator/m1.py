#!/usr/bin/env python3
"""Build M1 (POWER + ACTUATOR), 46 x 50 mm, 4-layer.

Parameterised on purpose: the change-consolidation pass is still running and will move some
resistor values and may add parts. Everything that can change lives in PARTS and PLACE below,
so a value change is a one-line edit and a re-run, not a redraw. That is the whole point of
building the tooling first.

Run with KiCad's bundled python:
  /Applications/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 m1.py
"""
import pcbnew, re, os, sys, time, json
from part_metadata import set_part_metadata

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = HERE + "/kilib/rocket.pretty"
OUT = HERE + "/m1.kicad_pcb"
mm = pcbnew.FromMM
W, H = 46.0, 66.0   # 66, not 56: M1 and M2 STACK on the tie rods rather than sitting end to end,
                    # so the bay is max(66, 96) = 96 mm either way.  The extra 10 mm costs nothing
                    # in bay length, nothing at JLCPCB (both inside the 100x100 tier) and ~5 g.
                    # What it buys is the room that makes the silkscreen legible and every part
                    # hand-reworkable, which is the entire point of build 1.
_OLD = """(56 not 50: the 30.48 mm ARM
                                       # terminal plus two M3 keep-outs will not fit 50 mm of left edge)
"""
# Four M3 SCREWS into the sled, one module at a time - NOT tie-rod passages.  the two-board architecture ruling (docs/HISTORY.md §2)
# supersedes GEOMETRY §7.4 on this: "the M3 tie rods only clamp the bulkheads/sled and never pass through any PCB", because the old
# ruling was geometrically impossible (two holes 112 mm apart and coplanar with the board would
# need a straight rod to pass through 112 mm of laminate).  Consequence for this file: M1 and M2
# do NOT need a matching hole pattern, and these four positions are NOT frozen - §9 item 7 parks
# them behind the sled decision, which also blocks the connector strain-relief tie holes.
HOLE_XY = [(4.0, 4.0), (42.0, 4.0), (4.0, 62.0), (42.0, 62.0)]
HOLE_D, HOLE_KEEPOUT = 3.2, 7.0

# ---------------------------------------------------------------- parts on M1
# ref : (lcsc, footprint, value, role)
PARTS = {
 # --- battery input / load switch -------------------------------------------------
 "J1":  ("C2915641", "CONN-TH_4P-P5.08_DIBO_DB128V-5.08", "BAT+/BAT-/SW/SW", "battery terminal"),
 "D1":  ("C83849",   "SMB_L4.6-W3.6-LS5.3-BI",            "SMBJ12CA",        "bidirectional TVS"),
 "Q1":  ("C2760089", "PDFN-8_L5.6-W5.2-P1.27-LS6.1-BL",   "AON6403",         "load switch A"),
 "Q2":  ("C2760089", "PDFN-8_L5.6-W5.2-P1.27-LS6.1-BL",   "AON6403",         "load switch B"),
 "R1":  ("C25741",   "R0402", "100k", "gate-source"),
 "R2":  ("C25744",   "R0402", "10k",  "SW pull to gnd"),
 "C1":  ("C46550466","CAP-SMD_BD8.0-L8.3-W8.3-LS9.0-FD_H10.5", "470uF/25V", "RAW bulk"),
 # --- servo drive ------------------------------------------------------------------
 "J5":  ("C32713291","HDR-TH_12P-P2.54-V-M-R3-C4-S2.54", "SERVO 3x4", "servo header, column-major"),
 "C2":  ("C45783", "C0805", "22uF", "servo HF"),
 "C3":  ("C45783", "C0805", "22uF", "servo HF"),
 "R24": ("C17557", "R0805", "220R", "servo1 series"),
 "R25": ("C17557", "R0805", "220R", "servo2 series"),
 "R26": ("C17557", "R0805", "220R", "servo3 series"),
 "R27": ("C17557", "R0805", "220R", "servo4 series"),
 "R40": ("C25744", "R0402", "10k", "servo1 failsafe pulldown (M1 side)"),
 "R41": ("C25744", "R0402", "10k", "servo2 failsafe pulldown"),
 "R42": ("C25744", "R0402", "10k", "servo3 failsafe pulldown"),
 "R43": ("C25744", "R0402", "10k", "servo4 failsafe pulldown"),
 # --- pyro -------------------------------------------------------------------------
 "J4":  ("C2915642", "CONN-TH_6P-P5.08_DIBO_DB128V-5.08", "ARM/PYRO", "arming + ematch terminal"),
 "Q3":  ("C20917", "SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR", "AO3400A", "pyro1 low side"),
 "Q4":  ("C20917", "SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR", "AO3400A", "pyro2 low side"),
 "R17": ("C11702", "R0402", "1k",   "pyro1 gate pulldown, kelvin to source"),
 "R21": ("C11702", "R0402", "1k",   "pyro2 gate pulldown, kelvin to source"),
 "C35": ("C57112", "C0603", "10nF", "pyro1 gate-source, anti-Miller"),
 "C36": ("C57112", "C0603", "10nF", "pyro2 gate-source, anti-Miller"),
 # --- sense dividers: UPPER arms live on the live-rail side (M1). Lower arms are on M2,
 #     so any open sense contact makes M2 read 0 V = "no battery / not armed / no igniter".
 "R14": ("C25744", "R0402", "10k",  "ARM_SENSE upper"),
 "R18": ("C25744", "R0402", "10k",  "PYRO1_CONT upper"),
 "R22": ("C25744", "R0402", "10k",  "PYRO2_CONT upper"),
 "R44": ("C25741", "R0402", "100k", "RAW_SENSE_PWR upper"),
 # --- inter-board interface. Position count is the mechanical key: 12 vs 9 cannot cross-mate.
 "J10": ("C157943", "CONN-TH_12P-P2.00_S12B-PH-K-S-LF-SN", "J-IF1 power+drive", "to M2"),
 "J11": ("C157912", "CONN-TH_9P-P2.00_S9B-PH-K-S-LF-SN",   "J-IF2 sense+ID",    "to M2"),
 # Frozen interface spec 3.6: BOTH footprints on BOTH boards, same nets, exactly one populated.
 # PH = bench config (separable, seconds to swap a module).  These 2.54 mm rows = FLIGHT config
 # (21 wires soldered directly, zero separable contacts - DTEG Appendix B accepts through-hole
 # solder as a fabrication method, so a soldered joint is not a connector and is not bound by the
 # locking clause) AND the automated-test fixture port AND the bottom-side test point group.
 # Assembly rule from the same section: PH row and THT row must never BOTH be left empty and
 # exposed - RAW (pins 11/12) sits next to GND (pin 10) and a wire whisker shorts the battery.
 "J10T": ("-", "HDR-TH_12P-P2.54-V-M-1x12", "J-IF1 solder/test row", "duplicate of J10, DNP"),
 "J11T": ("-", "HDR-TH_9P-P2.54-V-M-1x9",   "J-IF2 solder/test row", "duplicate of J11, DNP"),

 # --- escape provisions. The iteration budget is 3 spins, so the ratio that decides success is
 #     (defects found per spin) / (defects that need a spin rather than a bodge). The denominator
 #     is the cheaper one to move: a cut point turns a respin into a scalpel cut and a wire.
 #     0805 so they can be cut with a knife and re-bridged with solder by hand.
 # C17477 = 0805W8F0000T5E, 0R 0805, UNI-ROYAL, 6,116,600 pcs, $0.0044 (lcsc.com/product-detail/
 # C17477.html, checked 2026-09-05).  These two carried C17557 by mistake, which is the 220R
 # 0805 from the same series - JLC would have fitted 220R in series with RAW and with GATE_SW.
 "R50": ("C17477", "R0805", "0R", "RAW cut link: isolates M1 from M2, inserts an ammeter"),
 "R51": ("C17477", "R0805", "0R", "GATE_SW cut link: bypass the load-switch gate network if wrong"),
 # NOT a cut link in PYRO_BUS: that path carries the full 6-12 A fire pulse, an 0805 there would
 # be a failure point in the most safety-critical net, and the arming plug already IS the break.
 # This position instead lets the load-switch gate ratio be retuned without unsoldering R2.
 "R52": ("C25744", "R0402", "DNP", "optional parallel with R2, retunes the gate divider"),
}

# Exposed-via test points. Zero BOM lines - they are just vias with mask openings - and they are
# what turns "the board is dead, go get a meter" into a five-reading walk down the power chain.
TESTPOINTS = {
 # Seven readings in the order the current actually flows; a dead board is diagnosed by finding
 # the first one that reads wrong.  Each is a bare untented via sitting INSIDE its own net's
 # copper pour - zero extra track, zero stubs hanging off a power net.  An earlier version lined
 # them up in one tidy column on the right, which read better on screen but needed seven 10-20 mm
 # feeders threaded past D1 and the gate divider through a 0.9 mm corridor.  The walk-down order
 # is carried by the silkscreen numbers instead of by geometry, and each probe now lands right
 # next to the part it indicts.
 "TP1_BAT":  (16.5, 12.0, "BAT+"),        # 1. battery present at all
 "TP2_FETS": (26.5, 18.5, "FET_S"),       # 2. Q1 is passing
 "TP3_GATE": (25.4, 16.6, "GATE_SW"),     # 3. Vgs - separates "switch off" from "gate open".
                                          #    doubles as GATE_SW's own F.Cu/B.Cu change-over via
 "TP4_RAW":  (21.0, 27.5, "RAW"),         # 4. Q2 is passing -> the whole load switch works
 # 5/6/7 were at x 8.5-9.0, which is underneath J4: the DB128V body runs from the board edge to
 # x = 10.2, so all three probe points were buried under plastic and could not be reached at all.
 # Nothing electrical was wrong with them, which is exactly why it took a silkscreen warning to
 # notice.  Moved clear of the body; their pours are extended right to follow.
 "TP5_PBUS": (11.4, 34.5, "PYRO_BUS"),    # 5. the arming plug is in
 "TP6_PY1":  (11.5, 28.3, "PYRO1_OUT"),   # 6. igniter 1 loop
 "TP7_PY2":  (11.6, 17.4, "PYRO2_OUT"),   # 7. igniter 2 loop
 "TP_GND1":  (30.0, 27.0, "GND"),         # three grounds spread across the board, so a scope
 "TP_GND2":  (31.5, 48.0, "GND"),         # ground lead is never longer than about 10 mm from
 "TP_GND3":  (12.0, 44.0, "GND"),         # whichever of the seven you are on
}# ---------------------------------------------------------------- placement (mm, board coords)
# Edge allocation, one connector per edge so no edge has to hold two:
#   aft  y=0   J1 (20.32 of 31.0 usable)      fwd  y=50  J10 (24.0 of 31.0)
#   left x=0   J4 (30.48 of 35.0, inset 5)    right x=46 J11 (18.0 of 35.0)
#   centreline x=23 : J5 (servo plugs need |x-23| <= 10.3 for stack height)
PLACE = {
 # ---- one connector per edge, every housing opening facing off-board.
 #      J10 is rot 0, not 180.  At 180 its body pointed into the board so the ribbon had to
 #      U-turn, AND its pin order ran right to left, which reversed the four servo channels
 #      against J5 and forced all four to cross.  One number fixes both; the ICD is untouched.
 "J1":  (23.0,  5.2,   0),   # aft   : battery + arm switch, 5.08 mm terminal
 "J4":  ( 5.1, 29.0,  90),   # left  : arming plug + two e-match pairs
 "J11": (39.5, 30.0,  90),   # right : sense + board ID to M2
 "J10": (23.0, 59.2,   0),   # fwd   : power + drive to M2
 # The THT rows go OUTBOARD of the PH pads, not 5 mm inboard as the spec suggests.  The two
 # footprints are mutually exclusive, so the row is allowed to live under the PH housing - the
 # housing is above the board, the row's holes go through it, and it is probed from the BACK,
 # which is what "bottom-side test point group" means.  Inboard would have displaced C1, R50 and
 # the whole servo band; outboard costs nothing at all.
 "J10T": (23.0, 62.5,   0),
 "J11T": (43.0, 30.0,  90),

 # ---- the 7.5 A path.  Q1 and Q2 stack SOURCE TO SOURCE so current runs straight down the
 #      board: J1.2 -> Q1 drain -> Q1 source == Q2 source -> Q2 drain -> RAW.  Side by side, the
 #      FET_S copper has to detour around Q1's gate pad to reach Q2; facing, it is just the
 #      1.7 mm gap between two pad rows.
 "Q1":  (21.0, 14.5,   0),   # 14.5, not 11.5: J1 is a 10.55 mm deep terminal body
 "Q2":  (21.0, 22.0, 180),
 "D1":  (28.6, 13.0,   0),   # TVS, as close to the input pads as J1's 10.5 mm body allows
 "R1":  (29.0, 18.5, 180),   # gate divider: pin 2 (FET_S / SW_TERM) faces LEFT at the FETs and
 "R52": (29.0, 20.0, 180),   # pin 1 (GATE_DRV) faces right, so GATE_DRV is one vertical line
 "R2":  (29.0, 21.5, 180),
 "R51": (29.4, 23.7, 180),   # 0805 GATE_SW cut link, at the end of that same line

 # ---- pyro low sides, each hard against its own terminal pin, so the 6-12 A pulse path is the
 #      shortest copper on the board
 "Q4":  (13.2, 15.0,   0),   # drain -> J4.6 (5.10, 16.30)
 "R21": (16.0, 16.9,   0),
 "C36": (16.0, 18.5,   0),
 "Q3":  (13.2, 26.0,   0),   # drain -> J4.4 (5.10, 26.46)
 "R17": (16.0, 25.4,   0),
 "C35": (16.7, 27.0,   0),

 # ---- sense pickoffs.  First attempt put all four next to J11 so the high-impedance divider
 #      output stayed short.  Routing killed it: the three pyro rails they tap all live on the
 #      LEFT edge, so three long sense runs had to cross the board on B.Cu right where the two
 #      pyro gate lines run vertically from J10 - five nets fighting over one layer.  Moving the
 #      three pyro taps next to their own pours turns each input into a 2 mm stub, and their
 #      outputs then share one clean three-lane corridor at y 29..31 that crosses nothing.
 #      Only R44 stays at J11: RAW is the In2 plane, so its input is a bare via either way.
 "R22": (15.5, 21.5,   0),   # taps the PYRO2_OUT pour  -> J11.4 PYRO2_CONT
 "R18": (15.5, 30.8,   0),   # taps the PYRO1_OUT pour  -> J11.3 PYRO1_CONT
 "R14": (15.5, 32.6,   0),   # taps the PYRO_BUS pour   -> J11.2 ARM_SENSE
 "R44": (35.6, 30.0,   0),   # via straight down to In2 -> J11.5 RAW_SENSE_PWR

 # ---- servo header and its local decoupling
 "J5":  (23.0, 35.5,   0),
 "C2":  (14.5, 35.5,   0),
 "C3":  (31.0, 35.5,   0),

 # ---- one column per servo, sitting directly under that servo's own J5 signal pin: series
 #      resistor, then failsafe pulldown.  Each channel is a straight vertical line a finger can
 #      follow from the M2 connector to the servo plug without ever crossing another channel.
 "R24": (19.2, 42.0,  90), "R25": (21.7, 42.0,  90),
 "R26": (24.3, 42.0,  90), "R27": (26.8, 42.0,  90),
 # The pulldowns sit BESIDE the column, not in it.  Stacked in line with the signal (which is
 # what a vertical rotation gives you) the grounded end lands between J10 and the series
 # resistor, so the servo track has to run straight across a GND pad - DRC caught it as four
 # shorts.  A shunt element taps off the side; only a series element belongs in the path.
 "R40": (20.5, 45.5,   0), "R41": (23.0, 45.5,   0),
 "R42": (25.6, 45.5,   0), "R43": (28.1, 45.5,   0),

 # ---- bulk hold-up at the load end of RAW, and the RAW cut link feeding J10.11/12
 "C1":  (13.5, 51.8,   0),   # 13.5, not 16.0: the can is 10.2 mm wide and at 16.0 its right pad
                             # sat exactly on servo 1's column, the one channel of four that had
                             # to detour.  Sliding it left clears all four onto plain F.Cu.
 "R50": (29.0, 53.0, 270),   # 29.0, not 33.0: x 32.6..45.7 is the only clear rectangle left on
                             # the board and it is worth more as the printed diagnostic legend
                             # than as a home for a 0 ohm link that can sit anywhere on RAW.
}

# ---------------------------------------------------------------- nets on M1
# Derived from NETLIST_AS_DRAWN.md restricted to M1 refs, plus the interface nets.
# Interface pin order is frozen by the ICD: J-IF1 has GND guards either side of each pyro gate.
IF1 = ["GND", "PYRO1_GATE", "GND", "PYRO2_GATE", "GND",
       "SERVO1_MCU", "SERVO2_MCU", "SERVO3_MCU", "SERVO4_MCU",
       "GND", "RAW_IF", "RAW_IF"]
# IF2 pins 6-9 are ID0..ID3 in the ICD.  M2 pulls them up internally and reads the nibble
# ID3..ID0 before the buck loads, so 0b1111 means "no module answered".  M1 must therefore
# strap some of them low, and on M1 a bit that reads 0 is not a net of its own - it is GND.
# All four were left open, which made M1 announce itself as ABSENT to the board it is bolted to.
#
# M1 rev H  =  0b0101  (ID0 open, ID1 low, ID2 open, ID3 low).
# Not 0b0000 and not 0b1111: those are the two codes a gross fault produces - a solder bridge
# across the row reads 0000, an unplugged or broken cable reads 1111.  0b0101 is Hamming
# distance 2 from both, and carries both a 1 and a 0, so a stuck bit of either polarity moves
# the code onto an unassigned value instead of onto another module's identity.
IF2 = ["GND", "ARM_SENSE", "PYRO1_CONT", "PYRO2_CONT", "RAW_SENSE_PWR",
       "ID0", "GND", "ID2", "GND"]

NETS = {
 # J1 pinout is BAT+ / BAT- / SW / SW, matching the terminal's own silkscreen value string,
 # NETLIST_AS_DRAWN.md and the frozen design table.  It was written here as SW / BAT+ / GND / SW -
 # rotated one position - when the monolithic board was split into M1 and M2.  Nothing in the PCB
 # flow can catch that: a rotated connector is electrically legal and DRC-clean, and it only
 # surfaces the first time someone lands a battery on the terminal the silkscreen names.  Wired to
 # the old copper, battery + would have gone to a switch terminal and battery - to BAT+.
 # netcheck.py now diffs this table against NETLIST_AS_DRAWN.md on every build.
 "BAT+":      ["J1.1", "D1.1", "Q1.5", "Q1.6", "Q1.7", "Q1.8", "Q1.9"],
 "GND":       ["J1.2", "D1.2", "C1.2", "C2.2", "C3.2", "Q3.2", "Q4.2",
               "R17.2", "R21.2", "C35.2", "C36.2",
               "R40.2", "R41.2", "R42.2", "R43.2",
               "J5.3", "J5.6", "J5.9", "J5.12"],
 "SW_TERM":   ["J1.3", "J1.4", "R2.2", "R52.2"],   # the two switch pins are adjacent, so
 #     the reed-switch pair is one short loop and no bridge between neighbouring terminals can
 #     reach BAT+ from a switch pin.
 "FET_S":     ["Q1.1", "Q1.2", "Q1.3", "Q2.1", "Q2.2", "Q2.3", "R1.2"],
 # R51 splits the gate node so bring-up can force the FETs on or off without trusting the
 # 100k/10k network at all - the divider ratio is one of the values still under review.
 "GATE_DRV":  ["R1.1", "R2.1", "R52.1", "R51.1"],
 "GATE_SW":   ["R51.2", "Q1.4", "Q2.4"],
 "RAW":       ["Q2.5", "Q2.6", "Q2.7", "Q2.8", "Q2.9", "C1.1", "C2.1", "C3.1",
               "J4.1", "R44.1", "J5.2", "J5.5", "J5.8", "J5.11", "R50.1"],
 "RAW_IF":    ["R50.2"],
 "RAW_SENSE_PWR": ["R44.2"],
 "PYRO_BUS":  ["J4.2", "J4.3", "J4.5", "R14.1"],
 "ARM_SENSE": ["R14.2"],
 "PYRO1_OUT": ["J4.4", "Q3.3", "R18.1"],
 "PYRO2_OUT": ["J4.6", "Q4.3", "R22.1"],
 "PYRO1_CONT":["R18.2"],
 "PYRO2_CONT":["R22.2"],
 "PYRO1_GATE":["Q3.1", "R17.1", "C35.1"],
 "PYRO2_GATE":["Q4.1", "R21.1", "C36.1"],
 "SERVO1_MCU":["R24.1", "R40.1"],
 "SERVO2_MCU":["R25.1", "R41.1"],
 "SERVO3_MCU":["R26.1", "R42.1"],
 "SERVO4_MCU":["R27.1", "R43.1"],
 "SERVO1_OUT":["R24.2", "J5.1"],
 "SERVO2_OUT":["R25.2", "J5.4"],
 "SERVO3_OUT":["R26.2", "J5.7"],
 "SERVO4_OUT":["R27.2", "J5.10"],
 "ID0": [], "ID2": [],          # left open on M1 -> M2's pull-up reads them as 1
}
for i, n in enumerate(IF1, start=1):
    NETS.setdefault(n, []).append("J10.%d" % i)
    NETS.setdefault(n, []).append("J10T.%d" % i)
for i, n in enumerate(IF2, start=1):
    NETS.setdefault(n, []).append("J11.%d" % i)
    NETS.setdefault(n, []).append("J11T.%d" % i)


def main():
    t0 = time.time()
    b = pcbnew.NewBoard(OUT)
    b.SetCopperLayerCount(4)

    # Board clearance 0.15 mm, not KiCad's default 0.2.  JLCPCB's 4-layer 1oz floor is 0.127, and
    # the USB-C receptacle's own pad-to-pad geometry is exactly 0.200 - at the default rule the
    # connector reports four clearance errors against itself for being the shape it is.  0.15
    # still leaves 18% margin on the fab limit and stops a real defect hiding behind noise.
    ds = b.GetDesignSettings()
    ds.m_MinClearance = mm(0.15)
    # kicad-cli's DRC reads the DEFAULT NETCLASS clearance, not m_MinClearance - setting only the
    # latter changes nothing and leaves the four USB-C self-clearance reports standing.
    ds.m_NetSettings.GetDefaultNetclass().SetClearance(mm(0.15))

    # board outline
    pts = [(0, 0), (W, 0), (W, H), (0, H), (0, 0)]
    for i in range(4):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(mm(pts[i][0]), mm(pts[i][1])))
        s.SetEnd(pcbnew.VECTOR2I(mm(pts[i + 1][0]), mm(pts[i + 1][1])))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); b.Add(s)

    # M3 tie-rod holes as NPTH circles on Edge_Cuts
    for (hx, hy) in HOLE_XY:
        c = pcbnew.PCB_SHAPE(b); c.SetShape(pcbnew.SHAPE_T_CIRCLE)
        c.SetCenter(pcbnew.VECTOR2I(mm(hx), mm(hy)))
        c.SetEnd(pcbnew.VECTOR2I(mm(hx + HOLE_D / 2.0), mm(hy)))
        c.SetLayer(pcbnew.Edge_Cuts); c.SetWidth(mm(0.1)); b.Add(c)

    netobj = {}
    for n in NETS:
        ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); netobj[n] = ni

    placed, fail = {}, []
    for ref, (lcsc, fpname, val, role) in PARTS.items():
        fp = pcbnew.FootprintLoad(LIB, fpname)
        if fp is None:
            fail.append((ref, fpname)); continue
        fp.SetReference(ref); fp.SetValue(val)
        set_part_metadata(fp, lcsc, val)
        x, y, rot = PLACE[ref]
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        fp.SetOrientationDegrees(rot)
        b.Add(fp); placed[ref] = fp

    # exposed test vias: 1.2 mm pad / 0.6 mm drill, un-tented so a probe tip actually lands
    tps = 0
    for name, (tx, ty, net) in TESTPOINTS.items():
        if net not in netobj:
            print("  !! test point %s references unknown net %s" % (name, net)); continue
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(mm(tx), mm(ty)))
        v.SetWidth(mm(1.2)); v.SetDrill(mm(0.6))
        v.SetNet(netobj[net])
        try:
            v.SetFrontTentingMode(pcbnew.TENTING_MODE_NONE)
            v.SetBackTentingMode(pcbnew.TENTING_MODE_NONE)
        except Exception:
            pass
        b.Add(v); tps += 1

    assigned, missing = 0, []
    for net, pins in NETS.items():
        for p in pins:
            ref, pin = p.rsplit(".", 1)
            fp = placed.get(ref)
            if fp is None:
                missing.append(p); continue
            pad = fp.FindPadByNumber(pin)
            if pad is None:
                missing.append(p); continue
            pad.SetNet(netobj[net]); assigned += 1

    pcbnew.SaveBoard(OUT, b)
    total = sum(len(v) for v in NETS.values())
    print("M1  %.0f x %.0f mm, 4 layer" % (W, H))
    print("  parts placed : %d / %d   load failures: %s" % (len(placed), len(PARTS), fail or "none"))
    print("  nets         : %d   test vias: %d" % (len(NETS), tps))
    print("  pads to nets : %d / %d   unresolved: %d %s"
          % (assigned, total, len(missing), missing[:8]))
    print("  saved        : %s (%d bytes) in %.2f s" % (OUT, os.path.getsize(OUT), time.time() - t0))
    json.dump({"parts": len(placed), "nets": len(NETS), "assigned": assigned,
               "unresolved": missing}, open(HERE + "/m1_build.json", "w"), indent=1)


if __name__ == "__main__":
    main()
