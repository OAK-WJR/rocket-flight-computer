"""Run the production C driver against a clocked register/fault model.
This models documented transfers, not physical MEMS accuracy or real wiring.
"""
import ctypes as c
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
class Result(c.Structure):
    _fields_=[(k,c.c_uint32) for k in ('status','error','init_error','io_error','started_ms','sampled_ms',
               'finished_ms','config','evidence','history')]+[('raw',c.c_uint32*4),('bus_hz',c.c_uint32)]
NOW=c.CFUNCTYPE(c.c_uint32,c.c_void_p)
DELAY=c.CFUNCTYPE(None,c.c_void_p,c.c_uint32)
INIT=c.CFUNCTYPE(c.c_int,c.c_void_p,c.POINTER(c.c_uint32),c.POINTER(c.c_uint32))
XFER=c.CFUNCTYPE(c.c_int,c.c_void_p,c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.c_size_t,c.POINTER(c.c_uint32))
class IO(c.Structure):
    _fields_=[('ctx',c.c_void_p),('now',NOW),('delay',DELAY),('initialize',INIT),('transfer',XFER)]
class Device(c.Structure):
    _fields_=[('io',c.POINTER(IO)),('init_error',c.c_uint32),('history',c.c_uint32),
              ('bus_hz',c.c_uint32),('init_detail',c.c_uint32),('initialized',c.c_int)]

