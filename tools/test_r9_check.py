"""R9 gate regressions (tools/check_r9.py and its tools): every rule passes on a clean base and fails on a seeded defect
(r9_plan.md section 4 step 1). Bases: small synthetic boards for the spacing rules, and the R8 board read from git
(commit R8_COMMIT, the owner-accepted R8) for the rules that need the real parts. Where R8 itself fails a rule (R9's
contract is stricter), the test first repairs R8 in memory, shows the rule then passes, and seeds the defect.
Run from tools/ with KiCad's Python: python3 -m unittest test_r9_check"""
import copy
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'm3_design'))
import gcpw_solve as G                                          # noqa: E402 (plain python3)
try:
    import pcbnew
except ImportError:
    pcbnew = None
if pcbnew:
    import check_r9 as C9                                       # noqa: E402
    import pyro_probe as PP                                     # noqa: E402
    import bridge_table as BT                                   # noqa: E402
    import rule_h_seed as RS                                    # noqa: E402
    import tab_windows as TW                                    # noqa: E402
    import fit_check as FC                                      # noqa: E402
    import route_check as RC                                    # noqa: E402
    MM, mm = pcbnew.FromMM, pcbnew.ToMM

R8_COMMIT = '9c8179b'
R8_SHA = 'cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7'
# the rules R8 fails under the R9 contract, each for a recorded reason (r9_step1_handoff.md, "R8 against check_r9";
# step 2 adds K-contract: R8 has the base footprints, R9 the owner-decided variants, r9_step2_handoff.md, D-S2-12)
R8_FAILING = {'LC-1', 'P-0', 'P-1', 'P-3', 'P-5', 'P-6', 'P-7', 'P-9', 'P-10', 'P-11', 'R-1', 'R-4', 'R-7', 'M-2',
              'M-6', 'K-contract', 'K-power-pyro', 'K-inner'}
_R8 = {}


def r8_folder():
    """The R8 project files from git in a scratch folder (kilib linked for the 3D models)."""
    if 'dir' not in _R8:
        d = Path(tempfile.mkdtemp(prefix='r9_test_'))
        for name in ('m3.kicad_pcb', 'm3.kicad_pro', 'm3.kicad_dru'):
            data = subprocess.run(['git', '-C', str(ROOT), 'show', f'{R8_COMMIT}:m3_design/assembly_review/{name}'],
                                  capture_output=True, check=True).stdout
            (d / name).write_bytes(data)
        (d / 'kilib').symlink_to(ROOT / 'm3_design/assembly_review/kilib')
        _R8['dir'] = d
    return _R8['dir']


def tearDownModule():
    if 'dir' in _R8:
        shutil.rmtree(_R8['dir'], ignore_errors=True)


def joined(issues):
    return '\n'.join(issues)


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class Base(unittest.TestCase):
    # --- R8 base ---------------------------------------------------------------------------------------------------
    def r8(self):
        return pcbnew.LoadBoard(str(r8_folder() / 'm3.kicad_pcb'))

    def dru(self):
        return (r8_folder() / 'm3.kicad_dru').read_text()

    def rule(self, rid, board, real=True, **kw):
        folder = r8_folder() if real else None
        path = folder / 'm3.kicad_pcb' if real else None
        kw.setdefault('dru', self.dru() if real else '')
        rep = C9.check_board(board, folder, path, only={rid}, **kw)
        return rep['rules'][rid]['issues']

    def assertPasses(self, rid, board, **kw):
        found = self.rule(rid, board, **kw)
        self.assertEqual(found, [], f'{rid} should pass: {found[:5]}')

    def assertFails(self, rid, board, word=None, **kw):
        found = self.rule(rid, board, **kw)
        self.assertTrue(found, f'{rid} should fail')
        if word:
            self.assertIn(word, joined(found))
        return found

    # --- R8 edits --------------------------------------------------------------------------------------------------
    def P(self, x, y):
        return pcbnew.VECTOR2I(MM(x), MM(y))

    def move(self, b, ref, dx, dy):
        f = b.FindFootprintByReference(ref)
        f.Move(self.P(dx, dy))
        f.BuildCourtyardCaches()
        return f

    def place(self, b, ref, x, y, rot=None):
        f = b.FindFootprintByReference(ref)
        f.SetPosition(self.P(x, y))
        if rot is not None:
            f.SetOrientationDegrees(rot)
        f.BuildCourtyardCaches()
        return f

    def add_track(self, b, a, c, net, width=0.2, layer=None):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(self.P(*a)); t.SetEnd(self.P(*c)); t.SetWidth(MM(width))
        t.SetLayer(pcbnew.F_Cu if layer is None else layer)
        t.SetNet(b.FindNet(net)); b.Add(t)
        return t

    def add_via(self, b, x, y, net='GND', d=0.6):
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(self.P(x, y)); v.SetWidth(MM(d)); v.SetDrill(MM(0.3)); v.SetNet(b.FindNet(net)); b.Add(v)
        return v

    def vias_at(self, b, x, y, net=None, tol=0.02):
        return [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and (net is None or t.GetNetname() == net)
                and abs(mm(t.GetPosition().x) - x) < tol and abs(mm(t.GetPosition().y) - y) < tol]

    def remove(self, b, items):
        """Take tracks and vias out of play by moving them 300 mm off the board: BOARD.Remove() on a loaded board
        corrupts KiCad 10's SWIG type table once the board is freed (later boards come back as bare SwigPyObjects)."""
        for it in list(items):
            it.Move(self.P(300, 300))

    def renet(self, zones, net, b):
        for z in zones:
            z.SetNet(b.FindNet(net))

    def park(self, b, ref=None, item=None):
        it = b.FindFootprintByReference(ref) if ref else item
        it.SetPosition(self.P(300, 300))
        if ref:
            it.BuildCourtyardCaches()
        return it

    def area(self, b, name):
        return [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == name]

    def set_outline(self, z, box):
        o = z.Outline()
        o.RemoveAllContours()
        o.NewOutline()
        x0, y0, x1, y1 = box
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            o.Append(MM(x), MM(y))

    def scoped_dru(self):
        """R8's DRU with rule G's P-1b scope (what R9 step 2 writes)."""
        d = self.dru()
        g = C9.rule_text(d, C9.RULE_G)
        return d.replace(g, g.replace("A.intersectsArea('PYRO_BLOCK')", C9.G_SCOPE))

    # --- synthetic boards ------------------------------------------------------------------------------------------
    NETS = ('GND', '3V3', 'RAW_ACT', 'RAW_ACT_SENSE', 'RAW_ACT_SENSE_MID', 'BAT_IN', 'ACT_GATE', 'ACT_FET_S',
            'PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT', 'PYRO1_GATE', 'PYRO1_GATE_N', 'PYRO1_CONT', 'PYRO1_CONT_MID',
            'ARM1_SENSE', 'ARM1_SENSE_MID', 'ARM1_SENSE_MCU', 'SERVO1_MCU', 'SIGNAL')

    def synth(self):
        b = pcbnew.BOARD()
        self._synth = b
        for a, c in (((0, 0), (46, 0)), ((46, 0), (46, 100)), ((46, 100), (0, 100)), ((0, 100), (0, 0))):
            e = pcbnew.PCB_SHAPE(b); e.SetShape(pcbnew.SHAPE_T_SEGMENT); e.SetLayer(pcbnew.Edge_Cuts)
            e.SetStart(self.P(*a)); e.SetEnd(self.P(*c)); b.Add(e)
        b.SetCopperLayerCount(4)
        for n in self.NETS:
            b.Add(pcbnew.NETINFO_ITEM(b, n))
        return b

    def fp(self, b, ref, x, y, court=None, side='F'):
        f = pcbnew.FOOTPRINT(b)
        f.SetReference(ref)
        b.Add(f)
        f.SetPosition(self.P(x, y))
        if court:
            w, h = court
            s = pcbnew.PCB_SHAPE(f); s.SetShape(pcbnew.SHAPE_T_RECT)
            s.SetLayer(pcbnew.F_CrtYd if side == 'F' else pcbnew.B_CrtYd)
            s.SetStart(self.P(x - w / 2, y - h / 2)); s.SetEnd(self.P(x + w / 2, y + h / 2)); s.SetWidth(MM(0.05))
            f.Add(s)
            f.BuildCourtyardCaches()
        return f

    def pad(self, f, num, x, y, net, size=(0.5, 0.5), face='F', board=None):
        p = pcbnew.PAD(f)
        p.SetNumber(str(num)); p.SetShape(pcbnew.PAD_SHAPE_RECT); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        p.SetSize(self.P(*size))
        ls = pcbnew.LSET()
        for lay in ((pcbnew.F_Cu, pcbnew.F_Mask) if face == 'F' else (pcbnew.B_Cu, pcbnew.B_Mask)):
            ls.AddLayer(lay)
        p.SetLayerSet(ls)
        p.SetNet((board or self._synth).FindNet(net))
        f.Add(p)
        p.SetPosition(self.P(x, y))
        return p

    def track(self, b, a, c, net, width=0.2, layer=None):
        return self.add_track(b, a, c, net, width, layer)


