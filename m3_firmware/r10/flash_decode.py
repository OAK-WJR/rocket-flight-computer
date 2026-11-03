"""Decode raw ABI5 flash diagnostic evidence; no probe or array qualification."""
import struct

WORD_INDICES=tuple(range(98,128))+tuple(range(193,247))
STATES=('OFF','INITIALIZING','INIT_CONFIRM','POWER_GUARD','START','READING','CONFIRM','WAIT','RETRY','STOPPED')
ERRORS=('OK','ADAPTER','INIT','CONFIG','START_ERROR','READ_ERROR','TIMEOUT','COUNT',
        'DEVICE_BUSY','SUSPENDED','IDENTITY','SFDP_SIGNATURE','QUAD_DISABLED',
        'QUAD_IDENTITY','UNSTABLE_ID','STATUS_CHANGED','TIMEBASE','CLEANUP')
PORT_PHASES=('NEW','RESET_HELD','RESET_RELEASED','PRIMED','READY','FAULT')
PORT_ERRORS=('NONE','ADAPTER','CLOCK','DEVICE_REVISION','OWNERSHIP','GPIO',
             'CLOCK_ENABLE','PERIPHERAL_RESET','TIMING_WORKAROUND','CONFIGURATION',
             'ARGUMENT','START','STATUS','COUNT','DATA','CLEANUP')
COMMANDS=('sr1_before','sr2','sr3','jedec_before','sfdp_header','quad_id','jedec_after','sr1_after')
LENGTHS=(1,1,1,3,8,4,3,1)
NATIVE_FRAMES=(0x05000105,0x05000135,0x05000115,0x0500019f,
               0x0520255a,0x0710ed94,0x0500019f,0x05000105)

def driver_failure(detail):
    if not detail:return None
    why=detail>>24;phase=(detail>>16)&255
    return dict(reason=PORT_ERRORS[why] if why<len(PORT_ERRORS) else 'UNKNOWN',reason_code=why,
                phase=PORT_PHASES[phase] if phase<len(PORT_PHASES) else 'UNKNOWN',
                sr_low_raw='%04x'%(detail&65535))

def complete_evidence(raw):
    if (raw[0][0]&1 or raw[1][0]&128 or not raw[1][0]&2 or
        raw[3][:3]!=b'\xef\x40\x18' or raw[4][:4]!=b'SFDP' or
        raw[5][:4]!=b'\xef\x17\xef\x17' or raw[6][:3]!=raw[3][:3] or raw[7][0]!=raw[0][0]):
        raise ValueError('Flash last-good raw evidence contradicts the fitted profile')
    if any(any(data[n:]) for data,n in zip(raw,LENGTHS)):
        raise ValueError('Flash last-good padding contains unaccounted bytes')

