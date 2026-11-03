#!/usr/bin/env python3
"""R10 native-CAD contract (M3-ASSY-R10): rule-based checks, modelled on tools/check_r9.py, for the leaner R10 board
(r10_plan.md sections 4 and 6-8; docs/R10_VALIDATION.md R1-07, R1-m10).

usage: <KiCad python3> -I tools/check_r10.py [board.kicad_pcb] [--report out.json] [--fit FIT.json]
       [--plate PLATE.json] [--seed SEED.json] [--only S-1,M-1] [--stage functional|placement|full]
       [--bom BOM.csv] [--cpl CPL.csv]
exit 0 = every selected rule holds

Run with KiCad Python on a filled board. tools/check.sh runs it after fit_check --profile r10 (--fit) and
the optional plate_model.py --profile r10 (--plate) diagnostic. Without --fit the fit report is computed here.
Plate frequency is informational. Bare-contact clearance is checked only by the full tools/check.sh DRC gate.
--seed is accepted for check_r9's command shape only: R10 has no rule H (owner decision, r10_plan section 2
item 1), so no R10 rule reads it. --stage selects rule groups for build steps (functional, placement); only the full
stage (the default) is the gate. --bom / --cpl, when given, are also checked for the required-fitted safety parts.

Dropped from R9 (r10_plan section 2 item 1 and O1 / O2): every pyro-specific spacing rule (P-0 rules A-H / A2, P-1 /
P-2 PYRO_BLOCK, P-3 purity, P-4 rule H, P-5 bridge table, P-6 bare gate pads, P-7 gate guard, P-10 coat region by the
block, the strict pad rules, K-power-pyro's D18 / D85 / D19 spacing) and every RF rule (R-1..R-13, the U30 / U31 / J30 /
J31 checks, GCPW). Pyro copper uses the board default clearance, which KiCad DRC enforces.

Safety (AGENTS.md section 2, F8; single screw switch owner decision 2026-10-28):
  S-1   canonical pyro bus RAW_ACT: J124 and PYRO1_BUS are absent; R134.2 and R132.1 are on RAW_ACT behind Q121.
        Only named parts touch pyro / sense copper; no other part or copper bypasses R134 or the sense-divider tops
        (geometric copper connectivity includes tracks, arcs, vias, fill, drawings and copper text, any net or none).
  S-2   pyro feed: Q120 / Q121 are the back-to-back load switch BAT_IN -> ACT_FET_S -> RAW_ACT with gates on
        ACT_GATE; RAW_ACT is reached from no supply (BAT_IN, RAW_PROTECTED, ACT_FET_S, VLOGIC, ...) except through
        Q121; the downstream pyro / sense network has only its named rail ties and its copper touches no foreign pad
  S-3   gate networks defined off: Q124 (pyro) gate has a pull-down to its source, a gate-source capacitor and a series
        resistor from a U1 pin; Q120 / Q121 (P-FET load switch) gate has a gate-source resistor and capacitor and a
        series resistor from its driver; PC1 independently enables Q122 through R122, with R123 to GND
  S-4   R1-07 required fitted: every safety part (and every R10 contract part) is on the board, not DNP, not excluded
        from BOM or position files, not board-only, on the board and in the schematic; also in --bom / --cpl if given.
        Every production BOM designator's LCSC, canonical Manufacturer Part and footprint match its native fitted part.
        R19-GATE-02: every fitted resistor's and capacitor's Manufacturer Part decodes (mpn_decode: UNI-ROYAL, FOJAN,
        Yageo RC / RT / CC, Bourns CRM, Vishay MCT, Samsung CL, Murata GRM / GCJ, Fenghua) to its Value field (value,
        and any tolerance, voltage or dielectric the Value states); a part of another family is listed with its reason
  S-5   single screw switch: J400 contacts lead only through their 470 k resistors to BAT_IN and U9 EN; no part or
        copper bypasses the contact; obsolete ARM-terminal and fuse legends are rejected by K-legends
  S-6   external ports: no part (the MCU U1 excepted) has pads on both a port net (GPS_ / RADIO_ / CAM_ / PORT_ /
        AUX_) and a pyro / arming net (PYRO1_ / ARM1_ / ACT_ / RAW_ACT* and, R20-SAF-02, the switch / enable chain
        BAT_ENABLE / BAT_SW_*); port copper >= the board default clearance from pyro / arming copper on the same
        layer (no shared copper item)
  S-7   J122: exactly five terminal contacts, 1-4 on SERVO1-4_OUT and 5 on signal-reference GND; motor power and
        return stay in the harness (O3 / O6 and the screw-terminal amendment)
  S-8   R3-SAF-01 / R18-SAF-01: on In1 and In2 no track or zone fill of another net lies within 1.0 mm of a plated
        barrel (via or plated hole wall) of a BARREL_NETS net (11: RAW_ACT, the PYRO1 IGN / OUT / GATE / GATE_N nodes,
        the load-switch gate drive ACT_GATE / ACT_DRV / ACT_EN / ACT_EN_MCU, BAT_ENABLE, BAT_SW_RETURN), nor of the
        inner ring such a barrel keeps on that layer (D-R20-05, R20-SAF-05); GND counts only for the BARREL_GND_HAZARD
        nets ACT_GATE, ACT_DRV and PYRO1_OUT (D-R19-01)
  S-9   R3-GATE-07 / AUD-6: current-path copper >= 0.5 mm on fire-only RAW_ACT / PYRO1_IGN / PYRO1_OUT,
        >= 0.5 mm on ACT_FET_S and >= 1.0 mm on BAT_IN. FIRE_TERMINALS prunes dead-end branches such as sense taps; only the
        named, measured FIRE_NARROW entries are excepted
Mechanical and placement (kept from check_r9 where they still apply, read from the board):
  LC-1  local clearance overrides >= the applicable floor: J2 0.508 mm, TP 1.0 mm, all others 0.15 mm
  M-1   outline one rectangle from (0, 0), 46 mm wide, length read from the board <= 120 mm (P1), Edge.Cuts circles
        3.2 mm
  M-3   five M3 support circles only, centred within 0.01 mm on P1 / P2's (4, 4), (42, 4), (4, 44.3), (3.7, 86) and
        (42, 86) mm (R18-GATE-07); the former J122 plug tie holes are absent
  M-5   fit_check --profile r10 clean and bound to this board
  M-6   bottom parts SMD only, >= 1.5 mm from foreign through-hole pads, >= 3.5 mm from an M3 support centre
  M-7   U4 on the bottom at R9's rotation 180 (roll = -gyro_Y, R9_DECISIONS D-S7-06), actual lever arm -6.0 +/-0.05 mm;
        no via or fill under U4 / U5 on their side (check_r9.m7); the axis map is read from the board and reported
  P-11  All eight DB125 terminals (D-R19-14 adds J440, west) face outward with >= 4.95 mm wire room; J1 / J121 enter from -x (owner, r10_plan 2 item 2; J1's wires leave the same west face, R3-MEC-02);
        the entry direction is read from the footprint
        description ("wire entry +y"), else DB128's local -y. Wire room to the bore wall: R8 / R9's 6.25 mm is R8's
        measured value (a non-regression floor, not a derived need). Owner OQ-1, 2026-10-28: R10's accepted floor is
        4.95 mm with 16-22 AWG in DB125 terminals, pending physical fit qualification
  F9-1  owner OQ-2, 2026-10-28: the R10 reverse hot-plug model must pass. Its extracted copper/parts, source curves,
        solver, complete corner set, numerical limits and convergence are checked; stale or failing evidence fails.
        The old part-distance premise is not used. This remains a simulation inference, not a bench result
  F9-2  GAP-2: C82 and D9 have short actual B.Cu OUT connections and local saved-copper GND paths to U9;
        endpoints, layers and loop lengths are reported. Engineering layout bounds, not electrical qualification
  T-1   panel tabs (D-R2-13): R9 barred the aft edge because the SMA jacks overhung it; R10 has no jack, and its east
        edge's aft third carries the three GH ports. Each end third must be held on both sides: a legal 5 mm tab on the
        west edge in the aft and in the forward third, and on the east side in each end third either a legal east-edge
        tab or a legal tab on that end's short edge within its east third (tools/tab_windows.py's clearances)
Kept contract and copper rules:
  K-contract   R10 netlist contract: pin map, connectors, port power / UART isolation, camera UART, parts, removed parts
  K-binding    saved record-only firmware evidence equals native regeneration from the final board and reviewed tables
  K-actuators  m3_design/check_actuators.py --profile r10 in process (check.sh runs it only through this rule)
  K-loader     R3-MCU-01: every U1 pin that the H74x ROM bootloader uses (AN2606 Rev 64 Table 119, pp. 277-280) and
               that carries a net is in LOADER_R10 with that net, its recorded members (every other pad on the net, with
               its part value) and an electrical reason; pins the loader drives need a reason for the drive
  K-width      BAT_IN / RAW_PROTECTED power tracks >= 0.3 mm, no 0.3 mm run > 2 mm (R8-GATE-04); only dead-end
               R80.1 / R82.1 / R167.1 / R92.1 taps to their first power junction may use 0.15 mm without a length cap
  K-legends    pinned revision / safety texts, shown safety refs (R8-GATE-02/03), duplicate ids, pin legends, legend subjects (R10 word legends),
               R18-GATE-08: each connector word (WORD_LEGENDS_R10, the one list m3_design/r10_post.py places: IGN, BAT,
               CAM, SWD, SERVO, GPS, RADIO, SWITCH) once and beside its own connector (no other courtyard as near; only
               a named WORD_SEAMS tie, none on R10 since D-R19-06); D-R19-06: GPS and RADIO, the only names of the two
               identically pinned port terminals, lie inside their own terminal's courtyard y-span by WORD_SPAN_MARGIN;
               R19-GATE-06: the word's ink-box centre is >= 1.0 mm nearer its own courtyard than any other for GPS, RADIO
               and every word that clears it (BAT / SWITCH margins reported); R19-GATE-07: every visible silkscreen text
               is a designator or an allowed legend (terminal pins, words, port rows, harness note, pinned texts, JLC mark);
               R10 terminal pin legends (a combined 'Jnn n:NAME' table or an unknown bare 'n:NAME' legend, text or
               text box, is a conflicting second legend of the terminal pin it names / is nearest); AUD-10 counts subject distance for review;
               R3-MFG-01: no
               silkscreen item (board or footprint graphic, text, field), as its polygon, overlaps a pad's solder mask
               opening (pad copper + mask expansion) on its side; R20-MFG-02: each visible designator's ink is nearer
               its own courtyard than any other part's courtyard on its face, courtyards of any size (only exact,
               measured DESIGNATOR_COURTYARD_R20 entries excepted); R20-MFG-03: no Fab reference crosses its own Fab
               outline (only exact, measured FAB_REF_CROSSINGS_R20 entries); stale entries fail. D-R21-08
               (R21-GATE-05): each footprint carries exactly one visible Fab ${REFERENCE} on its own side's Fab layer
               (LS120's '+' / '-' the only other Fab texts), >= 0.3 mm high, its ink box crossing no other
               footprint's Fab outline or Fab reference and its ink centre inside no other footprint's Fab outline box.
               D-R22-06 (R22-GATE-02): its ink centre within FAB_REF_REACH (1.5 mm) of its own part's Fab body box (the
               courtyard box where the Fab layer has no body), its stroke >= 0.1 x height or >= 0.05 mm, and no
               board-level text on F.Fab / B.Fab
  K-power      R19-GATE-04: every path's floor is at least the IPC-2152 width for its named design current (30 C rise);
               the rails VLOGIC (trunk, C84 hold-up), PORT_5V3, CAM_5V (U402 -> J9), PORT_4V8 (U401, J410 / J420 / J440
               feeds) and 3V3 (U2 OUT) carry their drawn width; U401's pin links are named entries. R19-GATE-05: the
               paths are the copper on simple paths between the terminals (a side-branch loop is not on them); U9 IN needs
               one via of >= 1.0 / 0.5 mm, a parallel one >= 0.5 / 0.3 mm. Item 11: the J440 feed counts only its F.Cu vias.
               R18-GATE-02 / -03: U9's IN path (J1.1 -> U9.5 through C88) >= 1.0 mm and OUT path (U9.6 -> its In2 vias)
               >= 0.7 mm, only the named, measured POWER_NARROW entries (the 0.3 mm bar entries, the C88-local 0.7 mm
               runs, the 0.4 mm via link) excepted; IN >= 1 via of >= 1.0 / 0.5 mm, OUT >= 2 vias of >= 0.5 / 0.3 mm
               joined to In2 RAW_PROTECTED; Q124's source pads reach >= 2 In1 GND vias (>= 0.5 / 0.3 mm) on >= 0.3 mm
               F.Cu (D-R3-03); D-R19-09: the doubled feeds (U401 IN / EN / OUT, U402 IN: >= 2 In2 vias; C84 hold-up:
               >= 2 VLOGIC vias) and the buck outputs (L400.2 >= 2 In2 PORT_5V3 vias; L1.2 >= 2 In2 3V3 vias plus the
               named F/B-only bridge via (26.4, 79.26)). D-R20-02 (R20-PWR-02) / D-R21-02 (R21-GATE-01): each of the 26
               SINGLE_OPEN_TAPS regulator FB / OVLO / EN / ILIM taps stays joined to its source through its net's
               copper with any one via removed; a single point passes only as an exact SINGLE_OPEN_EXCEPTIONS entry
               (stale when no longer met). D-R22-02 (R22-POWER-01 / -02): 7 more taps, the TPS2553 GND pins U10.2 /
               U402.2, the CC Rd grounds R7.2 / R8.2 and the power-state monitors R60.1 (PA6), U1.28 (PA4) and R91.1,
               each an exact entry (33 taps, 15 entries). D-R23-01 / -02 (R23-MCU-02, R23-SAFETY-05): BOOT0, VCAP1,
               VCAP2 and the load switch's gate drive to Q120.4 / Q121.4, each an exact entry; D-R23-11 (R23-GATE-07):
               U4's power-ground pins U4.6 / U4.7 (40 taps, 22 entries)
  K-ports      D-R21-07 (R21-GATE-04): every port ESD clamp (J410 / J420 / J440 / J9 pins 3 and 4) lies within
               CLAMP_PATH_MAX (4.5 mm) of track from its terminal pin (pad centres, the net's track graph) on a path
               that does not pass the port's 1 k series resistor; D-R22-07 (R22-GATE-03): each clamp's GND pad reaches a
               GND via or plated GND pad through tracks (not the pour) within CLAMP_GND_MAX (1.0 mm)
  K-copper     R19-RTE-01: every pour piece holds a via of its net or joins two of its pads (only a named, measured
               POUR_DEBRIS entry excepted);
               vias in pads, overlap-only joints, thermal policy, via paste (check_r9.k_copper); GAP-3 admits only
               two exact filled/capped GND vias in U401.11, with unchanged maker paste and a VIPPO order condition
  K-inner      In1 GND only, In2 power and GND only (route_check r10 classes)
  K-reference  R19-REQ-10: every name critical_reference lists for R10 (R6, EXTENDED_R10, port, SD, AUD-2 slow lists) is
               a net of the board (a stale entry fails);
               (nets: the R6 / extended / port nets plus every signal-critical net of route_check's r10 classes,
               excluding only AUD-2's shared named slow-return list) samples have adjacent reference copper (critical_reference's extended set and the R10
               port nets): F.Cu over In1 GND; B.Cu over any In2 rail plane (GND, 3V3, 3V3A and R10's PORT_5V3,
               PORT_4V8, RAW_PROTECTED regions: decoupled DC rails, as R6 counted 3V3; Inference for the new ones);
               In1 / In2 tracks over F.Cu / B.Cu GND. An unreferenced sample passes only inside its own net's via
               antipad (REF_OWN_R of a same-net via, R9 D-S8-17), inside the S-8 void round its own barrel when it
               is a BARREL_GND_HAZARD net (BARREL_VOID_REACH, D-R19-01) or as a recorded REF_STRAY (D-R2-10)
  K-region     R4-RTE-02, R5-RTE-01 / -02 / -06: every B.Cu track of a signal-critical net (route_check r10's pyro,
               crystal, usb, spi, uart, portctl classes minus AUD-2's named slow list: the same nets K-reference samples; sampled every 0.02 mm on its
               centre line and on both edges pushed 0.1 mm outward) and every B.Cu SMD pad of such a net (0.05 mm grid
               over the pad grown by 0.1 mm) lies over exactly one In2 plane net and over In2 copper, outside its own
               vias' antipads (REF_OWN_R), the own through-hole pads' clearance voids (a no-copper region wholly
               inside the disc pad half-size + zone clearance + 0.05 mm; D-R26-01: or inside it and the antipad discs of
               the pad's GND partner vias, centres within 1.5 mm) and, for a BARREL_GND_HAZARD net, the S-8 void
               round its own barrels (D-R19-01); each connected B.Cu chain sees one plane net
  K-plane      R18-RTE-01: an inner power fill in several pieces needs two >= 0.5 mm outer links per extra piece;
               R19-GATE-03: deflated by 0.25 mm (unfractured), a landing via cut off from the largest piece by a neck
               under 0.5 mm is such a piece too; necks under 1.0 mm are reported. D-R21-06 (R21-GATE-03): the
               TAB_KEEPOUTS_R10 In2 keep-out (name, layer, outline, fill-only) and the non-GND inner copper under each
               of the four planned tab bands (TAB_BANDS_R10) at its recorded area: growth fails, a smaller figure is stale
  K-fill       R4-GATE-05: a copy of the board loaded from its file and refilled has the saved fill geometry in every
               zone UUID/layer/net (symmetric difference <= 0.01 mm^2); a stale or hand-edited fill fails
  K-rules      R4-GATE-01: m3.kicad_dru is pinned by SHA-256 (it is generated by m3_design/r10_sch.py); the .kicad_pro
               keeps min clearance and every net class clearance >= 0.15 mm, the min track / via / hole figures and the
               silkscreen text (1.0 mm height, 0.15 mm stroke), silk clearance and thermal-spoke floors (R18-GATE-06)
               at their recorded values, no DRC rule severity "ignore" and no DRC exclusions. D-R21-01 (R21-PWR-02 /
               R21-GATE-02): JLC's hole table (JLC_HOLE_TABLE: via hole to inner copper 0.2, PTH pad hole to inner
               copper 0.3, PTH hole to outer track 0.28, pad hole to hole 0.45 mm) held by its named DRU rules, none
               overridden by a later rule or undercut by any hole rule; and on the board every plated pad hole wall
               >= 0.3 mm from foreign In1 / In2 copper. D-R22-01 (R22-REQUIREMENTS-02): on the board, JLC_BOARD_HOLES:
               PTH rings >= 0.20 mm, via rings >= 0.05 mm, plated holes >= 0.15 mm, NPTH holes >= 0.50 mm, NPTH copper
               rings >= 0.45 mm and NPTH hole to any copper >= 0.2 mm (J3's 0.200 mm maker land at the limit).
               D-R22-05 (R22-GATE-01): every (min ...) read in any unit and position (unreadable fails); a later rule on
               any layer that can meet the pinned one counts as an override; and on the board via hole to foreign
               copper >= 0.2 mm, PTH hole to outer copper >= 0.28 mm and pad hole to hole >= 0.45 mm
  K-lands      R18-GATE-09: kilib/rocket.pretty is the only footprint library (fp-lib-table) and every footprint the board
               uses is generated and pinned by r10_parts --check or pinned here by its file's SHA-256 (FOOTPRINT_SHA256);
               R19-GATE-01: every placed footprint's and pad's paste margin / ratio, mask margin and paste / mask layers
               equal its library copy (zone, thermal and clearance overrides stay with K-copper / LC-1)
  K-retained   C29 flash and camera bypass,
               TP122 on the bottom; microSD C460 / C461 supply pads within 3 / 6 mm of J430.4
"""
import argparse
from contextlib import contextmanager
import csv
import hashlib
import heapq
import io
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
R10_BINDING_NOTE = Path('sources/r10_design/r10_binding_note.json')
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'quality_audit'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_actuators as actuators                             # noqa: E402
from sexpr import read, properties                              # noqa: E402

BUS_SENSE_REMOVED = frozenset({'R177', 'R124', 'R125', 'R182', 'R172', 'C122', 'R168', 'R170'})
PORT_REMOVED = frozenset({'U410', 'U420', 'R410', 'R411', 'R412', 'R420', 'R421', 'R422',
                          'U411', 'U421', 'R442', 'R452', 'C440', 'C443', 'C450', 'C453'})
REQUIRED_FITTED = (set(actuators.PINNED) - {'C121', 'J124'} - BUS_SENSE_REMOVED) | {
    'R131', 'C127', 'C129', 'C84', 'U11', 'U12', 'U13',
    'R100', 'R101', 'R102', 'R103', 'C91', 'C92', 'C93', 'C100', 'C29',
    'J400', 'J410', 'J420', 'J430', 'J440', 'U400', 'U401', 'U402'} | {f'{prefix}{n}' for prefix, numbers in
        (('R', (440, 441, 450, 451, 470, 471)), ('C', (410, 411, 420, 421, 444, 445)),
         ('R', range(460, 465)), ('C', (460, 461)),
         ('D', (400, 401, 410, 411, 420, 421, 440, 441)), ('R', (430, 431, 432)),
         ('R', range(400, 405)), ('C', range(400, 409)), ('L', (400,))) for n in numbers}
# Retained functional parts and their support, in addition to the safety/new-port set above. This closes the
# final native/schematic/BOM/CPL population invariant without another complete schematic-contract walk.
REQUIRED_FITTED |= {
    'U1', 'U2', 'U3', 'U4', 'U5', 'U10', 'L1', 'Y1', 'J3', 'J122', 'D4', 'D9',
    'Q123', 'D123', 'LS120', 'LED1', 'LED2',
    'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C13', 'C14', 'C15', 'C16', 'C17', 'C18',
    'C19', 'C20', 'C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C28', 'C30', 'C31', 'C32',
    'C60', 'C81', 'C82', 'C83', 'C85', 'C86', 'C88', 'C90', 'C94', 'C97', 'C98', 'C99',
    'C430', 'C431',
    'R5', 'R7', 'R8', 'R9', 'R10', 'R11', 'R12', 'R13', 'R32', 'R33', 'R60', 'R61',
    'R64', 'R85', 'R86', 'R87', 'R88', 'R89', 'R90', 'R91', 'R92', 'R104', 'R105',
    'R110', 'R162', 'R163', 'R164', 'R405'}
CONNECTORS = {
    'J1': ('BAT_IN', 'GND'), 'J400': ('BAT_SW_SOURCE', 'BAT_SW_RETURN'),
    'J410': ('PORT_4V8', 'GND', 'GPS_TX_WIRE', 'GPS_RX_WIRE'),
    'J420': ('PORT_4V8', 'GND', 'RADIO_TX_WIRE', 'RADIO_RX_WIRE'),
    'J440': ('PORT_4V8', 'GND', 'AUX_TX_WIRE', 'AUX_RX_WIRE'),             # D-R19-14: the spare AUX port, a J410 copy
    'J9': ('CAM_5V', 'GND', 'CAM_RX_WIRE', 'CAM_TX_WIRE'),
    'J122': ('SERVO1_OUT', 'SERVO2_OUT', 'SERVO3_OUT', 'SERVO4_OUT', 'GND')}
PARTS = {'J1': ('C466970', 'M3_DB125_2P_GN'),
         'J121': ('C52993880', 'M3_DB125_2P_BK'),
         'J400': ('C466970', 'M3_DB125_2P_GN'),
         'J410': ('C2757925', 'M3_DB125_4P_GN'), 'J420': ('C2757925', 'M3_DB125_4P_GN'),
         'J440': ('C2757925', 'M3_DB125_4P_GN'),
         'J9': ('C2757925', 'M3_DB125_4P_GN'), 'J122': ('C3646874', 'M3_DB125_5P_GN'),
         'C84': ('C46550466', 'M3_MA_8x10'),
         'C92': ('C19666', 'C0603'),  # AUD-1: same qualified land as C23/C28; inferred effective-capacitance bound 2.211uF.
         'C120': ('C29936', 'C_0603_1608Metric'),  # AUD-3: same qualified land as C86/C97/C98; 100ms settling.
         'Q120': ('C431196', 'M3_AONR21357_DFN3x3A_EP1'),
         'Q121': ('C431196', 'M3_AONR21357_DFN3x3A_EP1')}
PARTS['R432'] = ('C25744', 'R0402')  # AUD-7, retained camera switch FAULT pull-up.
PARTS['J430'] = ('C164170', 'M3_MICROSD_MOLEX_472192001')
PARTS['D402'] = ('C535146', 'M3_TSLP_2_20')  # D-R24-11: J400.2's contact clamp, the port clamps' ESD103-B1-02EL line
REMOVED = {'U30', 'U31', 'J30', 'J31', 'C121', 'C150', 'C151', 'U7', 'U8', 'L3', 'J124'}
# AUD-4 / AUD-5 / AUD-8: reject stale parts as well as removing required-population obligations.
AUD_REMOVED = {'J123', 'R160', 'R161', 'C160', 'D122', 'TP84', 'TP85', 'TP86', 'TP87', 'TP89', 'TP92',
               'U412', 'U422', 'R443', 'R453', 'C441', 'C442', 'C451', 'C452'}
REMOVED |= AUD_REMOVED
REMOVED |= BUS_SENSE_REMOVED | PORT_REMOVED
REMOVED |= {'R62', 'R63'}            # D-R18-01 (R18-REQ-08): V3V3_SENSE divider removed; PC3_C is NC
REMOVED |= {'TP121'}                 # D-R19-03 (R19-SAF-03): bare ACT_GATE probe pad removed; probe R119.1 / R120.2
REQUIRED_FITTED |= {'C123'}          # D-R19-04 (R19-SAF-06): Q122 gate-source capacitor


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


def assembly_population(text, required=REQUIRED_FITTED, *, require_qty=False, native_parts=None):
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    has_qty = 'Qty' in (reader.fieldnames or [])
    refs, issues, first_row = set(), [], {}
    if require_qty and not has_qty:
        issues.append('Qty column required for BOM')
    for line, row in enumerate(rows, 2):
        members = {ref.strip() for ref in (row.get('Designator') or '').split(',') if ref.strip()}
        for ref in sorted(members):
            if ref in first_row:
                issues.append(f'line {line}: {ref} already appears on line {first_row[ref]}')
            else:
                first_row[ref] = line
            if native_parts is not None:
                expected = native_parts.get(ref)
                if expected is None:
                    issues.append(f'line {line}: {ref} is not a native fitted part')
                else:
                    for field, wanted in expected.items():
                        actual = (row.get(field) or '').strip()
                        if not wanted or actual != wanted:
                            issues.append(f'line {line}: {ref} {field} {actual!r} differs from native fitted part {wanted!r}')
        refs.update(members)
        if has_qty:
            value = (row.get('Qty') or '').strip()
            if not re.fullmatch(r'\d+', value) or int(value) <= 0:
                issues.append(f'line {line}: Qty {value!r} must be a positive integer')
            elif int(value) != len(members):
                issues.append(f'line {line}: Qty {value} differs from {len(members)} distinct designators')
    return issues + [f'{ref}: required fitted part missing from assembly list' for ref in sorted(required - refs)]


def uart_ports(pins, values, codes):
    """Always-on GPS/radio/AUX: 1 k series and connector-side ESD, direct to their 3V3 MCU UARTs (D-R19-14)."""
    issues = []
    for ref in PORT_REMOVED | {'U412', 'U422', 'R443', 'R453', 'C441', 'C442', 'C451', 'C452'}:
        if ref in codes or ref in values or any(p.startswith(ref + '.') for p in pins):
            issues.append(f'{ref}: removed GPS/radio switch or translator part remains')
    def expect(ref, nets, code=None, value=None):
        for num, net in nets.items():
            actual = pins.get(f'{ref}.{num}')
            if actual != net and not (net is None and actual and actual.startswith('unconnected-')):
                issues.append(f'{ref}.{num}: direct UART requires {net}, got {actual}')
        if code and codes.get(ref) != code:
            issues.append(f'{ref}: direct UART requires LCSC {code}')
        if value and values.get(ref) != value:
            issues.append(f'{ref}: direct UART requires {value}')
    # D-R19-14: three electrically identical ports (terminal, RX / TX 1 k, 100 nF / 22 uF, TX / RX clamps, MCU TX / RX
    # pins); J410 moved to USART3 PD8 / PD9 and J440 (AUX) took USART6 PC6 / PC7.
    for port, j, r_rx, r_tx, c_small, c_big, d_tx, d_rx, tx_pin, rx_pin in (
            ('GPS', 'J410', 'R440', 'R441', 'C410', 'C411', 'D410', 'D411', '55', '56'),
            ('RADIO', 'J420', 'R450', 'R451', 'C420', 'C421', 'D420', 'D421', '52', '51'),
            ('AUX', 'J440', 'R470', 'R471', 'C444', 'C445', 'D440', 'D441', '63', '64')):
        expect(r_rx, {1: f'{port}_RX_WIRE', 2: f'{port}_RX_MCU'}, 'C21190', '1k 1%')
        expect(r_tx, {1: f'{port}_TX_MCU', 2: f'{port}_TX_WIRE'}, 'C21190', '1k 1%')
        expect(j, {1: 'PORT_4V8', 2: 'GND', 3: f'{port}_TX_WIRE', 4: f'{port}_RX_WIRE'}, 'C2757925')
        expect(c_small, {1: 'PORT_4V8', 2: 'GND'}, 'C14663', '100nF 50V X7R 10%')
        expect(c_big, {1: 'PORT_4V8', 2: 'GND'}, 'C21397', '22uF 25V X7R 10%')
        expect(d_tx, {1: f'{port}_TX_WIRE', 2: 'GND'}, 'C535146')
        expect(d_rx, {1: f'{port}_RX_WIRE', 2: 'GND'}, 'C535146')
        mcu_pins = {'TX': tx_pin, 'RX': rx_pin}
        for signal, mcu, resistor in (
                ('RX', f'{port}_RX_MCU', r_rx), ('TX', f'{port}_TX_MCU', r_tx)):
            want = {f'{resistor}.{2 if signal == "RX" else 1}',
                    f'U1.{mcu_pins[signal]}'}
            if {p for p, net in pins.items() if net == mcu} != want:
                issues.append(f'{mcu}: must touch only U1 and its 1k resistor')
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


SD_PINS = {1: 'SD_DAT2', 2: 'SD_CS', 3: 'SD_MOSI', 4: '3V3', 5: 'SD_SCK', 6: 'GND',
           7: 'SD_MISO', 8: 'SD_DAT1', 9: 'GND', 10: 'GND', 11: 'GND', 12: 'GND'}
SD_PULLUPS = {'R460': 'SD_CS', 'R461': 'SD_MOSI', 'R462': 'SD_MISO', 'R463': 'SD_DAT1', 'R464': 'SD_DAT2'}


def micro_sd(pins, values, codes):
    """Hinged socket, 3V3 SPI3 and all five 10k pull-ups; QSPI remains independently required."""
    issues = []
    expected = {'J430': (SD_PINS, 'C164170', '472192001')}
    expected.update({ref: ({1: net, 2: '3V3'}, 'C25804', '10k 1%') for ref, net in SD_PULLUPS.items()})
    expected['C460'] = ({1: '3V3', 2: 'GND'}, 'C14663', '100nF 50V X7R 10%')
    expected['C461'] = ({1: '3V3', 2: 'GND'}, 'C21397', '22uF 25V X7R 10%')
    for ref, (nets, code, value) in expected.items():
        if codes.get(ref) != code or values.get(ref) != value:
            issues.append(f'{ref}: microSD requires {value}, LCSC {code}')
        actual = {p: net for p, net in pins.items() if p.startswith(ref + '.')}
        want = {f'{ref}.{n}': net for n, net in nets.items()}
        if actual != want:
            issues.append(f'{ref}: microSD pin mapping must be {want}, got {actual}')
    members = {
        'SD_SCK': {'U1.78', 'J430.5'}, 'SD_MISO': {'U1.79', 'J430.7', 'R462.1'},
        'SD_MOSI': {'U1.80', 'J430.3', 'R461.1'}, 'SD_CS': {'U1.81', 'J430.2', 'R460.1'},
        'SD_DAT1': {'J430.8', 'R463.1'}, 'SD_DAT2': {'J430.1', 'R464.1'}}
    for net, want in members.items():
        actual = {p for p, name in pins.items() if name == net}
        if actual != want:
            issues.append(f'{net}: microSD members must be {sorted(want)}, got {sorted(actual)}')
    return issues


def port_power(pins, values, codes):
    """O5 regulated rails, always-on GPS/radio and retained camera default-off/FAULT/ILIM contract."""
    issues = []
    expected = {
        'U400': {1: 'PORT_FB', 2: 'RAW_PROTECTED', 3: 'RAW_PROTECTED', 4: 'GND', 5: 'PORT_SW', 6: 'PORT_BST'},
        'U401': {1: 'PORT_4V8', 2: 'PORT_4V8', 3: 'PORT_LDO_FB', 4: 'GND', 5: None, 6: 'GND',
                 7: 'PORT_5V3', 8: 'PORT_LDO_SS', 9: 'PORT_5V3', 10: 'PORT_5V3', 11: 'GND'}}
    pinned = {'U400': 'C2071044', 'U401': 'C2878140'}
    for port, switch, rb, supply, out, limit, code, mcu in (
            # D-R18-09 (R18-BOM-01): FOJAN FRC0603F2262TS, the stocked exact 22.6 kohm 1% 0603 drop-in.
            ('CAM', 'U402', 430, 'PORT_5V3', 'CAM_5V', '22.6k 1%', 'C2999509', ('41', '42')),):
        expected[switch] = {1: supply, 2: 'GND', 3: f'{port}_PWR_EN', 4: f'{port}_FAULT_N',
                            5: f'{port}_ILIM', 6: out}
        pinned[switch] = 'C55266'
        for ref, net, return_net, value, lcsc in (
                (f'R{rb}', f'{port}_ILIM', 'GND', limit, code),
                (f'R{rb + 1}', f'{port}_PWR_EN', 'GND', '100k 1%', 'C14675'),
                (f'R{rb + 2}', f'{port}_FAULT_N', '3V3', '10k 1%', 'C25744')):  # AUD-7, 0402 digital pull-up.
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



def signal_critical_nets(board):
    """Every net of `board` that route_check's r10 profile classes signal-critical (pyro, crystal, usb, spi, uart,
    portctl): the ONE definition K-reference and K-region share with route_check (R4-RTE-01)."""
    import route_check as rc
    previous = rc.PROFILE
    rc.set_profile('r10')
    try:
        return {n for n in (str(k) for k in board.GetNetsByName().keys()) if n and rc.net_class(n) in rc.SIGNAL_CRITICAL}
    finally:
        rc.set_profile(previous)


def return_path_nets(board):
    """AUD-2: omit only the shared named slow nets; critical hygiene classification stays intact."""
    import critical_reference as cr
    return {n for n in signal_critical_nets(board) if not cr.r10_slow_return_net(n)}


def own_antipads(board):
    """{net: [(x, y, r)]} mm: the antipads a net's own plated copper opens in the planes (R9 D-S8-17 for vias): its vias
    at REF_OWN_R, and its plated through-hole pads (the terminal barrels) at half the pad size + REF_PAD_ANTIPAD (the
    plane clearance of a barrel; Inference, the measured terminal voids reach 1.3 mm from the barrel centre)."""
    import pcbnew
    out = {}
    for v in board.GetTracks():
        if v.GetClass() == 'PCB_VIA':
            out.setdefault(v.GetNetname(), []).append((pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y),
                                                       REF_OWN_R))
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname():
                size = max(pcbnew.ToMM(p.GetSize().x), pcbnew.ToMM(p.GetSize().y))
                out.setdefault(p.GetNetname(), []).append((pcbnew.ToMM(p.GetPosition().x),
                                                           pcbnew.ToMM(p.GetPosition().y), size / 2 + REF_PAD_ANTIPAD))
    return out


def in_own_antipad(own, net, x, y):
    return any(math.dist((x, y), q[:2]) <= q[2] for q in own.get(net, ()))


# D-R19-01 (R19-SAF-01): S-8 keeps all foreign inner copper, GND included, BARREL_GAP clear of the barrel walls of the
# BARREL_GND_HAZARD nets, and r10_route_ground.BARREL_KEEPOUT opens the In1 / In2 fills there by a 16-sided polygon
# 1.05 mm beyond the wall. A sample of such a net's own copper inside that void has no reference by S-8's design, so
# K-reference and K-region skip it there (out to the polygon's corners, 1.05 / cos(pi / 16) = 1.0706 mm beyond the wall).
# Every other net's samples over the void are still taken.
BARREL_VOID_REACH = 1.071       # mm beyond the barrel wall


def own_barrel_voids(board, nets=None):
    """{net: [(x, y, r)]} mm: the inner-layer voids S-8 forces round the plated barrels of the GND-hazard nets."""
    import pcbnew
    nets = BARREL_GND_HAZARD if nets is None else nets
    out = {}
    for v in board.GetTracks():
        if v.GetClass() == 'PCB_VIA' and v.GetNetname() in nets:
            out.setdefault(v.GetNetname(), []).append((pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y),
                                                       pcbnew.ToMM(v.GetDrillValue()) / 2 + BARREL_VOID_REACH))
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname() in nets:
                r = max(pcbnew.ToMM(p.GetDrillSize().x), pcbnew.ToMM(p.GetDrillSize().y)) / 2
                out.setdefault(p.GetNetname(), []).append((pcbnew.ToMM(p.GetPosition().x),
                                                           pcbnew.ToMM(p.GetPosition().y), r + BARREL_VOID_REACH))
    return out


REGION_STEP = 0.02             # mm: K-region sample spacing along a track (centre line and both pushed edges)
REGION_MARGIN = 0.1            # mm: the edges are sampled this far outside the copper edge (R5-RTE-02)
REGION_PAD_STEP = 0.05         # mm: K-region sample grid over an SMD pad grown by REGION_MARGIN
REGION_HOLE_REACH = 0.30       # mm: a via's fill hole reaches no further than its pad radius + this (measured hole radius
                               # 0.401 = pad 0.25 + 0.15 on the R10 board; R6-RTE-02)
VOID_RIM_SIDES = 64            # the pad-void disc is this many sided polygon


def fill_hole_table(zones, vias):
    """[(x0, y0, x1, y1, chain, {nets})] mm: every hole (inner outline) of the In2 fills that is a via clearance hole:
    its area contains a via centre and every vertex of its outline lies within (pad radius + REGION_HOLE_REACH) of a via
    centre, so the hole is covered by via discs (one via: its box is no larger than 2 x (pad radius + reach); vias with
    merged antipads: a hole of the union). `nets` are the nets of the vias inside it. A slot, a plane pull-back or any
    other no-copper shape is no via hole (R6-RTE-02 / R6-GATE-01)."""
    import pcbnew
    out = []
    for ps in zones.values():
        for o in range(ps.OutlineCount()):
            for h in range(ps.HoleCount(o)):
                chain = ps.Hole(o, h)
                bb = chain.BBox()
                x0, y0 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
                x1, y1 = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
                near = [v for v in vias if x0 - 1.5 <= v[0] <= x1 + 1.5 and y0 - 1.5 <= v[1] <= y1 + 1.5]
                nets = {n for vx, vy, n, _ in near if x0 <= vx <= x1 and y0 <= vy <= y1
                        and chain.PointInside(pcbnew.VECTOR2I(pcbnew.FromMM(vx), pcbnew.FromMM(vy)))}
                covered = all(any(math.hypot(pcbnew.ToMM(chain.CPoint(k).x) - vx, pcbnew.ToMM(chain.CPoint(k).y) - vy)
                                  <= r + REGION_HOLE_REACH for vx, vy, _, r in near) for k in range(chain.PointCount()))
                if nets and covered and not hole_uncovered_area(chain, near) > HOLE_SLIVER_MM2:
                    out.append((x0, y0, x1, y1, chain, nets))
    return out


HOLE_SLIVER_MM2 = 2e-3         # mm2: what the via discs may leave of a via hole (R7-GATE-02); measured 4.95e-4 at the
                               # merged SPI1 hole (a 0.04 mm triangle between three discs), a slot is mm2 (10 mm: 8)


def hole_uncovered_area(chain, vias):
    """mm2 of the hole polygon `chain` not covered by the union of the discs (via pad radius + REGION_HOLE_REACH) of
    `vias`: a hole whose vertices are near vias but whose body is a slot between them is no via hole (R7-GATE-02)."""
    import pcbnew
    hole = pcbnew.SHAPE_POLY_SET()
    hole.AddOutline(chain)
    for vx, vy, _, r in vias:
        disc = pcbnew.SHAPE_POLY_SET()
        disc.NewOutline()
        for k in range(VOID_RIM_SIDES):
            a = 2 * math.pi * k / VOID_RIM_SIDES
            rr = (r + REGION_HOLE_REACH) / math.cos(math.pi / VOID_RIM_SIDES)       # circumscribed: never smaller
            disc.Append(pcbnew.FromMM(vx + rr * math.cos(a)), pcbnew.FromMM(vy + rr * math.sin(a)))
        hole.BooleanSubtract(disc)
    return hole.Area() / 1e12


def in_via_hole(table, net, x, y):
    import pcbnew
    pt = None
    for x0, y0, x1, y1, chain, nets in table:
        if x0 <= x <= x1 and y0 <= y <= y1 and any(n != net for n in nets):
            pt = pt or pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
            if chain.PointInside(pt):
                return True
    return False


PARTNER_REACH = 1.5            # mm: D-R26-01: a GND via centre this near a through-hole pad's centre is its GND partner
                               # (D-R19-15's 1.5 mm rule); its In2 antipad (pad radius + REGION_HOLE_REACH) cannot stay
                               # apart from the pad's own void (J440.3 / J440.4: void 1.2 mm, antipad 0.40 mm, 1.5 mm apart)


def pad_void_regions(zones, cx, cy, radius, partners=()):
    """[(free SHAPE_POLY_SET, outline index, escapes)]: the In2 no-copper regions inside the disc (cx, cy, radius) by
    polygon subtraction (no grid, so a 0.02 mm exit slot cannot slip through; R6-GATE-05); `escapes` when the region
    reaches the disc's rim (a vertex on the rim polygon). D-R26-01: `partners` [(x, y, r)] are the pad's GND partner
    vias' antipad discs: the region may also fill them, and it escapes when a vertex lies on the rim of the union (on the
    pad disc's rim outside every partner disc, or on a partner disc's rim outside the pad disc)."""
    import pcbnew

    def ngon(x, y, r):
        ps = pcbnew.SHAPE_POLY_SET()
        ps.NewOutline()
        for k in range(VOID_RIM_SIDES):
            a = 2 * math.pi * k / VOID_RIM_SIDES
            ps.Append(pcbnew.FromMM(x + r * math.cos(a)), pcbnew.FromMM(y + r * math.sin(a)))
        return ps
    disc = ngon(cx, cy, radius)
    for px, py, pr in partners:
        disc.BooleanAdd(ngon(px, py, pr))
    for ps in zones.values():
        disc.BooleanSubtract(ps)
    shrink = math.cos(math.pi / VOID_RIM_SIDES)
    rim = radius * shrink - 0.002
    rims = [(px, py, pr * shrink - 0.002) for px, py, pr in partners]

    def on_rim(x, y):
        return math.hypot(x - cx, y - cy) >= rim and all(math.hypot(x - px, y - py) >= pr for px, py, pr in rims)
    out = []
    for i in range(disc.OutlineCount()):
        chain = disc.COutline(i)
        escapes = any(on_rim(pcbnew.ToMM(chain.CPoint(k).x), pcbnew.ToMM(chain.CPoint(k).y))
                      for k in range(chain.PointCount()))
        out.append((disc, i, escapes))
    return out


class OwnPadVoids:
    """The plated through-hole pads' own clearance voids in the In2 planes: a sample is exempt only inside a no-copper
    component that lies wholly in the disc (pad half-size + zone clearance + 0.05 mm) around the pad centre. D-R26-01:
    or wholly in that disc and the antipad discs (pad radius + REGION_HOLE_REACH) of the pad's GND partner vias (GND via
    centres within PARTNER_REACH of the pad centre); the sample itself still lies in the pad disc."""

    def __init__(self, board, zones):
        import pcbnew
        self.zones, self.pads, self.cache = zones, {}, {}
        clearance = max((pcbnew.ToMM(z.GetOwnClearance(pcbnew.In2_Cu)) for z in board.Zones()
                         if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In2_Cu)), default=0.0)
        gnd = [(pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y), pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu)) / 2)
               for v in board.GetTracks() if v.GetClass() == 'PCB_VIA' and v.GetNetname() == 'GND']
        for f in board.GetFootprints():
            for p in f.Pads():
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname():
                    half = max(pcbnew.ToMM(p.GetSize().x), pcbnew.ToMM(p.GetSize().y)) / 2
                    cx, cy = pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)
                    partners = tuple((vx, vy, vr + REGION_HOLE_REACH) for vx, vy, vr in gnd
                                     if math.dist((vx, vy), (cx, cy)) <= PARTNER_REACH + 1e-6)
                    self.pads.setdefault(p.GetNetname(), []).append(
                        (len(self.cache), cx, cy, half + clearance + 0.05, partners))
                    self.cache[len(self.cache)] = None

    def exempt(self, net, x, y):
        import pcbnew
        pt = pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        for key, cx, cy, radius, partners in self.pads.get(net, ()):
            if math.dist((x, y), (cx, cy)) > radius:
                continue
            if self.cache[key] is None:
                self.cache[key] = pad_void_regions(self.zones, cx, cy, radius, partners)
            regions = self.cache[key]
            hit = [esc for ps, i, esc in regions if ps.Contains(pt, i, 1000, True)]
            if hit and not any(hit):
                return True
        return False


def region_issues(board):
    """K-region (R4-RTE-02, R5-RTE-01 / -02 / -06): every B.Cu track (straight or arc) of a signal-critical net is
    sampled every REGION_STEP on its centre line and on both edges pushed REGION_MARGIN outward, and every B.Cu SMD pad
    of such a net on a REGION_PAD_STEP grid over the pad grown by REGION_MARGIN; each sample lies over exactly one In2
    plane net, outside REF_OWN_R of the net's own vias and outside the net's own through-hole pads' clearance voids (a
    no-copper region wholly inside the pad's disc, or inside it and its GND partner vias' antipad discs, D-R26-01,
    OwnPadVoids); a no-copper sample inside a hole of the fill that holds
    another net's via (hole box <= 2 x (via pad radius + REGION_HOLE_REACH)) is a clearance hole, not a boundary. Each connected B.Cu chain (tracks joined end to end or
    through a pad of the net) sees exactly one In2 plane net in total. Returns (issues, evidence)."""
    import critical_reference as cr
    import pcbnew
    nets = return_path_nets(board)
    zones = {}
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In2_Cu) and z.HasFilledPolysForLayer(pcbnew.In2_Cu):
            zones.setdefault(z.GetNetname(), pcbnew.SHAPE_POLY_SET()).BooleanAdd(z.GetFilledPolysList(pcbnew.In2_Cu))
    vias = {}
    for v in board.GetTracks():
        if v.GetClass() == 'PCB_VIA':
            vias.setdefault(v.GetNetname(), []).append((pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y)))
    voids = OwnPadVoids(board, zones)
    barrel_voids = own_barrel_voids(board)                          # D-R19-01
    # a sample over no copper inside a hole of the In2 fill that holds another net's via is that via's clearance hole,
    # not a plane boundary (geometric: the hole's own outline and size, R6-RTE-02); K-reference holds the run's own
    # reference there (R5 fix pass, D-R5-03)
    via_holes = fill_hole_table(zones, [(pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y), v.GetNetname(),
                                         pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu)) / 2)
                                        for v in board.GetTracks() if v.GetClass() == 'PCB_VIA'])
    items, count = [], 0       # (net, label, endpoint keys, planes seen, gaps)

    def scan(net, pts):
        nonlocal count
        seen, gaps = set(), []
        for x, y in pts:
            if any(math.dist((x, y), q) <= REF_OWN_R for q in vias.get(net, ())):
                continue
            if in_own_antipad(barrel_voids, net, x, y):
                continue
            on = [n for n, ps in zones.items() if cr.inside(ps, x, y)]
            if not on and voids.exempt(net, x, y):
                continue
            if not on and in_via_hole(via_holes, net, x, y):
                continue
            count += 1
            seen.update(on)
            if not on:
                gaps.append((round(x, 2), round(y, 2)))
        return seen, gaps

    def key(pt):
        return (round(pcbnew.ToMM(pt.x), 3), round(pcbnew.ToMM(pt.y), 3))
    for t in board.GetTracks():
        if t.GetClass() not in ('PCB_TRACK', 'PCB_ARC') or t.GetLayer() != pcbnew.B_Cu or t.GetNetname() not in nets:
            continue
        net = t.GetNetname()
        seen, gaps = scan(net, [(x, y) for _, _, x, y in cr.track_samples(t, 0.0, REGION_STEP, REGION_MARGIN)])
        a, c = key(t.GetStart()), key(t.GetEnd())
        items.append((net, f'B.Cu run ({a[0]:.2f}, {a[1]:.2f}) - ({c[0]:.2f}, {c[1]:.2f})', {a, c}, seen, gaps))
    pads = []
    for f in board.GetFootprints():
        for p in f.Pads():
            net = p.GetNetname()
            if net not in nets or not p.IsOnLayer(pcbnew.B_Cu) or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            bb = p.GetBoundingBox()
            x0, x1 = pcbnew.ToMM(bb.GetLeft()) - REGION_MARGIN, pcbnew.ToMM(bb.GetRight()) + REGION_MARGIN
            y0, y1 = pcbnew.ToMM(bb.GetTop()) - REGION_MARGIN, pcbnew.ToMM(bb.GetBottom()) + REGION_MARGIN
            shape = p.GetEffectiveShape(pcbnew.B_Cu)
            nx, ny = int((x1 - x0) / REGION_PAD_STEP) + 1, int((y1 - y0) / REGION_PAD_STEP) + 1
            pts = []
            for i in range(nx + 1):
                for j in range(ny + 1):
                    x, y = x0 + i * (x1 - x0) / nx, y0 + j * (y1 - y0) / ny
                    if shape.Collide(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)), pcbnew.FromMM(REGION_MARGIN)):
                        pts.append((x, y))
            seen, gaps = scan(net, pts)
            pads.append(p)
            items.append((net, f'pad {f.GetReference()}.{p.GetNumber()}', {('pad', len(pads) - 1)}, seen, gaps))
    issues = []
    for net, label, _, seen, gaps in items:
        if len(seen) > 1 or gaps:
            issues.append(f'{net} {label} lies over In2 planes {sorted(seen) or "none"}'
                          + (f' and {len(gaps)} samples over no In2 copper, e.g. {gaps[0]}' if gaps else '')
                          + ' (one In2 plane region per signal-critical run)')
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    bynet = {}
    for i, it in enumerate(items):
        bynet.setdefault(it[0], []).append(i)
    for idx in bynet.values():
        for a in idx:
            for c in idx:
                if a >= c:
                    continue
                ea, ec = items[a][2], items[c][2]
                joined = bool(ea & ec)
                for tr, pd in ((a, c), (c, a)):               # a track whose end lies on a pad of the net
                    pad_key = next((k for k in items[pd][2] if k[0] == 'pad'), None)
                    if not joined and pad_key is not None and not any(k[0] == 'pad' for k in items[tr][2]):
                        pad = pads[pad_key[1]]
                        joined = any(pad.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
                                     for x, y in items[tr][2])
                if joined:
                    parent[find(a)] = find(c)
    groups = {}
    for i in range(len(items)):
        groups.setdefault(find(i), []).append(i)
    for g in groups.values():
        planes = set().union(*(items[i][3] for i in g))
        if len(planes) > 1:
            issues.append(f'{items[g[0]][0]} connected B.Cu chain ({", ".join(items[i][1] for i in g[:6])}) lies over '
                          f'In2 planes {sorted(planes)} (one In2 plane region per connected chain)')
    return issues, {'items': len(items), 'samples': count, 'nets': sorted(nets)}


def references(board):
    """K-reference (D-R2-10): critical_reference's samples with B.Cu over any In2 rail plane; an unreferenced sample
    passes inside its own net's via antipad (REF_OWN_R) or as a recorded REF_STRAY."""
    import critical_reference as cr
    import pcbnew
    refs = cr.references(True)
    refs[pcbnew.B_Cu] = (pcbnew.In2_Cu, REF_PLANES_B)
    nets = {n for n in set(cr.R6_NETS + cr.EXTENDED_R10 + cr.R10_PORT_NETS + cr.R10_SD_NETS) | signal_critical_nets(board)
            if not cr.r10_slow_return_net(n)}  # AUD-2; fast interfaces retain every reference sample.
    samples = cr.samples(board, nets, refs)
    fill = cr.fills(board, refs)
    empty = pcbnew.SHAPE_POLY_SET()
    missing = [s for s in samples if not cr.inside(fill.get(s[1], empty), s[2], s[3])]
    own = own_antipads(board)
    barrel_voids = own_barrel_voids(board)                          # D-R19-01: S-8's own-barrel voids
    stray = [s for s in missing if not in_own_antipad(own, s[0], s[2], s[3])
             and not in_own_antipad(barrel_voids, s[0], s[2], s[3])]
    used, loose = set(), []
    for s in stray:
        name = pcbnew.LayerName(s[1])
        hit = [k for k, e in enumerate(REF_STRAY) if e[:2] == (s[0], name) and math.dist(e[2:4], s[2:4]) <= 0.01]
        if hit:
            used.add(hit[0])
        else:
            loose.append((s[0], name, s[2], s[3]))
    issues = []
    if not samples:
        issues.append('no critical routed-reference samples (unrouted board)')
    if loose:
        issues.append(f'{len(loose)} critical signal samples lack adjacent reference copper outside their own via '
                      f'antipads, e.g. {loose[:3]}')
    issues += [f'stale REF_STRAY entry {e[:4]}' for k, e in enumerate(REF_STRAY) if k not in used and samples
               and len(samples) > 1000]
    return issues, {'samples': len(samples), 'unreferenced': len(missing), 'inside_own_antipad': len(missing) -
                    len(stray), 'recorded_stray': len(used), 'loose': len(loose),
                    'b_cu_planes': list(REF_PLANES_B), 'by_net_layer': cr._group([s for s in stray])}



def contract(text):
    """R10 netlist contract (K-contract): connectors, U1 pin map, port power and UART isolation, camera UART, pinned
    parts, removed R9 parts and nets. Population (S-4) and check_actuators (K-actuators) run as their own rules."""
    issues = []
    codes = {}
    pins, values = actuators.pad_nets(text, codes)
    if values.get('C92') != '4.7uF 16V X5R 10%':
        issues.append('AUD-1: C92 must be qualified 4.7uF 16V X5R 10% (C19666)')
    if values.get('C120') != '1uF 25V X7R 10%':
        issues.append('AUD-3: C120 must be qualified 1uF 25V X7R 10% (C29936)')
    issues += (uart_ports(pins, values, codes) + port_power(pins, values, codes)
               + camera_uart(pins, values, codes) + micro_sd(pins, values, codes))
    fps = {properties(f)['Reference'].items[2].atom: f for f in read(text).children('footprint')}
    refs = [properties(f)['Reference'].items[2].atom for f in read(text).children('footprint')]
    if len(refs) != len(set(refs)):
        issues.append('duplicate footprint reference')
    rf = re.compile(r'(U3[01]|J3[01]|Q3\d|[RCDLQ]3\d\d|D3[01]|L30|FB3[01]|TP30)')
    for ref in sorted((REMOVED & fps.keys()) | {r for r in fps if rf.fullmatch(r)}):
        issues.append(f'{ref}: removed R10 component remains')
    for ref, nets in CONNECTORS.items():
        if tuple(pins.get(f'{ref}.{i}') for i in range(1, len(nets) + 1)) != nets:
            issues.append(f'{ref}: connector pin mapping must be {nets}')
        electrical = {k for k in pins if k.startswith(ref + '.') and k.split('.')[-1].isdigit()}
        if electrical != {f'{ref}.{i}' for i in range(1, len(nets) + 1)}:
            issues.append(f'{ref}: wrong electrical pin count')
    expected_mcu = mcu_pin_table()
    for pin, net in expected_mcu.items():
        actual = pins.get('U1.' + pin)
        if actual != net and not (net == 'NC' and (actual is None or actual.startswith('unconnected-'))):
            issues.append(f'U1.{pin}: must be {net}, got {actual}')
    for ref, (code, land) in PARTS.items():
        if codes.get(ref) != code or ref not in fps or fps[ref].items[1].atom != 'rocket:' + land:
            issues.append(f'{ref}: must use {code} on rocket:{land}')
    forbidden = re.compile(r'^(PYRO|ARM|ACT_|SERVO|RAW_ACT|BAT_IN)')
    for ref in ('J410', 'J420', 'J440', 'U410', 'U420', 'U411', 'U421'):
        nets = [n for p, n in pins.items() if p.startswith(ref + '.') and n and forbidden.match(n)]
        if nets:
            issues.append(f'{ref}: external port touches safety nets {nets}')
    nets = (set(pins.values()) - {None}) | {n.items[-1].atom for n in read(text).children('net')}
    for net in nets:
        if net == 'PYRO1_BUS':
            issues.append('PYRO1_BUS: obsolete separate bus; R10 uses RAW_ACT behind Q120/Q121')
        if net.startswith('RAW_ACT_SENSE'):
            issues.append(f'{net}: duplicate bus sense removed; ARM1_SENSE is the sole RAW_ACT reading')
        if net in ('PYRO1_CONT_MCU', 'ARM1_SENSE_MCU'):
            issues.append(f'{net}: obsolete ADC tail; filtered sense nodes connect directly to PC0 / PC5')
        if re.match(r'^(GPS|RADIO)_(?:[TR]X_BUFFER|PWR_EN|FAULT_N|UART_OE|ILIM|IO_3V3|4V8)$', net):
            issues.append(f'{net}: obsolete switched/translated port net remains')
        if re.match(r'^(GNSS_|3V3_GNSS|3V3_RADIO|RADIO_(RF|SCK|MOSI|MISO|NSS|BUSY|DIO|NRST|TXEN|RXEN))', net):
            issues.append(f'{net}: obsolete on-board RF net remains')
    return issues


def functional(text):
    """The whole netlist-level contract in one call (kept for the generators' quick check)."""
    return actuators.check(text, profile='r10') + population(text) + contract(text)


# ======================================================================================================================
# R10 constants
# ======================================================================================================================
# R1-07: the safety parts that must be assembled (the task list, plus the sole bus-sense divider, the load-switch
# driver and the cold pull-up, all of which the F8 functions rely on). REQUIRED_FITTED (above) adds every R10 contract
# part and check_actuators' pinned parts.
SAFETY_FITTED = {'R134', 'R126', 'R127', 'R128', 'C126', 'Q124', 'Q120', 'Q121', 'R119', 'R120', 'C120', 'R121', 'Q122',
                 'J400', 'R80', 'R165', 'R122', 'R123', 'J121', 'D120', 'R129', 'R130', 'R131', 'R132', 'R133', 'R173', 'R175', 'R178', 'R180',
                 'C127', 'C128', 'C129',
                 'D402'}      # D-R24-11: J400.2's ESD clamp to GND, ahead of R165 (EN absolute maximum 6.5 V)
REQUIRED_FITTED |= SAFETY_FITTED
RAW = 'RAW_ACT'
ARMED = (RAW, 'PYRO1_IGN', 'PYRO1_OUT')
RAILS = frozenset({'GND', '3V3', '3V3A'})        # net-path searches stop here (a divider foot is not a feed)
MAX_PART_NETS = 4                               # parts with more distinct nets (ICs, U1) do not pass a path
ARMED_SIDE = re.compile(r'^(PYRO1_|ARM1_)')
RAW_SIDE = re.compile(r'^RAW_ACT(_SENSE\w*)?$')
LOAD_SWITCH = {'Q120': ('BAT_IN', 'ACT_FET_S'), 'Q121': ('RAW_ACT', 'ACT_FET_S')}   # (drain, source); gate ACT_GATE
PFET_ROLES = {'S': ('1', '2', '3'), 'G': ('4',), 'D': ('5', '6', '7', '8', '9')}     # AUD-3 AONR21357 (AOS PO-00047).
NFET_ROLES = {'S': ('1', '2', '3'), 'G': ('4',), 'D': ('5',)}                       # AON7524 DFN 3x3 (AOS)
# R20-SAF-02: S-6 also classes the AUX port's nets (D-R19-14) as port nets and the screw-switch / U9 EN chain
# (BAT_ENABLE, BAT_SW_SOURCE / _RETURN: a bridge there latches or bypasses the switch, R19-SAF-02) as protected.
PORT_NET = re.compile(r'^(GPS_|RADIO_|CAM_|PORT_|AUX_)')
SAFE_NET = re.compile(r'^(PYRO1_|ARM1_|ACT_|RAW_ACT|BAT_ENABLE|BAT_SW_)')
MCU_REF = 'U1'
DEFAULT_CLEARANCE = 0.15                       # mm, used only when the board carries no default net class
SERVO_TERMINAL = ('SERVO1_OUT', 'SERVO2_OUT', 'SERVO3_OUT', 'SERVO4_OUT', 'GND')
BOARD_WIDTH, BOARD_MAX = 46.0, 120.0            # P1
WIRE_ENTRY = {'J1': '-x', 'J121': '-x', 'J400': '-x', 'J440': '-x', 'J410': '+x', 'J420': '+x', 'J9': '+x', 'J122': '+x'}  # D-AVA-01: every DB125 shares the wire-room floor
WIRE_ROOM = 6.25                                # mm, R8 / R9 P-11
BOT_THT, BOT_M3 = 1.5, 3.5                      # mm, R9 M-6 without its pyro-via term (a pyro spacing rule)
IMU_LEVER_R10 = -6.0                           # mm: U4 centre x - 23 (roll axis), M3_R10 "IMU axis map" (R4-MEC-05)
IMU_PAD1_R10 = (1.21, -0.75)                   # mm: pad 1 board position from the U4 centre at rotation 180 on the bottom
IMU_ROTATION_R10 = 180.0                        # R9 D-S7-06 kept: U4 bottom, rotation 180
IMU_MAPS = {0.0: 'M3_R5 axis map: +X_imu = +x_board, +Y_imu = +y_board; roll = +gyro_Y',
            180.0: 'R9 D-S7-06 axis map: +X_imu = -x_board, +Y_imu = -y_board; roll = -gyro_Y'}
# D-R19-06: the ONE connector word list. m3_design/r10_post.py places these words in this order and K-legends gates the
# same list; SWITCH (J400) is the last entry, as r10_post placed it before the list was merged.
WORD_LEGENDS_R10 = {'IGN': 'J121', 'BAT': 'J1', 'CAM': 'J9', 'SWD': 'J2', 'SERVO': 'J122',
                    'GPS': 'J410', 'RADIO': 'J420', 'AUX': 'J440', 'SWITCH': 'J400'}   # D-R19-14: AUX at its reviewed spot
TERMINAL_PINS_R10 = (('J121', (('1', 'E1-'), ('2', 'E1+'))),
                     ('J1', (('1', 'BAT+'), ('2', 'GND'))),
                     ('J400', (('1', 'SW'), ('2', 'SW'))),
                     ('J122', (('1', 'S1'), ('2', 'S2'), ('3', 'S3'), ('4', 'S4'), ('5', 'GND'))),
                     ('J9', (('1', '5V4'), ('2', 'GND'), ('3', 'RXI'), ('4', 'TXO'))),
                     ('J410', (('1', '4V8'), ('2', 'GND'), ('3', 'TXO'), ('4', 'RXI'))),
                     ('J420', (('1', '4V8'), ('2', 'GND'), ('3', 'TXO'), ('4', 'RXI'))),
                     ('J440', (('1', '4V8'), ('2', 'GND'), ('3', 'TXO'), ('4', 'RXI'))))   # D-R19-14: identical ports
EPS = 1e-3
# K-reference (R10_DECISIONS D-R2-10): R9's D-S8-17 method on R10's planes.
REF_PLANES_B = ('GND', '3V3', '3V3A', 'PORT_5V3', 'PORT_4V8', 'RAW_PROTECTED')
REF_PAD_ANTIPAD = 0.6          # mm beyond half a plated pad's size: the plane void around a terminal barrel (Inference)
REF_OWN_R = 0.45               # mm: a sample this close to a same-net via centre lies in that via's own antipad
REF_STRAY = [   # (net, layer, x, y, reason): unreferenced samples outside their own via antipads; matched within 0.01 mm
    ('SPI1_MISO', 'B.Cu', 17.7904, 43.8818, "R9's translated IMU fan-out: the edge of SPI1_MISO's 45-degree stub passes "
                                             "SPI1_MOSI's via (17.55, 44.25) antipad at 0.440 mm (edge samples)"),
    ('SPI1_MISO', 'B.Cu', 17.7975, 43.8889, 'as above'),
    ('SPI1_MISO', 'F.Cu', 17.3046, 43.8869, "as above, F.Cu side: SPI1_MOSI's via (17.55, 44.25) at 0.438 mm, its In1 "
                                             "antipad"),
    ('SPI1_SCK', 'B.Cu', 17.1, 43.4, "R9's translated IMU fan-out: SPI1_SCK's B.Cu edge passes SPI1_MISO's via "
                                     "(17.55, 43.5) antipad at 0.461 mm"),
    ('SPI1_SCK', 'B.Cu', 17.1, 43.42, 'as above'),
]
# K-rules (R4-GATE-01): R10 has no pyro-specific rule, so the board default clearance is the only pyro spacing: the
# rules file is pinned (generated by m3_design/r10_sch.py; a reviewed change re-pins it) and the project's design rules
# may not be loosened. Floors are the values set on the accepted R10 project.
# D-R21-01: re-pinned for the three JLC hole rules (JLC_HOLE_TABLE); was 5acf6db7... (round 20)
DRU_SHA256 = '1d2dbe77f0331e4013964ffa0823994c947843c89f5e3886ca36ff2d7e2f0ff9'
PRO_FLOORS = {'min_clearance': 0.15, 'min_track_width': 0.15, 'min_via_diameter': 0.5, 'min_via_annular_width': 0.1,
              'min_through_hole_diameter': 0.3, 'min_hole_clearance': 0.2, 'min_hole_to_hole': 0.25,
              'min_copper_edge_clearance': 0.5, 'min_microvia_diameter': 0.2, 'min_microvia_drill': 0.1,
              # R18-GATE-06: REQUIREMENTS M2's silkscreen legibility floors (>= 1.0 mm text, >= 0.15 mm lines), which
              # DRC's text_height / text_thickness tests hold every silkscreen text to (their severities are pinned
              # below), and the project's silk clearance and thermal-spoke floors
              'min_text_height': 1.0, 'min_text_thickness': 0.15, 'min_silk_clearance': 0.15, 'min_resolved_spokes': 2}
NETCLASS_CLEARANCE_FLOOR = 0.15
# D-R21-01 (R21-PWR-02 / R21-BOM-01 / R21-MFG-01 / R21-GATE-02): JLCPCB's published hole table
# (https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-10-31), pinned so that a re-pinned DRU still cannot drop
# below it: (what, JLC's row, the DRU rule holding it, its layer, its condition (None: any), constraint, JLC minimum mm).
JLC_HOLE_TABLE = (
    ('via hole to inner copper', 'Inner layer via hole to copper clearance 0.2mm', 'General copper to hole clearance',
     None, None, 'hole_clearance', 0.20),
    ('PTH pad hole to inner copper', 'Inner layer PTH pad hole to copper clearance 0.3mm',
     'JLC inner-layer PTH pad hole to copper', 'inner',
     "A.Type == 'Pad' && A.Pad_Type == 'Through-hole' && (B.Type != 'Pad' || B.Pad_Type == 'Through-hole')",
     'hole_clearance', 0.30),
    ('PTH hole to outer track', 'PTH to Track 0.28mm (0.35mm recommended)', 'JLC outer-layer PTH hole to track', 'outer',
     "A.Type == 'Pad' && A.Pad_Type == 'Through-hole'", 'hole_clearance', 0.28),
    ('pad hole to hole', 'Pad Hole-to-Hole Spacing 0.45mm', 'JLC pad hole to hole', None,
     "A.Type == 'Pad' && B.Type == 'Pad'", 'hole_to_hole', 0.45),
)
JLC_HOLE_FLOOR = 0.20          # mm: JLC's least hole figure (via hole to copper, via hole to hole); no hole rule below it
JLC_PTH_INNER = 0.30           # mm: the board itself, every plated pad hole wall to foreign In1 / In2 copper


# D-R22-05 (R22-GATE-01): a constraint minimum may be written in any unit KiCad's rule parser takes and may follow (opt)
# or (max); every one is read and converted to mm, and one that cannot be read fails.
DRU_UNITS_MM = {'mm': 1.0, '': 1.0, 'mil': 0.0254, 'mils': 0.0254, 'thou': 0.0254, 'um': 0.001, 'µm': 0.001,
                'in': 25.4, 'inch': 25.4, '"': 25.4}


def _sexpr_end(text, start):
    """Index of the ')' closing the '(' at `start` (strings skipped)."""
    depth, i = 0, start
    while i < len(text):
        c = text[i]
        if c == '"':
            i = text.index('"', i + 1)
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if not depth:
                return i
        i += 1
    return len(text) - 1


def dru_min_mm(value):
    """A DRU '(min VALUE)' token in mm, or None when it cannot be read (unknown unit, no number)."""
    m = re.fullmatch(r'\s*([+-]?(?:\d+\.?\d*|\.\d+))\s*([A-Za-zµ"]*)\s*', value)
    if not m or m.group(2).lower() not in DRU_UNITS_MM:
        return None
    return float(m.group(1)) * DRU_UNITS_MM[m.group(2).lower()]


def _dru_tokens(text):
    """Tokens of a .kicad_dru text with '#' comments (to the end of the line, outside quoted strings) stripped: '(',
    ')', ('str', text) for a quoted string and ('atom', text) for a bare word (D-R23-05)."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == '#':
            j = text.find('\n', i)
            i = n if j < 0 else j + 1
        elif c in '()':
            out.append(c)
            i += 1
        elif c.isspace():
            i += 1
        elif c == '"':
            j, buf = i + 1, []
            while j < n and text[j] != '"':
                if text[j] == '\\' and j + 1 < n:
                    buf.append(text[j + 1])
                    j += 2
                    continue
                buf.append(text[j])
                j += 1
            if j >= n:
                raise ValueError('an unterminated quoted string')
            out.append(('str', ''.join(buf)))
            i = j + 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()"#':
                j += 1
            out.append(('atom', text[i:j]))
            i = j
    return out


def _dru_tree(tokens):
    """Nested lists of the tokens; ValueError on unbalanced parentheses."""
    stack = [[]]
    for t in tokens:
        if t == '(':
            stack.append([])
        elif t == ')':
            if len(stack) < 2:
                raise ValueError("an unmatched ')'")
            node = stack.pop()
            stack[-1].append(node)
        else:
            stack[-1].append(t)
    if len(stack) != 1:
        raise ValueError("an unclosed '('")
    return stack[0]


def dru_rules(text):
    """[dict(name, layer, condition, mins {constraint: min mm}, bad [unreadable items], severity)] of a .kicad_dru text
    in file order, read as KiCad reads it (D-R22-05 / D-R23-05): '#' comments stripped, rule names and layers quoted or
    bare, every (min ...) in a constraint in any unit and position. Anything that is not a readable rule is a dict with
    name None and its reason in bad."""
    def word(t):
        return t[1] if isinstance(t, tuple) else None
    try:
        tree = _dru_tree(_dru_tokens(text))
    except ValueError as e:
        return [dict(name=None, layer=None, condition=None, mins={}, bad=[f'the DRU cannot be read: {e}'], severity=None)]
    out = []
    for node in tree:
        if not isinstance(node, list) or not node or word(node[0]) not in ('version', 'rule'):
            out.append(dict(name=None, layer=None, condition=None, mins={}, severity=None,
                            bad=[f'an unknown top-level item {node!r:.60}']))
            continue
        if word(node[0]) == 'version':
            continue
        if len(node) < 2 or word(node[1]) is None:
            out.append(dict(name=None, layer=None, condition=None, mins={}, severity=None, bad=['a rule with no name']))
            continue
        rule = dict(name=word(node[1]), layer=None, condition=None, mins={}, bad=[], severity=None)
        for child in node[2:]:
            key = word(child[0]) if isinstance(child, list) and child else None
            arg = word(child[1]) if key and len(child) > 1 else None
            if key == 'layer':
                rule['layer'] = arg
            elif key == 'condition':
                rule['condition'] = arg
            elif key == 'severity':
                rule['severity'] = arg
            elif key == 'constraint' and arg:
                for sub in child[2:]:
                    if isinstance(sub, list) and sub and word(sub[0]) == 'min':
                        raw = ''.join(word(x) or '?' for x in sub[1:])
                        v = dru_min_mm(raw)
                        if v is None:
                            rule['bad'].append(f'{arg} (min {raw})')
                        else:
                            rule['mins'][arg] = min(v, rule['mins'].get(arg, v))
            elif key is None:
                rule['bad'].append(f'an unreadable item {child!r:.60}')
        out.append(rule)
    return out


def dru_layers_meet(pinned, later):
    """True when a rule on layer `later` can apply on some layer of a rule pinned to `pinned` (None = every layer;
    'inner' / 'outer' keywords; named copper layers), so that a later one can override it (D-R22-05)."""
    if pinned is None or later is None:
        return True
    inner = lambda lay: lay == 'inner' or re.fullmatch(r'In\d+\.Cu', lay) is not None         # noqa: E731
    outer = lambda lay: lay in ('outer', 'F.Cu', 'B.Cu')                                       # noqa: E731
    if inner(pinned):
        return inner(later) and (pinned == 'inner' or later in ('inner', pinned))
    if outer(pinned):
        return outer(later) and (pinned == 'outer' or later in ('outer', pinned))
    return True


# D-R23-07 (R23-GATE-03): every DRU minimum is floored, not only the hole rows: at the project's .kicad_pro floor where
# it is stricter than JLC's table (https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-11-01: multilayer trace /
# space 0.09 / 0.09 mm, via 0.15 / 0.25 mm, board-edge copper 0.2 mm), else at JLC's. A constraint with a minimum and no
# floor here fails until one is added; a rule severity other than error fails.
DRU_FLOORS = {'clearance': 0.15, 'track_width': 0.15, 'edge_clearance': 0.5, 'annular_width': 0.1, 'via_diameter': 0.5,
              'hole_size': 0.3, 'hole_clearance': 0.20, 'hole_to_hole': 0.25, 'text_height': 1.0,
              'text_thickness': 0.15, 'silk_clearance': 0.15, 'thermal_relief_gap': 0.15, 'thermal_spoke_width': 0.15,
              'physical_clearance': 0.15, 'physical_hole_clearance': 0.20, 'diff_pair_gap': 0.15,
              'courtyard_clearance': 0.0}


def jlc_hole_table(text, table=JLC_HOLE_TABLE, floor=JLC_HOLE_FLOOR, floors=None):
    """(issues, evidence): each JLC row's DRU rule exists once, with its pinned layer and condition and a minimum at
    least JLC's; no later rule able to apply on any of its layers (KiCad lets the last matching rule win; named layers
    and keywords both count) sets that constraint below JLC's figure; no hole rule anywhere is below JLC's least hole
    figure; every constraint minimum is readable (any unit, any position) and at least its DRU_FLOORS floor; no rule
    sets a severity other than error; nothing in the DRU is unreadable (D-R23-05 / -07)."""
    floors = DRU_FLOORS if floors is None else floors
    rules = dru_rules(text)
    issues, ev = [], []
    for r in rules:
        issues += [f'JLC table: DRU rule "{r["name"]}" has an unreadable minimum {b!r}' if r['name'] else
                   f'JLC table: the DRU holds {b}, which K-rules cannot read as a rule' for b in r['bad']]
    named = [r for r in rules if r['name']]
    for what, row, name, layer, cond, constraint, need in table:
        hits = [i for i, r in enumerate(named) if r['name'] == name]
        if len(hits) != 1:
            issues.append(f'JLC table: {what} ("{row}") needs one DRU rule "{name}", found {len(hits)}')
            continue
        i = hits[0]
        r = named[i]
        value = r['mins'].get(constraint)
        ev.append(dict(what=what, jlc=row, rule=name, constraint=constraint, min_mm=value, jlc_min_mm=need))
        if r['layer'] != layer or r['condition'] != cond:
            issues.append(f'JLC table: DRU rule "{name}" has layer {r["layer"]} and condition {r["condition"]!r}, not the '
                          f'pinned {layer} and {cond!r} ({what})')
        if value is None or value < need - 1e-9:
            issues.append(f'JLC table: DRU rule "{name}" {constraint} min {value} mm is below JLC\'s {need} mm ({what}: '
                          f'"{row}")')
        for later in named[i + 1:]:
            v = later['mins'].get(constraint)
            if v is not None and v < need - 1e-9 and dru_layers_meet(layer, later['layer']):
                issues.append(f'JLC table: DRU rule "{later["name"]}" ({constraint} min {v:.4g} mm on layer '
                              f'{later["layer"]}) follows "{name}" and can override JLC\'s {need} mm ({what})')
    for r in named:
        for constraint in ('hole_clearance', 'hole_to_hole'):
            v = r['mins'].get(constraint)
            if v is not None and v < floor - 1e-9:
                issues.append(f'JLC table: DRU rule "{r["name"]}" {constraint} min {v:.4g} mm is below JLC\'s {floor} mm '
                              'hole figure')
        for constraint, v in sorted(r['mins'].items()):
            least = floors.get(constraint)
            if least is None:
                issues.append(f'DRU floors: rule "{r["name"]}" sets {constraint} (min {v:.4g} mm) and DRU_FLOORS has no '
                              'floor for it (R23-GATE-03)')
            elif v < least - 1e-9:
                issues.append(f'DRU floors: rule "{r["name"]}" {constraint} min {v:.4g} mm is below the {least} mm floor '
                              '(R23-GATE-03)')
        if r['severity'] not in (None, 'error'):
            issues.append(f'DRU floors: rule "{r["name"]}" sets severity {r["severity"]}; only error is allowed '
                          '(R23-GATE-03)')
    return issues, ev


def _copper_items(board, layers, err=None):
    """{layer: [(net, item UUID, shape, bbox, label)]}: every copper item on each of `layers`, taken from copper_nodes
    (S-8's set, D-R23-06): pads (copper where flashed, else the plated barrel; an NPTH hole is no copper), tracks, vias
    (pad where flashed, else the barrel), board and footprint fill pieces, copper drawings and copper text. Shapes are
    KiCad SHAPEs or polygon sets; both measure SquaredDistance to a point."""
    import pcbnew
    want = set(layers)
    items = {lay: [] for lay in layers}
    names = {lay: board.GetLayerName(lay) for lay in layers}
    for key, lay, shape, bb, pad, net, label in copper_nodes(board):
        if lay not in want:
            continue
        if pad is not None and pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and not pad.FlashLayer(lay):
            continue
        if label.endswith(f' fill on {names[lay]}'):
            label = label[:-len(f' on {names[lay]}')]                 # 'GND fill', as the messages always read
        box = pcbnew.BOX2I(pcbnew.VECTOR2I(bb[0], bb[1]), pcbnew.VECTOR2L(bb[2] - bb[0], bb[3] - bb[1]))
        items[lay].append((net, key.split('/')[0], shape, box, label))
    return items


def _hole_points(pad, err):
    """The points of `pad`'s hole outline (its true slot or circle), copied out of the polygon (CPoint returns a reference
    into it, which dies with it), and its bbox."""
    import pcbnew
    hole = pcbnew.SHAPE_POLY_SET()
    pad.TransformHoleToPolygon(hole, 0, err, pcbnew.ERROR_INSIDE)
    pts = []
    for i in range(hole.OutlineCount()):
        o = hole.Outline(i)
        for k in range(o.PointCount()):
            q = o.CPoint(k)
            pts.append(pcbnew.VECTOR2I(int(q.x), int(q.y)))
    bb = hole.BBox()
    return pts, pcbnew.BOX2I(pcbnew.VECTOR2I(bb.GetX(), bb.GetY()), pcbnew.VECTOR2L(bb.GetWidth(), bb.GetHeight()))


def _nearest(items, pts, box, skip):
    """(squared distance in nm^2, label) of the nearest of `items` (layer list from _copper_items) to `pts`, among
    those whose bbox meets `box` and for which skip(net, uid) is false; None when there is none."""
    best = None
    for net, uid, ps, bb, what in items:
        if skip(net, uid) or not bb.Intersects(box):
            continue
        d = min(ps.SquaredDistance(q) for q in pts)
        if best is None or d < best[0]:
            best = (d, what)
    return best


def pth_inner_copper(board, floor=JLC_PTH_INNER, reach=1.0):
    """(issues, {pad: {layer: (mm, nearest)}}): every plated through-hole pad's hole wall to the nearest copper of
    another net on each inner layer (fill pieces, tracks, via pads or barrels, pads or plated barrels), measured on the
    board (D-R21-01: JLC's 0.3 mm, whatever the DRU says); copper over `reach` mm away is not measured."""
    import pcbnew
    inner = [lay for lay in board.GetEnabledLayers().CuStack() if lay not in (pcbnew.F_Cu, pcbnew.B_Cu)]
    err = pcbnew.FromMM(0.001)
    items = _copper_items(board, inner, err)
    issues, ev = [], {}
    margin = pcbnew.FromMM(reach)
    for f in sorted(board.GetFootprints(), key=lambda g: g.GetReference()):
        for p in f.Pads():
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
                continue
            pts, box = _hole_points(p, err)
            box.Inflate(margin)
            label = f'{f.GetReference()}.{p.GetNumber()}'
            for lay in inner:
                best = _nearest(items[lay], pts, box,
                                lambda net, uid, p=p: net == p.GetNetname() or uid == p.m_Uuid.AsString())
                if best is None:
                    continue
                dist = round(pcbnew.ToMM(int(math.sqrt(best[0]))), 3)
                ev.setdefault(label, {})[board.GetLayerName(lay)] = (dist, best[1])
                if dist < floor - 1e-6:
                    issues.append(f'JLC table: the {label} ({p.GetNetname()}) hole wall is {dist:.3f} mm from '
                                  f'{best[1]} on {board.GetLayerName(lay)}, under JLC\'s {floor} mm inner-layer PTH '
                                  'pad hole to copper')
    return issues, ev


# D-R22-01 (R22-REQUIREMENTS-02): the rest of JLC's hole, ring and NPTH rows, measured on the board whatever the DRU says
# (https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-10-31):
# - "PTH annular ring >=0.20mm" (multilayer, 1 oz: 0.20 mm recommended, 0.15 mm absolute minimum): held at 0.20 mm;
# - "Via diameter should be 0.1mm (0.15mm preferred) larger than Via hole size": a 0.05 mm via ring;
# - multilayer drill 0.15 - 6.3 mm, vias 0.15 mm hole / 0.25 mm diameter: every plated hole >= 0.15 mm;
# - "Min. Non-plated holes 0.50mm"; "NPTH pad annular ring >=0.45mm" (only where an NPTH pad carries copper);
# - "NPTH to Track 0.2mm": every NPTH hole wall >= 0.2 mm from any copper on any layer. J3's NPTH locating holes sit
#   0.200 mm from its GND SMD lands (HRO's land pattern, at the limit, not below: the DRU's "HRO M-12 internal SMD lands
#   to locating holes" rule sets that pair's DRC clearance to 0.20 mm, K-lands pins the footprint, and this check holds
#   the board to it within JLC_HOLE_TOL).
# D-R22-05 (R22-GATE-01): three more rows measured on the board, so a DRU edit cannot hide them: "Inner layer via hole
# to copper clearance 0.2mm" with "Via hole to Track 0.2mm" (every via hole wall >= 0.2 mm from foreign copper on every
# layer), "PTH to Track 0.28mm" (every PTH pad hole wall >= 0.28 mm from foreign copper on F.Cu / B.Cu) and "Pad
# Hole-to-Hole Spacing 0.45mm" (every pair of pad holes, plated or not, >= 0.45 mm wall to wall).
JLC_BOARD_HOLES = dict(pth_ring=0.20, via_ring=0.05, plated_hole=0.15, npth_hole=0.50, npth_ring=0.45,
                       npth_to_copper=0.20, via_hole_to_copper=0.20, pth_hole_to_outer_copper=0.28, pad_hole_to_hole=0.45)
JLC_HOLE_TOL = 0.001           # mm: polygon approximation (1 um arcs) of the measured shapes


def _seg_dist(a, b, c, d):
    """Distance (mm) between segments ab and cd (points as (x, y) mm)."""
    def pt(p, s, e):
        dx, dy = e[0] - s[0], e[1] - s[1]
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - s[0]) * dx + (p[1] - s[1]) * dy) / L2))
        return math.hypot(p[0] - s[0] - t * dx, p[1] - s[1] - t * dy)

    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    if a != b and c != d and cross(a, b, c) * cross(a, b, d) < 0 and cross(c, d, a) * cross(c, d, b) < 0:
        return 0.0
    return min(pt(a, c, d), pt(b, c, d), pt(c, a, b), pt(d, a, b))


def _pad_ring(pad, lay, err):
    """The annular ring (mm) of `pad` on `lay`: the least distance from its hole (the true slot or circle) to its copper
    outline."""
    import pcbnew
    hole = pad.GetEffectiveHoleShape()
    seg, radius = hole.GetSeg(), pcbnew.ToMM(hole.GetWidth()) / 2
    axis = ((pcbnew.ToMM(seg.A.x), pcbnew.ToMM(seg.A.y)), (pcbnew.ToMM(seg.B.x), pcbnew.ToMM(seg.B.y)))
    ps = pcbnew.SHAPE_POLY_SET()
    pad.TransformShapeToPolygon(ps, lay, 0, err, pcbnew.ERROR_INSIDE)
    best = None
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        pts = [(pcbnew.ToMM(o.CPoint(k).x), pcbnew.ToMM(o.CPoint(k).y)) for k in range(o.PointCount())]
        for k in range(len(pts)):
            d = _seg_dist(axis[0], axis[1], pts[k], pts[(k + 1) % len(pts)]) - radius
            best = d if best is None else min(best, d)
    return best


def jlc_board_holes(board, figs=None, tol=JLC_HOLE_TOL, reach=1.0):
    """(issues, evidence): D-R22-01, the board against JLC's ring, hole-size and NPTH rows (JLC_BOARD_HOLES)."""
    import pcbnew
    figs = JLC_BOARD_HOLES if figs is None else figs
    err, ring_err = pcbnew.FromMM(0.001), pcbnew.FromMM(0.0001)    # rings: 0.1 um arcs (J3's 0.200 mm sits at 0.20)
    cu = list(board.GetEnabledLayers().CuStack())
    issues, least = [], {}

    def note(key, value, where):
        if key not in least or value < least[key][0]:
            least[key] = (round(value, 3), where)
    for f in sorted(board.GetFootprints(), key=lambda g: g.GetReference()):
        for p in f.Pads():
            attr = p.GetAttribute()
            if attr not in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                continue
            label = (f'{f.GetReference()}.{p.GetNumber()}' if attr == pcbnew.PAD_ATTRIB_PTH else
                     f'{f.GetReference()} NPTH ({pcbnew.ToMM(p.GetPosition().x):.2f}, {pcbnew.ToMM(p.GetPosition().y):.2f})')
            drill = pcbnew.ToMM(min(p.GetDrillSize().x, p.GetDrillSize().y))
            flashed = [lay for lay in cu if p.FlashLayer(lay)]
            if attr == pcbnew.PAD_ATTRIB_PTH:
                note('plated_hole', drill, label)
                if drill < figs['plated_hole'] - tol:
                    issues.append(f'JLC holes: {label} plated hole {drill:.3f} mm is under JLC\'s {figs["plated_hole"]} '
                                  'mm minimum')
                for lay in flashed:
                    ring = _pad_ring(p, lay, ring_err)
                    note('pth_ring', ring, f'{label} {board.GetLayerName(lay)}')
                    if ring < figs['pth_ring'] - tol:
                        issues.append(f'JLC holes: {label} annular ring {ring:.3f} mm on {board.GetLayerName(lay)} is '
                                      f'under JLC\'s {figs["pth_ring"]} mm PTH annular ring')
            else:
                note('npth_hole', drill, label)
                if drill < figs['npth_hole'] - tol:
                    issues.append(f'JLC holes: {label} non-plated hole {drill:.3f} mm is under JLC\'s '
                                  f'{figs["npth_hole"]} mm minimum')
                for lay in flashed:
                    ring = _pad_ring(p, lay, ring_err)
                    note('npth_ring', ring, f'{label} {board.GetLayerName(lay)}')
                    if ring < figs['npth_ring'] - tol:
                        issues.append(f'JLC holes: {label} NPTH pad ring {ring:.3f} mm on {board.GetLayerName(lay)} is '
                                      f'under JLC\'s {figs["npth_ring"]} mm')
    for v in board.GetTracks():
        if v.GetClass() != 'PCB_VIA':
            continue
        at = f'via {v.GetNetname()} ({pcbnew.ToMM(v.GetPosition().x):.2f}, {pcbnew.ToMM(v.GetPosition().y):.2f})'
        drill = pcbnew.ToMM(v.GetDrillValue())
        note('plated_hole', drill, at)
        if drill < figs['plated_hole'] - tol:
            issues.append(f'JLC holes: {at} hole {drill:.3f} mm is under JLC\'s {figs["plated_hole"]} mm minimum')
        for lay in cu:
            if v.FlashLayer(lay):
                ring = (pcbnew.ToMM(v.GetWidth(lay)) - drill) / 2
                note('via_ring', ring, f'{at} {board.GetLayerName(lay)}')
                if ring < figs['via_ring'] - tol:
                    issues.append(f'JLC holes: {at} ring {ring:.3f} mm on {board.GetLayerName(lay)} is under JLC\'s '
                                  f'{figs["via_ring"]} mm (via diameter 0.1 mm over the hole)')
    items = _copper_items(board, cu, err)
    margin = pcbnew.FromMM(reach)
    outer = [lay for lay in cu if lay in (pcbnew.F_Cu, pcbnew.B_Cu)]
    for v in board.GetTracks():                                      # D-R22-05: via hole wall to foreign copper
        if v.GetClass() != 'PCB_VIA':
            continue
        c, r = v.GetPosition(), v.GetDrillValue() / 2
        centre = [pcbnew.VECTOR2I(int(c.x), int(c.y))]               # a round hole: wall gap = centre gap - radius
        box = pcbnew.BOX2I(pcbnew.VECTOR2I(int(c.x - r), int(c.y - r)), pcbnew.VECTOR2L(int(2 * r), int(2 * r)))
        box.Inflate(margin)
        at = f'via {v.GetNetname()} ({pcbnew.ToMM(c.x):.2f}, {pcbnew.ToMM(c.y):.2f})'
        for lay in cu:
            best = _nearest(items[lay], centre, box,
                            lambda net, uid, v=v: net == v.GetNetname() or uid == v.m_Uuid.AsString())
            if best is None:
                continue
            dist = pcbnew.ToMM(int(math.sqrt(best[0]) - r))
            note('via_hole_to_copper', dist, f'{at} to {best[1]} on {board.GetLayerName(lay)}')
            if dist < figs['via_hole_to_copper'] - tol:
                issues.append(f'JLC holes: {at} hole wall is {dist:.3f} mm from {best[1]} on {board.GetLayerName(lay)}, '
                              f'under JLC\'s {figs["via_hole_to_copper"]} mm via hole to copper')
    holes = []
    for f in sorted(board.GetFootprints(), key=lambda g: g.GetReference()):
        for p in f.Pads():
            if p.GetAttribute() not in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                continue
            h = p.GetEffectiveHoleShape()
            seg = h.GetSeg()
            label = (f'{f.GetReference()}.{p.GetNumber()}' if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else
                     f'{f.GetReference()} NPTH ({pcbnew.ToMM(p.GetPosition().x):.2f}, {pcbnew.ToMM(p.GetPosition().y):.2f})')
            holes.append((label, ((pcbnew.ToMM(seg.A.x), pcbnew.ToMM(seg.A.y)), (pcbnew.ToMM(seg.B.x), pcbnew.ToMM(seg.B.y))),
                          pcbnew.ToMM(h.GetWidth()) / 2))
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
                continue
            pts, box = _hole_points(p, err)                           # D-R22-05: PTH hole wall to outer copper
            box.Inflate(margin)
            for lay in outer:
                best = _nearest(items[lay], pts, box,
                                lambda net, uid, p=p: net == p.GetNetname() or uid == p.m_Uuid.AsString())
                if best is None:
                    continue
                dist = pcbnew.ToMM(int(math.sqrt(best[0])))
                note('pth_hole_to_outer_copper', dist, f'{label} to {best[1]} on {board.GetLayerName(lay)}')
                if dist < figs['pth_hole_to_outer_copper'] - tol:
                    issues.append(f'JLC holes: {label} hole wall is {dist:.3f} mm from {best[1]} on '
                                  f'{board.GetLayerName(lay)}, under JLC\'s {figs["pth_hole_to_outer_copper"]} mm PTH to track')
    for i, (la, sa, ra) in enumerate(holes):                          # D-R22-05: pad hole to pad hole
        for lb, sb, rb in holes[i + 1:]:
            gap = _seg_dist(sa[0], sa[1], sb[0], sb[1]) - ra - rb
            note('pad_hole_to_hole', gap, f'{la} to {lb}')
            if gap < figs['pad_hole_to_hole'] - tol:
                issues.append(f'JLC holes: {la} and {lb} holes are {gap:.3f} mm apart, under JLC\'s '
                              f'{figs["pad_hole_to_hole"]} mm pad hole to hole')
    npth = [(f, p) for f in board.GetFootprints() for p in f.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
    if npth:
        for f, p in sorted(npth, key=lambda fp: (fp[0].GetReference(), fp[1].GetPosition().x, fp[1].GetPosition().y)):
            pts, box = _hole_points(p, err)
            box.Inflate(margin)
            label = (f'{f.GetReference()} NPTH ({pcbnew.ToMM(p.GetPosition().x):.2f}, '
                     f'{pcbnew.ToMM(p.GetPosition().y):.2f})')
            for lay in cu:
                best = _nearest(items[lay], pts, box, lambda net, uid, p=p: uid == p.m_Uuid.AsString())
                if best is None:
                    continue
                dist = pcbnew.ToMM(int(math.sqrt(best[0])))
                note('npth_to_copper', dist, f'{label} to {best[1]} on {board.GetLayerName(lay)}')
                if dist < figs['npth_to_copper'] - tol:
                    issues.append(f'JLC holes: {label} is {dist:.3f} mm from {best[1]} on {board.GetLayerName(lay)}, '
                                  f'under JLC\'s {figs["npth_to_copper"]} mm NPTH to track')
    return issues, dict(figures=figs, least=least)


def k_rules(ctx):
    """m3.kicad_dru pinned by SHA-256 and the .kicad_pro design rules not loosened (pyro safety rests on them)."""
    issues, ev = [], {}
    dru = ctx.dru
    if ctx.board_path and Path(ctx.board_path).with_suffix('.kicad_dru').is_file():
        dru = Path(ctx.board_path).with_suffix('.kicad_dru').read_bytes().decode('utf-8')
    if dru is None:
        issues.append('K-rules: m3.kicad_dru not readable next to the board')
    else:
        actual = hashlib.sha256(dru.encode('utf-8')).hexdigest()
        ev['dru_sha256'] = actual
        ev['dru_sha256_expected'] = DRU_SHA256
        if actual != DRU_SHA256:
            issues.append(f'K-rules: m3.kicad_dru SHA-256 {actual} is not the pinned {DRU_SHA256} (a reviewed change '
                          're-pins DRU_SHA256 in tools/check_r10.py)')
        table, ev['jlc_hole_table'] = jlc_hole_table(dru)                 # D-R21-01
        issues += [f'K-rules: {i}' for i in table]
    if ctx.board is not None:
        walls, ev['pth_inner_copper_mm'] = pth_inner_copper(ctx.board)    # D-R21-01: the board itself
        issues += [f'K-rules: {i}' for i in walls]
        holes, ev['jlc_board_holes'] = jlc_board_holes(ctx.board)        # D-R22-01: rings, hole sizes, NPTH
        issues += [f'K-rules: {i}' for i in holes]
    bp = ctx.board_path
    pro = Path(bp).with_suffix('.kicad_pro') if bp else None
    if pro is None or not pro.is_file():
        issues.append('K-rules: the .kicad_pro next to the board is not readable')
        return issues, ev
    project = json.loads(pro.read_text())
    design = project.get('board', {}).get('design_settings', {})
    rules = design.get('rules', {})
    ev['pro_rules'] = {k: rules.get(k) for k in PRO_FLOORS}
    for key, floor in PRO_FLOORS.items():
        value = rules.get(key)
        if not isinstance(value, (int, float)) or value < floor - 1e-9:
            issues.append(f'K-rules: .kicad_pro design rule {key} = {value}, floor {floor} mm')
    classes = project.get('net_settings', {}).get('classes', [])
    ev['netclass_clearance'] = {c.get('name'): c.get('clearance') for c in classes}
    if not any(c.get('name') == 'Default' for c in classes):
        issues.append('K-rules: .kicad_pro has no Default net class')
    for c in classes:
        value = c.get('clearance')
        if not isinstance(value, (int, float)) or value < NETCLASS_CLEARANCE_FLOOR - 1e-9:
            issues.append(f'K-rules: net class {c.get("name")} clearance {value}, floor {NETCLASS_CLEARANCE_FLOOR} mm')
    ignored = sorted(k for k, v in design.get('rule_severities', {}).items() if v == 'ignore')
    ev['ignored_severities'] = ignored
    if ignored:
        issues.append(f'K-rules: DRC rule severities set to ignore: {ignored}')
    if design.get('drc_exclusions'):
        issues.append(f'K-rules: {len(design["drc_exclusions"])} DRC exclusions in the project')
    return issues, ev


# K-lands (R18-GATE-09): every footprint on the board comes from the project library (kilib/rocket.pretty, the only
# fp-lib-table entry). m3_design/r10_parts.py generates and pins its own (r10_parts --check); every other footprint the
# board uses is pinned here by the SHA-256 of its .kicad_mod file, so a land cannot drift by a consistent library +
# board edit: DRC's lib_footprint_mismatch (its severity pinned by K-rules) holds each placed copy to its library file.
# A reviewed land change re-pins its hash here; an entry no board footprint uses fails as stale.
FP_LIB_TABLE = [('rocket', '${KIPRJMOD}/kilib/rocket.pretty')]
FOOTPRINT_SHA256 = {
    'C0402': '6f69519a1386d08f592568670b3e5c0fe6d1ba01dec9b5786223e54762071960',
    'C0603': '7a5581f344f2e34bb9308a7be8ca5d26a895ea3260c8f3c2295489362c20d063',
    'C0805': '432e7edf7e5133ca9d7aa15fc6c55cbc65593f4c08ccd9144d266fcc4e41d4a7',
    'CRYSTAL-SMD_4P-L3.2-W2.5-BL': 'fdcb29ea9e045dd33896e43d95af3ffb8bce18fb8514fadda95bbe61057f04ba',
    'C_0603_1608Metric': '0251702c5ef3ff198866cca35d5300451e7e7585a77b82cb44801a9b10a5a02b',
    'C_1206_3216Metric': '50e88542e624c4b1625f73dae6c81cce3e1ffee306df17bf593ead99336fe7ca',
    'D_SMA': '692d3772ebc920ae2b7098332d02fce3d84007a4c47731a6eac8972a10e6ee4b',
    'D_SMB': '9383b37ca55f68f235c4e318d579e3368cc90994d5ac980abf8b51d69a8aa157',
    'IND-SMD_L4.0-W4.0': 'cd3d02453778dec7faa4e2773dbea0a2cd0b82b0747da3a4d54301ff0c625ca8',
    'LGA-14_L3.0-W2.5-P0.50-TL': 'c2bb89583600b3c6816e5651634f68e5e3d3b94a6fc1002b120486c7de1a56f6',
    'LQFP-100_L14.0-W14.0-P0.50-LS16.0-BL': '15b636529f9ba8afa17683a2a65c38b363e299e17254ae84c1ec35c4d7c64616',
    'M3_AON7524_DFN3x3A': '4442bf5999c46d815f38f6a5e2c163bb656bab50b4e1e0a6c7d08e521828f8dc',
    'M3_AP63200_TSOT26': '48764b1dbaa9dfce43c5061873ea446ff6a609d1fa12b6bb1c5862791bb25df9',
    'M3_GRM32_1210': 'd48373a1bf4d58da61c6c10711d034fe136a50b03317b0b0989f72445fae05ab',
    'M3_KT0805Y_A1': 'eb7e7b88bb21f08965bee9711a2d995b8655f3758d185ca90bcec821ebac5d3a',
    'M3_MLT5020_3pad': '11a0283a35c5d4e76de3cdc5bfba203f7c311bbf1a35bd6b264f6d5d9f26aef3',
    'M3_NCD0805R1_K1': '36d4b1cd250111db5c9e39ab49a8f8e50279af5783e3eaf0322666d89dfd23cf',
    'M3_R2512_UR': '4f5de32a3dd228be34b87daa4cd6ff46ff440f48e49feb695a575e8e7f074e92',
    'M3_TC2030_IDC_NL': '495529665d0ad5b09450699c52ac9cd2ab3767201c944c3e4b526de778df959b',
    'M3_TPS2121_RUX': 'd751482f04f3c6fe97ec9ddf3f10f61a00b968119da742c181db78790095fed5',
    'M3_TPS2553_DBV': 'bbecbdd55508b35943db71587e6ae427298620736b54659e5da827085e39b780',
    'M3_TPS25947_RPW': '0a9b347447f75e721fc899c3fc144abdea0f94da9a88dc9fb3b387361db7a842',
    'M3_TPS709_DBV': 'f75e69628079ee074af6e8fc4c660359c8f9284e07d1ff0986c5ca31715ad310',
    'M3_TSLP_2_20': 'db7aecba7f11006ec5cbb3581430e929fff34d9f0b3a52b1179f6b2b50846ad8',
    'M3_TXU0202_DCU': '92898e4be4ea10e52d9c95c2a0dc126a28f657e9702473b8d9f6b61f2f25923d',
    'M3_TestPad_1.5': '5edadc3a1073680d29c01ca0c6543475da9525892d54708404748d26169fa7d8',
    'R0402': '4ff8d61577e514db51ead9d834f53d57bb987c9eaec740cf4ea716091542ea68',
    'R0805': '3e8a4fb5d9d2e62b5e39840430c76a975be4f87c71e1719148403c0fde6ea3fe',
    'R2512': 'ede2ca0c4fe17825c05c7fcee8d9f5e95c9d431a71efc678a0a4e2bd62de63f7',
    'R_0603_1608Metric': 'b080117cac7e57ba1ac288ef9c3f015642787100362d72409072816d7dabe2d1',
    'SENSORS-SMD_MS5611-01BA03': '57d51041fad642e6b60027b5cabf06f2e1fe13c7c5b9c6c2f6dacdb58f5edd61',
    'SOD-323_L1.8-W1.3-LS2.5-RD': '2e6c2fe27766305768e5f2bed90117f25a5e31efa45bc2735ec00226fbe8a0bd',
    'SOIC-8_L5.3-W5.3-P1.27-LS8.0-BL': '62e3f47977328744d35a2c980b166e758dcfe32e76cfc402ea25389f0dfa1d84',
    'SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR': '560574e78cd85152bbf9c38e4a8e6997e3ba74eca8c57d556db4c523c85e7a0d',
    'SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL': '448c89fa3a8f53810be2c986bedc11a06277204c88de6ccd372e8ce5b8c46f8f',
    'TSOT-26_L2.9-W1.6-P0.95-LS2.8-BL': '5442069ef675d8aa52c12eec21bd8398a3ed7269c2a3acc393707d796ac21b03',
    'USB-C_SMD-TYPE-C-31-M-12_1': 'f77f08eb642c6ec21933dc0cf3e2e4866e5b54717d8f1c237a4159bbdc6e8ce6',
}

# OQ-1 accepted by the owner 2026-10-28; physical fit remains outstanding.
WIRE_ROOM_R10 = 4.95

# S-8 barrels (R3-SAF-01); the former PYRO1_BUS is now RAW_ACT. R18-SAF-01 / R18-GATE-01 (D-R18-04) add the load-switch
# gate drive and the arming-switch enable chain. GND is hazardous for the P-FET gate drive (a short from ACT_GATE /
# ACT_DRV to GND turns Q120 / Q121 on with PC1 low) and, D-R19-01 (R19-SAF-01), for PYRO1_OUT, Q124's drain: OUT to GND
# bypasses the fire FET and fires the match once the bus is enabled. GND on the N-FET gate or the enable chain (U9 EN,
# J400.2, Q122's gate and its MCU pin) holds them off; GND on RAW_ACT or PYRO1_IGN shorts the bus (through R134 for IGN)
# without driving current through the igniter.
BARREL_NETS = ('RAW_ACT', 'PYRO1_IGN', 'PYRO1_OUT', 'PYRO1_GATE', 'ACT_GATE', 'ACT_DRV', 'BAT_ENABLE', 'BAT_SW_RETURN',
               'ACT_EN', 'ACT_EN_MCU', 'PYRO1_GATE_N')
BARREL_GND_HAZARD = frozenset({'ACT_GATE', 'ACT_DRV', 'PYRO1_OUT'})
BARREL_GAP = 1.0                # mm, plated barrel wall to foreign In1 / In2 copper
# S-9 (R3-GATE-07): the current path between its power terminals. AUD-6 sets RAW_ACT / IGN / OUT to 0.5 mm;
# audit 2 item 3 adds pulsed ACT_FET_S. BAT_IN retains 1.0 mm; the seven named source bridges remain measured.
FIRE_MIN_W = 1.0                # mm
FIRE_ONLY = frozenset({'RAW_ACT', 'PYRO1_IGN', 'PYRO1_OUT', 'ACT_FET_S'})
FIRE_TERMINALS = {
    'PYRO1_IGN': ({'R134': ('1',)}, {'J121': ('2',)}),
    'PYRO1_OUT': ({'J121': ('1',)}, {'Q124': ('5',)}),
    'RAW_ACT': ({'Q121': ('5', '6', '7', '8', '9')}, {'R134': ('2',)}),
    'ACT_FET_S': ({'Q120': ('1', '2', '3')}, {'Q121': ('1', '2', '3')}),
    'BAT_IN': ({'J1': ('1',)}, {'Q120': ('5', '6', '7', '8', '9')}),
}
# Named narrow fire-path copper (net, layer, width mm, length mm, (x0, y0, x1, y1) ends sorted):
# the ACT_FET_S bridge between the facing sources of Q120 / Q121 (AUD-3 AONR21357 source pins 1-3 at 0.65 mm pitch, 0.35 mm
# wide; a 0.4 mm leg from each pin to a 0.4 mm bar). Adiabatic rise of a 0.4 mm x 35 um outer track carrying the whole
# 4.2 A pulse for 20 ms (Inference, upper bound: the six legs share it): J = 4.2 A / 1.4e-8 m^2 = 3.0e8 A/m^2;
# dT = J^2 rho t / (rho_d c) = 9.0e16 x 1.72e-8 x 0.02 / (8960 x 385) = 9.0 K; at GAP-5's 36 ms fault ceiling,
# 16.2 K (Inference, adiabatic). Matched within 0.01 mm; a narrower, longer or moved segment fails.
FIRE_NARROW = [
    # AUD-3: AONR21357's 0.65mm source pitch; D-AVA-01 translates the identical bridge +1 mm in y.
    ('ACT_FET_S', 'B.Cu', 0.4, 1.95, (12.525, 71.1, 14.475, 71.1), 'AONR21357 source bridge bar'),
    ('ACT_FET_S', 'B.Cu', 0.4, 1.1, (12.525, 71.1, 12.525, 72.2), 'Q120.1 source leg'),
    ('ACT_FET_S', 'B.Cu', 0.4, 1.1, (13.175, 71.1, 13.175, 72.2), 'Q120.2 source leg'),
    ('ACT_FET_S', 'B.Cu', 0.4, 1.1, (13.825, 71.1, 13.825, 72.2), 'Q120.3 source leg'),
    ('ACT_FET_S', 'B.Cu', 0.4, 1.1, (14.475, 70., 14.475, 71.1), 'Q121.1 source leg'),
    ('ACT_FET_S', 'B.Cu', 0.4, 1.1, (13.825, 70., 13.825, 71.1), 'Q121.2 source leg'),
    ('ACT_FET_S', 'B.Cu', 0.4, 1.1, (13.175, 70., 13.175, 71.1), 'Q121.3 source leg'),
]

# K-loader (R3-MCU-01). AN2606 Rev 64 (September 2024) Table 119 "STM32H74xxx/75xxx configuration in system memory boot
# mode", pp. 277-280 (https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-
# mode-stmicroelectronics.pdf; R8 cited the same table as Rev 70 Table 135, pp. 320-323): port -> (interface pin, how
# the loader uses it). 'out' = driven push-pull, 'od' = open-drain I/O (can drive low), 'in' = input ('in-pu' with the
# loader's pull-up). PF0 / PF1 (I2C2), PI0-PI3 (SPI2) and PH13 / PH14 (FDCAN1) are not on the LQFP100 package.
LOADER_H74X = {
    'PA9': ('USART1_TX', 'out'), 'PA10': ('USART1_RX', 'in-pu'), 'PB14': ('USART1_TX (PB14/PB15 map)', 'out'),
    'PB15': ('USART1_RX (PB14/PB15 map)', 'in-pu'), 'PA2': ('USART2_TX', 'out'), 'PA3': ('USART2_RX', 'in-pu'),
    'PB10': ('USART3_TX', 'out'), 'PB11': ('USART3_RX', 'in-pu'), 'PB6': ('I2C1_SCL', 'od'), 'PB9': ('I2C1_SDA', 'od'),
    'PF1': ('I2C2_SCL', 'od'), 'PF0': ('I2C2_SDA', 'od'), 'PA8': ('I2C3_SCL', 'od'), 'PC9': ('I2C3_SDA', 'od'),
    'PA7': ('SPI1_MOSI', 'in'), 'PA6': ('SPI1_MISO', 'out'), 'PA5': ('SPI1_SCK', 'in'), 'PA4': ('SPI1_NSS', 'in'),
    'PI3': ('SPI2_MOSI', 'in'), 'PI2': ('SPI2_MISO', 'out'), 'PI1': ('SPI2_SCK', 'in'), 'PI0': ('SPI2_NSS', 'in'),
    'PC12': ('SPI3_MOSI', 'in'), 'PC11': ('SPI3_MISO', 'out'), 'PC10': ('SPI3_SCK', 'in'), 'PA15': ('SPI3_NSS', 'in'),
    'PE14': ('SPI4_MOSI', 'in'), 'PE13': ('SPI4_MISO', 'out'), 'PE12': ('SPI4_SCK', 'in'), 'PE11': ('SPI4_NSS', 'in'),
    'PA11': ('USB_DM (DFU)', 'od'), 'PA12': ('USB_DP (DFU)', 'od'),
    'PH14': ('FDCAN1_RX', 'in-pu'), 'PH13': ('FDCAN1_TX', 'out')}
LOADER_DRIVES = ('out', 'od')
# R10 allowances: port -> (net, {pad: part value} of every other pad on the net, reason). A loader pin with a net must be
# here with that net and exactly those members (a new part, a changed value or another net fails); a driven pin's
# reason states why the drive is harmless. Members and values recorded
# from the R10 board of the round that set them (not re-measured in round 4).
LOADER_R10 = {
    'PA2': ('SERVO3_MCU', {'R152.1': '1k 0603', 'R156.1': '10k', 'D121.4': 'SRV05-4'},
            "USART2_TX drives the servo-3 signal through R152 1k: R8's allowance (frozen 3.2; a servo never sends 0x7F); "
            'servo power is off the board (O3), so a byte at most twitches an unpowered or harness-powered servo on the '
            'servicing bench. BOOT0 low also enters ROM when BOOT_ADD0=0x1FF0 (AN2606 Rev70 Table2 Pattern10); '
            'record/read back the intended user-flash boot configuration before flight'),
    'PA3': ('SERVO4_MCU', {'R153.1': '1k 0603', 'R157.1': '10k', 'D121.6': 'SRV05-4'},
            'USART2_RX: an input (AN2606 p. 278 lists both no pull and pull-up), never driven; the line is held by '
            'R157 10k and driven only by U1 itself in flight'),
    'PA4': ('LOGIC_SOURCE_ST', {'R91.2': '10k 1%', 'U11.9': 'TPS2121RUXR'},  # AUD-5.
            'SPI1_NSS: a slave input, no pull (p. 279), never driven; U11 ST with its R91 10k pull-up (R8 pin table) '
            'is the only driver'),
    'PA5': ('BAT_FAULT_N', {'R89.2': '10k 1%', 'U9.4': 'TPS259470LRPWR'},  # AUD-5.
            'SPI1_SCK: a slave input, no pull (p. 279), never driven; U9 FLT with its R89 10k pull-up (R8 pin table) is '
            'the only driver'),
    'PA6': ('VLOGIC_SENSE', {'R60.2': '100k', 'R61.1': '10k', 'C60.1': '10nF 50V X7R 10%'},
            'SPI1_MISO is driven push-pull by the loader into the VLOGIC divider node (R60 100k from VLOGIC, R61 10k to '
            'GND, C60 10 nF): the pin current is at most 3.3 V / (10k || 100k) = 0.36 mA (VLOGIC at 0 V, pin high), '
            'far below the 20 mA absolute-maximum I/O current (DS12110 Rev 10 Table 22, p. 105); VLOGIC (<= 8.4 V) '
            'reaches the pin only through R60 (<= 84 uA into a low pin); the reading is wrong only while in the loader'),
    'PE11': ('CAM_PWR_EN', {'R431.1': '100k 1%', 'U402.3': 'TPS2553DBVR'},
             'SPI4_NSS: a slave input, no pull (AN2606 p. 280): R431 100k holds U402 EN low, so the camera supply stays '
             'off in the loader'),
    'PE12': ('CAM_FAULT_N', {'R432.1': '10k 1%', 'U402.4': 'TPS2553DBVR'},  # AUD-7.
             'SPI4_SCK: a slave input, no pull (p. 280), never driven; U402 FAULT is open drain (TPS2553 data sheet) '
             'with the R432 10k pull-up'),
    'PC10': ('SD_SCK', {'J430.5': '472192001'},
             'SPI3_SCK is a loader slave input, never driven; J430.5 is the card clock input. PD0 SD_CS has R460 '
             '10k to 3V3, keeping the card deselected while all GPIOs are reset inputs'),
    'PC11': ('SD_MISO', {'J430.7': '472192001', 'R462.1': '10k 1%'},
             'SPI3_MISO is driven by the loader only during a host transfer; PD0 SD_CS is independent of the '
             'loader SPI3_NSS PA15 and is held high by R460 10k, so the card data output stays high impedance. '
             'R462 draws at most 3.3V/10k=0.33mA if PC11 drives low; serviced ROM use only, with intended user-flash BOOT_ADD0 readback before flight'),
    'PC12': ('SD_MOSI', {'J430.3': '472192001', 'R461.1': '10k 1%'},
             'SPI3_MOSI is a loader slave input, never driven; J430.3 is the card command input and R461 10k '
             'holds it high while the card stays deselected by SD_CS'),
    'PA11': ('USB_DM', None, 'DFU is the loader interface itself (R8 allowance); members not pinned (USB contract)'),
    'PA12': ('USB_DP', None, 'DFU is the loader interface itself (R8 allowance); members not pinned (USB contract)'),
    'PB6': ('QSPI_NCS', {'R10.1': '10k', 'U3.1': 'W25Q128JVSIQ'},
            "I2C1_SCL open drain, no pull: R8's allowance (frozen 3.5): the R10 10k pull-up keeps the flash deselected; "
            'the loader as an I2C slave pulls SCL low only to stretch a clock it receives'),
    'PB9': ('I2C1_SDA', {'R13.1': '4.7k', 'U5.7': 'MS561101BA03'},
            "I2C1_SDA open drain, no pull: R8's allowance (frozen 3.6): the barometer's own I2C data line with its 4.7k "
            'pull-up; the loader answers only address 0b1001110x, which the barometer (0x76 / 0x77) does not use'),
}


def real_net(n):
    return bool(n) and not n.startswith('unconnected-')


@contextmanager
def patched(module, **values):
    old = {k: getattr(module, k) for k in values}
    try:
        for k, v in values.items():
            setattr(module, k, v)
        yield
    finally:
        for k, v in old.items():
            setattr(module, k, v)


def part_nets(board):
    """{ref: set of real nets on its pads}, from the board's own pad nets."""
    return {f.GetReference(): {p.GetNetname() for p in f.Pads() if real_net(p.GetNetname())}
            for f in board.GetFootprints()}


def net_reach(nets_of, start, skip=(), stop=RAILS):
    """Nets reachable from `start` through parts (any part with <= MAX_PART_NETS nets, `skip` excepted), not through
    the rails. Returns {net: (previous net, part)} (start maps to None)."""
    members = {}
    for ref, nets in nets_of.items():
        for n in nets:
            members.setdefault(n, set()).add(ref)
    came, queue = {start: None}, [start]
    while queue:
        n = queue.pop()
        if n in stop and n != start:
            continue
        for ref in sorted(members.get(n, ())):
            if ref in skip or len(nets_of[ref]) > MAX_PART_NETS:
                continue
            for m in sorted(nets_of[ref]):
                if m not in came:
                    came[m] = (n, ref)
                    queue.append(m)
    return came


RAW_SIDE_NET = re.compile(r'^(RAW_ACT(_\w+)?|ACT_\w+)$')


def multinet_bridges(nets_of):
    """R5-SAF-01: parts other than U1 with more than MAX_PART_NETS nets are not walked by net_reach, so each is checked
    directly: pads on a RAW side net (RAW_ACT and its sense / MID / MCU nets, ACT_*) and on an armed-side net (PYRO1_*,
    ARM1_* and their sense / MID / MCU nets) at once bypasses the named pyro / sense chain. Returns [(ref, raw nets, armed
    nets)]."""
    out = []
    for ref, nets in sorted(nets_of.items()):
        if ref == MCU_REF or len(nets) <= MAX_PART_NETS:
            continue
        raw, armed = sorted(n for n in nets if RAW_SIDE_NET.match(n)), sorted(n for n in nets if ARMED_SIDE.match(n))
        if raw and armed:
            out.append((ref, raw, armed))
    return out


def multinet_issues(nets_of, rid):
    return [f'{rid}: {ref} (more than {MAX_PART_NETS} nets) has pads on the RAW-side net(s) {raw} and the armed-side '
            f'net(s) {armed}: it bypasses the named pyro / sense chain' for ref, raw, armed in multinet_bridges(nets_of)]


def net_path(came, net):
    out = [net]
    while came.get(net):
        net, ref = came[net]
        out[:0] = [net, f'[{ref}]']
    return ' '.join(out)


# ======================================================================================================================
# copper connectivity (geometry only: net labels on tracks, vias, fills and drawings are ignored)
# ======================================================================================================================
def copper_nodes(board):
    """[(key, layer, shape, bbox, pad-or-None, net, label)] of every copper pad, track, arc, via, fill island and
    copper drawing. One key per physical item (a pad or via spans its layers)."""
    import pcbnew
    import check_r8 as r8
    layers = list(board.GetEnabledLayers().CuStack())
    out = []

    def add(key, lay, shape, pad, net, label):
        b = shape.BBox()
        out.append((key, lay, shape, (b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom()), pad, net, label))

    def add_text(t, label):
        """Copper text (R3-GATE-02): its glyph polygons on its copper layer."""
        if t.GetLayer() not in layers or (hasattr(t, 'IsVisible') and not t.IsVisible()):
            return
        poly = pcbnew.SHAPE_POLY_SET()
        t.TransformShapeToPolygon(poly, t.GetLayer(), 0, pcbnew.FromMM(0.001), pcbnew.ERROR_OUTSIDE)
        if poly.OutlineCount():
            add(t.m_Uuid.AsString(), t.GetLayer(), poly, None, '', label)

    def add_zone(z, label):
        if z.GetIsRuleArea():
            return
        for lay in layers:
            if z.IsOnLayer(lay) and z.HasFilledPolysForLayer(lay):
                fill = z.GetFilledPolysList(lay)
                for i in range(fill.OutlineCount()):
                    add(f'{z.m_Uuid.AsString()}/{lay}/{i}', lay, fill.UnitSet(i), None, z.GetNetname(),
                        f'{label or z.GetNetname() or "(no net)"} fill on {board.GetLayerName(lay)}')
    for f in board.GetFootprints():
        ref = f.GetReference()
        for p in f.Pads():
            for lay in layers:                       # an NPTH pad that carries copper layers counts (R4-GATE-04)
                if p.IsOnLayer(lay):
                    add(p.m_Uuid.AsString(), lay, r8.item_shape(p, lay), p, p.GetNetname(), f'{ref}.{p.GetNumber()}')
        for g in f.GraphicalItems():
            if isinstance(g, pcbnew.PCB_SHAPE) and g.GetLayer() in layers:
                add(g.m_Uuid.AsString(), g.GetLayer(), g.GetEffectiveShape(), None, g.GetNetname(), f'{ref} copper drawing')
            elif not isinstance(g, pcbnew.PCB_SHAPE):
                add_text(g, f'{ref} copper text')
        for fld in f.GetFields():
            add_text(fld, f'{ref} copper field {fld.GetName()}')
        for z in f.Zones():
            add_zone(z, f'{ref} footprint zone')
    for t in board.GetTracks():
        kind = 'via' if t.GetClass() == 'PCB_VIA' else 'track'
        at = t.GetPosition() if kind == 'via' else t.GetStart()
        for lay in layers:
            if t.IsOnLayer(lay):
                add(t.m_Uuid.AsString(), lay, r8.item_shape(t, lay), None, t.GetNetname(),
                    f'{kind} {t.GetNetname() or "(no net)"} ({pcbnew.ToMM(at.x):.2f}, {pcbnew.ToMM(at.y):.2f})')
    for z in board.Zones():
        add_zone(z, None)
    for d in board.GetDrawings():
        if isinstance(d, pcbnew.PCB_SHAPE) and d.GetLayer() in layers:
            add(d.m_Uuid.AsString(), d.GetLayer(), d.GetEffectiveShape(), None, d.GetNetname(), 'board copper drawing')
        elif not isinstance(d, pcbnew.PCB_SHAPE):
            add_text(d, 'board copper text')
    return out


def copper_reach(nodes, net):
    """Grow from every pad of `net` through touching copper on a shared layer. Pads of other nets are recorded and not
    passed through; tracks, vias, fills and drawings are passed whatever their net. Returns ({foreign pad label: (its
    net, the item that touched it)}, reached item count)."""
    import pcbnew
    by_layer, by_key = {}, {}
    for i, n in enumerate(nodes):
        by_layer.setdefault(n[1], []).append(i)
        by_key.setdefault(n[0], []).append(i)
    seen = {n[0] for n in nodes if n[4] is not None and n[5] == net}
    queue = [i for k in seen for i in by_key[k]]
    foreign = {}
    while queue:
        i = queue.pop()
        _, lay, shape, box, _, _, label = nodes[i]
        for j in by_layer[lay]:
            key, _, other, b, pad, other_net, other_label = nodes[j]
            if key in seen or b[0] > box[2] or b[2] < box[0] or b[1] > box[3] or b[3] < box[1]:
                continue
            if not pcbnew.SHAPE.Collide(shape, other, 1):
                continue
            if pad is not None and other_net != net and other_net:
                foreign.setdefault(other_label, (other_net, label))
                continue
            seen.add(key)
            queue.extend(by_key[key])
    return foreign, len(seen)


def connectivity(ctx):
    if getattr(ctx, '_reach', None) is None:
        nodes = copper_nodes(ctx.board)
        ctx._reach = {net: copper_reach(nodes, net) for net in ARMED}
    return ctx._reach


# ======================================================================================================================
# S-rules
# ======================================================================================================================
MCU_SIDE = re.compile(r'(_MCU|^PYRO1_GATE_N)$')           # reject obsolete sense tails; retain the gate tail
GND_TIES = {      # (part, armed-side net): each intended tie to GND, with its reason (R4-SAF-02 / R4-GATE-03)
    ('R128', 'PYRO1_GATE'): 'gate pull-down (S-3)', ('C126', 'PYRO1_GATE'): 'gate-source capacitor (S-3)',
    ('Q124', 'PYRO1_GATE'): 'pyro FET gate pin; its source is GND', ('Q124', 'PYRO1_OUT'): 'pyro FET drain-source: fires the igniter',
    ('R133', 'ARM1_SENSE'): 'ARM_SENSE divider foot (2 k parallel pair)', ('R180', 'ARM1_SENSE'): 'ARM_SENSE divider foot',
    ('C129', 'ARM1_SENSE'): 'ARM_SENSE filter capacitor',
    ('R130', 'PYRO1_CONT'): 'continuity divider foot', ('R178', 'PYRO1_CONT'): 'continuity divider foot',
    ('C127', 'PYRO1_CONT'): 'continuity filter capacitor',
    ('C128', 'PYRO1_OUT'): 'igniter-output bypass capacitor'}
SUPPLY_TIES = {   # the board's intended ties to a supply, rail or the load-switch source node (not GND)
    ('D120', 'PYRO1_COLD', '3V3'): 'cold pull-up diode D120 / R131: the continuity cold-side bias (H-1)',
    ('Q121', 'RAW_ACT', 'ACT_FET_S'): 'load switch Q121 drain RAW_ACT, source on the back-to-back node (S-2)'}


ARMED_PARTS = {       # part: ({armed nets it may touch}, reason) (R6-GATE-07; the whole list on the R10 board, each named)
    'Q121': ({RAW}, 'load-switch drain feeds the pyro bus'),
    'TP120': ({RAW}, 'existing load-switch output test pad'),
    'J121': ({'PYRO1_OUT', 'PYRO1_IGN'}, 'igniter terminal'),
    'R134': ({'PYRO1_IGN', RAW}, 'igniter pulse resistor, bus to igniter'),
    'Q124': ({'PYRO1_OUT'}, 'pyro FET: drain on the igniter return'),
    'R132': ({RAW}, 'bus-sense divider high side'),
    'R131': ({'PYRO1_OUT'}, 'continuity cold pull-up (H-1)'),
    'R173': ({'PYRO1_OUT'}, 'continuity divider high side'),
    'C128': ({'PYRO1_OUT'}, 'igniter-output bypass capacitor')}


ARMED_NET_PARTS = {   # armed-side / RAW_ACT net: every part on it on the R10 board, each named (R7-SAF-01 / R7-GATE-03)
    'PYRO1_IGN': {'J121', 'R134'},
    'PYRO1_OUT': {'C128', 'J121', 'Q124', 'R131', 'R173'}, 'PYRO1_COLD': {'D120', 'R131'},
    'PYRO1_GATE': {'C126', 'Q124', 'R126', 'R128', 'TP122'},
    'PYRO1_CONT': {'C127', 'R129', 'R130', 'R178', 'U1'}, 'PYRO1_CONT_MID': {'R129', 'R173'},
    'ARM1_SENSE': {'C129', 'R133', 'R175', 'R180', 'U1'}, 'ARM1_SENSE_MID': {'R132', 'R175'},
    'RAW_ACT': {'Q121', 'R132', 'R134', 'TP120'}}
GATE_PARTS = {'R126': 'gate series resistor', 'R128': 'gate pull-down', 'C126': 'gate-source capacitor',
              'Q124': 'pyro FET', 'TP122': 'gate test pad'}
MCU_NET_PREFIX = re.compile(r'^(PYRO1_|ARM1_|RAW_ACT)')


def net_parts(board):
    out = {}
    for ref, nets in part_nets(board).items():
        for n in nets:
            out.setdefault(n, set()).add(ref)
    return out


def armed_net_issues(board):
    """R7-SAF-01: any part on an armed-side / RAW_ACT net other than the named ones (an extra test pad or part there is
    an unreviewed connection to the firing / sense chain)."""
    issues = []
    for n, refs in sorted(net_parts(board).items()):
        if not armed_net(n):
            continue
        if n not in ARMED_NET_PARTS:
            issues.append(f'S-1: armed-side net {n} is not in ARMED_NET_PARTS (parts {sorted(refs)})')
            continue
        extra = sorted(refs - ARMED_NET_PARTS[n])
        if extra:
            issues.append(f'S-1: {extra} on armed-side net {n} is not a named part of it (ARMED_NET_PARTS in '
                          f'tools/check_r10.py: {sorted(ARMED_NET_PARTS[n])})')
    return issues


DIRECT_ADC = {'PYRO1_CONT': '15', 'ARM1_SENSE': '33'}


def mcu_side_issues(board):
    """Only the firing-gate MCU tail remains; the filtered ADC nodes go directly to PC0 and PC5."""
    issues, members, nets_of = [], net_parts(board), part_nets(board)
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    for n, refs in sorted(members.items()):
        if not (MCU_NET_PREFIX.match(n) and MCU_SIDE.search(n)):
            continue
        if n != 'PYRO1_GATE_N':
            issues.append(f'S-1: obsolete MCU-side sense tail {n}; connect the filtered node directly to PC0 / PC5')
            continue
        toward, others = [], []
        for ref in sorted(refs - {'U1'}):
            other = nets_of[ref] - {n}
            two = ref.startswith('R') and len(fps[ref].Pads()) == 2 and len(other) == 1
            if two and armed_net(next(iter(other))):
                toward.append(ref)
            elif not (two and other == {'GND'}):
                others.append(ref)
        if 'U1' not in refs or toward != ['R126'] or others:
            issues.append(f'S-1: MCU-side net {n} is not U1 + R126 toward an armed net '
                          f'(parts {sorted(refs)}; toward {toward}, others {others}): a mis-named armed net')
    if 'U1' in fps:
        for net, pin in DIRECT_ADC.items():
            actual = {p.GetNumber() for p in fps['U1'].Pads() if p.GetNetname() == net}
            if actual and actual != {pin}:
                issues.append(f'S-1: filtered ADC net {net} must touch only U1.{pin}, got {sorted(actual)}')
    return issues


def armed_net(n):
    """A net on the armed bus or RAW_ACT side (including the high side of the sense dividers and the gate net)."""
    return bool(ARMED_SIDE.match(n) or RAW_SIDE.match(n)) and not MCU_SIDE.search(n)


def supply_net(n):
    import route_check as rc
    previous = rc.PROFILE
    rc.set_profile('r10')
    try:
        return n in SUPPLY_NETS or bool(SUPPLY_NET.match(n)) or rc.net_class(n) == 'power'
    finally:
        rc.set_profile(previous)


def supply_ties(board):
    """[(part, armed-side net, supply net)] of every part (whatever its net count) that has pads on an
    armed-side / RAW_ACT net and on a supply or rail net, other than the named ties above (R4-SAF-02 / R4-GATE-03)."""
    out = []
    for ref, nets in sorted(part_nets(board).items()):
        for a in sorted(n for n in nets if armed_net(n)):
            # These two protected ADC inputs intentionally share U1 with its supply pads. No other U1 safety
            # connection is exempt, and K-contract / K-actuators pin their direct roles independently.
            if ref == MCU_REF and a in DIRECT_ADC:
                fp = board.FindFootprintByReference(MCU_REF)
                if {p.GetNumber() for p in fp.Pads() if p.GetNetname() == a} == {DIRECT_ADC[a]}:
                    continue
            for sup in sorted(n for n in nets if n != a and supply_net(n) and not armed_net(n)):
                if (ref, a, sup) in SUPPLY_TIES or (sup == 'GND' and (ref, a) in GND_TIES):
                    continue
                out.append((ref, a, sup))
    return out


def tie_issues(ctx, rid, wanted):
    return [f'{rid}: {ref} has pads on the armed / RAW_ACT side net {a} and on the supply {sup}: not a named tie '
            f'(GND_TIES / SUPPLY_TIES in tools/check_r10.py)' for ref, a, sup in supply_ties(ctx.board) if wanted(a)]


def s1(ctx):
    """Owner single screw switch: RAW_ACT is the bus; only R134 and R132 lead into the firing / bus-sense chain."""
    issues, ev = [], {}
    if 'J124' in ctx.fps:
        issues.append('S-1: obsolete J124 ARM terminal must be removed')
    nets_of = part_nets(ctx.board)
    if any(n.GetNetname() == 'PYRO1_BUS' for n in ctx.board.GetNetsByNetcode().values()):
        issues.append('S-1: obsolete PYRO1_BUS must be merged into RAW_ACT')
    for ref, num, net in (('R134', '2', RAW), ('R134', '1', 'PYRO1_IGN'),
                          ('R132', '1', RAW), ('R132', '2', 'ARM1_SENSE_MID')):
        f = ctx.fps.get(ref)
        pad = f.FindPadByNumber(num) if f else None
        if pad is None or pad.GetNetname() != net:
            issues.append(f'S-1: {ref}.{num} must be on {net} (RAW_ACT bus behind Q120/Q121)')
    came = net_reach(nets_of, RAW, skip={'R134', 'R132'})
    for net in sorted(n for n in came if ARMED_SIDE.match(n)):
        issues.append(f'S-1: RAW_ACT reaches {net} outside R134 / R132: {net_path(came, net)}')
    ev['raw_act_reaches_without_r134_r132'] = sorted(came)
    issues += multinet_issues(nets_of, 'S-1')
    joins = {'R134': {RAW, 'PYRO1_IGN'}, 'R132': {RAW, 'ARM1_SENSE_MID'}}
    for ref, nets in sorted(nets_of.items()):                # any part, whatever its net count
        both = sorted(n for n in nets if ARMED_SIDE.match(n))
        if RAW in nets and both and nets != joins.get(ref):
            issues.append(f'S-1: {ref} has pads on RAW_ACT and pyro / sense net(s) {both}; only R134 / R132 may join them')
    issues += tie_issues(ctx, 'S-1', lambda a: a in ARMED)
    for ref, fp in sorted(ctx.fps.items()):                  # any part, whatever its reference
        on = sorted({p.GetNetname() for p in fp.Pads()} & set(ARMED))
        if not on:
            continue
        if ref not in ARMED_PARTS:
            what = 'test pad' if re.fullmatch(r'(TP|PT|TPA|TEST)\w*', ref) or len(fp.Pads()) == 1 else 'part'
            issues.append(f'S-1: {what} {ref} on armed copper {on} is not a named armed-side part (ARMED_PARTS in '
                          f'tools/check_r10.py)')
        elif not set(on) <= ARMED_PARTS[ref][0]:
            issues.append(f'S-1: {ref} is on armed net(s) {on}; its named armed nets are {sorted(ARMED_PARTS[ref][0])}')
    ev['armed_parts'] = sorted(ARMED_PARTS)
    issues += armed_net_issues(ctx.board) + mcu_side_issues(ctx.board)
    reach = connectivity(ctx)
    ev['raw_act_copper_items'] = reach[RAW][1]
    for label, (net, via) in sorted(reach[RAW][0].items()):
        if ARMED_SIDE.match(net):
            issues.append(f'S-1: RAW_ACT copper reaches {label} ({net}) through {via}: firing / sense chain is bypassed')
    return issues, ev


def s2(ctx):
    """The unified RAW_ACT bus is fed only through the back-to-back Q120 / Q121 load switch."""
    issues, ev = [], {}
    for ref, (drain, source) in LOAD_SWITCH.items():
        f = ctx.fps.get(ref)
        if f is None:
            issues.append(f'S-2: load switch {ref} missing')
            continue
        roles = {}
        for p in f.Pads():
            for role, nums in PFET_ROLES.items():
                if p.GetNumber() in nums:
                    roles.setdefault(role, set()).add(p.GetNetname())
        ev[ref] = {k: sorted(v) for k, v in roles.items()}
        want = {'D': {drain}, 'S': {source}, 'G': {'ACT_GATE'}}
        if roles != want:
            issues.append(f'S-2: {ref} must be drain {drain}, source {source}, gate ACT_GATE (is {ev[ref]})')
    nets_of = part_nets(ctx.board)
    came = net_reach(nets_of, RAW, skip={'Q121'})
    bad = sorted(n for n in came if not (RAW_SIDE.match(n) or ARMED_SIDE.match(n)) and n not in RAILS)
    issues += [f'S-2: RAW_ACT is joined to {n} other than through Q121: {net_path(came, n)}' for n in bad]
    ev['pyro_side'] = sorted(came)
    issues += multinet_issues(nets_of, 'S-2')
    issues += tie_issues(ctx, 'S-2', lambda a: a not in ARMED)
    ev['named_ties'] = {'gnd': len(GND_TIES), 'supply': [list(k) for k in SUPPLY_TIES]}
    for start, (foreign, count) in connectivity(ctx).items():
        ev[f'{start}_copper_items'] = count
        for label, (net, via) in sorted(foreign.items()):
            issues.append(f'S-2: {start} copper touches {label} ({net}) through {via}')
    return issues, ev


PULL_RANGE = (1e3, 100e3)       # ohm: the gate pull (R4-SAF-01)
SERIES_RANGE = (100.0, 10e3)    # ohm: the gate series resistor (R5-SAF-02)
MCU_PULL_RANGE = (100.0, 100e3)  # ohm: the MCU-side node's pull to GND (R127 type, R5-SAF-02)
GATE_CAP_MIN = 100e-9           # F: the gate-source capacitor
SUPPLY_NET = re.compile(r'^(PORT_|VBUS|VLOGIC|BAT_|RAW_PROTECTED|V3V3|CAM_5V$|[A-Z0-9_]*_(4V8|5V3|5V)$)')
SUPPLY_NETS = RAILS | {'BAT_IN', 'RAW_PROTECTED', 'VLOGIC', 'ACT_FET_S', 'RAW_ACT', 'PYRO1_BUS', 'PYRO1_OUT', 'PYRO1_IGN'}


def parse_value(text, kind):
    """A part Value field ('220nF 25V X7R', '4.7k', '4k7', '2R2', '2R 1%', '2.2uF') as ohms ('R') or farads ('C'); None
    if not readable. The first token is read whole: plain 'number[unit]' or infix notation ('4k7' = 4.7k, '100k5' =
    100.5k); anything else in it ('1e3', '1,5k') is unreadable (R6-GATE-06)."""
    text = (text or '').strip()
    mults = r'meg|[pnu\u00b5\u03bcmrRkKMG]'            # U+00B5 and U+03BC both read as micro (R7-GATE-01)
    unit = r'(?:\u03a9|\u2126|ohms?|F)?' if kind == 'R' else r'F?'
    m = re.match(rf'(\d+)({mults})(\d+)({unit})(?=\s|$)', text)
    if m:
        number, mult, unit_found = float(f'{m.group(1)}.{m.group(3)}'), m.group(2), m.group(4)
    else:
        m = re.match(rf'(\d+(?:\.\d+)?)\s*({mults})?\s*({unit})(?=\s|$)'
                     rf'(?!\s*(?:meg|[pnu\u00b5\u03bcmrRkKMG\u03a9\u2126F]|ohm))', text)
        if not m:
            return None                      # any other unconsumed tail is unreadable ('4.7 kx': a free-text tail
            # after a number may not start like a multiplier or unit)
        number, mult, unit_found = float(m.group(1)), m.group(2) or '', m.group(3) or ''
    has_f = unit_found == 'F'
    if kind == 'C' and not mult and not has_f:
        return None                  # a unitless capacitor value ('220') is not read as farads (R5-SAF-02)
    if kind == 'C' and mult == 'm' and not has_f:
        return None                  # '100m' is not a capacitor value; '100mF' is
    if kind == 'R':
        factor = {'': 1.0, 'r': 1.0, 'R': 1.0, 'k': 1e3, 'K': 1e3, 'm': 1e-3, 'M': 1e6, 'meg': 1e6, 'G': 1e9}.get(mult)
    else:
        factor = {'': 1.0, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, '\u00b5': 1e-6, '\u03bc': 1e-6, 'm': 1e-3}.get(mult)
    return None if factor is None else number * factor


def gate_network(ctx, fet, roles, label):
    """(issues, evidence): the gate of `fet` has a pull-down resistor (1 k - 100 k) and a capacitor (>= 100 nF) to its
    source and a series resistor to another, non-supply net (its driver; R4-SAF-01)."""
    f = ctx.fps.get(fet)
    if f is None:
        return [f'S-3: {fet} missing'], {}
    nets = {}
    for p in f.Pads():
        for role, nums in roles.items():
            if p.GetNumber() in nums:
                nets.setdefault(role, set()).add(p.GetNetname())
    if len(nets.get('G', ())) != 1 or len(nets.get('S', ())) != 1:
        return [f'S-3: {fet} gate / source pads not on one net each ({nets})'], {}
    gate, source = next(iter(nets['G'])), next(iter(nets['S']))
    found = {'pull': [], 'cap': [], 'series': []}
    for ref, nn in part_nets(ctx.board).items():
        if gate not in nn or len(nn) != 2 or len(ctx.fps[ref].Pads()) != 2:
            continue
        other = next(iter(nn - {gate}))
        kind = ref.rstrip('0123456789')
        if other == source and kind == 'R':
            found['pull'].append(ref)
        elif other == source and kind == 'C':
            found['cap'].append(ref)
        elif kind == 'R':
            found['series'].append((ref, other))
    values = {ref: ctx.fps[ref].GetValue() for k in ('pull', 'cap') for ref in found[k]}
    found['pull'] = [r for r in found['pull'] if PULL_RANGE[0] <= (parse_value(values[r], 'R') or 0) <= PULL_RANGE[1]]
    found['cap'] = [r for r in found['cap'] if (parse_value(values[r], 'C') or 0) >= GATE_CAP_MIN]
    found['series'] = [(r, o) for r, o in found['series'] if o not in SUPPLY_NETS and not SUPPLY_NET.match(o)
                       and SERIES_RANGE[0] <= (parse_value(ctx.fps[r].GetValue(), 'R') or 0) <= SERIES_RANGE[1]]
    issues = []
    for key, what in (('pull', f'a resistor from the gate ({gate}) to the source ({source}) of 1 k - 100 k'),
                      ('cap', f'a gate-source capacitor >= 100 nF ({gate} to {source})'),
                      ('series', f'a series resistor of 100 ohm - 10 k from a non-supply net into the gate ({gate})')):
        if not found[key]:
            issues.append(f'S-3: {label} {fet}: no {what}')
    return issues, dict(gate=gate, source=source, values=values, **found)


def same_layer_islands(board, nets, layer):
    """{pad label 'REF.N': island id} of the copper of `nets` on `layer` alone (tracks, pads and via rings on that layer,
    joined where they touch); a layer change never joins two islands, so an open via barrel cannot hide behind it."""
    import pcbnew
    items = []
    for t in board.GetTracks():
        if t.GetNetname() in nets and t.IsOnLayer(layer):
            items.append((t.GetNetname(), t.GetEffectiveShape(layer), None))
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() in nets and p.IsOnLayer(layer):
                items.append((p.GetNetname(), p.GetEffectiveShape(layer), f'{f.GetReference()}.{p.GetNumber()}'))
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a in range(len(items)):
        for b in range(a + 1, len(items)):
            if items[a][0] == items[b][0] and pcbnew.SHAPE.Collide(items[a][1], items[b][1], 0):
                parent[find(a)] = find(b)
    return {label: find(i) for i, (_, _, label) in enumerate(items) if label}


def local_gate_bias(ctx, fet, roles):
    """R18-SAF-02 / D-R18-02: the FET's gate pad and source pads each reach one pad of a 1 k - 100 k gate-source
    resistor through copper on the FET's own layer, so one open via or barrel cannot float the gate."""
    import pcbnew
    f = ctx.fps.get(fet)
    if f is None:
        return [f'S-3: {fet} missing'], []
    nets = {role: {p.GetNetname() for p in f.Pads() if p.GetNumber() in nums} for role, nums in roles.items()}
    if len(nets.get('G', ())) != 1 or len(nets.get('S', ())) != 1:
        return [], []                    # gate_network reports the pad-net fault itself
    gate, source = next(iter(nets['G'])), next(iter(nets['S']))
    layer = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
    island = same_layer_islands(ctx.board, {gate, source}, layer)
    g = island.get(f'{fet}.{roles["G"][0]}')
    s = {island.get(f'{fet}.{n}') for n in roles['S']}
    found = []
    for ref, nn in sorted(part_nets(ctx.board).items()):
        r = ctx.fps[ref]
        if nn != {gate, source} or not ref.startswith('R') or len(r.Pads()) != 2 or \
                not PULL_RANGE[0] <= (parse_value(r.GetValue(), 'R') or 0) <= PULL_RANGE[1]:
            continue
        pads = {p.GetNetname(): island.get(f'{ref}.{p.GetNumber()}') for p in r.Pads()}
        if pads.get(gate) == g and pads.get(source) in s:
            found.append(ref)
    if not found:
        return [f'S-3: load switch {fet}: no gate-source resistor of 1 k - 100 k joined to its gate and source pads by '
                f'{ctx.board.GetLayerName(layer)} copper alone (an open via barrel would float the gate)'], found
    return [], found


def s3(ctx):
    issues, ev = [], {}
    found, ev['Q124'] = gate_network(ctx, 'Q124', NFET_ROLES, 'pyro FET')
    issues += found
    u1 = {p.GetNetname() for p in ctx.fps['U1'].Pads()} if 'U1' in ctx.fps else set()
    if ev['Q124'] and not any(other in u1 and other not in SUPPLY_NETS for _, other in ev['Q124']['series']):
        issues.append('S-3: pyro FET Q124: no series resistor from a U1 GPIO pad (a non-rail net) into the gate')
    for node in sorted({o for _, o in ev['Q124'].get('series', ()) if o in u1 and o not in SUPPLY_NETS}):
        pulls = [ref for ref, nn in part_nets(ctx.board).items()          # R127 type: the MCU-side node to GND
                 if nn == {node, 'GND'} and len(ctx.fps[ref].Pads()) == 2 and ref.startswith('R')
                 and MCU_PULL_RANGE[0] <= (parse_value(ctx.fps[ref].GetValue(), 'R') or 0) <= MCU_PULL_RANGE[1]]
        ev['Q124'].setdefault('mcu_pull', {})[node] = pulls
        if not pulls:
            issues.append(f'S-3: pyro FET Q124: no resistor of 100 ohm - 100 k from the MCU-side gate node {node} to GND '
                          f'(it must be defined off while the MCU pin floats)')
        series = {r for r, o in ev['Q124']['series'] if o == node}
        for ref, nn in sorted(part_nets(ctx.board).items()):          # R6-SAF-02: only U1, the series R and R to GND
            if node not in nn or ref == 'U1' or ref in series:
                continue
            fp = ctx.fps[ref]
            if not (ref.startswith('R') and len(fp.Pads()) == 2 and nn == {node, 'GND'}):
                issues.append(f'S-3: {ref} is on the MCU-side gate node {node} (nets {sorted(nn)}): only U1, the series '
                              f'resistor and resistors to GND may touch it (a pull-up would hold the gate on)')
    gate_net = ev['Q124'].get('gate')
    for ref, nn in sorted(part_nets(ctx.board).items()):          # R7-GATE-03: only the named gate parts
        if gate_net in nn and ref not in GATE_PARTS:
            issues.append(f'S-3: {ref} is on the pyro gate net {gate_net}: only {sorted(GATE_PARTS)} may touch it '
                          f'(a part there changes the gate network)')
    for fet in ('Q120', 'Q121'):
        found, ev[fet] = gate_network(ctx, fet, PFET_ROLES, 'load switch')
        issues += found
        local, ev[fet]['local_bias'] = local_gate_bias(ctx, fet, PFET_ROLES)
        issues += local
    pins = {f'{ref}.{p.GetNumber()}': p.GetNetname() for ref, f in ctx.fps.items() for p in f.Pads()}
    # D-R19-04 (R19-SAF-06): C123 is Q122's gate-source capacitor (gate ACT_EN, source GND), completing the AGENTS 2.4
    # network (R122 series, R123 pull-down, C123).
    want = {'U1.16': 'ACT_EN_MCU', 'R122.1': 'ACT_EN_MCU', 'R122.2': 'ACT_EN', 'R123.1': 'ACT_EN',
            'R123.2': 'GND', 'Q122.1': 'ACT_EN', 'Q122.2': 'GND', 'Q122.3': 'ACT_DRV', 'C123.1': 'ACT_EN',
            'C123.2': 'GND'}
    for pin, net in want.items():
        if pins.get(pin) != net:
            issues.append(f'S-3: independent load-switch enable {pin} must be {net} (is {pins.get(pin)})')
    for net, refs in (('ACT_EN_MCU', {'U1', 'R122'}), ('ACT_EN', {'R122', 'R123', 'Q122', 'C123'})):
        if net_parts(ctx.board).get(net) != refs:
            issues.append(f'S-3: independent load-switch enable {net} must touch only {sorted(refs)}')
    # D-R18-01 (R18-MCU-01): R123 dominates a PC1 pull-up; D-R19-04: C123 10 nF (about 7 us PC1 edge with R122 || R123).
    for ref, value, kind in (('R122', 1e3, 'R'), ('R123', 2e3, 'R'), ('C123', 10e-9, 'C')):
        f = ctx.fps.get(ref)
        got = parse_value(f.GetValue(), kind) if f is not None else None
        if got is None or abs(got - value) > 1e-6 * value:
            issues.append(f'S-3: independent load-switch enable {ref} must be {value:g} ' + ('ohm' if kind == 'R' else 'F'))
    ev['load_enable'] = {p: pins.get(p) for p in want}
    return sorted(set(issues)), ev


def board_population(board, required=REQUIRED_FITTED):
    """R1-07 on the loaded board: present, not DNP / excluded from BOM or position files / board-only."""
    import pcbnew
    issues, fps = [], {f.GetReference(): f for f in board.GetFootprints()}
    flags = {'dnp': pcbnew.FP_DNP, 'exclude_from_bom': pcbnew.FP_EXCLUDE_FROM_BOM,
             'exclude_from_pos_files': pcbnew.FP_EXCLUDE_FROM_POS_FILES, 'board_only': pcbnew.FP_BOARD_ONLY}
    for ref in sorted(required):
        f = fps.get(ref)
        if f is None:
            issues.append(f'{ref}: required fitted part missing from the board')
            continue
        bad = [name for name, bit in flags.items() if f.GetAttributes() & bit]
        if f.GetValue().strip().upper() in ('DNP', 'NC', 'NF', 'NOFIT'):
            bad.append(f'value {f.GetValue()}')
        if bad:
            issues.append(f'{ref}: required fitted part excluded ({", ".join(bad)})')
    return issues


# R19-GATE-02: what a fitted resistor's or MLCC's maker part number encodes must be what its Value field says. JLC places
# the LCSC code (whose maker part S-4 already ties to the BOM), so a code re-pointed at the source to a part of another
# value (R131 10k -> C11702, a 1 kohm 0402WGF1001TCE) passed while Value still read 10k. Families decoded (value field and
# rating codes as each maker's part-numbering scheme gives them):
#   UNI-ROYAL thick film  0402WGF1002TCE    size, power, tolerance, 3 digits + multiplier (0-9, J / K / L = 0.1 / 0.01 /
#                                            0.001), packaging;  FOJAN FRC0603F2262TS the same value code
#   Yageo RC / RT         RC0603FR-0766K5L  size, tolerance, packaging, reel 07, value with R / K / M as decimal point
#   Bourns CRM            CRM2512-FX-2R00ELF  value with R as decimal point;  Vishay MCT0603MD2004BP500 3 digits + exp
#   Samsung CL            CL05B104KB54PNC   size, dielectric (A X5R, B X7R, C C0G), pF code, tolerance, voltage letter
#   Murata GRM / GCJ      GRM32ER71E226KE15L  size, height, dielectric (5C C0G, R7 X7R, R6 X5R), voltage (1E 25 V ...),
#                                            pF code, tolerance
#   Yageo CC              CC0603KRX7R9BB104 size, tolerance, packaging, dielectric, voltage digit, pF code
#   Fenghua               0603B103K500NT    size, dielectric (B X7R, N C0G, X X5R), pF code, tolerance, voltage (500 50 V)
# The value must match; a tolerance, voltage or dielectric the Value field states must match too. A part of another
# family is listed by name with the reason, not passed silently.
MPN_TOL = dict(B=0.1, C=0.25, D=0.5, F=1, G=2, J=5, K=10, M=20)
MPN_MULT = {**{str(d): 10.0 ** d for d in range(10)}, 'J': 0.1, 'K': 0.01, 'L': 0.001}
MPN_SAMSUNG_V = dict(R=4, Q=6.3, P=10, O=16, A=25, L=35, B=50, C=100, D=200, E=250)
MPN_SAMSUNG_D = dict(A='X5R', B='X7R', C='C0G')
MPN_MURATA_V = {'0J': 6.3, '1A': 10, '1C': 16, '1E': 25, 'YA': 35, '1H': 50, '2A': 100}
MPN_MURATA_D = {'5C': 'C0G', 'R7': 'X7R', 'R6': 'X5R', 'C7': 'X7S'}
MPN_YAGEO_CC_V = {'5': 6.3, '6': 10, '7': 16, '8': 25, '9': 50, '0': 100}
MPN_FENGHUA_D = dict(B='X7R', N='C0G', X='X5R')


def mpn_decode(mpn):
    """(kind 'R' / 'C', family, {value, tol %, volts, diel}) the maker part number encodes, or (None, None, None)."""
    def letters(code):                                       # 66K5, 100K, 750R, 2R00
        m = re.fullmatch(r'(\d*)([RKM])(\d*)', code)
        return float(f'{m[1] or 0}.{m[3] or 0}') * {'R': 1, 'K': 1e3, 'M': 1e6}[m[2]] if m and (m[1] or m[3]) else None

    def pf(code):                                            # 104, 226, 4R7 (pF)
        if re.fullmatch(r'\dR\d', code):
            return float(code.replace('R', '.')) * 1e-12
        m = re.fullmatch(r'(\d\d)(\d)', code)
        return int(m[1]) * 10 ** int(m[2]) * 1e-12 if m else None
    m = re.fullmatch(r'(\d{4})(W[A-Z0-9]|\dW)([BDFJ])(\d{3})([0-9JKL])T\w+', mpn)
    if m:
        return 'R', 'UNI-ROYAL', dict(value=int(m[4]) * MPN_MULT[m[5]], tol=MPN_TOL[m[3]])
    m = re.fullmatch(r'FRC(\d{4})([BDFJ])(\d{3})([0-9JKL])T\w*', mpn)
    if m:
        return 'R', 'FOJAN FRC', dict(value=int(m[3]) * MPN_MULT[m[4]], tol=MPN_TOL[m[2]])
    m = re.fullmatch(r'(RC|RT)(\d{4})([BCDFGJ])R[A-Z]?-?07(\w+?)L', mpn)
    if m and letters(m[4]) is not None:
        return 'R', f'Yageo {m[1]}', dict(value=letters(m[4]), tol=MPN_TOL[m[3]])
    m = re.fullmatch(r'CRM(\d{4})-([BDFJ])X-(\w+?)ELF', mpn)
    if m and letters(m[3]) is not None:
        return 'R', 'Bourns CRM', dict(value=letters(m[3]), tol=MPN_TOL[m[2]])
    m = re.fullmatch(r'MCT(\d{4})[A-Z]{2}(\d{3})(\d)([BCDF])P\w+', mpn)
    if m:
        return 'R', 'Vishay MCT', dict(value=int(m[2]) * 10.0 ** int(m[3]), tol=MPN_TOL[m[4]])
    m = re.fullmatch(r'CL(\d\d)([A-Z])(\w{3})([BCDFGJKM])([A-Z])\w+', mpn)
    if m and pf(m[3]) is not None:
        return 'C', 'Samsung CL', dict(value=pf(m[3]), tol=MPN_TOL[m[4]], volts=MPN_SAMSUNG_V.get(m[5]),
                                       diel=MPN_SAMSUNG_D.get(m[2]))
    m = re.fullmatch(r'(GRM|GCJ)(\d\d)(\w)(\w\w)(\w\w)(\w{3})([BCDFGJKM])\w+', mpn)
    if m and pf(m[6]) is not None:
        return 'C', f'Murata {m[1]}', dict(value=pf(m[6]), tol=MPN_TOL[m[7]], volts=MPN_MURATA_V.get(m[5]),
                                           diel=MPN_MURATA_D.get(m[4]))
    m = re.fullmatch(r'CC(\d{4})([BCDFGJKM])[RK](NPO|X7R|X5R|X7S)(\d)B[BN](\w{3})', mpn)
    if m and pf(m[5]) is not None:
        return 'C', 'Yageo CC', dict(value=pf(m[5]), tol=MPN_TOL[m[2]], volts=MPN_YAGEO_CC_V.get(m[4]),
                                     diel={'NPO': 'C0G'}.get(m[3], m[3]))
    m = re.fullmatch(r'(\d{4})([BNX])(\w{3})([BCDFGJKM])(\d\d)(\d)NT', mpn)
    if m and pf(m[3]) is not None:
        return 'C', 'Fenghua', dict(value=pf(m[3]), tol=MPN_TOL[m[4]], volts=int(m[5]) * 10 ** int(m[6]),
                                    diel=MPN_FENGHUA_D[m[2]])
    return None, None, None


def mpn_values(board):
    """(issues, evidence): every fitted R* / C* part's Manufacturer Part decodes (mpn_decode) to its Value field."""
    import pcbnew
    excluded = pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_BOARD_ONLY
    issues, decoded, listed = [], {}, {}
    for f in sorted(board.GetFootprints(), key=lambda g: g.GetReference()):
        ref = f.GetReference()
        if not re.fullmatch(r'[RC]\d+', ref) or f.GetAttributes() & excluded:
            continue
        fields = {field.GetName(): field.GetText().strip() for field in f.GetFields()}
        mpn, value = fields.get('Manufacturer Part', ''), f.GetValue().strip()
        kind, family, got = mpn_decode(mpn)
        if kind is None:
            listed[ref] = (f'{mpn or "no Manufacturer Part"}: not a resistor or MLCC family the gate decodes'
                           + (' (aluminium polymer capacitor)' if 'polymer' in value.lower() else ''))
            continue
        if kind != ref[0]:
            issues.append(f'{ref}: Manufacturer Part {mpn} is a {family} {"resistor" if kind == "R" else "capacitor"}')
            continue
        decoded[ref] = family
        want = parse_value(value, kind)
        if want is None or abs(want - got['value']) > 1e-6 * got['value']:
            issues.append(f'{ref}: Value {value!r} but {mpn} ({family}) is {got["value"]:g} '
                          f'{"ohm" if kind == "R" else "F"}')
        tol = re.search(r'(\d+(?:\.\d+)?)%', value)
        if tol and abs(float(tol[1]) - got['tol']) > 1e-9:
            issues.append(f'{ref}: Value {value!r} states {tol[1]} % but {mpn} is {got["tol"]:g} %')
        volts = re.search(r'(\d+(?:\.\d+)?)V\b', value)
        if volts and kind == 'C' and (got['volts'] is None or abs(float(volts[1]) - got['volts']) > 1e-9):
            issues.append(f'{ref}: Value {value!r} states {volts[1]} V but {mpn} is rated {got["volts"]} V')
        diel = re.search(r'\b(X7R|X5R|X7S|X6S|C0G|NP0|Y5V)\b', value)
        if diel and kind == 'C' and {'NP0': 'C0G'}.get(diel[1], diel[1]) != got['diel']:
            issues.append(f'{ref}: Value {value!r} states {diel[1]} but {mpn} is {got["diel"]}')
    from collections import Counter
    return [f'S-4: {i} (R19-GATE-02)' for i in issues], dict(
        decoded=len(decoded), families=dict(sorted(Counter(decoded.values()).items())), not_decoded=listed)


def s4(ctx):
    import pcbnew
    issues, ev = [], dict(required=len(REQUIRED_FITTED), safety=sorted(SAFETY_FITTED))
    issues += board_population(ctx.board)
    sch = Path(ctx.board_path).with_suffix('.kicad_sch') if ctx.board_path else None
    if sch is None or not sch.is_file():
        issues.append(f'schematic {sch} not found: the required-fitted check needs the schematic too')
    else:
        issues += [f'schematic: {i}' for i in schematic_population(sch)]
        ev['schematic'] = sch.name
    # D-R19-07 (R19-MFG-02 / R19-BOM-02): a part fitted by hand after both reflows gets no stencil aperture; paste on its
    # lands would leave reflowed solder on pads that the hand fit then has to clear.
    from export_fab import MANUAL_FIT
    for ref in sorted(MANUAL_FIT):
        f = ctx.fps.get(ref)
        pasted = sorted(p.GetNumber() for p in (f.Pads() if f else ())
                        if p.IsOnLayer(pcbnew.F_Paste) or p.IsOnLayer(pcbnew.B_Paste))
        if pasted:
            issues.append(f'{ref} is fitted by hand after reflow ({MANUAL_FIT[ref]}) but pads {pasted} carry paste')
    ev['manual_fit_unpasted'] = sorted(MANUAL_FIT)
    for name, path in (('BOM', ctx.bom), ('CPL', ctx.cpl)):
        if path:
            native_parts = None
            if name == 'BOM':
                native_parts = {}
                excluded = (pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES
                            | pcbnew.FP_BOARD_ONLY)
                for ref, part in ctx.fps.items():
                    if part.GetAttributes() & excluded:
                        continue
                    fields = {field.GetName(): field.GetText().strip() for field in part.GetFields()}
                    native_parts[ref] = {'LCSC Part #': fields.get('LCSC', ''),
                                         'Manufacturer Part': fields.get('Manufacturer Part', ''),
                                         'Footprint': str(part.GetFPID().GetLibItemName())}
                ev['BOM_native_identities'] = len(native_parts)
            # D-R18-09 (R18-REQ-10 / R18-MFG-06): hand-fitted parts stay required on the board and schematic, are absent
            # from the JLC uploads and present in the owner BOM beside them.
            text = Path(path).read_text()
            issues += [f'{name}: {i}' for i in assembly_population(text, REQUIRED_FITTED - set(MANUAL_FIT),
                                                                 require_qty=name == 'BOM', native_parts=native_parts)]
            listed = {ref.strip() for row in csv.DictReader(io.StringIO(text))
                      for ref in (row.get('Designator') or '').split(',') if ref.strip()}
            issues += [f'{name}: {ref} is fitted by hand after reflow ({MANUAL_FIT[ref]}) but is in the JLC upload'
                       for ref in sorted(set(MANUAL_FIT) & listed)]
            if name == 'BOM':
                owner = Path(path).with_name(Path(path).name.replace('_bom_jlc', '_bom_owner'))
                rows = list(csv.DictReader(io.StringIO(owner.read_text()))) if owner.is_file() else []
                owned = {ref.strip(): row for row in rows for ref in (row.get('Designator') or '').split(',')}
                for ref in sorted(MANUAL_FIT):
                    row, want = owned.get(ref), native_parts.get(ref, {})
                    if row is None or any((row.get(k) or '').strip() != v for k, v in want.items()):
                        issues.append(f'owner BOM: hand-fitted {ref} missing or not the native part {want}')
                ev['manual_fit'] = {ref: MANUAL_FIT[ref] for ref in sorted(MANUAL_FIT)}
            ev[name] = str(path)
        else:
            ev[name] = 'not supplied (board and schematic flags checked)'
    values, ev['mpn_values'] = mpn_values(ctx.board)
    return [f'S-4: {i}' for i in sorted(set(issues))] + values, ev


def s5(ctx):
    """The external J400 screw switch is the arming contact, isolated by 470 k on each side; D-R24-11: J400.2's own
    ESD clamp D402 (ESD103-B1-02EL) to GND is the one further member of BAT_SW_RETURN, ahead of R165."""
    issues, ev = [], {}
    pins = {f'{ref}.{p.GetNumber()}': p.GetNetname() for ref, f in ctx.fps.items() for p in f.Pads()}
    members = net_parts(ctx.board)
    for net, want in (('BAT_SW_SOURCE', {'J400', 'R80'}), ('BAT_SW_RETURN', {'J400', 'R165', 'D402'})):
        if members.get(net) != want:
            issues.append(f'S-5: {net} must touch only {sorted(want)}')
    for net, want in (('BAT_SW_SOURCE', {'J400.1', 'R80.2'}), ('BAT_SW_RETURN', {'J400.2', 'R165.1', 'D402.1'})):
        got = {pin for pin, n in pins.items() if n == net}
        if got != want:
            issues.append(f'S-5: {net} pads must be exactly {sorted(want)} (are {sorted(got)})')
    expected = {'J400.1': 'BAT_SW_SOURCE', 'J400.2': 'BAT_SW_RETURN', 'R80.1': 'BAT_IN',
                'R80.2': 'BAT_SW_SOURCE', 'R165.1': 'BAT_SW_RETURN', 'R165.2': 'BAT_ENABLE', 'U9.1': 'BAT_ENABLE',
                'D402.1': 'BAT_SW_RETURN', 'D402.2': 'GND'}
    for pin, net in expected.items():
        if pins.get(pin) != net:
            issues.append(f'S-5: {pin} must be {net} (is {pins.get(pin)})')
    clamp = ctx.fps.get('D402')
    if clamp is None:
        issues.append("S-5: D402 (J400.2's ESD clamp, D-R24-11) is missing")
    else:
        code = next((fld.GetText() for fld in clamp.GetFields() if fld.GetName() == 'LCSC'), None)
        if code != 'C535146' or clamp.GetValue() != 'ESD103-B1-02EL' or \
                sorted(p.GetNumber() for p in clamp.Pads() if p.GetNumber()) != ['1', '2']:
            issues.append(f'S-5: D402 must be the two-pad ESD103-B1-02EL C535146 (is {clamp.GetValue()} {code})')
    j400 = ctx.fps.get('J400')
    if j400 is not None and sorted(p.GetNumber() for p in j400.Pads() if p.GetNumber()) != ['1', '2']:
        issues.append('S-5: J400 must have exactly two switch contacts')
    for ref in ('R80', 'R165'):
        f = ctx.fps.get(ref)
        if f is None or parse_value(f.GetValue(), 'R') != 470e3:
            issues.append(f'S-5: {ref} must be 470k (external switch wire protection)')
    nets_of = part_nets(ctx.board)
    came = net_reach(nets_of, 'BAT_SW_SOURCE', skip={'J400'}, stop=RAILS | {'BAT_IN', 'BAT_ENABLE'})
    if 'BAT_SW_RETURN' in came:
        issues.append('S-5: a part bypasses the open J400 switch: ' + net_path(came, 'BAT_SW_RETURN'))
    nodes = copper_nodes(ctx.board)
    for start in ('BAT_SW_SOURCE', 'BAT_SW_RETURN'):
        foreign, count = copper_reach(nodes, start)
        ev[f'{start}_copper_items'] = count
        for label, (net, via) in sorted(foreign.items()):
            issues.append(f'S-5: {start} copper touches {label} ({net}) through {via}: switch contact / resistor bypass')
    return issues, ev


def barrel_shapes(board, nets=BARREL_NETS):
    """[(label, net, SHAPE)] of every plated barrel wall (via drill, plated pad hole) of `nets`."""
    import pcbnew
    out = []
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA' and t.GetNetname() in nets:
            p = t.GetPosition()
            out.append((f'via ({pcbnew.ToMM(p.x):.3f}, {pcbnew.ToMM(p.y):.3f})', t.GetNetname(),
                        pcbnew.SHAPE_CIRCLE(p, t.GetDrillValue() // 2)))
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname() in nets:
                out.append((f'{f.GetReference()}.{p.GetNumber()} hole', p.GetNetname(), p.GetEffectiveHoleShape()))
    return out


def barrel_rings(board, nets=BARREL_NETS):
    """[(label, net, layer, SHAPE)] of the inner-layer ring each plated barrel of `nets` keeps (flashed) on In1 / In2."""
    import pcbnew
    out = []
    items = [(f'via ({pcbnew.ToMM(t.GetPosition().x):.3f}, {pcbnew.ToMM(t.GetPosition().y):.3f})', t)
             for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() in nets]
    items += [(f'{f.GetReference()}.{p.GetNumber()}', p) for f in board.GetFootprints() for p in f.Pads()
              if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname() in nets]
    for label, item in items:
        for lay in (pcbnew.In1_Cu, pcbnew.In2_Cu):
            if item.IsOnLayer(lay) and item.FlashLayer(lay):
                out.append((f'{label} inner ring', item.GetNetname(), lay, item.GetEffectiveShape(lay)))
    return out


def s8(ctx, gap=BARREL_GAP, gnd_hazard=BARREL_GND_HAZARD):
    """R3-SAF-01 / R18-SAF-01: no In1 / In2 track or zone fill of another net within `gap` of a barrel wall of a
    BARREL_NETS net; GND counts only for the nets in `gnd_hazard` (the P-FET gate drive ACT_GATE / ACT_DRV and, since
    D-R19-01, PYRO1_OUT, the fire FET drain). D-R20-05 (R20-SAF-05): the same holds from an inner ring the barrel keeps
    on that layer (its copper is the barrel's net), so a protected terminal drops its unconnected inner rings."""
    import pcbnew
    import check_r8 as r8
    inner = (pcbnew.In1_Cu, pcbnew.In2_Cu)
    barrels = [(label, net, shape, None) for label, net, shape in barrel_shapes(ctx.board)]
    barrels += [(label, net, shape, lay) for label, net, lay, shape in barrel_rings(ctx.board)]
    issues, worst = [], {}
    # Every manufactured copper representation counts, including drawings, text and footprint zones.
    others = [(label, net, lay, shape, pad)
              for _, lay, shape, _, pad, net, label in copper_nodes(ctx.board)
              if lay in inner]
    for blabel, bnet, bshape, blay in barrels:
        for label, net, lay, shape, obj in others:
            if net == bnet or (net == 'GND' and bnet not in gnd_hazard) or (blay is not None and lay != blay) \
                    or not pcbnew.SHAPE.Collide(bshape, shape, pcbnew.FromMM(gap) - 1):
                continue
            g = r8.min_gap(bshape, shape, gap + 1)
            g = 0.0 if g is None else g
            key = (blabel, net, ctx.board.GetLayerName(lay))
            if key not in worst or g < worst[key]:
                worst[key] = g
    for (blabel, net, lay), g in sorted(worst.items()):
        issues.append(f'S-8: {net} copper on {lay} is {g:.3f} mm from the {blabel} '
                      f'{"" if blabel.endswith("inner ring") else "barrel "}of '
                      f'{next(b[1] for b in barrels if b[0] == blabel)} (minimum {gap} mm)')
    return issues, dict(barrels=sum(1 for b in barrels if b[3] is None), inner_rings=sum(1 for b in barrels if b[3] is not None),
                        gap_mm=gap, near={f'{k[0]} / {k[1]} / {k[2]}': round(v, 3) for k, v in sorted(worst.items())})


def track_graph(board, net, layers=None, lengths=None):
    """(pads, vias, edges) of `net`'s track graph: track ends, vias and pads as nodes ('P' + pad label, 'V' + via UUID,
    else ('N', layer, x um, y um)); a track end on another track's body (a T) splits that track there; a piece inside one
    node is no edge. `layers` (names) limits the tracks to those layers. edges: {key: (node a, node b, track)}; a dict
    passed as `lengths` receives {key: piece length in mm} (D-R21-07)."""
    import pcbnew
    pads, vias, segs = [], [], []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == net and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                pads.append((f'{f.GetReference()}.{p.GetNumber()}', f.GetReference(), p.GetNumber(), p))
    for t in board.GetTracks():
        if t.GetNetname() != net:
            continue
        if t.GetClass() == 'PCB_VIA':
            vias.append(t)
        elif layers is None or board.GetLayerName(t.GetLayer()) in layers:
            segs.append(t)

    def node(pt, lay):
        for lab, _, _, p in pads:
            if p.IsOnLayer(lay) and p.HitTest(pt):
                return 'P' + lab
        for v in vias:
            if (v.GetPosition() - pt).EuclideanNorm() <= v.GetWidth(lay) // 2:
                return 'V' + v.m_Uuid.AsString()
        return ('N', lay, round(pt.x / 1000), round(pt.y / 1000))
    edges = {}
    for t in segs:
        s, e = t.GetStart(), t.GetEnd()
        length = (e - s).EuclideanNorm()
        cuts = [0.0, 1.0]
        for o in segs:
            if o is t or o.GetLayer() != t.GetLayer() or length == 0:
                continue
            for q in (o.GetStart(), o.GetEnd()):
                k = ((q.x - s.x) * (e.x - s.x) + (q.y - s.y) * (e.y - s.y)) / length ** 2
                if 0 < k < 1 and math.hypot(q.x - s.x - k * (e.x - s.x), q.y - s.y - k * (e.y - s.y)) <= 1000:
                    cuts.append(k)
        cuts = sorted(set(cuts))
        for i in range(len(cuts) - 1):
            pa = pcbnew.VECTOR2I(int(round(s.x + cuts[i] * (e.x - s.x))), int(round(s.y + cuts[i] * (e.y - s.y))))
            pb = pcbnew.VECTOR2I(int(round(s.x + cuts[i + 1] * (e.x - s.x))), int(round(s.y + cuts[i + 1] * (e.y - s.y))))
            a, b = node(pa, t.GetLayer()), node(pb, t.GetLayer())
            if a != b:
                edges[f'{t.m_Uuid.AsString()}/{i}'] = (a, b, t)
                if lengths is not None:
                    lengths[f'{t.m_Uuid.AsString()}/{i}'] = pcbnew.ToMM(length) * (cuts[i + 1] - cuts[i])
    return pads, vias, edges


def simple_path_edges(edges, first, last):
    """R19-GATE-05: ({key: edge} of the edges that lie on some simple path between a node of `first` and a node of
    `last`, joined?). The graph gets a hub joined to every node of `first` and one joined to every node of `last`; an
    edge is kept when its biconnected block lies on the block-cut tree path between the two hubs. A side branch is
    dropped whole, a terminal-free loop hanging off one cut vertex included (leaf pruning kept such a loop and the run
    to it), while a loop on the path (two parallel vias, a bridge bar) stays."""
    from collections import defaultdict, deque
    hubs = (('HUB', 'first'), ('HUB', 'last'))
    every = dict(edges)
    for i, group in enumerate((first, last)):
        for n in group:
            every[('HUB', i, n)] = (hubs[i], n, None)
    adj = defaultdict(list)
    for k, (a, b, _) in every.items():
        if a != b:
            adj[a].append((k, b))
            adj[b].append((k, a))
    disc, low, blocks, stack_e, clock = {}, {}, [], [], 0
    for root in list(adj):                                   # iterative Hopcroft-Tarjan on the multigraph
        if root in disc:
            continue
        disc[root] = low[root] = clock
        clock += 1
        frames = [(root, None, iter(adj[root]))]
        while frames:
            u, via_key, it = frames[-1]
            for k, v in it:
                if k == via_key:
                    continue
                if v not in disc:
                    disc[v] = low[v] = clock
                    clock += 1
                    stack_e.append(k)
                    frames.append((v, k, iter(adj[v])))
                    break
                if disc[v] < disc[u]:
                    stack_e.append(k)
                    low[u] = min(low[u], disc[v])
            else:
                frames.pop()
                if frames:
                    parent = frames[-1][0]
                    low[parent] = min(low[parent], low[u])
                    if low[u] >= disc[parent]:
                        block = []
                        while True:
                            k = stack_e.pop()
                            block.append(k)
                            if k == via_key:
                                break
                        blocks.append(block)
    member = defaultdict(set)                                # node -> its blocks
    for i, block in enumerate(blocks):
        for k in block:
            member[every[k][0]].add(i)
            member[every[k][1]].add(i)
    if not member[hubs[0]] or not member[hubs[1]]:
        return {}, False
    nodes = {i: {every[k][j] for k in block for j in (0, 1)} for i, block in enumerate(blocks)}
    prev, queue = {('n', hubs[0]): None}, deque([('n', hubs[0])])
    while queue:                                             # the block-cut tree path between the hubs
        cur = queue.popleft()
        if cur == ('n', hubs[1]):
            break
        nxt = [('b', i) for i in member[cur[1]]] if cur[0] == 'n' else [('n', x) for x in nodes[cur[1]]]
        for item in nxt:
            if item not in prev:
                prev[item] = cur
                queue.append(item)
    if ('n', hubs[1]) not in prev:
        return {}, False
    on, cur = set(), ('n', hubs[1])
    while cur is not None:
        if cur[0] == 'b':
            on.add(cur[1])
        cur = prev[cur]
    return {k: every[k] for i in on for k in blocks[i] if every[k][2] is not None}, True


def fire_path(board, net, terminals):
    """(segments on the net's current path between the two terminal pad sets, connected?, terminal labels): the net's
    track graph (track ends, vias, pads as nodes) restricted to the copper on simple paths between the terminal sets
    (simple_path_edges): a sense tap ending in a resistor pad, or a loop on a side branch, is not fire copper; a branch
    inside one pad is no branch."""
    pads, _, edges = track_graph(board, net)
    term = [{lab for lab, ref, num, _ in pads if num in spec.get(ref, ())} for spec in terminals]
    kept, joined = simple_path_edges(edges, {'P' + lab for lab in term[0]}, {'P' + lab for lab in term[1]})
    unique = {e[2].m_Uuid.AsString(): e[2] for e in kept.values()}
    return list(unique.values()), joined, [sorted(t) for t in term]


def s9(ctx, floor=FIRE_MIN_W, narrow=FIRE_NARROW):
    """R3-GATE-07: current-path widths, with only the measured `narrow` list excepted."""
    import pcbnew
    mm = pcbnew.ToMM
    issues, ev, used = [], {}, set()
    for net, terminals in FIRE_TERMINALS.items():
        minimum = min(floor, 0.5) if net in FIRE_ONLY else floor  # AUD-6 / audit 2 item 3; BAT_IN stays 1.0 mm.
        segs, joined, term = fire_path(ctx.board, net, terminals)
        widths = sorted({round(mm(t.GetWidth()), 3) for t in segs})
        ev[net] = dict(terminals=term, path_segments=len(segs), widths_mm=widths, joined=joined, minimum_mm=minimum)
        if not joined:
            issues.append(f'S-9: {net}: no copper path between its power terminals {term}')
            continue
        for t in segs:
            w = mm(t.GetWidth())
            if w >= minimum - EPS:
                continue
            s, e = t.GetStart(), t.GetEnd()
            ends = tuple(round(v, 2) for v in sorted([(mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))])[0] +
                         sorted([(mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))])[1])
            length = mm(t.GetLength())
            hit = [k for k, x in enumerate(narrow) if x[0] == net and x[1] == ctx.board.GetLayerName(t.GetLayer())
                   and abs(x[2] - w) <= 0.005 and abs(x[3] - length) <= 0.01
                   and all(abs(a - b) <= 0.01 for a, b in zip(x[4], ends))]
            if hit:
                used.add(hit[0])
                continue
            issues.append(f'S-9: {net} fire-path track {w:.3f} mm wide, {length:.3f} mm long on '
                          f'{ctx.board.GetLayerName(t.GetLayer())} ({ends[0]}, {ends[1]})-({ends[2]}, {ends[3]}); '
                          f'minimum {minimum} mm ({"AUD-6" if net in FIRE_ONLY else "D-R2-02"})')
    issues += [f'S-9: stale FIRE_NARROW entry {x[:5]} ({x[5]})' for k, x in enumerate(narrow) if k not in used]
    ev['narrow_used'] = [narrow[k][5] for k in sorted(used)]
    return issues, ev


# K-power (R18-GATE-02 / R18-GATE-03). U9's input and output carry the whole board load (parts_budget.json
# c_camera_radio_gps_on: 11.25-13.06 W with every port on, the AUX allowance included, at most about 1.77 A at 7.4 V;
# D-R27-01 replaces round 18's pre-AUX 11.5 W; U9's current limit 3.95-4.86 A, calculated). Their copper is held at its
# designed width the way S-9 holds the fire path: J1.1 -> U9.5 (IN, through C88) at BAT_IN's 1.0 mm, U9.6 -> its In2
# RAW_PROTECTED vias (OUT) at 0.7 mm (tools/ipc2152.py: 0.68 mm for a 30 C rise at 2.9 A, external, no plane credit;
# Inference). Only the named, measured POWER_NARROW entries are excepted, matched exactly (a narrower, longer, moved or
# unused entry fails). The vias on each path keep their designed count and size, the OUT vias joined to the In2
# RAW_PROTECTED fill.
# R19-GATE-04: every path also names its design current (amps, with its basis); its floor, the reviewed drawn width, must
# be at least the IPC-2152 width for that current at a POWER_RISE rise (tools/ipc2152.py: external fit, 35 um, no plane
# credit, a long-conductor upper bound; Inference), or the table fails. The R19 rails (D-R18-11's VLOGIC, PORT_5V3,
# CAM_5V, PORT_4V8, 3V3) each have their current paths here. Design currents (parts_budget.json, maker ratings):
#   BAT_IN / RAW_PROTECTED 2.9 A  D-R3-03's U9 sizing current (0.68 mm)
#   PORT_5V3 out of U400   1.810 A  buck_camera_short_radio_gps_normal_A: camera shorted at its switch limit, ports on
#   PORT_5V3 into U401, PORT_4V8 out of it and to each port  1.9 A  ldo_shared_current_limit_A max: one port shorted
#   PORT_5V3 into U402, CAM_5V to J9  1.249 A  switch_limit_A camera max: the camera shorted
#   3V3 out of U2          2.0 A   AP63203 rated output (Diodes DS41271)
#   VLOGIC into U2         1.294 A U2's input at that rating from the 6.0 V pack floor: 2.0 x 3.3 / (0.85 x 6.0), 85 %
#                                  efficiency (Inference)
POWER_RISE = 30.0               # C, the U9 OUT basis above
POWER_PATHS = (   # end None: every via of the net (the plane transitions) ends the path
    # R19-GATE-05: at least one IN via of >= 1.0 / 0.5 mm; a parallel one beside it may be the 0.5 / 0.3 mm minimum.
    dict(name='U9 IN', net='BAT_IN', start={'J1': ('1',)}, end={'U9': ('5',)}, through={'C88': ('1',)}, floor=1.0,
         amps=2.9, vias=dict(count=1, drill=0.5, pad=1.0, plane=None, others=(0.5, 0.3))),
    dict(name='U9 OUT', net='RAW_PROTECTED', start={'U9': ('6',)}, end=None, through={}, floor=0.7, amps=2.9,
         vias=dict(count=2, drill=0.3, pad=0.5, plane='In2.Cu')),
    # D-R19-09 (R19-PWR-01): the supply feeds the round 19 pass doubled keep two vias each (an open barrel no longer
    # drops the load). R19-GATE-04: U401's IN and OUT runs are held at their 0.4 mm drawn width; the 0.25 mm links
    # between its paired pins (0.5 mm DSK pitch) are named POWER_NARROW entries.
    dict(name='U401 IN', net='PORT_5V3', start={'U401': ('9', '10')}, end=None, through={}, floor=0.4, amps=1.9,
         vias=dict(count=2, drill=0.3, pad=0.5, plane='In2.Cu')),
    dict(name='U401 EN', net='PORT_5V3', start={'U401': ('7',)}, end=None, through={}, floor=0.2,
         vias=dict(count=2, drill=0.3, pad=0.5, plane='In2.Cu')),                # an EN input: no design current
    dict(name='U401 OUT', net='PORT_4V8', start={'U401': ('1', '2')}, end=None, through={}, floor=0.4, amps=1.9,
         vias=dict(count=2, drill=0.3, pad=0.5, plane='In2.Cu')),
    dict(name='U402 IN', net='PORT_5V3', start={'U402': ('1',)}, end=None, through={'C430': ('1',)}, floor=0.4,
         amps=1.249, vias=dict(count=2, drill=0.3, pad=0.5, plane='In2.Cu')),
    # D-R19-14: the AUX port's F.Cu feed (In2 under J440 is 3V3) leaves the In2 PORT_4V8 region through two vias,
    # (29.75, 9.95) and (30.5, 9.95). Its path is held to F.Cu: through (29.75, 9.95) U401's B.Cu run reaches a third
    # via (29.75, 11.65 since D-R24-09), which would otherwise count for the feed and hide the loss of (30.5, 9.95)
    # (CAD hand-back).
    dict(name='J440 feed', net='PORT_4V8', start={'J440': ('1',)}, end=None, through={}, floor=0.4, amps=1.9,
         layers=('F.Cu',), vias=dict(count=2, drill=0.3, pad=0.5, plane='In2.Cu')),
    # R19-GATE-04: the GPS and radio ports' B.Cu feeds from their In2 PORT_4V8 via (one each, as drawn).
    dict(name='J410 feed', net='PORT_4V8', start={'J410': ('1',)}, end=None, through={}, floor=0.4, amps=1.9,
         vias=dict(count=1, drill=0.3, pad=0.5, plane='In2.Cu')),
    dict(name='J420 feed', net='PORT_4V8', start={'J420': ('1',)}, end=None, through={'C421': ('1',)}, floor=0.4,
         amps=1.9, vias=dict(count=1, drill=0.3, pad=0.5, plane='In2.Cu')),
    # R19-GATE-04: the camera supply, U402's output to J9.1 through C431 (B.Cu, no via).
    dict(name='CAM_5V out', net='CAM_5V', start={'U402': ('6',)}, end={'J9': ('1',)}, through={'C431': ('1',)},
         floor=0.4, amps=1.249, vias=dict(count=0, drill=0.3, pad=0.5, plane=None)),
    dict(name='C84 hold-up', net='VLOGIC', start={'C84': ('1',)}, end={'U11': ('1', '8')}, through={}, floor=0.4,
         amps=1.294, vias=dict(count=2, drill=0.3, pad=0.5, plane=None)),
    # R19-GATE-04: the logic rail's trunk, U11's output to U2's input (B.Cu, through C99).
    dict(name='VLOGIC trunk', net='VLOGIC', start={'U11': ('1', '8')}, end={'U2': ('2', '3')}, through={'C99': ('1',)},
         floor=0.4, amps=1.294, vias=dict(count=0, drill=0.3, pad=0.5, plane=None)),
    # D-R19-09 (R19-GATE-04): the two buck outputs. U400's L400.2 reaches In2 PORT_5V3 through two vias; U2's L1.2
    # reaches In2 3V3 through the direct via (23.1, 78.1) and through the F.Cu bridge over the RAW / VLOGIC corridor,
    # whose west via (26.4, 79.26) sits in the In2 RAW region and joins only F.Cu and B.Cu (a named bridge, measured).
    dict(name='U400 OUT', net='PORT_5V3', start={'L400': ('2',)}, end=None, through={'C404': ('1',)}, floor=0.4,
         amps=1.81, vias=dict(count=2, drill=0.3, pad=0.5, plane='In2.Cu')),
    dict(name='U2 OUT', net='3V3', start={'L1': ('2',)}, end=None, through={'C8': ('1',)}, floor=0.4, amps=2.0,
         vias=dict(count=2, drill=0.3, pad=0.5, plane='In2.Cu',
                   bridges=(((26.4, 79.26), 'the F.Cu bridge west end over the In2 RAW region: F.Cu and B.Cu only, '
                                            'measured on the R10 board (D-R19-09)'),))),
)
POWER_NARROW = [  # (net, layer, width mm, length mm, (x0, y0, x1, y1) ends sorted, reason), measured on the R10 board
    # D-R24-17: U9's input runs straight up U9.5's axis through C88.1 (C88 on that axis below U9), so the bar entry runs
    # on to C88.1 at its 0.3 mm width (0.76 mm outside the bar; K-width's 2 mm limit holds) and the 0.7 mm bypass section
    # is the one straight piece from the IN run's tap T to C88.1.
    ('BAT_IN', 'B.Cu', 0.3, 1.96, (18.25, 81.6, 18.25, 83.56), 'U9.5 IN bar entry to C88.1 at its 0.3 mm width'),
    ('BAT_IN', 'B.Cu', 0.7, 1.74, (18.25, 83.56, 18.25, 85.3), 'C88.1 local feed from the IN run\'s tap T'),
    ('RAW_PROTECTED', 'B.Cu', 0.3, 1.8, (18.75, 79.8, 18.75, 81.6), 'U9.6 OUT bar entry at its 0.3 mm width'),
    ('PORT_5V3', 'B.Cu', 0.25, 0.5, (26.45, 12.6, 26.45, 13.1), 'U401.10 to U401.9 IN pin link at the 0.5 mm DSK pitch'),
    # D-R24-17: U401's OUT run leaves the U401.1 / U401.2 link at a T between the pins (no 90-degree bend in a pad).
    ('PORT_4V8', 'B.Cu', 0.25, 0.25, (28.75, 12.6, 28.75, 12.85), 'U401.1 to the OUT run\'s T at the 0.5 mm DSK pitch'),
    ('PORT_4V8', 'B.Cu', 0.25, 0.25, (28.75, 12.85, 28.75, 13.1), 'U401.2 to the OUT run\'s T at the 0.5 mm DSK pitch'),
]
# The fire current returns from Q124's source pads 1-3 to In1 GND through an F.Cu bar and two via stubs (D-R3-03: the
# 0.3 mm bar rises 16 C at 4.2 A for 20 ms, adiabatic Inference) and >= 2 vias into the In1 GND fill.
FIRE_RETURN = dict(ref='Q124', pads=('1', '2', '3'), net='GND', width=0.3,
                   vias=dict(count=2, drill=0.3, pad=0.5, plane='In1.Cu'))


def path_graph(board, net, start, end=None, layers=None):
    """fire_path's track graph of `net` between the `start` pads and the `end` pads (None: every via of the net), kept
    to the copper on simple paths between them (simple_path_edges); `layers` limits the tracks to those layers (a feed
    drawn on one layer: its own vias, not copper beyond them). Returns (segments, joined, vias on the path, pad labels
    on the path)."""
    pads, vias, edges = track_graph(board, net, layers)
    first = {'P' + lab for lab, ref, num, _ in pads if num in start.get(ref, ())}
    last = ({'V' + v.m_Uuid.AsString() for v in vias} if end is None else
            {'P' + lab for lab, ref, num, _ in pads if num in end.get(ref, ())})
    kept, joined = simple_path_edges(edges, first, last)
    on = {x for a, b, _ in kept.values() for x in (a, b) if isinstance(x, str)}
    tracks = {e[2].m_Uuid.AsString(): e[2] for e in kept.values()}
    return (list(tracks.values()), joined, [v for v in vias if 'V' + v.m_Uuid.AsString() in on],
            sorted(n[1:] for n in on if n.startswith('P')))


def plane_via(board, via, layer, net):
    """True when `via` has a pad on `layer` and that pad touches the layer's zone fill of `net`."""
    import pcbnew
    if not via.FlashLayer(layer):
        return False
    pad = pcbnew.SHAPE_CIRCLE(via.GetPosition(), via.GetWidth(layer) // 2)
    return any(not z.GetIsRuleArea() and z.GetNetname() == net and z.IsOnLayer(layer) and z.HasFilledPolysForLayer(layer)
               and z.GetFilledPolysList(layer).Collide(pad, 0) for z in board.Zones())


def via_issues(board, label, vias, spec, net):
    """Count, drill, pad and (spec['plane']) plane connection of the vias carrying a power or return current. A via
    named in spec['bridges'] ((x, y) mm, measured reason) is a layer-to-layer bridge on the path: its size is checked,
    it needs no plane join and does not count; a named bridge that is not on the path fails (D-R19-09). With
    spec['others'] = (pad, drill) mm (R19-GATE-05, the D-R18-11 wording), `count` vias must meet the spec size and every
    further via only `others` (a parallel board-standard via beside the sized one)."""
    import pcbnew
    mm = pcbnew.ToMM
    issues, counted, used = [], [], set()
    bridges = spec.get('bridges', ())
    others = spec.get('others')
    sized = 0
    for v in vias:
        xy = (mm(v.GetPosition().x), mm(v.GetPosition().y))
        at = f'({xy[0]:.3f}, {xy[1]:.3f})'
        drill, pad = mm(v.GetDrillValue()), mm(v.GetWidth(pcbnew.F_Cu))
        big = drill >= spec['drill'] - EPS and pad >= spec['pad'] - EPS
        if others is None and not big:
            issues.append(f'{label}: via {at} {pad:.3f} / {drill:.3f} mm; at least {spec["pad"]} / {spec["drill"]} mm')
        elif others is not None and not big and (drill < others[1] - EPS or pad < others[0] - EPS):
            issues.append(f'{label}: via {at} {pad:.3f} / {drill:.3f} mm; a further via needs at least '
                          f'{others[0]} / {others[1]} mm')
        bridge = next((k for k, (b, _) in enumerate(bridges) if math.dist(b, xy) <= 0.02), None)
        if bridge is not None:
            used.add(bridge)
            continue
        counted.append(v)
        sized += big
        if spec['plane'] and not plane_via(board, v, board.GetLayerID(spec['plane']), net):
            issues.append(f'{label}: via {at} is not joined to the {spec["plane"]} {net} fill')
    if others is not None and sized < spec['count']:
        issues.insert(0, f'{label}: {sized} via(s) of at least {spec["pad"]} / {spec["drill"]} mm on the path; '
                         f'{spec["count"]} required (further vias >= {others[0]} / {others[1]} mm)')
    elif len(counted) < spec['count']:
        issues.insert(0, f'{label}: {len(counted)} via(s) on the path; at least {spec["count"]} required')
    issues += [f'{label}: named bridge via {b} is not on the path ({reason})' for k, (b, reason) in enumerate(bridges)
               if k not in used]
    return issues


def power_paths(board, paths=POWER_PATHS, narrow=POWER_NARROW):
    """R18-GATE-02 / R18-GATE-03: the U9 IN / OUT paths' widths (named exceptions only) and vias."""
    import pcbnew
    mm = pcbnew.ToMM
    issues, ev, used = [], {}, set()
    for spec in paths:
        name, net, floor = spec['name'], spec['net'], spec['floor']
        segs, joined, vias, on = path_graph(board, net, spec['start'], spec['end'], spec.get('layers'))
        ev[name] = dict(net=net, path_segments=len(segs), widths_mm=sorted({round(mm(t.GetWidth()), 3) for t in segs}),
                        joined=joined, floor_mm=floor, pads=on,
                        vias=[[round(mm(v.GetPosition().x), 3), round(mm(v.GetPosition().y), 3),
                               round(mm(v.GetWidth(pcbnew.F_Cu)), 3), round(mm(v.GetDrillValue()), 3)] for v in vias])
        if not joined:
            issues.append(f'{name}: no {net} copper path from {spec["start"]} to '
                          f'{spec["end"] or "a via of the net"}')
            continue
        if 'amps' in spec:                                   # R19-GATE-04: the floor holds the IPC-2152 width
            import ipc2152
            need = max(ipc2152.ipc_width(POWER_RISE, lay, spec['amps'])
                       for lay in {board.GetLayerName(t.GetLayer()) for t in segs} or {'F.Cu'})
            ev[name].update(amps=spec['amps'], ipc_floor_mm=round(need, 3))
            if floor < need - EPS:
                issues.append(f'{name}: floor {floor} mm is below the IPC-2152 width {need:.3f} mm for '
                              f'{spec["amps"]} A at a {POWER_RISE:g} C rise (tools/ipc2152.py)')
        issues += [f'{name}: the {net} path does not pass {ref}.{num}' for ref, nums in spec['through'].items()
                   for num in nums if f'{ref}.{num}' not in on]
        for t in segs:
            w = mm(t.GetWidth())
            if w >= floor - EPS:
                continue
            a, b = sorted([(mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y))])
            ends = tuple(round(v, 2) for v in a + b)
            length = mm(t.GetLength())
            hit = [k for k, x in enumerate(narrow) if x[0] == net and x[1] == board.GetLayerName(t.GetLayer())
                   and abs(x[2] - w) <= 0.005 and abs(x[3] - length) <= 0.01
                   and all(abs(c - d) <= 0.01 for c, d in zip(x[4], ends))]
            if hit:
                used.add(hit[0])
                continue
            issues.append(f'{name}: {net} track {w:.3f} mm wide, {length:.3f} mm long on '
                          f'{board.GetLayerName(t.GetLayer())} ({ends[0]}, {ends[1]})-({ends[2]}, {ends[3]}); '
                          f'minimum {floor} mm')
        issues += via_issues(board, name, vias, spec['vias'], net)
    issues += [f'stale POWER_NARROW entry {x[:5]} ({x[5]})' for k, x in enumerate(narrow) if k not in used]
    ev['narrow_used'] = [narrow[k][5] for k in sorted(used)]
    return issues, ev


def fire_return(board, spec=FIRE_RETURN):
    """R18-GATE-03: the tracks leaving Q124's source pads, followed through plain track joints until they reach a via
    or another part's pad: each at least spec width, every source pad on them, and their vias (count, size, plane)."""
    import pcbnew
    mm = pcbnew.ToMM
    label = f'{spec["ref"]} fire return'
    f = board.FindFootprintByReference(spec['ref'])
    if f is None:
        return [f'{label}: {spec["ref"]} missing'], {}
    net = spec['net']
    sources = [p for p in f.Pads() if p.GetNumber() in spec['pads'] and p.GetNetname() == net]
    if sorted(p.GetNumber() for p in sources) != sorted(spec['pads']):
        return [f'{label}: source pads {spec["pads"]} are not all on {net}'], {}
    tracks = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == net]
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == net]
    others = [p for g in board.GetFootprints() for p in g.Pads() if p.GetNetname() == net and p not in sources]
    near = lambda a, b: (a - b).EuclideanNorm() <= 1000                    # noqa: E731

    def on_body(t, q):
        a, b = t.GetStart(), t.GetEnd()
        dx, dy = b.x - a.x, b.y - a.y
        den = dx * dx + dy * dy
        k = max(0., min(1., ((q.x - a.x) * dx + (q.y - a.y) * dy) / den)) if den else 0.
        return math.hypot(q.x - a.x - k * dx, q.y - a.y - k * dy) <= t.GetWidth() / 2

    def in_source(t, q):
        return any(p.IsOnLayer(t.GetLayer()) and p.HitTest(q) for p in sources)
    group = {t.m_Uuid.AsString(): t for t in tracks if any(in_source(t, q) for q in (t.GetStart(), t.GetEnd()))}
    reached, queue = {}, list(group.values())
    while queue:
        t = queue.pop()
        for q in (t.GetStart(), t.GetEnd()):
            if in_source(t, q):
                continue
            via = next((v for v in vias if (v.GetPosition() - q).EuclideanNorm() <= v.GetWidth(t.GetLayer()) // 2), None)
            if via is not None:
                reached[via.m_Uuid.AsString()] = via
                continue
            if any(p.IsOnLayer(t.GetLayer()) and p.HitTest(q) for p in others):
                continue
            for o in tracks:
                uid = o.m_Uuid.AsString()
                if uid in group or o.GetLayer() != t.GetLayer():
                    continue
                if near(o.GetStart(), q) or near(o.GetEnd(), q) or on_body(o, q) \
                        or any(on_body(t, r) for r in (o.GetStart(), o.GetEnd())):
                    group[uid] = o
                    queue.append(o)
    issues = []
    for t in group.values():
        w = mm(t.GetWidth())
        if w < spec['width'] - EPS:
            issues.append(f'{label}: {net} track {w:.3f} mm wide on {board.GetLayerName(t.GetLayer())} '
                          f'({mm(t.GetStart().x):.3f}, {mm(t.GetStart().y):.3f})-({mm(t.GetEnd().x):.3f}, '
                          f'{mm(t.GetEnd().y):.3f}); minimum {spec["width"]} mm')
    for p in sources:
        if not any(p.IsOnLayer(t.GetLayer()) and p.GetEffectiveShape(t.GetLayer()).Collide(
                t.GetEffectiveShape(t.GetLayer()), 0) for t in group.values()):
            issues.append(f'{label}: source pad {spec["ref"]}.{p.GetNumber()} is on no return track')
    issues += via_issues(board, label, list(reached.values()), spec['vias'], net)
    return issues, dict(tracks=len(group), widths_mm=sorted({round(mm(t.GetWidth()), 3) for t in group.values()}),
                        vias=[[round(mm(v.GetPosition().x), 3), round(mm(v.GetPosition().y), 3),
                               round(mm(v.GetWidth(pcbnew.F_Cu)), 3), round(mm(v.GetDrillValue()), 3)]
                              for v in reached.values()])


# D-R20-02 (R20-PWR-02) / D-R21-02 (R21-PWR-01 / R21-GATE-01): every regulator sense, over-voltage, enable and current-
# limit tap must stay joined to its source through same-net copper when any one via of the net opens (a barrel crack):
# (net, tap pad, source pads, why). Round 19's R402.1 hung on the OUT via (29.75, 12.6) alone (open: FB falls to GND
# through R403 and the LDO drives the ports to its dropout); round 20's U2.1 (the 3V3 buck's FB / output sense) on the
# via (23.2, 68.6) alone. The list is the gate lens's survey of round 21 (every FB, OVLO, EN and ILIM node and its
# divider ends); a single point left on purpose is an exact SINGLE_OPEN_EXCEPTIONS entry.
SINGLE_OPEN_TAPS = (
    ('PORT_4V8', 'R402.1', ('U401.1', 'U401.2'), "U401's feedback divider top (R20-PWR-02)"),
    ('3V3', 'U2.1', ('L1.2',), "U2's FB / output-sense pin (R21-PWR-01)"),
    ('PORT_5V3', 'R400.1', ('L400.2',), "U400's feedback divider top"),
    ('PORT_FB_TOP', 'R400.2', ('R404.1',), "U400's feedback divider middle"),
    ('PORT_FB', 'U400.1', ('R404.2', 'R401.1'), "U400's FB pin"),
    ('PORT_LDO_FB', 'U401.3', ('R402.2', 'R403.1'), "U401's FB pin"),
    ('BAT_IN', 'R82.1', ('U9.5',), "U9's OVLO divider top"),
    ('BAT_OVLO', 'U9.2', ('R82.2', 'R83.1'), "U9's OVLO pin"),
    ('BAT_ENABLE', 'R81.1', ('U9.1',), "U9's EN pull-down (R20-SAF-01)"),
    ('BAT_ENABLE', 'C87.1', ('U9.1',), "U9's EN filter"),
    ('BAT_ILIM', 'R84.1', ('U9.9',), "U9's ILIM"),
    ('USB_LIMITED', 'R87.1', ('U10.6',), "U11's USB over-voltage divider top"),
    ('USB_OVLO', 'U11.5', ('R87.2', 'R88.1'), "U11's USB OV pin"),
    ('LOGIC_ILIM', 'R86.1', ('U11.10',), "U11's ILIM"),
    ('USB_ILIM', 'R85.1', ('U10.5',), "U10's ILIM"),
    ('CAM_ILIM', 'R430.1', ('U402.5',), "U402's ILIM"),
    ('GND', 'R401.2', ('U400.4',), "U400's feedback divider bottom"),
    ('GND', 'R403.2', ('U401.4', 'U401.6', 'U401.11'), "U401's feedback divider bottom"),
    ('GND', 'R83.2', ('U9.8',), "U9's OVLO divider bottom"),
    ('GND', 'R81.2', ('U9.8',), "U9's EN pull-down bottom"),
    ('GND', 'C87.2', ('U9.8',), "U9's EN filter bottom"),
    ('GND', 'R84.2', ('U9.8',), "U9's ILIM bottom"),
    ('GND', 'R85.2', ('U10.2',), "U10's ILIM bottom"),
    ('GND', 'R86.2', ('U11.3', 'U11.4', 'U11.6', 'U11.12'), "U11's ILIM bottom"),
    ('GND', 'R88.2', ('U11.3', 'U11.4', 'U11.6', 'U11.12'), "U11's USB OV divider bottom"),
    ('GND', 'R430.2', ('U402.2',), "U402's ILIM bottom"),
    # D-R22-02 (R22-POWER-01 / -02): the TPS2553s' own GND pins and the USB-C CC Rd returns, to the board's ground
    # (J1.2), and the power-state monitor inputs: PA6's VLOGIC sense (R60, the brown-out shed trigger), PA4's ST line
    # and R91, its pull-up, on 3V3.
    ('GND', 'U10.2', ('J1.2',), "U10's (TPS2553, USB limiter) GND pin (R22-POWER-01)"),
    ('GND', 'R7.2', ('J1.2',), 'R7 (USB-C CC1 Rd) GND'),
    ('GND', 'U402.2', ('J1.2',), "U402's (TPS2553, camera switch) GND pin (R22-POWER-01)"),
    ('GND', 'R8.2', ('J1.2',), 'R8 (USB-C CC2 Rd) GND'),
    ('VLOGIC', 'R60.1', ('U11.1', 'U11.8'), "R60, PA6's VLOGIC sense divider top (R22-POWER-02)"),
    ('LOGIC_SOURCE_ST', 'U1.28', ('U11.9',), "PA4, U11's ST status line (R22-POWER-02)"),
    ('3V3', 'R91.1', ('L1.2',), "R91, the ST pull-up's 3V3 end (R22-POWER-02)"),
    # D-R23-01 (R23-MCU-02): BOOT0's only pull-down and the two VCAP capacitors of the core LDO.
    ('BOOT0', 'U1.94', ('R5.1',), "BOOT0's pull-down R5 (R23-MCU-02)"),
    ('VCAP1', 'U1.48', ('C19.1',), "VCAP1's 2.2 uF capacitor C19 (R23-MCU-02)"),
    ('VCAP2', 'U1.73', ('C20.1',), "VCAP2's 2.2 uF capacitor C20 (R23-MCU-02)"),
    # D-R23-02 (R23-SAFETY-05): the load switch's gate drive from R121 to each FET's gate.
    ('ACT_GATE', 'Q120.4', ('R121.1',), "Q120's gate drive from R121 (R23-SAFETY-05)"),
    ('ACT_GATE', 'Q121.4', ('R121.1',), "Q121's gate drive from R121"),
    # D-R23-11 (R23-GATE-07): the IMU's only power-ground pins.
    ('GND', 'U4.6', ('J1.2',), "U4's (IMU) power ground pin 6 (R23-GATE-07)"),
    ('GND', 'U4.7', ('J1.2',), "U4's (IMU) power ground pin 7 (R23-GATE-07)"),
)
# (tap pad, via label as copper_nodes prints it, measured reason): the single points kept on purpose. An entry no longer
# met fails as stale, as POUR_DEBRIS does.
_ILIM_OPEN = ('TPS2553 SLVS841G section 8.5.1 p16: the current-limit threshold is proportional to the current sourced '
              'out of ILIM, so an open ILIM leg sets a lower limit (fail-safe; open-pin behaviour itself is not stated '
              'by TI: Inference)')
_U10_GND_OPEN = ("U10's only GND via (a B.Cu island with U10.2 and R7.2): open floats the TPS2553's ground (TI SLVS841G "
                 'states no open-GND behaviour: Inference); bench USB loss only. Second via at the next board change')
_U4_GND_OPEN = ("the IMU's only power-ground via (pins 6 / 7, 'GND, 0 V supply', DS15034 Rev 1 pin table): open, U4's "
                'supply ground floats and the IMU is dead (behaviour not stated by ST: Inference), so launch is not detected '
                'and the primary does not fire (fail-safe; the Blue Jay covers recovery) and roll control is lost. Second '
                'via at the next board change')
SINGLE_OPEN_EXCEPTIONS = [
    ('R87.1', 'via USB_LIMITED (22.00, 62.25)',
     "U11's USB over-voltage divider top off its In2 run: RAW_ACT (x 22.8) and PYRO1_CONT_MID (y 61.8) leave no B.Cu "
     'second path; open, the USB over-voltage cut-off is lost (USB is bench power only)'),
    # D-R24-10: R87.1's USB input via (16.0, 28.0) has a second barrel (16.6, 28.0); its entry is gone.
    ('R85.1', 'via USB_ILIM (14.82, 26.00)', "U10's ILIM: " + _ILIM_OPEN),
    # D-R22-02 (R22-POWER-01): this GND via is a TPS2553's only ground, so an open floats the IC's ground, not only
    # R_ILIM's return. D-R24-07: U402's island (U402.2 / R430.2) has a second via (32.3, 60.1); its entries are gone.
    ('R85.2', 'via GND (9.00, 27.84)', _U10_GND_OPEN),
    ('U10.2', 'via GND (9.00, 27.84)', _U10_GND_OPEN),
    ('R7.2', 'via GND (9.00, 27.84)', 'R7 (CC1 Rd) shares U10.2\'s island: ' + _U10_GND_OPEN),
    ('R8.2', 'via GND (9.95, 30.60)',
     "R8 (CC2 Rd)'s only GND via (a B.Cu island): open, a USB-C source sees no CC2 sink (with R7's island open too, no "
     'sink at all); bench USB only. Second via at the next board change'),
    # D-R22-02 (R22-POWER-02): the power-state monitor inputs R60.1 / U1.28 / R91.1 each have a second via since
    # D-R24-08; their entries are gone.
    # D-R23-01 (R23-MCU-02): measured on 5516eeec; each the net's only via. D-R24-04 / -03 give VCAP2 (U1.73) and BOOT0
    # (U1.94) a second via; D-R24-09 puts U401's divider beside it (U401.3: no via).
    ('U1.48', 'via VCAP1 (29.25, 38.00)',
     "VCAP1's only link to C19: open, the core LDO keeps one 2.2 uF instead of DS12110 Rev 8's two (Table 124 p. 216: CEXT "
     '2.2 uF +/-20 %, ESR < 100 mOhm); its stability then is an Inference'),
    # D-R23-02 (R23-SAFETY-05): the Q120.4 / Q121.4 gate drives from R121 each have a second via since D-R24-02.
    # D-R23-11 (R23-GATE-07): the GND via under U4 alone carries U4.6 / U4.7 (U4.2 / U4.3 reach GND another way).
    ('U4.6', 'via GND (16.75, 47.60)', _U4_GND_OPEN),
    ('U4.7', 'via GND (16.75, 47.60)', _U4_GND_OPEN),
    ('R81.1', 'via BAT_ENABLE (17.10, 82.80)',
     "D-R21-05: R81 sits at U9's end on F.Cu; EN still crosses this one via from the F.Cu run to U9.1 on B.Cu (no B.Cu "
     'spot at U9.1, D-R20-01): respin item, U9 west cell re-laid'),
    ('C87.1', 'via BAT_ENABLE (17.10, 82.80)', 'as R81.1: C87 sits beside R81 at U9\'s end (D-R21-05)'),
]


def _copper_adjacency(nodes, net):
    """({key: label}, {key: set(key)}) of `net`'s copper nodes touching on a shared layer (a pad or via spans its
    layers under one key)."""
    import pcbnew
    mine = [n for n in nodes if n[5] == net]
    label = {n[0]: n[6] for n in mine}
    adj = {k: set() for k in label}
    by_layer = {}
    for n in mine:
        by_layer.setdefault(n[1], []).append(n)
    for ns in by_layer.values():
        ns.sort(key=lambda n: n[3][0])
        for i, a in enumerate(ns):
            for c in ns[i + 1:]:
                if c[3][0] > a[3][2]:
                    break
                if a[0] == c[0] or a[3][1] > c[3][3] or c[3][1] > a[3][3]:
                    continue
                if pcbnew.SHAPE.Collide(a[2], c[2], 0):
                    adj[a[0]].add(c[0])
                    adj[c[0]].add(a[0])
    return label, adj


def single_via_opens(board, taps=SINGLE_OPEN_TAPS, exceptions=None):
    """(issues, evidence): every tap pad reaches one of its source pads through same-net copper (pads, tracks, vias,
    fill pieces touching on a shared layer; a via joins its layers) with the board intact and with any one via of the
    net removed. A single point is allowed only by an exact SINGLE_OPEN_EXCEPTIONS entry; an entry no longer met (its
    pads present) is stale."""
    exceptions = SINGLE_OPEN_EXCEPTIONS if exceptions is None else exceptions
    nodes = copper_nodes(board)
    issues, ev, used, graphs = [], {}, set(), {}
    for net, tap, sources, why in taps:
        if net not in graphs:
            graphs[net] = _copper_adjacency(nodes, net)
        label, adj = graphs[net]
        start = {k for k, v in label.items() if v == tap}
        goal = {k for k, v in label.items() if v in sources}

        def path(skip=None):
            """One tap-to-source node path avoiding `skip` (None when there is none)."""
            parent = {k: None for k in start if k != skip}
            todo = list(parent)
            while todo:
                k = todo.pop(0)
                if k in goal:
                    out = []
                    while k is not None:
                        out.append(k)
                        k = parent[k]
                    return out
                for m in adj[k]:
                    if m != skip and m not in parent:
                        parent[m] = k
                        todo.append(m)
            return None
        first = path()
        if not start or not goal or first is None:
            issues.append(f'{tap} ({why}) is not joined to {"/".join(sources)} on {net}')
            continue
        # only a via on one path can be needed by every path
        cut = sorted(label[k] for k in first if label[k].startswith('via ') and path(k) is None)
        for c in cut:
            hit = next((i for i, x in enumerate(exceptions) if x[0] == tap and x[1] == c), None)
            if hit is not None:
                used.add(hit)
                continue
            issues.append(f'{tap} ({why}) hangs on one via: opening {c} cuts it off from {"/".join(sources)}')
        ev[tap] = dict(net=net, single_points=cut)
    present = {f'{f.GetReference()}.{p.GetNumber()}' for f in board.GetFootprints() for p in f.Pads()}
    listed = {t[1] for t in taps}
    issues += [f'stale SINGLE_OPEN_EXCEPTIONS entry {x[0]} / {x[1]} ({x[2][:60]})' for i, x in enumerate(exceptions)
               if i not in used and x[0] in present and x[0] in listed]
    return issues, ev


def k_power(ctx):
    issues, ev = power_paths(ctx.board)
    found, ev['fire_return'] = fire_return(ctx.board)
    taps, ev['single_via_open_taps'] = single_via_opens(ctx.board)
    return [f'K-power: {i}' for i in issues + found + taps], ev


def default_clearance(board):
    import pcbnew
    try:
        return pcbnew.ToMM(board.GetDesignSettings().m_NetSettings.GetDefaultNetclass().GetClearance())
    except Exception:                                      # an older API or no net class: the documented default
        return DEFAULT_CLEARANCE


def s6(ctx):
    """External ports (O1 / O2 / F10): no port net shares a part, a copper item or the board default clearance with
    pyro / arming copper."""
    import pcbnew
    import check_r8 as r8
    issues, ev = [], {}
    for ref, nets in sorted(part_nets(ctx.board).items()):
        if ref == MCU_REF:
            continue                                       # the MCU is the intended common node (firmware, F10)
        ports, safe =sorted(n for n in nets if PORT_NET.match(n)), sorted(n for n in nets if SAFE_NET.match(n))
        if ports and safe:
            issues.append(f'S-6: {ref} joins port nets {ports} to pyro / arming nets {safe}')
    clr = default_clearance(ctx.board)
    ev['clearance_mm'] = clr
    safe = ctx.net_items(lambda n: bool(SAFE_NET.match(n or '')))
    worst = None
    for label, net, lay, shape, _ in ctx.net_items(lambda n: bool(PORT_NET.match(n or ''))):
        for l2, n2, lay2, s2, _ in safe:
            if lay2 != lay or not pcbnew.SHAPE.Collide(shape, s2, pcbnew.FromMM(clr) - 1):
                continue
            g = r8.min_gap(shape, s2, clr + 1)
            g = 0.0 if g is None else g
            where = f'{net} {label} to {n2} {l2} on {ctx.board.GetLayerName(lay)}'
            if worst is None or g < worst[0]:
                worst = (g, where)
            issues.append(f'S-6: {where}: {g:.3f} mm' + (' (shared copper)' if g == 0 else f' < {clr} mm'))
    ev['closest_violation'] = worst
    return sorted(set(issues)), ev


def s7(ctx):
    """Five contacts carry only servo signals and their common reference; no motor-power contact."""
    issues, ev = [], {}
    f = ctx.fps.get('J122')
    if f is None:
        return ['S-7: J122 missing'], ev
    pads = {p.GetNumber(): p for p in f.Pads() if p.GetNumber()}
    ev['pads'] = {k: p.GetNetname() for k, p in sorted(pads.items())}
    for i, net in enumerate(SERVO_TERMINAL, 1):
        num = str(i)
        if num not in pads or pads[num].GetNetname() != net:
            issues.append(f'S-7: J122.{num} must be {net} (is {ev["pads"].get(num)})')
    if sorted(p.GetNumber() for p in f.Pads()) != ['1', '2', '3', '4', '5']:
        issues.append('S-7: J122 must have exactly five contacts; no servo-power or obsolete header row')
    return sorted(set(issues)), ev


# D-R21-07 (R21-GATE-04): each port's ESD clamp sits on its wire net beside the terminal pin, ahead of the 1 k series
# resistor (D-R20-09 moved D440 / D441 to J440's pins; round 19 had D440 6.2 mm of track away): (terminal, pin, clamp
# pad, series resistor). The bound is the net's track-graph length from pin centre to clamp pad centre with the resistor's
# pads removed. Measured on the round 21 board (centre to centre): J410 4.288 / 4.388, J420 3.975 / 3.975, J440 4.075 /
# 4.175 (3.157 / 3.194 pad edge to pad edge), J9 3.975 / 3.975 mm.
PORT_CLAMPS = (('J410', '3', 'D410.1', 'R441'), ('J410', '4', 'D411.1', 'R440'),
               ('J420', '3', 'D420.1', 'R451'), ('J420', '4', 'D421.1', 'R450'),
               ('J440', '3', 'D440.1', 'R471'), ('J440', '4', 'D441.1', 'R470'),
               ('J9', '3', 'D401.1', 'R100'), ('J9', '4', 'D400.1', 'R101'),
               # D-R24-11: J400.2's contact clamp, on the screw side of R165 (470 k) as the port clamps sit on the wire side
               # of their 1 k resistors; measured on the round 24 board 4.114 mm (pin to clamp) / 0.7 mm (clamp to via).
               ('J400', '2', 'D402.1', 'R165'))
CLAMP_PATH_MAX = 4.5           # mm, pin centre to clamp pad centre along the track graph


def port_clamps(board, clamps=PORT_CLAMPS, bound=CLAMP_PATH_MAX):
    """(issues, {terminal pin: (clamp, mm)}): every clamp reached from its terminal pin along tracks and vias of the
    pin's net within `bound` mm, without passing through its series resistor's pads."""
    issues, ev = [], {}
    for ref, num, clamp, resistor in clamps:
        f = board.FindFootprintByReference(ref)
        pad = f.FindPadByNumber(num) if f else None
        if pad is None:
            issues.append(f'{ref}.{num} is missing')
            continue
        net = pad.GetNetname()
        lengths = {}
        _, _, edges = track_graph(board, net, lengths=lengths)
        adj = {}
        for key, (a, c, _) in edges.items():
            adj.setdefault(a, []).append((c, lengths[key]))
            adj.setdefault(c, []).append((a, lengths[key]))
        src, dst = f'P{ref}.{num}', f'P{clamp}'
        dist, todo, n = {src: 0.0}, [(0.0, 0, src)], 0          # (length, push count, node): nodes never compared
        while todo:
            d, _, u = heapq.heappop(todo)
            if u == dst or d > dist.get(u, math.inf):
                continue
            for v, w in adj.get(u, ()):
                if isinstance(v, str) and v.startswith(f'P{resistor}.'):
                    continue
                if d + w < dist.get(v, math.inf):
                    dist[v] = d + w
                    n += 1
                    heapq.heappush(todo, (d + w, n, v))
        got = dist.get(dst)
        ev[f'{ref}.{num}'] = (clamp, None if got is None else round(got, 3))
        if got is None:
            issues.append(f'{ref}.{num} ({net}): its clamp {clamp} is reached only through {resistor} or not at all '
                          '(the clamp must sit on the wire side of the series resistor)')
        elif got > bound + 1e-6:
            issues.append(f'{ref}.{num} ({net}): its clamp {clamp} is {got:.3f} mm of track from the pin, over '
                          f'{bound} mm (R21-GATE-04)')
    return issues, ev


# D-R22-07 (R22-GATE-03): the clamp's other half of the loop. Each clamp's GND pad reaches a GND via or GND plated pad
# through tracks (pour copper not counted) within CLAMP_GND_MAX mm, pad centre to via centre. Measured on 5516eeec:
# D410 / D411 / D420 / D421 / D440 / D441 0.7 mm, D400 / D401 0.8 mm.
CLAMP_GND_MAX = 1.0            # mm


def clamp_returns(board, clamps=PORT_CLAMPS, bound=CLAMP_GND_MAX):
    """(issues, {clamp GND pad: (mm, via or pad)}): each port clamp's GND pad to the nearest GND via or GND plated pad
    along GND tracks only."""
    import pcbnew
    lengths = {}
    pads, vias, edges = track_graph(board, 'GND', lengths=lengths)
    adj = {}
    for key, (a, c, _) in edges.items():
        adj.setdefault(a, []).append((c, lengths[key]))
        adj.setdefault(c, []).append((a, lengths[key]))
    plated = {'P' + lab for lab, _, _, p in pads if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH}
    where = {'V' + v.m_Uuid.AsString(): f'via GND ({pcbnew.ToMM(v.GetPosition().x):.3f}, '
                                         f'{pcbnew.ToMM(v.GetPosition().y):.3f})' for v in vias}
    issues, ev = [], {}
    for clamp in sorted({c[2].split('.')[0] for c in clamps}):
        f = board.FindFootprintByReference(clamp)
        gnd = [p for p in (f.Pads() if f else []) if p.GetNetname() == 'GND']
        if not gnd:
            issues.append(f'{clamp} has no GND pad')
            continue
        src = f'P{clamp}.{gnd[0].GetNumber()}'
        dist, todo, n, hit = {src: 0.0}, [(0.0, 0, src)], 0, None
        while todo:
            d, _, u = heapq.heappop(todo)
            if d > dist.get(u, math.inf):
                continue
            if u != src and isinstance(u, str) and (u.startswith('V') or u in plated):
                hit = (d, where.get(u, u[1:]))
                break
            for v, w in adj.get(u, ()):
                if d + w < dist.get(v, math.inf):
                    dist[v] = d + w
                    n += 1
                    heapq.heappush(todo, (d + w, n, v))
        ev[src[1:]] = None if hit is None else (round(hit[0], 3), hit[1])
        if hit is None:
            issues.append(f'{src[1:]} (the {clamp} clamp\'s GND) reaches no GND via through tracks, only through the pour '
                          '(R22-GATE-03)')
        elif hit[0] > bound + 1e-6:
            issues.append(f'{src[1:]} (the {clamp} clamp\'s GND) is {hit[0]:.3f} mm of track from {hit[1]}, over {bound} '
                          'mm (R22-GATE-03)')
    return issues, ev


def k_ports(ctx):
    issues, ev = port_clamps(ctx.board)
    returns, gnd = clamp_returns(ctx.board)                            # D-R22-07
    return ([f'K-ports: {i}' for i in issues + returns],
            dict(clamp_path_mm=ev, bound_mm=CLAMP_PATH_MAX, clamp_gnd_mm=gnd, gnd_bound_mm=CLAMP_GND_MAX))


# ======================================================================================================================
# mechanical and placement
# ======================================================================================================================
def lc1(board):
    """R10 permits equal or stronger local clearances; probe/debug floors remain stricter than board default."""
    import pcbnew
    issues, overrides = [], []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        floor = .508 if ref == 'J2' else 1. if ref.startswith('TP') else .15
        for label, item in [(ref, fp)] + [(f'{ref}.{p.GetNumber()}', p) for p in fp.Pads()]:
            value = item.GetLocalClearance()
            if value is None:
                continue
            value = pcbnew.ToMM(value)
            overrides.append(dict(item=label, clearance_mm=value, floor_mm=floor))
            if value < floor - 1e-9:
                issues.append(f'LC-1: {label} local clearance {value:g} mm is below its applicable {floor:g} mm floor')
    return issues, dict(overrides=overrides)


def k_inner_signal(ctx):
    """R10 only: GND may be drawn on In1; foreign copper there and non-power In2 routing remain prohibited."""
    import pcbnew
    import route_check as rc
    issues, length = [], {}
    for track in ctx.board.GetTracks():
        if track.GetClass() == 'PCB_VIA':
            continue
        layer, net = track.GetLayer(), track.GetNetname()
        bad = (layer == pcbnew.In1_Cu and net != 'GND') or (layer == pcbnew.In2_Cu and rc.net_class(net) != 'power')
        if bad:
            name = ctx.board.GetLayerName(layer)
            length[name] = length.get(name, 0.) + pcbnew.ToMM(track.GetLength())
            issues.append(f'{name} track of {net}: In1 carries GND only; In2 power and GND only')
    # R12-GATE-02: drawings/text and filled board/footprint zones are manufactured
    # copper too. Pads and vias legitimately traverse inner layers; the existing
    # track walk above already handles every routed segment/arc.
    routed = {item.m_Uuid.AsString() for item in ctx.board.GetTracks()}
    extra = 0
    for key, layer, shape, box, pad, net, label in copper_nodes(ctx.board):
        if pad is not None or key in routed or layer not in (pcbnew.In1_Cu, pcbnew.In2_Cu):
            continue
        extra += 1
        bad = (layer == pcbnew.In1_Cu and net != 'GND') or (layer == pcbnew.In2_Cu and rc.net_class(net) != 'power')
        if bad:
            issues.append(f'{ctx.board.GetLayerName(layer)} {label} of {net or "(no net)"}: '
                          'In1 carries GND only; In2 power and GND only')
    return issues, dict(length_mm=length, other_inner_copper_items=extra)


def m1(ctx):
    import pcbnew
    issues = []
    x0, y0, x1, y1 = ctx.outline
    width, length = x1 - x0, y1 - y0
    ev = dict(outline_mm=ctx.outline, width_mm=round(width, 3), length_mm=round(length, 3))
    if abs(width - BOARD_WIDTH) > 0.01:
        issues.append(f'M-1: board width {width:g} mm; P1 requires {BOARD_WIDTH:g} mm')
    if length > BOARD_MAX + 0.01:
        issues.append(f'M-1: board length {length:g} mm exceeds the P1 {BOARD_MAX:g} mm maximum')
    edges = [d for d in ctx.board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts
             and d.GetShape() != pcbnew.SHAPE_T_CIRCLE]
    mm = pcbnew.ToMM
    rect = (len(edges) == 1 and edges[0].GetShape() == pcbnew.SHAPE_T_RECT) or \
        (len(edges) == 4 and all(d.GetShape() == pcbnew.SHAPE_T_SEGMENT for d in edges) and
         all(abs(mm(d.GetStart().x) - mm(d.GetEnd().x)) < 1e-4 or abs(mm(d.GetStart().y) - mm(d.GetEnd().y)) < 1e-4
             for d in edges))
    if not rect or abs(x0) > 0.005 or abs(y0) > 0.005:
        issues.append(f'M-1: outline must be one rectangle from (0, 0) (found {len(edges)} edges from ({x0:g}, {y0:g}))')
    for d in ctx.board.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE and \
                abs(mm(d.GetRadius()) - 1.6) > 0.01:
            issues.append(f'M-1: Edge.Cuts circle at ({mm(d.GetCenter().x):g}, {mm(d.GetCenter().y):g}) is not a 3.2 mm hole')
    return issues, ev


# R18-GATE-07: the five sled-hole centres of REQUIREMENTS P1 / P2 and the parent docs/VEHICLE.md (board mm, origin at
# the top-left corner); fit_check only bounds the supports by region, so the positions are pinned here.
SUPPORTS_R10 = ((4.0, 4.0), (42.0, 4.0), (4.0, 44.3), (3.7, 86.0), (42.0, 86.0))
SUPPORT_TOL = 0.01              # mm


def m3(ctx, supports=SUPPORTS_R10, tol=SUPPORT_TOL):
    import pcbnew
    mm = pcbnew.ToMM
    holes = [(mm(d.GetCenter().x), mm(d.GetCenter().y)) for d in ctx.board.GetDrawings()
             if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE]
    issues = [] if len(holes) == 5 else ['M-3: exactly five M3 supports required; remove obsolete servo plug tie holes']
    for want in supports:
        near = [h for h in holes if math.dist(h, want) <= tol]
        if len(near) != 1:
            closest = min(holes, key=lambda h: math.dist(h, want), default=None)
            issues.append(f'M-3: the P1 / P2 support ({want[0]:g}, {want[1]:g}) needs one Edge.Cuts circle centred '
                          f'within {tol} mm (found {len(near)}; nearest '
                          + ('none' if closest is None else f'({closest[0]:.3f}, {closest[1]:.3f}), '
                             f'{math.dist(closest, want):.3f} mm away') + ')')
    issues += [f'M-3: Edge.Cuts circle at ({h[0]:.3f}, {h[1]:.3f}) is not a P1 / P2 support position' for h in holes
               if not any(math.dist(h, want) <= tol for want in supports)]
    return issues, {'support_circles': len(holes), 'servo_plug_tie_holes_required': False,
                    'centres_mm': sorted((round(x, 4), round(y, 4)) for x, y in holes),
                    'pinned_mm': [list(c) for c in supports], 'tolerance_mm': tol}


def m2(ctx, board_sha=None):
    """Optional plate diagnostics: no frequency floor or release condition (requirements audit 2, item 6)."""
    return [], dict(optional=True, report=ctx.plate, board_sha256=board_sha,
                    physical_vibration_qualification=False)


def m5(ctx, board_sha=None):
    rep = ctx.fit()
    issues = [f'M-5: fit_check: {i}' for i in rep.get('issues', [])]
    if rep.get('profile') != 'r10':
        issues.append(f'M-5: fit report profile {rep.get("profile")!r}; R10 needs fit_check --profile r10')
    if ctx.fit_given and board_sha and rep.get('board_sha256') != board_sha:
        issues.append('M-5: the fit report is not bound to this board (board_sha256)')
    ns, nt = rep.get('nearest_support'), rep.get('nearest_top_support')
    return issues, dict(width_mm=rep.get('width_mm'), length_mm=rep.get('length_mm'), supports=rep.get('supports'),
                        nearest_support=ns, nearest_top_support=nt)


def m6(ctx):
    import pcbnew
    import check_r8 as r8
    MM = pcbnew.FromMM
    issues = []
    supports = ctx.fit().get('supports', [])
    tht = [(f.GetReference(), p.GetPosition(), max(p.GetSize().x, p.GetSize().y) // 2)
           for f in ctx.board.GetFootprints() for p in f.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    for f in ctx.board.GetFootprints():
        if not f.IsFlipped():
            continue
        ref = f.GetReference()
        if any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in f.Pads()):
            issues.append(f'M-6: bottom part {ref} has through-hole pads (bottom parts SMD only)')
        cy = r8.courtyard(f)
        for other, c, r in tht:
            if other == ref:
                continue
            d = r8.min_gap(cy, pcbnew.SHAPE_CIRCLE(c, r), BOT_THT + 1)
            if d is not None and d < BOT_THT - EPS:
                issues.append(f'M-6: bottom part {ref} is {d:.2f} mm from {other}\'s through-hole pad (minimum {BOT_THT})')
                break
        for c in supports:
            d = r8.min_gap(cy, pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])), 1), BOT_M3 + 1)
            if d is not None and d < BOT_M3 - EPS:
                issues.append(f'M-6: bottom part {ref} is {d:.2f} mm from the M3 centre {tuple(c)} (minimum {BOT_M3})')
    return sorted(set(issues)), dict(supports=supports)


def pcbnew_mm(v):
    import pcbnew
    return pcbnew.ToMM(v)


# D-R24-20 (R24-TRI-15): JLC's assembly terms section 2.3 require 2.5 mm from a component body to the board edge
# (ORDERING 8.1). JLC adds rails on the two long edges only, so the rail-less short edges (y = 0 aft, y = 90 forward)
# keep that distance from every footprint's courtyard (a body never reaches past its courtyard), except the recorded DFM
# queries D-R24-15 kept, each at its measured courtyard distance (round 24, board 1407e850). A part nearer than 2.5 mm
# that is not listed, a listed part now nearer than recorded (grown) or at another distance (re-record), a listed part
# now clear (stale) and a listed part not on the board (missing) each fail.
SHORT_EDGE_MIN = 2.5            # mm, courtyard to the y = 0 / y = 90 board edge
SHORT_EDGE_TOL = 0.005          # mm
SHORT_EDGE_QUERIES = {          # ref: (edge, courtyard distance mm, why the part stays)
    'R400': ('aft', 1.025, "U400's feedback divider row under the buck loop"),
    'R401': ('aft', 1.025, "U400's feedback divider row under the buck loop"),
    'R404': ('aft', 1.025, "U400's feedback divider row under the buck loop"),
    'C403': ('aft', 1.955, "U400's input capacitor in the buck loop"),
    'C95': ('forward', 1.505, 'the hot-plug feed: C89 sits 1.0 mm aft of it'),
    'R166': ('forward', 1.755, "the hot-plug damper's 2512 on the BAT_DAMP run"),
}


def m8(ctx, queries=None, minimum=SHORT_EDGE_MIN, tol=SHORT_EDGE_TOL):
    """(issues, evidence): every footprint courtyard >= `minimum` from the rail-less short edges, but the recorded
    SHORT_EDGE_QUERIES at their measured distances."""
    import pcbnew
    import check_r8 as r8
    queries = SHORT_EDGE_QUERIES if queries is None else queries
    mm = pcbnew.ToMM
    _, y0, _, y1 = ctx.outline
    issues, near, seen = [], {}, set()
    for f in ctx.board.GetFootprints():
        ref = f.GetReference()
        bb = r8.courtyard(f).BBox()
        aft, fwd = mm(bb.GetTop()) - y0, y1 - mm(bb.GetBottom())
        edge, d = ('aft', aft) if aft <= fwd else ('forward', fwd)
        d = round(d, 3)
        q = queries.get(ref)
        seen.add(ref)
        if d >= minimum - EPS:
            if q is not None:
                issues.append(f'M-8: stale SHORT_EDGE_QUERIES entry {ref}: its courtyard is now {d:.3f} mm from the '
                              f'{edge} short edge (at least {minimum} mm)')
            continue
        near[ref] = [edge, d]
        if q is None:
            issues.append(f'M-8: {ref} courtyard is {d:.3f} mm from the {edge} short edge, under {minimum} mm (JLC '
                          'assembly terms section 2.3, ORDERING 8.1) and not a recorded DFM query (SHORT_EDGE_QUERIES)')
        elif q[0] != edge or d < q[1] - tol:
            issues.append(f'M-8: {ref} courtyard is {d:.3f} mm from the {edge} short edge, nearer than the recorded '
                          f'{q[1]} mm ({q[0]})')
        elif d > q[1] + tol:
            issues.append(f'M-8: SHORT_EDGE_QUERIES {ref} records {q[1]} mm, the board gives {d:.3f} mm (re-record it)')
    issues += [f'M-8: SHORT_EDGE_QUERIES entry {ref}: no such part on the board' for ref in sorted(queries)
               if ref not in seen]
    return issues, dict(minimum_mm=minimum, edges_mm=[round(y0, 3), round(y1, 3)], near=near,
                        queries={k: list(v[:2]) for k, v in queries.items()})


def m7(ctx):
    """check_r9.m7 (U4 bottom, rotation, lever arm, no via or fill under U4 / U5) at R10's recorded rotation, with the
    axis map read from the board."""
    import check_r9 as r9
    with patched(r9, IMU_ROTATION={**r9.IMU_ROTATION, ctx.board.GetTitleBlock().GetRevision(): IMU_ROTATION_R10}):
        with patched(r9, IMU_LEVER=math.inf):
            issues, ev = r9.m7(ctx)
    u4 = ctx.fps.get('U4')
    if u4 is not None:
        c = u4.GetPosition()
        lever = pcbnew_mm(c.x) - 23.0
        pad1 = u4.FindPadByNumber('1')
        offset = (pcbnew_mm(pad1.GetPosition().x - c.x), pcbnew_mm(pad1.GetPosition().y - c.y)) if pad1 else None
        ev['imu_lever_arm_signed_mm'] = round(lever, 3)
        ev['imu_pad1_offset_mm'] = None if offset is None else [round(v, 3) for v in offset]
        if abs(lever - IMU_LEVER_R10) > 0.05:
            issues.append(f'M-7: U4 centre x offset from the roll axis (x 23) is {lever:.3f} mm, recorded '
                          f'{IMU_LEVER_R10} mm (M3_R10 "IMU axis map")')
        if offset is None or any(abs(a - b) > 0.05 for a, b in zip(offset, IMU_PAD1_R10)):
            issues.append(f'M-7: U4 pad 1 is at {offset} mm from the centre, recorded {IMU_PAD1_R10} (a mirrored or '
                          'rotated footprint would change the axis map)')
        rot = round(u4.GetOrientationDegrees() % 360.0, 3)
        ev['board_axis_map'] = dict(side='bottom' if u4.IsFlipped() else 'top', rotation=rot,
                                    map=IMU_MAPS.get(rot, 'no recorded map'))
    return issues, ev


def entry_dir(f):
    """Board direction of a terminal's wire entry: the footprint description's "wire entry +y" (the R10 DB125
    lands), else DB128's local -y (check_r9.entry_dir)."""
    m = re.search(r'wire entry ([+-])([xy])', f.GetLibDescription() or '')
    sign, axis = (m[1], m[2]) if m else ('-', 'y')
    lx, ly = (1.0 if sign == '+' else -1.0, 0.0) if axis == 'x' else (0.0, 1.0 if sign == '+' else -1.0)
    th = math.radians(f.GetOrientationDegrees())
    c, s = math.cos(th), math.sin(th)
    dx, dy = lx * c + ly * s, -lx * s + ly * c
    if abs(dx) > abs(dy):
        return '+x' if dx > 0 else '-x'
    return '+y' if dy > 0 else '-y'


def p11(ctx):
    import check_r9 as r9
    issues, ev = [], {}
    for ref, want in WIRE_ENTRY.items():
        f = ctx.fps.get(ref)
        if f is None:
            issues.append(f'P-11: {ref} missing')
            continue
        d = entry_dir(f)
        ev[ref] = dict(entry=d)
        if d != want:
            issues.append(f'P-11: {ref} wires enter from {d}; R10 sets {want} (r10_plan section 2 item 2)')
        try:
            face, box = r9.entry_face(ctx, f, d)
        except ValueError as error:
            issues.append(f'P-11: {error}')
            continue
        if d in ('-x', '+x'):
            room = r9.wire_room(face)
            ev[ref].update(wire_room_mm=round(room, 3), r8_floor_mm=WIRE_ROOM, r10_accepted_floor_mm=WIRE_ROOM_R10,
                           owner_decision='OQ-1 wire-room floor accepted 2026-10-28; current P2: 20–22 AWG, insulation OD <= 1.8 mm (24 AWG igniter exception); narrowed-gauge owner acceptance pending (R10_VALIDATION row 31); physical bend fit unverified')
            if room < WIRE_ROOM_R10 - EPS:
                issues.append(f'P-11: {ref} has {room:.2f} mm of wire room to the bore wall (owner-accepted R10 '
                              f'floor {WIRE_ROOM_R10}; R8 {WIRE_ROOM})')
        else:
            issues += [f'P-11: {i}' for i in r9.axial_ok(ctx, f, d, face, box)]
    return issues, ev


def f9(ctx):
    """OQ-2: board-derived, reproducible reverse hot-plug evidence; never substitute a distance for a model pass."""
    import r10_hotplug as hp
    inputs = json.loads(hp.INPUTS.read_text())
    result = json.loads(hp.RESULTS.read_text())
    live = hp.extract(ctx.board, ctx.board_path)
    issues = []
    if hp.digest(live) != hp.digest(inputs):
        changed = [ref for ref in sorted(set(live['parts']) | set(inputs.get('parts', {})))
                   if hp.digest(live['parts'].get(ref)) != hp.digest(inputs.get('parts', {}).get(ref))]
        issues.append('F9-1: stale board-derived model inputs' + (': ' + ', '.join(changed) if changed else ''))
    issues += ['F9-1: ' + i for i in hp.validate(inputs, result, live['electrical_sha256'])]
    return issues, dict(board_sha256=live['board_sha256'], electrical_sha256=live['electrical_sha256'],
                        model_sha256=result.get('model_sha256'), qualification=result.get('qualification'),
                        limits=result.get('limits'), convergence=result.get('convergence'),
                        inference=result.get('inference'), owner_decision='OQ-2, 2026-10-28')


def local_ground_return(board, start, end, limit=14.0, step=.05, details=False):
    """GAP-2: shortest local saved-copper path, including real GND plane detours, on a 0.05mm grid.
    Layer changes occur only at GND vias/PTH copper, charged a full board thickness conservatively.
    This geometric model is not an inductance or electrical qualification."""
    import pcbnew
    import route_check as rc
    if start.GetNetname() != 'GND' or end.GetNetname() != 'GND':
        return None
    pts = [p.GetPosition() for p in (start, end)]
    grow = pcbnew.FromMM(2.)
    window = (min(p.x for p in pts) - grow, min(p.y for p in pts) - grow,
              max(p.x for p in pts) + grow, max(p.y for p in pts) + grow)
    raster = rc.Raster(window, pcbnew.FromMM(step))
    layers = [pcbnew.B_Cu, pcbnew.In1_Cu]  # GAP-2 reviewed local return: component side and uninterrupted In1 GND.
    copper, stitches, ends = [], [], []
    queue, best, came = [], {}, {}
    for i, layer in enumerate(layers):
        cop, stitch = rc.net_copper(board, 'GND', layer)
        copper.append(raster.fill(cop)); stitches.append(raster.fill(stitch))
        ends.append(raster.fill([rc._poly(end, layer)]) if end.IsOnLayer(layer) else bytearray(raster.nx * raster.ny))
        if start.IsOnLayer(layer):
            source = raster.fill([rc._poly(start, layer)])
            for k, on in enumerate(source):
                if on and copper[i][k]:
                    best[i, k] = 0.; came[i, k] = None; queue.append((0., i, k))
    heapq.heapify(queue)
    vertical = pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness())
    moves = [(dx, dy, step * math.hypot(dx, dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
    while queue:
        distance, layer, k = heapq.heappop(queue)
        if distance != best.get((layer, k)):
            continue
        if ends[layer][k]:
            if not details:
                return distance
            states, state = [], (layer, k)
            while state is not None:
                states.append(state); state = came[state]
            states.reverse()
            path = []
            for i, (lay, cell) in enumerate(states):
                if 0 < i < len(states) - 1:
                    before, after = states[i - 1], states[i + 1]
                    if before[0] == lay == after[0] and cell - before[1] == after[1] - cell:
                        continue
                x, y = raster.centre(cell)
                path.append([board.GetLayerName(layers[lay]), round(pcbnew.ToMM(x), 3), round(pcbnew.ToMM(y), 3)])
            return dict(distance_mm=distance, path_mm=path, layers=sorted({p[0] for p in path}),
                        endpoints=[f'{p.GetParentFootprint().GetReference()}.{p.GetNumber()}' for p in (start, end)])
        x, y = k % raster.nx, k // raster.nx
        adjacent = []
        for dx, dy, cost in moves:
            a, b = x + dx, y + dy
            if 0 <= a < raster.nx and 0 <= b < raster.ny:
                q = b * raster.nx + a
                if copper[layer][q] and (not dx or not dy or
                    (copper[layer][y * raster.nx + a] and copper[layer][b * raster.nx + x])):
                    adjacent.append((layer, q, cost))
        if stitches[layer][k]:
            adjacent += [(other, k, vertical) for other in range(len(layers)) if other != layer
                         and stitches[other][k] and copper[other][k]]
        for other, q, cost in adjacent:
            total = distance + cost
            if total <= limit and total < best.get((other, q), float('inf')):
                best[other, q] = total; came[other, q] = (layer, k); heapq.heappush(queue, (total, other, q))
    return None


def output_path(board, start, end):
    """GAP-2: shortest endpoint-linked B.Cu OUT track path; no vias, fills or remote-plane shortcut."""
    import pcbnew
    graph, positions = {}, {}
    for t in board.GetTracks():
        if t.GetClass() != 'PCB_TRACK' or t.GetLayer() != pcbnew.B_Cu or t.GetNetname() != start.GetNetname():
            continue
        a, b = [(p.x, p.y) for p in (t.GetStart(), t.GetEnd())]
        graph.setdefault(a, []).append((b, pcbnew.ToMM(t.GetLength())))
        graph.setdefault(b, []).append((a, pcbnew.ToMM(t.GetLength())))
        positions[a], positions[b] = t.GetStart(), t.GetEnd()
    starts = [p for p in positions if start.IsOnLayer(pcbnew.B_Cu) and start.HitTest(positions[p])]
    ends = {p for p in positions if end.IsOnLayer(pcbnew.B_Cu) and end.HitTest(positions[p])}
    queue, best, came = [(0., p) for p in starts], {p: 0. for p in starts}, {p: None for p in starts}
    heapq.heapify(queue)
    while queue:
        distance, p = heapq.heappop(queue)
        if distance != best.get(p):
            continue
        if p in ends:
            path, q = [], p
            while q is not None:
                path.append([pcbnew.ToMM(q[0]), pcbnew.ToMM(q[1])]); q = came[q]
            return dict(distance_mm=distance, path_mm=list(reversed(path)))
        for q, cost in graph[p]:
            total = distance + cost
            if total < best.get(q, float('inf')):
                best[q], came[q] = total, p; heapq.heappush(queue, (total, q))
    return None


def output_loop(ctx, bounds=None):
    """GAP-2: C82 and D9 protect U9 OUT through short actual OUT and local GND copper paths.
    Engineering regression bounds, not datasheet numeric limits or a bench qualification."""
    import check_r7 as r7
    import pcbnew
    pads = r7.pads_by_ref(ctx.board)
    out, ground = pads.get(('U9', '6')), pads.get(('U9', '8'))
    # GAP-2 reviewed cell: OUT / saved GND / total measured 3.391 / 9.178 / 12.569 mm (C82),
    # 6.873 / 9.818 / 16.692 mm (D9). These regression bounds preserve short local paths; TI gives no numeric limit.
    bounds = bounds or {'C82': (4., 10., 13.5), 'D9': (7., 10.5, 17.)}
    issues, ev = [], dict(bounds_mm=bounds, out_detour_ratio_max=1.25, ground_grid_mm=.05,
                          basis='GAP-2 engineering local-copper bounds; physical qualification pending',
                          area_method='projected OUT/GND paths joined through component pad centres; 0.05mm GND raster, not inductance')
    if out is None or ground is None or out.GetNetname() != 'RAW_PROTECTED' or ground.GetNetname() != 'GND':
        return ['GAP-2: U9 OUT.6 / GND.8 missing or miswired'], ev
    for ref in ('C82', 'D9'):
        power, ret = pads.get((ref, '1')), pads.get((ref, '2'))
        if power is None or ret is None or power.GetNetname() != 'RAW_PROTECTED' or ret.GetNetname() != 'GND':
            issues.append(f'GAP-2: {ref} must connect U9 OUT (pad1) to GND (pad2)'); continue
        f = ctx.fps[ref]
        if ref == 'C82' and (parse_value(f.GetValue(), 'C') or 0) < 1e-6:
            issues.append('GAP-2: C82 must provide at least 1uF on U9 OUT')
        if ref == 'D9' and f.GetValue() != 'B340A-13-F':
            issues.append('GAP-2: D9 must be the qualified B340A-13-F Schottky')
        if not all(p.IsOnLayer(pcbnew.B_Cu) for p in (out, power, ret, ground)):
            issues.append(f'GAP-2: {ref} requires the reviewed local B.Cu output protection cell')
        out_limit, return_limit, loop_limit = bounds[ref]
        out_path = output_path(ctx.board, out, power)
        outgoing = out_path['distance_mm'] if out_path else None
        ground_path = local_ground_return(ctx.board, ret, ground, return_limit, details=True)
        returning = ground_path['distance_mm'] if ground_path else None
        loop = None if outgoing is None or returning is None else outgoing + returning
        xy = lambda p: (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
        a, b = xy(out), xy(power)
        dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
        shortest = max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)
        detour = outgoing / shortest if outgoing is not None and shortest else None
        polygon = ([xy(out)] + out_path['path_mm'] + [xy(power), xy(ret)]
                   + [p[1:] for p in ground_path['path_mm']] + [xy(ground)]) if loop is not None else []
        area = abs(sum(a[0] * b[1] - a[1] * b[0] for a, b in zip(polygon, polygon[1:] + polygon[:1]))) / 2
        ev[ref] = dict(out_route_mm=outgoing, out_endpoints=['U9.6', ref + '.1'], out_layer='B.Cu',
                       out_path=out_path, out_octilinear_mm=shortest, out_detour_ratio=detour,
                       local_ground_route_mm=returning, ground_path=ground_path, loop_mm=loop,
                       projected_loop_area_mm2=area if polygon else None)
        if outgoing is None or outgoing > out_limit or detour is None or detour > ev['out_detour_ratio_max'] \
                or returning is None or loop > loop_limit:
            issues.append(f'GAP-2: {ref} needs short actual OUT / GND loop (OUT {outgoing}, return {returning}, loop {loop})')
    return issues, ev


def t1(ctx):
    """T-1 for R10 (D-R2-13): the west edge holds each end third; on the east side each end third is held by an
    east-edge tab or by a tab on that end's short edge within its east third. Clearances as tools/tab_windows.py."""
    import pcbnew
    import tab_windows as tw
    from fit_check import board_geometry
    b = ctx.board
    _, (x0, y0, x1, y1) = board_geometry(b)
    obs = tw.obstacles(b)
    holes = [((pcbnew.ToMM(d.GetCenter().x), pcbnew.ToMM(d.GetCenter().y)), pcbnew.ToMM(d.GetRadius()))
             for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE]

    def spans(edge):
        horiz = edge in ('aft', 'forward')
        e = {'west': x0, 'east': x1, 'aft': y0, 'forward': y1}[edge]
        lo, hi = (x0, x1) if horiz else (y0, y1)
        ok, a = [], lo + 0.5
        while a + tw.TAB_LEN <= hi - 0.5 + 1e-9:
            z = a + tw.TAB_LEN

            def gap(bb):
                along = max(bb[0] - z, a - bb[2], 0) if horiz else max(bb[1] - z, a - bb[3], 0)
                across = max(bb[1] - e, e - bb[3], 0) if horiz else max(bb[0] - e, e - bb[2], 0)
                return math.hypot(along, across)
            good = all(gap(bb) >= need - 1e-6 for _, bb, need in obs) and \
                all(gap((c[0] - r, c[1] - r, c[0] + r, c[1] + r)) >= tw.TAB_HOLE - 1e-6 for c, r in holes)
            if good:
                ok.append(round(a, 2))
            a = round(a + tw.STEP, 2)
        out = []
        for s in ok:
            if out and s - out[-1][1] <= tw.STEP + 0.01:
                out[-1][1] = s
            else:
                out.append([s, s])
        return [(p, round(q + tw.TAB_LEN, 2)) for p, q in out]
    wins = {e: spans(e) for e in ('west', 'east', 'aft', 'forward')}
    third_y, third_x = (y1 - y0) * tw.END_SHARE, (x1 - x0) * tw.END_SHARE
    aft = lambda ss: any(s[0] <= y0 + third_y - tw.TAB_LEN + 1e-6 for s in ss)           # noqa: E731
    fwd = lambda ss: any(s[1] >= y1 - third_y + tw.TAB_LEN - 1e-6 for s in ss)           # noqa: E731
    east_third = lambda ss: any(s[1] >= x1 - third_x + tw.TAB_LEN - 1e-6 for s in ss)    # noqa: E731
    issues = []
    if not aft(wins['west']):
        issues.append('T-1: no legal 5 mm tab on the west edge within the aft third')
    if not fwd(wins['west']):
        issues.append('T-1: no legal 5 mm tab on the west edge within the forward third')
    if not (aft(wins['east']) or east_third(wins['aft'])):
        issues.append('T-1: the east side of the aft third has no legal tab (east edge or aft edge east third)')
    if not (fwd(wins['east']) or east_third(wins['forward'])):
        issues.append('T-1: the east side of the forward third has no legal tab (east edge or forward edge east third)')
    return issues, dict(windows=wins, rule='R10_DECISIONS D-R2-13')


# ======================================================================================================================
# K-rules
# ======================================================================================================================
def k_contract(ctx):
    if ctx.text is None:
        return ['K-contract: no board file text (pass the saved board path)'], {}
    return contract(ctx.text), {}


def k_binding(ctx):
    """Check the saved evidence without regenerating or approving a firmware binding."""
    import r10_sch_check as sch
    if ctx.board_path is None or not Path(ctx.board_path).is_file():
        return ['K-binding: saved board path required for native binding-note validation'], {}
    board = Path(ctx.board_path)
    path = board.parent / R10_BINDING_NOTE
    try:
        saved = json.loads(path.read_text())
    except (OSError, UnicodeError, ValueError) as error:
        return [f'K-binding: saved binding note is missing or malformed: {error}'], {}
    if not isinstance(saved, dict):
        return ['K-binding: saved binding note must be a JSON object'], {}
    expected = sch.binding_note(board.parent, board)
    evidence = dict(note_sha256=file_sha(path), board_sha256=expected['board_sha256'],
                    status=expected['status'], u1_board_map_checked=expected['u1_board_map_checked'])
    issues = []
    for key in sorted(saved.keys() | expected.keys()):
        if key not in saved or key not in expected or (
                json.dumps(saved[key], sort_keys=True, allow_nan=False) !=
                json.dumps(expected[key], sort_keys=True, allow_nan=False)):
            issues.append(f'K-binding: saved {key} differs from native binding-note regeneration')
    return issues, evidence


def k_actuators(ctx):
    path = ROOT / 'm3_design/check_actuators.py'
    sha = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    if ctx.text is None:
        return ['K-actuators: no board file text (pass the saved board path)'], dict(sha256=sha)
    return [f'check_actuators: {i}' for i in actuators.check(ctx.text, ctx.dru, profile='r10')], dict(sha256=sha)


R10_PIN_TABLE = ROOT / 'm3_design/assembly_review/sources/r10_design/pin_table.tsv'


def mcu_pin_table(path=R10_PIN_TABLE):
    """The reviewed R10 table is the only complete MCU pin-map authority; it is never inferred from this board."""
    with Path(path).open() as table:
        rows = list(csv.DictReader(table, delimiter='\t'))
    if {row['pin'] for row in rows} != {str(i) for i in range(1, 101)} or len(rows) != 100:
        raise ValueError('R10 pin table must list every LQFP100 pin exactly once')
    if any(not row.get('r10_net') for row in rows):
        raise ValueError('R10 pin table has an empty r10_net; unused pins must say NC')
    return {row['pin']: row['r10_net'] for row in rows}


def loader_pins(board, port_pin=None, allowances=None):
    """K-loader (R3-MCU-01): (issues, evidence). Every U1 pin on a LOADER_H74X port that carries a net needs a
    LOADER_R10 allowance naming that net and the net's exact other members (pad -> part value); a loader-driven pin
    needs a reason for the drive; stale allowances fail."""
    allowances = LOADER_R10 if allowances is None else allowances
    if port_pin is None:
        with R10_PIN_TABLE.open() as table:
            port_pin = {row['port']: row['pin'] for row in csv.DictReader(table, delimiter='\t')}
    u1 = board.FindFootprintByReference(MCU_REF)
    if u1 is None:
        return ['U1 missing'], {}
    members = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            if real_net(p.GetNetname()) and f.GetReference() != MCU_REF:
                members.setdefault(p.GetNetname(), {})[f'{f.GetReference()}.{p.GetNumber()}'] = f.GetValue()
    issues, ev, used = [], {}, set()
    for port, (role, use) in sorted(LOADER_H74X.items()):
        pin = port_pin.get(port)
        if pin is None:
            ev[port] = 'not on this package'
            continue
        pad = u1.FindPadByNumber(pin)
        net = pad.GetNetname() if pad else None
        where = f'U1.{pin} {port} ({role}, loader {use}; AN2606 Rev 64 Table 119)'
        if pad is None:
            issues.append(f'{where}: pad missing')
            continue
        if not real_net(net):
            ev[port] = 'NC'
            continue
        entry = allowances.get(port)
        if entry is None:
            issues.append(f'{where} carries {net} with no LOADER_R10 allowance' +
                          (' (the loader drives this pin)' if use in LOADER_DRIVES else ''))
            continue
        used.add(port)
        want, pinned, reason = entry
        ev[port] = dict(net=net, role=role, use=use, reason=reason)
        if net != want:
            issues.append(f'{where} carries {net}; its allowance is for {want}')
            continue
        if not reason or not reason.strip():
            issues.append(f'{where}: allowance without an electrical reason')
        if pinned is not None:
            actual = members.get(net, {})
            if actual != pinned:
                extra = sorted(f'{k} {v}' for k, v in actual.items() if pinned.get(k) != v)
                gone = sorted(f'{k} {v}' for k, v in pinned.items() if actual.get(k) != v)
                issues.append(f'{where}: {net} members differ from the allowance (now {extra}, recorded {gone}); '
                              're-qualify the loader state')
    issues += [f'stale LOADER_R10 allowance {port} ({allowances[port][0]}): the pin carries no net or is not a loader '
               'pin' for port in sorted(set(allowances) - used)]
    return issues, ev


def k_loader(ctx):
    issues, ev = loader_pins(ctx.board)
    return [f'K-loader: {i}' for i in issues], ev


def silk_mask_overlaps(board, eps=0.001):
    """R3-MFG-01: every silkscreen item (board graphics and texts, footprint graphics, texts and visible fields), as its
    polygon, against every pad's solder mask opening on that side (the pad's copper polygon grown by its mask
    expansion; a pad with no mask layer on that side has none). DRC's silk-to-mask test misses degenerate shapes (a
    near-zero-length arc drawn as a nearly full circle); the polygons do not. Returns [(silk label, pad label, overlap
    depth mm)] with the depth the smaller side of the overlap's bounding box."""
    import pcbnew
    sides = ((pcbnew.F_SilkS, pcbnew.F_Mask, pcbnew.F_Cu), (pcbnew.B_SilkS, pcbnew.B_Mask, pcbnew.B_Cu))
    silk = {s: [] for s, _, _ in sides}

    def add(item, label):
        lay = item.GetLayer()
        if lay not in silk:
            return
        if hasattr(item, 'IsVisible') and not item.IsVisible():
            return
        poly = pcbnew.SHAPE_POLY_SET()
        item.TransformShapeToPolygon(poly, lay, 0, pcbnew.FromMM(0.001), pcbnew.ERROR_OUTSIDE)
        if poly.OutlineCount():
            silk[lay].append((label, poly, poly.BBox()))
    for d in board.GetDrawings():
        add(d, f'board {type(d).__name__} {getattr(d, "GetShapeStr", lambda: "")()}'.strip())
    for f in board.GetFootprints():
        ref = f.GetReference()
        for g in f.GraphicalItems():
            kind = g.GetShapeStr() if hasattr(g, 'GetShapeStr') else type(g).__name__
            at = g.GetStart() if hasattr(g, 'GetStart') else g.GetPosition()
            add(g, f'{ref} {kind} ({pcbnew.ToMM(at.x):.4f}, {pcbnew.ToMM(at.y):.4f})')
        for fld in f.GetFields():
            add(fld, f'{ref} field {fld.GetName()}')
    out = []
    for slay, mlay, clay in sides:
        if not silk[slay]:
            continue
        for f in board.GetFootprints():
            for p in f.Pads():
                if not p.IsOnLayer(mlay):
                    continue
                opening = pcbnew.SHAPE_POLY_SET()
                cu = clay if p.IsOnLayer(clay) else mlay
                grow = p.GetSolderMaskExpansion(mlay)
                p.TransformShapeToPolygon(opening, cu, max(0, grow), pcbnew.FromMM(0.001), pcbnew.ERROR_OUTSIDE)
                if grow < 0:                                   # a negative local margin shrinks the opening
                    opening.Inflate(grow, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, pcbnew.FromMM(0.001))
                if not opening.OutlineCount():
                    continue
                ob = opening.BBox()
                for label, poly, pb in silk[slay]:
                    if not pb.Intersects(ob):
                        continue
                    both = pcbnew.SHAPE_POLY_SET(poly)
                    both.BooleanIntersection(opening)
                    if not both.OutlineCount():
                        continue
                    bb = both.BBox()
                    depth = pcbnew.ToMM(min(bb.GetWidth(), bb.GetHeight()))
                    if depth > eps:
                        out.append((label, f'{f.GetReference()}.{p.GetNumber()} ({board.GetLayerName(mlay)})',
                                    round(depth, 3)))
    return sorted(set(out))



PORT_LEGENDS_R10 = {'J2': ('3V3', 'SWDIO', 'NRST', 'SWCLK', 'GND', 'NC')}
SERVO_HARNESS_NOTE = 'SERVO + FROM HARNESS'


def legend_items(board):
    items = list(board.GetDrawings())
    for fp in board.GetFootprints():
        items += list(fp.GraphicalItems()) + list(fp.GetFields())
    return items


def terminal_legends(board, items=None, terminals=None):
    """R10 individual terminal labels: every exact word once, strictly nearest its own connector pin. Text boxes
    and footprint text have the same policy as board text. Combined tables conflict with the individual labels."""
    import pcbnew
    terminals = dict(TERMINAL_PINS_R10 if terminals is None else terminals)
    expected = {(ref, n): f'{n}:{name}' for ref, pins in terminals.items() for n, name in pins}
    pads = [(f.GetReference(), p.GetNumber(), p.GetPosition()) for f in board.GetFootprints()
            if re.fullmatch(r'J\d+', f.GetReference()) for p in f.Pads() if p.GetNumber()]
    found, issues, evidence = {}, [], {}
    for item in legend_items(board) if items is None else items:
        if (not isinstance(item, (pcbnew.PCB_TEXT, pcbnew.PCB_TEXTBOX))
                or item.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS)
                or (hasattr(item, 'IsVisible') and not item.IsVisible())):
            continue
        text = item.GetText().strip()
        m = re.fullmatch(r'(J\d+)\s+(.+)', text)
        if m and m[1] in terminals:
            for pin, name in re.findall(r'(\d+):(\S+)', m[2]):
                issues.append(f'{m[1]}.{pin}: conflicting silkscreen pin legend {text!r}: this terminal uses '
                              f'individual "{expected.get((m[1], pin), "?")}" labels, not a combined table')
            continue
        if not re.fullmatch(r'\d+:\S+', text):
            continue
        if not pads:
            issues.append(f'terminal pin legend {text!r}: no connector pin on the board')
            continue
        bb = item.GetBoundingBox()

        def gap(c):
            return math.hypot(max(bb.GetLeft() - c.x, c.x - bb.GetRight(), 0),
                              max(bb.GetTop() - c.y, c.y - bb.GetBottom(), 0))
        ranked = sorted((gap(c), ref, num) for ref, num, c in pads)
        d0, ref, pin = ranked[0]
        d1 = ranked[1][0] if len(ranked) > 1 else math.inf
        key = (ref, pin)
        evidence[f'{text} ({pcbnew.ToMM(bb.GetLeft()):.3f}, {pcbnew.ToMM(bb.GetTop()):.3f})'] = (
            f'{ref}.{pin}', round(pcbnew.ToMM(d0), 3))
        if text != expected.get(key) or d1 - d0 <= pcbnew.FromMM(.01):
            issues.append(f'{ref}.{pin}: conflicting silkscreen pin legend {text!r}: its strictly nearest connector '
                          f'pin must be labelled "{expected.get(key, "not a terminal pin")}"')
        else:
            found[key] = found.get(key, 0) + 1
    for (ref, pin), word in expected.items():
        if board.FindFootprintByReference(ref) is not None and found.get((ref, pin), 0) != 1:
            issues.append(f'{ref}.{pin}: {found.get((ref, pin), 0)} legends "{word}" nearest it, expected one')
    return issues, evidence


# R18-GATE-08: the connector word legends as a blocking identity check: each appears once and sits beside its own
# connector, i.e. its ink box is nearer that connector's courtyard box than any other connector's (J*) on the legend's
# face by more than WORD_TIE. A connector is on a face when it is mounted there or has plated through-holes (the DB125
# terminals are on both); J430, the bottom-side microSD socket under RADIO, is not beside a top legend. AUD-10's 6 mm
# distance stays a review count. The words are WORD_LEGENDS_R10 alone (D-R19-06).
WORD_TIE = 0.01                 # mm
# A word legend at the seam of two abutting connectors touches both: (word, its own connector, the other one, measured
# reason). Accepted only while the two gaps tie (within WORD_TIE); a moved legend or an unused entry fails. D-R19-06
# (R19-MFG-01 / R19-GATE-06) moved RADIO off the J410 / J420 seam, so R10 names none.
WORD_SEAMS = []
# D-R19-06: J410 and J420 carry identical pin legends, so the word is the only thing that tells them apart: it must lie
# inside its own terminal's courtyard y-span (the pin row axis), WORD_SPAN_MARGIN clear of both ends (a seam word fails).
WORD_SPAN_R10 = {'GPS': 'J410', 'RADIO': 'J420', 'AUX': 'J440'}   # D-R19-14: J440 has the same pin legends too
WORD_SPAN_MARGIN = 0.5          # mm
# R19-GATE-06: centre distance as a legibility margin (r10_post's SUBJECT_MARGIN for notes): the centre of a word's ink box
# lies nearer its own connector's courtyard box than any other connector's on its face by WORD_CENTRE_MARGIN. Blocking
# for GPS and RADIO (identical port terminals with identical pin legends: the word is the only cue) and for every word
# whose margin cleared it on the R10 board (measured 2026-10-31: AUX 14.465, GPS 13.178, IGN 5.265, SERVO 3.764,
# RADIO 3.716, CAM 3.451, SWD 2.853 mm). BAT and SWITCH fill the 1.19 mm gaps between DB125 courtyards (0.080 / 0.040 mm,
# D-R19-06 keeps them there; per-pin legends and J121's black body disambiguate): their margins are reported only.
WORD_CENTRE_MARGIN = 1.0        # mm
WORD_CENTRE_BLOCKING = ('GPS', 'RADIO', 'AUX', 'IGN', 'SERVO', 'CAM', 'SWD')


def word_legends(board, items=None, subjects=WORD_LEGENDS_R10, seams=WORD_SEAMS, tie=WORD_TIE, spans=WORD_SPAN_R10,
                 span_margin=WORD_SPAN_MARGIN, centre_words=WORD_CENTRE_BLOCKING, centre_margin=WORD_CENTRE_MARGIN):
    """(issues, evidence): every connector word legend once, as visible silkscreen text or text box (board or footprint
    text), beside its own connector: no other connector's courtyard box within `tie` of the gap to its own, except a
    named, still-tied seam; a word of `spans` also lies inside its own connector's courtyard y-span by `span_margin`; a
    word of `centre_words` has its ink-box centre nearer its own courtyard box than any other by `centre_margin`
    (R19-GATE-06; every word's centre margin is reported)."""
    import pcbnew
    import check_r7 as r7
    mm = pcbnew.ToMM
    boxes = {pcbnew.F_SilkS: {}, pcbnew.B_SilkS: {}}
    for f in board.GetFootprints():
        if re.fullmatch(r'J\d+', f.GetReference()):
            c = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
            r = c.BBox() if c.OutlineCount() else f.GetBoundingBox(False)
            box = (mm(r.GetX()), mm(r.GetY()), mm(r.GetRight()), mm(r.GetBottom()))
            through = any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in f.Pads())
            for face, flipped in ((pcbnew.F_SilkS, False), (pcbnew.B_SilkS, True)):
                if through or f.IsFlipped() == flipped:
                    boxes[face][f.GetReference()] = box
    found, issues, evidence, used = {}, [], {}, set()
    for item in legend_items(board) if items is None else items:
        if (not isinstance(item, (pcbnew.PCB_TEXT, pcbnew.PCB_TEXTBOX))
                or item.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS)
                or (hasattr(item, 'IsVisible') and not item.IsVisible())):
            continue
        word = item.GetText().strip()
        if word not in subjects:
            continue
        found[word] = found.get(word, 0) + 1
        own = subjects[word]
        poly = pcbnew.SHAPE_POLY_SET()
        item.TransformShapeToPolygon(poly, item.GetLayer(), 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
        q = poly.BBox()
        ink = (mm(q.GetX()), mm(q.GetY()), mm(q.GetRight()), mm(q.GetBottom()))
        gaps = {ref: r7._box_gap(ink, box) for ref, box in boxes[item.GetLayer()].items()}
        where = f'{word!r} at ({ink[0]:.3f}, {ink[1]:.3f})'
        evidence[where] = {ref: round(g, 3) for ref, g in sorted(gaps.items(), key=lambda kv: kv[1])[:3]}
        if own not in gaps:
            issues.append(f'{own}: word legend {where} names a connector that is not on the board on its face')
            continue
        cx, cy = (ink[0] + ink[2]) / 2, (ink[1] + ink[3]) / 2
        centre = {ref: math.hypot(max(box[0] - cx, 0, cx - box[2]), max(box[1] - cy, 0, cy - box[3]))
                  for ref, box in boxes[item.GetLayer()].items()}
        margin = min((d for ref, d in centre.items() if ref != own), default=math.inf) - centre[own]
        evidence[where]['centre_margin'] = round(margin, 3)
        if word in centre_words and margin < centre_margin - EPS:
            nearest = min((ref for ref in centre if ref != own), key=centre.get)
            issues.append(f'{own}: word legend {where} centre is {centre[own]:.3f} mm from its own connector and '
                          f'{centre[nearest]:.3f} mm from {nearest}: it must be nearer its own by {centre_margin} mm '
                          '(R19-GATE-06)')
        if word in spans:
            y0, y1 = boxes[item.GetLayer()][own][1], boxes[item.GetLayer()][own][3]
            inside = min(ink[1] - y0, y1 - ink[3])
            evidence[where]['own_y_span_margin'] = round(inside, 3)
            if inside < span_margin - EPS:
                issues.append(f'{own}: word legend {where} lies {inside:.3f} mm inside its courtyard y-span '
                              f'({y0:.3f} .. {y1:.3f}); it must be inside by {span_margin} mm (D-R19-06)')
        for ref, g in sorted(gaps.items(), key=lambda kv: kv[1]):
            if ref == own or g > gaps[own] + tie:
                continue
            seam = next((k for k, x in enumerate(seams) if x[:3] == (word, own, ref)), None)
            if seam is not None and abs(g - gaps[own]) <= tie:
                used.add(seam)
                continue
            issues.append(f'{own}: word legend {where} is {g:.3f} mm from {ref} and {gaps[own]:.3f} mm from its own '
                          f'connector {own}: it must sit beside {own} (nearer it by more than {tie} mm)')
    for word, own in subjects.items():
        if board.FindFootprintByReference(own) is not None and found.get(word, 0) != 1:
            issues.append(f'{own}: word legend {word!r} appears {found.get(word, 0)} times on silkscreen, expected once')
    issues += [f'stale WORD_SEAMS entry {x[:3]} ({x[3]})' for k, x in enumerate(seams) if k not in used]
    return issues, evidence


# R19-GATE-07: AGENTS.md section 3 allows on silkscreen only designators, the terminal, arming and connector legends and
# the revision legend. Every visible silkscreen text (board text, text box, footprint text and field, either face) must
# be one of: a footprint's own Reference field (or a board text naming a footprint), a TERMINAL_PINS_R10 pin legend, a
# WORD_LEGENDS_R10 word, a PORT_LEGENDS_R10 row, SERVO_HARNESS_NOTE or a PINNED_TEXTS text. Which legend sits where stays
# with the other K-legends checks. D-R24-13 (R23-MANUFACTURING-02): JLC withdrew the order-number mark in May 2026 and
# asks for no JLCJLCJLCJLC text (https://jlcpcb.com/help/article/How-to-mark-on-PCB, updated 2026-05-22), so the
# placeholder is no longer allowed.
JLC_ORDER_MARK = 'JLCJLCJLCJLC'     # withdrawn (D-R24-13): not allowed on silkscreen


def silk_allowlist(board, items=None):
    """(issues, evidence): every visible silkscreen text is one of the allowed kinds (R19-GATE-07)."""
    import pcbnew
    refs = {f.GetReference() for f in board.GetFootprints()}
    allowed = ({f'{n}:{name}' for _, pins in TERMINAL_PINS_R10 for n, name in pins} | set(WORD_LEGENDS_R10)
               | {SERVO_HARNESS_NOTE} | {text for _, text in PINNED_TEXTS})

    def port_row(text):
        m = re.fullmatch(r'(J\d+)((?:\s+\d+:\S+)+)', text)
        names = PORT_LEGENDS_R10.get(m[1], ()) if m else ()
        rows = re.findall(r'(\d+):(\S+)', m[2]) if m else []
        return bool(rows) and all(0 < int(n) <= len(names) and names[int(n) - 1] == name for n, name in rows)
    issues, counts = [], {}
    for item in legend_items(board) if items is None else items:
        if (not isinstance(item, (pcbnew.PCB_TEXT, pcbnew.PCB_TEXTBOX))
                or item.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS)
                or (hasattr(item, 'IsVisible') and not item.IsVisible())):
            continue
        text = item.GetShownText(True).strip()
        parent = item.GetParentFootprint()
        if isinstance(item, pcbnew.PCB_FIELD) and item.GetName() == 'Reference':
            kind = 'designator' if parent is not None and text == parent.GetReference() else None
        elif isinstance(item, pcbnew.PCB_FIELD):
            kind = None                                    # a Value / part-number field shown on silkscreen
        elif text in refs:
            kind = 'designator text'
        elif text in allowed:
            kind = 'legend'
        elif port_row(text):
            kind = 'port row'
        else:
            kind = None
        if kind is None:
            box = item.GetBoundingBox()
            owner = f'{parent.GetReference()} ' if parent is not None else ''
            field = f'{item.GetName()} field ' if isinstance(item, pcbnew.PCB_FIELD) else ''
            issues.append(f'silkscreen text {text!r} ({owner}{field}{board.GetLayerName(item.GetLayer())}, '
                          f'{pcbnew.ToMM(box.GetCenter().x):.2f}, {pcbnew.ToMM(box.GetCenter().y):.2f}) is not a '
                          'designator or an allowed legend (R19-GATE-07, AGENTS.md section 3)')
        else:
            counts[kind] = counts.get(kind, 0) + 1
    return issues, counts


def port_legends(board, required=PORT_LEGENDS_R10, terminal_evidence=None):
    """R10 port / servo tables and harness note: every pin and note appears exactly once, without conflicting text."""
    import pcbnew
    seen, texts, issues = {}, [], []
    items = legend_items(board)
    for item in items:
        if (not isinstance(item, (pcbnew.PCB_TEXT, pcbnew.PCB_TEXTBOX))
                or item.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS)
                or (hasattr(item, 'IsVisible') and not item.IsVisible())):
            continue
        text = item.GetText().strip()
        texts.append(text)
        if re.match(r'^J122\s+.*\bNC\b', text):
            issues.append('J122: obsolete header NC-row legend; terminal contacts are S1/S2/S3/S4/GND')
        m = re.match(r'^(J\d+)\s+(.+)', text)
        if m and m[1] in required:
            if not re.fullmatch(r'\d+:[A-Z0-9]+(?:\s+\d+:[A-Z0-9]+)*', m[2]):
                issues.append(f'{m[1]}: malformed silkscreen pin table {text!r}')
            for pin, name in re.findall(r'(\d+):([A-Z0-9]+)', m[2]):
                seen.setdefault((m[1], int(pin)), []).append(name)
    issues += [f'{ref}.{i}: silkscreen must identify {name} exactly once (R10 port table)'
               for ref, names in required.items() for i, name in enumerate(names, 1)
               if seen.get((ref, i)) != [name]]
    issues += [f'{ref}.{pin}: unexpected silkscreen pin legend (R10 port table)' for ref, pin in seen
               if pin not in range(1, len(required[ref]) + 1)]
    found, evidence = terminal_legends(board, items)
    issues += found
    if terminal_evidence is not None:
        terminal_evidence.update(evidence)
    if texts.count(SERVO_HARNESS_NOTE) != 1:
        issues.append(f'J122: silkscreen must identify {SERVO_HARNESS_NOTE!r} exactly once')
    issues += [f'J122: conflicting servo harness legend {text!r}' for text in texts
               if text.startswith('SERVO ') and text != SERVO_HARNESS_NOTE]
    return issues


# K-text (R8-GATE-02): the revision and safety legends are pinned to their exact words (a changed text fails).
PINNED_TEXTS = (('B.Silkscreen', 'M3-ASSY-R10'),)
# R8-GATE-03: these references must stay shown on silkscreen (all shown on the R10 board now). The full hidden list is
# reported in the evidence, not pinned.
SHOWN_REFS = ('J1', 'J121', 'J122', 'J400', 'J9', 'J410', 'J420', 'J440', 'J3', 'Q120', 'Q121', 'Q124', 'R134')


def pinned_texts(board, pinned=PINNED_TEXTS):
    import pcbnew
    have = {}
    items = list(board.GetDrawings())
    for fp in board.GetFootprints():
        items += list(fp.GraphicalItems()) + list(fp.GetFields())
    for item in items:
        if isinstance(item, pcbnew.PCB_TEXT) and (not hasattr(item, 'IsVisible') or item.IsVisible()):
            have[(board.GetLayerName(item.GetLayer()), item.GetText())] = have.get(
                (board.GetLayerName(item.GetLayer()), item.GetText()), 0) + 1
    out = [f'silkscreen text {t!r} missing on {lay} (pinned revision / safety legend)' for lay, t in pinned
           if have.get((lay, t), 0) != 1]
    out += [f'obsolete ARM terminal or fuse legend {t!r} (single screw switch)' for (lay, t) in have
            if lay.endswith('Silkscreen') and (re.search(r'\bJ124\b|\bFUSE\b|\b5A\s+FAST\b', t, re.I)
                                               or re.fullmatch(r'ARM(?:1| CH1)?', t.strip(), re.I))]
    revs = sorted({t for (_, t) in have if re.match(r'^M3-ASSY-R\d+$', t)})
    return out + [f'revision legends {revs}: only M3-ASSY-R10 allowed' for _ in [0] if revs != ['M3-ASSY-R10']]


def hidden_refs(board, shown=SHOWN_REFS):
    """(issues, evidence): references not drawn on a silkscreen layer; a pinned safety / connector part may not be."""
    import pcbnew
    hidden = sorted(f.GetReference() for f in board.GetFootprints()
                    if not (f.Reference().IsVisible() and f.Reference().GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)))
    issues = [f'{r}: reference designator hidden (a safety / connector part must show it)'
              for r in shown if r in hidden]
    return issues, dict(hidden=hidden, hidden_count=len(hidden))


# K-width (R8-GATE-04): BAT_IN / RAW_PROTECTED track widths (recorded minimum 0.3 mm: U9 pad entries, D-R3-03).
HC_MIN_W = {'BAT_IN': 0.3, 'RAW_PROTECTED': 0.3}
HC_NARROW_MAX_LEN = 2.0          # mm: a chain of minimum-width segments longer than this fails
LOW_CURRENT_TAPS = (('R80', '1'), ('R82', '1'), ('R167', '1'), ('R92', '1'))


def resistor_tap_tracks(board):
    """Only dead-end branches from the four named resistor pads, stopping at the first power-copper junction.
    An unsplit segment containing an interior junction is not exempt. No power net is exempt as a whole."""
    import pcbnew
    tracks = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK']
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
    pads = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname()]
    same_point = lambda a, b: (a - b).EuclideanNorm() <= 1000

    def on_track(t, p):
        a, b = t.GetStart(), t.GetEnd()
        dx, dy = b.x - a.x, b.y - a.y
        den = dx * dx + dy * dy
        k = max(0., min(1., ((p.x - a.x) * dx + (p.y - a.y) * dy) / den)) if den else 0.
        return math.hypot(p.x - a.x - k * dx, p.y - a.y - k * dy) <= t.GetWidth() / 2 + 1000

    def in_fill(net, layer, point):
        return any(not z.GetIsRuleArea() and z.GetNetname() == net and z.IsOnLayer(layer)
                   and z.HasFilledPolysForLayer(layer) and z.GetFilledPolysList(layer).Contains(point, -1, 0, True)
                   for z in board.Zones())

    qualified, evidence = set(), {}
    for ref, number in LOW_CURRENT_TAPS:
        fp = board.FindFootprintByReference(ref)
        pad = fp.FindPadByNumber(number) if fp else None
        if pad is None or pad.GetNetname() not in HC_MIN_W:
            continue
        net = pad.GetNetname()
        candidates = [t for t in tracks if t.GetNetname() == net]
        starts = [(t, point) for t in candidates for point in (t.GetStart(), t.GetEnd())
                  if pad.IsOnLayer(t.GetLayer()) and pad.HitTest(point)]
        if len(starts) != 1:
            continue                         # A resistor pad on a through power run is not a dead-end tap.
        track, point = starts[0]
        layer = track.GetLayer()
        foreign = [p for p in pads if p.m_Uuid.AsString() != pad.m_Uuid.AsString()
                   and p.GetNetname() == net and p.IsOnLayer(layer)]
        same_vias = [v for v in vias if v.GetNetname() == net and v.IsOnLayer(layer)]
        if any(p.HitTest(point) for p in foreign) or any(same_point(v.GetPosition(), point) for v in same_vias) \
                or in_fill(net, layer, point):
            continue
        path, visited, joined = [], set(), False
        while track.m_Uuid.AsString() not in visited:
            uid = track.m_Uuid.AsString(); visited.add(uid)
            a, b = track.GetStart(), track.GetEnd()
            end = b if same_point(point, a) else a
            interior = lambda q: on_track(track, q) and not same_point(q, a) and not same_point(q, b)
            if any(interior(q) for t in candidates if t is not track and t.GetLayer() == layer
                   for q in (t.GetStart(), t.GetEnd())) or any(interior(v.GetPosition()) for v in same_vias):
                break
            shape = track.GetEffectiveShape(layer)
            if any(not p.HitTest(a) and not p.HitTest(b) and shape.Collide(p.GetEffectiveShape(layer), 0)
                   for p in foreign):
                break
            path.append(track)
            touching = [t for t in candidates if t.m_Uuid.AsString() not in visited
                        and t.GetLayer() == layer and on_track(t, end)]
            pad_join = any(p.HitTest(end) for p in foreign)
            via_join = any(same_point(v.GetPosition(), end) for v in same_vias)
            body_join = any(not same_point(end, t.GetStart()) and not same_point(end, t.GetEnd()) for t in touching)
            if pad_join or via_join or body_join or in_fill(net, layer, end) or len(touching) > 1:
                joined = True
                break
            if len(touching) != 1:
                break
            point, track = end, touching[0]
        if joined:
            qualified.update(t.m_Uuid.AsString() for t in path)
            evidence[f'{ref}.{number}'] = dict(net=net, segments=len(path),
                length_mm=round(sum(pcbnew.ToMM(t.GetLength()) for t in path), 4), minimum_mm=.15)
    return qualified, evidence


def k_width(board, floor=HC_MIN_W, max_len=HC_NARROW_MAX_LEN):
    import pcbnew
    mm = pcbnew.ToMM
    issues, ev = [], {}
    taps, tap_evidence = resistor_tap_tracks(board)
    ev['resistor_only_taps'] = tap_evidence
    for net, wmin in floor.items():
        tr = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == net]
        ev[net] = dict(tracks=len(tr), min_width_mm=round(min((mm(t.GetWidth()) for t in tr), default=0), 3))
        narrow = []
        for t in tr:
            w = mm(t.GetWidth())
            if t.m_Uuid.AsString() in taps:
                if w < .15 - EPS:
                    issues.append(f'{net} resistor-only tap track {w:.3f} mm wide; minimum 0.15 mm')
                continue
            if w < wmin - EPS:
                issues.append(f'{net} track {w:.3f} mm wide at ({mm(t.GetStart().x):.2f}, {mm(t.GetStart().y):.2f}) '
                              f'on {board.GetLayerName(t.GetLayer())}; minimum {wmin} mm')
            elif w <= wmin + EPS:
                narrow.append(t)
        parent = list(range(len(narrow)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i, a in enumerate(narrow):
            for j in range(i):
                b = narrow[j]
                ends = lambda t: {(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)}   # noqa: E731
                if a.GetLayer() == b.GetLayer() and ends(a) & ends(b):
                    parent[find(i)] = find(j)
        chains = {}
        for i, t in enumerate(narrow):
            chains.setdefault(find(i), []).append(t)
        longest = 0.0
        for ts in chains.values():
            length = sum(mm(t.GetLength()) for t in ts)
            longest = max(longest, length)
            if length > max_len + EPS:
                t = ts[0]
                issues.append(f'{net}: {wmin} mm-wide run {length:.2f} mm long on {board.GetLayerName(t.GetLayer())} '
                              f'near ({mm(t.GetStart().x):.2f}, {mm(t.GetStart().y):.2f}); limit {max_len} mm')
        ev[net]['longest_narrow_run_mm'] = round(longest, 2)
    return issues, ev


def poly_gap(a, c):
    """(edge distance mm, overlap area mm^2) of two SHAPE_POLY_SETs: (0, area) when they overlap (r7_post._poly_gap's
    measure, kept here so the gate does not depend on the generator)."""
    import pcbnew
    x = pcbnew.SHAPE_POLY_SET(a)
    x.BooleanIntersection(c)
    if x.OutlineCount():
        return 0.0, x.Area() / 1e12
    best = None
    for p_, q_ in ((a, c), (c, a)):
        for o in range(p_.OutlineCount()):
            chain = p_.Outline(o)
            for i in range(chain.PointCount()):
                for k in range(q_.OutlineCount()):
                    d = q_.Outline(k).SquaredDistance(chain.CPoint(i))
                    best = d if best is None else min(best, d)
    return (pcbnew.ToMM(math.sqrt(best)) if best is not None else math.inf), 0.0


# R20-MFG-02: AGENTS.md section 3 puts a designator nearer its own part than any other. The generator's test
# (m3_design/r7_post.courtyard_offenders / r8_post.courtyard_fails) compared only courtyards whose box centre lay within
# 8 mm of the ink, so a large neighbour's courtyard was never tested. The gate tests every courtyard on the text's face.
# (ref, other, own gap mm, overlap mm^2), measured on the R10 board 2026-10-31 (ink at 0.002 mm, courtyard polygons):
# these three move at the next board change (the generator's pre-filter now tests every courtyard), then delete them.
# D-R20-06: C400, C94 and R461 were re-placed (or hidden) by the generator's any-size courtyard test, so no entry
# remains.
DESIGNATOR_COURTYARD_R20 = []


def designator_courtyards(board, named=None, tol=0.002):
    """(issues, evidence): every visible designator whose ink (TransformShapeToPolygon) lies nearer another part's
    courtyard on the face the text is on than its own part's courtyard (r7_post.courtyard_offenders' measure), with
    every courtyard tested; only an exact DESIGNATOR_COURTYARD_R20 entry passes, and an entry no longer met fails."""
    import pcbnew
    named = DESIGNATOR_COURTYARD_R20 if named is None else named
    yards = {}
    for f in board.GetFootprints():
        ps = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
        if ps.OutlineCount():
            yards[f.GetReference()] = (f.IsFlipped(), ps, ps.BBox())

    def box_gap(a, c):
        dx = max(a.GetLeft() - c.GetRight(), c.GetLeft() - a.GetRight(), 0)
        dy = max(a.GetTop() - c.GetBottom(), c.GetTop() - a.GetBottom(), 0)
        return pcbnew.ToMM(math.hypot(dx, dy))
    offenders, checked = [], 0
    for f in sorted(board.GetFootprints(), key=lambda g: g.GetReference()):
        t, ref = f.Reference(), f.GetReference()
        if not t.IsVisible() or ref not in yards:
            continue
        checked += 1
        ink = pcbnew.SHAPE_POLY_SET()
        t.TransformShapeToPolygon(ink, t.GetLayer(), 0, pcbnew.FromMM(0.002), pcbnew.ERROR_INSIDE)
        back = t.GetLayer() == pcbnew.B_SilkS
        own = poly_gap(ink, yards[ref][1])[0]
        box = ink.BBox()
        near = []
        for other, (flip, ps, bb) in yards.items():
            if other == ref or flip != back or box_gap(box, bb) >= own:    # a polygon is never nearer than its box
                continue
            gap, area = poly_gap(ink, ps)
            if gap < own:
                near.append((gap, -area, other))
        if near:
            gap, area, other = min(near)
            offenders.append((ref, other, round(own, 3), round(gap, 3), round(-area, 3)))
    issues, used = [], set()
    for ref, other, own, gap, area in offenders:
        hit = next((k for k, x in enumerate(named) if x[:2] == (ref, other) and abs(x[2] - own) <= tol
                    and abs(x[3] - area) <= tol and gap == 0), None)
        if hit is not None:
            used.add(hit)
            continue
        issues.append(f"designator {ref} is nearer {other}'s courtyard ({gap:.3f} mm"
                      + (f', overlap {area:.3f} mm^2' if gap == 0 else '') + f') than its own ({own:.3f} mm) '
                      '(R20-MFG-02, AGENTS.md section 3)')
    present = {f.GetReference() for f in board.GetFootprints()}
    issues += [f'stale DESIGNATOR_COURTYARD_R20 entry {x[:4]} ({x[4]})' for k, x in enumerate(named)
               if k not in used and x[0] in present and x[1] in present]
    return issues, dict(designators_checked=checked, courtyards=len(yards),
                        offenders=[dict(ref=r, other=o, own_mm=w, gap_mm=g, overlap_mm2=a) for r, o, w, g, a in offenders])


# R20-MFG-03: a Fab reference (the footprint's '${REFERENCE}' text on its Fab layer) must not cross its own Fab
# outline (the body lines and marks on that layer): R119's 1.0 mm text over its 0402 outline prints as "R1119" in the
# assembly PDF. {ref: overlap mm^2 of the text polygon with the outline strokes}, measured on the R10 board 2026-10-31
# (0.002 mm polygons); r10_post.FAB_REFERENCE_CLEARANCES_R13 is where the CAD fix goes, then delete the entry.
# D-R20-07: the six measured crossings (C123, C445, D440, D441, R119, R173) are fixed in r10_post's
# FAB_REFERENCE_CLEARANCES_R13, so no entry remains.
FAB_REF_CROSSINGS_R20 = {}
# D-R21-08 (R21-GATE-05): the assembly drawings (bound fab outputs; C84 is fitted by hand from them) need every
# footprint's Fab designator: exactly one '${REFERENCE}' text on the footprint's own Fab layer, visible, at least
# FAB_REF_MIN_H high, its ink box crossing no other footprint's Fab outline strokes or Fab reference, and its ink centre
# inside no other footprint's Fab outline box (on another part's body). The only other Fab texts are the LS120
# buzzer's polarity marks (its library land).
FAB_TEXT_ALLOWED = {'LS120': ('+', '-')}
FAB_REF_MIN_H = 0.3            # mm (the smallest on the round 21 board: 0.3 mm, two parts)
# D-R22-06 (R22-GATE-02): each Fab reference's ink centre lies within FAB_REF_REACH of its own part's box (its Fab body
# shapes' box, or its courtyard box for the 14 parts whose Fab layer has no body outline, only a pin-1 dot or nothing);
# measured on 5516eeec: 20 references sit beside their body, the farthest 0.968 mm (D9). Every stroke is at least
# FAB_STROKE_RATIO x its height or FAB_STROKE_MIN (the board: 0.15 x height). No board-level text on a Fab layer.
FAB_REF_REACH = 1.5            # mm
FAB_STROKE_RATIO, FAB_STROKE_MIN = 0.1, 0.05
# D-R23-08 (R23-GATE-04): a Fab reference's character width is at least FAB_WIDTH_RATIO x its height or FAB_REF_MIN_H
# (the board: every Fab reference square, width = height)
FAB_WIDTH_RATIO = 0.5


def fab_ref_crossings(board, named=None, tol=0.001, allowed=None, min_h=FAB_REF_MIN_H, reach=None):
    """(issues, evidence): R20-MFG-03, every footprint's visible Fab reference that intersects its own Fab-layer shapes
    (only an exact FAB_REF_CROSSINGS_R20 entry passes; an entry whose crossing is gone fails as stale); D-R21-08, each
    footprint's one Fab reference (text, side, visibility, height) and its ink box clear of every other footprint's Fab
    outline (its strokes, and its box for the ink centre) and Fab reference ink box."""
    import pcbnew
    named = FAB_REF_CROSSINGS_R20 if named is None else named
    allowed = FAB_TEXT_ALLOWED if allowed is None else allowed
    reach = FAB_REF_REACH if reach is None else reach
    found, checked, used, issues = {}, 0, set(), []
    outlines, boxes, offsets, strokes, courtyard_boxed = {}, {}, {}, {}, []
    fabs = (pcbnew.F_Fab, pcbnew.B_Fab)
    for d in board.GetDrawings():                                      # D-R22-06: no board-level Fab text
        if d.GetLayer() not in fabs:
            continue
        at = d.GetPosition()
        where = f'on {board.GetLayerName(d.GetLayer())} at ({pcbnew.ToMM(at.x):.2f}, {pcbnew.ToMM(at.y):.2f})'
        if isinstance(d, (pcbnew.PCB_TEXT, pcbnew.PCB_TEXTBOX)):
            issues.append(f'board-level text {d.GetText()!r} {where}: only footprint references belong on the Fab layers '
                          '(R22-GATE-02)')
        else:                                                          # D-R23-08: no board-level Fab shape either
            issues.append(f'board-level {d.GetClass()} {where}: nothing but footprints belongs on the Fab layers '
                          '(R23-GATE-04)')

    def ink_box(t, lay):
        poly = pcbnew.SHAPE_POLY_SET()
        t.TransformShapeToPolygon(poly, lay, 0, pcbnew.FromMM(0.002), pcbnew.ERROR_INSIDE)
        bb = poly.BBox()
        box = pcbnew.SHAPE_POLY_SET()
        box.NewOutline()
        for x, y in ((bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()), (bb.GetRight(), bb.GetBottom()),
                     (bb.GetLeft(), bb.GetBottom())):
            box.Append(x, y)
        return poly, box
    for f in sorted(board.GetFootprints(), key=lambda g: g.GetReference()):
        ref = f.GetReference()
        fab = pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab
        # D-R23-08 (R23-GATE-04): text boxes and visible fields on a Fab layer are Fab text too
        fab_texts = [g for g in f.GraphicalItems() if isinstance(g, (pcbnew.PCB_TEXT, pcbnew.PCB_TEXTBOX))
                     and g.GetLayer() in fabs]
        fab_texts += [g for g in f.GetFields() if g.GetLayer() in fabs and g.IsVisible()]
        refs = [g for g in fab_texts if g.GetText() == '${REFERENCE}' and isinstance(g, pcbnew.PCB_TEXT)
                and not isinstance(g, pcbnew.PCB_FIELD)]
        others = sorted(g.GetText() for g in fab_texts if not any(g is r for r in refs))
        if others != sorted(allowed.get(ref, ())):
            issues.append(f'Fab text {others} on {ref}: only its ${{REFERENCE}} belongs on the Fab layers (R21-GATE-05)')
        if len(refs) != 1:
            issues.append(f'{ref} carries {len(refs)} Fab references; exactly one ${{REFERENCE}} text on '
                          f'{board.GetLayerName(fab)} (R21-GATE-05)')
        for t in refs:
            h = pcbnew.ToMM(t.GetTextHeight())
            if t.GetLayer() != fab:
                issues.append(f'Fab reference {ref} is on {board.GetLayerName(t.GetLayer())}, not its own side '
                              f'{board.GetLayerName(fab)}')
            if not t.IsVisible():
                issues.append(f'Fab reference {ref} is hidden')
            if h < min_h - 1e-6:
                issues.append(f'Fab reference {ref} is {h:.3f} mm high, under {min_h} mm (unreadable in the assembly '
                              'drawing, R21-GATE-05)')
            cw = pcbnew.ToMM(t.GetTextWidth())                         # D-R23-08: character width floor
            if cw < FAB_WIDTH_RATIO * h - 1e-6 and cw < min_h - 1e-6:
                issues.append(f'Fab reference {ref} characters are {cw:.3f} mm wide, under {FAB_WIDTH_RATIO} x its {h:.3f} '
                              f'mm height and under {min_h} mm (squashed, R23-GATE-04)')
        shapes = [g for g in f.GraphicalItems() if isinstance(g, pcbnew.PCB_SHAPE) and g.GetLayer() == fab]
        outline = pcbnew.SHAPE_POLY_SET()
        for g in shapes:
            g.TransformShapeToPolygon(outline, fab, 0, pcbnew.FromMM(0.002), pcbnew.ERROR_INSIDE)
        outline.Simplify()
        outlines[ref] = (fab, outline)
        body = [g for g in shapes if g.GetShape() != pcbnew.SHAPE_T_CIRCLE]          # a pin-1 dot is no body
        if body:
            own = body[0].GetBoundingBox()
            for g in body[1:]:
                own.Merge(g.GetBoundingBox())
        else:
            own = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd).BBox()
            courtyard_boxed.append(ref)
        for t in refs:
            if t.GetLayer() != fab or not t.IsVisible():
                continue
            checked += 1
            poly, box = ink_box(t, fab)
            boxes[ref] = (fab, box)
            c = box.BBox().Centre()
            off = pcbnew.ToMM(int(math.hypot(max(own.GetLeft() - c.x, 0, c.x - own.GetRight()),
                                             max(own.GetTop() - c.y, 0, c.y - own.GetBottom()))))
            offsets[ref] = round(off, 3)
            if off > reach + 1e-6:
                issues.append(f'Fab reference {ref} sits {off:.3f} mm from its own part\'s '
                              f'{"Fab body" if body else "courtyard"} box, over {reach} mm (R22-GATE-02)')
            h, w = pcbnew.ToMM(t.GetTextHeight()), pcbnew.ToMM(t.GetTextThickness())
            strokes[ref] = round(w / h, 3) if h else 0.0
            if w < FAB_STROKE_RATIO * h - 1e-6 and w < FAB_STROKE_MIN - 1e-6:
                issues.append(f'Fab reference {ref} stroke {w:.3f} mm is under {FAB_STROKE_RATIO} x its {h:.3f} mm height '
                              f'and under {FAB_STROKE_MIN} mm (invisible in the assembly drawing, R22-GATE-02)')
            if not shapes:
                continue
            x = pcbnew.SHAPE_POLY_SET(poly)
            x.BooleanIntersection(outline)
            if x.OutlineCount():
                found[ref] = round(x.Area() / 1e12, 4)
    for ref, area in found.items():
        if ref in named and abs(named[ref][0] - area) <= tol:
            used.add(ref)
            continue
        issues.append(f'Fab reference {ref} crosses its own Fab outline by {area:.4f} mm^2 (R20-MFG-03: the assembly '
                      'drawing misreads it)')
    present = {f.GetReference() for f in board.GetFootprints()}
    issues += [f'stale FAB_REF_CROSSINGS_R20 entry {ref} ({named[ref][1]})' for ref in sorted(named)
               if ref not in used and ref in present]
    neighbours = []
    for ref, (lay, box) in sorted(boxes.items()):
        bb = box.BBox()
        for other, (olay, outline) in sorted(outlines.items()):
            if other == ref or olay != lay or not outline.OutlineCount() or not outline.BBox().Intersects(bb):
                continue
            x = pcbnew.SHAPE_POLY_SET(box)
            x.BooleanIntersection(outline)
            if x.OutlineCount() and x.Area() > 0:
                neighbours.append((ref, f"{other}'s Fab outline", round(x.Area() / 1e12, 4)))
            elif outline.BBox().Contains(bb.Centre()):           # wholly on the other part's body
                neighbours.append((ref, f"{other}'s Fab outline box (inside it)", 0.0))
        for other, (olay, obox) in sorted(boxes.items()):
            if other <= ref or olay != lay or not obox.BBox().Intersects(bb):
                continue
            x = pcbnew.SHAPE_POLY_SET(box)
            x.BooleanIntersection(obox)
            if x.OutlineCount() and x.Area() > 0:
                neighbours.append((ref, f"{other}'s Fab reference", round(x.Area() / 1e12, 4)))
    issues += [f'Fab reference {ref} crosses {what} by {area:.4f} mm^2 (R21-GATE-05: the assembly drawing names the '
               'wrong part)' for ref, what, area in neighbours]
    far = max(offsets.items(), key=lambda kv: kv[1]) if offsets else None
    return issues, dict(fab_references_checked=checked, crossings=found, neighbour_crossings=neighbours,
                        farthest_from_own_box_mm=far, beside_own_box=sum(1 for v in offsets.values() if v > 0),
                        courtyard_boxed=sorted(courtyard_boxed),
                        least_stroke_ratio=min(strokes.values()) if strokes else None,
                        least_height_mm=min((pcbnew.ToMM(g.GetTextHeight()) for f in board.GetFootprints()
                                             for g in f.GraphicalItems() if isinstance(g, pcbnew.PCB_TEXT)
                                             and g.GetText() == '${REFERENCE}' and g.GetLayer() in fabs), default=None))


def k_legends(ctx):
    import check_r7 as r7
    review, ev = [], {}
    with patched(r7, WORD_LEGENDS=WORD_LEGENDS_R10):
        issues = list(r7.duplicate_ids(ctx.board)) + port_legends(ctx.board, terminal_evidence=ev) + \
            list(r7.legend_subjects(ctx.board, distance_review=review))  # AUD-10: distance only, names still block.
    words, word_ev = word_legends(ctx.board)                              # R18-GATE-08: identity blocks.
    issues += words
    extra, allowed = silk_allowlist(ctx.board)                            # R19-GATE-07: nothing else on silkscreen.
    issues += extra
    found = []
    overlaps = silk_mask_overlaps(ctx.board)
    found += [f'K-legends: silkscreen {s} overlaps the solder mask opening of {p} by {d:.3f} mm (R3-MFG-01)'
              for s, p, d in overlaps]
    texts = [f'K-legends: {i}' for i in pinned_texts(ctx.board)]
    hid, hev = hidden_refs(ctx.board)
    texts += [f'K-legends: {i}' for i in hid]
    yards, yard_ev = designator_courtyards(ctx.board)                    # R20-MFG-02
    fabs, fab_ev = fab_ref_crossings(ctx.board)                          # R20-MFG-03
    texts += [f'K-legends: {i}' for i in yards + fabs]
    return issues + found + texts, dict(terminal_legends=ev, word_legends=word_ev, silk_texts=allowed,
                                       silk_mask_overlaps=len(overlaps), designator_courtyards=yard_ev,
                                       fab_references=fab_ev,
                                       aud10_review=review, aud10_review_count=len(review), **hev)


def k_reference(ctx):
    import critical_reference as cr
    issues, ev = references(ctx.board)
    # R19-REQ-10: a name the R10 gates list that is no net of the board is stale and fails
    stale = cr.r10_stale_names({str(n) for n in ctx.board.GetNetsByName().keys()})
    issues += [f'stale critical_reference.{lst} entry {name!r}: no such net on the board (R19-REQ-10)' for lst, name in stale]
    return [f'K-reference: {i}' for i in issues], ev


# GAP-3: a local VIPPO manufacturing condition, not a general via-in-pad exemption or a fabrication claim.
# TI DSK0010A drawing 4218903/C: footprint-local mm. The exception follows only U401's rigid pose.
VIPPO_LOCAL_CENTRES = ((-.3, 0.), (.3, 0.))
VIPPO_LOCAL_EP = (-.6, -1., .6, 1.)
VIPPO_LOCAL_PASTE = ((-.565, -1., .565, -.11), (-.565, .11, .565, 1.))


def vippo_centres(fp):
    import check_r9 as r9
    return tuple(r9.to_board(fp, *p) for p in VIPPO_LOCAL_CENTRES)


def thermal_vias(board):
    """GAP-3: two 0.5/0.3 GND vias wholly in U401.11, with explicit filled/capped fabrication intent.
    The saved intent does not establish resin filling, copper capping or planarity: ordering and inspection do."""
    import pcbnew
    import check_r8 as r8
    import check_r9 as r9
    issues, qualified = [], set()
    fp = board.FindFootprintByReference('U401')
    pad = fp.FindPadByNumber('11') if fp else None
    if pad is None or pad.GetNetname() != 'GND' or not pad.IsOnLayer(pcbnew.B_Cu):
        return ['GAP-3: U401.11 must be the bottom GND exposed pad'], {}, qualified
    xy = lambda p: (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))
    def local_box(poly):
        points = [r9.to_local(fp, *xy(chain.CPoint(k))) for i in range(poly.OutlineCount())
                  for chain in (poly.Outline(i),) for k in range(chain.PointCount())]
        return (min(x for x, _ in points), min(y for _, y in points),
                max(x for x, _ in points), max(y for _, y in points))
    paste_polys = [poly for name, cu, poly in r8.paste_polys(board) if name == 'U401.paste' and cu == pcbnew.B_Cu]
    paste = [local_box(poly) for poly in paste_polys]
    paste_ok = len(paste) == 2 and all(any(max(abs(a - b) for a, b in zip(local_box(poly), expected)) <= EPS
                 and abs(poly.Area() / 1e12 - (expected[2] - expected[0]) * (expected[3] - expected[1])) <= EPS ** 2
                 for poly in paste_polys) for expected in VIPPO_LOCAL_PASTE)
    if not paste_ok:
        issues.append('GAP-3: U401 maker exposed-pad paste windows changed')
    shape = pad.GetEffectiveShape(pcbnew.B_Cu)
    ep_poly = pcbnew.SHAPE_POLY_SET()
    pad.TransformShapeToPolygon(ep_poly, pcbnew.B_Cu, 0, pcbnew.FromMM(.001), pcbnew.ERROR_INSIDE)
    ep_box = local_box(ep_poly)
    ep_ok = (pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and pad.GetShape() == pcbnew.PAD_SHAPE_RECT
             and fp.IsFlipped() and not pad.IsOnLayer(pcbnew.F_Cu)
             and max(abs(a - b) for a, b in zip(ep_box, VIPPO_LOCAL_EP)) <= EPS)
    if not ep_ok:
        issues.append('GAP-3: U401.11 exposed-pad shape or reviewed local pose changed')
    vias = [v for v in board.GetTracks() if v.GetClass() == 'PCB_VIA'
            and shape.Collide(pcbnew.SHAPE_CIRCLE(v.GetPosition(), v.GetDrillValue() // 2), pcbnew.FromMM(0.1))]
    if len(vias) != 2:
        issues.append(f'GAP-3: U401.11 requires exactly two thermal vias (has {len(vias)})')
    centres = vippo_centres(fp)
    for centre in centres:
        matches = [v for v in vias if math.dist(xy(v.GetPosition()), centre) <= EPS]
        ok = len(matches) == 1
        if ok:
            v = matches[0]
            ring, drill = pcbnew.ToMM(v.GetWidth(pcbnew.B_Cu)), pcbnew.ToMM(v.GetDrillValue())
            ok = (v.GetNetname() == 'GND' and abs(ring - 0.5) <= EPS and abs(drill - 0.3) <= EPS
                  and v.GetViaType() == pcbnew.VIATYPE_THROUGH
                  and v.TopLayer() == pcbnew.F_Cu and v.BottomLayer() == pcbnew.B_Cu
                  and v.GetFillingMode() == pcbnew.FILLING_MODE_FILLED
                  and v.GetCappingMode() == pcbnew.CAPPING_MODE_CAPPED)
            # The full ring, not only its centre, must fit the intended exposed pad.
            r = pcbnew.FromMM(0.25)
            c = v.GetPosition()
            ok = ok and all(shape.Collide(pcbnew.VECTOR2I(c.x + dx, c.y + dy), 0)
                            for dx, dy in ((-r, 0), (r, 0), (0, -r), (0, r)))
            if ok and paste_ok and ep_ok:
                qualified.add(v.m_Uuid.AsString())
        if not ok:
            issues.append(f'GAP-3: thermal via at {centre} must be 0.5/0.3 GND through-via, filled and capped, inside U401.11')
    return issues, dict(centres_mm=centres, local_centres_mm=VIPPO_LOCAL_CENTRES, qualified=len(qualified),
                        local_exposed_pad_mm=ep_box, local_paste_windows_mm=paste,
                        manufacturing_condition='resin-filled, copper-capped, planar VIPPO; physical fabrication unverified'), qualified


# R19-RTE-01 (gate note): route_check's pour_finger looks only at pieces longer than 3 mm, so a 1.693 mm^2 F.Cu GND
# fragment hanging off U1.19's pin tip (no via; its only contact the pad) passed. Every pour piece, any size, any layer,
# must hold a via of its own net (stitched to the net's other copper) or join two or more of its net's pads (carry
# current between them); a piece with no via and at most one pad is pour debris. A named POUR_DEBRIS entry (net, layer,
# pads, area mm^2, measured reason) admits one piece of exactly that geometry (area within 0.01 mm^2); unused fails.
# D-R20-03 (R20-RTE-02): U1.74's 0.282 mm^2 F.Cu GND piece is gone (board pad override ZONE_CONNECTION_NONE, as
# D-R19-05 for U1.19), so its entry is deleted; no pour debris is admitted.
POUR_DEBRIS = []


def pour_debris(board, named=None):
    """(issues, evidence): every zone fill piece holds a via of its net or touches two or more of its net's pads."""
    import pcbnew
    named = POUR_DEBRIS if named is None else named
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
    pads = [(f.GetReference(), p) for f in board.GetFootprints() for p in f.Pads()]
    issues, used, pieces, debris = [], set(), 0, []
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.GetNetname():
            continue
        net = z.GetNetname()
        for lid in z.GetLayerSet().CuStack():
            if not z.HasFilledPolysForLayer(lid):
                continue
            fill = z.GetFilledPolysList(lid)
            for i in range(fill.OutlineCount()):
                piece = fill.UnitSet(i)
                pieces += 1
                if any(v.GetNetname() == net and v.IsOnLayer(lid) and piece.Collide(v.GetEffectiveShape(lid), 0)
                       for v in vias):
                    continue
                touched = tuple(sorted({f'{ref}.{p.GetNumber()}' for ref, p in pads if p.GetNetname() == net
                                        and p.IsOnLayer(lid) and piece.Collide(p.GetEffectiveShape(lid), 0)}))
                if len(touched) >= 2:
                    continue
                area, layer = piece.Area() / 1e12, board.GetLayerName(lid)
                bb = piece.BBox()
                at = f'({pcbnew.ToMM(bb.GetCenter().x):.2f}, {pcbnew.ToMM(bb.GetCenter().y):.2f})'
                debris.append(dict(net=net, layer=layer, pads=list(touched), area_mm2=round(area, 3), at=at))
                hit = next((k for k, x in enumerate(named) if x[:3] == (net, layer, touched)
                            and abs(x[3] - area) <= 0.01), None)
                if hit is not None:
                    used.add(hit)
                    continue
                issues.append(f'pour debris: {net} fill {z.GetZoneName()} on {layer} has a {area:.3f} mm^2 piece at {at} '
                              f'with no via and ' + (f'only {touched[0]}' if touched else 'no pad') +
                              ' of its net (R19-RTE-01)')
    present = {(f'{ref}.{p.GetNumber()}', p.GetNetname()) for ref, p in pads}
    issues += [f'stale POUR_DEBRIS entry {x[:4]} ({x[4]})' for k, x in enumerate(named)
               if k not in used and all((pad, x[0]) in present for pad in x[2])]   # (judged on a board with its pads)
    return issues, dict(pieces=pieces, debris=debris)


def k_copper(ctx):
    """GAP-3's exact U401 thermal vias only; every other inherited copper and paste check is unchanged. R19-RTE-01: no
    pour debris (pour_debris)."""
    import check_r7 as r7
    import check_r8 as r8
    import check_r9 as r9
    import pcbnew
    thermal, evidence, allowed = thermal_vias(ctx.board)
    smd, paste = r7.vias_in_smd_pads, r8.via_paste

    def pad_exempt(p, v):
        return (v.m_Uuid.AsString() in allowed and p.GetParentFootprint().GetReference() == 'U401'
                and p.GetNumber() == '11' and p.GetNetname() == 'GND')

    def paste_exempt(name, cu, poly, v):
        return v.m_Uuid.AsString() in allowed and name == 'U401.paste' and cu == pcbnew.B_Cu

    with patched(r7, vias_in_smd_pads=lambda b: smd(b, exempt=pad_exempt)), \
            patched(r8, via_paste=lambda b: paste(b, exempt=paste_exempt)):
        issues, ev = r9.k_copper(ctx)
    debris, debris_ev = pour_debris(ctx.board)
    return issues + thermal + [f'K-copper: {i}' for i in debris], dict(ev, gap3=evidence, pour_pieces=debris_ev)


FILL_TOLERANCE = 0.01          # mm^2 symmetric difference per zone UUID/layer/net


def fill_freshness(path):
    """K-fill (R4-GATE-05): the saved zone fills are the board's current fills. A second copy of the board is loaded
    from `path`, refilled with ZONE_FILLER, and each zone's actual polygons compared. Returns (issues, evidence)."""
    import pcbnew

    def fills(b):
        out = {}
        for z in b.Zones():
            if z.GetIsRuleArea():
                continue
            for lay in z.GetLayerSet().Seq():
                out[(z.m_Uuid.AsString(), b.GetLayerName(lay), z.GetNetname())] = (
                    pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(lay)) if z.HasFilledPolysForLayer(lay)
                    else pcbnew.SHAPE_POLY_SET())
        return out
    board = pcbnew.LoadBoard(str(path))
    before = fills(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    after = fills(board)
    stale, differences = [], []
    for key in sorted(before.keys() | after.keys()):
        saved, refilled = before.get(key), after.get(key)
        difference = None
        if saved is not None and refilled is not None:
            left = pcbnew.SHAPE_POLY_SET(saved); left.BooleanSubtract(refilled)
            right = pcbnew.SHAPE_POLY_SET(refilled); right.BooleanSubtract(saved)
            difference = (left.Area() + right.Area()) / 1e12
            differences.append(difference)
        if difference is None or difference > FILL_TOLERANCE:
            stale.append(dict(uuid=key[0], layer=key[1], net=key[2],
                              saved_area_mm2=saved.Area() / 1e12 if saved is not None else None,
                              refilled_area_mm2=refilled.Area() / 1e12 if refilled is not None else None,
                              symmetric_difference_mm2=difference))
    return ([f'zone {item["uuid"]} ({item["net"] or "no net"}) on {item["layer"]}: saved fill geometry differs '
             f'from refill (symmetric difference {item["symmetric_difference_mm2"]} mm^2; '
             'refill the zones and save the board)' for item in stale],
            {'zones': len(before), 'stale': len(stale), 'tolerance_mm2': FILL_TOLERANCE,
             'comparison': 'symmetric_difference', 'maximum_difference_mm2': max(differences, default=0.0),
             'changed': stale})


def k_fill(ctx):
    if not ctx.board_path or not Path(ctx.board_path).is_file():
        return ['K-fill: no board file path to refill a copy from'], {}
    issues, ev = fill_freshness(ctx.board_path)
    return [f'K-fill: {i}' for i in issues], ev


def k_region(ctx):
    issues, ev = region_issues(ctx.board)
    return [f'K-region: {i}' for i in issues], ev


# K-plane (R18-RTE-01 / R18-PWR-01, D-R18-06): a power plane on an inner layer must fill as one piece; a residual
# same-net piece is acceptable only with >= PLANE_LINKS links, each an outer-layer copper path of tracks >= PLANE_LINK_W
# (plus pads and vias) from a via or plated pad landing in that piece to one landing in another piece. GND regions on
# In2 (CH1, Y1) are separate GND islands by design and stitched by vias, so GND is out of scope.
PLANE_LINKS = 2
PLANE_LINK_W = 0.5             # mm
PLANE_LAYERS = ('In1.Cu', 'In2.Cu')


def plane_pieces(board, layers=PLANE_LAYERS, skip=frozenset({'GND'})):
    """{(net, layer name): [SHAPE_POLY_SET of one piece, ...]} of every non-GND zone net's merged inner fill."""
    import pcbnew
    merged = {}
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.GetNetname() or z.GetNetname() in skip:
            continue
        for name in layers:
            lid = board.GetLayerID(name)
            if z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                merged.setdefault((z.GetNetname(), name), pcbnew.SHAPE_POLY_SET()).BooleanAdd(
                    z.GetFilledPolysList(lid))
    return {key: [ps.UnitSet(i) for i in range(ps.OutlineCount())] for key, ps in merged.items()}


def plane_links(board, net, pieces, width=PLANE_LINK_W, locate=None):
    """{piece index: number of its landing vias / plated pads whose outer-layer copper (tracks >= `width`, pads, vias)
    reaches a via or plated pad landing in another piece}. `locate(obj)` (R19-GATE-03) assigns each via / plated pad to
    a piece key instead (None: not a landing); the result is then keyed by those keys."""
    import pcbnew
    outer = (pcbnew.F_Cu, pcbnew.B_Cu)
    items, landing = [], {}
    for t in board.GetTracks():
        if t.GetNetname() != net:
            continue
        if t.GetClass() == 'PCB_VIA':
            items.append(('via', t, [(lid, t.GetEffectiveShape(lid)) for lid in outer]))
        elif t.GetLayer() in outer and pcbnew.ToMM(t.GetWidth()) >= width - EPS:
            items.append(('track', t, [(t.GetLayer(), t.GetEffectiveShape(t.GetLayer()))]))
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == net:
                items.append(('pad', p, [(lid, p.GetEffectiveShape(lid)) for lid in outer if p.IsOnLayer(lid)]))
    for k, (kind, obj, _) in enumerate(items):
        if kind == 'via' or (kind == 'pad' and obj.GetAttribute() == pcbnew.PAD_ATTRIB_PTH):
            if locate is not None:
                key = locate(obj)
                if key is not None:
                    landing[k] = key
                continue
            for i, piece in enumerate(pieces):
                if piece.Contains(obj.GetPosition()):
                    landing[k] = i
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a in range(len(items)):
        for b in range(a + 1, len(items)):
            if any(la == lb and pcbnew.SHAPE.Collide(sa, sb, 0) for la, sa in items[a][2] for lb, sb in items[b][2]):
                parent[find(a)] = find(b)
    reach = {}
    for k, i in landing.items():
        reach.setdefault(find(k), set()).add(i)
    keys = set(landing.values()) if locate is not None else range(len(pieces))
    return {i: sum(1 for k, j in landing.items() if j == i and len(reach[find(k)]) > 1) for i in keys}


# R19-GATE-03: K-plane counted fill pieces, so a fill joined through a neck thinner than one 0.5 mm link (seed b10b: the 3V3
# buck finger at 0.30 mm) passed. Each non-GND inner fill, unfractured (KiCad stores fills with zero-width slits to their
# holes, which a deflation would open as false necks), is deflated by PLANE_LINK_W / 2: a landing via or plated pad the
# deflation separates from the largest piece is a split piece and needs PLANE_LINKS outer links of >= PLANE_LINK_W.
# Necks narrower than PLANE_NECK_REPORT are reported. Calibrated on the R10 board (2026-10-31): only 3V3 In2 has
# necks under 1.0 mm, 0.549 mm (vias (18.8, 60.25), (19.05, 55.9), (22.6, 52.15), (23.0, 70.0), (23.1, 78.1) and
# (23.2, 68.6)), 0.589 mm ((9.2, 52.98)) and 0.706 mm ((19.5, 49.15)); PORT_4V8, PORT_5V3 and RAW_PROTECTED none.
# D-R26-02 / -04 moved two of those vias, (19.05, 55.9) -> (19.55, 55.825) and (9.2, 52.98) -> (9.2, 52.55); the neck
# widths are unchanged (0.549 / 0.549 / 0.589 / 0.706 mm).
PLANE_NECK_REPORT = 1.0         # mm


def plane_necks(board, links=PLANE_LINKS, width=PLANE_LINK_W, report=PLANE_NECK_REPORT, layers=PLANE_LAYERS,
                skip=frozenset({'GND'})):
    """(issues, evidence): R19-GATE-03 necks of the non-GND inner fills (see PLANE_NECK_REPORT)."""
    import pcbnew
    fills = {}
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.GetNetname() or z.GetNetname() in skip:
            continue
        for name in layers:
            lid = board.GetLayerID(name)
            if z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                fills.setdefault((z.GetNetname(), name), pcbnew.SHAPE_POLY_SET()).BooleanAdd(z.GetFilledPolysList(lid))
    issues, ev = [], {}
    for (net, layer), fill in sorted(fills.items()):
        fill.Unfracture()
        lands = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == net]
        lands += [p for f in board.GetFootprints() for p in f.Pads()
                  if p.GetNetname() == net and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
        lands = [o for o in lands if fill.Contains(o.GetPosition())]

        def where(o):
            p = o.GetPosition()
            label = 'via' if o.GetClass() == 'PCB_VIA' else f'{o.GetParentFootprint().GetReference()}.{o.GetNumber()}'
            return f'{label} ({pcbnew.ToMM(p.x):.3f}, {pcbnew.ToMM(p.y):.3f})'

        def split(d):
            """{landing UUID: deflated piece index, or ('alone', UUID)}, the largest piece's index."""
            c = pcbnew.SHAPE_POLY_SET(fill)
            c.Deflate(pcbnew.FromMM(d), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, pcbnew.FromMM(0.002))
            pieces = [c.UnitSet(i) for i in range(c.OutlineCount())]
            main = max(range(len(pieces)), key=lambda i: pieces[i].Area()) if pieces else None
            out = {}
            for o in lands:
                q, uid = o.GetPosition(), o.m_Uuid.AsString()
                hit = next((i for i, pc in enumerate(pieces) if pc.Contains(q)), None)
                if hit is None and pieces:
                    near = min(range(len(pieces)), key=lambda i: pieces[i].SquaredDistance(q))
                    hit = near if math.sqrt(pieces[near].SquaredDistance(q)) <= pcbnew.FromMM(d + 0.02) else None
                out[uid] = ('alone', uid) if hit is None else hit
            return out, main
        cut, main = split(width / 2)
        away = {uid: key for uid, key in cut.items() if key != main}
        if away:
            count = plane_links(board, net, None, width, locate=lambda o: away.get(o.m_Uuid.AsString(), 'main'))
            for key in sorted(set(away.values()), key=str):
                members = [where(o) for o in lands if away.get(o.m_Uuid.AsString()) == key]
                if count.get(key, 0) < links:
                    issues.append(f'K-plane: {net} on {layer}: {", ".join(members[:4])} join(s) the main fill only '
                                  f'through a neck under {width} mm and {count.get(key, 0)} link(s) of >= {width} mm '
                                  f'outer copper (minimum {links}; R19-GATE-03)')
        necks = []
        far, big = split(report / 2)
        groups = {}
        for o in lands:
            if far[o.m_Uuid.AsString()] != big:
                groups.setdefault(far[o.m_Uuid.AsString()], []).append(o)
        for members in groups.values():
            probe = members[0].m_Uuid.AsString()
            lo, hi = 0.0, report / 2
            for _ in range(11):
                mid = (lo + hi) / 2
                part, top = split(mid)
                lo, hi = (lo, mid) if part[probe] != top else (mid, hi)
            necks.append(dict(width_mm=round(2 * lo, 3), landings=[where(o) for o in members]))
        ev[f'{net} {layer}'] = sorted(necks, key=lambda n: n['width_mm'])
    return issues, dict(necks_under_mm=report, necks=ev)


def plane_issues(board, links=PLANE_LINKS):
    issues, ev = [], {}
    for (net, layer), pieces in sorted(plane_pieces(board).items()):
        areas = [round(p.Area() / 1e12, 2) for p in pieces]
        ev[f'{net} {layer}'] = areas
        if len(pieces) < 2:
            continue
        main = max(range(len(pieces)), key=lambda i: areas[i])
        count = plane_links(board, net, pieces)
        for i, area in enumerate(areas):
            if i != main and count[i] < links:
                bb = pieces[i].BBox()
                issues.append(f'K-plane: {net} on {layer} fills as {len(pieces)} pieces; the {area} mm^2 piece at '
                              f'({pcbnew_mm(bb.GetCenter().x):.2f}, {pcbnew_mm(bb.GetCenter().y):.2f}) has '
                              f'{count[i]} link(s) of >= {PLANE_LINK_W} mm outer copper (minimum {links})')
    return issues, dict(pieces_mm2=ev)


# D-R21-06 (R21-GATE-03): the panel-tab plan (docs/ORDERING.md 8.1: four 5 mm tabs). The In2 keep-out that D-R20-08
# drew under the west aft tab (m3_design/r10_route_ground.py TAB_KEEPOUTS) is pinned by name, layer, outline and its
# fill-only flags, and the non-GND In1 / In2 copper inside each tab's 3 mm band is held to its recorded area (mm^2):
# growth fails, and a smaller figure fails as stale until it is re-recorded. The east tabs stay over In2 RAW_PROTECTED
# (and PORT_5V3) until the owner chooses the east tab plan (D-R20-08).
TAB_KEEPOUTS_R10 = (('R20_TAB_KEEPOUT_WEST_AFT', ('In2.Cu',), ((-0.5, 12.5), (3.0, 12.5), (3.0, 17.5), (-0.5, 17.5))),)
TAB_BANDS_R10 = (
    ('west aft', (0.0, 12.5, 3.0, 17.5), {}),
    ('west forward', (0.0, 60.0, 3.0, 65.0), {}),
    ('east aft', (43.0, 6.75, 46.0, 11.75), {('In2.Cu', 'RAW_PROTECTED'): 7.497, ('In2.Cu', 'PORT_5V3'): 3.077}),
    ('east forward', (43.0, 63.75, 46.0, 68.75), {('In2.Cu', 'RAW_PROTECTED'): 12.244}),
)
TAB_BAND_TOL = 0.005           # mm^2


def tab_keepouts(board, pinned=TAB_KEEPOUTS_R10, bands=TAB_BANDS_R10, tol=TAB_BAND_TOL):
    """(issues, evidence): each pinned tab keep-out exactly as drawn, and the non-GND inner copper (fills, tracks, via
    and pad copper) inside each tab band at its recorded area."""
    import pcbnew
    issues, ev = [], dict(keepouts={}, bands={})
    for name, layers, outline in pinned:
        hits = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetZoneName() == name]
        if len(hits) != 1:
            issues.append(f'tab keep-out {name}: {len(hits)} rule areas on the board, 1 required (D-R20-08)')
            continue
        z = hits[0]
        lays = tuple(sorted(board.GetLayerName(lay) for lay in z.GetLayerSet().Seq()))
        o = z.Outline()
        pts = tuple((round(pcbnew.ToMM(o.CVertex(i).x), 4), round(pcbnew.ToMM(o.CVertex(i).y), 4))
                    for i in range(o.TotalVertices()))
        flags = (z.GetDoNotAllowZoneFills(), z.GetDoNotAllowTracks(), z.GetDoNotAllowVias(), z.GetDoNotAllowPads(),
                 z.GetDoNotAllowFootprints())
        ev['keepouts'][name] = dict(layers=lays, outline=pts, flags=flags)
        if lays != tuple(sorted(layers)):
            issues.append(f'tab keep-out {name} is on {list(lays)}, pinned {list(layers)}')
        if sorted(pts) != sorted(outline):
            issues.append(f'tab keep-out {name} outline {pts} is not the pinned {outline}')
        if flags != (True, False, False, False, False):
            issues.append(f'tab keep-out {name} flags (fills, tracks, vias, pads, footprints kept out) {flags}, pinned '
                          'fill-only')
    inner = [lay for lay in board.GetEnabledLayers().CuStack() if lay not in (pcbnew.F_Cu, pcbnew.B_Cu)]
    err = pcbnew.FromMM(0.001)
    copper = {}
    for lay in inner:
        for z in board.Zones():
            if not z.GetIsRuleArea() and z.IsOnLayer(lay) and z.HasFilledPolysForLayer(lay) and z.GetNetname() != 'GND':
                copper.setdefault((lay, z.GetNetname()), pcbnew.SHAPE_POLY_SET()).BooleanAdd(z.GetFilledPolysList(lay))
        for t in board.GetTracks():
            if t.IsOnLayer(lay) and t.GetNetname() != 'GND' and (t.GetClass() != 'PCB_VIA' or t.FlashLayer(lay)):
                ps = pcbnew.SHAPE_POLY_SET()
                t.TransformShapeToPolygon(ps, lay, 0, err, pcbnew.ERROR_INSIDE)
                copper.setdefault((lay, t.GetNetname()), pcbnew.SHAPE_POLY_SET()).BooleanAdd(ps)
        for f in board.GetFootprints():
            for p in f.Pads():
                if p.IsOnLayer(lay) and p.FlashLayer(lay) and p.GetNetname() != 'GND':
                    ps = pcbnew.SHAPE_POLY_SET()
                    p.TransformShapeToPolygon(ps, lay, 0, err, pcbnew.ERROR_INSIDE)
                    copper.setdefault((lay, p.GetNetname() or '(no net)'), pcbnew.SHAPE_POLY_SET()).BooleanAdd(ps)
    for band, (x0, y0, x1, y1), recorded in bands:
        box = pcbnew.SHAPE_POLY_SET()
        box.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            box.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        found = {}
        for (lay, net), ps in copper.items():
            x = pcbnew.SHAPE_POLY_SET(ps)
            x.BooleanIntersection(box)
            area = round(x.Area() / 1e12, 3)
            if area > 0:
                found[(board.GetLayerName(lay), net)] = area
        ev['bands'][band] = {f'{lay} {net}': a for (lay, net), a in sorted(found.items())}
        for key in sorted(set(found) | set(recorded)):
            got, want = found.get(key, 0.0), recorded.get(key, 0.0)
            if got > want + tol:
                issues.append(f'{key[1]} on {key[0]} under the {band} tab band ({x0}-{x1}, {y0}-{y1}) is {got:.3f} '
                              f'mm^2, recorded {want:.3f} (R21-GATE-03: no new power copper under a panel tab)')
            elif got < want - tol:
                issues.append(f'stale TAB_BANDS_R10 figure: {key[1]} on {key[0]} under the {band} tab band is '
                              f'{got:.3f} mm^2, recorded {want:.3f} (re-record it)')
    return issues, ev


def k_plane(ctx):
    issues, ev = plane_issues(ctx.board)
    necks, ev['necks'] = plane_necks(ctx.board)
    tabs, ev['tabs'] = tab_keepouts(ctx.board)                         # D-R21-06
    return issues + necks + [f'K-plane: {i}' for i in tabs], ev


# R19-GATE-01: board-instance overrides that change a stencil or mask aperture without touching the library file (DRC's
# library comparison does not look at them). Zone connection, thermal and clearance overrides stay with K-copper / LC-1.
LAND_OVERRIDES = (('paste margin', 'GetLocalSolderPasteMargin', 'mm'),
                  ('paste ratio', 'GetLocalSolderPasteMarginRatio', ''),
                  ('mask margin', 'GetLocalSolderMaskMargin', 'mm'))


def land_overrides(board, pretty):
    """(issues, pads compared): every placed footprint's paste / mask overrides and every pad's paste margin, paste
    ratio, mask margin and paste / mask layers (a flipped part mirrors them) equal its copy in `pretty`
    (pcbnew.FootprintLoad). A placed pad pairs with the library pad of its number at its footprint-local position
    (y mirrored back for a flipped part, within 2 um, then the same size): saved boards reorder pads."""
    import pcbnew
    from collections import defaultdict

    def shown(v, unit):
        return 'none' if v is None else (f'{pcbnew.ToMM(v):.3f} mm' if unit else f'{v:g}')

    def local(pad, flipped):
        r = pad.GetFPRelativePosition()
        return r.x, -r.y if flipped else r.y
    cache, issues, compared = {}, [], 0
    for f in sorted(board.GetFootprints(), key=lambda g: g.GetReference()):
        ref, name = f.GetReference(), f.GetFPID().GetLibItemName().wx_str()
        if name not in cache:
            cache[name] = pcbnew.FootprintLoad(str(pretty), name)
        lib = cache[name]
        if lib is None:
            issues.append(f'{ref}: no library copy of {name} to compare its paste / mask overrides with')
            continue
        for label, getter, unit in LAND_OVERRIDES:
            have, want = getattr(f, getter)(), getattr(lib, getter)()
            if have != want:
                issues.append(f'{ref}: footprint {label} {shown(have, unit)}, library {name} {shown(want, unit)}')
        lib_pads = defaultdict(list)
        for q in lib.Pads():
            lib_pads[q.GetNumber()].append(q)
        for p in f.Pads():
            number = p.GetNumber()
            x, y = local(p, f.IsFlipped())
            near = [q for q in lib_pads[number] if math.hypot(local(q, False)[0] - x, local(q, False)[1] - y) <= 2000]
            q = next((q for q in near if q.GetSize() == p.GetSize()), near[0] if near else None)
            label = f'{ref}.{number or "(unnumbered)"}'
            if q is None:
                issues.append(f'{label}: no pad of that number at its position in library {name}')
                continue
            compared += 1
            for what, getter, unit in LAND_OVERRIDES:
                have, want = getattr(p, getter)(), getattr(q, getter)()
                if have != want:
                    issues.append(f'{label}: pad {what} {shown(have, unit)}, library {shown(want, unit)}')
            for kind, front, back in (('paste', pcbnew.F_Paste, pcbnew.B_Paste), ('mask', pcbnew.F_Mask, pcbnew.B_Mask)):
                have = (p.IsOnLayer(back), p.IsOnLayer(front)) if f.IsFlipped() else (p.IsOnLayer(front), p.IsOnLayer(back))
                want = (q.IsOnLayer(front), q.IsOnLayer(back))
                if have != want:
                    issues.append(f'{label}: {kind} layers (front, back of the part) {have}, library {want}')
    return issues, compared


# D-R23-09 (R23-GATE-05): r10_parts' own footprints are pinned here too, by their generated files' SHA-256, so that a
# generator edit (for example Q120 / Q121's paste stripped) needs a reviewed re-pin; and the board's pasted pads are
# pinned per side (253 F.Paste / 375 B.Paste on 5516eeec, the bound package's flash counts).
GENERATED_SHA256 = {
    'M3_AONR21357_DFN3x3A_EP1': '98b34fd0b10c91fc0da1b4c3d45d92d8b8bb3ae4f6823ec7a751e82986fccc59',
    'M3_DB125_2P_BK': 'ca5722baf0962fcd555120c7360b958538408b0875eb3f59d970b7312f5c6967',
    'M3_DB125_2P_GN': '1898ccfb7f7cdd48402943955d673c8282f8dea6cadc967c855404ac23f650a7',
    # D-R26-01: pins 3 / 4 drop their unconnected inner rings (was 747446dd...)
    'M3_DB125_4P_GN': '5582eb2808a8e1e3bed547b5bef608854da161921ec61c847134f23e95edb78d',
    'M3_DB125_5P_GN': 'ca2aada63759dc14a4f130b89c3f264a28159c535bf0f4e5967a952782c07b5b',
    'M3_MA_8x10': '66db2b17c307081780c75c8a3c2b25c66e4720ef130c1c703e7d5f3182674993',
    'M3_MICROSD_MOLEX_472192001': 'ff60b0babf97df08f58030a70b4f929976b469ea4f131455be6c8d2cf310a97d',
    'M3_SRP5030TA': '33ab57ef2aecc64a129326274e1cce2abb16e5e27cdce55a2394a4fe12ffade0',
    'M3_TPS7A91_DSK10': '4d4f03f099a74f3a576cce028c3ff91cbe698e7bd22c2d573ca73d072321629d',
}
PASTE_TOTALS = {'F.Paste': 249, 'B.Paste': 381}     # D-R24-11: D402's two B.Paste apertures (D-R24-09: R402 / R403
#                                                      moved to B.Cu, 253 / 375 -> 249 / 379; D-R23-09)


def paste_totals(board, totals=None):
    """(issues, {layer: pads}): the board's pads with paste on each side against PASTE_TOTALS."""
    import pcbnew
    totals = PASTE_TOTALS if totals is None else totals
    count = {name: sum(1 for f in board.GetFootprints() for p in f.Pads() if p.GetLayerSet().Contains(board.GetLayerID(name)))
             for name in totals}
    return ([f'{name}: {n} pasted pads, pinned {totals[name]} (R23-GATE-05: a paste change needs a reviewed re-pin)'
             for name, n in count.items() if n != totals[name]], count)


def k_lands(ctx, pins=None, table=None, generated=None):
    """R18-GATE-09: the project library is the only footprint source and every footprint the board uses is pinned:
    generated by r10_parts (pinned there) or listed in FOOTPRINT_SHA256 with its library file's SHA-256. R19-GATE-01:
    no board instance changes a paste or mask aperture of its library copy (land_overrides)."""
    from r10_parts import FOOTPRINTS as GENERATED
    pins = FOOTPRINT_SHA256 if pins is None else pins
    table = FP_LIB_TABLE if table is None else table
    folder = Path(ctx.board_path).parent if ctx.board_path else ctx.folder
    if folder is None:
        return ['K-lands: the project folder is unknown (no board path)'], {}
    issues, used = [], {}
    libs = folder / 'fp-lib-table'
    found = [(lib.children('name')[0].items[1].atom, lib.children('uri')[0].items[1].atom)
             for lib in read(libs.read_text()).children('lib')] if libs.is_file() else None
    if found != table:
        issues.append(f'K-lands: fp-lib-table lists {found}; R10 uses only {table}')
    for f in ctx.board.GetFootprints():
        lib, name = f.GetFPID().GetLibNickname().wx_str(), f.GetFPID().GetLibItemName().wx_str()
        if lib != table[0][0]:
            issues.append(f'K-lands: {f.GetReference()} uses {lib}:{name}, not the project library {table[0][0]}')
            continue
        used.setdefault(name, []).append(f.GetReference())
    hashes = {}
    generated = GENERATED_SHA256 if generated is None else generated
    for name, refs in sorted(used.items()):
        if name in GENERATED:                                             # D-R23-09: pinned here as well
            path = folder / 'kilib/rocket.pretty' / f'{name}.kicad_mod'
            actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            if generated.get(name) is None:
                issues.append(f'K-lands: generated footprint {name} has no GENERATED_SHA256 pin (file SHA-256 {actual})')
            elif actual != generated[name]:
                issues.append(f'K-lands: generated footprint {name} file SHA-256 {actual} is not the pinned '
                              f'{generated[name]}: a generator change needs review, then a re-pin (R23-GATE-05)')
            continue
        path = folder / 'kilib/rocket.pretty' / f'{name}.kicad_mod'
        hashes[name] = actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        want = pins.get(name)
        refs = ', '.join(sorted(refs, key=lambda r: (re.sub(r'\d', '', r), int(re.sub(r'\D', '', r) or 0))))
        if want is None:
            issues.append(f'K-lands: {name} ({refs}) is neither generated by r10_parts nor pinned in FOOTPRINT_SHA256 '
                          f'(library file SHA-256 {actual})')
        elif actual != want:
            issues.append(f'K-lands: {name} ({refs}) library file SHA-256 {actual} is not the pinned {want}: a land '
                          'change needs review, then a re-pin in tools/check_r10.py')
    issues += [f'K-lands: stale FOOTPRINT_SHA256 entry {name} (no board footprint uses it)'
               for name in sorted(set(pins) - set(used))]
    issues += [f'K-lands: {name} is generated by r10_parts and pinned there; remove its FOOTPRINT_SHA256 entry'
               for name in sorted(set(pins) & set(GENERATED))]
    issues += [f'K-lands: stale GENERATED_SHA256 entry {name} (no board footprint uses it)'
               for name in sorted(set(generated) - set(used))]
    overrides, compared = land_overrides(ctx.board, folder / 'kilib/rocket.pretty')
    issues += [f'K-lands: {i} (R19-GATE-01: a stencil / mask change goes in the reviewed library land)' for i in overrides]
    pastes, counted = paste_totals(ctx.board)                         # D-R23-09
    issues += [f'K-lands: {i}' for i in pastes]
    return issues, dict(pinned=len(hashes), generated=sorted(set(used) & set(GENERATED)), footprints_used=len(used),
                        pads_compared_for_paste_mask=compared, pasted_pads=counted)


def sd_bypass(board):
    """Locality bounds are engineering layout constraints, not a measured card supply qualification."""
    import check_r7 as r7
    pads = r7.pads_by_ref(board)
    power = pads.get(('J430', '4'))
    issues, evidence = [], {}
    for ref, limit in (('C460', 3.), ('C461', 6.)):
        cap = pads.get((ref, '1'))
        distance = math.dist(tuple(power.GetPosition()), tuple(cap.GetPosition())) / 1e6 if power and cap else None
        evidence[ref] = dict(vdd_pad_distance_mm=distance, maximum_mm=limit)
        if distance is None or distance > limit + EPS:
            issues.append(f'microSD {ref}.1 requires <= {limit:g} mm pad distance to J430.4 (has {distance})')
    return issues, evidence


def retained_routing(ctx):
    """Unchanged camera / flash bypass and exposed-contact copper contracts (not pyro spacing: probe contact)."""
    import check_r7 as r7
    import pcbnew
    issues, camera = r7.camera_bypass(ctx.board)
    sd_issues, sd_evidence = sd_bypass(ctx.board)
    issues += sd_issues
    pads = r7.pads_by_ref(ctx.board)
    flash, bypass = pads.get(('U3', '8')), pads.get(('C29', '1'))
    evidence = {'camera_bypass': camera, 'microSD_bypass': sd_evidence}
    if flash is None or bypass is None:
        issues.append('flash local bypass U3.8/C29.1 missing')
    else:
        gap = math.dist(tuple(flash.GetPosition()), tuple(bypass.GetPosition())) / 1e6
        route = r7.direct_route(ctx.board, flash, bypass)
        evidence['flash'] = dict(pad_distance_mm=gap, direct_route_mm=route)
        if gap > 2 or route is None or route > 3:
            issues.append('C29 flash bypass requires <=2 mm pad distance and <=3 mm direct route')
    gate_pad = ctx.fps.get('TP122')
    if gate_pad is None or not gate_pad.IsFlipped():
        issues.append('TP122 must remain on B.Cu')
    return [f'K-retained: {i}' for i in issues], evidence


# ======================================================================================================================
def _r9(name):
    def run(c, s):
        import check_r9 as r9
        return getattr(r9, name)(c)
    return run


RULES = [
    ('S-1', 'single screw switch: RAW_ACT pyro bus, no J124', lambda c, s: s1(c)),
    ('S-2', 'pyro feed only through the load switch', lambda c, s: s2(c)),
    ('S-3', 'gate networks defined off', lambda c, s: s3(c)),
    ('S-4', 'required-fitted safety parts (R1-07), resistor / MLCC values decoded from the MPN (R19-GATE-02)',
     lambda c, s: s4(c)),
    ('S-5', 'J400 screw arming switch and protected EN contacts', lambda c, s: s5(c)),
    ('S-6', 'external ports apart from pyro / arming copper', lambda c, s: s6(c)),
    ('S-7', 'J122 five signal/reference terminal contacts (O3/O6)', lambda c, s: s7(c)),
    ('S-8', 'In1 / In2 copper >= 1.0 mm from pyro, load-switch gate and enable barrels (R3-SAF-01 / R18-SAF-01)', lambda c, s: s8(c)),
    ('S-9', 'fire/source copper >= 0.5 mm; BAT_IN >= 1.0 mm (AUD-6 / audit 2)', lambda c, s: s9(c)),
    ('K-contract', 'R10 netlist contract', lambda c, s: k_contract(c)),
    ('K-binding', 'saved record-only binding evidence matches native board', lambda c, s: k_binding(c)),
    ('K-loader', 'ROM-loader pins (AN2606 Rev70 Table135; R3-MCU-01/R17-MCU-02)', lambda c, s: k_loader(c)),
    ('K-actuators', 'check_actuators --profile r10', lambda c, s: k_actuators(c)),
    ('LC-1', 'local overrides respect the applicable floors', lambda c, s: lc1(c.board)),
    ('M-1', 'outline 46 mm wide, length <= 120 mm', lambda c, s: m1(c)),
    ('M-3', 'five supports at the P1 / P2 centres, former servo plug tie holes absent', lambda c, s: m3(c)),
    ('M-5', 'fit (profile r10)', lambda c, s: m5(c, s)),
    ('M-6', 'bottom keep-outs', lambda c, s: m6(c)),
    ('M-7', 'IMU and MEMS', lambda c, s: m7(c)),
    ('M-8', 'courtyards >= 2.5 mm from the rail-less short edges y = 0 / y = 90 (JLC assembly terms section 2.3, '
            'ORDERING 8.1), six recorded DFM queries (D-R24-15 / D-R24-20)', lambda c, s: m8(c)),
    ('P-11', 'terminal entry and owner-accepted 4.95 mm wire room', lambda c, s: p11(c)),
    ('F9-1', 'R10 reverse hot-plug model pass (OQ-2)', lambda c, s: f9(c)),
    ('F9-2', 'GAP-2 U9 output capacitor and Schottky local copper loops', lambda c, s: output_loop(c)),
    ('T-1', 'panel-tab windows (R10)', lambda c, s: t1(c)),
    ('K-legends', 'legends and ids, word centre margins, the silkscreen text allowlist (R19-GATE-06 / -07), '
                  'designator courtyards and Fab references (R20-MFG-02 / -03, R21-GATE-05)', lambda c, s: k_legends(c)),
    ('K-copper', 'copper hygiene, exact GAP-3 U401 VIPPO condition, no pour debris (R19-RTE-01)',
     lambda c, s: k_copper(c)),
    ('K-inner', 'In1 GND only, In2 power and GND only', lambda c, s: k_inner_signal(c)),
    ('K-reference', 'critical signal reference copper, no stale listed net (R19-REQ-10)', lambda c, s: k_reference(c)),
    ('K-region', 'critical B.Cu runs over one In2 plane region (R4-RTE-02)', lambda c, s: k_region(c)),
    ('K-plane', 'inner power fills one piece, else >= 2 links of >= 0.5 mm; necks under 0.5 mm count as splits '
                '(R18-RTE-01 / R19-GATE-03); the tab keep-out and tab-band copper (R21-GATE-03)', lambda c, s: k_plane(c)),
    ('K-fill', 'saved zone fills are current (refill a copy, R4-GATE-05)', lambda c, s: k_fill(c)),
    ('K-rules', 'm3.kicad_dru pinned, board design rules floor (R4-GATE-01), JLC hole table and PTH hole to inner copper '
                '(R21-GATE-02), JLC rings, hole sizes and NPTH to copper on the board (R22-REQUIREMENTS-02)',
     lambda c, s: k_rules(c)),
    ('K-lands', 'footprints from the project library, each generated or SHA-256 pinned (R18-GATE-09); placed paste / '
                'mask settings as the library (R19-GATE-01)', lambda c, s: k_lands(c)),
    ('K-width', 'BAT_IN / RAW_PROTECTED width floor (R8-GATE-04)', lambda c, s: k_width(c.board)),
    ('K-power', 'U9 IN / OUT, rail paths at their IPC-2152 width (R19-GATE-04 / -05), the doubled supply feeds and '
                'buck outputs (D-R19-09), Q124 fire return (R18-GATE-02 / -03), regulator FB / OV / EN / ILIM taps with '
                'no single via (R20-PWR-02 / R21-GATE-01)', lambda c, s: k_power(c)),
    ('K-ports', 'port ESD clamps on the wire side of the 1 k series resistor, <= 4.5 mm of track from the pin '
                '(R21-GATE-04)', lambda c, s: k_ports(c)),
    ('K-retained', 'flash/camera/microSD bypass, TP122', lambda c, s: retained_routing(c)),
]
STAGES = {'functional': {'S-1', 'S-2', 'S-3', 'S-4', 'S-5', 'S-6', 'S-7', 'K-contract', 'K-loader', 'K-actuators'}}
STAGES['placement'] = STAGES['functional'] | {'LC-1', 'M-1', 'M-3', 'M-5', 'M-6', 'M-7', 'M-8', 'P-11', 'F9-1', 'T-1',
                                              'K-legends', 'K-width'}
STAGES['full'] = {rid for rid, _, _ in RULES}


def selected_rules(only=None, stage='full'):
    """Validate explicit scope before loading context; an empty or unknown selection never passes."""
    if only is None:
        if stage not in STAGES:
            raise ValueError(f'unknown rule stage: {stage!r}')
        return STAGES[stage]
    selected = set(only)
    if not selected or not any(selected):
        raise ValueError('explicit rule selection is empty')
    unknown = selected - STAGES['full']
    if unknown:
        raise ValueError(f'unknown rule ids: {", ".join(repr(rid) for rid in sorted(unknown))}')
    return selected


def make_ctx(board, folder=None, board_path=None, fit=None, plate=None, seed=None, dru=None, text=None, bom=None,
             cpl=None):
    import check_r9 as r9
    import fit_check as fc

    class R10Ctx(r9.Ctx):
        def fit(self):
            if self.fit_report is None:
                self.fit_report = fc.check_board(self.board, self.folder or Path('.'), profile='r10')
            return self.fit_report
    ctx = R10Ctx(board, folder, board_path, fit, plate, seed, 0.0, dru)
    if text is None and board_path and Path(board_path).is_file():
        text = Path(board_path).read_text()
    ctx.text, ctx.bom, ctx.cpl, ctx.fit_given, ctx._reach = text, bom, cpl, fit is not None, None
    return ctx


def check_board(board, folder=None, board_path=None, fit=None, plate=None, seed=None, only=None, stage='full',
                board_sha=None, dru=None, text=None, bom=None, cpl=None):
    """Run the rules of `stage` (or `only`) on a loaded board; each rule that cannot run fails."""
    selected = selected_rules(only, stage)
    import route_check as rc
    ctx = make_ctx(board, folder, board_path, fit, plate, seed, dru, text, bom, cpl)
    previous = rc.PROFILE
    rc.set_profile('r10')
    out, flat = {}, []
    try:
        for rid, title, fn in RULES:
            if rid not in selected:
                continue
            try:
                issues, ev = fn(ctx, board_sha)
            except Exception as e:                       # a rule that cannot run fails, it never passes
                issues, ev = [f'{rid}: could not run: {type(e).__name__}: {e}'], {}
            out[rid] = dict(title=title, ok=not issues, issues=issues, evidence=ev)
            flat += [i if i.startswith(rid) else f'{rid}: {i}' for i in issues]
    finally:
        rc.set_profile(previous)
    return dict(profile='r10', stage=stage, complete=stage == 'full' and only is None, ok=not flat, rules=out,
                issues=flat, failing=[k for k, v in out.items() if not v['ok']])


def file_sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board', nargs='?', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--report', type=Path)
    ap.add_argument('--fit', type=Path, help='tools/fit_check.py --profile r10 --report of this board')
    ap.add_argument('--plate', type=Path, help='optional plate-model JSON, reported for information only')
    ap.add_argument('--seed', type=Path, help='accepted for check_r9\'s command shape; R10 has no rule H to seed')
    ap.add_argument('--only', help='comma-separated rule ids')
    ap.add_argument('--stage', choices=tuple(STAGES), default='full')
    ap.add_argument('--bom', type=Path, help='JLC BOM CSV to check for the required-fitted parts')
    ap.add_argument('--cpl', type=Path, help='JLC CPL CSV to check for the required-fitted parts')
    a = ap.parse_args()
    only = {rid.strip() for rid in a.only.split(',')} if a.only is not None else None
    try:
        selected_rules(only, a.stage)
    except ValueError as error:
        ap.error(str(error))
    import pcbnew
    import fit_check as fc
    bp = a.board.resolve()
    load = lambda p: json.loads(p.read_text()) if p else None      # noqa: E731

    def inputs():
        r = fc.input_hashes(bp)
        for p in (bp.with_suffix('.kicad_dru'), bp.with_suffix('.kicad_pro'), bp.with_suffix('.kicad_sch')):
            r[p.name] = file_sha(p)
        r[str(R10_BINDING_NOTE)] = file_sha(bp.parent / R10_BINDING_NOTE)
        return r
    before = inputs()
    sha = before[bp.name]
    fit = load(a.fit)
    if fit is not None and fit.get('board_sha256') != sha:
        print('FAIL the fit report is not bound to this board (board_sha256)')
        return 1
    plate = load(a.plate)
    report = check_board(pcbnew.LoadBoard(str(bp)), bp.parent, bp, fit=fit, plate=plate, seed=None,
                         only=only, stage=a.stage, board_sha=sha,
                         bom=a.bom, cpl=a.cpl)
    report['clearance_scope'] = 'J2/TP bare-contact clearance requires tools/check.sh DRC; this checker does not duplicate it'
    if plate is not None:
        report['optional_plate'] = dict(diagnostic_only=True, bound_to_board=plate.get('board_sha256') == sha,
                                        report=plate, physical_vibration_verified=False)
    if a.seed:
        report['seed_note'] = f'{a.seed} not read: R10 has no pyro rule H (r10_plan section 2 item 1)'
    if before != inputs():
        report['issues'].append('board, model, rules, schematic or binding evidence changed during check')
        report['ok'] = False
    tables = {'r10_pin_table': R10_PIN_TABLE,
              'masses': ROOT / 'm3_design/assembly_review/sources/r10_design/masses.json'}
    report.update(board_sha256=sha, inputs_sha256=before, checker_sha256=file_sha(__file__),
                  contract_tables_sha256={k: {'path': str(v.relative_to(ROOT)), 'sha256': file_sha(v)}
                                          for k, v in tables.items()})
    for rid, r in report['rules'].items():
        print(f"{rid:12s} {'OK  ' if r['ok'] else 'FAIL'} {r['title']}" + (f" ({len(r['issues'])})" if r['issues'] else ''))
    length = report['rules'].get('M-1', {}).get('evidence', {}).get('length_mm')
    if length is not None:
        print(f'board outline: {report["rules"]["M-1"]["evidence"]["width_mm"]:g} x {length:g} mm (P1: 46 mm wide, '
              f'<= {BOARD_MAX:g} mm long)')
    for i in report['issues']:
        print('FAIL', i)
    scope = a.stage if only is None else 'selected rules'
    print(f'R10 CAD contract ({scope}):', 'OK' if report['ok'] else f"FAIL ({len(report['issues'])} findings in "
          f"{len(report['failing'])} rules: {', '.join(report['failing'])})")
    if a.report:
        a.report.write_text(json.dumps(report, indent=1, default=str) + '\n')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
