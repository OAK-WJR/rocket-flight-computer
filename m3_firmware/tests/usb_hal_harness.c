#include <assert.h>
#include <stdio.h>
#include "../src/usb_stm32.c"
RCC_TypeDef rr;GPIO_TypeDef ga,gd;USB_TypeDef uu;
uint32_t SystemCoreClock=64000000;
static uint32_t ms,hz=48000000;
static unsigned init_calls,deinit_calls,disconnect_calls,read_flush,write_clear;
static int pll_error,stack_error,mounted,suspended,connected,inited;
uint32_t HAL_GetTick(void){return ms;}
int HAL_GPIO_ReadPin(GPIO_TypeDef *g,uint32_t p){return !!(g->IDR&p);}
void HAL_GPIO_Init(GPIO_TypeDef *g,GPIO_InitTypeDef *p){
 assert(!p->Pull);
 if(g==GPIOD)assert(p->Pin==GPIO_PIN_15&&p->Mode==GPIO_MODE_INPUT);
 else assert(g==GPIOA&&p->Pin==(GPIO_PIN_11|GPIO_PIN_12)&&p->Alternate==10&&p->Mode==GPIO_MODE_AF_PP);
}
int HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef *p){
 assert(rr.PLLCKSELR==3&&p->UsbClockSelection==8&&p->PeriphClockSelection==4);
 assert(p->PLL3.PLL3M==25&&p->PLL3.PLL3N==192&&p->PLL3.PLL3Q==4&&p->PLL3.PLL3FRACN==0);
 assert(p->PLL3.PLL3RGE==0&&p->PLL3.PLL3VCOSEL==1);
 if(!pll_error)rr.CR|=RCC_CR_PLL3ON|RCC_CR_PLL3RDY;
 return pll_error;
}
uint32_t HAL_RCCEx_GetPeriphCLKFreq(uint32_t p){assert(p==4);return hz;}
void HAL_PWREx_EnableUSBVoltageDetector(void){}
void HAL_NVIC_SetPriority(int irq,int pre,int sub){assert(irq==101&&pre==6&&sub==0);}
void tusb_int_handler(unsigned p,bool in_isr){assert(!p&&in_isr);}
bool tud_configure(unsigned p,unsigned cfg,const void *arg){
 const tud_configure_dwc2_t *d=arg;assert(!p&&cfg==1&&!d->vbus_sensing);return !stack_error;
}
bool tusb_init(unsigned p,const tusb_rhport_init_t *arg){
 assert(!p&&arg->role==1&&arg->speed==1&&(gd.IDR&GPIO_PIN_15));init_calls++;inited=1;return !stack_error;
}
bool tud_inited(void){return inited;}
bool tud_disconnect(void){disconnect_calls++;return true;}
bool tud_deinit(unsigned p){assert(!p);deinit_calls++;inited=mounted=connected=0;return true;}
bool tud_mounted(void){return mounted;}
bool tud_suspended(void){return suspended;}
bool tud_cdc_connected(void){return connected;}
void tud_task_ext(unsigned t,bool isr){assert(!t&&!isr);}
uint32_t tud_cdc_available(void){return 0;}
uint32_t tud_cdc_read(void *p,uint32_t n){(void)p;(void)n;assert(0);return 0;}
uint32_t tud_cdc_write(const void *p,uint32_t n){(void)p;return n;}
uint32_t tud_cdc_write_flush(void){return 0;}
void tud_cdc_read_flush(void){read_flush++;}
bool tud_cdc_write_clear(void){write_clear++;return true;}
unsigned bench_usb_snapshot(void *ctx,uint8_t *p,uint32_t a,uint32_t n){(void)ctx;(void)p;(void)a;(void)n;return 2;}
int bench_storage_usb_read(uint32_t a,uint8_t *p,size_t n){(void)a;(void)p;(void)n;return 1;}
static void fresh(void){
 rr.CR=RCC_CR_HSERDY;gd.IDR=0;ms=100;pll_error=stack_error=0;SystemCoreClock=64000000;hz=48000000;
 init_calls=deinit_calls=disconnect_calls=0;inited=mounted=suspended=connected=0;
}
int main(void){
 fresh();rr.CR=0;bench_usb_initialize();assert(status.error==USB_E_HSE);bench_usb_task();assert(!init_calls);
 fresh();rr.CR|=RCC_CR_PLL1ON;bench_usb_initialize();assert(status.error==USB_E_PLL_BUSY);
 fresh();pll_error=1;bench_usb_initialize();assert(status.error==USB_E_PLL_CONFIG);
 fresh();hz=47000000;bench_usb_initialize();assert(status.error==USB_E_FREQUENCY);
 fresh();SystemCoreClock=32000000;bench_usb_initialize();assert(status.error==USB_E_FREQUENCY);
 fresh();bench_usb_initialize();bench_usb_task();ms+=1000;bench_usb_task();assert(status.state==USB_WAIT_VBUS&&!init_calls);
 gd.IDR=GPIO_PIN_15;bench_usb_task();ms+=19;bench_usb_task();assert(!init_calls);
 gd.IDR=0;bench_usb_task();gd.IDR=GPIO_PIN_15;bench_usb_task();ms+=20;bench_usb_task();assert(init_calls==1&&status.state==USB_ATTACHED);
 mounted=connected=1;tud_mount_cb();bench_usb_task();assert(status.mounts==1&&status.state==USB_MOUNTED&&status.flags==15);
 suspended=1;tud_suspend_cb(false);bench_usb_task();assert(status.state==USB_SUSPENDED&&status.suspends==1);
 suspended=0;tud_resume_cb();assert(status.state==USB_MOUNTED);
 wire.tx_size=10;wire.rx_used=4;tud_cdc_line_state_cb(0,false,false);
 assert(!wire.tx_size&&!wire.rx_used&&read_flush==1&&write_clear==1);
 gd.IDR=0;bench_usb_task();assert(disconnect_calls==1&&deinit_calls==1&&status.detaches==1&&status.state==USB_WAIT_VBUS);
 gd.IDR=GPIO_PIN_15;bench_usb_task();ms+=20;bench_usb_task();assert(init_calls==2);
 rr.CR&=~RCC_CR_HSERDY;bench_usb_task();assert(status.state==USB_ERROR&&status.error==USB_E_CLOCK_LOST&&deinit_calls==2);
 fresh();bench_usb_initialize();stack_error=1;gd.IDR=GPIO_PIN_15;bench_usb_task();ms+=20;bench_usb_task();assert(status.error==USB_E_STACK&&!init_calls);
 fresh();bench_usb_initialize();ms=0xfffffff0;gd.IDR=GPIO_PIN_15;bench_usb_task();ms=4;bench_usb_task();assert(init_calls==1);
 puts("Scripted USB clock, VBUS/debounce, suspend/DTR, detach, failures and tick-wrap PASS");return 0;
}
