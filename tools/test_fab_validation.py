"""Manufacturing regressions: missing or corrupt placements must block release."""
from contextlib import redirect_stdout
import csv
import importlib.util
import io
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

    def test_connector_mechanical_tabs_are_independently_checked(self):
        self.pad_data = json.loads((ROOT / 'tools/jlc_easyeda/pads.json').read_text())
        changed = []
        # J9 (GH, C161692): the two unnumbered retention tabs are matched as EasyEDA pads 5 and 6
        for pad in self.pad_data['C161692']['pads']:
            fields = pad.split('~')
            if fields[8] in ('5', '6'):
                fields[2] = str(float(fields[2]) + 10)  # 2.54 mm shifted retention tabs
            changed.append('~'.join(fields))
        self.pad_data['C161692']['pads'] = changed
        self.assertIn('J9', self.verify())


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


class DnpPlaceholders(unittest.TestCase):
    """A DNP part left in the BOM is fitted by the owner; one excluded from the BOM is an unfitted placeholder."""
    ROW = dict(jlc_asm='', fp='C0402', x=10.0, y=10.0, rot=0.0, layer='F.Cu', smd=True, tht=False)

    def export(self, extra):
        spec = importlib.util.spec_from_file_location('export_fab', ROOT / 'tools/export_fab.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rows = module.footprints(BOARD) + [dict(self.ROW, **row) for row in extra]
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'fab'
            log = io.StringIO()
            with patch.object(module, 'footprints', return_value=rows), \
                    patch.object(module, 'run'), \
                    patch.object(module, 'write_manifest', return_value=output / 'manifest.json'), \
                    patch.object(sys, 'argv', ['export_fab.py', str(BOARD), '--out', str(output)]), \
                    redirect_stdout(log):
                module.main()
            files = {name: (output / f'm3_{name}.csv').read_text() if (output / f'm3_{name}.csv').exists() else ''
                     for name in ('bom_jlc', 'bom_owner', 'cpl_jlc')}
        return files, log.getvalue()

    def test_placeholder_is_in_no_bom_or_placement(self):
        files, log = self.export([
            dict(ref='C9001', value='DNP', lcsc='', mpn='', dnp=True, no_bom=True, no_pos=True),
            dict(ref='C9002', value='100nF', lcsc='C1525', mpn='CL05B104KO5NNNC', dnp=True, no_bom=False,
                 no_pos=False)])
        for text in files.values():
            self.assertNotIn('C9001', text)
        self.assertIn('C9002', files['bom_owner'])
        self.assertNotIn('C9002', files['bom_jlc'] + files['cpl_jlc'])
        self.assertRegex(log, r'not fitted \(DNP placeholders[^\n]*C9001')
        self.assertRegex(log, r'owner-fitted[^\n]*C9002')
        self.assertNotRegex(log, r'owner-fitted[^\n]*C9001')

    def test_dnp_without_part_number_must_be_excluded(self):
        with self.assertRaisesRegex(SystemExit, r"without a part number \['C9003'\].*unfitted placeholder"):
            self.export([dict(ref='C9003', value='DNP', lcsc='', mpn='', dnp=True, no_bom=False, no_pos=False)])


class BomLinesByCode(unittest.TestCase):
    """Pass 2 DFM-11: the JLC BOM has one line per LCSC code, whatever the comments say."""
    ROW = DnpPlaceholders.ROW
    export = DnpPlaceholders.export
    FIT = dict(dnp=False, no_bom=False, no_pos=True)    # BOM lines only: no placement correction needed

    def bom(self, extra):
        files, _ = self.export(extra)
        return list(csv.DictReader(io.StringIO(files['bom_jlc'])))

    def test_one_code_with_two_comments_is_one_line(self):
        rows = self.bom([dict(self.FIT, ref='C9101', value='100nF X', lcsc='C9999001', mpn='MPN-A'),
                         dict(self.FIT, ref='C9102', value='100nF Y', lcsc='C9999001', mpn='MPN-A')])
        line = [r for r in rows if r['LCSC Part #'] == 'C9999001']
        self.assertEqual(len(line), 1)
        self.assertEqual(line[0]['Designator'], 'C9101,C9102')
        self.assertEqual(line[0]['Qty'], '2')
        self.assertEqual(line[0]['Comment'], '100nF X; 100nF Y')

    def test_every_board_code_is_on_one_line(self):
        rows = self.bom([])
        codes = [r['LCSC Part #'] for r in rows if r['LCSC Part #']]
        self.assertEqual(len(codes), len(set(codes)))

    def test_one_code_on_two_footprints_stops_the_export(self):
        with self.assertRaisesRegex(SystemExit, r'LCSC C9999002 on several footprints'):
            self.bom([dict(self.FIT, ref='C9103', value='1uF', lcsc='C9999002', mpn='MPN-B'),
                      dict(self.FIT, ref='C9104', value='1uF', lcsc='C9999002', mpn='MPN-B', fp='C0603')])


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
