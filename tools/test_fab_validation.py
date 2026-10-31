"""Manufacturing regressions: missing or corrupt placements must block release, and no package is bound unchecked.

Some tests (test_current_package, ContentChecks) judge the fab package in m3_design/assembly_review/fab/ against the
current board, so after any copper or placement change run the fab step (m3_design/r10_fab.sh) before this suite
(R8P3-INTEGRITY-02). tools/check.sh runs it (R18-GATE-04): export_fab.py writes no manifest; fab_manifest.bind() writes
it only after the content checks (S-4 on the BOM / CPL, jlc_orient --verify-cpl, paste_check) pass.
"""
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
sys.path.insert(0, str(ROOT / 'tools'))

BOARD = ROOT / 'm3_design/assembly_review/m3.kicad_pcb'      # the board the fab package was made from (r10_fab.sh)
CPL = ROOT / 'm3_design/assembly_review/fab/m3_cpl_jlc.csv'


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
        """R10's connector retention lands are matched pad by pad, not only the signal pins: J3's USB-C shell tabs
        (C165948 pads 1-4) and J430's microSD fitting nails (C164170 pads 9-12, G2-G4 / G1). R9's JST GH J9 (C161692,
        unnumbered tabs mapped to EasyEDA 5 / 6 by jlc_orient.MECHANICAL) is not on R10, whose J9 is a DB125 terminal
        with no tab: that case is retired with R9's connector."""
        for ref, code, tabs in (('J3', 'C165948', ('1', '2')), ('J430', 'C164170', ('9', '10'))):
            with self.subTest(ref=ref):
                self.pad_data = json.loads((ROOT / 'tools/jlc_easyeda/pads.json').read_text())
                changed = []
                for pad in self.pad_data[code]['pads']:
                    fields = pad.split('~')
                    if fields[8] in tabs:
                        fields[2] = str(float(fields[2]) + 10)  # 2.54 mm shifted retention tabs
                    changed.append('~'.join(fields))
                self.pad_data[code]['pads'] = changed
                self.assertIn(f"('{ref}', ", self.verify())


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
                    patch.object(sys, 'argv', ['export_fab.py', str(BOARD), '--out', str(output)]), \
                    redirect_stdout(log):
                module.main()
            self.assertFalse((output / 'm3_fab_manifest.json').exists())     # R18-GATE-04: an export never binds
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


