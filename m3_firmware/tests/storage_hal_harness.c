#include <assert.h>
#include <stdio.h>
#include "../src/storage_stm32.c"
GPIO_TypeDef gb,gd,ge;
static uint32_t ms,clock_hz=64000000,error;
static int clock_error,init_error,cmd_error,rx_error,tx_error,map_error,readback_bad;
static unsigned afb,afd,afe,commands,reads,writes,maps;
static unsigned aborts;static int abort_error;
static QSPI_CommandTypeDef last;
uint32_t HAL_GetTick(void){return ms;}
void HAL_Delay(uint32_t t){ms+=t;}
void HAL_GPIO_WritePin(GPIO_TypeDef *p,uint16_t n,int high){if(high)p->ODR|=n;else p->ODR&=~n;}
int HAL_GPIO_ReadPin(GPIO_TypeDef *p,uint16_t n){return readback_bad?0:!!(p->ODR&n);}
void HAL_GPIO_Init(GPIO_TypeDef *p,GPIO_InitTypeDef *g){
 if(g->Mode==GPIO_MODE_AF_PP){
  assert(g->Pull==0);assert(g->Speed==GPIO_SPEED_FREQ_MEDIUM);
  if(p==GPIOB){assert(g->Alternate==(g->Pin==64?10:9));afb|=g->Pin;}
  if(p==GPIOD){assert(g->Alternate==9);afd|=g->Pin;}
  if(p==GPIOE){assert(g->Alternate==9);afe|=g->Pin;}
 }else{assert(p==GPIOB&&g->Pin==64&&(p->ODR&64));}
}
int HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef *g){
 assert(g->PeriphClockSelection==3&&g->QspiClockSelection==3&&g->CkperClockSelection==4);return clock_error;
}
uint32_t HAL_RCCEx_GetPeriphCLKFreq(uint64_t k){assert(k==RCC_PERIPHCLK_QSPI);return clock_hz;}
int HAL_QSPI_Init(QSPI_HandleTypeDef *q){
 assert(q->Instance==QUADSPI&&q->Init.ClockPrescaler==7&&q->Init.FlashSize==23);
 assert(q->Init.ChipSelectHighTime==QSPI_CS_HIGH_TIME_4_CYCLE&&q->Init.ClockMode==0&&q->Init.DualFlash==0);
 return init_error;
}
uint32_t HAL_QSPI_GetError(QSPI_HandleTypeDef *q){(void)q;return error;}
int HAL_QSPI_Abort(QSPI_HandleTypeDef *q){assert(q->Timeout==20);aborts++;return abort_error;}
void HAL_QSPI_SetTimeout(QSPI_HandleTypeDef *q,uint32_t t){assert(t==20);q->Timeout=t;}
int HAL_QSPI_Command(QSPI_HandleTypeDef *q,QSPI_CommandTypeDef *c,uint32_t timeout){
 (void)q;assert(timeout==20);commands++;last=*c;return cmd_error;
}
int HAL_QSPI_Receive(QSPI_HandleTypeDef *q,uint8_t *p,uint32_t t){(void)q;(void)p;assert(t==20);reads++;return rx_error;}
int HAL_QSPI_Transmit(QSPI_HandleTypeDef *q,uint8_t *p,uint32_t t){(void)q;(void)p;assert(t==20);writes++;return tx_error;}
int HAL_QSPI_MemoryMapped(QSPI_HandleTypeDef *q,QSPI_CommandTypeDef *c,QSPI_MemoryMappedTypeDef *m){
 (void)q;assert(c->Instruction==3&&c->AddressSize==QSPI_ADDRESS_24_BITS&&c->DataMode==QSPI_DATA_1_LINE);
 assert(!c->DummyCycles&&m->TimeOutActivation==QSPI_TIMEOUT_COUNTER_DISABLE);maps++;return map_error;
}
void bench_storage_progress(const BenchStorage *r){(void)r;}
int main(void){
 uint32_t hz,detail;uint8_t data[4096]={0};
 assert(!init(0,&hz,&detail)&&hz==8000000&&afb==68&&afd==14336&&afe==4);
 clock_hz=32000000;assert(init(0,&hz,&detail));clock_hz=64000000;
 clock_error=1;assert(init(0,&hz,&detail));clock_error=0;
 init_error=1;assert(init(0,&hz,&detail));init_error=0;
 readback_bad=1;assert(init(0,&hz,&detail));readback_bad=0;
 assert(!exchange(0,0x4b,-1,0,0,0,data,8,&detail));
 assert(last.AlternateByteMode==QSPI_ALTERNATE_BYTES_1_LINE&&last.AlternateBytesSize==QSPI_ALTERNATE_BYTES_32_BITS&&last.AlternateBytes==0);
 assert(!exchange(0,0x6b,0x123400,8,1,0,data,256,&detail));
 assert(last.Address==0x123400&&last.AddressMode==QSPI_ADDRESS_1_LINE&&last.DataMode==QSPI_DATA_4_LINES&&last.DummyCycles==8);
 assert(!exchange(0,3,0,0,0,0,data,4096,&detail));assert(last.AddressSize==QSPI_ADDRESS_24_BITS);
 unsigned calls=commands;
 for(unsigned i=0;i<256;i++) if(i!=6)assert(exchange(0,(uint8_t)i,-1,0,0,0,0,0,&detail));
 assert(commands==calls);
 assert(exchange(0,3,0xffffff,0,0,0,data,4,&detail));
 assert(exchange(0,2,1,0,0,data,0,256,&detail));assert(exchange(0,2,0,0,0,data,0,257,&detail));
#if M3_STORAGE_RECORD
 assert(!exchange(0,6,-1,0,0,0,0,0,&detail));assert(!exchange(0,2,0,0,0,data,0,256,&detail));assert(writes==1);
 assert(map(0,&detail));assert(!maps);
#else
 assert(exchange(0,6,-1,0,0,0,0,0,&detail));assert(exchange(0,2,0,0,0,data,0,256,&detail));assert(!writes);
 assert(!map(0,&detail));assert(maps==1);
#endif
 calls=reads;cmd_error=1;assert(exchange(0,3,0,0,0,0,data,4,&detail));assert(reads==calls&&detail&&gb.ODR&64);cmd_error=0;
 rx_error=1;assert(exchange(0,3,0,0,0,0,data,4,&detail));assert(detail&&gb.ODR&64);rx_error=0;
 error=4;assert(exchange(0,3,0,0,0,0,data,4,&detail));assert(detail==4);
#ifdef M3_USB
 error=0;
 /* Earlier fault cases deliberately leave a failed init handle behind. */
 assert(!init(0,&hz,&detail));assert(qspi.Timeout==20);
 StorageIO io={NULL,ticks,delay,init,exchange,map,progress};
 memset(&store,0,sizeof(store));store.io=io;store.initialized=1;store.result.status=STORE_READY;
 calls=commands;assert(bench_storage_usb_read(STORE_BYTES,data,1)==2);assert(commands==calls);
 storage_busy=1;assert(bench_storage_usb_read(0,data,1)==1);assert(commands==calls);storage_busy=0;
 assert(!bench_storage_usb_read(0,data,1024));assert(!aborts);
#if !M3_STORAGE_RECORD
 store.result.mapped=1;unsigned oldmaps=maps;
 assert(!bench_storage_usb_read(0,data,1024));assert(aborts==1&&maps==oldmaps+1&&store.result.mapped);
 map_error=1;assert(bench_storage_usb_read(0,data,1024)==2);assert(store.result.status==STORE_STOPPED&&!store.result.mapped);
 map_error=0;store.result.status=STORE_READY;store.result.mapped=1;abort_error=1;calls=commands;
 assert(bench_storage_usb_read(0,data,1024)==2);assert(commands==calls&&store.result.status==STORE_STOPPED&&!storage_busy);
#endif
 store.result.mapped=0;store.result.status=STORE_READY;rx_error=1;
 assert(bench_storage_usb_read(0,data,1024)==2);assert(store.result.error==STORE_IO&&store.result.history&(1U<<STORE_IO));
 assert(!storage_busy);calls=commands;assert(bench_storage_usb_read(0,data,1024)==1);assert(commands==calls);
#endif
 puts("QSPI pin, mode, framing, bounds, allowlist and failure cleanup: PASS (scripted)");
 return 0;
}
