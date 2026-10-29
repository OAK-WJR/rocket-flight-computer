"""Explicit R10 port-local copper. Ports use the frozen ports_place.tsv frame.

All corners and layer transitions below are deliberate fixed construction; no path
search or autorouting. Long MCU and common-rail trunks are separate integration
work. The returned boundary pads are listed in INTERFACES for that routing step.
"""
INTERFACES = {
    'GPS': {'rx': 'U411.4', 'tx': 'U411.5', 'oe': 'R442.1', 'en': 'R411.1', 'fault': 'R412.1', 'supply': 'U410.1'},
    'RADIO': {'rx': 'U421.4', 'tx': 'U421.5', 'oe': 'R452.1', 'en': 'R421.1', 'fault': 'R422.1', 'supply': 'U420.1'},
    'CAM': {'rx': 'U12.4', 'tx': 'U12.5', 'oe': 'R102.1', 'en': 'R431.1', 'fault': 'R432.1', 'supply': 'U402.1'},
}


def draw(d):
    for prefix, base, y in [('GPS', 410, 14.0), ('RADIO', 420, 26.0)]:
        port(d, prefix, base, y)
    camera(d)


def path(d, net, layer, width, *points):
    # Remove repeated endpoints where a fixed corner lands directly on a pad.
    pts = []
    for p in points:
        p = tuple(round(v, 4) for v in p)
        if not pts or p != pts[-1]:
            pts.append(p)
    if len(pts) > 1:
        d.track(net, layer, width, pts)


def elbow(d, net, layer, width, start, end, x_first=True):
    """A specified orthogonal corner, used only at the fixed local pad pairs."""
    a, b = d.pad(start, net=net), d.pad(end, net=net)
    corner = (b[0], a[1]) if x_first else (a[0], b[1])
    path(d, net, layer, width, a, corner, b)


def ground(d, ref, pin, layer, via, corner=None):
    a = d.pad(ref, pin, net='GND')
    path(d, 'GND', layer, .25, a, corner or (a[0], via[1]), via)
    d.via('GND', via)


