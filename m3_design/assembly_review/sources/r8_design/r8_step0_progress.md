# R8 step 0 progress log (owner decisions and pin table)

Resume from the last entry. Outputs: `R8_DECISIONS.md`, `pin_table.tsv` (this folder), `docs/REQUIREMENTS.md` edits, `r8_step0_handoff.md`.

## Log

1. Read r8_plan.md, survey_constraints/connectivity/baseline, plan_partial/cleansheet (incremental grepped). No earlier step handoffs exist (step 0 is first).
2. Read AGENTS.md, REQUIREMENTS.md (F10 pin contract), ROCKET_FC_FROZEN_DESIGN.md §3.10, R7 review pass1/2/3_electrical pin analyses.
3. Datasheets: none on disk. st.com curl hangs (HTTP/2 error, HTTP/1.1 stalls). Trying mirrors. Scratch folder: scratchpad/st_docs/{ds,an,rm} (delete when done).
4. Downloaded from st.com with browser headers (plain curl hangs): DS12110 Rev 11 (Jan 2026), AN2606 Rev 70 (Feb 2026), RM0433 Rev 9 (Oct 2026) into scratchpad/st_docs; pdftotext done. Read AN2606 Table 135/136 (pp. 320-326), RM0433 §50.4.2/§50.4.4 note/§50.11.4 (IOSWP, pp. 2159/2161/2222; Table 422 p. 2157 no per-instance restriction), DS12110 Table 10 pp. 89-94 (visual read 1), Table 9 I/O structures, §3.8 (p. 32), Table 8 (p. 63), Table 11 (p. 103).
5. D121 landing-order check (B's d121.py convention) on the R7 footprint: bottom rot 90 lands S1..S4 W->E for a bundle from U1 heading forward (pre-reversal); top rot 90 lands S4..S1. Decision: D121 bottom before the order reversal.
6. Next: annulus model of follow-on moves on B's seed (scratchpad/step0/pinmodel.py).
7. Annulus model (scratchpad/step0/pinmodel.py, search.py, variants.py, final.py) on B's seed with U1 rot 0 at (23,45): R7 pins 134 crossings; forced-only (H0+UART7+PE9, LEDs PA6/PA7, VBUS PC8) 104; greedy follow-on 17-20; decided map F1 = 13. Six optional moves each remove 7-19 crossings (BAT_FAULT_N PA4, LOGIC_SOURCE_ST PA5, CAM_UART_OE PA7, CAM_FAULT_N PE11, CAM_PWR_EN PE12, BUZZ_DRV PC13); USB_FAULT_N (gain 1) and PULLPIN (0) stay. LEDs move to PD5/PD7 with the LEDs placed on the west edge (top).
8. Visual second read of DS12110 Table 9 pp. 64, 69, 70, 72, 73, 75, 76, 79, 82, 83 and Table 10 text-layout re-read of every moved pin (read 2); all agree with read 1.
9. IPC fit (scorecard.py): outer 35 um: 30 C at 3.71 mm, 25 C at 4.35, 20 C at 5.28; inner 20 C at 5.56. AON6403 source row 3.12 mm span (R7 footprint).
10. Next: write pin_table.tsv (generator scratchpad/step0/make_table.py), R8_DECISIONS.md, REQUIREMENTS edits, handoff.
11. pin_table.tsv written (100 rows, 20 columns, 27 changed pins) by step0/make_table.py; reproduced byte-identical from `git show 431025d:...m3.kicad_pcb`. Model scripts copied to r8_design/step0/. Next: R8_DECISIONS.md, REQUIREMENTS edits, handoff.
12. R8_DECISIONS.md written (D1-D14). REQUIREMENTS.md F4, F10, M2 edited (R8 marks; 3 table rows). Verification: every pin_table row carries its citations (script check, 0 gaps); moved AF and pin numbers also agree with ST open pin data (third source). Deleted scratch repro board copy; kept scratchpad/st_docs (datasheets) for later steps.
13. Next: handoff, final read-through.
14. Handoff written (r8_step0_handoff.md). Final read-through of R8_DECISIONS done (added PC2_C/PC3_C SPI2 path via the SYSCFG analog switch, DS Table 9 note 4 p. 88). Step 0 complete; verification passed.
