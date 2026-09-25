"""Verify USB bench binaries, preserved CAD, protocol/HAL faults and absent-port behavior."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import uuid
from verify_storage_firmware import TESTS as LEGACY_TESTS,PROTECTED as LEGACY_PROTECTED,FOLDERS as HISTORICAL
from usb_binding import make_binding
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
PY=ROOT/'diagnostics/.venv/bin/python';OUT=HERE/'verification_usb'
TESTS=[*LEGACY_TESTS,'m3_firmware.test_usb','diagnostics.test_usb']
FOLDERS=tuple('build_usb_'+m+s for m in ('inspect','record') for s in ('','_query'))
PROTECTED=dict(LEGACY_PROTECTED,**{
 'm3_design/usb_review/m3.kicad_pcb':'e920cb93616475bd0a8cba37461bd292404b0695fadf94cf4cbae266bc28ba40',
 'm3_design/M3_USB_Candidate.zip':'a84ded19f396d81c7e4ee7102385cbc97a979b1f3df7eefe1be4c749d2a7e351',
 'm3_design/M3_Bench_Diagnostics_v0_5.zip':'47ed9fcefd34fe3899e7b553e02755c69237bad8327a71b8f785815a406f5173'})
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check_build(folder):
    if folder not in FOLDERS:raise ValueError('Only v0.6 builds are current USB candidates')
    p=HERE/folder;m=json.loads((p/'manifest.json').read_text());mode=folder.split('_')[2];query=folder.endswith('_query')
    options=dict(board='usb',camera_query=query,imu_samples=True,storage=mode)
    if m['build_options']!=options:raise ValueError('Compiled options mismatch')
    for name,digest in m['inputs'].items():
        if sha(HERE/name)!=digest:raise ValueError('Stale build source: '+name)
    identity=hashlib.sha256(json.dumps(dict(inputs=m['inputs'],options=options),sort_keys=True).encode()).hexdigest()
    if identity!=m['build_sha256']:raise ValueError('Build hash mismatch')
    protocol=json.loads((HERE/'protocol_usb.json').read_text())
    if m['protocol']!=protocol or m['board_sha256']!=protocol['board_sha256'] or m['profile']!=protocol['profile']:
        raise ValueError('Wrong protocol or PCB binding')
    if (m['hardware_tested'] or m['flashed'] or m['full_m3_complete'] or
        m['firmware_version']!='0.6' or m['usb_mode']!='CDC_READ_ONLY_REQUESTS'):raise ValueError('False completion claim')
    for n,d in m['artifacts'].items():
        if sha(p/n)!=d:raise ValueError('Changed artifact: '+n)
    raw=(p/'m3_bench.bin').read_bytes();sp,pc=struct.unpack('<II',raw[:8])
    if sp!=0x20020000 or not pc&1 or not 0x08000000<=(pc&~1)<0x08000000+len(raw):raise ValueError('Bad reset vector')
    if any(bytes.fromhex(m[n]) not in raw for n in ('board_sha256','build_sha256')):raise ValueError('Missing identity bytes')
    symbols=(p/'symbols.txt').read_text()
    if '24000000 00000400 B bench_mailbox' not in symbols:raise ValueError('Mailbox address/size mismatch')
    for n in ('bench_usb_initialize','bench_usb_task','bench_storage_usb_read','OTG_FS_IRQHandler','tud_rhport_init',
              'usb_wire_feed','dcd_init','HAL_QSPI_Abort','HAL_QSPI_SetTimeout'):
        if not re.search(r' T '+n+r'$',symbols,re.M):raise ValueError('Required USB function missing: '+n)
    irq=re.search(r'^([a-f0-9]+) [a-f0-9]+ T OTG_FS_IRQHandler$',symbols,re.M)
    if struct.unpack_from('<I',raw,4*(16+101))[0]!=(int(irq[1],16)|1):raise ValueError('USB interrupt vector is not linked handler')
    for n in ('HAL_FLASH_Program','HAL_FLASHEx_Erase','tud_dfu_runtime_reboot_to_dfu_cb'):
        if re.search(r' T '+n+r'$',symbols,re.M):raise ValueError('Unexpected mutation API')
    if bool(re.search(r' T HAL_QSPI_Transmit$',symbols,re.M))!=(mode=='record'):raise ValueError('Wrong inspect/program ability')
    return dict(build_sha256=identity,manifest_sha256=sha(p/'manifest.json'),artifacts=m['artifacts'],
        board_sha256=m['board_sha256'],binary_bytes=len(raw),storage=mode,camera_query=query)

def input_hashes():
    paths=[*HERE.glob('src/*'),*HERE.glob('test*.py'),*HERE.glob('tests/**/*'),
           *ROOT.glob('diagnostics/*.py'),*HERE.glob('*usb*.py'),HERE/'protocol_usb.json',HERE/'pins_usb.json',
           HERE/'USB_DIAGNOSTICS.md',*HERE.glob('research/usb/*'),
           ROOT/'m3_design/usb_review/verification_usb.json',ROOT/'m3_design/usb_review/schematic.net.xml']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()}

def main():
    OUT.mkdir(exist_ok=True);run=OUT/('run_'+uuid.uuid4().hex[:12]);run.mkdir();before=input_hashes()
    protected={}
    for n,d in PROTECTED.items():
        if not (ROOT/n).exists() and n.endswith('.zip'):continue
        if sha(ROOT/n)!=d:raise ValueError('Protected baseline changed: '+n)
        protected[n]=d
    binding=make_binding();builds={n:check_build(n) for n in FOLDERS}
    for n,b in builds.items():
        if b['board_sha256']!=binding['board_sha256']:raise ValueError('Build/CAD mismatch')
    vendor=json.loads((HERE/'vendor_manifest.json').read_text())
    for row in vendor['files']:
        if sha(HERE/row['path'])!=row['sha256']:raise ValueError('Modified ST source')
    tiny=json.loads((HERE/'research/usb/tinyusb_manifest.json').read_text())
    for n,d in tiny['files'].items():
        if sha(HERE/'vendor/tinyusb'/n)!=d:raise ValueError('Modified TinyUSB source')
    result=subprocess.run([str(PY),'-m','unittest',*TESTS,'-v'],cwd=ROOT,capture_output=True,text=True,timeout=60)
    log=result.stdout+result.stderr;(run/'regression.log').write_text(log);count=re.search(r'Ran (\d+) tests in',log)
    if result.returncode or not count:raise RuntimeError(log)
    # A nonexistent filesystem port exercises the real pyserial error path,
    # without selecting or touching any attached serial device.
    noport='/private/tmp/NO-M3-DEVICE-'+uuid.uuid4().hex
    if Path(noport).exists():raise RuntimeError('Unexpected device path')
    version=subprocess.run([str(PY),'-c','import importlib.metadata;print(importlib.metadata.version("pyserial"))'],capture_output=True,text=True,check=True)
    if version.stdout.strip()!='3.5':raise ValueError('Wrong pyserial dependency')
    absent={}
    for action in ('capture','dump'):
        out=run/('absent_'+action+('.json' if action=='capture' else ''))
        cmd=[str(PY),'-m','diagnostics.usb',action,'--port',noport,'--manifest',str(HERE/'build_usb_inspect/manifest.json'),
             '--out',str(out),'--assembly','NO-HARDWARE','--sectors','1']
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=15)
        (run/('absent_'+action+'.log')).write_text(r.stdout+r.stderr)
        e=json.loads((out if action=='capture' else out/'capture.json').read_text())
        if r.returncode!=3 or e['state']!='CONNECTION_FAILED' or e.get('bytes',0) or e.get('samples',[]):
            raise ValueError('Absent-port test invented data: '+r.stdout+r.stderr)
        if 'SerialException' not in e['error'] or 'No such file' not in e['error']:
            raise ValueError('Not a real absent-port failure: '+e['error'])
        if action=='dump' and (out/'flash.bin').exists():raise ValueError('Absent device created Flash data')
        absent[action]=dict(state=e['state'],exit_code=r.returncode)
    sys.path.insert(0,str(ROOT))
    from diagnostics.test_usb import Serial,manifest
    from diagnostics.usb import capture,dump
    from diagnostics.mailbox import analyze_mailbox
    from diagnostics.transport import atomic_json
    e=capture(Serial().client,manifest(),'SYNTHETIC-USB-001',run/'synthetic_capture.json',pause=lambda _:None,origin='SYNTHETIC_FIXTURE')
    report=analyze_mailbox(e,binding,manifest());atomic_json(run/'synthetic_analysis.json',report)
    serial=Serial();serial.fail_at=3
    partial=dump(serial.client,manifest(),run/'synthetic_interrupted_dump',1,origin='SYNTHETIC_FIXTURE')
    if partial['state']!='PARTIAL' or partial['bytes']!=1024:raise ValueError('Interrupted example wrong')
    (run/'ORIGIN.txt').write_text('All examples are scripted SYNTHETIC_FIXTURE or real absent-port failures. No physical board captured.\n')
    if before!=input_hashes() or any(sha(ROOT/n)!=d for n,d in protected.items()):raise ValueError('Inputs changed during verification')
    result=dict(schema=1,ok=True,tests=int(count[1]),builds=builds,inputs_sha256=before,protected_baselines=protected,
        run=str(run.relative_to(ROOT)),log_sha256=sha(run/'regression.log'),tinyusb_version=tiny['version'],
        vendor_files=len(vendor['files']),tinyusb_files=len(tiny['files']),absent_port=absent,
        hardware_tested=False,flashed=False,usb_electrical_qualified=False,full_m3_complete=False,
        scope='Four USB v0.6 builds, legacy host regression, C wire/HAL fault tests and prototype descriptors; no physical enumeration')
    (OUT/'regression.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('inputs_sha256','protected_baselines','builds')},indent=2))

if __name__=='__main__':main()
