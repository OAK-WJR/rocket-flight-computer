/* Bounded, read-only request protocol. USB packets may split anywhere.
 * CRC detects corruption; it is not authentication. No address/write commands.
 */
#include "usb_wire.h"
#include "checks.h"
#include <string.h>
static uint32_t get32(const uint8_t *p){return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put32(uint8_t *p,uint32_t v){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(v>>(i*8));}
void usb_wire_init(UsbWire *w,void *ctx,UsbRead snapshot,UsbRead flash){
    memset(w,0,sizeof(*w));w->ctx=ctx;w->snapshot=snapshot;w->flash=flash;
}
void usb_wire_reset(UsbWire *w){w->rx_used=w->tx_size=w->tx_sent=0;}
void usb_wire_tick(UsbWire *w,uint32_t now){
    if(w->rx_used && (uint32_t)(now-w->last_byte_ms)>500U){w->rx_used=0;w->partial_timeouts++;}
}
int usb_wire_feed(UsbWire *w,uint8_t b,uint32_t now){
    if(w->tx_size)return 0;
    usb_wire_tick(w,now);w->last_byte_ms=now;w->rx[w->rx_used++]=b;
    if(w->rx_used<USB_REQUEST_BYTES)return 1;
    if(memcmp(w->rx,"M3RQ",4)||get32(w->rx+20)!=bench_crc32(w->rx,20)){
        w->bad_requests++;memmove(w->rx,w->rx+1,USB_REQUEST_BYTES-1);w->rx_used--;return 1;
    }
    uint32_t version=(uint32_t)w->rx[4]|(uint32_t)w->rx[5]<<8;
    uint32_t op=(uint32_t)w->rx[6]|(uint32_t)w->rx[7]<<8;
    uint32_t request=get32(w->rx+8),address=get32(w->rx+12),length=get32(w->rx+16);
    unsigned status=USB_REPLY_BAD_REQUEST;
    w->requests++;w->last_request=request;
    if(version==1 && op==USB_OP_SNAPSHOT && address==0 && length==USB_PAYLOAD_MAX && w->snapshot)
        status=w->snapshot(w->ctx,w->tx+24,address,length);
    else if(version==1 && op==USB_OP_FLASH && length && length<=USB_PAYLOAD_MAX &&
            address<=0x1000000U && length<=0x1000000U-address && w->flash)
        status=w->flash(w->ctx,w->tx+24,address,length);
    if(status>USB_REPLY_READ_ERROR)status=USB_REPLY_READ_ERROR;
    if(status==USB_REPLY_BAD_REQUEST)w->bad_requests++;
    if(status==USB_REPLY_READ_ERROR)w->read_errors++;
    if(status!=USB_REPLY_OK)length=0;
    memcpy(w->tx,"M3RS",4);w->tx[4]=1;w->tx[5]=0;w->tx[6]=(uint8_t)status;w->tx[7]=0;
    put32(w->tx+8,request);put32(w->tx+12,address);put32(w->tx+16,length);put32(w->tx+20,op);
    put32(w->tx+24+length,bench_crc32(w->tx,24+length));
    w->rx_used=0;w->tx_sent=0;w->tx_size=28+length;return 1;
}
const uint8_t *usb_wire_pending(const UsbWire *w,uint32_t *n){
    *n=w->tx_size-w->tx_sent;return w->tx+w->tx_sent;
}
int usb_wire_sent(UsbWire *w,uint32_t n){
    if(n>w->tx_size-w->tx_sent)return 0;
    w->tx_sent+=n;if(w->tx_sent==w->tx_size)w->tx_sent=w->tx_size=0;return 1;
}
