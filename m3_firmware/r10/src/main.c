/* Sensor/ADC/read-only QSPI bench diagnostics. No actuator/PWM, UART, USB or
 * flash programming. External loads must be physically disconnected. */
#include "stm32h7xx.h"
#include "mailbox.h"
#include "generated.h"
#include "imu_frame.h"
#include "baro_frame.h"
#include "voltage_frame.h"
#include "flash_frame.h"
_Static_assert(R10_WORDS==256u && R10_CRC==255u && R10_ABI==5u,"ABI5 frame bounds");

#ifndef R10_HOST_TEST
/* Fail compilation if the stack-free startup's supply constants drift. */
_Static_assert(PWR_BASE == 0x58024800u, "startup PWR base");
_Static_assert(offsetof(PWR_TypeDef, CR3) == 0x0cu, "startup CR3 offset");
_Static_assert(offsetof(PWR_TypeDef, CSR1) == 4u, "startup CSR1 offset");
_Static_assert(PWR_CR3_LDOEN == 2u, "startup LDO mask");
_Static_assert(PWR_CSR1_ACTVOSRDY == 0x2000u, "startup ready mask");
#endif

#ifndef R10_HOST_TEST
__attribute__((section(".r10_mailbox"), aligned(8), used))
#endif
volatile uint32_t r10_mailbox[R10_WORDS];
static volatile uint32_t ticks_lo, ticks_hi;
static uint32_t main_count, sequence, ready;
static r10_observation obs;
static uint32_t frame[R10_WORDS];
static r10_imu imu;
static r10_baro baro;
static r10_voltage voltage;
static r10_flash_ro flash;

void SysTick_Handler(void) {
    if (++ticks_lo == 0u) ++ticks_hi;
}

static void sample(uint32_t state, uint32_t exception) {
    obs.state = state; obs.exception = exception;
    obs.ticks_lo = ticks_lo; obs.ticks_hi = ticks_hi;
    obs.main_count = main_count;
    obs.cfsr = SCB->CFSR; obs.hfsr = SCB->HFSR; obs.dfsr = SCB->DFSR;
    obs.mmfar = SCB->MMFAR; obs.bfar = SCB->BFAR; obs.icsr = SCB->ICSR;
    obs.rcc_cr = RCC->CR; obs.rcc_cfgr = RCC->CFGR;
    obs.rcc_d1cfgr = RCC->D1CFGR; obs.pwr_csr1 = PWR->CSR1;
    obs.systick_load = SysTick->LOAD;
    r10_frame(frame, &obs, R10_BOARD_HASH, R10_BUILD_HASH);
    /* A core exception may interrupt a sensor-state update. Do not present a
     * partially updated sensor object as a coherent/fresh sample in that case. */
    if (state!=R10_STATE_FAULT) {
        r10_pack_imu(frame,&imu);r10_pack_baro(frame,&baro);
        r10_pack_voltage(frame,&voltage,r10_native_adc_state());
        r10_pack_flash(frame,&flash,r10_native_qspi_state());
    }
    r10_publish(r10_mailbox, frame, &sequence);
}

void Default_Handler(void) {
    __disable_irq();
    /* Early faults and a damaged MSP cannot promise a complete record. */
    if (ready != 0u) sample(R10_STATE_FAULT, __get_IPSR());
    for (;;) __WFI();
}

int main(void) {
    __disable_irq();
    SCB->VTOR = FLASH_BASE;
    __DSB(); __ISB();
    obs.cpuid = SCB->CPUID;
    obs.idcode = DBGMCU->IDCODE;
    for (unsigned i = 0; i < 3u; ++i)
        obs.uid[i] = ((volatile const uint32_t *)UID_BASE)[i];
    obs.reset_flags = RCC->RSR; /* preserve sticky raw flags; do not clear */
    SystemCoreClockUpdate();
    obs.core_hz = SystemCoreClock;
    ready = 1u;
    sample(R10_STATE_STARTING, 0u);
    /* The pinned SystemInit selects HSI, no HSE/PLL dependencies. This is a
     * nominal clock, not an oscillator accuracy or crystal test. */
    if ((obs.cpuid & 0xff00fff0u) != 0x4100c270u ||
        (obs.idcode & 0xfffu) != 0x450u ||
        (RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_HSI ||
        SystemCoreClock == 0u || SystemCoreClock % 1000u != 0u ||
        SysTick_Config(SystemCoreClock / 1000u) != 0u) {
        sample(R10_STATE_FAULT, 0xffff0001u);
        for (;;) __WFI();
    }
    __enable_irq();
    r10_imu_begin(&imu,r10_native_imu_io(),ticks_lo);
    r10_baro_begin(&baro,r10_native_baro_io(),ticks_lo);
    r10_voltage_begin(&voltage,r10_native_voltage_io(),ticks_lo);
    r10_flash_ro_begin(&flash,r10_native_flash_io(),ticks_lo);
    uint32_t published = 0u;
    uint32_t polled = ticks_lo;
    for (;;) {
        __WFI();
        uint32_t now=ticks_lo;
        if ((uint32_t)(now-polled)>=20u) {
            polled=now;
            r10_imu_poll(&imu,now);
        }
        r10_baro_poll(&baro,ticks_lo);
        r10_voltage_poll(&voltage,ticks_lo);
        r10_flash_ro_poll(&flash,ticks_lo);
        __disable_irq();
        ++main_count;
        if ((uint32_t)(ticks_lo - published) >= R10_PUBLISH_PERIOD_TICKS) {
            published = ticks_lo;
            sample(R10_STATE_RUNNING, 0u);
        }
        __enable_irq();
    }
}
