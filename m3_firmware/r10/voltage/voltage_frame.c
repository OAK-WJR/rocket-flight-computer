#include "voltage_frame.h"
void r10_pack_voltage(uint32_t f[256],const r10_voltage *v,const r10_adc_port *p) {
    f[128]=v->state;f[129]=v->error;f[130]=v->last_error;
    f[131]=v->detail;f[132]=v->last_error_detail;
    f[133]=v->cleanup_error;f[134]=v->cleanup_detail;
    f[135]=v->stage_at;f[136]=v->batch_at;f[137]=v->observed_ms;f[138]=v->last_good_ms;
    f[139]=v->samples;f[140]=v->failures;f[141]=v->retries;f[142]=v->slot;f[143]=v->raw_mask;
    f[144]=(uint32_t)v->valid|((uint32_t)v->has_sample<<1);
    for (unsigned i=0;i<5u;++i) {
        f[145u+i]=v->raw[i];f[150u+i]=v->raw_ms[i];
        f[155u+i]=v->sample_raw[i];f[160u+i]=v->sample_ms[i];
    }
    f[165]=v->config.revision;f[166]=v->config.calibration;f[167]=v->config.sample_bits;
    f[168]=v->config.adc12_hz;f[169]=v->config.adc3_hz;
    f[170]=v->sample_config.revision;f[171]=v->sample_config.calibration;f[172]=v->sample_config.sample_bits;
    f[173]=v->sample_config.adc12_hz;f[174]=v->sample_config.adc3_hz;
    f[175]=v->values.vdda_mv;f[176]=v->values.logic_mv;f[177]=v->values.camera_mv;
    f[178]=v->values.v3v3_coarse_mv;f[179]=v->values.reference_drift_permille;
    f[180]=p->phase;f[181]=p->phase_ms;f[182]=p->revision;f[183]=p->calibration;
    f[184]=p->nominal_adc_hz;f[185]=p->calibration1;f[186]=p->calibration3;
    f[187]=p->last_cr;f[188]=p->last_isr;f[189]=p->last_dr;f[190]=p->unit;f[191]=p->detail;
    f[192]=(uint32_t)p->owned|((uint32_t)p->active<<1);
}
