#ifndef R10_SD_QUERY_H
#define R10_SD_QUERY_H
#include "metadata.h"

/* No hardware implementation is supplied here. A future adapter must use only
 * SPI3/its reviewed pins, finite register budgets, safe deselection and bounded
 * cleanup. Poll returns normalized response prefixes, retaining wire evidence
 * separately. It must enforce SPI response/clock timing, not just these nominal
 * scheduling guards. CMD0 is state-changing; exclusive cold start is required. */
enum { SDQ_IO_OK=0, SDQ_IO_BUSY=1, SDQ_IO_ERROR=2, SDQ_PROBE_REQUEST=SDM_COMMANDS };
enum { SDQ_OFF=0,SDQ_POWER_GUARD,SDQ_INITIALIZING,SDQ_INIT_CONFIRM,SDQ_START,SDQ_READING,
       SDQ_CONFIRM,SDQ_OP_WAIT,SDQ_RELEASE_CONFIRM,SDQ_COMPLETE,SDQ_STOPPED };
enum { SDQ_PROBE=0,SDQ_RESET,SDQ_IFCOND,SDQ_CRC_ON,SDQ_OCR_BEFORE,
       SDQ_APP,SDQ_OP_COND,SDQ_OCR_AFTER,SDQ_CSD,SDQ_CID,SDQ_PHASES };
enum { SDQ_OK=0,SDQ_ADAPTER,SDQ_COLD_START_REQUIRED,SDQ_INIT_ERROR,
       SDQ_CLOCK,SDQ_START_ERROR,SDQ_READ_ERROR,SDQ_COUNT,SDQ_TIMEOUT,
       SDQ_TIMEBASE,SDQ_CARD_STATUS,SDQ_IFCOND_ERROR,SDQ_VOLTAGE,
       SDQ_INIT_TIMEOUT,SDQ_METADATA,SDQ_CLEANUP,SDQ_BUS_NOT_IDLE,
       SDQ_OP_CLOCK_GAP };
/* Engineering bench policies, nominal ms, not measured physical timing. The
 *25ms stopped-clock guard is stricter than SDA4.4's <50ms polling rule. */
enum { SDQ_POWER_MS=2,SDQ_INIT_MS=500,SDQ_TRANSFER_MS=200,
       SDQ_OP_MS=1500,SDQ_OP_GAP_MS=25,SDQ_TOTAL_MS=5000 };
typedef struct {
    void *context;
    int (*initialize)(void *,uint32_t now,uint32_t *nominal_hz,
                      uint32_t *idle_clocks,uint32_t *detail);
    int (*start)(void *,unsigned request,uint32_t *detail);
    int (*poll)(void *,uint8_t *data,unsigned capacity,unsigned *count,uint32_t *detail);
    int (*cancel)(void *,uint32_t *detail);
} r10_sd_query_io;
typedef struct {
    r10_sd_query_io io;
    uint32_t state,error,detail,cleanup_error,cleanup_detail;
    uint32_t started_at,observed_at,stage_at,command_at,op_started_at;
    uint32_t last_op_at,completed_at,nominal_hz,idle_clocks;
    uint32_t failed_phase,commands_started,op_requests,last_io_count,metadata_error;
    uint32_t command_ticks[SDQ_PHASES],completed_mask;
    unsigned phase,version2,op_started,op_ready,valid,cold_start_declared;
    uint8_t counts[SDQ_PHASES],raw[SDQ_PHASES][20];
    r10_sd_metadata metadata;
} r10_sd_query;

void r10_sd_query_begin(r10_sd_query *,const r10_sd_query_io *,uint32_t now,
                        unsigned exclusive_cold_start_declared);
void r10_sd_query_poll(r10_sd_query *,uint32_t now);
#endif
