"""v8 C-to-host evidence and full Flash/USB round trip; all inputs synthetic."""
import ctypes as c,json,struct,tempfile,unittest
from pathlib import Path
from . import test_gnss as old,test_usb as uf
from .mailbox import FW,STATUS_PROTOCOL as P,decode,manifest_protocol,analyze_mailbox
from .power_status import measurement,checks
from .usb import capture,bound_snapshot
from .storage import recover
from m3_firmware import test_power_status as ps
from m3_firmware import test_storage as cs
def manifest(mode='inspect'):return json.loads((FW/('build_status_'+mode)/'manifest.json').read_text())
def frame(h=1,mode='inspect'):
    w=old.frame(h,mode);m=manifest(mode);w[1]=8;w[7]=P['capabilities']
    w[8:16]=struct.unpack('<8I',bytes.fromhex(m['board_sha256']));w[16:24]=struct.unpack('<8I',bytes.fromhex(m['build_sha256']))
    w[153:160]=[7,0x53,0x00530000,w[5]-1,w[5]-10,0,1]
    return uf.crc(w)
class PowerHostTests(unittest.TestCase):
    def test_high_mux_is_ambiguous_and_high_fault_is_not_power_good(self):
        r=measurement(frame());self.assertEqual(r['source_report'],'USB_OR_OUTPUT_HIZ')
        self.assertFalse(r['source_voltage_verified']);self.assertFalse(r['hardware_qualified'])
    def test_low_mux_reports_battery_selection_without_voltage_guarantee(self):
        w=frame();w[154]=0x51;w[155]|=2;r=measurement(w)
        self.assertEqual(r['source_report'],'BATTERY_IN2_SELECTED');self.assertFalse(r['source_voltage_verified'])
    def test_stale_future_and_uninitialized_cannot_claim_input_state(self):
        for value in (frame()[5]-101,frame()[5]+1):
            w=frame();w[156]=value;r=measurement(w);self.assertIsNone(r['active_fault_signals']);self.assertEqual(r['source_report'],'UNKNOWN')
        w=frame();w[153:160]=[0]*7;self.assertFalse(measurement(w)['current_inputs_valid'])
    def test_unknown_bits_and_impossible_history_rejected(self):
        for pos,val in ((153,128),(154,65536),(155,4),(183,1),(158,1),(155,0),(153,0)):
            w=frame();w[pos]=val
            with self.assertRaises(ValueError):decode(uf.crc(w))
    def test_short_pulse_remains_visible_after_recovery(self):
        w=frame();w[153]|=8;w[155]|=64;w[158]=1
        r=measurement(uf.crc(w));self.assertEqual(r['active_fault_signals'],[]);self.assertEqual(r['fault_signals_seen'],['USB_LIMITER'])
        rows,_=checks([dict(words=w)],True);self.assertIn(('POWER_FAULT_HISTORY','FAIL'),[x[:2] for x in rows])
    def test_history_cannot_silently_clear_within_capture(self):
        a,b=frame(1),frame(2);a[155]|=1
        rows,_=checks([dict(words=a),dict(words=b)],True);self.assertIn(('POWER_HISTORY_CLEARED','FAIL'),[x[:2] for x in rows])
    def test_new_manifest_cannot_accept_older_board_or_protocol(self):
        m=manifest();m['build_options']['board']='gnss'
        with self.assertRaises(ValueError):manifest_protocol(m)
        with self.assertRaises(ValueError):bound_snapshot(uf.Serial([old.frame()]).client(),manifest())
    def test_usb_capture_preserves_power_and_gnss_evidence(self):
        s=uf.Serial([frame(1),frame(2)]);m=manifest();binding=json.loads((FW/'build_status_inspect/binding.json').read_text())
        with tempfile.TemporaryDirectory() as t:
            e=capture(s.client,m,'SYNTHETIC-POWER',Path(t)/'capture.json',pause=lambda _:None,origin='SYNTHETIC_FIXTURE')
            r=analyze_mailbox(e,binding,m)
        states={x['id']:x['status'] for x in r['checks']}
        self.assertEqual(states['POWER_MONITOR'],'PASS');self.assertEqual(states['POWER_SOURCE'],'INFO')
        self.assertEqual(states['POWER_DYNAMIC_TEST'],'NOT_TESTED');self.assertEqual(states['GNSS_LINK'],'PASS')
        self.assertTrue(r['synthetic']);self.assertFalse(r['hardware_qualified'])
class PowerJournalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):old.GNSSJournalTests.setUpClass.__func__(cls)
    @classmethod
    def tearDownClass(cls):old.GNSSJournalTests.tearDownClass.__func__(cls)
    def begin(self,n=None,mode='record'):
        n=n or cs.Nor();d=cs.Device();w=frame(1,mode);raw=struct.pack('<256I',*w)
        self.lib.storage_begin(c.byref(d),c.byref(n.io),int(mode=='record'),cs.arr(raw[32:96]+raw[104:116]));return n,d
    def append(self,d,h):
        w=frame(h,'record');w[3]=0;w=uf.crc(w);self.lib.storage_append(c.byref(d),cs.arr(struct.pack('<256I',*w)),h)
    def test_actual_c_latched_fault_survives_full_journal_recovery(self):
        ps.PowerStatusTests.setUpClass()
        try:
            w=frame(1,'record');s=ps.State();lib=ps.PowerStatusTests.lib
            lib.power_status_init(c.byref(s),w[5]-2,0x53,1)
            lib.power_status_observe(c.byref(s),w[5]-1,0x53,0x11,1,1)
            w[153:160]=struct.unpack('<7I',bytes(s.r));w[3]=0;w=uf.crc(w)
            n,d=self.begin();self.lib.storage_append(c.byref(d),cs.arr(struct.pack('<256I',*w)),1)
            r=recover(bytes(n.memory[:4096]),'SYNTHETIC_FIXTURE');self.assertFalse(r['issues'])
            self.assertEqual(r['records'][0]['words'][153:160],w[153:160])
            self.assertEqual(r['records'][0]['power_status']['fault_signals_seen'],['BATTERY_EFUSE','CAMERA_EFUSE'])
        finally:ps.PowerStatusTests.tearDownClass()
    def test_truncated_power_snapshot_cannot_replace_preceding_record(self):
        n,d=self.begin();self.append(d,1);self.append(d,2);raw=bytes(n.memory[:4096]);start=1536
        for cut in (0,32,220,256,600,612,636,768,1024,1279,1280):
            r=recover(raw[:start+cut]+b'\xff'*(4096-start-cut))
            self.assertEqual(len(r['records']),2 if cut==1280 else 1)
            self.assertIn('power_status',r['records'][0])
