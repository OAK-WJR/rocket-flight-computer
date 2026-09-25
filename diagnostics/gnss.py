"""Independently decode raw UBX evidence. No GNSS configuration/control writes."""
import datetime
import struct

def measurement(words):
    from .mailbox import GNSS_PROTOCOL as p
    w=p['words'];r={n[5:].lower():words[i] for n,i in w.items() if n.startswith('GNSS_') and n not in ('GNSS_PVT','GNSS_VERSION')}
    raw=struct.pack('<23I',*words[207:230]);ver=struct.pack('<25I',*words[230:255])
    def text(a,b):return ver[a:b].split(b'\0',1)[0].decode('ascii',errors='replace')
    sw,hw,proto,model=text(0,30),text(30,40),text(40,70),text(70,100)
    known=(sw=='ROM SPG 5.10' or sw.startswith('ROM SPG 5.10 (')) and proto=='PROTVER=34.10' and model=='MOD=SAM-M10Q'
    tow,=struct.unpack_from('<I',raw);lon,lat,h,msl,ha,va=struct.unpack_from('<iiiiII',raw,24)
    epoch_age=(words[5]-r['epoch_ms'])&0xffffffff;pvt_age=(words[5]-r['pvt_ms'])&0xffffffff
    fresh=bool(r['flags']&32) and epoch_age<=3000 and pvt_age<=3000
    position=bool(r['flags']&4) and tow<604800000 and raw[20] in (2,3) and bool(raw[21]&1) and not(raw[78]&1) and abs(lat)<=900000000 and abs(lon)<=1800000000
    configured=r['kernel_hz']==64000000 and r['brr']==6667 and not r['error']
    accepted=known and fresh and position and configured and r['state']==5
    year,=struct.unpack_from('<H',raw,4);utc=None
    if r['flags']&4 and raw[11]&7==7:
        try:
            datetime.datetime(year,*raw[6:10],min(raw[10],59))
            if raw[10]<=60:utc=f'{year:04}-{raw[6]:02}-{raw[7]:02}T{raw[8]:02}:{raw[9]:02}:{raw[10]:02}Z'
        except ValueError:pass
    r.update(raw_pvt_hex=raw.hex(),selected_mon_ver_hex=ver.hex(),firmware=sw,hardware=hw,
      protocol=proto,model=model,identity_known=known,uart_settings_consistent=configured,epoch_age_ms=epoch_age,pvt_age_ms=pvt_age,
      fresh=fresh,position_flags_valid=position,location_accepted=accepted,receiver_itow_ms=tow,
      receiver_utc=utc,receiver_fix_type=raw[20],satellites=raw[23],
      latitude_deg=lat/1e7 if accepted else None,longitude_deg=lon/1e7 if accepted else None,
      height_ellipsoid_m=h/1000 if accepted else None,height_msl_m=msl/1000 if accepted else None,
      receiver_reported_horizontal_accuracy_m=ha/1000 if accepted else None,
      receiver_reported_vertical_accuracy_m=va/1000 if accepted else None,
      hardware_qualified=False,accuracy_measured=False)
    return r

def checks(samples,live):
    rows=[measurement(s['words']) for s in samples];a,b=rows[0],rows[-1]
    link=live and b['rx_bytes']>a['rx_bytes'] and b['ubx_good']>a['ubx_good'] and b['uart_settings_consistent']
    idok=b['identity_known'] and b['flags']&3==3
    result=[('GNSS_UART_CONFIG','PASS' if live and b['uart_settings_consistent'] else 'FAIL' if b['error'] else 'INCONCLUSIVE',
      f"reported kernel={b['kernel_hz']}Hz, BRR={b['brr']}, init error={b['error']}",
      'Register/configuration evidence is not a measurement of baud rate; verify PC6/PC7 with an instrument.'),
     ('GNSS_LINK','PASS' if link else 'INCONCLUSIVE',
      f"RX bytes {a['rx_bytes']}->{b['rx_bytes']}; UBX {b['ubx_good']}; NMEA {b['nmea_good']}; state/error {b['state']}/{b['error']}",
      'Check U6 3V3A, PC6/PC7, actual9600baud and cable/probe. Missing data does not identify a failed receiver by itself.'),
     ('GNSS_ID','PASS' if live and idok else 'INCONCLUSIVE',f"{b['firmware']}; {b['protocol']}; {b['model']}",
      'Unknown/missing MON-VER extensions remain raw evidence; do not apply the known-receiver decoder as a pass.'),
     ('GNSS_POSITION','PASS' if live and link and b['location_accepted'] else 'INCONCLUSIVE',
      f"fixType={b['receiver_fix_type']}, satellites={b['satellites']}, epoch_age={b['epoch_age_ms']}ms, accepted={b['location_accepted']}",
      'No fix indoors can be normal. Test under an open sky; this does not qualify accuracy or in-flight operation.'),
     ('GNSS_STREAM_HISTORY','INFO' if not b['history'] else 'FAIL',
      f"history=0x{b['history']:x}, discarded lower bound={b['dropped']}, bad checksum={b['bad_checksum']}, UART={b['uart_errors']}, TX errors={b['tx_errors']}",
      'Retain the capture. Check service gaps, UART clock/noise and incomplete packets before accepting a clean run.'),
     ('GNSS_RF_ACCURACY','NOT_TESTED','Receiver-reported accuracy is not independently measured error. Enclosure/antenna/RF performance is unqualified.','')]
    if any((x['history']&y['history'])!=x['history'] for x,y in zip(rows,rows[1:])):
        result.append(('GNSS_HISTORY_CLEARED','FAIL','GNSS error history cleared within one capture; possible reset or corruption.',''))
    return result,rows
