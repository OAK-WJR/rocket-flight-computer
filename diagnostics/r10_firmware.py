"""R10-only readback of the reviewed internal image and version-bound RAM record.

Does not install firmware or reset/halt the MCU. External loads must be isolated
and an operator must confirm reset boot into the installed image. The original
register-only and legacy R1 transport permissions are unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import time
import uuid

from m3_firmware.r10 import build as firmware_build
from m3_firmware.r10.decode import decode, pair
from .r10_swd import binding, write_new, sha_bytes
from .r10_offline import (BOARD_SHA, PROFILE, canonical, document, fields, identifier,
                          loads, regular_bytes, require, timestamp)
from .registers import CPUID_MASK, EXPECTED_CPUID, EXPECTED_FAMILY, PY_OCD_VERSION
from .transport import PyOCDReader, atomic_json, utc

ROOT = Path(__file__).resolve().parent.parent
FLASH = 0x08000000
RAM = 0x24000000
MAX_IMAGE = 65536
MAX_TRACE = 20000
REGS = dict(CPUID=0xe000ed00, IDCODE=0x5c001000,
            UID0=0x1ff1e800, UID1=0x1ff1e804, UID2=0x1ff1e808,
            FLASH_SIZE=0x1ff1e880, PWR_CSR1=0x58024804, VTOR=0xe000ed08,
            PWR_CSR1_AFTER_IMAGE=0x58024804, VTOR_AFTER_IMAGE=0xe000ed08)
SOURCES = ("diagnostics/r10_firmware.py", "diagnostics/r10_swd.py", "diagnostics/r10_offline.py",
           "diagnostics/r10_swd_binding.json", "diagnostics/r10_profile.json",
           "diagnostics/transport.py", "diagnostics/registers.py", "diagnostics/engine.py",
           "m3_firmware/r10/decode.py", "m3_firmware/r10/build.py")
BOOTSTRAP = ("import sys; sys.path.insert(0,sys.argv.pop(1)); "
             "from diagnostics.r10_firmware import main; raise SystemExit(main())")


def sources():
    return {p:sha_bytes(regular_bytes(ROOT/p, 2_000_000)) for p in SOURCES}


def build_bundle(manifest_bytes, image, *, current=True):
    m = loads(manifest_bytes.decode("utf-8"))
    require(isinstance(m, dict) and m.get("schema") == "r10-bench-build/v1" and
            m.get("profile") == PROFILE and m.get("board_sha256") == BOARD_SHA, "Wrong R10 firmware manifest")
    inputs = m.get("inputs")
    fields(inputs, ("schema", "sources", "board_inputs", "compiler", "flags"))
    expected_id = hashlib.sha256(firmware_build.canonical(inputs)).hexdigest()
    require(inputs["schema"] == "r10-bench-build-inputs/v1" and expected_id == m.get("build_id"),
            "Firmware build identity mismatch")
    abi=m.get("mailbox_abi",1)
    require(type(abi) is int and abi in (1,2,3) and type(m.get("mailbox_address")) is int and
            type(m.get("mailbox_bytes")) is int and m.get("mailbox_address") == RAM and
            m.get("mailbox_bytes") == {1:256,2:256,3:512}[abi] and
            m.get("actuation_implemented") is False, "Wrong mailbox/function contract")
    require(isinstance(m.get("outputs"), dict) and m["outputs"].get("r10_bench.bin") == sha_bytes(image),
            "Local image changed since build")
    require(664 <= len(image) <= MAX_IMAGE and len(image) % 4 == 0, "Image exceeds fixed read window")
    sp, entry = struct.unpack_from("<II", image)
    require(sp == 0x20020000 and entry & 1 and FLASH <= entry & ~1 < FLASH+len(image), "Wrong image vector")
    if current:
        expected, _ = firmware_build.validate_inputs()
        require(m.get("mailbox_abi") == 3 and m.get("barometer_driver_implemented") is True and m.get("sensor_drivers_implemented") is True,
                "Current R10 image must declare the reviewed sensor diagnostic ABI")
        require(inputs["sources"] == firmware_build.source_inventory() and
                inputs["board_inputs"] == expected["inputs"] and inputs["flags"] == firmware_build.FLAGS,
                "Firmware source/binding changed; rebuild the reviewed image")
    return m


class FirmwareAPGuard:
    """Exact granted record window; never the legacy generic/QSPI permissions."""
    def __init__(self, dp):
        self.dp = dp
        self.operations = []
        self.family = False
        self.image_bytes = 0
        self.ram = False
        self.ram_bytes = 0
        self.current_address = None

    def enable_image(self, cpuid, idcode, size):
        self.family=False;self.image_bytes=0;self.ram=False;self.ram_bytes=0;self.current_address=None
        require(type(cpuid) is int and type(idcode) is int and
                cpuid & CPUID_MASK == EXPECTED_CPUID and idcode & 0xfff == EXPECTED_FAMILY,
                "Wrong chip; internal flash remains disabled")
        require(type(size) is int and 664 <= size <= MAX_IMAGE and size % 4 == 0, "Bad image window")
        self.family, self.image_bytes = True, size

    def enable_ram(self, observed, expected, power, vtor, reset_boot_confirmed, record_bytes=256):
        self.ram=False;self.ram_bytes=0;self.current_address=None
        require(self.family and len(observed) == self.image_bytes and observed == expected and
                type(power) is int and power & 0x2000 and vtor == FLASH and reset_boot_confirmed is True and
                type(record_bytes) is int and record_bytes in (256,512),
                "No verified image/reset-boot/supply/VTOR prerequisite; RAM disabled")
        self.ram = True;self.ram_bytes=record_bytes

    def write_ap(self, address, value):
        require(type(address) is int and type(value) is int, "AP arguments must be integers")
        csw = address == 0 and value == 0x03000012
        initial = value in (REGS["CPUID"], REGS["IDCODE"])
        register = self.family and value in REGS.values()
        flash = self.family and FLASH <= value < FLASH+self.image_bytes and value % 4 == 0
        ram = self.ram and RAM <= value < RAM+self.ram_bytes and value % 4 == 0
        require(csw or (address == 4 and (initial or register or flash or ram)), "Blocked AP write/address")
        require(len(self.operations) < MAX_TRACE, "AP operation budget exhausted")
        self.operations.append(["AP_CONFIG_WRITE", address, value])
        if address==4:self.current_address=None
        result=self.dp.write_ap(address,value)
        if address==4:self.current_address=value
        return result

    def read_ap(self, address):
        require(type(address) is int and address in (0xfc,0x0c), "Blocked AP read")
        if address==0x0c:
            require(self.current_address is not None,"No checked target address for data read")
            # CSW enables address increment. Consume this single word grant,
            # including on an error, so another DRW cannot advance past it.
            self.current_address=None
        value = self.dp.read_ap(address)
        require(type(value) is int and 0 <= value <= 0xffffffff, "Invalid AP result")
        if address == 0xfc:
            require(value & 0x0fffe00f == 0x04770001, "Wrong AP0 identity")
        return value


class FirmwareReader(PyOCDReader):
    def open(self):
        driver = super().open()  # pinned DP/AP-only attach; no target initialization
        from pyocd.coresight.minimal_mem_ap import MinimalMemAP
        self.guard = FirmwareAPGuard(self.dp)
        self.ap = MinimalMemAP(self.guard)
        self.ap.init()
        return driver

    def read32(self, address):
        return self.ap.read32(address)

    def enable_image(self, c, d, length):
        self.guard.enable_image(c,d,length)

    def enable_ram(self, observed, expected, power, vtor, reset_boot_confirmed,record_bytes=256):
        self.guard.enable_ram(observed,expected,power,vtor,reset_boot_confirmed,record_bytes)


def prepare(board, manifest, image, out, assembly, probe, *, bench_isolated,
            reset_boot_confirmed, origin="SWD_CAPTURE"):
    binding(board)
    require(bench_isolated is True and reset_boot_confirmed is True,
            "Isolated loads and operator-confirmed reset boot are required")
    require(origin in ("SWD_CAPTURE","SYNTHETIC_FIXTURE"), "Bad origin")
    identifier(assembly); identifier(probe)
    raw = regular_bytes(manifest,262144); binary = regular_bytes(image,MAX_IMAGE)
    m = build_bundle(raw,binary)
    out = Path(out); out.mkdir(mode=0o700,parents=True,exist_ok=False)
    with (out/"expected_image.bin").open("xb") as f:f.write(binary)
    with (out/"manifest.json").open("xb") as f:f.write(raw)
    req = dict(schema="r10-firmware-request/v1", profile=PROFILE, board_sha256=BOARD_SHA,
        build_id=m["build_id"], manifest_sha256=sha_bytes(raw), image_sha256=sha_bytes(binary),
        image_bytes=len(binary), run_id=str(uuid.uuid4()), assembly_id=assembly, probe_id=probe,
        bench_isolated=True, reset_boot_confirmed=True, origin=origin, created_at=utc(), tool_sources=sources())
    write_new(out/"request.json",req)
    return req


def request(run, board, *, current=False):
    binding(board)
    r = document(Path(run)/"request.json")
    fields(r,("schema","profile","board_sha256","build_id","manifest_sha256","image_sha256","image_bytes",
              "run_id","assembly_id","probe_id","bench_isolated","reset_boot_confirmed","origin","created_at","tool_sources"))
    require(r["schema"] == "r10-firmware-request/v1" and r["profile"] == PROFILE and r["board_sha256"] == BOARD_SHA,
            "Wrong R10 request")
    for k in ("run_id","assembly_id","probe_id"):identifier(r[k])
    timestamp(r["created_at"])
    require(r["origin"] in ("SWD_CAPTURE","SYNTHETIC_FIXTURE") and
            r["bench_isolated"] is True and r["reset_boot_confirmed"] is True, "Missing declared bench/reset prerequisite")
    raw = regular_bytes(Path(run)/"manifest.json",262144); image = regular_bytes(Path(run)/"expected_image.bin",MAX_IMAGE)
    m = build_bundle(raw,image,current=current)
    require(r["build_id"] == m["build_id"] and r["manifest_sha256"] == sha_bytes(raw) and
            r["image_sha256"] == sha_bytes(image) and type(r["image_bytes"]) is int and r["image_bytes"] == len(image),
            "Request bundle changed")
    fields(r["tool_sources"], SOURCES)
    require(all(isinstance(v,str) and len(v)==64 and set(v)<=set("0123456789abcdef") for v in r["tool_sources"].values()),
            "Bad source digest")
    if current:require(r["tool_sources"] == sources(), "Worker sources changed since request")
    return r, image


def worker(run, board, reader_factory=None, pause=time.sleep):
    run = Path(run); req,image = request(run,board,current=True)
    manifest=document(run/"manifest.json");abi=manifest.get("mailbox_abi",1);record_bytes=manifest["mailbox_bytes"]
    if reader_factory is None:
        require(req["origin"]=="SWD_CAPTURE","Synthetic requests require an explicit synthetic reader")
        reader_factory=FirmwareReader
    s = dict(schema="r10-firmware-snapshot/v1", run_id=req["run_id"], origin=req["origin"],
             started_at=utc(), finished_at=None, state="CONNECTING", driver=None, registers=[],
             image_words_read=0, image_sha256=None, records=[], error=None, close_error=None, operations=[])
    def save():atomic_json(run/"snapshot.json",s)
    save(); reader=reader_factory(req["probe_id"])
    def read(address):
        v=reader.read32(address)
        require(type(v) is int and 0<=v<=0xffffffff,"Invalid 32-bit target value")
        return v
    def reg(name):
        row={"name":name,"address":REGS[name],"value":None,"error":None}
        try:row["value"]=read(row["address"])
        except Exception as exc:row["error"]=type(exc).__name__+": "+str(exc);raise
        finally:s["registers"].append(row);save()
        return row["value"]
    try:
        s["driver"]=reader.open();s["state"]="IDENTITY";save()
        c,d=reg("CPUID"),reg("IDCODE")
        require(c&CPUID_MASK==EXPECTED_CPUID and d&0xfff==EXPECTED_FAMILY,"Wrong CPU/device family")
        reader.enable_image(c,d,len(image))
        uid=[reg(n) for n in ("UID0","UID1","UID2")]
        require(reg("FLASH_SIZE")&0xffff == 2048,"Wrong flash capacity")
        power,vtor=reg("PWR_CSR1"),reg("VTOR")
        require(power&0x2000 and vtor==FLASH,"Supply/VTOR not ready; no SRAM read attempted")
        s["state"]="IMAGE_VERIFY";save()
        with (run/"observed_image.bin").open("xb",buffering=0) as observed:
            for offset in range(0,len(image),4):
                data=struct.pack("<I",read(FLASH+offset));observed.write(data)
                s["image_words_read"]+=1
                require(data==image[offset:offset+4],"Installed image differs at offset 0x%x" % offset)
                if offset%256==0:save()
        actual=regular_bytes(run/"observed_image.bin",MAX_IMAGE)
        s["image_sha256"]=sha_bytes(actual)
        power,vtor=reg("PWR_CSR1_AFTER_IMAGE"),reg("VTOR_AFTER_IMAGE")
        reader.enable_ram(actual,image,power,vtor,req["reset_boot_confirmed"],record_bytes)
        s["state"]="MAILBOX";save()
        for sample in range(2):
            attempts=[];s["records"].append({"sample":sample,"attempts":attempts,"accepted":None})
            for _ in range(3):
                a={"started_at":utc(),"before":None,"words":[],"after":None,"error":None}
                attempts.append(a);save()
                try:
                    a["before"]=read(RAM+12)
                    require(a["before"]!=0 and a["before"]%2==0,"No committed sequence yet")
                    for i in range(record_bytes//4):a["words"].append(read(RAM+4*i));save()
                    a["after"]=read(RAM+12)
                    require(a["before"]==a["after"]==a["words"][3],"Mailbox changed during read")
                    payload=struct.pack("<%dI"%(record_bytes//4),*a["words"])
                    decoded=decode(payload,BOARD_SHA,req["build_id"])
                    require(decoded["abi_version"]==abi,"Record ABI disagrees with verified image")
                    require(decoded["uid_words"]==uid and decoded["cpuid"]=="%08x"%c and decoded["idcode"]=="%08x"%d,
                            "Record identity disagrees with chip registers")
                except ValueError as exc:a["error"]=str(exc)
                finally:a["finished_at"]=utc();save()
                if a["error"] is None:
                    s["records"][-1]["accepted"]=len(attempts)-1;save();break
                pause(0.02)
            if sample==0:pause(1.1)
        s["state"]="CAPTURED" if all(r["accepted"] is not None for r in s["records"]) else "INCOMPLETE"
        if s["state"]!="CAPTURED":s["error"]="No coherent record within the bounded attempt budget"
    except Exception as exc:
        s["error"]=type(exc).__name__+": "+str(exc);s["state"]="INCOMPLETE"
    finally:
        try:reader.close()
        except Exception as exc:s["close_error"]=type(exc).__name__+": "+str(exc);s["state"]="INCOMPLETE"
        s["operations"]=list(reader.guard.operations) if getattr(reader,"guard",None) is not None else []
        s["finished_at"]=utc();save()
    code=0 if s["state"]=="CAPTURED" and all(x["accepted"] is not None for x in s["records"]) else 3
    write_new(run/"execution.json",dict(schema="r10-firmware-execution/v1",run_id=req["run_id"],
        request_sha256=sha_bytes(canonical(req)),snapshot_sha256=sha_bytes(regular_bytes(run/"snapshot.json",4_000_000)),
        worker_exit_code=code,completed_at=utc()))
    return code


def supervise(run,board,*,popen=subprocess.Popen,timeout=30):
    run=Path(run);req,_=request(run,board,current=True)
    require(req["origin"]=="SWD_CAPTURE","CLI requires live origin")
    command=[sys.executable,"-I","-B","-c",BOOTSTRAP,str(ROOT),"_worker","--run",str(run.resolve()),"--board",str(Path(board).resolve())]
    timed_out=False;error=None;pid=None
    with (run/"driver.log").open("x") as log:
        try:proc=popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        except OSError as exc:code=3;error=type(exc).__name__+": "+str(exc)
        else:
            pid=proc.pid
            try:code=proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out=True;proc.terminate()
                try:code=proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    try:code=proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:code=None;error="Worker unreaped; inspect PID before reconnecting"
    result=dict(schema="r10-firmware-supervision/v1",run_id=req["run_id"],request_sha256=sha_bytes(canonical(req)),
                worker_exit_code=code,worker_pid=pid,timed_out=timed_out,error=error,completed_at=utc())
    write_new(run/"supervision.json",result)
    return result


def analyze(run,board):
    run=Path(run);req,image=request(run,board)
    manifest=document(run/"manifest.json");abi=manifest.get("mailbox_abi",1);record_bytes=manifest["mailbox_bytes"]
    path=run/"snapshot.json"
    payload=regular_bytes(path,4_000_000) if path.exists() else None
    s=loads(payload.decode("utf-8")) if payload is not None else None
    observed_path=run/"observed_image.bin"
    observed=regular_bytes(observed_path,MAX_IMAGE) if observed_path.exists() else b""
    complete=False;records=[];temporal=True;raw_hash=sha_bytes(payload) if payload is not None else None
    regs={};operations=[]
    if s is not None:
        fields(s,("schema","run_id","origin","started_at","finished_at","state","driver","registers",
                  "image_words_read","image_sha256","records","error","close_error","operations"))
        require(s["schema"]=="r10-firmware-snapshot/v1" and s["run_id"]==req["run_id"] and s["origin"]==req["origin"],"Wrong raw snapshot/run")
        start=timestamp(s["started_at"])
        temporal=timestamp(req["created_at"])<=start<=timestamp(utc())
        if s["finished_at"] is not None:
            temporal=temporal and start<=timestamp(s["finished_at"])<=timestamp(utc())
        else:temporal=False
        require(s["state"] in ("CONNECTING","IDENTITY","IMAGE_VERIFY","MAILBOX","CAPTURED","INCOMPLETE"),"Unknown state")
        for key in ("error","close_error"):
            require(s[key] is None or isinstance(s[key],str),"Bad error type")
        rows=s["registers"]
        require(isinstance(rows,list) and len(rows)<=len(REGS),"Bad register count")
        for row,name in zip(rows,REGS):
            fields(row,("name","address","value","error"))
            require(row["name"]==name and type(row["address"]) is int and row["address"]==REGS[name],"Register order/address changed")
            require((type(row["value"]) is int and 0<=row["value"]<=0xffffffff and row["error"] is None) or
                    (row["value"] is None and isinstance(row["error"],str)),"Bad register result")
            regs[name]=row["value"]
        family=(type(regs.get("CPUID")) is int and type(regs.get("IDCODE")) is int and
                regs["CPUID"]&CPUID_MASK==EXPECTED_CPUID and regs["IDCODE"]&0xfff==EXPECTED_FAMILY)
        require(family or len(rows)<=2,"Family-specific reads before identity")
        require(type(s["image_words_read"]) is int and 0<=s["image_words_read"]<=len(image)//4 and
                s["image_words_read"]*4<=len(observed),"Bad partial image evidence")
        if s["image_sha256"] is not None:
            require(s["image_sha256"]==sha_bytes(observed) and observed==image,"Image verification contradicts preserved bytes")
        image_ok=observed==image and s["image_sha256"]==req["image_sha256"]
        operations=s["operations"]
        require(isinstance(operations,list) and len(operations)<=MAX_TRACE,"Trace too large")
        seen=set()
        flash_addresses=set(range(FLASH,FLASH+len(image),4))
        configured=False;post_power=False;post_vtor=False
        for op in operations:
            require(isinstance(op,list) and len(op)==3 and op[0]=="AP_CONFIG_WRITE" and
                    type(op[1]) is int and type(op[2]) is int,"Bad trace row")
            address,value=op[1:]
            allowed=(address==0 and value==0x03000012) or (address==4 and
                     (value in (REGS["CPUID"],REGS["IDCODE"]) or
                      (family and (value in REGS.values() or FLASH<=value<FLASH+len(image) and value%4==0)) or
                      (image_ok and RAM<=value<RAM+record_bytes and value%4==0)))
            require(allowed,"Forbidden target write or address in trace")
            if address==0:configured=True
            if address==4:
                require(configured,"Target read before checked AP configuration")
                if value not in (REGS["CPUID"],REGS["IDCODE"]):
                    require({REGS["CPUID"],REGS["IDCODE"]}<=seen,"Family-specific read before identity trace")
                if RAM<=value<RAM+record_bytes:
                    require(flash_addresses<=seen and post_power and post_vtor,"RAM read precedes full image/post-image prerequisites")
                if flash_addresses<=seen:
                    if value==REGS["PWR_CSR1"]:post_power=True
                    if value==REGS["VTOR"]:post_vtor=True
                seen.add(value)
        if req["origin"]=="SWD_CAPTURE" and (s["driver"] is not None or rows):
            d=s["driver"]
            fields(d,("probe_id","pyocd_version","target_init_executed","probe_description","dpidr","frequency_hz","driver_sources"))
            require(d["probe_id"]==req["probe_id"] and d["pyocd_version"]==PY_OCD_VERSION and
                    d["target_init_executed"] is False and type(d["frequency_hz"]) is int and d["frequency_hz"]==100000 and
                    isinstance(d["probe_description"],str),"Wrong live driver identity/options")
            require(isinstance(d["dpidr"],str) and len(d["dpidr"])==10 and d["dpidr"].startswith("0x") and
                    set(d["dpidr"][2:])<=set("0123456789abcdef"),"Bad DPIDR")
            ds=d["driver_sources"]
            require(isinstance(ds,dict) and len(ds)==3 and {"dap.py","minimal_mem_ap.py"}<=ds.keys() and
                    all(isinstance(k,str) and "/" not in k and "\\" not in k and k.endswith(".py") and
                        isinstance(v,str) and len(v)==64 and set(v)<=set("0123456789abcdef") for k,v in ds.items()),"Bad driver source evidence")
        groups=s["records"]
        require(isinstance(groups,list) and len(groups)<=2,"Wrong mailbox sample count")
        previous_attempt_end=start
        for index,group in enumerate(groups):
            fields(group,("sample","attempts","accepted"))
            require(type(group["sample"]) is int and group["sample"]==index,"Wrong sample order")
            attempts=group["attempts"];accepted=group["accepted"]
            require(isinstance(attempts,list) and len(attempts)<=3 and
                    (accepted is None or type(accepted) is int and 0<=accepted<len(attempts)),"Bad bounded attempts")
            accepted_record=None
            for i,a in enumerate(attempts):
                fields(a,("started_at","before","words","after","error"),("finished_at",))
                require(isinstance(a["words"],list) and len(a["words"])<=record_bytes//4 and
                        all(type(w) is int and 0<=w<=0xffffffff for w in a["words"]),"Bad mailbox words")
                for key in ("before","after"):
                    require(a[key] is None or type(a[key]) is int and 0<=a[key]<=0xffffffff,"Bad sequence evidence")
                require(a["error"] is None or isinstance(a["error"],str),"Bad attempt error")
                a_start=timestamp(a["started_at"])
                temporal=temporal and previous_attempt_end<=a_start
                if "finished_at" in a:
                    a_end=timestamp(a["finished_at"])
                    temporal=temporal and start<=a_start<=a_end<=timestamp(s["finished_at"] or utc())
                    previous_attempt_end=a_end
                else:temporal=False
                if i==accepted:
                    require(image_ok and len(a["words"])==record_bytes//4 and a["error"] is None and
                            a["before"]==a["after"]==a["words"][3],"Accepted record lacks coherent sequence/image")
                    record=decode(struct.pack("<%dI"%(record_bytes//4),*a["words"]),BOARD_SHA,req["build_id"])
                    require(record["abi_version"]==abi,"Accepted record ABI differs from verified image")
                    require(record["uid_words"]==[regs.get(n) for n in ("UID0","UID1","UID2")] and
                            record["cpuid"]=="%08x"%regs["CPUID"] and record["idcode"]=="%08x"%regs["IDCODE"],
                            "Accepted record differs from measured chip identity")
                    accepted_record=record
            records.append(accepted_record)
        complete=(s["state"]=="CAPTURED" and s["error"] is None and s["close_error"] is None and family and
                  len(regs)==len(REGS) and all(v is not None for v in regs.values()) and
                  regs["PWR_CSR1"]&0x2000!=0 and regs["VTOR"]==FLASH and regs["FLASH_SIZE"]&0xffff==2048 and
                  regs["PWR_CSR1_AFTER_IMAGE"]&0x2000!=0 and regs["VTOR_AFTER_IMAGE"]==FLASH and
                  image_ok and len(records)==2 and all(r is not None for r in records))
        if complete:
            require(set(REGS.values())|set(range(FLASH,FLASH+len(image),4))|set(range(RAM,RAM+record_bytes,4))<=seen,
                    "Complete capture lacks required address trace")
    receipts=[];execution=None;supervision=None
    for name,schema in (("execution.json","r10-firmware-execution/v1"),("supervision.json","r10-firmware-supervision/v1")):
        path=run/name
        if not path.exists():complete=False;continue
        receipt=document(path)
        required=("schema","run_id","request_sha256","worker_exit_code","completed_at")
        required+=(("snapshot_sha256",) if name=="execution.json" else ("worker_pid","timed_out","error"))
        fields(receipt,required)
        require(receipt["schema"]==schema and receipt["run_id"]==req["run_id"] and
                receipt["request_sha256"]==sha_bytes(canonical(req)),"Wrong receipt/run")
        exit_code=receipt["worker_exit_code"]
        require(exit_code is None or type(exit_code) is int,"Bad worker exit code")
        if name=="execution.json":
            execution=receipt
            require(receipt["snapshot_sha256"]==raw_hash,"Raw snapshot changed after execution")
            require(type(exit_code) is int and exit_code in (0,3),"Bad execution exit code")
        else:
            supervision=receipt
            require(type(receipt["timed_out"]) is bool and
                    (receipt["error"] is None or isinstance(receipt["error"],str)) and
                    (receipt["worker_pid"] is None or type(receipt["worker_pid"]) is int and receipt["worker_pid"]>0),"Bad supervision")
            if receipt["timed_out"] or receipt["error"] is not None:complete=False
        t=timestamp(receipt["completed_at"])
        temporal=temporal and timestamp(req["created_at"])<=t<=timestamp(utc())
        if s is not None and s["finished_at"] is not None:temporal=temporal and timestamp(s["finished_at"])<=t
        receipts.append(receipt)
        if exit_code!=0:complete=False
    if len(receipts)==2:temporal=temporal and timestamp(receipts[0]["completed_at"])<=timestamp(receipts[1]["completed_at"])
    complete=bool(complete and temporal)
    # Still validate paired identities when capture/cleanup/receipts failed,
    # but expose a capture-level progress verdict only for complete evidence.
    paired=pair(*records) if temporal and len(records)==2 and all(r is not None for r in records) else None
    progress=paired if complete else None
    state="INCOMPLETE"
    if complete:
        state="FAULT_RECORDED" if any(r["state"]=="FAULT" for r in records) else (
               "PROGRESS_OBSERVED" if progress["observed_progress"] else "NO_PROGRESS_OBSERVED")
    capture_error=s["error"] if s else "No snapshot"
    cleanup_error=s["close_error"] if s else None
    supervision_error=supervision["error"] if supervision else None
    if supervision and supervision["timed_out"] and supervision_error is None:
        supervision_error="Worker deadline exceeded"
    error=capture_error or cleanup_error or supervision_error
    worker_status=("UNKNOWN" if supervision is None else "UNREAPED" if supervision["worker_exit_code"] is None and
                   supervision["worker_pid"] is not None else "EXITED" if type(supervision["worker_exit_code"]) is int else "UNKNOWN")
    return dict(schema="r10-firmware-report/v1",origin=req["origin"],run_id=req["run_id"],assembly_id=req["assembly_id"],
                state=state,complete_capture=complete,temporal_coherence=temporal,
                observed_image_sha256=sha_bytes(observed) if observed else None,
                image_bytes_match=observed==image,board_sha256_claim=BOARD_SHA,build_id=req["build_id"],
                records=records,progress=progress,raw_snapshot_sha256=raw_hash,error=error,
                capture_error=capture_error,cleanup_error=cleanup_error,supervision=supervision,execution=execution,
                worker_status=worker_status,
                acquisition_sources=req["tool_sources"],analysis_sources=sources(),
                reset_boot_operator_declared=req["reset_boot_confirmed"],reset_continuity_verified=False,
                hardware_qualified=False,physical_board_identity_verified=False,flashed=False,fabrication_release=False)


def report(run,board,out):
    result=analyze(run,board)
    out=Path(out);out.mkdir(mode=0o700,parents=True,exist_ok=False)
    write_new(out/"report.json",result)
    labels={"INCOMPLETE":"证据不完整，不能据此判断器件损坏",
            "PROGRESS_OBSERVED":"两次记录显示固件主循环在前进",
            "NO_PROGRESS_OBSERVED":"未观察到主循环前进；保留启动/时序/调试连接等可能性",
            "FAULT_RECORDED":"固件留下异常记录；查看异常号与故障寄存器"}
    text=("# R10 固件读回\n\n状态：%s — %s\n\n证据来源：%s\n\n" % (result["state"],labels[result["state"]],result["origin"]) +
          "板号：%s；构建：%s\n\n" % (result["assembly_id"],result["build_id"]) +
          "内部镜像字节一致：%s；捕获完整：%s。\n\n" % (result["image_bytes_match"],result["complete_capture"]) +
          "芯片 UID、固件绑定与记录完整性不等于整板鉴定。复位启动为操作者声明，未独立证明复位连续性。\n\n" +
          "实板资格、传感器、功率通路和制造放行均未通过此工具验证。\n")
    if result["error"]:text+="\n采集错误：%s\n"%result["error"]
    if result["cleanup_error"]:text+="\n连接清理失败：%s\n"%result["cleanup_error"]
    if result["supervision"]:
        sup=result["supervision"]
        text+="\n子进程 PID=%s，状态=%s，退出码=%s，超时=%s；监督错误：%s。\n"%(
            sup["worker_pid"],result["worker_status"],sup["worker_exit_code"],sup["timed_out"],sup["error"])
    if result["worker_status"]=="UNREAPED":
        text+="\n不要重复连接；先确认上述 PID 对应的子进程已经结束。\n"
    if not result["complete_capture"]:
        text+="\n以下为保留的记录字段；捕获不完整，不确认主循环或传感器采集进度。\n"
    for i,record in enumerate(result["records"]):
        if record is None:
            text+="\n记录 %d：没有通过序号、CRC 与身份校验的完整记录。\n"%(i+1)
        else:
            text+=("\n记录 %d：%s，序号 %d，标称运行 %d ms，主循环计数 %d，异常号 0x%08x。\n" %
                   (i+1,record["state"],record["sequence"],record["nominal_uptime_ms"],record["main_count"],record["exception"]))
            text+="\nCFSR=%s；HFSR=%s。MMFAR=%s（有效位 %s）；BFAR=%s（有效位 %s）。\n"%(
                record["faults_raw"]["CFSR"],record["faults_raw"]["HFSR"],record["faults_raw"]["MMFAR"],
                record["fault_address_valid"]["MMFAR"],record["faults_raw"]["BFAR"],record["fault_address_valid"]["BFAR"])
            imu=record.get("imu")
            if imu is None:
                text+="\n此为历史 v1 记录，没有 IMU 诊断字段。\n"
            else:
                text+=("\nIMU U4：%s（固件状态 %s），当前错误 %s，历史错误 %s。\n"%
                       (imu["effective_state"],imu["state"],imu["error"],imu["last_error"]))
                text+=("\n已采样：%s；样本计数 %d；标称数据年龄 %s ms；有效掩码 0x%x；端点掩码 0x%x。\n"%
                       (imu["has_sample"],imu["samples"],imu["nominal_sample_age_ms"],
                        imu["effective_valid_mask"],imu["endpoint_mask"]))
                text+=("\n配置读回匹配：%s；标称 SPI %d Hz；总线错误 %d；重初始化 %d；错误详情 0x%s。\n"%
                       (imu["config_matches_profile"],imu["nominal_bus_hz"],imu["bus_errors"],
                        imu["retries"],imu["bus_detail_raw"]))
                text+="\n原始计数（器件原生轴，未校准）：%s。\n"%json.dumps(imu["raw_counts"],sort_keys=True)
            baro=record.get("baro")
            if baro is None:
                text+="\n历史 ABI 没有气压计字段。\n"
            else:
                text+=("\n气压计 U5：%s，当前错误 %s，历史错误 %s；有效掩码 0x%x。\n"%
                       (baro["effective_state"],baro["error"],baro["last_error"],baro["effective_valid_mask"]))
                text+=("\n上次有效压力 %s Pa，温度 %s（0.01 °C）；自采集请求起标称年龄 %s ms；样本计数 %d。\n"%
                       (baro["pressure_pa"],baro["temp_centic"],baro["nominal_sample_age_ms"],baro["samples"]))
                text+=("\n校准读取掩码 0x%x，当前 PROM CRC %x/%x，校验有效 %s；事务错误 %d，重初始化 %d，详情 0x%s。\n"%
                       (baro["prom_word_mask"],baro["crc_calculated"],baro["crc_stored"],baro["prom_valid"],
                        baro["bus_errors"],baro["retries"],baro["bus_detail_raw"]))
                text+=("\n本次待完成原始值 D1=%d / D2=%d；上次有效值 D1=%d / D2=%d。\n"%
                       (baro["pending_d1"],baro["pending_d2"],baro["sample_d1"],baro["sample_d2"]))
                text+="\n当前校准原始字：%s；上次有效样本校准：%s。\n"%(baro["current_prom"],baro["sample_prom"])
    (out/"report.md").write_text(text)
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="cmd",required=True)
    c=sub.add_parser("capture");c.add_argument("--manifest",type=Path,required=True);c.add_argument("--image",type=Path,required=True)
    c.add_argument("--out",type=Path,required=True);c.add_argument("--assembly-id",required=True);c.add_argument("--probe-id",required=True)
    c.add_argument("--bench-isolated",action="store_true");c.add_argument("--reset-boot-confirmed",action="store_true")
    for name in ("capture","_worker","report"):
        parser=c if name=="capture" else sub.add_parser(name)
        parser.add_argument("--board",type=Path,required=True)
        if name!="capture":parser.add_argument("--run",type=Path,required=True)
        if name=="report":parser.add_argument("--out",type=Path,required=True)
    a=p.parse_args(argv)
    try:
        if a.cmd=="_worker":
            require(request(a.run,a.board,current=True)[0]["origin"]=="SWD_CAPTURE","Live worker requires live origin")
            return worker(a.run,a.board)
        if a.cmd=="report":
            r=report(a.run,a.board,a.out);print(json.dumps(r));return 0 if r["complete_capture"] else 3
        prepare(a.board,a.manifest,a.image,a.out,a.assembly_id,a.probe_id,
                bench_isolated=a.bench_isolated,reset_boot_confirmed=a.reset_boot_confirmed)
        supervise(a.out,a.board)
        r=report(a.out,a.board,a.out/"analysis");print(json.dumps(r));return 0 if r["complete_capture"] else 3
    except (ValueError,OSError,TypeError,KeyError,OverflowError,RecursionError) as exc:
        print("R10 firmware capture refused: "+str(exc),file=sys.stderr);return 3


if __name__=="__main__":raise SystemExit(main())
