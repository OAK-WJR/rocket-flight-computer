# R9 step 10 (requalification and records): handoff

Status: **complete; the step's verification passes.** Every qualification the clean sheet invalidated is re-measured on
the final board and bound to its SHA-256, and the records are R9's: `docs/M3_R9.md`, `docs/R9_VALIDATION.md` (with the R9
deviation list for the owner), `docs/ORDERING.md`, the R9 clauses and "R9 acceptance" in `docs/REQUIREMENTS.md`,
STATUS.md, AGENTS.md, README.md and MARGIN_PRESCRIPTION P1-9's R9 status. Step 10 changed no copper: the board is still
`m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51`
(step 9's), and `tools/check.sh` exits 0 on it. Nothing committed or pushed. Decisions: `R9_DECISIONS.md` D-S10-01 …
D-S10-19. Log: `r9_step10_progress.md` (sessions 1–3). Evidence: `step10_evidence/`.

**Environment.** Sessions 1 and 2 ran without a GUI session (the D-S6-14 shim and the D-S9-06 wrapper); the Mac then
restarted, which wiped the scratch folder with the session-2 DC solves. Session 3 found the user logged into the GUI,
so kicad-cli, `tools/check.sh` and the tests ran as they are, with no shim or wrapper (D-S10-15), and it re-ran all 32
DC rows.

## 1. Produced

| File | What |
|---|---|
| `docs/M3_R9.md` | The R9 design record: what changed from R8, placement, the CH1 column, the RF strip, power (with the fire loop, the GND returns and the 26 supply paths), routing, ground, silkscreen (110 hidden designators listed), the requalification headlines, mechanical, hot-plug, the IMU axis map, firmware, checks, the fab outputs |
| `docs/R9_VALIDATION.md` | Build and validation: the step table, the hard gates, the done rows (34 met, 16 missed, each with its record), the requalification tables (pyro, RF, DC / IPC-2152 / reference, mechanical / hot-plug / IMU / firmware / fab), each row citing its evidence; the R9 deviation list for the owner (A none, B none, C1–C18, D the agent decisions, E 114 information instances, F the M2 sweep); open items |
| `docs/ORDERING.md` | R9's (sessions 1–2): stack-up, via covering with TP120's two open vias, four panel tabs, assembly counts, hole fill, coating and leakage figures, the stall test with the FETs judged, the IMU sign check, the keyed-radio immunity gate, the sled and its pours; "until R9 is accepted, order R8" |
| `docs/REQUIREMENTS.md` | R9 clauses (D-S10-08): F4 (the R9 solve, the GND return, the stall-test basis), F7 (the fire loop on the final copper), F8 (D85 at 2.5 mm, D18 2.65 mm, P-1b, LC-1, fill margins, P-3, P-7, the strict pad rules, pads named by role), F10 (the strip y 0–22.0, check_r9's R-rules, gaps, fence, the 46.13 mm radio distance), P1, P2, M2 (A8 gone, TP120's exception, the R9 list not accepted), M3 (the R9 cost run), the retired gate-spacing risk, a new "R9 acceptance" section |
| `STATUS.md`, `AGENTS.md`, `README.md` | R9 the current, unreviewed candidate; R8 the owner-accepted, orderable fallback (D-S10-10); R8's section now names its commit `9c8179b` |
| `docs/MARGIN_PRESCRIPTION.md` | P1-9: an R9 status beside R7's and R8's |
| `step10/requalify_r9.py` … `check_records.py` | `requalify_r9.py` (pyro / RF / mechanical / IMU / probes by the gate's own functions), `run_dc_r9.sh` (32 DC rows, refill scheduler), `tab_plan_r9.py`, `ordering_facts_r9.py`, `binding_note_r9.py`, `m2_sweep_r9.py`, `bind_report.py`, **new this session:** `fire_loop_r9.py` (F7's arithmetic from the bound solves, D-S10-16) and `check_records.py` (the records against their evidence, D-S10-13) |
| `step10_evidence/` | `requalify_r9.json`; `gate/` (session 3's `check.sh` output and its nine reports, each bound); `dc/` (the 32 solves, `dc_summary.txt`, `fire_loop.txt`); `reference_audit*`; `hotplug_feed.json`; `r9_binding_note.json`; `tab_plan.json`; `ordering_facts.json`; `m2_sweep.{json,txt}`; `tests.txt`; `check_records.txt` |
| `R9_DECISIONS.md` | D-S10-01 … D-S10-14 (sessions 1–2, D-S10-04's result filled now, its Q124 gate-drive figure corrected); D-S10-15 … D-S10-19 (session 3) |

## 2. Verification (board `fc3d5b34…`, unchanged by step 10)

| Item | Result |
|---|---|
| Board SHA-256 | `fc3d5b34…` at the start and the end of session 3 (sessions 1 and 2 recorded the same); every step-10 evidence file names it (check_records "binding") |
| `tools/check.sh` | exit 0 in 214 s (session 3, no shim; `step10_evidence/gate/check_sh.txt`): DRC 0 at every severity, unconnected 0, parity 0, ERC 0; metadata / 3D OK; silkscreen inside the outline; fit OK; plate model; rule-H seeded suite OK; check_r9 OK on all 40 rules; route_check r9 0 failing, 0 allowlisted, 0 leftovers; check_actuators OK. Its reports equal session 1's shim-run reports but for timestamps, paths and R-5's per-part split of the GNSS window samples (D-S10-18). Re-run at the end of the session on the finished records: exit 0 in 199 s, board SHA-256 unchanged, r9.json equal but for that split again |
| Tests | 474 tests in 26 suites OK, none skipped (KiCad python3, real kicad-cli); quality_audit 21 OK under python3 and KiCad python3 (run with `KICAD_PY` unset, as step 9 did: D-S10-18's third observation); audit_artifacts exit 0; the tests left git status and the board / fab files unchanged (`step10_evidence/tests.txt`) |
| DC (32 rows, `run_dc_r9.sh`, `DC_JOBS=8`) | all 32 rows rc 0 in 35.6 min (18:51-19:27Z), every output bound to `fc3d5b34…` (`step10_evidence/dc/`, `dc_summary.txt`); the fire loop 32.1 mΩ on the board, so F7's budget is 1.65 A ≥ 1.5 A (`dc/fire_loop.txt`); the servo GND return 0.32 mΩ; every supply drop under 80 mV at its load. The four fire segments equal the figures session 2 had put in M3_R9 (10.06 / 2.41 / 2.42 / 1.58 mΩ), and BAT_IN → U9 2.32, RAW_PROTECTED → U7 77.11 and → U11 16.22, CAM_5V → J9 2.88 mΩ equal step 9's post-check solves |
| Records check | `step10/check_records.py`: OK: 56 evidence files bound to the board, 151 hashed scripts and inputs equal to the files on disk, 10 records free of placeholders, every cited path resolving (the JSON keys included), 39 requalification rows each citing a file, 87 stated figures equal to their evidence (`step10_evidence/check_records.txt`) |
| Placeholders | none left in M3_R9, R9_VALIDATION, ORDERING, REQUIREMENTS, STATUS, AGENTS, README, R9_DECISIONS, this handoff or the progress log |

## 3. Reproduce

```bash
R=rocket-pcb/rocket-flight-computer-r9
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
NP=<python3 with numpy>                       # the parent project's cfd/venv/bin/python3
D=m3_design/assembly_review/sources/r9_design
B=m3_design/assembly_review/m3.kicad_pcb
cd $R && shasum -a 256 $B                     # fc3d5b34a4bfbaec...
NUMPY_PY=$NP bash tools/check.sh              # exit 0 (~4 min); without a GUI session see D-S6-14 / D-S9-06 / D-S10-07
DC_JOBS=8 bash $D/step10/run_dc_r9.sh $PWD/$B OUT gnd fire supply     # 32 rows, ~36 min with DC_JOBS=8 (the two GND windows set it)
python3 $D/step10/fire_loop_r9.py OUT $D/step9_evidence               # F7's figure from the bound solves
G=$D/step10_evidence/gate
PYTHONUNBUFFERED=1 $KP -I $D/step10/requalify_r9.py $B OUT/requalify_r9.json --seed $G/seed.json --fit $G/fit.json  # ~1 min
PYTHONUNBUFFERED=1 $KP -I $D/step10/tab_plan_r9.py $B OUT/tab_plan.json
PYTHONUNBUFFERED=1 $KP -I $D/step10/ordering_facts_r9.py $B OUT/ordering_facts.json \
    --dc $D/step9_evidence/dc005_raw.txt $D/step9_evidence/dc005_bat.txt $D/step9_evidence/dc005_fet.txt
PYTHONUNBUFFERED=1 $KP -I $D/step10/binding_note_r9.py $B OUT/r9_binding_note.json
PYTHONUNBUFFERED=1 $KP -I $D/step10/m2_sweep_r9.py $B --json OUT/m2_sweep.json > OUT/m2_sweep.txt
PYTHONUNBUFFERED=1 $KP -I tools/reference_audit.py $B [--extended]
(cd $D/step6_evidence && $NP -I hotplug_feed_r9.py --rb 2.32 --json OUT/hotplug_feed.json)
python3 $D/step10/bind_report.py $B REPORT OUT/REPORT                 # binds a report that does not name its board
python3 $D/step10/check_records.py --out $D/step10_evidence/check_records.txt    # the records against the evidence
(cd tools && for f in test_*.py; do KICAD_CLI=<kicad-cli> KICAD_PY=$KP NUMPY_PY=$NP $KP -B -m unittest ${f%.py}; done)
(cd quality_audit && env -u KICAD_PY python3 -B -m unittest test_quality_tools && env -u KICAD_PY $KP -B -m unittest test_quality_tools)
```

Session 3 ran `tools/check.sh`, the tests and kicad-cli straight, with a GUI session logged in. Without one, rebuild
the D-S6-14 shim and the D-S9-06 wrapper from the step-6 and step-9 handoffs, run check.sh with
`KICAD_CLI=<wrapper> KICAD_PY=<KiCad python3>` (D-S10-07) and give the tests the shim, as step 9 did. With a GUI session the
DC outputs start with wx's "create wxApp" assertion line; the evidence copies drop it (D-S10-15, D-S10-17).

## 4. Proposed parent VEHICLE.md stack-row update (D-S10-11; not applied)

In the parent repository's VEHICLE.md (`../../docs/VEHICLE.md` from this repository), row "Main-section stack,
bulkplate up", replace the flight-computer clause and the slack sentence with:

> flight computer board 102 (M3-ASSY-R9, the current candidate, 46 × 102 mm; M3-ASSY-R8, the owner-accepted fallback,
> is 46 × 118 mm with R7's outline, holes and jacks; parts on both sides; two edge-launch SMA jacks overhang its aft
> edge by 9.5 mm; J1's battery-wire entry faces the forward edge and both pyro terminals take their wires from the left
> (x = 0) edge; it fits the Ø50.8 mm coupler bore along its whole length; the sled puts the board's top face on the bore
> axis on nylon standoffs at the five M3 holes (4, 4), (42, 4), (4, 98), (42, 98) and (42, 59.5) mm, clears the bottom
> parts, which hang up to 3.0 mm below the board, is non-conductive under the whole bottom face, and carries both SMA
> plugs about 25–30 mm aft of the board edge), eyebolt nut and charge wiring ~25, recovery ~260 (…). Leaves ~68–84 mm
> of slack with R9 (~52–68 mm with R8's 118 mm board); …

Every R9 number is measured on `fc3d5b34…`: the outline and holes (`step10_evidence/requalify_r9.json` `mech.holes`,
`gate/fit.json`), the jacks' overhang (R-3), J1's entry (check_r9 M-4), the pyro terminals' entry (P-11), the deepest
bottom part (L1, 3.02 mm below the bottom face, `gate/check_sh.txt`); the slack is R8's row plus 16 mm (Calc). The parent
repository's commit rule is the coordinator's call (R8 D84's precedent).

## 5. What the review loop must know

- **None has run** (`r9_plan.md` §5). Inputs: R9_VALIDATION (the deviation list, the requalification tables) and this
  handoff. Reviewers: pyro safety, RF, power / thermal, mechanical, routing beauty (dedicated), gate integrity,
  requirements traceability, manufacturability.
- **Observations step 10 records and does not fix** (no tool its evidence hashes is changed, D-S10-18): check_r9's M-7
  docstring still says rotation 0 (the rule keys 180° on the revision and passes); R-5's per-part split of the in-window
  GNSS samples varies between runs (total and verdict do not); quality_audit's tests fail when `KICAD_PY` is exported
  (4 of 21), pass with it unset.
- **Figures worth a reviewer's look:** USB_LIMITED U10:6 → U11:7 83.02 mΩ (R8 52.66; 42 mV at 0.5 A; its two layer changes are one via each,
  each carrying the whole 0.5 A); the two GND vias beside Q124's source pins carrying 1.23 and 1.00 A of the 2.8 A fire
  pulse (≤ 20 ms; under 0.5 K, Inference); 3V3 → C100 44.85 mΩ (R8 18.36); RAW_ACT → J124.2 10.06 mΩ (the 1.0 mm RAW bar;
  R8 0.44). None is a rule miss: each sits inside F7's budget or the regulators' tolerances. Also C15's candidate
  redraws (VLOGIC, SERVO4_MCU, LED_RED, GNSS_ANT_GATE, RADIO_RXEN, USB_DP).
- **R8-era text left as written:** REQUIREMENTS P2 still says the owner's ruling on R8's sixth support is open, while M2
  records the R8 list accepted on 2026-10-20 with the C10 vibration item; R9 does not depend on it.

## 6. Open

1. The review loop on `fc3d5b34…` (two consecutive passes with no Critical or Major).
2. **Owner:** the dated acceptance of R9_VALIDATION's deviation list (M2), the length option (C1), the crystal plane
   (C14), TP120's in-pad vias (C18); commit or tag `m3-assy-r9`.
3. **Before ordering R9:** U4 in JLC stock or consigned; JLC's acceptance of four tabs on a 102 mm board (Inference,
   ORDERING §3); `FAB_NET=1 m3_design/r9_fab.sh` within 24 h of ordering (step 9's run, 2026-10-24 21:04Z, lapses at 2026-10-25
   21:04Z).
4. **Firmware:** an R9 binding from `step10_evidence/r9_binding_note.json` (the IMU map changes, the pins do not).
5. **Bench:** every ORDERING §5 item; R9-specific: the IMU sign check, the keyed-radio pyro-immunity test at 46 mm, the
   HSE frequency with the crystal plane, the stall test with the FETs judged, the tap check against 256.6 Hz, the
   hot-plug at U9 IN.
6. **Parent VEHICLE.md:** section 4's row (not applied).
7. **Scratch:** `<scratch>/r9/s10` (the DC run, the gate run, the test logs) is deleted at the end of this session; the
   evidence lives in `step10_evidence/`.
