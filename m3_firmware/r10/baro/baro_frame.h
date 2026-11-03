#ifndef R10_BARO_FRAME_H
#define R10_BARO_FRAME_H
#include "baro_core.h"
/* Fields64..97 are shared by the ABI3 and ABI4 records. */
void r10_pack_baro(uint32_t *,const r10_baro *);
#endif
