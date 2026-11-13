#!/usr/bin/env python3
"""Self-tests for R12's stage D analysis wrappers (tools/r12_hotplug.py, m3_design/r12_stageD.py's pure functions).

usage: python3 -I tools/test_r12_stageD.py      (no pcbnew, no numpy)
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'm3_design'))
DESIGN = ROOT / 'm3_design/r12/design'
# R12F12-TRI-22: the records are bound to the repository R12 board (tools/check.sh's R12 section checks the gated board
# itself through r12_hotplug.py --gate, with pcbnew)
BOARD = ROOT / 'm3_design/r12/m3.kicad_pcb'


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


class HotplugValidate(unittest.TestCase):
    """R12F12-TRI-22: R10's validate (with R12's patches) on the committed results, and seeded failures."""

    @classmethod
    def setUpClass(cls):
        import r12_hotplug
        r12_hotplug.install()
        cls.h = r12_hotplug
        cls.inputs = json.loads((DESIGN / 'hotplug_inputs_r12.json').read_text())
        cls.results = json.loads((DESIGN / 'hotplug_results_r12.json').read_text())

    def check(self, results=None, inputs=None):
        inputs = inputs or self.inputs
        return self.h.validate(inputs, results or self.results, inputs['electrical_sha256'])

    def mutated(self):
        return json.loads(json.dumps(self.results))

    def test_committed_results_validate(self):
        self.assertEqual(self.check(), [])
        self.assertTrue(self.results['passed'])
        self.assertEqual(len(self.results['rows']), 2304)
        self.assertEqual(self.results['failures'], [])

    def test_failed_metric_row_fails(self):
        bad = self.mutated()
        bad['rows'][17]['minimum_V'] = -15.5
        self.assertTrue(any(i.startswith('model fails') for i in self.check(bad)), self.check(bad))

    def test_duplicated_corner_fails(self):
        bad = self.mutated()
        bad['rows'] = [dict(r, corner=bad['rows'][0]['corner']) for r in bad['rows']]
        self.assertIn('missing or changed model corners', self.check(bad))
        bad = self.mutated()
        bad['rows'][1]['corner'] = bad['rows'][0]['corner']
        self.assertIn('missing or changed model corners', self.check(bad))

    def test_stale_inputs_or_model_fail(self):
        bad = self.mutated()
        bad['model_sha256'] = '0' * 64
        self.assertIn('stale model source', self.check(bad))
        inputs = json.loads(json.dumps(self.inputs))
        inputs['edges'][0]['R_ohm'] *= 1.5
        self.assertIn('stale model inputs', self.check(inputs=inputs))

    def test_recomputed_floats_at_1e12(self):
        """Retained-output floats agree at 1e-12 relative; a larger change, or a changed identity, fails."""
        live = self.h.base.retained_output(self.inputs)
        near = self.mutated()
        near['retained_output'] = json.loads(json.dumps(live))
        near['retained_output']['capacitance_F'] *= 1 + 5e-14
        self.assertEqual(self.check(near), [])
        far = self.mutated()
        far['retained_output'] = json.loads(json.dumps(live))
        far['retained_output']['capacitance_F'] *= 1 + 1e-9
        self.assertIn('stale retained-output calculation', self.check(far))
        ident = self.mutated()
        ident['retained_output'] = json.loads(json.dumps(live))
        ident['retained_output']['inference'] += ' '
        self.assertIn('stale retained-output calculation', self.check(ident))
        self.assertTrue(self.h.close(1.0, 1.0 + 5e-13))
        self.assertFalse(self.h.close(1.0, 1.0 + 5e-12))
        self.assertFalse(self.h.close(True, 1.0))
        self.assertFalse(self.h.close('a', 'b'))

    def test_records_bound_to_the_board(self):
        board = hashlib.sha256(BOARD.read_bytes()).hexdigest()
        self.assertEqual(self.inputs['board_sha256'], board)
        d = json.loads((DESIGN / 'stageD_budget.json').read_text())
        self.assertEqual(d['board_sha256'], board)
        self.assertEqual(d['source_board_sha256'], board)
        self.assertEqual(self.h.stage_d_binding(board), [])

    def test_stale_binding_fails(self):
        board = hashlib.sha256(BOARD.read_bytes()).hexdigest()
        self.assertEqual(len(self.h.stage_d_binding('0' * 64)), 3)
        inputs = dict(self.inputs, board_sha256='0' * 64)
        self.assertEqual(len(self.h.stage_d_binding(board, inputs=inputs)), 1)
        d = json.loads((DESIGN / 'stageD_budget.json').read_text())
        d['source_board_sha256'] = '0' * 64
        self.assertEqual(len(self.h.stage_d_binding(board, budget=d)), 1)


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
        I x the ACT_FET_S copper below the divider's tap at Q120's source (copper at 70 C). R12F12-TRI-30: the J1 -> Q120.3
        term is the BAT_IN network's, and the converter current's share of that copper lowers Q120's drain too."""
        d = json.loads((DESIGN / 'stageD_budget.json').read_text())
        f = d['fire']
        g, lo = f['gate'], f['gate']['q120_vgs_ratio_min_max'][0]
        hot = 1 + .00393 * 50
        z = d['bat_in_network']['Z_ohm']
        r_bat = z['Q120']['Q120'] * hot
        r_fets = d['fire_copper']['ACT_FET_S']['R_20C_ohm'] * hot
        four = g['q120_q121_vgs_four_stall_fire']
        i, ic = f['four_stall_A'], f['four_stall_converter_A']
        self.assertAlmostEqual(four['BAT_IN_V'], f['four_stall_BAT_IN_V'], places=9)
        self.assertAlmostEqual(four['fire_A'], i, places=9)
        self.assertAlmostEqual(four['Q120_drop_V'], i * f['pfet_hot_ohm'], places=9)
        self.assertAlmostEqual(four['BAT_IN_copper_drop_V'], i * r_bat + ic * z['Q120']['U9'] * hot, places=9)
        self.assertAlmostEqual(four['ACT_FET_S_copper_drop_V'], i * r_fets, places=9)
        want = -(f['four_stall_BAT_IN_V'] - ic * z['Q120']['U9'] * hot - i * (r_bat + f['pfet_hot_ohm']) - .1) * lo
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
        """R12F2-TRI-07: the 0.6 mm B.Cu RAW_PROTECTED trunk along the east edge, from U9's island to D5's branch, feeds
        both U400 and D5 and is rated at the sum (R12F12-TRI-40: named, not by coordinates)."""
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
        """R12F3-TRI-09: a branch's drop at D5 is its current times min(its own, D5's) resistance from U9.
        R12F10-TRI-09: the currents are raw_point's self-consistent solve: each sink's node is U9's output less the
        mutual-resistance drops, U400 / U403 draw their power at their own node, D5 carries U2's input current (U2's VIN
        = D5's node - 0.45 V - I x R(D5 -> U2)), R92 its node / 3234 ohm, and D5's loss is 0.45 V x its current."""
        import r12_stageD
        fire = dict(other_load_parts=dict(camera_W=6.0, ports_W=3.0, logic_W=0.5, microsd_write_W=0.3),
                    stalls={'4': dict(BAT_IN_V=5.0)},
                    shorted={'match_shorted_4_stalls': dict(BAT_IN_V=5.0),
                             'match_and_leads_shorted_4_stalls': dict(BAT_IN_V=5.0)})
        out = r12_stageD.pa6_corners(fire, 0.01, dict(D5=0.02, U400=0.05, U403=0.01), dict(R60=0.004, U2=0.003))
        h = out['healthy']
        k = 1 + 0.00393 * 50                                    # copper at 70 C (R12F9-TRI-04)
        c = h['branch_A']
        tot = sum(c.values())
        self.assertAlmostEqual(h['converter_A'], tot, places=12)
        u9_out = 5.0 - tot * (0.045 + 0.01 * k)                 # U9 RON 45 mOhm (R12F8-TRI-07)
        r = dict(U400=0.05 * k, U403=0.01 * k, D5=0.02 * k)
        at = dict(U400='U400', U403='U403', D5='D5', R92='D5')
        node = {n: u9_out - sum(c[j] * min(r[n], r[at[j]]) for j in c) for n in r}
        raw = (c['U403'] * 0.01 + (c['U400'] + c['D5'] + c['R92']) * 0.02) * k
        self.assertAlmostEqual(h['RAW_PROTECTED_drop_at_D5_V'], raw, places=12)
        self.assertAlmostEqual(h['U9_and_copper_drop_V'], 5.0 - node['D5'], places=12)
        self.assertAlmostEqual(c['U400'], 3.0 / node['U400'], places=12)
        self.assertAlmostEqual(c['U403'], 6.0 / node['U403'], places=12)
        self.assertAlmostEqual(c['R92'], node['D5'] / 3234.0, places=12)
        v_u2 = node['D5'] - 0.45 - c['D5'] * 0.003 * k
        self.assertAlmostEqual(h['U2_VIN_V'], v_u2, places=12)
        self.assertAlmostEqual(c['D5'], 0.8 / v_u2, places=12)              # D5's current = U2's input current
        self.assertAlmostEqual(h['D5_loss_W'], 0.45 * c['D5'], places=12)
        self.assertAlmostEqual(h['lumped_drop_V_superseded'] - h['U9_and_copper_drop_V'],
                               c['U403'] * (0.02 - 0.01) * k, places=12)

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
        want = sum(h['branch_A'][k] * (r_d5 - p['branch_shared_ohm'][n])
                   for k, n in (('U403', 'U403 (camera)'), ('U400', 'U400 (ports)')))
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
        self.assertAlmostEqual(u6['1A_rating_bound']['min_VCC_drift_V'],                 # 70 C copper (R12F12-TRI-31)
                               v33['drift']['min_V'] - u6['1A_rating_bound']['drop_drift_V'], places=9)
        self.assertGreater(u6['1A_rating_bound']['margin_drift_V'], 0.06)    # 0.069 V at 70 C copper (R12F12-TRI-31)
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
        """R12F8-TRI-06: R80 / R165 / R81 at +/-1.67 %. R12F12-TRI-30: EN is fed from R80.1, 18.6 mV below J1 at the
        four-stall point (5.7008 V against J1's 5.7194 V): 7.45 ms single drop-out and 6.935 ms worst-corner limit (7.60 /
        7.073 ms when J1's voltage was used), so D-R25-01's 7 ms line no longer holds there (it holds down to about 5.71 V
        at R80.1) and the bench rule is chatter_rule's number (Round12); 10 ms drop-out needs about 6.02 V at R80.1,
        turn-on about 29.9-135.9 ms."""
        e = self.d['en']
        i, dr, b = e['by_case']['initial'], e['by_case']['drift'], e['bound']
        self.assertAlmostEqual(i['resistor_tolerance'], 0.01, places=12)
        self.assertAlmostEqual(dr['resistor_tolerance'], self.TD, places=12)
        self.assertAlmostEqual(i['four_stall_periodic_limit_ms'], 7.410, places=3)   # R12F12-TRI-30 (7.549 at J1)
        self.assertAlmostEqual(dr['four_stall_single_dropout_ms'], 7.446, places=3)  # R12F12-TRI-30 (7.596 at J1)
        self.assertAlmostEqual(dr['four_stall_periodic_limit_ms'], 6.935, places=3)  # R12F12-TRI-30 (7.073 at J1)
        self.assertAlmostEqual(e['four_stall_R80_V'], 5.7008, places=4)
        self.assertAlmostEqual(b['margin_over_7ms_line_ms'], dr['four_stall_periodic_limit_ms'] - 7.0, places=12)
        self.assertLess(b['margin_over_7ms_line_ms'], 0.0)
        self.assertFalse(b['seven_ms_line_holds_at_four_stall'])
        self.assertAlmostEqual(b['seven_ms_line_holds_down_to_V'], 5.7095, places=3)
        self.assertGreater(b['seven_ms_line_holds_down_to_V'], e['four_stall_R80_V'])
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
        # R12F10-TRI-08: PA6's +/-250 nA input leakage through R60 || R61 widens each end
        e = 250e-9 * 100e3 * 10e3 / 110e3
        self.assertAlmostEqual(t['nominal_ratio'][0], (0.425 - e) * 11, places=12)
        self.assertAlmostEqual(t['nominal_ratio'][1], (0.455 + e) * 11, places=12)
        self.assertAlmostEqual(t['initial'][0], 4.6415, places=4)
        self.assertAlmostEqual(t['drift'][0], 4.6274, places=4)
        self.assertAlmostEqual(t['drift'][1], 5.0546, places=4)
        self.assertAlmostEqual(p['window']['divider_tolerance']['initial'], 0.001, places=12)
        self.assertAlmostEqual(p['window']['divider_tolerance']['drift'], 0.001 + 25e-6 * 67, places=12)
        self.assertAlmostEqual(p['window']['ratio']['drift'][0], self.w['sense']['drift']['VLOGIC_SENSE_ratio'][0], places=5)
        for name in ('healthy', 'match_shorted', 'match_and_leads_shorted'):
            c = p[name]
            for k, w in t.items():
                self.assertAlmostEqual(c['margin_to_trip_top_V'][k], c['VLOGIC_V'][0] - w[1], places=12)
        # R12F9-TRI-04: with the 0.1 % divider and the 0.425-0.455 V band the healthy margin is positive in every case
        # (about +25 mV at drift with PA6's leakage and the self-consistent currents, R12F10-TRI-08 / -09; +59 mV
        # without); a shorted match still trips PA6 (firmware rule 4)
        for k in t:
            self.assertGreater(p['healthy']['margin_to_trip_top_V'][k], 0.02)
            self.assertLess(p['match_shorted']['margin_to_trip_top_V'][k], 0.0)
            self.assertLess(p['match_and_leads_shorted']['margin_to_trip_top_V'][k], 0.0)

    def test_d_r12_21_margin_is_negative_with_tolerance(self):
        """D-R12-21's trip bottom over U9's turn-off corner: negative with the 1 % divider at 0.42 V (round 8); with
        R12F9-TRI-04's 0.1 % divider and 0.425 V bottom it clears in every case (+51 mV at drift)."""
        v = self.w['vlogic']
        m = v['pa6_retuned_margins_V']
        self.assertAlmostEqual(self.w['u9']['turn_off_max_bat_V']['initial'], 4.802, places=3)
        # R12F10-TRI-08: with PA6's input leakage (0.1229 / 0.1144 / 0.0513 V without)
        self.assertAlmostEqual(m['nominal_ratio']['above_u9_turn_off_through_d5'], 0.0979, places=4)
        self.assertAlmostEqual(m['initial']['above_u9_turn_off_through_d5'], 0.0894, places=4)
        self.assertAlmostEqual(m['drift']['above_u9_turn_off_through_d5'], 0.0264, places=4)
        self.assertEqual(self.d['pa6_corners']['trip_bottom_above_u9_turn_off_V'],
                         {k: x['above_u9_turn_off_through_d5'] for k, x in m.items()})

    def test_u9_ron_is_the_datasheet_maximum(self):
        import r12_budget
        self.assertEqual(r12_budget.U9_RON, 0.045)
        self.assertEqual(self.d['pa6_corners']['u9_ron_ohm'], 0.045)
        self.assertEqual(self.d['port_supply']['u400_input']['u9_ron_ohm'], 0.045)
        self.assertEqual(self.d['u403_input']['u9_ron_ohm'], 0.045)
        h, z = self.d['pa6_corners']['healthy'], self.d['bat_in_network']['Z_ohm']
        raw = h['RAW_PROTECTED_drop_at_D5_V']
        self.assertAlmostEqual(h['U9_and_copper_drop_V'],
                               h['converter_A'] * (0.045 + z['U9']['U9'] * 1.1965) + h['fire_A'] * z['U9']['Q120'] * 1.1965
                               + raw, places=12)
        self.assertAlmostEqual(h['fire_A'], self.d['fire']['four_stall_A'], places=15)
        self.assertNotIn("0.04 ohm", self.w['vlogic']['basis'])

    def test_holdup_from_r12_pa6_window(self):
        hw, hd = self.w['holdup'], self.d['holdup']['unshed']
        # R12F9-TRI-04 band / divider, R12F10-TRI-08 PA6 leakage (0.501-1.811 / 0.496-1.827 / 0.487-1.853 without)
        self.assertEqual(hw['from_pa6_trip_ms']['nominal_ratio'], [0.486, 1.854])
        self.assertEqual(hw['from_pa6_trip_ms']['initial'], [0.48, 1.87])
        self.assertEqual(hw['from_pa6_trip_ms']['drift'], [0.471, 1.897])
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
        z = self.d['bat_in_network']['Z_ohm']              # R12F12-TRI-30: the BAT_IN network's J1 -> U9.5
        self.assertAlmostEqual(p['J1_to_U9_ohm'], z['U9']['U9'] * r12_stageD.HOT_CU, places=12)
        self.assertAlmostEqual(p['fire_coupling_at_U9_ohm'], z['U9']['Q120'] * r12_stageD.HOT_CU, places=12)
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
        # round 9 lane B (0.1 % divider, 0.425-0.455 V band) gave +0.0591 / +0.0744 / +0.0835; round 10 lane A adds
        # PA6's input leakage (R12F10-TRI-08) and the self-consistent D5 current (R12F10-TRI-09)
        # D-R12-174 (86.85 mm board): the RAW_PROTECTED island's longer aft band lowers the shared RAW copper
        # (31.0 -> 30.0 mOhm): +0.0286 / +0.0441 / +0.0532 (+0.0251 / +0.0405 / +0.0497 on a1e65bb4); R12F12-TRI-30:
        # the fire current's share of the J1 -> U9.5 copper: +0.0270 / +0.0424 / +0.0516
        self.assertAlmostEqual(h['drift'], 0.0270, places=3)
        self.assertAlmostEqual(h['initial'], 0.0424, places=3)
        self.assertAlmostEqual(h['nominal_ratio'], 0.0516, places=3)

    def test_pa6_owner_options(self):
        o = self.d['pa6_corners']['owner_options']
        one, tenth = o['divider_1pct']['drift'], o['divider_0p1pct']['drift']
        # the adopted divider is the 0.1 % row (round 9 lane B)
        self.assertAlmostEqual(tenth['margin_to_trip_top_V']['healthy'],
                               self.d['pa6_corners']['healthy']['margin_to_trip_top_V']['drift'], places=12)
        self.assertIn('divider_0p1pct', o['adopted'])
        self.assertFalse(one['present_band_fits'])            # threshold alone cannot meet both limits at drift
        self.assertTrue(tenth['present_band_fits'])
        # +0.114 V with lane A's 0.42-0.45 V band (option (a)); +0.025 V with the adopted 0.425-0.455 V band (round 10)
        self.assertGreater(tenth['margin_to_trip_top_V']['healthy'], 0.02)
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
        self.assertEqual(b['adopted_band_V'], [0.425, 0.455])
        self.assertTrue(b['adopted_inside_room'])
        self.assertTrue(b['both_limits_clear'])
        self.assertGreaterEqual(b['room_width_drift_V'], b['band_width_V'])
        self.assertLessEqual(b['room_drift_V'][0], 0.425)
        self.assertGreaterEqual(b['room_drift_V'][1], 0.455)
        m = b['margins_V']['drift']
        self.assertAlmostEqual(m['healthy_to_trip_top'], 0.0270, places=3)          # R12F12-TRI-30 (0.0286; 0.0251)
        self.assertAlmostEqual(m['trip_bottom_above_u9_turn_off'], 0.0264, places=3)
        self.assertAlmostEqual(self.d['pa6_corners']['trip_bottom_above_u9_turn_off_V']['drift'],
                               m['trip_bottom_above_u9_turn_off'], places=4)

    def test_dummy_fire_bound_at_r134_low_end(self):
        f = self.d['fire']
        b = f['dummy_fire']
        self.assertEqual(b['drop_bound_case'], 'drift_low')
        self.assertAlmostEqual(b['by_R134']['drift_low']['R134_ohm'], 1.9666, places=4)
        self.assertAlmostEqual(b['by_R134']['budget_hot_high']['fire_A'], f['stalls']['0']['fire_A'], places=12)
        # D-R12-174: J1 -> Q120 through D8.1 (0.2677 on a1e65bb4); R12F12-TRI-30: the network's J1 -> Q120.3 and the
        # converter current's share of it (0.2716 before)
        self.assertAlmostEqual(b['drop_bound_V'], 0.2732, places=3)
        self.assertGreater(b['drop_bound_V'], b['by_R134']['budget_hot_high']['drop_bound_V'])
        self.assertTrue(b['bound_below_reject'])


