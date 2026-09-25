"""Independent decoding of v4 raw IMU observations; no orientation estimates."""
import struct
from .acquisition import within_cycle


def imu_measurement(words,protocol):
    w=protocol['words'];g=lambda n:words[w['IMU_'+n]]
    wire=struct.pack('<4I',*words[w['IMU_RAW']:w['IMU_RAW']+4])[:14]
    e=g('EVIDENCE');raw=list(struct.unpack('>7h',wire))
    d=dict(status=g('SAMPLE_STATUS'),error=g('SAMPLE_ERROR'),init_error=g('INIT_ERROR'),
           io_error=g('IO_ERROR'),read_start_ms=g('READ_START_MS'),read_ms=g('READ_MS'),
           read_finished_ms=g('READ_FINISHED_MS'),config=g('CONFIG'),evidence=e,
           error_history=g('ERROR_HISTORY'),spi_nominal_hz=g('BUS_HZ'),raw_hex=wire.hex(),
           raw_signed=raw,raw_transfer_complete=bool(e&0x10000),who_am_i=e>>24,
           status_before=e&255,status_after=(e>>8)&255,
           kind='decimated bench observation, not every 50Hz device update')
    d['nominal_units']=None
    # Preserve raw bytes on failures without presenting them as measurements.
    if d['status']==2 and not d['error'] and (e&0x70000)==0x70000:
        d['nominal_units']=dict(acceleration_g=[v/1024 for v in raw[:3]],
                              angular_rate_dps=[v*4000/32768 for v in raw[3:6]],
                              temperature_c=raw[6]/128+25)
    d['at_numeric_limit']=[i for i,v in enumerate(raw[:6]) if v in (-32768,32767)]
    return d


def imu_checks(samples,protocol,live):
    w=protocol['words'];records=[imu_measurement(x['words'],protocol) for x in samples]
    counters=[x['words'][w['ACQ_COUNTER']] for x in samples]
    fresh=(live and all(x['state']==3 for x in samples) and
           all(0<(b-a)%2**32<0x80000000 for a,b in zip(counters,counters[1:])))
    statuses=[]
    for sample,d in zip(samples,records):
        ws=sample['words'];e=d['evidence'];c=d['config']
        timing=(within_cycle(d['read_start_ms'],ws[w['ACQ_START_MS']],ws[w['ACQ_FINISHED_MS']])
                and within_cycle(d['read_ms'],d['read_start_ms'],d['read_finished_ms'])
                and within_cycle(d['read_finished_ms'],d['read_start_ms'],ws[w['ACQ_FINISHED_MS']])
                and within_cycle(ws[w['ACQ_FINISHED_MS']],ws[w['ACQ_START_MS']],ws[w['UPTIME_MS']])
                and (d['read_finished_ms']-d['read_start_ms'])%2**32<=5)
        coherent=(not d['error'] and not d['init_error'] and not d['io_error'] and
                  d['who_am_i']==0xe9 and e&0x70000==0x70000 and e&4 and not(e&0x8480) and
                  c&0xffffff==0x0f0a0a and c&0x02000000 and d['spi_nominal_hz']==1000000 and timing)
        status={0:'NOT_TESTED',1:'RUNNING',2:'PASS',3:'FAIL'}[d['status']]
        if status=='PASS' and not coherent:status='FAIL'
        if status=='PASS' and not fresh:status='INCONCLUSIVE'
        if status=='NOT_TESTED' and fresh:status='FAIL'
        if status!='PASS':d['nominal_units']=None
        statuses.append(status)
    status=next((v for v in ('FAIL','INCONCLUSIVE','RUNNING','NOT_TESTED') if v in statuses),'PASS')
    errors={v:k for k,v in protocol['imu']['errors'].items()}
    details=[dict(record=i,status=s,error=errors.get(d['error'],'UNKNOWN'),init_error=d['init_error'],
                  io_error=hex(d['io_error']),config=hex(d['config']),evidence=hex(d['evidence']))
             for i,(s,d) in enumerate(zip(statuses,records))]
    history=0
    for d in records:history|=d['error_history']
    stable=all((a['error_history'] & b['error_history'])==a['error_history'] for a,b in zip(records,records[1:]))
    rows=[('IMU_SAMPLES',status,str(details),
           'Identity/transport: inspect U4 3V3A and PB3/4/5/7. CONFIG: compare recorded values and reset evidence. '
           'READY_TIMEOUT: data-ready was not observed. UPDATE_DURING_READ: discard that burst. '
           'These causes narrow checks; they do not uniquely identify a damaged part.'),
          ('IMU_ERROR_HISTORY','FAIL' if not stable else 'INCONCLUSIVE' if history else 'INFO',
           f'latched error bits=0x{history:x}; history monotonic={stable}',
           'A later successful observation does not erase earlier failures; reset starts a new session.'),
          ('IMU_RANGE_SCREEN','INCONCLUSIVE' if any(d['at_numeric_limit'] for d in records) else 'INFO',
           'numeric rail indices per observation='+str([d['at_numeric_limit'] for d in records]),
           'Signed limits are retained, not invented invalid-data codes. Physical stimulus and a reference are still needed.'),
          ('IMU_INTERRUPT_WIRING','NOT_TESTED','DRDY is polled over SPI; the PE10 interrupt wire is not exercised.',''),
          ('IMU_SELF_TEST','NOT_TESTED','No built-in sensor self-test, calibrated motion or accuracy test has run.','')]
    return rows,records
