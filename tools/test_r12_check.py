"""Synthetic passing/failing R12 board-rule tests, plus schematic, library and budget regressions.
Real-board tests skip until the board is tracked and has routed tracks; no R12 copper fixture is committed here.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

try:
    import pcbnew
except ImportError:
    pcbnew = None
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'm3_design'))
if pcbnew:
    import check_r12 as r12
    import fit_check as fc
    import route_check as rc
import r12_sch
import r12_sch_check
import r12_budget

LIB = ROOT / 'm3_design/r12/kilib/rocket.pretty'


def mm(v):
    return pcbnew.FromMM(v)


@unittest.skipUnless(pcbnew, 'KiCad python required')
class Synthetic(unittest.TestCase):
    """check_r12 rules on a small board: a clean board passes, each seeded fault fails its rule."""

    def board(self, layers=4, length=90.0, width=46.0):
        b = pcbnew.BOARD()
        b.SetCopperLayerCount(layers)
        b.GetDesignSettings().SetBoardThickness(mm(1.6))
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_RECT)
        s.SetStart(pcbnew.VECTOR2I(0, 0))
        s.SetEnd(pcbnew.VECTOR2I(mm(width), mm(length)))
        s.SetLayer(pcbnew.Edge_Cuts)
        b.Add(s)
        fp = pcbnew.FootprintLoad(str(LIB), 'R0402')
        fp.SetReference('R14')
        b.Add(fp)
        fp.SetPosition(pcbnew.VECTOR2I(mm(10), mm(10)))
        b.GetTitleBlock().SetRevision(r12.REVISION)
        return b, fp

    def via(self, b, x, y, drill=0.3, dia=0.45):
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        v.SetDrill(mm(drill))
        v.SetWidth(mm(dia))
        b.Add(v)
        return v

    def run_rules(self, b, only, path=None):
        return r12.check_board(b, path or ROOT / 'm3_design/r12/m3.kicad_pcb', only=set(only), stage='copper')

    def test_clean_board_passes_geometry_rules(self):
        b, _ = self.board()
        self.via(b, 30, 30)
        report = self.run_rules(b, ('L-1', 'M-1', 'F-1', 'V-1', 'V-2'))
        self.assertTrue(report['ok'], report['issues'])

    def test_six_layers_fail(self):
        b, _ = self.board(layers=6)
        self.assertFalse(self.run_rules(b, ('L-1',))['ok'])

    def test_long_or_narrow_outline_fails(self):
        for kw in (dict(length=105.0), dict(width=50.0)):
            with self.subTest(**kw):
                b, _ = self.board(**kw)
                self.assertFalse(self.run_rules(b, ('M-1',))['ok'])

    def test_bottom_side_part_fails(self):
        b, fp = self.board()
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        report = self.run_rules(b, ('F-1',))
        self.assertFalse(report['ok'])
        self.assertTrue(any('bottom side' in i for i in report['issues']), report['issues'])

    def test_small_via_fails(self):
        for drill, dia in ((0.2, 0.45), (0.3, 0.4), (0.25, 0.35)):
            with self.subTest(drill=drill, dia=dia):
                b, _ = self.board()
                self.via(b, 30, 30, drill, dia)
                self.assertFalse(self.run_rules(b, ('V-1',))['ok'])

    def test_via_in_pad_fails(self):
        b, fp = self.board()
        pad = list(fp.Pads())[0]
        self.via(b, pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y))
        self.assertFalse(self.run_rules(b, ('V-2',))['ok'])

    def test_netlist_parity_and_revision(self):
        b, _ = self.board()
        report = r12.check_board(b, ROOT / 'm3_design/r12/m3.kicad_pcb', only={'N-1'}, stage='placement')
        self.assertFalse(report['ok'])                       # one part on the board, 184 in the schematic
        self.assertTrue(any('not on the board' in i for i in report['issues']))
        b.GetTitleBlock().SetRevision('M3-ASSY-R11')
        report = r12.check_board(b, ROOT / 'm3_design/r12/m3.kicad_pcb', only={'N-1'}, stage='placement')
        self.assertTrue(any('revision' in i for i in report['issues']))

    def test_rules_files_must_be_the_generators(self):
        with tempfile.TemporaryDirectory(prefix='r12-krules-') as d:
            path = Path(d) / 'm3.kicad_pcb'
            shutil.copy2(ROOT / 'm3_design/r12/m3.kicad_dru', Path(d) / 'm3.kicad_dru')
            shutil.copy2(ROOT / 'm3_design/r12/m3.kicad_pro', Path(d) / 'm3.kicad_pro')
            b, _ = self.board()
            self.assertTrue(r12.check_board(b, path, only={'K-rules'}, stage='placement')['ok'])
            dru = Path(d) / 'm3.kicad_dru'
            dru.write_text(dru.read_text().replace('(min 0.3mm)', '(min 0.2mm)'))
            self.assertFalse(r12.check_board(b, path, only={'K-rules'}, stage='placement')['ok'])

    def test_fit_report_binding(self):
        b, _ = self.board()
        ctx = dict(board=b, fit=dict(profile='r11', board_sha256='x', issues=[]), sha='y')
        self.assertEqual(len(r12.m5(ctx)), 2)


@unittest.skipUnless(pcbnew, 'KiCad python required')
class Profiles(unittest.TestCase):
    def test_fit_profile_r12(self):
        self.assertEqual((fc.R12_CFG['layers'], fc.R12_CFG['max_length'], fc.R12_CFG['one_side']), (4, 100.0, True))
        self.assertEqual((fc.R11_CFG['layers'], fc.R11_CFG['max_length'], fc.R11_CFG['one_side']), (6, 56.0, False))
        self.assertEqual(fc.GH_CLONE_PART.match('GH1.25-6PWT').group(1), '6')

    def test_fit_r12_flags_bottom_parts_and_layers(self):
        b = pcbnew.BOARD()
        b.SetCopperLayerCount(6)
        b.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(1.6))
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_RECT)
        s.SetStart(pcbnew.VECTOR2I(0, 0))
        s.SetEnd(pcbnew.VECTOR2I(mm(46), mm(110)))
        s.SetLayer(pcbnew.Edge_Cuts)
        b.Add(s)
        fp = pcbnew.FootprintLoad(str(LIB), 'R0402')
        fp.SetReference('R14')
        b.Add(fp)
        fp.SetPosition(pcbnew.VECTOR2I(mm(20), mm(20)))
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        report = fc.check_board(b, ROOT / 'm3_design/r12', profile='r12')
        text = ' '.join(report['issues'])
        self.assertEqual(report['profile'], 'r12')
        for needle in ('four-layer', 'bottom side', '100 mm'):
            self.assertIn(needle, text)

    def test_route_profile_r12(self):
        rc.set_profile('r12')
        try:
            self.assertIn('r12', rc.R10_LIKE)
            self.assertEqual((rc.LEFTOVERS, rc.PARALLEL_VIAS), ([], []))
            # D-R12-75A: only the recorded forced findings, each with a reason and the measured route figures
            self.assertEqual((rc.ALLOWLIST, rc.ROUTE_FIGURES), (rc.ALLOWLIST_R12, rc.ROUTE_FIGURES_R12))
            for e in rc.ALLOWLIST:
                self.assertTrue(e[4].startswith('D-R12-'), e[:4])
                if e[0] in ('detour', 'extra_vias'):
                    self.assertEqual((e[5]['len_mm'], e[5]['vias']), rc.ROUTE_FIGURES[e[1]], e[:4])
        finally:
            rc.set_profile('r8')


BOARD12 = ROOT / 'm3_design/r12/m3.kicad_pcb'


@unittest.skipUnless(pcbnew and BOARD12.is_file(), 'KiCad python and the R12 board required')
class Round1Fixes(unittest.TestCase):
    """R12 review round 1 gate fixes (D-R12-86 ... -90), seeded on the committed board."""

    @classmethod
    def setUpClass(cls):
        cls.board = pcbnew.LoadBoard(str(BOARD12))

    def kn(self, board=None):
        return r12.check_board(board or self.board, BOARD12, only={'K-neighbours'}, stage='full')

    def test_k_neighbours_registered_in_every_stage(self):
        for stage in ('placement', 'copper', 'full'):
            self.assertIn('K-neighbours', r12.STAGES[stage], stage)
        self.assertNotIn(('ACT_EN_MCU', 'LOGIC_SOURCE_ST'), r12.NEIGHBOUR_INERT)   # U11 deleted (D-R12-04)

    def test_k_neighbours_pass_on_board_and_fail_on_port_sense_at_g3(self):
        rep = self.kn()
        self.assertTrue(rep['ok'], rep['issues'])
        gates = rep['evidence']['k_neighbours']['bridged_gate_V']
        # D-R12-93: PORT_SENSE left G3 for PD10 (H9); its D-R12-86 inert entry is gone, so PORT_SENSE back on G3 fails
        self.assertEqual(set(gates), {f'ACT_EN_MCU/{n}' for n in ('PYRO1_CONT', 'CAM_5V_SENSE', 'NRST')})
        self.assertNotIn(('ACT_EN_MCU', 'PORT_SENSE'), r12.NEIGHBOUR_INERT)
        u1 = self.board.FindFootprintByReference('U1')
        g3 = next(p for p in u1.Pads() if p.GetNumber() == 'G3')
        kept = g3.GetNet()
        try:
            g3.SetNet(self.board.FindNet('PORT_SENSE'))
            rep = self.kn()
            self.assertFalse(rep['ok'])
            self.assertTrue(any('G3' in i and 'PORT_SENSE' in i for i in rep['issues']), rep['issues'])
        finally:
            g3.SetNet(kept)

    def test_k_neighbours_driver_or_uninert_net_fails(self):
        u1 = self.board.FindFootprintByReference('U1')
        g3 = next(p for p in u1.Pads() if p.GetNumber() == 'G3')
        g2 = next(p for p in u1.Pads() if p.GetNumber() == 'G2')
        net_g3, net_g2 = g3.GetNet(), g2.GetNet()
        led = self.board.FindNet('HG_CS')
        try:
            g2.SetNet(led)                                                    # a push-pull GPIO beside PC1
            rep = self.kn()
            self.assertFalse(rep['ok'])
            self.assertTrue(any('neighbour G2 carries HG_CS' in i for i in rep['issues']), rep['issues'])
        finally:
            g2.SetNet(net_g2)
        r33 = self.board.FindFootprintByReference('R33')
        pad = next(iter(r33.Pads()))
        kept = pad.GetNet()
        try:
            pad.SetNet(next(p for p in u1.Pads() if p.GetNumber() == 'E2').GetNet())   # an unrecorded part on CAM_5V_SENSE
            rep = self.kn()
            self.assertFalse(rep['ok'])
            self.assertTrue(any('R33' in i and 'sense net' in i for i in rep['issues']), rep['issues'])
        finally:
            pad.SetNet(kept)
        self.assertTrue(self.kn()['ok'])

    def test_dru_unconditional_after_scoped_refused(self):
        text = (BOARD12.with_suffix('.kicad_dru')).read_text()
        self.assertEqual(r12.dru_order(text), [])
        floor = text[text.index('# JLC multilayer 0.09 mm, plus 0.01 mm'):]
        floor = floor[:floor.index('\n\n')]
        self.assertIn('R12 board floor: copper clearance', floor)
        late = text.replace(floor + '\n\n', '') + '\n' + floor + '\n'       # the round-1 order: floor after J2's rule
        found = r12.dru_order(late)
        self.assertTrue(any('R12 board floor: copper clearance' in i and 'Tag-Connect' in i for i in found), found)
        with tempfile.TemporaryDirectory(prefix='r12-druorder-') as d:
            path = Path(d) / 'm3.kicad_pcb'
            (Path(d) / 'm3.kicad_dru').write_text(late)
            shutil.copy2(ROOT / 'm3_design/r12/m3.kicad_pro', Path(d) / 'm3.kicad_pro')
            rep = r12.check_board(self.board, path, only={'K-rules'}, stage='placement')
            self.assertFalse(rep['ok'])
            self.assertTrue(any('follows the scoped rule' in i for i in rep['issues']), rep['issues'])
        gen = r12_sch.dru((r12_sch.INPUT / 'm3.kicad_dru').read_text())
        self.assertEqual(r12.dru_order(gen), [])
        self.assertLess(gen.index('R12 board floor: copper clearance'), gen.index('Tag-Connect contact'))

    def test_route_check_hg_cs_is_spi(self):
        rc.set_profile('r12')
        try:
            for net in ('HG_CS', 'IMU_CS', 'SD_CS', 'QSPI_NCS'):
                self.assertEqual(rc.net_class(net), 'spi', net)
                self.assertIn(rc.net_class(net), rc.SIGNAL_CRITICAL, net)
        finally:
            rc.set_profile('r8')

    def test_fit_r12_db125_terminal_tails(self):
        report = fc.check_board(self.board, ROOT / 'm3_design/r12', profile='r12')
        tails = report['terminal_tails']
        self.assertEqual((tails['count'], tails['refs'], tails['max_below_seating_mm']), (2, ['J121'], 3.8))
        rows = {ref: box for _, ref, _, box in report['rows']}
        self.assertAlmostEqual(rows['J121.1 terminal tail'][4], -3.8, places=6)
        self.assertGreater(tails['minimum_bore_margin_mm'], 0)


@unittest.skipUnless(pcbnew and BOARD12.is_file() and (BOARD12.parent / 'fab/m3_bom_jlc.csv').is_file(),
                     'KiCad python, the R12 board and its fab package required')
class FabContent(unittest.TestCase):
    """R12F3-TRI-03: the R12 package's content checks run S-4 on the exported BOM / CPL (quantity, Manufacturer Part and
    Footprint against the board's native parts), as R10's and R11's packages do; seeded on a copy of the package."""

    def s4(self, out):
        import fab_manifest_r12 as fm12
        checks = fm12.content_checks(BOARD12, out, sys.executable)
        label, argv = checks[0]
        self.assertEqual(label, 'S-4 BOM / CPL identities')
        self.assertTrue(argv[2].endswith('check_r12.py'))
        self.assertEqual(argv[4:6], ['--only', 'S-4'])
        self.assertIn('--bom', argv)
        self.assertIn('--cpl', argv)
        return subprocess.run(argv, capture_output=True, text=True, timeout=600)

    def test_s4_bound_and_run_on_the_package(self):
        import fab_manifest_r12 as fm12
        self.assertIn('tools/check_r12.py', fm12.R12_INPUTS)
        fab = BOARD12.parent / 'fab'
        ok = self.s4(fab)
        self.assertEqual(ok.returncode, 0, ok.stdout[-2000:] + ok.stderr[-2000:])
        import csv
        with tempfile.TemporaryDirectory(prefix='r12-fabmut-') as d:
            out = Path(d)
            shutil.copy2(fab / 'm3_cpl_jlc.csv', out / 'm3_cpl_jlc.csv')
            with (fab / 'm3_bom_jlc.csv').open(newline='') as src:
                reader = csv.DictReader(src)
                fields, rows = reader.fieldnames, list(reader)
            row = next(r for r in rows if r['Designator'] == 'Q122,Q123,Q124')
            row.update({'Footprint': 'R0402', 'Manufacturer Part': 'AO3401A', 'Qty': '0'})
            with (out / 'm3_bom_jlc.csv').open('w', newline='') as dst:
                w = csv.DictWriter(dst, fieldnames=fields)
                w.writeheader()
                w.writerows(rows)
            bad = self.s4(out)
        self.assertNotEqual(bad.returncode, 0)
        text = bad.stdout
        for want in ("Qty '0' must be a positive integer", "Q124 Manufacturer Part 'AO3401A' differs",
                     "Q122 Footprint 'R0402' differs"):
            self.assertIn(want, text)