class Round10(unittest.TestCase):
    """R12F10-TRI-08 (PA6's own input leakage) and R12F10-TRI-09 (self-consistent D5 current) in the records."""

    @classmethod
    def setUpClass(cls):
        cls.d = json.loads((DESIGN / 'stageD_budget.json').read_text())
        cls.w = json.loads((DESIGN / 'r12_windows.json').read_text())

    def test_pa6_leakage_in_every_window(self):
        import r12_budget
        self.assertEqual(r12_budget.PA6_LEAK, 250e-9)
        for tol in (None, *r12_budget.PA6_TOL.values()):
            e = r12_budget.pa6_leak_V(tol)
            self.assertAlmostEqual(e, 250e-9 * 100e3 * 10e3 / 110e3 * (1 + (tol or 0)), places=15)
            if tol is not None:
                lo, hi = r12_budget.pa6_ratio(tol)
                w = r12_budget.pa6_trip_window(tol)
                self.assertAlmostEqual(w[0], (0.425 - e) / hi, places=12)
                self.assertAlmostEqual(w[1], (0.455 + e) / lo, places=12)
        v = self.w['vlogic']
        self.assertIn('Table 60', v['pa6_leakage']['source'])
        self.assertIn('Inference', v['pa6_leakage']['label'])
        self.assertAlmostEqual(v['pa6_threshold_bottom_needed_V']['drift'], 0.4226, places=4)
        p = self.d['pa6_corners']
        self.assertAlmostEqual(p['window']['leakage_A'], 250e-9, places=15)
        self.assertIn('R12F10-TRI-08', p['label'])
        b = p['owner_options']['band_derivation']
        self.assertAlmostEqual(b['room_drift_V'][0], 0.4226, places=4)
        self.assertGreaterEqual(b['room_drift_V'][1], 0.455)

    def test_d5_current_is_u2_input_current(self):
        f = self.d['fire']
        pt = f['converter_point_four_stall']
        self.assertAlmostEqual(pt['BAT_IN_V'], f['four_stall_BAT_IN_V'], places=12)
        self.assertAlmostEqual(pt['currents_A']['D5'], pt['U2_input_A'], places=10)
        self.assertAlmostEqual(pt['D5_loss_W'], 0.45 * pt['currents_A']['D5'], places=12)
        self.assertAlmostEqual(f['other_load_parts']['d5_W'], pt['D5_loss_W'], places=12)
        self.assertNotAlmostEqual(f['other_load_parts']['d5_W'], 0.45 * 0.3, places=3)
        h = self.d['pa6_corners']['healthy']
        self.assertAlmostEqual(h['D5_A'], pt['currents_A']['D5'], places=10)
        self.assertAlmostEqual(h['VLOGIC_A'], h['D5_A'], places=12)
        self.assertAlmostEqual(h['D5_loss_W'], 0.45 * h['D5_A'], places=12)
        raw = self.d['rails_shared']['raw_budget_A']
        self.assertAlmostEqual(raw['D5 IN'], h['D5_A'], places=10)
        u = self.d['port_supply']['u400_input']['four_stall_fire']
        self.assertAlmostEqual(u['converter_A'], h['converter_A'], places=10)
        self.assertAlmostEqual(self.d['u403_input']['converter_A'], h['converter_A'], places=10)

    def test_pack_load_convention_and_sensitivity(self):
        f = self.d['fire']
        v, i = f['four_stall_BAT_IN_V'], f['four_stall_A']
        conv = f['other_converter_load_W'] / v
        self.assertAlmostEqual(v, 7.4 - 0.15 * (i + conv + 4 * 1.92), places=6)
        s = f['pack_load_sensitivity']
        self.assertLess(s['four_stall_BAT_IN_V'], v)
        self.assertGreaterEqual(s['four_stall_A'], f['floor_A'])
        self.assertIn('en_at_that_BAT_IN', s)
        self.assertIn('Inference', s['basis'])


