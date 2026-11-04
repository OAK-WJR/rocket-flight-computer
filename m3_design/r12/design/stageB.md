# R12 stage B: board, stack-up and placement (2026-11-04; connectors updated for D-R12-29 … -31)

Stage B of `r12_plan.md` §4. `m3_design/r12_pcb.py` builds `m3_design/r12/m3.kicad_pcb` from the stage-A netlist and
`m3_design/r12_place.tsv`; `m3_design/r12_build.sh` runs it after stage A, then `fit_check --profile r12`, a native
DRC with schematic parity and `check_r12 --stage placement`. The board carries no copper but the footprints' own.
Nothing is committed or ordered. Decisions D-R12-21 … D-R12-28 are in `R12_DECISIONS.md`.

Evidence labels as AGENTS §2.5. Coordinates are board mm: x east (0 … 46), y forward from the aft edge (0 … 100),
every part on the top face (F, D-R12-01).

## 1. Outline 46 × 100 mm (D-R12-24)

46 mm (P1) by 100 mm, JLC's four-layer price step (a longer board costs more, `cost_study.md` §2.1, Live). A 90 mm
outline was placed first (the R10 length); the drafting router (stage C) could not complete it under R12's one-sided
assembly and the strict routing gate (every part on F, F and B the only signal layers, at most two vias on a critical
net that has no pour), so the forward half was spread over the extra 10 mm at no cost (Calculation on the stage-A price
table; the length is free below 100 mm). The coupler stack (`docs/VEHICLE.md` in the parent repository) had 52–84 mm of
slack against R9's 102 mm board; 100 mm is shorter than R9 (Inference: the stack figures are R9's).

## 2. Density

