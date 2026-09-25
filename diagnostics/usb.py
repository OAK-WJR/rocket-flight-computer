"""Explicit-port, bounded USB CDC diagnostic capture and log download.

Only snapshot/Flash-read requests exist. No target erase, reset, flash install or
arbitrary MCU memory access. CRC detects errors, not a counterfeit target.
"""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import struct
import time
import uuid
import zlib
from .mailbox import USB_PROTOCOL, USB_PROTOCOLS, decode, manifest_protocol, analyze_mailbox
from .registers import EXPECTED_FAMILY
from .transport import atomic_json, utc

SIZE=0x1000000
MAX=1024

def request_bytes(op,request,address,length):
    if type(op) is not int or op not in (1,2):raise ValueError('Only snapshot and Flash read supported')
    if any(type(x) is not int or not 0<=x<=0xffffffff for x in (request,address,length)):
        raise ValueError('Invalid unsigned request fields')
    if op==1 and (address,length)!=(0,MAX):
        raise ValueError('Invalid read length')
    if op==2 and not (0<=address<SIZE and 0<length<=MAX and address<=SIZE-length):
        raise ValueError('Flash bounds')
    data=struct.pack('<4sHHIII',b'M3RQ',1,op,request,address,length)
    return data+struct.pack('<I',zlib.crc32(data))

class DeviceError(RuntimeError):pass

class Client:
    def __init__(self,serial,timeout=3.0,clock=time.monotonic):
        if not .1<=timeout<=10:raise ValueError('Request deadline must be .1..10 seconds')
        self.serial=serial;self.timeout=timeout;self.clock=clock
        self.next=secrets.randbits(32);self.last=None

    def request(self,op,address,length):
        ident=self.next;self.next=(ident+1)&0xffffffff
        tx=request_bytes(op,ident,address,length);rx=bytearray();end=self.clock()+self.timeout
        self.last=dict(request_id=ident,op=op,address=address,length=length,tx_hex=tx.hex(),rx_hex='',error=None)
        def read(n):
            result=bytearray()
            while len(result)<n:
                if self.clock()>=end:raise TimeoutError('USB reply deadline; partial bytes preserved')
                block=self.serial.read(n-len(result))
                if not isinstance(block,bytes) or len(block)>n-len(result):raise ValueError('Invalid transport read')
                result.extend(block);rx.extend(block);self.last['rx_hex']=rx.hex()
            return bytes(result)
        try:
            done=0
            while done<len(tx):
                if self.clock()>=end:raise TimeoutError('USB request deadline')
                n=self.serial.write(tx[done:])
                if type(n) is not int or not 0<n<=len(tx)-done:raise IOError('Short/invalid USB write')
                done+=n
            header=read(24)
            magic,version,status,seq,at,n,echo_op=struct.unpack('<4sHHIIII',header)
            if (magic,version,seq,at,echo_op)!=(b'M3RS',1,ident,address,op):
                raise ValueError('USB response identity/header mismatch; no resync or retry')
            if status not in range(4) or n!=(length if status==0 else 0) or n>MAX:
                raise ValueError('USB response status/length mismatch')
            body=read(n);crc=read(4)
            if zlib.crc32(header+body)!=struct.unpack('<I',crc)[0]:raise ValueError('USB response CRC mismatch')
            if status:raise DeviceError({1:'Bad request',2:'Storage/snapshot busy; no automatic retry',3:'Device read failed'}[status])
            return body
        except Exception as e:
            self.last['error']=type(e).__name__+': '+str(e);raise

    def close(self):self.serial.close()

