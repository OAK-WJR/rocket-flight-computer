/* Scripted peripheral register/FIFO model. No physical SPI/clock/GPIO model.
 * Register semantics: ST RM0433 Rev 8, SPI_CR1/SR/IFCR; pinned bit definitions
 * in vendor/device/Include/stm32h743xx.h. Errata: ES0392 Rev 16 2.22.2/.4/.5/.6.
 * https://www.st.com/resource/en/reference_manual/rm0433-stm32h742-stm32h743753-and-stm32h750-value-line-advanced-armbased-32bit-mcus-stmicroelectronics.pdf
 * Status-read steps advance scripted frames, not elapsed hardware time.
 */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "spi_port.h"

enum {
    SPE=1u, CSTART=0x200u, CSUSP=0x400u, SSI=0x1000u, CS=0x80u,
    RXP=1u, TXP=2u, DXP=4u, EOT=8u, TXTF=0x10u,
    OVR=0x40u, CRCE=0x80u, MODF=0x200u, SUSP=0x800u,
    CLEARABLE=0xff8u, SPI1_RESET=0x1000u
};
enum fault_point { NO_FAULT, TX_WAIT, RX_WAIT, FINAL_RX_WAIT, EOT_WAIT };
enum event_kind { STATUS, RX_READ, DELAY, CS_LOW, CS_HIGH, ENABLE, DISABLE,
                  START, SUSPEND_REQUEST, RESET };
typedef struct {
    enum event_kind kind;
    uint32_t value, cr1, odr, completed, received, unread;
} event;
typedef struct {
    uint32_t values[32], seeds[32], odr, tx, completed, rx, expected;
    uint32_t reads, writes, resets, delay_total, latched;
    /* Bounded script storage, not a claim about hardware FIFO depth. */
    uint8_t tx_data[33], rx_data[34];
    unsigned tx_pending, rx_pending, rx_head, rx_tail;
    uint32_t fault, fault_sr;
    enum fault_point fault_at;
    int fault_fired, suspend_pending;
    int stall_tx, stall_rx, stall_eot, extra_rx, short_cs, bad_cfg, suspend_fails;
    event events[512];
    unsigned event_count;
} model;
static const uint32_t addresses[]={R10_CR,R10_D1CCIPR,R10_D2CCIP1R,R10_APB2RSTR,
 R10_AHB4ENR,R10_APB2ENR,R10_MODER,R10_OTYPER,R10_OSPEEDR,R10_PUPDR,
 R10_IDR,R10_BSRR,R10_AFRL,R10_SPI_CR1,R10_SPI_CR2,R10_CFG1,R10_CFG2,
 R10_IER,R10_SR,R10_IFCR,R10_TXDR,R10_RXDR,R10_I2SCFGR};
/* Seed real writable fields, including both set and clear unrelated bits.
 * In particular APB2RSTR bit 31 and OTYPER bits 31:16 are reserved, not seeds. */
static const struct { uint32_t address, seed, owned; } preserved[]={
    {R10_CR,        0x00011287u, 0x00000001u},
    {R10_D1CCIPR,   0x20010021u, 0x30000000u},
    {R10_D2CCIP1R,  0x91133042u, 0x00007000u},
    {R10_APB2RSTR,  0x00402021u, 0x00001000u},
    {R10_AHB4ENR,   0x13280415u, 0x00000002u},
    {R10_APB2ENR,   0x00502021u, 0x00001000u},
    {R10_MODER,    0xa5a5a5a5u, 0x0000cfc0u},
    {R10_OTYPER,   0x00005555u, 0x000000b8u},
    {R10_OSPEEDR,  0xaaaa5555u, 0x0000cfc0u},
    {R10_PUPDR,    0x99999999u, 0x0000cfc0u},
    {R10_AFRL,     0x12345678u, 0x00fff000u}
};
static const uint32_t odr_seed=0x5a25u;

