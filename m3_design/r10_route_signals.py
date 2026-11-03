"""R10 explicit cell and bus wiring (D-AVA-01); no route search.

UARTs use one transition from the top MCU to the bottom port cells. The two
always-on cells share terminal pitch, resistor/clamp placement and routing.
"""
S, IO = .2, .3
PORT_CONTROL_GND = ()


def uarts(d):
    t,p,v=d.track,d.pad,d.via
    # D-R19-14: J410 (GPS by default) moves to USART3 PD8 / PD9 (U1.55 / U1.56): north between C90's vias and RADIO_TX,
    # north-east beside the radio pair, then the former GPS run to the port cell. J440 (AUX) takes USART6 PC6 / PC7 (U1.63 /
    # U1.64), whose pins face the north-west corner: neither port crosses the other or the microSD contacts below.
    t('GPS_RX_MCU','F',S,[p('U1.56'),(26.5,33.6),(27.0,33.1),(27.0,31.4),(28.8,29.6),(28.8,11),(32,11)])
    v('GPS_RX_MCU',(32,11))
    t('GPS_RX_MCU','B',S,[(32,11),(32.425,11),p('R440.2')])
    t('GPS_TX_MCU','F',S,[p('U1.55'),(27.0,34.3),(27.4,33.9),(27.4,31.6),(29.3,29.7),(29.3,16),(33,16),(34,15)])
    v('GPS_TX_MCU',(34,15))
    t('GPS_TX_MCU','B',S,[(34,15),(34,14.575),p('R441.1')])
    t('RADIO_RX_MCU','F',S,[p('U1.51'),(29,32.6),(32,29.6),(32,26.25)])
    t('RADIO_TX_MCU','F',S,[p('U1.52'),(28.5,31.1),(31.2,28.4)])
    v('RADIO_RX_MCU',(32,26.25));v('RADIO_TX_MCU',(31.2,28.4))
    t('RADIO_RX_MCU','B',S,[(32,26.25),p('R450.2')])
    t('RADIO_TX_MCU','B',S,[(31.2,28.4),(31.825,28.4),p('R451.1')])
    for at in ((32.8,11.5),(35,15.1),(31.0,26.25),(30.3,27.8)):v('GND',at)
    # D-R19-14: the AUX pair on F.Cu only (no layer change): north, north-west beside VBUS_SENSE, north to the top cell.
    t('AUX_RX_MCU','F',S,[p('U1.64'),(22.5,29.95),(19.5,26.95),(19.5,20.6),p('R470.2')])
    t('AUX_TX_MCU','F',S,[p('U1.63'),(23.0,29.95),(20.0,26.95),(20.0,18.0),p('R471.1')])


def port_wires(d):
    t,p,v=d.track,d.pad,d.via
    for net,res,dio,jack in [('GPS_RX_WIRE','R440.1','D411','J410.4'),('GPS_TX_WIRE','R441.2','D410','J410.3'),
                            ('RADIO_RX_WIRE','R450.1','D421','J420.4'),('RADIO_TX_WIRE','R451.2','D420','J420.3'),
                            ('CAM_RX_WIRE','R100.1','D401','J9.3'),('CAM_TX_WIRE','R101.2','D400','J9.4')]:
        a=p(res)
        if dio in ('D410','D411'):
            branch=(37.1,a[1])
            t(net,'B',S,[a,branch,p(jack)])
            a=p(dio+'.1')
            t(net,'B',S,[branch,(37.1,a[1]+.575),(36.525,a[1]),a])
        else:
            t(net,'B',S,[a,p(jack)])
            t(net,'B',S,[(p(dio+'.1')[0],a[1]),p(dio+'.1')])
        a=p(dio+'.2')
        if dio in ('D410','D411'):
            at=(36.45,a[1]);t('GND','B',S,[a,at])
        elif dio in ('D400','D401'):
            # Keep both returns west of the three F.Cu camera control/supply lanes.
            at=(34.95,a[1]);t('GND','B',S,[a,at])
        else:
            at=(a[0],a[1]+.7)
            t('GND','B',S,[a,at])
        v('GND',at)
    # D-R19-14: the AUX cell is on the top beside J440 (its pins sit under the terminal body): each wire runs straight
    # west from its resistor to the terminal pin. The RX row sits 0.9 mm north of J440.4, so its wire steps down once, 45
    # degrees. D-R20-09 (R20-RTE-05): the clamps sit on the bottom under J440's body on the wire side, as D410 / D411 sit
    # under J410's (TX between pins 3 and 4, RX beyond pin 4, 3.2 mm from their pins, M-6 1.5 mm): each pin runs west on
    # B.Cu and drops into its clamp, and the clamp's return goes 0.7 mm further west to its own via.
    # D-R26-01 (R26-TRI-09): with the clamps on B.Cu each wire changes layer through its plated pin, and D-R19-15 keeps
    # the port UART nets under the 1.5 mm GND-partner rule, so each pin takes a GND via 1.5 mm north of its centre, on the
    # pin column between the pins: 0.30 mm from its own pad on F.Cu and B.Cu (the pins keep no inner ring, r10_parts),
    # 0.60 mm from its hole on In1, in the F.Cu / B.Cu pours and joined to In1 GND; the In2 3V3 fill clears it.
    for net,res,dio,jack in [('AUX_TX_WIRE','R471.2','D440','J440.3'),('AUX_RX_WIRE','R470.1','D441','J440.4')]:
        a=p(res);j=p(jack);b=p(dio+'.1')
        if a[1]==j[1]:
            t(net,'F',S,[a,j])
        else:
            t(net,'F',S,[a,(12.4,a[1]),(12.4-(j[1]-a[1]),j[1]),j])
        t(net,'B',S,[j,(b[0],j[1]),b])
        v('GND',(j[0],round(j[1]-1.5,4)))
        a=p(dio+'.2');at=(round(a[0]-.7,4),a[1])
        t('GND','B',S,[a,at]);v('GND',at)


