/* Bounded bench ADC adapter for the ABI-v4 bench image.
 * Register addresses/masks are checked against pinned CMSIS in native_adc.c. */
#ifndef R10_ADC_PORT_H
#define R10_ADC_PORT_H
#include "voltage_core.h"
enum {
    A_RCC=0x58024400u,A_GPIOA=0x58020000u,A_GPIOB=0x58020400u,
    A_ADC1=0x40022000u,A_ADC2=0x40022100u,A_ADC3=0x58026000u,
    A_COMMON12=0x40022300u,A_COMMON3=0x58026300u,
    A_IDCODE=0x5c001000u,A_FACTORY=0x1ff1e860u,
    A_RCC_CR=A_RCC,A_CFGR=A_RCC+0x10u,A_D1CFGR=A_RCC+0x18u,
    A_D1CCIPR=A_RCC+0x4cu,A_D3CCIPR=A_RCC+0x58u,
    A_RESET12=A_RCC+0x80u,A_RESET3=A_RCC+0x88u,
    A_ENABLE12=A_RCC+0xd8u,A_ENABLE3=A_RCC+0xe0u,
    A_ISR=0u,A_IER=4u,A_CR=8u,A_ADC_CFGR=12u,A_ADC_CFGR2=16u,
    A_SMPR1=20u,A_SMPR2=24u,A_PCSEL=28u,A_SQR1=48u,A_DR=64u,
    A_DIFSEL=192u,A_CALFACT=196u,A_CCR=8u,
    A_GATE12=0x20u,A_GATE3=0x01000000u,
    A_ADEN=1u,A_ADDIS=2u,A_ADSTART=4u,A_JADSTART=8u,A_ADSTP=16u,A_JADSTP=32u,
    A_BOOST=0x300u,A_LINEAR=0x10000u,A_LINEAR_READY=0x0fc00000u,
    A_REGULATOR=0x10000000u,A_DEEP=0x20000000u,A_DIFF=0x40000000u,A_CAL=0x80000000u,
    A_ADRDY=1u,A_EOSMP=2u,A_EOC=4u,A_EOS=8u,A_OVR=16u,A_LDORDY=0x1000u,
    A_FLAGS=0x7ffu,A_UNEXPECTED=0x7f0u,
    A_PRESCALER=7u<<18,A_INTERNAL=(1u<<22)|(1u<<24),
    A_SETTINGS=0x8000000cu,A_SAMPLE1=(7u<<9)|(7u<<15),A_SAMPLE3=(7u<<21)|(7u<<27),
    A_PRESELECT1=(1u<<3)|(1u<<5),A_PRESELECT3=(1u<<17)|(1u<<19),
    A_CONTROLS=0xc000003fu
};
enum {
    A_NEW,A_REGULATOR_WAIT,A_CAL1_WAIT,A_CAL1_GUARD,A_READY1_WAIT,
    A_CAL3_WAIT,A_CAL3_GUARD,A_READY3_WAIT,A_READY,A_ERROR
};
enum {
    A_FAIL_ADAPTER=1,A_FAIL_CLOCK,A_FAIL_ID,A_FAIL_FACTORY,A_FAIL_OWNERSHIP,
    A_FAIL_ENABLE,A_FAIL_RESET,A_FAIL_REGULATOR,A_FAIL_CALIBRATION,A_FAIL_READY,
    A_FAIL_CONFIG,A_FAIL_ARGUMENT,A_FAIL_START,A_FAIL_STATUS,A_FAIL_DATA,A_FAIL_CLEANUP
};
typedef struct {
    void *context;
    uint32_t (*read)(void *,uint32_t address,unsigned width);
    void (*write)(void *,uint32_t address,uint32_t value,unsigned width);
} r10_adc_mmio;
typedef struct {
    r10_adc_mmio io;
    uint32_t phase,phase_ms,revision,calibration,nominal_adc_hz;
    uint32_t calibration1,calibration3,last_cr,last_isr,last_dr,unit,detail;
    uint8_t owned,active;
} r10_adc_port;
int r10_adc_initialize(void *,uint32_t now_ms,r10_voltage_config *,uint32_t *);
int r10_adc_start(void *,unsigned slot,uint32_t *);
int r10_adc_poll(void *,uint32_t *,uint32_t *);
int r10_adc_cancel(void *,uint32_t *);
const r10_voltage_io *r10_native_voltage_io(void);
const r10_adc_port *r10_native_adc_state(void);
#endif
