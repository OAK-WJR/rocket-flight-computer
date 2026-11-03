# Round11 servo-cell fix validation

The generator-only servo correction passes its native geometry and real KiCad DRC checks. This is fix validation, not a qualifying independent review round or a complete-board release pass. AGENTS section 2, the circuit, MCU pins, J122, supports, IMU pose, clearance floors and allowlists are unchanged.

The frozen canonical PCB was not saved. Its SHA-256 at the probe was `419a8f49f39ea748a1622ecb5858ba060d1eb2fac7df7e3cca37a72dc6d8fd15`. The isolated final prototype is `175b8544fee35ef43ed6d5d27e999726ec43976de3eabbbd141e2fae8f599c2e`. Exact routes, source-slice fingerprint and structured checks are in [round11_servo_fix.json](round11_servo_fix.json).

All coordinates below are millimetres; all listed parts are on B.Cu.

| Part | x | y | Rotation |
|---|---:|---:|---:|
| D121 | 31.5 | 71.5 | 180 degrees |
| R150 | 34.6 | 75.9 | 0 degrees |
| R151 | 34.7 | 72.77 | 0 degrees |
| R152 | 34.7 | 70.23 | 0 degrees |
| R153 | 34.6 | 68.0 | 0 degrees |
| R154 / R155 | 32.45 / 30.55 | 74.53 | 270 degrees |
| R156 / R157 | 30.55 / 32.45 | 68.4 | 90 degrees |

R152 clears D121's actual cached courtyard. R150's MCU entry aligns with the existing transition at (33,75.9). The clamp/pull entry follows `(32.45,74.1) -> (33.5,74.1) -> (34,74.6) -> (34,75.6)`, ending within R150.1. This clears the SERVO2 transition and the R154 return without a crossing or tiny jog. The R154.2 return is a straight 0.3 mm track to the existing-count 0.5/0.3 mm GND via moved to (33.4,74.96). No via is added.

SERVO1/2 outputs turn beside their resistors at (36,75.9) and (36.37,72.77), then enter J122.1/.2 at their centres. The resistor-side horizontal runs are 0.575/0.845 mm. R153 aligns with J122.4 for one straight output. There are no whole-in-pad output tails. The servo functions generate 45 segments and 6 vias; the four pull-down fan-outs add 4 segments and 4 vias: 49 segments / 10 vias total for the servo cell, unchanged via count.

Native courtyard caches were rebuilt before measurement. The 1.5 mm M-6 floor passes: R150/R151/R152/R153 minima are 1.581/1.536/1.536/1.575 mm. The nearest actual courtyard polygon gap is 0.020 mm, at D121 to R151/R152. P-11 retains 5.003 mm CAD wire room at J122 against the unchanged 4.95 mm accepted floor; physical access remains unqualified.

The shared return's nearest foreign-copper ring/hole gaps are 0.238/0.338 mm on B.Cu and 0.522/0.622 mm on F.Cu. A native scan of 86,015 foreign pairs finds no servo copper violation at 0.15 mm or hole violation at 0.25 mm. The inherited tightest PWM escape copper gap is 0.154 mm. These are CAD shape measurements, reported to 0.001 mm.

| PWM transition | Nearest GND via | Centre distance |
|---|---|---:|
| SERVO1 (33,75.9) | (33.4,74.96) | 1.021567 mm |
| SERVO2 (34.325,73.8) | (33.4,74.96) | 1.483653 mm |
| SERVO3 (33.675,69.05) | (32.968,67.452) | 1.747413 mm |
| SERVO4 (34,66.5) | (32.968,67.452) | 1.404040 mm |

SERVO3's existing distance is retained. PWM nets are outside the project's 1.5 mm critical-signal partner list. The shared return improves SERVO2 from its earlier 1.699460 mm distance while preserving SERVO1's nearby return. These distances do not establish electrical return performance.

**Software / CAD evidence:** native pcbnew 10.0.6 generated/filled the temporary board; official KiCad 10.0.7 ran DRC. All final servo tracks exactly match the generator dry output. DRC reports 0 servo violations, 0 courtyard overlaps and 0 unconnected items. This focused command did not request schematic parity; the integrated gate must verify it. Eight of nine focused whole-board API rules pass. K-copper's four messages concern only two port via/paste groups in the concurrent port-fix snapshot. The snapshot still has 15 port-area DRC violations and one CAM_5V routing bump; the parallel port receipt and subsequent integrated build must close them.

Servo routing hygiene has 0 blockers, 0 missing leftover records, no micro/short segment, tiny jog, crossing, overlap, acute/off-angle, whole-in-pad segment or required-partner failure. Its remaining review inventory is three within-land series-resistor entry endpoints and the four inherited F.Cu MCU escapes counted as extra bends. No allowlist or floor is changed.

**Pending:** the integrated full build/check.sh, fabrication/binding, reproducibility and independent review. No firmware, electrical, thermal, e-match, harness, screwdriver, bore, stack or other physical qualification is claimed. R10 remains unaccepted.
