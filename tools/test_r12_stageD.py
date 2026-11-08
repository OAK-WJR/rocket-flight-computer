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
        self.assertAlmostEqual(g['q124_vgs_min_V'], 2.761, places=3)      # R12F6-TRI-03: 3V3 drift minimum 3.2237 V
        self.assertGreater(g['q124_vgs_min_V'], g['q124_vgs_row_V'])

    def test_pe4_load_includes_r127_and_stays_within_the_4_mA_row(self):
        """R12F4-TRI-02: PE4 (PYRO1_GATE_N) sources R127 1k as well as R126 220R + R128 10k."""
        import r12_stageD
        b = json.loads((DESIGN / 'stageD_budget.json').read_text())['fire']['gate']['q124_vgs_min_basis']
        vdd = b['vdd_min_V']
        self.assertAlmostEqual(b['pe4_load_mA'], (vdd / 1e3 + vdd / 10.22e3) * 1e3, places=9)
        self.assertAlmostEqual(b['pe4_load_mA'], 3.539, places=3)         # R12F6-TRI-03 (was 3.557 mA)
        self.assertAlmostEqual(b['pe4_load_max_mA'], b['pe4_load_vdd_max_V'] / 983.3e-3 * (1 + 1 / 10.22), places=6)
        self.assertAlmostEqual(b['pe4_load_max_mA'], 3.925, places=3)     # R12F6-TRI-03 (was 3.868 mA)
        self.assertIn(f"{b['pe4_load_max_mA']:.2f} mA", b['label'])
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
        k = 1 + 0.00393 * 50                                    # copper at 70 C (R12F9-TRI-04)
        raw = (6.0 * 0.01 + 3.0 * 0.02 + 1.0 * 0.02) / 5.0 * k
        self.assertAlmostEqual(h['RAW_PROTECTED_drop_at_D5_V'], raw, places=12)
        self.assertAlmostEqual(h['U9_and_copper_drop_V'], 2.0 * (0.045 + 0.01 * k) + raw, places=12)   # U9 RON 45 mOhm (R12F8-TRI-07)
        self.assertAlmostEqual(h['lumped_drop_V_superseded'] - h['U9_and_copper_drop_V'], 6.0 / 5.0 * 0.01 * k, places=12)

    def test_pa6_record_uses_branch_shares(self):
        d = json.loads((DESIGN / 'stageD_budget.json').read_text())
        p, s = d['pa6_corners'], d['dc_solves']
        self.assertAlmostEqual(p['branch_shared_ohm']['U403 (camera)'],
                               min(s['RAW_PROTECTED_U9_to_U403']['resistance_ohm'],
                                   s['RAW_PROTECTED_U9_to_D5']['resistance_ohm']) * p['copper_factor_70C'], places=12)
        # R12F8 (lane A review of lane P's 0.015 -> 0.010): the gap between the lumped and branch-share drops is not a
        # design margin but an identity of the two models, so check it exactly: the camera and port branches save
        # their power / BAT_IN x (R(U9 -> D5) - their shared resistance); positive whenever a branch sits nearer U9
        h, r_d5 = p['healthy'], p['raw_point_ohm']['D5']
        f = d['fire']['other_load_parts']
        want = sum(f[k] / h['BAT_IN_V'] * (r_d5 - p['branch_shared_ohm'][n])
                   for k, n in (('camera_W', 'U403 (camera)'), ('ports_W', 'U400 (ports)')))
        self.assertAlmostEqual(h['lumped_drop_V_superseded'] - h['U9_and_copper_drop_V'], want, places=12)
        self.assertGreater(want, 0.0)
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
        self.assertAlmostEqual(s['PORT_SENSE_thresholds']['drift']['vih_V'], 2.4609, places=4)   # R12F6-TRI-03
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
        self.assertAlmostEqual(self.w['fire']['gate']['q124_vgs_min_V'], 2.761, places=3)

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



