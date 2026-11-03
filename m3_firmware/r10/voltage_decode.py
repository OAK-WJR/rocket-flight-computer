"""Decode saved ABI4 voltage evidence. No probe or physical model."""
from fractions import Fraction

STATES=('OFF','INITIALIZING','START','READING','CONFIRM','WAIT','RETRY','STOPPED')
ERRORS=('OK','ADAPTER','INIT','CONFIG','CALIBRATION','START_ERROR','READ_ERROR','TIMEOUT',
        'RAW_RANGE','REFERENCE','REFERENCE_DRIFT','SATURATED','TIMEBASE','CLEANUP')
PORT_PHASES=('NEW','REGULATOR_WAIT','CAL1_WAIT','CAL1_GUARD','READY1_WAIT',
             'CAL3_WAIT','CAL3_GUARD','READY3_WAIT','READY','ERROR')
CONFIG_KEYS=('revision','factory_calibration16','resolution_bits','adc12_hz_nominal','adc3_hz_nominal')
CHANNELS=('reference_before','logic','camera','vbat','reference_after')
PORT_ERRORS=('NONE','ADAPTER','CLOCK','DEVICE_REVISION','FACTORY_CALIBRATION','ADC_OWNERSHIP',
             'CLOCK_ENABLE','PERIPHERAL_RESET','REGULATOR','CALIBRATION','READY','CONFIGURATION',
             'ARGUMENT','START','STATUS','DATA','CLEANUP')

def native_failure(detail):
    if not detail:return None
    reason=detail>>24;phase=(detail>>20)&15
    return dict(reason=PORT_ERRORS[reason] if reason<len(PORT_ERRORS) else 'UNKNOWN',reason_code=reason,
                phase=PORT_PHASES[phase] if phase<len(PORT_PHASES) else 'UNKNOWN',
                unit=(detail>>16)&3,isr_low_raw='%04x'%(detail&0xffff))

def nominal(config,raw):
    rev,cal,bits,hz1,hz3=config
    if (rev not in (0x1003,0x2001,0x2003,0x2007) or not 20000<=cal<=30000 or bits!=10 or
            hz1!=(4000000 if rev==0x1003 else 2000000) or hz3!=hz1):
        raise ValueError('Voltage sample configuration is incompatible with native profile')
    if len(raw)!=5 or any(not 0<=n<1023 for n in raw):
        raise ValueError('Voltage last-good raw data is clipped or out of range')
    a,b=raw[0],raw[4]
    if not a or not b or abs(a-b)*100>min(a,b)*2:
        raise ValueError('Voltage last-good reference is absent or drifting')
    def rounded(x):return (2*x.numerator+x.denominator)//(2*x.denominator)
    vdda=Fraction(3300*cal*1023*2,65535*(a+b))
    result=[rounded(vdda)]+[rounded(Fraction(raw[i]*ratio,1023)*vdda) for i,ratio in ((1,11),(2,11),(3,4))]
    result+=[rounded(Fraction(1000*abs(a-b),min(a,b)))]
    if not 1800<=result[0]<=3600:raise ValueError('Voltage last-good reference outside diagnostic screen')
    return result

