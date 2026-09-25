"""Read-only bench-firmware result capture. No flash/reset/halt/write commands.

Only the reviewed 512-byte AXI SRAM record is added to the existing register
whitelist, after family identity. Firmware must be separately installed.
"""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys
import time
import uuid
import zlib

from .engine import HERE, digest, load_json
from .registers import CPUID_MASK, EXPECTED_CPUID, EXPECTED_FAMILY
from .transport import PyOCDReader, atomic_json, utc

FW = HERE.parent/'m3_firmware'
PROTOCOL = load_json(FW/'protocol.json')
UART_PROTOCOL = load_json(FW/'protocol_uart.json')
IMU_PROTOCOL = load_json(FW/'protocol_imu.json')
STORAGE_PROTOCOL = load_json(FW/'protocol_storage.json')
USB_PROTOCOL = load_json(FW/'protocol_usb.json')
GNSS_PROTOCOL = load_json(FW/'protocol_gnss.json')
STATUS_PROTOCOL = load_json(FW/'protocol_status.json')
ASSEMBLY_PROTOCOL = load_json(FW/'protocol_assembly.json')
STATUS_PROTOCOLS=(STATUS_PROTOCOL,ASSEMBLY_PROTOCOL)
GNSS_PROTOCOLS=(GNSS_PROTOCOL,*STATUS_PROTOCOLS)
USB_PROTOCOLS=(USB_PROTOCOL,*GNSS_PROTOCOLS)
STORE_PROTOCOLS=(STORAGE_PROTOCOL,*USB_PROTOCOLS)
PROTOCOLS=(PROTOCOL,UART_PROTOCOL,IMU_PROTOCOL,*STORE_PROTOCOLS)
IMU_PROTOCOLS=(IMU_PROTOCOL,*STORE_PROTOCOLS)
CAMERA_PROTOCOLS=(UART_PROTOCOL,IMU_PROTOCOL,*STORE_PROTOCOLS)
# An assembly revision changes the CAD identity, not the v8 on-wire layout.
# Do not let a second profile with the same version alter the decoder schema.
if ({k:v for k,v in ASSEMBLY_PROTOCOL.items() if k not in ('profile','board_sha256')} !=
    {k:v for k,v in STATUS_PROTOCOL.items() if k not in ('profile','board_sha256')}):
    raise ValueError('Assembly revision changed the wire protocol')
WIRE_PROTOCOLS={x['version']:x for x in PROTOCOLS if x!=ASSEMBLY_PROTOCOL}
W = PROTOCOL['words']
# This is a range grant, so a mutable manifest may not enlarge/readdress it.
if (PROTOCOL['address'], PROTOCOL['bytes'], PROTOCOL['version']) != (0x24000000, 512, 2):
    raise ValueError('Protocol disagrees with reviewed SRAM range')
if (UART_PROTOCOL['address'], UART_PROTOCOL['bytes'], UART_PROTOCOL['version']) != (0x24000000,512,3):
    raise ValueError('UART protocol disagrees with the same reviewed SRAM range')
if (IMU_PROTOCOL['address'],IMU_PROTOCOL['bytes'],IMU_PROTOCOL['version']) != (0x24000000,512,4):
    raise ValueError('IMU protocol disagrees with the same reviewed SRAM range')
if (STORAGE_PROTOCOL['address'],STORAGE_PROTOCOL['bytes'],STORAGE_PROTOCOL['version']) != (0x24000000,1024,5):
    raise ValueError('Storage protocol disagrees with reviewed v5 range')
if (USB_PROTOCOL['address'],USB_PROTOCOL['bytes'],USB_PROTOCOL['version']) != (0x24000000,1024,6):
    raise ValueError('USB protocol disagrees with reviewed v6 range')
if (GNSS_PROTOCOL['address'],GNSS_PROTOCOL['bytes'],GNSS_PROTOCOL['version']) != (0x24000000,1024,7):
    raise ValueError('GNSS protocol disagrees with reviewed v7 range')
if (STATUS_PROTOCOL['address'],STATUS_PROTOCOL['bytes'],STATUS_PROTOCOL['version']) != (0x24000000,1024,8):
    raise ValueError('Power status protocol disagrees with reviewed v8 range')