class Round6Windows(unittest.TestCase):
    """R12 review round 6 (R12F6-TRI-03 3V3 PFM band; R12F6-TRI-01 cold screen at 10.2 kohm) in r12_windows.json and
    stageD_budget.json."""

    @classmethod
    def setUpClass(cls):
        cls.w = json.loads((DESIGN / 'r12_windows.json').read_text())
        cls.d = json.loads((DESIGN / 'stageD_budget.json').read_text())

    def test_3v3_window_is_the_pfm_band(self):
        """U2 LMR50410XDBVR (PFM): SLUSDW3A section 7.8 -1.5 / +2.5 % about 1.000 V, then the 1 % divider."""
        r = self.w['rails']['3V3 (U2 LMR50410, R14 47k / R15 20k)']
        self.assertEqual(r['pfm_regulation_band'], [-0.015, 0.025])
        self.assertIn('section 7.8', r['source'])
        self.assertIn('Inference', r['label'])
        for case, tol, lo, hi in (('initial', .01, 3.2539, 3.4824), ('drift', .01 + 100e-6 * 67, 3.2237, 3.5156)):
            self.assertAlmostEqual(r[case]['min_V'], round(.985 * (1 + 47 * (1 - tol) / (20 * (1 + tol))), 4), places=9)
            self.assertAlmostEqual(r[case]['max_V'], round(1.025 * (1 + 47 * (1 + tol) / (20 * (1 - tol))), 4), places=9)
            self.assertEqual((r[case]['min_V'], r[case]['max_V']), (lo, hi))
            self.assertTrue(r[case]['inside_limits'])
        self.assertLess(r['drift']['max_V'], 3.6)
        self.assertGreater(r['drift']['min_V'], 3.135)

    def test_stage_d_follows_the_window(self):
        u6, g = self.d['u6_supply'], self.d['fire']['gate']
        v33 = self.w['rails']['3V3 (U2 LMR50410, R14 47k / R15 20k)']
        self.assertAlmostEqual(u6['1A_rating_bound']['min_VCC_drift_V'],
                               v33['drift']['min_V'] - u6['1A_rating_bound']['drop_V'], places=9)
        self.assertGreater(u6['1A_rating_bound']['margin_drift_V'], 0.07)
        self.assertEqual(g['q124_vgs_min_basis']['vdd_min_V'], v33['drift']['min_V'])
        self.assertEqual(g['q124_vgs_min_basis']['pe4_load_vdd_max_V'], v33['drift']['max_V'])

    def test_cold_screen_topology_and_margins(self):
        c = self.w['cold_screen']
        self.assertIn('R136 5.1k', c['topology'])
        self.assertIn('Inference', c['label'])
        self.assertEqual(c['inputs']['vf_V'], [0.0, 0.4])
        for case in ('initial', 'drift'):
            m, k = c[case]['margins_mV'], c[case]['cases']
            self.assertEqual(c[case]['vdd_V'], [self.w['rails']['3V3 (U2 LMR50410, R14 47k / R15 20k)'][case][x]
                                                for x in ('min_V', 'max_V')])
            for key in ('open_PC0_above_healthy_mV', 'healthy_PC5_above_open_mV',
                        'R131_bridged_healthy_PC0_above_healthy_mV', 'R173_bridged_healthy_PC0_above_healthy_mV'):
                self.assertGreater(m[key], 5.0, (case, key))
            self.assertEqual(k['open']['PC5_mV'], [0.0, 0.0])
            self.assertEqual(k['R131_bridged_no_match']['PC5_mV'], [0.0, 0.0])
            self.assertEqual(k['R173_bridged_no_match']['PC5_mV'], [0.0, 0.0])
            self.assertLessEqual(m['shorted_vs_healthy_band_edges_mV'], 0.01)

    def test_cold_screen_nominal(self):
        """Lane P's check at 3.3 V / VF 0.25 V: open PC0 0.1425 V; the generator's nominal is 3.35 V."""
        import r12_budget
        n = self.w['cold_screen']['nominal_3V35_VF_0V25']
        self.assertAlmostEqual(n['open_PC0_mV'], (3.35 - .25) * 1e3 / 21.4, places=2)
        self.assertEqual(r12_budget.cold_screen(), self.w['cold_screen'])


