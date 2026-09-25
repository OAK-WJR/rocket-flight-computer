"""Production portable C journal vs NOR/page-wrap, torn-write and bus-fault model.
Scripted memory faults do not qualify real flash or physical brownouts.
"""
import ctypes as c
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib
HERE=Path(__file__).resolve().parent
N=0x1000000
class Result(c.Structure):
    _fields_=[(k,c.c_uint32) for k in ('mode','status','error','history','io_error','bus_hz','jedec','registers',
        'uid0','uid1','scanned','used','headers','invalid','next_sector','session','written','last','dropped',
        'address','write_ms','mapped','quad','blank','slot','res0','res1','res2')]
NOW=c.CFUNCTYPE(c.c_uint32,c.c_void_p);DELAY=c.CFUNCTYPE(None,c.c_void_p,c.c_uint32)
INIT=c.CFUNCTYPE(c.c_int,c.c_void_p,c.POINTER(c.c_uint32),c.POINTER(c.c_uint32))
XFER=c.CFUNCTYPE(c.c_int,c.c_void_p,c.c_uint8,c.c_int32,c.c_uint,c.c_int,c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.c_size_t,c.POINTER(c.c_uint32))
MAP=c.CFUNCTYPE(c.c_int,c.c_void_p,c.POINTER(c.c_uint32))
PROGRESS=c.CFUNCTYPE(None,c.c_void_p,c.POINTER(Result))
class IO(c.Structure):
    _fields_=[('ctx',c.c_void_p),('ticks',NOW),('delay',DELAY),('initialize',INIT),('command',XFER),('map',MAP),('progress',PROGRESS)]
class Device(c.Structure):
    _fields_=[('io',IO),('r',Result),('initialized',c.c_uint32),('opened',c.c_uint32),
             ('identity',c.c_uint8*84),('sector',c.c_uint8*4096)]
def arr(data):return (c.c_uint8*len(data)).from_buffer_copy(data)

class Nor:
    def __init__(self):
        self.memory=bytearray(b'\xff')*N;self.ms=0;self.stall=False;self.sr=[0,2,0]
        self.ops=[];self.events=[];self.programs=0;self.cut=None;self.cut_bytes=128
        self.ignore_wren=False;self.ignore_program=False;self.quad_fault=False;self.io_fail=None
        self.init_fail=False;self.map_fail=False;self.map_count=0;self.busy_until=0;self.forever=False
        self.id=b'\xef\x40\x18';self.sfdp=b'SFDP\x05\x01\x00\xff';self.uid=bytes(range(8))
        def init(_,hz,detail):hz[0]=8000000;detail[0]=0;return int(self.init_fail)
        def delay(_,ms):
            if not self.stall:self.ms+=ms
        def command(_,op,a,dummy,quad,tx,rx,n,detail):
            self.ops.append(op);detail[0]=0
            if self.io_fail==op:detail[0]=0x02000004;return 1
            data=b''
            if op in (5,0x35,0x15):
                if self.ms>=self.busy_until and not self.forever:self.sr[0]&=~1
                data=bytes([self.sr[{5:0,0x35:1,0x15:2}[op]]])
            elif op==0x9f:data=self.id
            elif op==0x5a:data=self.sfdp
            elif op==0x4b:data=self.uid
            elif op in (3,0x6b):
                if a<0 or a+n>N:raise AssertionError('Out of bounds read')
                data=bytes(self.memory[a:a+n])
                if op==0x6b:
                    self.events.append(('quad',a,n,dummy,quad))
                    if self.quad_fault:data=bytes([data[0]^1])+data[1:]
            elif op==6:
                if not self.ignore_wren:self.sr[0]|=2
            elif op==2:
                self.programs+=1;self.events.append(('program',a,n,dummy,quad))
                if not self.sr[0]&2:raise AssertionError('No WEL')
                data_tx=bytes(tx[:n])
                if not self.ignore_program:
                    count=self.cut_bytes if self.programs==self.cut else n
                    for i,v in enumerate(data_tx[:count]):self.memory[(a&~255)|((a+i)&255)]&=v
                self.sr[0]=(self.sr[0]&~2)|1;self.busy_until=self.ms+3
                if self.programs==self.cut:detail[0]=0x40000000;return 1
            else:raise AssertionError('Unexpected mutation/opcode: '+hex(op))
            if rx:
                if len(data)!=n:raise AssertionError('Bad response count')
                c.memmove(rx,data,n)
            return 0
        def mapping(_,detail):self.map_count+=1;detail[0]=0;return int(self.map_fail)
        self.io=IO(None,NOW(lambda _:self.ms%2**32),DELAY(delay),INIT(init),XFER(command),MAP(mapping),PROGRESS(lambda *_:None))

class StorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();path=Path(cls.tmp.name)/'storage.dylib'
        subprocess.run(['/usr/bin/clang','-dynamiclib','-O2','-Wall','-Wextra','-Werror',str(HERE/'src/storage.c'),
                        str(HERE/'src/checks.c'),'-o',str(path)],check=True,capture_output=True)
        cls.lib=c.CDLL(str(path));cls.lib.storage_begin.argtypes=[c.POINTER(Device),c.POINTER(IO),c.c_uint,c.POINTER(c.c_uint8)]
        cls.lib.storage_append.argtypes=[c.POINTER(Device),c.POINTER(c.c_uint8),c.c_uint32]
        cls.lib.storage_program_page.argtypes=[c.POINTER(Device),c.c_uint32,c.POINTER(c.c_uint8)]
        cls.lib.storage_read.argtypes=[c.POINTER(Device),c.c_uint32,c.POINTER(c.c_uint8),c.c_size_t]
        cls.lib.storage_page_valid.argtypes=[c.POINTER(c.c_uint8),c.c_uint32]
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def begin(self,nor=None,mode=1):
        nor=nor or Nor();d=Device();identity=arr(bytes(range(76)))
        self.lib.storage_begin(c.byref(d),c.byref(nor.io),mode,identity)
        return nor,d
    def append(self,d,counter=1):self.lib.storage_append(c.byref(d),arr(bytes(range(256))*2),counter)
    def test_full_scan_no_mutation_then_three_page_sample(self):
        n,d=self.begin();self.assertEqual((d.r.scanned,d.r.blank,d.r.status),(4096,65536,2));self.assertNotIn(6,n.ops)
        self.append(d);self.assertEqual((d.r.written,d.r.last,d.r.quad),(1,1,4))
        self.assertEqual([x[:3] for x in n.events if x[0]=='program'],[('program',a,256) for a in (0,256,512,768)])
        self.assertEqual({x[3:] for x in n.events if x[0]=='quad'},{(8,1)})
        self.assertEqual(set(n.ops),{3,5,0x35,0x15,0x9f,0x5a,0x4b,6,2,0x6b})
    def test_inspect_maps_and_never_programs_even_if_append_called(self):
        n,d=self.begin(mode=0);self.append(d)
        self.assertEqual((d.r.mapped,n.map_count,n.programs),(1,1,0));self.assertNotIn(6,n.ops)
        self.assertEqual(self.lib.storage_program_page(c.byref(d),0,arr(bytes(256))),0);self.assertEqual(d.r.error,14)
    def test_reboot_abandons_partial_sector(self):
        n,d=self.begin();self.append(d);first=bytes(n.memory[:4096]);n.sr[0]=0
        _,d2=self.begin(n);self.assertEqual((d2.r.next_sector,d2.r.session),(1,1))
        self.append(d2);self.assertEqual(n.memory[:4096],first);self.assertEqual(d2.r.written,1)
    def test_sector_rollover_exactly_five_samples(self):
        n,d=self.begin()
        for i in range(1,7):self.append(d,i)
        self.assertEqual((d.r.written,d.r.next_sector,d.r.slot),(6,1,1));self.assertEqual(n.programs,20)
        self.assertEqual(struct.unpack_from('<I',n.memory,4096+16)[0],0)
    def test_bounds_and_page_crossing_are_rejected_before_wren(self):
        for a in (1,255,N,N-1,0xffffffff):
            n,d=self.begin();self.lib.storage_program_page(c.byref(d),a,arr(bytes(256)))
            self.assertEqual(d.r.error,8);self.assertNotIn(6,n.ops)
    def test_existing_programmed_or_foreign_bytes_are_not_overwritten(self):
        n=Nor();n.memory[12345]=0;n,d=self.begin(n);prior=bytes(n.memory[:16384])
        self.append(d);self.assertEqual(n.memory[:16384],prior);self.assertEqual(d.r.session,4);self.assertEqual(d.r.invalid,1)
    def test_not_blank_after_scan_is_sticky_and_does_not_retry(self):
        n,d=self.begin();n.memory[1]=0;self.append(d);self.append(d,2)
        self.assertEqual((d.r.error,d.r.dropped,n.programs),(9,2,0));self.assertEqual(d.r.history,1<<9)
    def test_protection_bits_are_not_automatically_cleared(self):
        for which,mask in ((0,4),(0,0x1c),(1,0x40),(2,4)):
            n=Nor();n.sr[which]|=mask;n,d=self.begin(n);self.append(d)
            self.assertEqual(d.r.error,6);self.assertFalse({6,2,0x01,0x31,0x11}&set(n.ops))
    def test_lost_qe_is_configuration_error_without_status_write(self):
        n=Nor();n.sr[1]=0;n,d=self.begin(n);self.assertEqual(d.r.error,7);self.assertNotIn(6,n.ops)
    def test_wrong_identity_or_sfdp_stops_before_any_write(self):
        for field,value,error in (('id',b'\xff'*3,3),('sfdp',bytes(8),4)):
            n=Nor();setattr(n,field,value);n,d=self.begin(n);self.append(d)
            self.assertEqual(d.r.error,error);self.assertNotIn(6,n.ops)
    def test_wren_ignored_or_program_ignored_does_not_count(self):
        for field,error in (('ignore_wren',10),('ignore_program',12)):
            n,d=self.begin();setattr(n,field,True);self.append(d)
            self.assertEqual((d.r.error,d.r.written),(error,0))
    def test_busy_and_suspended_boot_rejected(self):
        for suspend in (True,False):
            n=Nor()
            if suspend:n.sr[1]|=128
            else:n.forever=True;n.sr[0]|=1
            n,d=self.begin(n);self.assertEqual(d.r.error,5);self.assertNotIn(6,n.ops)
    def test_poll_timeout_bounded_even_with_stopped_tick(self):
        n,d=self.begin();n.forever=True;n.stall=True;self.append(d)
        self.assertEqual((d.r.error,n.programs),(11,1));self.assertLess(len(n.ops),4200)
    def test_quad_lane_disagreement_stops_logging(self):
        n,d=self.begin();n.quad_fault=True;self.append(d)
        self.assertEqual((d.r.error,d.r.written,d.r.quad),(12,0,0))
    def test_transport_error_preserves_detail_and_no_retry(self):
        n,d=self.begin();n.io_fail=2;self.append(d);calls=len(n.ops);self.append(d,2)
        self.assertEqual((d.r.error,d.r.io_error,len(n.ops)),(2,0x02000004,calls))
    def test_full_array_retains_all_bytes_and_no_wren(self):
        n=Nor();n.memory[-1]=0;n,d=self.begin(n);self.append(d)
        self.assertEqual((d.r.error,d.r.used,d.r.written),(13,4096,0));self.assertNotIn(6,n.ops)
    def test_counter_repetition_does_not_overwrite(self):
        n,d=self.begin();self.append(d);calls=n.programs;self.append(d)
        self.assertEqual((d.r.error,n.programs),(15,calls))
    def test_partial_program_at_every_chunk_and_header_is_detected(self):
        from diagnostics.storage import page_decode
        for cut in range(1,5):
            for size in (0,1,128,255,256):
                n,d=self.begin();n.cut=cut;n.cut_bytes=size;self.append(d)
                self.assertEqual((d.r.error,d.r.written),(2,0))
                if size not in (0,256):
                    with self.assertRaises(ValueError):page_decode(bytes(n.memory[(cut-1)*256:cut*256]),(cut-1)*256)
                # Reboot never reuses a sector containing even one programmed bit.
                n.cut=None;n.sr[0]=0;n.busy_until=0;_,d2=self.begin(n)
                self.assertEqual(d2.r.next_sector,0 if cut==1 and size==0 else 1)
    def test_every_single_bit_change_fails_page_crc(self):
        n,d=self.begin();self.append(d)
        p=bytes(n.memory[256:512]);self.assertEqual(self.lib.storage_page_valid(arr(p),256),1)
        for bit in range(2048):
            x=bytearray(p);x[bit//8]^=1<<(bit%8)
            self.assertEqual(self.lib.storage_page_valid(arr(x),256),0)
    def test_page_relocation_not_accepted_even_with_recomputed_crc(self):
        n,d=self.begin();self.append(d);p=bytes(n.memory[256:512])
        self.assertEqual(self.lib.storage_page_valid(arr(p),4096+256),0)
    def test_counter_and_millisecond_rollover_do_not_hang(self):
        n,d=self.begin();n.ms=0xfffffffe;self.append(d,0xffffffff)
        self.assertEqual((d.r.error,d.r.written),(0,1));self.append(d,0);self.assertEqual(d.r.error,15)

class StorageAdapterTests(unittest.TestCase):
    def test_both_compiled_hal_modes_and_command_allowlist(self):
        with tempfile.TemporaryDirectory() as temp:
            for mode in (0,1):
                exe=Path(temp)/('hal'+str(mode))
                run=subprocess.run(['/usr/bin/clang','-Wall','-Wextra','-Werror','-fsanitize=undefined',
                   '-fno-sanitize-recover=all','-DM3_STORAGE',f'-DM3_STORAGE_RECORD={mode}',
                   '-I'+str(HERE/'tests/storage'),str(HERE/'tests/storage_hal_harness.c'),
                   str(HERE/'src/storage.c'),str(HERE/'src/checks.c'),'-o',str(exe)],capture_output=True,text=True)
                self.assertEqual(run.returncode,0,run.stderr)
                run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=10)
                self.assertEqual(run.returncode,0,run.stderr)
                self.assertIn('PASS (scripted)',run.stdout)

if __name__=='__main__':unittest.main()
