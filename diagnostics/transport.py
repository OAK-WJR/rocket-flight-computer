"""Pinned pyOCD transport: open probe + DP + AP0 only, no target.init().

SWD necessarily writes DP control and MEM-AP address/size registers. The AP
proxy rejects writes to the target-memory data register, and permits only the
reviewed diagnostic addresses. This does not promise zero timing/power impact
from connecting a debugger. No reset/halt/resume/erase/program fallback exists.
"""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import tempfile
import time
import uuid

from .engine import digest
from .registers import REGISTERS, CPUID_MASK, EXPECTED_CPUID, EXPECTED_FAMILY, PY_OCD_VERSION


def utc():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, data):
    path = Path(path)
    tmp = path.with_name(path.name + '.writing')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def pyocd_version():
    try:
        version = importlib.metadata.version('pyocd')
    except importlib.metadata.PackageNotFoundError:
        raise RuntimeError('pyOCD is not installed; use diagnostics/.venv/bin/python or install it per the README.')
    if version != PY_OCD_VERSION:
        raise RuntimeError(f'Requires the reviewed pyOCD {PY_OCD_VERSION}, found {version}; refusing to switch drivers silently.')
    return version


def probes():
    pyocd_version()
    from pyocd.core.helpers import ConnectHelper
    return ConnectHelper.get_all_connected_probes(blocking=False, print_wait_message=False)


class ReadOnlyAPGuard:
    """MinimalMemAP-compatible DP proxy: never write AP DRW/BD0..BD3."""
    def __init__(self, dp):
        self.dp = dp
        self.operations = []
        self.mailbox_enabled = False
        self.storage_mailbox_enabled = False
        self.flash_enabled = False
        self.operation_count=0
        self.trace_limit=None

    def write_ap(self, address, value):
        mailbox_word = (self.mailbox_enabled and isinstance(value, int) and not isinstance(value, bool)
                        and 0x24000000 <= value < (0x24000400 if self.storage_mailbox_enabled else 0x24000200) and value % 4 == 0)
        flash_word=(self.flash_enabled and type(value) is int and 0x90000000<=value<0x91000000 and value%4==0)
        if not ((address == 0 and value == 0x03000012) or
                (address == 4 and (value in {v[0] for v in REGISTERS.values()} or mailbox_word or flash_word))):
            raise RuntimeError(f'Blocked AP write: 0x{address:x} <- 0x{value:x}')
        self.operation_count+=1
        if self.trace_limit is None or len(self.operations)<self.trace_limit:
            self.operations.append(['AP_CONFIG_WRITE', address, value])
        return self.dp.write_ap(address, value)

    def read_ap(self, address):
        if address not in (0xFC, 0x0C):
            raise RuntimeError('Blocked AP read')
        value = self.dp.read_ap(address)
        if address == 0xFC and (not isinstance(value, int) or value & 0x0FFFE00F != 0x04770001):
            raise RuntimeError('Unexpected AP0 identity; no memory transactions allowed')
        return value


