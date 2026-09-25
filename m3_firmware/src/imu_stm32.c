#ifdef M3_IMU_SAMPLES
#include "stm32h7xx_hal.h"
#include "imu.h"
#include <string.h>

static SPI_HandleTypeDef spi;
static ImuDevice device;
static uint32_t ticks(void *ctx) { (void)ctx; return HAL_GetTick(); }
static void pause_ms(void *ctx,uint32_t ms) { (void)ctx; HAL_Delay(ms); }
static int initialize(void *ctx,uint32_t *bus_hz,uint32_t *detail) {
    (void)ctx; *bus_hz=0; *detail=0;
    __HAL_RCC_GPIOB_CLK_ENABLE();
    GPIO_InitTypeDef g={0};
    /* CS stays high through clock/pin setup and every unsuccessful operation. */
    HAL_GPIO_WritePin(GPIOB,GPIO_PIN_7,GPIO_PIN_SET);
    g.Pin=GPIO_PIN_7; g.Mode=GPIO_MODE_OUTPUT_PP; g.Pull=GPIO_NOPULL; g.Speed=GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOB,&g);
    if (HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_7)!=GPIO_PIN_SET) { *detail=0x40000001U; return IMU_SPI_INIT; }
    RCC_PeriphCLKInitTypeDef clk={0};
    clk.PeriphClockSelection=RCC_PERIPHCLK_SPI1 | RCC_PERIPHCLK_CKPER;
    clk.Spi123ClockSelection=RCC_SPI123CLKSOURCE_CLKP;
    clk.CkperClockSelection=RCC_CLKPSOURCE_HSI;
    HAL_StatusTypeDef rc=HAL_RCCEx_PeriphCLKConfig(&clk);
    if (rc!=HAL_OK) { *detail=(uint32_t)rc<<24; return IMU_CLOCK; }
    uint32_t kernel=HAL_RCCEx_GetPeriphCLKFreq(RCC_PERIPHCLK_SPI1);
    if (kernel!=64000000U) { *detail=0x40000002U; return IMU_CLOCK; }
    __HAL_RCC_SPI1_CLK_ENABLE(); __HAL_RCC_SPI1_FORCE_RESET(); __HAL_RCC_SPI1_RELEASE_RESET();
    memset(&spi,0,sizeof(spi)); spi.Instance=SPI1;
    spi.Init.Mode=SPI_MODE_MASTER; spi.Init.Direction=SPI_DIRECTION_2LINES;
    spi.Init.DataSize=SPI_DATASIZE_8BIT; spi.Init.CLKPolarity=SPI_POLARITY_LOW;
    spi.Init.CLKPhase=SPI_PHASE_1EDGE; spi.Init.NSS=SPI_NSS_SOFT;
    spi.Init.BaudRatePrescaler=SPI_BAUDRATEPRESCALER_64; spi.Init.FirstBit=SPI_FIRSTBIT_MSB;
    spi.Init.TIMode=SPI_TIMODE_DISABLE; spi.Init.CRCCalculation=SPI_CRCCALCULATION_DISABLE;
    spi.Init.CRCLength=SPI_CRC_LENGTH_DATASIZE; spi.Init.NSSPMode=SPI_NSS_PULSE_DISABLE;
    spi.Init.NSSPolarity=SPI_NSS_POLARITY_LOW; spi.Init.FifoThreshold=SPI_FIFO_THRESHOLD_01DATA;
    spi.Init.TxCRCInitializationPattern=SPI_CRC_INITIALIZATION_ALL_ZERO_PATTERN;
    spi.Init.RxCRCInitializationPattern=SPI_CRC_INITIALIZATION_ALL_ZERO_PATTERN;
    spi.Init.MasterSSIdleness=SPI_MASTER_SS_IDLENESS_00CYCLE;
    spi.Init.MasterInterDataIdleness=SPI_MASTER_INTERDATA_IDLENESS_00CYCLE;
    spi.Init.MasterReceiverAutoSusp=SPI_MASTER_RX_AUTOSUSP_DISABLE;
    spi.Init.MasterKeepIOState=SPI_MASTER_KEEP_IO_STATE_ENABLE;
    spi.Init.IOSwap=SPI_IO_SWAP_DISABLE;
    rc=HAL_SPI_Init(&spi);
    if (rc!=HAL_OK) { *detail=((uint32_t)rc<<24) | HAL_SPI_GetError(&spi); return IMU_SPI_INIT; }
    if ((SPI1->CFG1 & (SPI_CFG1_MBR | SPI_CFG1_DSIZE)) !=
        (SPI_BAUDRATEPRESCALER_64 | SPI_DATASIZE_8BIT) ||
        (SPI1->CFG2 & (SPI_CFG2_CPOL | SPI_CFG2_CPHA | SPI_CFG2_LSBFRST))) {
        *detail=0x40000003U; return IMU_SPI_INIT;
    }
    HAL_GPIO_WritePin(GPIOB,GPIO_PIN_3 | GPIO_PIN_5,GPIO_PIN_RESET);
    g.Pin=GPIO_PIN_3 | GPIO_PIN_4 | GPIO_PIN_5; g.Mode=GPIO_MODE_AF_PP;
    g.Alternate=GPIO_AF5_SPI1; g.Speed=GPIO_SPEED_FREQ_LOW; HAL_GPIO_Init(GPIOB,&g);
    *bus_hz=kernel/64U; /* nominal; no independent clock measurement */
    return IMU_OK;
}
static int exchange(void *ctx,const uint8_t *tx,uint8_t *rx,size_t n,uint32_t *detail) {
    (void)ctx; *detail=0;
    if (n<2 || n>15) { *detail=0x40000004U; return 1; }
    HAL_GPIO_WritePin(GPIOB,GPIO_PIN_7,GPIO_PIN_RESET);
    HAL_StatusTypeDef rc=HAL_SPI_TransmitReceive(&spi,tx,rx,(uint16_t)n,10);
    uint32_t e=HAL_SPI_GetError(&spi);
    HAL_GPIO_WritePin(GPIOB,GPIO_PIN_7,GPIO_PIN_SET);
    *detail=((uint32_t)rc<<24) | e;
    if (HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_7)!=GPIO_PIN_SET) *detail|=0x40000001U;
    return rc!=HAL_OK || *detail!=0;
}
static const ImuIO io={NULL,ticks,pause_ms,initialize,exchange};
void bench_imu_initialize(BenchIMU *r) { imu_begin(&device,&io,r); }
void bench_imu_sample(BenchIMU *r) { imu_sample(&device,r); }
#endif
