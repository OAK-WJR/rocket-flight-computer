/* Run the real R10 main.c with scripted registers; never an emulated-board pass. */
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include "stm32h7xx.h"
#include "checks.h"
#define main r10_target_main
#include "../src/main.c"
#undef main

FakeSCB fake_scb;
FakeRCC fake_rcc;
FakePWR fake_pwr;
FakeSysTick fake_systick;
FakeDBG fake_dbg;
uint32_t fake_uid[3], SystemCoreClock;
static unsigned irq_enabled, sleep_count, throw_fault, config_fail, inject_publish, stop_after;
static unsigned sensor_present, sensor_error_at, sensor_calls;
static uint8_t sensor_regs[128];
static unsigned baro_present;
static uint8_t baro_command,baro_conversion;
static uint32_t baro_ready;
static uint16_t baro_prom[8];
static r10_adc_port fake_voltage_port;
static unsigned voltage_present,voltage_error_at,voltage_slot;
static jmp_buf escape;
static int sensor_init(void *p,uint32_t *hz,uint32_t *detail) {
    (void)p;*hz=sensor_present?1000000u:0u;*detail=sensor_present?0u:1u;
    return sensor_present?0:-1;
}
static int sensor_exchange(void *p,const uint8_t *tx,uint8_t *rx,size_t n,uint32_t *detail) {
    (void)p;++sensor_calls;
    if(sensor_error_at && sleep_count>=sensor_error_at){*detail=0x03200000u;return -1;}
    uint8_t address=tx[0]&0x7fu;rx[0]=0;
    for(size_t i=1;i<n;++i) {
        if(tx[0]&0x80u)rx[i]=sensor_regs[address+i-1];
        else if(address==1u && (tx[i]&4u))sensor_regs[1]=0; /* completed POR in model */
        else sensor_regs[address+i-1]=tx[i];
    }
    return 0;
}
const r10_imu_io *r10_native_imu_io(void) {
    static const r10_imu_io io={.initialize=sensor_init,.exchange=sensor_exchange};
    return &io;
}
static int baro_init(void *p,uint32_t *hz,uint32_t *detail) {
    (void)p;*hz=baro_present?50000u:0;*detail=baro_present?0:42;return baro_present?0:-1;
}
static int baro_transfer(void *p,uint8_t addr,const uint8_t *tx,size_t nt,uint8_t *rx,size_t nr,uint32_t *detail) {
    (void)p;(void)detail;assert(addr==0x77);
    if(nt) {
        assert(nt==1 && !nr);baro_command=tx[0];
        if(tx[0]==0x1e){baro_conversion=0;baro_ready=ticks_lo+3;}
        if(tx[0]==0x48 || tx[0]==0x58){assert(!baro_conversion);baro_conversion=tx[0];baro_ready=ticks_lo+10;}
    } else if(nr==2) {
        assert(baro_command>=0xa0 && baro_command<=0xae);
        uint16_t word=baro_prom[(baro_command-0xa0)/2];rx[0]=word>>8;rx[1]=(uint8_t)word;
    } else {
        assert(nr==3 && baro_command==0 && baro_conversion && (uint32_t)(ticks_lo-baro_ready)<0x80000000u);
        uint32_t raw=baro_conversion==0x48?9085466u:8569150u;
        rx[0]=raw>>16;rx[1]=raw>>8;rx[2]=(uint8_t)raw;baro_conversion=0;
    }
    return 0;
}
const r10_baro_io *r10_native_baro_io(void) {
    static const r10_baro_io io={.initialize=baro_init,.transfer=baro_transfer};return &io;
}
static int voltage_init(void *p,uint32_t now,r10_voltage_config *c,uint32_t *detail) {
    (void)p;(void)now;*detail=voltage_present?0u:0x02000000u;
    if (!voltage_present) return R10_VOLTAGE_IO_ERROR;
    *c=(r10_voltage_config){0x2003u,24000u,10u,2000000u,2000000u};
    fake_voltage_port.phase=A_READY;fake_voltage_port.owned=1u;
    fake_voltage_port.revision=0x2003u;fake_voltage_port.calibration=24000u;
    fake_voltage_port.nominal_adc_hz=2000000u;return R10_VOLTAGE_IO_OK;
}
static int voltage_start(void *p,unsigned slot,uint32_t *detail) {
    (void)p;assert(slot<5u && !fake_voltage_port.active);
    if (voltage_error_at && sleep_count>=voltage_error_at) {
        *detail=0x0b800001u;return R10_VOLTAGE_IO_ERROR;
    }
    voltage_slot=slot;fake_voltage_port.active=1u;fake_voltage_port.unit=slot==1u || slot==2u?1u:3u;
    *detail=0u;return R10_VOLTAGE_IO_OK;
}
static int voltage_read(void *p,uint32_t *raw,uint32_t *detail) {
    (void)p;static const uint32_t data[5]={375u,140u,155u,256u,375u};
    assert(fake_voltage_port.active);*raw=data[voltage_slot];*detail=0u;
    fake_voltage_port.last_dr=*raw;fake_voltage_port.active=0u;return R10_VOLTAGE_IO_OK;
}
static int voltage_cancel(void *p,uint32_t *detail) {
    (void)p;fake_voltage_port.phase=A_NEW;fake_voltage_port.active=fake_voltage_port.owned=0u;
    *detail=0u;return R10_VOLTAGE_IO_OK;
}
const r10_voltage_io *r10_native_voltage_io(void) {
    static const r10_voltage_io io={.initialize=voltage_init,.start=voltage_start,
                                  .poll=voltage_read,.cancel=voltage_cancel};return &io;
}
const r10_adc_port *r10_native_adc_state(void) {return &fake_voltage_port;}
void __disable_irq(void) {irq_enabled=0;}
void __enable_irq(void) {irq_enabled=1;}
void __DSB(void) {}
void __ISB(void) {}
uint32_t __get_IPSR(void) {return 3;}
void SystemCoreClockUpdate(void) {}
uint32_t SysTick_Config(uint32_t ticks) {
    if (config_fail) return 1;
    fake_systick.LOAD=ticks-1;
    return 0;
}
void r10_publish_observe(volatile uint32_t *dest, const uint32_t *generation) {
    assert(dest[R10_SEQ]==*generation); /* generation is reserved before exposure */
    if (inject_publish) {
        inject_publish=0;
        r10_observation fault={.state=R10_STATE_FAULT,.exception=3};
        uint32_t next_frame[R10_WORDS];
        uint32_t previous=*generation;
        r10_frame(next_frame,&fault,R10_BOARD_HASH,R10_BUILD_HASH);
        r10_publish(dest,next_frame,&sequence);
        assert(dest[R10_SEQ]!=previous && dest[4]==R10_STATE_FAULT);
        longjmp(escape,1); /* exception handler never resumes the interrupted writer */
    }
}
void __WFI(void) {
    if (!irq_enabled || ++sleep_count > stop_after) longjmp(escape,1);
    if (throw_fault && sleep_count==2505) {
        fake_scb.CFSR=1u<<15;
        fake_scb.HFSR=1u<<30;
        fake_scb.BFAR=0x12345678;
        Default_Handler();
    }
    SysTick_Handler();
}

