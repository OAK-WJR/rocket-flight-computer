"""Read-only register allowlist, checked against pinned ST and Arm headers.

See sources/manifest.json. No peripheral data registers that acknowledge a
transaction on read, RAM writes, flash reads/programming, or GPIO commands.
"""
REGISTERS = {
    'CPUID': (0xE000ED00, 32),
    'DBGMCU_IDCODE': (0x5C001000, 32),
    'RCC_RSR': (0x580244D0, 32),
    'FLASH_SIZE_KIB': (0x1FF1E880, 16),
    'UID0': (0x1FF1E800, 32),
    'UID1': (0x1FF1E804, 32),
    'UID2': (0x1FF1E808, 32),
    'RCC_CR': (0x58024400, 32),
    'RCC_CFGR': (0x58024410, 32),
    'PWR_D3CR': (0x58024818, 32),
    'CFSR': (0xE000ED28, 32),
    'HFSR': (0xE000ED2C, 32),
    'MMFAR': (0xE000ED34, 32),
    'BFAR': (0xE000ED38, 32),
}
RESET_BITS = {
    17: 'CPU', 19: 'D1', 20: 'D2', 21: 'BOR', 22: 'PIN',
    23: 'POR', 24: 'SOFTWARE', 26: 'IWDG1', 28: 'WWDG1', 30: 'LOW_POWER',
}
EXPECTED_FAMILY = 0x450
CPUID_MASK = 0xFF0FFFF0  # implementation + architecture + part; ignore variant/revision
EXPECTED_CPUID = 0x410FC270
PY_OCD_VERSION = '0.45.1'

