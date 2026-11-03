#ifndef R10_BARO_IO_H
#define R10_BARO_IO_H
#include <stddef.h>
#include <stdint.h>
typedef struct {
    void *handle;
    int (*initialize)(void *,uint32_t *nominal_hz,uint32_t *detail);
    /* One STOP-terminated message: tx_count=1 or rx_count=2/3, never both.
     * Must return within a finite poll budget independent of SysTick. */
    int (*transfer)(void *,uint8_t address,const uint8_t *tx,size_t tx_count,
                    uint8_t *rx,size_t rx_count,uint32_t *detail);
} r10_baro_io;
const r10_baro_io *r10_native_baro_io(void);
#endif
