/* Input evidence only. No fault clearing, power cycling or actuator commands. */
#include "power_status.h"
#include <string.h>
_Static_assert(sizeof(BenchPowerStatus)==28,"Power result wire size");
void power_status_observe(PowerStatus *s,uint32_t now,uint32_t gpio,
                          uint32_t pending,int periodic,int config_ok){
    if(!s->initialized)return;
    BenchPowerStatus *r=&s->r;
    uint32_t gap=now-r->sampled_ms;
    if(gap>r->max_gap_ms)r->max_gap_ms=gap;
    if(gap>5U)r->flags|=POWER_GAP_SEEN;
    if(config_ok)r->flags|=POWER_CONFIG_VALID;
    else{r->flags&=~POWER_CONFIG_VALID;r->flags|=POWER_CONFIG_ERROR;}
    if(periodic)r->flags|=POWER_TICK_SEEN;
    pending&=POWER_PIN_MASK;
    if(pending){
        r->flags|=POWER_IRQ_SEEN;
        if(r->irq_count!=UINT32_MAX)r->irq_count++;
        else r->flags|=POWER_COUNT_SATURATED;
    }
    /* A falling-edge latch is evidence even if the input recovered before ISR.
     * ST has both edges enabled: its latch does NOT identify the edge direction. */
    r->history|=((~gpio)&POWER_PIN_MASK)|(pending&POWER_FAULT_MASK)|
                 ((gpio&POWER_PIN_MASK)<<16);
    if(pending||((gpio^r->gpio)&POWER_PIN_MASK))r->last_event_ms=now;
    r->gpio=gpio&0xffffU;r->sampled_ms=now;
}
void power_status_init(PowerStatus *s,uint32_t now,uint32_t gpio,int config_ok){
    memset(s,0,sizeof(*s));s->initialized=1;s->r.flags=POWER_CONFIGURED;
    s->r.gpio=gpio&0xffffU;s->r.sampled_ms=s->r.last_event_ms=now;
    power_status_observe(s,now,gpio,0,0,config_ok);
}
