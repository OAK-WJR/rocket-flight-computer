#ifndef M3_CAMERA_H
#define M3_CAMERA_H
#include <stddef.h>
#include <stdint.h>

enum {
    CAM_NONE, CAM_INIT, CAM_CLOCK, CAM_TX_TIMEOUT, CAM_RX_TIMEOUT,
    CAM_UART_ERROR, CAM_BAD_CRC, CAM_VERSION, CAM_RX_LIMIT,
    CAM_PIN_READBACK, CAM_TICK_STALLED
};
enum { CAM_BOOT_MS = 3000, CAM_REPLY_MS = 1000, CAM_TX_MS = 100, CAM_MAX_RX = 256 };

/* Exactly mailbox words 82..111. All captures are observations, not rail tests. */
typedef struct {
    uint32_t status, error, mode, start_ms, query_ms, finished_ms;
    uint32_t power_readback, oe_readback, kernel_hz, brr, isr;
    uint32_t tx_count, rx_count, discarded, crc_errors, protocol_version, features;
    uint32_t valid_length, raw_length, error_flags;
    uint32_t raw[8], packet[2];
} CameraResult;
_Static_assert(sizeof(CameraResult) == 120, "Camera mailbox ABI");

/* Nonblocking byte operations: 1=ready, 0=not ready, -1=UART error.
 * The platform initializer must leave camera power/OE low and TX idle high.
 * Only GET_DEVICE_INFO is emitted by this diagnostic, once per boot.
 */
typedef struct {
    void *ctx;
    uint32_t (*now)(void *);
    int (*init)(void *, CameraResult *);
    int (*power)(void *, int);
    int (*oe)(void *, int);
    int (*tx)(void *, uint8_t, CameraResult *);
    int (*tx_done)(void *, CameraResult *);
    int (*rx)(void *, uint8_t *, CameraResult *);
    void (*snapshot)(void *, CameraResult *);
} CameraIO;

uint8_t camera_crc8(const uint8_t *data, size_t size);
void camera_query(const CameraIO *io, int enabled, CameraResult *r);

#ifdef M3_CAMERA_UART
void bench_camera_safe_gpio(void);
void bench_camera_query(int enabled, CameraResult *result);
#endif
#endif
