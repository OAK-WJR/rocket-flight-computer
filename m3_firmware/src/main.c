/* M3-PWR-R3 BENCH measurements. Slow software SPI/I2C exposes wiring responses.
 * ADC voltage / MS5611 pressure samples have raw evidence and timestamps.
 * Optional v4 hardware SPI adds decimated IMU raw observations; v5 adds an
 * explicitly selected append-only logger or read-only inspection. v6 adds a USB
 * CDC readout. Physical USB, sensor accuracy and watchdog behavior are NOT
 * qualified. No actuation/flight-state logic.
 */
#include "stm32h7xx_hal.h"
#include "checks.h"
#include "voltage.h"
#include "generated.h"
#ifdef M3_POWER_STATUS
#include "power_status.h"
_Static_assert(W_POWER_FLAGS==153 && W_POWER_MAX_GAP_MS==159,"Power result placement");
#endif
#ifdef M3_GNSS
#include "gnss.h"
_Static_assert(W_GNSS_STATE==184 && W_GNSS_VERSION==230,"GNSS result placement");
#endif
#ifdef M3_USB
#include "usb.h"
#include "usb_wire.h"
_Static_assert(W_USB_STATE==160 && W_USB_RESERVED==183,"USB result placement");
#endif
#ifdef M3_STORAGE
#include "storage.h"
_Static_assert(W_STORE_MODE==128 && W_STORE_RESERVED==153,"Storage record placement");
#endif
#ifdef M3_IMU_SAMPLES
#include "imu.h"
_Static_assert(W_IMU_SAMPLE_STATUS==112 && W_IMU_RAW==122 && W_IMU_BUS_HZ==126, "IMU record placement");
#endif
#ifdef M3_CAMERA_UART
#include "camera.h"
_Static_assert(W_CAMERA_STATUS == 82 && W_CAMERA_PACKET == 110, "Camera result placement");
#endif
#include <string.h>

_Static_assert(sizeof(uint32_t) == 4, "Mailbox requires 32-bit words");
_Static_assert(D1_AXISRAM_BASE == MB_ADDRESS, "Wrong SRAM address");
#ifdef M3_HOST_TEST
__attribute__((aligned(32), used))
#else
__attribute__((section(".bench_mailbox"), aligned(32), used))
#endif
volatile uint32_t bench_mailbox[MB_BYTES / 4];
static uint32_t frame[MB_BYTES / 4];
static uint32_t seq;

static void interfaces(void){
#ifdef M3_GNSS
    BenchGNSS gnss;bench_gnss_status(&gnss);memcpy(&frame[W_GNSS_STATE],&gnss,sizeof(gnss));
#endif
#ifdef M3_USB
    BenchUSB usb;bench_usb_status(&usb);memcpy(&frame[W_USB_STATE],&usb,sizeof(usb));
#endif
#ifdef M3_POWER_STATUS
    /* After the legacy storage copy, which still zeroes reserved words153..155. */
    BenchPowerStatus power;bench_power_status(&power);memcpy(&frame[W_POWER_FLAGS],&power,sizeof(power));
#endif
}
static void publish(void) {
    interfaces();
    frame[W_UPTIME_MS] = HAL_GetTick();
    frame[W_SEQUENCE] = 0;
    frame[W_CRC32] = bench_crc32((const uint8_t *)frame, MB_BYTES - 4);
    bench_mailbox[W_SEQUENCE] = ++seq; /* odd: an update is in progress */
    __DMB();
    for (unsigned i = 0; i < MB_BYTES / 4; ++i)
        if (i != W_SEQUENCE) bench_mailbox[i] = frame[i];
    __DMB();
    bench_mailbox[W_SEQUENCE] = ++seq; /* even: complete committed snapshot */
    __DSB();
}
#ifdef M3_STORAGE
void bench_storage_progress(const BenchStorage *r) {
    memcpy(&frame[W_STORE_MODE],r,sizeof(*r));publish();
#ifdef M3_USB
    bench_usb_task();
#endif
}
#endif
#ifdef M3_USB
unsigned bench_usb_snapshot(void *ctx,uint8_t *out,uint32_t address,uint32_t n){
    (void)ctx;
    if(address || n!=MB_BYTES)return USB_REPLY_BAD_REQUEST;
    uint32_t first=bench_mailbox[W_SEQUENCE];
    if(first&1U)return USB_REPLY_BUSY;
    __DMB();
    for(unsigned i=0;i<MB_BYTES;i++)out[i]=((const volatile uint8_t *)bench_mailbox)[i];
    __DMB();
    return first==bench_mailbox[W_SEQUENCE]?USB_REPLY_OK:USB_REPLY_BUSY;
}
#endif

