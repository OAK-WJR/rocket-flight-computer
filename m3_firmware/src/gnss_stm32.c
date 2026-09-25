#ifdef M3_GNSS
#include "stm32h7xx_hal.h"
#include "gnss.h"
#include <string.h>
#define RING 2048U
#define ERRORS (USART_ISR_PE|USART_ISR_FE|USART_ISR_NE|USART_ISR_ORE)
typedef struct{uint32_t tick;uint8_t byte;} Received;
static Received ring[RING];
static volatile uint32_t head,tail,lost,errors;
static uint32_t seen_lost,seen_errors,last_service,last_poll,last_version,poll_start;
static GNSS gnss;
static UART_HandleTypeDef uart;
static int ready,inside,tx_used=8,tx_active;
static uint8_t poll[8];

void USART6_IRQHandler(void){
    for(unsigned budget=0;budget<32;budget++){
        uint32_t status=USART6->ISR;
        if(status&ERRORS){errors|=status&ERRORS;lost++;USART6->ICR=USART_ICR_PECF|USART_ICR_FECF|USART_ICR_NECF|USART_ICR_ORECF;}
        if(!(status&USART_ISR_RXNE_RXFNE))break;
        uint8_t b=(uint8_t)READ_REG(USART6->RDR);
        if(status&ERRORS)continue;
        uint32_t h=head,next=(h+1)&(RING-1);
        if(next==tail){lost++;continue;}
        ring[h].byte=b;ring[h].tick=HAL_GetTick();__DMB();head=next;
    }
}
void bench_gnss_initialize(void){
    uint32_t now=HAL_GetTick();gnss_init(&gnss,now);ready=inside=0;
    head=tail=lost=errors=seen_lost=seen_errors=0;last_service=last_poll=last_version=now;tx_used=8;tx_active=0;
    RCC_PeriphCLKInitTypeDef clk={0};clk.PeriphClockSelection=RCC_PERIPHCLK_USART6;
    clk.Usart16ClockSelection=RCC_USART16CLKSOURCE_HSI;
    if(HAL_RCCEx_PeriphCLKConfig(&clk)!=HAL_OK){gnss.result.error=GNSS_E_CLOCK;return;}
    gnss.result.kernel_hz=HAL_RCCEx_GetPeriphCLKFreq(RCC_PERIPHCLK_USART6);
    if(gnss.result.kernel_hz!=64000000U){gnss.result.error=GNSS_E_CLOCK;return;}
    __HAL_RCC_GPIOC_CLK_ENABLE();__HAL_RCC_USART6_CLK_ENABLE();
    __HAL_RCC_USART6_FORCE_RESET();__HAL_RCC_USART6_RELEASE_RESET();
    memset(&uart,0,sizeof(uart));uart.Instance=USART6;uart.Init.BaudRate=9600;
    uart.Init.WordLength=UART_WORDLENGTH_8B;uart.Init.StopBits=UART_STOPBITS_1;uart.Init.Parity=UART_PARITY_NONE;
    uart.Init.Mode=UART_MODE_TX_RX;uart.Init.HwFlowCtl=UART_HWCONTROL_NONE;uart.Init.OverSampling=UART_OVERSAMPLING_16;
    uart.Init.OneBitSampling=UART_ONE_BIT_SAMPLE_DISABLE;uart.Init.ClockPrescaler=UART_PRESCALER_DIV1;
    uart.AdvancedInit.AdvFeatureInit=UART_ADVFEATURE_NO_INIT;
    if(HAL_UART_Init(&uart)!=HAL_OK||HAL_UARTEx_EnableFifoMode(&uart)!=HAL_OK){gnss.result.error=GNSS_E_INIT;return;}
    gnss.result.brr=USART6->BRR;
    if(gnss.result.brr!=6667U||(USART6->ISR&(USART_ISR_TEACK|USART_ISR_REACK))!=(USART_ISR_TEACK|USART_ISR_REACK)){
        gnss.result.error=GNSS_E_CLOCK;return;
    }
    GPIO_InitTypeDef pin={0};pin.Pin=GPIO_PIN_6|GPIO_PIN_7;pin.Mode=GPIO_MODE_AF_PP;
    pin.Pull=GPIO_NOPULL;pin.Speed=GPIO_SPEED_FREQ_LOW;pin.Alternate=GPIO_AF7_USART6;HAL_GPIO_Init(GPIOC,&pin);
    HAL_NVIC_SetPriority(USART6_IRQn,6,0);HAL_NVIC_ClearPendingIRQ(USART6_IRQn);
    USART6->ICR=USART_ICR_PECF|USART_ICR_FECF|USART_ICR_NECF|USART_ICR_ORECF;
    USART6->CR1|=USART_CR1_RXNEIE_RXFNEIE|USART_CR1_PEIE;USART6->CR3|=USART_CR3_EIE;
    ready=1;HAL_NVIC_EnableIRQ(USART6_IRQn);
}
void bench_gnss_task(void){
    if(!ready||inside)return;
    inside=1;uint32_t now=HAL_GetTick();
    uint32_t gap=now-last_service;last_service=now;if(gap>gnss.result.max_gap_ms)gnss.result.max_gap_ms=gap;
    uint32_t l=lost,e=errors;
    if(l!=seen_lost||e!=seen_errors){
        /* Discard the damaged stream before accepting another complete packet. */
        uint32_t primask=__get_PRIMASK();__disable_irq();
        l=lost;e=errors;uint32_t queued=(head-tail)&(RING-1);tail=head;
        __set_PRIMASK(primask);
        /* dropped counts discarded queued bytes plus ISR loss events. A UART
         * overrun can conceal several bytes: this is a lower bound, not a
         * promise of an exact lost-byte count. */
        gnss_loss(&gnss,l-seen_lost+queued,e);seen_lost=l;seen_errors=e;
    }
    for(unsigned budget=0;budget<256&&tail!=head;budget++){
        uint32_t t=tail;__DMB();Received b=ring[t];__DMB();tail=(t+1)&(RING-1);
        gnss_feed(&gnss,b.byte,b.tick);
    }
    gnss_tick(&gnss,now);
    if(tx_active){
        while(tx_used<8&&(USART6->ISR&USART_ISR_TXE_TXFNF))WRITE_REG(USART6->TDR,poll[tx_used++]);
        if(tx_used==8&&(USART6->ISR&USART_ISR_TC))tx_active=0;
        else if((uint32_t)(now-poll_start)>200U){
            tx_used=8;tx_active=0;gnss.result.tx_errors++;gnss.result.history|=GNSS_H_TX;
        }
    }else if((USART6->ISR&USART_ISR_TC)&&(uint32_t)(now-last_poll)>=1000U){
        int version=!(gnss.result.flags&GNSS_VER)||(uint32_t)(now-last_version)>=10000U;
        gnss_poll_packet(poll,version);if(version)last_version=now;
        last_poll=poll_start=now;tx_used=0;tx_active=1;gnss.result.tx_count++;
    }
    inside=0;
}
void bench_gnss_status(BenchGNSS *out){gnss_tick(&gnss,HAL_GetTick());*out=gnss.result;}
#endif
