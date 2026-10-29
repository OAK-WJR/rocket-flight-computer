#!/usr/bin/env python3
"""Bounded fixed-copper routing between native connected clusters.

Always work in a new output directory. Existing copper and pads are immutable;
each accepted route passes native DRC and preserves every connected pad group.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r5_finish
import r5_maze
import r5_route
import r6_route

LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu)
DEFAULT_NETS = ('GPS_TX_MCU', 'RADIO_RX_MCU', 'RADIO_AUX_MCU', 'BUZZ_DRV')
DANGLING = {'track_dangling', 'via_dangling'}


def uid(item):
    return item.m_Uuid.AsString()


def clusters(board, net):
    connection = board.GetConnectivity()
    pads = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() == net]
    seen, result = set(), []
    for pad in pads:
        if uid(pad) in seen:
            continue
        items = {uid(pad): pad}
        for item in connection.GetConnectedItems(pad):
            if item.GetNetname() == net and item.GetClass() in ('PAD', 'PCB_TRACK', 'PCB_VIA'):
                items[uid(item)] = item
        seen.update(items)
        result.append(list(items.values()))
    return result


def pad_groups(board):
    board.BuildConnectivity()
    nets = {p.GetNetname() for f in board.GetFootprints() for p in f.Pads() if p.GetNetname()}
    return [frozenset(uid(p) for p in group if p.GetClass() == 'PAD')
            for net in sorted(nets) for group in clusters(board, net)]


def split_groups(before, after):
    membership = {pad: group for group in after for pad in group}
    return [sorted(group) for group in before if not group <= membership.get(next(iter(group)), frozenset())]


def anchors(group):
    vias = [item for item in group if item.GetClass() == 'PCB_VIA']
    items = vias or [item for item in group if item.GetClass() == 'PAD']
    return [(uid(item), (pcbnew.ToMM(item.GetPosition().x), pcbnew.ToMM(item.GetPosition().y)),
             set(LAYERS) if item.GetClass() == 'PCB_VIA' else
             {layer for layer in LAYERS if item.IsOnLayer(layer)}) for item in items]


def nearest_pairs(board, net):
    board.BuildConnectivity()
    groups = [anchors(group) for group in clusters(board, net)]
    pairs = []
    for i, first in enumerate(groups):
        for second in groups[i + 1:]:
            for a in first:
                for c in second:
                    pairs.append((math.dist(a[1], c[1]), a, c))
    return sorted(pairs, key=lambda pair: (pair[0], pair[1][1], pair[2][1]))


def native_drc(path, report):
    result = subprocess.run([r5_finish.CLI, 'pcb', 'drc', '--format', 'json', '-o', str(report), str(path)],
                            capture_output=True, text=True, timeout=90)
    if not report.exists():
        raise RuntimeError('Native DRC did not produce a report: ' + result.stderr[-1500:])
    data = json.loads(report.read_text())
    signatures = Counter((v['type'], tuple(sorted(item['uuid'] for item in v['items'])))
                         for v in data['violations'] if v['type'] not in DANGLING)
    return data, signatures


def deadline(_signum, _frame):
    raise TimeoutError('routing search deadline')


def search(board, net, first, second, seconds, margin=4):
    old_zones = {uid(zone) for zone in board.Zones()}
    r5_route.reference_keepouts(board)
    added = {uid(zone) for zone in board.Zones()} - old_zones
    handler = signal.signal(signal.SIGALRM, deadline)
    try:
        signal.setitimer(signal.ITIMER_REAL, seconds)
        return r5_maze.maze_multi(board, net, LAYERS, first[1], second[1],
                                 w=r5_finish.width(net), a_layers=first[2], c_layers=second[2],
                                 margin=margin, rip=None, via_cost=10)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, handler)
        for zone in list(board.Zones()):
            if uid(zone) in added:
                board.Delete(zone)


def copper_record(item):
    if item.GetClass() == 'PCB_VIA':
        return {'uuid': uid(item), 'net': item.GetNetname(), 'kind': 'via',
                'at': [pcbnew.ToMM(item.GetPosition().x), pcbnew.ToMM(item.GetPosition().y)],
                'diameter': pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)), 'drill': pcbnew.ToMM(item.GetDrill())}
    return {'uuid': uid(item), 'net': item.GetNetname(), 'kind': 'track', 'layer': item.GetLayer(),
            'start': [pcbnew.ToMM(item.GetStart().x), pcbnew.ToMM(item.GetStart().y)],
            'end': [pcbnew.ToMM(item.GetEnd().x), pcbnew.ToMM(item.GetEnd().y)],
            'width': pcbnew.ToMM(item.GetWidth())}


def run(source, output, nets, seconds=20, attempts=3, margin=4):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output directory must be new or empty')
    output.mkdir(parents=True, exist_ok=True)
    target = output / source.name
    for suffix in ('.kicad_pro', '.kicad_dru'):
        companion = source.with_suffix(suffix)
        if companion.exists():
            shutil.copy2(companion, target.with_suffix(suffix))
    for name in ('fp-lib-table', 'sym-lib-table'):
        if (source.parent / name).exists():
            shutil.copy2(source.parent / name, output / name)
    if (source.parent / 'kilib').exists():
        (output / 'kilib').symlink_to(source.parent / 'kilib', target_is_directory=True)
    shutil.copy2(source, target)
    source_sha = hashlib.sha256(target.read_bytes()).hexdigest()
    board = pcbnew.LoadBoard(str(target))
    r6_route.configure(board)
    r5_maze.MARGIN = .02
    r5_finish.UUID_SEED = None
    original_ids = {uid(item) for item in board.GetTracks()}
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(target), board, True)
    report, signatures = native_drc(target, output / 'baseline.json')
    initial_open = len(report['unconnected_items'])
    log = []
    for net in nets:
        tried = set()
        for attempt in range(attempts):
            pairs = [pair for pair in nearest_pairs(board, net)
                     if tuple(sorted((pair[1][0], pair[2][0]))) not in tried]
            if not pairs:
                break
            distance, first, second = pairs[0]
            tried.add(tuple(sorted((first[0], second[0]))))
            entry = {'net': net, 'attempt': attempt + 1, 'start': first[1], 'end': second[1],
                     'distance': distance, 'opens_before': len(report['unconnected_items'])}
            before_groups = pad_groups(board)
            start = time.monotonic()
            print('Search', net, first[1], second[1], flush=True)
            try:
                runs, vias = search(board, net, first, second, seconds, margin)
            except (RuntimeError, TimeoutError) as error:
                entry.update(status='no route', reason=str(error), seconds=time.monotonic() - start)
                log.append(entry)
                print(entry, flush=True)
                continue
            entry['seconds'] = time.monotonic() - start
            entry['route_runs'] = runs
            entry['route_vias'] = vias
            r5_finish.draw(board, net, runs, vias, r5_finish.width(net))
            pcbnew.ZONE_FILLER(board).Fill(board.Zones())
            candidate = output / 'candidate.kicad_pcb'
            # Same basename uses the copied project and custom rules during DRC.
            checkpoint = output / 'checkpoint.kicad_pcb'
            shutil.copy2(target, checkpoint)
            pcbnew.SaveBoard(str(target), board, True)
            new_report, new_signatures = native_drc(target, output / f'candidate-{len(log)}.json')
            splits = split_groups(before_groups, pad_groups(board))
            new_faults = list((new_signatures - signatures).elements())
            improved = len(new_report['unconnected_items']) < len(report['unconnected_items'])
            entry.update(opens_after=len(new_report['unconnected_items']), new_faults=new_faults,
                         split_pad_groups=splits, status='accepted' if improved and not new_faults and not splits else 'rejected')
            if entry['status'] == 'accepted':
                report, signatures = new_report, new_signatures
                shutil.copy2(target, candidate)
            else:
                shutil.copy2(checkpoint, target)
                board = pcbnew.LoadBoard(str(target))
            checkpoint.unlink()
            log.append(entry)
            print(entry, flush=True)
    delta = [copper_record(item) for item in board.GetTracks() if uid(item) not in original_ids]
    result = {'source': str(source), 'source_sha256': source_sha, 'candidate': str(target), 'opens_before': initial_open,
              'opens_after': len(report['unconnected_items']), 'attempts': log, 'added_copper': delta}
    (output / 'routes.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'opens_before': initial_open,
                      'opens_after': result['opens_after'], 'added_items': len(delta)}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', default='m3_design/assembly_review/m3.kicad_pcb')
    parser.add_argument('--out-dir')
    parser.add_argument('--nets', nargs='+', default=DEFAULT_NETS)
    parser.add_argument('--seconds', type=float, default=20)
    parser.add_argument('--attempts', type=int, default=3)
    parser.add_argument('--margin', type=float, default=4)
    args = parser.parse_args()
    directory = args.out_dir or tempfile.mkdtemp(prefix='r6-selected-', dir='/private/tmp')
    run(args.source, directory, args.nets, args.seconds, args.attempts, args.margin)


if __name__ == '__main__':
    main()
