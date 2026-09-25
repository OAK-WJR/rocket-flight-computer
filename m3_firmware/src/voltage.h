#ifndef M3_VOLTAGE_H
#define M3_VOLTAGE_H
#include <stdint.h>
typedef struct {
    uint32_t status, error, hal_error, init_error, valid;
    uint32_t cal, ref, logic, v3, vdda_mv, logic_mv, v3_mv, sample_ms;
    uint32_t pmcr, ccr, pcsel, cfgr, cr;
} BenchADC;
void bench_adc_sample(BenchADC *out);
#endif
