/* Scripted transport faults exercise the actual asynchronous core. No hardware
 * model, storage-array validation or peripheral access is claimed here. */
#include "flash_ro.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    uint8_t response[8][8];
    unsigned command, offset, chunk, starts[32], nstarts, calls, cancels;
    int initialize_rc, start_bad, read_bad, cleanup_rc;
    unsigned short_read, excess, busy_forever, hold_completion, fail_after;
    uint32_t hz, detail;
} transport;

static const uint8_t lengths[8]={1,1,1,3,8,4,3,1};
static void reset_transport(transport *t) {
    memset(t,0,sizeof(*t));
    t->chunk=8;t->hz=1000000;t->start_bad=-1;t->read_bad=-1;
    t->response[1][0]=2;
    memcpy(t->response[3],"\xef\x40\x18",3);
    memcpy(t->response[4],"SFDP\x05\x01\x00\xff",8);
    memcpy(t->response[5],"\xef\x17\xef\x17",4);
    memcpy(t->response[6],"\xef\x40\x18",3);
}
static int initialize(void *ctx,uint32_t now,uint32_t *hz,uint32_t *detail) {
    transport *t=ctx;(void)now;++t->calls;*hz=t->hz;*detail=t->detail;
    return t->initialize_rc;
}
static int start(void *ctx,unsigned command,uint32_t *detail) {
    transport *t=ctx;assert(command<8 && t->nstarts<32);
    /* Independent wire specification: opcode/address/mode/dummy/data widths.
     * This rejects state-changing or unreviewed frames before fake I/O. */
    static const uint8_t expected[8][9]={
        {5,0,0,0,0,0,0,1,1},{0x35,0,0,0,0,0,0,1,1},
        {0x15,0,0,0,0,0,0,1,1},{0x9f,0,0,0,0,0,0,1,3},
        {0x5a,1,24,0,0,0,8,1,8},{0x94,4,24,4,8,0xf0,4,4,4},
        {0x9f,0,0,0,0,0,0,1,3},{5,0,0,0,0,0,0,1,1}
    };
    const r10_flash_ro_command *d=r10_flash_ro_descriptor(command);assert(d);
    const uint8_t got[9]={d->opcode,d->address_lines,d->address_bits,
        d->alternate_lines,d->alternate_bits,d->alternate_value,
        d->dummy_cycles,d->data_lines,d->length};
    assert(!memcmp(got,expected[command],9));
    t->starts[t->nstarts++]=command;t->command=command;t->offset=0;
    *detail=t->detail;return (int)command==t->start_bad?FRO_ERROR:FRO_OK;
}
static int poll_io(void *ctx,uint8_t *bytes,uint32_t capacity,uint32_t *received,uint32_t *detail) {
    transport *t=ctx;assert(t->command<8);++t->calls;*detail=t->detail;
    assert(capacity==lengths[t->command]-t->offset);
    *received=0;
    if (t->busy_forever) return FRO_BUSY;
    if (t->excess) {*received=capacity+1;return FRO_OK;}
    if (t->short_read) return FRO_OK;
    unsigned n=capacity<t->chunk?capacity:t->chunk;
    memcpy(bytes,t->response[t->command]+t->offset,n);
    t->offset+=n;*received=n;
    if ((int)t->command==t->read_bad && t->offset>=t->fail_after) return FRO_ERROR;
    if (t->offset<lengths[t->command] || t->hold_completion) return FRO_BUSY;
    return FRO_OK;
}
static int cancel(void *ctx,uint32_t *detail) {
    transport *t=ctx;++t->cancels;*detail=t->detail;return t->cleanup_rc;
}
static void begin(transport *t,r10_flash_ro *f,uint32_t now) {
    r10_flash_ro_io io={t,initialize,start,poll_io,cancel};
    r10_flash_ro_begin(f,&io,now);
}
static void tick(r10_flash_ro *f,uint32_t *now) {r10_flash_ro_poll(f,(*now)++);}
static void until(r10_flash_ro *f,uint32_t *now,unsigned state) {
    for (unsigned n=0;n<600 && f->state!=state;++n) tick(f,now);
    assert(f->state==state);
}
static void failure(r10_flash_ro *f,uint32_t *now,unsigned error) {
    until(f,now,FRO_RETRY);
    assert(f->error==error && f->last_error==error && f->failures==1);
    assert(!f->valid && !r10_flash_ro_fresh(f,*now));
}
static void good(transport *t,r10_flash_ro *f,uint32_t *now) {
    until(f,now,FRO_WAIT);
    assert(f->samples==1 && f->has_sample && f->valid && !f->error);
    assert(f->completed_mask==255 && t->nstarts==8);
    for (unsigned i=0;i<8;++i) {
        assert(t->starts[i]==i && f->raw_count[i]==lengths[i]);
        assert(!memcmp(f->sample_raw[i],t->response[i],lengths[i]));
        assert(f->sample_command_ms[i]==f->command_ms[i]);
    }
    assert(f->sample_nominal_hz==1000000 && r10_flash_ro_fresh(f,*now));
    assert(r10_flash_ro_fresh(f,f->last_good_ms+2999));
    assert(!r10_flash_ro_fresh(f,f->last_good_ms+3000));
}
int main(int argc,char **argv) {
    assert(argc>=2);const char *name=argv[1];
    unsigned arg=argc>2?(unsigned)strtoul(argv[2],0,0):0;
    transport t;r10_flash_ro f;uint32_t now=0;
    reset_transport(&t);
    if (!strcmp(name,"good")) {
        t.chunk=arg;assert(arg>=1 && arg<=8);begin(&t,&f,now);good(&t,&f,&now);
    } else if (!strcmp(name,"wrap")) {
        now=0xfffffff8u;begin(&t,&f,now);good(&t,&f,&now);
    } else if (!strcmp(name,"bad-adapter")) {
        r10_flash_ro_io io={&t,initialize,start,poll_io,cancel};
        switch(arg) {case 0:io.initialize=0;break;case 1:io.start=0;break;
            case 2:io.poll=0;break;case 3:io.cancel=0;break;default:assert(0);}
        r10_flash_ro_begin(&f,&io,0);assert(f.state==FRO_STOPPED && f.error==FRO_ADAPTER);
        r10_flash_ro_poll(&f,1);assert(!t.calls && !t.nstarts && !t.cancels);
    } else if (!strcmp(name,"init-error")) {
        t.initialize_rc=-1;t.detail=0x12345678;begin(&t,&f,0);failure(&f,&now,FRO_INIT_ERROR);
        assert(f.detail==t.detail && f.last_error_detail==t.detail && t.cancels==1);
    } else if (!strcmp(name,"init-clock")) {
        t.hz=arg;begin(&t,&f,0);failure(&f,&now,FRO_CONFIG);assert(!t.nstarts);
    } else if (!strcmp(name,"init-timeout")) {
        t.initialize_rc=1;begin(&t,&f,0);r10_flash_ro_poll(&f,499);
        assert(f.state==FRO_INITIALIZING);r10_flash_ro_poll(&f,500);
        assert(f.state==FRO_RETRY && f.error==FRO_TIMEOUT && t.calls==1);
    } else if (!strcmp(name,"init-latency")) {
        begin(&t,&f,0);r10_flash_ro_poll(&f,0);r10_flash_ro_poll(&f,500);
        assert(f.state==FRO_RETRY && f.error==FRO_TIMEOUT && !t.nstarts);
    } else if (!strcmp(name,"power-guard")) {
        begin(&t,&f,0);r10_flash_ro_poll(&f,0);r10_flash_ro_poll(&f,1);
        assert(f.state==FRO_POWER_GUARD);
        for (unsigned n=0;n<50;++n) r10_flash_ro_poll(&f,1);
        assert(f.state==FRO_POWER_GUARD && !t.nstarts);
        r10_flash_ro_poll(&f,2);assert(f.state==FRO_START && !t.nstarts);
    } else if (!strcmp(name,"start-error")) {
        assert(arg<8);t.start_bad=(int)arg;t.detail=123;begin(&t,&f,0);
        failure(&f,&now,FRO_START_ERROR);assert(t.nstarts==arg+1 && f.command==arg);
        assert(f.completed_mask==((1u<<arg)-1u) && f.last_error_detail==123);
    } else if (!strcmp(name,"read-error")) {
        assert(arg<8);t.read_bad=(int)arg;t.chunk=1;t.detail=321;begin(&t,&f,0);
        failure(&f,&now,FRO_READ_ERROR);assert(f.command==arg && f.raw_count[arg]==1);
        assert(f.raw[arg][0]==t.response[arg][0] && f.last_error_detail==321);
    } else if (!strcmp(name,"partial-error")) {
        unsigned command=arg/16,bytes=arg%16;
        assert(command<8 && bytes>=1 && bytes<=lengths[command]);
        t.read_bad=(int)command;t.fail_after=bytes;t.chunk=1;begin(&t,&f,0);
        failure(&f,&now,FRO_READ_ERROR);
        assert(f.command==command && f.raw_count[command]==bytes);
        assert(!memcmp(f.raw[command],t.response[command],bytes));
    } else if (!strcmp(name,"count")) {
        t.excess=arg==0;t.short_read=arg==1;begin(&t,&f,0);failure(&f,&now,FRO_COUNT);
        assert(f.command==0 && !f.raw_count[0]);
    } else if (!strcmp(name,"timeout")) {
        t.busy_forever=1;begin(&t,&f,0);until(&f,&now,FRO_READING);
        uint32_t started=f.stage_at;r10_flash_ro_poll(&f,started+19);
        assert(f.state==FRO_READING);r10_flash_ro_poll(&f,started+20);
        assert(f.state==FRO_RETRY && f.error==FRO_TIMEOUT);
    } else if (!strcmp(name,"confirm-deadline")) {
        begin(&t,&f,0);until(&f,&now,FRO_CONFIRM);
        r10_flash_ro_poll(&f,f.stage_at+20);
        assert(f.error==FRO_TIMEOUT && f.state==FRO_RETRY);
    } else if (!strcmp(name,"full-but-busy")) {
        t.hold_completion=1;begin(&t,&f,0);until(&f,&now,FRO_READING);
        r10_flash_ro_poll(&f,now++);
        assert(f.raw_count[0]==1 && f.state==FRO_READING && !f.completed_mask);
        r10_flash_ro_poll(&f,now++);assert(f.state==FRO_READING);
        r10_flash_ro_poll(&f,f.stage_at+20);
        assert(f.state==FRO_RETRY && f.error==FRO_TIMEOUT && f.raw_count[0]==1);
    } else if (!strcmp(name,"batch-deadline")) {
        begin(&t,&f,0);until(&f,&now,FRO_START);
        while (f.state!=FRO_RETRY) {
            if (f.state==FRO_READING) now=f.stage_at+18;
            tick(&f,&now);
        }
        assert(f.error==FRO_TIMEOUT && f.command==7 && f.completed_mask==127);
        assert((uint32_t)(f.observed_ms-f.batch_at)>=150 && !f.has_sample);
    } else if (!strcmp(name,"batch-at-limit")) {
        begin(&t,&f,0);until(&f,&now,FRO_START);
        r10_flash_ro_poll(&f,f.batch_at+150);
        assert(f.state==FRO_RETRY && f.error==FRO_TIMEOUT && !t.nstarts);
    } else if (!strcmp(name,"busy-status")) {
        t.response[0][0]=1;begin(&t,&f,0);failure(&f,&now,FRO_DEVICE_BUSY);
        assert(t.nstarts==1 && f.raw[0][0]==1);
    } else if (!strcmp(name,"suspend")) {
        t.response[1][0]=0x82;begin(&t,&f,0);failure(&f,&now,FRO_SUSPENDED);
        assert(t.nstarts==2);
    } else if (!strcmp(name,"qe-disabled")) {
        t.response[1][0]=0;begin(&t,&f,0);failure(&f,&now,FRO_QUAD_DISABLED);
        assert(t.nstarts==5 && f.completed_mask==31);
    } else if (!strcmp(name,"identity")) {
        assert(arg<24);t.response[3][arg/8]^=(uint8_t)(1u<<(arg%8));
        begin(&t,&f,0);failure(&f,&now,FRO_IDENTITY);assert(t.nstarts==4);
    } else if (!strcmp(name,"sfdp")) {
        assert(arg<32);t.response[4][arg/8]^=(uint8_t)(1u<<(arg%8));
        begin(&t,&f,0);failure(&f,&now,FRO_SFDP_SIGNATURE);assert(t.nstarts==5);
    } else if (!strcmp(name,"quad")) {
        assert(arg<32);t.response[5][arg/8]^=(uint8_t)(1u<<(arg%8));
        begin(&t,&f,0);failure(&f,&now,FRO_QUAD_IDENTITY);assert(t.nstarts==6);
        assert(!memcmp(f.raw[5],t.response[5],4));
    } else if (!strcmp(name,"id-unstable")) {
        t.response[6][2]^=1;begin(&t,&f,0);failure(&f,&now,FRO_UNSTABLE_ID);
    } else if (!strcmp(name,"status-changed")) {
        t.response[7][0]=4;begin(&t,&f,0);failure(&f,&now,FRO_STATUS_CHANGED);
    } else if (!strcmp(name,"last-good")) {
        begin(&t,&f,0);good(&t,&f,&now);uint32_t stamp=f.last_good_ms;
        t.response[3][0]=0;t.detail=42;
        r10_flash_ro_poll(&f,stamp+1000);now=stamp+1001;
        failure(&f,&now,FRO_IDENTITY);
        assert(f.samples==1 && f.has_sample && f.last_good_ms==stamp);
        assert(f.sample_raw[3][0]==0xef && f.raw[3][0]==0);
        assert(f.sample_nominal_hz==1000000);
        memcpy(t.response[3],"\xef\x40\x18",3);t.nstarts=0;
        now=f.stage_at+1000;until(&f,&now,FRO_WAIT);
        assert(f.samples==2 && f.retries==1 && f.failures==1 && !f.error);
        assert(f.last_error==FRO_IDENTITY && f.has_sample && f.valid);
    } else if (!strcmp(name,"cleanup")) {
        t.start_bad=0;t.cleanup_rc=arg?FRO_BUSY:FRO_ERROR;t.detail=0x1234;
        begin(&t,&f,0);until(&f,&now,FRO_STOPPED);
        assert(f.error==FRO_START_ERROR && f.cleanup_error==FRO_CLEANUP);
        assert(f.cleanup_detail==0x1234 && f.last_error_detail==0x1234);
        unsigned calls=t.calls,starts=t.nstarts;r10_flash_ro_poll(&f,1000000);
        assert(t.calls==calls && t.nstarts==starts && !f.valid);
    } else if (!strcmp(name,"backward")) {
        begin(&t,&f,100);r10_flash_ro_poll(&f,100);r10_flash_ro_poll(&f,99);
        assert(f.state==FRO_STOPPED && f.error==FRO_TIMEBASE && t.cancels==1);
    } else if (!strcmp(name,"fresh")) {
        begin(&t,&f,0);good(&t,&f,&now);
        assert(!r10_flash_ro_fresh(&f,f.last_good_ms-1));
        f.state=FRO_RETRY;assert(!r10_flash_ro_fresh(&f,now));
        assert(!r10_flash_ro_fresh(0,0));
    } else if (!strcmp(name,"pending")) {
        begin(&t,&f,0);good(&t,&f,&now);uint32_t stamp=f.last_good_ms;
        r10_flash_ro_poll(&f,stamp+1000);
        assert(f.state==FRO_START && !f.completed_mask && f.command==0);
        assert(f.has_sample && f.valid && f.samples==1 && f.last_good_ms==stamp);
        for (unsigned i=0;i<8;++i) {
            assert(f.raw_count[i]==0 && f.command_ms[i]==0);
            for (unsigned b=0;b<8;++b) assert(f.raw[i][b]==0);
        }
        assert(!memcmp(f.sample_raw[4],"SFDP",4));
        assert(r10_flash_ro_fresh(&f,stamp+1000));
    } else if (!strcmp(name,"descriptor")) {
        assert(!r10_flash_ro_descriptor(8) && !r10_flash_ro_descriptor(0xffffffffu));
        r10_flash_ro_begin(0,0,0);r10_flash_ro_poll(0,0);
    } else assert(0);
    printf("PASS %s %u\n",name,arg);return 0;
}
