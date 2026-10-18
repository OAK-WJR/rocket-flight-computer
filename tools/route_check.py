#!/usr/bin/env python3
"""Routing hygiene gate: the clean-routing rules of AGENTS.md §3 and the owner's acceptance list, on every track and
via of the board (the review pass-2 geometry scan, sources/r7_review/pass2_routing_geometry.md §2, made a gate).

usage: <KiCad python3> -I tools/route_check.py [board.kicad_pcb] [--report out.json] [--list]
exit 0 = no failing instance and no stale allowlist entry (see GATE below)

Copper is grouped per (layer, net). Track end points within 1 µm form a node. A node is "plain" when exactly two
track ends meet there and it holds no pad, via or T (another track's body); a chain is a run of segments through
plain nodes. Connectivity follows KiCad's anchor rule (two items join when an anchor of one, a track end or a via or
pad centre, lies in the other's copper on a layer both are on). Categories (an instance is one place on the board):

  §3 rule categories, gated on every net:
    off_angle             heading more than 0.1° off a multiple of 45°, or more than 2 µm lateral error
    staircase             a chain run A,B,A,B,... of >= 4 segments with >= 2 shorter than 1 mm; also such a run
                          followed through T, via (onto another layer) and pad nodes (fix pass 5: at='node')
    acute_angle           two branches at a node meeting at 0.5°-89.5°; at a pad or via only when the wedge
                          between the branches' inner edges opens outside that pad's or via's copper; every branch
                          pair at the node is tested, not only the sharpest (fix pass 5)
    pour_stub             a track end touching nothing but its own net's pour whose run (back to the first junction,
                          pad or via) lies inside that pour's fill for more than POUR_STUB (1.0 mm): copper the fill
                          already provides, a stub (fix pass 5; a whole such run whose removal changes nothing is
                          dead_copper)
    fold_back             two branches at a node at < 0.5° (one doubles back over the other); at a pad or via only
                          when the shorter branch leaves that copper
    dead_copper           a stub: track copper or a via on no path between two terminals of its net (pads, and each
                          same-net pour fill island as one terminal; a run that only loops back on itself counts), so
                          it catches a dangling end and the dead branch a closed micro-loop hides from KiCad's
                          track_dangling, a run whose only contacts are one pour island (copper floating in the pour),
                          and a stub ending in a pour: a run from a track end that touches nothing but its own pour
                          back to the first junction, pad or via, whose removal leaves the net's pad groups (pours
                          joining) as they are (the pour already makes the joint it duplicates)
    dangling_via          a via with same-net copper on fewer than two layers
    critical_via_no_gnd   a via carrying a critical signal net's copper on >= 2 layers (its tracks, or a same-net pad
                          the via sits in: a layer change into a test pad counts, fix pass 5) with no GND via centre
                          within 1.5 mm (critical signal nets: RF, pyro/arm, HSE, USB data, SPI/QSPI/IMU_CS/radio
                          SPI, the other RADIO_*/GNSS_* nets)
  hygiene categories, gated on critical nets (the signal nets above and the power rails, GND included):
    micro_segment         a segment shorter than 50 µm (zero length included)
    short_segment         a segment from 50 µm up to max(its own width, 0.2 mm) long in open routing (not wholly
                          inside one same-net pad or via): a corner fattened by a sliver of track, not a run
    tiny_jog              a chain run A,B,A whose middle segment is < 0.5 mm or offsets the line by < 0.25 mm; every
                          A,B,A triple inside a longer alternating run (a staircase or an extra-bend run) is tested too;
                          fix pass 5: also where the middle segment S ends at a T, a via or a pad: a branch P arriving
                          at one end of S and a branch Q leaving the other end on the same heading A, S turning
                          45 or 90 deg off it (across a via P or Q may be on another layer; S wholly inside one pad or
                          via is the pad's or via's copper, not a jog; at='T' / 'via' / 'pad'); fix pass 6: also a
                          chain run P, M1..Mk (k >= 2), Q with Q back on P's heading and every middle segment off it
                          (an A,B,C,A knee), whose middle is < 0.5 mm in all or whose Q runs < 0.25 mm off P's line
                          (compound=k)
    via_overlap           two same-net vias whose copper rings overlap (centres closer than the sum of the radii):
                          overlapping copper (fix pass 5)
    collinear_unmerged    a plain node at 180° between two segments of the same width
    duplicate_segment     two segments with the same end points
    collinear_overlap     two collinear segments (centre lines within 1 µm) overlapping by more than 1 µm
    side_by_side_overlap  two parallel segments whose copper overlaps or leaves a same-net slit under 0.1 mm, along
                          more than half a track width
    crossing_without_node two segments crossing in both interiors
    overlap_only_joint    a track end that reaches same-net copper only through track width (not a node, pad, via
                          or another track's centre line)
    via_offcentre_joint   a track end inside a via's copper, more than 1 µm off its centre, where no track on that
                          layer reaches the via centre (KiCad DRC's track_not_centered_on_via)
    neck_down             a width change inside one conductor: two segments of different widths meeting at a plain
                          node, unless the narrower one runs straight on into a pad whose copper is within 1 mm of the
                          node (a pad-entry neck); a branch at a T, a via or a pad may be narrower than its trunk
    track_loop            a closed loop of tracks and vias on a net without a pour (two routes between the same
                          points: duplicate copper); one instance per independent loop
    detour                a net without a pour whose track copper is longer than DETOUR_MAX (1.6) x the octilinear
                          minimum spanning tree of its pad centres and more than DETOUR_SLACK (2 mm) longer than it
                          (for a two-pad net: the copper path against the octilinear pad-to-pad distance)
    extra_vias            such a net with more layer-changing vias (tracks on two or more layers) than it needs plus
                          VIA_SLACK (2: one crossing, under other copper and back): it needs none when all its pads
                          share a copper layer, one otherwise
                          (each forced exception of either is an allowlist entry with its measured reason)
    chain_detour          fix pass 6, nets with a pour (which the two net-level tests above cannot judge): a chain (a run
                          between two junctions: pads, vias, T nodes or ends) longer than CHAIN_DETOUR_MAX (1.25) x the
                          octilinear distance of its ends and more than CHAIN_DETOUR_SLACK (0.5 mm) longer than it
    pour_net_hop          fix pass 6, nets with a pour: two or more pure layer-change vias in series on one path (a via
                          joining exactly two of the net's track ends, on two layers, at its centre, with no pad, no
                          other track and no fill of its own pour on any layer): a hop under other copper and back, or
                          across two layers, between two junctions
    via_on_track          fix pass 7: a via joined to a same-net track by overlap only: the track's centre line passes
                          through the via's centre (the via sits on its body) with neither track end in the via, or the
                          track's copper overlaps the via's on a layer where no track of the net ends at the via's
                          centre (where the via also lies in its own net's fill on that layer: via_on_track_in_fill,
                          information)
  removable local bumps, gated on critical nets (fix pass 7, bump_audit; needs the board-specific clearance model):
    local_bump            a window of 2-8 segments inside a run (topology chains, poured nets included) that turns back
                          (longer than the Manhattan distance of its ends by > 0.05 mm) and exceeds the octilinear
                          distance of its ends by > 0.3 mm and 1.15 x, for which a 1-3 segment redraw at least 0.15 mm
                          shorter, with other headings than the window's own, passes RedrawCheck (strict: every other
                          net's copper, keep-outs, holes, the true board edge, no other net's power-pour fill, not
                          between a two-pad part's pads, no same-net copper but the branches at its ends, on B.Cu /
                          In2 no nearer a critical signal track on the paired layer than the window, whose reference
                          that pour is) and path_defects with those branches (--bumps-all: the other nets too,
                          local_bump_review, information)
  pour categories, gated on every net (zone fills as saved; the board must be filled):
    pour_sliver           a piece of a net's pour fill narrower than 0.25 mm (it vanishes when the fill is opened by
                          0.125 mm) and longer than 3 mm (bounding-box diagonal): a sliver between two tracks or pads
    pour_finger           a GND pour finger (a fill piece narrower than 0.5 mm, too narrow to hold a via: the fill
                          opened by 0.25 mm, and longer than 3 mm) holding a point more than 4 mm of copper from the
                          nearest GND via or plated GND hole; the ring (outline + PAD_RING 0.75 mm) of a GND pad with a
                          thermal or solid pour connection is that pad's relief (gap and spokes), not a finger: it is
                          left out before the length and reach are measured
                          (through-copper raster distance on that layer: a finger joined at one end only, or a long
                          bridge, that no via stitches)
    pad_pour_cut          a pad joined to a same-net pour (its zone connection, its own or the zone's, is thermal or
                          solid), inside that pour's outline on that layer, that the fill touches when the board is
                          refilled without its pour-trim keep-outs (rule areas R7_POUR_TRIM_n) but not as saved: a
                          trim took the pad's last pour contact (its spokes)
  information only (counted, never gated):
    power_via_no_gnd      a via carrying a power rail's tracks on >= 2 layers with no GND via centre within 1.5 mm
                          (AGENTS.md §3 sets the GND-via rule for critical signal nets; power layer changes are shown)
  (hygiene categories are counted on every net; on a non-critical net they are information for the review. --routes
  prints every pad-to-pad connection of every net without a pour: copper length, octilinear distance, ratio, vias.)
    width_change_junction segments of different widths at a T or a via (a narrower branch leaving a trunk)
    pad_end_offcentre     a track end more than 0.1 mm off the centre of a pad no larger than 2 mm
    segment_inside_pad    a segment >= 0.2 mm lying wholly inside the pad it ends in
    passes_through_pad    a segment crossing a same-net pad without ending in it
    extra_bends           a chain run A,B,A,B,... of >= 4 segments, fewer than 2 under 1 mm
    u_turn                a chain whose cumulative heading change reaches 180°
    short_layer_hop       a chain under 3 mm between two vias of a non-GND net

GATE: an instance fails unless ALLOWLIST below names it, when its category is a §3 rule or pour category, or when it
is a hygiene category on a critical net. An allowlist entry that matches nothing also fails (stale exceptions are
removed, not kept). A critical_via_no_gnd entry also fails when its reason has gone out of date: the project's GND via
search (m3_design/r7_hygiene.gnd_spots: GndFit, 0.6 and 0.5 mm vias, 0.025 mm grid) finds a legal spot within 1.5 mm of
the layer change on the board checked (nognd_audit). Fix pass 5 re-measures the other reasons too: a detour /
extra_vias entry (allowlist or LEFTOVERS) carries the measured route length and via count it was written for, and fails
when the board's route differs (measured_check: its search result and reason describe that route; fix pass 6: a
chain_detour / pour_net_hop entry likewise carries its run's length and via count); a tiny_jog / staircase /
short_segment / chain_detour entry fails when a redraw of its window (its segments plus one plain-joined neighbour each
side) by any 1-3 segment octilinear polyline clears every other net's copper (r7_hygiene.Clearance), the keep-outs and
the edge without itself making an acute turn, short segment, tiny jog or staircase with the branches at its ends
(alt_audit; pads and vias stay put, so a reason resting on moving them is still a review item; for a chain_detour the
redraw must also end the detour and, fix pass 7, not keep the window's own headings: that only pulls the same drawing
closer to its obstacle). Geometry only: no
electrical behaviour is checked here (DRC and tools/dc_solve.py do that). LEFTOVERS (below the allowlist) lists the
non-critical hygiene instances that are counted, not gated, each with its measured reason (checked: every entry must
still match an instance, and every non-critical instance of a hygiene category must have an entry).
"""
import argparse
from array import array
import heapq
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pcbnew

NM = 1e-6
TOL = 1000                       # nm: end points within 1 µm are one node
MICRO = 0.05                     # mm
ANG_TOL = 0.5                    # deg
OFF_DEG, OFF_LAT = 0.1, 0.002    # off-angle limits: degrees, mm lateral
SLIT = 0.1                       # mm: same-net slit narrower than this counts as side-by-side overlap
GND_REACH = 1.5                  # mm, centre to centre (M3_R5 criterion)
SHORT = 0.2                      # mm: short_segment below max(width, SHORT)
DETOUR_MAX = 1.6                 # copper length / octilinear pad-to-pad distance
DETOUR_SLACK = 2.0               # mm: and longer than the octilinear distance by more than this
VIA_SLACK = 2                    # vias beyond the layer change the pads force: one crossing (under and back)
SLIVER_W, SLIVER_L = 0.25, 3.0   # mm: pour_sliver narrower than / longer than
FINGER_W, FINGER_L = 0.5, 3.0    # mm: pour_finger narrower than / longer than
FINGER_REACH = 4.0               # mm of copper to the nearest GND via or plated GND hole
PAD_RING = 0.75                  # mm round a pad joined to its pour: its thermal gap (0.25-0.5) and spokes, not a finger
RASTER = 0.05                    # mm: through-copper distance raster
CU4 = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)

CLASSES = [
    ('rf', r'^(GNSS_RF_ANT|GNSS_RF_IN|RADIO_RF_ANT|RADIO_RF)$'),
    ('pyro', r'^(PYRO|ARM)'),
    ('crystal', r'^HSE_'),
    ('usb', r'^USB_D[PM]$'),
    ('spi', r'^(QSPI_|SPI1_|IMU_CS$|RADIO_(SCK|MOSI|MISO|NSS))'),
    ('rfif', r'^(RADIO_|GNSS_)'),
    ('power', r'^(3V3|3V3A|3V3_GNSS|3V3_RADIO|VLOGIC|VBUS|USB_LIMITED|BAT_IN|BAT_DAMP|RAW_PROTECTED|RAW_ACT|'
              r'CAM_5V|CAM_INPUT_LIMITED|CAM_IO_3V3|SW_NODE|CAM_SW|BST|CAM_BST|VCAP1|VCAP2|ACT_FET_S|GND)$'),
    ('actuator', r'^(ACT_|SERVO)'),
]
SIGNAL_CRITICAL = {'rf', 'pyro', 'crystal', 'usb', 'spi', 'rfif'}
CRITICAL = SIGNAL_CRITICAL | {'power'}
RULE = ('off_angle', 'staircase', 'acute_angle', 'fold_back', 'dead_copper', 'pour_stub', 'dangling_via',
        'critical_via_no_gnd')
HYGIENE = ('micro_segment', 'short_segment', 'tiny_jog', 'collinear_unmerged', 'duplicate_segment',
           'collinear_overlap', 'side_by_side_overlap', 'crossing_without_node', 'overlap_only_joint',
           'via_offcentre_joint', 'neck_down', 'track_loop', 'via_overlap', 'detour', 'extra_vias', 'chain_detour',
           'pour_net_hop', 'via_on_track')
POUR_STUB = 1.0                  # mm: a pour-only track end's run inside its own fill longer than this is a stub
CHAIN_DETOUR_MAX = 1.25          # poured nets: a run between two junctions longer than this x the octilinear distance
CHAIN_DETOUR_SLACK = 0.5         # mm: and longer than it by more than this (the pass-2 review's chain-detour measure)
POUR = ('pour_sliver', 'pour_finger', 'pad_pour_cut')
INFO = ('width_change_junction', 'pad_end_offcentre', 'segment_inside_pad', 'passes_through_pad', 'extra_bends',
        'u_turn', 'short_layer_hop', 'power_via_no_gnd', 'via_on_track_in_fill', 'local_bump_review')
REMOVABLE = ('local_bump',)      # fix pass 7: from the redraw search (bump_audit), gated on critical nets

# Justified exceptions: (category, net, layer ('via' for via categories, 'net' for detour / extra_vias), (x, y) mm,
# reason). An entry matches an instance of that category and net within 0.02 mm of (x, y). Every entry needs a measured
# reason, and an entry that no longer matches fails the gate (a critical_via_no_gnd entry also fails when nognd_audit
# finds a legal GND via spot for it). M3-ASSY-R7 (sources/r7_review/fix3_F4_handoff.md, fix4_F5_handoff.md):
# "raster search" = scratch A* over F/B/In2 at 0.05 mm with the net's copper removed, every clearance of the board
# (m3.kicad_dru incl. the pyro rules, bare test pads 1.0 mm, Tag-Connect 0.508 mm), the power pours kept whole and the
# crystal kept clear; it does not know the RF strip's fence openings, its GND-only In2 or the module keep-outs.
_BAND = ('radio band fan-in step out of the via rows: the band vias sit in two columns (x 9.4 / 10.0) on 0.5 mm rows '
         'and the F.Cu lanes run at 0.4 mm pitch (fixed by RADIO_DIO1\'s lane at y 27.2 and BAT_SW_RETURN 0.175 mm south of '
         'RADIO_NSS\'s lane), so a lane leaves its via 0.2 mm (BUSY: row 28.2, lane 28.0) or 0.3 mm (MISO_MCU: row 28.7, lane '
         '28.4) off its row: a 45 deg step of 0.2 / 0.3 mm offset is a tiny jog at any length (the class is offset < 0.25 '
         'mm or a middle < 0.5 mm: 0.3 mm gives 0.424 mm). The step cannot sit before the 10.0 column (a 9.4-column lane '
         'on its new row passes the 10.0-column vias 0.075 mm apart; BUSY at y 28.0 at x 10.0 overlaps RADIO_NRST\'s via '
         '(10.0, 27.7) by 0.025 mm), nor be avoided without re-spacing the via columns or rows (the U1-side columns, '
         'RADIO_DIO1 and BAT_SW_RETURN with them: a re-layout of the interface band). With every lane on its via row, the '
         'binding obstacles are D9.1 / D9.2\'s pads (top edge y 30.3: RADIO_NSS\'s lane at y 30.2 would pass them at '
         '0.025 mm) and the GND via (19.71, 30.51), which that lane would overlap (pass 6, P6-ROUTING_GEOMETRY-03(e)). '
         'alt_audit re-measures it on every run. '
         'Fix pass 5 removed the two band staircases (east chamfers lengthened to 1.004 mm; RG-11)')
_NOGND = ('no legal GND via spot within 1.5 mm on the final board: nognd_audit (below, gated) runs '
          'm3_design/r7_hygiene.gnd_spots there on every check (GndFit: r7_route.ViaCheck with board rules +0.02 mm '
          'and no via within 0.15 mm of a GND solder pad, bare test pads 1.02 mm, Tag-Connect 0.528 mm, Pyro D 0.52 mm, '
          'the 7.7 A corridors; 0.6 and 0.5 mm vias; 0.025 mm grid) and finds none; sliding the signal via along its '
          'tracks\' axis by up to 0.6 mm opens none either (fix pass 4, fx4/snip/slide.py)')
_IFACE = ('R7 interface topology (M3_R7 "Interface": west escape to the left-edge B.Cu corridor over In2 GND, the F.Cu '
          'band forward of the strip, lanes between the modules; the strip admits signals only through its fence '
          'openings and holds no In2 signal copper, F10 / check_r7)')
_LIMITER = ('antenna-bias limiter on B.Cu under U30 (M3_R7 "Limiter"): U30.13 / U30.14 are F.Cu pads on the module\'s '
            'aft row and only GND may cross F.Cu / In1 under the module (U30 keep-out, u-blox IM 4.4), so the net leaves '
            '1.9 mm aft to a via outside the module and runs back under it on B.Cu')
