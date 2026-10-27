"""Central MCU/sensor/flash/crystal circuit, rigidly translated R9 polyline tables.

The complete placement of this local block is held by the source-pad assertions.
Power-plane and ground-reference checks requalify it on R10, not by inherited hash.
"""
import r9_power
import r9_route_qspi_hse
import r9_route_imu_baro
from r10_route import CORE_SHIFT, Translated


def draw(d):
    translated = Translated(d, CORE_SHIFT)
    for family in (r9_route_qspi_hse, r9_route_imu_baro):
        for ref, num, net, at in getattr(family, 'PADS', ()):
            translated.pad(ref, num, net, at)
        family.draw(translated)
    r9_power.decoupling(translated, None)
