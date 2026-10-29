"""Central MCU/sensor/flash/crystal circuit, rigidly translated R9 polyline tables.

The complete placement of this local block is held by the source-pad assertions.
Power-plane and ground-reference checks requalify it on R10, not by inherited hash.
One deliberate exception (R10_DECISIONS D-R2-12): C32 (U5's 3V3A bypass) leaves R9's west end of the 3V3A line,
which falls 3.1 mm from R10's west mid support, for a spot north of U5.1 on the same line; its two R9 straps, its R9
GND via and its pad assertion are skipped here and redrawn by c32().
"""
import r9_power
import r9_route_qspi_hse
import r9_route_imu_baro
from r10_route import CORE_SHIFT, Translated

C32_R9 = {('3V3A', ((3.72, 48.15), (2.42, 48.15))), ('GND', ((1.58, 48.15), (0.85, 48.15)))}


class CoreTable(Translated):
    def track(self, net, layer, width, points):
        if (net, tuple(tuple(p) for p in points)) in C32_R9:
            return
        super().track(net, layer, width, points)

    def via(self, net, at, size=(0.5, 0.3)):
        if net == 'GND' and tuple(at) == r9_route_imu_baro.G['C32']:
            return
        super().via(net, at, size)


def c32(d):
    """C32 north of U5.1 (B.Cu, rotation 90): 3V3A pad onto the 3V3A line's U5.1 node, GND pad to its own via."""
    d.track('3V3A', 'B', 0.25, [(8.72, 46.65), d.pad('C32.1', net='3V3A', at=(8.72, 46.27))])
    d.track('GND', 'B', 0.2, [d.pad('C32.2', net='GND', at=(8.72, 45.43)), (8.72, 44.8)])
    d.via('GND', (8.72, 44.8))


def draw(d):
    translated = CoreTable(d, CORE_SHIFT)
    for family in (r9_route_qspi_hse, r9_route_imu_baro):
        for ref, num, net, at in getattr(family, 'PADS', ()):
            if ref != 'C32':
                translated.pad(ref, num, net, at)
        family.draw(translated)
    r9_power.decoupling(translated, None)
    c32(d)