def camera_local(d):
    t,p,v=d.track,d.pad,d.via
    t('CAM_RX_BUFFER','B',S,[p('U12.1'),(30.05,42.625),p('R100.2')])
    t('CAM_TX_BUFFER','B',S,[p('U12.8'),(33.15,42.25)])
    t('3V3','B',S,[p('U12.3'),(29.25,39.55),(29.25,38.65)]);v('3V3',(29.25,38.65))
    t('3V3','B',S,[(29.25,39.55),p('C100.1')])
    t('GND','B',S,[p('C100.2'),(28.85,40.95),(28.6,41.2)])
    t('CAM_IO_3V3','B',IO,[p('U13.5'),(31.65,49.85),(31.65,52.5),(31.65,53.525),p('R103.1')])
    t('GND','B',S,[p('R103.2'),(32.575,55.625),(33.2,55.0)])


def camera(d):
    camera_local(d)
    t,p,v=d.track,d.pad,d.via
    t('CAM_MCU_RX','F',S,[p('U1.37'),(32,43.5)]);v('CAM_MCU_RX',(32,43.5))
    t('CAM_MCU_RX','B',S,[(32,43.5),(31.2,42.7),(31.2,39.05),p('U12.4')])
    t('CAM_MCU_TX','F',S,[p('U1.38'),(32.05,43),(32.2,42.85)]);v('CAM_MCU_TX',(32.2,42.85))
    t('CAM_MCU_TX','B',S,[(32.2,42.85),(31.6,42.25),(31.6,39.05),p('U12.5')])
    v('GND',(33.1,43.65))
    t('GND','B',S,[p('U12.2'),(29.27,40.05),(28.85,40.47)])
    # Both joins end within R102.1; avoid needless diagonal tails inside its land.
    t('CAM_UART_OE','B',S,[p('U12.6'),(34.575,39.55)])
    t('CAM_UART_OE','B',S,[p('R102.1'),(34,40.275),(34,42)]);v('CAM_UART_OE',(34,42))
    t('CAM_UART_OE','F',S,[p('U1.39'),(31.75,42.5),(32.25,42),(34,42)])
    t('CAM_IO_3V3','B',S,[p('U12.7'),(32.2,40.05)]);v('CAM_IO_3V3',(32.2,40.05))
    t('GND','F',S,[p('C93.2'),(34.3,38.5)]);v('GND',(34.3,38.5))
    t('CAM_IO_3V3','F',S,[(32.2,40.05),p('C93.1'),(35.8,40.05),(36.55,40.8),(36.55,48.18)])
    v('CAM_IO_3V3',(36.55,48.18))
    t('CAM_IO_3V3','B',S,[(36.55,48.18),(31.12,48.18),p('U13.5')])
    # Parallel control trunks: the higher MCU pin takes the outer lane.
    t('CAM_PWR_EN','F',S,[p('U1.41'),(35.5,41.5),(35.5,57.4),(35.5,58.9),(37.025,60.425),p('R431.1')])
    t('CAM_PWR_EN','F',S,[(35.5,57.4),(34.4,57.4)]);v('CAM_PWR_EN',(34.4,57.4))
    t('CAM_PWR_EN','B',S,[(34.4,57.4),(31.35,57.4),p('U402.3')])
    t('CAM_FAULT_N','F',S,[p('U1.42'),(36,41),(36,56.3),(36.5,56.8)]);v('CAM_FAULT_N',(36.5,56.8))
    # D-R24-17: west to above R432.1 and straight down into it (one bend, chamfered with the rest), not a 0.67 mm drop
    # between two diagonals.
    t('CAM_FAULT_N','B',S,[(36.5,56.8),(35.27,56.8),p('R432.1'),(35.02,58.05),p('U402.4')])
    t('3V3','B',S,[p('R432.2'),(36.13,58.8)]);v('3V3',(36.13,58.8))
    t('CAM_5V_SENSE','F',S,[p('U1.35'),(31.7,44.5),(32.77,45.57),p('R104.2'),p('R105.1'),(32.77,51.0),p('C94.1')])
    t('CAM_5V','F',S,[p('R104.1'),(34.2,47.07),(34.2,49.325)]);v('CAM_5V',(34.2,49.325))
    # Control and ADC trunks are completed after the cell/fast-signal routes.


