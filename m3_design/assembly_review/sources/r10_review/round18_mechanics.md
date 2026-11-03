# Round 18 - placement and mechanics (Claude)

Board SHA-256 before/after: `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982` (unchanged). Totals: 0 Critical, 0 Major, 4 Minor.

- **R18-MEC-01** (Minor, new): Plate/strain evidence omits the heaviest, least-supported east-edge terminals; east mid-span has no support
  - Fix: Add J410, J420, J9, J400, C431, C421, C411 and R150-R155 to STRAIN_PARTS and the M3_R10 text; state the east-edge asymmetry; if the owner reopens placement, consider an east mid-span support near (42,59) with C431 relocated, otherwise require first-article vibration/shock and a >=4 mm standoff with underside insulation.
- **R18-MEC-02** (Minor, new): Top-hardware clearance at the (4,44.3) support is 0.008 mm to the gate and 0.31-0.42 mm to exposed 3V3/NRST/GND lands
  - Fix: Make nylon (or insulated) screws and washers at all five supports an explicit ORDERING/REQUIREMENTS line, or cover LED1/LED2/J2 lands within 4.5 mm of the support with mask/Kapton at assembly. No board change needed.
- **R18-MEC-03** (Minor, new): Wire-room figure uses the bare bore while P2 requires a 0.5 mm wall allowance; margin to the 4.95 mm floor is 0.053 mm
  - Fix: State in P2/OQ-1 that wire room is measured to the nominal Ø50.8 wall at 5 mm height and that the 0.5 mm allowance is not applied to it (or restate the floor); print all seven terminals in fit_check output.
- **R18-MEC-04** (Minor, carried (R17-MEC-02, R16-MEC-02)): Parent ../../docs/VEHICLE.md still describes removed R10 hardware
  - Fix: Apply the handoff replacement text in the parent repository workflow.

Confirmed: IMU map (+X=-x, +Y=-y, +Z=-z; roll=-gyro_Y; lever x=-6.0 mm), bore fit (worst 0.89 mm J3, DBs 2.98 mm), supports, plate 181.1 Hz/70.5 g, wire room 5.003 mm bare bore.

Fix-now (docs/tool only): R18-MEC-02: add nylon/insulated top hardware requirement (docs only); R18-MEC-01: add east-edge terminals and C431/C421/C411 to the plate strain table (tool/doc only); R18-MEC-03: one-sentence wire-room definition and print all seven terminals in fit_check

Details and coverage limits are in the JSON.