class Round7(unittest.TestCase):
    """R12 review round 7: R12F7-TRI-17 (EN turn-on over C87's specified range) and the generator part of R12F7-TRI-02
    (figures resting on the 3V3 window labelled Calculation / Inference)."""
    LABEL = '3V3 window, D-R12-139'

    @classmethod
    def setUpClass(cls):
        cls.w = json.loads((DESIGN / 'r12_windows.json').read_text())
        cls.d = json.loads((DESIGN / 'stageD_budget.json').read_text())

    def test_en_turn_on_spans_r10_c87_range(self):
        """R10 D-R19-10: C87 0.72 x (-10 %, X7R -15 % and bias) ... 1.265 x (+10 % x +15 %); not 0.648 ... 1.10 x."""
        import r12_stageD
        on = self.d['en']['by_case']['initial']['turn_on']
        self.assertEqual(on['c87_factor'], [r12_stageD.C87_LOW, r12_stageD.C87_HIGH])
        self.assertAlmostEqual(r12_stageD.C87_LOW, 0.72, places=12)
        self.assertAlmostEqual(r12_stageD.C87_HIGH, 1.265, places=12)
        self.assertGreater(on['fastest_ms'], 30.0)
        self.assertLess(on['fastest_ms'], 31.0)
        self.assertGreater(on['slowest_ms'], 131.0)
        self.assertLess(on['slowest_ms'], 132.0)
        self.assertIn('Inference', on['label'])
        self.assertEqual(r12_stageD.en_figures(self.d['en']['four_stall_BAT_IN_V'])['by_case']['initial']['turn_on'], on)

    def test_window_figures_carry_the_inference_label(self):
        v33 = self.w['rails']['3V3 (U2 LMR50410, R14 47k / R15 20k)']
        for label in (v33['label'], self.w['cold_screen']['label'], self.w['sense']['label'],
                      self.w['fire']['gate']['note'], self.d['u6_supply']['label'],
                      self.d['fire']['gate']['q124_vgs_min_basis']['label']):
            self.assertIn('Calculation / Inference', label)
            self.assertIn(self.LABEL, label)