def manifest_protocol(manifest):
    p=manifest.get('protocol')
    if p not in PROTOCOLS or manifest.get('profile') != p['profile']:
        raise ValueError('Unsupported manifest protocol/profile')
    if p in CAMERA_PROTOCOLS:
        if manifest.get('board_sha256') != p['board_sha256']:
            raise ValueError('UART manifest does not bind the reviewed board')
        options=manifest.get('build_options',{})
        if options.get('board')!=('assembly' if p==ASSEMBLY_PROTOCOL else 'status' if p==STATUS_PROTOCOL else 'gnss' if p==GNSS_PROTOCOL else 'usb' if p==USB_PROTOCOL else 'uart') or type(options.get('camera_query')) is not bool:
            raise ValueError('UART camera mode is missing from the build identity')
        if p in IMU_PROTOCOLS and options.get('imu_samples') is not True:
            raise ValueError('IMU acquisition is missing from the build identity')
        if p in STORE_PROTOCOLS and options.get('storage') not in ('inspect','record'):
            raise ValueError('Storage mode is missing from the build identity')
    return p


def word(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xffffffff:
        raise ValueError('Invalid 32-bit mailbox word')
    return value


def prom_crc4(prom):
    if len(prom) != 8 or any(type(v) is not int or not 0 <= v <= 65535 for v in prom):
        raise ValueError('Invalid PROM words')
    raw = bytearray(struct.pack('>8H', *prom)); raw[15] = 0
    rem = 0
    for b in raw:
        rem ^= b
        for _ in range(8):
            rem = ((rem << 1) ^ (0x3000 if rem & 0x8000 else 0)) & 0xffff
    return (rem >> 12) & 15


def prom_ok(w):
    prom = w[35:43]
    try:
        return (w[34] == 0x77 and
                not all(v==0 for v in prom[1:7]) and not all(v==65535 for v in prom[1:7]) and
                prom_crc4(prom) == w[43] == w[44] == (prom[7] & 15))
    except ValueError:
        return False


def decode(words):
    if not isinstance(words, list) or len(words) not in (128,256):
        raise ValueError('Mailbox must contain 128 or 256 words')
    data = bytearray(struct.pack('<'+str(len(words))+'I', *(word(v) for v in words)))
    if words[W['MAGIC']] != PROTOCOL['magic']:
        raise ValueError('No supported bench-firmware mailbox; not a hardware failure diagnosis')
    p=WIRE_PROTOCOLS.get(words[W['VERSION']])
    if p is None or words[W['LENGTH']] != p['bytes'] or len(data)!=p['bytes']:
        raise ValueError('Unsupported mailbox version or length')
    if words[W['SEQUENCE']] & 1:
        raise ValueError('Torn mailbox: writer is updating')
    data[12:16] = b'\0'*4
    if zlib.crc32(data[:-4]) != words[-1]:
        raise ValueError('Mailbox CRC32 mismatch; no results may be accepted')
    if words[W['CAPABILITIES']] != p['capabilities']:
        raise ValueError('Unexpected firmware capabilities')
    if words[W['STATE']] not in PROTOCOL['states'].values():
        raise ValueError('Unknown firmware state')
    for name in ('HSE_STATUS', 'IMU_STATUS', 'BARO_STATUS', 'FLASH_STATUS', 'ADC_STATUS', 'BARO_SAMPLE_STATUS'):
        if words[W[name]] not in PROTOCOL['statuses'].values():
            raise ValueError('Unknown result status: ' + name)
    if p in CAMERA_PROTOCOLS:
        cw=p['words']
        if (words[cw['CAMERA_STATUS']] not in range(4) or words[cw['CAMERA_MODE']] not in (0,1) or
            words[cw['CAMERA_RAW_LENGTH']]>32 or words[cw['CAMERA_VALID_LENGTH']] not in (0,5)):
            raise ValueError('Invalid camera result encoding')
    if p in IMU_PROTOCOLS:
        iw=p['words']
        if (words[iw['IMU_SAMPLE_STATUS']] not in range(4) or
            words[iw['IMU_SAMPLE_ERROR']] not in range(12) or words[iw['IMU_INIT_ERROR']] not in range(12) or
            words[iw['IMU_EVIDENCE']] & 0x00f80000 or words[iw['IMU_ERROR_HISTORY']] & ~0xffe or
            words[iw['IMU_RAW']+3] & 0xffff0000):
            raise ValueError('Invalid IMU result encoding or padding')
    if p in STORE_PROTOCOLS:
        reserved=words[153:255] if p==STORAGE_PROTOCOL else ([] if p==STATUS_PROTOCOL else words[153:160])+(words[183:184] if p in GNSS_PROTOCOLS else words[183:255])
        if (words[127] or any(reserved) or words[128] not in (0,1) or words[129] not in range(4) or
            words[130] not in range(16) or words[131]&~0xfffe or words[149] not in (0,1) or
            any(words[i]>4096 for i in (138,139,140,142,143)) or words[152]>(2 if p in GNSS_PROTOCOLS else 4) or
            words[141]>65536 or words[151]>65536):raise ValueError('Invalid storage encoding')
        if p in USB_PROTOCOLS and (words[160] not in range(7) or words[161] not in range(7) or words[162]&~15):
            raise ValueError('Invalid USB encoding')
        if p in GNSS_PROTOCOLS and (words[184] not in range(8) or words[185] not in range(3) or
            words[186]&~0x7f8 or words[187]&~63 or words[190]&~15 or
            (words[205] and (not 40<=words[205]<=512 or (words[205]-40)%30))):
            raise ValueError('Invalid GNSS encoding')
        if p==STATUS_PROTOCOL and (words[153]&~127 or words[154]&~0xffff or words[155]&~0x00530053):
            raise ValueError('Invalid power status encoding')
        if p==STATUS_PROTOCOL:
            f,g,h=words[153:156]
            if ((not f&1 and any(words[153:160])) or
                (f&1 and ((h&(~g)&0x53)!=((~g)&0x53) or ((h>>16)&g&0x53)!=(g&0x53))) or
                (bool(f&8)!=bool(words[158])) or (f&64 and words[158]!=0xffffffff)):
                raise ValueError('Inconsistent power status history')
    elif any(words[i] for i in range(82 if p==PROTOCOL else 112 if p==UART_PROTOCOL else 127,127)):
        raise ValueError('Reserved protocol fields are not zero')
    return dict(words=words, board_sha256=data[32:64].hex(), build_sha256=data[64:96].hex(),
                uid=words[26:29], heartbeat=words[6], uptime_ms=words[5], state=words[4],version=p['version'])


def read_consistent(reader, attempts=5, pause=time.sleep, protocol=PROTOCOL):
    """Preserve rejected frames as evidence, and never replace a bus fault by 0."""
    history = []
    for _ in range(attempts):
        row = {'before': None, 'after': None, 'words': [], 'error': None}
        try:
            row['before'] = word(reader.read_mailbox_word(3))
            if row['before'] & 1:
                raise ValueError('Writer busy')
            # Check the 16-byte header before entering v2's expanded area.
            # A v1 firmware initialized only 256 bytes; do not read beyond its
            # record into potentially uninitialized AXI SRAM/ECC locations.
            for i in range(4):
                row['words'].append(word(reader.read_mailbox_word(i)))
            if protocol not in PROTOCOLS:raise ValueError('Unknown expected protocol')
            if row['words'][:3] != [protocol['magic'],protocol['version'],protocol['bytes']]:
                raise ValueError('Unsupported mailbox header; extended SRAM was not read')
            if protocol in STORE_PROTOCOLS:reader.enable_storage_mailbox()
            for i in range(4,protocol['bytes']//4):
                row['words'].append(word(reader.read_mailbox_word(i)))
            row['after'] = word(reader.read_mailbox_word(3))
            if row['before'] != row['after'] or row['words'][3] != row['before']:
                raise ValueError('Sequence changed during capture')
            d = decode(row['words'])
            if d['state'] == 3 and any(row['words'][W[n]] == 1 for n in ('ADC_STATUS','BARO_SAMPLE_STATUS')):
                raise ValueError('Acquisition still in progress')
            if d['state']==3 and protocol in IMU_PROTOCOLS and row['words'][protocol['words']['IMU_SAMPLE_STATUS']]==1:
                raise ValueError('IMU acquisition still in progress')
        except Exception as e:
            row['error'] = type(e).__name__ + ': ' + str(e)
        history.append(row)
        if row['error'] is None:
            return {'accepted': len(history)-1, 'attempts': history}
        pause(.05)
    return {'accepted': None, 'attempts': history}


def capture_mailbox(reader, binding, manifest, assembly, output, origin='SWD_CAPTURE', pause=time.sleep, sample_count=2, interval=1.2):
    output = Path(output)
    if output.exists(): raise FileExistsError(str(output))
    protocol=manifest_protocol(manifest)
    if binding['board_sha256'] != manifest['board_sha256'] or binding['profile'] != protocol['profile']:
        raise ValueError('Binding/build/protocol mismatch')
    if not isinstance(assembly,str) or not assembly.strip(): raise ValueError('Assembly ID required')
    if origin not in ('SWD_CAPTURE','SYNTHETIC_FIXTURE'): raise ValueError('Unknown evidence origin')
    if type(sample_count) is not int or not 2 <= sample_count <= 30 or not 1.2 <= interval <= 10:
        raise ValueError('Capture bounds: 2..30 samples, interval 1.2..10 seconds')
    s = dict(schema=1, expected_samples=sample_count, interval_s=interval, origin=origin, capture_id=str(uuid.uuid4()), assembly_id=assembly,
             board_sha256=binding['board_sha256'], expected_build_sha256=manifest['build_sha256'],
             captured_at=utc(), state='STARTED', driver=None, identity={}, samples=[], error=None)
    started = time.monotonic(); atomic_json(output,s)
    try:
        s['driver'] = reader.open()
        for name in ('CPUID','DBGMCU_IDCODE'):
            s['identity'][name] = word(reader.read(name)); atomic_json(output,s)
        if (s['identity']['CPUID'] & CPUID_MASK != EXPECTED_CPUID or
            s['identity']['DBGMCU_IDCODE'] & 0xfff != EXPECTED_FAMILY):
            raise ValueError('Wrong MCU family; SRAM was not read')
        for name in ('UID0','UID1','UID2'):
            s['identity'][name] = word(reader.read(name))
        reader.enable_mailbox()
        for i in range(sample_count):
            if i: pause(interval)
            sample = read_consistent(reader, pause=pause,protocol=protocol)
            sample['elapsed_ms'] = (time.monotonic()-started)*1000
            s['samples'].append(sample); atomic_json(output,s)
        s['state'] = 'CAPTURED' if all(x['accepted'] is not None for x in s['samples']) else 'PARTIAL'
    except Exception as e:
        s['state'], s['error'] = 'CONNECTION_FAILED', type(e).__name__ + ': ' + str(e)
    finally:
        try: reader.close()
        except Exception as e: s['state'], s['error'] = 'CLEANUP_FAILED', type(e).__name__ + ': ' + str(e)
        if getattr(reader,'guard',None) is not None: s['debug_address_operations'] = reader.guard.operations
        s['finished_at'] = utc(); atomic_json(output,s)
    return s


def analyze_mailbox(s, binding, manifest):
    protocol=manifest_protocol(manifest)
    if s.get('schema') != 1 or s.get('origin') not in ('SWD_CAPTURE','USB_CAPTURE','SYNTHETIC_FIXTURE'):
        raise ValueError('Not supported evidence')
    if (s.get('board_sha256') != binding['board_sha256'] or binding['board_sha256'] != manifest['board_sha256'] or
        s.get('expected_build_sha256') != manifest['build_sha256'] or binding['profile']!=protocol['profile']):
        raise ValueError('Wrong board/build binding')
    checks = []; measurements = []
    def add(code,status,evidence,next_step=''):
        checks.append(dict(id=code,status=status,evidence=evidence,next_step=next_step))
    samples = []
    ident = s.get('identity',{})
    for value in ident.values(): word(value)
    family_ok = (ident.get('CPUID',0) & CPUID_MASK == EXPECTED_CPUID and
                 ident.get('DBGMCU_IDCODE',0) & 0xfff == EXPECTED_FAMILY)
    usb_capture=s.get('transport')=='USB_CDC'
    if s.get('origin')=='USB_CAPTURE' and not usb_capture:raise ValueError('Missing USB transport evidence')
    if usb_capture:
        if protocol not in USB_PROTOCOLS:raise ValueError('USB capture requires protocol v6/v7')
        family_ok=ident.get('DBGMCU_IDCODE',0)&0xfff==EXPECTED_FAMILY
        add('IDENTITY_SOURCE','INFO','USB identity comes from firmware; it is not independent SWD or cryptographic authentication.')
    if not family_ok:
        observed = all(n in ident for n in ('CPUID','DBGMCU_IDCODE'))
        add('TARGET','FAIL' if observed else 'INCONCLUSIVE',
            'MCU family identity mismatches the expected target.' if observed else 'No complete MCU identity was read; hardware condition is unknown.',
            s.get('error') or 'No mailbox result is accepted until target identity is confirmed.')
    for i, raw in enumerate(s.get('samples',[])):
        try:
            k = raw['accepted']
            if isinstance(k,bool) or not isinstance(k,int) or not 0 <= k < len(raw['attempts']):
                raise ValueError('No consistent accepted record')
            a = raw['attempts'][k]
            if a['error'] is not None or a['before'] != a['after'] or a['before'] != a['words'][3]:
                raise ValueError('Invalid accepted sequence')
            d = decode(a['words'])
            if d['version']!=protocol['version']:raise ValueError('Wrong firmware protocol for this manifest')
            if not family_ok or d['uid'] != [word(ident[n]) for n in ('UID0','UID1','UID2')]:
                raise ValueError('Firmware/capture UID mismatch')
            if usb_capture and d['words'][25]!=ident.get('DBGMCU_IDCODE'):
                raise ValueError('Firmware device identity changed')
            if d['board_sha256'] != binding['board_sha256'] or d['build_sha256'] != manifest['build_sha256']:
                raise ValueError('Different board/build firmware; do not use its pass bits')
            samples.append(d)
        except (KeyError,TypeError,ValueError,IndexError) as e:
            add('RECORD_'+str(i),'INCONCLUSIVE',str(e),'Check installed firmware/build and raw attempts; missing data is not a failed sensor.')
    expected = s.get('expected_samples',2)
    trusted = (type(expected) is int and 2 <= expected <= 30 and s.get('state') == 'CAPTURED' and
               len(samples) == expected and len(s.get('samples',[])) == expected)
    if not trusted:
        add('CAPTURE','INCONCLUSIVE','The requested bound, consistent records were not captured. State='+str(s.get('state')))
    else:
        a,b = samples[0],samples[-1]
        live = all(0 < ((y['heartbeat']-x['heartbeat']) & 0xffffffff) < 0x80000000 and
                   0 < ((y['uptime_ms']-x['uptime_ms']) & 0xffffffff) < 0x80000000
                   for x,y in zip(samples,samples[1:]))
        add('FIRMWARE_LIVENESS','PASS' if live else 'INCONCLUSIVE',
            f"heartbeat {a['heartbeat']} -> {b['heartbeat']}; uptime {a['uptime_ms']} -> {b['uptime_ms']} ms",
            'A stall or reset requires another capture and reset/clock evidence; a stable old record is not a pass.')
        w = b['words']
        add('TEST_SEQUENCE','PASS' if b['state']==3 and live else 'INCONCLUSIVE',
            f"state={b['state']}; stage={w[W['STAGE']]}; completed_ms={w[W['TEST_FINISHED_MS']]}")
        for code,key,detail,consistent,next_step in [
            ('HSE_READY','HSE_STATUS',f"RCC_CR during test=0x{w[30]:08x}",bool(w[30] & (1<<17)),
             'If not ready, check Y1/C25/C26/power. Ready bit does not measure frequency or oscillator margin.'),
            ('IMU_ID','IMU_STATUS',f'WHO_AM_I=0x{w[32]:02x}',w[32]==0xe9,
             'Check 3V3A, U4 power/pin orientation, PB3/PB4/PB5/PB7 wiring. Does not prove IMU samples or axes.'),
            ('BARO_PROM','BARO_STATUS',f'address=0x{w[34]:02x}; PROM={w[35:43]}; CRC={w[43]}/{w[44]}; error={w[47]}',
             prom_ok(w),
             'Error 1=SCL held low, 2=SDA held low, 3=NACK, 4=CRC mismatch, 5=empty PROM. Check U5/R12/R13/CSB/3V3A; CRC does not establish sensor accuracy.'),
            ('FLASH_JEDEC','FLASH_STATUS',f'JEDEC=0x{w[46]:06x}',w[46]==0xef4018,
             'Check U3 supply/orientation/NCS/CLK/IO0/IO1. This does not exercise IO2/IO3 as data lanes or write/erase/storage integrity.')]:
            result = {0:'NOT_TESTED',1:'RUNNING',2:'PASS',3:'FAIL'}[w[W[key]]]
            if result=='PASS' and not consistent: result='FAIL'
            if result=='PASS' and (not live or b['state']!=3): result='INCONCLUSIVE'
            add(code,result,detail,next_step)
        if protocol==PROTOCOL:
            add('CAMERA_DISABLED','INFO' if w[50]==0 else 'FAIL',f'PD3 digital readback={w[50]}',
                'Low digital readback is not proof of zero camera voltage; verify J9 externally.')
        from .acquisition import sample_measurements, measurement_checks
        measurements = [sample_measurements(d['words'],W) for d in samples]
        for c in measurement_checks(samples,W,live and b['state']==3):
            add(*c)
        if protocol in CAMERA_PROTOCOLS:
            from .camera import camera_checks,camera_measurement
            for c in camera_checks(w,manifest,live and b['state']==3):add(*c)
            for record,d in zip(measurements,samples):record['camera']=camera_measurement(d['words'],protocol)
        if protocol in IMU_PROTOCOLS:
            from .imu import imu_checks
            checks_imu,records=imu_checks(samples,protocol,live and b['state']==3)
            for c in checks_imu:add(*c)
            for record,imu in zip(measurements,records):record['imu']=imu
        if protocol in STORE_PROTOCOLS:
            from .storage import live_checks
            for c in live_checks(samples,manifest,live and b['state']==3):add(*c)
        if protocol in USB_PROTOCOLS:
            from .usb import live_checks as usb_checks
            for c in usb_checks(samples,live and b['state']==3,usb_capture):add(*c)
        if protocol in GNSS_PROTOCOLS:
            from .gnss import checks as gnss_checks
            cg,rg=gnss_checks(samples,live and b['state']==3)
            for c in cg:add(*c)
            for record,gnss in zip(measurements,rg):record['gnss']=gnss
        if protocol in STATUS_PROTOCOLS:
            from .power_status import checks as power_checks
            cp,rp=power_checks(samples,live and b['state']==3)
            for c in cp:add(*c)
            for record,power in zip(measurements,rp):record['power_status']=power
    if protocol not in IMU_PROTOCOLS:add('IMU_SAMPLES','NOT_TESTED','Identity-only firmware does not acquire IMU samples.')
    elif not trusted:add('IMU_SAMPLES','INCONCLUSIVE','No complete trusted IMU capture.')
    for name in ('SENSOR_ACCURACY','FLASH_QUAD_DATA','LOGGING_POWER_LOSS','USB_ENUMERATION',
                 'WATCHDOG_RESET','THERMAL_TRANSIENTS'):
        if name=='FLASH_QUAD_DATA' and protocol in STORE_PROTOCOLS and trusted:continue
        if name=='USB_ENUMERATION' and protocol in USB_PROTOCOLS and trusted:continue
        add(name,'NOT_TESTED','Not implemented or measured by this bench firmware.')
    if protocol==PROTOCOL:add('CAMERA_UART','NOT_TESTED','Not implemented by v0.2 firmware.')
    else:add('CAMERA_ELECTRICAL_QUALIFICATION','NOT_TESTED','No real rail, logic-level, leakage or timing measurements are provided by this mailbox.')
    return dict(schema=1, assembly_id=s.get('assembly_id'), board_sha256=binding['board_sha256'],
                build_sha256=manifest['build_sha256'], capture_id=s.get('capture_id'),
                synthetic=s['origin']=='SYNTHETIC_FIXTURE',
                origin=s['origin'],transport=s.get('transport','SWD'),
                overall='ISSUES_FOUND' if any(c['status']=='FAIL' for c in checks) else 'INCOMPLETE',
                hardware_qualified=False,fabrication_release=False,checks=checks,measurements=measurements)


def safe_origin(report):
    return 'SYNTHETIC_FIXTURE' if report['synthetic'] else report.get('origin','SWD_CAPTURE')


def report_file(raw, out, binding, manifest):
    r = analyze_mailbox(load_json(raw), binding, manifest)
    out = Path(out); out.mkdir(parents=True,exist_ok=False)
    r['input_sha256'] = digest(raw); atomic_json(out/'report.json',r)
    lines = ['# M3 bench self-test record', '', '**Synthetic data, not a measurement.**' if r['synthetic'] else '**This record is not whole-board acceptance.**',
             '', 'Status: '+r['overall'], '', '| Check | Result | Evidence and next step |','|---|---|---|']
    for c in r['checks']:
        text = (c['evidence']+' '+c['next_step']).replace('|','/').replace('\n',' ')
        lines.append(f"| {c['id']} | {c['status']} | {text} |")
    with (out/'measurements.jsonl').open('w') as stream:
        for record in r['measurements']:
            stream.write(json.dumps(dict(origin=safe_origin(r),assembly_id=r['assembly_id'],
                                        board_sha256=r['board_sha256'],build_sha256=r['build_sha256'],
                                        capture_id=r['capture_id'],**record),allow_nan=False)+'\n')
    (out/'report.md').write_text('\n'.join(lines)+'\n'); print(out/'report.md')
    return 2 if r['overall']=='ISSUES_FOUND' else 0


def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    for name in ('capture','_worker','report'):
        q=sub.add_parser(name)
        q.add_argument('--binding',type=Path,required=True)
        q.add_argument('--manifest',type=Path,required=True)
        q.add_argument('--out',type=Path,required=True)
        if name=='report':q.add_argument('snapshot',type=Path)
        else:
            q.add_argument('--probe-id',required=True);q.add_argument('--assembly-id',required=True)
            q.add_argument('--samples',type=int,default=2);q.add_argument('--interval',type=float,default=1.2)
    a=p.parse_args(); binding=load_json(a.binding); manifest=load_json(a.manifest)
    if a.command=='report':return report_file(a.snapshot,a.out,binding,manifest)
    if a.command=='_worker':
        capture_mailbox(PyOCDReader(a.probe_id),binding,manifest,a.assembly_id,a.out,sample_count=a.samples,interval=a.interval);return 0
    if not 2 <= a.samples <= 30 or not 1.2 <= a.interval <= 10:
        raise ValueError('Capture bounds: 2..30 samples, interval 1.2..10 seconds')
    a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
    raw=a.out/'mailbox.json'
    cmd=[sys.executable,'-m','diagnostics.mailbox','_worker','--binding',str(a.binding.resolve()),
         '--manifest',str(a.manifest.resolve()),'--out',str(raw),'--probe-id',a.probe_id,'--assembly-id',a.assembly_id,'--samples',str(a.samples),'--interval',str(a.interval)]
    with (a.out/'driver.log').open('w') as log:
        proc=subprocess.Popen(cmd,cwd=HERE.parent,stdout=log,stderr=subprocess.STDOUT)
        try:code=proc.wait(timeout=25 + (a.samples-2)*(a.interval+3))
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:proc.wait(timeout=3)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
            code=-1
    if not raw.exists():raise RuntimeError('No hardware evidence produced; see driver.log')
    if code:
        s=load_json(raw);s['state']='ABORTED';s['error']='worker failed/timed out';atomic_json(raw,s)
    r=report_file(raw,a.out/'analysis',binding,manifest)
    return r if load_json(raw)['state']=='CAPTURED' else 3


if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,RuntimeError,KeyError) as e:
        print(type(e).__name__+': '+str(e),file=sys.stderr);raise SystemExit(3)
