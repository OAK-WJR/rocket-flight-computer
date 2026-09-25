"""GNSS C-to-host, complete journal recovery and USB transport faults; synthetic."""
import ctypes as c
import json,struct,subprocess,tempfile,unittest,zlib
from pathlib import Path
from . import test_usb as usb_fixture
from .mailbox import FW,GNSS_PROTOCOL as P,decode,analyze_mailbox,manifest_protocol
from .gnss import measurement,checks
from .storage import recover
from .usb import capture,bound_snapshot,dump
from m3_firmware import test_gnss as cg,test_storage as cs

def manifest(mode='inspect'):return json.loads((FW/('build_gnss_'+mode)/'manifest.json').read_text())
def frame(h=1,mode='inspect'):
    m=manifest(mode);w=usb_fixture.frame(h,mode);w[1]=7;w[7]=P['capabilities']
    w[8:16]=struct.unpack('<8I',bytes.fromhex(m['board_sha256']));w[16:24]=struct.unpack('<8I',bytes.fromhex(m['build_sha256']))
    r=cg.Result();r.state=5;r.flags=63;r.kernel_hz=64000000;r.brr=6667
    r.rx_bytes=300*h;r.ubx_good=2*h;r.pvt_count=h;r.nmea_good=h
    r.last_byte_ms=r.mon_ms=r.pvt_ms=r.epoch_ms=w[5]-50;r.version_len=100
    r.pvt[:]=cg.pvt(h*1000)[6:-2];r.version[:]=cg.mon()[6:-2]
    w[184:255]=struct.unpack('<71I',bytes(r));return usb_fixture.crc(w)

class GNSSHostTests(unittest.TestCase):
    def test_signed_location_and_raw_units(self):
        r=measurement(frame());self.assertEqual((r['latitude_deg'],r['longitude_deg']),(37,-122))
        self.assertEqual((r['height_msl_m'],r['receiver_reported_horizontal_accuracy_m']),(26,1.4))
        self.assertFalse(r['accuracy_measured']);self.assertTrue(r['location_accepted'])
    def test_partial_and_unknown_encoding_rejected(self):
        for pos,val in ((184,8),(185,3),(186,1),(187,64),(190,32),(205,41),(152,3),(183,1)):
            w=frame();w[pos]=val
            with self.assertRaises(ValueError):decode(usb_fixture.crc(w))
    def test_stale_or_future_timestamp_cannot_be_overridden_by_fix_flag(self):
        for time in ((frame()[5]-3001)&0xffffffff,frame()[5]+1):
            w=frame();w[201]=time;r=measurement(usb_fixture.crc(w));self.assertFalse(r['location_accepted']);self.assertIsNone(r['latitude_deg'])
    def test_false_fix_flags_do_not_override_raw_receiver(self):
        for offset,value in ((20,0),(21,0),(78,1)):
            w=frame();p=bytearray(struct.pack('<23I',*w[207:230]));p[offset]=value;w[207:230]=struct.unpack('<23I',p)
            self.assertFalse(measurement(usb_fixture.crc(w))['location_accepted'])
    def test_unknown_model_keeps_raw_but_not_accepted_location(self):
        w=frame();v=bytearray(struct.pack('<25I',*w[230:255]));v[70:100]=b'MOD=MIA-M10Q'.ljust(30,b'\0');w[230:255]=struct.unpack('<25I',v)
        self.assertFalse(measurement(usb_fixture.crc(w))['location_accepted'])
    def test_wrong_uart_clock_evidence_cannot_claim_location(self):
        w=frame();w[188]=32000000
        self.assertFalse(measurement(usb_fixture.crc(w))['location_accepted'])
    def test_error_history_is_visible_and_cannot_clear(self):
        a,b=frame(1),frame(2);a[186]=b[186]=32;a[195]=b[195]=1
        cs,_=checks([dict(words=a),dict(words=b)],True);self.assertIn(('GNSS_STREAM_HISTORY','FAIL'),[x[:2] for x in cs])
        b[186]=0;cs,_=checks([dict(words=a),dict(words=b)],True);self.assertIn(('GNSS_HISTORY_CLEARED','FAIL'),[x[:2] for x in cs])
    def test_usb_v7_capture_retains_gnss_and_full_identity(self):
        s=usb_fixture.Serial([frame(1),frame(2)]);m=manifest();b=json.loads((FW/'build_gnss_inspect/binding.json').read_text())
        with tempfile.TemporaryDirectory() as t:
            e=capture(s.client,m,'SYNTHETIC-GNSS',Path(t)/'s.json',origin='SYNTHETIC_FIXTURE',pause=lambda _:None)
            r=analyze_mailbox(e,b,m)
        statuses={x['id']:x['status'] for x in r['checks']}
        self.assertEqual(statuses['GNSS_LINK'],'PASS');self.assertEqual(statuses['GNSS_POSITION'],'PASS')
        self.assertEqual(statuses['GNSS_RF_ACCURACY'],'NOT_TESTED');self.assertTrue(r['synthetic']);self.assertFalse(r['hardware_qualified'])
    def test_old_v6_frame_is_not_a_v7_capture(self):
        with self.assertRaises(ValueError):bound_snapshot(usb_fixture.Serial().client(),manifest())
    def test_bound_manifest_options_are_not_freely_relabelled(self):
        m=manifest();m['build_options']['board']='usb'
        with self.assertRaises(ValueError):manifest_protocol(m)
    def test_usb_download_interruption_keeps_prefix(self):
        s=usb_fixture.Serial([frame(1),frame(2)]);s.fail_at=3
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'dump';e=dump(s.client,manifest(),out,1,origin='SYNTHETIC_FIXTURE')
            self.assertEqual((e['state'],e['bytes']),('PARTIAL',1024));self.assertEqual((out/'flash.bin').stat().st_size,1024)

class GNSSJournalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();p=Path(cls.tmp.name)/'journal.dylib'
        subprocess.run(['/usr/bin/clang','-dynamiclib','-O2','-Wall','-Wextra','-Werror','-DM3_GNSS',
             str(FW/'src/storage.c'),str(FW/'src/checks.c'),'-o',str(p)],check=True,capture_output=True)
        cls.lib=c.CDLL(str(p));cls.lib.storage_begin.argtypes=[c.POINTER(cs.Device),c.POINTER(cs.IO),c.c_uint,c.POINTER(c.c_uint8)]
        cls.lib.storage_append.argtypes=[c.POINTER(cs.Device),c.POINTER(c.c_uint8),c.c_uint32]
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def begin(self,n=None,mode='record'):
        n=n or cs.Nor();d=cs.Device();w=frame(1,mode);raw=struct.pack('<256I',*w)
        self.lib.storage_begin(c.byref(d),c.byref(n.io),int(mode=='record'),cs.arr(raw[32:96]+raw[104:116]));return n,d
    def append(self,d,h):
        w=frame(h,'record');w[3]=0;self.lib.storage_append(c.byref(d),cs.arr(struct.pack('<256I',*w)),h)
    def test_exact_five_page_samples_three_per_sector_and_roundtrip(self):
        n,d=self.begin()
        for h in range(1,5):self.append(d,h)
        self.assertEqual((d.r.written,d.r.next_sector,d.r.slot,n.programs),(4,1,1,22))
        r=recover(bytes(n.memory[:8192]),'SYNTHETIC_FIXTURE');self.assertFalse(r['issues']);self.assertEqual(len(r['records']),4)
        row=r['records'][0];self.assertEqual(len(row['words']),256);self.assertEqual(row['gnss']['longitude_deg'],-122)
        self.assertEqual(row['usb_status'],'RECORDED_PRE_APPEND');self.assertFalse(row['hardware_qualified'])
    def test_every_cut_in_second_full_snapshot_preserves_first(self):
        n,d=self.begin();self.append(d,1);self.append(d,2);image=bytes(n.memory[:4096]);start=1536
        for cut in range(1281):
            r=recover(image[:start+cut]+b'\xff'*(4096-start-cut))
            self.assertEqual(len(r['records']),2 if cut==1280 else 1,cut)
    def test_snapshot_crc_still_checked_after_page_crc_repaired(self):
        n,d=self.begin();self.append(d,1);image=bytearray(n.memory[:4096]);image[256+32+140]^=1
        struct.pack_into('<I',image,256+252,zlib.crc32(image[256:508]))
        r=recover(image);self.assertFalse(r['records']);self.assertIn('INVALID_RECORD',{x['kind'] for x in r['issues']})
    def test_inspect_never_writes(self):
        n,d=self.begin(mode='inspect');self.append(d,1);self.assertEqual(n.programs,0);self.assertFalse({6,2}&set(n.ops))
    def test_program_fault_is_sticky_and_preceding_sample_survives(self):
        n,d=self.begin();self.append(d,1);n.cut=n.programs+3;self.append(d,2);self.append(d,3)
        self.assertEqual((d.r.written,d.r.dropped),(1,2));self.assertEqual(len(recover(bytes(n.memory[:4096]))['records']),1)
    def test_new_boot_does_not_overwrite_old_sector(self):
        n,d=self.begin();self.append(d,1);saved=bytes(n.memory[:4096]);n.sr[0]=0;n,d2=self.begin(n);self.append(d2,1)
        self.assertEqual(n.memory[:4096],saved);r=recover(bytes(n.memory[:8192]));self.assertEqual((r['sessions'],len(r['records'])),(2,2))
    def test_production_parser_payload_reaches_host_unchanged(self):
        cg.GNSSParserTests.setUpClass()
        try:
            parser=cg.Parser();lib=cg.GNSSParserTests.lib;lib.gnss_init(c.byref(parser),0)
            w=frame(1,'record')
            for byte in cg.mon()+cg.pvt(456000):lib.gnss_feed(c.byref(parser),byte,w[5]-25)
            parser.r.kernel_hz=64000000;parser.r.brr=6667 # scripted HAL evidence
            w[184:255]=struct.unpack('<71I',bytes(parser.r));w[3]=0;usb_fixture.crc(w)
            n,d=self.begin();self.lib.storage_append(c.byref(d),cs.arr(struct.pack('<256I',*w)),1)
            row=recover(bytes(n.memory[:4096]))['records'][0]
            self.assertEqual(row['gnss']['raw_pvt_hex'],bytes(parser.r.pvt).hex());self.assertEqual(row['gnss']['receiver_itow_ms'],456000)
        finally:cg.GNSSParserTests.tearDownClass()
