# Round12 C98 local return candidate

A single ordinary GND stitch at **(23.8,62.95)** passes the executed native DRC/parity, routing, fit and19 selected R10 contracts. It preserves every original track and gives C98.2 a local saved-copper route through In1 to the existing U11.12 GND fanout. Root accepted this candidate for source integration. The frozen PCB remains unchanged.

Frozen SHA-256 before/after: `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`. Temporary candidate: `34a2adfdb958f31e5210bfaea3113e93fcfe6f1e3f0227d537ed339b278f6103` in `.supervisor/r12_c98_via_only_native/m3.kicad_pcb`. Task-supplied HEAD: `d57b216c365fc8d18896bceba37f63caf20d52a4`. This is focused implementation evidence, with **0 Critical /0 Major /1 carried Minor** on the canonical board; it earns no full-round or clean-round credit. The completed full-round routing reports are unchanged.

## Exact proposed source change

In `m3_design/r10_route_power.py`, function `joins()`, keep the existing link and add only the second line:

```python
d.link('GND','B',S,'C98.2','U11.6',((23.5,62.5),))
d.via('GND',(23.8,62.95))
```

No fanout-table row or GND track is added. `m3_design/r10_fanout.tsv` and the ground stage remain unchanged. `Draw.via()` supplies the ordinary0.5mm ring /0.3mm drill, through F.Cu–B.Cu, unfilled and uncapped. The normal ground-stage loop removes unconnected inner pads while keeping start/end layers. No GAP-3 or other via-in-pad exemption is used. An equivalent STITCH-table insertion was considered; the source location above matches root's assigned source ownership and produces the same native via.

The temporary board has973 segments /296 vias /1809.708732mm track, against973 /295 /1809.708732mm frozen. Native multiset comparison proves every original track and via identical; only the specified GND via is added. Part poses, pad lands/nets and all non-GND tracks/vias are identical.

## R12-RTE-02: carried Minor, checked CAD remedy

File `m3_design/assembly_review/m3.kicad_pcb`: C98.2 GND at(23.8,62.2), B.Cu; U11.12 device GND at(25.8,65.25). U11.6 is PR1 tied GND, not the device ground pin. The original0.2mm GND track remains (23.8,62.2)→(23.5,62.5)→(23.5,63.75),1.674264mm total.

Native saved-fill contact tests establish the physical copper chain: C98.2 and the new via touch the same20.300299mm² B.GND island; the new via and U11.12's existing(25.8,65.9) via touch the same3760.541955mm² In1 GND island; U11.12 and its existing via touch the same B.GND island. New-via centres are contained without hit-test tolerance in the B, In1 and F saved GND fills. The previous remote(30.15,52.0) stitch remains. Fill areas are unchanged.