class Schematic(unittest.TestCase):
    """The committed R12 netlist meets the contract and every seeded fault is caught (ERC runs in the R12 gate)."""

    @classmethod
    def setUpClass(cls):
        cls.parts, cls.pins = r12_sch_check.read_netlist(ROOT / 'm3_design/r12/schematic.net.xml')

    def test_contract_holds(self):
        self.assertEqual(r12_sch_check.contract(self.parts, self.pins, ROOT / 'm3_design/r12'), [])

    def test_seeds_are_caught(self):
        seeded = r12_sch_check.seeds(self.parts, self.pins)
        self.assertTrue(all(seeded.values()), [k for k, v in seeded.items() if not v])
        self.assertTrue(r12_sch_check.side_seed(ROOT / 'm3_design/r12'))

    def test_pin_table_current(self):
        self.assertEqual((r12_sch.DESIGN / 'pin_table.tsv').read_text(), r12_sch.pin_table_text())

    def test_inputs_pinned(self):
        r12_sch.source_check()

    def test_one_side_and_economic(self):
        data = r12_sch.circuit()
        self.assertEqual(data['assembly']['sides'], 1)
        self.assertEqual(data['owner_fit'], {})          # D-R12-85: every part JLC-assembled (owner 2026-11-05)


@unittest.skipUnless(pcbnew, 'KiCad python required')
class Library(unittest.TestCase):
    def test_library_current_and_lands(self):
        import r12_parts
        files, copied = r12_parts.generated()
        self.assertEqual(r12_parts.stale(files, copied), [])
        r12_parts.geometry_checks()