void SysTick_Handler(void) {
    HAL_IncTick();
#ifdef M3_POWER_STATUS
    bench_power_tick();
#endif
}
/* Vendor Reset_Handler calls newlib's initializer; no constructors/CRT hooks. */
void _init(void) {}

void assert_failed(uint8_t *file, uint32_t line) {
    (void)file;
    frame[W_STATE] = STATE_FATAL;
    frame[W_BUS_ERROR] = 0x80000000U | line;
    publish();
    for (;;) { __NOP(); }
}

typedef struct { GPIO_TypeDef *port; uint16_t pin; } Pin;
static const Pin imu_sck = {GPIOB, GPIO_PIN_3};
static const Pin imu_miso = {GPIOB, GPIO_PIN_4};
static const Pin imu_mosi = {GPIOB, GPIO_PIN_5};
static const Pin imu_cs = {GPIOB, GPIO_PIN_7};
static const Pin flash_sck = {GPIOB, GPIO_PIN_2};
static const Pin flash_miso = {GPIOD, GPIO_PIN_12};
static const Pin flash_mosi = {GPIOD, GPIO_PIN_11};
static const Pin flash_cs = {GPIOB, GPIO_PIN_6};
static const Pin scl = {GPIOB, GPIO_PIN_8};
static const Pin sda = {GPIOB, GPIO_PIN_9};

static void set(Pin p, int high) { HAL_GPIO_WritePin(p.port, p.pin, high ? GPIO_PIN_SET : GPIO_PIN_RESET); }
static int get(Pin p) { return HAL_GPIO_ReadPin(p.port, p.pin) == GPIO_PIN_SET; }
static void half(void) { HAL_Delay(1); } /* deliberately <=500Hz, not throughput evidence */
static void configure(Pin p, uint32_t mode, int initial) {
    GPIO_InitTypeDef g = {0};
    set(p, initial); /* output latch first to avoid selecting a chip prematurely */
    g.Pin = p.pin; g.Mode = mode; g.Pull = GPIO_NOPULL; g.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(p.port, &g);
}

static void setup_gpio(void) {
    __HAL_RCC_GPIOB_CLK_ENABLE(); __HAL_RCC_GPIOD_CLK_ENABLE(); __HAL_RCC_GPIOE_CLK_ENABLE();
#ifdef M3_CAMERA_UART
    bench_camera_safe_gpio(); /* PC13 output latch low before enabling output mode */
#else
    configure((Pin){GPIOD, GPIO_PIN_3}, GPIO_MODE_OUTPUT_PP, 0); /* camera stays disabled */
#endif
    configure((Pin){GPIOE, GPIO_PIN_3}, GPIO_MODE_OUTPUT_PP, 0);
    configure((Pin){GPIOE, GPIO_PIN_7}, GPIO_MODE_OUTPUT_PP, 0);
    configure(imu_cs, GPIO_MODE_OUTPUT_PP, 1);
    configure(flash_cs, GPIO_MODE_OUTPUT_PP, 1);
    configure(imu_sck, GPIO_MODE_OUTPUT_PP, 0);
    configure(flash_sck, GPIO_MODE_OUTPUT_PP, 0);
    configure(imu_mosi, GPIO_MODE_OUTPUT_PP, 0);
    configure(flash_mosi, GPIO_MODE_OUTPUT_PP, 0);
    configure(imu_miso, GPIO_MODE_INPUT, 0);
    configure(flash_miso, GPIO_MODE_INPUT, 0);
    configure((Pin){GPIOE, GPIO_PIN_2}, GPIO_MODE_OUTPUT_PP, 1); /* flash /WP */
    configure((Pin){GPIOD, GPIO_PIN_13}, GPIO_MODE_OUTPUT_PP, 1); /* flash /HOLD */
    configure(scl, GPIO_MODE_OUTPUT_OD, 1);
    configure(sda, GPIO_MODE_OUTPUT_OD, 1);
}

