"""Localize already-validated saved R10 evidence; never access a probe.

The conclusions describe record-publication time, not the present state of a
board. Circuit identity is source-bound; suggested causes remain hypotheses.
This analysis-only module is deliberately outside capture SOURCES so adding it
does not change historical acquisition permissions or saved request shapes.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

from .r10_offline import Profile, BOARD_SHA, regular_bytes, require
from .r10_swd import sha_bytes
from m3_firmware.r10.imu import verify as imu_binding
from m3_firmware.r10.baro import verify as baro_binding
from m3_firmware.r10.voltage import verify as voltage_binding
from m3_firmware.r10.flash import verify_flash as flash_binding

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_SOURCES = (
    'diagnostics/r10_findings.py', 'diagnostics/r10_offline.py',
    'diagnostics/r10_profile.json',
    'm3_firmware/r10/imu/verify.py', 'm3_firmware/r10/baro/verify.py',
    'm3_firmware/r10/voltage/verify.py', 'm3_firmware/r10/flash/verify_flash.py',
    flash_binding.NETLIST, flash_binding.PIN_TABLE,
)
SIGNALS = {
    'flash': ('QSPI_NCS', 'QSPI_CLK', 'QSPI_IO0', 'QSPI_IO1', 'QSPI_IO2', 'QSPI_IO3'),
    'imu': ('IMU_CS', 'SPI1_SCK', 'SPI1_MISO', 'SPI1_MOSI'),
    'baro': ('I2C1_SCL', 'I2C1_SDA', 'BARO_SDO'),
    'voltage': ('VLOGIC_SENSE', 'CAM_5V_SENSE'),
}
REFS = {'flash': 'U3', 'imu': 'U4', 'baro': 'U5', 'voltage': 'U1'}
POWER_POINTS = {'flash': ('C9.1',), 'imu': ('C10.1', 'C11.1'),
                'baro': ('C10.1', 'C11.1'),
                'voltage': ('TP83.1', 'J9.1', 'C9.1', 'C10.1')}
LABELS = {'flash': '存储器 U3', 'imu': 'IMU U4', 'baro': '气压计 U5', 'voltage': 'ADC 电压采样'}
CONTROLLER_REASONS = {
    'ADAPTER', 'CLOCK', 'DEVICE_REVISION', 'OWNERSHIP', 'GPIO', 'CLOCK_ENABLE',
    'PERIPHERAL_RESET', 'TIMING_WORKAROUND', 'CONFIGURATION', 'ARGUMENT',
    'FACTORY_CALIBRATION', 'ADC_OWNERSHIP', 'REGULATOR', 'CALIBRATION', 'READY',
}


def catalog(board):
    """Bind every offered circuit endpoint to the reviewed native project."""
    profile = Profile(board=board)
    for module in (imu_binding, baro_binding, voltage_binding, flash_binding):
        module.verify(ROOT)
    tree = ET.fromstring(regular_bytes(ROOT / flash_binding.NETLIST))
    nets = {n.get('name'): n for n in tree.findall('./nets/net')}
    result = {}
    for name, ref in REFS.items():
        part = tree.find("./components/comp[@ref='%s']" % ref)
        require(part is not None, 'Missing diagnostic circuit part: ' + ref)
        signals = {}
        for net in SIGNALS[name]:
            require(net in nets, 'Missing diagnostic circuit net: ' + net)
            signals[net] = [dict(endpoint=n.get('ref') + '.' + n.get('pin'),
                                 pin_function=n.get('pinfunction'))
                            for n in nets[net].findall('node')]
        power = [dict(point=profile.point(key), ground=profile.ground(profile.point(key)))
                 for key in POWER_POINTS[name]]
        result[name] = dict(reference=ref, fitted_value=part.findtext('value'),
                            signals=signals, power_points=power,
                            physical_continuity_verified=False)
    return result


def _cause(name, data):
    """Inspection hypotheses only; no component-failure or repair verdict."""
    error = data['error']
    # Core TIMEBASE failures retain the previous driver detail. The core error
    # takes precedence over that history; otherwise an old CLOCK/REVISION fault
    # can be misreported as the cause of a new backwards-time event.
    if error == 'TIMEBASE':
        return ('TIMEBASE', '采集时间基准不连续，不能把此次失败归给器件。',
                ['时间基准倒退、跳变或调度异常'], ['核对固件时间基准和两次记录的时间、序号及主循环进度。'])
    native = data.get('current_driver_failure')
    if native and native['reason'] in CONTROLLER_REASONS:
        return ('CONTROLLER', '驱动报告 MCU 时钟、资源或配置前置条件失败。',
                ['MCU 时钟或寄存器配置', '接口被其他代码占用', '未支持的芯片版本或配置漂移'],
                ['先核对记录中的驱动原因、阶段及寄存器原值，再核对相应固件配置；这些证据不能定位为外部芯片损坏。'])
    if name == 'flash':
        if error in ('DEVICE_BUSY', 'SUSPENDED'):
            return ('DEVICE_STATE', '只读状态应答显示忙或暂停状态；没有自动改写该状态。',
                    ['先前事务或其他固件留下的器件状态', '应答、连线或配置不符合拟定器件状态'],
                    ['保留 SR1/SR2 原始应答并核对先前操作记录；本报告不提出自动复位、唤醒、写状态或擦除。'])
        if error == 'QUAD_DISABLED':
            return ('PROFILE', '读回的 QE 位不符合本板拟装器件的只读配置预期。',
                    ['装配器件或配置与受审配置不一致', '状态读取有误'],
                    ['核对 U3 实物完整型号、装配 BOM、SR2 原始应答和串行接口；不要据此自动写 QE。'])
        if error == 'QUAD_IDENTITY':
            return ('QUAD_INTERFACE', '四线身份应答不匹配；此前已完成的串行应答仍应分开检查。',
                    ['四线接口、模式或时序不符合预期', 'IO0–IO3 中存在接触、短路或装配问题', '器件型号或应答不符合受审配置'],
                    ['结合已完成掩码逐项核对串行 ID、SFDP、SR2 和四线原始值；检查列出的四条 IO 网络，不能凭此指定某一根线损坏。'])
        return ('INTERFACE', '只读事务或身份应答不符合预期。',
                ['U3 供电或回流问题', 'NCS、CLK 或数据网络连接问题', '器件睡眠、忙状态、型号或时序配置不同'],
                ['先核对 U3 的 3V3/GND、NCS 上拉 R10 及所列接口端点，再对照命令完成掩码和实际字节数；全 00/FF 也不能单独证明芯片损坏。'])
    if name == 'imu':
        if error.startswith('CONFIG'):
            return ('CONFIGURATION', '传感器配置写入或读回未满足受审配置。',
                    ['配置流程或器件型号不同', 'SPI 事务或供电不稳定'],
                    ['核对 WHO_AM_I、配置掩码、配置原值和错误详情，再检查列出的 SPI/IMU_CS 端点。'])
        return ('INTERFACE', 'IMU 事务、身份或新数据等待失败。',
                ['U4 供电或 SPI/片选连接问题', '复位、配置或轮询流程异常', '未在等待窗口获得新样本'],
                ['核对 U4 供电、SPI/IMU_CS、身份和状态原值；本采集路径是轮询路径，不能据此把原因指定为 INT1 引脚。'])
    if name == 'baro':
        if error in ('PROM_EMPTY', 'PROM_CRC', 'PROM_READ'):
            return ('CALIBRATION_DATA', '校准读取或其一致性校验失败。',
                    ['I2C 读取或供电不稳定', '配置、装配器件或校准内容不符合预期'],
                    ['核对 PROM 已读取掩码、原始字和 CRC；检查 I2C1_SCL/SDA、R12/R13 上拉和 BARO_SDO/R64。'])
        return ('INTERFACE', '气压计转换、原始值或成对数据不符合采集约束。',
                ['供电、I2C 接口或转换调度问题', '数据过期、原始值或温度补偿输入不符合范围'],
                ['分开核对待完成 D1/D2、上次有效 D1/D2 和校准字；结果范围失败不能单独证明气压计损坏。'])
    if error in ('REFERENCE', 'REFERENCE_DRIFT', 'SATURATED', 'RAW_RANGE'):
        return ('ANALOG_EVIDENCE', '参考或 ADC 原始值不满足当前采集约束。',
                ['参考、电源或分压网络异常', 'ADC 配置、校准或原始数据通路异常'],
                ['先核对两次内部参考、具体通道原值及有效掩码，再用独立仪表复核所列电源和分压；标称换算值不是电压合格判据。'])
    return ('CONTROLLER', 'ADC 采集或校准流程失败。',
            ['ADC 时钟、校准、配置或转换流程异常', '参考或模拟输入状态不同'],
            ['核对 ADC 驱动原因、单元、阶段及原始寄存器；不能从驱动错误直接认定外部电源芯片损坏。'])


def from_report(report, board):
    """Use only the validated analyze() result; no acquisition or target action."""
    require(report.get('schema') == 'r10-firmware-report/v1' and
            report.get('board_sha256_claim') == BOARD_SHA, 'Wrong localization input')
    require(report.get('origin') in ('SYNTHETIC_FIXTURE', 'SWD_CAPTURE'), 'Unknown evidence origin')
    circuits = catalog(board)
    findings = []

    def add(code, category, record, subsystem, observed, hypotheses=(), checks=(), evidence=None):
        findings.append(dict(code=code, category=category, record_index=record,
                             subsystem=subsystem, observed_zh=observed,
                             possible_causes_zh=list(hypotheses), next_checks_zh=list(checks),
                             evidence=evidence, circuit=circuits.get(subsystem),
                             confirmed_component_failure=False))

    eligible = (report.get('complete_capture') is True and report.get('temporal_coherence') is True
                and report.get('image_bytes_match') is True)
    if not eligible:
        add('CAPTURE_INCOMPLETE', 'incomplete_capture', None, 'capture',
            '捕获、时间顺序或镜像证据不完整；只保留原始记录，不据此定位当前器件故障。',
            checks=['核对捕获、清理、监督错误及进程是否结束；完成这些前置检查后再判断器件。'],
            evidence={k: report.get(k) for k in ('state', 'capture_error', 'cleanup_error', 'worker_status')})
    else:
        for index, record in enumerate(report['records']):
            if record is None:
                continue
            if record['state'] == 'FAULT':
                add('MCU_FAULT', 'core_fault', index, 'mcu',
                    'MCU 留下异常记录；异常路径中的外设字段不能证明采集仍在继续。',
                    checks=['核对异常号、CFSR/HFSR 及地址有效位，不把无效 BFAR/MMFAR 当作故障地址。'],
                    evidence={k: record[k] for k in ('exception', 'faults_raw', 'fault_address_valid')})
                continue
            for name in REFS:
                data = record.get(name)
                if data is None:
                    add(name.upper() + '_LEGACY', 'historical_abi', index, name,
                        '此历史 ABI 没有' + LABELS[name] + '字段；缺少字段不代表器件故障。')
                    continue
                evidence = {k: data.get(k) for k in (
                    'state', 'effective_state', 'error', 'last_error', 'detail_raw',
                    'bus_detail_raw', 'current_driver_failure', 'last_driver_failure',
                    'last_error_detail_raw', 'cleanup_error', 'cleanup_detail_raw',
                    'cleanup_driver_failure', 'has_sample', 'nominal_sample_age_ms')}
                if data['state'] == 'OFF':
                    add(name.upper() + '_OFF', 'not_started', index, name,
                        LABELS[name] + '尚未启动；不作器件好坏判断。', evidence=evidence)
                    continue
                if data['error'] != 'OK':
                    code, observed, possible, checks = _cause(name, data)
                    add(name.upper() + '_' + code, 'recorded_fault', index, name,
                        observed, possible, checks, evidence)
                if data.get('cleanup_error', 'OK') != 'OK':
                    add(name.upper() + '_CLEANUP', 'cleanup_failure', index, name,
                        '清理失败，保留原始错误与清理错误；驱动已停止，不能承诺接口处于已知状态。',
                        checks=['先核对两组错误详情及接口持有/停放状态；不自动重试或执行恢复写操作。'], evidence=evidence)
                if data['effective_state'] == 'STALE':
                    add(name.upper() + '_STALE', 'stale_evidence', index, name,
                        '上次样本在记录发布时已经过期；历史值不能作为本次有效读数。',
                        checks=['核对数据年龄、采集进度和调度；保留历史样本用于比较。'], evidence=evidence)
                if data['error'] == 'OK' and data['last_error'] != 'OK':
                    add(name.upper() + '_HISTORY', 'recorded_recovery', index, name,
                        '当前错误已清除，仍保留先前错误；历史错误不等于当前持续故障。',
                        checks=['将历史错误、重初始化计数和后续独立观测对照，不能把一次恢复当作稳定性验证。'], evidence=evidence)
                if data.get('fresh'):
                    add(name.upper() + '_SAMPLE', 'sample_observed', index, name,
                        '记录发布时具有符合此诊断配置的新样本；不证明精度、实物身份或长期可靠性。', evidence=evidence)
                elif data['error'] == 'OK' and data['effective_state'] != 'STALE':
                    add(name.upper() + '_WAIT', 'in_progress', index, name,
                        '尚无此次有效样本，或正在重新采集；不把等待阶段判作器件损坏。', evidence=evidence)
    return dict(schema='r10-evidence-localization/v1', origin=report['origin'],
                assessment_scope='record-publication time only' if eligible else 'preserved evidence only',
                circuit_sources={p: sha_bytes(regular_bytes(ROOT / p)) for p in ANALYSIS_SOURCES},
                findings=findings, confirmed_defects=[], hardware_qualified=False,
                physical_fault_localization_verified=False, automatic_target_actions=False)


def render_zh(localization):
    lines = ['\n\n## 证据与排查位置\n',
             '只解释保存记录发布时的状态；以下可能原因是排查假设，未确认任何器件损坏。\n']
    for finding in localization['findings']:
        record = finding['record_index']
        prefix = '捕获' if record is None else '记录 %d' % (record + 1)
        lines.append('\n%s / %s [%s]：%s\n' %
                     (prefix, finding['subsystem'], finding['code'], finding['observed_zh']))
        for cause in finding['possible_causes_zh']:
            lines.append('可能原因（未确认）：%s。\n' % cause)
        for check in finding['next_checks_zh']:
            lines.append('下一步：%s\n' % check)
        circuit = finding['circuit']
        if circuit and finding['category'] in ('recorded_fault', 'cleanup_failure'):
            lines.append('对应电路：%s %s。\n' % (circuit['reference'], circuit['fitted_value']))
            for net, nodes in circuit['signals'].items():
                lines.append('  %s：%s。\n' % (net, ' / '.join(n['endpoint'] for n in nodes)))
            for row in circuit['power_points']:
                p, g = row['point'], row['ground']
                lines.append('  电源记录位置 %s (%s)，%s，顶视坐标 %s mm；地参考 %s。\n' %
                             (p['point_id'], p['net'], p['side'], p['xy_mm'], g['point_id']))
    return ''.join(lines)
