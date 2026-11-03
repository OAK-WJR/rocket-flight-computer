"""R10 explicit supply cells and simple inner-plane boundaries (D-AVA-01).

In1 is solid GND; In2 uses broad rail regions, with only the crystal reference and
pyro-barrel ground exclusions retained. Every power route is drawn from its pads.
"""
import pcbnew
FULL = pcbnew.ZONE_CONNECTION_FULL
BAT, W, PAD_W, BYPASS_W = 1.0, .4, .3, .7
IN1_GND=[(.3,.3),(45.7,.3),(45.7,89.7),(.3,89.7)]
IN2_RAW=[(.3,.3),(45.7,.3),(45.7,89.7),(.3,89.7),(.3,61.8),(20.2,61.8),(20.2,64.3),(21.7,64.3),(21.7,82),(24,82),
         (24,64.9),(27.5,64.9),(27.5,61.8),(29.7,61.8),(29.7,82),(34.8,82),(34.8,61.8),(40.7,61.8),(40.7,63.3),(44,63.3),
         (44,4.4),(24.2,4.4),(24.2,7),(18,7),(18,10.5),(9,10.5),(9,7),(.3,7)]
IN2_PORT=[(24.5,4.7),(43.7,4.7),(43.7,63.0),(41,63.0),(41,7),(28,7),(28,15.5),(24.5,15.5)]
IN2_4V8=[(28.3,7.3),(40.7,7.3),(40.7,38),(31.5,38),(31.5,32.5),(28.3,32.5)]
IN2_3V3=[(.3,7.3),(8.7,7.3),(8.7,10.8),(18.3,10.8),(18.3,7.3),(24.2,7.3),(24.2,15.8),(28,15.8),
         (28,32.8),(31.2,32.8),(31.2,38.3),(40.7,38.3),(40.7,61.5),(34.5,61.5),(34.5,81.7),(30,81.7),(30,61.5),
         (27.2,61.5),(27.2,64.6),(23.7,64.6),(23.7,81.7),(22,81.7),(22,64.0),(20.5,64.0),(20.5,61.5),(.3,61.5)]
IN2_GND_CH1=[(.3,51.8),(8.65,51.8),(8.65,53.55),(9.75,53.55),(9.75,51.3),(18.55,51.3),
             (18.55,53.4),(18,53.4),(18,56.45),(17.45,56.45),(17.45,62.3),(16.5,62.3),(16.5,66.1),(.3,66.1)]
Y1_AREA = [(18.9, 44.3), (26.8, 44.3), (26.8, 48.95), (18.9, 48.95)]
# R8-RTE-02 (round 8): a bump (x 26.8-28.6, y 45.8-47.0) takes the 3V3 tooth between the island's edge and C22.2's GND via
# (27.8, 46.6) into the island, its edge meeting the antipad of the GND via (29.2, 46.2).
IN2_GND_Y1 = [(20.6, 44.3), (26.8, 44.3), (26.8, 45.8), (28.6, 45.8), (28.6, 47.0), (26.8, 47.0), (26.8, 49.7), (24.5, 49.7), (24.5, 48.95),
              (18.9, 48.95), (18.9, 45.45), (20.6, 45.45)]


