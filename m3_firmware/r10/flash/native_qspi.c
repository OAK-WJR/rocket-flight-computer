/* Native register bridge; cross-compiled/model-reviewed, not hardware tested. */
#include "stm32h7xx.h"
#include "qspi_port.h"
#include <stddef.h>
#define CHECK(a,b) _Static_assert((a)==(b),"QSPI register drift: " #a)
CHECK(QSPI_R_BASE,Q_BASE);CHECK(RCC_BASE,Q_RCC);CHECK(GPIOB_BASE,Q_GPIOB);
CHECK(GPIOD_BASE,Q_GPIOD);CHECK(GPIOE_BASE,Q_GPIOE);CHECK(DBGMCU_BASE,Q_ID);
CHECK(RCC_BASE+offsetof(RCC_TypeDef,AHB3ENR),Q_ENABLE);
CHECK(RCC_BASE+offsetof(RCC_TypeDef,AHB3RSTR),Q_RESET);
CHECK(RCC_BASE+offsetof(RCC_TypeDef,AHB4ENR),Q_GPIO_ENABLE);
CHECK(RCC_BASE+offsetof(RCC_TypeDef,D1CCIPR),Q_D1CCIPR);
CHECK(RCC_BASE+offsetof(RCC_TypeDef,D1CFGR),Q_D1CFGR);
CHECK(RCC_BASE+offsetof(RCC_TypeDef,CFGR),Q_CFGR);
CHECK(RCC_AHB3ENR_QSPIEN,Q_GATE);CHECK(RCC_AHB3RSTR_QSPIRST,Q_GATE);
CHECK(RCC_AHB4ENR_GPIOBEN|RCC_AHB4ENR_GPIODEN|RCC_AHB4ENR_GPIOEEN,Q_GPIO_GATES);
CHECK(RCC_D1CCIPR_QSPISEL,0x30u);CHECK(RCC_CR_HSION|RCC_CR_HSIRDY|RCC_CR_HSIDIV,0x1du);
CHECK(RCC_CFGR_SW|RCC_CFGR_SWS,0x3fu);CHECK(RCC_D1CFGR_D1CPRE|RCC_D1CFGR_HPRE,0xf0fu);
#define OFF(type,member,value) CHECK(offsetof(type,member),value)
OFF(GPIO_TypeDef,MODER,Q_MODER);OFF(GPIO_TypeDef,OTYPER,Q_OTYPER);OFF(GPIO_TypeDef,OSPEEDR,Q_SPEED);
OFF(GPIO_TypeDef,PUPDR,Q_PULL);OFF(GPIO_TypeDef,IDR,Q_IDR);OFF(GPIO_TypeDef,ODR,Q_ODR);
OFF(GPIO_TypeDef,BSRR,Q_BSRR);OFF(GPIO_TypeDef,AFR,Q_AFRL);
OFF(QUADSPI_TypeDef,CR,Q_CR);OFF(QUADSPI_TypeDef,DCR,Q_DCR);OFF(QUADSPI_TypeDef,SR,Q_SR);
OFF(QUADSPI_TypeDef,FCR,Q_FCR);OFF(QUADSPI_TypeDef,DLR,Q_DLR);OFF(QUADSPI_TypeDef,CCR,Q_CCR);
OFF(QUADSPI_TypeDef,AR,Q_AR);OFF(QUADSPI_TypeDef,ABR,Q_ABR);OFF(QUADSPI_TypeDef,DR,Q_DR);
CHECK(QUADSPI_SR_TEF,Q_TEF);CHECK(QUADSPI_SR_TCF,Q_TCF);CHECK(QUADSPI_SR_FTF,Q_FTF);
CHECK(QUADSPI_SR_SMF,Q_SMF);CHECK(QUADSPI_SR_TOF,Q_TOF);CHECK(QUADSPI_SR_BUSY,Q_BUSY);
CHECK(QUADSPI_SR_FLEVEL,Q_LEVEL);CHECK(QUADSPI_FCR_CTEF|QUADSPI_FCR_CTCF|QUADSPI_FCR_CSMF|QUADSPI_FCR_CTOF,Q_FLAGS);
CHECK(QUADSPI_CR_EN|(63u<<QUADSPI_CR_PRESCALER_Pos),Q_CONTROL);
CHECK((23u<<QUADSPI_DCR_FSIZE_Pos)|(3u<<QUADSPI_DCR_CSHT_Pos),Q_DEVICE);
CHECK(QUADSPI_CCR_IMODE_0,0x100u);CHECK(QUADSPI_CCR_FMODE_0,0x04000000u);
CHECK(QUADSPI_CCR_FRCM,0x20000000u);
CHECK(QUADSPI_CCR_ADMODE_Pos,10u);CHECK(QUADSPI_CCR_ADSIZE_Pos,12u);
CHECK(QUADSPI_CCR_ABMODE_Pos,14u);CHECK(QUADSPI_CCR_DCYC_Pos,18u);CHECK(QUADSPI_CCR_DMODE_Pos,24u);

static uint32_t read_register(void *ctx,uint32_t addr,unsigned width) {
    (void)ctx;
    if (width==8u) return *(volatile const uint8_t *)(uintptr_t)addr;
    return *(volatile const uint32_t *)(uintptr_t)addr;
}
static void write_register(void *ctx,uint32_t addr,uint32_t value,unsigned width) {
    (void)ctx;(void)width;*(volatile uint32_t *)(uintptr_t)addr=value;__DSB();
}
__attribute__((noinline)) static int prime(void *ctx) {
    (void)ctx;uint32_t previous=__get_PRIMASK();__disable_irq();
    /* ES0392 Rev16 2.7.4: the first CCR store through CR-disable must finish
     * within127 kernel clocks. Keep these three stores consecutive: no helper
     * calls, waits, interrupt or compiler-inserted instructions between them.
     * Object-code checks establish this sequence, not physical bus timing. */
    __asm volatile(
        "str %[maximum], [%[base], #0]\n"
        "dsb sy\n"
        "str %[run], [%[base], #20]\n"
        "str %[run], [%[base], #20]\n"
        "str %[zero], [%[base], #0]\n"
        "dsb sy\n"
        : : [base] "r" (QSPI_R_BASE),[maximum] "r" (QUADSPI_CR_PRESCALER|QUADSPI_CR_EN),
            [run] "r" (QUADSPI_CCR_FRCM),[zero] "r" (0u) : "memory");
    __set_PRIMASK(previous);return FRO_OK;
}
static r10_qspi_port port={.io={.read=read_register,.write=write_register,.prime=prime}};
static const r10_flash_ro_io io={.context=&port,.initialize=r10_qspi_initialize,
    .start=r10_qspi_start,.poll=r10_qspi_poll,.cancel=r10_qspi_cancel};
const r10_flash_ro_io *r10_native_flash_io(void) {return &io;}
const r10_qspi_port *r10_native_qspi_state(void) {return &port;}