| Face | Parts | Courtyards (sum; they do not overlap) | Face area | Fill |
|---|---|---|---|---|
| Top | 184 | 1995 mm² | 4600 mm² | 43.4 % |
| Bottom | 0 (THT tails of J1, J121, J3's shell and LS120 only) | — | — | — |

Measured with the generator's courtyard boxes (the stage-A estimate was 1995 mm², `r12_plan.md` §1).

## 3. Stack-up (D-R12-03, D-R12-22)

JLCPCB's standard 1.6 mm four-layer build **JLC04161H-7628** as `r12_pcb.STACKUP` writes it: F.Cu 0.035, prepreg 7628
0.2104, In1.Cu 0.0152 (0.5 oz), core 1.065, In2.Cu 0.0152, prepreg 7628 0.2104, B.Cu 0.035 mm, ENIG (Inference until
the order page is re-read: the figures are JLC's published table as recalled, not re-fetched in this stage). In1 and
In2 are typed power. Their use (stage C, D-R12-22): In1 one GND plane; In2 the 3V3 plane with three islands
(`m3_design/r12_planes.tsv`).

## 4. Mounting holes (D-R12-24)

Four M3 supports, 3.2 mm, at (3.0, 5.9), (43.0, 5.9), (3.5, 94.1), (42.5, 94.1). The aft pair sits 3.0 mm in from the
long edges (not R11's 3.5) because the aft GH row (J400 4-pin, J122 6-pin, J9 6-pin clones) needs 32.7 mm of courtyard
between the two washers' 3.8 mm keep-outs; with the holes at x 3.5 / 42.5 the courtyards overlap by 0.38 mm
(Calculation: GH body half-widths 4.125 / 5.375 mm from JST's drawing as fit_check models it). The washer (7 mm OD)
then overhangs the long edge by 0.5 mm, inside the Ø50.8 mm bore (Calculation; Inference that the sled tolerates it).
fit_check: nearest top hardware clearance J1.2's wire allocation 3.850 mm (≥ 3.8), nearest bottom envelope J1.2's wire
5.650 mm (≥ 3.5).

## 5. Edge assignment and blocks

| Where | Parts | Reason |
|---|---|---|
| Aft edge (y 0), mouths aft | SH 1.0 ports (D-R12-31): J400 (x 11.0), J122 (21.6), J9 (33.5) | switch beside the power entry; servo leads from the fin can; camera beside its buck |
| Forward edge (y 100), mouths forward | SH 1.0 ports: J420 radio (11.5), J410 GPS SH-6 (23.0), J440 AUX (34.5), in the MicoAir H743's pin order | U1's UART balls are on rows J / K and column 10 |
| West edge | J1 battery pads (3.5, 15.3), 5.0 mm pitch, with a 10 × 8.2 mm keep-clear for a later terminal (D-R12-30); J121 DB125-2 screw terminal (7.4, 37.0), wires west, wire room 5.00 mm ≥ 4.95 (D-R12-29) | pack leads arrive from aft along x = 0; the pyro cell beside J121 |
| East edge | J3 USB-C (41.4, 44.0) | U1's USB balls B10 / C10 face east |
| Aft-west | J1 ladder (D8, C80, C96), U9 + EN / OVLO / ILIM / dVdt, damper R166 / C89 / C95 | the power front end in one block (AVA-style) |
| Aft-middle / east | RAW cluster (C82, C97, R92, D9, TP81, D5), servo network (R150–R157, D121) at J122, camera / port / 3V3 buck cells (U403, U400, U2) in a column | one power end; each buck cell VIN cap – IC – inductor – output cap in a line |
| West, y 25–50 | pyro cell: Q120 / Q121 load switch, R134, Q124, gate networks, cold / continuity / arm banks, TP120 / TP122 | the fire path short and on F (J121 at its edge) |
| Centre | U1 (23.0, 44.0, rotation 0), Y1 west, decoupling at the four corners of a 6.5 mm fan-out ring | column 1 west (HSE, pyro), row A aft (IMU, servos), column 10 east (USB, SD, QSPI) |
| Aft of U1 | U4 IMU (23.0, 31.6, rotation 180) on the roll axis (moved 3 mm aft in stage C, D-R12-32), U5 baro (29.0, 32.0), 3V3A parts | sensors together over the 3V3A island |
| South-east of U1 | U3 QSPI flash (34.0, 57.0), D6, C84 hold-up (owner-fitted) | |
| Forward-middle | J430 microSD (20.0, 68.0, rotation 180, contacts toward U1), pull-ups | |
| Forward | LS120 buzzer (owner-fitted THT), LEDs, J2 Tag-Connect, test pads, port R / C at the GH row | |

The placement rules the generator holds (it stops the build otherwise): courtyards apart, ≥ 0.25 mm from a long edge and
≥ 0.5 mm from a short edge (J3's mouth excepted, as R10 / R11), every exposed top pad ≥ 3.8 mm from a support centre and
every plated pin ≥ 3.5 mm.

## 6. IMU (D-R12-25)

U4 at (23.0, 31.6), rotation 180, top face: lever arm to the roll axis x = 23 mm is 0.000 mm (`r12_gate_data.json`
imu). The axis map changes from R11 (U4 was on the bottom, roll = −gyro_Y, D-R11-11) because the part moved to the top
face; the R12 map is **not derived in this stage**: it needs the ISM6HG256X datasheet orientation figure against the
top-face 180° placement, then a bench check (open item for stage D; firmware must not reuse R11's map). The IMU body keeps R10's two rule areas (body: no via, no pour; pad-ring interior: no track) on F.Cu.
The baro keeps only its body area: R10's no-track band between the pad rows fitted the MS5611; the LPS28DFW's centre
GND pad 7 can only join its GND pads across that band (D-R12-25).

## 7. Gate results (this stage)

| Check | Result |
|---|---|
| `r12_pcb.py` legality | OK, 184 parts, deterministic (two builds byte-identical) |
| `fit_check --profile r12` | OK (CAD envelopes only) |
| `check_r12 --stage placement` | OK (L-1, M-1, F-1, N-1, K-rules, M-5) |
| kicad-cli DRC with schematic parity | 0 violations, 0 parity issues; 399 unconnected items (no copper yet) |

Not verified: physical fit with the sled, wires and plugs; the GH clone mating (O-R12-04); the IMU axis map.
