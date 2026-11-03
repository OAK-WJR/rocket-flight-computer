/* Actual acquisition core + actual ADC adapter + scripted MMIO + ABI4 packer. */
#define main r10_adc_model_cases
#include "test_adc.c"
#undef main
#include "voltage_frame.h"
static unsigned bad_read;
static uint32_t fixture_read(void *ctx,uint32_t address,unsigned width) {
    model *m=ctx;uint32_t value=read_reg(ctx,address,width);
    if (address==A_ADC1+A_DR && bad_read==4u && m->sequence==2u) return 0xffffffffu;
    if (address==A_ADC3+A_DR && bad_read==5u && m->sequence==5u) return 400u;
    return value;
}
void r10_voltage_fixture(uint32_t f[256],unsigned mode,uint32_t base) {
    memset(f,0,256u*sizeof(*f));f[9]=0x20030450u;f[5]=base;
    model m;r10_adc_port p;r10_voltage v={0};setup(&m,&p,0x2003u);
    if (!mode) {r10_pack_voltage(f,&v,&p);return;}
    m.good_values=1u;p.io.read=fixture_read;bad_read=0u;
    r10_voltage_io io={&p,r10_adc_initialize,r10_adc_start,r10_adc_poll,r10_adc_cancel};
    r10_voltage_begin(&v,&io,base);uint32_t step=0u;
    for (;step<500u && !v.samples && !v.error;++step) {
        m.now=base+step;r10_voltage_poll(&v,m.now);
    }
    assert(v.samples==1u && v.valid && !v.error);
    if (mode>=2u) {
        if (mode==2u || mode==3u) *at(&m,A_ADC3+A_ISR)|=A_OVR;
        if (mode==3u) m.ignore_reset=1u;
        if (mode==4u || mode==5u) bad_read=mode;
        if (mode==6u) *at(&m,A_GPIOA)&=~(3u<<12);
        uint32_t started=v.last_good_ms+250u;
        for (step=0u;step<150u && !v.error;++step) {
            m.now=started+step;r10_voltage_poll(&v,m.now);
        }
        assert(v.error && !v.valid && v.has_sample);
    }
    f[5]=m.now+1u;r10_pack_voltage(f,&v,&p);
}
void r10_voltage_pack_sentinels(uint32_t f[256]) {
    for (unsigned i=0;i<256u;++i) f[i]=0xa5a5a5a5u;
    r10_voltage v={0};r10_adc_port p={0};r10_pack_voltage(f,&v,&p);
}

void r10_test_voltage_record(uint32_t f[256],unsigned mode) {
    uint32_t local[256];r10_voltage_fixture(local,mode,f[5]-500u);
    for (unsigned i=128u;i<193u;++i) f[i]=local[i];
}
