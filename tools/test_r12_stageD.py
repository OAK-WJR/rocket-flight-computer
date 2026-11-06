#!/usr/bin/env python3
"""Self-tests for R12's stage D analysis wrappers (tools/r12_hotplug.py, m3_design/r12_stageD.py's pure functions).

usage: python3 -I tools/test_r12_stageD.py      (no pcbnew, no numpy)
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'm3_design'))
DESIGN = ROOT / 'm3_design/r12/design'


class HotplugWrapper(unittest.TestCase):
    def setUp(self):
        import r12_hotplug
        r12_hotplug.install()
        self.h = r12_hotplug
        self.inputs = json.loads((DESIGN / 'hotplug_inputs_r12.json').read_text())

    def test_parts_are_r12s(self):
        self.assertEqual(self.h.component_issues(self.inputs), [])

    def test_other_u9_or_tvs_fails(self):
        bad = json.loads(json.dumps(self.inputs))
        bad['parts']['U9']['fields']['Manufacturer Part'] = 'TPS259470LRPWR'
        self.assertIn('U9 is not an R12 part (TPS259470ARPWR)', self.h.component_issues(bad))
        bad = json.loads(json.dumps(self.inputs))
        bad['parts']['D8']['fields']['Manufacturer Part'] = 'SMBJ12CA'
        self.assertIn('unsupported model component or net role: D8', self.h.component_issues(bad))

    def test_results_bound_to_inputs(self):
        res = json.loads((DESIGN / 'hotplug_results_r12.json').read_text())
        self.assertEqual(res['inputs_sha256'], self.h.base.digest(self.inputs))
        self.assertEqual(res['model_sha256'], self.h.model_sha())
        self.assertEqual(len(res['rows']), 2304)


class StageDFigures(unittest.TestCase):
    def test_budget_record(self):
        d = json.loads((DESIGN / 'stageD_budget.json').read_text())
        f = d['fire']
        self.assertAlmostEqual(f['total_loop_ohm'], f['fire_branch_without_pack_ohm'] + 0.15, places=9)
        self.assertEqual(sorted(d['fire_copper']), ['ACT_FET_S', 'BAT_IN', 'PYRO1_IGN', 'PYRO1_OUT', 'RAW_ACT'])
        self.assertTrue(all(c['layers'] == ['F.Cu'] for c in d['fire_copper'].values()))
        self.assertGreaterEqual(f['gnd_return_used_ohm'], 0.005)

    def test_vgs_12V_bound_uses_largest_ratio(self):
        """D-R12-91 (R12F1-TRI-19): 12 / (51k / 60.8k) + 0.1 = 14.41 V, not the smallest ratio's 14.60 V."""
        g = json.loads((DESIGN / 'stageD_budget.json').read_text())['fire']['gate']
        lo, hi = g['q120_vgs_ratio_min_max']
        self.assertAlmostEqual(hi, 51e3 / 60.8e3, places=9)
        self.assertAlmostEqual(lo, 49e3 / 59.2e3, places=9)
        self.assertAlmostEqual(g['q120_vgs_exceeds_12V_above_pack_V'], 12 / hi + .1, places=9)
        self.assertAlmostEqual(g['q120_vgs_exceeds_12V_above_pack_V'], 14.406, places=2)

    def test_vgs_during_fire_from_act_fet_s(self):
        """R12F2-TRI-08: the gate divider hangs on ACT_FET_S = BAT_IN - I_fire x RDS(Q120 hot), not on BAT_IN."""
        f = json.loads((DESIGN / 'stageD_budget.json').read_text())['fire']
        g, lo = f['gate'], f['gate']['q120_vgs_ratio_min_max'][0]
        four = g['q120_q121_vgs_four_stall_fire']
        self.assertAlmostEqual(four['BAT_IN_V'], f['four_stall_BAT_IN_V'], places=9)
        self.assertAlmostEqual(four['fire_A'], f['four_stall_A'], places=9)
        self.assertAlmostEqual(four['Q120_drop_V'], f['four_stall_A'] * f['pfet_hot_ohm'], places=9)
        want = -(f['four_stall_BAT_IN_V'] - f['four_stall_A'] * f['pfet_hot_ohm'] - .1) * lo
        self.assertAlmostEqual(four['vgs_V'], want, places=9)
        self.assertAlmostEqual(four['vgs_V'], -4.576, places=3)
        self.assertNotIn('q120_q121_vgs_V', g)          # the BAT_IN-based figure (-4.652 V) is gone

    def test_u400_in_excludes_en_stub(self):
        """R12F2-TRI-06: U400.5 (EN, tied to VIN) carries no load current; U400 IN starts at VIN (pin 3) only."""
        d = json.loads((DESIGN / 'stageD_budget.json').read_text())
        r = d['rails']['U400 IN']
        self.assertNotIn('U400.5', r['pads'])
        self.assertIn('U400.3', r['pads'])
        self.assertNotIn('0.250', r['layers'].get('F.Cu', {}).get('by_width_mm', {}))
        self.assertEqual(d['dc_solves']['RAW_PROTECTED_U9_to_U400']['sink'], 'U400:3')

    def test_shared_raw_trunk_at_summed_current(self):
        """R12F2-TRI-07: the B.Cu trunk (45.2, 16.4) -> (45.2, 29.2) feeds both U400 and D5 and is rated at the sum."""
        d = json.loads((DESIGN / 'stageD_budget.json').read_text())
        rails = d['rails']
        trunk = [g for g in d['rails_shared']['groups'] if g['layer'] == 'B.Cu' and g['width_mm'] == 0.6]
        self.assertEqual(len(trunk), 1)
        g = trunk[0]
        self.assertEqual(g['paths'], ['D5 IN', 'U400 IN'])
        self.assertAlmostEqual(g['length_mm'], 12.8, places=3)
        self.assertAlmostEqual(g['design_A_sum'], rails['D5 IN']['amps'] + rails['U400 IN']['amps'], places=9)
        self.assertAlmostEqual(g['ipc_rise_design_sum_C'], 46.13, places=1)
        self.assertAlmostEqual(g['budget_A_sum'], rails['D5 IN']['budget_A'] + rails['U400 IN']['budget_A'], places=9)
        self.assertLess(g['ipc_rise_budget_C'], 5.0)
        self.assertTrue(any(o.get('shared_with') == g['paths'] and o['layer'] == 'B.Cu'
                            for o in rails['U400 IN']['over_30C']))


