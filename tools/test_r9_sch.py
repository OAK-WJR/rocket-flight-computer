"""R9 build step 2 regressions (m3_design/r9_lib.py, r9_dru.py, r9_sch.py, r9_sch_check.py): every transform reproduces
its committed output, refuses an input it was not written for, and every check fails on a seeded defect.
Run from tools/ with KiCad's Python: python3 -m unittest test_r9_sch (the library, DRU and sheet tests also run under
plain python3)."""
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
import r9_dru                                                   # noqa: E402
import r9_lib                                                   # noqa: E402
import r9_sch                                                   # noqa: E402
try:
    import pcbnew
except ImportError:
    pcbnew = None

R8_COMMIT = '9c8179b'
PROJECT = ROOT / 'm3_design/assembly_review'
LIB = PROJECT / 'kilib/rocket.pretty'


def r8_file(name):
    return subprocess.run(['git', '-C', str(ROOT), 'show', f'{R8_COMMIT}:m3_design/assembly_review/{name}'],
                          capture_output=True, check=True).stdout


class Library(unittest.TestCase):
    def test_variants_are_the_committed_files(self):
        for variant in r9_lib.VARIANTS:
            text, _al, issues = r9_lib.build(LIB, variant)
            self.assertEqual(issues, [], variant)
            self.assertEqual((LIB / f'{variant}.kicad_mod').read_text(), text, variant)

    def test_same_land_numbering_mirrored(self):
        for variant, (base, _d) in r9_lib.VARIANTS.items():
            b = r9_lib.pads((LIB / f'{base}.kicad_mod').read_text())
            v = r9_lib.pads((LIB / f'{variant}.kicad_mod').read_text())
            self.assertEqual(set(b), set(v))
            for n in b:                       # each pad: same shape, size, drill, layers, x mirrored, y kept
                self.assertEqual((b[n][0],) + b[n][3:], (v[n][0],) + v[n][3:])
                self.assertEqual((b[n][1], b[n][2]), (-v[n][1] or 0.0, v[n][2]))
        self.assertEqual(r9_lib.alias((LIB / 'M3_DB128L_2P_BK.kicad_mod').read_text(),
                                      (LIB / 'M3_DB128L_2P_BK_SW.kicad_mod').read_text()), {'1': '2', '2': '1'})

    def test_jlc_pad_alias_matches_the_library(self):
        """tools/jlc_orient.PAD_ALIAS must be the base number at each variant pad's position (it needs pcbnew to import,
        so the table is read from the source)."""
        src = (HERE / 'jlc_orient.py').read_text()
        m = re.search(r'^PAD_ALIAS = (\{.*?\}\})', src, re.S | re.M)
        self.assertIsNotNone(m)
        table = eval(m.group(1))                                     # a literal dict in our own source
        for variant, (base, _d) in r9_lib.VARIANTS.items():
            want = r9_lib.alias((LIB / f'{base}.kicad_mod').read_text(), (LIB / f'{variant}.kicad_mod').read_text())
            self.assertEqual(table.get(variant), want, variant)

    def test_build_flags_an_asymmetric_body(self):
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d)
            for variant, (base, _d) in r9_lib.VARIANTS.items():
                shutil.copy(LIB / f'{base}.kicad_mod', lib / f'{base}.kicad_mod')
            p = lib / 'M3_DB128L_2P_BK.kicad_mod'
            t = p.read_text()
            p.write_text(t.replace('(start -5.07 -5.5)\n\t\t(end 5.07 5.7)', '(start -5.07 -5.5)\n\t\t(end 5.5 5.7)'))
            issues = r9_lib.build(lib, 'M3_DB128L_2P_BK_SW')[2]
            self.assertTrue(any('not symmetric' in i for i in issues), issues)
            p.write_text(t.replace('(at 0 -6.6 0)', '(at 0.5 -6.6 0)'))           # a text off the axis would move
            self.assertTrue(any('text off local x' in i for i in r9_lib.build(lib, 'M3_DB128L_2P_BK_SW')[2]))

    def test_mirrored_refuses_rotated_items(self):
        t = (LIB / 'M3_DB128L_2P_BK.kicad_mod').read_text().replace('(at -2.54 0)', '(at -2.54 0 90)')
        with self.assertRaises(AssertionError):
            r9_lib.mirrored(t, 'M3_DB128L_2P_BK', 'X', 'd')

    def test_check_mode_flags_a_tampered_variant(self):
        with tempfile.TemporaryDirectory() as d:
            proj = Path(d)
            (proj / 'kilib').mkdir()
            shutil.copytree(LIB, proj / 'kilib/rocket.pretty')
            run = lambda: subprocess.run([sys.executable, '-B', str(ROOT / 'm3_design/r9_lib.py'), str(proj),   # noqa
                                          '--check'], capture_output=True, text=True)
            self.assertEqual(run().returncode, 0)
            p = proj / 'kilib/rocket.pretty/M3_DB128L_2P_BK_SW.kicad_mod'
            p.write_text(p.read_text().replace('(at 2.54 0)', '(at 2.6 0)'))
            r = run()
            self.assertEqual(r.returncode, 1)
            self.assertIn('differs from its generated text', r.stdout)


