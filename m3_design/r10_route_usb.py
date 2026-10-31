"""USB local circuit retained rigidly; direct data and SWD leads to central MCU."""
import r9_route_usb_swd as old
from r10_route import CORE_SHIFT, Translated

USB_SHIFT = (0.0, -3.5)


def draw(d, feed=False):
    local = Translated(d, USB_SHIFT)
    core = Translated(d, CORE_SHIFT)
    for ref, num, net, at in old.PADS:
        if ref not in ('U1', 'J2', 'C24', 'TP86', 'TP92', 'R85', 'C86', 'R110', 'TP82', 'R90'):
            local.pad(ref, num, net, at)
    nrst_count = 0
    for index, (net, layer, width, pts) in enumerate(old.TRACKS):
        if net == 'USB_DM' and layer == 'F' and pts == [(6.88,33.55),(7.75,33.55),(8.15,33.15),(8.8,33.15)]:
            pts = [(6.88,33.55),(8.4,33.55),(8.8,33.15)]
        if net == 'USB_DP' and layer == 'F' and pts == [(6.88,34.05),(7.9,34.05),(7.9,35.05)]:
            pts = [(6.88,34.05),(7.455,34.05),(7.9,34.495),(7.9,35.05)]
        if net in ('CC1', 'CC2', 'VBUS') or index < 6:
            if net == 'VBUS' and layer == 'B' and pts == [(11.35, 33.5), (11.35, 32.15)]:
                # Tee into the retained trunk on U10.1's axis (R9-RTE-05).
                d.track(net, layer, width, [(11.3, 30.0), d.pad('U10.1')])
            else:
                local.track(net, layer, width, pts)
        elif net == 'USB_FAULT_N':
            continue  # R10 circuit pass: make a four-lane SPI3 escape beside NRST.
        elif net == 'NRST':
            if nrst_count < 2:
                core.track(net, layer, width, pts)
            elif nrst_count == 2:
                d.track('NRST','B',.2,[core.move(old.V_C24),(25.13,49.1),d.pad('C24.1')])
            nrst_count += 1
        elif net == 'USB_ILIM':
            continue
        elif net == 'GND' and pts[-1] == old.G_D4:
            local.track(net, layer, width, pts)

    d.track('USB_DM', 'F', .2, [d.pad('D4.6'), (15.85, 29.65), (19.5, 33.3), d.pad('U1.70')])
    d.track('USB_DP', 'F', .2, [d.pad('D4.4'), (16.75, 31.55), (19, 33.8), d.pad('U1.71')])
    # VBUS_SENSE retains the B.Cu hop under USB_LIMITED, then uses a direct
    # 45-degree F.Cu approach followed by the U1.65 axis.
    d.track('VBUS_SENSE', 'B', .2, [d.pad('R9.2'), (9.95, 27.7)])
    d.track('VBUS_SENSE', 'F', .2, [(9.95, 27.7), (10.9, 27.7), (15.15, 23.45)])
    d.via('VBUS_SENSE', (15.15, 23.45))
    d.track('VBUS_SENSE', 'B', .2, [(15.15, 23.45), (18.45, 26.75)])
    d.via('VBUS_SENSE', (18.45, 26.75))
    d.track('VBUS_SENSE', 'F', .2, [(18.45, 26.75), (22.0, 30.3), d.pad('U1.65')])
    d.track('VBUS_SENSE', 'F', .2, [(9.95, 27.7), d.pad('R110.1')])
    # Retain the qualified inward MCU escape, then pass below SPI3's source vias on B.Cu.
    d.track('USB_FAULT_N', 'F', .2, [d.pad('U1.87'), (16.7, 42.5), (16.7, 39.05)])
    d.via('USB_FAULT_N', (16.7, 39.05))
    d.track('USB_FAULT_N', 'B', .2, [(16.7, 39.05), (15.0383, 40.7117), (9.3, 40.7117),
                                   (9.3, 34.1), (12.6, 30.8), (12.6, 26.55), d.pad('U10.4')])
    # D-AVA-01: the fault pull-up joins the limiter cell, freeing J2's pin-legend band. D-R19-14: R90 moves 3.5 mm east,
    # out of J440.4's 1.5 mm M-6 ring, to the end of its own run (which no longer doubles back west); its 3V3 via moves with it.
    d.track('USB_FAULT_N', 'B', .2, [d.pad('U10.4'),(13.05,25.7),(13.05,23.95),d.pad('R90.2')])
    d.track('3V3', 'B', .2, [d.pad('R90.1'),(9.6,23.0)])
    d.via('3V3',(9.6,23.0))
    # SWD from the TC2030 pads (J2: 2 SWDIO, 4 SWCLK, 3 NRST), clear of its three locating holes.
    # J2's F.Cu keep-out covers the strip between its pad rows: each track ends inside its pad, outside the strip.
    d.pad('J2.2', at=(3.73, 38.765)); d.pad('J2.4', at=(5.0, 38.765)); d.pad('J2.3', at=(5.0, 40.035))
    d.track('SWDIO', 'F', .2, [(3.73, 38.45), (6.08, 36.1), (12.6, 36.1), (14.85, 33.85), (18.5, 33.85),
                               d.pad('U1.72')])
    d.track('SWCLK', 'F', .2, [(5.0, 38.45), (6.85, 36.6), (14.3, 36.6), (14.7, 37.0), d.pad('U1.76')])
    # NRST leaves J2.3 south on F.Cu (between J2's 3V3 / GND stub vias and R33), runs north west of R32 / R33 and east
    # over the bottom USB_FAULT_N run to one via, then enters V_NRST from the west on B.Cu (R10_DECISIONS D-R2-09: the
    # former B.Cu leg from J2 and its two hop vias are gone).
    d.track('NRST', 'F', .2, [(5.0, 40.35), (6.2021, 41.5521), (8.2479, 41.5521),
                             (9.5, 40.3), (9.5, 38.3), (10.5, 37.3), (14.2, 37.3)])
    d.via('NRST', (14.2, 37.3))
    d.track('NRST', 'B', .2, [(14.2, 37.3), (15.2607,36.2393), (22.54,36.2393), core.move(old.V_NRST)])
    d.via('NRST', core.move(old.V_NRST))
    for net, x in [('3V3', 3.73), ('GND', 6.27)]:
        d.track(net, 'F', .2, [(x, 40.35), (x, 40.8)])
        d.via(net, (x, 40.8))
    for at in (old.V_A, old.V_B, old.V_D):
        local.via('VBUS', at, old.VIA_PWR)
    for net, at in old.SIGNAL_VIAS:
        if net in ('CC1', 'CC2') or (net == 'VBUS_SENSE' and at == old.V_SENSE):
            local.via(net, at)
    for at in (old.V_C24,):
        core.via('NRST', at)
    local.via('GND', old.G_D4)

    # USB_ILIM: R85 sits on F.Cu above the limiter (outside both courtyards): one via north of its east pad, then a short
    # B.Cu run to U10.5; its GND pad joins C28.2's existing GND via.
    d.track('USB_ILIM', 'F', .2, [d.pad('R85.1'), (14.825, 26.0)])
    d.via('USB_ILIM', (14.825, 26.0))
    d.track('USB_ILIM', 'B', .2, [(14.825, 26.0), (14.825, 27.0), (14.325, 27.5), d.pad('U10.5')])
    d.track('GND', 'F', .2, [d.pad('R110.2'), (11.6, 23.9)])
    d.via('GND', (11.6, 23.9))
    # Local bypass and one transition into the west In2 power corridor. This corridor
    # passes outside SPI3/IMU and below the crystal keep-out before reaching the mux.
    d.track('USB_LIMITED','B',.4,[d.pad('U10.6'),(15.1,28.45),(15.55,28)])
    d.via('USB_LIMITED',(16,28))
    d.track('USB_LIMITED','F',.4,[(16,28),d.pad('C86.1')])
    d.track('GND','F',.3,[d.pad('C86.2'),(18.3,25.3)]);d.via('GND',(18.3,25.3))
    d.track('USB_LIMITED','B',.4,[(15.55,28),(16,28)]
    )
    # D-R20-04 (R20-RTE-01): TP82 sits on the diagonal's own extension, B(11.2,20.7), so its spur is one straight run
    # (D-R19-14's 4.03 mm two-bend tail to B(11.0,17.6) is gone).
    d.track('USB_LIMITED','B',.4,[(15.55,28),(15.55,25.05),d.pad('TP82.1')])

    if feed:
        power_feed(d)


def power_feed(d):
    """Draw after In2 rail regions exist, so the stage gate sees their real routing constraints."""
    # D-R18-06: both via ends sit inside the In2 3V3 shoulder and bay (r10_route_power.IN2_3V3), so this run no longer
    # cuts the 3V3 fill into pieces.
    d.track('USB_LIMITED','In2',.4,[(16,28),(15,29),(8.5,29),(8.5,30.3),(9.6,31.4),(9.6,50.85),(26.2,50.85),(26.2,61.8),(26.2,62.4),(25.6,63.0)])
    d.track('USB_LIMITED','In2',.4,[(26.2,61.8),(22.45,61.8),(22,62.25)])
    for at in ((25.6,63.0),(22,62.25)):d.via('USB_LIMITED',at)
    d.track('USB_LIMITED','B',.3,[(25.6,63.0),(25.35,62.75),d.pad('C98.1')])
    d.track('USB_LIMITED','B',.3,[d.pad('C98.1'),(24.3,63.25),d.pad('U11.7')])
    d.track('USB_LIMITED','B',.4,[(22,62.25),d.pad('R87.1')])
