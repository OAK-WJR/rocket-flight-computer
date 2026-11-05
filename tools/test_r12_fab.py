"""Tests for the R12 fab package tooling (m3_design/r12_fab.sh, tools/export_fab_r12.py, tools/jlc_orient_r12.py,
tools/fab_manifest_r12.py). The wrapper and data tests always run; the package tests export the R12 board (R12_BOARD,
else m3_design/r12/m3.kicad_pcb) into a temporary folder, bind it, and seed faults into copies. They skip cleanly when
the R12 board is absent or KiCad's Python / kicad-cli is unavailable.

usage: <KiCad python3> tools/test_r12_fab.py        (KICAD_PY / KICAD_CLI override KiCad's default macOS location)
"""
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import export_fab_r12                                            # noqa: E402
import fab_manifest_r12 as fm12                                  # noqa: E402
import jlc_orient_r12                                            # noqa: E402

KICAD_PY = os.environ.get('KICAD_PY') or \
    '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3'
KICAD_CLI = os.environ.get('KICAD_CLI') or '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
BOARD = Path(os.environ.get('R12_BOARD') or ROOT / 'm3_design/r12/m3.kicad_pcb')
TOOL = str(ROOT / 'tools/fab_manifest_r12.py')
NOISE = ('Debug: Adding duplicate', 'create wxApp', 'Fontconfig', 'stdpbase')


def run(*argv, env=None):
    result = subprocess.run([str(a) for a in argv], capture_output=True, text=True, timeout=900,
                            env=dict(os.environ, KICAD_PY=KICAD_PY, KICAD_CLI=KICAD_CLI, **(env or {})))
    text = '\n'.join(line for line in (result.stdout + result.stderr).splitlines()
                     if not any(word in line for word in NOISE))
    return result.returncode, text


class Wrappers(unittest.TestCase):
    """The R10 sources the wrappers execute still carry every replaced text, and the R12 data agrees with the tables."""

    def test_sources_apply_and_compile(self):
        for module in (export_fab_r12, jlc_orient_r12):
            text = module.source()
            for _, new, _ in module.REPLACE:
                self.assertIn(new, text)
            compile(text, module.SOURCE.name, 'exec')

    def test_one_side_layers(self):
        text = export_fab_r12.source()
        self.assertIn("'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'", text)
        self.assertNotIn('B.Paste,', text)

    def test_mechanical_table_matches_jlc_footprints(self):
        """R12_MECHANICAL's tab numbers are JLCEDA's: present in the pad file, left tab at -x, right at +x, beyond
        the signal pins' numbers, and each footprint exists in the R12 library."""
        pads = json.loads(jlc_orient_r12.PADS.read_text())
        codes = {'M3_SHC_4P': 'C7430446', 'M3_SHC_6P': 'C7430448'}
        self.assertEqual(set(jlc_orient_r12.R12_MECHANICAL), set(codes))
        for name, (left, right) in jlc_orient_r12.R12_MECHANICAL.items():
            self.assertTrue((ROOT / f'm3_design/r12/kilib/rocket.pretty/{name}.kicad_mod').exists(), name)
            record = pads[codes[name]]
            xs = {f.split('~')[8]: float(f.split('~')[2]) - record['head'][0] for f in record['pads']}
            self.assertLess(xs[left], 0, name)
            self.assertGreater(xs[right], 0, name)
            self.assertEqual(min(int(left), int(right)), len(xs) - 1, name)

    def test_binding_inputs(self):
        if not BOARD.exists():
            self.skipTest('no R12 board')
        inputs = fm12.input_hashes(BOARD)
        self.assertIn('cad/m3.kicad_pcb', inputs)
        for name in fm12.R12_INPUTS:
            self.assertIn(name, inputs)
        for name in fm12.R10_ONLY:
            self.assertNotIn(name, inputs)

    def test_content_check_commands(self):
        checks = fm12.content_checks(BOARD, ROOT / 'x', 'kpy')
        self.assertEqual([argv[-1] for _, argv in checks], ['--verify-cpl', '--paste'])


