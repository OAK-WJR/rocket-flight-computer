#include "voltage_core.h"
#include <string.h>

static unsigned configuration(const r10_voltage_config *c) {
    if (!c || c->sample_bits!=R10_VOLTAGE_BITS || !c->adc12_hz ||
        c->adc12_hz>4000000u || !c->adc3_hz || c->adc3_hz>4000000u)
        return R10_VOLTAGE_CONFIG;
    /* Explicit allowlist; a numerically higher revision is not evidence that
     * its ADC implementation is compatible. ES0392 Rev16 Table2. */
    if (c->revision!=0x1003u && c->revision!=0x2001u &&
        c->revision!=0x2003u && c->revision!=0x2007u)
        return R10_VOLTAGE_CONFIG;
    /* Wide corruption screen around the factory 16-bit calibration, not a
     * claimed factory acceptance band or an accuracy qualification. */
    if (c->calibration<20000u || c->calibration>30000u)
        return R10_VOLTAGE_CALIBRATION;
    return R10_VOLTAGE_OK;
}

static uint32_t rounded(uint64_t numerator, uint64_t denominator) {
    return (uint32_t)((numerator+denominator/2u)/denominator);
}

unsigned r10_voltage_compute(const r10_voltage_config *c,
                            const uint32_t raw[R10_VOLTAGE_CHANNELS],
                            r10_voltage_values *out) {
    if (!out) return R10_VOLTAGE_ADAPTER;
    memset(out,0,sizeof(*out));
    unsigned error=configuration(c);
    if (error) return error;
    if (!raw) return R10_VOLTAGE_ADAPTER;
    for (unsigned i=0;i<R10_VOLTAGE_CHANNELS;++i) {
        if (raw[i]>R10_VOLTAGE_MAX) return R10_VOLTAGE_RAW_RANGE;
        if (raw[i]==R10_VOLTAGE_MAX) return R10_VOLTAGE_SATURATED;
    }
    uint32_t a=raw[R10_VOLTAGE_REF_BEFORE], b=raw[R10_VOLTAGE_REF_AFTER];
    if (!a || !b) return R10_VOLTAGE_REFERENCE;
    uint32_t low=a<b?a:b, delta=a>b?a-b:b-a;
    /* A bracketing-reference check rejects a changing reference. This 2% line
     * is a diagnostic policy, not the ADC's specified measurement accuracy. */
    if (delta*100u>low*2u) return R10_VOLTAGE_REFERENCE_DRIFT;
    uint64_t denominator=65535ull*(a+b);
    uint64_t numerator=3300ull*c->calibration*R10_VOLTAGE_MAX*2u;
    uint32_t vdda=rounded(numerator,denominator);
    if (vdda<1800u || vdda>3600u) return R10_VOLTAGE_REFERENCE;
    /* Derive each result from the same unrounded rational reference; rounding
     * VDDA first would add a second avoidable error to the divided inputs. */
    r10_voltage_values values={0};
    values.vdda_mv=vdda;
    values.logic_mv=rounded(3300ull*c->calibration*2u*raw[R10_VOLTAGE_LOGIC]*11u,denominator);
    values.camera_mv=rounded(3300ull*c->calibration*2u*raw[R10_VOLTAGE_CAMERA]*11u,denominator);
    values.v3v3_coarse_mv=rounded(3300ull*c->calibration*2u*raw[R10_VOLTAGE_VBAT]*4u,denominator);
    values.reference_drift_permille=rounded(1000ull*delta,low);
    *out=values;
    return R10_VOLTAGE_OK;
}

static void failed(r10_voltage *v, unsigned error, uint32_t now) {
    v->error=error;v->last_error=error;v->last_error_detail=v->detail;
    v->valid=0u;++v->failures;
    v->stage_at=now;
    uint32_t detail=0u;
    if (v->io.cancel(v->io.context,&detail)!=R10_VOLTAGE_IO_OK) {
        v->cleanup_error=R10_VOLTAGE_CLEANUP;
        v->cleanup_detail=detail;
        v->state=R10_VOLTAGE_STOPPED;
        /* Keep the original error and its detail; cleanup is a separate cause. */
    } else {
        v->cleanup_error=R10_VOLTAGE_OK;
        v->cleanup_detail=0u;
        v->state=error==R10_VOLTAGE_TIMEBASE?R10_VOLTAGE_STOPPED:R10_VOLTAGE_RETRY;
    }
}

static void batch(r10_voltage *v, uint32_t now) {
    v->batch_at=now;v->stage_at=now;v->slot=0u;v->raw_mask=0u;
    memset(v->raw,0,sizeof(v->raw));memset(v->raw_ms,0,sizeof(v->raw_ms));
    v->state=R10_VOLTAGE_START;
}

