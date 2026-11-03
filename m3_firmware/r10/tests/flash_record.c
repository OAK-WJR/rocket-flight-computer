/* Actual core + native-port model + serializer, never linked in a target image. */
#define main r10_qspi_model_test_main
#include "../flash/test_qspi.c"
#undef main
#include "../flash/flash_frame.h"
void r10_test_flash_record(uint32_t out[256],unsigned scenario) {
    model m;r10_qspi_port p;r10_flash_ro f;uint32_t now=100;
    setup(&m,&p);memset(&f,0,sizeof(f));
    if (scenario==0) {r10_pack_flash(out,&f,&p);return;}
    if (scenario==2) m.stuck_busy=1;
    if (scenario==10) *at(&m,Q_ID)=0x20080450u;
    r10_flash_ro_io io={&p,r10_qspi_initialize,r10_qspi_start,r10_qspi_poll,r10_qspi_cancel};
    r10_flash_ro_begin(&f,&io,now);
    for (unsigned i=0;i<500 && f.state!=FRO_WAIT && f.state!=FRO_RETRY && f.state!=FRO_STOPPED;++i) {
        if (f.state==FRO_READING) {
            if (scenario==6 && f.command==0) m.fifo[0]=1;
            if (scenario==7 && f.command==1) m.fifo[0]=0;
            if (scenario==8 && f.command==5) m.fifo[0]=0xee;
            if (scenario==9 && f.command==6) m.fifo[0]=0xee;
        }
        r10_flash_ro_poll(&f,now++);
    }
    if (scenario>=3 && scenario<=5) {
        assert(f.state==FRO_WAIT);m.after_dr_error=1;
        if (scenario==5) m.reset_ignored=1;
        now=f.last_good_ms+1000;
        r10_flash_ro_poll(&f,now++);
        for (unsigned i=0;i<500 && f.state!=FRO_RETRY && f.state!=FRO_STOPPED;++i)
            r10_flash_ro_poll(&f,now++);
        if (scenario==4) {
            assert(f.state==FRO_RETRY);m.after_dr_error=0;now=f.stage_at+1000;
            for (unsigned i=0;i<500 && f.state!=FRO_WAIT;++i) r10_flash_ro_poll(&f,now++);
        }
    }
    r10_pack_flash(out,&f,&p);
}
