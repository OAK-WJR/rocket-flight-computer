#include "imu_frame.h"
static uint32_t pair(int16_t a,int16_t b) {
    return (uint32_t)(uint16_t)a|((uint32_t)(uint16_t)b<<16);
}
void r10_pack_imu(uint32_t f[64],const r10_imu *d) {
    f[45]=d->state;f[46]=d->error;
    f[47]=(uint32_t)d->who|((uint32_t)d->status_reg<<8)|((uint32_t)d->valid_mask<<16)|
          ((uint32_t)d->has_sample<<24);
    f[48]=d->samples;f[49]=d->last_good_ms;f[50]=d->endpoint_mask;
    for(unsigned i=0;i<5;++i)f[51u+i]=pair(d->raw[2u*i],d->raw[2u*i+1u]);
    for(unsigned i=0;i<2;++i) {
        f[56u+i]=(uint32_t)d->config[4u*i]|((uint32_t)d->config[4u*i+1u]<<8)|
                  ((uint32_t)d->config[4u*i+2u]<<16)|((uint32_t)d->config[4u*i+3u]<<24);
    }
    f[58]=d->bus_errors;f[59]=d->nominal_bus_hz;f[60]=d->bus_detail;
    f[61]=d->retry_count;f[62]=d->last_error;
}
