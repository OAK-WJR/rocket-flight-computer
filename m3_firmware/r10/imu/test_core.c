/* Scripted sensor register model. Does not model sensor physics or SPI timing. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "imu_core.h"
typedef struct {
    uint8_t regs[128];
    unsigned calls,writes,inits;
    int fail_reg,fail_read,ignore_write,hold_reset,init_error;
    unsigned fail_call;
    uint32_t hz;
} model;
static void defaults(model *m) {
    memset(m->regs,0,sizeof m->regs);
    m->regs[0x0f]=0x73;m->regs[0x12]=0x04;m->regs[0x15]=0x08;
}
static void setup(model *m) {
    memset(m,0,sizeof(*m));defaults(m);
    m->fail_reg=-1;m->ignore_write=-1;m->hz=1000000;
}
static int initialize(void *p,uint32_t *hz,uint32_t *detail) {
    model *m=p;m->inits++;*hz=m->hz;*detail=m->init_error?0x11110000u:0;
    return m->init_error;
}
static int transfer(void *p,const uint8_t *tx,uint8_t *rx,size_t n,uint32_t *detail) {
    model *m=p;m->calls++;*detail=0;
    assert(n>=2 && n<=33);
    unsigned reg=tx[0]&0x7f,read=tx[0]>>7;
    if ((m->fail_call && m->calls==m->fail_call) || ((int)reg==m->fail_reg && (int)read==m->fail_read)) {
        *detail=0xaabbccdd;return 1;
    }
    memset(rx,0,n);
    if (read) {
        for (size_t i=1;i<n;++i) {
            assert(tx[i]==0); /* read dummy is deterministic */
            unsigned address=reg+((m->regs[0x12]&4)?(unsigned)(i-1):0);
            assert(address<128);rx[i]=m->regs[address];
        }
    } else {
        m->writes++;
        if ((int)reg==m->ignore_write)return 0;
        if (reg==1 && tx[1]&4) {defaults(m);m->regs[1]=m->hold_reset?4:0;return 0;}
        if ((reg==0x10 || reg==0x11) && tx[1]&15)assert(m->regs[0x13]&8);
        if (reg==0x4e && tx[1]&0x38)assert(m->regs[0x13]&8);
        for (size_t i=1;i<n;++i) {assert(reg+i-1<128);m->regs[reg+i-1]=tx[i];}
    }
    return 0;
}
static r10_imu_io io(model *m) {
    return (r10_imu_io){.handle=m,.initialize=initialize,.exchange=transfer};
}
static void configured(model *m,r10_imu *d,uint32_t start) {
    r10_imu_io bus=io(m);r10_imu_begin(d,&bus,start);
    assert(d->state==R10_IMU_BOOT_WAIT && m->calls==0);
    r10_imu_poll(d,start+34);assert(m->calls==0);
    r10_imu_poll(d,start+35);assert(d->state==R10_IMU_RESET_WAIT);
    unsigned n=m->calls;r10_imu_poll(d,start+69);assert(m->calls==n);
    r10_imu_poll(d,start+70);assert(d->state==R10_IMU_WAIT_DATA);
    assert(m->regs[0x10]==0x06 && m->regs[0x11]==0x06 && m->regs[0x12]==0x44);
    assert(m->regs[0x15]==0x0d && m->regs[0x17]==3 && m->regs[0x4e]==0x99 && m->regs[3]==1);
    assert(m->regs[0x13]&8);
}
static void put16(model *m,unsigned reg,int16_t value) {
    uint16_t bits=(uint16_t)value;m->regs[reg]=(uint8_t)bits;m->regs[reg+1]=(uint8_t)(bits>>8);
}
static void data(model *m) {
    const int16_t values[10]={INT16_MIN,-1,INT16_MAX,100,200,-300,-1000,0,1000,-256};
    for(unsigned i=0;i<6;++i)put16(m,0x22+2*i,values[i]);
    for(unsigned i=0;i<3;++i)put16(m,0x34+2*i,values[6+i]);
    put16(m,0x20,values[9]);m->regs[0x1e]=15;
}
int main(void) {
    model m;r10_imu d;
    setup(&m);configured(&m,&d,0);data(&m);r10_imu_poll(&d,90);
    assert(d.state==R10_IMU_WAIT_DATA && d.samples==0); /* early DRDY cannot pass */
    r10_imu_poll(&d,190);
    assert(d.state==R10_IMU_READY && d.valid_mask==15 && d.samples==1 && d.who==0x73);
    const int16_t expected[10]={INT16_MIN,-1,INT16_MAX,100,200,-300,-1000,0,1000,-256};
    assert(memcmp(d.raw,expected,sizeof expected)==0 && d.endpoint_mask==5);
    /* No ready bit does not replace a recently valid sample with zeros. */
    m.regs[0x1e]=0;r10_imu_poll(&d,191);assert(d.state==R10_IMU_READY && d.samples==1);
    r10_imu_poll(&d,441);assert(d.state==R10_IMU_STALE && d.valid_mask==0 && d.error==R10_IMU_NO_DATA);
    data(&m);r10_imu_poll(&d,460);assert(d.state==R10_IMU_READY && d.samples==2);
    /* Temperature validity is separate from low/high acceleration and gyro. */
    m.regs[0x1e]=11;r10_imu_poll(&d,480);assert(d.valid_mask==11);
    /* An error on the second burst must not expose the first burst as new data. */
    int16_t saved[10];memcpy(saved,d.raw,sizeof saved);put16(&m,0x22,1234);
    m.fail_reg=0x34;m.fail_read=1;unsigned samples=d.samples;r10_imu_poll(&d,500);
    assert(d.state==R10_IMU_ERROR && d.error==R10_IMU_DATA_READ && d.valid_mask==0);
    assert(memcmp(saved,d.raw,sizeof saved)==0 && d.samples==samples && d.bus_errors==1);
    unsigned calls=m.calls;r10_imu_poll(&d,1499);assert(m.calls==calls);
    r10_imu_poll(&d,1500);assert(d.retry_count==1 && d.state==R10_IMU_BOOT_WAIT);
    assert(d.bus_detail==0xaabbccdd && d.last_error==R10_IMU_DATA_READ);
    m.fail_reg=-1;r10_imu_poll(&d,1535);r10_imu_poll(&d,1570);data(&m);r10_imu_poll(&d,1690);
    assert(d.state==R10_IMU_READY && d.samples==samples+1 && d.last_error==R10_IMU_DATA_READ);
    /* Wrong identity: no device writes (including no POR). */
    setup(&m);m.regs[0x0f]=0xe9;r10_imu_io bus=io(&m);r10_imu_begin(&d,&bus,0);r10_imu_poll(&d,35);
    assert(d.error==R10_IMU_ID && m.writes==0);
    setup(&m);m.hold_reset=1;bus=io(&m);r10_imu_begin(&d,&bus,0);r10_imu_poll(&d,35);r10_imu_poll(&d,70);
    assert(d.error==R10_IMU_RESET);
    setup(&m);m.ignore_write=0x17;bus=io(&m);r10_imu_begin(&d,&bus,0);r10_imu_poll(&d,35);r10_imu_poll(&d,70);
    assert(d.error==R10_IMU_CONFIG_MISMATCH && d.valid_mask==0);
    /* Vendor read/modify/write failure latches the bus: no follow-on write. */
    setup(&m);bus=io(&m);r10_imu_begin(&d,&bus,0);r10_imu_poll(&d,35);
    m.fail_reg=0x15;m.fail_read=1;unsigned writes=m.writes;r10_imu_poll(&d,70);
    assert(d.error==R10_IMU_CONFIG_WRITE && m.writes==writes+4); /* interface, IF_INC, BDU, DRDY mask */
    calls=m.calls;r10_imu_poll(&d,71);assert(m.calls==calls);
    /* Each protected configuration field can independently fail the sample. */
    const uint8_t regs[8]={0x10,0x11,0x12,0x15,0x17,0x4e,0x03,0x13};
    const uint8_t bits[8]={1,1,0x40,1,1,1,4,8};
    for(unsigned i=0;i<8;++i) {
        setup(&m);configured(&m,&d,0);data(&m);m.regs[regs[i]]^=bits[i];r10_imu_poll(&d,190);
        assert(d.error==R10_IMU_CONFIG_MISMATCH && d.samples==0 && d.valid_mask==0);
    }
    setup(&m);configured(&m,&d,0xfffffff0u);data(&m);r10_imu_poll(&d,0xfffffff0u+190u);
    assert(d.state==R10_IMU_READY);
    d.samples=0xffffffffu;r10_imu_poll(&d,0xfffffff0u+200u);assert(d.samples==0 && d.has_sample);
    m.regs[0x1e]=0;r10_imu_poll(&d,0xfffffff0u+201u);assert(d.state==R10_IMU_READY);
    /* Persistent matching config + no data must eventually reinitialize too. */
    setup(&m);configured(&m,&d,0);r10_imu_poll(&d,321);assert(d.state==R10_IMU_STALE);
    r10_imu_poll(&d,1320);assert(d.retry_count==0);
    r10_imu_poll(&d,1321);assert(d.retry_count==1 && d.state==R10_IMU_BOOT_WAIT && m.inits==2);
    /* Inject a transport failure at every initialization/configuration transfer.
     * No vendor helper may send another transaction after the failed one. */
    setup(&m);configured(&m,&d,0);unsigned config_calls=m.calls;
    for(unsigned n=1;n<=config_calls;++n) {
        setup(&m);m.fail_call=n;bus=io(&m);r10_imu_begin(&d,&bus,0);
        r10_imu_poll(&d,35);r10_imu_poll(&d,70);
        assert(d.state==R10_IMU_ERROR && d.valid_mask==0 && d.samples==0 && d.bus_errors==1);
        assert(m.calls==n && d.bus_failed && d.bus_detail==0xaabbccdd);
    }
    setup(&m);m.hz=2000000;bus=io(&m);r10_imu_begin(&d,&bus,0);assert(d.error==R10_IMU_PORT && m.calls==0);
    setup(&m);m.init_error=1;bus=io(&m);r10_imu_begin(&d,&bus,0);assert(d.error==R10_IMU_PORT && d.bus_detail==0x11110000u);
    r10_imu_begin(&d,NULL,0);assert(d.error==R10_IMU_PORT);
    puts("scripted IMU cases passed; no hardware or sensor physics tested");
    return 0;
}
