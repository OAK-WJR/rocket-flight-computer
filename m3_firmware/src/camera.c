/* Ordinary camera device-information transaction. Protocol facts and limits:
 * research/CAMERA_UART.md. No button emulation, settings writes or recording
 * commands. A camera can auto-record: power remains ON after an enabled test.
 */
#include "camera.h"
#include <string.h>

uint8_t camera_crc8(const uint8_t *data, size_t size) {
    uint8_t crc = 0;
    for (size_t n = 0; n < size; ++n) {
        crc ^= data[n];
        for (unsigned b = 0; b < 8; ++b)
            crc = (uint8_t)((crc << 1) ^ ((crc & 0x80U) ? 0xd5U : 0U));
    }
    return crc;
}

typedef struct { uint32_t last, same; } ClockGuard;
static int alive(const CameraIO *io, ClockGuard *g, CameraResult *r, uint32_t *now) {
    *now = io->now(io->ctx);
    if (*now != g->last) { g->last = *now; g->same = 0; }
    else if (++g->same >= 1000000U) { r->error = CAM_TICK_STALLED; return 0; }
    return 1;
}
static void raw_byte(CameraResult *r, uint8_t b) {
    if (r->raw_length < 32) {
        unsigned n = r->raw_length++;
        r->raw[n / 4] |= (uint32_t)b << (8U * (n % 4));
    }
}

void camera_query(const CameraIO *io, int enabled, CameraResult *r) {
    uint32_t now;
    uint8_t packet[5] = {0}, byte = 0;
    unsigned length = 0;
    const uint8_t request[] = {0xcc, 0x00, 0x60};
    memset(r, 0, sizeof(*r));
    r->mode = enabled ? 1U : 0U;
    r->start_ms = now = io->now(io->ctx);
    ClockGuard guard = {now, 0};
    /* Lower OE before any change to the camera supply. */
    r->oe_readback = (uint32_t)io->oe(io->ctx, 0);
    r->power_readback = (uint32_t)io->power(io->ctx, 0);
    if (r->oe_readback || r->power_readback) { r->error = CAM_PIN_READBACK; goto done; }
    if (!enabled) goto done; /* NOT_TESTED: no UART setup or camera power-on */
    r->status = 1;
    r->error = (uint32_t)io->init(io->ctx, r);
    if (r->error) goto done;
    r->power_readback = (uint32_t)io->power(io->ctx, 1);
    if (r->power_readback != 1) { r->error = CAM_PIN_READBACK; goto done; }
    uint32_t power_at = io->now(io->ctx);
    do {
        if (!alive(io, &guard, r, &now)) goto done;
    } while ((uint32_t)(now - power_at) < CAM_BOOT_MS);
    r->oe_readback = (uint32_t)io->oe(io->ctx, 1);
    if (r->oe_readback != 1) { r->error = CAM_PIN_READBACK; goto done; }
    /* Drain pre-request traffic with a byte/time limit. Never accept a stale
     * device-info frame as the response to our new query. */
    uint32_t drain_at = io->now(io->ctx);
    for (;;) {
        int got = io->rx(io->ctx, &byte, r);
        if (got < 0) { r->error = CAM_UART_ERROR; goto done; }
        if (!got) break;
        if (++r->discarded >= CAM_MAX_RX) { r->error = CAM_RX_LIMIT; goto done; }
        if (!alive(io, &guard, r, &now)) goto done;
        if ((uint32_t)(now - drain_at) >= CAM_TX_MS) { r->error = CAM_RX_LIMIT; goto done; }
    }
    r->query_ms = io->now(io->ctx);
    while (r->tx_count < sizeof(request)) {
        if (!alive(io, &guard, r, &now)) goto done;
        if ((uint32_t)(now-r->query_ms) >= CAM_TX_MS) { r->error = CAM_TX_TIMEOUT; goto done; }
        int sent = io->tx(io->ctx, request[r->tx_count], r);
        if (sent < 0) { r->error = CAM_UART_ERROR; goto done; }
        if (sent) ++r->tx_count;
    }
    for (;;) {
        if (!alive(io, &guard, r, &now)) goto done;
        if ((uint32_t)(now-r->query_ms) >= CAM_TX_MS) { r->error = CAM_TX_TIMEOUT; goto done; }
        int complete = io->tx_done(io->ctx, r);
        if (complete < 0) { r->error = CAM_UART_ERROR; goto done; }
        if (complete) break;
    }
    uint32_t reply_at = io->now(io->ctx);
    for (;;) {
        if (!alive(io, &guard, r, &now)) goto done;
        if ((uint32_t)(now-reply_at) >= CAM_REPLY_MS) {
            r->error = r->crc_errors ? CAM_BAD_CRC : CAM_RX_TIMEOUT; goto done;
        }
        int got = io->rx(io->ctx, &byte, r);
        if (got < 0) { r->error = CAM_UART_ERROR; goto done; }
        if (!got) continue;
        ++r->rx_count; raw_byte(r, byte);
        if (!length && byte != 0xcc) ++r->discarded;
        else {
            packet[length++] = byte;
            if (length == sizeof(packet)) {
                if (camera_crc8(packet, 4) == packet[4]) {
                    for (unsigned n = 0; n < sizeof(packet); ++n)
                        r->packet[n/4] |= (uint32_t)packet[n] << (8U*(n%4));
                    r->valid_length = 5;
                    r->protocol_version = packet[1];
                    r->features = packet[2] | ((uint32_t)packet[3] << 8);
                    if (packet[1] != 1) r->error = CAM_VERSION;
                    goto done;
                }
                ++r->crc_errors;
                /* Retain a later header already received inside this bad
                 * candidate; a noise byte must not consume the next frame. */
                unsigned next = 1;
                while (next < sizeof(packet) && packet[next] != 0xcc) ++next;
                r->discarded += next;
                length = (unsigned)sizeof(packet) - next;
                memmove(packet, packet + next, length);
            }
        }
        if (r->rx_count >= CAM_MAX_RX) { r->error = CAM_RX_LIMIT; goto done; }
    }
done:
    /* End communication on every path. Deliberately do NOT cut camera power:
     * this firmware cannot know whether its SD card is recording/flushing. */
    r->oe_readback = (uint32_t)io->oe(io->ctx, 0);
    if (r->oe_readback && !r->error) r->error = CAM_PIN_READBACK;
    io->snapshot(io->ctx, r);
    r->finished_ms = io->now(io->ctx);
    r->status = r->error ? 3U : (enabled ? 2U : 0U);
}