_POUR6 = ('fix pass 6 (P6-DOCS-01), a net with a pour: ')
ALLOWLIST = [
    ('tiny_jog', 'RADIO_BUSY', 'F.Cu', (9.4, 28.2), _BAND + ' (0.283 mm step)'),
    ('tiny_jog', 'RADIO_MISO_MCU', 'F.Cu', (10.0, 28.7), _BAND + ' (0.424 mm step)'),
    ('critical_via_no_gnd', 'RADIO_RXEN', 'via', (23.8, 39.45), _NOGND + '; nearest GND via 2.23 mm'),
    ('critical_via_no_gnd', 'RADIO_NRST', 'via', (9.3, 50.0), _NOGND + ' (left-edge corridor); nearest 3.18 mm'),
    ('critical_via_no_gnd', 'RADIO_BUSY', 'via', (9.4, 28.2), _NOGND + ' (band via columns); nearest 1.65 mm'),
    ('critical_via_no_gnd', 'RADIO_BUSY', 'via', (10.0, 49.5), _NOGND + ' (left-edge corridor); nearest 2.60 mm'),
    ('critical_via_no_gnd', 'RADIO_MOSI', 'via', (9.4, 29.2), _NOGND + ' (band via columns); nearest 1.65 mm'),
    ('critical_via_no_gnd', 'RADIO_DIO1', 'via', (10.0, 50.5), _NOGND + ' (left-edge corridor); nearest 3.57 mm'),
    ('critical_via_no_gnd', 'RADIO_MISO_MCU', 'via', (10.0, 28.7), _NOGND + ' (band via columns); nearest 2.11 mm'),
    ('critical_via_no_gnd', 'RADIO_MOSI_MCU', 'via', (9.4, 48.5), _NOGND + ' (left-edge corridor); nearest 1.71 mm'),
    ('critical_via_no_gnd', 'PYRO1_GATE', 'via', (20.45, 92.4),
     'the via sits in TP122\'s 1.5 mm bare test pad (B.Cu), the gate drive\'s test point: a GND via within 1.5 mm of its '
     'centre would come within 0.45 mm of the pad edge, against the 1.0 mm a bare test pad keeps from foreign copper '
     '(check_r7; GndFit 1.02 mm), so nognd_audit finds no spot (fix pass 5: the layer change into a pad is now counted). '
     'The layer change carries no through current: TP122 is a terminal (probe point), the gate is driven on F.Cu; '
     'nearest GND via 2.93 mm'),
    ('detour', 'GNSS_RESET_N', 'net', (14.3, 54.5),
     _IFACE + ': 59.3 mm / 2 vias; the raster search finds 39.3 mm only with a 28.7 mm In2 run through the 3V3 plane '
     'and an F.Cu run crossing the strip fence at x 14.8, outside its openings'),
    ('detour', 'RADIO_DIO1', 'net', (14.3, 50.5),
     _IFACE + ': 69.1 mm / 4 vias; the raster search finds 48.0 mm / 2 vias only with a 39.8 mm In2 run ending inside '
     'the strip (In2 carries only GND there)'),
    ('extra_vias', 'RADIO_DIO1', 'net', (14.3, 50.5), _IFACE + ': 4 vias, as its detour entry'),
    ('detour', 'RADIO_NRST', 'net', (37.0, 14.0),
     _IFACE + ' (and R311 beside U31): 85.4 mm / 4 vias; the raster search U1.56 -> U31.3 finds 51.3 mm only with a '
     '32.1 mm In2 run into the strip'),
    ('extra_vias', 'RADIO_NRST', 'net', (37.0, 14.0), _IFACE + ': 4 vias, as its detour entry'),
    ('extra_vias', 'RADIO_NSS', 'net', (24.2, 20.39),
     _IFACE + ': 58.4 mm / 4 vias; the raster search U1.51 -> U31.14 finds 3 vias only with a 25.2 mm In2 run ending '
     'inside the strip'),
    ('extra_vias', 'RADIO_RXEN', 'net', (25.6, 7.43),
     'fix-pass-2 RXEN route (F.Cu lane x 20.6 between the modules, R312 at U31): 51.9 mm / 4 vias; the raster search '
     'U1.45 -> U31.10 finds 2 vias only with an 18.2 mm In2 run straight under the 3V3 buck (U2, C7, L1: x 19.6-20.7, '
     'y 27-44) through the 3V3 plane'),
    ('detour', 'RADIO_TXEN', 'net', (31.13, 18.95),
     'U31.19 -> U31.9 are on opposite sides of the module and only GND may cross its pad field on any layer (EBYTE '
     'manual 4.1; U31_KEEPOUT, B.Cu and In2 under the whole body), so TXEN runs round the module\'s west side on B.Cu '
     '(M3_R7 exceptions): 25.2 mm / 2 vias; the raster search\'s 12.2 mm path crosses the keep-out'),
    ('detour', 'GNSS_LNA_EN', 'net', (13.0, 13.3), _LIMITER + ': 7.45 mm for a 3.72 mm pad tree'),
    ('detour', 'GNSS_VCC_RF', 'net', (9.7, 12.25), _LIMITER + ': 6.2 mm for a 2.61 mm pad tree'),
    ('extra_vias', 'PYRO1_CONT', 'net', (24.6, 87.2),
     'net copper 53.33 mm (the rerouted chain R168.1 -> R129.2 47.53 mm): fix pass 4 plane-preserving route '
     '(r7_polish.pyro1_cont; fix pass 5 drew its F.Cu run S/SE/S): R168.1 on B.Cu at U1, the divider on F.Cu in the pyro '
     'block, SWCLK/SWDIO and the IMU between; the raster search with every power pour on every layer kept whole '
     '(3V3/3V3A included), 1.0 mm to PYRO1_GATE_N and every pyro rule finds no route with fewer than 6 vias (fx4/rt/pc8, '
     'via cost 15); the 4-via route of fix pass 3 cut the In2 3V3 island under U1/U4 (P4-REGRESSION-01); each layer '
     'change has a GND via within 1.5 mm'),
    ('extra_vias', 'ARM1_SENSE', 'net', (19.2, 92.4),
     '63.7 mm / 4 vias: R170.1 on B.Cu at U1, the divider (R133, R180, R175, C129) on F.Cu in the pyro block; the raster '
     'search R170.1 -> R133.1 (every pyro rule) finds no route with fewer than 4 vias (51.8 mm / 4)'),
    ('extra_vias', 'QSPI_IO2', 'net', (29.4, 59.5),
     '33.3 mm / 3 vias: U1.1 (U1\'s right column) to U3.3 (the QSPI flash north of U1) crosses U1\'s right-side escapes '
     'and the QSPI fan; the raster search finds 31.9 mm / 3 vias at best'),
    ('detour', 'VCAP1', 'net', (18.2, 45.9),
     '6.71 mm / 2 vias for 1.37 mm: C19.1 sits on B.Cu under U1 between its escape vias; the raster search finds '
     'nothing shorter than 5.81 mm / 2 vias (inherited R6; a shorter loop needs C19 moved)'),
    ('detour', 'VCAP2', 'net', (16.0, 60.8),
     '12.67 mm / 1 via for 3.0 mm: U1.73 escapes west and C20.1 sits on B.Cu under U1\'s SW corner; the direct via '
     'spots collide with C17, 3V3, USB_DP\'s via, the SWD lines and TP85 (pass-3 fitprobe) and the raster search '
     'finds the same west loop at 10.75 mm / 1 via (inherited R6; needs C20 moved next to U1.73, '
     'P3-ROUTING_QUALITY-05)'),
    ('detour', 'VBUS', 'net', (6.8, 76.3),
     '8 pads: J3\'s two VBUS contact groups (F.Cu, 4.8 mm apart) and C83 on F.Cu, C28, D4, R9 and U10 on B.Cu: a '
     '42.5 mm tree joining both contacts through C28 and the ESD clamp D4 (USB-C input, inherited R6)'),
    ('extra_vias', 'VBUS', 'net', (6.8, 76.3), 'as its detour entry: 6 vias for F/B pads that interleave'),
    ('extra_vias', 'RAW_PROTECTED', 'net', (35.7, 85.675),
     '12 pads, 3 on F.Cu (U9.6, C82.1, D9.1) and 9 on B.Cu from y 27 to y 104 (U11, C97, R92, TP70, TP81, U7, C71, '
     'R122): a distribution tree whose F and B pads interleave, 7 vias for 143.5 mm (inherited R6 topology)'),
    # fix pass 6 (P6-DOCS-01): poured nets' chain detours and series layer hops, each with its run's measured length
    # (measured_check) and, for a chain detour, alt_audit's gated search for a 1-3 segment redraw (none clean)
    ('chain_detour', '3V3', 'B.Cu', (36.94, 52.65),
     _POUR6 + 'C7 (U12 / C100): 3V3 from the via (36.94, 52.65) round the south end of C11 (B.Cu, 39.4-40.8, '
     '53.9-57.3: C11.1 3V3A, C11.2 GND) and back up into C100.1, 14.37 mm for 5.16 (fix pass 7: 16.32, the two local '
     'bumps at its ends redrawn, P7-ROUTING-01): the north side is closed by 3V3A\'s B.Cu run x 40.1 (y 51.9-54.6), '
     'which ends in C11.1, so both octilinear two-segment routes cross it; a run between C11\'s two pads (0.65 mm gap) '
     'is not taken (bump_audit strict); the local-bump search finds no other shorter window (inherited R6; a shorter '
     'feed needs C100 or C11 moved, or C100.1 its own via into 3V3_In2)', dict(path_mm=14.368)),
    ('chain_detour', 'GND', 'F.Cu', (14.3, 59.0),
     _POUR6 + 'U1.74 (VSS) to its GND via (11.3, 59.3), 6.62 mm for 3.12, round 3V3\'s F.Cu run (12.6-14.3, y 59.5) and '
     'via (12.6, 59.5), which both two-segment routes cross (inherited R6)', dict(path_mm=6.621)),
    ('chain_detour', 'GND', 'F.Cu', (16.35, 45.95),
     _POUR6 + 'U1.49 (VSS) to the GND via (16.35, 43.55) 2.4 mm straight above it: the straight run passes the 3V3 via '
     '(15.85, 44.25) at 0.075 mm (rule 0.15), so the run goes round it (6.56 mm; inherited R6)', dict(path_mm=6.556)),
    ('chain_detour', 'GND', 'F.Cu', (27.65, 29.85),
     _POUR6 + 'GND via (27.65, 29.85) to C99.2, 2.31 mm for 1.78: both two-segment routes cross VLOGIC\'s F.Cu diagonal '
     '(27.905, 29.25)-(28.505, 29.85); the clean three-segment redraws are longer (2.53 mm)', dict(path_mm=2.308)),
    ('chain_detour', 'GND', 'B.Cu', (13.7, 80.6),
     _POUR6 + 'U10.2 to Q123.2, 6.08 mm for 3.42: the two-segment routes cross U10.1 (VBUS) and RAW_ACT\'s via '
     '(12.6, 81.27) (inherited R6)', dict(path_mm=6.084)),
    ('chain_detour', 'GND', 'B.Cu', (32.3, 55.7),
     _POUR6 + 'C23.2 to the GND via (31.5, 53.5), 4.01 mm for 2.53: the two-segment routes cross 3V3\'s B.Cu run to '
     'C23.1 (31.1-32.1, y 54.5); the clean three-segment redraws are longer (4.05 mm)', dict(path_mm=4.014)),
    ('chain_detour', 'RAW_ACT', 'F.Cu', (10.4, 64.67),
     _POUR6 + 'RAW_ACT_SENSE tap (a divider feed, uA) from R177.1 round R182 / R125 to its via (13.7, 65.37), 5.60 mm '
     'for 3.59: the direct routes cross GND\'s F.Cu (11.37, 64.1-65.1) between R177 and R182, and a via beside R177.1 '
     'collides with VBUS_SENSE\'s F.Cu diagonal (8.0, 65.9)-(10.9, 63.0) and USB_DM / USB_DP\'s B.Cu at x 10.05 '
     '(probed, fix pass 6)', dict(path_mm=5.604)),
    ('chain_detour', 'RAW_ACT', 'F.Cu', (12.6, 81.27),
     _POUR6 + 'the same tap\'s end from its In2 / F.Cu via (12.6, 81.27) into R6_RAW_ACT_F, 7.11 mm for 5.12: VBUS\'s '
     'F.Cu run (10.8, 79.95)-(10.8, 81.525)-(11.325, 82.05)-(13.225, 82.05) and C83.1 box the via in (the 0.5 mm2 fill '
     'fragment round it joins nothing), so the run goes round VBUS\'s via (10.8, 79.95) to the fill west of it; the '
     'direct routes cross that VBUS copper (inherited R6)', dict(path_mm=7.108)),
    ('pour_net_hop', '3V3', 'via', (41.0, 77.92),
     _POUR6 + '3V3 into J2.1 (Tag-Connect; its via-in-pad is M2\'s named exception): on F.Cu the feed crosses SWDIO\'s '
     'diagonal (33.43, 69.65)-(41.7, 77.92) into J2 and J2\'s 0.508 mm contact rule, so it runs on B.Cu under J2\'s pad '
     'field between the via (41.0, 77.92) and J2.1\'s via (44.035, 77.92)', dict(path_mm=11.186, vias=2)),
    ('pour_net_hop', '3V3', 'via', (12.5, 89.2),
     _POUR6 + '3V3 In2 feed (7.9, 84.6) -> (21.9, 96.125): In2 between x 12.5 and 16.3 holds the BAT_IN In2 fill '
     '(x < 14) and CAM_FAULT_N\'s and SERVO4_MCU\'s In2 runs (x 14.64-16.0), which an In2 run cannot cross; the 3.8 mm '
     'F.Cu hop passes over them', dict(path_mm=22.974, vias=2)),
    ('pour_net_hop', '3V3', 'via', (35.1, 45.025),
     _POUR6 + '3V3 from B.Cu (33.8, 43.725) to the F.Cu T (36.5, 51.65) through an In2 run in a 3V3_In2 void: on B.Cu '
     'the run crosses 3V3A\'s B.Cu (36.9-39.4, y 48.1), on F.Cu RAW_PROTECTED\'s diagonal (36.15, 47.9)-(38.05, 49.8)',
     dict(path_mm=12.316, vias=2)),
    ('pour_net_hop', 'RAW_ACT', 'via', (13.1, 75.97),
     _POUR6 + 'RAW_ACT_SENSE tap R177.1 (F.Cu) -> R6_RAW_ACT_F (F.Cu) through B.Cu and In2 (a divider feed, uA): F.Cu '
     'is closed by LS120.1, D123.1 and 3V3\'s F.Cu runs (x 11-13.4, y 76.5-80.2), B.Cu by the BAT_IN_B pour from '
     'y 80.9 and Q123 / U10 / R163 (inherited R6)', dict(path_mm=22.291, vias=2)),
    ('pour_net_hop', 'CAM_5V', 'via', (41.3, 32.425),
     _POUR6 + 'U13.1 -> C91.1, both B.Cu: the B.Cu route crosses CAM_IO_3V3\'s B.Cu diagonal (42.8, 32.45)-(40.75, 34.5) '
     'and U13.5 (probed); the 2.4 mm F.Cu hop passes over it (inherited R6)', dict(path_mm=4.614, vias=2)),
    ('extra_vias', 'VLOGIC', 'net', (18.2, 29.4),
     '10 pads, 2 on F.Cu (C84.1 at x 7.5, C99.1 at U11) and 8 on B.Cu (U2, C7, C6, TP83, U11, R60): 5 vias for '
     '66.37 mm (inherited R6 tree; C84, the bulk capacitor, sits 10 mm west of U2; fix pass 5 ended two runs at the U2.2 '
     '/ U2.3 pad centres, +0.1 mm; fix pass 7 took the 0.6 mm F.Cu peak round D122.2 out, P7-ROUTING-01)'),
    ('local_bump', 'USB_LIMITED', 'B.Cu', (33.1, 26.15),
     'fix pass 7: C98.1 (U11\'s input bulk capacitor, B.Cu) to the U11.7 node (30.8, 27.85) leaves the pad\'s top edge NW, '
     'W, SW round BAT_SW_RETURN\'s via (31.9, 26.325) and comes back S (4.35 mm; inherited R6). The shorter redraws bump_audit '
     'finds (S, SW past the GND via (32.2, 27.033), W into the node: 3.4 mm) cut the B.Cu GND copper that is R105.2\'s '
     'only path to that via: R105.2 (GND) leaves the net\'s pad group (r7_polish pad-group check, fix pass 7); between '
     'that GND via and the BAT_SW_RETURN via there is 0.216 mm, too little for the 0.25 mm run'),
    ('chain_detour', '3V3A', 'B.Cu', (35.5, 76.54),
     'fix pass 7 (P7-ROUTING-04 / P7-REGRESSION-02), a net with a pour: the hop from U4.5\'s (VDDIO) via (35.5, 76.54) to '
     'the U4.8 / C31 / C30 node\'s via (37.4, 76.52), 2.505 mm for 1.908: the GND via (36.5, 76.54), U4.6 / U4.7\'s '
     'return via, sits on the straight line 1.0 / 0.9 mm from the two, and the IMU\'s GND ties fill the south side, so '
     'the hop goes round it to the north (NE, E, SE); its gap to that via (0.200 mm) is set by the SE diagonal into the '
     'east via\'s centre, whose line the via positions fix. A drawing short enough to pass the chain test (E leg '
     '0.12 mm lower, fix pass 6) only cut that gap to 0.169 mm. Both vias also join the one 3V3A_In2 island: the hop is '
     'kept as U4.5\'s short path to the 100 nF capacitors at U4.8 (Inference: via-island-via adds about 1 nH)',
     dict(path_mm=2.505)),
]


# Non-critical leftovers (counted, not gated; REQUIREMENTS M2 review items, P4-DOCS-01): (category, net, layer, (x, y),
# measured reason). Every non-critical instance of a LEFTOVER_CATS (hygiene) category must have an entry, and an
# entry that matches nothing fails, as for the allowlist (leftover_check). Filled from the fix-pass-4 searches
# (sources/r7_review/fix4_F5_handoff.md).
LEFTOVER_CATS = HYGIENE            # every hygiene category (fix pass 5; was detour / extra_vias / tiny_jog / short_segment)
_S = ('raster search on the fix-pass-4 board (scratch fx4/det/r3, r4, r5: F/B/In2 at 0.05 mm (r5: 0.1 mm over the '
      'whole board), the net\'s copper removed, every board clearance incl. the pyro rules, a multi-pad net searched edge '
      'by edge over the octilinear MST of its pads and summed). The search blocks every power pour on every layer, a '
      'stricter rule than the board follows (most of these nets run partly through a void of a 3V3 / 3V3A / BAT_IN '
      'pour on In2, P5-DOCS-01(d)), so "no route" or "the best found" holds under that rule only, not for every route '
      'the board would take')
