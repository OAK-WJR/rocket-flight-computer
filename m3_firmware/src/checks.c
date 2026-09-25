#include "checks.h"

uint32_t bench_crc32(const uint8_t *data, size_t size) {
    uint32_t rem = UINT32_MAX;
    for (size_t i = 0; i < size; ++i) {
        rem ^= data[i];
        for (unsigned b = 0; b < 8; ++b)
            rem = (rem >> 1) ^ ((rem & 1) ? 0xedb88320U : 0U);
    }
    return rem ^ UINT32_MAX;
}

/* AN520_004: low BYTE of word7 is zeroed, not just the stored CRC nibble.
 * Consume words as big-endian bytes; do not modify the raw evidence array.
 * Independent manufacturer's vector is in test_firmware.py.
 */
uint8_t bench_prom_crc4(const uint16_t prom[8]) {
    uint16_t rem = 0;
    for (unsigned i = 0; i < 16; ++i) {
        uint16_t word = prom[i / 2];
        if (i / 2 == 7) word &= 0xff00U;
        rem ^= (i & 1) ? (word & 255U) : (word >> 8);
        for (unsigned b = 0; b < 8; ++b)
            rem = (uint16_t)((rem << 1) ^ ((rem & 0x8000U) ? 0x3000U : 0U));
    }
    return (uint8_t)((rem >> 12) & 15U);
}

int bench_prom_nonempty(const uint16_t prom[8]) {
    /* Zero/floating buses can satisfy CRC4. Reject both as separate faults. */
    unsigned zero = 0, ones = 0;
    for (unsigned i = 1; i <= 6; ++i) {
        zero += prom[i] == 0;
        ones += prom[i] == 0xffff;
    }
    return zero != 6 && ones != 6;
}

/* H743 factory VREFINT calibration and observations are BOTH 16 bit.
 * Do not use HAL v1.11.6's generic VREF helper, which rescales to 12 bit.
 * Bounds detect erased/12-bit calibration and nonsensical VDDA, not accuracy.
 */
int bench_voltages(uint32_t cal, uint32_t ref, uint32_t logic, uint32_t v3,
                   uint32_t *vdda_mv, uint32_t *logic_mv, uint32_t *v3_mv) {
    *vdda_mv = *logic_mv = *v3_mv = 0;
    if (cal < 20000 || cal > 30000 || !ref || ref >= 65535 || logic > 65535 || v3 > 65535)
        return 0;
    uint32_t v = (3300U * cal + ref / 2U) / ref;
    if (v < 1800 || v > 3600) return 0;
    *vdda_mv = v;
    *logic_mv = (uint32_t)(((uint64_t)logic * v * 11U + 32767U) / 65535U);
    *v3_mv = (uint32_t)(((uint64_t)v3 * v * 2U + 32767U) / 65535U);
    return 1;
}

/* TE MS5611 B3 pp8-9, including both low-temperature correction branches.
 * Signed division truncates toward zero, explicitly (no signed-shift rules).
 * Preserve raw observations separately. No altitude or control calculation.
 */
int bench_ms5611(const uint16_t c[8], uint32_t d1, uint32_t d2,
                 int32_t *pressure_pa, int32_t *temp_centic) {
    *pressure_pa = *temp_centic = 0;
    if (!d1 || !d2 || d1 >= 0xffffffU || d2 >= 0xffffffU ||
        !bench_prom_nonempty(c) || bench_prom_crc4(c) != (c[7] & 15U)) return 0;
    int64_t dt = (int64_t)d2 - (int64_t)c[5] * 256;
    int64_t temp = 2000 + dt * c[6] / 8388608;
    int64_t off = (int64_t)c[2] * 65536 + (int64_t)c[4] * dt / 128;
    int64_t sens = (int64_t)c[1] * 32768 + (int64_t)c[3] * dt / 256;
    if (temp < 2000) {
        int64_t square = (temp - 2000) * (temp - 2000);
        int64_t off2 = 5 * square / 2, sens2 = 5 * square / 4;
        if (temp < -1500) {
            square = (temp + 1500) * (temp + 1500);
            off2 += 7 * square; sens2 += 11 * square / 2;
        }
        temp -= dt * dt / 2147483648LL;
        off -= off2; sens -= sens2;
    }
    int64_t pressure = ((int64_t)d1 * sens / 2097152 - off) / 32768;
    if (temp < INT32_MIN || temp > INT32_MAX || pressure < INT32_MIN || pressure > INT32_MAX)
        return 0;
    *temp_centic = (int32_t)temp; *pressure_pa = (int32_t)pressure;
    /* Full documented operating range, not a calibration/accuracy test. */
    return temp >= -4000 && temp <= 8500 && pressure >= 1000 && pressure <= 120000;
}
