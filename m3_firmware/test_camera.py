"""Execute the production camera transaction against scripted byte/time faults.
Synthetic data only; no UART/board is connected by these tests.
"""
import ctypes as c
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE=Path(__file__).resolve().parent

class Result(c.Structure):
    _fields_=[(n,c.c_uint32) for n in ('status','error','mode','start_ms','query_ms','finished_ms',
      'power_readback','oe_readback','kernel_hz','brr','isr','tx_count','rx_count','discarded','crc_errors',
      'protocol_version','features','valid_length','raw_length','error_flags')]+[('raw',c.c_uint32*8),('packet',c.c_uint32*2)]

NOW=c.CFUNCTYPE(c.c_uint32,c.c_void_p)
INIT=c.CFUNCTYPE(c.c_int,c.c_void_p,c.POINTER(Result))
LEVEL=c.CFUNCTYPE(c.c_int,c.c_void_p,c.c_int)
TX=c.CFUNCTYPE(c.c_int,c.c_void_p,c.c_uint8,c.POINTER(Result))
DONE=c.CFUNCTYPE(c.c_int,c.c_void_p,c.POINTER(Result))
RX=c.CFUNCTYPE(c.c_int,c.c_void_p,c.POINTER(c.c_uint8),c.POINTER(Result))
SNAP=c.CFUNCTYPE(None,c.c_void_p,c.POINTER(Result))
class IO(c.Structure):
    _fields_=[('ctx',c.c_void_p),('now',NOW),('init',INIT),('power',LEVEL),('oe',LEVEL),
              ('tx',TX),('tx_done',DONE),('rx',RX),('snapshot',SNAP)]

def reply(version=1,features=0x1234):
    from diagnostics.camera import crc8
    b=bytes([0xcc,version,features&255,features>>8]);return b+bytes([crc8(b)])

class Script:
    def __init__(self,data=None,pre=b'',fail='',start=100,version=1):
        self.time=start;self.data=list(reply(version) if data is None else data);self.pre=list(pre)
        self.fail=fail;self.events=[];self.txbytes=[];self.power=0;self.oe=0;self.done=False
        def now(_):
            if self.fail!='tick_stall':self.time=(self.time+1)&0xffffffff
            return self.time
        def init(_,r):
            self.events.append(('init',self.time))
            r.contents.kernel_hz=64000000;r.contents.brr=556
            return 1 if fail=='init' else 2 if fail=='clock' else 0
        def power(_,high):
            self.power=high;self.events.append(('power',high,self.time))
            if fail=='power_low' and high:self.power=0
            return self.power
        def oe(_,high):
            self.oe=high;self.events.append(('oe',high,self.time))
            if fail=='oe_low' and high:self.oe=0
            if fail=='oe_stuck':self.oe=1
            return self.oe
        def tx(_,b,r):
            if fail=='tx':return 0
            self.txbytes.append(b);return 1
        def done(_,r):
            if fail=='tc':return 0
            self.done=True;return 1
        def rx(_,b,r):
            if fail=='rx' and self.done:r.contents.error_flags=8;return -1
            source=self.data if self.done else self.pre
            if fail=='pre_flood' and not self.done:b[0]=0x55;return 1
            if source:b[0]=source.pop(0);return 1
            return 0
        def snap(_,r):
            r.contents.power_readback=self.power;r.contents.oe_readback=self.oe
        self.io=IO(None,NOW(now),INIT(init),LEVEL(power),LEVEL(oe),TX(tx),DONE(done),RX(rx),SNAP(snap))

class CameraTransactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();lib=Path(cls.tmp.name)/'camera.dylib'
        # Apple's signed Python process cannot load the UBSan runtime; the
        # separate native platform harness carries sanitizer instrumentation.
        subprocess.run(['/usr/bin/clang','-dynamiclib','-O2','-Wall','-Wextra','-Werror',
          str(HERE/'src/camera.c'),'-o',str(lib)],check=True,capture_output=True)
        cls.lib=c.CDLL(str(lib));cls.lib.camera_query.argtypes=[c.POINTER(IO),c.c_int,c.POINTER(Result)]
        cls.lib.camera_crc8.argtypes=[c.c_void_p,c.c_size_t];cls.lib.camera_crc8.restype=c.c_uint8
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def run_script(self,**kwargs):
        enabled=kwargs.pop('enabled',True);s=Script(**kwargs);r=Result()
        c.memset(c.byref(r),0xa5,c.sizeof(r)) # stale success/result must be cleared
        self.lib.camera_query(c.byref(s.io),enabled,c.byref(r));return s,r
    def test_crc_standard_and_wire_request_vectors(self):
        self.assertEqual(self.lib.camera_crc8(b'123456789',9),0xbc)
        self.assertEqual(self.lib.camera_crc8(bytes.fromhex('cc00'),2),0x60)
    def test_disabled_mode_does_not_open_uart_or_turn_on_camera(self):
        s,r=self.run_script(enabled=False)
        self.assertEqual((r.status,r.error,r.tx_count,r.rx_count,r.valid_length),(0,0,0,0,0))
        self.assertFalse(s.txbytes);self.assertNotIn('init',[e[0] for e in s.events])
        self.assertEqual((s.power,s.oe),(0,0))
    def test_info_query_only_and_idle_shutdown_order(self):
        s,r=self.run_script()
        self.assertEqual(s.txbytes,[0xcc,0,0x60]);self.assertEqual((r.status,r.error,r.valid_length),(2,0,5))
        self.assertEqual((r.protocol_version,r.features),(1,0x1234))
        power=next(e for e in s.events if e[:2]==('power',1))
        enable=next(e for e in s.events if e[:2]==('oe',1))
        self.assertGreaterEqual((enable[2]-power[2])%2**32,3000)
        self.assertEqual(s.events[-1][:2],('oe',0));self.assertEqual((s.power,s.oe),(1,0))
        self.assertEqual(bytes(r.packet)[:5],reply())
    def test_preexisting_valid_reply_is_discarded(self):
        s,r=self.run_script(pre=reply(),data=b'')
        self.assertEqual((r.status,r.error,r.valid_length),(3,4,0));self.assertEqual(r.discarded,5)
        self.assertEqual(bytes(r.packet),bytes(8));self.assertEqual(s.oe,0)
    def test_fresh_reply_after_stale_data_keeps_history(self):
        _,r=self.run_script(pre=reply(features=0x7777))
        self.assertEqual((r.status,r.features,r.discarded),(2,0x1234,5))
    def test_no_response_and_partial_frame_timeout_clear_old_success(self):
        for data in (b'',reply()[:4]):
            s,r=self.run_script(data=data)
            self.assertEqual((r.status,r.error,r.valid_length),(3,4,0))
            self.assertLessEqual((r.finished_ms-r.query_ms)%2**32,1100);self.assertEqual(s.oe,0)
    def test_bad_crc_then_valid_response_preserves_rejection(self):
        bad=bytearray(reply());bad[-1]^=1
        _,r=self.run_script(data=bytes(bad)+reply())
        self.assertEqual((r.status,r.crc_errors,r.rx_count),(2,1,10))
    def test_every_single_bit_corruption_cannot_pass(self):
        good=reply()
        for bit in range(40):
            data=bytearray(good);data[bit//8]^=1<<(bit%8)
            _,r=self.run_script(data=data)
            self.assertEqual(r.status,3,(bit,bytes(data)))
            self.assertEqual(r.valid_length,0)
    def test_noise_with_embedded_header_resynchronizes(self):
        _,r=self.run_script(data=b'\x55\xcc\x11'+reply(features=0xcc))
        self.assertEqual((r.status,r.features),(2,0xcc));self.assertGreater(r.discarded,0)
    def test_unknown_protocol_retains_raw_frame_but_is_not_success(self):
        _,r=self.run_script(version=99)
        self.assertEqual((r.status,r.error,r.protocol_version,r.valid_length),(3,7,99,5))
    def test_rx_electrical_error_is_not_crc_pass(self):
        s,r=self.run_script(fail='rx')
        self.assertEqual((r.status,r.error,r.error_flags),(3,5,8));self.assertEqual(s.oe,0)
    def test_tx_and_tc_stalls_are_bounded(self):
        for fail in ('tx','tc'):
            s,r=self.run_script(fail=fail)
            self.assertEqual((r.status,r.error),(3,3));self.assertEqual(s.oe,0)
            self.assertLessEqual((r.finished_ms-r.query_ms)%2**32,101)
    def test_failed_initialization_never_energizes_camera(self):
        for fail,error in [('init',1),('clock',2),('oe_stuck',9),('power_low',9),('oe_low',9)]:
            s,r=self.run_script(fail=fail)
            self.assertEqual((r.status,r.error),(3,error));self.assertFalse(s.txbytes)
            if fail in ('init','clock','oe_stuck'):self.assertNotIn(('power',1),[e[:2] for e in s.events])
    def test_flood_has_byte_limit_and_raw_capture_does_not_overflow(self):
        _,r=self.run_script(data=b'\x55'*300)
        self.assertEqual((r.status,r.error,r.rx_count,r.raw_length),(3,8,256,32))
        self.assertEqual(bytes(r.raw),b'\x55'*32)
        _,r=self.run_script(fail='pre_flood')
        self.assertEqual((r.error,r.tx_count),(8,0))
        self.assertTrue(0<r.discarded<=256) # the 100ms drain deadline can win first
    def test_tick_wrap_still_uses_elapsed_time(self):
        _,r=self.run_script(start=0xfffffff0)
        self.assertEqual(r.status,2);self.assertLess(r.finished_ms,0xfffffff0)
    def test_stopped_tick_cannot_spin_forever_in_query_engine(self):
        s,r=self.run_script(fail='tick_stall')
        self.assertEqual((r.status,r.error),(3,10));self.assertEqual(s.oe,0)
    def test_real_stm32_adapter_against_register_and_gpio_stubs(self):
        exe=Path(self.tmp.name)/'camera_hal_harness'
        subprocess.run(['/usr/bin/clang','-O1','-Wall','-Wextra','-Werror','-fsanitize=undefined',
          '-I'+str(HERE/'tests/camera'),'-I'+str(HERE/'src'),
          str(HERE/'tests/camera_hal_harness.c'),str(HERE/'src/camera.c'),'-o',str(exe)],
          check=True,capture_output=True,text=True)
        result=subprocess.run([str(exe)],check=True,capture_output=True,text=True,timeout=5)
        self.assertIn('12 scripted STM32 UART cases passed',result.stdout);self.assertEqual(result.stderr,'')

if __name__=='__main__':unittest.main()
