"""Interpret raw bench samples independently of the firmware's pass flags.

Voltage units mV, MS5611 pressure Pa, temperature 0.01 C. No flight-state logic.
Limits here are diagnostic plausibility windows, not accuracy certification.
"""
from decimal import Decimal, localcontext


def signed(v):
    return v if v < 0x80000000 else v - 0x100000000


def pressure_reference(c, d1, d2):
    """TE B3 equations at 32 decimal digits; no firmware integer rounding."""
    with localcontext() as ctx:
        ctx.prec = 32
        dt = Decimal(d2) - Decimal(c[5])*256
        t = 2000 + dt*c[6]/8388608
        off = Decimal(c[2])*65536 + Decimal(c[4])*dt/128
        sens = Decimal(c[1])*32768 + Decimal(c[3])*dt/256
        if t < 2000:
            off2 = 5*(t-2000)**2/2
            sens2 = 5*(t-2000)**2/4
            if t < -1500:
                off2 += 7*(t+1500)**2
                sens2 += 11*(t+1500)**2/2
            t -= dt*dt/2147483648
            off -= off2; sens -= sens2
        p = (Decimal(d1)*sens/2097152 - off)/32768
        return float(p), float(t)


def sample_measurements(w, W):
    g=lambda n:w[W[n]]
    return dict(counter=g('ACQ_COUNTER'),uptime_ms=g('UPTIME_MS'),
                started_ms=g('ACQ_START_MS'),finished_ms=g('ACQ_FINISHED_MS'),
                adc=dict(status=g('ADC_STATUS'),error=g('ADC_ERROR'),hal_error=g('ADC_HAL_ERROR'),
                         init_error=g('ADC_INIT_ERROR'),valid_mask=g('ADC_VALID_MASK'),
                         sampled_ms=g('ADC_SAMPLE_MS'),calibration_raw=g('ADC_CAL_RAW'),
                         reference_raw=g('ADC_REF_RAW'),vlogic_raw=g('ADC_VLOGIC_RAW'),
                         v3v3_raw=g('ADC_3V3_RAW'),vdda_mv=g('VDDA_MV'),
                         vlogic_mv=g('VLOGIC_MV'),v3v3_mv=g('V3V3_MV')),
                baro=dict(status=g('BARO_SAMPLE_STATUS'),error=g('BARO_SAMPLE_ERROR'),
                          valid_mask=g('BARO_VALID_MASK'),prom=w[35:43],
                          d1=g('BARO_D1'),d2=g('BARO_D2'),d1_read_ms=g('BARO_D1_MS'),
                          d2_read_ms=g('BARO_D2_MS'),pressure_pa=signed(g('PRESSURE_PA')),
                          temperature_centic=signed(g('TEMP_CENTIC'))))


def within_cycle(value,start,end):
    return ((value-start)&0xffffffff) <= ((end-start)&0xffffffff) < 2000


def measurement_checks(samples,W,live):
    m=[sample_measurements(s['words'],W) for s in samples]
    fresh=(live and all(s['state']==3 for s in samples) and
           all(0 < ((b['counter']-a['counter'])&0xffffffff) < 0x80000000 for a,b in zip(m,m[1:])) and
           all(within_cycle(x['finished_ms'],x['started_ms'],x['uptime_ms']) for x in m))
    rows=[('SAMPLE_FRESHNESS','PASS' if fresh else 'INCONCLUSIVE',
           'counters='+str([x['counter'] for x in m]),'A static old sample is not a pass.')]
    grouped={}
    for i,(sample,decoded) in enumerate(zip(m,samples)):
        for code,status,evidence,step in _sample_checks(sample,decoded['words'],W,fresh):
            grouped.setdefault(code,[]).append((i,status,evidence,step))
    for code,records in grouped.items():
        statuses=[r[1] for r in records]
        status=next((x for x in ('FAIL','INCONCLUSIVE','RUNNING','NOT_TESTED') if x in statuses),statuses[-1])
        affected=[i for i,s,_,_ in records if s not in ('PASS','INFO')]
        rows.append((code,status,'affected records='+str(affected)+'; latest='+records[-1][2],records[-1][3]))
    return rows