class Round8(unittest.TestCase):
    """R12 review round 8, analyses lane: R12F8-TRI-06 (drift case in the EN model and the PA6 window), -07 (U9 RON at
    SLVSFC9C's 45 mOhm maximum), -08 (PA6 hold-up over the divider tolerance, R12's window), -09 (U403 VIN and the
    camera-pin estimate on the current copper; the U400 feed drop), -10 (OVLO pin)."""
    TD = 0.01 + 100e-6 * 67

    @classmethod
    def setUpClass(cls):
        cls.w = json.loads((DESIGN / 'r12_windows.json').read_text())
        cls.d = json.loads((DESIGN / 'stageD_budget.json').read_text())

    def test_en_model_matches_r10_at_1pct(self):
        import r11_stageD
        import r12_budget
        for v in (8.4, 6.0, 5.72, 5.5):
            self.assertEqual(r12_budget.en_model(v), r11_stageD.en_model(v))
            self.assertEqual(r12_budget.en_model(v, 0.01), r11_stageD.en_model(v))

    def test_en_bound_is_the_drift_case(self):
        """R12F8-TRI-06: R80 / R165 / R81 at +/-1.67 %: 7.61 ms single drop-out and 7.08 ms worst-corner limit at the
        four-stall BAT_IN, 7 ms line to about 5.71 V, 10 ms drop-out needs about 6.02 V, turn-on about 29.9-135.9 ms."""
        e = self.d['en']
        i, dr, b = e['by_case']['initial'], e['by_case']['drift'], e['bound']
        self.assertAlmostEqual(i['resistor_tolerance'], 0.01, places=12)
        self.assertAlmostEqual(dr['resistor_tolerance'], self.TD, places=12)
        self.assertAlmostEqual(i['four_stall_periodic_limit_ms'], 7.56, places=2)
        self.assertAlmostEqual(dr['four_stall_single_dropout_ms'], 7.61, places=2)
        self.assertAlmostEqual(dr['four_stall_periodic_limit_ms'], 7.08, places=2)
        self.assertAlmostEqual(b['margin_over_7ms_line_ms'], dr['four_stall_periodic_limit_ms'] - 7.0, places=12)
        self.assertGreater(b['margin_over_7ms_line_ms'], 0.0)
        self.assertTrue(b['seven_ms_line_holds_at_four_stall'])
        self.assertAlmostEqual(b['seven_ms_line_holds_down_to_V'], 5.7095, places=3)
        self.assertLess(b['seven_ms_line_holds_down_to_V'], e['four_stall_BAT_IN_V'])
        self.assertAlmostEqual(b['single_10ms_dropout_needs_pack_V'], 6.025, places=2)
        self.assertAlmostEqual(b['turn_on_ms'][0], 29.94, places=1)
        self.assertAlmostEqual(b['turn_on_ms'][1], 135.88, places=1)
        self.assertEqual(b['turn_on_ms'], [min(i['turn_on']['fastest_ms'], dr['turn_on']['fastest_ms']),
                                           max(i['turn_on']['slowest_ms'], dr['turn_on']['slowest_ms'])])

    def test_pa6_window_and_margins_in_both_cases(self):
        p = self.d['pa6_corners']
        t = p['window']['trip_V']
        # R12F9-TRI-04 (round 9 lane B): band 0.425-0.455 V, R60 / R61 0.1 % 25 ppm/K
        self.assertEqual(p['window']['threshold_V'], [0.425, 0.455])
        self.assertAlmostEqual(t['nominal_ratio'][0], 0.425 * 11, places=12)
        self.assertAlmostEqual(t['nominal_ratio'][1], 0.455 * 11, places=12)
        self.assertAlmostEqual(t['initial'][0], 4.6665, places=4)
        self.assertAlmostEqual(t['drift'][0], 4.6523, places=4)
        self.assertAlmostEqual(t['drift'][1], 5.0294, places=4)
        self.assertAlmostEqual(p['window']['divider_tolerance']['initial'], 0.001, places=12)
        self.assertAlmostEqual(p['window']['divider_tolerance']['drift'], 0.001 + 25e-6 * 67, places=12)
        self.assertAlmostEqual(p['window']['ratio']['drift'][0], self.w['sense']['drift']['VLOGIC_SENSE_ratio'][0], places=5)
        for name in ('healthy', 'match_shorted', 'match_and_leads_shorted'):
            c = p[name]
            for k, w in t.items():
                self.assertAlmostEqual(c['margin_to_trip_top_V'][k], c['VLOGIC_V'][0] - w[1], places=12)
        # R12F9-TRI-04: with the 0.1 % divider and the 0.425-0.455 V band the healthy margin is positive in every case
        # (about +59 mV at drift); a shorted match still trips PA6 (firmware rule 4)
        for k in t:
            self.assertGreater(p['healthy']['margin_to_trip_top_V'][k], 0.05)
            self.assertLess(p['match_shorted']['margin_to_trip_top_V'][k], 0.0)
            self.assertLess(p['match_and_leads_shorted']['margin_to_trip_top_V'][k], 0.0)

    def test_d_r12_21_margin_is_negative_with_tolerance(self):
        """D-R12-21's trip bottom over U9's turn-off corner: negative with the 1 % divider at 0.42 V (round 8); with
        R12F9-TRI-04's 0.1 % divider and 0.425 V bottom it clears in every case (+51 mV at drift)."""
        v = self.w['vlogic']
        m = v['pa6_retuned_margins_V']
        self.assertAlmostEqual(self.w['u9']['turn_off_max_bat_V']['initial'], 4.802, places=3)
        self.assertAlmostEqual(m['nominal_ratio']['above_u9_turn_off_through_d5'], 0.1229, places=4)
        self.assertAlmostEqual(m['initial']['above_u9_turn_off_through_d5'], 0.1144, places=4)
        self.assertAlmostEqual(m['drift']['above_u9_turn_off_through_d5'], 0.0513, places=4)
        self.assertEqual(self.d['pa6_corners']['trip_bottom_above_u9_turn_off_V'],
                         {k: x['above_u9_turn_off_through_d5'] for k, x in m.items()})

    def test_u9_ron_is_the_datasheet_maximum(self):
        import r12_budget
        self.assertEqual(r12_budget.U9_RON, 0.045)
        self.assertEqual(self.d['pa6_corners']['u9_ron_ohm'], 0.045)
        self.assertEqual(self.d['port_supply']['u400_input']['u9_ron_ohm'], 0.045)
        self.assertEqual(self.d['u403_input']['u9_ron_ohm'], 0.045)
        h, s = self.d['pa6_corners']['healthy'], self.d['dc_solves']
        raw = h['RAW_PROTECTED_drop_at_D5_V']
        self.assertAlmostEqual(h['U9_and_copper_drop_V'],
                               h['converter_A'] * (0.045 + s['BAT_IN_J1_to_U9']['resistance_ohm'] * 1.1965) + raw,
                               places=12)
        self.assertNotIn("0.04 ohm", self.w['vlogic']['basis'])

    def test_holdup_from_r12_pa6_window(self):
        hw, hd = self.w['holdup'], self.d['holdup']['unshed']
        self.assertEqual(hw['from_pa6_trip_ms']['nominal_ratio'], [0.501, 1.811])     # R12F9-TRI-04 band / divider
        self.assertEqual(hw['from_pa6_trip_ms']['initial'], [0.496, 1.827])
        self.assertEqual(hw['from_pa6_trip_ms']['drift'], [0.487, 1.853])
        for k in ('nominal_ratio', 'initial', 'drift'):
            self.assertEqual([round(x, 3) for x in hd['pa6_trip_ms'][k]], hw['from_pa6_trip_ms'][k])
        self.assertEqual(hd['pa6_trip_range_ms']['drift'], hd['pa6_trip_ms']['drift'])

    def test_u403_input_and_camera_pin(self):
        u, s = self.d['u403_input'], self.d['dc_solves']
        r403 = s['RAW_PROTECTED_U9_to_U403']['resistance_ohm'] * 1.1965     # 70 C copper (R12F9-TRI-04)
        self.assertAlmostEqual(u['branch_shared_ohm']['U403 (camera)'], r403, places=12)
        self.assertLessEqual(u['branch_shared_ohm']['U400 (ports)'], r403)
        self.assertAlmostEqual(u['VIN_V'], u['BAT_IN_V'] - u['drop_to_U403_VIN_V'], places=12)
        self.assertTrue(u['below_VO_over_0V75'])
        for k, v in u['camera_pin_estimate_V'].items():
            self.assertAlmostEqual(v, u['headroom']['max_held_V'][k]
                                   - (s['CAM_5V_L401_to_J9']['resistance_ohm'] * 1.1965 + .15) - .05, places=9)
        self.assertIn('Inference', u['label'])

    def test_u400_feed_drop(self):
        f, r = self.d['u400_feed_drop'], self.d['rails']
        shared = [g for g in self.d['rails_shared']['groups'] if 'U400 IN' in g['paths']]
        want = r['U400 IN']['amps'] * r['U400 IN']['R_tracks_series_ohm'] + sum(
            g['R_series_ohm'] * sum(r[n]['amps'] for n in g['paths'] if n != 'U400 IN') for g in shared)
        self.assertAlmostEqual(f['design_V'], want, places=12)
        self.assertLess(f['budget_V'], f['design_V'])

    def test_ovlo_pin(self):
        o = self.w['u9']['ovlo_pin_V_at_5V71']
        self.assertAlmostEqual(o['nominal'], round(5.71 * 133 / 1133, 4), places=9)
        self.assertAlmostEqual(o['nominal'], 0.6703, places=4)
        self.assertNotIn('0.676', self.w['u9']['ovlo_pin_roc'])
        self.assertTrue(self.w['u9']['ovlo_pin_roc_ok'])


