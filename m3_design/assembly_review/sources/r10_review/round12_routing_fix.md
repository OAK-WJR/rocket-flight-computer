# Round12 routing source integration

Two full source-driven native builds/check0 reproduce42 generated files. The
PCB is `7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`.
All original part poses,pad lands/nets,GND tracks and via geometry/flags are
identical. Three BAT_ENABLE F.Cu segments are replaced, saving1.408326mm, and
one ordinary0.5/0.3mm GND stitch at(23.8,62.95) is added. The fanout table is
unchanged. C98's0.05mm-grid saved-copper device return is7.345584mm versus
31.812237mm before. These are geometric paths, not measured inductance or
source-transfer/USB-attach response.

The current141 instances partition110 ordinary information+22 AUD10 inside-pad+
9 hygiene leftovers;0 failing/allowlisted/stale/local-bump candidates,56 bump
windows. The9 locations appear once in the final deviation JSON. Two new
information items are explicit: C98's in-fill ring/track annotation, and the
shortened BAT_ENABLE chain's `extra_bends` label. The latter equals its
15.639697mm unobstructed45degree geodesic. Both simplest two-segment alternatives
fail native0.15mm copper screening; no universal impossibility is asserted.
The rejected repointed C98 link added a0.424mm tiny jog and was not adopted.

Full native geometry,actual final gate,category counts and alternative-screen
evidence are in `round12_fix_native.json` and `round12_routing_fix.json`.
`round12_fix_validation.json` binds the two complete builds. Fresh full rounds
13/14 must review this committed PCB; focused work earns no clean-round credit.
Circuit,pins,axes,supports,gate scope and AGENTS section2 are unchanged.
