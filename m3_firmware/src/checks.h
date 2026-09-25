#ifndef M3_CHECKS_H
#define M3_CHECKS_H
#include <stddef.h>
#include <stdint.h>
uint32_t bench_crc32(const uint8_t *data, size_t size);
uint8_t bench_prom_crc4(const uint16_t prom[8]);
int bench_prom_nonempty(const uint16_t prom[8]);
int bench_voltages(uint32_t cal, uint32_t ref, uint32_t logic, uint32_t v3,
                   uint32_t *vdda_mv, uint32_t *logic_mv, uint32_t *v3_mv);
int bench_ms5611(const uint16_t prom[8], uint32_t d1, uint32_t d2,
                 int32_t *pressure_pa, int32_t *temp_centic);
#endif
