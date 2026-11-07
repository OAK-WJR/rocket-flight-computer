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
        """R12F2-TRI-08: the gate divider hangs on ACT_FET_S = BAT_IN - I_fire x RDS(Q120 hot), not on BAT_IN.
        R12F5-TRI-03: and the fire current crosses the J1 -> Q120 BAT_IN copper first, while Q121's source sits a further
        I x the ACT_FET_S copper below the divider's tap at Q120's source (copper at 70 C)."""
        d = json.loads((DESIGN / 'stageD_budget.json').read_text())
        f = d['fire']
        g, lo = f['gate'], f['gate']['q120_vgs_ratio_min_max'][0]
        hot = 1 + .00393 * 50
        r_bat = d['fire_copper']['BAT_IN']['R_20C_ohm'] * hot
        r_fets = d['fire_copper']['ACT_FET_S']['R_20C_ohm'] * hot
        four = g['q120_q121_vgs_four_stall_fire']
        i = f['four_stall_A']
        self.assertAlmostEqual(four['BAT_IN_V'], f['four_stall_BAT_IN_V'], places=9)
        self.assertAlmostEqual(four['fire_A'], i, places=9)
        self.assertAlmostEqual(four['Q120_drop_V'], i * f['pfet_hot_ohm'], places=9)
        self.assertAlmostEqual(four['BAT_IN_copper_drop_V'], i * r_bat, places=9)
        self.assertAlmostEqual(four['ACT_FET_S_copper_drop_V'], i * r_fets, places=9)
        want = -(f['four_stall_BAT_IN_V'] - i * (r_bat + f['pfet_hot_ohm']) - .1) * lo
        self.assertAlmostEqual(four['vgs_Q120_V'], want, places=9)
        self.assertAlmostEqual(four['vgs_Q121_V'], want + i * r_fets, places=9)
        self.assertLess(four['vgs_Q120_V'], four['vgs_Q121_V'])
        self.assertLess(four['vgs_Q121_V'], -4.5)
        self.assertAlmostEqual(four['margin_to_minus_4V5_row_V']['Q121'], -four['vgs_Q121_V'] - 4.5, places=9)
        self.assertNotIn('vgs_V', four)                 # the single-node figure (-4.576 V) is gone
        self.assertNotIn('q120_q121_vgs_V', g)          # the BAT_IN-based figure (-4.652 V) is gone

    def test_u400_input_condition_and_headroom(self):
        """R12F5-TRI-02: the PORT_4V8 window holds only while U400 VIN >= VO / 0.75; the four-stall and 6.0 V-pack
        points are below it, and the estimate rests on the 200 kHz foldback (SLVSD90B 6.4.1)."""
        p = json.loads((DESIGN / 'stageD_budget.json').read_text())['port_supply']
        self.assertIn('VO / 0.75', p['window_holds_for'])
        u = p['u400_input']
        self.assertTrue(u['label'].startswith('Calculation / Inference'))
        for name in ('four_stall_fire', '6V0_pack_converters_only'):
            c = u[name]
            self.assertTrue(c['below_VO_over_0V75'])
            self.assertAlmostEqual(c['VIN_V'], round(c['BAT_IN_V'] - c['drop_to_U400_VIN_V'], 4), places=4)
            self.assertFalse(c['holds_window_top_at_580kHz'])
            self.assertTrue(c['holds_window_top_with_foldback'])
            self.assertAlmostEqual(c['dmax']['200kHz_tOFF_max_310ns'], 1 - 310e-9 * 200e3, places=4)

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
        # R12F5-TRI-05: R126 / R128 at the drift ends (+/-1.67 %), as the 3V3 drift minimum
        td = 0.01 + 100e-6 * 67
        self.assertAlmostEqual(b['resistor_tolerance'], td, places=12)
        want = (b['vdd_min_V'] - 0.4) * 10e3 * (1 - td) / (10e3 * (1 - td) + 220 * (1 + td))
        self.assertAlmostEqual(g['q124_vgs_min_V'], want, places=9)
        self.assertAlmostEqual(g['q124_vgs_min_V'], 2.777, places=3)
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


