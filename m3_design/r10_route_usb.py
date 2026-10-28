"""USB local circuit retained rigidly; direct data and SWD leads to central MCU."""
import r9_route_usb_swd as old
from r10_route import CORE_SHIFT, Translated

USB_SHIFT = (0.0, -3.5)


def draw(d):
    local = Translated(d, USB_SHIFT)
    core = Translated(d, CORE_SHIFT)
    for ref, num, net, at in old.PADS:
        if ref not in ('U1', 'J2', 'C24', 'TP86', 'TP92'):
            local.pad(ref, num, net, at)
    nrst_count = 0
    for index, (net, layer, width, pts) in enumerate(old.TRACKS):
        if net in ('CC1', 'CC2', 'VBUS', 'USB_ILIM') or index < 6:
            if net == 'VBUS' and layer == 'B' and pts == [(11.35, 33.5), (11.35, 32.15)]:
                # Tee into the retained trunk on U10.1's axis (R9-RTE-05).
                d.track(net, layer, width, [(11.3, 30.0), d.pad('U10.1')])
            else:
                local.track(net, layer, width, pts)
        elif net == 'USB_FAULT_N' and layer == 'B' and pts[0] != old.V_FAULT:
            if pts[-1] == (14.05, 26.5):
                # AUD-5: delete the entire TP86 branch; U10.4 and R90 remain connected below.
                continue
            local.track(net, layer, width, pts)
        elif net == 'NRST':
            if nrst_count < 3:
                core.track(net, layer, width, pts)
            nrst_count += 1
        elif net == '3V3' and layer == 'B' or net == 'GND' and pts[-1] == old.G_D4:
            local.track(net, layer, width, pts)

    d.track('USB_DM', 'F', .2, [d.pad('D4.6'), (15.85, 29.65), (19.5, 33.3), d.pad('U1.70')])
    d.track('USB_DP', 'F', .2, [d.pad('D4.4'), (16.75, 31.55), (19, 33.8), d.pad('U1.71')])
    # VBUS sense: R9 (bottom) -> F.Cu over the USB pair's outside -> U1.65; R110 tapped on the bottom.
    d.track('VBUS_SENSE', 'B', .2, [d.pad('R9.2'), (9.95, 27.7)])
    d.track('VBUS_SENSE', 'F', .2, [(9.95, 27.7), (14.5, 27.7), (16.6, 29.8), (17.875, 29.8),
                                    (22.0, 33.925), d.pad('U1.65')])
    d.via('VBUS_SENSE', (17.875, 29.8))
    # AUD-5: stop at the divider pad, removing TP92 and its entire branch.
    d.track('VBUS_SENSE', 'B', .2, [(17.875, 29.8), d.pad('R110.1')])
    # D-R3-B4: the drop sits 0.05 mm west of R2's (16.75, 39.05), 0.20 mm from U1.80.
    d.track('USB_FAULT_N', 'F', .2, [d.pad('U1.87'), (16.7, 42.5), (16.7, 39.05)])
    d.track('USB_FAULT_N', 'B', .2, [(16.7, 39.05), (11.85, 39.05), (11.85, 31.85),
                                    (12.6, 31.1), (12.6, 26.55), (13.9, 26.55)])
    # SWD from the TC2030 pads (J2: 2 SWDIO, 4 SWCLK, 3 NRST), clear of its three locating holes.
    # J2's F.Cu keep-out covers the strip between its pad rows: each track ends inside its pad, outside the strip.
    d.pad('J2.2', at=(3.73, 38.765)); d.pad('J2.4', at=(5.0, 38.765)); d.pad('J2.3', at=(5.0, 40.035))
    d.track('SWDIO', 'F', .2, [(3.73, 38.45), (3.73, 36.5), (13.0, 36.5), (15.65, 33.85), (18.5, 33.85),
                               d.pad('U1.72')])
    d.track('SWCLK', 'F', .2, [(5.0, 38.45), (5.0, 38.0), (6.0, 37.0), d.pad('U1.76')])
    # NRST leaves J2.3 south on F.Cu (between J2's 3V3 / GND stub vias and R33), runs north west of R32 / R33 and east
    # over the bottom USB_FAULT_N run to one via, then enters V_NRST from the west on B.Cu (R10_DECISIONS D-R2-09: the
    # former B.Cu leg from J2 and its two hop vias are gone).
    d.track('NRST', 'F', .2, [(5.0, 40.35), (6.2021, 41.5521), (8.2479, 41.5521),
                            (9.5, 40.3), (9.5, 38.4), (10.0, 37.9), (12.4, 37.9)])
    d.via('NRST', (12.4, 37.9))
    d.track('NRST', 'B', .2, [(12.4, 37.9), (14.2, 36.1), (21.9, 36.1), (22.54, 36.74), core.move(old.V_NRST)])
    for net, x in [('3V3', 3.73), ('GND', 6.27)]:
        d.track(net, 'F', .2, [(x, 40.35), (x, 40.8)])
        d.via(net, (x, 40.8))
    for at in (old.V_A, old.V_B, old.V_D):
        local.via('VBUS', at, old.VIA_PWR)
    for net, at in old.SIGNAL_VIAS:
        if net in ('CC1', 'CC2') or (net == 'VBUS_SENSE' and at == old.V_SENSE):
            local.via(net, at)
    for at in (old.V_NRST, old.V_C24):
        core.via('NRST', at)
    d.via('USB_FAULT_N', (16.7, 39.05))
    local.via('3V3', old.V3['R90'])
    local.via('GND', old.G_D4)

    # USB_LIMITED (USB VBUS after U10's limit) to the power mux U11 entirely on B.Cu: TP82, east along y 33.25,
    # then down the free bottom lane at x 32.3 (east of U1's decoupling) to U11.7, with C98 and R87 tapped on the way.
    d.track('USB_LIMITED', 'B', .4, [d.pad('U10.6'), (14.35, 28.9), d.pad('C86.1')])
    d.track('USB_LIMITED', 'B', .4, [d.pad('C86.1'), (15.95, 30.95), d.pad('TP82.1')])
    # R10_DECISIONS D-R3-B1: beside the camera port the bottom lane runs at x 31.8 (0.5 mm west, in the free strip
    # under U1's east pin row) so the bottom channel east of it holds the camera RX hop and its GND vias; one 45 deg
    # step south of the camera cell returns it to x 32.3.
    d.track('USB_LIMITED', 'B', .4, [d.pad('TP82.1'), (31.8, 33.25), (31.8, 45.0), (32.3, 45.5), (32.3, 58.2)])
    d.track('USB_LIMITED', 'B', .4, [(32.3, 58.2), (32.3, 59.2)])
    d.track('USB_LIMITED', 'B', .4, [(32.3, 59.2), d.pad('U11.7')])
    d.track('USB_LIMITED', 'B', .4, [(32.3, 59.2), d.pad('C98.1')])
    d.track('USB_LIMITED', 'B', .4, [d.pad('R87.1'), (30.0, 58.6), (30.4, 58.2), (32.3, 58.2)])
