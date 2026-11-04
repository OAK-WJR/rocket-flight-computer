/* Cross-build bridge only; no function here runs at load/link time. */
#include "stm32h7xx.h"
#include "spi3_port.h"
#include <stddef.h>
#define CHECK(a,b) _Static_assert((a)==(b),"SD SPI3 drift: " #a)
CHECK(SPI3_BASE,SD3_SPI);CHECK(GPIOC_BASE,SD3_GPIOC);CHECK(GPIOD_BASE,SD3_GPIOD);CHECK(RCC_BASE,SD3_RCC);
#define OFFSET(base,type,member,value) CHECK((base)+offsetof(type,member),value)
OFFSET(RCC_BASE,RCC_TypeDef,APB1LENR,SD3_ENABLE);OFFSET(RCC_BASE,RCC_TypeDef,APB1LRSTR,SD3_RESET);
OFFSET(RCC_BASE,RCC_TypeDef,AHB4ENR,SD3_GPIO_ENABLE);OFFSET(RCC_BASE,RCC_TypeDef,D1CCIPR,SD3_D1CCIPR);
OFFSET(RCC_BASE,RCC_TypeDef,D2CCIP1R,SD3_D2CCIP1R);OFFSET(RCC_BASE,RCC_TypeDef,CFGR,SD3_CFGR);
OFFSET(RCC_BASE,RCC_TypeDef,D1CFGR,SD3_D1CFGR);
OFFSET(SPI3_BASE,SPI_TypeDef,CR1,SD3_CR1);OFFSET(SPI3_BASE,SPI_TypeDef,CR2,SD3_CR2);
OFFSET(SPI3_BASE,SPI_TypeDef,CFG1,SD3_CFG1);OFFSET(SPI3_BASE,SPI_TypeDef,CFG2,SD3_CFG2);
OFFSET(SPI3_BASE,SPI_TypeDef,SR,SD3_SR);OFFSET(SPI3_BASE,SPI_TypeDef,IFCR,SD3_IFCR);
OFFSET(SPI3_BASE,SPI_TypeDef,TXDR,SD3_TXDR);OFFSET(SPI3_BASE,SPI_TypeDef,RXDR,SD3_RXDR);
OFFSET(SPI3_BASE,SPI_TypeDef,IER,SD3_IER);OFFSET(SPI3_BASE,SPI_TypeDef,I2SCFGR,SD3_I2S);
CHECK(RCC_APB1LENR_SPI3EN,SD3_GATE);CHECK(RCC_APB1LRSTR_SPI3RST,SD3_GATE);
CHECK(offsetof(GPIO_TypeDef,MODER),SD3_MODER);CHECK(offsetof(GPIO_TypeDef,OTYPER),SD3_TYPE);
CHECK(offsetof(GPIO_TypeDef,OSPEEDR),SD3_SPEED);CHECK(offsetof(GPIO_TypeDef,PUPDR),SD3_PULL);
CHECK(offsetof(GPIO_TypeDef,IDR),SD3_IDR);CHECK(offsetof(GPIO_TypeDef,ODR),SD3_ODR);
CHECK(offsetof(GPIO_TypeDef,BSRR),SD3_BSRR);CHECK(offsetof(GPIO_TypeDef,AFR)+4u,SD3_AFRH);
CHECK(RCC_AHB4ENR_GPIOCEN|RCC_AHB4ENR_GPIODEN,SD3_GPIO_GATES);
CHECK(RCC_CR_HSION|RCC_CR_HSIRDY|RCC_CR_HSIDIV,0x1du);
CHECK(RCC_CFGR_SW|RCC_CFGR_SWS,0x3fu);CHECK(RCC_D1CFGR_D1CPRE|RCC_D1CFGR_HPRE,0xf0fu);
CHECK(RCC_D1CCIPR_CKPERSEL,0x30000000u);CHECK(RCC_D2CCIP1R_SPI123SEL,0x7000u);
CHECK((7u<<SPI_CFG1_MBR_Pos)|(7u<<SPI_CFG1_CRCSIZE_Pos)|7u,SD3_CONFIG1);
CHECK(SPI_CFG2_AFCNTR|SPI_CFG2_SSM|SPI_CFG2_MASTER,SD3_CONFIG2);
CHECK(SPI_SR_RXPLVL|SPI_SR_RXWNE|SPI_SR_RXP,SD3_RX_PENDING);
CHECK(SPI_SR_UDR|SPI_SR_OVR|SPI_SR_CRCE|SPI_SR_TIFRE|SPI_SR_MODF,SD3_ERRORS);
CHECK(SPI_CR1_SSI,0x1000u);CHECK(SPI_CR1_CSTART|SPI_CR1_SPE,0x201u);CHECK(SPI_CR1_CSUSP,0x400u);

static uint32_t read_register(void *context,uint32_t address,unsigned width) {
 (void)context;return width==1u?*(volatile const uint8_t *)(uintptr_t)address:*(volatile const uint32_t *)(uintptr_t)address;
}
static void write_register(void *context,uint32_t address,uint32_t value,unsigned width) {
 (void)context;
 if (width==1u) {*(volatile uint8_t *)(uintptr_t)address=(uint8_t)value;}
 else {*(volatile uint32_t *)(uintptr_t)address=value;}
 __DSB();
}
static void delay(void *context,unsigned cycles) {(void)context;for (unsigned i=0;i<cycles;++i)__NOP();}
static r10_sd_spi3_port port={.io={.read=read_register,.write=write_register,.delay_cycles=delay},.poll_limit=65536};
static const r10_sd_bus bus={.context=&port,.initialize=r10_sd_spi3_initialize,.select=r10_sd_spi3_select,
                           .transfer=r10_sd_spi3_transfer,.release=r10_sd_spi3_release};
const r10_sd_bus *r10_native_sd_bus(void) {return &bus;}
const r10_sd_spi3_port *r10_native_sd_spi3_state(void) {return &port;}
