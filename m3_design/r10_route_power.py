"""R10 explicit supply cells and simple inner-plane boundaries (D-AVA-01).

In1 is solid GND; In2 uses broad rail regions, with only the crystal reference and
pyro-barrel ground exclusions retained. Every power route is drawn from its pads.
"""
import pcbnew
FULL = pcbnew.ZONE_CONNECTION_FULL
BAT, W, PAD_W, BYPASS_W = 1.0, .4, .3, .7
IN1_GND=[(.3,.3),(45.7,.3),(45.7,89.7),(.3,89.7)]
IN2_RAW=[(.3,.3),(45.7,.3),(45.7,89.7),(.3,89.7),(.3,61.8),(21.7,61.8),(21.7,82),(24,82),
         (24,61.8),(29.7,61.8),(29.7,82),(34.8,82),(34.8,61.8),(40.7,61.8),(40.7,63.3),(44,63.3),
         (44,4.4),(24.2,4.4),(24.2,7),(18,7),(18,10.5),(9,10.5),(9,7),(.3,7)]
IN2_PORT=[(24.5,4.7),(43.7,4.7),(43.7,63.0),(41,63.0),(41,7),(28,7),(28,15.5),(24.5,15.5)]
IN2_4V8=[(28.3,7.3),(40.7,7.3),(40.7,38),(31.5,38),(31.5,32.5),(28.3,32.5)]
IN2_3V3=[(.3,7.3),(8.7,7.3),(8.7,10.8),(18.3,10.8),(18.3,7.3),(24.2,7.3),(24.2,15.8),(28,15.8),
         (28,32.8),(31.2,32.8),(31.2,38.3),(40.7,38.3),(40.7,61.5),(34.5,61.5),(34.5,81.7),(30,81.7),(30,61.5),
         (23.7,61.5),(23.7,81.7),(22,81.7),(22,61.5),(.3,61.5)]
IN2_GND_CH1=[(.3,51.8),(8.65,51.8),(8.65,53.55),(9.75,53.55),(9.75,51.3),(18.55,51.3),
             (18.55,53.4),(18,53.4),(18,56.45),(17.45,56.45),(17.45,61.35),(20.4,61.35),(22.75,59.0),(24,59.0),(24,60.1),(21.1,62.3),(16.5,62.3),(16.5,66.1),(.3,66.1)]
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
    t('BAT_IN','F',BAT,[p('D8.1'),(12.525,75.825),p('C80.1'),p('C96.1'),p('C89.1'),p('C95.1')])
    t('BAT_IN','B',BAT,[p('J1.1'),(13.0,74.1),p('Q120.9')])
    feed=(17.5,87.3)
    t('BAT_IN','F',BAT,[p('C95.1'),(14.116,88.891),(17.5,88.891),feed]);v('BAT_IN',feed,size=(1.,.5))
    t('BAT_IN','B',BAT,[feed,(19.4,85.4)])
    t('BAT_IN','B',BYPASS_W,[(19.4,85.4),p('C88.1'),(18.25,84.37),(18.25,83.4)])
    t('BAT_IN','B',PAD_W,[(18.25,83.4),p('U9.5')])
    t('BAT_IN','B',W,[feed,(15.5,87.3),p('R82.1')])
    t('BAT_IN','B',W,[p('R82.1'),(13.925,83.9),p('R167.1')])
    t('BAT_IN','F',S,[p('D8.1'),(10.2,71.85),(10.2,70.2),(12.825,70.2),p('R80.1')])
    t('BAT_IN','F',W,[p('C89.1'),(11.625,83.8),p('TP80.1')])
    t('BAT_DAMP','F',W,[p('C95.2'),p('C89.2'),(18.6,84.7),p('R166.1')])
    t('GND','F',W,[p('R166.2'),(29,86.3)]);v('GND',(29,86.3))


