#include "voltage_core.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

/* Deliberately scripted conversions: these are not simulated ADC silicon. */
typedef struct {
    r10_voltage_config config;
    uint32_t raw[5], detail;
    unsigned init_calls, starts, reads, cancels, active, next_slot;
    uint32_t *clock, read_cost;
    int init_rc, start_rc, read_rc, cancel_rc;
} fixture;
static int initialize(void *ctx,uint32_t now,r10_voltage_config *c,uint32_t *detail) {
    fixture *f=ctx;(void)now;++f->init_calls;*c=f->config;*detail=f->detail;
    return f->init_rc;
}
static int start(void *ctx,unsigned slot,uint32_t *detail) {
    fixture *f=ctx;assert(!f->active);assert(slot==f->next_slot);
    ++f->starts;*detail=f->detail;
    if (f->start_rc==R10_VOLTAGE_IO_OK) f->active=1u;
    return f->start_rc;
}
static int read_value(void *ctx,uint32_t *raw,uint32_t *detail) {
    fixture *f=ctx;assert(f->active);++f->reads;*detail=f->detail;
    if (f->read_rc==R10_VOLTAGE_IO_OK) {
        *raw=f->raw[f->next_slot];f->next_slot=(f->next_slot+1u)%5u;f->active=0u;
    }
    if (f->clock) *f->clock+=f->read_cost;
    return f->read_rc;
}
static int cancel(void *ctx,uint32_t *detail) {
    fixture *f=ctx;++f->cancels;*detail=f->detail;
    if (f->cancel_rc==R10_VOLTAGE_IO_OK) {f->active=0u;f->next_slot=0u;}
    return f->cancel_rc;
}
static void setup(r10_voltage *v,fixture *f,uint32_t now) {
    memset(f,0,sizeof(*f));
    f->config=(r10_voltage_config){.revision=0x2003u,.calibration=24000u,
        .sample_bits=10u,.adc12_hz=2000000u,.adc3_hz=2000000u};
    const uint32_t raw[5]={375u,140u,155u,256u,375u};memcpy(f->raw,raw,sizeof(raw));
    r10_voltage_io io={.context=f,.initialize=initialize,.start=start,.poll=read_value,.cancel=cancel};
    r10_voltage_begin(v,&io,now);
}
static void complete(r10_voltage *v,uint32_t *now) {
    uint32_t before=v->samples;
    for (unsigned i=0;i<30u && v->samples==before;++i) r10_voltage_poll(v,(*now)++);
    assert(v->samples==before+1u);assert(v->valid);assert(v->has_sample);
    assert(v->raw_mask==R10_VOLTAGE_ALL);assert(v->state==R10_VOLTAGE_WAIT);
}
static void until_failure(r10_voltage *v,uint32_t *now) {
    for (unsigned i=0;i<600u && !v->error;++i) r10_voltage_poll(v,(*now)++);
    assert(v->error);assert(!v->valid);
}
int main(void) {
    r10_voltage v;fixture f;uint32_t now=0u;
    setup(&v,&f,now);complete(&v,&now);
    assert(f.init_calls==1u && f.starts==5u && f.reads==5u && !f.active);
    assert(!f.cancels);assert(r10_voltage_fresh(&v,v.last_good_ms));
    assert(r10_voltage_fresh(&v,v.last_good_ms+999u));
    assert(!r10_voltage_fresh(&v,v.last_good_ms+1000u));
    for (unsigned i=1u;i<5u;++i) assert((uint32_t)(v.sample_ms[i]-v.sample_ms[i-1])==3u);

    /* A failed later batch preserves the last complete sample, without calling
     * its values current. A reset/retry cannot silently mix the two batches. */
    r10_voltage_values old=v.values;uint32_t old_raw[5];memcpy(old_raw,v.sample_raw,sizeof(old_raw));
    uint32_t last=v.last_good_ms;
    now=last+R10_VOLTAGE_PERIOD_MS;f.raw[2]=1024u;
    until_failure(&v,&now);
    assert(v.error==R10_VOLTAGE_RAW_RANGE && v.last_error==v.error);
    assert(v.raw_mask==7u && v.raw[2]==1024u && v.raw_ms[2]);
    assert(v.samples==1u && v.last_good_ms==last && v.has_sample);
    assert(!memcmp(&v.values,&old,sizeof(old)) && !memcmp(v.sample_raw,old_raw,sizeof(old_raw)));
    assert(!r10_voltage_fresh(&v,now));assert(f.cancels==1u && !f.active);
    f.raw[2]=150u;now=v.stage_at+R10_VOLTAGE_RETRY_MS;
    r10_voltage_poll(&v,now++);assert(!v.valid);complete(&v,&now);
    assert(v.retries==1u && v.samples==2u && v.last_error==R10_VOLTAGE_RAW_RANGE);
    assert(v.sample_raw[2]==150u && v.last_good_ms!=last);

    /* Init/read deadline is checked before accepting a late ready/result. */
    setup(&v,&f,0u);f.init_rc=R10_VOLTAGE_IO_BUSY;
    r10_voltage_poll(&v,499u);assert(!v.error && f.init_calls==1u);
    f.init_rc=R10_VOLTAGE_IO_OK;r10_voltage_poll(&v,500u);
    assert(v.error==R10_VOLTAGE_TIMEOUT && f.init_calls==1u && !v.samples);
    setup(&v,&f,0u);r10_voltage_poll(&v,0u);r10_voltage_poll(&v,1u);
    f.read_rc=R10_VOLTAGE_IO_BUSY;r10_voltage_poll(&v,20u);assert(!v.error && f.reads==1u);
    f.read_rc=R10_VOLTAGE_IO_OK;r10_voltage_poll(&v,21u);
    assert(v.error==R10_VOLTAGE_TIMEOUT && f.reads==1u && !v.raw_mask);

    /* Repeated short waits must not evade the batch-age bound. */
    setup(&v,&f,0u);r10_voltage_poll(&v,0u);
    for (unsigned i=0;i<4u;++i) {
        r10_voltage_poll(&v,1u+i*22u);r10_voltage_poll(&v,18u+i*22u);r10_voltage_poll(&v,19u+i*22u);
    }
    assert(v.raw_mask==15u);r10_voltage_poll(&v,99u);r10_voltage_poll(&v,100u);
    assert(v.error==R10_VOLTAGE_TIMEOUT && v.raw_mask==15u && !v.has_sample);

    /* The final read may itself take too long. Keep its raw evidence, but no
     * last-good result can commit using the callback's earlier entry time. */
    setup(&v,&f,0u);now=0u;f.clock=&now;
    for (unsigned i=0;i<40u && !(v.state==R10_VOLTAGE_READING && v.slot==4u);++i)
        r10_voltage_poll(&v,now++);
    assert(v.slot==4u && v.state==R10_VOLTAGE_READING);f.read_cost=100u;
    r10_voltage_poll(&v,now++);assert(v.state==R10_VOLTAGE_CONFIRM && !v.has_sample);
    r10_voltage_poll(&v,now++);assert(v.error==R10_VOLTAGE_TIMEOUT && v.raw_mask==31u && !v.samples);
    setup(&v,&f,0u);now=0u;f.clock=&now;
    r10_voltage_poll(&v,now++);r10_voltage_poll(&v,now++);f.read_cost=21u;
    r10_voltage_poll(&v,now++);assert(v.state==R10_VOLTAGE_CONFIRM && !v.has_sample);
    r10_voltage_poll(&v,now++);assert(v.error==R10_VOLTAGE_TIMEOUT && v.raw_mask==1u && !v.samples);

    setup(&v,&f,0u);f.read_rc=R10_VOLTAGE_IO_ERROR;f.cancel_rc=R10_VOLTAGE_IO_ERROR;f.detail=0xbadu;
    now=0u;until_failure(&v,&now);
    assert(v.state==R10_VOLTAGE_STOPPED && v.error==R10_VOLTAGE_READ_ERROR);
    assert(v.detail==0xbadu && v.last_error_detail==0xbadu &&
           v.cleanup_error==R10_VOLTAGE_CLEANUP && v.cleanup_detail==0xbadu && f.cancels==1u);
    unsigned calls=f.init_calls+f.starts+f.reads+f.cancels;
    for (unsigned i=0;i<10000u;++i) r10_voltage_poll(&v,i);
    assert(f.init_calls+f.starts+f.reads+f.cancels==calls);

    setup(&v,&f,100u);r10_voltage_poll(&v,99u);
    assert(v.error==R10_VOLTAGE_TIMEBASE && v.state==R10_VOLTAGE_STOPPED && !f.init_calls && f.cancels==1u);
    now=0xfffffff8u;setup(&v,&f,now);complete(&v,&now);
    assert(v.last_good_ms<20u);assert(r10_voltage_fresh(&v,now));

    for (unsigned slot=0;slot<5u;++slot) {
        now=0u;setup(&v,&f,now);f.raw[slot]=1023u;until_failure(&v,&now);
        assert(v.error==R10_VOLTAGE_SATURATED && !v.has_sample && v.raw_mask==31u);
    }
    for (unsigned i=0;i<3u;++i) {
        now=0u;setup(&v,&f,now);
        if (i==0u) f.init_rc=2;else if (i==1u) f.start_rc=R10_VOLTAGE_IO_BUSY;else f.read_rc=2;
        until_failure(&v,&now);
        assert(v.error==(i==0u?R10_VOLTAGE_INIT:i==1u?R10_VOLTAGE_START_ERROR:R10_VOLTAGE_READ_ERROR));
        assert(f.cancels==1u && !v.has_sample);
    }
    setup(&v,&f,0u);f.config.revision=0x2008u;now=0u;until_failure(&v,&now);
    assert(v.error==R10_VOLTAGE_CONFIG && !f.starts);
    setup(&v,&f,0u);f.config.calibration=0xffffu;now=0u;until_failure(&v,&now);
    assert(v.error==R10_VOLTAGE_CALIBRATION && !f.starts);
    setup(&v,&f,0u);f.raw[4]=400u;now=0u;until_failure(&v,&now);
    assert(v.error==R10_VOLTAGE_REFERENCE_DRIFT && !v.has_sample && v.raw_mask==31u);
    setup(&v,&f,0u);f.raw[1]=f.raw[2]=0u;now=0u;complete(&v,&now);
    assert(v.values.logic_mv==0u && v.values.camera_mv==0u && v.valid);

    r10_voltage_io bad={0};r10_voltage_begin(&v,&bad,0u);
    assert(v.state==R10_VOLTAGE_STOPPED && v.error==R10_VOLTAGE_ADAPTER);
    r10_voltage_poll(&v,1000u);assert(!v.has_sample);
    r10_voltage_begin(0,0,0u);r10_voltage_poll(0,0u);assert(!r10_voltage_fresh(0,0u));
    puts("scripted voltage acquisition, timing and recovery cases passed");
    return 0;
}
