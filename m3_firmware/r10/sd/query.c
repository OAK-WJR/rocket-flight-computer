#include "query.h"
#include <string.h>

static void fail(r10_sd_query *q,unsigned error,uint32_t now) {
    unsigned already_released=q->state==SDQ_RELEASE_CONFIRM;
    q->error=error;q->failed_phase=q->phase;q->valid=0;q->stage_at=now;
    uint32_t detail=0;
    if (!already_released && q->io.cancel(q->io.context,&detail)!=SDQ_IO_OK) {
        q->cleanup_error=SDQ_CLEANUP;q->cleanup_detail=detail;
    }
    q->state=SDQ_STOPPED; /* Never issue a reset/retry after a failure. */
}
void r10_sd_query_begin(r10_sd_query *q,const r10_sd_query_io *io,uint32_t now,unsigned cold) {
    if (!q) return;
    memset(q,0,sizeof(*q));q->started_at=q->observed_at=q->stage_at=now;
    q->cold_start_declared=cold==1u;
    if (!q->cold_start_declared) {q->error=SDQ_COLD_START_REQUIRED;q->state=SDQ_STOPPED;return;}
    if (!io || !io->initialize || !io->start || !io->poll || !io->cancel) {
        q->error=SDQ_ADAPTER;q->state=SDQ_STOPPED;return;
    }
    q->io=*io;q->state=SDQ_POWER_GUARD;
}
static unsigned request(const r10_sd_query *q) {
    static const unsigned commands[SDQ_PHASES]={SDQ_PROBE_REQUEST,SDM_CMD0,SDM_CMD8,
        SDM_CRC_ON,SDM_CMD58,SDM_CMD55,SDM_ACMD41_SDSC,SDM_CMD58,SDM_CMD9,SDM_CMD10};
    return q->phase==SDQ_OP_COND && q->version2?SDM_ACMD41_HC:commands[q->phase];
}
static unsigned confirm(r10_sd_query *q,uint32_t now) {
    unsigned phase=q->phase,count=q->counts[phase];const uint8_t *p=q->raw[phase];
    if (phase==SDQ_PROBE) {
        if (count!=8u) return SDQ_COUNT;
        for (unsigned i=0;i<count;++i) if (p[i]!=0xffu) return SDQ_BUS_NOT_IDLE;
    } else {
        if (!count) return SDQ_COUNT;
        if (phase==SDQ_IFCOND && p[0]==5u) {
            if (count!=1u) return SDQ_COUNT;
            q->version2=0u; /* SDv1 branch, never a CMD1/MMC fallback. */
        } else if (phase==SDQ_IFCOND) {
            if (p[0]!=1u) return SDQ_CARD_STATUS;
            if (count!=5u) return SDQ_COUNT;
            if (p[1] || p[2] || p[3]!=1u || p[4]!=0xaau) return SDQ_IFCOND_ERROR;
            q->version2=1u;
        } else if (phase==SDQ_OCR_BEFORE || phase==SDQ_OCR_AFTER) {
            if (p[0]>1u || (phase==SDQ_OCR_AFTER && p[0])) return SDQ_CARD_STATUS;
            if (count!=5u) return SDQ_COUNT;
            uint32_t ocr=((uint32_t)p[1]<<24)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<8)|p[4];
            if (!(ocr&0x00300000u)) return SDQ_VOLTAGE;
            if (phase==SDQ_OCR_AFTER && !(ocr&0x80000000u)) return SDQ_CARD_STATUS;
        } else if (phase==SDQ_CSD || phase==SDQ_CID) {
            if (p[0]) return SDQ_CARD_STATUS;
            if (count!=20u) return SDQ_COUNT;
            (void)r10_sd_metadata_decode(q->raw[SDQ_OCR_AFTER],5u,
                q->raw[SDQ_CID],phase==SDQ_CID?20u:0u,q->raw[SDQ_CSD],20u,&q->metadata);
            unsigned code=q->metadata.errors[phase==SDQ_CID?1u:2u];
            if (code) {q->metadata_error=code;return SDQ_METADATA;}
            if (phase==SDQ_CID && !q->metadata.metadata_valid) {
                q->metadata_error=q->metadata.errors[0];return SDQ_METADATA;
            }
        } else {
            if (count!=1u) return SDQ_COUNT;
            if (phase==SDQ_RESET || phase==SDQ_CRC_ON) {
                if (p[0]!=1u) return SDQ_CARD_STATUS;
            } else if (p[0]>1u) return SDQ_CARD_STATUS;
        }
    }
    q->completed_mask|=1u<<phase;
    if (phase==SDQ_OP_COND && p[0]) {
        q->stage_at=now;q->state=SDQ_OP_WAIT;return SDQ_OK;
    }
    if (phase==SDQ_OP_COND) q->op_ready=1u;
    if (phase==SDQ_CID) {
        uint32_t detail=0;
        if (q->io.cancel(q->io.context,&detail)!=SDQ_IO_OK) {
            q->error=q->cleanup_error=SDQ_CLEANUP;q->cleanup_detail=detail;
            q->failed_phase=phase;q->state=SDQ_STOPPED;return SDQ_OK;
        }
        /* cancel() is also a callback. Its elapsed time must be observed by a
         * subsequent poll before an acquisition is accepted as complete. */
        q->state=SDQ_RELEASE_CONFIRM;return SDQ_OK;
    }
    ++q->phase;q->state=SDQ_START;return SDQ_OK;
}
void r10_sd_query_poll(r10_sd_query *q,uint32_t now) {
    if (!q || q->state==SDQ_OFF || q->state==SDQ_STOPPED || q->state==SDQ_COMPLETE) return;
    if ((uint32_t)(now-q->observed_at)>=0x80000000u) {fail(q,SDQ_TIMEBASE,now);return;}
    q->observed_at=now;
    if ((uint32_t)(now-q->started_at)>=SDQ_TOTAL_MS) {fail(q,SDQ_TIMEOUT,now);return;}
    if (q->op_started && !q->op_ready) {
        if ((uint32_t)(now-q->op_started_at)>=SDQ_OP_MS) {fail(q,SDQ_INIT_TIMEOUT,now);return;}
        if ((uint32_t)(now-q->last_op_at)>=SDQ_OP_GAP_MS) {fail(q,SDQ_OP_CLOCK_GAP,now);return;}
    }
    if (q->phase>=SDQ_PHASES) {fail(q,SDQ_ADAPTER,now);return;}
    if (q->state==SDQ_RELEASE_CONFIRM) {
        if ((uint32_t)(now-q->command_at)>=SDQ_TRANSFER_MS) {fail(q,SDQ_TIMEOUT,now);return;}
        q->valid=1u;q->completed_at=now;q->state=SDQ_COMPLETE;return;
    }
    if (q->state==SDQ_POWER_GUARD) {
        if ((uint32_t)(now-q->stage_at)>=SDQ_POWER_MS) {
            q->stage_at=now;q->state=SDQ_INITIALIZING;
        }
        return;
    }
    if (q->state==SDQ_INITIALIZING) {
        if ((uint32_t)(now-q->stage_at)>=SDQ_INIT_MS) {fail(q,SDQ_TIMEOUT,now);return;}
        q->detail=0;int rc=q->io.initialize(q->io.context,now,&q->nominal_hz,&q->idle_clocks,&q->detail);
        if (rc==SDQ_IO_BUSY) return;
        if (rc!=SDQ_IO_OK) {fail(q,SDQ_INIT_ERROR,now);return;}
        q->state=SDQ_INIT_CONFIRM;return;
    }
    if (q->state==SDQ_INIT_CONFIRM) {
        /* Include the initialize callback's elapsed time before any card command. */
        if ((uint32_t)(now-q->stage_at)>=SDQ_INIT_MS) {fail(q,SDQ_TIMEOUT,now);return;}
        if (q->nominal_hz!=250000u || q->idle_clocks<80u) {fail(q,SDQ_CLOCK,now);return;}
        q->state=SDQ_START;return;
    }
    if (q->state==SDQ_OP_WAIT) {
        if ((uint32_t)(now-q->stage_at)>=2u) {q->phase=SDQ_APP;q->state=SDQ_START;}
        return;
    }
    if (q->state==SDQ_START) {
        unsigned op=request(q);q->counts[q->phase]=0;
        memset(q->raw[q->phase],0,20u);q->completed_mask&=~(1u<<q->phase);
        q->command_at=q->command_ticks[q->phase]=now;q->detail=0;++q->commands_started;
        if (q->phase==SDQ_OP_COND) {
            if (!q->op_started) {q->op_started_at=now;q->op_started=1u;}
            q->last_op_at=now;++q->op_requests;
        }
        if (q->io.start(q->io.context,op,&q->detail)!=SDQ_IO_OK) {fail(q,SDQ_START_ERROR,now);return;}
        q->state=SDQ_READING;return;
    }
    if (q->state==SDQ_READING || q->state==SDQ_CONFIRM) {
        if ((uint32_t)(now-q->command_at)>=SDQ_TRANSFER_MS) {fail(q,SDQ_TIMEOUT,now);return;}
        if (q->state==SDQ_CONFIRM) {
            unsigned error=confirm(q,now);if (error) fail(q,error,now);return;
        }
        uint8_t data[20]={0};unsigned got=0,have=q->counts[q->phase];q->detail=0;
        if (have>20u) {fail(q,SDQ_COUNT,now);return;}
        int rc=q->io.poll(q->io.context,data,20u-have,&got,&q->detail);q->last_io_count=got;
        if (got>20u-have) {fail(q,SDQ_COUNT,now);return;}
        if (got) {memcpy(q->raw[q->phase]+have,data,got);q->counts[q->phase]=(uint8_t)(have+got);}
        if (rc==SDQ_IO_BUSY) return;
        if (rc!=SDQ_IO_OK) {fail(q,SDQ_READ_ERROR,now);return;}
        q->state=SDQ_CONFIRM;return;
    }
    fail(q,SDQ_ADAPTER,now);
}
