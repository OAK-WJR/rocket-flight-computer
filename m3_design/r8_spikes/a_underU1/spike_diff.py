import json, sys
a, b = sys.argv[1], sys.argv[2]
def drc(p):
    r = json.load(open(p + '/drc.json'))
    out = set()
    for v in r['violations']:
        if v['type'] in ('silk_over_copper', 'silk_overlap', 'silk_edge_clearance', 'lib_footprint_issues'):
            continue
        out.add((v['type'], ' || '.join(sorted(i['description'] + ' @%.2f,%.2f' % (i['pos']['x'], i['pos']['y']) for i in v['items']))))
    un = set(' || '.join(sorted(i['description'] for i in v['items'])) for v in r['unconnected_items'])
    return out, un
def rc(p):
    r = json.load(open(p + '/rc.json'))
    f = set((d['cat'], d['net'], d.get('layer'), round(d['x'], 2), round(d['y'], 2)) for d in r['failures'])
    i = set((d['cat'], d['net'], d.get('layer'), round(d['x'], 2), round(d['y'], 2)) for d in r['instances'])
    return f, i
(da, ua), (db, ub) = drc(a), drc(b)
print('DRC violations new in', b, len(db - da)); [print('  +', x) for x in sorted(db - da)]
print('DRC violations gone', len(da - db)); [print('  -', x) for x in sorted(da - db)]
print('unconnected: seed', len(ua), b, len(ub), 'new', len(ub - ua))
for x in sorted(ub - ua): print('  +', x)
(fa, ia), (fb, ib) = rc(a), rc(b)
print('route_check failures new', len(fb - fa)); [print('  +', x) for x in sorted(fb - fa)]
print('route_check instances new', len(ib - ia)); [print('  +', x) for x in sorted(ib - ia)]
