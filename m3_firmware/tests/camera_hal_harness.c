/* Executes the actual STM32 adapter, with register/HAL behavior scripted. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define M3_CAMERA_UART
#include "../src/camera_stm32.c"
GPIO_TypeDef gb,gc,gd;
USART_TypeDef usart;
static uint32_t tick,kernel=64000000;
static int clock_fail,init_fail,fifo_fail,tx_af,rx_af,init_calls,gpio_count;
static GPIO_TypeDef *ports[10];
uint32_t HAL_GetTick(void) { return ++tick; }
void HAL_GPIO_WritePin(GPIO_TypeDef *p,uint16_t pin,int high) {
    if(high)p->ODR|=pin;else p->ODR&=~pin;p->IDR=p->ODR;
}
int HAL_GPIO_ReadPin(GPIO_TypeDef *p,uint16_t pin) { return (p->IDR&pin)!=0; }
void HAL_GPIO_Init(GPIO_TypeDef *p,GPIO_InitTypeDef *g) {
    ports[gpio_count++]=p;
    if(g->Mode==GPIO_MODE_AF_PP) {
        assert(p==GPIOB && g->Alternate==7 && !(gc.ODR&GPIO_PIN_13));
        if(g->Pin==GPIO_PIN_10) { assert(gb.ODR&GPIO_PIN_10);tx_af++; }
        else { assert(g->Pin==GPIO_PIN_11 && g->Pull==GPIO_PULLUP);rx_af++; }
    }
}
int HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef *p) {
    assert(p->PeriphClockSelection==RCC_PERIPHCLK_USART3 && p->Usart234578ClockSelection==RCC_USART234578CLKSOURCE_HSI);
    return clock_fail;
}
uint32_t HAL_RCCEx_GetPeriphCLKFreq(uint64_t p) { assert(p==RCC_PERIPHCLK_USART3);return kernel; }
int HAL_UART_Init(UART_HandleTypeDef *h) {
    init_calls++;assert(h->Instance==USART3 && h->Init.BaudRate==115200);
    assert(h->Init.Mode==UART_MODE_TX_RX && h->Init.Parity==UART_PARITY_NONE);
    assert(h->Init.OverSampling==UART_OVERSAMPLING_16 && h->Init.ClockPrescaler==UART_PRESCALER_DIV1);
    usart.BRR=556;usart.ISR=USART_ISR_TEACK|USART_ISR_REACK;usart.CR1=1;
    return init_fail;
}
int HAL_UARTEx_EnableFifoMode(UART_HandleTypeDef *h) { assert(h==&camera_uart);return fifo_fail; }
static void reset(void) {
    memset(&gb,0,sizeof(gb));memset(&gc,0,sizeof(gc));memset(&gd,0,sizeof(gd));memset(&usart,0,sizeof(usart));
    tick=0;kernel=64000000;clock_fail=init_fail=fifo_fail=tx_af=rx_af=init_calls=gpio_count=initialized=0;
}
int main(void) {
    CameraResult r={0};uint8_t b=0;int n=0;
    reset();bench_camera_safe_gpio();assert(ports[0]==GPIOC && ports[1]==GPIOD);assert(!gc.ODR&&!gd.ODR);n++;
    reset();bench_camera_safe_gpio();bench_camera_query(0,&r);assert(!init_calls&&!r.status&&!r.power_readback&&!r.oe_readback);n++;
    reset();assert(initialize(NULL,&r)==0);assert(tx_af==1&&rx_af==1&&r.brr==556&&initialized);n++;
    reset();clock_fail=1;assert(initialize(NULL,&r)==CAM_CLOCK&&!tx_af&&!init_calls);n++;
    reset();kernel=32000000;assert(initialize(NULL,&r)==CAM_CLOCK&&!init_calls);n++;
    reset();init_fail=1;assert(initialize(NULL,&r)==CAM_INIT&&!tx_af);n++;
    reset();fifo_fail=1;assert(initialize(NULL,&r)==CAM_INIT&&!tx_af);n++;
    reset();usart.TDR=0x55;assert(transmit(NULL,0xcc,&r)==0&&usart.TDR==0x55);
    usart.ISR=USART_ISR_TXE_TXFNF;assert(transmit(NULL,0xcc,&r)==1&&usart.TDR==0xcc);n++;
    reset();assert(complete(NULL,&r)==0);usart.ISR=USART_ISR_TC;assert(complete(NULL,&r)==1);n++;
    reset();b=0xa5;assert(receive(NULL,&b,&r)==0&&b==0xa5);usart.ISR=USART_ISR_RXNE_RXFNE;usart.RDR=0xcc;
    assert(receive(NULL,&b,&r)==1&&b==0xcc);n++;
    for(unsigned flag=1;flag<=8;flag<<=1) {
        reset();memset(&r,0,sizeof(r));usart.ISR=flag|USART_ISR_RXNE_RXFNE;b=0xa5;
        assert(receive(NULL,&b,&r)==-1&&b==0xa5&&r.error_flags==flag&&usart.ICR==15);
    }n++;
    reset();initialized=1;gd.IDR=GPIO_PIN_3;usart.CR1=1;usart.ISR=USART_ISR_NE;memset(&r,0,sizeof(r));
    snapshot(NULL,&r);assert(r.error==CAM_UART_ERROR&&r.error_flags==4&&r.power_readback==1&&!usart.CR1);n++;
    assert(n==12);puts("12 scripted STM32 UART cases passed");return 0;
}
