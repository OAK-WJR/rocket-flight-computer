"""Scripted CDC transport faults and actual C wire/journal interoperability."""
import copy
import ctypes as c
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
from unittest.mock import Mock
from .usb import Client,DeviceError,request_bytes,capture,dump,bound_snapshot
from .mailbox import FW,USB_PROTOCOL as P,decode,manifest_protocol,analyze_mailbox,read_consistent
from .test_storage import store_frame,crc,Reader
from .test_imu import imu_frame
from .storage import recover
from .transport import PyOCDReader
from m3_firmware import test_usb as cw,test_storage as cs
Wire,READ=cw.Wire,cw.READ
Nor,Device,arr=cs.Nor,cs.Device,cs.arr

def manifest(mode='inspect'):return json.loads((FW/('build_usb_'+mode)/'manifest.json').read_text())
def frame(h=1,mode='inspect'):
    m=manifest(mode);w=store_frame(h,mode);w[1]=6;w[7]=1023
    w[8:16]=struct.unpack('<8I',bytes.fromhex(m['board_sha256']))
    w[16:24]=struct.unpack('<8I',bytes.fromhex(m['build_sha256']))
    w[160:168]=[4,0,15,48000000,1,0,1,0];w[176]=(1<<17)|(1<<29);w[180]=1<<15;return crc(w)
def raw(w):return struct.pack('<256I',*w)

class Serial:
    """Independent wire implementation, irregular read/write boundaries."""
    def __init__(self,frames=None):
        self.rx=bytearray();self.tx=bytearray();self.closed=False;self.frames=list(frames or [frame(1),frame(2)])
        self.next_frame=0;self.now=0;self.requests=[];self.mutate=None;self.fail_at=None;self.status=0
    def clock(self):self.now+=.001;return self.now
    def write(self,data):
        n=min(7,len(data));self.tx.extend(data[:n])
        if len(self.tx)==24:
            header=bytes(self.tx[:20]);self.tx.clear()
            magic,version,op,seq,a,size=struct.unpack('<4sHHIII',header);assert(magic,version)==(b'M3RQ',1)
            self.requests.append((op,a,size))
            if op==1:
                payload=raw(self.frames[min(self.next_frame,len(self.frames)-1)]);self.next_frame+=1
            else:payload=bytes((i+a)%256 for i in range(size))
            if self.fail_at==len(self.requests):self.rx.extend(b'M3RS');return n
            if self.status:payload=b''
            reply=struct.pack('<4sHHIIII',b'M3RS',1,self.status,seq,a,len(payload),op)+payload
            reply+=struct.pack('<I',zlib.crc32(reply))
            if self.mutate:reply=self.mutate(reply)
            self.rx.extend(reply)
        return n
    def read(self,n):
        n=min(n,13,len(self.rx));data=bytes(self.rx[:n]);del self.rx[:n];return data
    def close(self):self.closed=True
    def client(self):return Client(self,timeout=.5,clock=self.clock)