def control(d):
    t,p,v=d.track,d.pad,d.via
    t('BAT_SW_SOURCE','B',S,[p('J400.1'),(10.8,64.1),(10.8,69.2)]);v('BAT_SW_SOURCE',(10.8,69.2))
    t('BAT_SW_SOURCE','F',S,[(10.8,69.2),p('R80.2')])
    t('BAT_SW_RETURN','F',S,[p('J400.2'),(11.575,67.6),p('R165.1')])
    t('BAT_ENABLE','F',S,[p('R165.2'),(16.3,67.0),(16.3,66.0),(19.675,66.0),p('R81.1')])
    t('BAT_ENABLE','F',S,[(16.3,66.0),p('C87.1')])
    t('BAT_ENABLE','F',S,[(19.675,66.0),(19.675,66.4)]);v('BAT_ENABLE',(19.675,66.4))
    t('BAT_ENABLE','B',S,[(19.675,66.4),(21,66.4),(21,68.6),(21.3,68.9)]);v('BAT_ENABLE',(21.3,68.9))
    t('BAT_ENABLE','F',S,[(21.3,68.9),(21.3,71.5),(22.6,72.8),(22.6,79.5),(22.1,80),(19.9,80),(17.1,82.8)])
    v('BAT_ENABLE',(17.1,82.8));t('BAT_ENABLE','B',S,[(17.1,82.8),p('U9.1')])



def efuse(d):
    t,p,v=d.track,d.pad,d.via;rp='RAW_PROTECTED'
    t(rp,'B',PAD_W,[p('U9.6'),(18.75,79.8)])
    t(rp,'B',BYPASS_W,[(18.75,79.8),(19.3,79.25),p('C82.1')])
    # D9 remains beside OUT; its cathode faces north, and its return shares the input-capacitor ground via.
    t(rp,'B',BYPASS_W,[(18.75,79.8),(16.25,77.3),p('D9.1')])
    t(rp,'B',BYPASS_W,[p('C82.1'),(20.3,78.25),(20.3,79.1)])
    for at in ((20.3,79.1),(21.1,79.1)):v(rp,at)
    t(rp,'B',W,[(20.3,79.1),(21.1,79.1)])
    t('GND','B',W,[p('C82.2'),(20.45,76.4),(20.85,76.4)]);v('GND',(20.85,76.4))
    t('GND','B',W,[p('D9.2'),(16.4,79.9),(17.2,79.9)]);v('GND',(17.2,79.9))
    t('GND','F',W,[p('C96.2'),p('C80.2'),(15.875,79.9),(17.2,79.9)])
    t('BAT_ILIM','B',S,[p('U9.9'),p('R84.1')])
    t('BAT_DVDT','B',S,[p('U9.7'),(19.85,80.1),p('C81.1')])
    t('BAT_OVLO','B',S,[p('U9.2'),(16.9,81.825),(16.4,82.325),(16.4,83.0)])
    t('BAT_OVLO','B',S,[p('R83.1'),(12.025,83.0),(16.4,83.0),(16.4,83.15),p('R82.2')])
    t('GND','B',S,[p('U9.8'),(19.825,81.375),(20.2,81.0)]);v('GND',(20.2,81.0))
    t('GND','B',P,[p('C88.2'),(20.9,83.53)]);v('GND',(20.9,83.53))
    for layer,pad in [('B','U11.2'),('F','C97.1')]:t(rp,layer,P,[p(pad),(24.3,66.0)])
    v(rp,(24.3,66.0))
    t(rp,'B',W,[p('TP81.1'),(31.0,83.6)]);v(rp,(31.0,83.6))
    t(rp,'F',W,[p('R92.1'),(30.175,86.5)]);v(rp,(30.175,86.5))


P=.3

