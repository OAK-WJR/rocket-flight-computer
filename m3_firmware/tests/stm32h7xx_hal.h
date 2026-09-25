/* HOST TEST DOUBLE ONLY. Never included by the ARM build. */
#include <stdint.h>
#include <stddef.h>
typedef struct { uint32_t output; } GPIO_TypeDef;
extern GPIO_TypeDef gb, gd, ge;
#define GPIOB (&gb)
#define GPIOD (&gd)
#define GPIOE (&ge)
#define GPIO_PIN_2 (1U<<2)
#define GPIO_PIN_3 (1U<<3)
#define GPIO_PIN_4 (1U<<4)
#define GPIO_PIN_5 (1U<<5)
#define GPIO_PIN_6 (1U<<6)
#define GPIO_PIN_7 (1U<<7)
#define GPIO_PIN_8 (1U<<8)
#define GPIO_PIN_9 (1U<<9)
#define GPIO_PIN_11 (1U<<11)
#define GPIO_PIN_12 (1U<<12)
#define GPIO_PIN_13 (1U<<13)
#define GPIO_PIN_SET 1
#define GPIO_PIN_RESET 0
#define GPIO_MODE_INPUT 0
#define GPIO_MODE_OUTPUT_PP 1
#define GPIO_MODE_OUTPUT_OD 2
#define GPIO_NOPULL 0
#define GPIO_SPEED_FREQ_LOW 0
typedef struct { uint32_t Pin, Mode, Pull, Speed; } GPIO_InitTypeDef;
typedef struct { uint32_t RSR, CR, CFGR; } RCC_TypeDef;
typedef struct { uint32_t IDCODE; } DBG_TypeDef;
extern RCC_TypeDef rcc;
extern DBG_TypeDef dbg;
extern uint32_t uid[3],SystemCoreClock;
#define RCC (&rcc)
#define DBGMCU (&dbg)
#define UID_BASE ((uintptr_t)uid)
#define D1_AXISRAM_BASE 0x24000000U
#define RCC_CFGR_SWS 0x38U
#define RCC_CFGR_SWS_HSI 0
#define RCC_CR_HSERDY (1U<<17)
#define RCC_OSCILLATORTYPE_HSE 1
#define RCC_HSE_ON 1
#define RCC_HSE_OFF 0
#define RCC_PLL_NONE 0
typedef struct { uint32_t OscillatorType,HSEState; struct { uint32_t PLLState; } PLL; } RCC_OscInitTypeDef;
typedef int HAL_StatusTypeDef;
#define HAL_OK 0
#define __DMB() ((void)0)
#define __DSB() ((void)0)
#define __NOP() ((void)0)
#define __HAL_RCC_GPIOB_CLK_ENABLE() ((void)0)
#define __HAL_RCC_GPIOD_CLK_ENABLE() ((void)0)
#define __HAL_RCC_GPIOE_CLK_ENABLE() ((void)0)
uint32_t HAL_GetTick(void);
void HAL_Delay(uint32_t delay);
void HAL_IncTick(void);
void HAL_Init(void);
void SystemCoreClockUpdate(void);
void HAL_GPIO_Init(GPIO_TypeDef *, GPIO_InitTypeDef *);
void HAL_GPIO_WritePin(GPIO_TypeDef *, uint16_t, int);
int HAL_GPIO_ReadPin(GPIO_TypeDef *, uint16_t);
void HAL_GPIO_TogglePin(GPIO_TypeDef *,uint16_t);
HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *);
