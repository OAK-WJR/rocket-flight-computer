"""Fault recovery uses pages emitted by production C, host checks independent CRC.
All inputs are synthetic; no probe, target reset or flash mutation is exercised.
"""
import copy
import ctypes as c
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
from unittest.mock import Mock
from .mailbox import (FW,STORAGE_PROTOCOL as P,IMU_PROTOCOL,decode,manifest_protocol,read_consistent,
                      capture_mailbox,analyze_mailbox)
from .storage import recover,page_decode,dump,live_checks
from .transport import ReadOnlyAPGuard,PyOCDReader
from .test_imu import imu_frame
from .test_mailbox import SyntheticMailbox
from m3_firmware import test_storage as cs
Nor,Device,arr=cs.Nor,cs.Device,cs.arr

def manifest(mode='inspect'):return json.loads((FW/('build_storage_'+mode)/'manifest.json').read_text())
def crc(w):
    raw=bytearray(struct.pack('<256I',*w));raw[12:16]=bytes(4);w[-1]=zlib.crc32(raw[:-4]);return w
def store_frame(h=1,mode='inspect',**changes):
    m=manifest(mode);w=imu_frame(h)+[0]*128;w[1]=5;w[2]=1024;w[7]=511;w[127]=0
    w[16:24]=struct.unpack('<8I',bytes.fromhex(m['build_sha256']))
    r=dict(MODE=int(mode=='record'),STATUS=2,BUS_HZ=8000000,JEDEC=0xef4018,REGISTERS=0x200,
           SCANNED_SECTORS=4096,MAPPED=int(mode=='inspect'),ERROR_ADDRESS=0xffffffff,BLANK_PAGES=65536)
    if mode=='record':r.update(WRITTEN=h,LAST_COUNTER=h,QUAD_PAGES=3*h+1,LAST_WRITE_MS=w[5])
    r.update(changes)
    for k,v in r.items():w[P['words']['STORE_'+k]]=v
    return crc(w)
class Reader(SyntheticMailbox):
    def enable_storage_mailbox(self):self.extended=True

class StorageHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cs.StorageTests.setUpClass();cls.lib=cs.StorageTests.lib
    @classmethod
    def tearDownClass(cls):cs.StorageTests.tearDownClass()
    def journal(self,count=2):
        n=Nor();d=Device();w=store_frame(1,'record');raw=struct.pack('<256I',*w)
        self.lib.storage_begin(c.byref(d),c.byref(n.io),1,arr(raw[32:96]+raw[104:116]))
        for h in range(1,count+1):
            w=store_frame(h,'record');w[3]=0
            self.lib.storage_append(c.byref(d),arr(struct.pack('<128I',*w[:128])),h)
        return n,d
    def test_v5_crc_and_coexistence_with_imu_voltage_and_camera(self):
        frames=[store_frame(1),store_frame(2)];m=manifest();b=json.loads((FW/'build_storage_inspect/binding.json').read_text())
        with tempfile.TemporaryDirectory() as t:
            s=capture_mailbox(Reader(frames),b,m,'SYNTHETIC',Path(t)/'x.json',origin='SYNTHETIC_FIXTURE',pause=lambda _:None)
        r=analyze_mailbox(s,b,m);status={x['id']:x['status'] for x in r['checks']}
        for key in ('FLASH_STORAGE','IMU_SAMPLES','ADC_MEASUREMENTS','BARO_MEASUREMENTS'):self.assertEqual(status[key],'PASS')
        self.assertEqual(status['FLASH_QUAD_DATA'],'NOT_TESTED');self.assertFalse(r['hardware_qualified'])
    def test_crc_covers_extension_and_reserved_bits(self):
        w=store_frame()
        for pos in range(127,256):
            bad=w.copy();bad[pos]^=0x40000000
            with self.assertRaises(ValueError):decode(bad)
        for pos,val in ((127,1),(128,3),(129,5),(130,17),(131,1),(138,4097),(149,3),(153,1),(254,1)):
            bad=w.copy();bad[pos]=val
            with self.assertRaises(ValueError):decode(crc(bad))
    def test_old_header_does_not_grant_v5_extension(self):
        r=Reader([imu_frame(),imu_frame()]);r.enable_mailbox()
        x=read_consistent(r,attempts=1,pause=lambda _:None,protocol=P)
        self.assertIsNone(x['accepted']);self.assertLessEqual(max(r.words),3);self.assertFalse(hasattr(r,'extended'))
    def test_wrong_manifest_mode_size_and_board_fail(self):
        for edit in ('size','board','mode'):
            m=copy.deepcopy(manifest())
            if edit=='size':m['protocol']['bytes']=2048
            elif edit=='board':m['board_sha256']='00'*32
            else:m['build_options']['storage']='erase'
            with self.assertRaises(ValueError):manifest_protocol(m)
    def test_transport_ranges_never_allow_target_writes(self):
        dp=Mock();g=ReadOnlyAPGuard(dp);g.mailbox_enabled=True
        with self.assertRaises(RuntimeError):g.write_ap(4,0x24000200)
        g.storage_mailbox_enabled=True;g.write_ap(4,0x240003fc)
        for address in (0x24000400,0x90000000):
            with self.assertRaises(RuntimeError):g.write_ap(4,address)
        g.flash_enabled=True;g.write_ap(4,0x90000000);g.write_ap(4,0x90fffffc)
        for address,value in ((4,0x91000000),(4,0x90000001),(0xc,123),(0x10,123),(0,0x03000052)):
            with self.assertRaises(RuntimeError):g.write_ap(address,value)
    def test_v5_transport_extra_sram_requires_committed_header(self):
        r=PyOCDReader('none');r.guard=ReadOnlyAPGuard(Mock());r.guard.mailbox_enabled=True
        for header in ([1295204932,4,512,2],[1295204932,5,1024,3]):
            r.read_mailbox_word=lambda i:header[i]
            with self.assertRaises(RuntimeError):r.enable_storage_mailbox()
            self.assertFalse(r.guard.storage_mailbox_enabled)
        r.read_mailbox_word=lambda i:[1295204932,5,1024,2][i];r.enable_storage_mailbox()
        self.assertTrue(r.guard.storage_mailbox_enabled)
    def test_flash_read_bounds_and_missing_grant(self):
        r=PyOCDReader('none');r.guard=ReadOnlyAPGuard(Mock());r.ap=Mock();r.ap.read32.return_value=0x12345678
        with self.assertRaises(RuntimeError):r.read_flash(0,4)
        r.guard.flash_enabled=True
        for a,n in ((-4,4),(1,4),(0,0),(0,4097),(0x1000000,4),(0,True)):
            with self.assertRaises(ValueError):r.read_flash(a,n)
        self.assertEqual(r.read_flash(0,4),b'\x78\x56\x34\x12')
    def test_production_journal_decodes_raw_signed_and_failure_evidence(self):
        n,d=self.journal(2);r=recover(bytes(n.memory[:4096]),origin='SYNTHETIC_FIXTURE')
        self.assertEqual(len(r['records']),2);self.assertFalse(r['issues']);row=r['records'][0]
        self.assertEqual(row['imu']['nominal_units']['acceleration_g'],[1,-1,.5]);self.assertFalse(row['hardware_qualified'])
        self.assertEqual(row['build_sha256'],manifest('record')['build_sha256'])
    def test_every_cut_within_next_record_preserves_prior_record(self):
        n,d=self.journal(2);good=bytes(n.memory[:4096]);a=1024
        # Every byte boundary, includingCRC bytes and final complete page.
        for cut in range(769):
            image=good[:a+cut]+b'\xff'*(4096-a-cut);r=recover(image)
            self.assertEqual(len(r['records']),2 if cut==768 else 1,cut)
    def test_missing_header_does_not_accept_otherwise_good_samples(self):
        n,_=self.journal();n.memory[:256]=bytes(256)
        r=recover(bytes(n.memory[:4096]));self.assertFalse(r['records']);self.assertTrue(r['issues'])
    def test_wrong_board_in_payload_rejected_even_after_all_crcs_repaired(self):
        n,_=self.journal();image=bytearray(n.memory[:4096]);image[256+32+32]^=1
        struct.pack_into('<I',image,256+252,zlib.crc32(image[256:256+252]))
        r=recover(bytes(image));self.assertEqual(len(r['records']),1);self.assertIn('INVALID_RECORD',{x['kind'] for x in r['issues']})
    def test_unknown_pages_retained_and_bad_size_rejected(self):
        image=bytearray(b'\xff')*4096;image[1]=0;r=recover(image)
        self.assertFalse(r['records']);self.assertTrue(r['issues'])
        for data in (b'x',bytes(4097)):
            with self.assertRaises(ValueError):recover(data)
    def test_sector_rollover_and_reboot_session_are_distinct(self):
        n,d=self.journal(6);raw=struct.pack('<256I',*store_frame(1,'record'));d2=Device()
        self.lib.storage_begin(c.byref(d2),c.byref(n.io),1,arr(raw[32:96]+raw[104:116]))
        w=store_frame(1,'record');w[3]=0;self.lib.storage_append(c.byref(d2),arr(struct.pack('<128I',*w[:128])),1)
        r=recover(bytes(n.memory[:12288]));self.assertEqual((len(r['records']),r['sessions']),(7,2));self.assertFalse(r['issues'])
    def test_recorder_failure_and_lost_count_are_not_pass(self):
        for changes in (dict(ERROR=12,STATUS=3,HISTORY=4096),dict(DROPPED=1),dict(REGISTERS=0x4200),dict(MAPPED=1)):
            samples=[dict(words=store_frame(1,'record')),dict(words=store_frame(2,'record',**changes))]
            rows=live_checks(samples,manifest('record'),True)
            self.assertTrue(any(c[1]=='FAIL' for c in rows),changes)
    def test_absent_probe_download_records_failure_without_fake_data(self):
        reader=Mock();reader.open.side_effect=RuntimeError('no probe')
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out';r=dump(reader,manifest(),out)
            self.assertEqual(r['state'],'CONNECTION_FAILED');self.assertEqual(r['bytes'],0)
            self.assertFalse((out/'flash.bin').exists());reader.read_flash.assert_not_called()
    def test_download_grant_requires_bound_inspect_state_and_uid(self):
        w=store_frame();m=manifest()
        for change in (None,'record','uid','sha','mapping','status'):
            r=PyOCDReader('none');r.guard=ReadOnlyAPGuard(Mock());r.guard.mailbox_enabled=True
            f=w.copy()
            if change=='record':f[128]=1
            elif change=='uid':f[26]^=1
            elif change=='sha':f[16]^=1
            elif change=='mapping':f[149]=0
            elif change=='status':f[129]=3
            f=crc(f);r.read_mailbox_word=lambda i:f[i]
            r.read=lambda name:w[{'UID0':26,'UID1':27,'UID2':28}[name]]
            if change:
                with self.assertRaises(RuntimeError):r.enable_flash_dump(m)
                self.assertFalse(r.guard.flash_enabled)
            else:
                self.assertEqual(r.enable_flash_dump(m)['uid'],w[26:29]);self.assertTrue(r.guard.flash_enabled)
    def test_download_keeps_partial_image_and_never_fills_fault_with_zero(self):
        base=decode(store_frame(USED_SECTORS=2));reader=Mock()
        reader.open.return_value={'synthetic':True};reader.enable_flash_dump.return_value=base
        reader.read_flash.side_effect=[bytes([0x5a])*4096,OSError('scripted bus failure')]
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out';r=dump(reader,manifest(),out)
            self.assertEqual((r['state'],r['bytes']),('PARTIAL',4096));self.assertIn('bus failure',r['error'])
            self.assertEqual((out/'flash.bin').read_bytes(),bytes([0x5a])*4096)
    def test_download_stops_if_chip_identity_changes(self):
        a=decode(store_frame(USED_SECTORS=1));b=decode(store_frame(USED_SECTORS=1));b['words'][136]^=1
        reader=Mock();reader.open.return_value={};reader.enable_flash_dump.side_effect=[a,b]
        with tempfile.TemporaryDirectory() as t:
            r=dump(reader,manifest(),Path(t)/'out')
            self.assertNotEqual(r['state'],'CAPTURED');reader.read_flash.assert_not_called()
    def test_download_hash_and_complete_size(self):
        import hashlib
        reader=Mock();reader.open.return_value={};reader.enable_flash_dump.return_value=decode(store_frame(USED_SECTORS=1))
        reader.read_flash.return_value=bytes(4096)
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out';r=dump(reader,manifest(),out)
            self.assertEqual(r['state'],'CAPTURED');self.assertEqual(r['sha256'],hashlib.sha256(bytes(4096)).hexdigest())
            with self.assertRaises(FileExistsError):dump(reader,manifest(),out)
    def test_history_cannot_be_silently_cleared(self):
        rows=[dict(words=store_frame(1,'record',DROPPED=1)),dict(words=store_frame(2,'record'))]
        self.assertIn(('FLASH_HISTORY','FAIL'),[r[:2] for r in live_checks(rows,manifest('record'),True)])

if __name__=='__main__':unittest.main()
