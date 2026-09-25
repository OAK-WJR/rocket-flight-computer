import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch as mock_patch

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


if __name__ == '__main__':
    unittest.main()