LEFTOVERS = [
    ('detour', 'BAT_FAULT_N', 'net', (11.975, 43.1),
     '39.97 mm / 4 vias for a 22.47 mm pad tree (R89.2 / U9.4 on F.Cu, TP85 on B.Cu, U1.81 on F.Cu; inherited R6); ' + _S +
     ': 31.4 mm / 2 vias, but only with a forced 0.125 mm jog (B.Cu between VLOGIC at x 11.9 and QSPI_IO0\'s via '
     '(12.9, 44.4): the corridor needs x <= 12.365 by the via and x >= 12.385 by VLOGIC) and a via hairpin under U1.81 '
     '(TP87\'s 1.0 mm bare-pad keep-out and C20 leave no via spot on the pin\'s line): kept'),
    ('extra_vias', 'BAT_FAULT_N', 'net', (11.975, 43.1), 'as its detour entry: 4 vias; the search\'s 2-via route needs '
     'the forced jog and the hairpin'),
    ('detour', 'BAT_SW_RETURN', 'net', (15.38, 110.4),
     '160.34 mm / 5 vias for 76.28 mm (J1.4, the external switch return, to R165.1 at (3.3, 39.1): up the east edge, '
     'across the forward end and down the west side; inherited R6); ' + _S + ' (det/r5): 177.7 mm / 7 vias, longer; the '
     'direct west side is closed by the 7.7 A BAT_IN / RAW_ACT pours'),
    ('extra_vias', 'BAT_SW_RETURN', 'net', (15.38, 110.4), 'as its detour entry: the search\'s best has 7 vias'),
    ('extra_vias', 'BAT_SW_SOURCE', 'net', (20.46, 110.4),
     '129.2 mm / 7 vias (J1.3, the external switch source, to R80.2 at (17.1, 24.5), up the east edge; inherited R6); '
     + _S + ' (det/r5): 124.9 mm / 6 vias, with six F/B hops along the strip\'s forward edge (y 23.9-25.1): one via less '
     'for as many layer hops, not simpler'),
    ('detour', 'BUZZ_OUT', 'net', (14.87, 79.8),
     '22.55 mm / 1 via for an 8.76 mm pad tree (D123, LS120 on F.Cu, Q123 on B.Cu); ' + _S + ': 21.7 mm / 1 via, the '
     'present route'),
    ('detour', 'CAM_EN', 'net', (36.7, 84.975),
     '6.95 mm / 1 via for 3.73 mm (R74.2 / R75.1 on F.Cu, U7.2 on B.Cu); its B.Cu leg threads C71.1 / U7.1 (fix pass 5: '
     'W, S, SW instead of the 0.293 mm step, +0.18 mm); ' + _S + ': 7.45 mm / 1 via, longer'),
    ('detour', 'CAM_FAULT_N', 'net', (20.8, 96.175),
     '92.46 mm / 5 vias for 53.69 mm (R76.2 and R77.1 by the camera eFuse, U1.85; across the pyro block and under the IMU '
     'area; inherited R6; fix pass 5 straightened its In2 run: its tiny step and its staircase went; fix pass 6 moved its '
     'In2 run back to x 14.64 through its via down to y 91.85, one 0.78 mm step onto x 15.19, so SERVO4_MCU\'s run is '
     '0.67-0.71 mm away again, -0.55 mm; fix pass 7 took its In2 bump between the vias (16.04, 67.46) and (19.82, 62.35) '
     'out, -2.61 mm); ' + _S +
     ' (fix-pass-4 copper): 78.9 mm but 7 vias'),
    ('extra_vias', 'CAM_FAULT_N', 'net', (20.8, 96.175), 'as its detour entry: the shorter search route has 7 vias'),
    ('extra_vias', 'CAM_MCU_RX', 'net', (17.35, 45.95),
     '32.81 mm / 6 vias; its F.Cu hop (25.85-28.25, y 42.35) between two In2 runs passes over a 3V3_In2 fill bridge (fix '
     'pass 5, measured: on In2 the same run clears every track but cuts that fill); ' + _S + ': 32.1 mm / 5 vias, by four '
     'In2 / F.Cu alternations along y 42.3 under the QSPI flash (In2 runs 4.6 and 2.9 mm, 0.05-0.1 mm grid jogs): one '
     'via less for two more In2 hops, not simpler'),
    ('detour', 'CAM_MCU_TX', 'net', (17.85, 45.95),
     '65.87 mm / 5 vias; ' + _S + ': 66.0 mm / 5 vias, the present route (fix pass 3: the 50.8 mm / 3-via candidate cuts '
     'the In2 3V3 plane at the buck output, L1.2 -> U1.75 14.25 -> 29.66 mOhm)'),
    ('extra_vias', 'CAM_MCU_TX', 'net', (17.85, 45.95), 'as its detour entry: the search\'s best also has 5 vias'),
    ('detour', 'CAM_PWR_EN', 'net', (36.7, 86.625),
     '81.9 mm / 8 vias (R74.1 by the camera eFuse to U1.84; no F/B-only route exists, fix pass 3); ' + _S + ': 59.1 mm / 8 '
     'vias, hopping F / In2 / B / F / B / F / B / In2 / F through the pyro block and under U1 (det/r3/CAM_PWR_EN_0): '
     'shorter, as many vias and more layer hops; the corridor trade-off with the SWD lines is P3-REQUIREMENTS-01 '
     'option (b), for the owner'),
    ('extra_vias', 'CAM_PWR_EN', 'net', (36.7, 86.625), 'as its detour entry: the search\'s best also has 8 vias'),
    ('extra_vias', 'CAM_UART_OE', 'net', (42.175, 45.7),
     'rerouted in fix pass 4 (r7_polish.reroutes): 44.1 mm / 6 vias -> 30.68 mm / 4 vias; ' + _S + ': 33.1 mm / 5 vias. '
     'R102.1, U12.6 and TP91 are on B.Cu, U1.7 on F.Cu, and the run must cross SWCLK\'s F.Cu diagonal (a 2.7 mm In2 hop)'),
    ('extra_vias', 'LED_YEL', 'net', (40.7, 29.4),
     '36.26 mm / 3 vias (R33.1 to U1.37, both F.Cu, across the U1-side radio lanes); ' + _S + ': 36.0 mm / 3 vias, the '
     'present route'),
    ('extra_vias', 'LOGIC_SOURCE_ST', 'net', (30.725, 38.6),
     '58.31 mm / 11 vias (U11.9 / R91.2 and TP87 on B.Cu, U1.82 on F.Cu; inherited R6; fix pass 5 took the step across '
     'its via (30.725, 37.5) out); its F.Cu hop (16.42-18.78, y 48.2) between two In2 runs passes over a 3V3_In2 fill '
     'bridge (measured: on In2 it clears every track but cuts that fill); ' + _S + ': 55.5 mm / 10 vias with 21 mm of '
     'In2 in four runs: one via less, not simpler'),
    ('extra_vias', 'NRST', 'net', (29.4, 47.92),
     'J2 branch rerouted in fix pass 4 (r7_polish.reroutes; off In1): 54.33 mm / 6 vias -> 46.11 mm / 4 vias; ' + _S +
     ': 45.4 mm / 5 vias. C24.1 is on B.Cu, U1.14 and J2.3 on F.Cu, and the J2 branch crosses SWCLK and the SPI1 area'),
    ('detour', 'RAW_ACT_SENSE', 'net', (13.75, 67.4),
     '38.93 mm / 2 vias for a 24.05 mm pad tree (C122, R124, R125, R182 by the servo feed, R172 at U1); ' + _S + ': '
     '41.4 mm / 2 vias, longer'),
    ('extra_vias', 'SERVO1_MCU', 'net', (31.05, 81.25),
     '65.32 mm / 5 vias (D121 / R154 / R150 on B.Cu, U1.22 on F.Cu); ' + _S + ': 62.2 mm / 4 vias, with 14.6 mm of In2 in '
     'two runs under U1\'s SE corner and the SPI1 area: one via less for two In2 runs, not simpler'),
    ('extra_vias', 'SERVO2_MCU', 'net', (32.95, 81.25),
     '76.72 mm / 9 vias (D121, R155, R151 by the servo header on B.Cu, U1.23 on F.Cu; inherited R6). Measured blockers '
     '(fix pass 5, and pass-5 review): its F.Cu hairpin between vias (28.1, 58.6) and (30.1, 60.8) hops C13.2\'s B.Cu GND '
     'tie (x 29.4, y 57.82-59.7): the straight B.Cu run at y 58.6 collides with it, and GndFit finds no legal GND via spot '
     'within 1 mm of C13.2 north of that row to shorten the tie; its In2 hop (26.3, 67.4) -> (24.4, 69.3) crosses '
     'SPI1_SCK\'s B.Cu diagonal; ' + _S + ': the header legs 21.4 mm / 2 vias and 1.8 mm, and no route from D121.3 into '
     'U1.23 under that rule'),
    ('detour', 'SERVO2_OUT', 'net', (25.54, 76.97),
     '34.94 mm / 1 via for 16.9 mm (J122.4 to R151.2; inherited R6; fix pass 7 redrew its In2 run below the pyro block, '
     'S, E, NE -> SE, E, NE, -2.13 mm, the pass-7 review\'s redraw); bump_audit --bumps-all finds no shorter clean '
     'redraw of any window of it; ' + _S + ': 31.4 mm / 1 via only with 0.15 and 0.55 mm jogs on B.Cu in the pyro block '
     '(det/r3/SERVO2_OUT_0); with every segment >= 0.6 mm it needs 3 vias (32.3 mm, rt/s2o_a)'),
    ('detour', 'SERVO4_MCU', 'net', (31.05, 83.55),
     '96.38 mm / 3 vias for 56.3 mm (D121.6, R153, R157 by the servo header, U1.25; fix pass 5 straightened its In2 run '
     'down x 15.505, the 0.36 mm step gone; fix pass 6: one 0.71 mm SE step onto x 16.005 below the 3V3 via '
     '(16.3, 90.525), 0.67 mm from CAM_FAULT_N, same length); ' + _S + ' (fix-pass-4 copper): 97.8 mm / 11 vias'),
    ('detour', 'SERVO4_OUT', 'net', (25.54, 71.89),
     '46.92 mm / 3 vias for 25.74 mm (J122.10 to R153.2); ' + _S + ': 52.4 mm / 6 vias'),
    ('extra_vias', 'SERVO4_OUT', 'net', (25.54, 71.89), 'as its detour entry: the search\'s best has 6 vias'),
    ('detour', 'SWCLK', 'net', (42.365, 76.65),
     'fix-pass-3 route, 62.7 mm / 4 vias, F/B only, out of U1\'s SW corner (SWD is idle in flight); ' + _S + ': 61.0 mm / '
     '4 vias in the same corridor'),
    ('extra_vias', 'SWCLK', 'net', (42.365, 76.65), 'as its detour entry: the search\'s best also has 4 vias'),
    ('extra_vias', 'SWDIO', 'net', (42.365, 77.92),
     'fix-pass-3 route, 53.72 mm / 4 vias; ' + _S + ': 54.0 mm / 4 vias, the present route'),
    ('extra_vias', 'VBUS_SENSE', 'net', (16.1, 71.875),
     '43.13 mm / 4 vias (R110, R9, TP92 on B.Cu, U1.62 on F.Cu); ' + _S + ': 47.2 mm / 6 vias'),
]

# Measured route figures (len_mm, vias: route_check --routes on the final board) of every net with a detour or
# extra_vias entry in ALLOWLIST or LEFTOVERS: the entries' search results and reasons describe these routes, and the
# gate fails when the board's route differs (measured_check).
ROUTE_FIGURES = {
    'ARM1_SENSE': (63.73, 4), 'BAT_FAULT_N': (39.97, 4), 'BAT_SW_RETURN': (160.34, 5), 'BAT_SW_SOURCE': (129.2, 7),
    'BUZZ_OUT': (22.55, 1), 'CAM_EN': (6.95, 1), 'CAM_FAULT_N': (92.46, 5),
    'CAM_MCU_RX': (32.81, 6), 'CAM_MCU_TX': (65.87, 5), 'CAM_PWR_EN': (81.9, 8), 'CAM_UART_OE': (30.68, 4),
    'GNSS_LNA_EN': (7.45, 1), 'GNSS_RESET_N': (59.34, 2), 'GNSS_VCC_RF': (6.2, 1), 'LED_YEL': (36.26, 3),
    'LOGIC_SOURCE_ST': (58.31, 11), 'NRST': (46.11, 4), 'PYRO1_CONT': (53.33, 6), 'QSPI_IO2': (33.26, 3),
    'RADIO_DIO1': (69.09, 4), 'RADIO_NRST': (85.44, 4), 'RADIO_NSS': (58.4, 4), 'RADIO_RXEN': (51.88, 4),
    'RADIO_TXEN': (25.17, 2), 'RAW_ACT_SENSE': (38.93, 2), 'RAW_PROTECTED': (143.53, 7), 'SERVO1_MCU': (65.32, 5),
    'SERVO2_MCU': (76.72, 9), 'SERVO2_OUT': (34.94, 1), 'SERVO4_MCU': (96.38, 3), 'SERVO4_OUT': (46.92, 3),
    'SWCLK': (62.7, 4), 'SWDIO': (53.72, 4), 'VBUS': (42.49, 6), 'VBUS_SENSE': (43.13, 4), 'VCAP1': (6.71, 2),
    'VCAP2': (12.67, 1), 'VLOGIC': (66.37, 5),
}


def net_class(name):
    for c, rx in CLASSES:
        if re.search(rx, name):
            return c
    return 'other'