def servos_local(d):
    t,p,v=d.track,d.pad,d.via
    # Four pull-downs face their clamp pins in two aligned rows.
    for i,pin,res in [(1,1,154),(2,3,155),(3,4,156),(4,6,157)]:
        d.link(f'SERVO{i}_MCU','B',S,f'D121.{pin}',f'R{res}.1')
    # The entries end inside the series lands, clear of the shared GND return.
    t('SERVO1_MCU','B',S,[p('R154.1'),(33.5,74.1),(34,74.6),(34,75.6)])
    t('SERVO2_MCU','B',S,[p('D121.3'),(30.55,71.85),(32.955,71.85),p('R151.1')])
    t('SERVO3_MCU','B',S,[p('D121.4'),(30.55,71.2),(32.905,71.2),p('R152.1')])
    t('SERVO4_MCU','B',S,[p('R157.1'),(32.945,68.83),p('R153.1')])
    t('GND','B',IO,[p('D121.2'),(31.5,73.6)]);v('GND',(31.5,73.6))
    t('3V3','B',IO,[p('D121.5'),(31.5,69.4)]);v('3V3',(31.5,69.4))
    for i in range(1,5):
        a=p(f'R{149+i}.2');b=p(f'J122.{i}');turn=(round(a[0]+abs(b[1]-a[1]),4),b[1])
        # Turn beside the first two resistors for centred terminal entries without in-pad tails.
        if i in (1,2): turn=(round(b[0]-abs(b[1]-a[1]),4),a[1])
        pts=[a,b] if a == turn or turn == b else [a,turn,b]
        t(f'SERVO{i}_OUT','B',S,pts)


def servos(d):
    servos_local(d)
    t,p,v=d.track,d.pad,d.via
    ends=[(33,75.9),(34.325,73.8),(33.675,69.05),(34,66.5)]
    for i,x in enumerate((30.3,30.78,31.26,31.74),1):
        a=p('U1.'+str(21+i));end=ends[i-1];turn=end[1]-(end[0]-x)
        t(f'SERVO{i}_MCU','F',S,[a,(a[0],52),(x,52+x-a[0]),(x,turn),end])
        v(f'SERVO{i}_MCU',end)
    t('SERVO1_MCU','B',S,[(33,75.9),p('R150.1')])
    t('SERVO2_MCU','B',S,[(34.325,73.8),(33.875,73.35),p('R151.1')])
    t('SERVO3_MCU','B',S,[(33.675,69.05),(33.675,70.23)])
    t('SERVO4_MCU','B',S,[(34,66.5),(34,68)])


def status(d):
    t,p,v=d.track,d.pad,d.via
    t('VLOGIC_SENSE','F',S,[p('U1.30'),(32.05,47),(32.05,53.28),p('R61.1'),
                             (32.3,54.47),(32.3,56.6),p('C60.1'),(32.77,57.93),p('R60.2')])
    t('LOGIC_SOURCE_ST','F',S,[p('U1.28'),(31.65,48),(31.65,51.0),(30.85,51.8)])
    v('LOGIC_SOURCE_ST',(30.85,51.8))
    # D-R24-08 (R22-POWER-02): PA4's ST line gets a second barrel south-west of the first, joined to it on both layers.
    v('LOGIC_SOURCE_ST',(30.45,51.4))
    for layer in ('F','B'):
        t('LOGIC_SOURCE_ST',layer,S,[(30.45,51.4),(30.85,51.8)])
    t('LOGIC_SOURCE_ST','B',S,[(30.85,51.8),(30.85,53.1),(29.8,54.15),(29.8,59.125),p('R91.2')])
    t('LOGIC_SOURCE_ST','B',S,[p('R91.2'),(28.925,60.625),p('U11.9')])
    t('BAT_FAULT_N','F',S,[p('U1.29'),(28.2,47.5)]);v('BAT_FAULT_N',(28.2,47.5))
    t('BAT_FAULT_N','B',S,[(28.2,47.5),(28,47.3),(26,47.3),(26,51.55),(26.9,52.45)])
    v('BAT_FAULT_N',(26.9,52.45))
    # D-R18-03 (R18-SAF-03): 0.47 mm east of R17's run, 0.55 mm edge from ACT_EN_MCU; the same 45-degree run to R89.2.
    t('BAT_FAULT_N','F',S,[(26.9,52.45),(27.37,52.92),(27.37,65.655),(23.85,69.175),(23,69.175),p('R89.2')])
    t('BAT_FAULT_N','F',S,[p('R89.2'),(22.175,80.475),(19.3,83.35),(16.55,83.35),(16.55,80.9)])
    v('BAT_FAULT_N',(16.55,80.9))
    t('BAT_FAULT_N','B',S,[(16.55,80.9),p('U9.4')])


