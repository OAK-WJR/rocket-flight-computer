#ifdef M3_STORAGE
#include "stm32h7xx_hal.h"
#include "storage.h"
#include <string.h>
static QSPI_HandleTypeDef qspi;
static Storage store;
#ifdef M3_USB
static unsigned storage_busy;
#endif
static uint32_t ticks(void *ctx){(void)ctx;return HAL_GetTick();}
static void delay(void *ctx,uint32_t ms){(void)ctx;HAL_Delay(ms);}
static void progress(void *ctx,const BenchStorage *r){(void)ctx;bench_storage_progress(r);}
static int init(void *ctx,uint32_t *hz,uint32_t *detail) {
    (void)ctx;*hz=0;*detail=0;
    __HAL_RCC_GPIOB_CLK_ENABLE();__HAL_RCC_GPIOD_CLK_ENABLE();__HAL_RCC_GPIOE_CLK_ENABLE();
    GPIO_InitTypeDef g={0};
    HAL_GPIO_WritePin(GPIOB,GPIO_PIN_6,GPIO_PIN_SET);
    g.Pin=GPIO_PIN_6;g.Mode=GPIO_MODE_OUTPUT_PP;g.Pull=GPIO_NOPULL;g.Speed=GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOB,&g);
    if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_6)!=GPIO_PIN_SET){*detail=0x40000001;return 1;}
    RCC_PeriphCLKInitTypeDef clk={0};
    clk.PeriphClockSelection=RCC_PERIPHCLK_QSPI|RCC_PERIPHCLK_CKPER;
    clk.QspiClockSelection=RCC_QSPICLKSOURCE_CLKP;clk.CkperClockSelection=RCC_CLKPSOURCE_HSI;
    HAL_StatusTypeDef rc=HAL_RCCEx_PeriphCLKConfig(&clk);
    if(rc!=HAL_OK){*detail=(uint32_t)rc<<24;return 1;}
    uint32_t kernel=HAL_RCCEx_GetPeriphCLKFreq(RCC_PERIPHCLK_QSPI);
    if(kernel!=64000000U){*detail=0x40000002;return 1;}
    __HAL_RCC_QSPI_CLK_ENABLE();__HAL_RCC_QSPI_FORCE_RESET();__HAL_RCC_QSPI_RELEASE_RESET();
    memset(&qspi,0,sizeof(qspi));qspi.Instance=QUADSPI;
    qspi.Init.ClockPrescaler=7;qspi.Init.FifoThreshold=4;
    qspi.Init.SampleShifting=QSPI_SAMPLE_SHIFTING_NONE;qspi.Init.FlashSize=23;
    qspi.Init.ChipSelectHighTime=QSPI_CS_HIGH_TIME_4_CYCLE;qspi.Init.ClockMode=QSPI_CLOCK_MODE_0;
    qspi.Init.FlashID=QSPI_FLASH_ID_1;qspi.Init.DualFlash=QSPI_DUALFLASH_DISABLE;
    rc=HAL_QSPI_Init(&qspi);
    if(rc!=HAL_OK){*detail=((uint32_t)rc<<24)|HAL_QSPI_GetError(&qspi);return 1;}
#ifdef M3_USB
    /* Abort/remap use the handle timeout, not Command's explicit 20ms. */
    HAL_QSPI_SetTimeout(&qspi,20);
