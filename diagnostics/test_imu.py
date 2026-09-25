"""Protocol v4 faults and evidence classification, all synthetic."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from .engine import load_json
from .mailbox import (FW,IMU_PROTOCOL,PROTOCOL,UART_PROTOCOL,capture_mailbox,analyze_mailbox,
                      decode,read_consistent,report_file,manifest_protocol)
from .test_mailbox import SyntheticMailbox,checksum
from .test_acquisition import measured
from .test_camera import uart_frame

def imu_frame(h=1,mode=False,raw=None,**changes):
    folder=FW/('build_imu_query' if mode else 'build_imu_idle')
    m=load_json(folder/'manifest.json');p=IMU_PROTOCOL['words']
    w=measured(h);camera=uart_frame(h,mode)
    w[1]=4;w[7]=255;w[8:16]=camera[8:16];w[16:24]=struct.unpack('<8I',bytes.fromhex(m['build_sha256']))
    # Reuse real camera fixture payload while keeping measurement timestamps.
    w[82:112]=camera[82:112];w[50]=camera[50]
    if mode:
        offset=10000
        for n in (5,53,54,65,76,77):w[n]+=offset
        w[49]=5015
    d={'SAMPLE_STATUS':2,'CONFIG':0x020f0a0a,'EVIDENCE':0xe9070004,'BUS_HZ':1000000,
       'READ_START_MS':w[5]-80,'READ_MS':w[5]-80,'READ_FINISHED_MS':w[5]-79}
    d.update(changes)
    for k,v in d.items():w[p['IMU_'+k]]=v
    wire=struct.pack('>7h',1024,-1024,512,8192,-8192,0,128) if raw is None else raw
    w[122:126]=struct.unpack('<4I',wire+bytes(2))
    return checksum(w)

def evidence(frames=None,mode=False):
    f=FW/('build_imu_query' if mode else 'build_imu_idle');b=load_json(f/'binding.json');m=load_json(f/'manifest.json')
    with tempfile.TemporaryDirectory() as tmp:
        raw=Path(tmp)/'raw.json'
        s=capture_mailbox(SyntheticMailbox(frames or [imu_frame(1,mode),imu_frame(2,mode)]),b,m,
                         'SYNTHETIC-IMU',raw,origin='SYNTHETIC_FIXTURE',pause=lambda _:None)
    return s,b,m

class ImuMailboxTests(unittest.TestCase):
    def report(self,frames=None,mode=False):
        r=analyze_mailbox(*evidence(frames,mode));return r,{c['id']:c['status'] for c in r['checks']}
    def test_nominal_units_and_other_functions_are_preserved(self):
        r,s=self.report()
        for key in ('IMU_SAMPLES','ADC_MEASUREMENTS','BARO_MEASUREMENTS'):self.assertEqual(s[key],'PASS')
        units=r['measurements'][0]['imu']['nominal_units']
        self.assertEqual(units,dict(acceleration_g=[1,-1,.5],angular_rate_dps=[1000,-1000,0],temperature_c=26))
        self.assertEqual(r['overall'],'INCOMPLETE');self.assertTrue(r['synthetic']);self.assertFalse(r['hardware_qualified'])
        for key in ('IMU_INTERRUPT_WIRING','IMU_SELF_TEST','USB_ENUMERATION','LOGGING_POWER_LOSS'):self.assertEqual(s[key],'NOT_TESTED')
    def test_optional_camera_query_coexists_with_imu(self):
        r,s=self.report(mode=True);self.assertEqual(s['CAMERA_UART'],'PASS');self.assertEqual(s['IMU_SAMPLES'],'PASS')
    def test_each_claimed_success_must_match_evidence(self):
        bad=[{'SAMPLE_ERROR':3},{'INIT_ERROR':7},{'IO_ERROR':0x40},{'BUS_HZ':500},
             {'CONFIG':0x000f0a0a},{'CONFIG':0x021f0a0a},{'CONFIG':0x020f0b0a},
             {'EVIDENCE':0xe9060004},{'EVIDENCE':0xe9050004},{'EVIDENCE':0xe9030004},
             {'EVIDENCE':0xe9070000},{'EVIDENCE':0xe9070404},{'EVIDENCE':0xe9070084},
             {'EVIDENCE':0x00070004},{'EVIDENCE':0xe9078004}]
        for change in bad:
            r,s=self.report([imu_frame(1),imu_frame(2,**change)])
            self.assertEqual(s['IMU_SAMPLES'],'FAIL',change);self.assertIsNone(r['measurements'][-1]['imu']['nominal_units'])
    def test_burst_time_order_and_duration_checked(self):
        for change in ({'READ_START_MS':0},{'READ_MS':0},{'READ_FINISHED_MS':0},
                       {'READ_START_MS':3310,'READ_MS':3311,'READ_FINISHED_MS':3320}):
            _,s=self.report([imu_frame(1),imu_frame(2,**change)]);self.assertEqual(s['IMU_SAMPLES'],'FAIL',change)
    def test_sensor_failure_is_kept_after_a_later_valid_sample(self):
        r,s=self.report([imu_frame(1,SAMPLE_STATUS=3,SAMPLE_ERROR=8,ERROR_HISTORY=256),imu_frame(2,ERROR_HISTORY=256)])
        self.assertEqual(s['IMU_SAMPLES'],'FAIL');self.assertEqual(s['IMU_ERROR_HISTORY'],'INCONCLUSIVE')
        self.assertEqual(r['measurements'][0]['imu']['error'],8)
    def test_history_cannot_clear_inside_one_capture(self):
        _,s=self.report([imu_frame(1,ERROR_HISTORY=256),imu_frame(2)])
        self.assertEqual(s['IMU_ERROR_HISTORY'],'FAIL')
    def test_old_record_or_heartbeat_without_acquisition_does_not_pass(self):
        _,s=self.report([imu_frame(1),imu_frame(1)]);self.assertEqual(s['IMU_SAMPLES'],'INCONCLUSIVE')
        f=imu_frame(2);f[52]=1;checksum(f)
        _,s=self.report([imu_frame(1),f]);self.assertEqual(s['IMU_SAMPLES'],'INCONCLUSIVE')
    def test_signed_temperature_and_numeric_rails_retained(self):
        wire=struct.pack('>7h',-32768,32767,0,-32768,32767,-1,-128)
        r,s=self.report([imu_frame(1,raw=wire),imu_frame(2,raw=wire)])
        self.assertEqual(s['IMU_SAMPLES'],'PASS');self.assertEqual(s['IMU_RANGE_SCREEN'],'INCONCLUSIVE')
        d=r['measurements'][0]['imu'];self.assertEqual(d['nominal_units']['temperature_c'],24)
        self.assertEqual(d['raw_hex'],wire.hex());self.assertEqual(d['at_numeric_limit'],[0,1,3,4])
    def test_unknown_fields_and_padding_rejected_even_with_valid_crc(self):
        for pos,value in ((112,9),(113,999),(114,999),(120,0xe90f0004),(121,1),(121,1<<12),(125,0xffff0000)):
            f=imu_frame();f[pos]=value;checksum(f)
            with self.assertRaises(ValueError,msg=str(pos)):decode(f)
    def test_every_new_payload_bit_is_crc_protected(self):
        f=imu_frame()
        for i in range(112,127):
            for bit in range(32):
                changed=f.copy();changed[i]^=1<<bit
                with self.assertRaises(ValueError):decode(changed)
    def test_version_mismatch_stops_at_header(self):
        for expected,fr in ((PROTOCOL,imu_frame()),(UART_PROTOCOL,imu_frame()),(IMU_PROTOCOL,uart_frame())):
            reader=SyntheticMailbox([fr,fr]);reader.enable_mailbox()
            r=read_consistent(reader,attempts=1,pause=lambda _:None,protocol=expected)
            self.assertIsNone(r['accepted']);self.assertLessEqual(max(reader.words),3)
    def test_manifest_cannot_change_memory_grant_or_mode(self):
        _,_,m=evidence()
        for change in ('size','version','profile','mode'):
            x=copy.deepcopy(m)
            if change=='size':x['protocol']['bytes']=1024
            elif change=='version':x['protocol']['version']=5
            elif change=='profile':x['board_sha256']='00'*32
            else:x['build_options']['imu_samples']=False
            with self.assertRaises(ValueError):manifest_protocol(x)
    def test_report_jsonl_marks_synthetic_failure_and_raw_bytes(self):
        s,b,m=evidence([imu_frame(1),imu_frame(2,SAMPLE_STATUS=3,SAMPLE_ERROR=9,EVIDENCE=0xe9070404,ERROR_HISTORY=512)])
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'raw.json').write_text(json.dumps(s))
            self.assertEqual(report_file(p/'raw.json',p/'report',b,m),2)
            rows=[json.loads(x) for x in (p/'report/measurements.jsonl').read_text().splitlines()]
            self.assertTrue(all(r['origin']=='SYNTHETIC_FIXTURE' for r in rows))
            self.assertEqual(rows[1]['imu']['error'],9);self.assertIsNone(rows[1]['imu']['nominal_units'])

if __name__=='__main__':unittest.main()