# ======================================================================================================================
class Tools(Base):
    def test_gcpw_solver_reproduces_pass2(self):
        rows = G.validate()
        for r in rows:
            self.assertLessEqual(abs(r['diff_ohm']), 1.0, r)
        coated = next(r for r in rows if r['case'] == 'gcpw_coated')
        self.assertLessEqual(abs(coated['solved_ohm'] - 50.3), 1.0)

    def test_gcpw_monotone_and_bend_limit(self):
        z = [G.z0(0.30, g)['z0_ohm'] for g in (0.25, 0.30, C9.R5_BEND_GAP)]
        self.assertLess(z[0], z[1])
        self.assertLess(z[1], z[2])
        self.assertLessEqual(z[2], 52.3)                       # R-5's re-solved bend limit stays inside 50 +- 2.5
        self.assertGreaterEqual(z[0], 47.5)

    def test_reset_voltage_model(self):
        self.assertAlmostEqual(BT.gate_voltage('ARM1_SENSE', 'PYRO1_GATE_N'), 0.367, places=3)   # R8P1-PYRO-04
        self.assertLess(BT.gate_voltage('ARM1_SENSE_MCU', 'PYRO1_GATE_N'), BT.GATE_RESET_MAX)
        self.assertGreater(BT.gate_voltage('3V3', 'PYRO1_GATE'), 3.0)
        self.assertEqual(BT.gate_voltage('GND', 'PYRO1_GATE'), 0.0)
        self.assertEqual(BT.gate_voltage('unconnected-(U1-PE3-Pad2)', 'PYRO1_GATE_N'), 0.0)

    def test_route_check_r9_profile_is_empty(self):
        try:
            RC.set_profile('r9')
            self.assertEqual((RC.ALLOWLIST, RC.LEFTOVERS, RC.ROUTE_FIGURES), ([], [], {}))
            self.assertTrue(RC.KEEPOUT_BASELINE)
        finally:
            RC.set_profile('r8')
        self.assertTrue(RC.ALLOWLIST)                         # r8's own list is untouched

    def test_retention_holes_derived_from_j122(self):
        b = self.r8()
        holes, problems, info = FC.retention_holes(b, with_info=True)
        self.assertEqual(problems, [])
        self.assertEqual(sorted((round(x, 2), round(y, 2)) for x, y in holes), sorted(FC.RETENTION_HOLES))
        d = next(d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE
                 and abs(mm(d.GetCenter().y) - 68.6) < 0.01)
        d.Move(self.P(0, -5))                                 # 6.6 mm past the courtyard end
        self.assertTrue(FC.retention_holes(b, with_info=True)[1])

    def test_tab_windows_on_r8(self):
        b = self.r8()
        issues, ev = TW.check(b)
        self.assertEqual(issues, [])
        self.assertEqual(ev['windows']['west'], [(0.5, 6.0), (48.5, 77.25), (86.25, 117.5)])
        self.assertEqual(ev['windows']['east'], [(0.5, 23.0), (104.25, 117.5)])

    def test_rule_h_variants_each_change_the_rule(self):
        v = RS.dru_variants(self.dru())
        self.assertEqual(set(v), {'seed', 'pad_override', 'min_lowered', 'deleted', 'moved_first', 'narrowed',
                                  'raw_dropped', 'act_gate_dropped'})
        for name, text in v.items():
            if name not in ('seed', 'pad_override'):
                self.assertNotEqual(text, self.dru(), name)

    def test_rule_h_seed_places_the_pair_inside_rule_h(self):
        b = self.r8()
        moved, g = RS.seed(b, 'Q124', '5', 'R129', '2', pcbnew.F_Cu)
        self.assertEqual(moved, 'R129')
        self.assertAlmostEqual(g, RS.SEED_GAP, delta=0.004)

    @unittest.skipUnless(shutil.which('kicad-cli') or Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli').exists(),
                         'kicad-cli required')
    def test_rule_h_seeded_suite_end_to_end(self):
        # one pair, eight variants: DRC catches the plain seed, check_actuators every rule edit, LC-1 the override
        report, issues = RS.run(r8_folder() / 'm3.kicad_pcb', pairs=1)
        self.assertEqual(issues, [])
        v = report['pairs'][0]['variants']
        self.assertIn('DRC', v['seed']['caught_by'])
        self.assertNotIn('DRC', v['pad_override']['caught_by'])      # the override blinds DRC (D-S1-01) ...
        self.assertIn('check_r9 LC-1', v['pad_override']['caught_by'])   # ... and LC-1 catches it
        for name in ('min_lowered', 'deleted', 'moved_first', 'narrowed'):
            self.assertIn('check_actuators', v[name]['caught_by'], name)
        self.assertTrue(all('pyro_probe' in x['caught_by'] for x in v.values()))

    def test_check_actuators_15b_is_rule_based(self):
        import check_actuators as CA
        text, dru = (r8_folder() / 'm3.kicad_pcb').read_text(), self.dru()
        old = re.search(r'\(name "PYRO_BLOCK"\).*?\(polygon\s*\(pts((?:\s*\(xy [^)]*\))+)\s*\)', text, re.S)
        self.assertIsNotNone(old)

        def with_pts(pts, extra=''):
            new = ' '.join(f'(xy {x} {y})' for x, y in pts)
            return text[:old.start(1)] + ' ' + new + ' ' + text[old.end(1):]
        b15 = lambda t: [i for i in CA.check(t, dru) if 'PYRO_BLOCK' in i]      # noqa: E731
        self.assertTrue(b15(text))                            # R8's rectangle misses J121 / J124 / D120 + 1 mm
        big = [(2, 76), (44, 76), (44, 118), (2, 118)]
        self.assertEqual(b15(with_pts(big)), [])
        notch = [(2, 76), (44, 76), (44, 118), (12, 118), (12, 95), (2, 95)]       # a notch into J124's corner
        self.assertIn('J124', joined(b15(with_pts(notch))))
        t = with_pts(big)
        i = t.index('(tracks allowed)', t.index('(name "PYRO_BLOCK")'))
        t = t[:i] + '(tracks not_allowed)' + t[i + len('(tracks allowed)'):]
        self.assertTrue(b15(t))