def mm(v):
    return v * NM


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def pt_seg(p, a, b):
    """Distance from p to segment ab, and the projection parameter t along ab."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return dist(p, a), 0.0
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2
    tc = min(1.0, max(0.0, t))
    return math.hypot(p[0] - (a[0] + tc * dx), p[1] - (a[1] + tc * dy)), t


def heading(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360.0


def dev45(h):
    r = h % 45.0
    return min(r, 45.0 - r)


def vang(u, v):
    nu, nv = math.hypot(*u), math.hypot(*v)
    if nu == 0 or nv == 0:
        return None
    c = (u[0] * v[0] + u[1] * v[1]) / (nu * nv)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def interior_crossing(a, b, c, d):
    r = (b[0] - a[0], b[1] - a[1]); s = (d[0] - c[0], d[1] - c[1])
    den = r[0] * s[1] - r[1] * s[0]
    if den == 0:
        return None
    t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den
    u = ((c[0] - a[0]) * r[1] - (c[1] - a[1]) * r[0]) / den
    la, lc = math.hypot(*r), math.hypot(*s)
    if TOL < t * la < la - TOL and TOL < u * lc < lc - TOL:
        return a[0] + t * r[0], a[1] + t * r[1]
    return None


def P(p):
    return pcbnew.VECTOR2I(int(round(p[0])), int(round(p[1])))


# --- connectivity (KiCad anchor rule) --------------------------------------------------------------------------------

class NetCopper:
    """One net's tracks, vias, pads and pour fills, as plain data (nm), for the connectivity graph. Built from a board
    by collect(); tracks/vias carry their pcbnew object in 'obj' (left out of the graph when skipped)."""

    def __init__(self, net):
        self.net, self.tracks, self.vias, self.pads, self.zones = net, [], [], [], []


def collect(board, nets=None):
    """{net: NetCopper} for every net with copper (nets limits it)."""
    out = {}

    def get(n):
        if n not in out:
            out[n] = NetCopper(n)
        return out[n]
    for t in board.GetTracks():
        n = t.GetNetname()
        if not n or (nets is not None and n not in nets):
            continue
        if t.GetClass() == 'PCB_VIA':
            p = t.GetPosition()
            get(n).vias.append(dict(pos=(p.x, p.y), r=t.GetWidth(pcbnew.F_Cu) / 2,
                                    layers={l for l in CU4 if t.IsOnLayer(l)}, obj=t))
        elif t.GetClass() in ('PCB_TRACK', 'PCB_ARC'):
            a, b = t.GetStart(), t.GetEnd()
            get(n).tracks.append(dict(lid=t.GetLayer(), a=(a.x, a.y), b=(b.x, b.y), w=t.GetWidth(), obj=t))
    for f in board.GetFootprints():
        for k, p in enumerate(f.Pads()):
            n = p.GetNetname()
            if not n or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or (nets is not None and n not in nets):
                continue
            bb = p.GetBoundingBox()
            get(n).pads.append(dict(name=f'{f.GetReference()}.{p.GetNumber()}', key=f'{f.GetReference()}.{p.GetNumber()}#{k}',
                                    pos=(p.GetPosition().x, p.GetPosition().y), obj=p,
                                    layers={l for l in CU4 if p.IsOnLayer(l)},
                                    bb=(bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())))
    for z in board.Zones():
        n = z.GetNetname()
        if z.GetIsRuleArea() or not n or (nets is not None and n not in nets):
            continue
        get(n).zones.append((z, [l for l in CU4 if z.IsOnLayer(l)]))
    return out


def _in_pad(pd, lid, p, extra=0):
    l, t, r, b = pd['bb']
    return lid in pd['layers'] and l - extra <= p[0] <= r + extra and t - extra <= p[1] <= b + extra and \
        pd['obj'].GetEffectiveShape(lid).Collide(P(p), int(extra))


def _in_zone(nc, lid, p, acc=0):
    return any(lid in lays and z.HitTestFilledArea(lid, P(p), int(acc)) for z, lays in nc.zones)


def _islands(nc, lid, p=None, shape=None, acc=0):
    """Keys (zone index, layer, outline index) of the net's pour fill islands on lid that hold point p (within acc) or
    touch shape."""
    out = []
    cache = nc.__dict__.setdefault('islands', {})
    for k, (z, lays) in enumerate(nc.zones):
        if lid not in lays or not z.HasFilledPolysForLayer(lid):
            continue
        if (k, lid) not in cache:
            fill = z.GetFilledPolysList(lid)
            polys = []
            for o in range(fill.OutlineCount()):
                one = pcbnew.SHAPE_POLY_SET()
                one.AddOutline(fill.Outline(o))
                for h in range(fill.HoleCount(o)):
                    one.AddHole(fill.Hole(o, h))
                bb = one.BBox()
                polys.append((o, one, (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())))
            cache[(k, lid)] = polys
        for o, one, bb in cache[(k, lid)]:
            if shape is None:
                if not (bb[0] - acc <= p[0] <= bb[2] + acc and bb[1] - acc <= p[1] <= bb[3] + acc):
                    continue
                hit = one.Collide(P(p), int(acc))
            else:
                sb = shape.BBox()
                if sb.GetRight() < bb[0] or sb.GetLeft() > bb[2] or sb.GetBottom() < bb[1] or sb.GetTop() > bb[3]:
                    continue
                hit = one.Collide(shape, 1000)
            if hit:
                out.append((k, lid, o))
    return out


def graph(nc, zones=True, skip=frozenset(), strict=False, island_nodes=False):
    """The net's copper as a multigraph. Nodes: track-end clusters (per layer, TOL), points where an anchor meets a
    track's body, vias, pads and the terminal hub 'S' (node 0). Edges: (u, v, ref) with ref ('t', track index, s0, s1)
    for a track piece between parameters s0 < s1, ('link',) for an anchor join, ('S',) from a terminal (a pad; ('Z', key)
    instead for a contact with pour fill island `key`, and with
    zones=True every track end or via inside a same-net pour fill) to the hub. With island_nodes=True each pour fill
    island is a node of its own, joined to the hub by one ('Z', key) edge, and each contact with it is an edge
    ('Zc', key) to that node (copper that touches only one island then closes no path between two terminals).
    skip: id()s of pcbnew objects to leave
    out. strict=True joins a track end to another track only on its centre line (a T, within TOL), not anywhere in its
    copper: an overlap-only joint is then no joint. Returns (number of nodes, edges, node of each via (by index), node
    of each pad (by index))."""
    tracks = [(i, t) for i, t in enumerate(nc.tracks) if id(t['obj']) not in skip]
    vias = [(i, v) for i, v in enumerate(nc.vias) if id(v['obj']) not in skip]
    edges = []
    n = [1]

    def node():
        n[0] += 1
        return n[0] - 1
    island = {}

    def zedge(nd, key):
        if not island_nodes:
            edges.append((0, nd, ('Z', key)))
            return
        if key not in island:
            island[key] = node()
            edges.append((0, island[key], ('Z', key)))
        edges.append((island[key], nd, ('Zc', key)))
    via_node = {i: node() for i, _ in vias}
    pad_node = {i: node() for i in range(len(nc.pads))}
    for i in pad_node:
        edges.append((0, pad_node[i], ('S',)))
    for i, p1 in enumerate(nc.pads):              # same-net pads whose copper overlaps (a pin drawn as two pads)
        for j in range(i + 1, len(nc.pads)):
            p2 = nc.pads[j]
            b1, b2 = p1['bb'], p2['bb']
            if b1[2] < b2[0] or b2[2] < b1[0] or b1[3] < b2[1] or b2[3] < b1[1]:
                continue
            if any(p1['obj'].GetEffectiveShape(l).Collide(p2['obj'].GetEffectiveShape(l), 0)
                   for l in p1['layers'] & p2['layers']):
                edges.append((pad_node[i], pad_node[j], ('link',)))
    # end clusters per layer
    cl = {}                       # (lid, grid key) -> list of (point, node)
    end_node = {}
    for i, t in tracks:
        for e, p in ((0, t['a']), (1, t['b'])):
            g = (round(p[0] / TOL), round(p[1] / TOL))
            hit = None
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for q, nd in cl.get((t['lid'], g[0] + dx, g[1] + dy), ()):
                        if dist(q, p) <= TOL:
                            hit = nd
            if hit is None:
                hit = node()
                cl.setdefault((t['lid'], g[0], g[1]), []).append((p, hit))
            end_node[(i, e)] = hit
    clusters = defaultdict(list)          # lid -> [(point, node)]
    for (lid, _, _), L in cl.items():
        clusters[lid] += L
    # each track: its attachments along the body
    by_layer = defaultdict(list)
    for i, t in tracks:
        by_layer[t['lid']].append((i, t))
    for i, t in tracks:
        a, b, w, lid = t['a'], t['b'], t['w'], t['lid']
        L = dist(a, b)
        x0, x1 = min(a[0], b[0]) - w, max(a[0], b[0]) + w
        y0, y1 = min(a[1], b[1]) - w, max(a[1], b[1]) + w
        att = [(0.0, end_node[(i, 0)]), (1.0, end_node[(i, 1)])]
        own = {end_node[(i, 0)], end_node[(i, 1)]}
        for q, nd in clusters[lid]:
            if nd in own or not (x0 <= q[0] <= x1 and y0 <= q[1] <= y1):
                continue
            d, s = pt_seg(q, a, b)
            if (d <= TOL and TOL < s * L < L - TOL) if strict else d <= w / 2:
                att.append((min(1.0, max(0.0, s)), nd))
        for j, v in vias:
            if lid not in v['layers']:
                continue
            for e, p in ((0, a), (1, b)):
                if dist(p, v['pos']) <= v['r']:
                    edges.append((end_node[(i, e)], via_node[j], ('link',)))
            d, s = pt_seg(v['pos'], a, b)
            if d <= (TOL if strict else w / 2) and dist(v['pos'], a) > v['r'] and dist(v['pos'], b) > v['r']:
                att.append((min(1.0, max(0.0, s)), via_node[j]))
        for k, pd in enumerate(nc.pads):
            if lid not in pd['layers']:
                continue
            for e, p in ((0, a), (1, b)):
                if _in_pad(pd, lid, p):
                    edges.append((end_node[(i, e)], pad_node[k], ('link',)))
            d, s = pt_seg(pd['pos'], a, b)
            if d <= w / 2 and not _in_pad(pd, lid, a) and not _in_pad(pd, lid, b):
                att.append((min(1.0, max(0.0, s)), pad_node[k]))
        att.sort(key=lambda x: x[0])
        for (s0, u), (s1, v) in zip(att, att[1:]):
            edges.append((u, v, ('t', i, s0, s1)))
        if zones:
            for e, p in ((0, a), (1, b)):
                for key in _islands(nc, lid, p):
                    zedge(end_node[(i, e)], key)
    for j, v in vias:
        for k, pd in enumerate(nc.pads):
            if any(_in_pad(pd, l, v['pos']) for l in v['layers'] & pd['layers']) or \
                    (v['layers'] & pd['layers'] and dist(pd['pos'], v['pos']) <= v['r']):
                edges.append((via_node[j], pad_node[k], ('link',)))
        if zones:
            for l in sorted(v['layers']):                  # one terminal edge per pour island holding the via
                for key in _islands(nc, l, v['pos'], acc=v['r']):
                    zedge(via_node[j], key)
    if zones:
        for k, pd in enumerate(nc.pads):
            for l in sorted(pd['layers']):
                for key in _islands(nc, l, shape=pd['obj'].GetEffectiveShape(l)):
                    zedge(pad_node[k], key)
    return n[0], edges, via_node, pad_node


def blocks(nn, edges):
    """Biconnected component id of each edge (iterative Tarjan; parallel edges and self-loops allowed)."""
    adj = [[] for _ in range(nn)]
    comp = [-1] * len(edges)
    cid = 0
    for k, (u, v, _) in enumerate(edges):
        if u == v:
            comp[k] = cid
            cid += 1
            continue
        adj[u].append((v, k))
        adj[v].append((u, k))
    disc, low = [-1] * nn, [0] * nn
    tick = 0
    estack = []
    for root in range(nn):
        if disc[root] != -1:
            continue
        disc[root] = low[root] = tick
        tick += 1
        stack = [(root, -1, iter(adj[root]))]
        while stack:
            u, pe, it = stack[-1]
            pushed = False
            for v, k in it:
                if k == pe:
                    continue
                if disc[v] == -1:
                    estack.append(k)
                    disc[v] = low[v] = tick
                    tick += 1
                    stack.append((v, k, iter(adj[v])))
                    pushed = True
                    break
                if disc[v] < disc[u]:
                    low[u] = min(low[u], disc[v])
                    estack.append(k)
            if pushed:
                continue
            stack.pop()
            if stack:
                p = stack[-1][0]
                low[p] = min(low[p], low[u])
                if low[u] >= disc[p]:
                    while True:
                        k = estack.pop()
                        comp[k] = cid
                        if k == pe:
                            break
                    cid += 1
    return comp


def _inside_one(nc, r):
    """Whether a track piece lies inside one same-net pad or via (both ends in it): no copper of its own."""
    t = nc.tracks[r[1]]
    p0 = (t['a'][0] + r[2] * (t['b'][0] - t['a'][0]), t['a'][1] + r[2] * (t['b'][1] - t['a'][1]))
    p1 = (t['a'][0] + r[3] * (t['b'][0] - t['a'][0]), t['a'][1] + r[3] * (t['b'][1] - t['a'][1]))
    if any(_in_pad(pd, t['lid'], p0) and _in_pad(pd, t['lid'], p1) for pd in nc.pads):
        return True
    return any(t['lid'] in v['layers'] and dist(p0, v['pos']) <= v['r'] and dist(p1, v['pos']) <= v['r']
               for v in nc.vias)


def dead(nc, pour_islands=True):
    """Dead copper of one net: ({track index: [(s0, s1), ...] dead pieces}, [dead via indices]). An edge is live when
    its biconnected block (of the graph with the terminal hub, strict joints) holds a terminal edge and at least one
    other edge, i.e. it lies on a cycle through the hub: on a path between two terminals. A via whose only copper is
    one pour is dead; pieces inside one same-net pad or via are not counted (they have no copper of their own).
    pour_islands=True (the gate): each pour fill island is one terminal (graph(island_nodes=True)), so a run touching
    only one island is dead; and a stub ending in a pour is dead: a run from a track end whose only contact is the
    net's pour (no pad, via, link or other track) through plain nodes back to the first other node, unless the run's
    far end is another such end on a different island (a bridge between two islands), when removing the run's whole
    tracks leaves the net's pad groups with the pours joining exactly as they are. pour_islands=False keeps every
    pour contact a separate terminal edge (m3_design/r7_hygiene.py's dead stage, whose output the build pins)."""
    nn, edges, via_node, pad_node = graph(nc, strict=True, island_nodes=pour_islands)
    comp = blocks(nn, edges)
    size = Counter(comp)
    live = {comp[k] for k, (u, v, r) in enumerate(edges) if r[0] in ('S', 'Z') and size[comp[k]] >= 2}
    pieces = defaultdict(list)
    used = defaultdict(bool)
    for k, (u, v, r) in enumerate(edges):
        alive = comp[k] in live
        if r[0] == 't':
            if not alive and not _inside_one(nc, r):
                pieces[r[1]].append((r[2], r[3]))
        if alive:
            used[u] = used[v] = True
    dvias = [j for j, nd in via_node.items() if not used[nd]]
    if pour_islands:
        for i, segs in _pour_stubs(nc, edges, via_node, pad_node, set(pieces)).items():
            pieces[i] += segs
    return dict(pieces), dvias


def _pour_stubs(nc, edges, via_node, pad_node, already):
    """Stubs ending in a pour (see dead()): {track index: [(0.0, 1.0)]}."""
    inc = defaultdict(list)
    for k, (u, v, r) in enumerate(edges):
        if u != v:
            inc[u].append(k)
            inc[v].append(k)
    special = set(via_node.values()) | set(pad_node.values()) | {0}

    def kinds(nd):
        return [edges[k][2][0] for k in inc[nd]]

    def pour_only(nd):
        if nd in special:
            return False
        ks = kinds(nd)
        return ks.count('t') == 1 and 'link' not in ks and 'Zc' in ks

    def islands_of(nd):
        return {edges[k][2][1] for k in inc[nd] if edges[k][2][0] == 'Zc'}
    out, done, base = {}, set(), None
    for e0 in sorted(nd for nd in inc if pour_only(nd)):
        if e0 in done:
            continue
        run, cur, k = [], e0, next(k for k in inc[e0] if edges[k][2][0] == 't')
        while True:
            u, v, r = edges[k]
            run.append(k)
            cur = v if u == cur else u
            ks = kinds(cur)
            if cur in special or ks.count('t') != 2 or 'link' in ks or cur == e0:
                break
            k = next(x for x in inc[cur] if edges[x][2][0] == 't' and x != k)
        done.add(e0)
        done.add(cur)
        if pour_only(cur) and not (islands_of(cur) & islands_of(e0)):
            continue                                   # a bridge between two islands of the net's pour
        idx = {edges[k][2][1] for k in run}
        if any(edges[k][2][2] > 1e-9 or edges[k][2][3] < 1 - 1e-9 for k in run) or idx & already:
            continue                                   # part of a longer track, or already dead
        if base is None:
            base = pad_groups(nc, zones=True)
        skip = frozenset(id(nc.tracks[i]['obj']) for i in idx)
        if pad_groups(nc, skip=skip, zones=True) == base:
            for i in idx:
                out[i] = [(0.0, 1.0)]
    return out


def pad_groups(nc, skip=frozenset(), zones=False):
    """The net's pads partitioned by track/via connectivity (with zones=True pour fill islands also join what they
    touch): frozenset of frozensets of pad keys."""
    nn, edges, _, pad_node = graph(nc, zones=zones, skip=skip)
    island = {}
    for u, v, r in edges:
        if r[0] == 'Z' and r[1] not in island:
            island[r[1]] = nn + len(island)
    nn += len(island)
    edges = [(island[r[1]], v, ('link',)) if r[0] == 'Z' else (u, v, r) for u, v, r in edges]
    parent = list(range(nn))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for u, v, r in edges:
        if r[0] != 'S':
            parent[root(u)] = root(v)
    comp = defaultdict(set)
    for k, nd in pad_node.items():
        comp[root(nd)].add(nc.pads[k]['key'])
    return frozenset(frozenset(c) for c in comp.values())


def loops(nc):
    """Independent track loops of a net without pours: [(x, y, layer) of a point on each loop]. Joins inside one pad
    or via, and pieces under 1 µm, are contracted first (they are one place, not a loop)."""
    if nc.zones:
        return []
    nn, edges, _, _ = graph(nc, zones=False)
    parent = list(range(nn))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def piece_len(r):
        t = nc.tracks[r[1]]
        return (r[3] - r[2]) * dist(t['a'], t['b'])
    for u, v, r in edges:
        if r[0] == 'link' or (r[0] == 't' and piece_len(r) <= TOL):
            parent[root(u)] = root(v)
    contracted = [root(i) for i in range(nn)]
    out = []
    for u, v, r in edges:
        if r[0] != 't' or piece_len(r) <= TOL or contracted[u] == contracted[v]:
            continue                               # (a piece inside one pad or via is no loop)
        ru, rv = root(u), root(v)
        if ru == rv:
            t = nc.tracks[r[1]]
            s = (r[2] + r[3]) / 2
            out.append((t['a'][0] + s * (t['b'][0] - t['a'][0]), t['a'][1] + s * (t['b'][1] - t['a'][1]),
                        t['lid']))
        else:
            parent[ru] = rv
    return out


def critical_transitions(board):
    """Vias carrying a critical signal net's tracks on two or more layers: [(net, (x, y) nm, nearest GND via mm)]."""
    gnd, out = [], []
    by = defaultdict(list)
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            if t.GetNetname() == 'GND':
                gnd.append((t.GetPosition().x, t.GetPosition().y))
        elif t.GetClass() == 'PCB_TRACK' and net_class(t.GetNetname()) in SIGNAL_CRITICAL:
            by[t.GetNetname()].append((t.GetLayer(), (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)))
    for t in board.GetTracks():
        n = t.GetNetname()
        if t.GetClass() != 'PCB_VIA' or n not in by:
            continue
        p, r = (t.GetPosition().x, t.GetPosition().y), t.GetWidth(pcbnew.F_Cu) / 2
        lays = {lid for lid, a, b in by[n] if dist(a, p) <= r or dist(b, p) <= r}
        if len(lays) >= 2:
            g = min((dist(q, p) for q in gnd), default=None)
            out.append((n, p, None if g is None else mm(g)))
    return out


def net_route(nc):
    """Route metrics of a net without a pour (pads closer than 0.1 mm are one point): dict(pads (distinct points), len
    (track copper, mm), mst (octilinear minimum spanning tree of the pad centres, mm), vias (vias carrying the net's
    tracks on two or more layers), need (0 when every pad shares a copper layer, else 1), at (centre of the first pad by
    name, nm), first (its name)). For a two-pad net, len / mst is the detour ratio of its one connection."""
    pts = []
    for p in sorted(nc.pads, key=lambda q: q['key']):
        if not any(dist(p['pos'], q['pos']) < 0.1 / NM for q in pts):
            pts.append(p)
    n = len(pts)

    def octile(a, b):
        dx, dy = abs(mm(a[0] - b[0])), abs(mm(a[1] - b[1]))
        return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)
    done, best, mst = [False] * n, [float('inf')] * n, 0.0
    if n:
        best[0] = 0.0
    for _ in range(n):
        u = min((i for i in range(n) if not done[i]), key=lambda i: best[i])
        done[u] = True
        mst += best[u]
        for v in range(n):
            if not done[v]:
                best[v] = min(best[v], octile(pts[u]['pos'], pts[v]['pos']))
    vias = 0
    for v in nc.vias:
        if len({t['lid'] for t in nc.tracks if dist(t['a'], v['pos']) <= v['r'] or dist(t['b'], v['pos']) <= v['r']}) >= 2:
            vias += 1
    common = set.intersection(*[set(p['layers']) for p in pts]) if pts else set()
    return dict(pads=n, len=sum(mm(dist(t['a'], t['b'])) for t in nc.tracks), mst=mst, vias=vias,
                need=0 if common else 1, at=pts[0]['pos'] if pts else (0, 0), first=pts[0]['name'] if pts else '')


# --- pour fills: slivers, fingers, through-copper distance to GND stitching ------------------------------------------

def _edges(ps):
    """Every edge ((x0, y0), (x1, y1)) of a polygon set's outlines and holes, nm."""
    out = []
    chains = []
    for o in range(ps.OutlineCount()):
        chains.append(ps.Outline(o))
        chains += [ps.Hole(o, h) for h in range(ps.HoleCount(o))]
    for c in chains:
        n = c.PointCount()
        pts = [c.CPoint(i) for i in range(n)]
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            out.append(((a.x, a.y), (b.x, b.y)))
    return out


class Raster:
    """A grid over window (x0, y0, x1, y1) nm at `step` nm; cell (i, j) has its centre at x0 + (i + 0.5) step."""

    def __init__(self, win, step):
        self.x0, self.y0 = win[0], win[1]
        self.step = step
        self.nx = max(1, int(math.ceil((win[2] - win[0]) / step)))
        self.ny = max(1, int(math.ceil((win[3] - win[1]) / step)))

    def fill(self, polysets, grid=None):
        """Cells whose centre lies inside any of the polygon sets (even-odd per set): a bytearray (OR into grid)."""
        nx, ny, st = self.nx, self.ny, self.step
        grid = bytearray(nx * ny) if grid is None else grid
        X1, Y1 = self.x0 + nx * st, self.y0 + ny * st
        for ps in polysets:
            bb = ps.BBox()
            if bb.GetRight() < self.x0 or bb.GetLeft() > X1 or bb.GetBottom() < self.y0 or bb.GetTop() > Y1:
                continue
            rows = defaultdict(list)
            for (ax, ay), (bx, by) in _edges(ps):
                if ay == by:
                    continue
                lo, hi = (ay, by) if ay < by else (by, ay)
                j0 = max(0, int(math.ceil((lo - self.y0) / st - 0.5)))
                j1 = min(ny - 1, int(math.ceil((hi - self.y0) / st - 0.5)) - 1)
                for j in range(j0, j1 + 1):
                    yc = self.y0 + (j + 0.5) * st
                    rows[j].append(ax + (yc - ay) * (bx - ax) / (by - ay))
            for j, xs in rows.items():
                xs.sort()
                base = j * nx
                for a, b in zip(xs[0::2], xs[1::2]):
                    i0 = max(0, int(math.ceil((a - self.x0) / st - 0.5)))
                    i1 = min(nx - 1, int(math.ceil((b - self.x0) / st - 0.5)) - 1)
                    if i1 >= i0:
                        grid[base + i0:base + i1 + 1] = b'\x01' * (i1 - i0 + 1)
        return grid

    def centre(self, k):
        return self.x0 + (k % self.nx + 0.5) * self.step, self.y0 + (k // self.nx + 0.5) * self.step


def reach(r, copper, sources, limit):
    """Through-copper distance (mm) from the source cells over the copper cells (8-neighbour raster Dijkstra), searched
    out to `limit` mm: an array with -1 for copper cells not reached within the limit (and for non-copper)."""
    nx, ny, st = r.nx, r.ny, mm(r.step)
    d = array('d', [-1.0]) * (nx * ny)
    h = []
    for k in range(nx * ny):
        if sources[k] and copper[k]:
            d[k] = 0.0
            h.append((0.0, k))
    heapq.heapify(h)
    steps = [(1, 0, st), (-1, 0, st), (0, 1, st), (0, -1, st)] + [(a, b, st * math.sqrt(2)) for a in (1, -1)
                                                                  for b in (1, -1)]
    while h:
        dk, k = heapq.heappop(h)
        if dk > d[k]:
            continue
        i, j = k % nx, k // nx
        for di, dj, w in steps:
            a, b = i + di, j + dj
            if 0 <= a < nx and 0 <= b < ny:
                q = b * nx + a
                nd = dk + w
                if copper[q] and nd <= limit and (d[q] < 0 or nd < d[q]):
                    d[q] = nd
                    heapq.heappush(h, (nd, q))
    return d


def _poly(item, lid):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, lid, 0, 2000, pcbnew.ERROR_INSIDE)
    return ps


def net_copper(board, net, lid):
    """(copper, stitching): the net's copper on lid as polygon sets (fills, tracks, pads, vias) and its stitching (its
    vias and plated through holes, which reach every layer)."""
    cop, stitch = [], []
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() == net and z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
            cop.append(z.GetFilledPolysList(lid))
    for t in board.GetTracks():
        if t.GetNetname() != net or not t.IsOnLayer(lid):
            continue
        ps = _poly(t, lid)
        cop.append(ps)
        if t.GetClass() == 'PCB_VIA':
            stitch.append(ps)
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == net and p.IsOnLayer(lid):
                ps = _poly(p, lid)
                cop.append(ps)
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                    stitch.append(ps)
    return cop, stitch


def thin_pieces(fill, half):
    """Pieces of `fill` narrower than 2 x half (nm): the fill minus its opening by half (re-grown 10 um more):
    [(polygon set of the piece, bbox (x0, y0, x1, y1) nm, length mm (bbox diagonal), area mm²)]."""
    er = pcbnew.SHAPE_POLY_SET(fill)
    er.Deflate(int(half), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, 5000)
    er.Inflate(int(half) + 10000, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, 5000)
    thin = pcbnew.SHAPE_POLY_SET(fill)
    thin.BooleanSubtract(er)
    out = []
    for i in range(thin.OutlineCount()):
        one = pcbnew.SHAPE_POLY_SET()
        one.AddOutline(thin.Outline(i))
        for h in range(thin.HoleCount(i)):
            one.AddHole(thin.Hole(i, h))
        bb = one.BBox()
        box = (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())
        out.append((one, box, math.hypot(mm(box[2] - box[0]), mm(box[3] - box[1])), one.Area() * NM * NM))
    return out


def gnd_reach(board, lid, window, region=None, limit=40.0):
    """Through-copper distance (mm) from each GND copper point of layer lid inside `region` (x0, y0, x1, y1 mm;
    default the window) to the nearest GND via or plated GND hole, searched over the window (mm) out to `limit`:
    [(distance or None when farther than limit, x, y)] on the RASTER grid."""
    cop, stitch = net_copper(board, 'GND', lid)
    r = Raster(tuple(v / NM for v in window), RASTER / NM)
    copper = r.fill(cop)
    d = reach(r, copper, r.fill(stitch), limit)
    x0, y0, x1, y1 = region or window
    out = []
    for k in range(r.nx * r.ny):
        if copper[k]:
            x, y = (mm(v) for v in r.centre(k))
            if x0 <= x < x1 and y0 <= y < y1:
                out.append((d[k] if d[k] >= 0 else None, x, y))
    return out


def pad_rings(board):
    """{(net, layer): SHAPE_POLY_SET} of the rings (outline grown by PAD_RING) of the pads with a thermal or solid
    connection to a same-net pour on that layer, inside its outline (pad_contacts)."""
    rings = {}
    pads = {f'{f.GetReference()}.{p.GetNumber()}#{k}': p for f in board.GetFootprints() for k, p in enumerate(f.Pads())}
    for (key, lid), (net, conn, inside, touch) in pad_contacts(board).items():
        if conn == 'none' or not inside:
            continue
        ps = pcbnew.SHAPE_POLY_SET()
        pads[key].TransformShapeToPolygon(ps, lid, int(PAD_RING / NM), 5000, pcbnew.ERROR_OUTSIDE)
        rings.setdefault((net, lid), pcbnew.SHAPE_POLY_SET()).BooleanAdd(ps)
    return rings