static uint8_t spi_byte(Pin clock, Pin dout, Pin din, uint8_t tx) {
    uint8_t rx = 0;
    for (unsigned i = 0; i < 8; ++i) {
        set(dout, (tx & 0x80U) != 0); tx <<= 1;
        half(); set(clock, 1); half();
        rx = (uint8_t)((rx << 1) | (unsigned)get(din));
        set(clock, 0);
    }
    return rx;
}

static void test_imu(void) {
    frame[W_IMU_STATUS] = STATUS_RUNNING; frame[W_STAGE] = 2; publish();
    set(imu_cs, 0); half();
    (void)spi_byte(imu_sck, imu_mosi, imu_miso, 0x80U | 0x72U);
    uint8_t id = spi_byte(imu_sck, imu_mosi, imu_miso, 0);
    half(); set(imu_cs, 1);
    frame[W_IMU_ID] = id;
    frame[W_IMU_STATUS] = id == 0xe9 ? STATUS_PASS : STATUS_FAIL;
    publish();
}

static void test_flash(void) {
    frame[W_FLASH_STATUS] = STATUS_RUNNING; frame[W_STAGE] = 4; publish();
    set(flash_cs, 0); half();
    (void)spi_byte(flash_sck, flash_mosi, flash_miso, 0x9f);
    uint32_t id = 0;
    for (unsigned i = 0; i < 3; ++i)
        id = (id << 8) | spi_byte(flash_sck, flash_mosi, flash_miso, 0);
    half(); set(flash_cs, 1);
    frame[W_FLASH_ID] = id;
    frame[W_FLASH_STATUS] = id == 0xef4018 ? STATUS_PASS : STATUS_FAIL;
    publish();
}

/* Software I2C: use actual line readback, external pull-ups and bounded
 * stretching. Never drive a bus high or scan unrelated devices. One documented
 * MS5611 power-on reset precedes PROM reads; no repeated recovery/reset loop.
 */
static int scl_high(void) {
    set(scl, 1);
    uint32_t start = HAL_GetTick();
    while (!get(scl)) {
        if ((uint32_t)(HAL_GetTick() - start) >= 5) {
            frame[W_BUS_ERROR] = 1; return 0;
        }
    }
    half(); return 1;
}
static int start(void) {
    set(sda, 1);
    if (!scl_high()) return 0;
    if (!get(sda)) { frame[W_BUS_ERROR] = 2; return 0; }
    set(sda, 0); half(); set(scl, 0); half(); return 1;
}
static int stop(void) {
    set(scl, 0); set(sda, 0); half();
    if (!scl_high()) { set(sda, 1); return 0; }
    set(sda, 1); half();
    if (!get(sda)) { frame[W_BUS_ERROR] = 2; return 0; }
    return 1;
}
static int send(uint8_t v) {
    for (unsigned i = 0; i < 8; ++i) {
        set(sda, (v & 0x80U) != 0); v <<= 1; half();
        if (!scl_high()) return 0;
        set(scl, 0); half();
    }
    set(sda, 1); half();
    if (!scl_high()) return 0;
    int ack = !get(sda); set(scl, 0); half();
    if (!ack) frame[W_BUS_ERROR] = 3;
    return ack;
}
static int receive(uint8_t *out, int last) {
    uint8_t v = 0; set(sda, 1);
    for (unsigned i = 0; i < 8; ++i) {
        half(); if (!scl_high()) return 0;
        v = (uint8_t)((v << 1) | (unsigned)get(sda)); set(scl, 0); half();
    }
    set(sda, last); half(); if (!scl_high()) return 0;
    set(scl, 0); set(sda, 1); half(); *out = v; return 1;
}
static int read_prom(unsigned word, uint16_t *out) {
    uint8_t hi = 0, lo = 0;
    /* TE specifies separate command + STOP, followed by read + STOP. */
    int ok = start() && send(0xee) && send((uint8_t)(0xa0U + 2U * word));
    int stopped = stop();
    if (!ok || !stopped) return 0;
    ok = start() && send(0xef) && receive(&hi, 0) && receive(&lo, 1);
    stopped = stop();
    if (!ok || !stopped) return 0;
    *out = (uint16_t)((hi << 8) | lo); return 1;
}
static void test_baro(void) {
    uint16_t prom[8] = {0};
    frame[W_BARO_STATUS] = STATUS_RUNNING; frame[W_STAGE] = 3;
    frame[W_BARO_ADDRESS] = 0x77; publish(); /* CSB=0 => complemented address bit=1 */
    /* TE MS5611 datasheet requires this once after power-on, then 2.8ms reload. */
    int reset_ok = start() && send(0xee) && send(0x1e);
    int stopped = stop();
    if (!reset_ok || !stopped) {
        frame[W_BARO_STATUS] = STATUS_FAIL; publish(); return;
    }
    HAL_Delay(5);
    for (unsigned i = 0; i < 8; ++i) {
        if (!read_prom(i, &prom[i])) {
            frame[W_BARO_STATUS] = STATUS_FAIL; publish(); return;
        }
        frame[W_BARO_PROM + i] = prom[i];
    }
    frame[W_BARO_CRC_CALC] = bench_prom_crc4(prom);
    frame[W_BARO_CRC_STORED] = prom[7] & 15U;
    int ok = bench_prom_nonempty(prom) && frame[W_BARO_CRC_CALC] == frame[W_BARO_CRC_STORED];
    if (!ok) frame[W_BUS_ERROR] = bench_prom_nonempty(prom) ? 4 : 5;
    frame[W_BARO_STATUS] = ok ? STATUS_PASS : STATUS_FAIL; publish();
}

