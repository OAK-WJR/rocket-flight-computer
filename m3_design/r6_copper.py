#!/usr/bin/env python3
"""Short, explicit R6 power-loop and flash bypass conductors; KiCad DRC follows."""
import pcbnew
from r5_routes import route


def local_copper(board):
    before = {t.m_Uuid.AsString() for t in board.GetTracks()}
    front = pcbnew.F_Cu
    paths = [
        ('3V3', .25, [(21.07, 17.9), (19.38, 17.9), (19.2, 18.08)]),
        ('TLM_SW', .5, [(22.6, 5.5), (23.65, 5.5), (24.65, 4.5)]),
        ('TLM_SW', .25, [(22.275, 2.5), (24.65, 2.5), (24.65, 4.5)]),
        ('TLM_BST', .2, [(20.725, 2.5), (22.6, 4.375), (22.6, 4.55)]),
        ('TLM_INPUT_LIMITED', .5, [(20.4, 6.45), (20.4, 7.4), (18.5, 9.3)]),
        ('RAW_PROTECTED', .3, [(7.75, 7.975), (7.75, 7.775), (9.025, 7.775), (9.05, 7.75), (9.05, 7.25)]),
        ('TLM_5V_REG', .5, [(29.35, 4.5), (30.8, 5.95), (30.8, 8), (29.3, 9.5), (28.5, 9.5)]),
    ]
    for net, width, points in paths:
        route(board, net, front, points, width)
    for track in board.GetTracks():
        if track.m_Uuid.AsString() not in before:
            track.SetLocked(True)
    print(f'Added {len(paths)} short R6 power/bypass routes')
