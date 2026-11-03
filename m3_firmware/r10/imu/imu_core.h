#ifndef R10_IMU_CORE_H
#define R10_IMU_CORE_H
#include <stddef.h>
#include <stdint.h>
#include "ism6hg256x_reg.h"

/* ISM6HG256X register driver only. No attitude/control/actuator functions. */
enum { R10_IMU_OFF, R10_IMU_BOOT_WAIT, R10_IMU_RESET_WAIT,
       R10_IMU_WAIT_DATA, R10_IMU_READY, R10_IMU_STALE, R10_IMU_ERROR };
enum { R10_IMU_OK, R10_IMU_PORT, R10_IMU_ID, R10_IMU_RESET,
       R10_IMU_CONFIG_WRITE, R10_IMU_CONFIG_READ, R10_IMU_CONFIG_MISMATCH,
       R10_IMU_STATUS_READ, R10_IMU_DATA_READ, R10_IMU_NO_DATA };
enum { R10_IMU_FRESH_MS=250, R10_IMU_BOOT_MS=35, R10_IMU_RETRY_MS=1000,
       R10_IMU_SETTLE_MS=100 };

typedef struct {
    void *handle;
    int (*initialize)(void *, uint32_t *nominal_hz, uint32_t *detail);
    /* Must finish within a finite poll/time budget, even if a tick stops. */
    int (*exchange)(void *, const uint8_t *, uint8_t *, size_t, uint32_t *detail);
} r10_imu_io;

typedef struct {
    uint32_t state, error, stage_at, last_good_ms, samples, bus_errors;
    uint32_t nominal_bus_hz, bus_detail, retry_count, endpoint_mask, last_error, stale_since;
    uint8_t who, status_reg, valid_mask, config[8], bus_failed, has_sample;
    /* gyro XYZ, low-g XYZ, high-g XYZ, temperature: native little-endian counts.
     * No roll-axis mapping, calibration or sample-synchronization claim. */
    int16_t raw[10];
    r10_imu_io io;
    stmdev_ctx_t sensor;
} r10_imu;

void r10_imu_begin(r10_imu *, const r10_imu_io *, uint32_t now_ms);
void r10_imu_poll(r10_imu *, uint32_t now_ms);
#endif
