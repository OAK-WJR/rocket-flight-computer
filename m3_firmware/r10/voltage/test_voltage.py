"""Execute acquisition and ADC MMIO models. No probe or board access."""
import ctypes
from fractions import Fraction
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r10_voltage_binding',HERE/'verify.py')
binding=importlib.util.module_from_spec(spec);spec.loader.exec_module(binding)

class Config(ctypes.Structure):
    _fields_=[(k,ctypes.c_uint32) for k in ('revision','calibration','sample_bits','adc12_hz','adc3_hz')]
class Values(ctypes.Structure):
    _fields_=[(k,ctypes.c_uint32) for k in
             ('vdda_mv','logic_mv','camera_mv','v3v3_coarse_mv','reference_drift_permille')]

class Voltage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        library=Path(cls.temp.name)/'voltage.dylib'
        subprocess.run(['/usr/bin/clang','-dynamiclib','-O2','-std=c11','-Wall','-Wextra','-Werror',
                        str(HERE/'voltage_core.c'),'-o',str(library)],check=True,capture_output=True)
        cls.lib=ctypes.CDLL(str(library))
        cls.lib.r10_voltage_compute.argtypes=[ctypes.POINTER(Config),ctypes.POINTER(ctypes.c_uint32),ctypes.POINTER(Values)]
        cls.lib.r10_voltage_compute.restype=ctypes.c_uint
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def compute(self,raw=(375,140,155,256,375),config=None):
        if config is None:config=Config(0x2003,24000,10,2000000,2000000)
        out=Values(*([0xdeadbeef]*5))
        rc=self.lib.r10_voltage_compute(ctypes.byref(config),(ctypes.c_uint32*5)(*raw),ctypes.byref(out))
        return rc,out
    def test_scripted_acquisition_deadlines_recovery_and_wrap(self):
        exe=Path(self.temp.name)/'core'
        subprocess.run(['/usr/bin/clang','-O1','-g','-std=c11','-Wall','-Wextra','-Werror',
                        '-fsanitize=address,undefined','-fno-sanitize-recover=all',
                        str(HERE/'test_core.c'),str(HERE/'voltage_core.c'),'-o',str(exe)],check=True,capture_output=True)
        run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=10)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(run.stderr,'')
        self.assertIn('scripted voltage acquisition, timing and recovery cases passed',run.stdout)
    def test_native_adc_state_machine_and_faults_against_fake_mmio(self):
        exe=Path(self.temp.name)/'adc'
        run=subprocess.run(['/usr/bin/clang','-O1','-g','-std=c11','-Wall','-Wextra','-Werror',
            '-fsanitize=address,undefined','-fno-sanitize-recover=all',
            str(HERE/'test_adc.c'),str(HERE/'adc_port.c'),str(HERE/'voltage_core.c'),'-o',str(exe)],
            capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=10)
        self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(run.stderr,'')
        self.assertIn('ADC MMIO sequencing and fault cases passed',run.stdout)
    def test_native_register_constants_cross_compile_against_pinned_cmsis(self):
        gcc=os.environ.get('R10_ARM_GCC') or shutil.which('arm-none-eabi-gcc')
        if not gcc:self.skipTest('Arm compiler unavailable; native bridge compilation not tested')
        version=subprocess.check_output([gcc,'--version'],text=True)
        self.assertIn('15.2.1',version,'Review a compiler change explicitly')
        root=HERE.parents[2]
        for name in ('voltage_core','adc_port','native_adc'):
            run=subprocess.run([gcc,'-mcpu=cortex-m7','-mthumb','-mfloat-abi=soft','-Os','-std=c11',
                '-ffreestanding','-fno-builtin','-Wall','-Wextra','-Werror','-DSTM32H743xx',
                '-I'+str(root/'m3_firmware/vendor/cmsis'),'-I'+str(root/'m3_firmware/vendor/device/Include'),
                '-c',str(HERE/(name+'.c')),'-o',str(Path(self.temp.name)/(name+'.o'))],
                capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
    def test_nominal_conversions_match_independent_fraction_oracle(self):
        rng=random.Random(0xadc10)
        def rounded(x):return (2*x.numerator+x.denominator)//(2*x.denominator)
        accepted=0
        for _ in range(2000):
            cal=rng.randint(23000,26000)
            ref=rng.randint(365,500)
            raw=[ref,rng.randint(0,1022),rng.randint(0,1022),rng.randint(0,1022),ref+rng.randint(-3,3)]
            ideal_vdda=Fraction(3300*cal,65535)/Fraction(raw[0]+raw[4],2*1023)
            rc,values=self.compute(raw,Config(0x2003,cal,10,2000000,2000000))
            if not 1800<=rounded(ideal_vdda)<=3600:
                self.assertNotEqual(rc,0);self.assertEqual(bytes(values),bytes(Values()));continue
            accepted+=1;self.assertEqual(rc,0)
            self.assertEqual(values.vdda_mv,rounded(ideal_vdda))
            for field,slot,ratio in [('logic_mv',1,11),('camera_mv',2,11),('v3v3_coarse_mv',3,4)]:
                self.assertEqual(getattr(values,field),rounded(Fraction(raw[slot],1023)*ideal_vdda*ratio))
        self.assertGreater(accepted,1500)
    def test_both_native_external_dividers_are_eleven_not_legacy_two(self):
        rc,v=self.compute((375,100,100,100,375))
        self.assertEqual(rc,0);self.assertEqual(v.logic_mv,v.camera_mv)
        self.assertLess(abs(v.logic_mv*4-v.v3v3_coarse_mv*11),10)
    def test_bad_factory_word_unknown_revision_and_clock_metadata(self):
        for cal in (0,4095,19999,30001,65535,0xffffffff):
            rc,v=self.compute(config=Config(0x2003,cal,10,2000000,2000000))
            self.assertNotEqual(rc,0);self.assertEqual(bytes(v),bytes(Values()))
        for rev in (0,0x2002,0x2008,0x10030000,0xffffffff):
            self.assertNotEqual(self.compute(config=Config(rev,24000,10,2000000,2000000))[0],0)
        for bits in (0,8,12,14,16,32):
            self.assertNotEqual(self.compute(config=Config(0x2003,24000,bits,2000000,2000000))[0],0)
        for a,b in ((0,2000000),(2000000,0),(4000001,2000000),(2000000,4000001)):
            self.assertNotEqual(self.compute(config=Config(0x2003,24000,10,a,b))[0],0)
    def test_reference_zero_clipping_and_out_of_range_do_not_return_values(self):
        for slot in range(5):
            for value in (1023,1024,65535,0xffffffff):
                raw=[375,140,155,256,375];raw[slot]=value
                rc,v=self.compute(raw);self.assertNotEqual(rc,0);self.assertEqual(bytes(v),bytes(Values()))
        for a,b in ((0,375),(375,0),(1,1),(800,800),(375,400)):
            rc,v=self.compute((a,140,155,256,b))
            self.assertNotEqual(rc,0);self.assertEqual(bytes(v),bytes(Values()))
    def test_zero_external_supply_is_a_retained_observation(self):
        rc,v=self.compute((375,0,0,256,375))
        self.assertEqual(rc,0);self.assertEqual((v.logic_mv,v.camera_mv),(0,0))
    def test_reference_drift_policy_boundary(self):
        self.assertEqual(self.compute((400,140,155,256,408))[0],0)
        self.assertNotEqual(self.compute((400,140,155,256,409))[0],0)
        self.assertEqual(self.compute((408,140,155,256,400))[0],0)
    def test_known_revision_ids_are_explicitly_supported_by_math_only(self):
        for rev in (0x1003,0x2001,0x2003,0x2007):
            self.assertEqual(self.compute(config=Config(rev,24000,10,2000000,2000000))[0],0)
    def test_native_source_parts_reference_and_sense_wiring(self):
        self.assertTrue(binding.verify())
    def test_changed_manufacturer_register_or_clock_reference_is_rejected(self):
        original=json.loads((HERE/'provenance.json').read_text())
        for name in original['pinned_sources']:
            changed=json.loads(json.dumps(original))
            changed['pinned_sources'][name]='00'*32
            with self.assertRaises(ValueError):binding.verify_native_sources(provenance=changed)
    def test_changed_divider_or_legacy_pin_is_rejected(self):
        raw=(binding.ROOT/binding.NETLIST).read_bytes()
        for ref in ('R60','R61','R104','R105','U1'):
            tree=ET.fromstring(raw)
            tree.find("./components/comp[@ref='%s']/value"%ref).text='wrong'
            with self.assertRaises(ValueError):binding.voltage_contract(tree)
        for pin in ('30','35','6','19','20','21'):
            tree=ET.fromstring(raw)
            for n in tree.findall('./nets/net/node'):
                if n.get('ref')=='U1' and n.get('pin')==pin:n.set('pin','17')
            with self.assertRaises(ValueError):binding.voltage_contract(tree)
        for name in ('VLOGIC_SENSE','CAM_5V_SENSE','3V3A','3V3'):
            tree=ET.fromstring(raw)
            tree.find("./nets/net[@name='%s']"%name).set('name','wrong')
            with self.assertRaises(ValueError):binding.voltage_contract(tree)

if __name__=='__main__':unittest.main()
