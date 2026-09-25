"""Independently check a camera-info response, retaining raw/error evidence."""
import struct

def crc8(data):
    # Polynomial long division, separate implementation from the C shift loop.
    remainder=int.from_bytes(bytes(data)+b'\0','big')
    for bit in range(len(data)*8+7,7,-1):
        if remainder & (1<<bit):remainder ^= 0x1d5 << (bit-8)
    return remainder

def camera_measurement(words,protocol):
    w=protocol['words']
    d={k[7:].lower():words[n] for k,n in w.items() if k.startswith('CAMERA_') and k not in ('CAMERA_RAW','CAMERA_PACKET')}
    d['raw_hex']=struct.pack('<8I',*words[w['CAMERA_RAW']:w['CAMERA_RAW']+8])[:d['raw_length']].hex()
    d['response_hex']=struct.pack('<2I',*words[w['CAMERA_PACKET']:w['CAMERA_PACKET']+2])[:d['valid_length']].hex()
    d['kind']='one_boot_query; repeated mailbox samples are not repeated UART tests'
    return d

def camera_checks(words,manifest,live):
    d=camera_measurement(words,manifest['protocol']);checks=[]
    def add(code,status,evidence,next_step=''):checks.append((code,status,evidence,next_step))
    enabled=int(manifest['build_options']['camera_query'])
    mode_ok=d['mode']==enabled
    add('CAMERA_MODE','PASS' if mode_ok else 'FAIL',f"build mode={enabled}, reported={d['mode']}")
    off=d['oe_readback']==0
    add('CAMERA_OUTPUT_DISABLED','INFO' if off else 'FAIL',f"PC13 final digital readback={d['oe_readback']}",
        'Verify TP91 electrically; a GPIO bit is not an output-voltage measurement.')
    pwr=words[50]
    pwr_ok=pwr in (0,1) and pwr==d['power_readback'] and (enabled or pwr==0)
    add('CAMERA_POWER_COMMAND','INFO' if pwr_ok else 'FAIL',f"PD3 current={pwr}, query-end={d['power_readback']}",
        'Enabled query mode leaves power ON to avoid interrupting an SD write. Measure TP72/90; software cannot prove those supplies are present.')
    response=bytes.fromhex(d['response_hex'])
    raw=bytes.fromhex(d['raw_hex'])
    # The C transaction returns immediately after the valid response; when
    # the entire stream fits in the raw prefix, its tail must be that response.
    stream_ok=d['rx_count']>32 or raw[-5:]==response
    cw=manifest['protocol']['words']
    query_delay=(d['query_ms']-d['start_ms'])%2**32
    sequence_end=words[cw['TEST_FINISHED_MS']]
    time_ok=(3000<=query_delay<0x80000000
      and (d['finished_ms']-d['query_ms'])%2**32<=1100
      and (sequence_end-d['finished_ms'])%2**32<0x80000000
      and (words[cw['UPTIME_MS']]-sequence_end)%2**32<0x80000000)
    frame_ok=(len(response)==5 and response[0]==0xcc and response[1]==1 and crc8(response[:4])==response[4]
      and d['protocol_version']==response[1] and d['features']==int.from_bytes(response[2:4],'little'))
    coherent=(mode_ok and enabled and off and pwr_ok and pwr==1 and d['error']==0 and d['error_flags']==0
      and d['kernel_hz']==64000000 and d['brr']==556 and d['tx_count']==3 and 5<=d['rx_count']<=256
      and d['raw_length']==min(d['rx_count'],32) and time_ok and frame_ok and stream_ok)
    status={0:'NOT_TESTED',1:'RUNNING',2:'PASS',3:'FAIL'}[d['status']]
    if status=='PASS' and not coherent:status='FAIL'
    if enabled and status=='NOT_TESTED' and live:status='FAIL'
    if not enabled and (status!='NOT_TESTED' or d['tx_count'] or d['rx_count'] or d['error']):status='FAIL'
    if status=='PASS' and not live:status='INCONCLUSIVE'
    errors={n:k for k,n in manifest['protocol']['camera']['errors'].items()}
    add('CAMERA_UART',status,f"error={errors.get(d['error'],'UNKNOWN')}, response={d['response_hex']}, tx/rx={d['tx_count']}/{d['rx_count']}, raw={d['raw_hex']}",
      'Check CAM_5V/TP72, CAM_IO_3V3/TP90, OE/TP91, U12/U13 and J9 TX/RX direction. No response also permits wrong camera mode/protocol or startup delay; it does not identify a failed IC.')
    add('CAMERA_RECEIVE_HISTORY','INCONCLUSIVE' if d['crc_errors'] or d['discarded'] else 'INFO',
      f"discarded={d['discarded']}, CRC-rejected candidates={d['crc_errors']}, USART error bits=0x{d['error_flags']:x}",
      'A later valid reply does not erase noise or stale traffic recorded earlier.')
    return checks
