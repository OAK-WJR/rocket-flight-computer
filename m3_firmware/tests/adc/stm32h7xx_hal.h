/* HOST TEST ONLY: scripted ADC peripheral calls, not an electrical model. */
#include <stdint.h>
typedef struct { uint32_t output; } GPIO_TypeDef;
extern GPIO_TypeDef gc;
#define GPIOC (&gc)
#define GPIO_PIN_2 4U
#define GPIO_PIN_3 8U
#define GPIO_MODE_ANALOG 3U
#define GPIO_NOPULL 0U
typedef struct {uint32_t Pin,Mode,Pull,Speed;} GPIO_InitTypeDef;
typedef struct {uint32_t PMCR;} SYSCFG_TypeDef;
extern SYSCFG_TypeDef sy;
#define SYSCFG (&sy)
#define SYSCFG_PMCR_PC2SO (1U<<26)
#define SYSCFG_PMCR_PC3SO (1U<<27)
#define SYSCFG_SWITCH_PC2 SYSCFG_PMCR_PC2SO
#define SYSCFG_SWITCH_PC3 SYSCFG_PMCR_PC3SO
#define SYSCFG_SWITCH_PC2_OPEN SYSCFG_PMCR_PC2SO
#define SYSCFG_SWITCH_PC3_OPEN SYSCFG_PMCR_PC3SO
typedef struct {uint32_t PCSEL,CFGR,CR;} ADC_TypeDef;
extern ADC_TypeDef a3;
#define ADC3 (&a3)
typedef struct {uint32_t CCR;} ADC_Common_TypeDef;
extern ADC_Common_TypeDef acommon;
#define ADC3_COMMON (&acommon)
extern uint16_t factory_cal;
#define VREFINT_CAL_ADDR (&factory_cal)
typedef struct {uint32_t ClockPrescaler,Resolution,ScanConvMode,EOCSelection,NbrOfConversion,
 NbrOfDiscConversion,ExternalTrigConv,ExternalTrigConvEdge,ConversionDataManagement,
 Overrun,LeftBitShift;} ADC_InitTypeDef;
typedef struct {ADC_TypeDef *Instance;ADC_InitTypeDef Init;uint32_t ErrorCode;} ADC_HandleTypeDef;
typedef struct {uint32_t Channel,Rank,SamplingTime,SingleDiff,OffsetNumber;} ADC_ChannelConfTypeDef;
#define DISABLE 0
#define RCC_CLKPSOURCE_HSI 1
#define RCC_ADCCLKSOURCE_CLKP 2
#define RCC_PERIPHCLK_ADC 3
#define ADC_CLOCK_ASYNC_DIV16 16
#define ADC_RESOLUTION_16B 16
#define ADC_EOC_SINGLE_CONV 1
#define ADC_SOFTWARE_START 0
#define ADC_EXTERNALTRIGCONVEDGE_NONE 0
#define ADC_CONVERSIONDATA_DR 0
#define ADC_OVR_DATA_PRESERVED 0
#define ADC_LEFTBITSHIFT_NONE 0
#define ADC_CALIB_OFFSET_LINEARITY 1
#define ADC_SINGLE_ENDED 0
#define ADC_REGULAR_RANK_1 1
#define ADC_SAMPLETIME_810CYCLES_5 1621
#define ADC_OFFSET_NONE 0
#define ADC_CHANNEL_VREFINT 19
#define ADC_CHANNEL_0 0
#define ADC_CHANNEL_1 1
#define HAL_OK 0
#define HAL_ERROR 1
typedef int HAL_StatusTypeDef;
#define __HAL_RCC_GPIOC_CLK_ENABLE() ((void)0)
#define __HAL_RCC_SYSCFG_CLK_ENABLE() ((void)0)
#define __HAL_RCC_ADC3_CLK_ENABLE() ((void)0)
#define __HAL_RCC_ADC3_FORCE_RESET() ((void)0)
#define __HAL_RCC_ADC3_RELEASE_RESET() ((void)0)
void clock_config(int);
#define __HAL_RCC_CLKP_CONFIG(v) clock_config(v)
#define __HAL_RCC_ADC_CONFIG(v) clock_config(v)
uint32_t HAL_GetTick(void);
void HAL_Delay(uint32_t);
void HAL_GPIO_Init(GPIO_TypeDef *,GPIO_InitTypeDef *);
void HAL_SYSCFG_AnalogSwitchConfig(uint32_t,uint32_t);
uint32_t HAL_RCCEx_GetPeriphCLKFreq(uint32_t);
HAL_StatusTypeDef HAL_ADC_Init(ADC_HandleTypeDef *);
void LL_ADC_StartCalibration(ADC_TypeDef *,uint32_t,uint32_t);
uint32_t LL_ADC_IsCalibrationOnGoing(ADC_TypeDef *);
HAL_StatusTypeDef HAL_ADC_ConfigChannel(ADC_HandleTypeDef *,ADC_ChannelConfTypeDef *);
HAL_StatusTypeDef HAL_ADC_Start(ADC_HandleTypeDef *);
HAL_StatusTypeDef HAL_ADC_PollForConversion(ADC_HandleTypeDef *,uint32_t);
uint32_t HAL_ADC_GetValue(ADC_HandleTypeDef *);
HAL_StatusTypeDef HAL_ADC_Stop(ADC_HandleTypeDef *);