def pour_pieces(board):
    """The pour_sliver and pour_finger pieces of the board's fills (see the module docstring): [dict(cat, net, lid,
    poly (SHAPE_POLY_SET of the piece), box (nm), len_mm, plus area_mm2 / width_mm or cells_beyond / at)]."""
    out = []
    rings = pad_rings(board)
    by = defaultdict(list)
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.GetNetname():
            continue
        for lid in CU4:
            if z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                by[(z.GetNetname(), lid)].append(z.GetFilledPolysList(lid))
    for (net, lid), fills in sorted(by.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        fill = pcbnew.SHAPE_POLY_SET()
        for f in fills:
            fill.BooleanAdd(f)
        for one, box, L, area in thin_pieces(fill, SLIVER_W / 2 / NM):
            if L > SLIVER_L and area > 0.15:
                out.append(dict(cat='pour_sliver', net=net, lid=lid, poly=one, box=box, len_mm=round(L, 2),
                                area_mm2=round(area, 3), width_mm=round(area / L, 3)))
        if net != 'GND':
            continue
        ring = rings.get((net, lid))
        cand = []
        for one, box, L, area in thin_pieces(fill, FINGER_W / 2 / NM):
            if L <= FINGER_L:
                continue
            if ring is None:
                cand.append((one, box, L))
                continue
            rest = pcbnew.SHAPE_POLY_SET(one)
            rest.BooleanSubtract(ring)
            for i in range(rest.OutlineCount()):
                part = pcbnew.SHAPE_POLY_SET()
                part.AddOutline(rest.Outline(i))
                for h in range(rest.HoleCount(i)):
                    part.AddHole(rest.Hole(i, h))
                bb = part.BBox()
                pbox = (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())
                PL = math.hypot(mm(pbox[2] - pbox[0]), mm(pbox[3] - pbox[1]))
                if PL > FINGER_L:
                    cand.append((part, pbox, PL))
        if not cand:
            continue
        cop, stitch = net_copper(board, net, lid)
        for one, box, L in cand:
            m = (FINGER_REACH + 0.5) / NM
            r = Raster((box[0] - m, box[1] - m, box[2] + m, box[3] + m), RASTER / NM)
            copper = r.fill(cop)
            d = reach(r, copper, r.fill(stitch), FINGER_REACH)
            tgt = r.fill([one])
            far = [k for k in range(r.nx * r.ny) if tgt[k] and copper[k] and d[k] < 0]
            if far:
                xs = [r.centre(k) for k in far]
                p = max(xs, key=lambda q: (q[1], q[0]))
                out.append(dict(cat='pour_finger', net=net, lid=lid, poly=one, box=box, len_mm=round(L, 2),
                                cells_beyond=len(far), at=(round(mm(p[0]), 2), round(mm(p[1]), 2))))
    return out


def pad_connection(pad, zone):
    """The zone connection a pad gets from a zone: its own override, else the zone's; THT_THERMAL is thermal for a
    plated through hole and solid for an SMD pad. 'thermal', 'solid' or 'none'."""
    c = pad.GetLocalZoneConnection()
    if c == pcbnew.ZONE_CONNECTION_INHERITED:
        c = zone.GetPadConnection()
    if c == pcbnew.ZONE_CONNECTION_NONE:
        return 'none'
    if c == pcbnew.ZONE_CONNECTION_THT_THERMAL:
        return 'thermal' if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else 'solid'
    return 'thermal' if c == pcbnew.ZONE_CONNECTION_THERMAL else 'solid'


TRIM_PREFIX = 'R7_POUR_TRIM_'     # the generated pour-trim keep-outs (m3_design/r7_polish.pour_trim); the board's design
                                  # fill keep-outs (IMU/BARO bodies, Tag-Connect contacts, SMA launches) are intended


def is_trim(z):
    return z.GetIsRuleArea() and z.GetDoNotAllowZoneFills() and z.GetZoneName().startswith(TRIM_PREFIX)


def fill_keepouts(board):
    """{layer: [outline]} of the pour-trim keep-out rule areas (TRIM_PREFIX)."""
    out = defaultdict(list)
    for z in board.Zones():
        if is_trim(z):
            for lid in CU4:
                if z.IsOnLayer(lid):
                    out[lid].append(z.Outline())
    return out


def pad_contacts(board, pads=None):
    """{(pad key 'REF.N#k', layer): (net, connection, inside the zone outline, touches the fill)} for every pad on a
    layer where a same-net pour exists (pads limits it to those pad keys)."""
    zones = defaultdict(list)
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.GetNetname():
            for lid in CU4:
                if z.IsOnLayer(lid):
                    zones[(z.GetNetname(), lid)].append(z)
    out = {}
    for f in board.GetFootprints():
        for k, p in enumerate(f.Pads()):
            key = f'{f.GetReference()}.{p.GetNumber()}#{k}'
            if not p.GetNetname() or (pads is not None and key not in pads):
                continue
            for lid in CU4:
                zs = zones.get((p.GetNetname(), lid))
                if not zs or not p.IsOnLayer(lid):
                    continue
                sh = p.GetEffectiveShape(lid)
                conn = 'none'
                inside = touch = False
                for z in zs:
                    c = pad_connection(p, z)
                    if c == 'none':
                        continue
                    if z.Outline().Collide(sh, 0):
                        inside = True
                        conn = c if conn != 'solid' else conn
                    if z.HasFilledPolysForLayer(lid) and z.GetFilledPolysList(lid).Collide(sh, 50000):
                        touch = True
                out[(key, lid)] = (p.GetNetname(), conn, inside, touch)
    return out


def unkept_copy(board):
    """A copy of the saved board (reloaded from its file, with the .kicad_pro / .kicad_dru beside it, so the fills use the
    board's own rules) with its pour-trim keep-outs (TRIM_PREFIX) switched off, refilled natively; None when the board
    has no file."""
    import shutil
    import tempfile
    src = Path(board.GetFileName() or '')
    if not src.name or not src.exists():
        return None
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / ('unkept_' + src.name)
        shutil.copy(src, dst)
        for ext in ('.kicad_pro', '.kicad_dru'):
            if src.with_suffix(ext).exists():
                shutil.copy(src.with_suffix(ext), dst.with_suffix(ext))
        free = pcbnew.LoadBoard(str(dst))
    for z in free.Zones():          # disabled, not removed: a removed ZONE garbage-collected by Python breaks SWIG's
        if is_trim(z):              # type table for every board (KiCad 10.0.6, seen here)
            z.SetDoNotAllowZoneFills(False)
    free.BuildConnectivity()
    if not pcbnew.ZONE_FILLER(free).Fill(free.Zones()):
        raise RuntimeError('native zone fill failed')
    return free


def pad_pour_cuts(board, free=None):
    """pad_pour_cut instances (see the module docstring): pads with a thermal or solid connection to a same-net pour,
    inside its outline, that touch the fill of the board refilled without its zone-fill keep-out rule areas (free; by
    default unkept_copy(board)) but not the board's own fill: [dict(pad, net, lid, conn, at)]."""
    if not fill_keepouts(board):
        return []
    free = unkept_copy(board) if free is None else free
    if free is None:
        raise RuntimeError('pad_pour_cut needs the saved board (its fills without the keep-outs)')
    now = pad_contacts(board)
    was = pad_contacts(free)
    out = []
    pads = {f'{f.GetReference()}.{p.GetNumber()}#{k}': p for f in board.GetFootprints() for k, p in enumerate(f.Pads())}
    for (key, lid), (net, conn, inside, touch) in sorted(now.items()):
        if conn == 'none' or not inside or touch or not was.get((key, lid), (0, 0, 0, False))[3]:
            continue
        q = pads[key].GetPosition()
        out.append(dict(pad=key.split('#')[0], net=net, lid=lid, conn=conn, at=(q.x, q.y)))
    return out


def pours(board):
    """pour_sliver on every net's fills, pour_finger on GND's, pad_pour_cut (see the module docstring): instance
    dicts."""
    inst = []
    for c in pad_pour_cuts(board):
        inst.append(dict(cat='pad_pour_cut', net=c['net'], cls=net_class(c['net']), layer=board.GetLayerName(c['lid']),
                         x=round(mm(c['at'][0]), 4), y=round(mm(c['at'][1]), 4), pad=c['pad'], conn=c['conn']))
    for pc in pour_pieces(board):
        box = pc['box']
        kw = {k: v for k, v in pc.items() if k not in ('cat', 'net', 'lid', 'poly', 'box')}
        inst.append(dict(cat=pc['cat'], net=pc['net'], cls=net_class(pc['net']), layer=board.GetLayerName(pc['lid']),
                         x=round(mm((box[0] + box[2]) / 2), 2), y=round(mm((box[1] + box[3]) / 2), 2),
                         box=[round(mm(v), 2) for v in box], **kw))
    return inst


# --- the scan --------------------------------------------------------------------------------------------------------

class Copper:
    """Tracks, vias, pads and pours of a board, grouped for the scan (nm coordinates)."""

    def __init__(self, board):
        self.board = board
        self.segs, self.vias, self.pads = [], [], []
        for t in board.GetTracks():
            c = t.GetClass()
            if c == 'PCB_VIA':
                p = t.GetPosition()
                self.vias.append(dict(i=len(self.vias), pos=(p.x, p.y), net=t.GetNetname(),
                                      r=t.GetWidth(pcbnew.F_Cu) / 2, item=t))
            elif c in ('PCB_TRACK', 'PCB_ARC'):
                a, b = t.GetStart(), t.GetEnd()
                self.segs.append(dict(i=len(self.segs), lid=t.GetLayer(), layer=board.GetLayerName(t.GetLayer()),
                                      net=t.GetNetname(), a=(a.x, a.y), b=(b.x, b.y), w=t.GetWidth(),
                                      arc=c == 'PCB_ARC', uid=t.m_Uuid.AsString()))
        for s in self.segs:
            s['len'] = mm(dist(s['a'], s['b']))
        for fp in board.GetFootprints():
            for p in fp.Pads():
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    continue
                bb = p.GetBoundingBox()
                self.pads.append(dict(name=f'{fp.GetReference()}.{p.GetNumber()}', net=p.GetNetname(),
                                      pos=(p.GetPosition().x, p.GetPosition().y), pad=p,
                                      bb=(bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()),
                                      size=max(bb.GetWidth(), bb.GetHeight())))
        self.zones = defaultdict(list)
        for z in board.Zones():
            if not z.GetIsRuleArea():
                for lid in z.GetLayerSet().CuStack():
                    self.zones[(z.GetNetname(), lid)].append(z)
        self.by_ln = defaultdict(list)
        for s in self.segs:
            self.by_ln[(s['lid'], s['net'])].append(s)
        self.pads_by_net = defaultdict(list)
        for p in self.pads:
            self.pads_by_net[p['net']].append(p)
        self.vias_by_net = defaultdict(list)
        for v in self.vias:
            self.vias_by_net[v['net']].append(v)

    def pads_at(self, net, lid, pt, extra=0):
        out = []
        for p in self.pads_by_net.get(net, []):
            l, t, r, b = p['bb']
            if l - extra <= pt[0] <= r + extra and t - extra <= pt[1] <= b + extra and p['pad'].IsOnLayer(lid) \
                    and p['pad'].GetEffectiveShape(lid).Collide(P(pt), int(extra)):
                out.append(p)
        return out

    def in_zone(self, net, lid, pt, acc=0):
        return any(z.HitTestFilledArea(lid, P(pt), int(acc)) for z in self.zones.get((net, lid), []))

    def inside_one(self, s):
        """Whether segment s lies wholly inside one same-net pad or via (both ends in its copper)."""
        for v in self.vias_by_net.get(s['net'], []):
            if v['item'].IsOnLayer(s['lid']) and dist(s['a'], v['pos']) <= v['r'] and dist(s['b'], v['pos']) <= v['r']:
                return True
        at_b = {id(p) for p in self.pads_at(s['net'], s['lid'], s['b'])}
        return any(id(p) in at_b for p in self.pads_at(s['net'], s['lid'], s['a']))


def topology(board, cu):
    """Per (layer, net) track-end nodes and chains (runs through plain nodes), as scan() and the local-bump audit
    use them: (ends {(segment index, end): node}, nodes, plain(node), chains [(chain [(seg, a, b)], start node,
    end node)])."""
    # ---- nodes ---------------------------------------------------------------------------------------------------
    ends, nodes = {}, []
    for (lid, net), group in cu.by_ln.items():
        clusters = {}
        for s in group:
            for e, p in ((0, s['a']), (1, s['b'])):
                key = None
                gx, gy = round(p[0] / TOL), round(p[1] / TOL)
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        k = (gx + dx, gy + dy)
                        if k in clusters and dist(clusters[k]['p'], p) <= TOL:
                            key = k
                if key is None:
                    key = (gx, gy)
                    clusters[key] = dict(p=p, m=[])
                clusters[key]['m'].append((s, e))
        for cl in clusters.values():
            p = cl['p']
            ids = {s['i'] for s, _ in cl['m']}
            through = []
            for o in group:
                if o['i'] not in ids:
                    d, t = pt_seg(p, o['a'], o['b'])
                    L = dist(o['a'], o['b'])
                    if d <= TOL and TOL < t * L < L - TOL:
                        through.append(o)
            via, via_off = None, None
            for v in cu.vias_by_net.get(net, []):
                dv = dist(v['pos'], p)
                if dv <= TOL:
                    via = v
                    break
                if dv <= v['r'] and (via_off is None or dv < via_off[1]):
                    via_off = (v, dv)
            node = dict(p=p, lid=lid, layer=board.GetLayerName(lid), net=net, m=cl['m'], through=through, via=via,
                        via_off=via_off, pads=cu.pads_at(net, lid, p))
            nodes.append(node)
            for s, e in cl['m']:
                ends[(s['i'], e)] = node

    def plain(n):
        return len(n['m']) == 2 and not n['through'] and not n['pads'] and not n['via']

    # ---- chains (scan() measures staircases, jogs, U-turns, short hops on them) ----------------------------------
    seen, chains = set(), []
    for s in cu.segs:
        if s['i'] in seen or s['len'] == 0:
            continue
        cur, e, guard = s, 0, 0
        while guard < 100000:
            n = ends[(cur['i'], e)]
            if not plain(n):
                break
            ns, ne = [m for m in n['m'] if m[0]['i'] != cur['i']][0]
            if ns['i'] == s['i']:
                break
            cur, e = ns, 1 - ne
            guard += 1
        chain, start = [], ends[(cur['i'], e)]
        while True:
            seen.add(cur['i'])
            a, b = (cur['a'], cur['b']) if e == 0 else (cur['b'], cur['a'])
            chain.append((cur, a, b))
            n = ends[(cur['i'], 1 - e)]
            if not plain(n):
                break
            ns, ne = [m for m in n['m'] if m[0]['i'] != cur['i']][0]
            if ns['i'] in seen:
                break
            cur, e = ns, ne
        chains.append((chain, start, n))
    return ends, nodes, plain, chains


def scan(board):
    """Every instance of every category on the board, as dicts (cat, net, cls, layer, x, y and details)."""
    cu = Copper(board)
    inst = []
    poured = {n for (n, _) in cu.zones}

    def add(cat, net, layer, pt, **kw):
        inst.append(dict(cat=cat, net=net, cls=net_class(net), layer=layer, x=round(mm(pt[0]), 4),
                         y=round(mm(pt[1]), 4), **kw))

    # ---- nodes and chains (topology) -------------------------------------------------------------------------------
    ends, nodes, plain, chains = topology(board, cu)

    # segment ends at each via's centre on every layer: a path goes on through a via onto another layer
    via_ends = defaultdict(list)
    for v in cu.vias:
        for lid in CU4:
            for s in cu.by_ln.get((lid, v['net']), []):
                for e, q in ((0, s['a']), (1, s['b'])):
                    if dist(q, v['pos']) <= TOL:
                        via_ends[v['i']].append((s, e))

    def branches(n, skip, cross=True):
        """Every branch leaving node n as (segment, far point, far node): the other track ends at n, both halves of a
        track passing through n (a T), and at a via (cross=True) the track ends at its centre on the other layers."""
        out = []
        for s, e in n['m']:
            if s['i'] != skip:
                out.append((s, s['b'] if e == 0 else s['a'], ends[(s['i'], 1 - e)]))
        for o in n['through']:
            if o['i'] != skip:
                out += [(o, o['a'], ends[(o['i'], 0)]), (o, o['b'], ends[(o['i'], 1)])]
        if cross and n['via'] is not None:
            for s, e in via_ends[n['via']['i']]:
                if s['lid'] != n['lid'] and s['i'] != skip:
                    out.append((s, s['b'] if e == 0 else s['a'], ends[(s['i'], 1 - e)]))
        return out

    def node_kind(n):
        return 'via' if n['via'] else ('pad' if n['pads'] else ('T' if n['through'] or len(n['m']) > 2 else
                                                                 ('plain' if len(n['m']) == 2 else 'end')))

    def h45(a, b):
        return round(heading(a, b) / 45.0) * 45 % 360

    def turn_of(A, B):
        return min((B - A) % 360, 360 - (B - A) % 360)

    def tiny_step(mid, turn):
        return mid < 0.5 or mid * math.sin(math.radians(turn)) < 0.25

    def pour_run_inside(s, e):
        """mm of centre line inside the net's own fill (0.05 mm samples) along the run from end e of segment s back
        through plain nodes to the first junction, pad or via."""
        inside, cur, ce, guard = 0.0, s, e, 0
        while guard < 1000:
            a = cur['a'] if ce == 0 else cur['b']
            b = cur['b'] if ce == 0 else cur['a']
            n = max(1, int(math.ceil(cur['len'] / 0.05)))
            for k in range(n):
                t = (k + 0.5) / n
                q = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
                if cu.in_zone(cur['net'], cur['lid'], q):
                    inside += cur['len'] / n
            far = ends[(cur['i'], 1 - ce)]
            if not plain(far):
                break
            cur, ce = [(o, oe) for o, oe in far['m'] if o['i'] != cur['i']][0]
            guard += 1
        return inside

    # ---- track ends ----------------------------------------------------------------------------------------------
    for s in cu.segs:
        for e, p in ((0, s['a']), (1, s['b'])):
            n = ends[(s['i'], e)]
            others = [m for m in n['m'] if m[0]['i'] != s['i']]
            if n['via_off'] and not n['via'] and not n['pads'] and not any(
                    dist(q, n['via_off'][0]['pos']) <= TOL for o in cu.by_ln[(s['lid'], s['net'])] for q in (o['a'], o['b'])):
                # inside a via's copper off its centre, and no track on this layer reaches that centre (KiCad's
                # track_not_centered_on_via)
                add('via_offcentre_joint', s['net'], s['layer'], p, off_mm=round(mm(n['via_off'][1]), 4))
            elif not (n['via'] or n['via_off'] or n['pads'] or others or n['through']):
                far = ends[(s['i'], 1 - e)]
                near_ids = {m[0]['i'] for m in far['m']} | {o['i'] for o in far['through']}
                for o in cu.by_ln[(s['lid'], s['net'])]:
                    # (copper of a segment joined to this one at its other end is the stub's own: not a joint)
                    if o['i'] != s['i'] and o['i'] not in near_ids and \
                            pt_seg(p, o['a'], o['b'])[0] <= (o['w'] + s['w']) / 2:
                        add('overlap_only_joint', s['net'], s['layer'], p, to='track')
                        break
                else:
                    if any(dist(v['pos'], p) <= v['r'] + s['w'] / 2 for v in cu.vias_by_net.get(s['net'], [])):
                        add('overlap_only_joint', s['net'], s['layer'], p, to='via')
                    elif cu.pads_at(s['net'], s['lid'], p, extra=s['w'] / 2):
                        add('overlap_only_joint', s['net'], s['layer'], p, to='pad')
                    elif cu.in_zone(s['net'], s['lid'], p):
                        inside = pour_run_inside(s, e)
                        if inside > POUR_STUB:
                            add('pour_stub', s['net'], s['layer'], p, inside_mm=round(inside, 3))
            for pd in n['pads']:
                off = mm(dist(pd['pos'], p))
                if off > 0.1 and pd['size'] <= 2.0 / NM:
                    add('pad_end_offcentre', s['net'], s['layer'], p, pad=pd['name'], off_mm=round(off, 4))

    # ---- segments ------------------------------------------------------------------------------------------------
    for s in cu.segs:
        if s['len'] < MICRO:
            add('micro_segment', s['net'], s['layer'], s['a'], len_mm=round(s['len'], 4),
                end=(round(mm(s['b'][0]), 4), round(mm(s['b'][1]), 4)))
        elif s['len'] < max(mm(s['w']), SHORT) and not cu.inside_one(s):
            add('short_segment', s['net'], s['layer'], s['a'], len_mm=round(s['len'], 4),
                width=round(mm(s['w']), 3), end=(round(mm(s['b'][0]), 4), round(mm(s['b'][1]), 4)))
        if s['len'] == 0 or s['arc']:
            continue
        h = heading(s['a'], s['b'])
        d = dev45(h)
        lat = s['len'] * math.sin(math.radians(d))
        if d > OFF_DEG or lat > OFF_LAT:
            add('off_angle', s['net'], s['layer'], s['a'], end=(round(mm(s['b'][0]), 4), round(mm(s['b'][1]), 4)),
                dev_deg=round(d, 3), lat_mm=round(lat, 4))
        for pd in cu.pads_by_net.get(s['net'], []):
            l, t, r, b = pd['bb']
            if max(s['a'][0], s['b'][0]) < l or min(s['a'][0], s['b'][0]) > r or \
               max(s['a'][1], s['b'][1]) < t or min(s['a'][1], s['b'][1]) > b or not pd['pad'].IsOnLayer(s['lid']):
                continue
            sh = pd['pad'].GetEffectiveShape(s['lid'])
            if not sh.Collide(pcbnew.SHAPE_SEGMENT(P(s['a']), P(s['b']), 0), 0):
                continue
            ina, inb = sh.Collide(P(s['a']), 0), sh.Collide(P(s['b']), 0)
            if not ina and not inb:
                add('passes_through_pad', s['net'], s['layer'], s['a'], pad=pd['name'])
            elif ina and inb and s['len'] >= 0.2:
                add('segment_inside_pad', s['net'], s['layer'], s['a'], pad=pd['name'], len_mm=round(s['len'], 3))

    # ---- pairs: duplicates, overlaps, crossings ------------------------------------------------------------------
    for (lid, net), group in cu.by_ln.items():
        layer = board.GetLayerName(lid)
        for i, si in enumerate(group):
            ai, bi = si['a'], si['b']
            Li = dist(ai, bi)
            if Li == 0:
                continue
            ux, uy = (bi[0] - ai[0]) / Li, (bi[1] - ai[1]) / Li
            for sj in group[i + 1:]:
                aj, bj = sj['a'], sj['b']
                Lj = dist(aj, bj)
                if Lj == 0:
                    continue
                g = max(si['w'], sj['w']) + SLIT / NM
                if max(ai[0], bi[0]) + g < min(aj[0], bj[0]) or max(aj[0], bj[0]) + g < min(ai[0], bi[0]) or \
                   max(ai[1], bi[1]) + g < min(aj[1], bj[1]) or max(aj[1], bj[1]) + g < min(ai[1], bi[1]):
                    continue
                vx, vy = (bj[0] - aj[0]) / Lj, (bj[1] - aj[1]) / Lj
                if abs(ux * vy - uy * vx) < 1e-4:                       # parallel
                    off = abs((aj[0] - ai[0]) * uy - (aj[1] - ai[1]) * ux)
                    t1 = (aj[0] - ai[0]) * ux + (aj[1] - ai[1]) * uy
                    t2 = (bj[0] - ai[0]) * ux + (bj[1] - ai[1]) * uy
                    ov = min(Li, max(t1, t2)) - max(0, min(t1, t2))
                    other = (round(mm(aj[0]), 4), round(mm(aj[1]), 4), round(mm(bj[0]), 4), round(mm(bj[1]), 4))
                    if off <= TOL and ov > TOL:
                        dup = (dist(ai, aj) <= TOL and dist(bi, bj) <= TOL) or (dist(ai, bj) <= TOL and dist(bi, aj) <= TOL)
                        add('duplicate_segment' if dup else 'collinear_overlap', net, layer, ai,
                            end=(round(mm(bi[0]), 4), round(mm(bi[1]), 4)), other=other, overlap_mm=round(mm(ov), 4))
                    elif TOL < off < (si['w'] + sj['w']) / 2 + SLIT / NM and ov > max(si['w'], sj['w']) / 2:
                        add('side_by_side_overlap', net, layer, ai, end=(round(mm(bi[0]), 4), round(mm(bi[1]), 4)),
                            other=other, offset_mm=round(mm(off), 4), overlap_mm=round(mm(ov), 4))
                else:
                    x = interior_crossing(ai, bi, aj, bj)
                    if x is not None:
                        add('crossing_without_node', net, layer, x)

    # ---- nodes: angles, merges, width changes --------------------------------------------------------------------
    for n in nodes:
        p = n['p']
        br = [((s['b'][0] - p[0], s['b'][1] - p[1]) if e == 0 else (s['a'][0] - p[0], s['a'][1] - p[1]), s)
              for s, e in n['m']]
        for o in n['through']:
            br += [((o['a'][0] - p[0], o['a'][1] - p[1]), o), ((o['b'][0] - p[0], o['b'][1] - p[1]), o)]
        br = [x for x in br if x[0] != (0, 0)]
        holder = n['pads'][0]['pad'] if n['pads'] else (n['via']['item'] if n['via'] else None)
        pairs = []
        for i in range(len(br)):
            for j in range(i + 1, len(br)):
                if br[i][1]['i'] != br[j][1]['i']:
                    a = vang(br[i][0], br[j][0])
                    if a is not None:
                        pairs.append((a, i, j))
        pairs.sort()
        if pairs and pairs[0][0] < ANG_TOL:
            a, i, j = pairs[0]
            (u, s1), (v, s2) = br[i], br[j]
            short = min((u, s1), (v, s2), key=lambda q: math.hypot(*q[0]))
            far = (p[0] + short[0][0], p[1] + short[0][1])
            if holder is None or not holder.GetEffectiveShape(n['lid']).Collide(P(far), 0):
                add('fold_back', n['net'], n['layer'], p, at='free' if holder is None else 'pad/via')
        for a, i, j in pairs:                          # every acute pair, sharpest first (fix pass 5: not only the
            if a < ANG_TOL:                            # sharpest, which a pad may swallow while another is exposed)
                continue
            if a >= 90 - ANG_TOL:
                break
            (u, s1), (v, s2) = br[i], br[j]
            # apex of the wedge between the branches' inner edges
            nu, nv = math.hypot(*u), math.hypot(*v)
            bis = ((u[0] / nu + v[0] / nv), (u[1] / nu + v[1] / nv))
            nb = math.hypot(*bis)
            r = (s1['w'] + s2['w']) / 4 / math.sin(math.radians(a / 2))
            apex = (p[0] + bis[0] / nb * r, p[1] + bis[1] / nb * r)
            if holder is None or not holder.GetEffectiveShape(n['lid']).Collide(P(apex), 0):
                add('acute_angle', n['net'], n['layer'], p, deg=round(a, 2),
                    at='free' if holder is None else 'pad/via')
                break
        if len(br) == 2 and plain(n) and abs(vang(br[0][0], br[1][0]) - 180) <= ANG_TOL and br[0][1]['w'] == br[1][1]['w']:
            add('collinear_unmerged', n['net'], n['layer'], p, lens=(round(br[0][1]['len'], 3), round(br[1][1]['len'], 3)))
        if not n['pads'] and len({x[1]['w'] for x in br}) > 1:
            neck = plain(n)
            if neck:                                   # a pad-entry neck: the narrower segment ends in a pad near p
                (_, s1), (_, s2) = br
                nar = s1 if s1['w'] < s2['w'] else s2
                q = nar['b'] if dist(nar['a'], p) <= TOL else nar['a']
                if any(pd['pad'].GetEffectiveShape(n['lid']).Collide(P(p), int(1.0 / NM))
                       for pd in cu.pads_at(n['net'], n['lid'], q)):
                    neck = False
            add('neck_down' if neck else 'width_change_junction', n['net'], n['layer'], p,
                at='via' if n['via'] else ('free' if plain(n) else 'T'),
                widths=sorted({round(mm(x[1]['w']), 3) for x in br}))

    # ---- chains: staircases, jogs, U-turns, short hops -----------------------------------------------------------
    for chain, n0, n1 in chains:
        s0 = chain[0][0]
        hs = [round(heading(a, b) / 45.0) * 45 % 360 for _, a, b in chain]
        lens = [s['len'] for s, _, _ in chain]
        i = 0
        while i < len(hs) - 2:
            A, B = hs[i], hs[i + 1]
            if A == B:
                i += 1
                continue
            j = i + 2
            while j < len(hs) and hs[j] == (A if (j - i) % 2 == 0 else B):
                j += 1
            if j - i >= 3:
                turn = min((B - A) % 360, 360 - (B - A) % 360)
                seg = [round(x, 3) for x in lens[i:j]]
                p1 = chain[j - 1][2]
                def tiny(mid):
                    return mid < 0.5 or mid * math.sin(math.radians(turn)) < 0.25
                if j - i >= 4:
                    cat = 'staircase' if sum(1 for x in lens[i:j] if x < 1.0) >= 2 else 'extra_bends'
                    for k in range(i, j - 2):          # a tiny jog inside the longer run (P3-ROUTING_GEOMETRY-01)
                        if tiny(lens[k + 1]):
                            q = chain[k + 2][2]
                            add('tiny_jog', s0['net'], s0['layer'], chain[k][1],
                                end=(round(mm(q[0]), 4), round(mm(q[1]), 4)),
                                seglens=[round(x, 3) for x in lens[k:k + 3]], inside=cat)
                else:
                    cat = 'tiny_jog' if tiny(lens[i + 1]) else None
                if cat:
                    add(cat, s0['net'], s0['layer'], chain[i][1], end=(round(mm(p1[0]), 4), round(mm(p1[1]), 4)),
                        seglens=seg)
                i = j - 1
            else:
                i += 1
        cum = peak = 0
        for k in range(len(hs) - 1):
            d = (hs[k + 1] - hs[k]) % 360
            cum += d - 360 if d > 180 else d
            peak = max(peak, abs(cum))
        if peak >= 180:
            add('u_turn', s0['net'], s0['layer'], chain[0][1], path_mm=round(sum(lens), 3))
        if s0['net'] != 'GND' and n0['via'] is not None and n1['via'] is not None and n0['via'] is not n1['via'] \
                and sum(lens) < 3.0:
            add('short_layer_hop', s0['net'], s0['layer'], n0['p'], hop_mm=round(sum(lens), 3))
        # compound tiny jog (fix pass 6, P6-ROUTING_GEOMETRY-02): P, M1..Mk (k >= 2), Q with Q back on P's heading and
        # every middle segment off it (an A,B,C,A knee: the A,B,A test above sees a one-segment middle only), whose
        # middle is < 0.5 mm in all or whose Q runs < 0.25 mm off P's line
        for i in range(len(hs) - 3):
            for j in range(i + 1, len(hs)):
                if hs[j] != hs[i]:
                    continue
                if j - i - 1 >= 2 and dist(chain[i][1], chain[i][2]) > 0:
                    a0, a1, q0 = chain[i][1], chain[i][2], chain[j][1]
                    off = mm(abs((q0[0] - a0[0]) * (a1[1] - a0[1]) - (q0[1] - a0[1]) * (a1[0] - a0[0])) / dist(a0, a1))
                    mid = sum(lens[i + 1:j])
                    if round(mid, 4) < 0.5 or round(off, 4) < 0.25:
                        q1 = chain[j][2]
                        add('tiny_jog', s0['net'], s0['layer'], chain[i][1], end=(round(mm(q1[0]), 4), round(mm(q1[1]), 4)),
                            seglens=[round(x, 3) for x in lens[i:j + 1]], compound=j - i - 1, mid_mm=round(mid, 3),
                            offset_mm=round(off, 3))
                break                                  # the first return to P's heading closes the window
        # chain detour on a net with a pour (fix pass 6, P6-DOCS-01): the net-level detour test cannot judge a poured
        # net, so every run between two junctions (pads, vias, T nodes) is measured against the octilinear distance of
        # its ends
        if s0['net'] in poured:
            pa, pb = chain[0][1], chain[-1][2]
            dx, dy = abs(mm(pb[0] - pa[0])), abs(mm(pb[1] - pa[1]))
            octile = max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)
            L = sum(lens)
            if L - octile > CHAIN_DETOUR_SLACK and L > CHAIN_DETOUR_MAX * octile:
                add('chain_detour', s0['net'], s0['layer'], pa, end=(round(mm(pb[0]), 4), round(mm(pb[1]), 4)),
                    path_mm=round(L, 3), octile_mm=round(octile, 3), nseg=len(chain))

    # ---- poured nets: layer changes in series (fix pass 6, P6-DOCS-01) --------------------------------------------
    # a via of a poured net is a pure layer change when exactly two of the net's track ends meet at its centre, on two
    # layers, with no pad, no other track and no fill of its own pour on any layer: it joins nothing. Runs joined
    # through such vias form a path between two junctions; two or more pure vias in series are a layer hop (under
    # other copper and back, or across two layers) that the net-level extra_vias test cannot judge on a poured net
    pure = {}
    for v in cu.vias:
        if v['net'] not in poured:
            continue
        at_c = [(s, q) for lid in CU4 for s in cu.by_ln.get((lid, v['net']), []) for q in (s['a'], s['b'])
                if dist(q, v['pos']) <= TOL]
        near = [s for lid in CU4 for s in cu.by_ln.get((lid, v['net']), []) if pt_seg(v['pos'], s['a'], s['b'])[0] <= v['r']]
        if len(at_c) == 2 and len({s['lid'] for s, _ in at_c}) == 2 and len(near) == 2 and \
                not any(cu.pads_at(v['net'], lid, v['pos']) for lid in CU4) and \
                not any(cu.in_zone(v['net'], lid, v['pos'], v['r']) for lid in CU4):
            pure[v['i']] = v
    parent = {}

    def root(k):
        while parent.setdefault(k, k) != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k
    for c, (chain, n0, n1) in enumerate(chains):
        for n in (n0, n1):
            if n['via'] is not None and n['via']['i'] in pure:
                parent[root(('c', c))] = root(('v', n['via']['i']))
    groups = defaultdict(lambda: ([], []))
    for k in list(parent):
        g = groups[root(k)]
        (g[0] if k[0] == 'v' else g[1]).append(k[1])
    for vs, cs in groups.values():
        if len(vs) >= 2:
            first = min(pure[i]['pos'] for i in vs)
            add('pour_net_hop', pure[vs[0]]['net'], 'via', first, vias_n=len(vs),
                path_mm=round(sum(chains[c][0][k][0]['len'] for c in cs for k in range(len(chains[c][0]))), 3),
                at=sorted([round(mm(pure[i]['pos'][0]), 4), round(mm(pure[i]['pos'][1]), 4)] for i in vs))

    # ---- jogs and staircases through T, via and pad nodes (fix pass 5; the chains above see only plain nodes) ------
    for s in cu.segs:
        if s['len'] == 0 or s['arc']:
            continue
        n0, n1 = ends[(s['i'], 0)], ends[(s['i'], 1)]
        if (plain(n0) and plain(n1)) or cu.inside_one(s):
            continue
        B = h45(s['a'], s['b'])
        hit = None
        b0, b1 = branches(n0, s['i']), branches(n1, s['i'])
        for p_, pfar, _ in b0:
            A = h45(pfar, n0['p'])
            t = turn_of(A, B)
            if t not in (45, 90) or not tiny_step(s['len'], t):
                continue
            # P's line going on straight through n0 (or Q's back through n1) makes S a side branch off a straight run
            # (a via fan-out or a rung between two runs), not a step in a path
            if any(h45(n0['p'], f) == A for o, f, _ in b0 if o['lid'] == p_['lid']):
                continue
            for q_, qfar, _ in b1:
                if q_['i'] != p_['i'] and h45(n1['p'], qfar) == A and \
                        not any(h45(n1['p'], f) == (A + 180) % 360 for o, f, _ in b1 if o['lid'] == q_['lid']):
                    hit = (p_, q_, t)
                    break
            if hit:
                break
        if hit:
            p_, q_, t = hit
            add('tiny_jog', s['net'], s['layer'], n0['p'], end=(round(mm(n1['p'][0]), 4), round(mm(n1['p'][1]), 4)),
                mid_mm=round(s['len'], 3), offset_mm=round(s['len'] * math.sin(math.radians(t)), 3),
                at=f'{node_kind(n0)}/{node_kind(n1)}', via=p_['lid'] != s['lid'] or q_['lid'] != s['lid'])
    runs = []
    for s in cu.segs:
        if s['len'] == 0 or s['arc']:
            continue
        for e in (0, 1):
            a, b = (s['a'], s['b']) if e == 0 else (s['b'], s['a'])
            stack = [[(s, a, b, ends[(s['i'], 1 - e)], h45(a, b), s['len'])]]
            while stack:
                path = stack.pop()
                last = path[-1]
                ext = []
                if len(path) < 40:
                    used = {x[0]['i'] for x in path}
                    for o, far, fn in branches(last[3], last[0]['i'], cross=False):   # a staircase is on one layer
                        if o['i'] in used or dist(last[2], far) == 0:
                            continue
                        h = h45(last[2], far)
                        if (len(path) == 1 and turn_of(last[4], h) in (45, 90)) or \
                                (len(path) > 1 and h == path[-2][4]):
                            ext.append(path + [(o, last[2], far, fn, h, mm(dist(last[2], far)))])
                if ext:
                    stack += ext
                elif len(path) >= 4 and sum(1 for x in path if x[5] < 1.0) >= 2 and \
                        any(not plain(x[3]) for x in path[:-1]):
                    runs.append(path)
    kept = []
    for path in sorted(runs, key=len, reverse=True):
        ids = frozenset(x[0]['i'] for x in path)
        if not any(ids <= k for k, _ in kept):
            kept.append((ids, path))
    for ids, path in kept:
        x0 = path[0]
        start = min(path[0][1], path[-1][2])                      # one orientation, so a run is reported once
        end = path[-1][2] if start == path[0][1] else path[0][1]
        add('staircase', x0[0]['net'], x0[0]['layer'], start, at='node', seglens=[round(x[5], 3) for x in path],
            nodes=[node_kind(x[3]) for x in path[:-1]], end=(round(mm(end[0]), 4), round(mm(end[1]), 4)))

    # ---- vias ----------------------------------------------------------------------------------------------------
    gnd = [v['pos'] for v in cu.vias_by_net.get('GND', [])]
    for v in cu.vias:
        layers, tracked = set(), set()
        for lid in CU4:
            for s in cu.by_ln.get((lid, v['net']), []):
                if dist(s['a'], v['pos']) <= v['r'] or dist(s['b'], v['pos']) <= v['r']:
                    tracked.add(lid)
                elif pt_seg(v['pos'], s['a'], s['b'])[0] <= s['w'] / 2:
                    layers.add(lid)                                     # the via sits on the track's body
            if lid in tracked or cu.pads_at(v['net'], lid, v['pos']) or cu.in_zone(v['net'], lid, v['pos'], v['r']):
                layers.add(lid)
        if len(layers) < 2:
            add('dangling_via', v['net'], 'via', v['pos'])
        power = net_class(v['net']) == 'power' and v['net'] != 'GND'
        padl = {lid for lid in CU4 if cu.pads_at(v['net'], lid, v['pos'])}   # a via in a pad: a layer change too
        if (net_class(v['net']) in SIGNAL_CRITICAL or power) and len(tracked | padl) >= 2:
            g = min((dist(q, v['pos']) for q in gnd), default=None)
            if g is None or mm(g) > GND_REACH:
                add('power_via_no_gnd' if power else 'critical_via_no_gnd', v['net'], 'via', v['pos'],
                    gnd_mm=None if g is None else round(mm(g), 3), into_pad=bool(padl - tracked))
    for net, vs in cu.vias_by_net.items():                          # same-net vias whose rings overlap
        for i, v in enumerate(vs):
            for w in vs[i + 1:]:
                d = dist(v['pos'], w['pos'])
                if TOL < d < v['r'] + w['r'] - TOL:
                    add('via_overlap', net, 'via', min(v['pos'], w['pos']),
                        other=[round(mm(c), 4) for c in max(v['pos'], w['pos'])], centres_mm=round(mm(d), 4))
    # a via on a same-net track's body (fix pass 7, P7-ROUTING-03 / P7-DOCS-01): a track with neither end in the via
    # whose centre line passes through the via's centre (the via sits on its body), or whose copper overlaps the via's
    # copper on a layer where no track of the net ends at the via's centre (the via has no node there): the two are
    # joined by overlap only. Where the via also lies in its own net's fill on that layer the fill makes the joint
    # (information)
    for v in cu.vias:
        for lid in CU4:
            if not v['item'].IsOnLayer(lid):
                continue
            group = cu.by_ln.get((lid, v['net']), [])
            node_here = any(dist(q, v['pos']) <= TOL for o in group for q in (o['a'], o['b']))
            for s in group:
                d = pt_seg(v['pos'], s['a'], s['b'])[0]
                if dist(s['a'], v['pos']) > v['r'] and dist(s['b'], v['pos']) > v['r'] and \
                        (d <= s['w'] / 2 + TOL or (d < v['r'] + s['w'] / 2 - TOL and not node_here)):
                    in_fill = cu.in_zone(v['net'], lid, v['pos'], v['r'])
                    add('via_on_track_in_fill' if in_fill else 'via_on_track', v['net'], board.GetLayerName(lid),
                        v['pos'], off_mm=round(mm(d), 4), track=[round(mm(c), 4) for c in s['a'] + s['b']])

    # ---- connectivity: dead copper and loops -----------------------------------------------------------------------
    for net, nc in sorted(collect(board).items()):
        pieces, dvias = dead(nc)
        for i, segs in sorted(pieces.items()):
            t = nc.tracks[i]
            for s0, s1 in segs:
                if (s1 - s0) * dist(t['a'], t['b']) <= TOL:
                    continue
                p = (t['a'][0] + s1 * (t['b'][0] - t['a'][0]), t['a'][1] + s1 * (t['b'][1] - t['a'][1]))
                add('dead_copper', net, board.GetLayerName(t['lid']), p,
                    len_mm=round(mm((s1 - s0) * dist(t['a'], t['b'])), 4))
        for j in dvias:
            add('dead_copper', net, 'via', nc.vias[j]['pos'])
        for x, y, lid in loops(nc):
            add('track_loop', net, board.GetLayerName(lid), (x, y))
        if nc.zones:
            continue
        r = net_route(nc)
        if r['pads'] < 2:
            continue
        kw = dict(pads=r['pads'], first=r['first'], len_mm=round(r['len'], 2), mst_mm=round(r['mst'], 2),
                  ratio=round(r['len'] / r['mst'], 2) if r['mst'] > 0 else None, vias=r['vias'], need=r['need'])
        if r['len'] > DETOUR_MAX * r['mst'] and r['len'] - r['mst'] > DETOUR_SLACK:
            add('detour', net, 'net', r['at'], **kw)
        if r['vias'] > r['need'] + VIA_SLACK:
            add('extra_vias', net, 'net', r['at'], **kw)
    inst += pours(board)
    return inst


