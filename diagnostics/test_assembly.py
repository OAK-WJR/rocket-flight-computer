"""Same v8 payload must still reject a different PCB/build identity."""
import json,struct,tempfile,unittest
from pathlib import Path
from . import test_power_status as old,test_usb as usb
from .mailbox import FW,ASSEMBLY_PROTOCOL,STATUS_PROTOCOL,decode,manifest_protocol,analyze_mailbox
from .usb import bound_snapshot,capture

def manifest():return json.loads((FW/'build_assembly_inspect/manifest.json').read_text())
def frame(h=1):
    w=old.frame(h);m=manifest()
    w[8:16]=struct.unpack('<8I',bytes.fromhex(m['board_sha256']))
    w[16:24]=struct.unpack('<8I',bytes.fromhex(m['build_sha256']))
    return usb.crc(w)

class AssemblyProfileTests(unittest.TestCase):
    def test_old_and_new_profiles_have_explicit_distinct_bindings(self):
        self.assertEqual(manifest_protocol(old.manifest()),STATUS_PROTOCOL)
        self.assertEqual(manifest_protocol(manifest()),ASSEMBLY_PROTOCOL)
        self.assertNotEqual(decode(old.frame())['board_sha256'],decode(frame())['board_sha256'])
    def test_same_wire_version_cannot_hide_wrong_pcb(self):
        for words,m in [(old.frame(),manifest()),(frame(),old.manifest())]:
            with self.assertRaises(ValueError):bound_snapshot(usb.Serial([words]).client(),m)
    def test_forged_board_profile_and_capability_rejected(self):
        for key,value in [('profile','M3-PDIAG-R1'),('board_sha256',STATUS_PROTOCOL['board_sha256'])]:
            m=manifest();m[key]=value
            with self.assertRaises(ValueError):manifest_protocol(m)
        m=manifest();m['protocol']['capabilities']=0
        with self.assertRaises(ValueError):manifest_protocol(m)
    def test_invalid_power_history_still_rejected(self):
        w=frame();w[155]=0
        with self.assertRaises(ValueError):decode(usb.crc(w))
    def test_fault_history_survives_new_profile_usb_capture(self):
        a,b=frame(1),frame(2);b[153]|=8;b[155]|=64;b[158]=1;b=usb.crc(b)
        m=manifest();binding=json.loads((FW/'build_assembly_inspect/binding.json').read_text())
        with tempfile.TemporaryDirectory() as t:
            e=capture(usb.Serial([a,b]).client,m,'SYNTHETIC-ASSEMBLY',Path(t)/'capture.json',pause=lambda _:None,origin='SYNTHETIC_FIXTURE')
            r=analyze_mailbox(e,binding,m)
        checks={x['id']:x['status'] for x in r['checks']}
        self.assertEqual(checks['POWER_FAULT_HISTORY'],'FAIL')
        self.assertEqual(checks['POWER_DYNAMIC_TEST'],'NOT_TESTED')
        self.assertTrue(r['synthetic']);self.assertFalse(r['hardware_qualified'])

if __name__=='__main__':unittest.main()
