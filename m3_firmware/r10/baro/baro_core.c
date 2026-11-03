/* TE MS5611-01BA03 B3 (06/2017) pp7-13; AN520_004 p12.
 * Reuse the repository's reviewed pure CRC/compensation functions, never its
 * legacy board pin map. No altitude estimate, flight state or actuation here. */
#include "baro_core.h"
#include "checks.h"
static void fail(r10_baro *d,uint32_t error,uint32_t now) {
    d->state=R10_BARO_ERROR;d->error=d->last_error=error;d->valid_mask=0;d->stage_at=now;
}
static int transfer(r10_baro *d,const uint8_t *tx,size_t nt,uint8_t *rx,size_t nr) {
    if(d->bus_failed)return -1;
    uint32_t detail=0;
    if(d->io.transfer(d->io.handle,0x77u,tx,nt,rx,nr,&detail)!=0) {
        d->bus_errors++;d->bus_detail=detail;d->bus_failed=1;return -1;
    }
    return 0;
}
static int command(r10_baro *d,uint8_t cmd) {return transfer(d,&cmd,1,0,0);}
static int read_bytes(r10_baro *d,uint8_t cmd,uint8_t *dst,size_t count) {
    if(command(d,cmd)!=0)return -1;
    return transfer(d,0,0,dst,count);
}
static void start_wait(r10_baro *d,uint32_t state,uint32_t now) {
    d->state=state;d->stage_at=now;d->wait_pending=1;
}
static int waited(r10_baro *d,uint32_t now,uint32_t minimum) {
    /* Start the guard only on the first poll AFTER the command callback
     * returns. A slow transfer must not consume part of conversion/reload time. */
    if(d->wait_pending){d->stage_at=now;d->wait_pending=0;return 0;}
    return (uint32_t)(now-d->stage_at)>=minimum;
}
static void start_port(r10_baro *d,uint32_t now) {
    d->valid_mask=d->bus_failed=d->prom_mask=d->prom_index=d->prom_valid=0;
    d->crc_calculated=d->crc_stored=0;d->d1=d->d2=d->d1_ms=d->d2_ms=0;
    d->acquisition_started_ms=0;
    d->candidate_pressure_pa=d->candidate_temp_centic=0;
    for(unsigned i=0;i<8;++i)d->prom[i]=0;
    d->error=R10_BARO_OK;d->nominal_bus_hz=0;
    uint32_t detail=0;
    if(!d->io.initialize || !d->io.transfer ||
       d->io.initialize(d->io.handle,&d->nominal_bus_hz,&detail)!=0 ||
       !d->nominal_bus_hz || d->nominal_bus_hz>100000u) {
        d->bus_detail=detail;fail(d,R10_BARO_PORT,now);return;
    }
    start_wait(d,R10_BARO_POWER_WAIT,now);
}
void r10_baro_begin(r10_baro *d,const r10_baro_io *io,uint32_t now) {
    for(size_t i=0;i<sizeof(*d);++i)((uint8_t *)d)[i]=0;
    if(io)d->io=*io;
    start_port(d,now);
}
static uint32_t raw24(const uint8_t b[3]) {
    return (uint32_t)b[0]<<16|(uint32_t)b[1]<<8|b[2];
}
static int convert(r10_baro *d,uint32_t now) {
    d->acquisition_started_ms=now; /* conservative: before the command callback */
    if(command(d,0x48u)!=0){fail(d,R10_BARO_CONVERT_D1,now);return -1;}
    start_wait(d,R10_BARO_WAIT_D1,now);return 0;
}
void r10_baro_poll(r10_baro *d,uint32_t now) {
    if(d->has_sample && (uint32_t)(now-d->sample_started_ms)>R10_BARO_FRESH_MS)d->valid_mask=0;
    if(d->state==R10_BARO_OFF)return;
    if(d->state==R10_BARO_ERROR) {
        if((uint32_t)(now-d->stage_at)>=R10_BARO_RETRY_MS){d->retry_count++;start_port(d,now);}
        return;
    }
    if(d->state==R10_BARO_POWER_WAIT) {
        if(!waited(d,now,R10_BARO_POWER_MS))return;
        if(command(d,0x1eu)!=0){fail(d,R10_BARO_RESET,now);return;}
        start_wait(d,R10_BARO_RESET_WAIT,now);return;
    }
    if(d->state==R10_BARO_RESET_WAIT) {
        if(!waited(d,now,R10_BARO_RESET_MS))return;
        d->state=R10_BARO_PROM;return;
    }
    if(d->state==R10_BARO_PROM) {
        uint8_t b[2]={0};unsigned i=d->prom_index;
        if(read_bytes(d,(uint8_t)(0xa0u+2u*i),b,2)!=0){fail(d,R10_BARO_PROM_READ,now);return;}
        d->prom[i]=(uint16_t)b[0]<<8|b[1];d->prom_mask|=(uint8_t)(1u<<i);d->prom_index++;
        if(d->prom_index!=8)return;
        d->crc_calculated=bench_prom_crc4(d->prom);d->crc_stored=d->prom[7]&15u;
        if(!bench_prom_nonempty(d->prom)){fail(d,R10_BARO_PROM_EMPTY,now);return;}
        if(d->crc_calculated!=d->crc_stored){fail(d,R10_BARO_PROM_CRC,now);return;}
        d->prom_valid=1;(void)convert(d,now);return;
    }
    if(d->state==R10_BARO_READY){(void)convert(d,now);return;}
    if(d->state==R10_BARO_COMMIT) {
        /* Observe time on a subsequent poll, after both read callbacks and
         * compensation have returned. Callback latency cannot bypass age. */
        if((uint32_t)(now-d->acquisition_started_ms)>R10_BARO_FRESH_MS) {
            fail(d,R10_BARO_PAIR_STALE,now);return;
        }
        d->sample_d1=d->d1;d->sample_d2=d->d2;
        d->sample_d1_ms=d->d1_ms;d->sample_d2_ms=d->d2_ms;
        d->pressure_pa=d->candidate_pressure_pa;d->temp_centic=d->candidate_temp_centic;
        for(unsigned i=0;i<8;++i)d->sample_prom[i]=d->prom[i];
        d->samples++;d->has_sample=1;d->last_good_ms=now;d->valid_mask=3;
        d->sample_started_ms=d->acquisition_started_ms;
        d->state=R10_BARO_READY;d->error=R10_BARO_OK;return;
    }
    if(d->state==R10_BARO_WAIT_D1 || d->state==R10_BARO_WAIT_D2) {
        /* A delayed poll must never turn old conversions into fresh data.
         * Re-init after this error rather than overlap an uncertain conversion. */
        if((uint32_t)(now-d->acquisition_started_ms)>R10_BARO_FRESH_MS) {
            fail(d,R10_BARO_PAIR_STALE,now);return;
        }
        if(!waited(d,now,R10_BARO_CONVERT_MS))return;
        uint8_t b[3]={0};int first=d->state==R10_BARO_WAIT_D1;
        if(read_bytes(d,0,b,3)!=0){fail(d,first?R10_BARO_READ_D1:R10_BARO_READ_D2,now);return;}
        uint32_t value=raw24(b);
        if(first){d->d1=value;d->d1_ms=now;}else{d->d2=value;d->d2_ms=now;}
        if(!value || value==0xffffffu){fail(d,R10_BARO_ADC_INVALID,now);return;}
        if(first) {
            if(command(d,0x58u)!=0){fail(d,R10_BARO_CONVERT_D2,now);return;}
            start_wait(d,R10_BARO_WAIT_D2,now);return;
        }
        if(!bench_ms5611(d->prom,d->d1,d->d2,&d->candidate_pressure_pa,&d->candidate_temp_centic)) {
            fail(d,R10_BARO_RESULT_RANGE,now);return;
        }
        /* Keep candidates separate until a fresh post-callback timestamp. */
        d->state=R10_BARO_COMMIT;
    }
}
