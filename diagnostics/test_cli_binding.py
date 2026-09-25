"""An explicitly selected candidate profile must survive the CLI boundary."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from .engine import HERE


class BindingCLI(unittest.TestCase):
    def test_explicit_profile_and_default_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            snapshot=json.loads((HERE/'examples/blank_firmware/snapshot.json').read_text())
            self.assertEqual(snapshot['origin'],'SYNTHETIC_FIXTURE')
            binding=json.loads((HERE/'board_binding.json').read_text())
            binding['board_sha256']=snapshot['board_sha256']='a'*64
            (p/'binding.json').write_text(json.dumps(binding));(p/'snapshot.json').write_text(json.dumps(snapshot))
            command=[sys.executable,'-m','diagnostics','report',str(p/'snapshot.json'),'--out']
            a=subprocess.run(command+[str(p/'explicit'),'--binding',str(p/'binding.json')],cwd=HERE.parent,capture_output=True,text=True,timeout=10)
            self.assertIn(a.returncode,(0,2),a.stderr)
            report=json.loads((p/'explicit/report.json').read_text())
            self.assertEqual(report['board_sha256'],'a'*64)
            b=subprocess.run(command+[str(p/'default')],cwd=HERE.parent,capture_output=True,text=True,timeout=10)
            self.assertEqual(b.returncode,3,b.stdout+b.stderr)
            self.assertFalse((p/'default/report.json').exists())
    def test_profile_template_retains_probe_coordinates(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);snapshot=json.loads((HERE/'examples/blank_firmware/snapshot.json').read_text())
            self.assertEqual(snapshot['origin'],'SYNTHETIC_FIXTURE')
            binding=json.loads((HERE/'board_binding.json').read_text());binding['probes']['3V3']['board_xy_mm']=[41.81,94.5]
            (p/'binding.json').write_text(json.dumps(binding));(p/'snapshot.json').write_text(json.dumps(snapshot))
            a=subprocess.run([sys.executable,'-m','diagnostics','bench-template',str(p/'snapshot.json'),
                              '--binding',str(p/'binding.json'),'--out',str(p/'bench.json')],cwd=HERE.parent,capture_output=True,text=True,timeout=10)
            self.assertEqual(a.returncode,0,a.stderr)
            reading=json.loads((p/'bench.json').read_text())
            self.assertTrue(all(q['measurement'] is None for q in reading['points']))
            self.assertEqual(next(q for q in reading['points'] if q['net']=='3V3')['board_xy_mm'],[41.81,94.5])