class Rules(unittest.TestCase):
    def setUp(self):
        self.r8 = r8_file('m3.kicad_dru').decode()

    def test_transform_is_the_committed_file(self):
        r9 = (PROJECT / 'm3.kicad_dru').read_text()
        self.assertEqual(r9_dru.transform(self.r8), r9)
        self.assertEqual(r9_dru.verify(self.r8, r9), [])

    def test_only_rule_g_changes_and_two_rules_are_added(self):
        r9 = r9_dru.transform(self.r8)
        a, b = dict(r9_dru.rules(self.r8)), dict(r9_dru.rules(r9))
        self.assertEqual(set(b) - set(a), {'R9 RAW_ACT pins to foreign copper', 'R9 bare test pads to foreign copper'}
                         | set(r9_dru.fill_names()))
        self.assertEqual({n for n in a if a[n] != b[n]}, {r9_dru.RULE_G})
        self.assertIn(r9_dru.G_SCOPE, b[r9_dru.RULE_G])
        names = [n for n, _ in r9_dru.rules(r9)]
        self.assertEqual(names[-1], 'R9 bare test pads to foreign copper')
        self.assertLess(names.index('R9 RAW_ACT pins to foreign copper'), names.index('Pyro A: RAW_ACT to pyro control'))

    def test_fill_margins_follow_their_rules_on_zones_only(self):
        # step 5 (D-S5-12): one fill rule per pyro rule A-G / A2, right after A2 and before H, its rule's condition on
        # zone pairs with the minimum raised by FILL_MARGIN; nothing else changes
        r9 = r9_dru.transform(self.r8)
        names = [n for n, _ in r9_dru.rules(r9)]
        i = names.index('Pyro A2: RAW_ACT to RAW_ACT_SENSE')
        self.assertEqual(names[i + 1:i + 1 + len(r9_dru.FILL_BASE)], r9_dru.fill_names())
        self.assertLess(i + len(r9_dru.FILL_BASE), names.index('Pyro H: live pads to sense and gate pads (solder bridge)'))
        b = dict(r9_dru.rules(r9))
        for base, name in zip(r9_dru.FILL_BASE, r9_dru.fill_names()):
            key = base.split(':')[0].split()[1]
            cond = re.search(r'\(condition "(.*)"\)', b[base]).group(1)
            self.assertIn(f"(A.Type == 'Zone' || B.Type == 'Zone') && ({cond})", b[name])
            mn = float(re.search(r'min ([\d.]+)mm', b[base]).group(1))
            self.assertAlmostEqual(float(re.search(r'min ([\d.]+)mm', b[name]).group(1)), mn + r9_dru.FILL_MARGIN[key])
            self.assertGreaterEqual(r9_dru.FILL_MARGIN[key], 0.25 if key != 'E' else 0.35)
        self.assertEqual(r9_dru.without_fill(r9).count('R9 fill margin'), 0)
        for name in r9_dru.fill_names():                      # a weakened or dropped fill rule is caught
            blk = r9_dru.rule_block(r9, name)
            self.assertNotEqual(r9_dru.verify(self.r8, r9.replace(blk, blk.replace("(A.Type == 'Zone' || ", "(A.Type == 'Pad' || "))), [], name)
            self.assertNotEqual(r9_dru.verify(self.r8, r9.replace(blk + '\n', '')), [], name)

    def test_transform_refuses_another_input(self):
        with self.assertRaises(AssertionError):
            r9_dru.transform(self.r8 + '\n')

    def test_verify_flags_edits(self):
        r9 = r9_dru.transform(self.r8)
        h = r9_dru.rule_block(r9, 'Pyro H: live pads to sense and gate pads (solder bridge)')
        tp = r9_dru.rule_block(r9, 'R9 bare test pads to foreign copper')
        cases = {
            'rule A edited': r9.replace("(rule \"Pyro A: RAW_ACT to pyro control\"\n  (condition \"A.NetName == 'RAW_ACT'",
                                        "(rule \"Pyro A: RAW_ACT to pyro control\"\n  (condition \"A.NetName == 'RAW_ACT' "
                                        "&& A.Layer == 'F.Cu'"),
            'rule G widened': r9.replace("&& B.NetName != 'GND' && B.NetName != 'RAW_ACT' && B.NetName != 'PYRO1_BUS'",
                                         "&& B.NetName != 'GND' && B.NetName != '3V3' && B.NetName != 'RAW_ACT' && "
                                         "B.NetName != 'PYRO1_BUS'", 1),
            'test-pad rule before H': r9.replace('\n' + tp, '').replace(h, tp + '\n' + h),
            'test-pad rule lowered': r9.replace(tp, tp.replace('1.0mm', '0.5mm')),
            'RAW pin rule removed': r9.replace(r9_dru.rule_block(r9, 'R9 RAW_ACT pins to foreign copper'), ''),
        }
        for name, text in cases.items():
            self.assertNotEqual(text, r9, name)
            self.assertNotEqual(r9_dru.verify(self.r8, text), [], name)

    def test_check_actuators_pins_the_r9_rules(self):
        sys.path.insert(0, str(ROOT / 'm3_design'))
        import check_actuators as CA
        r9 = (PROJECT / 'm3.kicad_dru').read_text()
        self.assertEqual([i for i in CA.check('(kicad_pcb)', r9) if 'kicad_dru' in i or 'rule "' in i], [])
        self.assertTrue(any('m3.kicad_dru changed' in i for i in CA.check('(kicad_pcb)', self.r8)))
        tp = r9_dru.rule_block(r9, 'R9 bare test pads to foreign copper')
        self.assertTrue(any('m3.kicad_dru changed' in i for i in CA.check('(kicad_pcb)', r9.replace(tp, tp.replace(
            '1.0mm', '0.9mm')))))


