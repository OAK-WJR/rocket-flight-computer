"""Fetch the small, matched CubeH7 v1.13.0 subset needed by bench diagnostics.

Public sources only. Every downloaded file is checked against the pinned Git
tree blob hash and recorded with SHA256. No package install or board access.
"""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
CUBE = '5abb9764b32e11a6557b90bf39531528019b5761'
HAL = 'a1996eed9172b59887bafaaa0ea1816ea14d48b5'
DEVICE = '8f922cdc7cc6de2344e75ddd657889f4ff761790'


def get(url):
    with urlopen(Request(url, headers={'User-Agent': 'M3-bench-build'}), timeout=30) as r:
        return r.read()


def tree(repo, sha):
    data = json.loads(get(f'https://api.github.com/repos/{repo}/git/trees/{sha}?recursive=1'))
    if data.get('truncated'):
        raise ValueError('Truncated upstream tree')
    return {x['path']: x for x in data['tree']}


def main():
    cube = tree('STMicroelectronics/STM32CubeH7', CUBE)
    assert cube['Drivers/STM32H7xx_HAL_Driver']['sha'] == HAL
    assert cube['Drivers/CMSIS/Device/ST/STM32H7xx']['sha'] == DEVICE
    device = tree('STMicroelectronics/cmsis-device-h7', DEVICE)
    hal = tree('STMicroelectronics/stm32h7xx-hal-driver', HAL)
    jobs = []

    def add(repo, sha, index, path, local):
        jobs.append((f'https://raw.githubusercontent.com/{repo}/{sha}/{path}',
                     index[path]['sha'], 'vendor/' + local))

    for h in ('core_cm7.h', 'cmsis_compiler.h', 'cmsis_gcc.h', 'cmsis_version.h',
              'mpu_armv7.h', 'cachel1_armv7.h'):
        add('STMicroelectronics/STM32CubeH7', CUBE, cube,
            'Drivers/CMSIS/Include/' + h, 'cmsis/' + h)
    add('STMicroelectronics/STM32CubeH7', CUBE, cube, 'Drivers/CMSIS/LICENSE.txt', 'cmsis/LICENSE.txt')
    for p in ('Include/stm32h7xx.h', 'Include/stm32h743xx.h', 'Include/system_stm32h7xx.h',
              'Source/Templates/system_stm32h7xx.c',
              'Source/Templates/gcc/startup_stm32h743xx.s', 'LICENSE.md'):
        add('STMicroelectronics/cmsis-device-h7', DEVICE, device, p, 'device/' + p)
    for module in ('', '_cortex', '_gpio', '_gpio_ex', '_rcc', '_rcc_ex', '_flash',
                   '_flash_ex', '_pwr', '_pwr_ex', '_def', '_exti', '_adc', '_adc_ex', '_dma', '_dma_ex', '_mdma', '_uart', '_uart_ex', '_spi', '_spi_ex', '_qspi'):
        p = 'Inc/stm32h7xx_hal' + module + '.h'
        add('STMicroelectronics/stm32h7xx-hal-driver', HAL, hal, p, 'hal/' + p)
    for module in ('', '_cortex', '_gpio', '_rcc', '_rcc_ex', '_flash', '_flash_ex', '_pwr', '_pwr_ex', '_adc', '_adc_ex', '_uart', '_uart_ex', '_spi', '_spi_ex', '_qspi'):
        p = 'Src/stm32h7xx_hal' + module + '.c'
        add('STMicroelectronics/stm32h7xx-hal-driver', HAL, hal, p, 'hal/' + p)
    for p in ('Inc/Legacy/stm32_hal_legacy.h', 'Inc/stm32h7xx_ll_adc.h', 'Inc/stm32h7xx_ll_delayblock.h', 'LICENSE.md'):
        add('STMicroelectronics/stm32h7xx-hal-driver', HAL, hal, p, 'hal/' + p)
    for p in ('Projects/NUCLEO-H743ZI/Templates/Inc/stm32h7xx_hal_conf.h',
              'Projects/NUCLEO-H743ZI/Templates/STM32CubeIDE/STM32H743ZITx_FLASH_DTCMRAM.ld'):
        add('STMicroelectronics/STM32CubeH7', CUBE, cube, p, 'reference/' + Path(p).name)
    for name in ('main.c', 'stm32h7xx_hal_msp.c'):
        p = 'Projects/NUCLEO-H743ZI/Examples/ADC/ADC_RegularConversion_Polling/Src/' + name
        add('STMicroelectronics/STM32CubeH7', CUBE, cube, p, 'reference/adc_polling/' + name)

    def fetch(job):
        url, blob, local = job
        dest = HERE / local
        data = dest.read_bytes() if dest.exists() else get(url)
        if hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() != blob:
            raise ValueError('Upstream blob mismatch: ' + local)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dict(path=local, url=url, git_blob=blob, sha256=hashlib.sha256(data).hexdigest())

    with ThreadPoolExecutor(max_workers=6) as pool:
        files = list(pool.map(fetch, jobs))
    (HERE/'vendor_manifest.json').write_text(json.dumps(dict(cube=CUBE, hal=HAL, device=DEVICE, files=files), indent=2)+'\n')
    print('Pinned vendor files:', len(files), flush=True)


if __name__ == '__main__':
    main()
