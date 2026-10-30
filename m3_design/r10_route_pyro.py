"""R10 CH1, the independent load switch and repeated ADC cells (D-AVA-01).

Explicit octilinear routes. Fire paths stay on the outer layers, with no series via;
C126/R128/R126 and the passive cold screen retain their electrical functions.
"""
S, P, FIRE = .2, .3, .5


def draw(d):
    t,p,v=d.track,d.pad,d.via
    # West igniter cell; the source return and gate network retain their local geometry.
    t('RAW_ACT','B',FIRE,[p('Q121.8'),(17.58,64.0),p('R134.2')])
    t('PYRO1_IGN','B',FIRE,[p('J121.2'),(7.4,59.4),(12.0,64.0),p('R134.1')])
    t('PYRO1_OUT','F',FIRE,[p('J121.1'),(10.63,54.1),(11.63,55.1),p('Q124.5')])
    t('GND','F',P,[p('Q124.3'),p('Q124.1')])
    for n in ('2','1'):
        a=p('Q124.'+n);t('GND','F',P,[a,(15.85,a[1])]);v('GND',(15.85,a[1]))
    v('PYRO1_OUT',(11.63,55.1));v('GND',(10.3,55.6))
    t('PYRO1_OUT','B',S,[(11.63,55.1),(10.37,56.36),(10.37,56.6),(10.37,57.5),p('R131.1')])
    t('PYRO1_OUT','B',S,[(10.37,57.5),p('C128.1')])
    t('PYRO1_OUT','B',S,[(10.37,56.6),(15.5,56.6),(17,58.1),(17,61.8),(20.83,61.8),p('R173.1')])
    d.link('PYRO1_COLD','B',S,'R131.2','D120.1')
    t('3V3','B',S,[p('D120.3'),(15.7,61.6)]);v('3V3',(15.7,61.6))
    d.link('PYRO1_GATE_N','F',S,'U1.3','R126.1')
    d.link('PYRO1_GATE_N','F',S,'R126.1','R127.1')
    t('PYRO1_GATE','B',P,[p('TP122.1'),(14.4,53.3)])
    v('PYRO1_GATE',(14.4,53.3));v('GND',(15.35,52.15))
    t('PYRO1_GATE','F',P,[(14.4,53.3),(16.0,53.3),p('R126.2')])
    t('PYRO1_GATE','F',P,[p('R126.2'),(16.0,55.395)])
    t('PYRO1_GATE','F',P,[(16.0,55.395),(15.3,55.395),p('Q124.4')])
    t('PYRO1_GATE','F',P,[(16.0,55.395),(16.0,56.125),p('C126.1')])
    d.link('PYRO1_GATE','F',P,'C126.1','R128.1')
    t('GND','F',P,[p('R128.2'),(17.76,58.375),p('C126.2')])
    # Two identical five-part cells: the filtered end faces the ADC, the high-side end faces the firing circuit.
    for net,mid,refs,x in [('PYRO1_CONT','PYRO1_CONT_MID',('R173','R129','R130','R178','C127'),23.0),
                          ('ARM1_SENSE','ARM1_SENSE_MID',('R132','R175','R133','R180','C129'),28.0)]:
        a,b,c,e,f=refs
        d.link(mid,'B',S,a+'.2',b+'.1')
        tail = [(27.55,52.8),p(f+'.1')] if f == 'C129' else [(x,p(f+'.1')[1]+.05),p(f+'.1')]
        t(net,'B',S,[p(b+'.2'),p(c+'.1'),p(e+'.1'),*tail])
        t('GND','B',P,[p(c+'.2'),p(e+'.2'),(x+.86,p(f+'.2')[1]),p(f+'.2')])
        at=(30.15,52.0) if f == 'C129' else (p(f+'.2')[0]+.8,p(f+'.2')[1]+.8)
        knee=[(29.35,52.0)] if f == 'C129' else []
        t('GND','B',P,[p(f+'.2'),*knee,at]);v('GND',at)
    t('PYRO1_CONT','B',S,[p('C127.1'),(24.0,52.15)])
    v('PYRO1_CONT',(24.0,52.15))
    t('PYRO1_CONT','F',S,[(24.0,52.15),p('U1.15')])
    t('RAW_ACT','B',S,[p('R134.2'),(19.2,63.875),(22.8,63.875),(22.8,61.4),(26.17,58.03),p('R132.1')])
    t('ARM1_SENSE','B',S,[p('C129.1'),(29.75,49.4),(29.75,45.5),(29.2,45.5)])
    v('ARM1_SENSE',(29.2,45.5))
    t('ARM1_SENSE','F',S,[(29.2,45.5),p('U1.33')])
    # Facing DFN sources, 0.4 mm qualified pin bridges; the common branch passes through the slew capacitor.
    t('ACT_FET_S','B',.4,[p('Q120.1'),(12.525,71.1),(14.475,71.1),p('Q121.1')])
    for q in ('Q120','Q121'):
        for n in ('2','3'):
            a=p(q+'.'+n);t('ACT_FET_S','B',.4,[a,(a[0],71.1)])
    t('ACT_FET_S','B',P,[(14.475,71.1),(16.45,71.1),p('C120.1'),(17.52,72.17),p('R120.1')])
    t('ACT_GATE','B',P,[p('Q120.4'),(15.575,73.3),(16.2,73.3),p('C120.2'),(18.23,73.3),p('R120.2')])
    v('ACT_GATE',(16.2,73.3))
    t('ACT_GATE','B',P,[p('Q121.4'),(11.8,70.725)]);v('ACT_GATE',(11.8,70.725))
    t('ACT_GATE','F',P,[(11.8,70.725),(11.8,71.4),(12.7,72.3),p('R121.1'),(15.2,72.3),(16.2,73.3)])
    t('ACT_GATE','B',P,[(11.8,70.725),(11.025,71.5),p('TP121.1')])
    d.link('ACT_DRV','F',P,'Q122.3','R121.2',((15.8,70.14),))
    t('ACT_EN_MCU','F',S,[p('U1.16'),(24.5,51.6),(26.5,53.6),(26.5,66.0),(25.3,67.2),(21.0,67.2),(19.6,68.6),p('R122.1')])
    d.link('ACT_EN','F',S,'Q122.1','R122.2',((19.08,70.75),))
    d.link('ACT_EN','F',S,'R122.2','R123.1')
    d.link('RAW_ACT','B',.4,'Q121.9','TP120.1')
