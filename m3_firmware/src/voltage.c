/* Bench ADC3: PC2_C/INP0, PC3_C/INP1, internal VREFINT/INP19.
 * ST CubeH7 v1.13.0 HAL/LL; polling only, no DMA/cache/interrupt sharing.
 */
#include "stm32h7xx_hal.h"
#include "checks.h"
#include "voltage.h"
#include "generated.h"
#include <string.h>

static ADC_HandleTypeDef adc;
static uint32_t attempted, init_error, clocked;

static uint32_t initialize(void) {
    __HAL_RCC_GPIOC_CLK_ENABLE(); __HAL_RCC_SYSCFG_CLK_ENABLE();
    GPIO_InitTypeDef g = {0};
    g.Pin = GPIO_PIN_2 | GPIO_PIN_3; g.Mode = GPIO_MODE_ANALOG; g.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOC, &g);
    HAL_SYSCFG_AnalogSwitchConfig(SYSCFG_SWITCH_PC2, SYSCFG_SWITCH_PC2_OPEN);
    HAL_SYSCFG_AnalogSwitchConfig(SYSCFG_SWITCH_PC3, SYSCFG_SWITCH_PC3_OPEN);
    if ((SYSCFG->PMCR & (SYSCFG_PMCR_PC2SO | SYSCFG_PMCR_PC3SO)) !=
        (SYSCFG_PMCR_PC2SO | SYSCFG_PMCR_PC3SO)) return 10;
    __HAL_RCC_CLKP_CONFIG(RCC_CLKPSOURCE_HSI);
    __HAL_RCC_ADC_CONFIG(RCC_ADCCLKSOURCE_CLKP);
    if (HAL_RCCEx_GetPeriphCLKFreq(RCC_PERIPHCLK_ADC) != 64000000U) return 1;
    __HAL_RCC_ADC3_CLK_ENABLE();
    clocked = 1;
    __HAL_RCC_ADC3_FORCE_RESET(); __HAL_RCC_ADC3_RELEASE_RESET();
    adc.Instance = ADC3;
    adc.Init.ClockPrescaler = ADC_CLOCK_ASYNC_DIV16;
    adc.Init.Resolution = ADC_RESOLUTION_16B;
    adc.Init.ScanConvMode = DISABLE;
    adc.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
    adc.Init.NbrOfConversion = 1;
    adc.Init.NbrOfDiscConversion = 1;
    adc.Init.ExternalTrigConv = ADC_SOFTWARE_START;
    adc.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
    adc.Init.ConversionDataManagement = ADC_CONVERSIONDATA_DR;
    adc.Init.Overrun = ADC_OVR_DATA_PRESERVED;
    adc.Init.LeftBitShift = ADC_LEFTBITSHIFT_NONE;
    if (HAL_ADC_Init(&adc) != HAL_OK) return 2;
    /* HAL calibration's 633,600,000-iteration timeout can stall a bench test.
     * Use the same ST LL start operation with an explicit 200ms limit. With
     * HSI/16, the analog clock is 4MHz (rev Y) / 2MHz (rev V); even the HAL's
     * conservative 165010-cycle bound is <83ms here. One attempt per boot.
     */
    LL_ADC_StartCalibration(ADC3, ADC_CALIB_OFFSET_LINEARITY, ADC_SINGLE_ENDED);
    uint32_t began = HAL_GetTick();
    while (LL_ADC_IsCalibrationOnGoing(ADC3))
        if ((uint32_t)(HAL_GetTick() - began) >= 200U) return 3;
    HAL_Delay(1); /* >4 ADC clocks between calibration and enable */
    return 0;
}

static uint32_t convert(uint32_t channel, uint32_t *out) {
    ADC_ChannelConfTypeDef c = {0};
    c.Channel = channel; c.Rank = ADC_REGULAR_RANK_1;
    c.SamplingTime = ADC_SAMPLETIME_810CYCLES_5;
    c.SingleDiff = ADC_SINGLE_ENDED; c.OffsetNumber = ADC_OFFSET_NONE;
    if (HAL_ADC_ConfigChannel(&adc, &c) != HAL_OK) return 4;
    HAL_Delay(1); /* internal reference settle >=5us, no undocumented assumption */
    if (HAL_ADC_Start(&adc) != HAL_OK) return 5;
    if (HAL_ADC_PollForConversion(&adc, 20) != HAL_OK) {
        (void)HAL_ADC_Stop(&adc); return 6;
    }
    *out = HAL_ADC_GetValue(&adc);
    if (HAL_ADC_Stop(&adc) != HAL_OK) return 7;
    return 0;
}

void bench_adc_sample(BenchADC *o) {
    memset(o, 0, sizeof(*o)); o->status = STATUS_FAIL;
    o->cal = *VREFINT_CAL_ADDR;
    if (!attempted) { attempted = 1; init_error = initialize(); }
    o->init_error = init_error; o->error = init_error;
    if (!o->error && (o->cal < 20000 || o->cal > 30000)) o->error = 8;
    if (!o->error) { o->error = convert(ADC_CHANNEL_VREFINT, &o->ref); if (!o->error) o->valid |= 1; }
    if (!o->error) { o->error = convert(ADC_CHANNEL_0, &o->logic); if (!o->error) o->valid |= 2; }
    if (!o->error) { o->error = convert(ADC_CHANNEL_1, &o->v3); if (!o->error) o->valid |= 4; }
    if (!o->error && adc.ErrorCode) o->error = 11;
    if (!o->error && !bench_voltages(o->cal, o->ref, o->logic, o->v3, &o->vdda_mv, &o->logic_mv, &o->v3_mv))
        o->error = 9;
    if (!o->error) o->status = STATUS_PASS; /* acquisition, not electrical qualification */
    o->sample_ms = HAL_GetTick(); o->hal_error = adc.ErrorCode;
    o->pmcr = SYSCFG->PMCR;
    if (clocked) {
        o->ccr = ADC3_COMMON->CCR; o->pcsel = ADC3->PCSEL;
        o->cfgr = ADC3->CFGR; o->cr = ADC3->CR;
    }
}
