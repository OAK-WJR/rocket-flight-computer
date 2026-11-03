#!/usr/bin/env python3
"""Place R6 exposed test pads without moving circuitry; caller owns routing/refill.

repair(board) changes only the supplied in-memory board and returns an audit log.
Standalone use requires a distinct --output path; it never overwrites the source.
Filled zones are ignored while locating pads and must be refilled afterwards.
"""
import argparse
import json
import math
from pathlib import Path
import re
import sys

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from fit_check import board_geometry, RETENTION_HOLES

MM, mm = pcbnew.FromMM, pcbnew.ToMM
GAP = 1.0
STEP = 0.5
CELL = 4.0


def point(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def xy(p):
    return mm(p.x), mm(p.y)


class Index:
    def __init__(self):
        self.items, self.cells = [], {}

    def keys(self, box, extra=0):
        x0, y0 = math.floor((mm(box.GetX()) - extra) / CELL), math.floor((mm(box.GetY()) - extra) / CELL)
        x1, y1 = math.floor((mm(box.GetRight()) + extra) / CELL), math.floor((mm(box.GetBottom()) + extra) / CELL)
        return ((x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1))

    def add(self, shape, kind, name, net='', owner=None):
        index = len(self.items)
        self.items.append((shape, kind, name, net, owner))
        for key in self.keys(shape.BBox()):
            self.cells.setdefault(key, []).append(index)

    def near(self, shape, extra=0):
        found = {index for key in self.keys(shape.BBox(), extra) for index in self.cells.get(key, ())}
        return (self.items[index] for index in found)


def obstacles(board, target, layer):
    hard, copper = Index(), Index()
    courtyard_layer = pcbnew.B_CrtYd if layer == pcbnew.B_Cu else pcbnew.F_CrtYd
    for f in board.GetFootprints():
        if f == target:
            continue
        for pad in f.Pads():
            if pad.IsOnLayer(layer):
                hard.add(pad.GetEffectiveShape(layer), 'pad', f'{f.GetReference()}.{pad.GetNumber()}',
                         pad.GetNetname(), pad)
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                hard.add(pad.GetEffectiveHoleShape(), 'hole', f'{f.GetReference()}.{pad.GetNumber()}', '', pad)
        f.BuildCourtyardCaches()
        court = f.GetCourtyard(courtyard_layer)
        if court.OutlineCount():
            hard.add(court, 'courtyard', f.GetReference(), owner=f)
    for track in board.GetTracks():
        if track.IsOnLayer(layer):
            copper.add(track.GetEffectiveShape(layer), 'track', track.m_Uuid.AsString(), track.GetNetname(), track)
    for zone in board.Zones():
        if zone.GetIsRuleArea() and zone.IsOnLayer(layer) and (zone.GetDoNotAllowPads() or zone.GetDoNotAllowFootprints()):
            hard.add(zone.Outline(), 'keepout', zone.GetZoneName(), owner=zone)
    return hard, copper


def translated(shape, delta):
    result = shape.Clone()
    result.Move(delta)
    return result


def candidate_positions(origin, outline):
    """Nearest grid candidates first, with an exact unchanged candidate first."""
    x0, y0, x1, y1 = outline
    positions = [(origin[0], origin[1])]
    positions += [(x * STEP, y * STEP)
                  for x in range(math.ceil((x0 + 1.1) / STEP), math.floor((x1 - 1.1) / STEP) + 1)
                  for y in range(math.ceil((y0 + 1.1) / STEP), math.floor((y1 - 1.1) / STEP) + 1)
                  if (x * STEP, y * STEP) != origin]
    positions.sort(key=lambda p: (math.dist(p, origin), p))
    return positions


def old_leadouts(board, pad, layer):
    """Only same-net conductors directly touching the original pad are detached."""
    shape = pad.GetEffectiveShape(layer)
    found = []
    for track in board.GetTracks():
        if track.GetNetname() != pad.GetNetname() or not track.IsOnLayer(layer):
            continue
        ends = [track.GetPosition()] if track.GetClass() == 'PCB_VIA' else [track.GetStart(), track.GetEnd()]
        width = track.GetWidth(layer) if track.GetClass() == 'PCB_VIA' else track.GetWidth()
        if any(shape.Collide(end, width // 2) for end in ends):
            found.append(track)
    return found


def describe(track, reason):
    return dict(uuid=track.m_Uuid.AsString(), net=track.GetNetname(), kind=track.GetClass(),
                start_mm=xy(track.GetPosition() if track.GetClass() == 'PCB_VIA' else track.GetStart()),
                end_mm=None if track.GetClass() == 'PCB_VIA' else xy(track.GetEnd()), reason=reason)


def repair(board):
    holes, outline = board_geometry(board)
    board_shape = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(board_shape, False):
        raise RuntimeError('Cannot determine board boundary for test-pad placement')
    targets = sorted((f for f in board.GetFootprints() if re.fullmatch(r'TP\d+', f.GetReference())),
                     key=lambda f: int(f.GetReference()[2:]))
    result = dict(moved=[], retained=[], ripped=[], unplaced=[], clearance_mm=GAP,
                  zones_require_refill=True, reroute_required=False)
    for f in targets:
        pads = list(f.Pads())
        if len(pads) != 1 or pads[0].GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            raise RuntimeError(f'{f.GetReference()}: expected one bare SMD test pad')
        pad = pads[0]
        layer = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
        original = f.GetPosition()
        origin = xy(original)
        original_pad = pad.GetEffectiveShape(layer)
        f.BuildCourtyardCaches()
        original_court = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
        if not original_court.OutlineCount():
            raise RuntimeError(f'{f.GetReference()}: missing courtyard')
        hard, copper = obstacles(board, f, layer)
        chosen, best_rip = None, None
        for position in candidate_positions(origin, outline):
            delta = point(position[0] - origin[0], position[1] - origin[1])
            shape = translated(original_pad, delta)
            court = translated(original_court, delta)
            bounds = court.BBox()
            # Corners plus middle of edges keep the complete rectangular TP courtyard inside
            # the real rounded board outline; extra 0.15 mm exceeds the 0.3 mm pad-to-edge rule.
            x0, y0, x1, y1 = (mm(bounds.GetX()) - .15, mm(bounds.GetY()) - .15,
                               mm(bounds.GetRight()) + .15, mm(bounds.GetBottom()) + .15)
            if not all(board_shape.Contains(point(x, y)) for x in (x0, (x0 + x1) / 2, x1)
                       for y in (y0, (y0 + y1) / 2, y1)):
                continue
            # Clearance to support hardware is physical, rather than only to the 3.2 mm bore.
            if any(math.dist(position, h) < (2.85 if h in RETENTION_HOLES else 4.6) for h in holes):
                continue
            blocked = False
            for other, kind, name, net, owner in hard.near(shape, GAP + .4):
                if kind == 'courtyard':
                    collision = court.Collide(other, MM(.05))
                else:
                    gap = GAP if kind == 'pad' and (net != pad.GetNetname() or name.startswith('TP')) else .3
                    collision = shape.Collide(other, MM(gap) - 1000)
                if collision:
                    blocked = True
                    break
            if blocked:
                continue
            rip = [owner for other, kind, name, net, owner in copper.near(shape, GAP)
                   if net != pad.GetNetname() and shape.Collide(other, MM(GAP) - 1000)]
            if not rip:
                chosen = (position, [])
                break
            score = (len(rip), math.dist(position, origin))
            if best_rip is None or score < best_rip[0]:
                best_rip = (score, position, rip)
        if chosen is None and best_rip:
            chosen = (best_rip[1], best_rip[2])
        if chosen is None:
            result['unplaced'].append(f.GetReference())
            continue
        position, rip = chosen
        moving = math.dist(position, origin) > 1e-6
        detached = old_leadouts(board, pad, layer) if moving else []
        by_uuid = {track.m_Uuid.AsString(): (track, 'old test-pad leadout') for track in detached}
        by_uuid.update({track.m_Uuid.AsString(): (track, 'foreign copper within 1 mm of selected test pad') for track in rip})
        for track, reason in by_uuid.values():
            result['ripped'].append(dict(testpad=f.GetReference(), **describe(track, reason)))
            board.Delete(track)
        if moving:
            f.SetPosition(point(*position))
            result['moved'].append(dict(ref=f.GetReference(), net=pad.GetNetname(), side='B' if f.IsFlipped() else 'F',
                                        old_mm=origin, new_mm=position, distance_mm=math.dist(position, origin),
                                        detached_own=len(detached), ripped_foreign=len(rip)))
        else:
            result['retained'].append(f.GetReference())
        pad.SetLocalClearance(MM(GAP))
    result['reroute_required'] = bool(result['moved'] or result['ripped'])
    result['ok'] = not result['unplaced']
    print(f"R6 test pads: {len(result['moved'])} moved, {len(result['retained'])} retained, "
          f"{len(result['ripped'])} directly affected conductors removed, {len(result['unplaced'])} unplaced")
    for row in result['moved']:
        print(f"  {row['ref']} {row['side']}: {row['old_mm']} -> {row['new_mm']} ({row['distance_mm']:.2f} mm); "
              f"detach {row['detached_own']}, foreign rip {row['ripped_foreign']}")
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    if args.board.resolve() == args.output.resolve():
        ap.error('--output must differ from the input board')
    b = pcbnew.LoadBoard(str(args.board))
    report = repair(b)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    if not report['ok']:
        return 1
    pcbnew.SaveBoard(str(args.output), b, True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