# ======================================================================================================================
class SpacingRules(Base):
    """P-0 rule by rule on synthetic pads and tracks: just under the minimum fails, just over passes."""

    def probe(self, b, name):
        return PP.probe(b, rules={name: PP.RULES[name]})[name]['violation_count']

    def pair(self, na, nb, gap, kind='pad-pad', refs=('X1', 'X2'), w=0.2, layer=pcbnew.F_Cu if pcbnew else None):
        b = self.synth()
        self.fp(b, 'U1', 40, 90, court=(14, 14))              # P-1b: far from the pairs
        fa = self.fp(b, refs[0], 10, 10)
        self.pad(fa, 1, 10, 10, na)
        if kind == 'pad-pad':
            fb = fa if refs[1] == refs[0] else self.fp(b, refs[1], 10.5 + gap, 10)
            self.pad(fb, 2, 10.5 + gap, 10, nb)
        else:
            x = 10.25 + gap + w / 2
            self.track(b, (x, 9), (x, 11), nb, w, layer)
        return b

    def test_each_dru_rule(self):
        cases = [('A', 'RAW_ACT', 'ARM1_SENSE', 0.5, 'track'), ('B', 'PYRO1_OUT', 'PYRO1_GATE', 0.5, 'track'),
                 ('C', 'PYRO1_BUS', 'PYRO1_CONT_MID', 0.3, 'track'), ('D', 'GND', 'PYRO1_IGN', 0.5, 'pad-pad'),
                 ('E', 'RAW_ACT', 'PYRO1_BUS', 1.0, 'pad-pad'), ('F', 'PYRO1_OUT', '3V3', 0.5, 'track'),
                 ('G', 'PYRO1_GATE_N', 'SERVO1_MCU', 0.3, 'track'), ('A2', 'RAW_ACT', 'RAW_ACT_SENSE', 0.3, 'track'),
                 ('H', 'PYRO1_OUT', 'PYRO1_CONT', 1.0, 'pad-pad'), ('H+', 'PYRO1_BUS', 'ARM1_SENSE', 1.2, 'pad-pad'),
                 ('GS', 'PYRO1_GATE', 'ARM1_SENSE_MID', 1.2, 'pad-pad'), ('AG', 'ACT_GATE', 'GND', 1.2, 'pad-pad')]
        for name, na, nb, mn, kind in cases:
            with self.subTest(rule=name):
                self.assertTrue(self.probe(self.pair(na, nb, mn - 0.05, kind), name), f'{name} missed a seeded pair')
                self.assertFalse(self.probe(self.pair(na, nb, mn + 0.05, kind), name), f'{name} flagged a legal pair')

    def test_own_part_exemptions_match_the_dru(self):
        self.assertFalse(self.probe(self.pair('PYRO1_OUT', 'PYRO1_GATE', 0.2, refs=('Q124', 'Q124')), 'B'))
        self.assertTrue(self.probe(self.pair('PYRO1_OUT', 'PYRO1_GATE', 0.2, refs=('R900', 'R901')), 'B'))
        self.assertFalse(self.probe(self.pair('ACT_GATE', 'GND', 0.4, refs=('Q121', 'Q121')), 'AG'))

    def test_gate_rule_scope_clips_u1(self):
        b = self.pair('PYRO1_GATE_N', 'SERVO1_MCU', 0.2, 'track')
        self.assertTrue(self.probe(b, 'G'))
        u1 = b.FindFootprintByReference('U1')
        u1.SetPosition(self.P(10.3, 10)); u1.BuildCourtyardCaches()        # the pair now inside U1's courtyard
        self.assertFalse(self.probe(b, 'G'))

    def test_p0_rule_reports_through_check_r9(self):
        self.assertFails('P-0', self.pair('RAW_ACT', 'PYRO1_BUS', 0.8), 'pyro rule E', real=False)