@unittest.skipUnless(BOARD.exists(), f'no R12 board at {BOARD}')
@unittest.skipUnless(Path(KICAD_PY).exists() and Path(KICAD_CLI).exists(), 'KiCad Python / kicad-cli unavailable')
class Package(unittest.TestCase):
    """Export and bind the R12 board's package into a temporary folder, then seed faults into copies of it."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix='r12fab_'))
        cls.out = cls.tmp / 'fab'
        record = cls.tmp / 'export.json'
        code, text = run(KICAD_PY, '-I', ROOT / 'tools/jlc_orient_r12.py', ROOT / 'tools/jlc_easyeda/pads_r12.json',
                         BOARD, '--out', cls.tmp / 'corrections.json')
        cls.orient = (code, text)
        code, text = run(KICAD_PY, '-I', ROOT / 'tools/export_fab_r12.py', BOARD, '--out', cls.out,
                         '--pending', record)
        cls.export = (code, text)
        cls.bind = run(sys.executable, TOOL, BOARD, '--out', cls.out, '--bind', record) if code == 0 else (1, text)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def copy(self):
        dest = Path(tempfile.mkdtemp(dir=self.tmp)) / 'fab'
        shutil.copytree(self.out, dest)
        return dest

    def check(self, out, mode):
        return run(KICAD_PY, '-I', TOOL, BOARD, '--out', out, mode)

    def rewrite(self, path, edit):
        with open(path, newline='') as source:
            rows = list(csv.reader(source))
        rows = edit(rows)
        with open(path, 'w', newline='') as sink:
            csv.writer(sink).writerows(rows)

    def test_corrections_reproduce_the_tracked_file(self):
        """Every part matches JLC's footprint ("CHECK: none") and the tracked corrections are current."""
        self.assertEqual(self.orient[0], 0, self.orient[1][-2000:])
        tracked = json.loads((ROOT / 'tools/jlc_corrections_r12.json').read_text())
        fresh = json.loads((self.tmp / 'corrections.json').read_text())
        self.assertEqual(tracked, fresh, 'tools/jlc_corrections_r12.json is stale: run m3_design/r12_fab.sh')

    def test_package_binds_and_verifies(self):
        self.assertEqual(self.export[0], 0, self.export[1][-2000:])
        self.assertEqual(self.bind[0], 0, self.bind[1][-2000:])
        code, text = run(sys.executable, TOOL, BOARD, '--out', self.out, '--content')
        self.assertEqual(code, 0, text)
        stem = BOARD.stem
        names = {p.name for p in self.out.iterdir()}
        for suffix in fm12.fm.OUTPUTS + ('fab_manifest.json',):
            self.assertIn(f'{stem}_{suffix}', names)
        with open(self.out / f'{stem}_cpl_jlc.csv', newline='') as source:
            self.assertEqual({row['Layer'] for row in csv.DictReader(source)}, {'Top'})

    def test_cpl_row_missing(self):
        out = self.copy()
        self.rewrite(out / f'{BOARD.stem}_cpl_jlc.csv', lambda rows: rows[:1] + rows[2:])
        code, text = self.check(out, '--verify-cpl')
        self.assertNotEqual(code, 0)
        self.assertIn('designators differ', text)

    def test_cpl_bottom_layer(self):
        out = self.copy()
        self.rewrite(out / f'{BOARD.stem}_cpl_jlc.csv', lambda rows: rows[:1] + [rows[1][:3] + ['Bottom'] + rows[1][4:]]
                     + rows[2:])
        code, text = self.check(out, '--verify-cpl')
        self.assertNotEqual(code, 0)
        self.assertIn('off the Top layer', text)

    def test_cpl_rotation_wrong(self):
        out = self.copy()

        def turn(rows):
            for row in rows[1:]:
                if row[0] == 'U1':
                    row[4] = str((int(row[4]) + 90) % 360)
            return rows
        self.rewrite(out / f'{BOARD.stem}_cpl_jlc.csv', turn)
        code, text = self.check(out, '--verify-cpl')
        self.assertNotEqual(code, 0)
        self.assertIn('rotation differs', text)

    def test_owner_part_in_jlc_bom(self):
        out = self.copy()
        stem = BOARD.stem
        with open(out / f'{stem}_bom_owner.csv', newline='') as source:
            owner = list(csv.reader(source))[1:]
        self.rewrite(out / f'{stem}_bom_jlc.csv', lambda rows: rows + [owner[0][:6] + ['SMT']])
        code, text = self.check(out, '--verify-cpl')
        self.assertNotEqual(code, 0)
        self.assertIn('owner-fitted or out-of-BOM parts', text)

    def test_gerber_layer_missing(self):
        out = self.copy()
        zpath = out / f'{BOARD.stem}_gerber.zip'
        with zipfile.ZipFile(zpath) as z:
            files = {n: z.read(n) for n in z.namelist()}
        with zipfile.ZipFile(zpath, 'w') as z:
            for name, data in files.items():
                if not name.endswith('-In2_Cu.gbr'):
                    z.writestr(name, data)
        code, text = self.check(out, '--paste')
        self.assertNotEqual(code, 0)
        self.assertIn('In2_Cu.gbr', text)

    def test_tampered_output_unbinds(self):
        out = self.copy()
        with open(out / f'{BOARD.stem}_bom_jlc.csv', 'a') as sink:
            sink.write('\n')
        code, text = run(sys.executable, TOOL, BOARD, '--out', out)
        self.assertNotEqual(code, 0)
        self.assertIn('fabrication output missing or changed', text)


if __name__ == '__main__':
    unittest.main()