class Round12(unittest.TestCase):
    """R12 round 12 lane A: the BAT_IN network and EN at R80.1 (R12F12-TRI-30), the bench rule as a number (-23), the
    walk and joined paths (-24), 70 C drift minima and PA6's upper end (-31), the 3V3 budget (-11), VBUS_SENSE (-06),
    Q122's gate (-04) and D8's return (-16)."""

    @classmethod
    def setUpClass(cls):
        cls.d = json.loads((DESIGN / 'stageD_budget.json').read_text())

    def seeded(self):
        return json.loads(json.dumps(self.d))

    def test_record_passes(self):
        import r12_stageD
        self.assertEqual(r12_stageD.record_issues(self.d), [])

    def test_bench_rule_is_below_both_conventions(self):
        import r12_stageD
        e, f = self.d['en'], self.d['fire']
        ch = e['chatter_rule']
        main = e['bound']['four_stall_periodic_limit_ms']
        sens = f['pack_load_sensitivity']['en_at_that_BAT_IN']['four_stall_periodic_limit_ms']
        self.assertEqual(ch['limits_ms'], dict(gap1_constant_power=main, whole_current_sensitivity=sens))
        self.assertEqual(ch['worst_limit_ms'], min(main, sens))
        self.assertLessEqual(ch['bench_rule_ms'], min(main, sens) - 0.10 + 1e-12)
        self.assertGreater(ch['bench_rule_ms'] + 0.1, min(main, sens) - 0.10)        # the largest such 0.1 ms step
        self.assertEqual(ch['bench_rule_ms'], r12_stageD.bench_rule_ms(min(main, sens)))
        self.assertIn(f"< {ch['bench_rule_ms']:.1f} ms", ch['bench_rule'])
        self.assertEqual(r12_stageD.bench_rule_ms(6.845), 6.7)
        self.assertEqual(r12_stageD.bench_rule_ms(6.8), 6.7)
        self.assertEqual(r12_stageD.bench_rule_ms(6.7999), 6.6)
        self.assertEqual(r12_stageD.bench_rule_ms(7.073), 6.9)

    def test_bench_rule_seeds_fail(self):
        """Astra power-2: a sensitivity limit of 6.0 ms must fail; so must a rule not 0.10 ms under the worst limit."""
        import r12_stageD
        bad = self.seeded()
        bad['fire']['pack_load_sensitivity']['en_at_that_BAT_IN']['four_stall_periodic_limit_ms'] = 6.0
        self.assertTrue(r12_stageD.record_issues(bad))
        bad = self.seeded()
        bad['en']['chatter_rule']['bench_rule_ms'] = round(bad['en']['chatter_rule']['worst_limit_ms'], 1)
        self.assertTrue(r12_stageD.record_issues(bad))
        bad = self.seeded()
        bad['en']['chatter_rule']['bench_rule_ms'] -= 0.1
        self.assertTrue(any('largest' in i for i in r12_stageD.record_issues(bad)))
        bad = self.seeded()
        bad['en']['bound']['four_stall_periodic_limit_ms'] = 6.5
        self.assertTrue(r12_stageD.record_issues(bad))
        bad = self.seeded()
        del bad['en']['chatter_rule']
        self.assertTrue(r12_stageD.record_issues(bad))

    def test_unjoined_rail_fails(self):
        """R12F12-TRI-24: C84's VLOGIC run crosses C84.1; the walk joins it, and a path with joined false fails."""
        import r12_stageD
        r = self.d['rails']['C84 hold-up']
        self.assertTrue(r['joined'])
        self.assertIn('C84.1', r['pads'])
        self.assertTrue(all(x['joined'] for x in self.d['rails'].values()))
        bad = self.seeded()
        bad['rails']['C84 hold-up']['joined'] = False
        self.assertIn('rail path C84 hold-up is not joined', r12_stageD.record_issues(bad))

    def test_bat_in_network(self):
        n = self.d['bat_in_network']
        z = n['Z_ohm']
        self.assertEqual(n['order'], ['U9', 'Q120', 'R80'])
        self.assertLess(n['reciprocity_max_rel_asymmetry'], 1e-6)
        for a in z:
            for b in z:
                self.assertAlmostEqual(z[a][b], z[b][a], delta=1e-6 * z[a][b])
                self.assertGreater(z[a][b], 0.0)
                self.assertLessEqual(z[a][b], min(z[a][a], z[b][b]) * (1 + 1e-6))
        f, k = self.d['fire'], 1 + 0.00393 * 50
        for name in ('0', '4'):
            s = f['stalls'][name]
            for p in ('U9', 'Q120', 'R80'):
                self.assertAlmostEqual(s[f'{p}_V'], s['BAT_IN_V'] - k * (z[p]['U9'] * s['converter_A']
                                                                        + z[p]['Q120'] * s['fire_A']), places=12)
        four = f['stalls']['4']
        self.assertAlmostEqual(four['converter_A'], f['other_converter_load_W'] / four['BAT_IN_V'], places=9)
        self.assertAlmostEqual(f['fire_branch_without_pack_ohm'] * four['fire_A'],
                               four['BAT_IN_V'] - k * z['Q120']['U9'] * four['converter_A'], places=12)
        # EN at R80.1, not J1
        self.assertEqual(self.d['en']['four_stall_R80_V'], four['R80_V'])
        self.assertEqual(self.d['en']['four_stall_BAT_IN_V'], four['BAT_IN_V'])
        self.assertGreater(four['BAT_IN_V'] - four['R80_V'], 0.01)
        s = f['pack_load_sensitivity']
        self.assertEqual(s['en_at_that_BAT_IN']['R80_V'], s['four_stall_R80_V'])
        self.assertLess(s['four_stall_R80_V'], s['four_stall_BAT_IN_V'])
        # the fire loop's BAT_IN term is the network's J1 -> Q120.3
        self.assertAlmostEqual(f['bat_in_fire_term_70C_ohm'], z['Q120']['Q120'] * k, places=15)

    def test_drift_minima_at_70C(self):
        """R12F12-TRI-31: the U6 and port 'drift' minima use 70 C copper."""
        k = 1 + 0.00393 * 50
        u6 = self.d['u6_supply']
        v33 = json.loads((DESIGN / 'r12_windows.json').read_text())['rails']['3V3 (U2 LMR50410, R14 47k / R15 20k)']
        for row in ('1A_rating_bound', '0V5_allocation', 'u6_only_6mA'):
            r = u6[row]
            self.assertAlmostEqual(r['drop_drift_V'], r['drop_V'] * k, places=15)
            self.assertAlmostEqual(r['min_VCC_drift_V'], v33['drift']['min_V'] - r['drop_drift_V'], places=12)
            self.assertAlmostEqual(r['min_VCC_initial_V'], v33['initial']['min_V'] - r['drop_V'], places=12)
        ps = self.d['port_supply']
        for port in ('J410', 'J420', 'J440'):
            for row in ('budget_0A561', 'design_1A9'):
                r = ps[port][row]
                self.assertAlmostEqual(r['drop_bound_drift_V'], r['drop_bound_V'] * k, places=15)
                self.assertAlmostEqual(r['min_drift_V'], ps['window_drift_V'][0] - r['drop_bound_drift_V'], places=12)

    def test_pa6_upper_end_at_its_own_vf(self):
        p = self.d['pa6_corners']
        for name in ('healthy', 'match_shorted', 'match_and_leads_shorted'):
            c = p[name]
            hi = c['upper_end_VF_0V25']
            self.assertAlmostEqual(c['VLOGIC_V'][1], c['BAT_IN_V'] - hi['U9_and_copper_drop_V'] - .25
                                   - hi['VLOGIC_copper_drop_at_R60_V'], places=12)
            self.assertLess(hi['D5_A'], c['D5_A'])                 # a higher U2 VIN draws less current

    def test_3v3_budget(self):
        import r12_stageD
        b = self.d['u3v3_budget']
        lim = r12_stageD.u2_limit()
        self.assertAlmostEqual(lim['ripple_A'], 3.35 * (8.15 - 3.35) / (8.15 * 3.76e-6 * 700e3), places=12)
        self.assertAlmostEqual(b['u2_limit_A'], 0.875, places=3)              # triage TRI-11
        self.assertLess(b['u2_limit_fsw_min_A'], b['u2_limit_A'])
        self.assertTrue(b['fits_200MHz'])
        self.assertFalse(b['fits_480MHz'])
        c = b['cases']['200MHz_VOS3_Tj85']
        self.assertEqual(c['MCU_A'], 0.220)                                    # DS12110 Rev 8 Table 30 / 31, rev Y
        self.assertAlmostEqual(c['peak_A'], c['MCU_A'] + sum(b['loads_A'].values()) + b['buzzer_on_phase_A'], places=12)
        self.assertIn('Inference', b['label'])
        self.assertIn('DS12110 Rev 8', b['mcu_source'])

    def test_vbus_sense(self):
        v = self.d['vbus_sense']
        self.assertTrue(v['topology_ok'])
        self.assertAlmostEqual(v['ratio_nominal'], 0.6, places=12)
        for case in ('initial', 'drift'):
            c = v['cases'][case]
            self.assertGreater(c['VBUS_SENSE_V'][0], c['vih_V'])
            self.assertLess(c['VBUS_SENSE_V'][1], c['abs_max_V'])
        self.assertTrue(v['ok'])
        import r12_stageD
        bad = self.seeded()
        bad['vbus_sense']['topology_ok'] = False
        self.assertTrue(r12_stageD.record_issues(bad))

    def test_q122_gate(self):
        q = self.d['q122_gate']
        self.assertTrue(q['topology_ok'])
        self.assertAlmostEqual(q['vgs_nominal_3V30_V'], 3.30 * (2e3 / 1.2) / (2e3 / 1.2 + 1e3), places=12)
        self.assertGreater(q['vgs_min_V'], q['vgs_th_max_V'])
        self.assertGreater(min(q['single_open_V'].values()), q['vgs_th_max_V'])
        self.assertTrue(q['pc1_within_voh_row'])

    def test_d8_return(self):
        r = self.d['d8_return']
        self.assertEqual(len(r['runs']), 2)
        self.assertLess(r['R_20C_ohm'], 0.002)
        self.assertLess(r['L_nH'], 1.0)
        self.assertIn('Inference', r['label'])


if __name__ == '__main__':
    unittest.main()