def _sample_checks(latest,w,W,fresh):
    from .mailbox import prom_ok
    g=lambda n:w[W[n]]
    rows=[]
    def add(code,status,evidence,next_step=''):rows.append((code,status,evidence,next_step))
    a=latest['adc']; cal=a['calibration_raw']; ref=a['reference_raw']
    consistent=False
    if (20000 <= cal <= 30000 and 0 < ref < 65535 and a['valid_mask']==7 and
        all(0 <= a[k] <= 65535 for k in ('vlogic_raw','v3v3_raw'))):
        expected=3300*cal/ref
        consistent=(1800 <= expected <= 3600 and abs(a['vdda_mv']-expected) <= .51 and
                    abs(a['vlogic_mv']-a['vlogic_raw']*a['vdda_mv']*11/65535) <= .51 and
                    abs(a['v3v3_mv']-a['v3v3_raw']*a['vdda_mv']*2/65535) <= .51 and
                    g('SYSCFG_PMCR') & 0x0c000000 == 0x0c000000 and
                    g('ADC_PCSEL') & 0x80003 == 0x80003 and
                    not a['error'] and not a['init_error'] and not a['hal_error'] and
                    within_cycle(a['sampled_ms'],latest['started_ms'],latest['finished_ms']))
    status={0:'NOT_TESTED',1:'RUNNING',2:'PASS',3:'FAIL'}[a['status']]
    if status=='PASS' and not consistent:status='FAIL'
    if status=='PASS' and not fresh:status='INCONCLUSIVE'
    add('ADC_MEASUREMENTS',status,str(a),
        'Compare TP_VLOGIC/3V3/3V3A with a DMM; check R60/R61 and R62/R63. ADC status is acquisition only; no accuracy qualification.')
    if status=='PASS':
        nominal=3135 <= a['v3v3_mv'] <= 3465 and 3135 <= a['vdda_mv'] <= 3465 and 3500 <= a['vlogic_mv'] <= 8600
        add('POWER_BENCH_SCREEN','INFO' if nominal else 'FAIL',
            f"VLOGIC={a['vlogic_mv']}mV, 3V3={a['v3v3_mv']}mV, 3V3A/VREF+={a['vdda_mv']}mV",
            'Nominal bench window: 3.3V +/-5%, VLOGIC 3.5..8.6V. An outlier requires DMM comparison; it does not identify a failed part by itself.')
    b=latest['baro']; consistent=False
    if (b['valid_mask']==3 and not b['error'] and prom_ok(w) and
        0 < b['d1'] < 0xffffff and 0 < b['d2'] < 0xffffff):
        pressure,temp=pressure_reference(b['prom'],b['d1'],b['d2'])
        consistent=(abs(b['pressure_pa']-pressure) <= 3 and abs(b['temperature_centic']-temp) <= 2 and
                    1000 <= b['pressure_pa'] <= 120000 and -4000 <= b['temperature_centic'] <= 8500 and
                    within_cycle(b['d1_read_ms'],latest['started_ms'],latest['finished_ms']) and
                    within_cycle(b['d2_read_ms'],b['d1_read_ms'],latest['finished_ms']))
    status={0:'NOT_TESTED',1:'RUNNING',2:'PASS',3:'FAIL'}[b['status']]
    if status=='PASS' and not consistent:status='FAIL'
    if status=='PASS' and not fresh:status='INCONCLUSIVE'
    add('BARO_MEASUREMENTS',status,str(b),
        '1/2=held I2C lines, 3=NACK, 10=invalid PROM, 11=invalid raw conversion, 12=range/conversion. Compare with an independent pressure/temperature reference; repeated valid values alone do not prove a working sensor.')
    return rows