static unsigned index_of(uint32_t address) {
    for(unsigned i=0;i<sizeof addresses/sizeof *addresses;++i)
        if(addresses[i]==address)return i;
    assert(!"MMIO address escaped sensor/RCC allowlist");return 0;
}
static uint32_t get(model *m,uint32_t a) {return m->values[index_of(a)];}
static void set(model *m,uint32_t a,uint32_t v) {m->values[index_of(a)]=v;}
static void seed(model *m,uint32_t a,uint32_t v) {
    set(m,a,v);m->seeds[index_of(a)]=v;
}
static void record(model *m,enum event_kind kind,uint32_t value) {
    assert(m->event_count<sizeof m->events/sizeof *m->events);
    m->events[m->event_count++]=(event){kind,value,get(m,R10_SPI_CR1),m->odr,
                                     m->completed,m->rx,m->rx_pending};
}
static void assert_preserved(model *m) {
    for(unsigned i=0;i<sizeof preserved/sizeof *preserved;++i)
        assert((get(m,preserved[i].address)&~preserved[i].owned)==
               (m->seeds[index_of(preserved[i].address)]&~preserved[i].owned));
    assert((m->odr&~CS)==(odr_seed&~CS));
}
static void flush_fifos(model *m) {
    m->tx_pending=m->rx_pending=m->rx_head=m->rx_tail=0;
    memset(m->tx_data,0,sizeof m->tx_data);
    memset(m->rx_data,0,sizeof m->rx_data);
    m->suspend_pending=0;
}
static void latch(model *m,uint32_t flags) {
    m->latched|=flags;
    if(flags&(EOT|SUSP))set(m,R10_SPI_CR1,get(m,R10_SPI_CR1)&~CSTART);
    if(flags&MODF) {
        /* Mode fault clears SPE/IOLOCK and consequently flushes the FIFOs. */
        set(m,R10_SPI_CR1,get(m,R10_SPI_CR1)&~(SPE|CSTART|0x10000u));
        flush_fifos(m);
    }
}
static void complete_frame(model *m) {
    if(!(get(m,R10_SPI_CR1)&CSTART) || !m->tx_pending || m->stall_rx)return;
    assert(m->completed<m->tx && m->rx_tail<sizeof m->rx_data);
    m->rx_data[m->rx_tail++]=(uint8_t)(m->tx_data[m->completed]^0x5au);
    --m->tx_pending;++m->rx_pending;++m->completed;
    if(m->completed==m->expected) {
        if(!m->stall_eot)latch(m,EOT);
        if(m->extra_rx) {
            assert(m->rx_tail<sizeof m->rx_data);
            m->rx_data[m->rx_tail++]=0xeeu;++m->rx_pending;
        }
    }
}
static int inject_now(model *m) {
    if(!m->expected || !m->fault || m->fault_fired)return 0;
    switch(m->fault_at) {
    case TX_WAIT:return m->tx==0;
    case RX_WAIT:return m->tx==1 && m->rx==0;
    case FINAL_RX_WAIT:return m->completed==m->expected && m->rx+1==m->expected;
    case EOT_WAIT:return m->completed==m->expected && m->rx==m->expected;
    default:return 0;
    }
}
static uint32_t read_mmio(void *ctx,uint32_t a,unsigned width) {
    model *m=ctx;m->reads++;assert(m->reads<100000u);
    if(a==R10_RXDR) {
        assert(width==1);
        if(!(get(m,R10_SPI_CR1)&SPE))return 0;
        assert(m->rx_pending);
        uint8_t value=m->rx_data[m->rx_head++];
        --m->rx_pending;++m->rx;record(m,RX_READ,value);return value;
    }
    assert(width==4);
    assert(a!=R10_IFCR); /* Driver must directly write W1C, never RMW it. */
    if(a==R10_IDR)return m->short_cs?m->odr&~CS:m->odr;
    if(a==R10_CFG1 && m->bad_cfg)return get(m,a)^1u;
    if(a==R10_SPI_CR1)return get(m,a)&~CSUSP;
    if(a==R10_SR) {
        complete_frame(m);
        if(m->suspend_pending && !m->suspend_fails) {
            m->suspend_pending=0;latch(m,SUSP);
        }
        int injected=inject_now(m);
        if(injected) {m->fault_fired=1;latch(m,m->fault);}
        uint32_t flags=m->latched;
        /* ES0392 2.22.4: TXP can also be set with SPE disabled. */
        if(!m->stall_tx)flags|=TXP;
        if((get(m,R10_SPI_CR1)&SPE) && m->rx_pending)flags|=RXP;
        if((flags&(TXP|RXP))==(TXP|RXP))flags|=DXP;
        if(injected)m->fault_sr=flags;
        record(m,STATUS,flags);return flags;
    }
    return get(m,a);
}
static void write_mmio(void *ctx,uint32_t a,uint32_t v,unsigned width) {
    model *m=ctx;m->writes++;
    if(a==R10_TXDR) {
        assert(width==1 && (get(m,R10_SPI_CR1)&(SPE|CSTART))==(SPE|CSTART));
        assert(!(m->odr&CS) && m->tx<m->expected && m->tx<sizeof m->tx_data);
        m->tx_data[m->tx++]=(uint8_t)v;++m->tx_pending;
        if(m->tx==m->expected)latch(m,TXTF);
        return;
    }
    assert(width==4);
    if(a==R10_IFCR) {m->latched&=~(v&CLEARABLE);return;}
    uint32_t old=get(m,a);
    if(a==R10_SPI_CR1) {
        set(m,a,v&~CSUSP); /* CSUSP is a request, never readable storage. */
        if(!(v&SPE)) {
            set(m,a,get(m,a)&~CSTART);flush_fifos(m);
            if(old&SPE)record(m,DISABLE,0);
        } else {
            assert(!(m->latched&MODF));
            if(!(old&SPE))record(m,ENABLE,0);
            if((v&CSTART) && !(old&CSTART)) {
                m->expected=get(m,R10_SPI_CR2)&0xffffu;
                assert(m->expected && !m->tx_pending && !m->rx_pending);
                m->tx=m->completed=m->rx=0;m->rx_head=m->rx_tail=0;
                record(m,START,m->latched);
            }
            if(v&CSUSP) {m->suspend_pending=1;record(m,SUSPEND_REQUEST,0);}
        }
    } else {
        set(m,a,v);
    }
    if(a==R10_BSRR) {
        /* BSRR set wins if both halves address the same pin. */
        m->odr=(m->odr&~(v>>16))|(v&0xffffu);
        record(m,(m->odr&CS)?CS_HIGH:CS_LOW,v);
    }
    if(a==R10_APB2RSTR && (v&SPI1_RESET) && !(old&SPI1_RESET)) {
        m->resets++;m->tx=m->completed=m->rx=m->expected=m->latched=0;
        flush_fifos(m);
        for(unsigned i=0;i<sizeof addresses/sizeof *addresses;++i)
            if(addresses[i]>=R10_SPI1 && addresses[i]<R10_SPI1+84)m->values[i]=0;
        record(m,RESET,0);
    }
    assert_preserved(m); /* Catch transient clobbers too, including reset pulses. */
}
static void delay(void *ctx,unsigned cycles) {
    model *m=ctx;m->delay_total+=cycles;record(m,DELAY,cycles);
}
static r10_spi_port port(model *m) {
    memset(m,0,sizeof(*m));m->odr=odr_seed;
    for(unsigned i=0;i<sizeof preserved/sizeof *preserved;++i)
        seed(m,preserved[i].address,preserved[i].seed);
    return (r10_spi_port){.io={m,read_mmio,write_mmio,delay},.poll_limit=256};
}
static void initialized(model *m,r10_spi_port *p) {
    uint32_t hz=0,detail=1;
    assert(r10_spi_initialize(p,&hz,&detail)==0 && hz==1000000u && detail==0 && p->initialized);
    assert(get(m,R10_CFG1)==R10_SPI_CONFIG1 && get(m,R10_CFG2)==R10_SPI_CONFIG2);
    assert((get(m,R10_CR)&1u) && (get(m,R10_AHB4ENR)&2u));
    assert((get(m,R10_APB2ENR)&SPI1_RESET) && !(get(m,R10_APB2RSTR)&SPI1_RESET));
    assert(!(get(m,R10_D1CCIPR)&0x30000000u));
    assert((get(m,R10_D2CCIP1R)&0x7000u)==0x4000u);
    assert((get(m,R10_MODER)&0xcfc0u)==0x4a80u);
    assert((get(m,R10_AFRL)&0xfff000u)==0x555000u);
    assert(!(get(m,R10_OTYPER)&0xb8u) && !(get(m,R10_OSPEEDR)&0xcfc0u));
    assert(!(get(m,R10_PUPDR)&0xcfc0u) && (m->odr&CS));
    assert(!m->latched && !m->tx_pending && !m->rx_pending);
    assert_preserved(m);
}
static unsigned only_event(model *m,enum event_kind kind) {
    unsigned found=m->event_count;
    for(unsigned i=0;i<m->event_count;++i)if(m->events[i].kind==kind) {
        assert(found==m->event_count);found=i;
    }
    assert(found<m->event_count);return found;
}
static void successful(model *m,r10_spi_port *p,unsigned n,unsigned pattern) {
    uint8_t tx[33],rx[33];
    for(unsigned i=0;i<sizeof tx;++i)tx[i]=(uint8_t)(pattern+7u*i);
    memset(rx,0xa5,sizeof rx);
    uint32_t detail=1,delay_before=m->delay_total,resets=m->resets;
    m->event_count=0;
    assert(r10_spi_exchange(p,tx,rx,n,&detail)==0 && detail==0 && p->initialized);
    for(unsigned i=0;i<n;++i)assert(rx[i]==(uint8_t)(tx[i]^0x5au));
    assert(m->tx==n && m->completed==n && m->rx==n);
    assert(p->transmitted==n && p->received==n && !p->stage);
    assert(m->delay_total-delay_before==192u && (m->odr&CS));
    assert(!(get(m,R10_SPI_CR1)&(SPE|CSTART|CSUSP)) && get(m,R10_IER)==0);
    assert(!m->latched && !m->tx_pending && !m->rx_pending && m->resets==resets);
    assert_preserved(m);

    unsigned enabled=only_event(m,ENABLE),low=only_event(m,CS_LOW);
    unsigned start=only_event(m,START),high=only_event(m,CS_HIGH),off=only_event(m,DISABLE);
    unsigned early=m->event_count,observed=m->event_count,guard=m->event_count,last_rx=0;
    assert(enabled<low && low<start && !m->events[start].value);
    for(unsigned i=0;i<m->event_count;++i) {
        event *e=&m->events[i];
        if(e->kind==RX_READ)last_rx=i;
        if(e->kind==STATUS && (e->value&EOT)) {
            assert(e->completed==n && !(e->cr1&CSTART));
            observed=i;
            if(e->unread) {
                assert((e->value&(RXP|TXTF))==(RXP|TXTF));
                assert(e->received==n-1 && e->unread==1);early=i;
            }
        }
        if(e->kind==DELAY && e->value==128u) {
            assert(guard==m->event_count);guard=i;
            assert(!(e->odr&CS) && (e->cr1&SPE) && !e->unread);
        }
    }
    /* An observed EOT with RX unread must precede the final read. The final
     * observed EOT must precede the 128-NOP request, CS high, then SPE clear. */
    assert(early<last_rx && last_rx<observed && observed<guard && guard<high && high<off);
    assert(m->events[high].cr1&SPE);
}

