"""Fault cases for the real fixed-range transport and the bench mailbox ABI."""
import copy
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import Mock

from .engine import analyze, load_json
from .mailbox import FW, PROTOCOL, W, decode, read_consistent, capture_mailbox, analyze_mailbox, prom_crc4
from .transport import ReadOnlyAPGuard
from .test_diagnostics import SyntheticReader, fixture, bench_fixture, BINDING


def frame(heartbeat=1, **changes):
    manifest=load_json(FW/'build/manifest.json')
    w=[0]*128
    w[0:8]=[PROTOCOL['magic'],2,512,heartbeat*2,3,1000+heartbeat*1200,heartbeat,63]
    w[8:16]=struct.unpack('<8I',bytes.fromhex(manifest['board_sha256']))
    w[16:24]=struct.unpack('<8I',bytes.fromhex(manifest['build_sha256']))
    w[25]=0x20030450;w[26:29]=[0,0x01234567,0x89abcdef]
    w[29]=2;w[30]=1<<17;w[31]=2;w[32]=0xe9;w[33]=2;w[34]=0x77
    w[35:43]=[0x3132,0x3334,0x3536,0x3738,0x3940,0x4142,0x4344,0x450b]
    w[43]=w[44]=11;w[45]=2;w[46]=0xef4018;w[48]=5;w[49]=900
    for name,value in changes.items():w[W[name]]=value
    return checksum(w)


def checksum(w):
    data=bytearray(struct.pack('<128I',*w));data[12:16]=bytes(4)
    w[127]=zlib.crc32(data[:508]);return w


class SyntheticMailbox(SyntheticReader):
    def __init__(self, frames=None, **kwargs):
        super().__init__(**kwargs);self.frames=frames or [frame(1),frame(2)]
        self.sample=0;self.seq_reads=0;self.enabled=False;self.words=[]
    def enable_mailbox(self):self.enabled=True
    def read_mailbox_word(self,i):
        if not self.enabled:raise RuntimeError('Not enabled')
        self.words.append(i)
        v=self.frames[min(self.sample,len(self.frames)-1)][i]
        if i==3:
            self.seq_reads+=1
            if self.seq_reads==3:self.seq_reads=0;self.sample+=1
        return v


def evidence(frames=None, reader=None):
    binding=load_json(FW/'build/binding.json');manifest=load_json(FW/'build/manifest.json')
    with tempfile.TemporaryDirectory() as t:
        s=capture_mailbox(reader or SyntheticMailbox(frames),binding,manifest,'SYNTHETIC-NOT-HARDWARE',
                          Path(t)/'raw.json',origin='SYNTHETIC_FIXTURE',pause=lambda _:None)
    return s,binding,manifest


