#ifndef R10_SD_METADATA_H
#define R10_SD_METADATA_H
#include <stdint.h>

/* Metadata codec only: no GPIO, SPI access, card reset or media writes.
 * Input/output buffers must not overlap. A register packet is normalized as
 * R1,0xFE,16 register bytes,CRC16 high,CRC16 low; inter-token idle clocks are
 * retained by the eventual transport, not included in this 20-byte packet. */
enum r10_sd_error {
    SDM_OK=0, SDM_ARGUMENT, SDM_SHORT, SDM_R1, SDM_TOKEN, SDM_CRC16,
    SDM_END_BIT, SDM_CRC7, SDM_CID_FIELDS, SDM_OCR_NOT_READY,
    SDM_OCR_VOLTAGE, SDM_UNSUPPORTED_CSD, SDM_CSD_FIELDS,
    SDM_ADDRESSING_MISMATCH
};
enum r10_sd_meta_command {
    SDM_CMD0, SDM_CMD8, SDM_CRC_ON, SDM_CMD55, SDM_ACMD41_SDSC,
    SDM_ACMD41_HC, SDM_CMD58, SDM_CMD9, SDM_CMD10, SDM_COMMANDS
};
typedef struct {
    uint64_t reported_capacity_bytes, reported_sectors512;
    uint32_t errors[3], lengths[3], ocr, serial;
    uint16_t year;
    uint8_t month, manufacturer_id, revision_major, revision_minor;
    uint8_t csd_structure, block_addressed, metadata_valid;
    uint8_t oem[2], product[5]; /* Untrusted bytes, not terminal-safe strings. */
    uint8_t raw_ocr[5], raw_cid[20], raw_csd[20];
} r10_sd_metadata;

/* Emits only one fixed metadata/initialization frame, including valid CRC7.
 * CMD0 resets protocol state and can interrupt pending programming: generating
 * this frame is NOT permission to send it to a live/writing card. The later
 * transport must establish exclusive, cold-start ownership first. */
unsigned r10_sd_metadata_frame(unsigned command, uint8_t frame[6]);

/* Decode saved normalized responses, preserving bounded partial raw prefixes.
 * errors/lengths order: OCR,CID,CSD. Successful parsing is not authentication,
 * physical capacity/integrity, endurance or logging qualification. */
unsigned r10_sd_metadata_decode(const uint8_t *ocr, unsigned ocr_n,
                               const uint8_t *cid, unsigned cid_n,
                               const uint8_t *csd, unsigned csd_n,
                               r10_sd_metadata *out);
#endif
