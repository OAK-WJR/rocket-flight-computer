/* Raw, decimated bench observations; no attitude estimation or control. */
#ifndef M3_BENCH_IMU_H
#define M3_BENCH_IMU_H
#include <stdint.h>
#include <stddef.h>

enum ImuError {
    IMU_OK, IMU_CLOCK, IMU_SPI_INIT, IMU_TRANSFER, IMU_IDENTITY,
    IMU_RESET, IMU_IREG_TIMEOUT, IMU_CONFIG, IMU_READY_TIMEOUT,
    IMU_UPDATE_DURING_READ, IMU_READ_TOO_SLOW, IMU_TICK_STALLED
};
enum { IMU_RAW_COMPLETE=1U<<16, IMU_CONFIG_VERIFIED=1U<<17,
       IMU_INITIALIZED=1U<<18 };
typedef struct {
    uint32_t status, error, init_error, io_error;
    uint32_t started_ms, sampled_ms, finished_ms, config, evidence, history;
    uint32_t raw[4]; /* 14 wire bytes, then two zero padding bytes */
    uint32_t bus_hz;
} BenchIMU;
_Static_assert(sizeof(BenchIMU)==60, "Protocol v4 IMU result is 15 words");

typedef struct {
    void *ctx;
    uint32_t (*now)(void *);
    void (*delay_ms)(void *, uint32_t);
    int (*initialize)(void *, uint32_t *bus_hz, uint32_t *detail);
    /* A single CS-low transfer, including command byte; 0 means complete.
     * On failure rx is only untrusted evidence. Adapter always deasserts CS. */
    int (*transfer)(void *, const uint8_t *, uint8_t *, size_t, uint32_t *detail);
} ImuIO;
typedef struct {
    const ImuIO *io;
    uint32_t init_error, history, bus_hz, init_detail;
    int initialized;
} ImuDevice;

void imu_begin(ImuDevice *, const ImuIO *, BenchIMU *);
void imu_sample(ImuDevice *, BenchIMU *);
void bench_imu_initialize(BenchIMU *);
void bench_imu_sample(BenchIMU *);
#endif
