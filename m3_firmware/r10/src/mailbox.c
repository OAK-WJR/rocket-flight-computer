#include "mailbox.h"
#ifdef R10_PUBLISH_OBSERVER
/* Test-only scheduling hook; absent from the ARM build. */
void r10_publish_observe(volatile uint32_t *, const uint32_t *);
#endif

static void barrier(void) {
#if defined(__arm__) || defined(__thumb__)
    __asm volatile ("dmb sy" ::: "memory");
#else
    __asm volatile ("" ::: "memory");
#endif
}

uint32_t r10_crc32(const uint8_t *data, size_t size) {
    uint32_t rem = UINT32_MAX;
    for (size_t i = 0; i < size; ++i) {
        rem ^= data[i];
        for (unsigned b = 0; b < 8; ++b)
            rem = (rem >> 1) ^ ((rem & 1u) ? 0xedb88320u : 0u);
    }
    return rem ^ UINT32_MAX;
}

static uint32_t le32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

void r10_frame(uint32_t out[R10_WORDS], const r10_observation *o,
               const uint8_t board_hash[32], const uint8_t build_hash[32]) {
    for (unsigned i = 0; i < R10_WORDS; ++i) out[i] = 0u;
    out[0] = R10_MAGIC; out[1] = R10_ABI; out[2] = R10_WORDS * 4u;
    out[4] = o->state; out[5] = o->ticks_lo; out[6] = o->ticks_hi;
    out[7] = o->main_count; out[8] = o->cpuid; out[9] = o->idcode;
    for (unsigned i = 0; i < 3u; ++i) out[10u+i] = o->uid[i];
    out[13] = o->reset_flags; out[14] = o->rcc_cr; out[15] = o->rcc_cfgr;
    out[16] = o->rcc_d1cfgr; out[17] = o->pwr_csr1;
    out[18] = o->cfsr; out[19] = o->hfsr; out[20] = o->dfsr;
    out[21] = o->mmfar; out[22] = o->bfar; out[23] = o->icsr;
    out[24] = o->core_hz; out[25] = o->systick_load;
    out[26] = o->exception;
    /* 27: compiled sensor SPI/I2C GPIO policy. Not an electrical observation. */
    out[27]=1u;
    for (unsigned i = 0; i < 8u; ++i) {
        out[28u+i] = le32(board_hash+4u*i);
        out[36u+i] = le32(build_hash+4u*i);
    }
    out[44] = 31u; /* identity, nominal tick, exception, IMU and barometer */
}

void r10_publish(volatile uint32_t dest[R10_WORDS], uint32_t frame[R10_WORDS],
                 uint32_t *sequence) {
    uint32_t next = (*sequence + 2u) & ~1u;
    if (next == 0u) next = 2u;
    /* Reserve before exposing a committed generation. An NMI/fault publisher
     * must get a new generation even if it interrupts the final store below. */
    *sequence = next;
    barrier();
    frame[R10_SEQ] = next;
    frame[R10_CRC] = r10_crc32((const uint8_t *)frame, R10_CRC * 4u);
    dest[R10_SEQ] = next - 1u;
    barrier();
    for (unsigned i = 0; i < R10_WORDS; ++i)
        if (i != R10_SEQ) dest[i] = frame[i];
    barrier();
    dest[R10_SEQ] = next;
#ifdef R10_PUBLISH_OBSERVER
    r10_publish_observe(dest, sequence);
#endif
    barrier();
}
