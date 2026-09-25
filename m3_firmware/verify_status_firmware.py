"""Bind v8 status binaries, native CAD and reproducible software fault evidence."""
import hashlib,json,re,struct,subprocess,sys,uuid
from pathlib import Path
from verify_gnss_firmware import TESTS as OLD_TESTS,PROTECTED as OLD_PROTECTED,FOLDERS as OLD_GNSS
from status_binding import make_binding
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;PY=ROOT/'diagnostics/.venv/bin/python'
OUT=HERE/'verification_status'
TESTS=[*OLD_TESTS,'m3_firmware.test_power_status','diagnostics.test_power_status']
FOLDERS=tuple('build_status_'+m+s for m in ('inspect','record') for s in ('','_query'))
PROTECTED=dict(OLD_PROTECTED,**{
 'm3_design/M3_GNSS_Candidate.zip':'b4d1ab9d7e97fefd5eb971182fba206700cc6dc9a7a581993cce82a40c3a299c',
 'm3_design/M3_Bench_Diagnostics_v0_7.zip':'c39ca327ab2df8bdf4b2362548c6df4d1ddd33aa8bcc6501b3933d64bfaae9d9'})
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check_build(folder,variant='status'):
    if variant not in ('status','assembly'):raise ValueError('Unreviewed variant')
    permitted=tuple('build_'+variant+'_'+m+s for m in ('inspect','record') for s in ('','_query'))
    if folder not in permitted:raise ValueError('Not a status/assembly build')
    p=HERE/folder;m=json.loads((p/'manifest.json').read_text());mode=folder.split('_')[2]
    opts=dict(board=variant,camera_query=folder.endswith('_query'),imu_samples=True,storage=mode)
    if m['build_options']!=opts:raise ValueError('Wrong options')
    for n,d in m['inputs'].items():
        if sha(HERE/n)!=d:raise ValueError('Stale source '+n)
    ident=hashlib.sha256(json.dumps(dict(inputs=m['inputs'],options=opts),sort_keys=True).encode()).hexdigest()
    proto=json.loads((HERE/('protocol_'+variant+'.json')).read_text())
    if m['build_sha256']!=ident or m['protocol']!=proto or m['board_sha256']!=proto['board_sha256'] or m['profile']!=proto['profile']:raise ValueError('Identity mismatch')
    if any(m[n] for n in ('hardware_tested','flashed','full_m3_complete')) or m['firmware_version']!=('0.8' if variant=='status' else '0.8.1'):raise ValueError('False completion claim')
    for n,want in [('power_status_mode','INPUT_ONLY_LATCHED_HISTORY'),('gnss_mode','UBX_READ_ONLY_POLLS_9600'),('usb_mode','CDC_READ_ONLY_REQUESTS')]:
        if m[n]!=want:raise ValueError('Wrong capability '+n)
    for n,d in m['artifacts'].items():
        if sha(p/n)!=d:raise ValueError('Changed binary '+n)
    raw=(p/'m3_bench.bin').read_bytes();sp,entry=struct.unpack_from('<II',raw)
    if sp!=0x20020000 or not entry&1 or not 0x08000000<=(entry&~1)<0x08000000+len(raw):raise ValueError('Wrong reset vector')
    if any(bytes.fromhex(m[n]) not in raw for n in ('board_sha256','build_sha256')):raise ValueError('Missing binary identity')
    symbols=(p/'symbols.txt').read_text()
    if '24000000 00000400 B bench_mailbox' not in symbols:raise ValueError('Wrong SRAM range')
    for n in ('bench_power_initialize','bench_power_tick','bench_power_status','power_status_observe','bench_gnss_task','bench_storage_usb_read','bench_usb_initialize'):
        if not re.search(r' T '+n+r'$',symbols,re.M):raise ValueError('Missing '+n)
    for name,irq in [('EXTI0_IRQHandler',6),('EXTI1_IRQHandler',7),('EXTI4_IRQHandler',10),('EXTI9_5_IRQHandler',23),('USART6_IRQHandler',71),('OTG_FS_IRQHandler',101)]:
        match=re.search(r'^([a-f0-9]+) [a-f0-9]+ T '+name+'$',symbols,re.M)
        if not match or struct.unpack_from('<I',raw,4*(16+irq))[0]!=(int(match[1],16)|1):raise ValueError('Wrong IRQ vector '+name)
    for n in ('HAL_FLASH_Program','HAL_FLASHEx_Erase','tud_dfu_runtime_reboot_to_dfu_cb'):
        if re.search(r' T '+n+r'$',symbols,re.M):raise ValueError('Unexpected programming API')
    if bool(re.search(r' T HAL_QSPI_Transmit$',symbols,re.M))!=(mode=='record'):raise ValueError('Wrong write capability')
    return dict(build_sha256=ident,manifest_sha256=sha(p/'manifest.json'),board_sha256=m['board_sha256'],artifacts=m['artifacts'],binary_bytes=len(raw))
