/* Append-only diagnostic journal. W25Q128JV Rev M, sections 7.1,8.2.9,8.2.13.
 * Legacy records use three pages/512 bytes; GNSS uses five pages/1024 bytes.
 * Never erase
 * data, reuse a sector after reboot, wrap page programming, or hide a failure.
 * CRC is accidental-corruption detection, not authentication or atomicity.
 */
#include "storage.h"
#include "checks.h"
#include <string.h>
_Static_assert(sizeof(BenchStorage)==28*4,"Storage wire layout");
static void put(uint8_t *p,uint32_t v) { for (unsigned i=0;i<4;i++) p[i]=(uint8_t)(v>>(8*i)); }
static uint32_t get(const uint8_t *p) { return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static int blank(const uint8_t *p,size_t n) { for(size_t i=0;i<n;i++) if(p[i]!=255) return 0; return 1; }
static int fail(Storage *s,unsigned e,uint32_t address) {
    s->result.error=e; s->result.history|=1U<<e;
    s->result.error_address=address; s->result.status=STORE_STOPPED; return 0;
}
static int cmd(Storage *s,uint8_t op,int32_t a,unsigned dummy,int quad,
               const uint8_t *tx,uint8_t *rx,size_t n) {
    uint32_t detail=0;
    if(s->io.command(s->io.ctx,op,a,dummy,quad,tx,rx,n,&detail)) {
        s->result.io_error=detail; return fail(s,STORE_IO,a<0?0xffffffffU:(uint32_t)a);
    }
    return 1;
}
static int statuses(Storage *s) {
    uint8_t r[3];
    if(!cmd(s,5,-1,0,0,0,r,1)||!cmd(s,0x35,-1,0,0,0,r+1,1)||!cmd(s,0x15,-1,0,0,0,r+2,1)) return 0;
    s->result.registers=(uint32_t)r[0]|(uint32_t)r[1]<<8|(uint32_t)r[2]<<16;
    return 1;
}
static int writable(Storage *s) {
    if(s->result.mode!=STORE_RECORD||!s->initialized||s->result.mapped) return fail(s,STORE_READ_ONLY,0xffffffffU);
    if(s->result.error) return 0;
    if(!statuses(s)) return 0;
    uint32_t r=s->result.registers;
    if(r&0x8003U) return fail(s,STORE_BUSY,0xffffffffU); /* SUS or BUSY/WEL on entry */
    if(r&(0x1cU|0x4000U|0x40000U)) return fail(s,STORE_PROTECTED,0xffffffffU); /* BP/CMP/WPS */
    if(!(r&0x200U)) return fail(s,STORE_QE,0xffffffffU);
    return 1;
}
int storage_read(Storage *s,uint32_t a,uint8_t *p,size_t n) {
    if(!p||!n||n>STORE_SECTOR||a>STORE_BYTES||n>STORE_BYTES-a||s->result.mapped)
        return fail(s,STORE_BOUNDS,a);
    return cmd(s,3,(int32_t)a,0,0,0,p,n);
}
int storage_program_page(Storage *s,uint32_t a,const uint8_t page[STORE_PAGE]) {
    uint8_t readback[STORE_PAGE];
    if(!page||a%STORE_PAGE||a>STORE_BYTES-STORE_PAGE) return fail(s,STORE_BOUNDS,a);
    if(!writable(s)||!storage_read(s,a,readback,sizeof(readback))) return 0;
    if(!blank(readback,sizeof(readback))) return fail(s,STORE_NOT_BLANK,a);
    if(!cmd(s,6,-1,0,0,0,0,0)||!statuses(s)) return 0;
    if((s->result.registers&3U)!=2U) return fail(s,STORE_WEL,a);
    if(!cmd(s,2,(int32_t)a,0,0,page,0,STORE_PAGE)) return 0;
    uint32_t start=s->io.ticks(s->io.ctx); unsigned polls;
    for(polls=0;polls<12;polls++) {
        uint8_t r=0;
        if(!cmd(s,5,-1,0,0,0,&r,1)) return 0;
        if(!(r&1)) break;
        if((uint32_t)(s->io.ticks(s->io.ctx)-start)>=10U) break;
        s->io.delay(s->io.ctx,1);
    }
    if(!statuses(s)) return 0;
    if(s->result.registers&0x8001U) return fail(s,STORE_TIMEOUT,a);
    if(s->result.registers&2U) return fail(s,STORE_WEL,a);
    if(!storage_read(s,a,readback,sizeof(readback))) return 0;
    if(memcmp(page,readback,sizeof(readback))) return fail(s,STORE_VERIFY,a);
    if(!cmd(s,0x6b,(int32_t)a,8,1,0,readback,sizeof(readback))) return 0;
    if(memcmp(page,readback,sizeof(readback))) return fail(s,STORE_VERIFY,a);
    s->result.quad_pages++;
    s->result.last_write_ms=s->io.ticks(s->io.ctx);
    return 1;
}
void storage_page(uint8_t *p,unsigned type,uint32_t address,uint32_t session,
                  uint32_t counter,unsigned chunk,const uint8_t *payload,unsigned n) {
    memset(p,255,STORE_PAGE);
    if(n>STORE_CHUNK||(!payload&&n)) return;
    put(p,STORE_MAGIC);put(p+4,1);put(p+8,type);put(p+12,address);
    put(p+16,session);put(p+20,counter);put(p+24,chunk);put(p+28,n);
    if(n)memcpy(p+32,payload,n);
    put(p+252,bench_crc32(p,252));
}
int storage_page_valid(const uint8_t *p,uint32_t address) {
    if(get(p)!=STORE_MAGIC||get(p+4)!=1||get(p+12)!=address||get(p+28)>STORE_CHUNK||
       get(p+252)!=bench_crc32(p,252))return 0;
    unsigned type=get(p+8),chunk=get(p+24),n=get(p+28);
    if(get(p+16)>=STORE_SECTORS||get(p+16)>address/STORE_SECTOR)return 0;
    if(type==1) { if(address%STORE_SECTOR||chunk||n!=84||get(p+20)) return 0; }
    else if(type==2||type==3) {
        unsigned slot=address%STORE_SECTOR/STORE_PAGE;
        unsigned pages=type==2?3U:5U,last=type==2?72U:144U;
        if(!slot||chunk!=(slot-1)%pages||n!=(chunk==pages-1?last:STORE_CHUNK)||!get(p+20))return 0;
    } else return 0;
    return blank(p+32+n,STORE_CHUNK-n);
}
void storage_begin(Storage *s,const StorageIO *io,unsigned mode,const uint8_t identity[76]) {
    memset(s,0,sizeof(*s));s->io=*io;s->result.mode=mode;
    s->result.status=STORE_SCANNING;s->result.error_address=0xffffffffU;
    if(mode>STORE_RECORD) { fail(s,STORE_FORMAT,0xffffffffU);return; }
    memcpy(s->identity,identity,76);
    uint32_t detail=0;
    int e=io->initialize(io->ctx,&s->result.bus_hz,&detail);
    if(e) {s->result.io_error=detail;fail(s,STORE_CLOCK,0xffffffffU);return;}
    io->delay(io->ctx,6); /* startup already waited100ms; tPUW >=5ms independent guard */
    if(!statuses(s))return;
    if(s->result.registers&0x8001U){fail(s,STORE_BUSY,0xffffffffU);return;}
    uint8_t id[8];
    if(!cmd(s,0x9f,-1,0,0,0,id,3))return;
    s->result.jedec=(uint32_t)id[0]<<16|(uint32_t)id[1]<<8|id[2];
    if(s->result.jedec!=0xef4018U){fail(s,STORE_ID,0xffffffffU);return;}
    if(!cmd(s,0x5a,0,8,0,0,id,8))return;
    if(memcmp(id,"SFDP",4)){fail(s,STORE_SFDP,0xffffffffU);return;}
    /* QSPI dummy field is max31: use a four-byte zero alternate-byte phase for4Bh. */
    if(!cmd(s,0x4b,-1,0,0,0,id,8))return;
    memcpy(s->identity+76,id,8);s->result.uid[0]=get(id);s->result.uid[1]=get(id+4);
    s->initialized=1;
    if(mode==STORE_RECORD&&!writable(s))return;
    for(uint32_t sector=0;sector<STORE_SECTORS;sector++) {
        uint32_t a=sector*STORE_SECTOR;
        if(!storage_read(s,a,s->sector,STORE_SECTOR))return;
        if(!blank(s->sector,STORE_SECTOR))s->result.used_sectors=sector+1;
        for(unsigned page=0;page<16;page++) {
            const uint8_t *p=s->sector+page*STORE_PAGE;
            if(blank(p,STORE_PAGE))s->result.blank_pages++;
            else if(!storage_page_valid(p,a+page*STORE_PAGE))s->result.invalid_pages++;
            else if(page==0)s->result.valid_headers++;
        }
        s->result.scanned_sectors=sector+1;
        if(io->progress&&sector%32==0)io->progress(io->ctx,&s->result);
    }
    s->result.next_sector=s->result.used_sectors;s->result.session=s->result.next_sector;
    if(mode==STORE_INSPECT) {
        if(io->map_readonly(io->ctx,&detail)){s->result.io_error=detail;fail(s,STORE_IO,0xffffffffU);return;}
        s->result.mapped=1;
    } else if(s->result.next_sector==STORE_SECTORS){fail(s,STORE_FULL,STORE_BYTES);return;}
    s->result.status=STORE_READY;
}
void storage_append(Storage *s,const uint8_t payload[STORE_PAYLOAD],uint32_t counter) {
    if(s->result.mode!=STORE_RECORD)return;
    if(s->result.status!=STORE_READY){s->result.dropped++;return;}
    if(!counter||counter<=s->result.last_counter){fail(s,STORE_FORMAT,0xffffffffU);s->result.dropped++;return;}
    if(!s->sector_open) {
        if(s->result.next_sector>=STORE_SECTORS){fail(s,STORE_FULL,STORE_BYTES);s->result.dropped++;return;}
        uint32_t a=s->result.next_sector*STORE_SECTOR;
        if(!storage_read(s,a,s->sector,STORE_SECTOR))goto dropped;
        if(!blank(s->sector,STORE_SECTOR)){fail(s,STORE_NOT_BLANK,a);goto dropped;}
        storage_page(s->sector,1,a,s->result.session,0,0,s->identity,84);
        if(!storage_program_page(s,a,s->sector))goto dropped;
        s->sector_open=1;s->result.slot=0;
    }
    for(unsigned i=0;i<STORE_RECORD_PAGES;i++) {
        uint32_t a=s->result.next_sector*STORE_SECTOR+(1+STORE_RECORD_PAGES*s->result.slot+i)*STORE_PAGE;
        unsigned n=i==STORE_RECORD_PAGES-1?STORE_PAYLOAD-i*STORE_CHUNK:STORE_CHUNK;
        storage_page(s->sector,STORE_RECORD_KIND,a,s->result.session,counter,i,payload+i*STORE_CHUNK,n);
        if(!storage_program_page(s,a,s->sector))goto dropped;
    }
    s->result.written++;s->result.last_counter=counter;
    if(++s->result.slot==STORE_RECORD_SLOTS){s->result.next_sector++;s->sector_open=0;s->result.slot=0;}
    return;
dropped:s->result.dropped++;
}
