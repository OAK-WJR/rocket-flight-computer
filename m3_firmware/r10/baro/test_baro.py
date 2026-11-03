"""Actual portable barometer C and native R10 endpoints; no physical sensor."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('r10_baro_verify',HERE/'verify.py')
source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
class Barometer(unittest.TestCase):
    def test_native_i2c_bounded_register_adapter(self):
        with tempfile.TemporaryDirectory() as t:
            exe=Path(t)/'baro-i2c'
            r=subprocess.run(['/usr/bin/clang','-O1','-g','-std=c11','-Wall','-Wextra','-Werror',
                '-fsanitize=undefined','-fno-sanitize-recover=undefined','-I'+str(HERE),
                str(HERE/'test_i2c.c'),str(HERE/'i2c_port.c'),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=5)
            self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stderr,'')
    def test_portable_acquisition_with_scripted_sensor(self):
        with tempfile.TemporaryDirectory() as t:
            exe=Path(t)/'baro-core'
            r=subprocess.run(['/usr/bin/clang','-O1','-g','-std=c11','-Wall','-Wextra','-Werror',
                '-fsanitize=undefined','-fno-sanitize-recover=undefined','-I'+str(HERE),'-I'+str(ROOT/'m3_firmware/src'),
                str(HERE/'test_core.c'),str(HERE/'baro_core.c'),str(ROOT/'m3_firmware/src/checks.c'),'-o',str(exe)],
                capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=5)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('scripted barometer core cases passed',r.stdout);self.assertEqual(r.stderr,'')
    def test_source_and_native_endpoints(self):self.assertTrue(source.verify())
    def test_wrong_source_part_and_address_strap_rejected(self):
        raw=(ROOT/source.NETLIST).read_bytes();tree=ET.fromstring(raw)
        tree.find("./components/comp[@ref='U5']/fields/field[@name='Manufacturer Part']").text='MS5607'
        with self.assertRaises(ValueError):source.sensor_contract(tree)
        tree=ET.fromstring(raw)
        for net in tree.findall('./nets/net'):
            for node in net.findall('node'):
                if node.get('ref')=='U5' and node.get('pin')=='4':node.set('pin','8')
        with self.assertRaises(ValueError):source.sensor_contract(tree)
if __name__=='__main__':unittest.main()
