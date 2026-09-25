#ifndef M3_USB_H
#define M3_USB_H
#include <stddef.h>
#include <stdint.h>
enum {USB_DISABLED,USB_CLOCK_INIT,USB_WAIT_VBUS,USB_ATTACHED,USB_MOUNTED,USB_SUSPENDED,USB_ERROR};
enum {USB_E_NONE,USB_E_HSE,USB_E_PLL_BUSY,USB_E_PLL_CONFIG,USB_E_FREQUENCY,USB_E_STACK,USB_E_CLOCK_LOST};
typedef struct {
    uint32_t state,error,flags,clock_hz,attaches,detaches,mounts,suspends;
    uint32_t rx_bytes,tx_bytes,requests,bad_requests,partial_timeouts,last_request,read_errors,max_gap_ms;
    uint32_t rcc_cr,pllckselr,pll3divr,d2ccip2r,gpiod_idr,gccfg,dctl,reserved;
} BenchUSB;
void bench_usb_initialize(void);
void bench_usb_task(void);
void bench_usb_status(BenchUSB *);
unsigned bench_usb_snapshot(void *,uint8_t *,uint32_t,uint32_t);
int bench_storage_usb_read(uint32_t,uint8_t *,size_t);
#endif
