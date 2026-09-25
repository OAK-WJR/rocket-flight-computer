"""Append-only M3 diagnostic log recovery and bounded, read-only SWD download.
No flash installation, reset, halt, erase, formatting or target-memory writes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib
from .transport import PyOCDReader,atomic_json,utc

SIZE=0x1000000
SECTOR=4096
PAGE=256
MAGIC=0x474c334d

def page_decode(data,address):
    if len(data)!=PAGE:raise ValueError('Truncated page')
    if data==b'\xff'*PAGE:return None
    magic,version,kind,at,session,counter,chunk,n=struct.unpack('<8I',data[:32])
    if magic!=MAGIC or version!=1 or at!=address or n>220:raise ValueError('Foreign/torn page header')
    if zlib.crc32(data[:252])!=struct.unpack('<I',data[252:])[0]:raise ValueError('Page CRC mismatch')
    if not 0<=session<=address//SECTOR<4096:raise ValueError('Invalid session/sector')
    if kind==1:
        if address%SECTOR or chunk or counter or n!=84:raise ValueError('Invalid sector header')
    elif kind in (2,3):
        slot=address%SECTOR//PAGE
        pages,last=(3,72) if kind==2 else (5,144)
        if slot==0 or chunk!=(slot-1)%pages or n!=(last if chunk==pages-1 else 220) or not counter:
            raise ValueError('Invalid sample chunk')
    else:raise ValueError('Unknown page kind')
    if data[32+n:252]!=b'\xff'*(220-n):raise ValueError('Noncanonical page padding')
    return dict(kind=kind,address=address,session=session,counter=counter,chunk=chunk,payload=data[32:32+n])

def prefix_decode(payload,header):
    from .mailbox import STORAGE_PROTOCOL,USB_PROTOCOL,GNSS_PROTOCOL,STATUS_PROTOCOL,W,prom_ok
    from .acquisition import sample_measurements,measurement_checks
    from .imu import imu_checks
    from .camera import camera_measurement
    if len(payload) not in (512,1024):raise ValueError('Partial diagnostic prefix/snapshot')
    full=len(payload)==1024
    words=list(struct.unpack('<'+str(len(payload)//4)+'I',payload))
    protocol={7:GNSS_PROTOCOL,8:STATUS_PROTOCOL}.get(words[1]) if full else {5:STORAGE_PROTOCOL,6:USB_PROTOCOL}.get(words[1])
    if protocol is None or words[:4]!=[1295204932,protocol['version'],1024,0] or words[7]!=protocol['capabilities'] or words[127]:
        raise ValueError('Wrong diagnostic prefix schema')
    if payload[32:96]!=header[:64] or payload[104:116]!=header[64:76]:
        raise ValueError('Sample/sector board, build or MCU identity mismatch')
    # Reuse v5 field validation by adding an explicitly synthetic EMPTY extension.
    # This only validates the encoding; it does not invent live Flash status.
    from .mailbox import decode
    extended=words.copy() if full else words+[0]*128
    if not full:extended[-1]=zlib.crc32(struct.pack('<255I',*extended[:-1]))
    decode(extended)
    row=sample_measurements(words,W)
    checks,imu=imu_checks([dict(words=words,state=words[4])],protocol,True)
    row.update(counter=words[52],words=words,imu=imu[0],imu_checks=checks,
               acquisition_checks=measurement_checks([dict(words=words,state=words[4])],W,True),
               camera=camera_measurement(words,protocol),baro_prom_ok=prom_ok(words),
               usb_status='RECORDED_PRE_APPEND' if full else 'NOT_RECORDED')
    if full:
        from .gnss import measurement
        row['gnss']=measurement(words)
        if protocol==STATUS_PROTOCOL:
            from .power_status import measurement as power_measurement
            row['power_status']=power_measurement(words)
    return row

def recover(data,origin='FILE_UNVERIFIED'):
    if origin not in ('FILE_UNVERIFIED','SWD_CAPTURE','USB_CAPTURE','SYNTHETIC_FIXTURE'):raise ValueError('Unknown origin')
    if len(data)>SIZE or len(data)%SECTOR:raise ValueError('Image must contain whole 4KiB sectors, at most16MiB')
    records=[];issues=[];sessions={};last={};blank=0
    for base in range(0,len(data),SECTOR):
        pages=[]
        for i in range(16):
            a=base+i*PAGE
            try:
                p=page_decode(data[a:a+PAGE],a)
                if p is None:blank+=1
            except ValueError as e:
                p=None;issues.append(dict(address=a,kind='INVALID_PAGE',reason=str(e)))
            pages.append(p)
        h=pages[0]
        if h is None:
            if any(pages[1:]):issues.append(dict(address=base,kind='ORPHAN_SECTOR'))
            continue
        identity=h['payload'];session=h['session']
        if session in sessions and sessions[session]!=identity:
            issues.append(dict(address=base,kind='SESSION_IDENTITY_CHANGED'));continue
        sessions[session]=identity
        if session*SECTOR==base and h['kind']!=1:raise ValueError('Invalid sector type')
        # Each boot uses one record size and starts a new sector. Infer the
        # sector's layout from its first CRC-valid data page; mixed chunks
        # invalidate that record, while earlier complete records survive.
        kind=next((p['kind'] for p in pages[1:] if p and p['kind'] in (2,3)),2)
        width=3 if kind==2 else 5
        for slot in range(15//width):
            a=base+(1+slot*width)*PAGE;chunks=pages[1+slot*width:1+(slot+1)*width]
            physical=data[a:a+width*PAGE]
            if physical==b'\xff'*(width*PAGE):continue
            if any(p is None for p in chunks):
                issues.append(dict(address=a,kind='INCOMPLETE_RECORD'));continue
            counters={p['counter'] for p in chunks}
            if (len(counters)!=1 or any(p['kind']!=kind or p['session']!=session for p in chunks) or
                [p['chunk'] for p in chunks]!=list(range(width))):
                issues.append(dict(address=a,kind='MIXED_RECORD'));continue
            counter=chunks[0]['counter']
            if counter<=last.get(session,0):
                issues.append(dict(address=a,kind='NONMONOTONIC_COUNTER'));continue
            try:
                row=prefix_decode(b''.join(p['payload'] for p in chunks),identity)
                if row['counter']!=counter:raise ValueError('Page/payload counter mismatch')
            except ValueError as e:
                issues.append(dict(address=a,kind='INVALID_RECORD',reason=str(e)));continue
            prior=last.get(session)
            if prior is not None and counter!=prior+1:
                issues.append(dict(address=a,kind='MISSING_COUNTERS',after=prior,before=counter))
            last[session]=counter
            row.update(address=a,session=session,board_sha256=identity[:32].hex(),build_sha256=identity[32:64].hex(),
                       mcu_uid=identity[64:76].hex(),flash_uid=identity[76:].hex(),origin=origin,
                       hardware_qualified=False)
            records.append(row)
    return dict(schema=1,format='M3LG-v1',origin=origin,image_bytes=len(data),image_sha256=hashlib.sha256(data).hexdigest(),
                records=records,issues=issues,blank_pages=blank,sessions=len(sessions),
                hardware_qualified=False,scope='Complete CRC-valid diagnostic records only; not physical power-loss qualification')

def live_checks(samples,manifest,live):
    rows=[d['words'] for d in samples];w=rows[-1];mode=int(manifest['build_options']['storage']=='record')
    good=all(r[128]==mode and r[129]==2 and r[130]==0 and r[131]==0 and r[132]==0 and
             r[133]==8000000 and r[134]==0xef4018 and r[138]==4096 and r[149]==1-mode
             for r in rows)
    good=good and (not mode or all(r[135]&0x200 and not r[135]&0x4c01f for r in rows))
    result=[('FLASH_STORAGE','INCONCLUSIVE' if not live else 'PASS' if good else 'FAIL',
             f'mode={mode}, status/error={w[129:132]}, scanned={w[138]}, invalid_pages={w[141]}, dropped={w[146]}')]
    stable=all((x[131]&y[131])==x[131] and y[146]>=x[146] and y[144]>=x[144] for x,y in zip(rows,rows[1:]))
    result.append(('FLASH_HISTORY','INFO' if stable else 'FAIL','Error bits and counters must not clear within one capture'))
    if mode:
        advanced=all(0<y[144]-x[144] and y[145]>x[145] and y[150]>x[150] for x,y in zip(rows,rows[1:]))
        result.append(('FLASH_APPEND','PASS' if live and good and advanced and not any(r[146] for r in rows) else
                       'FAIL' if live and any(r[146] for r in rows) else 'INCONCLUSIVE',
                       f'verified samples={w[144]}, last counter={w[145]}, dropped={w[146]}'))
    result.append(('FLASH_QUAD_DATA','PASS' if live and good and mode and all(r[150]>0 for r in rows) else 'NOT_TESTED',
                   f'{w[150]} newly programmed pages compared using03h and6Bh; blank reads alone do not prove four lanes'))
    result.append(('FLASH_OLD_DATA','INCONCLUSIVE' if w[141] else 'INFO',
                   f'{w[141]} nonblank invalid/unknown pages retained; download for record-level recovery'))
    return result

def dump(reader,manifest,out):
    from .mailbox import manifest_protocol,STORAGE_PROTOCOL
    out=Path(out)
    if out.exists():raise FileExistsError(str(out))
    if manifest_protocol(manifest)!=STORAGE_PROTOCOL or manifest['build_options']['storage']!='inspect':
        raise ValueError('Dump is read-only inspect mode only')
    out.mkdir(parents=True);e=dict(schema=1,origin='SWD_CAPTURE',state='STARTED',bytes=0,
                                  started_at=utc(),board_sha256=manifest['board_sha256'],error=None)
    atomic_json(out/'capture.json',e)
    try:
        e['driver']=reader.open();reader.enable_mailbox()
        before=reader.enable_flash_dump(manifest);e['before']=before
        size=before['words'][139]*SECTOR
        digest=hashlib.sha256()
        with (out/'flash.bin').open('xb') as f:
            for offset in range(0,size,SECTOR):
                check=reader.enable_flash_dump(manifest)
                if check['uid']!=before['uid'] or check['words'][136:140]!=before['words'][136:140]:
                    raise RuntimeError('Device/scan identity changed during download')
                chunk=reader.read_flash(offset,SECTOR)
                if not isinstance(chunk,bytes) or len(chunk)!=SECTOR:raise RuntimeError('Short/nonbyte flash response')
                f.write(chunk);f.flush();digest.update(chunk);e['bytes']+=len(chunk)
                atomic_json(out/'capture.json',e)
        after=reader.enable_flash_dump(manifest);e['after']=after
        if (after['uid']!=before['uid'] or after['words'][136:140]!=before['words'][136:140] or
            ((after['uptime_ms']-before['uptime_ms'])&0xffffffff)>=0x80000000):raise RuntimeError('Reset/identity change during download')
        e.update(state='CAPTURED',sha256=digest.hexdigest())
    except Exception as ex:e.update(state='PARTIAL' if e['bytes'] else 'CONNECTION_FAILED',error=type(ex).__name__+': '+str(ex))
    finally:
        try:reader.close()
        except Exception as ex:e.update(state='CLEANUP_FAILED',error=str(ex))
        if isinstance(reader,PyOCDReader) and reader.guard is not None:
            e['ap_config_trace']=reader.guard.operations
            e['ap_config_count']=reader.guard.operation_count
            e['trace_truncated']=reader.guard.operation_count>len(reader.guard.operations)
        e['finished_at']=utc();atomic_json(out/'capture.json',e)
    return e

def write_recovery(image,out):
    out=Path(out)
    if out.exists():raise FileExistsError(str(out))
    result=recover(Path(image).read_bytes());out.mkdir(parents=True)
    with (out/'records.jsonl').open('x') as f:
        for row in result.pop('records'):f.write(json.dumps(row,allow_nan=False)+'\n')
    atomic_json(out/'recovery.json',result);return result

def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='cmd',required=True)
    r=s.add_parser('recover');r.add_argument('image');r.add_argument('--out',required=True)
    d=s.add_parser('dump');d.add_argument('--probe-id',required=True);d.add_argument('--manifest',required=True);d.add_argument('--out',required=True)
    args=p.parse_args()
    if args.cmd=='recover':result=write_recovery(args.image,args.out);code=2 if result['issues'] else 0
    else:
        result=dump(PyOCDReader(args.probe_id),json.loads(Path(args.manifest).read_text()),args.out)
        code=0 if result['state']=='CAPTURED' else 3
    print(json.dumps(result,indent=2));return code

if __name__=='__main__':sys.exit(main())