class USBHostTests(unittest.TestCase):
    def test_host_request_canonical_and_bounds(self):
        q=request_bytes(2,9,100,10);self.assertEqual(len(q),24);self.assertEqual(struct.unpack('<I',q[-4:])[0],zlib.crc32(q[:20]))
        for op,a,n in ((1,1,1024),(1,0,7),(2,0,0),(2,0,1025),(2,0xffffffff,7),(2,0x1000000,1),(3,0,1)):
            with self.assertRaises(ValueError):request_bytes(op,1,a,n)
    def test_usb_crc_board_identity_and_packet_splits(self):
        s=Serial();d=bound_snapshot(s.client(),manifest());self.assertEqual(d['words'],frame());self.assertEqual(len(s.requests),1)
    def test_corrupt_crc_and_wrong_header_never_accepted(self):
        for pos in (0,4,8,12,16,20,30,1040):
            s=Serial();s.mutate=lambda b,p=pos:b[:p]+bytes([b[p]^1])+b[p+1:]
            client=s.client()
            with self.assertRaises(ValueError):client.request(1,0,1024)
            self.assertIsNotNone(client.last['error']);self.assertEqual(len(s.requests),1)
    def test_stalls_short_reply_busy_and_short_write_are_bounded(self):
        s=Serial();s.fail_at=1;client=s.client()
        with self.assertRaises(TimeoutError):client.request(1,0,1024)
        self.assertEqual(client.last['rx_hex'],b'M3RS'.hex())
        for status in (1,2,3):
            s=Serial();s.status=status
            with self.assertRaises(DeviceError):s.client().request(1,0,1024)
        s=Serial();s.write=lambda _:0
        with self.assertRaises(IOError):s.client().request(1,0,1024)
    def test_old_build_or_forged_board_fields_rejected_even_with_crc(self):
        for pos in (8,16,25):
            w=frame();w[pos]^=1;s=Serial([crc(w)])
            with self.assertRaises(ValueError):bound_snapshot(s.client(),manifest())
        with self.assertRaises(ValueError):bound_snapshot(Serial([store_frame()]).client(),manifest())
    def test_capture_analyzes_raw_sensors_and_usb_without_independent_identity_claim(self):
        s=Serial();m=manifest();b=json.loads((FW/'build_usb_inspect/binding.json').read_text())
        with tempfile.TemporaryDirectory() as t:
            e=capture(s.client,m,'SCRIPTED',Path(t)/'capture.json',pause=lambda _:None,origin='SYNTHETIC_FIXTURE')
            report=analyze_mailbox(e,b,m)
        status={x['id']:x['status'] for x in report['checks']}
        for name in ('USB_ENUMERATION','IMU_SAMPLES','ADC_MEASUREMENTS','BARO_MEASUREMENTS','FLASH_STORAGE'):
            self.assertEqual(status[name],'PASS')
        self.assertEqual(status['USB_ELECTRICAL_QUALIFICATION'],'NOT_TESTED')
        self.assertTrue(report['synthetic']);self.assertFalse(report['hardware_qualified']);self.assertTrue(s.closed)
        self.assertIn('not independent',next(x['evidence'] for x in report['checks'] if x['id']=='IDENTITY_SOURCE'))
    def test_no_connection_or_partial_capture_retains_truthful_evidence(self):
        def absent():raise IOError('No serial port')
        with tempfile.TemporaryDirectory() as t:
            e=capture(absent,manifest(),'NONE',Path(t)/'absent.json',pause=lambda _:None)
            self.assertEqual((e['state'],e['samples'],e['identity']),('CONNECTION_FAILED',[],{}))
            s=Serial();s.fail_at=2;e=capture(s.client,manifest(),'SCRIPTED',Path(t)/'partial.json',pause=lambda _:None)
            self.assertEqual(e['state'],'PARTIAL');self.assertEqual(len(e['samples']),1)
            self.assertEqual(e['exchanges'][-1]['rx_hex'],b'M3RS'.hex());self.assertTrue(s.closed)
    def test_identity_change_and_stale_capture_cannot_pass_liveness(self):
        w=frame(2);w[26]^=1;s=Serial([frame(1),crc(w)]);m=manifest()
        with tempfile.TemporaryDirectory() as t:
            e=capture(s.client,m,'SCRIPTED',Path(t)/'changed.json',pause=lambda _:None)
            self.assertEqual(e['state'],'PARTIAL')
            s=Serial([frame(1),frame(1)]);e=capture(s.client,m,'SCRIPTED',Path(t)/'stale.json',pause=lambda _:None)
            b=json.loads((FW/'build_usb_inspect/binding.json').read_text());r=analyze_mailbox(e,b,m)
            status={x['id']:x['status'] for x in r['checks']};self.assertEqual(status['FIRMWARE_LIVENESS'],'INCONCLUSIVE')
            self.assertEqual(status['USB_ENUMERATION'],'INCONCLUSIVE')
    def test_download_exact_sectors_and_crc_verified_chunks(self):
        s=Serial()
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'download';e=dump(s.client,manifest(),out,1)
            self.assertEqual((e['state'],e['bytes']),('DOWNLOADED',4096))
            self.assertEqual((out/'flash.bin').read_bytes(),bytes(range(256))*16)
            self.assertEqual(len((out/'chunks.jsonl').read_text().splitlines()),4);self.assertTrue(s.closed)
    def test_download_interrupt_keeps_prefix_no_padded_or_retried_data(self):
        s=Serial();s.fail_at=3
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'download';e=dump(s.client,manifest(),out,1)
            self.assertEqual((e['state'],e['bytes']),('PARTIAL',1024));self.assertEqual(len(s.requests),3)
            self.assertEqual((out/'flash.bin').stat().st_size,1024)
            self.assertEqual(e['last_exchange']['rx_hex'],b'M3RS'.hex())
    def test_dump_refuses_record_or_failed_storage_or_changed_identity(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):dump(Serial().client,manifest('record'),Path(t)/'r',1)
            w=frame();w[130]=2;s=Serial([crc(w)])
            e=dump(s.client,manifest(),Path(t)/'fault',1);self.assertEqual(e['bytes'],0)
            self.assertFalse((Path(t)/'fault/flash.bin').exists());self.assertEqual(len(s.requests),1)
            w=frame(2);w[26]^=1;s=Serial([frame(),crc(w)]);e=dump(s.client,manifest(),Path(t)/'swap',1)
            self.assertEqual(e['state'],'PARTIAL');self.assertEqual(e['bytes'],4096)
    def test_v6_reserved_padding_crc_and_manifest_are_strict(self):
        for pos,val in ((153,1),(159,1),(183,1),(254,1),(160,7),(161,7),(162,16)):
            w=frame();w[pos]=val
            with self.assertRaises(ValueError):decode(crc(w))
        for key in ('board','storage','imu_samples'):
            m=copy.deepcopy(manifest());m['build_options'][key]='invalid'
            with self.assertRaises(ValueError):manifest_protocol(m)
    def test_wrong_clock_value_remains_decodable_failure_evidence(self):
        from .usb import live_checks
        w=frame();w[160:164]=[6,4,0,47000000];d=decode(crc(w))
        result={x[0]:x[1] for x in live_checks([d],True,False)}
        self.assertEqual(result['USB_CLOCK'],'FAIL');self.assertEqual(result['USB_ENUMERATION'],'INCONCLUSIVE')
    def test_ready_flags_cannot_override_contradictory_register_evidence(self):
        from .usb import live_checks
        for pos,key in ((176,'USB_CLOCK'),(180,'USB_VBUS_EVIDENCE')):
            w=frame();w[pos]=0;d=decode(crc(w));r={x[0]:x[1] for x in live_checks([d],True,True)}
            self.assertEqual(r[key],'FAIL');self.assertEqual(r['USB_ENUMERATION'],'INCONCLUSIVE')
    def test_swd_extension_requires_committed_known_header(self):
        r=Mock();r.guard.mailbox_enabled=True
        for header,good in (([1295204932,6,1024,2],True),([1295204932,7,1024,2],True),([1295204932,8,1024,2],False),
                           ([1295204932,6,1024,1],False),([1295204932,6,2048,2],False)):
            r.read_mailbox_word.side_effect=header
            if good:PyOCDReader.enable_storage_mailbox(r);self.assertTrue(r.guard.storage_mailbox_enabled)
            else:
                with self.assertRaises(RuntimeError):PyOCDReader.enable_storage_mailbox(r)
                self.assertFalse(r.guard.storage_mailbox_enabled)
        old=Reader([imu_frame(),imu_frame()]);old.enable_mailbox()
        self.assertIsNone(read_consistent(old,1,lambda _:None,P)['accepted']);self.assertFalse(hasattr(old,'extended'))

