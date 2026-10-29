#!/usr/bin/env python3
"""Reuse the reviewed grid finisher with the R6 net contract and recorded replay.

--critical-only completes scripted nets before the non-critical Freerouting pass.
--record/--replay have the same guarded geometry format as r5_finish.py.
"""
from pathlib import Path
import sys

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r5_finish as finish
import r6_route


def drop_unused(board):
    """Remove dangling copper in checked batches, splitting only rejected batches.

    Each accepted batch preserves native connectivity after a zone refill.
    This avoids a full refill for each of hundreds of disconnected stubs.
    """
    removed = 0
    for _ in range(10):
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(finish.PCB, board, True)
        left, other, dangling = finish.drc(finish.PCB)
        index = finish._index(board)
        pending = [index[u] for u in sorted(dangling) if u in index]
        base = finish.n_open(board)
        accepted = 0

        def attempt(items):
            nonlocal accepted
            if not items:
                return
            transaction = finish.Txn(board)
            keys = [finish._key(item) for item in items]
            for item in items:
                transaction.delete(item)
            if finish.n_open(board, fill=True) <= base:
                accepted += len(items)
                return
            transaction.undo()
            if len(keys) > 1:
                # Undo recreates objects, so refresh handles before each half.
                half = len(keys) // 2
                for group in (keys[:half], keys[half:]):
                    current = {finish._key(t): t for t in board.GetTracks()}
                    attempt([current[k] for k in group if k in current])

        attempt(pending)
        removed += accepted
        if not accepted:
            break
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(finish.PCB, board, True)
    left, other, _ = finish.drc(finish.PCB)
    return left, other, removed


def main():
    board = next((x for x in sys.argv[1:] if not x.startswith('--')),
                 'm3_design/assembly_review/m3.kicad_pcb')
    finish.PCB = board
    # Iterative passes must not reuse IDs from an earlier saved routing pass.
    finish.UUID_SEED = None
    finish._drop_unused = drop_unused
    if '--rounds-only' in sys.argv:
        finish.late_islands = lambda board, state: None
    r6_route.configure(pcbnew.LoadBoard(board))
    finish.critical = r6_route.critical
    if '--critical-only' in sys.argv:
        original = finish.drc

        def filtered(path):
            pairs, other, dangling = original(path)
            return [p for p in pairs if r6_route.critical(p[0])], other, dangling

        finish.drc = filtered
    finish.main()


if __name__ == '__main__':
    main()
