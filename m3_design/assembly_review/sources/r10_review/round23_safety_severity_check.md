# Round 23 safety severity check: R23-SAFETY-08(a) and R23-SAFETY-05

Independent severity verification of two round 23 safety findings filed as Minor.

- **Target:** commit `c70d261`, board `m3_design/assembly_review/m3.kicad_pcb`.
- **Board SHA-256:** `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1` before and after (unchanged).
- **Method:** read-only. Geometry and connectivity come from the native board through KiCad's pcbnew. Opens were
  seeded in memory only. The models are NumPy scripts. The local probes are in `.supervisor/r23_verify/`
  (`scripts/`, `calc/`), which git excludes.
- **Labels:** **Calc** is arithmetic on board values or maker figures. **Sim** is the numerical gate and e-match
  model. **Inf** is an inference not checked against an original datasheet or a measurement.
- **Not used as evidence:** the reviewer's Minor label.

## Verdicts

| Finding | Filed | Verified | One-line reason |
|---|---|---|---|
| R23-SAFETY-08(a) | Minor | **Minor** | A bounded residual that a screen can cover, not a credible fire. A fire needs three things together: a three-lead solder bridge, a missed AOI and bench QSPI check, and firmware that keeps IO2 fighting PE4 for ≥ 0.55 ms. Normal page-program logging cannot fire it, because C126 (220 nF) filters the gate. No explicit screen exists today: a gate gap. |
| R23-SAFETY-05 | Minor | **Minor** | A bounded margin residual. The numbers reproduce exactly (four stalls 1.063–1.128 A). They hold only under a single via fault together with the conditional four-stall case. The current stays ≥ 1.42× the maker's all-fire and ≥ 1.06× the maker's recommended minimum firing current. No inadvertent-fire path and no AGENTS §2 violation. |

## R23-SAFETY-08(a): QSPI_IO2 next to PE4

### Geometry, re-measured (Calc, native board)

**U1 pins 1–5** (LQFP-100, 0.5 mm pitch):

| Pin | Port | Net | Pad centre (mm) | Pad size (mm) |
|---|---|---|---|---|
| U1.1 | PE2 | QSPI_IO2 | (17.0, 50.55) | 0.30 × 1.60 |
| U1.2 | PE3 | no net | (17.5, 50.55) | 0.30 × 1.60 |
| U1.3 | PE4 | PYRO1_GATE_N | (18.0, 50.55) | 0.30 × 1.60 |
| U1.4 | PE5 | no net | (18.5, 50.55) | 0.30 × 1.60 |
| U1.5 | PE6 | no net | (19.0, 50.55) | 0.30 × 1.60 |

- **Pad edge to pad edge:** U1.1 to U1.2 is 0.200 mm, U1.2 to U1.3 is 0.200 mm, and U1.1 to U1.3 is **0.700 mm**.
- **Solder mask:** the board's mask expansion is 0 and no pad has a local margin. Each opening is the pad, which
  leaves a 0.200 mm web between pins in CAD.
- **Paste:** apertures are 1:1, with no margin or ratio.
- **QSPI_IO2 under U1:** the track runs (17.0,49.1)–(18.9,49.1), 0.2 mm wide, on F.Cu.
  - It is **0.550 mm** from U1.3's inner pad end (y = 49.75). The polygon distance is 0.5505 mm; the reviewer's
    0.5507 is the same figure.
  - It is not on F.Mask, so it is mask-covered.
  - The track (y 49.0–49.2) lies 0.8–1.0 mm inside the nominal 14 mm body outline (y = 50.0). The body outline is an
    Inf from the LQFP-100 14 × 14 footprint; U1 carries only a pin-1 dot on F.Fab.
- **PYRO1_GATE_N copper:** U1.3, a track (18.0,50.55)–(18.0,54.24), R126.1 and R127.1. Within 1 mm of it on F.Cu
  there are only:
  - the no-net U1.2 / U1.4 (0.200 mm) and U1.5 (0.700 mm);
  - GND fill, pads and vias (≥ 0.2505 mm);
  - QSPI_IO2: the track at 0.550 mm (its other segments 0.75–0.95 mm), then U1.1 at 0.700 mm;
  - a 3V3 via at 0.836 mm from R126.1. This one is already inventoried.

  QSPI_IO2 is therefore the only push-pull signal within 0.6 mm.
