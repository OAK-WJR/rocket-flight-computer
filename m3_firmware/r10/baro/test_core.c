/* Sensor command/PROM/conversion model, not pressure physics or real I2C. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "baro_core.h"
#include "checks.h"
typedef struct {
    uint32_t now,ready_at,latency,calls,fail_call,resets,starts,initializes;
    uint32_t d1,d2,hz;
    uint16_t prom[8];
    uint8_t command,conversion;
    int absent;
} model;
static int initialize(void *ctx,uint32_t *hz,uint32_t *detail) {
    model *m=ctx;m->initializes++;*hz=m->hz;*detail=0;
    if(m->absent){*detail=42;return -1;}
    return 0;
}
static int transfer(void *ctx,uint8_t addr,const uint8_t *tx,size_t nt,uint8_t *rx,size_t nr,uint32_t *detail) {
    model *m=ctx;assert(addr==0x77 && m->calls<10000);m->calls++;m->now+=m->latency;
    if(m->calls==m->fail_call){*detail=0x1234;return -1;}
    assert((nt==1 && nr==0 && tx) || (nt==0 && (nr==2 || nr==3) && rx));
    if(nt) {
        m->command=tx[0];
        if(tx[0]==0x1e){m->resets++;m->conversion=0;m->ready_at=m->now+3;}
        else if(tx[0]==0x48 || tx[0]==0x58) {
            assert(m->conversion==0);m->starts++;m->conversion=tx[0];m->ready_at=m->now+10;
        } else if(tx[0]>=0xa0 && tx[0]<=0xae)assert((uint32_t)(m->now-m->ready_at)<0x80000000u);
        else assert(tx[0]==0);
    } else if(nr==2) {
        assert(m->command>=0xa0 && m->command<=0xae && !(m->command&1));
        uint16_t value=m->prom[(m->command-0xa0)/2];rx[0]=value>>8;rx[1]=(uint8_t)value;
    } else {
        assert(m->command==0 && m->conversion && (uint32_t)(m->now-m->ready_at)<0x80000000u);
        uint32_t value=m->conversion==0x48?m->d1:m->d2;
        rx[0]=value>>16;rx[1]=value>>8;rx[2]=(uint8_t)value;m->conversion=0;
    }
    return 0;
}
static r10_baro_io io(model *m) {return (r10_baro_io){m,initialize,transfer};}
static model good(void) {
    model m={.d1=9085466,.d2=8569150,.hz=50000};
    const uint16_t c[8]={0,40127,36924,23317,23282,33464,28312,0};
    for(unsigned i=0;i<8;++i)m.prom[i]=c[i];
    m.prom[7]=bench_prom_crc4(m.prom);return m;
}
static void poll(r10_baro *d,model *m) {m->now++;r10_baro_poll(d,m->now);}
static void outcome(r10_baro *d,model *m) {
    for(unsigned i=0;i<500 && d->state!=R10_BARO_READY && d->state!=R10_BARO_ERROR;++i)poll(d,m);
    assert(d->state==R10_BARO_READY || d->state==R10_BARO_ERROR);
}
static void begin(r10_baro *d,model *m) {r10_baro_io port=io(m);r10_baro_begin(d,&port,m->now);}
int main(void) {
    const uint16_t published_crc[]={0x3132,0x3334,0x3536,0x3738,0x3940,0x4142,0x4344,0x4500};
    assert(bench_prom_crc4(published_crc)==11);
    model m=good();r10_baro d;begin(&d,&m);outcome(&d,&m);
    assert(d.state==R10_BARO_READY && d.prom_valid && d.prom_mask==255 && d.samples==1 && d.has_sample);
    assert(d.pressure_pa==100009 && d.temp_centic==2007 && d.valid_mask==3);
    assert(d.sample_d1==9085466 && d.sample_d2==8569150 && m.starts==2 && m.resets==1);
    assert((uint32_t)(d.sample_d2_ms-d.sample_d1_ms)>=12);
    uint32_t startup_calls=m.calls;
    /* Callback latency must not shorten any post-command wait. */
    m=good();m.latency=20;begin(&d,&m);outcome(&d,&m);assert(d.state==R10_BARO_READY);
    /* Every message in initial acquisition fails closed, with no follow-on IO. */
    for(uint32_t fail=1;fail<=startup_calls;++fail) {
        m=good();m.fail_call=fail;begin(&d,&m);outcome(&d,&m);
        assert(d.state==R10_BARO_ERROR && !d.valid_mask && !d.has_sample && d.samples==0);
        assert(d.bus_errors==1 && d.bus_detail==0x1234 && m.calls==fail);
        uint32_t calls=m.calls;for(unsigned i=0;i<20;++i)poll(&d,&m);assert(m.calls==calls);
    }
    m=good();m.absent=1;begin(&d,&m);assert(d.state==R10_BARO_ERROR && d.error==R10_BARO_PORT && !m.calls);
    m.absent=0;m.now+=999;r10_baro_poll(&d,m.now);assert(m.initializes==1);
    m.now++;r10_baro_poll(&d,m.now);outcome(&d,&m);assert(d.state==R10_BARO_READY && d.retry_count==1);
    for(unsigned zero=0;zero<2;++zero) {
        m=good();for(unsigned i=0;i<8;++i)m.prom[i]=zero?0xffff:0;
        begin(&d,&m);outcome(&d,&m);assert(d.error==R10_BARO_PROM_EMPTY && d.prom_mask==255);
    }
    m=good();m.prom[3]^=1;begin(&d,&m);outcome(&d,&m);
    assert(d.error==R10_BARO_PROM_CRC && d.crc_calculated!=d.crc_stored && !d.prom_valid);
    for(unsigned which=0;which<4;++which) {
        m=good();if(which<2)m.d1=which?0xffffffu:0;else m.d2=which==2?0:0xffffffu;
        begin(&d,&m);outcome(&d,&m);assert(d.error==R10_BARO_ADC_INVALID && !d.has_sample);
    }
    m=good();m.d2=100;begin(&d,&m);outcome(&d,&m);
    assert(d.error==R10_BARO_RESULT_RANGE && d.candidate_temp_centic<-4000);
    /* No partial pair may replace last-good values/calibration. */
    m=good();begin(&d,&m);outcome(&d,&m);uint16_t saved_prom[8];memcpy(saved_prom,d.sample_prom,sizeof saved_prom);
    uint32_t saved_d1=d.sample_d1;m.d1+=5000;
    poll(&d,&m);while(d.state!=R10_BARO_WAIT_D2)poll(&d,&m);
    m.fail_call=m.calls+1;outcome(&d,&m);
    assert(d.error==R10_BARO_READ_D2 && d.samples==1 && d.sample_d1==saved_d1 && !d.valid_mask);
    assert(d.d1!=saved_d1 && !memcmp(saved_prom,d.sample_prom,sizeof saved_prom));
    m.prom[2]^=1;m.fail_call=0;m.conversion=0;m.now+=1000;r10_baro_poll(&d,m.now);outcome(&d,&m);
    assert(d.error==R10_BARO_PROM_CRC && d.has_sample && d.samples==1);
    assert(!memcmp(saved_prom,d.sample_prom,sizeof saved_prom));
    /* Staleness clears validity even while the next pair is in progress. */
    m=good();begin(&d,&m);outcome(&d,&m);poll(&d,&m);poll(&d,&m);
    m.now+=300;r10_baro_poll(&d,m.now);assert(d.has_sample && !d.valid_mask && d.samples==1);
    assert(d.error==R10_BARO_PAIR_STALE);
    /* Late D2 completion must not refresh an already old D1 conversion. */
    m=good();begin(&d,&m);outcome(&d,&m);uint32_t previous=d.last_good_ms;
    poll(&d,&m);while(d.state!=R10_BARO_WAIT_D2)poll(&d,&m);poll(&d,&m);
    uint32_t before=m.calls;m.now+=300;r10_baro_poll(&d,m.now);
    assert(d.state==R10_BARO_ERROR && d.error==R10_BARO_PAIR_STALE && !d.valid_mask);
    assert(d.samples==1 && d.last_good_ms==previous && m.calls==before);
    /* A read callback that crosses the deadline cannot replace retained data. */
    m=good();begin(&d,&m);outcome(&d,&m);previous=d.last_good_ms;
    poll(&d,&m);while(d.state!=R10_BARO_WAIT_D2)poll(&d,&m);poll(&d,&m);
    m.now=d.acquisition_started_ms+249u;m.latency=1;r10_baro_poll(&d,m.now);
    assert(d.state==R10_BARO_COMMIT && d.samples==1 && d.last_good_ms==previous);
    poll(&d,&m);
    assert(d.state==R10_BARO_ERROR && d.error==R10_BARO_PAIR_STALE && d.samples==1 && !d.valid_mask);
    m=good();begin(&d,&m);outcome(&d,&m);
    poll(&d,&m);while(d.state!=R10_BARO_WAIT_D2)poll(&d,&m);poll(&d,&m);
    m.now=d.acquisition_started_ms+249u;r10_baro_poll(&d,m.now);assert(d.state==R10_BARO_COMMIT);
    poll(&d,&m);assert(d.state==R10_BARO_READY && d.samples==2 && d.valid_mask==3);
    assert((uint32_t)(m.now-d.sample_started_ms)==250u);
    /* Timer/sample wrap and a stale bus rate cannot impersonate no sample. */
    m=good();m.now=0xffffffd0u;begin(&d,&m);outcome(&d,&m);assert(d.state==R10_BARO_READY);
    d.samples=0xffffffffu;poll(&d,&m);outcome(&d,&m);assert(d.has_sample && d.samples==0 && d.valid_mask==3);
    m=good();m.hz=200000;begin(&d,&m);assert(d.error==R10_BARO_PORT && !m.calls);
    puts("scripted barometer core cases passed; no hardware tested");return 0;
}