# ======================================================================================================================
class PyroRules(Base):
    def test_lc1_board_wide(self):
        b = self.r8()
        self.assertFails('LC-1', b, 'J124.2')                 # R8's 0.3 mm override on the ARM terminal's RAW pin
        for f in b.GetFootprints():
            for p in f.Pads():
                p.SetLocalClearance(None)
        self.assertPasses('LC-1', b)
        b.FindFootprintByReference('J124').FindPadByNumber('1').SetLocalClearance(MM(0.3))   # an armed-pad override
        self.assertFails('LC-1', b, 'J124.1 (PYRO1_BUS)')
        b.FindFootprintByReference('J124').FindPadByNumber('1').SetLocalClearance(None)
        b.FindFootprintByReference('C120').FindPadByNumber('2').SetLocalClearance(MM(0.2))   # any net, not only pyro
        self.assertFails('LC-1', b, 'C120.2')
        b.FindFootprintByReference('C120').FindPadByNumber('2').SetLocalClearance(None)
        b.FindFootprintByReference('U3').SetLocalClearance(MM(0.1))
        self.assertFails('LC-1', b, 'footprint U3')

    def repaired_block(self):
        b = self.r8()
        self.set_outline(self.area(b, 'PYRO_BLOCK')[0], (2, 76, 44, 118))
        return b

    def test_p1_block_area_by_content(self):
        self.assertFails('P-1', self.r8(), 'D120')            # R8's R4-era rectangle misses D120 and the terminals + 1 mm
        b = self.repaired_block()
        self.assertPasses('P-1', b, dru=self.scoped_dru())
        self.assertFails('P-1', b, 'P-1b')                    # R8's DRU: rule G only inside PYRO_BLOCK
        self.set_outline(self.area(b, 'PYRO_BLOCK')[0], (12, 76, 44, 118))
        self.assertFails('P-1', b, 'J124 courtyard', dru=self.scoped_dru())
        b = self.repaired_block()
        self.area(b, 'PYRO_BLOCK')[0].SetDoNotAllowTracks(True)
        self.assertFails('P-1', b, 'restrict nothing', dru=self.scoped_dru())
        b = self.repaired_block()
        z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName('PYRO_BLOCK')
        z.SetLayerSet(self.area(b, 'PYRO_BLOCK')[0].GetLayerSet())
        b.Add(z)
        self.set_outline(z, (30, 30, 35, 35))
        self.assertFails('P-1', b, 'exactly one', dru=self.scoped_dru())

    def test_p2_armed_live_confined(self):
        b = self.r8()
        self.assertPasses('P-2', b)
        self.add_track(b, (30, 60), (30, 62), 'PYRO1_IGN')
        self.assertFails('P-2', b, 'PYRO1_IGN')

    def repaired_purity(self):
        b = self.r8()
        ctx = C9.Ctx(b, r8_folder(), r8_folder() / 'm3.kicad_pcb')
        hull = C9.ch1_hull(ctx)
        drop = []
        for t in b.GetTracks():
            n = t.GetNetname()
            if C9.CH1_NET.match(n) or n == 'GND' or (n in ('RAW_ACT', '3V3') and t.GetClass() != 'PCB_VIA'
                                                     and t.GetLayer() == pcbnew.F_Cu):
                continue
            if any(pcbnew.SHAPE.Collide(hull, t.GetEffectiveShape(lay), MM(1.0)) for lay in
                   b.GetEnabledLayers().CuStack() if t.IsOnLayer(lay)):
                drop.append(t)
        self.remove(b, drop)
        self.park(b, 'TP84')
        self.renet([z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() in ('ACT_FET_S', 'BAT_IN', 'RAW_ACT')
                    and not z.IsOnLayer(pcbnew.F_Cu)], 'GND', b)          # R8's B.Cu / In2 power pours under the block
        return b

    def test_p3_block_purity(self):
        self.assertFails('P-3', self.r8(), 'BAT_ENABLE')
        b = self.repaired_purity()
        self.assertPasses('P-3', b)
        self.add_track(b, (22, 90), (22, 91), 'BAT_IN')                       # F.Cu: only CH1, GND, RAW_ACT, 3V3
        self.assertFails('P-3', b, 'BAT_IN')
        b = self.repaired_purity()
        self.add_track(b, (22, 90), (22, 91), '3V3', layer=pcbnew.In2_Cu)    # In1 / In2: GND only
        self.assertFails('P-3', b, 'In2')
        b = self.repaired_purity()
        self.add_track(b, (19.85, 86.0), (19.85, 87.0), 'BAT_IN', layer=pcbnew.B_Cu)   # 0.4 mm beside B.Cu CONT
        self.assertFails('P-3', b, '1.0 mm inside the hull')

    def seed_report(self, issues=()):
        return dict(board_sha256=None, pairs=[dict(pair='Q124.5 -- R129.2')], issues=list(issues))

    def test_p4_rule_h_live(self):
        b = self.r8()
        self.assertPasses('P-4', b, seed=self.seed_report())
        self.assertFails('P-4', b, 'not run')
        self.assertFails('P-4', b, 'caught by nothing', seed=self.seed_report(['x variant deleted: caught by nothing']))
        v = RS.dru_variants(self.dru())
        self.assertFails('P-4', b, 'last pyro rule', seed=self.seed_report(), dru=v['moved_first'])
        self.assertFails('P-4', b, 'minimum >= 1.0', seed=self.seed_report(), dru=v['min_lowered'])
        later = self.dru() + '\n(rule "late"\n  (condition "A.Type == \'Pad\'")\n  (constraint clearance (min 0.2mm)))\n'
        self.assertFails('P-4', b, 'after rule H', seed=self.seed_report(), dru=later)

    def bridge(self, na, nb, gap, refs=('R900', 'C900')):
        b = self.synth()
        fa = self.fp(b, refs[0], 10, 10)
        self.pad(fa, 1, 10, 10, na)
        fb = fa if refs[1] == refs[0] else self.fp(b, refs[1], 10.5 + gap, 10)
        self.pad(fb, 2, 10.5 + gap, 10, nb)
        return b

    def test_p5_bridge_table(self):
        self.assertFails('P-5', self.bridge('PYRO1_OUT', 'GND', 0.8), 'FIRES when armed', real=False)
        self.assertPasses('P-5', self.bridge('PYRO1_OUT', 'GND', 1.05), real=False)
        self.assertFails('P-5', self.bridge('PYRO1_BUS', 'ARM1_SENSE', 1.1), 'live past', real=False)   # strict 1.2
        self.assertPasses('P-5', self.bridge('PYRO1_BUS', 'ARM1_SENSE', 1.25), real=False)
        self.assertPasses('P-5', self.bridge('PYRO1_OUT', 'PYRO1_CONT_MID', 0.6), real=False)  # R4: own midpoint
        self.assertPasses('P-5', self.bridge('PYRO1_OUT', 'GND', 0.3, refs=('C128', 'C128')), real=False)  # own part
        self.assertPasses('P-5', self.bridge('PYRO1_GATE_N', 'ARM1_SENSE_MCU', 0.6), real=False)  # 0.10 V in reset
        self.assertFails('P-5', self.bridge('PYRO1_GATE', '3V3', 0.9), 'FIRES', real=False)
        self.assertFails('P-5', self.bridge('ACT_GATE', 'GND', 1.1), 'actuator switch on', real=False)
        self.assertPasses('P-5', self.bridge('ACT_GATE', 'ACT_FET_S', 0.5), real=False)       # switch held off

    def test_p6_bare_gate(self):
        self.assertFails('P-6', self.bridge('PYRO1_GATE', '3V3', 0.8), '3V3', real=False)
        self.assertPasses('P-6', self.bridge('PYRO1_GATE', '3V3', 1.05), real=False)
        self.assertPasses('P-6', self.bridge('PYRO1_GATE', '3V3', 0.3, refs=('R900', 'R900')), real=False)
        self.assertFails('P-6', self.bridge('ACT_GATE', 'ACT_FET_S', 0.6), 'ACT_FET_S', real=False)   # Z5b >= 1.0
        self.assertFails('P-6', self.r8(), 'Q121.4')

    def guard(self, other, gap, layer=None, gate_layer=None):
        b = self.synth()
        self.fp(b, 'U1', 40, 90, court=(14, 14))
        gl = pcbnew.F_Cu if gate_layer is None else gate_layer
        self.track(b, (10, 5), (10, 15), 'PYRO1_GATE_N', 0.2, gl)
        x = 10.1 + gap + 0.1
        self.track(b, (x, 5), (x, 15), other, 0.2, pcbnew.F_Cu if layer is None else layer)
        return b

    def test_p7_gate_guard_by_reset_voltage(self):
        self.assertFails('P-7', self.guard('ARM1_SENSE', 0.4), '0.37 V', real=False)
        self.assertPasses('P-7', self.guard('ARM1_SENSE', 0.55), real=False)
        self.assertPasses('P-7', self.guard('ARM1_SENSE_MCU', 0.4), real=False)    # 0.10 V
        self.assertPasses('P-7', self.guard('GND', 0.2), real=False)
        self.assertFails('P-7', self.guard('3V3', 0.3, layer=pcbnew.In1_Cu), 'In1', real=False)   # F.Cu / In1 close
        self.assertPasses('P-7', self.guard('3V3', 0.3, layer=pcbnew.In2_Cu), real=False)         # 1.2 mm away
        self.assertFails('P-7', self.r8(), 'ARM1_SENSE')

    def gate_pin(self, net, gap, ref=None):
        """A synthetic U1 whose pad 3 is the gate pin (PYRO1_GATE_N, inside the courtyard) and a 0.2 mm track of `net`
        (or, with ref, another pad of that part) `gap` mm beyond the pad's east edge (P-7b)."""
        b = self.synth()
        f = self.fp(b, 'U1', 20, 20, court=(14, 14))
        self.pad(f, 3, 20, 20, 'PYRO1_GATE_N', size=(0.3, 1.6))
        if ref == 'U1':
            self.pad(f, 6, 20.15 + gap + 0.15, 20, net, size=(0.3, 1.6))
        else:
            x = 20.15 + gap + 0.1
            self.track(b, (x, 18), (x, 22), net, 0.2)
        return b

    def test_p7b_mcu_gate_pin(self):
        self.assertFails('P-7', self.gate_pin('SIGNAL', 0.25), 'P-7b', real=False)       # R9P1-PYRO-01's 0.25 mm
        self.assertPasses('P-7', self.gate_pin('SIGNAL', 0.55), real=False)
        self.assertPasses('P-7', self.gate_pin('GND', 0.2), real=False)
        self.assertPasses('P-7', self.gate_pin('3V3', 0.3, ref='U1'), real=False)          # U1's own pins: its pitch

    def test_p8_sense_end(self):
        b = self.r8()
        self.assertPasses('P-8', b)
        t = next(t for t in b.GetTracks() if t.GetNetname() == 'PYRO1_CONT_MCU' and t.GetClass() == 'PCB_TRACK')
        a = t.GetEnd()
        self.add_track(b, (mm(a.x), mm(a.y)), (mm(a.x) + 2.0, mm(a.y)), 'PYRO1_CONT_MCU')
        self.assertFails('P-8', b, 'MCU end')

    def repaired_tp122(self):
        b = self.r8()
        for v in self.vias_at(b, 20.45, 92.4, 'PYRO1_GATE'):              # A8: the via inside TP122, out of play
            v.SetNet(b.FindNet('GND'))
            v.Move(self.P(300, 300))
        return b

    def test_p9_test_pads(self):
        self.assertFails('P-9', self.r8(), 'PYRO1_GATE via')
        b = self.repaired_tp122()
        self.assertPasses('P-9', b)
        self.add_via(b, 30.0, 70.0, 'PYRO1_GATE')                         # a gate layer change with no GND via
        self.assertFails('P-9', b, 'no GND via within 1.5')
        b = self.repaired_tp122()
        tp = b.FindFootprintByReference('TP122')
        tp.Flip(tp.GetPosition(), False)
        self.assertFails('P-9', b, 'bottom side')
        b = self.repaired_tp122()
        self.place(b, 'C15', 21.8, 92.4)                                   # a bottom part beside TP122
        self.assertFails('P-9', b, 'from TP122')

    def test_p10_coat_region(self):
        self.assertFails('P-10', self.r8(), 'TP121')
        b = self.r8()
        self.park(b, 'TP121')
        self.assertPasses('P-10', b)
        self.place(b, 'U5', 22, 96)
        self.assertFails('P-10', b, 'U5')
        b = self.r8()
        self.park(b, 'TP121')
        self.place(b, 'U4', 23, 80.5)
        self.assertFails('P-10', b, 'U4')

    def test_p11_terminal_entry(self):
        self.assertFails('P-11', self.r8(), 'J121 wires enter from +x')
        b = self.r8()
        self.place(b, 'J121', 36.0, 93.32, 90)                            # entry -x, as the owner set
        self.assertPasses('P-11', b)
        self.place(b, 'J124', 10.0, 93.32, -90)
        self.assertFails('P-11', b, 'J124 wires enter from +x')
        b = self.r8()
        self.place(b, 'J121', 36.0, 93.32, 90)
        self.move(b, 'J124', -0.6, 0)
        self.assertFails('P-11', b, 'wire room')


