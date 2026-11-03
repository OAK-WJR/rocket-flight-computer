#include "i2c_port.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

/* A scripted peripheral, not an electrical model. Advancing the wire, copying
 * into RXDR, reading RXDR, STOP detection and BUSY release are distinct events.
 * Defensive injected flag combinations need not be physically reachable. */
enum event_kind { STATUS, STARTED, TX_WRITE, RX_READ, STOP_REQUEST, DISABLE, RESET, CLEAR, GUARD };
enum fault_point { NONE, INIT_IDLE, IDLE, TX_READY, RX_FIRST, RX_MIDDLE, RX_LAST,
                   STOP_READY, BUSY_READY, FINAL_READY };
typedef struct {
    enum event_kind kind;
    uint32_t value, cr2;
    unsigned wire, unread, tx, rx;
} event;
static const uint32_t addresses[]={
    R10_I2C_RCC_CR,R10_I2C_CFGR,R10_I2C_D1CFGR,R10_I2C_D2CFGR,R10_I2C_D2CCIP2R,
    R10_I2C_APB1LRSTR,R10_I2C_AHB4ENR,R10_I2C_APB1LENR,
    R10_I2C_MODER,R10_I2C_OTYPER,R10_I2C_OSPEEDR,R10_I2C_PUPDR,R10_I2C_IDR,R10_I2C_AFRH,
    R10_I2C_CR1,R10_I2C_CR2,R10_I2C_OAR1,R10_I2C_OAR2,R10_I2C_TIMINGR,
    R10_I2C_TIMEOUTR,R10_I2C_ISR,R10_I2C_ICR,R10_I2C_RXDR,R10_I2C_TXDR
};
static const struct {uint32_t address, seed, owned;} preserved[]={
    {R10_I2C_RCC_CR,0x00011287u,0}, {R10_I2C_CFGR,0x00004000u,0},
    {R10_I2C_D1CFGR,0x00000050u,0}, {R10_I2C_D2CFGR,0x00000500u,0},
    {R10_I2C_D2CCIP2R,0x20700125u,0},
    {R10_I2C_APB1LRSTR,0x80404003u,0x00200000u},
    {R10_I2C_AHB4ENR,0x13280415u,2u}, {R10_I2C_APB1LENR,0x40424003u,0x00200000u},
    {R10_I2C_MODER,0xa5a54a80u,0x000f0000u}, /* SPI PB3/4/5/7 already in use. */
    {R10_I2C_OTYPER,0x00005505u,0x300u}, {R10_I2C_OSPEEDR,0xaaaa5030u,0x000f0000u},
    {R10_I2C_PUPDR,0x99991015u,0x000f0000u}, {R10_I2C_AFRH,0x12345678u,0xffu}
};
typedef struct {
    uint32_t values[sizeof addresses/sizeof *addresses], seeds[sizeof addresses/sizeof *addresses];
    unsigned reads,writes,isr_reads,resets,starts,delays,stop_requests;
    unsigned active,address_ticks,expected,tx,rx,wire,unread,tx_pending,read_direction;
    unsigned stop_seen,stop_cleared,busy_release_ticks,wire_done;
    uint32_t flags,held_lines;
    unsigned idle_hold,byte_hold,tx_hold,stall_idle,stall_tx,stall_rx_at,stall_stop,stall_busy;
    unsigned cleanup_fails,disable_fails,extra_rx,premature_stop,stop_with_rx;
    enum fault_point fault_at;
    uint32_t fault,fault_isr;
    unsigned fault_fired,gate_gpio,gate_i2c;
    uint32_t bad_read_address,bad_read_mask;
    uint8_t tx_data,rx_data,pattern;
    event events[4096];unsigned event_count;
} model;
static unsigned index_of(uint32_t a) {
    for (unsigned i=0;i<sizeof addresses/sizeof *addresses;++i)if (addresses[i]==a)return i;
    assert(!"MMIO escaped I2C1/GPIOB/RCC allowlist");return 0;
}
static uint32_t get(model *m,uint32_t a) {return m->values[index_of(a)];}
static void set(model *m,uint32_t a,uint32_t v) {m->values[index_of(a)]=v;}
static void seed(model *m,uint32_t a,uint32_t v) {set(m,a,v);m->seeds[index_of(a)]=v;}
static void record(model *m,enum event_kind k,uint32_t v) {
    assert(m->event_count<sizeof m->events/sizeof *m->events);
    m->events[m->event_count++]=(event){k,v,get(m,R10_I2C_CR2),m->wire,m->unread,m->tx,m->rx};
}
static void assert_preserved(model *m) {
    for (unsigned i=0;i<sizeof preserved/sizeof *preserved;++i)
        assert((get(m,preserved[i].address)&~preserved[i].owned)==
               (m->seeds[index_of(preserved[i].address)]&~preserved[i].owned));
}
static void clear_engine(model *m) {
    m->active=m->expected=m->address_ticks=m->tx=m->rx=m->wire=m->unread=0;
    m->tx_pending=m->wire_done=m->flags=m->stop_seen=m->stop_cleared=m->busy_release_ticks=0;
    set(m,R10_I2C_CR2,get(m,R10_I2C_CR2)&~(R10_I2C_START|R10_I2C_STOP|0x8000u));
}
static void stop_on_wire(model *m) {
    m->flags|=R10_I2C_STOPF;
    set(m,R10_I2C_CR2,get(m,R10_I2C_CR2)&~(R10_I2C_START|R10_I2C_STOP));
}
static void advance(model *m) {
    if (!(get(m,R10_I2C_CR1)&R10_I2C_PE) || !m->active)return;
    if (get(m,R10_I2C_CR2)&R10_I2C_STOP) {
        if (!m->cleanup_fails) {stop_on_wire(m);m->flags&=~R10_I2C_BUSY;}
        return;
    }
    if (m->flags&R10_I2C_STOPF) {
        if (!m->stall_busy && !m->unread && ++m->busy_release_ticks>=2)m->flags&=~R10_I2C_BUSY;
        return;
    }
    if (m->address_ticks) {
        if (--m->address_ticks)return;
        set(m,R10_I2C_CR2,get(m,R10_I2C_CR2)&~R10_I2C_START);
    }
    if (m->premature_stop) {stop_on_wire(m);return;}
    if (m->byte_hold) {--m->byte_hold;return;}
    if (m->read_direction && !m->unread && m->wire<m->expected && m->stall_rx_at!=m->wire+1) {
        m->rx_data=(uint8_t)(m->pattern+7u*m->wire);++m->wire;m->unread=1;
    } else if (!m->read_direction && m->tx_pending) {
        if(m->tx_hold){--m->tx_hold;return;}
        m->tx_pending=0;++m->wire;
    }
    if (m->wire==m->expected) {
        /* A late STOP is separately selectable. Early STOP may coexist with
         * the final RXNE while software has not yet consumed that last byte. */
        if (!m->stall_stop && (m->stop_with_rx || m->wire_done))stop_on_wire(m);
        m->wire_done=1;
    }
}
static int inject_now(model *m,uint32_t s) {
    if (!m->fault || m->fault_fired)return 0;
    switch (m->fault_at) {
    case INIT_IDLE:case IDLE:return !m->active;
    case TX_READY:return m->active && !m->read_direction && !m->tx && (s&R10_I2C_TXIS);
    case RX_FIRST:return m->active && m->unread && !m->rx;
    case RX_MIDDLE:return m->active && m->unread && m->rx==1;
    case RX_LAST:return m->active && m->unread && m->rx+1==m->expected;
    case STOP_READY:return m->active && m->tx+m->rx==m->expected &&
                           !m->stop_seen && (s&R10_I2C_STOPF);
    case BUSY_READY:return m->stop_seen && !m->stop_cleared && !(s&R10_I2C_BUSY);
    case FINAL_READY:return m->stop_cleared!=0;
    default:return 0;
    }
}
static uint32_t read_mmio(void *ctx,uint32_t a,unsigned width) {
    model *m=ctx;++m->reads;assert(m->reads<100000u);index_of(a);
    assert(a!=R10_I2C_ICR); /* W1C is write-only; RMW is a test failure. */
    if (a==R10_I2C_RXDR) {
        assert(width==4 && m->unread && (get(m,R10_I2C_CR1)&R10_I2C_PE));
        --m->unread;++m->rx;record(m,RX_READ,m->rx_data);return m->rx_data;
    }
    assert(width==4);
    if (a==R10_I2C_IDR)return 0xffffu&~m->held_lines;
    if (a==m->bad_read_address)return get(m,a)^m->bad_read_mask;
    if (a==R10_I2C_ISR) {
        ++m->isr_reads;advance(m);
        uint32_t s=m->flags|1u; /* TXE is not TXIS and not completion. */
        if (!m->active && (m->stall_idle || m->idle_hold)) {
            s|=R10_I2C_BUSY;if (m->idle_hold)--m->idle_hold;
        }
        if (m->active && !m->address_ticks && !m->read_direction && !m->tx && !m->stall_tx)
            s|=R10_I2C_TXIS;
        if (m->unread || (m->extra_rx && m->stop_seen))s|=R10_I2C_RXNE;
        if (inject_now(m,s)) {
            m->flags|=m->fault;s|=m->fault;m->fault_fired=1;m->fault_isr=s;
            if (m->fault&(R10_I2C_ARLO|R10_I2C_TIMEOUT))set(m,R10_I2C_CR2,get(m,R10_I2C_CR2)&~R10_I2C_START);
        }
        if ((s&R10_I2C_STOPF) && m->tx+m->rx==m->expected)m->stop_seen=1;
        record(m,STATUS,s);return s;
    }
    return get(m,a);
}
static void write_mmio(void *ctx,uint32_t a,uint32_t v,unsigned width) {
    model *m=ctx;++m->writes;index_of(a);
    if (a==R10_I2C_TXDR) {
        assert(width==4 && m->active && !m->read_direction && !m->address_ticks && !m->tx);
        assert(get(m,R10_I2C_CR1)==R10_I2C_PE);
        m->tx_data=(uint8_t)v;++m->tx;m->tx_pending=1;record(m,TX_WRITE,v);return;
    }
    assert(width==4 && a!=R10_I2C_ISR && a!=R10_I2C_IDR && a!=R10_I2C_RXDR);
    for (unsigned i=0;i<sizeof preserved/sizeof *preserved;++i)
        if (a==preserved[i].address)assert(preserved[i].owned); /* selectors read-only */
    if (a==R10_I2C_ICR) {
        m->flags&=~(v&0x3f38u);
        if ((v&R10_I2C_STOPF) && m->active) {m->stop_cleared=1;m->active=0;}
        record(m,CLEAR,v);return;
    }
    uint32_t old=get(m,a);
    if (a==R10_I2C_CR2) {
        /* Writing zero to START/STOP does not clear a hardware request. */
        set(m,a,v|(old&(R10_I2C_START|R10_I2C_STOP)));
        if (v&R10_I2C_STOP) {
            assert(!(v&R10_I2C_START));++m->stop_requests;record(m,STOP_REQUEST,v);
        } else if (v&R10_I2C_START) {
            assert(!m->active && !m->unread && !m->tx_pending);
            assert((v&0x3ffu)==0xeeu && (v&R10_I2C_AUTOEND));
            assert(!(v&(0x01000000u|0x800u|0x1000u|0x8000u|0x04000000u)));
            assert(get(m,R10_I2C_CR1)==R10_I2C_PE);
            m->active=1;m->address_ticks=2;m->expected=(v>>16)&0xffu;
            m->read_direction=(v&R10_I2C_RD_WRN)!=0;
            assert(m->expected==(m->read_direction?2u:1u) || (m->read_direction && m->expected==3u));
            m->tx=m->rx=m->wire=m->wire_done=m->stop_seen=m->stop_cleared=m->busy_release_ticks=0;
            m->flags=R10_I2C_BUSY;++m->starts;record(m,STARTED,v);
        }
    } else if (a==R10_I2C_CR1) {
        if (!v && (old&R10_I2C_PE)) {
            record(m,DISABLE,v);
            if (!m->disable_fails) {clear_engine(m);set(m,a,v);}
        } else set(m,a,v);
    } else if ((a==R10_I2C_AHB4ENR && m->gate_gpio) || (a==R10_I2C_APB1LENR && m->gate_i2c)) {
        /* Failed clock-enable write. */
    } else set(m,a,v);
    if (a==R10_I2C_APB1LRSTR && (v&0x00200000u) && !(old&0x00200000u)) {
        ++m->resets;clear_engine(m);
        for (unsigned i=0;i<sizeof addresses/sizeof *addresses;++i)
            if (addresses[i]>=R10_I2C1 && addresses[i]<R10_I2C1+44)m->values[i]=0;
        record(m,RESET,v);
    }
    assert_preserved(m); /* Includes transient clobbers during reset/initialization. */
}
static void delay(void *ctx,unsigned cycles) {
    model *m=ctx;assert(cycles==512u);m->delays+=cycles;record(m,GUARD,cycles);
}
static r10_i2c_port port(model *m) {
    memset(m,0,sizeof(*m));m->pattern=0x51;m->stop_with_rx=1;
    for (unsigned i=0;i<sizeof preserved/sizeof *preserved;++i)
        seed(m,preserved[i].address,preserved[i].seed);
    return (r10_i2c_port){.io={m,read_mmio,write_mmio,delay},.poll_limit=64};
}
static void initialized(model *m,r10_i2c_port *p) {
    uint32_t hz=0,detail=1;
    assert(r10_i2c_initialize(p,&hz,&detail)==0 && hz==50000u && !detail && p->initialized);
    assert(get(m,R10_I2C_CR1)==1 && get(m,R10_I2C_TIMINGR)==0x70b44f4fu);
    assert(!get(m,R10_I2C_OAR1) && !get(m,R10_I2C_OAR2) && !get(m,R10_I2C_TIMEOUTR));
    assert((get(m,R10_I2C_MODER)&0xf0000u)==0xa0000u);
    assert((get(m,R10_I2C_OTYPER)&0x300u)==0x300u && (get(m,R10_I2C_AFRH)&0xffu)==0x44u);
    assert(!(get(m,R10_I2C_PUPDR)&0xf0000u) && !(get(m,R10_I2C_OSPEEDR)&0xf0000u));
    assert(!m->active && !m->flags && !m->unread && !m->tx_pending);assert_preserved(m);
    m->event_count=0;
}
static int transfer(r10_i2c_port *p,unsigned n,uint8_t *rx,uint32_t *detail) {
    const uint8_t cmd=0xa2;
    return r10_i2c_transfer(p,0x77,n?NULL:&cmd,n?0:1,rx,n,detail);
}
static void successful(model *m,r10_i2c_port *p,unsigned n) {
    uint8_t rx[4]={0xa5,0xa5,0xa5,0xa5};uint32_t detail=1;
    unsigned resets=m->resets,starts=m->starts,polls=m->isr_reads,delays=m->delays;
    m->event_count=0;
    assert(transfer(p,n,rx,&detail)==0 && !detail && p->initialized && !p->stage);
    assert(m->wire==(n?n:1) && m->rx==n && m->tx==(n?0:1));
    assert(p->received==n && p->transmitted==(n?0u:1u));
    for (unsigned i=0;i<n;++i)assert(rx[i]==(uint8_t)(m->pattern+7u*i));
    assert(rx[n]==0xa5 && (!m->tx || m->tx_data==0xa2));
    assert(m->resets==resets && m->starts==starts+1 && m->delays-delays==512u);
    assert(m->isr_reads-polls<=p->poll_limit && !m->flags && !m->active && !m->unread);
    assert(get(m,R10_I2C_CR1)==1 && !get(m,R10_I2C_CR2));assert_preserved(m);
    unsigned last_rx=0,stop_observed=0,clear=0,wire_rx=0;
    for (unsigned i=0;i<m->event_count;++i) {
        event *e=&m->events[i];
        assert(e->kind!=DISABLE && e->kind!=RESET && e->kind!=STOP_REQUEST);
        if (e->kind==RX_READ)last_rx=i;
        if (e->kind==TX_WRITE)assert(!e->wire);
        if (e->kind==STATUS && (e->value&R10_I2C_STOPF)) {
            assert(e->wire==(n?n:1) && !(e->cr2&R10_I2C_START));stop_observed=i;
            if (e->unread)wire_rx=i;
        }
        if (e->kind==CLEAR) {assert(e->value==R10_I2C_STOPF);clear=i;}
    }
    assert(stop_observed<clear && (!n || last_rx<stop_observed));
    if (n && m->stop_with_rx)assert(wire_rx && wire_rx<last_rx);
}
static void assert_failed(model *m,r10_i2c_port *p,uint32_t detail,unsigned polls,unsigned resets) {
    assert((detail&0x80000000u) && !p->initialized);
    assert(m->isr_reads-polls<=p->poll_limit+R10_I2C_CLEANUP_POLLS+1);
    assert(m->resets==resets+1 && !get(m,R10_I2C_CR1));
    assert(!m->flags && !m->active && !m->unread && !m->tx_pending);
    assert_preserved(m);
    unsigned writes=m->writes,reads=m->reads;uint8_t rx[3];uint32_t ignored;
    assert(transfer(p,3,rx,&ignored)!=0 && m->writes==writes && m->reads==reads);
}
static void test_faults(void) {
    const uint32_t faults[]={0x10,0x100,0x200,0x400,0x1000,0x800,0x2000,0x8,0x40,0x80};
    const unsigned stages[]={0,4,6,7,8,8,8,9,10,11};
    for (unsigned f=0;f<sizeof faults/sizeof *faults;++f) {
        model m;r10_i2c_port p=port(&m);uint32_t hz=1,detail;
        m.fault_at=INIT_IDLE;m.fault=faults[f];
        assert(r10_i2c_initialize(&p,&hz,&detail)!=0 && !hz && !p.initialized);
        assert(m.fault_fired && ((detail>>16)&0xffu)==R10_I2C_INIT_IDLE);
        assert((detail&0xffffu)==m.fault_isr && m.resets==2 && !get(&m,R10_I2C_CR1));
        m.fault=0;initialized(&m,&p);successful(&m,&p,3);
    }
    for (unsigned point=IDLE;point<=FINAL_READY;++point)
    for (unsigned f=0;f<sizeof faults/sizeof *faults;++f)
    for (unsigned cleanup=0;cleanup<2;++cleanup)
    for (unsigned direction=0;direction<2;++direction) {
        if((direction==0 && point>=RX_FIRST && point<=RX_LAST) || (direction==1 && point==TX_READY))continue;
        model m;r10_i2c_port p=port(&m);initialized(&m,&p);
        m.fault_at=(enum fault_point)point;m.fault=faults[f];m.cleanup_fails=cleanup;m.disable_fails=cleanup;
        unsigned polls=m.isr_reads,resets=m.resets;uint32_t detail=0;uint8_t rx[3]={0xcc,0xcc,0xcc};
        assert(transfer(&p,direction?3:0,rx,&detail)!=0);
        assert(m.fault_fired && (detail&0xffffu)==m.fault_isr && ((detail>>16)&0xffu)==stages[point]);
        assert_failed(&m,&p,detail,polls,resets);
        if (point==IDLE || faults[f]==R10_I2C_ARLO)assert(!m.stop_requests);
        if (point==TX_READY)assert(!p.transmitted && (detail&R10_I2C_TXIS));
        if (point>=RX_FIRST && point<=RX_LAST) {
            unsigned consumed=point-RX_FIRST;
            assert(p.received==consumed && rx[consumed]==0xcc && (detail&R10_I2C_RXNE));
        }
        if (point==STOP_READY)assert(detail&R10_I2C_STOPF);
        if (point==BUSY_READY)assert(!(detail&R10_I2C_BUSY));
        m.fault=0;m.cleanup_fails=m.disable_fails=0;
        initialized(&m,&p);successful(&m,&p,0);successful(&m,&p,2);successful(&m,&p,3);
    }
    model delayed;r10_i2c_port port_delayed=port(&delayed);initialized(&delayed,&port_delayed);
    delayed.tx_hold=10;successful(&delayed,&port_delayed,0); /* final TX still on wire, TXE != TXIS */
}
static void test_stalls(void) {
    for (unsigned point=0;point<9;++point)
    for (unsigned cleanup=0;cleanup<2;++cleanup) {
        model m;r10_i2c_port p=port(&m);initialized(&m,&p);
        if (point==0)m.stall_idle=1;
        if (point==1)m.stall_tx=1;
        if (point>=2 && point<=4)m.stall_rx_at=point-1;
        if (point==5)m.stall_stop=1;
        if (point==6)m.stall_busy=1;
        if (point==7)m.extra_rx=1;
        if (point==8)m.premature_stop=1;
        m.cleanup_fails=cleanup;m.disable_fails=cleanup;
        unsigned polls=m.isr_reads,resets=m.resets;uint32_t detail;uint8_t rx[3];
        assert(transfer(&p,point==1?0:3,rx,&detail)!=0);
        assert_failed(&m,&p,detail,polls,resets);
        if (point==0)assert(!m.stop_requests);
    }
    /* Sweep every shared-budget boundary, including exhaustion at the final
     * status check. A wait must not replenish the transfer's budget. */
    unsigned seen=0,successes=0;
    for (unsigned limit=1;limit<30;++limit) {
        model m;r10_i2c_port p=port(&m);initialized(&m,&p);
        m.idle_hold=3;m.byte_hold=4;p.poll_limit=limit;
        unsigned polls=m.isr_reads,resets=m.resets;uint32_t detail;uint8_t rx[3];
        if (transfer(&p,3,rx,&detail)) {
            seen|=1u<<p.stage;assert_failed(&m,&p,detail,polls,resets);
        } else {++successes;assert(m.isr_reads-polls<=limit);}
    }
    assert(successes && (seen&(1u<<R10_I2C_IDLE)) && (seen&(1u<<R10_I2C_RX)) &&
           (seen&(1u<<R10_I2C_WAIT_STOP)) && (seen&(1u<<R10_I2C_WAIT_BUSY)) && (seen&(1u<<R10_I2C_FINAL)));
}
static void test_initialization_and_contract(void) {
    const struct {uint32_t address,mask;} clocks[]={
        {R10_I2C_RCC_CR,1},{R10_I2C_RCC_CR,4},{R10_I2C_RCC_CR,8},{R10_I2C_RCC_CR,16},
        {R10_I2C_CFGR,1},{R10_I2C_CFGR,8},{R10_I2C_D1CFGR,8},
        {R10_I2C_D1CFGR,0x800},{R10_I2C_D2CFGR,0x40},{R10_I2C_D2CCIP2R,0x1000},
        {R10_I2C_D2CCIP2R,0x3000}
    };
    for (unsigned i=0;i<sizeof clocks/sizeof *clocks;++i) {
        model m;r10_i2c_port p=port(&m);uint32_t hz=1,detail;
        seed(&m,clocks[i].address,get(&m,clocks[i].address)^clocks[i].mask);
        assert(r10_i2c_initialize(&p,&hz,&detail)!=0 && !hz && !p.initialized && !m.writes);
        assert(detail==0x80020000u);
        /* The same clock drift during use invalidates and quiesces the port. */
        p=port(&m);initialized(&m,&p);
        seed(&m,clocks[i].address,get(&m,clocks[i].address)^clocks[i].mask);
        uint8_t rx[3];unsigned polls=m.isr_reads,resets=m.resets;
        assert(transfer(&p,3,rx,&detail)!=0);assert_failed(&m,&p,detail,polls,resets);
    }
    model m;r10_i2c_port p=port(&m);
    seed(&m,R10_I2C_D2CCIP2R,get(&m,R10_I2C_D2CCIP2R)|0x2000u);
    initialized(&m,&p);successful(&m,&p,0);successful(&m,&p,3);
    for (unsigned line=0x100;line<=0x200;line<<=1) {
        p=port(&m);m.held_lines=line;uint32_t hz=1,detail;
        assert(r10_i2c_initialize(&p,&hz,&detail)!=0 && !hz && !p.initialized);
        assert(((detail>>16)&0xffu)==R10_I2C_INIT_IDLE && m.isr_reads<=p.poll_limit+1 && !m.starts);
        m.held_lines=0;initialized(&m,&p);m.held_lines=line;
        uint8_t rx[3];unsigned polls=m.isr_reads,resets=m.resets;
        assert(transfer(&p,3,rx,&detail)!=0);assert_failed(&m,&p,detail,polls,resets);
    }
    const struct {uint32_t address,mask;} bad[]={
        {R10_I2C_CR1,0x1000},{R10_I2C_TIMINGR,1},{R10_I2C_OAR1,0x8000},
        {R10_I2C_OAR2,0x8000},{R10_I2C_TIMEOUTR,0x8000},{R10_I2C_CR2,R10_I2C_START},
        {R10_I2C_MODER,0x10000},{R10_I2C_OTYPER,0x100},{R10_I2C_PUPDR,0x10000},
        {R10_I2C_OSPEEDR,0x10000},{R10_I2C_AFRH,1}
    };
    for (unsigned i=0;i<sizeof bad/sizeof *bad;++i) {
        p=port(&m);m.bad_read_address=bad[i].address;m.bad_read_mask=bad[i].mask;
        uint32_t hz=1,detail;assert(r10_i2c_initialize(&p,&hz,&detail)!=0 && !hz && !p.initialized);
        assert(!get(&m,R10_I2C_CR1) && m.resets==2 && !m.starts);
    }
    for (unsigned kind=0;kind<4;++kind) {
        p=port(&m);
        if (kind==0)m.gate_gpio=1;
        if (kind==1)m.gate_i2c=1;
        if (kind==2)m.stall_idle=1;
        if (kind==3) {m.fault_at=INIT_IDLE;m.fault=R10_I2C_NACKF;}
        uint32_t hz=1,detail;assert(r10_i2c_initialize(&p,&hz,&detail)!=0 && !hz && !p.initialized);
        assert(m.isr_reads<=p.poll_limit+1 && !m.starts);assert_preserved(&m);
    }
}
static void test_arguments(void) {
    model m;r10_i2c_port p=port(&m);initialized(&m,&p);
    uint8_t tx=0xa2,rx[4];uint32_t detail;
    unsigned writes=m.writes,reads=m.reads;
    for (unsigned nt=0;nt<4;++nt)for (unsigned nr=0;nr<5;++nr) {
        if ((nt==1 && nr==0) || (nt==0 && (nr==2 || nr==3)))continue;
        assert(r10_i2c_transfer(&p,0x77,&tx,nt,rx,nr,&detail)!=0 && p.initialized);
    }
    assert(r10_i2c_transfer(&p,0x76,&tx,1,NULL,0,&detail)!=0);
    assert(r10_i2c_transfer(&p,0xee,&tx,1,NULL,0,&detail)!=0);
    assert(r10_i2c_transfer(&p,0x77,NULL,1,NULL,0,&detail)!=0);
    assert(r10_i2c_transfer(&p,0x77,NULL,0,NULL,3,&detail)!=0);
    assert(transfer(&p,3,rx,NULL)!=0 && transfer(NULL,3,rx,&detail)!=0);
    assert(m.writes==writes && m.reads==reads);
    for (unsigned kind=0;kind<5;++kind) {
        p=port(&m);
        if (kind==0)p.poll_limit=0;
        if (kind==1)p.poll_limit=1000001;
        if (kind==2)p.io.read=NULL;
        if (kind==3)p.io.write=NULL;
        if (kind==4)p.io.delay_cycles=NULL;
        uint32_t hz=1;assert(r10_i2c_initialize(&p,&hz,&detail)!=0 && !hz && !m.reads && !m.writes);
    }
}
static void test_model_semantics(void) {
    model m;r10_i2c_port p=port(&m);initialized(&m,&p);
    write_mmio(&m,R10_I2C_CR2,0x020224eeu,4);
    assert(get(&m,R10_I2C_CR2)&R10_I2C_START);
    write_mmio(&m,R10_I2C_CR2,0x020204eeu,4);
    assert(get(&m,R10_I2C_CR2)&R10_I2C_START); /* zero does not clear START */
    assert(!(read_mmio(&m,R10_I2C_ISR,4)&R10_I2C_RXNE));
    assert(read_mmio(&m,R10_I2C_ISR,4)&R10_I2C_RXNE);
    assert(!(get(&m,R10_I2C_CR2)&R10_I2C_START));
    assert(m.wire==1 && m.unread && !m.rx);
    write_mmio(&m,R10_I2C_ICR,R10_I2C_RXNE,4);assert(m.unread);
    assert(read_mmio(&m,R10_I2C_RXDR,4)==0x51u);
    uint32_t s=read_mmio(&m,R10_I2C_ISR,4);
    assert((s&(R10_I2C_RXNE|R10_I2C_STOPF))==(R10_I2C_RXNE|R10_I2C_STOPF));
    assert(m.wire==2 && m.rx==1 && m.unread);
    m.flags|=R10_I2C_BERR|R10_I2C_NACKF;
    write_mmio(&m,R10_I2C_ICR,0,4);assert(m.flags&R10_I2C_BERR);
    write_mmio(&m,R10_I2C_ICR,R10_I2C_NACKF,4);
    assert(!(m.flags&R10_I2C_NACKF) && (m.flags&R10_I2C_BERR));
    write_mmio(&m,R10_I2C_CR1,0,4);
    assert(!m.flags && !m.unread && !m.active && get(&m,R10_I2C_TIMINGR)==R10_I2C_TIMING);
    initialized(&m,&p);
    write_mmio(&m,R10_I2C_CR2,0x020120eeu,4);
    (void)read_mmio(&m,R10_I2C_ISR,4);(void)read_mmio(&m,R10_I2C_ISR,4);
    write_mmio(&m,R10_I2C_TXDR,0xa2,4);assert(m.tx_pending && !m.wire);
    write_mmio(&m,R10_I2C_CR1,0,4);assert(!m.tx_pending);
}
static void test_timing_envelope(void) {
    /* Check the documented design envelope, not measured board timing. ns. */
    for (unsigned mhz=60;mhz<=68;++mhz) {
        double t=1000.0/mhz,presc=8*t;
        double low=80*presc+50+2*t,high=80*presc+50+2*t;
        assert(low>=4700 && high>=4000 && low+high>=10000);
        assert(12*presc>=1000+250);
        assert(4*presc>=300-50-3*t && 4*presc<=3450-1000-260-4*t);
        assert(512*t>=4700 && t<250); /* tBUF guard and ES0392 setup constraint. */
    }
}
int main(void) {
    test_model_semantics();test_timing_envelope();test_arguments();
    test_initialization_and_contract();test_faults();test_stalls();
    model m;r10_i2c_port p=port(&m);initialized(&m,&p);
    for (unsigned i=0;i<20;++i) {
        m.stop_with_rx=i%2;m.pattern=(uint8_t)(19*i);
        successful(&m,&p,0);successful(&m,&p,2);successful(&m,&p,3);
    }
    puts("scripted native I2C1 cases passed; no hardware timing tested");return 0;
}
