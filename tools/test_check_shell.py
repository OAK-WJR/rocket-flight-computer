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
r11 = '--profile' in sys.argv and sys.argv[sys.argv.index('--profile') + 1] == 'r11' or \\
    any('r11' in pathlib.Path(a).parts for a in sys.argv[1:])
label = stage + ('@r11' if r11 else '')
if stage == 'test_r11_check' and os.environ.get('R11_BOARD'):     # the R11 section hands its board to the self-test
    label += '+R11_BOARD' + ('+required' if os.environ.get('R11_BOARD_REQUIRED') == '1' else '')
with open(os.environ['GATE_LOG'], 'a') as log:
    log.write(label + '\\n')
if stage == 'r10_parts' and ('--check' not in sys.argv or '--board' not in sys.argv):
    sys.exit(17)
if stage.startswith('fab_manifest') and not (pathlib.Path(sys.argv[1]).parent / 'fab/m3_fab_manifest.json').is_file():
    sys.exit(19)
if stage.startswith('fab_manifest') and '--content' not in sys.argv:      # R18-GATE-04: the binding alone is not enough
    sys.exit(23)
if stage == 'fit_check' and r11 and sys.argv[sys.argv.index('--profile') + 1] != 'r11':
    sys.exit(29)
sys.exit(13 if os.environ.get('FAIL_STAGE') in (stage, label) else 0)
'''
        for path in ('quality_audit/verify_board.py', 'tools/silk_check.py', 'tools/fit_check.py',
                     'tools/plate_model.py', 'tools/check_r10.py', 'tools/route_check.py',
                     'm3_design/check_actuators.py', 'm3_design/r10_parts.py', 'm3_design/r10_sch_check.py',
                     'tools/check_r11.py', 'm3_design/r11_sch_check.py'):
            (self.root / path).write_text(stub)
        for path in ('tools/fab_manifest.py', 'tools/fab_manifest_r11.py', 'tools/test_r11_check.py',
                     'tools/test_check_shell.py', 'tools/test_procurement.py',
                     'tools/test_fab_validation.py', 'tools/test_fit_check.py', 'tools/test_paste_check.py',
                     'tools/test_r10_parts.py', 'tools/test_route_check.py', 'tools/test_r10_check.py'):
            (self.root / path).write_text(stub)
        self.log = self.root / 'gate.log'
        self.env = dict(os.environ, KICAD_CLI=str(self.cli), KICAD_PY=sys.executable, NUMPY_PY=sys.executable,
                        GATE_LOG=str(self.log), TMPDIR=str(self.root))
        self.env.pop('R10_SKIP_FAB_MANIFEST', None)
        for key in ('R11_BOARD', 'R11_BOARD_REQUIRED'):
            self.env.pop(key, None)
        (self.root / 'board.kicad_pcb').write_text('board copy\n')

    SELFTESTS = ['test_check_shell', 'test_procurement', 'test_fab_validation', 'test_fit_check', 'test_paste_check',
                 'test_r10_parts', 'test_route_check', 'test_r10_check', 'test_r10_check', 'test_r11_check']
    CONTRACTS = ['r10_sch_check', 'verify_board', 'silk_check', 'r10_parts', 'fit_check', 'check_r10', 'route_check']
    R11_CONTRACTS = ['r11_sch_check@r11', 'verify_board@r11', 'silk_check@r11', 'fit_check@r11', 'check_r11@r11',
                     'route_check@r11']
    R11_TEXT = '(kicad_pcb (title_block (title "M3") (rev "M3-ASSY-R11")))\n'

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


    # ---- R11 section (D-R11-08) ----------------------------------------------------------------------------------------
    def r11_board(self, manifest=True, track=True):
        """The repository R11 board of the temporary tree, tracked by a git index there unless told otherwise."""
        board = self.root / 'm3_design/r11/m3.kicad_pcb'
        (board.parent / 'fab').mkdir(parents=True, exist_ok=True)
        board.write_text(self.R11_TEXT)
        if manifest:
            (board.parent / 'fab/m3_fab_manifest.json').write_text('{}')
        if track:
            subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
            subprocess.run(['git', '-C', str(self.root), 'add', 'm3_design/r11/m3.kicad_pcb'], check=True)
        return board

    def selftests_r11(self, required=True):
        return self.SELFTESTS[:-1] + ['test_r11_check+R11_BOARD' + ('+required' if required else '')]

    def test_r11_section_runs_after_r10_when_the_board_is_tracked(self):
        self.r11_board()
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.log.read_text().splitlines(),
                         self.CONTRACTS + self.R11_CONTRACTS + ['fab_manifest_r11@r11'] + self.selftests_r11())
        self.assertIn('== R11 gate:', result.stdout)

    def test_an_untracked_r11_board_does_not_run_the_r11_section(self):
        self.r11_board(track=False)
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), self.CONTRACTS + self.SELFTESTS)

    def test_a_stale_r11_board_variable_is_not_handed_to_the_selftest(self):
        self.env.update(R11_BOARD=str(self.root / 'board.kicad_pcb'), R11_BOARD_REQUIRED='1')
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.log.read_text().splitlines()[-1], 'test_r11_check')

    def test_each_r11_stage_failure_fails_the_gate(self):
        self.r11_board()
        for stage in self.R11_CONTRACTS + ['fab_manifest_r11@r11']:
            with self.subTest(stage=stage):
                self.log.unlink(missing_ok=True)
                self.env['FAIL_STAGE'] = stage
                result = self.run_gate()
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(self.log.read_text().splitlines()[-1], stage)

    def test_r11_schematic_contract_is_required_while_the_board_exists(self):
        self.r11_board()
        (self.root / 'm3_design/r11_sch_check.py').unlink()
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('r11_sch_check.py missing', result.stdout)
        self.assertEqual(self.log.read_text().splitlines(), self.CONTRACTS)

    def test_r11_repository_package_is_required(self):
        self.r11_board(manifest=False)
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.log.read_text().splitlines()[-1], 'fab_manifest_r11@r11')
        self.assertIn('R11 fab package unbound', result.stdout)

    def test_r11_package_needs_its_content_checks(self):
        self.r11_board()
        script = self.root / 'tools/check.sh'
        script.write_text(script.read_text().replace('"$CANON11" --content', '"$CANON11"'))
        self.assertNotEqual(self.run_gate().returncode, 0)
        self.assertEqual(self.log.read_text().splitlines()[-1], 'fab_manifest_r11@r11')

    def test_r11_fit_must_use_the_r11_profile(self):
        self.r11_board()
        script = self.root / 'tools/check.sh'
        script.write_text(script.read_text().replace('"$R11" --profile r11 --report "$O11/fit.json"',
                                                     '"$R11" --profile r10 --report "$O11/fit.json"'))
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_an_explicit_r11_board_runs_the_r11_section_alone(self):
        copy = self.root / 'copy/r11/m3.kicad_pcb'
        (copy.parent / 'fab').mkdir(parents=True)
        copy.write_text(self.R11_TEXT)
        (copy.parent / 'fab/m3_fab_manifest.json').write_text('{}')
        result = self.run_gate(copy)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), self.R11_CONTRACTS + self.selftests_r11())
        self.assertIn('R11 fab manifest: not checked (board copy)', result.stdout)
        self.log.unlink()
        self.env['FAIL_STAGE'] = 'check_r11@r11'
        self.assertNotEqual(self.run_gate(copy).returncode, 0)
        self.assertEqual(self.log.read_text().splitlines()[-1], 'check_r11@r11')

    def test_a_tracked_but_missing_r11_board_fails(self):
        board = self.r11_board()
        board.unlink()
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('R11 board tracked but missing', result.stderr)


    def test_a_parse_error_anywhere_fails_before_any_stage(self):
        """A syntax error late in check.sh must not let the earlier stages run and the EXIT trap end with status 0."""
        script = self.root / 'tools/check.sh'
        text = script.read_text()
        marker = 'selftest python3 "$ROOT/tools/test_check_shell.py"'
        self.assertIn(marker, text)
        script.write_text(text.replace(marker, 'if ) then\n' + marker))
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('does not parse', result.stderr)
        self.assertFalse(self.log.exists())

    def test_the_exit_trap_keeps_a_failing_status(self):
        """With the parse self-check removed, a late failure still exits non-zero through the EXIT trap."""
        script = self.root / 'tools/check.sh'
        text = script.read_text().replace('bash -n "$0" ||', 'true ||')
        script.write_text(text)
        self.env['FAIL_STAGE'] = 'test_r11_check'
        result = self.run_gate()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('reports:', result.stdout)

if __name__ == '__main__':
    unittest.main()
