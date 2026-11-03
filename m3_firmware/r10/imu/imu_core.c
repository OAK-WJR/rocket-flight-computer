#include "imu_core.h"

static int32_t exchange(r10_imu *d, uint8_t reg, uint8_t *data, uint16_t count, int read) {
    uint8_t tx[33]={0}, rx[33]={0};
    if (d->bus_failed || count==0 || count>32 || reg>0x7f) return -1;
    tx[0]=read ? (uint8_t)(reg|0x80u) : reg;
    if (!read) for (unsigned i=0;i<count;++i)tx[i+1]=data[i];
    uint32_t detail=0;
    if (d->io.exchange(d->io.handle,tx,rx,(size_t)count+1u,&detail)!=0) {
        d->bus_errors++; d->bus_detail=detail; d->bus_failed=1;
        return -1;
    }
    if (read) for (unsigned i=0;i<count;++i)data[i]=rx[i+1];
    return 0;
}
static int32_t read_register(void *handle,uint8_t reg,uint8_t *data,uint16_t count) {
    return exchange(handle,reg,data,count,1);
}
static int32_t write_register(void *handle,uint8_t reg,const uint8_t *data,uint16_t count) {
    /* The vendor write interface is const; the common callback never modifies
     * this payload on the write path. */
    return exchange(handle,reg,(uint8_t *)data,count,0);
}
static void fail(r10_imu *d,uint32_t error,uint32_t now) {
    d->state=R10_IMU_ERROR; d->error=error; d->last_error=error; d->valid_mask=0; d->stage_at=now;
}
static void start_port(r10_imu *d,uint32_t now) {
    d->valid_mask=0; d->bus_failed=0; d->who=0; d->status_reg=0;
    d->nominal_bus_hz=0; d->error=R10_IMU_OK;
    uint32_t detail=0;
    if (!d->io.initialize || !d->io.exchange ||
        d->io.initialize(d->io.handle,&d->nominal_bus_hz,&detail)!=0 ||
        d->nominal_bus_hz!=1000000u) {
        d->bus_detail=detail;
        fail(d,R10_IMU_PORT,now);return;
    }
    d->state=R10_IMU_BOOT_WAIT;d->stage_at=now;
}
void r10_imu_begin(r10_imu *d,const r10_imu_io *io,uint32_t now) {
    for (size_t i=0;i<sizeof(*d);++i)((uint8_t *)d)[i]=0;
    if (io) d->io=*io;
    d->sensor=(stmdev_ctx_t){.write_reg=write_register,.read_reg=read_register,.handle=d};
    start_port(d,now);
}

/* Raw register values are retained; masks exclude unrelated/reserved bits.
 * 120 Hz low-g + gyro, 480 Hz high-g, +/-16g, +/-4000dps, +/-64g.
 * High-g FS=001 is shared with the reviewed LSM6DSV320X alternate; WHO_AM_I
 * alone cannot distinguish these two parts. Never use its incompatible FS=011. */
static const uint8_t config_regs[8]={0x10,0x11,0x12,0x15,0x17,0x4e,0x03,0x13};
static const uint8_t config_masks[8]={0x7f,0x7f,0xc5,0x07,0x03,0xff,0x1d,0x08};
static const uint8_t config_values[8]={0x06,0x06,0x44,0x05,0x03,0x99,0x01,0x08};

