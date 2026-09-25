#ifdef M3_POWER_STATUS
#include "stm32h7xx_hal.h"
#include "power_status.h"
static PowerStatus status;
static volatile unsigned ready;
static const IRQn_Type irqs[]={EXTI0_IRQn,EXTI1_IRQn,EXTI4_IRQn,EXTI9_5_IRQn};
static int configuration_ok(void){
    const uint32_t modes=0x330fU; /* two mode/pull bits for PD0,1,4,6 */
    if(!(RCC->AHB4ENR&RCC_AHB4ENR_GPIODEN)||!(RCC->APB4ENR&RCC_APB4ENR_SYSCFGEN))return 0;
    if((GPIOD->MODER&modes)||(GPIOD->PUPDR&modes))return 0;
    if((SYSCFG->EXTICR[0]&0xffU)!=0x33U||(SYSCFG->EXTICR[1]&0xf0fU)!=0x303U)return 0;
    if((EXTI->IMR1&POWER_PIN_MASK)!=POWER_PIN_MASK||
       (EXTI->FTSR1&POWER_PIN_MASK)!=POWER_PIN_MASK||
       (EXTI->RTSR1&POWER_PIN_MASK)!=POWER_MUX_MASK)return 0;
    for(unsigned i=0;i<sizeof(irqs)/sizeof(irqs[0]);i++)if(!NVIC_GetEnableIRQ(irqs[i]))return 0;
    return 1;
}
void bench_power_initialize(void){
    uint32_t mask=__get_PRIMASK();__disable_irq();ready=0;
    __HAL_RCC_GPIOD_CLK_ENABLE();__HAL_RCC_SYSCFG_CLK_ENABLE();
    GPIO_InitTypeDef g={0};g.Pin=POWER_FAULT_MASK;g.Mode=GPIO_MODE_IT_FALLING;
    g.Pull=GPIO_NOPULL;HAL_GPIO_Init(GPIOD,&g);
    g.Pin=POWER_MUX_MASK;g.Mode=GPIO_MODE_IT_RISING_FALLING;HAL_GPIO_Init(GPIOD,&g);
    /* Discard only pre-monitor pending edges. Startup level is captured below. */
    EXTI->PR1=POWER_PIN_MASK;
    for(unsigned i=0;i<sizeof(irqs)/sizeof(irqs[0]);i++){
        HAL_NVIC_SetPriority(irqs[i],14,0);HAL_NVIC_ClearPendingIRQ(irqs[i]);HAL_NVIC_EnableIRQ(irqs[i]);
    }
    power_status_init(&status,HAL_GetTick(),GPIOD->IDR,configuration_ok());ready=1;
    __set_PRIMASK(mask);
}
static void event(uint32_t lines){
    uint32_t mask=__get_PRIMASK();__disable_irq();
    uint32_t pending=EXTI->PR1&lines&POWER_PIN_MASK;
    EXTI->PR1=pending; /* W1C only the handled status lines */
    if(ready&&pending)power_status_observe(&status,HAL_GetTick(),GPIOD->IDR,pending,0,configuration_ok());
    __set_PRIMASK(mask);
}
void EXTI0_IRQHandler(void){event(1U);}
void EXTI1_IRQHandler(void){event(2U);}
void EXTI4_IRQHandler(void){event(16U);}
void EXTI9_5_IRQHandler(void){event(64U);}
void bench_power_tick(void){
    if(!ready)return;
    uint32_t mask=__get_PRIMASK();__disable_irq();
    power_status_observe(&status,HAL_GetTick(),GPIOD->IDR,0,1,configuration_ok());
    __set_PRIMASK(mask);
}
void bench_power_status(BenchPowerStatus *out){
    uint32_t mask=__get_PRIMASK();__disable_irq();*out=status.r;__set_PRIMASK(mask);
}
#endif
