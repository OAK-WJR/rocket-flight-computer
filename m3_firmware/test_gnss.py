"""Fault injections into the production GNSS parser. All bytes are synthetic."""
import ctypes as c
from pathlib import Path
import struct,subprocess,tempfile,unittest

HERE=Path(__file__).resolve().parent
NAMES=('state error history flags kernel_hz brr uart_errors rx_bytes dropped ubx_good nmea_good '
       'bad_checksum bad_length timeouts last_byte_ms mon_ms pvt_ms epoch_ms tx_count tx_errors '
       'pvt_count version_len max_gap_ms').split()
class Result(c.Structure):
    _fields_=[(n,c.c_uint32) for n in NAMES]+[('pvt',c.c_uint8*92),('version',c.c_uint8*100)]
class Parser(c.Structure):
    _fields_=[('r',Result)]+[(n,c.c_uint32) for n in 'started now last_epoch have_epoch epoch_current'.split()]+[
        (n,c.c_uint) for n in 'phase used length kind id cka ckb checka nmea_used'.split()]+[('payload',c.c_uint8*512),('nmea',c.c_uint8*128)]
def ubx(kind,ident,payload=b''):
    body=bytes((kind,ident))+struct.pack('<H',len(payload))+payload;a=b=0
    for v in body:a=(a+v)&255;b=(b+a)&255
    return b'\xb5\x62'+body+bytes((a,b))
def mon(sw=b'ROM SPG 5.10 (7b202e)',proto=b'PROTVER=34.10',model=b'MOD=SAM-M10Q'):
    return ubx(10,4,sw.ljust(30,b'\0')+b'000A0000\0\0'+proto.ljust(30,b'\0')+model.ljust(30,b'\0'))
def pvt(tow=123000,fix=3,flags=1,invalid=0):
    p=bytearray(92);struct.pack_into('<IHBBBBBB',p,0,tow,2026,9,8,13,45,12,7)
    p[20:24]=bytes((fix,flags,0,12))
    struct.pack_into('<iiiiII',p,24,-1220000000,370000000,52000,26000,1400,2200)
    p[78]=invalid;return ubx(1,7,p)
def nmea(body=b'GNGGA,123456.00,,,,,0,00,99.99,,,,,,'):
    checksum=0
    for v in body:checksum^=v
    return b'$'+body+b'*%02X\r\n'%checksum

class GNSSParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();path=Path(cls.tmp.name)/'gnss.dylib'
        subprocess.run(['/usr/bin/clang','-dynamiclib','-O2','-Wall','-Wextra','-Werror',str(HERE/'src/gnss.c'),'-o',str(path)],check=True,capture_output=True)
        cls.lib=c.CDLL(str(path));cls.lib.gnss_init.argtypes=[c.POINTER(Parser),c.c_uint32]
        cls.lib.gnss_feed.argtypes=[c.POINTER(Parser),c.c_uint8,c.c_uint32];cls.lib.gnss_tick.argtypes=[c.POINTER(Parser),c.c_uint32]
        cls.lib.gnss_loss.argtypes=[c.POINTER(Parser),c.c_uint32,c.c_uint32]
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def setUp(self):self.g=Parser();self.lib.gnss_init(c.byref(self.g),0)
    def feed(self,data,now=100):
        for b in data:self.lib.gnss_feed(c.byref(self.g),b,now)
        return self.g.r
    def tick(self,t):self.lib.gnss_tick(c.byref(self.g),t)
    def test_uninitialized_stays_off(self):
        g=Parser();self.lib.gnss_tick(c.byref(g),9999);self.assertEqual(g.r.state,0)
    def test_default_nmea_is_link_evidence_not_a_fix(self):
        r=self.feed(nmea());self.tick(6000)
        self.assertEqual((r.nmea_good,r.pvt_count,r.state,r.flags),(1,0,2,0))
    def test_read_only_poll_packets_match_independent_constants(self):
        p=(c.c_uint8*8)();self.lib.gnss_poll_packet(p,1);self.assertEqual(bytes(p).hex(),'b5620a0400000e34')
        self.lib.gnss_poll_packet(p,0);self.assertEqual(bytes(p).hex(),'b562010700000819')
    def test_known_identity_revision_suffix_and_signed_coordinates(self):
        self.feed(mon());r=self.feed(pvt());self.assertEqual((r.state,r.flags),(5,63))
        self.assertEqual(struct.unpack_from('<ii',bytes(r.pvt),24),(-1220000000,370000000))
        self.assertEqual(bytes(r.version[:30]).rstrip(b'\0'),b'ROM SPG 5.10 (7b202e)')
    def test_unknown_model_retains_bytes_without_claiming_identity(self):
        self.feed(mon(model=b'MOD=MIA-M10Q'));r=self.feed(pvt())
        self.assertEqual(r.state,3);self.assertFalse(r.flags&2);self.assertTrue(r.history&256)
    def test_unknown_firmware_and_protocol_not_silently_accepted(self):
        for kwargs in ({'sw':b'ROM SPG 5.10X'},{'sw':b'ROM SPG 5.11'},{'proto':b'PROTVER=34.11'}):
            self.setUp();self.feed(mon(**kwargs));r=self.feed(pvt());self.assertEqual(r.state,3)
    def test_short_mon_and_wrong_pvt_lengths(self):
        self.feed(ubx(10,4,bytes(41)));r=self.feed(ubx(1,7,bytes(91)))
        self.assertEqual((r.bad_length,r.pvt_count,r.version_len),(2,0,0))
    def test_checksum_failure_preserves_last_raw_and_cannot_refresh(self):
        self.feed(mon());self.feed(pvt(),100);before=bytes(self.g.r.pvt)
        bad=bytearray(pvt(124000));bad[-1]^=1;r=self.feed(bad,4000)
        self.assertEqual((r.state,r.bad_checksum),(6,1));self.assertEqual(bytes(r.pvt),before)
    def test_checksum_both_bytes_and_nmea_are_checked(self):
        for pos in (-1,-2):
            q=bytearray(pvt());q[pos]^=128;self.feed(q)
        q=bytearray(nmea());q[5]^=1;r=self.feed(q)
        self.assertEqual((r.bad_checksum,r.pvt_count,r.nmea_good),(3,0,0))
    def test_repeated_itow_does_not_rejuvenate_a_frozen_receiver(self):
        self.feed(mon());self.feed(pvt(),100);r=self.feed(pvt(),4000)
        self.assertEqual((r.epoch_ms,r.pvt_ms,r.state),(100,4000,6))
    def test_backwards_epoch_and_week_rollover(self):
        self.feed(mon());self.feed(pvt(604799000),100);r=self.feed(pvt(0),1100)
        self.assertEqual(r.state,5);r=self.feed(pvt(604798000),2100);self.assertEqual(r.state,6)
    def test_invalid_epoch_and_invalid_llh(self):
        self.feed(mon());r=self.feed(pvt(604800000));self.assertEqual(r.state,6)
        r=self.feed(pvt(invalid=1));self.assertEqual(r.state,4);self.assertFalse(r.flags&8)
    def test_fix_type_and_fixok_are_both_required(self):
        self.feed(mon())
        for fix,flag in ((0,0),(1,1),(3,0),(4,1),(5,1)):
            r=self.feed(pvt(fix=fix,flags=flag));self.assertEqual(r.state,4)
    def test_coordinate_range_rejected(self):
        self.feed(mon());raw=bytearray(pvt()[6:-2]);struct.pack_into('<i',raw,28,900000001)
        r=self.feed(ubx(1,7,raw));self.assertEqual(r.state,4)
    def test_partial_packet_timeout_and_recovery(self):
        self.feed(pvt()[:25],100);self.tick(501);r=self.feed(mon()+pvt(),502)
        self.assertEqual((r.timeouts,r.state),(1,5))
    def test_oversize_and_noise_recovery(self):
        self.feed(b'\xb5\x62\x01\x07\xff\xff');self.feed(b'$'+b'x'*129)
        r=self.feed(b'\0\xff\xb5'+mon()+pvt());self.assertEqual((r.bad_length,r.state),(2,5))
    def test_uart_loss_invalidates_until_new_epoch(self):
        self.feed(mon());self.feed(pvt());self.lib.gnss_loss(c.byref(self.g),10,8);r=self.feed(pvt(),200)
        self.assertEqual((r.state,r.dropped,r.uart_errors),(6,10,8))
        r=self.feed(pvt(124000),1100);self.assertEqual(r.state,5);self.assertEqual(r.history&24,24)
    def test_millisecond_wrap(self):
        self.lib.gnss_init(c.byref(self.g),0xffffff00);self.feed(mon(),0xffffff10);self.feed(pvt(),0xfffffff0)
        self.tick(1000);self.assertEqual(self.g.r.state,5);self.tick(4000);self.assertEqual(self.g.r.state,6)
    def test_wire_size(self):self.assertEqual(c.sizeof(Result),284)

class GNSSAdapterTests(unittest.TestCase):
    def test_production_adapter_fault_harness(self):
        with tempfile.TemporaryDirectory() as td:
            exe=Path(td)/'gnss_hal'
            r=subprocess.run(['/usr/bin/clang','-std=c11','-Wall','-Wextra','-Werror',
                '-I'+str(HERE/'tests/gnss'),'-I'+str(HERE/'src'),str(HERE/'tests/gnss_hal_harness.c'),
                str(HERE/'src/gnss.c'),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(exe)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('14 scripted',r.stdout)
