/* Memory origins/sizes from ST's H743 template and stm32h743xx.h.
 * DTCM holds normal program data/stack; v2-v4 expose512 initialized bytes,
 * v5 initializes1024. The host checks the exact header before extending access.
 * No heap. No sections may spill into the mailbox region.
 */
ENTRY(Reset_Handler)
MEMORY {
 FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 2048K
 RAM (xrw) : ORIGIN = 0x20000000, LENGTH = 128K
 MAILBOX (rw) : ORIGIN = 0x24000000, LENGTH = 1024
}
_estack = ORIGIN(RAM) + LENGTH(RAM);
SECTIONS {
 .isr_vector : { . = ALIGN(4); KEEP(*(.isr_vector)) } >FLASH
 .text : { *(.text*) *(.rodata*) *(.glue_7*) KEEP(*(.init)) KEEP(*(.fini)) . = ALIGN(4); } >FLASH
 .ARM.extab : { *(.ARM.extab*) } >FLASH
 .ARM.exidx : { __exidx_start = .; *(.ARM.exidx*) __exidx_end = .; } >FLASH
 .preinit_array : { PROVIDE_HIDDEN(__preinit_array_start = .); KEEP(*(.preinit_array*)) PROVIDE_HIDDEN(__preinit_array_end = .); } >FLASH
 .init_array : { PROVIDE_HIDDEN(__init_array_start = .); KEEP(*(SORT(.init_array.*))) KEEP(*(.init_array*)) PROVIDE_HIDDEN(__init_array_end = .); } >FLASH
 .fini_array : { PROVIDE_HIDDEN(__fini_array_start = .); KEEP(*(SORT(.fini_array.*))) KEEP(*(.fini_array*)) PROVIDE_HIDDEN(__fini_array_end = .); } >FLASH
 _sidata = LOADADDR(.data);
 .data : { . = ALIGN(4); _sdata = .; *(.data*) . = ALIGN(4); _edata = .; } >RAM AT>FLASH
 .bss (NOLOAD) : { . = ALIGN(4); _sbss = .; *(.bss*) *(COMMON) . = ALIGN(4); _ebss = .; } >RAM
 .bench_mailbox (NOLOAD) : { KEEP(*(.bench_mailbox)) } >MAILBOX
 .ARM.attributes 0 : { *(.ARM.attributes) }
 ASSERT(SIZEOF(.bench_mailbox) == 512 || SIZEOF(.bench_mailbox) == 1024, "Mailbox ABI changed")
 ASSERT(_ebss <= _estack - 8192, "Less than 8KiB reserved stack")
}
