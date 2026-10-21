# Spike (d) RF buses: progress log

Running log so a successor can resume. Scratch: `$SCRATCH/r8_design/spike_d_rf/` (session scratchpad).
This spike edits only `m3_design/r8_spikes/d_rf/` (brief).

## Log

- Read r8_plan, step 0-2 handoffs, R8_DECISIONS D1-D28, plan_partial, plan_cleansheet RF sections, check_r8,
  route_check header, the R7 strip copper.
- Findings before routing:
  - The seed's camera supply (U7 at (33.8, 29.2), TP71 at (38.4, 23.9)) sits within 5 mm of RF parts
    (R313/R315, FB31, C310): D17 restricted parts. Must be re-placed for F10 (to be measured on the scratch board).
  - Rigid strip GND vias (23.8, 17.7) and (23.2, 14.67) (R7's NSS-hop GND partners) bound the module-gap corridor:
    6 lanes fit at 0.5 mm pitch (x 20.6-23.1) but not with a fence via slot inside the gap.
  - Fence (D16, openings <= 2.7 mm): the R7 small parts R305 and C300 sit 0.2 mm south of FENCE_Y and block fence
    vias between the GNSS lanes; small shifts (R305 -0.13 mm, C300 -0.15 mm) are planned.
- Next: scratch base board (spike_base.py), then rf routing (rf_route_r8.py), then DRC / route_check / check_r8
  subsets.
- Base board built (`spike_base.py`): 247 rigid items kept; all 12 rigid groups equal R7 once two things hold:
  - m3.kicad_dru must sit beside the board when it is loaded (the filler takes the RF 0.25 mm gap from it);
  - at least one non-GND F.Cu pour must exist: with none, the native refill moves GND_F's boundary by a few µm along
    the RF lines and strip_gcpw flips single 0.01 mm samples (finding F-1 for the orchestrator; R6_BAT_IN_crossbar_F
    kept as a stand-in).
- Seed F10 separation failures measured: C310-TP71 2.38, C312-TP71 4.99, FB31-TP71 1.79, R313-U7 1.99, R315-U7 3.19,
  U31-TP71 3.50 mm.
- Pitfall found and fixed: `board.Save()` into another folder rewrote the scratch `m3.kicad_pro` with KiCad defaults
  (clearance 0.2, no minimum), so later loads filled and checked with wrong rules (an apparent strip_gcpw drift and false
  DRC clearance findings). Both scripts now save with `SaveBoard(..., aSkipSettings=True)` and copy the project files.
  With that, base and routed boards keep all 12 rigid digests, stable across load + refill.
- F-1 re-measured with correct rules: removing every non-GND F.Cu pour moves 15 of 744 strip_gcpw side samples by
  0.01-0.02 mm (4 of them inside 0.30 mm) - fill noise; any F.Cu power pour present (R8 will have them) avoids it.
- First routing pass (rf_route_r8.py): rigid OK, fence OK, rf_strip OK, stitching OK, F10 separation OK.
- Routing converged (rf_route_r8.py): rigid 12/12 equal R7, fence OK (4 openings 2.0-2.6 mm), rf_strip / stitching /
  F10 separation / rf_gnd_reach / launch / module ground / rf_grounds OK; DRC 0 and route_check 0 on spike nets/parts;
  byte-identical rebuilds (KIID seeds 8401/8402).
- Fixes along the way: SCK passes via (23.8, 17.7) on its east side (a west pass was a local_bump); MOSI/NSS straight
  (jogs were bumps); trio steps 0.4 east inside the strip to kill a MISO-MOSI GND finger; square corners at the trio's
  module end (45-degree ones made S,SE,S,SE staircases); R312 at y 7.15 (courtyard vs U31); GND stitch vias (22.1,26.7)
  and (24.15,26.5) outside the strip.
- Status cluster placed (D3 primary): J2 to the west edge (2.35, 42.75) rot -90, R32/LED1 row y 41.8, R33/LED2 row
  y 44.0; LED lanes F.Cu, 0 vias. Tab windows: left 0.5-6.0 and 48.5-117.5 (seed 41.5-117.5), right 0.5-25.0.
- Findings recorded for RESULT: limiter LNA_EN / VCC_RF detours are keep-out forced (D11 redraw cannot clear them);
  CAM_FAULT_N / CAM_PWR_EN cannot escape on F.Cu between DIO1 and NRST (U12 bounds NRST at x 33.4) -> inward dives;
  check_r8 inner_signal fails on the rigid CH1 In2 ARM1_SENSE link (D20 vs D9).
- Next: final run with TP71 at (33.6, 50.0), run_spike.sh, image, RESULT.md.
- DONE. Final run (`run_spike.sh`): base 191397e4..., routed 485cd0c4... (byte-identical on repeat); rigid 12/12, gcpw
  0/744 samples differ, fence / rf_strip / F10 OK, DRC 0 and route_check 0 on spike nets. RESULT.md written (primary
  approach passed; proposals P1-P9, findings F-1-F-8). Scratch boards deleted (rebuild with run_spike.sh OUTDIR).
