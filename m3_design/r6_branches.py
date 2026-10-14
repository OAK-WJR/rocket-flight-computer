#!/usr/bin/env python3
"""Explicit low-current branch repairs; widths are not actuator feed widths."""
import pcbnew
import r5_finish
import r5_maze
import r5_routes

F, B, IN2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu


def connect(board, net, start, end, width=.2, start_layers=None, end_layers=None):
    paths, vias = r5_maze.maze_multi(board, net, (F, B, IN2), start, end,
                                    w=width, a_layers=start_layers, c_layers=end_layers,
                                    margin=4, via_cost=10)
    r5_finish.draw(board, net, paths, vias, width)
    print('Branch', net, start, end, 'vias', vias, flush=True)


def move_c120(board):
    cap = board.FindFootprintByReference('C120')
    for track in list(board.GetTracks()):
        if track.GetClass() != 'PCB_TRACK' or track.GetLayer() != B:
            continue
        if any(track.GetNetname() == pad.GetNetname() and
               (pad.HitTest(track.GetStart()) or pad.HitTest(track.GetEnd())) for pad in cap.Pads()):
            board.Delete(track)
    cap.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(3.5), pcbnew.FromMM(82)))
    connect(board, 'ACT_GATE', (4.2, 82), (5.9, 84.4), .2, {B}, {B})


def repair(board):
    # A Tag-Connect pin must escape its footprint's probe keep-out before a via.
    bad = {'7cf1ff68-4fca-4431-ad1f-f275db0ad6e1', 'a5a971d1-a8a4-4b55-80fe-85ce5d51a3fb'}
    for track in list(board.GetTracks()):
        if track.m_Uuid.AsString() in bad:
            board.Delete(track)
    jobs = [
        ('ACT_FET_S', (8.8, 83.5), (7, 83.5), .25, {B}, {B}),
        ('TLM_5V_REG', (9.225, 13.3), (11.3, 11.45), .25, {F}, {F}),
        ('BAT_IN', (15.975, 9.2), (11.9, 15.35), .2, {B}, {B}),
        ('RAW_ACT', (10.4, 46.67), (5.3, 64.2), .2, {F}, None),
        ('3V3', (36.5, 63.63), (32, 64), .2, {B}, {F}),
        ('IMU_CS', (36.5, 62.77), (24.35, 48.75), .2, {B}, {F}),
    ]
    for net, start, end, width, sl, el in jobs:
        try:
            connect(board, net, start, end, width, sl, el)
        except RuntimeError as error:
            print('Branch remains open:', error, flush=True)
    previous = r5_maze.PASSABLE_IN2
    try:
        r5_maze.PASSABLE_IN2 = previous | {'BAT_IN'}
        r5_routes.tie(board, 'GND', (9.2, 90.6), (8.7, 90.6), B, w=.25, tries=3)
        print('Q122 ground return added', flush=True)
    except RuntimeError as error:
        print('Q122 ground return remains open:', error, flush=True)
    finally:
        r5_maze.PASSABLE_IN2 = previous
    pad = next(p for p in board.FindFootprintByReference('C25').Pads() if p.GetNumber() == '2')
    pad.SetThermalSpokeAngleDegrees(45)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
