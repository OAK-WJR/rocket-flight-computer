#ifndef R10_I2C_PORT_H
#define R10_I2C_PORT_H
#include <stddef.h>
#include <stdint.h>

/* Names are separate from spi_port.h; native_i2c.c checks pinned CMSIS. */
enum {
    R10_I2C_RCC=0x58024400u, R10_I2C_GPIOB=0x58020400u, R10_I2C1=0x40005400u,
    R10_I2C_RCC_CR=R10_I2C_RCC, R10_I2C_CFGR=R10_I2C_RCC+0x10,
    R10_I2C_D1CFGR=R10_I2C_RCC+0x18, R10_I2C_D2CFGR=R10_I2C_RCC+0x1c,
    R10_I2C_D2CCIP2R=R10_I2C_RCC+0x54, R10_I2C_APB1LRSTR=R10_I2C_RCC+0x90,
    R10_I2C_AHB4ENR=R10_I2C_RCC+0xe0, R10_I2C_APB1LENR=R10_I2C_RCC+0xe8,
    R10_I2C_MODER=R10_I2C_GPIOB, R10_I2C_OTYPER=R10_I2C_GPIOB+4,
    R10_I2C_OSPEEDR=R10_I2C_GPIOB+8, R10_I2C_PUPDR=R10_I2C_GPIOB+12,
    R10_I2C_IDR=R10_I2C_GPIOB+16, R10_I2C_AFRH=R10_I2C_GPIOB+36,
    R10_I2C_CR1=R10_I2C1, R10_I2C_CR2=R10_I2C1+4,
    R10_I2C_OAR1=R10_I2C1+8, R10_I2C_OAR2=R10_I2C1+12,
    R10_I2C_TIMINGR=R10_I2C1+16, R10_I2C_TIMEOUTR=R10_I2C1+20,
    R10_I2C_ISR=R10_I2C1+24, R10_I2C_ICR=R10_I2C1+28,
    R10_I2C_RXDR=R10_I2C1+36, R10_I2C_TXDR=R10_I2C1+40,
    R10_I2C_PE=1u, R10_I2C_TXIS=2u, R10_I2C_RXNE=4u,
    R10_I2C_NACKF=0x10u, R10_I2C_STOPF=0x20u,
    R10_I2C_BERR=0x100u, R10_I2C_ARLO=0x200u, R10_I2C_OVR=0x400u,
    R10_I2C_TIMEOUT=0x1000u, R10_I2C_BUSY=0x8000u,
    R10_I2C_RD_WRN=0x400u, R10_I2C_START=0x2000u, R10_I2C_STOP=0x4000u,
    R10_I2C_AUTOEND=0x02000000u, R10_I2C_NBYTES_SHIFT=16,
    R10_I2C_ERRORS=0x3f10u, /* Required faults plus unexpected PECERR/ALERT. */
    R10_I2C_CLEAR=0x3f38u, R10_I2C_UNEXPECTED=0xc8u, /* ADDR/TC/TCR */
    R10_I2C_ENABLE=0x00200000u, R10_I2C_GPIO_ENABLE=2u,
    R10_I2C_PINS=0x300u, R10_I2C_PIN_FIELDS=0x000f0000u,
    R10_I2C_AF_MASK=0xffu, R10_I2C_AF4=0x44u, R10_I2C_AF_MODE=0x000a0000u,
    R10_I2C_CLOCK_MASK=0x3000u, R10_I2C_HSI_SOURCE=0x2000u,
    R10_I2C_HSI_MASK=0x1du, R10_I2C_HSI_READY=5u,
    R10_I2C_SYS_MASK=0x3fu, R10_I2C_AHB_MASK=0xf0fu, R10_I2C_APB_MASK=0x70u,
    R10_I2C_POLL_MAX=1000000u, R10_I2C_CLEANUP_POLLS=128u,
    R10_I2C_BUS_FREE_CYCLES=512u
};
/* PRESC=7, SCLDEL=11, SDADEL=4, SCLH=SCLL=79. See contract derivation. */
#define R10_I2C_TIMING 0x70b44f4fu
#define R10_I2C_NOMINAL_HZ 50000u
#define R10_I2C_ADDRESS 0x77u
enum r10_i2c_stage {
    R10_I2C_ADAPTER=1, R10_I2C_CLOCK, R10_I2C_CONFIG, R10_I2C_INIT_IDLE,
    R10_I2C_ARGUMENT, R10_I2C_IDLE, R10_I2C_TX, R10_I2C_RX,
    R10_I2C_WAIT_STOP, R10_I2C_WAIT_BUSY, R10_I2C_FINAL
};
typedef struct {
    void *context;
    uint32_t (*read)(void *,uint32_t address,unsigned width);
    void (*write)(void *,uint32_t address,uint32_t value,unsigned width);
    void (*delay_cycles)(void *,unsigned cycles);
} r10_i2c_mmio;
typedef struct {
    r10_i2c_mmio io;
    uint32_t poll_limit, last_isr, stage, transmitted, received;
    uint8_t initialized;
} r10_i2c_port;
int r10_i2c_initialize(void *,uint32_t *nominal_hz,uint32_t *detail);
int r10_i2c_transfer(void *,uint8_t,const uint8_t *,size_t,uint8_t *,size_t,uint32_t *);
#endif
