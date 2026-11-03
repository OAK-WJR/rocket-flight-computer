ENTRY(Reset_Handler)
MEMORY {
 FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 2048K
 RAM (rw) : ORIGIN = 0x20000000, LENGTH = 128K
 MAILBOX (rw) : ORIGIN = 0x24000000, LENGTH = 512
}
_estack = ORIGIN(RAM) + LENGTH(RAM);
SECTIONS {
 .isr_vector : { KEEP(*(.isr_vector)) } >FLASH
 .text : { *(.text*) *(.rodata*) . = ALIGN(4); } >FLASH
 .ARM.extab : { *(.ARM.extab*) } >FLASH
 .ARM.exidx : { *(.ARM.exidx*) } >FLASH
 _sidata = LOADADDR(.data);
 .data : { . = ALIGN(4); _sdata = .; *(.data*) . = ALIGN(4); _edata = .; } >RAM AT>FLASH
 .bss (NOLOAD) : { . = ALIGN(4); _sbss = .; *(.bss*) *(COMMON) . = ALIGN(4); _ebss = .; } >RAM
 .r10_mailbox (NOLOAD) : { KEEP(*(.r10_mailbox)) } >MAILBOX
 _r10_mailbox_start = ADDR(.r10_mailbox);
 _r10_mailbox_end = ADDR(.r10_mailbox) + SIZEOF(.r10_mailbox);
 .ARM.attributes 0 : { *(.ARM.attributes) }
 ASSERT(ADDR(.isr_vector) == 0x08000000, "vector moved")
 ASSERT(SIZEOF(.isr_vector) == 664, "H743 vector count changed")
 ASSERT(ADDR(.r10_mailbox) == 0x24000000 && SIZEOF(.r10_mailbox) == 512, "R10 ABI changed")
 ASSERT(_ebss <= _estack - 8192, "stack reserve less than 8KiB")
}
