"""Bounded R10 readback against synthetic DP/MCU bytes only. No probe access."""
import contextlib
import copy
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zlib

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diagnostics import r10_firmware as r
from m3_firmware.r10 import build
from m3_firmware.r10.decode import IMU_CONFIG_VALUES

BOARD=r.ROOT/"m3_design/assembly_review/m3.kicad_pcb"


def frame(build_id,ticks=1000,sequence=2,state=2,uid=(123,456,789)):
    words=[0]*128
    words[:10]=[int.from_bytes(b"R10D","little"),3,512,sequence,state,ticks,0,ticks,0x411fc271,0x20030450]
    words[10:13]=uid
    words[24:26]=[64000000,63999]
    words[28:36]=struct.unpack("<8I",bytes.fromhex(r.BOARD_SHA))
    words[36:44]=struct.unpack("<8I",bytes.fromhex(build_id))
    words[27]=1;words[44]=31
    words[127]=zlib.crc32(struct.pack("<127I",*words[:127]))
    return words


def bundle(folder):
    image=bytearray(704)
    struct.pack_into("<II",image,0,0x20020000,r.FLASH+665)
    binding,_=build.validate_inputs()
    inputs=dict(schema="r10-bench-build-inputs/v1",sources=build.source_inventory(),
                board_inputs=binding["inputs"],compiler="SYNTHETIC TEST FIXTURE 15.2.1",flags=build.FLAGS)
    identity=r.sha_bytes(build.canonical(inputs))
    manifest=dict(schema="r10-bench-build/v1",profile=r.PROFILE,board_sha256=r.BOARD_SHA,
                  build_id=identity,inputs=inputs,outputs={"r10_bench.bin":r.sha_bytes(image)},
                  mailbox_address=r.RAM,mailbox_bytes=512,mailbox_abi=3,barometer_driver_implemented=True,
                  sensor_drivers_implemented=True,actuation_implemented=False)
    (folder/"manifest.json").write_text(json.dumps(manifest))
    (folder/"image.bin").write_bytes(image)
    return bytes(image),identity


class DP:
    def __init__(self):self.writes=[]
    def write_ap(self,address,value):self.writes.append((address,value))
    def read_ap(self,address):return 0x04770001 if address==0xfc else 0


