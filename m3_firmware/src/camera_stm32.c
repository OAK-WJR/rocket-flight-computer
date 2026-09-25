#ifdef M3_CAMERA_UART
#include "stm32h7xx_hal.h"
#include "camera.h"
#include <string.h>
static UART_HandleTypeDef camera_uart;
static int initialized;
#define CAM_RX_ERRORS (USART_ISR_PE | USART_ISR_FE | USART_ISR_NE | USART_ISR_ORE)

void bench_camera_safe_gpio(void) {
    __HAL_RCC_GPIOC_CLK_ENABLE(); __HAL_RCC_GPIOD_CLK_ENABLE();
    GPIO_InitTypeDef g = {0};
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);
    g.Pin=GPIO_PIN_13; g.Mode=GPIO_MODE_OUTPUT_PP; g.Pull=GPIO_NOPULL; g.Speed=GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOC, &g);
    HAL_GPIO_WritePin(GPIOD, GPIO_PIN_3, GPIO_PIN_RESET);
    g.Pin=GPIO_PIN_3; HAL_GPIO_Init(GPIOD, &g);
}
static uint32_t ticks(void *ctx) { (void)ctx; return HAL_GetTick(); }
static int output_enable(void *ctx, int high) {
    (void)ctx; HAL_GPIO_WritePin(GPIOC,GPIO_PIN_13,high?GPIO_PIN_SET:GPIO_PIN_RESET);
    return HAL_GPIO_ReadPin(GPIOC,GPIO_PIN_13)==GPIO_PIN_SET;
}
static int power_enable(void *ctx, int high) {
    (void)ctx; HAL_GPIO_WritePin(GPIOD,GPIO_PIN_3,high?GPIO_PIN_SET:GPIO_PIN_RESET);
    return HAL_GPIO_ReadPin(GPIOD,GPIO_PIN_3)==GPIO_PIN_SET;
}
static int initialize(void *ctx, CameraResult *r) {
    (void)ctx;
    RCC_PeriphCLKInitTypeDef clock = {0};
    clock.PeriphClockSelection=RCC_PERIPHCLK_USART3;
    clock.Usart234578ClockSelection=RCC_USART234578CLKSOURCE_HSI;
    if (HAL_RCCEx_PeriphCLKConfig(&clock)!=HAL_OK) return CAM_CLOCK;
    r->kernel_hz=HAL_RCCEx_GetPeriphCLKFreq(RCC_PERIPHCLK_USART3);
    if (r->kernel_hz!=64000000U) return CAM_CLOCK;
    __HAL_RCC_GPIOB_CLK_ENABLE(); __HAL_RCC_USART3_CLK_ENABLE();
    __HAL_RCC_USART3_FORCE_RESET(); __HAL_RCC_USART3_RELEASE_RESET();
    /* Establish idle-high at the MCU pin before selecting USART AF and before
     * enabling U12. RX has an MCU-side pull-up while U12 output is high-Z. */
    HAL_GPIO_WritePin(GPIOB,GPIO_PIN_10,GPIO_PIN_SET);
    GPIO_InitTypeDef g={0};
    g.Pin=GPIO_PIN_10; g.Mode=GPIO_MODE_OUTPUT_PP; g.Pull=GPIO_NOPULL; g.Speed=GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOB,&g);
    memset(&camera_uart,0,sizeof(camera_uart));
    camera_uart.Instance=USART3;
    camera_uart.Init.BaudRate=115200;
    camera_uart.Init.WordLength=UART_WORDLENGTH_8B;
    camera_uart.Init.StopBits=UART_STOPBITS_1;
    camera_uart.Init.Parity=UART_PARITY_NONE;
    camera_uart.Init.Mode=UART_MODE_TX_RX;
    camera_uart.Init.HwFlowCtl=UART_HWCONTROL_NONE;
    camera_uart.Init.OverSampling=UART_OVERSAMPLING_16;
    camera_uart.Init.OneBitSampling=UART_ONE_BIT_SAMPLE_DISABLE;
    camera_uart.Init.ClockPrescaler=UART_PRESCALER_DIV1;
    camera_uart.AdvancedInit.AdvFeatureInit=UART_ADVFEATURE_NO_INIT;
    if (HAL_UART_Init(&camera_uart)!=HAL_OK || HAL_UARTEx_EnableFifoMode(&camera_uart)!=HAL_OK)
        return CAM_INIT;
    r->brr=USART3->BRR;
    if (r->brr != 556U || !(USART3->ISR & USART_ISR_TEACK) || !(USART3->ISR & USART_ISR_REACK))
        return CAM_CLOCK;
    g.Mode=GPIO_MODE_AF_PP;g.Alternate=GPIO_AF7_USART3;g.Pin=GPIO_PIN_10;
    HAL_GPIO_Init(GPIOB,&g);
    g.Pin=GPIO_PIN_11;g.Pull=GPIO_PULLUP;HAL_GPIO_Init(GPIOB,&g);
    initialized=1;
    return CAM_NONE;
}
static int errors(CameraResult *r) {
    uint32_t flags=USART3->ISR; r->isr=flags;
    if (!(flags & CAM_RX_ERRORS)) return 0;
    r->error_flags |= flags & CAM_RX_ERRORS; /* retain before W1C */
    __HAL_UART_CLEAR_FLAG(&camera_uart,UART_CLEAR_PEF|UART_CLEAR_FEF|UART_CLEAR_NEF|UART_CLEAR_OREF);
    return 1;
}
static int transmit(void *ctx,uint8_t b,CameraResult *r) {
    (void)ctx; if (errors(r)) return -1;
    if (!(USART3->ISR & USART_ISR_TXE_TXFNF)) return 0;
    USART3->TDR=b;return 1;
}
static int complete(void *ctx,CameraResult *r) {
    (void)ctx;if (errors(r)) return -1;
    return (USART3->ISR & USART_ISR_TC)!=0;
}
static int receive(void *ctx,uint8_t *b,CameraResult *r) {
    (void)ctx;if (errors(r)) return -1;
    if (!(USART3->ISR & USART_ISR_RXNE_RXFNE)) return 0;
    *b=(uint8_t)USART3->RDR;
    if (errors(r)) return -1;
    return 1;
}
static void snapshot(void *ctx,CameraResult *r) {
    (void)ctx;
    r->power_readback=HAL_GPIO_ReadPin(GPIOD,GPIO_PIN_3)==GPIO_PIN_SET;
    r->oe_readback=HAL_GPIO_ReadPin(GPIOC,GPIO_PIN_13)==GPIO_PIN_SET;
    if (initialized) {
        r->isr=USART3->ISR;r->error_flags |= r->isr & CAM_RX_ERRORS;
        if (r->error_flags && !r->error) r->error=CAM_UART_ERROR;
        __HAL_UART_DISABLE(&camera_uart);
    }
}
void bench_camera_query(int enabled,CameraResult *result) {
    const CameraIO io={NULL,ticks,initialize,power_enable,output_enable,transmit,complete,receive,snapshot};
    camera_query(&io,enabled,result);
}
#endif
