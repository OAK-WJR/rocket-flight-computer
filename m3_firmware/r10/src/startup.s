.syntax unified
.cpu cortex-m7
.thumb

/* No C, stack use or SRAM reads before ECC initialization. DTCM ECC words
 * are 32 bits; AXI SRAM words are 64 bits (RM0433, AN5342). */
.section .text.Reset_Handler,"ax",%progbits
.global Reset_Handler
.type Reset_Handler,%function
.thumb_func
Reset_Handler:
    cpsid i
    /* RM0433 6.4.1: Run* forbids RAM writes until ACTVOSRDY. Mirror the
     * pinned H743 LDO branch of ExitRun0Mode without a C call/stack access.
     * PWR base/CR3/CSR1 offsets and masks are checked against the pinned header. */
    ldr r0, =0x58024800
    ldr r1, [r0, #0x0c]
    orr r1, r1, #2
    str r1, [r0, #0x0c]
.global r10_supply_wait
r10_supply_wait:
    ldr r1, [r0, #4]
    tst r1, #0x2000
    beq r10_supply_wait
    dsb sy
    ldr r0, =0x20000000
    ldr r1, =0x20020000
    movs r2, #0
1:  str r2, [r0], #4
    cmp r0, r1
    blo 1b
    ldr r0, =_r10_mailbox_start
    ldr r1, =_r10_mailbox_end
    movs r3, #0
2:  strd r2, r3, [r0], #8
    cmp r0, r1
    blo 2b
    dsb sy
    ldr r0, =_sidata
    ldr r1, =_sdata
    ldr r2, =_edata
3:  cmp r1, r2
    bhs 4f
    ldr r3, [r0], #4
    str r3, [r1], #4
    b 3b
4:  bl SystemInit
    bl main
5:  b 5b
.size Reset_Handler, .-Reset_Handler

.section .isr_vector,"a",%progbits
.balign 1024
.global g_pfnVectors
.type g_pfnVectors,%object
g_pfnVectors:
    .word _estack, Reset_Handler
    .word Default_Handler, Default_Handler /* NMI, HardFault */
    .word Default_Handler, Default_Handler, Default_Handler
    .word 0, 0, 0, 0
    .word Default_Handler, Default_Handler, 0, Default_Handler, SysTick_Handler
    /* H743 IRQn 0..149. No external interrupt is enabled. */
    .rept 150
    .word Default_Handler
    .endr
.size g_pfnVectors, .-g_pfnVectors
