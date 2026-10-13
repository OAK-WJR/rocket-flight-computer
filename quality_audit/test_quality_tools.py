import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch as mock_patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from fill_part_metadata import fill, identity_preserved, plan
from audit_artifacts import audit

from normalize_metadata import normalize, part_table, table_drift
from sexpr import patch, properties, protected_digest, read
from verify_board import report_findings, verify, erc_findings, input_hashes

BOARD = '''(kicad_pcb (version 20260206)
 (footprint "R0402"
  (property "Reference" "R1") (property "Value" "10k")
  (property "LCSC" "C25744") (property "LCSC Part" "C25900")
  (descr "stale sample part") (at 5 6 90)
  (pad "1" smd rect (at 1 2) (size 0.5 0.6) (net 1 "DATA"))
  (model "kilib/model.wrl" (offset (xyz 1 2 3)) (rotate (xyz 0 0 90)))))'''


class QualityTools(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'kilib').mkdir()
        (self.root / 'kilib/model.wrl').write_text('# VRML model fixture')

    def test_lossless_repair_and_idempotence(self):
        out, changes, models = normalize(BOARD, self.root)
        self.assertEqual(protected_digest(BOARD), protected_digest(out))
        self.assertIn('(property "LCSC Part" "C25744")', out)
        self.assertIn('(rotate (xyz 0 0 90))', out)
        self.assertEqual(len(changes), 2)
        self.assertEqual(models, {Path('kilib/model.wrl')})
        again, changes, _ = normalize(out, self.root)
        self.assertEqual(again, out)
        self.assertEqual(changes, [])

    def test_real_copper_and_model_transform_changes_detected(self):
        before = protected_digest(BOARD)
        self.assertNotEqual(before, protected_digest(BOARD.replace('(at 1 2)', '(at 1 3)')))
        self.assertNotEqual(before, protected_digest(BOARD.replace('xyz 0 0 90', 'xyz 0 0 180')))
        self.assertNotEqual(before, protected_digest(BOARD.replace('"DATA"', '"OTHER"')))

    def test_parser_rejects_truncation_and_duplicate_property(self):
        for text in ('(kicad_pcb', '(kicad_pcb))', '(kicad_pcb "unterminated)', '() ()'):
            with self.assertRaises(ValueError):
                read(text)
        self.assertEqual(read('(a "text ( ) \\\" quote")').items[1].atom, 'text ( ) " quote')
        with self.assertRaises(ValueError):
            properties(read('(footprint "R" (property "LCSC" "C1") (property "LCSC" "C2"))'))
        with self.assertRaises(ValueError):
            patch('(a)', [(0, 2, 'a'), (1, 3, 'b')])

    def test_library_cleanup_keeps_geometry_and_provenance_in_changes(self):
        library = BOARD[BOARD.index(' (footprint'):].strip()[:-1]
        out, changes, _ = normalize(library, self.root, library=True)
        self.assertEqual(protected_digest(library), protected_digest(out))
        self.assertNotIn('(property "LCSC', out)
        self.assertTrue(any(x['before'] == 'C25900' and x['after'] is None for x in changes))

    def test_model_path_escape_and_missing_file_are_rejected(self):
        with self.assertRaises(ValueError):
            normalize(BOARD.replace('kilib/model.wrl', '../outside.wrl'), self.root)
        with self.assertRaises(FileNotFoundError):
            normalize(BOARD.replace('kilib/model.wrl', 'missing.wrl'), self.root)

    def test_literal_table_does_not_execute_builder(self):
        source = self.root / 'parts.py'
        source.write_text('raise RuntimeError("must not run")\n'
                          'PARTS={"R1": ("C999", "R0402", "10k", "sample")}\n')
        drift = table_drift(BOARD, part_table(source))
        self.assertEqual(drift[0]['ref'], 'R1')
        self.assertEqual(drift[0]['PARTS'][0], 'C999')

    def test_report_missing_sections_or_filtered_coverage_fails(self):
        with self.assertRaises(ValueError):
            report_findings({})
        with self.assertRaises(ValueError):
            report_findings({'violations': [], 'unconnected_items': [],
                             'schematic_parity': [], 'included_severities': ['error']})

    def fake_tool(self, report, mutate=False, erc=None):
        def run(args, **kwargs):
            if '--version' in args:
                return subprocess.CompletedProcess(args, 0, 'test-version', '')
            r=report if 'drc' in args else erc or {
                'sheets':[{'violations':[]}], 'included_severities':['error','warning','exclusion'],
                'ignored_checks':[]}
            Path(args[args.index('--output') + 1]).write_text(json.dumps(r))
            if mutate:
                with Path(args[-1]).open('a') as f:
                    f.write('\n')
            # Deliberately return 0 despite violations: gate must inspect report too.
            return subprocess.CompletedProcess(args, 0, '', '')
        return run

    def clean_report(self):
        return {'violations': [], 'unconnected_items': [], 'schematic_parity': [],
                'included_severities': ['error', 'warning', 'exclusion'], 'ignored_checks': []}

    def fixture_board(self):
        board = self.root / 'test.kicad_pcb'
        board.write_text(normalize(BOARD, self.root)[0])
        board.with_suffix('.kicad_sch').write_text('synthetic parity test fixture')
        return board

    def test_zero_exit_does_not_hide_findings(self):
        board = self.fixture_board()
        report = self.clean_report()
        report['unconnected_items'] = [{'type': 'unconnected_items'}]
        with mock_patch('verify_board.subprocess.run', side_effect=self.fake_tool(report)):
            result = verify(board, Path('fake-cli'), self.root / 'evidence.json')
        self.assertFalse(result['ok'])
        self.assertEqual(result['counts']['unconnected_items'], 1)
        self.assertTrue(result['inputs_unchanged'])

    def test_disabled_checks_or_mutated_inputs_fail(self):
        board = self.fixture_board()
        report = self.clean_report()
        report['ignored_checks'] = [{'key': 'missing_courtyard'}]
        with mock_patch('verify_board.subprocess.run', side_effect=self.fake_tool(report, True)):
            result = verify(board, Path('fake-cli'), self.root / 'changed.json')
        self.assertFalse(result['ok'])
        self.assertFalse(result['inputs_unchanged'])
        self.assertTrue(any('disabled' in x for x in result['issues']))

    def test_missing_report_writes_failure_evidence(self):
        board = self.fixture_board()
        with mock_patch('verify_board.subprocess.run', return_value=
                        subprocess.CompletedProcess([], 0, '', '')):
            result = verify(board, Path('fake-cli'), self.root / 'missing.json')
        self.assertFalse(result['ok'])
        self.assertTrue((self.root / 'missing.json').is_file())

    def test_hierarchical_sheet_and_symbol_edit_invalidate_evidence(self):
        board=self.fixture_board();child=self.root/'child.kicad_sch'
        child.write_text('original child');symbol=self.root/'kilib/local.kicad_sym';symbol.write_text('original symbol')
        before=input_hashes(board);child.write_text('wrong GPIO mapping')
        self.assertNotEqual(before,input_hashes(board))
        child.write_text('original child');symbol.write_text('wrong pin numbering')
        self.assertNotEqual(before,input_hashes(board))

    def test_erc_violations_and_disabled_checks_fail_even_with_zero_exit(self):
        board=self.fixture_board()
        for i,erc in enumerate([
                {'sheets':[{'violations':[{'type':'pin_to_pin'}]}], 'ignored_checks':[]},
                {'sheets':[{'violations':[]}], 'ignored_checks':[{'key':'footprint_filter'}]}]):
            erc['included_severities']=['error','warning','exclusion']
            with mock_patch('verify_board.subprocess.run',side_effect=self.fake_tool(self.clean_report(),erc=erc)):
                result=verify(board,Path('fake-cli'),self.root/('erc_%d.json'%i))
            self.assertFalse(result['ok']);self.assertTrue(any('ERC' in s for s in result['issues']))
        with self.assertRaises(ValueError):erc_findings({'sheets':[]})