class Windows(unittest.TestCase):
    """Stage A windows: the committed JSON is the generator's and the key results hold."""

    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(r12_budget.OUT.read_text())

    def test_current(self):
        self.assertEqual(json.dumps(r12_budget.compute(), indent=1, sort_keys=True) + '\n', r12_budget.OUT.read_text())

    def test_fire_floor(self):
        self.assertGreaterEqual(self.data['fire']['four_stall_A'], 1.125)
        self.assertTrue(self.data['fire']['four_stall_ok'])

    def test_rails_inside_limits_at_initial_tolerance(self):
        for name, row in self.data['rails'].items():
            with self.subTest(rail=name):
                self.assertTrue(row['initial']['inside_limits'], row['initial'])

    def test_ovlo_and_sense(self):
        self.assertTrue(self.data['u9']['ovlo_check_ok'])
        self.assertTrue(self.data['sense']['PORT_SENSE_ok'])
        self.assertTrue(self.data['crystal']['ok'])
        self.assertTrue(self.data['vlogic']['usb_only_ok'])

    def test_crystal_range_includes_capacitor_tolerance(self):
        """R12F3-TRI-05: the gm_crit range spans C25 / C26's tolerance and 2-5 pF stray; 18 pF +5 % at 5 pF stray gave
        1.5027 mA/V, above DS12110's 1.5 mA/V Gm_critmax, so C25 / C26 are 15 pF."""
        x = self.data['crystal']
        self.assertEqual(x['C25_C26_pF'], [15.0, 15.0])
        self.assertEqual(x['C25_C26_tolerance'], [0.05, 0.05])
        self.assertEqual(x['circuit_CL_pF'], [9.125, 11.0, 12.875])
        self.assertLess(x['gm_crit_range_mA_per_V'][1], 1.5)
        self.assertGreater(x['gm_crit_18pF_5pct_corner_mA_per_V'], 1.5)
        self.assertLess(x['total_offset_ppm_bound'], x['usb_fs_limit_ppm'] / 10)

    def test_round1_labels_and_cam_input(self):
        """D-R12-86 / -87 (R12F1-TRI-03, -17): PA4 sense labelled with its drift Inference; CAM_5V input condition."""
        self.assertEqual(self.data['sense']['label'],
                         'Calculation (1 % resistors, rail windows above; DS12110 leakage); drift Inference')
        self.assertEqual((self.data['sense']['PORT_SENSE_divider']['R111_ohm'],
                          self.data['sense']['PORT_SENSE_divider']['R112_ohm']), (47e3, 100e3))
        cam = self.data['cam_input']
        self.assertIn('VO / 0.75', cam['window_holds_for'])
        self.assertTrue(cam['label'].startswith('Calculation / Inference'))
        lo, hi = cam['min_recommended_VIN_V']['initial']
        rail = self.data['rails']['CAM_5V (U403 TPS563208, R433 51k + R434 10k / R435 10k)']['initial']
        self.assertAlmostEqual(lo, rail['min_V'] / 0.75, places=3)
        self.assertAlmostEqual(hi, rail['max_V'] / 0.75, places=3)
        self.assertLess(cam['four_stall_U403_VIN_V'], lo)                 # the four-stall point is below the condition

    def test_divider_math(self):
        lo, hi = r12_budget.divider((1.0, 1.0), 1e3, 1e3, 0.0)
        self.assertEqual((lo, hi), (2.0, 2.0))
        lo, hi = r12_budget.divider((0.749, 0.787), 52e3, 10e3, 0.01)
        self.assertLess(lo, 0.749 * 6.2)
        self.assertGreater(hi, 0.787 * 6.2)


