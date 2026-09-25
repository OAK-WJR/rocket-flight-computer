#define M3_POWER_STATUS
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/power_status_stm32.c"
GPIO_TypeDef gd;RCC_TypeDef rc;SYSCFG_TypeDef sc;EXTI_TypeDef ex;
uint32_t masks,now;static unsigned enabled[32],configured,priorities;
uint32_t HAL_GetTick(void){return now;}
void HAL_GPIO_Init(GPIO_TypeDef *p,GPIO_InitTypeDef *g){
    assert(p==&gd&&g->Pull==0);
    assert((g->Pin==0x51&&g->Mode==GPIO_MODE_IT_FALLING)||(g->Pin==2&&g->Mode==GPIO_MODE_IT_RISING_FALLING));
    configured|=g->Pin;
    for(unsigned n=0;n<16;n++)if(g->Pin&(1U<<n)){
        p->MODER&=~(3U<<(n*2));p->PUPDR&=~(3U<<(n*2));
        sc.EXTICR[n/4]=(sc.EXTICR[n/4]&~(15U<<((n%4)*4)))|(3U<<((n%4)*4));
    }
    ex.IMR1|=g->Pin;ex.FTSR1|=g->Pin;ex.RTSR1&=~g->Pin;
    if(g->Mode==GPIO_MODE_IT_RISING_FALLING)ex.RTSR1|=g->Pin;
}
void HAL_NVIC_SetPriority(IRQn_Type n,unsigned p,unsigned sub){assert(n==6||n==7||n==10||n==23);assert(p==14&&!sub);priorities++;}
void HAL_NVIC_ClearPendingIRQ(IRQn_Type n){assert(n==6||n==7||n==10||n==23);}
void HAL_NVIC_EnableIRQ(IRQn_Type n){enabled[n]=1;}
int NVIC_GetEnableIRQ(IRQn_Type n){return enabled[n];}
int main(void){
    BenchPowerStatus r;now=100;gd.MODER=gd.PUPDR=0xffffffffU;gd.ODR=0xa5a5;gd.IDR=0x53;
    masks=1;bench_power_initialize();assert(masks==1);assert(configured==0x53&&priorities==4);
    assert(gd.ODR==0xa5a5&&gd.MODER==(0xffffffffU&~0x330fU)&&gd.PUPDR==(0xffffffffU&~0x330fU));
    assert((sc.EXTICR[0]&0xff)==0x33&&(sc.EXTICR[1]&0xf0f)==0x303);
    assert(ex.FTSR1==0x53&&ex.RTSR1==2);bench_power_status(&r);assert(r.flags==3);
    now++;masks=0;bench_power_tick();assert(!masks);bench_power_status(&r);assert(r.flags==7);
    ex.PR1=0x41;EXTI9_5_IRQHandler();assert(ex.PR1==0x40);bench_power_status(&r);
    assert(r.history&0x40);assert(!(r.history&1));assert(r.irq_count==1);
    ex.PR1=1;EXTI0_IRQHandler();ex.PR1=2;EXTI1_IRQHandler();ex.PR1=16;EXTI4_IRQHandler();
    bench_power_status(&r);assert((r.history&0xffff)==0x51&&r.irq_count==4&&gd.ODR==0xa5a5);
    const unsigned pins[]={0,1,4,6};
    for(unsigned i=0;i<4;i++){
        unsigned p=pins[i],save=gd.MODER;gd.MODER|=1U<<(p*2);bench_power_tick();bench_power_status(&r);assert(!(r.flags&2));gd.MODER=save;
        save=gd.PUPDR;gd.PUPDR|=1U<<(p*2);bench_power_tick();bench_power_status(&r);assert(!(r.flags&2));gd.PUPDR=save;
        save=sc.EXTICR[p/4];sc.EXTICR[p/4]^=1U<<((p%4)*4);bench_power_tick();bench_power_status(&r);assert(!(r.flags&2));sc.EXTICR[p/4]=save;
        enabled[irqs[i]]=0;bench_power_tick();bench_power_status(&r);assert(!(r.flags&2));enabled[irqs[i]]=1;
    }
    uint32_t *regs[]={&rc.AHB4ENR,&rc.APB4ENR,&ex.IMR1,&ex.FTSR1,&ex.RTSR1};
    for(unsigned i=0;i<5;i++){uint32_t save=*regs[i];*regs[i]=0;bench_power_tick();bench_power_status(&r);assert(!(r.flags&2));*regs[i]=save;}
    bench_power_tick();bench_power_status(&r);assert((r.flags&34)==34);assert(gd.ODR==0xa5a5&&!masks);
    puts("status HAL input mapping, 21 configuration corruptions, IRQ masks and recovery passed; synthetic only");
}