static int baro_conversion(uint8_t command, uint32_t *raw, uint32_t *at) {
    uint8_t hi = 0, mid = 0, lo = 0;
    int ok = start() && send(0xee) && send(command);
    int stopped = stop();
    if (!ok || !stopped) return 0;
    HAL_Delay(11); /* OSR4096 maximum 9.04ms; includes millisecond quantization */
    ok = start() && send(0xee) && send(0x00); /* ADC-read command then STOP */
    stopped = stop();
    if (!ok || !stopped) return 0;
    ok = start() && send(0xef) && receive(&hi, 0) && receive(&mid, 0) && receive(&lo, 1);
    stopped = stop();
    if (!ok || !stopped) return 0;
    *raw = ((uint32_t)hi << 16) | ((uint32_t)mid << 8) | lo;
    *at = HAL_GetTick(); /* read-completed timestamp, not an exact conversion edge */
    return 1;
}

static void sample_baro(void) {
    uint16_t prom[8];
    uint32_t d1 = 0, d2 = 0, t1 = 0, t2 = 0;
    int32_t pressure = 0, temp = 0;
    frame[W_BARO_SAMPLE_STATUS] = STATUS_FAIL;
    frame[W_BARO_SAMPLE_ERROR] = 10;
    if (frame[W_BARO_STATUS] != STATUS_PASS) return;
    for (unsigned i = 0; i < 8; ++i) prom[i] = (uint16_t)frame[W_BARO_PROM + i];
    if (!bench_prom_nonempty(prom) || bench_prom_crc4(prom) != (prom[7] & 15U)) return;
    uint32_t startup_error = frame[W_BUS_ERROR]; frame[W_BUS_ERROR] = 0;
    int ok = baro_conversion(0x48, &d1, &t1);
    if (ok) frame[W_BARO_VALID_MASK] |= 1;
    if (ok) {
        ok = baro_conversion(0x58, &d2, &t2);
        if (ok) frame[W_BARO_VALID_MASK] |= 2;
    }
    frame[W_BARO_D1] = d1; frame[W_BARO_D2] = d2;
    frame[W_BARO_D1_MS] = t1; frame[W_BARO_D2_MS] = t2;
    frame[W_BARO_SAMPLE_ERROR] = frame[W_BUS_ERROR]; frame[W_BUS_ERROR] = startup_error;
    if (!ok) return;
    if (!d1 || !d2 || d1 == 0xffffffU || d2 == 0xffffffU) {
        frame[W_BARO_SAMPLE_ERROR] = 11; return;
    }
    ok = bench_ms5611(prom, d1, d2, &pressure, &temp);
    frame[W_PRESSURE_PA] = (uint32_t)pressure; frame[W_TEMP_CENTIC] = (uint32_t)temp;
    if (!ok) { frame[W_BARO_SAMPLE_ERROR] = 12; return; }
    frame[W_BARO_SAMPLE_STATUS] = STATUS_PASS;
}

