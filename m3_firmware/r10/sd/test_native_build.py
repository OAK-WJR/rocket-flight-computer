"""Cross-build the real bridge and transport; never execute target IO."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


class NativeBuild(unittest.TestCase):
    def test_pinned_H743_register_contract_and_byte_MMIO_compile(self):
        compiler = os.environ.get('R10_ARM_GCC') or shutil.which('arm-none-eabi-gcc')
        if not compiler:
            self.skipTest('Arm compiler unavailable; native SPI3 bridge not cross-tested')
        self.assertIn('15.2.1', subprocess.check_output([compiler, '--version'], text=True),
                      'Review an Arm compiler change explicitly')
        root = Path(os.environ.get('R10_REPOSITORY', str(HERE.parents[2])))
        include = root / 'm3_firmware/vendor'
        flags = ['-std=c11', '-Os', '-mcpu=cortex-m7', '-mthumb', '-mfloat-abi=soft',
                 '-ffreestanding', '-fno-builtin', '-ffunction-sections', '-fdata-sections',
                 '-Wall', '-Wextra', '-Werror', '-DSTM32H743xx', '-DCORE_CM7',
                 '-I' + str(include / 'device/Include'), '-I' + str(include / 'cmsis')]
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            for name in ('metadata', 'query', 'wire', 'spi3_port', 'native_spi3'):
                run = subprocess.run([compiler, *flags, '-c', str(HERE / (name + '.c')),
                                      '-o', str(out / (name + '.o'))],
                                     capture_output=True, text=True, timeout=30)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            dump = subprocess.check_output([str(compiler).replace('gcc', 'objdump'), '-d',
                                            str(out / 'native_spi3.o')], text=True)
            for instruction in ('ldrb', 'strb', 'dsb', 'nop'):
                self.assertRegex(dump, r'\b' + instruction + r'(?:\.w)?\b')
            # Building these objects does not link them into the bench image.
            self.assertIsNone(re.search(r'<_GLOBAL__sub_I_', dump))


if __name__ == '__main__':
    unittest.main()
