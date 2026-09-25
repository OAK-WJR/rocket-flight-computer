"""Bind four GNSS bench binaries, preserved inputs and reproducible software evidence."""
import hashlib,json,re,struct,subprocess,sys,uuid
from pathlib import Path
from verify_usb_firmware import TESTS as OLD_TESTS,PROTECTED as OLD_PROTECTED,FOLDERS as USB_FOLDERS,HISTORICAL as OLDER
from gnss_binding import make_binding
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
PY=ROOT/'diagnostics/.venv/bin/python';OUT=HERE/'verification_gnss'
TESTS=[*OLD_TESTS,'m3_firmware.test_gnss','diagnostics.test_gnss']
HISTORICAL=(*OLDER,*USB_FOLDERS)
FOLDERS=tuple('build_gnss_'+m+s for m in ('inspect','record') for s in ('','_query'))
PROTECTED=dict(OLD_PROTECTED,**{'m3_design/M3_Bench_Diagnostics_v0_6.zip':'f9231d950a205731a3ac91d924127ffde1879723ab4cb4c59d84318d4ee3db93'})
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def check_build(folder):
    if folder not in FOLDERS:raise ValueError('Not a current GNSS build')
    p=HERE/folder;m=json.loads((p/'manifest.json').read_text());mode=folder.split('_')[2]
    opts=dict(board='gnss',camera_query=folder.endswith('_query'),imu_samples=True,storage=mode)
    if m['build_options']!=opts:raise ValueError('Wrong build options')
    for n,d in m['inputs'].items():
        if sha(HERE/n)!=d:raise ValueError('Stale source '+n)
    identity=hashlib.sha256(json.dumps(dict(inputs=m['inputs'],options=opts),sort_keys=True).encode()).hexdigest()
    p7=json.loads((HERE/'protocol_gnss.json').read_text())
    if (m['build_sha256']!=identity or m['protocol']!=p7 or m['board_sha256']!=p7['board_sha256'] or m['profile']!=p7['profile']):
        raise ValueError('Wrong binary/CAD/protocol identity')
    if any(m[n] for n in ('hardware_tested','flashed','full_m3_complete')) or m['firmware_version']!='0.7':raise ValueError('False completion claim')
    if m['gnss_mode']!='UBX_READ_ONLY_POLLS_9600' or m['usb_mode']!='CDC_READ_ONLY_REQUESTS':raise ValueError('Wrong receiver/USB scope')
    for n,d in m['artifacts'].items():
        if sha(p/n)!=d:raise ValueError('Modified binary '+n)
    raw=(p/'m3_bench.bin').read_bytes();sp,entry=struct.unpack_from('<II',raw)
    if sp!=0x20020000 or not entry&1 or not 0x08000000<=(entry&~1)<0x08000000+len(raw):raise ValueError('Wrong reset vector')
    if any(bytes.fromhex(m[n]) not in raw for n in ('board_sha256','build_sha256')):raise ValueError('Binary identity absent')
    symbols=(p/'symbols.txt').read_text()
    if '24000000 00000400 B bench_mailbox' not in symbols:raise ValueError('Wrong SRAM range')
    for n in ('bench_gnss_initialize','bench_gnss_task','gnss_feed','gnss_tick','gnss_poll_packet',
              'bench_usb_initialize','bench_storage_usb_read','HAL_QSPI_Abort','HAL_QSPI_SetTimeout'):
        if not re.search(r' T '+n+r'$',symbols,re.M):raise ValueError('Function missing '+n)
    for name,irq in [('USART6_IRQHandler',71),('OTG_FS_IRQHandler',101)]:
        match=re.search(r'^([a-f0-9]+) [a-f0-9]+ T '+name+'$',symbols,re.M)
        if not match or struct.unpack_from('<I',raw,4*(16+irq))[0]!=(int(match[1],16)|1):raise ValueError('Wrong IRQ vector '+name)
    for n in ('HAL_FLASH_Program','HAL_FLASHEx_Erase','tud_dfu_runtime_reboot_to_dfu_cb'):
        if re.search(r' T '+n+r'$',symbols,re.M):raise ValueError('Unexpected mutation API')
    if bool(re.search(r' T HAL_QSPI_Transmit$',symbols,re.M))!=(mode=='record'):raise ValueError('Wrong inspect/write capability')
    return dict(build_sha256=identity,manifest_sha256=sha(p/'manifest.json'),artifacts=m['artifacts'],
                board_sha256=m['board_sha256'],binary_bytes=len(raw),storage=mode,camera_query=opts['camera_query'])

