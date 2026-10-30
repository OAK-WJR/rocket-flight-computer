"""Central MCU/sensor/flash/crystal circuit, rigidly translated R9 polyline tables.

The fast-interface placement is held by source-pad assertions. D-AVA-01 redraws the local
C13-C16/C19 ground/supply joins, C24 reset-filter tap and 3V3A power trunk for adjacent cell escapes.
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
        if net == '3V3' and layer == 'B' and points == [(24.25,38.5),(23.87,38.12),(23.52,38.12)]:
            points = [(24.25,38.5),(24.25,37.7),(23.52,37.7),(22.44,37.7),(22.02,38.12)]
        if net == '3V3' and points == [(23.52,36.8),(23.52,38.12)]:
            points = [(23.52,36.8),(23.52,37.7)]
        if net == '3V3' and layer == 'B' and points == [(24.2,50.0),(24.2,49.32)]:
            points = [(24.2,50.0),(24.05,49.85),(24.05,49.32)]
        if net == 'GND' and points == [(24.2,48.48),(24.2,47.7)]:
            points = [(24.05,48.48),(24.2,48.33),(24.2,47.7)]
        if net == 'VCAP1' and layer == 'B' and points == [(24.25,39.5),(23.35,39.5)]:
            points = [(24.25,39.5),(23.35,38.6)]
        if net == 'GND' and points == [(23.35,40.65),(24.25,40.65)]:
            points = [(23.35,39.85),(22.6,39.85)]
            width = .2
        if net == 'GND' and points == [(9.85,52.02),(9.85,52.8)]:
            points = [(9.85,52.02),(10.25,52.42),(10.25,53.1)]
        if net == 'GND' and points == [(16.82,53.6),(16.82,55.3)]:
            return
        if net == '3V3A' and points == [(11.5,51.7),(21.05,51.7),(22.0,50.75)]:
            return
        if net == '3V3' and points in ([(17.0,52.05),(17.0,52.95),(16.35,53.6),(15.2,53.6)], [(15.2,53.6),(15.98,53.6)]):
            return
        if (net, tuple(tuple(p) for p in points)) in C32_R9:
            return
        super().track(net, layer, width, points)

    def via(self, net, at, size=(0.5, 0.3)):
        if net == 'GND' and tuple(at) == (24.25,40.65):
            at = (22.6,39.85)
        if net == 'GND' and tuple(at) == (9.85,52.8):
            at = (10.25,53.1)
        if net == '3V3' and tuple(at) == (15.2,53.6):
            return
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
    # Analog supply uses one straight inner-layer trunk below the crystal keep-out.
    d.track('3V3A','B',.25,[(16.5,50.2),(16,50.2)]);d.via('3V3A',(16,50.2))
    d.track('3V3A','In2',.25,[(16,50.2),(26.05,50.2),(27,49.25)])
    # C14 remains at its MCU supply pin; its transition is east of the adjacent buzzer escape.
    d.track('3V3','F',.3,[d.pad('U1.11'),(22,51.55),(22.6,52.15)])
    d.via('3V3',(22.6,52.15))
    d.track('3V3','B',.3,[(22.6,52.15),d.pad('C14.1'),(21.82,51.8),(19.5,49.48),(19.5,49.15)])
    d.track('GND','B',.2,[d.pad('C14.2'),(20.98,52.96),(21.82,53.8)])
