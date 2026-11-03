"""Compile the actual sensor state machine and official ST driver on the host."""
import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("r10_imu_verify",HERE/"verify.py")
source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)

class ImuCore(unittest.TestCase):
    def test_native_spi_polling_and_gpio_boundaries(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/"spi-test"
            r=subprocess.run(["/usr/bin/clang","-O1","-g","-Wall","-Wextra","-Werror","-std=c11",
                              "-fsanitize=undefined","-fno-sanitize-recover=undefined","-I"+str(HERE),
                              str(HERE/"test_spi.c"),str(HERE/"spi_port.c"),"-o",str(output)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            result=subprocess.run([str(output)],capture_output=True,text=True,timeout=5)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn("scripted native SPI cases passed",result.stdout)
            self.assertEqual(result.stderr,"")

    def test_actual_c_state_machine_and_vendor_with_scripted_spi(self):
        source.verify()
        vendor=HERE.parent/"vendor/ism6hg256x"
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/"imu-test"
            # AppleClang predefines __weak as an Objective-C ownership qualifier.
            # Select ST's function attribute without editing the pinned source.
            r=subprocess.run(["/usr/bin/clang","-U__weak","-D__weak=__attribute__((weak))","-O1","-g","-Wall","-Wextra","-Werror","-std=c11",
                              "-fsanitize=undefined","-fno-sanitize-recover=undefined","-I"+str(HERE),"-I"+str(vendor),
                              str(HERE/"test_core.c"),str(HERE/"imu_core.c"),str(vendor/"ism6hg256x_reg.c"),
                              "-o",str(output)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            result=subprocess.run([str(output)],capture_output=True,text=True,timeout=5)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn("scripted IMU cases passed",result.stdout)
            self.assertEqual(result.stderr,"")

    def test_pinned_sources_and_pin_map(self):
        self.assertTrue(source.verify())

    def test_tampered_vendor_file_fails_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);vendor=root/"m3_firmware/r10/vendor/ism6hg256x"
            shutil.copytree(HERE.parent/"vendor/ism6hg256x",vendor)
            pin=root/source.PIN_TABLE;pin.parent.mkdir(parents=True);pin.write_bytes((source.ROOT/source.PIN_TABLE).read_bytes())
            net=root/source.NETLIST;net.parent.mkdir(parents=True,exist_ok=True);net.write_bytes((source.ROOT/source.NETLIST).read_bytes())
            self.assertTrue(source.verify(root))
            (vendor/"ism6hg256x_reg.h").write_bytes(b"changed header")
            with self.assertRaisesRegex(ValueError,"driver changed"):source.verify(root)

    def test_native_pin_swap_and_wrong_fitted_part_are_rejected(self):
        raw=(source.ROOT/source.NETLIST).read_bytes()
        self.assertEqual(len(source.sensor_contract(ET.fromstring(raw))),8)
        tree=ET.fromstring(raw)
        tree.find("./components/comp[@ref='U4']/fields/field[@name='Manufacturer Part']").text="ICM-45686"
        with self.assertRaises(ValueError):source.sensor_contract(tree)
        tree=ET.fromstring(raw)
        for net in tree.findall('./nets/net'):
            for node in net.findall('node'):
                if node.get('ref')=='U1' and node.get('pin')=='89':node.set('pin','90')
        with self.assertRaises(ValueError):source.sensor_contract(tree)

if __name__=="__main__":unittest.main()
