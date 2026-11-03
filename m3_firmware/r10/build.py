"""Cross-build an independent R10 bench image. Never opens a probe or flashes.

Compiler prefix is supplied at runtime or discovered on PATH. Old R1 builds and
their board binding are deliberately untouched.
"""
import argparse
import hashlib
import json
import importlib.util
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BOARD = "m3_design/assembly_review/m3.kicad_pcb"
VENDOR_SYSTEM = "m3_firmware/vendor/device/Source/Templates/system_stm32h7xx.c"
LOCAL_INPUTS = ["binding.json", "protocol.json", "build.py", "linker.ld",
                "src/startup.s", "src/main.c", "src/mailbox.c", "src/mailbox.h", "src/memory.c",
                "imu/imu_core.c","imu/imu_core.h","imu/spi_port.c","imu/spi_port.h",
                "imu/native_spi.c","imu/imu_frame.c","imu/imu_frame.h","imu/verify.py",
                "baro/baro_io.h","baro/baro_core.h","baro/baro_core.c","baro/baro_frame.h","baro/baro_frame.c",
                "baro/i2c_port.h","baro/i2c_port.c","baro/native_i2c.c","baro/verify.py","baro/provenance.json",
                "vendor/ism6hg256x/ism6hg256x_reg.c","vendor/ism6hg256x/ism6hg256x_reg.h",
                "vendor/ism6hg256x/LICENSE","vendor/ism6hg256x/manifest.json",
                "voltage/voltage_core.h","voltage/voltage_core.c","voltage/adc_port.h","voltage/adc_port.c",
                "voltage/native_adc.c","voltage/voltage_frame.h","voltage/voltage_frame.c",
                "voltage/verify.py","voltage/provenance.json",
                "flash/flash_ro.c","flash/flash_ro.h","flash/qspi_port.c","flash/qspi_port.h",
                "flash/native_qspi.c","flash/flash_frame.c","flash/flash_frame.h",
                "flash/verify_flash.py","flash/provenance.json"]