static void test_model_register_semantics(void) {
    model m;r10_spi_port p=port(&m);initialized(&m,&p);
    write_mmio(&m,R10_SPI_CR2,2,4);write_mmio(&m,R10_SPI_CR1,SSI|SPE,4);
    write_mmio(&m,R10_BSRR,CS<<16,4);write_mmio(&m,R10_SPI_CR1,SSI|SPE|CSTART,4);
    write_mmio(&m,R10_TXDR,0x11,1);write_mmio(&m,R10_TXDR,0x22,1);
    assert(m.tx==2 && !m.completed && !m.rx && m.latched==TXTF);
    assert(!(read_mmio(&m,R10_SR,4)&EOT) && m.completed==1 && m.rx_pending==1);
    assert((read_mmio(&m,R10_SR,4)&(EOT|TXTF|RXP))==(EOT|TXTF|RXP));
    assert(m.completed==2 && !m.rx && m.rx_pending==2);
    assert(!(read_mmio(&m,R10_SPI_CR1,4)&CSTART));
    write_mmio(&m,R10_IFCR,0,4);assert(m.latched==(EOT|TXTF));
    write_mmio(&m,R10_IFCR,EOT,4);assert(m.latched==TXTF);
    latch(&m,OVR|CRCE);
    write_mmio(&m,R10_IFCR,OVR|RXP,4);
    assert((read_mmio(&m,R10_SR,4)&CLEARABLE)==(TXTF|CRCE));
    assert((read_mmio(&m,R10_SR,4)&CLEARABLE)==(TXTF|CRCE));
    assert(read_mmio(&m,R10_RXDR,1)==(0x11u^0x5au) && m.rx_pending==1);
    write_mmio(&m,R10_IFCR,CLEARABLE,4);
    assert((read_mmio(&m,R10_SR,4)&(CLEARABLE|RXP))==RXP); /* no re-latching */
    write_mmio(&m,R10_SPI_CR1,SSI,4);
    assert(!m.rx_pending && !m.tx_pending && read_mmio(&m,R10_RXDR,1)==0);
    assert(!(read_mmio(&m,R10_SR,4)&RXP) && get(&m,R10_CFG1)==R10_SPI_CONFIG1);

    /* Disable also drops a queued TX frame alongside unread RX data. */
    write_mmio(&m,R10_SPI_CR2,3,4);write_mmio(&m,R10_SPI_CR1,SSI|SPE|CSTART,4);
    write_mmio(&m,R10_TXDR,0x33,1);write_mmio(&m,R10_TXDR,0x44,1);
    (void)read_mmio(&m,R10_SR,4);assert(m.tx_pending==1 && m.rx_pending==1);
    latch(&m,OVR);write_mmio(&m,R10_SPI_CR1,SSI,4);
    assert(!m.tx_pending && !m.rx_pending && m.latched==OVR);
    write_mmio(&m,R10_IFCR,OVR,4);write_mmio(&m,R10_SPI_CR1,SSI|SPE|CSTART,4);
    assert(!(read_mmio(&m,R10_SR,4)&RXP) && !m.completed);
    write_mmio(&m,R10_SPI_CR1,SSI|SPE|CSTART|CSUSP,4);
    assert(!(read_mmio(&m,R10_SPI_CR1,4)&CSUSP) && m.suspend_pending);
    assert(read_mmio(&m,R10_SR,4)&SUSP);
    assert(!(read_mmio(&m,R10_SPI_CR1,4)&(CSUSP|CSTART)) && !m.suspend_pending);
    write_mmio(&m,R10_IFCR,SUSP,4);
    assert(!(read_mmio(&m,R10_SR,4)&SUSP)); /* request was consumed only once */
    assert_preserved(&m);
}