class MailboxTests(unittest.TestCase):
    def report(self,frames=None):
        return analyze_mailbox(*evidence(frames))
    def statuses(self,r):return {c['id']:c['status'] for c in r['checks']}
    def test_supported_fixture_is_still_incomplete_and_not_hardware(self):
        r=self.report();s=self.statuses(r)
        self.assertEqual(r['overall'],'INCOMPLETE');self.assertTrue(r['synthetic'])
        self.assertFalse(r['hardware_qualified']);self.assertFalse(r['fabrication_release'])
        for k in ('FIRMWARE_LIVENESS','IMU_ID','BARO_PROM','FLASH_JEDEC'):self.assertEqual(s[k],'PASS')
        for k in ('ADC_MEASUREMENTS','FLASH_QUAD_DATA','USB_ENUMERATION'):self.assertEqual(s[k],'NOT_TESTED')
    def test_manufacturer_crc4_vector(self):
        self.assertEqual(prom_crc4([0x3132,0x3334,0x3536,0x3738,0x3940,0x4142,0x4344,0x4500]),0xb)
    def test_crc_rejects_every_single_bit_error_in_record(self):
        original=frame()
        for byte in range(512):
            if 12<=byte<16:continue # sequence is checked independently
            for bit in range(8):
                w=original.copy();w[byte//4]^=1<<((byte%4)*8+bit)
                with self.assertRaises(ValueError):decode(w)
    def test_half_written_odd_sequence_rejected(self):
        w=frame();w[3]|=1
        with self.assertRaises(ValueError):decode(w)
    def test_changed_sequence_cannot_be_accepted(self):
        r=SyntheticMailbox();r.enable_mailbox();base=r.read_mailbox_word;seen=0
        def moving(i):
            nonlocal seen
            v=base(i)
            if i==3:
                seen+=1
                if seen%3==0:return v+2
            return v
        r.read_mailbox_word=moving
        self.assertIsNone(read_consistent(r,pause=lambda _:None)['accepted'])
    def test_bus_fault_preserves_partial_words(self):
        r=SyntheticMailbox();r.enable_mailbox();original=r.read_mailbox_word
        def fail(i):
            if i==10:raise OSError('injected SWD fault')
            return original(i)
        r.read_mailbox_word=fail
        result=read_consistent(r,attempts=1,pause=lambda _:None)
        self.assertIsNone(result['accepted']);self.assertEqual(len(result['attempts'][0]['words']),10)
        self.assertIn('injected SWD fault',result['attempts'][0]['error'])
    def test_frozen_record_cannot_show_sensor_pass(self):
        r=self.report([frame(1),frame(1)]);s=self.statuses(r)
        self.assertEqual(s['FIRMWARE_LIVENESS'],'INCONCLUSIVE');self.assertEqual(s['IMU_ID'],'INCONCLUSIVE')
    def test_reset_between_records_is_not_monotonic(self):
        self.assertEqual(self.statuses(self.report([frame(8),frame(1)]))['FIRMWARE_LIVENESS'],'INCONCLUSIVE')
    def test_wrong_firmware_identity_not_used(self):
        f=frame(2);f[16]^=1;checksum(f)
        r=self.report([frame(1),f]);self.assertNotIn('IMU_ID',self.statuses(r))
    def test_firmware_uid_must_match_independent_swd(self):
        f=frame(2);f[27]^=1;checksum(f)
        self.assertNotIn('IMU_ID',self.statuses(self.report([frame(1),f])))
    def test_report_rejects_stale_expected_binding(self):
        s,b,m=evidence();b['board_sha256']='0'*64
        with self.assertRaises(ValueError):analyze_mailbox(s,b,m)
    def test_wrong_family_performs_no_mailbox_reads(self):
        r=SyntheticMailbox(overrides={'DBGMCU_IDCODE':0x483});s,_,_=evidence(reader=r)
        self.assertEqual(r.words,[]);self.assertFalse(r.enabled);self.assertTrue(r.closed)
        self.assertNotEqual(s['state'],'CAPTURED')
    def test_no_probe_does_not_diagnose_a_broken_mcu(self):
        reader=SyntheticMailbox();reader.open=Mock(side_effect=OSError('No probe connected'))
        r=analyze_mailbox(*evidence(reader=reader))
        self.assertEqual(self.statuses(r)['TARGET'],'INCONCLUSIVE')
        self.assertEqual(r['overall'],'INCOMPLETE')
        self.assertFalse(any(c['status']=='PASS' for c in r['checks']))
    def test_wrong_chip_ids_or_empty_prom_cannot_hide_under_pass(self):
        for change,key in [({'IMU_ID':0xff},'IMU_ID'),({'FLASH_ID':0xffffff},'FLASH_JEDEC')]:
            self.assertEqual(self.statuses(self.report([frame(1),frame(2,**change)]))[key],'FAIL')
        for value in (0,65535):
            f=frame(2);f[35:43]=[value]*8;f[43]=f[44]=0;checksum(f)
            self.assertEqual(self.statuses(self.report([frame(1),f]))['BARO_PROM'],'FAIL')
    def test_crc_valid_record_with_bad_prom_crc_is_failed(self):
        f=frame(2);f[36]^=0x10;checksum(f)
        self.assertEqual(self.statuses(self.report([frame(1),f]))['BARO_PROM'],'FAIL')
    def test_no_read_data_write_permission_is_added(self):
        dp=Mock();g=ReadOnlyAPGuard(dp)
        with self.assertRaises(RuntimeError):g.write_ap(4,0x24000000)
        g.mailbox_enabled=True
        for a in range(0x24000000,0x24000200,4):g.write_ap(4,a)
        for a in (0x23fffffc,0x24000200,0x24000001,0x08000000):
            with self.assertRaises(RuntimeError):g.write_ap(4,a)
        for addr in (0x0c,0x10,0x14,0x18,0x1c):
            with self.assertRaises(RuntimeError):g.write_ap(addr,0)
    def test_new_power_board_uses_new_path(self):
        for profile in ('M3-PWR-R1','M3-PWR-R2','M3-PWR-R3'):
            b=copy.deepcopy(BINDING);b['profile']=profile;s=fixture();bench=bench_fixture(s,{'VLOGIC':0.2})
            c=next(c for c in analyze(s,b,bench)['checks'] if c['id']=='POWER_PATH')
            self.assertIn('U10',c['next_step']);self.assertIn('U11',c['next_step']);self.assertNotIn('D3 polarity',c['next_step'])
    def test_unknown_power_profile_does_not_guess_component(self):
        b=copy.deepcopy(BINDING);b['profile']='NEW-UNKNOWN';s=fixture()
        c=next(c for c in analyze(s,b,bench_fixture(s,{'VLOGIC':0.2}))['checks'] if c['id']=='POWER_PATH')
        self.assertNotIn('D3',c['next_step']);self.assertNotIn('U10',c['next_step'])


if __name__=='__main__':unittest.main()