def decode_flash(words):
    v=[words[i] for i in WORD_INDICES]
    state,error,last=v[:3];flags=v[69];pflags=v[83]
    if (state>=len(STATES) or error>=len(ERRORS) or last>=len(ERRORS) or
        flags&~3 or pflags&~7 or v[5] not in (0,17) or v[16]>8 or
        v[17] not in (0,1,3,7,15,31,63,127,255) or v[70]>=len(PORT_PHASES)):
        raise ValueError('Unsupported flash state/error/count/flags')
    if state==0 and any(v):raise ValueError('OFF flash record carries acquisition claims')
    valid=bool(flags&1);has=bool(flags&2)
    if valid and (not has or error or state not in (4,5,6,7)):
        raise ValueError('Flash validity contradicts acquisition phase')
    if error and (state not in (1,2,3,8,9) or error!=last):
        raise ValueError('Flash error contradicts acquisition phase/history')
    if state in (8,9) and not error:raise ValueError('Flash retry/stop lacks failure evidence')
    if v[5] and state!=9:raise ValueError('Failed flash cleanup did not stop acquisition')
    data=struct.pack('<16I',*v[35:51]);sample=struct.pack('<16I',*v[53:69])
    raw=[data[i*8:(i+1)*8] for i in range(8)]
    good=[sample[i*8:(i+1)*8] for i in range(8)]
    counts=tuple(struct.pack('<2I',*v[51:53]))
    if any(n>limit for n,limit in zip(counts,LENGTHS)):
        raise ValueError('Flash partial byte count exceeds its command')
    if any(any(raw[i][counts[i]:]) for i in range(8)):
        raise ValueError('Flash partial bytes exceed the retained count')
    if any(v[17]&(1<<i) and counts[i]!=LENGTHS[i] for i in range(8)):
        raise ValueError('Flash completion mask lacks a full response')
    if not has and any((*v[27:35],*v[53:69],v[10],v[12],v[13])):
        raise ValueError('Flash last-good evidence exists without a sample')
    if has:
        complete_evidence(good)
        times=v[27:35]
        if v[12]!=1000000 or any(((n-v[10])&0xffffffff)>=150 for n in times):
            raise ValueError('Flash last-good clock/timestamps contradict a bounded batch')
        if any(((b-a)&0xffffffff)>=150 for a,b in zip(times,times[1:])):
            raise ValueError('Flash last-good command order is inconsistent')
    if valid and (v[11]!=1000000 or v[70]!=4 or not pflags&1 or pflags&4 or v[82]!=1000000 or
                  v[72] not in (0x1003,0x2001,0x2003,0x2007) or v[72]!=words[9]>>16):
        raise ValueError('Flash validity lacks native clock/ownership evidence')
    if pflags&2 and (not pflags&1 or v[70] not in (4,5)):
        raise ValueError('Flash active transfer lacks native ownership')
    if valid and (v[80]>=8 or v[78]!=NATIVE_FRAMES[v[80]] or v[76]!=v[78] or
                  v[79]!=LENGTHS[v[80]]-1 or v[81]>LENGTHS[v[80]] or
                  v[74]!=0x3f000001 or v[75]&0x19):
        raise ValueError('Flash validity contradicts the native read-only frame/status')
    age=((words[5]-v[10])&0xffffffff) if has else None
    fresh=valid and age is not None and age<3000
    return dict(state=STATES[state],effective_state='STALE' if valid and not fresh else STATES[state],
        error=ERRORS[error],last_error=ERRORS[last],detail_raw='%08x'%v[3],last_error_detail_raw='%08x'%v[4],
        cleanup_error=ERRORS[v[5]],cleanup_detail_raw='%08x'%v[6],
        current_driver_failure=driver_failure(v[3]),last_driver_failure=driver_failure(v[4]),
        cleanup_driver_failure=driver_failure(v[6]),
        reported_valid=valid,effective_valid=fresh,has_sample=has,fresh=fresh,
        nominal_sample_age_ms=age,last_good_tick_lo=v[10],nominal_bus_hz=v[11],sample_nominal_bus_hz=v[12],
        samples=v[13],failures=v[14],retries=v[15],command=v[16],completed_mask=v[17],last_io_count=v[18],
        pending_byte_counts=dict(zip(COMMANDS,counts)),
        pending_raw=dict(zip(COMMANDS,(raw[i][:counts[i]].hex() for i in range(8)))),
        sample_raw=dict(zip(COMMANDS,(good[i][:LENGTHS[i]].hex() for i in range(8)))) if has else None,
        pending_tick_lo=dict(zip(COMMANDS,v[19:27])),sample_tick_lo=dict(zip(COMMANDS,v[27:35])) if has else None,
        core_times=dict(stage_tick_lo=v[7],batch_tick_lo=v[8],observed_tick_lo=v[9]),
        port=dict(phase=PORT_PHASES[v[70]],phase_tick_lo=v[71],revision_raw=v[72],
            detail_raw='%08x'%v[73],last_failure=driver_failure(v[73]),last_cr_raw='%08x'%v[74],
            last_sr_raw='%08x'%v[75],last_ccr_raw='%08x'%v[76],last_dr_raw=v[77],
            expected_ccr_raw='%08x'%v[78],expected_dlr=v[79],command=v[80],received_bytes=v[81],
            nominal_bus_hz=v[82],owned=bool(pflags&1),transfer_active=bool(pflags&2),pins_parked=bool(pflags&4)),
        array_integrity_assessed=False,device_identity_authenticated=False,hardware_qualified=False,
        note='Read-only status/identity responses; no array, write, endurance, power-loss or physical timing qualification.')