def gated(d):
    return d['cat'] in RULE or d['cat'] in POUR or (d['cat'] in HYGIENE + REMOVABLE and d['cls'] in CRITICAL)


def _figures(d):
    """The measured route figures an entry quotes for a detour / extra_vias instance (ROUTE_FIGURES), else None."""
    if d['cat'] not in MEASURED_CATS or d['net'] not in ROUTE_FIGURES:
        return None
    L, n = ROUTE_FIGURES[d['net']]
    return dict(len_mm=L, vias=n)


def evaluate(inst, allowlist=None):
    """Split the instances into failures, allowed ones and stale allowlist entries."""
    allowlist = ALLOWLIST if allowlist is None else allowlist
    used = [False] * len(allowlist)
    failures, allowed = [], []
    for d in inst:
        hit = None
        for k, e in enumerate(allowlist):
            cat, net, layer, xy, reason = e[:5]
            if cat == d['cat'] and net == d['net'] and layer == d['layer'] and \
                    math.hypot(xy[0] - d['x'], xy[1] - d['y']) <= 0.02:
                hit = k
                break
        if hit is not None:
            used[hit] = True
            allowed.append(dict(d, reason=allowlist[hit][4], measured=allowlist[hit][5] if len(allowlist[hit]) > 5
                                else _figures(d)))
        elif gated(d):
            failures.append(d)
    stale = [e for e, u in zip(allowlist, used) if not u]
    return failures, allowed, stale


