#include "flash_frame.h"
static void set(uint32_t f[256],unsigned logical,uint32_t value) {
    f[logical<30u?98u+logical:163u+logical]=value;
}
static uint32_t bytes4(const uint8_t *p) {
    return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);
}
void r10_pack_flash(uint32_t f[256],const r10_flash_ro *s,const r10_qspi_port *p) {
    const uint32_t core[19]={s->state,s->error,s->last_error,s->detail,s->last_error_detail,
        s->cleanup_error,s->cleanup_detail,s->stage_at,s->batch_at,s->observed_ms,s->last_good_ms,
        s->nominal_hz,s->sample_nominal_hz,s->samples,s->failures,s->retries,
        s->command,s->completed_mask,s->io_count};
    for (unsigned i=0;i<19u;++i) set(f,i,core[i]);
    for (unsigned i=0;i<8u;++i) {set(f,19u+i,s->command_ms[i]);set(f,27u+i,s->sample_command_ms[i]);}
    for (unsigned i=0;i<16u;++i) {
        set(f,35u+i,bytes4(&s->raw[i/2u][4u*(i%2u)]));
        set(f,53u+i,bytes4(&s->sample_raw[i/2u][4u*(i%2u)]));
    }
    for (unsigned i=0;i<2u;++i) set(f,51u+i,bytes4(&s->raw_count[i*4u]));
    set(f,69u,(uint32_t)s->valid|((uint32_t)s->has_sample<<1));
    const uint32_t port[14]={p->phase,p->phase_ms,p->revision,p->detail,p->last_cr,p->last_sr,
        p->last_ccr,p->last_dr,p->expected_ccr,p->expected_dlr,p->command,p->received,
        p->nominal_hz,(uint32_t)p->owned|((uint32_t)p->active<<1)|((uint32_t)p->parked<<2)};
    for (unsigned i=0;i<14u;++i) set(f,70u+i,port[i]);
}