def port_supply(d):
    t,p,v=d.track,d.pad,d.via;rp='RAW_PROTECTED'
    # Maker-derived buck loop, unchanged in its local frame.
    t(rp,'F',W,[p('C400.1'),p('U400.2'),p('U400.3'),(15.8,9.0)])
    t(rp,'F',W,[p('C400.1'),(14.1,7.6),(14.1,9.0),p('C401.1')])
    for at in ((14.1,7.6),(14.1,9.0)):v(rp,at)
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
    t('PORT_5V3','B',W,[p('C405.1'),(25.9,12.6),p('U401.10')])
    t('PORT_5V3','B',.25,[p('U401.10'),p('U401.9')])
    t('PORT_5V3','B',S,[p('U401.7'),(25.65,14.1),(25.65,14.9)]);v('PORT_5V3',(25.65,14.9))
    d.link('PORT_LDO_SS','B',S,'U401.8','C408.1')
    for at in ((27.3,13.6),(27.9,13.6)):v('GND',at,filled=True,capped=True)
    d.link('PORT_4V8','B',.25,'U401.1','U401.2')
    t('PORT_4V8','B',W,[p('U401.1'),(29.75,12.6)]);v('PORT_4V8',(29.75,12.6))
    t('PORT_LDO_FB','B',S,[p('U401.3'),(29.75,13.6)]);v('PORT_LDO_FB',(29.75,13.6))
    t('PORT_4V8','F',W,[(29.75,12.6),p('R402.1')])
    t('PORT_LDO_FB','F',S,[(29.75,13.6),(32.225,13.6)])
    t('PORT_LDO_FB','F',S,[p('R402.2'),(32.225,13.6),p('R403.1')])
    t('PORT_4V8','B',W,[p('C406.1'),(28.4,10.2),(29.75,11.55),(29.75,12.6)])
    t('PORT_4V8','F',W,[p('C407.1'),(31.1,20.3),(30.3,20.3)]);v('PORT_4V8',(30.3,20.3))
    t('PORT_4V8','B',S,[p('R405.1'),(33.725,16.35),(33.725,17.3)])
    # Identical always-on port bypass cells and direct terminal feeds.
    for cap,small,jack in [('C411','C410','J410'),('C421','C420','J420')]:
        a=p(cap+'.1');t('PORT_4V8','B',W,[a,p(jack+'.1')])
        at=(a[0],a[1]-1.5);t('PORT_4V8','B',W,[a,at]);v('PORT_4V8',at)
        a=p(small+'.1');at=(a[0],a[1]-.9);t('PORT_4V8','B',W,[a,at]);v('PORT_4V8',at)
    # Camera input bypass is local to IN; the quiet rail arrives along the bottom of the cell.
    t('PORT_5V3','B',W,[p('U402.1'),(30.7,61.025),p('C430.1'),(42.0,61.8)])
    v('PORT_5V3',(42.0,61.8))
    t('CAM_5V','B',W,[p('U402.6'),(34.55,61.2),(38.0,61.2),(38.0,57.2),p('C431.1')])
    t('CAM_5V','B',W,[p('C431.1'),(34.1,53.3),(34.1,50.575),p('C91.1')]
    )
    t('CAM_5V','B',W,[p('C91.1'),(34.15,49.325),(34.15,48.75),p('U13.1')])
    t('CAM_5V','B',W,[p('C431.1'),(36.75,55.0),p('J9.1')])
    t('CAM_ILIM','B',S,[p('U402.5'),(34.175,59.0),p('R430.1')])


def logic(d):
    t,p,v=d.track,d.pad,d.via
    # Mux, input capacitors and 3V3 buck retain their maker-derived relative geometry.
    t('VLOGIC','B',W,[p('U11.8'),p('U11.1'),p('C99.1'),p('U2.2'),p('U2.3'),(27.75,68.6),(29.8,68.6)])
    t('VLOGIC','B',W,[(29.8,68.6),(29.8,70.0),(29.8,72.8),p('C7.1')])
    t('VLOGIC','B',W,[(29.8,72.8),(29.8,81.75),(29.5,82.05)]);v('VLOGIC',(29.5,82.05))
    t('VLOGIC','F',W,[(29.5,82.05),(29.2,81.75),p('C84.1')])
    # Probe and divider share a direct trunk above the mux, kept out of the switch node.
    t('VLOGIC','B',W,[(29.8,81.75),(34.25,81.75),p('TP83.1')])
    t('VLOGIC','B',S,[(29.8,68.6),(29.8,64),(33.5,64),(34.5,63)])
    v('VLOGIC',(34.5,63));t('VLOGIC','F',S,[(34.5,63),(34.5,58.87),p('R60.1')])
    d.link('LOGIC_ILIM','B',S,'U11.10','R86.1')
    t('LOGIC_SS','B',S,[p('U11.11'),(26.15,64.75),p('C85.1')])
    t('USB_OVLO','B',S,[p('R87.2'),(22.5,64.25),p('U11.5')]);t('USB_OVLO','B',S,[p('R87.2'),p('R88.1')])
    d.link('SW_NODE','B',W,'U2.5','L1.1')
    t('SW_NODE','B',W,[(24.4,72.5),(21.78,72.5),p('C5.1')])
    t('BST','B',.25,[p('U2.6'),(23.05,71.0),p('C5.2')])
    t('3V3','B',W,[p('U2.1'),(23.2,68.6)]);v('3V3',(23.2,68.6))
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


def draw(d):
    planes(d);battery(d);control(d);efuse(d);port_supply(d);logic(d);joins(d)
    from r10_route_usb import power_feed
    power_feed(d)
