#ifdef M3_USB
#include "tusb.h"
#include "stm32h7xx_hal.h"
/* TinyUSB example VID/PID, development only. Not an allocated production ID.
 * A host additionally checks exact PCB/build hashes and MCU UID after opening.
 */
static const tusb_desc_device_t device={
    .bLength=sizeof(tusb_desc_device_t),.bDescriptorType=TUSB_DESC_DEVICE,.bcdUSB=0x0200,
    .bDeviceClass=TUSB_CLASS_MISC,.bDeviceSubClass=MISC_SUBCLASS_COMMON,.bDeviceProtocol=MISC_PROTOCOL_IAD,
    .bMaxPacketSize0=64,.idVendor=0xcafe,.idProduct=0x4001,.bcdDevice=0x0006,
    .iManufacturer=1,.iProduct=2,.iSerialNumber=3,.bNumConfigurations=1
};
/* Request up to500mA only after configuration; pre-enumeration and suspend
 * current of the actual board remain unqualified. No remote wakeup. */
static const uint8_t config[]={
    TUD_CONFIG_DESCRIPTOR(1,2,0,TUD_CONFIG_DESC_LEN+TUD_CDC_DESC_LEN,0,500),
    TUD_CDC_DESCRIPTOR(0,4,0x81,8,0x02,0x82,64)
};
const uint8_t *tud_descriptor_device_cb(void){return (const uint8_t *)&device;}
const uint8_t *tud_descriptor_configuration_cb(uint8_t index){return index==0?config:NULL;}
const uint16_t *tud_descriptor_string_cb(uint8_t index,uint16_t language){
    (void)language;static uint16_t out[40];unsigned n=0;
    const char *strings[]={"","M3 bench development","M3 USB diagnostics v0.6","","Read-only diagnostics"};
    if(index==0){out[1]=0x0409;n=1;}
    else if(index==3){
        const char hex[]="0123456789ABCDEF";const uint8_t *id=(const uint8_t *)UID_BASE;
        for(unsigned i=0;i<12;i++){out[++n]=hex[id[i]>>4];out[++n]=hex[id[i]&15];}
    }else if(index<sizeof(strings)/sizeof(strings[0])){
        const char *s=strings[index];while(*s && n<39)out[++n]=(uint8_t)*s++;
    }else return NULL;
    out[0]=(uint16_t)((TUSB_DESC_STRING<<8)|(2*n+2));return out;
}
#endif
