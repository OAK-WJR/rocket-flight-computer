#ifndef M3_POWER_STATUS_H
#define M3_POWER_STATUS_H
#include <stdint.h>
/* GPIOD: battery FLT PD0, mux ST PD1, camera FLT PD4, USB FLT PD6. */
#define POWER_PIN_MASK 0x53U
#define POWER_FAULT_MASK 0x51U
#define POWER_MUX_MASK 0x02U
enum { POWER_CONFIGURED=1, POWER_CONFIG_VALID=2, POWER_TICK_SEEN=4,
       POWER_IRQ_SEEN=8, POWER_GAP_SEEN=16, POWER_CONFIG_ERROR=32,
       POWER_COUNT_SATURATED=64 };
/* Protocol v8 words153..159; history low16=seen low, high16=seen high. */
typedef struct {
    uint32_t flags,gpio,history,sampled_ms,last_event_ms,irq_count,max_gap_ms;
} BenchPowerStatus;
typedef struct { BenchPowerStatus r; uint32_t initialized; } PowerStatus;
void power_status_init(PowerStatus *,uint32_t now,uint32_t gpio,int config_ok);
void power_status_observe(PowerStatus *,uint32_t now,uint32_t gpio,
                          uint32_t pending,int periodic,int config_ok);
void bench_power_initialize(void);
void bench_power_tick(void);
void bench_power_status(BenchPowerStatus *);
#endif
