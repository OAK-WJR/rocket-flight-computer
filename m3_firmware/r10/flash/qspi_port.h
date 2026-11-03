/* Bounded, exclusively-owned QUADSPI transport for read-only bench commands. */
#ifndef R10_QSPI_PORT_H
#define R10_QSPI_PORT_H
#include "flash_ro.h"
enum {
    Q_RCC=0x58024400u,Q_GPIOB=0x58020400u,Q_GPIOD=0x58020c00u,Q_GPIOE=0x58021000u,
    Q_BASE=0x52005000u,Q_ID=0x5c001000u,
    Q_RCC_CR=Q_RCC,Q_CFGR=Q_RCC+0x10u,Q_D1CFGR=Q_RCC+0x18u,
    Q_D1CCIPR=Q_RCC+0x4cu,Q_RESET=Q_RCC+0x7cu,Q_ENABLE=Q_RCC+0xd4u,Q_GPIO_ENABLE=Q_RCC+0xe0u,
    Q_GATE=0x4000u,Q_GPIO_GATES=0x1au,
    Q_MODER=0u,Q_OTYPER=4u,Q_SPEED=8u,Q_PULL=12u,Q_IDR=16u,Q_ODR=20u,
    Q_BSRR=24u,Q_AFRL=32u,Q_AFRH=36u,
    Q_CR=0u,Q_DCR=4u,Q_SR=8u,Q_FCR=12u,Q_DLR=16u,Q_CCR=20u,Q_AR=24u,Q_ABR=28u,Q_DR=32u,
    Q_TEF=1u,Q_TCF=2u,Q_FTF=4u,Q_SMF=8u,Q_TOF=16u,Q_BUSY=32u,Q_LEVEL=0x3f00u,
    Q_FLAGS=0x1bu,Q_ERRORS=0x19u,Q_CONTROL=0x3f000001u,Q_DEVICE=(23u<<16)|(3u<<8)
};
enum {Q_NEW,Q_RESET_HELD,Q_RESET_RELEASED,Q_PRIMED,Q_READY,Q_FAULT};
enum {Q_FAIL_ADAPTER=1,Q_FAIL_CLOCK,Q_FAIL_ID,Q_FAIL_OWNERSHIP,Q_FAIL_GPIO,
      Q_FAIL_ENABLE,Q_FAIL_RESET,Q_FAIL_TIMING,Q_FAIL_CONFIG,Q_FAIL_ARGUMENT,
      Q_FAIL_START,Q_FAIL_STATUS,Q_FAIL_COUNT,Q_FAIL_DATA,Q_FAIL_CLEANUP};
typedef struct {
    void *context;
    uint32_t (*read)(void *,uint32_t address,unsigned width);
    void (*write)(void *,uint32_t address,uint32_t value,unsigned width);
    /* ES0392 2.7.4 timing primitive. Called only with QSPI reset/idle and all
     * data/clock pins parked, NCS driven high. Native code masks interrupts
     * around the prescribed consecutive CCR/CCR/CR stores. No SPI opcode. */
    int (*prime)(void *);
} r10_qspi_mmio;
typedef struct {
    r10_qspi_mmio io;
    uint32_t phase,phase_ms,revision,detail,last_cr,last_sr,last_ccr,last_dr;
    uint32_t expected_ccr,expected_dlr,command,received,nominal_hz;
    uint8_t owned,active,parked;
} r10_qspi_port;
int r10_qspi_initialize(void *,uint32_t,uint32_t *,uint32_t *);
int r10_qspi_start(void *,unsigned,uint32_t *);
int r10_qspi_poll(void *,uint8_t *,uint32_t,uint32_t *,uint32_t *);
int r10_qspi_cancel(void *,uint32_t *);
const r10_flash_ro_io *r10_native_flash_io(void);
const r10_qspi_port *r10_native_qspi_state(void);
#endif
