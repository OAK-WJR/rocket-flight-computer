#include <stdint.h>
typedef int IRQn_Type;
enum { EXTI0_IRQn=6,EXTI1_IRQn=7,EXTI4_IRQn=10,EXTI9_5_IRQn=23 };
typedef struct {uint32_t MODER,PUPDR,IDR,ODR;} GPIO_TypeDef;
typedef struct {uint32_t AHB4ENR,APB4ENR;} RCC_TypeDef;
typedef struct {uint32_t EXTICR[4];} SYSCFG_TypeDef;
typedef struct {uint32_t IMR1,FTSR1,RTSR1,PR1;} EXTI_TypeDef;
typedef struct {uint32_t Pin,Mode,Pull;} GPIO_InitTypeDef;
extern GPIO_TypeDef gd;
extern RCC_TypeDef rc;
extern SYSCFG_TypeDef sc;
extern EXTI_TypeDef ex;
extern uint32_t masks,now;
#define GPIOD (&gd)
#define RCC (&rc)
#define SYSCFG (&sc)
#define EXTI (&ex)
#define RCC_AHB4ENR_GPIODEN 8U
#define RCC_APB4ENR_SYSCFGEN 2U
#define GPIO_MODE_IT_FALLING 1U
#define GPIO_MODE_IT_RISING_FALLING 2U
#define GPIO_NOPULL 0U
#define __HAL_RCC_GPIOD_CLK_ENABLE() (rc.AHB4ENR|=8U)
#define __HAL_RCC_SYSCFG_CLK_ENABLE() (rc.APB4ENR|=2U)
#define __get_PRIMASK() masks
#define __disable_irq() (masks=1U)
#define __set_PRIMASK(x) (masks=(x))
uint32_t HAL_GetTick(void);
void HAL_GPIO_Init(GPIO_TypeDef *,GPIO_InitTypeDef *);
void HAL_NVIC_SetPriority(IRQn_Type,unsigned,unsigned);
void HAL_NVIC_ClearPendingIRQ(IRQn_Type);
void HAL_NVIC_EnableIRQ(IRQn_Type);
int NVIC_GetEnableIRQ(IRQn_Type);
