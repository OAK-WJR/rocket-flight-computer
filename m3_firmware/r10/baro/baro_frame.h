#ifndef R10_BARO_FRAME_H
#define R10_BARO_FRAME_H
#include "baro_core.h"
/* Caller supplies the 128-word v3 record. */
void r10_pack_baro(uint32_t *,const r10_baro *);
#endif