def leftover_check(inst, leftovers=None):
    """(recorded, missing, stale): the non-critical LEFTOVER_CATS instances with a LEFTOVERS entry, those without one,
    and the entries that match no instance."""
    leftovers = LEFTOVERS if leftovers is None else leftovers
    used = [False] * len(leftovers)
    recorded, missing = [], []
    for d in inst:
        if d['cat'] not in LEFTOVER_CATS or d['cls'] in CRITICAL:
            continue
        hit = None
        for k, e in enumerate(leftovers):
            cat, net, layer, xy, reason = e[:5]
            if cat == d['cat'] and net == d['net'] and layer == d['layer'] and \
                    math.hypot(xy[0] - d['x'], xy[1] - d['y']) <= 0.02:
                hit = k
                break
        if hit is None:
            missing.append(d)
        else:
            used[hit] = True
            recorded.append(dict(d, reason=leftovers[hit][4], measured=leftovers[hit][5] if len(leftovers[hit]) > 5
                                 else _figures(d)))
    return recorded, missing, [e for e, u in zip(leftovers, used) if not u]


def nognd_audit(board, allowed, search=None):
    """For every allowed critical_via_no_gnd instance, the project's GND via spot search on this board (default
    m3_design/r7_hygiene.gnd_spots, the search gnd_vias' fine pass runs): [(instance, (spot, diameter, distance))] for
    each one where a legal spot within GND_REACH exists, i.e. whose allowlist reason no longer holds."""
    if search is None:
        root = Path(__file__).resolve().parents[1]
        for d in (root / 'm3_design', root / 'tools'):
            if str(d) not in sys.path:
                sys.path.insert(0, str(d))
        import r7_hygiene as hy                     # noqa: E402 (board-specific search, imported only here)

        def search(b, q):
            return hy.gnd_spots(b, q, GND_REACH, first=True)
    out = []
    for d in allowed:
        if d['cat'] != 'critical_via_no_gnd':
            continue
        hit = search(board, (d['x'], d['y']))
        if hit:
            out.append((d, hit[0]))
    return out


MEASURED_CATS = ('detour', 'extra_vias')
CHAIN_MEASURED = ('chain_detour', 'pour_net_hop')   # entries carry a sixth element dict(path_mm[, vias])
MEASURED_LEN_TOL = 0.05          # mm


def measured_check(entries_hit):
    """For every allowed or recorded detour / extra_vias instance (dicts from evaluate / leftover_check, carrying the
    entry's `measured` = dict(len_mm, vias)): [(instance, problem)] where the entry quotes no measured figures or
    figures that are not the present route's (route length within MEASURED_LEN_TOL, vias exactly). An entry's search
    result and reason describe one route; when the copper changes, the entry is stale even though its anchor (the
    net's first pad) still matches."""
    out = []
    for d in entries_hit:
        if d['cat'] in CHAIN_MEASURED:          # fix pass 6: the run's own length (and via count) for a poured net
            m = d.get('measured')
            if not m or 'path_mm' not in m:
                out.append((d, 'no measured path_mm in the entry'))
            elif abs(m['path_mm'] - d['path_mm']) > MEASURED_LEN_TOL or m.get('vias', d.get('vias_n')) != d.get('vias_n'):
                out.append((d, f"entry quotes {m['path_mm']} mm{' / ' + str(m['vias']) + ' vias' if 'vias' in m else ''}, "
                               f"the board has {d['path_mm']} mm{' / ' + str(d['vias_n']) + ' vias' if 'vias_n' in d else ''}"))
            continue
        if d['cat'] not in MEASURED_CATS:
            continue
        m = d.get('measured')
        if not m:
            out.append((d, 'no measured len_mm / vias in the entry'))
        elif abs(m['len_mm'] - d['len_mm']) > MEASURED_LEN_TOL or m['vias'] != d['vias']:
            out.append((d, f"entry quotes {m['len_mm']} mm / {m['vias']} vias, the board has {d['len_mm']} mm / "
                           f"{d['vias']} vias"))
    return out


# --- re-measuring jog / staircase / short-segment reasons (fix pass 5, P5-ROUTING_GEOMETRY-04 (a)) -----------------
ALT_CATS = ('tiny_jog', 'staircase', 'short_segment', 'chain_detour')
ALT_STEP = 0.025                 # mm: bend-position sampling of the candidate redraws
NPTH_CLEAR = 0.26                # mm: copper to a non-plated hole (m3.kicad_dru 0.25 + Clearance's 0.01 margin)
ALT_SLACK = (1.1, 0.2)           # a candidate may be at most 1.1 x the window's length + 0.2 mm: a redraw that trades
                                 # the defect for a longer route is a detour, not a cleaner drawing
ALT_SLACK_POWER = (1.0, 0.0)     # on a power rail no longer than the present window (copper length is resistance,
                                 # inductance and, on a switching node, radiating area)
DIRS8 = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def _unit(k):
    ux, uy = DIRS8[k]
    n = math.hypot(ux, uy)
    return ux / n, uy / n


def path_defects(seq, w):
    """seq: [(direction index 0-7, length mm, same_layer)] of consecutive pieces of one path (a piece with
    same_layer False is a neighbour across a via: it joins jog tests only). The gate's own tests on the sequence:
    a turn sharper than 90 deg, a short piece (< max(w, SHORT), where not flagged exempt by a length of None), a tiny
    jog (A, B, A with the middle < 0.5 mm or offsetting < 0.25 mm) or a staircase (an A, B, A, B run of >= 4 same-layer
    pieces with >= 2 shorter than 1 mm). Returns the first defect found, or None."""
    for (k1, l1, s1), (k2, l2, s2) in zip(seq, seq[1:]):
        if s1 and s2 and min((k2 - k1) % 8, (k1 - k2) % 8) > 2:
            return 'acute'
    for k, l, s in seq:
        if s and l is not None and l < max(w, SHORT):
            return 'short'
    for i in range(len(seq) - 2):
        (a, _, _), (bk, lm, _), (c, _, _) = seq[i:i + 3]
        if a == c and a != bk and lm is not None:
            t = min((bk - a) % 8, (a - bk) % 8) * 45
            if lm < 0.5 or lm * math.sin(math.radians(t)) < 0.25:
                return 'tiny_jog'
    for i in range(len(seq) - 3):                  # fix pass 6: a 2+ piece middle (A, B, C, A knee)
        for j in range(i + 1, len(seq)):
            if seq[j][0] != seq[i][0]:
                continue
            mids = seq[i + 1:j]
            if len(mids) >= 2 and all(l is not None and s for _, l, s in mids):
                ux, uy = _unit(seq[i][0])
                vx = sum(_unit(k)[0] * l for k, l, _ in mids)
                vy = sum(_unit(k)[1] * l for k, l, _ in mids)
                if round(sum(l for _, l, _ in mids), 4) < 0.5 or round(abs(vx * uy - vy * ux), 4) < 0.25:
                    return 'tiny_jog'
            break
    i = 0
    while i < len(seq) - 3:
        j = i + 2
        while j < len(seq) and seq[j][2] and seq[j][0] == seq[j - 2][0] and seq[j][0] != seq[j - 1][0]:
            j += 1
        if j - i >= 4 and all(s for _, _, s in seq[i:j]) and \
                sum(1 for _, l, _ in seq[i:j] if l is not None and l < 1.0) >= 2:
            return 'staircase'
        i += 1
    return None


def _dir_of(a, b):
    """Direction index of the 0/45/90 vector a -> b (nm), or None."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    for k, (ux, uy) in enumerate(DIRS8):
        if ux == 0 and abs(dx) <= 2 and dy * uy > 0:
            return k
        if uy == 0 and abs(dy) <= 2 and dx * ux > 0:
            return k
        if ux and uy and dx * ux > 0 and dy * uy > 0 and abs(abs(dx) - abs(dy)) <= 2:
            return k
    return None


def alt_window(board, d, cu=None):
    """The redraw window of an instance (tiny_jog, staircase, short_segment): its segments on its layer between its two
    reported points, plus one segment on each side where the joint is plain (two track ends only). Returns dict(net,
    lid, w, segs (dicts), w0, w1 (end points, nm), prev / next (the other branches at w0 / w1 as (direction leaving the
    window end, same_layer)), length mm) or None when the path is not found."""
    cu = cu or Copper(board)
    lid = board.GetLayerID(d['layer'])
    segs = cu.by_ln.get((lid, d['net']), [])
    p0 = (d['x'] / NM, d['y'] / NM)
    p1 = (d['end'][0] / NM, d['end'][1] / NM)

    def at(p, s):
        return dist(s['a'], p) <= TOL or dist(s['b'], p) <= TOL

    def other(s, p):
        return s['b'] if dist(s['a'], p) <= TOL else s['a']
    # BFS over segment end points from p0 to p1
    from collections import deque
    prev_of = {}
    q = deque([(p0, None)])
    seen = {(round(p0[0] / TOL), round(p0[1] / TOL))}
    found = None
    while q:
        p, via = q.popleft()
        if dist(p, p1) <= TOL:
            found = p
            break
        for s in segs:
            if at(p, s):
                n = other(s, p)
                key = (round(n[0] / TOL), round(n[1] / TOL))
                if key not in seen:
                    seen.add(key)
                    prev_of[key] = (p, s)
                    q.append((n, s))
    if found is None:
        return None
    path = []
    p = found
    while dist(p, p0) > TOL:
        pp, s = prev_of[(round(p[0] / TOL), round(p[1] / TOL))]
        path.append(s)
        p = pp
    path.reverse()
    w = max(s['w'] for s in path)

    def branches_at(p, exclude):
        same = [s for s in segs if s['i'] not in exclude and at(p, s)]
        thru = [s for s in segs if s['i'] not in exclude and not at(p, s) and pt_seg(p, s['a'], s['b'])[0] <= TOL]
        vias = [v for v in cu.vias_by_net.get(d['net'], []) if dist(v['pos'], p) <= TOL]
        pads = cu.pads_at(d['net'], lid, p)
        return same, thru, vias, pads

    def extend(p, exclude):
        same, thru, vias, pads = branches_at(p, exclude)
        if len(same) == 1 and not thru and not vias and not pads:
            return same[0]
        return None
    ids = {s['i'] for s in path}
    e0 = extend(p0, ids)
    if e0 is not None:
        path.insert(0, e0)
        ids.add(e0['i'])
        w0 = other(e0, p0)
    else:
        w0 = p0
    e1 = extend(p1, ids)
    if e1 is not None:
        path.append(e1)
        ids.add(e1['i'])
        w1 = other(e1, p1)
    else:
        w1 = p1

    def nbrs(p):
        same, thru, vias, pads = branches_at(p, ids)
        out = [(_dir_of(p, other(s, p)), s['len'], True) for s in same]
        out += [(_dir_of(p, q), mm(dist(p, q)), True) for s in thru for q in (s['a'], s['b'])]
        for v in vias:
            for (l2, n2), group in cu.by_ln.items():
                if n2 == d['net'] and l2 != lid:
                    out += [(_dir_of(p, other(s, p)), s['len'], False) for s in group if at(p, s)]
        return [x for x in out if x[0] is not None], bool(vias or pads), vias, pads
    nb0, held0, v0, pd0 = nbrs(w0)
    nb1, held1, v1, pd1 = nbrs(w1)
    return dict(net=d['net'], lid=lid, w=w, segs=path, w0=w0, w1=w1, prev=nb0, next=nb1, held=(v0, pd0, v1, pd1),
                length=sum(s['len'] for s in path))


def alt_candidates(win, step=None):
    """Every octilinear polyline of 1-3 segments from the window's w0 to w1 (bend positions on an ALT_STEP grid, or
    `step` mm) that passes path_defects together with the branches at both ends and is no longer than ALT_SLACK
    (ALT_SLACK_POWER on a power rail) allows, or the window's own 'cap': [[points nm]]."""
    step = ALT_STEP if step is None else step
    w0, w1, wn = win['w0'], win['w1'], win['w'] * NM
    D = (mm(w1[0] - w0[0]), mm(w1[1] - w0[1]))
    slack = ALT_SLACK_POWER if net_class(win['net']) == 'power' else ALT_SLACK
    cap = win.get('cap', win['length'] * slack[0] + slack[1])
    v0, pd0, v1, pd1 = win['held']

    def inside(pt, vias, pads):
        return any(dist(v['pos'], pt) <= v['r'] for v in vias) or \
            any(p['pad'].GetEffectiveShape(win['lid']).Collide(P(pt), 0) for p in pads)

    def ok_seq(dirs, lens):
        if sum(lens) > cap + 1e-9:
            return False
        L = list(lens)
        # a piece wholly inside the pad or via at either end is that copper, not a short segment
        a0, b0 = _unit(dirs[0]), _unit(dirs[-1])
        if inside((w0[0] + a0[0] * L[0] / NM, w0[1] + a0[1] * L[0] / NM), v0, pd0):
            L[0] = None
        if inside((w1[0] - b0[0] * lens[-1] / NM, w1[1] - b0[1] * lens[-1] / NM), v1, pd1):
            L[-1] = None
        core = [(k, l, True) for k, l in zip(dirs, L)]
        prevs = [((k + 4) % 8, l, s) for k, l, s in win['prev']] or [None]
        nexts = [(k, l, s) for k, l, s in win['next']] or [None]
        for p in prevs:
            for n in nexts:
                seq = ([p] if p else []) + core + ([n] if n else [])
                if path_defects(seq, wn):
                    return False
        return True
    out = []
    for k in range(8):                                         # one segment
        ux, uy = _unit(k)
        L = math.hypot(*D)
        if L > 0 and abs(D[0] - ux * L) < 1e-6 and abs(D[1] - uy * L) < 1e-6 and ok_seq([k], [L]):
            out.append([w0, w1])
    for k1 in range(8):                                        # two segments
        for k2 in range(8):
            if k2 in (k1, (k1 + 4) % 8):
                continue
            (a1, b1), (a2, b2) = _unit(k1), _unit(k2)
            det = a1 * b2 - a2 * b1
            l1 = (D[0] * b2 - D[1] * a2) / det
            l2 = (a1 * D[1] - b1 * D[0]) / det
            if l1 > 1e-6 and l2 > 1e-6 and ok_seq([k1, k2], [l1, l2]):
                out.append([w0, (w0[0] + a1 * l1 / NM, w0[1] + b1 * l1 / NM), w1])
    reach = math.hypot(*D) + 2.0
    for k1 in range(8):                                        # three segments
        for k2 in range(8):
            if k2 in (k1, (k1 + 4) % 8):
                continue
            for k3 in range(8):
                if k3 in (k2, (k2 + 4) % 8):
                    continue
                (a1, b1), (a2, b2), (a3, b3) = _unit(k1), _unit(k2), _unit(k3)
                det = a2 * b3 - a3 * b2
                if abs(det) < 1e-9:
                    continue
                for n in range(1, int(reach / step) + 1):
                    t = n * step
                    R = (D[0] - a1 * t, D[1] - b1 * t)
                    l2 = (R[0] * b3 - R[1] * a3) / det
                    l3 = (a2 * R[1] - b2 * R[0]) / det
                    if l2 > 1e-6 and l3 > 1e-6 and ok_seq([k1, k2, k3], [t, l2, l3]):
                        p1 = (w0[0] + a1 * t / NM, w0[1] + b1 * t / NM)
                        p2 = (p1[0] + a2 * l2 / NM, p1[1] + b2 * l2 / NM)
                        out.append([w0, p1, p2, w1])
    return out


EDGE_CLEAR = 0.5                 # mm: copper to the board edge (m3.kicad_pro min_copper_edge_clearance), at the outline
                                 # and at the internal Edge.Cuts holes (fix pass 7: alt_audit used to test the outline's
                                 # bounding box + 0.3 mm, so DRC could reject a redraw it called clean)
REF_PAIR = {pcbnew.B_Cu: pcbnew.In2_Cu, pcbnew.In2_Cu: pcbnew.B_Cu}   # strict: a pour on one is the other's reference
REF_GAP = 0.3                    # mm: the pours' clearance round a redraw (zone clearance 0.3 on the power pours)
NAMED_KEEPOUTS = ('U30_KEEPOUT', 'U31_KEEPOUT')   # m3.kicad_dru "R7 U30 / U31 keep-out": no non-GND track inside (rule
                                                   # areas that carry no track keep-out flag of their own)


def _clearance_class(clearance):
    if clearance is not None:
        return clearance
    root = Path(__file__).resolve().parents[1]
    for p in (root / 'm3_design', root / 'tools'):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import r7_hygiene as hy                     # noqa: E402 (board-specific rules, imported only here)
    return hy.Clearance