static void sample_bench(void) {
    BenchADC a;
    frame[W_ACQ_COUNTER]++;
    for (unsigned i = W_ACQ_START_MS; i <= W_ADC_CR; ++i) frame[i] = 0;
    frame[W_ACQ_START_MS] = HAL_GetTick();
    frame[W_ADC_STATUS] = frame[W_BARO_SAMPLE_STATUS] = STATUS_RUNNING;
    /* Keep the last COMPLETE SRAM snapshot readable during acquisition.
     * Commit once below in main; a stalled conversion cannot advance heartbeat.
     */
    bench_adc_sample(&a);
    frame[W_ADC_STATUS] = a.status; frame[W_ADC_ERROR] = a.error;
    frame[W_ADC_HAL_ERROR] = a.hal_error; frame[W_ADC_INIT_ERROR] = a.init_error;
    frame[W_ADC_VALID_MASK] = a.valid; frame[W_ADC_CAL_RAW] = a.cal;
    frame[W_ADC_REF_RAW] = a.ref; frame[W_ADC_VLOGIC_RAW] = a.logic; frame[W_ADC_3V3_RAW] = a.v3;
    frame[W_VDDA_MV] = a.vdda_mv; frame[W_VLOGIC_MV] = a.logic_mv; frame[W_V3V3_MV] = a.v3_mv;
    frame[W_ADC_SAMPLE_MS] = a.sample_ms; frame[W_SYSCFG_PMCR] = a.pmcr;
    frame[W_ADC_CCR] = a.ccr; frame[W_ADC_PCSEL] = a.pcsel;
    frame[W_ADC_CFGR] = a.cfgr; frame[W_ADC_CR] = a.cr;
    sample_baro();
#ifdef M3_IMU_SAMPLES
    BenchIMU imu;
    bench_imu_sample(&imu);
    memcpy(&frame[W_IMU_SAMPLE_STATUS],&imu,sizeof(imu));
#endif
    frame[W_ACQ_FINISHED_MS] = HAL_GetTick();
}

int main(void) {
    uint32_t reset_flags = RCC->RSR;
    SystemCoreClockUpdate(); /* vendor SystemInit leaves HSI, no PLL */
    HAL_Init();
    /* No I/D cache enable: SWD sees committed SRAM rather than dirty cache. */
    setup_gpio();
#ifdef M3_POWER_STATUS
    bench_power_initialize();
#endif
    for (unsigned i = 0; i < MB_BYTES / 4; ++i) bench_mailbox[i] = 0; /* initialize SRAM/ECC */
    frame[W_MAGIC] = MB_MAGIC; frame[W_VERSION] = MB_VERSION; frame[W_LENGTH] = MB_BYTES;
    frame[W_CAPABILITIES] = MB_CAPABILITIES; frame[W_STATE] = STATE_BOOT;
    memcpy(&frame[W_BOARD_SHA], board_sha, 32); memcpy(&frame[W_BUILD_SHA], build_sha, 32);
    frame[W_RESET_FLAGS] = reset_flags; frame[W_DEVICE_ID] = DBGMCU->IDCODE;
    for (unsigned i = 0; i < 3; ++i) frame[W_UID + i] = ((const uint32_t *)UID_BASE)[i];
    frame[W_RCC_CFGR] = RCC->CFGR;
    frame[W_CAM_ENABLE_READBACK] = HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_3);
    publish();
    if (SystemCoreClock != 64000000U || (RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_HSI) {
        frame[W_STATE] = STATE_FATAL; frame[W_BUS_ERROR] = 6; publish();
        for (;;) { __NOP(); }
    }
    HAL_Delay(100); /* comfortably beyond sensor interface power-up delay */
    frame[W_STATE] = STATE_TESTING; frame[W_STAGE] = 1; frame[W_HSE_STATUS] = STATUS_RUNNING; publish();
    RCC_OscInitTypeDef oscillator = {0};
    oscillator.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    oscillator.HSEState = RCC_HSE_ON;
    oscillator.PLL.PLLState = RCC_PLL_NONE;
    HAL_StatusTypeDef result = HAL_RCC_OscConfig(&oscillator);
    frame[W_HSE_CR] = RCC->CR;
    frame[W_HSE_STATUS] = result == HAL_OK && (RCC->CR & RCC_CR_HSERDY) ? STATUS_PASS : STATUS_FAIL;
    /* Never switch SYSCLK to the tested oscillator. USB alone retains HSE
     * and uses an independent PLL3; older build modes keep their old behavior. */
#ifdef M3_USB
    bench_usb_initialize();publish();
#else
    oscillator.HSEState = RCC_HSE_OFF; (void)HAL_RCC_OscConfig(&oscillator); publish();
#endif
    test_imu(); test_baro(); test_flash();
#ifdef M3_CAMERA_UART
    CameraResult camera;
    frame[W_STAGE] = 6; frame[W_CAMERA_STATUS] = M3_CAMERA_QUERY ? STATUS_RUNNING : STATUS_NOT_TESTED;
    frame[W_CAMERA_MODE] = M3_CAMERA_QUERY;
    publish();
    bench_camera_query(M3_CAMERA_QUERY, &camera);
    memcpy(&frame[W_CAMERA_STATUS], &camera, sizeof(camera));
    frame[W_CAM_ENABLE_READBACK] = HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_3);
    publish();
