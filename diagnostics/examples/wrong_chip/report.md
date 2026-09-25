# M3 diagnostic record

**Synthetic test data; must not be used for physical acceptance.**

Status: ISSUES_FOUND; assembly ID: SYNTHETIC-NOT-A-BOARD
Board file SHA-256: `cd647b9400a4e2bfca729b0c96e97cb2fb97ec3455387bfe58a5aeb008527f72`

| Check | Result | Finding and next step |
|---|---|---|
| CAPTURE_COMPLETENESS | INCONCLUSIVE | Capture state=IDENTITY_UNCONFIRMED; only retained readings are interpreted. Errors / timeouts / missing data are never evidence of a pass. |
| DBG_IDENTITY | FAIL | CPUID=0x411fc271, DEV_ID=0x483, REV_ID=0x1000. These fields only confirm the core and compatible family, not the exact part number, package or authenticity. |
| DEVICE_TESTS | NOT_TESTED | Device identity not confirmed; part-specific registers are not interpreted.  |
| POWER_MEASUREMENTS | NOT_TESTED | No external instrument voltage evidence. Fill in an independent bench measurement sheet; never use the ADC reference to prove its own supply is correct. |
| SPI_SENSOR | NOT_TESTED | IMU identity, sample liveness, noise and interrupt not yet performed.  |
| I2C_SENSOR | NOT_TESTED | Barometer PROM CRC, conversion and noise not yet performed.  |
| QSPI_DATA | NOT_TESTED | External flash quad write/read verification not yet performed.  |
| USB_DATA | NOT_TESTED | USB enumeration and data transfer not yet performed.  |
| WATCHDOG | NOT_TESTED | Real watchdog timeout reset not yet performed.  |
| TRANSIENTS | NOT_TESTED | Power start-up, ripple and load steps not yet performed.  |
| GNSS | NOT_POPULATED | U6 is not fitted in this assembly configuration; the physical configuration still needs recording.  |
