"""Fault-localization, provenance and absent-device tests for the bench entry."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from . import triage as t
from .test_assembly import frame
from .test_usb import Serial, crc
from .triage_map import read_board, TEST_POINTS
from .usb import capture


class TriageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx=t.context()

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.out=Path(self.tmp.name)

    def evidence(self, frames=None, fail_at=None, factory=None, origin='SYNTHETIC_FIXTURE'):
        s=Serial(frames or [frame(1),frame(2)]);s.fail_at=fail_at
        e=capture(factory or s.client,self.ctx['manifest'],'SCRIPTED-001',self.out/'capture.json',
                  pause=lambda _:None,origin=origin)
        return e,s

    def bench(self,e,values):
        b=t.bench_template(e,self.ctx);b['same_supply_configuration']=True
        b['supply_configuration']='SYNTHETIC stable USB-only demonstration'
        for p in b['points']:
            if p['net'] in values:
                p['measurement']=dict(value=values[p['net']],unit='V',uncertainty_v=.01,
                    input_ohm=10000000,instrument='SYNTHETIC-METER',measured_at=e['finished_at'])
        return b

    def report(self,e,b=None):
        return t.write_report(e,self.ctx,self.out,b)

    def test_board_counts_rotations_and_ground_refs(self):
        m=self.ctx['mapping'];self.assertEqual(len(m['points']),30)
        self.assertEqual(sum(p['dedicated_testpad'] for p in m['points'].values()),20)
        # Independently recorded native KiCad pad positions, not generated expectations.
        for name,xy in {'J2.5':[41.81,126.5],'C28.1':[9.5,123.9],'R63.1':[19.47,99.2],
                        'TP75.1':[18.,51.46],'TP92.1':[18.,128.5]}.items():
            self.assertEqual(m['points'][name]['xy_mm'],xy)
        for p in m['points'].values():
            self.assertEqual(m['points'][p['ground']]['net'],'GND')

    def test_net_mutation_rejected_even_with_rehashed_file(self):
        board=t.DEFAULT_BOARD.read_text()
        old='(property "Reference" "TP80"'
        pos=board.index(old);start=board.rfind('(footprint',0,pos);end=board.find('\n\t(footprint',pos)
        block=board[start:end];self.assertIn('"BAT_IN"',block)
        modified=board[:start]+block.replace('"BAT_IN"','"GND"')+board[end:]
        path=self.out/'bad.kicad_pcb';path.write_text(modified)
        with self.assertRaisesRegex(ValueError,'net mismatch'):
            read_board(path,hashlib.sha256(path.read_bytes()).hexdigest())

    def test_wrong_board_is_rejected_before_opening_serial(self):
        bad=self.out/'bad.kicad_pcb';bad.write_text('not the reviewed board')
        calls=[]
        with self.assertRaises(ValueError):
            t.capture_report(lambda:calls.append(True),'A',self.out/'run',board=bad)
        self.assertEqual(calls,[]);self.assertFalse((self.out/'run').exists())

    def test_modified_binary_is_rejected_before_opening_serial(self):
        m=self.out/'manifest.json';m.write_bytes(t.DEFAULT_MANIFEST.read_bytes())
        (self.out/'m3_bench.bin').write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError,'artifact changed'):
            t.context(m)

    def test_stale_binding_coordinates_are_rejected(self):
        original=t.document
        def stale(path):
            value=original(path)
            if Path(path).name=='binding.json':value['probes']['3V3']['board_xy_mm'][0]+=.5
            return value
        with patch.object(t,'document',side_effect=stale),self.assertRaisesRegex(ValueError,'Stale measurement'):
            t.context()

    def test_successful_capture_is_not_whole_board_pass(self):
        e,s=self.evidence();r=self.report(e)
        self.assertTrue(s.closed);self.assertEqual(s.requests,[(1,0,1024)]*2)
        self.assertTrue(r['complete_live_capture']);self.assertEqual(r['exit_code'],0)
        self.assertEqual(r['overall'],'INCOMPLETE');self.assertFalse(r['hardware_qualified'])
        self.assertFalse(r['full_m3_complete']);self.assertIsNone(r['unique_failed_component'])
        self.assertTrue(r['synthetic']);self.assertIn('Synthetic demo',(self.out/'report.html').read_text())
        b=t.document(self.out/'bench_template.json')
        self.assertTrue(all(p['measurement'] is None for p in b['points']))
        self.assertIsNone(b['same_supply_configuration'])

    def test_absent_device_has_no_measurements_or_pass(self):
        def absent():raise OSError('No serial device')
        e,_=self.evidence(factory=absent,origin='USB_CAPTURE');r=self.report(e)
        self.assertEqual(r['capture_state'],'CONNECTION_FAILED');self.assertEqual(r['exit_code'],3)
        self.assertEqual(r['measurements'],[]);self.assertEqual(e['exchanges'],[])
        self.assertFalse(any(c['status']=='PASS' for c in r['checks']))
        self.assertEqual([g['id'] for g in r['investigations']],['usb_power','source_mux','logic_3v3','clock_reset','usb_data'])
        self.assertNotIn('imu',[g['id'] for g in r['investigations']])

    def test_partial_capture_preserves_bytes_and_cannot_pass(self):
        e,s=self.evidence(fail_at=2);r=self.report(e)
        self.assertEqual(r['capture_state'],'PARTIAL');self.assertEqual(r['exit_code'],3)
        self.assertEqual(e['exchanges'][-1]['rx_hex'],b'M3RS'.hex());self.assertTrue(s.closed)
        self.assertFalse(any(c['status']=='PASS' for c in r['checks']))

    def test_recovered_usb_fault_is_still_a_branch_investigation(self):
        a,b=frame(1),frame(2);b[153]|=8;b[155]|=64;b[158]=1
        e,_=self.evidence([a,crc(b)]);r=self.report(e)
        self.assertEqual(r['exit_code'],2)
        self.assertIn('usb_power',[g['id'] for g in r['investigations']])
        self.assertEqual(next(c['status'] for c in r['checks'] if c['id']=='POWER_FAULT_HISTORY'),'FAIL')

    def test_sensor_collapse_orders_supply_before_sensor(self):
        a,b=frame(1),frame(2);b[31]=3;b[32]=0
        e,_=self.evidence([a,crc(b)])
        report=self.report(e,self.bench(e,{'VBUS':5.,'VLOGIC':4.9,'3V3':3.3,'3V3A':.1}))
        groups=[g['id'] for g in report['investigations']]
        self.assertLess(groups.index('sensor_power'),groups.index('imu'))
        self.assertIn('L2',next(c['next_step'] for c in report['checks'] if c['id']=='POWER_PATH'))

    def test_current_revision_usb_collapse_names_u10_u11_not_removed_diode(self):
        e,_=self.evidence();r=self.report(e,self.bench(e,{'VBUS':5.,'VLOGIC':.1,'3V3':.1,'3V3A':.1}))
        step=next(c['next_step'] for c in r['checks'] if c['id']=='POWER_PATH')
        self.assertIn('U10',step);self.assertIn('U11',step);self.assertNotIn('not recognised',step)

    def test_uncertainty_crossing_screen_is_inconclusive(self):
        e,_=self.evidence();b=self.bench(e,{'3V3':3.14});r=self.report(e,b)
        self.assertEqual(next(c['status'] for c in r['checks'] if c['id']=='DC_3V3'),'INCONCLUSIVE')

    def test_mixed_revision_session_origin_and_duplicate_points_rejected(self):
        e,_=self.evidence();original=self.bench(e,{'3V3':3.3})
        for key,value in [('board_sha256','0'*64),('capture_id','other'),('assembly_id','other'),('origin','MANUAL_BENCH')]:
            b=copy.deepcopy(original);b[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):t.bench_checks(b,e,self.ctx)
        b=copy.deepcopy(original);b['points'].append(copy.deepcopy(b['points'][0]))
        with self.assertRaises(ValueError):t.bench_checks(b,e,self.ctx)

    def test_changed_ground_position_or_frame_rejected(self):
        e,_=self.evidence();original=self.bench(e,{'3V3':3.3})
        for key,value in [('ground','TP80.1'),('ground_xy_mm',[8.5,8.5]),('board_xy_mm',[0,0])]:
            b=copy.deepcopy(original);b['points'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):t.bench_checks(b,e,self.ctx)
        original['coordinate_frame']='BOTTOM mirror'
        with self.assertRaises(ValueError):t.bench_checks(original,e,self.ctx)

    def test_unconfirmed_supply_configuration_never_compares_rails(self):
        e,_=self.evidence();b=self.bench(e,{'3V3':3.3});b['same_supply_configuration']=None
        with self.assertRaisesRegex(ValueError,'supply configuration'):t.bench_checks(b,e,self.ctx)

    def test_wrong_firmware_words_or_wire_crc_rejected(self):
        e,_=self.evidence();bad=copy.deepcopy(e);bad['samples'][0]['attempts'][0]['words'][16]^=1
        with self.assertRaisesRegex(ValueError,'disagree'):t.validate_capture(bad)
        bad=copy.deepcopy(e);rx=bytearray.fromhex(bad['exchanges'][0]['rx_hex']);rx[-1]^=1;bad['exchanges'][0]['rx_hex']=rx.hex()
        with self.assertRaisesRegex(ValueError,'CRC'):t.validate_capture(bad)

    def test_stale_data_unknown_state_and_fake_completed_capture(self):
        e,_=self.evidence([frame(1),frame(1)]);r=self.report(e)
        self.assertFalse(r['complete_live_capture']);self.assertEqual(r['exit_code'],3)
        for state in ('PASS','STARTED'):
            bad=copy.deepcopy(e);bad['state']=state
            with self.assertRaises(ValueError):t.validate_capture(bad)
        e['samples'].pop()
        with self.assertRaises(ValueError):t.validate_capture(e)

    def test_html_escapes_ids_and_errors_and_uses_local_links(self):
        def absent():raise OSError('<img src=x onerror=alert(1)>')
        e,_=self.evidence(factory=absent);e['assembly_id']='<script>alert(1)</script>'
        (self.out/'capture.json').write_text(json.dumps(e))
        self.report(e);html=(self.out/'report.html').read_text()
        self.assertNotIn('<script>',html);self.assertNotIn('<img src=x',html)
        self.assertIn('&lt;script&gt;',html);self.assertIn('Content-Security-Policy',html)
        self.assertIn('id="point-TP80-1"',html);self.assertIn('href="#point-TP80-1"',html)

    def test_existing_output_not_overwritten(self):
        out=self.out/'existing';out.mkdir();(out/'marker').write_text('keep')
        calls=[]
        with self.assertRaises(FileExistsError):t.capture_report(lambda:calls.append(True),'A',out)
        self.assertEqual(calls,[]);self.assertEqual((out/'marker').read_text(),'keep')

    def test_offline_preserves_exact_source_bytes_and_bench(self):
        e,_=self.evidence();b=self.bench(e,{'3V3':3.3});bench=self.out/'meter.json'
        bench.write_text(json.dumps(b));out=self.out/'offline'
        r=t.offline_report(self.out/'capture.json',out,bench=bench)
        self.assertEqual((out/'capture.json').read_bytes(),(self.out/'capture.json').read_bytes())
        self.assertEqual((out/'bench_input.json').read_bytes(),bench.read_bytes())
        self.assertEqual(r['sources']['capture_sha256'],t.sha(out/'capture.json'))

    def test_duplicate_json_keys_and_nonfinite_values_rejected(self):
        path=self.out/'bad.json'
        for data in ('{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}'):
            path.write_text(data)
            with self.subTest(data=data),self.assertRaises(ValueError):t.document(path)


if __name__=='__main__':unittest.main()
