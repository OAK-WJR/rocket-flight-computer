"""Offline, self-contained bench report. All evidence text is HTML-escaped."""
from html import escape
import json


def esc(value):
    return escape(str(value),quote=True)


def point_id(endpoint):
    return 'point-'+endpoint.replace('.','-')


def board_svg(mapping, groups):
    x0,y0,x1,y1=mapping['bounds_mm'];w=x1-x0;h=y1-y0
    active={p for g in groups for p in g['points']}
    parts={'J1','J2','J3','J9','U1','U2','U3','U4','U5','U6','U7','U8','U9','U10','U11','U12','U13','L1','L2'}
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0-5} {y0-7} {w+10} {h+14}" role="img" aria-label="M3 PCB top-side probe locations">',
        '<title>M3-ASSY-R1 TOP · saved pad centres in mm</title>',
        '<style>text{font-family:Arial,sans-serif}a:hover circle{stroke:#111;stroke-width:.6}</style>',
        f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="1" fill="#eaf3ee" stroke="#27634b" stroke-width=".4"/>',
        f'<text x="{x0}" y="{y0-2.5}" font-size="2.3" fill="#23374d">TOP · x → · y ↓</text>']
    for ref,p in mapping['components'].items():
        if ref not in parts:continue
        x,y=p['xy_mm']
        lines.append(f'<g><title>{esc(ref+" "+p["value"])}</title><rect x="{x-1.8}" y="{y-1.3}" width="3.6" height="2.6" rx=".3" fill="#cedbd2"/>'
                     f'<text x="{x}" y="{y+.55}" text-anchor="middle" font-size="1.5" fill="#4f655b">{esc(ref)}</text></g>')
    for i,(endpoint,p) in enumerate(mapping['points'].items(),1):
        x,y=p['xy_mm'];color='#64748b' if p['net']=='GND' else '#b84616' if endpoint in active else '#1469a0'
        label=f'{endpoint} · {p["net"]} · ({x:.3f}, {y:.3f}) mm · GND {p["ground"]}'
        dx=-1.2 if x>x1-6 else 1.2;anchor='end' if dx<0 else 'start'
        dy=.6
        if endpoint in ('J2.4','J2.5'):dx,dy,anchor=0,-1.3,'middle'
        if endpoint=='R61.1':dy=-.5
        lines.append(f'<a href="#{point_id(endpoint)}"><title>{esc(label)}</title><circle cx="{x}" cy="{y}" r=".7" fill="{color}" stroke="white" stroke-width=".2"/>'
                     f'<text x="{x+dx}" y="{y+dy}" text-anchor="{anchor}" font-size="1.65" fill="{color}">{i:02}</text></a>')
    lines.append(f'<text x="{x0}" y="{y1+4}" font-size="2" fill="#23374d">{w:g} × {h:g} mm · centres only</text></svg>')
    return ''.join(lines)