@unittest.skipUnless(pcbnew, 'KiCad python required')
class RealBoard(unittest.TestCase):
    def test_r12_board_placement_rules(self):
        path = os.environ.get('R12_BOARD')
        if not path:
            if os.environ.get('R12_BOARD_REQUIRED') == '1':
                self.fail('R12_BOARD_REQUIRED=1 but R12_BOARD is not set')
            self.skipTest('no tracked, routed R12 board supplied')
        path = Path(path).resolve()
        if not path.is_file() or not path.is_relative_to(ROOT):
            self.skipTest('R12 board is not a repository build')
        tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', str(path.relative_to(ROOT))],
                                 cwd=ROOT, capture_output=True).returncode == 0
        if not tracked:
            self.skipTest('R12 board is untracked (build output)')
        board = pcbnew.LoadBoard(str(path))
        if not any(t.GetClass() in ('PCB_TRACK', 'PCB_ARC') for t in board.GetTracks()):
            self.skipTest('R12 board is unrouted')
        report = r12.check_board(board, Path(path), stage='placement')
        self.assertTrue(report['ok'], report['issues'])


# Reuse only synthetic construction helpers; every assertion invokes the R12 rule dispatcher.
if pcbnew:
    import test_r11_check as fixtures11
    import test_r10_check as fixtures10
    import check_r10 as r10


