#ifndef M3_STORAGE_H
#define M3_STORAGE_H
#include <stddef.h>
#include <stdint.h>

#define STORE_BYTES 0x1000000U
#define STORE_SECTOR 4096U
#define STORE_PAGE 256U
#define STORE_SECTORS (STORE_BYTES/STORE_SECTOR)
#ifdef M3_GNSS
#define STORE_PAYLOAD 1024U
#define STORE_RECORD_KIND 3U
#define STORE_RECORD_PAGES 5U
#define STORE_RECORD_SLOTS 3U
#else
#define STORE_PAYLOAD 512U
#define STORE_RECORD_KIND 2U
#define STORE_RECORD_PAGES 3U
#define STORE_RECORD_SLOTS 5U
#endif
#define STORE_CHUNK 220U
#define STORE_MAGIC 0x474c334dU /* M3LG, little endian */
enum { STORE_OK, STORE_CLOCK, STORE_IO, STORE_ID, STORE_SFDP, STORE_BUSY,
       STORE_PROTECTED, STORE_QE, STORE_BOUNDS, STORE_NOT_BLANK, STORE_WEL,
       STORE_TIMEOUT, STORE_VERIFY, STORE_FULL, STORE_READ_ONLY, STORE_FORMAT };
enum { STORE_INSPECT, STORE_RECORD };
enum { STORE_NOT_STARTED, STORE_SCANNING, STORE_READY, STORE_STOPPED };

/* Exactly words 128..155 of protocol v5. No pointers/padding on the wire. */
typedef struct {
    uint32_t mode,status,error,history,io_error,bus_hz,jedec,registers;
    uint32_t uid[2],scanned_sectors,used_sectors,valid_headers,invalid_pages;
    uint32_t next_sector,session,written,last_counter,dropped,error_address;
    uint32_t last_write_ms,mapped,quad_pages,blank_pages,slot,reserved[3];
} BenchStorage;
typedef struct {
    void *ctx;
    uint32_t (*ticks)(void *);
    void (*delay)(void *,uint32_t);
    int (*initialize)(void *,uint32_t *hz,uint32_t *detail);
    /* address=-1 omits address; dummy=0..31 clocks; quad applies only to data.
     * tx/rx mutually exclusive. Reads are synchronous, all bounds checked below. */
    int (*command)(void *,uint8_t,int32_t,unsigned,int,const uint8_t *,uint8_t *,size_t,uint32_t *);
    int (*map_readonly)(void *,uint32_t *);
    void (*progress)(void *,const BenchStorage *);
} StorageIO;
typedef struct {
    StorageIO io;
    BenchStorage result;
    uint32_t initialized,sector_open;
    uint8_t identity[84]; /* board SHA32, build SHA32, MCU UID12, flash UID8 */
    uint8_t sector[STORE_SECTOR];
} Storage;

/* Never issues erase, reset, suspend/resume, status-write or unlock commands. */
void storage_begin(Storage *,const StorageIO *,unsigned mode,const uint8_t identity[76]);
int storage_read(Storage *,uint32_t,uint8_t *,size_t);
int storage_program_page(Storage *,uint32_t,const uint8_t page[STORE_PAGE]);
void storage_append(Storage *,const uint8_t payload[STORE_PAYLOAD],uint32_t counter);
void storage_page(uint8_t *,unsigned type,uint32_t address,uint32_t session,
                  uint32_t counter,unsigned chunk,const uint8_t *,unsigned length);
int storage_page_valid(const uint8_t *,uint32_t address);
void bench_storage_begin(unsigned mode,const uint8_t identity[76],BenchStorage *);
void bench_storage_append(const uint8_t *,uint32_t,BenchStorage *);
void bench_storage_progress(const BenchStorage *);
#endif