class Sheets(unittest.TestCase):
    def test_transform_of_r8_is_the_committed_sheets(self):
        with tempfile.TemporaryDirectory() as d:
            proj = Path(d)
            names = subprocess.run(['git', '-C', str(ROOT), 'ls-tree', '--name-only', R8_COMMIT,
                                    'm3_design/assembly_review/'], capture_output=True, check=True, text=True).stdout
            for name in [Path(n).name for n in names.split()]:
                if name.endswith('.kicad_sch'):
                    (proj / name).write_bytes(r8_file(name))
            (proj / 'kilib').symlink_to(PROJECT / 'kilib')
            for _ in range(2):                                       # the second run changes nothing
                subprocess.run([sys.executable, '-B', str(ROOT / 'm3_design/r9_sch.py'), str(proj)], check=True,
                               capture_output=True)
                for f in sorted(proj.glob('*.kicad_sch')):
                    self.assertEqual(f.read_bytes(), (PROJECT / f.name).read_bytes(), f.name)

    def test_footprint_field_must_be_r8s_or_r9s(self):
        t = (PROJECT / 'pyro.kicad_sch').read_text().replace('rocket:M3_DB128L_2P_BK_SW', 'rocket:M3_DB128L_2P', 1)
        with self.assertRaises(AssertionError):
            r9_sch.t_footprints('pyro.kicad_sch', t)
        t = r8_file('pyro.kicad_sch').decode()
        once = r9_sch.t_footprints('pyro.kicad_sch', t)
        self.assertEqual(once.count('rocket:M3_DB128L_2P_BK_SW"'), 2)
        self.assertEqual(r9_sch.t_footprints('pyro.kicad_sch', once), once)

    def test_notes_refuse_an_unexpected_sheet(self):
        t = r8_file('servos.kicad_sch').decode().replace("ahead of their reversal", "ahead of the reversal")
        with self.assertRaises(AssertionError):
            r9_sch.t_notes('servos.kicad_sch', t)


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class Board(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = Path(tempfile.mkdtemp(prefix='r9_sch_test_'))
        (cls.dir / 'm3.kicad_pcb').write_bytes(r8_file('m3.kicad_pcb'))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def board(self):
        return pcbnew.LoadBoard(str(self.dir / 'm3.kicad_pcb'))

    def test_apply_variants_in_place_and_idempotent(self):
        b = self.board()
        nets = {(f.GetReference(), p.GetNumber()): p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
        zc = {p.GetNumber(): p.GetLocalZoneConnection() for p in b.FindFootprintByReference('J122').Pads()}
        self.assertEqual(r9_lib.apply_variants(b), ['J121', 'J122', 'J124'])
        self.assertEqual(r9_lib.apply_variants(b), [])
        for ref in ('J121', 'J122', 'J124'):
            self.assertEqual(r9_lib.compare_to_library(b.FindFootprintByReference(ref)), [])
        self.assertEqual(nets, {(f.GetReference(), p.GetNumber()): p.GetNetname() for f in b.GetFootprints()
                                for p in f.Pads()})
        self.assertEqual(zc, {p.GetNumber(): p.GetLocalZoneConnection() for p in b.FindFootprintByReference('J122').Pads()})
        j124 = b.FindFootprintByReference('J124')
        p1 = next(p for p in j124.Pads() if p.GetNumber() == '1')
        self.assertEqual(round(pcbnew.ToMM(p1.GetFPRelativePosition().x), 3), 2.54)
        self.assertEqual(p1.GetShape(pcbnew.F_Cu), pcbnew.PAD_SHAPE_RECTANGLE)      # pin 1 keeps the square pad

    def test_compare_to_library_flags_a_moved_pad(self):
        b = self.board()
        r9_lib.apply_variants(b)
        p = next(p for p in b.FindFootprintByReference('J122').Pads() if p.GetNumber() == '7')
        r = p.GetFPRelativePosition()
        p.SetFPRelativePosition(pcbnew.VECTOR2I(r.x + pcbnew.FromMM(0.1), r.y))
        self.assertTrue(any("['7']" in i for i in r9_lib.compare_to_library(b.FindFootprintByReference('J122'))))

    def test_apply_variants_refuses_an_unexpected_footprint(self):
        b = self.board()
        b.FindFootprintByReference('J121').SetFPID(pcbnew.LIB_ID('rocket', 'M3_DB128L_2P'))
        with self.assertRaises(AssertionError):
            r9_lib.apply_variants(b)

    def test_clear_overrides_leaves_lc1_clean(self):
        import check_r9 as C9
        b = self.board()
        self.assertEqual(len(C9.lc1(b)[0]), 29)
        cleared = r9_lib.clear_overrides(b)
        self.assertEqual(len(cleared), 29)
        self.assertEqual(C9.lc1(b)[0], [])
        f = b.FindFootprintByReference('U1')
        f.SetLocalClearance(pcbnew.FromMM(0.2))                         # a footprint-level override is cleared too
        self.assertEqual(r9_lib.clear_overrides(b), [('U1', '', 0.2)])

    def test_check_r9_pins_the_variants(self):
        import check_r9 as C9
        b = self.board()
        rep = C9.check_board(b, None, None, only={'K-contract'}, dru='')
        self.assertTrue(any('J124: requires M3_DB128L_2P_BK_SW' in i for i in rep['issues']), rep['issues'])
        r9_lib.apply_variants(b)
        rep = C9.check_board(b, None, None, only={'K-contract'}, dru='')
        self.assertFalse(any(r in i for i in rep['issues'] for r in ('J121:', 'J122:', 'J124:')), rep['issues'])

    def test_netlist_diff_flags_undecided_changes(self):
        import r8_sch_check as r8c
        import r9_sch_check as C
        with tempfile.TemporaryDirectory() as d:
            p8, p9 = Path(d) / 'r8.xml', Path(d) / 'r9.xml'
            p8.write_bytes(r8_file('schematic.net.xml'))
            p9.write_bytes((PROJECT / 'schematic.net.xml').read_bytes())
            issues, rows = C.netlist_diff(r8c.parse(p8), r8c.parse(p9))
            self.assertEqual(issues, [])
            self.assertEqual(len(rows), 4)
            t = p9.read_text()
            p9.write_text(t.replace('<value>ARM CH1: BUS1 / RAW</value>', '<value>ARM</value>'))
            self.assertTrue(any('J124' in i for i in C.netlist_diff(r8c.parse(p8), r8c.parse(p9))[0]))
            p9.write_text(t.replace('<field name="LCSC">C430601</field>', '<field name="LCSC">C430603</field>', 1))
            n8, n9 = r8c.parse(p8), r8c.parse(p9)
            self.assertTrue(C.netlist_diff(n8, n9)[0])
            self.assertTrue(C.bom_check(n8, n9)[0])
            m = re.search(r'<node ref="J124" pin="1"', t)
            self.assertIsNotNone(m)
            p9.write_text(t.replace('<node ref="J124" pin="1"', '<node ref="J124" pin="9"'))
            self.assertTrue(any('pin' in i for i in C.netlist_diff(r8c.parse(p8), r8c.parse(p9))[0]))


if __name__ == '__main__':
    unittest.main()