void r10_voltage_begin(r10_voltage *v, const r10_voltage_io *io, uint32_t now) {
    if (!v) return;
    memset(v,0,sizeof(*v));v->observed_ms=now;v->stage_at=now;
    if (!io || !io->initialize || !io->start || !io->poll || !io->cancel) {
        v->state=R10_VOLTAGE_STOPPED;v->error=R10_VOLTAGE_ADAPTER;
        v->last_error=v->error;return;
    }
    v->io=*io;v->state=R10_VOLTAGE_INITIALIZING;
}

void r10_voltage_poll(r10_voltage *v, uint32_t now) {
    if (!v || v->state==R10_VOLTAGE_OFF || v->state==R10_VOLTAGE_STOPPED) return;
    if ((uint32_t)(now-v->observed_ms)>=0x80000000u) {
        failed(v,R10_VOLTAGE_TIMEBASE,now);return;
    }
    v->observed_ms=now;
    switch (v->state) {
    case R10_VOLTAGE_RETRY:
        if ((uint32_t)(now-v->stage_at)>=R10_VOLTAGE_RETRY_MS) {
            ++v->retries;v->stage_at=now;v->state=R10_VOLTAGE_INITIALIZING;
            memset(&v->config,0,sizeof(v->config));
        }
        return;
    case R10_VOLTAGE_INITIALIZING: {
        if ((uint32_t)(now-v->stage_at)>=R10_VOLTAGE_INIT_MS) {
            failed(v,R10_VOLTAGE_TIMEOUT,now);return;
        }
        v->detail=0u;
        int rc=v->io.initialize(v->io.context,now,&v->config,&v->detail);
        if (rc==R10_VOLTAGE_IO_BUSY) return;
        unsigned error=rc==R10_VOLTAGE_IO_OK?configuration(&v->config):R10_VOLTAGE_INIT;
        if (error) {failed(v,error,now);return;}
        v->error=R10_VOLTAGE_OK;batch(v,now);return;
    }
    case R10_VOLTAGE_WAIT:
        if ((uint32_t)(now-v->last_good_ms)>=R10_VOLTAGE_PERIOD_MS) batch(v,now);
        return;
    case R10_VOLTAGE_START:
    case R10_VOLTAGE_READING:
    case R10_VOLTAGE_CONFIRM:
        if ((uint32_t)(now-v->batch_at)>=R10_VOLTAGE_BATCH_MS) {
            failed(v,R10_VOLTAGE_TIMEOUT,now);return;
        }
        break;
    default:
        failed(v,R10_VOLTAGE_ADAPTER,now);return;
    }
    if (v->state==R10_VOLTAGE_START) {
        v->detail=0u;
        if (v->io.start(v->io.context,v->slot,&v->detail)!=R10_VOLTAGE_IO_OK) {
            failed(v,R10_VOLTAGE_START_ERROR,now);return;
        }
        v->stage_at=now;v->state=R10_VOLTAGE_READING;return;
    }
    if ((uint32_t)(now-v->stage_at)>=R10_VOLTAGE_CONVERSION_MS) {
        failed(v,R10_VOLTAGE_TIMEOUT,now);return;
    }
    if (v->state==R10_VOLTAGE_READING) {
        uint32_t raw=0u;
        v->detail=0u;
        int rc=v->io.poll(v->io.context,&raw,&v->detail);
        if (rc==R10_VOLTAGE_IO_BUSY) return;
        if (rc!=R10_VOLTAGE_IO_OK) {failed(v,R10_VOLTAGE_READ_ERROR,now);return;}
        v->raw[v->slot]=raw;v->raw_ms[v->slot]=now;v->raw_mask|=1u<<v->slot;
        if (raw>R10_VOLTAGE_MAX) {failed(v,R10_VOLTAGE_RAW_RANGE,now);return;}
        /* Re-observe time on the next call before accepting this conversion.
         * A slow adapter callback cannot hide inside its entry timestamp. */
        v->state=R10_VOLTAGE_CONFIRM;return;
    }
    if (++v->slot<R10_VOLTAGE_CHANNELS) {v->state=R10_VOLTAGE_START;return;}
    r10_voltage_values values;
    unsigned error=r10_voltage_compute(&v->config,v->raw,&values);
    if (error) {failed(v,error,now);return;}
    memcpy(v->sample_raw,v->raw,sizeof(v->raw));
    memcpy(v->sample_ms,v->raw_ms,sizeof(v->raw_ms));
    v->sample_config=v->config;v->values=values;
    v->last_good_ms=v->raw_ms[R10_VOLTAGE_REF_AFTER];
    ++v->samples;v->has_sample=1u;v->valid=1u;
    v->error=R10_VOLTAGE_OK;v->state=R10_VOLTAGE_WAIT;
}

int r10_voltage_fresh(const r10_voltage *v, uint32_t now) {
    return v && v->has_sample && v->valid && !v->error &&
           v->state!=R10_VOLTAGE_OFF && v->state!=R10_VOLTAGE_STOPPED &&
           (uint32_t)(now-v->last_good_ms)<R10_VOLTAGE_FRESH_MS;
}