class Round3Fixes(unittest.TestCase):
    """R12 review round 3 (R12F3-TRI-06 / -09) in the stage D record and its pure functions."""

    def test_q124_vgs_from_voh_minimum(self):
        """R12F3-TRI-06: PE4's VOH is only guaranteed >= VDD - 0.4 V (DS12110 Rev 8 Table 158)."""
        g = json.loads((DESIGN / 'stageD_budget.json').read_text())['fire']['gate']
        b = g['q124_vgs_min_basis']
        self.assertEqual(b['voh_drop_V'], 0.4)
        want = (b['vdd_min_V'] - 0.4) * 9.9e3 / (9.9e3 + 222.2)
        self.assertAlmostEqual(g['q124_vgs_min_V'], want, places=9)
        self.assertAlmostEqual(g['q124_vgs_min_V'], 2.778, places=3)
        self.assertGreater(g['q124_vgs_min_V'], g['q124_vgs_row_V'])

    def test_pe4_load_includes_r127_and_stays_within_the_4_mA_row(self):
        """R12F4-TRI-02: PE4 (PYRO1_GATE_N) sources R127 1k as well as R126 220R + R128 10k."""
        import r12_stageD
        b = json.loads((DESIGN / 'stageD_budget.json').read_text())['fire']['gate']['q124_vgs_min_basis']
        vdd = b['vdd_min_V']
        self.assertAlmostEqual(b['pe4_load_mA'], (vdd / 1e3 + vdd / 10.22e3) * 1e3, places=9)
        self.assertAlmostEqual(b['pe4_load_mA'], 3.557, places=3)
        self.assertAlmostEqual(b['pe4_load_max_mA'], b['pe4_load_vdd_max_V'] / 983.3e-3 * (1 + 1 / 10.22), places=6)
        self.assertAlmostEqual(b['pe4_load_max_mA'], 3.868, places=3)
        self.assertLessEqual(b['pe4_load_max_mA'], b['voh_row_mA'])
        self.assertEqual(b['voh_row_mA'], 4.0)
        self.assertTrue(b['pe4_load_within_voh_row'])
        self.assertAlmostEqual(r12_stageD.pe4_load_mA(3.3), 3.3 + 3.3 / 10.22, places=12)

    def test_gate_overvoltage_note_covers_the_pad_dwell(self):
        """R12F4-TRI-03: the bus is on from the on-rail check until switch-off, not only in flight."""
        note = json.loads((DESIGN / 'r12_windows.json').read_text())['fire']['gate']['note']
        self.assertNotIn('only enabled in flight', note)
        self.assertIn('from the on-rail check until switch-off', note)
        self.assertIn('pad or flight', note)
        self.assertNotIn('0.32 mA', note)

    def test_pa6_branches_charged_at_their_shared_resistance(self):
        """R12F3-TRI-09: a branch's drop at D5 is its current times min(its own, D5's) resistance from U9."""
        import r12_stageD
        fire = dict(other_converter_load_W=10.0,
                    other_load_parts=dict(camera_W=6.0, ports_W=3.0, logic_W=0.5, microsd_write_W=0.3, d5_W=0.1,
                                          r92_W=0.1),
                    stalls={'4': dict(BAT_IN_V=5.0)},
                    shorted={'match_shorted_4_stalls': dict(BAT_IN_V=5.0),
                             'match_and_leads_shorted_4_stalls': dict(BAT_IN_V=5.0)})
        out = r12_stageD.pa6_corners(fire, 0.01, dict(D5=0.02, U400=0.05, U403=0.01))
        h = out['healthy']
        raw = (6.0 * 0.01 + 3.0 * 0.02 + 1.0 * 0.02) / 5.0
        self.assertAlmostEqual(h['RAW_PROTECTED_drop_at_D5_V'], raw, places=12)
        self.assertAlmostEqual(h['U9_and_copper_drop_V'], 2.0 * 0.05 + raw, places=12)
        self.assertAlmostEqual(h['lumped_drop_V_superseded'] - h['U9_and_copper_drop_V'], 6.0 / 5.0 * 0.01, places=12)

    def test_pa6_record_uses_branch_shares(self):
        d = json.loads((DESIGN / 'stageD_budget.json').read_text())
        p, s = d['pa6_corners'], d['dc_solves']
        self.assertAlmostEqual(p['branch_shared_ohm']['U403 (camera)'],
                               min(s['RAW_PROTECTED_U9_to_U403']['resistance_ohm'],
                                   s['RAW_PROTECTED_U9_to_D5']['resistance_ohm']), places=12)
        self.assertGreater(p['healthy']['lumped_drop_V_superseded'] - p['healthy']['U9_and_copper_drop_V'], 0.015)
        self.assertIn('upper bound', p['label'])

if __name__ == '__main__':
    unittest.main()
