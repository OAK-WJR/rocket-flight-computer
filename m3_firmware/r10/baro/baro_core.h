#ifndef R10_BARO_CORE_H
#define R10_BARO_CORE_H
#include "baro_io.h"
enum { R10_BARO_OFF,R10_BARO_POWER_WAIT,R10_BARO_RESET_WAIT,R10_BARO_PROM,
       R10_BARO_WAIT_D1,R10_BARO_WAIT_D2,R10_BARO_READY,R10_BARO_ERROR,R10_BARO_COMMIT };
enum { R10_BARO_OK,R10_BARO_PORT,R10_BARO_RESET,R10_BARO_PROM_READ,
       R10_BARO_PROM_EMPTY,R10_BARO_PROM_CRC,R10_BARO_CONVERT_D1,R10_BARO_READ_D1,
       R10_BARO_CONVERT_D2,R10_BARO_READ_D2,R10_BARO_ADC_INVALID,R10_BARO_RESULT_RANGE,R10_BARO_PAIR_STALE };
enum { R10_BARO_POWER_MS=10,R10_BARO_RESET_MS=5,R10_BARO_CONVERT_MS=12,
       R10_BARO_FRESH_MS=250,R10_BARO_RETRY_MS=1000 };
typedef struct {
    uint32_t state,error,stage_at,last_good_ms,samples,bus_errors;
    uint32_t nominal_bus_hz,bus_detail,retry_count,last_error;
    uint32_t d1,d2,d1_ms,d2_ms,sample_d1,sample_d2,sample_d1_ms,sample_d2_ms;
    uint32_t acquisition_started_ms,sample_started_ms;
    int32_t pressure_pa,temp_centic,candidate_pressure_pa,candidate_temp_centic;
    uint16_t prom[8],sample_prom[8];
    uint8_t prom_mask,prom_index,crc_calculated,crc_stored,prom_valid;
    uint8_t valid_mask,has_sample,bus_failed,wait_pending;
    r10_baro_io io;
} r10_baro;
void r10_baro_begin(r10_baro *,const r10_baro_io *,uint32_t now_ms);
void r10_baro_poll(r10_baro *,uint32_t now_ms);
#endif