def buzzer(d):
    t,p,v=d.track,d.pad,d.via
    t('BUZZ_DRV','F',S,[p('U1.8'),(20.5,51.8),(20.2,52.1)]);v('BUZZ_DRV',(20.2,52.1))
    t('BUZZ_DRV','B',S,[(20.2,52.1),(20.2,56.0),p('R162.1')])
    t('BUZZ_G','B',S,[p('R162.2'),(20.5,58.87),p('R163.1')])
    t('GND','B',S,[p('R163.2'),(22.33,59.73),(22.33,58.25)]);v('GND',(22.33,58.25))
    # D-R18-05: the gate lead west of Q123 moves 0.25 mm east (0.15 mm from Q123.2), >= 0.5 mm from R173's OUT pad.
    t('BUZZ_G','B',S,[(20.5,58.7),(17.75,58.7),(17.75,60.45),p('Q123.1')])
    t('BUZZ_OUT','F',IO,[p('LS120.2'),(24.85,61.02),(24,61.87),p('D123.2')])
    t('BUZZ_OUT','F',IO,[(24,61.87),(23.68,61.55),(19.55,61.55),(19.55,60.85)])
    v('BUZZ_OUT',(19.55,60.85));t('BUZZ_OUT','B',IO,[(19.55,60.85),(20.15,60.85),(20.5,60.5),p('Q123.3')])
    # D-R18-05 (R18-SAF-04): CH1's 5.1k-isolated PYRO1_CONT_MID run south of Q123, bounded by the gate lead and the
    # BUZZ_OUT via above (drawn after them, so the per-family gate judges it against the copper that shapes it).
    # D-R26-02: R173 sits 0.65 mm further north, so the run turns 45 degrees at (16.87, 60.82) instead of a chamfered
    # 90 at (16.87, 61.8): 10.58 mm against a 6.81 mm octilinear distance (1.55 x; straight down it would be 11.15 mm,
    # 1.64 x, a detour). D-R26-04: the diagonal's ends sit 0.05 mm further south and west than first drawn, so it is
    # 0.2005 mm from Q123.1 (BUZZ_G) (0.165 mm from (16.87, 60.77)) and the run's 0.175 mm stays the pair's minimum.
    t('PYRO1_CONT_MID','B',S,[p('R173.2'),(16.87,60.82),(17.85,61.8),(20.83,61.8),(23.0,59.63),p('R129.1')])
    t('3V3','F',IO,[p('LS120.1'),(18.8,60.25),(18.8,61.9),(19.9,63),p('D123.1')])
    v('3V3',(18.8,60.25))
    t('3V3','F',IO,[(18.8,60.25),(17.05,60.25),(15.7,61.6)])


def leds(d):
    """Local status cell clears the SPI3/SWD escapes and retained IMU supply vias."""
    t, p = d.track, d.pad
    t('LED_RED', 'F', S, [p('U1.86'), (13.7, 42.0), p('R32.1')])
    t('LED_RED_A', 'F', S, [p('R32.2'), (10.3, 42.6), p('LED1.2')])
    t('LED_YEL', 'F', S, [p('U1.88'), (14.4, 43.0), (14.4, 43.7),
                         (13.5, 44.6), p('R33.1')])
    t('LED_YEL_A', 'F', S, [p('R33.2'), (9.9, 45.0), p('LED2.1')])
    # Reuse the existing C32 GND via; it is already connected to the solid In1 plane.
    t('GND', 'F', S, [p('LED1.1'), (8.1, 44.18), (8.72, 44.8)])
    t('GND', 'F', S, [p('LED2.2'), (6.5, 46.5)])
    d.via('GND', (6.5, 46.5))



def draw(d):
    import r10_route_sd
    r10_route_sd.draw(d)
    # D-R18-01 (R18-REQ-08): the V3V3_SENSE divider (R62/R63) and its PC3_C escape are removed.
    uarts(d);port_wires(d);camera(d);servos(d);status(d);leds(d);buzzer(d)