class Binding(unittest.TestCase):
    """R18-GATE-04: the manifest is written only by bind(), after every content check passed on an unchanged export."""
    def setUp(self):
        ManifestValidation.setUp(self)                      # the same fixture project, without its tests
        self.path.unlink()                                  # an export leaves the package unbound
        self.record = self.folder / 'export.json'
        self.manifest.write_pending(self.board, self.out, self.manifest.input_hashes(self.board), self.record)

    def bind(self, failures=()):
        with patch.object(self.manifest, 'run_content_checks', return_value=list(failures)) as checks:
            path = self.manifest.bind(self.board, self.out, self.record, kicad_py='kicad-python', echo=lambda *a: None)
        checks.assert_called_once()
        return path

    def test_record_is_not_a_manifest(self):
        self.assertTrue(self.record.is_file())
        with self.assertRaises(OSError):
            self.manifest.verify_manifest(self.board, self.out)

    def test_each_failing_content_check_leaves_the_package_unbound(self):
        for label in ('S-4 BOM / CPL', 'CPL rebuilt from JLC footprints', 'paste openings'):
            with self.subTest(check=label):
                with self.assertRaisesRegex(ValueError, 'content checks failed.*not bound'):
                    self.bind([(label, 1)])
                self.assertFalse(self.path.exists())
                self.assertTrue(self.record.is_file())

    def test_passing_checks_bind_the_export(self):
        self.assertEqual(self.bind(), self.path)
        self.assertEqual(self.manifest.verify_manifest(self.board, self.out), 5)
        self.assertFalse(self.record.exists())

    def test_changes_since_the_export_refuse_to_bind(self):
        (self.out / 'm3_cpl_jlc.csv').write_text('edited placement\n')
        with self.assertRaisesRegex(ValueError, 'outputs changed since the export'):
            self.bind()
        (self.out / 'm3_cpl_jlc.csv').write_text('export fixture\n')
        self.board.write_text('changed copper\n')
        with self.assertRaisesRegex(ValueError, 'inputs changed since the export'):
            self.bind()
        self.assertFalse(self.path.exists())

    def test_content_checks_are_the_three_validators_on_the_package(self):
        checks = dict(self.manifest.content_checks(self.board, self.out, 'kicad-python'))
        s4 = checks['S-4 BOM / CPL']
        self.assertEqual(s4[:3], ['kicad-python', '-I', str(ROOT / 'tools/check_r10.py')])
        self.assertEqual(s4[3:], [str(self.board), '--only', 'S-4', '--bom', str(self.out / 'm3_bom_jlc.csv'),
                                  '--cpl', str(self.out / 'm3_cpl_jlc.csv')])
        cpl = checks['CPL rebuilt from JLC footprints']
        self.assertEqual(cpl[2:], [str(ROOT / 'tools/jlc_orient.py'), str(ROOT / 'tools/jlc_easyeda/pads.json'),
                                   str(self.board), '--verify-cpl', str(self.out / 'm3_cpl_jlc.csv')])
        self.assertEqual(checks['paste openings'][2:], [str(ROOT / 'tools/paste_check.py'), str(self.board),
                                                        str(self.out / 'm3_gerber.zip')])

    def test_cli_content_and_bind_run_the_content_checks(self):
        """The command lines check.sh (--content) and r10_fab.sh (--bind) use run every content check and fail on any
        one; a stand-in KiCad Python fails only the check named in FAIL_CHECK."""
        fake = self.folder / 'kicad-python'
        fake.write_text('#!/bin/sh\ncase "$2" in *"$FAIL_CHECK"*) echo "seeded failure in $2"; exit 3;; esac\n'
                        'echo "$2 OK"\n')                     # argv: -I TOOL BOARD ...: $2 is the check's script
        fake.chmod(0o755)
        tool = str(ROOT / 'tools/fab_manifest.py')

        def cli(*args, fail='none'):
            env = dict(os.environ, KICAD_PY=str(fake), FAIL_CHECK=fail)
            return subprocess.run([sys.executable, tool, str(self.board), *args], capture_output=True, text=True,
                                  env=env, timeout=60)
        for script in ('check_r10.py', 'jlc_orient.py', 'paste_check.py'):
            with self.subTest(failing=script):
                result = cli('--bind', str(self.record), fail=script)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('seeded failure', result.stdout)
                self.assertFalse(self.path.exists())
        result = cli('--bind', str(self.record))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(sum(line.startswith('fab content check ') and ': OK (' in line
                             for line in result.stdout.splitlines()), 3, result.stdout)
        self.assertTrue(self.path.exists())
        result = cli('--content', fail='paste_check.py')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('content checks failed: paste openings', result.stderr)
        result = cli()                                          # the plain verify: hashes only, no checks run
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('content check', result.stdout)

    def test_export_records_but_never_binds(self):
        """export_fab.py deletes a stale manifest and, with --pending, records the export for bind()."""
        spec = importlib.util.spec_from_file_location('export_fab', ROOT / 'tools/export_fab.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rows = module.footprints(BOARD)

        def fake_cli(*args):
            target = Path(args[args.index('-o') + 1])
            if target.suffix == '.pdf':
                target.write_text('drawing fixture\n')
        output = self.folder / 'export'
        output.mkdir()
        (output / 'm3_fab_manifest.json').write_text('{"schema": 1}')
        record = self.folder / 'record.json'
        for argv in ([], ['--pending', str(record)]):
            with self.subTest(argv=argv), patch.object(module, 'footprints', return_value=rows), \
                    patch.object(module, 'run', side_effect=fake_cli), \
                    patch.object(sys, 'argv', ['export_fab.py', str(BOARD), '--out', str(output), *argv]), \
                    redirect_stdout(io.StringIO()) as log:
                module.main()
                self.assertFalse((output / 'm3_fab_manifest.json').exists())
                self.assertEqual(record.is_file(), bool(argv), log.getvalue())
        data = json.loads(record.read_text())
        self.assertEqual(data['inputs_sha256'], self.manifest.input_hashes(BOARD))
        self.assertEqual(sorted(data['outputs_sha256']), sorted(self.manifest.output_names(BOARD, output)))


@unittest.skipUnless(Path(KICAD_PY).exists() or shutil.which(KICAD_PY), 'KiCad Python required')
class ContentChecks(unittest.TestCase):
    """R18-GATE-04 seeds on a copy of the repository package: each content check passes on the real package and fails
    on its seed (s17: D9's CPL row turned 180 deg; s18: R134's BOM code swapped; the bottom paste layer missing)."""
    def setUp(self):
        import fab_manifest
        self.manifest = fab_manifest
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / 'fab'
        shutil.copytree(BOARD.parent / 'fab', self.out)

    def check(self, label):
        argv = dict(self.manifest.content_checks(BOARD, self.out, KICAD_PY))[label]
        return subprocess.run(argv, capture_output=True, text=True, timeout=300)

    def rows(self, name):
        with (self.out / name).open(newline='') as source:
            reader = csv.DictReader(source)
            return reader.fieldnames, list(reader)

    def write(self, name, fields, rows):
        with (self.out / name).open('w', newline='') as target:
            writer = csv.DictWriter(target, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_real_package_passes_every_content_check(self):
        self.assertEqual(self.manifest.run_content_checks(BOARD, self.out, KICAD_PY, echo=lambda *a: None), [])

    def test_reversed_polarised_placement_fails(self):
        fields, rows = self.rows('m3_cpl_jlc.csv')
        row = next(r for r in rows if r['Designator'] == 'D9')
        row['Rotation'] = str((float(row['Rotation']) + 180) % 360)
        self.write('m3_cpl_jlc.csv', fields, rows)
        result = self.check('CPL rebuilt from JLC footprints')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("('D9', ", result.stdout + result.stderr)

    def test_substituted_bom_code_fails(self):
        fields, rows = self.rows('m3_bom_jlc.csv')
        row = next(r for r in rows if 'R134' in r['Designator'].split(','))
        self.assertEqual(row['LCSC Part #'], 'C3013496')
        row['LCSC Part #'] = 'C25744'
        self.write('m3_bom_jlc.csv', fields, rows)
        result = self.check('S-4 BOM / CPL')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('R134 LCSC Part #', result.stdout)

    def test_missing_paste_layer_fails(self):
        import zipfile
        source = self.out / 'm3_gerber.zip'
        kept = self.out / 'kept.zip'
        with zipfile.ZipFile(source) as old, zipfile.ZipFile(kept, 'w') as new:
            for info in old.infolist():
                if 'B_Paste' not in info.filename:
                    new.writestr(info, old.read(info))
        kept.replace(source)
        self.assertNotEqual(self.check('paste openings').returncode, 0)


if __name__ == '__main__':
    unittest.main()
