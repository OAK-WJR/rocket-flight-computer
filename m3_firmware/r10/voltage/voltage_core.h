#ifndef R10_VOLTAGE_CORE_H
#define R10_VOLTAGE_CORE_H
#include <stdint.h>

/* Bench measurement only. The adapter must perform one bounded step per call;
 * BUSY is not a permission to spin. No load/control output belongs here. */
enum { R10_VOLTAGE_IO_ERROR=-1, R10_VOLTAGE_IO_OK=0, R10_VOLTAGE_IO_BUSY=1 };
enum {
    R10_VOLTAGE_REF_BEFORE, R10_VOLTAGE_LOGIC, R10_VOLTAGE_CAMERA,
    R10_VOLTAGE_VBAT, R10_VOLTAGE_REF_AFTER, R10_VOLTAGE_CHANNELS
};
enum {
    R10_VOLTAGE_OFF, R10_VOLTAGE_INITIALIZING, R10_VOLTAGE_START,
    R10_VOLTAGE_READING, R10_VOLTAGE_CONFIRM, R10_VOLTAGE_WAIT, R10_VOLTAGE_RETRY,
    R10_VOLTAGE_STOPPED
};
enum {
    R10_VOLTAGE_OK, R10_VOLTAGE_ADAPTER, R10_VOLTAGE_INIT,
    R10_VOLTAGE_CONFIG, R10_VOLTAGE_CALIBRATION, R10_VOLTAGE_START_ERROR,
    R10_VOLTAGE_READ_ERROR, R10_VOLTAGE_TIMEOUT, R10_VOLTAGE_RAW_RANGE,
    R10_VOLTAGE_REFERENCE, R10_VOLTAGE_REFERENCE_DRIFT,
    R10_VOLTAGE_SATURATED, R10_VOLTAGE_TIMEBASE, R10_VOLTAGE_CLEANUP
};
enum {
    R10_VOLTAGE_INIT_MS=500, R10_VOLTAGE_CONVERSION_MS=20,
    R10_VOLTAGE_BATCH_MS=100, R10_VOLTAGE_PERIOD_MS=250,
    R10_VOLTAGE_FRESH_MS=1000, R10_VOLTAGE_RETRY_MS=1000,
    R10_VOLTAGE_BITS=10, R10_VOLTAGE_MAX=1023,
    R10_VOLTAGE_ALL=(1u<<R10_VOLTAGE_CHANNELS)-1u
};
typedef struct {
    uint32_t revision, calibration, sample_bits, adc12_hz, adc3_hz;
} r10_voltage_config;
typedef struct {
    uint32_t vdda_mv, logic_mv, camera_mv, v3v3_coarse_mv;
    uint32_t reference_drift_permille;
} r10_voltage_values;
typedef struct {
    void *context;
    /* Return OK only once both ADCs are calibrated/ready. Repeated BUSY calls
     * continue that initialization, rather than restarting calibration. */
    int (*initialize)(void *, uint32_t now_ms, r10_voltage_config *, uint32_t *detail);
    /* Slots map to ADC3/19, ADC1/3, ADC1/5, ADC3/17, ADC3/19, in that order.
     * start must return OK or ERROR, never BUSY. One conversion at a time. */
    int (*start)(void *, unsigned slot, uint32_t *detail);
    int (*poll)(void *, uint32_t *raw, uint32_t *detail);
    /* OK certifies no conversion remains active and initialization can restart.
     * Any other result latches STOPPED: no automatic retry of an unsafe port. */
    int (*cancel)(void *, uint32_t *detail);
} r10_voltage_io;
typedef struct {
    uint32_t state, error, last_error, detail, last_error_detail;
    uint32_t cleanup_error, cleanup_detail;
    uint32_t stage_at, batch_at, observed_ms, last_good_ms;
    uint32_t samples, failures, retries, slot, raw_mask;
    uint32_t raw[R10_VOLTAGE_CHANNELS], raw_ms[R10_VOLTAGE_CHANNELS];
    uint32_t sample_raw[R10_VOLTAGE_CHANNELS], sample_ms[R10_VOLTAGE_CHANNELS];
    r10_voltage_config config, sample_config;
    r10_voltage_values values;
    uint8_t has_sample, valid;
    r10_voltage_io io;
} r10_voltage;

/* Nominal conversions, not rail pass/fail or a complete uncertainty budget.
 * VBAT/4 has a specified +/-10% ratio error; its value is deliberately coarse.
 * R60/R61 and R104/R105 both divide by 11 nominally. */
unsigned r10_voltage_compute(const r10_voltage_config *,
                            const uint32_t raw[R10_VOLTAGE_CHANNELS],
                            r10_voltage_values *);
void r10_voltage_begin(r10_voltage *, const r10_voltage_io *, uint32_t now_ms);
void r10_voltage_poll(r10_voltage *, uint32_t now_ms);
int r10_voltage_fresh(const r10_voltage *, uint32_t now_ms);
#endif
