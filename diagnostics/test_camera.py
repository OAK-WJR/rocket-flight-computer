"""UART-v3 mailbox faults; synthetic observations are never board qualification."""
import copy,struct,tempfile,unittest
from pathlib import Path
from .mailbox import FW,UART_PROTOCOL,capture_mailbox,analyze_mailbox,read_consistent,decode
from .engine import load_json
from .test_mailbox import frame,checksum,SyntheticMailbox
from .camera import crc8

def uart_frame(heartbeat=1,mode=True,**changes):
    manifest=load_json(FW/('build_uart_query' if mode else 'build_uart_idle')/'manifest.json')
    w=frame(heartbeat);cw=UART_PROTOCOL['words']
    w[1]=3;w[7]=127;w[5]=10000+heartbeat*1200
    w[8:16]=struct.unpack('<8I',bytes.fromhex(manifest['board_sha256']))
    w[16:24]=struct.unpack('<8I',bytes.fromhex(manifest['build_sha256']))
    if mode:
        d={'STATUS':2,'MODE':1,'START_MS':2000,'QUERY_MS':5000,'FINISHED_MS':5010,'POWER_READBACK':1,
           'KERNEL_HZ':64000000,'BRR':556,'TX_COUNT':3,'RX_COUNT':5,'PROTOCOL_VERSION':1,
           'FEATURES':0x1234,'VALID_LENGTH':5,'RAW_LENGTH':5}
        for k,v in d.items():w[cw['CAMERA_'+k]]=v
        raw=bytes([0xcc,1,0x34,0x12]);raw+=bytes([crc8(raw)])
        w[102:110]=struct.unpack('<8I',raw+bytes(27));w[110:112]=struct.unpack('<2I',raw+bytes(3))
        w[50]=1;w[49]=5015
    for k,v in changes.items():w[cw['CAMERA_'+k]]=v
    return checksum(w)

def evidence(frames=None,mode=True):
    folder=FW/('build_uart_query' if mode else 'build_uart_idle')
    b,m=load_json(folder/'binding.json'),load_json(folder/'manifest.json')
    reader=SyntheticMailbox(frames or [uart_frame(1,mode),uart_frame(2,mode)])
    with tempfile.TemporaryDirectory() as tmp:
        s=capture_mailbox(reader,b,m,'SYNTHETIC-CAMERA',Path(tmp)/'raw.json',origin='SYNTHETIC_FIXTURE',pause=lambda _:None)
    return s,b,m

class CameraMailboxTests(unittest.TestCase):
    def results(self,frames=None,mode=True):
        r=analyze_mailbox(*evidence(frames,mode));return r,{q['id']:q['status'] for q in r['checks']}
    def test_valid_info_still_not_a_qualified_board(self):
        r,s=self.results();self.assertEqual(s['CAMERA_UART'],'PASS')
        self.assertEqual(s['CAMERA_ELECTRICAL_QUALIFICATION'],'NOT_TESTED');self.assertEqual(r['overall'],'INCOMPLETE')
        self.assertTrue(r['synthetic']);self.assertFalse(r['hardware_qualified'])
        self.assertEqual(r['measurements'][0]['camera']['response_hex'],'cc013412'+f'{crc8(bytes.fromhex("cc013412")):02x}')
    def test_default_mode_never_claims_camera_tested(self):
        _,s=self.results(mode=False);self.assertEqual(s['CAMERA_UART'],'NOT_TESTED')
    def test_crc_implementation_matches_published_check(self):
        self.assertEqual(crc8(b'123456789'),0xbc);self.assertEqual(crc8(bytes.fromhex('cc00')),0x60)
    def test_old_version_rejected_before_extended_read(self):
        r=SyntheticMailbox([frame(),frame()]);r.enable_mailbox()
        x=read_consistent(r,attempts=1,pause=lambda _:None,protocol=UART_PROTOCOL)
        self.assertIsNone(x['accepted']);self.assertLessEqual(max(r.words),3)
    def test_new_version_rejected_by_legacy_expected_profile(self):
        r=SyntheticMailbox([uart_frame(),uart_frame()]);r.enable_mailbox()
        self.assertIsNone(read_consistent(r,attempts=1,pause=lambda _:None)['accepted']);self.assertLessEqual(max(r.words),3)
    def test_mode_or_raw_success_inconsistencies_rejected(self):
        for change in ({'MODE':0},{'ERROR':5},{'VALID_LENGTH':0},{'TX_COUNT':2},{'OE_READBACK':1},
                       {'KERNEL_HZ':32000000},{'BRR':277},{'FEATURES':1},{'ERROR_FLAGS':8},
                       {'QUERY_MS':2100},{'FINISHED_MS':7000},{'RAW_LENGTH':0},
                       {'START_MS':6000}):
            _,s=self.results([uart_frame(1),uart_frame(2,**change)])
            self.assertEqual(s['CAMERA_UART'],'FAIL',change)
        for word,value in ((49,4000),(49,15000),(102,0)):
            f=uart_frame(2);f[word]=value;checksum(f)
            _,s=self.results([uart_frame(1),f]);self.assertEqual(s['CAMERA_UART'],'FAIL',(word,value))
    def test_wire_crc_checked_independent_of_mailbox_crc(self):
        f=uart_frame(2);f[111]^=1;checksum(f)
        _,s=self.results([uart_frame(1),f]);self.assertEqual(s['CAMERA_UART'],'FAIL')
    def test_prior_noise_is_preserved_after_a_valid_reply(self):
        r,s=self.results([uart_frame(1),uart_frame(2,CRC_ERRORS=1,DISCARDED=5)])
        self.assertEqual(s['CAMERA_UART'],'PASS');self.assertEqual(s['CAMERA_RECEIVE_HISTORY'],'INCONCLUSIVE')
        self.assertEqual(r['measurements'][-1]['camera']['crc_errors'],1)
    def test_frozen_mailbox_cannot_grant_uart_pass(self):
        _,s=self.results([uart_frame(1),uart_frame(1)]);self.assertEqual(s['CAMERA_UART'],'INCONCLUSIVE')
    def test_manifest_cannot_enlarge_memory_grant(self):
        s,b,m=evidence();m=copy.deepcopy(m);m['protocol']['bytes']=1024
        with self.assertRaises(ValueError):analyze_mailbox(s,b,m)
    def test_board_profile_identity_mismatch_rejected(self):
        s,b,m=evidence();b=copy.deepcopy(b);b['profile']='M3-PWR-R3'
        with self.assertRaises(ValueError):analyze_mailbox(s,b,m)
    def test_reserved_words_still_rejected(self):
        w=uart_frame();w[112]=1;checksum(w)
        with self.assertRaises(ValueError):decode(w)
    def test_pin_voltage_not_inferred_from_command(self):
        r,s=self.results();power=next(q for q in r['checks'] if q['id']=='CAMERA_POWER_COMMAND')
        self.assertEqual(power['status'],'INFO');self.assertIn('cannot prove',power['next_step'])

if __name__=='__main__':unittest.main()
