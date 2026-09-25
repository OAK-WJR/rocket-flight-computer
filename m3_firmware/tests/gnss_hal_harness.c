/* Production register/IRQ adapter against a scripted FIFO. No physical UART. */
#define M3_GNSS
#include "gnss/stm32h7xx_hal.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/gnss_stm32.c"
GPIO_TypeDef gb,gc,gd;USART_TypeDef usart;
uint32_t masked;
static uint32_t ms,hz=64000000,brr=6667;
static int clock_fail,init_fail,gpio_calls,irq_enabled,hold_tc;
static unsigned in_count,in_pos,out_count;
static uint8_t input[4096],output[512];
uint32_t HAL_GetTick(void){return ms;}
void HAL_GPIO_Init(GPIO_TypeDef *p,GPIO_InitTypeDef *i){
    assert(p==GPIOC&&i->Pin==(GPIO_PIN_6|GPIO_PIN_7)&&i->Alternate==7&&i->Pull==GPIO_NOPULL);gpio_calls++;
}
int HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef *p){assert(p->PeriphClockSelection==RCC_PERIPHCLK_USART6&&p->Usart16ClockSelection==RCC_USART16CLKSOURCE_HSI);return clock_fail;}
uint32_t HAL_RCCEx_GetPeriphCLKFreq(uint64_t p){assert(p==RCC_PERIPHCLK_USART6);return hz;}
int HAL_UART_Init(UART_HandleTypeDef *u){
    assert(u->Instance==USART6&&u->Init.BaudRate==9600&&u->Init.Mode==UART_MODE_TX_RX&&u->Init.Parity==UART_PARITY_NONE);
    usart.BRR=brr;usart.ISR=USART_ISR_TEACK|USART_ISR_REACK|USART_ISR_TXE_TXFNF|USART_ISR_TC;return init_fail;
}
int HAL_UARTEx_EnableFifoMode(UART_HandleTypeDef *u){assert(u->Instance==USART6);return 0;}
void HAL_NVIC_SetPriority(int n,int p,int s){assert(n==71&&p==6&&s==0);}
void HAL_NVIC_ClearPendingIRQ(int n){assert(n==71);}
void HAL_NVIC_EnableIRQ(int n){assert(n==71);irq_enabled=1;}
uint32_t mock_read(uint32_t *p){
    assert(p==&usart.RDR&&in_pos<in_count);uint32_t v=input[in_pos++];
    usart.ISR&=~ERRORS;if(in_pos==in_count)usart.ISR&=~USART_ISR_RXNE_RXFNE;return v;
}
void mock_write(uint32_t *p,uint32_t v){assert(p==&usart.TDR&&out_count<sizeof(output));output[out_count++]=v;if(hold_tc)usart.ISR&=~USART_ISR_TC;}
static void fresh(void){
    ms=0;hz=64000000;brr=6667;clock_fail=init_fail=gpio_calls=irq_enabled=hold_tc=0;masked=0;
    in_pos=in_count=out_count=0;memset(&usart,0,sizeof(usart));bench_gnss_initialize();
}
static void receive(unsigned n){
    assert(n<=sizeof(input));in_pos=0;in_count=n;usart.ISR|=USART_ISR_RXNE_RXFNE;
    while(in_pos<in_count){unsigned prior=in_pos;USART6_IRQHandler();assert(in_pos-prior<=32);}
}
int main(void){
    BenchGNSS r;bench_gnss_status(&r);assert(r.state==GNSS_OFF);
    fresh();assert(gpio_calls==1&&irq_enabled&&ready&&usart.CR1&(1U<<5)&&usart.CR3&1);
    fresh();clock_fail=1;gpio_calls=0;bench_gnss_initialize();bench_gnss_status(&r);assert(r.error==1&&!ready&&!gpio_calls);
    fresh();hz=32000000;bench_gnss_initialize();assert(!ready&&gnss.result.error==1);
    fresh();init_fail=1;bench_gnss_initialize();assert(!ready&&gnss.result.error==2);
    fresh();brr=123;bench_gnss_initialize();assert(!ready&&gnss.result.error==1);
    fresh();ms=6000;bench_gnss_task();bench_gnss_status(&r);assert(r.state==GNSS_NO_DATA);
    /* Byte order and the bounded receive budget are preserved. */
    fresh();memset(input,0x55,600);receive(600);assert(head==600);
    bench_gnss_task();assert(tail==256);bench_gnss_task();assert(tail==512);bench_gnss_task();assert(tail==600&&gnss.result.rx_bytes==600);
    /* Ring overflow discards the uncertain prefix and preserves caller mask. */
    fresh();receive(2060);assert(lost==13);masked=1;bench_gnss_task();assert(masked==1&&tail==head&&gnss.result.dropped==2060&&gnss.result.history&GNSS_H_OVERFLOW);
    fresh();usart.ISR|=USART_ISR_ORE;USART6_IRQHandler();bench_gnss_task();assert(gnss.result.uart_errors==8&&gnss.result.dropped==1);
    fresh();ms=1000;bench_gnss_task();bench_gnss_task();assert(out_count==8);
    const uint8_t version[]={0xb5,0x62,0x0a,0x04,0,0,0x0e,0x34};assert(!memcmp(output,version,8));
    fresh();hold_tc=1;ms=1000;bench_gnss_task();bench_gnss_task();assert(out_count==8&&tx_active);
    ms=1201;bench_gnss_task();assert(gnss.result.tx_errors==1&&!tx_active);
    fresh();ms=1000;bench_gnss_task();usart.ISR&=~USART_ISR_TXE_TXFNF;ms=1201;bench_gnss_task();assert(gnss.result.tx_errors==1&&out_count==0);
    fresh();ms=1234;bench_gnss_task();assert(gnss.result.max_gap_ms==1234);
    puts("GNSS HAL: 14 scripted clock/FIFO/overflow/timeout checks passed; no hardware");return 0;
}