#endif
#ifdef M3_IMU_SAMPLES
    BenchIMU imu;
    frame[W_STAGE]=7; frame[W_IMU_SAMPLE_STATUS]=STATUS_RUNNING; publish();
    bench_imu_initialize(&imu);
    memcpy(&frame[W_IMU_SAMPLE_STATUS],&imu,sizeof(imu)); publish();
#endif
#ifdef M3_STORAGE
    BenchStorage storage;
    uint8_t identity[76];memcpy(identity,board_sha,32);memcpy(identity+32,build_sha,32);
    memcpy(identity+64,&frame[W_UID],12);
    frame[W_STAGE]=8;frame[W_STORE_STATUS]=STORE_SCANNING;frame[W_STORE_MODE]=M3_STORAGE_RECORD;publish();
    bench_storage_begin(M3_STORAGE_RECORD,identity,&storage);
    memcpy(&frame[W_STORE_MODE],&storage,sizeof(storage));publish();
#endif
#ifdef M3_GNSS
    bench_gnss_initialize();publish();
#endif
    frame[W_STATE] = STATE_READY; frame[W_STAGE] = 5; frame[W_TEST_FINISHED_MS] = HAL_GetTick();
    for (;;) {
        uint32_t began = HAL_GetTick();
        sample_bench();
        frame[W_HEARTBEAT]++;
        frame[W_CAM_ENABLE_READBACK] = HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_3);
#ifdef M3_STORAGE
        frame[W_UPTIME_MS]=HAL_GetTick();frame[W_SEQUENCE]=0;
        /* Record the fixed v5 prefix: words0..126 + reserved zero word127.
         * Storage's live counters and v5 CRC are outside this 512-byte payload. */
        frame[127]=0;
#ifdef M3_GNSS
        /* v7 keeps a complete1024-byte snapshot (five pages); GNSS and USB
         * evidence must not silently disappear with the old512-byte prefix.
         * The storage counters describe state BEFORE this append. */
        bench_gnss_task();interfaces();frame[W_UPTIME_MS]=HAL_GetTick();
        frame[W_CRC32]=bench_crc32((const uint8_t *)frame,MB_BYTES-4);
#endif
        bench_storage_append((const uint8_t *)frame,frame[W_ACQ_COUNTER],&storage);
        memcpy(&frame[W_STORE_MODE],&storage,sizeof(storage));
#endif
        publish(); HAL_GPIO_TogglePin(GPIOE, GPIO_PIN_7);
        uint32_t elapsed = HAL_GetTick() - began;
        if (elapsed < 1000U) HAL_Delay(1000U - elapsed); /* nominal <=1 sample/s, no catch-up */
    }
}
