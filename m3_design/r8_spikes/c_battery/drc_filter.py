#!/usr/bin/env python3
"""Filter a kicad-cli DRC JSON report to the spike's nets and area (plain Python).

usage: python3 drc_filter.py DRC.json [--all]
A violation counts when any of its items names a spike net, or (for net-less items: courtyards, holes, silkscreen)
lies inside the band area. lib_footprint_issues and silkscreen classes are listed separately (not copper DRC).
Unconnected items count when either end is on a spike net. Exit 1 when any copper violation or unconnected item
counts.
"""
import json
import re
import sys
from collections import Counter

SPIKE_NETS = {'BAT_IN', 'BAT_DAMP', 'ACT_FET_S', 'RAW_ACT', 'ACT_GATE', 'ACT_DRV', 'ACT_EN', 'BAT_SW_SOURCE',
              'BAT_SW_RETURN', 'RAW_ACT_SENSE_MID'}
AREA = (0.0, 66.5, 46.0, 118.0)           # the band: J122 forward to the forward edge
NON_COPPER = {'lib_footprint_issues', 'lib_footprint_mismatch', 'silk_over_copper', 'silk_overlap',
              'silk_edge_clearance', 'text_height', 'text_thickness'}
NET_RE = re.compile(r'\[([^\]]+)\]')
# footprints the spike places (battery.py PLACE); a courtyard overlap counts only when one of these is involved
_SRC = open(__file__.replace('drc_filter.py', 'battery.py')).read()
BAND_PARTS = set(re.findall(r"^\s+'([A-Z]+\d+)': \(", _SRC[_SRC.index('PLACE = {'):_SRC.index('POUR =')], re.M))
FP_RE = re.compile(r'^Footprint (\S+)')


def nets_of(item):
    return set(NET_RE.findall(item.get('description', '')))


def in_area(item):
    p = item.get('pos') or {}
    x, y = p.get('x'), p.get('y')
    return x is not None and AREA[0] <= x <= AREA[2] and AREA[1] <= y <= AREA[3]


def relevant(v, gnd_in_area=True):
    if v.get('type') == 'courtyards_overlap':
        refs = {m.group(1) for it in v['items'] for m in [FP_RE.match(it.get('description', ''))] if m}
        return bool(refs & BAND_PARTS)
    for it in v['items']:
        n = nets_of(it)
        if n & SPIKE_NETS:
            return True
        if gnd_in_area and 'GND' in n and in_area(it):
            return True
    if all(not nets_of(it) or nets_of(it) <= {'<no net>'} for it in v['items']):
        return any(in_area(it) for it in v['items'])
    return False


def main(path, show_all=False):
    d = json.load(open(path))
    copper, other = [], []
    for v in d['violations']:
        if not relevant(v):
            continue
        (other if v['type'] in NON_COPPER else copper).append(v)
    unc = [u for u in d.get('unconnected_items', []) if relevant(u)]
    print(f'copper violations on spike nets / band area: {len(copper)} {dict(Counter(v["type"] for v in copper))}')
    for v in copper:
        print(f'  {v["type"]}: {v["description"]}')
        for it in v['items']:
            print(f'      {it["description"]} @ ({it["pos"]["x"]:.3f}, {it["pos"]["y"]:.3f})')
    print(f'unconnected items on spike nets (and GND in the band): {len(unc)}')
    for u in unc:
        print('  ' + ' | '.join(f'{it["description"]} @ ({it["pos"]["x"]:.2f}, {it["pos"]["y"]:.2f})'
                                for it in u['items']))
    print(f'non-copper (silk / library) in the band: {len(other)} {dict(Counter(v["type"] for v in other))}')
    if show_all:
        for v in other:
            print(f'  {v["type"]}: ' + ' | '.join(it['description'] for it in v['items']))
    return 1 if copper or unc else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], '--all' in sys.argv))
