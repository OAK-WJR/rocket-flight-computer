"""USB local circuit retained rigidly; direct data and SWD leads to central MCU."""
import r9_route_usb_swd as old
from r10_route import CORE_SHIFT, Translated

USB_SHIFT = (0.0, -3.5)


def draw(d):
    local = Translated(d, USB_SHIFT)
    core = Translated(d, CORE_SHIFT)
    for ref, num, net, at in old.PADS:
        if ref not in ('U1', 'J2', 'C24'):
            local.pad(ref, num, net, at)
    nrst_count = 0
    for index, (net, layer, width, pts) in enumerate(old.TRACKS):
        if net in ('CC1', 'CC2', 'VBUS', 'USB_ILIM') or index < 6:
            local.track(net, layer, width, pts)
        elif net == 'VBUS_SENSE' and not (layer == 'F' and pts[0] == old.V_SENSE2):
            local.track(net, layer, width, pts)
        elif net == 'USB_FAULT_N' and layer == 'B' and pts[0] != old.V_FAULT:
            local.track(net, layer, width, pts)
        elif net == 'NRST':
            if nrst_count < 3:
                core.track(net, layer, width, pts)
            nrst_count += 1
        elif net == '3V3' and layer == 'B' or net == 'GND' and pts[-1] == old.G_D4:
            local.track(net, layer, width, pts)

    d.track('USB_DM', 'F', .2, [d.pad('D4.6'), (15.85, 29.65), (19.5, 33.3), d.pad('U1.70')])
    d.track('USB_DP', 'F', .2, [d.pad('D4.4'), (16.75, 31.55), (19, 33.8), d.pad('U1.71')])
    d.track('VBUS_SENSE', 'F', .2, [(16.6, 29.8), (17.7, 29.8), (22, 34.1), d.pad('U1.65')])
    d.track('USB_FAULT_N', 'F', .2, [d.pad('U1.87'), (16.75, 42.5), (16.75, 39.05)])
    d.track('USB_FAULT_N', 'B', .2, [(16.75, 39.05), (16.2, 38.5), (11.2, 38.5),
                                    (11.2, 32.5), (12.6, 31.1), (12.6, 26.55), (13.9, 26.55)])
    d.track('SWDIO', 'F', .2, [d.pad('U1.72'), (18.5, 34.1), (18.25, 33.85),
                             (12, 33.85), (8.15, 37.7), (3.73, 37.7), (3.73, 38.45)])
    d.track('SWCLK', 'F', .2, [d.pad('U1.76'), (14.4, 37), (13.25, 38.15), (5.3, 38.15), (5, 38.45)])
    d.track('NRST', 'B', .2, [(22.54, 38.5), (21.64, 39.4), (5, 39.4), (5, 40.8)])
    d.track('NRST', 'F', .2, [(5, 40.8), (5, 40.35)])
    for net, x in [('3V3', 3.73), ('GND', 6.27)]:
        d.track(net, 'F', .2, [(x, 40.8), (x, 40.35)])
        d.via(net, (x, 40.8))
    for at in (old.V_A, old.V_B, old.V_D):
        local.via('VBUS', at, old.VIA_PWR)
    for net, at in old.SIGNAL_VIAS:
        if net in ('CC1', 'CC2', 'VBUS_SENSE'):
            local.via(net, at)
    for at in (old.V_NRST, old.V_C24):
        core.via('NRST', at)
    d.via('NRST', (5, 40.8))
    d.via('USB_FAULT_N', (16.75, 39.05))
    local.via('3V3', old.V3['R90'])
    local.via('GND', old.G_D4)

    # The power mux source crosses the central circuit through R9's checked
    # interior corridor. Its destination lead belongs to the power family.
    d.track('USB_LIMITED', 'B', .3, [d.pad('U10.6'), (14.35, 28.9), d.pad('C86.1')])
    d.track('USB_LIMITED', 'B', .3, [d.pad('C86.1'), (15.95, 30.95),
                                   (18.25, 33.25), (23.25, 38.25)])
    d.track('USB_LIMITED', 'F', .3, [(23.25, 38.25), (28.1, 43.1),
                                   (28.1, 48.3), (29.45, 49.65), (31.05, 49.65)])
    d.via('USB_LIMITED', (23.25, 38.25))
    d.via('USB_LIMITED', (31.05, 49.65))
