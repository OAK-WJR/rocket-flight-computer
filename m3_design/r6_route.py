#!/usr/bin/env python3
"""R6 Freerouting 2.4.1 transport; only non-critical connections may be open."""
from pathlib import Path
import sys

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r5_route as transport

EXTRA_POWER = ('TLM_INPUT_LIMITED', 'TLM_5V_REG', 'TLM_5V', 'TLM_SW', 'TLM_BST')
POWER = transport.POWER + EXTRA_POWER
CRITICAL = transport.CRITICAL


def critical(net):
    return (net in POWER or net in CRITICAL or
            net.startswith(('PYRO', 'ARM', 'RAW_ACT_SENSE', 'ACT_')) or
            net in ('HSE_IN', 'HSE_OUT', 'USB_DP', 'USB_DM', 'CC1', 'CC2', 'TLM_FB'))


def configure(board):
    nets = {p.GetNetname() for f in board.GetFootprints() for p in f.Pads() if p.GetNetname()}
    transport.POWER = tuple(n for n in POWER if n in nets)
    transport.CLASSES = {k: (v[0], [n for n in v[1] if n in nets])
                         for k, v in transport.CLASSES.items()}


def import_noncritical(board, session):
    """Keep reviewed critical copper exactly; import only new signal routing.

    The DSN omits some pours, so the external router may add unnecessary supply
    or pyro branches. Those branches must not replace the reviewed native paths.
    """
    original = pcbnew.LoadBoard(board)
    protected = []
    for track in original.GetTracks():
        if critical(track.GetNetname()):
            copy = track.Duplicate()
            copy.SetUuid(pcbnew.KIID(track.m_Uuid.AsString()))
            protected.append(copy)
    transport.import_ses(board, session)
    routed = pcbnew.LoadBoard(board)
    for track in list(routed.GetTracks()):
        if critical(track.GetNetname()):
            routed.Delete(track)
    for track in protected:
        track.SetParent(routed)
        track.SetNet(routed.FindNet(track.GetNetname()))
        track.SetLocked(True)
        routed.Add(track)
    routed.BuildConnectivity()
    pcbnew.ZONE_FILLER(routed).Fill(routed.Zones())
    pcbnew.SaveBoard(board, routed, True)
    print(f'Restored {len(protected)} reviewed critical tracks/vias unchanged')


def main():
    command = sys.argv[1]
    positional = [x for x in sys.argv[2:] if not x.startswith('--')]
    board = positional[0] if positional else 'm3_design/assembly_review/m3.kicad_pcb'
    pcb = pcbnew.LoadBoard(board)
    configure(pcb)
    if command == 'export':
        import r5_finish
        pairs, other, _ = r5_finish.drc(board)
        incomplete = [p for p in pairs if critical(p[0])]
        if incomplete or other:
            raise RuntimeError('Finish scripted critical copper before Freerouting: ' + repr(incomplete + other))
        seed = next((int(x.split('=', 1)[1]) for x in sys.argv if x.startswith('--seed=')), 61)
        transport.export(board, positional[1] if len(positional) > 1 else 'm3_design/r6_autoroute.dsn',
                         '--no-in2' in sys.argv, seed, '--warm' in sys.argv)
    elif command == 'import':
        import_noncritical(board, positional[1] if len(positional) > 1 else 'm3_design/r6_autoroute.ses')
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main()