# ======================================================================================================================
class RfRules(Base):
    def test_r1_strip_extent(self):
        b = self.synth()
        self.fp(b, 'C300', 10, 20, court=(1.6, 1.0))                       # an RF part inside y_f
        self.fp(b, 'R306', 18, 26, court=(0.9, 1.8))                       # MCU-end resistor: outside the strip
        self.assertPasses('R-1', b, real=False)
        self.fp(b, 'C301', 13, 21.8, court=(1.6, 1.0))                    # reaches 22.3
        self.assertFails('R-1', b, 'C301', real=False)
        b = self.synth()
        f = self.fp(b, 'C72', 30, 20)
        self.pad(f, 1, 30, 20, '3V3')                                      # a non-RF pad in the strip
        self.assertFails('R-1', b, 'non-RF pad C72.1', real=False)

    def test_r2_strip_layers(self):
        b = self.r8()
        self.assertPasses('R-2', b)
        self.add_track(b, (20, 10), (22, 10), '3V3', layer=pcbnew.In1_Cu)
        self.assertFails('R-2', b, 'In1.Cu track of 3V3')
        b = self.r8()
        self.add_track(b, (20, 15), (20, 17), 'RADIO_NSS', layer=pcbnew.B_Cu)
        self.assertFails('R-2', b, 'B.Cu track of RADIO_NSS')
        b = self.r8()
        self.add_track(b, (36, 2), (36, 3.0), 'RADIO_TXEN', layer=pcbnew.B_Cu)   # beyond R8's 22.72 mm on B.Cu
        self.assertFails('R-2', b, 'RADIO_TXEN runs')
        b = self.r8()
        for z in self.area(b, 'U31_KEEPOUT'):
            z.SetZoneName('U31_KO')
        self.assertFails('R-2', b, 'U31_KEEPOUT')

    def test_r3_jacks(self):
        b = self.r8()
        self.assertPasses('R-3', b)
        self.place(b, 'J30', 12.85, 0, 90)
        self.assertFails('R-3', b, 'rotation 0')
        b = self.r8()
        self.place(b, 'J31', 20.0, 0)
        self.assertFails('R-3', b, 'apart')
        b = self.r8()
        self.place(b, 'J30', 3.0, 0)
        self.assertFails('R-3', b, 'plug envelope')

    def repaired_launch(self):
        b = self.r8()
        self.add_via(b, 12.85 + 1.25, 4.15)                               # R7 / R8's J30 via sits at (+1.20, 4.65)
        return b

    def test_r4_launch_congruent(self):
        self.assertFails('R-4', self.r8(), '(+1.25, 4.15)')
        b = self.repaired_launch()
        self.assertPasses('R-4', b)
        self.remove(b, self.vias_at(b, 31.54 - 1.45, 1.0, 'GND'))
        self.assertFails('R-4', b, 'J31: no GND via')
        b = self.repaired_launch()
        z = next(z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'R7_J31_launch_In1')
        z.Move(self.P(0.1, 0))
        self.assertFails('R-4', b, 'J31: exactly one')

    def rf_track(self, b, net, x, y0):
        return next(t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == net and
                    abs(mm(t.GetStart().x) - x) < 0.01 and abs(mm(t.GetEnd().x) - x) < 0.01 and
                    abs(min(mm(t.GetStart().y), mm(t.GetEnd().y)) - y0) < 0.05)

    def test_r5_gcpw(self):
        b = self.r8()
        self.assertPasses('R-5', b)
        self.rf_track(b, 'GNSS_RF_IN', 13.71, 7.13).SetWidth(MM(0.35))
        self.assertFails('R-5', b, 'wide')
        b = self.r8()
        t = self.rf_track(b, 'GNSS_RF_IN', 13.71, 7.13)
        self.add_track(b, (13.79, 7.6), (13.79, 8.6), 'GNSS_RF_IN', width=0.3)   # copper 0.08 mm off the line
        self.assertFails('R-5', b, 'GNSS_RF_IN')
        b = self.r8()
        self.renet([z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND'
                    and z.IsOnLayer(pcbnew.In1_Cu)], '3V3', b)
        self.assertFails('R-5', b, 'In1 GND missing')
        _ = t

    def test_r6_line_length(self):
        b = self.r8()
        self.assertPasses('R-6', b)
        t = self.rf_track(b, 'RADIO_RF', 32.4, 7.6)
        t.SetStart(self.P(32.4, 7.6)); t.SetEnd(self.P(34.4, 7.6))                 # the line now detours east
        for a, c in (((34.4, 7.6), (34.4, 9.05)), ((34.4, 9.05), (32.4, 9.05))):
            self.add_track(b, a, c, 'RADIO_RF', width=0.3)
        self.assertFails('R-6', b, 'RADIO line')

    def repaired_stitching(self):
        b = self.r8()
        self.add_via(b, 11.35, 5.7)                                        # the GNSS line's west gap (R8: 2.73 mm)
        return b

    def test_r7_stitching_and_fence(self):
        self.assertFails('R-7', self.r8(), 'GNSS west')
        b = self.repaired_stitching()
        self.assertPasses('R-7', b, y_f=23.3)                              # R8's fence row (R9's y_f is 22.0)
        self.assertFails('R-7', b, 'fence')                                # at R9's y_f the R8 fence is 1.3 mm off
        self.remove(b, self.vias_at(b, 11.35, 5.7))
        self.assertFails('R-7', b, 'GNSS west', y_f=23.3)
        b = self.repaired_stitching()
        fence = sorted((t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND'
                        and abs(mm(t.GetPosition().y) - 23.3) < 0.06), key=lambda t: t.GetPosition().x)
        fence[2].Move(self.P(300, 300))
        self.assertFails('R-7', b, 'fence', y_f=23.3)

    def test_r8_module_keepouts(self):
        b = self.r8()
        self.assertPasses('R-8', b)
        z = next(z for z in self.area(b, 'U31_KEEPOUT') if z.IsOnLayer(pcbnew.B_Cu) and not z.IsOnLayer(pcbnew.F_Cu))
        self.set_outline(z, (25.2, 9.0, 34.86, 19.0))
        self.assertFails('R-8', b, 'uncovered on')
        b = self.r8()
        self.add_track(b, (8, 14), (12, 14), '3V3')
        self.assertFails('R-8', b, 'inside U30_KEEPOUT')
        # In1 GND is sampled under U31's whole body, the pad-ring band included (R9P1-INTEGRITY-02): a notch in the
        # band, outside the keep-out's interior, fails
        b = self.r8()
        z = next(z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and
                 z.IsOnLayer(pcbnew.In1_Cu) and z.HitTestFilledArea(pcbnew.In1_Cu, self.P(25.2, 13.2)))
        fill = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(pcbnew.In1_Cu))
        notch = pcbnew.SHAPE_POLY_SET()
        notch.NewOutline()
        for x, y in ((25.0, 13.0), (25.5, 13.0), (25.5, 13.5), (25.0, 13.5)):
            notch.Append(MM(x), MM(y))
        fill.BooleanSubtract(notch)
        z.SetFilledPolysList(pcbnew.In1_Cu, fill)
        self.assertFails('R-8', b, 'U31 In1.Cu: GND missing')

    def test_r9_chain_topology(self):
        b = self.r8()
        self.assertPasses('R-9', b)
        self.move(b, 'C302', -0.5, 0)
        self.assertFails('R-9', b, 'C302')
        b = self.r8()
        self.move(b, 'C303', -0.2, 0)
        self.assertFails('R-9', b, 'stub')
        b = self.r8()
        self.move(b, 'D30', 0, 1.5)
        self.assertFails('R-9', b, 'D30')

    def test_r10_rf_separation(self):
        b = self.r8()
        self.assertPasses('R-10', b)
        fb, u7 = b.FindFootprintByReference('FB31').GetPosition(), b.FindFootprintByReference('U7').GetPosition()
        d = math.hypot(u7.x - fb.x, u7.y - fb.y)
        self.move(b, 'FB31', mm(u7.x - fb.x) / mm(d) * 0.8, mm(u7.y - fb.y) / mm(d) * 0.8)   # 6.66 -> ~5.86 mm
        found = self.assertFails('R-10', b, '5.94')
        self.assertNotIn('minimum 5.0', joined(found))                     # F10's 5 mm still holds: the R9 hard X9

    def test_r11_coexistence(self):
        b = self.r8()
        self.assertPasses('R-11', b)
        self.add_track(b, (17.5, 20), (17.5, 22), 'RADIO_RXEN')
        self.assertFails('R-11', b, 'RADIO_RXEN')
        b = self.r8()
        self.move(b, 'U31', -4.0, 0)
        self.assertFails('R-11', b, 'module courtyards')

    def test_r12_rf_supply(self):
        b = self.r8()
        self.assertPasses('R-12', b)
        self.move(b, 'C311', 2.0, 0)
        self.assertFails('R-12', b, 'C311')
        b = self.r8()
        self.add_track(b, (2, 30), (2, 330), '3V3_GNSS', width=0.15)       # 1.24 ohm of track
        self.assertFails('R-12', b, 'series resistance')
        b = self.r8()
        b.FindFootprintByReference('FB31').FindPadByNumber('1').SetNet(b.FindNet('3V3_GNSS'))
        self.assertFails('R-12', b, 'FB31')

    def test_r13_radio_to_pyro(self):
        b = self.r8()
        self.assertPasses('R-13', b)
        self.place(b, 'J121', 36, 50)
        self.assertFails('R-13', b, 'J121')


