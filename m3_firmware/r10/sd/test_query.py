"""Execute the portable metadata query against a protocol model, with no IO.

The model decodes fixed command frames and tracks card/app/CRC state. It does
not choose responses by reading the query's state machine. These tests cannot
qualify native SPI timing, a real card, media integrity or an installed board.
"""
import ctypes as c
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_metadata as codec

OK, BUSY, ERROR = 0, 1, 2
PROBE = 9
U32P = c.POINTER(c.c_uint32)
INIT = c.CFUNCTYPE(c.c_int, c.c_void_p, c.c_uint32, U32P, U32P, U32P)
START = c.CFUNCTYPE(c.c_int, c.c_void_p, c.c_uint, U32P)
POLL = c.CFUNCTYPE(c.c_int, c.c_void_p, c.POINTER(c.c_uint8), c.c_uint, U32P, U32P)
CANCEL = c.CFUNCTYPE(c.c_int, c.c_void_p, U32P)


class IO(c.Structure):
    _fields_ = [('context', c.c_void_p), ('initialize', INIT), ('start', START),
                ('poll', POLL), ('cancel', CANCEL)]


class Query(c.Structure):
    _fields_ = [('io', IO)] + [(n, c.c_uint32) for n in (
        'state error detail cleanup_error cleanup_detail started_at observed_at stage_at '
        'command_at op_started_at last_op_at completed_at nominal_hz idle_clocks '
        'failed_phase commands_started op_requests last_io_count metadata_error').split()] + [
        ('command_ticks', c.c_uint32 * 10), ('completed_mask', c.c_uint32)] + [
        (n, c.c_uint) for n in 'phase version2 op_started op_ready valid cold_start_declared'.split()] + [
        ('counts', c.c_uint8 * 10), ('raw', (c.c_uint8 * 20) * 10),
        ('metadata', codec.Metadata)]


class CardModel:
    def __init__(self, lib, *, legacy=False, block=True, busy=2, chunk=20, now=0):
        self.lib = lib
        self.legacy, self.block, self.busy, self.chunk = legacy, block, busy, chunk
        self.now = now
        self.idle = 1
        self.crc = False
        self.app = False
        self.response = b''
        self.cursor = 0
        self.commands, self.initializations, self.reads, self.cancels = [], 0, 0, 0
        self.nominal_hz, self.idle_clocks = 250000, 80
        self.init_rc, self.cancel_rc = OK, OK
        self.start_error = self.read_error = self.overcount = None
        self.read_busy = False
        self.reply_overrides = {}
        self.advance = {}  # Callback elapsed time is visible at the next core poll.
        self.exceptions = []
        self.current_request = None
        self.callbacks = (INIT(self.initialize), START(self.start), POLL(self.poll), CANCEL(self.cancel))
        self.io = IO(None, *self.callbacks)

    def _delay(self, key):
        self.now = (self.now + self.advance.pop(key, 0)) & 0xffffffff

    def initialize(self, _context, _now, hz, clocks, detail):
        self.initializations += 1
        hz[0], clocks[0], detail[0] = self.nominal_hz, self.idle_clocks, 0x1100
        self._delay('initialize')
        return self.init_rc

    def start(self, _context, request, detail):
        try:
            detail[0] = 0x2200 | request
            if self.response and self.cursor < len(self.response):
                raise AssertionError('Overlapping normalized transactions')
            self.current_request = request
            self.commands.append((request, self.now))
            if request == PROBE:
                reply = b'\xff' * 8
            else:
                frame = (c.c_uint8 * 6)()
                if self.lib.r10_sd_metadata_frame(request, frame) != 0:
                    raise AssertionError('Unknown or non-fixed command')
                encoded = bytes(frame)
                if encoded[5] != ((codec.crc7(encoded[:5]) << 1) | 1):
                    raise AssertionError('Invalid command CRC7')
                op, arg = encoded[0] & 63, int.from_bytes(encoded[1:5], 'big')
                if op == 0:
                    if sum(r == 0 for r, _ in self.commands) != 1:
                        raise AssertionError('Unexpected reset retry')
                    self.idle = 1
                    reply = b'\x01'
                elif op == 8:
                    if arg != 0x1aa:
                        raise AssertionError('Wrong host voltage/check pattern')
                    reply = b'\x05' if self.legacy else b'\x01\x00\x00\x01\xaa'
                elif op == 59:
                    if arg != 1 or not self.idle:
                        raise AssertionError('CRC command in wrong mode')
                    self.crc = True
                    reply = bytes([self.idle])
                elif op == 55:
                    self.app = True
                    reply = bytes([self.idle])
                elif op == 41:
                    if not self.crc or not self.app:
                        raise AssertionError('Missing CRC_ON or APP prefix')
                    if arg != (0 if self.legacy else 0x40000000):
                        raise AssertionError('Unexpected HCS branch')
                    self.app = False
                    if self.busy is None:
                        self.idle = 1
                    elif self.busy:
                        self.busy -= 1
                        self.idle = 1
                    else:
                        self.idle = 0
                    reply = bytes([self.idle])
                elif op == 58:
                    ocr = 0x00ff8000 | ((0x80000000 | (int(self.block) << 30)) if not self.idle else 0)
                    reply = bytes([self.idle]) + ocr.to_bytes(4, 'big')
                elif op in (9, 10):
                    if self.idle or not self.crc:
                        raise AssertionError('Register access before initialization/CRC')
                    reply = codec.cid() if op == 10 else codec.csd() if self.block else codec.csd(0, 1023, 9, 5)
                else:
                    raise AssertionError('Unexpected media/write/erase command')
            self.response = self.reply_overrides.get(request, reply)
            self.cursor = 0
            self._delay('start')
            return ERROR if request == self.start_error else OK
        except Exception as error:
            self.exceptions.append(error)
            return ERROR

    def poll(self, _context, data, capacity, count, detail):
        self.reads += 1
        detail[0] = 0x3300 | self.current_request
        if self.current_request == self.overcount:
            count[0] = capacity + 1
            return OK
        if self.read_busy:
            count[0] = 0
            self._delay('poll')
            return BUSY
        n = min(capacity, self.chunk, len(self.response) - self.cursor)
        if n:
            c.memmove(data, self.response[self.cursor:self.cursor+n], n)
        self.cursor += n
        count[0] = n
        self._delay('poll')
        if self.current_request == self.read_error:
            return ERROR
        return BUSY if self.cursor != len(self.response) else OK

    def cancel(self, _context, detail):
        self.cancels += 1
        detail[0] = 0x4400
        self._delay('cancel')
        return self.cancel_rc


