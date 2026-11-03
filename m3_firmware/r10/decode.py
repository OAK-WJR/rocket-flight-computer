"""Decode saved R10 RAM bytes only. No probe, programmer or target connection."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import stat
import zlib

MAGIC = int.from_bytes(b"R10D", "little")
HEX = re.compile(r"[0-9a-f]{64}\Z")


IMU_STATES = ("OFF", "BOOT_WAIT", "RESET_WAIT", "WAIT_DATA", "READY", "STALE", "ERROR")
IMU_ERRORS = ("OK", "PORT", "ID", "RESET", "CONFIG_WRITE", "CONFIG_READ", "CONFIG_MISMATCH",
              "STATUS_READ", "DATA_READ", "NO_DATA")
IMU_RAW = ("gyro_x", "gyro_y", "gyro_z", "low_g_x", "low_g_y", "low_g_z",
           "high_g_x", "high_g_y", "high_g_z", "temperature")
IMU_CONFIG_MASKS = (0x7f, 0x7f, 0xc5, 7, 3, 0xff, 0x1d, 8)
IMU_CONFIG_VALUES = (6, 6, 0x44, 5, 3, 0x99, 1, 8)


def decode_imu(w):
    state, error = w[45:47]
    who, status, valid = w[47] & 255, w[47] >> 8 & 255, w[47] >> 16 & 255
    has_sample = bool(w[47] & (1 << 24))
    if (state >= len(IMU_STATES) or error >= len(IMU_ERRORS) or w[62] >= len(IMU_ERRORS) or
            w[47] & 0xfe000000 or valid & ~15 or w[50] & ~0x1ff):
        raise ValueError("Unsupported IMU state/flags/error")
    if state == 0 and any(w[45:63]):
        raise ValueError("OFF IMU record carries sensor claims")
    if state != 4 and valid:
        raise ValueError("IMU data validity contradicts sensor state")
    if state == 6 and error == 0 or state == 5 and error != 9:
        raise ValueError("IMU error contradicts sensor state")
    raw = struct.unpack("<10h", struct.pack("<5I", *w[51:56]))
    config = list(struct.pack("<2I", *w[56:58]))
    config_ok = all(c & m == v for c, m, v in zip(config, IMU_CONFIG_MASKS, IMU_CONFIG_VALUES))
    if state == 4 and (error or not has_sample or who != 0x73 or valid & 11 != 11 or
                       w[59] != 1000000 or not config_ok):
        raise ValueError("READY IMU record has inconsistent configuration/sample flags")
    # Age at publication can exceed the core's last poll age. Suppress freshness
    # here without losing a coherent diagnostic record or mislabelling old data.
    age = ((w[5] - w[49]) & 0xffffffff) if has_sample else None
    fresh = state == 4 and age is not None and age <= 250
    return dict(state=IMU_STATES[state], effective_state="STALE" if state == 4 and not fresh else IMU_STATES[state],
                error=IMU_ERRORS[error], last_error=IMU_ERRORS[w[62]], who_am_i="%02x" % who,
                status_raw="%02x" % status, reported_valid_mask=valid, effective_valid_mask=valid if fresh else 0,
                has_sample=has_sample, fresh=fresh, nominal_sample_age_ms=age,
                samples=w[48], last_good_tick_lo=w[49], endpoint_mask=w[50], raw_counts=dict(zip(IMU_RAW, raw)),
                config_raw=config, config_matches_profile=config_ok, bus_errors=w[58],
                nominal_bus_hz=w[59], bus_detail_raw="%08x" % w[60], retries=w[61],
                sensor_identity_authenticated=False, axes="native XYZ; no roll map or calibration",
                simultaneous_channels=False, hardware_qualified=False)


BARO_STATES=("OFF","POWER_WAIT","RESET_WAIT","PROM","WAIT_D1","WAIT_D2","READY","ERROR","COMMIT")
BARO_ERRORS=("OK","PORT","RESET","PROM_READ","PROM_EMPTY","PROM_CRC","CONVERT_D1","READ_D1",
             "CONVERT_D2","READ_D2","ADC_INVALID","RESULT_RANGE","PAIR_STALE")


def prom_crc4(prom):
    remainder=0
    for index in range(16):
        word=prom[index//2] & (0xff00 if index//2==7 else 0xffff)
        remainder^=word & 255 if index&1 else word>>8
        for _ in range(8):
            remainder=((remainder<<1)^(0x3000 if remainder&0x8000 else 0))&0xffff
    return remainder>>12


def compensate_ms5611(c,d1,d2):
    """Independent integer evaluation of B3 pp8-9, truncating toward zero."""
    div=lambda a,b:-(abs(a)//b) if a<0 else a//b
    dt=d2-c[5]*256
    temp=2000+div(dt*c[6],8388608)
    offset=c[2]*65536+div(c[4]*dt,128)
    sensitivity=c[1]*32768+div(c[3]*dt,256)
    if temp<2000:
        square=(temp-2000)**2
        off2=div(5*square,2);sens2=div(5*square,4)
        if temp<-1500:
            square=(temp+1500)**2;off2+=7*square;sens2+=div(11*square,2)
        temp-=div(dt*dt,2147483648)
        offset-=off2;sensitivity-=sens2
    return div(div(d1*sensitivity,2097152)-offset,32768),temp


def decode_baro(w):
    state,error=w[64:66];flags=w[66]
    valid=flags&3;has_sample=bool(flags&256);prom_valid=bool(flags&512)
    if (state>=len(BARO_STATES) or error>=len(BARO_ERRORS) or w[91]>=len(BARO_ERRORS) or
            flags&~0x303 or w[85]>255 or w[86]&~0x0f0f):
        raise ValueError("Unsupported barometer state/error/flags")
    if state==0 and any(w[64:98]):raise ValueError("OFF barometer carries sensor claims")
    if (state==7 and (not error or valid)) or (state!=7 and error):
        raise ValueError("Barometer error/validity contradicts phase")
    current=list(struct.unpack('<8H',struct.pack('<4I',*w[77:81])))
    sample=list(struct.unpack('<8H',struct.pack('<4I',*w[81:85])))
    nonempty=lambda p:not all(x==0 for x in p[1:7]) and not all(x==65535 for x in p[1:7])
    current_crc=prom_crc4(current)
    if prom_valid and (w[85]!=255 or not nonempty(current) or current_crc!=current[7]&15 or
                       (w[86]&15)!=current_crc or (w[86]>>8)!=current[7]&15):
        raise ValueError("Barometer PROM validity disagrees with raw calibration")
    signed=lambda v:v-0x100000000 if v&0x80000000 else v
    pressure,temp=signed(w[75]),signed(w[76])
    if has_sample and (not nonempty(sample) or prom_crc4(sample)!=sample[7]&15 or
                       not 0<w[73]<0xffffff or not 0<w[74]<0xffffff or
                       not 1000<=pressure<=120000 or not -4000<=temp<=8500):
        raise ValueError("Barometer last-good sample has inconsistent evidence")
    if has_sample and compensate_ms5611(sample,w[73],w[74])!=(pressure,temp):
        raise ValueError("Barometer compensated values disagree with raw last-good evidence")
    if valid and (valid!=3 or not has_sample or not prom_valid or state not in (4,5,6,8)):
        raise ValueError("Barometer reported validity contradicts sample/phase")
    if valid and current!=sample:raise ValueError("Fresh barometer pair uses a different PROM")
    age=((w[5]-w[97])&0xffffffff) if has_sample else None
    fresh=valid==3 and age is not None and age<=250
    return dict(state=BARO_STATES[state],error=BARO_ERRORS[error],last_error=BARO_ERRORS[w[91]],
                effective_state="STALE" if valid and not fresh else BARO_STATES[state],
                has_sample=has_sample,fresh=fresh,reported_valid_mask=valid,effective_valid_mask=valid if fresh else 0,
                samples=w[67],last_good_tick_lo=w[68],nominal_sample_age_ms=age,
                pressure_pa=pressure if has_sample else None,temp_centic=temp if has_sample else None,
                sample_d1=w[73],sample_d2=w[74],sample_d1_tick_lo=w[92],sample_d2_tick_lo=w[93],
                pending_d1=w[69],pending_d2=w[70],pending_d1_tick_lo=w[71],pending_d2_tick_lo=w[72],
                candidate_pressure_pa=signed(w[94]),candidate_temp_centic=signed(w[95]),
                pending_acquisition_tick_lo=w[96],sample_acquisition_tick_lo=w[97],
                current_prom=current,sample_prom=sample,prom_word_mask=w[85],prom_valid=prom_valid,
                crc_calculated=w[86]&15,crc_stored=w[86]>>8,bus_errors=w[87],nominal_bus_hz=w[88],
                bus_detail_raw='%08x'%w[89],retries=w[90],hardware_qualified=False,
                note="Compensated pair from sequential conversions; no altitude/control or physical calibration claim.")


def decode(raw, board_sha256, build_id):
    for value in (board_sha256, build_id):
        if not isinstance(value, str) or not HEX.fullmatch(value):
            raise ValueError("Expected a canonical SHA256 identity")
    if len(raw) not in (256,512):
        raise ValueError("R10 record must be exactly 256 (v1/v2) or 512 (v3) bytes")
    w = struct.unpack("<%dI"%(len(raw)//4), raw)
    if w[0] != MAGIC or w[1] not in (1,2,3) or w[2] != len(raw) or len(raw)!={1:256,2:256,3:512}[w[1]]:
        raise ValueError("Not a supported R10D ABI; legacy R1 records are incompatible")
    if w[3] == 0 or w[3] & 1:
        raise ValueError("Unpublished or in-progress record")
    if zlib.crc32(raw[:-4]) != w[-1]:
        raise ValueError("Torn or damaged record: CRC mismatch")
    if raw[112:144].hex() != board_sha256 or raw[144:176].hex() != build_id:
        raise ValueError("Record board/build identity mismatch")
    policy, caps = {1:(0,7),2:(1,15),3:(1,31)}[w[1]]
    if w[4] not in (1, 2, 3) or w[27] != policy or w[44] != caps or (w[1] == 1 and any(w[45:63])):
        raise ValueError("Unsupported state/capabilities/reserved fields")
    imu = decode_imu(w) if w[1] >= 2 else None
    baro = decode_baro(w) if w[1]==3 else None
    if w[1]==3 and (w[63] or any(w[98:127])):raise ValueError("Nonzero v3 reserved fields")
    if w[4] == 3 and imu is not None and imu["state"] != "OFF":
        raise ValueError("Core FAULT must withhold interrupted IMU state")
    if w[4]==3 and baro is not None and baro["state"]!="OFF":
        raise ValueError("Core FAULT must withhold interrupted barometer state")
    identity_consistent = ((w[8] >> 24) == 0x41 and (w[8] >> 4) & 0xfff == 0xc27 and w[9] & 0xfff == 0x450)
    clock_consistent = (w[24] == 64000000 >> ((w[14] >> 3) & 3) and w[15] & 0x38 == 0 and w[16] == 0)
    # Keep coherent FAULT evidence when the failure is precisely an unexpected
    # identity/clock. It must not be converted into a decoding exception/loss.
    if w[4] != 3 and not identity_consistent:
        raise ValueError("Unexpected CPU/device family")
    if w[4] != 3 and not clock_consistent:
        raise ValueError("Unexpected nominal HSI clock")
    if w[4] == 2 and (w[25] != w[24] // 1000 - 1 or w[26] != 0):
        raise ValueError("RUNNING record has inconsistent tick/fault state")
    if w[4] != 3 and (w[18] or w[19] or w[26]):
        raise ValueError("Fault evidence contradicts non-fault state")
    return {
        "schema": "r10-bench-record-report/v3", "abi_version": w[1], "imu": imu,"baro":baro,
        "state": {1:"STARTING", 2:"RUNNING", 3:"FAULT"}[w[4]],
        "sequence": w[3], "nominal_uptime_ms": w[5] | w[6] << 32,
        "main_count": w[7], "cpuid": "%08x" % w[8], "idcode": "%08x" % w[9],
        "uid_words": list(w[10:13]), "reset_flags_raw": "%08x" % w[13],
        "core_hz_nominal": w[24], "exception": w[26],
        "identity_consistent": identity_consistent, "clock_consistent": clock_consistent,
        "faults_raw": {k: "%08x" % w[i] for k,i in
                       (("CFSR",18),("HFSR",19),("DFSR",20),("MMFAR",21),("BFAR",22),("ICSR",23))},
        "fault_address_valid": {"MMFAR": bool(w[18] & (1 << 7)), "BFAR": bool(w[18] & (1 << 15))},
        "board_sha256_claim": board_sha256, "build_id_claim": build_id,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "physical_board_identity_verified": False, "hardware_qualified": False,
        "firmware_signature_verified": False,
        "note": "Self-reported build binding and CRC only; no hardware or sensor pass inferred."
    }


def pair(first, second):
    for name in ("abi_version", "cpuid", "idcode", "uid_words", "board_sha256_claim", "build_id_claim", "core_hz_nominal"):
        if first[name] != second[name]:
            raise ValueError("Paired records disagree on " + name)
    ticks = second["nominal_uptime_ms"] - first["nominal_uptime_ms"]
    loops = (second["main_count"] - first["main_count"]) & 0xffffffff
    seq = (second["sequence"] - first["sequence"]) & 0xffffffff
    advancing = (first["state"] == second["state"] == "RUNNING" and
                 ticks > 0 and 0 < loops < 0x80000000 and 0 < seq < 0x80000000)
    sensor_progress=None
    if first["imu"] is not None and second["imu"] is not None:
        a,b=first["imu"],second["imu"]
        samples=(b["samples"]-a["samples"])&0xffffffff
        sample_time=(b["last_good_tick_lo"]-a["last_good_tick_lo"])&0xffffffff
        sensor_progress=dict(reported_acquisition_progress=bool(advancing and a["fresh"] and b["fresh"] and
                             0<samples<0x80000000 and 0<sample_time<0x80000000),
                             sample_count_delta=samples,nominal_last_sample_delta_ms=sample_time,
                             hardware_qualified=False)
    barometer_progress=None
    if first["baro"] is not None and second["baro"] is not None:
        a,b=first["baro"],second["baro"]
        samples=(b["samples"]-a["samples"])&0xffffffff
        sample_time=(b["sample_acquisition_tick_lo"]-a["sample_acquisition_tick_lo"])&0xffffffff
        barometer_progress=dict(reported_acquisition_progress=bool(advancing and a["fresh"] and b["fresh"] and
                                0<samples<0x80000000 and 0<sample_time<0x80000000),
                                sample_count_delta=samples,nominal_acquisition_delta_ms=sample_time,hardware_qualified=False)
    return {"observed_progress": advancing, "nominal_elapsed_ms": ticks,
            "main_count_delta": loops, "imu_progress":sensor_progress,"baro_progress":barometer_progress, "hardware_qualified": False,
            "note": "Two saved records; capture timing, reset continuity and provenance are not verified here."}


def json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def read_bytes(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("Regular file required")
        with os.fdopen(fd, "rb", closefd=False) as f:
            raw = f.read(limit + 1)
    finally:
        os.close(fd)
    if len(raw) > limit:
        raise ValueError("Input exceeds fixed size limit")
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--second", type=Path)
    parser.add_argument("--manifest", type=Path, required=True, help="trusted local R10 build manifest")
    parser.add_argument("--board", type=Path, required=True)
    args = parser.parse_args()
    try:
        m = json.loads(read_bytes(args.manifest, 262144), object_pairs_hook=json_object,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
        if (not isinstance(m, dict) or m.get("schema") != "r10-bench-build/v1" or
                m.get("profile") != "M3-ASSY-R10" or not isinstance(m.get("inputs"), dict)):
            raise ValueError("Trusted R10 build manifest required")
        build_id = hashlib.sha256(json.dumps(m["inputs"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        board_sha = hashlib.sha256(read_bytes(args.board, 33554432)).hexdigest()
        if build_id != m.get("build_id") or board_sha != m.get("board_sha256"):
            raise ValueError("Manifest identity does not match its inputs or supplied board")
        first = decode(read_bytes(args.snapshot, 512), board_sha, build_id)
        if type(m.get("mailbox_abi",1)) is not int or first["abi_version"] != m.get("mailbox_abi",1):
            raise ValueError("Record ABI differs from trusted build manifest")
        result = {"record": first}
        if args.second:
            second = decode(read_bytes(args.second, 512), board_sha, build_id)
            result.update(second=second, pair=pair(first, second))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(3, "R10 decode refused: %s\n" % exc)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