def port(d, prefix, base, y):
    sw, buf, ldo, jack = f'U{base}', f'U{base+1}', f'U{base+2}', f'J{base}'
    rx, tx, oe, bleed = [f'R{base+30+i}' for i in range(4)]
    maincap, incap, outcap, iocap = [f'C{base+30+i}' for i in range(4)]
    n = lambda suffix: prefix + '_' + suffix
    p = lambda x, dy: (x, round(y+dy, 4))
    # Translator and series resistors retain the proven R9 camera pin geometry.
    d.link(n('RX_BUFFER'), 'F', .2, f'{buf}.1', f'{rx}.2')
    d.link(n('TX_BUFFER'), 'F', .2, f'{buf}.8', f'{tx}.1')
    path(d,n('UART_OE'),'F',.2,d.pad(buf,'6'),p(34.95,4.575),d.pad(oe,'1'))
    # RX crosses the TX corridor on B.Cu, with dedicated reference vias.
    vrx0, vrx1, vesd = p(37.5,-2.6), p(39.9,1.875), p(38.4,2.85)
    path(d,n('RX_WIRE'),'F',.2,d.pad(rx,'1'),vrx0)
    path(d,n('RX_WIRE'),'B',.2,vrx0,p(39.9,-.2),vrx1)
    path(d,n('RX_WIRE'),'F',.2,vrx1,d.pad(jack,'4'))
    for v in (vrx0,vrx1,vesd): d.via(n('RX_WIRE'),v)
    path(d,n('RX_WIRE'),'F',.2,d.pad(f'D{base+1}','1'),p(38.4,2.275),vesd)
    path(d,n('RX_WIRE'),'B',.2,vesd,p(39.375,1.875),vrx1)
    for v in (p(38.25,-2.6),p(39.9,2.7),p(38,1.5)):d.via('GND',v)
    # Board TX reaches pin3, which must cross to the endpoint RX in the harness.
    path(d,n('TX_WIRE'),'F',.2,d.pad(tx,'2'),p(38.5,4.55),p(39.4,3.65),p(39.4,.625),d.pad(jack,'3'))
    path(d,n('TX_WIRE'),'F',.2,d.pad(f'D{base}','1'),p(38.95,.625),p(39.4,.625))
    path(d,'GND','F',.25,d.pad(f'D{base}','2'),p(38.8,-.625))
    d.via('GND',p(38.8,-.625))
    path(d,'GND','F',.25,d.pad(f'D{base+1}','2'),p(38.675,1.5),p(38,1.5))
    # Local main-domain bypass; the via is the common3V3 trunk boundary.
    a=d.pad(maincap,'1');path(d,'3V3','F',.25,a,(34.95,a[1]),d.pad(buf,'3'))
    v3=p(33.2,-2);path(d,'3V3','F',.25,a,v3);d.via('3V3',v3)
    ground(d,buf,'2','F',p(35.9,-.9))
    ground(d,maincap,'2','F',p(35.975,-2.85))
    ground(d,oe,'2','F',p(32.5,7))
    # Separate translator-side3V3 from the switched output, as the camera uses.
    vio=p(35.45,3.75)
    path(d,n('IO_3V3'),'F',.25,d.pad(buf,'7'),vio);d.via(n('IO_3V3'),vio)
    path(d,n('IO_3V3'),'B',.25,vio,p(35.45,4.45),d.pad(iocap,'1'),d.pad(ldo,'5'))
    path(d,n('IO_3V3'),'F',.25,vio,p(35.45,5.75),d.pad(outcap,'1'))
    path(d,n('IO_3V3'),'B',.25,d.pad(ldo,'5'),p(36.3,3.45),p(40.925,3.45),d.pad(bleed,'1'))
    ground(d,iocap,'2','B',p(33.8,2.2))
    ground(d,outcap,'2','F',p(38.1,7.8))
    ground(d,bleed,'2','B',p(42.825,2.2))
    ground(d,ldo,'2','B',p(39.8,5.4),p(39.8,5.4))
    ground(d,incap,'2','B',p(43.625,6.1))
    # Switch output trunk: quiet-regulated power, never a hold-up rail.
    supply=n('4V8'); cout=f'C{base+1}'
    path(d,supply,'B',.4,d.pad(sw,'6'),p(33.35,-1.5),p(36,-1.5),p(38.3,-3.8),d.pad(cout,'1'))
    vp=p(41.8,-1.875); path(d,supply,'F',.4,d.pad(jack,'1'),vp,p(41.8,5.1))
    d.via(supply,vp);d.via(supply,p(41.8,5.1))
    path(d,supply,'B',.4,vp,p(41.8,-3.4),d.pad(cout,'1'))
    path(d,supply,'B',.4,p(41.8,5.1),d.pad(incap,'1'))
    elbow(d,supply,'B',.4,f'{ldo}.1',f'{incap}.1')
    ground(d,cout,'2','B',p(44.4,-2.8))
    ground(d,jack,'2','F',p(40.0,-.625))
    # Load-switch bias, limit and fault. FAULT escapes on F to avoid the ILIM loop.
    en,ilim,fault=n('PWR_EN'),n('ILIM'),n('FAULT_N')
    elbow(d,en,'B',.2,f'{sw}.3',f'R{base+1}.1')
    d.link(ilim,'B',.2,f'{sw}.5',f'R{base}.1')
    vf=p(32.9,-4.45);path(d,fault,'B',.2,d.pad(sw,'4'),vf);d.via(fault,vf);d.via('GND',p(32.9,-3.65))
    if prefix=='GPS':
        ve=p(28.675,-9.6);d.via(fault,ve);d.via('GND',p(27.925,-9.6))
        path(d,fault,'F',.2,vf,p(32.9,-5.375),ve)
        path(d,fault,'B',.2,ve,d.pad(f'R{base+2}','1'))
    else:
        path(d,fault,'F',.2,vf,p(32.9,-5.3),p(28.0,-5.3),p(28.0,-7.825),d.pad(f'R{base+2}','1'))
    for ref,pin,layer,via in [(sw,'2','B',p(28.9,-3.5)),(f'R{base}','2','B',p(35.625,-4.4)),
                               (f'R{base+1}','2','B',p(33.6,-6.3)),(f'C{base}','2','F',p(31.775,-2.7))]:
        ground(d,ref,pin,layer,via)
    vinput=p(30.225,-2.3)
    path(d,'PORT_4V8','F',.4,d.pad(f'C{base}','1'),vinput);d.via('PORT_4V8',vinput)
    path(d,'PORT_4V8','B',.4,vinput,p(29.7,-2.3),d.pad(sw,'1'))
    pull=f'R{base+2}';layer='B' if prefix=='GPS' else 'F';a=d.pad(pull,'2');v=(a[0],a[1]-.9)
    path(d,'3V3',layer,.25,a,v);d.via('3V3',v)


