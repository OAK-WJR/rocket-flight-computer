#include "adc_port.h"

static uint32_t rd(r10_adc_port *p,uint32_t address) {return p->io.read(p->io.context,address,32u);}
static void wr(r10_adc_port *p,uint32_t address,uint32_t value) {p->io.write(p->io.context,address,value,32u);}
static void modify(r10_adc_port *p,uint32_t a,uint32_t mask,uint32_t value) {wr(p,a,(rd(p,a)&~mask)|value);}
static int fail(r10_adc_port *p,unsigned reason,uint32_t *detail) {
    p->detail=(reason<<24)|((p->phase&15u)<<20)|((p->unit&3u)<<16)|(p->last_isr&0xffffu);
    p->phase=A_ERROR;if (detail) *detail=p->detail;return R10_VOLTAGE_IO_ERROR;
}
static int clock_ok(r10_adc_port *p,unsigned own) {
    if ((rd(p,A_RCC_CR)&0x1du)!=5u || (rd(p,A_CFGR)&0x3fu) ||
        (rd(p,A_D1CFGR)&0xf0fu) || (rd(p,A_D1CCIPR)&0x30000000u)) return 0;
    if (own && ((rd(p,A_D3CCIPR)&0x30000u)!=0x20000u ||
        !(rd(p,A_ENABLE12)&A_GATE12) ||
        (rd(p,A_ENABLE3)&(A_GATE3|3u))!=(A_GATE3|3u))) return 0;
    return 1;
}
static int reset_owned(r10_adc_port *p) {
    modify(p,A_RESET12,A_GATE12,A_GATE12);modify(p,A_RESET3,A_GATE3,A_GATE3);
    if (!(rd(p,A_RESET12)&A_GATE12) || !(rd(p,A_RESET3)&A_GATE3)) return 0;
    modify(p,A_RESET12,A_GATE12,0u);modify(p,A_RESET3,A_GATE3,0u);
    if ((rd(p,A_RESET12)&A_GATE12) || (rd(p,A_RESET3)&A_GATE3)) return 0;
    for (unsigned i=0;i<3u;++i) {
        uint32_t a=i==0u?A_ADC1:i==1u?A_ADC2:A_ADC3;
        if (rd(p,a+A_CR)!=A_DEEP) return 0;
    }
    return 1;
}
static int configure(r10_adc_port *p,uint32_t a) {
    uint32_t cr=rd(p,a+A_CR);
    if ((cr&A_CONTROLS)!=A_ADEN || !(cr&A_REGULATOR) || (cr&A_DEEP)) return 0;
    wr(p,a+A_IER,0u);wr(p,a+A_ADC_CFGR,A_SETTINGS);wr(p,a+A_ADC_CFGR2,0u);
    wr(p,a+A_SMPR1,a==A_ADC1?A_SAMPLE1:0u);
    wr(p,a+A_SMPR2,a==A_ADC3?A_SAMPLE3:0u);
    wr(p,a+A_PCSEL,a==A_ADC1?A_PRESELECT1:A_PRESELECT3);
    wr(p,a+A_SQR1,(a==A_ADC1?3u:19u)<<6);
    wr(p,a+A_ISR,A_FLAGS); /* Only own post-reset initialization flags. */
    return rd(p,a+A_ADC_CFGR)==A_SETTINGS && !rd(p,a+A_IER) && !rd(p,a+A_ADC_CFGR2) &&
        rd(p,a+A_SMPR1)==(a==A_ADC1?A_SAMPLE1:0u) &&
        rd(p,a+A_SMPR2)==(a==A_ADC3?A_SAMPLE3:0u) &&
        rd(p,a+A_PCSEL)==(a==A_ADC1?A_PRESELECT1:A_PRESELECT3);
}
int r10_adc_initialize(void *ctx,uint32_t now,r10_voltage_config *config,uint32_t *detail) {
    r10_adc_port *p=ctx;
    if (!p || !config || !detail || !p->io.read || !p->io.write) {
        if (detail) {*detail=A_FAIL_ADAPTER<<24;}
        return R10_VOLTAGE_IO_ERROR;
    }
    if (p->phase==A_ERROR) {*detail=p->detail;return R10_VOLTAGE_IO_ERROR;}
    if (!clock_ok(p,p->owned)) return fail(p,A_FAIL_CLOCK,detail);
    *detail=0u;
    if (p->phase!=A_NEW && p->phase!=A_READY && (uint32_t)(now-p->phase_ms)>=200u)
        return fail(p,p->phase==A_REGULATOR_WAIT?A_FAIL_REGULATOR:
                    (p->phase==A_READY1_WAIT || p->phase==A_READY3_WAIT)?A_FAIL_READY:A_FAIL_CALIBRATION,detail);
    switch (p->phase) {
    case A_NEW: {
        uint32_t id=rd(p,A_IDCODE);p->revision=id>>16;
        /* ES0392 Rev16 Table2: explicit IDs, never an open-ended >= check.
         * Nominal post-Y divide-by-two follows the pinned ST HAL algorithm;
         * it is configuration metadata, not a measured analog clock. */
        if ((id&0xfffu)!=0x450u || (p->revision!=0x1003u && p->revision!=0x2001u &&
                                  p->revision!=0x2003u && p->revision!=0x2007u))
            return fail(p,A_FAIL_ID,detail);
        p->calibration=p->io.read(p->io.context,A_FACTORY,16u);
        if (p->calibration<20000u || p->calibration>30000u) return fail(p,A_FAIL_FACTORY,detail);
        if ((rd(p,A_ENABLE12)&A_GATE12) || (rd(p,A_ENABLE3)&A_GATE3)) return fail(p,A_FAIL_OWNERSHIP,detail);
        p->owned=1u;
        modify(p,A_ENABLE12,A_GATE12,A_GATE12);modify(p,A_ENABLE3,A_GATE3|3u,A_GATE3|3u);
        if (!(rd(p,A_ENABLE12)&A_GATE12) || (rd(p,A_ENABLE3)&(A_GATE3|3u))!=(A_GATE3|3u))
            return fail(p,A_FAIL_ENABLE,detail);
        if (!reset_owned(p)) return fail(p,A_FAIL_RESET,detail);
        /* The common clock source can change only once every ADC is disabled. */
        modify(p,A_D3CCIPR,0x30000u,0x20000u);
        if (!clock_ok(p,1u)) return fail(p,A_FAIL_CLOCK,detail);
        modify(p,A_GPIOA,3u<<12,3u<<12);modify(p,A_GPIOA+12u,3u<<12,0u);
        modify(p,A_GPIOB,3u<<2,3u<<2);modify(p,A_GPIOB+12u,3u<<2,0u);
        if ((rd(p,A_GPIOA)&(3u<<12))!=(3u<<12) || (rd(p,A_GPIOA+12u)&(3u<<12)) ||
            (rd(p,A_GPIOB)&(3u<<2))!=(3u<<2) || (rd(p,A_GPIOB+12u)&(3u<<2)))
            return fail(p,A_FAIL_CONFIG,detail);
        wr(p,A_COMMON12+A_CCR,A_PRESCALER);wr(p,A_COMMON3+A_CCR,A_PRESCALER|A_INTERNAL);
        if (rd(p,A_COMMON12+A_CCR)!=A_PRESCALER || rd(p,A_COMMON3+A_CCR)!=(A_PRESCALER|A_INTERNAL))
            return fail(p,A_FAIL_CONFIG,detail);
        for (unsigned i=0;i<2u;++i) {
            uint32_t a=i?A_ADC3:A_ADC1;
            wr(p,a+A_DIFSEL,0u);wr(p,a+A_CR,0u);wr(p,a+A_CR,A_REGULATOR);
        }
        p->nominal_adc_hz=p->revision==0x1003u?4000000u:2000000u;
        p->phase=A_REGULATOR_WAIT;p->phase_ms=now;return R10_VOLTAGE_IO_BUSY;
    }
    case A_REGULATOR_WAIT:
        if ((uint32_t)(now-p->phase_ms)<1u) return R10_VOLTAGE_IO_BUSY;
        for (unsigned i=0;i<2u;++i) {
            uint32_t a=i?A_ADC3:A_ADC1;p->unit=i?3u:1u;
            p->last_cr=rd(p,a+A_CR);p->last_isr=rd(p,a+A_ISR);
            if (p->last_cr!=A_REGULATOR || (p->revision==0x2003u && !(p->last_isr&A_LDORDY)))
                return fail(p,A_FAIL_REGULATOR,detail);
        }
        p->unit=1u;wr(p,A_ADC1+A_CR,A_REGULATOR|A_LINEAR|A_CAL);
        if (!(rd(p,A_ADC1+A_CR)&A_CAL)) return fail(p,A_FAIL_CALIBRATION,detail);
        p->phase=A_CAL1_WAIT;p->phase_ms=now;return R10_VOLTAGE_IO_BUSY;
    case A_CAL1_WAIT:
    case A_CAL3_WAIT: {
        uint32_t a=p->phase==A_CAL1_WAIT?A_ADC1:A_ADC3;p->unit=a==A_ADC1?1u:3u;
        p->last_cr=rd(p,a+A_CR);
        if (p->last_cr&A_CAL) return R10_VOLTAGE_IO_BUSY;
        if ((p->last_cr&A_LINEAR_READY)!=A_LINEAR_READY || (p->last_cr&A_CONTROLS))
            return fail(p,A_FAIL_CALIBRATION,detail);
        uint32_t cal=rd(p,a+A_CALFACT);
        if (a==A_ADC1) p->calibration1=cal;else p->calibration3=cal;
        p->phase=a==A_ADC1?A_CAL1_GUARD:A_CAL3_GUARD;p->phase_ms=now;
        return R10_VOLTAGE_IO_BUSY;
    }
    case A_CAL1_GUARD:
    case A_CAL3_GUARD: {
        if ((uint32_t)(now-p->phase_ms)<1u) return R10_VOLTAGE_IO_BUSY;
        uint32_t a=p->phase==A_CAL1_GUARD?A_ADC1:A_ADC3;
        modify(p,a+A_CR,A_LINEAR,0u);wr(p,a+A_ISR,A_ADRDY);modify(p,a+A_CR,A_ADEN,A_ADEN);
        p->phase=a==A_ADC1?A_READY1_WAIT:A_READY3_WAIT;p->phase_ms=now;
        return R10_VOLTAGE_IO_BUSY;
    }
    case A_READY1_WAIT:
    case A_READY3_WAIT: {
        uint32_t a=p->phase==A_READY1_WAIT?A_ADC1:A_ADC3;p->unit=a==A_ADC1?1u:3u;
        p->last_cr=rd(p,a+A_CR);p->last_isr=rd(p,a+A_ISR);
        if (!(p->last_isr&A_ADRDY)) return R10_VOLTAGE_IO_BUSY;
        if (!configure(p,a)) return fail(p,A_FAIL_CONFIG,detail);
        if (a==A_ADC1) {
            p->unit=3u;wr(p,A_ADC3+A_CR,A_REGULATOR|A_LINEAR|A_CAL);
            if (!(rd(p,A_ADC3+A_CR)&A_CAL)) return fail(p,A_FAIL_CALIBRATION,detail);
            p->phase=A_CAL3_WAIT;p->phase_ms=now;return R10_VOLTAGE_IO_BUSY;
        }
        p->phase=A_READY;
        break;
    }
    case A_READY:break;
    default:return fail(p,A_FAIL_ADAPTER,detail);
    }
    *config=(r10_voltage_config){p->revision,p->calibration,10u,p->nominal_adc_hz,p->nominal_adc_hz};
    return R10_VOLTAGE_IO_OK;
}
static int settings_ok(r10_adc_port *p) {
    if (rd(p,A_ADC2+A_CR)!=A_DEEP) return 0;
    if ((rd(p,A_GPIOA)&(3u<<12))!=(3u<<12) || (rd(p,A_GPIOA+12u)&(3u<<12)) ||
        (rd(p,A_GPIOB)&(3u<<2))!=(3u<<2) || (rd(p,A_GPIOB+12u)&(3u<<2))) return 0;
    if (!clock_ok(p,1u) || rd(p,A_COMMON12+A_CCR)!=A_PRESCALER ||
        rd(p,A_COMMON3+A_CCR)!=(A_PRESCALER|A_INTERNAL)) return 0;
    for (unsigned i=0;i<2u;++i) {
        uint32_t a=i?A_ADC3:A_ADC1, cr=rd(p,a+A_CR);
        uint32_t allowed=(p->active && p->unit==(i?3u:1u))?A_ADSTART:0u;
        if ((cr&(A_CONTROLS&~allowed))!=A_ADEN || !(cr&A_REGULATOR) || (cr&(A_DEEP|A_BOOST|A_LINEAR))) return 0;
        if (p->revision==0x2003u && !(rd(p,a+A_ISR)&A_LDORDY)) return 0;
        if (rd(p,a+A_ADC_CFGR)!=A_SETTINGS || rd(p,a+A_ADC_CFGR2) || rd(p,a+A_IER) ||
            rd(p,a+A_DIFSEL) || rd(p,a+A_SMPR1)!=(i?0u:A_SAMPLE1) ||
            rd(p,a+A_SMPR2)!=(i?A_SAMPLE3:0u) || rd(p,a+A_PCSEL)!=(i?A_PRESELECT3:A_PRESELECT1)) return 0;
    }
    return 1;
}
int r10_adc_start(void *ctx,unsigned slot,uint32_t *detail) {
    r10_adc_port *p=ctx;
    if (!p || !detail || p->phase!=A_READY || p->active || slot>=5u) {
        if (detail) {*detail=A_FAIL_ARGUMENT<<24;}
        return R10_VOLTAGE_IO_ERROR;
    }
    if (!settings_ok(p)) return fail(p,A_FAIL_CONFIG,detail);
    uint32_t a=(slot==1u || slot==2u)?A_ADC1:A_ADC3,channel=slot==1u?3u:slot==2u?5u:slot==3u?17u:19u;
    p->unit=a==A_ADC1?1u:3u;
    for (unsigned i=0;i<2u;++i) {
        uint32_t cr=rd(p,(i?A_ADC3:A_ADC1)+A_CR);
        if ((cr&A_CONTROLS)!=A_ADEN || !(cr&A_REGULATOR) || (cr&(A_DEEP|A_BOOST))) return fail(p,A_FAIL_START,detail);
    }
    p->last_isr=rd(p,a+A_ISR);
    if (p->last_isr&(A_FLAGS&~A_ADRDY)) return fail(p,A_FAIL_STATUS,detail);
    wr(p,a+A_SQR1,channel<<6);
    if (rd(p,a+A_SQR1)!=(channel<<6)) return fail(p,A_FAIL_CONFIG,detail);
    modify(p,a+A_CR,A_ADSTART,A_ADSTART);p->last_cr=rd(p,a+A_CR);p->last_isr=rd(p,a+A_ISR);
    if (!(p->last_cr&A_ADSTART) && (p->last_isr&(A_EOC|A_EOS))!=(A_EOC|A_EOS)) return fail(p,A_FAIL_START,detail);
    p->active=1u;*detail=0u;return R10_VOLTAGE_IO_OK;
}
int r10_adc_poll(void *ctx,uint32_t *raw,uint32_t *detail) {
    r10_adc_port *p=ctx;
    if (!p || !raw || !detail || p->phase!=A_READY || !p->active) {
        if (detail) {*detail=A_FAIL_ARGUMENT<<24;}
        return R10_VOLTAGE_IO_ERROR;
    }
    if (!settings_ok(p)) return fail(p,A_FAIL_CONFIG,detail);
    uint32_t a=p->unit==1u?A_ADC1:A_ADC3;
    p->last_cr=rd(p,a+A_CR);p->last_isr=rd(p,a+A_ISR);
    if (p->last_isr&A_UNEXPECTED || (p->last_cr&(A_CONTROLS&~A_ADSTART))!=A_ADEN)
        return fail(p,A_FAIL_STATUS,detail);
    if ((p->last_isr&(A_EOC|A_EOS))!=(A_EOC|A_EOS)) {
        if (!(p->last_cr&A_ADSTART)) return fail(p,A_FAIL_STATUS,detail);
        *detail=0u;return R10_VOLTAGE_IO_BUSY;
    }
    /* Conversion completion may occur between the earlier CR and ISR reads.
     * Re-observe CR; do not reject a normal, non-atomic status transition. */
    p->last_cr=rd(p,a+A_CR);
    if (p->last_cr&A_ADSTART) {*detail=0u;return R10_VOLTAGE_IO_BUSY;}
    p->last_dr=rd(p,a+A_DR);p->last_isr=rd(p,a+A_ISR);
    if (p->last_isr&(A_UNEXPECTED|A_EOC)) return fail(p,A_FAIL_DATA,detail);
    wr(p,a+A_ISR,A_EOS|A_EOSMP);p->last_isr=rd(p,a+A_ISR);
    if (p->last_isr&(A_FLAGS&~A_ADRDY)) return fail(p,A_FAIL_DATA,detail);
    *raw=p->last_dr;p->active=0u;*detail=0u;return R10_VOLTAGE_IO_OK;
}
int r10_adc_cancel(void *ctx,uint32_t *detail) {
    r10_adc_port *p=ctx;
    if (!p || !detail || !p->io.read || !p->io.write) {
        if (detail) {*detail=A_FAIL_ADAPTER<<24;}
        return R10_VOLTAGE_IO_ERROR;
    }
    if (p->owned) {
        if (!reset_owned(p)) return fail(p,A_FAIL_CLEANUP,detail);
        modify(p,A_ENABLE12,A_GATE12,0u);modify(p,A_ENABLE3,A_GATE3,0u);
        if ((rd(p,A_ENABLE12)&A_GATE12) || (rd(p,A_ENABLE3)&A_GATE3)) return fail(p,A_FAIL_CLEANUP,detail);
    }
    p->owned=0u;p->active=0u;p->phase=A_NEW;*detail=0u;return R10_VOLTAGE_IO_OK;
}
