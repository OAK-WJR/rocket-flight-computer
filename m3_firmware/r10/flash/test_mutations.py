"""Selected fault mutations must fail executable assertions, not compilation."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE=Path(__file__).resolve().parent

class FlashMutations(unittest.TestCase):
    def test_five_core_regressions_are_observed(self):
        source=(HERE/'flash_ro.c').read_text()
        variants=[
            ('quad_gate','if (f->command==FRO_QUAD_ID && !(f->raw[FRO_SR2][0]&2u))',
             'if (0)','qe-disabled'),
            ('cleanup','if (f->io.cancel(f->io.context,&detail)!=FRO_OK)',
             'if ((f->io.cancel(f->io.context,&detail),0))','cleanup'),
            ('last_good','f->valid=0u;++f->failures;f->stage_at=now;',
             'memcpy(f->sample_raw,f->raw,sizeof(f->raw));f->valid=0u;++f->failures;f->stage_at=now;','last-good'),
            ('stale','(uint32_t)(now-f->last_good_ms)<FRO_FRESH_MS',
             '(uint32_t)(now-f->last_good_ms)<=FRO_FRESH_MS','fresh'),
            ('batch_deadline','if ((uint32_t)(now-f->batch_at)>=FRO_BATCH_MS)',
             'if (0)','batch-at-limit'),
        ]
        self.check_variants(source,'core',variants)
    def test_three_register_regressions_are_observed(self):
        source=(HERE/'qspi_port.c').read_text()
        variants=[
            ('ncs_af','{Q_GPIOB,6,10}','{Q_GPIOB,6,9}','good'),
            ('zero_ccr_recovery','write32(p,Q_BASE+Q_CCR,0u);write32(p,Q_BASE+Q_CR,0u);',
             'write32(p,Q_BASE+Q_CCR,0u);','good'),
            ('pin_drift','if (!pins_ok(p)) return Q_FAIL_GPIO;',
             'if (0) return Q_FAIL_GPIO;','drift'),
        ]
        self.check_variants(source,'port',variants)
    def check_variants(self,source,kind,variants):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for name,old,new,case in variants:
                with self.subTest(mutation=name):
                    self.assertEqual(source.count(old),1)
                    modified=out/(name+'.c');modified.write_text(source.replace(old,new))
                    binary=out/name
                    inputs=[str(HERE/'test_flash_ro.c'),str(modified)] if kind=='core' else [
                        str(HERE/'test_qspi.c'),str(modified),str(HERE/'flash_ro.c')]
                    run=subprocess.run([shutil.which('cc'),'-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                        '-Wno-unused-function','-I'+str(HERE),*inputs,'-o',str(binary)],capture_output=True,text=True)
                    self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                    arg=str(0x58020420) if case=='drift' else '0'
                    run=subprocess.run([str(binary),case,arg],capture_output=True,text=True,timeout=5)
                    self.assertNotEqual(run.returncode,0)
                    self.assertIn('Assertion',run.stderr)

if __name__=='__main__':unittest.main(verbosity=2)
