"""Execute the real read-only core against scripted transport faults."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent

class FlashReadOnly(unittest.TestCase):
    cases_run=0
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.binary=Path(cls.temp.name)/'test_flash_ro'
        subprocess.run([shutil.which('cc'),'-std=c11','-O1','-g',
            '-Wall','-Wextra','-Werror','-pedantic','-fsanitize=address,undefined',
            str(ROOT/'test_flash_ro.c'),str(ROOT/'flash_ro.c'),'-o',str(cls.binary)],check=True)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def case(self,name,arg=0):
        type(self).cases_run+=1
        p=subprocess.run([str(self.binary),name,str(arg)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertIn('PASS '+name,p.stdout)

def install(name,args):
    def method(self):
        for arg in args:
            with self.subTest(arg=arg):self.case(name,arg)
    setattr(FlashReadOnly,'test_'+name.replace('-','_'),method)

for name,args in {
    'good':range(1,9),'wrap':[0],'bad-adapter':range(4),'init-error':[0],
    'init-clock':[0,999999,1000001,0xffffffff],'init-timeout':[0],
    'init-latency':[0],'power-guard':[0],'start-error':range(8),
    'read-error':range(8),'count':range(2),'timeout':[0],
    'partial-error':[i*16+n for i,length in enumerate([1,1,1,3,8,4,3,1]) for n in range(1,length+1)],
    'confirm-deadline':[0],'full-but-busy':[0],'batch-deadline':[0],'batch-at-limit':[0],
    'busy-status':[0],'suspend':[0],'qe-disabled':[0],
    'identity':range(24),'sfdp':range(32),'quad':range(32),
    'id-unstable':[0],'status-changed':[0],'last-good':[0],
    'cleanup':range(2),'backward':[0],'fresh':[0],'pending':[0],'descriptor':[0],
}.items():install(name,args)

if __name__=='__main__':unittest.main(verbosity=2)
