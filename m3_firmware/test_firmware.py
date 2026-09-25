"""Compile and execute actual portable firmware checks on the host.
These are software tests, not a board or a SPICE model.
"""
import ctypes
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib
import random

HERE=Path(__file__).resolve().parent


class FirmwareChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        lib=Path(cls.tmp.name)/'checks.dylib'
        subprocess.run(['/usr/bin/clang','-dynamiclib','-O2','-Wall','-Wextra','-Werror',
                        str(HERE/'src/checks.c'),'-o',str(lib)],check=True,capture_output=True)
        cls.c=ctypes.CDLL(str(lib));cls.c.bench_crc32.restype=ctypes.c_uint32
        cls.c.bench_crc32.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
        cls.c.bench_prom_crc4.restype=ctypes.c_uint8
        cls.c.bench_prom_crc4.argtypes=[ctypes.POINTER(ctypes.c_uint16)]
        cls.c.bench_prom_nonempty.argtypes=[ctypes.POINTER(ctypes.c_uint16)]
        cls.c.bench_voltages.argtypes=[ctypes.c_uint32]*4+[ctypes.POINTER(ctypes.c_uint32)]*3
        cls.c.bench_ms5611.argtypes=[ctypes.POINTER(ctypes.c_uint16),ctypes.c_uint32,ctypes.c_uint32,
                                    ctypes.POINTER(ctypes.c_int32),ctypes.POINTER(ctypes.c_int32)]
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_crc32_standard_check_vector(self):
        v=b'123456789';self.assertEqual(self.c.bench_crc32(v,len(v)),0xcbf43926)
    def test_crc32_mailbox_length_matches_independent_zlib(self):
        for data in (bytes(508),bytes(range(254))*2,bytes([255])*508):
            self.assertEqual(self.c.bench_crc32(data,len(data)),zlib.crc32(data))
    def test_te_published_crc4_vector_and_raw_not_modified(self):
        vals=[0x3132,0x3334,0x3536,0x3738,0x3940,0x4142,0x4344,0x4500]
        a=(ctypes.c_uint16*8)(*vals)
        self.assertEqual(self.c.bench_prom_crc4(a),11);self.assertEqual(list(a),vals)
    def test_crc_low_byte_is_excluded_per_an520(self):
        for low in range(256):
            a=(ctypes.c_uint16*8)(0x3132,0x3334,0x3536,0x3738,0x3940,0x4142,0x4344,0x4500|low)
            self.assertEqual(self.c.bench_prom_crc4(a),11)
    def test_blank_bus_rejected_even_if_crc_matches(self):
        for value in (0,0xffff):
            self.assertEqual(self.c.bench_prom_nonempty((ctypes.c_uint16*8)(*[value]*8)),0)
    def test_compiled_vector_and_mailbox_symbol(self):
        raw=(HERE/'build/m3_bench.bin').read_bytes()
        sp,entry=struct.unpack('<II',raw[:8]);self.assertEqual(sp,0x20020000)
        self.assertTrue(entry & 1);self.assertTrue(0x08000000 <= (entry&~1) < 0x08000000+len(raw))
        self.assertIn('24000000 00000200 B bench_mailbox',(HERE/'build/symbols.txt').read_text())
        m=json.loads((HERE/'build/manifest.json').read_text());self.assertFalse(m['hardware_tested']);self.assertFalse(m['flashed'])
    def test_actual_bus_routines_against_scripted_line_responses(self):
        exe=Path(self.tmp.name)/'bus_harness'
        subprocess.run(['/usr/bin/clang','-O1','-g','-Wall','-Wextra','-Werror',
                        '-I'+str(HERE/'tests'),'-I'+str(HERE/'src'),'-I'+str(HERE/'build'),
                        str(HERE/'tests/bus_harness.c'),str(HERE/'src/checks.c'),'-o',str(exe)],
                       check=True,capture_output=True,text=True)
        r=subprocess.run([str(exe)],check=True,capture_output=True,text=True,timeout=5)
        self.assertIn('14 scripted bus cases passed',r.stdout)
    def test_actual_adc_driver_and_bounded_failures(self):
        exe=Path(self.tmp.name)/'adc_harness'
        subprocess.run(['/usr/bin/clang','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=undefined',
                        '-I'+str(HERE/'tests/adc'),'-I'+str(HERE/'src'),'-I'+str(HERE/'build'),
                        str(HERE/'tests/adc_harness.c'),str(HERE/'src/checks.c'),'-o',str(exe)],
                       check=True,capture_output=True,text=True)
        r=subprocess.run([str(exe)],check=True,capture_output=True,text=True,timeout=5)
        self.assertIn('13 scripted ADC cases passed',r.stdout);self.assertEqual(r.stderr,'')
    def test_h743_reference_scaling_never_multiplies_by_16(self):
        a,b,c=(ctypes.c_uint32() for _ in range(3))
        self.assertEqual(self.c.bench_voltages(24458,24458,10000,32768,ctypes.byref(a),ctypes.byref(b),ctypes.byref(c)),1)
        self.assertEqual((a.value,b.value,c.value),(3300,5539,3300))
        for cal,ref in ((1529,24458),(24458,0),(65535,24458),(24458,1529),(24458,65535)):
            self.assertEqual(self.c.bench_voltages(cal,ref,10000,32768,ctypes.byref(a),ctypes.byref(b),ctypes.byref(c)),0)
            self.assertEqual((a.value,b.value,c.value),(0,0,0))
    def test_te_pressure_example_and_independent_cold_compensation(self):
        from diagnostics.mailbox import prom_crc4
        from diagnostics.acquisition import pressure_reference
        coeff=[0,40127,36924,23317,23282,33464,28312,0];coeff[7]=prom_crc4(coeff)
        c=(ctypes.c_uint16*8)(*coeff);p,t=ctypes.c_int32(),ctypes.c_int32()
        self.assertEqual(self.c.bench_ms5611(c,9085466,8569150,ctypes.byref(p),ctypes.byref(t)),1)
        self.assertEqual((p.value,t.value),(100009,2007))
        rng=random.Random(5611)
        for raw_temp in [7000000,7500000,8000000,8566784,8569150,9500000]+[rng.randrange(7000000,9600000) for _ in range(500)]:
            expected_p,expected_t=pressure_reference(coeff,9085466,raw_temp)
            self.c.bench_ms5611(c,9085466,raw_temp,ctypes.byref(p),ctypes.byref(t))
            self.assertLessEqual(abs(p.value-expected_p),3);self.assertLessEqual(abs(t.value-expected_t),2)
        for bad in (0,0xffffff,0x1000000):
            self.assertEqual(self.c.bench_ms5611(c,bad,8569150,ctypes.byref(p),ctypes.byref(t)),0)
            self.assertEqual((p.value,t.value),(0,0))


if __name__=='__main__':unittest.main()