def decode_voltage(w):
    state,error,last=w[128:131];flags=w[144];pflags=w[192]
    if (state>=len(STATES) or error>=len(ERRORS) or last>=len(ERRORS) or
            w[133] not in (0,13) or flags&~3 or pflags&~3 or w[142]>5 or
            w[143] not in (0,1,3,7,15,31) or w[180]>=len(PORT_PHASES) or w[190] not in (0,1,3)):
        raise ValueError('Unsupported voltage state/error/flags')
    if state==0 and any(w[128:193]):raise ValueError('OFF voltage record carries acquisition claims')
    valid=bool(flags&1);has=bool(flags&2)
    if valid and (not has or error or state not in (2,3,4,5)):
        raise ValueError('Voltage validity contradicts acquisition phase')
    if error and (state not in (1,6,7) or error!=last):
        raise ValueError('Voltage failure contradicts phase/history')
    if state in (6,7) and not error:raise ValueError('Voltage retry/stop lacks failure evidence')
    if w[133] and state!=7:raise ValueError('Failed voltage cleanup did not stop acquisition')
    raw=list(w[145:150]);raw_ms=list(w[150:155])
    if any((raw[i] or raw_ms[i]) and not w[143]&(1<<i) for i in range(5)):
        raise ValueError('Voltage partial sample mask contradicts raw evidence')
    good=list(w[155:160]);good_ms=list(w[160:165]);config=list(w[165:170]);good_config=list(w[170:175])
    values=list(w[175:180])
    if not has and any((*w[155:165],*w[170:180],w[138],w[139])):
        raise ValueError('Voltage last-good evidence exists without a sample')
    if has:
        if nominal(good_config,good)!=values:
            raise ValueError('Voltage converted values disagree with retained raw evidence')
        if good_config[0]!=w[9]>>16:raise ValueError('Voltage sample revision differs from MCU record')
        if w[138]!=good_ms[4] or any(((good_ms[i+1]-good_ms[i])&0xffffffff)>=100 for i in range(4)) or ((good_ms[4]-good_ms[0])&0xffffffff)>=100:
            raise ValueError('Voltage last-good timestamps contradict a bounded serial batch')
    if valid and (config!=good_config or w[180]!=8 or not pflags&1 or
                  w[182]!=config[0] or w[183]!=config[1] or w[184]!=config[3]):
        raise ValueError('Voltage validity lacks native driver/configuration evidence')
    age=((w[5]-w[138])&0xffffffff) if has else None
    fresh=valid and age is not None and age<1000
    names=('vdda_mv_nominal','logic_mv_nominal','camera_mv_nominal','v3v3_mv_coarse','reference_drift_permille')
    return dict(state=STATES[state],effective_state='STALE' if valid and not fresh else STATES[state],
        error=ERRORS[error],last_error=ERRORS[last],detail_raw='%08x'%w[131],last_error_detail_raw='%08x'%w[132],
        cleanup_error=ERRORS[w[133]],cleanup_detail_raw='%08x'%w[134],reported_valid=valid,effective_valid=fresh,
        current_driver_failure=native_failure(w[131]),last_driver_failure=native_failure(w[132]),
        cleanup_driver_failure=native_failure(w[134]),
        has_sample=has,fresh=fresh,nominal_sample_age_ms=age,last_good_tick_lo=w[138],
        samples=w[139],failures=w[140],retries=w[141],slot=w[142],pending_mask=w[143],
        pending_raw=dict(zip(CHANNELS,raw)),pending_tick_lo=dict(zip(CHANNELS,raw_ms)),
        sample_raw=dict(zip(CHANNELS,good)),sample_tick_lo=dict(zip(CHANNELS,good_ms)),
        current_configuration=dict(zip(CONFIG_KEYS,config)),sample_configuration=dict(zip(CONFIG_KEYS,good_config)),
        values_nominal=dict(zip(names,values)) if has else None,
        core_times=dict(stage_tick_lo=w[135],batch_tick_lo=w[136],observed_tick_lo=w[137]),
        port=dict(phase=PORT_PHASES[w[180]],phase_tick_lo=w[181],revision_raw=w[182],factory_calibration16_raw=w[183],
            adc_hz_nominal=w[184],adc1_calfact_raw=w[185],adc3_calfact_raw=w[186],last_cr_raw='%08x'%w[187],
            last_isr_raw='%08x'%w[188],last_dr_raw=w[189],unit=w[190],detail_raw='%08x'%w[191],
            last_failure=native_failure(w[191]),owned=bool(pflags&1),conversion_active=bool(pflags&2)),
        electrical_health_assessed=False,measurement_accuracy_qualified=False,hardware_qualified=False,
        note="Freshness is evaluated at record publication; capture timing and physical acquisition are not authenticated.")