def keepout(d, name, pts):
    """An In2 track keep-out rule area (fills, vias and pads allowed), as R9's Y1_In2_keepout after its step 8."""
    z = pcbnew.ZONE(d.board)
    z.SetIsRuleArea(True)
    z.SetLayer(pcbnew.In2_Cu)
    z.SetZoneName(name)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowZoneFills(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    if not d.dry:
        d.board.Add(z)


def planes(d):
    d.zone('R10_GND_In1', 'GND', 'In1', IN1_GND, 1, clr=0.25, conn=FULL)
    d.zone('R10_RAW_In2', 'RAW_PROTECTED', 'In2', IN2_RAW, 1, clr=0.25, conn=FULL)
    d.zone('R10_PORT_5V3_In2', 'PORT_5V3', 'In2', IN2_PORT, 1, clr=0.25, conn=FULL)
    d.zone('R10_PORT_4V8_In2', 'PORT_4V8', 'In2', IN2_4V8, 1, clr=0.25, conn=FULL)
    d.zone('R10_3V3_In2', '3V3', 'In2', IN2_3V3, 1, clr=0.25, conn=FULL)
    d.zone('R10_GND_In2_CH1', 'GND', 'In2', IN2_GND_CH1, 2, clr=0.25, conn=FULL)
    d.zone('R10_GND_In2_Y1', 'GND', 'In2', IN2_GND_Y1, 2, clr=0.25, conn=FULL)
    keepout(d, 'R10_Y1_In2_keepout', Y1_AREA)


S=.2


def battery(d):
    t,p,v=d.track,d.pad,d.via
    t('BAT_IN','F',BAT,[p('J1.1'),(8.9,74.1),(9.8,75),p('D8.1')])
    # C80 moves 0.05 mm for the maximum DB125 courtyard; keep the straight
    # capacitor bus within its pad rather than introducing a tiny diagonal.
    t('BAT_IN','F',BAT,[p('D8.1'),(12.525,75.825),(12.525,79.5),p('C96.1'),p('C89.1'),p('C95.1')])
    t('BAT_IN','B',BAT,[p('J1.1'),(13.0,74.1),p('Q120.9')])
    # D-R24-17: U9's input runs straight up its pad's axis through C88.1 (C88 now sits on that axis below U9), so no
    # track turns 90 degrees at C88, at the trunk or at the 1.0 mm IN via: the via climbs 0.15 mm (its 1.0 mm F.Cu feed
    # keeps a 1.02 mm leg past its chamfer), the 1.0 mm run reaches the via on one diagonal, and the R82 / R167 tap
    # leaves the trunk at a T, where the run narrows to the 0.7 mm bypass section.
    feed=(17.5,87.15)
    t('BAT_IN','F',BAT,[p('C95.1'),(14.116,88.891),(17.5,88.891),feed]);v('BAT_IN',feed,size=(1.,.5))
    t('BAT_IN','B',BAT,[feed,(18.25,86.4),(18.25,85.3)])
    t('BAT_IN','B',BYPASS_W,[(18.25,85.3),p('C88.1')])
    t('BAT_IN','B',PAD_W,[p('C88.1'),p('U9.5')])
    t('BAT_IN','B',W,[(18.25,85.3),(15.5,85.3),p('R82.1')])
    t('BAT_IN','B',W,[p('R82.1'),(13.925,83.9),p('R167.1')])
    t('BAT_IN','F',S,[p('D8.1'),(10.2,71.85),(10.2,70.2),(13.075,70.2),p('R80.1')])
    t('BAT_IN','F',W,[p('C89.1'),(11.625,83.8),p('TP80.1')])
    t('BAT_DAMP','F',W,[p('C95.2'),p('C89.2'),(18.6,84.7),p('R166.1')])
    t('GND','F',W,[p('R166.2'),(29,86.3)]);v('GND',(29,86.3))


def control(d):
    t,p,v=d.track,d.pad,d.via
    t('BAT_SW_SOURCE','B',S,[p('J400.1'),(10.8,67.5),(10.8,69.2)]);v('BAT_SW_SOURCE',(10.8,69.2))
    t('BAT_SW_SOURCE','F',S,[(10.8,69.2),p('R80.2')])
    t('BAT_SW_RETURN','F',S,[p('J400.2'),(11.825,67.6),p('R165.1')])
    # D-R24-11: J400.2's contact clamp D402 sits on the bottom under J400's body on the wire side, between pins 1 and 2,
    # as D440 sits between J440's pins 3 and 4 (M-6 1.5 mm): the tap leaves J400.2's own pad west on B.Cu and turns
    # north into D402.1, so a discharge into the screw reaches the clamp before R165. The clamp's return goes 0.7 mm east
    # to its own GND via (In1 / In2 GND there), clear of the J400 designator and BAT legends on the top and 2:SW below.
    j,b=p('J400.2'),p('D402.1')
    t('BAT_SW_RETURN','B',S,[j,(b[0],j[1]),b])
    a=p('D402.2');at=(round(a[0]+.7,4),a[1])
    t('GND','B',S,[a,at]);v('GND',at)
    # D-R19-02 (R19-SAF-02): the via sits 0.2 mm further south, 0.500 mm from R134.2 (RAW_ACT) instead of 0.300 mm.
    # D-R21-04: with R81's stub gone (D-R21-05) the run turns into the via on a 45 degree piece from (19.075, 66.0), not
    # at (19.675, 66.0) (a removable local bump on this critical net).
    t('BAT_ENABLE','F',S,[p('R165.2'),(15.3,67.0),(16.3,66.0),(19.075,66.0),(19.675,66.6)]);v('BAT_ENABLE',(19.675,66.6))
    # D-R21-04 (R21-REQ-04): the B.Cu hop's last bend moves 0.3 mm west, so its final 45 degree run is 0.849 mm long
    # into the via (21.3, 68.9) (was a 0.424 mm jog, 0.3 mm off the F.Cu run); TP120's 1.0 mm and R88.2 stay clear.
    t('BAT_ENABLE','B',S,[(19.675,66.6),(20.7,67.625),(20.7,68.3),(21.3,68.9)]);v('BAT_ENABLE',(21.3,68.9))
    # D-R21-05 (R21-SAF-01): R81 (EN's pull-down) and C87 (its filter) sit on the F.Cu EN run at U9's end, pads 1 on the
    # run (C87.1 on its last bend, so no piece of the run lies inside a pad) and pads 2 in the F.Cu GND piece of U9.8's
    # via (20.2, 81.0): an open anywhere up the switch run leaves EN held low by R81, and only the via (17.1, 82.8)
    # stays in series between U9.1 and R81 / C87.
    t('BAT_ENABLE','F',S,[(21.3,68.9),(21.3,75.2),(18.0232,78.4768),p('R81.1'),p('C87.1'),(17.1,82.8)])
    v('BAT_ENABLE',(17.1,82.8));t('BAT_ENABLE','B',S,[(17.1,82.8),p('U9.1')])



def efuse(d):
    t,p,v=d.track,d.pad,d.via;rp='RAW_PROTECTED'
    t(rp,'B',PAD_W,[p('U9.6'),(18.75,79.8)])
    t(rp,'B',BYPASS_W,[(18.75,79.8),(19.3,79.25),p('C82.1')])
    # D9 remains beside OUT; its cathode faces north, and its return shares the input-capacitor ground via.
    t(rp,'B',BYPASS_W,[(18.75,79.8),(16.25,77.3),p('D9.1')])
    # D-R24-17: the two In2 vias each leave C82.1's edge on their own 0.7 mm leg (south, and east), so no track turns
    # 90 degrees at a via (was south to the first via, then a 0.4 mm link east to the second).
    t(rp,'B',BYPASS_W,[p('C82.1'),(20.3,78.25),(20.3,79.1)])
    for at in ((20.3,79.1),(21.1,78.25)):v(rp,at)
    t(rp,'B',BYPASS_W,[(20.3,78.25),(21.1,78.25)])
    t('GND','B',W,[p('C82.2'),(20.45,76.4),(20.85,76.4)]);v('GND',(20.85,76.4))
    t('GND','B',W,[p('D9.2'),(16.4,79.9),(17.2,79.9)]);v('GND',(17.2,79.9))
    t('GND','F',W,[p('C96.2'),(15.475,79.5),(15.875,79.9),(17.2,79.9)])
    t('BAT_ILIM','B',S,[p('U9.9'),p('R84.1')])
    t('BAT_DVDT','B',S,[p('U9.7'),(19.85,80.1),p('C81.1')])
    # Keep the three-way junction explicit without the former 0.15 mm open-copper leg.
    # Pads/vias stay fixed; the local DRC/route comparison was checked before adoption.
    t('BAT_OVLO','B',S,[p('U9.2'),(16.9,81.825),(16.25,82.475),(16.25,83.0)])
    t('BAT_OVLO','B',S,[p('R83.1'),(12.025,83.0),(16.25,83.0),p('R82.2')])
    t('GND','B',S,[p('U9.8'),(19.825,81.375),(20.2,81.0)]);v('GND',(20.2,81.0))
    t('GND','B',P,[p('C88.2'),(19.59,84.06)]);v('GND',(19.59,84.06))
    for layer,pad in [('B','U11.2'),('F','C97.1')]:t(rp,layer,P,[p(pad),(24.3,66.0)])
    v(rp,(24.3,66.0))
    t(rp,'B',W,[p('TP81.1'),(31.0,83.6)]);v(rp,(31.0,83.6))
    t(rp,'F',W,[p('R92.1'),(30.175,85.9)]);v(rp,(30.175,85.9))      # D-R24-15: with R92, 0.8 mm aft


P=.3

def port_supply(d):
    t,p,v=d.track,d.pad,d.via;rp='RAW_PROTECTED'
    # Maker-derived buck loop, unchanged in its local frame.
    t(rp,'F',W,[p('C400.1'),p('U400.2'),p('U400.3'),(15.8,9.0)])
    # D-R24-17: the second input via sits on the drop, before a 45-degree turn into C401.1 (was at a 90-degree corner).
    t(rp,'F',W,[p('C400.1'),(14.1,7.6),(14.1,8.5),(14.6,9.0),p('C401.1')])
    for at in ((14.1,7.6),(14.1,8.5)):v(rp,at)
    t('PORT_SW','F',W,[p('U400.5'),p('C402.2'),p('L400.1')])
    t('PORT_BST','F',.25,[p('U400.6'),(18.6,4.0),p('C402.1')])
    t('PORT_FB','F',S,[p('U400.1'),p('R404.2'),p('R401.1')])
    t('PORT_FB_TOP','F',S,[p('R404.1'),p('R400.2')])
    t('PORT_5V3','F',S,[p('R400.1'),(27.8,1.8),(28.6,2.6)])
    t('PORT_5V3','F',BAT,[p('L400.2'),(28.6,5.55)])
    t('PORT_5V3','F',BAT,[p('C403.1'),(28.6,5.55),p('C404.1')])
    t('PORT_5V3','F',W,[p('C404.1'),(27.6,8.0),(26.8,8.0),(26.0,8.0)])
    for at in ((26.0,8.0),(26.8,8.0)):v('PORT_5V3',at)
    # LDO input and exact filled/capped thermal pair retained; output parts align with the port column.
    t('PORT_5V3','B',W,[p('C405.1'),(25.9,8.6)]);v('PORT_5V3',(25.9,8.6))
    # D-R19-09 (R19-PWR-01): a second In2 via on the LDO input run, between C405.1 and U401.10.
    t('PORT_5V3','B',W,[p('C405.1'),(26.45,10.85),(26.45,11.95),p('U401.10')]);v('PORT_5V3',(26.45,11.95))
    t('PORT_5V3','B',.25,[p('U401.10'),p('U401.9')])
    t('PORT_5V3','B',S,[p('U401.7'),(25.65,14.1),(25.65,14.9)]);v('PORT_5V3',(25.65,14.9))
    t('PORT_5V3','B',S,[(25.65,14.9),(24.9,14.9)]);v('PORT_5V3',(24.9,14.9))   # D-R19-09: EN's second In2 via
    d.link('PORT_LDO_SS','B',S,'U401.8','C408.1')
    for at in ((27.3,13.6),(27.9,13.6)):v('GND',at,filled=True,capped=True)
    # D-R24-17: the OUT run leaves the U401.1 / U401.2 link at a T between the two pins (was a 90-degree bend in U401.1's
    # pad), on y 12.85 to R402.1 (R402 0.25 mm south with it).
    t('PORT_4V8','B',.25,[p('U401.1'),(28.75,12.85),p('U401.2')])
    # D-R24-09 (round 21 power lens; D-R20-02 / D-R21 U401.3 exception): R402 / R403 sit on B.Cu beside U401, so the
    # output tap, the FB node and the divider's ground all join U401's pins on bottom copper with no via: the divider
    # top on the OUT run past its via, FB straight east from U401.3, the bottom straight to U401.4 (GND).
    # The OUT run's In2 via moves 0.95 mm north on the C406.1 run, off R402.1's land.
    t('PORT_4V8','B',W,[(28.75,12.85),(29.75,12.85),p('R402.1')])
    t('PORT_LDO_FB','B',S,[p('U401.3'),(31.725,13.6)])
    t('PORT_LDO_FB','B',S,[p('R402.2'),(31.725,13.6),p('R403.1')])
    t('GND','B',S,[p('R403.2'),(29.575,14.1),p('U401.4')])
    t('PORT_4V8','B',W,[p('C406.1'),(29.75,9.95),(29.75,11.65),(29.75,12.85)]);v('PORT_4V8',(29.75,11.65))
    v('PORT_4V8',(29.75,9.95))                    # D-R19-09: the LDO output's second In2 via, at C406.1's run bend
    t('PORT_4V8','F',W,[p('C407.1'),(31.1,20.3),(30.3,20.3)]);v('PORT_4V8',(30.3,20.3))
    t('PORT_4V8','B',S,[p('R405.1'),(33.725,16.35),(33.725,17.3)])
    # Always-on port bypass cells and terminal feeds.
    for cap,small,jack in [('C411','C410','J410'),('C421','C420','J420')]:
        a=p(cap+'.1')
        if cap=='C411':
            # The plane via lies on the direct diagonal, clear of the cap land; terminal entry is centred.
            at=(36.0,23.35)
            t('PORT_4V8','B',W,[(35.1,24.25),at,p(jack+'.1')]);v('PORT_4V8',at)
        else:
            t('PORT_4V8','B',W,[a,p(jack+'.1')])
            at=(a[0],a[1]-1.5);t('PORT_4V8','B',W,[a,at]);v('PORT_4V8',at)
        a=p(small+'.1');at=(a[0],a[1]-.9);t('PORT_4V8','B',W,[a,at]);v('PORT_4V8',at)
    # D-R19-14: the AUX port J440 (north-west corner, In2 is 3V3 there) takes PORT_4V8 on F.Cu from the LDO output's In2
    # region through two vias, (29.75, 9.95) (C406.1's run bend) and a second at (30.5, 9.95), west along y 9.95 north of
    # GPS_RX's turn, then on y 11.0 south of C405.2's return via and C401, with its C445 / C444 bypass pair (the C411 /
    # C410 copies) on the run.
    v('PORT_4V8',(30.5,9.95))
    t('PORT_4V8','F',W,[(30.5,9.95),(29.75,9.95),(26.5,9.95),(25.45,11.0),(15.2,11.0),(12.5,11.0),p('J440.1')])
    t('PORT_4V8','F',W,[(15.2,11.0),p('C445.1')])
    t('PORT_4V8','F',W,[(12.5,11.0),p('C444.1')])
    # Camera input bypass is local to IN; the quiet rail arrives along the bottom of the cell.
    # D-R19-09 (R19-PWR-01): the camera switch's feed gets a second In2 via 0.75 mm further into the strip.
    t('PORT_5V3','B',W,[p('U402.1'),(30.7,61.025),p('C430.1'),(42.0,61.8),(42.75,61.8)])
    v('PORT_5V3',(42.0,61.8));v('PORT_5V3',(42.75,61.8))
    t('CAM_5V','B',W,[p('U402.6'),(34.2,60.85),(37.7,60.85),p('C431.1')])
    # Pass west of the rotated cap's return land and the TP74 keep-out.
    t('CAM_5V','B',W,[(39.3,59.0),(37.75,57.45),(37.75,53.6),p('J9.1')])
    t('CAM_5V','B',W,[p('J9.1'),(34.95,52.75)])
    t('CAM_5V','B',W,[p('C91.1'),(34.2,51.675),(34.2,49.325),(33.625,48.75),p('U13.1')])
    t('CAM_ILIM','B',S,[p('U402.5'),(34.175,59.0),p('R430.1')])


def logic(d):
    t,p,v=d.track,d.pad,d.via
    # Mux, input capacitors and 3V3 buck retain their maker-derived relative geometry.
    t('VLOGIC','B',W,[p('U11.8'),p('U11.1'),p('C99.1'),p('U2.2'),p('U2.3'),(27.75,68.6),(29.8,68.6)])
    t('VLOGIC','B',W,[(29.8,68.6),(29.8,72.8),p('C7.1')])
    # D-R19-09 (R19-PWR-01): C84 hangs on two parallel vias, so one open barrel no longer drops the 470 uF hold-up.
    t('VLOGIC','B',W,[(29.8,72.8),(29.8,81.15),(29.8,81.75),(29.5,82.05)]);v('VLOGIC',(29.5,82.05))
    v('VLOGIC',(29.8,81.15))
    t('VLOGIC','F',W,[(29.5,82.05),(29.2,81.75),p('C84.1')])
    t('VLOGIC','F',W,[(29.8,81.15),(29.2,81.75)])
    # Probe and divider share a direct trunk above the mux, kept out of the switch node.
    t('VLOGIC','B',W,[(29.8,81.75),(34.25,81.75),p('TP83.1')])
    t('VLOGIC','B',S,[(29.8,68.6),(29.8,67.7),(34.5,63)])
    v('VLOGIC',(34.5,63));t('VLOGIC','F',S,[(34.5,63),(34.5,62.4),(34.5,59.47),p('R60.1')])
    # D-R24-08 (R22-POWER-02): PA6's VLOGIC sense gets a second barrel on its F.Cu drop, 0.6 mm north of the first,
    # joined to it on B.Cu: either barrel alone feeds R60.1.
    v('VLOGIC',(34.5,62.4));t('VLOGIC','B',S,[(34.5,62.4),(34.5,63)])
    d.link('LOGIC_ILIM','B',S,'U11.10','R86.1')
    t('LOGIC_SS','B',S,[p('U11.11'),(26.15,64.75),p('C85.1')])
    t('USB_OVLO','B',S,[p('R87.2'),(22.5,64.25),p('U11.5')]);t('USB_OVLO','B',S,[p('R87.2'),p('R88.1')])
    d.link('SW_NODE','B',W,'U2.5','L1.1')
    t('SW_NODE','B',W,[(24.4,72.5),(21.78,72.5),p('C5.1')])
    t('BST','B',.25,[p('U2.6'),(23.05,71.0),p('C5.2')])
    t('3V3','B',W,[p('U2.1'),(23.2,68.6)]);v('3V3',(23.2,68.6))
    # D-R21-02 (R21-PWR-01): U2.1 (AP63203 FB, its output sense) also reaches the In2 3V3 plane through R89's via
    # (23.0, 70.0): one 45 degree B.Cu run from the pad's south end (the gate lens's f01b). An in-line second via at
    # (22.55, 68.6) would sit 0.886 mm (In2) from the BAT_ENABLE barrel (21.3, 68.9), under S-8's 1.0 mm.
    t('3V3','B',W,[(24.05,68.95),(23.0,70.0)])
    t('3V3','B',W,[(24.2,77.0),(23.1,78.1)]);v('3V3',(23.1,78.1))
    t('3V3','B',W,[p('C8.1'),(25.4,79.26),p('C9.1')])
    # Bridge the buck and core plane regions across the RAW/VLOGIC corridor.
    t('3V3','B',W,[(25.4,79.26),(26.4,79.26)]);v('3V3',(26.4,79.26))
    t('3V3','F',W,[(26.4,79.26),(30.8,79.26)]);v('3V3',(30.8,79.26))
    t('3V3','B',W,[p('L1.2'),(25.0,77.88),p('C8.1')])


def joins(d):
    t,p,v=d.track,d.pad,d.via
    t('GND','F',S,[p('U1.74'),(17.5,39.3)])
    t('GND','B',P,[p('C17.2'),(17.5,38.82),(17.5,39.3)])
    t('GND','F',P,[p('J3.A1B12'),(6.88,26.8)]);t('GND','F',P,[p('J3.B1A12'),(6.88,34.8)])
    d.link('GND','B',S,'C98.2','U11.6',((23.5,62.5),))
    d.via('GND',(23.8,62.95))
    # D-R18-03: U11.12 joins C99.2's return (its own via left the ACT_EN_MCU corridor).
    t('GND','B',P,[p('U11.12'),(25.8,66.9)])


def draw(d):
    planes(d);battery(d);control(d);efuse(d);port_supply(d);logic(d);joins(d)
    from r10_route_usb import power_feed
    power_feed(d)
