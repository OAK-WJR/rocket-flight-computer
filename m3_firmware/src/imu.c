#include "imu.h"
#include <string.h>

/* DS-000577 rev1.0, pp58,66-80,109-110; TDK pinned reference for reset/pulls.
 * Full-scale fields retain reset values: +/-32g and +/-4000deg/s. Only ODR
 * changes to 50Hz. The caller observes <=1/s, not all sensor output samples.
 */
enum { PWR=0x10, INT_CFG0=0x16, INT_CFG1=0x17, INT_CFG2=0x18,
       INT_STATUS=0x19, ACC_CFG=0x1b, GYR_CFG=0x1c, INTF=0x2d,
       DRIVE=0x32, WHO=0x72, IADDR=0x7c, IDATA=0x7e, MISC=0x7f };
#define SREG 0xa267U
#define DRDY 4U

static int failure(BenchIMU *r, int e) { if (!r->error) r->error=(uint32_t)e; return 0; }
static int transfer(ImuDevice *s, BenchIMU *r, uint8_t reg, uint8_t *data, size_t n, int read) {
    uint8_t tx[15]={0}, rx[15]={0};
    if (!n || n>14) return failure(r,IMU_TRANSFER);
    tx[0]=reg | (read ? 0x80U : 0U);
    if (!read) memcpy(tx+1,data,n);
    int e=s->io->transfer(s->io->ctx,tx,rx,n+1,&r->io_error);
    if (read) memcpy(data,rx+1,n); /* preserve, but never validate a partial transfer */
    return e ? failure(r,IMU_TRANSFER) : 1;
}
static int read8(ImuDevice *s, BenchIMU *r, uint8_t reg, uint8_t *v) {
    return transfer(s,r,reg,v,1,1);
}
static int write8(ImuDevice *s, BenchIMU *r, uint8_t reg, uint8_t v) {
    return transfer(s,r,reg,&v,1,0);
}
static int delay(ImuDevice *s, BenchIMU *r, uint32_t ms) {
    uint32_t t=s->io->now(s->io->ctx);
    s->io->delay_ms(s->io->ctx,ms);
    return (uint32_t)(s->io->now(s->io->ctx)-t)>=ms || failure(r,IMU_TICK_STALLED);
}
static int iready(ImuDevice *s, BenchIMU *r) {
    for (unsigned i=0;i<10;++i) {
        uint8_t v=0;
        if (!read8(s,r,MISC,&v)) return 0;
        if (v&1U) return 1;
        if (!delay(s,r,1)) return 0;
    }
    return failure(r,IMU_IREG_TIMEOUT);
}
static int iread(ImuDevice *s, BenchIMU *r, uint16_t reg, uint8_t *v) {
    uint8_t a[2]={(uint8_t)(reg>>8),(uint8_t)reg};
    /* Read of IDATA also prefetches the next address; wait again afterward. */
    return iready(s,r) && transfer(s,r,IADDR,a,2,0) && delay(s,r,1) &&
           iready(s,r) && read8(s,r,IDATA,v) && delay(s,r,1) && iready(s,r);
}
static int iwrite(ImuDevice *s, BenchIMU *r, uint16_t reg, uint8_t v) {
    uint8_t a[3]={(uint8_t)(reg>>8),(uint8_t)reg,v};
    /* Address AND data in one burst: separate writes cause read-prefetch. */
    return iready(s,r) && transfer(s,r,IADDR,a,3,0) && delay(s,r,1) && iready(s,r);
}
static int update(ImuDevice *s, BenchIMU *r, uint16_t reg, uint8_t clear, uint8_t set) {
    uint8_t old=0, got=0;
    if (!iread(s,r,reg,&old)) return 0;
    uint8_t want=(old & (uint8_t)~clear) | set;
    return iwrite(s,r,reg,want) && iread(s,r,reg,&got) &&
           (got==want || failure(r,IMU_CONFIG));
}
static int configuration(ImuDevice *s, BenchIMU *r) {
    uint8_t id=0, a[2]={0}, p=0, endian=0, ic[3]={0};
    if (!read8(s,r,WHO,&id)) return 0;
    r->evidence=(r->evidence & 0x00ffffffU) | ((uint32_t)id<<24);
    if (id!=0xe9U) return failure(r,IMU_IDENTITY);
    if (!transfer(s,r,ACC_CFG,a,2,1) || !read8(s,r,PWR,&p) ||
        !iread(s,r,SREG,&endian) || !transfer(s,r,INT_CFG0,ic,3,1)) return 0;
    r->config=a[0] | ((uint32_t)a[1]<<8) | ((uint32_t)p<<16) | ((uint32_t)endian<<24);
    if (a[0]!=0x0a || a[1]!=0x0a || p!=0x0f || !(endian&2U) ||
        ic[0]!=4 || ic[1]!=0 || ic[2]!=1) return failure(r,IMU_CONFIG);
    r->evidence|=IMU_CONFIG_VERIFIED;
    return 1;
}
static void finish(ImuDevice *s, BenchIMU *r) {
    if (r->error) s->history|=1U<<r->error;
    r->history=s->history;
    r->finished_ms=s->io->now(s->io->ctx);
    r->status=r->error ? 3U : 2U;
}
void imu_begin(ImuDevice *s, const ImuIO *io, BenchIMU *r) {
    memset(s,0,sizeof(*s)); memset(r,0,sizeof(*r)); s->io=io;
    r->started_ms=io->now(io->ctx); r->status=1;
    int e=io->initialize(io->ctx,&s->bus_hz,&r->io_error);
    r->bus_hz=s->bus_hz;
    uint8_t id=0, intf=0, drive=0, v=0;
    if (e) { failure(r,e==IMU_CLOCK ? IMU_CLOCK : IMU_SPI_INIT); goto done; }
    if (s->bus_hz!=1000000U) { failure(r,IMU_CLOCK); goto done; }
    if (!read8(s,r,WHO,&id)) goto done;
    r->evidence=(uint32_t)id<<24;
    if (id!=0xe9) { failure(r,IMU_IDENTITY); goto done; }
    if (!read8(s,r,INTF,&intf) || !read8(s,r,DRIVE,&drive) ||
        !write8(s,r,MISC,2) || !delay(s,r,2)) goto done;
    if (!write8(s,r,DRIVE,drive) || !write8(s,r,INTF,intf) || !read8(s,r,MISC,&v)) goto done;
    if (v&2U) { failure(r,IMU_RESET); goto done; }
    if (!read8(s,r,INT_STATUS,&v)) goto done;
    if (!(v&0x80U)) { failure(r,IMU_RESET); goto done; }
    /* Disable interrupts before changing their drive/mode/polarity. */
    if (!write8(s,r,INT_CFG0,0) || !write8(s,r,INT_CFG1,0) || !write8(s,r,INT_CFG2,1)) goto done;
    if (!update(s,r,SREG,0,2)) goto done;
    /* Preserve all other fields, disable pulls on active/grounded pins.
     * INT2/pin9 remains unconnected: preserve its default internal pull. */
    const uint8_t masks[]={0x48,0x92,0x24,0x49};
    for (unsigned i=0;i<4;++i) if (!update(s,r,(uint16_t)(0xa03aU+i),masks[i],0)) goto done;
    if (!iread(s,r,0xa03e,&v)) goto done;
    if (!(v&2U)) { failure(r,IMU_CONFIG); goto done; }
    if (!write8(s,r,ACC_CFG,0x0a) || !write8(s,r,GYR_CFG,0x0a) ||
        !write8(s,r,INT_CFG0,DRDY) || !write8(s,r,PWR,0x0f) || !delay(s,r,100)) goto done;
    /* 100ms is a conservative bench settling choice, not a guaranteed maximum. */
    if (!configuration(s,r)) goto done;
    s->initialized=1; r->evidence|=IMU_INITIALIZED;
done:
    s->init_error=r->error; s->init_detail=r->io_error; r->init_error=r->error;
    finish(s,r);
}
void imu_sample(ImuDevice *s, BenchIMU *r) {
    memset(r,0,sizeof(*r)); r->status=1; r->bus_hz=s->bus_hz;
    r->started_ms=s->io->now(s->io->ctx); r->init_error=s->init_error;
    uint8_t status=0;
    if (s->init_error || !s->initialized) {
        r->io_error=s->init_detail; failure(r,s->init_error ? (int)s->init_error : IMU_SPI_INIT); goto done;
    }
    r->evidence|=IMU_INITIALIZED;
    if (!configuration(s,r)) goto done; /* detect sensor reset/config drift each observation */
    if (!read8(s,r,INT_STATUS,&status)) goto done; /* discard pre-existing DRDY */
    r->evidence|=status;
    if (status&0x80U) { failure(r,IMU_RESET); goto done; }
    unsigned i;
    for (i=0;i<100;++i) {
        if (!delay(s,r,1) || !read8(s,r,INT_STATUS,&status)) goto done;
        r->evidence=(r->evidence & ~0xffU) | status;
        if (status&0x80U) { failure(r,IMU_RESET); goto done; }
        if (status&DRDY) break;
    }
    if (i==100) { failure(r,IMU_READY_TIMEOUT); goto done; }
    r->started_ms=s->io->now(s->io->ctx); /* start of the raw burst, not device sample time */
    if (!transfer(s,r,0,(uint8_t *)r->raw,14,1)) goto done;
    r->sampled_ms=s->io->now(s->io->ctx); r->evidence|=IMU_RAW_COMPLETE;
    if (!read8(s,r,INT_STATUS,&status)) goto done;
    r->evidence|=(uint32_t)status<<8;
    if (status&0x80U) { failure(r,IMU_RESET); goto done; }
    if (status&DRDY) { failure(r,IMU_UPDATE_DURING_READ); goto done; }
    if ((uint32_t)(s->io->now(s->io->ctx)-r->started_ms)>5U) failure(r,IMU_READ_TOO_SLOW);
done:
    finish(s,r);
}
