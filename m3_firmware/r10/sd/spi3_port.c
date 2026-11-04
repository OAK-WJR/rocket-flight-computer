#include "spi3_port.h"
#include <string.h>

static uint32_t rd(r10_sd_spi3_port *p,uint32_t a) {return p->io.read(p->io.context,a,4);}
static void wr(r10_sd_spi3_port *p,uint32_t a,uint32_t v) {p->io.write(p->io.context,a,v,4);}
static void modify(r10_sd_spi3_port *p,uint32_t a,uint32_t m,uint32_t v) {wr(p,a,(rd(p,a)&~m)|v);}
static int fail(r10_sd_spi3_port *p,unsigned e,uint32_t *detail) {
 p->error=e;p->detail=(e<<24)|(p->stage<<16)|(p->last_sr&0xffffu);
 p->ready=0;*detail=p->detail;return SDQ_IO_ERROR;
}
static int clock_ok(r10_sd_spi3_port *p) {
 p->observed_clock[0]=rd(p,SD3_CR);p->observed_clock[1]=rd(p,SD3_CFGR);
 p->observed_clock[2]=rd(p,SD3_D1CFGR);p->observed_clock[3]=rd(p,SD3_D1CCIPR);
 p->observed_clock[4]=rd(p,SD3_D2CCIP1R);
 return (p->observed_clock[0]&0x1du)==5u && !(p->observed_clock[1]&0x3fu) &&
        !(p->observed_clock[2]&0xf0fu) && !(p->observed_clock[3]&0x30000000u) &&
        (p->observed_clock[4]&0x7000u)==0x4000u;
}
static int pins_ok(r10_sd_spi3_port *p) {
 static const uint32_t addresses[10]={SD3_GPIOC+SD3_MODER,SD3_GPIOC+SD3_TYPE,
  SD3_GPIOC+SD3_PULL,SD3_GPIOC+SD3_SPEED,SD3_GPIOC+SD3_AFRH,SD3_GPIOD+SD3_MODER,
  SD3_GPIOD+SD3_TYPE,SD3_GPIOD+SD3_PULL,SD3_GPIOD+SD3_SPEED,SD3_GPIOD+SD3_IDR};
 for (unsigned i=0;i<10u;++i)p->observed_pins[i]=rd(p,addresses[i]);
 return (p->observed_pins[0]&SD3_GPIO_FIELDS)==SD3_GPIO_AF_MODES &&
  !(p->observed_pins[1]&SD3_GPIO_TYPES) && !(p->observed_pins[2]&SD3_GPIO_FIELDS) &&
  !(p->observed_pins[3]&SD3_GPIO_FIELDS) && (p->observed_pins[4]&SD3_AF_MASK)==SD3_AF_VALUE &&
  (p->observed_pins[5]&3u)==1u && !(p->observed_pins[6]&1u) && !(p->observed_pins[7]&3u) &&
  !(p->observed_pins[8]&3u) && (p->observed_pins[9]&1u)==(p->selected?0u:1u);
}
static int config_ok(r10_sd_spi3_port *p) {
 p->observed_config[0]=rd(p,SD3_CFG1);p->observed_config[1]=rd(p,SD3_CFG2);
 p->observed_config[2]=rd(p,SD3_IER);p->observed_config[3]=rd(p,SD3_I2S);
 return p->observed_config[0]==SD3_CONFIG1 && p->observed_config[1]==SD3_CONFIG2 &&
        !p->observed_config[2] && !p->observed_config[3] &&
        (rd(p,SD3_ENABLE)&SD3_GATE) && !(rd(p,SD3_RESET)&SD3_GATE);
}
static int reset_spi3(r10_sd_spi3_port *p) {
 modify(p,SD3_RESET,SD3_GATE,SD3_GATE);unsigned asserted=!!(rd(p,SD3_RESET)&SD3_GATE);
 modify(p,SD3_RESET,SD3_GATE,0);return asserted && !(rd(p,SD3_RESET)&SD3_GATE);
}
static int wait_flag(r10_sd_spi3_port *p,uint32_t flag,uint32_t *budget,uint32_t *detail) {
 while (*budget) {
  --*budget;p->last_sr=rd(p,SD3_SR);
  if (p->last_sr&(SD3_ERRORS|SD3_SUSP))return fail(p,SD3_STATUS,detail);
  if ((p->last_sr&flag)==flag)return SDQ_IO_OK;
 }
 return fail(p,SD3_BUDGET,detail);
}
int r10_sd_spi3_transfer(void *context,const uint8_t *tx,uint8_t *rx,unsigned n,
                       unsigned *accepted,unsigned *received,uint32_t *detail) {
 r10_sd_spi3_port *p=context;*accepted=*received=0;*detail=0;p->stage=4;p->accepted=p->received=0;
 if (!p->ready || !tx || !rx || !n || n>16u)return fail(p,SD3_ARGUMENT,detail);
 if (!clock_ok(p))return fail(p,SD3_CLOCK,detail);
 if (!config_ok(p) || !pins_ok(p) || (rd(p,SD3_CR1)&0x1201u)!=0x1000u)return fail(p,SD3_CONFIG,detail);
 uint32_t budget=p->poll_limit;
 wr(p,SD3_IFCR,SD3_FLAGS);wr(p,SD3_CR2,n);modify(p,SD3_CR1,1u,1u);
 modify(p,SD3_CR1,0x200u,0x200u);
 for (unsigned i=0;i<n;++i) {
  p->stage=5;if (wait_flag(p,SD3_TXP,&budget,detail)!=SDQ_IO_OK)goto failed;
  p->io.write(p->io.context,SD3_TXDR,tx[i],1);p->accepted=++*accepted;
  p->stage=6;if (wait_flag(p,SD3_RXP,&budget,detail)!=SDQ_IO_OK)goto failed;
  rx[i]=(uint8_t)p->io.read(p->io.context,SD3_RXDR,1);p->received=++*received;
 }
 p->stage=7;if (wait_flag(p,SD3_EOT,&budget,detail)!=SDQ_IO_OK)goto failed;
 p->last_sr=rd(p,SD3_SR);
 if (p->last_sr&(SD3_ERRORS|SD3_SUSP))return fail(p,SD3_STATUS,detail);
 if (p->last_sr&SD3_RX_PENDING)return fail(p,SD3_EXTRA_RX,detail);
 /* ES0392 post-EOT disable guard: engineering starting point only. Clock
  * policy is HSI64, but real SCK/CS setup/hold and truncation need waveforms. */
 p->io.delay_cycles(p->io.context,512);
 modify(p,SD3_CR1,1u,0);wr(p,SD3_IFCR,SD3_FLAGS);
 if (rd(p,SD3_CR1)&0x201u)return fail(p,SD3_CONFIG,detail);
 p->stage=0;return SDQ_IO_OK;
failed:
 return SDQ_IO_ERROR; /* Query failure then calls bounded owned-resource release. */
}
int r10_sd_spi3_select(void *context,unsigned asserted,uint32_t *detail) {
 r10_sd_spi3_port *p=context;*detail=0;p->stage=8;
 if (!p->ready || asserted>1u)return fail(p,SD3_ARGUMENT,detail);
 if (!clock_ok(p))return fail(p,SD3_CLOCK,detail);
 if (!config_ok(p) || (rd(p,SD3_CR1)&0x201u))return fail(p,SD3_CONFIG,detail);
 /* transfer() never touches this GPIO: selection persists across polls. */
 wr(p,SD3_GPIOD+SD3_BSRR,asserted?0x10000u:1u);p->selected=asserted;
 p->io.delay_cycles(p->io.context,512);
 if (!pins_ok(p))return fail(p,SD3_GPIO,detail);
 p->stage=0;return SDQ_IO_OK;
}
int r10_sd_spi3_initialize(void *context,uint32_t *hz,uint32_t *clocks,uint32_t *detail) {
 r10_sd_spi3_port *p=context;*hz=*clocks=*detail=0;p->stage=1;p->error=p->detail=0;
 if (!p->io.read || !p->io.write || !p->io.delay_cycles || !p->poll_limit || p->poll_limit>1000000u)
  return fail(p,SD3_ADAPTER,detail);
 if (p->owned || (rd(p,SD3_ENABLE)&SD3_GATE) || (rd(p,SD3_RESET)&SD3_GATE))
  return fail(p,SD3_OWNERSHIP,detail);
 if (!clock_ok(p))return fail(p,SD3_CLOCK,detail);
 modify(p,SD3_GPIO_ENABLE,SD3_GPIO_GATES,SD3_GPIO_GATES);
 if ((rd(p,SD3_GPIO_ENABLE)&SD3_GPIO_GATES)!=SD3_GPIO_GATES)return fail(p,SD3_GPIO_CLOCK,detail);
 p->owned=SD3_GPIO_OWNED;p->selected=0;
 wr(p,SD3_GPIOD+SD3_BSRR,1u);modify(p,SD3_GPIOD+SD3_TYPE,1u,0);
 modify(p,SD3_GPIOD+SD3_PULL,3u,0);modify(p,SD3_GPIOD+SD3_SPEED,3u,0);
 modify(p,SD3_GPIOD+SD3_MODER,3u,1u);
 if (!(rd(p,SD3_GPIOD+SD3_IDR)&1u))return fail(p,SD3_GPIO,detail);
 p->owned|=SD3_SPI_OWNED;modify(p,SD3_ENABLE,SD3_GATE,SD3_GATE);
 if (!(rd(p,SD3_ENABLE)&SD3_GATE))return fail(p,SD3_SPI_CLOCK,detail);
 p->stage=2;if (!reset_spi3(p))return fail(p,SD3_SPI_RESET,detail);
 wr(p,SD3_CR1,0x1000u);wr(p,SD3_CR2,0);wr(p,SD3_IER,0);wr(p,SD3_I2S,0);
 wr(p,SD3_CFG1,SD3_CONFIG1);wr(p,SD3_CFG2,SD3_CONFIG2);wr(p,SD3_IFCR,SD3_FLAGS);
 modify(p,SD3_GPIOC+SD3_TYPE,SD3_GPIO_TYPES,0);modify(p,SD3_GPIOC+SD3_PULL,SD3_GPIO_FIELDS,0);
 modify(p,SD3_GPIOC+SD3_SPEED,SD3_GPIO_FIELDS,0);modify(p,SD3_GPIOC+SD3_AFRH,SD3_AF_MASK,SD3_AF_VALUE);
 modify(p,SD3_GPIOC+SD3_MODER,SD3_GPIO_FIELDS,SD3_GPIO_AF_MODES);
 p->stage=3;
 if (!clock_ok(p))return fail(p,SD3_CLOCK,detail);
 if (!config_ok(p) || !pins_ok(p))return fail(p,SD3_CONFIG,detail);
 p->ready=1;uint8_t tx[10];memset(tx,0xff,sizeof(tx));unsigned accepted=0,received=0;
 /* One80-clock transfer with CS high, not ten separately selected bytes. */
 if (r10_sd_spi3_transfer(p,tx,p->idle_rx,10,&accepted,&received,detail)!=SDQ_IO_OK)return SDQ_IO_ERROR;
 *hz=250000u;*clocks=80u;p->stage=0;return SDQ_IO_OK;
}
int r10_sd_spi3_release(void *context,uint32_t *detail) {
 r10_sd_spi3_port *p=context;*detail=0;
 if (!p->owned)return SDQ_IO_OK; /* An unclaimed external SPI3 is never reset. */
 p->ready=0;p->stage=9;unsigned ok=1;
 if (p->owned&SD3_GPIO_OWNED)wr(p,SD3_GPIOD+SD3_BSRR,1u);
 if (p->owned&SD3_SPI_OWNED) {
  if (rd(p,SD3_ENABLE)&SD3_GATE) {
   if ((rd(p,SD3_CR1)&0x201u)==0x201u) {
    modify(p,SD3_CR1,0x400u,0x400u);uint32_t budget=128;
    while (budget && !(rd(p,SD3_SR)&SD3_SUSP) && (rd(p,SD3_CR1)&0x200u))--budget;
   }
   if (!reset_spi3(p))ok=0;
   if (rd(p,SD3_CR1)&0x201u)ok=0;
  }
  modify(p,SD3_ENABLE,SD3_GATE,0);
  if (rd(p,SD3_ENABLE)&SD3_GATE)ok=0;
 }
 if (p->owned&SD3_GPIO_OWNED) {
  modify(p,SD3_GPIOC+SD3_MODER,SD3_GPIO_FIELDS,SD3_GPIO_FIELDS);
  modify(p,SD3_GPIOC+SD3_PULL,SD3_GPIO_FIELDS,0);
  if ((rd(p,SD3_GPIOC+SD3_MODER)&SD3_GPIO_FIELDS)!=SD3_GPIO_FIELDS ||
      (rd(p,SD3_GPIOC+SD3_PULL)&SD3_GPIO_FIELDS) || !(rd(p,SD3_GPIOD+SD3_IDR)&1u))ok=0;
 }
 if (!ok) {p->cleanup_error=SD3_CLEANUP;p->cleanup_detail=(p->stage<<16)|(p->last_sr&0xffffu);*detail=p->cleanup_detail;return SDQ_IO_ERROR;}
 p->owned=0;p->selected=0;p->stage=0;return SDQ_IO_OK;
}
void r10_sd_spi3_bus(r10_sd_spi3_port *p,r10_sd_bus *bus) {
 bus->context=p;bus->initialize=r10_sd_spi3_initialize;bus->select=r10_sd_spi3_select;
 bus->transfer=r10_sd_spi3_transfer;bus->release=r10_sd_spi3_release;
}