def camera(d):
    """Retained camera translator core; changed supply/ADC trunks remain explicit."""
    d.link('CAM_RX_BUFFER','F',.2,'U12.1','R100.2')
    d.link('CAM_TX_BUFFER','F',.2,'U12.8','R101.1')
    d.link('CAM_UART_OE','F',.2,'U12.6','R102.1')
    # Camera keeps its existing pin3 camera-RX / pin4 camera-TX naming.
    path(d,'CAM_RX_WIRE','F',.2,d.pad('R100.1'),(38.3,36.15),(39.0,36.85),(39.0,38.025),(39.6,38.625),d.pad('J9.3'))
    path(d,'CAM_TX_WIRE','F',.2,d.pad('R101.2'),(38.4,42.55),(39.4,41.55),(39.4,40.275),(39.8,39.875),d.pad('J9.4'))
    elbow(d,'CAM_RX_WIRE','F',.2,'D401.1','J9.3')
    elbow(d,'CAM_TX_WIRE','F',.2,'D400.1','J9.4')
    ground(d,'D401','2','F',(38.8,37.1))
    ground(d,'D400','2','F',(38.8,40.9))
    elbow(d,'3V3','F',.2,'C100.1','U12.3')
    elbow(d,'GND','F',.2,'C100.2','U12.2')
    v3=(33.2,36.6);path(d,'3V3','F',.25,d.pad('C100.1'),v3);d.via('3V3',v3)
    ground(d,'U12','2','F',(35.45,36.9))
    ground(d,'R102','2','F',(34.95,45.1))
    vio=(35.45,41.75);path(d,'CAM_IO_3V3','F',.25,d.pad('U12.7'),vio);d.via('CAM_IO_3V3',vio)
    path(d,'CAM_IO_3V3','B',.25,vio,(35.45,42.45),d.pad('C93.1'),d.pad('U13.5'))
    path(d,'CAM_IO_3V3','B',.25,d.pad('C93.1'),(34.6,42.45),(34.6,46.02),d.pad('C92.1'))
    path(d,'CAM_IO_3V3','B',.25,d.pad('U13.5'),(36.3,41.5),(40.8,41.5),(41.8,42.5),(41.8,46.3),d.pad('R103.1'))
    ground(d,'C93','2','B',(33.8,40.2))
    ground(d,'C92','2','B',(35.45,49.9))
    ground(d,'U13','2','B',(39.2,44.2))
    ground(d,'C91','2','B',(43.625,44.1))
    ground(d,'R103','2','B',(42.625,47.3))
    # Current-limiter below the ports: short buck feed, connector output runs east.
    path(d,'CAM_ILIM','F',.2,d.pad('U402.5'),(39,60),(39,61.925),d.pad('R430.1'))
    path(d,'CAM_PWR_EN','F',.2,d.pad('U402.3'),(35,60.95),(33.175,59.125),d.pad('R431.1'))
    path(d,'CAM_FAULT_N','F',.2,d.pad('U402.4'),(38.8,60.95),(38.8,55.5),(37.8,54.5),d.pad('R432.1'))
    elbow(d,'PORT_5V3','F',.4,'U402.1','C430.1')
    for ref,pin,layer,via in [('U402','2','F',(35,60)),('R430','2','F',(40.8,60.275)),
                              ('R431','2','F',(34.825,55.9)),('C430','2','F',(37.775,57.6))]:
        ground(d,ref,pin,layer,via)
    a=d.pad('R432.2');v=(a[0],a[1]-.9);path(d,'3V3','F',.25,a,v);d.via('3V3',v)
