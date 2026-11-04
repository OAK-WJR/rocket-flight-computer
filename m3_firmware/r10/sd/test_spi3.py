"""Actual query/wire/SPI3 C against scripted registers and a byte peer.

No STM32 image or physical peripheral is executed. The model checks software
register boundaries and sequencing, not electrical waveforms or silicon.
"""
import ctypes as c
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import test_query as protocol
import test_wire as wiretest

P=c.POINTER
READ=c.CFUNCTYPE(c.c_uint32,c.c_void_p,c.c_uint32,c.c_uint)
WRITE=c.CFUNCTYPE(None,c.c_void_p,c.c_uint32,c.c_uint32,c.c_uint)
DELAY=c.CFUNCTYPE(None,c.c_void_p,c.c_uint)
RCC=0x58024400;GC=0x58020800;GD=0x58020c00;SPI=0x40003c00
CR=RCC;CFGR=RCC+0x10;D1CFGR=RCC+0x18;D1CCIPR=RCC+0x4c;D2CCIP1R=RCC+0x50
RESET=RCC+0x90;GATES=RCC+0xe0;ENABLE=RCC+0xe8

class MMIO(c.Structure):
    _fields_=[('context',c.c_void_p),('read',READ),('write',WRITE),('delay_cycles',DELAY)]

class Port(c.Structure):
    _fields_=[('io',MMIO)]+[(n,c.c_uint32) for n in (
      'poll_limit owned ready selected stage error detail last_sr accepted received cleanup_error cleanup_detail'
    ).split()]+[('observed_clock',c.c_uint32*5),('observed_config',c.c_uint32*4),
               ('observed_pins',c.c_uint32*10),('idle_rx',c.c_uint8*10)]