static int check_config(r10_imu *d) {
    for (unsigned i=0;i<8;++i) {
        if (ism6hg256x_read_reg(&d->sensor,config_regs[i],&d->config[i],1)!=0)return -1;
        if ((d->config[i]&config_masks[i])!=config_values[i])return 1;
    }
    return 0;
}
static int configure(r10_imu *d) {
    stmdev_ctx_t *s=&d->sensor;
    /* Every call is checked. The bus latch blocks any later transaction after
     * a failed exchange, even if a vendor helper performs multiple operations. */
    uint8_t interface=1; /* I2C/I3C off, SPI 4-wire, push-pull/active-high default */
    uint8_t ctrl4=0;
    if (ism6hg256x_write_reg(s,ISM6HG256X_IF_CFG,&interface,1)!=0 ||
        ism6hg256x_auto_increment_set(s,1)!=0 || ism6hg256x_block_data_update_set(s,1)!=0 ||
        ism6hg256x_read_reg(s,ISM6HG256X_CTRL4,&ctrl4,1)!=0)return -1;
    /* Mask DRDY until hardware filter settling; set before enabling any ODR. */
    ctrl4|=0x08u;
    if (ism6hg256x_write_reg(s,ISM6HG256X_CTRL4,&ctrl4,1)!=0 ||
        ism6hg256x_gy_full_scale_set(s,ISM6HG256X_4000dps)!=0 ||
        ism6hg256x_xl_full_scale_set(s,ISM6HG256X_16g)!=0 ||
        ism6hg256x_hg_xl_full_scale_set(s,ISM6HG256X_64g)!=0 ||
        ism6hg256x_xl_setup(s,ISM6HG256X_ODR_AT_120Hz,ISM6HG256X_XL_HIGH_PERFORMANCE_MD)!=0 ||
        ism6hg256x_gy_setup(s,ISM6HG256X_ODR_AT_120Hz,ISM6HG256X_GY_HIGH_PERFORMANCE_MD)!=0 ||
        ism6hg256x_hg_xl_data_rate_set(s,ISM6HG256X_HG_XL_ODR_AT_480Hz,1)!=0)return -1;
    return 0;
}
static int16_t signed_le(const uint8_t *p) {
    uint16_t bits=(uint16_t)p[0]|((uint16_t)p[1]<<8);
    /* Avoid implementation-defined out-of-range unsigned->signed conversion. */
    return bits<0x8000u ? (int16_t)bits : (int16_t)((int32_t)bits-65536);
}
void r10_imu_poll(r10_imu *d,uint32_t now) {
    if (d->state==R10_IMU_OFF)return;
    if (d->state==R10_IMU_ERROR) {
        if ((uint32_t)(now-d->stage_at)>=R10_IMU_RETRY_MS) {
            d->retry_count++;start_port(d,now);
        }
        return;
    }
    if (d->state==R10_IMU_BOOT_WAIT) {
        if ((uint32_t)(now-d->stage_at)<R10_IMU_BOOT_MS)return;
        if (ism6hg256x_device_id_get(&d->sensor,&d->who)!=0 || d->who!=ISM6HG256X_ID) {
            fail(d,R10_IMU_ID,now);return;
        }
        /* Same SW_POR command as ST's driver, but the 35 ms delay is a
         * nonblocking state rather than a delay callback or an infinite poll. */
        ism6hg256x_func_cfg_access_t reset={.sw_por=1};
        if (ism6hg256x_write_reg(&d->sensor,ISM6HG256X_FUNC_CFG_ACCESS,(uint8_t *)&reset,1)!=0) {
            fail(d,R10_IMU_RESET,now);return;
        }
        d->state=R10_IMU_RESET_WAIT;d->stage_at=now;return;
    }
    if (d->state==R10_IMU_RESET_WAIT) {
        if ((uint32_t)(now-d->stage_at)<R10_IMU_BOOT_MS)return;
        uint8_t reset=0;
        if (ism6hg256x_read_reg(&d->sensor,ISM6HG256X_FUNC_CFG_ACCESS,&reset,1)!=0 ||
            reset&4u || ism6hg256x_device_id_get(&d->sensor,&d->who)!=0 || d->who!=ISM6HG256X_ID) {
            fail(d,R10_IMU_RESET,now);return;
        }
        if (configure(d)!=0) {fail(d,R10_IMU_CONFIG_WRITE,now);return;}
        int rc=check_config(d);
        if (rc!=0) {fail(d,rc<0?R10_IMU_CONFIG_READ:R10_IMU_CONFIG_MISMATCH,now);return;}
        d->state=R10_IMU_WAIT_DATA;d->stage_at=now;return;
    }
    /* Additional software warm-up floor: 70 ms gyro startup + three samples
     * at 120 Hz is 95 ms (AN6353 Tables27/28). Hardware DRDY_MASK remains the
     * settling authority; 100 nominal host ms is not measured sensor timing. */
    if (d->state==R10_IMU_WAIT_DATA && (uint32_t)(now-d->stage_at)<R10_IMU_SETTLE_MS)return;
    int rc=check_config(d);
    if (rc!=0) {fail(d,rc<0?R10_IMU_CONFIG_READ:R10_IMU_CONFIG_MISMATCH,now);return;}
    if (ism6hg256x_read_reg(&d->sensor,ISM6HG256X_STATUS_REG,&d->status_reg,1)!=0) {
        fail(d,R10_IMU_STATUS_READ,now);return;
    }
    if ((d->status_reg&0x0bu)!=0x0bu) {
        uint32_t age=now-(d->has_sample?d->last_good_ms:d->stage_at);
        if (age>R10_IMU_FRESH_MS) {
            if (d->state==R10_IMU_STALE && (uint32_t)(now-d->stale_since)>=R10_IMU_RETRY_MS) {
                d->retry_count++;start_port(d,now);return;
            }
            if (d->state!=R10_IMU_STALE)d->stale_since=now;
            d->valid_mask=0;d->state=R10_IMU_STALE;d->error=R10_IMU_NO_DATA;d->last_error=R10_IMU_NO_DATA;
        }
        return;
    }
    uint8_t low[14]={0},high[6]={0};
    if (ism6hg256x_read_reg(&d->sensor,ISM6HG256X_OUT_TEMP_L,low,14)!=0 ||
        ism6hg256x_read_reg(&d->sensor,ISM6HG256X_UI_OUTX_L_A_OIS_HG,high,6)!=0) {
        fail(d,R10_IMU_DATA_READ,now);return;
    }
    /* Commit all channels only after both transfers succeed. BDU guarantees
     * each 16-bit pair, not common timing across axes or the two accelerometers. */
    for (unsigned i=0;i<6;++i)d->raw[i]=signed_le(low+2u+2u*i);
    for (unsigned i=0;i<3;++i)d->raw[6u+i]=signed_le(high+2u*i);
    d->raw[9]=signed_le(low);d->endpoint_mask=0;
    for (unsigned i=0;i<9;++i)
        if (d->raw[i]==INT16_MIN || d->raw[i]==INT16_MAX)d->endpoint_mask|=1u<<i;
    d->samples++;d->has_sample=1;d->last_good_ms=now;d->valid_mask=d->status_reg&0x0fu;
    d->state=R10_IMU_READY;d->error=R10_IMU_OK;
}
