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
import r12_fire as fire
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
        self.assertFalse(report['ok'])                       # one part on the board, 187 in the schematic
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
        # the first scoped clearance rule is the JLC SMD pad rule since R12F5-TRI-06 (Tag-Connect's before it)
        self.assertTrue(any('R12 board floor: copper clearance' in i and 'R12 JLC SMD pad to pad' in i for i in found),
                        found)
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


@unittest.skipUnless(pcbnew and BOARD12.is_file(), 'KiCad python and the R12 board required')
class FireGaps(unittest.TestCase):
    """R12F5-TRI-01 (tightened by the round 5 verifier, lane P2): S-10 carries R10's fire-net copper gaps (D-R26-02 / -04)
    and D-R11-23 to R12 on every layer, fills and barrels included, default-deny, with item-pair exceptions at their
    floors (m3_design/r12_fire.py). The committed board passes; each planted bridge-risk item fails S-10, and DRC with
    the committed DRU fails it too (the DRU is generated from the same definition)."""

    CLI = os.environ.get('KICAD_CLI') or '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'

    def setUp(self):
        self.board = pcbnew.LoadBoard(str(BOARD12))

    def s10(self):
        return r12.check_board(self.board, BOARD12, only={'S-10'}, stage='copper')

    def track(self, net, a, b, layer=None, width=0.2):
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
        t.SetWidth(mm(width)); t.SetLayer(pcbnew.F_Cu if layer is None else layer)
        if net:
            t.SetNet(self.board.FindNet(net) or self.add_net(net))
        self.board.Add(t)
        return t

    def add_net(self, name):
        n = pcbnew.NETINFO_ITEM(self.board, name)
        self.board.Add(n)
        return n

    def zone(self, net, pts, layer):
        z = pcbnew.ZONE(self.board); z.SetNet(self.board.FindNet(net)); z.SetLayer(layer)
        o = z.Outline(); o.NewOutline()
        for x, y in pts:
            o.Append(mm(x), mm(y))
        z.SetFilledPolysList(layer, pcbnew.SHAPE_POLY_SET(o)); z.SetIsFilled(True); self.board.Add(z)
        return z

    STRIP = """import pcbnew, sys
x0, y0, x1, y1 = map(float, sys.argv[2:6])
b = pcbnew.LoadBoard(sys.argv[1])
for t in list(b.GetTracks()):
    at = t.GetPosition() if t.GetClass() == 'PCB_VIA' else t.GetStart()
    if t.GetNetname() != sys.argv[6] and x0 < pcbnew.ToMM(at.x) < x1 and y0 < pcbnew.ToMM(at.y) < y1:
        b.Remove(t)
pcbnew.SaveBoard(sys.argv[1], b)
"""

    def drc_s10(self, strip=None):
        """kicad-cli DRC of the planted board with the committed DRU: the S-10 rule violations. strip (x0, y0, x1, y1,
        net): first remove, in a separate KiCad python process on the saved copy, every track and via of another net
        that starts inside the box."""
        if not Path(self.CLI).exists():
            self.skipTest('kicad-cli unavailable')
        with tempfile.TemporaryDirectory(prefix='r12-s10-') as d:
            path = Path(d) / 'm3.kicad_pcb'
            for name in ('m3.kicad_dru', 'm3.kicad_pro'):
                shutil.copy2(BOARD12.with_name(name), Path(d) / name)
            pcbnew.SaveBoard(str(path), self.board)
            if strip:
                subprocess.run([sys.executable, '-I', '-c', self.STRIP, str(path), *map(str, strip)], check=True,
                               capture_output=True, timeout=300)
            subprocess.run([self.CLI, 'pcb', 'drc', '--format', 'json', '--severity-error', '-o', str(Path(d) / 'd.json'),
                            str(path)], capture_output=True, timeout=300, check=True)
            found = json.loads((Path(d) / 'd.json').read_text())['violations']
        return [v['description'] + ' | ' + ' / '.join(i['description'] for i in v['items']) for v in found
                if "rule 'S-10" in v['description']]

    def planted(self, want, drc=None):
        """S-10 fails with an issue containing every string of want; DRC reports an S-10 violation naming drc."""
        rep = self.s10()
        self.assertFalse(rep['ok'])
        hits = [i for i in rep['issues'] if all(w in i for w in want)]
        self.assertTrue(hits, rep['issues'])
        if drc is not None:
            found = self.drc_s10()
            self.assertTrue([v for v in found if all(w in v for w in drc)], found)
        return hits

    def test_committed_board_passes_with_recorded_exceptions(self):
        rep = self.s10()
        self.assertTrue(rep['ok'], rep['issues'])
        ev = rep['evidence']['s10']
        kept = {e['pair'] for e in ev['exceptions']}
        for pair in ('PYRO1_GATE_N track (20.6, 51.6)-(18.9, 51.6) to 3V3 U1.B2 on F.Cu: 0.150',
                     'PYRO1_GATE Q124.1 to PYRO1_OUT Q124.3 on F.Cu: 1.04'):
            self.assertTrue([k for k in kept if k.startswith(pair)], pair)
        self.assertEqual(len(kept), sum(len(v) for v in fire.EXCEPTIONS.values()))       # no stale, none extra
        self.assertEqual(set(fire.EXCEPTIONS), set(fire.WHY))
        self.assertTrue(ev['u1_nc_balls'])
        self.assertTrue(all(' U1.' in p and 'unconnected-(U1-' in p for p in ev['u1_nc_balls']))
        self.assertIn('ACT_DRV', ev['netlist_classes']['sink'])
        self.assertIn('BUZZ_OUT', ev['netlist_classes']['sink'])
        self.assertIn('VLOGIC', ev['netlist_classes']['supply'])
        self.assertIn('PYRO1_CONT', ev['netlist_classes']['mcu'])

    def test_verifier_A_B_J_low_side_sinks_and_vlogic_near_out_fail(self):
        # J121.1 (7.4, 35.25), 1.9 mm land: a 0.2 mm track 0.2 mm east (round 5 verifier cases A, B, J)
        for net in ('ACT_DRV', 'BUZZ_OUT', 'VLOGIC'):
            with self.subTest(net=net):
                self.setUp()
                self.track(net, (8.65, 35.0), (8.65, 35.5))
                self.planted(('PYRO1_OUT J121.1 to ' + net, ': 0.20', 'below 1.04 mm'),
                             drc=("'S-10 PYRO1_OUT to every net'", net))

    def test_verifier_C_D_G_bridges_to_the_gate_track_fail(self):
        # PYRO1_GATE track (11.03, 44.2)-(13, 44.2), 0.2 mm wide (cases C, D: formerly the blanket-inert nets; G)
        for net, gap in (('QSPI_IO2', '0.10'), ('HSE_OUT', '0.10'), ('ACT_EN_MCU', '0.20')):
            with self.subTest(net=net):
                self.setUp()
                y = 43.95 if gap == '0.10' else 43.85
                self.track(net, (12.0, y), (12.8, y), width=0.1)
                self.planted(('PYRO1_GATE track (11.03, 44.2)-(13, 44.2) to ' + net, ': ' + gap, 'below 1.0585'),
                             drc=("'S-10 Q124 gate nets to every raising net'", net))

    def test_verifier_E_new_3v3_near_the_pe4_lane_inside_u1_fails(self):
        # the D-R11-23 exception names its item pairs: a new 3V3 track 0.15 mm south of the lane (as near as U1.B2,
        # the excepted pair's floor) is not excepted (the verifier planted 0.2 mm, touching HSE_IN)
        self.track('3V3', (18.95, 51.85), (19.1, 51.85), width=0.1)
        self.planted(('PYRO1_GATE_N track (20.6, 51.6)-(18.9, 51.6) to 3V3 track (18.95, 51.85)-(19.1, 51.85)',
                      ': 0.15', 'below 1.0585'), drc=("'S-10 Q124 gate nets to every raising net'", '[3V3]'))

    def test_verifier_F_protected_net_fill_is_measured(self):
        # a PYRO1_OUT fill on In2 over a 3V3 track: S-10 measures protected-net fills too (was one-directional)
        self.zone('PYRO1_OUT', [(30, 90), (31, 90), (31, 91), (30, 91)], pcbnew.In2_Cu)
        self.track('3V3', (30.5, 89.5), (30.5, 91.5), pcbnew.In2_Cu)
        self.planted(('PYRO1_OUT fill PYRO1_OUT to 3V3 track (30.5, 89.5)-(30.5, 91.5)', ': 0.0000 mm'),
                     drc=("'S-10 PYRO1_OUT to every net'", 'Zone [PYRO1_OUT]'))

    def test_verifier_G_H_I_still_fail(self):
        self.track('VCAP1', (8.75, 35.0), (8.75, 35.5))                               # H: 0.3 mm from J121.1
        self.planted(('PYRO1_OUT J121.1 to VCAP1', ': 0.30'), drc=("'S-10 PYRO1_OUT to every net'", 'VCAP1'))
        self.setUp()
        self.track('PORT_4V8', (8.65, 35.0), (8.65, 35.5), pcbnew.In2_Cu)            # I: In2, near J121.1's barrel
        self.planted(('PYRO1_OUT J121.1 barrel to PORT_4V8', 'In2.Cu'),
                     drc=("'S-10 PYRO1_OUT to every net'", 'PORT_4V8'))

    def test_out_to_gnd_copper_and_fill(self):
        self.track('GND', (6.25, 34.9), (6.25, 35.25))                                # 0.1 mm west of J121.1
        self.planted(('PYRO1_OUT J121.1 to GND', 'below 0.25 mm'), drc=("'S-10 PYRO1_OUT to GND'",))
        self.setUp()
        self.zone('GND', [(8.65, 35.0), (9.5, 35.0), (9.5, 35.5), (8.65, 35.5)], pcbnew.B_Cu)
        self.planted(('PYRO1_OUT J121.1 to GND fill', 'below 0.5 mm'), drc=("'S-10 PYRO1_OUT to GND fills'",))

    def test_ign_to_gnd_copper_and_fill_fail(self):
        # J121.2 (7.4, 38.75), 1.9 mm land, is RAW_ACT through R134 2 ohm: a GND bridge overloads R134 (verifier)
        self.track('GND', (7.2, 40.0), (7.6, 40.0))                                   # 0.2 mm south of J121.2
        self.planted(('PYRO1_IGN J121.2 to GND track (7.2, 40)-(7.6, 40)', ': 0.20', 'below 0.25 mm'),
                     drc=("'S-10 PYRO1_IGN to every net'", 'GND'))
        self.setUp()
        self.zone('GND', [(7.0, 40.0), (7.8, 40.0), (7.8, 40.4), (7.0, 40.4)], pcbnew.F_Cu)   # a fill 0.3 mm away
        self.planted(('PYRO1_IGN J121.2 to GND fill', ': 0.30', 'below 0.5 mm'),
                     drc=("'S-10 PYRO1_IGN to fills'", 'GND'))

    def test_ign_pours_pulled_back(self):
        # J121.2 sat 0.100 mm from GND_pour_B (B) and 0.25 mm from GND_In1: every fill now keeps 0.5 mm
        near = [r for r in r12.fire_gaps(self.board) if r['a'] == 'J121.2' and r['b'].startswith('fill ')]
        self.assertTrue(all(r['gap'] >= fire.FILL_MIN - 5e-4 for r in near), near)

    def test_nc_exemption_is_u1_balls_only(self):
        # another part's NC pad net, copper with no net and a U1 NC net on a track all count as foreign copper
        for net in ('unconnected-(D120-A2-Pad2)', '', 'unconnected-(U1-PC15-PadB1)'):
            with self.subTest(net=net):
                self.setUp()
                self.track(net, (12.0, 43.85), (12.8, 43.85), width=0.1)
                self.planted(('PYRO1_GATE track (11.03, 44.2)-(13, 44.2) to', ': 0.20', 'below 1.0585'))
                if net:
                    found = self.drc_s10()
                    self.assertTrue([v for v in found if "'S-10 Q124 gate nets to every raising net'" in v], found)

    def test_exception_floor_and_stale_entries(self):
        key = 'D-R11-23'
        kept = fire.EXCEPTIONS[key]
        try:
            fire.EXCEPTIONS[key] = tuple((a, b, layer, 0.2 if b == 'U1.B2' and floor < 0.2 else floor)
                                         for a, b, layer, floor in kept)
            self.planted(('PYRO1_GATE_N track (20.6, 51.6)-(18.9, 51.6) to 3V3 U1.B2', 'below the 0.200 mm floor'))
            fire.EXCEPTIONS[key] = kept + (('U1.C3', 'via (1, 1)', 'F.Cu', 0.5),)
            self.planted(('exception U1.C3 to via (1, 1) on F.Cu', 'stale entry'))
        finally:
            fire.EXCEPTIONS[key] = kept
        self.assertTrue(self.s10()['ok'])

    def test_moved_excepted_item_is_not_excepted(self):
        # B2's dog-bone via (19.8, 50.8) moved 0.1 mm toward the lane: a new item (fails its limit), the old pair stale
        for t in self.board.GetTracks():
            if t.GetClass() == 'PCB_VIA' and t.GetPosition() == pcbnew.VECTOR2I(mm(19.8), mm(50.8)):
                t.SetPosition(pcbnew.VECTOR2I(mm(19.8), mm(50.9)))
        hits = self.planted(('PYRO1_GATE_N track (20.6, 51.6)-(18.9, 51.6) to 3V3 via (19.8, 50.9)', 'below 1.0585'))
        self.assertTrue(hits)
        self.assertTrue(any('via (19.8, 50.8)' in i and 'stale' in i for i in self.s10()['issues']))

    def test_netlist_guard_refuses_classing_a_sink_out(self):
        kept = dict(fire.NOT_A_PATH)
        try:
            fire.NOT_A_PATH[(fire.OUT, 'ACT_DRV')] = 'planted'
            self.planted(('PYRO1_OUT / ACT_DRV is classed "not a path"', 'sink'))
        finally:
            fire.NOT_A_PATH.clear(); fire.NOT_A_PATH.update(kept)

    # ---- R12F6-TRI-02: the U1 NC-ball exemption is the gate nets' only -------------------------------------------
    def test_r12f6_tri02_nc_ball_counts_against_out_and_ign(self):
        """A U1 NC ball is foreign copper to PYRO1_OUT (1.04 mm) and PYRO1_IGN (0.25 mm), exempt only for the gate nets;
        a PYRO1_OUT track 0.38 mm (the gate lens's plant) and a PYRO1_IGN track 0.20 mm from U1.A1 (PC14, NC) fail
        S-10 and DRC. (0.38 mm is above IGN's own 0.25 mm limit, so IGN is planted below that limit.)"""
        nc = 'unconnected-(U1-PE3-PadB3)'
        self.assertEqual(fire.pair_limit(fire.OUT, None, nc, 'U1', False)[:2], (fire.OUT_MIN, 'out'))
        self.assertEqual(fire.pair_limit(fire.IGN, None, nc, 'U1', False)[:2], (fire.IGN_MIN, 'ign'))
        self.assertEqual(fire.pair_limit(fire.IGN, None, nc, 'U1', True)[:2], (fire.FILL_MIN, 'ign'))
        for gate in fire.GATES:
            self.assertEqual(fire.pair_limit(gate, None, nc, 'U1', False)[:2], (None, 'U1 NC ball'))
        rules = {r[0]: r[2] for r in fire.dru_rules()}
        for name in ('S-10 PYRO1_OUT to every net', 'S-10 PYRO1_IGN to every net', 'S-10 PYRO1_IGN to fills'):
            self.assertNotIn("unconnected-*", rules[name], name)
        self.assertIn(fire.NOT_U1_NC, rules['S-10 Q124 gate nets to every raising net'])
        # U1.A1 (19.4, 50.4), 0.4 mm land: 0.1 mm tracks north of it
        for net, y, gap, lim, rule in ((fire.OUT, 49.77, '0.38', 'below 1.04 mm', "'S-10 PYRO1_OUT to every net'"),
                                       (fire.IGN, 49.95, '0.20', 'below 0.25 mm', "'S-10 PYRO1_IGN to every net'")):
            with self.subTest(net=net):
                self.setUp()
                self.track(net, (19.3, y), (19.5, y), width=0.1)
                self.planted((f'{net} track (19.3, {y:g})-(19.5, {y:g}) to unconnected-(U1-PC14-PadA1) U1.A1',
                              ': ' + gap, lim))
                # KiCad reports at most one clearance violation for a track against several items of one footprint or
                # net (lane P2's DRC quirk), so the DRC probe strips the other nets' tracks and vias round U1's A1
                # corner first (on the saved copy): U1's pads stay, and the NC ball must then be reported.
                found = self.drc_s10(strip=(17, 47, 23, 51, net))
                self.assertTrue([v for v in found if rule in v and 'U1-PC14-PadA1' in v and net in v], found)

    # ---- R12F6-TRI-01: the cold pull-up through R136, and the commanded-fire state -------------------------------
    def netlist(self, mutate):
        """A temporary copy of the committed netlist with mutate(root) applied (the board stays the committed one)."""
        import xml.etree.ElementTree as ET
        tree = ET.parse(BOARD12.with_name('schematic.net.xml'))
        mutate(tree.getroot())
        d = tempfile.mkdtemp(prefix='r12-net-')
        self.addCleanup(shutil.rmtree, d, True)
        path = Path(d) / 'schematic.net.xml'
        tree.write(path)
        return path

    @staticmethod
    def move_node(root, ref, pin, net):
        node = parent = None
        for n in root.findall('./nets/net'):
            for x in n.findall('node'):
                if (x.get('ref'), x.get('pin')) == (ref, pin):
                    node, parent = x, n
        parent.remove(node)
        next(n for n in root.findall('./nets/net') if n.get('name') == net).append(node)

    @staticmethod
    def set_value(root, ref, value):
        next(c for c in root.findall('./components/comp') if c.get('ref') == ref).find('value').text = value

    def s10_netlist(self, path):
        return r12.check_board(self.board, BOARD12, only={'S-10'}, stage='copper', netlist=path)

    def test_r12f6_tri01_cold_pullup_holds_in_the_fire_state(self):
        """The committed netlist: 3V3 -> R136 5.1k -> D120.1 (PYRO1_COLD_PU) -> PYRO1_COLD -> R131 5.1k -> PYRO1_OUT, so
        a bridge across R131 while Q124 conducts meets R136; CONT_MID meets R129; each class reason covers Q124 on."""
        parts, pins = r12_sch_check.read_netlist(BOARD12.with_name('schematic.net.xml'))
        self.assertEqual((pins['R136', '1'], pins['R136', '2'], pins['D120', '1'], pins['D120', '3'], pins['R131', '2'],
                          pins['R131', '1']), ('3V3', 'PYRO1_COLD_PU', 'PYRO1_COLD_PU', 'PYRO1_COLD', 'PYRO1_COLD',
                                               'PYRO1_OUT'))
        self.assertEqual((parts['R131']['value'], parts['R136']['value']), ('5.1k', '5.1k'))
        ev = self.s10()['evidence']['s10']['fire_state']
        self.assertEqual(ev['series_ohm']['PYRO1_COLD'], {'3V3': 5100.0})
        self.assertEqual(ev['series_ohm']['PYRO1_CONT_MID'], {'PYRO1_CONT': 5100.0})
        self.assertEqual(ev['series_ohm']['D120.1'], 'PYRO1_COLD_PU')
        for (p, f), why in fire.NOT_A_PATH.items():
            if p == fire.OUT and f not in ('GND',) + fire.PROTECTED:
                self.assertIn('Q124 on', why, f)
        self.assertNotIn((fire.OUT, 'PYRO1_COLD_PU'), fire.NOT_A_PATH)     # held at OUT_MIN like every net

    def test_r12f6_tri01_anode_on_3v3_fails(self):
        """D120's anode planted back on 3V3 (round 6's circuit): S-10's netlist guard fails twice (the anode itself, and
        the PYRO1_COLD class at 0 ohm in the fire state), and S-2 refuses D120 as an unnamed armed-side supply tie."""
        path = self.netlist(lambda root: self.move_node(root, 'D120', '1', '3V3'))
        rep = self.s10_netlist(path)
        self.assertFalse(rep['ok'])
        self.assertTrue([i for i in rep['issues'] if "D120.1 (the cold pull-up diode's anode) is on 3V3 itself" in i],
                        rep['issues'])
        self.assertTrue([i for i in rep['issues'] if 'PYRO1_OUT / PYRO1_COLD is classed "not a path"' in i
                         and 'joins 3V3 to GND through only 0 ohm' in i], rep['issues'])
        for pad in self.board.FindFootprintByReference('D120').Pads():
            if pad.GetNumber() == '1':
                pad.SetNet(self.board.FindNet('3V3'))
        s2 = r12.check_board(self.board, BOARD12, only={'S-2'}, stage='copper')
        self.assertTrue([i for i in s2['issues'] if 'D120 has pads on the armed / RAW_ACT side net PYRO1_COLD and on the '
                         'supply 3V3' in i], s2['issues'])

    def test_r12f6_tri01_series_resistor_bypassed_or_too_small_fails(self):
        for value, ohm in (('0', '0'), ('1k', '1000')):
            with self.subTest(value=value):
                path = self.netlist(lambda root: self.set_value(root, 'R136', value))
                rep = self.s10_netlist(path)
                self.assertTrue([i for i in rep['issues'] if 'PYRO1_COLD' in i and f'through only {ohm} ohm' in i],
                                rep['issues'])

    def test_r12f6_tri01_new_class_must_hold_with_q124_on(self):
        """A planted not-a-path class the older guard passes (LED_RED_A is no rail, sink or MCU pin) fails the fire-state
        guard: PE4's neighbour LED_RED reaches it through R32 220 ohm."""
        kept = dict(fire.NOT_A_PATH)
        try:
            fire.NOT_A_PATH[(fire.OUT, 'LED_RED_A')] = 'planted'
            self.assertEqual(fire.guard(fire.netlist_classes(BOARD12.with_name('schematic.net.xml'))), [])
            self.planted(('PYRO1_OUT / LED_RED_A is classed "not a path"', 'joins LED_RED to GND through only 220 ohm'))
        finally:
            fire.NOT_A_PATH.clear(); fire.NOT_A_PATH.update(kept)
        self.assertTrue(self.s10()['ok'])

    def test_r12f6_tri01_cold_pullup_node_held_from_out(self):
        """PYRO1_COLD_PU is not classed out: its copper 0.2 mm from J121.1 fails S-10 and DRC like any net."""
        self.track('PYRO1_COLD_PU', (8.65, 35.0), (8.65, 35.5))
        self.planted(('PYRO1_OUT J121.1 to PYRO1_COLD_PU', ': 0.20', 'below 1.04 mm'),
                     drc=("'S-10 PYRO1_OUT to every net'", 'PYRO1_COLD_PU'))

    def test_dru_is_generated_from_s10(self):
        """The DRU's S-10 rules are r12_fire.dru_rules(), in order after R11's scoped rules, with general limits at least
        S-10's; each exception names its two items and its floor (kicad-cli matches them: the build's DRC is 0)."""
        text = BOARD12.with_suffix('.kicad_dru').read_text()
        rules = fire.dru_rules()
        at = [text.index(f'(rule "{r[0]}"') for r in rules]
        self.assertEqual(at, sorted(at))
        self.assertGreater(at[0], text.index('R9 bare test pads to foreign copper'))
        for r in rules:
            self.assertIn(fire.dru_text(r), text)
        self.assertGreaterEqual(fire.DRU_GATE_MM, fire.GATE_MIN)
        self.assertEqual(len(rules), 6 + sum(len(v) for v in fire.EXCEPTIONS.values()))
        for key, pairs in fire.EXCEPTIONS.items():
            for a, b, layer, floor in pairs:
                self.assertIn(f'(rule "S-10 exception ({key}): {a} to {b} on {layer}"\n  (layer "{layer}")', text)
                self.assertLess(floor, fire.GATE_MIN)
        self.assertLess(text.index('R12 JLC SMD pad to pad'), text.index('Tag-Connect contact'))
        self.assertIs(r12.fire, fire)
        self.assertEqual(r12_sch.FIRE_RULES, tuple(rules))

    def test_u6_corner_lands_clear_jlc_limits(self):
        """R12F5-TRI-06: U6's corner lands (NXP's chamfered land) keep >= 0.15 mm pad to pad and >= 0.10 mm mask web."""
        f = self.board.FindFootprintByReference('U6')
        pads = {p.GetNumber(): p for p in f.Pads()}

        def gap(a, b):
            lo, hi = 0, mm(0.5)
            while hi - lo > 100:
                mid = (lo + hi) // 2
                lo, hi = (lo, mid) if a.Collide(b, mid) else (mid, hi)
            return hi / 1e6

        def mask(p):
            s = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(s, pcbnew.F_Mask, p.GetSolderMaskExpansion(pcbnew.F_Mask), mm(0.001),
                                      pcbnew.ERROR_OUTSIDE)
            return s
        for a, b in (('4', '5'), ('8', '9'), ('12', '13'), ('16', '1')):
            with self.subTest(pair=(a, b)):
                pa, pb = pads[a], pads[b]
                self.assertGreaterEqual(gap(pa.GetEffectiveShape(pcbnew.F_Cu), pb.GetEffectiveShape(pcbnew.F_Cu)), 0.15)
                self.assertGreaterEqual(gap(mask(pa), mask(pb)), 0.10)
        self.assertIn('R12 JLC SMD pad to pad (different nets)', BOARD12.with_suffix('.kicad_dru').read_text())


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

    def test_r12f6_tri09_port_pin_names(self):
        """R12F6-TRI-09 (R10 test_r27_port_terminal_pin_names, ported): the SH ports' pin names are D-R12-31's order
        (1 GND, 2 4V8, 3 TXO, 4 RXI; J410 5-6 NC) on their own symbols, each name on the net it names; R11's
        PortTerminal names, the servo symbol on J410 and the other seeded name faults are caught."""
        names = r12_sch_check.read_pin_names(ROOT / 'm3_design/r12/schematic.net.xml')
        self.assertEqual(r12_sch_check.terminal_pin_issues(names), [])
        seeded = r12_sch_check.name_seeds(names)
        self.assertEqual(len(seeded), 5)
        self.assertTrue(all(seeded.values()), seeded)
        data = r12_sch.circuit()
        self.assertEqual({ref: data['parts'][ref]['lib'] for ref in ('J410', 'J420', 'J440')},
                         {'J410': 'M3:PortSH6', 'J420': 'M3:PortSH4', 'J440': 'M3:PortSH4'})
        self.assertEqual({names['J410', p][0] for p in '56'}, {'NC'})
        lib = (ROOT / 'm3_design/r12/kilib/m3.kicad_sym').read_text()
        sheets = ''.join((ROOT / 'm3_design/r12' / s).read_text() for s in r12_sch.SHEET_FILES)
        for name in ('PortSH4', 'PortSH6', 'ServoGH6', 'SwitchGH4', 'CameraGH6'):
            s = lib.index(f'\t(symbol "{name}"\n')
            descr = lib[s:lib.index('(property "ki_keywords"', s)]
            self.assertIn('ZX-SH1.0', descr, name)
        self.assertNotIn('GH-1.25', sheets)
        self.assertNotIn('SM06B-GHS', sheets)
        self.assertNotIn('SM04B-GHS', sheets)

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
