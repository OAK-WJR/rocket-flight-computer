/* Test double. ARM build never includes this directory. */
#ifndef GNSS_TEST_HAL
#define GNSS_TEST_HAL
#include <stdint.h>
#include <stddef.h>
typedef struct { uint32_t ODR,IDR; } GPIO_TypeDef;
typedef struct { uint32_t BRR,ISR,ICR,RDR,TDR,CR1,CR3; } USART_TypeDef;
extern GPIO_TypeDef gb,gc,gd;
extern USART_TypeDef usart;
#define GPIOB (&gb)
#define GPIOC (&gc)
#define GPIOD (&gd)
#define USART3 (&usart)
#define GPIO_PIN_3 (1U<<3)
#define GPIO_PIN_10 (1U<<10)
#define GPIO_PIN_11 (1U<<11)
#define GPIO_PIN_13 (1U<<13)
#define GPIO_PIN_RESET 0
#define GPIO_PIN_SET 1
#define GPIO_MODE_OUTPUT_PP 1
#define GPIO_MODE_AF_PP 2
#define GPIO_NOPULL 0
#define GPIO_PULLUP 1
#define GPIO_SPEED_FREQ_LOW 0
#define GPIO_AF7_USART3 7
#define RCC_PERIPHCLK_USART3 2
#define RCC_USART234578CLKSOURCE_HSI 3
#define UART_WORDLENGTH_8B 0
#define UART_STOPBITS_1 0
#define UART_PARITY_NONE 0
#define UART_MODE_TX_RX 12
#define UART_HWCONTROL_NONE 0
#define UART_OVERSAMPLING_16 0
#define UART_ONE_BIT_SAMPLE_DISABLE 0
#define UART_PRESCALER_DIV1 0
#define UART_ADVFEATURE_NO_INIT 0
#define USART_ISR_PE 1U
#define USART_ISR_FE 2U
#define USART_ISR_NE 4U
#define USART_ISR_ORE 8U
#define USART_ISR_RXNE_RXFNE (1U<<5)
#define USART_ISR_TC (1U<<6)
#define USART_ISR_TXE_TXFNF (1U<<7)
#define USART_ISR_TEACK (1U<<21)
#define USART_ISR_REACK (1U<<22)
#define UART_CLEAR_PEF 1U
#define UART_CLEAR_FEF 2U
#define UART_CLEAR_NEF 4U
#define UART_CLEAR_OREF 8U
#define HAL_OK 0
typedef struct { uint32_t Pin,Mode,Pull,Speed,Alternate; } GPIO_InitTypeDef;
typedef struct { uint64_t PeriphClockSelection; uint32_t Usart234578ClockSelection,Usart16ClockSelection; } RCC_PeriphCLKInitTypeDef;
typedef struct { USART_TypeDef *Instance;
    struct { uint32_t BaudRate,WordLength,StopBits,Parity,Mode,HwFlowCtl,OverSampling,OneBitSampling,ClockPrescaler; } Init;
    struct { uint32_t AdvFeatureInit; } AdvancedInit;
} UART_HandleTypeDef;
#define __HAL_RCC_GPIOB_CLK_ENABLE() ((void)0)
#define __HAL_RCC_GPIOC_CLK_ENABLE() ((void)0)
#define __HAL_RCC_GPIOD_CLK_ENABLE() ((void)0)
#define __HAL_RCC_USART3_CLK_ENABLE() ((void)0)
#define __HAL_RCC_USART3_FORCE_RESET() ((void)0)
#define __HAL_RCC_USART3_RELEASE_RESET() ((void)0)
#define __HAL_UART_CLEAR_FLAG(h,f) ((h)->Instance->ICR=(f))
#define __HAL_UART_DISABLE(h) ((h)->Instance->CR1=0)
uint32_t HAL_GetTick(void);
void HAL_GPIO_Init(GPIO_TypeDef *,GPIO_InitTypeDef *);
void HAL_GPIO_WritePin(GPIO_TypeDef *,uint16_t,int);
int HAL_GPIO_ReadPin(GPIO_TypeDef *,uint16_t);
int HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef *);
uint32_t HAL_RCCEx_GetPeriphCLKFreq(uint64_t);
int HAL_UART_Init(UART_HandleTypeDef *);
int HAL_UARTEx_EnableFifoMode(UART_HandleTypeDef *);
#define USART6 (&usart)
#define GPIO_PIN_6 (1U<<6)
#define GPIO_PIN_7 (1U<<7)
#define GPIO_AF7_USART6 7
#define USART6_IRQn 71
#define RCC_PERIPHCLK_USART6 4
#define RCC_USART16CLKSOURCE_HSI 3
#define __HAL_RCC_USART6_CLK_ENABLE() ((void)0)
#define __HAL_RCC_USART6_FORCE_RESET() ((void)0)
#define __HAL_RCC_USART6_RELEASE_RESET() ((void)0)
#define USART_ICR_PECF 1U
#define USART_ICR_FECF 2U
#define USART_ICR_NECF 4U
#define USART_ICR_ORECF 8U
#define USART_CR1_PEIE (1U<<8)
#define USART_CR1_RXNEIE_RXFNEIE (1U<<5)
#define USART_CR3_EIE 1U
uint32_t mock_read(uint32_t *);
void mock_write(uint32_t *,uint32_t);
#define READ_REG(r) mock_read(&(r))
#define WRITE_REG(r,v) mock_write(&(r),(v))
#define __DMB() ((void)0)
extern uint32_t masked;
#define __get_PRIMASK() (masked)
#define __disable_irq() (masked=1)
#define __set_PRIMASK(v) (masked=(v))
void HAL_NVIC_SetPriority(int,int,int);
void HAL_NVIC_ClearPendingIRQ(int);
void HAL_NVIC_EnableIRQ(int);
#endif
