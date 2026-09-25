"""Build a bench-only ELF/HEX/BIN and pin the exact PCB + source identities.
Does not download dependencies, run a programmer, or connect to a board.
"""
import hashlib
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / 'build'
TOOL = HERE/'toolchain/arm-gnu-toolchain-15.2.rel1-darwin-arm64-arm-none-eabi/bin/arm-none-eabi-'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition: raise ValueError(message)


def main():
    global OUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board',choices=['power','uart','usb','gnss','status','assembly'],default='power')
    parser.add_argument('--camera-query',action='store_true',help='UART/USB board: query camera once at boot, leave power ON')
    parser.add_argument('--imu-samples',action='store_true',help='UART/USB board: raw IMU bench observations')
    parser.add_argument('--storage',choices=['inspect','record'],help='Bench logger; inspect is read-only, record appends without erase')
    args=parser.parse_args()
    modern=args.board in ('uart','usb','gnss','status','assembly')
    usb=args.board in ('usb','gnss','status','assembly')
    gnss=args.board in ('gnss','status','assembly')
    status=args.board in ('status','assembly')
    require(not args.camera_query or modern,'Camera query requires reviewed UART/USB hardware')
    require(not args.imu_samples or modern,'IMU bench acquisition requires a reviewed binding')
    require(not args.storage or (modern and args.imu_samples),'Storage requires UART/USB hardware and --imu-samples')
    require(not usb or (args.storage and args.imu_samples),'USB/GNSS diagnostics include the existing storage and IMU record')
    suffix='_uart' if modern else ''
    protocol_path=HERE/('protocol'+suffix+'.json');pins_path=HERE/('pins'+suffix+'.json')
    if args.imu_samples:protocol_path=HERE/'protocol_imu.json'
    if args.storage:protocol_path=HERE/'protocol_storage.json'
    if args.board=='usb':protocol_path=HERE/'protocol_usb.json';pins_path=HERE/'pins_usb.json'
    if args.board=='gnss':protocol_path=HERE/'protocol_gnss.json';pins_path=HERE/'pins_gnss.json'
    if args.board=='status':protocol_path=HERE/'protocol_status.json';pins_path=HERE/'pins_status.json'
    if args.board=='assembly':protocol_path=HERE/'protocol_assembly.json';pins_path=HERE/'pins_status.json'
    protocol=json.loads(protocol_path.read_text())
    if gnss:
        for relative,digest in protocol['gnss']['source_hashes'].items():
            require(sha(ROOT/relative)==digest,'GNSS primary reference changed: '+relative)
    if status:
        for relative,digest in protocol['power_status']['source_hashes'].items():
            require(sha(ROOT/relative)==digest,'Power status reference changed: '+relative)
    if args.storage:
        for relative,digest in protocol['storage']['source_hashes'].items():
            require(sha(ROOT/relative)==digest,'Storage reference changed: '+relative)
    if args.imu_samples:
        for relative,digest in protocol['imu']['source_hashes'].items():
            require(sha(ROOT/relative)==digest,'IMU source reference changed: '+relative)
    if modern:
        if args.board=='assembly':from assembly_binding import make_binding
        elif args.board=='status':from status_binding import make_binding
        elif args.board=='gnss':from gnss_binding import make_binding
        elif args.board=='usb':from usb_binding import make_binding
        else:from uart_binding import make_binding
        binding=make_binding()
        folder=ROOT/('m3_design/'+args.board+'_review' if usb else 'm3_design/uart_review')
        if args.board=='status':folder=ROOT/'m3_design/power_status_review'
        OUT=HERE/('build_uart_query' if args.camera_query else 'build_uart_idle')
        if args.imu_samples:OUT=HERE/('build_imu_query' if args.camera_query else 'build_imu_idle')
        if args.storage:OUT=HERE/('build_storage_'+args.storage+('_query' if args.camera_query else ''))
        if usb:OUT=HERE/('build_'+args.board+'_'+args.storage+('_query' if args.camera_query else ''))
    else:
        folder=ROOT/'m3_design/power_review'
        binding=json.loads((folder/'diagnostics_binding.json').read_text())
    board=folder/'m3.kicad_pcb'
    require(binding['profile']==protocol['profile'],'Unsupported board profile')
    require(binding['board_sha256'] == sha(board), 'PCB changed; review binding before compiling')
    if modern:require(sha(board)==protocol['board_sha256'],'Revision changed; firmware pin map needs review')
    # Native schematic netlist must agree with every firmware GPIO's pin name.
    tree = ET.parse(folder/'schematic.net.xml')
    names = {n.attrib['pinfunction'].rsplit('_', 1)[0]: net.attrib['name']
             for net in tree.findall('.//nets/net') for n in net.findall('node')
             if n.attrib['ref'] == 'U1'}
    for pin, net in json.loads(pins_path.read_text()).items():
        require(names.get(pin) == net, str((pin, net, names.get(pin))))
    components = {c.attrib['ref']: c.findtext('value') for c in tree.findall('.//components/comp')}
    if args.imu_samples:require(components.get('U4')=='ICM-45686','Unexpected IMU part')
    for ref, expected in {'R60':'100k','R61':'10k','R62':'10k','R63':'10k'}.items():
        require(components.get(ref) == expected, 'ADC divider value changed: ' + ref)
    pin_nets = {(n.attrib['ref'],n.attrib['pin']): net.attrib['name']
                for net in tree.findall('.//nets/net') for n in net.findall('node')}
    if args.storage:
        require(components.get('U3')=='W25Q128JVSIQ','Unreviewed Flash part')
        for pin,net in {'1':'QSPI_NCS','2':'QSPI_IO1','3':'QSPI_IO2','4':'GND',
                        '5':'QSPI_IO0','6':'QSPI_CLK','7':'QSPI_IO3','8':'3V3'}.items():
            require(pin_nets.get(('U3',pin))==net,'Flash pad/net changed: '+pin)
        require(sha(HERE/'research/w25q128jv.pdf')==protocol['storage']['datasheet_sha256'],'Flash primary reference changed')
    if args.imu_samples:
        expected_imu={'1':'SPI1_MISO','2':'GND','3':'GND','4':'IMU_INT1','5':'3V3A',
                      '6':'GND','7':'GND','8':'3V3A','10':'GND','11':'GND','12':'IMU_CS',
                      '13':'SPI1_SCK','14':'SPI1_MOSI'}
        for pin,net in expected_imu.items():require(pin_nets.get(('U4',pin))==net,'IMU pin/pull configuration changed: '+pin)
        require(pin_nets.get(('U4','9'),'').startswith('unconnected-'),'Floating INT2 pull assumption changed')
    for ref, pair in {'R60':('VLOGIC','VLOGIC_SENSE'), 'R61':('VLOGIC_SENSE','GND'),
                      'R62':('3V3','V3V3_SENSE'), 'R63':('V3V3_SENSE','GND')}.items():
        require({pin_nets.get((ref,'1')),pin_nets.get((ref,'2'))} == set(pair),
                'ADC divider topology changed: ' + ref)
    vendor = json.loads((HERE/'vendor_manifest.json').read_text())
    for row in vendor['files']:
        require(sha(HERE/row['path']) == row['sha256'], 'Vendor file modified: ' + row['path'])
    if usb:
        tiny_manifest=HERE/'research/usb/tinyusb_manifest.json'
        tiny=json.loads(tiny_manifest.read_text())
        require(tiny['version']=='0.21.0','Unreviewed USB dependency version')
        for name,digest in tiny['files'].items():
            require(sha(HERE/'vendor/tinyusb'/name)==digest,'USB dependency changed: '+name)
    sources = sorted([*HERE.glob('src/*'), protocol_path, pins_path,
                      HERE/'linker.ld', HERE/'build.py', HERE/'vendor_manifest.json', HERE/'uart_binding.py'])
    if usb:sources += [tiny_manifest,HERE/'usb_binding.py']
    if gnss:sources += [HERE/'gnss_binding.py']
    if status:sources += [HERE/'status_binding.py']
    if args.board=='assembly':sources += [HERE/'assembly_binding.py']
    inputs = {str(p.relative_to(HERE)): sha(p) for p in sources}
    options={'board':args.board,'camera_query':args.camera_query}
    if args.imu_samples:options['imu_samples']=True
    if args.storage:options['storage']=args.storage
    build_sha = hashlib.sha256(json.dumps({'inputs':inputs,'options':options}, sort_keys=True).encode()).hexdigest()
    OUT.mkdir(exist_ok=True)
    if args.board=='assembly' and (OUT/'manifest.json').exists():
        raise FileExistsError('Preserve existing assembly firmware build')
    h = ['/* Generated from reviewed protocol + source hashes. */', '#include <stdint.h>']
    for key in ('magic', 'version', 'bytes', 'address', 'capabilities'):
        h.append(f'#define MB_{key.upper()} {protocol[key]}U')
    for group, prefix in (('words','W'), ('states','STATE'), ('statuses','STATUS')):
        for key, value in protocol[group].items(): h.append(f'#define {prefix}_{key} {value}U')
    for label, value in [('board', binding['board_sha256']), ('build', build_sha)]:
        h.append(f'static const uint8_t {label}_sha[32] = {{'+','.join('0x'+value[i:i+2] for i in range(0,64,2))+'};')
    (OUT/'generated.h').write_text('\n'.join(h)+'\n')
    flags = ['-mcpu=cortex-m7','-mthumb','-mfloat-abi=soft','-Os','-g3',
             '-ffunction-sections','-fdata-sections','-fno-common','-Wall','-Wextra','-Werror',
             '-Wdate-time','-DSTM32H743xx','-DUSE_HAL_DRIVER','-DUSE_PWR_LDO_SUPPLY',
             '-DHSE_VALUE=25000000U','-DUSER_VECT_TAB_ADDRESS',
             f'-ffile-prefix-map={HERE}=.',f'-fdebug-prefix-map={HERE}=.']
    if modern:flags += ['-DM3_CAMERA_UART','-DM3_CAMERA_QUERY='+str(int(args.camera_query))]
    if usb:flags += ['-DM3_USB','-I'+str(HERE/'vendor/tinyusb/src')]
    if gnss:flags += ['-DM3_GNSS']
    if status:flags += ['-DM3_POWER_STATUS']
    if args.imu_samples:flags += ['-DM3_IMU_SAMPLES']
    if args.storage:flags += ['-DM3_STORAGE','-DM3_STORAGE_RECORD='+str(int(args.storage=='record'))]
    flags += ['-I'+str(OUT)]
    for inc in ['src','vendor/cmsis','vendor/device/Include','vendor/hal/Inc']:
        flags += ['-I'+str(HERE/inc)]
    srcs = [*sorted((HERE/'src').glob('*.c')),
            HERE/'vendor/device/Source/Templates/system_stm32h7xx.c',
            HERE/'vendor/device/Source/Templates/gcc/startup_stm32h743xx.s',
            *sorted((HERE/'vendor/hal/Src').glob('*.c'))]
    if usb:
        srcs += [HERE/'vendor/tinyusb/src'/s for s in ['tusb.c','common/tusb_fifo.c','device/usbd.c',
            'class/cdc/cdc_device.c','portable/synopsys/dwc2/dwc2_common.c','portable/synopsys/dwc2/dcd_dwc2.c']]
    env = dict(os.environ, SOURCE_DATE_EPOCH='1788739200')
    commands = []
    def run(args):
        commands.append([str(x) for x in args])
        return subprocess.run(args, check=True, capture_output=True, text=True, env=env, cwd=HERE).stdout
    version = run([str(TOOL)+'gcc','--version']).splitlines()[0]
    objects = []
    for src in srcs:
        obj = OUT/(src.stem+'.o'); objects.append(obj)
        run([str(TOOL)+'gcc', *flags, '-c', str(src), '-o', str(obj)])
    elf = OUT/'m3_bench.elf'
    run([str(TOOL)+'gcc', *flags, '-nostartfiles', '--specs=nano.specs', '--specs=nosys.specs',
         '-T'+str(HERE/'linker.ld'), '-Wl,--gc-sections', '-Wl,-Map='+str(OUT/'m3_bench.map'),
         *map(str,objects), '-o',str(elf), '-lc', '-lgcc'])
    for fmt,ext in [('binary','bin'),('ihex','hex')]:
        run([str(TOOL)+'objcopy','-O',fmt,str(elf),str(OUT/('m3_bench.'+ext))])
    symbols = run([str(TOOL)+'nm','-S',str(elf)])
    require(f"24000000 {protocol['bytes']:08x} B bench_mailbox" in symbols, 'Mailbox linker address/size mismatch')
    # No accidentally linked self-programming or external flash erase/write APIs.
    forbidden=['HAL_FLASH_Program','HAL_FLASHEx_Erase','HAL_ADCEx_Calibration_Start']
    if args.storage!='record':forbidden.append('HAL_QSPI_Transmit')
    require(not any(n in symbols for n in forbidden),
            'Unexpected programming API linked')
    if args.storage=='record':require(' T HAL_QSPI_Transmit' in symbols,'Append program adapter not linked')
    if args.storage=='inspect':require(' T HAL_QSPI_MemoryMapped' in symbols,'Read-only dump not linked')
    (OUT/'symbols.txt').write_text(symbols)
    size = run([str(TOOL)+'size',str(elf)]); print(size.strip())
    record = dict(schema=1, profile=binding['profile'], board_sha256=binding['board_sha256'],
                  build_sha256=build_sha, compiler=version, inputs=inputs, build_options=options,
                  artifacts={p.name:sha(p) for p in OUT.glob('m3_bench.*')},
                  hardware_tested=False, flashed=False,
                  test_scope=('Input-only power status/history, GNSS reception, full bench records and USB readout; no hardware qualification' if status else
                              'GNSS read-only polls/reception, full diagnostic records and USB download; no physical/RF qualification' if args.board=='gnss' else
                              'USB CDC snapshot/download, raw bench journal and optional camera query; not USB or hardware qualified' if args.board=='usb' else
                              'bench diagnostic journal/read-only inspection plus IMU/voltage/pressure, optional camera query; not hardware qualified' if args.storage else
                              'bench raw IMU observations, voltage/pressure and optional camera query; not hardware qualified'
                              if args.imu_samples else 'bench voltage/pressure acquisition plus slow GPIO connectivity; not hardware qualified'),
                  protocol=protocol, commands=commands,
                  camera_mode='GET_DEVICE_INFO_ONCE_POWER_STAYS_ON' if args.camera_query else 'DISABLED',
                  firmware_version='0.8.1' if args.board=='assembly' else '0.8' if args.board=='status' else '0.7' if args.board=='gnss' else '0.6' if args.board=='usb' else '0.5' if args.storage else '0.4' if args.imu_samples else '0.3-rebuild' if args.board=='uart' else '0.2-rebuild',
                  usb_mode='CDC_READ_ONLY_REQUESTS' if usb else 'NOT_IMPLEMENTED',
                  gnss_mode='UBX_READ_ONLY_POLLS_9600' if gnss else 'NOT_IMPLEMENTED',
                  power_status_mode='INPUT_ONLY_LATCHED_HISTORY' if status else 'NOT_IMPLEMENTED',
                  storage_mode=args.storage or 'IDENTITY_ONLY',
                  imu_mode='RAW_OBSERVATION_AT_MOST_1HZ' if args.imu_samples else 'IDENTITY_ONLY',
                  full_m3_complete=False)
    (OUT/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    (OUT/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
    print('Built:',elf, '\nBuild identity:',build_sha, '\nHardware tested: false')


if __name__ == '__main__':
    try: main()
    except subprocess.CalledProcessError as e:
        print(e.stdout, e.stderr, file=sys.stderr); raise SystemExit(e.returncode)
