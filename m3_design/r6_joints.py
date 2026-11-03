#!/usr/bin/env python3
"""Repair weak endpoint overlaps in memory after routing; never move parts."""
import argparse
import json
import math
from pathlib import Path
import sys
import uuid

import pcbnew

import r5_maze
from r6_testpads import Index

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check_r6 import copper_shapes, distance_to_segment, overlap_only_joints, xy

MM, mm = pcbnew.FromMM, pcbnew.ToMM
NAMESPACE = uuid.UUID('8b5ab056-d383-41ec-b80b-f5f3345a5729')


def vector(p):
    return pcbnew.VECTOR2I(*p)


def coords(p):
    return p.x, p.y


def index_copper(board):
    result = {}
    for layer, items in copper_shapes(board).items():
        result[layer] = Index()
        for name, net, shape, owner in items:
            result[layer].add(shape, owner.GetClass(), name, net, owner)
    return result


def detect(board, indices):
    """Same endpoint criterion as the independent checker, with spatial lookup."""
    found, seen = [], set()
    for track in board.GetTracks():
        if track.GetClass() != 'PCB_TRACK':
            continue
        layer, net = track.GetLayer(), track.GetNetname()
        for end in (track.GetStart(), track.GetEnd()):
            key = (layer, net, *coords(end))
            if key in seen:
                continue
            same = [entry for entry in indices[layer].near(pcbnew.SHAPE_CIRCLE(end, track.GetWidth() // 2))
                    if entry[3] == net and entry[4] != track]
            if any(shape.Collide(end, 0) for shape, kind, _, _, _ in same if kind != 'PCB_TRACK'):
                continue
            if any(distance_to_segment(xy(end), xy(owner.GetStart()), xy(owner.GetEnd())) <= .001
                   for _, kind, _, _, owner in same if kind == 'PCB_TRACK'):
                continue
            touch = [entry for entry in same if entry[0].Collide(end, max(0, track.GetWidth() // 2 - 1000))]
            if touch:
                found.append((track, coords(end), touch))
                seen.add(key)
    return sorted(found, key=lambda f: (f[0].GetNetname(), f[0].GetLayer(), f[1]))


def paths(a, b):
    """Short deterministic 0/45/90-degree routes, in integer board units."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    if not dx or not dy or abs(dx) == abs(dy):
        return [[a, b]] if a != b else []
    diagonal = min(abs(dx), abs(dy))
    sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
    knees = [(a[0] + sx * diagonal, a[1] + sy * diagonal),
             (b[0] - sx * diagonal, b[1] - sy * diagonal),
             (a[0], b[1]), (b[0], a[1])]
    return [[a, k, b] for k in dict.fromkeys(knees)]


def destinations(end, target, width):
    shape, kind, _, _, owner = target
    if kind in ('PAD', 'PCB_VIA'):
        return [coords(owner.GetPosition())]
    if kind == 'PCB_TRACK':
        a, b = coords(owner.GetStart()), coords(owner.GetEnd())
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = dx * dx + dy * dy
        u = 0 if not length else max(0, min(1, ((end[0] - a[0]) * dx + (end[1] - a[1]) * dy) / length))
        nearest = (round(a[0] + u * dx), round(a[1] + u * dy))
        return list(dict.fromkeys([nearest, *sorted((a, b), key=lambda p: math.dist(end, p))]))
    if kind == 'ZONE':
        # Land the complete trace end inside copper, not on another thin overlap.
        radius = max(MM(.1), width // 2)
        inside = []
        for step in range(1, 61):
            distance = MM(step * .025)
            for dx, dy in ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)):
                p = (end[0] + dx * distance, end[1] + dy * distance)
                if all(shape.Contains(vector((p[0] + round(radius * math.cos(i * math.pi / 8)),
                                              p[1] + round(radius * math.sin(i * math.pi / 8)))))
                       for i in range(16)):
                    inside.append(p)
            if inside:
                break
        return inside
    return []


def candidate(board, net, layer, width, points):
    tracks = []
    for a, b in zip(points, points[1:]):
        if a == b:
            continue
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(vector(a)); track.SetEnd(vector(b))
        track.SetLayer(layer); track.SetWidth(width); track.SetNet(board.FindNet(net))
        tracks.append(track)
    return tracks


def redundant_stub(track, index):
    """A short branch touching only one conductor cannot join two conductors."""
    if math.dist(coords(track.GetStart()), coords(track.GetEnd())) > MM(1):
        return None
    shape = track.GetEffectiveShape(track.GetLayer())
    contacts = [entry for entry in index.near(shape)
                if entry[3] == track.GetNetname() and entry[4] != track
                and entry[0].Collide(shape, 0)]
    if len(contacts) != 1:
        return None
    target, kind, name, _, owner = contacts[0]
    if kind == 'ZONE':
        # One zone object can contain several disconnected copper islands.
        return None
    if kind == 'PCB_TRACK':
        anchored = any(distance_to_segment(xy(end), xy(owner.GetStart()), xy(owner.GetEnd())) <= .001
                       for end in (track.GetStart(), track.GetEnd()))
    else:
        anchored = any(target.Collide(end, 0) for end in (track.GetStart(), track.GetEnd()))
    return name if anchored else None


def duplicate_segment(track, index):
    a, b = coords(track.GetStart()), coords(track.GetEnd())
    return any(kind == 'PCB_TRACK' and net == track.GetNetname()
               and {coords(owner.GetStart()), coords(owner.GetEnd())} == {a, b}
               and owner.GetWidth() == track.GetWidth()
               for _, kind, _, net, owner in index.near(track.GetEffectiveShape(track.GetLayer())))


def clear(board, tracks, index, keepouts, holes):
    settings = board.GetDesignSettings()
    edge = board.GetBoardEdgesBoundingBox()
    for track in tracks:
        if duplicate_segment(track, index):
            return False
        shape, net, layer = track.GetEffectiveShape(track.GetLayer()), track.GetNetname(), track.GetLayer()
        box = shape.BBox()
        border = settings.m_CopperEdgeClearance
        if (box.GetX() < edge.GetX() + border or box.GetY() < edge.GetY() + border or
                box.GetRight() > edge.GetRight() - border or box.GetBottom() > edge.GetBottom() - border):
            return False
        block = r5_maze.BLOCK
        in_block = not (mm(box.GetRight()) < block[0] or mm(box.GetX()) > block[2] or
                        mm(box.GetBottom()) < block[1] or mm(box.GetY()) > block[3])
        for foreign, kind, _, other_net, owner in index.near(shape, 1.1):
            if other_net == net:
                continue
            gap = max(settings.m_MinClearance,
                      MM(r5_maze.rule_clearance(net, other_net, in_block) - r5_maze.MARGIN),
                      owner.GetLocalClearance() or 0)
            if kind != 'ZONE':
                gap = max(gap, owner.GetOwnClearance(layer))
            if (kind == 'PAD' and owner.GetParentFootprint().GetReference() == 'J2'
                    and owner.GetNumber() in ('1', '2', '3', '4', '5', '6')
                    and owner.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH):
                gap = max(gap, MM(.508))
            if shape.Collide(foreign, max(0, gap - 1000)):
                return False
        if any(shape.Collide(area, 0) for area in keepouts.get(layer, [])):
            return False
        if any(other_net != net and shape.Collide(hole, settings.m_HoleClearance - 1000)
               for other_net, hole in holes):
            return False
    return True


def repair(board):
    """Re-detect weak joints, add clear bridges, return every unresolved finding.

    Refills before detection and after changes. Prunes a branch only when it is
    at most 1 mm long, touches exactly one other same-net conductor, and already
    has an endpoint anchored on that conductor. Such a branch cannot connect
    two conductors. Other repairs add short clear centerline bridges. Existing
    pads, vias, footprints and useful tracks stay fixed. Pruning can expose an
    unused fan-out via: run the finisher's checked dangling-copper cleanup next,
    then native DRC. This helper never prunes an entire escape route.
    """
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    indices = index_copper(board)
    findings = detect(board, indices)
    detected = len(findings)
    pruned = []
    while True:
        removal = next(((track, target) for track, _, _ in findings
                        for target in [redundant_stub(track, indices[track.GetLayer()])]
                        if target), None)
        if removal is None:
            break
        track, target = removal
        pruned.append({'net': track.GetNetname(), 'layer': board.GetLayerName(track.GetLayer()),
                       'uuid': track.m_Uuid.AsString(), 'target': target,
                       'path_mm': [xy(track.GetStart()), xy(track.GetEnd())],
                       'reason': 'Short branch anchored to only one same-net conductor'})
        board.Delete(track)
        indices = index_copper(board)
        findings = detect(board, indices)
    keepouts, holes = {}, []
    for zone in list(board.Zones()) + [z for f in board.GetFootprints() for z in f.Zones()]:
        if zone.GetIsRuleArea() and zone.GetDoNotAllowTracks():
            for layer in indices:
                if zone.IsOnLayer(layer):
                    keepouts.setdefault(layer, []).append(zone.Outline())
    for f in board.GetFootprints():
        for pad in f.Pads():
            if pad.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH, pcbnew.PAD_ATTRIB_PTH):
                holes.append((pad.GetNetname(), pad.GetEffectiveHoleShape()))
    fixed, skipped = [], []
    for source, end, targets in findings:
        net, layer = source.GetNetname(), source.GetLayer()
        attempts = []
        for target in targets:
            width = min(source.GetWidth(), target[4].GetWidth()) if target[1] == 'PCB_TRACK' else source.GetWidth()
            for dest in destinations(end, target, width):
                if math.dist(end, dest) > MM(2):
                    continue
                for points in paths(end, dest):
                    length = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
                    attempts.append((length, target[2], width, points))
        selected = None
        for _, name, width, points in sorted(attempts):
            tracks = candidate(board, net, layer, width, points)
            if clear(board, tracks, indices[layer], keepouts, holes):
                selected = name, width, points, tracks
                break
        if selected is None:
            skipped.append({'net': net, 'layer': board.GetLayerName(layer),
                            'endpoint_mm': [mm(x) for x in end], 'reason': 'No clear local centerline bridge'})
            continue
        name, width, points, tracks = selected
        for track in tracks:
            key = f'{net}:{layer}:{coords(track.GetStart())}:{coords(track.GetEnd())}:{width}'
            track.SetUuid(pcbnew.KIID(str(uuid.uuid5(NAMESPACE, key))))
            track.SetLocked(True)
            board.Add(track)
            indices[layer].add(track.GetEffectiveShape(layer), 'PCB_TRACK',
                               'PCB_TRACK ' + track.m_Uuid.AsString(), net, track)
        fixed.append({'net': net, 'layer': board.GetLayerName(layer), 'target': name,
                      'width_mm': mm(width), 'path_mm': [[mm(v) for v in p] for p in points]})
    if fixed or pruned:
        board.BuildConnectivity()
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    unresolved, checked = overlap_only_joints(board, copper_shapes(board))
    return {'detected': detected, 'pruned': pruned, 'fixed': fixed, 'skipped': skipped,
            'unresolved': unresolved, 'track_endpoints_checked': checked,
            'dangling_cleanup_required': bool(pruned),
            'native_drc_required': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.board.resolve() == args.output.resolve():
        raise SystemExit('Use a distinct output path')
    board = pcbnew.LoadBoard(str(args.board))
    report = repair(board)
    pcbnew.SaveBoard(str(args.output), board, True)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
