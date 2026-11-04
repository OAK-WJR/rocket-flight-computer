"""Actual C query + wire parser against a byte-oriented peer, no target IO."""
import ctypes as c
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import test_query as protocol
import test_metadata as codec

P=c.POINTER
INIT=c.CFUNCTYPE(c.c_int,c.c_void_p,P(c.c_uint32),P(c.c_uint32),P(c.c_uint32))
SELECT=c.CFUNCTYPE(c.c_int,c.c_void_p,c.c_uint,P(c.c_uint32))
TRANSFER=c.CFUNCTYPE(c.c_int,c.c_void_p,P(c.c_uint8),P(c.c_uint8),c.c_uint,
                     P(c.c_uint),P(c.c_uint),P(c.c_uint32))
RELEASE=c.CFUNCTYPE(c.c_int,c.c_void_p,P(c.c_uint32))

class Bus(c.Structure):
    _fields_=[('context',c.c_void_p),('initialize',INIT),('select',SELECT),
              ('transfer',TRANSFER),('release',RELEASE)]

class Wire(c.Structure):
    _fields_=[('bus',Bus)]+[(n,c.c_uint32) for n in (
        'state error detail cleanup_error cleanup_detail request accepted_total received_total exchanges '
        'prefix_count token_count result_count result_delivered trace_accepted trace_received initialized selected'
    ).split()]+[('tx_prefix',c.c_uint8*64),('rx_prefix',c.c_uint8*64),('result',c.c_uint8*20)]

class Peer:
    def __init__(self,*,legacy=False,block=True):
        self.legacy,self.block=legacy,block
        self.selected=False;self.command=[];self.reply=[];self.commands=[];self.exceptions=[]
        self.now=0;self.idle=True;self.crc=False;self.app=False;self.busy=2
        self.initializations=self.releases=self.transfers=self.high_clocks=0
        self.wire=[];self.fail_transfer=None;self.count_fault=None;self.bad_token=None
        self.missing_r1=False;self.missing_token=False;self.bad_r1=False
        self.release_error=False;self.select_error=False;self.clock=250000;self.release_delay=0
        self.callbacks=(INIT(self.initialize),SELECT(self.select),TRANSFER(self.transfer),RELEASE(self.release))
        self.bus=Bus(None,*self.callbacks)

    def initialize(self,ctx,hz,clocks,detail):
        self.initializations+=1;hz[0]=self.clock;clocks[0]=80;detail[0]=0
        return 0

    def select(self,ctx,asserted,detail):
        detail[0]=0
        if self.select_error:detail[0]=0x1234;return 2
        try:
            if asserted:
                assert not self.selected,'CS was reasserted during an unfinished transaction'
                self.command=[];self.reply=[]
            elif self.selected:
                assert not self.reply,'CS rose before the full reply/register packet was consumed'
            self.selected=bool(asserted);return 0
        except Exception as e:self.exceptions.append(e);return 2

    def prepare(self):
        frame=bytes(self.command)
        assert frame[0]&0xc0==0x40
        assert frame[5]==(codec.crc7(frame[:5])<<1)|1
        op=frame[0]&63;arg=int.from_bytes(frame[1:5],'big');self.commands.append((op,arg))
        assert op in (0,8,59,55,41,58,9,10),'Unexpected media or write command'
        if op==0:
            assert arg==0 and sum(x==0 for x,_ in self.commands)==1
            self.idle=True;reply=b'\x01'
        elif op==8:
            assert arg==0x1aa
            reply=b'\x05' if self.legacy else b'\x01\0\0\x01\xaa'
        elif op==59:
            assert arg==1 and self.idle
            self.crc=True;reply=b'\x01'
        elif op==55:
            assert arg==0;self.app=True;reply=bytes([int(self.idle)])
        elif op==41:
            assert self.app and self.crc and arg==(0 if self.legacy else 0x40000000)
            self.app=False
            if self.busy:self.busy-=1
            else:self.idle=False
            reply=bytes([int(self.idle)])
        elif op==58:
            assert arg==0
            value=0x00ff8000|(0 if self.idle else 0x80000000|(int(self.block)<<30))
            reply=bytes([int(self.idle)])+value.to_bytes(4,'big')
        else:
            assert arg==0 and self.crc and not self.idle
            packet=codec.cid() if op==10 else codec.csd() if self.block else codec.csd(0,1023,9,5)
            if self.bad_token is not None:packet=packet[:1]+bytes([self.bad_token])+packet[2:]
            # Two idle bytes occur between R1 and the actual data token.
            reply=packet[:1]+b'\xff\xff'+packet[1:]
            if self.missing_token:reply=packet[:1]+b'\xff'*16
        if self.missing_r1:reply=b'\xff'*16
        if self.bad_r1:reply=b'\x80'
        self.reply=list(b'\xff'+reply)

    def transfer(self,ctx,tx,rx,n,accepted,received,detail):
        self.transfers+=1;accepted[0]=received[0]=0;detail[0]=0
        if self.transfers==self.fail_transfer:detail[0]=0xabcd;return 2
        try:
            for i in range(n):
                value=tx[i]
                if not self.selected:
                    assert value==0xff,'Non-idle byte clocked with CS high'
                    self.high_clocks+=8;reply=0xff
                elif len(self.command)<6:
                    self.command.append(value);reply=0xff
                    if len(self.command)==6:self.prepare()
                else:
                    assert value==0xff,'Payload sent after metadata command'
                    reply=self.reply.pop(0) if self.reply else 0xff
                rx[i]=reply;accepted[0]+=1;received[0]+=1
                self.wire.append((self.selected,value,reply))
            if self.count_fault=='over':accepted[0]=n+1
            if self.count_fault=='receive':accepted[0]=0;received[0]=1
            if self.count_fault=='short':received[0]=0
            return 0
        except Exception as e:self.exceptions.append(e);return 2

    def release(self,ctx,detail):
        self.releases+=1;detail[0]=0x4321 if self.release_error else 0
        self.now=(self.now+self.release_delay)&0xffffffff
        if self.release_error:return 2
        self.selected=False;self.reply=[];return 0

