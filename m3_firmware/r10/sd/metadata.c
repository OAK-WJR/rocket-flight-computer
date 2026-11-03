#include "metadata.h"
#include <string.h>

/* SDA v9.10 section4.5: MSB-first CRC7(x^7+x^3+1) and
 * CRC16(x^16+x^12+x^5+1), zero initial remainder, no final XOR. */
static uint8_t crc7(const uint8_t *p,unsigned n) {
    uint8_t crc=0;
    for (unsigned i=0;i<n;++i)
        for (unsigned bit=0;bit<8u;++bit) {
            unsigned feedback=((crc>>6)^((p[i]>>(7u-bit))&1u))&1u;
            crc=(uint8_t)((crc<<1)&0x7fu);
            if (feedback) crc^=9u;
        }
    return crc;
}
static uint16_t crc16(const uint8_t *p,unsigned n) {
    uint16_t crc=0;
    for (unsigned i=0;i<n;++i) {
        crc^=(uint16_t)((uint16_t)p[i]<<8);
        for (unsigned bit=0;bit<8u;++bit)
            crc=(uint16_t)((crc<<1)^((crc&0x8000u)?0x1021u:0u));
    }
    return crc;
}
static uint32_t be32(const uint8_t *p) {
    return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3];
}
unsigned r10_sd_metadata_frame(unsigned command,uint8_t out[6]) {
    static const uint8_t opcode[SDM_COMMANDS]={0,8,59,55,41,41,58,9,10};
    static const uint32_t argument[SDM_COMMANDS]={0,0x1aau,1,0,0,0x40000000u,0,0,0};
    if (!out) return SDM_ARGUMENT;
    memset(out,0,6u);
    if (command>=SDM_COMMANDS) return SDM_ARGUMENT;
    uint32_t arg=argument[command];
    out[0]=(uint8_t)(0x40u|opcode[command]);out[1]=(uint8_t)(arg>>24);
    out[2]=(uint8_t)(arg>>16);out[3]=(uint8_t)(arg>>8);out[4]=(uint8_t)arg;
    out[5]=(uint8_t)((crc7(out,5u)<<1)|1u);
    return SDM_OK;
}
static unsigned prefix(uint8_t *out,const uint8_t *p,unsigned n,unsigned size) {
    if (n>size || (!p && n)) return SDM_ARGUMENT;
    if (n) memcpy(out,p,n);
    return n==size?SDM_OK:SDM_SHORT;
}
static unsigned reg_packet(const uint8_t p[20]) {
    if (p[0]) return SDM_R1;
    if (p[1]!=0xfeu) return SDM_TOKEN;
    if (crc16(p+2,16u)!=((uint16_t)p[18]<<8|p[19])) return SDM_CRC16;
    if (!(p[17]&1u)) return SDM_END_BIT;
    if (crc7(p+2,15u)!=(p[17]>>1)) return SDM_CRC7;
    return SDM_OK;
}
static unsigned cid_fields(r10_sd_metadata *o) {
    const uint8_t *p=o->raw_cid+2;
    unsigned month=p[14]&15u,major=p[8]>>4,minor=p[8]&15u;
    if (!month || month>12u || major>9u || minor>9u) return SDM_CID_FIELDS;
    o->manufacturer_id=p[0];memcpy(o->oem,p+1,2u);memcpy(o->product,p+3,5u);
    o->revision_major=(uint8_t)major;o->revision_minor=(uint8_t)minor;
    o->serial=be32(p+9);o->year=(uint16_t)(2000u+((p[13]&15u)<<4)+(p[14]>>4));
    o->month=(uint8_t)month;return SDM_OK;
}
static unsigned csd_fields(r10_sd_metadata *o) {
    const uint8_t *p=o->raw_csd+2;
    unsigned structure=p[0]>>6,read_length=p[5]&15u;
    o->csd_structure=(uint8_t)structure;
    if (structure>1u) return SDM_UNSUPPORTED_CSD; /* SDUC has no SPI mode. */
    if ((!structure && (read_length<9u || read_length>11u)) ||
        (structure==1u && read_length!=9u)) return SDM_CSD_FIELDS;
    if (!o->errors[0] && o->block_addressed!=(structure==1u)) return SDM_ADDRESSING_MISMATCH;
    uint64_t capacity;
    if (structure==1u) {
        uint32_t size=((uint32_t)(p[7]&63u)<<16)|((uint32_t)p[8]<<8)|p[9];
        capacity=((uint64_t)size+1u)<<19;
    } else {
        unsigned size=((unsigned)(p[6]&3u)<<10)|((unsigned)p[7]<<2)|(p[8]>>6);
        unsigned multiplier=((unsigned)(p[9]&3u)<<1)|(p[10]>>7);
        capacity=((uint64_t)size+1u)<<(multiplier+2u+read_length);
        /* R10 supports the SDSC capacity class only through2GiB. A larger
         * reported v1 geometry is kept raw, not silently re-addressed. */
        if (capacity>0x80000000ull) return SDM_CSD_FIELDS;
    }
    o->reported_capacity_bytes=capacity;o->reported_sectors512=capacity>>9;
    return SDM_OK;
}
unsigned r10_sd_metadata_decode(const uint8_t *ocr,unsigned on,
                               const uint8_t *cid,unsigned cn,
                               const uint8_t *csd,unsigned sn,r10_sd_metadata *o) {
    if (!o) return SDM_ARGUMENT;
    memset(o,0,sizeof(*o));o->lengths[0]=on;o->lengths[1]=cn;o->lengths[2]=sn;
    o->errors[0]=prefix(o->raw_ocr,ocr,on,5u);
    o->errors[1]=prefix(o->raw_cid,cid,cn,20u);
    o->errors[2]=prefix(o->raw_csd,csd,sn,20u);
    if (!o->errors[0]) {
        o->ocr=be32(o->raw_ocr+1);o->block_addressed=(uint8_t)((o->ocr>>30)&1u);
        if (o->raw_ocr[0]) o->errors[0]=SDM_R1;
        else if (!(o->ocr&0x80000000u)) o->errors[0]=SDM_OCR_NOT_READY;
        else if (!(o->ocr&0x00300000u)) o->errors[0]=SDM_OCR_VOLTAGE;
    }
    if (!o->errors[1]) o->errors[1]=reg_packet(o->raw_cid);
    if (!o->errors[1]) o->errors[1]=cid_fields(o);
    if (!o->errors[2]) o->errors[2]=reg_packet(o->raw_csd);
    if (!o->errors[2]) o->errors[2]=csd_fields(o);
    for (unsigned i=0;i<3u;++i) if (o->errors[i]) return o->errors[i];
    o->metadata_valid=1u;return SDM_OK;
}
