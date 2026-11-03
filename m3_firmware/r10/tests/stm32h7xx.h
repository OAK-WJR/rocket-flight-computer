/* Scripted host register model only. Not MCU/device-header replacement. */
#ifndef R10_SCRIPTED_STM32_H
#define R10_SCRIPTED_STM32_H
#include <stdint.h>
typedef struct {uint32_t VTOR,CPUID,CFSR,HFSR,DFSR,MMFAR,BFAR,ICSR;} FakeSCB;
typedef struct {uint32_t CR,CFGR,D1CFGR,RSR;} FakeRCC;
typedef struct {uint32_t CSR1;} FakePWR;
typedef struct {uint32_t LOAD;} FakeSysTick;
typedef struct {uint32_t IDCODE;} FakeDBG;
extern FakeSCB fake_scb;
extern FakeRCC fake_rcc;
extern FakePWR fake_pwr;
extern FakeSysTick fake_systick;
extern FakeDBG fake_dbg;
extern uint32_t fake_uid[3], SystemCoreClock;
#define SCB (&fake_scb)
#define RCC (&fake_rcc)
#define PWR (&fake_pwr)
#define SysTick (&fake_systick)
#define DBGMCU (&fake_dbg)
#define UID_BASE ((uintptr_t)fake_uid)
#define FLASH_BASE 0x08000000u
#define RCC_CFGR_SWS 0x38u
#define RCC_CFGR_SWS_HSI 0u
void __disable_irq(void);
void __enable_irq(void);
void __DSB(void);
void __ISB(void);
void __WFI(void);
uint32_t __get_IPSR(void);
void SystemCoreClockUpdate(void);
uint32_t SysTick_Config(uint32_t ticks);
#endif
