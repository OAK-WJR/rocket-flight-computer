"""Execute portable R10 C, verify corruption handling and reject wrong builds.
These are host tests, not target, sensor, power or physical-board tests.
"""
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zlib

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location("r10_"+name, HERE/(name+".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


build = load("build")
decoder = load("decode")


class Observation(ctypes.Structure):
    _fields_ = [(k, ctypes.c_uint32) for k in (
        "state ticks_lo ticks_hi main_count cpuid idcode uid0 uid1 uid2 reset_flags "
        "rcc_cr rcc_cfgr rcc_d1cfgr pwr_csr1 cfsr hfsr dfsr mmfar bfar icsr "
        "core_hz systick_load exception").split()]


class ActualC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        library = Path(cls.temp.name)/"r10.dylib"
        subprocess.run(["/usr/bin/clang", "-dynamiclib", "-O2", "-std=c11", "-Wall", "-Wextra", "-Werror",
                        "-I"+str(HERE/"imu"), "-I"+str(HERE/"vendor/ism6hg256x"),
                        "-I"+str(HERE/"baro"),"-I"+str(HERE/"voltage"),"-I"+str(HERE.parents[1]/"m3_firmware/src"),
                        str(HERE/"src/mailbox.c"), str(HERE/"imu/imu_frame.c"), str(HERE/"tests/imu_record.c"),
                        str(HERE/"tests/voltage_record.c"),str(HERE/"voltage/voltage_core.c"),
                        str(HERE/"voltage/adc_port.c"),str(HERE/"voltage/voltage_frame.c"),
                        str(HERE/"baro/baro_frame.c"),str(HERE.parents[1]/"m3_firmware/src/checks.c"),
                        "-o", str(library)], check=True, capture_output=True)
        cls.lib = ctypes.CDLL(str(library))
        u32p = ctypes.POINTER(ctypes.c_uint32)
        u8p = ctypes.POINTER(ctypes.c_uint8)
        cls.lib.r10_frame.argtypes = [u32p, ctypes.POINTER(Observation), u8p, u8p]
        cls.lib.r10_publish.argtypes = [u32p, u32p, u32p]
        cls.lib.r10_crc32.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        cls.lib.r10_crc32.restype = ctypes.c_uint32
        cls.lib.r10_test_sensor_record.argtypes = [u32p, ctypes.c_uint]
        cls.lib.r10_test_baro_record.argtypes=[u32p,ctypes.c_uint]
        cls.lib.r10_test_voltage_record.argtypes=[u32p,ctypes.c_uint]
        cls.lib.bench_ms5611.argtypes=[ctypes.POINTER(ctypes.c_uint16),ctypes.c_uint32,ctypes.c_uint32,
                                      ctypes.POINTER(ctypes.c_int32),ctypes.POINTER(ctypes.c_int32)]
        cls.board = "a0"*32; cls.identity = "17"*32

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def frame(self, ticks=10, count=10, sequence=0, state=2):
        obs = Observation(state=state, ticks_lo=ticks & 0xffffffff, ticks_hi=ticks >> 32,
                          main_count=count, cpuid=0x411fc271, idcode=0x20030450,
                          uid0=0x1234, uid1=0x5678, uid2=0x9abc,
                          core_hz=64000000, systick_load=63999)
        words = (ctypes.c_uint32*256)()
        dest = (ctypes.c_uint32*256)(*([0xdeadbeef]*256))
        bh = (ctypes.c_uint8*32).from_buffer_copy(bytes.fromhex(self.board))
        ih = (ctypes.c_uint8*32).from_buffer_copy(bytes.fromhex(self.identity))
        self.lib.r10_frame(words, ctypes.byref(obs), bh, ih)
        seq = ctypes.c_uint32(sequence)
        self.lib.r10_publish(dest, words, ctypes.byref(seq))
        self.assertEqual(bytes(dest), bytes(words))
        return bytes(dest)

    def decode(self, raw):
        return decoder.decode(raw, self.board, self.identity)

    def mutate(self, raw, index, value):
        words = list(struct.unpack("<%dI"%(len(raw)//4), raw)); words[index] = value
        payload = struct.pack("<%dI"%(len(words)-1), *words[:-1])
        return payload+struct.pack("<I", zlib.crc32(payload))

    def test_standard_crc_and_empty(self):
        for data in (b"", b"123456789", bytes(range(256)), b"\xff"*4096):
            self.assertEqual(self.lib.r10_crc32(data, len(data)), zlib.crc32(data))

    def test_actual_c_record_matches_independent_decoder(self):
        data = self.decode(self.frame())
        self.assertEqual((data["state"], data["sequence"], data["nominal_uptime_ms"], data["main_count"]),
                         ("RUNNING", 2, 10, 10))
        self.assertFalse(data["hardware_qualified"])
        self.assertFalse(data["physical_board_identity_verified"])

    def test_every_single_bit_corruption_is_rejected(self):
        raw = self.frame()
        for bit in range(len(raw)*8):
            damaged = bytearray(raw); damaged[bit//8] ^= 1 << (bit%8)
            with self.assertRaises(ValueError): self.decode(damaged)

    def test_randomized_real_c_publications(self):
        rng = random.Random(0x10)
        for _ in range(100):
            ticks = rng.randrange(1 << 56); loops = rng.randrange(1 << 32)
            raw = self.frame(ticks, loops)
            result = self.decode(raw)
            self.assertEqual((result["nominal_uptime_ms"], result["main_count"]), (ticks, loops))
            self.assertEqual(zlib.crc32(raw[:-4]), struct.unpack_from("<I", raw, len(raw)-4)[0])

    def test_sequence_wrap_never_exposes_zero(self):
        self.assertEqual(self.decode(self.frame(sequence=0xfffffffe))["sequence"], 2)

    def test_lengths_old_abi_and_unpublished_rejected(self):
        raw = self.frame()
        for damaged in (b"", raw[:-1], raw+b"x", bytes(256), self.mutate(raw, 0, 0x4d334244),
                        self.mutate(raw, 3, 0), self.mutate(raw, 3, 3)):
            with self.assertRaises(ValueError): self.decode(damaged)

    def test_semantic_faults_rejected_even_with_valid_crc(self):
        raw = self.frame()
        for index, value in ((4,0),(8,0),(9,0),(15,8),(18,1),(19,1),(24,0),
                             (24,64000001),(25,100),(26,3),(27,3),(44,127),(45,7),(62,1)):
            with self.assertRaises(ValueError): self.decode(self.mutate(raw, index, value))

    def sensor_frame(self, mode=0, ticks=1000):
        words=(ctypes.c_uint32*256).from_buffer_copy(self.frame(ticks))
        self.lib.r10_test_sensor_record(words,mode)
        dest=(ctypes.c_uint32*256)();sequence=ctypes.c_uint32(words[3])
        self.lib.r10_publish(dest,words,ctypes.byref(sequence))
        return bytes(dest)

    def voltage_frame(self,mode=1,ticks=1000):
        words=(ctypes.c_uint32*256).from_buffer_copy(self.frame(ticks))
        self.lib.r10_test_voltage_record(words,mode)
        dest=(ctypes.c_uint32*256)();sequence=ctypes.c_uint32(words[3])
        self.lib.r10_publish(dest,words,ctypes.byref(sequence))
        return bytes(dest)

    def test_actual_voltage_core_adapter_model_and_serializer_are_decoded(self):
        d=self.decode(self.voltage_frame())["voltage"]
        self.assertTrue(d["fresh"]);self.assertEqual(d["state"],"WAIT")
        self.assertEqual(list(d["sample_raw"].values()),[375,140,155,256,375])
        self.assertEqual(d["sample_configuration"]["factory_calibration16"],24000)
        for name in ("hardware_qualified","measurement_accuracy_qualified","electrical_health_assessed"):
            self.assertFalse(d[name])

    def test_voltage_failure_keeps_full_raw_error_and_last_good_sample(self):
        old=self.decode(self.voltage_frame())["voltage"]["values_nominal"]
        for mode,error in ((2,"START_ERROR"),(3,"START_ERROR"),(4,"RAW_RANGE"),(5,"REFERENCE_DRIFT"),(6,"START_ERROR")):
            with self.subTest(mode=mode):
                d=self.decode(self.voltage_frame(mode))["voltage"]
                self.assertFalse(d["fresh"]);self.assertTrue(d["has_sample"])
                self.assertEqual(d["error"],error);self.assertEqual(d["values_nominal"],old)
                if mode==3:
                    self.assertEqual((d["state"],d["cleanup_error"]),("STOPPED","CLEANUP"))
                    self.assertEqual(d["cleanup_driver_failure"]["reason"],"CLEANUP")
                    self.assertEqual(d["last_driver_failure"]["reason"],"STATUS")
                if mode==4:
                    self.assertEqual(d["pending_raw"]["logic"],0xffffffff)
                    self.assertEqual(d["port"]["last_dr_raw"],0xffffffff)
                    self.assertNotEqual(d["sample_raw"]["logic"],0xffffffff)

    def test_voltage_age_counter_wrap_and_progress_are_separate(self):
        raw=self.voltage_frame(ticks=10)
        first=self.decode(raw);tick=first["voltage"]["last_good_tick_lo"]
        for age in (999,1000,1001,0xffffffff):
            d=self.decode(self.mutate(raw,5,(tick+age)&0xffffffff))["voltage"]
            self.assertEqual(d["fresh"],age<1000)
        first=self.decode(self.mutate(self.voltage_frame(ticks=1000),139,0xffffffff))
        raw=self.mutate(self.voltage_frame(ticks=2000),139,0)
        raw=self.mutate(self.mutate(raw,3,first["sequence"]+2),7,first["main_count"]+20)
        second=self.decode(raw)
        result=decoder.pair(first,second)["voltage_progress"]
        self.assertTrue(result["reported_acquisition_progress"]);self.assertEqual(result["sample_count_delta"],1)
        raw=self.voltage_frame(mode=4,ticks=2000)
        failed=self.decode(self.mutate(self.mutate(raw,3,first["sequence"]+2),7,first["main_count"]+20))
        paired=decoder.pair(first,failed)
        self.assertTrue(paired["observed_progress"])
        self.assertFalse(paired["voltage_progress"]["reported_acquisition_progress"])

    def test_v4_reserved_space_and_voltage_semantic_claims_are_checked(self):
        raw=self.voltage_frame()
        for index,value in ((63,1),(98,1),(127,1),(193,1),(254,1),(128,0),(129,99),
                            (133,13),(142,6),(143,2),(144,1),(170,0x2008),(175,1),(180,0),(192,0),(4,3)):
            with self.subTest(index=index,value=value),self.assertRaises(ValueError):self.decode(self.mutate(raw,index,value))

    def test_actual_c_imu_raw_packing_and_config_validity(self):
        imu=self.decode(self.sensor_frame())["imu"]
        self.assertEqual(imu["state"],"READY")
        self.assertTrue(imu["fresh"])
        self.assertEqual(imu["nominal_sample_age_ms"],20)
        self.assertEqual(list(imu["raw_counts"].values()),[-32768,32767,-1,0,1,-2,30000,-30000,12,-256])
        self.assertEqual(imu["endpoint_mask"],3)
        self.assertTrue(imu["config_matches_profile"])
        self.assertFalse(imu["sensor_identity_authenticated"])

    def test_old_sample_suppressed_without_losing_fault_history(self):
        raw=self.sensor_frame()
        for age in (251,1000,0xffffffff):
            imu=self.decode(self.mutate(raw,49,(1000-age)&0xffffffff))["imu"]
            self.assertFalse(imu["fresh"])
            self.assertEqual((imu["effective_state"],imu["effective_valid_mask"]),("STALE",0))
        for mode,state,error in ((1,"STALE","NO_DATA"),(2,"ERROR","DATA_READ")):
            imu=self.decode(self.sensor_frame(mode))["imu"]
            self.assertEqual((imu["state"],imu["error"]),(state,error))
            self.assertEqual(imu["raw_counts"]["gyro_x"],-32768)
            self.assertFalse(imu["fresh"])
            self.assertEqual(imu["effective_valid_mask"],0)

    def test_sensor_counter_and_low_tick_wrap_keep_sample_identity(self):
        raw=self.sensor_frame(ticks=10)
        imu=self.decode(self.mutate(raw,48,0))["imu"]
        self.assertTrue(imu["has_sample"])
        self.assertEqual(imu["samples"],0)
        self.assertEqual(imu["nominal_sample_age_ms"],20)
        self.assertTrue(imu["fresh"])

    def test_sensor_inconsistent_claims_rejected(self):
        raw=self.sensor_frame()
        for index,value in ((45,7),(46,10),(47,0x100b73),(47,0x810f0f73),
                            (47,0x01010b73),(50,0x200),(56,0),(59,2000000),(62,10),(4,3)):
            with self.subTest(index=index,value=value),self.assertRaises(ValueError):
                self.decode(self.mutate(raw,index,value))

    def test_v1_saved_records_stay_decodable_but_cannot_pair_with_v2(self):
        for version in (1,2):
            words=list(struct.unpack("<256I",self.frame()))[:64]
            words[1]=version;words[2]=256;words[27]=0 if version==1 else 1;words[44]=7 if version==1 else 15
            payload=struct.pack("<63I",*words[:63]);raw=payload+struct.pack("<I",zlib.crc32(payload))
            old=self.decode(raw)
            self.assertEqual(old["abi_version"],version)
            self.assertIsNone(old["baro"])
            with self.assertRaises(ValueError):decoder.pair(old,self.decode(self.frame()))

    def test_historical_v3_sensor_records_keep_their_layout_and_reserved_contract(self):
        words=list(struct.unpack("<256I",self.baro_frame()))[:128]
        words[1]=3;words[2]=512;words[27]=1;words[44]=31
        raw=struct.pack("<127I",*words[:127]);raw+=struct.pack("<I",zlib.crc32(raw))
        old=self.decode(raw)
        self.assertEqual(old["baro"]["pressure_pa"],100009)
        self.assertIsNone(old["voltage"])
        with self.assertRaises(ValueError):decoder.pair(old,self.decode(self.frame()))
        with self.assertRaises(ValueError):self.decode(self.mutate(raw,98,1))

    def test_main_progress_and_sensor_progress_are_separate(self):
        first=self.decode(self.sensor_frame(ticks=1000))
        raw=self.mutate(self.sensor_frame(ticks=2000),3,6)
        raw=self.mutate(raw,7,20)
        second=self.decode(self.mutate(raw,48,57))
        result=decoder.pair(first,second)
        self.assertTrue(result["observed_progress"])
        self.assertTrue(result["imu_progress"]["reported_acquisition_progress"])
        result=decoder.pair(first,self.decode(raw))
        self.assertTrue(result["observed_progress"])
        self.assertFalse(result["imu_progress"]["reported_acquisition_progress"])

    def baro_frame(self,mode=0,ticks=1000):
        words=(ctypes.c_uint32*256).from_buffer_copy(self.frame(ticks))
        self.lib.r10_test_baro_record(words,mode)
        dest=(ctypes.c_uint32*256)();sequence=ctypes.c_uint32(words[3])
        self.lib.r10_publish(dest,words,ctypes.byref(sequence));return bytes(dest)

    def test_actual_c_barometer_pack_keeps_raw_calibration_and_values(self):
        d=self.decode(self.baro_frame())["baro"]
        self.assertEqual((d["pressure_pa"],d["temp_centic"]),(100009,2007))
        self.assertTrue(d["fresh"])
        self.assertEqual(d["current_prom"],d["sample_prom"])
        self.assertEqual(d["nominal_sample_age_ms"],45)
        self.assertEqual(d["sample_d1"],9085466)
        self.assertFalse(d["hardware_qualified"])

    def test_barometer_integer_compensation_matches_c_across_temperature_branches(self):
        rng=random.Random(0x5611)
        for _ in range(500):
            c=[rng.randrange(65536) for _ in range(8)];c[7]=(c[7]&0xff00)|decoder.prom_crc4(c)
            d1,d2=rng.randrange(1,0xffffff),rng.randrange(1,0xffffff)
            pressure,temp=ctypes.c_int32(),ctypes.c_int32()
            self.lib.bench_ms5611((ctypes.c_uint16*8)(*c),d1,d2,ctypes.byref(pressure),ctypes.byref(temp))
            self.assertEqual(decoder.compensate_ms5611(c,d1,d2),(pressure.value,temp.value))

    def test_barometer_failure_keeps_last_good_pair_and_its_prom(self):
        for mode,error in ((1,"READ_D2"),(2,"PROM_CRC")):
            d=self.decode(self.baro_frame(mode))["baro"]
            self.assertEqual(d["error"],error);self.assertFalse(d["fresh"])
            self.assertEqual(d["effective_valid_mask"],0)
            self.assertEqual(d["pressure_pa"],100009)
            self.assertNotEqual(d["pending_d1"],d["sample_d1"])
        self.assertNotEqual(d["current_prom"],d["sample_prom"])

    def test_barometer_age_counter_wrap_and_inconsistent_claims(self):
        raw=self.baro_frame(ticks=10)
        d=self.decode(self.mutate(raw,67,0))["baro"]
        self.assertTrue(d["has_sample"]);self.assertTrue(d["fresh"])
        self.assertFalse(self.decode(self.mutate(raw,97,(10-251)&0xffffffff))["baro"]["fresh"])
        for index,value in ((64,9),(65,13),(66,3),(85,0),(86,0xffff),(81,0),(73,0),(75,999),(75,100010),(91,13),(98,1),(4,3)):
            with self.subTest(index=index),self.assertRaises(ValueError):self.decode(self.mutate(raw,index,value))

    def test_wrong_board_or_build_rejected(self):
        for bh, ih in (("a1"*32,self.identity),(self.board,"18"*32),("x",self.identity)):
            with self.assertRaises(ValueError): decoder.decode(self.frame(), bh, ih)

    def test_fault_state_preserved_and_address_validity_explicit(self):
        raw = self.mutate(self.frame(state=3), 18, 1 << 7)
        result = self.decode(raw)
        self.assertEqual(result["state"], "FAULT")
        self.assertEqual(result["fault_address_valid"], {"MMFAR":True,"BFAR":False})

    def test_faults_about_clock_or_identity_remain_readable(self):
        raw = self.frame(state=3)
        clock = self.decode(self.mutate(raw,24,0))
        identity = self.decode(self.mutate(raw,9,0))
        self.assertEqual(clock["state"],"FAULT")
        self.assertFalse(clock["clock_consistent"])
        self.assertFalse(identity["identity_consistent"])
        self.assertFalse(clock["hardware_qualified"])

    def test_paired_main_and_tick_progress_required(self):
        first = self.decode(self.frame())
        advance = self.decode(self.frame(20,20,2))
        self.assertTrue(decoder.pair(first,advance)["observed_progress"])
        for later in (first, self.decode(self.frame(9,20,2)), self.decode(self.frame(20,10,2)),
                      self.decode(self.frame(20,20,0)), self.decode(self.frame(20,20,2,state=3))):
            self.assertFalse(decoder.pair(first,later)["observed_progress"])

    def test_tick_low_word_rollover_and_loop_counter_wrap(self):
        first = self.decode(self.frame(0xfffffff0,0xfffffff0,2))
        later = self.decode(self.frame(0x100000010,0x10,4))
        self.assertEqual(decoder.pair(first,later)["main_count_delta"],32)
        self.assertTrue(decoder.pair(first,later)["observed_progress"])

    def test_saved_record_cli_with_synthetic_manifest_and_wrong_board_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);board=folder/"board";board.write_bytes(b"SYNTHETIC TEST BOARD")
            inputs={"test_fixture":"SYNTHETIC ONLY"}
            bh=hashlib.sha256(board.read_bytes()).hexdigest()
            ih=hashlib.sha256(build.canonical(inputs)).hexdigest()
            with mock.patch.object(self,"board",bh),mock.patch.object(self,"identity",ih):
                (folder/"first.bin").write_bytes(self.frame())
                (folder/"second.bin").write_bytes(self.frame(20,20,2))
            manifest=folder/"manifest.json"
            manifest.write_text(json.dumps({"schema":"r10-bench-build/v1","profile":"M3-ASSY-R10",
                                           "board_sha256":bh,"build_id":ih,"mailbox_abi":4,"mailbox_bytes":1024,"inputs":inputs}))
            cmd=[sys.executable,str(HERE/"decode.py"),"--snapshot",str(folder/"first.bin"),
                 "--second",str(folder/"second.bin"),"--board",str(board),"--manifest",str(manifest)]
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=5)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(result.stdout)
            self.assertTrue(report["pair"]["observed_progress"])
            self.assertFalse(report["record"]["hardware_qualified"])
            original=json.loads(manifest.read_text())
            for field,value in (("mailbox_abi",True),("mailbox_abi",3),("mailbox_bytes",512),("mailbox_bytes",1024.0)):
                changed=dict(original);changed[field]=value;manifest.write_text(json.dumps(changed))
                rejected=subprocess.run(cmd,capture_output=True,text=True,timeout=5)
                self.assertEqual(rejected.returncode,3,rejected.stdout)
                self.assertNotIn("Traceback",rejected.stderr)
            missing=dict(original);missing.pop("mailbox_bytes");manifest.write_text(json.dumps(missing))
            rejected=subprocess.run(cmd,capture_output=True,text=True,timeout=5)
            self.assertEqual(rejected.returncode,3)
            manifest.write_text(json.dumps(original))
            board.write_bytes(b"WRONG SYNTHETIC BOARD")
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=5)
            self.assertEqual(result.returncode,3)
            self.assertNotIn("Traceback",result.stderr)

    def test_cli_malformed_manifest_is_controlled_error(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);(p/"snapshot").write_bytes(self.frame());(p/"board").write_bytes(b"test")
            for content in ("null","[]",'{"schema":"a","schema":"b"}',"NaN"):
                (p/"manifest").write_text(content)
                r=subprocess.run([sys.executable,str(HERE/"decode.py"),"--snapshot",str(p/"snapshot"),
                                  "--board",str(p/"board"),"--manifest",str(p/"manifest")],
                                 capture_output=True,text=True,timeout=5)
                self.assertEqual(r.returncode,3)
                self.assertNotIn("Traceback",r.stderr)


class BuildContract(unittest.TestCase):
    def test_freestanding_memcpy_preserves_source_and_guard_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/"copy.dylib"
            subprocess.run(["/usr/bin/clang","-dynamiclib","-O2","-fno-builtin","-Wall","-Wextra","-Werror",
                "-Dmemset=r10_private_memset","-Dmemcpy=r10_private_memcpy",str(HERE/"src/memory.c"),"-o",str(output)],check=True,capture_output=True)
            fn=ctypes.CDLL(str(output)).r10_private_memcpy
            fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t];fn.restype=ctypes.c_void_p
            for length in (0,1,2,7,31,256):
                source=(ctypes.c_ubyte*272)(*[(i*17)&255 for i in range(272)])
                old=bytes(source);dest=(ctypes.c_ubyte*272)(*([0xa5]*272))
                self.assertEqual(fn(ctypes.byref(dest,3),ctypes.byref(source,5),length),ctypes.addressof(dest)+3)
                self.assertEqual(bytes(source),old)
                self.assertEqual(bytes(dest),b"\xa5"*3+old[5:5+length]+b"\xa5"*(269-length))

    def test_freestanding_memory_primitive_preserves_guard_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/"memory.dylib"
            subprocess.run(["/usr/bin/clang","-dynamiclib","-O2","-fno-builtin",
                            "-Dmemset=r10_private_memset","-Dmemcpy=r10_private_memcpy",str(HERE/"src/memory.c"),"-o",str(output)],
                           check=True,capture_output=True)
            lib=ctypes.CDLL(str(output));fn=lib.r10_private_memset
            fn.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_size_t];fn.restype=ctypes.c_void_p
            for length in (0,1,2,31,256):
                for value in (-1,0,0x123):
                    buf=(ctypes.c_uint8*258)(*([0x5a]*258));address=ctypes.addressof(buf)+1
                    self.assertEqual(fn(address,value,length),address)
                    self.assertEqual(bytes(buf),b"\x5a"+bytes([value&255])*length+b"\x5a"*(257-length))

    def test_real_main_with_scripted_registers_and_faults(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            (folder/"generated.h").write_text(build.header("a0"*32,"17"*32))
            executable=folder/"runtime"
            subprocess.run(["/usr/bin/clang","-std=c11","-O1","-g","-Wall","-Wextra","-Werror","-DR10_HOST_TEST",
                            "-fsanitize=undefined","-DR10_PUBLISH_OBSERVER","-I"+str(HERE/"tests"),"-I"+str(folder),
                            "-I"+str(HERE/"imu"),"-I"+str(HERE/"vendor/ism6hg256x"),
                            "-I"+str(HERE/"baro"),"-I"+str(HERE/"voltage"),"-I"+str(HERE.parents[1]/"m3_firmware/src"),
                            "-U__weak","-D__weak=__attribute__((weak))",
                            str(HERE/"tests/runtime.c"),str(HERE/"src/mailbox.c"),str(HERE/"imu/imu_core.c"),
                            str(HERE/"imu/imu_frame.c"),str(HERE/"baro/baro_frame.c"),str(HERE/"baro/baro_core.c"),
                            str(HERE/"voltage/voltage_core.c"),str(HERE/"voltage/voltage_frame.c"),
                            str(HERE.parents[1]/"m3_firmware/src/checks.c"),
                            str(HERE/"vendor/ism6hg256x/ism6hg256x_reg.c"),"-o",str(executable)],
                           check=True,capture_output=True,text=True)
            r=subprocess.run([str(executable)],check=True,capture_output=True,text=True,timeout=5)
            self.assertIn("scripted runtime cases passed",r.stdout)
            self.assertEqual(r.stderr,"")

    def test_saved_input_read_is_bounded_and_rejects_fifo_and_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);p=folder/"bytes";p.write_bytes(b"abc")
            self.assertEqual(decoder.read_bytes(p,3),b"abc")
            with self.assertRaises(ValueError):decoder.read_bytes(p,2)
            link=folder/"link";link.symlink_to(p)
            with self.assertRaises(OSError):decoder.read_bytes(link,3)
            fifo=folder/"fifo";os.mkfifo(fifo)
            with self.assertRaises(ValueError):decoder.read_bytes(fifo,3)

    def test_duplicate_manifest_keys_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"a":1,"a":2}',object_pairs_hook=decoder.json_object)

    def test_reviewed_board_and_vendor_inputs(self):
        binding, protocol = build.validate_inputs()
        self.assertEqual(binding["mailbox_bytes"],1024)
        self.assertEqual(protocol["magic_le"],decoder.MAGIC)
        self.assertFalse(binding["actuation_implemented"])

    def test_changed_board_is_not_accepted_by_updating_a_runtime_argument(self):
        original = build.digest
        with mock.patch.object(build, "digest", side_effect=lambda p: "0"*64 if str(p).endswith("m3.kicad_pcb") else original(p)):
            with self.assertRaisesRegex(ValueError,"Reviewed R10 input changed"):
                build.validate_inputs()

    def test_changed_vendor_is_rejected(self):
        original = build.digest
        with mock.patch.object(build,"digest",side_effect=lambda p: "0"*64 if str(p).endswith("core_cm7.h") else original(p)):
            with self.assertRaisesRegex(ValueError,"Pinned vendor source changed"):
                build.validate_inputs()

    def test_generated_identity_has_exact_raw_hash_bytes(self):
        source = build.header("a0"*32,"b1"*32)
        self.assertEqual(source.count("0xa0"),32)
        self.assertEqual(source.count("0xb1"),32)

    def test_protocol_word_offsets_and_reserved_zero_match_real_c(self):
        p = json.loads((HERE/"protocol.json").read_text())
        self.assertEqual(p["words"]["sequence"],3)
        self.assertEqual(p["words"]["crc32"],255)
        self.assertEqual(p["words"]["board_sha256"]*4,112)
        self.assertEqual(p["words"]["build_id"]*4,144)

    def test_binary_vector_checker_rejects_corruption(self):
        vectors = [0x08000401]*166
        vectors[0] = 0x20020000
        for i in (7,8,9,10,13): vectors[i] = 0
        raw = struct.pack("<166I",*vectors)+bytes(2048)
        symbols = "24000000 00000400 B r10_mailbox\n24000000 B _r10_mailbox_start\n24000400 B _r10_mailbox_end\n"
        build.verify_binary(raw,symbols,"strd r2, r3, [r0]\ndmb sy")
        for i, v in ((0,0x20040000),(1,0x08000400),(7,0x08000401),(165,0x09000001)):
            broken=list(vectors);broken[i]=v
            with self.assertRaises(ValueError):
                build.verify_binary(struct.pack("<166I",*broken)+bytes(2048),symbols,"strd dmb")
        with self.assertRaises(ValueError): build.verify_binary(raw,symbols,"no required instructions")
        with self.assertRaises(ValueError):build.verify_binary(raw,symbols.replace('24000400','24000100'),"strd dmb")


if __name__ == "__main__":
    unittest.main()
