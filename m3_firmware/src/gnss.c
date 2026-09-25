/* u-blox SPG5.10 UBX-21035062 R03 pp41-44,89-90,98-100.
 * Bounded receiver diagnostics. No configuration writes or control outputs.
 */
#include "gnss.h"
#include <string.h>
_Static_assert(sizeof(BenchGNSS)==284,"GNSS wire words184..254");
static uint32_t u32(const uint8_t *p){return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void reset(GNSS *g){g->phase=0;g->used=0;g->length=0;g->nmea_used=0;}
static int hex(uint8_t x){return x>='0'&&x<='9'?x-'0':x>='A'&&x<='F'?x-'A'+10:x>='a'&&x<='f'?x-'a'+10:-1;}
static int text_is(const uint8_t *p,unsigned n,const char *s){size_t z=strlen(s);return z<n&&!memcmp(p,s,z)&&p[z]==0;}
static int firmware_known(const uint8_t *p){
    /* MON-VER includes a ROM revision hash, e.g. "ROM SPG 5.10 (7b202e)".
     * Keep that exact raw string; do not incorrectly require it to end at5.10. */
    return !memcmp(p,"ROM SPG 5.10",12)&&(p[12]==0||(p[12]==' '&&p[13]=='('))&&memchr(p,0,30)!=0;
}
void gnss_init(GNSS *g,uint32_t now){memset(g,0,sizeof(*g));g->started=now;g->now=now;g->result.state=GNSS_LISTENING;}
void gnss_loss(GNSS *g,uint32_t dropped,uint32_t errors){
    reset(g);g->result.dropped+=dropped;g->result.uart_errors|=errors;
    g->result.history|=(dropped?GNSS_H_OVERFLOW:0)|(errors?GNSS_H_UART:0);
    /* A broken byte stream cannot keep the previous solution marked fresh. */
    g->epoch_current=0;
}
static void message(GNSS *g,uint32_t now){
    BenchGNSS *r=&g->result;uint8_t *p=g->payload;r->ubx_good++;
    if(g->kind==10&&g->id==4){
        if(g->length<40||(g->length-40)%30){r->bad_length++;r->history|=GNSS_H_LENGTH;return;}
        memset(r->version,0,sizeof(r->version));memcpy(r->version,p,40);
        for(unsigned i=40;i<g->length;i+=30){
            if(!memcmp(p+i,"PROTVER=",8))memcpy(r->version+40,p+i,30);
            if(!memcmp(p+i,"MOD=",4))memcpy(r->version+70,p+i,30);
        }
        r->flags|=GNSS_VER;r->flags&=~GNSS_ID_OK;r->version_len=g->length;r->mon_ms=now;
        if(firmware_known(r->version)&&text_is(r->version+40,30,"PROTVER=34.10")&&
           text_is(r->version+70,30,"MOD=SAM-M10Q"))r->flags|=GNSS_ID_OK;
        else r->history|=GNSS_H_ID;
    }else if(g->kind==1&&g->id==7){
        if(g->length!=92){r->bad_length++;r->history|=GNSS_H_LENGTH;return;}
        memcpy(r->pvt,p,92);r->pvt_count++;r->pvt_ms=now;r->flags|=GNSS_PVT;
        uint32_t tow=u32(p);
        if(tow>=604800000U){g->epoch_current=0;r->history|=GNSS_H_EPOCH;return;}
        uint32_t delta=(tow+604800000U-g->last_epoch)%604800000U;
        if(!g->have_epoch||(delta>0&&delta<302400000U)){
            g->last_epoch=tow;g->have_epoch=1;r->epoch_ms=now;g->epoch_current=1;
        }else if(delta){g->epoch_current=0;r->history|=GNSS_H_EPOCH;}
    }
}
void gnss_tick(GNSS *g,uint32_t now){
    BenchGNSS *r=&g->result;
    if(r->state==GNSS_OFF)return;
    if((g->phase||g->nmea_used)&&(uint32_t)(now-r->last_byte_ms)>400U){
        reset(g);r->timeouts++;r->history|=GNSS_H_TIMEOUT;
    }
    g->now=now;r->flags&=~(GNSS_POSITION|GNSS_UTC|GNSS_FRESH);
    if(r->error){r->state=GNSS_HAL_ERROR;return;}
    if(!(r->flags&GNSS_PVT)){
        r->state=(uint32_t)(now-g->started)>5000U?GNSS_NO_DATA:GNSS_LISTENING;return;
    }
    const uint8_t *p=r->pvt;
    if((p[20]==2||p[20]==3)&&(p[21]&1)&&!(p[78]&1)){
        int32_t lon=(int32_t)u32(p+24),lat=(int32_t)u32(p+28);
        if(lon>=-1800000000&&lon<=1800000000&&lat>=-900000000&&lat<=900000000)r->flags|=GNSS_POSITION;
    }
    if((p[11]&7)==7)r->flags|=GNSS_UTC;
    if(g->epoch_current&&(uint32_t)(now-r->pvt_ms)<=3000U&&(uint32_t)(now-r->epoch_ms)<=3000U)r->flags|=GNSS_FRESH;
    if(!(r->flags&GNSS_ID_OK))r->state=GNSS_UNKNOWN_ID;
    else if(!(r->flags&GNSS_FRESH))r->state=GNSS_STALE;
    else r->state=r->flags&GNSS_POSITION?GNSS_FIX:GNSS_NO_FIX;
}
void gnss_feed(GNSS *g,uint8_t b,uint32_t now){
    gnss_tick(g,now);BenchGNSS *r=&g->result;r->rx_bytes++;r->last_byte_ms=now;
    if(!g->phase){
        if(b==0xb5){g->nmea_used=0;g->phase=1;return;}
        if(b=='$'){g->nmea_used=1;g->nmea[0]=b;return;}
        if(!g->nmea_used)return;
        if(g->nmea_used==sizeof(g->nmea)){g->nmea_used=0;r->bad_length++;r->history|=GNSS_H_LENGTH;return;}
        g->nmea[g->nmea_used++]=b;
        if(b=='\n'){
            unsigned n=g->nmea_used;int good=0;
            if(n>=7&&g->nmea[n-2]=='\r'&&g->nmea[n-5]=='*'){
                unsigned ck=0;for(unsigned i=1;i<n-5;i++)ck^=g->nmea[i];
                int a=hex(g->nmea[n-4]),z=hex(g->nmea[n-3]);good=a>=0&&z>=0&&ck==(unsigned)(a*16+z);
            }
            if(good)r->nmea_good++;else{r->bad_checksum++;r->history|=GNSS_H_CHECKSUM;}
            g->nmea_used=0;
        }return;
    }
    if(g->phase==1){g->phase=b==0x62?2:b==0xb5?1:0;g->cka=g->ckb=0;return;}
    if(g->phase==7){g->checka=b;g->phase=8;return;}
    if(g->phase==8){
        if(g->checka==g->cka&&b==g->ckb)message(g,now);
        else{r->bad_checksum++;r->history|=GNSS_H_CHECKSUM;}
        reset(g);gnss_tick(g,now);return;
    }
    g->cka=(g->cka+b)&255;g->ckb=(g->ckb+g->cka)&255;
    switch(g->phase){
    case 2:g->kind=b;g->phase=3;break;
    case 3:g->id=b;g->phase=4;break;
    case 4:g->length=b;g->phase=5;break;
    case 5:g->length|=(unsigned)b<<8;g->used=0;
        if(g->length>sizeof(g->payload)){reset(g);r->bad_length++;r->history|=GNSS_H_LENGTH;}
        else g->phase=g->length?6:7;
        break;
    default:g->payload[g->used++]=b;if(g->used==g->length)g->phase=7;break;
    }
}
void gnss_poll_packet(uint8_t p[8],int version){
    p[0]=0xb5;p[1]=0x62;p[2]=version?10:1;p[3]=version?4:7;p[4]=p[5]=0;
    unsigned a=0,b=0;for(unsigned i=2;i<6;i++){a=(a+p[i])&255;b=(b+a)&255;}p[6]=a;p[7]=b;
}
