"""Status indicators, pull-pin and supply sensing; explicit R10 polylines."""
import r9_route_status as old
from r10_route import CORE_SHIFT, Translated


def draw(d):
    core = Translated(d, CORE_SHIFT)
    buz = Translated(d, (-9, -8))
    for net, layer, width, pts in old.TRACKS:
        if net.startswith('LED') or (net == 'GND' and pts[0] in ((5.2, 45.1), (7.8, 47.0))):
            core.track(net, layer, width, pts)
        elif net in ('BUZZ_DRV', 'PULLPIN', 'VLOGIC_SENSE') and layer == 'F':
            core.track(net, layer, width, pts)
        elif net in ('BUZZ_G', 'BUZZ_OUT') or (net == '3V3' and pts[0] == old.V3['BUZ']) or (net == 'GND' and pts[0] == (26.6, 23.9)):
            buz.track(net, layer, width, pts)
        elif net == 'V3V3_SENSE' or (net == '3V3' and pts[0] == (16.1, 54.5)) or (net == 'GND' and pts[0] == (16.28, 55.3)):
            core.track(net, layer, width, pts)
    for net, at in old.SIGNAL_VIAS:
        (buz if net == 'BUZZ_OUT' else core).via(net, at)
    core.via('GND', old.G['LED1'])
    buz.via('GND', old.G['BUZ'])
    buz.via('3V3', old.V3['BUZ'])

    d.track('BUZZ_DRV', 'B', .2, [(22.3, 41.5), (23.86, 39.94), (29.75, 39.94),
                                  (30.1, 39.59), (30.1, 25), (23.25, 18.15), d.pad('R162.1')])
    d.track('PULLPIN', 'B', .2, [(21.85, 43.1), (22.48, 42.47), (31.5, 42.47),
                                (31.5, 31), (18, 17.5), (11.5, 17.5), d.pad('D122.3')])
    d.link('PULLPIN', 'B', .2, 'D122.3', 'C160.1', ((11, 14.58),))
    d.link('PULLPIN', 'B', .2, 'C160.1', 'R160.2')
    d.link('PULLPIN', 'B', .2, 'R160.2', 'R161.2', ((12.57, 12),))
    d.track('PULLPIN_EXT', 'F', .2, [d.pad('J123.1'), (11.375, 9.6)])
    d.via('PULLPIN_EXT', (11.375, 9.6))
    d.track('PULLPIN_EXT', 'B', .2, [(11.375, 9.6), (12, 10.225), d.pad('R160.1')])
    for ref, net, at in [('R161.1', '3V3', (15.2, 12)), ('D122.2', '3V3', (13.8, 18.75)),
                         ('D122.1', 'GND', (13.8, 15.25)), ('C160.2', 'GND', (12, 15.2))]:
        d.track(net, 'B', .2, [d.pad(ref), at]); d.via(net, at)
    d.track('GND', 'F', .2, [d.pad('J123.2'), (13.3, 9.625)])
    d.via('GND', (13.3, 9.625))

    d.track('VLOGIC_SENSE', 'B', .2, [(26, 44.1), (26.775, 44.875), (29.8, 44.875),
                                     (30.3, 45.375), (30.3, 50.3), (29, 51.6), d.pad('R61.1')])
    d.link('VLOGIC_SENSE', 'B', .2, 'R61.1', 'C60.1')
    d.link('VLOGIC_SENSE', 'B', .2, 'C60.1', 'R60.2')
    d.link('GND', 'B', .2, 'R61.2', 'C60.2', ((29.54, 55.5),))
    d.track('GND', 'B', .2, [d.pad('C60.2'), (31.3, 55.5)])
    d.via('GND', (31.3, 55.5))
