/* Independent MMIO/flash-frame model. No analog or real-silicon emulation. */
#include "qspi_port.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct {uint32_t addr,value;} reg;
typedef struct {
    reg regs[160];unsigned nr,writes,reads,primes,sequence,active,n,left,offset,cr_clear_after_zero;
    unsigned stuck_busy,missing_tcf,no_data,extra,ignore_dr,after_dr_error,stale_clear,reset_ignored;
    unsigned prime_fails,prime_leaves_busy,ncs_low;
    uint32_t ignored,forced_sr,bad_dr;
    uint8_t fifo[16];
} model;
static uint32_t *at(model *m,uint32_t a) {
    for (unsigned i=0;i<m->nr;++i) if (m->regs[i].addr==a) return &m->regs[i].value;
    assert(m->nr<160);m->regs[m->nr]=(reg){a,0};return &m->regs[m->nr++].value;
}
static unsigned pinmode(model *m,uint32_t base,unsigned pin) {return (*at(m,base+Q_MODER)>>(pin*2))&3;}
static uint32_t status(model *m) {
    uint32_t sr=*at(m,Q_BASE+Q_SR)|m->forced_sr;
    if (m->active) {
        sr|=(m->left?Q_BUSY|Q_FTF:0)|(m->left<<8);
        if (!m->missing_tcf) sr|=Q_TCF;
        if (m->stuck_busy) sr|=Q_BUSY;
    }
    return sr;
}
static uint32_t read_reg(void *ctx,uint32_t a,unsigned width) {
    model *m=ctx;++m->reads;
    assert(width==(a==Q_BASE+Q_DR?8u:32u));
    if (a>=Q_BASE && a<Q_BASE+0x100) assert(*at(m,Q_ENABLE)&Q_GATE);
    if (a==Q_BASE+Q_SR) return status(m);
    if (a==Q_GPIOB+Q_IDR) {
        if (m->ncs_low) return 0;
        return pinmode(m,Q_GPIOB,6)==1?(*at(m,Q_GPIOB+Q_ODR)&64u):
            (m->active && m->left?0:64u);
    }
    if (a==Q_BASE+Q_DR) {
        assert(m->left && m->active);
        uint32_t v=m->bad_dr?m->bad_dr:m->fifo[m->offset];
        if (!m->ignore_dr) {--m->left;++m->offset;}
        if (m->after_dr_error) m->forced_sr|=Q_TEF;
        return v;
    }
    return *at(m,a);
}
static uint32_t gpio_mask(uint32_t a) {
    uint32_t base=a&~0x3ffu,off=a-base;
    unsigned p[3],n=0;
    if (base==Q_GPIOB) {p[n++]=2;p[n++]=6;}
    else if (base==Q_GPIOD) {p[n++]=11;p[n++]=12;p[n++]=13;}
    else if (base==Q_GPIOE) p[n++]=2;
    else return 0;
    uint32_t mask=0;
    for (unsigned i=0;i<n;++i) {
        if (off==Q_MODER || off==Q_SPEED || off==Q_PULL) mask|=3u<<(p[i]*2);
        else if (off==Q_OTYPER) mask|=1u<<p[i];
        else if (off==(p[i]<8?Q_AFRL:Q_AFRH)) mask|=15u<<((p[i]%8)*4);
    }
    return mask;
}
static void frame(model *m) {
    static const uint32_t ccr[8]={0x05000105,0x05000135,0x05000115,0x0500019f,
        0x0520255a,0x0710ed94,0x0500019f,0x05000105};
    static const unsigned length[8]={1,1,1,3,8,4,3,1};
    static const uint8_t data[8][8]={{0},{2},{0},{0xef,0x40,0x18},
        {'S','F','D','P',5,1,0,255},{0xef,0x17,0xef,0x17},{0xef,0x40,0x18},{0}};
    unsigned i=0;
    while (i<8 && ccr[i]!=*at(m,Q_BASE+Q_CCR)) ++i;
    assert(i<8);++m->sequence;
    assert(*at(m,Q_BASE+Q_CR)==Q_CONTROL && *at(m,Q_BASE+Q_DCR)==Q_DEVICE);
    assert(*at(m,Q_BASE+Q_CCR)==ccr[i] && *at(m,Q_BASE+Q_DLR)==length[i]-1);
    assert(*at(m,Q_BASE+Q_ABR)==(i==5?0xf0u:0u));
    assert(m->primes && pinmode(m,Q_GPIOB,6)==2 && pinmode(m,Q_GPIOB,2)==2);
    assert(((*at(m,Q_GPIOB+Q_AFRL)>>24)&15u)==10u);
    assert(((*at(m,Q_GPIOB+Q_AFRL)>>8)&15u)==9u);
    assert(((*at(m,Q_GPIOE+Q_AFRL)>>8)&15u)==9u);
    assert(((*at(m,Q_GPIOD+Q_AFRH)>>12)&0xfffu)==0x999u);
    memcpy(m->fifo,data[i],8);m->n=length[i];m->offset=0;
    m->left=m->no_data?0:m->n+m->extra;m->active=1;
}
static void write_reg(void *ctx,uint32_t a,uint32_t v,unsigned width) {
    model *m=ctx;++m->writes;assert(width==32u);
    uint32_t mask=gpio_mask(a);
    if (a==Q_ENABLE || a==Q_RESET) mask=Q_GATE;
    if (a==Q_GPIO_ENABLE) mask=Q_GPIO_GATES;
    if (mask) assert(!((v^*at(m,a))&~mask));
    else assert(a==Q_GPIOB+Q_BSRR || (a>=Q_BASE && a<=Q_BASE+Q_ABR));
    if (m->ignored==a) return;
    if (a==Q_GPIOB+Q_BSRR) {assert(v==64u);*at(m,Q_GPIOB+Q_ODR)|=v;return;}
    if (a==Q_RESET && (v&Q_GATE) && !m->reset_ignored) {
        for (unsigned i=0;i<m->nr;++i)
            if (m->regs[i].addr>=Q_BASE && m->regs[i].addr<Q_BASE+0x100) m->regs[i].value=0;
        m->active=m->left=m->forced_sr=0;m->cr_clear_after_zero=1;
    }
    if (a>=Q_BASE && a<Q_BASE+0x100) assert(*at(m,Q_ENABLE)&Q_GATE);
    if (a==Q_BASE+Q_CCR) {
        if (!v) {
            assert(pinmode(m,Q_GPIOB,6)==1 && !*at(m,Q_BASE+Q_CR));
            *at(m,Q_BASE+Q_SR)|=Q_BUSY;m->cr_clear_after_zero=0;
        } else if (v!=0x20000000u) {
            assert(!status(m));assert((v&0xfc000000u)==0x04000000u);
        }
    }
    if (a==Q_BASE+Q_CR && !v) m->cr_clear_after_zero=1;
    if (a==Q_BASE+Q_CR && v==Q_CONTROL) {
        assert(m->cr_clear_after_zero && m->primes);
        *at(m,Q_BASE+Q_SR)=0;
    }
    if (a==Q_BASE+Q_FCR) {
        assert(v==Q_TCF);if (!m->stale_clear) {m->active=0;*at(m,Q_BASE+Q_SR)&=~v;}return;
    }
    *at(m,a)=v;
    if (a==Q_BASE+Q_CCR && v && v!=0x20000000u && !(v&0xc00u)) frame(m);
    if (a==Q_BASE+Q_AR) {assert(v==0 && (*at(m,Q_BASE+Q_CCR)&0xc00u));frame(m);}
}
static int prime(void *ctx) {
    model *m=ctx;++m->primes;
    assert(pinmode(m,Q_GPIOB,6)==1 && pinmode(m,Q_GPIOB,2)==3);
    assert(pinmode(m,Q_GPIOD,11)==3 && pinmode(m,Q_GPIOD,12)==3 && pinmode(m,Q_GPIOD,13)==3);
    assert(pinmode(m,Q_GPIOE,2)==3 && (*at(m,Q_GPIOB+Q_ODR)&64u));
    assert(!*at(m,Q_BASE+Q_CR) && !status(m));
    if (m->prime_fails) return FRO_ERROR;
    write_reg(m,Q_BASE+Q_CR,0xff000001,32);
    write_reg(m,Q_BASE+Q_CCR,0x20000000,32);
    write_reg(m,Q_BASE+Q_CCR,0x20000000,32);
    write_reg(m,Q_BASE+Q_CR,0,32);
    if (m->prime_leaves_busy) *at(m,Q_BASE+Q_SR)|=Q_BUSY;
    return FRO_OK;
}
static void setup(model *m,r10_qspi_port *p) {
    memset(m,0,sizeof(*m));memset(p,0,sizeof(*p));p->io=(r10_qspi_mmio){m,read_reg,write_reg,prime};
    *at(m,Q_RCC_CR)=5;*at(m,Q_ID)=0x20030450;
    *at(m,Q_ENABLE)=0x1000;*at(m,Q_GPIO_ENABLE)=0x80;
    *at(m,Q_GPIOB+Q_MODER)=0xa5a5a5a5u&~((3u<<4)|(3u<<12));
    *at(m,Q_GPIOD+Q_MODER)=0x5a5a5a5au&~((3u<<22)|(3u<<24)|(3u<<26));
    *at(m,Q_GPIOE+Q_MODER)=0xa5a5a5a5u&~(3u<<4);
    const uint32_t bases[]={Q_GPIOB,Q_GPIOD,Q_GPIOE};
    for (unsigned i=0;i<3;++i) {
        *at(m,bases[i]+Q_PULL)=0xaaaaaaaau;*at(m,bases[i]+Q_SPEED)=0x55555555u;
        *at(m,bases[i]+Q_OTYPER)=0xffffu;*at(m,bases[i]+Q_AFRL)=0x5a5a5a5au;
        *at(m,bases[i]+Q_AFRH)=0xa5a5a5a5u;
    }
}
static int initialized(r10_qspi_port *p,uint32_t *detail) {
    uint32_t hz=0;int rc=FRO_BUSY;
    for (uint32_t now=0;now<20 && rc==FRO_BUSY;++now) rc=r10_qspi_initialize(p,now,&hz,detail);
    if (!rc) assert(hz==1000000 && p->nominal_hz==hz);
    return rc;
}
static void full(model *m,r10_qspi_port *p,r10_flash_ro *f,uint32_t *now) {
    r10_flash_ro_io io={p,r10_qspi_initialize,r10_qspi_start,r10_qspi_poll,r10_qspi_cancel};
    r10_flash_ro_begin(f,&io,*now);
    for (unsigned i=0;i<500 && f->state!=FRO_WAIT && f->state!=FRO_RETRY && f->state!=FRO_STOPPED;++i)
        r10_flash_ro_poll(f,(*now)++);
    (void)m;
}
int main(int argc,char **argv) {
    assert(argc>=2);const char *name=argv[1];unsigned arg=argc>2?(unsigned)strtoul(argv[2],0,0):0;
    model m;r10_qspi_port p;r10_flash_ro f;uint32_t detail=0,hz=0,now=0,got=0;uint8_t bytes[8];
    setup(&m,&p);
    if (!strcmp(name,"good")) {
        full(&m,&p,&f,&now);assert(f.state==FRO_WAIT && f.samples==1 && f.completed_mask==255 && m.sequence==8);
        assert(!memcmp(f.sample_raw[5],"\xef\x17\xef\x17",4));
        assert(!r10_qspi_cancel(&p,&detail) && !p.owned && !p.active);
        assert(!(*at(&m,Q_ENABLE)&Q_GATE) && pinmode(&m,Q_GPIOB,6)==1 && (*at(&m,Q_GPIOB+Q_ODR)&64));
    } else if (!strcmp(name,"revision")) {
        *at(&m,Q_ID)=(arg<<16)|0x450u;assert(!initialized(&p,&detail));
    } else if (!strcmp(name,"unknown")) {
        *at(&m,Q_ID)=(arg<<16)|0x450u;assert(initialized(&p,&detail)==FRO_ERROR && !m.writes);
        assert(!r10_qspi_cancel(&p,&detail) && !m.writes);
    } else if (!strcmp(name,"clock")) {
        const uint32_t regs[]={Q_RCC_CR,Q_CFGR,Q_D1CFGR,Q_D1CCIPR};
        const uint32_t values[]={0,4,8,16};assert(arg<4);*at(&m,regs[arg])=values[arg];
        assert(initialized(&p,&detail)==FRO_ERROR && !m.writes);
    } else if (!strcmp(name,"owned")) {
        *at(&m,Q_ENABLE)|=Q_GATE;assert(initialized(&p,&detail)==FRO_ERROR && !m.writes);
    } else if (!strcmp(name,"pin-owned")) {
        *at(&m,Q_GPIOE+Q_MODER)|=1u<<4;
        assert(initialized(&p,&detail)==FRO_ERROR && !p.owned && !m.primes);
    } else if (!strcmp(name,"same-tick")) {
        assert(r10_qspi_initialize(&p,0,&hz,&detail)==FRO_BUSY);
        unsigned before=m.writes;
        for (unsigned n=0;n<20;++n) assert(r10_qspi_initialize(&p,0,&hz,&detail)==FRO_BUSY);
        assert(m.writes==before && p.phase==Q_RESET_HELD);
    } else if (!strcmp(name,"init-drift")) {
        assert(r10_qspi_initialize(&p,0,&hz,&detail)==FRO_BUSY);
        if (!arg) *at(&m,Q_GPIO_ENABLE)&=~2u;
        else *at(&m,Q_RESET)&=~Q_GATE;
        unsigned before=m.writes;
        assert(r10_qspi_initialize(&p,1,&hz,&detail)==FRO_ERROR && m.writes==before);
    } else if (!strcmp(name,"read-drift")) {
        assert(!initialized(&p,&detail));assert(!r10_qspi_start(&p,0,&detail));
        *at(&m,Q_BASE+(arg?Q_DLR:Q_CCR))^=1u;
        assert(r10_qspi_poll(&p,bytes,8,&got,&detail)==FRO_ERROR && !got && m.offset==0);
    } else if (!strcmp(name,"zero-capacity")) {
        assert(!initialized(&p,&detail));assert(!r10_qspi_start(&p,0,&detail));
        assert(r10_qspi_poll(&p,0,0,&got,&detail)==FRO_BUSY && !got && !m.offset);
        assert(!r10_qspi_poll(&p,bytes,1,&got,&detail) && got==1);
    } else if (!strcmp(name,"prime-fail")) {
        m.prime_fails=arg==0;m.prime_leaves_busy=arg==1;
        assert(initialized(&p,&detail)==FRO_ERROR && (detail>>24)==Q_FAIL_TIMING);
        assert(pinmode(&m,Q_GPIOB,6)==1 && !m.sequence);
    } else if (!strcmp(name,"ignored")) {
        m.ignored=arg;assert(initialized(&p,&detail)==FRO_ERROR && !m.sequence);
    } else if (!strcmp(name,"stale")) {
        assert(!initialized(&p,&detail));m.forced_sr=arg;
        assert(r10_qspi_start(&p,0,&detail)==FRO_ERROR && !m.sequence);
    } else if (!strcmp(name,"drift")) {
        assert(!initialized(&p,&detail));
        uint32_t mask=1u;
        if (arg==Q_GPIOB+Q_AFRL) mask=1u<<8;
        if (arg==Q_GPIOB+Q_MODER || arg==Q_GPIOB+Q_SPEED || arg==Q_GPIOB+Q_PULL) mask=1u<<4;
        if (arg==Q_ENABLE) mask=Q_GATE;
        if (arg==Q_GPIO_ENABLE) mask=2u;
        if (arg==Q_D1CCIPR) mask=16u;
        *at(&m,arg)^=mask;
        assert(r10_qspi_start(&p,0,&detail)==FRO_ERROR && !m.sequence);
    } else if (!strcmp(name,"transfer-fault")) {
        m.stuck_busy=arg==0;m.no_data=arg==1;m.extra=arg==2;m.after_dr_error=arg==3;
        m.stale_clear=arg==4;m.ignore_dr=arg==5;m.missing_tcf=arg==6;
        m.bad_dr=arg==7?0x1ffu:0;
        full(&m,&p,&f,&now);
        assert(f.state==FRO_RETRY && f.failures==1 && !f.valid && !f.samples);
        assert(pinmode(&m,Q_GPIOB,6)==1 && !p.owned);
    } else if (!strcmp(name,"partial")) {
        assert(!initialized(&p,&detail));
        for (unsigned cmd=0;cmd<8;++cmd) {
            assert(!r10_qspi_start(&p,cmd,&detail));unsigned count=0;int rc=FRO_BUSY;
            while (rc==FRO_BUSY) {rc=r10_qspi_poll(&p,bytes+count,1,&got,&detail);count+=got;}
            assert(rc==FRO_OK && count==p.expected_dlr+1);
        }
    } else if (!strcmp(name,"cleanup-fail")) {
        assert(!initialized(&p,&detail));assert(!r10_qspi_start(&p,0,&detail));m.reset_ignored=1;
        assert(r10_qspi_cancel(&p,&detail)==FRO_ERROR && p.owned);
    } else if (!strcmp(name,"ignored-reset")) {
        *at(&m,Q_BASE+Q_CR)=1;m.reset_ignored=1;
        assert(initialized(&p,&detail)==FRO_ERROR && !m.primes);
    } else if (!strcmp(name,"invalid-command")) {
        assert(!initialized(&p,&detail));unsigned writes=m.writes;
        assert(r10_qspi_start(&p,arg,&detail)==FRO_ERROR && m.writes==writes);
    } else if (!strcmp(name,"restart")) {
        assert(!initialized(&p,&detail));assert(!r10_qspi_cancel(&p,&detail));
        assert(!initialized(&p,&detail) && m.primes==2);
    } else if (!strcmp(name,"recover")) {
        m.after_dr_error=1;full(&m,&p,&f,&now);
        assert(f.state==FRO_RETRY && f.failures==1 && !f.valid);
        m.after_dr_error=0;now=f.stage_at+1000;
        for (unsigned i=0;i<500 && f.state!=FRO_WAIT;++i) r10_flash_ro_poll(&f,now++);
        assert(f.state==FRO_WAIT && f.samples==1 && f.retries==1 && f.failures==1);
        assert(f.last_error==FRO_READ_ERROR && f.valid && !f.error);
    } else assert(0);
    printf("PASS %s %u\n",name,arg);return 0;
}