def input_hashes():
    paths=[*HERE.glob('src/*'),*HERE.glob('test*.py'),*HERE.glob('tests/**/*'),
           *ROOT.glob('diagnostics/*.py'),*HERE.glob('*gnss*.py'),HERE/'protocol_gnss.json',HERE/'pins_gnss.json',
           HERE/'GNSS_DIAGNOSTICS.md',HERE/'README.md',ROOT/'M3_STATUS.md',ROOT/'diagnostics/README.md',
           *HERE.glob('research/gnss/*'),*ROOT.glob('m3_design/*gnss*.py'),ROOT/'m3_design/README.md',
           ROOT/'m3_design/gnss_review/verification_gnss.json',ROOT/'m3_design/gnss_review/GNSS_REVIEW.md',
           ROOT/'m3_design/gnss_review/bom_review.json',ROOT/'m3_core/sources/sam_m10q_im.pdf']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file() and '__pycache__' not in p.parts}

def main():
    OUT.mkdir(exist_ok=True);run=OUT/('run_'+uuid.uuid4().hex[:12]);run.mkdir();before=input_hashes()
    protected={n:d for n,d in PROTECTED.items() if (ROOT/n).exists()}
    for n,d in protected.items():
        if sha(ROOT/n)!=d:raise ValueError('Protected original changed '+n)
    binding=make_binding();builds={n:check_build(n) for n in FOLDERS}
    for file,key,base in [(HERE/'vendor_manifest.json','files',HERE),(HERE/'research/usb/tinyusb_manifest.json','files',HERE/'vendor/tinyusb')]:
        rows=json.loads(file.read_text())[key]
        entries=((r['path'],r['sha256']) for r in rows) if isinstance(rows,list) else rows.items()
        for n,d in entries:
            if sha(base/n)!=d:raise ValueError('Vendor source changed '+n)
    r=subprocess.run([str(PY),'-m','unittest',*TESTS,'-v'],cwd=ROOT,capture_output=True,text=True,timeout=60)
    log=r.stdout+r.stderr;(run/'regression.log').write_text(log);count=re.search(r'Ran (\d+) tests in',log)
    if r.returncode or not count:raise RuntimeError(log)
    cad=subprocess.run([str(PY),'-m','unittest','discover','-s','m3_design','-p','test_gnss.py','-v'],cwd=ROOT,capture_output=True,text=True,timeout=90)
    cadlog=cad.stdout+cad.stderr;(run/'cad_regression.log').write_text(cadlog);cadcount=re.search(r'Ran (\d+) tests in',cadlog)
    if cad.returncode or not cadcount:raise RuntimeError(cadlog)
    absent={};noport='/private/tmp/NO-M3-GNSS-'+uuid.uuid4().hex
    for action in ('capture','dump'):
        out=run/('absent_'+action+('.json' if action=='capture' else ''))
        cmd=[str(PY),'-m','diagnostics.usb',action,'--port',noport,'--manifest',str(HERE/'build_gnss_inspect/manifest.json'),
             '--out',str(out),'--assembly','NO-HARDWARE','--sectors','1']
        result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=15);(run/('absent_'+action+'.log')).write_text(result.stdout+result.stderr)
        e=json.loads((out if action=='capture' else out/'capture.json').read_text())
        if result.returncode!=3 or e['state']!='CONNECTION_FAILED' or e.get('samples',[]) or e.get('bytes',0):raise ValueError('No-device path invented results')
        if 'SerialException' not in e['error'] or 'No such file' not in e['error']:raise ValueError('Not actual absent-port failure')
        absent[action]=dict(state=e['state'],exit_code=result.returncode)
    sys.path.insert(0,str(ROOT))
    from diagnostics.test_gnss import frame,manifest
    from diagnostics.test_usb import Serial
    from diagnostics.usb import capture
    from diagnostics.mailbox import analyze_mailbox
    e=capture(Serial([frame(1),frame(2)]).client,manifest(),'SYNTHETIC-GNSS',run/'synthetic_capture.json',pause=lambda _:None,origin='SYNTHETIC_FIXTURE')
    (run/'synthetic_analysis.json').write_text(json.dumps(analyze_mailbox(e,binding,manifest()),indent=2)+'\n')
    (run/'ORIGIN.txt').write_text('Synthetic/scripted tests and real absent-port failures only. No physical board or GNSS signal captured.\n')
    if before!=input_hashes() or any(sha(ROOT/n)!=d for n,d in protected.items()):raise ValueError('Inputs changed during verification')
    result=dict(ok=True,tests=int(count[1]),cad_tests=int(cadcount[1]),builds=builds,inputs_sha256=before,
        protected_baselines=protected,run=str(run.relative_to(ROOT)),log_sha256=sha(run/'regression.log'),
        cad_log_sha256=sha(run/'cad_regression.log'),absent_port=absent,hardware_tested=False,flashed=False,
        rf_qualified=False,full_m3_complete=False,scope='GNSS/USB bench diagnostics; software and CAD evidence only')
    (OUT/'regression.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('builds','inputs_sha256','protected_baselines')},indent=2))
if __name__=='__main__':main()
