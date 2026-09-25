/* Executes actual voltage.c with scripted HAL responses and a call recorder. */
#include "../src/voltage.c"
#include <assert.h>
#include <stdio.h>
GPIO_TypeDef gc;
SYSCFG_TypeDef sy;
ADC_TypeDef a3;
ADC_Common_TypeDef acommon;
uint16_t factory_cal=24458;
static unsigned ticks, mode, init_calls, start_calls, poll_calls, stop_calls, cal_calls;
static unsigned channel, channels[8], nch, clock_stage;
uint32_t HAL_GetTick(void){return ticks++;}
void HAL_Delay(uint32_t d){ticks+=d;}
void clock_config(int v){assert(v==(++clock_stage==1 ? RCC_CLKPSOURCE_HSI:RCC_ADCCLKSOURCE_CLKP));}
void HAL_GPIO_Init(GPIO_TypeDef *p,GPIO_InitTypeDef *g){
    assert(p==GPIOC && g->Pin==(GPIO_PIN_2|GPIO_PIN_3) && g->Mode==GPIO_MODE_ANALOG && g->Pull==GPIO_NOPULL);
}
void HAL_SYSCFG_AnalogSwitchConfig(uint32_t sw,uint32_t value){
    assert(sw==value);if(mode!=10)sy.PMCR|=value;
}
uint32_t HAL_RCCEx_GetPeriphCLKFreq(uint32_t p){assert(p==RCC_PERIPHCLK_ADC);return mode==9 ? 0:64000000;}
HAL_StatusTypeDef HAL_ADC_Init(ADC_HandleTypeDef *a){
    init_calls++;assert(a->Instance==ADC3 && a->Init.ClockPrescaler==16 && a->Init.Resolution==16);
    assert(a->Init.NbrOfConversion==1 && a->Init.ScanConvMode==DISABLE);
    assert(a->Init.ExternalTrigConv==ADC_SOFTWARE_START && a->Init.ConversionDataManagement==ADC_CONVERSIONDATA_DR);
    if(mode==1){a->ErrorCode=99;return HAL_ERROR;}return HAL_OK;
}
void LL_ADC_StartCalibration(ADC_TypeDef *a,uint32_t c,uint32_t s){
    assert(a==ADC3 && c==ADC_CALIB_OFFSET_LINEARITY && s==ADC_SINGLE_ENDED);cal_calls++;
}
uint32_t LL_ADC_IsCalibrationOnGoing(ADC_TypeDef *a){assert(a==ADC3);return mode==2;}
HAL_StatusTypeDef HAL_ADC_ConfigChannel(ADC_HandleTypeDef *a,ADC_ChannelConfTypeDef *c){
    (void)a;assert(nch<8);channels[nch++]=channel=c->Channel;
    assert(c->Rank==1 && c->SamplingTime==1621 && c->SingleDiff==0 && c->OffsetNumber==0);
    if(mode==3 && channel==0)return HAL_ERROR;
    a3.PCSEL|=1U<<channel;return HAL_OK;
}
HAL_StatusTypeDef HAL_ADC_Start(ADC_HandleTypeDef *a){
    start_calls++;a->ErrorCode=0;if(mode==4 && channel==0)return HAL_ERROR;return HAL_OK;
}
HAL_StatusTypeDef HAL_ADC_PollForConversion(ADC_HandleTypeDef *a,uint32_t ms){
    assert(ms==20);poll_calls++;
    if(mode==5 && channel==0){a->ErrorCode=55;return HAL_ERROR;}return HAL_OK;
}
uint32_t HAL_ADC_GetValue(ADC_HandleTypeDef *a){
    (void)a;return channel==19 ? (mode==8 ? 0:24458) : (channel==0 ? 10000:32768);
}
HAL_StatusTypeDef HAL_ADC_Stop(ADC_HandleTypeDef *a){
    stop_calls++;if(mode==11 && channel==1)a->ErrorCode=42;
    return mode==6 && channel==0 ? HAL_ERROR:HAL_OK;
}
static void reset(unsigned fault){
    mode=fault;ticks=init_calls=start_calls=poll_calls=stop_calls=cal_calls=nch=clock_stage=0;
    memset(&adc,0,sizeof(adc));attempted=init_error=clocked=0;
    memset(&sy,0,sizeof(sy));memset(&a3,0,sizeof(a3));factory_cal=fault==7 ? 1529:24458;
}
int main(void){
    BenchADC v;
    reset(0);bench_adc_sample(&v);
    assert(v.status==STATUS_PASS && v.error==0 && v.valid==7);
    assert(v.vdda_mv==3300 && v.logic_mv==5539 && v.v3_mv==3300);
    assert(nch==3 && channels[0]==19 && channels[1]==0 && channels[2]==1);
    assert(cal_calls==1 && init_calls==1 && start_calls==3 && poll_calls==3 && stop_calls==3);
    bench_adc_sample(&v);assert(cal_calls==1 && init_calls==1 && nch==6);
    for(unsigned m=1;m<=11;m++){
        static const unsigned err[]={0,2,3,4,5,6,7,8,9,1,10,11};
        reset(m);bench_adc_sample(&v);assert(v.status==STATUS_FAIL && v.error==err[m]);
        assert(v.vdda_mv==0 && v.logic_mv==0 && v.v3_mv==0 && ticks<250);
        if(m>=3 && m<=6)assert(v.valid==1); /* ref preserved; no invented later channel */
        if(m==5)assert(stop_calls==2 && v.hal_error==55);
        if(m==2){bench_adc_sample(&v);assert(init_calls==1 && cal_calls==1);}
    }
    reset(0);bench_adc_sample(&v);mode=5;bench_adc_sample(&v);
    assert(v.status==STATUS_FAIL && v.valid==1 && v.v3==0 && v.v3_mv==0); /* no stale success */
    puts("13 scripted ADC cases passed; actual production C, not hardware");
}
