"""Ordered bench investigations, not unique component failure diagnoses."""
GROUPS = {
 'battery':dict(title='Battery input and protection',components=['J1','U9','R80','R81','R84'],points=['TP80.1','TP84.1','TP81.1','TP85.1','TP88.1'],
   action='Confirm the input, contact enable and post-protection voltage first; FAULT only locates the protection branch and cannot distinguish a load short, temperature, wiring or chip problem.'),
 'usb_power':dict(title='USB supply and current limit',components=['J3','U10','R85'],points=['C28.1','TP82.1','TP86.1','TP88.1'],
   action='Measure stage by stage along USB input and current-limit output, checking the cable and supply configuration; USB failing to connect does not show the MCU is broken.'),
 'source_mux':dict(title='Logic source selection and hold-up',components=['U11','C84'],points=['TP81.1','TP82.1','TP83.1','TP87.1','TP88.1'],
   action='Compare both inputs with VLOGIC. ST high may also mean a high-impedance output and cannot alone be taken as USB supplying normally.'),
 'logic_3v3':dict(title='3.3 V regulator and load',components=['U2','L1','C8','C9'],points=['TP83.1','C6.1','J2.5','J2.1'],
   action='Confirm the regulator input first, then check 3V3, the U2/L1 area and downstream loads; DC readings cannot prove start-up, ripple or transient stability.'),
 'sensor_power':dict(title='Sensor supply branch',components=['L2','C10','C11'],points=['J2.5','C10.1','J2.1'],
   action='If 3V3 is present but 3V3A is low, check the L2 connection and downstream loads first, then IMU, barometer or GNSS communication.'),
 'clock_reset':dict(title='MCU start-up, clock and debug',components=['U1','Y1','C25','C26','J2'],points=['J2.5','J2.4','C19.1','C20.1','J2.1'],
   action='After confirming supply and reset, read start-up / clock evidence over SWD. J2 has a project-specific pin order; clock ready bits are not a frequency measurement.'),
 'adc':dict(title='Voltage acquisition and dividers',components=['R60','R61','R62','R63','U1'],points=['C6.1','R61.1','J2.5','R63.1','J2.1'],
   action='Measure each rail and its divider node as a pair with an independent meter, recording error and input impedance; the ADC reference cannot prove its own supply correct.'),
 'imu':dict(title='IMU communication and raw samples',components=['U4','R11','C30','C31'],points=['C10.1','J2.1'],
   action='After confirming supply, check U4 orientation, chip select, SPI and DRDY. Judge identity, data freshness and error history separately; never replace the chip over one error code.'),
 'barometer':dict(title='Barometer communication',components=['U5','R12','R13','R64','C32'],points=['C10.1','J2.1'],
   action='After confirming supply, follow the NACK, bus-held-low or PROM CRC error branch; bench readings do not prove pressure accuracy or installed venting.'),
 'storage':dict(title='Flash and logging chain',components=['U3','R10','C29'],points=['J2.5','J2.1'],
   action='Distinguish JEDEC, quad read-back, write protection, capacity and download errors; keep the original log first and never erase as a recovery step.'),
 'gnss':dict(title='GNSS reception and data freshness',components=['U6','C33','C34'],points=['C10.1','J2.1'],
   action='Distinguish no serial response, stale data and no fix. No fix alone does not prove the receiver is broken; then check antenna, enclosure and actual signal.'),
 'camera':dict(title='Camera separate supply and UART',components=['J9','U7','U8','U12','U13'],points=['TP70.1','TP71.1','TP72.1','TP90.1','TP91.1','TP75.1','TP76.1','TP74.1'],
   action='The camera is off by default; check the installed image\'s query mode first, then supply, the separate I/O supply and UART. This tool never switches camera power.'),
 'usb_data':dict(title='USB data and cable detection',components=['J3','D4','R7','R8','R9','R110','U1'],points=['C28.1','TP92.1','J2.5','J2.1'],
   action='Compare the raw USB exchange, cable detection, clock and enumeration state. CRC / timeouts can come from the cable, software or supply and cannot uniquely locate D4 or the MCU.'),
}


def investigations(report, state):
    reasons={}
    def use(group,why):
        reasons.setdefault(group,[])
        if why not in reasons[group]:reasons[group].append(why)
    if state!='CAPTURED':
        for g in ('usb_power','source_mux','logic_3v3','clock_reset','usb_data'):
            use(g,'Capture incomplete: confirm connection, supply and installed firmware first; readings not obtained are neither a pass nor evidence of a broken chip.')
    for c in report['checks']:
        if c['status'] not in ('FAIL','WARNING','INCONCLUSIVE'):continue
        k=c['id'];why=k+': '+c['status']
        if state!='CAPTURED' and k.startswith(('IMU','BARO','FLASH','LOGGING','GNSS','CAMERA','ADC')):
            # No sensor result was accepted: resolve the capture path first.
            # Missing records alone do not justify examining each sensor IC.
            continue
        if k.startswith('DC_3V3A'):use('sensor_power',why)
        elif k.startswith('DC_3V3'):use('logic_3v3',why)
        elif k=='POWER_PATH':
            step=c.get('next_step','')
            use('sensor_power' if 'L2' in step else 'logic_3v3' if 'U2/' in step else 'source_mux',why)
        elif k.startswith(('ADC','DIV_')):use('adc',why)
        elif k.startswith('IMU'):use('imu',why)
        elif k.startswith('BARO'):use('barometer',why)
        elif k.startswith(('FLASH','LOGGING')):use('storage',why)
        elif k.startswith('GNSS'):use('gnss',why)
        elif k.startswith('CAMERA'):use('camera',why)
        elif k.startswith('USB'):use('usb_data',why)
        elif k.startswith(('TARGET','RECORD_','FIRMWARE','TEST_SEQUENCE','HSE','POWER_MONITOR','POWER_HISTORY')):use('clock_reset',why)
    # These have already been decoded and checked by the mailbox analyzer.
    for row in report.get('measurements',[]):
        p=row.get('power_status',{})
        faults=set(p.get('fault_signals_seen') or [])|set(p.get('active_fault_signals') or [])
        for fault,g in [('BATTERY_EFUSE','battery'),('USB_LIMITER','usb_power'),('CAMERA_EFUSE','camera')]:
            if fault in faults:use(g,fault+': a current or historical FAULT was observed; the root cause is not uniquely determined.')
    return [dict(id=g,**row,reasons=reasons[g]) for g,row in GROUPS.items() if g in reasons]
