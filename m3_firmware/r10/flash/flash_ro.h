#ifndef R10_FLASH_RO_H
#define R10_FLASH_RO_H
#include <stdint.h>
enum { FRO_ERROR=-1,FRO_OK=0,FRO_BUSY=1 };
enum { FRO_SR1,FRO_SR2,FRO_SR3,FRO_ID_A,FRO_SFDP,FRO_QUAD_ID,FRO_ID_B,FRO_SR1_AFTER,FRO_COMMANDS };
enum { FRO_OFF,FRO_INITIALIZING,FRO_INIT_CONFIRM,FRO_POWER_GUARD,FRO_START,
       FRO_READING,FRO_CONFIRM,FRO_WAIT,FRO_RETRY,FRO_STOPPED };
enum { FRO_NO_ERROR,FRO_ADAPTER,FRO_INIT_ERROR,FRO_CONFIG,FRO_START_ERROR,FRO_READ_ERROR,
       FRO_TIMEOUT,FRO_COUNT,FRO_DEVICE_BUSY,FRO_SUSPENDED,FRO_IDENTITY,FRO_SFDP_SIGNATURE,
       FRO_QUAD_DISABLED,FRO_QUAD_IDENTITY,FRO_UNSTABLE_ID,FRO_STATUS_CHANGED,FRO_TIMEBASE,FRO_CLEANUP };
enum { FRO_INIT_MS=500,FRO_TRANSFER_MS=20,FRO_BATCH_MS=150,FRO_RETRY_MS=1000,
       FRO_PERIOD_MS=1000,FRO_FRESH_MS=3000,FRO_BYTES_MAX=8,FRO_ALL=255 };
typedef struct {
    uint8_t opcode,address_lines,address_bits,alternate_lines,alternate_bits,alternate_value;
    uint8_t dummy_cycles,data_lines,length;
} r10_flash_ro_command;
const r10_flash_ro_command *r10_flash_ro_descriptor(unsigned command);
typedef struct {
    void *context;
    int (*initialize)(void *,uint32_t now_ms,uint32_t *nominal_hz,uint32_t *detail);
    int (*start)(void *,unsigned command,uint32_t *detail);
    /* A bounded call may return partial bytes even on BUSY or ERROR. Never
     * write beyond capacity; capacity0 is used while waiting for completion. */
    int (*poll)(void *,uint8_t *,uint32_t capacity,uint32_t *received,uint32_t *detail);
    /* OK certifies a quiescent interface. It does not reset/wake the flash. */
    int (*cancel)(void *,uint32_t *detail);
} r10_flash_ro_io;
typedef struct {
    uint32_t state,error,last_error,detail,last_error_detail,cleanup_error,cleanup_detail;
    uint32_t stage_at,batch_at,observed_ms,last_good_ms;
    uint32_t nominal_hz,sample_nominal_hz,samples,failures,retries,command,completed_mask,io_count;
    uint32_t command_ms[FRO_COMMANDS],sample_command_ms[FRO_COMMANDS];
    uint8_t raw[FRO_COMMANDS][FRO_BYTES_MAX],raw_count[FRO_COMMANDS];
    uint8_t sample_raw[FRO_COMMANDS][FRO_BYTES_MAX],has_sample,valid;
    r10_flash_ro_io io;
} r10_flash_ro;
void r10_flash_ro_begin(r10_flash_ro *,const r10_flash_ro_io *,uint32_t now_ms);
void r10_flash_ro_poll(r10_flash_ro *,uint32_t now_ms);
int r10_flash_ro_fresh(const r10_flash_ro *,uint32_t now_ms);
#endif
