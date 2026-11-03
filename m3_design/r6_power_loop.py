#!/usr/bin/env python3
"""Repair the R6 buck feedback loop in memory; caller owns DRC, refill and save."""
import argparse
from pathlib import Path
import uuid

import pcbnew

MM, mm = pcbnew.FromMM, pcbnew.ToMM
F, B, I2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu
C174_POSITION = (14.9, 6.4, 0)
NAMESPACE = uuid.UUID('d0aed399-60a2-427a-8979-eb2b6387ae86')


def point(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def xy(p):
    return round(mm(p.x), 4), round(mm(p.y), 4)


def repair(board):
    """Keep FB left of U14; relocate local leadouts and add ground returns.

    Only C174 moves. No schematic, pad geometry, unrelated net, or board outline
    is changed. Deterministic UUIDs make repeated calls replace their own copper.
    Added tracks are locked so automatic routing preserves the reviewed paths.
    """
    expected = {'U14': (21.5, 5.5), 'U16': (10, 7), 'R190': (18.05, 1.5),
                'R206': (18.05, 3.5), 'R191': (18.05, 5.5),
                'C171': (27, 9.5), 'C172': (14.8, 3.3)}
    for ref, position in expected.items():
        f = board.FindFootprintByReference(ref)
        if f is None or xy(f.GetPosition()) != position:
            raise RuntimeError('Power-loop placement changed; rederive ' + ref)
    capacitor = board.FindFootprintByReference('C174')
    if capacitor is None or xy(capacitor.GetPosition()) not in ((23.7, 9.5), C174_POSITION[:2]):
        raise RuntimeError('Unexpected C174 position')

    # Replace old leads by endpoint identity, never by broad spatial deletion.
    remove = [
        ('TLM_5V_REG', F, (23.7, 10.275), (24.7, 9.275)),
        ('TLM_5V_REG', F, (23.7, 10.275), (24.5, 9.475)),
        ('TLM_5V_REG', F, (15.8, 5.75), (14.8, 4.75)),
        ('TLM_5V_REG', F, (14.8, 4.75), (14.8, 4.8)),
        ('TLM_5V_REG', B, (14.4, 5.75), (15.8, 5.75)),
        ('TLM_5V_REG', B, (8.6, 11.55), (14.4, 5.75)),
        ('RAW_PROTECTED', F, (15.7, 7.8), (15, 7.1)),
        ('RAW_PROTECTED', F, (15, 7.1), (11.7, 7.1)),
        ('RAW_PROTECTED', F, (11.7, 7.1), (11.5, 7.3)),
        ('RAW_PROTECTED', F, (11.5, 7.3), (11.5, 8)),
        ('RAW_PROTECTED', F, (11.5, 8), (11.3, 8.2)),
        ('RAW_PROTECTED', F, (11.3, 8.2), (9.5, 8.2)),
    ]
    signatures = {(net, layer, frozenset((a, b))) for net, layer, a, b in remove}
    paths = [
        # FB has one compact, entirely front-side tree, no copper below U14.
        ('TLM_FB', F, .2, [(18.875, 1.5), (18.875, 3.5)]),
        ('TLM_FB', F, .2, [(18.875, 3.5), (19.925, 4.55), (20.4, 4.55)]),
        ('TLM_FB', F, .2, [(18.875, 3.5), (17.225, 5.15), (17.225, 5.5)]),
        ('TLM_FB', F, .2, [(15.675, 6.4), (16.575, 5.5), (17.225, 5.5)]),
        # Preserve the old output-power connection after removing C174's leads.
        ('TLM_5V_REG', F, .2, [(24.5, 9.475), (24.7, 9.275)]),
        # C174 and divider sample the quiet C172 positive pad, not the switch node.
        ('TLM_5V_REG', F, .25, [(14.8, 4.8), (13.85, 5.75), (13.2, 5.75)]),
        ('TLM_5V_REG', F, .2, [(13.2, 5.75), (13.85, 6.4), (14.125, 6.4)]),
        ('TLM_5V_REG', B, .2, [(8.6, 11.55), (13.2, 6.95), (13.2, 5.75)]),
        # Move only the input branch's obstructing local loop off the front.
        ('RAW_PROTECTED', F, .3, [(9.5, 8.2), (9.35, 8.35), (9.35, 8.45)]),
        ('RAW_PROTECTED', I2, .3, [(9.35, 8.45), (10.4, 7.4), (15.3, 7.4), (15.7, 7.8)]),
        # A short narrow escape is required by the 0.5 mm-pitch U16 output pin.
        ('TLM_INPUT_LIMITED', F, .25, [(10.95, 7.75), (10.95, 8.25), (10.9, 8.3)]),
        ('TLM_INPUT_LIMITED', I2, .5, [(10.9, 8.3), (11.7, 9.1), (18.5, 9.1),
                                    (18.55, 9.05), (19.45, 9.05)]),
        ('GND', F, .4, [(25.5, 9.5), (26.4, 10.4), (26.5, 10.4)]),
        ('GND', F, .4, [(14.8, 1.8), (14.8, .85)]),
    ]
    vias = [('TLM_5V_REG', (13.2, 5.75)), ('RAW_PROTECTED', (9.35, 8.45)),
            ('TLM_INPUT_LIMITED', (10.9, 8.3)), ('GND', (26.5, 10.4)),
            ('GND', (14.8, .85))]
    generated = {}
    for index, (net, layer, width, pts) in enumerate(paths):
        for segment, (a, b) in enumerate(zip(pts, pts[1:])):
            key = str(uuid.uuid5(NAMESPACE, f'track:{index}:{segment}'))
            generated[key] = (net, layer, width, a, b)
    via_ids = {str(uuid.uuid5(NAMESPACE, f'via:{i}')): (net, p)
               for i, (net, p) in enumerate(vias)}
    removed = []
    for track in list(board.GetTracks()):
        identity = track.m_Uuid.AsString()
        is_via = track.GetClass() == 'PCB_VIA'
        old_output_via = is_via and track.GetNetname() == 'TLM_5V_REG' and xy(track.GetPosition()) == (15.8, 5.75)
        signature = (track.GetNetname(), track.GetLayer(), frozenset((xy(track.GetStart()), xy(track.GetEnd()))))
        if (track.GetNetname() == 'TLM_FB' or identity in generated or identity in via_ids
                or old_output_via or (not is_via and signature in signatures)):
            removed.append(identity)
            board.Delete(track)
    capacitor.SetOrientationDegrees(C174_POSITION[2])
    capacitor.SetPosition(point(*C174_POSITION[:2]))
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
    for identity, (net, p) in via_ids.items():
        via = pcbnew.PCB_VIA(board)
        via.SetUuid(pcbnew.KIID(identity))
        via.SetPosition(point(*p))
        via.SetWidth(MM(.6))
        via.SetDrill(MM(.3))
        via.SetLayerPair(F, B)
        via.SetNet(board.FindNet(net))
        via.SetLocked(True)
        board.Add(via)
    board.BuildConnectivity()
    return {'C174_position': C174_POSITION, 'removed_items': removed,
            'added_tracks': len(generated), 'added_vias': len(via_ids),
            'zones_require_refill': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.board.resolve() == args.output.resolve():
        raise SystemExit('Use a distinct output path')
    board = pcbnew.LoadBoard(str(args.board))
    print(repair(board))
    pcbnew.SaveBoard(str(args.output), board, True)
