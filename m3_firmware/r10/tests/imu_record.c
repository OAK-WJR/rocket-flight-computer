/* Portable serialization fixture; never opens a target or simulates motion. */
#include "imu_frame.h"
#include "baro_frame.h"
#include "checks.h"
void r10_test_sensor_record(uint32_t frame[64], unsigned mode) {
    r10_imu d={0};
    const int16_t values[10]={-32768,32767,-1,0,1,-2,30000,-30000,12,-256};
    const uint8_t config[8]={6,6,0x44,0x0d,3,0x99,1,8};
    d.state=R10_IMU_READY;d.who=0x73;d.status_reg=0x0f;d.valid_mask=0x0f;
    d.has_sample=1;d.samples=7;d.last_good_ms=frame[5]-20u;d.endpoint_mask=3;
    d.nominal_bus_hz=1000000u;
    for(unsigned i=0;i<10;++i)d.raw[i]=values[i];
    for(unsigned i=0;i<8;++i)d.config[i]=config[i];
    if(mode==1){d.state=R10_IMU_STALE;d.error=d.last_error=R10_IMU_NO_DATA;d.valid_mask=0;}
    if(mode==2){d.state=R10_IMU_ERROR;d.error=d.last_error=R10_IMU_DATA_READ;
                d.valid_mask=0;d.bus_errors=1;d.bus_detail=0x03200000u;d.retry_count=2;}
    r10_pack_imu(frame,&d);
}
void r10_test_baro_record(uint32_t frame[128],unsigned mode) {
    r10_baro d={0};
    const uint16_t c[8]={0,40127,36924,23317,23282,33464,28312,0};
    for(unsigned i=0;i<8;++i)d.prom[i]=c[i];
    d.prom[7]=bench_prom_crc4(d.prom);
    for(unsigned i=0;i<8;++i)d.sample_prom[i]=d.prom[i];
    d.state=R10_BARO_WAIT_D1;d.valid_mask=3;d.has_sample=d.prom_valid=1;
    d.prom_mask=255;d.crc_calculated=d.crc_stored=(uint8_t)d.prom[7];
    d.samples=7;d.last_good_ms=frame[5]-20u;d.nominal_bus_hz=50000;
    d.acquisition_started_ms=frame[5]-5u;d.sample_started_ms=frame[5]-45u;
    d.sample_d1=d.d1=9085466;d.sample_d2=d.d2=8569150;
    d.sample_d1_ms=d.d1_ms=frame[5]-35u;d.sample_d2_ms=d.d2_ms=frame[5]-20u;
    d.pressure_pa=100009;d.temp_centic=2007;
    if(mode) {
        d.state=R10_BARO_ERROR;d.valid_mask=0;d.error=d.last_error=R10_BARO_READ_D2;
        d.bus_errors=1;d.bus_detail=0x80040010u;d.d1+=123;
    }
    if(mode==2) {
        d.error=d.last_error=R10_BARO_PROM_CRC;d.prom[2]^=1;d.prom_valid=0;
        d.crc_calculated=bench_prom_crc4(d.prom);
    }
    r10_pack_baro(frame,&d);
}
