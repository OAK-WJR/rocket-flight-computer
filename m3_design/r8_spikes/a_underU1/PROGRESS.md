# Spike (a) under U1: progress log

Resume from the last entry. Scratch: `$SCRATCH/r8_design/spike_a_underU1/` (r7.kicad_pcb = `git show 431025d:m3_design/assembly_review/m3.kicad_pcb`).

Build: `PYTHONUNBUFFERED=1 $KPY -I spike_build.py r7.kicad_pcb OUTDIR [--no-routes] [--fallback]`
Verify: `run_verify.sh OUTDIR` (DRC json, route_check json, spike_verify.py).

1. Read handoffs 0-2, plan, surveys, plan_partial. Scope nets: QSPI x6, HSE_IN/OUT, NRST, ARM1_SENSE(_MCU),
   VCAP1/2, BOOT0, decoupling (3V3/GND/3V3A at U1), parts U3 C29 R10 Y1 C25 C26 C13-C24 R5 R170.
2. spike_build.py: R7 + R8 netlist + seed placement + rigid copper only + B8 In2 zones. Seed board (no routes):
   all 12 rigid groups match R7.
   - Finding: the native fill needs the project rules beside the board (else strip_gcpw changes).
   - Finding: removing R7's four far F.Cu power zones together changes strip_gcpw (0.01 mm at 13/372 samples);
     kept them in the scratch board. Real build (step 5) must re-check this.
3. v1-v3 iterations (scratch v1..v3). v3 = primary approach PASS on the spike filter: rigid 12/12 OK, DRC 0 on spike
   nets/parts, route_check 0 failures on spike nets. Topology: flash O1 (seed), ARM1_SENSE on B.Cu along the forward
   edge under the fwd pad row (y 52.6) then straight up x 18.18 to the exit via; NRST via at pin 14 then B.Cu y 51.85
   west to J2; Y1 rot 90 B; VDD11 / VDD100 / VDDA outward; dividers parked forward (not routed).
   Next: diff DRC + route_check vs the seed board (power/GND items), check_r8 on v3, render, measurements, RESULT.md.
4. Final (scratch `final/`): diff vs seed clean (0 new DRC, 0 new route_check failures), check_r8 only change = C29
   fixed; clearance probe >= 0.2 mm except R7-inherited items; KIID seed 8301 -> byte-identical rebuilds
   (3d922707...). RESULT.md written. DONE: primary approach passed; fallback not needed.
