"""R10 CH1, the independent load switch and repeated ADC cells (D-AVA-01).

Explicit octilinear routes. Fire paths stay on the outer layers, with no series via;
C126/R128/R126 and the passive cold screen retain their electrical functions.
"""
S, P, FIRE = .2, .3, .5


def draw(d):
    t,p,v=d.track,d.pad,d.via
    # West igniter cell; the source return and gate network retain their local geometry.
    t('RAW_ACT','B',FIRE,[p('Q121.8'),(17.58,64.0),p('R134.2')])
    # D-R18-05 (R18-SAF-04): the IGN diagonal moves 0.5 mm south-west, >= 0.5 mm from R131.1 (PYRO1_OUT).
    t('PYRO1_IGN','B',FIRE,[p('J121.2'),(7.4,59.9),(11.5,64.0),p('R134.1')])
    t('PYRO1_OUT','F',FIRE,[p('J121.1'),(10.63,54.1),(11.63,55.1),p('Q124.5')])
    t('GND','F',P,[p('Q124.3'),p('Q124.1')])
    for n in ('2','1'):
        a=p('Q124.'+n);t('GND','F',P,[a,(15.85,a[1])]);v('GND',(15.85,a[1]))
    v('PYRO1_OUT',(11.63,55.1));v('GND',(10.3,55.6))
    t('PYRO1_OUT','B',S,[(11.63,55.1),(10.37,56.36),(10.37,56.6),(10.37,57.5),p('R131.1')])
    t('PYRO1_OUT','B',S,[(10.37,57.5),p('C128.1')])
    # D-R18-05 (R18-SAF-04): R173 sits at the OUT end, so no PYRO1_OUT copper runs between R134.2 (RAW_ACT) and the
    # buzzer FET; the PYRO1_CONT_MID node behind R173's 5.1k takes that corridor (r10_route_signals.buzzer draws it
    # after the buzzer gate lead and BUZZ_OUT via that bound it).
    t('PYRO1_OUT','B',S,[(10.37,56.6),(15.5,56.6),(16.87,57.97),p('R173.1')])
    d.link('PYRO1_COLD','B',S,'R131.2','D120.1')
    t('3V3','B',S,[p('D120.3'),(15.7,61.6)]);v('3V3',(15.7,61.6))
    d.link('PYRO1_GATE_N','F',S,'U1.3','R126.1')
    d.link('PYRO1_GATE_N','F',S,'R126.1','R127.1')
    t('PYRO1_GATE','B',P,[p('TP122.1'),(14.4,53.3)])
    v('PYRO1_GATE',(14.4,53.3));v('GND',(15.35,52.15))
    t('PYRO1_GATE','F',P,[(14.4,53.3),(15.06,53.3),p('R126.2')])
    t('PYRO1_GATE','F',P,[p('R126.2'),(16.0,55.395)])
    t('PYRO1_GATE','F',P,[(16.0,55.395),(15.3,55.395),p('Q124.4')])
    t('PYRO1_GATE','F',P,[(16.0,55.395),(16.0,56.125),p('C126.1')])
    d.link('PYRO1_GATE','F',P,'C126.1','R128.1')
    t('GND','F',P,[p('R128.2'),(17.76,58.375),p('C126.2')])
    # Two identical five-part cells: the filtered end faces the ADC, the high-side end faces the firing circuit.
    for net,mid,refs,x in [('PYRO1_CONT','PYRO1_CONT_MID',('R173','R129','R130','R178','C127'),23.0),
                          ('ARM1_SENSE','ARM1_SENSE_MID',('R132','R175','R133','R180','C129'),28.0)]:
        a,b,c,e,f=refs
        if a != 'R173':                 # CH1's MID run: r10_route_signals.buzzer (D-R18-05)
            d.link(mid,'B',S,a+'.2',b+'.1')
        tail = [(27.55,52.8),p(f+'.1')] if f == 'C129' else [(x,p(f+'.1')[1]+.05),p(f+'.1')]
        t(net,'B',S,[p(b+'.2'),p(c+'.1'),p(e+'.1'),*tail])
        ground_tail = [(x+.86,p(f+'.2')[1]+.49)] if f == 'C127' else [(x+.86,p(f+'.2')[1])]
        t('GND','B',P,[p(c+'.2'),p(e+'.2'),*ground_tail,p(f+'.2')])
        at=(30.15,52.0) if f == 'C129' else (p(f+'.2')[0]+.8,p(f+'.2')[1]+.8)
        knee=[(29.35,52.0)] if f == 'C129' else []
        t('GND','B',P,[p(f+'.2'),*knee,at]);v('GND',at)
    t('PYRO1_CONT','B',S,[p('C127.1'),(24.0,52.15)])
    v('PYRO1_CONT',(24.0,52.15))
    t('PYRO1_CONT','F',S,[(24.0,52.15),p('U1.15')])
    # D-R24-17: the sense tap leaves R134.2's 2512 land on its own line (y 63.875, inside the land), so the chamfered corner
    # at (22.8, 63.875) makes no staircase with a 0.177 mm step.
    t('RAW_ACT','B',S,[(19.075,63.875),(22.8,63.875),(22.8,61.4),(26.17,58.03),p('R132.1')])
    t('ARM1_SENSE','B',S,[p('C129.1'),(29.75,49.4),(29.75,45.5),(29.2,45.5)])
    v('ARM1_SENSE',(29.2,45.5))
    t('ARM1_SENSE','F',S,[(29.2,45.5),p('U1.33')])
    # Facing DFN sources, 0.4 mm qualified pin bridges; the common branch passes through the slew capacitor.
    t('ACT_FET_S','B',.4,[p('Q120.1'),(12.525,71.1),(14.475,71.1),p('Q121.1')])
    for q in ('Q120','Q121'):
        for n in ('2','3'):
            a=p(q+'.'+n);t('ACT_FET_S','B',.4,[a,(a[0],71.1)])
    t('ACT_FET_S','B',P,[(14.475,71.1),(16.45,71.1),p('C120.1'),(17.52,72.17),p('R120.1')])
    t('ACT_GATE','B',P,[p('Q120.4'),(15.2625,72.9875),(15.575,73.3),(16.2,73.3),p('C120.2'),(18.23,73.3),p('R120.2')])
    v('ACT_GATE',(16.2,73.3))
    # D-R24-02 (R23-SAFETY-05, D-R23-02): each FET's gate drive gets a second barrel. Q120's sits between the parallel
    # F.Cu and B.Cu diagonals (0.44 mm apart) on two stubs inside its own pad, so either barrel alone joins R121 to
    # Q120.4; the gate networks themselves stay local on via-free bottom copper.
    v('ACT_GATE',(15.4,72.85))
    t('ACT_GATE','B',P,[(15.4,72.85),(15.2625,72.9875)])
    t('ACT_GATE','F',P,[(15.4,72.85),(15.575,72.675)])
    # D-R18-02 (R18-SAF-02): Q121's gate keeps its own 100k (R119) to the source bridge on via-free bottom copper, so
    # an open in either ACT_GATE layer change leaves both P-FETs biased off; the island's single via now sits below
    # R119. D-R19-03 (R19-SAF-03): the bare probe pad TP121 and its stub are removed; probe ACT_GATE at R119.1 or R120.2.
    t('ACT_GATE','B',P,[p('Q121.4'),(11.14,70.0),p('R119.1'),(11.14,71.7)]);v('ACT_GATE',(11.14,71.7))
    # D-R24-02: Q121's second barrel at the F.Cu run's corner, joined to the first by a B.Cu diagonal under the F.Cu one.
    t('ACT_GATE','B',P,[(11.14,71.7),(11.74,72.3)]);v('ACT_GATE',(11.74,72.3))
    t('ACT_FET_S','B',P,[p('R119.2'),(12.525,71.1)])
    t('ACT_GATE','F',P,[(11.14,71.7),(11.74,72.3),p('R121.1'),(15.2,72.3),(15.575,72.675),(16.2,73.3)])
    d.link('ACT_DRV','F',P,'Q122.3','R121.2',((15.8,70.14),))
    # D-R18-03 (R18-SAF-03): >= 0.5 mm edge to BAT_FAULT_N (moved east, r10_route_signals.status) on the run and the
    # turn, and >= 0.5 mm to the buzzer's BUZZ_OUT pad LS120.2 (a 3V3-strong node through the coil); the U11.12 GND via
    # left this corridor (r10_route_power.joins).
    t('ACT_EN_MCU','F',S,[p('U1.16'),(24.5,51.6),(26.62,53.72),(26.62,65.344),(24.764,67.2),(21.77,67.2),p('R122.1')])
    d.link('ACT_EN','F',S,'Q122.1','R122.2',((19.08,70.75),))
    d.link('ACT_EN','F',S,'R122.2','R123.1')
    # D-R19-04 (R19-SAF-06): C123, Q122's gate-source 10 nF, sits straight below the gate pad; its GND pad joins R123.2's
    # fan-out via (r10_fanout.tsv, drawn by the ground family).
    t('ACT_EN','F',S,[p('Q122.1'),p('C123.1')])
    t('GND','F',P,[p('C123.2'),(19.207,71.85),(19.967,71.09)])
    d.link('RAW_ACT','B',.4,'Q121.9','TP120.1')
