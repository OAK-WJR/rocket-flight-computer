"""Verify diagnostic storage builds and fault models, never flash or edit CAD."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import uuid
from verify_imu_firmware import (HERE,ROOT,PY,sha,check_build as legacy_build,
    input_hashes as legacy_inputs,PROTECTED as OLD_PROTECTED,TESTS as OLD_TESTS,FOLDERS as OLD_FOLDERS)

OUT=HERE/'verification_storage'
TESTS=[*OLD_TESTS,'m3_firmware.test_storage','diagnostics.test_storage']
NEW_FOLDERS=tuple('build_storage_'+mode+suffix for mode in ('inspect','record') for suffix in ('','_query'))
FOLDERS=(*OLD_FOLDERS,*NEW_FOLDERS)
PROTECTED=dict(OLD_PROTECTED,**{'m3_design/M3_Bench_Diagnostics_v0_4.zip':
                              '6bc45965be420083fbf9e887c9d25877a6d0b3f0388564c3f77fe62789696440'})
def input_hashes():
    files=[HERE/'research/w25q128jv.pdf',HERE/'research/stm32h743_ds12110_rev5.pdf',
           HERE/'research/storage_sources.json',HERE/'research/STORAGE_ACQUISITION.md']
    return dict(legacy_inputs(),**{str(p.relative_to(ROOT)):sha(p) for p in files})

def check_build(folder):
    if folder not in NEW_FOLDERS:return legacy_build(folder)
    p=HERE/folder;m=json.loads((p/'manifest.json').read_text())
    mode='record' if folder.startswith('build_storage_record') else 'inspect';query=folder.endswith('_query')
    expected_options=dict(board='uart',camera_query=query,imu_samples=True,storage=mode)
    if m['build_options']!=expected_options:raise ValueError('Wrong compiled mode: '+folder)
    for name,digest in m['inputs'].items():
        if sha(HERE/name)!=digest:raise ValueError('Stale build input: '+name)
    identity=hashlib.sha256(json.dumps({'inputs':m['inputs'],'options':expected_options},sort_keys=True).encode()).hexdigest()
    if identity!=m['build_sha256']:raise ValueError('Build identity changed')
    protocol=json.loads((HERE/'protocol_storage.json').read_text())
    if m['protocol']!=protocol or m['profile']!=protocol['profile'] or m['board_sha256']!=protocol['board_sha256']:
        raise ValueError('Wrong board or storage protocol')
    if m['hardware_tested'] or m['flashed'] or m['full_m3_complete'] or m['firmware_version']!='0.5':
        raise ValueError('Wrong completion claim')
    for name,digest in m['artifacts'].items():
        if sha(p/name)!=digest:raise ValueError('Changed output: '+name)
    data=(p/'m3_bench.bin').read_bytes();sp,entry=struct.unpack('<II',data[:8])
    if sp!=0x20020000 or not entry&1 or not 0x08000000<=(entry&~1)<0x08000000+len(data):raise ValueError('Wrong vector')
    for name in ('board_sha256','build_sha256'):
        if bytes.fromhex(m[name]) not in data:raise ValueError('Binary identity missing')
    symbols=(p/'symbols.txt').read_text()
    if '24000000 00000400 B bench_mailbox' not in symbols:raise ValueError('Wrong mailbox size/address')
    for name in ('bench_imu_sample','bench_storage_begin','bench_storage_append','HAL_QSPI_Command','HAL_QSPI_Receive'):
        if not re.search(r' T '+name+r'$',symbols,re.M):raise ValueError('Required function missing: '+name)
    tx=bool(re.search(r' T HAL_QSPI_Transmit$',symbols,re.M));mapped=bool(re.search(r' T HAL_QSPI_MemoryMapped$',symbols,re.M))
    pp=bool(re.search(r' T storage_program_page$',symbols,re.M))
    if (tx,pp,mapped)!=(mode=='record',mode=='record',mode=='inspect'):raise ValueError('Wrong linked mutation/mapping capability')
    if any(n in symbols for n in ('HAL_FLASH_Program','HAL_FLASHEx_Erase','HAL_QSPI_AutoPolling_IT')):
        raise ValueError('Unreviewed write/interrupt API')
    return dict(build_sha256=identity,manifest_sha256=sha(p/'manifest.json'),artifacts=m['artifacts'],
                board_sha256=m['board_sha256'],binary_bytes=len(data),storage=mode,camera_query=query)

def main():
    OUT.mkdir(exist_ok=True);run=OUT/('run_'+uuid.uuid4().hex[:12]);run.mkdir()
    before=input_hashes();protected={}
    for name,digest in PROTECTED.items():
        p=ROOT/name
        if not p.exists() and p.suffix=='.zip':continue
        if sha(p)!=digest:raise ValueError('Protected baseline changed: '+name)
        protected[name]=digest
    builds={name:check_build(name) for name in FOLDERS}
    vendor=json.loads((HERE/'vendor_manifest.json').read_text())
    for row in vendor['files']:
        if sha(HERE/row['path'])!=row['sha256']:raise ValueError('Vendor source changed')
    r=subprocess.run([str(PY),'-m','unittest',*TESTS,'-v'],cwd=ROOT,capture_output=True,text=True,timeout=60)
    log=r.stdout+r.stderr;(run/'regression.log').write_text(log);count=re.search(r'Ran (\d+) tests in',log)
    if r.returncode or not count:raise RuntimeError(log)
    inventory=subprocess.run([str(PY),'-m','diagnostics','probes'],cwd=ROOT,capture_output=True,text=True,timeout=15)
    if inventory.returncode:raise RuntimeError(inventory.stderr)
    probes=json.loads(inventory.stdout);(run/'probe_inventory.json').write_text(inventory.stdout)
    absent='NO-DEVICE-SELFTEST-'+uuid.uuid4().hex
    if any(p['id']==absent for p in probes['probes']):raise ValueError('Unexpected real probe')
    folder=HERE/'build_storage_inspect';out=run/'absent_dump'
    cmd=[str(PY),'-m','diagnostics.storage','dump','--probe-id',absent,'--manifest',str(folder/'manifest.json'),'--out',str(out)]
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=35);(run/'absent_dump.log').write_text(r.stdout+r.stderr)
    evidence=json.loads((out/'capture.json').read_text())
    if r.returncode!=3 or evidence['state']!='CONNECTION_FAILED' or evidence['bytes'] or (out/'flash.bin').exists():
        raise ValueError('No-probe result invented data')
    # Produce one reusable file generated by the production C journal and corrupt
    # a later record. Recovery must retain the first complete observation.
    import sys
    sys.path.insert(0,str(ROOT))
    from diagnostics.test_storage import StorageHostTests
    from diagnostics.storage import write_recovery
    fixture=run/'synthetic_interrupted_record';fixture.mkdir()
    StorageHostTests.setUpClass()
    try:
        n,d=StorageHostTests().journal(2)
        image=bytes(n.memory[:1024+350])+b'\xff'*(4096-1024-350)
    finally:StorageHostTests.tearDownClass()
    (fixture/'flash.bin').write_bytes(image)
    recovered=write_recovery(fixture/'flash.bin',fixture/'recovered')
    rows=[json.loads(x) for x in (fixture/'recovered/records.jsonl').read_text().splitlines()]
    if len(rows)!=1 or not recovered['issues']:raise ValueError('Torn write example not detected')
    (fixture/'ORIGIN.txt').write_text('SYNTHETIC_FIXTURE: produced by scripted NOR model, not read from a physical board.\n')
    if before!=input_hashes() or any(sha(ROOT/n)!=d for n,d in protected.items()):raise ValueError('Inputs changed during verification')
    record=dict(schema=1,ok=True,tests=int(count[1]),builds=builds,inputs_sha256=before,protected_baselines=protected,
                run=str(run.relative_to(ROOT)),log_sha256=sha(run/'regression.log'),vendor_files=len(vendor['files']),
                absent_probe=dict(state=evidence['state'],exit=r.returncode),synthetic_example=str(fixture.relative_to(ROOT)),
                torn_record_byte_boundaries=769,hardware_tested=False,flashed=False,full_m3_complete=False,
                scope='Nine compiled bench modes; C NOR/HAL fault models, bounded host recovery and readonly download, no physical qualification')
    (OUT/'regression.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k not in ('inputs_sha256','protected_baselines','builds')},indent=2))

if __name__=='__main__':main()