class PyOCDReader:
    def __init__(self, probe_id):
        self.probe_id = probe_id
        self.session = self.dp = self.guard = self.ap = self.temp = None
        self.old_cwd = os.getcwd()

    def open(self):
        pyocd_version()
        from pyocd.core.session import Session
        from pyocd.probe.debug_probe import DebugProbe
        from pyocd.coresight.minimal_mem_ap import MinimalMemAP
        from pyocd.target.builtin.target_STM32H743xx import STM32H743xx
        found = [p for p in probes() if p.unique_id == self.probe_id]
        if len(found) != 1:
            raise RuntimeError('A unique, exactly matching probe ID is required; not connected or ID mismatch.')
        self.temp = tempfile.TemporaryDirectory(prefix='m3-swd-')
        options = dict(target_override='stm32h743xx', connect_mode='attach',
                       auto_unlock=False, resume_on_disconnect=False, no_config=True,
                       project_dir=self.temp.name, frequency=100000, dap_protocol='swd')
        self.session = Session(found[0], auto_open=False, options=options)
        if type(self.session.target) is not STM32H743xx:
            raise RuntimeError('Unexpected target class; refusing vendor initialization')
        if self.session.delegate is not None or self.session.target.debug_sequence_delegate is not None:
            raise RuntimeError('Unexpected user/debug script; refusing connection')
        # Crucial: no board/core/flash initialization, no breakpoints/watchpoints.
        self.session.open(init_board=False)
        self.dp = self.session.target.dp
        self.dp.connect(DebugProbe.Protocol.SWD)
        # pyOCD's connect sequence does not propagate a False power ACK result.
        if not self.dp.power_up_debug():
            raise RuntimeError('Debug/system power request was not acknowledged')
        self.guard = ReadOnlyAPGuard(self.dp)
        self.ap = MinimalMemAP(self.guard)
        self.ap.init()
        modules = [inspect.getfile(type(x)) for x in (self.dp, self.ap, found[0])]
        return {'pyocd_version': PY_OCD_VERSION, 'probe_id': self.probe_id,
                'probe_description': found[0].description,
                'dpidr': f'0x{self.dp.dpidr.idr:08x}', 'frequency_hz': 100000,
                'target_init_executed': False,
                'driver_sources': {Path(p).name: digest(p) for p in modules}}

    def read(self, name):
        address, bits = REGISTERS[name]
        # FLASHSIZE is a 16-bit field; read its aligned word and retain low half.
        return int(self.ap.read32(address)) & ((1 << bits)-1)

    def enable_mailbox(self):
        """Opt-in fixed 512-byte AXI RAM range, after checked family identity."""
        c, d = self.read('CPUID'), self.read('DBGMCU_IDCODE')
        if c & CPUID_MASK != EXPECTED_CPUID or d & 0xFFF != EXPECTED_FAMILY:
            raise RuntimeError('Wrong target; mailbox range remains disabled')
        self.guard.mailbox_enabled = True

    def read_mailbox_word(self, index):
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < (256 if self.guard.storage_mailbox_enabled else 128):
            raise ValueError('Mailbox word outside reviewed range')
        if not self.guard.mailbox_enabled:
            raise RuntimeError('Mailbox access was not enabled')
        return int(self.ap.read32(0x24000000 + 4 * index))

    def enable_storage_mailbox(self):
        """Only v5/v6/v7 initialize the extra ECC SRAM. Grant after exact header."""
        if not self.guard.mailbox_enabled:raise RuntimeError('Family not checked')
        self.guard.storage_mailbox_enabled=False
        header=[self.read_mailbox_word(i) for i in range(4)]
        if header[0]!=1295204932 or header[1] not in (5,6,7) or header[2]!=1024 or header[3]&1:
            raise RuntimeError('No committed v5/v6/v7 header')
        self.guard.storage_mailbox_enabled=True

    def enable_flash_dump(self, manifest):
        from .mailbox import STORAGE_PROTOCOL,manifest_protocol,read_consistent,decode
        self.guard.flash_enabled=False
        if manifest_protocol(manifest)!=STORAGE_PROTOCOL or manifest['build_options']['storage']!='inspect':
            raise RuntimeError('Dump requires exact v5 inspect image')
        result=read_consistent(self,protocol=STORAGE_PROTOCOL)
        if result['accepted'] is None:raise RuntimeError('No consistent inspect status')
        d=decode(result['attempts'][result['accepted']]['words']);w=d['words']
        if (d['board_sha256']!=manifest['board_sha256'] or d['build_sha256']!=manifest['build_sha256'] or
            d['uid']!=[self.read(n) for n in ('UID0','UID1','UID2')] or d['state']!=3 or
            w[128]!=0 or w[129]!=2 or w[130]!=0 or w[131]!=0 or w[134]!=0xef4018 or
            w[138]!=4096 or w[149]!=1):raise RuntimeError('Flash mapping evidence not ready/bound')
        self.guard.flash_enabled=True
        self.guard.trace_limit=2048
        return d

    def read_flash(self,offset,length):
        if (type(offset) is not int or type(length) is not int or offset%4 or length%4 or
            not 0<length<=4096 or not 0<=offset<=0x1000000-length):raise ValueError('Flash read bounds')
        if not self.guard.flash_enabled:raise RuntimeError('Flash grant disabled')
        import struct
        return b''.join(struct.pack('<I',int(self.ap.read32(0x90000000+i))) for i in range(offset,offset+length,4))

    def close(self):
        try:
            if self.dp is not None:
                self.dp.disconnect()  # release only debugger power requests
        finally:
            try:
                if self.session is not None:
                    self.session.close()  # board was never initialized
            finally:
                os.chdir(self.old_cwd)
                if self.temp is not None:
                    self.temp.cleanup()


def capture(reader, binding, assembly_id, output, origin='SWD_CAPTURE', pause=time.sleep):
    """Persist every result, including connection failure and partial bus faults."""
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError('Capture evidence already exists: ' + str(output))
    started = time.monotonic()
    s = dict(schema=1, origin=origin, capture_id=str(uuid.uuid4()), captured_at=utc(),
             assembly_id=assembly_id, board_sha256=binding['board_sha256'],
             state='STARTED', driver=None, error=None, reads=[])
    atomic_json(output, s)
    def read(name, sample):
        address, bits = REGISTERS[name]
        row = dict(name=name, sample=sample, address=f'0x{address:08x}', bits=bits,
                   value=None, error=None, elapsed_ms=(time.monotonic()-started)*1000)
        value = None
        try:
            value = reader.read(name)
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < 2**bits:
                raise ValueError('Transport returned invalid register value')
            row['value'] = f'0x{value:0{bits//4}x}'
        except Exception as e:
            row['error'] = type(e).__name__ + ': ' + str(e)
        s['reads'].append(row)
        atomic_json(output, s)
        return value
    try:
        s['driver'] = reader.open()
        c, d = read('CPUID', 0), read('DBGMCU_IDCODE', 0)
        if c is None or d is None or c & CPUID_MASK != EXPECTED_CPUID or d & 0xFFF != EXPECTED_FAMILY:
            s['state'] = 'IDENTITY_UNCONFIRMED'
        else:
            # Preserve reset history before any optional observations; never clear it.
            for name in REGISTERS:
                if name not in ('CPUID', 'DBGMCU_IDCODE'):
                    read(name, 0)
            pause(.02)
            for name in ('RCC_RSR', 'RCC_CR', 'RCC_CFGR'):
                read(name, 1)
            s['state'] = 'PARTIAL' if any(r['error'] for r in s['reads']) else 'CAPTURED'
    except Exception as e:
        s['state'], s['error'] = 'CONNECTION_FAILED', type(e).__name__ + ': ' + str(e)
    finally:
        try:
            reader.close()
        except Exception as e:
            s['state'], s['error'] = 'CLEANUP_FAILED', type(e).__name__ + ': ' + str(e)
        if getattr(reader, 'guard', None) is not None:
            s['debug_address_operations'] = reader.guard.operations
        s['finished_at'] = utc()
        atomic_json(output, s)
    return s