#endif
    /* DS12110 Rev5 Tables10/12/13: PB6 is AF10, all other pins AF9. */
    g.Mode=GPIO_MODE_AF_PP;g.Speed=GPIO_SPEED_FREQ_MEDIUM;g.Alternate=GPIO_AF9_QUADSPI;
    g.Pin=GPIO_PIN_2;HAL_GPIO_Init(GPIOB,&g);HAL_GPIO_Init(GPIOE,&g);
    g.Pin=GPIO_PIN_11|GPIO_PIN_12|GPIO_PIN_13;HAL_GPIO_Init(GPIOD,&g);
    g.Pin=GPIO_PIN_6;g.Alternate=GPIO_AF10_QUADSPI;HAL_GPIO_Init(GPIOB,&g);
    *hz=kernel/8U;return 0;
}
static QSPI_CommandTypeDef base(uint8_t op,int32_t address,unsigned dummy,int quad,size_t n) {
    QSPI_CommandTypeDef c={0};c.Instruction=op;c.InstructionMode=QSPI_INSTRUCTION_1_LINE;
    c.AddressMode=address<0?QSPI_ADDRESS_NONE:QSPI_ADDRESS_1_LINE;
    c.AddressSize=QSPI_ADDRESS_24_BITS;c.Address=address<0?0:(uint32_t)address;
    c.AlternateByteMode=QSPI_ALTERNATE_BYTES_NONE;
    if(op==0x4b){c.AlternateByteMode=QSPI_ALTERNATE_BYTES_1_LINE;c.AlternateBytesSize=QSPI_ALTERNATE_BYTES_32_BITS;}
    c.DataMode=n?(quad?QSPI_DATA_4_LINES:QSPI_DATA_1_LINE):QSPI_DATA_NONE;
    c.NbData=(uint32_t)n;c.DummyCycles=dummy;c.DdrMode=QSPI_DDR_MODE_DISABLE;
    c.DdrHoldHalfCycle=QSPI_DDR_HHC_ANALOG_DELAY;c.SIOOMode=QSPI_SIOO_INST_EVERY_CMD;
    return c;
}
static int exchange(void *ctx,uint8_t op,int32_t address,unsigned dummy,int quad,
                    const uint8_t *tx,uint8_t *rx,size_t n,uint32_t *detail) {
    (void)ctx;*detail=0;
    int allowed=0;
    if(rx&&!tx) {
        allowed=((op==5||op==0x35||op==0x15)&&address==-1&&!dummy&&!quad&&n==1)||
                (op==0x9f&&address==-1&&!dummy&&!quad&&n==3)||
                (op==0x4b&&address==-1&&!dummy&&!quad&&n==8)||
                (op==0x5a&&address==0&&dummy==8&&!quad&&n==8)||
                ((op==3||op==0x6b)&&address>=0&&n&&n<=STORE_SECTOR&&
                 (uint32_t)address<=STORE_BYTES-n&&dummy==(op==3?0U:8U)&&quad==(op==0x6b));
    }
#if M3_STORAGE_RECORD
    if(!rx)allowed|=(op==6&&address==-1&&!dummy&&!quad&&!tx&&!n)||
        (op==2&&tx&&address>=0&&!(address%STORE_PAGE)&&
         (uint32_t)address<=STORE_BYTES-STORE_PAGE&&!dummy&&!quad&&n==STORE_PAGE);
#else
    if(tx)allowed=0;
#endif
    if(!allowed){*detail=0x40000003U;return 1;}
    QSPI_CommandTypeDef c=base(op,address,dummy,quad,n);
    HAL_StatusTypeDef rc=HAL_QSPI_Command(&qspi,&c,20);
    if(rc==HAL_OK&&rx)rc=HAL_QSPI_Receive(&qspi,rx,20);
#if M3_STORAGE_RECORD
    if(rc==HAL_OK&&tx)rc=HAL_QSPI_Transmit(&qspi,(uint8_t *)tx,20);
#endif
    *detail=((uint32_t)rc<<24)|HAL_QSPI_GetError(&qspi);
    if(rc!=HAL_OK||*detail) {
        /* Do not reset the flash or retry an ambiguous program. Release only CS. */
        GPIO_InitTypeDef g={0};HAL_GPIO_WritePin(GPIOB,GPIO_PIN_6,GPIO_PIN_SET);
        g.Pin=GPIO_PIN_6;g.Mode=GPIO_MODE_OUTPUT_PP;g.Pull=GPIO_NOPULL;g.Speed=GPIO_SPEED_FREQ_LOW;
        HAL_GPIO_Init(GPIOB,&g);return 1;
    }
    return 0;
}
static int map(void *ctx,uint32_t *detail) {
    (void)ctx;
#if M3_STORAGE_RECORD
    *detail=0x40000004;return 1;
#else
    QSPI_CommandTypeDef c=base(3,0,0,0,1);
    QSPI_MemoryMappedTypeDef m={0};m.TimeOutActivation=QSPI_TIMEOUT_COUNTER_DISABLE;
    HAL_StatusTypeDef rc=HAL_QSPI_MemoryMapped(&qspi,&c,&m);
    *detail=((uint32_t)rc<<24)|HAL_QSPI_GetError(&qspi);return rc!=HAL_OK||*detail;
#endif
}
void bench_storage_begin(unsigned mode,const uint8_t identity[76],BenchStorage *r) {
    const StorageIO io={NULL,ticks,delay,init,exchange,map,progress};
#ifdef M3_USB
    storage_busy=1;
#endif
    storage_begin(&store,&io,mode,identity);*r=store.result;
#ifdef M3_USB
    storage_busy=0;
#endif
}
void bench_storage_append(const uint8_t *payload,uint32_t counter,BenchStorage *r) {
#ifdef M3_USB
    storage_busy=1;
#endif
#if M3_STORAGE_RECORD
    storage_append(&store,payload,counter);*r=store.result;
#else
    (void)payload;(void)counter;*r=store.result;
#endif
#ifdef M3_USB
    storage_busy=0;
#endif
}
#ifdef M3_USB
/* Read-only USB requests are serialized against initialization/programming.
 * Use bounded indirect HAL transfers, never CPU reads from a stalled QSPI AHB
 * window. INSPECT restores its mapped mode afterward for its explicit state. */
int bench_storage_usb_read(uint32_t address,uint8_t *out,size_t n){
    if(!out||!n||n>1024U||address>STORE_BYTES||n>STORE_BYTES-address)return 2;
    if(storage_busy||store.result.status!=STORE_READY||!store.initialized)return 1;
    storage_busy=1;unsigned was_mapped=store.result.mapped;uint32_t detail=0;
    if(was_mapped){
        if(HAL_QSPI_Abort(&qspi)!=HAL_OK){
            store.result.error=STORE_IO;store.result.history|=1U<<STORE_IO;
            store.result.status=STORE_STOPPED;store.result.io_error=HAL_QSPI_GetError(&qspi);
            store.result.mapped=0;storage_busy=0;return 2;
        }
        store.result.mapped=0;
    }
    int ok=storage_read(&store,address,out,n);
    if(ok&&was_mapped){
        if(map(NULL,&detail)){
            store.result.error=STORE_IO;store.result.history|=1U<<STORE_IO;
            store.result.status=STORE_STOPPED;store.result.io_error=detail;ok=0;
        }else store.result.mapped=1;
    }
    storage_busy=0;return ok?0:2;
}
#endif
#endif
