"""Compiled regressions must be caught by behavioural C tests, not build errors."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
CHILD='''
import importlib.util,io,json,pathlib,sys,unittest
spec=importlib.util.spec_from_file_location("sd_metadata_mutation_tests",sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.HERE=pathlib.Path(sys.argv[2])
suite=unittest.defaultTestLoader.loadTestsFromTestCase(module.ActualC)
result=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
print(json.dumps(dict(tests=result.testsRun,failures=[str(t) for t,_ in result.failures],errors=[str(t) for t,_ in result.errors])))
sys.exit(0 if result.testsRun==18 and result.failures and not result.errors else 1)
'''
QUERY_CHILD='''
import importlib.util,io,json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(sys.argv[1]).parent))
spec=importlib.util.spec_from_file_location("sd_query_mutation_tests",sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.HERE=pathlib.Path(sys.argv[2])
suite=unittest.defaultTestLoader.loadTestsFromTestCase(module.ActualQuery)
result=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
print(json.dumps(dict(tests=result.testsRun,failures=[str(t) for t,_ in result.failures],errors=[str(t) for t,_ in result.errors])))
sys.exit(0 if result.testsRun==21 and result.failures and not result.errors else 1)
'''


class CompiledRegressions(unittest.TestCase):
    def test_four_real_compiled_regressions_fail_the_independent_behaviour_tests(self):
        original=(HERE/'metadata.c').read_text()
        cases=(
            ('crc16_seed','uint16_t crc=0;','uint16_t crc=0xffffu;',
             'test_native_structure_and_standard_crc16_vector'),
            ('capacity32','((uint64_t)size+1u)<<19','((uint32_t)size+1u)<<19',
             'test_csd_capacity_extremes_use_64_bit_math'),
            ('block_read_opcode','{0,8,59,55,41,41,58,9,10}','{0,8,59,55,41,41,58,9,17}',
             'test_known_cmd0_cmd8_crc_and_all_fixed_frames'),
            ('skip_wire_crc','if (crc16(p+2,16u)!=','if (0 && crc16(p+2,16u)!=',
             'test_every_single_register_packet_bit_error_is_detected'),
        )
        for name,before,after,expected_failure in cases:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                self.assertEqual(original.count(before),1)
                (root/'metadata.c').write_text(original.replace(before,after,1))
                (root/'metadata.h').write_bytes((HERE/'metadata.h').read_bytes())
                run=subprocess.run([sys.executable,'-B','-c',CHILD,str(HERE/'test_metadata.py'),str(root)],
                                   capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                result=json.loads(run.stdout)
                self.assertEqual(result['tests'],18);self.assertEqual(result['errors'],[])
                self.assertTrue(any(expected_failure in n for n in result['failures']))

    def test_query_deadline_ownership_and_cleanup_regressions_fail_at_runtime(self):
        original=(HERE/'query.c').read_text()
        cases=(
            ('early_completion','q->state=SDQ_RELEASE_CONFIRM;return SDQ_OK;',
             'q->valid=1u;q->completed_at=now;q->state=SDQ_COMPLETE;return SDQ_OK;',
             'test_late_successful_cleanup_is_not_accepted'),
            ('missing_clock_gap',
             'if ((uint32_t)(now-q->last_op_at)>=SDQ_OP_GAP_MS) {fail(q,SDQ_OP_CLOCK_GAP,now);return;}',
             '/* deliberately removed clock gap guard */',
             'test_clock_gap_and_backwards_time_stop_pending_query'),
            ('loose_cold_declaration','q->cold_start_declared=cold==1u;',
             'q->cold_start_declared=cold!=0u;',
             'test_cold_start_is_exact_and_missing_adapter_has_no_io'),
            ('repeated_cleanup','unsigned already_released=q->state==SDQ_RELEASE_CONFIRM;',
             'unsigned already_released=0u;',
             'test_late_successful_cleanup_is_not_accepted'),
        )
        for name,before,after,expected_failure in cases:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                self.assertEqual(original.count(before),1)
                for filename in ('metadata.c','metadata.h','query.h'):
                    (root/filename).write_bytes((HERE/filename).read_bytes())
                (root/'query.c').write_text(original.replace(before,after,1))
                run=subprocess.run([sys.executable,'-B','-c',QUERY_CHILD,str(HERE/'test_query.py'),str(root)],
                                   capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                result=json.loads(run.stdout)
                self.assertEqual(result['tests'],21);self.assertEqual(result['errors'],[])
                self.assertTrue(any(expected_failure in n for n in result['failures']))


if __name__=='__main__':unittest.main()
