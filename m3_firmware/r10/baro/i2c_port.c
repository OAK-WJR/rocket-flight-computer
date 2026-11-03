#include "i2c_port.h"

static uint32_t rd(r10_i2c_port *p,uint32_t a) {return p->io.read(p->io.context,a,4);}
static void wr(r10_i2c_port *p,uint32_t a,uint32_t v) {p->io.write(p->io.context,a,v,4);}
static void modify(r10_i2c_port *p,uint32_t a,uint32_t mask,uint32_t v) {
    wr(p,a,(rd(p,a)&~mask)|v);
}
static int adapter_valid(const r10_i2c_port *p) {
    return p && p->io.read && p->io.write && p->io.delay_cycles &&
           p->poll_limit && p->poll_limit<=R10_I2C_POLL_MAX;
}
static int clocks_valid(r10_i2c_port *p) {
    /* Read-only contract: core/AHB/APB1 = undivided HSI; kernel = APB1 or HSI.
     * Ratio APB1/kernel=1 also avoids ES0392 2.19.9 without preloading TXDR. */
    uint32_t source=rd(p,R10_I2C_D2CCIP2R)&R10_I2C_CLOCK_MASK;
    return (rd(p,R10_I2C_RCC_CR)&R10_I2C_HSI_MASK)==R10_I2C_HSI_READY &&
           !(rd(p,R10_I2C_CFGR)&R10_I2C_SYS_MASK) &&
           !(rd(p,R10_I2C_D1CFGR)&R10_I2C_AHB_MASK) &&
           !(rd(p,R10_I2C_D2CFGR)&R10_I2C_APB_MASK) &&
           (source==0 || source==R10_I2C_HSI_SOURCE);
}
static void reset_i2c(r10_i2c_port *p) {
    modify(p,R10_I2C_APB1LRSTR,R10_I2C_ENABLE,R10_I2C_ENABLE);
    (void)rd(p,R10_I2C_APB1LRSTR);
    modify(p,R10_I2C_APB1LRSTR,R10_I2C_ENABLE,0);
    (void)rd(p,R10_I2C_APB1LRSTR);
}
static int pins_valid(r10_i2c_port *p) {
    return (rd(p,R10_I2C_MODER)&R10_I2C_PIN_FIELDS)==R10_I2C_AF_MODE &&
           (rd(p,R10_I2C_OTYPER)&R10_I2C_PINS)==R10_I2C_PINS &&
           !(rd(p,R10_I2C_PUPDR)&R10_I2C_PIN_FIELDS) &&
           !(rd(p,R10_I2C_OSPEEDR)&R10_I2C_PIN_FIELDS) &&
           (rd(p,R10_I2C_AFRH)&R10_I2C_AF_MASK)==R10_I2C_AF4;
}
static int config_valid(r10_i2c_port *p) {
    return (rd(p,R10_I2C_AHB4ENR)&R10_I2C_GPIO_ENABLE) &&
           (rd(p,R10_I2C_APB1LENR)&R10_I2C_ENABLE) &&
           !(rd(p,R10_I2C_APB1LRSTR)&R10_I2C_ENABLE) &&
           rd(p,R10_I2C_CR1)==R10_I2C_PE && rd(p,R10_I2C_TIMINGR)==R10_I2C_TIMING &&
           !rd(p,R10_I2C_OAR1) && !rd(p,R10_I2C_OAR2) && !rd(p,R10_I2C_TIMEOUTR) &&
           !(rd(p,R10_I2C_CR2)&(R10_I2C_START|R10_I2C_STOP)) && pins_valid(p);
}
static uint32_t diagnostic(const r10_i2c_port *p) {
    return 0x80000000u|(p->stage<<16)|(p->last_isr&0xffffu);
}
static int status(r10_i2c_port *p,uint32_t *budget) {
    if (!*budget)return 1;
    --*budget;p->last_isr=rd(p,R10_I2C_ISR);
    /* Always reject faults before accepting even a simultaneously ready flag. */
    return (p->last_isr&(R10_I2C_ERRORS|R10_I2C_UNEXPECTED))!=0;
}
static int bus_free(r10_i2c_port *p,uint32_t *budget,int stopped) {
    while (*budget) {
        if (status(p,budget))return 1;
        if (p->last_isr&(R10_I2C_RXNE|R10_I2C_TXIS))return 1;
        if (!stopped && (p->last_isr&R10_I2C_STOPF))return 1;
        if (!(p->last_isr&R10_I2C_BUSY) &&
            (rd(p,R10_I2C_IDR)&R10_I2C_PINS)==R10_I2C_PINS)return 0;
    }
    return 1;
}
static int wait_byte(r10_i2c_port *p,uint32_t flag,uint32_t *budget) {
    while (*budget) {
        if (status(p,budget))return 1;
        if (p->last_isr&flag)return 0;
        if (p->last_isr&R10_I2C_STOPF)return 1; /* premature STOP */
    }
    return 1;
}
static void abort_i2c(r10_i2c_port *p,int started) {
    p->initialized=0;
    if (!(rd(p,R10_I2C_APB1LENR)&R10_I2C_ENABLE))return;
    uint32_t s=rd(p,R10_I2C_ISR);
    /* Do not generate STOP after arbitration loss or on somebody else's BUSY.
     * Mask START out of the write: a request bit is not ordinary RMW storage. */
    if (started && !((s|p->last_isr)&R10_I2C_ARLO) &&
        (s&R10_I2C_BUSY) && !(s&R10_I2C_STOPF) && (rd(p,R10_I2C_CR1)&R10_I2C_PE)) {
        wr(p,R10_I2C_CR2,(rd(p,R10_I2C_CR2)&~R10_I2C_START)|R10_I2C_STOP);
        for (unsigned i=0;i<R10_I2C_CLEANUP_POLLS;++i) {
            s=rd(p,R10_I2C_ISR);
            if ((s&(R10_I2C_STOPF|R10_I2C_ARLO)) || !(s&R10_I2C_BUSY))break;
        }
    }
    wr(p,R10_I2C_CR1,0);(void)rd(p,R10_I2C_CR1); /* RM0433 PE reset sequence. */
    reset_i2c(p); /* Local, finite, also flushes pending TX/RX on a stuck bus. */
}
int r10_i2c_initialize(void *context,uint32_t *hz,uint32_t *detail) {
    r10_i2c_port *p=context;
    if (hz)*hz=0;
    if (detail)*detail=0x80010000u;
    if (!hz || !detail || !adapter_valid(p))return 1;
    int previously_initialized=p->initialized;
    p->initialized=0;p->stage=R10_I2C_CLOCK;p->last_isr=0;
    p->transmitted=p->received=0;
    if (!clocks_valid(p)) {
        *detail=diagnostic(p);
        if (previously_initialized)abort_i2c(p,0);
        return 1;
    }
    p->stage=R10_I2C_CONFIG;
    modify(p,R10_I2C_AHB4ENR,R10_I2C_GPIO_ENABLE,R10_I2C_GPIO_ENABLE);
    if (!(rd(p,R10_I2C_AHB4ENR)&R10_I2C_GPIO_ENABLE))goto failure;
    modify(p,R10_I2C_APB1LENR,R10_I2C_ENABLE,R10_I2C_ENABLE);
    if (!(rd(p,R10_I2C_APB1LENR)&R10_I2C_ENABLE))goto failure;
    reset_i2c(p);
    wr(p,R10_I2C_CR1,0);(void)rd(p,R10_I2C_CR1);
    /* Park only PB8/9 in analog mode before setting open drain/AF4. R12/R13
     * pull up to 3V3; U5 VDD/PS are on 3V3A. No GPIOB ODR/BSRR access. */
    modify(p,R10_I2C_MODER,R10_I2C_PIN_FIELDS,R10_I2C_PIN_FIELDS);
    modify(p,R10_I2C_OTYPER,R10_I2C_PINS,R10_I2C_PINS);
    modify(p,R10_I2C_PUPDR,R10_I2C_PIN_FIELDS,0);
    modify(p,R10_I2C_OSPEEDR,R10_I2C_PIN_FIELDS,0);
    modify(p,R10_I2C_AFRH,R10_I2C_AF_MASK,R10_I2C_AF4);
    wr(p,R10_I2C_CR2,0);wr(p,R10_I2C_OAR1,0);wr(p,R10_I2C_OAR2,0);
    wr(p,R10_I2C_TIMEOUTR,0);wr(p,R10_I2C_TIMINGR,R10_I2C_TIMING);
    wr(p,R10_I2C_ICR,R10_I2C_CLEAR); /* W1C: never read ICR. */
    modify(p,R10_I2C_MODER,R10_I2C_PIN_FIELDS,R10_I2C_AF_MODE);
    wr(p,R10_I2C_CR1,R10_I2C_PE); /* analog filter ON, DNF=0, no DMA/IRQ */
    if (!config_valid(p))goto failure;
    p->stage=R10_I2C_INIT_IDLE;
    p->io.delay_cycles(p->io.context,R10_I2C_BUS_FREE_CYCLES);
    uint32_t budget=p->poll_limit;
    if (bus_free(p,&budget,0))goto failure;
    p->initialized=1;p->stage=0;*hz=R10_I2C_NOMINAL_HZ;*detail=0;return 0;
failure:
    *detail=diagnostic(p);abort_i2c(p,0);return 1;
}
int r10_i2c_transfer(void *context,uint8_t address,const uint8_t *tx,size_t tx_count,
                     uint8_t *rx,size_t rx_count,uint32_t *detail) {
    r10_i2c_port *p=context;
    if (detail)*detail=0x80050000u;
    if (!detail || !adapter_valid(p) || !p->initialized)return 1;
    /* Reject invalid shapes without MMIO or disturbing a usable port. */
    if (address!=R10_I2C_ADDRESS ||
        !((tx_count==1 && tx && rx_count==0) ||
          (tx_count==0 && rx && (rx_count==2 || rx_count==3))))return 1;
    p->transmitted=p->received=p->last_isr=0;p->stage=R10_I2C_CLOCK;
    int started=0;
    uint32_t budget=p->poll_limit;
    if (!clocks_valid(p))goto failure;
    p->stage=R10_I2C_CONFIG;
    if (!config_valid(p))goto failure;
    p->stage=R10_I2C_IDLE;
    /* At nominal 64 MHz, 512 NOPs alone exceed Standard-mode tBUF=4.7 us.
     * This guard is an assumption-dependent design allowance, not metrology. */
    p->io.delay_cycles(p->io.context,R10_I2C_BUS_FREE_CYCLES);
    if (bus_free(p,&budget,0))goto failure;
    uint32_t count=(uint32_t)(tx_count?tx_count:rx_count);
    wr(p,R10_I2C_CR2,((uint32_t)address<<1)|(count<<R10_I2C_NBYTES_SHIFT)|
       R10_I2C_AUTOEND|R10_I2C_START|(rx_count?R10_I2C_RD_WRN:0));
    started=1;
    if (tx_count) {
        p->stage=R10_I2C_TX;
        if (wait_byte(p,R10_I2C_TXIS,&budget))goto failure;
        p->io.write(p->io.context,R10_I2C_TXDR,tx[0],4);++p->transmitted;
    } else {
        p->stage=R10_I2C_RX;
        for (size_t i=0;i<rx_count;++i) {
            if (wait_byte(p,R10_I2C_RXNE,&budget))goto failure;
            rx[i]=(uint8_t)p->io.read(p->io.context,R10_I2C_RXDR,4);++p->received;
        }
    }
    p->stage=R10_I2C_WAIT_STOP;
    for (;;) {
        if (status(p,&budget))goto failure;
        if (p->last_isr&(R10_I2C_RXNE|R10_I2C_TXIS))goto failure;
        if (p->last_isr&R10_I2C_STOPF)break;
    }
    p->stage=R10_I2C_WAIT_BUSY;
    if (bus_free(p,&budget,1))goto failure;
    wr(p,R10_I2C_ICR,R10_I2C_STOPF);
    p->stage=R10_I2C_FINAL;
    if (status(p,&budget) || (p->last_isr&(R10_I2C_STOPF|R10_I2C_BUSY|R10_I2C_RXNE|R10_I2C_TXIS)) ||
        (rd(p,R10_I2C_IDR)&R10_I2C_PINS)!=R10_I2C_PINS)goto failure;
    wr(p,R10_I2C_CR2,0);
    p->stage=0;*detail=0;return 0;
failure:
    *detail=diagnostic(p);abort_i2c(p,started);return 1;
}