At0.05mm grid, saved-copper C98.2→U11.12 return falls from**31.812237mm to7.345584mm**, a24.466652mm geometric reduction. Candidate0.025mm-grid sensitivity result is7.270584mm. The method searches B.Cu plus In1.Cu and conservatively charges full1.6mm board thickness per layer change. Baseline needed a12mm search margin; candidate uses the normal2mm local margin. These are geometric path lengths, not inductance or transient measurements. [TI TPS2121 SLVSEA3F](https://www.ti.com/lit/ds/symlink/tps2121.pdf), p4 establishes pins6/12; p33 calls for close bypasses and short/wide layout but supplies no numerical loop limit. No functional failure of the frozen board has been demonstrated.

## Ordinary manufacturing margins and M2 disposition

|New-via relationship|Ring-to-pad/paste gap|Hole-to-mask/paste gap|
|---|---:|---:|
|C98.2, B.Cu GND|0.025mm|0.125mm|
|C97.2, F.Cu GND|0.040mm|0.140mm|
|D123.2, F.Cu BUZZ_OUT|0.180mm|0.280mm|
|U11.6, B.Cu GND|0.450mm|0.550mm|
|U11.7, B.Cu USB_LIMITED|0.211mm|0.311mm|

Mask expansion is0 for these pads. The new via meets the0.1mm hole-to-mask/paste minimum and no ring/paste overlap rule. The closest new C98 hole margin is0.025mm beyond that rule. Native distance precision is0.001mm; this is nominal CAD evidence. Closest nearby foreign tracks have0.183mm gap to USB_LIMITED on B.Cu and0.222mm to BUZZ_OUT on F.Cu, above0.15mm. Native DRC also checks all other copper, holes and constraints.

**Keep one new explicit M2 deviation:** `via_on_track_in_fill`, GND B.Cu at(23.8,62.95). The centre is0.300mm off the original x=23.5 straight track, and its0.25mm ring overlaps the0.1mm half-width by0.050mm. The via independently stitches the saved GND fill; it is not attached only by track overlap. An exact collinear centre node there would alter the original copper. No jog or node is added. The informational classification is not used as evidence of the return improvement; the native fill contacts and path measurement provide that evidence. Total route instances rise140→141; the9 old noncritical leftovers are unchanged. Two USB_LIMITED power-via companion distances improve2.618→1.801mm and2.915→1.931mm, both still above1.5mm and still informational under the existing power-via policy.

## Executed checks

- Official KiCad10.0.7 CLI DRC, all severities plus schematic parity:0 violations /0 unconnected /0 parity /0 ignored checks.
- KiCad10.0.6 Python native geometry, refill and saved-fill contacts: pass. `K-fill` confirms saved fill freshness.
- `route_check.py --profile r10 --bumps-all`:0 failing /0 allowed /0 stale, no new critical bump,57 bump windows. The single new in-fill annotation is recorded above.
- `fit_check.py --profile r10`: pass, CAD envelopes only. Native M-6 bottom keepouts and S-8 pyro-barrel-to-inner-copper rules pass.
-19 selected contracts pass: S-1,S-2,S-3,S-5,S-8,S-9,F9-2,M-5,M-6,P-11,K-copper,K-inner,K-reference,K-region,K-width,K-retained,K-fill,K-rules,K-legends. This selected run explicitly reports `complete:false`; it is not the31-rule full gate. K-reference retains160761 samples,10056 unreferenced(10049 own antipad),6 recorded strays,0 loose. K-region retains165 items /62984 samples /39 nets. Seven terminal wire-room results remain5.003mm.

The bounded0.05mm placement screen sampled15373 sites within3.5mm of C98.2:155 passed ordinary geometric screening and one grid site lay inside the existing C98 B.GND island. This is not a continuous/global impossibility claim. The alternative repointed GND link (23.8,62.2)→(23.8,62.95)→(23.5,63.25)→(23.5,63.75) passed DRC but failed routing for a0.424mm GND tiny jog /0.300mm offset; it is rejected.

## Provenance and limits

Executed generator/checker fingerprints, exact contacts, route annotation, full selected-rule evidence and raw evidence-file fingerprints are in `round12_c98_candidate.json`. Principal source fingerprints before integration:

|Source|SHA-256|
|---|---|
|m3_design/r10_route_power.py|`47b09de152993cb694578fa947043db895cc1290591e619599db07684529cff8`|
|m3_design/r10_fanout.tsv|`6997c2b9ac393cd182a2a02992afd64d667cfdabffbc862e4718e8b174c5573f`|
|m3_design/r10_route_ground.py|`01ed1e24283f5b355a38b09c095ffbbd8877ff68174648ffaa53b4633463cb3b`|
|tools/check_r10.py|`003c0e88d643d8be9d14fb5dff4101296bed5892cf22a344070a71b184d65a55`|
|tools/route_check.py|`d8070ccbb4a9ef21d2adc442577ac93110822e54d708a884b1c225896ae670f0`|

No canonical PCB save, source edit, full build/check, ERC rerun, fabrication export or Git action occurred during this focused candidate phase. Temporary evidence is under `.supervisor/r12_c98_*`. Root owns the later combined regeneration, all gates and hash/fabrication refresh. Electrical/thermal behavior, soldering/assembly, inductance and physical fit remain unqualified. The original carried finding stays open on the frozen PCB until the accepted source change is rebuilt and verified; the in-fill M2 annotation remains on the owner deviation list.