class ActualQuery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        p = Path(cls.temp.name)
        harness = p / 'harness.c'
        harness.write_text('#include "query.h"\n#include <stddef.h>\n'
            'unsigned query_size(void){return sizeof(r10_sd_query);}\n'
            'unsigned query_metadata_offset(void){return offsetof(r10_sd_query,metadata);}\n'
            'unsigned query_complete(void){return SDQ_COMPLETE;}\n'
            'unsigned query_stopped(void){return SDQ_STOPPED;}\n')
        library = p / 'query.dylib'
        subprocess.run(['/usr/bin/clang', '-dynamiclib', '-O2', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-I'+str(HERE), str(HERE/'query.c'), str(HERE/'metadata.c'), str(harness),
                        '-o', str(library)], check=True, capture_output=True)
        cls.lib = c.CDLL(str(library))
        cls.lib.r10_sd_query_begin.argtypes = [c.POINTER(Query), c.POINTER(IO), c.c_uint32, c.c_uint]
        cls.lib.r10_sd_query_poll.argtypes = [c.POINTER(Query), c.c_uint32]
        cls.lib.r10_sd_metadata_frame.argtypes = [c.c_uint, c.POINTER(c.c_uint8)]
        cls.complete = cls.lib.query_complete()
        cls.stopped = cls.lib.query_stopped()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def begin(self, **kw):
        m = CardModel(self.lib, **kw)
        q = Query()
        self.lib.r10_sd_query_begin(c.byref(q), c.byref(m.io), m.now, 1)
        return q, m

    def step(self, q, m, delta=1):
        self.lib.r10_sd_query_poll(c.byref(q), m.now)
        if m.exceptions:
            raise m.exceptions[0]
        m.now = (m.now + delta) & 0xffffffff

    def finish(self, q, m, maximum=7000):
        for _ in range(maximum):
            if q.state in (self.complete, self.stopped):
                return
            self.step(q, m)
        self.fail('Portable query exceeded the independent bounded model run')

    def assert_terminal(self, q, m):
        before = (q.state, q.error, len(m.commands), m.cancels, m.initializations, m.reads)
        for _ in range(20):
            self.step(q, m, 37)
        self.assertEqual(before, (q.state, q.error, len(m.commands), m.cancels, m.initializations, m.reads))

    def test_native_layout_is_checked(self):
        self.assertEqual(self.lib.query_size(), c.sizeof(Query))
        self.assertEqual(self.lib.query_metadata_offset(), Query.metadata.offset)

    def test_v2_success_fixed_order_crc_and_single_reset(self):
        q,m = self.begin()
        self.finish(q,m)
        self.assertEqual((q.state,q.error,q.valid,q.metadata.valid),(self.complete,0,1,1))
        commands=[r for r,_ in m.commands]
        self.assertEqual(commands,[9,0,1,2,6,3,5,3,5,3,5,6,7,8])
        self.assertEqual((q.op_requests,q.completed_mask,m.cancels),(3,1023,1))
        self.assertEqual(q.metadata.capacity,32<<30)
        self.assert_terminal(q,m)

    def test_legacy_branch_has_no_cmd1_fallback(self):
        q,m=self.begin(legacy=True,block=False)
        self.finish(q,m)
        self.assertEqual((q.error,q.valid,q.version2),(0,1,0))
        self.assertEqual([r for r,_ in m.commands if r in (4,5)],[4,4,4])
        self.assertEqual((q.metadata.block,q.metadata.capacity),(0,64<<20))

    def test_v2_sdsc_is_not_silently_forced_to_block_addressing(self):
        q,m=self.begin(block=False)
        self.finish(q,m)
        self.assertEqual((q.error,q.valid,q.version2,q.metadata.block),(0,1,1,0))

    def test_fragmented_prefixes_and_tick_wrap(self):
        for chunk in (1,2,7,20):
            with self.subTest(chunk=chunk):
                q,m=self.begin(chunk=chunk,now=0xffffffe0)
                self.finish(q,m)
                self.assertEqual((q.valid,q.error),(1,0))
                self.assertEqual(bytes(q.raw[8]),codec.csd())
                self.assertEqual(bytes(q.raw[9]),codec.cid())

    def test_cold_start_is_exact_and_missing_adapter_has_no_io(self):
        m=CardModel(self.lib)
        for cold in (0,2,0xffffffff):
            q=Query();self.lib.r10_sd_query_begin(c.byref(q),c.byref(m.io),0,cold)
            self.assertEqual((q.state,q.error),(self.stopped,2))
            self.assert_terminal(q,m)
        q=Query();self.lib.r10_sd_query_begin(c.byref(q),None,0,1)
        self.assertEqual((q.state,q.error),(self.stopped,1))
        self.assertEqual((m.initializations,m.reads,m.cancels,len(m.commands)),(0,0,0,0))

    def test_initialization_error_and_wrong_clock_stop_before_probe(self):
        for name,value,error in (('init_rc',ERROR,3),('nominal_hz',400000,4),('idle_clocks',79,4)):
            with self.subTest(name=name):
                q,m=self.begin();setattr(m,name,value);self.finish(q,m)
                self.assertEqual((q.valid,q.error,len(m.commands),m.cancels),(0,error,0,1))
                self.assert_terminal(q,m)

    def test_late_successful_initialization_is_not_accepted(self):
        q,m=self.begin();m.advance['initialize']=500;self.finish(q,m)
        self.assertEqual((q.error,q.valid,len(m.commands)),(8,0,0))

    def test_never_ready_initialization_is_bounded(self):
        q,m=self.begin();m.init_rc=BUSY;self.finish(q,m)
        self.assertEqual((q.error,q.valid,len(m.commands)),(8,0,0))
        self.assertLessEqual(m.now,503)

    def test_preflight_nonidle_is_not_card_absence_or_reset_permission(self):
        q,m=self.begin();m.reply_overrides[9]=b'\0'+b'\xff'*7;self.finish(q,m)
        self.assertEqual((q.error,q.failed_phase,q.valid),(16,0,0))
        self.assertEqual([r for r,_ in m.commands],[9])
        self.assertEqual(bytes(q.raw[0][:8]),m.reply_overrides[9])

    def test_start_read_and_count_failures_retain_evidence_and_never_retry(self):
        for field,error in (('start_error',5),('read_error',6),('overcount',7)):
            with self.subTest(field=field):
                q,m=self.begin();setattr(m,field,0);self.finish(q,m)
                self.assertEqual((q.error,q.valid,q.failed_phase),(error,0,1))
                self.assertEqual([r for r,_ in m.commands],[9,0])
                if field=='read_error':self.assertEqual(bytes(q.raw[1][:q.counts[1]]),b'\x01')
                if field=='overcount':self.assertEqual(q.last_io_count,21)
                self.assert_terminal(q,m)

    def test_read_stall_and_late_callbacks_are_not_accepted(self):
        for key in ('read_busy','start','poll'):
            with self.subTest(callback=key):
                q,m=self.begin()
                if key=='read_busy':m.read_busy=True
                else:m.advance[key]=200
                self.finish(q,m)
                self.assertEqual((q.valid,q.error),(0,8))
                self.assert_terminal(q,m)

    def test_command_responses_and_voltage_fail_closed(self):
        cases=((0,b'\0',10),(1,b'\x01\0\0\x01\xab',11),
               (2,b'\x05',10),(6,b'\x01\0\0\0\0',12),
               (3,b'\x05',10),(5,b'\x05',10),
               (7,b'\x01',10),(8,b'\x04',10))
        for request,reply,error in cases:
            with self.subTest(request=request):
                q,m=self.begin();m.reply_overrides[request]=reply;self.finish(q,m)
                self.assertEqual((q.valid,q.error),(0,error))
                self.assert_terminal(q,m)

    def test_metadata_crc_and_address_mode_fail_with_raw_bytes(self):
        for request,reply in ((7,codec.csd()[:-1]+bytes([codec.csd()[-1]^1])),
                              (8,codec.cid()[:-1]+bytes([codec.cid()[-1]^1])),
                              (7,codec.csd(0,1023,9,5))):
            with self.subTest(request=request):
                q,m=self.begin();m.reply_overrides[request]=reply;self.finish(q,m)
                self.assertEqual((q.error,q.valid),(14,0))
                self.assertNotEqual(q.metadata_error,0)
                phase=8 if request==7 else 9
                self.assertEqual(bytes(q.raw[phase]),reply)
                self.assertFalse(q.completed_mask & (1<<phase))

    def test_pending_acmd41_has_no_interleaved_metadata_and_deadline(self):
        q,m=self.begin(busy=None);self.finish(q,m)
        self.assertEqual((q.error,q.valid),(13,0))
        commands=[r for r,_ in m.commands]
        self.assertEqual(commands[:5],[9,0,1,2,6])
        self.assertTrue(all(r in (3,5) for r in commands[5:]))
        self.assertEqual(commands.count(0),1)
        self.assert_terminal(q,m)

    def test_clock_gap_and_backwards_time_stop_pending_query(self):
        for backwards,error in ((False,17),(True,9)):
            q,m=self.begin(busy=None)
            for _ in range(100):
                if q.op_started:break
                self.step(q,m)
            self.assertTrue(q.op_started)
            m.now=(m.now-3 if backwards else m.now+25)&0xffffffff
            self.step(q,m)
            self.assertEqual((q.error,q.valid),(error,0))
            self.assert_terminal(q,m)

    def test_cleanup_error_never_qualifies_complete_metadata(self):
        q,m=self.begin();m.cancel_rc=ERROR;self.finish(q,m)
        self.assertEqual((q.error,q.cleanup_error,q.cleanup_detail,q.valid),(15,15,0x4400,0))
        self.assertEqual(q.metadata.valid,1)  # Parsed evidence is separate from acquisition completion.
        self.assert_terminal(q,m)

    def test_primary_and_cleanup_errors_are_separate(self):
        q,m=self.begin();m.cancel_rc=ERROR;m.reply_overrides[0]=b'\x04';self.finish(q,m)
        self.assertEqual((q.error,q.cleanup_error,q.cleanup_detail,q.valid),(10,15,0x4400,0))

    def test_late_successful_cleanup_is_not_accepted(self):
        for elapsed in (200,6000):
            with self.subTest(elapsed=elapsed):
                q,m=self.begin();m.advance['cancel']=elapsed;self.finish(q,m)
                self.assertEqual((q.valid,q.error),(0,8))
                self.assertEqual(m.cancels,1)
                self.assert_terminal(q,m)

    def test_cleanup_timebase_reversal_never_publishes_valid(self):
        q,m=self.begin();m.advance['cancel']=0xfffffffc;self.finish(q,m)
        self.assertEqual((q.valid,q.error,m.cancels),(0,9,1))
        self.assert_terminal(q,m)

    def test_entire_final_command_budget_includes_cleanup_boundary(self):
        # With this one-byte-time model, CID start->cancel is2ticks. The final
        # confirmation adds1tick:196+3=199 is accepted,197+3=200 is timed out.
        for elapsed,valid,error in ((196,1,0),(197,0,8)):
            with self.subTest(elapsed=elapsed):
                q,m=self.begin();m.advance['cancel']=elapsed;self.finish(q,m)
                self.assertEqual((q.valid,q.error,m.cancels),(valid,error,1))


if __name__=='__main__':
    unittest.main()
