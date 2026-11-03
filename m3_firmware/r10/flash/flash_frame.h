#ifndef R10_FLASH_FRAME_H
#define R10_FLASH_FRAME_H
#include "qspi_port.h"
/* Logical84-word record spans98..127 and193..246 of the ABI5 mailbox.
 * Existing sensor and voltage fields and the1020-byte CRC offset stay fixed. */
enum {R10_FLASH_RECORD_WORDS=84};
void r10_pack_flash(uint32_t frame[256],const r10_flash_ro *,const r10_qspi_port *);
#endif