def serial_client(port):
    import importlib.metadata
    import inspect
    import serial
    if importlib.metadata.version('pyserial')!='3.5':raise RuntimeError('Expected pinned pyserial 3.5')
    # Construct before open so DTR/RTS values are explicit. This is a CDC byte
    # stream, not a 1200-baud touch/reset or a vendor control command.
    s=serial.Serial(port=None,baudrate=115200,timeout=.05,write_timeout=.5)
    s.dtr=True;s.rts=False;s.port=port
    try:
        s.open();s.reset_input_buffer();client=Client(s)
        source=Path(inspect.getfile(type(s)))
        client.driver=dict(pyserial='3.5',port=port,source=source.name,sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        return client
    except Exception:s.close();raise

def validate_manifest(m):
    if manifest_protocol(m) not in USB_PROTOCOLS:raise ValueError('USB requires the exact v6/v7 board/firmware protocol')
    expected=hashlib.sha256(json.dumps({'inputs':m['inputs'],'options':m['build_options']},sort_keys=True).encode()).hexdigest()
    if m['build_sha256']!=expected:raise ValueError('Manifest build hash mismatch')
    return m

def bound_snapshot(client,m,uid=None):
    raw=client.request(1,0,MAX)
    d=decode(list(struct.unpack('<256I',raw)))
    if (d['version']!=m['protocol']['version'] or d['board_sha256']!=m['board_sha256'] or d['build_sha256']!=m['build_sha256'] or
        d['words'][25]&0xfff!=EXPECTED_FAMILY or d['uid'] in ([0,0,0],[0xffffffff]*3)):
        raise ValueError('Firmware board/build/device mismatch; no result accepted')
    if uid is not None and d['uid']!=uid:raise ValueError('MCU identity changed during connection')
    return d

def capture(factory,m,assembly,out,samples=2,interval=1.2,pause=time.sleep,origin='USB_CAPTURE'):
    validate_manifest(m);out=Path(out)
    if out.exists():raise FileExistsError(str(out))
    if type(samples) is not int or not 2<=samples<=30 or not 1.2<=interval<=10:raise ValueError('Capture bounds')
    if not isinstance(assembly,str) or not assembly.strip():raise ValueError('Assembly ID required')
    if origin not in ('USB_CAPTURE','SYNTHETIC_FIXTURE'):raise ValueError('Origin')
    e=dict(schema=1,transport='USB_CDC',origin=origin,capture_id=str(uuid.uuid4()),assembly_id=assembly,
        board_sha256=m['board_sha256'],expected_build_sha256=m['build_sha256'],expected_samples=samples,
        interval_s=interval,captured_at=utc(),state='STARTED',identity={},samples=[],exchanges=[],error=None,
        identity_source='FIRMWARE_REPORTED_NOT_INDEPENDENT',sequence_method='FIRMWARE_SEQCOPY')
    atomic_json(out,e);client=None;uid=None
    try:
        client=factory();e['driver']=getattr(client,'driver',None)
        for i in range(samples):
            if i:pause(interval)
            try:d=bound_snapshot(client,m,uid)
            finally:e['exchanges'].append(client.last);atomic_json(out,e)
            if uid is None:
                uid=d['uid'];e['identity']=dict(DBGMCU_IDCODE=d['words'][25],**dict(zip(('UID0','UID1','UID2'),uid)))
            seq=d['words'][3]
            e['samples'].append(dict(accepted=0,attempts=[dict(before=seq,after=seq,words=d['words'],error=None)]))
            atomic_json(out,e)
        e['state']='CAPTURED'
    except Exception as x:e['state']='CONNECTION_FAILED' if not e['samples'] else 'PARTIAL';e['error']=type(x).__name__+': '+str(x)
    finally:
        if client is not None:
            try:client.close()
            except Exception as x:e['state']='CLEANUP_FAILED';e['error']=type(x).__name__+': '+str(x)
        e['finished_at']=utc();atomic_json(out,e)
    return e

def dump(factory,m,out,sectors=4096,origin='USB_CAPTURE'):
    validate_manifest(m);out=Path(out)
    # A quiescent inspect image prevents the source changing while downloading.
    if m['build_options']['storage']!='inspect':raise ValueError('USB dump requires inspect firmware')
    if type(sectors) is not int or not 1<=sectors<=4096:raise ValueError('1..4096 sectors')
    if origin not in ('USB_CAPTURE','SYNTHETIC_FIXTURE'):raise ValueError('Origin')
    out.mkdir(parents=True,exist_ok=False)
    e=dict(schema=1,transport='USB_CDC',origin=origin,state='STARTED',bytes=0,requested_bytes=sectors*4096,
        board_sha256=m['board_sha256'],build_sha256=m['build_sha256'],captured_at=utc(),error=None,
        snapshots=[],last_exchange=None,hardware_qualified=False)
    ep=out/'capture.json';atomic_json(ep,e);client=None;hasher=hashlib.sha256()
    try:
        client=factory();e['driver']=getattr(client,'driver',None);before=bound_snapshot(client,m);e['snapshots'].append(before)
        w=before['words']
        if (w[128]!=0 or w[129]!=2 or w[130] or w[131] or w[134]!=0xef4018 or w[138]!=4096 or w[149]!=1):
            raise ValueError('Flash inspect state not ready/error-free; download not started')
        with (out/'flash.bin').open('xb') as raw,(out/'chunks.jsonl').open('x') as log:
            for address in range(0,sectors*4096,MAX):
                block=client.request(2,address,MAX)
                raw.write(block);raw.flush();hasher.update(block);e['bytes']+=len(block)
                log.write(json.dumps(dict(address=address,bytes=len(block),sha256=hashlib.sha256(block).hexdigest(),
                    request_id=client.last['request_id'],crc_checked=True))+'\n');log.flush()
                atomic_json(ep,e)
            after=bound_snapshot(client,m,before['uid']);e['snapshots'].append(after)
            if not 0<((after['uptime_ms']-before['uptime_ms'])&0xffffffff)<0x80000000:
                raise ValueError('Clock stalled/reset during dump; identity alone is insufficient')
        e['state']='DOWNLOADED'
    except Exception as x:e['state']='PARTIAL' if e['bytes'] else 'CONNECTION_FAILED';e['error']=type(x).__name__+': '+str(x)
    finally:
        e['sha256']=hasher.hexdigest()
        if client is not None:
            e['last_exchange']=client.last
            try:client.close()
            except Exception as x:e['state']='CLEANUP_FAILED';e['error']=type(x).__name__+': '+str(x)
        e['finished_at']=utc();atomic_json(ep,e)
    return e

def live_checks(samples,live,via_usb):
    w=samples[-1]['words'];u=USB_PROTOCOL['usb'];state=w[160];error=w[161]
    states={v:k for k,v in u['states'].items()};errors={v:k for k,v in u['errors'].items()}
    clock_consistent=w[163]==48000000 and w[176]&((1<<17)|(1<<29))==((1<<17)|(1<<29))
    vbus_consistent=bool(w[162]&2)==bool(w[180]&(1<<15))
    valid=live and state==4 and error==0 and clock_consistent and vbus_consistent and w[162]&7==7
    yield ('USB_CLOCK','FAIL' if error in (1,2,3,4,6) or (w[162]&1 and not clock_consistent) else
        'PASS' if live and w[162]&1 and clock_consistent else 'INCONCLUSIVE',
        f'Firmware clock error={errors[error]}, derived clock={w[163]}Hz, RCC_CR=0x{w[176]:08x}',
        'Check HSE/PLL status via SWD if USB is unavailable. Register-derived frequency is not an instrument measurement.')
    if not vbus_consistent:yield ('USB_VBUS_EVIDENCE','FAIL','VBUS flag contradicts the recorded PD15 digital input.','')
    yield ('USB_ENUMERATION','PASS' if valid and via_usb else 'INCONCLUSIVE',
        f"Firmware state={states[state]}, error={errors[error]}, clock={w[163]}Hz, flags=0x{w[162]:x}.",
        'A valid CDC capture demonstrates this connection only, not suspend/current/signal integrity qualification.')
    yield ('USB_ERROR_HISTORY','INFO' if not (w[171] or w[172] or w[174]) else 'FAIL',
        f'bad frames={w[171]}, partial timeouts={w[172]}, read errors={w[174]}, max service gap={w[175]}ms',
        'Check raw exchanges, cable and Flash state; counters do not identify a failed component alone.')
    if error==5:yield ('USB_STACK','FAIL','USB stack initialization failed; clock and VBUS evidence are retained.','')
    yield ('USB_ELECTRICAL_QUALIFICATION','NOT_TESTED','Pre-enumeration/suspend/current, attach latency and signal integrity require measurements.','')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['capture','dump'])
    ap.add_argument('--port',required=True);ap.add_argument('--manifest',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path);ap.add_argument('--assembly')
    ap.add_argument('--samples',type=int,default=2);ap.add_argument('--sectors',type=int,default=4096)
    a=ap.parse_args();m=validate_manifest(json.loads(a.manifest.read_text()))
    # The installed binary and the expected manifest must travel together.
    for name in ('m3_bench.bin','m3_bench.elf'):
        if hashlib.sha256((a.manifest.parent/name).read_bytes()).hexdigest()!=m['artifacts'][name]:
            raise ValueError('Firmware artifact changed: '+name)
    factory=lambda:serial_client(a.port)
    if a.action=='capture':
        if a.out.with_suffix('.analysis.json').exists():raise FileExistsError('Analysis output already exists')
        e=capture(factory,m,a.assembly,a.out,a.samples)
        binding=json.loads((a.manifest.parent/'binding.json').read_text())
        report=analyze_mailbox(e,binding,m);atomic_json(a.out.with_suffix('.analysis.json'),report)
    else:e=dump(factory,m,a.out,a.sectors)
    print(json.dumps(dict(state=e['state'],error=e['error'],hardware_qualified=False),indent=2))
    return 0 if e['state'] in ('CAPTURED','DOWNLOADED') else 3

if __name__=='__main__':raise SystemExit(main())