- **In R10 the PE3 / PE5 sentinels are analog and never driven** (docs/M3_R10.md "Firmware"). A two-lead bridge
  onto either of them is inert. Only a **three-lead bridge across pins 1–3** joins QSPI_IO2 to PE4.
- **The pad-to-track path needs a mask void.** Without one, solder would have to cross 0.55 mm of solder mask under
  the package body to reach a covered track. That is not credible (Inf).

### Gate network on the board (Calc)

- PE4 drives PYRO1_GATE_N.
- **R127** is 1 kΩ from PYRO1_GATE_N to GND.
- **R126** is 220 Ω in series, from PYRO1_GATE_N to PYRO1_GATE (Q124.4).
- **R128** is 10 kΩ from PYRO1_GATE to GND.
- **C126** is 220 nF from PYRO1_GATE to GND, the gate–source capacitor (Q124's source pins 1–3 are GND).
- **C128 is not the gate capacitor.** It is 100 nF on PYRO1_OUT, the drain. The brief's "C128 gate–source" is a
  mislabel.
- **The reviewer's calculation (`calcs.py`) leaves C126 out entirely.**
- **Gate time constant:** 47–50 µs with C126 at −10 % plus Ciss, and 53.0 µs nominal. Ciss is 2250 pF typical
  ([AON7524 Rev 1.1](https://www.aosmd.com/res/datasheets/AON7524.pdf) p2).

### What the bridge does

**DC fight (Calc / Inf).** With the bridge, PE4's low driver (with R127) fights whichever driver pulls IO2 high.

- **The model:** DS12110 Rev 8 Table 61 p141 gives VOL ≤ 0.4 V at 8 mA and VOH ≥ VDD − 0.4 V at −8 mA, read as
  drivers of ≤ 50 Ω ([DS12110](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf); treating them as
  resistors is an Inf).
- **The fight current is 33–66 mA.** That exceeds the 20 mA absolute-maximum IIO (Table 22 p107), so the real
  driver ratio is outside characterised data.

| Source holding IO2 high | Fight level at PE4 | DC gate |
|---|---|---|
| MCU IO2, equal drivers (50 / 50 Ω) | 1.610 V | **1.571 V** (reviewer: 1.58 V) |
| MCU IO2, driver skew 30–50 Ω | 1.215–2.025 V | 1.186–1.977 V |
| W25Q128JV at 100 % drive (Inf about 35 Ω) | 1.902 V | 1.857 V |
| W25Q128JV at its default 25 % drive (Inf about 140 Ω) | 0.568–0.838 V | 0.555–0.817 V |

The flash drive settings: W25Q128JVSIQ has QE = 1 factory-fixed ([W25Q128JV Rev G](https://www.winbond.com/resource-files/w25q128jv%20revg%2004082019%20plus.pdf)
p16, p74) and a DRV default of 25 % (p17). Its DC table gives only VOH at −100 µA (p62), so its drive resistance is
an Inf.

**Q124's response (Inf).** The model interpolates log(ID) through three anchors:

- the 250 µA VGS(th) point (0.4 / 0.8 / 1.2 V; p2);
- about 3 A at VGS(th) + 0.7 V, from Fig 1's 1.5 V curve (p3);
- about 60 A at VGS(th) + 1.2 V, from the 2 V curve.

The curve shifts rigidly with VGS(th), and VGS(th) moves −3 mV/K.

- **Gate needed for the 0.30 A no-fire current:** 1.33 V for a typical part at 25 °C, 0.82 V for a minimum-VGS(th)
  part at 60 °C.
- **Gate needed for the 0.75 A all-fire current:** 1.40 / 0.89 V.
- **E-match limits:** [MJG J-Tek technical sheet](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF)
  p1 gives:
  - no-fire 0.30 A for 30 s;
  - all-fire 0.75 A for 0.5 s;
  - recommended minimum firing current 1.00 A;
  - minimum all-fire energy 4 mJ;
  - mean bridgewire 1.0 Ω (SD 0.09 Ω).
- **Hazard loop:** 8.4 V bus with a 0.73 Ω match and no lead resistance, giving I_max = 2.805 A.

**A sustained fight fires the match.**

- **MCU drivers:** in every corner except the typical FET under the strong-N skew (45 mA).
- **Flash at 100 % drive:** always.
- **Timing (Sim):** Q124 passes 0.30 A 28–89 µs after the fight starts. The bridge absorbs 4 mJ after
  **0.54–0.64 ms** of continuous fight.
- **Flash at its default 25 % drive:** the match stays below no-fire. The worst case is 0.274 A, a minimum-VGS(th)
  part at 60 °C, which leaves only a 9 % margin and depends on the Inf flash resistance.

### QSPI patterns (Sim; QSPI mode behaviour is an Inf)

**Where IO2 can fight PE4.**

- **Single- and dual-line phases:** QUADSPI either forces IO2 low (RM0433 as quoted on the ST community forum) or
  releases it (FMEA V-13's reading). Either way IO2 does not fight PE4's low. RM0433 was not re-read here.
- **Quad phases:** IO2 carries data bits 6 and 2 of every byte.
- **Logging writes:** the firmware does not exist yet, so its write instruction is open.
  - If it uses Quad Input Page Program 0x32, a single-line instruction and address are followed by 512 quad clocks
    for a 256-byte page. Then comes tPP, 0.4 ms typical and 3 ms maximum, with no fight (Rev G p37, p65).
  - Standard 0x02 writes never use IO2.

**Pages modelled.** The gate is the RC-averaged fight (the bit rate is far above 1/τ), followed by Q124 and the
bridgewire.

- Clocks: 10, 25, 50 and 100 MHz.
- IO2-high density in data: 0.5 (random) and 1.0 (0xFF / 0x44 padding).
- Page rates: 80/s (F5's 500 Hz log at 40 B per sample, an Inf), 100, 400 and 1000/s, and the back-to-back
  maximum (about 2200–2450/s).
- Four drivers × FET corners per case.

| QSPI clock | Data burst | Worst gate peak | Worst RMS match current (any rate) | Against 0.30 A no-fire |
|---|---|---|---|---|
| 100 MHz | 5.1 µs | 0.206 V | 14 µA | ≥ 20,000× below |
| 50 MHz | 10.2 µs | 0.390 V | 0.11 mA | ≥ 2,600× below |
| 25 MHz | 20.5 µs | 0.703 V | **6.0 mA** (F5 rate: 1.1 mA) | ≥ 50× below |
| 10 MHz, random data | 51.2 µs | 0.675 V | 5.3 mA | ≥ 56× below |
| 10 MHz, all-ones data | 51.2 µs | 1.318 V | Typical FET at 25 °C: ≤ 25 mA. Minimum-VGS(th) FET at 60 °C: **0.08–0.80 A** (80/s up to the maximum rate) | Minimum-VGS(th) FET: **exceeded from about 400 pages/s** (strong-P skew) or **1000 pages/s** (equal drivers). At F5's 80/s the RMS is 0.08–0.15 A, but a match with a 1 ms thermal time constant sees 0.29–0.54 A |

Thermal filters of 1, 7.1 and 44 ms give the same picture.

**Long quad reads of erased flash** (0x6B, IO2 driven by the flash):

- **Default 25 % drive:** the gate stays ≤ 0.817 V and the current ≤ 0.274 A for any length. That is below
  no-fire.
- **100 % drive (only if firmware sets DRV = 00):**
  - a 4 KB read puts 0.08–2.3 mJ into the bridge;
  - a 64 KB read puts 10–41 mJ into it, against the 4 mJ all-fire energy, so it **fires**.
- **Memory-mapped mode left parked:** with nCS held low and the clock stopped on a '1', the fight is DC.

**The claim is overstated.** "With the bus enabled that fires the match during QSPI logging" does not hold for page-program logging at ≥ 25 MHz.

**Patterns that do fire.** With the bridge present and the bus live, the match fires only under a sustained IO2-high
fight of ≥ about 0.55 ms:

- a GPIO-driven PE2 held high;
- long quad reads, or a parked memory-mapped read, with the flash at 100 % drive;
- Quad Page Program run at a slow clock (≤ about 10 MHz) on IO2-dense data at high page rates, with a low-VGS(th)
  FET.

### Likelihood and screens

**How likely the bridge is (Inf: no JLC or maker defect data in the repository).**

- **What it takes:**
  - one solder mass across three gull-wing leads and two 0.200 mm mask webs, which is an uncommon reflow defect;
  - or, for the pad-to-track path, a mask void, which is not credible.
- **Paste volume is ordinary.** At the preferred 0.10 mm stencil, a 1:1 0.30 × 1.60 mm aperture gives about
  0.048 mm³ per lead (Calc). That is comparable to a reduced aperture on a thicker stencil, so the CAD shows no
  unusual bridging driver (Inf).
- **It is easy to see.** The leads are exposed on the top side.

| Screen | Catches the bridge? |
|---|---|
| JLC AOI | Likely (Inf: JLC's standard process, not documented in this repository) |
| ORDERING §8.2 first-article inspection | No. It checks U1's pin-1 and orientation, not its joints |
| ORDERING §8.3 bench QSPI qualification (F5 throughput / recovery, "full-flight storage alongside primary QSPI", HSE under QSPI activity) | **Yes, implicitly.** At the default 25 % drive, a quad read of a '1' on IO2 settles at 0.57–0.84 V. That is below the MCU's VIL maximum of 0.99 V (0.3 VDD, Table 60 p139), so bits 6 and 2 read as 0 deterministically (Calc / Inf). Any quad readback compare fails on the bench with dummy loads, before an e-match. It is not written as a safety gate, and it fails to apply if firmware never uses quad mode, in which case the bridge is also inert. |
| Passive cold screen | Not dependably. Bursts at ≥ 25 MHz lift the gate ≤ 0.70 V for ≤ 20 µs |
| Per-flight pre-insertion check | No. The board is off |

### Verdict: Minor

- **Not Critical.** A fire needs all of:
  - a three-lead bridge, a defect that a two-lead bridge cannot reproduce by design (FMEA H-2's trade);
  - an escape from AOI and from the bench's quad-mode QSPI qualification;
  - firmware that keeps IO2 fighting PE4 for ≥ about 0.55 ms while PC1 is high.

  Normal logging at ≥ 25 MHz stays ≥ 50× below no-fire.
- **Not Major.**
  - The intact board meets F7 and F8.
  - AGENTS §2.4 still holds with the bridge: in reset both pins are analog and QSPI_IO2 has no pull-up, so R127 and
    R128 hold the gate off.
  - Single-bridge cases are an inventoried residual class with no fault-tolerance claim (R10_VALIDATION §1, where this
    pair is listed at 0.2000 / 0.5500 / 0.7000 mm).
- **Is Minor.** It is a bounded residual with a gate gap: no explicit, deterministic screen exists before an e-match
  meets the live bus.

### Recommended fix (no board change)

1. **ORDERING §8.3 first article, before coating and first power.**
   - Inspect U1 pins 1–5 at ≥ 10×.
   - Meter U3.3 (QSPI_IO2) to R127.1 (PYRO1_GATE_N). Require no beep and > 100 Ω.
   - The expected readings are an Inf: about 0 Ω if bridged, a diode-plus-1 kΩ path or open if intact.
2. **Firmware ground refusal, with PC1 and PE4 locked low before the passive screen.** Use either check:
   - a quad-mode read-verify of a known all-ones region at the default DRV;
   - or a ≥ 1 ms PE2-high aggressor with the bus off, refusing if CONT leaves its band.
3. **While PC1 is high:**
   - keep W25Q DRV at its default;
   - never park memory-mapped mode without the QUADSPI timeout;
   - make no bulk quad reads;
   - never drive PE2 as a GPIO high;
   - run Quad Page Program at ≥ 25 MHz, or use 0x02.
4. **R10_VALIDATION §1:** add the mechanism and the screen to this pair's row.

**Respin:** optional. Nothing on the board needs to change.

## R23-SAFETY-05: Q120's gate on one via

### Topology (Calc, connectivity graph of the native board's ACT_GATE copper)

- **ACT_GATE copper:**
  - R121.1 on F.Cu;
  - two vias, (16.200,73.300) and (11.140,71.700), each 0.50 / 0.30 mm and flashed on F.Cu and B.Cu;
  - Q120.4, C120.2 and R120.2 on B.Cu;
  - R119.1 and Q121.4 on B.Cu.
- **Via (16.2,73.3) opened in memory:** the net splits into {R121.1, Q121.4, R119.1} and {Q120.4, C120.2, R120.2}.
  - Q120's gate is then held only by R120 (100 kΩ) and C120 (1 µF) to its source, so VGS = 0 and Q120 is off.
  - With PC1 high, Q121 is driven at VGS = −(100/110) V_S.
  - The bus is fed through Q120's body diode, from BAT_IN (drain) to ACT_FET_S (source).
- **Via (11.14,71.7) opened instead:** Q121 is isolated and off, so the bus is dead, which the powered check
  refuses. That case is fail-safe.
- **Neither open adds a fire path.** It can only remove bus current.

### Fire current (Calc on `parts_budget.json` `fire_current_GAP1`)

**Budget reproduced exactly.** The branch is 4.4678 Ω: R134 hot 2.029 Ω, match 2 Ω, leads 0.3 Ω, copper 70 °C
0.0355 Ω, return and terminal 0.015 Ω, Q124 0.0082 Ω and 2 × 0.04 Ω for the P-FETs. The pack is 0.15 Ω, the other
load 13.064 W and each stall 1.92 A.

| Stalls | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| Intact board (A) | 1.5409 | 1.4758 | 1.4104 | 1.3448 | 1.2787 |

**With Q120's body diode in series.** VSD is −0.7 V typical and −1.0 V maximum at IS = −1 A
([AONR21357 Rev 2.1](https://www.aosmd.com/res/datasheets/AONR21357.pdf) p2). Fig 6 (p3) gives about 0.68–0.70 V at
1.1–1.4 A at 25 °C.

| Case | 0 stalls | 3 stalls | 4 stalls |
|---|---|---|---|
| VSD 0.7 V, branch kept | 1.390 A | 1.194 A | **1.128 A** |
| VSD 1.0 V, branch kept | 1.325 A | 1.129 A | **1.063 A** |
| VSD 0.7 / 1.0 V, Q120's 0.04 Ω removed | 1.402 / 1.336 A | 1.204 / 1.139 A | 1.137 / 1.072 A |
| −20 °C (Inf: VSD + 0.09 V) | | | 1.043–1.118 A |

These match the reviewer's 1.128 / 1.063, 1.194 / 1.129 and 1.390 / 1.325 A.

**Four-stall margins:**

| Reference | Ratio |
|---|---|
| Maker all-fire, 0.75 A | 1.39–1.52× |
| Maker recommended minimum firing current, 1.00 A | 1.04–1.14× |
| Project 1.125 A floor | 0.93–1.01× |

**Pulse length (Inf).** A first-order bridgewire model, bounded by the maker's 0.30 A / 30 s, 0.75 A / 0.5 s and
4 mJ figures, makes the least sensitive admissible match fire in 4.1–5.2 ms at these currents. The intact board
gives 3.0 ms. Both are inside the 20 ms pulse. The chosen lot's 20 ms firing is still unqualified (F7).

### Detection (Calc / Inf)

- **Idle bus:** the bus reads 0.45–0.55 V low, a 5.4–7.4 % shift on ARM1_SENSE (/11.2). The idle drop comes from
  about 1.5 mA on Fig 6.
- **First-article gate probe:** ORDERING §8.3's load-switch step probes ACT_GATE. Probing R120.2 or C120.2 (Q120's
  side) catches a pre-existing open; probing only R119.1 does not.
- **Dummy-load fire:** firing into a dummy load would show 0.7–1.0 V of extra BAT_IN-to-RAW_ACT drop.

### Verdict: Minor

**Not Major.**

- F7's 1.125 A floor is the budget for the intact native board.
- The shortfall appears only under a single via fault combined with the conditional four-stall case.
- The channel then still delivers ≥ 1.04 A, above the maker's recommended minimum.
- AGENTS §2 is untouched: the bus still comes after the load switch, both gates stay defined off, and there is no
  fire path.

**Is Minor:** a bounded margin residual with an incomplete screen.

### Recommended fix

**Now (text, no board change):**

1. **First article:** probe ACT_GATE at both R119.1 and R120.2 / C120.2 with PC1 high, and record |VGS| for each
   FET.
2. **First article:** record BAT_IN − RAW_ACT, or the fire current, during the dummy-load fire. A drop above 0.2 V
   fails.
3. **Per flight:** adopt the powered BUS-against-VLOGIC band once it is qualified.

**Respin:** add a second F.Cu–B.Cu via at Q120's gate.

## Coverage limits

**Datasheets and records not re-read:**

- RM0433 was not re-read. The QUADSPI IO2 single-line and idle behaviour is an Inf.
- JLC's AOI coverage and defect rates are not documented here.

**Model inputs (Inf):**

- the MCU and flash driver resistances under the fight;
- the W25Q drive at mA levels;
- AON7524's sub-amp transfer curve, extrapolated from typical curves with a rigid VGS(th) shift;
- the threshold temperature coefficient;
- the J-Tek thermal model.

**Not tested or covered:**

- No bench measurement, SPICE or firmware.
- Part (a) only: PYRO1_GATE's own neighbours, and parts (b) and (c) of R23-SAFETY-08, were not re-measured.
- The via-open probability is unquantified.
- Cold VSD is an Inf.