class RedrawCheck:
    """The tests a candidate redraw of a window passes to count as clean (alt_audit, bump_audit): every other net's
    copper (m3_design/r7_hygiene.Clearance: m3.kicad_dru incl. the pyro rules, bare test pads 1.0 mm, Tag-Connect
    0.508 mm, +0.01 mm), every track keep-out rule area and the module keep-outs for non-GND nets, NPTH_CLEAR from every
    non-plated hole, EDGE_CLEAR from the board outline and its Edge.Cuts holes. strict (bump_audit, fix pass 7) adds
    three conservative tests, so that a removable bump is one a redraw clears without a judgement call: the redraw
    enters no other net's power-pour fill (it could cut that pour; the GND pours refill round it), threads between the
    two pads of no two-pad part, touches no same-net copper but the branches at its two ends (no new crossing,
    overlap or pass through a pad or via), and on B.Cu / In2 comes no nearer a critical signal track on the paired layer
    (whose reference that pour is) than the window's present copper does."""

    def __init__(self, board, clearance=None):
        self.board = board
        self.clr = _clearance_class(clearance)(board)
        self.keep = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowTracks()]
        self.named = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetZoneName() in NAMED_KEEPOUTS]
        self.npth = [((f_p.GetPosition().x, f_p.GetPosition().y), max(f_p.GetDrillSize().x, f_p.GetDrillSize().y) / 2)
                     for f in board.GetFootprints() for f_p in f.Pads() if f_p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
        self.edges, self.circles, self.outline = [], [], None
        bb = board.GetBoardEdgesBoundingBox()
        if bb.GetWidth() > 0 and bb.GetHeight() > 0:      # (a test board has no outline: no edge test)
            poly = pcbnew.SHAPE_POLY_SET()
            board.GetBoardPolygonOutlines(poly, False)
            self.outline = poly
            for o in range(poly.OutlineCount()):
                for ch in [poly.Outline(o)] + [poly.Hole(o, h) for h in range(poly.HoleCount(o))]:
                    for k in range(ch.SegmentCount()):
                        e = ch.CSegment(k)
                        self.edges.append(((e.A.x, e.A.y), (e.B.x, e.B.y)))
            shapes = list(board.GetDrawings()) + [g for f in board.GetFootprints() for g in f.GraphicalItems()]
            for g in shapes:                             # the polygon approximates circles by chords: test them exactly
                if g.GetLayer() == pcbnew.Edge_Cuts and g.GetClass() == 'PCB_SHAPE' and \
                        g.GetShape() == pcbnew.SHAPE_T_CIRCLE:
                    c = g.GetCenter()
                    self.circles.append(((c.x, c.y), g.GetRadius()))
        self.pours = defaultdict(list)                   # strict: other nets' power-pour fills, per layer
        for z in board.Zones():
            if not z.GetIsRuleArea() and z.GetNetname() != 'GND':
                for lid in z.GetLayerSet().CuStack():
                    self.pours[lid].append((z.GetNetname(), z))
        self.two_pad = []                                # strict: the axis between a two-pad part's pads, per layer
        for f in board.GetFootprints():
            ps = [q for q in f.Pads() if q.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
            if len(ps) == 2:
                for lid in CU4:
                    if all(q.IsOnLayer(lid) for q in ps):
                        self.two_pad.append((lid, ps))

    def local(self, box):
        """A copy of the clearance model holding only the items that touch box (nm): fast repeated tests in one area."""
        import copy
        c = copy.copy(self.clr)
        c.items = [it for it in self.clr.items if not (it[3][2] < box[0] or it[3][0] > box[2] or it[3][3] < box[1] or
                                                       it[3][1] > box[3])]
        c.gone = set()
        return c

    def why(self, net, lid, pts, w, gone=(), clr=None, strict=False, cu=None, ends=(), present=()):
        """The first reason the polyline pts (nm) of net on lid, width w (nm), is not clean, or None. present: the
        window's own segments (dicts), for the reference test (strict, with cu)."""
        clr = clr or self.clr
        clr.gone = set(gone)
        try:
            for a, c in zip(pts, pts[1:]):
                if clr.why(net, lid, a, c, w) is not None:
                    return 'clearance'
                seg = pcbnew.SHAPE_SEGMENT(P(a), P(c), int(w))
                if any(z.IsOnLayer(lid) and z.Outline().Collide(seg, 0) for z in self.keep):
                    return 'keep-out'
                if net != 'GND' and any(z.IsOnLayer(lid) and z.Outline().Collide(seg, 0) for z in self.named):
                    return 'module keep-out'
                if any(pt_seg(h, a, c)[0] - r - w / 2 < NPTH_CLEAR / NM for h, r in self.npth):
                    return 'npth'
                if self.outline is not None:
                    if not (self.outline.Contains(P(a)) and self.outline.Contains(P(c))):
                        return 'edge'
                    lim = EDGE_CLEAR / NM + w / 2
                    x0, x1, y0, y1 = min(a[0], c[0]) - lim, max(a[0], c[0]) + lim, min(a[1], c[1]) - lim, \
                        max(a[1], c[1]) + lim
                    for e0, e1 in self.edges:
                        if max(e0[0], e1[0]) < x0 or min(e0[0], e1[0]) > x1 or max(e0[1], e1[1]) < y0 or \
                                min(e0[1], e1[1]) > y1:
                            continue
                        if _seg_seg(a, c, e0, e1) < lim:
                            return 'edge'
                    if any(pt_seg(h, a, c)[0] - r < lim for h, r in self.circles):
                        return 'edge'
                if not strict:
                    continue
                for n2, z in self.pours.get(lid, ()):
                    if n2 != net and z.GetFilledPolysList(lid).Collide(seg, 0):
                        return f'enters the {n2} pour'
                for l2, ps in self.two_pad:
                    if l2 != lid:
                        continue
                    q0, q1 = (ps[0].GetPosition().x, ps[0].GetPosition().y), (ps[1].GetPosition().x, ps[1].GetPosition().y)
                    x = interior_crossing(a, c, q0, q1)
                    if x is not None and not any(q.GetEffectiveShape(lid).Collide(P(x), 0) for q in ps):
                        return 'between the pads of ' + ps[0].GetParentFootprint().GetReference()
                if cu is not None and lid in REF_PAIR:
                    # a critical signal track on the paired layer takes this layer's pour as its reference (B.Cu over
                    # In2, In2 under B.Cu; tools/critical_reference.py): a redraw may not cut that pour where the
                    # window's present copper does not already (fix pass 7: LED_RED's and SERVO2_MCU's "removable"
                    # bumps did, 465 / 179 samples)
                    reach = w / 2 + REF_GAP / NM
                    for (l2, n2), group in cu.by_ln.items():
                        if l2 != REF_PAIR[lid] or n2 == net or net_class(n2) not in SIGNAL_CRITICAL:
                            continue
                        for o in group:
                            r = reach + o['w'] / 2
                            if _seg_seg(a, c, o['a'], o['b']) < r and \
                                    not any(_seg_seg(q['a'], q['b'], o['a'], o['b']) < r for q in present):
                                return f'cuts the reference of {n2}'
                if cu is not None:
                    for o in cu.by_ln.get((lid, net), ()):
                        if o['uid'] in gone or any(dist(o['a'], q) <= TOL or dist(o['b'], q) <= TOL or
                                                   pt_seg(q, o['a'], o['b'])[0] <= TOL for q in ends):
                            continue
                        if _seg_seg(a, c, o['a'], o['b']) < (w + o['w']) / 2:
                            return 'same-net track'
                    for v in cu.vias_by_net.get(net, ()):
                        if not any(dist(v['pos'], q) <= TOL for q in ends) and pt_seg(v['pos'], a, c)[0] < v['r'] + w / 2:
                            return 'same-net via'
                    for pd in cu.pads_by_net.get(net, ()):
                        if pd['pad'].IsOnLayer(lid) and not any(pd['pad'].GetEffectiveShape(lid).Collide(P(q), 0)
                                                                for q in ends) and \
                                pd['pad'].GetEffectiveShape(lid).Collide(seg, 0):
                            return 'same-net pad'
            return None
        finally:
            clr.gone = set()


def _headings(win):
    """The direction indices of a window's segments walked from w0 to w1."""
    p, out = win['w0'], []
    for s in win['segs']:
        q = s['b'] if dist(s['a'], p) <= TOL else s['a']
        out.append(_dir_of(p, q))
        p = q
    return out


def _seg_seg(a, b, c, d):
    """Shortest distance (nm) between segments ab and cd."""
    if interior_crossing(a, b, c, d) is not None:
        return 0.0
    return min(pt_seg(a, c, d)[0], pt_seg(b, c, d)[0], pt_seg(c, a, b)[0], pt_seg(d, a, b)[0])


def alt_audit(board, entries_hit, clearance=None):
    """For every allowed or recorded tiny_jog / staircase / short_segment / chain_detour instance (fix pass 6: for a
    chain_detour the candidate must also end the detour: no longer than CHAIN_DETOUR_MAX x the octilinear distance or
    CHAIN_DETOUR_SLACK beyond it): a redraw of its window (alt_window) by any alt_candidates polyline that passes
    RedrawCheck (every other net's copper, keep-outs, non-plated holes, the board edge; fix pass 7: the true outline at
    EDGE_CLEAR and the module keep-outs). Pads and vias stay where they are (a reason that rests on moving them is
    beyond this test). [(instance, candidate points mm)] for each instance whose reason no longer holds; an instance
    whose window cannot be found is reported with candidate None."""
    cu = Copper(board)
    out = []
    chk = None
    for d in entries_hit:
        if d['cat'] not in ALT_CATS or 'end' not in d:
            continue
        win = alt_window(board, d, cu)
        if win is None:
            out.append((d, None))
            continue
        shape = None
        if d['cat'] == 'chain_detour':          # the redraw must end the detour, not merely be no longer
            o = d['octile_mm']
            win['cap'] = min(win['length'], max(CHAIN_DETOUR_MAX * o, o + CHAIN_DETOUR_SLACK)) - 1e-6
            shape = _headings(win)              # fix pass 7: nor be the same drawing with its bends moved closer to its
                                                # obstacle (P7-ROUTING-04: that passes the metric, not the detour)
        if chk is None:
            chk = RedrawCheck(board, clearance)
        uid = {s['uid'] for s in win['segs']}
        found = None
        for pts in alt_candidates(win):
            if shape is not None and [_dir_of(a, c) for a, c in zip(pts, pts[1:])] == shape:
                continue
            if chk.why(d['net'], win['lid'], pts, win['w'], gone=uid) is None:
                found = [(round(mm(p[0]), 4), round(mm(p[1]), 4)) for p in pts]
                break
        if found:
            out.append((d, found))
    return out


# --- local bumps (fix pass 7, P7-ROUTING-01) ------------------------------------------------------------------------
# chain_detour judges a whole run between two junctions and alt_audit accepts only a redraw that ends the detour, so a
# bump inside a longer run (or a redraw that removes part of a detour) was invisible to the gate. bump_audit slides a
# window over every run of every critical net (poured nets included) and asks the redraw machinery for a shorter one.
BUMP_EXCESS = 0.3                # mm: a window longer than the octilinear distance of its ends by more than this,
BUMP_RATIO = 1.15                # and more than this factor,
BUMP_BACK = 0.05                 # and longer than the Manhattan distance of its ends by more than this (it turns back:
                                 # a monotone L or Z that a diagonal would shorten is a drawing style, not a bump),
BUMP_SAVE = 0.15                 # is a removable local bump when a 1-3 segment redraw at least this much shorter passes
                                 # RedrawCheck (strict) and path_defects with the branches at both ends
BUMP_MAXSEG = 8                  # segments per window
BUMP_STEP = 0.05                 # mm: bend sampling of the bump redraws


def _bump_window(cu, chain, i, j, L):
    """alt_candidates' window for segments i..j-1 of a chain: end points, the branches at both ends (across a via onto
    the other layers too), the vias and pads holding the ends."""
    segs = chain[i:j]
    s0 = segs[0][0]
    lid, net = s0['lid'], s0['net']
    w0, w1 = segs[0][1], segs[-1][2]
    ids = {s['i'] for s, _, _ in segs}

    def nbrs(p):
        out = []
        for s in cu.by_ln.get((lid, net), ()):
            if s['i'] in ids:
                continue
            if dist(s['a'], p) <= TOL:
                out.append((_dir_of(p, s['b']), s['len'], True))
            elif dist(s['b'], p) <= TOL:
                out.append((_dir_of(p, s['a']), s['len'], True))
            elif pt_seg(p, s['a'], s['b'])[0] <= TOL:
                out += [(_dir_of(p, q), mm(dist(p, q)), True) for q in (s['a'], s['b'])]
        vias = [v for v in cu.vias_by_net.get(net, ()) if dist(v['pos'], p) <= TOL]
        if vias:
            for (l2, n2), group in cu.by_ln.items():
                if n2 == net and l2 != lid:
                    for s in group:
                        if dist(s['a'], p) <= TOL:
                            out.append((_dir_of(p, s['b']), s['len'], False))
                        elif dist(s['b'], p) <= TOL:
                            out.append((_dir_of(p, s['a']), s['len'], False))
        return [x for x in out if x[0] is not None], vias, cu.pads_at(net, lid, p)
    nb0, v0, pd0 = nbrs(w0)
    nb1, v1, pd1 = nbrs(w1)
    return dict(net=net, lid=lid, w=s0['w'], segs=[s for s, _, _ in segs], w0=w0, w1=w1, prev=nb0, next=nb1,
                held=(v0, pd0, v1, pd1), length=L)


def bump_windows(chain):
    """[(excess mm, i, j, length mm, octilinear mm)] of every window of 2..BUMP_MAXSEG segments of one chain (one
    width) that turns back and exceeds the octilinear distance of its ends by BUMP_EXCESS and BUMP_RATIO."""
    out = []
    n = len(chain)
    for i in range(n):
        for j in range(i + 2, min(n, i + BUMP_MAXSEG) + 1):
            segs = chain[i:j]
            if len({s['w'] for s, _, _ in segs}) > 1:
                continue
            a, c = segs[0][1], segs[-1][2]
            L = sum(s['len'] for s, _, _ in segs)
            dx, dy = abs(mm(c[0] - a[0])), abs(mm(c[1] - a[1]))
            o = max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)
            if L - (dx + dy) > BUMP_BACK and L - o > BUMP_EXCESS and L > BUMP_RATIO * o:
                out.append((L - o, i, j, L, o))
    return out


def bump_audit(board, clearance=None, nets=None, step=BUMP_STEP):
    """Removable local bumps: for every chain (topology) of the nets selected (default: the critical classes), its
    bump_windows, largest excess first and skipping windows that overlap one already found, each searched for a 1-3
    segment redraw at least BUMP_SAVE shorter (alt_candidates with that cap, shortest first) that passes RedrawCheck
    (strict) and is not the window's own sequence of headings (that only moves the bends closer to their obstacle).
    Returns (instances, windows searched): one 'local_bump' instance per removable window, at its first
    point, with the window's and the redraw's lengths and the redraw's points (mm)."""
    cu = Copper(board)
    _, _, _, chains = topology(board, cu)
    chk = None
    out, searched = [], 0
    for chain, _, _ in chains:
        s0 = chain[0][0]
        net = s0['net']
        if not (net_class(net) in CRITICAL if nets is None else nets(net)):
            continue
        taken = []
        for ex, i, j, L, o in sorted(bump_windows(chain), key=lambda t: (-t[0], t[1], t[2])):
            if any(i < tj and ti < j for ti, tj in taken):
                continue
            searched += 1
            if chk is None:
                chk = RedrawCheck(board, clearance)
            win = _bump_window(cu, chain, i, j, L)
            win['cap'] = L - BUMP_SAVE
            r = (math.hypot(win['w1'][0] - win['w0'][0], win['w1'][1] - win['w0'][1]) + 3.0 / NM)
            box = (min(win['w0'][0], win['w1'][0]) - r, min(win['w0'][1], win['w1'][1]) - r,
                   max(win['w0'][0], win['w1'][0]) + r, max(win['w0'][1], win['w1'][1]) + r)
            clr = chk.local(box)
            uid = {s['uid'] for s in win['segs']}
            shape = [_dir_of(a, c) for _, a, c in chain[i:j]]
            found = None
            for pts in sorted(alt_candidates(win, step), key=lambda q: sum(dist(a, c) for a, c in zip(q, q[1:]))):
                if [_dir_of(a, c) for a, c in zip(pts, pts[1:])] == shape:
                    continue                    # the same drawing with its bends moved into its own clearance: tighter,
                                                # not a removed bump (P7-ROUTING-04's threshold artefact)
                if chk.why(net, s0['lid'], pts, win['w'], gone=uid, clr=clr, strict=True, cu=cu,
                           ends=(win['w0'], win['w1']), present=win['segs']) is None:
                    found = pts
                    break
            if found is None:
                continue
            taken.append((i, j))
            out.append(dict(cat='local_bump', net=net, cls=net_class(net), layer=s0['layer'],
                            x=round(mm(win['w0'][0]), 4), y=round(mm(win['w0'][1]), 4),
                            end=(round(mm(win['w1'][0]), 4), round(mm(win['w1'][1]), 4)), path_mm=round(L, 3),
                            octile_mm=round(o, 3), nseg=j - i,
                            redraw_mm=round(sum(mm(dist(a, c)) for a, c in zip(found, found[1:])), 3),
                            candidate=[(round(mm(p[0]), 4), round(mm(p[1]), 4)) for p in found]))
    return out, searched


def summary(inst):
    rows = []
    for cat in RULE + HYGIENE + REMOVABLE + POUR + INFO:
        L = [d for d in inst if d['cat'] == cat]
        if not L:
            continue
        by_layer = Counter(d['layer'] for d in L)
        by_cls = Counter(d['cls'] for d in L)
        rows.append(f"  {cat:22s} {len(L):5d}  layers {dict(sorted(by_layer.items()))}  classes {dict(sorted(by_cls.items()))}")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board', nargs='?', type=Path, default=Path(__file__).resolve().parents[1] /
                    'm3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--report', type=Path, help='write every instance, failure and allowed exception as JSON')
    ap.add_argument('--list', action='store_true', help='print every instance, not only the failures')
    ap.add_argument('--routes', action='store_true', help='print every pad-to-pad connection of every net without a '
                    'pour: copper length, octilinear distance, ratio, vias')
    ap.add_argument('--bumps-all', action='store_true', help='also search the non-critical nets for removable local '
                    'bumps (information, local_bump_review; slow)')
    args = ap.parse_args()
    board = pcbnew.LoadBoard(str(args.board))
    if args.routes:
        for net, nc in sorted(collect(board).items()):
            if not nc.zones:
                r = net_route(nc)
                if r['pads'] >= 2:
                    print(f"route {net:22s} {r['pads']:2d} pads {r['len']:8.2f} mm  octile MST {r['mst']:7.2f}  ratio "
                          f"{r['len'] / r['mst'] if r['mst'] else 0:5.2f}  vias {r['vias']:2d} (needs {r['need']})")
    inst = scan(board)
    bumps, searched = bump_audit(board)              # fix pass 7: removable local bumps on the critical nets (gated)
    inst += bumps
    if args.bumps_all:
        more, n_more = bump_audit(board, nets=lambda n: net_class(n) not in CRITICAL)
        inst += [dict(d, cat='local_bump_review') for d in more]
        searched += n_more
    failures, allowed, stale = evaluate(inst)
    print('routing hygiene: instances per category (per layer, per net class)')
    for row in summary(inst):
        print(row)
    if args.list:
        for d in inst:
            print('   ', json.dumps(d))
    for d in failures:
        print('FAIL', d['cat'], d['net'], d['layer'], (d['x'], d['y']),
              {k: v for k, v in d.items() if k not in ('cat', 'net', 'layer', 'x', 'y', 'cls')})
    for e in stale:
        print('FAIL stale allowlist entry (matches nothing):', e[:4])
    audit = nognd_audit(board, allowed)
    for d, (spot, dia, dist_) in audit:
        print('FAIL allowlisted critical_via_no_gnd has a legal GND via spot:', d['net'], (d['x'], d['y']),
              f'{dia} mm via at {spot}, {dist_:.3f} mm')
    recorded, missing, stale_left = leftover_check(inst)
    for d in missing:
        print('FAIL non-critical leftover without a recorded reason (LEFTOVERS):', d['cat'], d['net'], d['layer'],
              (d['x'], d['y']))
    for e in stale_left:
        print('FAIL stale LEFTOVERS entry (matches nothing):', e[:4])
    figures = measured_check(allowed + recorded)
    for d, why in figures:
        print('FAIL out-of-date measured figures:', d['cat'], d['net'], (d['x'], d['y']), why)
    alt = alt_audit(board, allowed + recorded)
    for d, pts in alt:
        print('FAIL', 'allowlisted' if d in allowed else 'recorded', d['cat'], d['net'], d['layer'], (d['x'], d['y']),
              'is removable: clean redraw' if pts else 'cannot be re-measured (window not found)', pts or '')
    bad = failures or stale or audit or missing or stale_left or figures or alt
    print(f'routing hygiene: {len(failures)} failing, {len(allowed)} allowlisted, {len(stale)} stale allowlist entries, '
          f'{len(audit)} out-of-date no-GND reasons, {len(recorded)} leftovers recorded ({len(missing)} unrecorded, '
          f'{len(stale_left)} stale), {len(figures)} out-of-date route figures, {len(alt)} removable jog / staircase / '
          f'short-segment / chain-detour exceptions, {len(bumps)} removable local bumps on critical nets '
          f'({searched} bump windows searched):', 'FAIL' if bad else 'OK')
    if args.report:
        args.report.write_text(json.dumps(dict(instances=inst, failures=failures, allowed=allowed,
                                               stale=[list(e) for e in stale],
                                               nognd_audit=[dict(d, spot=list(sp), via=dia, dist=dd)
                                                            for d, (sp, dia, dd) in audit],
                                               leftovers=recorded, leftovers_missing=missing,
                                               leftovers_stale=[list(e) for e in stale_left],
                                               measured_check=[dict(d, problem=w) for d, w in figures],
                                               alt_audit=[dict(d, candidate=p) for d, p in alt]), indent=1) + '\n')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
