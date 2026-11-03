#include "flash_ro.h"
#include <string.h>
/* Manufacturer RevM Table1/2 andFigure41. All addresses are zero. The quad-ID
 * frame is 1-line instruction,4-line24-bit address,4-line8-bitF0 mode,4dummy
 * cycles and4-line data. No state-changing flash opcode belongs in this table. */
static const r10_flash_ro_command commands[FRO_COMMANDS]={
    {0x05,0,0,0,0,0,0,1,1}, {0x35,0,0,0,0,0,0,1,1},
    {0x15,0,0,0,0,0,0,1,1}, {0x9f,0,0,0,0,0,0,1,3},
    {0x5a,1,24,0,0,0,8,1,8}, {0x94,4,24,4,8,0xf0,4,4,4},
    {0x9f,0,0,0,0,0,0,1,3}, {0x05,0,0,0,0,0,0,1,1}
};
const r10_flash_ro_command *r10_flash_ro_descriptor(unsigned c) {
    return c<FRO_COMMANDS?&commands[c]:0;
}
static void failed(r10_flash_ro *f,unsigned error,uint32_t now) {
    f->error=f->last_error=error;f->last_error_detail=f->detail;
    f->valid=0u;++f->failures;f->stage_at=now;
    uint32_t detail=0u;
    if (f->io.cancel(f->io.context,&detail)!=FRO_OK) {
        f->cleanup_error=FRO_CLEANUP;f->cleanup_detail=detail;f->state=FRO_STOPPED;
    } else {
        f->cleanup_error=0u;f->cleanup_detail=0u;
        f->state=error==FRO_TIMEBASE?FRO_STOPPED:FRO_RETRY;
    }
}
static void batch(r10_flash_ro *f,uint32_t now) {
    f->batch_at=now;f->command=0u;f->completed_mask=0u;f->io_count=0u;
    memset(f->raw,0,sizeof(f->raw));memset(f->raw_count,0,sizeof(f->raw_count));
    memset(f->command_ms,0,sizeof(f->command_ms));f->state=FRO_START;
}
void r10_flash_ro_begin(r10_flash_ro *f,const r10_flash_ro_io *io,uint32_t now) {
    if (!f) return;
    memset(f,0,sizeof(*f));f->stage_at=f->observed_ms=now;
    if (!io || !io->initialize || !io->start || !io->poll || !io->cancel) {
        f->state=FRO_STOPPED;f->error=f->last_error=FRO_ADAPTER;return;
    }
    f->io=*io;f->state=FRO_INITIALIZING;
}
static unsigned confirmed(r10_flash_ro *f) {
    switch (f->command) {
    case FRO_SR1:case FRO_SR1_AFTER:
        if (f->raw[f->command][0]&1u) return FRO_DEVICE_BUSY;
        if (f->command==FRO_SR1_AFTER && f->raw[FRO_SR1][0]!=f->raw[FRO_SR1_AFTER][0])
            return FRO_STATUS_CHANGED;
        break;
    case FRO_SR2:if (f->raw[FRO_SR2][0]&0x80u) return FRO_SUSPENDED;break;
    case FRO_ID_A:
        if (memcmp(f->raw[FRO_ID_A],"\xef\x40\x18",3u)) return FRO_IDENTITY;
        break;
    case FRO_SFDP:if (memcmp(f->raw[FRO_SFDP],"SFDP",4u)) return FRO_SFDP_SIGNATURE;break;
    case FRO_QUAD_ID:
        if (memcmp(f->raw[FRO_QUAD_ID],"\xef\x17\xef\x17",4u)) return FRO_QUAD_IDENTITY;
        break;
    case FRO_ID_B:if (memcmp(f->raw[FRO_ID_A],f->raw[FRO_ID_B],3u)) return FRO_UNSTABLE_ID;break;
    default:break;
    }
    return FRO_NO_ERROR;
}
void r10_flash_ro_poll(r10_flash_ro *f,uint32_t now) {
    if (!f || f->state==FRO_OFF || f->state==FRO_STOPPED) return;
    if ((uint32_t)(now-f->observed_ms)>=0x80000000u) {failed(f,FRO_TIMEBASE,now);return;}
    f->observed_ms=now;
    switch (f->state) {
    case FRO_RETRY:
        if ((uint32_t)(now-f->stage_at)>=FRO_RETRY_MS) {
            ++f->retries;f->stage_at=now;f->nominal_hz=0u;f->state=FRO_INITIALIZING;
        }
        return;
    case FRO_INITIALIZING: {
        if ((uint32_t)(now-f->stage_at)>=FRO_INIT_MS) {failed(f,FRO_TIMEOUT,now);return;}
        f->detail=0u;int rc=f->io.initialize(f->io.context,now,&f->nominal_hz,&f->detail);
        if (rc==FRO_BUSY) return;
        if (rc!=FRO_OK) {failed(f,FRO_INIT_ERROR,now);return;}
        if (f->nominal_hz!=1000000u) {failed(f,FRO_CONFIG,now);return;}
        f->state=FRO_INIT_CONFIRM;return;
    }
    case FRO_INIT_CONFIRM:
        if ((uint32_t)(now-f->stage_at)>=FRO_INIT_MS) {failed(f,FRO_TIMEOUT,now);return;}
        f->stage_at=now;f->state=FRO_POWER_GUARD;return;
    case FRO_POWER_GUARD:
        if ((uint32_t)(now-f->stage_at)>=1u) {f->error=0u;batch(f,now);}
        return;
    case FRO_WAIT:
        if ((uint32_t)(now-f->last_good_ms)>=FRO_PERIOD_MS) batch(f,now);
        return;
    case FRO_START:case FRO_READING:case FRO_CONFIRM:
        if ((uint32_t)(now-f->batch_at)>=FRO_BATCH_MS) {failed(f,FRO_TIMEOUT,now);return;}
        break;
    default:failed(f,FRO_ADAPTER,now);return;
    }
    if (f->command>=FRO_COMMANDS) {failed(f,FRO_ADAPTER,now);return;}
    const r10_flash_ro_command *c=&commands[f->command];
    if (f->state==FRO_START) {
        if (f->command==FRO_QUAD_ID && !(f->raw[FRO_SR2][0]&2u)) {failed(f,FRO_QUAD_DISABLED,now);return;}
        f->detail=0u;f->stage_at=f->command_ms[f->command]=now;
        if (f->io.start(f->io.context,f->command,&f->detail)!=FRO_OK) {failed(f,FRO_START_ERROR,now);return;}
        f->state=FRO_READING;return;
    }
    if ((uint32_t)(now-f->stage_at)>=FRO_TRANSFER_MS) {failed(f,FRO_TIMEOUT,now);return;}
    if (f->state==FRO_READING) {
        unsigned before=f->raw_count[f->command];
        if (before>c->length) {failed(f,FRO_COUNT,now);return;}
        uint8_t data[FRO_BYTES_MAX]={0};uint32_t got=0u;f->detail=0u;
        int rc=f->io.poll(f->io.context,data,c->length-before,&got,&f->detail);f->io_count=got;
        if (got>c->length-before) {failed(f,FRO_COUNT,now);return;}
        memcpy(&f->raw[f->command][before],data,got);f->raw_count[f->command]=(uint8_t)(before+got);
        if (rc==FRO_BUSY) return;
        if (rc!=FRO_OK) {failed(f,FRO_READ_ERROR,now);return;}
        if (f->raw_count[f->command]!=c->length) {failed(f,FRO_COUNT,now);return;}
        f->completed_mask|=1u<<f->command;f->state=FRO_CONFIRM;return;
    }
    unsigned error=confirmed(f);
    if (error) {failed(f,error,now);return;}
    if (++f->command<FRO_COMMANDS) {f->state=FRO_START;return;}
    memcpy(f->sample_raw,f->raw,sizeof(f->raw));
    memcpy(f->sample_command_ms,f->command_ms,sizeof(f->command_ms));
    f->sample_nominal_hz=f->nominal_hz;f->last_good_ms=f->batch_at;
    ++f->samples;f->has_sample=f->valid=1u;f->error=0u;f->state=FRO_WAIT;
}
int r10_flash_ro_fresh(const r10_flash_ro *f,uint32_t now) {
    return f && f->has_sample && f->valid && !f->error &&
           (f->state==FRO_START || f->state==FRO_READING || f->state==FRO_CONFIRM || f->state==FRO_WAIT) &&
           (uint32_t)(now-f->last_good_ms)<FRO_FRESH_MS;
}
