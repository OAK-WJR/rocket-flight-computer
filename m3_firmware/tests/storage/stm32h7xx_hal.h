/* Scripted HAL; not on ARM include paths. */
#ifndef STORAGE_TEST_HAL
#define STORAGE_TEST_HAL
#include <stdint.h>
typedef struct { uint32_t ODR; } GPIO_TypeDef;
extern GPIO_TypeDef gb,gd,ge;
#define GPIOB (&gb)
#define GPIOD (&gd)
#define GPIOE (&ge)
#define QUADSPI ((void *)0x52005000)
#define GPIO_PIN_2 4
#define GPIO_PIN_6 64
#define GPIO_PIN_11 2048
#define GPIO_PIN_12 4096
#define GPIO_PIN_13 8192
#define GPIO_PIN_SET 1
#define GPIO_NOPULL 0
#define GPIO_MODE_OUTPUT_PP 1
#define GPIO_MODE_AF_PP 2
#define GPIO_SPEED_FREQ_LOW 0
#define GPIO_SPEED_FREQ_MEDIUM 1
#define GPIO_AF9_QUADSPI 9
#define GPIO_AF10_QUADSPI 10
#define RCC_PERIPHCLK_QSPI 1
#define RCC_PERIPHCLK_CKPER 2
#define RCC_QSPICLKSOURCE_CLKP 3
#define RCC_CLKPSOURCE_HSI 4
#define QSPI_SAMPLE_SHIFTING_NONE 0
#define QSPI_CS_HIGH_TIME_4_CYCLE 3
#define QSPI_CLOCK_MODE_0 0
#define QSPI_FLASH_ID_1 0
#define QSPI_DUALFLASH_DISABLE 0
#define QSPI_INSTRUCTION_1_LINE 1
#define QSPI_ADDRESS_NONE 0
#define QSPI_ADDRESS_1_LINE 1
#define QSPI_ADDRESS_24_BITS 2
#define QSPI_ALTERNATE_BYTES_NONE 0
#define QSPI_ALTERNATE_BYTES_1_LINE 1
#define QSPI_ALTERNATE_BYTES_32_BITS 3
#define QSPI_DATA_NONE 0
#define QSPI_DATA_1_LINE 1
#define QSPI_DATA_4_LINES 3
#define QSPI_DDR_MODE_DISABLE 0
#define QSPI_DDR_HHC_ANALOG_DELAY 0
#define QSPI_SIOO_INST_EVERY_CMD 0
#define QSPI_TIMEOUT_COUNTER_DISABLE 0
#define HAL_OK 0
typedef int HAL_StatusTypeDef;
typedef struct {uint32_t Pin,Mode,Pull,Speed,Alternate;} GPIO_InitTypeDef;
typedef struct {uint64_t PeriphClockSelection;uint32_t QspiClockSelection,CkperClockSelection;} RCC_PeriphCLKInitTypeDef;
typedef struct {
 void *Instance;
 uint32_t Timeout;
 struct {uint32_t ClockPrescaler,FifoThreshold,SampleShifting,FlashSize,ChipSelectHighTime,ClockMode,FlashID,DualFlash;} Init;
} QSPI_HandleTypeDef;
typedef struct {
 uint32_t Instruction,Address,AlternateBytes,AddressSize,AlternateBytesSize,DummyCycles,InstructionMode,AddressMode,
 AlternateByteMode,DataMode,NbData,DdrMode,DdrHoldHalfCycle,SIOOMode;
} QSPI_CommandTypeDef;
typedef struct {uint32_t TimeOutPeriod,TimeOutActivation;} QSPI_MemoryMappedTypeDef;
#define __HAL_RCC_GPIOB_CLK_ENABLE() ((void)0)
#define __HAL_RCC_GPIOD_CLK_ENABLE() ((void)0)
#define __HAL_RCC_GPIOE_CLK_ENABLE() ((void)0)
#define __HAL_RCC_QSPI_CLK_ENABLE() ((void)0)
#define __HAL_RCC_QSPI_FORCE_RESET() ((void)0)
#define __HAL_RCC_QSPI_RELEASE_RESET() ((void)0)
uint32_t HAL_GetTick(void);
void HAL_Delay(uint32_t);
void HAL_GPIO_WritePin(GPIO_TypeDef *,uint16_t,int);
int HAL_GPIO_ReadPin(GPIO_TypeDef *,uint16_t);
void HAL_GPIO_Init(GPIO_TypeDef *,GPIO_InitTypeDef *);
int HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef *);
uint32_t HAL_RCCEx_GetPeriphCLKFreq(uint64_t);
int HAL_QSPI_Init(QSPI_HandleTypeDef *);
uint32_t HAL_QSPI_GetError(QSPI_HandleTypeDef *);
int HAL_QSPI_Command(QSPI_HandleTypeDef *,QSPI_CommandTypeDef *,uint32_t);
int HAL_QSPI_Receive(QSPI_HandleTypeDef *,uint8_t *,uint32_t);
int HAL_QSPI_Transmit(QSPI_HandleTypeDef *,uint8_t *,uint32_t);
int HAL_QSPI_MemoryMapped(QSPI_HandleTypeDef *,QSPI_CommandTypeDef *,QSPI_MemoryMappedTypeDef *);
int HAL_QSPI_Abort(QSPI_HandleTypeDef *);
void HAL_QSPI_SetTimeout(QSPI_HandleTypeDef *,uint32_t);
#endif