class Round9(unittest.TestCase):
    """R12F9-TRI-04 (copper at 70 C in the four-stall bounds) and R12F9-TRI-05 (dummy-fire drop bound)."""

    @classmethod
    def setUpClass(cls):
        cls.d = json.loads((DESIGN / 'stageD_budget.json').read_text())

    def test_hot_copper_factor(self):
        import r12_stageD
        self.assertAlmostEqual(r12_stageD.HOT_CU, 1.1965, places=12)
        p, s = self.d['pa6_corners'], self.d['dc_solves']
        self.assertEqual(p['copper_factor_70C'], r12_stageD.HOT_CU)
        for k in ('D5', 'U400', 'U403'):
            self.assertAlmostEqual(p['raw_point_ohm'][k],
                                   s[f'RAW_PROTECTED_U9_to_{k}']['resistance_ohm'] * r12_stageD.HOT_CU, places=12)
        self.assertAlmostEqual(p['J1_to_U9_ohm'], s['BAT_IN_J1_to_U9']['resistance_ohm'] * r12_stageD.HOT_CU, places=12)
        u = self.d['port_supply']['u400_input']
        self.assertAlmostEqual(u['J1_to_U9_ohm'], p['J1_to_U9_ohm'], places=12)
        self.assertAlmostEqual(u['branch_shared_ohm']['U400 (ports)'], p['raw_point_ohm']['U400'], places=12)
        self.assertAlmostEqual(p['vlogic_shared_ohm'], min(s['VLOGIC_D5_to_R60']['resistance_ohm'],
                                                           s['VLOGIC_D5_to_U2']['resistance_ohm']) * r12_stageD.HOT_CU,
                               places=12)
        h = p['healthy']
        self.assertAlmostEqual(h['VLOGIC_copper_drop_at_R60_V'], h['VLOGIC_A'] * p['vlogic_shared_ohm'], places=12)
        self.assertAlmostEqual(h['VLOGIC_V'][0], h['BAT_IN_V'] - h['U9_and_copper_drop_V'] - .45
                               - h['VLOGIC_copper_drop_at_R60_V'], places=12)
        self.assertIn('70 C', p['label'])
        self.assertIn('70 C', u['label'])
        self.assertIn('70 C', self.d['u403_input']['label'])

    def test_pa6_margins_hot(self):
        h = self.d['pa6_corners']['healthy']['margin_to_trip_top_V']
        # round 9 lane B (0.1 % divider, 0.425-0.455 V band); lane A's 1 % / 0.42-0.45 V figures were -0.0144 /
        # +0.0476 / +0.1385
        self.assertAlmostEqual(h['drift'], 0.0591, places=3)
        self.assertAlmostEqual(h['initial'], 0.0744, places=3)
        self.assertAlmostEqual(h['nominal_ratio'], 0.0835, places=3)

    def test_pa6_owner_options(self):
        o = self.d['pa6_corners']['owner_options']
        one, tenth = o['divider_1pct']['drift'], o['divider_0p1pct']['drift']
        # the adopted divider is the 0.1 % row (round 9 lane B)
        self.assertAlmostEqual(tenth['margin_to_trip_top_V']['healthy'],
                               self.d['pa6_corners']['healthy']['margin_to_trip_top_V']['drift'], places=12)
        self.assertIn('divider_0p1pct', o['adopted'])
        self.assertFalse(one['present_band_fits'])            # threshold alone cannot meet both limits at drift
        self.assertTrue(tenth['present_band_fits'])
        # +0.114 V with lane A's 0.42-0.45 V band (option (a)); +0.059 V with the adopted 0.425-0.455 V band
        self.assertGreater(tenth['margin_to_trip_top_V']['healthy'], 0.05)
        for row in (o['divider_0p1pct']['initial'], tenth):
            m = row['centred_band_margins_V']
            self.assertGreater(m['healthy_to_trip_top'], 0.0)
            self.assertGreater(m['trip_bottom_above_u9_turn_off'], 0.0)
            self.assertAlmostEqual(m['healthy_to_trip_top'], m['trip_bottom_above_u9_turn_off'], delta=0.02)

    def test_pa6_adopted_band(self):
        """Round 9 lane B: the firmware band is the 0.1 % drift case's room with the 30 mV band centred, to the mV, and
        both limits clear in both resistor cases."""
        import r12_budget
        b = self.d['pa6_corners']['owner_options']['band_derivation']
        self.assertEqual(list(r12_budget.PA6_THRESHOLD), [0.425, 0.455])
        self.assertIs(r12_budget.PA6_TOL, r12_budget.TOL_PRECISE)
        self.assertEqual(b['band_V'], [0.425, 0.455])
        self.assertTrue(b['equals_threshold'])
        self.assertTrue(b['both_limits_clear'])
        self.assertGreaterEqual(b['room_width_drift_V'], b['band_width_V'])
        self.assertLessEqual(b['room_drift_V'][0], 0.425)
        self.assertGreaterEqual(b['room_drift_V'][1], 0.455)
        m = b['margins_V']['drift']
        self.assertAlmostEqual(m['healthy_to_trip_top'], 0.0591, places=3)
        self.assertAlmostEqual(m['trip_bottom_above_u9_turn_off'], 0.0513, places=3)
        self.assertAlmostEqual(self.d['pa6_corners']['trip_bottom_above_u9_turn_off_V']['drift'],
                               m['trip_bottom_above_u9_turn_off'], places=4)

    def test_dummy_fire_bound_at_r134_low_end(self):
        f = self.d['fire']
        b = f['dummy_fire']
        self.assertEqual(b['drop_bound_case'], 'drift_low')
        self.assertAlmostEqual(b['by_R134']['drift_low']['R134_ohm'], 1.9666, places=4)
        self.assertAlmostEqual(b['by_R134']['budget_hot_high']['fire_A'], f['stalls']['0']['fire_A'], places=12)
        self.assertAlmostEqual(b['drop_bound_V'], 0.2677, places=4)
        self.assertGreater(b['drop_bound_V'], b['by_R134']['budget_hot_high']['drop_bound_V'])
        self.assertTrue(b['bound_below_reject'])


if __name__ == '__main__':
    unittest.main()