class PartIdentityTools(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = {'C11702': {'Manufacturer': 'UNI-ROYAL(Uniroyal Elec)',
                                  'Manufacturer Part': '0402WGF1001TCE'}}
        self.board = '''(kicad_pcb (uuid "board-uuid")
 (net 1 "SIGNAL") (segment (start 1 2) (end 3 4) (width 0.2) (net 1) (uuid "track-uuid"))
 (footprint "R0402" (uuid "footprint-uuid") (at 10 20 270) (layer "B.Cu") (attr smd)
  (property "Reference" "R9") (property "Value" "1k")
  (property "LCSC" "C11702" (at 0 0 270) (layer "B.Fab") (hide yes)
    (uuid "acdeeeee-1234-4567-8901-111111111111")
    (effects (font (size 1 1)) (justify mirror)))
  (property "Manufacturer" "" (at 0 0 270) (layer "B.SilkS") (hide yes)
    (uuid "bcdeeeee-1234-4567-8901-111111111111"))
  (pad "1" smd rect (at 0 0) (size 1 1) (net 1 "SIGNAL"))))'''
        self.schematic = '''(kicad_sch (uuid "sheet-uuid")
 (lib_symbols (symbol "Device:R" (property "Manufacturer" "library-untouched")))
 (symbol (lib_id "Device:R") (at 50 50 90) (uuid "symbol-uuid")
  (property "Reference" "R9") (property "Value" "1k")
  (property "LCSC" "C11702" (at 50 50 90) (hide yes)
    (effects (font (size 1 1)) (justify left)))
  (pin "1" (uuid "pin-uuid"))))'''

    def test_fill_preserves_copper_uuid_side_existing_fields_and_is_idempotent(self):
        output, changes = fill(self.board, self.catalog)
        self.assertEqual(len(changes), 2)
        self.assertTrue(identity_preserved(self.board, output, changes))
        old = properties(read(self.board).children('footprint')[0])
        new = properties(read(output).children('footprint')[0])
        self.assertEqual(old['Manufacturer'].children('uuid')[0].value(),
                         new['Manufacturer'].children('uuid')[0].value())
        self.assertNotEqual(new['LCSC'].children('uuid')[0].value(),
                            new['Manufacturer Part'].children('uuid')[0].value())
        for key in ('at', 'layer', 'effects', 'hide'):
            self.assertEqual(new['LCSC'].children(key)[0].value(),
                             new['Manufacturer Part'].children(key)[0].value())
        again, changes2 = fill(output, self.catalog)
        self.assertEqual(again, output)
        self.assertEqual(changes2, [])
        for before, after in [('width 0.2', 'width 0.1'), ('"SIGNAL"', '"OTHER"'),
                              ('"track-uuid"', '"changed-uuid"'), ('at 10 20', 'at 11 20'),
                              ('"bcdeeeee-1234-4567-8901-111111111111"', '"changed"')]:
            self.assertFalse(identity_preserved(self.board, output.replace(before, after), changes))

    def test_only_fitted_parts_require_and_receive_identities(self):
        board = self.root / 'm3.kicad_pcb'
        for attr, expected in [('smd', True), ('through_hole', True), ('smd dnp', False),
                               ('smd exclude_from_bom', False), ('', False)]:
            source = self.board.replace('(attr smd)', '(attr ' + attr + ')')
            board.write_text(source)
            result = audit(board)
            self.assertEqual(bool(result['missing_required_part_fields']), expected)
            repaired, changes = fill(source, self.catalog)
            self.assertEqual(bool(changes), expected)
            board.write_text(repaired)
            self.assertEqual(audit(board)['missing_required_part_fields'], [])
        board.write_text(self.board.replace('"LCSC" "C11702"', '"LCSC" ""'))
        self.assertIn('LCSC', audit(board)['missing_required_part_fields'][0]['fields'])

    def test_schematic_library_and_unfitted_symbols_remain_unchanged(self):
        result, changes = fill(self.schematic, self.catalog, {'R9'})
        self.assertEqual(len(changes), 2)
        self.assertTrue(identity_preserved(self.schematic, result, changes))
        self.assertIn('"library-untouched"', result)
        self.assertEqual(fill(self.schematic, self.catalog, set()), (self.schematic, []))
        self.assertEqual(fill(result, self.catalog, {'R9'}), (result, []))
        with self.assertRaises(ValueError):
            fill(self.schematic, self.catalog)

    def test_unknown_code_conflicting_existing_identity_and_visible_template_fail(self):
        for source in [self.board.replace('C11702', 'C999'),
                       self.board.replace('"Manufacturer" ""', '"Manufacturer" "Wrong"'),
                       self.board.replace('(hide yes)', '(hide no)')]:
            with self.assertRaises(ValueError):
                fill(source, self.catalog)
        complete, _ = fill(self.board, self.catalog)
        complete = complete.replace('UNI-ROYAL(Uniroyal Elec)', 'existing-name')
        self.assertEqual(fill(complete, self.catalog), (complete, []))

    def test_visible_existing_blank_identity_fails_with_hidden_lcsc(self):
        for field in ('Manufacturer', 'Manufacturer Part'):
            for hidden in ('(hide no)', ''):
                source = self.board.replace('"Manufacturer" ""', '"' + field + '" ""')
                node = read(source).children('footprint')[0]
                target = properties(node)[field]
                source = patch(source, [(target.start, target.end,
                                        source[target.start:target.end].replace('(hide yes)', hidden))])
                self.assertEqual(properties(read(source).children('footprint')[0])[
                    'LCSC'].children('hide')[0].items[1].atom, 'yes')
                with self.assertRaisesRegex(ValueError, 'Expected hidden identity target'):
                    fill(source, self.catalog)
                symbol = read(self.schematic).children('symbol')[0]
                source = patch(self.schematic, [(symbol.end - 1, symbol.end - 1,
                                                '(property "' + field + '" "" ' + hidden + ')')])
                with self.assertRaisesRegex(ValueError, 'Expected hidden identity target'):
                    fill(source, self.catalog, {'R9'})

    def test_plan_requires_matching_schematic_and_cli_dry_run_is_nonmutating(self):
        board = self.root / 'm3.kicad_pcb'
        schematic = self.root / 'child.kicad_sch'
        board.write_text(self.board)
        schematic.write_text(self.schematic)
        planned = plan(self.root, self.catalog)
        self.assertEqual(sum(len(c) for _, _, _, c in planned), 4)
        catalog = self.root / 'catalog.json'
        catalog.write_text(json.dumps({'parts': self.catalog, 'source': 'verified test fixture',
                                       'reviewed_date': '2026-10-12'}))
        tool = Path(__file__).resolve().parents[1] / 'tools/fill_part_metadata.py'
        command = [sys.executable, str(tool), '--project', str(self.root), '--catalog', str(catalog)]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        self.assertIn('dry-run: 4 identity fields', result.stdout)
        self.assertEqual(board.read_text(), self.board)
        self.assertEqual(schematic.read_text(), self.schematic)
        subprocess.run(command + ['--write'], capture_output=True, text=True, check=True)
        self.assertEqual(sum(len(c) for _, _, _, c in plan(self.root, self.catalog)), 0)
        schematic.write_text(self.schematic.replace('C11702', 'C999'))
        with self.assertRaises(ValueError):
            plan(self.root, self.catalog)
        schematic.unlink()
        with self.assertRaises(ValueError):
            plan(self.root, self.catalog)

    def test_required_identity_gate_fails_with_clean_drc_and_erc(self):
        board = self.root / 'm3.kicad_pcb'
        board.write_text(self.board)
        board.with_suffix('.kicad_sch').write_text(self.schematic)
        helper = QualityTools()
        with mock_patch('verify_board.subprocess.run', side_effect=helper.fake_tool(helper.clean_report())):
            result = verify(board, Path('fake-cli'), self.root / 'evidence.json')
        self.assertFalse(result['ok'])
        self.assertEqual(result['issues'], ['Missing required fitted-part identity fields'])


if __name__ == '__main__':
    unittest.main()