class ActualWire(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();p=Path(cls.temp.name)
        (p/'h.c').write_text('#include "wire.h"\nunsigned wire_size(void){return sizeof(r10_sd_wire);}\n'
            'unsigned query_complete(void){return SDQ_COMPLETE;}\n'
            'unsigned query_stopped(void){return SDQ_STOPPED;}\n')
        lib=p/'wire.dylib'
        subprocess.run(['/usr/bin/clang','-dynamiclib','-O2','-std=c11','-Wall','-Wextra','-Werror',
            '-I'+str(HERE),str(HERE/'wire.c'),str(HERE/'query.c'),str(HERE/'metadata.c'),str(p/'h.c'),'-o',str(lib)],
            check=True,capture_output=True)
        cls.lib=c.CDLL(str(lib));cls.lib.r10_sd_wire_attach.argtypes=[P(Wire),P(Bus),P(protocol.IO)]
        cls.lib.r10_sd_query_begin.argtypes=[P(protocol.Query),P(protocol.IO),c.c_uint32,c.c_uint]
        cls.lib.r10_sd_query_poll.argtypes=[P(protocol.Query),c.c_uint32]
        cls.complete=cls.lib.query_complete();cls.stopped=cls.lib.query_stopped()
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def begin(self,**kw):
        peer=Peer(**kw);wire=Wire();io=protocol.IO();q=protocol.Query()
        self.assertEqual(self.lib.r10_sd_wire_attach(c.byref(wire),c.byref(peer.bus),c.byref(io)),0)
        self.lib.r10_sd_query_begin(c.byref(q),c.byref(io),peer.now,1)
        return q,wire,peer,io

    def step(self,q,p):
        self.lib.r10_sd_query_poll(c.byref(q),p.now)
        if p.exceptions:raise p.exceptions[0]
        p.now=(p.now+1)&0xffffffff

    def finish(self,q,p):
        for _ in range(6000):
            if q.state in (self.complete,self.stopped):return
            self.step(q,p)
        self.fail('Query did not reach a bounded terminal state')

    def test_c_ffi_layout(self):self.assertEqual(self.lib.wire_size(),c.sizeof(Wire))

    def test_v2_complete_packets_continuous_cs_and_fixed_commands(self):
        q,w,p,io=self.begin();self.finish(q,p)
        self.assertEqual((q.valid,q.error,q.metadata.valid,p.releases),(1,0,1,1))
        self.assertEqual([op for op,arg in p.commands],[0,8,59,58,55,41,55,41,55,41,58,9,10])
        self.assertEqual(bytes(q.raw[8]),codec.csd());self.assertEqual(bytes(q.raw[9]),codec.cid())
        self.assertEqual(p.high_clocks,64+8*len(p.commands))
        self.assertFalse(p.selected)

    def test_legacy_and_v2_sdsc_have_no_mmc_fallback(self):
        for legacy in (False,True):
            with self.subTest(legacy=legacy):
                q,w,p,io=self.begin(legacy=legacy,block=False);self.finish(q,p)
                self.assertEqual((q.valid,q.metadata.block,q.metadata.capacity),(1,0,64<<20))
                self.assertNotIn(1,[x for x,_ in p.commands])

    def test_fragmented_data_retains_cs_until_last_crc_byte(self):
        q,w,p,io=self.begin();seen=False
        for _ in range(6000):
            self.step(q,p)
            if w.state==5 and w.result_count>2:
                seen=True;self.assertTrue(p.selected);self.assertGreater(w.result_count,w.result_delivered-1)
            if q.state in (self.complete,self.stopped):break
        self.assertTrue(seen);self.assertEqual(q.valid,1)

    def test_wrong_clock_never_sends_a_card_command(self):
        q,w,p,io=self.begin();p.clock=1000000;self.finish(q,p)
        self.assertEqual((q.valid,q.error,p.commands),(0,4,[]))

    def test_no_response_and_invalid_prefix_are_bounded_not_absence_claims(self):
        for flag,expected in (('missing_r1',6),('bad_r1',7)):
            q,w,p,io=self.begin();setattr(p,flag,True);self.finish(q,p)
            self.assertEqual((q.valid,q.error,w.error),(0,6,expected))
            self.assertLess(p.transfers,24);self.assertEqual(len(p.commands),1)

    def test_missing_and_bad_data_tokens_retain_current_prefix(self):
        q,w,p,io=self.begin();p.missing_token=True;self.finish(q,p)
        self.assertEqual((q.valid,q.error,w.error),(0,6,8));self.assertEqual(q.raw[8][0],0)
        # Bad tokens leave normalized R1+token bytes before failing.
        q,w,p,io=self.begin();p.bad_token=0x0b;self.finish(q,p)
        self.assertEqual((q.valid,q.error,w.error),(0,6,9))
        self.assertEqual(bytes(q.raw[8][:q.counts[8]]),b'\0\x0b')

    def test_transfer_counts_cannot_read_uninitialized_or_excess_bytes(self):
        for fault in ('over','receive','short'):
            q,w,p,io=self.begin();p.count_fault=fault;self.finish(q,p)
            self.assertEqual((q.valid,q.error,w.error),(0,5,5))
            self.assertEqual((w.trace_accepted,w.trace_received),(0,0) if fault!='short' else (8,0))

    def test_first_and_later_bus_failures_preserve_stage_and_trace(self):
        for call in (1,2,4,7,20):
            q,w,p,io=self.begin();p.fail_transfer=call;self.finish(q,p)
            self.assertEqual((q.valid,w.error,w.detail),(0,4,0xabcd))
            self.assertGreaterEqual(w.exchanges,1);self.assertEqual(p.releases,1)

    def test_select_and_cleanup_failures_do_not_become_success(self):
        q,w,p,io=self.begin();p.select_error=True;p.release_error=True;self.finish(q,p)
        self.assertEqual((q.valid,q.error,q.cleanup_error,w.cleanup_error),(0,5,15,10))
        self.assertEqual((w.detail,w.cleanup_detail),(0x1234,0x4321))

    def test_late_release_is_rechecked_and_not_repeated(self):
        q,w,p,io=self.begin();p.release_delay=6000;self.finish(q,p)
        self.assertEqual((q.valid,q.error,p.releases),(0,8,1))

    def test_failed_and_completed_queries_do_no_more_bus_io(self):
        for failed in (False,True):
            q,w,p,io=self.begin();p.bad_r1=failed;self.finish(q,p)
            before=(p.transfers,p.releases,len(p.commands))
            for _ in range(30):self.step(q,p)
            self.assertEqual(before,(p.transfers,p.releases,len(p.commands)))

if __name__=='__main__':unittest.main()
