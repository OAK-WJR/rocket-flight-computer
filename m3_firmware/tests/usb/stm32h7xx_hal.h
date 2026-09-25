/* Test-only scripted peripherals; never part of an ARM build. */
#ifndef USB_TEST_HAL
#define USB_TEST_HAL
#include <stdint.h>
#include <stddef.h>
typedef struct{uint32_t CR,PLLCKSELR,PLL3DIVR,D2CCIP2R;} RCC_TypeDef;
typedef struct{uint32_t IDR;} GPIO_TypeDef;
typedef struct{uint32_t GCCFG,DCTL;} USB_TypeDef;
typedef struct{uint32_t DCTL;} USB_OTG_DeviceTypeDef;
extern RCC_TypeDef rr;extern GPIO_TypeDef ga,gd;extern USB_TypeDef uu;
extern uint32_t SystemCoreClock;
extern uint8_t usb_test_uid[12];
#define UID_BASE usb_test_uid
#define RCC (&rr)
#define GPIOA (&ga)
#define GPIOD (&gd)
#define USB2_OTG_FS (&uu)
#define USB2_OTG_FS_PERIPH_BASE ((uintptr_t)&uu)
#define USB_OTG_DEVICE_BASE offsetof(USB_TypeDef,DCTL)
#define RCC_CR_HSERDY (1U<<17)
#define RCC_CR_PLL1ON (1U<<24)
#define RCC_CR_PLL2ON (1U<<26)
#define RCC_CR_PLL3ON (1U<<28)
#define RCC_CR_PLL3RDY (1U<<29)
#define RCC_PLLSOURCE_HSE 3
#define RCC_PERIPHCLK_USB 4
#define RCC_USBCLKSOURCE_PLL3 8
#define RCC_PLL3VCIRANGE_0 0
#define RCC_PLL3VCOMEDIUM 1
#define GPIO_PIN_15 (1<<15)
#define GPIO_PIN_11 (1<<11)
#define GPIO_PIN_12 (1<<12)
#define GPIO_MODE_INPUT 0
#define GPIO_MODE_AF_PP 2
#define GPIO_NOPULL 0
#define GPIO_PIN_SET 1
#define GPIO_SPEED_FREQ_HIGH 2
#define GPIO_AF10_OTG2_FS 10
#define OTG_FS_IRQn 101
#define HAL_MAX_DELAY 0xffffffffU
#define HAL_OK 0
typedef struct{uint32_t Pin,Mode,Pull,Speed,Alternate;} GPIO_InitTypeDef;
typedef struct{uint32_t PLL3M,PLL3N,PLL3P,PLL3Q,PLL3R,PLL3RGE,PLL3VCOSEL,PLL3FRACN;} PLL3Init;
typedef struct{uint32_t PeriphClockSelection,UsbClockSelection;PLL3Init PLL3;} RCC_PeriphCLKInitTypeDef;
#define __HAL_RCC_GPIOA_CLK_ENABLE() ((void)0)
#define __HAL_RCC_GPIOD_CLK_ENABLE() ((void)0)
#define __HAL_RCC_PLL_PLLSOURCE_CONFIG(x) (rr.PLLCKSELR=(x))
#define __HAL_RCC_USB2_OTG_FS_CLK_ENABLE() ((void)0)
#define __HAL_RCC_USB2_OTG_FS_FORCE_RESET() ((void)0)
#define __HAL_RCC_USB2_OTG_FS_RELEASE_RESET() ((void)0)
#define __NOP() ((void)0)
uint32_t HAL_GetTick(void);
int HAL_GPIO_ReadPin(GPIO_TypeDef *,uint32_t);
void HAL_GPIO_Init(GPIO_TypeDef *,GPIO_InitTypeDef *);
int HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef *);
uint32_t HAL_RCCEx_GetPeriphCLKFreq(uint32_t);
void HAL_PWREx_EnableUSBVoltageDetector(void);
void HAL_NVIC_SetPriority(int,int,int);
#endif