class Sensor:
    def __init__(self,start=0,fail_at=0,init_error=0):
        self.us=start*1000;self.fail_at=fail_at;self.init_error=init_error;self.count=0
        self.events=[];self.invalid=[];self.stall=False;self.busy=False;self.no_ready=False
        self.overlap=False;self.slow=False;self.fail_raw=False;self.bad_reset=False
        self.skip_write=None;self.raw=struct.pack('>7h',1024,-1024,512,8192,-8192,0,128)
        self.seed()
        def now(_):return (self.us//1000)%2**32
        def delay(_,ms):
            if not self.stall:self.us+=ms*1000
        def init(_,hz,detail):hz[0]=1000000;detail[0]=0;return self.init_error
        def exchange(_,txp,rxp,n,detail):
            detail[0]=0;self.count+=1;tx=bytes(txp[:n]);a=tx[0]&127;read=bool(tx[0]&128)
            self.events.append((self.us,read,a,tx[1:]))
            if self.count==self.fail_at or (self.fail_raw and read and a==0):
                detail[0]=0x03000040;return 1
            if not 2<=n<=15:self.invalid.append(('length',n));return 1
            self.us+=n*8;self.update()
            if read:
                if a==0:
                    if n!=15:self.invalid.append(('burst_length',n))
                    data=self.raw
                    if self.overlap:self.us+=20000;self.update()
                    if self.slow:self.us+=6000
                elif a==0x7e:
                    if n!=2:self.invalid.append(('indirect_burst',n))
                    data=bytes([self.indirect.get(self.address,0)]);self.address+=1
                elif a==0x7f:data=bytes([0 if self.busy else 1])
                else:data=bytes(self.regs[a:a+n-1])
                for i,v in enumerate(data):rxp[i+1]=v
                if a==0x19:self.regs[0x19]=0
            elif a==0x7c:
                if n not in (3,4):self.invalid.append(('indirect_address_burst',n))
                self.address=(tx[1]<<8)|tx[2]
                if n==4 and self.skip_write!=self.address:self.indirect[self.address]=tx[3]
            elif a==0x7f and tx[1]==2:
                self.seed();self.regs[0x19]=0 if self.bad_reset else 0x80
            else:
                for i,v in enumerate(tx[1:]):
                    if self.skip_write!=a+i:self.regs[a+i]=v
                if a==0x10 and tx[1]==15:self.next_ready=self.us+20000
            return 0
        self.io=IO(None,NOW(now),DELAY(delay),INIT(init),XFER(exchange))
    def seed(self):
        self.regs=bytearray(128);self.regs[0x72]=0xe9;self.regs[0x2d]=0x51;self.regs[0x32]=0x13
        self.regs[0x19]=0x80;self.address=0;self.next_ready=None
        self.indirect={0xa267:0x80,0xa03a:0xdb,0xa03b:0xbe,0xa03c:0xff,0xa03d:0xfd,0xa03e:0xa6}
    def update(self):
        if self.next_ready is not None and self.us>=self.next_ready:
            if not self.no_ready and self.regs[0x16]&4:self.regs[0x19]|=4
            self.next_ready+=((self.us-self.next_ready)//20000+1)*20000

class ImuDriverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();lib=Path(cls.tmp.name)/'imu.dylib'
        subprocess.run(['/usr/bin/clang','-dynamiclib','-O2','-Wall','-Wextra','-Werror',
                        str(HERE/'src/imu.c'),'-o',str(lib)],check=True,capture_output=True)
        cls.lib=c.CDLL(str(lib))
        cls.lib.imu_begin.argtypes=[c.POINTER(Device),c.POINTER(IO),c.POINTER(Result)]
        cls.lib.imu_sample.argtypes=[c.POINTER(Device),c.POINTER(Result)]
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def begin(self,s=None):
        s=s or Sensor();d=Device();r=Result();c.memset(c.byref(r),0xa5,c.sizeof(r))
        self.lib.imu_begin(c.byref(d),c.byref(s.io),c.byref(r));return s,d,r
    def sample(self,d):
        r=Result();c.memset(c.byref(r),0xa5,c.sizeof(r));self.lib.imu_sample(c.byref(d),c.byref(r));return r
    def test_init_preserves_reserved_fields_and_unused_int2_pull(self):
        s,d,r=self.begin();self.assertEqual((r.status,r.error,d.initialized),(2,0,1))
        self.assertEqual(c.sizeof(Result),60);self.assertFalse(s.invalid)
        self.assertEqual([s.indirect[x] for x in (0xa03a,0xa03b,0xa03c,0xa03d,0xa03e)],
                         [0xdb&~0x48,0xbe&~0x92,0xff&~0x24,0xfd&~0x49,0xa6])
        self.assertEqual(s.indirect[0xa267],0x82)
        self.assertEqual((s.regs[0x2d],s.regs[0x32]),(0x51,0x13))
        self.assertEqual(r.config,0x820f0a0a)
    def test_raw_burst_is_fresh_and_wire_bytes_are_unchanged(self):
        s,d,_=self.begin();r=self.sample(d)
        self.assertEqual((r.status,r.error),(2,0));self.assertEqual(r.evidence,0xe9070004)
        self.assertEqual(bytes(r.raw),s.raw+b'\0\0');self.assertLessEqual((r.finished_ms-r.started_ms)%2**32,5)
        bursts=[x for x in s.events if x[1:3]==(True,0)]
        self.assertEqual(len(bursts),1);self.assertEqual(len(bursts[0][3]),14)
    def test_every_init_transfer_failure_aborts_and_never_retries_on_sample(self):
        normal,_,_=self.begin()
        for at in range(1,normal.count+1):
            s,d,r=self.begin(Sensor(fail_at=at))
            self.assertEqual((r.status,r.error,r.init_error),(3,3,3),at)
            self.assertEqual(s.count,at,at);sample=self.sample(d)
            self.assertEqual(s.count,at);self.assertEqual(sample.io_error,0x03000040)
            self.assertEqual((sample.status,sample.init_error),(3,3));self.assertEqual(bytes(sample.raw),bytes(16))
    def test_wrong_identity_blocks_all_configuration_writes(self):
        s=Sensor();s.regs[0x72]=0;_,_,r=self.begin(s)
        self.assertEqual((r.status,r.error),(3,4));self.assertEqual(s.count,1)
        self.assertTrue(all(x[1] for x in s.events))
    def test_clock_or_spi_setup_failure_never_touches_sensor(self):
        for e in (1,2):
            s,d,r=self.begin(Sensor(init_error=e));self.assertEqual((r.error,r.init_error),(e,e));self.assertEqual(s.count,0)
    def test_reset_completion_required(self):
        s=Sensor();s.bad_reset=True;s,d,r=self.begin(s)
        self.assertEqual(r.error,5);self.assertFalse(d.initialized)
    def test_indirect_busy_is_bounded(self):
        s=Sensor();s.busy=True;s,d,r=self.begin(s)
        self.assertEqual(r.error,6);self.assertLess(s.us,50000)
        self.assertFalse(any(x[2]==0x7c for x in s.events))
    def test_no_split_ireg_writes_and_minimum_waits(self):
        s,_,_=self.begin()
        for i,event in enumerate(s.events):
            if event[2]==0x7c:
                self.assertIn(len(event[3]),(2,3))
                self.assertGreaterEqual(s.events[i+1][0]-event[0],1000)
    def test_readback_detects_a_write_that_did_not_take(self):
        for address in (0xa267,0xa03a,0xa03b,0xa03c,0xa03d,0x1b,0x1c,0x16,0x18):
            s=Sensor();s.skip_write=address;_,_,r=self.begin(s)
            self.assertEqual((r.status,r.error),(3,7),hex(address))
    def test_runtime_config_drift_cannot_use_stale_scale_or_identity(self):
        for address,value,e in ((0x1b,0x2a,7),(0x1c,0x3a,7),(0x10,0,7),(0x72,0xff,4),(0x18,3,7)):
            s,d,_=self.begin();s.regs[address]=value;r=self.sample(d)
            self.assertEqual((r.status,r.error),(3,e));self.assertEqual(bytes(r.raw),bytes(16))
        s,d,_=self.begin();s.indirect[0xa267]&=~2;r=self.sample(d);self.assertEqual(r.error,7)
    def test_old_ready_flag_is_not_accepted_as_new_data(self):
        s,d,_=self.begin();s.no_ready=True;s.regs[0x19]|=4;started=s.us;r=self.sample(d)
        self.assertEqual((r.status,r.error),(3,8));self.assertLess(s.us-started,120000)
        self.assertFalse(r.evidence&0x10000);self.assertFalse(any(x[1:3]==(True,0) for x in s.events))
    def test_update_during_burst_keeps_bytes_but_rejects_sample(self):
        s,d,_=self.begin();s.overlap=True;r=self.sample(d)
        self.assertEqual((r.status,r.error),(3,9));self.assertTrue(r.evidence&0x10000)
        self.assertEqual(bytes(r.raw)[:14],s.raw)
    def test_slow_burst_and_transport_fault_do_not_pass(self):
        s,d,_=self.begin();s.slow=True;r=self.sample(d);self.assertEqual(r.error,10)
        s,d,_=self.begin();s.fail_raw=True;r=self.sample(d)
        self.assertEqual(r.error,3);self.assertFalse(r.evidence&0x10000)
    def test_fail_then_success_retains_history_but_clears_old_error(self):
        s,d,_=self.begin();s.no_ready=True;a=self.sample(d);s.no_ready=False;b=self.sample(d)
        self.assertEqual((a.error,b.error,b.status),(8,0,2));self.assertEqual(b.history,1<<8)
    def test_success_then_failure_clears_raw_and_valid_bit(self):
        s,d,_=self.begin();a=self.sample(d);s.regs[0x72]=0;b=self.sample(d)
        self.assertEqual(a.status,2);self.assertEqual(b.status,3);self.assertEqual(bytes(b.raw),bytes(16))
        self.assertFalse(b.evidence&0x10000)
    def test_signed_rails_and_zero_are_not_invented_invalid_codes(self):
        for raw in (bytes(14),bytes([255])*14,struct.pack('>7h',-32768,32767,0,-32768,32767,-1,-128)):
            s,d,_=self.begin();s.raw=raw;r=self.sample(d)
            self.assertEqual(r.status,2);self.assertEqual(bytes(r.raw),raw+bytes(2))
    def test_millisecond_wrap_does_not_create_a_timeout(self):
        s,d,r=self.begin(Sensor(start=0xfffffff0));self.assertEqual(r.error,0)
        r=self.sample(d);self.assertEqual(r.error,0)
    def test_nonadvancing_delay_detected_without_unbounded_polling(self):
        s=Sensor();s.stall=True;_,_,r=self.begin(s);self.assertEqual(r.error,11)
    def test_every_sample_transfer_failure_aborts_without_false_valid_sample(self):
        s,d,_=self.begin();before=s.count;self.sample(d);total=s.count-before
        for at in range(1,total+1):
            s,d,_=self.begin();s.fail_at=s.count+at;r=self.sample(d)
            self.assertEqual((r.status,r.error,r.io_error),(3,3,0x03000040),at)
            self.assertEqual(s.count,s.fail_at,at)
    def test_actual_c_result_bytes_decode_through_host_report(self):
        from diagnostics.test_imu import imu_frame,evidence
        from diagnostics.test_mailbox import checksum
        from diagnostics.mailbox import analyze_mailbox
        s,d,_=self.begin(Sensor(start=10000));frames=[]
        for h in (1,2):
            r=self.sample(d);w=imu_frame(h);delta=r.finished_ms+80-w[5]
            for i in (5,53,54,65,76,77):w[i]=(w[i]+delta)%2**32
            w[112:127]=struct.unpack('<15I',bytes(r));frames.append(checksum(w));s.us+=1200000
        report=analyze_mailbox(*evidence(frames))
        self.assertEqual(next(x['status'] for x in report['checks'] if x['id']=='IMU_SAMPLES'),'PASS')
        self.assertEqual(report['measurements'][0]['imu']['nominal_units']['acceleration_g'],[1,-1,.5])

class ImuPlatformTests(unittest.TestCase):
    def test_actual_stm32_adapter_with_scripted_hal(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/'imu-hal'
            compiled=subprocess.run(['/usr/bin/clang','-O1','-Wall','-Wextra','-Werror','-fsanitize=undefined',
                '-fno-sanitize-recover=all','-I'+str(HERE/'tests/imu'),str(HERE/'tests/imu_hal_harness.c'),
                str(HERE/'src/imu.c'),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=5)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('12 scripted STM32 SPI adapter cases passed',run.stdout)

if __name__=='__main__':unittest.main()
