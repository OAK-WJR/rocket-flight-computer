"""Transport regressions must compile and fail the expected runtime assertion."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
CHILD = '''
import importlib.util,io,json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(sys.argv[1]).parent))
spec=importlib.util.spec_from_file_location('sd_transport_mutation_tests',sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.HERE=pathlib.Path(sys.argv[2])
result=unittest.TextTestRunner(stream=io.StringIO()).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(getattr(module,sys.argv[3])))
print(json.dumps(dict(tests=result.testsRun,failures=[str(t) for t,_ in result.failures],
                     errors=[str(t) for t,_ in result.errors])))
sys.exit(0 if result.testsRun==int(sys.argv[4]) and result.failures and not result.errors else 1)
'''


class TransportRegressions(unittest.TestCase):
    def reject(self, filename, testfile, cls, count, cases):
        original = (HERE / filename).read_text()
        for name, before, after, occurrences, expected in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                for source in ('wire.h', 'wire.c', 'query.h', 'query.c', 'metadata.h',
                               'metadata.c', 'spi3_port.h', 'spi3_port.c'):
                    shutil.copyfile(HERE / source, root / source)
                self.assertEqual(original.count(before), occurrences)
                (root / filename).write_text(original.replace(before, after))
                run = subprocess.run([sys.executable, '-B', '-c', CHILD, str(HERE / testfile),
                                      str(root), cls, str(count)], capture_output=True,
                                     text=True, timeout=30)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                result = json.loads(run.stdout)
                self.assertEqual(result['errors'], [])
                self.assertTrue(any(expected in n for n in result['failures']), result)

    def test_wire_byte_bounds_continuous_select_and_release_regressions(self):
        self.reject('wire.c', 'test_wire.py', 'ActualWire', 12, (
            ('missing_R1_byte_limit',
             'if (w->prefix_count>=SDW_R1_BYTES)return error(w,SDW_R1_TIMEOUT,0);',
             '/* omitted response byte limit */', 1,
             'test_no_response_and_invalid_prefix_are_bounded_not_absence_claims'),
            ('missing_idle_clocks',
             'if (exchange(w,&tx,&rx,1)!=SDQ_IO_OK)return SDQ_IO_ERROR;',
             '(void)tx;(void)rx;', 1,
             'test_v2_complete_packets_continuous_cs_and_fixed_commands'),
            ('early_CS_high', 'unsigned budget=SDW_POLL_BYTES;',
             'unsigned budget=SDW_POLL_BYTES;\n    if (w->selected && select_card(w,0)!=SDQ_IO_OK)return SDQ_IO_ERROR;', 1,
             'test_v2_complete_packets_continuous_cs_and_fixed_commands'),
            ('missing_release', 'int rc=w->bus.release(w->bus.context,detail);',
             'int rc=SDQ_IO_OK;', 1,
             'test_v2_complete_packets_continuous_cs_and_fixed_commands'),
        ))

    def test_native_register_order_width_ownership_and_cleanup_regressions(self):
        self.reject('spi3_port.c', 'test_spi3.py', 'ActualSPI3', 14, (
            ('missing_final_status_check',
             'p->last_sr=rd(p,SD3_SR);\n if (p->last_sr&(SD3_ERRORS|SD3_SUSP))return fail(p,SD3_STATUS,detail);',
             'p->last_sr=rd(p,SD3_SR);', 1,
             'test_late_EOT_error_is_rechecked_before_clearing_flags'),
            ('missing_CS_preload',
             'wr(p,SD3_GPIOD+SD3_BSRR,1u);modify(p,SD3_GPIOD+SD3_TYPE,1u,0);',
             'modify(p,SD3_GPIOD+SD3_TYPE,1u,0);', 1,
             'test_chip_select_is_preloaded_before_output_mode'),
            ('wrong_reset_register', 'modify(p,SD3_RESET,SD3_GATE,SD3_GATE);',
             'modify(p,SD3_RESET+8u,SD3_GATE,SD3_GATE);', 1,
             'test_full_query_preserves_clock_neighbours_and_releases_owned_SPI3'),
            ('word_TXDR_write', 'p->io.write(p->io.context,SD3_TXDR,tx[i],1);',
             'p->io.write(p->io.context,SD3_TXDR,tx[i],4);', 1,
             'test_full_query_preserves_clock_neighbours_and_releases_owned_SPI3'),
            ('bypassed_clock_policy', 'if (!clock_ok(p))return fail(p,SD3_CLOCK,detail);',
             'if (!clock_ok(p) && 0)return fail(p,SD3_CLOCK,detail);', 4,
             'test_wrong_shared_clock_is_read_only_and_no_command'),
            ('missing_cleanup_gate_readback', 'if (rd(p,SD3_ENABLE)&SD3_GATE)ok=0;',
             '(void)rd(p,SD3_ENABLE);', 1,
             'test_failed_clock_gating_never_claims_successful_cleanup'),
        ))


if __name__ == '__main__':
    unittest.main()