FLAGS = ["-mcpu=cortex-m7", "-mthumb", "-mfloat-abi=soft", "-Os", "-g3",
         "-std=c11", "-ffreestanding", "-fno-builtin", "-fno-common",
         "-ffunction-sections", "-fdata-sections", "-fstack-usage",
         "-Wall", "-Wextra", "-Werror", "-DSTM32H743xx", "-DUSE_PWR_LDO_SUPPLY"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def validate_inputs(root=ROOT):
    binding = json.loads((HERE / "binding.json").read_text())
    if binding["profile"] != "M3-ASSY-R10":
        raise ValueError("R10 profile required")
    for rel, expected in binding["inputs"].items():
        if digest(root / rel) != expected:
            raise ValueError("Reviewed R10 input changed: " + rel)
    vendor = json.loads((root / "m3_firmware/vendor_manifest.json").read_text())
    for item in vendor["files"]:
        path = root / "m3_firmware" / item["path"]
        if digest(path) != item["sha256"]:
            raise ValueError("Pinned vendor source changed: " + item["path"])
    spec=importlib.util.spec_from_file_location("r10_sensor_sources",HERE/"imu/verify.py")
    sensor=importlib.util.module_from_spec(spec);spec.loader.exec_module(sensor)
    sensor.verify(root)
    spec=importlib.util.spec_from_file_location("r10_barometer_sources",HERE/"baro/verify.py")
    barometer=importlib.util.module_from_spec(spec);spec.loader.exec_module(barometer)
    barometer.verify(root)
    spec=importlib.util.spec_from_file_location("r10_voltage_sources",HERE/"voltage/verify.py")
    voltage=importlib.util.module_from_spec(spec);spec.loader.exec_module(voltage)
    voltage.verify(root)
    spec=importlib.util.spec_from_file_location("r10_flash_sources",HERE/"flash/verify_flash.py")
    flash=importlib.util.module_from_spec(spec);spec.loader.exec_module(flash)
    flash.verify(root)
    protocol = json.loads((HERE / "protocol.json").read_text())
    if (protocol["magic_le"] != int.from_bytes(b"R10D", "little") or
            protocol["address"] != binding["mailbox_address"] or
            protocol["bytes"] != binding["mailbox_bytes"] or protocol["version"]!=5):
        raise ValueError("R10 mailbox contract mismatch")
    return binding, protocol


def header(board_hash, build_hash):
    def array(name, value):
        data = ",".join("0x%02x" % x for x in bytes.fromhex(value))
        return "static const uint8_t %s[32] = {%s};\n" % (name, data)
    return ("/* Generated from reviewed R10 build inputs. */\n#include <stdint.h>\n" +
            array("R10_BOARD_HASH", board_hash) + array("R10_BUILD_HASH", build_hash))


def source_inventory():
    """Current reviewed firmware inputs, shared with the bounded reader."""
    sources = {str((HERE / p).relative_to(ROOT)): digest(HERE / p) for p in LOCAL_INPUTS}
    for p in ("m3_firmware/src/checks.c","m3_firmware/src/checks.h"):sources[p]=digest(ROOT/p)
    vendor = json.loads((ROOT / "m3_firmware/vendor_manifest.json").read_text())
    sources.update({"m3_firmware/"+p["path"]: p["sha256"] for p in vendor["files"]})
    return sources


def verify_qspi_primitive(disassembly):
    match=re.search(r'<prime>:\n(.*?)(?=\n\n|\Z)',disassembly,re.S)
    if not match:raise ValueError('QSPI timing primitive missing from linked image')
    body=match.group(1)
    if 'cpsid' not in body or 'PRIMASK' not in body.upper():
        raise ValueError('QSPI timing stores are not interrupt-masked')
    lines=[line.strip() for line in body.splitlines()]
    for i in range(len(lines)-2):
        triple=lines[i:i+3]
        if (all(re.search(r'\bstr(?:\.w)?\b',line) for line in triple) and
                '#20]' in triple[0] and '#20]' in triple[1] and
                re.search(r'\[r\d+(?:, #0)?\]',triple[2])):
            return
    raise ValueError('QSPI CCR/CCR/CR stores are not consecutive')


def verify_binary(raw, symbols, disassembly):
    if len(raw) < 664:
        raise ValueError("Truncated firmware vector table")
    vectors = struct.unpack("<166I", raw[:664])
    if vectors[0] != 0x20020000:
        raise ValueError("DTCM stack address changed")
    for index, address in enumerate(vectors[1:], 1):
        if index in (7, 8, 9, 10, 13):
            if address != 0:
                raise ValueError("Reserved vector is not zero")
        elif not (address & 1 and 0x08000000 <= (address & ~1) < 0x08000000 + len(raw)):
            raise ValueError("Vector does not point into this Thumb image")
    if not re.search(r"^24000000\s+00000400\s+B\s+r10_mailbox$", symbols, re.M):
        raise ValueError("R10 mailbox symbol/address/length mismatch")
    if (not re.search(r"^24000000\s+B\s+_r10_mailbox_start$",symbols,re.M) or
            not re.search(r"^24000400\s+B\s+_r10_mailbox_end$",symbols,re.M)):
        raise ValueError("Startup ECC mailbox bounds changed")
    if not re.search(r"\bstrd\b", disassembly) or not re.search(r"\bdmb\b", disassembly):
        raise ValueError("ECC double-word init or publication barrier missing")
    verify_qspi_primitive(disassembly)


def build(prefix, out):
    binding, _ = validate_inputs()
    gcc = prefix + "gcc"
    banner = subprocess.check_output([gcc, "--version"], text=True).splitlines()[0]
    if "15.2.1" not in banner:
        raise ValueError("This build is pinned to Arm GNU 15.2.1; review a compiler change first")
    sources = source_inventory()
    identity = {"schema": "r10-bench-build-inputs/v1", "sources": sources,
                "board_inputs": binding["inputs"], "compiler": banner, "flags": FLAGS}
    build_id = hashlib.sha256(canonical(identity)).hexdigest()
    out = out.resolve()
    if out.exists():
        raise ValueError("Refusing to overwrite an existing build directory")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="r10-build-", dir=out.parent) as temp:
        stage = Path(temp)
        (stage / "generated.h").write_text(header(binding["inputs"][BOARD], build_id))
        compiler_root = Path(shutil.which(gcc) or gcc).resolve().parents[1]
        common = FLAGS + ["-ffile-prefix-map="+str(ROOT)+"=.",
                          "-fdebug-prefix-map="+str(compiler_root)+"=./toolchain",
                          "-ffile-prefix-map="+str(compiler_root)+"=./toolchain",
                          "-fdebug-prefix-map="+str(stage)+"=./build",
                          "-ffile-prefix-map="+str(stage)+"=./build"]
        includes = [HERE / "src", HERE/"imu",HERE/"baro",HERE/"voltage",HERE/"flash",ROOT/"m3_firmware/src", HERE/"vendor/ism6hg256x", stage, ROOT / "m3_firmware/vendor/cmsis",
                    ROOT / "m3_firmware/vendor/device/Include"]
        includes = ["-I"+str(p) for p in includes]
        env = dict(os.environ, SOURCE_DATE_EPOCH="0", LC_ALL="C")
        objects = []
        for path in [HERE/"src/startup.s", HERE/"src/main.c", HERE/"src/mailbox.c", HERE/"src/memory.c", ROOT/VENDOR_SYSTEM,
                     HERE/"imu/imu_core.c",HERE/"imu/spi_port.c",HERE/"imu/native_spi.c",HERE/"imu/imu_frame.c",
                     HERE/"baro/baro_core.c",HERE/"baro/i2c_port.c",HERE/"baro/native_i2c.c",HERE/"baro/baro_frame.c",ROOT/"m3_firmware/src/checks.c",
                     HERE/"vendor/ism6hg256x/ism6hg256x_reg.c",HERE/"voltage/voltage_core.c",
                     HERE/"voltage/adc_port.c",HERE/"voltage/native_adc.c",HERE/"voltage/voltage_frame.c",
                     HERE/"flash/flash_ro.c",HERE/"flash/qspi_port.c",HERE/"flash/native_qspi.c",HERE/"flash/flash_frame.c"]:
            obj = stage/(path.stem+".o")
            subprocess.run([gcc, *common, *includes, "-c", str(path), "-o", str(obj)], check=True, env=env)
            objects.append(str(obj))
        elf = stage / "r10_bench.elf"
        subprocess.run([gcc, *common, "-nostdlib", "-nostartfiles", *objects,
                        "-T"+str(HERE/"linker.ld"), "-Wl,--gc-sections,--build-id=none",
                        "-Wl,-Map="+str(stage/"r10_bench.map"), "-lgcc", "-o", str(elf)], check=True, env=env)
        for fmt, suffix in (("binary", "bin"), ("ihex", "hex")):
            subprocess.run([prefix+"objcopy", "-O", fmt, str(elf), str(stage/("r10_bench."+suffix))], check=True)
        symbols = subprocess.check_output([prefix+"nm", "-n", "-S", str(elf)], text=True)
        asm = subprocess.check_output([prefix+"objdump", "-d", str(elf)], text=True)
        # objdump's header embeds its input path; keep artifacts portable.
        asm = asm.replace(str(stage), "./build")
        (stage/"symbols.txt").write_text(symbols)
        (stage/"disassembly.txt").write_text(asm)
        verify_binary((stage/"r10_bench.bin").read_bytes(), symbols, asm)
        for path in [stage/"r10_bench.map", *stage.glob("*.su")]:
            text = path.read_text()
            for original, replacement in ((str(stage), "./build"), (str(compiler_root), "./toolchain"), (str(ROOT), ".")):
                text = text.replace(original, replacement)
            path.write_text(text)
        # Refuse a mid-build source/board change rather than signing stale inputs.
        validate_inputs()
        if any(digest(ROOT/p) != h for p, h in sources.items()):
            raise ValueError("Source changed while compiling")
        outputs = {p.name: digest(p) for p in stage.iterdir() if p.is_file()}
        manifest = {"schema": "r10-bench-build/v1", "profile": binding["profile"],
                    "build_id": build_id, "inputs": identity, "outputs": outputs,
                    "mailbox_address": binding["mailbox_address"], "mailbox_bytes": 1024,
                    "board_sha256": binding["inputs"][BOARD], "hardware_tested": False,
                    "flashed": False, "actuation_implemented": False,
                    "sensor_drivers_implemented": True,"barometer_driver_implemented":True, "voltage_driver_implemented":True,"mailbox_abi":5,"flash_driver_implemented":True,"flight_qualified": False}
        (stage/"manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n")
        shutil.copytree(stage, out)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain-prefix", default=os.environ.get("ARM_TOOLCHAIN_PREFIX"))
    parser.add_argument("--out", type=Path, required=True, help="new output directory; never overwritten")
    args = parser.parse_args()
    prefix = args.toolchain_prefix
    if not prefix:
        found = shutil.which("arm-none-eabi-gcc")
        if not found:
            parser.error("set --toolchain-prefix /path/to/bin/arm-none-eabi-")
        prefix = found[:-3]
    try:
        m = build(prefix, args.out)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(2, "R10 build refused: %s\n" % exc)
    print(json.dumps({"build_id": m["build_id"], "binary_sha256": m["outputs"]["r10_bench.bin"],
                      "hardware_tested": False, "flashed": False}))


if __name__ == "__main__":
    main()
