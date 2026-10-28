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
sys.exit(13 if os.environ.get('FAIL_STAGE') == stage else 0)
'''
        for path in ('quality_audit/verify_board.py', 'tools/silk_check.py', 'tools/fit_check.py',
                     'tools/plate_model.py', 'tools/check_r10.py', 'tools/route_check.py',
                     'm3_design/check_actuators.py'):
            (self.root / path).write_text(stub)
        for path in ('tools/fab_manifest.py', 'tools/test_check_shell.py', 'tools/test_fit_check.py',
                     'tools/test_paste_check.py', 'tools/test_route_check.py', 'tools/test_r10_check.py'):
            (self.root / path).write_text(stub)
        self.log = self.root / 'gate.log'
        self.env = dict(os.environ, KICAD_CLI=str(self.cli), KICAD_PY=sys.executable, NUMPY_PY=sys.executable,
                        GATE_LOG=str(self.log), TMPDIR=str(self.root))

    SELFTESTS = ['test_check_shell', 'test_fit_check', 'test_paste_check', 'test_route_check', 'test_r10_check',
                 'test_r10_check']
    CONTRACTS = ['verify_board', 'silk_check', 'fit_check', 'plate_model', 'check_r10', 'route_check',
                 'check_actuators']

    def run_gate(self, board=None):
        return subprocess.run(['bash', str(self.root / 'tools/check.sh'), str(board or self.root / 'board.kicad_pcb')],
                              env=self.env, capture_output=True, text=True, timeout=30)

    def test_success_requires_all_contracts(self):
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), self.CONTRACTS + self.SELFTESTS)
        self.assertNotIn('fab manifest', result.stdout)      # no fab folder beside the board: nothing to check

    def test_each_new_contract_failure_blocks_later_stages(self):
        stages = ['fit_check', 'plate_model', 'check_r10', 'route_check', 'check_actuators']
        for stage in stages:
            with self.subTest(stage=stage):
                self.log.unlink(missing_ok=True)
                self.env['FAIL_STAGE'] = stage
                result = self.run_gate()
                self.assertEqual(result.returncode, 13, result.stdout + result.stderr)
                self.assertEqual(self.log.read_text().splitlines()[-1], stage)

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

    def test_fab_manifest_binding(self):
        """R8-GATE-05: the repository board must match its fab manifest; a board copy is not held to it."""
        for sub in ('m3_design/assembly_review/fab', 'copy/fab'):
            (self.root / sub).mkdir(parents=True)
            (self.root / sub / 'm3_fab_manifest.json').write_text('{}')
        repo = self.root / 'm3_design/assembly_review/m3.kicad_pcb'
        copy = self.root / 'copy/m3.kicad_pcb'
        result = self.run_gate(copy)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('fab manifest: not checked (board copy)', result.stdout)
        self.assertNotIn('fab_manifest', self.log.read_text())
        self.log.unlink()
        self.assertEqual(self.run_gate(repo).returncode, 0)
        self.assertIn('fab_manifest', self.log.read_text().splitlines())
        self.env['FAIL_STAGE'] = 'fab_manifest'
        result = self.run_gate(repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('fab package bound to a different board: run m3_design/r10_fab.sh', result.stdout)


if __name__ == '__main__':
    unittest.main()
