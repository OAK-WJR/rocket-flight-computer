"""Record bounded software tests and the absent-probe error path. No flashing."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
OUT=HERE/'verification'
PY=ROOT/'diagnostics/.venv/bin/python'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    files=[*HERE.glob('*.py'),*HERE.glob('*.json'),*HERE.glob('src/*'),*HERE.glob('tests/**/*'),
           *ROOT.glob('diagnostics/*.py'),HERE/'linker.ld',*HERE.glob('*.md'),
           ROOT/'M3_STATUS.md',ROOT/'diagnostics/README.md',HERE/'research/acquisition_sources.json']
    inputs={str(p.relative_to(ROOT)):sha(p) for p in files if p.is_file() and p.name!='package_check.json'}
    board=ROOT/'m3_design/power_review/m3.kicad_pcb'
    board_sha=sha(board)
    build=json.loads((HERE/'build/manifest.json').read_text())
    if build['board_sha256']!=board_sha:raise ValueError('Build is stale')
    for name,digest in build['inputs'].items():
        if sha(HERE/name)!=digest:raise ValueError('Build source changed: '+name)
    cmd=[str(PY),'-m','unittest','diagnostics.test_diagnostics','diagnostics.test_cli_binding',
         'diagnostics.test_mailbox','m3_firmware.test_firmware','diagnostics.test_acquisition','-v']
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=60)
    log=r.stdout+r.stderr;(OUT/'regression.log').write_text(log)
    match=re.search(r'Ran (\d+) tests in',log)
    if r.returncode or not match:raise RuntimeError(log)
    inventory=subprocess.run([str(PY),'-m','diagnostics','probes'],cwd=ROOT,capture_output=True,text=True,timeout=15)
    if inventory.returncode:raise RuntimeError(inventory.stderr)
    probes=json.loads(inventory.stdout);(OUT/'probe_inventory.json').write_text(inventory.stdout)
    absent='NO-DEVICE-SELFTEST-'+uuid.uuid4().hex
    if any(p['id']==absent for p in probes['probes']):raise RuntimeError('Unexpected probe identity')
    no_probe=OUT/('absent_probe_'+uuid.uuid4().hex[:10])
    command=[str(PY),'-m','diagnostics.mailbox','capture','--probe-id',absent,'--assembly-id','NO-HARDWARE',
             '--binding',str(HERE/'build/binding.json'),'--manifest',str(HERE/'build/manifest.json'),
             '--out',str(no_probe)]
    failure=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=35)
    raw=json.loads((no_probe/'mailbox.json').read_text())
    if failure.returncode!=3 or raw['state']!='CONNECTION_FAILED' or raw['samples'] or raw['identity']:
        raise RuntimeError('Absent-probe path produced unexpected evidence')
    if sha(board)!=board_sha or any(sha(ROOT/n)!=v for n,v in inputs.items()):
        raise ValueError('Inputs changed during verification')
    record=dict(schema=1,ok=True,tests=int(match[1]),scripted_bus_cases=14,scripted_adc_cases=13,
                board_sha256=board_sha,build_sha256=build['build_sha256'],inputs_sha256=inputs,
                log_sha256=sha(OUT/'regression.log'),absent_probe_capture=str(no_probe.relative_to(ROOT)),
                absent_probe_exit=failure.returncode,hardware_tested=False,flashed=False,
                scope='Host CRC/ABI/math/fault tests, scripted GPIO and ADC responses; not hardware or electrical simulation')
    (OUT/'regression.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='inputs_sha256'},indent=2))


if __name__=='__main__':main()
