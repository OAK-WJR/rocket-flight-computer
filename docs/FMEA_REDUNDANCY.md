# Rocket Flight Computer v1 — Redundancy Architecture and Fault-Tolerance Ruling (REDUNDANCY-1, 2026-09-03)

> This document revises all of the firmware constraints in `ROCKET_FC_FROZEN_DESIGN.md` §7, and proposes schematic changes to §2.3 / §3.9 / §5.2 that must be implemented before fab. Geometry follows `GEOMETRY_REV_G.md`.
> **Severity order (the document's only weighting)**: ① inadvertent firing on the ground / during handling (personal injury) > ② no deployment (ballistic, total loss, range incident) > ③ deployment at the wrong time (high-speed deployment, shredded recovery) > ④ loss of roll control (mission failure, rocket usually recoverable) > ⑤ loss of log/telemetry.
> **First principle throughout**: any change that trades a ⑤ or ④ risk for a ② or ① risk is rejected, however "safe" it looks.

---

## 1. Single-point-of-failure list

Criterion: a **single** component, solder joint, wire, register write or human action is enough to cause the consequence. Sorted by severity.

### 1.1 INJURY class (inadvertent firing on the ground / during handling)

| # | Failure | Cause | Detectable today? | Consequence | Backstop |
|---|---|---|---|---|---|
| **I-1** | **Q3/Q4 (AO3400A) drain-source short** | Accumulated damage from the previous flight's 4.0–9.84 A pulses (rev G §5.6 rates 9.84 A MARGINAL); ESD; a solder bridge between the adjacent SOT-23 drain and source | **No — and the "FET short self-test" claimed in §7 cannot be implemented on this netlist.** `PYRO1_OUT = {J4.4, Q3.3, R18.1}`; the only path up from the drain is igniter → `PYRO_BUS`, and with the ARM plug out `PYRO_BUS` is pulled to 0 V through R14/R15. Plug out: a healthy FET, a shorted FET, an open igniter and no igniter **all read 0 V** on PC0. Plug in: a shorted FET has already fired the charge | The charge fires the moment the operator is holding the ARM plug | **None.** Change H-1 (cold drain pull-up + BAT54A blocking) turns it into a cold measurement **before** the plug goes in; procedure P-2 (power up and self-test first, connect ARM after) downgrades the whole class of "only shows up at power-up" faults to bench findings |
| **I-2** | **An adjacent-pin solder bridge onto a pyro gate** | LQFP100, 0.5 mm pitch. `PE3 = LED_RED (pin 2) / PE4 = PYRO1_GATE (pin 3) / PE5 = PYRO2_GATE (pin 4) / PE6 = BUZZ_GATE (pin 5)` are four consecutive pins. The gate network 470R + 1k + 10 nF (τ = 4.7 µs) passes both the red LED's hundreds-of-ms highs and the 2.7 kHz buzzer drive; 3.3 V through the 470R/1k divider gives 2.24 V at the gate, **far above the AO3400A's true maximum threshold of 1.45 V** (rev G §5.7) | **No.** With ARM out the drain is always 0 V, so no test can see gate activity | The charge fires on the bench | **None.** Change H-2 (separate the two gates and surround them with sentinel pins driven low) + H-1 make the bridge testable (toggle the red LED / buzzer and watch whether CONT collapses) |
| **I-3** | **A single solder bridge between PE4 ↔ PE5** | Same as above; the two are physically adjacent | No (as I-1). Testable after H-1: driving gate 1 must not move drain 2 | One fire command fires both channels. The main comes out with the drogue at apogee (③); two charges in one compartment may over-pressure and break the airframe; ~13.6 A from both channels through the single 5 A fuse | None. Removed structurally by H-2 |
| **I-4** | **A stray strand on the J-ARM terminal bridging RAW to PYRO_BUS** | In the netlist `J4.1 = RAW` and `J4.2 = PYRO_BUS` are **adjacent**; after rev G §3.3's reorder `ARM_A (RAW)` and `ARM_B (PYRO_BUS)` are still adjacent. Stranded wire splaying in a 5.08 mm screw terminal is a standard failure | **The hardware already has the sensor; firmware never looks in this direction.** §7.4 uses ARM_SENSE in one direction only, "confirm armed before firing". With a stray strand, `ARM_SENSE = 0.764 V` while the plug is visibly out | As long as the reed switch is closed, the vehicle is **permanently armed**, and the 5 A fuse is bypassed. Every safety inference the operator draws from "the plug is out" is void | Firmware rule F-14 (negative ARM_SENSE check) + procedure P-1 (termination outside the airframe, only tinned solid wire or ferrules, every wire re-checked with a DMM) |
| **I-5** | **AP63203 high-side FET short → VLOGIC (≈ 8 V) straight onto 3V3** | Single-point failure of a synchronous buck | **No**, the MCU is itself the victim | PE4 at 8 V through the 470R/1k gives 5.4 V, far above threshold → fire. The MCU dies at the same time; no firmware defence exists | Cannot be covered in firmware. The only effective measure is **the order in procedure P-2**: power up → self-test → tone → **only then** connect the ARM link. Optional H-9 (3.6 V clamp on 3V3, which fails short = board dies on the bench) |
| **I-6** | **Q2 (AON6403) drain-source short, or the SW wire chafing to ground** | The main MOSFET failure mode is a drain-source short; `GATE_SW = {Q1.4, Q2.4, R1.1, R2.1}` leaves the board through R2 (10k) to `SW_TERM = {J1.3, J1.4}` on an **unclamped bare wire** (frozen §8 item 6 gave that treatment only to the pull-pin, not to the SW pair with far more serious electrical consequences) | **Nothing in the netlist reads back switch state.** The only available check is bench test T-1: battery connected, external switch OFF, USB plugged in — `VBAT_SENSE (PC4)` must then read **< 0.2 V** (RAW floats only through R3's 147k). Anything higher means a shorted FET or stuck switch | The board cannot be turned off → inserting the ARM plug energises a live bus | Bench test T-1 (zero cost, uses the existing divider) + procedure: SW twisted pair, opposite side from the pyro/servo harness, separate ties |
| **I-7** | **No "lift-off latch" as a precondition for firing** | §7.4 only requires reading ARM_SENSE and CONT and **never requires any flight-phase condition**. A design gap, not a component failure | **Undetectable** (a design property, not a runtime event). The board's IMU and barometer show it can be implemented, not that its absence can be noticed | While armed, **any single** firmware defect, stack overflow or EMI glitch driving a gate high releases energy | Firmware rule F-6 (LIFTOFF latch, two-source OR, never cleared for the whole flight). This is also the safety precondition for any "re-arm after reset" scheme |
| **I-8** | **No disarm after landing** | §7 defines launch detection and apogee detection but **never defines LANDED**. After landing the reed switch is still closed, the ARM plug still in, and 0.764 mA still flows through the unfired channel's bridgewire | Yes (stable pressure + \|a\| ≈ 1 g + a time floor), but the state does not exist today | Recovery crew walk up to a rocket still in flight state carrying an unfired charge. The most common real injury scenario in this field | Firmware rule F-8 (LANDED → permanent disarm, cleared only by power-off) + procedure P-5 (approach from the side, pull the ARM plug first, then switch off, then touch the airframe) |

### 1.2 VEHICLE_LOSS class

| # | Failure | Cause | Detectable today? | Consequence | Backstop |
|---|---|---|---|---|---|
| **V-1** | **IMU DRDY stops → IWDG never fed → reset → pyros permanently disarmed** | §3.4 pin 40 and §7.1: `the IWDG is fed only in this ISR`. The ICM-45686 is a 2.5 × 3.0 mm LGA-14 with no lead compliance; a cracked joint under 30 g boost vibration, SPI1 losing sync or latch-up — any of these stops the 800 Hz edges | **Today the only "detector" is the reset itself, which is the fault.** A DRDY edge counter checked by an independent timer would detect it within 25 ms | One sensor hiccup escalates a ④-class event into a ② total loss | The full ruling in §2. Core: **an IMU stall must only degrade, never reset** |
| **V-2** | **A reset loses the "flight phase", not just the arm bit** | The state machine restarts in PAD; launch detection is a boost-transient criterion that will never be true again at 2 km and 0 m/s | Completely undetectable today (no state persists across reset) | **Even with the pyros correctly re-armed, the rocket will not fire**, because it thinks it is on the pad. That is the real end of the kill chain | Firmware rule F-4 (.noinit flight record + flash phase log + live-evidence cross-check) |
| **V-3** | **The fire pulse is terminated by software** | §7.4 only says "pulse ≤ 20 ms" without specifying how. If the CPU hangs / HardFaults / is hit by EMI mid-pulse, the gate stays high | Visible in the log afterwards; undetectable in flight | Rev G §5.6: 6.81 A / 3.09 W into a 1.0 Ω load, RthJA 125 °C/W → **313 °C** steady-state rise, FET destroyed (and MOSFETs tend to fail **short** → next flight becomes I-1). The 5 A fuse at 136 % of rating "may take minutes to blow" and does not cover this intermediate state. An IWDG period of 2 s × 6.81 A = 93 A²s, enough to blow the shared fuse → the second channel dies too | Firmware rule F-9: hardware termination (the highest-priority timer ISR writes BSRR directly, or a timer compare event triggers a DMA write to `GPIOE->BSRR`) + rev G's independent TIM2 25 ms hard abort + IWDG period shortened to ~400 ms |
| **V-4** | **L2 (4.7 µH SWPA4030) open** | Netlist: `3V3A = {L2.2, U1.20 (VREF+), U1.21 (VDDA), U4.5/U4.8 (IMU), U5.1/U5.2 (MS5611), U6.2/U6.17 (GNSS), ...}`. **One 3 mm-tall wirewound inductor in single string ahead of every sensor and the ADC reference** | Free to test but not done today: solve VDDA from `VREFINT` against `VREFIN_CAL (0x1FF1E860)` (§7.9 already reads it, just not as a fault signal); add AVD @ 2.8 V | IMU + barometer + GNSS + **the whole ADC scale** die together. `PYRO*_CONT`, `ARM_SENSE` and `VBAT_SENSE` then read wrong but mutually consistent. **It punches through every "voting" and "cross-check" redundancy on the board at once** | Firmware rule F-12 (VREFINT criterion + "all three sensors lost at once" classified as one RAIL_DEAD code) + procedure (L2/L1 on the staking and pull-check list). **The strongest single argument for a permanently fitted backup altimeter** |
| **V-5** | **The single 5 A fuse + the single PYRO_BUS in series ahead of both channels** | `PYRO_BUS = {J4.2, J4.3, J4.5, R14.1}`, one net, three terminal positions. The ARM plug is its only bridge to RAW | Partly: after the fuse blows `ARM_SENSE → 0` while `VBAT_SENSE` is normal — a clear signature (F-13) | One igniter shorted (crushed, against the airframe wall) → 40 A-class short → fuse blows → **both channels dead**. "Two pyro channels" are therefore not redundant against anything upstream | Structural: H-5 (split PYRO_BUS into two independently fused buses, a netlist-only change). Otherwise only P-1's per-wire DMM check + a permanent backup altimeter. **A normal fire does not threaten the fuse**: 20 ms × 6.81 A = 0.93 A²s, while a blade fuse's melting I²t is tens of A²s → **do not shorten the pulse** (see the rejected items in §4) |
| **V-6** | **25 MHz HSE crystal failure with CSS not enabled** | Y1 is a mechanical resonator in a 30 g environment, next to the lever arm of a 14 mm screw terminal. A grep of all six documents finds no `CSS` and no `HSI` fallback | Yes (CSS raises an NMI), but not enabled | PLL loses lock → CPU stops → silent, complete, no deployment. **No watchdog strategy can save it** (the core has no clock). With a blocking wait for HSE-ready at boot, not even the IWDG is running yet | Firmware rule F-2 (CSSHSEON + NMI switches to HSI + **recompute every time constant**: 200 → 64 MHz stretches a 20 ms pulse to 62 ms, straight into V-3's thermal-destruction zone) |
| **V-7** | **§7.4 makes ARM_SENSE and PYRO*_CONT preconditions for firing** | Verbatim: "before firing, read ARM_SENSE to confirm armed and PYRO*_CONT to confirm the bridgewire is present". Implemented literally, that is a veto | N/A — a rule defect | One cracked 0402, one ADC channel stuck at zero, one VREF disturbance, and a healthy rocket refuses to deploy. The costs are wildly asymmetric: **firing into an open bridgewire costs nothing; refusing to fire into a good one costs the vehicle.** And both readings' reference sits behind V-4's L2 | Firmware rule F-10 (**in flight, sense readings are only logged and annunciated and never veto a fire**; on the ground they are hard refusals, because refusing on the ground is free) |
| **V-8** | **Blocked static port / failed bay seal / sunlight on the MS5611** | Assembly side: tape, filler, a misaligned sled, epoxy overflow; a translucent coupler | Partly: 30 s pressure σ (**log only, no alarm** — it misjudges on a calm day); dP/dT correlation (a sealed bay follows Gay-Lussac: `1013 / 293 = 3.457 hPa/K = 29 m/K`, so 5 K of sun is 145 m); a human-in-the-loop block/release test (the only reliable one on a calm day) | Late or missed apogee (②), or a completely wrong main altitude (③). **And the primary and backup altimeters share the same bay and the same vents → electronic redundancy is useless against it** | Procedure P-3 (3–4 small holes at 120°, away from the sensor, sealed bulkheads, a bench leak test, a ground ejection test) + firmware F-11 (keep an inertial vote in the apogee decision, so that §7.7's "the accelerometer must not be promoted" becomes a **conditional** rule) |
| **V-9** | **MS5611 stuck value / light sensitivity / ejection pressure shock** | A hung I2C (the spare header shares I2C1, admitted low-confidence in §3.6), the internal ADC stalling, ejection gas leaking into the av-bay. **Unique to this rocket**: the MS5611 is a gel-covered bare die and is light-sensitive, and this rocket **rolls actively** → a beam of sunlight through a vent sweeps the sensor at the roll frequency, producing a "live, plausible-looking" periodic pressure error | Yes, but only with the right criterion: **N consecutive identical raw D1 words**, never a threshold on the engineering value — pressure is naturally constant at apogee, so a threshold detector would **declare the barometer dead exactly when it is needed most** | Missed apogee (②), or frozen below main altitude → main at apogee (③) | Firmware rule F-11's full BARO_VALID set + 500 ms blinding after each fire + a vented foam cover over the sensor (blocks light and cushions ejection shock) + no line of sight from vent to sensor |
| **V-10** | **Battery / load switch / buck / 3V3 / MCU / firmware image — all single-string** | Architecture | A dead buck cannot test itself; the battery can be tested on the ground (load step T-2) | Total loss | **Cannot be covered on the board.** The only backstop is §3's permanently fitted independent commercial altimeter |
| **V-11** | **Reed/magnetic switch bouncing under vibration → whole-board power loss → POR** | Reed blades have mechanical resonances in the low kHz; `SW_TERM` carries only 76 µA, **below the wetting current of any non-hermetic contact**, and oxide films grow with life | Afterwards, yes (RCC_RSR POR/BOR + boot counter) | Power loss is worse than a reset: `.noinit` SRAM and the VBAT domain (VBAT copper-tied to VDD) **vanish together** | Existing immunity is ~1 ms (the gate charges through R1's 100k from −7.64 V to the worst-case −2.2 V threshold in about 0.95 ms) + 12.5–18 ms from the logic-side 470 µF. The residual risk is a **magnet-shift-class long open**, covered by F-4's reference-free live-evidence path. H-7 (R2 10k → 1k, raising the wetting current) needs zero new part numbers |
| **V-12** | **An open pull-pin reads as "pulled"** | `PULLPIN = {R36.1, R37.1, U1.61}`, R36 10k pull-up to 3V3, R37 1k in series to J6.1, J6.2 = GND. A broken wire = 3.30 V = "pulled", i.e. the permissive state | Yes (require firmware to **witness** a LOW → HIGH transition; high at power-up = fault) | If the pull-pin is given interlock authority: a broken wire silently removes the interlock (direction ①); a chafe to ground reads "inserted" in flight → **inhibits deployment** (direction ②). **No polarity is safe for both** | Firmware rule F-7: the pull-pin is **advisory only**, may only gate the ground PAD_ARMED → READY transition, and is **completely ignored** after launch detection; the witnessed transition is written to `.noinit` so a brown-out reset on the pad does not cause a refusal to arm |
| **V-13** | **QSPI /WP and /HOLD floating** | §1 deleted the two pull-ups on the grounds that "in 4-bit mode they are driven data lines". **But the part ships with QE = 0**: the JEDEC ID read, status-register reads and the write that sets QE are all single-line transfers during which QUADSPI does not drive IO2/IO3 | Indirectly (read-back verification fails), but §7's "all storage errors are non-fatal" guarantees it is silently swallowed | /HOLD floating low = the part freezes mid-transfer; /WP floating low + SRP = 1 = status register cannot be written. **And this is the very path that carries the self-test for "writes accepted but not stored"** | H-3: restore 2 × 10k (`C25744`, already used 13 times, zero new part numbers) |
| **V-14** | **A jumper or debris left between J2 pin 5 (3V3) and pin 6 (BOOT0)** | §1 explicitly replaced the BOOT0 button with "a jumper selects DFU" — i.e. **the normal maintenance action is shorting these two pins** | Completely undetectable (the ROM bootloader reports nothing, and the LEDs are invisible inside a closed rocket) | Every power-up enters the ROM bootloader and the flight software never runs. The gates are safe (PE4/PE5 are not in the AN2606 driven list), so this is a **silent ②**, not ① | Procedure P-2: the jumper is a bench tool and never flies; J2 wrapped in clear heat shrink before flight; **"a boot tone must be heard at power-up" is a hard go/no-go** — silence means abort (also covers V-14, I-1 and an unfinished erase) |
| **V-15** | **Roll-control integrator wind-up at zero dynamic pressure → all four servos hard-over, exactly at the fire instant** | §7 never says when roll control ends. In coast dynamic pressure goes to zero, the fins lose authority, and the integrator winds up to full deflection | Yes (rolling minimum of VBAT_SENSE + sign consistency between commanded and measured roll acceleration) | Rev G §5.5: four stalled servos at 7.66 A + a fire at 6.81–9.84 A = **14.5–17.5 A**, on the same RAW and the same 492 µF. With a 6.2 V battery RAW drops to 4.03 V and VLOGIC to 3.63 V < the AP63203's 3.8 V minimum input → brown-out reset, **exactly at the moment of firing**. Does not happen with a full 8.4 V battery | Firmware rule F-5: **end roll control at burnout** (the mission objective is over by then) + command all four to the 1520 µs centre 200 ms before firing, then stop PWM + anti-windup clamping |
| **V-16** | **A stray strand bridging PYRO_BUS to the same channel's OUT** | `J4.3 (PYRO_BUS)` is next to `J4.4 (PYRO1_OUT)`; in rev G's order `PYRO1_B` is next to `PYRO1_A` | **Not at all.** The drain is pulled to PYRO_BUS, so `PYRO*_CONT` reads exactly the healthy 0.764 V, and H-1's cold test reads healthy too | At fire time a bus-to-ground dead short → fuse blows → both channels dead, and the igniter never even heats | Only procedure P-1: with ARM out and both igniters fitted, measure `J4.4 ↔ J4.5` and `J4.6 ↔ J4.5` on a DMM low-current range; they must read the igniter resistance (≥ 1.0 Ω, a rev G hard requirement), and near zero means abort. Record the values on the flight card |
| **V-17** | **J-ARM pin definitions conflict between two documents, and nobody has ruled** | Netlist: `J4.1 = RAW / J4.2, 3, 5 = PYRO_BUS / J4.4 = PYRO1_OUT / J4.6 = PYRO2_OUT`. Rev G §3.3, aft → forward: `PYRO1_B / PYRO1_A / PYRO2_B / PYRO2_A / ARM_A / ARM_B`. **They differ** | N/A | This is the connector the operator terminates live-charge leads into by hand, outside the airframe, from a drawing — and rev G §7.3-3 says it is **unreachable once inside the airframe**. Miswired = ① or ② | Rule before fab and write down which wins; silkscreen must print **function names**, not numbers; the schematic notes have already shown this library's pin-numbering conventions cannot be extrapolated (two LEDs on the same board with opposite polarity numbering) |
| **V-18** | **The ARM plug is physically unreachable in flight configuration** | Rev G §7.3-3: the DB128V screw axis is ~5.25 mm inside the wire-entry face, J-ARM has 8.34 mm of clearance, an M2.5 screwdriver will not fit → "all 6 ARM/PYRO wires must be terminated outside the airframe … any re-termination on the pad requires pulling the sled"; §3.4: "no service port inside the airframe" | N/A | **The premise of the entire safety argument ("the ARM plug goes in last and comes out first") does not hold in flight configuration.** Either it becomes a flying plug dangling outside the airframe (new failures: yanked off by the harness at 30 g, chafing on the airframe wall), or it is already in when the airframe is closed and the reed switch becomes the only pad interlock — and the reed switch **has no state readback in the netlist** | Must be ruled before fab (see H-6 in §4). The second most important open item in this review |
| **V-19** | **No LANDED state → no location, no landing report, no disarm** | Undefined in §7 | N/A | A rocket that deploys normally and drifts 1–2 km downwind into crops is as completely lost as a ballistic one, and the log is lost with it (no telemetry on board; LoRa is unfitted pads only) | Firmware F-8 + procedure: **a permanently fitted independent commercial GPS tracker from the first flight** (own battery, own switch). The best value item on this list |
| **V-20** | **The buzzer is inaudible at any legal safe distance; and "silence" has five meanings** | MLT-8530 rated 80 dB @ 10 cm → **30.3 dB** free-field at 30.5 m, lower through the airframe, against a 45–55 dBA site background. `LS1.1 = 3V3`, so a flat battery, an open reed switch, a dead buck, a hung MCU, an open coil and firmware that didn't intend to beep are **acoustically identical** | N/A (a design property) | The operator walks away believing the rocket is armed when it is actually dead, or the reverse | Firmware F-15 (**silence is always a fault**; an unconditional "proof of life" chirp within 50 ms of reset) + procedure P-4 (**the last step is confirming the READY tone at ≤ 1 m; after walking away there is no further information**) + aim one vent at the buzzer as a sound port |

---

## 2. Ruling on the watchdog / reset chain

### 2.1 Diagnosis: the chain was misdiagnosed, and the reality is worse

The brief's chain was: `IMU stops → IWDG not fed → reset → permanently disarmed → no deployment`. Three corrections:

1. **"Permanently disarmed" misreads the frozen text.** §7.4 says `never automatically re-arm after a reset (requires an explicit ground command **or a definite flight-phase condition**)`. The second disjunct already authorises what we want to do — **the rule is not wrong, it is undefined**. So this section does not overturn §7.4; it pins down that "definite flight-phase condition".
2. **Even with the arm bit correctly restored, the rocket will not deploy.** The state machine also restarts in PAD, and launch detection is a boost-transient criterion that will never be true again at 2 km and 0 m/s. **What must survive a reset is the flight phase, the pad pressure reference, the launch time and each channel's fired flag — not just one arm bit.**
3. **The IMU is only one entry point, and a different feeding scheme does nothing for the others**: (a) resets from the fire event's own ground bounce and drain avalanche; (b) reed-switch bounce — a **power loss**, not a reset, which takes `.noinit` and the VBAT domain with it; (c) V-15's concurrent stall + fire droop; (d) HardFault; (e) **DRDY stuck or chattering** — under the current rule it would **keep feeding the dog** at kHz rates while starving the main loop, a completely silent failure with the watchdog pointed at exactly the wrong task.

### 2.2 Ruling

**Reject "add a second timer that feeds the dog"**: that only proves the NVIC is alive and does nothing for anything downstream of a reset.

**Adopt a dual-supervisor structure + survivable reset.**

- **SAFETY task**: `TIM6` or `TIM7` update interrupt, **100 Hz**, priority above logging and below the DRDY ISR. It exclusively owns: non-blocking MS5611 reads, `PC0/PC1/PC4/PC5` sampling, the flight state machine, launch/apogee/main criteria, pyro gate arbitration, and updates to the `.noinit` flight record. **The IWDG is fed only at the end of a complete SAFETY pass.**
- **Key qualification (without it the kill chain just moves from the IMU to the barometer)**: the feed condition is **control flow completing**, **never any I/O succeeding**. Every peripheral transaction in a SAFETY pass must be non-blocking with a hard timeout, and **a timeout is a normal exit** that marks that sensor invalid and lets the pass finish normally. The invariant goes into the specification: *a SAFETY pass must complete in bounded time under any peripheral behaviour.*
- **Shorten the period from ≥ 2 s to ~400 ms** (PR = /4, RLR ≈ 3200, checked against the fast LSI corner). The original ≥ 2 s tolerated slow logging, which is no longer on this path. The real reason to shorten it is **V-3**: with a gate stuck on, the IWDG period is the FET's last thermal protection (2 s × 6.81 A = 93 A²s, enough to destroy the FET and blow the shared fuse). At 100 Hz, 400 ms still leaves 40 passes of margin.
- **Start the IWDG in software** (option byte left in software mode), and **only after the SAFETY task has completed its first tick**. Reason: hardware start + an IMU/flash that never comes up = an endless reset loop in the air. *(ST's own HAL header contradicts itself on the polarity comment for `OB_IWDG1_SW`; check against RM0433 before programming.)*
- **CONTROL supervisor**: the DRDY ISR only increments a counter; SAFETY checks it every pass. No advance for 25 ms → `IMU_STALL`: servos to 1520 µs centre, then PWM off, roll control off, switch the apogee vote set, set the flag, log, annunciate, up to 3 bounded re-initialisations (1 s apart), then structural removal (swap a function pointer for a stub, not an `if` every cycle). **An IMU stall never resets the MCU.**
- **DRDY rate limit**: > 1.2 kHz of edges within 100 ms → mask the EXTI and let the SAFETY task poll the IMU instead. This removes the silent mode in 2.1(e).
- **Enable HSE CSS** (F-2). A second entry point fully independent of the IMU, and the new watchdog cannot save it either (the timers grow on the same dead clock tree).

### 2.3 Rule text replacing §7.4 (paste directly into the specification)

```
§7.4' Pyro arming, reset recovery and the safe state

7.4'.1  The first instructions after reset (after clock init, before anything else, in this order):
        a) Configure PE4, PYRO2_GATE and every sentinel pin as push-pull outputs driven low (GPIOE->BSRR);
        b) Read RCC_RSR into the flight record, then write RMVF; classify in the order
           PORRSTF → BORRSTF → IWDG1RSTF → WWDG1RSTF → SFTRSTF → LPWRRSTF → PINRSTF.
           (STM32 internal resets also pull NRST low, so PINRSTF can be set together with other flags;
            hence the ordering. This behaviour was not re-checked against RM0433 and is used only for
            log classification, never in any arming criterion.)
        c) The pyros are DISARMED at the instant of reset and stay DISARMED until the criterion in
           7.4'.4 has been evaluated.

7.4'.2  The flight record lives in a .noinit section in the linker script (AXI SRAM or SRAM4),
        not in BKPSRAM. Reason: VBAT is copper-tied to VDD (§3.1 pin 6), so BKPSRAM has no retention
        advantage over ordinary SRAM, yet adds two silent failure points (PWR_CR1 DBP / BKPRAMEN).
        SRAM contents are not cleared by any reset, so the record survives IWDG/software/NRST/BOR
        resets and disappears only on a real power loss — exactly the semantics needed.
        Adding a VBAT coin cell or LSE to "improve retention" is forbidden: it would let a stale
        "in flight" record survive into the next pad session, turning reset recovery into a pad hazard.

        Record format (double-buffered, each copy with its own CRC32 and incrementing sequence number,
        so a reset halfway through a write cannot destroy both):
        magic | version | seq | power_session_id | state | flags | rcc_rsr | reset_count |
        t_since_launch_ms | pad_pressure_pa | agl_max_m | agl_now_m | vspeed_now |
        flight_proven | fired_mask | fire_attempts[2] | pullpin_edge_seen | crc32

        power_session_id is derived from the reset cause: POR or BOR always starts a new session and
        invalidates any inherited record. This closes the path "a phase word left by the previous
        flight/test is inherited after a reset on the pad".

7.4'.3  Non-volatile phase log: an append-only phase log in a pre-erased reserved W25Q128 sector,
        each entry ≤ 32 bytes with this flight's nonce, a sequence number and a CRC, **written only
        on phase transitions** (ARMED / LAUNCH / BURNOUT / APOGEE / FIRE1 / FIRE2 / RESET / LANDED);
        at boot take the last valid entry.
        pad_pressure_pa and the configuration are written **at the ARM instant**, not at launch
        detection — launch detection is the moment of maximum vibration and current in the whole
        flight, the worst possible moment to start a flash transaction.
        The sector is pre-erased on the bench and never erased in flight. A failed write only sets
        a flag and never blocks anything.

7.4'.4  Post-reset arming criterion — only live evidence measured after lift-off.
        In flight, no sense circuit may veto arming or firing:
        ARM_SENSE, PULLPIN and VBAT_SENSE are only logged and annunciated in the air.
        (If ARM_SENSE really is 0, commanding a fire draws no current anyway; if the divider
         resistor has cracked, commanding the fire as usual saves the rocket. On the ground these
         three are hard refusals, because refusing on the ground is free.)

        Condition B (record survived): magic/version/CRC/sequence valid, power_session_id matches
                 this session, state ∈ {BOOST, COAST, DESCENT}, t_since_launch_ms < 600000,
                 and the baro altitude measured after boot is more than 100 m above the stored pad
                 reference.
        Condition C (record lost, i.e. a real power loss): within a 500 ms window after boot,
                 (i) a sustained baro descent rate |v| > 30 m/s for 500 ms, or
                 (ii) free fall |a| < 0.3 g for 300 ms.
        **No gyro criterion** (hand rotation easily exceeds 60 °/s).
        **No "pressure stable / vertical speed near zero" criterion** (a rocket lying in the
        grass satisfies it too).

        B holds → restore phase, t_since_launch, pad_pressure, agl_max and fired_mask; continue flight.
        Only C holds → enter DESCENT_UNKNOWN, arm, and **run no apogee vote** (see 7.4'.5).
        Neither holds → treat as on the pad and follow the normal ground arming procedure.

7.4'.5  DESCENT_UNKNOWN behaviour (by definition the rocket is past apogee, so apogee logic is
        meaningless and dangerous): the only action is descent-based: if a sustained baro descent
        rate > 30 m/s lasts 0.5 s and the drogue channel has not fired, fire the drogue channel
        immediately; then, if the pad reference can be recovered from flash, fire the main by AGL,
        otherwise fire the main at "drogue fire + t_main_nominal".
        If **no sustained descent is measured** within the specified window after entering this
        state, disarm permanently and alarm continuously.
        Sound the alarm tone continuously for the whole time in this state.

7.4'.6  More than 3 resets in one continuous flight → MINIMAL mode: QUADSPI logging off, GNSS off,
        USB off, TIM5/servos off; only barometer + IMU + pyros + buzzer remain.

7.4'.7  Fired flags: a channel with its fired_mask bit set must not fire again unless its CONT
        still reads closed. When fired_mask is unknown, treat every channel as unfired — one extra
        pulse into a burnt bridgewire is harmless, one missed pulse is the vehicle. CONT must be
        read together with ARM_SENSE:
        ARM_SENSE ≈ 0.764 V and CONT ≈ 0.764 V = bridgewire present;
        ARM_SENSE ≈ 0.764 V and CONT ≈ 0 V = already fired or bridgewire missing;
        **with ARM_SENSE ≈ 0, CONT carries no information and must never be used to set a fired
        flag** (plug out, blown fuse and a loose terminal all make both CONT lines read 0).

7.4'.8  The in-air boot path must be a separate code path from the pad boot path, selected in
        the first microseconds by RCC_RSR + the record. The in-air path skips flash erase, GNSS
        configuration, long self-tests and USB enumeration, and **never runs any self-test that
        drives a pyro gate**.
        Budget and measure: reset to "able to evaluate the apogee criterion" ≤ 250 ms, listed as an
        acceptance test (one MS5611 OSR4096 conversion is 9.04 ms; two or three samples for vertical
        speed make the budget achievable, but it must be measured).

7.4'.9  Landing: baro altitude stable within ±3 m for 10 s **or** |a| within 1 g ±0.3 g and
        |ω| < 5 °/s for 10 s **or** more than T_max since launch — any of these enters LANDED:
        drive both gates low, set a software latch that only a power-off can clear, write a LANDED
        log entry, stop the 800 Hz loop and logging, and switch the buzzer to locator mode.
        The landing criterion must require **stable altitude**, not "slow descent", and must enforce
        a T_min floor, or a misjudgement under canopy would inhibit the main.
```

### 2.4 Why this is safe on the pad

- Every physical quantity in the criterion is **unreachable** within human reach: a 100 m altitude difference, a sustained 30 m/s descent, sustained 0.3 g free fall. The two deleted criteria (gyro rotation, stable pressure) are exactly the reachable ones.
- **Arming ≠ firing.** When condition B holds a real apogee decision is still required; when condition C holds the only action requires a sustained 30 m/s descent. And during handling the ARM link is physically unplugged anyway.
- The comparison with today is asymmetric: **under the current rule one fault (an IMU hiccup) is total loss; under the new rule an inadvertent fire on the pad needs a forged record + a physically impossible measurement + a wrong apogee decision — three independent failures.**
- The record vanishes on a real power loss (VBAT = VDD), an **accidental virtue** of this design that must be written down and protected as a safety decision (F-17).

---

## 3. Redundancy architecture

### 3.1 The layered picture

| Layer | Content | Covers | Does not cover |
|---|---|---|---|
| **Hardware (on board)** | Two pyro channels; one IMU providing two votes, one barometer providing one; `PC0/PC1` are ADC123 channels, so ADC1 and ADC3 can read them and cross-check | Open/dud igniters, a single open FET; a single ADC peripheral/calibration fault | **Everything shared upstream**: battery, reed switch, Q1/Q2, RAW, ARM plug, 5 A fuse, PYRO_BUS, buck, 3V3, MCU, firmware image, L2/3V3A, the baro bay. The dual ADC read shares VREF, so it is useless against V-4 |
| **Firmware** | Dual supervisors (SAFETY 100 Hz + CONTROL); cross-reset phase recovery (`.noinit` + flash log); per-sensor degraded modes; 2-of-N apogee vote; descent-rate backup for the main; timer fallbacks; fire-result verification and cross-channel escalation | Sensors stalling/lying, resets, power loss, a blocked static port, drogue failure, single-channel fire failure | A dead MCU, dead power, defects in the firmware itself |
| **Procedure** | **A permanently fitted independent commercial altimeter** (own battery/switch/igniter/charge); **a permanently fitted independent GPS tracker**; a pad checklist; harness standards; per-wire DMM check of the terminals; ground ejection tests | **Everything** the two layers above leave: MCU, buck, battery, switch, fuse, firmware defects, L2 | The shared vents and av-bay (V-8); shared shear pins, shock cord and parachutes |

### 3.2 Independent backup altimeter: permanent, not "first flight only"

**Ruling: permanent.** The reason is not conservatism: V-10 and V-4 cannot be covered by any on-board means, the firmware will change between flights, and this rocket carries a roll-control loop that has never flown — which can fly the rocket off course by itself.

**The definition of independence must be hard-coded** (it is the definition in TRA L3 certification and IREC DTEG §6.9.1, worded the same in both: "completely separate systems, including batteries, switches, avionics, and energetics"; DTEG §6.9.2 also states explicitly "A dual pole switch does not satisfy the requirement for redundant arming switches"):
- Its own battery, its own arming switch, its own igniter, its own charge well.
- **The two altimeters never share one igniter** — one altimeter's fire current would return through the other's output stage.
- Two charges in one well is standard and acceptable; **the two charges for the same event must be staggered** (the AltusMetrum manual: "it's often important to ensure that multiple apogee charges don't fire at precisely the same time, as that can over pressurize the apogee deployment bay and cause a structural failure of the air-frame"; its Redundant Apogee mode staggers by 2 seconds by default).

**The honest cost, to be settled now**: rev G §7.2 closes the whole av-bay with **+1.558 mm of radial margin** (the binding item is the plugged servo header), §7.3-2 makes a battery width ≤ 36 mm a hard constraint, and §7.3-3 finds the terminals cannot be tightened inside the airframe. **Adding another altimeter + battery + switch hole + two charge wells is not "one sled position"; it means a longer coupler, a separate bay section, or a 4 in airframe.** That is a vehicle-level decision and must be made before fab, or this "must" will be quietly dropped at assembly — the worst outcome of all.

**Channel roles (§7 never says whether this rocket is single- or dual-deploy — the biggest open item in this review)**:
- If **dual deploy**: on this board ch1 = apogee/drogue, ch2 = main, and all redundancy comes from the commercial unit. Then **the board has zero redundancy for either event**, and the backup altimeter goes from "should" to "no fly without it".
- If **single deploy**: ch2 is free on-board deployment redundancy — fire ch2 **unconditionally** 2.0 s after ch1 is commanded (do not gate it on "whether ch1 succeeded", which is unobservable), and size both charges for simultaneous firing.
- **If the backup altimeter is not flown on a given flight, this board must be reconfigured as single deploy with both channels on apogee. Never fly dual deploy on a single-string board.**

### 3.3 Items deliberately not made redundant, and why
| Not done | Reason |
|---|---|
| **A second barometer** | Both chips would share the same bay, the same vents, the same 3V3A, the same I2C1 and the same driver. The dominant barometer failure in this field is "the bay pressure is wrong", not "the chip died" — the two would **read wrong together**. Spend the money on vent workmanship and the backup altimeter |
| **A second IMU** | It buys back a ④ (roll control), while ② is still being bought with free firmware. Wrong spending order. AltusMetrum's flagship TeleMetrum also has one barometer and one accelerometer, and PerfectFlite has one barometer — shipping products get their reliability from system-level independence and mechanical discipline, not stacked on-board sensors |
| **Redundant MCU / voting pair / a second buck** | Same; and a second buck's OR network would introduce a new common-mode point |
| **microSD or a second flash** | Class ⑤. §7's "storage error paths are all non-fatal + logging is a low-priority ring-buffer consumer" is **correct** and must stay as is. Any change trading ② for ⑤ runs backwards |
| **A supply-supervisor hardware clamp on the pyro gates** (like the "disables all outputs when the microcontroller voltage is below 2.7V" on the Blue Raven product page) | It turns a ① protection into a new single point that can **block firing** (supervisor output stuck asserted = neither channel ever fires = ②). This design already has something stronger: the removable fused ARM link is a **physical break** no software state can bypass. If it is ever added, H-1's cold self-test must be extended to "prove the clamp releases", or it is not added |
| **A separate battery for the pyro bus** (leave J4.1/RAW empty and feed PYRO_BUS from an external pyro battery) | **Explicitly rejected.** It deletes a whole layer of physical interlock: today PYRO_BUS is live only when "reed switch closed **and** ARM plug in"; afterwards the ARM plug is the only condition. Worse, it **rebuilds by hand the hazard that §1's S3 ruling removed**: with the board off (3V3 = 0) and the plug in, 8.4 V reaches three ADC pins with VDD = 0 through R14 (10k) / R18 (10k), while §3 says FT/TT pins have `IINJ = −5/+0 mA, positive injection not allowed at all`. And it does not deliver the claimed benefit — fire current still returns igniter → drain → source → board ground plane, so the high-di/dt loop still passes by the MCU and sensors. The energy independence that is really needed lives off the board, in the backup altimeter's own battery |
| **Shortening the fire pulse to 12 ms** | See the rejected items in §4 |
| **VBAT coin cell / LSE** | See F-17. Keeping VBAT = VDD is a safety decision, not a part-saving one |

---

## 4. Hardware change list

> All are schematic-stage changes (the PCB was not yet routed). Baseline: 101 soldered parts / 39 part numbers.

### 4.1 MUST

**H-1 — Cold pull-up on the pyro drains + reverse blocking. `+2 × 47 kΩ 0603` + `1 × BAT54A SOT-23`.**

Connection: `3V3 → BAT54A common anode; cathode 1 → 47k → PYRO1_OUT; cathode 2 → 47k → PYRO2_OUT`.

- **Covers**: I-1 (FET short, completely untestable today, where the only "test" is inserting the plug and seeing whether it goes off), open FETs, a **cold** reading of igniter present/open, ADC channels stuck at zero, and makes the I-2/I-3 bridges testable. It turns §7's "FET short self-test", **which cannot be implemented on this hardware**, into a real four-state measurement.
- **Values (ARM plug out, both gates low, 3V3 = 3.3 V, solved simultaneously with R14/R15, R18/R19, R22/R23 all 10k/1k; the three ADC nodes are **one** resistor network and must be read jointly, not channel by channel)**:

  | PC5 (ARM_SENSE) | PC0 | PC1 | Reading |
  |---|---|---|---|
  | 40.5 mV | 40.5 mV | 40.5 mV | Both igniters present, both FETs healthy (**normal flight configuration**) |
  | 31.4 mV | 31.4 mV | 56.9 mV | Igniter on ch1 only |
  | 31.4 mV | 56.9 mV | 31.4 mV | Igniter on ch2 only |
  | 0 | 56.9 mV | 56.9 mV | No igniter on either channel |
  | 0 | 0 | 0 or 56.9 mV | **At least one FET shorted / drain shorted to ground → continuous tone, refuse everything, do not touch the ARM plug** |
  | Any > 100 mV | | | Pull-up part or divider damaged → continuous tone, refuse to arm |

  Adjacent states differ by 16.4–25.5 mV; a 16-bit LSB is 50.35 µV → **326–506 LSB**, ample with oversampling. Bridgewire current **31.4–40.5 µA** (not 62.9 µA — the pull-up current splits between the drain's own 11k divider and the 11k through the bridgewire), 19–24× below the 0.764 mA armed-state test current already accepted today.
- **Active half (optional but strongly recommended)**: with the plug out, drive each gate high for 10 ms in turn; CONT must collapse to ≈ 0 mV and then recover; no collapse = 470R open / gate bond broken / FET open. The current through the bridgewire during this comes from the other channel's pull-up, about **70 µA** (not zero). This is the **only** way in the whole design to verify the firing path end to end.
- **New failure mode introduced**: **a shorted pull-up resistor is class ①.** Without the BAT54A: with the ARM plug in, the drain is clamped to 3.3 V, 5.1 V appears across the bridgewire, and at rev G's mandatory ≥ 1.0 Ω that is **5.1 A → immediate fire**. The BAT54A is there to remove exactly that: with the drain at 8.4 V above the 3.3 V anode, the diode is reverse-biased and the path is fully open (reverse leakage at the µA level, flowing from the drain into 3V3, which can fire nothing). The diode's forward drop lowers the cold-test source to about 3.1 V, scaling the table down by 6 %; calibrate once on the bench. Vf's temperature drift maps to about 1.5 mV at the ADC nodes, acceptable. **The diode itself open** = cold test reads all zeros = false "FET short" = scrub the flight, which is the safe direction.
- **Cost**: +3 parts, +1 part number (47k is already R4's part number; the BAT54A is new, but it is the same family prepared for the pull-pin clamp in frozen §8 item 6). The layout must stay out of rev G §4's Z2 high-current corner.

**H-2 — Separate the two pyro gates and surround them with sentinel pins. Zero parts.**

- Today: `PE3 = LED_RED (2) / PE4 = PYRO1_GATE (3) / PE5 = PYRO2_GATE (4) / PE6 = BUZZ_GATE (5)`.
- Change to: `PYRO1_GATE = PE4 (pin 3)` unchanged; `PYRO2_GATE → PE13 (pin 43)`; `LED_RED → PE8 (pin 38)`; `BUZZ_GATE → PE15 (pin 45)`. **`PE3 (2), PE5 (4), PE6 (5), PE12 (42), PE14 (44)` are all configured as push-pull outputs permanently driven low and connected to no net on the PCB**, as sentinels. A solder bridge onto a sentinel only pulls the gate low.
- **Do not** put the buzzer on pins 97/98: they are next to `pin 96 = PB9 = I2C1_SDA`, which would aim a 2.7 kHz square wave at the deployment-critical sensor bus. And **do not** add sentinels only on the outside while leaving the two gates adjacent (I-3 is not protected by any outside sentinel).
- **New failure mode introduced**: a bridge between `PE2 (pin 1) = QSPI_IO2` and the `PE3` sentinel shorts a high-speed flash data line onto an output driven low and kills QSPI logging — **exactly the intended trade: a ① hazard exchanged for a ⑤**. Also, 5 GPIOs are permanently spent "doing nothing" (about 40 remain free), and a careless GPIO initialisation sweep would silently remove the sentinels → the sentinel configuration must live in the same function that drives the pyro gates low.
- **Must check**: whether `PE13/PE15` are in the H743 bootloader list of AN2606 Table 113 (PE pins usually are not, but this is **marked unverified**), and whether their reset state has no pull. Note `PE4 = TIM1_CH3N? / PE13 = TIM1_CH3 / PE5 = TIM15_CH1 / PE4 = TIM15_CH1N` — however they are arranged, the pyro gates land on timer AFs, so the accompanying firmware rule F-16 (never enable the RCC clocks of TIM1 and TIM15 + lock PE3/PE4/PE5/PE6/PE12/PE13/PE14 with `GPIOE->LCKR`) is **mandatory**.

**H-3 — Restore the QSPI /WP and /HOLD pull-ups. `+2 × 10 kΩ` (`C25744`, already used 13 times, zero new part numbers).**

- Covers V-13. The part ships with `QE = 0`, so the JEDEC ID read, the three status-register reads and the write that sets QE are all single-line transactions during which QUADSPI does not drive `PE2/PD13`. §1's deletion argument ("driven data lines in 4-bit mode") only holds after QE is set, and **the self-test itself runs before that**.
- New failure mode: two more solder joints and a little capacitive load on two QSPI data lines; irrelevant on 20 mm traces.

**H-4 — Add a pull-down on `VBUS_SENSE (PD15)`. `+1 × 100 kΩ` (already R3/R1's part number).**

- Today `VBUS_SENSE = {R9.2, U1.62}`, R9 = 100k to VBUS, **no pull-down**. Both configurations are broken: with no internal pull, after unplugging PD15 is a truly floating CMOS input that drifts anywhere (→ may enable the OTG stack in flight, exactly what §7.11 prevents, and may cause a false "USB present → refuse to arm" scrub); with the internal pull-down (30/40/50 kΩ on the H7), a plugged cable reads only `5.0 × 40 / 140 = 1.43 V`, below the FT input VIH ≈ 1.79 V → **USB is never detected**.
- Add 100k to ground and force `PUPDR[PD15] = 00`: 2.50 V plugged (still 2.20 V at USB's 4.40 V minimum), a hard 0 V unplugged. The divider also halves VBUS overvoltage events on a pin limited to 7.3 V.
- New failure mode: none. But **the external pull-down only works with the internal pull disabled**; both together give 1.11 V and reproduce the failure.

**H-5 — Rule on the J-ARM pin definition + split PYRO_BUS into two independently fused buses. Zero parts on the board.**

- V-17 must be ruled first (netlist vs rev G §3.3). Also fix V-5: split `PYRO_BUS` into `PYRO1_BUS` (carrying R14's ARM_SENSE divider) and `PYRO2_BUS`, make the 6-pos terminal `RAW_A / PYRO1_BUS / PYRO1_OUT / RAW_B / PYRO2_BUS / PYRO2_OUT`, and make the removable arming plug a four-wire, two-fuse part (RAW_A → F1 → PYRO1_BUS, RAW_B → F2 → PYRO2_BUS).
- **Covers**: a shorted igniter on one channel no longer kills the other (today it necessarily does).
- **Cost**: zero board parts; +1 fuse holder in the plug; ARM_SENSE can only see the ch1 bus (ch2 bus visibility comes from H-1's cold test and the CONT readings).
- **New failure modes**: a stray strand between `RAW_A/RAW_B` and the adjacent BUS position is still I-4, now in two places; the plug gains two more contacts in a 30 g environment, and an intermittent contact = no deployment. **If not adopted**, the document must say in black and white "the two pyro channels are not redundant against anything upstream", and the backup altimeter is promoted from "should" to "no fly without it".
- **Do not** lower the fuse rating: a normal fire is 20 ms × 6.81 A = **0.93 A²s**, while a blade fuse's melting I²t is tens of A²s — a normal fire does not threaten it at all. The real threats are shorts (V-5) and a gate stuck on (V-3).

**H-6 — Rule on the physical form of the ARM link (V-18). Zero parts on the board; a vehicle-level decision.**

Pick one of two, now:
- (a) Run a short pigtail from J-ARM's RAW/BUS positions to a connector outside the airframe **with positive locking, keying and strain relief**, treated as flight hardware (pull test + checklist item + Remove-Before-Flight streamer). New failures: yanked off by the harness at 30 g = both channels dead; chafing on the airframe wall = I-4.
- (b) Accept that the ARM link is already in when the airframe is closed and the reed switch is the only pad interlock. Then **the T-1 bench test, a continuous power-on heartbeat tone and F-14's negative ARM_SENSE check are upgraded from "recommended" to "mandatory"**, because no physical break is within human reach any more.

### 4.2 SHOULD

**H-7 — `R2` from 10 kΩ to 1 kΩ. Zero parts.** Switch current 76 µA → 760 µA, out of the oxide-film regime of non-hermetic contacts; also improves `Vgs` from −7.64 V to −8.32 V @ 8.4 V (AON6403 Vgs absolute max ±20 V, safe). New failure: the turn-off gate charging constant changes very little (the turn-off path is still R1's 100k alone); no material effect.

**H-8 — Unidirectional TVS (SMAJ18A class) on each pyro drain ×2. +2 parts, +1 part number.** Covers EMI injected into the MCU/sensors by the 36 V fast edge at the fire instant (V-3, and the highest-probability entry to the kill chain: "your own first charge resets you"). **The variant "reuse the BOM's SS34 from drain to bus" is explicitly rejected**: the SS34's reverse leakage is already hundreds of µA at 25 °C and rises about an order of magnitude every 25 °C, while the whole continuity test runs on only 0.764 mA — in a sun-baked airframe it would pull an **open** igniter to a "healthy" reading, turning a detected failure into an undetected one, which is disqualifying by this document's criteria. New failure: a shorted TVS = that drain permanently grounded = that channel cannot fire; H-1's cold test must cover it, so H-1 must land first.

**H-9 — A 1 µF/50 V 0603 (`C15849`, zero new part numbers) from `GATE_SW` to the common-source node (**not** to ground). +1 part, rated "consider".**
- Existing bounce immunity is already ~1 ms (the gate charges through R1's 100k from −7.64 V to the worst-case −2.2 V threshold in about 0.95 ms) plus 12.5–18 ms of logic-side hold-up; reed **contact bounce** is already covered. This capacitor raises immunity to about 124 ms, aimed at **magnet-shift-class long opens**.
- The direction must be gate-source, not gate-ground: a shorted gate-source capacitor → Vgs = 0 → FET off → board dead on the bench (safe direction); a shorted gate-ground capacitor would **lock the board permanently on**, which is class ①.
- Cost: about 124 ms of power-off delay — "flip the switch" and "confirm power is off" no longer happen together, so the procedure must change to confirming silence and no lights. X5R loses 20–35 % at 8.4 V DC bias; recompute the "124 ms" with the real capacitance.
- **Note that rev G §5.7 already overturned the 99 A hot-plug inrush** (the gate network's 9.091 kΩ Thevenin × Ciss 6100–9120 pF → τ 55–83 µs is itself a soft start), so **do not** use "inrush suppression" as a reason again.

**H-10 — BAT54S clamp on the pull-pin to 3V3/GND. +1 part (same family as H-1).** Closes frozen §8 item 6. §8 thought the 1k series resistor was enough, but the arithmetic: with a chafe onto 8.4 V the only path is the 10k pull-up, and the pin sees `3.3 + 5.1 × 10 / 11 = 7.94 V`, above the 7.3 V absolute limit, and H743 FT pins have **no** clamp diode to VDD. No resistor change alone works (withstanding it needs > 2.76 k, reading a low needs < 4.0 k, with no usable margin at either end). New failure: a shorted BAT54S pins PD14 to a rail → covered for free by the checklist item "PULLPIN must change state when the pin is pulled".

### 4.3 Explicitly rejected

| Rejected | Reason |
|---|---|
| **Shortening the fire pulse from 20 ms to 12 ms** | Trades ② for ⑤, exactly the backwards trade this document forbids. The fuse is not at risk at all (0.93–1.41 A²s vs tens of A²s). A cold, high-resistance, badly crimped igniter needs **more** energy. For comparison, the Blue Raven's default output duration is **1.0 second**; this design is already 50× shorter than a shipping product — the thin side is this one, not the other. If it changes at all, the direction is **longer**, to 25–30 ms after checking against the AO3400A's transient thermal impedance (rev G's 25 ms hard abort is the upper bound) |
| **Cutting the RAW → J4.1 copper and using an external pyro battery** | See §3.3. Deletes a physical interlock + rebuilds the S3 hazard + the claimed decoupling does not materialise (the return still runs through the board ground plane) |
| **A software-controlled high-side series switch on the pyro bus ("two switches in series", textbook style)** | This design already has a **stronger** series break: the removable fused ARM plug, physically open and impossible for software to bypass. A software-controlled series switch will be stuck closed exactly when it most needs to be open, while introducing a new common-mode blocking point for **both** channels (① traded for ②) |
| **Second barometer / second IMU / redundant MCU / microSD** | See §3.3 |
| **VBAT coin cell or LSE** | See F-17 |
| **BOR at Level 2/3** | See F-3 |

**Net hardware additions (MUST items): +6 parts (47k × 2, BAT54A × 1, 10k × 2, 100k × 1), +1 part number (BAT54A).** Against 101 parts / 39 part numbers that is **+5.9 % placements, +2.6 % part numbers**. All 0402/0603/SOT-23, about 15 mm² in total, placeable between the MCU and the pyro block in the y 34–46 zone (**not in rev G §4's Z2 high-current corner, which has only 0.20 mm left**).

---

## 5. Firmware rules (replacing / revising frozen §7)

> Imperative, each ready to go into the specification. Those with a § number state what they replace.

**F-1 (replaces §7.1)** Two loops, two clocks. Roll control stays in the 800 Hz DRDY ISR (the sensor's clock). **Launch detection, apogee detection, main detection, pyro arbitration, the flight record and IWDG feeding all move to a 100 Hz SAFETY timer ISR (TIM6/TIM7)**, consuming whatever sensor data is currently valid. The IWDG is fed only at the end of a complete SAFETY pass, **conditioned on control flow completing, not on any I/O succeeding**. Period ~400 ms. A SAFETY pass must complete in bounded time under any peripheral behaviour. No code path may disable interrupts for more than 20 µs; no ISR may busy-wait without a bound (always bounded with the free-running TIM2 microsecond timebase that §7.3 reserves). The flight-state structure shared between the loops uses single-writer discipline + seqlock snapshots.
- *New failure*: the IWDG no longer proves the roll loop is alive → a hung roll loop now only silently loses roll control (④) instead of resetting (②). This is a **deliberate trade**, but it means the CONTROL supervisor, its logging and its tones are now safety-related code and must be tested as such. A defect in the SAFETY task itself becomes the watchdog's new single point → that function must be short, allocation-free, simply branched, and unit-tested on its own.

**F-2 (new)** Enable `RCC_CR.CSSHSEON`. Put a timeout on the HSE-ready wait at boot, falling back to HSI. NMI handler: switch to a known HSI clock tree **and recompute every safety time constant** (200 → 64 MHz stretches a 20 ms pulse to 62 ms, a 333 Hz servo frame to 104 Hz, and every timer by 3.1×), set `CLOCK_DEGRADED`, log, annunciate, **keep flying, never reset**. Also cross-check the timebase for free in flight: TIM2 counts against the LSI-derived IWDG interval and against MS5611 conversion completion (OSR4096 8.22 ms typ / 9.04 ms max).

**F-3 (new)** Option byte `OB_BOR_LEVEL1` (ST's own `stm32h7xx_hal_flash_ex.h`: LEVEL0 1.6 V / LEVEL1 2.1 V / LEVEL2 2.4 V / LEVEL3 2.7 V; **exact rising/falling thresholds and hysteresis not checked against DS12110**). At every boot compare `FLASH_OPTSR_CUR` with the compile-time expectation and refuse to arm on mismatch (option bytes can be silently changed by a debugger session or a full erase). **Do not use Level 2/3**: that would turn survivable voltage dips into resets, trading ⑤ for ②. The cost of Level 1 is the W25Q128 (2.7 V minimum) running out of spec in the last 600 mV → covered by F-12's write inhibit. Also enable `PVD @ 2.85 V (VDD)` and `AVD @ 2.8 V (VDDA)`, each with hysteresis and a minimum re-trigger interval to prevent interrupt storms; **the PVD handler must not abort a fire pulse already more than 8 ms in** (a half fire is worse than no fire).

**F-4 (replaces §7.4)** Full text in §2.3.

**F-5 (new, revises §7.3)** Roll control ends at **burnout + margin**, not at apogee — the mission objective ends with the motor, and continuing to actuate only pollutes V2's velocity integral (the centripetal component on an off-axis accelerometer) and eats into the fire energy budget. 200 ms before any fire command: write **1520 µs** to all four (the HV6120's centre, not 1500 and not 0), stop PWM 200 ms later, and hold until 200 ms after the pulse.
- **Must be measured on the bench**: both official MKS pages return 404, and **no document says** whether the HV6120 holds its last position (at full torque) or goes limp with no signal. If it holds, `CCR = 0` neither unloads the current nor centres, and the whole §7.2 argument that "a servo line defined low after reset = safe" loses its basis. Method: load to an end stop, remove the signal, record holding current and whether it releases, and write the answer into §7.
- Servo stall detection: command near centre while `VBAT_SENSE` stays depressed for > 1 s → `SERVO_STALL`, drive PA0–PA3 low (held by the 10k pull-downs), log, annunciate. Absolute roll-rate limit |p| > 600 °/s → freeze the integrator, **centre immediately and give up roll control**.
- **Explicitly rejected: "command full opposite deflection when the gyro saturates"**: one possible cause of saturation is a reversed control sign, and commanding full deflection at maximum dynamic pressure on a clipped measurement escalates ④ to ②.

**F-6 (new)** A `LIFTOFF` latch is a **hard precondition on every firing path**, checked in ISR context alongside the ARM_SENSE and CONT checks, never cleared for the whole flight. Set when `(axial acceleration > 3 g for 100 ms)` **OR** `(when IMU_VALID is false: AGL > 30 m and climbing > 15 m/s for 200 ms)`. If both hold within 500 ms, also set `LAUNCH_CORROBORATED` (only that allows the timer fallback to act). **"Sustained" is the key**: a knock is a < 20 ms event.
- Also set a monotonic `FLIGHT_PROVEN` latch: `AGL_max ≥ 100 m` (relative to the pad reference) **or** a peak integrated velocity > 50 m/s. **It gates the entire apogee decision.**

**F-7 (new)** The pull-pin is advisory only: it only gates the ground `PAD_ARMED → READY` transition, must **witness** a LOW → HIGH transition (high at power-up = a fault code, not a permission), writes the transition event into the `.noinit` record so a brown-out reset on the pad does not cause a refusal to arm, and is **completely ignored after launch detection**. Log its level every housekeeping cycle.

**F-8 (new)** LANDED definition and behaviour: see 7.4'.9 in §2.3. After landing the buzzer switches to locator mode (300 ms / 5 s), SYSCLK drops, GNSS turns off (or keeps one last-position tone), and a 256-byte flight summary is written to **bank 2** of the MCU's internal flash (execution is from bank 1) — **only when LANDED and disarmed**, with the sector address checked against the linker script at compile time (H743 internal flash has 128 KB sectors and 256-bit words; a naive 256-byte write consumes a whole sector and stalls instruction fetch).

**F-9 (replaces §7.4's "pulse ≤ 20 ms")** **Hardware termination** of fire pulses: at the fire instant, load a dedicated timer whose ISR has the highest priority in the system (above DRDY) and whose only action is writing the clear to `GPIOE->BSRR`; where possible use a timer compare event triggering a DMA write to BSRR instead, so the pulse ends even if the CPU stops. Layer on top rev G §5.6's **independent TIM2-measured 25 ms hard abort**, and the SAFETY task's backstop: any gate high for more than 30 ms → drive both low unconditionally and set a fault. **Only one channel on at any time** is guaranteed structurally by **one single arbitration function** that takes a channel number and asserts the other channel is low before driving; two charges for the same event must be staggered.

**F-10 (revises the last sentence of §7.4, mandatory)** **In flight, ARM_SENSE and PYRO*_CONT are only logged and annunciated and must never veto a fire command.** On the ground they are hard refusals. The asymmetry must be written into the specification: firing into an open/absent bridgewire costs nothing, refusing to fire into a good one costs the vehicle; and both readings hang behind V-4's single inductor.

**F-11 (replaces §7.7)** Apogee detection.

- Per-cycle validity flags. `BARO_VALID` = PROM CRC-4 passed at boot **and** re-verified at arming **and** no I2C error within 200 ms **and** the **raw D1 words of the last 10 conversions not all identical** (**never threshold the engineering value** — pressure naturally stops changing at apogee, so a threshold detector would declare it dead exactly when it is needed; at OSR4096 real noise is several LSB of the 24-bit word, so bit-identical words are practically impossible) **and** D2 refreshing **and** 10–1200 mbar **and** |dP/dt| < 500 mbar/s **and** not within 500 ms after any fire. `IMU_VALID` = the DRDY count advancing **and** WHO_AM_I (register 0x72 → 0xE9) re-verified at 10 Hz **and** configuration registers read back consistently at 1 Hz **and** the noise floor in bounds (`σ_a ∈ [0.5, 20] mg`, `σ_g ∈ [0.02, 2] °/s`; TDK's published 70 µg/√Hz and 3.8 mdps/√Hz predict 1.40 mg / 0.076 °/s at 400 Hz bandwidth; **below the lower bound is the danger sign** — it means the sensor is not sampling at all).
- Three votes. **V1 baro** = the filtered altitude has fallen ≥ 3 m from its running maximum for 200 ms, |v| < 100 m/s (transonic lockout), `BARO_VALID`, and that running maximum corresponds to AGL ≥ 100 m. **V2 acceleration** = the vertical velocity from integrating acceleration alone crosses ≤ 0 **after having exceeded 50 m/s** (a **crossing**, not a level — the level is always true at rest), `IMU_VALID`, and saturation occupied ≤ 5 % of boost. **V3 tilt** = gyro-integrated tilt > 90°, `IMU_VALID`, `FLIGHT_PROVEN`, burnout + 1 s.
- Global gate: `LIFTOFF` ∧ `FLIGHT_PROVEN` ∧ apogee lockout elapsed ∧ burnout + 0.5 s. **Apogee lockout = min(configured value, 0.5 × simulated apogee time), with no fixed 3 s floor** — a low-impulse / under-performing flight reaches apogee in 4–6 s, and a fixed floor would push the drogue into the fast segment after apogee. The real transonic defence is the velocity lockout (conditional, degrading gracefully on off-nominal trajectories), not time.
- Fire: `(V1 + V2 + V3) ≥ 2` (a majority of valid votes), latched until the end of flight. **For any apogee decision earlier than 60 % of the nominal apogee time, V1 must be one of the votes** — the barometer is the only sensor an inertial fault cannot fool, and early deployment is the destructive direction.
- **A velocity lock that overrides everything**: with estimated velocity > 100 m/s, **do not fire the apogee charge**, whatever the votes. This is needed because V3 is **correlated** with this rocket's most likely mission failure: a roll-control instability can take tilt past 90° while the rocket is still fast, and correlated failure of two votes is exactly what a voting architecture must not have.
- Acceleration saturation handling **replaces §7.6's intuition**: `|a| ≥ 32 g` **is positive evidence that thrust is still on; it must keep the gate closed**, not open it. Only saturation lasting longer than 1.5 × the credible burn time for that motor class is judged a fault (only then does it open on "fail permissive"). Saturation invalidates V2 but **does not affect V3** (axial saturation has nothing to do with the gyro).
- Degradation rules: `IMU_VALID = false` (V2 and V3 **live and die together** — same chip, same SPI, same 3V3A) → V1 alone, with a tightened criterion (fall ≥ 5 m for 400 ms, |v| < 60 m/s). `BARO_VALID = false` → V2 ∧ V3; if acceleration saturated, V3 + timer fallback; here **§7.7's "the accelerometer must not be promoted to primary apogee source" must give way** — a blocked vent is the most common real deployment failure in this field, and if the inertial votes can never be promoted that failure has no solution. Also strengthen the dead-baro criterion to "pressure has risen ≥ 150–300 Pa from its running minimum and held for 300 ms" (a transonic dip falls back and drops again; a real apogee does not). Both failed → enable the timer fallback **only if `LAUNCH_CORROBORATED` ∧ `FLIGHT_PROVEN`**, firing at the nominal apogee time within [3 s, 60 s]; if launch has only a single source, the timer fallback is **disabled** and the vehicle is left to the backup altimeter. Log the reason loudly.
- Main: apogee latched ∧ apogee fire + 1.5 s ∧ AGL < h_main ∧ sustained descent. **Backup main**: apogee latched ∧ baro descent rate > 60 m/s for 1 s → deploy the main early (drogue failed). With `BARO_VALID` false, fall back to "apogee fire + t_main_nominal".
- Disagreement: exactly one vote true for > 3 s while the other valid votes are false → set `DISAGREE`, log which one, annunciate after landing, **do not fire on it**.
- Continuous re-zeroing of the pad reference: while `LAUNCHED` is false and the rocket is confirmed still (|a| within 0.98–1.02 g, |ω| < 5 °/s for 5 s), slowly track pad pressure; freeze at launch detection. **Write it to flash at the ARM instant.** Reason: rockets typically sit on the rail for 15–60 minutes, and a 4 hPa weather change is 33 m of apparent altitude, and this number feeds both the main altitude and the post-reset arming criterion.

**F-12 (new)** In every SAFETY pass, solve absolute VDDA from `VREFINT` against `VREFIN_CAL (0x1FF1E860)` (§7.9 already reads it, just not as a fault signal). VDDA outside 3.0–3.6 V → `ANALOG_RAIL_FAULT`: mark every ADC-derived value suspect, sound a dedicated tone, **refuse to arm on the ground, never inhibit firing in flight**. This is the only free detector for V-4 (L2); set the trip threshold from one bench measurement with L2 deliberately disconnected. Also: when `3V3A` collapses, the I2C pull-ups `R12/R13` hang on `3V3` (not 3V3A) and back-feed an unpowered MS5611's pins — "IMU + barometer + GNSS lost at once" must be classified as **one** `RAIL_DEAD` code, not three independent faults. VDDA < 3.10 V: stop starting new flash page programs; < 3.00 V: abort logging for 500 ms and flag it (the declared cost of choosing BOR Level 1).

**F-13 (new)** Fire-result verification and escalation. During the pulse, burst-sample `PYROn_CONT`, `ARM_SENSE` and `VBAT_SENSE` at ~10 kHz (100 Hz gives only one or two samples in 20 ms, not enough). Success signature: the drain collapses toward 0, the bus sags moderately, and CONT reads **open** within ~100 ms after the pulse (bridgewire burnt). Failure signatures and responses: (a) the drain doesn't collapse and the bus doesn't sag → FET not conducting or igniter resistance too high → retry; (b) CONT still closed after 100 ms → bridgewire not burnt → retry; (c) **the bus collapses hard toward the drain** = short signature → **never retry** (a retry pumps 30–50 A repeatedly through the shared fuse and kills the other channel), log, annunciate, and switch to the other channel if configured; (d) `ARM_SENSE` collapses to 0 while `VBAT_SENSE` is normal → fuse/plug/terminal open, both channels void, stop trying. **Limit by outcome, not to a single attempt**: at most 3 pulses per channel, 200 ms apart, stopping as soon as CONT reads open. ("One pulse per channel" is wrong: a pulse cut off by a reset at 5 ms delivers only a quarter of its energy, and the record would then forbid forever the retry that could have saved the vehicle.) Monitor CONT at 100 Hz throughout the flight: a channel going open during boost must **pre-emptively** queue the other channel for the same event.

**F-14 (new)** A **negative** ARM_SENSE check: from power-up until the state machine enters `PAD_ARM_PENDING` (airframe closed, on the rail, operator action expected), `ARM_SENSE < 50 mV` is a precondition for every ground mode. Reading > 0.4 V before that **is a ① hazard, not a state**: latch a continuous tone + solid red LED, refuse every interactive mode, refuse to arm, log. This covers I-4 (stray strand on the terminal), a forgotten plug, and on-board shorts. Likewise, H-1's active gate self-test **may only run** when all of these hold: no valid in-flight record, `ARM_SENSE` read < 50 mV in the same millisecond and re-sampled continuously during the test (abort within one ADC conversion), the pull-pin reading "inserted", and more than 2 s since power-up; the function may run only once per power-up and clears its own entry (function pointer / latch) so that even a wild jump cannot re-enter it. **The cold passive half (all gates low) has no such restriction and runs at every power-up.** Written as a §7 invariant: *apart from a commanded in-flight fire, no code path may drive a pyro gate high while ARM_SENSE is non-zero.*

**F-15 (replaces §7.14)** See §6.

**F-16 (new)** The RCC clocks for `TIM1` and `TIM15` are **never enabled** for the lifetime of the firmware (a peripheral without a clock cannot drive a pin), and after PE3/PE4/PE5/PE6/PE12/PE13/PE14 are configured as GPIO push-pull outputs they are locked with `GPIOE->LCKR` (LCKR freezes MODER/OTYPER/OSPEEDR/PUPDR/AFRL/AFRH until the next reset). **Read back LCKR bit 16 to confirm the lock took**; refuse to arm if not (a wrong LCKR write sequence fails silently).

**F-17 (new; must be written into the frozen document with its reason)** **No VBAT coin cell, no LSE, and this deletion is not to be reopened.** VBAT copper-tied to VDD makes the backup domain disappear together with 3V3, exactly the semantics F-4 needs: the flight record survives a reset but not a real power loss. A coin cell would let a stale "in flight" record live into the next pad session and become an input to the arming criterion. Timekeeping across resets is served by the record's `t_since_launch_ms`, updated at 100 Hz (10 ms resolution, zero timing hardware). The accepted cost: a real power loss in flight loses the phase, and then F-4's condition C and the flash phase log are relied upon — **so both are mandatory, not optional.**

**F-18 (revises §7.6 / new)** SPI1 and IMU recovery (§7.13 gave the backup path's I2C1 a full recovery procedure yet said nothing about **the one bus that can kill the vehicle** — priorities completely inverted): an explicit recovery routine = abort the transfer, disable SPI1, flush the FIFO, clear all error flags, re-initialise, raise then lower CS, re-read WHO_AM_I, reconfigure DRDY; called by the SAFETY task on `IMU_STALL`, bounded in count and logged. **INT1 must be configured in pulse mode, not latched mode** — in latched mode one failed status-register read holds INT1 asserted forever, with no further EXTI edges: a permanent silent stall caused purely by firmware on intact hardware. Also have the SAFETY task poll the IMU's own `INT_STATUS` as a completely interrupt-independent bypass. **Explicitly program `PUPDR[PB4] = 01` (pull-up)**: PB4's NJTRST reset pull-up is gone once it is configured as AF5, and §5.4 also requires disabling the ICM-45686's AP_SDO internal pull-up — without this step an open MISO **floats** instead of reading 0xFF, and the diagnostic "WHO_AM_I == 0xFF" simply does not exist. PUPDR is independent of MODER, a pull-up does not affect SPI at ≤ 24 MHz, and it sits on the **surviving side** of a cracked joint.

**F-19 (revises §7.7 / §7.13)** **No MS5611 I2C transaction may run in DRDY ISR context** (one OSR4096 conversion is 9.04 ms; putting it inside a 1.25 ms ISR is immediately fatal, and a hung bus goes straight to the end of the kill chain). Instead use a non-blocking state machine in the SAFETY task with pipelined conversions (start on tick N, read on tick N+1), lowering the effective pressure rate to 50 Hz if needed to buy 50 % bus headroom (50 Hz is ample for apogee detection). A sample not updated for more than 50 ms is marked degraded, and **nothing ever blocks**. I2C1 recovery (9 clocks + STOP) must be driven by a **timer**, not by the stuck transaction, running in a low-priority context with interrupts enabled; after ≤ 2 attempts declare `BARO_INVALID`. If the spare header is ever populated, an external device must not be able to drag a transaction past the timeout — otherwise use §3.6's own fallback and move to I2C3 (PA8/PC9), permanently giving up SDMMC1_D1 (microSD is deleted and logging is class ⑤, so the trade is worth it).

**F-20 (new)** Storage integrity self-test (run on the bench, not on the pad): JEDEC ID = `EF 40 18`; in **SR1** (05h) BP2:0 / TB / SEC / SRP all 0; in **SR2** (35h) **CMP** and SRL 0; in **SR3** (15h) **WPS** 0. — CMP is in SR2, not SR1, so checking only SR1 reads a reserved bit; and with `WPS = 1` the part switches to individual block locks, **all block lock bits are 1 after power-up and the whole chip is read-only**, while SR1 reads perfectly clean and every page program silently "succeeds" without storing anything. Also: erase-write-read-compare on a dedicated scrub sector; 32 pseudo-random pages of the flight area must all be 0xFF; the erase routine writes an "erase complete" magic and a generation counter **last**. Full-chip erase only on the bench (a W25Q128 chip erase can take 200 s; tying up the pad with it is worse than flying without a log); on the pad, flash faults are always **downgraded to warnings**. After a reset, locate the write pointer by binary search at boot and **never erase**. Log records are packed into full 256-byte pages by a low-priority consumer before programming (programming each 64 B record gives 254 programs/s, 76 % flash duty at the 3 ms worst-case program time; packed, 19 %), and the CRC is also computed on the consumer side. Apart from one single audited "clear protection" routine, nothing anywhere may issue a write-status-register command.

**F-21 (new)** Keep the SOIC-8 clip readback path alive (the only way to get data off a destroyed board): never set the BP/CMP/SRP/WPS/OTP lock bits; with the board unpowered the part must still answer single-line `0x9F` and `0x03` (1-4-4 reads on the H7 side are fine, but confirm by measurement after every QSPI driver change); keep the package on the top side, not shadowed by tall parts, uncoated, with a pin-1 mark on the silkscreen. The log format is public and re-synchronisable (magic, version, fixed-length records, per-record CRC, monotonic sequence number).

**F-22 (new)** Freshness is a property of **every** sensing path, not a special case for the IMU. Every path carries a monotonic sample count and a timestamp, and the SAFETY task checks that they advance at the right rate. The ADC matters most: if its DMA stalls, `PC0/PC1/PC4/PC5` all freeze at their last readings, so every arming precondition passes forever, the continuity trace in the log is a perfect straight line, and F-13's fire verification always "succeeds". Use drifting internal channels (VREFINT, die temperature) as liveness signals: N consecutive byte-identical conversions across the whole sequence is the stalled-DMA signature. Freshness and dropped-frame counters must be logged (even when 0), or a dead consumer cannot be told from a healthy one. Also: `PC0/PC1` are `ADC123_INP10/11`, so ADC1 and ADC3 can read them together and compare, with a persistent difference = ADC fault rather than a continuity change — free, but state honestly that it is **redundant only against peripheral/calibration/configuration faults and useless against V-4** (both instances share VREF+/VDDA).

**F-23 (new)** At every boot write `RCC_RSR`, the reset counter, the recovered record and the reason for every arming decision as a separate record type. **Any reset between launch detection and landing grounds that vehicle until the cause is found**, and the cause must be written down before the next flight. Log whether the three votes agreed on every flight, so a slowly worsening vent or a drifting gyro shows up as a trend rather than on the flight that loses the rocket.

---

## 6. Ground procedures and annunciation

### 6.1 What the buzzer can do (get the physics straight first)

MLT-8530 rated 80 dB @ 10 cm (**the LCSC product page lists no SPL; this value comes from the frozen document and was not checked against the maker's datasheet**). Free field: 1 m → 60 dB, 3 m → 50.5 dB, 10 m → 40 dB, **30.5 m → 30.3 dB**. Site background 45–55 dBA. **Even assuming zero transmission loss through the airframe, the signal is 15–25 dB below background at any legal safe distance.** The conclusion does not depend on the airframe-loss estimate:

- **Reliable decoding radius ≈ 1 m (calm), 0.3–0.5 m with wind.**
- **After walking away there is no information channel at all.** Everything a person must know has to be heard **as the last step before clearing the pad, within 1 m of the rocket**. Everything that changes after walking away (battery sag, an igniter lead coming loose, a blown fuse, an MCU reset) must be handled autonomously by firmware and logged, **never "beep and hope"**.
- A free remedy: aim one av-bay vent at the buzzer as a sound port (counted in the vent-area budget, away from the MS5611). New failure: one more light path and water path, and the vent area must be recomputed.

Three more hard constraints:
1. The MLT-8530 is a 2.7 kHz resonant electromagnetic buzzer; **off resonance it doesn't change pitch, it loses 15–20 dB**. So §7.14's "high/low tone" coding cannot be implemented on this transducer — **the language can only use durations and counts, at a constant frequency**. Sweep on the bench to find the real resonant peak (already required by §7.14).
2. The buzzer is a 95 mA / 0.31 W load on 3V3, and the LC corner is 12.8 kHz, so **2.7 kHz lands below the corner, essentially unattenuated (about +0.4 dB), on 3V3A = VDDA = VREF+**; it is also a 2.7 kHz mechanical pressure source bolted to the same board, right next to the 800 Hz-sampled IMU and the gel-sealed MS5611. **Rule: the buzzer must be silent during any measurement that feeds a pass/fail criterion** (including H-1's millivolt-level pyro readings, the battery load step, IMU noise floor, and the baro σ / dP/dT measurements — the latter coupling is **acoustic** and strongest in a **sealed bay**, reading "sealed" as "vented", anti-correlated with the truth). For measurement windows longer than 2 s, use the yellow LED as heartbeat and announce the start and end of the silent window with a distinct pattern.
3. Recompute the hold-up budget with the real load: 470 µF's 12 mJ is 18.2 ms at 0.65 W, **only ≈ 12.5 ms with the buzzer's 0.31 W added**, and the pad / ascent is exactly when it is sounding. **The buzzer is silent from launch detection until landing** (nobody can hear it, it wastes a third of the brown-out budget, and it pollutes measurements).

### 6.2 Tone codes

Elements: `·` = 60 ms, `—` = 300 ms, 120 ms between elements, 500 ms between groups. All at the measured resonant frequency.

| State | Pattern | Period |
|---|---|---|
| Proof of life (< 50 ms after reset, **unconditional, before any test**) | `— ·` (this combination appears in no periodic pattern, so a reset loop cannot masquerade as healthy) | Once |
| Self-test in progress | `·` every 150 ms (fast trill) | Continuous |
| SAFE / disarmed / all passed | `—` `[ch1]` `[ch2]`, `·` = igniter present, `—` = open | 2 s |
| Warnings present but armable | SAFE tone, with `— —` + N × `·` inserted every third frame | 2 s |
| REFUSE (not armable) | `— —` + N × `·`, forever. **Never sounds the READY tone** | 2 s |
| Armed but not ready | Same, frame compressed to 1 s (sounds more urgent) | 1 s |
| **ARMED-READY (go)** | `· · ·` — no other three-short pattern exists in the language | 1 s |
| **PYRO HAZARD** | **A continuous unbroken tone** — the only continuous tone in the language, with one meaning: **do not approach, do not insert the ARM plug, pull the ARM plug now** | — |
| In flight | Silent | — |
| Landed locator | `—` every 5 s | 5 s |

**Fault codes (N × `·`)**: 1 battery / 2 supply rail or VREF (including `ANALOG_RAIL_FAULT`) / 3 IMU absent or self-test failed / 4 IMU noise floor abnormal (suspect joint or mounting) / 5 barometer absent or PROM CRC / 6 implausible barometer readings / 7 suspected av-bay seal (vent) / 8 storage / 9 pyro ch1 / 10 pyro ch2 / 11 inconsistent ARM / pull-pin / USB state / 12 servos / 13 GNSS no fix (warning only) / 14 unexplained reset on the last flight.

**LED language (the only channel when someone is wearing ear defenders, or working with the bay open in a noisy prep area)**: red = hazard/refuse states (solid for hazard, fault-code flashes for refuse); yellow = heartbeat, one flash per frame. **Numeric codes are given as red LED flash counts, not beep counts** — counting fourteen 60 ms beeps against a 76 dBA background plus wind is impossible, while an LED is fully readable at the 1 m the READY confirmation requires anyway. The fault-code table is printed on the silkscreen and on a laminated card that travels with the rocket box.

**Three hard rules in the driver layer**: silence is never a healthy state (every state must sound within ≤ 2 s); the continuous tone has exactly one meaning; **one single low-level driver** enforces a ≤ 25 % duty-cycle ceiling outside the hazard state (not for hold-up, but because an always-on buzzer **masks every other code** and, per §6.1 item 2, pollutes every measurement).

### 6.3 Procedures

**Bench (powered, ARM link out, pull-pin inserted)**
- **T-1 load-switch integrity**: battery connected, external switch **OFF**, USB plugged in. `VBAT_SENSE (PC4)` must read **< 0.2 V** (RAW then floats only through R3/R4's 147k, with D2 blocking in reverse). Higher = Q1/Q2 drain-source short, a stuck switch, or the SW wire chafed to ground → no fly. **This is the only test that can find I-6, and it can only be done with the switch OFF and USB power; a pad self-test can never do it.** (It also voids §7.10's "reads ≈ 1.487 V on USB power alone": that number assumes RAW sits at VLOGIC, which D2's direction forbids; the real value is set by SS34 reverse leakage and is **undetermined**, anywhere from millivolts to a volt depending on the part and temperature, so it cannot be a criterion. USB presence is judged **only by PD15**.)
- **T-2 battery load step** (the only test that finds "8.4 V open-circuit but high internal resistance"): step all four servos ±5° together, sample `VBAT_SENSE` at 1 kHz, and compare with that vehicle's golden baseline from build. Ratio > 1.4 = high internal resistance / loose terminal / cold battery → no fly; < 0.6 = a linkage has come off → warning. Limit the amplitude to ±5° about centre and abort immediately if `VBAT < 6.6 V`.
- **T-3 pyro cold self-test** (H-1): ARM out, both gates low, read jointly per the table in §4.1. Any 0 mV or > 100 mV → continuous tone, **do not touch the ARM plug**. Then a 10 ms gate pulse per channel in turn; CONT must collapse to ≈ 0 and recover.
- **T-4 per-wire terminal check** (the only defence against V-16): ARM out, both igniters connected, measure each BUS ↔ OUT on a DMM low-current range; it must read the igniter resistance, **≥ 1.0 Ω** (a rev G hard requirement); near zero = no fly. Record the values on the flight card.
- **T-5 human-in-the-loop sensor checks**: a tap test (for 20 s, chirp once for every > 2 g transient; the operator taps three times and counts three chirps — in one step this proves the IMU is alive, DRDY is firing, the ISR is running, the buzzer works, and **the sensor is mechanically coupled to the airframe**, which no purely electrical test can show); a vent test (for 20 s, chirp once for every |ΔP| > 0.5 hPa; the operator covers and uncovers the vent — **the only reliable vent criterion on a calm day**).
- **T-6 full-travel servo sweep**, visually confirming all four fins move and return to centre; one chirp per commanded position so the observer knows which one is being tested.
- Also on the bench: full-chip erase (**only here**), F-20's storage self-test, GNSS lock confirmation (**warning only, never a go criterion**), remove the DFU jumper from J2 and wrap it in clear heat shrink, unplug the USB cable.

**Assembly**
- Terminate all 4 battery/switch wires and all 6 ARM/PYRO wires **outside the airframe** and torque to 0.4 N·m (rev G §7.3-3: they cannot be tightened inside), using only tinned solid wire or ferrules; pull-test each wire; mark each screw with torque paint.
- Make the charge and igniter a sealed assembly; weigh and record the charge; put a paint mark on the igniter lead where it enters the charge well so movement is visible; photograph every charge well; a second person signs. **No electrical measurement can tell whether an igniter is actually in its charge well.**
- Harness per IREC DTEG Appendix B: strain-relief slack at every termination; the 3×4 servo header must be positively retained by a zip tie through the 3 mm hole (the header itself has no latch); no twisted splices or wire nuts; no tape/glue/RTV as insulation or bundling; only clear heat shrink so terminations stay visible; **stake every part > 7 g** (on this board: the two 10 mm 470 µF cans, the two 14 mm screw terminals and the buzzer; L1/L2 are also recommended, with a visual and resistance check); the battery must be rigidly held in a fixture, never by hook-and-loop or zip ties alone.
- Insert the pull-pin and confirm the board reads "inserted" (which also proves the pull-pin wire is intact). Close the airframe. **Confirm the 3–4 vents are open and untaped.**

**On the pad**
1. Rocket on the rail, vertical.
2. **Power this board first (ARM link still out)**: hear the proof-of-life tone → self-test trill → SAFE tone, and decode the two continuity symbols. **This ordering is the general means of downgrading the whole class of "only shows up at power-up" ① events — I-1 / I-5 / I-6 / V-14 — into bench / early-pad findings. Silence = no fly.**
3. Arm the **backup altimeter** and confirm its own continuity tones.
4. **Insert this board's ARM link last** (it is the electrical safety device). Within 2 s the tone must change from SAFE to ARMED; also check the ratio `ARM_SENSE / (VBAT_SENSE × 147/47) = 1/11 ± 15 %` (computed with the VREFINT-calibrated VDDA; **never an absolute millivolt window**: `PC0 = PYRO_BUS / 11`, a 6.4 V battery gives 0.582 V, and an absolute window would flag a battery state §7 explicitly allows as a fault).
5. Pull the pull-pin and hear the state change.
6. At ≤ 1 m confirm the `· · ·` READY tone and clear the pad. **Know clearly that this is the last piece of information you will get.**
7. Before launch, any unexpected boot tone → abort, return to the rocket, pull the ARM link first.

**Recovery**
8. Approach from the side, **never standing in line with any charge well or directly in front of the nose**.
9. **Pull this board's ARM link first** and confirm the armed tone stops; then switch off the backup altimeter; finally switch off main power and touch the airframe.
10. After landing, read the log before powering the board for any other purpose. **Any reset between launch detection and landing grounds that vehicle.**

---

## 7. Real-world failure frequency vs where we spend

### 7.1 What the rules require (primary text)

- **NAR High Power Rocket Safety Code** (the PDF nar.org serves today, self-labelled "Revision of August 2012") only requires "I will use a recovery system such as a parachute…", plus two lines that bind this design: "**The function of onboard energetics and firing circuits will be inhibited except when my rocket is in the launching position**" and "When arming onboard energetics and firing circuits I will ensure that no person is at the pad except safety personnel and those required for arming and disarming operations."
- **Tripoli Unified Safety Code v2 (effective January 2026)**: 11-1 landing speed ≤ 35 ft/s; **11-6** total impulse > 2560 N·s requires an "electronically controlled recovery system which does not rely upon the motor"; **13-8** electronic recovery devices stay inhibited until the rocket is erected in position and before the igniter is installed; 13-10 disarm before lowering. **"redundan" appears zero times in the whole text.**
- **Redundancy is mandated in only two places, both defined the same way**: Tripoli L3 certification requires "Dual redundant electronics… two completely independent and separate electronic recovery systems… redundancy means completely separate systems, including batteries, switches, avionics, and energetics"; IREC / Spaceport America Cup DTEG 2026 §6.9.1 has the same list, §6.9.2 says "A dual pole switch does not satisfy the requirement for redundant arming switches", §6.10.1 requires at least one of the two to be COTS, and §6.11.3 says "A COTS microcontroller running SRAD flight software shall be considered an SRAD system" — **this board can never serve as the COTS half**.

**Compliance conclusion**: this design is **compliant** for ordinary L1/L2 club flights, because the removable fused ARM link is a real physical break on `PYRO_BUS`, satisfying "inhibited except in the launching position" — **provided the ground procedure really does insert it last and pull it before lowering**, and V-18 shows that premise does not hold with the current mechanical design. It **does not meet** the L3 / IREC definition of redundancy, and the two on-board pyro channels are far from that definition.

(One difference rather than a violation: IREC DTEG §6.17.1.1 forbids LiPo inside the rocket; NAR and Tripoli do not. This rocket's 2S LiPo is legal at club launches but, as is, cannot fly at IREC.)

### 7.2 What shipping products actually do (primary documents)

- **AltOS 1.9.22 source** (Debian orig tarball, grep of the whole tree): **no watchdog on any flight-computer product** — `ao_watchdog.c` is only built for `src/fox1ihu` (a CubeSat IHU), and it kicks an external chip via GPIO rather than using an IWDG. TeleMetrum / TeleMega / EasyMini ship **deliberately** without a watchdog. There is also no cross-reset persistence of flight state: `ao_flight()` always starts from `ao_flight_startup` and re-decides pad/idle/invalid. **An in-air reset also loses the flight on AltOS — but it never resets itself, and never permanently disarms.**
- **Featherweight Blue Raven user manual (2026-05-12 edition)**: "Manual arm… When false (**default for deployments**), the channel is **enabled at power up**." Deployment channels are armed at power-up; safety comes from elsewhere — a vehicle-level event "**Liftoff Detected — Always required before any deployment**", plus the hardware interlock described on the product page, "disables all outputs when the microcontroller voltage is below 2.7V, including start-up, shutdown, and brown-out situations". Apogee uses a **2-of-3 vote**: "fires when 2 of 3 independent sensor methods detect apogee… barometric pressure increasing, gyro-based flight tilt exceeding 90 degrees, and accel-only velocity estimate of less than 0 feet/second", with a transonic lockout (`Vel1 < 400 ft/s`), an apogee latch, an "Apo channel fired + 1.5 s" gate, and a descent-rate backup main (`Bvel1 < −200 ft/s`, "Early main deployment if apogee charge fails and rocket is falling too fast"). The manual also addresses the sealed-bay case explicitly: "The default deployment settings of the Blue Raven will work based on gyro and accelerometer measurements for apogee deployments **even if the av-bay is sealed**" — a shipping product with a large flight history **designed inertial votes specifically for blocked vents**, which is why §7.7's absolute prohibition must become conditional.
- **PerfectFlite StratoLoggerCF**: designed **not to reset** — "can tolerate a power loss of several seconds (depending on battery voltage) without resetting", with dedicated power-up error codes 1 "Total power loss during last flight" and 2 "Momentary power loss during last flight… brownout protection allowed the altimeter to continue normal operation, but a loose connection or other issue is likely". *(This quote comes from a fetch in another domain; perfectflite.com's TLS certificate has expired and it could not be re-checked this round — **treat as unverified**.)*
- **Eggtimer Quantum (user guide 1.09G)**: "The Quantum is designed so that it will not self-arm itself" (a person must enter a check code); its recommended L3 wiring uses a **separate** deployment battery because "having the separate deployment battery 100% prevents any kind of deployment glitch from affecting the flight computer side"; the rationale for its FailSafe feature reads: "Almost everyone who's had enough electronic-deployment flights has had a flight end badly because of a drogue deployment failure. Some common failures are: motor eject charge fires late, or doesn't fire at all; drogue gets stuck in the body tube; shorted or bad ematch doesn't fire."
- **AltusMetrum manual**: "Apogee lockout is the number of seconds after launch where the flight computer will not fire the apogee charge, even if the rocket appears to be at apogee. This is often called Mach Delay…" — **the timer is an inhibit, not a trigger**; the same page explains transonic handling is done with a Kalman filter rather than an accelerometer AND gate, and recommends leaving this default at zero.

**The fleet's answer is consistent, and it is the opposite of frozen §7's**: nobody resets because a sensor stalls; either there is no watchdog at all or the design rides through disturbances; nobody permanently disarms in flight; everyone gates firing on a latched lift-off detection. **The §7.1 + §7.4 combination (only feed point = the IMU ISR, and no re-arm after reset) is worse than every shipping product I could find: it turns a survivable sensor hiccup into a guaranteed ballistic rocket.**

### 7.3 What actually destroys amateur rockets, and whether our spending is in the right place

There are no rigorous public statistics (this must be stated honestly). Three kinds of indirect evidence are available, and all point the same way: which faults vendors designed dedicated error codes and features for (of the StratoLoggerCF's six power-up error codes, **two** are for power interruption and **zero** for sensor algorithms); where vendors spend the words in their manuals (switch bounce, terminal wire retention and connector seating far outweigh decision logic); and IREC DTEG Appendix B — **almost entirely mechanical clauses**: strain relief at every termination, positive locking of every mated pair, no twisted splices or wire nuts, no tape/glue/RTV, a pull test on every termination, "All components greater than 7g shall be staked", "'Velcro' and/or tie wraps shall not be used as the sole method of mounting batteries".

**So this rocket's redundancy budget, in order:**

1. **A permanently fitted independent commercial altimeter** (own battery / switch / igniter / charge) + **a permanently fitted independent GPS tracker**. The only thing that covers V-4, V-10 and firmware defects; zero changes to this board; the cost is a vehicle-level geometry decision (§3.2).
2. **All the firmware rules in §2 and §5. Zero parts, the widest coverage.**
3. **Harness, staking, terminal discipline, vent workmanship, ground ejection tests, per-wire DMM checks. Zero parts, covering the class that statistically happens most.**
4. **The 6 parts in §4.1.** They buy three things firmware cannot: a cold pyro self-test, a gate a solder bridge cannot fire, and a readable USB state.
5. Everything else.

**Plainly: a correctly written arming procedure and correctly made strain relief beat any clever electronic redundancy.** The two heaviest musts in this document (a permanent backup altimeter, and taking the watchdog off the IMU) are one procedure and one firmware change; all 6 new parts together are worth less than the single ordering rule "connect the ARM link only after the power-up self-test passes". Conversely, a checklist too long for anyone to follow is worse than a short one — **the pad section (steps 4–6) must fit in five lines, laminated, travelling with the rocket, read back by a second person.**

---

## 8. Net impact and remaining risk

### 8.1 Additions

| Item | Delta |
|---|---|
| Soldered parts | **+6** (47k × 2, BAT54A × 1, 10k × 2, 100k × 1) → 101 → **107 (+5.9 %)**; +11 if H-8/H-9/H-10 are adopted |
| Part numbers | **+1** (BAT54A) → 39 → **40 (+2.6 %)**; the BAT54 family also serves H-10 |
| Area | About 15 mm², all 0402/0603/SOT-23, in the y 34–46 zone, **never in rev G §4's Z2** |
| GPIO | Net +3 (5 sentinels, 2 signals moved) |
| Timers | +1 basic timer (TIM6/TIM7) for the SAFETY task; TIM2 still reserved per §7.3 as the free-running microsecond timebase |
| Netlist changes | J-ARM pin-definition ruling (V-17); optional PYRO_BUS split (H-5); `J1.4` from SW to GND (giving the 12 A return two screw positions, while the 76 µA switch needs only one); `R2` 10k → 1k |
| Firmware | A rework of about 2000–3000 lines + a full set of injection tests (on a shaker, in a pressure pot, injecting resets in every flight phase and verifying the record reads back with a valid CRC and a monotonic sequence). **The largest cost of all, far larger than the parts** |
| Vehicle | Backup altimeter + tracker + their batteries/switches/charge wells → **a longer coupler or a separate bay section** (rev G's +1.558 mm margin cannot absorb it) |

### 8.2 What remains single-string after every change

The battery; the reed/magnetic switch (with no state readback in the netlist); the Q1/Q2 load-switch pair; the RAW bus; the ARM plug and its contacts; AP63203 + L1 + 3V3; **L2 and 3V3A (IMU + barometer + GNSS + VREF+ together)**; the MCU; the firmware image; the single MS5611; the HSE crystal (CSS only downgrades it from "silent death" to "degraded flight"); the av-bay and its set of vents (shared by the primary and backup altimeters, so electronic redundancy is useless against it); shear pins, shock cord, parachutes; and **the person doing the wiring**.

**Without H-5, add: the single 5 A fuse and the single PYRO_BUS.**

In one sentence: **this board is, and will remain, a single-string system on the deployment path. Its only real redundancy is off the board.** What every on-board change in this document does is: turn undetectable failures into detectable ones, downgrade ① to ⑤, and change "one fault means total loss" into "three independent faults are needed". None of them creates a second independent path.

### 8.3 Honest residual risk

1. **A shorted H-1 pull-up resistor is still a ① path**, just blocked by the BAT54A. Diode short + resistor short is a double fault of negligible probability, but it must be on record, and F-14's "> 100 … *(the original text ends here, truncated)*