static void reset_model(void) {
    memset(&fake_scb,0,sizeof fake_scb);memset(&fake_rcc,0,sizeof fake_rcc);
    memset(&fake_systick,0,sizeof fake_systick);memset(&obs,0,sizeof obs);
    memset(frame,0,sizeof frame);
    memset(&imu,0,sizeof imu);memset(sensor_regs,0,sizeof sensor_regs);
    memset(&baro,0,sizeof baro);baro_present=baro_command=baro_conversion=baro_ready=0;
    memset(&voltage,0,sizeof voltage);memset(&fake_voltage_port,0,sizeof fake_voltage_port);
    voltage_present=voltage_error_at=voltage_slot=0u;
    const uint16_t coefficients[]={0,40127,36924,23317,23282,33464,28312,0};
    for(unsigned i=0;i<8;++i)baro_prom[i]=coefficients[i];
    baro_prom[7]=bench_prom_crc4(baro_prom);
    sensor_present=sensor_error_at=sensor_calls=0;
    sensor_regs[0x0f]=0x73;sensor_regs[0x15]=8;sensor_regs[0x1e]=0x0f;
    for(unsigned i=0;i<14;++i)sensor_regs[0x20+i]=(uint8_t)(i+1);
    for(unsigned i=0;i<6;++i)sensor_regs[0x34+i]=(uint8_t)(i+20);
    for(unsigned i=0;i<R10_WORDS;++i) r10_mailbox[i]=0;
    ticks_lo=ticks_hi=main_count=sequence=ready=0;
    sleep_count=throw_fault=config_fail=irq_enabled=inject_publish=0;
    stop_after=3005;
    fake_scb.CPUID=0x411fc271;
    fake_dbg.IDCODE=0x20030450;
    fake_rcc.RSR=0x00800000;
    fake_uid[0]=123;fake_uid[1]=456;fake_uid[2]=789;
    SystemCoreClock=64000000;
}
static void run_main(void) {
    if(setjmp(escape)==0) (void)r10_target_main();
}
static void valid_record(uint32_t state) {
    uint32_t copy[R10_WORDS];
    for(unsigned i=0;i<R10_WORDS;++i)copy[i]=r10_mailbox[i];
    assert(copy[0]==R10_MAGIC && copy[1]==R10_ABI && copy[2]==1024);
    assert(copy[3]!=0 && (copy[3]&1)==0 && copy[4]==state);
    assert(copy[R10_CRC]==r10_crc32((const uint8_t*)copy,R10_CRC*4));
    assert(copy[27]==2 && copy[44]==63);
}
int main(void) {
    reset_model();run_main();valid_record(R10_STATE_RUNNING);
    assert(r10_mailbox[5]==3000 && r10_mailbox[7]==3000);
    assert(r10_mailbox[13]==0x00800000 && fake_rcc.RSR==0x00800000);
    assert(r10_mailbox[25]==63999 && fake_scb.VTOR==FLASH_BASE);
    assert(r10_mailbox[45]==R10_IMU_ERROR && r10_mailbox[46]==R10_IMU_PORT);
    assert(sensor_calls==0); /* MCU heartbeat survives a missing sensor */
    assert(r10_mailbox[64]==R10_BARO_ERROR && r10_mailbox[65]==R10_BARO_PORT);
    reset_model();sensor_present=baro_present=1;run_main();valid_record(R10_STATE_RUNNING);
    assert(r10_mailbox[67]>0 && (r10_mailbox[66]&0x103u)==0x103u);
    assert(r10_mailbox[75]==100009 && r10_mailbox[76]==2007 && baro.samples>0);
    reset_model();sensor_present=1;run_main();valid_record(R10_STATE_RUNNING);
    assert(r10_mailbox[45]==R10_IMU_READY && r10_mailbox[48]>0 && r10_mailbox[59]==1000000u);
    assert((r10_mailbox[47]&0x010f0000u)==0x010f0000u && r10_mailbox[51]==0x06050403u);
    reset_model();sensor_present=1;sensor_error_at=2400;run_main();valid_record(R10_STATE_RUNNING);
    assert(r10_mailbox[45]==R10_IMU_ERROR && r10_mailbox[46]==R10_IMU_CONFIG_READ);
    assert(r10_mailbox[48]>0 && r10_mailbox[58]==1 && !(r10_mailbox[47]&0x00ff0000u));
    reset_model();voltage_present=1;run_main();valid_record(R10_STATE_RUNNING);
    assert(r10_mailbox[139]>0u && r10_mailbox[144]==3u);
    assert(r10_mailbox[176]>4900u && r10_mailbox[176]<5000u);
    reset_model();voltage_present=1;voltage_error_at=2400;run_main();valid_record(R10_STATE_RUNNING);
    assert(r10_mailbox[139]>0u && r10_mailbox[144]==2u && r10_mailbox[129]==R10_VOLTAGE_START_ERROR);
    assert(r10_mailbox[155]==375u && r10_mailbox[176]>4900u);
    reset_model();sensor_present=baro_present=voltage_present=1;throw_fault=1;run_main();valid_record(R10_STATE_FAULT);
    assert(imu.samples>0); /* exception must not expose a partially updated IMU object */
    for(unsigned i=45;i<63;++i)assert(r10_mailbox[i]==0);
    assert(baro.samples>0);for(unsigned i=64;i<R10_CRC;++i)assert(r10_mailbox[i]==0);
    reset_model();stop_after=999;run_main();valid_record(R10_STATE_STARTING);
    assert(r10_mailbox[5]==0 && ticks_lo==999);
    reset_model();throw_fault=1;run_main();valid_record(R10_STATE_FAULT);
    assert(r10_mailbox[26]==3 && r10_mailbox[22]==0x12345678 && !irq_enabled);
    reset_model();fake_dbg.IDCODE=0;run_main();valid_record(R10_STATE_FAULT);
    assert(r10_mailbox[26]==0xffff0001u && !irq_enabled && sleep_count==0);
    reset_model();fake_scb.CPUID=0;run_main();valid_record(R10_STATE_FAULT);
    reset_model();SystemCoreClock=0;run_main();valid_record(R10_STATE_FAULT);
    reset_model();SystemCoreClock=64000001;run_main();valid_record(R10_STATE_FAULT);
    reset_model();fake_rcc.CFGR=0x08;run_main();valid_record(R10_STATE_FAULT);
    reset_model();config_fail=1;run_main();valid_record(R10_STATE_FAULT);
    reset_model();ticks_lo=0xffffffffu;ticks_hi=9;SysTick_Handler();
    assert(ticks_lo==0 && ticks_hi==10);
    reset_model();inject_publish=1;
    if(setjmp(escape)==0)sample(R10_STATE_RUNNING,0);
    valid_record(R10_STATE_FAULT);
    assert(r10_mailbox[R10_SEQ]==4 && sequence==4);
    puts("scripted runtime cases passed; no hardware tested");
    return 0;
}