def input_hashes():
    paths=[*HERE.glob('src/*'),*HERE.glob('test*.py'),*HERE.glob('tests/**/*'),*ROOT.glob('diagnostics/*.py'),
           *HERE.glob('*status*.*'),HERE/'build.py',HERE/'POWER_STATUS_DIAGNOSTICS.md',ROOT/'M3_STATUS.md',
           *ROOT.glob('m3_design/*status*.py'),*ROOT.glob('m3_design/power_status_review/*.json'),
           ROOT/'m3_design/power_status_review/POWER_STATUS_REVIEW.md']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file() and '__pycache__' not in p.parts}
def main():
    OUT.mkdir(exist_ok=True);run=OUT/('run_'+uuid.uuid4().hex[:12]);run.mkdir();before=input_hashes()
    for n,d in PROTECTED.items():
        if (ROOT/n).exists() and sha(ROOT/n)!=d:raise ValueError('Protected archive changed '+n)
    make_binding();builds={n:check_build(n) for n in FOLDERS}
    for folder in OLD_GNSS:
        m=json.loads((HERE/folder/'manifest.json').read_text())
        for n,d in m['artifacts'].items():
            if sha(HERE/folder/n)!=d:raise ValueError('Old GNSS binary changed')
    logs={}
    for label,cmd in [('software',[str(PY),'-m','unittest',*TESTS,'-v']),
                      ('cad',[str(PY),'-m','unittest','discover','-s','m3_design','-p','test_status.py','-v'])]:
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=90);log=r.stdout+r.stderr
        (run/(label+'.log')).write_text(log);count=re.search(r'Ran (\d+) tests in',log)
        if r.returncode or not count:raise RuntimeError(log)
        logs[label]=dict(tests=int(count[1]),sha256=sha(run/(label+'.log')))
    absent={};noport='/private/tmp/NO-M3-PDIAG-'+uuid.uuid4().hex
    for action in ('capture','dump'):
        out=run/('absent_'+action+('.json' if action=='capture' else ''))
        cmd=[str(PY),'-m','diagnostics.usb',action,'--port',noport,'--manifest',str(HERE/'build_status_inspect/manifest.json'),
             '--out',str(out),'--assembly','NO-HARDWARE','--sectors','1']
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=15);(run/('absent_'+action+'.log')).write_text(r.stdout+r.stderr)
        e=json.loads((out if action=='capture' else out/'capture.json').read_text())
        if r.returncode!=3 or e['state']!='CONNECTION_FAILED' or e.get('samples',[]) or e.get('bytes',0):raise ValueError('Absent-device path invented measurements')
        if 'No such file' not in e['error']:raise ValueError('Not a real absent-port test')
        absent[action]=dict(state=e['state'],exit_code=r.returncode)
    sys.path.insert(0,str(ROOT))
    from diagnostics.test_power_status import frame,manifest
    from diagnostics.test_usb import Serial,crc
    from diagnostics.usb import capture
    from diagnostics.mailbox import analyze_mailbox
    frames=[frame(1),frame(2)];frames[1][153]|=8;frames[1][155]|=64;frames[1][158]=1;frames[1]=crc(frames[1])
    e=capture(Serial(frames).client,manifest(),'SYNTHETIC-RECOVERED-USB-FAULT',run/'synthetic_capture.json',pause=lambda _:None,origin='SYNTHETIC_FIXTURE')
    (run/'synthetic_analysis.json').write_text(json.dumps(analyze_mailbox(e,make_binding(),manifest()),indent=2)+'\n')
    (run/'ORIGIN.txt').write_text('Software/fault injection and actual absent-port tests only. No physical board, GNSS signal or power transient measured.\n')
    if before!=input_hashes():raise ValueError('Inputs changed during verification')
    result=dict(ok=True,builds=builds,inputs_sha256=before,tests=logs,absent_port=absent,protected_archives=PROTECTED,
                run=str(run.relative_to(ROOT)),hardware_tested=False,flashed=False,full_m3_complete=False)
    (OUT/'regression.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('builds','inputs_sha256','protected_archives')},indent=2))
if __name__=='__main__':main()
