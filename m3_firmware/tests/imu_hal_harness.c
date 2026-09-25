/* Runs the actual GPIO/clock/CS adapter, instrumented with UBSan. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define M3_IMU_SAMPLES
#include "../src/imu_stm32.c"
GPIO_TypeDef gb;
SPI_TypeDef bus;
static uint32_t tick,kernel,error_bits;
static int cs_stuck,clock_fail,init_fail,bad_cfg,init_count,af_count,xfer_count,transfer_rc;
uint32_t HAL_GetTick(void) { return tick; }
void HAL_Delay(uint32_t ms) { tick+=ms; }
void HAL_GPIO_WritePin(GPIO_TypeDef *p,uint16_t pins,int high) {
    assert(p==GPIOB && !(pins & ~(GPIO_PIN_3|GPIO_PIN_5|GPIO_PIN_7)));
    if(high)p->ODR|=pins;else p->ODR&=~pins;
    p->IDR=p->ODR;
    if(cs_stuck)p->IDR&=~GPIO_PIN_7;
}
int HAL_GPIO_ReadPin(GPIO_TypeDef *p,uint16_t pins) { assert(p==GPIOB&&pins==GPIO_PIN_7);return (p->IDR&pins)!=0; }
void HAL_GPIO_Init(GPIO_TypeDef *p,GPIO_InitTypeDef *g) {
    assert(p==GPIOB && g->Pull==GPIO_NOPULL && g->Speed==GPIO_SPEED_FREQ_LOW);
    assert(gb.ODR & GPIO_PIN_7);
    if(g->Mode==GPIO_MODE_AF_PP) {
        assert(init_count==1 && g->Alternate==5 && g->Pin==(GPIO_PIN_3|GPIO_PIN_4|GPIO_PIN_5));
        af_count++;
    } else assert(g->Pin==GPIO_PIN_7&&g->Mode==GPIO_MODE_OUTPUT_PP);
}
int HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef *p) {
    assert(p->PeriphClockSelection==(RCC_PERIPHCLK_SPI1|RCC_PERIPHCLK_CKPER));
    assert(p->Spi123ClockSelection==RCC_SPI123CLKSOURCE_CLKP&&p->CkperClockSelection==RCC_CLKPSOURCE_HSI);
    return clock_fail;
}
uint32_t HAL_RCCEx_GetPeriphCLKFreq(uint64_t p) { assert(p==RCC_PERIPHCLK_SPI1);return kernel; }
int HAL_SPI_Init(SPI_HandleTypeDef *h) {
    init_count++;assert(h->Instance==SPI1 && h->Init.Mode==SPI_MODE_MASTER);
    assert(h->Init.Direction==SPI_DIRECTION_2LINES&&h->Init.DataSize==7&&h->Init.CLKPolarity==0&&h->Init.CLKPhase==0);
    assert(h->Init.NSS==SPI_NSS_SOFT && h->Init.BaudRatePrescaler==SPI_BAUDRATEPRESCALER_64);
    assert(h->Init.FirstBit==0 && h->Init.FifoThreshold==0 && h->Init.MasterKeepIOState==SPI_MASTER_KEEP_IO_STATE_ENABLE);
    assert(!h->Init.IOSwap&&!h->Init.CRCCalculation&&!h->Init.TIMode);
    bus.CFG1=SPI_BAUDRATEPRESCALER_64|7;bus.CFG2=0;
    if(bad_cfg==1)bus.CFG1=7;
    if(bad_cfg>1)bus.CFG2=1U<<(bad_cfg-2);
    return init_fail;
}
int HAL_SPI_TransmitReceive(SPI_HandleTypeDef *h,const uint8_t *tx,uint8_t *rx,uint16_t n,uint32_t timeout) {
    assert(h==&spi && timeout==10 && !(gb.ODR&GPIO_PIN_7));
    assert(n>=2&&n<=15);xfer_count++;
    for(unsigned i=0;i<n;i++)rx[i]=tx[i]^0x55U;
    return transfer_rc;
}
uint32_t HAL_SPI_GetError(SPI_HandleTypeDef *h) { assert(h==&spi);return error_bits; }
static void reset(void) {
    memset(&gb,0,sizeof(gb));memset(&bus,0,sizeof(bus));tick=0;kernel=64000000;error_bits=0;
    cs_stuck=clock_fail=init_fail=bad_cfg=init_count=af_count=xfer_count=transfer_rc=0;
}
int main(void) {
    uint32_t hz,detail;uint8_t tx[15]={0xf2},rx[15]={0};int n=0;
    reset();assert(initialize(NULL,&hz,&detail)==0&&hz==1000000&&af_count==1);n++;
    reset();cs_stuck=1;assert(initialize(NULL,&hz,&detail)==IMU_SPI_INIT&&detail==0x40000001&&!init_count);n++;
    reset();clock_fail=1;assert(initialize(NULL,&hz,&detail)==IMU_CLOCK&&!af_count&&!init_count);n++;
    reset();kernel=32000000;assert(initialize(NULL,&hz,&detail)==IMU_CLOCK&&!init_count);n++;
    reset();init_fail=3;error_bits=0x40;assert(initialize(NULL,&hz,&detail)==IMU_SPI_INIT&&detail==0x03000040&&!af_count);n++;
    for(int k=1;k<=4;k++) { reset();bad_cfg=k;assert(initialize(NULL,&hz,&detail)==IMU_SPI_INIT&&!af_count); }n++;
    reset();assert(initialize(NULL,&hz,&detail)==0);
    assert(exchange(NULL,tx,rx,15,&detail)==0&&xfer_count==1&&rx[0]==(0xf2^0x55));assert(gb.ODR&GPIO_PIN_7);n++;
    for(int rc=1;rc<=3;rc++) {
        reset();assert(initialize(NULL,&hz,&detail)==0);transfer_rc=rc;error_bits=0x40;
        assert(exchange(NULL,tx,rx,2,&detail)!=0&&detail==((uint32_t)rc<<24|0x40));assert(gb.ODR&GPIO_PIN_7);
    }n++;
    reset();assert(initialize(NULL,&hz,&detail)==0);error_bits=0x20;
    assert(exchange(NULL,tx,rx,2,&detail)!=0&&detail==0x20);assert(gb.ODR&GPIO_PIN_7);n++;
    reset();assert(initialize(NULL,&hz,&detail)==0);cs_stuck=1;
    assert(exchange(NULL,tx,rx,2,&detail)!=0&&detail==0x40000001);n++;
    reset();assert(initialize(NULL,&hz,&detail)==0);
    assert(exchange(NULL,tx,rx,0,&detail)!=0&&exchange(NULL,tx,rx,16,&detail)!=0&&!xfer_count);n++;
    reset();pause_ms(NULL,100);assert(ticks(NULL)==100);n++;
    assert(n==12);puts("12 scripted STM32 SPI adapter cases passed");return 0;
}
