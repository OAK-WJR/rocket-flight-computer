"""Verify the assembly-only CAD revision with the unchanged production diagnostics."""
import hashlib,json,re,subprocess,sys,uuid
from pathlib import Path
from assembly_binding import make_binding
from verify_status_firmware import TESTS as PREVIOUS_TESTS,PROTECTED as PREVIOUS_PROTECTED,FOLDERS as STATUS_FOLDERS,check_build as shared_check
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;PY=ROOT/'diagnostics/.venv/bin/python'
OUT=HERE/'verification_assembly'
FOLDERS=tuple('build_assembly_'+m+s for m in ('inspect','record') for s in ('','_query'))
TESTS=[*PREVIOUS_TESTS,'diagnostics.test_assembly']
PROTECTED=dict(PREVIOUS_PROTECTED,**{'m3_design/M3_PDIAG_Review_v0_8.zip':'87a78b675789c7f26a1c7399ac99e2c3af750ae01dd4aaf9332c15356a8f087f'})
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check_build(folder):return shared_check(folder,'assembly')
def input_hashes():
    paths=[*HERE.glob('src/*'),*HERE.glob('test*.py'),*HERE.glob('tests/**/*'),*ROOT.glob('diagnostics/*.py'),
           *HERE.glob('*.py'),*HERE.glob('protocol*.json'),HERE/'pins_status.json',HERE/'ASSEMBLY_DIAGNOSTICS.md',
           ROOT/'M3_STATUS.md',ROOT/'m3_design/README.md',*ROOT.glob('m3_design/*assembly*.py'),
           *ROOT.glob('m3_design/assembly_review/*.json'),ROOT/'m3_design/assembly_review/ASSEMBLY_REVIEW.md']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file() and '__pycache__' not in p.parts}
def main():
    OUT.mkdir(exist_ok=True);run=OUT/('run_'+uuid.uuid4().hex[:12]);run.mkdir();before=input_hashes()
    protected={n:d for n,d in PROTECTED.items() if (ROOT/n).exists()}
    for n,d in protected.items():
        if sha(ROOT/n)!=d:raise ValueError('Protected archive changed '+n)
    binding=make_binding();builds={n:check_build(n) for n in FOLDERS}
    previous={}
    for folder in STATUS_FOLDERS:
        m=json.loads((HERE/folder/'manifest.json').read_text())
        for n,d in m['artifacts'].items():
            if sha(HERE/folder/n)!=d:raise ValueError('Previous binary changed '+folder+'/'+n)
        previous[folder]=dict(build_sha256=m['build_sha256'],artifacts=m['artifacts'])
    old=json.loads((HERE/'build_status_inspect/manifest.json').read_text())
    c_inputs={n:d for n,d in old['inputs'].items() if n.startswith('src/')}
    if any(sha(HERE/n)!=d for n,d in c_inputs.items()):raise ValueError('Production firmware changed beyond CAD binding')
    print('Four binary/CAD identities verified; production C and prior binaries preserved.',flush=True)
    logs={}
    for label,cmd in [('software',[str(PY),'-m','unittest',*TESTS,'-v']),
                      ('cad',[str(PY),'-m','unittest','discover','-s','m3_design','-p','test_assembly.py','-v'])]:
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr
        (run/(label+'.log')).write_text(log);count=re.search(r'Ran (\d+) tests in',log)
        if r.returncode or not count:raise RuntimeError(log)
        logs[label]=dict(tests=int(count[1]),sha256=sha(run/(label+'.log')))
        print(label,logs[label]['tests'],'passed',flush=True)
    absent={};noport='/private/tmp/NO-M3-ASSEMBLY-'+uuid.uuid4().hex
    for action in ('capture','dump'):
        out=run/('absent_'+action+('.json' if action=='capture' else ''))
        cmd=[str(PY),'-m','diagnostics.usb',action,'--port',noport,'--manifest',str(HERE/'build_assembly_inspect/manifest.json'),
             '--out',str(out),'--assembly','NO-HARDWARE','--sectors','1']
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=15);(run/('absent_'+action+'.log')).write_text(r.stdout+r.stderr)
        e=json.loads((out if action=='capture' else out/'capture.json').read_text())
        if r.returncode!=3 or e['state']!='CONNECTION_FAILED' or e.get('samples',[]) or e.get('bytes',0):raise ValueError('Absent-device path invented measurements')
        if 'No such file' not in e['error']:raise ValueError('Not an actual absent-port test')
        absent[action]=dict(state=e['state'],exit_code=r.returncode)
    sys.path.insert(0,str(ROOT))
    from diagnostics.test_assembly import frame,manifest
    from diagnostics.test_usb import Serial,crc
    from diagnostics.usb import capture
    from diagnostics.mailbox import analyze_mailbox
    frames=[frame(1),frame(2)];frames[1][153]|=8;frames[1][155]|=64;frames[1][158]=1;frames[1]=crc(frames[1])
    e=capture(Serial(frames).client,manifest(),'SYNTHETIC-ASSEMBLY-USB-FAULT',run/'synthetic_capture.json',pause=lambda _:None,origin='SYNTHETIC_FIXTURE')
    (run/'synthetic_analysis.json').write_text(json.dumps(analyze_mailbox(e,binding,manifest()),indent=2)+'\n')
    (run/'ORIGIN.txt').write_text('Software/fault injection and actual absent-port errors only. No physical board, RF, power transient or assembly fit was measured.\n')
    if before!=input_hashes():raise ValueError('Verification inputs changed during run')
    result=dict(ok=True,builds=builds,inputs_sha256=before,tests=logs,absent_port=absent,protected_archives=protected,
        previous_status_binaries=previous,production_c_unchanged=c_inputs,run=str(run.relative_to(ROOT)),
        hardware_tested=False,flashed=False,full_m3_complete=False)
    (OUT/'regression.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('builds','inputs_sha256','protected_archives','previous_status_binaries','production_c_unchanged')},indent=2))
if __name__=='__main__':main()
