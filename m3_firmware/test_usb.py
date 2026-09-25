"""Production C stream protocol and scripted HAL lifecycle, not real USB PHY tests."""
import ctypes as c
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib
HERE=Path(__file__).resolve().parent
READ=c.CFUNCTYPE(c.c_uint,c.c_void_p,c.POINTER(c.c_uint8),c.c_uint32,c.c_uint32)
class Wire(c.Structure):
    _fields_=[('ctx',c.c_void_p),('snapshot',READ),('flash',READ),('rx',c.c_uint8*24),('tx',c.c_uint8*1052),
        *[(n,c.c_uint32) for n in ('rx_used','tx_size','tx_sent','last_byte_ms','requests','bad_requests','partial_timeouts','last_request','read_errors')]]

def request(op=1,seq=0x12345678,address=0,n=1024,version=1):
    raw=struct.pack('<4sHHIII',b'M3RQ',version,op,seq,address,n)
    return raw+struct.pack('<I',zlib.crc32(raw))

class USBWireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();p=Path(cls.temp.name)/'wire.dylib'
        subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-shared','-fPIC',
            str(HERE/'src/usb_wire.c'),str(HERE/'src/checks.c'),'-o',str(p)],check=True,capture_output=True)
        cls.lib=c.CDLL(str(p));cls.lib.usb_wire_init.argtypes=[c.POINTER(Wire),c.c_void_p,READ,READ]
        cls.lib.usb_wire_feed.argtypes=[c.POINTER(Wire),c.c_uint8,c.c_uint32]
        cls.lib.usb_wire_tick.argtypes=[c.POINTER(Wire),c.c_uint32]
        cls.lib.usb_wire_pending.argtypes=[c.POINTER(Wire),c.POINTER(c.c_uint32)]
        cls.lib.usb_wire_pending.restype=c.POINTER(c.c_uint8)
        cls.lib.usb_wire_sent.argtypes=[c.POINTER(Wire),c.c_uint32]
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def setUp(self):
        self.w=Wire();self.calls=[];self.error=0
        def read(_,p,a,n):
            self.calls.append((a,n))
            for i in range(n):p[i]=(a+i)%256
            return self.error
        self.callback=READ(read);self.lib.usb_wire_init(c.byref(self.w),None,self.callback,self.callback)
    def feed(self,data,now=20):
        for b in data:self.assertEqual(self.lib.usb_wire_feed(c.byref(self.w),b,now),1)
    def response(self):
        n=c.c_uint32();ptr=self.lib.usb_wire_pending(c.byref(self.w),c.byref(n));b=c.string_at(ptr,n.value)
        self.assertEqual(zlib.crc32(b[:-4]),struct.unpack('<I',b[-4:])[0]);return b
    def test_every_packet_split_and_one_callback(self):
        for split in range(25):
            self.setUp();q=request();self.feed(q[:split]);self.feed(q[split:]);b=self.response()
            self.assertEqual(b[:24],struct.pack('<4sHHIIII',b'M3RS',1,0,0x12345678,0,1024,1))
            self.assertEqual(b[24:-4],bytes(range(256))*4);self.assertEqual(self.calls,[(0,1024)])
    def test_corrupt_every_request_byte_has_no_read_side_effect(self):
        for bit in range(24*8):
            self.setUp();q=bytearray(request());q[bit//8]^=1<<(bit%8);self.feed(q)
            self.assertEqual(self.calls,[]);self.assertEqual(self.w.tx_size,0)
    def test_noise_resynchronizes_on_next_complete_valid_request(self):
        self.feed(b'noise'+bytes(71)+request(op=2,address=100,n=7));b=self.response()
        self.assertEqual(b[24:-4],bytes(range(100,107)));self.assertGreater(self.w.bad_requests,0)
    def test_bounded_flash_last_byte_and_overflow_rejected(self):
        for a,n,good in ((0xffffff,1,True),(0xffff00,256,True),(0x1000000,1,False),
            (0xffff00,257,False),(0xffffffff,1024,False),(0,0,False),(0,1025,False)):
            self.setUp();self.feed(request(op=2,address=a,n=n));b=self.response()
            self.assertEqual(bool(self.calls),good);self.assertEqual(b[6],0 if good else 1)
    def test_unknown_operations_and_versions_cannot_access_memory(self):
        for op,ver,a,n in ((0,1,0,1024),(3,1,0,1024),(65535,1,0,1024),(1,2,0,1024),(1,1,1,1024),(1,1,0,1023)):
            self.setUp();self.feed(request(op=op,version=ver,address=a,n=n));self.assertEqual(self.response()[6],1);self.assertFalse(self.calls)
    def test_failed_read_never_returns_stale_payload(self):
        for error,status in ((1,1),(2,2),(3,3),(99,3)):
            self.setUp();self.error=error;self.feed(request());b=self.response()
            self.assertEqual((len(b),b[6],self.w.read_errors),(28,status,int(status==3)))
    def test_partial_transmit_and_backpressure(self):
        self.feed(request());original=self.response();self.assertFalse(self.lib.usb_wire_feed(c.byref(self.w),1,20))
        self.assertFalse(self.lib.usb_wire_sent(c.byref(self.w),2000));result=bytearray()
        while self.w.tx_size:
            n=c.c_uint32();ptr=self.lib.usb_wire_pending(c.byref(self.w),c.byref(n));take=min(17,n.value)
            result.extend(c.string_at(ptr,take));self.assertTrue(self.lib.usb_wire_sent(c.byref(self.w),take))
        self.assertEqual(result,original);self.feed(request(seq=9));self.assertEqual(self.w.last_request,9)
    def test_timeout_wrap_and_disconnect_clear_pending_only(self):
        self.feed(request()[:10],0xfffffff0);self.lib.usb_wire_tick(c.byref(self.w),0x200)
        self.assertEqual((self.w.rx_used,self.w.partial_timeouts),(0,1));self.feed(request())
        self.lib.usb_wire_reset(c.byref(self.w));self.assertEqual((self.w.tx_size,self.w.rx_used,self.w.requests),(0,0,1))

class USBAdapterTests(unittest.TestCase):
    def test_real_tinyusb_descriptor_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            exe=Path(t)/'desc';cmd=['cc','-std=c11','-Wall','-Wextra','-Werror','-DM3_USB',
                '-I'+str(HERE/'vendor/tinyusb/src'),'-I'+str(HERE/'src'),'-I'+str(HERE/'tests/usb'),
                str(HERE/'tests/usb_descriptor_harness.c'),'-o',str(exe)]
            r=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=5);self.assertEqual(r.returncode,0,r.stderr)
    def test_hal_clock_vbus_lifecycle_and_dtr_faults(self):
        with tempfile.TemporaryDirectory() as t:
            exe=Path(t)/'usb';cmd=['cc','-std=c11','-Wall','-Wextra','-Werror','-DM3_USB',
                '-I'+str(HERE/'tests/usb'),'-I'+str(HERE/'src'),str(HERE/'tests/usb_hal_harness.c'),
                str(HERE/'src/usb_wire.c'),str(HERE/'src/checks.c'),'-o',str(exe)]
            r=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=5);self.assertEqual(r.returncode,0,r.stderr)
    def test_storage_usb_aborts_mapping_and_preserves_faults(self):
        for mode in (0,1):
            with tempfile.TemporaryDirectory() as t:
                exe=Path(t)/'qspi';cmd=['cc','-std=c11','-Wall','-Wextra','-Werror','-DM3_USB','-DM3_STORAGE',
                    '-DM3_STORAGE_RECORD='+str(mode),'-I'+str(HERE/'tests/storage'),
                    str(HERE/'tests/storage_hal_harness.c'),str(HERE/'src/storage.c'),str(HERE/'src/checks.c'),'-o',str(exe)]
                r=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
                r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=5);self.assertEqual(r.returncode,0,r.stderr)

if __name__=='__main__':unittest.main()