# ======================================================================================================================
class MechanicalAndKept(Base):
    def test_m2_vibration(self):
        b = self.r8()
        ok = dict(board_sha256=None, f1=dict(jacks_only=dict(pinned_D5=264.5)), supports=[])
        self.assertPasses('M-2', b, plate=ok)
        self.assertFails('M-2', b, 'not run')
        low = copy.deepcopy(ok); low['f1']['jacks_only']['pinned_D5'] = 208.7       # R8: under the 209 Hz floor
        self.assertFails('M-2', b, '209', plate=low)
        other = dict(ok, board_sha256='0' * 64)
        found = C9.check_board(b, r8_folder(), r8_folder() / 'm3.kicad_pcb', only={'M-2'}, plate=other,
                               board_sha=R8_SHA, dru=self.dru())['rules']['M-2']['issues']
        self.assertIn('not bound to this board', joined(found))

    def test_m3_tie_holes(self):
        b = self.r8()
        self.assertPasses('M-3', b)
        d = next(d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE
                 and abs(mm(d.GetCenter().y) - 82.6) < 0.01)
        d.Move(self.P(4, 0))                                               # tie line off the plugs
        self.assertFails('M-3', b)
        b = self.r8()
        self.place(b, 'D121', 24.25, 75.6)                                 # a bottom part in the tie channel
        self.assertFails('M-3', b, 'tie path')

    def test_m4_j1(self):
        b = self.r8()
        self.assertPasses('M-4', b)
        self.place(b, 'J1', 23.0, 104.0)
        self.assertFails('M-4', b, 'entry face')
        b = self.r8()
        self.place(b, 'J1', 23.0, 110.4, 0)
        self.assertFails('M-4', b, 'enter from -y')
        b = self.r8()
        self.place(b, 'J1', 5.0, 50.0, 180)
        self.assertFails('M-4', b, 'grouped')

    def test_m5_fit_floors(self):
        b = self.r8()
        rep = FC.check_board(b, r8_folder())
        self.assertPasses('M-5', b, fit=rep)
        bad = copy.deepcopy(rep)
        bad['rows'] = [[0.45 if r[1] == 'J122 mated' else r[0]] + list(r[1:]) for r in bad['rows']]
        self.assertFails('M-5', b, 'owner decision 5', fit=bad)
        bad = copy.deepcopy(rep)
        bad['nearest_top_support'] = [4.0, 'TP30.1 exposed top pad', [4.0, 4.0]]    # above P2's 3.8, below R8's
        self.assertFails('M-5', b, 'top hardware', fit=bad)
        bad = copy.deepcopy(rep)
        bad['issues'] = ['X: outside bore by 0.1 mm']
        self.assertFails('M-5', b, 'outside bore', fit=bad)

    def repaired_bottom(self):
        b = self.r8()
        self.remove(b, self.vias_at(b, 24.0, 53.7) + self.vias_at(b, 29.3, 47.5))   # D61's two MCU-side vias
        return b

    def test_m6_bottom_keepouts(self):
        self.assertFails('M-6', self.r8(), 'pyro via')                     # no D61 exception in R9
        b = self.repaired_bottom()
        self.assertPasses('M-6', b)
        self.place(b, 'C15', 26.0, 74.0)                                   # beside J122's pin tails
        self.assertFails('M-6', b, 'through-hole pad')
        b = self.repaired_bottom()
        j = b.FindFootprintByReference('J123')
        j.Flip(j.GetPosition(), False)
        self.assertFails('M-6', b, 'J123 has through-hole pads')

    def test_m7_imu_and_mems(self):
        b = self.r8()
        self.assertPasses('M-7', b)
        self.add_via(b, 10.0, 53.8)
        self.assertFails('M-7', b, 'under U4')
        b = self.r8()
        self.place(b, 'U4', 10.0, 53.8, 90)
        self.assertFails('M-7', b, 'rotation 0')
        b = self.r8()
        self.place(b, 'U4', 10.0, 53.8, 180)                               # R9's map on an R8 board
        self.assertFails('M-7', b, 'rotation 0')
        tb = b.GetTitleBlock()
        tb.SetRevision('M3-ASSY-R9')
        b.SetTitleBlock(tb)
        self.assertPasses('M-7', b)                                         # R9 is held to its recorded 180
        self.place(b, 'U4', 10.0, 53.8, 0)
        self.assertFails('M-7', b, 'rotation 180')
        b = self.r8()
        self.place(b, 'U4', 6.0, 53.8)
        self.assertFails('M-7', b, 'lever arm')
        b = self.r8()
        self.add_track(b, (10.0, 60.2), (11.0, 60.2), 'SIGNAL' if b.FindNet('SIGNAL') else 'GND', layer=pcbnew.B_Cu)
        self.assertFails('M-7', b, 'U5')

    def test_f9_input_protection(self):
        b = self.r8()
        self.assertPasses('F9-1', b)
        self.place(b, 'C96', 23.0, 80.0)                                   # 30 mm aft of J1.1
        self.assertFails('F9-1', b, 'C96')
        b = self.r8()
        self.move(b, 'U9', 0, -5.0)
        self.assertFails('F9-1', b, 'U9')

    def test_t1_tab_windows(self):
        b = self.r8()
        self.assertPasses('T-1', b)
        f = pcbnew.FOOTPRINT(b); f.SetReference('C999'); b.Add(f)
        s = pcbnew.PCB_SHAPE(f); s.SetShape(pcbnew.SHAPE_T_RECT); s.SetLayer(pcbnew.F_CrtYd)
        s.SetStart(self.P(40, 80)); s.SetEnd(self.P(45, 118)); s.SetWidth(MM(0.05)); f.Add(s); f.BuildCourtyardCaches()
        self.assertFails('T-1', b, 'east edge within the forward third')

    def test_k_contract_legends_copper(self):
        import r9_lib
        b = self.r8()
        for rid in ('K-legends', 'K-copper', 'K-actuators'):
            self.assertPasses(rid, b)
        self.assertFails('K-contract', b, 'J124: requires M3_DB128L_2P_BK_SW')   # R8 has the base footprints (D-S2-12)
        r9_lib.apply_variants(b)                                                  # the owner-decided variants, in place
        self.assertPasses('K-contract', b)
        # R8's terminal legends now sit beside the other pin: D92 catches it (R9's silkscreen is redrawn, step 8)
        self.assertFails('K-legends', b, 'terminal pin legend "1:BUS1"')
        b.FindFootprintByReference('R306').SetValue('330R')
        self.assertFails('K-contract', b, 'R306')
        b = self.r8()
        gnss = [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetText().strip() == 'GNSS']
        self.park(b, item=gnss[0])                                       # the J30 legend 300 mm away
        self.assertFails('K-legends', b, 'GNSS')
        b = self.r8()
        c = b.FindFootprintByReference('C300').FindPadByNumber('1').GetPosition()
        self.add_via(b, mm(c.x), mm(c.y), '3V3_GNSS')
        self.assertFails('K-copper', b, 'C300')

    def test_k_power_pyro_strengthened(self):
        b = self.r8()
        self.assertFails('K-power-pyro', b, 'minimum 2.5 mm')            # R8 1.089 mm: D85 now 2.5 (hard X2d)
        self.renet([z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() in ('ACT_FET_S', 'BAT_IN')],
                   'GND', b)
        self.assertPasses('K-power-pyro', b)
        p = b.FindFootprintByReference('J124').FindPadByNumber('1').GetPosition()
        self.add_track(b, (mm(p.x) + 3.3, mm(p.y) - 1), (mm(p.x) + 3.3, mm(p.y) + 1), 'BAT_IN')   # 2 mm: R8's 1.0 passes
        self.assertFails('K-power-pyro', b, 'BAT_IN')

    def test_k_inner_signal_no_exemption(self):
        b = self.r8()
        self.assertFails('K-inner', b, 'ARM1_SENSE')                     # R8's rigid In2 link: no exemption in R9
        for t in b.GetTracks():
            if t.GetClass() == 'PCB_TRACK' and t.GetLayer() == pcbnew.In2_Cu and t.GetNetname() == 'ARM1_SENSE':
                t.SetLayer(pcbnew.F_Cu)
        self.assertPasses('K-inner', b)
        self.add_track(b, (20, 40), (22, 40), 'GND', layer=pcbnew.In1_Cu)
        self.assertFails('K-inner', b, 'In1')

    def test_k_actuators_pin(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'check_actuators.py'
            p.write_text(C9.CHECK_ACTUATORS.read_text() + '\n# edited\n')
            keep = C9.CHECK_ACTUATORS
            try:
                C9.CHECK_ACTUATORS = p
                self.assertFails('K-actuators', self.r8(), 'reviewed R9 version')
            finally:
                C9.CHECK_ACTUATORS = keep

    def test_r8_fails_exactly_the_recorded_rules(self):
        """The R8 comparison of the R9 contract (r9_step1_handoff.md): R8's failing set under check_r9."""
        b = self.r8()
        rep = C9.check_board(b, r8_folder(), r8_folder() / 'm3.kicad_pcb', dru=self.dru(),
                             plate=dict(board_sha256=R8_SHA, f1=dict(jacks_only=dict(pinned_D5=208.7))),
                             seed=dict(board_sha256=R8_SHA, pairs=[dict(pair='Q124.5 -- R129.2')], issues=[]),
                             board_sha=R8_SHA)
        self.assertEqual(set(rep['failing']), R8_FAILING)


if __name__ == '__main__':
    unittest.main()
