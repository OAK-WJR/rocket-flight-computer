"""SYNTHETIC evidence: end-to-end measurement decoding and fault retention."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from .test_mailbox import frame,checksum,evidence,SyntheticMailbox
from .mailbox import W,PROTOCOL,analyze_mailbox,capture_mailbox,report_file,prom_crc4
from .acquisition import pressure_reference


def measured(h=1,**changes):
    w=frame(h)
    w[35:43]=[0,40127,36924,23317,23282,33464,28312,0]
    w[42]=prom_crc4(w[35:43]);w[43]=w[44]=w[42]
    values=dict(ACQ_COUNTER=h,ACQ_START_MS=w[5]-700,ACQ_FINISHED_MS=w[5]-50,
                ADC_STATUS=2,ADC_VALID_MASK=7,ADC_CAL_RAW=24458,ADC_REF_RAW=24458,
                ADC_VLOGIC_RAW=10000,ADC_3V3_RAW=32768,VDDA_MV=3300,VLOGIC_MV=5539,V3V3_MV=3300,
                ADC_SAMPLE_MS=w[5]-680,SYSCFG_PMCR=0x0c000000,ADC_PCSEL=0x80003,
                BARO_SAMPLE_STATUS=2,BARO_VALID_MASK=3,BARO_D1=9085466,BARO_D2=8569150,
                PRESSURE_PA=100009,TEMP_CENTIC=2007,BARO_D1_MS=w[5]-450,BARO_D2_MS=w[5]-100)
    values.update(changes)
    for name,v in values.items():w[W[name]]=v
    return checksum(w)


class AcquisitionTests(unittest.TestCase):
    def report(self,frames=None):return analyze_mailbox(*evidence(frames or [measured(1),measured(2)]))
    def statuses(self,frames=None):return {r['id']:r['status'] for r in self.report(frames)['checks']}
    def test_reference_vector_and_nominal_capture(self):
        p,t=pressure_reference([0,40127,36924,23317,23282,33464,28312,0],9085466,8569150)
        self.assertAlmostEqual(p,100009.0702,places=3);self.assertAlmostEqual(t,2007.9854,places=3)
        s=self.statuses()
        for key in ('SAMPLE_FRESHNESS','ADC_MEASUREMENTS','BARO_MEASUREMENTS'):self.assertEqual(s[key],'PASS')
        r=self.report();self.assertEqual(r['overall'],'INCOMPLETE');self.assertTrue(r['synthetic'])
        self.assertFalse(r['hardware_qualified']);self.assertFalse(r['fabrication_release'])
    def test_wrong_reference_resolution_and_scaled_voltage_fail(self):
        for bad in ({'ADC_CAL_RAW':1529},{'ADC_REF_RAW':0},{'VDDA_MV':52800},
                    {'VLOGIC_MV':550},{'SYSCFG_PMCR':0},{'ADC_PCSEL':3},{'ADC_ERROR':6},{'ADC_HAL_ERROR':55}):
            self.assertEqual(self.statuses([measured(1),measured(2,**bad)])['ADC_MEASUREMENTS'],'FAIL')
    def test_heartbeat_alone_does_not_make_stale_samples_fresh(self):
        s=self.statuses([measured(1),measured(2,ACQ_COUNTER=1)])
        self.assertEqual(s['SAMPLE_FRESHNESS'],'INCONCLUSIVE');self.assertEqual(s['ADC_MEASUREMENTS'],'INCONCLUSIVE')
    def test_timestamps_outside_cycle_are_not_accepted(self):
        for key,result in [('ADC_SAMPLE_MS','ADC_MEASUREMENTS'),('BARO_D2_MS','BARO_MEASUREMENTS')]:
            self.assertEqual(self.statuses([measured(1),measured(2,**{key:0})])[result],'FAIL')
    def test_partial_conversion_never_presents_a_new_valid_zero(self):
        r=self.report([measured(1),measured(2,ADC_STATUS=3,ADC_ERROR=6,ADC_VALID_MASK=1,ADC_3V3_RAW=0,V3V3_MV=0)])
        self.assertEqual(next(c['status'] for c in r['checks'] if c['id']=='ADC_MEASUREMENTS'),'FAIL')
        self.assertEqual(r['measurements'][-1]['adc']['valid_mask'],1)
    def test_wrong_baro_result_is_checked_against_raw(self):
        for bad in ({'PRESSURE_PA':1000},{'TEMP_CENTIC':0},{'BARO_D1':0},{'BARO_D2':0xffffff},
                    {'BARO_VALID_MASK':1},{'BARO_SAMPLE_ERROR':3}):
            self.assertEqual(self.statuses([measured(1),measured(2,**bad)])['BARO_MEASUREMENTS'],'FAIL')
    def test_earlier_failure_cannot_disappear_after_recovery(self):
        r=self.report([measured(1,BARO_SAMPLE_STATUS=3,BARO_SAMPLE_ERROR=3),measured(2)])
        self.assertEqual(r['overall'],'ISSUES_FOUND')
        self.assertEqual(next(c['status'] for c in r['checks'] if c['id']=='BARO_MEASUREMENTS'),'FAIL')
    def test_longer_capture_retains_all_records_and_jsonl_origin(self):
        _,binding,manifest=evidence()
        with tempfile.TemporaryDirectory() as t:
            t=Path(t);raw=t/'raw.json'
            s=capture_mailbox(SyntheticMailbox([measured(i) for i in range(1,5)]),binding,manifest,
                              'SYNTHETIC-NOT-HARDWARE',raw,origin='SYNTHETIC_FIXTURE',pause=lambda _:None,sample_count=4)
            report_file(raw,t/'report',binding,manifest)
            log=[json.loads(x) for x in (t/'report/measurements.jsonl').read_text().splitlines()]
            self.assertEqual(len(log),4);self.assertEqual([x['counter'] for x in log],[1,2,3,4])
            self.assertTrue(all(x['origin']=='SYNTHETIC_FIXTURE' for x in log))
            self.assertEqual(s['state'],'CAPTURED')
    def test_cold_signed_temperature(self):
        w=measured(1); p,t=pressure_reference(w[35:43],9085466,7500000)
        # Host independently verifies signed temperature decoding at a cold point.
        w[W['BARO_D2']]=7500000;w[W['TEMP_CENTIC']]=int(t)&0xffffffff;w[W['PRESSURE_PA']]=int(p)
        checksum(w)
        self.assertEqual(self.statuses([w,measured(2)])['BARO_MEASUREMENTS'],'PASS')
    def test_legacy_abi_rejected_instead_of_misinterpreted(self):
        from .mailbox import decode,read_consistent
        w=measured(1);w[1]=1;w[2]=256;checksum(w)
        with self.assertRaises(ValueError):decode(w)
        r=SyntheticMailbox([w,w]);r.enable_mailbox()
        self.assertIsNone(read_consistent(r,attempts=1,pause=lambda _:None)['accepted'])
        self.assertLessEqual(max(r.words),3)
    def test_sample_timestamp_wrap_is_supported(self):
        from .acquisition import within_cycle
        self.assertTrue(within_cycle(0x10,0xffffff00,0x80))
        self.assertFalse(within_cycle(0xfffff000,0xffffff00,0x80))


if __name__=='__main__':unittest.main()
