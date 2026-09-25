#ifndef M3_GNSS_H
#define M3_GNSS_H
#include <stdint.h>
#include <stddef.h>

enum { GNSS_OFF, GNSS_LISTENING, GNSS_NO_DATA, GNSS_UNKNOWN_ID,
       GNSS_NO_FIX, GNSS_FIX, GNSS_STALE, GNSS_HAL_ERROR };
enum { GNSS_E_NONE, GNSS_E_CLOCK, GNSS_E_INIT };
enum { GNSS_H_UART=1U<<3, GNSS_H_OVERFLOW=1U<<4, GNSS_H_CHECKSUM=1U<<5,
       GNSS_H_LENGTH=1U<<6, GNSS_H_TIMEOUT=1U<<7, GNSS_H_ID=1U<<8,
       GNSS_H_EPOCH=1U<<9, GNSS_H_TX=1U<<10 };
enum { GNSS_VER=1, GNSS_ID_OK=2, GNSS_PVT=4, GNSS_POSITION=8,
       GNSS_UTC=16, GNSS_FRESH=32 };
/* Wire words184..254. Exact PVT92 plus MON-VER fixed40 and the exact30-byte
 * PROTVER/MOD extension fields selected from the packet. Not a full MON-VER
 * transcript. version_len records the original payload length. */
typedef struct {
    uint32_t state,error,history,flags,kernel_hz,brr,uart_errors,rx_bytes;
    uint32_t dropped,ubx_good,nmea_good,bad_checksum,bad_length,timeouts;
    uint32_t last_byte_ms,mon_ms,pvt_ms,epoch_ms,tx_count,tx_errors;
    uint32_t pvt_count,version_len,max_gap_ms;
    uint8_t pvt[92],version[100];
} BenchGNSS;
typedef struct {
    BenchGNSS result;
    uint32_t started,now,last_epoch,have_epoch,epoch_current;
    unsigned phase,used,length,kind,id,cka,ckb,checka;
    unsigned nmea_used;
    uint8_t payload[512],nmea[128];
} GNSS;
void gnss_init(GNSS *,uint32_t);
void gnss_feed(GNSS *,uint8_t,uint32_t);
void gnss_tick(GNSS *,uint32_t);
void gnss_loss(GNSS *,uint32_t,uint32_t);
void gnss_poll_packet(uint8_t out[8],int version);
void bench_gnss_initialize(void);
void bench_gnss_task(void);
void bench_gnss_status(BenchGNSS *);
#endif
