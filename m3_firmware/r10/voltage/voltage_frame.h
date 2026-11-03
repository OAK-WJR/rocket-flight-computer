#ifndef R10_VOLTAGE_FRAME_H
#define R10_VOLTAGE_FRAME_H
#include "adc_port.h"
/* ABI4: caller owns a zeroed256-word frame and its CRC. */
void r10_pack_voltage(uint32_t frame[256],const r10_voltage *,const r10_adc_port *);
#endif
