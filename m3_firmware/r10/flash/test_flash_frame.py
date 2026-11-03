"""Actual C core/port/serializer checked by an independent saved-record decoder."""
import ctypes
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r10_flash_decode',HERE.parent/'flash_decode.py')
decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
INDICES=list(range(98,128))+list(range(193,247))

class FlashRecord(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();lib=Path(cls.temp.name)/'flash_record.dylib'
        p=subprocess.run(['/usr/bin/clang','-dynamiclib','-O1','-g','-std=c11','-Wall','-Wextra','-Werror',
             '-I'+str(HERE),str(HERE/'flash_ro.c'),str(HERE/'qspi_port.c'),
             str(HERE/'flash_frame.c'),str(HERE.parent/'tests/flash_record.c'),'-o',str(lib)],
             capture_output=True,text=True)
        if p.returncode:raise RuntimeError(p.stdout+p.stderr)
        cls.lib=ctypes.CDLL(str(lib));cls.lib.r10_test_flash_record.argtypes=[ctypes.POINTER(ctypes.c_uint32),ctypes.c_uint]
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def record(self,scenario=1):
        storage=(ctypes.c_uint32*258)(*([0xa5a5a5a5]*258))
        ptr=ctypes.cast(ctypes.byref(storage,4),ctypes.POINTER(ctypes.c_uint32))
        self.lib.r10_test_flash_record(ptr,scenario)
        self.assertEqual(storage[0],0xa5a5a5a5);self.assertEqual(storage[257],0xa5a5a5a5)
        words=list(storage)[1:257]
        for i in set(range(256))-set(INDICES):self.assertEqual(words[i],0xa5a5a5a5)
        words[5]=words[107];words[9]=0x20030450
        return words
    def test_only_the_84_declared_words_are_touched(self):
        self.assertEqual(len(INDICES),84);self.record()
    def test_protocol_layout_preserves_sensor_and_voltage_word_ranges(self):
        p=json.loads((HERE.parent/'protocol.json').read_text())
        self.assertEqual((p['version'],p['bytes'],p['words']['crc32']),(5,1024,255))
        self.assertEqual(p['flash']['logical_word_locations'],INDICES)
        self.assertFalse(set(INDICES)&set(range(128,193)))
        self.assertFalse(set(INDICES)&set(range(0,98)))
        self.assertEqual(p['reserved_words'],[63]+list(range(247,255)))
    def test_off_has_no_claims(self):
        r=decoder.decode_flash(self.record(0));self.assertEqual(r['state'],'OFF');self.assertFalse(r['has_sample'])
    def test_actual_complete_batch_round_trip(self):
        r=decoder.decode_flash(self.record())
        self.assertEqual(r['state'],'WAIT');self.assertTrue(r['fresh']);self.assertEqual(r['samples'],1)
        self.assertEqual(r['sample_raw']['jedec_before'],'ef4018')
        self.assertEqual(r['sample_raw']['quad_id'],'ef17ef17')
        self.assertEqual(r['pending_byte_counts']['sfdp_header'],8)
        for key in ('array_integrity_assessed','device_identity_authenticated','hardware_qualified'):
            self.assertIs(r[key],False)
    def test_expiration_uses_batch_start_and_is_exclusive(self):
        words=self.record();origin=words[108]
        words[5]=(origin+2999)&0xffffffff;self.assertTrue(decoder.decode_flash(words)['fresh'])
        words[5]=(origin+3000)&0xffffffff
        r=decoder.decode_flash(words);self.assertFalse(r['fresh']);self.assertEqual(r['effective_state'],'STALE')
        self.assertEqual(r['sample_raw']['quad_id'],'ef17ef17')
    def test_partial_read_without_completion_is_not_a_sample(self):
        r=decoder.decode_flash(self.record(2));self.assertEqual(r['error'],'TIMEOUT')
        self.assertEqual(r['pending_byte_counts']['sr1_before'],1)
        self.assertFalse(r['has_sample']);self.assertIsNone(r['sample_raw'])
    def test_failure_retains_distinct_last_good(self):
        r=decoder.decode_flash(self.record(3));self.assertEqual(r['error'],'READ_ERROR')
        self.assertTrue(r['has_sample']);self.assertFalse(r['fresh']);self.assertEqual(r['samples'],1)
        self.assertEqual(r['sample_raw']['quad_id'],'ef17ef17')
        self.assertEqual(r['current_driver_failure']['reason'],'STATUS')
    def test_recovery_keeps_the_error_history(self):
        r=decoder.decode_flash(self.record(4));self.assertEqual(r['state'],'WAIT');self.assertTrue(r['fresh'])
        self.assertEqual(r['error'],'OK');self.assertEqual(r['last_error'],'READ_ERROR')
        self.assertEqual(r['samples'],2);self.assertEqual(r['failures'],1);self.assertEqual(r['retries'],1)
    def test_failed_cleanup_is_terminal_and_separately_visible(self):
        r=decoder.decode_flash(self.record(5));self.assertEqual(r['state'],'STOPPED')
        self.assertEqual(r['cleanup_error'],'CLEANUP');self.assertEqual(r['error'],'READ_ERROR')
        self.assertEqual(r['cleanup_driver_failure']['reason'],'CLEANUP')
        self.assertFalse(r['fresh']);self.assertTrue(r['has_sample'])
    def test_wire_protocol_failures_retain_their_actual_bytes(self):
        cases=[(6,'DEVICE_BUSY','sr1_before','01'),(7,'QUAD_DISABLED','sr2','00'),
               (8,'QUAD_IDENTITY','quad_id','ee17ef17'),(9,'UNSTABLE_ID','jedec_after','ee4018')]
        for scenario,error,command,raw in cases:
            with self.subTest(scenario=scenario):
                r=decoder.decode_flash(self.record(scenario));self.assertEqual(r['error'],error)
                self.assertEqual(r['pending_raw'][command],raw);self.assertFalse(r['fresh'])
    def test_unknown_revision_is_failure_evidence_not_a_dropped_record(self):
        r=decoder.decode_flash(self.record(10));self.assertEqual(r['error'],'INIT')
        self.assertEqual(r['current_driver_failure']['reason'],'DEVICE_REVISION')
        self.assertEqual(r['port']['revision_raw'],0x2008);self.assertFalse(r['fresh'])
    def test_invalid_last_good_id_or_counts_are_rejected(self):
        cases=[(59,0),(51,0x04010101),(69,1),(83,0),(12,0),(70,5),(72,0x2008),(83,5)]
        for logical,value in cases:
            with self.subTest(logical=logical):
                words=self.record();words[INDICES[logical]]=value
                with self.assertRaises(ValueError):decoder.decode_flash(words)
    def test_unaccounted_pending_bytes_and_nonprefix_masks_are_rejected(self):
        for logical,value in [(35,0x100),(17,0x40),(5,17)]:
            with self.subTest(logical=logical):
                words=self.record(2);words[INDICES[logical]]=value
                with self.assertRaises(ValueError):decoder.decode_flash(words)

if __name__=='__main__':unittest.main(verbosity=2)
