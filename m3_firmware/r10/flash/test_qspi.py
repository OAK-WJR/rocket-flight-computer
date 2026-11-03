"""Scripted MMIO tests for a native transport candidate, not board acceptance."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent
class QspiPort(unittest.TestCase):
    cases_run=0
    @classmethod
    def setUpClass(cls):
        cls.repository=Path(os.environ.get('R10_REPOSITORY',str(ROOT.parents[2])))
        cls.temp=tempfile.TemporaryDirectory()
        cls.output=Path(cls.temp.name)
        cls.binary=cls.output/'test_qspi'
        subprocess.run([shutil.which('cc'),'-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
            '-pedantic','-fsanitize=address,undefined',str(ROOT/'test_qspi.c'),
            str(ROOT/'qspi_port.c'),str(ROOT/'flash_ro.c'),'-o',str(cls.binary)],check=True)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def case(self,name,arg=0):
        type(self).cases_run+=1
        p=subprocess.run([str(self.binary),name,str(arg)],capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
    def test_native_arm_constants_and_timing_stores(self):
        compiler=os.environ.get('R10_ARM_GCC') or shutil.which('arm-none-eabi-gcc')
        if not compiler:self.skipTest('Arm compiler unavailable; native bridge object not tested')
        toolchain=Path(compiler)
        self.assertIn('15.2.1',subprocess.check_output([str(toolchain),'--version'],text=True),
                      'Review an Arm compiler change explicitly')
        include=self.repository/'m3_firmware/vendor'
        output=self.output/'native_qspi.arm.o'
        cmd=[str(toolchain),'-std=c11','-Os','-mcpu=cortex-m7','-mthumb','-ffreestanding',
             '-DSTM32H743xx','-DCORE_CM7','-Wall','-Wextra','-Werror',
             '-I'+str(include/'device/Include'),'-I'+str(include/'cmsis'),
             '-c',str(ROOT/'native_qspi.c'),'-o',str(output)]
        p=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        dump=subprocess.check_output([str(toolchain).replace('gcc','objdump'),'-d',str(output)],text=True)
        prime=re.search(r'<prime>:\n(.*?)(?=\n\n|\Z)',dump,re.S)
        self.assertIsNotNone(prime,dump)
        body=prime.group(1)
        self.assertIn('cpsid',body);self.assertIn('PRIMASK',body.upper())
        lines=[s.strip() for s in body.splitlines()]
        found=False
        for i in range(len(lines)-2):
            sequence=lines[i:i+3]
            if (all(re.search(r'\bstr(?:\.w)?\b',s) for s in sequence) and
                '#20]' in sequence[0] and '#20]' in sequence[1] and
                re.search(r'\[r\d+(?:, #0)?\]',sequence[2])):
                found=True
        self.assertTrue(found,body)
        for source in ['flash_ro.c','qspi_port.c']:
            p=subprocess.run([str(toolchain),'-std=c11','-Os','-mcpu=cortex-m7','-mthumb','-ffreestanding',
                              '-Wall','-Wextra','-Werror','-c',str(ROOT/source),'-o',str(self.output/(source+'.arm.o'))],
                              capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)

def install(name,args):
    def method(self):
        for arg in args:
            with self.subTest(arg=arg):self.case(name,arg)
    setattr(QspiPort,'test_'+name.replace('-','_'),method)

for name,args in {
    'good':[0],'revision':[0x1003,0x2001,0x2003,0x2007],
    'unknown':[0,0x1002,0x2002,0x2008,0xffff],
    'clock':range(4),'owned':[0],'pin-owned':[0],'same-tick':[0],
    'init-drift':range(2),'read-drift':range(2),'zero-capacity':[0],
    'prime-fail':range(2),
    'ignored':[0x580244e0,0x580244d4,0x5802447c,0x58020418,
               0x58020400,0x58020420,0x52005004,0x52005000],
    'stale':[1,2,4,8,16,32,0x100,0x2000],
    'drift':[0x58024400,0x58024410,0x58024418,0x5802444c,
             0x580244d4,0x580244e0,0x58020420,0x58020400,
             0x58020408,0x5802040c,0x52005000,0x52005004],
    'transfer-fault':range(8),'partial':[0],'cleanup-fail':[0],
    'ignored-reset':[0],'invalid-command':[8,0xffffffff],'restart':[0],'recover':[0],
}.items():install(name,args)

if __name__=='__main__':unittest.main(verbosity=2)