static void test_stage_errors(void) {
    const uint32_t errors[]={0x20u,OVR,CRCE,0x100u,MODF,SUSP};
    const uint32_t stages[]={0,5,6,6,7},sent[]={0,0,1,3,3},received[]={0,0,0,2,3};
    uint8_t tx[]={0x11,0x22,0x33},rx[3];
    /* Deliberately injected SR faults exercise defensive handling even for
     * errors not normally reachable in this master/CRC-disabled configuration. */
    for(unsigned point=TX_WAIT;point<=EOT_WAIT;++point)
    for(unsigned i=0;i<sizeof errors/sizeof *errors;++i)
    for(unsigned failed_suspend=0;failed_suspend<2;++failed_suspend) {
        model m;r10_spi_port p=port(&m);initialized(&m,&p);
        m.fault=errors[i];m.fault_at=(enum fault_point)point;m.suspend_fails=(int)failed_suspend;
        m.event_count=0;uint32_t detail=0;unsigned reads=m.reads;
        assert(r10_spi_exchange(&p,tx,rx,3,&detail)!=0 && !p.initialized);
        assert(m.fault_fired && (detail&0x80000000u));
        assert(((detail>>16)&0xffu)==stages[point] && (detail&0xffffu)==m.fault_sr);
        assert((detail&errors[i])==errors[i]);
        uint32_t ready=point==TX_WAIT?TXP:point==EOT_WAIT?EOT:RXP;
        if(errors[i]!=MODF || ready!=RXP)assert(detail&ready); /* ready must not hide error */
        assert(p.transmitted==sent[point] && p.received==received[point]);
        assert(m.reads-reads<800 && m.resets==2 && (m.odr&CS));
        assert(!m.latched && !m.tx_pending && !m.rx_pending && !(get(&m,R10_SPI_CR1)&SPE));
        assert(only_event(&m,CS_HIGH)<only_event(&m,RESET));
        assert_preserved(&m);
        /* Removing the fault is insufficient: only explicit init recovers. */
        m.fault=0;m.fault_at=NO_FAULT;m.suspend_fails=0;
        unsigned writes=m.writes;reads=m.reads;
        assert(r10_spi_exchange(&p,tx,rx,3,&detail)!=0 && m.writes==writes && m.reads==reads);
        initialized(&m,&p);assert(m.resets==3);
        successful(&m,&p,3,0x41);successful(&m,&p,3,0x87);
    }
}