def html_report(report,mapping,svg):
    synthetic=report['synthetic'];failed=sum(c['status']=='FAIL' for c in report['checks'])
    pending=sum(c['status'] in ('NOT_TESTED','INCONCLUSIVE','RUNNING') for c in report['checks'])
    status='Issues found' if failed else 'Evidence still incomplete'
    origin='Synthetic demo · not real-board data' if synthetic else 'Bench record · not a whole-board pass'
    meter=report['synthetic_meter_observations']+report['physical_meter_observations']
    measured={p['probe']:p['measurement'] for p in meter}
    def links(points):
        return ' → '.join(f'<a href="#{point_id(p)}">{esc(p)} <small>{esc(mapping["points"][p]["net"])}</small></a>' for p in points)
    cards=[]
    for i,g in enumerate(report['investigations'],1):
        cards.append(f'<article class="investigation"><div class="eyebrow">Check order {i:02}</div><h3>{esc(g["title"])}</h3>'
                     f'<p>{esc(g["action"])}</p><p class="route">{links(g["points"])}</p>'
                     f'<p class="muted">Related references: {esc(", ".join(g["components"]))}<br>Triggering evidence: {esc(" / ".join(g["reasons"]))}</p></article>')
    if not cards:cards=['<p>The current evidence triggered no branch fault check. The untested items below and real-board measurements are still needed.</p>']
    point_rows=[]
    for i,(endpoint,p) in enumerate(mapping['points'].items(),1):
        x,y=p['xy_mm'];gx,gy=p['ground_xy_mm'];q=measured.get(endpoint)
        reading=f'{q["value"]:g} ± {q["uncertainty_v"]:g} V' if q else 'not measured'
        detail=f'{q["instrument"]} · {q["measured_at"]} · Rin {q["input_ohm"]:g} Ω' if q else ''
        kind='test pad' if p['dedicated_testpad'] else 'component pad'
        point_rows.append(f'<tr id="{point_id(endpoint)}"><td>{i:02}</td><td><strong>{esc(endpoint)}</strong><small>{kind}</small></td>'
                          f'<td>{esc(p["net"])}</td><td>{x:.3f}, {y:.3f}</td><td>{esc(p["ground"])}<small>{gx:.3f}, {gy:.3f}</small></td>'
                          f'<td>{esc(reading)}<small>{esc(detail)}</small></td></tr>')
    check_rows=[]
    for c in report['checks']:
        text=c.get('evidence','')
        if not isinstance(text,str):text=json.dumps(text,ensure_ascii=False)
        check_rows.append(f'<tr><td><code>{esc(c["id"])}</code></td><td><span class="badge {esc(c["status"])}">{esc(c["status"])}</span></td>'
                          f'<td>{esc(text)}<small>{esc(c.get("next_step",""))}</small></td></tr>')
    error=f'<p class="error"><strong>Capture error</strong><br>{esc(report["capture_error"])}</p>' if report['capture_error'] else ''
    return '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'">