class Round5Windows(unittest.TestCase):
    """R12 review round 5 (R12F5-TRI-02, -04, -05, -16, -17) in r12_windows.json (stage A, no board)."""

    @classmethod
    def setUpClass(cls):
        cls.w = json.loads((DESIGN / 'r12_windows.json').read_text())

    def test_pd10_leakage_is_ft_xx(self):
        """R12F5-TRI-16: PD10 is FT_h, an FT_xx pin: +/-250 nA (DS12110 Rev 8 Table 60); +/-350 nA is FT_u only."""
        d = self.w['sense']['PORT_SENSE_divider']
        self.assertEqual(d['pd10_leak_A'], 250e-9)
        self.assertAlmostEqual(d['low_when_off_V'], round(250e-9 * 100e3 * (1 + 0.01 + 100e-6 * 67), 3), places=6)

    def test_port_sense_thresholds_from_the_3v3_window(self):
        """R12F5-TRI-17: VIH 0.7 x the 3V3 maximum and the VDD + 0.3 ceiling at its minimum, per resistor case."""
        s, v33 = self.w['sense'], self.w['rails']['3V3 (U2 LMR50410, R14 47k / R15 20k)']
        for case in ('initial', 'drift'):
            t = s['PORT_SENSE_thresholds'][case]
            self.assertAlmostEqual(t['vih_V'], round(0.7 * v33[case]['max_V'], 4), places=9)
            self.assertAlmostEqual(t['ceiling_V'], round(v33[case]['min_V'] + 0.3, 4), places=9)
            self.assertGreater(s[case]['PORT_SENSE_V'][0], t['vih_V'])
            self.assertLess(s[case]['PORT_SENSE_V'][1], t['ceiling_V'])
        self.assertAlmostEqual(s['PORT_SENSE_thresholds']['drift']['vih_V'], 2.4249, places=4)
        self.assertNotIn('3.43 V', s['PORT_SENSE_limits'])
        self.assertTrue(s['PORT_SENSE_ok'])

    def test_q120_generator_figures_on_the_act_fet_s_basis(self):
        """R12F5-TRI-04: no -0.833 x V_BAT figures; the -4.5 V row holds down to about 5.54 V (bus on) / 5.63 V (fire)."""
        g = self.w['fire']['gate']
        self.assertNotIn('5.72V_four_stall', g['q120_q121_vgs_V'])
        self.assertNotIn('5.4 V pack', g['q120_rds_row'])
        self.assertNotIn('-V_BAT x', g['note'])
        lo = 49e3 / 59.2e3
        self.assertAlmostEqual(g['q120_vgs_4V5_min_bat_V']['bus_on'], round(4.5 / lo + .1, 3), places=9)
        self.assertAlmostEqual(g['q120_q121_vgs_V']['8.4V_bus_on'], round(-(8.4 - .1) * lo, 3), places=9)
        self.assertLess(g['q120_q121_vgs_V']['four_stall_fire'], -4.5)

    def test_q124_stage_a_bound_at_drift_ends(self):
        """R12F5-TRI-05: the stage A placeholder uses the 3V3 drift minimum and the drift resistor ends."""
        self.assertAlmostEqual(self.w['fire']['gate']['q124_vgs_min_V'], 2.777, places=3)

    def test_port_input_condition(self):
        """R12F5-TRI-02: PORT_4V8's window is conditioned on U400 VIN >= VO / 0.75, as D-R12-87 does for U403."""
        u, rail = self.w['port_input'], self.w['rails']['PORT_4V8 (U400 TPS563208, R400 47k + R404 5.1k / R401 10k 0.1 %)']
        self.assertIn('VO / 0.75', u['window_holds_for'])
        self.assertIn('VO / 0.75', rail['limits_basis'])
        for case in ('initial', 'drift'):
            lo, hi = u['min_recommended_VIN_V'][case]
            self.assertAlmostEqual(lo, round(rail[case]['min_V'] / .75, 3), places=9)
            self.assertAlmostEqual(hi, round(rail[case]['max_V'] / .75, 3), places=9)
        for name in ('four_stall_fire', '6V0_pack_converters_only'):
            self.assertLess(u[name]['VIN_V'], u['min_recommended_VIN_V']['drift'][0])
            self.assertTrue(u[name]['holds_window_top_with_foldback'])


if __name__ == '__main__':
    unittest.main()
