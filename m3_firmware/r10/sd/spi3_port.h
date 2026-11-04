#ifndef R10_SD_SPI3_PORT_H
#define R10_SD_SPI3_PORT_H
#include "wire.h"

/* Addresses/masks must cross-compile against the pinned H743 CMSIS header.
 * This port does not change shared clock selectors. Initialization requires
 * the reviewed HSI64 CKPER/SPI123 policy and exclusive cold-start ownership. */
enum {
 SD3_RCC=0x58024400u,SD3_GPIOC=0x58020800u,SD3_GPIOD=0x58020c00u,SD3_SPI=0x40003c00u,
 SD3_CR=SD3_RCC,SD3_CFGR=SD3_RCC+0x10u,SD3_D1CFGR=SD3_RCC+0x18u,
 SD3_D1CCIPR=SD3_RCC+0x4cu,SD3_D2CCIP1R=SD3_RCC+0x50u,
 SD3_RESET=SD3_RCC+0x90u,SD3_GPIO_ENABLE=SD3_RCC+0xe0u,SD3_ENABLE=SD3_RCC+0xe8u,
 SD3_MODER=0u,SD3_TYPE=4u,SD3_SPEED=8u,SD3_PULL=12u,SD3_IDR=16u,SD3_ODR=20u,
 SD3_BSRR=24u,SD3_AFRH=36u,
 SD3_CR1=SD3_SPI,SD3_CR2=SD3_SPI+4u,SD3_CFG1=SD3_SPI+8u,SD3_CFG2=SD3_SPI+12u,
 SD3_IER=SD3_SPI+16u,SD3_SR=SD3_SPI+20u,SD3_IFCR=SD3_SPI+24u,
 SD3_TXDR=SD3_SPI+32u,SD3_RXDR=SD3_SPI+48u,SD3_I2S=SD3_SPI+80u,
 SD3_GATE=0x8000u,SD3_GPIO_GATES=12u,SD3_GPIO_FIELDS=0x03f00000u,
 SD3_GPIO_AF_MODES=0x02a00000u,SD3_GPIO_TYPES=0x1c00u,SD3_AF_MASK=0x000fff00u,
 SD3_AF_VALUE=0x00066600u,SD3_CONFIG1=0x70070007u,SD3_CONFIG2=0x84400000u,
 SD3_RXP=1u,SD3_TXP=2u,SD3_EOT=8u,SD3_ERRORS=0x03e0u,SD3_SUSP=0x800u,
 SD3_RX_PENDING=0xe001u,SD3_FLAGS=0xff8u,SD3_GPIO_OWNED=1u,SD3_SPI_OWNED=2u
};
enum { SD3_OK=0,SD3_ADAPTER,SD3_CLOCK,SD3_OWNERSHIP,SD3_GPIO_CLOCK,SD3_GPIO,
       SD3_SPI_CLOCK,SD3_SPI_RESET,SD3_CONFIG,SD3_ARGUMENT,SD3_STATUS,SD3_BUDGET,
       SD3_EXTRA_RX,SD3_CLEANUP };
typedef struct {
 void *context;
 uint32_t (*read)(void *,uint32_t address,unsigned width_bytes);
 void (*write)(void *,uint32_t address,uint32_t value,unsigned width_bytes);
 void (*delay_cycles)(void *,unsigned minimum_loop_iterations);
} r10_sd_spi3_mmio;
typedef struct {
 r10_sd_spi3_mmio io;
 uint32_t poll_limit,owned,ready,selected,stage,error,detail;
 uint32_t last_sr,accepted,received,cleanup_error,cleanup_detail;
 uint32_t observed_clock[5],observed_config[4];
 uint32_t observed_pins[10];
 uint8_t idle_rx[10];
} r10_sd_spi3_port;
int r10_sd_spi3_initialize(void *,uint32_t *,uint32_t *,uint32_t *);
int r10_sd_spi3_select(void *,unsigned,uint32_t *);
int r10_sd_spi3_transfer(void *,const uint8_t *,uint8_t *,unsigned,unsigned *,unsigned *,uint32_t *);
int r10_sd_spi3_release(void *,uint32_t *);
void r10_sd_spi3_bus(r10_sd_spi3_port *,r10_sd_bus *);
const r10_sd_bus *r10_native_sd_bus(void);
const r10_sd_spi3_port *r10_native_sd_spi3_state(void);
#endif
