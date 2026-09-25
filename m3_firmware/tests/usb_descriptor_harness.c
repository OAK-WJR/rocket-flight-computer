/* The real pinned TinyUSB descriptor macros/types are used by this executable. */
#include <assert.h>
#include <stdio.h>
#include "../src/usb_descriptors.c"
uint8_t usb_test_uid[12]={0,1,2,3,4,5,6,7,8,9,10,11};
int main(void){
 const tusb_desc_device_t *d=(const tusb_desc_device_t *)tud_descriptor_device_cb();
 assert(sizeof(*d)==18&&d->bLength==18&&d->bcdUSB==0x200&&d->idVendor==0xcafe&&d->idProduct==0x4001);
 assert(d->bMaxPacketSize0==64&&d->bNumConfigurations==1);
 const uint8_t *p=tud_descriptor_configuration_cb(0);
 unsigned length=p[2]|(unsigned)p[3]<<8,offset=0,interfaces=0,endpoints=0,mask=0;
 assert(length==TUD_CONFIG_DESC_LEN+TUD_CDC_DESC_LEN&&p[4]==2&&p[7]==0x80&&p[8]==250);
 while(offset<length){
  unsigned n=p[offset];assert(n>=2&&offset+n<=length);
  if(p[offset+1]==TUSB_DESC_INTERFACE)interfaces++;
  if(p[offset+1]==TUSB_DESC_ENDPOINT){
   unsigned ep=p[offset+2],size=p[offset+4]|(unsigned)p[offset+5]<<8;endpoints++;
   if(ep==0x81){assert(size==8&&p[offset+3]==3);mask|=1;}
   else if(ep==0x02){assert(size==64&&p[offset+3]==2);mask|=2;}
   else {assert(ep==0x82&&size==64&&p[offset+3]==2);mask|=4;}
  }
  offset+=n;
 }
 assert(interfaces==2&&endpoints==3&&mask==7&&!tud_descriptor_configuration_cb(1));
 const uint16_t *s=tud_descriptor_string_cb(3,0x409);assert((s[0]&255)==50);
 const char *serial="000102030405060708090A0B";
 for(unsigned i=0;i<24;i++)assert(s[1+i]==(unsigned char)serial[i]);
 assert(!tud_descriptor_string_cb(255,0));puts("Real USB descriptor binary walk: PASS");return 0;
}
