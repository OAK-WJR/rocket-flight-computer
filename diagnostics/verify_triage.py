"""Reproducible host-only regression and report demonstrations; no real port."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

from . import triage as t
from .test_assembly import frame
from .test_usb import Serial,crc
from .transport import atomic_json

ROOT=t.ROOT;FW=ROOT/'m3_firmware';OUT=ROOT/'diagnostics/verification_triage'
KPY='/Applications/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3'
KCLI='/Applications/KiCad.app/Contents/MacOS/kicad-cli'
sys.path.insert(0,str(FW))
from verify_assembly_firmware import TESTS

PROTECTED={
 'm3_design/M3_Assembly_Review_v0_8_1.zip':'fad260d2bf28c996fbbebf673454d44291791d0ead9d9f7e00e203cc84f997be',
 'm3_design/M3_PDIAG_Review_v0_8.zip':'87a78b675789c7f26a1c7399ac99e2c3af750ae01dd4aaf9332c15356a8f087f',
 'm3_design/assembly_review/m3.kicad_pcb':'e432d3436d5029de0a74a4b0ebcd02ec092dedf6d4252ce310f7be301558627f'}


def inputs():
    paths=[*ROOT.glob('diagnostics/*.py'),*ROOT.glob('diagnostics/*.md'),*FW.glob('src/*'),
           *FW.glob('test*.py'),*FW.glob('tests/**/*'),*FW.glob('protocol*.json'),
           ROOT/'m3_design/check_design.py',ROOT/'quality_audit/sexpr.py',ROOT/'M3_STATUS.md',
           FW/'README.md',ROOT/'m3_design/README.md']
    return {str(p.relative_to(ROOT)):t.sha(p) for p in paths if p.is_file() and '__pycache__' not in p.parts}


def artifacts():
    result={}
    for path in FW.glob('build_assembly_*/manifest.json'):
        m=t.document(path)
        for n,d in m['artifacts'].items():
            if t.sha(path.parent/n)!=d:raise ValueError('Firmware artifact changed '+str(path.parent/n))
        result[path.parent.name]=dict(build_sha256=m['build_sha256'],artifacts=m['artifacts'])
    if len(result)!=4:raise ValueError('Four exact firmware builds required')
    return result


def native_points(run,ctx):
    # The native PAD transform is independent of triage_map's text transform.
    atomic_json(run/'probe_map_input.json',ctx['mapping'])
    source='''import json,sys
from pathlib import Path
import pcbnew
m=json.loads(Path(sys.argv[2]).read_text());b=pcbnew.LoadBoard(sys.argv[1]);a={}
for f in b.GetFootprints():
 for p in f.Pads():
  key=f.GetReference()+'.'+p.GetNumber()
  if key in m['points']:
   if key in a:raise ValueError('Duplicate native point '+key)
   a[key]=dict(xy_mm=[round(p.GetPosition().x/1e6,6),round(p.GetPosition().y/1e6,6)],net=p.GetNetname())
errors=[k for k,p in m['points'].items() if a.get(k)!=dict(xy_mm=p['xy_mm'],net=p['net'])]
Path(sys.argv[3]).write_text(json.dumps(dict(board_sha256=m['board_sha256'],points=a,errors=errors),indent=2)+'\\n')
if errors:raise SystemExit(1)
'''
    (run/'read_native_points.py').write_text(source)
    r=subprocess.run([KPY,str(run/'read_native_points.py'),str(t.DEFAULT_BOARD),str(run/'probe_map_input.json'),
        str(run/'native_points.json')],capture_output=True,text=True,cwd=ROOT,timeout=30)
    (run/'native.log').write_text(r.stdout+r.stderr)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    n=t.document(run/'native_points.json')
    if n['errors'] or len(n['points'])!=30:raise ValueError('Native coordinates differ')
    return dict(points=30,errors=0,kicad=subprocess.check_output([KCLI,'--version'],text=True).strip(),
                result_sha256=t.sha(run/'native_points.json'),log_sha256=t.sha(run/'native.log'))


def main():
    OUT.mkdir(exist_ok=True);run=OUT/('run_'+uuid.uuid4().hex[:12]);run.mkdir()
    before=inputs();binaries=artifacts()
    for n,d in PROTECTED.items():
        if t.sha(ROOT/n)!=d:raise ValueError('Protected artifact changed: '+n)
    ctx=t.context();native=native_points(run,ctx)
    print('30 saved-PCB points match native KiCad.',flush=True)
    r=subprocess.run([sys.executable,'-m','unittest',*TESTS,'diagnostics.test_triage','-v'],
                     cwd=ROOT,capture_output=True,text=True,timeout=120)
    log=r.stdout+r.stderr;(run/'software.log').write_text(log);n=re.search(r'Ran (\d+) tests in',log)
    if r.returncode or not n:raise RuntimeError(log)
    print(n[1]+' software regressions passed.',flush=True)
    scenarios={}
    cases={'nominal':([frame(1),frame(2)],None),'partial':([frame(1),frame(2)],2)}
    a,b=frame(1),frame(2);b[153]|=8;b[155]|=64;b[158]=1
    cases['recovered_usb_fault']=([a,crc(b)],None)
    for name,(frames,fail) in cases.items():
        serial=Serial(frames);serial.fail_at=fail
        out=run/name
        report=t.capture_report(serial.client,'SYNTHETIC-'+name,out,pause=lambda _:None,origin='SYNTHETIC_FIXTURE')
        if any(req!=(1,0,1024) for req in serial.requests) or not serial.closed:
            raise ValueError('Unexpected operation/cleanup')
        scenarios[name]=dict(state=report['capture_state'],exit_code=report['exit_code'],
                             overall=report['overall'],groups=[g['id'] for g in report['investigations']])
    e=t.document(run/'nominal/capture.json');bench=t.bench_template(e,ctx)
    bench.update(same_supply_configuration=True,supply_configuration='SYNTHETIC stable USB-only DC demonstration')
    for p in bench['points']:
        if p['net'] in ('VBUS','VLOGIC','3V3','3V3A'):
            p['measurement']=dict(value={'VBUS':5.,'VLOGIC':4.9,'3V3':3.3,'3V3A':.1}[p['net']],
                unit='V',uncertainty_v=.01,input_ohm=10000000,instrument='SYNTHETIC-METER',measured_at=e['finished_at'])
    atomic_json(run/'synthetic_meter.json',bench)
    r=t.offline_report(run/'nominal/capture.json',run/'sensor_power_collapse',bench=run/'synthetic_meter.json')
    scenarios['sensor_power_collapse']=dict(exit_code=r['exit_code'],groups=[g['id'] for g in r['investigations']])
    # A deliberately nonexistent path exercises the actual pinned serial driver.
    noport='/private/tmp/NO-M3-TRIAGE-'+uuid.uuid4().hex
    r=subprocess.run([sys.executable,'-m','diagnostics.triage','capture','--port',noport,
        '--assembly','NO-HARDWARE','--out',str(run/'absent_port')],cwd=ROOT,capture_output=True,text=True,timeout=15)
    (run/'absent_port.log').write_text(r.stdout+r.stderr)
    absent=t.document(run/'absent_port/capture.json');ar=t.document(run/'absent_port/report.json')
    if r.returncode!=3 or absent['state']!='CONNECTION_FAILED' or absent['samples'] or absent['exchanges']:
        raise ValueError('Absent-port capture invented data')
    if 'No such file' not in absent['error'] or any(c['status']=='PASS' for c in ar['checks']):
        raise ValueError('Not an honest actual absent-port test')
    scenarios['actual_absent_port']=dict(state=absent['state'],exit_code=r.returncode,measurements=0)
    (run/'ORIGIN.txt').write_text('Synthetic transport/DC fault cases and an actual nonexistent serial port only. No hardware was connected, measured or flashed.\n')
    if before!=inputs() or binaries!=artifacts():raise ValueError('Verification inputs changed during run')
    for name,d in PROTECTED.items():
        if t.sha(ROOT/name)!=d:raise ValueError('Protected artifact changed during run')
    result=dict(ok=True,run=str(run.relative_to(ROOT)),inputs_sha256=before,native_points=native,
        software=dict(tests=int(n[1]),log_sha256=t.sha(run/'software.log')),scenarios=scenarios,
        firmware_unchanged=binaries,protected_artifacts=PROTECTED,
        hardware_connected=False,hardware_tested=False,flashed=False,full_m3_complete=False)
    atomic_json(OUT/'regression.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('inputs_sha256','firmware_unchanged','protected_artifacts')},indent=2))


if __name__=='__main__':main()
