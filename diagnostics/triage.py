"""M3-ASSY-R1 bounded snapshot capture, saved-PCB probe map and bench triage.

This host entry makes only the existing snapshot request. A report can narrow
an investigation to a circuit branch; it cannot certify or uniquely diagnose
physical hardware. No PCB, firmware or existing evidence is overwritten.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import struct
import sys
import time
import zlib

from .engine import load_json, analyze_bench, number
from .mailbox import ASSEMBLY_PROTOCOL, manifest_protocol, analyze_mailbox
from .transport import atomic_json, utc
from .triage_map import ROOT, read_board, measurement_binding
from .triage_rules import investigations, GROUPS
from .usb import validate_manifest, serial_client, capture, request_bytes

DEFAULT_MANIFEST = ROOT/'m3_firmware/build_assembly_inspect/manifest.json'
DEFAULT_BOARD = ROOT/'m3_design/assembly_review/m3.kicad_pcb'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def document(path):
    if Path(path).stat().st_size > 2_000_000:
        raise ValueError('Evidence JSON exceeds 2 MB bound')
    return load_json(path)


def timestamp(value):
    if not isinstance(value, str) or len(value) > 80:
        raise ValueError('Timestamp required')
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('Timestamp must include timezone')
    return d


def identifier(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise ValueError('Nonempty assembly/capture ID up to 200 characters required')


def context(manifest=DEFAULT_MANIFEST, board=DEFAULT_BOARD):
    manifest, board = Path(manifest), Path(board)
    m = validate_manifest(document(manifest))
    if manifest_protocol(m) != ASSEMBLY_PROTOCOL:
        raise ValueError('Triage map is reviewed only for M3-ASSY-R1')
    for name in ('m3_bench.bin', 'm3_bench.elf'):
        if sha(manifest.parent/name) != m['artifacts'][name]:
            raise ValueError('Firmware artifact changed: '+name)
    original = document(manifest.parent/'binding.json')
    if original.get('profile') != m['profile'] or original.get('board_sha256') != m['board_sha256']:
        raise ValueError('Wrong measurement binding revision')
    mapping = read_board(board, m['board_sha256'])
    for net, probe in original['probes'].items():
        p = mapping['points'][probe['probe']]
        g = mapping['points'][probe['ground']]
        if (p['net'] != net or g['net'] != 'GND' or
                probe['board_xy_mm'] != p['xy_mm'] or probe['ground_xy_mm'] != g['xy_mm']):
            raise ValueError('Stale measurement binding: '+net)
    for group in GROUPS.values():
        if set(group['points'])-mapping['points'].keys() or set(group['components'])-mapping['components'].keys():
            raise ValueError('Investigation names an absent pad/component')
    return dict(manifest=m, binding=measurement_binding(mapping, original), mapping=mapping,
                sources=dict(manifest_sha256=sha(manifest), binding_sha256=sha(manifest.parent/'binding.json'),
                             board_sha256=sha(board), artifacts={n:m['artifacts'][n] for n in ('m3_bench.bin','m3_bench.elf')}))


def validate_capture(e):
    """Cross-check accepted words against the preserved CDC bytes as well as CRC.

    Hashes/CRCs are consistency checks, not authentication of the target or the
    operator. Partial/error bytes remain uninterpreted failure evidence.
    """
    if e.get('transport') != 'USB_CDC' or e.get('origin') not in ('USB_CAPTURE','SYNTHETIC_FIXTURE'):
        raise ValueError('This entry expects USB CDC evidence')
    identifier(e.get('assembly_id')); identifier(e.get('capture_id'))
    if timestamp(e['finished_at']) < timestamp(e['captured_at']):
        raise ValueError('Capture time order')
    expected = e.get('expected_samples')
    if type(expected) is not int or not 2 <= expected <= 30:
        raise ValueError('Capture sample bound')
    if not 1.2 <= number(e.get('interval_s'), 'interval_s') <= 10:
        raise ValueError('Capture interval bound')
    if e.get('state') not in ('CAPTURED','PARTIAL','CONNECTION_FAILED','CLEANUP_FAILED'):
        raise ValueError('Unfinished or unknown capture state')
    samples, exchanges = e.get('samples'), e.get('exchanges')
    if not isinstance(samples,list) or not isinstance(exchanges,list) or not len(samples) <= len(exchanges) <= expected:
        raise ValueError('Raw exchange/sample count')
    for i, sample in enumerate(samples):
        x = exchanges[i]
        if sample['accepted'] != 0 or len(sample['attempts']) != 1 or sample['attempts'][0]['error'] is not None:
            raise ValueError('Unknown accepted USB record')
        if (x['op'],x['address'],x['length']) != (1,0,1024):
            raise ValueError('Unexpected command in snapshot capture')
        tx, rx = bytes.fromhex(x['tx_hex']), bytes.fromhex(x['rx_hex'])
        if tx != request_bytes(1,x['request_id'],0,1024) or len(rx) != 1052 or x['error'] is not None:
            raise ValueError('Accepted record lacks complete raw exchange')
        if struct.unpack('<4sHHIIII',rx[:24]) != (b'M3RS',1,0,x['request_id'],0,1024,1):
            raise ValueError('Response header mismatch')
        if zlib.crc32(rx[:-4]) != struct.unpack('<I',rx[-4:])[0]:
            raise ValueError('Response CRC mismatch')
        if list(struct.unpack('<256I',rx[24:-4])) != sample['attempts'][0]['words']:
            raise ValueError('Decoded words disagree with preserved response')
    if e['state'] == 'CAPTURED' and (len(samples) != expected or e.get('error') is not None):
        raise ValueError('CAPTURED state contradicts preserved records')


def bench_template(e, ctx):
    return dict(schema=1,board_sha256=ctx['binding']['board_sha256'],assembly_id=e['assembly_id'],
        capture_id=e['capture_id'],origin='SYNTHETIC_FIXTURE' if e['origin']=='SYNTHETIC_FIXTURE' else 'MANUAL_BENCH',
        coordinate_frame=ctx['mapping']['coordinate_frame'],supply_configuration='',same_supply_configuration=None,
        points=[dict(net=net,**p,measurement=None) for net,p in ctx['binding']['probes'].items()])


def bench_checks(b, e, ctx):
    if b.get('coordinate_frame') != ctx['mapping']['coordinate_frame']:
        raise ValueError('Measurement coordinates must use the reviewed TOP view')
    rows = b.get('points')
    if not isinstance(rows,list): raise ValueError('Bench points must be a list')
    measured = []
    for row in rows:
        net = row.get('net'); expected = ctx['binding']['probes'].get(net)
        if expected is None or any(row.get(k) != expected[k] for k in ('probe','board_xy_mm','ground','ground_xy_mm')):
            raise ValueError('Measurement location/ground differs from saved PCB: '+str(net))
        if row.get('measurement') is not None:
            timestamp(row['measurement'].get('measured_at')); measured.append(row)
    if measured and (b.get('same_supply_configuration') is not True or
                     not isinstance(b.get('supply_configuration'),str) or not b['supply_configuration'].strip()):
        raise ValueError('Paired DC readings require an explicit unchanged supply configuration')
    checks=[]
    def add(code,status,evidence,next_step=''):
        checks.append(dict(id=code,status=status,evidence=evidence,next_step=next_step))
    analyze_bench(b,e,ctx['binding'],add)
    return checks,measured


def write_report(e, ctx, out, bench=None):
    from .triage_report import html_report, board_svg
    validate_capture(e)
    report = analyze_mailbox(e,ctx['binding'],ctx['manifest'])
    meter_checks, meter = bench_checks(bench,e,ctx) if bench is not None else bench_checks(bench_template(e,ctx),e,ctx)
    report['checks'].extend(meter_checks)
    out=Path(out)
    if document(out/'capture.json') != e:
        raise ValueError('Report input differs from preserved capture.json')
    sources=json.loads(json.dumps(ctx['sources']))
    sources['capture_sha256']=sha(out/'capture.json')
    if (out/'bench_input.json').exists():sources['bench_sha256']=sha(out/'bench_input.json')
    report.update(capture_state=e['state'],capture_error=e.get('error'),captured_at=e['captured_at'],
        overall='ISSUES_FOUND' if any(x['status']=='FAIL' for x in report['checks']) else 'INCOMPLETE',
        physical_meter_observations=meter if e['origin']!='SYNTHETIC_FIXTURE' else [],
        synthetic_meter_observations=meter if e['origin']=='SYNTHETIC_FIXTURE' else [],
        sources=sources,full_m3_complete=False,unique_failed_component=None,
        scope='Bounded bench snapshots and optional external DC observations; no flight qualification')
    report['investigations']=investigations(report,e['state'])
    status={c['id']:c['status'] for c in report['checks']}
    report['complete_live_capture']=(e['state']=='CAPTURED' and status.get('FIRMWARE_LIVENESS')=='PASS' and status.get('TEST_SEQUENCE')=='PASS')
    report['exit_code']=3 if not report['complete_live_capture'] else 2 if report['overall']=='ISSUES_FOUND' else 0
    atomic_json(out/'report.json',report)
    atomic_json(out/'probe_map.json',ctx['mapping'])
    atomic_json(out/'bench_template.json',bench_template(e,ctx))
    svg=board_svg(ctx['mapping'],report['investigations'])
    (out/'board.svg').write_text(svg,encoding='utf-8')
    (out/'report.html').write_text(html_report(report,ctx['mapping'],svg),encoding='utf-8')
    return report


def capture_report(factory, assembly, out, manifest=DEFAULT_MANIFEST, board=DEFAULT_BOARD,
                   samples=2, interval=1.2, pause=time.sleep, origin='USB_CAPTURE'):
    identifier(assembly)
    ctx=context(manifest,board)  # all identity checks before any serial I/O
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    e=capture(factory,ctx['manifest'],assembly,out/'capture.json',samples,interval,pause,origin)
    return write_report(e,ctx,out)


def offline_report(source,out,manifest=DEFAULT_MANIFEST,board=DEFAULT_BOARD,bench=None):
    ctx=context(manifest,board);e=document(source);validate_capture(e)
    # Analyze/validate inputs before making an output directory.
    analyze_mailbox(e,ctx['binding'],ctx['manifest'])
    b=document(bench) if bench else None
    if b is not None:bench_checks(b,e,ctx)
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    (out/'capture.json').write_bytes(Path(source).read_bytes())
    if bench:(out/'bench_input.json').write_bytes(Path(bench).read_bytes())
    return write_report(e,ctx,out,b)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest='action',required=True)
    for action in ('capture','report'):
        p=sub.add_parser(action);p.add_argument('--out',type=Path,required=True)
        p.add_argument('--manifest',type=Path,default=DEFAULT_MANIFEST)
        p.add_argument('--board',type=Path,default=DEFAULT_BOARD)
        if action=='capture':
            p.add_argument('--port',required=True);p.add_argument('--assembly',required=True)
            p.add_argument('--samples',type=int,default=2);p.add_argument('--interval',type=float,default=1.2)
        else:
            p.add_argument('source',type=Path);p.add_argument('--bench',type=Path)
    a=ap.parse_args()
    try:
        if a.action=='capture':
            r=capture_report(lambda:serial_client(a.port),a.assembly,a.out,a.manifest,a.board,a.samples,a.interval)
        else:r=offline_report(a.source,a.out,a.manifest,a.board,a.bench)
        print(json.dumps(dict(report=str(a.out/'report.html'),state=r['capture_state'],overall=r['overall'],
                              hardware_qualified=False,exit_code=r['exit_code']),ensure_ascii=False))
        return r['exit_code']
    except (OSError,ValueError,KeyError,TypeError,IndexError,struct.error) as exc:
        print(type(exc).__name__+': '+str(exc),file=sys.stderr);return 3


if __name__=='__main__':raise SystemExit(main())
