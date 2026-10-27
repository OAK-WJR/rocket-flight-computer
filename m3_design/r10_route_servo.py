"""Four direct PWM lanes to the end header; no servo positive-power copper.

The local protected-header circuit uses R9's explicit table translated 20 mm.
The MCU fanout is new: four ordered diagonals followed by straight F.Cu lanes.
J122's ground carries signal reference under the O6 pack-star harness contract.
"""
import r9_route_servo as old
from r10_route import Translated


def draw(d):
    local = Translated(d, (0.0, 20.0))
    for ref, num, net, at in old.PADS:
        if ref != 'U1':
            local.pad(ref, num, net, at)
    # Preserve the local clamp, pulls, series resistors and header links, but
    # replace every old MCU lead rather than retaining a detached stub.
    for net, layer, width, pts in old.TRACKS:
        if net.startswith('SERVO') and layer == 'F' and pts[0][1] == 52.05:
            continue
        if net == 'GND' and layer == 'F':
            continue
        local.track(net, layer, width, pts)
    for net, at, size in old.VIAS:
        if at != old.V_GND_U1:
            local.via(net, at, size)
    for i, (x, turn) in enumerate(zip((19.19, 21.73, 24.27, 26.81), (51.6, 52.3, 53.0, 53.7)), 1):
        net = f'SERVO{i}_MCU'
        start = d.pad('U1', 21 + i, net=net)
        d.track(net, 'F', 0.2, [start, (start[0], turn), (x, turn + start[0] - x), (x, 74.9)])
    d.track('GND', 'F', 0.2, [d.pad('U1.19', net='GND'), (26.0, 51.4), (26.4, 51.8)])
    d.via('GND', (26.4, 51.8))
    d.via('GND', (25.54, 76.3))
