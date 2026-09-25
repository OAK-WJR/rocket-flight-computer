"""Exercise production status history with synthetic levels and IRQ latches."""
import ctypes as c
import subprocess,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
class Result(c.Structure):
    _fields_=[(n,c.c_uint32) for n in 'flags gpio history sampled_ms last_event_ms irq_count max_gap_ms'.split()]
class State(c.Structure):_fields_=[('r',Result),('initialized',c.c_uint32)]
class PowerStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();p=Path(cls.tmp.name)/'power.dylib'
        subprocess.run(['/usr/bin/clang','-dynamiclib','-O2','-Wall','-Wextra','-Werror',str(HERE/'src/power_status.c'),'-o',str(p)],check=True,capture_output=True)
        cls.lib=c.CDLL(str(p));cls.lib.power_status_init.argtypes=[c.POINTER(State),c.c_uint32,c.c_uint32,c.c_int]
        cls.lib.power_status_observe.argtypes=[c.POINTER(State),c.c_uint32,c.c_uint32,c.c_uint32,c.c_int,c.c_int]
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def setUp(self):self.s=State();self.lib.power_status_init(c.byref(self.s),100,0x53,1)
    def observe(self,now=101,gpio=0x53,pending=0,periodic=1,ok=1):
        self.lib.power_status_observe(c.byref(self.s),now,gpio,pending,periodic,ok);return self.s.r
    def test_uninitialized_is_not_measurement(self):
        self.s=State();self.observe(gpio=0,pending=1);self.assertEqual(bytes(self.s),bytes(32))
    def test_initial_inputs_recorded_without_inventing_interrupt(self):
        r=self.s.r;self.assertEqual((r.flags,r.history,r.irq_count,r.max_gap_ms),(3,0x530000,0,0))
    def test_fault_pulse_recovers_before_handler_but_history_survives(self):
        for pin in (1,16,64):
            r=self.observe(pending=pin);self.assertTrue(r.history&pin);self.assertEqual(r.gpio,0x53)
        self.assertEqual(r.irq_count,3);self.assertEqual(r.history&0xffff,0x51)
    def test_mux_latch_does_not_invent_edge_direction(self):
        r=self.observe(pending=2);self.assertFalse(r.history&2)
        r=self.observe(now=102,gpio=0x51,pending=2);self.assertTrue(r.history&2)
        self.assertEqual(r.history&0x51,0)
    def test_observed_low_and_recovery_never_clear_history(self):
        self.observe(gpio=0);r=self.observe(now=102);self.assertEqual(r.history,0x00530053)
    def test_other_gpio_and_interrupt_bits_do_not_create_power_events(self):
        r=self.observe(gpio=0xabff,pending=0xffac);self.assertEqual((r.irq_count,r.history&0xffff),(0,0))
    def test_config_corruption_then_recovery_retains_failure(self):
        r=self.observe(ok=0);self.assertFalse(r.flags&2);self.assertTrue(r.flags&32)
        r=self.observe(now=102);self.assertEqual(r.flags&34,34)
    def test_clock_wrap_and_long_reported_gap(self):
        self.lib.power_status_init(c.byref(self.s),0xfffffffe,0x53,1)
        r=self.observe(now=1);self.assertEqual(r.max_gap_ms,3);self.assertFalse(r.flags&16)
        r=self.observe(now=100);self.assertEqual(r.max_gap_ms,99);self.assertTrue(r.flags&16)
    def test_irq_counter_saturates_instead_of_hiding_history(self):
        self.s.r.irq_count=0xffffffff;r=self.observe(pending=1);self.assertEqual(r.irq_count,0xffffffff);self.assertTrue(r.flags&64)
    def test_event_timestamp_stays_at_last_change(self):
        self.observe(now=101,gpio=0x52);r=self.observe(now=104,gpio=0x52)
        self.assertEqual((r.last_event_ms,r.sampled_ms),(101,104))
    def test_actual_hal_adapter_is_input_only_and_detects_register_faults(self):
        exe=Path(self.tmp.name)/'hal'
        subprocess.run(['/usr/bin/clang','-O1','-Wall','-Wextra','-Werror','-fsanitize=undefined',
            '-I'+str(HERE/'tests/power_status'),'-I'+str(HERE/'src'),
            str(HERE/'tests/power_status_hal_harness.c'),str(HERE/'src/power_status.c'),'-o',str(exe)],check=True,capture_output=True)
        r=subprocess.run([str(exe)],check=True,capture_output=True,text=True,timeout=5)
        self.assertIn('21 configuration corruptions',r.stdout);self.assertEqual(r.stderr,'')
if __name__=='__main__':unittest.main()
