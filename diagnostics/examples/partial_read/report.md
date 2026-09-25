# M3 diagnostic record

**Synthetic test data; must not be used for physical acceptance.**

Status: INCOMPLETE; assembly ID: SYNTHETIC-NOT-A-BOARD
Board file SHA-256: `cd647b9400a4e2bfca729b0c96e97cb2fb97ec3455387bfe58a5aeb008527f72`

| Check | Result | Finding and next step |
|---|---|---|
| CAPTURE_COMPLETENESS | INCONCLUSIVE | Capture state=PARTIAL; only retained readings are interpreted. Errors / timeouts / missing data are never evidence of a pass. |
| DBG_IDENTITY | PASS | CPUID=0x411fc271, DEV_ID=0x450, REV_ID=0x2003. These fields only confirm the core and compatible family, not the exact part number, package or authenticity. |
| FLASH_CAPACITY | PASS | Flash size register=2048 KiB; the current VI part expects 2048 KiB. This reads the size identifier; it is not a write / erase / read-back test. |
| BOARD_UID | PASS | UID=00000000-01234567-89abcdef Register the UID against the physical assembly ID; a single zero 32-bit word is not a device error. |
| RESET_HISTORY | NOT_TESTED | RCC_RSR not read.  |
| CLOCK_SNAPSHOT | INFO | System clock source=HSI; selected source ready=True. Only configuration / ready state is checked; frequency accuracy, start-up margin and jitter still need measurement. |
| HSE_STATE | NOT_TESTED | HSE enabled=False, ready=False. HSE not enabled does not mean the crystal is bad; enabled but not ready must be separated into still initialising, software configuration, or a Y1/C25/C26 problem. |
| CPU_FAULT_FLAGS | INFO | CPU fault flags recorded; state not cleared. Flags set do not mean a fault is still present, and zero flags do not prove the firmware correct. Fault addresses are interpreted only when VALID is set. |
| VOLTAGE_SCALING | INFO | VOS code=1, VOSRDY=True. Digital state is not a measured VCAP voltage; interpret with the silicon revision and operating mode. |
| POWER_MEASUREMENTS | NOT_TESTED | No external instrument voltage evidence. Fill in an independent bench measurement sheet; never use the ADC reference to prove its own supply is correct. |
| SPI_SENSOR | NOT_TESTED | IMU identity, sample liveness, noise and interrupt not yet performed.  |
| I2C_SENSOR | NOT_TESTED | Barometer PROM CRC, conversion and noise not yet performed.  |
| QSPI_DATA | NOT_TESTED | External flash quad write/read verification not yet performed.  |
| USB_DATA | NOT_TESTED | USB enumeration and data transfer not yet performed.  |
| WATCHDOG | NOT_TESTED | Real watchdog timeout reset not yet performed.  |
| TRANSIENTS | NOT_TESTED | Power start-up, ripple and load steps not yet performed.  |
| GNSS | NOT_POPULATED | U6 is not fitted in this assembly configuration; the physical configuration still needs recording.  |
