"""Release gate must execute each native contract and propagate every failure."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class GateSequence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ('tools', 'quality_audit', 'm3_design'):
            (self.root / directory).mkdir()
        shutil.copyfile(Path(__file__).with_name('check.sh'), self.root / 'tools/check.sh')
        self.cli = self.root / 'kicad-cli'
        self.cli.write_text('#!' + sys.executable + '\n' + '''
import json, pathlib, sys
report = {'violations': [], 'unconnected_items': [], 'schematic_parity': []}
if sys.argv[1] == 'sch':
    report = {'sheets': [{'violations': []}]}
pathlib.Path(sys.argv[sys.argv.index('-o') + 1]).write_text(json.dumps(report))
''')
        self.cli.chmod(0o755)
        stub = '''
import os, pathlib, sys
stage = pathlib.Path(__file__).stem
with open(os.environ['GATE_LOG'], 'a') as log:
    log.write(stage + '\\n')
if stage == 'r10_parts' and ('--check' not in sys.argv or '--board' not in sys.argv):
    sys.exit(17)
if stage == 'fab_manifest' and not (pathlib.Path(sys.argv[1]).parent / 'fab/m3_fab_manifest.json').is_file():
    sys.exit(19)
if stage == 'fab_manifest' and '--content' not in sys.argv:      # R18-GATE-04: the binding alone is not enough
    sys.exit(23)
sys.exit(13 if os.environ.get('FAIL_STAGE') == stage else 0)
'''
        for path in ('quality_audit/verify_board.py', 'tools/silk_check.py', 'tools/fit_check.py',
                     'tools/plate_model.py', 'tools/check_r10.py', 'tools/route_check.py',
                     'm3_design/check_actuators.py', 'm3_design/r10_parts.py', 'm3_design/r10_sch_check.py'):
            (self.root / path).write_text(stub)
        for path in ('tools/fab_manifest.py', 'tools/test_check_shell.py', 'tools/test_procurement.py',
                     'tools/test_fab_validation.py', 'tools/test_fit_check.py', 'tools/test_paste_check.py',
                     'tools/test_r10_parts.py', 'tools/test_route_check.py', 'tools/test_r10_check.py'):
            (self.root / path).write_text(stub)
        self.log = self.root / 'gate.log'
        self.env = dict(os.environ, KICAD_CLI=str(self.cli), KICAD_PY=sys.executable, NUMPY_PY=sys.executable,
                        GATE_LOG=str(self.log), TMPDIR=str(self.root))
        self.env.pop('R10_SKIP_FAB_MANIFEST', None)
        (self.root / 'board.kicad_pcb').write_text('board copy\n')

    SELFTESTS = ['test_check_shell', 'test_procurement', 'test_fab_validation', 'test_fit_check', 'test_paste_check',
                 'test_r10_parts', 'test_route_check', 'test_r10_check', 'test_r10_check']
    CONTRACTS = ['r10_sch_check', 'verify_board', 'silk_check', 'r10_parts', 'fit_check', 'check_r10', 'route_check']

    def run_gate(self, board=None):
        return subprocess.run(['bash', str(self.root / 'tools/check.sh'), str(board or self.root / 'board.kicad_pcb')],
                              env=self.env, capture_output=True, text=True, timeout=30)

    def repo_board(self, manifest=True):
        """The repository board of the temporary tree (with its fab manifest unless told otherwise)."""
        repo = self.root / 'm3_design/assembly_review/m3.kicad_pcb'
        (repo.parent / 'fab').mkdir(parents=True, exist_ok=True)
        repo.write_text('repository board\n')
        if manifest:
            (repo.parent / 'fab/m3_fab_manifest.json').write_text('{}')
        return repo

    def test_success_requires_all_contracts(self):
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), self.CONTRACTS + self.SELFTESTS)
        self.assertNotIn('fab manifest', result.stdout)      # no fab folder beside the board: nothing to check

    def test_each_new_contract_failure_blocks_later_stages(self):
        stages = ['r10_parts', 'fit_check', 'check_r10', 'route_check']
        for stage in stages:
            with self.subTest(stage=stage):
                self.log.unlink(missing_ok=True)
                self.env['FAIL_STAGE'] = stage
                result = self.run_gate()
                self.assertEqual(result.returncode, 13, result.stdout + result.stderr)
                self.assertEqual(self.log.read_text().splitlines()[-1], stage)

    def test_sheet_replay_failure_stops_the_gate(self):
        """D-R23-10 (R23-GATE-06): check.sh runs the schematic contract and sheet replay (r10_sch_check) first; its
        failure (a hand-edited sheet note) fails the gate before any later stage runs."""
        self.env['FAIL_STAGE'] = 'r10_sch_check'
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('schematic contract / sheet replay FAILED', result.stdout)
        self.assertEqual(self.log.read_text().splitlines(), ['r10_sch_check'])

    def test_parts_budget_stage_must_check_without_regenerating(self):
        script = self.root / 'tools/check.sh'
        script.write_text(script.read_text().replace('--check --board', '--board'))
        result = self.run_gate()
        self.assertEqual(result.returncode, 17, result.stdout + result.stderr)
        self.assertEqual(self.log.read_text().splitlines()[-1], 'r10_parts')

    def test_each_selftest_failure_fails_the_gate(self):
        """R8-GATE-01: a failing gate self-test makes check.sh exit non-zero and later self-tests do not run."""
        for stage in sorted(set(self.SELFTESTS)):
            with self.subTest(stage=stage):
                self.log.unlink(missing_ok=True)
                self.env['FAIL_STAGE'] = stage
                result = self.run_gate()
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('gate self-test FAILED', result.stdout)
                self.assertEqual(self.log.read_text().splitlines()[-1], stage)

    def test_missing_board_fails_before_any_stage(self):
        result = self.run_gate(self.root / 'absent/m3.kicad_pcb')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('board not found', result.stderr)
        self.assertFalse(self.log.exists())

    def test_fab_manifest_binding(self):
        """R8-GATE-05: the repository board must match its fab manifest; a board copy is not held to it."""
        repo = self.repo_board()
        (self.root / 'copy/fab').mkdir(parents=True)
        (self.root / 'copy/fab/m3_fab_manifest.json').write_text('{}')
        copy = self.root / 'copy/m3.kicad_pcb'
        copy.write_text('repository board\n')                   # same bytes, another file: still a copy
        result = self.run_gate(copy)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('fab manifest: not checked (board copy)', result.stdout)
        self.assertNotIn('fab_manifest', self.log.read_text())
        self.log.unlink()
        (copy.parent / 'fab/m3_fab_manifest.json').unlink()
        result = self.run_gate(copy)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('fab manifest', result.stdout)
        self.assertEqual(self.log.read_text().splitlines(), self.CONTRACTS + self.SELFTESTS)
        self.log.unlink()
        self.assertEqual(self.run_gate(repo).returncode, 0)
        self.assertEqual(self.log.read_text().splitlines(), self.CONTRACTS + ['fab_manifest'] + self.SELFTESTS)
        self.env['FAIL_STAGE'] = 'fab_manifest'
        result = self.run_gate(repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('failing its content checks: run m3_design/r10_fab.sh', result.stdout)

    def test_canonical_manifest_is_required(self):
        """R17-GATE-01: a missing repository manifest must reach its verifier and stop the gate."""
        repo = self.repo_board(manifest=False)
        result = self.run_gate(repo)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), self.CONTRACTS + ['fab_manifest'])
        self.assertIn('run m3_design/r10_fab.sh', result.stdout)

    def test_repository_package_needs_its_content_checks(self):
        """R18-GATE-04: the repository branch asks the verifier for the content checks, not the hashes alone."""
        repo = self.repo_board()
        script = self.root / 'tools/check.sh'
        script.write_text(script.read_text().replace('"$CANON" --content', '"$CANON"'))
        result = self.run_gate(repo)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), self.CONTRACTS + ['fab_manifest'])

    def test_repository_board_is_recognised_by_identity(self):
        """R18-GATE-05: another spelling of the repository board (a symlinked folder; a case variant on a
        case-insensitive volume) is the repository board, held to its package; it is not a board copy."""
        repo = self.repo_board()
        (self.root / 'alias').symlink_to(repo.parent, target_is_directory=True)
        spellings = [self.root / 'alias/m3.kicad_pcb',
                     self.root / 'm3_design/assembly_review/../assembly_review/m3.kicad_pcb']
        upper = self.root / 'M3_DESIGN/assembly_review/m3.kicad_pcb'
        if upper.exists():                                       # macOS / Windows default volumes
            spellings.append(upper)
        self.env['FAIL_STAGE'] = 'fab_manifest'
        for board in spellings:
            with self.subTest(board=str(board.relative_to(self.root))):
                self.log.unlink(missing_ok=True)
                result = self.run_gate(board)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn('not checked (board copy)', result.stdout)
                self.assertEqual(self.log.read_text().splitlines(), self.CONTRACTS + ['fab_manifest'])

    def test_skip_flag_no_longer_skips_the_package(self):
        """R18-GATE-05: the former build-stage flag R10_SKIP_FAB_MANIFEST has no effect: the package is still checked."""
        repo = self.repo_board()
        for flag in ('1', 'yes'):
            with self.subTest(flag=flag):
                self.env.update(R10_SKIP_FAB_MANIFEST=flag, FAIL_STAGE='fab_manifest')
                self.log.unlink(missing_ok=True)
                result = self.run_gate(repo)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn('not checked', result.stdout)
                self.assertEqual(self.log.read_text().splitlines(), self.CONTRACTS + ['fab_manifest'])
        self.assertNotIn('R10_SKIP_FAB_MANIFEST', (Path(__file__).with_name('check.sh')).read_text())


if __name__ == '__main__':
    unittest.main()