class Registers:
    def __init__(self,**kw):
        self.peer=wiretest.Peer(**kw);self.exceptions=[];self.writes=[];self.reads=[];self.delays=[]
        self.reg={CR:5,CFGR:0,D1CFGR:0,D1CCIPR:0x20,D2CCIP1R:0x80004000,
          GATES:0x8002,ENABLE:0x4000,RESET:0x40}
        for base in (GC,GD):
            for off in (0,4,8,12,16,20,24,36):self.reg[base+off]=0xa5a5a5a5
        self.reg[GD+16]=self.reg[GD+20]=0xa5a5a5a5
        for off in (0,4,8,12,16,20,24,32,48,80):self.reg[SPI+off]=0
        self.before=dict(self.reg);self.rx=[];self.n=0;self.sent=0;self.eot=False;self.guarded=False
        self.stall=None;self.error_bits=0;self.extra_rx=False;self.ignored=set();self.stuck_cs=False
        self.miso_low=False;self.late_error=False;self.eot_reads=0;self.reset_pulses=0;self.incomplete_deselects=0
        self.callbacks=(READ(self.read),WRITE(self.write),DELAY(self.delay))
        self.io=MMIO(None,*self.callbacks)

    def read(self,ctx,a,width):
        try:
            self.reads.append((a,width))
            assert a in self.reg,'Unexpected register read: '+hex(a)
            if SPI<=a<SPI+84:
                assert self.reg[ENABLE]&0x8000,'SPI3 register read without clock'
                assert width==(1 if a==SPI+48 else 4)
            else:assert width==4
            if a==SPI+20:
                sr=(2 if self.stall!='tx' else 0)|(1|0x2000 if self.rx and self.stall!='rx' else 0)
                if self.eot and self.stall!='eot':sr|=8;self.eot_reads+=1
                if self.reg[SPI]&0x400:sr|=0x800
                # Last-byte RXP read is first, wait-for-EOT read is second.
                # Inject only on the following snapshot, so the final check
                # (rather than wait_flag's earlier check) must detect it.
                if self.late_error and self.eot_reads>=3:sr|=0x40
                return sr|self.error_bits
            if a==SPI+48:
                assert self.rx,'Read of empty receive FIFO'
                value=self.rx.pop(0)
                if self.extra_rx and self.sent==self.n and not self.rx:self.rx.append(0x44)
                return value
            if a==GD+16 and self.stuck_cs:return self.reg[a]&~1
            return self.reg[a]
        except Exception as e:self.exceptions.append(e);return 0

    def write(self,ctx,a,value,width):
        try:
            self.writes.append((a,value,width))
            masks={ENABLE:0x8000,RESET:0x8000,GATES:12,GC:0x03f00000,GC+4:0x1c00,
                   GC+8:0x03f00000,GC+12:0x03f00000,GC+36:0x000fff00,
                   GD:3,GD+4:1,GD+8:3,GD+12:3}
            if a in masks:
                assert width==4
                assert not ((self.reg[a]^value)&~masks[a]),'Unrelated register field changed'
            elif a==GD+24:assert width==4 and value in (1,0x10000)
            else:
                assert a in (SPI,SPI+4,SPI+8,SPI+12,SPI+16,SPI+24,SPI+32,SPI+80),hex(a)
                assert self.reg[ENABLE]&0x8000,'SPI3 write without clock'
                assert width==(1 if a==SPI+32 else 4)
            if a in self.ignored:return
            if a==RESET and value&0x8000:
                self.reset_pulses+=1
                for off in (0,4,8,12,16,20,24,32,48,80):self.reg[SPI+off]=0
                self.rx=[];self.sent=0;self.eot=False;self.guarded=False
            if a==GD+24:
                old=bool(self.reg[GD+20]&1)
                self.reg[GD+20]=(self.reg[GD+20]|1) if value==1 else (self.reg[GD+20]&~1)
                self.reg[GD+16]=(self.reg[GD+16]&~1)|(self.reg[GD+20]&1)
                new=bool(self.reg[GD+20]&1)
                if old and not new:
                    self.peer.command=[];self.peer.reply=[]
                if not old and new and self.peer.reply:self.incomplete_deselects+=1
                self.peer.selected=not new;return
            if a==SPI+4:
                assert not self.reg[SPI]&1,'TSIZE written while SPE enabled'
                self.n=value;self.sent=0;self.eot=False;self.eot_reads=0;self.guarded=False
            if a==SPI:
                if self.reg[SPI]&1 and not value&1 and self.eot:
                    assert self.guarded,'SPI disabled before post-EOT guard'
                    assert not self.rx,'SPI disabled before RxFIFO drained'
                if value&0x400:value&=~0x200
            if a==SPI+24:
                assert value==0xff8
                self.eot=False;self.eot_reads=0;self.guarded=False
            if a==SPI+32:
                assert self.reg[SPI]&0x201==0x201,'TXDR before SPE/CSTART'
                tx=(c.c_uint8*1)(value);rx=(c.c_uint8*1)();accepted=c.c_uint();received=c.c_uint();detail=c.c_uint32()
                rc=self.peer.transfer(None,tx,rx,1,c.pointer(accepted),c.pointer(received),c.pointer(detail))
                # Callbacks receive pointer objects; peer writes through [0].
                assert rc==0,'Byte peer rejected transfer'
                self.rx.append(0 if self.miso_low else rx[0]);self.sent+=1
                if self.sent==self.n:
                    self.eot=True
                    if self.stall!='eot':self.reg[SPI]&=~0x200
                return
            self.reg[a]=value
        except Exception as e:self.exceptions.append(e)

    def delay(self,ctx,count):
        self.delays.append(count)
        if self.eot and count>=512:self.guarded=True

