#ifndef USB_TEST_TUSB
#define USB_TEST_TUSB
#include <stdbool.h>
#include <stdint.h>
typedef struct{uint16_t bm_double_buffered;bool vbus_sensing;} tud_configure_dwc2_t;
typedef struct{unsigned role,speed;} tusb_rhport_init_t;
#define TUD_CFGID_DWC2 1
#define TUSB_ROLE_DEVICE 1
#define TUSB_SPEED_FULL 1
void tusb_int_handler(unsigned,bool);
bool tud_configure(unsigned,unsigned,const void *);
bool tusb_init(unsigned,const tusb_rhport_init_t *);
bool tud_inited(void);
bool tud_disconnect(void);
bool tud_deinit(unsigned);
bool tud_mounted(void);
bool tud_suspended(void);
bool tud_cdc_connected(void);
void tud_task_ext(unsigned,bool);
uint32_t tud_cdc_available(void);
uint32_t tud_cdc_read(void *,uint32_t);
uint32_t tud_cdc_write(const void *,uint32_t);
uint32_t tud_cdc_write_flush(void);
void tud_cdc_read_flush(void);
bool tud_cdc_write_clear(void);
#endif
