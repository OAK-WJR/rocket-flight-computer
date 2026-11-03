#include "baro_frame.h"
void r10_pack_baro(uint32_t *f,const r10_baro *d) {
    f[64]=d->state;f[65]=d->error;
    f[66]=d->valid_mask|((uint32_t)d->has_sample<<8)|((uint32_t)d->prom_valid<<9);
    f[67]=d->samples;f[68]=d->last_good_ms;
    f[69]=d->d1;f[70]=d->d2;f[71]=d->d1_ms;f[72]=d->d2_ms;
    f[73]=d->sample_d1;f[74]=d->sample_d2;
    f[75]=(uint32_t)d->pressure_pa;f[76]=(uint32_t)d->temp_centic;
    for(unsigned i=0;i<4;++i) {
        f[77u+i]=d->prom[2u*i]|((uint32_t)d->prom[2u*i+1u]<<16);
        f[81u+i]=d->sample_prom[2u*i]|((uint32_t)d->sample_prom[2u*i+1u]<<16);
    }
    f[85]=d->prom_mask;f[86]=d->crc_calculated|((uint32_t)d->crc_stored<<8);
    f[87]=d->bus_errors;f[88]=d->nominal_bus_hz;f[89]=d->bus_detail;
    f[90]=d->retry_count;f[91]=d->last_error;f[92]=d->sample_d1_ms;f[93]=d->sample_d2_ms;
    f[94]=(uint32_t)d->candidate_pressure_pa;f[95]=(uint32_t)d->candidate_temp_centic;
    f[96]=d->acquisition_started_ms;f[97]=d->sample_started_ms;
}
