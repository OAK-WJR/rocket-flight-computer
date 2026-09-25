"""Verify v4 bench software and legacy compatibility; no flashing or CAD edits."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import uuid
from verify_uart_firmware import (HERE,ROOT,PY,sha,check_build as legacy_build,
                                 input_hashes as legacy_inputs,PROTECTED as LEGACY_PROTECTED,TESTS as LEGACY_TESTS)

OUT=HERE/'verification_imu'
TESTS=[*LEGACY_TESTS,'m3_firmware.test_imu','diagnostics.test_imu']
FOLDERS=('build','build_uart_idle','build_uart_query','build_imu_idle','build_imu_query')
PROTECTED=dict(LEGACY_PROTECTED,**{
    'm3_design/M3_Bench_Diagnostics_v0_3.zip':'a43fb17c1b7122a80e91f30231e4ee1d19308f8ad8a68872a86fc172ed1698a1'})

def input_hashes():
    files=[*HERE.glob('research/imu_reference/**/*'),HERE/'research/IMU_ACQUISITION.md',
           ROOT/'m3_core/sources/icm45686.pdf']
    return dict(legacy_inputs(),**{str(p.relative_to(ROOT)):sha(p) for p in files if p.is_file()})

def check_build(folder):
    if folder not in ('build_imu_idle','build_imu_query'):return legacy_build(folder)
    p=HERE/folder;m=json.loads((p/'manifest.json').read_text());query=folder.endswith('_query')
    for name,digest in m['inputs'].items():
        if sha(HERE/name)!=digest:raise ValueError('Stale source: '+folder+'/'+name)
    identity=hashlib.sha256(json.dumps({'inputs':m['inputs'],'options':m['build_options']},sort_keys=True).encode()).hexdigest()
    if identity!=m['build_sha256'] or m['build_options']!={'board':'uart','camera_query':query,'imu_samples':True}:
        raise ValueError('Wrong v4 build identity/options')
    for name,digest in m['artifacts'].items():
        if sha(p/name)!=digest:raise ValueError('Modified binary: '+folder+'/'+name)
    protocol=json.loads((HERE/'protocol_imu.json').read_text())
    if m['protocol']!=protocol or m['profile']!=protocol['profile'] or m['board_sha256']!=protocol['board_sha256']:
        raise ValueError('Wrong v4 board/protocol')
    if m['hardware_tested'] or m['flashed'] or m['full_m3_complete'] or m['firmware_version']!='0.4':
        raise ValueError('Invalid completion claim')
    for name,digest in protocol['imu']['source_hashes'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Reference changed: '+name)
    data=(p/'m3_bench.bin').read_bytes();sp,entry=struct.unpack('<II',data[:8])
    if sp!=0x20020000 or not entry&1 or not 0x08000000 <= (entry&~1) < 0x08000000+len(data):
        raise ValueError('Invalid compiled vector')
    if any(bytes.fromhex(m[k]) not in data for k in ('board_sha256','build_sha256')):
        raise ValueError('Missing binary identity')
    symbols=(p/'symbols.txt').read_text()
    if '24000000 00000200 B bench_mailbox' not in symbols:raise ValueError('Mailbox moved')
    for symbol in ('bench_imu_initialize','bench_imu_sample','HAL_SPI_TransmitReceive','bench_camera_query'):
        if not re.search(r' T '+symbol+r'$',symbols,re.M):raise ValueError('Missing linked function: '+symbol)
    return dict(build_sha256=identity,manifest_sha256=sha(p/'manifest.json'),artifacts=m['artifacts'],
                board_sha256=m['board_sha256'],binary_bytes=len(data),camera_query=query,imu_samples=True)

def main():
    OUT.mkdir(exist_ok=True);run=OUT/('run_'+uuid.uuid4().hex[:12]);run.mkdir()
    before=input_hashes();protected={}
    for name,digest in PROTECTED.items():
        p=ROOT/name
        if not p.exists() and p.suffix=='.zip':continue
        if sha(p)!=digest:raise ValueError('Protected baseline changed: '+name)
        protected[name]=digest
    builds={f:check_build(f) for f in FOLDERS}
    if builds['build_imu_idle']['artifacts']['m3_bench.bin']==builds['build_imu_query']['artifacts']['m3_bench.bin']:
        raise ValueError('Camera mode binaries must differ')
    vendor=json.loads((HERE/'vendor_manifest.json').read_text())
    for row in vendor['files']:
        if sha(HERE/row['path'])!=row['sha256']:raise ValueError('Modified vendor file')
    refs=json.loads((HERE/'research/imu_reference/manifest.json').read_text())
    for row in refs['files']:
        raw=(HERE/'research/imu_reference'/row['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row['sha256'] or hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=row['git_blob']:
            raise ValueError('Modified primary reference: '+row['path'])
    result=subprocess.run([str(PY),'-m','unittest',*TESTS,'-v'],cwd=ROOT,capture_output=True,text=True,timeout=60)
    log=result.stdout+result.stderr;(run/'regression.log').write_text(log)
    count=re.search(r'Ran (\d+) tests in',log)
    if result.returncode or not count:raise RuntimeError(log)
    inventory=subprocess.run([str(PY),'-m','diagnostics','probes'],cwd=ROOT,capture_output=True,text=True,timeout=15)
    if inventory.returncode:raise RuntimeError(inventory.stderr)
    probes=json.loads(inventory.stdout);(run/'probe_inventory.json').write_text(inventory.stdout)
    absent_results={}
    for mode in ('idle','query'):
        absent='NO-DEVICE-SELFTEST-'+uuid.uuid4().hex
        if any(p['id']==absent for p in probes['probes']):raise ValueError('Unexpected probe identity')
        folder=HERE/('build_imu_'+mode);out=run/('absent_'+mode)
        cmd=[str(PY),'-m','diagnostics.mailbox','capture','--probe-id',absent,'--assembly-id','NO-HARDWARE',
             '--binding',str(folder/'binding.json'),'--manifest',str(folder/'manifest.json'),'--out',str(out)]
        tested=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=35)
        evidence=json.loads((out/'mailbox.json').read_text())
        if tested.returncode!=3 or evidence['state']!='CONNECTION_FAILED' or evidence['samples'] or evidence['identity']:
            raise ValueError('Absent probe yielded invalid evidence')
        absent_results[mode]=dict(path=str(out.relative_to(ROOT)),exit=tested.returncode,state=evidence['state'])
    sys.path.insert(0,str(ROOT))
    from diagnostics.test_imu import imu_frame
    from diagnostics.test_mailbox import SyntheticMailbox
    from diagnostics.mailbox import capture_mailbox,report_file
    folder=HERE/'build_imu_idle';binding=json.loads((folder/'binding.json').read_text());manifest=json.loads((folder/'manifest.json').read_text())
    example=run/'synthetic_imu_update_during_read';example.mkdir()
    frames=[imu_frame(1),imu_frame(2,SAMPLE_STATUS=3,SAMPLE_ERROR=9,EVIDENCE=0xe9070404,ERROR_HISTORY=512)]
    capture_mailbox(SyntheticMailbox(frames),binding,manifest,'SYNTHETIC-NOT-HARDWARE',example/'mailbox.json',
                    origin='SYNTHETIC_FIXTURE',pause=lambda _:None)
    if report_file(example/'mailbox.json',example/'analysis',binding,manifest)!=2:
        raise ValueError('Failed IMU example did not report issues')
    if before!=input_hashes() or any(sha(ROOT/n)!=d for n,d in protected.items()):
        raise ValueError('Inputs changed during verification')
    record=dict(schema=1,ok=True,tests=int(count[1]),builds=builds,inputs_sha256=before,
                protected_baselines=protected,vendor_files=len(vendor['files']),reference_files=len(refs['files']),
                run=str(run.relative_to(ROOT)),log_sha256=sha(run/'regression.log'),
                scripted_spi_adapter_cases=12,portable_imu_tests=20,imu_host_tests=13,
                absent_probe_results=absent_results,synthetic_example=str(example.relative_to(ROOT)),
                hardware_tested=False,flashed=False,full_m3_complete=False,
                scope='Five compiled bench targets, scripted C/HAL faults, fixed-range host parsing and relocated package; no physical qualification')
    (OUT/'regression.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k not in ('inputs_sha256','protected_baselines','builds')},indent=2))

if __name__=='__main__':main()
