/* Scripted HAL only; never on the ARM include path. */
#ifndef IMU_TEST_HAL_H
#define IMU_TEST_HAL_H
#include <stdint.h>
#include <stddef.h>
typedef struct { uint32_t IDR,ODR; } GPIO_TypeDef;
typedef struct { uint32_t CFG1,CFG2; } SPI_TypeDef;
extern GPIO_TypeDef gb;
extern SPI_TypeDef bus;
#define GPIOB (&gb)
#define SPI1 (&bus)
#define GPIO_PIN_3 8U
#define GPIO_PIN_4 16U
#define GPIO_PIN_5 32U
#define GPIO_PIN_7 128U
#define GPIO_PIN_RESET 0
#define GPIO_PIN_SET 1
#define GPIO_NOPULL 0
#define GPIO_SPEED_FREQ_LOW 0
#define GPIO_MODE_OUTPUT_PP 1
#define GPIO_MODE_AF_PP 2
#define GPIO_AF5_SPI1 5
#define RCC_PERIPHCLK_SPI1 8ULL
#define RCC_PERIPHCLK_CKPER 16ULL
#define RCC_SPI123CLKSOURCE_CLKP 4
#define RCC_CLKPSOURCE_HSI 2
#define SPI_MODE_MASTER 1
#define SPI_DIRECTION_2LINES 0
#define SPI_DATASIZE_8BIT 7
#define SPI_POLARITY_LOW 0
#define SPI_PHASE_1EDGE 0
#define SPI_NSS_SOFT 8
#define SPI_BAUDRATEPRESCALER_64 (5UL<<28)
#define SPI_FIRSTBIT_MSB 0
#define SPI_TIMODE_DISABLE 0
#define SPI_CRCCALCULATION_DISABLE 0
#define SPI_CRC_LENGTH_DATASIZE 0
#define SPI_NSS_PULSE_DISABLE 0
#define SPI_NSS_POLARITY_LOW 0
#define SPI_FIFO_THRESHOLD_01DATA 0
#define SPI_CRC_INITIALIZATION_ALL_ZERO_PATTERN 0
#define SPI_MASTER_SS_IDLENESS_00CYCLE 0
#define SPI_MASTER_INTERDATA_IDLENESS_00CYCLE 0
#define SPI_MASTER_RX_AUTOSUSP_DISABLE 0
#define SPI_MASTER_KEEP_IO_STATE_ENABLE 8
#define SPI_IO_SWAP_DISABLE 0
#define SPI_CFG1_MBR (7UL<<28)
#define SPI_CFG1_DSIZE 31U
#define SPI_CFG2_CPOL 1U
#define SPI_CFG2_CPHA 2U
#define SPI_CFG2_LSBFRST 4U
typedef int HAL_StatusTypeDef;
#define HAL_OK 0
typedef struct { uint32_t Pin,Mode,Pull,Speed,Alternate; } GPIO_InitTypeDef;
typedef struct { uint64_t PeriphClockSelection; uint32_t Spi123ClockSelection,CkperClockSelection; } RCC_PeriphCLKInitTypeDef;
typedef struct {
    SPI_TypeDef *Instance;
    struct { uint32_t Mode,Direction,DataSize,CLKPolarity,CLKPhase,NSS,BaudRatePrescaler,FirstBit,
      TIMode,CRCCalculation,CRCPolynomial,CRCLength,NSSPMode,NSSPolarity,FifoThreshold,
      TxCRCInitializationPattern,RxCRCInitializationPattern,MasterSSIdleness,MasterInterDataIdleness,
      MasterReceiverAutoSusp,MasterKeepIOState,IOSwap; } Init;
} SPI_HandleTypeDef;
#define __HAL_RCC_GPIOB_CLK_ENABLE() ((void)0)
#define __HAL_RCC_SPI1_CLK_ENABLE() ((void)0)
#define __HAL_RCC_SPI1_FORCE_RESET() ((void)0)
#define __HAL_RCC_SPI1_RELEASE_RESET() ((void)0)
uint32_t HAL_GetTick(void);
void HAL_Delay(uint32_t);
void HAL_GPIO_Init(GPIO_TypeDef *,GPIO_InitTypeDef *);
void HAL_GPIO_WritePin(GPIO_TypeDef *,uint16_t,int);
int HAL_GPIO_ReadPin(GPIO_TypeDef *,uint16_t);
int HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef *);
uint32_t HAL_RCCEx_GetPeriphCLKFreq(uint64_t);
int HAL_SPI_Init(SPI_HandleTypeDef *);
int HAL_SPI_TransmitReceive(SPI_HandleTypeDef *,const uint8_t *,uint8_t *,uint16_t,uint32_t);
uint32_t HAL_SPI_GetError(SPI_HandleTypeDef *);
#endif
