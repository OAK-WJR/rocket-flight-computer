#ifndef R10_SPI_PORT_H
#define R10_SPI_PORT_H
#include <stddef.h>
#include <stdint.h>

/* Addresses/masks have ARM-side static assertions against pinned H743 headers. */
enum {
    R10_RCC=0x58024400u, R10_GPIOB=0x58020400u, R10_SPI1=0x40013000u,
    R10_CR=R10_RCC, R10_D1CCIPR=R10_RCC+0x4c, R10_D2CCIP1R=R10_RCC+0x50,
    R10_APB2RSTR=R10_RCC+0x98, R10_AHB4ENR=R10_RCC+0xe0, R10_APB2ENR=R10_RCC+0xf0,
    R10_MODER=R10_GPIOB, R10_OTYPER=R10_GPIOB+4, R10_OSPEEDR=R10_GPIOB+8,
    R10_PUPDR=R10_GPIOB+12, R10_IDR=R10_GPIOB+16, R10_BSRR=R10_GPIOB+24, R10_AFRL=R10_GPIOB+32,
    R10_SPI_CR1=R10_SPI1, R10_SPI_CR2=R10_SPI1+4, R10_CFG1=R10_SPI1+8,
    R10_CFG2=R10_SPI1+12, R10_IER=R10_SPI1+16, R10_SR=R10_SPI1+20,
    R10_IFCR=R10_SPI1+24, R10_TXDR=R10_SPI1+32, R10_RXDR=R10_SPI1+48,
    R10_I2SCFGR=R10_SPI1+80
};
#define R10_SPI_CONFIG1 0x50070007u
#define R10_SPI_CONFIG2 0x87400000u
typedef struct {
    void *context;
    uint32_t (*read)(void *,uint32_t address,unsigned width);
    void (*write)(void *,uint32_t address,uint32_t value,unsigned width);
    void (*delay_cycles)(void *,unsigned cycles);
} r10_spi_mmio;
typedef struct {
    r10_spi_mmio io;
    uint32_t poll_limit, last_sr, stage, transmitted, received;
    uint8_t initialized;
} r10_spi_port;
int r10_spi_initialize(void *,uint32_t *nominal_hz,uint32_t *detail);
int r10_spi_exchange(void *,const uint8_t *,uint8_t *,size_t,uint32_t *detail);
#endif
