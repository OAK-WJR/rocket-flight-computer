"""Manufacturing regressions: missing or corrupt placements must block release."""
import csv
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
KICAD_PY = os.environ.get('KICAD_PY',
    '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3')
BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'
CPL = BOARD.parent / 'fab/m3_cpl_jlc.csv'


@unittest.skipUnless(Path(KICAD_PY).exists() or shutil.which(KICAD_PY), 'KiCad Python required')
class PlacementValidation(unittest.TestCase):
    def setUp(self):
        with CPL.open(newline='') as source:
            self.rows = list(csv.DictReader(source))
        self.headers = list(self.rows[0])
        self.pad_data = None

    def verify(self, valid=False):
        with tempfile.TemporaryDirectory() as tmp:
            cpl = Path(tmp) / 'placements.csv'
            with cpl.open('w', newline='') as output:
                writer = csv.DictWriter(output, fieldnames=self.headers)
                writer.writeheader()
                writer.writerows(self.rows)
            pads = ROOT / 'tools/jlc_easyeda/pads.json'
            if self.pad_data is not None:
                pads = Path(tmp) / 'pads.json'
                pads.write_text(json.dumps(self.pad_data))
            result = subprocess.run([KICAD_PY, '-I', str(ROOT / 'tools/jlc_orient.py'),
                str(pads), str(BOARD), '--verify-cpl', str(cpl)],
                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode == 0, valid, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def row(self, ref):
        return next(row for row in self.rows if row['Designator'] == ref)

    def test_current_package(self):
        self.verify(valid=True)

    def test_missing_mcu(self):
        self.rows.remove(self.row('U1'))
        self.assertIn('missing', self.verify())

    def test_duplicate_component(self):
        self.rows.append(dict(self.row('U1')))
        self.assertIn('duplicate', self.verify())

    def test_unknown_component(self):
        self.row('U1')['Designator'] = 'U9999'
        self.assertIn('unexpected', self.verify())

    def test_wrong_side(self):
        self.row('C90')['Layer'] = 'Top' if self.row('C90')['Layer'] == 'Bottom' else 'Bottom'
        self.assertIn('wrong assembly side', self.verify())

    def test_body_corrected_terminal_rotation(self):
        row = self.row('J1')
        row['Rotation'] = str((float(row['Rotation']) + 180) % 360)
        self.assertIn('rotation differs', self.verify())

    def test_proxy_part_position(self):
        row = self.row('R100')
        row['Mid X'] = str(float(row['Mid X'][:-2]) + 1) + 'mm'
        self.assertIn('position differs', self.verify())

    def test_non_finite_position(self):
        self.row('U1')['Mid X'] = 'nanmm'
        self.assertIn('non-finite', self.verify())

    def test_wrong_coordinate_units(self):
        self.row('U1')['Mid X'] = '1in'
        self.assertIn('coordinates must be in mm', self.verify())

    def test_duplicate_header(self):
        self.headers.append('Rotation')
        self.assertIn('invalid column headers', self.verify())

    def test_missing_source_pad_numbers(self):
        self.pad_data = json.loads((ROOT / 'tools/jlc_easyeda/pads.json').read_text())
        changed = []
        for pad in self.pad_data['C5271084']['pads']:
            fields = pad.split('~')
            fields[8] = 'UNMATCHED_' + fields[8]
            changed.append('~'.join(fields))
        self.pad_data['C5271084']['pads'] = changed
        self.assertIn('incomplete independent pad coverage', self.verify())


class ExportPreflight(unittest.TestCase):
    def test_unverified_part_stops_before_outputs(self):
        spec = importlib.util.spec_from_file_location('export_fab', ROOT / 'tools/export_fab.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rows = module.footprints(BOARD)
        next(row for row in rows if row['ref'] == 'U1')['lcsc'] = 'C_UNREVIEWED'
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'fab'
            with patch.object(module, 'footprints', return_value=rows), \
                    patch.object(module, 'run') as run, \
                    patch.object(sys, 'argv', ['export_fab.py', str(BOARD), '--out', str(output)]):
                with self.assertRaisesRegex(SystemExit, 'unverified placement corrections'):
                    module.main()
                run.assert_not_called()
                self.assertFalse(output.exists())


class ManifestValidation(unittest.TestCase):
    def setUp(self):
        import fab_manifest
        self.manifest = fab_manifest
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.board = self.folder / 'm3.kicad_pcb'
        for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_dru', '.kicad_sch'):
            self.board.with_suffix(suffix).write_text('source fixture\n')
        for name in ('fp-lib-table', 'sym-lib-table'):
            (self.folder / name).write_text('library fixture\n')
        self.out = self.folder / 'fab'
        self.out.mkdir()
        for suffix in ('gerber.zip', 'bom_jlc.csv', 'cpl_jlc.csv', 'assembly_top.pdf', 'assembly_bottom.pdf'):
            (self.out / f'm3_{suffix}').write_text('export fixture\n')
        self.path = self.manifest.write_manifest(self.board, self.out, self.manifest.input_hashes(self.board))

    def test_current_binding(self):
        self.assertEqual(self.manifest.verify_manifest(self.board, self.out), 5)

    def test_changed_copper(self):
        self.board.write_text('changed copper\n')
        with self.assertRaisesRegex(ValueError, 'current CAD'):
            self.manifest.verify_manifest(self.board, self.out)

    def test_changed_artifact(self):
        (self.out / 'm3_gerber.zip').write_text('stale Gerbers\n')
        with self.assertRaisesRegex(ValueError, 'output missing or changed'):
            self.manifest.verify_manifest(self.board, self.out)

    def test_missing_output_entry(self):
        data = json.loads(self.path.read_text())
        del data['outputs_sha256']['m3_cpl_jlc.csv']
        self.path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'missing required outputs'):
            self.manifest.verify_manifest(self.board, self.out)

    def test_source_change_during_export(self):
        before = self.manifest.input_hashes(self.board)
        self.board.with_suffix('.kicad_dru').write_text('changed clearance rules\n')
        with self.assertRaisesRegex(ValueError, 'changed during fabrication export'):
            self.manifest.write_manifest(self.board, self.out, before)


if __name__ == '__main__':
    unittest.main()