<title>M3 bench diagnostics and test-point map</title><style>
:root{color-scheme:light;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif;color:#182d40;background:#f2f5f7;font-size:15px}
*{box-sizing:border-box}body{margin:0}main{max-width:1440px;margin:auto;padding:32px}h1{font-size:32px;letter-spacing:-.6px;margin:8px 0}h2{font-size:22px;margin:0 0 16px}h3{font-size:19px;margin:6px 0 10px}
p{line-height:1.7;margin:10px 0}a{color:#1267a0;text-decoration-thickness:1px;text-underline-offset:3px}header,.panel{background:white;border:1px solid #d9e2e8;border-radius:12px;padding:26px;margin-bottom:20px}
.eyebrow{font-size:12px;color:#496276;letter-spacing:.8px}.notice{background:#fff1d3;color:#664200;padding:10px 14px;border-radius:6px;font-weight:650}.error{background:#fff0ea;color:#8b2e10;padding:14px;border-radius:6px;overflow-wrap:anywhere}
.stats{display:flex;gap:14px;flex-wrap:wrap;margin:18px 0}.stat{min-width:150px;background:#eff4f7;padding:12px 16px;border-radius:8px}.stat b{display:block;font-size:23px;margin-top:4px}.muted,small{color:#526a7c;font-size:12px}small{display:block;line-height:1.55;margin-top:4px}
.layout{display:grid;grid-template-columns:minmax(235px,280px) 1fr;gap:24px;align-items:start}.board{position:sticky;top:12px}.board svg{width:100%;height:auto;display:block;max-height:1000px}.investigation{padding:18px 0;border-bottom:1px solid #dce4eb}.investigation:first-child{padding-top:0}.investigation:last-child{border-bottom:0}.route{font-size:13px;line-height:2}.route a{display:inline-block}.route small{display:inline;font-size:11px}
.tablewrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px}th{text-align:left;background:#eef3f6;color:#3f596b;font-weight:600}th,td{padding:12px 10px;vertical-align:top;border-bottom:1px solid #e0e7ec}tr:target{background:#fff0cd;outline:2px solid #d08b18}code{font-size:12px;overflow-wrap:anywhere}.badge{display:inline-block;border:1px solid #cdd8df;border-radius:5px;padding:3px 6px;font-size:11px}.FAIL{background:#ffe4df;border-color:#f6b7a9;color:#8b2e10}.PASS{background:#e6f1eb;color:#255840}.INCONCLUSIVE,.WARNING{background:#fff2d8;color:#6c4c06}
.hash{font-family:monospace;overflow-wrap:anywhere;font-size:12px}summary{cursor:pointer;font-weight:600;padding:4px 0}footer{color:#526a7c;line-height:1.7;padding:0 6px 24px;font-size:13px}@media(max-width:760px){main{padding:14px}.layout{grid-template-columns:1fr}.board{position:static}.board svg{max-height:780px}header,.panel{padding:18px}h1{font-size:26px}}@media print{body{background:white}.board{position:static}.panel,header{border-radius:0}main{padding:0}.layout{display:block}.board svg{max-height:900px}.board{break-after:page}tr{break-inside:avoid}}
</style></head><body><main>''' + f'''
<header><div class="eyebrow">M3-ASSY-R1 · bench diagnostics</div><h1>{status}</h1><div class="notice">{origin}</div>
<div class="stats"><div class="stat">Capture state<b>{esc(report['capture_state'])}</b></div><div class="stat">Explicit failures<b>{failed}</b></div><div class="stat">Incomplete / insufficient<b>{pending}</b></div><div class="stat">Located test points<b>{len(mapping['points'])}</b></div></div>
<p>Assembly ID <strong>{esc(report['assembly_id'])}</strong> · {esc(report['captured_at'])}<br><small>Record {esc(report['capture_id'])}</small></p>{error}
<p class="muted">Check power first, then communication and devices. These are troubleshooting branches and cannot uniquely identify a broken chip; missing readings never count as a pass.</p>
</header><div class="layout"><aside class="panel board"><h2>Test-point map</h2>{svg}<p class="muted">Component side TOP, x right, y down, in mm. Numbers match the table below; hover for the net, click to jump to the row. Orange marks branches to check, grey is ground. The map shows pad / part centres, not footprint outlines or copper.</p></aside>
<section class="panel"><h2>Next checks</h2>{''.join(cards)}</section></div>
<section class="panel"><h2>Test points and instrument records</h2><p class="muted">External instrument values are kept separate from the on-board ADC. Prefer dedicated test pads; component pads need a fine probe without bridging neighbours. The ground in the table must match the current board.</p><div class="tablewrap"><table><thead><tr><th>No.</th><th>Pad</th><th>Net</th><th>x, y / mm</th><th>Reference ground / mm</th><th>Independent meter reading</th></tr></thead><tbody>{''.join(point_rows)}</tbody></table></div></section>
<section class="panel"><details open><summary>All sub-checks and the evidence behind each judgement</summary><p class="muted">PASS applies only to its own row. The overall result is always INCOMPLETE or ISSUES_FOUND. On-board sample values and raw bytes are in report.json / capture.json in the same directory.</p><div class="tablewrap"><table><thead><tr><th>Check</th><th>Result</th><th>Evidence and next action</th></tr></thead><tbody>{''.join(check_rows)}</tbody></table></div></details></section>
<section class="panel"><h2>Versions and evidence</h2><p>PCB</p><p class="hash">{esc(report['board_sha256'])}</p><p>Firmware build</p><p class="hash">{esc(report['build_sha256'])}</p><p class="muted">capture.json in the same directory keeps every exchange and partially received bytes, probe_map.json holds the board coordinates, and bench_template.json's measurement fields default to empty. Meter readings from different supply configurations must never be compared as a pair. Identities and hashes are for linking and consistency checks, not chip authentication.</p></section>
<footer>This report covers ordinary bench power, acquisition, storage and communication diagnostics. Transients, temperature rise, real assembly, sensor accuracy and the real watchdog still need real-board verification. This tool never flashes, resets, clears history or switches power; full rocket function and flight verification are not complete.</footer>
</main></body></html>'''
