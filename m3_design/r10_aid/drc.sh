#!/bin/bash
# drc.sh board.kicad_pcb(named m3 inside a project dir) : summary of non-silk violations except dangling vias
CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli; J=$(dirname $1)/drc_out.json
$CLI pcb drc --severity-all --format json -o $J $1 >/dev/null 2>&1
python3 - $J "$2" <<'PY'
import json,sys,collections,re
d=json.load(open(sys.argv[1])); flt=sys.argv[2]
nets=collections.Counter()
for u in d['unconnected_items']:
    for i in u['items']:
        m=re.search(r'\[([^\]]+)\]',i['description'])
        if m: nets[m.group(1)]+=1; break
v=[x for x in d['violations'] if 'silk' not in x['type'] and x['type']!='via_dangling' and x['type']!='lib_footprint_issues']
print(len(d['unconnected_items']),'unconnected in',len(nets),'nets;',len(v),'violations;', sum(1 for x in d['violations'] if x['type']=='via_dangling'),'dangling vias')
for x in v:
    s=' / '.join(i['description'][:58] for i in x['items'])
    if not flt or re.search(flt,s): print(' ',x['type'],'|',s, '|', x['description'][-28:])
PY
