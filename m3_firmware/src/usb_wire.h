#ifndef M3_USB_WIRE_H
#define M3_USB_WIRE_H
#include <stddef.h>
#include <stdint.h>
#define USB_REQUEST_BYTES 24U
#define USB_PAYLOAD_MAX 1024U
#define USB_RESPONSE_MAX (24U + USB_PAYLOAD_MAX + 4U)
enum { USB_OP_SNAPSHOT=1, USB_OP_FLASH=2 };
enum { USB_REPLY_OK=0, USB_REPLY_BAD_REQUEST=1, USB_REPLY_BUSY=2, USB_REPLY_READ_ERROR=3 };
typedef unsigned (*UsbRead)(void *,uint8_t *,uint32_t,uint32_t);
typedef struct {
    void *ctx;
    UsbRead snapshot,flash;
    uint8_t rx[USB_REQUEST_BYTES],tx[USB_RESPONSE_MAX];
    uint32_t rx_used,tx_size,tx_sent,last_byte_ms;
    uint32_t requests,bad_requests,partial_timeouts,last_request,read_errors;
} UsbWire;
void usb_wire_init(UsbWire *,void *,UsbRead,UsbRead);
void usb_wire_reset(UsbWire *);
void usb_wire_tick(UsbWire *,uint32_t);
int usb_wire_feed(UsbWire *,uint8_t,uint32_t);
const uint8_t *usb_wire_pending(const UsbWire *,uint32_t *);
int usb_wire_sent(UsbWire *,uint32_t);
#endif
