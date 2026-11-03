/* Fake MMIO with independent hardware-state constraints; no analog simulation. */
#include "adc_port.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct {uint32_t addr,value;} reg;
typedef struct {
    reg registers[160];unsigned n,reads,writes,cal_reads[2],conversion_reads,sequence;
    unsigned stuck_cal,missing_ldo,ignore_reset,inject_after_dr,good_values,stuck_ready,dr_keeps_eoc;
    uint32_t ignore_write;
    uint32_t now,regulator_at[2],calibrated_at[2];
} model;
static uint32_t *at(model *m,uint32_t a) {
    for (unsigned i=0;i<m->n;++i) if (m->registers[i].addr==a) return &m->registers[i].value;
    assert(m->n<160u);m->registers[m->n]=(reg){a,0u};return &m->registers[m->n++].value;
}
static uint32_t read_reg(void *ctx,uint32_t a,unsigned width) {
    model *m=ctx;++m->reads;
    assert(width==(a==A_FACTORY?16u:32u));
    if (a==A_ADC1+A_CR || a==A_ADC3+A_CR) {
        unsigned i=a==A_ADC1+A_CR?0u:1u;
        if ((*at(m,a)&A_CAL) && !m->stuck_cal && ++m->cal_reads[i]>3u) {
            *at(m,a)&=~A_CAL;*at(m,a)|=A_LINEAR_READY;
            m->calibrated_at[i]=m->now;
        }
    }
    if ((a==A_ADC1+A_ISR || a==A_ADC3+A_ISR) &&
        (*at(m,a-A_ISR+A_CR)&A_ADSTART) && ++m->conversion_reads>2u) {
        *at(m,a)|=A_EOC|A_EOS|A_EOSMP;*at(m,a-A_ISR+A_CR)&=~A_ADSTART;
    }
    uint32_t value=*at(m,a);
    if (a==A_ADC1+A_DR || a==A_ADC3+A_DR) {
        if (!m->dr_keeps_eoc) *at(m,a-A_DR+A_ISR)&=~A_EOC;
        if (m->inject_after_dr) *at(m,a-A_DR+A_ISR)|=A_OVR;
    }
    return value;
}
static void write_reg(void *ctx,uint32_t a,uint32_t v,unsigned width) {
    model *m=ctx;++m->writes;assert(width==32u);
    /* This model grants only ADC registers, two analog pin fields and their
     * clock/reset fields. A stray output, flash, DMA or peripheral write fails. */
    unsigned allowed=0u;uint32_t mask=0xffffffffu;
    if (a==A_ENABLE12 || a==A_RESET12) {allowed=1u;mask=A_GATE12;}
    if (a==A_ENABLE3) {allowed=1u;mask=A_GATE3|3u;}
    if (a==A_RESET3) {allowed=1u;mask=A_GATE3;}
    if (a==A_D3CCIPR) {allowed=1u;mask=0x30000u;}
    if (a==A_GPIOA || a==A_GPIOA+12u) {allowed=1u;mask=3u<<12;}
    if (a==A_GPIOB || a==A_GPIOB+12u) {allowed=1u;mask=3u<<2;}
    if (a==A_COMMON12+A_CCR || a==A_COMMON3+A_CCR) allowed=1u;
    const unsigned offsets[]={A_ISR,A_IER,A_CR,A_ADC_CFGR,A_ADC_CFGR2,
                              A_SMPR1,A_SMPR2,A_PCSEL,A_SQR1,A_DIFSEL};
    for (unsigned i=0;i<sizeof(offsets)/sizeof(offsets[0]);++i)
        if (a==A_ADC1+offsets[i] || a==A_ADC3+offsets[i]) allowed=1u;
    assert(allowed && !((v^*at(m,a))&~mask));
    if (m->ignore_write==a) return;
    if (a==A_ADC1+A_ISR || a==A_ADC3+A_ISR) {
        assert(!(v&~A_FLAGS));*at(m,a)&=~v;return;
    }
    if (a==A_RESET12 || a==A_RESET3) {
        if (v&(a==A_RESET12?A_GATE12:A_GATE3)) {
            for (unsigned i=0;i<3u;++i) {
                uint32_t b=i==0u?A_ADC1:i==1u?A_ADC2:A_ADC3;
                if ((a==A_RESET12 && i<2u) || (a==A_RESET3 && i==2u)) {
                    if (!m->ignore_reset) {
                        for (unsigned j=0;j<m->n;++j)
                            if (m->registers[j].addr>=b && m->registers[j].addr<b+0x100u) m->registers[j].value=0u;
                        *at(m,b+A_CR)=A_DEEP;
                    }
                }
            }
        }
    }
    if (a==A_COMMON12+A_CCR || a==A_COMMON3+A_CCR || a==A_D3CCIPR) {
        assert(!(*at(m,A_ADC1+A_CR)&(A_ADEN|A_CAL)));
        assert(!(*at(m,A_ADC2+A_CR)&(A_ADEN|A_CAL)));
        assert(!(*at(m,A_ADC3+A_CR)&(A_ADEN|A_CAL)));
    }
    if (a==A_ADC1+A_CR || a==A_ADC3+A_CR) {
        uint32_t old=*at(m,a),b=a-A_CR;
        if (v&A_CAL) {
            assert(!(old&A_ADEN));assert((v&(A_REGULATOR|A_LINEAR|A_DIFF|A_DEEP))==(A_REGULATOR|A_LINEAR));
            assert((uint32_t)(m->now-m->regulator_at[b==A_ADC1?0u:1u])>=1u);
            assert(!(*at(m,(b==A_ADC1?A_ADC3:A_ADC1)+A_CR)&(A_CAL|A_ADSTART)));
        }
        if (v&A_ADEN) {
            assert(!(v&A_CAL));assert(v&A_REGULATOR);
            if (!(old&A_ADEN))
                assert((uint32_t)(m->now-m->calibrated_at[b==A_ADC1?0u:1u])>=1u);
            if (!(old&A_ADEN) && !m->stuck_ready) *at(m,b+A_ISR)|=A_ADRDY;
        }
        if ((v&A_REGULATOR) && !(old&A_REGULATOR)) m->regulator_at[b==A_ADC1?0u:1u]=m->now;
        if (v&A_REGULATOR && !m->missing_ldo) *at(m,b+A_ISR)|=A_LDORDY;
        if (v&A_ADSTART && !(old&A_ADSTART)) {
            static const unsigned units[5]={3,1,1,3,3},channels[5]={19,3,5,17,19};
            m->sequence%=5u;assert(units[m->sequence]==(b==A_ADC1?1u:3u));
            assert(*at(m,b+A_SQR1)==channels[m->sequence]<<6);
            assert(!(*at(m,b+A_ISR)&A_EOC));
            assert(!(*at(m,(b==A_ADC1?A_ADC3:A_ADC1)+A_CR)&A_ADSTART));
            static const uint32_t good[5]={375u,140u,155u,256u,375u};
            *at(m,b+A_DR)=m->good_values?good[m->sequence]:300u+m->sequence;
            ++m->sequence;m->conversion_reads=0u;
        }
    }
    for (unsigned i=0;i<2u;++i) {
        uint32_t b=i?A_ADC3:A_ADC1;
        if (a==b+A_ADC_CFGR || a==b+A_SMPR1 || a==b+A_SMPR2 || a==b+A_SQR1 || a==b+A_IER) {
            assert(*at(m,b+A_CR)&A_ADEN);assert(!(*at(m,b+A_CR)&A_ADSTART));
        }
    }
    *at(m,a)=v;
}
static void setup(model *m,r10_adc_port *p,uint32_t revision) {
    memset(m,0,sizeof(*m));memset(p,0,sizeof(*p));
    p->io=(r10_adc_mmio){m,read_reg,write_reg};
    *at(m,A_RCC_CR)=5u;*at(m,A_IDCODE)=(revision<<16)|0x450u;*at(m,A_FACTORY)=24000u;
    *at(m,A_ADC1+A_CR)=A_DEEP;*at(m,A_ADC2+A_CR)=A_DEEP;*at(m,A_ADC3+A_CR)=A_DEEP;
    *at(m,A_GPIOA)=0xa5a5a5a5u;*at(m,A_GPIOB)=0x5a5a5a5au;
    *at(m,A_GPIOA+12u)=0x55555555u;*at(m,A_GPIOB+12u)=0xaaaaaaaau;
}
static int initialized_at(r10_adc_port *p,r10_voltage_config *c,uint32_t *detail,uint32_t started) {
    model *m=p->io.context;
    for (uint32_t elapsed=0u;elapsed<500u;++elapsed) {
        m->now=started+elapsed;
        int rc=r10_adc_initialize(p,m->now,c,detail);
        if (rc!=R10_VOLTAGE_IO_BUSY) return rc;
    }
    assert(0);return -1;
}
static int initialized(r10_adc_port *p,r10_voltage_config *c,uint32_t *detail) {
    return initialized_at(p,c,detail,0u);
}
int main(void) {
    model m;r10_adc_port p;r10_voltage_config c;uint32_t detail=0u,raw=0u;
    const uint32_t revisions[]={0x1003u,0x2001u,0x2003u,0x2007u};
    for (unsigned i=0;i<4u;++i) {
        uint32_t revision=revisions[i];setup(&m,&p,revision);
        /* Only V is documented to expose LDORDY. Timed regulator guards
         * still apply to every revision, including those without this bit. */
        if (revision!=0x2003u) m.missing_ldo=1u;
        assert(initialized(&p,&c,&detail)==R10_VOLTAGE_IO_OK);
        assert(c.revision==revision && c.sample_bits==10u && c.calibration==24000u);
        assert(c.adc12_hz==(i?2000000u:4000000u));assert(c.adc3_hz==c.adc12_hz);
        assert((*at(&m,A_GPIOA)&~(3u<<12))==(0xa5a5a5a5u&~(3u<<12)));
        assert((*at(&m,A_GPIOB)&~(3u<<2))==(0x5a5a5a5au&~(3u<<2)));
        for (unsigned slot=0;slot<5u;++slot) {
            assert(!r10_adc_start(&p,slot,&detail));int rc=1;unsigned n=0;
            while (rc==R10_VOLTAGE_IO_BUSY && n++<10u) rc=r10_adc_poll(&p,&raw,&detail);
            assert(rc==R10_VOLTAGE_IO_OK && raw==300u+slot);
        }
        assert(!r10_adc_cancel(&p,&detail));assert(p.phase==A_NEW && !p.active && !p.owned);
    }
    const uint32_t unknown[]={0u,0x1002u,0x2002u,0x2004u,0x2008u,0xffffu};
    for (unsigned i=0;i<sizeof(unknown)/sizeof(unknown[0]);++i) {
        setup(&m,&p,unknown[i]);assert(initialized(&p,&c,&detail)==-1 && !m.writes);
    }
    setup(&m,&p,0x2003u);assert(!initialized_at(&p,&c,&detail,0xfffffffcu));
    /* Multiple wakes in one tick must not consume either settling guard. */
    setup(&m,&p,0x2003u);m.now=100u;
    assert(r10_adc_initialize(&p,m.now,&c,&detail)==R10_VOLTAGE_IO_BUSY);
    unsigned guard_writes=m.writes;
    for (unsigned i=0;i<12u;++i) {
        assert(r10_adc_initialize(&p,m.now,&c,&detail)==R10_VOLTAGE_IO_BUSY);
        assert(p.phase==A_REGULATOR_WAIT && m.writes==guard_writes);
    }
    m.now=101u;
    for (unsigned i=0;i<12u;++i)
        assert(r10_adc_initialize(&p,m.now,&c,&detail)==R10_VOLTAGE_IO_BUSY);
    assert(p.phase==A_CAL1_GUARD && !(*at(&m,A_ADC1+A_CR)&A_ADEN));
    assert(!initialized_at(&p,&c,&detail,102u));
    setup(&m,&p,0x2003u);*at(&m,A_RCC_CR)|=8u;assert(initialized(&p,&c,&detail)==-1 && !m.writes);
    setup(&m,&p,0x2003u);*at(&m,A_ENABLE12)|=A_GATE12;assert(initialized(&p,&c,&detail)==-1 && !m.writes);
    assert(!r10_adc_cancel(&p,&detail) && !m.writes);
    setup(&m,&p,0x2003u);m.stuck_cal=1u;assert(initialized(&p,&c,&detail)==-1);assert((detail>>24)==A_FAIL_CALIBRATION);
    setup(&m,&p,0x2003u);m.missing_ldo=1u;assert(initialized(&p,&c,&detail)==-1);assert((detail>>24)==A_FAIL_REGULATOR);
    setup(&m,&p,0x2003u);assert(!initialized(&p,&c,&detail));*at(&m,A_ADC3+A_ISR)|=A_EOC;
    unsigned before=m.writes;assert(r10_adc_start(&p,0u,&detail)==-1 && m.writes==before);
    assert(*at(&m,A_ADC3+A_ISR)&A_EOC);
    setup(&m,&p,0x2003u);assert(!initialized(&p,&c,&detail));assert(!r10_adc_start(&p,0u,&detail));m.inject_after_dr=1u;
    int rc=1;for (unsigned n=0;n<10u && rc==1;++n) rc=r10_adc_poll(&p,&raw,&detail);
    assert(rc==-1 && (detail>>24)==A_FAIL_DATA && p.last_dr==300u && (p.last_isr&A_OVR));
    m.ignore_reset=1u;assert(r10_adc_cancel(&p,&detail)==-1 && (detail>>24)==A_FAIL_CLEANUP);
    for (unsigned which=0;which<9u;++which) {
        setup(&m,&p,0x2003u);assert(!initialized(&p,&c,&detail));
        if (which==0u) *at(&m,A_ADC1+A_ADC_CFGR)|=1u;
        else if (which==1u) *at(&m,A_ENABLE12)&=~A_GATE12;
        else if (which==2u) *at(&m,A_ADC2+A_CR)|=A_ADEN;
        else if (which==3u) *at(&m,A_ADC1+A_CR)|=A_ADSTART;
        else if (which==4u) *at(&m,A_GPIOA)&=~(3u<<12);
        else if (which==5u) *at(&m,A_GPIOB)&=~(3u<<2);
        else if (which==6u) *at(&m,A_GPIOA+12u)|=1u<<12;
        else if (which==7u) *at(&m,A_GPIOB+12u)|=1u<<2;
        else *at(&m,A_ENABLE3)&=~1u;
        before=m.writes;assert(r10_adc_start(&p,0u,&detail)==-1 && m.writes==before);
    }
    const uint32_t ignored[]={A_ENABLE12,A_ENABLE3,A_RESET12,A_RESET3,A_GPIOA,
        A_COMMON3+A_CCR,A_ADC1+A_ADC_CFGR,A_ADC1+A_SMPR1,A_ADC3+A_CR};
    for (unsigned i=0;i<sizeof(ignored)/sizeof(ignored[0]);++i) {
        setup(&m,&p,0x2003u);m.ignore_write=ignored[i];
        assert(initialized(&p,&c,&detail)==R10_VOLTAGE_IO_ERROR);
    }
    setup(&m,&p,0x2003u);m.stuck_ready=1u;
    assert(initialized(&p,&c,&detail)==-1 && (detail>>24)==A_FAIL_READY);
    for (unsigned mode=0;mode<2u;++mode) {
        setup(&m,&p,0x2003u);assert(!initialized(&p,&c,&detail));
        if (mode==0u) m.ignore_write=A_ADC3+A_ISR;else m.dr_keeps_eoc=1u;
        assert(!r10_adc_start(&p,0u,&detail));rc=1;
        for (unsigned i=0;i<10u && rc==1;++i) rc=r10_adc_poll(&p,&raw,&detail);
        assert(rc==-1 && (detail>>24)==A_FAIL_DATA);
    }
    /* Execute the real portable acquisition core against this MMIO adapter. */
    setup(&m,&p,0x2003u);m.good_values=1u;
    r10_voltage_io io={&p,r10_adc_initialize,r10_adc_start,r10_adc_poll,r10_adc_cancel};
    r10_voltage v;r10_voltage_begin(&v,&io,0u);uint32_t now=0u;
    for (;now<500u && !v.samples && !v.error;++now) {
        m.now=now;
        unsigned accesses=m.reads+m.writes;r10_voltage_poll(&v,now);
        assert(m.reads+m.writes-accesses<140u);
    }
    assert(v.samples==1u && v.valid && r10_voltage_fresh(&v,now));
    assert(v.sample_config.revision==0x2003u && v.raw_mask==31u);
    assert(v.values.vdda_mv>=3290u && v.values.vdda_mv<=3300u);
    assert(v.values.logic_mv>4900u && v.values.logic_mv<5000u);
    r10_voltage_values saved=v.values;uint32_t last=v.last_good_ms;
    *at(&m,A_ADC3+A_ISR)|=A_OVR;now=last+R10_VOLTAGE_PERIOD_MS;
    r10_voltage_poll(&v,now++);r10_voltage_poll(&v,now++);
    assert(v.error && !v.valid && v.samples==1u && !r10_voltage_fresh(&v,now));
    assert(v.last_good_ms==last && !memcmp(&v.values,&saved,sizeof(saved)));
    puts("ADC MMIO sequencing and fault cases passed; not linked or hardware tested");
    return 0;
}