class Four(fixtures11.Six if pcbnew else object):
    def __init__(self):
        super().__init__(length=100)
        self.board.SetCopperLayerCount(4)
        self.board.GetTitleBlock().SetRevision(r12.REVISION)
        for net in r12.reference_names():
            self.net(net)

    def run(self, only, **kw):
        return r12.check_board(self.board, kw.pop('path', r12.R12_DIR / 'm3.kicad_pcb'), only=set(only), **kw)

    def rect_fill(self, net, box, layer):
        x0, y0, x1, y1 = box
        self.net(net)
        z = self.zone(net, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer)
        z.SetFilledPolysList(layer, pcbnew.SHAPE_POLY_SET(z.Outline()))
        z.SetIsFilled(True)
        return z

    def yard(self, f, x0, y0, x1, y1):
        g = pcbnew.PCB_SHAPE(f); g.SetShape(pcbnew.SHAPE_T_RECT); g.SetLayer(pcbnew.F_CrtYd)
        g.SetStart(self.P(x0, y0)); g.SetEnd(self.P(x1, y1)); g.SetWidth(mm(.05)); f.Add(g)
        f.BuildCourtyardCaches()

    def text(self, text, x, y, layer=None):
        t = pcbnew.PCB_TEXT(self.board); t.SetText(text)
        t.SetLayer(pcbnew.F_SilkS if layer is None else layer)
        t.SetPosition(self.P(x, y)); t.SetTextSize(self.P(1, 1)); t.SetTextThickness(mm(.15))
        self.board.Add(t)
        return t

    def sh(self, ref, x, y):
        want = r12.SH_PORTS[ref]
        return self.part(ref, x, y, [(n, net, (int(n) * 2, 0), 'smd') for n, net in want.items()],
                         part=f'ZX-SH1.0-{len(want)}PWT')


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class SafetyPorts(fixtures10.SyntheticBase if pcbnew else unittest.TestCase):
    def run_rule(self, rid):
        return r12.check_board(self.board, r12.R12_DIR / 'm3.kicad_pcb', only={rid})['issues']

    def load_switch(self):
        for ref, drain, y in (('Q120', 'BAT_IN', 40), ('Q121', 'RAW_ACT', 50)):
            self.part(ref, [('1', 3, 0, 'ACT_GATE'), ('2', 2, 0, 'ACT_FET_S'), ('3', 1, 3, drain)], at=(20, y))

    def test_s1_pass_and_bypass(self):
        self.assertEqual(self.run_rule('S-1'), [])
        self.part('R999', [('1', 0, 0, 'RAW_ACT'), ('2', 2, 0, 'PYRO1_IGN')], at=(10, 10))
        self.assertTrue(self.run_rule('S-1'))

    def test_s2_pass_and_swapped_source(self):
        self.load_switch()
        self.assertEqual(self.run_rule('S-2'), [])
        self.board.FindFootprintByReference('Q121').FindPadByNumber('2').SetNet(self.board.FindNet('BAT_IN'))
        self.assertTrue(self.run_rule('S-2'))

    def test_s3_pass_and_missing_bias_or_cap(self):
        fixtures10.Synthetic.gates(self)
        u1 = self.board.FindFootprintByReference('U1')
        u1.FindPadByNumber('16').SetNumber('F2')
        q = self.board.FindFootprintByReference('Q124')
        # Change the synthetic DFN to the three-pad AO3400A package, preserving the gate-network fixture.
        for p in list(q.Pads()):
            if p.GetNumber() in ('2', '3'):
                q.Remove(p)
        for p in q.Pads():
            p.SetNumber({'1': '2', '4': '1', '5': '3'}[p.GetNumber()])
        self.assertEqual(self.run_rule('S-3'), [])
        self.board.Remove(self.local[0])
        self.assertTrue(any('copper alone' in i for i in self.run_rule('S-3')))
        self.board.Add(self.local[0])
        self.board.FindFootprintByReference('C123').SetValue('1nF')
        self.assertTrue(self.run_rule('S-3'))

    def test_s5_pass_and_switch_nc_or_bypass(self):
        fixtures10.Synthetic.power_switch(self)
        f = self.board.FindFootprintByReference('J400')
        for n in ('3', '4'):
            p = pcbnew.PAD(f); p.SetNumber(n); p.SetPosition(self.P(5, 15 + int(n))); f.Add(p)
        self.assertEqual(self.run_rule('S-5'), [])
        f.FindPadByNumber('3').SetNet(self.board.FindNet('BAT_IN'))
        self.assertTrue(self.run_rule('S-5'))
        self.board.FindFootprintByReference('R80').SetValue('0R')
        self.assertTrue(any('470k' in i for i in self.run_rule('S-5')))

    def test_s6_pass_and_port_bridge(self):
        self.part('J410', [('1', 0, 0, 'GPS_TX_MCU')], at=(15, 10))
        self.assertEqual(self.run_rule('S-6'), [])
        self.part('R999', [('1', 0, 0, 'GPS_TX_MCU'), ('2', 2, 0, 'RAW_ACT')], at=(15, 15))
        self.assertTrue(self.run_rule('S-6'))


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class PortedRules(unittest.TestCase):
    def assert_rule(self, s, rid, good=True, **kw):
        rep = s.run({rid}, **kw)
        self.assertFalse(any('check could not run' in i for i in rep['issues']), rep['issues'])
        self.assertEqual(rep['ok'], good, rep['issues'])
        self.assertIn(rid, rep['rules'])
        return rep

    @staticmethod
    def populated():
        s = Four()
        parts, _ = r12_sch.model(r12_sch.circuit())
        for i, (ref, part) in enumerate(parts.items()):
            f = pcbnew.FootprintLoad(str(LIB), part['footprint'].split(':')[1])
            f.SetReference(ref); f.SetValue(part['value']); s.board.Add(f)
            f.SetPosition(s.P(10 + 15 * (i % 10), 10 + 15 * (i // 10)))
            for k, v in part['fields'].items():
                f.SetField(k, v)
            if 'exclude_from_bom' in part['flags']:
                f.SetAttributes(f.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        return s, parts

    def test_s4_owner_fit_refused(self):
        """D-R12-85: a part named in circuit.json owner_fit (hand-fitted, off the JLC BOM) fails S-4."""
        s, _ = self.populated()
        real = r12_sch.circuit
        try:
            r12_sch.circuit = lambda: dict(real(), owner_fit={'LS120': 'hand-fitted after reflow'})
            rep = self.assert_rule(s, 'S-4', False)
        finally:
            r12_sch.circuit = real
        self.assertTrue(any('LS120 is owner-fitted' in i for i in rep['issues']), rep['issues'])

    def test_s4_population_and_assembly(self):
        s, parts = self.populated()
        self.assert_rule(s, 'S-4')
        f = s.board.FindFootprintByReference('R128')
        old = f.GetAttributes(); f.SetAttributes(old | pcbnew.FP_DNP)
        self.assert_rule(s, 'S-4', False)
        f.SetAttributes(old)
        # Both files exercise the assembly branch, including the separate owner BOM identities.
        import csv
        with tempfile.TemporaryDirectory() as tmp:
            bom = Path(tmp) / 'r12_bom_jlc.csv'; cpl = Path(tmp) / 'r12_cpl.csv'
            fields = ['Designator', 'Qty', 'LCSC Part #', 'Manufacturer Part', 'Footprint']
            rows = [dict(zip(fields, [ref, 1, p['fields'].get('LCSC', ''), p['fields'].get('Manufacturer Part', ''),
                                     p['footprint'].split(':')[1]])) for ref, p in parts.items() if 'exclude_from_bom' not in p['flags']]
            manual = set(r12_sch.circuit()['owner_fit'])
            for path, chosen in ((bom, [r for r in rows if r['Designator'] not in manual]),
                                 (bom.with_name('r12_bom_owner.csv'), [r for r in rows if r['Designator'] in manual])):
                with path.open('w') as out:
                    w = csv.DictWriter(out, fieldnames=fields); w.writeheader(); w.writerows(chosen)
            cpl.write_text('Designator\n' + '\n'.join(r['Designator'] for r in rows if r['Designator'] not in manual) + '\n')
            self.assert_rule(s, 'S-4', bom=bom, cpl=cpl)
            cpl.write_text(cpl.read_text().replace('R128\n', ''))
            self.assert_rule(s, 'S-4', False, bom=bom, cpl=cpl)

    def test_s7_and_w2_sh_ports(self):
        s = Four()
        for i, ref in enumerate(r12.SH_PORTS):
            s.sh(ref, 10, 10 + i * 10)
        for rid in ('S-7', 'W-2'):
            self.assert_rule(s, rid)
        s.board.FindFootprintByReference('J122').FindPadByNumber('6').SetNet(s.net('3V3'))
        for rid in ('S-7', 'W-2'):
            self.assert_rule(s, rid, False)
        s.board.FindFootprintByReference('J410').FindPadByNumber('1').SetNet(s.net('PORT_4V8'))
        self.assert_rule(s, 'W-2', False)

    def test_s8_foreign_inner_copper_and_rings(self):
        for layer in (pcbnew.In1_Cu, pcbnew.In2_Cu):
            for net in ('SIGNAL', 'GND'):
                with self.subTest(layer=layer, net=net):
                    s = Four(); s.via(10, 10, 'PYRO1_OUT', d=.45)
                    t = s.track((12, 8), (12, 12), net, layer, .1)
                    self.assert_rule(s, 'S-8')
                    t.Move(s.P(-1, 0)); self.assert_rule(s, 'S-8', False)
        s = Four()
        s.part('J121', 10, 10, [('1', 'PYRO1_OUT', (0, 0), 'pth')])
        # 1.1 mm from the hole wall, but only 0.7 mm from the retained ring.
        s.track((11.65, 8), (11.65, 12), 'SIGNAL', pcbnew.In2_Cu, .1)
        rep = self.assert_rule(s, 'S-8', False)
        self.assertTrue(any('inner ring' in i for i in rep['issues']))
        s = Four(); s.via(10, 10, 'RAW_ACT', d=.45)
        s.track((10.8, 8), (10.8, 12), 'GND', pcbnew.In2_Cu, .1)
        self.assert_rule(s, 'S-8')  # Original safe GND exception, not a signal exemption.

    def test_s9_current_paths(self):
        s = Four()
        paths = [('PYRO1_IGN', 'R134', 'J121'), ('PYRO1_OUT', 'J121', 'Q124'),
                 ('RAW_ACT', 'Q121', 'R134'), ('ACT_FET_S', 'Q120', 'Q121'), ('BAT_IN', 'J1', 'Q120')]
        fps, tracks = {}, []
        for i, (net, a, b) in enumerate(paths):
            for ref, x in ((a, 10), (b, 20)):
                if ref not in fps:
                    fps[ref] = s.part(ref, 0, 0, [])
                f = fps[ref]; p = pcbnew.PAD(f); p.SetNumber(str(i + 1)); p.SetNet(s.net(net))
                p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
                layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu); p.SetLayerSet(layers)
                p.SetSize(s.P(.8, .8)); p.SetPosition(s.P(x, 10 + i * 10)); f.Add(p)
            tracks.append(s.track((10, 10 + i * 10), (20, 10 + i * 10), net, width=1 if net == 'BAT_IN' else .5))
        self.assert_rule(s, 'S-9')
        for t in tracks:
            old = t.GetWidth(); t.SetWidth(mm(.3)); self.assert_rule(s, 'S-9', False); t.SetWidth(old)
        s.board.Remove(tracks[0]); self.assert_rule(s, 'S-9', False)

    def test_w1_wire_battery_and_db125_pyro(self):
        s = Four()
        for ref, nets in (('J1', ('BAT_IN', 'GND')), ('J121', ('PYRO1_OUT', 'PYRO1_IGN'))):
            s.part(ref, 10, 10 if ref == 'J1' else 20,
                   [(str(i + 1), net, (i * 5, 0), 'pth') for i, net in enumerate(nets)],
                   part='DB125-3.5-2P-BK-S' if ref == 'J121' else None)
        self.assert_rule(s, 'W-1')
        s.board.FindFootprintByReference('J121').FindPadByNumber('1').SetNet(s.net('PYRO1_IGN'))
        self.assert_rule(s, 'W-1', False)

    def test_lc1_local_floors(self):
        for ref, floor in (('R1', .15), ('J2', .508), ('TP1', 1.0)):
            s = Four(); f = s.part(ref, 10, 10, [('1', 'GND', (0, 0), 'smd')])
            f.SetLocalClearance(mm(floor)); self.assert_rule(s, 'LC-1')
            f.FindPadByNumber('1').SetLocalClearance(mm(floor - .01)); self.assert_rule(s, 'LC-1', False)

    def test_m3_recorded_supports(self):
        s = Four(); supports = [(3, 5.9), (43, 5.9), (3.5, 94.1), (42.5, 94.1)]
        for xy in supports: s.hole(*xy)
        self.assert_rule(s, 'M-3', data={'supports': supports})
        s.hole(23, 50); self.assert_rule(s, 'M-3', False, data={'supports': supports})

    def test_m6_one_side(self):
        s = Four(); f = s.part('R1', 10, 10, [('1', 'GND', (0, 0), 'smd')])
        self.assert_rule(s, 'M-6')
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM); self.assert_rule(s, 'M-6', False)

    def test_m7_sensor_geometry_without_pin_numbers(self):
        def board():
            s = Four()
            for ref, x in (('U4', 23), ('U5', 10), ('U99', 35)):
                f = s.part(ref, x, 40, [('A', 'IMU_CS' if ref == 'U4' else 'HG_CS' if ref == 'U99' else 'I2C1_SDA',
                                        (-2, 0), 'smd'), ('Z', 'GND', (2, 0), 'smd')])
                s.yard(f, x - 2, 38, x + 2, 42)
            return s
        data = {'imu': {'rotation': 0, 'lever_mm': 0}}
        s = board(); self.assert_rule(s, 'M-7', data=data)
        s.via(35, 40, 'GND'); self.assert_rule(s, 'M-7', False, data=data)
        # D-R12-52: U5 (MS5607) has R10's pad-interior track ban again.
        s = board(); s.track((9.5, 39.5), (10.5, 39.5), 'I2C1_SCL', pcbnew.F_Cu)
        self.assert_rule(s, 'M-7', False, data=data)

    def test_m8_short_edges(self):
        s = Four(); f = s.part('R1', 10, 10, [])
        s.yard(f, 9, 9, 11, 11); self.assert_rule(s, 'M-8', data={})
        f.Move(s.P(0, -8)); f.BuildCourtyardCaches(); self.assert_rule(s, 'M-8', False, data={})

    def test_k_copper_no_vippo(self):
        s = Four(); f = s.part('U401', 10, 10, [('11', 'SIGNAL', (0, 0), 'smd')])
        p = f.FindPadByNumber('11'); layers = p.GetLayerSet(); layers.AddLayer(pcbnew.F_Paste); p.SetLayerSet(layers)
        self.assert_rule(s, 'K-copper')
        s.via(10, 10, 'SIGNAL', d=.45); self.assert_rule(s, 'K-copper', False)

    def test_k_inner_mixed_layer(self):
        s = Four(); s.track((5, 5), (10, 5), 'GND', pcbnew.In1_Cu)
        t = s.track((5, 6), (10, 6), 'GPS_TX_WIRE', pcbnew.In2_Cu)
        self.assert_rule(s, 'K-inner')
        t.SetNet(s.net('SPI1_SCK')); self.assert_rule(s, 'K-inner', False)
        t.SetNet(s.net('GPS_TX_WIRE')); t.SetLayer(pcbnew.In1_Cu); self.assert_rule(s, 'K-inner', False)

    def test_k_reference_all_signal_layers(self):
        for layer, plane, net in ((pcbnew.F_Cu, pcbnew.In1_Cu, 'GND'),
                                  (pcbnew.In2_Cu, pcbnew.In1_Cu, 'GND'),
                                  (pcbnew.B_Cu, pcbnew.In2_Cu, '3V3')):
            s = Four(); t = s.track((10, 10), (20, 10), 'GPS_TX_WIRE', layer, .1)
            s.rect_fill(net, (5, 5, 25, 15), plane)
            if layer == pcbnew.In2_Cu:
                self.assert_rule(s, 'K-reference', False)  # In1 alone cannot replace the nearer B reference.
                s.rect_fill('GND', (5, 5, 25, 15), pcbnew.B_Cu)
            self.assert_rule(s, 'K-reference')
            t.Move(s.P(0, 20)); self.assert_rule(s, 'K-reference', False)

    def test_k_region_one_plane(self):
        s = Four(); s.track((10, 10), (20, 10), 'USB_DP', pcbnew.B_Cu)
        s.rect_fill('3V3', (5, 5, 25, 15), pcbnew.In2_Cu)
        self.assert_rule(s, 'K-region')
        s.rect_fill('PORT_4V8', (15, 5, 25, 15), pcbnew.In2_Cu)
        self.assert_rule(s, 'K-region', False)

    def test_k_plane_split(self):
        s = Four(); s.rect_fill('3V3', (5, 5, 15, 15), pcbnew.In2_Cu)
        self.assert_rule(s, 'K-plane')
        s.rect_fill('3V3', (20, 5, 30, 15), pcbnew.In2_Cu)
        self.assert_rule(s, 'K-plane', False)

    def test_advisory_tier(self):
        # D-R12-67A: stage C pass 1 reports K-reference / K-region / K-plane without failing; safety never relaxes.
        s = Four(); s.rect_fill('3V3', (5, 5, 15, 15), pcbnew.In2_Cu); s.rect_fill('3V3', (20, 5, 30, 15), pcbnew.In2_Cu)
        s.via(10, 30, 'PYRO1_OUT', d=.45); s.track((11, 28), (11, 32), 'SIGNAL', pcbnew.In2_Cu, .1)
        strict = s.run({'K-plane', 'S-8'})
        self.assertEqual(set(strict['failing']), {'K-plane', 'S-8'})
        rep = s.run({'K-plane', 'S-8'}, advisory=('K-plane',))
        self.assertFalse(rep['ok'])  # S-8 still fails the run
        self.assertEqual(rep['failing'], ['S-8'])
        self.assertEqual(rep['reported'], ['K-plane'])
        self.assertTrue(rep['advisory'] and all(i.startswith('K-plane: ') for i in rep['advisory']))
        self.assertFalse(any(i.startswith('K-plane') for i in rep['issues']))
        self.assertFalse(rep['rules']['K-plane']['ok'])
        only = s.run({'K-plane'}, advisory=('K-plane',))
        self.assertTrue(only['ok'], only['issues'])  # advisory findings alone pass
        for bad in (('S-8',), ('M-7',), ('W-1',), ('LC-1',), ('K-inner',), ('K-copper',), ('S-*',)):
            with self.subTest(advisory=bad), self.assertRaises(ValueError):
                s.run({'K-plane'}, advisory=bad)
        cli = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'tools/check_r12.py'), '--advisory', 'S-8'],
                             capture_output=True, text=True)
        self.assertNotEqual(cli.returncode, 0)
        self.assertIn('always fatal', cli.stderr)

    def test_k_plane_neck_floor(self):
        # D-R12-34 / -36: a 3V3 neck must be >= 1.0 mm; 1.4 mm passes, 0.6 mm fails.
        for width, ok in ((1.4, True), (.6, False)):
            s = Four()
            s.rect_fill('3V3', (5, 5, 15, 15), pcbnew.In2_Cu)
            s.rect_fill('3V3', (14.9, 10 - width / 2, 20.1, 10 + width / 2), pcbnew.In2_Cu)
            s.rect_fill('3V3', (20, 5, 30, 15), pcbnew.In2_Cu)
            s.via(10, 10, '3V3'); s.via(25, 10, '3V3')    # plane_necks judges pieces that hold a 3V3 landing
            s.fill()
            self.assert_rule(s, 'K-plane', ok)

    def test_k_fill_saved_geometry(self):
        s = Four(); z = s.rect_fill('3V3', (5, 5, 20, 20), pcbnew.In2_Cu)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER); s.fill()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'm3.kicad_pcb'; pcbnew.SaveBoard(str(p), s.board)
            self.assert_rule(s, 'K-fill', path=p)
            poly = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(pcbnew.In2_Cu)); poly.Move(s.P(1, 0))
            z.SetFilledPolysList(pcbnew.In2_Cu, poly); pcbnew.SaveBoard(str(p), s.board)
            self.assert_rule(s, 'K-fill', False, path=p)

    def test_k_legends_complete_and_wrong_sh_pin(self):
        s = Four()
        pins = dict(r12.TERMINAL_PINS)
        pins['J2'] = tuple(enumerate(r10.PORT_LEGENDS_R10['J2'], 1))
        labels = []
        for i, (ref, contacts) in enumerate(pins.items()):
            x, y = 40 + (i % 3) * 60, 30 + (i // 3) * 40
            f = s.part(ref, x, y, [(str(n), 'SIGNAL', (5 * j, 0), 'smd') for j, (n, _) in enumerate(contacts)])
            s.yard(f, x - 6, y - 5, x + 5 * (len(contacts) - 1) + 6, y + 5)
            f.Reference().SetPosition(s.P(x, y + 4)); f.Reference().SetTextSize(s.P(1, 1))
            f.Value().SetVisible(False)
            fab = pcbnew.PCB_TEXT(f); fab.SetText('${REFERENCE}'); fab.SetLayer(pcbnew.F_Fab)
            fab.SetTextSize(s.P(1, 1)); fab.SetTextThickness(mm(.15)); fab.SetPosition(s.P(x, y)); f.Add(fab)
            for j, (n, word) in enumerate(contacts):
                labels.append(s.text(f'{n}:{word}' if ref != 'J2' else f'J2 {n}:{word}', x + 5 * j, y + 2))
            for word, subject in r10.WORD_LEGENDS_R10.items():
                if subject == ref:
                    s.text(word, x + 5 * (len(contacts) - 1) / 2, y - 3)
        note = s.text(r10.SERVO_HARNESS_NOTE, 30, 150)
        s.text(r12.REVISION, 30, 160, pcbnew.B_SilkS)
        self.assert_rule(s, 'K-legends')
        labels[0].SetText('1:WRONG'); self.assert_rule(s, 'K-legends', False)
        labels[0].SetText(f'{pins["J1"][0][0]}:{pins["J1"][0][1]}'); self.assert_rule(s, 'K-legends')
        # D-R12-81: an absent harness note is waived; a conflicting or duplicated one still fails; a contact legend
        # is never waived
        note.SetText('SERVO FROM HARNESS'); self.assert_rule(s, 'K-legends', False)
        s.board.Remove(note); self.assert_rule(s, 'K-legends')
        twice = [s.text(r10.SERVO_HARNESS_NOTE, 30, 150), s.text(r10.SERVO_HARNESS_NOTE, 90, 150)]
        self.assert_rule(s, 'K-legends', False)
        for t in twice:
            s.board.Remove(t)
        self.assert_rule(s, 'K-legends')
        s.board.Remove(labels[1]); self.assert_rule(s, 'K-legends', False)

    def test_every_pending_rule_is_registered(self):
        self.assertNotIn('K-legends', r12.STAGES['copper'])  # r12_build runs routing before stage-D post.
        self.assertEqual(r12.PENDING, ())
        self.assertEqual(set(r12.IMPLEMENTED), set(r12.PORTED))
        self.assertTrue(set(r12.IMPLEMENTED) <= set(r12.STAGES['full']))


if __name__ == '__main__':
    unittest.main()
