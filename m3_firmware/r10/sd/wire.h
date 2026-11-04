#ifndef R10_SD_WIRE_H
#define R10_SD_WIRE_H
#include "query.h"

/* Internal diagnostic transport, not an arbitrary-command service. No native
 * hardware implementation is provided by this file. The bus callbacks must be
 * bounded, preserve SPI1/shared resources and keep CS unchanged by transfer().
 * Counts mean FIFO accepted / received bytes, not measured wire completion. */
typedef struct {
    void *context;
    int (*initialize)(void *,uint32_t *nominal_hz,uint32_t *idle_clocks,uint32_t *detail);
    int (*select)(void *,unsigned asserted,uint32_t *detail);
    int (*transfer)(void *,const uint8_t *tx,uint8_t *rx,unsigned count,
                    unsigned *accepted,unsigned *received,uint32_t *detail);
    int (*release)(void *,uint32_t *detail);
} r10_sd_bus;
enum { SDW_OFF=0,SDW_IDLE,SDW_R1,SDW_SUFFIX,SDW_TOKEN,SDW_REGISTER,SDW_DONE,SDW_FAILED };
enum { SDW_OK=0,SDW_ARGUMENT,SDW_STATE,SDW_SELECT,SDW_TRANSFER,SDW_COUNT,
       SDW_R1_TIMEOUT,SDW_R1_PREFIX,SDW_TOKEN_TIMEOUT,SDW_BAD_TOKEN,SDW_RELEASE };
/* Byte limits are bench engineering policies, not claims that this checks all
 * SD timing. Core wall-clock guards and native finite MMIO budgets also apply. */
enum { SDW_TRACE=64,SDW_R1_BYTES=16,SDW_TOKEN_BYTES=16,SDW_POLL_BYTES=16 };
typedef struct {
    r10_sd_bus bus;
    uint32_t state,error,detail,cleanup_error,cleanup_detail;
    uint32_t request,accepted_total,received_total,exchanges;
    uint32_t prefix_count,token_count,result_count,result_delivered;
    uint32_t trace_accepted,trace_received,initialized,selected;
    uint8_t tx_prefix[SDW_TRACE],rx_prefix[SDW_TRACE],result[20];
} r10_sd_wire;

/* The returned normalized IO is inert until query.begin(cold=1) and polling.
 * This declaration does not establish physical cold-start ownership. */
int r10_sd_wire_attach(r10_sd_wire *,const r10_sd_bus *,r10_sd_query_io *);
#endif
