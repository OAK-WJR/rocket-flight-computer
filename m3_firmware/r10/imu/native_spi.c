#include "stm32h7xx.h"
#include "imu_core.h"
#include "spi_port.h"

#define CHECK_OFFSET(base,type,member,value) _Static_assert((base)+offsetof(type,member)==(value),"SPI MMIO drift: " #member)
_Static_assert(GPIOB_BASE==R10_GPIOB && RCC_BASE==R10_RCC && SPI1_BASE==R10_SPI1,"SPI bases");
CHECK_OFFSET(RCC_BASE,RCC_TypeDef,D1CCIPR,R10_D1CCIPR);
CHECK_OFFSET(RCC_BASE,RCC_TypeDef,D2CCIP1R,R10_D2CCIP1R);
CHECK_OFFSET(RCC_BASE,RCC_TypeDef,APB2RSTR,R10_APB2RSTR);
CHECK_OFFSET(RCC_BASE,RCC_TypeDef,AHB4ENR,R10_AHB4ENR);
CHECK_OFFSET(RCC_BASE,RCC_TypeDef,APB2ENR,R10_APB2ENR);
CHECK_OFFSET(GPIOB_BASE,GPIO_TypeDef,BSRR,R10_BSRR);
CHECK_OFFSET(GPIOB_BASE,GPIO_TypeDef,AFR,R10_AFRL);
CHECK_OFFSET(SPI1_BASE,SPI_TypeDef,TXDR,R10_TXDR);
CHECK_OFFSET(SPI1_BASE,SPI_TypeDef,RXDR,R10_RXDR);
CHECK_OFFSET(SPI1_BASE,SPI_TypeDef,I2SCFGR,R10_I2SCFGR);
_Static_assert((SPI_CFG2_AFCNTR|SPI_CFG2_SSM|SPI_CFG2_CPOL|SPI_CFG2_CPHA|SPI_CFG2_MASTER)==R10_SPI_CONFIG2,"SPI mode3");
_Static_assert(((5u<<SPI_CFG1_MBR_Pos)|(7u<<SPI_CFG1_CRCSIZE_Pos)|7u)==R10_SPI_CONFIG1,"SPI frame/CRC size");

static uint32_t read_mmio(void *ctx,uint32_t address,unsigned width) {
    (void)ctx;
    return width==1 ? *(volatile uint8_t *)(uintptr_t)address : *(volatile uint32_t *)(uintptr_t)address;
}
static void write_mmio(void *ctx,uint32_t address,uint32_t value,unsigned width) {
    (void)ctx;
    if (width==1) *(volatile uint8_t *)(uintptr_t)address=(uint8_t)value;
    else *(volatile uint32_t *)(uintptr_t)address=value;
    __DSB();
}
static void delay_cycles(void *ctx,unsigned cycles) {
    (void)ctx;for (unsigned i=0;i<cycles;++i)__NOP();
}
static r10_spi_port port={.io={.read=read_mmio,.write=write_mmio,.delay_cycles=delay_cycles},.poll_limit=65536};
static const r10_imu_io io={.handle=&port,.initialize=r10_spi_initialize,.exchange=r10_spi_exchange};
const r10_imu_io *r10_native_imu_io(void) {return &io;}
