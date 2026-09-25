#ifdef M3_USB
#include "stm32h7xx_hal.h"
#include "usb.h"
#include "usb_wire.h"
#include "tusb.h"
#include <string.h>
_Static_assert(sizeof(BenchUSB)==24*4,"USB mailbox layout");
static BenchUSB status;
static UsbWire wire;
static uint32_t ready,active,inside,last_service,high_since,high_pending;
uint32_t tusb_time_millis_api(void){return HAL_GetTick();}
void OTG_FS_IRQHandler(void){tusb_int_handler(0,true);}
static unsigned flash_read(void *ctx,uint8_t *out,uint32_t address,uint32_t n){
    (void)ctx;int rc=bench_storage_usb_read(address,out,n);
    return rc==0?USB_REPLY_OK:rc==1?USB_REPLY_BUSY:USB_REPLY_READ_ERROR;
}
static void hardware_record(void){
    status.rcc_cr=RCC->CR;status.pllckselr=RCC->PLLCKSELR;
    status.pll3divr=RCC->PLL3DIVR;status.d2ccip2r=RCC->D2CCIP2R;
    status.gpiod_idr=GPIOD->IDR;
    if(ready){
        status.gccfg=USB2_OTG_FS->GCCFG;
        USB_OTG_DeviceTypeDef *d=(USB_OTG_DeviceTypeDef *)(USB2_OTG_FS_PERIPH_BASE+USB_OTG_DEVICE_BASE);
        status.dctl=d->DCTL;
    }
}
void bench_usb_status(BenchUSB *out){
    status.requests=wire.requests;status.bad_requests=wire.bad_requests;
    status.partial_timeouts=wire.partial_timeouts;status.last_request=wire.last_request;
    status.read_errors=wire.read_errors;hardware_record();*out=status;
}
static void failed(unsigned e){hardware_record();status.error=e;status.state=USB_ERROR;status.flags=0;ready=0;}
void bench_usb_initialize(void){
    ready=active=inside=high_pending=0;
    memset(&status,0,sizeof(status));status.state=USB_CLOCK_INIT;
    usb_wire_init(&wire,NULL,bench_usb_snapshot,flash_read);
    __HAL_RCC_GPIOA_CLK_ENABLE();__HAL_RCC_GPIOD_CLK_ENABLE();
    GPIO_InitTypeDef g={0};g.Pin=GPIO_PIN_15;g.Mode=GPIO_MODE_INPUT;g.Pull=GPIO_NOPULL;HAL_GPIO_Init(GPIOD,&g);
    if(!(RCC->CR&RCC_CR_HSERDY)){failed(USB_E_HSE);return;}
    /* All current acquisition kernels stay on HSI/CLKP. No running PLL may
     * be silently reparented when selecting the shared PLL input source. */
    if(RCC->CR&(RCC_CR_PLL1ON|RCC_CR_PLL2ON|RCC_CR_PLL3ON)){failed(USB_E_PLL_BUSY);return;}
    __HAL_RCC_PLL_PLLSOURCE_CONFIG(RCC_PLLSOURCE_HSE);
    RCC_PeriphCLKInitTypeDef clk={0};clk.PeriphClockSelection=RCC_PERIPHCLK_USB;
    clk.UsbClockSelection=RCC_USBCLKSOURCE_PLL3;
    clk.PLL3.PLL3M=25;clk.PLL3.PLL3N=192;clk.PLL3.PLL3P=2;clk.PLL3.PLL3Q=4;clk.PLL3.PLL3R=2;
    clk.PLL3.PLL3RGE=RCC_PLL3VCIRANGE_0;clk.PLL3.PLL3VCOSEL=RCC_PLL3VCOMEDIUM;clk.PLL3.PLL3FRACN=0;
    if(HAL_RCCEx_PeriphCLKConfig(&clk)!=HAL_OK){failed(USB_E_PLL_CONFIG);return;}
    status.clock_hz=HAL_RCCEx_GetPeriphCLKFreq(RCC_PERIPHCLK_USB);
    if(status.clock_hz!=48000000U || SystemCoreClock!=64000000U){failed(USB_E_FREQUENCY);return;}
    g.Pin=GPIO_PIN_11|GPIO_PIN_12;g.Mode=GPIO_MODE_AF_PP;g.Pull=GPIO_NOPULL;
    g.Speed=GPIO_SPEED_FREQ_HIGH;g.Alternate=GPIO_AF10_OTG2_FS;HAL_GPIO_Init(GPIOA,&g);
    HAL_PWREx_EnableUSBVoltageDetector();
    __HAL_RCC_USB2_OTG_FS_CLK_ENABLE();
    __HAL_RCC_USB2_OTG_FS_FORCE_RESET();__HAL_RCC_USB2_OTG_FS_RELEASE_RESET();
    HAL_NVIC_SetPriority(OTG_FS_IRQn,6,0);
    ready=1;status.flags=1;status.state=USB_WAIT_VBUS;last_service=HAL_GetTick();
}
void tud_mount_cb(void){status.mounts++;status.state=USB_MOUNTED;}
void tud_umount_cb(void){status.state=USB_ATTACHED;usb_wire_reset(&wire);}
void tud_suspend_cb(bool remote_wakeup){(void)remote_wakeup;status.suspends++;status.state=USB_SUSPENDED;}
void tud_resume_cb(void){status.state=tud_mounted()?USB_MOUNTED:USB_ATTACHED;}
void tud_cdc_line_state_cb(uint8_t itf,bool dtr,bool rts){
    (void)rts;
    if(itf==0 && !dtr){
        usb_wire_reset(&wire);tud_cdc_read_flush();tud_cdc_write_clear();
    }
}
void bench_usb_task(void){
#ifdef M3_GNSS
    /* GNSS keeps receiving even with no USB cable or a failed USB clock. */
    extern void bench_gnss_task(void);bench_gnss_task();
#endif
    if(!ready || inside)return;
    inside=1;uint32_t now=HAL_GetTick(),gap=now-last_service;last_service=now;
    if((RCC->CR&(RCC_CR_HSERDY|RCC_CR_PLL3RDY))!=(RCC_CR_HSERDY|RCC_CR_PLL3RDY)){
        if(active){tud_disconnect();tud_deinit(0);active=0;}
        usb_wire_reset(&wire);failed(USB_E_CLOCK_LOST);inside=0;return;
    }
    if(gap>status.max_gap_ms)status.max_gap_ms=gap;
    unsigned vbus=HAL_GPIO_ReadPin(GPIOD,GPIO_PIN_15)==GPIO_PIN_SET;
    status.flags=1U|(vbus?2U:0U);
    if(!vbus){
        high_pending=0;
        if(active){tud_disconnect();tud_deinit(0);active=0;status.detaches++;usb_wire_reset(&wire);}
        status.state=USB_WAIT_VBUS;inside=0;return;
    }
    if(!active){
        if(!high_pending){high_pending=1;high_since=now;}
        if((uint32_t)(now-high_since)<20U){inside=0;return;}
        const tud_configure_dwc2_t cfg={.bm_double_buffered=0,.vbus_sensing=false};
        const tusb_rhport_init_t rh={.role=TUSB_ROLE_DEVICE,.speed=TUSB_SPEED_FULL};
        /* dcd_init connects internally, so call it only after stable VBUS. */
        if(!tud_configure(0,TUD_CFGID_DWC2,&cfg)||!tusb_init(0,&rh)){
            if(tud_inited()){tud_disconnect();tud_deinit(0);}
            failed(USB_E_STACK);inside=0;return;
        }
        active=1;status.attaches++;status.state=USB_ATTACHED;
    }
    tud_task_ext(0,false);
    status.flags|=tud_mounted()?4U:0U;status.flags|=tud_cdc_connected()?8U:0U;
    usb_wire_tick(&wire,now);
    if(tud_mounted() && !tud_suspended() && tud_cdc_connected()){
        for(unsigned budget=0;budget<64 && !wire.tx_size && tud_cdc_available();budget++){
            uint8_t byte;
            if(tud_cdc_read(&byte,1)!=1)break;
            status.rx_bytes++;usb_wire_feed(&wire,byte,now);
        }
        uint32_t n=0;const uint8_t *p=usb_wire_pending(&wire,&n);
        if(n){
            uint32_t accepted=tud_cdc_write(p,n);usb_wire_sent(&wire,accepted);
            status.tx_bytes+=accepted;tud_cdc_write_flush();
        }
    }
    inside=0;
}
/* Service deferred USB work while the existing slow bench sensors wait.
 * Interrupt handlers only dispatch USB events, never sample sensors/flash. */
void HAL_Delay(uint32_t ms){
    uint32_t begin=HAL_GetTick();
    if(ms<HAL_MAX_DELAY)ms++;
    while((uint32_t)(HAL_GetTick()-begin)<ms){bench_usb_task();__NOP();}
}
#endif