class USBInteropTests(unittest.TestCase):
    def test_host_client_against_production_c_stream_protocol(self):
        cw.USBWireTests.setUpClass()
        try:
            lib=cw.USBWireTests.lib;w=Wire();payload=raw(frame())
            def read(_,out,a,n):
                c.memmove(out,payload,n);return 0
            callback=READ(read);lib.usb_wire_init(c.byref(w),None,callback,callback)
            class CSerial:
                def write(self,data):
                    for b in data:assert lib.usb_wire_feed(c.byref(w),b,100)
                    return len(data)
                def read(self,n):
                    count=c.c_uint32();ptr=lib.usb_wire_pending(c.byref(w),c.byref(count));n=min(n,count.value,11)
                    b=c.string_at(ptr,n);assert lib.usb_wire_sent(c.byref(w),n);return b
            self.assertEqual(bound_snapshot(Client(CSerial()),manifest())['words'],frame())
        finally:cw.USBWireTests.tearDownClass()
    def test_v6_journal_recovers_raw_prefix_without_inventing_usb_stats(self):
        cs.StorageTests.setUpClass()
        try:
            n=Nor();d=Device();w=frame(1,'record');b=raw(w)
            cs.StorageTests.lib.storage_begin(c.byref(d),c.byref(n.io),1,arr(b[32:96]+b[104:116]))
            w[3]=0;w[127]=0;cs.StorageTests.lib.storage_append(c.byref(d),arr(struct.pack('<128I',*w[:128])),w[52])
            report=recover(bytes(n.memory[:4096]),origin='SYNTHETIC_FIXTURE')
            self.assertEqual(len(report['records']),1);self.assertEqual(report['issues'],[])
            self.assertEqual(report['records'][0]['usb_status'],'NOT_RECORDED')
            self.assertFalse(report['hardware_qualified'])
        finally:cs.StorageTests.tearDownClass()

if __name__=='__main__':unittest.main()
