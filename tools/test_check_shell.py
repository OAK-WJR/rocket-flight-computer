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
        for path in ('quality_audit/verify_board.py', 'tools/silk_check.py',
                     'tools/check_r6.py', 'm3_design/check_actuators.py', 'tools/fit_check.py'):
            (self.root / path).write_text('''
import os, pathlib, sys
stage = pathlib.Path(__file__).stem
with open(os.environ['GATE_LOG'], 'a') as log:
    log.write(stage + '\\n')
sys.exit(13 if os.environ.get('FAIL_STAGE') == stage else 0)
''')
        self.log = self.root / 'gate.log'
        self.env = dict(os.environ, KICAD_CLI=str(self.cli), KICAD_PY=sys.executable,
                        GATE_LOG=str(self.log), TMPDIR=str(self.root))

    def run_gate(self):
        return subprocess.run(['bash', str(self.root / 'tools/check.sh'), str(self.root / 'board.kicad_pcb')],
                              env=self.env, capture_output=True, text=True, timeout=20)

    def test_success_requires_all_contracts(self):
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.log.read_text().splitlines(),
                         ['verify_board', 'silk_check', 'check_r6', 'check_actuators', 'fit_check'])

    def test_each_new_contract_failure_blocks_later_stages(self):
        stages = ['check_r6', 'check_actuators', 'fit_check']
        for stage in stages:
            with self.subTest(stage=stage):
                self.log.unlink(missing_ok=True)
                self.env['FAIL_STAGE'] = stage
                result = self.run_gate()
                self.assertEqual(result.returncode, 13, result.stdout + result.stderr)
                self.assertEqual(self.log.read_text().splitlines()[-1], stage)


if __name__ == '__main__':
    unittest.main()
