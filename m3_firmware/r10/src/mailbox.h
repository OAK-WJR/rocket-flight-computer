#ifndef R10_MAILBOX_H
#define R10_MAILBOX_H
#include <stdint.h>
#include <stddef.h>

/* Separate from every R1 bench ABI. Little-endian, 128 words, CRC at byte508. */
#define R10_WORDS 128u
#define R10_MAGIC 0x44303152u /* ASCII R10D */
#define R10_ABI 3u
#define R10_SEQ 3u
#define R10_CRC 127u
#define R10_PUBLISH_PERIOD_TICKS 1000u
enum {
    R10_STATE_STARTING = 1u, R10_STATE_RUNNING = 2u, R10_STATE_FAULT = 3u
};
typedef struct {
    uint32_t state, ticks_lo, ticks_hi, main_count;
    uint32_t cpuid, idcode, uid[3], reset_flags;
    uint32_t rcc_cr, rcc_cfgr, rcc_d1cfgr, pwr_csr1;
    uint32_t cfsr, hfsr, dfsr, mmfar, bfar, icsr;
    uint32_t core_hz, systick_load, exception;
} r10_observation;

uint32_t r10_crc32(const uint8_t *data, size_t size);
void r10_frame(uint32_t out[R10_WORDS], const r10_observation *obs,
               const uint8_t board_hash[32], const uint8_t build_hash[32]);
void r10_publish(volatile uint32_t dest[R10_WORDS], uint32_t frame[R10_WORDS],
                 uint32_t *sequence);
#endif
