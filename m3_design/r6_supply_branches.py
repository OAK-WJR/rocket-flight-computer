"""Complete two low-current supply branches after the R6 power-loop repair."""
import uuid

import pcbnew

MM, mm = pcbnew.FromMM, pcbnew.ToMM
F, B = pcbnew.F_Cu, pcbnew.B_Cu
NAMESPACE = uuid.UUID('0bf8c130-d556-44b3-9bda-3d42b3ef2385')
R80_POSITION = (16.3, 6.45)


def point(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def xy(p):
    return round(mm(p.x), 4), round(mm(p.y), 4)


def repair(board):
    """Move R80 clear of its boxed-in pad and add reviewed, locked branches.

    R80 pin 2 must still be unrouted on the initial call; the signal router
    connects BAT_SW_SOURCE afterwards. Pour refill and native DRC are required.
    Deterministic track identities make repeated calls replace their own work.
    """
    expected = {'C175': (10, 13.3), 'U15': (10, 10.5),
                'D8': (11.9, 13.2), 'C174': (14.9, 6.4)}
    for ref, position in expected.items():
        footprint = board.FindFootprintByReference(ref)
        if footprint is None or xy(footprint.GetPosition()) != position:
            raise RuntimeError('Supply-branch placement changed; rederive ' + ref)
    resistor = board.FindFootprintByReference('R80')
    if resistor is None or xy(resistor.GetPosition()) not in ((16.8, 9.2), R80_POSITION):
        raise RuntimeError('Unexpected R80 placement')
    if xy(resistor.GetPosition()) != R80_POSITION:
        for track in board.GetTracks():
            if any(track.GetNetname() == pad.GetNetname()
                   and (pad.HitTest(track.GetStart()) or pad.HitTest(track.GetEnd()))
                   for pad in resistor.Pads()):
                raise RuntimeError('R80 already routed; preserve or reroute its attached copper first')
    paths = [
        ('BAT_IN', B, .2, [(15.475, 6.45), (13.375, 8.55),
                           (13.375, 13.85), (11.875, 15.35), (11.9, 15.35)]),
        ('TLM_5V_REG', F, .25, [(9.225, 13.3), (10.025, 14.1),
                              (11.325, 14.1), (11.525, 13.9),
                              (11.525, 11.6), (11.325, 11.4),
                              (11.3, 11.425), (11.3, 11.45)]),
    ]
    generated = {}
    for index, (net, layer, width, pts) in enumerate(paths):
        for segment, (a, b) in enumerate(zip(pts, pts[1:])):
            identity = str(uuid.uuid5(NAMESPACE, f'track:{index}:{segment}'))
            generated[identity] = net, layer, width, a, b
    for track in list(board.GetTracks()):
        if track.m_Uuid.AsString() in generated:
            board.Delete(track)
    resistor.SetPosition(point(*R80_POSITION))
    resistor.Reference().SetPosition(point(13.8, 6.4))
    for identity, (net, layer, width, a, b) in generated.items():
        track = pcbnew.PCB_TRACK(board)
        track.SetUuid(pcbnew.KIID(identity))
        track.SetLayer(layer)
        track.SetWidth(MM(width))
        track.SetStart(point(*a))
        track.SetEnd(point(*b))
        track.SetNet(board.FindNet(net))
        track.SetLocked(True)
        board.Add(track)
    board.BuildConnectivity()
    return {'R80_position': R80_POSITION, 'added_tracks': len(generated),
            'zones_require_refill': True, 'BAT_SW_SOURCE_requires_routing': True}
