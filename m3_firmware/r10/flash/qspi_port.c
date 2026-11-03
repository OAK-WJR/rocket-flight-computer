#include "qspi_port.h"
typedef struct {uint32_t base;unsigned pin,af;} pin;
static const pin pins[6]={
    {Q_GPIOB,2,9},{Q_GPIOD,11,9},{Q_GPIOD,12,9},
    {Q_GPIOE,2,9},{Q_GPIOD,13,9},{Q_GPIOB,6,10}
};
static int valid(const r10_qspi_port *p) {
    return p && p->io.read && p->io.write && p->io.prime;
}
static uint32_t read32(r10_qspi_port *p,uint32_t a) {return p->io.read(p->io.context,a,32);}
static void write32(r10_qspi_port *p,uint32_t a,uint32_t v) {p->io.write(p->io.context,a,v,32);}
static int fail(r10_qspi_port *p,uint32_t *detail,unsigned why) {
    if (p) {p->detail=(why<<24)|((p->phase&0xffu)<<16)|(p->last_sr&0xffffu);p->phase=Q_FAULT;}
    if (detail) *detail=p?p->detail:Q_FAIL_ADAPTER<<24;
    return FRO_ERROR;
}
static int field(r10_qspi_port *p,uint32_t addr,uint32_t mask,uint32_t value) {
    uint32_t before=read32(p,addr);write32(p,addr,(before&~mask)|(value&mask));
    return read32(p,addr)==((before&~mask)|(value&mask));
}
static int clock_ok(r10_qspi_port *p) {
    /* Explicit nominal HSI64/HCLK64 policy. Leave shared clock selectors alone.
     * /64 serial clock respects ES0392 2.7.6 even when using HCLK as kernel. */
    return (read32(p,Q_RCC_CR)&0x1du)==5u && !(read32(p,Q_CFGR)&0x3fu) &&
           !(read32(p,Q_D1CFGR)&0xf0fu) && !(read32(p,Q_D1CCIPR)&0x30u);
}
static int parked_pin(r10_qspi_port *p,pin q) {
    unsigned mode=(read32(p,q.base+Q_MODER)>>(2*q.pin))&3u;
    return mode==0u || mode==3u ||
           (p->parked && q.base==Q_GPIOB && q.pin==6u && mode==1u &&
            (read32(p,Q_GPIOB+Q_ODR)&64u));
}
static int park(r10_qspi_port *p) {
    /* Set ODR before selecting output, so moving NCS out of AF can only
     * release a read. Never issue RESET, WAKE, WREN, PROGRAM or ERASE. */
    write32(p,Q_GPIOB+Q_BSRR,64u);
    if (!(read32(p,Q_GPIOB+Q_ODR)&64u)) return 0;
    if (!field(p,Q_GPIOB+Q_OTYPER,64u,0u) ||
        !field(p,Q_GPIOB+Q_SPEED,3u<<12,0u) ||
        !field(p,Q_GPIOB+Q_PULL,3u<<12,0u) ||
        !field(p,Q_GPIOB+Q_MODER,3u<<12,1u<<12)) return 0;
    for (unsigned i=0;i<5u;++i) {
        pin q=pins[i];unsigned shift=2*q.pin;
        if (!field(p,q.base+Q_PULL,3u<<shift,0u) ||
            !field(p,q.base+Q_MODER,3u<<shift,3u<<shift)) return 0;
    }
    p->parked=1u;
    return (read32(p,Q_GPIOB+Q_IDR)&64u)!=0u;
}
static int configure_pins(r10_qspi_port *p) {
    for (unsigned i=0;i<6u;++i) {
        pin q=pins[i];unsigned shift=2*q.pin,afshift=4*(q.pin%8);
        uint32_t afr=q.base+(q.pin<8u?Q_AFRL:Q_AFRH);
        if (!field(p,q.base+Q_OTYPER,1u<<q.pin,0u) ||
            !field(p,q.base+Q_SPEED,3u<<shift,0u) ||
            !field(p,q.base+Q_PULL,3u<<shift,0u) ||
            !field(p,afr,15u<<afshift,q.af<<afshift) ||
            !field(p,q.base+Q_MODER,3u<<shift,2u<<shift)) return 0;
    }
    p->parked=0u;return 1;
}
static int pins_ok(r10_qspi_port *p) {
    for (unsigned i=0;i<6u;++i) {
        pin q=pins[i];unsigned shift=2*q.pin,afshift=4*(q.pin%8);
        uint32_t afr=q.base+(q.pin<8u?Q_AFRL:Q_AFRH);
        if ((read32(p,q.base+Q_MODER)&(3u<<shift))!=(2u<<shift) ||
            (read32(p,q.base+Q_OTYPER)&(1u<<q.pin)) ||
            (read32(p,q.base+Q_SPEED)&(3u<<shift)) ||
            (read32(p,q.base+Q_PULL)&(3u<<shift)) ||
            (read32(p,afr)&(15u<<afshift))!=(q.af<<afshift)) return 0;
    }
    return 1;
}
static unsigned configuration(r10_qspi_port *p) {
    if (!clock_ok(p)) return Q_FAIL_CLOCK;
    if (!(read32(p,Q_ENABLE)&Q_GATE) ||
        (read32(p,Q_GPIO_ENABLE)&Q_GPIO_GATES)!=Q_GPIO_GATES ||
        (read32(p,Q_RESET)&Q_GATE)) return Q_FAIL_ENABLE;
    if (!pins_ok(p)) return Q_FAIL_GPIO;
    p->last_cr=read32(p,Q_BASE+Q_CR);
    if (p->last_cr!=Q_CONTROL || read32(p,Q_BASE+Q_DCR)!=Q_DEVICE) return Q_FAIL_CONFIG;
    return 0;
}
int r10_qspi_initialize(void *context,uint32_t now,uint32_t *hz,uint32_t *detail) {
    r10_qspi_port *p=context;
    if (hz) *hz=0;
    if (detail) *detail=0;
    if (!valid(p) || !hz || !detail) return fail(p,detail,Q_FAIL_ADAPTER);
    if (!clock_ok(p)) return fail(p,detail,Q_FAIL_CLOCK);
    if (p->phase==Q_NEW) {
        uint32_t id=read32(p,Q_ID);p->revision=id>>16;
        if ((id&0xfffu)!=0x450u || (p->revision!=0x1003u && p->revision!=0x2001u &&
            p->revision!=0x2003u && p->revision!=0x2007u)) return fail(p,detail,Q_FAIL_ID);
        if ((read32(p,Q_ENABLE)&Q_GATE) || (read32(p,Q_RESET)&Q_GATE)) return fail(p,detail,Q_FAIL_OWNERSHIP);
        if (!field(p,Q_GPIO_ENABLE,Q_GPIO_GATES,Q_GPIO_GATES)) return fail(p,detail,Q_FAIL_ENABLE);
        for (unsigned i=0;i<6u;++i) if (!parked_pin(p,pins[i])) return fail(p,detail,Q_FAIL_OWNERSHIP);
        p->owned=1u;
        if (!park(p)) return fail(p,detail,Q_FAIL_GPIO);
        if (!field(p,Q_ENABLE,Q_GATE,Q_GATE)) return fail(p,detail,Q_FAIL_ENABLE);
        if (!field(p,Q_RESET,Q_GATE,Q_GATE)) return fail(p,detail,Q_FAIL_RESET);
        p->phase=Q_RESET_HELD;p->phase_ms=now;return FRO_BUSY;
    }
    if (!p->owned || !(read32(p,Q_ENABLE)&Q_GATE)) return fail(p,detail,Q_FAIL_OWNERSHIP);
    if ((read32(p,Q_GPIO_ENABLE)&Q_GPIO_GATES)!=Q_GPIO_GATES) return fail(p,detail,Q_FAIL_ENABLE);
    if (!!(read32(p,Q_RESET)&Q_GATE)!=(p->phase==Q_RESET_HELD)) return fail(p,detail,Q_FAIL_RESET);
    if (p->phase==Q_RESET_HELD) {
        if ((uint32_t)(now-p->phase_ms)<1u) return FRO_BUSY;
        if (!field(p,Q_RESET,Q_GATE,0u)) return fail(p,detail,Q_FAIL_RESET);
        p->phase=Q_RESET_RELEASED;return FRO_BUSY;
    }
    if (p->phase==Q_RESET_RELEASED) {
        p->last_cr=read32(p,Q_BASE+Q_CR);p->last_sr=read32(p,Q_BASE+Q_SR);
        if (p->last_cr || p->last_sr || read32(p,Q_BASE+Q_CCR)) return fail(p,detail,Q_FAIL_RESET);
        if (!p->parked || p->io.prime(p->io.context)!=FRO_OK) return fail(p,detail,Q_FAIL_TIMING);
        p->phase=Q_PRIMED;return FRO_BUSY;
    }
    if (p->phase==Q_PRIMED) {
        p->last_sr=read32(p,Q_BASE+Q_SR);p->last_cr=read32(p,Q_BASE+Q_CR);
        if (p->last_cr || p->last_sr) return fail(p,detail,Q_FAIL_TIMING);
        /* Remove FRCM while the external pins are still parked. Clearing CCR
         * itself has ES0392 2.7.3's BUSY hazard: explicitly clear/set EN after
         * that write and require an idle readback before exposing AF pins. */
        write32(p,Q_BASE+Q_CCR,0u);write32(p,Q_BASE+Q_CR,0u);
        write32(p,Q_BASE+Q_DCR,Q_DEVICE);write32(p,Q_BASE+Q_CR,Q_CONTROL);
        p->last_sr=read32(p,Q_BASE+Q_SR);
        if (p->last_sr) return fail(p,detail,Q_FAIL_TIMING);
        if (!configure_pins(p)) return fail(p,detail,Q_FAIL_GPIO);
        unsigned error=configuration(p);if (error) return fail(p,detail,error);
        if (!(read32(p,Q_GPIOB+Q_IDR)&64u)) return fail(p,detail,Q_FAIL_GPIO);
        p->phase=Q_READY;p->nominal_hz=1000000u;*hz=p->nominal_hz;return FRO_OK;
    }
    if (p->phase==Q_READY && !p->active) {
        unsigned error=configuration(p);if (error) return fail(p,detail,error);
        *hz=p->nominal_hz;return FRO_OK;
    }
    return fail(p,detail,Q_FAIL_CONFIG);
}
static uint32_t lines(unsigned n) {return n==4u?3u:n==1u?1u:0u;}
int r10_qspi_start(void *context,unsigned command,uint32_t *detail) {
    r10_qspi_port *p=context;
    if (detail) *detail=0;
    if (!valid(p) || !detail) return fail(p,detail,Q_FAIL_ADAPTER);
    const r10_flash_ro_command *c=r10_flash_ro_descriptor(command);
    if (!c || p->phase!=Q_READY || !p->owned || p->active) return fail(p,detail,Q_FAIL_ARGUMENT);
    unsigned error=configuration(p);if (error) return fail(p,detail,error);
    p->last_sr=read32(p,Q_BASE+Q_SR);
    if (p->last_sr || !(read32(p,Q_GPIOB+Q_IDR)&64u)) return fail(p,detail,Q_FAIL_STATUS);
    p->expected_dlr=c->length-1u;
    p->expected_ccr=c->opcode|0x100u|(lines(c->address_lines)<<10)|
        ((c->address_bits?2u:0u)<<12)|(lines(c->alternate_lines)<<14)|
        ((uint32_t)c->dummy_cycles<<18)|(lines(c->data_lines)<<24)|0x04000000u;
    /* 8-bit alternate size encodes zero. SIOO=0: send each opcode anew. */
    write32(p,Q_BASE+Q_DLR,p->expected_dlr);write32(p,Q_BASE+Q_ABR,c->alternate_value);
    if (read32(p,Q_BASE+Q_DLR)!=p->expected_dlr ||
        read32(p,Q_BASE+Q_ABR)!=c->alternate_value) return fail(p,detail,Q_FAIL_CONFIG);
    p->command=command;p->received=0u;p->active=1u;
    write32(p,Q_BASE+Q_CCR,p->expected_ccr);
    p->last_ccr=read32(p,Q_BASE+Q_CCR);
    if (p->last_ccr!=p->expected_ccr) return fail(p,detail,Q_FAIL_START);
    if (c->address_bits) write32(p,Q_BASE+Q_AR,0u);
    return FRO_OK;
}
int r10_qspi_poll(void *context,uint8_t *out,uint32_t capacity,uint32_t *received,uint32_t *detail) {
    r10_qspi_port *p=context;
    if (received) *received=0;
    if (detail) *detail=0;
    if (!valid(p) || !detail || !received) return fail(p,detail,Q_FAIL_ADAPTER);
    if (p->phase!=Q_READY || !p->active || p->command>=FRO_COMMANDS || capacity>FRO_BYTES_MAX ||
        (capacity && !out)) return fail(p,detail,Q_FAIL_ARGUMENT);
    unsigned error=configuration(p);if (error) return fail(p,detail,error);
    const r10_flash_ro_command *c=r10_flash_ro_descriptor(p->command);
    p->last_ccr=read32(p,Q_BASE+Q_CCR);
    if (p->last_ccr!=p->expected_ccr || read32(p,Q_BASE+Q_DLR)!=p->expected_dlr)
        return fail(p,detail,Q_FAIL_CONFIG);
    p->last_sr=read32(p,Q_BASE+Q_SR);
    if (p->last_sr&Q_ERRORS) return fail(p,detail,Q_FAIL_STATUS);
    unsigned count=(p->last_sr&Q_LEVEL)>>8;
    if (p->received>c->length || count>32u || count>c->length-p->received)
        return fail(p,detail,Q_FAIL_COUNT);
    unsigned take=count<capacity?count:capacity;
    for (unsigned i=0;i<take;++i) {
        p->last_dr=p->io.read(p->io.context,Q_BASE+Q_DR,8u);
        if (p->last_dr>255u) return fail(p,detail,Q_FAIL_DATA);
        out[i]=(uint8_t)p->last_dr;++*received;++p->received;
        p->last_sr=read32(p,Q_BASE+Q_SR);
        if (p->last_sr&Q_ERRORS) return fail(p,detail,Q_FAIL_STATUS);
    }
    p->last_sr=read32(p,Q_BASE+Q_SR);
    if (p->last_sr&Q_ERRORS) return fail(p,detail,Q_FAIL_STATUS);
    count=(p->last_sr&Q_LEVEL)>>8;
    if (count>32u || count>c->length-p->received) return fail(p,detail,Q_FAIL_COUNT);
    if (!(p->last_sr&Q_TCF) || (p->last_sr&Q_BUSY)) return FRO_BUSY;
    if (count || p->received!=c->length) return fail(p,detail,Q_FAIL_COUNT);
    if (!(read32(p,Q_GPIOB+Q_IDR)&64u)) return fail(p,detail,Q_FAIL_GPIO);
    write32(p,Q_BASE+Q_FCR,Q_TCF);
    p->last_sr=read32(p,Q_BASE+Q_SR);
    if (p->last_sr) return fail(p,detail,Q_FAIL_STATUS);
    p->active=0u;return FRO_OK;
}
int r10_qspi_cancel(void *context,uint32_t *detail) {
    r10_qspi_port *p=context;
    if (detail) *detail=0;
    if (!valid(p) || !detail) return fail(p,detail,Q_FAIL_ADAPTER);
    if (!p->owned) {p->active=0u;return FRO_OK;}
    /* Do not spin on ABORT/BUSY. Park NCS high, reset only the owned QSPI,
     * then certify the reset/idle readback. Failure is terminal in the core. */
    if ((read32(p,Q_GPIO_ENABLE)&Q_GPIO_GATES)!=Q_GPIO_GATES || !park(p))
        return fail(p,detail,Q_FAIL_CLEANUP);
    if (!(read32(p,Q_ENABLE)&Q_GATE)) return fail(p,detail,Q_FAIL_CLEANUP);
    write32(p,Q_BASE+Q_CR,0u);
    if (!field(p,Q_RESET,Q_GATE,Q_GATE) || !field(p,Q_RESET,Q_GATE,0u))
        return fail(p,detail,Q_FAIL_CLEANUP);
    p->last_cr=read32(p,Q_BASE+Q_CR);p->last_sr=read32(p,Q_BASE+Q_SR);
    if (p->last_cr || p->last_sr || read32(p,Q_BASE+Q_CCR) ||
        !field(p,Q_ENABLE,Q_GATE,0u)) return fail(p,detail,Q_FAIL_CLEANUP);
    p->owned=p->active=0u;p->phase=Q_NEW;p->nominal_hz=0u;return FRO_OK;
}