int main(void) {
    test_model_register_semantics();test_stage_errors();
    model m;r10_spi_port p=port(&m);initialized(&m,&p);
    /* Consecutive transactions, no model reset or re-init between successes. */
    for(unsigned n=2;n<=33;++n) {
        successful(&m,&p,n,n);successful(&m,&p,n,0x80u+n);
    }
    uint8_t tx[34]={0},rx[34]={0};uint32_t detail=0;
    for(unsigned kind=0;kind<4;++kind) {
        p=port(&m);initialized(&m,&p);
        if(kind==0)m.stall_tx=1;
        if(kind==1)m.stall_rx=1;
        if(kind==2)m.stall_eot=1;
        if(kind==3)m.extra_rx=1;
        unsigned reads=m.reads;
        assert(r10_spi_exchange(&p,tx,rx,3,&detail)!=0 && !p.initialized && (m.odr&CS));
        assert(m.reads-reads<800 && m.resets==2); /* shared budget plus finite cleanup */
        assert(!m.rx_pending && !m.tx_pending && !m.latched);assert_preserved(&m);
        m.stall_tx=m.stall_rx=m.stall_eot=m.extra_rx=0;
        initialized(&m,&p);successful(&m,&p,3,kind);
    }
    p=port(&m);m.short_cs=1;uint32_t hz;
    assert(r10_spi_initialize(&p,&hz,&detail)!=0 && !p.initialized && hz==0);
    p=port(&m);seed(&m,R10_CR,get(&m,R10_CR)&~4u);unsigned before=m.reads;
    assert(r10_spi_initialize(&p,&hz,&detail)!=0 && m.reads-before<300);
    p=port(&m);seed(&m,R10_CR,get(&m,R10_CR)|8u);
    assert(r10_spi_initialize(&p,&hz,&detail)!=0 && !p.initialized);
    p=port(&m);m.bad_cfg=1;
    assert(r10_spi_initialize(&p,&hz,&detail)!=0 && !p.initialized);
    p=port(&m);initialized(&m,&p);before=m.writes;
    assert(r10_spi_exchange(&p,tx,rx,34,&detail)!=0 && m.writes==before);
    p=port(&m);initialized(&m,&p);p.poll_limit=5;
    assert(r10_spi_exchange(&p,tx,rx,3,&detail)!=0 && !p.initialized); /* shared budget */
    puts("scripted native SPI cases passed; no hardware timing tested");return 0;
}
