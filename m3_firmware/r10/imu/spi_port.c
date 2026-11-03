#include "spi_port.h"

static uint32_t rd(r10_spi_port *p,uint32_t a) {return p->io.read(p->io.context,a,4);}
static void wr(r10_spi_port *p,uint32_t a,uint32_t v) {p->io.write(p->io.context,a,v,4);}
static void modify(r10_spi_port *p,uint32_t a,uint32_t mask,uint32_t v) {wr(p,a,(rd(p,a)&~mask)|v);}
static void reset_spi(r10_spi_port *p) {
    modify(p,R10_APB2RSTR,0x1000u,0x1000u);(void)rd(p,R10_APB2RSTR);
    modify(p,R10_APB2RSTR,0x1000u,0);(void)rd(p,R10_APB2RSTR);
}
static void high(r10_spi_port *p) {wr(p,R10_BSRR,0x80u);}
static int wait_flag(r10_spi_port *p,uint32_t flags,uint32_t *budget) {
    while (*budget) {
        --*budget;p->last_sr=rd(p,R10_SR);
        if (p->last_sr&(0x03e0u|0x0800u))return 1;
        if ((p->last_sr&flags)==flags)return 0;
    }
    return 1;
}
static int initialization_error(r10_spi_port *p,uint32_t *detail) {
    *detail=0x80000000u|(p->stage<<16)|(p->last_sr&0xffffu);
    p->initialized=0;return 1;
}
int r10_spi_initialize(void *context,uint32_t *hz,uint32_t *detail) {
    r10_spi_port *p=context;*hz=0;*detail=0;p->initialized=0;p->stage=1;p->last_sr=0;
    if (!p->io.read || !p->io.write || !p->io.delay_cycles || !p->poll_limit || p->poll_limit>1000000u)
        return initialization_error(p,detail);
    modify(p,R10_AHB4ENR,2u,2u);
    if (!(rd(p,R10_AHB4ENR)&2u))return initialization_error(p,detail);
    /* CS first, then output mode. Only sensor pins on GPIOB are changed. */
    high(p);modify(p,R10_OTYPER,0xb8u,0);modify(p,R10_PUPDR,0xcfc0u,0);
    modify(p,R10_OSPEEDR,0xcfc0u,0);modify(p,R10_MODER,0xc000u,0x4000u);
    p->stage=2;
    if (!(rd(p,R10_IDR)&0x80u))return initialization_error(p,detail);
    uint32_t budget=p->poll_limit;
    modify(p,R10_CR,1u,1u);
    while (budget && !(rd(p,R10_CR)&4u))--budget;
    if (!budget || (rd(p,R10_CR)&0x18u))return initialization_error(p,detail);
    modify(p,R10_D1CCIPR,0x30000000u,0);modify(p,R10_D2CCIP1R,0x7000u,0x4000u);
    modify(p,R10_APB2ENR,0x1000u,0x1000u);(void)rd(p,R10_APB2ENR);
    if (!(rd(p,R10_APB2ENR)&0x1000u))return initialization_error(p,detail);
    reset_spi(p);p->stage=3;
    wr(p,R10_SPI_CR1,0x1000u);wr(p,R10_SPI_CR2,0);wr(p,R10_IER,0);wr(p,R10_I2SCFGR,0);
    wr(p,R10_CFG1,R10_SPI_CONFIG1);wr(p,R10_CFG2,R10_SPI_CONFIG2);wr(p,R10_IFCR,0x0ff8u);
    modify(p,R10_AFRL,0x00fff000u,0x00555000u);modify(p,R10_MODER,0x0fc0u,0x0a80u);
    if (rd(p,R10_CFG1)!=R10_SPI_CONFIG1 || rd(p,R10_CFG2)!=R10_SPI_CONFIG2 ||
        (rd(p,R10_D1CCIPR)&0x30000000u) || (rd(p,R10_D2CCIP1R)&0x7000u)!=0x4000u ||
        (rd(p,R10_AFRL)&0x00fff000u)!=0x00555000u || (rd(p,R10_MODER)&0xcfc0u)!=0x4a80u ||
        rd(p,R10_IER)!=0 || !(rd(p,R10_IDR)&0x80u))return initialization_error(p,detail);
    p->initialized=1;*hz=1000000u;p->stage=0;return 0;
}
int r10_spi_exchange(void *context,const uint8_t *tx,uint8_t *rx,size_t count,uint32_t *detail) {
    r10_spi_port *p=context;*detail=0;p->transmitted=0;p->received=0;p->last_sr=0;p->stage=4;
    if (!p->initialized || !tx || !rx || count<2 || count>33) {
        *detail=0x80040000u;return 1;
    }
    uint32_t budget=p->poll_limit;
    /* Each transfer disables/re-enables SPI (ES0392 rapid-restart workaround). */
    if (rd(p,R10_SPI_CR1)&1u)goto failure;
    wr(p,R10_IFCR,0x0ff8u);wr(p,R10_SPI_CR2,(uint32_t)count);
    modify(p,R10_SPI_CR1,1u,1u);
    p->io.delay_cycles(p->io.context,32); /* SCK settles to mode3 idle before CS */
    wr(p,R10_BSRR,0x00800000u);p->io.delay_cycles(p->io.context,32);
    modify(p,R10_SPI_CR1,0x200u,0x200u);
    for (size_t i=0;i<count;++i) {
        p->stage=5;if (wait_flag(p,2u,&budget))goto failure;
        p->io.write(p->io.context,R10_TXDR,tx[i],1);p->transmitted++;
        p->stage=6;if (wait_flag(p,1u,&budget))goto failure;
        rx[i]=(uint8_t)p->io.read(p->io.context,R10_RXDR,1);p->received++;
    }
    p->stage=7;if (wait_flag(p,8u,&budget))goto failure;
    if (rd(p,R10_SR)&1u)goto failure; /* unexpected unread FIFO data */
    /* Engineering initial guard, not an ST-qualified minimum (ES0392). */
    p->io.delay_cycles(p->io.context,128);high(p);
    wr(p,R10_IFCR,0x18u);modify(p,R10_SPI_CR1,1u,0);wr(p,R10_IFCR,0x0ff8u);
    if (!(rd(p,R10_IDR)&0x80u))goto failure;
    p->stage=0;return 0;
failure:
    *detail=0x80000000u|(p->stage<<16)|(p->last_sr&0xffffu);
    high(p);
    if ((rd(p,R10_SPI_CR1)&0x201u)==0x201u) {
        modify(p,R10_SPI_CR1,0x400u,0x400u);
        uint32_t cleanup=128;
        while (cleanup && !(rd(p,R10_SR)&0x800u) && (rd(p,R10_SPI_CR1)&0x200u))--cleanup;
        if (rd(p,R10_SR)&0x800u)wr(p,R10_IFCR,0x800u);
    }
    /* Reset is bounded and local even if suspension failed. No further xfer
     * can run until explicit initialize succeeds. */
    reset_spi(p);p->initialized=0;return 1;
}