class ActualSPI3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();p=Path(cls.temp.name)
        (p/'h.c').write_text('#include "spi3_port.h"\nunsigned port_size(void){return sizeof(r10_sd_spi3_port);}\n'
            'unsigned query_complete(void){return SDQ_COMPLETE;}\nunsigned query_stopped(void){return SDQ_STOPPED;}\n')
        lib=p/'spi3.dylib'
        subprocess.run(['/usr/bin/clang','-dynamiclib','-O2','-std=c11','-Wall','-Wextra','-Werror',
            '-I'+str(HERE),*[str(HERE/(n+'.c')) for n in ('metadata','query','wire','spi3_port')],str(p/'h.c'),'-o',str(lib)],
            check=True,capture_output=True)
        cls.lib=c.CDLL(str(lib));cls.lib.r10_sd_spi3_bus.argtypes=[P(Port),P(wiretest.Bus)]
        cls.lib.r10_sd_wire_attach.argtypes=[P(wiretest.Wire),P(wiretest.Bus),P(protocol.IO)]
        cls.lib.r10_sd_query_begin.argtypes=[P(protocol.Query),P(protocol.IO),c.c_uint32,c.c_uint]
        cls.lib.r10_sd_query_poll.argtypes=[P(protocol.Query),c.c_uint32]
        cls.lib.r10_sd_spi3_transfer.argtypes=[P(Port),P(c.c_uint8),P(c.c_uint8),c.c_uint,
                                             P(c.c_uint),P(c.c_uint),P(c.c_uint32)]
        cls.complete=cls.lib.query_complete();cls.stopped=cls.lib.query_stopped()
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def begin(self,**kw):
        m=Registers(**kw);port=Port();port.io=m.io;port.poll_limit=64
        bus=wiretest.Bus();wire=wiretest.Wire();io=protocol.IO();q=protocol.Query()
        self.lib.r10_sd_spi3_bus(c.byref(port),c.byref(bus))
        self.assertEqual(self.lib.r10_sd_wire_attach(c.byref(wire),c.byref(bus),c.byref(io)),0)
        self.lib.r10_sd_query_begin(c.byref(q),c.byref(io),0,1)
        return q,port,wire,m,io,bus

    def step(self,q,m):
        self.lib.r10_sd_query_poll(c.byref(q),m.peer.now)
        if m.exceptions:raise m.exceptions[0]
        if m.peer.exceptions:raise m.peer.exceptions[0]
        m.peer.now=(m.peer.now+1)&0xffffffff

    def finish(self,q,m):
        for _ in range(6000):
            if q.state in (self.complete,self.stopped):return
            self.step(q,m)
        self.fail('No bounded terminal state')

    def test_native_ffi_layout(self):self.assertEqual(self.lib.port_size(),c.sizeof(Port))

    def test_full_query_preserves_clock_neighbours_and_releases_owned_SPI3(self):
        q,p,w,m,io,bus=self.begin();self.finish(q,m)
        self.assertEqual((q.valid,q.error,p.owned,p.ready),(1,0,0,0))
        self.assertEqual(m.peer.high_clocks,80+64+8*len(m.peer.commands))
        self.assertEqual(m.incomplete_deselects,0)
        self.assertEqual(m.reg[ENABLE],m.before[ENABLE]);self.assertEqual(m.reg[RESET],m.before[RESET])
        for a in (CR,CFGR,D1CFGR,D1CCIPR,D2CCIP1R):self.assertEqual(m.reg[a],m.before[a])
        self.assertTrue(all(a not in (CR,CFGR,D1CFGR,D1CCIPR,D2CCIP1R) for a,v,width in m.writes))
        self.assertTrue(all(width==1 for a,v,width in m.writes if a==SPI+32))
        self.assertTrue(all(width==1 for a,width in m.reads if a==SPI+48))

    def test_wrong_shared_clock_is_read_only_and_no_command(self):
        for a,mask in ((CR,8),(CFGR,8),(D1CFGR,8),(D1CCIPR,1<<28),(D2CCIP1R,1<<12)):
            q,p,w,m,io,bus=self.begin();m.reg[a]^=mask;self.finish(q,m)
            self.assertEqual((q.valid,q.error,p.error),(0,3,2));self.assertEqual(m.writes,[])
            self.assertEqual(m.peer.commands,[])

    def test_chip_select_is_preloaded_before_output_mode(self):
        q,p,w,m,io,bus=self.begin();self.finish(q,m)
        preload=next(i for i,(a,v,width) in enumerate(m.writes) if a==GD+24 and v==1)
        output=next(i for i,(a,v,width) in enumerate(m.writes) if a==GD and v&3==1)
        self.assertLess(preload,output)

    def test_invalid_transfer_lengths_have_no_register_access(self):
        for n in (0,17,0xffffffff):
            q,p,w,m,io,bus=self.begin()
            for _ in range(20):
                self.step(q,m)
                if p.ready:break
            before=(len(m.reads),len(m.writes));data=(c.c_uint8*20)()
            accepted=c.c_uint(9);received=c.c_uint(9);detail=c.c_uint32()
            rc=self.lib.r10_sd_spi3_transfer(c.byref(p),data,data,n,c.byref(accepted),c.byref(received),c.byref(detail))
            self.assertEqual((rc,accepted.value,received.value,p.error),(2,0,0,9))
            self.assertEqual(before,(len(m.reads),len(m.writes)))

    def test_failed_pin_configuration_keeps_observed_values_after_cleanup(self):
        q,p,w,m,io,bus=self.begin()
        for _ in range(50):
            self.step(q,m)
            if m.peer.commands:break
        changed=m.reg[GC+36]^(1<<8);m.reg[GC+36]=changed
        self.finish(q,m)
        self.assertEqual((q.valid,p.error,p.observed_pins[4]),(0,8,changed))

    def test_external_SPI3_ownership_is_never_reset_or_parked(self):
        for a in (ENABLE,RESET):
            q,p,w,m,io,bus=self.begin();m.reg[a]|=0x8000;self.finish(q,m)
            self.assertEqual((q.valid,q.error,p.error),(0,3,3));self.assertEqual(m.writes,[])

    def test_GPIO_and_SPI_enable_readbacks_fail_with_separate_cleanup(self):
        for a,error in ((GATES,4),(ENABLE,6),(RESET,7),(GC,8)):
            q,p,w,m,io,bus=self.begin();m.ignored.add(a);self.finish(q,m)
            self.assertEqual((q.valid,q.error,p.error),(0,3,error))
            self.assertEqual(m.peer.commands,[])

    def test_TX_RX_EOT_stalls_have_finite_software_budgets(self):
        for stall in ('tx','rx','eot'):
            q,p,w,m,io,bus=self.begin();m.stall=stall;self.finish(q,m)
            self.assertEqual((q.valid,q.error,p.error),(0,3,11));self.assertEqual(m.peer.commands,[])
            self.assertLess(sum(a==SPI+20 for a,width in m.reads),220)

    def test_error_status_and_extra_RX_data_do_not_become_metadata_success(self):
        for bits in (0x20,0x40,0x80,0x100,0x200,0x800):
            q,p,w,m,io,bus=self.begin();m.error_bits=bits;self.finish(q,m)
            self.assertEqual((q.valid,q.error,p.error),(0,3,10))
        q,p,w,m,io,bus=self.begin();m.extra_rx=True;self.finish(q,m)
        self.assertEqual((q.valid,q.error,p.error),(0,3,12))

    def test_late_EOT_error_is_rechecked_before_clearing_flags(self):
        q,p,w,m,io,bus=self.begin();m.late_error=True;self.finish(q,m)
        self.assertEqual((q.valid,q.error,p.error),(0,3,10))

    def test_bootstrap_and_preflight_low_MISO_do_not_identify_card_absence(self):
        q,p,w,m,io,bus=self.begin();m.miso_low=True;self.finish(q,m)
        self.assertEqual((q.valid,q.error),(0,16));self.assertEqual(m.peer.commands,[])
        self.assertEqual(bytes(p.idle_rx),bytes(10));self.assertEqual(bytes(q.raw[0][:8]),bytes(8))

    def test_config_drift_after_bootstrap_stops_before_another_card_command(self):
        q,p,w,m,io,bus=self.begin()
        for _ in range(30):
            self.step(q,m)
            if m.peer.commands:break
        count=len(m.peer.commands);m.reg[SPI+8]^=1<<28
        self.finish(q,m);self.assertEqual(q.valid,0);self.assertEqual(p.error,8)
        self.assertEqual(len(m.peer.commands),count)

    def test_failed_clock_gating_never_claims_successful_cleanup(self):
        q,p,w,m,io,bus=self.begin()
        for _ in range(2000):
            self.step(q,m)
            if len(m.peer.commands)==13 and w.state==6:break
        m.ignored.add(ENABLE);self.finish(q,m)
        self.assertEqual((q.valid,q.error,q.cleanup_error,p.cleanup_error),(0,15,15,13))
        self.assertNotEqual(p.owned,0)

if __name__=='__main__':unittest.main()
