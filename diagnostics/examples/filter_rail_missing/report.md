# M3 diagnostic record

**Synthetic test data; must not be used for physical acceptance.**

Status: ISSUES_FOUND; assembly ID: SYNTHETIC-NOT-A-BOARD
Board file SHA-256: `cd647b9400a4e2bfca729b0c96e97cb2fb97ec3455387bfe58a5aeb008527f72`

| Check | Result | Finding and next step |
|---|---|---|
| DBG_IDENTITY | PASS | CPUID=0x411fc271, DEV_ID=0x450, REV_ID=0x2003. These fields only confirm the core and compatible family, not the exact part number, package or authenticity. |
| FLASH_CAPACITY | PASS | Flash size register=2048 KiB; the current VI part expects 2048 KiB. This reads the size identifier; it is not a write / erase / read-back test. |
| BOARD_UID | PASS | UID=00000000-01234567-89abcdef Register the UID against the physical assembly ID; a single zero 32-bit word is not a device error. |
| RESET_HISTORY | INFO | Reset flags: POR Flags may accumulate or have been cleared by firmware; they cannot uniquely identify the last reset cause. This program never clears them. |
| CLOCK_SNAPSHOT | INFO | System clock source=HSI; selected source ready=True. Only configuration / ready state is checked; frequency accuracy, start-up margin and jitter still need measurement. |
| HSE_STATE | NOT_TESTED | HSE enabled=False, ready=False. HSE not enabled does not mean the crystal is bad; enabled but not ready must be separated into still initialising, software configuration, or a Y1/C25/C26 problem. |
| CPU_FAULT_FLAGS | INFO | CPU fault flags recorded; state not cleared. Flags set do not mean a fault is still present, and zero flags do not prove the firmware correct. Fault addresses are interpreted only when VALID is set. |
| VOLTAGE_SCALING | INFO | VOS code=1, VOSRDY=True. Digital state is not a measured VCAP voltage; interpret with the silicon revision and operating mode. |
| DC_3V3 | PASS | 3V3 measured interval=[3.2980,3.3020] V. 3.3 V ±5% is only a DC screening window, not proof that every chip or transient is acceptable. |
| DC_3V3A | FAIL | 3V3A measured interval=[0.0480,0.0520] V. 3.3 V ±5% is only a DC screening window, not proof that every chip or transient is acceptable. |
| POWER_PATH | FAIL | 3V3 present but 3V3A not established. Check the L2 connection and sensor-side load shorts first, then SPI/I2C. |
| DIV_VLOGIC | INFO | Measured interval [0.41618,0.42018] V; the 1% resistor + meter input loading model expects [0.41009,0.42564] V. Overlap only means consistency with this model; if they do not overlap, check wiring / meter / fitted resistor values first, then the divider and ADC side. |
| DIV_3V3 | INFO | Measured interval [1.64800,1.65200] V; the 1% resistor + meter input loading model expects [1.63169,1.66668] V. Overlap only means consistency with this model; if they do not overlap, check wiring / meter / fitted resistor values first, then the divider and ADC side. |
| SPI_SENSOR | NOT_TESTED | IMU identity, sample liveness, noise and interrupt not yet performed.  |
| I2C_SENSOR | NOT_TESTED | Barometer PROM CRC, conversion and noise not yet performed.  |
| QSPI_DATA | NOT_TESTED | External flash quad write/read verification not yet performed.  |
| USB_DATA | NOT_TESTED | USB enumeration and data transfer not yet performed.  |
| WATCHDOG | NOT_TESTED | Real watchdog timeout reset not yet performed.  |
| TRANSIENTS | NOT_TESTED | Power start-up, ripple and load steps not yet performed.  |
| GNSS | NOT_POPULATED | U6 is not fitted in this assembly configuration; the physical configuration still needs recording.  |
