/* Executes the actual production static bus routines against scripted line
 * levels and an independent rising-edge transaction recorder. No hardware.
 */
#define M3_HOST_TEST 1
#define main firmware_main_unused
#include "../src/main.c"
#undef main
#include <assert.h>
#include <stdio.h>

GPIO_TypeDef gb,gd,ge;
RCC_TypeDef rcc;
DBG_TypeDef dbg;
uint32_t uid[3],SystemCoreClock=64000000;
static unsigned ticks,imu_rx,flash_rx,sda_pos,sda_size;
static uint8_t imu_value=0xe9;
static uint32_t flash_value=0xef4018;
static int sda_bits[512],scl_stuck,active;
static uint8_t out_byte,tx[128],ack_tx[128];
static unsigned out_count,tx_count;
static uint8_t imu_tx[8],flash_tx[8],spi_acc[2];
static unsigned spi_n[2],spi_count[2];

uint32_t HAL_GetTick(void){ return ticks++; }
void HAL_Delay(uint32_t t){ ticks+=t+1; }
void HAL_IncTick(void){ ticks++; }
void HAL_Init(void){}
void bench_adc_sample(BenchADC *a){memset(a,0,sizeof(*a));} /* not exercised by this bus test */
void SystemCoreClockUpdate(void){}
void HAL_GPIO_Init(GPIO_TypeDef *p,GPIO_InitTypeDef *g){
    if(p==GPIOB && (g->Pin==GPIO_PIN_8 || g->Pin==GPIO_PIN_9)) assert(g->Mode==GPIO_MODE_OUTPUT_OD);
}
void HAL_GPIO_TogglePin(GPIO_TypeDef *p,uint16_t pin){p->output^=pin;}
HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *o){
    rcc.CR=o->HSEState ? RCC_CR_HSERDY : 0;return HAL_OK;
}
static void record_spi(unsigned channel,unsigned bit){
    spi_acc[channel]=(uint8_t)((spi_acc[channel]<<1)|bit);
    if(++spi_n[channel]==8){
        assert(spi_count[channel]<8);
        (channel ? flash_tx : imu_tx)[spi_count[channel]++]=spi_acc[channel];spi_n[channel]=0;spi_acc[channel]=0;
    }
}
void HAL_GPIO_WritePin(GPIO_TypeDef *p,uint16_t pin,int high){
    unsigned before=p->output;
    if(p==GPIOD && pin==GPIO_PIN_3) assert(high==0); /* no camera enable allowed */
    if(p==GPIOB && pin==GPIO_PIN_9 && (before&GPIO_PIN_8)){
        if(!high && (before&GPIO_PIN_9)){active=1;out_count=0;out_byte=0;}
        if(high && !(before&GPIO_PIN_9))active=0;
    }
    if(p==GPIOB && pin==GPIO_PIN_8 && high && !(before&GPIO_PIN_8) && active){
        if(out_count<8)out_byte=(uint8_t)((out_byte<<1)|!!(before&GPIO_PIN_9));
        if(++out_count==9){assert(tx_count<128);ack_tx[tx_count]=!!(before&GPIO_PIN_9);tx[tx_count++]=out_byte;out_byte=0;out_count=0;}
    }
    if(p==GPIOB && pin==GPIO_PIN_3 && high && !(before&GPIO_PIN_3) && !(before&GPIO_PIN_7))
        record_spi(0,!!(before&GPIO_PIN_5));
    if(p==GPIOB && pin==GPIO_PIN_2 && high && !(before&GPIO_PIN_2) && !(before&GPIO_PIN_6))
        record_spi(1,!!(gd.output&GPIO_PIN_11));
    if(high)p->output|=pin;else p->output&=~pin;
}
int HAL_GPIO_ReadPin(GPIO_TypeDef *p,uint16_t pin){
    if(p==GPIOB && pin==GPIO_PIN_4){unsigned bit=imu_rx++;return bit<8 ? 0 : ((imu_value>>(15-bit))&1);}
    if(p==GPIOD && pin==GPIO_PIN_12){unsigned bit=flash_rx++;return bit<8 ? 0 : ((flash_value>>(31-bit))&1);}
    if(p==GPIOB && pin==GPIO_PIN_8)return !scl_stuck;
    if(p==GPIOB && pin==GPIO_PIN_9){assert(sda_pos<sda_size);return sda_bits[sda_pos++];}
    return !!(p->output&pin);
}
static void reset_mock(void){
    memset(frame,0,sizeof(frame));gb.output=gd.output=ge.output=0;
    imu_rx=flash_rx=sda_pos=sda_size=out_count=tx_count=0;active=0;scl_stuck=0;ticks=0;
    memset(spi_n,0,sizeof(spi_n));memset(spi_count,0,sizeof(spi_count));memset(spi_acc,0,sizeof(spi_acc));
    setup_gpio();active=0;tx_count=0;
}
static void push(int bit){assert(sda_size<512);sda_bits[sda_size++]=bit;}
static void promscript(const uint16_t p[8]){
    push(1);push(0);push(0);push(1); /* reset: idle, address ACK, command ACK, STOP */
    for(unsigned i=0;i<8;i++){
        push(1);push(0);push(0);push(1); /* command phase */
        push(1);push(0); /* read address ACK */
        for(int bit=15;bit>=0;bit--)push((p[i]>>bit)&1);
        push(1); /* stop line released */
    }
}
static void conversion_script(uint32_t value){
    push(1);push(0);push(0);push(1); /* conversion command */
    push(1);push(0);push(0);push(1); /* ADC read command */
    push(1);push(0);
    for(int bit=23;bit>=0;bit--)push((value>>bit)&1);
    push(1);
}
static void sample_prom(void){
    uint16_t p[8]={0,40127,36924,23317,23282,33464,28312,0};
    p[7]=bench_prom_crc4(p);
    for(unsigned i=0;i<8;i++)frame[W_BARO_PROM+i]=p[i];
    frame[W_BARO_STATUS]=STATUS_PASS;
}
int main(void){
    uint16_t p[8]={0x3132,0x3334,0x3536,0x3738,0x3940,0x4142,0x4344,0x450b};
    reset_mock();imu_value=0xe9;test_imu();
    assert(frame[W_IMU_STATUS]==STATUS_PASS && frame[W_IMU_ID]==0xe9);
    assert(spi_count[0]==2 && imu_tx[0]==0xf2 && imu_tx[1]==0 && (gb.output&GPIO_PIN_7));
    reset_mock();imu_value=0xff;test_imu();assert(frame[W_IMU_STATUS]==STATUS_FAIL);
    reset_mock();flash_value=0xef4018;test_flash();
    assert(frame[W_FLASH_STATUS]==STATUS_PASS && frame[W_FLASH_ID]==0xef4018);
    assert(spi_count[1]==4 && flash_tx[0]==0x9f && flash_tx[1]==0 && flash_tx[2]==0 && flash_tx[3]==0);
    reset_mock();flash_value=0xffffff;test_flash();assert(frame[W_FLASH_STATUS]==STATUS_FAIL);
    reset_mock();promscript(p);test_baro();
    assert(frame[W_BARO_STATUS]==STATUS_PASS && sda_pos==sda_size);
    assert(tx_count==42 && tx[0]==0xee && tx[1]==0x1e);
    for(unsigned i=0;i<8;i++){
        assert(tx[2+5*i]==0xee && tx[3+5*i]==0xa0+2*i && tx[4+5*i]==0xef);
        assert(frame[W_BARO_PROM+i]==p[i]);
    }
    reset_mock();p[2]^=1;promscript(p);test_baro();assert(frame[W_BARO_STATUS]==STATUS_FAIL && frame[W_BUS_ERROR]==4);
    reset_mock();memset(p,0,sizeof(p));promscript(p);test_baro();assert(frame[W_BUS_ERROR]==5);
    reset_mock();push(1);push(1);push(1);test_baro();assert(frame[W_BARO_STATUS]==STATUS_FAIL && frame[W_BUS_ERROR]==3);
    reset_mock();scl_stuck=1;test_baro();assert(frame[W_BARO_STATUS]==STATUS_FAIL && frame[W_BUS_ERROR]==1 && ticks<100);
    reset_mock();sample_prom();conversion_script(9085466);conversion_script(8569150);sample_baro();
    assert(frame[W_BARO_SAMPLE_STATUS]==STATUS_PASS && frame[W_BARO_VALID_MASK]==3);
    assert(frame[W_PRESSURE_PA]==100009 && frame[W_TEMP_CENTIC]==2007);
    assert(frame[W_BARO_D1_MS]<frame[W_BARO_D2_MS] && tx_count==16 && sda_pos==sda_size);
    assert(tx[0]==0xee && tx[1]==0x48 && tx[2]==0xee && tx[3]==0 && tx[4]==0xef);
    assert(tx[8]==0xee && tx[9]==0x58 && tx[11]==0 && tx[12]==0xef);
    assert(ack_tx[5]==0 && ack_tx[6]==0 && ack_tx[7]==1); /* ACK, ACK, final NACK */
    assert(ack_tx[13]==0 && ack_tx[14]==0 && ack_tx[15]==1);
    reset_mock();sample_prom();conversion_script(0);conversion_script(8569150);sample_baro();
    assert(frame[W_BARO_SAMPLE_STATUS]==STATUS_FAIL && frame[W_BARO_SAMPLE_ERROR]==11);
    reset_mock();sample_prom();conversion_script(9085466);push(1);push(1);push(1);sample_baro();
    assert(frame[W_BARO_SAMPLE_ERROR]==3 && frame[W_BARO_VALID_MASK]==1 && frame[W_BARO_D2]==0);
    reset_mock();sample_prom();scl_stuck=1;sample_baro();
    assert(frame[W_BARO_SAMPLE_ERROR]==1 && frame[W_BARO_VALID_MASK]==0 && ticks<100);
    reset_mock();frame[W_BARO_STATUS]=STATUS_FAIL;sample_baro();
    assert(frame[W_BARO_SAMPLE_ERROR]==10 && tx_count==0); /* no reads with bad calibration */
    puts("14 scripted bus cases passed; actual production C routines, not hardware");
    return 0;
}
