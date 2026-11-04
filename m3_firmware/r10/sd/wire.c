#include "wire.h"
#include <string.h>

static int error(r10_sd_wire *w,unsigned code,uint32_t detail) {
    w->error=code;w->detail=detail;w->state=SDW_FAILED;return SDQ_IO_ERROR;
}
static uint32_t sum(uint32_t a,unsigned n) {return a>UINT32_MAX-n?UINT32_MAX:a+n;}
static void trace(uint8_t *p,uint32_t *count,const uint8_t *v,unsigned n) {
    for (unsigned i=0;i<n && *count<SDW_TRACE;++i)p[(*count)++]=v[i];
}
static int exchange(r10_sd_wire *w,const uint8_t *tx,uint8_t *rx,unsigned n) {
    unsigned accepted=0,received=0;uint32_t detail=0;
    int rc=w->bus.transfer(w->bus.context,tx,rx,n,&accepted,&received,&detail);
    ++w->exchanges;
    if (accepted>n || received>accepted) return error(w,SDW_COUNT,detail);
    trace(w->tx_prefix,&w->trace_accepted,tx,accepted);
    trace(w->rx_prefix,&w->trace_received,rx,received);
    w->accepted_total=sum(w->accepted_total,accepted);w->received_total=sum(w->received_total,received);
    if (rc!=SDQ_IO_OK) return error(w,SDW_TRANSFER,detail);
    if (accepted!=n || received!=n) return error(w,SDW_COUNT,detail);
    return SDQ_IO_OK;
}
static int select_card(r10_sd_wire *w,unsigned asserted) {
    uint32_t detail=0;
    if (w->bus.select(w->bus.context,asserted,&detail)!=SDQ_IO_OK)
        return error(w,SDW_SELECT,detail);
    w->selected=asserted;return SDQ_IO_OK;
}
static int finish(r10_sd_wire *w) {
    /* A command, response and register packet are one continuous-CS session.
     * Only here deselect, then clock one idle byte (bench policy). */
    if (select_card(w,0)!=SDQ_IO_OK)return SDQ_IO_ERROR;
    uint8_t tx=0xff,rx=0;
    if (exchange(w,&tx,&rx,1)!=SDQ_IO_OK)return SDQ_IO_ERROR;
    w->state=SDW_DONE;return SDQ_IO_OK;
}
static int initialize(void *context,uint32_t now,uint32_t *hz,uint32_t *clocks,uint32_t *detail) {
    r10_sd_wire *w=context;(void)now;
    if (w->state!=SDW_OFF) {*detail=SDW_STATE;return error(w,SDW_STATE,0);}
    int rc=w->bus.initialize(w->bus.context,hz,clocks,detail);
    if (rc==SDQ_IO_BUSY)return rc;
    if (rc!=SDQ_IO_OK)return error(w,SDW_TRANSFER,*detail);
    w->initialized=1;w->state=SDW_IDLE;return SDQ_IO_OK;
}
static int start_impl(r10_sd_wire *w,unsigned request) {
    if (!w->initialized || (w->state!=SDW_IDLE && w->state!=SDW_DONE))
        return error(w,SDW_STATE,0);
    w->request=request;w->error=w->detail=0;
    w->prefix_count=w->token_count=w->result_count=w->result_delivered=0;
    w->accepted_total=w->received_total=w->exchanges=0;
    w->trace_accepted=w->trace_received=0;
    memset(w->result,0,sizeof(w->result));memset(w->tx_prefix,0,sizeof(w->tx_prefix));
    memset(w->rx_prefix,0,sizeof(w->rx_prefix));
    if (request==SDQ_PROBE_REQUEST) {
        uint8_t tx[8],rx[8]={0};memset(tx,0xff,sizeof(tx));
        if (select_card(w,0)!=SDQ_IO_OK)return SDQ_IO_ERROR;
        if (exchange(w,tx,rx,8)!=SDQ_IO_OK)return SDQ_IO_ERROR;
        memcpy(w->result,rx,8);w->result_count=8;w->state=SDW_DONE;return SDQ_IO_OK;
    }
    uint8_t frame[6],rx[6]={0};
    if (r10_sd_metadata_frame(request,frame)!=SDM_OK)return error(w,SDW_ARGUMENT,request);
    if (select_card(w,1)!=SDQ_IO_OK)return SDQ_IO_ERROR;
    if (exchange(w,frame,rx,6)!=SDQ_IO_OK)return SDQ_IO_ERROR;
    w->state=SDW_R1;return SDQ_IO_OK;
}
static int start(void *context,unsigned request,uint32_t *detail) {
    r10_sd_wire *w=context;int rc=start_impl(w,request);
    *detail=(w->error<<24)|(w->detail&0xffffffu);return rc;
}
static int receive(r10_sd_wire *w,uint8_t value) {
    if (w->state==SDW_R1) {
        ++w->prefix_count;
        if (value==0xffu) {
            if (w->prefix_count>=SDW_R1_BYTES)return error(w,SDW_R1_TIMEOUT,0);
            return SDQ_IO_BUSY;
        }
        if (value&0x80u)return error(w,SDW_R1_PREFIX,value);
        w->result[w->result_count++]=value;
        if ((w->request==SDM_CMD8 || w->request==SDM_CMD58) && value<=1u)w->state=SDW_SUFFIX;
        else if ((w->request==SDM_CMD9 || w->request==SDM_CMD10) && !value)w->state=SDW_TOKEN;
        else return finish(w);
    } else if (w->state==SDW_SUFFIX) {
        w->result[w->result_count++]=value;
        if (w->result_count==5u)return finish(w);
    } else if (w->state==SDW_TOKEN) {
        ++w->token_count;
        if (value==0xffu) {
            if (w->token_count>=SDW_TOKEN_BYTES)return error(w,SDW_TOKEN_TIMEOUT,0);
            return SDQ_IO_BUSY;
        }
        w->result[w->result_count++]=value;
        if (value!=0xfeu)return error(w,SDW_BAD_TOKEN,value);
        w->state=SDW_REGISTER;
    } else if (w->state==SDW_REGISTER) {
        w->result[w->result_count++]=value;
        if (w->result_count==20u)return finish(w);
    } else return error(w,SDW_STATE,w->state);
    return SDQ_IO_BUSY;
}
static int poll(void *context,uint8_t *data,unsigned capacity,unsigned *count,uint32_t *detail) {
    r10_sd_wire *w=context;*count=0;*detail=0;
    if (!data || !capacity || capacity>20u)return error(w,SDW_ARGUMENT,capacity);
    unsigned budget=SDW_POLL_BYTES;
    while (budget-- && w->state!=SDW_DONE && w->state!=SDW_FAILED) {
        if (w->state<SDW_R1 || w->state>SDW_REGISTER) {error(w,SDW_STATE,w->state);break;}
        if (w->result_count-w->result_delivered>=capacity)break;
        uint8_t tx=0xff,rx=0;
        if (exchange(w,&tx,&rx,1)!=SDQ_IO_OK)break;
        (void)receive(w,rx);
    }
    if (w->result_count>20u || w->result_delivered>w->result_count)
        return error(w,SDW_COUNT,w->result_count);
    unsigned n=w->result_count-w->result_delivered;
    if (n>capacity)n=capacity;
    memcpy(data,w->result+w->result_delivered,n);w->result_delivered+=n;*count=n;
    *detail=(w->error<<24)|(w->detail&0xffffffu);
    if (w->state==SDW_FAILED)return SDQ_IO_ERROR;
    return w->state==SDW_DONE && w->result_delivered==w->result_count?SDQ_IO_OK:SDQ_IO_BUSY;
}
static int cancel(void *context,uint32_t *detail) {
    r10_sd_wire *w=context;*detail=0;
    /* release() owns finite native cleanup. Success invalidates this adapter:
     * a caller cannot silently restart a once-initialized card. */
    int rc=w->bus.release(w->bus.context,detail);
    w->initialized=0;
    if (rc!=SDQ_IO_OK) {w->cleanup_error=SDW_RELEASE;w->cleanup_detail=*detail;}
    if (w->state!=SDW_FAILED)w->state=SDW_OFF;
    if (rc==SDQ_IO_OK)w->selected=0;
    return rc==SDQ_IO_OK?SDQ_IO_OK:SDQ_IO_ERROR;
}
int r10_sd_wire_attach(r10_sd_wire *w,const r10_sd_bus *bus,r10_sd_query_io *io) {
    if (!w || !io)return SDQ_IO_ERROR;
    memset(w,0,sizeof(*w));memset(io,0,sizeof(*io));
    if (!bus || !bus->initialize || !bus->select || !bus->transfer || !bus->release)return SDQ_IO_ERROR;
    w->bus=*bus;io->context=w;io->initialize=initialize;io->start=start;io->poll=poll;io->cancel=cancel;
    return SDQ_IO_OK;
}