class FakeReader:
    def __init__(self,image,build_id,*,bad_image=False,wrong_family=False,ready=True,vtor=r.FLASH,
                 odd=False,torn=False,bad_uid=False,fault=False,read_error=None,close_error=False,open_error=False):
        self.image=image;self.guard=r.FirmwareAPGuard(DP());self.guard.write_ap(0,0x03000012)
        self.regs=dict(zip(r.REGS.values(),[0x411fc271,0x20030450,123,456,789,2048,0x2000,r.FLASH]))
        if wrong_family:self.regs[r.REGS["IDCODE"]]=0x483
        self.regs[r.REGS["PWR_CSR1"]]=0x2000 if ready else 0
        self.regs[r.REGS["VTOR"]]=vtor
        uid=(1,2,3) if bad_uid else (123,456,789)
        self.frames=[frame(build_id,1000,2,3 if fault else 2,uid),frame(build_id,2000,4,3 if fault else 2,uid)]
        self.bad_image=bad_image;self.odd=odd;self.torn=torn;self.read_error=read_error
        self.close_error=close_error;self.open_error=open_error;self.closed=False;self.ram_reads=0;self.seen=[]

    def open(self):
        if self.open_error:raise OSError("SYNTHETIC OPEN FAILURE")
        return {"kind":"SYNTHETIC_FIXTURE","not_hardware":True}

    def read32(self,address):
        self.guard.write_ap(4,address);self.seen.append(address)
        if address==self.read_error:raise OSError("SYNTHETIC READ FAILURE")
        if address in self.regs:return self.regs[address]
        if r.FLASH<=address<r.FLASH+len(self.image):
            v=struct.unpack_from("<I",self.image,address-r.FLASH)[0]
            return v^1 if self.bad_image and address==r.FLASH else v
        if r.RAM<=address<r.RAM+512:
            index=self.ram_reads;self.ram_reads+=1
            if self.odd:return 3
            value=self.frames[min(index//130,1)][(address-r.RAM)//4]
            return value+2 if self.torn and index%130==129 else value
        raise AssertionError("SYNTHETIC address escaped allowlist")

    def enable_image(self,c,d,size):self.guard.enable_image(c,d,size)
    enable_ram=r.FirmwareReader.enable_ram  # exercise the production adapter, not a permissive fake
    def close(self):
        self.closed=True
        if self.close_error:raise OSError("SYNTHETIC CLOSE FAILURE")


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.run=self.root/"run"
        self.image,self.identity=bundle(self.root)

    def prepare(self,origin="SYNTHETIC_FIXTURE"):
        return r.prepare(BOARD,self.root/"manifest.json",self.root/"image.bin",self.run,"SYNTHETIC-BOARD","FAKE-PROBE",
                         bench_isolated=True,reset_boot_confirmed=True,origin=origin)

    def receipt(self,req,code=0,timeout=False):
        r.write_new(self.run/"supervision.json",dict(schema="r10-firmware-supervision/v1",run_id=req["run_id"],
            request_sha256=r.sha_bytes(r.canonical(req)),worker_exit_code=code,worker_pid=12345,timed_out=timeout,
            error=None,completed_at=r.utc()))

    def capture(self,**kwargs):
        req=self.prepare();reader=FakeReader(self.image,self.identity,**kwargs)
        code=r.worker(self.run,BOARD,lambda _:reader,pause=lambda _:None)
        self.receipt(req,code)
        return reader,r.analyze(self.run,BOARD)

    def replace(self,name,obj):
        (self.run/name).write_text(json.dumps(obj))

    def seal(self):
        ex=r.document(self.run/"execution.json")
        ex["snapshot_sha256"]=r.sha_bytes((self.run/"snapshot.json").read_bytes())
        self.replace("execution.json",ex)

    def test_normal_paired_capture_is_not_hardware_qualification(self):
        reader,result=self.capture()
        self.assertTrue(reader.closed)
        self.assertEqual(result["state"],"PROGRESS_OBSERVED")
        self.assertTrue(result["complete_capture"])
        self.assertEqual(result["origin"],"SYNTHETIC_FIXTURE")
        for k in ("hardware_qualified","physical_board_identity_verified","reset_continuity_verified","flashed","fabrication_release"):
            self.assertIs(result[k],False)
        self.assertEqual(reader.ram_reads,260)

    def test_wrong_chip_stops_after_two_identity_registers(self):
        reader,result=self.capture(wrong_family=True)
        self.assertEqual(reader.seen,[r.REGS["CPUID"],r.REGS["IDCODE"]])
        self.assertFalse(result["complete_capture"])

    def test_supply_or_vtor_not_ready_stops_before_image_and_ram(self):
        for kwargs in ({"ready":False},{"vtor":0}):
            with self.subTest(kwargs=kwargs):
                run=self.run;self.run=self.root/("run"+str(kwargs))
                reader,result=self.capture(**kwargs)
                self.assertFalse(any(r.FLASH<=a<r.FLASH+len(self.image) or r.RAM<=a<r.RAM+512 for a in reader.seen))
                self.assertFalse(result["complete_capture"]);self.run=run

    def test_image_mismatch_preserves_partial_image_without_reading_ram(self):
        reader,result=self.capture(bad_image=True)
        self.assertEqual(len((self.run/"observed_image.bin").read_bytes()),4)
        self.assertEqual(reader.ram_reads,0)
        self.assertFalse(result["image_bytes_match"])

    def test_odd_generation_has_bounded_attempts(self):
        reader,result=self.capture(odd=True)
        self.assertEqual(reader.ram_reads,6)
        self.assertFalse(result["complete_capture"])

    def test_torn_sequences_never_count_as_a_complete_record(self):
        reader,result=self.capture(torn=True)
        self.assertEqual(reader.ram_reads,780)
        self.assertFalse(result["complete_capture"])

    def test_record_uid_disagreeing_with_chip_is_rejected(self):
        _,result=self.capture(bad_uid=True)
        self.assertFalse(result["complete_capture"])
        self.assertEqual(result["records"],[None,None])

    def test_terminal_fault_is_reported_as_fault_and_not_live_progress(self):
        _,result=self.capture(fault=True)
        self.assertEqual(result["state"],"FAULT_RECORDED")
        self.assertFalse(result["progress"]["observed_progress"])

    def test_read_and_close_failures_keep_raw_evidence(self):
        for name,kwargs in (("read",{"read_error":r.RAM+24}),("close",{"close_error":True}),("open",{"open_error":True})):
            with self.subTest(name=name):
                self.run=self.root/name
                reader,result=self.capture(**kwargs)
                self.assertTrue(reader.closed);self.assertFalse(result["complete_capture"])
                self.assertTrue((self.run/"snapshot.json").is_file())

    def test_wrong_board_and_missing_reset_declaration_fail_before_probe(self):
        bad=self.root/"badboard";bad.write_text("wrong board")
        with self.assertRaises(ValueError):r.prepare(bad,self.root/"manifest.json",self.root/"image.bin",self.run,"A","P",bench_isolated=True,reset_boot_confirmed=True)
        with self.assertRaises(ValueError):r.prepare(BOARD,self.root/"manifest.json",self.root/"image.bin",self.run,"A","P",bench_isolated=True,reset_boot_confirmed=False)
        self.assertFalse(self.run.exists())

    def test_synthetic_origin_never_defaults_to_real_probe(self):
        self.prepare()
        with mock.patch.object(r,"FirmwareReader") as factory:
            with self.assertRaisesRegex(ValueError,"explicit synthetic"):r.worker(self.run,BOARD)
            factory.assert_not_called()

    def test_bundle_drift_rejected_before_reader_construction(self):
        self.prepare();(self.run/"expected_image.bin").write_bytes(b"wrong")
        with mock.patch.object(r,"FirmwareReader") as factory:
            with self.assertRaises(ValueError):r.worker(self.run,BOARD,reader_factory=factory)
            factory.assert_not_called()

    def test_worker_source_drift_rejected_before_reader_construction(self):
        self.prepare()
        with mock.patch.object(r,"sources",return_value={}) as _,mock.patch.object(r,"FirmwareReader") as factory:
            with self.assertRaises(ValueError):r.worker(self.run,BOARD,reader_factory=factory)
            factory.assert_not_called()

    def test_raw_snapshot_mutation_is_not_replayed_as_evidence(self):
        self.capture();raw=r.document(self.run/"snapshot.json");raw["error"]="edited";self.replace("snapshot.json",raw)
        with self.assertRaisesRegex(ValueError,"changed after execution"):r.analyze(self.run,BOARD)

    def test_missing_receipt_or_timeout_retains_records_but_is_incomplete(self):
        self.capture();(self.run/"supervision.json").unlink()
        result=r.analyze(self.run,BOARD)
        self.assertFalse(result["complete_capture"]);self.assertIsNotNone(result["records"][0])
        req=r.document(self.run/"request.json");self.receipt(req,timeout=True)
        self.assertFalse(r.analyze(self.run,BOARD)["complete_capture"])

    def test_incomplete_capture_retains_records_without_progress_verdict(self):
        for case in ("complete", "close_failure", "missing_supervision", "timeout"):
            with self.subTest(case=case):
                self.run=self.root/case
                req=self.prepare()
                reader=FakeReader(self.image,self.identity,close_error=(case=="close_failure"))
                for index,words in enumerate(reader.frames):
                    words[45]=4  # Scripted READY sensor, not a physical reading.
                    words[47]=(1<<24)|(15<<16)|(15<<8)|0x73
                    words[48]=56+index
                    words[49]=words[5]-20
                    words[56:58]=struct.unpack("<2I",bytes(IMU_CONFIG_VALUES))
                    words[59]=1000000
                    words[127]=zlib.crc32(struct.pack("<127I",*words[:127]))
                code=r.worker(self.run,BOARD,lambda _:reader,pause=lambda _:None)
                if case!="missing_supervision":
                    self.receipt(req,code,timeout=(case=="timeout"))
                original=(self.run/"snapshot.json").read_bytes()
                result=r.report(self.run,BOARD,self.root/(case+"-report"))
                self.assertEqual((self.run/"snapshot.json").read_bytes(),original)
                self.assertEqual([rec["imu"]["samples"] for rec in result["records"]],[56,57])
                self.assertTrue(all(rec["imu"]["fresh"] for rec in result["records"]))
                self.assertFalse(result["hardware_qualified"])
                if case=="complete":
                    self.assertTrue(result["complete_capture"])
                    self.assertTrue(result["progress"]["imu_progress"]["reported_acquisition_progress"])
                    self.assertEqual(result["state"],"PROGRESS_OBSERVED")
                else:
                    self.assertFalse(result["complete_capture"])
                    self.assertEqual(result["state"],"INCOMPLETE")
                    self.assertIsNone(result["progress"])
                    self.assertIn("不确认主循环或传感器采集进度",
                                  (self.root/(case+"-report")/"report.md").read_text())

    def test_reversed_sample_chronology_cannot_report_progress(self):
        self.capture();raw=r.document(self.run/"snapshot.json")
        a,b=[group["attempts"][0] for group in raw["records"]]
        a["started_at"],b["started_at"]=b["started_at"],a["started_at"]
        a["finished_at"],b["finished_at"]=b["finished_at"],a["finished_at"]
        self.replace("snapshot.json",raw);self.seal()
        result=r.analyze(self.run,BOARD)
        self.assertFalse(result["temporal_coherence"])
        self.assertFalse(result["complete_capture"])
        self.assertIsNone(result["progress"])
        self.assertIsNotNone(result["records"][0])

    def test_incomplete_capture_still_rejects_disagreeing_record_pair(self):
        req=self.prepare();reader=FakeReader(self.image,self.identity,close_error=True)
        second=reader.frames[1]
        second[14]=8  # Coherent HSI /2 record; disagrees with the first record.
        second[24]=32000000
        second[25]=31999
        second[127]=zlib.crc32(struct.pack("<127I",*second[:127]))
        code=r.worker(self.run,BOARD,lambda _:reader,pause=lambda _:None)
        self.receipt(req,code)
        snapshot=r.document(self.run/"snapshot.json")
        self.assertTrue(all(g["accepted"] is not None for g in snapshot["records"]))
        self.assertEqual(code,3)
        with self.assertRaisesRegex(ValueError,"Paired records disagree on core_hz_nominal"):
            r.analyze(self.run,BOARD)

    def test_cleanup_error_remains_in_json_and_human_report(self):
        self.capture(close_error=True)
        result=r.report(self.run,BOARD,self.root/"analysis")
        self.assertIn("SYNTHETIC CLOSE FAILURE",result["cleanup_error"])
        self.assertIn("SYNTHETIC CLOSE FAILURE",result["error"])
        self.assertIn("连接清理失败",(self.root/"analysis/report.md").read_text())

    def test_sensor_fields_reach_saved_json_and_human_report(self):
        self.capture()
        result=r.report(self.run,BOARD,self.root/"analysis")
        self.assertEqual(result["records"][0]["imu"]["state"],"OFF")
        self.assertFalse(result["records"][0]["imu"]["fresh"])
        text=(self.root/"analysis/report.md").read_text()
        self.assertIn("IMU U4：OFF",text)
        self.assertIn("未校准",text)
        self.assertIn("气压计 U5：OFF",text)

    def test_current_bundle_cannot_claim_old_or_missing_sensor_contract(self):
        manifest=(self.root/"manifest.json").read_bytes()
        r.build_bundle(manifest,self.image)
        for field,value in (("mailbox_abi",1),("sensor_drivers_implemented",False)):
            changed=json.loads(manifest);changed[field]=value
            with self.assertRaises(ValueError):r.build_bundle(json.dumps(changed).encode(),self.image)
            # Historical replay still relies on its exact stored image/inputs,
            # not today's source inventory or ABI declaration.
            if field=="mailbox_abi":changed["mailbox_bytes"]=256
            r.build_bundle(json.dumps(changed).encode(),self.image,current=False)

    def test_old_abi_record_rejected_under_current_image_contract(self):
        req=self.prepare();reader=FakeReader(self.image,self.identity)
        for words in reader.frames:
            words[1]=1;words[27]=0;words[44]=7
            words[127]=zlib.crc32(struct.pack("<127I",*words[:127]))
        code=r.worker(self.run,BOARD,lambda _:reader,pause=lambda _:None)
        self.receipt(req,code)
        result=r.analyze(self.run,BOARD)
        self.assertEqual((code,result["state"]),(3,"INCOMPLETE"))
        self.assertFalse(result["complete_capture"])
        attempts=r.document(self.run/"snapshot.json")["records"][0]["attempts"]
        self.assertTrue(all("ABI" in attempt["error"] for attempt in attempts))

    def test_record_window_metadata_requires_exact_integer_version_and_size(self):
        original=json.loads((self.root/"manifest.json").read_bytes())
        for key,value in (("mailbox_abi",3.0),("mailbox_bytes",512.0),("mailbox_bytes",1024),
                          ("mailbox_address",float(r.RAM))):
            changed=dict(original);changed[key]=value
            with self.assertRaises(ValueError):r.build_bundle(json.dumps(changed).encode(),self.image,current=False)

    def test_timeout_report_preserves_unreaped_pid_and_reconnect_instruction(self):
        self.capture();sup=r.document(self.run/"supervision.json")
        sup.update(worker_exit_code=None,timed_out=True,error="Worker unreaped",completed_at=r.utc())
        self.replace("supervision.json",sup)
        result=r.report(self.run,BOARD,self.root/"analysis")
        self.assertEqual(result["worker_status"],"UNREAPED")
        self.assertEqual(result["supervision"]["worker_pid"],12345)
        self.assertIn("Worker unreaped",result["error"])
        self.assertIn("不要重复连接",(self.root/"analysis/report.md").read_text())
        self.assertFalse(result["complete_capture"])

    def test_bad_receipt_shape_bool_exit_and_future_clock_are_not_passes(self):
        self.capture();old=r.document(self.run/"execution.json")
        for val in (None,[],42):
            self.replace("execution.json",val)
            with self.assertRaises(ValueError):r.analyze(self.run,BOARD)
        value=copy.deepcopy(old);value["worker_exit_code"]=False;self.replace("execution.json",value)
        with self.assertRaises(ValueError):r.analyze(self.run,BOARD)
        value=copy.deepcopy(old);value["completed_at"]="2099-01-01T00:00:00+00:00";self.replace("execution.json",value)
        result=r.analyze(self.run,BOARD)
        self.assertFalse(result["complete_capture"]);self.assertFalse(result["temporal_coherence"])

    def test_supply_is_rechecked_after_image_before_ram(self):
        req=self.prepare();reader=FakeReader(self.image,self.identity)
        original=reader.read32
        def read(address):
            if address==r.REGS["PWR_CSR1"] and r.FLASH+len(self.image)-4 in reader.seen:
                reader.regs[address]=0
            return original(address)
        reader.read32=read
        code=r.worker(self.run,BOARD,lambda _:reader,pause=lambda _:None);self.receipt(req,code)
        result=r.analyze(self.run,BOARD)
        self.assertEqual(reader.ram_reads,0);self.assertFalse(result["complete_capture"])
        self.assertTrue(result["image_bytes_match"])

    def test_live_driver_schema_requires_exact_pinned_metadata(self):
        req=self.prepare(origin="SWD_CAPTURE");reader=FakeReader(self.image,self.identity)
        driver=dict(probe_id="FAKE-PROBE",pyocd_version=r.PY_OCD_VERSION,target_init_executed=False,
                    probe_description="SYNTHETIC LIVE-SCHEMA TEST",dpidr="0x2ba01477",frequency_hz=100000,
                    driver_sources={n:"a"*64 for n in ("dap.py","minimal_mem_ap.py","fake_probe.py")})
        reader.open=lambda:copy.deepcopy(driver)
        code=r.worker(self.run,BOARD,lambda _:reader,pause=lambda _:None);self.receipt(req,code)
        self.assertTrue(r.analyze(self.run,BOARD)["complete_capture"])
        original=r.document(self.run/"snapshot.json")
        for change in (dict(target_init_executed=True),dict(pyocd_version="0.44.0"),dict(frequency_hz=True),
                       dict(origin="SYNTHETIC_FIXTURE"),dict(driver_sources={}),dict(dpidr="wrong")):
            raw=copy.deepcopy(original);raw["driver"].update(change);self.replace("snapshot.json",raw);self.seal()
            with self.assertRaises(ValueError):r.analyze(self.run,BOARD)

    def test_malformed_accepted_index_and_forbidden_address_are_rejected(self):
        self.capture();original=r.document(self.run/"snapshot.json")
        for mutate in (lambda v:v["records"][0].update(accepted=True),
                       lambda v:v["records"][0]["attempts"][0]["words"].__setitem__(4,999),
                       lambda v:v["operations"].append(["AP_CONFIG_WRITE",12,1]),
                       lambda v:v["operations"].append(["AP_CONFIG_WRITE",4,r.RAM+512]),
                       lambda v:v["operations"].insert(3,["AP_CONFIG_WRITE",4,r.RAM]),
                       lambda v:v.update(operations=[])):
            raw=copy.deepcopy(original);mutate(raw);self.replace("snapshot.json",raw);self.seal()
            with self.assertRaises(ValueError):r.analyze(self.run,BOARD)

    def test_cli_report_synthetic_origin_and_no_overwrite(self):
        self.capture();out=self.root/"analysis"
        with contextlib.redirect_stdout(io.StringIO()):code=r.main(["report","--run",str(self.run),"--board",str(BOARD),"--out",str(out)])
        self.assertEqual(code,0);self.assertIn("SYNTHETIC_FIXTURE",(out/"report.md").read_text())
        with contextlib.redirect_stderr(io.StringIO()):code=r.main(["report","--run",str(self.run),"--board",str(BOARD),"--out",str(out)])
        self.assertEqual(code,3)


class GuardTests(unittest.TestCase):
    def test_production_reader_forwards_the_exact_versioned_record_window(self):
        reader=object.__new__(r.FirmwareReader);reader.guard=r.FirmwareAPGuard(DP())
        image=bytes(704);reader.enable_image(0x411fc271,0x20030450,len(image))
        reader.enable_ram(image,image,0x2000,r.FLASH,True,512)
        reader.guard.write_ap(4,r.RAM+508)
        with self.assertRaises(ValueError):reader.guard.write_ap(4,r.RAM+512)
        reader.enable_ram(image,image,0x2000,r.FLASH,True,256)
        with self.assertRaises(ValueError):reader.guard.write_ap(4,r.RAM+256)
        reader.guard.write_ap(4,r.RAM+252)
    def test_v3_exact_window_requires_image_grant_and_bad_revalidation_revokes_it(self):
        g=r.FirmwareAPGuard(DP());image=bytes(704)
        g.enable_image(0x411fc271,0x20030450,704)
        for address in (r.RAM,r.RAM+508):
            with self.assertRaises(ValueError):g.write_ap(4,address)
        g.enable_ram(image,image,0x2000,r.FLASH,True,512)
        g.write_ap(4,r.RAM+508)
        with self.assertRaises(ValueError):g.write_ap(4,r.RAM+512)
        with self.assertRaises(ValueError):g.enable_ram(image,image,0x2000,r.FLASH,True,1024)
        with self.assertRaises(ValueError):g.write_ap(4,r.RAM)
    def test_auto_increment_requires_fresh_tar_for_every_drw(self):
        class AutoDP(DP):
            def __init__(self):super().__init__();self.tar=0;self.reads=[]
            def write_ap(self,address,value):
                super().write_ap(address,value)
                if address==4:self.tar=value
            def read_ap(self,address):
                if address==0xfc:return super().read_ap(address)
                self.reads.append(self.tar);v=self.tar;self.tar+=4;return v
        dp=AutoDP();g=r.FirmwareAPGuard(dp);g.enable_image(0x411fc271,0x20030450,704)
        g.enable_ram(b"x"*704,b"x"*704,0x2000,r.FLASH,True)
        g.write_ap(4,r.RAM+252);self.assertEqual(g.read_ap(12),r.RAM+252)
        with self.assertRaises(ValueError):g.read_ap(12)
        self.assertEqual(dp.reads,[r.RAM+252])

    def test_addresses_and_data_writes_are_blocked_at_every_stage(self):
        g=r.FirmwareAPGuard(DP())
        with self.assertRaises(ValueError):g.read_ap(0x0c)
        bad=[(12,0),(16,0),(4,r.RAM),(4,r.FLASH),(4,0x58020018),(4,True),(0,0x23000052)]
        for a,v in bad:
            with self.assertRaises(ValueError):g.write_ap(a,v)
        g.enable_image(0x411fc271,0x20030450,704)
        g.write_ap(4,r.FLASH+700)
        for addr in (r.FLASH+704,r.FLASH-4,r.RAM,r.FLASH+1,0x90000000):
            with self.assertRaises(ValueError):g.write_ap(4,addr)
        g.enable_ram(b"x"*704,b"x"*704,0x2000,r.FLASH,True)
        g.write_ap(4,r.RAM+252)
        for addr in (r.RAM+256,r.RAM+512,r.RAM-4,r.RAM+1):
            with self.assertRaises(ValueError):g.write_ap(4,addr)
        with self.assertRaises(ValueError):g.write_ap(12,0x12345678)
        self.assertTrue(all(address in (0,4) for address,_ in g.dp.writes))

    def test_ap_identity_and_bad_value_fail_closed(self):
        for value in (0,True,None,0x100000000):
            dp=DP();dp.read_ap=lambda _:value
            g=r.FirmwareAPGuard(dp)
            with self.assertRaises(ValueError):g.read_ap(0xfc)
        dp=DP();g=r.FirmwareAPGuard(dp)
        with self.assertRaises(ValueError):g.read_ap(8)


class SupervisionTests(unittest.TestCase):
    setUp=CaptureTests.setUp
    prepare=CaptureTests.prepare
    def test_deadline_preserves_snapshot_and_records_unreaped_pid(self):
        req=self.prepare(origin="SWD_CAPTURE")
        sentinel=b'{"partial":"SYNTHETIC RAW"}\n';(self.run/"snapshot.json").write_bytes(sentinel)
        proc=mock.Mock(pid=4567)
        proc.wait.side_effect=[subprocess.TimeoutExpired("child",30),subprocess.TimeoutExpired("child",3),subprocess.TimeoutExpired("child",3)]
        factory=mock.Mock(return_value=proc)
        result=r.supervise(self.run,BOARD,popen=factory)
        command=factory.call_args.args[0]
        self.assertEqual(command[1:4],["-I","-B","-c"])
        self.assertEqual(command[5],str(r.ROOT))
        proc.terminate.assert_called_once();proc.kill.assert_called_once()
        self.assertIsNone(result["worker_exit_code"]);self.assertEqual(result["worker_pid"],4567)
        self.assertEqual((self.run/"snapshot.json").read_bytes(),sentinel)

    def test_spawn_failure_is_supervision_evidence(self):
        self.prepare(origin="SWD_CAPTURE")
        result=r.supervise(self.run,BOARD,popen=mock.Mock(side_effect=OSError("synthetic exec refused")))
        self.assertEqual(result["worker_exit_code"],3)
        self.assertIn("synthetic exec refused",result["error"])
        self.assertFalse((self.run/"snapshot.json").exists())

    def test_failed_prerequisites_never_open_ram(self):
        for args in ((b"a"*704,b"b"*704,0x2000,r.FLASH,True),
                     (b"a"*704,b"a"*704,0,r.FLASH,True),
                     (b"a"*704,b"a"*704,0x2000,0,True),
                     (b"a"*704,b"a"*704,0x2000,r.FLASH,False)):
            g=r.FirmwareAPGuard(DP());g.enable_image(0x411fc271,0x20030450,704)
            with self.assertRaises(ValueError):g.enable_ram(*args)
            self.assertFalse(g.ram)

    def test_failed_revalidation_revokes_previous_grants_and_latched_tar(self):
        g=r.FirmwareAPGuard(DP());g.enable_image(0x411fc271,0x20030450,704)
        g.enable_ram(b"a"*704,b"a"*704,0x2000,r.FLASH,True);g.write_ap(4,r.RAM)
        with self.assertRaises(ValueError):g.enable_ram(b"a"*704,b"b"*704,0x2000,r.FLASH,True)
        with self.assertRaises(ValueError):g.write_ap(4,r.RAM)
        with self.assertRaises(ValueError):g.read_ap(0x0c)
        with self.assertRaises(ValueError):g.enable_image(0,0,704)
        with self.assertRaises(ValueError):g.write_ap(4,r.FLASH)


if __name__=="__main__":unittest.main()
