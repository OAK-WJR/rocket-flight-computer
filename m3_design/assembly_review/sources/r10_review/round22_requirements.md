# Round 22 - requirements and physics roots (Claude)

Target commit ec8cb98; board SHA-256 5516eeec... unchanged before and after.

**Totals: 0 Critical / 0 Major / 4 Minor (all new).** Every REQUIREMENTS row and the owner decisions trace to the board: connector poses and pin nets, gate networks, supports, outline, and the R81 / C87 move. DRC (all severities, with parity) is 0. route_check r10 is 0 failing. The round 21 sheet notes are correct. M2's "design rules within JLC's limits" is met by the board on every JLC row checked, but the gate holds only part of JLC's table.

## Findings

- **R22-REQUIREMENTS-01 (Minor): row 30's premise.** Without the AUD-2 exemption, exactly 4 arming-chain vias fail the partner-via rule, with row 30's distances (1.866 / 1.875 / 2.902 / 7.467 mm). The project's own spot search (`r7_hygiene.gnd_spots`, the test M2 uses for missing-GND-via entries) finds a legal GND via 0.671 mm from three of them: (10.2,68.9), (20.7,69.2) and (20.275,66.3). It finds none for (17.1,82.8). The exemption is physically sound: these nodes sit behind 470 kOhm, with 227 kOhm x 220 nF = 50 ms and about 7 uA. But that is the reason, not lack of room. Fix: text only, in row 30 and D-R21-04.
- **R22-REQUIREMENTS-02 (Minor): JLC table partly gated.** K-rules pins four hole rows. A seeded PTH ring of 0.10 mm (JLC minimum 0.15) and a 0.40 mm NPTH (JLC minimum 0.50) pass DRC, and check_r10 has no test for either. The board itself meets both: rings 0.30 / 0.20 mm, NPTH holes 0.60 / 0.991 mm. Other figures on the board:
  - PTH hole to foreign copper ≥ 0.551 mm on all four layers;
  - via hole to via hole ≥ 0.259 mm;
  - mask web ≥ 0.150 mm;
  - J3's NPTH to its GND land 0.200 mm, at JLC's 0.2 mm (the maker's land).

  Fix: checks only.
- **R22-REQUIREMENTS-03 (Minor): J400 ESD not covered.** The operator turns the J400 switch by hand on the rail, and J400 has no clamp. No requirement or bench item covers ESD there. A worst-case full transfer (150 pF at 8 kV into C87) gives about 7.5 V on EN, against EN's 6.5 V absolute maximum. This is an Inference: a floating vehicle's small capacitance to earth limits the real charge. The failure is fail-safe for firing (U9 off or damaged). Fix: text, a handling step and a first-article discharge check.
- **R22-REQUIREMENTS-04 (Minor): stale lines.** The OQ-6 accepted-risk bullet omits C88, which the D-R21-03 note and the board put on BAT_IN; a cracked C88 is an unfused pack short. ORDERING's U4 row cites the stock check at 10:13Z, but the file is from 23:23Z.

## Fix verification

| Change | Verdict | Measured |
|---|---|---|
| D-R21-01 | Confirmed (gate coverage partial) | Every PTH hole ≥ 0.551 mm from foreign copper on F / In1 / In2 / B; DRC 0; JLC figures match |
| D-R21-02 | Confirmed (presence) | 0.4 mm B.Cu 3V3 run from U2.1 to (23.0,70.0) |
| D-R21-03 | Confirmed | Three notes correct; R21-REQ-01 / -02 closed |
| D-R21-04 | Confirmed (wording partly) | Classes as claimed; 0 failing; no jog; one counted short layer hop; see -01 |
| D-R21-05 | Confirmed | Poses as claimed; EN at most 2.03 V |
| D-R21-06..09 | Not checked here | Other lenses |
| R21-REQ-03 / -05 / -06 | Confirmed | J440 named; envelope flagged as an owner / simulator item; R7–R9 text moved |

## Fix now

- -01: row 30 / D-R21-04 wording (text).
- -02: K-rules PTH ring ≥ 0.15 mm and NPTH ≥ 0.50 mm (checks).
- -03: J400 ESD in F8 / F9 and ORDERING 8.3 (text).
- -04: C88 in the OQ-6 bullet; ORDERING timestamp (text).

## Closed candidates

- The AUD-2 exemption against M2 / AGENTS §2: the exemption is permitted through the named list and owner row 30.
- 0.55 mm inner clearance as an oversized margin: it narrows strips but splits nothing.
- The 0.5 / 0.3 mm via ring: JLC's via rule is hole + 0.1 mm.
- U11's 0.2 mm pads: TI's land.
- Redundant AUD-2 entries: harmless.
- The TP 1.0 mm rule: rooted in the bare probe pads.
- OQ-7's position constraint: live.

Open owner items (cost, east tabs, row 18, P3 factor, hold-up, U4 / U9 stock) are noted, not filed.

## Coverage limits

CAD and document review only. The ESD figure is an Inference. The three GND-via spots were not seeded and refilled. check.sh and check_r10 were not run on the canonical tree. Probe outputs are in `.supervisor/r22_requirements/`.
